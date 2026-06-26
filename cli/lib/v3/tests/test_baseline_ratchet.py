from __future__ import annotations

from cli.lib.v3.baseline.ratchet import (
    assert_monotone_decrease,
    ratchet,
    tighten_baseline,
)


def test_violations_in_baseline_are_grandfathered():
    res = ratchet(current={"a", "b"}, baseline={"a", "b", "c"})
    assert res.ok is True
    assert res.new_violations == ()
    assert res.resolved == ("c",)  # c は解消済


def test_new_violation_outside_baseline_fails():
    res = ratchet(current={"a", "x"}, baseline={"a"})
    assert res.ok is False
    assert res.new_violations == ("x",)


def test_tighten_baseline_only_shrinks():
    # baseline は解消分だけ縮む。新規(current の baseline 外)は baseline に入れない。
    new_base = tighten_baseline(baseline={"a", "b", "c"}, current={"a", "x"})
    assert new_base == frozenset({"a"})  # b,c 解消 / x は debt 化しない


def test_monotone_decrease_guard():
    assert assert_monotone_decrease(old_baseline={"a", "b"}, new_baseline={"a"}) is True
    assert assert_monotone_decrease(old_baseline={"a"}, new_baseline={"a", "b"}) is False  # 増加=違反
