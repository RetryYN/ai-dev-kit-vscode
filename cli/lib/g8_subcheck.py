from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

try:
    from .g7_subcheck import execute_test_file
except ImportError:  # pragma: no cover - direct script execution fallback
    from g7_subcheck import execute_test_file


IT_ROW_RE = re.compile(r"^\|\s*(IT-[A-Z0-9-]+)\s*\|")
IT_SEARCH_RE = re.compile(r"\b(IT-[A-Z0-9-]+)\b")
PATH_RE = re.compile(r"((?:cli|tests)/[A-Za-z0-9_./-]+\.(?:py|bats))")

L8_TEST_DESIGN_PATH = Path("docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md")
ANCHOR_MAP_REF = "cli/lib/g8_subcheck.py::G8_ANCHOR_MAP"

G8_ANCHOR_MAP: dict[str, list[str]] = {
    "IT-MOD-01": ["cli/tests/test-helix-routing.bats::IT-MOD-01"],
    "IT-MOD-02": [
        "cli/lib/tests/test_handover.py::IT-MOD-02",
        "cli/lib/tests/test_workspace_manager.py::IT-MOD-02",
    ],
    "IT-MOD-03": ["cli/tests/test-wsc-hooks-pretooluse-agent-and-design-guards.bats::IT-MOD-03"],
    "IT-MOD-04": ["cli/lib/tests/test_helix_db_v34_v35.py::IT-MOD-04"],
    "IT-MOD-05": ["cli/lib/tests/test_http_api_routes_push_pr.py::IT-MOD-05"],
    "IT-MOD-06": ["cli/lib/tests/test_integration_l45.py::IT-MOD-06"],
    "IT-MOD-07": [
        "cli/lib/tests/test_harness_monitor_integration.py::IT-MOD-07",
        "cli/tests/test-wsc-hook-sessionstart-harness-summary.bats::IT-MOD-07",
    ],
    "IT-IF-01": ["cli/tests/test-helix-routing.bats::IT-IF-01"],
    "IT-IF-02": [
        "cli/lib/tests/test_harness_monitor_integration.py::IT-IF-02",
        "cli/tests/test-wsc-hook-sessionstart-harness-summary.bats::IT-IF-02",
    ],
    "IT-IF-03": [
        "cli/lib/tests/test_http_api_routes_push_pr.py::IT-IF-03",
        "cli/lib/tests/test_http_api_routes_telemetry.py::IT-IF-03",
    ],
    "IT-IF-04": ["cli/lib/tests/test_helix_db_v34_v35.py::IT-IF-04"],
    "IT-IP-01": ["cli/tests/test-helix-routing.bats::IT-IP-01"],
    "IT-IP-02": ["cli/tests/test-wsc-hooks-pretooluse-agent-and-design-guards.bats::IT-IP-02"],
    "IT-IP-03": [
        "cli/lib/tests/test_handover.py::IT-IP-03",
        "cli/lib/tests/test_workspace_manager.py::IT-IP-03",
    ],
    "IT-IP-04": ["cli/lib/tests/test_helix_db_v34_v35.py::IT-IP-04"],
    "IT-IP-05": [
        "cli/lib/tests/test_http_api_routes_push_pr.py::IT-IP-05",
        "cli/lib/tests/test_integration_l45.py::IT-IP-05",
    ],
    "IT-DB-01": ["cli/lib/tests/test_workspace_manager.py::IT-DB-01"],
    "IT-DB-02": ["cli/lib/tests/test_http_api_routes_telemetry.py::IT-DB-02"],
    "IT-DB-03": ["cli/lib/tests/test_integration_l45.py::IT-DB-03"],
    "IT-DB-04": ["cli/lib/tests/test_workspace_manager.py::IT-DB-04"],
    "IT-DB-05": ["cli/lib/tests/test_integration_l45.py::IT-DB-05"],
}


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _parse_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _extract_source_paths(text: str) -> list[str]:
    return [item for item in dict.fromkeys(PATH_RE.findall(text))]


def load_it_inventory(project_root: Path) -> dict[str, dict[str, Any]]:
    doc_path = project_root / L8_TEST_DESIGN_PATH
    inventory: dict[str, dict[str, Any]] = {}
    for line_no, line in enumerate(doc_path.read_text(encoding="utf-8").splitlines(), start=1):
        match = IT_ROW_RE.match(line)
        if not match:
            continue
        it_id = match.group(1)
        cells = _parse_table_cells(line)
        source_cell = cells[-1] if cells else ""
        inventory[it_id] = {
            "doc_path": L8_TEST_DESIGN_PATH.as_posix(),
            "line_no": line_no,
            "cells": cells,
            "source_paths": _extract_source_paths(source_cell),
        }
    return inventory


