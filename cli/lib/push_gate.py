#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath


PYTEST_TESTS_CMD = ["python3", "-m", "pytest", "cli/lib/tests/", "-q"]
PYTEST_CATALOG_CMD = ["python3", "-m", "pytest", "cli/lib/tests/test_command_catalog.py", "-q"]
SECRET_CMD = ["pre-commit", "run", "--all-files"]
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bgit\s+branch\s+-D\b"),
    re.compile(r"\brm\s+-rf\b"),
    re.compile(r"(?:^|[^\w-])--force(?:[=\s]|$)"),
    re.compile(r"(?:^|[^\w-])--no-verify(?:[=\s]|$)"),
]
DESTRUCTIVE_EXCLUDED_PREFIXES = (
    "cli/lib/tests/",
    "cli/tests/",
    "tests/",
    "docs/",
)
DESTRUCTIVE_ROLLBACK_PREFIX = "cli/migrations/rollback/"
DESTRUCTIVE_DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")


def _repo_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git repository not found")
    return Path(proc.stdout.strip()).resolve()


def _run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


def _result(gate_id: str, passed: bool, detail: str, fix: str) -> dict:
    return {
        "id": gate_id,
        "passed": passed,
        "detail": detail,
        "fix": fix,
    }


def _parse_pytest_count(stdout: str, stderr: str) -> str | None:
    text = "\n".join(part for part in (stdout, stderr) if part).strip()
    match = re.search(r"(\d+)\s+passed", text)
    if match:
        return match.group(1)
    return None


def _parse_bats_count(stdout: str, stderr: str) -> str | None:
    text = "\n".join(part for part in (stdout, stderr) if part).strip()
    match = re.search(r"1\.\.(\d+)", text)
    if match:
        return match.group(1)
    match = re.search(r"(\d+)\s+tests?,\s+0\s+failures", text)
    if match:
        return match.group(1)
    return None


def _format_failure(proc: subprocess.CompletedProcess[str]) -> str:
    text = (proc.stderr or proc.stdout or "").strip()
    if not text:
        return f"exit {proc.returncode}"
    return text.splitlines()[-1]


def _parse_diff_path(raw_line: str) -> str | None:
    match = DESTRUCTIVE_DIFF_HEADER.match(raw_line)
    if not match:
        return None
    return match.group(2)


def _is_excluded_destructive_path(path: str) -> bool:
    pure_path = PurePosixPath(path)
    path_text = pure_path.as_posix()
    if path_text.startswith(DESTRUCTIVE_EXCLUDED_PREFIXES):
        return True
    return path_text.startswith(DESTRUCTIVE_ROLLBACK_PREFIX) and path_text.endswith(".sql")


def run_gate_tests() -> dict:
    repo_root = _repo_root()
    pytest_proc = _run_command(PYTEST_TESTS_CMD, cwd=repo_root)
    if pytest_proc.returncode != 0:
        return _result(
            "G-tests",
            False,
            f"pytest FAIL: {_format_failure(pytest_proc)}",
            "テスト fail を修正してから再実行",
        )

    bats_files = sorted(str(path.relative_to(repo_root)) for path in (repo_root / "cli" / "tests").glob("*.bats"))
    if not bats_files:
        return _result(
            "G-tests",
            False,
            "bats FAIL: no .bats files found under cli/tests",
            "テスト fail を修正してから再実行",
        )

    bats_proc = _run_command(["bats", *bats_files], cwd=repo_root)
    if bats_proc.returncode != 0:
        return _result(
            "G-tests",
            False,
            f"bats FAIL: {_format_failure(bats_proc)}",
            "テスト fail を修正してから再実行",
        )

    pytest_count = _parse_pytest_count(pytest_proc.stdout, pytest_proc.stderr) or "pytest PASS"
    bats_count = _parse_bats_count(bats_proc.stdout, bats_proc.stderr) or "bats PASS"
    return _result("G-tests", True, f"pytest {pytest_count} + bats {bats_count}", "なし")


def run_gate_catalog() -> dict:
    repo_root = _repo_root()
    proc = _run_command(PYTEST_CATALOG_CMD, cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-catalog",
            False,
            f"test_command_catalog FAIL: {_format_failure(proc)}",
            "help/docs 同期不足、`helix commands` 確認",
        )

    count = _parse_pytest_count(proc.stdout, proc.stderr) or "PASS"
    return _result("G-catalog", True, f"{count} PASS", "なし")


def run_gate_secret() -> dict:
    repo_root = _repo_root()
    try:
        proc = _run_command(SECRET_CMD, cwd=repo_root)
    except FileNotFoundError:
        # pre-commit 不在: scripts/git-hooks/pre-commit (in-repo gitleaks) を直接呼ぶ
        in_repo_hook = repo_root / "scripts" / "git-hooks" / "pre-commit"
        if in_repo_hook.exists():
            proc = _run_command(["bash", str(in_repo_hook)], cwd=repo_root)
            if proc.returncode != 0:
                return _result(
                    "G-secret",
                    False,
                    f"in-repo pre-commit hook FAIL: {_format_failure(proc)}",
                    "secret detected、staged change を確認",
                )
            return _result("G-secret", True, "in-repo pre-commit hook PASS", "なし")
        return _result(
            "G-secret",
            True,
            "pre-commit / in-repo hook 不在 → skip (warning)",
            "pre-commit インストール推奨: pip install pre-commit",
        )
    if proc.returncode != 0:
        return _result(
            "G-secret",
            False,
            f"pre-commit FAIL: {_format_failure(proc)}",
            "secret detected、staged change を確認",
        )
    return _result("G-secret", True, "pre-commit PASS", "なし")


