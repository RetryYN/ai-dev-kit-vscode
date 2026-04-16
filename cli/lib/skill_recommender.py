#!/usr/bin/env python3
"""HELIX スキル推挙を Codex で実行する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import skill_catalog
from skill_jsonl_schema import JsonlSchemaError, validate_entry


MODEL_NAME = "gpt-5.4-mini"
CACHE_TTL_SECONDS = 3600
NETWORK_EXIT_CODES = {7, 8, 28, 124}


class RecommenderError(RuntimeError):
    """推挙処理の終了コード付きエラー。"""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _repo_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _default_catalog_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "skill-catalog.json"


def _default_cache_dir() -> Path:
    return _repo_root() / ".helix" / "cache" / "recommendations"


def _default_jsonl_catalog_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "skill-catalog.jsonl"


def _default_skills_root() -> Path:
    env_root = os.environ.get("HELIX_SKILLS_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    helix_home = os.environ.get("HELIX_HOME", "").strip()
    if helix_home:
        return Path(helix_home).resolve() / "skills"
    return Path.home() / "ai-dev-kit-vscode" / "skills"


def _template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "skill-search-prompt.md"


def _helix_codex_path() -> str:
    env = os.environ.get("HELIX_CODEX", "").strip()
    if env:
        return env
    return str(Path(__file__).resolve().parents[1] / "helix-codex")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _render_prompt(template: str, vars: dict[str, Any]) -> str:
    rendered = template
    for key, value in vars.items():
        token = "{{" + key + "}}"
        rendered = rendered.replace(token, "null" if value is None else str(value))
    return rendered


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None

    for match in re.finditer(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE):
        candidate = match.group(1).strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        return None

    try:
        parsed = json.loads(text[first : last + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _cache_key(
    task_text: str,
    top_n: int,
    layer_filter: str | None,
    category_filter: str | None,
    catalog_version: str,
    phase_filter: list[str] | None,
    use_no_jsonl: bool,
    jsonl_version: str,
) -> str:
    payload = {
        "task_text": task_text,
        "top_n": top_n,
        "layer_filter": layer_filter or "",
        "category_filter": category_filter or "",
        "catalog_version": catalog_version,
        "phase_filter": phase_filter or [],
        "use_no_jsonl": use_no_jsonl,
        "jsonl_version": jsonl_version,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_is_fresh(path: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    if not path.is_file():
        return False
    return (time.time() - path.stat().st_mtime) <= ttl_seconds


def _load_or_build_catalog(catalog_path: Path) -> dict[str, Any]:
    if catalog_path.is_file():
        return skill_catalog.load_catalog(catalog_path)
    skills_root = _default_skills_root()
    catalog = skill_catalog.build_catalog(skills_root)
    skill_catalog.save_catalog(catalog, catalog_path)
    return catalog


def _filter_catalog(catalog: dict[str, Any], layer_filter: str | None, category_filter: str | None) -> dict[str, Any]:
    skills = []
    for skill in catalog.get("skills", []):
        if not isinstance(skill, dict):
            continue
        if layer_filter and _safe_text(skill.get("helix_layer")) != layer_filter:
            continue
        if category_filter and _safe_text(skill.get("category")) != category_filter:
            continue
        skills.append(skill)

    return {
        "version": catalog.get("version", "1.0"),
        "generated_at": catalog.get("generated_at", ""),
        "skill_count": len(skills),
        "reference_count": sum(len(s.get("references", [])) for s in skills),
        "skills": skills,
    }


def _run_recommender(prompt: str) -> str:
    cmd = [_helix_codex_path(), "--role", "recommender", "--task", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RecommenderError(5, "Codex 呼び出しがタイムアウトしました（60秒）。") from exc
    except OSError as exc:
        raise RecommenderError(3, f"helix-codex の起動に失敗しました: {exc}") from exc

    stderr_text = (proc.stderr or "").strip()
    if stderr_text:
        print(f"[skill_recommender] helix-codex stderr:\n{stderr_text}", file=sys.stderr)

    if proc.returncode != 0:
        if proc.returncode in NETWORK_EXIT_CODES:
            raise RecommenderError(5, f"ネットワークまたはタイムアウトで失敗しました (exit={proc.returncode})。")
        raise RecommenderError(3, f"helix-codex が失敗しました (exit={proc.returncode})。")

    return proc.stdout or ""


def _jsonl_version(path: Path) -> str:
    if not path.is_file():
        return ""
    return str(path.stat().st_mtime_ns)


def _load_jsonl_candidates(
    jsonl_path: Path,
    *,
    phase_filter: list[str] | None = None,
    use_no_jsonl: bool = False,
) -> tuple[list[dict] | None, str | None]:
    """
    Returns (candidates, fallback_reason)
    - JSONL ファイル不在 / parse fail / schema fail / approved/manual 0件
      → (None, reason)
    - 正常: phase_filter で絞込み → (filtered_list, None)
      (filtered_list が 0 件でも JSONL 正常扱い、JSON にフォールバックしない)
    """
    if use_no_jsonl:
        return None, "jsonl_disabled"
    if not jsonl_path.is_file():
        return None, "jsonl_missing"

    non_empty_lines = [line for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    parsed_entries = skill_catalog.read_jsonl_catalog(jsonl_path)
    if len(parsed_entries) != len(non_empty_lines):
        print("[skill_recommender] 警告: JSONL parse failed. JSON fallback を使用します。", file=sys.stderr)
        return None, "jsonl_parse_failed"

    valid_entries: list[dict] = []
    for entry in parsed_entries:
        if not isinstance(entry, dict):
            continue
        try:
            validate_entry(entry, known_task_ids=None)
        except JsonlSchemaError:
            continue
        valid_entries.append(entry)

    if non_empty_lines and not valid_entries:
        print("[skill_recommender] 警告: JSONL schema invalid. JSON fallback を使用します。", file=sys.stderr)
        return None, "jsonl_schema_invalid"

    approved_manual = [
        entry
        for entry in valid_entries
        if str(((entry.get("classification") or {}).get("status") if isinstance(entry.get("classification"), dict) else "")).strip()
        in {"approved", "manual"}
    ]
    if not approved_manual:
        return None, "jsonl_no_approved"

    if not phase_filter:
        return approved_manual, None

    allowed = {phase.strip() for phase in phase_filter if phase.strip()}
    filtered: list[dict] = []
    for entry in approved_manual:
        phases = entry.get("phases")
        if not isinstance(phases, list):
            continue
        if any(str(phase).strip() in allowed for phase in phases):
            filtered.append(entry)
    return filtered, None


def _jsonl_prompt_lines(entries: list[dict]) -> str:
    return "\n".join(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) for entry in entries)


def _normalize_references(refs: Any) -> list[str]:
    if not isinstance(refs, list):
        return []

    normalized: list[str] = []
    for ref in refs:
        if isinstance(ref, dict):
            path = _safe_text(ref.get("path")).strip()
            if path:
                normalized.append(path)
            continue
        text = _safe_text(ref).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_result(data: dict[str, Any], top_n: int, task_text: str) -> dict[str, Any]:
    normalized_candidates: list[dict[str, Any]] = []
    raw_candidates = data.get("recommendations")
    if not isinstance(raw_candidates, list):
        raw_candidates = data.get("candidates", [])
    if isinstance(raw_candidates, list):
        for index, item in enumerate(raw_candidates):
            if not isinstance(item, dict):
                continue
            skill_id = _safe_text(item.get("skill_id")).strip()
            if not skill_id:
                continue
            try:
                score = float(item.get("score", 0.0))
            except (TypeError, ValueError):
                score = 1.0 - (index / max(len(raw_candidates), 1))
            score = max(0.0, min(1.0, score))
            normalized_candidates.append(
                {
                    "skill_id": skill_id,
                    "score": score,
                    "reason": _safe_text(item.get("reason") or item.get("match_reason")).strip(),
                    "references": _normalize_references(item.get("references", [])),
                    "recommended_agent": _safe_text(item.get("recommended_agent")).strip(),
                }
            )

    normalized_candidates = normalized_candidates[: max(top_n, 0)]

    no_match_reason: str | None
    raw_reason = data.get("no_match_reason")
    if raw_reason is None:
        no_match_reason = None
    else:
        text = _safe_text(raw_reason).strip()
        no_match_reason = text or None

    task_summary = _safe_text(data.get("task_summary")).strip() or task_text.strip()

    return {
        "candidates": normalized_candidates,
        "task_summary": task_summary,
        "no_match_reason": no_match_reason,
    }


def _overwrite_agents_with_jsonl(result: dict[str, Any], jsonl_candidates: list[dict]) -> None:
    agent_map: dict[str, str] = {}
    for entry in jsonl_candidates:
        if not isinstance(entry, dict):
            continue
        skill_id = _safe_text(entry.get("id")).strip()
        agent = _safe_text(entry.get("agent")).strip()
        if skill_id and agent:
            agent_map[skill_id] = agent

    for item in result.get("candidates", []):
        if not isinstance(item, dict):
            continue
        skill_id = _safe_text(item.get("skill_id")).strip()
        if skill_id in agent_map:
            item["recommended_agent"] = agent_map[skill_id]


def recommend(
    task_text: str,
    top_n: int = 5,
    layer_filter: str | None = None,
    category_filter: str | None = None,
    catalog_path: Path | None = None,
    cache_dir: Path | None = None,
    jsonl_catalog_path: Path | None = None,
    phase_filter: list[str] | None = None,
    use_no_jsonl: bool = False,
    force_refresh: bool = False,
) -> dict[str, Any]:
    if not task_text.strip():
        raise RecommenderError(2, "task_text が空です。")

    resolved_catalog_path = (catalog_path or _default_catalog_path()).resolve()
    resolved_cache_dir = (cache_dir or _default_cache_dir()).resolve()
    resolved_jsonl_path = (jsonl_catalog_path or _default_jsonl_catalog_path()).resolve()
    catalog = _load_or_build_catalog(resolved_catalog_path)
    filtered_catalog = _filter_catalog(catalog, layer_filter, category_filter)
    catalog_version = _safe_text(catalog.get("version") or "1.0")
    jsonl_candidates, fallback_reason = _load_jsonl_candidates(
        resolved_jsonl_path,
        phase_filter=phase_filter,
        use_no_jsonl=use_no_jsonl,
    )
    is_jsonl_mode = jsonl_candidates is not None and fallback_reason is None
    if fallback_reason and fallback_reason != "jsonl_disabled":
        print(f"[skill_recommender] debug: JSONL fallback reason={fallback_reason}", file=sys.stderr)

    key = _cache_key(
        task_text,
        top_n,
        layer_filter,
        category_filter,
        catalog_version,
        phase_filter,
        use_no_jsonl,
        _jsonl_version(resolved_jsonl_path),
    )
    cache_file = resolved_cache_dir / f"{key}.json"

    if not force_refresh and _cache_is_fresh(cache_file):
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        if isinstance(cached, dict):
            cached["_cached"] = True
            cached["_model"] = MODEL_NAME
            return cached

    template = _template_path().read_text(encoding="utf-8")
    prompt = _render_prompt(
        template,
        {
            "TASK_TEXT": task_text,
            "TOP_N": top_n,
            "LAYER_FILTER": layer_filter,
            "CATEGORY_FILTER": category_filter,
            "jsonl_candidates": _jsonl_prompt_lines(jsonl_candidates or []) if is_jsonl_mode else "",
            "skill_catalog": "" if is_jsonl_mode else json.dumps(filtered_catalog, ensure_ascii=False, separators=(",", ":")),
            "CATALOG_JSON": json.dumps(filtered_catalog, ensure_ascii=False, separators=(",", ":")),
        },
    )

    raw_output = _run_recommender(prompt)
    extracted = _extract_json(raw_output)
    if extracted is None:
        retry_prompt = prompt + "\n\n重要: JSON 形式厳守。JSON 以外の文字を一切出力しないこと。"
        raw_output = _run_recommender(retry_prompt)
        extracted = _extract_json(raw_output)
    if extracted is None:
        raise RecommenderError(4, "推挙結果の JSON 解析に失敗しました。")

    result = _normalize_result(extracted, top_n, task_text)
    if is_jsonl_mode and jsonl_candidates is not None:
        _overwrite_agents_with_jsonl(result, jsonl_candidates)
    result["_cached"] = False
    result["_model"] = MODEL_NAME

    resolved_cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HELIX スキル推挙 CLI")
    parser.add_argument("--task", required=True, help="タスク記述")
    parser.add_argument("--top-n", type=int, default=5, help="上位候補数")
    parser.add_argument("--layer", default=None, help="helix_layer フィルタ")
    parser.add_argument("--category", default=None, help="category フィルタ")
    parser.add_argument("--phase", default=None, help="phase フィルタ（カンマ区切り）")
    parser.add_argument("--json", action="store_true", help="JSON のみ出力")
    parser.add_argument("--no-cache", action="store_true", help="推挙キャッシュを無視")
    parser.add_argument("--no-jsonl", action="store_true", help="JSONL を使わず JSON mode を強制")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    phase_filter = [part.strip() for part in (args.phase or "").split(",") if part.strip()] or None
    try:
        result = recommend(
            task_text=args.task,
            top_n=max(1, args.top_n),
            layer_filter=args.layer,
            category_filter=args.category,
            phase_filter=phase_filter,
            use_no_jsonl=args.no_jsonl,
            force_refresh=args.no_cache,
        )
    except RecommenderError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return exc.code

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"検索: {result.get('task_summary', '').strip() or args.task.strip()}")
    print("")
    candidates = result.get("candidates", [])
    if not candidates:
        reason = result.get("no_match_reason") or "該当スキルは見つかりませんでした。"
        print(f"候補なし: {reason}")
        return 0

    for i, cand in enumerate(candidates, start=1):
        refs = cand.get("references", [])
        refs_text = ", ".join(refs) if refs else "なし"
        print(f"{i}. [{cand.get('skill_id', '')}] score {float(cand.get('score', 0.0)):.2f}  agent: {cand.get('recommended_agent', '')}")
        print(f"   reason: {cand.get('reason', '')}")
        print(f"   refs ({len(refs)}): {refs_text}")
        print("")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
