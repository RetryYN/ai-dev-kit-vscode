from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import code_catalog


REJECT_LOG_PATH = Path(".helix/cache/code-catalog-rejected.log")


def test_parse_helix_index_comment_basic() -> None:
    entry = code_catalog.parse_helix_index_comment("# @helix:index id=foo domain=bar summary=baz")

    assert entry is not None
    assert entry["id"] == "foo"
    assert entry["domain"] == "bar"
    assert entry["summary"] == "baz"
    assert entry["related"] == []


def test_scan_file_picks_python_def(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=sample.foo domain=cli/lib summary=foo関数を登録する\n"
        "def foo():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    entries = code_catalog.scan_file(source)

    assert len(entries) == 1
    assert entries[0]["id"] == "sample.foo"
    assert entries[0]["path"] == source.as_posix()
    assert entries[0]["line_no"] == 1
    assert entries[0]["source_hash"]


def test_should_redact_detects_auth_token() -> None:
    should_skip, reason = code_catalog.should_redact("auth_token を含む要約")

    assert should_skip is True
    assert reason is not None


def test_should_redact_detects_long_token() -> None:
    should_skip, reason = code_catalog.should_redact("summary with token " + "A" * 32)

    assert should_skip is True
    assert reason == "secret_like_value"


def test_should_redact_allows_safe_words() -> None:
    for word in ["tokenize", "passwordless", "credentialing"]:
        should_skip, reason = code_catalog.should_redact(f"Summary includes {word}")
        assert should_skip is False
        assert reason is None


def test_should_redact_allows_version_string() -> None:
    should_skip, reason = code_catalog.should_redact("v1.0.0")
    assert should_skip is False
    assert reason is None

    should_skip, reason = code_catalog.should_redact("commit hash abc1234")
    assert should_skip is False
    assert reason is None


def test_scan_file_logs_rejection() -> None:
    with tempfile.TemporaryDirectory() as workdir:
        source = Path(workdir) / "code_catalog_reject_sample.py"
        source.write_text(
            "# @helix:index id=foo domain=bar summary=auth_token is forbidden\n",
            encoding="utf-8",
        )
        if REJECT_LOG_PATH.exists():
            REJECT_LOG_PATH.unlink()

        entries = code_catalog.scan_file(source)

        assert entries == []
        lines = REJECT_LOG_PATH.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1


def test_parse_helix_index_comment_parses_quoted_fields_and_related() -> None:
    entry = code_catalog.parse_helix_index_comment(
        "# @helix:index id=\"code-catalog.parse-frontmatter\" domain=cli/lib summary=\"YAML frontmatter を展開する\" related=common/security,workflow/design"
    )

    assert entry is not None
    assert entry["id"] == "code-catalog.parse-frontmatter"
    assert entry["domain"] == "cli/lib"
    assert entry["summary"] == "YAML frontmatter を展開する"
    assert entry["related"] == ["common/security", "workflow/design"]


def test_parse_helix_index_comment_ignores_incomplete_marker() -> None:
    assert code_catalog.parse_helix_index_comment("# @helix:index id=foo summary=missing-domain") is None


def test_parse_helix_index_comment_rejects_secret_like_summary() -> None:
    assert (
        code_catalog.parse_helix_index_comment(
            "# @helix:index id=foo domain=bar summary=secret token ABCDEFGHIJKLMNOPQRSTUVWXYZabcd1234"
        )
        is None
    )


def test_scan_file_skips_danger_summary_and_records_rejection_path(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "\n".join(
            [
                "# @helix:index id=ok-id domain=cli/lib summary=tokenize is allowed",
                "# @helix:index id=bad-id domain=cli/lib summary=api_key token leaked",
                "# @helix:index id=another-id domain=cli/lib summary=passwordless flow is allowed",
            ]
        ),
        encoding="utf-8",
    )

    if REJECT_LOG_PATH.exists():
        REJECT_LOG_PATH.unlink()

    entries = code_catalog.scan_file(source)

    assert len(entries) == 2
    assert [entry["id"] for entry in entries] == ["ok-id", "another-id"]
    rejected = REJECT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(rejected) == 1
    assert "bad-id" not in rejected[0]
    assert "danger_pattern" in rejected[0]


def test_scan_tracked_files_filters_supported_extensions(tmp_path: Path) -> None:
    with tempfile.TemporaryDirectory() as workdir:
        root = Path(workdir)
        python_file = root / "sample.py"
        text_file = root / "sample.txt"
        python_file.write_text("# @helix:index id=keep domain=cli/lib summary=keep.py", encoding="utf-8")
        text_file.write_text("# @helix:index id=skip domain=cli/lib summary=skip.txt", encoding="utf-8")
        import subprocess

        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "add", "sample.py", "sample.txt"], cwd=root, check=True, capture_output=True)

        entries = code_catalog.scan_tracked_files(root)

        assert [entry["id"] for entry in entries] == ["keep"]


