#!/usr/bin/env python3
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import yaml

import helix_db


EXIT_USAGE = 64
EXIT_NOT_FOUND = 2


class HelixArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"{self.prog}: error: {message}\n")


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_db_path() -> Path:
    return Path(helix_db.resolve_default_db_path())


def _parser(prog: str) -> HelixArgumentParser:
    return HelixArgumentParser(prog=prog, add_help=True)


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def compute_schema_hash(spec_dict) -> str:
    canonical = _canonical_json(spec_dict)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _relative_source_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _infer_contract_type(spec_dict: dict) -> str:
    openapi = str(spec_dict.get("openapi") or "").strip()
    if "/" in openapi:
        return openapi.split("/", 1)[0]
    if openapi:
        return openapi
    return "yaml-contract"


def _infer_symbol_id(source_path: str) -> str:
    stem = source_path[:-5] if source_path.endswith(".yaml") else source_path
    return stem.replace("/", ".")


def _infer_version(spec_dict: dict) -> str | None:
    info = spec_dict.get("info")
    if isinstance(info, dict) and info.get("version"):
        return str(info["version"])
    version = spec_dict.get("version")
    if version is not None:
        return str(version)
    openapi = str(spec_dict.get("openapi") or "").strip()
    if "/" in openapi:
        return openapi.split("/", 1)[1]
    return None


def _infer_plan(source_path: str) -> str | None:
    for part in source_path.split("/"):
        if part.startswith("PLAN-"):
            return part
    return None


def _load_spec(path: Path) -> dict:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {"value": loaded}


def scan_d_api_yamls(repo_root) -> list[dict]:
    root = Path(repo_root).resolve()
    pattern = "docs/features/**/D-API/*.yaml"
    contracts: list[dict] = []
    for path in sorted(root.glob(pattern)):
        spec_dict = _load_spec(path)
        source_path = _relative_source_path(path, root)
        contracts.append(
            {
                "contract_type": _infer_contract_type(spec_dict),
                "source_path": source_path,
                "symbol_id": _infer_symbol_id(source_path),
                "version": _infer_version(spec_dict),
                "schema_hash": compute_schema_hash(spec_dict),
                "breaking_change_flag": 0,
                "introduced_plan": _infer_plan(source_path),
                "raw_spec": _canonical_json(spec_dict),
            }
        )
    return contracts


def _connect_write(db_path: Path) -> sqlite3.Connection:
    helix_db._prepare_db_path(db_path)
    conn = helix_db.get_connection(db_path)
    helix_db._ensure_schema(conn)
    return conn


def bulk_insert(db_path, contracts) -> int:
    target = Path(db_path)
    conn = _connect_write(target)
    try:
        existing_hashes = {
            row["schema_hash"]
            for row in conn.execute(
                "SELECT schema_hash FROM contract_entries WHERE schema_hash IS NOT NULL"
            ).fetchall()
        }
        inserted = 0
        for contract in contracts:
            schema_hash = contract.get("schema_hash")
            if schema_hash and schema_hash in existing_hashes:
                continue
            conn.execute(
                """
                INSERT INTO contract_entries (
                    contract_type,
                    source_path,
                    symbol_id,
                    version,
                    schema_hash,
                    breaking_change_flag,
                    introduced_plan,
                    raw_spec
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contract.get("contract_type"),
                    contract.get("source_path"),
                    contract.get("symbol_id"),
                    contract.get("version"),
                    schema_hash,
                    int(contract.get("breaking_change_flag", 0)),
                    contract.get("introduced_plan"),
                    contract.get("raw_spec"),
                ),
            )
            if schema_hash:
                existing_hashes.add(schema_hash)
            inserted += 1
        conn.commit()
        return inserted
    finally:
        conn.close()


def find_by_symbol(db_path, symbol_id: str) -> list[dict]:
    conn = _connect_write(Path(db_path))
    try:
        rows = conn.execute(
            """
            SELECT id, contract_type, source_path, symbol_id, version, schema_hash,
                   breaking_change_flag, introduced_plan
            FROM contract_entries
            WHERE symbol_id = ?
            ORDER BY id
            """,
            (symbol_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _cmd_init(argv: list[str]) -> int:
    parser = _parser("contract_registry.py init")
    parser.add_argument("--repo-root", default=str(_default_repo_root()))
    parser.add_argument("--db-path", default=str(_default_db_path()))
    args = parser.parse_args(argv)

    contracts = scan_d_api_yamls(args.repo_root)
    inserted = bulk_insert(args.db_path, contracts)
    print(inserted)
    return 0


def _cmd_find(argv: list[str]) -> int:
    parser = _parser("contract_registry.py find")
    parser.add_argument("symbol_id")
    parser.add_argument("--db-path", default=str(_default_db_path()))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    rows = find_by_symbol(args.db_path, args.symbol_id)
    if not rows:
        print(f"contract not found: {args.symbol_id}", file=sys.stderr)
        return EXIT_NOT_FOUND

    if args.as_json:
        print(json.dumps({"contracts": rows}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    for row in rows:
        print(
            "\t".join(
                [
                    str(row.get("id") or ""),
                    str(row.get("contract_type") or ""),
                    str(row.get("symbol_id") or ""),
                    str(row.get("version") or ""),
                    str(row.get("source_path") or ""),
                ]
            )
        )
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: contract_registry.py <init|find> [...]", file=sys.stderr)
        return EXIT_USAGE

    command = sys.argv[1]
    argv = sys.argv[2:]
    if command == "init":
        return _cmd_init(argv)
    if command == "find":
        return _cmd_find(argv)

    print(f"Unknown command: {command}", file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