def run_gate_ff(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    fetch_proc = _run_command(["git", "fetch", remote, branch], cwd=repo_root)
    if fetch_proc.returncode != 0:
        return _result(
            "G-ff",
            False,
            f"git fetch FAIL: {_format_failure(fetch_proc)}",
            "rebase 必要、`git pull --rebase origin main`",
        )

    target_ref = f"{remote}/{branch}"
    proc = _run_command(["git", "merge-base", "--is-ancestor", target_ref, "HEAD"], cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-ff",
            False,
            f"{target_ref} is not an ancestor of HEAD",
            "rebase 必要、`git pull --rebase origin main`",
        )
    return _result("G-ff", True, f"{target_ref} fast-forward OK", "なし")


def run_gate_attr(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    range_ref = f"{remote}/{branch}..HEAD"
    count_proc = _run_command(["git", "rev-list", "--count", range_ref], cwd=repo_root)
    if count_proc.returncode != 0:
        return _result(
            "G-attr",
            False,
            f"git rev-list FAIL: {_format_failure(count_proc)}",
            "commit 修正必要 (amend or rebase -i)",
        )

    total = int((count_proc.stdout or "0").strip() or "0")
    match_proc = _run_command(
        ["git", "log", range_ref, "--format=%H", "--grep", "Co-Authored-By"],
        cwd=repo_root,
    )
    if match_proc.returncode != 0:
        return _result(
            "G-attr",
            False,
            f"git log FAIL: {_format_failure(match_proc)}",
            "commit 修正必要 (amend or rebase -i)",
        )

    matched = len([line for line in match_proc.stdout.splitlines() if line.strip()])
    if matched != total:
        return _result(
            "G-attr",
            False,
            f"{total} commits / {matched} with Co-Authored-By",
            "commit 修正必要 (amend or rebase -i)",
        )
    return _result("G-attr", True, f"{total} commits / {matched} with Co-Authored-By", "なし")


def run_gate_nondestructive(remote: str = "origin", branch: str = "main") -> dict:
    repo_root = _repo_root()
    range_ref = f"{remote}/{branch}..HEAD"
    proc = _run_command(["git", "diff", "--unified=0", range_ref], cwd=repo_root)
    if proc.returncode != 0:
        return _result(
            "G-nondestructive",
            False,
            f"git diff FAIL: {_format_failure(proc)}",
            "destructive operation 検出、manual-confirm 必要",
        )

    offenders: list[str] = []
    current_path: str | None = None
    for raw_line in proc.stdout.splitlines():
        parsed_path = _parse_diff_path(raw_line)
        if parsed_path is not None:
            current_path = parsed_path
            continue
        if not raw_line.startswith("+") or raw_line.startswith("+++"):
            continue
        if current_path and _is_excluded_destructive_path(current_path):
            continue
        line = raw_line[1:]
        for pattern in DESTRUCTIVE_PATTERNS:
            match = pattern.search(line)
            if match:
                path = current_path or "<unknown>"
                offenders.append(f"{match.group(0).strip()} in {path}")
                break

    if offenders:
        return _result(
            "G-nondestructive",
            False,
            f"destructive pattern: {offenders[0]}",
            "destructive operation 検出、manual-confirm 必要",
        )
    return _result("G-nondestructive", True, "no destructive pattern", "なし")


def run_all_gates(execute: bool = False, remote: str = "origin", branch: str = "main") -> dict:
    gates = [
        run_gate_tests(),
        run_gate_catalog(),
        run_gate_secret(),
        run_gate_ff(remote, branch),
        run_gate_attr(remote, branch),
        run_gate_nondestructive(remote, branch),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    result = {
        "ok": not failed,
        "failed_count": len(failed),
        "gates": gates,
        "execute_requested": execute,
        "remote": remote,
        "branch": branch,
        "push": {
            "attempted": False,
            "ok": False,
            "detail": "",
        },
    }

    if failed or not execute:
        return result

    repo_root = _repo_root()
    push_proc = _run_command(["git", "push", remote, branch], cwd=repo_root)
    result["push"]["attempted"] = True
    result["push"]["ok"] = push_proc.returncode == 0
    result["push"]["detail"] = _format_failure(push_proc) if push_proc.returncode != 0 else f"git push {remote} {branch}"
    result["ok"] = push_proc.returncode == 0
    return result


def _print_report(payload: dict) -> None:
    print("[helix push] gate verification...")
    for gate in payload["gates"]:
        mark = "✓" if gate["passed"] else "✗"
        print(f"{mark} {gate['id']:<15} ({gate['detail']})")
        if not gate["passed"]:
            print(f"  Fix: {gate['fix']}")

    if not payload["ok"]:
        if payload["failed_count"]:
            suffix = "gate failed" if payload["failed_count"] == 1 else "gates failed"
            print(f"\n[helix push] BLOCKED ({payload['failed_count']} {suffix})")
        else:
            print(f"\n[helix push] git push failed: {payload['push']['detail']}")
        return

    if payload["execute_requested"]:
        print(
            f"\n[helix push] all gates PASS -> executing git push "
            f"{payload['remote']} {payload['branch']}"
        )
    else:
        print("\n[helix push] all gates PASS")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", "-h", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args, extra = parser.parse_known_args(argv)
    if args.help:
        parser.print_help()
        return 0
    if extra:
        print(f"エラー: 不明なオプションです: {extra[0]}", file=sys.stderr)
        return 2

    payload = run_all_gates(execute=args.execute, remote=args.remote, branch=args.branch)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_report(payload)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
