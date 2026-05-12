from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
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
from detectors.axis_03_dup import Axis03RealDuplicate  # noqa: E402
from detectors.axis_04_skill_decay import Axis04SkillDecay  # noqa: E402
from detectors.axis_05_plan_debt import Axis05PlanDebtLoop  # noqa: E402
from detectors.axis_07_doc_drift import Axis07DocDrift  # noqa: E402
from detectors.axis_08_plan_integrity import Axis08PlanIntegrity  # noqa: E402
from detectors.axis_06_naming import Axis06NamingConfusion  # noqa: E402
from detectors.axis_09_refactor import Axis09RefactorOpportunity  # noqa: E402
from detectors.axis_10_relation_graph import Axis10RelationGraph  # noqa: E402
from detectors.axis_11_regression import Axis11RegressionDetection  # noqa: E402
from detectors.axis_12_connection import Axis12ConnectionDeficiency  # noqa: E402
from detectors.axis_13_model_skill import Axis13ModelSkillAnalytics  # noqa: E402
from detectors.axis_14_orchestration import Axis14OrchestrationIntegrity  # noqa: E402
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


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _existing_table(conn: sqlite3.Connection, names: Iterable[str]) -> str | None:
    for table_name in names:
        if _table_exists(conn, table_name):
            return table_name
    return None


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"] if row is not None else 0)


def _parse_iso_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _verdict_color(verdict: str) -> str:
    return {
        "passed": "green",
        "failed": "red",
        "blocked": "gray",
    }.get(verdict, "gray")


