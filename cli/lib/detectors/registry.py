from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR.parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from detectors.base import (  # noqa: E402
    BaseDetector,
    DetectorResult,
    STUB_REASON,
    emit_json,
    load_config,
    record_detector_run,
)
from detectors.axis_01_dead import Axis01DeadCodeDrift  # noqa: E402
from detectors.axis_02_coverage import Axis02CoverageErosion  # noqa: E402
import helix_db  # noqa: E402


EXIT_USAGE = 64
EXIT_BLOCKED = 2


@dataclass(frozen=True, slots=True)
class DetectorDescriptor:
    axis_id: str
    name: str
    phase_gate: str | None
    kind: str


class TelemetryDetector(BaseDetector):
    id = "axis-00"
    name = "telemetry baseline"
    phase_gate = None
    kind = "baseline"

    def run(self, db_path: str | Path) -> DetectorResult:
        return DetectorResult(
            verdict="blocked",
            findings=[],
            cost_ms=0,
            raw={"reason": STUB_REASON, "baseline": True},
        )


def _make_stub_detector(axis_id: str, name: str, phase_gate: str | None) -> type[BaseDetector]:
    detector_name = name
    detector_gate = phase_gate

    class _StubDetector(BaseDetector):
        id = axis_id
        name = detector_name
        phase_gate = detector_gate
        kind = "stub"

        def run(self, db_path: str | Path) -> DetectorResult:
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=0,
                raw={"reason": STUB_REASON},
            )

    _StubDetector.__name__ = "Detector" + axis_id.replace("-", "_").replace("axis_", "Axis")
    return _StubDetector


Axis03RealDuplicate = _make_stub_detector("axis-03", "real duplicate", "G4")
Axis04SkillDecay = _make_stub_detector("axis-04", "skill resolution decay", None)
Axis05PlanDebtLoop = _make_stub_detector("axis-05", "plan debt loop", "G6")
Axis06NamingConfusion = _make_stub_detector("axis-06", "naming confusion", "G2")
Axis07DocDrift = _make_stub_detector("axis-07", "doc expression drift", "G2")
Axis08PlanIntegrity = _make_stub_detector("axis-08", "plan-retro integrity", "G6")
Axis09RefactorOpportunity = _make_stub_detector("axis-09", "refactoring opportunity", "G4")
Axis10RelationGraph = _make_stub_detector("axis-10", "relation graph", None)
Axis11RegressionDetection = _make_stub_detector("axis-11", "regression detection", "G6")
Axis12ConnectionDeficiency = _make_stub_detector("axis-12", "connection deficiency", "G2")
Axis13ModelSkillAnalytics = _make_stub_detector("axis-13", "model & skill analytics", None)
Axis14OrchestrationIntegrity = _make_stub_detector("axis-14", "orchestration integrity", "G4")


REGISTRY: dict[str, type[BaseDetector]] = {
    TelemetryDetector.id: TelemetryDetector,
    Axis01DeadCodeDrift.id: Axis01DeadCodeDrift,
    Axis02CoverageErosion.id: Axis02CoverageErosion,
    Axis03RealDuplicate.id: Axis03RealDuplicate,
    Axis04SkillDecay.id: Axis04SkillDecay,
    Axis05PlanDebtLoop.id: Axis05PlanDebtLoop,
    Axis06NamingConfusion.id: Axis06NamingConfusion,
    Axis07DocDrift.id: Axis07DocDrift,
    Axis08PlanIntegrity.id: Axis08PlanIntegrity,
    Axis09RefactorOpportunity.id: Axis09RefactorOpportunity,
    Axis10RelationGraph.id: Axis10RelationGraph,
    Axis11RegressionDetection.id: Axis11RegressionDetection,
    Axis12ConnectionDeficiency.id: Axis12ConnectionDeficiency,
    Axis13ModelSkillAnalytics.id: Axis13ModelSkillAnalytics,
    Axis14OrchestrationIntegrity.id: Axis14OrchestrationIntegrity,
}


def _descriptor(detector: type[BaseDetector]) -> DetectorDescriptor:
    return DetectorDescriptor(
        axis_id=detector.id,
        name=detector.name,
        phase_gate=detector.phase_gate,
        kind=getattr(detector, "kind", "stub"),
    )


def _detector_status(detector: BaseDetector) -> str:
    kind = getattr(detector, "kind", "stub")
    return "baseline" if kind == "baseline" else kind


def list_detectors() -> list[dict[str, Any]]:
    return [
        {
            "axis_id": descriptor.axis_id,
            "name": descriptor.name,
            "phase_gate": descriptor.phase_gate,
            "kind": descriptor.kind,
            "status": "baseline" if descriptor.kind == "baseline" else descriptor.kind,
        }
        for descriptor in (_descriptor(REGISTRY[axis_id]) for axis_id in sorted(REGISTRY.keys()))
    ]


