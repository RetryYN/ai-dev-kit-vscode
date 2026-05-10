from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
import re
import sys


_BASELINE_PID_RE = re.compile(r"^codex-baseline-(\d+)-(\d+)\.txt$")
_SUMMARY_BLOCK_RE = re.compile(
    r"---SUMMARY_START---\s*(?P<body>.*?)\s*---SUMMARY_END---",
    re.DOTALL,
)
_DIFF_LINES_RE = re.compile(r"^diff_lines:\s*(?P<value>.+?)\s*$", re.MULTILINE)
_CONCURRENT_BASELINE_ERROR = (
    "concurrent baseline must be in PROJECT_ROOT/.helix/tmp/ and match "
    "codex-baseline-<pid>-<stamp>.txt format, got: {path}"
)


def read_snapshot(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    }


def _extract_summary_block(stdout: str) -> str | None:
    match = _SUMMARY_BLOCK_RE.search(stdout)
    if match is None:
        return None
    return match.group("body")


def _extract_summary_diff_lines_raw(stdout: str) -> str | None:
    summary_block = _extract_summary_block(stdout)
    if summary_block is None:
        return None
    match = _DIFF_LINES_RE.search(summary_block)
    if match is None:
        return None
    return match.group("value").strip()


def parse_summary_diff_lines(stdout: str) -> tuple[int | None, str]:
    summary_block = _extract_summary_block(stdout)
    if summary_block is None:
        return None, "no_summary"

    raw_value = _extract_summary_diff_lines_raw(stdout)
    if raw_value is None:
        return None, "missing"

    try:
        return int(raw_value), "present"
    except ValueError:
        return None, "invalid"


def count_actual_diff_lines(
    before_paths: set[str],
    after_paths: set[str],
    untracked_after_paths: set[str],
) -> int:
    actual_files = (after_paths - before_paths) | untracked_after_paths
    return len(actual_files)


def check_write_expected(
    *,
    task_type: str,
    summary_stdout: str,
    before_paths: set[str],
    after_paths: set[str],
    untracked_after_paths: set[str],
) -> list[str]:
    if task_type != "実装":
        return []

    actual_files = (after_paths - before_paths) | untracked_after_paths
    actual_count = count_actual_diff_lines(
        before_paths,
        after_paths,
        untracked_after_paths,
    )
    parsed_diff_lines, status = parse_summary_diff_lines(summary_stdout)
    warnings: list[str] = []

    if actual_count == 0:
        warnings.append("audit-only failure suspected: task_type=実装 だが git diff 0 件")

    if status in {"no_summary", "missing"}:
        warnings.append("self-report missing diff_lines")
    elif status == "invalid":
        raw_value = _extract_summary_diff_lines_raw(summary_stdout) or ""
        warnings.append(f"self-report diff_lines invalid: {raw_value}")
    elif parsed_diff_lines is not None:
        if parsed_diff_lines == 0 and actual_count > 0:
            warnings.append(
                f"self-report claims zero diff but actual={len(actual_files)} files"
            )
        if parsed_diff_lines > 0 and actual_count == 0:
            warnings.append(
                f"self-report mismatches actual: claimed={parsed_diff_lines}, actual=0"
            )

    return warnings


def _extract_pid(path: Path) -> int | None:
    match = _BASELINE_PID_RE.match(path.name)
    if match is None:
        return None
    return int(match.group(1))


def _is_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _project_root() -> Path:
    return Path(
        os.environ.get("PROJECT_ROOT")
        or os.environ.get("HELIX_PROJECT_ROOT")
        or os.getcwd()
    ).resolve()


def validate_concurrent_baseline_path(raw_path: str) -> Path:
    path = Path(raw_path)
    realpath = path.resolve()
    baseline_root = _project_root() / ".helix" / "tmp"

    if (
        path.is_symlink()
        or path != realpath
        or not realpath.is_relative_to(baseline_root)
        or _BASELINE_PID_RE.match(realpath.name) is None
        or not realpath.is_file()
    ):
        raise ValueError(_CONCURRENT_BASELINE_ERROR.format(path=raw_path))

    return realpath


