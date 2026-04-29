"""Tests for audit_validator (PLAN-002 Sprint 2a)。"""
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_validator import (
    DECISION_ENUM,
    FAIL_SAFE_ENUM,
    SHA256_HEX_RE,
    validate_decisions_yaml,
)


def _write_yaml(text: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    f.write(text)
    f.close()
    return Path(f.name)


SHA = "a" * 64
SHB = "b" * 64


def _valid_yaml() -> str:
    return textwrap.dedent(f"""\
        version: 1
        metadata:
          scope_hash: "{SHA}"
          source_hash: "{SHB}"
          schema_version: 1
        decisions:
          - candidate_id: src/x.py
            schema_version: 1
            scope_hash: "{SHA}"
            decision: keep
            rationale: looks good
            evidence:
              source: src/x.py
              hash: deadbeef
              redacted: true
            fail_safe_action: skip
        """)


def test_valid_yaml_passes():
    p = _write_yaml(_valid_yaml())
    r = validate_decisions_yaml(p)
    assert r.success, r.errors
    assert len(r.decisions) == 1
    assert r.metadata is not None


def test_missing_version():
    text = _valid_yaml().replace("version: 1\n", "")
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("version" in e for e in r.errors)


def test_wrong_version():
    text = _valid_yaml().replace("version: 1\n", "version: 2\n")
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("version must be 1" in e for e in r.errors)


def test_missing_metadata():
    text = textwrap.dedent("""\
        version: 1
        decisions: []
        """)
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("metadata" in e for e in r.errors)


def test_invalid_scope_hash_format():
    text = _valid_yaml().replace(SHA, "x" * 10)
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("sha256 hex 64" in e for e in r.errors)


def test_invalid_decision_enum():
    text = _valid_yaml().replace("decision: keep", "decision: unknown")
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("decision must be one of" in e for e in r.errors)


def test_invalid_fail_safe_enum():
    text = _valid_yaml().replace(
        "fail_safe_action: skip", "fail_safe_action: nuke"
    )
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert any("fail_safe_action must be one of" in e for e in r.errors)


def test_missing_evidence_redacted_bool():
    text = _valid_yaml().replace("redacted: true", "redacted: yes_string")
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    # PyYAML auto-casts "yes" but "yes_string" stays as str → bool 期待を満たさない
    assert not r.success
    assert any("evidence.redacted" in e for e in r.errors)


def test_collects_all_errors():
    text = textwrap.dedent("""\
        version: 99
        metadata:
          scope_hash: bad
          source_hash: bad
          schema_version: not_int
        decisions:
          - candidate_id: ""
            schema_version: 1
            scope_hash: bad
            decision: unknown
            rationale: r
            evidence:
              source: x
              hash: y
              redacted: not_bool
            fail_safe_action: bad
        """)
    p = _write_yaml(text)
    r = validate_decisions_yaml(p)
    assert not r.success
    assert len(r.errors) >= 5  # multiple errors collected


def test_file_not_found():
    r = validate_decisions_yaml("/tmp/nonexistent_decisions_file.yaml")
    assert not r.success
    assert any("not found" in e for e in r.errors)


def test_constants():
    assert DECISION_ENUM == ("keep", "remove", "merge", "deprecate")
    assert FAIL_SAFE_ENUM == ("skip", "quarantine", "manual_review")
    assert SHA256_HEX_RE.match("a" * 64)
    assert not SHA256_HEX_RE.match("A" * 64)  # uppercase rejected
    assert not SHA256_HEX_RE.match("a" * 63)  # length
