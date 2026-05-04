import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import hook_payload


MODULE_PATH = LIB_DIR / "hook_payload.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_extracts_write_and_tool_response_paths() -> None:
    safe_paths, rejected = hook_payload.extract_changed_paths(
        {
            "tool_input": {"file_path": "src/app.ts"},
            "tool_response": {"filePath": "docs/設計.md"},
        }
    )

    assert safe_paths == ["src/app.ts", "docs/設計.md"]
    assert rejected == []


def test_extracts_multiedit_and_deduplicates_paths() -> None:
    safe_paths, rejected = hook_payload.extract_changed_paths(
        {
            "tool_input": {
                "file_path": "src/app.ts",
                "files": [{"file_path": "src/app.ts"}, {"path": "src/other.ts"}],
            }
        }
    )

    assert safe_paths == ["src/app.ts", "src/other.ts"]
    assert rejected == []


def test_rejects_shell_metacharacters() -> None:
    safe_paths, rejected = hook_payload.extract_changed_paths(
        {"tool_input": {"file_path": "src/app.ts;touch/tmp/pwned"}}
    )

    assert safe_paths == []
    assert rejected == ["src/app.ts;touch/tmp/pwned"]
