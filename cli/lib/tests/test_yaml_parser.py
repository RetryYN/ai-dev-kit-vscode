import json
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import yaml_parser


def test_get_nested_reads_deep_dotpath() -> None:
    data = yaml_parser.parse_yaml("a:\n  b:\n    c: 42\n")

    assert yaml_parser.get_nested(data, "a.b.c") == 42


def test_get_nested_prefers_existing_dotted_key() -> None:
    data = yaml_parser.parse_yaml("gates:\n  G1.5:\n    status: passed\n")

    assert yaml_parser.get_nested(data, "gates.G1.5.status") == "passed"


def test_get_nested_returns_none_for_missing_key() -> None:
    data = yaml_parser.parse_yaml("a:\n  b: value\n")

    assert yaml_parser.get_nested(data, "a.c") is None


def test_set_nested_creates_missing_containers() -> None:
    data = {}

    yaml_parser.set_nested(data, "phase.current.step", "L4")

    assert data == {"phase": {"current": {"step": "L4"}}}


def test_set_nested_preserves_existing_dotted_key() -> None:
    data = {"gates": {"G1.5": {"status": "pending"}}}

    yaml_parser.set_nested(data, "gates.G1.5.status", "passed")

    assert data["gates"]["G1.5"]["status"] == "passed"


def test_dump_yaml_round_trips_simple_structure() -> None:
    original = {"a": {"b": 1}, "flag": True, "name": "sample"}

    dumped = yaml_parser.dump_yaml(original)
    parsed = yaml_parser.parse_yaml(dumped)

    assert parsed == original


def test_dump_yaml_round_trips_block_list_of_mappings() -> None:
    original = {
        "status": "draft",
        "finalized_at": None,
        "revision_history": [
            {
                "revision": 1,
                "action": "plan_reset",
                "from_status": "finalized",
                "finalized_at": "2026-04-30T15:57:34Z",
            }
        ],
    }

    dumped = yaml_parser.dump_yaml(original)
    parsed = yaml_parser.parse_yaml(dumped)

    assert parsed == original


def test_parse_literal_block_scalar_in_mapping() -> None:
    data = yaml_parser.parse_yaml("task: |\n  line one\n  line two\nnext: ok\n")

    assert data["task"] == "line one\nline two"
    assert data["next"] == "ok"


def test_parse_quoted_key_with_special_chars() -> None:
    data = yaml_parser.parse_yaml('type_casting:\n  "null/None/~/empty": null\n')

    assert data["type_casting"]["null/None/~/empty"] is None


def test_parse_literal_block_scalar_in_list_mapping() -> None:
    data = yaml_parser.parse_yaml("ai:\n  - role: tl\n    task: |\n      check A\n      check B\n")

    assert data["ai"][0]["role"] == "tl"
    assert data["ai"][0]["task"] == "check A\ncheck B"


def test_parse_list_mapping_with_nested_sequence_value() -> None:
    data = yaml_parser.parse_yaml(
        """
applies_when:
  all:
    - drive: [be]
    - any:
        - has_external_api: true
        - has_db_migration: true
"""
    )

    assert data == {
        "applies_when": {
            "all": [
                {"drive": ["be"]},
                {"any": [{"has_external_api": True}, {"has_db_migration": True}]},
            ]
        }
    }


def test_parse_list_mapping_keeps_sibling_keys_outside_empty_child() -> None:
    data = yaml_parser.parse_yaml(
        """
items:
  - key:
      nested: 1
    other: 2
"""
    )

    assert data == {"items": [{"key": {"nested": 1}, "other": 2}]}


def test_dump_yaml_round_trips_multiline_string() -> None:
    original = {"ai": [{"role": "tl", "task": "check A\ncheck B"}]}

    dumped = yaml_parser.dump_yaml(original)
    parsed = yaml_parser.parse_yaml(dumped)

    assert parsed == original


def test_build_output_with_header_preserves_comment_block() -> None:
    text = "# header one\n# header two\na: 1\n"

    output = yaml_parser._build_output_with_header(text, {"a": 2})

    assert output.startswith("# header one\n# header two\n\n")
    assert "a: 2" in output


def test_write_yaml_safe_updates_file_and_keeps_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("# header\na:\n  b: old\n", encoding="utf-8")

    yaml_parser.write_yaml_safe(str(yaml_path), "a.b", "new")

    assert "b: new" in yaml_path.read_text(encoding="utf-8")
    assert (tmp_path / ".helix" / "locks" / "yaml-phase.lock").exists()


def test_write_yaml_safe_uses_file_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("a: 1\n", encoding="utf-8")
    calls: list[str] = []

    class DummyLock:
        def __enter__(self):
            calls.append("enter")
            return 0

        def __exit__(self, exc_type, exc, tb):
            calls.append("exit")
            return False

    def fake_file_lock(name: str, timeout: float = 5.0, lock_dir=None):
        assert name == "yaml-phase"
        return DummyLock()

    monkeypatch.setattr(yaml_parser, "file_lock", fake_file_lock)

    yaml_parser.write_yaml_safe(str(yaml_path), "a", "2")

    assert calls == ["enter", "exit"]


def test_write_yaml_safe_parallel_processes_smoke(tmp_path: Path) -> None:
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("gates:\n  G2:\n    status: pending\n", encoding="utf-8")
    parser = Path(yaml_parser.__file__).resolve()

    proc1 = subprocess.Popen(
        [sys.executable, str(parser), "write", str(yaml_path), "gates.G2.status", "passed"]
    )
    proc2 = subprocess.Popen(
        [sys.executable, str(parser), "write", str(yaml_path), "gates.G3.status", "passed"]
    )

    assert proc1.wait(timeout=10) == 0
    assert proc2.wait(timeout=10) == 0

    data = yaml_parser.parse_yaml(yaml_path.read_text(encoding="utf-8"))
    assert yaml_parser.get_nested(data, "gates.G2.status") == "passed"
    assert yaml_parser.get_nested(data, "gates.G3.status") == "passed"


def test_main_dump_outputs_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    yaml_path = tmp_path / "state.yaml"
    yaml_path.write_text("a:\n  b: test\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["yaml_parser.py", "dump", str(yaml_path)])

    yaml_parser.main()
    output = capsys.readouterr().out

    assert json.loads(output) == {"a": {"b": "test"}}


def test_main_read_invalid_yaml_exits_with_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "broken.yaml"
    yaml_path.write_text("a:\n  - not-supported\n  b: 1\n@", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["yaml_parser.py", "read", str(yaml_path), "a.b"])

    with pytest.raises(SystemExit) as exc_info:
        yaml_parser.main()

    assert exc_info.value.code == 1
    assert "YAML 解析失敗" in capsys.readouterr().err


def test_main_read_missing_key_prints_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    yaml_path = tmp_path / "state.yaml"
    yaml_path.write_text("a:\n  b: 1\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["yaml_parser.py", "read", str(yaml_path), "a.c"])

    yaml_parser.main()

    assert capsys.readouterr().out == ""
