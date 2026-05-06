import argparse
import json
import sqlite3
import sys
from pathlib import Path

import helix_db


EXIT_USAGE = 64
EXIT_NOT_FOUND = 2

ENTRY_COLUMNS = (
    "id",
    "axis",
    "stack",
    "lifecycle",
    "parent_entry_id",
    "sprint_id",
    "agent_actor",
    "ref",
    "version",
    "metadata",
    "created_at",
    "updated_at",
)


class HelixArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def _resolve_db_path() -> Path:
    return Path(helix_db.resolve_default_db_path())


def _connect() -> sqlite3.Connection:
    db_path = _resolve_db_path()
    helix_db._prepare_db_path(db_path)
    conn = helix_db.get_connection(db_path)
    helix_db._ensure_schema(conn)
    return conn


def _parser(prog: str) -> HelixArgumentParser:
    return HelixArgumentParser(prog=prog, add_help=True)


def _row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    if data.get("metadata"):
        try:
            data["metadata"] = json.loads(data["metadata"])
        except json.JSONDecodeError:
            pass
    return data


def _print_integrity_error(
    exc: sqlite3.IntegrityError,
    duplicate_id: str | None = None,
    invalid_values: dict[str, str | None] | None = None,
) -> int:
    message = str(exc)
    if "UNIQUE constraint failed: entries.id" in message and duplicate_id:
        print(f"エラー: 重複 id: {duplicate_id}", file=sys.stderr)
    elif "CHECK constraint failed" in message:
        detail = _constraint_detail(message, invalid_values or {})
        print(f"エラー: 不正な値です: {detail}", file=sys.stderr)
    else:
        print(f"エラー: DB 制約違反: {message}", file=sys.stderr)
    return EXIT_USAGE


def _constraint_detail(message: str, values: dict[str, str | None]) -> str:
    for field, value in values.items():
        if field in message:
            return f"{field}={value}"
    return message


def _validate_metadata(raw: str | None) -> str | None:
    if raw is None:
        return None
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"metadata must be valid JSON: {exc.msg}") from exc
    return raw