def load_newer_baselines(
    baseline_dir: Path,
    own_baseline: Path,
    *,
    window_seconds: float = 60.0,
) -> list[set[str]]:
    if not baseline_dir.is_dir() or not own_baseline.exists():
        return []

    own_mtime_ns = own_baseline.stat().st_mtime_ns
    window_ns = int(window_seconds * 1_000_000_000)
    baselines: list[set[str]] = []
    for candidate in sorted(baseline_dir.glob("codex-baseline-*.txt")):
        if candidate == own_baseline or not candidate.is_file():
            continue
        try:
            mtime_ns = candidate.stat().st_mtime_ns
            in_window = abs(mtime_ns - own_mtime_ns) <= window_ns
            pid = _extract_pid(candidate)
            if pid is None:
                if in_window:
                    baselines.append(read_snapshot(candidate))
                continue

            if in_window or _is_pid_alive(pid):
                baselines.append(read_snapshot(candidate))
                continue

            try:
                candidate.unlink()
            except OSError:
                pass
        except FileNotFoundError:
            continue
    return baselines


def find_allowed_files_violations(
    *,
    before_paths: set[str],
    after_paths: set[str],
    untracked_after_paths: set[str],
    allowed_patterns: list[str],
    concurrent_baselines: list[set[str]] | None = None,
) -> list[str]:
    if not allowed_patterns:
        return []

    candidates = after_paths - before_paths
    new_untracked = (candidates & untracked_after_paths) - before_paths

    ambiguous_tracked: set[str] = set()
    for other_before in concurrent_baselines or []:
        ambiguous_tracked.update((after_paths - other_before) - new_untracked)

    violations: list[str] = []
    for path in sorted(candidates):
        if any(fnmatch.fnmatch(path, pattern) for pattern in allowed_patterns):
            continue
        if path in new_untracked:
            violations.append(path)
            continue
        if path in ambiguous_tracked:
            continue
        violations.append(path)

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate helix-codex allowed-files deltas.")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--untracked-after", required=True)
    parser.add_argument("--allowed-files")
    parser.add_argument("--baseline-dir")
    parser.add_argument("--own-baseline")
    parser.add_argument("--concurrent-from", action="append", default=[])
    parser.add_argument("--check-write-expected", action="store_true", default=False)
    parser.add_argument("--task-type", default="不明")
    parser.add_argument("--summary-stdout")
    args = parser.parse_args()

    before_path = Path(args.before)
    after_path = Path(args.after)
    untracked_after_path = Path(args.untracked_after)
    before_paths = read_snapshot(before_path)
    after_paths = read_snapshot(after_path)
    untracked_after_paths = read_snapshot(untracked_after_path)

    if args.check_write_expected:
        summary_stdout = ""
        if args.summary_stdout:
            summary_path = Path(args.summary_stdout)
            if summary_path.exists():
                summary_stdout = summary_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
        for warning in check_write_expected(
            task_type=args.task_type,
            summary_stdout=summary_stdout,
            before_paths=before_paths,
            after_paths=after_paths,
            untracked_after_paths=untracked_after_paths,
        ):
            print(f"WARNING: {warning}", file=sys.stderr)

    if not args.allowed_files:
        return 0

    if not args.baseline_dir or not args.own_baseline:
        parser.error("--baseline-dir and --own-baseline are required with --allowed-files")

    baseline_dir = Path(args.baseline_dir)
    own_baseline_path = Path(args.own_baseline)
    patterns = [item.strip() for item in args.allowed_files.split(",") if item.strip()]
    concurrent_baselines = load_newer_baselines(baseline_dir, own_baseline_path)

    try:
        for raw_path in args.concurrent_from:
            concurrent_baselines.append(
                read_snapshot(validate_concurrent_baseline_path(raw_path))
            )
    except ValueError as exc:
        print(str(exc))
        return 1

    violations = find_allowed_files_violations(
        before_paths=before_paths,
        after_paths=after_paths,
        untracked_after_paths=untracked_after_paths,
        allowed_patterns=patterns,
        concurrent_baselines=concurrent_baselines,
    )

    if violations:
        print("エラー: --allowed-files 外の変更を検出しました")
        print("allowed: " + ", ".join(patterns))
        for path in violations:
            print(f"  - {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
