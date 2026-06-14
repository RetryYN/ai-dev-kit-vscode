from __future__ import annotations

"""Plan dependency gate wrapper with baseline + changed-files ratchet.

`cli/lib/vg_overview.py` already consumes
`collect_plan_dependency_gate_summary()` via `required_clean`.
"""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Sequence

import plan_validator
from changed_files import changed_files


DEFAULT_BASELINE_PATH = "cli/config/plan-dependency-baseline.json"
_WARNING_RE = re.compile(r"^WARN \[(?P<plan_id>[^\]]+)\] field=(?P<field>\S+) reason=(?P<reason>.+)$")


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


def fingerprint_dependency_warning(plan_id: str, field: str, reason: str) -> str:
    raw = f"{plan_id}|{field}|{reason}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _classify_warning(field: str, reason: str) -> str:
    if field == "dependencies" and reason.startswith("cycle detected:"):
        return "cycle"
    if field == "dependencies.blocks" and " does not require " in reason:
        return "missing_reciprocal"
    return "other"


def _list_plan_files(project_root: Path) -> list[Path]:
    plans_root = project_root / "docs" / "plans"
    if not plans_root.is_dir():
        return []
    return sorted(path.resolve() for path in plans_root.rglob("*.md"))


def _collect_plan_warnings(path: Path, repo_root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    try:
        payload = plan_validator.load_frontmatter(path)
        frontmatter = plan_validator.parse_frontmatter(payload)
    except Exception as exc:
        plan_id = path.stem
        field = "frontmatter"
        reason = str(exc)
        findings.append(
            {
                "plan_id": plan_id,
                "path": _normalize_path(path, repo_root),
                "field": field,
                "reason": reason,
                "kind": "other",
                "fingerprint": fingerprint_dependency_warning(plan_id, field, reason),
            }
        )
        return findings

    warnings: list[str] = []
    plan_validator.validate_dependencies(path, frontmatter, warnings)
    for warning in warnings:
        match = _WARNING_RE.match(warning)
        if not match:
            continue
        plan_id = match.group("plan_id")
        field = match.group("field")
        reason = match.group("reason")
        findings.append(
            {
                "plan_id": plan_id,
                "path": _normalize_path(path, repo_root),
                "field": field,
                "reason": reason,
                "kind": _classify_warning(field, reason),
                "fingerprint": fingerprint_dependency_warning(plan_id, field, reason),
            }
        )
    return findings


def collect_plan_dependency_findings(
    *,
    repo_root: str | Path | None = None,
) -> list[dict[str, object]]:
    repo_root_path = _resolve_project_root(repo_root)
    findings: list[dict[str, object]] = []
    for path in _list_plan_files(repo_root_path):
        findings.extend(_collect_plan_warnings(path, repo_root_path))
    return sorted(
        findings,
        key=lambda item: (
            str(item["path"]),
            str(item["plan_id"]),
            str(item["field"]),
            str(item["reason"]),
        ),
    )


def _load_baseline_fingerprints(baseline_path: str | Path, repo_root: Path) -> set[str]:
    path = Path(baseline_path).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    fingerprints: set[str] = set()
    for finding in payload.get("accepted_dependency_warning", []):
        fingerprint = str(finding.get("fingerprint", "")).strip()
        if fingerprint:
            fingerprints.add(fingerprint)
            continue
        plan_id = str(finding.get("plan_id", "")).strip()
        field = str(finding.get("field", "")).strip()
        reason = str(finding.get("reason", "")).strip()
        if plan_id and field and reason:
            fingerprints.add(fingerprint_dependency_warning(plan_id, field, reason))
    return fingerprints


def _filter_changed_plan_findings(
    findings: list[dict[str, object]],
    changed: list[str],
    repo_root: Path,
) -> list[dict[str, object]]:
    changed_paths = {
        _normalize_path(path, repo_root)
        for path in changed
        if str(path).startswith("docs/plans/") and str(path).endswith(".md")
    }
    if not changed_paths:
        return []
    return [finding for finding in findings if finding["path"] in changed_paths]


def check_plan_dependency_gate(
    *,
    repo_root: str | Path | None = None,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    gate: bool = False,
    upstream: str | None = None,
) -> dict[str, object]:
    repo_root_path = _resolve_project_root(repo_root)
    findings = collect_plan_dependency_findings(repo_root=repo_root_path)
    baseline_fingerprints = _load_baseline_fingerprints(baseline_path, repo_root_path)
    advisory_new = [finding for finding in findings if finding["fingerprint"] not in baseline_fingerprints]

    report: dict[str, object] = {
        "check_name": "check_plan_dependency_gate",
        "mode": "gate" if gate else "advisory",
        "exit_code": 0,
        "clean": not findings,
        "finding_count": len(findings),
        "new_finding_count": len(advisory_new),
        "blocking_finding_count": sum(1 for finding in findings if finding["kind"] in {"cycle", "missing_reciprocal"}),
        "findings": findings,
        "new_findings": advisory_new,
        "blocking_findings": [finding for finding in findings if finding["kind"] in {"cycle", "missing_reciprocal"}],
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
                "new_finding_count": 0,
                "blocking_finding_count": 0,
                "findings": [],
                "new_findings": [],
                "blocking_findings": [],
            }
        )
        return report
    if source_status == "unavailable":
        report.update(
            {
                "clean": False,
                "finding_count": 0,
                "new_finding_count": 0,
                "blocking_finding_count": 0,
                "findings": [],
                "new_findings": [],
                "blocking_findings": [],
                "skipped_reason": "changed-files unavailable",
            }
        )
        return report

    changed_findings = _filter_changed_plan_findings(findings, list(changed_payload["files"]), repo_root_path)
    new_findings = [
        finding for finding in changed_findings if finding["fingerprint"] not in baseline_fingerprints
    ]
    new_blocking_findings = [
        finding for finding in new_findings if finding["kind"] in {"cycle", "missing_reciprocal"}
    ]
    report.update(
        {
            "clean": not new_blocking_findings,
            "exit_code": int(bool(new_blocking_findings)),
            "finding_count": len(changed_findings),
            "new_finding_count": len(new_findings),
            "blocking_finding_count": len(new_blocking_findings),
            "findings": changed_findings,
            "new_findings": new_findings,
            "blocking_findings": new_blocking_findings,
        }
    )
    return report


