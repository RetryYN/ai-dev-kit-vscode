from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import code_catalog


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
