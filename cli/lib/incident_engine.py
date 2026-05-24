"""Incident mode CLI backend.

契約:
- HELIX-workflows/helix-process/incident-workflow.md
- docs/plans/L7/L7-cli-helix-incident-implplan.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


VALID_SEVERITIES = ("P0", "P1", "P2", "P3")
VALID_ENVS = ("prod", "dev")
VALID_KINDS = ("recovery", "troubleshoot")
FORWARD_ROUTES = (
    {"layer": "L1", "purpose": "暫定対処を要求定義へ昇華"},
    {"layer": "L3", "purpose": "運用要件・復旧要件を要件定義へ反映"},
    {"layer": "L4-L6", "purpose": "恒久対策の設計・実装を正式化"},
    {"layer": "L8", "purpose": "再発防止の結合テストを追加"},
    {"layer": "L9", "purpose": "総合テストで hotfix 回帰を確認"},
    {"layer": "L14", "purpose": "postmortem と運用学習へ接続"},
)


class IncidentError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


@dataclass(slots=True)
class IncidentSession:
    incident_id: str
    summary: str
    severity: str
    env: str
    kind: str
    status: str
    detected_at: str
    triaged_at: str | None
    hotfix_at: str | None
    resolved_at: str | None
    owner: str | None
    impact: str | None
    release_ref: str | None
    warnings: list[str]
    route_targets: list[dict[str, str]]
    timeline: list[dict[str, str]]
    log_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "IncidentSession":
        return cls(
            incident_id=str(payload.get("incident_id") or ""),
            summary=str(payload.get("summary") or ""),
            severity=str(payload.get("severity") or "P1"),
            env=str(payload.get("env") or "prod"),
            kind=str(payload.get("kind") or "recovery"),
            status=str(payload.get("status") or "detected"),
            detected_at=str(payload.get("detected_at") or ""),
            triaged_at=_optional_text(payload.get("triaged_at")),
            hotfix_at=_optional_text(payload.get("hotfix_at")),
            resolved_at=_optional_text(payload.get("resolved_at")),
            owner=_optional_text(payload.get("owner")),
            impact=_optional_text(payload.get("impact")),
            release_ref=_optional_text(payload.get("release_ref")),
            warnings=[str(item) for item in payload.get("warnings") or []],
            route_targets=[
                {"layer": str(item.get("layer") or ""), "purpose": str(item.get("purpose") or "")}
                for item in payload.get("route_targets") or []
            ],
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


class IncidentEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.incident_dir = self.project_root / ".helix" / "incident"
        self.current_path = self.incident_dir / "CURRENT.json"

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _default_log_path(self, incident_id: str) -> Path:
        return self.incident_dir / f"incident-{incident_id}.md"

    def _validate_severity(self, severity: str) -> str:
        value = severity.strip().upper()
        if value not in VALID_SEVERITIES:
            raise IncidentError(f"unsupported severity: {severity}", 2)
        return value

    def _validate_env(self, env: str) -> str:
        value = env.strip().lower()
        if value not in VALID_ENVS:
            raise IncidentError(f"unsupported env: {env}", 2)
        return value

    def _validate_kind(self, kind: str | None, env: str) -> str:
        if kind is None:
            return "recovery" if env == "prod" else "troubleshoot"
        value = kind.strip().lower()
        if value not in VALID_KINDS:
            raise IncidentError(f"unsupported kind: {kind}", 2)
        return value

    def _write_session(self, session: IncidentSession) -> None:
        self.incident_dir.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get_status(self) -> IncidentSession | None:
        if not self.current_path.exists():
            return None
        return IncidentSession.from_dict(json.loads(self.current_path.read_text(encoding="utf-8")))

    def _require_session(self) -> IncidentSession:
        session = self.get_status()
        if session is None:
            raise IncidentError("No active incident session", 2)
        return session

    def _append_timeline(self, session: IncidentSession, event: str, detail: str) -> None:
        session.timeline.append({"at": self._now_iso(), "event": event, "detail": detail})

    def _render_log_text(self, session: IncidentSession) -> str:
        lines = [
            "---",
            f"incident_id: {session.incident_id}",
            f"severity: {session.severity}",
            f"env: {session.env}",
            f"kind: {session.kind}",
            f"status: {session.status}",
            "---",
            "",
            f"# Incident Log — {session.incident_id}",
            "",
            f"- Summary: {session.summary}",
            f"- Owner: {session.owner or '-'}",
            f"- Impact: {session.impact or '-'}",
            f"- Release Ref: {session.release_ref or '-'}",
            "",
            "## Timeline",
        ]
        for item in session.timeline:
            lines.append(f"- {item['at']} {item['event']}: {item['detail']}")
        if len(session.timeline) == 0:
            lines.append("- pending")
        lines.extend(["", "## Forward Routes"])
        for route in session.route_targets:
            lines.append(f"- {route['layer']}: {route['purpose']}")
        return "\n".join(lines) + "\n"

    def _write_log(self, session: IncidentSession) -> None:
        path = self.project_root / session.log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_log_text(session), encoding="utf-8")

    def _base_routes(self) -> list[dict[str, str]]:
        return [dict(item) for item in FORWARD_ROUTES]

    def detect_incident(
        self,
        *,
        incident_id: str,
        summary: str,
        severity: str,
        env: str,
        dry_run: bool = False,
    ) -> IncidentSession:
        normalized_severity = self._validate_severity(severity)
        normalized_env = self._validate_env(env)
        if not incident_id.strip():
            raise IncidentError("--incident-id is required", 2)
        if not summary.strip():
            raise IncidentError("--summary is required", 2)
        if self.get_status() is not None and not dry_run:
            raise IncidentError("active incident session already exists", 2)
        now = self._now_iso()
        session = IncidentSession(
            incident_id=incident_id.strip(),
            summary=summary.strip(),
            severity=normalized_severity,
            env=normalized_env,
            kind="recovery" if normalized_env == "prod" else "troubleshoot",
            status="detected",
            detected_at=now,
            triaged_at=None,
            hotfix_at=None,
            resolved_at=None,
            owner=None,
            impact=None,
            release_ref=None,
            warnings=["暫定収束後は route で L1/L3/L4-L6/L14 へ昇華すること"],
            route_targets=self._base_routes(),
            timeline=[{"at": now, "event": "detected", "detail": summary.strip()}],
            log_path=str(self._default_log_path(incident_id.strip()).relative_to(self.project_root)),
        )
        if not dry_run:
            self._write_session(session)
            self._write_log(session)
        return session

    def triage_incident(
        self,
        *,
        owner: str,
        impact: str,
        severity: str | None = None,
        kind: str | None = None,
    ) -> IncidentSession:
        session = self._require_session()
        if severity is not None:
            session.severity = self._validate_severity(severity)
        session.owner = owner.strip()
        session.impact = impact.strip()
        session.kind = self._validate_kind(kind, session.env)
        session.status = "triaged"
        session.triaged_at = self._now_iso()
        self._append_timeline(session, "triaged", f"{session.owner} / {session.kind} / {session.impact}")
        self._write_session(session)
        self._write_log(session)
        return session

    def apply_hotfix(
        self,
        *,
        change: str,
        release_ref: str | None = None,
        converged: bool = True,
    ) -> IncidentSession:
        session = self._require_session()
        session.release_ref = _optional_text(release_ref)
        session.status = "mitigated" if converged else "hotfix_in_progress"
        session.hotfix_at = self._now_iso()
        if converged:
            session.resolved_at = session.hotfix_at
        self._append_timeline(session, "hotfix", change.strip())
        self._write_session(session)
        self._write_log(session)
        return session

    def build_route_payload(self) -> dict[str, Any]:
        session = self._require_session()
        ready = session.status in {"mitigated", "resolved"}
        next_step = (
            "恒久対策を L1/L3/L4-L6 に起票し、L14 postmortem へ接続"
            if ready
            else "detect → triage → hotfix 完了後に恒久対策へ接続"
        )
        return {
            "incident_id": session.incident_id,
            "status": session.status,
            "kind": session.kind,
            "ready_for_formalization": ready,
            "next_step": next_step,
            "routes": session.route_targets,
        }

    def generate_postmortem(self, output_path: Path) -> Path:
        session = self._require_session()
        if output_path.exists():
            raise IncidentError(f"output already exists: {output_path}", 2)
        payload = self.build_route_payload()
        lines = [
            f"# Incident Postmortem — {session.incident_id}",
            "",
            "## Summary",
            f"- Severity: {session.severity}",
            f"- Env: {session.env}",
            f"- Kind: {session.kind}",
            f"- Status: {session.status}",
            f"- Owner: {session.owner or '-'}",
            f"- Impact: {session.impact or '-'}",
            f"- Release Ref: {session.release_ref or '-'}",
            "",
            "## Timeline",
        ]
        for item in session.timeline:
            lines.append(f"- {item['at']} {item['event']}: {item['detail']}")
        lines.extend(
            [
                "",
                "## Forward Formalization",
                f"- Ready: {'yes' if payload['ready_for_formalization'] else 'no'}",
                f"- Next: {payload['next_step']}",
            ]
        )
        for route in payload["routes"]:
            lines.append(f"- {route['layer']}: {route['purpose']}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path


def _emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if isinstance(payload, dict) and "incident_id" in payload:
        lines = [f"[HELIX Incident] {payload['incident_id']} ({payload.get('status', '-')})"]
        if "kind" in payload:
            lines.append(f"kind={payload['kind']} ready={payload.get('ready_for_formalization', '-')}")
        if "next_step" in payload:
            lines.append(f"next={payload['next_step']}")
        if "routes" in payload:
            for route in payload["routes"]:
                lines.append(f"{route['layer']}: {route['purpose']}")
        print("\n".join(lines))
        return
    print(str(payload))


def _session_payload(session: IncidentSession) -> dict[str, Any]:
    return {
        "incident_id": session.incident_id,
        "status": session.status,
        "severity": session.severity,
        "env": session.env,
        "kind": session.kind,
        "log_path": session.log_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix incident")
    sub = parser.add_subparsers(dest="command", required=True)

    detect = sub.add_parser("detect")
    detect.add_argument("--incident-id", required=True)
    detect.add_argument("--summary", required=True)
    detect.add_argument("--severity", default="P1")
    detect.add_argument("--env", default="prod")
    detect.add_argument("--dry-run", action="store_true")
    detect.add_argument("--json", action="store_true")

    triage = sub.add_parser("triage")
    triage.add_argument("--owner", required=True)
    triage.add_argument("--impact", required=True)
    triage.add_argument("--severity")
    triage.add_argument("--kind")
    triage.add_argument("--json", action="store_true")

    hotfix = sub.add_parser("hotfix")
    hotfix.add_argument("--change", required=True)
    hotfix.add_argument("--release-ref")
    hotfix.add_argument("--no-converged", action="store_true")
    hotfix.add_argument("--json", action="store_true")

    postmortem = sub.add_parser("postmortem")
    postmortem.add_argument("--output", required=True)

    route = sub.add_parser("route")
    route.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = IncidentEngine()
    try:
        if args.command == "detect":
            session = engine.detect_incident(
                incident_id=args.incident_id,
                summary=args.summary,
                severity=args.severity,
                env=args.env,
                dry_run=args.dry_run,
            )
            payload = _session_payload(session)
            if args.dry_run:
                payload["dry_run"] = True
            _emit(payload, args.json)
            return 0
        if args.command == "triage":
            session = engine.triage_incident(
                owner=args.owner,
                impact=args.impact,
                severity=args.severity,
                kind=args.kind,
            )
            _emit(_session_payload(session), args.json)
            return 0
        if args.command == "hotfix":
            session = engine.apply_hotfix(
                change=args.change,
                release_ref=args.release_ref,
                converged=not args.no_converged,
            )
            _emit(_session_payload(session), args.json)
            return 0
        if args.command == "postmortem":
            output = engine.generate_postmortem(Path(args.output).expanduser())
            print(str(output))
            return 0
        if args.command == "route":
            _emit(engine.build_route_payload(), args.json)
            return 0
        raise IncidentError(f"unsupported command: {args.command}", 2)
    except IncidentError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
