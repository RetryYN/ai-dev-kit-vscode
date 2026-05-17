"""Rollback orchestrator unit tests for PLAN-084 gate 6.

設計参照:
- docs/v2/L3-detailed-design/D-API/D-API-SEP-rollback-gate6.md §2/§3/§4
- docs/adr/ADR-018-db-separation-and-event-sourcing.md §Decision.5 gate 6

DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-001〜005
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from cli.lib import rollback_orchestrator


# @helix:index id=plan084.rollback.tests domain=cli/lib/tests summary=PLAN-084 rollback orchestrator unit tests
def _write_backup_fixture(path: Path, *, diff_event_count: int, cutover_at: datetime) -> None:
    payload = b"legacy helix db backup bytes"
    path.write_bytes(payload)
    manifest = {
        "expected_sha256": hashlib.sha256(payload).hexdigest(),
        "diff_event_count": diff_event_count,
        "cutover_at": cutover_at.isoformat(),
    }
    Path(f"{path}.rollback.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@pytest.fixture
def rollback_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    backup_path = tmp_path / "helix.db.rollback.bak"
    _write_backup_fixture(
        backup_path,
        diff_event_count=4,
        cutover_at=datetime.now(UTC) - timedelta(days=1),
    )
    monkeypatch.setenv("HELIX_DB_CUTOVER", "1")
    monkeypatch.setenv("HELIX_DB_ROLLBACK_BACKUP_PATH", str(backup_path))
    monkeypatch.setenv("HELIX_DB_ROLLBACK_CONFIRM_TOKEN", "po-approved-token")
    return backup_path


class TestRollbackPreflight:
    def test_rollback_u_001_preflight_passes_when_cutover_and_backup_are_ready(
        self, rollback_env: Path
    ) -> None:
        """DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-001 (preflight が cutover/backup 整合を PASS 判定する)"""
        payload = rollback_orchestrator.rollback_preflight()

        assert payload["can_rollback"] is True
        assert payload["cutover_enabled"] is True
        assert payload["backup_path"] == str(rollback_env.resolve())
        assert payload["backup_integrity_ok"] is True
        assert payload["rollback_window_open"] is True
        assert payload["diff_event_count"] == 4
        assert payload["reasons"] == []

    def test_rollback_u_002_preflight_fails_when_manifest_checksum_mismatches(
        self, rollback_env: Path
    ) -> None:
        """DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-002 (checksum 不一致は fail-close する)"""
        rollback_env.write_bytes(b"tampered backup")

        payload = rollback_orchestrator.rollback_preflight()

        assert payload["can_rollback"] is False
        assert payload["backup_integrity_ok"] is False
        assert any("sha256" in reason for reason in payload["reasons"])

    def test_rollback_u_003_preflight_fails_when_rollback_window_is_expired(
        self, rollback_env: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-003 (7d 超過は rollback 不可と判定する)"""
        monkeypatch.setenv(
            "HELIX_DB_CUTOVER_AT",
            (datetime.now(UTC) - timedelta(days=8)).isoformat(),
        )

        payload = rollback_orchestrator.rollback_preflight()

        assert payload["can_rollback"] is False
        assert payload["rollback_window_open"] is False
        assert any("rollback window" in reason for reason in payload["reasons"])


class TestRollbackExecute:
    def test_rollback_u_004_execute_rejects_invalid_confirm_token(
        self, rollback_env: Path
    ) -> None:
        """DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-004 (PO token 不一致は PermissionError にする)"""
        with pytest.raises(PermissionError, match="invalid rollback confirm token"):
            rollback_orchestrator.rollback_execute(
                confirm_token="wrong-token",
                backup_path=str(rollback_env),
            )

    def test_rollback_u_005_execute_switches_cutover_back_to_dual_write_mode(
        self, rollback_env: Path
    ) -> None:
        """DoD 検証: D-API-SEP-rollback-gate6.md ROLLBACK-U-005 (valid token で cutover flag を 0 に戻し結果を返す)"""
        result = rollback_orchestrator.rollback_execute(
            confirm_token="po-approved-token",
            backup_path=str(rollback_env),
        )

        assert result.rolled_back is True
        assert result.backup_path == str(rollback_env.resolve())
        assert result.diff_event_count == 4
        assert rollback_orchestrator.os.environ["HELIX_DB_CUTOVER"] == "0"
        assert result.reverted_at.endswith("+00:00")