def get_detector(axis_id: str) -> BaseDetector:
    detector_cls = REGISTRY.get(axis_id)
    if detector_cls is None:
        raise KeyError(axis_id)
    return detector_cls()


def run_detector(axis_id: str, db_path: str | Path, *, config: dict[str, Any] | None = None) -> DetectorResult:
    detector = get_detector(axis_id)
    resolved_config = config if config is not None else load_config(db_path)
    result = detector.run(db_path)
    record_detector_run(db_path, detector, result, config=resolved_config, command="run")
    return result


def run_all(db_path: str | Path, *, config: dict[str, Any] | None = None) -> dict[str, DetectorResult]:
    resolved_config = config if config is not None else load_config(db_path)
    results: dict[str, DetectorResult] = {}
    for axis_id in sorted(REGISTRY.keys()):
        detector = get_detector(axis_id)
        result = detector.run(db_path)
        record_detector_run(db_path, detector, result, config=resolved_config, command="run-all")
        results[axis_id] = result
    return results


def _detector_payload(axis_id: str, detector: BaseDetector, result: DetectorResult | None = None) -> dict[str, Any]:
    payload = {
        "axis_id": axis_id,
        "name": detector.name,
        "phase_gate": detector.phase_gate,
        "kind": getattr(detector, "kind", "stub"),
    }
    if result is not None:
        payload.update(result.to_dict())
        payload["status"] = "stub" if result.raw.get("reason") == STUB_REASON else _detector_status(detector)
    else:
        payload["status"] = _detector_status(detector)
    return payload


def dashboard_data(db_path: str | Path | None = None) -> dict[str, Any]:
    target_db = Path(db_path or helix_db.resolve_default_db_path())
    results = run_all(target_db)
    axes: list[dict[str, Any]] = []
    counts = {"passed": 0, "failed": 0, "blocked": 0}
    for axis_id in sorted(REGISTRY.keys()):
        detector = get_detector(axis_id)
        result = results[axis_id]
        payload = _detector_payload(axis_id, detector, result)
        axes.append(payload)
        counts[result.verdict] += 1

    mermaid = _render_mermaid(axes, counts)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(axes),
        "counts": counts,
        "passed_axes": [item["axis_id"] for item in axes if item["verdict"] == "passed"],
        "blocked_axes": [item["axis_id"] for item in axes if item["verdict"] == "blocked"],
        "axes": axes,
        "mermaid": mermaid,
    }


def _verdict_color(verdict: str) -> str:
    return {
        "passed": "fill:#d1fae5,stroke:#059669,color:#064e3b",
        "failed": "fill:#fee2e2,stroke:#dc2626,color:#7f1d1d",
        "blocked": "fill:#e5e7eb,stroke:#6b7280,color:#111827",
    }.get(verdict, "fill:#e5e7eb,stroke:#6b7280,color:#111827")


def _render_mermaid(axes: Iterable[dict[str, Any]], counts: dict[str, int]) -> str:
    lines = ["graph TD", "  %% PLAN-063 detector dashboard"]
    for item in axes:
        axis_id = item["axis_id"]
        label = f"{axis_id}<br/>{item['name']}<br/>{item['verdict']}"
        node_name = axis_id.replace("-", "_")
        lines.append(f'  {node_name}["{label}"]')
        lines.append(f"  style {node_name} {_verdict_color(item['verdict'])}")
    lines.append(
        "  summary[[passed={passed} blocked={blocked} failed={failed}]]".format(
            passed=counts.get("passed", 0),
            blocked=counts.get("blocked", 0),
            failed=counts.get("failed", 0),
        )
    )
    for item in axes:
        lines.append(f"  summary --> {item['axis_id'].replace('-', '_')}")
    return "\n".join(lines)


def _render_list_text(items: list[dict[str, Any]]) -> str:
    lines = ["axis-id\tname\tgate\tkind\tstatus"]
    for item in items:
        gate = item["phase_gate"] or "-"
        lines.append(
            f"{item['axis_id']}\t{item['name']}\t{gate}\t{item['kind']}\t{item['status']}"
        )
    return "\n".join(lines)


def _render_run_text(axis_id: str, result: DetectorResult) -> str:
    detector = get_detector(axis_id)
    status = "stub" if result.raw.get("reason") == STUB_REASON else result.verdict
    gate = detector.phase_gate or "-"
    return (
        f"axis={axis_id} name={detector.name} gate={gate} "
        f"verdict={result.verdict} status={status} cost_ms={result.cost_ms}"
    )


