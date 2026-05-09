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


def write_snapshot(path: Path, *lines: str) -> None:
    path.write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def make_main_argv(
    before: Path,
    after: Path,
    untracked_after: Path,
    allowed_files: str,
    baseline_dir: Path,
    own_baseline: Path,
    *concurrent_from: Path,
) -> list[str]:
    argv = [
        "codex_post_validation.py",
        "--before",
        str(before),
        "--after",
        str(after),
        "--untracked-after",
        str(untracked_after),
        "--allowed-files",
        allowed_files,
        "--baseline-dir",
        str(baseline_dir),
        "--own-baseline",
        str(own_baseline),
    ]
    for path in concurrent_from:
        argv.extend(["--concurrent-from", str(path)])
    return argv


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


def test_extract_pid_reads_pid_and_rejects_legacy_fake_name() -> None:
    assert (
        codex_post_validation._extract_pid(Path("codex-baseline-12345-67890.txt"))
        == 12345
    )
    assert codex_post_validation._extract_pid(Path("codex-baseline-1-older.txt")) is None


def test_load_newer_baselines_includes_alive_pid_outside_window(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    own = baseline_dir / "codex-baseline-2-own.txt"
    alive = baseline_dir / f"codex-baseline-{os.getpid()}-999999999.txt"

    base_time = 1_700_000_000_000_000_000
    write_baseline(own, "tracked-own.txt\n", base_time)
    write_baseline(alive, "tracked-alive.txt\n", base_time - 5_000_000_000)

    baselines = codex_post_validation.load_newer_baselines(
        baseline_dir,
        own,
        window_seconds=1.0,
    )

    assert baselines == [{"tracked-alive.txt"}]


def test_load_newer_baselines_cleans_up_dead_pid_outside_window(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    own = baseline_dir / "codex-baseline-2-own.txt"
    stale = baseline_dir / "codex-baseline-999999999-123456789.txt"

    base_time = 1_700_000_000_000_000_000
    write_baseline(own, "tracked-own.txt\n", base_time)
    write_baseline(stale, "tracked-stale.txt\n", base_time - 5_000_000_000)

    baselines = codex_post_validation.load_newer_baselines(
        baseline_dir,
        own,
        window_seconds=1.0,
    )

    assert baselines == []
    assert not stale.exists()


def test_load_newer_baselines_keeps_legacy_fake_name_window_only(tmp_path: Path) -> None:
    baseline_dir = tmp_path / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    own = baseline_dir / "codex-baseline-2-own.txt"
    legacy_recent = baseline_dir / "codex-baseline-1-older.txt"
    legacy_stale = baseline_dir / "codex-baseline-1-stale.txt"

    base_time = 1_700_000_000_000_000_000
    write_baseline(own, "tracked-own.txt\n", base_time)
    write_baseline(legacy_recent, "tracked-recent.txt\n", base_time - 500_000_000)
    write_baseline(legacy_stale, "tracked-stale.txt\n", base_time - 5_000_000_000)

    baselines = codex_post_validation.load_newer_baselines(
        baseline_dir,
        own,
        window_seconds=1.0,
    )

    assert baselines == [{"tracked-recent.txt"}]
    assert legacy_stale.exists()


def test_find_violations_rejects_new_untracked_with_concurrent_baseline() -> None:
    violations = codex_post_validation.find_allowed_files_violations(
        before_paths=set(),
        after_paths={"rogue.txt"},
        untracked_after_paths={"rogue.txt"},
        allowed_patterns=["allowed.txt"],
        concurrent_baselines=[{"rogue.txt"}],
    )

    assert violations == ["rogue.txt"]


def test_main_accepts_valid_concurrent_baseline_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project"
    baseline_dir = project_root / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    before = baseline_dir / "codex-baseline-22222-33333.txt"
    after = baseline_dir / "after.txt"
    untracked_after = baseline_dir / "untracked-after.txt"
    concurrent = baseline_dir / "codex-baseline-12345-67890.txt"

    write_snapshot(before, "tracked-a.txt")
    write_snapshot(after, "tracked-a.txt", "tracked-b.txt")
    write_snapshot(untracked_after)
    write_snapshot(concurrent, "tracked-a.txt")

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(
        sys,
        "argv",
        make_main_argv(
            before,
            after,
            untracked_after,
            "tracked-a.txt",
            baseline_dir,
            before,
            concurrent,
        ),
    )

    assert codex_post_validation.main() == 0


def test_main_rejects_concurrent_baseline_outside_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    baseline_dir = project_root / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    before = baseline_dir / "codex-baseline-22222-33333.txt"
    after = baseline_dir / "after.txt"
    untracked_after = baseline_dir / "untracked-after.txt"
    outside = tmp_path / "outside" / "codex-baseline-1-1.txt"
    outside.parent.mkdir()

    write_snapshot(before, "tracked-a.txt")
    write_snapshot(after, "tracked-a.txt")
    write_snapshot(untracked_after)
    write_snapshot(outside, "tracked-a.txt")

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(
        sys,
        "argv",
        make_main_argv(
            before,
            after,
            untracked_after,
            "tracked-a.txt",
            baseline_dir,
            before,
            outside,
        ),
    )

    assert codex_post_validation.main() == 1
    assert _read_stdout(capsys) == (
        "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/ and match "
        f"codex-baseline-<pid>-<stamp>.txt format, got: {outside}"
    )


def test_main_rejects_concurrent_baseline_with_invalid_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    baseline_dir = project_root / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    before = baseline_dir / "codex-baseline-22222-33333.txt"
    after = baseline_dir / "after.txt"
    untracked_after = baseline_dir / "untracked-after.txt"
    invalid_name = baseline_dir / "foo.txt"

    write_snapshot(before, "tracked-a.txt")
    write_snapshot(after, "tracked-a.txt")
    write_snapshot(untracked_after)
    write_snapshot(invalid_name, "tracked-a.txt")

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(
        sys,
        "argv",
        make_main_argv(
            before,
            after,
            untracked_after,
            "tracked-a.txt",
            baseline_dir,
            before,
            invalid_name,
        ),
    )

    assert codex_post_validation.main() == 1
    assert _read_stdout(capsys) == (
        "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/ and match "
        f"codex-baseline-<pid>-<stamp>.txt format, got: {invalid_name}"
    )


def test_main_rejects_concurrent_baseline_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    baseline_dir = project_root / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    before = baseline_dir / "codex-baseline-22222-33333.txt"
    after = baseline_dir / "after.txt"
    untracked_after = baseline_dir / "untracked-after.txt"
    target = baseline_dir / "codex-baseline-9-9.txt"
    symlink_path = baseline_dir / "codex-baseline-1-1.txt"

    write_snapshot(before, "tracked-a.txt")
    write_snapshot(after, "tracked-a.txt")
    write_snapshot(untracked_after)
    write_snapshot(target, "tracked-a.txt")
    symlink_path.symlink_to(target)

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(
        sys,
        "argv",
        make_main_argv(
            before,
            after,
            untracked_after,
            "tracked-a.txt",
            baseline_dir,
            before,
            symlink_path,
        ),
    )

    assert codex_post_validation.main() == 1
    assert _read_stdout(capsys) == (
        "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/ and match "
        f"codex-baseline-<pid>-<stamp>.txt format, got: {symlink_path}"
    )


def test_main_rejects_missing_concurrent_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_root = tmp_path / "project"
    baseline_dir = project_root / ".helix" / "tmp"
    baseline_dir.mkdir(parents=True)
    before = baseline_dir / "codex-baseline-22222-33333.txt"
    after = baseline_dir / "after.txt"
    untracked_after = baseline_dir / "untracked-after.txt"
    missing = baseline_dir / "codex-baseline-1-1.txt"

    write_snapshot(before, "tracked-a.txt")
    write_snapshot(after, "tracked-a.txt")
    write_snapshot(untracked_after)

    monkeypatch.setenv("PROJECT_ROOT", str(project_root))
    monkeypatch.setattr(
        sys,
        "argv",
        make_main_argv(
            before,
            after,
            untracked_after,
            "tracked-a.txt",
            baseline_dir,
            before,
            missing,
        ),
    )

    assert codex_post_validation.main() == 1
    assert _read_stdout(capsys) == (
        "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/ and match "
        f"codex-baseline-<pid>-<stamp>.txt format, got: {missing}"
    )


def _read_stdout(capsys: pytest.CaptureFixture[str]) -> str:
    return capsys.readouterr().out.strip()
