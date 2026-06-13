from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


UT_ROW_RE = re.compile(r"^\|\s*(UT-[A-Z0-9-]+)\s*\|")
UT_SEARCH_RE = re.compile(r"\b(UT-[A-Z0-9-]+)\b")
HOOK_HINT_RE = re.compile(r"\.sh$")
DEFAULT_TEST_TIMEOUT_SECONDS = 120.0


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _default_anchor_map_path(root: Path) -> Path:
    return root / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml"


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("anchor map must be a mapping")
    return payload


def load_anchor_map(path: Path) -> dict[str, list[str]]:
    payload = _read_yaml(path)
    anchors = payload.get("anchors") or {}
    if not isinstance(anchors, dict):
        raise ValueError("anchors must be a mapping")

    normalized: dict[str, list[str]] = {}
    for ut_id, raw_tests in anchors.items():
        if not isinstance(ut_id, str):
            raise ValueError("anchor key must be a string")
        if isinstance(raw_tests, str):
            tests = [raw_tests]
        elif isinstance(raw_tests, list):
            tests = [str(item).strip() for item in raw_tests if str(item).strip()]
        else:
            raise ValueError(f"anchor value must be string or list: {ut_id}")
        normalized[ut_id.strip()] = tests
    return normalized


def _parse_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def load_ut_inventory(project_root: Path) -> dict[str, dict[str, Any]]:
    docs_root = project_root / "docs" / "v2" / "L7-test-design"
    inventory: dict[str, dict[str, Any]] = {}

    for doc_path in sorted(docs_root.glob("*.md")):
        for line_no, line in enumerate(doc_path.read_text(encoding="utf-8").splitlines(), start=1):
            match = UT_ROW_RE.match(line)
            if not match:
                continue
            ut_id = match.group(1)
            cells = _parse_table_cells(line)
            module_hint = ""
            if doc_path.name == "whole-source-coverage-単体テスト設計.md" and len(cells) >= 3:
                module_hint = cells[2]
            inventory[ut_id] = {
                "doc_path": doc_path.relative_to(project_root).as_posix(),
                "line_no": line_no,
                "cells": cells,
                "module_hint": module_hint,
            }
    return inventory