def test_rebuild_catalog_writes_jsonl_and_returns_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jsonl_path = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    db_path = tmp_path / ".helix" / "helix.db"
    entries = [
        {
            "id": "cli-lib.foo",
            "domain": "cli/lib",
            "summary": "test summary",
            "path": "cli/lib/foo.py",
            "line_no": 1,
            "since": "v1",
            "related": [],
            "source_hash": "a" * 64,
            "updated_at": "2026-05-03T00:00:00+00:00",
        }
    ]

    def _scan(_path: Path) -> list[dict]:
        return entries

    synced: dict[str, bool] = {}

    def _sync(payload: list[dict], _db: Path) -> None:
        synced["called"] = True
        synced["count"] = len(payload)

    monkeypatch.setattr(code_catalog, "scan_tracked_files", _scan)
    monkeypatch.setattr(code_catalog, "sync_to_db", _sync)
    result = code_catalog.rebuild_catalog(tmp_path, jsonl_path, db_path)

    assert result["entry_count"] == 1
    assert jsonl_path.exists()
    assert synced.get("called") is True
    assert synced.get("count") == 1


def test_rebuild_catalog_rolls_back_jsonl_on_db_sync_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jsonl_path = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    db_path = tmp_path / ".helix" / "helix.db"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    original_content = (
        '{"id":"old.id","domain":"cli/lib","summary":"old","path":"old.py","line_no":1,'
        '"since":"v0","related":[],"source_hash":"0","updated_at":"2026-05-01T00:00:00+00:00"}\n'
    )
    jsonl_path.write_text(original_content, encoding="utf-8")

    def _scan(_path: Path) -> list[dict]:
        return [
            {
                "id": "new.id",
                "domain": "cli/lib",
                "summary": "new",
                "path": "new.py",
                "line_no": 2,
                "since": "v1",
                "related": [],
                "source_hash": "1",
                "updated_at": "2026-05-03T00:00:00+00:00",
            }
        ]

    monkeypatch.setattr(code_catalog, "scan_tracked_files", _scan)

    def _sync(_payload: list[dict], _db: Path) -> None:
        raise RuntimeError("sync failed")

    monkeypatch.setattr(code_catalog, "sync_to_db", _sync)

    with pytest.raises(RuntimeError):
        code_catalog.rebuild_catalog(tmp_path, jsonl_path, db_path)

    assert jsonl_path.read_text(encoding="utf-8") == original_content


def test_scan_file_skips_string_literals(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        'X = "# @helix:index id=str.foo domain=bar summary=stringliteral"\n',
        encoding="utf-8",
    )

    entries = code_catalog.scan_file(source)

    assert entries == []


def test_scan_file_only_comment_lines(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text(
        "# @helix:index id=comment.foo domain=bar summary=commentline\n"
        'X = "# @helix:index id=str.foo domain=bar summary=stringliteral"\n',
        encoding="utf-8",
    )

    entries = code_catalog.scan_file(source)

    assert [entry["id"] for entry in entries] == ["comment.foo"]


def test_scan_tracked_files_excludes_markdown(tmp_path: Path) -> None:
    root = tmp_path
    markdown_file = root / "sample.md"
    python_file = root / "sample.py"
    markdown_file.write_text("# @helix:index id=skip.md domain=docs summary=markdown\n", encoding="utf-8")
    python_file.write_text("# @helix:index id=keep.py domain=cli/lib summary=python\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "sample.md", "sample.py"], cwd=root, check=True, capture_output=True)

    entries = code_catalog.scan_tracked_files(root)

    assert ".md" not in code_catalog._TRACKED_SUFFIXES
    assert [entry["id"] for entry in entries] == ["keep.py"]


def test_rebuild_catalog_rejects_duplicate_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jsonl_path = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    db_path = tmp_path / ".helix" / "helix.db"

    def _scan(_path: Path) -> list[dict]:
        return [{"id": "duplicate.id"}, {"id": "duplicate.id"}]

    monkeypatch.setattr(code_catalog, "scan_tracked_files", _scan)

    with pytest.raises(ValueError, match=r"重複した id が検出されました: duplicate\.id \(2 箇所\)"):
        code_catalog.rebuild_catalog(tmp_path, jsonl_path, db_path)

    assert not jsonl_path.exists()
