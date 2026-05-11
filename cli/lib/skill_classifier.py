#!/usr/bin/env python3
"""HELIX スキル分類を Codex で実行する。"""
from __future__ import annotations

import hashlib, json, re, subprocess
from pathlib import Path
from typing import Any

try:
    from .llm_classifier_base import CodexResponseError, LLMClassifierBase
    from .model_registry import resolve_role_model
    from .skill_jsonl_schema import ALLOWED_AGENTS, ALLOWED_PHASES, JsonlSchemaError
except ImportError:  # pragma: no cover
    from llm_classifier_base import CodexResponseError, LLMClassifierBase
    from model_registry import resolve_role_model
    from skill_jsonl_schema import ALLOWED_AGENTS, ALLOWED_PHASES, JsonlSchemaError

MODEL_NAME = resolve_role_model("classifier", default="gpt-5.4-mini")
CLASSIFIER_RETRY_COUNT = 3
NETWORK_EXIT_CODES = {7, 8, 28, 124}


class ClassifierError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _template_path(template_path: Path | None) -> Path:
    return template_path or Path(__file__).resolve().parents[1] / "templates" / "prompts" / "skill-classify.md"


def _helix_codex_path(helix_codex_path: str | None) -> str:
    return helix_codex_path or str(Path(__file__).resolve().parents[1] / "helix-codex")


def _to_csv(values: set[str]) -> str:
    return ", ".join(sorted(values))


def _extract_json_block(text: str) -> dict[str, Any] | None:
    if not text or not text.strip():
        return None
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE):
        try:
            parsed = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        first, last = stripped.find("{"), stripped.rfind("}")
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


def _validate_classification(raw: dict[str, Any], *, known_task_ids: set[str], allowed_agents: set[str], allowed_phases: set[str]) -> dict[str, Any]:
    required = {"phases", "tasks", "triggers", "anti_triggers", "agent", "similar", "confidence"}
    missing = required - set(raw)
    _ensure(isinstance(raw, dict) and not missing, "entry", f"missing required fields: {sorted(missing)}")
    phases, tasks = _ensure_str_list(raw.get("phases"), field="phases"), _ensure_str_list(raw.get("tasks"), field="tasks")
    triggers = _ensure_str_list(raw.get("triggers"), field="triggers")
    anti_triggers = _ensure_str_list(raw.get("anti_triggers"), field="anti_triggers")
    similar = _ensure_str_list(raw.get("similar"), field="similar")
    _ensure(not (set(phases) - allowed_phases), "phases", f"contains unknown values: {sorted(set(phases) - allowed_phases)}")
    _ensure(not (set(tasks) - known_task_ids), "tasks", f"contains unknown task ids: {sorted(set(tasks) - known_task_ids)}")
    agent, confidence = raw.get("agent"), raw.get("confidence")
    _ensure(isinstance(agent, str) and agent in allowed_agents, "agent", "must be one of ALLOWED_AGENTS")
    _ensure(isinstance(confidence, (int, float)), "confidence", "must be numeric")
    confidence_value = float(confidence)
    _ensure(0.0 <= confidence_value <= 1.0, "confidence", "must be in range [0.0, 1.0]")
    return {"phases": phases, "tasks": tasks, "triggers": triggers, "anti_triggers": anti_triggers, "agent": agent, "similar": similar, "confidence": confidence_value}


class SkillClassifier(LLMClassifierBase):
    role = MODEL_NAME
    classifier_name = "skill_classifier"
    codex_timeout_sec = 1800

    def _cache_key(self, query: str, context: dict | None) -> str:
        context = context or {}
        payload = {
            "skill_id": query,
            "content_sha": hashlib.sha256(str(context.get("skill_md_content", "")).encode("utf-8")).hexdigest(),
            "known_task_ids": sorted(context.get("known_task_ids", [])),
            "allowed_agents": sorted(context.get("allowed_agents", [])),
            "allowed_phases": sorted(context.get("allowed_phases", [])),
            "template_path": str(context.get("template_path") or ""),
        }
        return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    def _build_prompt(self, query: str, context: dict | None) -> str:
        context = context or {}
        if context.get("prompt") is not None:
            return str(context["prompt"])
        return self._render_prompt(_template_path(context.get("template_path")), {
            "skill_id": query, "skill_md_content": context.get("skill_md_content", ""),
            "allowed_phases": _to_csv(set(context.get("allowed_phases", ALLOWED_PHASES))),
            "allowed_agents": _to_csv(set(context.get("allowed_agents", ALLOWED_AGENTS))),
            "known_task_ids": _to_csv(set(context.get("known_task_ids", set()))),
        })

    def _invoke_codex(self, query: str, context: dict | None) -> str:
        cmd = [_helix_codex_path((context or {}).get("helix_codex_path")), "--role", "classifier", "--task", self._build_prompt(query, context)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.codex_timeout_sec, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ClassifierError(7, "Codex 呼び出しがタイムアウトしました（1800秒）。") from exc
        except OSError as exc:
            raise ClassifierError(7, f"helix-codex の起動に失敗しました: {exc}") from exc
        if proc.returncode != 0:
            if proc.returncode in NETWORK_EXIT_CODES:
                raise ClassifierError(7, f"ネットワークまたはタイムアウトで失敗しました (exit={proc.returncode})。")
            raise ClassifierError(7, f"helix-codex が失敗しました (exit={proc.returncode})。")
        return proc.stdout or ""

    def _parse_response(self, raw: str) -> dict:
        extracted = _extract_json_block(raw)
        if extracted is None:
            raise CodexResponseError("JSON object not found in classifier output")
        return _validate_classification(extracted, known_task_ids=self._known_task_ids, allowed_agents=self._allowed_agents, allowed_phases=self._allowed_phases)

    def classify_skill(self, skill_id: str, skill_md_content: str, *, known_task_ids: set[str], allowed_agents: set[str] = ALLOWED_AGENTS, allowed_phases: set[str] = ALLOWED_PHASES, template_path: Path | None = None, helix_codex_path: str | None = None) -> dict:
        self._known_task_ids, self._allowed_agents, self._allowed_phases = set(known_task_ids), set(allowed_agents), set(allowed_phases)
        return super().classify(skill_id, {
            "skill_md_content": skill_md_content, "known_task_ids": self._known_task_ids,
            "allowed_agents": self._allowed_agents, "allowed_phases": self._allowed_phases,
            "template_path": template_path, "helix_codex_path": helix_codex_path,
        })


def classify_skill(skill_id: str, skill_md_content: str, *, known_task_ids: set[str], allowed_agents: set[str] = ALLOWED_AGENTS, allowed_phases: set[str] = ALLOWED_PHASES, template_path: Path | None = None, helix_codex_path: str | None = None) -> dict:
    last_error: Exception | None = None
    for _ in range(CLASSIFIER_RETRY_COUNT):
        try:
            return SkillClassifier().classify_skill(skill_id, skill_md_content, known_task_ids=known_task_ids, allowed_agents=allowed_agents, allowed_phases=allowed_phases, template_path=template_path, helix_codex_path=helix_codex_path)
        except ClassifierError:
            raise
        except (CodexResponseError, JsonlSchemaError) as exc:
            last_error = exc
    message = "分類結果のバリデーションに失敗しました。"
    if last_error is not None:
        message = f"{message} {last_error}"
    raise ClassifierError(8, message)


def skill_classify(*args, **kwargs) -> dict:
    return classify_skill(*args, **kwargs)
