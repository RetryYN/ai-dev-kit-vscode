#!/usr/bin/env python3
"""HELIX スキル分類を Codex で実行する。"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    from .skill_jsonl_schema import ALLOWED_AGENTS, ALLOWED_PHASES, JsonlSchemaError
except ImportError:  # pragma: no cover - script execution fallback
    from skill_jsonl_schema import ALLOWED_AGENTS, ALLOWED_PHASES, JsonlSchemaError


MODEL_NAME = "gpt-5.4-mini"
CLASSIFIER_RETRY_COUNT = 3
NETWORK_EXIT_CODES = {7, 8, 28, 124}


class ClassifierError(RuntimeError):
    """分類処理の終了コード付きエラー。"""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _template_path(template_path: Path | None) -> Path:
    if template_path is not None:
        return template_path
    return Path(__file__).resolve().parents[1] / "templates" / "skill-classify-prompt.md"


def _helix_codex_path(helix_codex_path: str | None) -> str:
    if helix_codex_path:
        return helix_codex_path
    return str(Path(__file__).resolve().parents[1] / "helix-codex")


def _to_csv(values: set[str]) -> str:
    return ", ".join(sorted(values))


def _render_prompt(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", "" if value is None else str(value))
    return rendered


def _extract_json_block(text: str) -> dict[str, Any] | None:
    if not text or not text.strip():
        return None

    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed

    first = stripped.find("{")
    last = stripped.rfind("}")
    if first == -1 or last == -1 or first >= last:
        return None

    try:
        parsed = json.loads(stripped[first : last + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _ensure(condition: bool, field: str, message: str) -> None:
    if not condition:
        raise JsonlSchemaError(field, message)


def _ensure_str_list(value: Any, *, field: str) -> list[str]:
    _ensure(isinstance(value, list), field, "must be a list")
    _ensure(all(isinstance(item, str) for item in value), field, "all elements must be strings")
    return value


def _validate_classification(
    raw: dict[str, Any],
    *,
    known_task_ids: set[str],
    allowed_agents: set[str],
    allowed_phases: set[str],
) -> dict[str, Any]:
    _ensure(isinstance(raw, dict), "entry", "must be an object")

    required = {"phases", "tasks", "triggers", "anti_triggers", "agent", "similar", "confidence"}
    missing = required - set(raw)
    _ensure(not missing, "entry", f"missing required fields: {sorted(missing)}")

    phases = _ensure_str_list(raw.get("phases"), field="phases")
    unknown_phases = set(phases) - allowed_phases
    _ensure(not unknown_phases, "phases", f"contains unknown values: {sorted(unknown_phases)}")

    tasks = _ensure_str_list(raw.get("tasks"), field="tasks")
    unknown_tasks = set(tasks) - known_task_ids
    _ensure(not unknown_tasks, "tasks", f"contains unknown task ids: {sorted(unknown_tasks)}")

    triggers = _ensure_str_list(raw.get("triggers"), field="triggers")
    anti_triggers = _ensure_str_list(raw.get("anti_triggers"), field="anti_triggers")
    similar = _ensure_str_list(raw.get("similar"), field="similar")

    agent = raw.get("agent")
    _ensure(isinstance(agent, str), "agent", "must be a string")
    _ensure(agent in allowed_agents, "agent", "must be one of ALLOWED_AGENTS")

    confidence = raw.get("confidence")
    _ensure(isinstance(confidence, (int, float)), "confidence", "must be numeric")
    confidence_value = float(confidence)
    _ensure(0.0 <= confidence_value <= 1.0, "confidence", "must be in range [0.0, 1.0]")

    return {
        "phases": phases,
        "tasks": tasks,
        "triggers": triggers,
        "anti_triggers": anti_triggers,
        "agent": agent,
        "similar": similar,
        "confidence": confidence_value,
    }


def _run_classifier(prompt: str, *, helix_codex_path: str) -> str:
    cmd = [helix_codex_path, "--role", "classifier", "--task", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ClassifierError(7, "Codex 呼び出しがタイムアウトしました（1800秒）。") from exc
    except OSError as exc:
        raise ClassifierError(7, f"helix-codex の起動に失敗しました: {exc}") from exc

    if proc.returncode != 0:
        if proc.returncode in NETWORK_EXIT_CODES:
            raise ClassifierError(7, f"ネットワークまたはタイムアウトで失敗しました (exit={proc.returncode})。")
        raise ClassifierError(7, f"helix-codex が失敗しました (exit={proc.returncode})。")

    return proc.stdout or ""


def classify_skill(
    skill_id: str,
    skill_md_content: str,
    *,
    known_task_ids: set[str],
    allowed_agents: set[str] = ALLOWED_AGENTS,
    allowed_phases: set[str] = ALLOWED_PHASES,
    template_path: Path | None = None,
    helix_codex_path: str | None = None,
) -> dict:
    """
    Codex (gpt-5.4-mini) を呼んで skill を分類。
    戻り値: classification dict {phases, tasks, triggers, anti_triggers, agent, similar, confidence}
    失敗時 ClassifierError raise (code=7: network/codex failure, code=8: validation failure)
    retry: 不正 JSON / validation fail で最大 CLASSIFIER_RETRY_COUNT 回
    """
    tpl_path = _template_path(template_path)
    template = tpl_path.read_text(encoding="utf-8")

    prompt = _render_prompt(
        template,
        {
            "skill_id": skill_id,
            "skill_md_content": skill_md_content,
            "allowed_phases": _to_csv(set(allowed_phases)),
            "allowed_agents": _to_csv(set(allowed_agents)),
            "known_task_ids": _to_csv(set(known_task_ids)),
        },
    )

    last_error: Exception | None = None
    for _ in range(CLASSIFIER_RETRY_COUNT):
        raw_output = _run_classifier(prompt, helix_codex_path=_helix_codex_path(helix_codex_path))
        extracted = _extract_json_block(raw_output)
        if extracted is None:
            last_error = JsonlSchemaError("entry", "JSON object not found in classifier output")
            continue

        try:
            return _validate_classification(
                extracted,
                known_task_ids=known_task_ids,
                allowed_agents=allowed_agents,
                allowed_phases=allowed_phases,
            )
        except JsonlSchemaError as exc:
            last_error = exc

    message = "分類結果のバリデーションに失敗しました。"
    if last_error is not None:
        message = f"{message} {last_error}"
    raise ClassifierError(8, message)
