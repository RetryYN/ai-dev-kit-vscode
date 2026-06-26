"""Retired V2 tombstone — import_cycle 検出は V3 engine (FN-DET-17) へ委譲済み。

V2 helper の検出実体は cutover で retire 済み。本テストは旧 V2 実装の回帰用だったが、
検出正本は V3 detector (FN-DET-17) + その UT (cli/lib/v3/tests/) へ移行した。ファイルは
functional-registry の path 解決のため残置(skip でなく retire 明示の trivial test)。
"""
from __future__ import annotations


def test_v2_dependency_cycle_checks_retired_delegated_to_v3() -> None:
    # 検出は V3 (FN-DET-17) が正本。V2 実装は tombstone 退役済み。
    assert True
