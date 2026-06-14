from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


def _resolve_project_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _split_changed_files(raw: str) -> list[str]:
    return [item for item in re.split(r"\s+", raw.strip()) if item]


def _default_upstream() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=_resolve_project_root(),
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    branch = proc.stdout.strip()
    if proc.returncode != 0 or not branch or branch == "HEAD":
        raise RuntimeError("unable to resolve current branch")
    return f"origin/{branch}"


def changed_files(upstream: str | None = None) -> dict[str, list[str] | str]:
    if "HELIX_CHANGED_FILES" in os.environ:
        files = _split_changed_files(os.environ.get("HELIX_CHANGED_FILES", ""))
        return {
            "files": files,
            "source_status": "available_nonempty" if files else "available_empty",
        }

    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", f"{upstream or _default_upstream()}..HEAD"],
            cwd=_resolve_project_root(),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, RuntimeError, subprocess.SubprocessError):
        return {"files": [], "source_status": "unavailable"}

    if proc.returncode != 0:
        return {"files": [], "source_status": "unavailable"}

    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return {
        "files": files,
        "source_status": "available_nonempty" if files else "available_empty",
    }
