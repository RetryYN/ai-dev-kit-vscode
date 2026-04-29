"""Tests for audit_hash module (PLAN-002 Sprint 2a)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_hash import (
    canonical_json,
    sha256_of,
    compute_decision_hash,
    compute_source_hash,
    DECISION_HASH_FIELDS,
)


def test_canonical_json_sorts_keys():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_json_no_whitespace():
    assert canonical_json({"a": 1, "b": [1, 2]}) == '{"a":1,"b":[1,2]}'


def test_canonical_json_unicode_japanese():
    # ensure_ascii=False で日本語は escape されない
    assert canonical_json({"k": "日本語"}) == '{"k":"日本語"}'


def test_canonical_json_nested():
    obj = {"outer": {"inner_b": 2, "inner_a": 1}, "list": [3, 1, 2]}
    expected = '{"list":[3,1,2],"outer":{"inner_a":1,"inner_b":2}}'
    assert canonical_json(obj) == expected


def test_sha256_of_known_value():
    # echo -n test | sha256sum
    assert sha256_of("test") == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def test_sha256_of_empty():
    assert sha256_of("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_compute_decision_hash_deterministic():
    d = {
        "candidate_id": "x",
        "schema_version": 1,
        "scope_hash": "a" * 64,
        "decision": "keep",
        "evidence": {"source": "x", "hash": "y", "redacted": True},
        "rationale": "r",
        "fail_safe_action": "skip",
    }
    h1 = compute_decision_hash(d)
    h2 = compute_decision_hash(dict(d))
    assert h1 == h2


def test_compute_decision_hash_ignores_extra_fields():
    base = {
        "candidate_id": "x",
        "schema_version": 1,
        "scope_hash": "a" * 64,
        "decision": "keep",
        "evidence": {},
        "rationale": "r",
        "fail_safe_action": "skip",
    }
    h1 = compute_decision_hash(base)
    h2 = compute_decision_hash({
        **base,
        "status": "active",
        "import_run_id": "abc",
        "created_at": 12345,
    })
    assert h1 == h2, "non-target fields should not affect hash"


def test_compute_decision_hash_changes_on_rationale():
    base = {
        "candidate_id": "x",
        "schema_version": 1,
        "scope_hash": "a" * 64,
        "decision": "keep",
        "evidence": {},
        "rationale": "r",
        "fail_safe_action": "skip",
    }
    h1 = compute_decision_hash(base)
    h2 = compute_decision_hash({**base, "rationale": "different"})
    assert h1 != h2


def test_compute_decision_hash_changes_on_decision():
    base = {
        "candidate_id": "x",
        "schema_version": 1,
        "scope_hash": "a" * 64,
        "decision": "keep",
        "evidence": {},
        "rationale": "r",
        "fail_safe_action": "skip",
    }
    h1 = compute_decision_hash(base)
    h2 = compute_decision_hash({**base, "decision": "remove"})
    assert h1 != h2


def test_compute_source_hash_deterministic():
    text = "version: 1\ndecisions: []\n"
    assert compute_source_hash(text) == compute_source_hash(text)


def test_compute_source_hash_changes_on_text_change():
    h1 = compute_source_hash("version: 1\n")
    h2 = compute_source_hash("version: 2\n")
    assert h1 != h2


def test_decision_hash_fields_constant():
    assert DECISION_HASH_FIELDS == (
        "candidate_id",
        "schema_version",
        "scope_hash",
        "decision",
        "evidence",
        "rationale",
        "fail_safe_action",
    )