def _scan_legacy_inline_anchors(project_root: Path) -> list[str]:
    anchored: set[str] = set()
    scan_roots = [project_root / "cli" / "lib" / "tests", project_root / "cli" / "tests"]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in {".py", ".bats"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            anchored.update(match.group(1) for match in UT_SEARCH_RE.finditer(text))
    return sorted(anchored)


def _hook_candidate_map() -> dict[str, list[str]]:
    # Hook は cli/lib/tests + cli/tests の direct test のみ候補にする。
    # 下位 module の unit/integration test だけでは shell hook contract を
    # 過大主張しやすいため、indirect coverage は missing 扱いに倒す。
    return {
        "post-tool-use.sh": ["cli/lib/tests/test_audit_log.py"],
        "posttooluse-design-doc-web-search-revert.sh": [
            "cli/tests/test-wsc-hook-posttooluse-design-doc-web-search-revert.bats"
        ],
        "posttooluse-helix-job-enqueue.sh": ["cli/tests/test-wsc-hook-posttooluse-helix-job-enqueue.bats"],
        "posttooluse-plan-auto-register.sh": ["cli/tests/test-wsc-hook-posttooluse-plan-auto-register.bats"],
        "posttooluse-skill-catalog-rebuild.sh": ["cli/tests/test-wsc-hook-posttooluse-skill-catalog-rebuild.bats"],
        "precompact-state-snapshot.sh": ["cli/tests/test-wsc-hook-precompact-state-snapshot.bats"],
        "pretooluse-agent-fire.sh": [],
        "pretooluse-agent-guard.sh": [],
        "pretooluse-askuserquestion.sh": ["cli/lib/tests/test_pretooluse_askuserquestion.py"],
        "pretooluse-codex-slot-check.sh": [],
        "pretooluse-design-doc-web-search-guard.sh": [],
        "pretooluse-opus-repo-block.sh": ["cli/tests/test-wsc-hook-pretooluse-opus-repo-block.bats"],
        "sessionstart-harness-summary.sh": ["cli/tests/test-wsc-hook-sessionstart-harness-summary.bats"],
        "sessionstart-history-injection.sh": ["cli/tests/test-layer-4-5-integration.bats"],
        "stop-recovery-update.sh": ["cli/tests/test-wsc-hook-stop-recovery-update.bats"],
        "stop.sh": [
            "cli/lib/tests/test_session_telemetry.py",
            "cli/tests/test-helix-stop-hook-wiring.bats",
        ],
        "userpromptsubmit-context-bundle.sh": ["cli/tests/test-wsc-hook-userpromptsubmit-context-bundle.bats"],
    }


def _candidate_tests_for_module(project_root: Path, module_hint: str) -> list[str]:
    if not module_hint:
        return []

    if module_hint in _hook_candidate_map():
        return [
            rel_path
            for rel_path in _hook_candidate_map()[module_hint]
            if (project_root / rel_path).exists()
        ]

    if module_hint.endswith(".py"):
        stem = Path(module_hint).stem
        prefixes = [
            f"cli/lib/tests/test_{stem}.py",
            f"cli/lib/tests/test_{stem}_unit.py",
            f"cli/lib/tests/test_{stem}_integration.py",
        ]
        candidates = [path for path in prefixes if (project_root / path).exists()]
        if candidates:
            return candidates

    if HOOK_HINT_RE.search(module_hint):
        return []
    return []


def _normalize_anchor_paths(project_root: Path, test_paths: list[str]) -> list[str]:
    return [path for path in dict.fromkeys(test_paths) if (project_root / path).exists()]


def _runner_for_path(rel_path: str) -> list[str]:
    if rel_path.endswith(".py"):
        return [sys.executable, "-m", "pytest", rel_path, "-q"]
    if rel_path.endswith(".bats"):
        return ["bats", rel_path]
    raise ValueError(f"unsupported test runner for {rel_path}")


def _env_test_timeout_seconds() -> float | None:
    raw = os.environ.get("HELIX_G7_TEST_TIMEOUT_SECONDS")
    if raw is None:
        return DEFAULT_TEST_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError:
        return DEFAULT_TEST_TIMEOUT_SECONDS
    return timeout if timeout > 0 else None


def execute_test_file(project_root: Path, rel_path: str) -> dict[str, Any]:
    command = _runner_for_path(rel_path)
    timeout_seconds = _env_test_timeout_seconds()
    proc = subprocess.Popen(
        command,
        cwd=project_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_seconds)
        return {
            "runner": command[0],
            "command": command,
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False,
            "timeout_seconds": timeout_seconds,
        }
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = proc.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
        timeout_message = f"G7 subcheck test timed out after {timeout_seconds}s: {rel_path}"
        stderr = (stderr or "").rstrip()
        if stderr:
            stderr = f"{stderr}\n{timeout_message}\n"
        else:
            stderr = f"{timeout_message}\n"
        return {
            "runner": command[0],
            "command": command,
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "timeout_seconds": timeout_seconds,
        }


def _env_execute_tests_default() -> bool:
    return os.environ.get("HELIX_DOCTOR_SKIP_EXEC_TESTS") != "1"


def collect_g7_subcheck(
    project_root: Path | None = None,
    anchor_map_path: Path | None = None,
    *,
    execute_tests: bool | None = None,
    test_runner: Callable[[Path, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    anchor_path = anchor_map_path or _default_anchor_map_path(root)
    inventory = load_ut_inventory(root)
    anchors = load_anchor_map(anchor_path)
    legacy_ids = [ut_id for ut_id in _scan_legacy_inline_anchors(root) if ut_id in inventory]
    if execute_tests is None:
        execute_tests = _env_execute_tests_default()
    test_runner = test_runner or execute_test_file

    anchored_ids: list[str] = []
    missing_ids: list[str] = []
    unanchored_ids: list[str] = []
    unanchored_candidates: dict[str, list[str]] = {}
    execution_cache: dict[str, dict[str, Any]] = {}
    exec_pass_ids: list[str] = []

    for ut_id in sorted(inventory):
        mapped_paths = _normalize_anchor_paths(root, anchors.get(ut_id, []))
        if mapped_paths:
            anchored_ids.append(ut_id)
            file_results: list[dict[str, Any]] = []
            for rel_path in mapped_paths:
                if execute_tests and rel_path not in execution_cache:
                    execution_cache[rel_path] = test_runner(root, rel_path)
                if rel_path in execution_cache:
                    file_results.append(execution_cache[rel_path])
            if not execute_tests:
                exec_pass_ids.append(ut_id)
            elif file_results and all(result["returncode"] == 0 for result in file_results):
                exec_pass_ids.append(ut_id)
            continue

        candidates = _candidate_tests_for_module(root, str(inventory[ut_id].get("module_hint", "")))
        if candidates:
            unanchored_ids.append(ut_id)
            unanchored_candidates[ut_id] = candidates
        else:
            missing_ids.append(ut_id)

    return {
        "advisory": True,
        "exit_code": 0,
        "anchor_mechanism": "yaml_ssot",
        "anchor_map": anchor_path.relative_to(root).as_posix(),
        "ut_total": len(inventory),
        "legacy_inline_anchors": {"count": len(legacy_ids), "ids": legacy_ids},
        "anchored": {"count": len(anchored_ids), "ids": anchored_ids},
        "exec_pass": {"count": len(exec_pass_ids), "ids": exec_pass_ids},
        "missing": {"count": len(missing_ids), "ids": missing_ids},
        "unanchored_but_exists": {
            "count": len(unanchored_ids),
            "ids": unanchored_ids,
            "candidates": unanchored_candidates,
        },
        "test_results": execution_cache,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "G7 subcheck (advisory)",
        f"anchor_mechanism: {report['anchor_mechanism']}",
        f"anchor_map: {report['anchor_map']}",
        f"ut_total: {report['ut_total']}",
        f"legacy_inline_anchors: {report['legacy_inline_anchors']['count']}",
        f"anchored: {report['anchored']['count']}",
        f"exec_pass: {report['exec_pass']['count']}",
        f"missing: {report['missing']['count']}",
        f"unanchored_but_exists: {report['unanchored_but_exists']['count']}",
    ]
    if report["missing"]["ids"]:
        lines.append("missing_ids: " + ", ".join(report["missing"]["ids"]))
    if report["unanchored_but_exists"]["ids"]:
        lines.append("unanchored_ids: " + ", ".join(report["unanchored_but_exists"]["ids"]))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advisory G7 subcheck detector.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="skip per-file test execution and treat anchors as structural only",
    )
    parser.add_argument("--anchor-map", help="override YAML anchor map path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = _project_root()
    anchor_map_path = Path(args.anchor_map).expanduser().resolve() if args.anchor_map else None
    report = collect_g7_subcheck(
        project_root=root,
        anchor_map_path=anchor_map_path,
        execute_tests=not args.no_exec,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