def _format_percent(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _fetch_detector_run_rows(conn: sqlite3.Connection, limit: int = 14) -> list[dict[str, Any]]:
    if not _table_exists(conn, "detector_runs"):
        return []
    rows = conn.execute(
        """
        SELECT run_id, recorded_at, axis_id, detector_name, phase_gate, verdict,
               findings_json, cost_ms, raw_json, config_json, command, db_path
        FROM detector_runs
        WHERE axis_id != 'axis-00'
        ORDER BY recorded_at DESC, run_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        findings_json = str(row["findings_json"] or "[]")
        try:
            findings = json.loads(findings_json)
        except Exception:
            findings = []
        items.append(
            {
                "run_id": int(row["run_id"]),
                "recorded_at": str(row["recorded_at"] or ""),
                "axis_id": str(row["axis_id"] or ""),
                "detector_name": str(row["detector_name"] or ""),
                "phase_gate": str(row["phase_gate"] or "") or None,
                "verdict": str(row["verdict"] or ""),
                "verdict_color": _verdict_color(str(row["verdict"] or "")),
                "findings_count": len(findings) if isinstance(findings, list) else 0,
                "cost_ms": int(row["cost_ms"] or 0),
                "command": str(row["command"] or ""),
            }
        )
    return items


def _aggregate_invocation_log(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "invocation_log"):
        return {"window_hours": 1, "total": 0, "by_role": [], "by_model": []}

    threshold = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    rows = conn.execute(
        """
        SELECT role, model, timestamp
        FROM invocation_log
        WHERE timestamp >= ?
        ORDER BY timestamp DESC, id DESC
        """,
        (threshold,),
    ).fetchall()
    role_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    for row in rows:
        role = str(row["role"] or "").strip() or "-"
        model = str(row["model"] or "").strip() or "-"
        role_counts[role] += 1
        model_counts[model] += 1

    def _items(counter: Counter[str]) -> list[dict[str, Any]]:
        return [
            {"label": label, "count": count}
            for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:5]
        ]

    return {
        "window_hours": 1,
        "total": len(rows),
        "by_role": _items(role_counts),
        "by_model": _items(model_counts),
    }


def _aggregate_code_entries(conn: sqlite3.Connection) -> dict[str, Any]:
    table_name = _existing_table(conn, ("code_entries", "code_index"))
    if table_name is None:
        return {
            "source_table": None,
            "total": 0,
            "coverage_eligible": 0,
            "uncovered_pct": 0.0,
        }

    total = _count_rows(conn, table_name)
    columns = _table_columns(conn, table_name)
    eligible = total
    if "bucket" in columns:
        row = conn.execute(
            f"SELECT COUNT(*) AS count FROM {table_name} WHERE bucket = ?",
            ("coverage_eligible",),
        ).fetchone()
        eligible = int(row["count"] if row is not None else 0)

    uncovered_pct = 0.0
    if total > 0:
        uncovered_pct = round(((total - eligible) / total) * 100.0, 1)

    return {
        "source_table": table_name,
        "total": total,
        "coverage_eligible": eligible,
        "uncovered_pct": uncovered_pct,
    }


def _aggregate_observe_tables(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'observe_%'
        ORDER BY name
        """
    ).fetchall()
    tables: list[dict[str, Any]] = []
    for row in rows:
        table_name = str(row["name"])
        columns = _table_columns(conn, table_name)
        summary: dict[str, Any] = {
            "table": table_name,
            "rows": _count_rows(conn, table_name),
        }
        latest = conn.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 1").fetchone()
        if latest is not None:
            if "accuracy_score" in columns:
                summary["accuracy_score"] = latest["accuracy_score"]
            elif "score" in columns:
                summary["score"] = latest["score"]
            if "verdict" in columns:
                summary["verdict"] = latest["verdict"]
        tables.append(summary)
    return {"tables": tables}


def _aggregate_skill_usage(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "skill_usage"):
        return {"window_days": 7, "top": []}

    threshold = datetime.now(timezone.utc) - timedelta(days=7)
    rows = conn.execute(
        """
        SELECT skill_id, created_at, completed_at
        FROM skill_usage
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()
    counts: Counter[str] = Counter()
    for row in rows:
        created_at = _parse_iso_datetime(row["created_at"]) or _parse_iso_datetime(row["completed_at"])
        if created_at is None or created_at < threshold:
            continue
        skill_id = str(row["skill_id"] or "").strip() or "-"
        counts[skill_id] += 1
    top = [
        {"skill_id": skill_id, "count": count}
        for skill_id, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]
    return {"window_days": 7, "top": top}


def _aggregate_routing_decisions(conn: sqlite3.Connection) -> dict[str, Any]:
    if not _table_exists(conn, "routing_decisions"):
        return {"total": 0, "carry": 0, "debt": 0, "other": 0}

    rows = conn.execute("SELECT * FROM routing_decisions ORDER BY rowid DESC").fetchall()
    carry = debt = other = 0
    for row in rows:
        values = [
            str(row[key] or "")
            for key in row.keys()
            if key in {"decision", "detail", "source", "path", "title", "kind", "status", "comment"}
        ]
        blob = " ".join(values).lower()
        if "carry" in blob:
            carry += 1
        elif "debt" in blob:
            debt += 1
        else:
            other += 1
    return {"total": len(rows), "carry": carry, "debt": debt, "other": other}


def _render_detector_runs_text(items: list[dict[str, Any]]) -> list[str]:
    lines = ["detector_runs (latest 14)"]
    if not items:
        lines.append("  - none")
        return lines
    for item in items:
        lines.append(
            f"  - {item['axis_id']} [{item['verdict']}] {item['detector_name']} "
            f"findings={item['findings_count']} cost_ms={item['cost_ms']}"
        )
    return lines


def _render_table_list_text(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [title]
    if not items:
        lines.append("  - none")
        return lines
    for item in items:
        parts = [f"{key}={value}" for key, value in item.items()]
        lines.append("  - " + " ".join(parts))
    return lines




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

    conn = helix_db.get_connection(target_db)
    try:
        detector_runs = _fetch_detector_run_rows(conn, limit=14)
        invocation_log = _aggregate_invocation_log(conn)
        code_entries = _aggregate_code_entries(conn)
        observe_tables = _aggregate_observe_tables(conn)
        skill_usage = _aggregate_skill_usage(conn)
        routing_decisions = _aggregate_routing_decisions(conn)
    finally:
        conn.close()

    mermaid = _render_mermaid(axes, counts, detector_runs, invocation_log, code_entries, observe_tables, skill_usage, routing_decisions)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(axes),
        "counts": counts,
        "passed_axes": [item["axis_id"] for item in axes if item["verdict"] == "passed"],
        "blocked_axes": [item["axis_id"] for item in axes if item["verdict"] == "blocked"],
        "axes": axes,
        "detector_runs": detector_runs,
        "invocation_log": invocation_log,
        "code_entries": code_entries,
        "observe_tables": observe_tables,
        "skill_usage": skill_usage,
        "routing_decisions": routing_decisions,
        "mermaid": mermaid,
    }


def _verdict_color(verdict: str) -> str:
    return {
        "passed": "fill:#d1fae5,stroke:#059669,color:#064e3b",
        "failed": "fill:#fee2e2,stroke:#dc2626,color:#7f1d1d",
        "blocked": "fill:#e5e7eb,stroke:#6b7280,color:#111827",
    }.get(verdict, "fill:#e5e7eb,stroke:#6b7280,color:#111827")


def _render_mermaid(
    axes: Iterable[dict[str, Any]],
    counts: dict[str, int],
    detector_runs: list[dict[str, Any]],
    invocation_log: dict[str, Any],
    code_entries: dict[str, Any],
    observe_tables: dict[str, Any],
    skill_usage: dict[str, Any],
    routing_decisions: dict[str, Any],
) -> str:
    lines = ["graph TD", "  %% PLAN-063 detector dashboard"]

    summary = "  summary[[passed={passed} blocked={blocked} failed={failed}]]".format(
        passed=counts.get("passed", 0),
        blocked=counts.get("blocked", 0),
        failed=counts.get("failed", 0),
    )
    lines.append(summary)

    section_nodes = {
        "detector_runs": f"detector_runs[[detector_runs<br/>latest={len(detector_runs)}]]",
        "invocation_log": f"invocation_log[[invocation_log<br/>1h={invocation_log.get('total', 0)}]]",
        "code_entries": (
            "code_entries[[code_entries<br/>coverage_eligible={coverage}<br/>uncovered%={percent}]]".format(
                coverage=code_entries.get("coverage_eligible", 0),
                percent=_format_percent(float(code_entries.get("uncovered_pct", 0.0))),
            )
        ),
        "observe_tables": f"observe_tables[[observe_*<br/>tables={len(observe_tables.get('tables', []))}]]",
        "skill_usage": f"skill_usage[[skill_usage<br/>top={len(skill_usage.get('top', []))}]]",
        "routing_decisions": (
            "routing_decisions[[routing_decisions<br/>carry={carry}<br/>debt={debt}]]".format(
                carry=routing_decisions.get("carry", 0),
                debt=routing_decisions.get("debt", 0),
            )
        ),
    }
    for node in section_nodes.values():
        lines.append(f"  {node}")
    for section_name in section_nodes:
        lines.append(f"  summary --> {section_name}")

    for item in axes:
        axis_id = item["axis_id"]
        label = f"{axis_id}<br/>{item['name']}<br/>{item['verdict']}"
        node_name = axis_id.replace("-", "_")
        lines.append(f'  {node_name}["{label}"]')
        lines.append(f"  style {node_name} {_verdict_color(item['verdict'])}")
        lines.append(f"  summary --> {node_name}")

    for run in detector_runs:
        node_name = f"run_{run['run_id']}"
        label = (
            f"{run['axis_id']}<br/>{run['verdict']}<br/>{run['detector_name']}<br/>"
            f"findings={run['findings_count']}"
        )
        lines.append(f'  {node_name}["{label}"]')
        lines.append(f"  style {node_name} {_verdict_color(run['verdict'])}")
        lines.append(f"  detector_runs --> {node_name}")

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
        f"generated_at={data['generated_at']}",
        f"detectors total={data['total']} passed={data['counts']['passed']} failed={data['counts']['failed']} blocked={data['counts']['blocked']}",
        "",
    ]
    lines.append("detectors (latest verdicts)")
    for item in data["axes"]:
        gate = item["phase_gate"] or "-"
        lines.append(f"  - {item['axis_id']}\t{item['name']}\t{gate}\t{item['verdict']}")
    lines.append("")
    lines.extend(_render_detector_runs_text(data.get("detector_runs", [])))
    lines.append("")
    lines.append(
        "invocation_log (last 1h) total={total}".format(total=data["invocation_log"].get("total", 0))
    )
    for item in data["invocation_log"].get("by_role", []):
        lines.append(f"  role {item['label']}={item['count']}")
    for item in data["invocation_log"].get("by_model", []):
        lines.append(f"  model {item['label']}={item['count']}")
    lines.append("")
    code_entries = data["code_entries"]
    lines.append(
        "code_entries source={source} coverage_eligible={eligible} uncovered%={percent}".format(
            source=code_entries.get("source_table") or "-",
            eligible=code_entries.get("coverage_eligible", 0),
            percent=_format_percent(float(code_entries.get("uncovered_pct", 0.0))),
        )
    )
    lines.append("")
    lines.append("observe_*")
    observe_tables = data.get("observe_tables", {}).get("tables", [])
    if observe_tables:
        for item in observe_tables:
            extras = [f"rows={item['rows']}"]
            if "accuracy_score" in item:
                extras.append(f"accuracy_score={item['accuracy_score']}")
            if "score" in item:
                extras.append(f"score={item['score']}")
            if "verdict" in item:
                extras.append(f"verdict={item['verdict']}")
            lines.append(f"  - {item['table']} " + " ".join(extras))
    else:
        lines.append("  - none")
    lines.append("")
    lines.append("skill_usage (last 7d top 5)")
    if data.get("skill_usage", {}).get("top"):
        for item in data["skill_usage"]["top"]:
            lines.append(f"  - {item['skill_id']}={item['count']}")
    else:
        lines.append("  - none")
    lines.append("")
    routing = data.get("routing_decisions", {})
    lines.append(
        "routing_decisions carry={carry} debt={debt} total={total}".format(
            carry=routing.get("carry", 0),
            debt=routing.get("debt", 0),
            total=routing.get("total", 0),
        )
    )
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
        "  --format text|mermaid|json   dashboard の表示形式\n"
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
