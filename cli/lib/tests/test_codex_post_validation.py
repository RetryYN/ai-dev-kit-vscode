import os
import py_compile
import sys
from pathlib import Path


import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import codex_post_validation


MODULE_PATH = LIB_DIR / "codex_post_validation.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def write_baseline(path: Path, content: str, mtime_ns: int) -> None:
    path.write_text(content, encoding="utf-8")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def test_find_allowed_files_violations_excludes_concurrent_tracked_change() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths={"tracked-a.txt"},
        after_paths={"tracked-a.txt", "tracked-b.txt"},
        untracked_after_paths=set(),
        allowed_patterns=["tracked-a.txt"],
        concurrent_baselines=[{"tracked-a.txt"}],
    )

    assert violations == []


def test_find_allowed_files_violations_rejects_new_untracked_file() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths=set(),
        after_paths={"rogue.txt"},
        untracked_after_paths={"rogue.txt"},
        allowed_patterns=["allowed.txt"],
        concurrent_baselines=[set()],
    )

    assert violations == ["rogue.txt"]


def test_load_newer_baselines_includes_recent_older_and_newer_baselines(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    older = baseline_dir / "codex-baseline-1-older.txt"
    own = baseline_dir / "codex-baseline-2-own.txt"
    newer = baseline_dir / "codex-baseline-3-newer.txt"

    base_time = 1_700_000_000_000_000_000
    write_baseline(older, "tracked-b.txt\n", base_time - 500_000_000)
    write_baseline(own, "tracked-a.txt\n", base_time)
    write_baseline(newer, "tracked-c.txt\n", base_time + 500_000_000)

    baselines = codex_post_validation.load_newer_baselines(
        baseline_dir,
        own,
        window_seconds=1.0,
    )

    assert baselines == [{"tracked-b.txt"}, {"tracked-c.txt"}]


def test_find_allowed_files_violations_keeps_nonconcurrent_tracked_violation() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths={"tracked-a.txt"},
        after_paths={"tracked-a.txt", "tracked-b.txt"},
        untracked_after_paths=set(),
        allowed_patterns=["tracked-a.txt"],
        concurrent_baselines=[{"tracked-a.txt", "tracked-b.txt"}],
    )

    assert violations == ["tracked-b.txt"]


def test_load_newer_baselines_ignores_old_baseline(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    old = baseline_dir / "codex-baseline-1-old.txt"
    own = baseline_dir / "codex-baseline-2-own.txt"
    recent = baseline_dir / "codex-baseline-3-recent.txt"

    base_time = 1_700_000_000_000_000_000
    write_baseline(old, "tracked-old.txt\n", base_time - 5_000_000_000)
    write_baseline(own, "tracked-own.txt\n", base_time)
    write_baseline(recent, "tracked-recent.txt\n", base_time + 500_000_000)

    baselines = codex_post_validation.load_newer_baselines(
        baseline_dir,
        own,
        window_seconds=1.0,
    )

    assert baselines == [{"tracked-recent.txt"}]


def test_find_violations_rejects_new_untracked_with_concurrent_baseline() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths=set(),
        after_paths={"rogue.txt"},
        untracked_after_paths={"rogue.txt"},
        allowed_patterns=["allowed.txt"],
        concurrent_baselines=[{"rogue.txt"}],
    )

    assert violations == ["rogue.txt"]
