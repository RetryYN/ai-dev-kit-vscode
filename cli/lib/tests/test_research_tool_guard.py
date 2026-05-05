import py_compile
import sys
from io import StringIO
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import research_tool_guard


MODULE_PATH = LIB_DIR / "research_tool_guard.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_check_tool_allows_valid_websearch_payload(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO('{"tool_name":"WebSearch","tool_input":{"query":"sdk"}}'))

    assert research_tool_guard.main(["check-tool"]) == 0


def test_check_tool_allows_empty_payload(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO(""))

    assert research_tool_guard.main(["check-tool"]) == 0


def test_check_tool_denies_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO("{not valid json"))

    assert research_tool_guard.main(["check-tool"]) == 1


def test_check_tool_denies_non_dict_payload(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO('["WebSearch"]'))

    assert research_tool_guard.main(["check-tool"]) == 1


def test_check_tool_denies_unexpected_tool(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO('{"tool_name":"Bash","tool_input":{"command":"ls"}}'))

    assert research_tool_guard.main(["check-tool"]) == 1


def test_check_tool_allows_webfetch_payload(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdin", StringIO('{"tool_name":"WebFetch","tool_input":{"url":"https://example.com"}}'))

    assert research_tool_guard.main(["check-tool"]) == 0
