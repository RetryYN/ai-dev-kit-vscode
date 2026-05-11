import sqlite3
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import code_edges
import helix_db


def test_extract_python_edges_captures_import_call_and_inherit(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "import os\n"
        "from pathlib import Path\n"
        "class Child(BaseModel):\n"
        "    pass\n"
        "print(Path('x'))\n",
        encoding="utf-8",
    )

    edges = code_edges.extract_python_edges(source)
    edge_pairs = {(edge["edge_type"], edge["to_external_ref"]) for edge in edges}

    assert ("import", "os") in edge_pairs
    assert ("import", "pathlib.Path") in edge_pairs
    assert ("inherit", "BaseModel") in edge_pairs
    assert ("call", "print") in edge_pairs
    assert ("call", "Path") in edge_pairs


def test_extract_sql_edges_reads_cursor_execute_tables(tmp_path: Path) -> None:
    source = tmp_path / "sql_sample.py"
    source.write_text(
        "def run(cursor):\n"
        "    cursor.execute('CREATE TABLE demo (id INTEGER)')\n"
        "    cursor.execute('INSERT INTO demo VALUES (1)')\n"
        "    cursor.execute('SELECT * FROM demo')\n",
        encoding="utf-8",
    )

    edges = code_edges.extract_sql_edges(source)
    edge_pairs = {(edge["edge_type"], edge["to_external_ref"]) for edge in edges}

    assert ("sql_create", "demo") in edge_pairs
    assert ("sql_insert", "demo") in edge_pairs
    assert ("sql_from", "demo") in edge_pairs


def test_extract_yaml_refs_reads_anchor_ref_and_role(tmp_path: Path) -> None:
    source = tmp_path / "contract.yaml"
    source.write_text(
        "defaults: &base\n"
        "  role: reviewer\n"
        "use_defaults: *base\n"
        "ref: docs/features/demo/D-API/api.yaml\n",
        encoding="utf-8",
    )

    edges = code_edges.extract_yaml_refs(source)
    edge_pairs = {(edge["edge_type"], edge["to_external_ref"]) for edge in edges}

    assert ("yaml_anchor", "base") in edge_pairs
    assert ("yaml_ref", "base") in edge_pairs
    assert ("yaml_role", "reviewer") in edge_pairs
    assert ("yaml_ref", "docs/features/demo/D-API/api.yaml") in edge_pairs


def test_bulk_insert_persists_edge_rows(tmp_path: Path) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))

    inserted = code_edges.bulk_insert(
        db_path,
        [
            {
                "from_entry_id": 101,
                "to_entry_id": 202,
                "to_external_ref": "demo.target",
                "edge_type": "call",
                "weight": 2,
                "source_line": 14,
                "raw_meta": '{"source_path":"cli/lib/demo.py"}',
            }
        ],
    )

    conn = helix_db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT from_entry_id, to_entry_id, edge_type, weight FROM code_edges"
        ).fetchone()
    finally:
        conn.close()

    assert inserted == 1
    assert row["from_entry_id"] == 101
    assert row["to_entry_id"] == 202
    assert row["edge_type"] == "call"
    assert row["weight"] == 2


def test_rebuild_edges_scans_cli_lib_python_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cli_lib = repo_root / "cli" / "lib"
    cli_lib.mkdir(parents=True, exist_ok=True)
    (cli_lib / "a.py").write_text("import os\nprint(os.getcwd())\n", encoding="utf-8")
    (cli_lib / "b.py").write_text(
        "class Child(Base):\n"
        "    pass\n"
        "def run(cursor):\n"
        "    cursor.execute('SELECT * FROM sample')\n",
        encoding="utf-8",
    )
    db_path = repo_root / ".helix" / "helix.db"
    helix_db.init_db(str(db_path))

    inserted = code_edges.rebuild_edges(db_path, repo_root)

    conn = helix_db.get_connection(db_path)
    try:
        count_row = conn.execute("SELECT COUNT(*) AS count FROM code_edges").fetchone()
    finally:
        conn.close()

    assert inserted >= 5
    assert count_row["count"] == inserted
