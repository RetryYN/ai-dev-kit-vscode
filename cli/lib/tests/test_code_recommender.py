from __future__ import annotations

import json
import os
import time
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = LIB_DIR.parent.parent


import code_recommender


def test_cache_key_is_deterministic() -> None:
    first = code_recommender._cache_key("frontmatter parser", 3)
    second = code_recommender._cache_key("frontmatter parser", 3)
    third = code_recommender._cache_key("frontmatter", 3)

    assert first == second
    assert first != third


def test_cache_key_includes_catalog_fingerprint() -> None:
    first = code_recommender._cache_key("frontmatter parser", 3, "fp-123")
    second = code_recommender._cache_key("frontmatter parser", 3, "fp-124")
    base = code_recommender._cache_key("frontmatter parser", 3)

    assert first != second
    assert first != base


def test_cache_is_fresh_detects_missing_and_ttl() -> None:
    cache_file = Path("/tmp/code-recommender-cache-test.json")
    if cache_file.exists():
        cache_file.unlink()

    assert code_recommender._cache_is_fresh(cache_file, ttl_seconds=60) is False

    now = int(time.time())
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text("{}", encoding="utf-8")
    old_time = now - 5
    os.utime(cache_file, (old_time, old_time))
    assert code_recommender._cache_is_fresh(cache_file, ttl_seconds=60) is True

    too_old_time = now - 120
    os.utime(cache_file, (too_old_time, too_old_time))
    assert code_recommender._cache_is_fresh(cache_file, ttl_seconds=60) is False


