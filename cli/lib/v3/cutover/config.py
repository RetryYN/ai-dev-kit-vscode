"""cutover-gate 用 config builder。rollback 機構(rollback.py)を gate へ wire する。

build_cutover_config は cutover-gate(gate.py)が要求する config を組み立てる。restore_dry_run は
rollback.restore_dry_run(throwaway DB の round-trip)を callable として渡し、可逆性を機械実証する。

**重要**: これは gate を機械的に green にできることを示すための config であって、cutover の EXECUTION
(promote/退役/物理削除)を一切行わない。retirement_inventory が空なら gate は『非破壊 promote』を
sanction するのみ。実 V2 退役(破壊的)は parity 到達 + 人間 go が前提(cutover-design §4)。
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from collections.abc import Sequence

try:
    from v3.cutover import rollback
except ImportError:  # pragma: no cover
    from cli.lib.v3.cutover import rollback


def _probe_restore_round_trip() -> bool:
    """throwaway sqlite DB で archive→restore round-trip を実証(本物に触れない)。"""
    with tempfile.TemporaryDirectory() as tmp:
        probe = os.path.join(tmp, "probe.db")
        connection = sqlite3.connect(probe)
        connection.execute("CREATE TABLE probe (x TEXT)")
        connection.execute("INSERT INTO probe VALUES ('ok')")
        connection.commit()
        connection.close()
        return rollback.restore_dry_run(probe)


def build_cutover_config(repo_root: str, *, retire: Sequence[str] = ()) -> dict[str, object]:
    archive_dir = os.path.join(repo_root, ".helix", "v3-cutover-archive")
    os.makedirs(archive_dir, exist_ok=True)
    retire_list = list(retire)
    return {
        # gate.py が読む正式キー名に合わせる(surviving_surface / retired_inventory / retired_actual)
        "surviving_surface": ["helix/core-manifest.tsv", "cli/helix"],
        "retired_inventory": retire_list,  # 空 = 何も退役しない(非破壊)
        "retired_actual": retire_list,  # commit が退役する実集合(= inventory と一致が pin の前提)
        "v2_path_inventory": [],
        "promote_reverse": "import-switch",  # V3 昇格の逆手順(config 契約)
        "window_expiry": "2026-07-31",
        "archive_dir": archive_dir,
        "restore_dry_run": _probe_restore_round_trip,  # rollback 機構を wire(callable)
        # accepted_gap が要求する正式キー: deadline / owner / bridge
        "detector_gap_policy": {"deadline": "2026-07-31", "owner": "helix", "bridge": "v2-detectors"},
    }
