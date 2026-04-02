from __future__ import annotations

import json
import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_CONTEXT_PATH_RE = re.compile(r"^[A-Za-z0-9_./{}*?-]+$")
_ALLOWED_EXECUTION = {"helix-codex", "claude-agent"}
_REQUIRED_FIELDS = {"name", "role", "task_template", "context_files", "output_contract", "execution"}


class SubAgentBuilder(BuilderBase):
    BUILDER_TYPE = "sub-agent"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["name", "role", "task_template", "context_files", "output_contract", "execution"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        role = str(params.get("role", "")).strip()
        task_template = str(params.get("task_template", "")).strip()
        context_files = params.get("context_files")
        output_contract = params.get("output_contract")
        execution = str(params.get("execution", "")).strip()

        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
        if not role:
            raise ValueError("role is required")
        if not task_template:
            raise ValueError("task_template is required")
        if not isinstance(context_files, list) or not context_files:
            raise ValueError("context_files must be a non-empty array")
        if not isinstance(output_contract, dict) or not output_contract:
            raise ValueError("output_contract must be a non-empty object")
        if execution not in _ALLOWED_EXECUTION:
            raise ValueError(f"execution must be one of {sorted(_ALLOWED_EXECUTION)}")

        normalized_context_files: list[str] = []
        for index, pattern in enumerate(context_files, start=1):
            path_pattern = str(pattern).strip()
            if not path_pattern:
                raise ValueError(f"context_files[{index}] is empty")
            _validate_context_path_pattern(path_pattern)
            normalized_context_files.append(path_pattern)

        return {
            "name": name,
            "role": role,
            "task_template": task_template,
            "context_files": normalized_context_files,
            "output_contract": output_contract,
            "execution": execution,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        output_dir = Path(self.project_root) / "builders" / "sub-agents"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{params['name']}.json"
        payload = {
            "name": params["name"],
            "builder_type": self.BUILDER_TYPE,
            "role": params["role"],
            "task_template": params["task_template"],
            "context_files": params["context_files"],
            "output_contract": params["output_contract"],
            "execution": params["execution"],
            "execution_template": _build_execution_template(params),
        }

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return [{"path": str(output_path.relative_to(self.project_root)), "kind": "sub-agent-definition"}]

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if len(paths) != 1:
            raise ValueError("sub-agent expects one artifact")

        output_path = paths[0]
        if not output_path.exists():
            raise ValueError(f"artifact not found: {output_path}")

        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}")

        if not isinstance(payload, dict):
            raise ValueError("sub-agent definition must be an object")

        missing = sorted(_REQUIRED_FIELDS - set(payload.keys()))
        if missing:
            raise ValueError(f"missing required fields: {missing}")

        if payload.get("execution") not in _ALLOWED_EXECUTION:
            raise ValueError(f"execution must be one of {sorted(_ALLOWED_EXECUTION)}")

        for pattern in payload.get("context_files", []):
            _validate_context_path_pattern(str(pattern))

        return {
            "valid": True,
            "checked_files": [str(output_path)],
            "quality_score": 100,
        }


def _validate_context_path_pattern(path_pattern: str):
    if Path(path_pattern).is_absolute():
        raise ValueError(f"context_files must be relative path patterns: {path_pattern}")
    if ".." in path_pattern:
        raise ValueError(f"context_files must not include '..': {path_pattern}")
    if not _CONTEXT_PATH_RE.match(path_pattern):
        raise ValueError(f"invalid context_files path pattern: {path_pattern}")


def _build_execution_template(params: dict) -> dict:
    execution = params["execution"]
    role = params["role"]
    task_template = params["task_template"]

    if execution == "helix-codex":
        return {
            "tool": "helix-codex",
            "command": f"helix codex --role {role} --task {task_template!r}",
            "notes": "task_template のプレースホルダは実行時に埋める",
        }

    return {
        "tool": "claude-agent",
        "task_tool": {
            "model": "sonnet",
            "prompt_template": task_template,
            "context_files": params["context_files"],
        },
        "notes": "Task tool へ prompt と context を渡す",
    }


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(SubAgentBuilder)
