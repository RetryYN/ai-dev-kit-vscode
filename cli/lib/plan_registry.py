#!/usr/bin/env python3
"""契約: PLAN-100 Phase 4 Wave 4

plan_registry bulk import CLI helper。
cli/lib/plan_parser.py の upsert_plan() を用いて docs/plans/ 配下の PLAN doc を一括登録する。
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Generator

try:
    from . import plan_parser
    from .migrations import v35_plan_registry
except ImportError:  # pragma: no cover
    import plan_parser
    from migrations import v35_plan_registry


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_DIR = REPO_ROOT / "docs" / "plans"
DEFAULT_DB_PATH = REPO_ROOT / ".helix" / "helix.db"


def _stored_doc_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _json_safe(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _iter_plan_files(docs_dir: Path) -> Generator[Path, None, None]:
    """docs_dir 配下の PLAN-*.md と ADR-*.md を yield"""
    seen: set[Path] = set()
    for pattern in ("PLAN-*.md", "ADR-*.md"):
        for path in sorted(docs_dir.rglob(pattern)):
            resolved = path.resolve()
            if not path.is_file() or resolved in seen:
                continue
            seen.add(resolved)
            yield path


def bulk_import(
    docs_dir: Path = DEFAULT_DOCS_DIR,
    db_path: Path | None = None,
    verbose: bool = False,
) -> dict:
    """docs/plans/*.md を全件 UPSERT。戻り値: {total, success, failed, errors}"""
    docs_dir = docs_dir.expanduser().resolve()
    resolved_db_path = (db_path or DEFAULT_DB_PATH).expanduser().resolve()
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    result = {"total": 0, "success": 0, "failed": 0, "errors": []}

    conn = sqlite3.connect(str(resolved_db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        v35_plan_registry.migrate_v34_to_v35(conn)

        for path in _iter_plan_files(docs_dir):
            result["total"] += 1
            try:
                frontmatter = _json_safe(plan_parser.parse_frontmatter(str(path)))
                upsert_result = plan_parser.upsert_plan(conn, frontmatter, _stored_doc_path(path))
            except Exception as exc:  # pragma: no cover
                result["failed"] += 1
                error = f"{path.as_posix()}: {exc}"
                result["errors"].append(error)
                if verbose:
                    print(f"FAIL {error}")
                continue

            if upsert_result.get("status") == "parse_error":
                result["failed"] += 1
                error = f"{path.as_posix()}: parse_error"
                result["errors"].append(error)
                if verbose:
                    print(f"FAIL {error}")
                continue

            result["success"] += 1
            if verbose:
                plan_id = upsert_result.get("plan_id") or path.stem
                print(f"OK {plan_id} <- {path.as_posix()}")
    finally:
        conn.close()

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="HELIX plan registry bulk import")
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    parser.add_argument("--db", type=Path, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    result = bulk_import(docs_dir=args.docs_dir, db_path=args.db, verbose=args.verbose)
    print(f"Import complete: {result['success']}/{result['total']} success, {result['failed']} failed")
    if result.get("errors"):
        for err in result["errors"]:
            print(f"  ERROR: {err}")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
