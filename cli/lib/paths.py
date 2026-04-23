from __future__ import annotations

import os
import subprocess
from pathlib import Path


def project_root() -> Path:
    """Git リポジトリルートを返す。Git 外の場合は cwd fallback。"""
    env = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()

    try:
        raw = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if raw:
            return Path(raw).resolve()
    except Exception:
        pass

    return Path.cwd().resolve()
