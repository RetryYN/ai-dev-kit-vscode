from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from cli.lib.v3.detectors.runner import DetectorSpec, Finding, run_doctor


@dataclass(frozen=True)
class _Res:
    ok: bool


def _spec(detector_id, subjects):
    return DetectorSpec(
        detector_id=detector_id,
        source_kind="db_projection",
        severity="hard",
        load=lambda db: None,
        analyze=lambda x: _Res(ok=not subjects),
        messages=lambda r: [Finding(id=detector_id, severity="hard", subject=s, missing=()) for s in subjects],
    )


def test_no_baseline_fails_on_violations():
    res = run_doctor(sqlite3.connect(":memory:"), [_spec("D1", ["x", "y"])])
    assert res.ok is False


def test_baseline_grandfathers_known_findings():
    res = run_doctor(sqlite3.connect(":memory:"), [_spec("D1", ["x", "y"])], baselines={"D1": frozenset({"x", "y"})})
    assert res.ok is True  # 全 grandfathered
    assert len(res.findings) == 2  # finding は report に残る(advisory surface)


def test_baseline_flags_new_violation_outside_baseline():
    res = run_doctor(sqlite3.connect(":memory:"), [_spec("D1", ["x", "NEW"])], baselines={"D1": frozenset({"x"})})
    assert res.ok is False  # NEW は baseline 外 = regression
