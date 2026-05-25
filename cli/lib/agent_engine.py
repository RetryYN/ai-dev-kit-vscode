"""HELIX W agent drive CLI backend.

契約:
- HELIX-workflows/helix-process/two-stage-agent-design.md
- docs/plans/L7/L7-drive-agent-cli-connectplan.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


PHASE1_DRIVES = ("be", "fe", "db", "fullstack")
STAGE_STATUSES = ("in_progress", "ready")
PHASE1_LAYERS = ["L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]
PHASE3_LAYERS = ["L10", "L11", "L12", "L13", "L14"]
PARENT_DESIGN = "HELIX-workflows/helix-process/two-stage-agent-design.md"


class AgentEngineError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _normalize_stage(payload: Any) -> dict[str, Any]:
    stage = dict(payload or {})
    stage.setdefault("current_layer", None)
    stage.setdefault("layer_history", [])
    return stage


def _normalize_active_phases(payload: Any) -> list[str]:
    values = payload if isinstance(payload, list) else []
    phases: list[str] = []
    for item in values:
        value = str(item).strip()
        if value and value not in phases:
            phases.append(value)
    return phases


@dataclass(slots=True)
class AgentSession:
    agent_id: str
    summary: str
    status: str
    active_phases: list[str]
    parent_design: str
    phase1: dict[str, Any]
    phase2: dict[str, Any]
    phase3: dict[str, Any]
    warnings: list[str]
    timeline: list[dict[str, str]]
    log_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "summary": self.summary,
            "status": self.status,
            "current_phase": self.current_phase,
            "active_phases": list(self.active_phases),
            "parent_design": self.parent_design,
            "phase1": dict(self.phase1),
            "phase2": dict(self.phase2),
            "phase3": dict(self.phase3),
            "warnings": list(self.warnings),
            "timeline": [dict(item) for item in self.timeline],
            "log_path": self.log_path,
        }

    @property
    def current_phase(self) -> str:
        return self.active_phases[0] if self.active_phases else "phase1"

    @current_phase.setter
    def current_phase(self, phase: str) -> None:
        value = str(phase).strip() or "phase1"
        self.active_phases = [value, *[item for item in self.active_phases if item != value]]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentSession":
        active_phases = _normalize_active_phases(payload.get("active_phases"))
        if "active_phases" not in payload:
            active_phases = ["phase1"]
        return cls(
            agent_id=str(payload.get("agent_id") or ""),
            summary=str(payload.get("summary") or ""),
            status=str(payload.get("status") or "initialized"),
            active_phases=active_phases,
            parent_design=str(payload.get("parent_design") or PARENT_DESIGN),
            phase1=_normalize_stage(payload.get("phase1")),
            phase2=_normalize_stage(payload.get("phase2")),
            phase3=_normalize_stage(payload.get("phase3")),
            warnings=[str(item) for item in payload.get("warnings") or []],
            timeline=[
                {
                    "at": str(item.get("at") or ""),
                    "event": str(item.get("event") or ""),
                    "detail": str(item.get("detail") or ""),
                }
                for item in payload.get("timeline") or []
            ],
            log_path=str(payload.get("log_path") or ""),
        )


class AgentEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.agent_dir = self.project_root / ".helix" / "agent"
        self.current_path = self.agent_dir / "CURRENT.json"

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _default_log_path(self, agent_id: str) -> Path:
        return self.agent_dir / f"{agent_id}.md"

    def _validate_agent_id(self, agent_id: str) -> str:
        value = agent_id.strip()
        if not value:
            raise AgentEngineError("--agent-id is required", 2)
        return value

    def _validate_summary(self, summary: str) -> str:
        value = summary.strip()
        if not value:
            raise AgentEngineError("--summary is required", 2)
        return value

    def _validate_plan_id(self, plan_id: str) -> str:
        value = plan_id.strip()
        if not value:
            raise AgentEngineError("--plan-id is required", 2)
        return value

    def _validate_phase1_drive(self, drive: str) -> str:
        value = drive.strip()
        if value not in PHASE1_DRIVES:
            raise AgentEngineError(f"unsupported phase1 drive: {drive}", 2)
        return value

    def _validate_status(self, status: str) -> str:
        value = status.strip()
        if value not in STAGE_STATUSES:
            raise AgentEngineError(f"unsupported status: {status}", 2)
        return value

    def _new_stage(self, *, drive: str, label: str) -> dict[str, Any]:
        return {
            "label": label,
            "drive": drive,
            "plan_id": None,
            "status": "pending",
            "summary": None,
            "started_at": None,
            "completed_at": None,
            "current_layer": None,
            "layer_history": [],
        }

    def _write_session(self, session: AgentSession) -> None:
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _render_log_text(self, session: AgentSession) -> str:
        lines = [
            "---",
            f"agent_id: {session.agent_id}",
            f"status: {session.status}",
            f"current_phase: {session.current_phase}",
            f"active_phases: {', '.join(session.active_phases)}",
            f"parent_design: {session.parent_design}",
            "---",
            "",
            f"# HELIX Agent Log — {session.agent_id}",
            "",
            f"- Summary: {session.summary}",
            f"- Active phases: {', '.join(session.active_phases) or '-'}",
            f"- Phase1: {session.phase1.get('drive', '-')} / {session.phase1.get('status', '-')}",
            f"- Phase2: {session.phase2.get('drive', '-')} / {session.phase2.get('status', '-')}",
            f"- Phase3: {session.phase3.get('drive', '-')} / {session.phase3.get('status', '-')}",
            "",
            "## Timeline",
        ]
        for item in session.timeline:
            lines.append(f"- {item['at']} {item['event']}: {item['detail']}")
        lines.extend(["", "## Warnings"])
        for warning in session.warnings:
            lines.append(f"- {warning}")
        return "\n".join(lines) + "\n"

    def _write_log(self, session: AgentSession) -> None:
        path = self.project_root / session.log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_log_text(session), encoding="utf-8")

    def get_status(self) -> AgentSession | None:
        if not self.current_path.exists():
            return None
        payload = json.loads(self.current_path.read_text(encoding="utf-8"))
        return AgentSession.from_dict(payload)

    def _require_session(self) -> AgentSession:
        session = self.get_status()
        if session is None:
            raise AgentEngineError("No active agent session", 2)
        return session

    def _append_timeline(self, session: AgentSession, event: str, detail: str) -> None:
        session.timeline.append({"at": self._now_iso(), "event": event, "detail": detail})

    def _validate_layer_phase(self, phase: str) -> str:
        value = phase.strip()
        if value not in {"phase1", "phase2", "phase3"}:
            raise AgentEngineError(f"unsupported phase: {phase}", 2)
        return value

    def _activate_phase(self, session: AgentSession, phase: str) -> None:
        if phase not in session.active_phases:
            session.active_phases.append(phase)

    def _deactivate_phase(self, session: AgentSession, phase: str) -> None:
        session.active_phases = [item for item in session.active_phases if item != phase]

    def _validate_layer_name(self, phase: str, layer: str) -> str:
        value = layer.strip()
        allowed_layers = PHASE3_LAYERS if phase == "phase3" else PHASE1_LAYERS
        if value not in allowed_layers:
            raise AgentEngineError(f"unsupported layer: {layer}", 2)
        return value

    def _validate_layer_status(self, status: str) -> str:
        value = status.strip()
        if value not in {"entered", "completed"}:
            raise AgentEngineError(f"unsupported layer status: {status}", 2)
        return value

    def advance_layer(self, *, phase: str, layer: str, status: str) -> AgentSession:
        normalized_phase = self._validate_layer_phase(phase)
        normalized_layer = self._validate_layer_name(normalized_phase, layer)
        normalized_status = self._validate_layer_status(status)
        session = self._require_session()
        stage = getattr(session, normalized_phase)
        history = stage.setdefault("layer_history", [])
        now = self._now_iso()

        if normalized_status == "entered":
            if history and history[-1].get("completed_at") is None:
                history[-1]["completed_at"] = now
            stage["current_layer"] = normalized_layer
            history.append(
                {
                    "layer": normalized_layer,
                    "entered_at": now,
                    "completed_at": None,
                }
            )
        else:
            if not history or history[-1].get("layer") != normalized_layer:
                raise AgentEngineError("layer mismatch", 2)
            history[-1]["completed_at"] = now

        self._append_timeline(session, "layer", f"{normalized_phase} / {normalized_layer} / {normalized_status}")
        self._write_session(session)
        self._write_log(session)
        return session

    def init_session(self, *, agent_id: str, summary: str, phase1_drive: str = "fullstack") -> AgentSession:
        normalized_agent_id = self._validate_agent_id(agent_id)
        normalized_summary = self._validate_summary(summary)
        normalized_drive = self._validate_phase1_drive(phase1_drive)
        current = self.get_status()
        if current is not None and current.agent_id != normalized_agent_id:
            raise AgentEngineError(
                f"active agent session already exists: {current.agent_id}",
                2,
            )
        now = self._now_iso()
        session = AgentSession(
            agent_id=normalized_agent_id,
            summary=normalized_summary,
            status="initialized",
            active_phases=["phase1"],
            parent_design=PARENT_DESIGN,
            phase1=self._new_stage(drive=normalized_drive, label="一般システム"),
            phase2=self._new_stage(drive="agent", label="エージェント昇華"),
            phase3=self._new_stage(drive="agent", label="L10-L14 合流"),
            warnings=[
                "Phase 1 は be/fe/db/fullstack のいずれかで L1-L9 を完了すること",
                "Phase 2 は drive=agent で L1-L9 を完了してから merge すること",
                "route_engine 接続は scope 外のため、本 CLI は HELIX W 起動経路のみ扱う",
            ],
            timeline=[{"at": now, "event": "init", "detail": normalized_summary}],
            log_path=str(self._default_log_path(normalized_agent_id).relative_to(self.project_root)),
        )
        self._write_session(session)
        self._write_log(session)
        return session

    def update_stage1(
        self,
        *,
        plan_id: str,
        drive: str,
        status: str,
        summary: str | None = None,
    ) -> AgentSession:
        session = self._require_session()
        normalized_plan = self._validate_plan_id(plan_id)
        normalized_drive = self._validate_phase1_drive(drive)
        normalized_status = self._validate_status(status)
        now = self._now_iso()
        session.phase1.update(
            {
                "plan_id": normalized_plan,
                "drive": normalized_drive,
                "status": normalized_status,
                "summary": _optional_text(summary),
                "started_at": session.phase1.get("started_at") or now,
                "completed_at": now if normalized_status == "ready" else None,
            }
        )
        if normalized_status == "ready":
            self._activate_phase(session, "phase2")
        session.status = f"phase1_{normalized_status}"
        self._append_timeline(
            session,
            "stage1",
            f"{normalized_drive} / {normalized_plan} / {normalized_status}",
        )
        self._write_session(session)
        self._write_log(session)
        return session

    def update_stage2(
        self,
        *,
        plan_id: str,
        status: str,
        summary: str | None = None,
    ) -> AgentSession:
        session = self._require_session()
        if session.phase1.get("status") != "ready":
            raise AgentEngineError("stage1 must be ready before stage2", 2)
        normalized_plan = self._validate_plan_id(plan_id)
        normalized_status = self._validate_status(status)
        now = self._now_iso()
        session.phase2.update(
            {
                "plan_id": normalized_plan,
                "status": normalized_status,
                "summary": _optional_text(summary),
                "started_at": session.phase2.get("started_at") or now,
                "completed_at": now if normalized_status == "ready" else None,
            }
        )
        self._activate_phase(session, "phase2")
        session.status = f"phase2_{normalized_status}"
        self._append_timeline(
            session,
            "stage2",
            f"agent / {normalized_plan} / {normalized_status}",
        )
        self._write_session(session)
        self._write_log(session)
        return session

    def merge(self, *, plan_id: str, summary: str | None = None) -> AgentSession:
        session = self._require_session()
        if session.phase1.get("status") != "ready":
            raise AgentEngineError("stage1 must be ready before merge", 2)
        if session.phase2.get("status") != "ready":
            raise AgentEngineError("stage2 must be ready before merge", 2)
        normalized_plan = self._validate_plan_id(plan_id)
        now = self._now_iso()
        session.phase3.update(
            {
                "plan_id": normalized_plan,
                "status": "ready",
                "summary": _optional_text(summary),
                "started_at": session.phase3.get("started_at") or now,
                "completed_at": now,
            }
        )
        session.active_phases = ["phase3"]
        session.status = "phase3_ready"
        self._append_timeline(session, "merge", normalized_plan)
        self._write_session(session)
        self._write_log(session)
        return session

    def start_phase(self, *, phase: str) -> AgentSession:
        normalized_phase = self._validate_layer_phase(phase)
        session = self._require_session()
        getattr(session, normalized_phase)["status"] = "in_progress"
        self._activate_phase(session, normalized_phase)
        self._append_timeline(session, "phase", f"{normalized_phase} / started")
        self._write_session(session)
        self._write_log(session)
        return session

    def pause_phase(self, *, phase: str) -> AgentSession:
        normalized_phase = self._validate_layer_phase(phase)
        session = self._require_session()
        self._deactivate_phase(session, normalized_phase)
        self._append_timeline(session, "phase", f"{normalized_phase} / paused")
        self._write_session(session)
        self._write_log(session)
        return session

    def resume_phase(self, *, phase: str) -> AgentSession:
        normalized_phase = self._validate_layer_phase(phase)
        session = self._require_session()
        self._activate_phase(session, normalized_phase)
        self._append_timeline(session, "phase", f"{normalized_phase} / resumed")
        self._write_session(session)
        self._write_log(session)
        return session

    def route_current(self, phase: str | None = None) -> dict[str, Any]:
        session = self._require_session()
        selected_phase = self._normalize_phase(phase, session)
        if selected_phase == "phase1":
            drive = str(session.phase1.get("drive") or "fullstack")
            return {
                "phase": "phase1",
                "drive": drive,
                "layers": list(PHASE1_LAYERS),
                "plan_id": session.phase1.get("plan_id"),
                "parent_design": session.parent_design,
                "recommended_command": f"helix agent stage1 --plan-id <PLAN> --drive {drive} --status ready",
            }
        if selected_phase == "phase2":
            return {
                "phase": "phase2",
                "drive": "agent",
                "layers": list(PHASE1_LAYERS),
                "plan_id": session.phase2.get("plan_id"),
                "parent_design": session.parent_design,
                "recommended_command": "helix agent stage2 --plan-id <PLAN> --status ready",
            }
        return {
            "phase": "phase3",
            "drive": "agent",
            "layers": list(PHASE3_LAYERS),
            "plan_id": session.phase3.get("plan_id"),
            "parent_design": session.parent_design,
            "recommended_command": "helix agent merge --plan-id <PLAN>",
        }

    def _normalize_phase(self, phase: str | None, session: AgentSession) -> str:
        if phase is not None:
            value = phase.strip()
            if value not in {"phase1", "phase2", "phase3"}:
                raise AgentEngineError(f"unsupported phase: {phase}", 2)
            return value
        if session.phase3.get("status") == "ready":
            return "phase3"
        if session.phase1.get("status") == "ready":
            return "phase2"
        return "phase1"


def _print_session(session: AgentSession) -> None:
    print(f"[HELIX Agent] {session.agent_id} ({session.status})")
    print(f"current_phase: {session.current_phase}")
    print(f"active_phases: {', '.join(session.active_phases)}")
    print(f"parent_design: {session.parent_design}")


def _print_route(route: dict[str, Any]) -> None:
    print(f"phase: {route['phase']}")
    print(f"drive: {route['drive']}")
    print(f"layers: {', '.join(route['layers'])}")
    print(f"parent_design: {route['parent_design']}")
    print(f"recommended_command: {route['recommended_command']}")


def _phase_action_payload(session: AgentSession, *, phase: str, action: str) -> dict[str, Any]:
    return {
        "status": "ok",
        "phase": phase,
        "action": action,
        "active_phases": list(session.active_phases),
        "current_phase": session.current_phase,
    }


def _print_phase_action(payload: dict[str, Any]) -> None:
    print(f"status: {payload['status']}")
    print(f"phase: {payload['phase']} ({payload['action']})")
    print(f"active_phases: {', '.join(payload['active_phases'])}")
    print(f"current_phase: {payload['current_phase']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HELIX W agent drive controller")
    subparsers = parser.add_subparsers(dest="subcommand")

    init_parser = subparsers.add_parser("init", help="HELIX W agent session を初期化")
    init_parser.add_argument("--agent-id", required=True)
    init_parser.add_argument("--summary", required=True)
    init_parser.add_argument("--phase1-drive", default="fullstack", choices=PHASE1_DRIVES)
    init_parser.add_argument("--json", action="store_true")

    stage1_parser = subparsers.add_parser("stage1", help="Phase 1 (一般システム) を更新")
    stage1_parser.add_argument("--plan-id", required=True)
    stage1_parser.add_argument("--drive", required=True, choices=PHASE1_DRIVES)
    stage1_parser.add_argument("--status", default="in_progress", choices=STAGE_STATUSES)
    stage1_parser.add_argument("--summary")
    stage1_parser.add_argument("--json", action="store_true")

    stage2_parser = subparsers.add_parser("stage2", help="Phase 2 (agent) を更新")
    stage2_parser.add_argument("--plan-id", required=True)
    stage2_parser.add_argument("--status", default="in_progress", choices=STAGE_STATUSES)
    stage2_parser.add_argument("--summary")
    stage2_parser.add_argument("--json", action="store_true")

    merge_parser = subparsers.add_parser("merge", help="Phase 3 (L10-L14 合流) を開始")
    merge_parser.add_argument("--plan-id", required=True)
    merge_parser.add_argument("--summary")
    merge_parser.add_argument("--json", action="store_true")

    route_parser = subparsers.add_parser("route", help="現在 phase の HELIX route を表示")
    route_parser.add_argument("--phase", choices=("phase1", "phase2", "phase3"))
    route_parser.add_argument("--json", action="store_true")

    phase_parser = subparsers.add_parser("phase", help="active phases を更新")
    phase_subparsers = phase_parser.add_subparsers(dest="phase_action")
    for action in ("start", "pause", "resume"):
        action_parser = phase_subparsers.add_parser(action, help=f"phase を {action} する")
        action_parser.add_argument("--phase", required=True)
        action_parser.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    engine = AgentEngine()

    try:
        if args.subcommand == "init":
            session = engine.init_session(
                agent_id=args.agent_id,
                summary=args.summary,
                phase1_drive=args.phase1_drive,
            )
            if args.json:
                print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_session(session)
            return 0

        if args.subcommand == "stage1":
            session = engine.update_stage1(
                plan_id=args.plan_id,
                drive=args.drive,
                status=args.status,
                summary=args.summary,
            )
            if args.json:
                print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_session(session)
            return 0

        if args.subcommand == "stage2":
            session = engine.update_stage2(
                plan_id=args.plan_id,
                status=args.status,
                summary=args.summary,
            )
            if args.json:
                print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_session(session)
            return 0

        if args.subcommand == "merge":
            session = engine.merge(plan_id=args.plan_id, summary=args.summary)
            if args.json:
                print(json.dumps(session.to_dict(), ensure_ascii=False, indent=2))
            else:
                _print_session(session)
            return 0

        if args.subcommand == "route":
            route = engine.route_current(phase=args.phase)
            if args.json:
                print(json.dumps(route, ensure_ascii=False, indent=2))
            else:
                _print_route(route)
            return 0

        if args.subcommand == "phase":
            if args.phase_action == "start":
                session = engine.start_phase(phase=args.phase)
                payload = _phase_action_payload(session, phase=args.phase, action="started")
            elif args.phase_action == "pause":
                session = engine.pause_phase(phase=args.phase)
                payload = _phase_action_payload(session, phase=args.phase, action="paused")
            elif args.phase_action == "resume":
                session = engine.resume_phase(phase=args.phase)
                payload = _phase_action_payload(session, phase=args.phase, action="resumed")
            else:
                parser.print_help()
                return 1
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                _print_phase_action(payload)
            return 0

        parser.print_help()
        return 1
    except AgentEngineError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
