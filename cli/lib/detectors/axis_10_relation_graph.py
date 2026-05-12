from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult

try:
    from ..extractors.bash_trace import MAIN_FUNCTION, scan_helix_bash_scripts  # type: ignore
    from ..extractors.hook_config import extract_hook_configs  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script execution
    from extractors.bash_trace import MAIN_FUNCTION, scan_helix_bash_scripts  # type: ignore
    from extractors.hook_config import extract_hook_configs  # type: ignore


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [{key: row[key] for key in row.keys()} for row in conn.execute(query, params).fetchall()]


def _load_latest_detector_runs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "detector_runs"):
        return []
    axis_ids = tuple(f"axis-{index:02d}" for index in range(1, 15))
    placeholders = ", ".join("?" for _ in axis_ids)
    rows = _rows(
        conn,
        f"""
        SELECT run_id, axis_id, detector_name, verdict, findings_json, raw_json
        FROM detector_runs
        WHERE axis_id IN ({placeholders})
        ORDER BY axis_id, run_id DESC
        """,
        axis_ids,
    )
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        axis_id = str(row.get("axis_id") or "")
        if axis_id and axis_id not in latest:
            latest[axis_id] = row
    return [latest[axis_id] for axis_id in sorted(latest)]


def _load_code_edges(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "code_edges"):
        return []
    return _rows(conn, "SELECT * FROM code_edges ORDER BY id")


def _load_contract_entries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_exists(conn, "contract_entries"):
        return []
    return _rows(
        conn,
        """
        SELECT id, source_path, symbol_id, contract_type, version
        FROM contract_entries
        ORDER BY id
        """,
    )


def _decode_raw_meta(raw_meta: Any) -> dict[str, Any]:
    if not isinstance(raw_meta, str) or not raw_meta.strip():
        return {}
    try:
        parsed = json.loads(raw_meta)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _escape_label(text: str) -> str:
    return text.replace('"', "'")


class _GraphBuilder:
    def __init__(self) -> None:
        self._node_ids: dict[tuple[Any, ...], str] = {}
        self._node_lines: list[str] = []
        self._edge_lines: list[str] = []
        self._edges_seen: set[tuple[str, str, str]] = set()

    def node(self, key: tuple[Any, ...], label: str) -> str:
        if key in self._node_ids:
            return self._node_ids[key]
        node_id = f"n{len(self._node_ids) + 1}"
        self._node_ids[key] = node_id
        self._node_lines.append(f'  {node_id}["{_escape_label(label)}"]')
        return node_id

    def edge(self, source: str, target: str, label: str = "") -> None:
        key = (source, target, label)
        if key in self._edges_seen:
            return
        self._edges_seen.add(key)
        if label:
            self._edge_lines.append(f'  {source} -->|"{_escape_label(label)}"| {target}')
        else:
            self._edge_lines.append(f"  {source} --> {target}")

    @property
    def node_count(self) -> int:
        return len(self._node_ids)

    @property
    def edge_count(self) -> int:
        return len(self._edges_seen)

    def render(self) -> str:
        return "\n".join(["graph LR", *self._node_lines, *self._edge_lines])


