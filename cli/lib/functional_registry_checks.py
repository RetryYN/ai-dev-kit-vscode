from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

from functional_registry_seed import DOMAIN_SCAN_TARGETS, parse_markdown_registry_names
from registry_checks import (
    DetectorReport,
    Finding,
    RegistryLoadError,
    _coerce_entry_rows,
    _load_yaml_payload,
)


DOMAIN_ENUM = frozenset({"cli", "lib", "hook", "agent", "skill", "workflow", "template"})
FR_ID_PATTERN = re.compile(r"^FR-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
DEFAULT_SCAN_TARGETS = DOMAIN_SCAN_TARGETS


@dataclass(slots=True)
class FunctionalRegistryEntry:
    id: str
    name: str
    domain: str
    description: str
    l1_fr: list[str]
    l3_fr: list[str]
    status: str
    code_paths: list[str]
    doc_paths: list[str]


@dataclass(frozen=True, slots=True)
class ScannedAsset:
    domain: str
    path: str
    names: tuple[str, ...]


def _normalize_path(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _normalize_text_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [value for item in raw if (value := str(item).strip())]
    value = str(raw).strip()
    return [value] if value else []


def _normalize_path_list(raw: Any) -> list[str]:
    return [value for item in _normalize_text_list(raw) if (value := _normalize_path(item))]


def _require_mapping(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise ValueError("functional registry entry must be a mapping")
    return raw


def _require_text(raw: Any, field_name: str) -> str:
    value = str(raw or "").strip()
    if not value:
        raise ValueError(f"missing required field: {field_name}")
    return value


def _validate_entry(raw: Any) -> FunctionalRegistryEntry:
    row = _require_mapping(raw)
    required_fields = (
        "id",
        "name",
        "domain",
        "description",
        "l1_fr",
        "l3_fr",
        "status",
        "code_paths",
        "doc_paths",
    )
    for field_name in required_fields:
        if field_name not in row:
            raise ValueError(f"missing required field: {field_name}")

    domain = _require_text(row.get("domain"), "domain")
    if domain not in DOMAIN_ENUM:
        raise ValueError(f"unsupported domain: {domain}")

    return FunctionalRegistryEntry(
        id=_require_text(row.get("id"), "id"),
        name=_require_text(row.get("name"), "name"),
        domain=domain,
        description=_require_text(row.get("description"), "description"),
        l1_fr=_normalize_text_list(row.get("l1_fr")),
        l3_fr=_normalize_text_list(row.get("l3_fr")),
        status=_require_text(row.get("status"), "status"),
        code_paths=_normalize_path_list(row.get("code_paths")),
        doc_paths=_normalize_path_list(row.get("doc_paths")),
    )


def _relative_to(base: Path, target: Path) -> str:
    try:
        return target.relative_to(base).as_posix()
    except ValueError:
        return target.as_posix()


def _display_path(path: str | Path, base: Path | None = None) -> str:
    path_obj = Path(path).expanduser()
    if base is None:
        return _normalize_path(path_obj.as_posix())
    return _relative_to(base.resolve(), path_obj.resolve())


def _derive_asset_names(domain: str, rel_path: str) -> tuple[str, ...]:
    path = Path(rel_path)
    names: list[str] = []

    if domain == "skill" and path.name == "SKILL.md":
        try:
            names.append(path.relative_to("skills").parent.as_posix())
        except ValueError:
            names.append(path.parent.as_posix())
    elif domain == "template":
        try:
            template_relative = path.relative_to("cli/templates").as_posix()
        except ValueError:
            template_relative = path.as_posix()
        names.append(template_relative)

    names.append(path.name)
    return tuple(dict.fromkeys(name for name in names if name))


def _scan_assets(repo_root: Path, scan_targets: Mapping[str, Sequence[str]]) -> list[ScannedAsset]:
    assets: dict[str, ScannedAsset] = {}
    for domain, patterns in scan_targets.items():
        for pattern in patterns:
            for path in sorted(repo_root.glob(pattern)):
                if not path.is_file():
                    continue
                rel_path = _relative_to(repo_root, path)
                assets.setdefault(
                    rel_path,
                    ScannedAsset(
                        domain=domain,
                        path=rel_path,
                        names=_derive_asset_names(domain, rel_path),
                    ),
                )
    return sorted(assets.values(), key=lambda asset: asset.path)


def _build_trace_issues(entry: FunctionalRegistryEntry) -> list[str]:
    issues: list[str] = []
    for field_name, trace_ids in (("l1_fr", entry.l1_fr), ("l3_fr", entry.l3_fr)):
        if not trace_ids:
            issues.append(f"{field_name} is empty")
            continue
        invalid_ids = [trace_id for trace_id in trace_ids if not FR_ID_PATTERN.fullmatch(trace_id)]
        if invalid_ids:
            issues.append(f"{field_name} has invalid ids: {', '.join(invalid_ids)}")
    return issues


def _build_report(
    check_name: str,
    findings: list[Finding],
    metrics: dict[str, Any],
) -> DetectorReport:
    return DetectorReport.build(
        check_name=check_name,
        domain="functional_registry",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def load_functional_registry(yaml_path: str | Path) -> list[FunctionalRegistryEntry]:
    path = Path(yaml_path).expanduser().resolve()
    try:
        payload = _load_yaml_payload(path.read_text(encoding="utf-8"))
        rows = _coerce_entry_rows(payload)
        return [_validate_entry(row) for row in rows]
    except (OSError, ValueError) as exc:
        raise RegistryLoadError(str(exc)) from exc


def _resolve_repo_root(registry_path: str | Path, repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()

    registry_path_obj = Path(registry_path).expanduser().resolve()
    if registry_path_obj.parent.name == "config" and registry_path_obj.parent.parent.name == "cli":
        return registry_path_obj.parent.parent.parent
    return registry_path_obj.parent


def check_functional_registry(
    registry_path: str | Path,
    repo_root: str | Path,
    scan_targets: Mapping[str, Sequence[str]] | None = None,
) -> DetectorReport:
    repo_root_path = Path(repo_root).expanduser().resolve()
    registry_display = _display_path(registry_path, repo_root_path)
    entries = load_functional_registry(registry_path)
    findings: list[Finding] = []

    duplicate_ids: dict[str, int] = {}
    for entry in entries:
        duplicate_ids[entry.id] = duplicate_ids.get(entry.id, 0) + 1

    for entry in entries:
        if duplicate_ids[entry.id] > 1:
            findings.append(
                Finding(
                    severity="P1",
                    kind="duplicate_id",
                    entry_id=entry.id,
                    path=registry_display,
                    message=f"registry id {entry.id} is duplicated",
                    remediation="make each functional registry id unique",
                )
            )

        if entry.status != "deprecated":
            for rel_path in (*entry.code_paths, *entry.doc_paths):
                if not (repo_root_path / rel_path).exists():
                    findings.append(
                        Finding(
                            severity="P2",
                            kind="missing_registered_path",
                            entry_id=entry.id,
                            path=rel_path,
                            message=f"registered path does not exist: {rel_path}",
                            remediation="remove the stale path or restore the asset",
                        )
                    )

        if entry.status == "active":
            trace_issues = _build_trace_issues(entry)
            if trace_issues:
                findings.append(
                    Finding(
                        severity="P3",
                        kind="invalid_fr_trace",
                        entry_id=entry.id,
                        path=registry_display,
                        message="; ".join(trace_issues),
                        remediation="fill valid l1_fr and l3_fr ids for active entries",
                    )
                )

    registered_identities = {
        (entry.domain, rel_path)
        for entry in entries
        for rel_path in (*entry.code_paths, *entry.doc_paths)
    }
    registered_names_by_domain: dict[str, set[str]] = {}
    for entry in entries:
        registered_names_by_domain.setdefault(entry.domain, set()).add(entry.name)
    scanned_assets = _scan_assets(repo_root_path, scan_targets or DEFAULT_SCAN_TARGETS)

    for asset in scanned_assets:
        if (asset.domain, asset.path) in registered_identities:
            continue
        domain_names = registered_names_by_domain.get(asset.domain, set())
        if any(name in domain_names for name in asset.names):
            continue
        findings.append(
            Finding(
                severity="P2",
                kind="unregistered_asset",
                entry_id="UNREGISTERED",
                path=asset.path,
                message=f"{asset.domain} asset exists on disk but is missing from the functional registry",
                remediation="add the asset path and name to cli/config/functional-registry.yaml",
            )
        )

    return _build_report(
        "check_functional_registry",
        findings,
        {
            "entries": len(entries),
            "duplicate_ids": sum(1 for count in duplicate_ids.values() if count > 1),
            "scanned_assets": len(scanned_assets),
            "registered_paths": len(registered_identities),
        },
    )


def check_fr_sot_alignment(
    md_path: str | Path,
    yaml_path: str | Path,
    repo_root: str | Path | None = None,
) -> DetectorReport:
    yaml_entries = load_functional_registry(yaml_path)
    md_path_obj = Path(md_path).expanduser().resolve()
    repo_root_path = _resolve_repo_root(yaml_path, repo_root)
    md_names = parse_markdown_registry_names(md_path_obj.read_text(encoding="utf-8"), repo_root_path)
    yaml_names = [entry.name for entry in yaml_entries]
    yaml_name_set = set(yaml_names)
    md_name_set = set(md_names)
    findings: list[Finding] = []

    if len(md_names) != len(yaml_names):
        findings.append(
            Finding(
                severity="P2",
                kind="md_count_mismatch",
                entry_id="FUNCTIONAL-REGISTRY",
                path=_normalize_path(md_path_obj.name),
                message=f"markdown count {len(md_names)} does not match yaml count {len(yaml_names)}",
                remediation="sync markdown table rows with cli/config/functional-registry.yaml",
            )
        )

    missing_from_md = sorted(yaml_name_set - md_name_set)
    extra_in_md = sorted(md_name_set - yaml_name_set)
    if missing_from_md or extra_in_md:
        detail_parts: list[str] = []
        if missing_from_md:
            detail_parts.append(f"missing in markdown: {', '.join(missing_from_md[:5])}")
        if extra_in_md:
            detail_parts.append(f"extra in markdown: {', '.join(extra_in_md[:5])}")
        findings.append(
            Finding(
                severity="P2",
                kind="md_name_set_mismatch",
                entry_id="FUNCTIONAL-REGISTRY",
                path=_normalize_path(md_path_obj.name),
                message="; ".join(detail_parts),
                remediation="make markdown §3-§9 names match the yaml registry names",
            )
        )

    return _build_report(
        "check_fr_sot_alignment",
        findings,
        {
            "yaml_entries": len(yaml_names),
            "md_entries": len(md_names),
            "missing_from_md": len(missing_from_md),
            "extra_in_md": len(extra_in_md),
        },
    )


def _finding_fingerprint(finding: Mapping[str, Any]) -> str:
    raw = "|".join(
        str(finding.get(field, ""))
        for field in ("severity", "kind", "entry_id", "path")
    )
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


def build_functional_registry_baseline_payload(
    registry_path: str | Path,
    md_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    owner: str = "codex",
    created: str | None = None,
    expiry: str | None = None,
    expiry_days: int = 90,
    generated_by: str = "functional_registry_checks.py --emit-baseline",
) -> dict[str, Any]:
    repo_root_path = _resolve_repo_root(registry_path, repo_root)
    created_date = date.fromisoformat(_normalize_iso_date(created, fallback=date.today()))
    expiry_date = date.fromisoformat(expiry) if expiry else created_date + timedelta(days=expiry_days)
    reports = [
        _decorate_report_payload(check_functional_registry(registry_path, repo_root_path)),
        _decorate_report_payload(check_fr_sot_alignment(md_path, registry_path, repo_root=repo_root_path)),
    ]
    return {
        "intentional_baseline": True,
        "owner": owner,
        "created": created_date.isoformat(),
        "expiry": expiry_date.isoformat(),
        "generated_by": generated_by,
        "reports": reports,
    }


def write_functional_registry_baseline(
    output_path: str | Path,
    registry_path: str | Path,
    md_path: str | Path,
    repo_root: str | Path | None = None,
    **kwargs: Any,
) -> Path:
    output_path_obj = Path(output_path).expanduser().resolve()
    payload = build_functional_registry_baseline_payload(
        registry_path=registry_path,
        md_path=md_path,
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
    parser = argparse.ArgumentParser(description="functional registry detector utilities")
    parser.add_argument("--emit-baseline", action="store_true", help="write a machine-readable functional registry baseline")
    parser.add_argument("--repo-root", default=".", help="repository root for disk scans and grouped-row expansion")
    parser.add_argument("--registry-path", default="cli/config/functional-registry.yaml", help="functional registry yaml path")
    parser.add_argument(
        "--md-path",
        default="docs/v2/L3-requirements/helix-workflows-functional-registry.md",
        help="functional registry markdown SSoT path",
    )
    parser.add_argument(
        "--output",
        default="cli/config/functional-registry-baseline.json",
        help="baseline output path",
    )
    parser.add_argument("--owner", default="codex", help="baseline owner metadata")
    parser.add_argument("--created", default=None, help="baseline creation date (YYYY-MM-DD)")
    parser.add_argument("--expiry", default=None, help="baseline expiry date (YYYY-MM-DD)")
    parser.add_argument("--expiry-days", type=int, default=90, help="expiry offset when --expiry is omitted")
    parser.add_argument(
        "--generated-by",
        default="functional_registry_checks.py --emit-baseline",
        help="baseline generated_by metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.emit_baseline:
        parser.error("no action requested")

    output_path = write_functional_registry_baseline(
        output_path=args.output,
        registry_path=args.registry_path,
        md_path=args.md_path,
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
