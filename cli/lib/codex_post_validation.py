from __future__ import annotations

import argparse
import fnmatch
import os
from pathlib import Path
import re


_BASELINE_PID_RE = re.compile(r"^codex-baseline-(\d+)-(\d+)\.txt$")


def read_snapshot(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip()
    }


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
    parser.add_argument("--allowed-files", required=True)
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--own-baseline", required=True)
    args = parser.parse_args()

    before_path = Path(args.before)
    after_path = Path(args.after)
    untracked_after_path = Path(args.untracked_after)
    baseline_dir = Path(args.baseline_dir)
    own_baseline_path = Path(args.own_baseline)
    patterns = [item.strip() for item in args.allowed_files.split(",") if item.strip()]

    violations = find_allowed_files_violations(
        before_paths=read_snapshot(before_path),
        after_paths=read_snapshot(after_path),
        untracked_after_paths=read_snapshot(untracked_after_path),
        allowed_patterns=patterns,
        concurrent_baselines=load_newer_baselines(baseline_dir, own_baseline_path),
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
