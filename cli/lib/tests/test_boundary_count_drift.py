from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
ADD_FEATURE_GLOB = "docs/plans/add-feature/add-feature-*.md"
AUDIT_YAML_FILES = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml",
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml",
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml",
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml",
    REPO_ROOT / "docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml",
)
PYTHON_CONTRACT_MIRROR = (
    REPO_ROOT / "cli/lib/tests/test_helix_l0_l14_flow_contract.py"
)
BATS_CONTRACT_MIRROR = REPO_ROOT / "cli/tests/test-helix-l0-l14-flow-contract.bats"
PIN_KEYS = {
    "repository_add_feature_files_discovered",
    "deferred_repository_add_feature_files_discovered",
    "full_objective_repository_add_feature_files_discovered",
    "all_repository_add_feature_files_checked",
}


@dataclass(frozen=True)
class CountRecord:
    source: str
    label: str
    value: int


def _ground_truth_count() -> int:
    return len(sorted((REPO_ROOT / "docs/plans/add-feature").glob("add-feature-*.md")))


def _walk_scalars(payload, prefix: str = "") -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_walk_scalars(value, next_prefix))
        return rows
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            next_prefix = f"{prefix}[{index}]"
            rows.extend(_walk_scalars(value, next_prefix))
        return rows
    rows.append((prefix, payload))
    return rows


def _yaml_count_records(path: Path) -> list[CountRecord]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    records: list[CountRecord] = []
    for label, value in _walk_scalars(payload):
        key = label.rsplit(".", 1)[-1]
        if key in PIN_KEYS and isinstance(value, int):
            records.append(CountRecord(path.name, label, value))

    glob_patterns = payload.get("glob_patterns", []) if isinstance(payload, dict) else []
    for item in glob_patterns:
        if item.get("pattern") == ADD_FEATURE_GLOB:
            records.append(
                CountRecord(
                    path.name,
                    f"glob_patterns[{ADD_FEATURE_GLOB}]",
                    int(item["match_count"]),
                )
            )
    return records


def _text_count_records(path: Path) -> list[CountRecord]:
    text = path.read_text(encoding="utf-8")
    records: list[CountRecord] = []
    for key in sorted(PIN_KEYS):
        pattern = re.compile(rf'["\']{re.escape(key)}["\']\s*[:=]\s*(\d+)')
        for index, match in enumerate(pattern.finditer(text), start=1):
            records.append(
                CountRecord(
                    path.name,
                    f"{key}#{index}",
                    int(match.group(1)),
                )
            )
    glob_pattern = re.compile(rf'["\']{re.escape(ADD_FEATURE_GLOB)}["\']\s*[:=]\s*(\d+)')
    for index, match in enumerate(glob_pattern.finditer(text), start=1):
        records.append(
            CountRecord(
                path.name,
                f"{ADD_FEATURE_GLOB}#{index}",
                int(match.group(1)),
            )
        )
    return records


def _collect_count_records() -> list[CountRecord]:
    records: list[CountRecord] = []
    for path in AUDIT_YAML_FILES:
        records.extend(_yaml_count_records(path))
    records.extend(_text_count_records(PYTHON_CONTRACT_MIRROR))
    records.extend(_text_count_records(BATS_CONTRACT_MIRROR))
    return records


def _assert_all_counts_match(records: list[CountRecord], expected_count: int) -> None:
    assert records, "count pins must exist"
    for record in records:
        assert record.value == expected_count, (
            f"{record.source}:{record.label} expected {expected_count} got {record.value}"
        )


def test_boundary_count_pins_match_add_feature_plan_ground_truth() -> None:
    """DoD 検証: TL P2-2 add-feature count pin は全 mirror で実数と一致する。"""

    expected_count = _ground_truth_count()
    _assert_all_counts_match(_collect_count_records(), expected_count)


def test_boundary_count_guard_detects_single_site_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: TL P2-2 1 箇所だけズレても drift guard が fail する。"""

    expected_count = _ground_truth_count()
    records = _collect_count_records()
    injected = [
        CountRecord(records[0].source, records[0].label, records[0].value + 1),
        *records[1:],
    ]
    monkeypatch.setattr(sys.modules[__name__], "_collect_count_records", lambda: injected)

    with pytest.raises(AssertionError, match="expected"):
        _assert_all_counts_match(_collect_count_records(), expected_count)
