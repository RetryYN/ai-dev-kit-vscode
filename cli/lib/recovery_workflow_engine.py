"""Recovery workflow CLI backend.

契約:
- docs/v2/L7-design/L7-cli-helix-recovery-impl-design.md
- docs/plans/L7/L7-cli-helix-recovery-implplan.md §3-§8
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

try:
    from . import cutover_orchestrator, recovery_plan_check
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    import cutover_orchestrator
    import recovery_plan_check
    from paths import project_root as detect_project_root


PHASE_LABELS: dict[str, str] = {
    "RP-1": "ガード検出",
    "RP-2": "警告/停止",
    "RP-3": "状態把握",
    "RP-4": "再開ポイント確定",
    "RP-5": "認識訂正",
    "RP-6": "ロールバック/再開",
}
PHASE_ORDER: tuple[str, ...] = tuple(PHASE_LABELS.keys())
PHASE_BY_CONDITION: dict[str, str] = {
    "C1": "RP-2",
    "C2": "RP-1",
    "C3": "RP-3",
    "C4": "RP-2",
}
CONDITION_PRIORITY: dict[str, int] = {"C2": 0, "C1": 1, "C3": 2, "C4": 3}
SEVERITY_PRIORITY: dict[str, int] = {"FAIL": 0, "WARN": 1, "UNKNOWN": 2, "CLEAR": 3}
STOP_HOOK_NAME = "stop-recovery-update.sh"
DEFAULT_POSTMORTEM_TEMPLATE = "cli/templates/plan/recovery/postmortem-template.md"
FALLBACK_RECOVERY_TEMPLATE = "cli/templates/plan/recovery/template.md"


class RecoveryWorkflowError(RuntimeError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(slots=True)
class RecoverySession:
    plan_id: str
    status: str
    started_at: str
    current_phase: str
    triggered_conditions: list[dict[str, Any]]
    reopen_point: str | None
    log_path: str
    forward_target: str | None
    warnings: list[str]
    completed_at: str | None = None
    skip_reason: str | None = None
    last_snapshot_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RecoverySession":
        return cls(
            plan_id=str(payload.get("plan_id") or ""),
            status=str(payload.get("status") or ""),
            started_at=str(payload.get("started_at") or ""),
            current_phase=str(payload.get("current_phase") or ""),
            triggered_conditions=list(payload.get("triggered_conditions") or []),
            reopen_point=_optional_text(payload.get("reopen_point")),
            log_path=str(payload.get("log_path") or ""),
            forward_target=_optional_text(payload.get("forward_target")),
            warnings=[str(item) for item in payload.get("warnings") or []],
            completed_at=_optional_text(payload.get("completed_at")),
            skip_reason=_optional_text(payload.get("skip_reason")),
            last_snapshot_at=_optional_text(payload.get("last_snapshot_at")),
        )


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


class RecoveryWorkflowEngine:
    def __init__(
        self,
        *,
        project_root: str | Path | None = None,
        helix_home: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.helix_home = Path(
            helix_home or os.environ.get("HELIX_HOME", Path(__file__).resolve().parents[2])
        ).expanduser().resolve()
        self.recovery_dir = self.project_root / ".helix" / "recovery"
        self.current_path = self.recovery_dir / "CURRENT.json"

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _run_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            check=False,
        )

    def _load_frontmatter(self, path: Path) -> dict[str, Any]:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                payload = yaml.safe_load("\n".join(lines[1:index])) or {}
                return payload if isinstance(payload, dict) else {}
        return {}

    def _find_plan_path(self, plan_id: str) -> Path:
        docs_dir = self.project_root / "docs" / "plans"
        if not docs_dir.is_dir():
            raise RecoveryWorkflowError(f"PLAN not found: {plan_id}", 1)
        for candidate in sorted(docs_dir.rglob("*.md")):
            frontmatter = self._load_frontmatter(candidate)
            if str(frontmatter.get("plan_id") or "").strip() == plan_id:
                if str(frontmatter.get("kind") or "").strip() != "recovery":
                    raise RecoveryWorkflowError(
                        f"PLAN kind must be recovery: {plan_id}",
                        1,
                    )
                return candidate
        raise RecoveryWorkflowError(f"PLAN not found: {plan_id}", 1)

    def _load_triggered_conditions_from_recover_check(self) -> list[dict[str, Any]]:
        recover_cli = self.helix_home / "cli" / "helix-recover"
        result = self._run_command([str(recover_cli), "check", "--json"])
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "helix recover check failed").strip()
            raise RecoveryWorkflowError(message, 1)
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise RecoveryWorkflowError(f"failed to parse recover check JSON: {exc}", 1) from exc
        if not isinstance(payload, list):
            raise RecoveryWorkflowError("recover check JSON must be a list", 1)
        normalized: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise RecoveryWorkflowError("recover check item must be an object", 1)
            condition_id = str(item.get("condition_id") or "").strip()
            severity = str(item.get("severity") or "").strip()
            source = str(item.get("source") or "").strip()
            if not condition_id or not severity or not source:
                raise RecoveryWorkflowError("recover check item missing required keys", 1)
            normalized.append(
                {
                    "condition_id": condition_id,
                    "severity": severity,
                    "source": source,
                    "metric_value": item.get("metric_value"),
                    "threshold": item.get("threshold"),
                    "evidence": str(item.get("evidence") or ""),
                    "detail": str(item.get("detail") or ""),
                    "triggered": bool(item.get("triggered")),
                    "requires_attention": bool(item.get("requires_attention")),
                }
            )
        return normalized

    def _select_start_phase(self, triggered_conditions: list[dict[str, Any]]) -> str:
        if not triggered_conditions:
            return "RP-1"
        ranked = sorted(
            triggered_conditions,
            key=lambda item: (
                SEVERITY_PRIORITY.get(str(item.get("severity")), 99),
                CONDITION_PRIORITY.get(str(item.get("condition_id")), 99),
            ),
        )
        condition_id = str(ranked[0].get("condition_id"))
        return PHASE_BY_CONDITION.get(condition_id, "RP-1")

    def _infer_forward_target(self, reopen_point: str | None) -> str | None:
        point = _optional_text(reopen_point)
        if point and point.startswith("L") and point[1:].isdigit():
            return point
        return None

    def _is_stop_hook_registered(self) -> bool:
        settings_path = self.project_root / ".claude" / "settings.json"
        if not settings_path.exists():
            return False
        try:
            payload = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        hooks = payload.get("hooks", {}) if isinstance(payload, dict) else {}
        entries = hooks.get("Stop", []) if isinstance(hooks, dict) else []
        for entry in entries:
            for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
                command = str(hook.get("command") or "")
                if STOP_HOOK_NAME in command:
                    return True
        return False

    def _write_session(self, session: RecoverySession) -> None:
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get_status(self) -> RecoverySession | None:
        if not self.current_path.exists():
            return None
        payload = json.loads(self.current_path.read_text(encoding="utf-8"))
        return RecoverySession.from_dict(payload)

    def _require_active_session(self) -> RecoverySession:
        session = self.get_status()
        if session is None:
            raise RecoveryWorkflowError("No active recovery session", 2)
        return session

    def _default_log_path(self, plan_id: str) -> Path:
        return self.recovery_dir / f"recovery-log-{plan_id}.md"

    def _render_log_text(self, session: RecoverySession) -> str:
        triggered = ", ".join(
            f"{item.get('condition_id')}:{item.get('severity')}"
            for item in session.triggered_conditions
        ) or "-"
        lines: list[str] = [
            "---",
            f"plan_id: {session.plan_id}",
            f"status: {session.status}",
            f"started_at: {session.started_at}",
            f"current_phase: {session.current_phase}",
            "---",
            "",
            f"# Recovery Log — {session.plan_id}",
            "",
            "## 事故記録",
            f"- session_started_at: {session.started_at}",
            f"- triggered_conditions: {triggered}",
            "",
            "## timeline",
            f"- {session.started_at} session initialized",
            "",
            "## 認識訂正履歴",
            "- 初回開始",
            "",
            "## 中間結論",
            "- Recovery workflow session is active.",
            "",
            "## context 再構築",
            "- 1. recovery workflow doc を確認する",
            "- 2. helix recovery status を確認する",
            "- 3. 再開ポイントを 1 つに固定する",
            "",
            "## 再開ポイント",
            f"- reopen_point: {session.reopen_point or '-'}",
            "",
            "## 再発防止",
            "- stop-hook と recovery-log を更新してから中断する",
            "",
        ]
        return "\n".join(lines)

    def _ensure_log(self, session: RecoverySession) -> Path:
        log_path = self.project_root / session.log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text(self._render_log_text(session), encoding="utf-8")
        missing = recovery_plan_check.check_recovery_template_sections(log_path)
        if missing:
            raise RecoveryWorkflowError(
                f"recovery log missing required sections: {', '.join(missing)}",
                1,
            )
        return log_path

    def start_session(self, plan_id: str, reopen_point: str | None, *, dry_run: bool = False) -> RecoverySession:
        self._find_plan_path(plan_id)
        current = self.get_status()
        if current is not None and current.status == "active":
            raise RecoveryWorkflowError(
                f"recovery session already active: {current.plan_id}",
                2,
            )
        triggered_conditions = self._load_triggered_conditions_from_recover_check()
        phase = self._select_start_phase(triggered_conditions)
        warnings: list[str] = []
        if not self._is_stop_hook_registered():
            warnings.append(
                "Stop hook (stop-recovery-update.sh) が未登録です。"
            )
        session = RecoverySession(
            plan_id=plan_id,
            status="active",
            started_at=self._now_iso(),
            current_phase=phase,
            triggered_conditions=triggered_conditions,
            reopen_point=_optional_text(reopen_point),
            log_path=str(self._default_log_path(plan_id).relative_to(self.project_root)),
            forward_target=self._infer_forward_target(reopen_point),
            warnings=warnings,
        )
        if not dry_run:
            self._write_session(session)
            self._ensure_log(session)
        return session

    def advance_phase(self, from_phase: str, to_phase: str) -> RecoverySession:
        if from_phase not in PHASE_LABELS or to_phase not in PHASE_LABELS:
            raise RecoveryWorkflowError("invalid phase id", 1)
        session = self._require_active_session()
        if session.current_phase != from_phase:
            raise RecoveryWorkflowError(
                f"current phase mismatch: expected {session.current_phase}, got {from_phase}",
                1,
            )
        if PHASE_ORDER.index(to_phase) < PHASE_ORDER.index(from_phase):
            raise RecoveryWorkflowError("phase cannot move backwards", 1)
        session.current_phase = to_phase
        self._write_session(session)
        self._append_line_to_section(
            self._ensure_log(session),
            "timeline",
            f"- {self._now_iso()} phase advanced: {from_phase} -> {to_phase}",
        )
        return session

    def _append_line_to_section(self, path: Path, section_name: str, line: str) -> None:
        markers = {
            "timeline": ("## timeline", "## タイムライン"),
            "correction": ("## 認識訂正履歴", "## 訂正履歴"),
        }
        section_markers = markers.get(section_name)
        if section_markers is None:
            raise RecoveryWorkflowError(f"unsupported section: {section_name}", 1)
        lines = path.read_text(encoding="utf-8").splitlines()
        start_index = next(
            (index for index, raw in enumerate(lines) if any(raw.strip() == marker for marker in section_markers)),
            None,
        )
        if start_index is None:
            raise RecoveryWorkflowError(f"section not found: {section_name}", 1)
        insert_index = len(lines)
        for index in range(start_index + 1, len(lines)):
            if lines[index].startswith("## "):
                insert_index = index
                break
        lines.insert(insert_index, line)
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def append_log(self, text: str) -> None:
        session = self._require_active_session()
        self._append_line_to_section(
            self._ensure_log(session),
            "correction",
            f"- {self._now_iso()} {text.strip()}",
        )

    def export_log(self, destination: str | Path) -> Path:
        session = self._require_active_session()
        src = self._ensure_log(session)
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        return dest

    def generate_postmortem(self, output_path: str | Path | None = None, template_path: str | Path | None = None) -> Path:
        session = self._require_active_session()
        log_path = self._ensure_log(session)
        output = Path(
            output_path
            or (
                self.project_root
                / "docs"
                / "postmortem"
                / f"recovery-{session.plan_id}-{datetime.now(UTC).date().isoformat()}.md"
            )
        )
        if output.exists():
            raise RecoveryWorkflowError(f"output already exists: {output}", 2)
        template_candidates = [
            self.project_root / str(template_path) if template_path else self.project_root / DEFAULT_POSTMORTEM_TEMPLATE,
            self.project_root / FALLBACK_RECOVERY_TEMPLATE,
        ]
        template_text = ""
        for candidate in template_candidates:
            if candidate.exists():
                template_text = candidate.read_text(encoding="utf-8")
                break
        log_text = log_path.read_text(encoding="utf-8")
        rendered = (
            template_text.replace("{{PLAN_ID}}", session.plan_id)
            .replace("{{STARTED_AT}}", session.started_at)
            .replace("{{CURRENT_PHASE}}", session.current_phase)
            .replace("{{LOG_PATH}}", str(log_path.relative_to(self.project_root)))
            .replace("{{RECOVERY_LOG}}", log_text.strip())
        )
        if not rendered.strip():
            rendered = (
                f"# Recovery Postmortem — {session.plan_id}\n\n"
                f"- started_at: {session.started_at}\n"
                f"- current_phase: {session.current_phase}\n"
                f"- log_path: {log_path.relative_to(self.project_root)}\n\n"
                f"## Recovery Log\n\n{log_text}"
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered.rstrip() + "\n", encoding="utf-8")
        return output

    def complete_session(
        self,
        *,
        confirm_token: str | None,
        forward_target: str | None,
        dry_run: bool,
        skip_cutover: bool,
        skip_reason: str | None,
    ) -> dict[str, Any]:
        session = self._require_active_session()
        next_target = _optional_text(forward_target) or session.forward_target
        if skip_cutover:
            if not _optional_text(skip_reason):
                raise RecoveryWorkflowError("--skip-cutover requires --skip-reason", 1)
            result = {"status": "skipped", "reason": str(skip_reason).strip()}
            if not dry_run:
                session.status = "completed"
                session.completed_at = self._now_iso()
                session.forward_target = next_target
                session.skip_reason = str(skip_reason).strip()
                self._write_session(session)
            return result

        try:
            token = cutover_orchestrator._validate_confirm_token(str(confirm_token or ""))
        except ValueError as exc:
            raise RecoveryWorkflowError(str(exc), 2) from exc

        preflight = cutover_orchestrator.cutover_preflight()
        preflight_payload = asdict(preflight)
        if not preflight.ready:
            raise RecoveryWorkflowError(
                "cutover preflight failed: " + ", ".join(preflight.blockers),
                1,
            )
        if dry_run:
            return {"status": "dry_run", "preflight": preflight_payload}

        result = cutover_orchestrator.cutover_execute(confirm_token=token)
        session.status = "completed"
        session.completed_at = self._now_iso()
        session.forward_target = next_target
        self._write_session(session)
        self._append_line_to_section(
            self._ensure_log(session),
            "timeline",
            f"- {session.completed_at} session completed",
        )
        return result

    def snapshot_on_stop(self) -> None:
        session = self.get_status()
        if session is None or session.status != "active":
            return
        session.last_snapshot_at = self._now_iso()
        self._write_session(session)
        self._append_line_to_section(
            self._ensure_log(session),
            "timeline",
            f"- {session.last_snapshot_at} stop-hook snapshot captured",
        )


def _format_status_text(session: RecoverySession) -> str:
    lines = [
        f"[HELIX Recovery] {session.plan_id} ({session.status})",
        f"開始: {session.started_at}",
        f"現在 Phase: {session.current_phase} {PHASE_LABELS.get(session.current_phase, '')}".rstrip(),
        f"再開ポイント: {session.reopen_point or '-'}",
    ]
    if session.triggered_conditions:
        lines.append(
            "発火条件: "
            + ", ".join(
                f"{item.get('condition_id')} {item.get('severity')}"
                for item in session.triggered_conditions
            )
        )
    lines.append(f"recovery-log: {session.log_path}")
    lines.append(f"Forward 復帰先: {session.forward_target or '-'}")
    if session.status == "active":
        started = datetime.fromisoformat(session.started_at)
        if datetime.now(started.tzinfo or UTC) - started > timedelta(days=7):
            lines.append("警告: 7 日以上 active な stale session です")
    lines.extend(f"警告: {warning}" for warning in session.warnings)
    return "\n".join(lines)


def _format_start_text(session: RecoverySession, *, dry_run: bool) -> str:
    lines = [
        f"[HELIX Recovery] session 開始: {session.plan_id}",
        f"再開ポイント: {session.reopen_point or '-'}",
        f"初期 Phase: {session.current_phase} {PHASE_LABELS.get(session.current_phase, '')}".rstrip(),
        f"recovery-log: {session.log_path}",
    ]
    if dry_run:
        lines.append("[dry-run] CURRENT.json は未更新です")
    else:
        lines.append(".helix/recovery/CURRENT.json を初期化しました")
    lines.extend(
        f"警告: {warning}\n手動登録: helix hook add stop stop-recovery-update.sh"
        if STOP_HOOK_NAME in warning
        else f"警告: {warning}"
        for warning in session.warnings
    )
    lines.append("次のステップ: helix recovery phase --show")
    return "\n".join(lines)


def _format_phase_text(session: RecoverySession) -> str:
    return f"{session.current_phase} {PHASE_LABELS.get(session.current_phase, '')}".rstrip()


def render_help() -> str:
    return (
        "Usage: helix recovery <subcommand> [options]\n\n"
        "Subcommands:\n"
        "  start       Recovery session を開始\n"
        "  status      現在の session 状態を表示\n"
        "  phase       phase を表示・進行\n"
        "  log         recovery-log の表示・追記・export\n"
        "  postmortem  postmortem draft を生成\n"
        "  done        Recovery を完了し cutover を確認\n"
        "  help        この help を表示\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False, prog="helix recovery")
    subparsers = parser.add_subparsers(dest="subcommand")

    start = subparsers.add_parser("start")
    start.add_argument("--plan-id", required=True)
    start.add_argument("--reopen-point")
    start.add_argument("--dry-run", action="store_true")

    status = subparsers.add_parser("status")
    status.add_argument("--json", action="store_true")

    phase = subparsers.add_parser("phase")
    phase.add_argument("--show", action="store_true")
    phase.add_argument("--advance", action="store_true")
    phase.add_argument("--from", dest="from_phase")
    phase.add_argument("--to", dest="to_phase")

    log = subparsers.add_parser("log")
    log.add_argument("--show", action="store_true")
    log.add_argument("--append")
    log.add_argument("--export")

    postmortem = subparsers.add_parser("postmortem")
    postmortem.add_argument("--output")
    postmortem.add_argument("--template")

    done = subparsers.add_parser("done")
    done.add_argument("--confirm-token")
    done.add_argument("--forward-target")
    done.add_argument("--dry-run", action="store_true")
    done.add_argument("--skip-cutover", action="store_true")
    done.add_argument("--skip-reason")

    subparsers.add_parser("help")
    return parser


def main(argv: list[str] | None = None) -> int:
    args_list = list(argv or sys.argv[1:])
    if not args_list or args_list[0] in {"-h", "--help", "help"}:
        print(render_help())
        return 0

    parser = build_parser()
    args = parser.parse_args(args_list)
    engine = RecoveryWorkflowEngine()

    try:
        if args.subcommand == "start":
            session = engine.start_session(args.plan_id, args.reopen_point, dry_run=args.dry_run)
            print(_format_start_text(session, dry_run=args.dry_run))
            return 0

        if args.subcommand == "status":
            session = engine.get_status()
            if session is None:
                print("No active recovery session")
                return 1
            if args.json:
                print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(_format_status_text(session))
            return 0

        if args.subcommand == "phase":
            if args.show:
                session = engine._require_active_session()
                print(_format_phase_text(session))
                return 0
            if args.advance:
                if not args.from_phase or not args.to_phase:
                    raise RecoveryWorkflowError("--advance requires --from and --to", 1)
                session = engine.advance_phase(args.from_phase, args.to_phase)
                print(_format_phase_text(session))
                return 0
            raise RecoveryWorkflowError("phase requires --show or --advance", 1)

        if args.subcommand == "log":
            session = engine._require_active_session()
            log_path = engine._ensure_log(session)
            if args.show:
                print(log_path.read_text(encoding="utf-8").rstrip())
                return 0
            if args.append:
                engine.append_log(args.append)
                print(f"appended to {session.log_path}")
                return 0
            if args.export:
                dest = engine.export_log(args.export)
                print(str(dest))
                return 0
            raise RecoveryWorkflowError("log requires --show, --append, or --export", 1)

        if args.subcommand == "postmortem":
            output = engine.generate_postmortem(args.output, args.template)
            print(str(output))
            return 0

        if args.subcommand == "done":
            payload = engine.complete_session(
                confirm_token=args.confirm_token,
                forward_target=args.forward_target,
                dry_run=args.dry_run,
                skip_cutover=args.skip_cutover,
                skip_reason=args.skip_reason,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
    except RecoveryWorkflowError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code

    print(render_help())
    return 0


def snapshot_on_stop() -> None:
    RecoveryWorkflowEngine().snapshot_on_stop()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
