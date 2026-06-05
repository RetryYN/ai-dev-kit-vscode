from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from registry_checks import DetectorReport, Finding, RegistryLoadError, _coerce_entry_rows, _load_yaml_payload


TARGET_SOT_SECTIONS = ("コーディング規約", "コミット規約", "禁止事項")
ALLOWED_ENFORCEMENT_KINDS = frozenset({"lint_config", "hook", "commitlint", "ci_gate", "manual"})
ALLOWED_ENFORCEMENT_STATUSES = frozenset({"enforced", "partial", "manual", "not-implemented"})
GAP_STATUSES = frozenset({"partial", "manual", "not-implemented"})
DEFAULT_SELF_ASSETS = (
    "cli/lib/coding_rule_checks.py",
    "cli/config/coding-rule-registry.yaml",
)


@dataclass(slots=True)
class Enforcement:
    kind: str
    paths: list[str]
    status: str


@dataclass(slots=True)
class CodingRuleEntry:
    id: str
    rule: str
    sot_section: str
    enforcement: Enforcement


def _normalize_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"missing required field: {field_name}")
    return text


def _normalize_path(raw: Any) -> str:
    text = str(raw or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _normalize_path_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [value for item in raw if (value := _normalize_path(item))]
    value = _normalize_path(raw)
    return [value] if value else []


def _require_mapping(raw: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise ValueError(f"{field_name} must be a mapping")
    return raw


def _validate_entry(raw: Any) -> CodingRuleEntry:
    row = _require_mapping(raw, "coding rule entry")
    enforcement_row = _require_mapping(row.get("enforcement"), "enforcement")
    kind = _normalize_text(enforcement_row.get("kind"), "enforcement.kind")
    status = _normalize_text(enforcement_row.get("status"), "enforcement.status")
    if kind not in ALLOWED_ENFORCEMENT_KINDS:
        raise ValueError(f"unsupported enforcement kind: {kind}")
    if status not in ALLOWED_ENFORCEMENT_STATUSES:
        raise ValueError(f"unsupported enforcement status: {status}")

    sot_section = _normalize_text(row.get("sot_section"), "sot_section")
    if sot_section not in TARGET_SOT_SECTIONS:
        raise ValueError(f"unsupported sot_section: {sot_section}")

    return CodingRuleEntry(
        id=_normalize_text(row.get("id"), "id"),
        rule=_normalize_text(row.get("rule"), "rule"),
        sot_section=sot_section,
        enforcement=Enforcement(
            kind=kind,
            paths=_normalize_path_list(enforcement_row.get("paths")),
            status=status,
        ),
    )


def _resolve_repo_root(registry_path: str | Path, repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()

    registry_path_obj = Path(registry_path).expanduser().resolve()
    if registry_path_obj.parent.name == "config" and registry_path_obj.parent.parent.name == "cli":
        return registry_path_obj.parent.parent.parent
    return registry_path_obj.parent


def _display_path(path: str | Path, base: Path | None = None) -> str:
    path_obj = Path(path).expanduser()
    if base is None:
        return _normalize_path(path_obj.as_posix())
    try:
        return path_obj.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return _normalize_path(path_obj.as_posix())


def _build_report(check_name: str, findings: list[Finding], metrics: dict[str, Any]) -> DetectorReport:
    return DetectorReport.build(
        check_name=check_name,
        domain="coding_rule_registry",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def load_coding_rule_registry(yaml_path: str | Path) -> list[CodingRuleEntry]:
    path = Path(yaml_path).expanduser().resolve()
    try:
        payload = _load_yaml_payload(path.read_text(encoding="utf-8"))
        rows = _coerce_entry_rows(payload)
        return [_validate_entry(row) for row in rows]
    except (OSError, ValueError) as exc:
        raise RegistryLoadError(str(exc)) from exc


def _registered_asset_paths(functional_registry_path: str | Path) -> set[str]:
    path = Path(functional_registry_path).expanduser().resolve()
    payload = _load_yaml_payload(path.read_text(encoding="utf-8"))
    rows = _coerce_entry_rows(payload)
    registered: set[str] = set()
    for row in rows:
        mapping = _require_mapping(row, "functional registry entry")
        registered.update(_normalize_path_list(mapping.get("code_paths")))
        registered.update(_normalize_path_list(mapping.get("doc_paths")))
    return registered


def check_coding_rule_sot(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    functional_registry_path: str | Path | None = None,
    self_assets: Sequence[str] = DEFAULT_SELF_ASSETS,
) -> DetectorReport:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    registry_display = _display_path(registry_path, repo_root_path)
    entries = load_coding_rule_registry(registry_path)
    findings: list[Finding] = []
    gap_count = 0
    missing_path_count = 0
    mismatch_count = 0

    for entry in entries:
        if entry.enforcement.status in GAP_STATUSES:
            gap_count += 1
            findings.append(
                Finding(
                    severity="P3",
                    kind="enforcement_gap",
                    entry_id=entry.id,
                    path=registry_display,
                    message=f"{entry.enforcement.status} enforcement leaves this rule outside full mechanical coverage",
                    remediation="implement the enforcement or keep the gap explicit until a later Action closes it",
                )
            )

        if entry.enforcement.status == "enforced" and not entry.enforcement.paths:
            mismatch_count += 1
            findings.append(
                Finding(
                    severity="P2",
                    kind="status_path_mismatch",
                    entry_id=entry.id,
                    path=registry_display,
                    message="status=enforced requires at least one concrete enforcement path",
                    remediation="add the enforcing file path or downgrade the status to partial/manual/not-implemented",
                )
            )

        for rel_path in entry.enforcement.paths:
            if not (repo_root_path / rel_path).exists():
                missing_path_count += 1
                findings.append(
                    Finding(
                        severity="P2",
                        kind="missing_enforcement_path",
                        entry_id=entry.id,
                        path=rel_path,
                        message=f"declared enforcement path does not exist: {rel_path}",
                        remediation="restore the file or remove the stale path from the registry",
                    )
                )

    functional_registry_display = "cli/config/functional-registry.yaml"
    registered_assets: set[str] = set()
    target_functional_registry = functional_registry_path or (repo_root_path / functional_registry_display)
    try:
        if Path(target_functional_registry).exists():
            registered_assets = _registered_asset_paths(target_functional_registry)
    except RegistryLoadError:
        registered_assets = set()

    unregistered_self_assets = 0
    for asset in self_assets:
        normalized_asset = _normalize_path(asset)
        if normalized_asset not in registered_assets:
            unregistered_self_assets += 1
            findings.append(
                Finding(
                    severity="P2",
                    kind="unregistered_self_asset",
                    entry_id="CODING-RULE-DETECTOR",
                    path=normalized_asset,
                    message="coding-rule detector asset is missing from cli/config/functional-registry.yaml",
                    remediation="register the detector asset in cli/config/functional-registry.yaml",
                )
            )

    return _build_report(
        "check_coding_rule_sot",
        findings,
        {
            "entries": len(entries),
            "gap_entries": gap_count,
            "missing_enforcement_paths": missing_path_count,
            "status_path_mismatches": mismatch_count,
            "unregistered_self_assets": unregistered_self_assets,
        },
    )


def _extract_clause_sections(text: str) -> dict[str, list[str]]:
    collected: dict[str, list[str]] = {section: [] for section in TARGET_SOT_SECTIONS}
    current_section: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            heading = line[3:].strip()
            current_section = heading if heading in collected else None
            continue
        if current_section and line.startswith("- "):
            collected[current_section].append(line[2:].strip())
    return collected


def check_coding_rule_alignment(
    claude_md_path: str | Path,
    registry_path: str | Path,
) -> DetectorReport:
    entries = load_coding_rule_registry(registry_path)
    claude_md_path_obj = Path(claude_md_path).expanduser().resolve()
    clauses_by_section = _extract_clause_sections(claude_md_path_obj.read_text(encoding="utf-8"))
    registry_counts: dict[str, int] = {section: 0 for section in TARGET_SOT_SECTIONS}
    for entry in entries:
        registry_counts[entry.sot_section] += 1

    findings: list[Finding] = []
    md_total = sum(len(items) for items in clauses_by_section.values())
    registry_total = len(entries)
    if md_total != registry_total:
        findings.append(
            Finding(
                severity="P2",
                kind="rule_count_mismatch",
                entry_id="CLAUDE-CODING-RULES",
                path=claude_md_path_obj.name,
                message=f"CLAUDE.md rule count {md_total} does not match registry count {registry_total}",
                remediation="sync coding-rule-registry.yaml entries with CLAUDE.md bullet rules",
            )
        )

    section_diffs = [
        f"{section}: md={len(clauses_by_section[section])} registry={registry_counts[section]}"
        for section in TARGET_SOT_SECTIONS
        if len(clauses_by_section[section]) != registry_counts[section]
    ]
    if section_diffs:
        findings.append(
            Finding(
                severity="P2",
                kind="section_count_mismatch",
                entry_id="CLAUDE-CODING-RULES",
                path=claude_md_path_obj.name,
                message="; ".join(section_diffs),
                remediation="make per-section registry entry counts match the CLAUDE.md SSoT headings",
            )
        )

    return _build_report(
        "check_coding_rule_alignment",
        findings,
        {
            "claude_rule_count": md_total,
            "registry_rule_count": registry_total,
            "claude_section_counts": {section: len(clauses_by_section[section]) for section in TARGET_SOT_SECTIONS},
            "registry_section_counts": registry_counts,
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


def build_coding_rule_baseline_payload(
    registry_path: str | Path,
    claude_md_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    owner: str = "codex",
    created: str | None = None,
    expiry: str | None = None,
    expiry_days: int = 90,
    generated_by: str = "coding_rule_checks.py --emit-baseline",
) -> dict[str, Any]:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    created_date = date.fromisoformat(_normalize_iso_date(created, fallback=date.today()))
    expiry_date = date.fromisoformat(expiry) if expiry else created_date + timedelta(days=expiry_days)
    reports = [
        _decorate_report_payload(
            check_coding_rule_sot(
                registry_path=registry_path,
                repo_root=repo_root_path,
            )
        ),
        _decorate_report_payload(check_coding_rule_alignment(claude_md_path, registry_path)),
    ]
    return {
        "intentional_baseline": True,
        "owner": owner,
        "created": created_date.isoformat(),
        "expiry": expiry_date.isoformat(),
        "generated_by": generated_by,
        "reports": reports,
    }


def write_coding_rule_baseline(
    output_path: str | Path,
    registry_path: str | Path,
    claude_md_path: str | Path,
    repo_root: str | Path | None = None,
    **kwargs: Any,
) -> Path:
    output_path_obj = Path(output_path).expanduser().resolve()
    payload = build_coding_rule_baseline_payload(
        registry_path=registry_path,
        claude_md_path=claude_md_path,
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
    parser = argparse.ArgumentParser(description="coding rule registry detector utilities")
    parser.add_argument("--emit-baseline", action="store_true", help="write a machine-readable coding rule baseline")
    parser.add_argument("--repo-root", default=".", help="repository root for enforcement path checks")
    parser.add_argument("--registry-path", default="cli/config/coding-rule-registry.yaml", help="coding rule registry yaml path")
    parser.add_argument(
        "--claude-md-path",
        "--md-path",
        dest="claude_md_path",
        default="CLAUDE.md",
        help="CLAUDE.md SSoT path",
    )
    parser.add_argument(
        "--output",
        default="cli/config/coding-rule-registry-baseline.json",
        help="baseline output path",
    )
    parser.add_argument("--owner", default="codex", help="baseline owner metadata")
    parser.add_argument("--created", default=None, help="baseline creation date (YYYY-MM-DD)")
    parser.add_argument("--expiry", default=None, help="baseline expiry date (YYYY-MM-DD)")
    parser.add_argument("--expiry-days", type=int, default=90, help="expiry offset when --expiry is omitted")
    parser.add_argument(
        "--generated-by",
        default="coding_rule_checks.py --emit-baseline",
        help="baseline generated_by metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.emit_baseline:
        parser.error("no action requested")

    output_path = write_coding_rule_baseline(
        output_path=args.output,
        registry_path=args.registry_path,
        claude_md_path=args.claude_md_path,
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
