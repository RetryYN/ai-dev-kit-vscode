from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from pathlib import PurePosixPath

KNOWN_SOURCE_STATUSES = frozenset({
    "available_nonempty",
    "available_empty",
    "unavailable",
})


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


def _is_direct_pytest_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    return (
        pure_path.as_posix().startswith("cli/lib/tests/")
        and pure_path.name.startswith("test_")
        and pure_path.suffix == ".py"
    )


def _is_direct_bats_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    return pure_path.as_posix().startswith("cli/tests/") and pure_path.suffix == ".bats"


def _is_cli_script_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    if pure_path.parts[:1] != ("cli",):
        return False
    if len(pure_path.parts) != 2:
        return False
    return pure_path.suffix != ".md"


def _is_code_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    path_text = pure_path.as_posix()
    if path_text.startswith(("docs/", "HELIX-workflows/")):
        return False
    if _is_direct_pytest_path(path) or _is_direct_bats_path(path) or _is_cli_script_path(path):
        return True
    if path_text.startswith("cli/lib/") and pure_path.suffix == ".py":
        return True
    if path_text.startswith("cli/tests/") and pure_path.suffix in {".bats", ".bash", ".sh"}:
        return True
    if path_text.startswith(("scripts/", ".github/")):
        return True
    return pure_path.suffix in {".py", ".sh", ".bash", ".bats", ".toml", ".yaml", ".yml", ".json"}


def select_test_targets(
    files: list[str],
    *,
    repo_root: Path | None = None,
) -> dict[str, list[str] | bool]:
    root = (repo_root or _resolve_project_root()).resolve()
    pytest_targets: set[str] = set()
    bats_targets: set[str] = set()
    unmapped_code_files: list[str] = []
    has_code_changes = False

    for raw_path in sorted({item.strip() for item in files if item and item.strip()}):
        path = PurePosixPath(raw_path).as_posix()

        if _is_direct_pytest_path(path):
            has_code_changes = True
            pytest_targets.add(path)
            continue
        if _is_direct_bats_path(path):
            has_code_changes = True
            bats_targets.add(path)
            continue
        if path.startswith("cli/lib/") and PurePosixPath(path).suffix == ".py":
            has_code_changes = True
            module_name = PurePosixPath(path).stem
            matches = sorted((root / "cli" / "lib" / "tests").glob(f"test_{module_name}*.py"))
            if matches:
                pytest_targets.update(match.relative_to(root).as_posix() for match in matches)
            else:
                unmapped_code_files.append(path)
            continue
        if _is_cli_script_path(path):
            has_code_changes = True
            script_name = PurePosixPath(path).name
            matches = sorted((root / "cli" / "tests").glob(f"*{script_name}*.bats"))
            if matches:
                bats_targets.update(match.relative_to(root).as_posix() for match in matches)
            else:
                unmapped_code_files.append(path)
            continue
        if _is_code_path(path):
            has_code_changes = True
            unmapped_code_files.append(path)

    return {
        "pytest_targets": sorted(pytest_targets),
        "bats_targets": sorted(bats_targets),
        "has_code_changes": has_code_changes,
        "unmapped_code_files": unmapped_code_files,
    }
