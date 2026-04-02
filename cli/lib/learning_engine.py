from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRAGMA_JOURNAL_MODE = "WAL"
PRAGMA_BUSY_TIMEOUT_MS = 5000

_REDACTION_TOKENS = (
    "password",
    "passwd",
    "token",
    "secret",
    "apikey",
    "api_key",
    "api-key",
    "access_token",
    "refresh_token",
    "private_key",
    "credential",
    "authorization",
    "bearer",
    "ssh-rsa",
    "-----begin",
    "/home",
)

_REDACTION_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+\b", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9._-]+\b"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bxox[bap]-[A-Za-z0-9-]+\b", re.IGNORECASE),
)

_KEY_VALUE_PATTERN = re.compile(r"([a-zA-Z0-9_\-.]+)=([^\s,;]+)")
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA journal_mode={PRAGMA_JOURNAL_MODE}")
    conn.execute(f"PRAGMA busy_timeout={PRAGMA_BUSY_TIMEOUT_MS}")
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slugify(text: str) -> str:
    lowered = (text or "").strip().lower()
    normalized = _SLUG_PATTERN.sub("-", lowered)
    normalized = normalized.strip("-")
    return normalized or "unknown"


def _json_load_or_none(text: str) -> Any | None:
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    if not stripped:
        return None
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _truncate(text: str, limit: int = 220) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _redact(value: Any, stats: dict[str, int] | None = None) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            if any(token in key_lower for token in _REDACTION_TOKENS):
                if stats is not None:
                    stats["count"] = stats.get("count", 0) + 1
                redacted[str(key)] = "[REDACTED]"
            else:
                redacted[str(key)] = _redact(item, stats)
        return redacted

    if isinstance(value, list):
        return [_redact(item, stats) for item in value]

    if isinstance(value, tuple):
        return tuple(_redact(item, stats) for item in value)

    if not isinstance(value, str):
        return value

    candidate = value
    for pattern in _REDACTION_PATTERNS:
        if pattern.search(candidate):
            if stats is not None:
                stats["count"] = stats.get("count", 0) + 1
            return "[REDACTED]"

    lowered = candidate.lower()
    if any(token in lowered for token in _REDACTION_TOKENS):
        if stats is not None:
            stats["count"] = stats.get("count", 0) + 1
        return "[REDACTED]"

    return candidate


def _extract_parameters(action_desc: str, evidence: str, stats: dict[str, int]) -> dict[str, Any]:
    payload = _json_load_or_none(evidence)
    if isinstance(payload, dict):
        return _redact(payload, stats)
    if isinstance(payload, list):
        return {"payload": _redact(payload, stats)}

    parameters: dict[str, Any] = {}
    for key, value in _KEY_VALUE_PATTERN.findall(action_desc or ""):
        parameters[str(key)] = str(value)

    if evidence and not parameters:
        parameters["evidence"] = _truncate(str(evidence).strip())

    return _redact(parameters, stats)


def _build_pattern_key(task_type: str, action_types: list[str]) -> str:
    type_slug = _slugify(task_type)
    compact = [
        _slugify(action_type).replace("-", "_")
        for action_type in action_types
        if action_type
    ]
    compact = [item for item in compact if item]
    head = "__".join(compact[:4]) if compact else "no_action"
    seed = f"{type_slug}|{'|'.join(compact)}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"{type_slug}::{head}::{digest}"


def _guess_builder_type(task_type: str, action_types: list[str]) -> str:
    joined = " ".join(action_types).lower()
    if "builder-agent-skill" in joined or "skill" in joined:
        return "agent-skill"
    if "builder-verify" in joined or "verify" in joined or "script" in joined:
        return "verify-script"
    if "builder-sub-agent" in joined or "sub-agent" in joined:
        return "sub-agent"
    if "builder-task" in joined or "task" in joined:
        return "task"

    lowered = (task_type or "").lower()
    if "review" in lowered:
        return "agent-skill"
    return "task"


