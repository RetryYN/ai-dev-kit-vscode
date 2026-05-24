"""Add-feature mode CLI backend.

契約:
- HELIX-workflows/helix-process/add-feature-workflow.md
- docs/plans/L7/L7-cli-helix-add-feature-implplan.md
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


REQUIREMENT_LAYERS = ("L1", "L3")
DESIGN_LAYERS = ("L4", "L5", "L6")
IMPLEMENTATION_LAYERS = ("L7", "L8", "L9")
BASE_WARNINGS = [
    "要件変更を伴う場合は L1/L3 の追補も別途反映すること",
    "route_engine 接続は別 PLAN carry",
]


class AddFeatureError(RuntimeError):
    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _optional_text(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _normalize_path_list(values: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        text = value.strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _validate_feature(value: str) -> str:
    feature = value.strip()
    if not feature:
        raise AddFeatureError("--feature is required", 2)
    return feature


def _validate_summary(value: str) -> str:
    summary = value.strip()
    if not summary:
        raise AddFeatureError("--summary is required", 2)
    return summary


def _validate_plan_id(value: str, flag_name: str) -> str:
    plan_id = value.strip()
    if not plan_id:
        raise AddFeatureError(f"{flag_name} is required", 2)
    return plan_id


def _build_route_targets(requirement_layers: list[str]) -> list[dict[str, str]]:
    targets: list[dict[str, str]] = []
    for layer in requirement_layers:
        targets.append({"layer": layer, "purpose": "追加要求/要件を既存ドキュメントへ追補"})
    targets.extend(
        [
            {"layer": "L4", "purpose": "基本設計に追加 feature の差分を追補"},
            {"layer": "L5", "purpose": "詳細設計に契約/構成の差分を追補"},
            {"layer": "L6", "purpose": "機能設計と単体テスト設計の trace を更新"},
            {"layer": "L7", "purpose": "追加実装を既存 impl PLAN に紐づけて実施"},
            {"layer": "L8", "purpose": "既存結合テスト影響を確認し追加ケースを反映"},
            {"layer": "L9", "purpose": "既存総合テスト回帰を確認する"},
        ]
    )
    return targets


@dataclass(slots=True)
class AddFeatureSession:
    feature_id: str
    summary: str
    status: str
    design_plan: str
    impl_plan: str | None
    requirement_layers: list[str]
    design_docs: list[str]
    modules: list[str]
    test_paths: list[str]
    warnings: list[str]
    route_targets: list[dict[str, str]]
    timeline: list[dict[str, str]]
    log_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AddFeatureSession":
        return cls(
            feature_id=str(payload.get("feature_id") or ""),
            summary=str(payload.get("summary") or ""),
            status=str(payload.get("status") or ""),
            design_plan=str(payload.get("design_plan") or ""),
            impl_plan=_optional_text(payload.get("impl_plan")),
            requirement_layers=[str(item) for item in payload.get("requirement_layers") or []],
            design_docs=[str(item) for item in payload.get("design_docs") or []],
            modules=[str(item) for item in payload.get("modules") or []],
            test_paths=[str(item) for item in payload.get("test_paths") or []],
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


class AddFeatureEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.state_dir = self.project_root / ".helix" / "add-feature"
        self.current_path = self.state_dir / "CURRENT.json"

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _default_log_path(self, feature_id: str) -> Path:
        return self.state_dir / f"{feature_id}.md"

    def _write_session(self, session: AddFeatureSession) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.current_path.write_text(
            json.dumps(session.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _render_log_text(self, session: AddFeatureSession) -> str:
        lines = [
            "---",
            f"feature_id: {session.feature_id}",
            f"status: {session.status}",
            f"design_plan: {session.design_plan}",
            f"impl_plan: {session.impl_plan or '-'}",
            "---",
            "",
            f"# Add-feature Log — {session.feature_id}",
            "",
            f"- Summary: {session.summary}",
            f"- Requirement layers: {', '.join(session.requirement_layers) or '-'}",
            f"- Design docs: {', '.join(session.design_docs) or '-'}",
            f"- Modules: {', '.join(session.modules) or '-'}",
            f"- Test paths: {', '.join(session.test_paths) or '-'}",
            "",
            "## Timeline",
        ]
        for item in session.timeline:
            lines.append(f"- {item['at']} {item['event']}: {item['detail']}")
        lines.extend(["", "## Forward Routes"])
        for route in session.route_targets:
            lines.append(f"- {route['layer']}: {route['purpose']}")
        return "\n".join(lines) + "\n"

    def _write_log(self, session: AddFeatureSession) -> None:
        path = self.project_root / session.log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_log_text(session), encoding="utf-8")

    def get_status(self) -> AddFeatureSession | None:
        if not self.current_path.exists():
            return None
        payload = json.loads(self.current_path.read_text(encoding="utf-8"))
        return AddFeatureSession.from_dict(payload)

    def _require_session(self) -> AddFeatureSession:
        session = self.get_status()
        if session is None:
            raise AddFeatureError("No active add-feature session", 2)
        return session

    def add_design(
        self,
        *,
        feature_id: str,
        summary: str,
        requires_plan: str,
        design_docs: list[str] | None = None,
        requirement_layers: list[str] | None = None,
    ) -> AddFeatureSession:
        normalized_feature = _validate_feature(feature_id)
        normalized_summary = _validate_summary(summary)
        normalized_plan = _validate_plan_id(requires_plan, "--requires-plan")
        current = self.get_status()
        if current is not None and current.feature_id != normalized_feature:
            raise AddFeatureError(
                f"active session already exists for feature: {current.feature_id}",
                2,
            )

        selected_requirement_layers = [layer for layer in requirement_layers or [] if layer in REQUIREMENT_LAYERS]
        now = self._now_iso()
        session = AddFeatureSession(
            feature_id=normalized_feature,
            summary=normalized_summary,
            status="design_supplemented",
            design_plan=normalized_plan,
            impl_plan=current.impl_plan if current else None,
            requirement_layers=selected_requirement_layers,
            design_docs=_normalize_path_list(design_docs),
            modules=current.modules if current else [],
            test_paths=current.test_paths if current else [],
            warnings=list(BASE_WARNINGS),
            route_targets=_build_route_targets(selected_requirement_layers),
            timeline=(current.timeline if current else [])
            + [{"at": now, "event": "add-design", "detail": normalized_summary}],
            log_path=str(self._default_log_path(normalized_feature).relative_to(self.project_root)),
        )
        self._write_session(session)
        self._write_log(session)
        return session

    def add_impl(
        self,
        *,
        feature_id: str,
        summary: str,
        requires_plan: str,
        modules: list[str],
        test_paths: list[str] | None = None,
    ) -> AddFeatureSession:
        session = self._require_session()
        normalized_feature = _validate_feature(feature_id)
        if session.feature_id != normalized_feature:
            raise AddFeatureError(
                f"active session feature mismatch: expected {session.feature_id}, got {normalized_feature}",
                2,
            )
        if session.status not in {"design_supplemented", "implementation_supplemented"}:
            raise AddFeatureError("add-design must be completed before add-impl", 2)

        normalized_summary = _validate_summary(summary)
        normalized_plan = _validate_plan_id(requires_plan, "--requires-plan")
        normalized_modules = _normalize_path_list(modules)
        if not normalized_modules:
            raise AddFeatureError("--module is required", 2)

        session.summary = normalized_summary
        session.status = "implementation_supplemented"
        session.impl_plan = normalized_plan
        session.modules = normalized_modules
        session.test_paths = _normalize_path_list(test_paths)
        session.timeline.append(
            {"at": self._now_iso(), "event": "add-impl", "detail": normalized_summary}
        )
        self._write_session(session)
        self._write_log(session)
        return session

    def build_route_payload(self) -> dict[str, Any]:
        session = self._require_session()
        ready = session.status == "implementation_supplemented"
        next_step = (
            "L8/L9 の回帰確認へ進み、必要なら L1/L3 の追補も別 PLAN で反映する"
            if ready
            else "add-design → add-impl を完了してから L8/L9 回帰確認へ進む"
        )
        return {
            "feature_id": session.feature_id,
            "status": session.status,
            "design_plan": session.design_plan,
            "impl_plan": session.impl_plan,
            "ready_for_integration": ready,
            "next_step": next_step,
            "routes": session.route_targets,
            "warnings": session.warnings,
        }


def _emit(payload: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if isinstance(payload, dict) and "feature_id" in payload:
        lines = [f"[HELIX Add-feature] {payload['feature_id']} ({payload.get('status', '-')})"]
        if "design_plan" in payload:
            lines.append(f"design_plan={payload['design_plan']} impl_plan={payload.get('impl_plan') or '-'}")
        if "next_step" in payload:
            lines.append(f"next={payload['next_step']}")
        for route in payload.get("routes") or []:
            lines.append(f"{route['layer']}: {route['purpose']}")
        print("\n".join(lines))
        return
    print(str(payload))


def _session_payload(session: AddFeatureSession) -> dict[str, Any]:
    return {
        "feature_id": session.feature_id,
        "status": session.status,
        "design_plan": session.design_plan,
        "impl_plan": session.impl_plan,
        "design_docs": session.design_docs,
        "modules": session.modules,
        "test_paths": session.test_paths,
        "log_path": session.log_path,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix add-feature")
    sub = parser.add_subparsers(dest="command", required=True)

    add_design = sub.add_parser("add-design")
    add_design.add_argument("--feature", required=True)
    add_design.add_argument("--summary", required=True)
    add_design.add_argument("--requires-plan", required=True)
    add_design.add_argument("--design-doc", action="append", default=[])
    add_design.add_argument("--requirements-layer", action="append", choices=REQUIREMENT_LAYERS, default=[])
    add_design.add_argument("--json", action="store_true")

    add_impl = sub.add_parser("add-impl")
    add_impl.add_argument("--feature", required=True)
    add_impl.add_argument("--summary", required=True)
    add_impl.add_argument("--requires-plan", required=True)
    add_impl.add_argument("--module", action="append", default=[])
    add_impl.add_argument("--test-path", action="append", default=[])
    add_impl.add_argument("--json", action="store_true")

    status = sub.add_parser("status")
    status.add_argument("--json", action="store_true")

    route = sub.add_parser("route")
    route.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = AddFeatureEngine()
    try:
        if args.command == "add-design":
            session = engine.add_design(
                feature_id=args.feature,
                summary=args.summary,
                requires_plan=args.requires_plan,
                design_docs=args.design_doc,
                requirement_layers=args.requirements_layer,
            )
            _emit(_session_payload(session), args.json)
            return 0
        if args.command == "add-impl":
            session = engine.add_impl(
                feature_id=args.feature,
                summary=args.summary,
                requires_plan=args.requires_plan,
                modules=args.module,
                test_paths=args.test_path,
            )
            _emit(_session_payload(session), args.json)
            return 0
        if args.command == "status":
            session = engine.get_status()
            if session is None:
                raise AddFeatureError("No active add-feature session", 2)
            _emit(_session_payload(session), args.json)
            return 0
        if args.command == "route":
            _emit(engine.build_route_payload(), args.json)
            return 0
        raise AddFeatureError(f"unsupported command: {args.command}", 2)
    except AddFeatureError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
