"""DoD 検証: L7-doctor-summary-jsonplan.md §3"""

from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import doctor_summary


def test_parse_doctor_output_counts_sections() -> None:
    """DoD 検証: L7-doctor-summary-jsonplan.md multi-section summary."""
    output = """=== HELIX Doctor ===

[必須依存]
  ✓ python3

[PLAN registry advisory]
  ✓ plan drift advisory

[V-model pair freeze]
  △ check vmodel pair freeze: critical:3 warning:2 info:6

[stale locks]
  ✗ stale lock cleanup

結果: 2 pass, 1 fail, 11 warn
"""

    summary = doctor_summary.parse_doctor_output(output)

    assert summary["pass_count"] == 2
    assert summary["fail_count"] == 1
    assert summary["warn_count"] == 11
    assert summary["sections"] == [
        {"name": "必須依存", "status": "pass", "count": 0},
        {"name": "PLAN registry advisory", "status": "pass", "count": 0},
        {"name": "V-model pair freeze", "status": "warn", "count": 11},
        {"name": "stale locks", "status": "fail", "count": 1},
    ]


def test_parse_doctor_output_handles_empty() -> None:
    """DoD 検証: L7-doctor-summary-jsonplan.md empty output handling."""
    assert doctor_summary.parse_doctor_output("") == {
        "pass_count": 0,
        "fail_count": 0,
        "warn_count": 0,
        "sections": [],
    }


def test_parse_doctor_output_section_status_detection() -> None:
    """DoD 検証: L7-doctor-summary-jsonplan.md marker status detection."""
    output = """[pass section]
  ✓ all good
[warn section]
  △ advisory found
[fail section]
  ✗ required missing
"""

    sections = doctor_summary.parse_doctor_output(output)["sections"]

    assert sections == [
        {"name": "pass section", "status": "pass", "count": 0},
        {"name": "warn section", "status": "warn", "count": 1},
        {"name": "fail section", "status": "fail", "count": 1},
    ]
