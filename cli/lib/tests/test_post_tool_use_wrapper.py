import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WRAPPER = REPO_ROOT / "cli" / "libexec" / "helix-post-tool-use"


def test_wrapper_dispatches_each_safe_path(tmp_path: Path) -> None:
    log_path = tmp_path / "hook.log"
    fake_hook = tmp_path / "fake-hook"
    fake_hook.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' \"$1\" >> \"$HELIX_TEST_HOOK_LOG\"\n",
        encoding="utf-8",
    )
    fake_hook.chmod(0o755)

    payload = {
        "tool_input": {
            "file_path": "src/app.ts",
            "files": [{"path": "docs/設計.md"}, {"file_path": "bad;path"}],
        }
    }
    env = os.environ.copy()
    env["HELIX_POST_TOOL_USE_HOOK"] = str(fake_hook)
    env["HELIX_TEST_HOOK_LOG"] = str(log_path)

    proc = subprocess.run(
        [str(WRAPPER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert log_path.read_text(encoding="utf-8").splitlines() == ["src/app.ts", "docs/設計.md"]
    assert "unsupported file_path skipped" in proc.stderr


def test_wrapper_returns_hook_failure(tmp_path: Path) -> None:
    fake_hook = tmp_path / "fake-hook"
    fake_hook.write_text("#!/usr/bin/env bash\nexit 7\n", encoding="utf-8")
    fake_hook.chmod(0o755)

    env = os.environ.copy()
    env["HELIX_POST_TOOL_USE_HOOK"] = str(fake_hook)

    proc = subprocess.run(
        [str(WRAPPER)],
        input=json.dumps({"tool_input": {"file_path": "src/app.ts"}}),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert proc.returncode == 7
