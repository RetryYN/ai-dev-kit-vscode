import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import contract_registry
import helix_db


def _write_contract(path: Path, title: str, version: str, extra: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            'openapi: "cli-contract/1.0"\n'
            "info:\n"
            f"  title: {title}\n"
            f"  version: {version}\n"
            "commands:\n"
            "  - name: sample\n"
            f"{extra}"
        ),
        encoding="utf-8",
    )


def test_scan_d_api_yamls_extracts_contract_dicts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_contract(repo_root / "docs" / "features" / "alpha" / "D-API" / "api.yaml", "alpha", "1.0.0")
    _write_contract(repo_root / "docs" / "features" / "beta" / "D-API" / "api.yaml", "beta", "2.0.0")

    contracts = contract_registry.scan_d_api_yamls(repo_root)

    assert [item["source_path"] for item in contracts] == [
        "docs/features/alpha/D-API/api.yaml",
        "docs/features/beta/D-API/api.yaml",
    ]
    assert all(item["contract_type"] == "cli-contract" for item in contracts)
    assert contracts[0]["symbol_id"] == "docs.features.alpha.D-API.api"


def test_compute_schema_hash_is_stable_and_sensitive() -> None:
    spec_a = {"info": {"title": "demo", "version": "1.0.0"}, "commands": [{"name": "run"}]}
    spec_b = {"commands": [{"name": "run"}], "info": {"version": "1.0.0", "title": "demo"}}
    spec_c = {"info": {"title": "demo", "version": "2.0.0"}, "commands": [{"name": "run"}]}

    assert contract_registry.compute_schema_hash(spec_a) == contract_registry.compute_schema_hash(spec_b)
    assert contract_registry.compute_schema_hash(spec_a) != contract_registry.compute_schema_hash(spec_c)


def test_bulk_insert_is_idempotent_by_schema_hash(tmp_path: Path) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))

    contracts = [
        {
            "contract_type": "cli-contract",
            "source_path": "docs/features/demo/D-API/api.yaml",
            "symbol_id": "docs.features.demo.D-API.api",
            "version": "1.0.0",
            "schema_hash": "hash-1",
            "breaking_change_flag": 0,
            "introduced_plan": None,
            "raw_spec": '{"info":{"title":"demo"}}',
        }
    ]

    first = contract_registry.bulk_insert(db_path, contracts)
    second = contract_registry.bulk_insert(db_path, contracts)

    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM contract_entries").fetchone()
    finally:
        conn.close()

    assert first == 1
    assert second == 0
    assert row["count"] == 1


def test_find_by_symbol_returns_inserted_contracts(tmp_path: Path) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))
    contract_registry.bulk_insert(
        db_path,
        [
            {
                "contract_type": "cli-contract",
                "source_path": "docs/features/demo/D-API/api.yaml",
                "symbol_id": "docs.features.demo.D-API.api",
                "version": "1.0.0",
                "schema_hash": "hash-lookup",
                "breaking_change_flag": 0,
                "introduced_plan": "PLAN-063",
                "raw_spec": '{"info":{"title":"demo"}}',
            }
        ],
    )

    rows = contract_registry.find_by_symbol(db_path, "docs.features.demo.D-API.api")

    assert len(rows) == 1
    assert rows[0]["schema_hash"] == "hash-lookup"


def test_v16_to_v17_migration_preserves_invocation_log(tmp_path: Path) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO invocation_log (
                timestamp, type, role, model, task_id, plan_id, sprint,
                input_bytes, output_bytes, duration_ms, decision, cost_cents,
                parent_invocation_id, raw_meta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-05-12T00:00:00",
                "codex",
                "se",
                "gpt-5.4",
                "W-2pre",
                "PLAN-063",
                ".2",
                10,
                20,
                30,
                "passed",
                0.5,
                None,
                "{}",
            ),
        )
        conn.execute("DELETE FROM schema_version WHERE version >= 17")
        for table in ("contract_entries", "code_edges", "entries", "links"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
    finally:
        conn.close()

    helix_db.init_db(str(db_path))

    conn = helix_db.get_connection(db_path)
    try:
        preserved = conn.execute("SELECT plan_id, task_id FROM invocation_log").fetchone()
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('contract_entries', 'code_edges')"
            ).fetchall()
        }
    finally:
        conn.close()

    assert preserved["plan_id"] == "PLAN-063"
    assert preserved["task_id"] == "W-2pre"
    assert tables == {"contract_entries", "code_edges"}
