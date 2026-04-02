from __future__ import annotations

import json
import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_ALLOWED_FAILURE_POLICY = {"stop_on_first", "continue_all", "escalate"}


class WorkflowBuilder(BuilderBase):
    BUILDER_TYPE = "workflow"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["name", "nodes", "edges", "failure_policy"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        nodes = params.get("nodes")
        edges = params.get("edges")
        failure_policy = str(params.get("failure_policy", "")).strip()

        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("nodes must be a non-empty array")
        if not isinstance(edges, list):
            raise ValueError("edges must be an array")
        if failure_policy not in _ALLOWED_FAILURE_POLICY:
            raise ValueError(f"failure_policy must be one of {sorted(_ALLOWED_FAILURE_POLICY)}")

        normalized_nodes: list[dict] = []
        node_ids: set[str] = set()
        for index, node in enumerate(nodes, start=1):
            if not isinstance(node, dict):
                raise ValueError(f"nodes[{index}] must be an object")
            node_id = str(node.get("id", "")).strip()
            builder = str(node.get("builder", "")).strip()
            if not node_id:
                raise ValueError(f"nodes[{index}].id is required")
            if node_id in node_ids:
                raise ValueError(f"duplicate node id: {node_id}")
            if not builder:
                raise ValueError(f"nodes[{index}].builder is required")
            node_ids.add(node_id)
            normalized_nodes.append(dict(node))

        normalized_edges: list[dict] = []
        for index, edge in enumerate(edges, start=1):
            if not isinstance(edge, dict):
                raise ValueError(f"edges[{index}] must be an object")
            from_node = str(edge.get("from", "")).strip()
            to_node = str(edge.get("to", "")).strip()
            condition = str(edge.get("condition", "success")).strip() or "success"
            if not from_node or not to_node:
                raise ValueError(f"edges[{index}] requires from/to")
            if from_node not in node_ids:
                raise ValueError(f"edges[{index}].from references unknown node: {from_node}")
            if to_node not in node_ids:
                raise ValueError(f"edges[{index}].to references unknown node: {to_node}")
            normalized_edges.append({"from": from_node, "to": to_node, "condition": condition})

        cycle = _find_cycle(node_ids=node_ids, edges=normalized_edges)
        if cycle:
            raise ValueError(f"workflow has cycle: {' -> '.join(cycle)}")

        return {
            "name": name,
            "nodes": normalized_nodes,
            "edges": normalized_edges,
            "failure_policy": failure_policy,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        workflows_dir = Path(self.project_root) / "builders" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        output_path = workflows_dir / f"{params['name']}.json"
        payload = {
            "name": params["name"],
            "builder_type": self.BUILDER_TYPE,
            "nodes": params["nodes"],
            "edges": params["edges"],
            "failure_policy": params["failure_policy"],
        }

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return [{"path": str(output_path.relative_to(self.project_root)), "kind": "workflow-definition"}]

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if len(paths) != 1:
            raise ValueError("workflow builder expects one artifact")

        output_path = paths[0]
        if not output_path.exists():
            raise ValueError(f"artifact not found: {output_path}")

        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}")

        if not isinstance(payload, dict):
            raise ValueError("workflow definition must be an object")

        nodes = payload.get("nodes")
        edges = payload.get("edges")
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("workflow definition requires nodes/edges arrays")

        node_ids = {str(node.get("id")) for node in nodes if isinstance(node, dict) and node.get("id")}
        if not node_ids:
            raise ValueError("workflow definition has no valid nodes")

        cycle = _find_cycle(node_ids=node_ids, edges=[edge for edge in edges if isinstance(edge, dict)])
        if cycle:
            raise ValueError(f"workflow has cycle: {' -> '.join(cycle)}")

        return {
            "valid": True,
            "checked_files": [str(output_path)],
            "quality_score": 100,
        }


def _find_cycle(node_ids: set[str], edges: list[dict]) -> list[str]:
    graph: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        from_node = str(edge.get("from", "")).strip()
        to_node = str(edge.get("to", "")).strip()
        if from_node in graph and to_node in graph:
            graph[from_node].append(to_node)

    color = {node_id: 0 for node_id in node_ids}  # 0=unvisited, 1=visiting, 2=done
    parent: dict[str, str | None] = {node_id: None for node_id in node_ids}

    def dfs(node: str) -> list[str]:
        color[node] = 1
        for nxt in graph[node]:
            if color[nxt] == 0:
                parent[nxt] = node
                cycle = dfs(nxt)
                if cycle:
                    return cycle
            elif color[nxt] == 1:
                path = [nxt]
                cur = node
                while cur != nxt and cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.append(nxt)
                path.reverse()
                return path
        color[node] = 2
        return []

    for node in sorted(node_ids):
        if color[node] == 0:
            found = dfs(node)
            if found:
                return found
    return []


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(WorkflowBuilder)
