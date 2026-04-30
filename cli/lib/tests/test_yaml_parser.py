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


def test_build_output_with_header_preserves_comment_block() -> None:
    text = "# header one\n# header two\na: 1\n"

    output = yaml_parser._build_output_with_header(text, {"a": 2})

    assert output.startswith("# header one\n# header two\n\n")
    assert "a: 2" in output


def test_write_yaml_safe_updates_file_and_keeps_lock(tmp_path: Path) -> None:
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("# header\na:\n  b: old\n", encoding="utf-8")

    yaml_parser.write_yaml_safe(str(yaml_path), "a.b", "new")

    assert "b: new" in yaml_path.read_text(encoding="utf-8")
    assert yaml_path.with_name("phase.yaml.lock").exists()


def test_write_yaml_safe_uses_file_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    yaml_path = tmp_path / "phase.yaml"
    yaml_path.write_text("a: 1\n", encoding="utf-8")
    calls: list[int] = []

    def fake_flock(_file, operation: int) -> None:
        calls.append(operation)

    monkeypatch.setattr(yaml_parser.fcntl, "flock", fake_flock)

    yaml_parser.write_yaml_safe(str(yaml_path), "a", "2")

    assert calls == [yaml_parser.fcntl.LOCK_EX, yaml_parser.fcntl.LOCK_UN]


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
