from __future__ import annotations

"""Functional-registry `uses` detector with changed-files gate support.

`cli/lib/vg_overview.py` consumes `collect_fr_uses_full_required_summary()`
via `required_clean` (C-3a: forward uses-target existence は full-scan
full-required, `clean = blocking_finding_count == 0`)。`collect_fr_uses_gate_summary()`
は changed-files ratchet 用に残し、既存 test の monkeypatch surface として使う。
逆参照(reverse)は C-3b で forward `uses` からの derived index 化に切り替えた。
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any, Sequence

from changed_files import changed_files
from registry_checks import _coerce_entry_rows, _load_yaml_payload


DEFAULT_REGISTRY_PATH = "cli/config/functional-registry.yaml"


def _resolve_project_root(repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _normalize_path(path: str | Path, repo_root: Path) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = (repo_root / path_obj).resolve()
    try:
        return path_obj.relative_to(repo_root).as_posix()
    except ValueError:
        return path_obj.as_posix()


def _normalize_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    value = str(raw).strip()
    return [value] if value else []


def _load_registry_entries(registry_path: str | Path, repo_root: Path) -> list[dict[str, Any]]:
    path = Path(registry_path)
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    payload = _load_yaml_payload(path.read_text(encoding="utf-8"))
    return [dict(row) for row in _coerce_entry_rows(payload)]


def build_reverse_used_by_index(entries: Sequence[dict[str, Any]]) -> dict[str, set[str]]:
    """Project reverse edges from forward `uses` without writing back to registry."""

    entry_ids = {
        str(entry.get("id", "")).strip()
        for entry in entries
        if str(entry.get("id", "")).strip()
    }
    used_by_map: dict[str, set[str]] = {entry_id: set() for entry_id in entry_ids}
    for entry in entries:
        entry_id = str(entry.get("id", "")).strip()
        if not entry_id:
            continue
        for target_id in _normalize_list(entry.get("uses")):
            if target_id in used_by_map:
                used_by_map[target_id].add(entry_id)
    return used_by_map


def collect_fr_uses_findings(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> list[dict[str, Any]]:
    repo_root_path = _resolve_project_root(repo_root)
    registry_path_obj = Path(registry_path)
    if not registry_path_obj.is_absolute():
        registry_path_obj = (repo_root_path / registry_path_obj).resolve()
    registry_rel = _normalize_path(registry_path_obj, repo_root_path)
    entries = _load_registry_entries(registry_path_obj, repo_root_path)
    id_set = {
        str(entry.get("id", "")).strip()
        for entry in entries
        if str(entry.get("id", "")).strip()
    }
    used_by_map = build_reverse_used_by_index(entries)

    findings: list[dict[str, Any]] = []
    for entry in entries:
        entry_id = str(entry.get("id", "")).strip()
        if not entry_id:
            continue
        for target_id in _normalize_list(entry.get("uses")):
            if target_id not in id_set:
                findings.append(
                    {
                        "entry_id": entry_id,
                        "target_id": target_id,
                        "kind": "missing_uses_target",
                        "severity": "P1",
                        "path": registry_rel,
                        "message": f"{entry_id} uses -> {target_id} が registry に存在しない",
                        "remediation": "functional-registry.yaml に uses 先 entry を追加するか uses 参照を削除する",
                    }
                )
        if "used_by" not in entry:
            continue

        expected_used_by = used_by_map.get(entry_id, set())
        actual_used_by = set(_normalize_list(entry.get("used_by")))
        if actual_used_by != expected_used_by:
            findings.append(
                {
                    "entry_id": entry_id,
                    "target_id": entry_id,
                    "kind": "reverse_reference_drift",
                    "severity": "P1",
                    "path": registry_rel,
                    "message": (
                        f"{entry_id} used_by が derived reverse と不一致 "
                        f"(expected={sorted(expected_used_by)}, actual={sorted(actual_used_by)})"
                    ),
                    "remediation": (
                        "used_by を削除して forward uses を正本にするか、"
                        "手書き used_by を derived reverse と一致させる"
                    ),
                }
            )
    return sorted(findings, key=lambda item: (item["entry_id"], item["target_id"], item["kind"]))


def check_fr_uses(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    gate: bool = False,
    upstream: str | None = None,
) -> dict[str, Any]:
    repo_root_path = _resolve_project_root(repo_root)
    registry_path_obj = Path(registry_path)
    if not registry_path_obj.is_absolute():
        registry_path_obj = (repo_root_path / registry_path_obj).resolve()
    registry_rel = _normalize_path(registry_path_obj, repo_root_path)
    findings = collect_fr_uses_findings(repo_root=repo_root_path, registry_path=registry_path_obj)

    blocking_findings = [
        finding
        for finding in findings
        if finding["kind"] in {"missing_uses_target", "reverse_reference_drift"}
    ]
    warning_findings: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "check_name": "check_fr_uses",
        "mode": "gate" if gate else "advisory",
        "exit_code": 0,
        "clean": not findings,
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking_findings),
        "warning_count": len(warning_findings),
        "findings": findings,
        "blocking_findings": blocking_findings,
        "warning_findings": warning_findings,
        "source_status": "not_applicable",
        "skipped_reason": None,
    }
    if not gate:
        return report

    changed_payload = changed_files(upstream=upstream)
    source_status = str(changed_payload["source_status"])
    report["source_status"] = source_status
    if source_status == "available_empty":
        report.update(
            {
                "clean": True,
                "finding_count": 0,
                "blocking_finding_count": 0,
                "warning_count": 0,
                "findings": [],
                "blocking_findings": [],
                "warning_findings": [],
            }
        )
        return report
    if source_status == "unavailable":
        report.update(
            {
                "clean": False,
                "finding_count": 0,
                "blocking_finding_count": 0,
                "warning_count": 0,
                "findings": [],
                "blocking_findings": [],
                "warning_findings": [],
                "skipped_reason": "changed-files unavailable",
            }
        )
        return report

    changed_paths = {_normalize_path(path, repo_root_path) for path in changed_payload["files"]}
    if registry_rel not in changed_paths:
        report.update(
            {
                "clean": True,
                "finding_count": 0,
                "blocking_finding_count": 0,
                "warning_count": 0,
                "findings": [],
                "blocking_findings": [],
                "warning_findings": [],
            }
        )
        return report

    report.update(
        {
            "clean": not blocking_findings,
            "exit_code": int(bool(blocking_findings)),
        }
    )
    return report


def collect_fr_uses_gate_summary(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    upstream: str | None = None,
) -> dict[str, Any]:
    report = check_fr_uses(
        repo_root=repo_root,
        registry_path=registry_path,
        gate=True,
        upstream=upstream,
    )
    return {
        "clean": report["clean"],
        "finding_count": report["finding_count"],
        "source_status": report["source_status"],
        "skipped_reason": report["skipped_reason"],
    }


def collect_fr_uses_full_required_summary(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    report = check_fr_uses(
        repo_root=repo_root,
        registry_path=registry_path,
        gate=False,
    )
    blocking_finding_count = int(report["blocking_finding_count"])
    warning_count = int(report["warning_count"])
    return {
        "clean": blocking_finding_count == 0,
        "finding_count": int(report["finding_count"]),
        "blocking_finding_count": blocking_finding_count,
        "warning_count": warning_count,
        "source_status": "full_required",
        "skipped_reason": None,
        "mode": "full_required",
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="functional-registry uses helper")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--registry-path", default=DEFAULT_REGISTRY_PATH, help="functional registry path")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    parser.add_argument("--gate", action="store_true", help="evaluate changed-files gate")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    report = check_fr_uses(
        repo_root=args.repo_root,
        registry_path=args.registry_path,
        gate=args.gate,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(report)
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
