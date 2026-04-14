import copy
import json
import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import merge_settings


MODULE_PATH = LIB_DIR / "merge_settings.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_merge_adds_helix_hooks_once() -> None:
    settings = {"hooks": {"SessionStart": [{"hooks": [{"command": "custom-start"}]}]}}

    changed = merge_settings.merge(settings)
    changed_again = merge_settings.merge(settings)

    assert changed is True
    assert changed_again is False
    assert len(settings["hooks"]["SessionStart"]) == 2
    assert "PreToolUse" in settings["hooks"]


def test_remove_keeps_non_helix_hooks_and_cleans_empty_events() -> None:
    settings = {
        "hooks": {
            "SessionStart": [
                {"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-start"}]},
                {"hooks": [{"command": "custom-start"}]},
            ],
            "Stop": [
                {"hooks": [{"command": "~/ai-dev-kit-vscode/cli/helix-session-summary"}]},
            ],
        }
    }

    changed = merge_settings.remove(settings)

    assert changed is True
    assert settings["hooks"]["SessionStart"] == [{"hooks": [{"command": "custom-start"}]}]
    assert "Stop" not in settings["hooks"]


def test_main_writes_settings_file_and_exits_zero_when_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(sys, "argv", ["merge_settings.py", str(settings_path)])

    with pytest.raises(SystemExit) as exc:
        merge_settings.main()

    assert exc.value.code == 0
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" in payload
    assert "SessionStart" in payload["hooks"]


def test_main_exits_one_when_no_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps({"hooks": copy.deepcopy(merge_settings.HELIX_HOOKS)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["merge_settings.py", str(settings_path)])

    with pytest.raises(SystemExit) as exc:
        merge_settings.main()

    assert exc.value.code == 1
