from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from registry_checks import DetectorReport, Finding, RegistryLoadError, _load_yaml_payload


DEFAULT_CONCEPT_PATH = "docs/v2/L0-helix-workflows/concept.md"
ALLOWED_BC_KINDS = frozenset({"forward", "derived"})
ALLOWED_IMPLEMENTATION_STATUSES = frozenset(
    {
        "installed",
        "partial",
        "L4-carry",
        "not-implemented",
        "installed / migration target",
    }
)
GAP_IMPLEMENTATION_STATUSES = frozenset({"partial", "L4-carry", "not-implemented"})
EXPECTED_BC_NAMES = (
    "Forward",
    "Scrum",
    "Discovery",
    "Reverse",
    "Incident",
    "Add-feature",
    "Refactor",
    "Retrofit",
    "Research",
    "Recovery",
)
GLOSSARY_REQUIRED_FIELDS = ("cli", "file_path", "schema_field", "grep_pattern")


@dataclass(slots=True)
class GlossaryEntry:
    term: str
    definition: str
    cli: str
    file_path: str
    schema_field: str
    grep_pattern: str
    implementation_status: str


@dataclass(slots=True)
class BoundedContextEntry:
    name: str
    kind: str
    unique_terms: list[str]
    anti_corruption_via: str


@dataclass(slots=True)
class DDDRegistry:
    glossary: list[GlossaryEntry]
    bounded_contexts: list[BoundedContextEntry]


