#!/usr/bin/env python3
"""HELIX code index の流用候補を Codex で推挙する。"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from .defaults_loader import load_defaults
    from . import helix_db
    from .model_registry import resolve_role_model
except ImportError:  # pragma: no cover - script execution fallback
    from defaults_loader import load_defaults
    import helix_db
    from model_registry import resolve_role_model


MODEL_NAME = resolve_role_model("recommender", default="gpt-5.4-mini")
_DEFAULTS = load_defaults()
CACHE_TTL_SECONDS = _DEFAULTS["recommender"]["cache_ttl_sec"]
NETWORK_EXIT_CODES = {7, 8, 28, 124}
_ENTRYPOINT_GUARD_RE = re.compile(r"if\s+__name__\s*==\s*(['\"])__main__\1")


# @helix:index id=code-recommender.code-recommender-error domain=cli/lib summary=CodeRecommenderErrorクラス
class CodeRecommenderError(RuntimeError):
    """コード推挙処理の終了コード付きエラー。"""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _repo_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _default_cache_dir() -> Path:
    return _repo_root() / ".helix" / "cache" / "recommendations" / "code"


def _template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "prompts" / "code-search.md"


def _helix_codex_path() -> str:
    env = os.environ.get("HELIX_CODEX", "").strip()
    if env:
        return env
    return str(Path(__file__).resolve().parents[1] / "helix-codex")


def _default_catalog_jsonl_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "code-catalog.jsonl"


def _catalog_fingerprint(jsonl_path: Path) -> str:
    if not jsonl_path.is_file():
        return "no-catalog"
    try:
        stat = jsonl_path.stat()
    except OSError:
        return "no-catalog"
    return f"{stat.st_mtime_ns}:{stat.st_size}"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _repo_relative_path(entry: dict[str, Any]) -> Path:
    return Path(_safe_text(entry.get("path")).strip())


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _module_name_for_path(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def _symbol_at_line(path: Path, line_no: int) -> tuple[str, str]:
    if line_no <= 0:
        return "", ""
    text = _read_text(path)
    if not text:
        return "", ""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "", ""

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if node.lineno != line_no:
            continue
        kind = "class" if isinstance(node, ast.ClassDef) else "function"
        return node.name, kind

    return "", ""


def _has_entrypoint_guard(path: Path) -> bool:
    text = _read_text(path)
    return bool(text and _ENTRYPOINT_GUARD_RE.search(text))


def _is_entrypoint_main(entry: dict[str, Any]) -> bool:
    rel_path = _repo_relative_path(entry)
    if not rel_path.as_posix():
        return False

    symbol_line = 0
    try:
        symbol_line = int(entry.get("symbol_line") or entry.get("line_no") or 0)
    except (TypeError, ValueError):
        symbol_line = 0

    if symbol_line <= 0:
        return False

    symbol_name, kind = _symbol_at_line(_repo_root() / rel_path, symbol_line)
    if symbol_name != "main" or kind != "function":
        return False

    module_name = _module_name_for_path(rel_path)
    return module_name.endswith("__main__") or _has_entrypoint_guard(_repo_root() / rel_path)


def _cache_key(query: str, top_n: int, catalog_fingerprint: str = "", bucket: str = "coverage_eligible") -> str:
    payload = {"query": query, "n": top_n, "catalog_fingerprint": catalog_fingerprint, "bucket": bucket}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_is_fresh(path: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
    if not path.is_file():
        return False
    return (time.time() - path.stat().st_mtime) <= ttl_seconds


def _gc_expired_cache(cache_dir: Path, ttl_seconds: int = CACHE_TTL_SECONDS) -> int:
    now = time.time()
    removed = 0
    for cache_file in cache_dir.glob("*.json"):
        try:
            if now - cache_file.stat().st_mtime > ttl_seconds:
                cache_file.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def _fetch_entries(db_path: str | Path | None = None, *, bucket: str = "coverage_eligible") -> list[dict[str, Any]]:
    if bucket not in {"coverage_eligible", "private_helper", "excluded", "all"}:
        raise CodeRecommenderError(2, f"unsupported bucket: {bucket}")

    resolved_db_path = str(db_path or helix_db.resolve_default_db_path())
    helix_db._prepare_db_path(resolved_db_path)
    conn = helix_db._connect(resolved_db_path)
    helix_db._ensure_schema(conn)
    conn.row_factory = sqlite3.Row
    try:
        sql = """
            SELECT id, domain, summary, path, line_no, symbol_line, since, related, bucket
            FROM code_index
        """
        params: list[str] = []
        if bucket != "all":
            sql += " WHERE bucket = ?"
            params.append(bucket)
        sql += " ORDER BY id"
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _summary_tokens(summary: str) -> set[str]:
    return {part for part in re.split(r"[\s_\-./()]+", summary.lower()) if part}


def _entry_lines(entries: list[dict[str, Any]]) -> str:
    """Return prompt input using only the allowed metadata fields."""
    lines: list[str] = []
    for entry in entries:
        entry_id = _safe_text(entry.get("id")).replace("|", "/").strip()
        domain = _safe_text(entry.get("domain")).replace("|", "/").strip()
        path = _safe_text(entry.get("path")).replace("|", "/").strip()
        line_no = _safe_text(entry.get("line_no")).strip()
        summary = re.sub(r"\s+", " ", _safe_text(entry.get("summary")).replace("|", "/")).strip()
        if entry_id and domain and path and line_no and summary:
            lines.append(f"{entry_id}|{domain}|{path}:{line_no}|{summary}")
    return "\n".join(lines)


def _render_prompt(template: str, query: str, top_n: int, entries: str) -> str:
    return (
        template.replace("{QUERY}", query)
        .replace("{N}", str(top_n))
        .replace("{ENTRIES}", entries)
        .replace("{{QUERY}}", query)
        .replace("{{N}}", str(top_n))
        .replace("{{ENTRIES}}", entries)
    )


def _extract_json(text: str) -> Any | None:
    if not text:
        return None

    for match in re.finditer(r"```(?:json)?\s*([\[{][\s\S]*?[\]}])\s*```", text, flags=re.IGNORECASE):
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue

    starts = [pos for pos in (text.find("{"), text.find("[")) if pos != -1]
    if not starts:
        return None
    first = min(starts)
    last_obj = text.rfind("}")
    last_arr = text.rfind("]")
    last = max(last_obj, last_arr)
    if last == -1 or first >= last:
        return None

    try:
        return json.loads(text[first : last + 1])
    except json.JSONDecodeError:
        return None


def _run_recommender(prompt: str) -> str:
    cmd = [_helix_codex_path(), "--role", "recommender", "--task", prompt]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, check=False)
    except subprocess.TimeoutExpired as exc:
        raise CodeRecommenderError(5, "Codex 呼び出しがタイムアウトしました（1800秒）。") from exc
    except OSError as exc:
        raise CodeRecommenderError(5, f"helix-codex の起動に失敗しました: {exc}") from exc

    stderr_text = (proc.stderr or "").strip()
    if stderr_text:
        print(f"[code_recommender] helix-codex stderr:\n{stderr_text}", file=sys.stderr)

    if proc.returncode != 0:
        if proc.returncode in NETWORK_EXIT_CODES:
            raise CodeRecommenderError(5, f"ネットワークまたはタイムアウトで失敗しました (exit={proc.returncode})。")
        raise CodeRecommenderError(5, f"helix-codex が失敗しました (exit={proc.returncode})。")

    return proc.stdout or ""


def _coerce_score(value: Any, fallback: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = fallback
    return max(0.0, min(1.0, score))


def _normalize_result(data: Any, top_n: int) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        raw_items = data.get("recommendations")
        if not isinstance(raw_items, list):
            raw_items = data.get("candidates")
        if not isinstance(raw_items, list):
            raw_items = data.get("results")
    else:
        raw_items = data
    if not isinstance(raw_items, list):
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        entry_id = _safe_text(item.get("id") or item.get("code_id") or item.get("entry_id") or item.get("skill_id")).strip()
        if not entry_id or entry_id in seen:
            continue
        seen.add(entry_id)
        normalized.append(
            {
                "id": entry_id,
                "score": _coerce_score(item.get("score"), 1.0 - (index / max(len(raw_items), 1))),
                "reason": _safe_text(item.get("reason") or item.get("match_reason")).strip(),
            }
        )
    return normalized[: max(top_n, 0)]


def _attach_entry_metadata(candidates: list[dict[str, Any]], entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {_safe_text(entry.get("id")): entry for entry in entries}
    enriched: list[dict[str, Any]] = []
    for candidate in candidates:
        entry_id = _safe_text(candidate.get("id")).strip()
        entry = by_id.get(entry_id)
        if entry is None:
            continue
        enriched.append(
            {
                "id": entry_id,
                "domain": _safe_text(entry.get("domain")).strip(),
                "summary": _safe_text(entry.get("summary")).strip(),
                "path": _safe_text(entry.get("path")).strip(),
                "line_no": entry.get("line_no") or "",
                "score": _coerce_score(candidate.get("score"), 0.0),
                "reason": _safe_text(candidate.get("reason")).strip(),
            }
        )
    return enriched


def _query_terms(query: str) -> list[str]:
    lowered = query.lower().strip()
    terms = [part for part in re.split(r"[\s_\-./:()]+", lowered) if part]
    if lowered and lowered not in terms:
        terms.append(lowered)
    return terms


def _local_lexical_fallback(query: str, top_n: int, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms = _query_terms(query)
    if not terms:
        return []

    scored: list[dict[str, Any]] = []
    for entry in entries:
        haystack = " ".join(
            _safe_text(entry.get(field)).lower()
            for field in ("id", "domain", "summary", "path")
        )
        matched = [term for term in terms if term in haystack]
        if not matched:
            continue
        score = min(1.0, len(set(matched)) / max(len(set(terms)), 1))
        scored.append(
            {
                "id": _safe_text(entry.get("id")).strip(),
                "score": score,
                "reason": f"local lexical match: {', '.join(sorted(set(matched))[:3])}",
            }
        )

    scored.sort(key=lambda item: (-float(item.get("score", 0.0)), _safe_text(item.get("id"))))
    return scored[: max(top_n, 0)]


def _load_fresh_cache(cache_file: Path, top_n: int, entries: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    if not _cache_is_fresh(cache_file):
        return None
    cached = json.loads(cache_file.read_text(encoding="utf-8"))
    return _attach_entry_metadata(_normalize_result(cached, top_n), entries)


def _write_cache(cache_file: Path, normalized: list[dict[str, Any]]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    removed = _gc_expired_cache(cache_file.parent, CACHE_TTL_SECONDS)
    print(f"[code_recommender] cache gc removed={removed}", file=sys.stderr)
    tmp_path = cache_file.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, cache_file)


# @helix:index id=code-recommender.find-code domain=cli/lib summary=codeを検索する
def find_code(query: str, n: int = 5, *, bucket: str = "coverage_eligible") -> list[dict[str, Any]]:
    """query に合う code_index entry を上位 n 件返す。"""
    query_text = query.strip()
    top_n = max(1, int(n))
    if not query_text:
        raise CodeRecommenderError(2, "query が空です。")

    entries = _fetch_entries(bucket=bucket)
    if not entries:
        return []

    cache_dir = _default_cache_dir()
    catalog_fingerprint = _catalog_fingerprint(_default_catalog_jsonl_path())
    cache_key = _cache_key(query_text, top_n, catalog_fingerprint, bucket=bucket)
    cache_file = cache_dir / f"{cache_key}.json"
    cached_results = _load_fresh_cache(cache_file, top_n, entries)
    if cached_results is not None:
        return cached_results

    template = _template_path().read_text(encoding="utf-8")
    prompt = _render_prompt(template, query_text, top_n, _entry_lines(entries))
    try:
        raw_output = _run_recommender(prompt)
        extracted = _extract_json(raw_output)
        if extracted is None:
            retry_prompt = prompt + "\n\n重要: JSON 形式厳守。JSON 以外の文字を一切出力しないこと。"
            raw_output = _run_recommender(retry_prompt)
            extracted = _extract_json(raw_output)
    except CodeRecommenderError as exc:
        if exc.code != 5:
            raise
        print(f"[code_recommender] local fallback: llm unavailable ({exc})", file=sys.stderr)
        return _attach_entry_metadata(_local_lexical_fallback(query_text, top_n, entries), entries)
    if extracted is None:
        raise CodeRecommenderError(4, "推挙結果の JSON 解析に失敗しました。")

    normalized = _normalize_result(extracted, top_n)
    _write_cache(cache_file, normalized)
    return _attach_entry_metadata(normalized, entries)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HELIX code index 推挙 CLI")
    parser.add_argument("query", help="検索クエリ")
    parser.add_argument("-n", "--top-n", type=int, default=5, help="上位候補数")
    parser.add_argument(
        "--bucket",
        choices=["coverage_eligible", "private_helper", "excluded", "all"],
        default="coverage_eligible",
        help="code_index bucket で候補を絞り込む",
    )
    parser.add_argument("--json", action="store_true", help="JSON のみ出力")
    return parser


# @helix:index id=code-recommender.main domain=cli/lib summary=mainを実行する
def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        results = find_code(args.query, n=max(1, args.top_n), bucket=args.bucket)
    except CodeRecommenderError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return exc.code

    if args.json:
        print(json.dumps({"results": results, "_model": MODEL_NAME}, ensure_ascii=False, indent=2))
        return 0

    for item in results:
        print(
            f"{item.get('id', '')}\t{item.get('domain', '')}\t"
            f"{item.get('path', '')}:{item.get('line_no', '')}\t"
            f"{float(item.get('score', 0.0)):.2f}\t{item.get('reason', '')}"
        )
    return 0


def find_duplicates(
    threshold: float = 0.85,
    *,
    domain: str = "",
    include_entrypoints: bool = False,
) -> list[dict[str, Any]]:
    entries = _fetch_entries(bucket="all")
    if domain:
        entries = [entry for entry in entries if _safe_text(entry.get("domain")).strip() == domain]

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        by_domain.setdefault(_safe_text(entry.get("domain")).strip(), []).append(entry)

    matches: list[dict[str, Any]] = []
    for domain_name, grouped_entries in by_domain.items():
        for index, left in enumerate(grouped_entries):
            left_summary = _safe_text(left.get("summary"))
            left_tokens = _summary_tokens(left_summary)
            for right in grouped_entries[index + 1 :]:
                right_tokens = _summary_tokens(_safe_text(right.get("summary")))
                union = left_tokens | right_tokens
                score = 0.0 if not union else len(left_tokens & right_tokens) / len(union)
                if score < threshold:
                    continue
                if not include_entrypoints and (_is_entrypoint_main(left) or _is_entrypoint_main(right)):
                    continue
                matches.append(
                    {
                        "left_id": _safe_text(left.get("id")).strip(),
                        "right_id": _safe_text(right.get("id")).strip(),
                        "score": score,
                        "domain": domain_name,
                    }
                )

    return sorted(
        matches,
        key=lambda item: (-float(item.get("score", 0.0)), _safe_text(item.get("domain")), _safe_text(item.get("left_id")), _safe_text(item.get("right_id"))),
    )


if __name__ == "__main__":
    raise SystemExit(main())
