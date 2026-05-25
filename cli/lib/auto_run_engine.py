"""helix auto-run framework skeleton.

契約: docs/plans/L7/L7-auto-run-loop-frameworkplan.md
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


STATE_DIR = Path(".helix") / "auto-run"
STATE_PATH = STATE_DIR / "current.json"
STATE_VERSION = 1
DEFAULT_DURATION_MINUTES = 60


class AutoRunError(RuntimeError):
    """Raised when auto-run state or arguments are invalid."""


def _now() -> datetime:
    return datetime.now().astimezone()


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _parse_iso(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def _ensure_dict(payload: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise AutoRunError(f"invalid {label} payload")
    return payload


def _tool_root() -> Path:
    env = os.environ.get("HELIX_HOME", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _remaining_minutes(deadline_at: str) -> int:
    seconds = (_parse_iso(deadline_at) - _now()).total_seconds()
    return max(0, math.ceil(seconds / 60))


class AutoRunEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.state_path = self.project_root / STATE_PATH
        self.state_dir = self.state_path.parent
        self.heartbeat_scheduler = _tool_root() / "cli" / "helix-heartbeat-scheduler"

    def _load_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise AutoRunError("auto-run state is not initialized; run `helix auto-run start` first")
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        return _ensure_dict(payload, label="state")

    def _save_state(self, payload: dict[str, Any]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(_json_dump(payload), encoding="utf-8")

    def _budget_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        window = _ensure_dict(state.get("budget_window") or {}, label="budget_window")
        deadline_at = str(window.get("deadline_at") or "").strip()
        duration_minutes = int(window.get("duration_minutes") or 0)
        source = str(window.get("source") or "duration").strip() or "duration"
        if not deadline_at:
            raise AutoRunError("budget_window.deadline_at is missing")
        remaining = _remaining_minutes(deadline_at)
        within_window = state.get("status") == "running" and remaining > 0
        return {
            "duration_minutes": duration_minutes,
            "deadline_at": deadline_at,
            "source": source,
            "remaining_minutes": remaining,
            "within_time_window": within_window,
        }

    def _resolve_deadline(self, *, duration_minutes: int | None, until: str | None) -> tuple[int, datetime, str]:
        if duration_minutes is not None and until is not None:
            raise AutoRunError("--until and --duration-minutes are mutually exclusive")
        if until is not None:
            raw = until.strip()
            deadline_at = self._parse_until(raw)
            duration = max(1, math.ceil((deadline_at - _now()).total_seconds() / 60))
            return duration, deadline_at, "until"
        effective_duration = DEFAULT_DURATION_MINUTES if duration_minutes is None else duration_minutes
        if effective_duration <= 0:
            raise AutoRunError("--duration-minutes must be > 0")
        deadline_at = _now() + timedelta(minutes=effective_duration)
        return effective_duration, deadline_at, "duration"

    def _parse_until(self, raw: str) -> datetime:
        now = _now()
        if re.fullmatch(r"\d{2}:\d{2}", raw):
            hour, minute = (int(part) for part in raw.split(":", 1))
            if hour > 23 or minute > 59:
                raise AutoRunError(f"invalid --until: {raw}")
            deadline = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if deadline <= now:
                deadline += timedelta(days=1)
            return deadline
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise AutoRunError(f"invalid --until: {raw}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=now.tzinfo)
        return parsed

    def _run_heartbeat_scheduler(self, *, within_time_window: bool) -> dict[str, Any]:
        if not self.heartbeat_scheduler.exists():
            raise AutoRunError(f"heartbeat scheduler not found: {self.heartbeat_scheduler}")

        env = os.environ.copy()
        env["HELIX_PROJECT_ROOT"] = str(self.project_root)
        env["HELIX_WITHIN_TIME_WINDOW"] = "1" if within_time_window else "0"
        proc = subprocess.run(
            [str(self.heartbeat_scheduler), "--json"],
            cwd=str(self.project_root),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip() or proc.stdout.strip() or "heartbeat scheduler failed"
            raise AutoRunError(stderr)
        return _ensure_dict(json.loads(proc.stdout), label="heartbeat")

    def _build_resume_snapshot(
        self,
        state: dict[str, Any],
        budget: dict[str, Any],
        heartbeat: dict[str, Any],
    ) -> dict[str, Any]:
        should_resume = (
            state.get("status") == "running"
            and bool(budget.get("within_time_window"))
            and bool(heartbeat.get("should_schedule"))
        )
        if state.get("status") != "running":
            reason = "auto-run is stopped"
        elif not budget.get("within_time_window"):
            reason = "budget window expired"
        elif not heartbeat.get("should_schedule"):
            reason = "no carry to resume"
        else:
            reason = "carry detected within time window"
        candidate = heartbeat.get("schedulewakeup_candidate") or {}
        return {
            "resume_ready": should_resume,
            "action": "resume_plan" if should_resume else "idle",
            "reason": reason,
            "plan_id": state.get("plan", {}).get("plan_id"),
            "prompt": candidate.get("prompt") or "Review handover and resume the active PLAN.",
            "after_minutes": candidate.get("after_minutes"),
        }

    def _enrich_state(self, state: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(state)
        budget = self._budget_snapshot(state)
        heartbeat = _ensure_dict(payload.get("heartbeat") or {}, label="heartbeat")
        payload["budget"] = budget
        payload["resume"] = self._build_resume_snapshot(payload, budget, heartbeat)
        return payload

    def start(
        self,
        *,
        plan_id: str,
        duration_minutes: int | None = None,
        until: str | None = None,
    ) -> dict[str, Any]:
        plan_id = plan_id.strip()
        if not plan_id:
            raise AutoRunError("--plan-id is required")

        started_at = _now()
        effective_duration, deadline_at, source = self._resolve_deadline(
            duration_minutes=duration_minutes,
            until=until,
        )
        state = {
            "version": STATE_VERSION,
            "status": "running",
            "started_at": started_at.isoformat(timespec="seconds"),
            "updated_at": started_at.isoformat(timespec="seconds"),
            "plan": {
                "plan_id": plan_id,
                "resume_target": "handover_next_action",
            },
            "budget_window": {
                "duration_minutes": effective_duration,
                "deadline_at": deadline_at.isoformat(timespec="seconds"),
                "source": source,
            },
            "heartbeat": {
                "checked_at": None,
                "should_schedule": False,
                "carry_count": 0,
                "within_time_window": True,
                "schedulewakeup_candidate": None,
            },
            "integrations": {
                "compaction_api": "pending_next_phase",
                "schedulewakeup_hook": "out_of_scope_this_task",
            },
            "session_control": {
                "mode": "dry_run",
                "status": "idle",
                "last_restart_at": None,
                "restart_count": 0,
            },
        }
        self._save_state(state)
        return self._enrich_state(state)

    def status(self) -> dict[str, Any]:
        return self._enrich_state(self._load_state())

    def budget(self, *, set_minutes: int | None = None) -> dict[str, Any]:
        state = self._load_state()
        if set_minutes is not None:
            if set_minutes <= 0:
                raise AutoRunError("--set-minutes must be > 0")
            deadline_at = _now() + timedelta(minutes=set_minutes)
            state["budget_window"] = {
                "duration_minutes": set_minutes,
                "deadline_at": deadline_at.isoformat(timespec="seconds"),
                "source": "duration",
            }
            state["updated_at"] = _now_iso()
            self._save_state(state)
        return self._enrich_state(state)

    def heartbeat(self) -> dict[str, Any]:
        state = self._load_state()
        budget = self._budget_snapshot(state)
        heartbeat = self._run_heartbeat_scheduler(
            within_time_window=bool(budget["within_time_window"])
        )
        heartbeat["checked_at"] = _now_iso()
        heartbeat["within_time_window"] = budget["within_time_window"]
        state["heartbeat"] = heartbeat
        state["updated_at"] = _now_iso()
        self._save_state(state)
        return self._enrich_state(state)

    def resume(self) -> dict[str, Any]:
        state = self._load_state()
        heartbeat = self.heartbeat()
        state = self._load_state()
        budget = self._budget_snapshot(state)
        resume = self._build_resume_snapshot(state, budget, heartbeat["heartbeat"])
        state["last_resume_check_at"] = _now_iso()
        state["updated_at"] = _now_iso()
        self._save_state(state)
        payload = self._enrich_state(state)
        payload["resume"] = resume
        return payload

    def stop(self) -> dict[str, Any]:
        state = self._load_state()
        state["status"] = "stopped"
        state["stopped_at"] = _now_iso()
        state["updated_at"] = state["stopped_at"]
        self._save_state(state)
        return self._enrich_state(state)


def _print_payload(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"status: {payload.get('status')}")
    plan_id = payload.get("plan", {}).get("plan_id")
    if plan_id:
        print(f"plan_id: {plan_id}")
    budget = payload.get("budget", {})
    if budget:
        print(
            f"budget: {budget.get('remaining_minutes')}m remaining "
            f"(deadline={budget.get('deadline_at')})"
        )
    resume = payload.get("resume", {})
    if resume:
        print(f"resume: {resume.get('action')} ({resume.get('reason')})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix auto-run")
    sub = parser.add_subparsers(dest="subcmd", required=True)

    p_start = sub.add_parser("start")
    p_start.add_argument("--plan-id", required=True)
    p_start.add_argument("--duration-minutes", type=int, default=None)
    p_start.add_argument("--until")
    p_start.add_argument("--json", action="store_true")

    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("--json", action="store_true")

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--json", action="store_true")

    p_heartbeat = sub.add_parser("heartbeat")
    p_heartbeat.add_argument("--json", action="store_true")

    p_budget = sub.add_parser("budget")
    p_budget.add_argument("--set-minutes", type=int)
    p_budget.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    engine = AutoRunEngine()

    try:
        if args.subcmd == "start":
            payload = engine.start(
                plan_id=args.plan_id,
                duration_minutes=args.duration_minutes,
                until=args.until,
            )
        elif args.subcmd == "status":
            payload = engine.status()
        elif args.subcmd == "resume":
            payload = engine.resume()
        elif args.subcmd == "stop":
            payload = engine.stop()
        elif args.subcmd == "heartbeat":
            payload = engine.heartbeat()
        elif args.subcmd == "budget":
            payload = engine.budget(set_minutes=args.set_minutes)
        else:  # pragma: no cover
            parser.error(f"unknown subcommand: {args.subcmd}")
            return 2
    except AutoRunError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_payload(payload, as_json=bool(getattr(args, "json", False)))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