def _require_mapping(raw: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise ValueError(f"{field_name} must be a mapping")
    return raw


def _require_text(raw: Any, field_name: str) -> str:
    value = str(raw or "").strip()
    if not value:
        raise ValueError(f"missing required field: {field_name}")
    return value


def _normalize_text(raw: Any) -> str:
    return str(raw or "").strip()


def _normalize_text_list(raw: Any, field_name: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError(f"{field_name} must be a list")
    return [value for item in raw if (value := str(item).strip())]


def _validate_glossary_entry(raw: Any) -> GlossaryEntry:
    row = _require_mapping(raw, "glossary entry")
    required_fields = (
        "term",
        "definition",
        "cli",
        "file_path",
        "schema_field",
        "grep_pattern",
        "implementation_status",
    )
    for field_name in required_fields:
        if field_name not in row:
            raise ValueError(f"missing required field: {field_name}")

    return GlossaryEntry(
        term=_require_text(row.get("term"), "term"),
        definition=_require_text(row.get("definition"), "definition"),
        cli=_normalize_text(row.get("cli")),
        file_path=_normalize_text(row.get("file_path")),
        schema_field=_normalize_text(row.get("schema_field")),
        grep_pattern=_normalize_text(row.get("grep_pattern")),
        implementation_status=_normalize_text(row.get("implementation_status")),
    )


def _validate_bounded_context_entry(raw: Any) -> BoundedContextEntry:
    row = _require_mapping(raw, "bounded context entry")
    required_fields = ("name", "kind", "unique_terms", "anti_corruption_via")
    for field_name in required_fields:
        if field_name not in row:
            raise ValueError(f"missing required field: {field_name}")

    kind = _require_text(row.get("kind"), "kind")
    if kind not in ALLOWED_BC_KINDS:
        raise ValueError(f"unsupported bounded context kind: {kind}")

    return BoundedContextEntry(
        name=_require_text(row.get("name"), "name"),
        kind=kind,
        unique_terms=_normalize_text_list(row.get("unique_terms"), "unique_terms"),
        anti_corruption_via=_normalize_text(row.get("anti_corruption_via")),
    )


def load_ddd_registry(yaml_path: str | Path) -> DDDRegistry:
    path = Path(yaml_path).expanduser().resolve()
    try:
        payload = _require_mapping(_load_yaml_payload(path.read_text(encoding="utf-8")), "ddd registry")
        if "glossary" not in payload or "bounded_contexts" not in payload:
            raise ValueError("ddd registry requires glossary and bounded_contexts sections")

        glossary_rows = payload.get("glossary")
        bc_rows = payload.get("bounded_contexts")
        if not isinstance(glossary_rows, list):
            raise ValueError("glossary must be a list")
        if not isinstance(bc_rows, list):
            raise ValueError("bounded_contexts must be a list")

        return DDDRegistry(
            glossary=[_validate_glossary_entry(row) for row in glossary_rows],
            bounded_contexts=[_validate_bounded_context_entry(row) for row in bc_rows],
        )
    except (OSError, ValueError) as exc:
        raise RegistryLoadError(str(exc)) from exc


def _resolve_repo_root(registry_path: str | Path, repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()

    registry_path_obj = Path(registry_path).expanduser().resolve()
    if registry_path_obj.parent.name == "config" and registry_path_obj.parent.parent.name == "cli":
        return registry_path_obj.parent.parent.parent
    return registry_path_obj.parent


def _resolve_concept_md_path(registry_path: str | Path, repo_root: str | Path | None = None, concept_md_path: str | Path | None = None) -> Path:
    if concept_md_path is not None:
        return Path(concept_md_path).expanduser().resolve()
    return _resolve_repo_root(registry_path, repo_root) / DEFAULT_CONCEPT_PATH


def _display_path(path: str | Path, base: Path | None = None) -> str:
    path_obj = Path(path).expanduser()
    if base is None:
        return path_obj.as_posix()
    try:
        return path_obj.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path_obj.as_posix()


def _build_report(check_name: str, findings: list[Finding], metrics: dict[str, Any]) -> DetectorReport:
    return DetectorReport.build(
        check_name=check_name,
        domain="ddd_registry",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def _parse_table_cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _is_table_divider(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    cells = _parse_table_cells(stripped)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _extract_section_lines(text: str, heading_prefix: str) -> list[str]:
    lines = text.splitlines()
    start_index: int | None = None
    heading_level: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") and stripped.startswith(heading_prefix):
            start_index = index + 1
            heading_level = len(line) - len(line.lstrip("#"))
            break
    if start_index is None or heading_level is None:
        raise ValueError(f"missing heading: {heading_prefix}")

    section: list[str] = []
    for line in lines[start_index:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= heading_level:
                break
        section.append(line)
    return section


def _extract_table_rows(text: str, heading_prefix: str) -> list[tuple[str, ...]]:
    section_lines = _extract_section_lines(text, heading_prefix)
    for index, line in enumerate(section_lines):
        if line.strip().startswith("|") and index + 1 < len(section_lines) and _is_table_divider(section_lines[index + 1]):
            rows: list[tuple[str, ...]] = []
            row_index = index + 2
            while row_index < len(section_lines) and section_lines[row_index].strip().startswith("|"):
                rows.append(_parse_table_cells(section_lines[row_index]))
                row_index += 1
            if rows:
                return rows
    raise ValueError(f"missing markdown table under heading: {heading_prefix}")


def _normalize_md_label(value: str) -> str:
    text = value.strip().replace("`", "")
    bold_match = re.search(r"\*\*([^*]+)\*\*", text)
    if bold_match:
        return bold_match.group(1).strip()
    text = re.sub(r"\([^)]*\)", "", text).strip()
    return text.strip("*_ ")


def _load_concept_glossary_terms(concept_md_path: Path) -> list[str]:
    text = concept_md_path.read_text(encoding="utf-8")
    rows = _extract_table_rows(text, "### §12.1")
    return [_normalize_md_label(row[0]) for row in rows if row]


def _load_concept_bc_names(concept_md_path: Path) -> list[str]:
    text = concept_md_path.read_text(encoding="utf-8")
    rows = _extract_table_rows(text, "### §14.1")
    return [_normalize_md_label(row[0]) for row in rows if row]


def _count_concept_bc_examples(concept_md_path: Path) -> int:
    text = concept_md_path.read_text(encoding="utf-8")
    section_lines = _extract_section_lines(text, "### §14.2")
    return sum(1 for line in section_lines if line.strip().startswith("- "))


def _concept_parse_error(check_name: str, error: Exception, concept_md_path: Path) -> DetectorReport:
    return _build_report(
        check_name,
        [
            Finding(
                severity="P1",
                kind="concept_parse_error",
                entry_id="CONCEPT-SSOT",
                path=concept_md_path.as_posix(),
                message=str(error),
                remediation="fix docs/v2/L0-helix-workflows/concept.md so the §12/§14 tables remain machine-readable",
            )
        ],
        {"concept_parse_error": 1},
    )


def check_glossary_coverage(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
    concept_md_path: str | Path | None = None,
) -> DetectorReport:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    registry_display = _display_path(registry_path, repo_root_path)
    registry = load_ddd_registry(registry_path)
    concept_path = _resolve_concept_md_path(registry_path, repo_root_path, concept_md_path)
    try:
        concept_terms = _load_concept_glossary_terms(concept_path)
    except (OSError, ValueError) as exc:
        return _concept_parse_error("check_glossary_coverage", exc, concept_path)

    findings: list[Finding] = []
    duplicate_terms = 0
    implementation_gaps = 0
    missing_field_findings = 0
    invalid_statuses = 0

    if len(concept_terms) < 19:
        findings.append(
            Finding(
                severity="P1",
                kind="concept_glossary_row_shortage",
                entry_id="CONCEPT-SSOT",
                path=_display_path(concept_path, repo_root_path),
                message=f"concept glossary row count is {len(concept_terms)} but AC-12 requires at least 19",
                remediation="restore the 19 glossary rows in docs/v2/L0-helix-workflows/concept.md §12.1",
            )
        )

    if len(registry.glossary) != len(concept_terms):
        findings.append(
            Finding(
                severity="P2",
                kind="glossary_count_mismatch",
                entry_id="DDD-GLOSSARY",
                path=registry_display,
                message=f"registry glossary rows={len(registry.glossary)} do not match concept rows={len(concept_terms)}",
                remediation="sync cli/config/ddd-registry.yaml glossary rows with concept.md §12.1",
            )
        )

    concept_term_set = set(concept_terms)
    registry_terms = [entry.term for entry in registry.glossary]
    registry_term_set = set(registry_terms)
    missing_terms = sorted(concept_term_set - registry_term_set)
    extra_terms = sorted(registry_term_set - concept_term_set)
    if missing_terms or extra_terms:
        findings.append(
            Finding(
                severity="P2",
                kind="glossary_term_drift",
                entry_id="DDD-GLOSSARY",
                path=registry_display,
                message=f"missing={missing_terms or '-'} extra={extra_terms or '-'}",
                remediation="make glossary term names match concept.md §12.1 exactly",
            )
        )

    term_counts: dict[str, int] = {}
    for entry in registry.glossary:
        term_counts[entry.term] = term_counts.get(entry.term, 0) + 1

        if term_counts[entry.term] > 1:
            duplicate_terms += 1
            findings.append(
                Finding(
                    severity="P2",
                    kind="duplicate_term",
                    entry_id=entry.term,
                    path=registry_display,
                    message=f"glossary term {entry.term} is duplicated",
                    remediation="keep each glossary term unique in cli/config/ddd-registry.yaml",
                )
            )

        missing_fields = [field_name for field_name in GLOSSARY_REQUIRED_FIELDS if not getattr(entry, field_name)]
        if missing_fields:
            missing_field_findings += 1
            findings.append(
                Finding(
                    severity="P2",
                    kind="missing_glossary_field",
                    entry_id=entry.term,
                    path=registry_display,
                    message=f"missing required glossary fields: {', '.join(missing_fields)}",
                    remediation="fill cli / file_path / schema_field / grep_pattern for every glossary entry",
                )
            )

        if entry.implementation_status not in ALLOWED_IMPLEMENTATION_STATUSES:
            invalid_statuses += 1
            findings.append(
                Finding(
                    severity="P2",
                    kind="invalid_implementation_status",
                    entry_id=entry.term,
                    path=registry_display,
                    message=f"unsupported implementation_status: {entry.implementation_status}",
                    remediation="use the concept.md-compatible implementation_status values only",
                )
            )
            continue

        if entry.implementation_status in GAP_IMPLEMENTATION_STATUSES:
            implementation_gaps += 1
            findings.append(
                Finding(
                    severity="P3",
                    kind="implementation_gap",
                    entry_id=entry.term,
                    path=registry_display,
                    message=f"{entry.implementation_status} leaves this glossary term outside full installed coverage",
                    remediation="keep the carry explicit until a later Action closes the gap",
                )
            )

    return _build_report(
        "check_glossary_coverage",
        findings,
        {
            "concept_terms": len(concept_terms),
            "registry_terms": len(registry.glossary),
            "duplicate_terms": duplicate_terms,
            "missing_term_count": len(missing_terms),
            "extra_term_count": len(extra_terms),
            "missing_field_findings": missing_field_findings,
            "invalid_statuses": invalid_statuses,
            "implementation_gaps": implementation_gaps,
        },
    )


def check_bc_anti_corruption(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
    concept_md_path: str | Path | None = None,
) -> DetectorReport:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    registry_display = _display_path(registry_path, repo_root_path)
    registry = load_ddd_registry(registry_path)
    concept_path = _resolve_concept_md_path(registry_path, repo_root_path, concept_md_path)
    try:
        example_count = _count_concept_bc_examples(concept_path)
    except (OSError, ValueError) as exc:
        return _concept_parse_error("check_bc_anti_corruption", exc, concept_path)

    findings: list[Finding] = []
    missing_fields = 0
    if example_count < 3:
        findings.append(
            Finding(
                severity="P2",
                kind="bc_example_shortage",
                entry_id="DDD-BC",
                path=_display_path(concept_path, repo_root_path),
                message=f"concept §14.2 contains {example_count} examples but AC-14 requires at least 3",
                remediation="restore at least 3 anti-corruption examples in concept.md §14.2",
            )
        )

    for entry in registry.bounded_contexts:
        missing = []
        if not entry.unique_terms:
            missing.append("unique_terms")
        if not entry.anti_corruption_via:
            missing.append("anti_corruption_via")
        if not missing:
            continue
        missing_fields += 1
        findings.append(
            Finding(
                severity="P2",
                kind="missing_bc_field",
                entry_id=entry.name,
                path=registry_display,
                message=f"missing required BC fields: {', '.join(missing)}",
                remediation="fill unique_terms and anti_corruption_via for every bounded context entry",
            )
        )

    return _build_report(
        "check_bc_anti_corruption",
        findings,
        {
            "entries": len(registry.bounded_contexts),
            "concept_examples": example_count,
            "missing_field_entries": missing_fields,
        },
    )


def check_bc_mode_coverage(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
    concept_md_path: str | Path | None = None,
) -> DetectorReport:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    registry_display = _display_path(registry_path, repo_root_path)
    registry = load_ddd_registry(registry_path)
    concept_path = _resolve_concept_md_path(registry_path, repo_root_path, concept_md_path)
    try:
        concept_names = _load_concept_bc_names(concept_path)
    except (OSError, ValueError) as exc:
        return _concept_parse_error("check_bc_mode_coverage", exc, concept_path)

    findings: list[Finding] = []
    registry_names = [entry.name for entry in registry.bounded_contexts]
    concept_name_set = set(concept_names)
    expected_name_set = set(EXPECTED_BC_NAMES)
    registry_name_set = set(registry_names)
    missing_modes = sorted(expected_name_set - registry_name_set)
    unexpected_modes = sorted(registry_name_set - expected_name_set)

    if len(concept_names) != 10:
        findings.append(
            Finding(
                severity="P1",
                kind="concept_bc_row_mismatch",
                entry_id="CONCEPT-SSOT",
                path=_display_path(concept_path, repo_root_path),
                message=f"concept §14.1 row count is {len(concept_names)} but AC-14 requires 10",
                remediation="restore the 10 bounded contexts in concept.md §14.1",
            )
        )

    if concept_name_set != expected_name_set:
        findings.append(
            Finding(
                severity="P2",
                kind="concept_bc_term_drift",
                entry_id="CONCEPT-SSOT",
                path=_display_path(concept_path, repo_root_path),
                message=f"concept BC names do not match Forward1+derived9: {sorted(concept_name_set)}",
                remediation="make concept.md §14.1 keep the canonical Forward1+derived9 names",
            )
        )

    for entry in registry.bounded_contexts:
        expected_kind = "forward" if entry.name == "Forward" else "derived"
        if entry.kind != expected_kind:
            findings.append(
                Finding(
                    severity="P2",
                    kind="bc_kind_mismatch",
                    entry_id=entry.name,
                    path=registry_display,
                    message=f"{entry.name} must use kind={expected_kind} but found {entry.kind}",
                    remediation="make Forward use kind=forward and every derived workflow use kind=derived",
                )
            )

    for name in missing_modes:
        findings.append(
            Finding(
                severity="P2",
                kind="missing_bc_mode",
                entry_id=name,
                path=registry_display,
                message=f"bounded context mode is missing: {name}",
                remediation="add the missing bounded context row to cli/config/ddd-registry.yaml",
            )
        )

    for name in unexpected_modes:
        findings.append(
            Finding(
                severity="P2",
                kind="unexpected_bc_mode",
                entry_id=name,
                path=registry_display,
                message=f"unexpected bounded context mode is present: {name}",
                remediation="remove the extra bounded context row or rename it to the canonical workflow name",
            )
        )

    return _build_report(
        "check_bc_mode_coverage",
        findings,
        {
            "concept_entries": len(concept_names),
            "registry_entries": len(registry.bounded_contexts),
            "forward_present": int("Forward" in registry_name_set),
            "derived_present": sum(1 for name in registry_names if name != "Forward"),
            "missing_modes": len(missing_modes),
            "unexpected_modes": len(unexpected_modes),
        },
    )


def _finding_fingerprint(finding: Mapping[str, Any]) -> str:
    raw = "|".join(str(finding.get(field, "")) for field in ("severity", "kind", "entry_id", "path"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decorate_report_payload(report: DetectorReport) -> dict[str, Any]:
    payload = json.loads(report.render("json"))
    for finding in payload.get("findings", []):
        finding["fingerprint"] = _finding_fingerprint(finding)
    return payload


def _normalize_iso_date(value: str | None, *, fallback: date) -> str:
    if not value:
        return fallback.isoformat()
    return date.fromisoformat(value).isoformat()


def build_ddd_registry_baseline_payload(
    registry_path: str | Path,
    concept_md_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    owner: str = "codex",
    created: str | None = None,
    expiry: str | None = None,
    expiry_days: int = 90,
    generated_by: str = "ddd_registry_checks.py --emit-baseline",
) -> dict[str, Any]:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    created_date = date.fromisoformat(_normalize_iso_date(created, fallback=date.today()))
    expiry_date = date.fromisoformat(expiry) if expiry else created_date + timedelta(days=expiry_days)
    reports = [
        _decorate_report_payload(check_glossary_coverage(registry_path=registry_path, repo_root=repo_root_path, concept_md_path=concept_md_path)),
        _decorate_report_payload(check_bc_anti_corruption(registry_path=registry_path, repo_root=repo_root_path, concept_md_path=concept_md_path)),
        _decorate_report_payload(check_bc_mode_coverage(registry_path=registry_path, repo_root=repo_root_path, concept_md_path=concept_md_path)),
    ]
    return {
        "intentional_baseline": True,
        "owner": owner,
        "created": created_date.isoformat(),
        "expiry": expiry_date.isoformat(),
        "generated_by": generated_by,
        "reports": reports,
    }


def write_ddd_registry_baseline(
    output_path: str | Path,
    registry_path: str | Path,
    concept_md_path: str | Path,
    repo_root: str | Path | None = None,
    **kwargs: Any,
) -> Path:
    output_path_obj = Path(output_path).expanduser().resolve()
    payload = build_ddd_registry_baseline_payload(
        registry_path=registry_path,
        concept_md_path=concept_md_path,
        repo_root=repo_root,
        **kwargs,
    )
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_path_obj.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path_obj


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ddd registry detector utilities")
    parser.add_argument("--emit-baseline", action="store_true", help="write a machine-readable DDD registry baseline")
    parser.add_argument("--repo-root", default=".", help="repository root for concept path resolution")
    parser.add_argument("--registry-path", default="cli/config/ddd-registry.yaml", help="ddd registry yaml path")
    parser.add_argument(
        "--concept-md-path",
        "--concept-path",
        dest="concept_md_path",
        default=DEFAULT_CONCEPT_PATH,
        help="concept.md SSoT path",
    )
    parser.add_argument(
        "--output",
        default="cli/config/ddd-registry-baseline.json",
        help="baseline output path",
    )
    parser.add_argument("--owner", default="codex", help="baseline owner metadata")
    parser.add_argument("--created", default=None, help="baseline creation date (YYYY-MM-DD)")
    parser.add_argument("--expiry", default=None, help="baseline expiry date (YYYY-MM-DD)")
    parser.add_argument("--expiry-days", type=int, default=90, help="expiry offset when --expiry is omitted")
    parser.add_argument(
        "--generated-by",
        default="ddd_registry_checks.py --emit-baseline",
        help="baseline generated_by metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.emit_baseline:
        parser.error("no action requested")

    output_path = write_ddd_registry_baseline(
        output_path=args.output,
        registry_path=args.registry_path,
        concept_md_path=args.concept_md_path,
        repo_root=args.repo_root,
        owner=args.owner,
        created=args.created,
        expiry=args.expiry,
        expiry_days=args.expiry_days,
        generated_by=args.generated_by,
    )
    print(output_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
