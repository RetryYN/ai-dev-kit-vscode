from __future__ import annotations

import hashlib
import py_compile
import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import review_evidence_checks


MODULE_PATH = LIB_DIR / "review_evidence_checks.py"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _base_review_evidence() -> dict[str, str]:
    return {
        "review_id": "REV-001",
        "review_kind": "cross_agent",
        "reviewer_role": "tl-advisor",
        "reviewer_model": "gpt-5.5",
        "worker_model": "gpt-5.4",
        "reviewed_commit": "abc123def456",
        "review_output_path": "artifacts/review-output.json",
        "review_output_sha256": _sha256_text('{"verdict":"approve"}\n'),
        "tests_green_at": "2026-06-21T10:00:00+09:00",
        "reviewed_at": "2026-06-21T10:05:00+09:00",
        "verdict": "approve",
    }


def _write_plan(root: Path, review_evidence: dict[str, str] | None) -> Path:
    plan_path = root / "docs" / "plans" / "process" / "process-2026-06-21-review-evidence.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "plan_id": "process-2026-06-21-review-evidence",
        "title": "review evidence detector test",
        "kind": "planning",
        "layer": "L7",
        "drive": "be",
        "status": "draft",
    }
    if review_evidence is not None:
        payload["review_evidence"] = review_evidence
    plan_path.write_text(
        "---\n"
        + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
        + "---\n\n# body\n",
        encoding="utf-8",
    )
    return plan_path


def _write_review_output(root: Path, text: str = '{"verdict":"approve"}\n') -> Path:
    path = root / "artifacts" / "review-output.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _finding_kinds(report: review_evidence_checks.DetectorReport) -> list[str]:
    return [finding.kind for finding in report.findings]


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_clean_review_evidence_has_no_findings(tmp_path: Path) -> None:
    _write_review_output(tmp_path)
    plan_path = _write_plan(tmp_path, _base_review_evidence())

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert report.findings == []


def test_missing_field_emits_finding(tmp_path: Path) -> None:
    _write_review_output(tmp_path)
    review_evidence = _base_review_evidence()
    review_evidence.pop("review_id")
    plan_path = _write_plan(tmp_path, review_evidence)

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert _finding_kinds(report) == ["review_evidence_missing_field"]
    assert "review_id" in report.findings[0].message


def test_not_genuine_cross_agent_when_models_match(tmp_path: Path) -> None:
    _write_review_output(tmp_path)
    review_evidence = _base_review_evidence()
    review_evidence["worker_model"] = review_evidence["reviewer_model"]
    plan_path = _write_plan(tmp_path, review_evidence)

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert _finding_kinds(report) == ["review_evidence_not_genuine_cross_agent"]


def test_reviewed_before_tests_green_emits_finding(tmp_path: Path) -> None:
    _write_review_output(tmp_path)
    review_evidence = _base_review_evidence()
    review_evidence["tests_green_at"] = "2026-06-21T10:10:00+09:00"
    review_evidence["reviewed_at"] = "2026-06-21T10:05:00+09:00"
    plan_path = _write_plan(tmp_path, review_evidence)

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert _finding_kinds(report) == ["review_evidence_reviewed_before_tests_green"]


def test_output_tamper_emits_finding(tmp_path: Path) -> None:
    _write_review_output(tmp_path, '{"verdict":"approve"}\n')
    review_evidence = _base_review_evidence()
    review_evidence["review_output_sha256"] = _sha256_text('{"verdict":"approve"}\n')
    plan_path = _write_plan(tmp_path, review_evidence)
    (tmp_path / "artifacts" / "review-output.json").write_text(
        '{"verdict":"changes_required"}\n',
        encoding="utf-8",
    )

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert _finding_kinds(report) == ["review_evidence_output_tamper_or_missing"]


def test_not_applicable_when_review_evidence_is_absent(tmp_path: Path) -> None:
    plan_path = _write_plan(tmp_path, None)

    report = review_evidence_checks.check_review_evidence([plan_path], tmp_path)

    assert report.findings == []
