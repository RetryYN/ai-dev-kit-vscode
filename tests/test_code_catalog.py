import json
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cli" / "lib"))

import code_catalog  # noqa: E402
import helix_db  # noqa: E402


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def write(repo: Path, rel_path: str, text: str) -> Path:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True, capture_output=True, text=True)
    return path


def test_excluded_patterns_classify_fixed_operational_paths() -> None:
    assert code_catalog.classify_bucket("setup.sh", "setup_task") == "excluded"
    assert code_catalog.classify_bucket("skills/agent-skills/hooks/foo.sh", "hook_task") == "excluded"
    assert code_catalog.classify_bucket("verify/bar.sh", "verify_task") == "excluded"


def test_private_helper_bucket_for_underscore_symbols() -> None:
    assert code_catalog.classify_bucket("cli/lib/x.py", "_helper") == "private_helper"


def test_public_symbols_are_coverage_eligible() -> None:
    assert code_catalog.classify_bucket("cli/lib/x.py", "foo", "function") == "coverage_eligible"
    assert code_catalog.classify_bucket("cli/lib/x.py", "Bar", "class") == "coverage_eligible"


def test_non_indexable_paths_prefilter() -> None:
    true_paths = [
        "test_foo.py",
        "tests/x.py",
        "cli/tests/y.py",
        "fixture/z.py",
        "generated/a.py",
        "vendor/b.py",
    ]
    for rel_path in true_paths:
        assert code_catalog.is_non_indexable_path(rel_path)
    assert not code_catalog.is_non_indexable_path("cli/lib/c.py")


def test_python_symbol_line_resolves_marker_offset(tmp_path: Path) -> None:
    source = write(
        init_repo(tmp_path),
        "cli/lib/offset.py",
        "# @helix:index id=x.offset domain=cli/lib summary=offset marker\n\n"
        "def target():\n"
        "    return 1\n",
    )
    assert code_catalog.resolve_symbol_line(source, 1) == 3
    [entry] = code_catalog.scan_file(source)
    assert entry["line_no"] == 1
    assert entry["symbol_line"] == 3


def test_bash_symbol_line_resolves_function(tmp_path: Path) -> None:
    source = write(
        init_repo(tmp_path),
        "setup.sh",
        "# @helix:index id=setup.run domain=ops summary=setup runner\n"
        "function run_setup {\n"
        "  true\n"
        "}\n",
    )
    assert code_catalog.resolve_symbol_line(source, 1) == 2


def test_default_seed_metadata_for_three_buckets() -> None:
    assert code_catalog.default_seed_metadata("coverage_eligible", covered=True) == {
        "seed_candidate": True,
        "seed_promotable": False,
    }
    assert code_catalog.default_seed_metadata("private_helper", covered=True) == {
        "seed_candidate": True,
        "seed_promotable": False,
    }
    assert code_catalog.default_seed_metadata("excluded", covered=True) == {
        "seed_candidate": False,
        "seed_promotable": False,
    }


