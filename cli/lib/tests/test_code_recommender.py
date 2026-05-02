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


def test_find_code_uses_cache_without_running_recommender(monkeypatch, tmp_path: Path) -> None:
    cache_dir = tmp_path / ".helix" / "cache" / "recommendations" / "code"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_payload = [{"id": "code-catalog.parse-frontmatter", "score": 0.98, "reason": "cached"}]
    query = "frontmatter parser"
    cache_key = code_recommender._cache_key(query, 1)
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
    monkeypatch.setattr(code_recommender, "_run_recommender", _fake_run)
    monkeypatch.setattr(code_recommender, "_fetch_entries", lambda: _fetch_entries())

    results = code_recommender.find_code(query, n=1)

    assert called["run_recommender"] == 0
    assert len(results) == 1
    assert results[0]["id"] == "code-catalog.parse-frontmatter"
