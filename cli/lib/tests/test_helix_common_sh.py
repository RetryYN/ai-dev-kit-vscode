import subprocess
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]


def test_require_rg_warns_when_missing() -> None:
    script = LIB_DIR / "helix-common.sh"
    proc = subprocess.run(
        [
            "bash",
            "-lc",
            f'export PATH="/nonexistent"; source "{script}"; require_rg',
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "ripgrep (rg) が未インストール" in proc.stderr
    assert "apt install ripgrep" in proc.stderr
    assert "brew install ripgrep" in proc.stderr
