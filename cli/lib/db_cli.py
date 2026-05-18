#!/usr/bin/env python3
"""HELIX DB CLI helpers for local rollback drills.

Design references:
- docs/plans/PLAN-086-rollback-fault-injection-drill.md §3-4
- docs/adr/ADR-020-cutover-rollback-gates.md §Decision.2
- cli/lib/rollback_orchestrator.py
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cli.lib import helix_db, rollback_orchestrator


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
SUPPORTED_TARGET_VERSION = 30
DEV_WARNING = """WARNING: This is a dev-only convenience tool for local migration testing.
For production retreat from a problematic migration, prefer writing a
forward-only undo migration (e.g. v32_undo_v31.py). See ADR-020 Decision.2
for rationale."""
ARCHIVE_DB_FILENAMES = (
    "orchestration.db",
    "vmodel.db",
    "scrum.db",
    "plan.db",
    "backend.db",
    "frontend.db",
)
EVENT_SOURCE_DBS = ("orchestration.db", "vmodel.db", "scrum.db")


class DbArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, warning_text: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.warning_text = warning_text

    def format_help(self) -> str:
        base = super().format_help()
        if not self.warning_text:
            return base
        return f"{self.warning_text}\n\n{base}"

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


@dataclass(frozen=True)
class RollbackPreflight:
    target_version: int
    current_version: int | None
    backup_version: int | None
    current_db_path: Path
    backup_path: Path
    project_root: Path
    helix_dir: Path
    archive_dir: Path
    self_backup_path: Path
    diff_event_count: int
    can_rollback: bool
    reasons: tuple[str, ...]
    advisory: dict[str, Any] | None


def _now() -> datetime:
    return datetime.now(UTC)


def _timestamp_slug() -> str:
    return _now().strftime("%Y-%m-%dT%H-%M-%S")


def _target_version(value: str) -> int:
    if not value.startswith("v") or not value[1:].isdigit():
        raise argparse.ArgumentTypeError("--to は v30 の形式で指定してください")
    version = int(value[1:])
    if version != SUPPORTED_TARGET_VERSION:
        raise argparse.ArgumentTypeError(
            f"PLAN-086 で対応する rollback target は v{SUPPORTED_TARGET_VERSION} のみです"
        )
    return version


def _schema_version(db_path: Path) -> int:
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_version'"
        ).fetchone()
        if row is None:
            raise RuntimeError(f"schema_version table is missing: {db_path}")
        version_row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return int(version_row[0] or 0)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _count_event_rows(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    with sqlite3.connect(str(db_path)) as conn:
        if not _table_exists(conn, "event_envelope"):
            return 0
        row = conn.execute("SELECT COUNT(*) FROM event_envelope").fetchone()
        return int(row[0] or 0)


def _count_diff_events(helix_dir: Path) -> int:
    return sum(_count_event_rows(helix_dir / filename) for filename in EVENT_SOURCE_DBS)


@contextlib.contextmanager
def _patched_environ(updates: dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _best_effort_orchestrator_preflight(backup_path: Path) -> dict[str, Any] | None:
    env_updates = {
        rollback_orchestrator.ROLLBACK_BACKUP_PATH_ENV: str(backup_path),
        "HELIX_DB_CUTOVER": os.environ.get("HELIX_DB_CUTOVER", "1"),
    }
    with _patched_environ(env_updates):
        try:
            return rollback_orchestrator.rollback_preflight()
        except Exception as exc:  # pragma: no cover - advisory only
            return {"error": str(exc)}


def _build_preflight(target_version: int, current_db_path: Path, backup_path: Path, project_root: Path) -> RollbackPreflight:
    helix_dir = current_db_path.parent
    archive_dir = helix_dir / "v31-archive" / _timestamp_slug()
    self_backup_path = helix_dir / f"{current_db_path.name}.pre-rollback.bak"
    reasons: list[str] = []
    current_version: int | None = None
    backup_version: int | None = None

    if not current_db_path.exists():
        reasons.append(f"current db が存在しません: {current_db_path}")
    else:
        try:
            current_version = _schema_version(current_db_path)
        except Exception as exc:
            reasons.append(str(exc))

    if not backup_path.exists():
        reasons.append(f"backup file が存在しません: {backup_path}")
    else:
        try:
            backup_version = _schema_version(backup_path)
        except Exception as exc:
            reasons.append(str(exc))

    if current_version is not None and current_version <= target_version:
        reasons.append(
            f"current schema_version={current_version} は rollback target v{target_version} より新しくありません"
        )
    if backup_version is not None and backup_version != target_version:
        reasons.append(
            f"backup schema_version={backup_version} が target v{target_version} と一致しません"
        )

    diff_event_count = _count_diff_events(helix_dir)
    advisory = _best_effort_orchestrator_preflight(backup_path)
    if diff_event_count == 0 and advisory is not None:
        advisory_count = advisory.get("diff_event_count")
        if isinstance(advisory_count, int) and advisory_count > 0:
            diff_event_count = advisory_count

    return RollbackPreflight(
        target_version=target_version,
        current_version=current_version,
        backup_version=backup_version,
        current_db_path=current_db_path,
        backup_path=backup_path,
        project_root=project_root,
        helix_dir=helix_dir,
        archive_dir=archive_dir,
        self_backup_path=self_backup_path,
        diff_event_count=diff_event_count,
        can_rollback=not reasons,
        reasons=tuple(reasons),
        advisory=advisory,
    )


def _print_preflight(preflight: RollbackPreflight, *, dry_run: bool) -> None:
    print(DEV_WARNING)
    print("")
    print(f"mode: {'dry-run' if dry_run else 'execute'}")
    print(f"target_version: v{preflight.target_version}")
    print(
        "current_schema_version: "
        + (f"v{preflight.current_version}" if preflight.current_version is not None else "unknown")
    )
    print(
        "backup_schema_version: "
        + (f"v{preflight.backup_version}" if preflight.backup_version is not None else "unknown")
    )
    print(f"backup_path: {preflight.backup_path}")
    print(f"self_backup_path: {preflight.self_backup_path}")
    print(f"archive_dir: {preflight.archive_dir}")
    print(f"diff_event_count: {preflight.diff_event_count}")
    if preflight.advisory and preflight.advisory.get("reasons"):
        joined = "; ".join(str(reason) for reason in preflight.advisory["reasons"])
        print(f"orchestrator_advisory: {joined}")
    if preflight.can_rollback:
        print("preflight: PASS")
        if dry_run:
            print("next_step: rerun with --confirm to execute rollback")
    else:
        print("preflight: FAIL")
        for reason in preflight.reasons:
            print(f"reason: {reason}")


def _self_backup(current_db_path: Path, self_backup_path: Path) -> None:
    self_backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(current_db_path, self_backup_path)


def _archive_split_dbs(helix_dir: Path, archive_dir: Path) -> list[Path]:
    archive_dir.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    for filename in ARCHIVE_DB_FILENAMES:
        source = helix_dir / filename
        if not source.exists():
            continue
        target = archive_dir / filename
        shutil.move(str(source), str(target))
        moved.append(target)
    return moved


def _restore_backup(backup_path: Path, current_db_path: Path) -> None:
    current_db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, current_db_path)


def _clone_event_table_dump(source_db: Path) -> tuple[int, str] | None:
    if not source_db.exists():
        return None

    source = sqlite3.connect(str(source_db))
    source.row_factory = sqlite3.Row
    try:
        if not _table_exists(source, "event_envelope"):
            return None

        schema_row = source.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'event_envelope'"
        ).fetchone()
        if schema_row is None or not schema_row["sql"]:
            return None

        rows = source.execute("SELECT * FROM event_envelope ORDER BY occurred_at, event_id").fetchall()
        dest = sqlite3.connect(":memory:")
        try:
            dest.execute(str(schema_row["sql"]))
            index_rows = source.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'index' AND tbl_name = 'event_envelope' AND sql IS NOT NULL"
            ).fetchall()
            for index_row in index_rows:
                dest.execute(str(index_row["sql"]))

            if rows:
                columns = [column[1] for column in source.execute("PRAGMA table_info(event_envelope)").fetchall()]
                placeholders = ", ".join("?" for _ in columns)
                insert_sql = (
                    f"INSERT INTO event_envelope ({', '.join(columns)}) VALUES ({placeholders})"
                )
                payload = [tuple(row[column] for column in columns) for row in rows]
                dest.executemany(insert_sql, payload)
            dump_sql = "\n".join(dest.iterdump())
        finally:
            dest.close()
        return (len(rows), dump_sql)
    finally:
        source.close()


def _export_diff_archive(archive_dir: Path, export_path: Path, current_version: int | None) -> int:
    export_path.parent.mkdir(parents=True, exist_ok=True)
    databases: list[dict[str, Any]] = []
    total_event_count = 0
    for filename in ARCHIVE_DB_FILENAMES:
        archived_db = archive_dir / filename
        dumped = _clone_event_table_dump(archived_db)
        if dumped is None:
            continue
        event_count, dump_sql = dumped
        total_event_count += event_count
        databases.append(
            {
                "db_name": archived_db.stem,
                "path": str(archived_db),
                "event_count": event_count,
                "dump_sql": dump_sql,
            }
        )

    payload = {
        "generated_at": _now().isoformat(),
        "source_schema_version": current_version,
        "archive_dir": str(archive_dir),
        "total_event_count": total_event_count,
        "databases": databases,
    }
    export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return total_event_count


def _run_doctor(project_root: Path) -> None:
    if os.environ.get("HELIX_DB_ROLLBACK_SKIP_DOCTOR") == "1":
        return
    doctor_script = Path(__file__).resolve().parents[1] / "helix-doctor"
    env = os.environ.copy()
    result = subprocess.run(
        [str(doctor_script)],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "helix doctor failed after rollback:\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )


def _execute_rollback(preflight: RollbackPreflight, *, export_diff: Path | None) -> int:
    _self_backup(preflight.current_db_path, preflight.self_backup_path)
    archived = _archive_split_dbs(preflight.helix_dir, preflight.archive_dir)
    _restore_backup(preflight.backup_path, preflight.current_db_path)

    restored_version = _schema_version(preflight.current_db_path)
    if restored_version != preflight.target_version:
        raise RuntimeError(
            f"restored schema_version={restored_version} が target v{preflight.target_version} と一致しません"
        )

    exported_count = None
    if export_diff is not None:
        exported_count = _export_diff_archive(
            preflight.archive_dir,
            export_diff,
            preflight.current_version,
        )

    _run_doctor(preflight.project_root)

    print(DEV_WARNING)
    print("")
    print("rollback: completed")
    print(f"restored_db: {preflight.current_db_path}")
    print(f"restored_schema_version: v{restored_version}")
    print(f"self_backup_path: {preflight.self_backup_path}")
    print(f"archived_split_db_count: {len(archived)}")
    print(f"archive_dir: {preflight.archive_dir}")
    print(f"diff_event_count: {preflight.diff_event_count}")
    if export_diff is None:
        print("diff_action: discard (archived files retained)")
    else:
        print(f"diff_action: export -> {export_diff}")
        print(f"exported_event_count: {exported_count}")
    return EXIT_SUCCESS


def cmd_rollback(args: argparse.Namespace) -> int:
    current_db_path = Path(args.db_path or helix_db._resolve_db_path(None)).resolve()
    backup_path = Path(args.backup_path).expanduser().resolve()
    project_root = Path(args.project_root or current_db_path.parent.parent).resolve()
    preflight = _build_preflight(args.to, current_db_path, backup_path, project_root)

    if not args.confirm:
        _print_preflight(preflight, dry_run=True)
        return EXIT_SUCCESS if preflight.can_rollback else EXIT_FAILURE

    _print_preflight(preflight, dry_run=False)
    if not preflight.can_rollback:
        return EXIT_FAILURE

    try:
        export_path = (
            None if args.export_diff is None else Path(args.export_diff).expanduser().resolve()
        )
        return _execute_rollback(preflight, export_diff=export_path)
    except Exception as exc:
        print(f"rollback: failed: {exc}", file=sys.stderr)
        print(f"self_backup_path: {preflight.self_backup_path}", file=sys.stderr)
        print(f"archive_dir: {preflight.archive_dir}", file=sys.stderr)
        return EXIT_FAILURE


def build_parser() -> argparse.ArgumentParser:
    parser = DbArgumentParser(prog="helix db", description="HELIX DB utilities")
    parser.add_argument("--project-root", help=argparse.SUPPRESS)
    parser.add_argument("--db-path", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="subcmd")

    rollback = sub.add_parser(
        "rollback",
        prog="helix db rollback",
        description="Restore a pre-v31 backup for local rollback drills.",
        warning_text=DEV_WARNING,
    )
    rollback.add_argument("--to", required=True, type=_target_version, metavar="v30")
    rollback.add_argument("--backup-path", required=True, metavar="PATH")
    rollback.add_argument("--confirm", action="store_true", help="実 rollback を実行する")
    group = rollback.add_mutually_exclusive_group()
    group.add_argument(
        "--discard-diff",
        action="store_true",
        help="cutover 後の diff event を archive に残し export しない (default)",
    )
    group.add_argument(
        "--export-diff",
        metavar="PATH",
        help="archive 済み split DB の event_envelope を JSON として export する",
    )
    rollback.set_defaults(func=cmd_rollback)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "subcmd", None):
        parser.print_help()
        return EXIT_SUCCESS
    handler = getattr(args, "func", None)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
