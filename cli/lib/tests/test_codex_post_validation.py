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


def test_find_allowed_files_violations_excludes_concurrent_tracked_change() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths={"tracked-a.txt"},
        after_paths={"tracked-a.txt", "tracked-b.txt"},
        untracked_after_paths=set(),
        allowed_patterns=["tracked-a.txt"],
        concurrent_baselines=[{"tracked-a.txt"}],
    )

    assert violations == []


def test_find_allowed_files_violations_rejects_new_untracked_even_with_concurrent_baseline() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths=set(),
        after_paths={"rogue.txt"},
        untracked_after_paths={"rogue.txt"},
        allowed_patterns=["allowed.txt"],
        concurrent_baselines=[set()],
    )

    assert violations == ["rogue.txt"]


def test_load_newer_baselines_ignores_older_snapshots(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    older = baseline_dir / "codex-baseline-1-older.txt"
    own = baseline_dir / "codex-baseline-2-own.txt"
    newer = baseline_dir / "codex-baseline-3-newer.txt"

    older.write_text("tracked-b.txt\n", encoding="utf-8")
    own.write_text("tracked-a.txt\n", encoding="utf-8")
    newer.write_text("tracked-a.txt\n", encoding="utf-8")

    older_time = own.stat().st_mtime_ns - 1_000_000
    newer_time = own.stat().st_mtime_ns + 1_000_000
    os.utime(older, ns=(older_time, older_time))
    os.utime(newer, ns=(newer_time, newer_time))

    baselines = codex_post_validation.load_newer_baselines(baseline_dir, own)

    assert baselines == [{"tracked-a.txt"}]


def test_find_allowed_files_violations_keeps_nonconcurrent_tracked_violation() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths={"tracked-a.txt"},
        after_paths={"tracked-a.txt", "tracked-b.txt"},
        untracked_after_paths=set(),
        allowed_patterns=["tracked-a.txt"],
        concurrent_baselines=[{"tracked-a.txt", "tracked-b.txt"}],
    )

    assert violations == ["tracked-b.txt"]