def collect_plan_dependency_gate_summary(
    *,
    repo_root: str | Path | None = None,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    upstream: str | None = None,
) -> dict[str, object]:
    report = check_plan_dependency_gate(
        repo_root=repo_root,
        baseline_path=baseline_path,
        gate=True,
        upstream=upstream,
    )
    return {
        "clean": report["clean"],
        "finding_count": report["finding_count"],
        "source_status": report["source_status"],
        "skipped_reason": report["skipped_reason"],
    }


def build_plan_dependency_baseline_payload(
    *,
    repo_root: str | Path | None = None,
    generated_by: str = "plan_dependency_gate.py --write-baseline",
) -> dict[str, object]:
    findings = collect_plan_dependency_findings(repo_root=repo_root)
    return {
        "intentional_baseline": True,
        "owner": "codex",
        "created": "2026-06-14",
        "expiry": "2026-09-12",
        "generated_by": generated_by,
        "accepted_dependency_warning": findings,
    }


def write_plan_dependency_baseline(
    output_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    generated_by: str = "plan_dependency_gate.py --write-baseline",
) -> Path:
    payload = build_plan_dependency_baseline_payload(
        repo_root=repo_root,
        generated_by=generated_by,
    )
    repo_root_path = _resolve_project_root(repo_root)
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = (repo_root_path / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="plan dependency gate helper")
    parser.add_argument("--write-baseline", action="store_true", help="write the current warnings as baseline")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--output", default=DEFAULT_BASELINE_PATH, help="baseline output path")
    parser.add_argument(
        "--generated-by",
        default="plan_dependency_gate.py --write-baseline",
        help="baseline generated_by metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if not args.write_baseline:
        parser.error("no action requested")
    output_path = write_plan_dependency_baseline(
        args.output,
        repo_root=args.repo_root,
        generated_by=args.generated_by,
    )
    print(output_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
