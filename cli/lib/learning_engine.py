"""HELIX learning engine.

責務: 実行履歴から成功/失敗パターンを分析し、再利用可能な recipe を生成する。
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
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
_HELIX_TEST_RESULT_PATTERN = re.compile(r"Results:\s*(\d+)\s+passed,\s*(\d+)\s+failed", re.IGNORECASE)
_PY_MYPY_ERROR_PATTERN = re.compile(r"Found\s+(\d+)\s+errors?", re.IGNORECASE)
_TS_ERROR_PATTERN = re.compile(r"\berror TS\d+:", re.IGNORECASE)
_HISTORY_QUERY_TOKEN_PATTERN = re.compile(r"[\s,]+")

_FAILURE_TYPE_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "syntax_error": (
        re.compile(r"\bsyntaxerror\b", re.IGNORECASE),
        re.compile(r"\binvalid syntax\b", re.IGNORECASE),
        re.compile(r"\bparse error\b", re.IGNORECASE),
        re.compile(r"\berror TS\d+\b", re.IGNORECASE),
        re.compile(r"\bsyntax\s+error\b", re.IGNORECASE),
    ),
    "timeout": (
        re.compile(r"\btimeout\b", re.IGNORECASE),
        re.compile(r"\btimed out\b", re.IGNORECASE),
        re.compile(r"\bdeadline exceeded\b", re.IGNORECASE),
    ),
    "test_failure": (
        re.compile(r"\btest(s)?\s+failed\b", re.IGNORECASE),
        re.compile(r"\bpytest\b", re.IGNORECASE),
        re.compile(r"\bjest\b", re.IGNORECASE),
        re.compile(r"\bplaywright\b", re.IGNORECASE),
        re.compile(r"\bassert(ion)?\s+failed\b", re.IGNORECASE),
    ),
    "gate_failure": (
        re.compile(r"\bgate\b", re.IGNORECASE),
        re.compile(r"\bg[1-8](?:\.\d+)?\b", re.IGNORECASE),
        re.compile(r"\bphase guard\b", re.IGNORECASE),
        re.compile(r"\bdeliverable gate\b", re.IGNORECASE),
        re.compile(r"\bfreeze\b", re.IGNORECASE),
    ),
}

_FAILURE_PREVENTION_TEMPLATES: dict[str, str] = {
    "syntax_error": "静的検査（lint/type-check）を修正前後で実行し、構文と型の不整合を先に除去する。",
    "runtime_error": "入力境界・null許容・例外処理を明示し、異常系の再現テストを追加する。",
    "test_failure": "失敗テストを最小再現として固定し、1件ずつ修正して回帰テストを追加する。",
    "gate_failure": "ゲート要件をチェックリスト化し、未達項目を埋めてから再判定する。",
    "timeout": "重い処理を分割し、タイムアウト閾値とリトライ条件を明示する。",
}

_VERIFICATION_CACHE: dict[str, dict[str, Any]] = {}
_BUILDER_EXECUTION_RUN_ID_MULTIPLIER = -1


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


def _collect_summary(recipe: dict[str, Any]) -> str:
    """recipe から検索用の 1 行サマリを生成する。"""
    classification = recipe.get("classification", {})
    if not isinstance(classification, dict):
        classification = {}

    pattern = recipe.get("pattern", {})
    if not isinstance(pattern, dict):
        pattern = {}

    metrics = recipe.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    notes = recipe.get("notes", {})
    if not isinstance(notes, dict):
        notes = {}

    builder = str(classification.get("builder_type") or pattern.get("builder_type") or "unknown").strip() or "unknown"

    raw_tags = classification.get("tags", [])
    tags = [str(tag).strip() for tag in raw_tags if str(tag).strip()] if isinstance(raw_tags, list) else []

    success_rate = metrics.get("success_rate")
    if success_rate is None:
        success_rate = metrics.get("action_pass_rate")
    if success_rate is None:
        success_rate = metrics.get("observation_pass_rate")
    if success_rate is None and metrics.get("action_failure_rate") is not None:
        try:
            success_rate = 1.0 - float(metrics.get("action_failure_rate") or 0.0)
        except (TypeError, ValueError):
            success_rate = None
    if success_rate is None and metrics.get("observation_failure_rate") is not None:
        try:
            success_rate = 1.0 - float(metrics.get("observation_failure_rate") or 0.0)
        except (TypeError, ValueError):
            success_rate = None
    if success_rate is None:
        try:
            success_rate = float(metrics.get("quality_score", 0.0) or 0.0) / 100.0
        except (TypeError, ValueError):
            success_rate = 0.0

    try:
        normalized_success_rate = float(success_rate)
    except (TypeError, ValueError):
        normalized_success_rate = 0.0
    normalized_success_rate = min(max(normalized_success_rate, 0.0), 1.0)

    why = str(
        notes.get("why_it_worked")
        or notes.get("failure_reason")
        or notes.get("applicability")
        or ""
    )
    why = " ".join(why.split())

    return (
        f"{builder} | tags:{','.join(tags[:5])} | "
        f"success:{normalized_success_rate:.0%} | {why[:80]}"
    )


def _collect_failure_text(
    output_log: str,
    action_rows: list[sqlite3.Row],
    observation_rows: list[sqlite3.Row],
) -> str:
    parts: list[str] = []
    if output_log:
        parts.append(str(output_log))

    for row in action_rows:
        status = str(row["status"] or "").lower()
        if status not in {"failed", "error"}:
            continue
        for key in ("action_desc", "evidence"):
            text = str(row[key] or "").strip()
            if text:
                parts.append(text)

    for row in observation_rows:
        reason = str(row["reason"] or "").strip()
        if reason:
            parts.append(reason)

    return "\n".join(parts).strip()


def _classify_failure_type(
    task_type: str,
    output_log: str,
    action_rows: list[sqlite3.Row],
    observation_rows: list[sqlite3.Row],
) -> str:
    corpus = _collect_failure_text(output_log, action_rows, observation_rows).lower()

    # テスト実行系 action が失敗していれば test_failure を優先する。
    for row in action_rows:
        status = str(row["status"] or "").lower()
        action_type = str(row["action_type"] or "").lower()
        if status in {"failed", "error"} and any(tag in action_type for tag in ("test", "pytest", "jest", "playwright")):
            return "test_failure"

    for failure_type in ("syntax_error", "timeout", "test_failure", "gate_failure"):
        patterns = _FAILURE_TYPE_PATTERNS.get(failure_type, ())
        if any(pattern.search(corpus) for pattern in patterns):
            return failure_type

    task_hint = str(task_type or "").lower()
    if "test" in task_hint:
        return "test_failure"
    if "gate" in task_hint:
        return "gate_failure"

    return "runtime_error"


def _failure_reason(
    output_log: str,
    action_rows: list[sqlite3.Row],
    observation_rows: list[sqlite3.Row],
    redaction_stats: dict[str, int],
) -> str:
    for row in observation_rows:
        reason = str(row["reason"] or "").strip()
        if reason:
            return _truncate(str(_redact(reason, redaction_stats)), limit=220)

    for row in action_rows:
        status = str(row["status"] or "").lower()
        if status not in {"failed", "error"}:
            continue
        evidence = str(row["evidence"] or "").strip()
        if evidence:
            return _truncate(str(_redact(evidence, redaction_stats)), limit=220)
        desc = str(row["action_desc"] or "").strip()
        if desc:
            return _truncate(str(_redact(desc, redaction_stats)), limit=220)

    if output_log:
        return _truncate(str(_redact(output_log, redaction_stats)), limit=220)
    return "失敗理由をログから特定できませんでした。"


def _failure_prevention_template(failure_type: str) -> str:
    return _FAILURE_PREVENTION_TEMPLATES.get(
        failure_type,
        _FAILURE_PREVENTION_TEMPLATES["runtime_error"],
    )


def _history_query_tokens(query: str) -> list[str]:
    text = str(query or "").strip().lower()
    if not text:
        return []
    return [token for token in _HISTORY_QUERY_TOKEN_PATTERN.split(text) if token]


def _history_recipe_text(recipe: dict[str, Any]) -> str:
    classification = recipe.get("classification", {})
    notes = recipe.get("notes", {})
    source = recipe.get("source", {})

    if not isinstance(classification, dict):
        classification = {}
    if not isinstance(notes, dict):
        notes = {}
    if not isinstance(source, dict):
        source = {}

    parts: list[str] = []
    for key in ("pattern_key", "recipe_id", "failure_type"):
        value = recipe.get(key)
        if value:
            parts.append(str(value))
    for key in ("task_type", "role", "builder_type"):
        value = classification.get(key)
        if value:
            parts.append(str(value))
    for key in ("failure_reason", "recurrence_prevention", "why_it_worked", "applicability"):
        value = notes.get(key)
        if value:
            parts.append(str(value))
    for key in ("task_id", "plan_goal"):
        value = source.get(key)
        if value:
            parts.append(str(value))
    return " ".join(parts).lower()


def _history_recipe_score(tokens: list[str], recipe: dict[str, Any]) -> float:
    text = _history_recipe_text(recipe)
    classification = recipe.get("classification", {})
    tags: set[str] = set()
    if isinstance(classification, dict):
        raw_tags = classification.get("tags", [])
        if isinstance(raw_tags, list):
            tags = {str(item).lower() for item in raw_tags}

    metrics = recipe.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    try:
        quality = float(metrics.get("quality_score", 0.0) or 0.0)
    except (TypeError, ValueError):
        quality = 0.0
    quality = min(max(quality, 0.0), 100.0) / 100.0

    if not tokens:
        return quality * 100.0

    text_hits = sum(1 for token in tokens if token in text)
    tag_hits = sum(1 for token in tokens if any(token in tag for tag in tags))
    summary = str(recipe.get("summary") or "").lower()
    summary_hits = sum(1 for token in tokens if token in summary) if summary else 0
    return (
        (text_hits / len(tokens)) * 70.0
        + (tag_hits / len(tokens)) * 20.0
        + quality * 10.0
        + (summary_hits / len(tokens)) * 15.0
    )


def _project_root_from_db_path(db_path: str) -> Path:
    path = Path(db_path).resolve()
    if path.parent.name == ".helix":
        return path.parent.parent
    return path.parent


def _resolve_tool(project_root: Path, tool_name: str) -> str | None:
    local_tool = project_root / "node_modules" / ".bin" / tool_name
    if local_tool.exists() and os.access(local_tool, os.X_OK):
        return str(local_tool)
    return shutil.which(tool_name)


def _run_command(command: list[str], cwd: Path, timeout: int = 5) -> tuple[bool, int | None, str, str]:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout)),
            check=False,
        )
        return True, int(proc.returncode), str(proc.stdout or ""), str(proc.stderr or "")
    except FileNotFoundError:
        return False, None, "", "not available"
    except subprocess.TimeoutExpired as exc:
        stdout = str(exc.stdout or "")
        stderr = str(exc.stderr or "")
        if stderr:
            stderr += "\n"
        stderr += f"timeout({timeout}s)"
        return True, None, stdout, stderr
    except Exception as exc:  # noqa: BLE001
        return False, None, "", str(exc)


def _parse_json_from_text(text: str) -> Any | None:
    stripped = (text or "").strip()
    if not stripped:
        return None

    for start_char in ("{", "["):
        idx = stripped.find(start_char)
        if idx < 0:
            continue
        candidate = stripped[idx:].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _encode_builder_execution_run_id(builder_row_id: int) -> int:
    return _BUILDER_EXECUTION_RUN_ID_MULTIPLIER * int(builder_row_id)


def _decode_builder_execution_run_id(run_id: int) -> int | None:
    try:
        raw = int(run_id)
    except (TypeError, ValueError):
        return None
    if raw < 0:
        return abs(raw)
    return None


def _find_test_result_in_text(text: str) -> tuple[int, int] | None:
    matches = list(_HELIX_TEST_RESULT_PATTERN.finditer(text or ""))
    if not matches:
        return None
    latest = matches[-1]
    try:
        return int(latest.group(1)), int(latest.group(2))
    except (TypeError, ValueError):
        return None


def _latest_helix_test_result(project_root: Path) -> tuple[int, int] | None:
    candidates: list[Path] = [
        project_root / ".helix" / "logs" / "helix-test.log",
        project_root / ".helix" / "logs" / "helix-test.txt",
        project_root / ".helix" / "runtime" / "helix-test.log",
        project_root / ".helix" / "helix-test.log",
        project_root / "helix-test.log",
    ]

    log_dir = project_root / ".helix" / "logs"
    if log_dir.exists():
        candidates.extend(sorted(log_dir.glob("helix-test*.log")))
        candidates.extend(sorted(log_dir.glob("helix-test*.txt")))

    existing = [path for path in candidates if path.exists() and path.is_file()]
    existing.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    for path in existing:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        parsed = _find_test_result_in_text(text)
        if parsed is not None:
            return parsed

    db_path = project_root / ".helix" / "helix.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute(
                """
                SELECT output_log
                FROM task_runs
                WHERE output_log LIKE '%Results:%passed,%failed%'
                ORDER BY completed_at DESC, id DESC
                LIMIT 20
                """
            ).fetchall()
            conn.close()
            for item in row:
                if not item:
                    continue
                parsed = _find_test_result_in_text(str(item[0] or ""))
                if parsed is not None:
                    return parsed
        except sqlite3.Error:
            pass

    return None


def _count_python_source_lines(path: Path) -> int:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return 0
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        count += 1
    return count


def _extract_python_coverage_percent(coverage_db: Path, project_root: Path) -> float | None:
    try:
        from coverage import numbits  # type: ignore
    except Exception:
        return None

    try:
        conn = sqlite3.connect(str(coverage_db))
        rows = conn.execute(
            """
            SELECT file.path, line_bits.numbits
            FROM line_bits
            JOIN file ON file.id = line_bits.file_id
            """
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return None

    if not rows:
        return None

    covered_by_file: dict[str, set[int]] = {}
    for path_value, numbits_blob in rows:
        file_path = str(path_value or "")
        if not file_path:
            continue
        try:
            line_numbers = set(int(v) for v in numbits.numbits_to_nums(numbits_blob))
        except Exception:
            continue
        if not line_numbers:
            continue
        bucket = covered_by_file.setdefault(file_path, set())
        bucket.update(line_numbers)

    total_lines = 0
    covered_lines = 0
    for path_value, covered in covered_by_file.items():
        target = Path(path_value)
        if not target.is_absolute():
            target = (project_root / target).resolve()
        source_count = _count_python_source_lines(target)
        if source_count <= 0:
            continue
        total_lines += source_count
        covered_lines += min(len(covered), source_count)

    if total_lines <= 0:
        return None

    return (covered_lines / total_lines) * 100.0


def _extract_go_coverage_percent(coverage_out: Path, project_root: Path) -> float | None:
    go_tool = _resolve_tool(project_root, "go")
    if go_tool:
        available, code, stdout, stderr = _run_command(
            [go_tool, "tool", "cover", "-func", str(coverage_out)],
            cwd=project_root,
            timeout=5,
        )
        if available and code is not None:
            output = f"{stdout}\n{stderr}"
            matched = re.search(r"total:\s+\(statements\)\s+([0-9.]+)%", output)
            if matched:
                try:
                    return float(matched.group(1))
                except ValueError:
                    pass

    try:
        text = coverage_out.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    total = 0
    covered = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("mode:"):
            continue
        parts = stripped.split()
        if len(parts) < 3:
            continue
        try:
            statements = int(parts[-2])
            hits = int(parts[-1])
        except ValueError:
            continue
        total += statements
        if hits > 0:
            covered += statements

    if total <= 0:
        return None
    return (covered / total) * 100.0


def _collect_test_results(project_root: str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    result: dict[str, Any] = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "coverage": 0.0,
        "test_files": [],
    }

    parsed = _latest_helix_test_result(root)
    if parsed is not None:
        passed, failed = parsed
        result["passed"] = max(0, int(passed))
        result["failed"] = max(0, int(failed))
        result["total"] = max(0, int(passed) + int(failed))

    verify_dir = root / "verify"
    if verify_dir.exists():
        files = [str(path.relative_to(root)) for path in sorted(verify_dir.glob("*.sh")) if path.is_file()]
        result["test_files"] = files

    coverage_summary = root / "coverage" / "coverage-summary.json"
    if coverage_summary.exists():
        try:
            payload = json.loads(coverage_summary.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                coverage = (
                    payload.get("total", {})
                    if isinstance(payload.get("total"), dict)
                    else payload
                )
                lines = coverage.get("lines", {}) if isinstance(coverage, dict) else {}
                pct = lines.get("pct") if isinstance(lines, dict) else None
                if isinstance(pct, (int, float)):
                    result["coverage"] = round(float(pct), 2)
                    return result
        except Exception:  # noqa: BLE001
            pass

    py_coverage_db = root / ".coverage"
    if py_coverage_db.exists():
        py_cov = _extract_python_coverage_percent(py_coverage_db, root)
        if isinstance(py_cov, (int, float)):
            result["coverage"] = round(float(py_cov), 2)
            return result

    go_coverage_out = root / "coverage.out"
    if go_coverage_out.exists():
        go_cov = _extract_go_coverage_percent(go_coverage_out, root)
        if isinstance(go_cov, (int, float)):
            result["coverage"] = round(float(go_cov), 2)

    return result


def _validate_matrix_schema(project_root: Path) -> bool:
    try:
        from . import matrix_compiler as compiler
    except ImportError:
        import matrix_compiler as compiler  # type: ignore

    matrix = compiler._load_matrix(project_root)  # type: ignore[attr-defined]
    cli_root = Path(compiler.__file__).resolve().parents[1]
    deliverables_rules, _structure, naming, _common_defs = compiler._read_rules(project_root, cli_root)  # type: ignore[attr-defined]
    compiler.validate_matrix(matrix, deliverables_rules, naming)
    return True


def _collect_contract_results(project_root: str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    result: dict[str, Any] = {"api_diff": "", "type_check": "", "schema_valid": None}

    openapi_files = sorted(root.glob("docs/**/D-API/*.yaml")) + sorted(root.glob("docs/**/D-API/*.yml"))
    if not openapi_files:
        result["api_diff"] = "not found"
    else:
        openapi_diff = _resolve_tool(root, "openapi-diff")
        if not openapi_diff:
            result["api_diff"] = "not available"
        elif len(openapi_files) < 2:
            result["api_diff"] = "found"
        else:
            available, code, stdout, stderr = _run_command(
                [openapi_diff, str(openapi_files[-2]), str(openapi_files[-1])],
                cwd=root,
                timeout=5,
            )
            if not available or code is None:
                result["api_diff"] = "not available"
            elif code == 0:
                result["api_diff"] = "0 breaking changes"
            else:
                output = f"{stdout}\n{stderr}"
                if re.search(r"no breaking changes", output, re.IGNORECASE):
                    result["api_diff"] = "0 breaking changes"
                else:
                    result["api_diff"] = f"breaking changes detected (exit={code})"

    type_check_messages: list[str] = []
    if (root / "tsconfig.json").exists():
        tsc = _resolve_tool(root, "tsc")
        if not tsc:
            type_check_messages.append("typescript project detected (not available)")
        else:
            available, code, stdout, stderr = _run_command(
                [tsc, "--noEmit", "--pretty", "false"],
                cwd=root,
                timeout=5,
            )
            if not available or code is None:
                type_check_messages.append("typescript project detected (not available)")
            elif code == 0:
                type_check_messages.append("0 errors (typescript)")
            else:
                output = f"{stdout}\n{stderr}"
                errors = len(_TS_ERROR_PATTERN.findall(output))
                if errors > 0:
                    type_check_messages.append(f"{errors} errors (typescript)")
                else:
                    type_check_messages.append(f"typescript errors (exit={code})")

    if (root / "pyproject.toml").exists():
        mypy = _resolve_tool(root, "mypy")
        if not mypy:
            type_check_messages.append("mypy project detected (not available)")
        else:
            available, code, stdout, stderr = _run_command([mypy, "."], cwd=root, timeout=5)
            if not available or code is None:
                type_check_messages.append("mypy project detected (not available)")
            elif code == 0:
                type_check_messages.append("0 errors (mypy)")
            else:
                output = f"{stdout}\n{stderr}"
                matched = _PY_MYPY_ERROR_PATTERN.search(output)
                if matched:
                    type_check_messages.append(f"{int(matched.group(1))} errors (mypy)")
                else:
                    type_check_messages.append(f"mypy errors (exit={code})")

    result["type_check"] = "; ".join(type_check_messages) if type_check_messages else "not detected"

    if (root / ".helix" / "matrix.yaml").exists():
        try:
            result["schema_valid"] = _validate_matrix_schema(root)
        except Exception:  # noqa: BLE001
            result["schema_valid"] = False

    return result


def _parse_ruff_errors(output: str) -> int:
    found_match = re.search(r"Found\s+(\d+)\s+errors?", output, re.IGNORECASE)
    if found_match:
        return int(found_match.group(1))
    total = 0
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        head = stripped.split(maxsplit=1)[0]
        if head.isdigit():
            total += int(head)
    return total


def _collect_lint_errors(project_root: Path) -> int:
    ruff = _resolve_tool(project_root, "ruff")
    if ruff:
        available, code, stdout, stderr = _run_command([ruff, "check", "--statistics", "."], cwd=project_root, timeout=5)
        if available and code == 0:
            return 0
        if available and code is not None:
            parsed = _parse_ruff_errors(f"{stdout}\n{stderr}")
            return parsed if parsed > 0 else 1

    eslint = _resolve_tool(project_root, "eslint")
    if eslint:
        available, code, stdout, stderr = _run_command([eslint, ".", "--format", "json"], cwd=project_root, timeout=5)
        if available and (stdout or stderr):
            payload = _parse_json_from_text(stdout or stderr)
            if isinstance(payload, list):
                total = 0
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    total += int(item.get("errorCount", 0) or 0)
                return total
        if available and code == 0:
            return 0
        if available and code is not None:
            return 1

    flake8 = _resolve_tool(project_root, "flake8")
    if flake8:
        available, code, stdout, stderr = _run_command([flake8, "."], cwd=project_root, timeout=5)
        if available and code == 0:
            return 0
        if available and code is not None:
            merged = "\n".join([line for line in (stdout, stderr) if line]).strip()
            if not merged:
                return 1
            return len([line for line in merged.splitlines() if line.strip()])

    return -1


def _collect_security_issues(project_root: Path) -> int:
    npm = _resolve_tool(project_root, "npm")
    if npm and (project_root / "package.json").exists():
        available, code, stdout, stderr = _run_command([npm, "audit", "--json"], cwd=project_root, timeout=5)
        if available and (stdout or stderr):
            payload = _parse_json_from_text(stdout or stderr)
            if isinstance(payload, dict):
                meta = payload.get("metadata", {})
                vulnerabilities = meta.get("vulnerabilities", {}) if isinstance(meta, dict) else {}
                if isinstance(vulnerabilities, dict):
                    high = int(vulnerabilities.get("high", 0) or 0)
                    critical = int(vulnerabilities.get("critical", 0) or 0)
                    return high + critical
        if available and code == 0:
            return 0

    pip_audit = _resolve_tool(project_root, "pip-audit")
    if pip_audit and ((project_root / "pyproject.toml").exists() or (project_root / "requirements.txt").exists()):
        available, code, stdout, stderr = _run_command([pip_audit, "-f", "json"], cwd=project_root, timeout=5)
        if available and (stdout or stderr):
            payload = _parse_json_from_text(stdout or stderr)
            if isinstance(payload, list):
                count = 0
                for dep in payload:
                    if not isinstance(dep, dict):
                        continue
                    vulns = dep.get("vulns", [])
                    if isinstance(vulns, list):
                        count += len(vulns)
                return count
        if available and code == 0:
            return 0

    return -1


def _collect_textlint_errors(project_root: Path) -> int:
    textlint = _resolve_tool(project_root, "textlint")
    if not textlint:
        return -1

    available, code, stdout, stderr = _run_command(
        [textlint, "--format", "json", "."],
        cwd=project_root,
        timeout=5,
    )
    if not available:
        return -1

    payload = _parse_json_from_text(stdout or stderr)
    if isinstance(payload, list):
        total = 0
        for item in payload:
            if not isinstance(item, dict):
                continue
            messages = item.get("messages", [])
            if isinstance(messages, list):
                total += len(messages)
        return total

    if code == 0:
        return 0
    if code is not None:
        return 1
    return -1


def _collect_quality_results(project_root: str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    result = {"lint_errors": -1, "security_issues": -1, "textlint_errors": -1}
    try:
        result["lint_errors"] = int(_collect_lint_errors(root))
    except Exception:  # noqa: BLE001
        result["lint_errors"] = -1
    try:
        result["security_issues"] = int(_collect_security_issues(root))
    except Exception:  # noqa: BLE001
        result["security_issues"] = -1
    try:
        result["textlint_errors"] = int(_collect_textlint_errors(root))
    except Exception:  # noqa: BLE001
        result["textlint_errors"] = -1
    return result


def _collect_verification(project_root: str) -> dict[str, Any]:
    key = str(Path(project_root).resolve())
    cached = _VERIFICATION_CACHE.get(key)
    if cached is not None:
        return copy.deepcopy(cached)

    verification = {
        "tests": _collect_test_results(project_root),
        "contracts": _collect_contract_results(project_root),
        "quality": _collect_quality_results(project_root),
        "collected_at": _now_iso(),
    }
    _VERIFICATION_CACHE[key] = verification
    return copy.deepcopy(verification)


def analyze_success(task_run_id: int, db_path: str) -> dict[str, Any] | None:
    """成功実行ログを recipe dict に変換する。"""
    builder_row_id = _decode_builder_execution_run_id(task_run_id)
    if builder_row_id is not None:
        return _analyze_builder_success(builder_row_id=builder_row_id, db_path=db_path)

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

    project_root = _project_root_from_db_path(db_path)
    verification = _collect_verification(str(project_root))

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
        "verification": verification,
        "source": {
            "task_run_id": int(task_row["id"]),
            "task_id": str(task_row["task_id"] or ""),
            "plan_goal": _redact(str(task_row["plan_goal"] or ""), redaction_stats),
            "started_at": str(task_row["started_at"] or ""),
            "completed_at": str(task_row["completed_at"] or ""),
        },
        "created_at": _now_iso(),
    }
    recipe["summary"] = _collect_summary(recipe)

    return recipe


def analyze_failure(task_run_id: int, db_path: str) -> dict[str, Any] | None:
    """失敗実行ログを failure recipe dict に変換する。"""
    builder_row_id = _decode_builder_execution_run_id(task_run_id)
    if builder_row_id is not None:
        return _analyze_builder_failure(builder_row_id=builder_row_id, db_path=db_path)

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

    status_text = str(task_row["status"] or "").strip().lower()
    if status_text == "completed":
        conn.close()
        raise ValueError(f"task_run_id is not failure: {task_run_id}")

    action_rows = conn.execute(
        """
        SELECT action_index, action_type, action_desc, status, evidence
        FROM action_logs
        WHERE task_run_id = ?
        ORDER BY action_index ASC, id ASC
        """,
        (int(task_run_id),),
    ).fetchall()

    observation_rows = conn.execute(
        """
        SELECT passed, reason
        FROM observations
        WHERE task_run_id = ?
        ORDER BY id ASC
        """,
        (int(task_run_id),),
    ).fetchall()
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
        fallback_action = str(task_row["task_type"] or "task-failed")
        action_types = [fallback_action]
        steps = [
            {
                "index": 1,
                "tool": fallback_action,
                "action_type": fallback_action,
                "description": fallback_action,
                "parameters": {
                    "status": status_text or "failed",
                },
                "status": "failed",
            }
        ]

    action_total = len(steps)
    action_failed = sum(1 for step in steps if str(step.get("status", "")).lower() in {"failed", "error"})
    action_failure_rate = (action_failed / action_total) if action_total > 0 else 1.0

    observation_total = len(observation_rows)
    observation_failed = sum(1 for row in observation_rows if int(row["passed"] or 0) == 0)
    observation_failure_rate = (observation_failed / observation_total) if observation_total > 0 else 1.0

    # failure recipe でも score を持たせ、検索時に比較可能にする（低いほど不安定）。
    quality_score = max(0.0, 100.0 - (((action_failure_rate * 0.45) + (observation_failure_rate * 0.55)) * 100.0))

    task_type = str(task_row["task_type"] or "unknown")
    role = str(task_row["role"] or "")
    output_log = str(task_row["output_log"] or "")
    failure_type = _classify_failure_type(task_type, output_log, action_rows, observation_rows)
    failure_reason = _failure_reason(output_log, action_rows, observation_rows, redaction_stats)

    pattern_key = _build_pattern_key(f"{task_type}-failure", action_types + [failure_type])
    pattern_digest = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:8]
    recipe_id = f"recipe-failure-{int(task_run_id)}-{pattern_digest}"

    tags = sorted(
        {
            f"task:{_slugify(task_type)}",
            f"role:{_slugify(role)}" if role else "role:unknown",
            f"failure:{failure_type}",
            *[f"action:{_slugify(item)}" for item in action_types if item],
        }
    )

    project_root = _project_root_from_db_path(db_path)
    verification = _collect_verification(str(project_root))

    recipe = {
        "recipe_id": recipe_id,
        "pattern_key": pattern_key,
        "success": False,
        "failure_type": failure_type,
        "steps": sorted(steps, key=lambda item: int(item.get("index", 0))),
        "metrics": {
            "action_count": action_total,
            "action_failure_rate": round(action_failure_rate, 4),
            "observation_total": observation_total,
            "observation_failure_rate": round(observation_failure_rate, 4),
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
            "failure_reason": failure_reason,
            "recurrence_prevention": _failure_prevention_template(failure_type),
            "applicability": f"{role or '汎用ロール'} が担当する {task_type} の失敗予防チェックで再利用できる。",
        },
        "verification": verification,
        "source": {
            "task_run_id": int(task_row["id"]),
            "task_id": str(task_row["task_id"] or ""),
            "plan_goal": _redact(str(task_row["plan_goal"] or ""), redaction_stats),
            "status": status_text or "failed",
            "started_at": str(task_row["started_at"] or ""),
            "completed_at": str(task_row["completed_at"] or ""),
            "output_log": _truncate(str(_redact(output_log, redaction_stats)), limit=400) if output_log else "",
        },
        "created_at": _now_iso(),
    }
    recipe["summary"] = _collect_summary(recipe)
    return recipe


def _analyze_builder_success(builder_row_id: int, db_path: str) -> dict[str, Any] | None:
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    builder_row = conn.execute(
        """
        SELECT
            id,
            execution_id,
            builder_type,
            builder_name,
            task_id,
            status,
            success,
            input_signature_json,
            pattern_tags_json,
            step_trace_json,
            current_step,
            quality_score,
            validation_summary_json,
            started_at,
            finished_at,
            error_text
        FROM builder_executions
        WHERE id = ?
        """,
        (int(builder_row_id),),
    ).fetchone()
    conn.close()

    if builder_row is None:
        raise ValueError(f"builder_executions に実行履歴がありません: {builder_row_id}")

    success_flag = int(builder_row["success"] or 0) == 1
    status_text = str(builder_row["status"] or "").strip().lower()
    if not success_flag and status_text != "completed":
        raise ValueError(f"builder 実行が成功していません: {builder_row_id}")

    redaction_stats = {"count": 0}
    action_types: list[str] = []
    steps: list[dict[str, Any]] = []

    raw_trace = _json_load_or_none(str(builder_row["step_trace_json"] or ""))
    step_trace = raw_trace if isinstance(raw_trace, list) else []

    for index, item in enumerate(step_trace, start=1):
        if isinstance(item, dict):
            action_type = str(item.get("name") or f"step-{index}").strip() or f"step-{index}"
            raw_data = item.get("data")
            if isinstance(raw_data, (dict, list, tuple)):
                parameters = _redact(raw_data, redaction_stats)
            elif raw_data is None:
                parameters = {}
            else:
                parameters = {"value": _redact(raw_data, redaction_stats)}
            status = str(item.get("status") or "passed")
        else:
            action_type = f"step-{index}"
            parameters = {"value": _redact(item, redaction_stats)}
            status = "passed"

        action_types.append(action_type)
        steps.append(
            {
                "index": index,
                "tool": action_type,
                "action_type": action_type,
                "description": action_type,
                "parameters": parameters,
                "status": status,
            }
        )

    if not steps:
        fallback_step = (
            str(builder_row["current_step"] or "").strip()
            or str(builder_row["builder_type"] or "").strip()
            or "builder-execution"
        )
        action_types = [fallback_step]
        steps = [
            {
                "index": 1,
                "tool": fallback_step,
                "action_type": fallback_step,
                "description": fallback_step,
                "parameters": {},
                "status": "passed",
            }
        ]

    action_total = len(steps)
    action_passed = sum(1 for step in steps if str(step.get("status", "")).lower() in {"passed", "completed"})
    if action_total > 0 and action_passed == 0 and success_flag:
        action_passed = action_total
    action_pass_rate = (action_passed / action_total) if action_total > 0 else 0.0

    observation_total = 1
    observation_pass_rate = 1.0 if success_flag else 0.0

    raw_quality_score = builder_row["quality_score"]
    try:
        quality_score = float(raw_quality_score)
    except (TypeError, ValueError):
        quality_score = 0.0
    quality_score = min(max(quality_score, 0.0), 100.0)
    if quality_score <= 0.0:
        quality_score = ((action_pass_rate * 0.45) + (observation_pass_rate * 0.55)) * 100.0

    builder_type = str(builder_row["builder_type"] or "builder")
    task_type = f"builder-{builder_type}"
    role = "builder"
    pattern_key = _build_pattern_key(task_type, action_types)
    pattern_digest = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:8]
    recipe_id = f"recipe-builder-{int(builder_row['id'])}-{pattern_digest}"

    raw_tags = _json_load_or_none(str(builder_row["pattern_tags_json"] or ""))
    pattern_tags = raw_tags if isinstance(raw_tags, list) else []
    tags = sorted(
        {
            f"task:{_slugify(task_type)}",
            "role:builder",
            f"builder:{_slugify(builder_type)}",
            *[f"action:{_slugify(item)}" for item in action_types if item],
            *[str(tag) for tag in pattern_tags if str(tag).strip()],
        }
    )

    project_root = _project_root_from_db_path(db_path)
    verification = _collect_verification(str(project_root))

    raw_signature = _json_load_or_none(str(builder_row["input_signature_json"] or ""))
    input_signature = raw_signature if isinstance(raw_signature, dict) else {}

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
            "builder_type": builder_type,
            "tags": tags,
        },
        "security": {
            "redaction_applied": True,
            "redacted_fields": int(redaction_stats.get("count", 0)),
            "notes": "global sync 前提で redaction 済み",
        },
        "notes": {
            "why_it_worked": _infer_why_it_worked(action_types, observation_pass_rate),
            "applicability": f"builder_type={builder_type} の自動生成タスクで再利用しやすい。",
        },
        "verification": verification,
        "source": {
            "origin": "builder_executions",
            "builder_execution_id": str(builder_row["execution_id"] or ""),
            "builder_row_id": int(builder_row["id"]),
            "task_id": str(builder_row["task_id"] or ""),
            "builder_name": _redact(str(builder_row["builder_name"] or ""), redaction_stats),
            "input_signature": _redact(input_signature, redaction_stats),
            "started_at": str(builder_row["started_at"] or ""),
            "completed_at": str(builder_row["finished_at"] or ""),
            "error_text": _redact(str(builder_row["error_text"] or ""), redaction_stats),
            "task_run_id": _encode_builder_execution_run_id(int(builder_row["id"])),
        },
        "created_at": _now_iso(),
    }

    validation = _json_load_or_none(str(builder_row["validation_summary_json"] or ""))
    if isinstance(validation, dict) and validation:
        recipe["source"]["validation_summary"] = _redact(validation, redaction_stats)

    recipe["summary"] = _collect_summary(recipe)
    return recipe


def _analyze_builder_failure(builder_row_id: int, db_path: str) -> dict[str, Any] | None:
    conn = _connect(db_path)
    conn.row_factory = sqlite3.Row

    builder_row = conn.execute(
        """
        SELECT
            id,
            execution_id,
            builder_type,
            builder_name,
            task_id,
            status,
            success,
            input_signature_json,
            pattern_tags_json,
            step_trace_json,
            current_step,
            quality_score,
            validation_summary_json,
            started_at,
            finished_at,
            error_text
        FROM builder_executions
        WHERE id = ?
        """,
        (int(builder_row_id),),
    ).fetchone()
    conn.close()

    if builder_row is None:
        raise ValueError(f"builder_executions に実行履歴がありません: {builder_row_id}")

    success_flag = int(builder_row["success"] or 0) == 1
    status_text = str(builder_row["status"] or "").strip().lower()
    if success_flag or status_text == "completed":
        raise ValueError(f"builder 実行は失敗ではありません: {builder_row_id}")

    redaction_stats = {"count": 0}
    action_types: list[str] = []
    steps: list[dict[str, Any]] = []
    failure_action_rows: list[dict[str, Any]] = []

    raw_trace = _json_load_or_none(str(builder_row["step_trace_json"] or ""))
    step_trace = raw_trace if isinstance(raw_trace, list) else []

    for index, item in enumerate(step_trace, start=1):
        if isinstance(item, dict):
            action_type = str(item.get("name") or f"step-{index}").strip() or f"step-{index}"
            raw_data = item.get("data")
            if isinstance(raw_data, (dict, list, tuple)):
                parameters = _redact(raw_data, redaction_stats)
            elif raw_data is None:
                parameters = {}
            else:
                parameters = {"value": _redact(raw_data, redaction_stats)}
            status = str(item.get("status") or "passed")
        else:
            action_type = f"step-{index}"
            parameters = {"value": _redact(item, redaction_stats)}
            status = "passed"

        action_types.append(action_type)
        steps.append(
            {
                "index": index,
                "tool": action_type,
                "action_type": action_type,
                "description": action_type,
                "parameters": parameters,
                "status": status,
            }
        )
        failure_action_rows.append(
            {
                "action_type": action_type,
                "action_desc": action_type,
                "status": status,
                "evidence": json.dumps(parameters, ensure_ascii=False, default=str),
            }
        )

    if not steps:
        fallback_step = (
            str(builder_row["current_step"] or "").strip()
            or str(builder_row["builder_type"] or "").strip()
            or "builder-execution"
        )
        action_types = [fallback_step]
        steps = [
            {
                "index": 1,
                "tool": fallback_step,
                "action_type": fallback_step,
                "description": fallback_step,
                "parameters": {"status": status_text or "failed"},
                "status": "failed",
            }
        ]
        failure_action_rows = [
            {
                "action_type": fallback_step,
                "action_desc": fallback_step,
                "status": "failed",
                "evidence": str(builder_row["error_text"] or ""),
            }
        ]

    action_total = len(steps)
    action_failed = sum(1 for step in steps if str(step.get("status", "")).lower() in {"failed", "error"})
    if action_failed == 0:
        action_failed = 1
    action_failure_rate = (action_failed / action_total) if action_total > 0 else 1.0

    # builder failure は 1 観測として扱う。
    observation_total = 1
    observation_failure_rate = 1.0

    raw_quality_score = builder_row["quality_score"]
    try:
        quality_score = float(raw_quality_score)
    except (TypeError, ValueError):
        quality_score = 0.0
    quality_score = min(max(quality_score, 0.0), 100.0)
    if quality_score <= 0.0:
        quality_score = max(0.0, 100.0 - (((action_failure_rate * 0.45) + (observation_failure_rate * 0.55)) * 100.0))

    builder_type = str(builder_row["builder_type"] or "builder")
    task_type = f"builder-{builder_type}"
    role = "builder"
    error_text = str(builder_row["error_text"] or "")
    failure_type = _classify_failure_type(task_type, error_text, failure_action_rows, [])
    failure_reason = _failure_reason(error_text, failure_action_rows, [], redaction_stats)

    pattern_key = _build_pattern_key(f"{task_type}-failure", action_types + [failure_type])
    pattern_digest = hashlib.sha1(pattern_key.encode("utf-8")).hexdigest()[:8]
    recipe_id = f"recipe-builder-failure-{int(builder_row['id'])}-{pattern_digest}"

    raw_tags = _json_load_or_none(str(builder_row["pattern_tags_json"] or ""))
    pattern_tags = raw_tags if isinstance(raw_tags, list) else []
    tags = sorted(
        {
            f"task:{_slugify(task_type)}",
            "role:builder",
            f"builder:{_slugify(builder_type)}",
            f"failure:{failure_type}",
            *[f"action:{_slugify(item)}" for item in action_types if item],
            *[str(tag) for tag in pattern_tags if str(tag).strip()],
        }
    )

    project_root = _project_root_from_db_path(db_path)
    verification = _collect_verification(str(project_root))

    raw_signature = _json_load_or_none(str(builder_row["input_signature_json"] or ""))
    input_signature = raw_signature if isinstance(raw_signature, dict) else {}

    recipe = {
        "recipe_id": recipe_id,
        "pattern_key": pattern_key,
        "success": False,
        "failure_type": failure_type,
        "steps": sorted(steps, key=lambda item: int(item.get("index", 0))),
        "metrics": {
            "action_count": action_total,
            "action_failure_rate": round(action_failure_rate, 4),
            "observation_total": observation_total,
            "observation_failure_rate": round(observation_failure_rate, 4),
            "quality_score": round(quality_score, 2),
        },
        "classification": {
            "task_type": task_type,
            "role": role,
            "builder_type": builder_type,
            "tags": tags,
        },
        "security": {
            "redaction_applied": True,
            "redacted_fields": int(redaction_stats.get("count", 0)),
            "notes": "global sync 前提で redaction 済み",
        },
        "notes": {
            "failure_reason": failure_reason,
            "recurrence_prevention": _failure_prevention_template(failure_type),
            "applicability": f"builder_type={builder_type} の失敗予防チェックとして再利用しやすい。",
        },
        "verification": verification,
        "source": {
            "origin": "builder_executions",
            "builder_execution_id": str(builder_row["execution_id"] or ""),
            "builder_row_id": int(builder_row["id"]),
            "task_id": str(builder_row["task_id"] or ""),
            "builder_name": _redact(str(builder_row["builder_name"] or ""), redaction_stats),
            "input_signature": _redact(input_signature, redaction_stats),
            "status": status_text or "failed",
            "started_at": str(builder_row["started_at"] or ""),
            "completed_at": str(builder_row["finished_at"] or ""),
            "error_text": _truncate(str(_redact(error_text, redaction_stats)), limit=400),
            "task_run_id": _encode_builder_execution_run_id(int(builder_row["id"])),
        },
        "created_at": _now_iso(),
    }

    validation = _json_load_or_none(str(builder_row["validation_summary_json"] or ""))
    if isinstance(validation, dict) and validation:
        recipe["source"]["validation_summary"] = _redact(validation, redaction_stats)

    recipe["summary"] = _collect_summary(recipe)
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

    recipe["summary"] = _collect_summary(recipe)

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


def from_history(query: str, project_root: str, limit: int = 5) -> dict[str, Any]:
    """履歴 recipe から候補を検索し、失敗パターンは警告として返す。"""
    recipes = list_recipes(project_root)
    if not recipes:
        return {
            "query": str(query or ""),
            "recommendations": [],
            "warnings": [],
            "failure_recipes": [],
        }

    tokens = _history_query_tokens(query)
    scored: list[dict[str, Any]] = []
    for recipe in recipes:
        if not isinstance(recipe, dict):
            continue
        score = _history_recipe_score(tokens, recipe)
        if tokens and score <= 0.0:
            continue
        scored.append({**recipe, "_score": score})

    scored.sort(key=lambda item: float(item.get("_score", 0.0) or 0.0), reverse=True)

    recommendations: list[dict[str, Any]] = []
    warning_messages: list[str] = []
    failure_recipes: list[dict[str, Any]] = []

    for item in scored:
        failure_type = str(item.get("failure_type") or "").strip()
        explicit_success = item.get("success")
        is_failure = explicit_success is False or bool(failure_type)

        if not is_failure:
            clean = dict(item)
            clean.pop("_score", None)
            recommendations.append(clean)
            if len(recommendations) >= max(1, int(limit)):
                break
            continue

        notes = item.get("notes", {}) if isinstance(item.get("notes"), dict) else {}
        source = item.get("source", {}) if isinstance(item.get("source"), dict) else {}
        reason_raw = (
            notes.get("failure_reason")
            or source.get("error_text")
            or source.get("output_log")
            or failure_type
            or "原因不明"
        )
        reason = _truncate(str(_redact(str(reason_raw))), limit=200)
        warning = f"このパターンは過去に失敗しています: {reason}"
        warning_messages.append(warning)

        failure_detail = dict(item)
        failure_detail.pop("_score", None)
        failure_detail["warning"] = warning
        failure_recipes.append(failure_detail)

    return {
        "query": str(query or ""),
        "recommendations": recommendations[: max(1, int(limit))],
        "warnings": warning_messages[: max(1, int(limit))],
        "failure_recipes": failure_recipes[: max(1, int(limit))],
    }


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
    try:
        if all_success:
            task_rows: list[sqlite3.Row] = []
            builder_rows: list[sqlite3.Row] = []
            try:
                task_rows = conn.execute(
                    "SELECT id FROM task_runs WHERE status = 'completed' ORDER BY id ASC"
                ).fetchall()
            except sqlite3.Error:
                task_rows = []
            try:
                builder_rows = conn.execute(
                    """
                    SELECT id
                    FROM builder_executions
                    WHERE success = 1 OR status = 'completed'
                    ORDER BY id ASC
                    """
                ).fetchall()
            except sqlite3.Error:
                builder_rows = []

            run_ids = [int(row["id"]) for row in task_rows]
            run_ids.extend(_encode_builder_execution_run_id(int(row["id"])) for row in builder_rows)
            return run_ids

        if task_id is None:
            row = None
            try:
                row = conn.execute(
                    "SELECT id FROM task_runs WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
                ).fetchone()
            except sqlite3.Error:
                row = None
            if row:
                return [int(row["id"])]

            builder_row = None
            try:
                builder_row = conn.execute(
                    """
                    SELECT id
                    FROM builder_executions
                    WHERE success = 1 OR status = 'completed'
                    ORDER BY
                        CASE WHEN finished_at = '' THEN 1 ELSE 0 END,
                        finished_at DESC,
                        id DESC
                    LIMIT 1
                    """
                ).fetchone()
            except sqlite3.Error:
                builder_row = None
            return [_encode_builder_execution_run_id(int(builder_row["id"]))] if builder_row else []

        value = str(task_id).strip()
        if not value:
            return []

        if value.isdigit():
            row = None
            try:
                row = conn.execute(
                    "SELECT id FROM task_runs WHERE id = ? AND status = 'completed'",
                    (int(value),),
                ).fetchone()
            except sqlite3.Error:
                row = None
            if row:
                return [int(row["id"])]

            builder_row = None
            try:
                builder_row = conn.execute(
                    """
                    SELECT id
                    FROM builder_executions
                    WHERE id = ? AND (success = 1 OR status = 'completed')
                    """,
                    (int(value),),
                ).fetchone()
            except sqlite3.Error:
                builder_row = None
            return [_encode_builder_execution_run_id(int(builder_row["id"]))] if builder_row else []

        row = None
        try:
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
        except sqlite3.Error:
            row = None
        if row:
            return [int(row["id"])]

        builder_row = None
        try:
            builder_row = conn.execute(
                """
                SELECT id
                FROM builder_executions
                WHERE
                    (task_id = ? OR execution_id = ?)
                    AND (success = 1 OR status = 'completed')
                ORDER BY id DESC
                LIMIT 1
                """,
                (value, value),
            ).fetchone()
        except sqlite3.Error:
            builder_row = None

        return [_encode_builder_execution_run_id(int(builder_row["id"]))] if builder_row else []
    finally:
        conn.close()