def test_gc_expired_cache_removes_only_expired_files(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".helix" / "cache" / "recommendations" / "code"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fresh = cache_dir / "fresh.json"
    stale = cache_dir / "stale.json"
    fresh.write_text("{}", encoding="utf-8")
    stale.write_text("{}", encoding="utf-8")

    now = int(time.time())
    os.utime(fresh, (now - 10, now - 10))
    os.utime(stale, (now - 2000, now - 2000))

    removed = code_recommender._gc_expired_cache(cache_dir, ttl_seconds=60)

    assert removed == 1
    assert fresh.exists()
    assert not stale.exists()


def test_catalog_fingerprint_changes_after_jsonl_update(tmp_path: Path) -> None:
    jsonl_path = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text("line-1\n", encoding="utf-8")
    before = code_recommender._catalog_fingerprint(jsonl_path)

    jsonl_path.write_text("line-1\nline-2\n", encoding="utf-8")
    after = code_recommender._catalog_fingerprint(jsonl_path)

    assert before != after


def test_catalog_fingerprint_handles_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    assert not missing.exists()
    assert code_recommender._catalog_fingerprint(missing) == "no-catalog"


def test_find_code_uses_cache_without_running_recommender(monkeypatch, tmp_path: Path) -> None:
    cache_dir = tmp_path / ".helix" / "cache" / "recommendations" / "code"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_payload = [{"id": "code-catalog.parse-frontmatter", "score": 0.98, "reason": "cached"}]
    query = "frontmatter parser"
    cache_key = code_recommender._cache_key(query, 1, "no-catalog")
    cache_file = cache_dir / f"{cache_key}.json"
    cache_file.write_text(json.dumps(cache_payload, ensure_ascii=False) + "\n", encoding="utf-8")

    called = {"run_recommender": 0}

    def _fake_run(_: str) -> str:
        called["run_recommender"] += 1
        raise RuntimeError("should not be called")

    def _fetch_entries() -> list[dict]:
        return [
            {
                "id": "code-catalog.parse-frontmatter",
                "domain": "cli/lib",
                "summary": "frontmatter parser",
                "path": "cli/lib/code_catalog.py",
                "line_no": 50,
                "since": "v1",
                "related": "[]",
            }
        ]

    monkeypatch.setattr(code_recommender, "_default_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(code_recommender, "_default_catalog_jsonl_path", lambda: tmp_path / "no-catalog.jsonl")
    monkeypatch.setattr(code_recommender, "_run_recommender", _fake_run)
    monkeypatch.setattr(code_recommender, "_fetch_entries", lambda: _fetch_entries())

    results = code_recommender.find_code(query, n=1)

    assert called["run_recommender"] == 0
    assert len(results) == 1
    assert results[0]["id"] == "code-catalog.parse-frontmatter"


def test_entry_lines_include_only_allowlist_metadata() -> None:
    entries = [
        {
            "id": "code-catalog.scan-file",
            "domain": "cli/lib",
            "summary": "対象ファイルを走査する",
            "path": "cli/lib/code_catalog.py",
            "line_no": 166,
            "source_hash": "secret-source-hash",
            "updated_at": "2026-05-03T00:00:00Z",
            "raw_rejected_summary": "password=secret",
            "code": "def should_not_send(): pass",
        }
    ]

    lines = code_recommender._entry_lines(entries)

    assert lines == "code-catalog.scan-file|cli/lib|cli/lib/code_catalog.py:166|対象ファイルを走査する"
    assert "source_hash" not in lines
    assert "secret-source-hash" not in lines
    assert "password=secret" not in lines
    assert "should_not_send" not in lines


def test_attach_entry_metadata_filters_ids_missing_from_current_db() -> None:
    candidates = [
        {"id": "stale.removed", "score": 1.0, "reason": "old cache"},
        {"id": "code-catalog.scan-file", "score": 0.8, "reason": "current"},
    ]
    entries = [
        {
            "id": "code-catalog.scan-file",
            "domain": "cli/lib",
            "summary": "対象ファイルを走査する",
            "path": "cli/lib/code_catalog.py",
            "line_no": 166,
        }
    ]

    results = code_recommender._attach_entry_metadata(candidates, entries)

    assert [item["id"] for item in results] == ["code-catalog.scan-file"]


def test_find_code_misses_cache_when_catalog_fingerprint_changes(monkeypatch, tmp_path: Path) -> None:
    cache_dir = tmp_path / ".helix" / "cache" / "recommendations" / "code"
    cache_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = tmp_path / ".helix" / "cache" / "code-catalog.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text('{"id":"code-catalog.scan-file"}\n', encoding="utf-8")

    stale_key = code_recommender._cache_key("scan file", 1, "old-fingerprint")
    (cache_dir / f"{stale_key}.json").write_text(
        json.dumps([{"id": "stale.removed", "score": 1.0, "reason": "old generation"}], ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    called = {"run_recommender": 0}

    def _fake_run(_: str) -> str:
        called["run_recommender"] += 1
        return json.dumps({"recommendations": [{"id": "code-catalog.scan-file", "score": 0.9, "reason": "fresh"}]})

    entries = [
        {
            "id": "code-catalog.scan-file",
            "domain": "cli/lib",
            "summary": "対象ファイルを走査する",
            "path": "cli/lib/code_catalog.py",
            "line_no": 166,
        }
    ]

    monkeypatch.setattr(code_recommender, "_default_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(code_recommender, "_default_catalog_jsonl_path", lambda: jsonl_path)
    monkeypatch.setattr(code_recommender, "_fetch_entries", lambda: entries)
    monkeypatch.setattr(code_recommender, "_template_path", lambda: REPO_ROOT / "cli" / "templates" / "code-search-prompt.md")
    monkeypatch.setattr(code_recommender, "_run_recommender", _fake_run)

    results = code_recommender.find_code("scan file", n=1)

    assert called["run_recommender"] == 1
    assert [item["id"] for item in results] == ["code-catalog.scan-file"]


def test_find_code_local_fallback_when_llm_unavailable(monkeypatch, tmp_path: Path, capsys) -> None:
    entries = [
        {
            "id": "code-catalog.scan-file",
            "domain": "cli/lib",
            "summary": "対象ファイルを走査する",
            "path": "cli/lib/code_catalog.py",
            "line_no": 166,
        },
        {
            "id": "skill-catalog.strip-quotes",
            "domain": "cli/lib",
            "summary": "引用符を除去する",
            "path": "cli/lib/skill_catalog.py",
            "line_no": 42,
        },
    ]

    def _unavailable(_: str) -> str:
        raise code_recommender.CodeRecommenderError(5, "llm unavailable")

    monkeypatch.setattr(code_recommender, "_default_cache_dir", lambda: tmp_path / "cache")
    monkeypatch.setattr(code_recommender, "_default_catalog_jsonl_path", lambda: tmp_path / "missing.jsonl")
    monkeypatch.setattr(code_recommender, "_fetch_entries", lambda: entries)
    monkeypatch.setattr(code_recommender, "_template_path", lambda: REPO_ROOT / "cli" / "templates" / "code-search-prompt.md")
    monkeypatch.setattr(code_recommender, "_run_recommender", _unavailable)

    results = code_recommender.find_code("scan file", n=1)
    captured = capsys.readouterr()

    assert [item["id"] for item in results] == ["code-catalog.scan-file"]
    assert "local fallback: llm unavailable" in captured.err


def test_find_code_writes_normalized_cache_only(monkeypatch, tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    jsonl_path = tmp_path / "code-catalog.jsonl"
    jsonl_path.write_text('{"id":"code-catalog.scan-file"}\n', encoding="utf-8")
    entries = [
        {
            "id": "code-catalog.scan-file",
            "domain": "cli/lib",
            "summary": "対象ファイルを走査する",
            "path": "cli/lib/code_catalog.py",
            "line_no": 166,
        }
    ]

    def _fake_run(_: str) -> str:
        return json.dumps(
            {
                "recommendations": [
                    {
                        "id": "code-catalog.scan-file",
                        "score": 0.9,
                        "reason": "fresh",
                        "summary": "must not be cached",
                        "path": "must/not/cache.py",
                    }
                ]
            },
            ensure_ascii=False,
        )

    monkeypatch.setattr(code_recommender, "_default_cache_dir", lambda: cache_dir)
    monkeypatch.setattr(code_recommender, "_default_catalog_jsonl_path", lambda: jsonl_path)
    monkeypatch.setattr(code_recommender, "_fetch_entries", lambda: entries)
    monkeypatch.setattr(code_recommender, "_template_path", lambda: REPO_ROOT / "cli" / "templates" / "code-search-prompt.md")
    monkeypatch.setattr(code_recommender, "_run_recommender", _fake_run)

    results = code_recommender.find_code("scan file", n=1)
    cache_key = code_recommender._cache_key("scan file", 1, code_recommender._catalog_fingerprint(jsonl_path))
    cached = json.loads((cache_dir / f"{cache_key}.json").read_text(encoding="utf-8"))

    assert results[0]["summary"] == "対象ファイルを走査する"
    assert cached == [{"id": "code-catalog.scan-file", "score": 0.9, "reason": "fresh"}]
