import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db
from llm_classifier_base import CodexInvocationError, CodexResponseError, LLMClassifierBase


class DummyClassifier(LLMClassifierBase):
    role = "gpt-5.4-mini"
    classifier_name = "dummy_classifier"


class RuleClassifier(DummyClassifier):
    classifier_name = "rule_classifier"

    def _classify_from_rules(self, query: str, context: dict | None) -> dict | None:
        return {"decision": "rule", "query": query, "context": context or {}}


def _classifier(tmp_path: Path) -> DummyClassifier:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(db_path)
    classifier = DummyClassifier(db_path=db_path)
    classifier.cache_dir = tmp_path / ".helix" / "cache" / classifier.classifier_name
    return classifier


def test_cache_key_is_deterministic(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    context = {"phase": "L1", "items": ["a", "b"]}

    first = classifier._cache_key("select skills", context)
    second = classifier._cache_key("select skills", {"items": ["a", "b"], "phase": "L1"})

    assert first == second
    assert first != classifier._cache_key("select effort", context)


def test_cache_lookup_returns_none_for_missing(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)

    assert classifier._cache_lookup("missing") is None


def test_cache_store_and_lookup(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    payload = {"decision": "ok", "score": 0.91}

    classifier._cache_store("cache-key", payload)

    assert classifier._cache_lookup("cache-key") == payload


def test_cache_ttl_expires(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    classifier.cache_ttl_sec = 1
    classifier._cache_store("cache-key", {"decision": "ok"})
    cache_file = classifier.cache_dir / "cache-key.json"
    old_time = time.time() - 5
    os.utime(cache_file, (old_time, old_time))

    assert classifier._cache_lookup("cache-key") is None


def test_render_prompt_expands_one_level_include(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    (tmp_path / "foo.md").write_text("included {{include nested.md}}\n", encoding="utf-8")
    (tmp_path / "nested.md").write_text("nested\n", encoding="utf-8")
    template = tmp_path / "prompt.md"
    template.write_text("start\n{{include foo.md}}end\n", encoding="utf-8")

    rendered = classifier._render_prompt(template, {})

    assert rendered == "start\nincluded {{include nested.md}}\nend\n"


def test_render_prompt_missing_include_raises(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    template = tmp_path / "prompt.md"
    template.write_text("{{include missing.md}}\n", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        classifier._render_prompt(template, {})


def test_render_prompt_expands_include_and_variables(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    (tmp_path / "header.md").write_text("hello {{name}}\n", encoding="utf-8")
    template = tmp_path / "prompt.md"
    template.write_text("{{include header.md}}task={{task}}\n", encoding="utf-8")

    rendered = classifier._render_prompt(template, {"name": "HELIX", "task": "review"})

    assert rendered == "hello HELIX\ntask=review\n"


def test_invoke_codex_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(CodexInvocationError):
        classifier._invoke_codex("query", None)


def test_parse_response_invalid_json(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)

    with pytest.raises(CodexResponseError):
        classifier._parse_response("not json")


def test_record_decision_inserts_evidence_entry(tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    query = "choose a skill"
    result = {"skill": "testing"}
    cache_key = classifier._cache_key(query, None)
    classifier._last_cache_key = cache_key

    classifier._record_decision(query, result, source="codex")

    entry_id = f"{classifier.classifier_name}.{hashlib.sha256(query.encode('utf-8')).hexdigest()[:12]}"
    conn = helix_db.get_connection(classifier.db_path)
    try:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row["axis"] == "evidence"
    assert row["stack"] == "n/a"
    assert row["lifecycle"] == "initial"
    assert row["ref"] == f"{classifier.classifier_name}/{cache_key}"
    assert row["agent_actor"] == "codex-gpt-5.4-mini"
    assert json.loads(row["metadata"]) == {"query": query, "result": result, "source": "codex"}


def test_classify_rule_hook_skips_codex_and_records_rule_source(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    db_path = tmp_path / ".helix" / "helix.db"
    helix_db.init_db(db_path)
    classifier = RuleClassifier(db_path=db_path)
    classifier.cache_dir = tmp_path / ".helix" / "cache" / classifier.classifier_name
    calls = {"invoke": 0}

    def fake_invoke(query: str, context: dict | None) -> str:
        calls["invoke"] += 1
        return '{"decision": "codex"}'

    monkeypatch.setattr(classifier, "_invoke_codex", fake_invoke)

    result = classifier.classify("rule query", {"phase": "L4"})

    assert result == {"decision": "rule", "query": "rule query", "context": {"phase": "L4"}}
    assert calls["invoke"] == 0
    conn = helix_db.get_connection(classifier.db_path)
    try:
        row = conn.execute(
            "SELECT metadata FROM entries WHERE id LIKE 'rule_classifier.%'",
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert json.loads(row["metadata"])["source"] == "rule"


def test_classify_full_flow_with_mock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    classifier = _classifier(tmp_path)
    calls = {"invoke": 0}

    def fake_invoke(query: str, context: dict | None) -> str:
        calls["invoke"] += 1
        assert query == "classify this"
        assert context == {"phase": "L4"}
        return '{"decision": "use-testing", "confidence": 0.93}'

    monkeypatch.setattr(classifier, "_invoke_codex", fake_invoke)

    first = classifier.classify("classify this", {"phase": "L4"})
    second = classifier.classify("classify this", {"phase": "L4"})

    assert first == {"decision": "use-testing", "confidence": 0.93}
    assert second == first
    assert calls["invoke"] == 1

    conn = helix_db.get_connection(classifier.db_path)
    try:
        rows = conn.execute(
            "SELECT metadata FROM entries WHERE id LIKE ?",
            (f"{classifier.classifier_name}.%",),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert json.loads(rows[0]["metadata"])["source"] == "codex"
