"""cutover rollback の安全機構(cutover-design.md §3)。

cutover は破壊的・不可逆。ここでは **非破壊**の rollback 基盤を提供する:
- archive_db: V2 DB を archive 先へ copy + checksum(削除しない)。
- restore_db: archive から restore + checksum 照合。
- restore_dry_run: archive→restore の round-trip を **一時ファイル上で**実行し可逆性を実証(本物に触れない)。

これらは cutover-gate の rollback_preflight が要求する「restore dry-run 成功」を満たすための機構。
実際の cutover EXECUTION(promote/退役)は人間の明示 go が前提(本 module は infra のみ、実行しない)。
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass


def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArchiveRecord:
    source_path: str
    archive_path: str
    checksum: str


def archive_db(db_path: str, archive_dir: str, label: str) -> ArchiveRecord:
    """db_path を archive_dir/<label>/ へ copy(move でなく copy = 元を残す)+ checksum。"""
    if not os.path.isfile(db_path):
        raise FileNotFoundError(db_path)
    dest_dir = os.path.join(archive_dir, label)
    os.makedirs(dest_dir, exist_ok=True)
    archive_path = os.path.join(dest_dir, os.path.basename(db_path))
    shutil.copy2(db_path, archive_path)
    return ArchiveRecord(source_path=db_path, archive_path=archive_path, checksum=_sha256_file(archive_path))


def restore_db(record: ArchiveRecord, target_path: str) -> bool:
    """archive から target へ restore し、checksum が archive 時と一致することを確認。"""
    if not os.path.isfile(record.archive_path):
        return False
    if _sha256_file(record.archive_path) != record.checksum:
        return False  # archive 自体が破損 = restore 不可
    shutil.copy2(record.archive_path, target_path)
    return _sha256_file(target_path) == record.checksum


def restore_dry_run(db_path: str) -> bool:
    """archive→restore の round-trip を一時領域で実証(本物の DB / archive に触れない)。

    cutover 前に「この DB は確実に archive→restore できる」を非破壊で確認する。
    """
    if not os.path.isfile(db_path):
        return False
    original = _sha256_file(db_path)
    with tempfile.TemporaryDirectory() as tmp:
        record = archive_db(db_path, tmp, "dryrun")
        restored = os.path.join(tmp, "restored.db")
        if not restore_db(record, restored):
            return False
        return _sha256_file(restored) == original