def _scan_inline_anchors(project_root: Path) -> list[str]:
    anchored: set[str] = set()
    scan_roots = [project_root / "cli" / "lib" / "tests", project_root / "cli" / "tests", project_root / "tests"]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".bats"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            anchored.update(match.group(1) for match in IT_SEARCH_RE.finditer(text))
    return sorted(anchored)


def _split_anchor_spec(spec: str) -> tuple[str, str | None]:
    if "::" not in spec:
        return spec, None
    rel_path, needle = spec.split("::", 1)
    needle = needle.strip() or None
    return rel_path.strip(), needle


def _existing_anchor_paths(project_root: Path, specs: list[str]) -> list[str]:
    normalized: list[str] = []
    for spec in specs:
        rel_path, needle = _split_anchor_spec(spec)
        path = project_root / rel_path
        if not path.is_file():
            return []
        if not needle:
            return []
        text = path.read_text(encoding="utf-8", errors="ignore")
        if needle not in text:
            return []
        normalized.append(rel_path)
    return [item for item in dict.fromkeys(normalized)]


def _env_execute_tests_default() -> bool:
    return os.environ.get("HELIX_DOCTOR_SKIP_EXEC_TESTS") != "1"


def collect_g8_subcheck(
    project_root: Path | None = None,
    *,
    execute_tests: bool | None = None,
    test_runner: Callable[[Path, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    inventory = load_it_inventory(root)
    legacy_ids = [it_id for it_id in _scan_inline_anchors(root) if it_id in inventory]
    if execute_tests is None:
        execute_tests = _env_execute_tests_default()
    test_runner = test_runner or execute_test_file

    anchored_ids: list[str] = []
    missing_ids: list[str] = []
    unanchored_ids: list[str] = []
    unanchored_candidates: dict[str, list[str]] = {}
    execution_cache: dict[str, dict[str, Any]] = {}
    exec_pass_ids: list[str] = []

    for it_id in sorted(inventory):
        mapped_paths = _existing_anchor_paths(root, G8_ANCHOR_MAP.get(it_id, []))
        if mapped_paths:
            anchored_ids.append(it_id)
            file_results: list[dict[str, Any]] = []
            for rel_path in mapped_paths:
                if execute_tests and rel_path not in execution_cache:
                    execution_cache[rel_path] = test_runner(root, rel_path)
                if rel_path in execution_cache:
                    file_results.append(execution_cache[rel_path])
            if not execute_tests:
                exec_pass_ids.append(it_id)
            elif file_results and all(result["returncode"] == 0 for result in file_results):
                exec_pass_ids.append(it_id)
            continue

        candidates = [
            rel_path
            for rel_path in inventory[it_id]["source_paths"]
            if (root / rel_path).is_file()
        ]
        if candidates:
            unanchored_ids.append(it_id)
            unanchored_candidates[it_id] = candidates
        else:
            missing_ids.append(it_id)

    clean = (
        len(anchored_ids) == len(inventory)
        and not missing_ids
        and not unanchored_ids
        and len(exec_pass_ids) == len(anchored_ids)
    )
    return {
        "advisory": True,
        "exit_code": 0,
        "anchor_mechanism": "inline_python_ssot",
        "anchor_map": ANCHOR_MAP_REF,
        "it_total": len(inventory),
        "legacy_inline_anchors": {"count": len(legacy_ids), "ids": legacy_ids},
        "anchored": {"count": len(anchored_ids), "ids": anchored_ids},
        "exec_pass": {"count": len(exec_pass_ids), "ids": exec_pass_ids},
        "missing": {"count": len(missing_ids), "ids": missing_ids},
        "unanchored_but_exists": {
            "count": len(unanchored_ids),
            "ids": unanchored_ids,
            "candidates": unanchored_candidates,
        },
        "clean": clean,
        "test_results": execution_cache,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "G8 subcheck (advisory)",
        f"anchor_mechanism: {report['anchor_mechanism']}",
        f"anchor_map: {report['anchor_map']}",
        f"it_total: {report['it_total']}",
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
    parser = argparse.ArgumentParser(description="Advisory G8 subcheck detector.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="skip per-file test execution and treat anchors as structural only",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    execute_tests = False if args.no_exec else None
    report = collect_g8_subcheck(project_root=_project_root(), execute_tests=execute_tests)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
