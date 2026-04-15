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
) -> str:
    payload = {
        "task_text": task_text,
        "top_n": top_n,
        "layer_filter": layer_filter or "",
        "category_filter": category_filter or "",
        "catalog_version": catalog_version,
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


def _normalize_result(data: dict[str, Any], top_n: int, task_text: str) -> dict[str, Any]:
    normalized_candidates: list[dict[str, Any]] = []
    raw_candidates = data.get("candidates", [])
    if isinstance(raw_candidates, list):
        for item in raw_candidates:
            if not isinstance(item, dict):
                continue
            skill_id = _safe_text(item.get("skill_id")).strip()
            if not skill_id:
                continue
            try:
                score = float(item.get("score", 0.0))
            except (TypeError, ValueError):
                score = 0.0
            score = max(0.0, min(1.0, score))
            refs = item.get("references", [])
            if not isinstance(refs, list):
                refs = []
            normalized_candidates.append(
                {
                    "skill_id": skill_id,
                    "score": score,
                    "reason": _safe_text(item.get("reason")).strip(),
                    "references": [_safe_text(ref).strip() for ref in refs if _safe_text(ref).strip()],
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


def recommend(
    task_text: str,
    top_n: int = 5,
    layer_filter: str | None = None,
    category_filter: str | None = None,
    catalog_path: Path | None = None,
    cache_dir: Path | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    if not task_text.strip():
        raise RecommenderError(2, "task_text が空です。")

    resolved_catalog_path = (catalog_path or _default_catalog_path()).resolve()
    resolved_cache_dir = (cache_dir or _default_cache_dir()).resolve()
    catalog = _load_or_build_catalog(resolved_catalog_path)
    filtered_catalog = _filter_catalog(catalog, layer_filter, category_filter)
    catalog_version = _safe_text(catalog.get("version") or "1.0")

    key = _cache_key(task_text, top_n, layer_filter, category_filter, catalog_version)
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
    parser.add_argument("--json", action="store_true", help="JSON のみ出力")
    parser.add_argument("--no-cache", action="store_true", help="推挙キャッシュを無視")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = recommend(
            task_text=args.task,
            top_n=max(1, args.top_n),
            layer_filter=args.layer,
            category_filter=args.category,
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
