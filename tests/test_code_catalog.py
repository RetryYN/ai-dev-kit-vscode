import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cli" / "lib"))

import code_catalog  # noqa: E402


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
