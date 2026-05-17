"""Rollback orchestration helpers for PLAN-084 gate 6.

This module intentionally models the gate 6 control-plane rollback only:
- validate that cutover is currently enabled
- verify the legacy backup and its integrity manifest
- require a PO-issued confirmation token
- switch the process-local adapter flag back to dual-write mode

Destructive data-path actions such as dropping projection tables remain a
runbook/PO carry item outside this module.

Design references:
- docs/adr/ADR-018-db-separation-and-event-sourcing.md §Decision.5 gate 6
- docs/v2/L3-detailed-design/D-API/D-API-SEP-rollback-gate6.md
- cli/lib/compatibility_adapter.py
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from . import helix_db

ROLLBACK_WINDOW_DAYS = 7
ROLLBACK_CONFIRM_TOKEN_ENV = "HELIX_DB_ROLLBACK_CONFIRM_TOKEN"
ROLLBACK_BACKUP_PATH_ENV = "HELIX_DB_ROLLBACK_BACKUP_PATH"
ROLLBACK_CUTOVER_AT_ENV = "HELIX_DB_CUTOVER_AT"
ROLLBACK_MANIFEST_SUFFIX = ".rollback.json"


@dataclass(frozen=True)
class RollbackResult:
    rolled_back: bool
    backup_path: str
    diff_event_count: int
    reverted_at: str


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_isoformat() -> str:
    return _utcnow().isoformat()


def _resolve_backup_path(backup_path: str | Path | None = None) -> Path:
    if backup_path is not None:
        return Path(backup_path).expanduser().resolve()

    env_path = os.environ.get(ROLLBACK_BACKUP_PATH_ENV)
    if env_path:
        return Path(env_path).expanduser().resolve()

    legacy_db = Path(helix_db._resolve_db_path(None)).resolve()
    return legacy_db.with_suffix(f"{legacy_db.suffix}.rollback.bak")


def _manifest_path_for(backup_path: Path) -> Path:
    return Path(f"{backup_path}{ROLLBACK_MANIFEST_SUFFIX}")


def _parse_iso8601_utc(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("cutover_at must include UTC timezone information")
    return parsed.astimezone(UTC)


def _sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(backup_path: Path) -> dict[str, Any] | None:
    manifest_path = _manifest_path_for(backup_path)
    if not manifest_path.exists():
        return None
    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("rollback manifest must be a JSON object")
    return payload


def _resolve_cutover_at(manifest: dict[str, Any] | None) -> datetime | None:
    raw_value = os.environ.get(ROLLBACK_CUTOVER_AT_ENV)
    if not raw_value and manifest is not None:
        manifest_value = manifest.get("cutover_at")
        if isinstance(manifest_value, str):
            raw_value = manifest_value
    if not raw_value:
        return None
    return _parse_iso8601_utc(raw_value)


def _resolve_diff_event_count(manifest: dict[str, Any] | None) -> int | None:
    if manifest is None:
        return None
    diff_event_count = manifest.get("diff_event_count")
    if not isinstance(diff_event_count, int) or diff_event_count < 0:
        raise ValueError("rollback manifest diff_event_count must be a non-negative integer")
    return diff_event_count


def _is_within_rollback_window(cutover_at: datetime | None) -> bool:
    if cutover_at is None:
        return False
    elapsed = _utcnow() - cutover_at
    return timedelta(0) <= elapsed <= timedelta(days=ROLLBACK_WINDOW_DAYS)


# @helix:index id=plan084.rollback.preflight domain=cli/lib summary=gate 6 rollback preflight for cutover state and backup integrity
def rollback_preflight() -> dict[str, Any]:
    """rollback 実行前の preflight (HELIX_DB_CUTOVER state 確認 + backup 整合)."""
    backup_path = _resolve_backup_path()
    manifest_path = _manifest_path_for(backup_path)
    reasons: list[str] = []

    cutover_enabled = os.environ.get("HELIX_DB_CUTOVER") == "1"
    if not cutover_enabled:
        reasons.append("HELIX_DB_CUTOVER=1 ではないため rollback 対象ではない")

    backup_exists = backup_path.exists()
    if not backup_exists:
        reasons.append("legacy backup file が存在しない")

    manifest = _load_manifest(backup_path) if backup_exists else None
    manifest_exists = manifest is not None
    if not manifest_exists:
        reasons.append("rollback manifest が存在しない")

    backup_integrity_ok = False
    diff_event_count: int | None = None
    cutover_at: datetime | None = None
    if manifest is not None:
        expected_sha256 = manifest.get("expected_sha256")
        if not isinstance(expected_sha256, str) or not expected_sha256:
            reasons.append("rollback manifest expected_sha256 が不正")
        else:
            actual_sha256 = _sha256_for(backup_path)
            backup_integrity_ok = secrets.compare_digest(actual_sha256, expected_sha256)
            if not backup_integrity_ok:
                reasons.append("backup sha256 が manifest と一致しない")

        diff_event_count = _resolve_diff_event_count(manifest)
        if diff_event_count is None:
            reasons.append("diff_event_count が取得できない")

        cutover_at = _resolve_cutover_at(manifest)
        if cutover_at is None:
            reasons.append("cutover_at が記録されていない")
        elif not _is_within_rollback_window(cutover_at):
            reasons.append("rollback window (7d) を超過している")

    return {
        "cutover_enabled": cutover_enabled,
        "backup_path": str(backup_path),
        "manifest_path": str(manifest_path),
        "backup_exists": backup_exists,
        "manifest_exists": manifest_exists,
        "backup_integrity_ok": backup_integrity_ok,
        "cutover_at": cutover_at.isoformat() if cutover_at is not None else None,
        "rollback_window_open": _is_within_rollback_window(cutover_at),
        "diff_event_count": diff_event_count,
        "can_rollback": not reasons,
        "reasons": reasons,
    }


# @helix:index id=plan084.rollback.execute domain=cli/lib summary=gate 6 rollback execution with PO token validation and cutover flag retreat
def rollback_execute(*, confirm_token: str, backup_path: str) -> RollbackResult:
    """実 rollback 実行 (PO 承認 token 必須、本実装は code 完成のみ、実行は PO carry)."""
    expected_token = os.environ.get(ROLLBACK_CONFIRM_TOKEN_ENV)
    if not expected_token:
        raise RuntimeError("rollback confirm token is not configured")
    if not confirm_token:
        raise ValueError("confirm_token must not be empty")
    if not secrets.compare_digest(confirm_token, expected_token):
        raise PermissionError("invalid rollback confirm token")

    preflight = rollback_preflight()
    requested_backup = str(_resolve_backup_path(backup_path))
    if requested_backup != preflight["backup_path"]:
        raise ValueError("backup_path does not match the preflight target")
    if not preflight["can_rollback"]:
        raise RuntimeError(
            "rollback preflight failed: " + "; ".join(preflight["reasons"])
        )

    # Gate 6 switches the adapter back to dual-write mode first.
    os.environ["HELIX_DB_CUTOVER"] = "0"
    reverted_at = _utcnow_isoformat()
    diff_event_count = preflight["diff_event_count"]
    assert isinstance(diff_event_count, int)
    return RollbackResult(
        rolled_back=True,
        backup_path=requested_backup,
        diff_event_count=diff_event_count,
        reverted_at=reverted_at,
    )