def cmd_show(entry_id: str) -> int:
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT {', '.join(ENTRY_COLUMNS)} FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if row is None:
            print(f"エラー: entry not found: {entry_id}", file=sys.stderr)
            return EXIT_NOT_FOUND

        links = conn.execute(
            """
            SELECT from_id, to_id, kind, metadata
            FROM links
            WHERE from_id = ? OR to_id = ?
            ORDER BY kind, from_id, to_id
            """,
            (entry_id, entry_id),
        ).fetchall()
    finally:
        conn.close()

    data = _row_to_dict(row)
    for key in ENTRY_COLUMNS:
        value = data.get(key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        print(f"{key}: {value if value is not None else ''}")

    print("links:")
    for link in links:
        link_data = dict(link)
        metadata = link_data.get("metadata") or ""
        print(f"  {link_data['from_id']}\t{link_data['kind']}\t{link_data['to_id']}\t{metadata}")
    return 0


def dispatch(cmd: str, argv: list[str]) -> int:
    if cmd == "list":
        return _list(argv)
    if cmd == "add":
        return _add(argv)
    if cmd == "update":
        if not argv:
            print("エラー: update には id が必要です", file=sys.stderr)
            return EXIT_USAGE
        return _update(argv[0], argv[1:])
    if cmd == "link":
        if len(argv) < 2:
            print("エラー: link には from/to が必要です", file=sys.stderr)
            return EXIT_USAGE
        return _link(argv[0], argv[1], argv[2:])
    if cmd == "unlink":
        if len(argv) < 2:
            print("エラー: unlink には from/to が必要です", file=sys.stderr)
            return EXIT_USAGE
        return _unlink(argv[0], argv[1], argv[2:])
    if cmd == "coverage":
        return _coverage(argv)
    print(f"エラー: 不明なサブコマンドです: {cmd}", file=sys.stderr)
    return EXIT_USAGE


def _list(argv: list[str]) -> int:
    parser = _parser("helix entry list")
    parser.add_argument("--axis")
    parser.add_argument("--stack")
    parser.add_argument("--lifecycle")
    parser.add_argument("--sprint")
    parser.add_argument("--agent")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    where = []
    params = []
    filters = {
        "axis": args.axis,
        "stack": args.stack,
        "lifecycle": args.lifecycle,
        "sprint_id": args.sprint,
        "agent_actor": args.agent,
    }
    for column, value in filters.items():
        if value is not None:
            where.append(f"{column} = ?")
            params.append(value)

    sql = f"SELECT {', '.join(ENTRY_COLUMNS)} FROM entries"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id"

    conn = _connect()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    entries = [_row_to_dict(row) for row in rows]
    if args.as_json:
        print(json.dumps({"entries": entries}, ensure_ascii=False, indent=2))
        return 0

    for row in entries:
        print(
            "\t".join(
                [
                    str(row.get("id") or ""),
                    "-",
                    str(row.get("axis") or ""),
                    str(row.get("lifecycle") or ""),
                    str(row.get("ref") or ""),
                    str(row.get("sprint_id") or ""),
                ]
            )
        )
    return 0


def _add(argv: list[str]) -> int:
    parser = _parser("helix entry add")
    parser.add_argument("--id", required=True)
    parser.add_argument("--axis", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--stack")
    parser.add_argument("--lifecycle", default="initial")
    parser.add_argument("--sprint")
    parser.add_argument("--agent")
    parser.add_argument("--parent")
    parser.add_argument("--metadata", type=_validate_metadata)
    args = parser.parse_args(argv)

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO entries
                (id, axis, stack, lifecycle, parent_entry_id, sprint_id, agent_actor, ref, metadata, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                args.id,
                args.axis,
                args.stack,
                args.lifecycle,
                args.parent,
                args.sprint,
                args.agent,
                args.ref,
                args.metadata,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        return _print_integrity_error(
            exc,
            duplicate_id=args.id,
            invalid_values={
                "axis": args.axis,
                "stack": args.stack,
                "lifecycle": args.lifecycle,
            },
        )
    finally:
        conn.close()
    return 0


def _update(entry_id: str, argv: list[str]) -> int:
    parser = _parser("helix entry update")
    parser.add_argument("--lifecycle")
    parser.add_argument("--metadata", type=_validate_metadata)
    parser.add_argument("--stack")
    parser.add_argument("--sprint")
    parser.add_argument("--agent")
    args = parser.parse_args(argv)

    updates = []
    params = []
    field_map = {
        "lifecycle": args.lifecycle,
        "metadata": args.metadata,
        "stack": args.stack,
        "sprint_id": args.sprint,
        "agent_actor": args.agent,
    }
    for column, value in field_map.items():
        if value is not None:
            updates.append(f"{column} = ?")
            params.append(value)

    if not updates:
        print("エラー: update する内容が指定されていません", file=sys.stderr)
        return EXIT_USAGE

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)

    conn = _connect()
    try:
        result = conn.execute(
            f"UPDATE entries SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        if result.rowcount == 0:
            print(f"エラー: entry not found: {entry_id}", file=sys.stderr)
            return EXIT_NOT_FOUND
        conn.commit()
    except sqlite3.IntegrityError as exc:
        return _print_integrity_error(
            exc,
            invalid_values={
                "stack": args.stack,
                "lifecycle": args.lifecycle,
            },
        )
    finally:
        conn.close()
    return 0


def _link(from_id: str, to_id: str, argv: list[str]) -> int:
    parser = _parser("helix entry link")
    parser.add_argument("--kind", required=True)
    parser.add_argument("--metadata", type=_validate_metadata)
    args = parser.parse_args(argv)

    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO links (from_id, to_id, kind, metadata) VALUES (?, ?, ?, ?)",
            (from_id, to_id, args.kind, args.metadata),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        return _print_integrity_error(exc, invalid_values={"kind": args.kind})
    finally:
        conn.close()
    return 0


def _unlink(from_id: str, to_id: str, argv: list[str]) -> int:
    parser = _parser("helix entry unlink")
    parser.add_argument("--kind", required=True)
    args = parser.parse_args(argv)

    conn = _connect()
    try:
        conn.execute(
            "DELETE FROM links WHERE from_id = ? AND to_id = ? AND kind = ?",
            (from_id, to_id, args.kind),
        )
        conn.commit()
    finally:
        conn.close()
    return 0


def _coverage(argv: list[str]) -> int:
    parser = _parser("helix entry coverage")
    parser.add_argument("--triplet", action="store_true")
    parser.add_argument("--axis", action="store_true")
    parser.add_argument("--stack", action="store_true")
    parser.add_argument("--lifecycle", action="store_true")
    parser.add_argument("--sprint", action="store_true")
    parser.add_argument("--agent", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    if not args.triplet:
        print("エラー: coverage には --triplet が必要です", file=sys.stderr)
        return EXIT_USAGE

    AXES = ("design", "plan", "code", "schema", "test", "review", "evidence")
    STACKS = ("front", "back", "contract", "fullstack", "infra", "n/a")
    LIFECYCLES = ("initial", "addition", "modification", "migration", "deprecation", "removed")

    conn = _connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        rows = conn.execute(
            """
            SELECT axis, COALESCE(stack, 'n/a') AS stack, lifecycle, COUNT(*) AS count
            FROM entries
            GROUP BY axis, COALESCE(stack, 'n/a'), lifecycle
            """
        ).fetchall()
    finally:
        conn.close()

    counts = {(row["axis"], row["stack"], row["lifecycle"]): int(row["count"]) for row in rows}
    triplet = []
    for axis in AXES:
        for stack in STACKS:
            for lifecycle in LIFECYCLES:
                count = counts.get((axis, stack, lifecycle), 0)
                triplet.append(
                    {
                        "axis": axis,
                        "stack": stack,
                        "lifecycle": lifecycle,
                        "count": count,
                        "ratio": (count / total) if total else 0.0,
                    }
                )

    if args.as_json:
        print(json.dumps({"triplet": triplet}, ensure_ascii=False, indent=2))
        return 0

    for item in triplet:
        print(
            f"{item['axis']}\t{item['stack']}\t{item['lifecycle']}\t"
            f"{item['count']}\t{item['ratio']:.6f}"
        )
    return 0
