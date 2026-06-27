#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_contains(path: str, needle: str) -> None:
    text = read(path)
    require(needle in text, f"{path} missing {needle!r}")


def count_pattern(path: str, pattern: str) -> int:
    return len(re.findall(pattern, read(path), flags=re.MULTILINE))


def parse_progress_rows(text: str) -> dict[int, str]:
    rows: dict[int, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\|\s*(\d+)\s*\|(?:[^|]*\|){3}\s*([^|]+?)\s*\|$", line)
        if match:
            rows[int(match.group(1))] = match.group(2).strip()
    return rows


def parse_balance_rows(text: str) -> list[tuple[int, int, float]]:
    rows: list[tuple[int, int, float]] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## 3. V-Model Pair Closure"):
            in_section = True
            continue
        if in_section and line.startswith("## 4."):
            break
        if not in_section or not line.startswith("| L"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells[0] == "Left design":
            continue
        if len(cells) < 7:
            continue
        rows.append((int(cells[2]), int(cells[3]), float(cells[4])))
    return rows


def main() -> int:
    progress = read("docs/v3/gates/G0.5-l0-to-l1-handoff.md")
    require("Strict progress" in progress, "G0.5 progress line missing")
    rows = parse_progress_rows(progress)
    complete_count = sum(1 for status in rows.values() if status == "complete")
    incomplete_count = sum(1 for status in rows.values() if status == "incomplete")
    require(len(rows) == 26, f"expected 26 progress rows, got {len(rows)}")
    require(complete_count == 26, f"expected 26 complete rows, got {complete_count}")
    require(incomplete_count == 0, f"expected 0 incomplete rows, got {incomplete_count}")
    require(rows.get(25) == "complete", "item #25 must be complete")
    require(rows.get(26) == "complete", "item #26 must be complete")
    require("26 complete / 26 total" in progress, "G0.5 progress has not been updated to 26/26")
    require("100.00%" in progress, "G0.5 progress percent mismatch")

    for table in ("template_catalog", "doc_coverage", "prompt_interpretations", "learning_candidates"):
        require_contains("docs/v3/engine/personal-edition-schema-contract.md", f"`{table}`")

    for rule in (
        "template-coverage",
        "review-loop-closure",
        "prompt-interpretation-risk",
        "learning-forward-return",
        "upgrade-assist-contract",
    ):
        require_contains("docs/v3/engine/personal-edition-gate-wiring.md", f"`{rule}`")

    for gate in ("G1", "G3", "G4", "G5", "G6"):
        require_contains("docs/v3/gates/G1-G6-personal-edition-evidence.md", f"| {gate} |")
    require_contains("docs/v3/gates/G1-G6-personal-edition-evidence.md", "implementation_status")
    require_contains("docs/v3/gates/independent-review-evidence.md", "Closure status: #25 can be counted as complete")

    balance_rows = parse_balance_rows(read("docs/v3/gates/G1-G6-personal-edition-evidence.md"))
    require(len(balance_rows) == 5, f"expected 5 V-model balance rows, got {len(balance_rows)}")
    for design_count, test_design_count, balance_ratio in balance_rows:
        require(design_count > 0, "design_count must be positive")
        require(test_design_count > 0, "test_design_count must be positive")
        require(balance_ratio >= 1.0, f"balance_ratio must be >= 1.0, got {balance_ratio}")

    schema_contract = read("docs/v3/engine/personal-edition-schema-contract.md")
    require(schema_contract.count("implementation_status") >= 4, "schema contract must mark implementation_status for all personal tables")
    require("L7-carry" in schema_contract, "schema contract must mark L7 carry implementation status")

    seed_count = count_pattern("docs/v3/engine/template-catalog-seeds.md", r"^\| TPL-SEED-\d{3} \|")
    require(seed_count >= 14, f"expected at least 14 template seeds, got {seed_count}")

    workflow_text = read("docs/v3/engine/personal-edition-workflows.md")
    matrix = workflow_text.split("## 6. Forward Convergence Matrix", 1)[1].split("## 7. Gate And Test Summary", 1)[0]
    drive_rows = len(
        re.findall(
            r"^\| (design / Forward|add-feature|discovery|reverse|recovery|incident|refactor|retrofit|scrum|research|screen-design|frontend-design|design-bottomup|upgrade-assist) \|",
            matrix,
            flags=re.MULTILINE,
        )
    )
    require(drive_rows == 14, f"expected 14 forward convergence rows, got {drive_rows}")

    print("personal-edition-design-check: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"personal-edition-design-check: fail: {exc}", file=sys.stderr)
        raise SystemExit(1)
