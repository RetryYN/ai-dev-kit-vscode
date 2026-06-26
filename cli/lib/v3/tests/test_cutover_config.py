from __future__ import annotations

from cli.lib.v3.cutover.config import _probe_restore_round_trip, build_cutover_config


def test_probe_restore_round_trip_proves_reversibility():
    # rollback 機構が throwaway DB で archive→restore round-trip できる
    assert _probe_restore_round_trip() is True


def test_build_cutover_config_satisfies_rollback_preflight_fields(tmp_path):
    cfg = build_cutover_config(str(tmp_path))
    # gate の rollback_preflight が要求する 4 項目が揃う
    assert cfg["promote_reverse"]
    assert cfg["window_expiry"]
    assert cfg["archive_dir"]
    assert callable(cfg["restore_dry_run"])
    assert cfg["restore_dry_run"]() is True


def test_build_cutover_config_is_nondestructive_by_default(tmp_path):
    # 既定は retire=() = 何も退役しない(非破壊)。破壊的退役は明示が必要。
    cfg = build_cutover_config(str(tmp_path))
    assert cfg["retirement_inventory"] == []
    cfg2 = build_cutover_config(str(tmp_path), retire=["cli/tests/old.bats"])
    assert cfg2["retirement_inventory"] == ["cli/tests/old.bats"]
