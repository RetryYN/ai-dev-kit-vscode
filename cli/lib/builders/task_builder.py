from __future__ import annotations

import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_TASK_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*$")
_TOP_LEVEL_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+:\s*$")


class TaskBuilder(BuilderBase):
    BUILDER_TYPE = "task"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["category", "task_id", "name", "role", "estimate", "skill", "actions"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        category = str(params.get("category", "")).strip()
        task_id = str(params.get("task_id", "")).strip()
        name = str(params.get("name", "")).strip()
        role = str(params.get("role", "")).strip()
        skill = str(params.get("skill", "")).strip()
        actions = params.get("actions")

        try:
            estimate = int(params.get("estimate"))
        except (TypeError, ValueError):
            raise ValueError("estimate must be an integer")

        if not category or not _CATEGORY_RE.match(category):
            raise ValueError("category must match ^[a-z0-9][a-z0-9-]*$")
        if not task_id or not _TASK_ID_RE.match(task_id):
            raise ValueError("task_id must match ^[a-zA-Z0-9][a-zA-Z0-9-]*$")
        if not name:
            raise ValueError("name is required")
        if not role:
            raise ValueError("role is required")
        if estimate < 1:
            raise ValueError("estimate must be >= 1")
        if not skill:
            raise ValueError("skill is required")
        if not isinstance(actions, list) or not actions:
            raise ValueError("actions must be a non-empty array")

        normalized_actions: list[dict] = []
        for index, action in enumerate(actions, start=1):
            if not isinstance(action, dict):
                raise ValueError(f"actions[{index}] must be an object")
            action_type = str(action.get("type", "")).strip()
            desc = str(action.get("desc", "")).strip()
            if not action_type:
                raise ValueError(f"actions[{index}].type is required")
            if not desc:
                raise ValueError(f"actions[{index}].desc is required")
            normalized_actions.append({"type": action_type, "desc": desc})

        return {
            "category": category,
            "task_id": task_id,
            "name": name,
            "role": role,
            "estimate": estimate,
            "skill": skill,
            "actions": normalized_actions,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        overlay_path = Path(self.project_root) / ".helix" / "task-catalog.yaml"
        overlay_path.parent.mkdir(parents=True, exist_ok=True)

        task_id = params["task_id"]
        _ensure_task_not_exists(task_id, overlay_path)

        if overlay_path.exists():
            content = overlay_path.read_text(encoding="utf-8")
        else:
            content = "# task-catalog overlay (project-local)\n"

        updated = _append_task_entry(content, params)
        overlay_path.write_text(updated, encoding="utf-8")

        return [
            {
                "path": str(overlay_path.relative_to(self.project_root)),
                "kind": "task-catalog-overlay",
                "category": params["category"],
                "task_id": params["task_id"],
            }
        ]

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if len(paths) != 1:
            raise ValueError("task builder expects one artifact")

        catalog_path = paths[0]
        if not catalog_path.exists():
            raise ValueError(f"artifact not found: {catalog_path}")

        content = catalog_path.read_text(encoding="utf-8")
        artifact = artifacts[0] if artifacts else {}
        category = str(artifact.get("category", "")).strip()
        task_id = str(artifact.get("task_id", "")).strip()
        if not category or not task_id:
            raise ValueError("artifact must include category and task_id")

        _validate_task_entry(content=content, category=category, task_id=task_id)

        return {
            "valid": True,
            "checked_files": [str(catalog_path)],
            "quality_score": 100,
        }


def _ensure_task_not_exists(task_id: str, overlay_path: Path):
    task_line = f"  {task_id}:"

    if overlay_path.exists():
        overlay_content = overlay_path.read_text(encoding="utf-8")
        if task_line in overlay_content:
            raise ValueError(f"task_id already exists in overlay: {task_id}")

    shared_catalog = Path(__file__).resolve().parents[2] / "templates" / "task-catalog.yaml"
    if shared_catalog.exists():
        shared_content = shared_catalog.read_text(encoding="utf-8")
        if task_line in shared_content:
            raise ValueError(f"task_id already exists in shared catalog: {task_id}")


def _append_task_entry(content: str, params: dict) -> str:
    category = params["category"]
    task_block = _build_task_block(params)

    if not content.endswith("\n"):
        content += "\n"

    lines = content.splitlines()

    category_index = _find_category_index(lines, category)
    if category_index is None:
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"{category}:")
        lines.extend(task_block)
        return "\n".join(lines) + "\n"

    insert_at = _category_insert_index(lines, category_index)
    for offset, line in enumerate(task_block):
        lines.insert(insert_at + offset, line)
    return "\n".join(lines) + "\n"


def _build_task_block(params: dict) -> list[str]:
    lines = [
        f"  {params['task_id']}:",
        f"    name: \"{_yaml_escape(params['name'])}\"",
        f"    role: {params['role']}",
        f"    estimate: {int(params['estimate'])}",
        f"    skill: {params['skill']}",
        "    actions:",
    ]

    for action in params["actions"]:
        action_type = _yaml_escape(action["type"])
        desc = _yaml_escape(action["desc"])
        lines.append(f"      - {{ type: {action_type}, desc: \"{desc}\" }}")

    return lines


def _yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _find_category_index(lines: list[str], category: str) -> int | None:
    target = f"{category}:"
    for index, line in enumerate(lines):
        if line == target:
            return index
    return None


def _category_insert_index(lines: list[str], category_index: int) -> int:
    index = category_index + 1
    while index < len(lines):
        if _TOP_LEVEL_KEY_RE.match(lines[index]):
            break
        index += 1
    return index


def _validate_task_entry(content: str, category: str, task_id: str):
    lines = content.splitlines()
    category_line = f"{category}:"
    task_line = f"  {task_id}:"

    category_start = None
    for index, line in enumerate(lines):
        if line == category_line:
            category_start = index
            break
    if category_start is None:
        raise ValueError(f"category not found: {category}")

    category_end = len(lines)
    for index in range(category_start + 1, len(lines)):
        if _TOP_LEVEL_KEY_RE.match(lines[index]):
            category_end = index
            break

    task_start = None
    for index in range(category_start + 1, category_end):
        if lines[index] == task_line:
            task_start = index
            break
    if task_start is None:
        raise ValueError(f"task not found in category {category}: {task_id}")

    task_end = category_end
    for index in range(task_start + 1, category_end):
        if lines[index].startswith("  ") and not lines[index].startswith("    "):
            task_end = index
            break

    task_block = lines[task_start:task_end]
    required_prefixes = [
        "    name:",
        "    role:",
        "    estimate:",
        "    skill:",
        "    actions:",
    ]
    for prefix in required_prefixes:
        if not any(line.startswith(prefix) for line in task_block):
            raise ValueError(f"missing required task field: {prefix.strip(':')}")

    action_lines = [line for line in task_block if line.startswith("      - {")]
    if not action_lines:
        raise ValueError("task actions must include at least one entry")

    for line in action_lines:
        if "type:" not in line or "desc:" not in line:
            raise ValueError(f"invalid action entry: {line}")


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(TaskBuilder)
