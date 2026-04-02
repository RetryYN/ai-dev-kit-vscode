from __future__ import annotations

import json
import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_ALLOWED_STOP_TYPES = {"verdict", "count", "file_exists", "custom"}
_ALLOWED_FAILURE = {"escalate", "retry", "abort"}
_REQUIRED_FIELDS = {"name", "role", "task_template", "stop_condition", "max_iterations", "on_failure"}


class AgentLoopBuilder(BuilderBase):
    BUILDER_TYPE = "agent-loop"

    INPUT_SCHEMA = {
        "type": "object",
        "required": [
            "name",
            "role",
            "task_template",
            "stop_condition",
            "max_iterations",
            "on_failure",
        ],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        role = str(params.get("role", "")).strip()
        task_template = str(params.get("task_template", "")).strip()
        stop_condition = params.get("stop_condition")
        on_failure = str(params.get("on_failure", "")).strip()

        try:
            max_iterations = int(params.get("max_iterations"))
        except (TypeError, ValueError):
            raise ValueError("max_iterations must be an integer")

        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
        if not role:
            raise ValueError("role is required")
        if not task_template:
            raise ValueError("task_template is required")
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if on_failure not in _ALLOWED_FAILURE:
            raise ValueError(f"on_failure must be one of {sorted(_ALLOWED_FAILURE)}")

        normalized_stop = _validate_stop_condition(stop_condition)

        return {
            "name": name,
            "role": role,
            "task_template": task_template,
            "stop_condition": normalized_stop,
            "max_iterations": max_iterations,
            "on_failure": on_failure,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        loops_dir = Path(self.project_root) / "builders" / "loops"
        loops_dir.mkdir(parents=True, exist_ok=True)

        output_path = loops_dir / f"{params['name']}.json"
        payload = {
            "name": params["name"],
            "builder_type": self.BUILDER_TYPE,
            "role": params["role"],
            "task_template": params["task_template"],
            "stop_condition": params["stop_condition"],
            "max_iterations": params["max_iterations"],
            "on_failure": params["on_failure"],
        }

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        return [{"path": str(output_path.relative_to(self.project_root)), "kind": "loop-definition"}]

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if len(paths) != 1:
            raise ValueError("agent-loop expects one artifact")

        output_path = paths[0]
        if not output_path.exists():
            raise ValueError(f"artifact not found: {output_path}")

        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}")

        if not isinstance(payload, dict):
            raise ValueError("loop definition must be an object")

        missing = sorted(_REQUIRED_FIELDS - set(payload.keys()))
        if missing:
            raise ValueError(f"missing required fields: {missing}")

        _validate_stop_condition(payload.get("stop_condition"))

        return {
            "valid": True,
            "checked_files": [str(output_path)],
            "quality_score": 100,
        }


def _validate_stop_condition(stop_condition: object) -> dict:
    if not isinstance(stop_condition, dict):
        raise ValueError("stop_condition must be an object")

    stop_type = str(stop_condition.get("type", "")).strip()
    if stop_type not in _ALLOWED_STOP_TYPES:
        raise ValueError(f"stop_condition.type must be one of {sorted(_ALLOWED_STOP_TYPES)}")

    value = stop_condition.get("value")

    if stop_type == "count":
        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValueError("stop_condition.value must be an integer when type=count")
        if value < 1:
            raise ValueError("stop_condition.value must be >= 1 when type=count")
    elif stop_type in {"verdict", "file_exists", "custom"}:
        if value is None:
            raise ValueError(f"stop_condition.value is required when type={stop_type}")

    return {"type": stop_type, "value": value}


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(AgentLoopBuilder)