class Axis10RelationGraph(BaseDetector):
    id = "axis-10"
    name = "relation graph"
    phase_gate = None
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        target_db = Path(db_path)
        helix_db._prepare_db_path(str(target_db))
        root = _project_root(db_path)
        conn = helix_db.get_connection(target_db)

        try:
            detector_runs = _load_latest_detector_runs(conn)
            code_edges = _load_code_edges(conn)
            contract_entries = _load_contract_entries(conn)
        finally:
            conn.close()

        bash_traces = scan_helix_bash_scripts(root)
        hook_configs = extract_hook_configs(root)

        graph = _GraphBuilder()
        root_node = graph.node(("hub", "root"), "axis-10 relation graph")
        detector_hub = graph.node(("hub", "detectors"), "detector runs")
        code_hub = graph.node(("hub", "code"), "code edges")
        contract_hub = graph.node(("hub", "contracts"), "contract entries")
        bash_hub = graph.node(("hub", "bash"), "bash trace")
        hook_hub = graph.node(("hub", "hooks"), "hook config")

        for hub in (detector_hub, code_hub, contract_hub, bash_hub, hook_hub):
            graph.edge(root_node, hub)

        for row in detector_runs:
            axis_id = str(row.get("axis_id") or "")
            verdict = str(row.get("verdict") or "unknown")
            name = str(row.get("detector_name") or axis_id)
            node = graph.node(("detector", axis_id), f"{axis_id}<br/>{name}<br/>{verdict}")
            graph.edge(detector_hub, node, "latest")

        for row in code_edges:
            meta = _decode_raw_meta(row.get("raw_meta"))
            caller_label = str(meta.get("source_path") or f"entry:{row.get('from_entry_id')}")
            if row.get("source_line"):
                caller_label = f"{caller_label}:{row['source_line']}"
            callee_label = str(row.get("to_external_ref") or f"entry:{row.get('to_entry_id')}")
            caller = graph.node(("code", "caller", caller_label), caller_label)
            callee = graph.node(("code", "callee", callee_label), callee_label)
            graph.edge(code_hub, caller)
            graph.edge(caller, callee, str(row.get("edge_type") or "call"))

        for row in contract_entries:
            source_path = str(row.get("source_path") or f"contract:{row.get('id')}")
            symbol_id = str(row.get("symbol_id") or source_path)
            label = f"{source_path}<br/>{symbol_id}"
            node = graph.node(("contract", row.get("id"), symbol_id), label)
            graph.edge(contract_hub, node, str(row.get("contract_type") or "contract"))

        bash_index = {
            (str(row.get("script") or ""), str(row.get("function") or "")): row for row in bash_traces
        }
        for row in bash_traces:
            script = str(row.get("script") or "")
            function_name = str(row.get("function") or MAIN_FUNCTION)
            script_node = graph.node(("bash-script", script), script)
            graph.edge(bash_hub, script_node)
            if function_name != MAIN_FUNCTION:
                function_node = graph.node(("bash-fn", script, function_name), f"{script}<br/>{function_name}()")
                graph.edge(script_node, function_node, "defines")
            else:
                function_node = script_node

            callees = row.get("callees")
            if not isinstance(callees, list):
                continue
            for callee in callees:
                if not isinstance(callee, str):
                    continue
                if callee.startswith("source:"):
                    target_label = callee.split(":", 1)[1]
                    target_node = graph.node(("bash-source", target_label), target_label)
                    graph.edge(function_node, target_node, "source")
                    continue
                if (script, callee) in bash_index:
                    target_node = graph.node(("bash-fn", script, callee), f"{script}<br/>{callee}()")
                else:
                    target_node = graph.node(("bash-call", script, callee), callee)
                graph.edge(function_node, target_node, "calls")

        for row in hook_configs:
            hook_event = str(row.get("hook_event") or "")
            matcher = str(row.get("matcher") or "*")
            command = str(row.get("command") or "")
            script_path = str(row.get("script_path") or command)
            hook_node = graph.node(("hook", hook_event, matcher, command), f"{hook_event}<br/>{matcher}")
            target_node = graph.node(("hook-script", script_path), script_path)
            graph.edge(hook_hub, hook_node)
            graph.edge(hook_node, target_node, "command")

        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict="passed",
            findings=[],
            cost_ms=cost_ms,
            raw={
                "mermaid": graph.render(),
                "node_count": graph.node_count,
                "edge_count": graph.edge_count,
                "detector_count": len(detector_runs),
                "code_edge_count": len(code_edges),
                "contract_count": len(contract_entries),
                "bash_trace_count": len(bash_traces),
                "hook_count": len(hook_configs),
                "project_root": str(root),
            },
        )