def _render_dashboard_text(data: dict[str, Any]) -> str:
    lines = [
        "helix detect dashboard",
        f"total={data['total']} passed={data['counts']['passed']} failed={data['counts']['failed']} blocked={data['counts']['blocked']}",
    ]
    for item in data["axes"]:
        gate = item["phase_gate"] or "-"
        lines.append(f"{item['axis_id']}\t{item['name']}\t{gate}\t{item['verdict']}")
    return "\n".join(lines)


def _parse_args(argv: list[str]) -> dict[str, Any]:
    json_output = False
    fail_under = None
    output_format = "text"
    help_requested = False
    remaining: list[str] = []
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token in {"-h", "--help"}:
            help_requested = True
            idx += 1
            continue
        if token == "--json":
            json_output = True
            idx += 1
            continue
        if token == "--fail-under":
            if idx + 1 >= len(argv):
                raise ValueError("--fail-under には数値が必要です")
            fail_under = int(argv[idx + 1])
            idx += 2
            continue
        if token == "--format":
            if idx + 1 >= len(argv):
                raise ValueError("--format には値が必要です")
            output_format = argv[idx + 1]
            idx += 2
            continue
        remaining.append(token)
        idx += 1

    if help_requested:
        return {"command": "help", "json": json_output, "fail_under": fail_under, "format": output_format, "args": remaining}

    if not remaining:
        raise ValueError("subcommand が必要です")

    command = remaining[0]
    args = remaining[1:]
    return {
        "command": command,
        "json": json_output,
        "fail_under": fail_under,
        "format": output_format,
        "args": args,
    }


def _usage() -> str:
    return (
        "Usage: helix detect [--json] [--fail-under N] <list|run|dashboard> [args...]\n\n"
        "Commands:\n"
        "  list                    detector 一覧を表示\n"
        "  run <axis-id>           指定 detector を実行\n"
        "  dashboard               全 detector を集約して表示\n"
        "\nOptions:\n"
        "  --json                  JSON で structured output を出力\n"
        "  --fail-under N          passed 数の下限を指定\n"
        "  --format text|mermaid   dashboard の表示形式\n"
    )


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    try:
        parsed = _parse_args(raw_argv)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return EXIT_USAGE

    if parsed["command"] == "help":
        print(_usage())
        return 0

    command = parsed["command"]
    json_output = bool(parsed["json"])
    fail_under = parsed["fail_under"]
    output_format = parsed["format"]
    args = parsed["args"]
    db_path = Path(helix_db.resolve_default_db_path())

    if command == "list":
        if args:
            print(f"未知の引数: {' '.join(args)}", file=sys.stderr)
            return EXIT_USAGE
        items = list_detectors()
        if json_output:
            emit_json({"total": len(items), "detectors": items})
        else:
            print(_render_list_text(items))
        return 0

    if command == "run":
        if len(args) != 1:
            print("run には axis-id が必要です", file=sys.stderr)
            print(_usage(), file=sys.stderr)
            return EXIT_USAGE
        axis_id = args[0]
        try:
            result = run_detector(axis_id, db_path)
        except KeyError:
            print(f"未知の detector: {axis_id}", file=sys.stderr)
            return EXIT_USAGE
        detector = get_detector(axis_id)
        payload = {
            "detector": {
                "axis_id": detector.id,
                "name": detector.name,
                "phase_gate": detector.phase_gate,
                "kind": getattr(detector, "kind", "stub"),
            },
            "result": result.to_dict(),
            "status": "stub" if result.raw.get("reason") == STUB_REASON else result.verdict,
        }
        if json_output:
            emit_json(payload)
        else:
            print(_render_run_text(axis_id, result))
        if fail_under is not None and (1 if result.verdict == "passed" else 0) < fail_under:
            return 1 if result.verdict != "blocked" else EXIT_BLOCKED
        if result.verdict == "passed":
            return 0
        if result.verdict == "failed":
            return 1
        return EXIT_BLOCKED

    if command == "dashboard":
        if args:
            print(f"未知の引数: {' '.join(args)}", file=sys.stderr)
            return EXIT_USAGE
        data = dashboard_data(db_path)
        if json_output or output_format == "json":
            emit_json(data)
        elif output_format == "mermaid":
            print(data["mermaid"])
        else:
            print(_render_dashboard_text(data))
        if fail_under is not None and data["counts"].get("passed", 0) < fail_under:
            return 1
        return 0

    print(f"未知の detector subcommand: {command}", file=sys.stderr)
    print(_usage(), file=sys.stderr)
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
