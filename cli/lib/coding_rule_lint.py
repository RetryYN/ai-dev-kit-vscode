from __future__ import annotations

"""Mechanical coding rule lint wrapper with baseline + changed-files ratchet.

`cli/lib/vg_overview.py` already consumes
`collect_coding_rule_lint_gate_summary()` via `required_clean`.
"""

import argparse
import hashlib
import json
import os
import py_compile
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

from changed_files import changed_files
from registry_checks import _coerce_entry_rows, _load_yaml_payload


DEFAULT_REGISTRY_PATH = "cli/config/coding-rule-registry.yaml"
DEFAULT_BASELINE_PATH = "cli/config/coding-rule-registry-baseline.json"
CORE_REQUIRED_TOOLS = frozenset({"bash_n", "py_compile"})


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


def _first_line(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.readline().strip()
    except OSError:
        return ""


def _is_bash_script(path: Path) -> bool:
    return path.suffix == ".sh" or "bash" in _first_line(path)


def _walk_repo_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "__pycache__"} for part in path.parts):
            continue
        files.append(path.resolve())
    return sorted(files)


def _list_repo_files(repo_root: Path) -> list[Path]:
    try:
        tracked_proc = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        untracked_proc = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return _walk_repo_files(repo_root)

    if tracked_proc.returncode != 0 or untracked_proc.returncode != 0:
        return _walk_repo_files(repo_root)
    files = {
        (repo_root / line.strip()).resolve()
        for proc in (tracked_proc, untracked_proc)
        for line in proc.stdout.splitlines()
        if line.strip()
    }
    return sorted(files)


def _load_registry_tool_map(registry_path: str | Path) -> dict[str, str]:
    path = Path(registry_path).expanduser().resolve()
    payload = _load_yaml_payload(path.read_text(encoding="utf-8"))
    tool_map: dict[str, str] = {}
    for row in _coerce_entry_rows(payload):
        raw_tools = row.get("linter_tool")
        if raw_tools is None:
            continue
        if isinstance(raw_tools, list):
            tools = [str(item).strip() for item in raw_tools if str(item).strip()]
        else:
            tool = str(raw_tools).strip()
            tools = [tool] if tool else []
        for tool in tools:
            tool_map[tool] = str(row.get("id", "")).strip()
    return tool_map


def _build_violation(rule_id: str, file: str, line: int, tool: str, message: str) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "file": file,
        "line": max(1, int(line or 1)),
        "tool": tool,
        "message": message.strip() or f"{tool} violation",
    }