def _infer_why_it_worked(action_types: list[str], observation_pass_rate: float) -> str:
    lowered = {action_type.lower() for action_type in action_types}

    has_search = any("search" in item or "research" in item for item in lowered)
    has_verify = any("verify" in item or "check" in item or "fact" in item for item in lowered)
    has_generate = any("generate" in item or "build" in item for item in lowered)

    if has_search and has_verify and has_generate:
        return "調査→生成→検証の順序が守られ、手戻りを抑えて品質を確保できたため。"
    if has_search and has_verify:
        return "先に情報収集し、検証で誤りを早期に除去できたため。"
    if has_generate and has_verify:
        return "実装生成後に検証を挟むことで、失敗パターンを早く検知できたため。"
    if observation_pass_rate >= 0.8:
        return "主要観測項目の通過率が高く、再現性のある手順として機能したため。"
    return "アクション順序が単純で実行負荷が低く、安定して完了できたため。"


def _infer_applicability(task_type: str, role: str, action_types: list[str]) -> str:
    type_label = task_type or "不明タスク"
    role_label = role or "汎用ロール"
    if any("security" in action.lower() for action in action_types):
        return f"{role_label} が担当する {type_label} 系のセキュリティ検証タスクで再利用しやすい。"
    if any("api" in action.lower() for action in action_types):
        return f"{role_label} が担当する {type_label} 系の API 実装・検証タスクで適用しやすい。"
    return f"{role_label} が担当する {type_label} 系の標準実装フローで適用しやすい。"


def analyze_success(task_run_id: int, db_path: str) -> dict[str, Any] | None:
    """成功タスク実行ログを recipe dict に変換する。"""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    task_row = conn.execute(
        """
        SELECT id, task_id, task_type, plan_goal, role, status, started_at, completed_at, output_log
        FROM task_runs
        WHERE id = ?
        """,
        (int(task_run_id),),
    ).fetchone()

    if task_row is None:
        conn.close()
        raise ValueError(f"task_run_id not found: {task_run_id}")

    if str(task_row["status"]).lower() != "completed":
        conn.close()
        raise ValueError(f"task_run_id is not successful(completed): {task_run_id}")

    action_rows = conn.execute(
        """
        SELECT action_index, action_type, action_desc, status, evidence
        FROM action_logs
        WHERE task_run_id = ?
        ORDER BY action_index ASC, id ASC
        """,
        (int(task_run_id),),
    ).fetchall()

    observation_row = conn.execute(
        """
        SELECT COUNT(*) AS total, COALESCE(SUM(passed), 0) AS passed
        FROM observations
        WHERE task_run_id = ?
        """,
        (int(task_run_id),),
    ).fetchone()

    conn.close()

    redaction_stats = {"count": 0}
    steps: list[dict[str, Any]] = []
    action_types: list[str] = []

    for fallback_index, row in enumerate(action_rows, start=1):
        action_type = str(row["action_type"] or "").strip()
        action_desc = str(row["action_desc"] or "").strip()
        action_status = str(row["status"] or "pending").strip()
        evidence = str(row["evidence"] or "")
        action_types.append(action_type)

        step_index = int(row["action_index"] or fallback_index)
        parameters = _extract_parameters(action_desc, evidence, redaction_stats)
        safe_desc = _redact(action_desc, redaction_stats)

        steps.append(
            {
                "index": step_index,
                "tool": action_type,
                "action_type": action_type,
                "description": safe_desc,
                "parameters": parameters,
                "status": action_status,
            }
        )

    if not steps:
        return None

    action_total = len(steps)
    action_passed = sum(1 for step in steps if str(step.get("status", "")).lower() in {"passed", "completed"})
    action_pass_rate = (action_passed / action_total) if action_total > 0 else 0.0

    observation_total = int(observation_row["total"] or 0) if observation_row else 0
    observation_passed = int(observation_row["passed"] or 0) if observation_row else 0
    observation_pass_rate = (observation_passed / observation_total) if observation_total > 0 else 0.0

    quality_score = ((action_pass_rate * 0.45) + (observation_pass_rate * 0.55)) * 100.0

    task_type = str(task_row["task_type"] or "unknown")
    role = str(task_row["role"] or "")
    pattern_key = _build_pattern_key(task_type, action_types)
    pattern_digest = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:8]
    recipe_id = f"recipe-{int(task_run_id)}-{pattern_digest}"

    tags = sorted(
        {
            f"task:{_slugify(task_type)}",
            f"role:{_slugify(role)}" if role else "role:unknown",
            *[f"action:{_slugify(item)}" for item in action_types if item],
        }
    )

    recipe = {
        "recipe_id": recipe_id,
        "pattern_key": pattern_key,
        "steps": sorted(steps, key=lambda item: int(item.get("index", 0))),
        "metrics": {
            "action_count": action_total,
            "action_pass_rate": round(action_pass_rate, 4),
            "observation_total": observation_total,
            "observation_pass_rate": round(observation_pass_rate, 4),
            "quality_score": round(quality_score, 2),
        },
        "classification": {
            "task_type": task_type,
            "role": role,
            "builder_type": _guess_builder_type(task_type, action_types),
            "tags": tags,
        },
        "security": {
            "redaction_applied": True,
            "redacted_fields": int(redaction_stats.get("count", 0)),
            "notes": "global sync 前提で redaction 済み",
        },
        "notes": {
            "why_it_worked": _infer_why_it_worked(action_types, observation_pass_rate),
            "applicability": _infer_applicability(task_type, role, action_types),
        },
        "source": {
            "task_run_id": int(task_row["id"]),
            "task_id": str(task_row["task_id"] or ""),
            "plan_goal": _redact(str(task_row["plan_goal"] or ""), redaction_stats),
            "started_at": str(task_row["started_at"] or ""),
            "completed_at": str(task_row["completed_at"] or ""),
        },
        "created_at": _now_iso(),
    }

    return recipe


