#!/usr/bin/env python3
"""HELIX スキル推挙を Codex で実行する。"""
from __future__ import annotations

import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
from typing import Any

import skill_catalog
from model_registry import resolve_role_model
from skill_jsonl_schema import ALLOWED_AGENTS, JsonlSchemaError, validate_entry

try:
    from .defaults_loader import load_defaults
    from .llm_classifier_base import CodexResponseError, LLMClassifierBase
except ImportError:  # pragma: no cover
    from defaults_loader import load_defaults
    from llm_classifier_base import CodexResponseError, LLMClassifierBase

MODEL_NAME = resolve_role_model("recommender", default="gpt-5.4-mini")
_DEFAULTS = load_defaults()
CACHE_TTL_SECONDS = _DEFAULTS["recommender"]["cache_ttl_sec"]
NETWORK_EXIT_CODES = {7, 8, 28, 124}


class RecommenderError(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _repo_root() -> Path:
    return Path(os.environ.get("HELIX_PROJECT_ROOT") or Path(__file__).resolve().parents[2]).resolve()


def _default_catalog_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "skill-catalog.json"


def _default_cache_dir() -> Path:
    return _repo_root() / ".helix" / "cache" / "recommendations"


def _default_jsonl_catalog_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "skill-catalog.jsonl"


def _default_skills_root() -> Path:
    if os.environ.get("HELIX_SKILLS_ROOT"):
        return Path(os.environ["HELIX_SKILLS_ROOT"]).resolve()
    return Path(os.environ["HELIX_HOME"]).resolve() / "skills" if os.environ.get("HELIX_HOME") else Path.home() / "ai-dev-kit-vscode" / "skills"


def _template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "prompts" / "skill-search.md"


def _helix_codex_path() -> str:
    return os.environ.get("HELIX_CODEX", "").strip() or str(Path(__file__).resolve().parents[1] / "helix-codex")


def _safe_text(value: Any) -> str:
    return "" if value is None else str(value)


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    for match in re.finditer(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, flags=re.IGNORECASE):
        try:
            parsed = json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    first, last = text.find("{"), text.rfind("}")
    if first == -1 or last == -1 or first >= last:
        return None
    try:
        parsed = json.loads(text[first : last + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _cache_key(task_text: str, top_n: int, layer_filter: str | None, category_filter: str | None, catalog_version: str, phase_filter: list[str] | None, use_no_jsonl: bool, jsonl_version: str) -> str:
    payload = {"task_text": task_text, "top_n": top_n, "layer_filter": layer_filter or "", "category_filter": category_filter or "", "catalog_version": catalog_version, "phase_filter": phase_filter or [], "use_no_jsonl": use_no_jsonl, "jsonl_version": jsonl_version}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _gc_expired_cache(cache_dir: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> int:
    now, removed = time.time(), 0
    for cache_file in cache_dir.glob("*.json"):
        try:
            if now - cache_file.stat().st_mtime > ttl_seconds:
                cache_file.unlink()
                removed += 1
        except OSError:
            pass
    return removed


def _load_or_build_catalog(catalog_path: Path) -> dict[str, Any]:
    if catalog_path.is_file():
        return skill_catalog.load_catalog(catalog_path)
    catalog = skill_catalog.build_catalog(_default_skills_root())
    skill_catalog.save_catalog(catalog, catalog_path)
    return catalog


def _filter_catalog(catalog: dict[str, Any], layer_filter: str | None, category_filter: str | None) -> dict[str, Any]:
    skills = [s for s in catalog.get("skills", []) if isinstance(s, dict) and (not layer_filter or _safe_text(s.get("helix_layer")) == layer_filter) and (not category_filter or _safe_text(s.get("category")) == category_filter)]
    return {"version": catalog.get("version", "1.0"), "generated_at": catalog.get("generated_at", ""), "skill_count": len(skills), "reference_count": sum(len(s.get("references", [])) for s in skills), "skills": skills}


def _run_recommender(prompt: str) -> str:
    cmd = [_helix_codex_path(), "--role", "recommender", "--task", prompt]
    env = os.environ.copy()
    # recommender は書き込みを行わないため、親の CODEX_BIN を子 helix-codex へ引き継がない。
    env.pop("CODEX_BIN", None)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, check=False, env=env)
    except subprocess.TimeoutExpired as exc:
        raise RecommenderError(5, "Codex 呼び出しがタイムアウトしました（1800秒）。") from exc
    except OSError as exc:
        raise RecommenderError(3, f"helix-codex の起動に失敗しました: {exc}") from exc
    if (proc.stderr or "").strip():
        print(f"[skill_recommender] helix-codex stderr:\n{proc.stderr.strip()}", file=sys.stderr)
    if proc.returncode != 0:
        if proc.returncode in NETWORK_EXIT_CODES:
            raise RecommenderError(5, f"ネットワークまたはタイムアウトで失敗しました (exit={proc.returncode})。")
        raise RecommenderError(3, f"helix-codex が失敗しました (exit={proc.returncode})。")
    return proc.stdout or ""


def _jsonl_version(path: Path) -> str:
    return str(path.stat().st_mtime_ns) if path.is_file() else ""


def _load_jsonl_candidates(jsonl_path: Path, *, phase_filter: list[str] | None = None, use_no_jsonl: bool = False) -> tuple[list[dict] | None, str | None]:
    if use_no_jsonl:
        return None, "jsonl_disabled"
    if not jsonl_path.is_file():
        return None, "jsonl_missing"
    non_empty = [line for line in jsonl_path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    parse_failures = sum(1 for raw in non_empty if _extract_json(raw) is None)
    parsed_entries = skill_catalog.read_jsonl_catalog(jsonl_path)
    if parse_failures and not parsed_entries:
        print("[skill_recommender] 警告: JSONL parse failed. JSON fallback を使用します。", file=sys.stderr)
        return None, "jsonl_parse_failed"
    if parse_failures:
        print("[skill_recommender] 警告: JSONL parse failed. 有効行のみで継続します。", file=sys.stderr)
    valid_entries = []
    for entry in parsed_entries:
        try:
            if isinstance(entry, dict):
                validate_entry(entry, known_task_ids=None)
                valid_entries.append(entry)
        except JsonlSchemaError:
            pass
    if non_empty and not valid_entries:
        print("[skill_recommender] 警告: JSONL schema invalid. JSON fallback を使用します。", file=sys.stderr)
        return None, "jsonl_schema_invalid"
    approved = [e for e in valid_entries if str(((e.get("classification") or {}).get("status") if isinstance(e.get("classification"), dict) else "")).strip() in {"approved", "manual"}]
    if not approved:
        return None, "jsonl_no_approved"
    if not phase_filter:
        return approved, None
    allowed = {p.strip() for p in phase_filter if p.strip()}
    return [e for e in approved if any(str(p).strip() in allowed for p in e.get("phases", []))], None


def _jsonl_prompt_lines(entries: list[dict]) -> str:
    return "\n".join(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) for entry in entries)


def _normalize_references(refs: Any) -> list[str]:
    out = []
    for ref in refs if isinstance(refs, list) else []:
        text = _safe_text(ref.get("path") if isinstance(ref, dict) else ref).strip()
        if text:
            out.append(text)
    return out


def _normalize_agent_name(value: Any) -> str:
    text = _safe_text(value).strip()
    match = re.fullmatch(r"helix-codex\s+--role\s+([a-z][a-z0-9-]*)", text)
    text = match.group(1) if match else text
    return text if text in ALLOWED_AGENTS else ""


def _normalize_result(data: dict[str, Any], top_n: int, task_text: str) -> dict[str, Any]:
    raw_candidates = data.get("recommendations") if isinstance(data.get("recommendations"), list) else data.get("candidates", [])
    candidates = []
    for index, item in enumerate(raw_candidates if isinstance(raw_candidates, list) else []):
        if not isinstance(item, dict) or not _safe_text(item.get("skill_id")).strip():
            continue
        try:
            score = float(item.get("score", 0.0))
        except (TypeError, ValueError):
            score = 1.0 - (index / max(len(raw_candidates), 1))
        candidates.append({"skill_id": _safe_text(item.get("skill_id")).strip(), "score": max(0.0, min(1.0, score)), "reason": _safe_text(item.get("reason") or item.get("match_reason")).strip(), "references": _normalize_references(item.get("references", [])), "recommended_agent": _normalize_agent_name(item.get("recommended_agent"))})
    raw_reason = data.get("no_match_reason")
    return {"candidates": candidates[: max(top_n, 0)], "task_summary": _safe_text(data.get("task_summary")).strip() or task_text.strip(), "no_match_reason": None if raw_reason is None else (_safe_text(raw_reason).strip() or None)}


def _overwrite_agents_with_jsonl(result: dict[str, Any], jsonl_candidates: list[dict]) -> None:
    agent_map = {_safe_text(e.get("id")).strip(): _safe_text(e.get("agent")).strip() for e in jsonl_candidates if isinstance(e, dict)}
    for item in result.get("candidates", []):
        skill_id = _safe_text(item.get("skill_id")).strip()
        if skill_id in agent_map and agent_map[skill_id]:
            item["recommended_agent"] = agent_map[skill_id]


def _normalize_commands(value: Any) -> list[str]:
    return [_safe_text(item).strip() for item in value if _safe_text(item).strip()] if isinstance(value, list) else []


def _attach_catalog_commands(result: dict[str, Any], catalog: dict[str, Any]) -> None:
    command_map = {_safe_text(s.get("id")).strip(): _normalize_commands(s.get("commands")) for s in catalog.get("skills", []) if isinstance(s, dict)}
    for candidate in result.get("candidates", []):
        candidate["commands"] = list(command_map.get(_safe_text(candidate.get("skill_id")).strip(), []))


class SkillRecommender(LLMClassifierBase):
    role = MODEL_NAME
    classifier_name = "skill_recommender"
    cache_ttl_sec = CACHE_TTL_SECONDS

    def __init__(self, db_path: Path | None = None) -> None:
        super().__init__(db_path=db_path)
        self._cache_hit, self._top_n, self._task_text = False, 5, ""

    def _cache_key(self, query: str, context: dict | None) -> str:
        c = context or {}
        return _cache_key(query, int(c.get("top_n", 5)), c.get("layer_filter"), c.get("category_filter"), _safe_text(c.get("catalog_version") or "1.0"), c.get("phase_filter"), bool(c.get("use_no_jsonl", False)), _safe_text(c.get("jsonl_version") or ""))

    def _cache_lookup(self, key: str) -> dict | None:
        self._cache_hit = False
        data = super()._cache_lookup(key)
        self._cache_hit = data is not None
        return data

    def _cache_store(self, key: str, value: dict) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[skill_recommender] cache gc removed={_gc_expired_cache(self.cache_dir, CACHE_TTL_SECONDS)}", file=sys.stderr)
        path = self.cache_dir / f"{key}.json"
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp_path, path)

    def _build_prompt(self, query: str, context: dict | None) -> str:
        return _safe_text((context or {}).get("prompt"))

    def _invoke_codex(self, query: str, context: dict | None) -> str:
        prompt = self._build_prompt(query, context)
        raw = _run_recommender(prompt)
        return raw if _extract_json(raw) is not None else _run_recommender(prompt + "\n\n重要: JSON 形式厳守。JSON 以外の文字を一切出力しないこと。")

    def _parse_response(self, raw: str) -> dict:
        extracted = _extract_json(raw)
        if extracted is None:
            raise CodexResponseError("recommendation JSON parse failed")
        return _normalize_result(extracted, self._top_n, self._task_text)


def recommend(task_text: str, top_n: int = 5, layer_filter: str | None = None, category_filter: str | None = None, catalog_path: Path | None = None, cache_dir: Path | None = None, jsonl_catalog_path: Path | None = None, phase_filter: list[str] | None = None, use_no_jsonl: bool = False, force_refresh: bool = False) -> dict[str, Any]:
    if not task_text.strip():
        raise RecommenderError(2, "task_text が空です。")
    resolved_catalog_path = (catalog_path or _default_catalog_path()).resolve()
    resolved_cache_dir = (cache_dir or _default_cache_dir()).resolve()
    resolved_jsonl_path = (jsonl_catalog_path or _default_jsonl_catalog_path()).resolve()
    catalog = _load_or_build_catalog(resolved_catalog_path)
    filtered_catalog = _filter_catalog(catalog, layer_filter, category_filter)
    jsonl_candidates, fallback_reason = _load_jsonl_candidates(resolved_jsonl_path, phase_filter=phase_filter, use_no_jsonl=use_no_jsonl)
    is_jsonl_mode = jsonl_candidates is not None and fallback_reason is None
    if fallback_reason and fallback_reason != "jsonl_disabled":
        print(f"[skill_recommender] debug: JSONL fallback reason={fallback_reason}", file=sys.stderr)
    classifier = SkillRecommender()
    prompt = classifier._render_prompt(_template_path(), {
        "TASK_TEXT": task_text, "TOP_N": str(top_n),
        "LAYER_FILTER": "null" if layer_filter is None else layer_filter,
        "CATEGORY_FILTER": "null" if category_filter is None else category_filter,
        "jsonl_candidates": _jsonl_prompt_lines(jsonl_candidates or []) if is_jsonl_mode else "",
        "skill_catalog": "" if is_jsonl_mode else json.dumps(filtered_catalog, ensure_ascii=False, separators=(",", ":")),
        "CATALOG_JSON": json.dumps(filtered_catalog, ensure_ascii=False, separators=(",", ":")),
    })
    classifier.cache_dir = resolved_cache_dir
    classifier.cache_ttl_sec = -1 if force_refresh else CACHE_TTL_SECONDS
    classifier._top_n, classifier._task_text = top_n, task_text
    context = {"top_n": top_n, "layer_filter": layer_filter, "category_filter": category_filter, "catalog_version": _safe_text(catalog.get("version") or "1.0"), "phase_filter": phase_filter, "use_no_jsonl": use_no_jsonl, "jsonl_version": _jsonl_version(resolved_jsonl_path), "prompt": prompt}
    try:
        result = classifier.classify(task_text, context)
    except CodexResponseError as exc:
        raise RecommenderError(4, "推挙結果の JSON 解析に失敗しました。") from exc
    if is_jsonl_mode and jsonl_candidates is not None:
        _overwrite_agents_with_jsonl(result, jsonl_candidates)
    _attach_catalog_commands(result, catalog)
    result["_cached"], result["_model"] = classifier._cache_hit, MODEL_NAME
    return result


def skill_search(query: str, n: int = 5) -> list[dict[str, Any]]:
    return [{"id": c.get("skill_id"), "score": c.get("score"), "agent": c.get("recommended_agent")} for c in recommend(query, top_n=n).get("candidates", [])]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HELIX スキル推挙 CLI")
    for flags, kwargs in [
        (("--task",), {"required": True, "help": "タスク記述"}),
        (("--top-n",), {"type": int, "default": 5, "help": "上位候補数"}),
        (("--layer",), {"default": None, "help": "helix_layer フィルタ"}),
        (("--category",), {"default": None, "help": "category フィルタ"}),
        (("--phase",), {"default": None, "help": "phase フィルタ（カンマ区切り）"}),
    ]:
        parser.add_argument(*flags, **kwargs)
    parser.add_argument("--json", action="store_true", help="JSON のみ出力")
    parser.add_argument("--no-cache", action="store_true", help="推挙キャッシュを無視")
    parser.add_argument("--no-jsonl", action="store_true", help="JSONL を使わず JSON mode を強制")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    phase_filter = [part.strip() for part in (args.phase or "").split(",") if part.strip()] or None
    try:
        result = recommend(task_text=args.task, top_n=max(1, args.top_n), layer_filter=args.layer, category_filter=args.category, phase_filter=phase_filter, use_no_jsonl=args.no_jsonl, force_refresh=args.no_cache)
    except RecommenderError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return exc.code
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"検索: {result.get('task_summary', '').strip() or args.task.strip()}\n")
    if not result.get("candidates", []):
        print(f"候補なし: {result.get('no_match_reason') or '該当スキルは見つかりませんでした。'}")
        return 0
    for i, cand in enumerate(result["candidates"], start=1):
        refs, commands = cand.get("references", []), cand.get("commands", [])
        print(f"{i}. [{cand.get('skill_id', '')}] score {float(cand.get('score', 0.0)):.2f}  agent: {cand.get('recommended_agent', '')}")
        print(f"   reason: {cand.get('reason', '')}")
        print(f"   refs ({len(refs)}): {', '.join(refs) if refs else 'なし'}")
        print(f"   関連コマンド: {' | '.join(commands) if isinstance(commands, list) and commands else 'なし'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
