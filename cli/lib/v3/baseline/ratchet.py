"""C5 keystone: baseline ratchet (shrink-only known-debt)。

detector が出す violation のうち **baseline(既知 debt の frozenset)に含まれるものは grandfather**し、
baseline 外の新規 violation だけを hard fail にする。baseline は **shrink-only**(縮小のみ許可)で、
CI が monotone-decrease を assert することで debt が増えないことを機械保証する(cutover 後の段階的
hard 化を安全にする = NFR-V3-03)。

設計正本: docs/v3/engine/baseline-ratchet.md。pure-function。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class RatchetResult:
    ok: bool
    new_violations: tuple[str, ...]  # current - baseline = baseline 外の新規 = hard fail
    resolved: tuple[str, ...]  # baseline - current = 解消済(baseline を縮められる)


def ratchet(current: Iterable[str], baseline: Iterable[str]) -> RatchetResult:
    """current violation を baseline で grandfather。新規(baseline 外)があれば ok=False。"""
    current_set = set(current)
    baseline_set = set(baseline)
    new_violations = tuple(sorted(current_set - baseline_set))
    resolved = tuple(sorted(baseline_set - current_set))
    return RatchetResult(ok=not new_violations, new_violations=new_violations, resolved=resolved)


def tighten_baseline(baseline: Iterable[str], current: Iterable[str]) -> frozenset[str]:
    """baseline を current の解消分だけ縮める(shrink-only の正しい更新)。新規は足さない。"""
    return frozenset(set(baseline) & set(current))


def assert_monotone_decrease(old_baseline: Iterable[str], new_baseline: Iterable[str]) -> bool:
    """baseline は shrink-only: new ⊆ old(項目を増やしてはいけない)。"""
    return set(new_baseline) <= set(old_baseline)
