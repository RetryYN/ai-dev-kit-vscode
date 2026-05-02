from __future__ import annotations

import sys
import tempfile
from pathlib import Path


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