def save_recipe(recipe: dict[str, Any], project_root: str) -> str:
    """recipe dict を .helix/recipes/<id>.json に保存してパスを返す。"""
    if not isinstance(recipe, dict):
        raise ValueError("recipe must be a dict")

    recipe_id = str(recipe.get("recipe_id") or "").strip()
    if not recipe_id:
        pattern_key = str(recipe.get("pattern_key") or "")
        digest = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:8] if pattern_key else "unknown"
        recipe_id = f"recipe-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{digest}"
        recipe["recipe_id"] = recipe_id

    recipe_dir = Path(project_root) / ".helix" / "recipes"
    recipe_dir.mkdir(parents=True, exist_ok=True)

    output_path = recipe_dir / f"{recipe_id}.json"
    output_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(output_path)


def list_recipes(project_root: str) -> list[dict[str, Any]]:
    """.helix/recipes 下の recipe 一覧を返す。"""
    recipe_dir = Path(project_root) / ".helix" / "recipes"
    if not recipe_dir.exists():
        return []

    recipes: list[dict[str, Any]] = []
    for recipe_file in sorted(recipe_dir.glob("*.json")):
        try:
            payload = json.loads(recipe_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        payload["_path"] = str(recipe_file)
        recipes.append(payload)
    return recipes


def find_recipe(recipe_id: str, project_root: str) -> dict[str, Any] | None:
    """Search order(project-local -> user-global) で recipe を解決する。"""
    clean_id = str(recipe_id or "").strip()
    if not clean_id:
        return None

    file_name = clean_id if clean_id.endswith(".json") else f"{clean_id}.json"

    local_path = Path(project_root) / ".helix" / "recipes" / file_name
    if local_path.exists():
        try:
            payload = json.loads(local_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload["_path"] = str(local_path)
                return payload
        except json.JSONDecodeError:
            return None

    user_global = Path.home() / ".helix" / "recipes" / file_name
    if user_global.exists():
        try:
            payload = json.loads(user_global.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload["_path"] = str(user_global)
                return payload
        except json.JSONDecodeError:
            return None

    return None


def resolve_success_run_ids(db_path: str, task_id: str | None = None, all_success: bool = False) -> list[int]:
    """learn 用に成功 task_run_id 一覧を返す。"""
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    if all_success:
        rows = conn.execute(
            "SELECT id FROM task_runs WHERE status = 'completed' ORDER BY id ASC"
        ).fetchall()
        conn.close()
        return [int(row["id"]) for row in rows]

    if task_id is None:
        row = conn.execute(
            "SELECT id FROM task_runs WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return [int(row["id"])] if row else []

    value = str(task_id).strip()
    if not value:
        conn.close()
        return []

    if value.isdigit():
        row = conn.execute(
            "SELECT id FROM task_runs WHERE id = ? AND status = 'completed'",
            (int(value),),
        ).fetchone()
        conn.close()
        return [int(row["id"])] if row else []

    row = conn.execute(
        """
        SELECT id
        FROM task_runs
        WHERE task_id = ? AND status = 'completed'
        ORDER BY id DESC
        LIMIT 1
        """,
        (value,),
    ).fetchone()
    conn.close()
    return [int(row["id"])] if row else []