def test_jsonl_entry_contains_bucket_symbol_line_and_metadata(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write(
        repo,
        "cli/lib/catalog_fixture.py",
        "# @helix:index id=catalog.fixture domain=cli/lib summary=catalog fixture\n"
        "def fixture_symbol():\n"
        "    return 1\n",
    )
    entries = code_catalog.scan_tracked_files(repo)
    assert entries
    jsonl_path = repo / ".helix/cache/code-catalog.jsonl"
    code_catalog.write_jsonl(entries, jsonl_path)
    row = json.loads(jsonl_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["bucket"] == "coverage_eligible"
    assert row["symbol_line"] == 2
    assert row["metadata"]["seed_candidate"] is True
    assert row["metadata"]["seed_promotable"] is False


def test_non_indexable_files_do_not_emit_jsonl_entries(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write(
        repo,
        "tests/indexed.py",
        "# @helix:index id=tests.hidden domain=tests summary=hidden test marker\n"
        "def hidden():\n"
        "    return 1\n",
    )
    write(
        repo,
        "cli/lib/visible.py",
        "# @helix:index id=visible.marker domain=cli/lib summary=visible marker\n"
        "def visible():\n"
        "    return 1\n",
    )
    entries = code_catalog.scan_tracked_files(repo)
    assert [entry["id"] for entry in entries] == ["visible.marker"]


def test_compute_uncovered_includes_bucket_and_seed_fields(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write(
        repo,
        "cli/lib/uncovered_fixture.py",
        "def public_symbol():\n"
        "    return 1\n\n"
        "def _private_symbol():\n"
        "    return 2\n",
    )
    payload = code_catalog.compute_uncovered(repo)
    by_symbol = {item["symbol"]: item for item in payload["items"]}
    assert by_symbol["public_symbol"]["bucket"] == "coverage_eligible"
    assert by_symbol["public_symbol"]["seed_candidate"] is True
    assert by_symbol["public_symbol"]["seed_promotable"] is False
    assert by_symbol["_private_symbol"]["bucket"] == "private_helper"
    assert by_symbol["_private_symbol"]["seed_candidate"] is False


def coverage_report_repo(tmp_path: Path) -> Path:
    repo = init_repo(tmp_path)
    write(
        repo,
        "cli/lib/report_fixture.py",
        "# @helix:index id=report.covered domain=cli/lib summary=covered public\n"
        "def covered_public():\n"
        "    return 1\n\n"
        "def uncovered_public():\n"
        "    return 2\n\n"
        "# @helix:index id=report.private domain=cli/lib summary=covered private\n"
        "def _covered_private():\n"
        "    return 3\n\n"
        "def _uncovered_private():\n"
        "    return 4\n",
    )
    write(
        repo,
        "setup.sh",
        "setup_task() {\n"
        "  true\n"
        "}\n",
    )
    entries = code_catalog.scan_tracked_files(repo)
    private_entry = next(entry for entry in entries if entry["id"] == "report.private")
    private_entry["metadata"]["seed_promotable"] = True
    code_catalog.write_jsonl(entries, repo / ".helix/cache/code-catalog.jsonl")
    return repo


def test_compute_coverage_report_returns_covered_and_uncovered_union(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="all")
    by_symbol = {item["symbol"]: item for item in payload["items"]}
    assert {"covered_public", "uncovered_public", "_covered_private", "_uncovered_private", "setup_task"} <= set(by_symbol)
    assert by_symbol["covered_public"]["id"] == "report.covered"
    assert "id" not in by_symbol["uncovered_public"]
    assert "metadata" not in by_symbol["covered_public"]


def test_filter_by_bucket_coverage_eligible(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="coverage_eligible")
    assert {item["bucket"] for item in payload["items"]} == {"coverage_eligible"}


def test_filter_by_bucket_private_helper(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="private_helper")
    assert {item["symbol"] for item in payload["items"]} == {"_covered_private", "_uncovered_private"}


def test_filter_by_seed_candidate_true(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="all", seed_candidate="true")
    assert {item["symbol"] for item in payload["items"]} == {"covered_public", "uncovered_public", "_covered_private"}


def test_filter_by_seed_promotable_false(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="all", seed_promotable="false")
    assert "_covered_private" not in {item["symbol"] for item in payload["items"]}
    assert all(item["seed_promotable"] is False for item in payload["items"])


def test_summary_bucket_counts_present(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="all")
    assert payload["summary"]["bucket_counts"] == {
        "coverage_eligible": 2,
        "private_helper": 2,
        "excluded": 1,
    }


def test_summary_seed_candidate_count_present(tmp_path: Path) -> None:
    payload = code_catalog.compute_coverage_report(coverage_report_repo(tmp_path), bucket="all")
    assert payload["summary"]["seed_candidate_count"] == 3
    assert payload["summary"]["seed_promotable_count"] == 1


def test_coverage_pct_unchanged_by_bucket_filter(tmp_path: Path) -> None:
    repo = coverage_report_repo(tmp_path)
    all_payload = code_catalog.compute_coverage_report(repo, bucket="all")
    private_payload = code_catalog.compute_coverage_report(repo, bucket="private_helper")
    assert all_payload["summary"]["coverage_pct"] == private_payload["summary"]["coverage_pct"] == 50.0


def test_compute_coverage_report_scope_cli_lib_returns_more_eligible(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write(
        repo,
        "cli/lib/code_catalog.py",
        "def core_symbol():\n"
        "    return 1\n",
    )
    write(
        repo,
        "cli/lib/extra_module.py",
        "def extra_symbol():\n"
        "    return 2\n",
    )

    core5 = code_catalog.compute_coverage_report(repo, scope="core5", bucket="coverage_eligible")
    cli_lib = code_catalog.compute_coverage_report(repo, scope="cli-lib", bucket="coverage_eligible")

    assert core5["summary"]["eligible"] == 1
    assert cli_lib["summary"]["eligible"] == 2
    assert cli_lib["summary"]["eligible"] > core5["summary"]["eligible"]


def test_three_bucket_classification_deterministic(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    jsonl_path = repo / ".helix/cache/code-catalog.jsonl"
    db_path = repo / ".helix/helix.db"
    write(
        repo,
        "cli/lib/public_fixture.py",
        "# @helix:index id=fixture.public domain=cli/lib summary=public fixture\n"
        "def public_symbol():\n"
        "    return 1\n",
    )
    write(
        repo,
        "cli/lib/private_fixture.py",
        "# @helix:index id=fixture.private domain=cli/lib summary=private fixture\n"
        "def _private_symbol():\n"
        "    return 2\n",
    )
    write(
        repo,
        "setup.sh",
        "# @helix:index id=fixture.excluded domain=ops summary=excluded fixture\n"
        "setup_task() {\n"
        "  true\n"
        "}\n",
    )

    code_catalog.rebuild_catalog(repo, jsonl_path, db_path)
    first_rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    first_projection = {
        row["id"]: {"bucket": row["bucket"], "symbol_line": row["symbol_line"]}
        for row in first_rows
    }

    code_catalog.rebuild_catalog(repo, jsonl_path, db_path)
    second_rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    second_projection = {
        row["id"]: {"bucket": row["bucket"], "symbol_line": row["symbol_line"]}
        for row in second_rows
    }

    assert first_projection == {
        "fixture.excluded": {"bucket": "excluded", "symbol_line": 2},
        "fixture.private": {"bucket": "private_helper", "symbol_line": 2},
        "fixture.public": {"bucket": "coverage_eligible", "symbol_line": 2},
    }
    assert second_projection == first_projection


def test_migration_v14_to_v15_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-v14.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
        INSERT INTO schema_version (version, applied_at) VALUES (14, '2026-05-03T00:00:00');
        CREATE TABLE code_index (
          id TEXT PRIMARY KEY,
          domain TEXT NOT NULL,
          summary TEXT NOT NULL,
          path TEXT NOT NULL,
          line_no INTEGER NOT NULL,
          since TEXT,
          related TEXT,
          source_hash TEXT,
          updated_at DATETIME
        );
        INSERT INTO code_index (id, domain, summary, path, line_no)
        VALUES ('legacy.entry', 'cli/lib', 'legacy entry', 'cli/lib/legacy.py', 7);
        """
    )

    helix_db.migrate(conn)
    helix_db.migrate(conn)

    version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    columns = {row[1] for row in conn.execute("PRAGMA table_info(code_index)").fetchall()}
    row = conn.execute(
        "SELECT id, symbol_line, bucket FROM code_index WHERE id = 'legacy.entry'"
    ).fetchone()
    versions = [row[0] for row in conn.execute("SELECT version FROM schema_version ORDER BY version")]
    conn.close()

    assert version == 15
    assert versions == [14, 15]
    assert {"bucket", "symbol_line"} <= columns
    assert row == ("legacy.entry", 7, "coverage_eligible")


def test_non_indexable_takes_priority_over_excluded(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    jsonl_path = repo / ".helix/cache/code-catalog.jsonl"
    write(
        repo,
        "tests/setup.sh",
        "# @helix:index id=tests.setup domain=tests summary=tests setup\n"
        "tests_setup() {\n"
        "  true\n"
        "}\n",
    )
    write(
        repo,
        "generated/setup.sh",
        "# @helix:index id=generated.setup domain=generated summary=generated setup\n"
        "generated_setup() {\n"
        "  true\n"
        "}\n",
    )
    write(
        repo,
        "setup.sh",
        "# @helix:index id=root.setup domain=ops summary=root setup\n"
        "root_setup() {\n"
        "  true\n"
        "}\n",
    )

    code_catalog.rebuild_catalog(repo, jsonl_path, repo / ".helix/helix.db")
    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]

    assert {row["id"] for row in rows} == {"root.setup"}
    assert rows[0]["bucket"] == "excluded"


def test_excluded_only_for_actual_paths(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write(
        repo,
        "cli/lib/setup.sh",
        "# @helix:index id=cli.setup domain=cli/lib summary=cli setup\n"
        "cli_setup() {\n"
        "  true\n"
        "}\n",
    )

    entries = code_catalog.scan_tracked_files(repo)

    assert len(entries) == 1
    assert entries[0]["id"] == "cli.setup"
    assert entries[0]["bucket"] == "coverage_eligible"
