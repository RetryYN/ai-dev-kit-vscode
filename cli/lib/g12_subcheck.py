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


AT_ROW_RE = re.compile(r"^\|\s*(AT-[0-9]+)\s*\|")
AT_SEARCH_RE = re.compile(r"\b(AT-[0-9]+)\b")

L12_TEST_DESIGN_PATH = Path(
    "docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md"
)
ANCHOR_MAP_REF = "cli/lib/g12_subcheck.py::G12_ANCHOR_MAP"

# Each anchor below was verified against an existing test that genuinely executes
# the scenario and asserts the acceptance surface. Anything weaker stays missing.
G12_ANCHOR_MAP: dict[str, list[str]] = {
    # AT-17: `helix gate G2 --static-only` keeps static PASS in warning mode, then
    # fail-closes in enforce mode when readiness findings remain open.
    "AT-17": ["cli/tests/test-helix-gate-readiness.bats::AT-17"],
    # AT-29: the functional-registry detector executes and asserts invalid trace,
    # duplicate ID, missing path, and unregistered asset findings.
    "AT-29": ["cli/lib/tests/test_functional_registry_checks.py::AT-29"],
    # AT-30: the glossary detector executes and asserts drift, duplicates, and
    # missing/invalid glossary fields from concept/registry mismatch.
    "AT-30": ["cli/lib/tests/test_ddd_registry_checks.py::AT-30"],
    # AT-50: `helix-push --gate` executes the secret gate and asserts `G-secret`
    # passes in a clean repo before push is allowed to continue.
    "AT-50": ["cli/tests/helix-push.bats::AT-50"],
    # AT-53: raw `git push` and raw `codex exec` are blocked, and `helix-codex`
    # rejects write execution without explicit approval evidence.
    "AT-53": [
        "cli/lib/tests/test_llm_guard.py::AT-53",
        "cli/tests/test-helix-codex.bats::AT-53",
    ],
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


def load_at_inventory(project_root: Path) -> dict[str, dict[str, Any]]:
    doc_path = project_root / L12_TEST_DESIGN_PATH
    inventory: dict[str, dict[str, Any]] = {}
    for line_no, line in enumerate(doc_path.read_text(encoding="utf-8").splitlines(), start=1):
        match = AT_ROW_RE.match(line)
        if not match:
            continue
        at_id = match.group(1)
        cells = _parse_table_cells(line)
        inventory[at_id] = {
            "doc_path": L12_TEST_DESIGN_PATH.as_posix(),
            "line_no": line_no,
            "cells": cells,
            "requirement_id": cells[1] if len(cells) > 1 else "",
            "scenario": cells[2] if len(cells) > 2 else "",
            "acceptance": cells[3] if len(cells) > 3 else "",
            "priority": cells[4] if len(cells) > 4 else "",
        }
    return inventory


def _scan_inline_anchors(project_root: Path) -> list[str]:
    anchored: set[str] = set()
    scan_roots = [
        project_root / "cli" / "lib" / "tests",
        project_root / "cli" / "tests",
        project_root / "tests",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".bats"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            anchored.update(match.group(1) for match in AT_SEARCH_RE.finditer(text))
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
        if re.search(r"\b" + re.escape(needle) + r"\b", text) is None:
            return []
        normalized.append(rel_path)
    return [item for item in dict.fromkeys(normalized)]


def _candidate_anchor_paths(project_root: Path, specs: list[str]) -> list[str]:
    candidates: list[str] = []
    for spec in specs:
        rel_path, _needle = _split_anchor_spec(spec)
        if (project_root / rel_path).is_file():
            candidates.append(rel_path)
    return [item for item in dict.fromkeys(candidates)]


def _env_execute_tests_default() -> bool:
    return os.environ.get("HELIX_DOCTOR_SKIP_EXEC_TESTS") != "1"


def collect_g12_subcheck(
    project_root: Path | None = None,
    *,
    execute_g7_tests: bool | None = None,
    test_runner: Callable[[Path, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    inventory = load_at_inventory(root)
    if execute_g7_tests is None:
        execute_g7_tests = _env_execute_tests_default()
    test_runner = test_runner or execute_test_file

    legacy_ids = [at_id for at_id in _scan_inline_anchors(root) if at_id in inventory]
    anchored_ids: list[str] = []
    exec_pass_ids: list[str] = []
    missing_ids: list[str] = []
    unanchored_ids: list[str] = []
    unanchored_candidates: dict[str, list[str]] = {}
    execution_cache: dict[str, dict[str, Any]] = {}

    for at_id in sorted(inventory):
        specs = G12_ANCHOR_MAP.get(at_id, [])
        mapped_paths = _existing_anchor_paths(root, specs)
        if mapped_paths:
            anchored_ids.append(at_id)
            file_results: list[dict[str, Any]] = []
            for rel_path in mapped_paths:
                if execute_g7_tests and rel_path not in execution_cache:
                    execution_cache[rel_path] = test_runner(root, rel_path)
                if rel_path in execution_cache:
                    file_results.append(execution_cache[rel_path])
            if not execute_g7_tests:
                exec_pass_ids.append(at_id)
            elif file_results and all(result["returncode"] == 0 for result in file_results):
                exec_pass_ids.append(at_id)
            continue

        candidates = _candidate_anchor_paths(root, specs)
        if candidates:
            unanchored_ids.append(at_id)
            unanchored_candidates[at_id] = candidates
        else:
            missing_ids.append(at_id)

    passed = (
        len(anchored_ids) == len(inventory)
        and len(exec_pass_ids) == len(anchored_ids)
        and not missing_ids
    )
    return {
        "advisory": True,
        "exit_code": 0,
        "anchor_mechanism": "inline_python_ssot",
        "anchor_map": ANCHOR_MAP_REF,
        "implemented": True,
        "passed": passed,
        "at_total": len(inventory),
        "gap_count": len(inventory) - len(anchored_ids),
        "legacy_inline_anchors": {"count": len(legacy_ids), "ids": legacy_ids},
        "anchored": {"count": len(anchored_ids), "ids": anchored_ids},
        "exec_pass": {"count": len(exec_pass_ids), "ids": exec_pass_ids},
        "unanchored_but_exists": {
            "count": len(unanchored_ids),
            "ids": unanchored_ids,
            "candidates": unanchored_candidates,
        },
        "missing": {"count": len(missing_ids), "ids": missing_ids},
        "test_results": execution_cache,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "G12 subcheck (advisory)",
        f"anchor_mechanism: {report['anchor_mechanism']}",
        f"anchor_map: {report['anchor_map']}",
        f"implemented: {str(report['implemented']).lower()}",
        f"passed: {str(report['passed']).lower()}",
        f"at_total: {report['at_total']}",
        f"anchored: {report['anchored']['count']}",
        f"exec_pass: {report['exec_pass']['count']}",
        f"missing: {report['missing']['count']}",
        f"unanchored_but_exists: {report['unanchored_but_exists']['count']}",
        f"gap_count: {report['gap_count']}",
    ]
    if report["missing"]["ids"]:
        lines.append("missing_ids: " + ", ".join(report["missing"]["ids"]))
    if report["unanchored_but_exists"]["ids"]:
        lines.append("unanchored_ids: " + ", ".join(report["unanchored_but_exists"]["ids"]))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advisory G12 subcheck detector.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-exec",
        action="store_true",
        help="skip per-file test execution and treat anchors as structural only",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    execute_g7_tests = False if args.no_exec else None
    report = collect_g12_subcheck(
        project_root=_project_root(),
        execute_g7_tests=execute_g7_tests,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
