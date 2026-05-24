"""Refactor mode CLI backend.

契約: docs/plans/L7/L7-cli-helix-refactor-implplan.md §2 / §4
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal

try:
    from . import lock_helper
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    import lock_helper
    from paths import project_root as detect_project_root


SUPPORTED_DRIFT_TYPES = ("code_smell", "structural")
SESSION_FILE_NAME = "refactor-session.json"
AUDIT_FILE_NAME = "refactor-session.audit.log"
LOCK_NAME = "refactor-session"
PYTEST_COUNT_RE = re.compile(r"(\d+)\s+(passed|failed|skipped)")
BATS_COUNT_RE = re.compile(r"#\s+(tests|pass|fail|failures|skip)\s+(\d+)", re.IGNORECASE)


class RefactorError(RuntimeError):
    """Base error for refactor CLI."""


class RefactorInputError(RefactorError):
    """Invalid user input or missing session state."""


class RefactorCheckError(RefactorError):
    """Baseline or regression validation failed."""


@dataclass(frozen=True, slots=True)
class TestResult:
    command: str
    returncode: int
    passed: int
    failed: int
    skipped: int
    total: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and self.failed == 0


@dataclass(frozen=True, slots=True)
class CheckResult:
    session_id: str
    baseline_passed: int
    baseline_failed: int
    baseline_total: int
    current_passed: int
    current_failed: int
    current_total: int
    ok: bool
    regression_reason: str | None
    test_result: TestResult


@dataclass(frozen=True, slots=True)
class RefactorSession:
    session_id: str
    targets: list[str]
    test_cmd: str
    plan_id: str | None
    baseline_passed: int
    baseline_failed: int
    baseline_skipped: int
    baseline_total: int
    started_at: str
    last_check_at: str | None
    check_count: int
    status: Literal["active", "completed"]
    routed_from: str | None
    route_signal: str | None
    drift_type: str | None
    schema_version: str
    project_root: str
    created_by: str
    last_result: Literal["pass", "fail", "unknown"] | None
    targets_hash: str
    trace_status: Literal["linked", "unlinked"]
    force_close_reason: str | None
    from_debt_id: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RefactorSession":
        return cls(**payload)


class RefactorEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.helix_dir = self.project_root / ".helix"
        self.session_path = self.helix_dir / SESSION_FILE_NAME
        self.audit_path = self.helix_dir / AUDIT_FILE_NAME

    @contextmanager
    def _session_lock(self) -> Any:
        paths = lock_helper.resolve_paths(LOCK_NAME, "project", str(self.project_root), None)
        lock_helper.ensure_lock_parent(paths)
        lock_helper._reject_symlink(paths.lock_file)
        fd = os.open(paths.lock_file, os.O_RDWR | os.O_CREAT, lock_helper.lock_file_mode(paths.scope))
        try:
            os.chmod(paths.lock_file, lock_helper.lock_file_mode(paths.scope))
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _normalize_targets(self, targets: list[str]) -> list[str]:
        if not targets:
            raise RefactorInputError("--target is required")
        normalized: list[str] = []
        seen: set[str] = set()
        for raw in targets:
            candidate = Path(raw)
            resolved = (candidate if candidate.is_absolute() else self.project_root / candidate).resolve()
            try:
                relative = resolved.relative_to(self.project_root)
            except ValueError as exc:
                raise RefactorInputError(f"target must stay within project root: {raw}") from exc
            if not resolved.exists():
                raise RefactorInputError(f"target not found: {relative.as_posix()}")
            relative_str = relative.as_posix()
            if relative_str not in seen:
                seen.add(relative_str)
                normalized.append(relative_str)
        return normalized

    def _validate_drift_type(self, drift_type: str | None) -> str | None:
        if drift_type is None:
            return None
        normalized = drift_type.strip()
        if normalized not in SUPPORTED_DRIFT_TYPES:
            raise RefactorInputError(f"unsupported drift_type: {normalized}")
        return normalized

    def _targets_hash(self, targets: list[str]) -> str:
        return hashlib.sha256(json.dumps(targets, sort_keys=True).encode("utf-8")).hexdigest()

    def _load_session_unlocked(self) -> RefactorSession | None:
        if not self.session_path.exists():
            return None
        payload = json.loads(self.session_path.read_text(encoding="utf-8"))
        return RefactorSession.from_dict(payload)

    def load_session(self) -> RefactorSession | None:
        with self._session_lock():
            return self._load_session_unlocked()

    def _save_session_unlocked(self, session: RefactorSession) -> None:
        self.helix_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(session), ensure_ascii=False, indent=2, sort_keys=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.helix_dir, delete=False) as handle:
            handle.write(payload)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(self.session_path)

    def _clear_session_unlocked(self) -> None:
        try:
            self.session_path.unlink()
        except FileNotFoundError:
            pass

    def _append_audit_log(self, event: str, session: RefactorSession) -> None:
        self.helix_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "event": event,
            "session_id": session.session_id,
            "timestamp": self._now_iso(),
            "force_close_reason": session.force_close_reason,
            "plan_id": session.plan_id,
            "targets": session.targets,
        }
        with self.audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    def run_test_cmd(self, cmd: str) -> TestResult:
        args = shlex.split(cmd)
        if not args:
            raise RefactorInputError("--test-cmd is required")
        completed = subprocess.run(
            args,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        combined = "\n".join(part for part in (stdout, stderr) if part)
        passed = 0
        failed = 0
        skipped = 0

        matches = PYTEST_COUNT_RE.findall(combined)
        if matches:
            for count, label in matches:
                value = int(count)
                if label == "passed":
                    passed = value
                elif label == "failed":
                    failed = value
                elif label == "skipped":
                    skipped = value
            total = passed + failed + skipped
            return TestResult(cmd, completed.returncode, passed, failed, skipped, total, stdout, stderr)

        bats_counts = {key.lower(): int(value) for key, value in BATS_COUNT_RE.findall(combined)}
        if bats_counts:
            total = bats_counts.get("tests", 0)
            failed = bats_counts.get("fail", bats_counts.get("failures", 0))
            skipped = bats_counts.get("skip", 0)
            passed = bats_counts.get("pass", max(total - failed - skipped, 0))
            return TestResult(cmd, completed.returncode, passed, failed, skipped, total, stdout, stderr)

        return TestResult(cmd, completed.returncode, 0, 0 if completed.returncode == 0 else 1, 0, 0, stdout, stderr)

    def _build_session(
        self,
        *,
        targets: list[str],
        test_cmd: str,
        plan_id: str | None,
        baseline: TestResult,
        signal_id: str | None,
        auto_routed_from: str | None,
        drift_type: str | None,
        from_debt_id: str | None,
    ) -> RefactorSession:
        session_id = f"refactor-{datetime.now().strftime('%Y%m%d-%H%M%S%f')}"
        return RefactorSession(
            session_id=session_id,
            targets=targets,
            test_cmd=test_cmd,
            plan_id=plan_id,
            baseline_passed=baseline.passed,
            baseline_failed=baseline.failed,
            baseline_skipped=baseline.skipped,
            baseline_total=baseline.total,
            started_at=self._now_iso(),
            last_check_at=None,
            check_count=0,
            status="active",
            routed_from=auto_routed_from,
            route_signal=signal_id,
            drift_type=drift_type,
            schema_version="1",
            project_root=str(self.project_root),
            created_by=os.environ.get("USER", "unknown"),
            last_result=None,
            targets_hash=self._targets_hash(targets),
            trace_status="linked" if plan_id else "unlinked",
            force_close_reason=None,
            from_debt_id=from_debt_id,
        )

    def init_session(
        self,
        *,
        targets: list[str],
        test_cmd: str,
        plan_id: str | None,
        signal_id: str | None = None,
        auto_routed_from: str | None = None,
        drift_type: str | None = None,
        from_debt_id: str | None = None,
    ) -> RefactorSession:
        if not test_cmd.strip():
            raise RefactorInputError("--test-cmd is required")
        normalized_targets = self._normalize_targets(targets)
        normalized_drift_type = self._validate_drift_type(drift_type)
        with self._session_lock():
            if self._load_session_unlocked() is not None:
                raise RefactorInputError("active session exists, run 'helix refactor status' or 'helix refactor done'")
            baseline = self.run_test_cmd(test_cmd)
            if not baseline.ok:
                raise RefactorCheckError("baseline tests failed")
            session = self._build_session(
                targets=normalized_targets,
                test_cmd=test_cmd,
                plan_id=plan_id,
                baseline=baseline,
                signal_id=signal_id,
                auto_routed_from=auto_routed_from,
                drift_type=normalized_drift_type,
                from_debt_id=from_debt_id,
            )
            self._save_session_unlocked(session)
            return session

    def _evaluate_regression(self, session: RefactorSession, result: TestResult) -> str | None:
        if result.failed > 0 or result.returncode != 0:
            return "failed_count"
        if result.total < session.baseline_total:
            return "total_count"
        if result.passed < session.baseline_passed:
            return "passed_count"
        return None

    def check_session(self) -> CheckResult:
        with self._session_lock():
            session = self._load_session_unlocked()
            if session is None:
                raise RefactorInputError("no active refactor session")
            result = self.run_test_cmd(session.test_cmd)
            regression_reason = self._evaluate_regression(session, result)
            updated = replace(
                session,
                last_check_at=self._now_iso(),
                check_count=session.check_count + 1,
                last_result="pass" if regression_reason is None else "fail",
            )
            self._save_session_unlocked(updated)
            return CheckResult(
                session_id=session.session_id,
                baseline_passed=session.baseline_passed,
                baseline_failed=session.baseline_failed,
                baseline_total=session.baseline_total,
                current_passed=result.passed,
                current_failed=result.failed,
                current_total=result.total,
                ok=regression_reason is None,
                regression_reason=regression_reason,
                test_result=result,
            )

    def status_payload(self) -> dict[str, Any]:
        with self._session_lock():
            session = self._load_session_unlocked()
            if session is None:
                raise RefactorInputError("no active refactor session")
            return {
                "session_id": session.session_id,
                "targets": session.targets,
                "plan_id": session.plan_id,
                "test_cmd": session.test_cmd,
                "baseline": {
                    "passed": session.baseline_passed,
                    "failed": session.baseline_failed,
                    "skipped": session.baseline_skipped,
                    "total": session.baseline_total,
                },
                "started_at": session.started_at,
                "last_check_at": session.last_check_at,
                "check_count": session.check_count,
                "route_signal": session.route_signal,
                "routed_from": session.routed_from,
                "drift_type": session.drift_type,
                "trace_status": session.trace_status,
            }

    def done_session(self, *, force: bool, reason: str | None) -> RefactorSession:
        if force and not (reason or "").strip():
            raise RefactorInputError("--reason is required when --force is used")
        with self._session_lock():
            session = self._load_session_unlocked()
            if session is None:
                raise RefactorInputError("no active refactor session")
            if force:
                closed = replace(session, status="completed", force_close_reason=reason, last_result="unknown")
                self._append_audit_log("force_close", closed)
                self._clear_session_unlocked()
                return closed

            result = self.run_test_cmd(session.test_cmd)
            regression_reason = self._evaluate_regression(session, result)
            updated = replace(
                session,
                last_check_at=self._now_iso(),
                check_count=session.check_count + 1,
                last_result="pass" if regression_reason is None else "fail",
            )
            if regression_reason is not None:
                self._save_session_unlocked(updated)
                raise RefactorCheckError("regression exists, cannot close session")
            closed = replace(updated, status="completed")
            self._append_audit_log("complete", closed)
            self._clear_session_unlocked()
            return closed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix refactor")
    sub = parser.add_subparsers(dest="command")

    init_parser = sub.add_parser("init")
    init_parser.add_argument("--target", action="append", default=[])
    init_parser.add_argument("--test-cmd")
    init_parser.add_argument("--plan-id")
    init_parser.add_argument("--signal-id")
    init_parser.add_argument("--auto-routed-from")
    init_parser.add_argument("--drift-type")
    init_parser.add_argument("--from-debt-id")

    check_parser = sub.add_parser("check")
    check_parser.add_argument("--verbose", action="store_true")

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--json", action="store_true")

    done_parser = sub.add_parser("done")
    done_parser.add_argument("--force", action="store_true")
    done_parser.add_argument("--reason")
    return parser


def _print_status(payload: dict[str, Any]) -> None:
    baseline = payload["baseline"]
    print("[helix refactor status]")
    print(f"session_id:   {payload['session_id']}")
    print(f"target:       {', '.join(payload['targets'])}")
    print(f"plan_id:      {payload['plan_id'] or '(none)'}")
    print(f"test_cmd:     {payload['test_cmd']}")
    print(
        "baseline:     "
        f"passed={baseline['passed']} / failed={baseline['failed']} / skipped={baseline['skipped']}"
    )
    print(f"started:      {payload['started_at']}")
    print(f"last_check:   {payload['last_check_at'] or '(none)'}")
    print(f"check_count:  {payload['check_count']}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    engine = RefactorEngine()
    try:
        if args.command == "init":
            if not (args.test_cmd or "").strip():
                raise RefactorInputError("--test-cmd is required")
            session = engine.init_session(
                targets=args.target,
                test_cmd=args.test_cmd,
                plan_id=args.plan_id,
                signal_id=args.signal_id,
                auto_routed_from=args.auto_routed_from,
                drift_type=args.drift_type,
                from_debt_id=args.from_debt_id,
            )
            print("[helix refactor init]")
            print(f"target: {', '.join(session.targets)}")
            if session.trace_status == "unlinked":
                print("warning: plan_id omitted; trace_status=unlinked")
            print(f"保護網テスト: {session.test_cmd}")
            print(
                "  "
                f"passed: {session.baseline_passed} / failed: {session.baseline_failed} / skipped: {session.baseline_skipped}"
            )
            print(f"保護網 GREEN ✓ — session 開始 (session_id: {session.session_id})")
            return 0

        if args.command == "check":
            result = engine.check_session()
            print(f"[helix refactor check] session: {result.session_id}")
            print(f"baseline: passed={result.baseline_passed} / failed={result.baseline_failed}")
            print(f"current:  passed={result.current_passed} / failed={result.current_failed}")
            if result.ok:
                print("振る舞い不変 ✓ — 次の小変更を実施してください")
                return 0
            print("REGRESSION DETECTED ✗ — 変更を revert して保護網を緑に戻してください")
            return 1

        if args.command == "status":
            payload = engine.status_payload()
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            else:
                _print_status(payload)
            return 0

        if args.command == "done":
            session = engine.done_session(force=args.force, reason=args.reason)
            if args.force:
                print(f"session 完了 (force) — reason: {session.force_close_reason}")
            else:
                print(f"session 完了 ✓ — session_id: {session.session_id}")
            return 0
    except RefactorInputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except RefactorCheckError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
