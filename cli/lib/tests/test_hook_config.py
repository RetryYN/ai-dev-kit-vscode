import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from extractors.hook_config import extract_hook_configs


def test_extract_hook_configs_reads_settings_and_local_settings(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    claude_dir = repo_root / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Write",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "~/ai-dev-kit-vscode/cli/helix-check-claudemd",
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    (claude_dir / "settings.local.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "matcher": "Edit|Write|MultiEdit",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "$HELIX_ROOT/.claude/hooks/pretooluse-opus-repo-block.sh",
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    rows = extract_hook_configs(repo_root)
    keys = {
        (row["hook_event"], row["matcher"], row["script_path"])
        for row in rows
    }

    assert ("PreToolUse", "Write", "~/ai-dev-kit-vscode/cli/helix-check-claudemd") in keys
    assert (
        "PostToolUse",
        "Edit|Write|MultiEdit",
        "$HELIX_ROOT/.claude/hooks/pretooluse-opus-repo-block.sh",
    ) in keys