def fingerprint_violation(violation: dict[str, Any]) -> str:
    raw = "|".join(
        str(violation.get(field, ""))
        for field in ("rule_id", "file", "line", "tool", "message")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _decorate_violation(violation: dict[str, Any]) -> dict[str, Any]:
    payload = dict(violation)
    payload["fingerprint"] = fingerprint_violation(payload)
    return payload


def _bash_n_violation(path: Path, repo_root: Path, rule_id: str) -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["bash", "-n", path.as_posix()],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode == 0:
        return []
    stderr = (proc.stderr or proc.stdout).strip()
    line = 1
    message = "bash -n failed"
    for raw_line in stderr.splitlines():
        if "line " in raw_line:
            number = raw_line.split("line ", 1)[1].split(":", 1)[0].strip()
            if number.isdigit():
                line = int(number)
        if "syntax error" in raw_line:
            message = raw_line.split(":", 2)[-1].strip()
            break
    return [_build_violation(rule_id, _normalize_path(path, repo_root), line, "bash_n", message)]


def _py_compile_violation(path: Path, repo_root: Path, rule_id: str) -> list[dict[str, Any]]:
    try:
        py_compile.compile(path.as_posix(), doraise=True)
        return []
    except py_compile.PyCompileError as exc:
        message = str(exc)
        line = 1
        normalized_message = "py_compile failed"
        for raw_line in message.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("File ") and ", line " in stripped:
                number = stripped.split(", line ", 1)[1].split(",", 1)[0].strip()
                if number.isdigit():
                    line = int(number)
            if "SyntaxError:" in stripped:
                normalized_message = stripped.split("SyntaxError:", 1)[1].strip()
        return [_build_violation(rule_id, _normalize_path(path, repo_root), line, "py_compile", normalized_message)]


def _ruff_violations(paths: list[Path], repo_root: Path, rule_id: str) -> list[dict[str, Any]]:
    if not paths or shutil.which("ruff") is None:
        return []
    proc = subprocess.run(
        ["ruff", "check", "--output-format", "json", *[path.as_posix() for path in paths]],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode not in {0, 1}:
        return []
    payload = json.loads(proc.stdout or "[]")
    return [
        _build_violation(
            rule_id,
            _normalize_path(item["filename"], repo_root),
            item.get("location", {}).get("row", 1),
            "ruff",
            item.get("message", "ruff violation"),
        )
        for item in payload
    ]


def _shellcheck_violations(paths: list[Path], repo_root: Path, rule_id: str) -> list[dict[str, Any]]:
    if not paths or shutil.which("shellcheck") is None:
        return []
    proc = subprocess.run(
        ["shellcheck", "-f", "json", *[path.as_posix() for path in paths]],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode not in {0, 1}:
        return []
    payload = json.loads(proc.stdout or "[]")
    return [
        _build_violation(
            rule_id,
            _normalize_path(item.get("file", ""), repo_root),
            item.get("line", 1),
            "shellcheck",
            item.get("message", "shellcheck violation"),
        )
        for item in payload
    ]


def collect_violations(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> list[dict[str, Any]]:
    repo_root_path = _resolve_project_root(repo_root)
    registry_path_obj = Path(registry_path)
    if not registry_path_obj.is_absolute():
        registry_path_obj = (repo_root_path / registry_path_obj).resolve()
    tool_map = _load_registry_tool_map(registry_path_obj)
    files = _list_repo_files(repo_root_path)
    python_files = [path for path in files if path.suffix == ".py"]
    shell_files = [path for path in files if _is_bash_script(path)]

    findings: list[dict[str, Any]] = []
    bash_rule_id = tool_map.get("bash_n")
    if bash_rule_id:
        for path in shell_files:
            findings.extend(_bash_n_violation(path, repo_root_path, bash_rule_id))

    py_rule_id = tool_map.get("py_compile")
    if py_rule_id:
        for path in python_files:
            findings.extend(_py_compile_violation(path, repo_root_path, py_rule_id))

    ruff_rule_id = tool_map.get("ruff")
    if ruff_rule_id:
        findings.extend(_ruff_violations(python_files, repo_root_path, ruff_rule_id))

    shellcheck_rule_id = tool_map.get("shellcheck")
    if shellcheck_rule_id:
        findings.extend(_shellcheck_violations(shell_files, repo_root_path, shellcheck_rule_id))

    decorated = [_decorate_violation(finding) for finding in findings]
    return sorted(
        decorated,
        key=lambda item: (
            str(item["file"]),
            int(item["line"]),
            str(item["tool"]),
            str(item["rule_id"]),
            str(item["message"]),
        ),
    )


def _load_baseline_fingerprints(baseline_path: str | Path) -> set[str]:
    path = Path(baseline_path).expanduser()
    if not path.is_absolute():
        path = (_resolve_project_root() / path).resolve()
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    fingerprints: set[str] = set()
    for report in payload.get("reports", []):
        for finding in report.get("findings", []):
            fingerprint = str(finding.get("fingerprint", "")).strip()
            if fingerprint:
                fingerprints.add(fingerprint)
                continue
            fingerprints.add(
                fingerprint_violation(
                    {
                        "rule_id": finding.get("rule_id"),
                        "file": finding.get("file"),
                        "line": finding.get("line"),
                        "tool": finding.get("tool"),
                        "message": finding.get("message"),
                    }
                )
            )
    return fingerprints


def _filter_changed_findings(
    findings: list[dict[str, Any]],
    changed: Iterable[str],
    repo_root: Path,
) -> list[dict[str, Any]]:
    changed_paths = {_normalize_path(path, repo_root) for path in changed}
    return [finding for finding in findings if finding["file"] in changed_paths]


def evaluate_coding_rule_lint(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    gate: bool = False,
    upstream: str | None = None,
) -> dict[str, Any]:
    repo_root_path = _resolve_project_root(repo_root)
    findings = collect_violations(repo_root=repo_root_path, registry_path=registry_path)
    baseline_path_obj = Path(baseline_path)
    if not baseline_path_obj.is_absolute():
        baseline_path_obj = (repo_root_path / baseline_path_obj).resolve()
    baseline_fingerprints = _load_baseline_fingerprints(baseline_path_obj)
    advisory_new = [finding for finding in findings if finding["fingerprint"] not in baseline_fingerprints]

    report = {
        "check_name": "check_coding_rule_lint",
        "mode": "gate" if gate else "advisory",
        "exit_code": 0,
        "clean": not findings,
        "finding_count": len(findings),
        "new_finding_count": len(advisory_new),
        "findings": findings,
        "new_findings": advisory_new,
        "source_status": "not_applicable",
        "skipped_reason": None,
    }
    if not gate:
        return report

    changed_payload = changed_files(upstream=upstream)
    source_status = str(changed_payload["source_status"])
    report["source_status"] = source_status
    if source_status == "available_empty":
        report["clean"] = True
        report["findings"] = []
        report["new_findings"] = []
        report["finding_count"] = 0
        report["new_finding_count"] = 0
        return report
    if source_status == "unavailable":
        report["clean"] = False
        report["skipped_reason"] = "changed-files unavailable"
        report["findings"] = []
        report["new_findings"] = []
        report["finding_count"] = 0
        report["new_finding_count"] = 0
        return report

    changed_findings = _filter_changed_findings(findings, changed_payload["files"], repo_root_path)
    new_findings = [finding for finding in changed_findings if finding["fingerprint"] not in baseline_fingerprints]
    report["findings"] = changed_findings
    report["new_findings"] = new_findings
    report["finding_count"] = len(changed_findings)
    report["new_finding_count"] = len(new_findings)
    report["clean"] = not new_findings
    report["exit_code"] = int(bool(new_findings))
    return report


def collect_coding_rule_lint_gate_summary(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    upstream: str | None = None,
) -> dict[str, Any]:
    report = evaluate_coding_rule_lint(
        repo_root=repo_root,
        registry_path=registry_path,
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


def collect_coding_rule_lint_full_required_summary(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
) -> dict[str, Any]:
    findings = collect_violations(repo_root=repo_root, registry_path=registry_path)
    blocking_findings = [
        finding for finding in findings if str(finding.get("tool", "")) in CORE_REQUIRED_TOOLS
    ]
    warning_count = len(findings) - len(blocking_findings)
    return {
        "clean": len(blocking_findings) == 0,
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking_findings),
        "warning_count": warning_count,
        "source_status": "full_required",
        "skipped_reason": None,
        "mode": "core_full_required",
    }


def build_coding_rule_lint_baseline_payload(
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    owner: str = "codex",
    created: str | None = None,
    expiry: str | None = None,
    expiry_days: int = 90,
    generated_by: str = "coding_rule_lint.py --write-baseline",
) -> dict[str, Any]:
    repo_root_path = _resolve_project_root(repo_root)
    created_date = date.fromisoformat(created) if created else date.today()
    expiry_date = date.fromisoformat(expiry) if expiry else created_date + timedelta(days=expiry_days)
    findings = collect_violations(repo_root=repo_root_path, registry_path=registry_path)
    return {
        "intentional_baseline": True,
        "owner": owner,
        "created": created_date.isoformat(),
        "expiry": expiry_date.isoformat(),
        "generated_by": generated_by,
        "reports": [
            {
                "check_name": "check_coding_rule_lint",
                "mode": "advisory",
                "findings": findings,
                "metrics": {
                    "finding_count": len(findings),
                    "tools": sorted({finding["tool"] for finding in findings}),
                },
            }
        ],
    }


def write_coding_rule_lint_baseline(
    output_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    owner: str = "codex",
    created: str | None = None,
    expiry: str | None = None,
    expiry_days: int = 90,
    generated_by: str = "coding_rule_lint.py --write-baseline",
) -> Path:
    payload = build_coding_rule_lint_baseline_payload(
        repo_root=repo_root,
        registry_path=registry_path,
        owner=owner,
        created=created,
        expiry=expiry,
        expiry_days=expiry_days,
        generated_by=generated_by,
    )
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = (_resolve_project_root(repo_root) / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="coding rule lint helper")
    parser.add_argument("--write-baseline", action="store_true", help="write the current lint findings as baseline")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--registry-path", default=DEFAULT_REGISTRY_PATH, help="coding rule registry path")
    parser.add_argument("--output", default=DEFAULT_BASELINE_PATH, help="baseline output path")
    parser.add_argument("--owner", default="codex", help="baseline owner metadata")
    parser.add_argument("--created", default=None, help="baseline creation date (YYYY-MM-DD)")
    parser.add_argument("--expiry", default=None, help="baseline expiry date (YYYY-MM-DD)")
    parser.add_argument("--expiry-days", type=int, default=90, help="expiry offset when --expiry is omitted")
    parser.add_argument("--generated-by", default="coding_rule_lint.py --write-baseline", help="baseline generated_by metadata")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if not args.write_baseline:
        parser.error("no action requested")
    output_path = write_coding_rule_lint_baseline(
        args.output,
        repo_root=args.repo_root,
        registry_path=args.registry_path,
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
