import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import verify_agent


def _write_plan(root: Path, name: str = "PLAN-999-test.md", text: str | None = None) -> Path:
    path = root / "docs" / "plans" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text
        or """# PLAN-999: test

## 検証
- pytest unit test を実行する
- security dependency validation を行う
""",
        encoding="utf-8",
    )
    return path


def _write_verify_tools(root: Path) -> Path:
    path = root / ".helix" / "patterns" / "verify-tools.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """version: 1
tools:
  - id: pytest
    category: unit-test
    languages: [py]
    license: MIT
    last_release_or_activity: 2026-03-20
    maintenance_signal: active
    official_source: https://pytest.org
    security_notes: []
    adoption_status: candidate_only
  - id: trivy
    category: security
    languages: [any]
    license: Apache-2.0
    last_release_or_activity: 2026-04-10
    maintenance_signal: active
    official_source: https://github.com/aquasecurity/trivy
    security_notes: []
    adoption_status: candidate_only
""",
        encoding="utf-8",
    )
    return path


def _write_contract(root: Path) -> Path:
    path = root / "docs" / "features" / "sample" / "D-CONTRACT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# D-CONTRACT\n- endpoint: /api/test\n", encoding="utf-8")
    return path


def test_harvest_matches_verify_tools_and_required_fields(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)
    _write_verify_tools(tmp_path)

    result = verify_agent.harvest(str(plan), project_root=tmp_path)

    assert result["plan_id"] == "PLAN-999"
    assert {candidate["tool_id"] for candidate in result["candidates"]} == {"pytest", "trivy"}
    for candidate in result["candidates"]:
        for field in verify_agent.HARVEST_REQUIRED_FIELDS:
            assert field in candidate
        assert candidate["source"] == ".helix/patterns/verify-tools.yaml"


def test_harvest_fallback_when_verify_tools_missing(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)

    result = verify_agent.harvest(str(plan), project_root=tmp_path)

    assert result["candidates"][0]["source"] == "fallback"
    assert result["candidates"][0]["adoption_status"] == "candidate_only"
    assert "fallback_reason" in result["candidates"][0]


def test_harvest_llm_suggest_uses_injected_runner(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)
    _write_verify_tools(tmp_path)

    def fake_runner(role: str, thinking: str, task: str) -> str:
        assert role == "research"
        assert thinking == "low"
        return json.dumps(
            {
                "candidates": [
                    {
                        "tool_id": "mutmut",
                        "official_source": "https://mutmut.readthedocs.io",
                        "license": "BSD-3-Clause",
                        "last_release_or_activity": "2026-04-01",
                        "maintenance_signal": "active",
                        "security_notes": [],
                    }
                ]
            }
        )

    result = verify_agent.harvest(str(plan), llm_suggest=True, project_root=tmp_path, codex_runner=fake_runner)

    llm = [candidate for candidate in result["candidates"] if candidate["source"] == "llm-suggest"]
    assert llm and llm[0]["tool_id"] == "mutmut"
    assert llm[0]["adoption_status"] == "candidate_only"


def test_design_requires_at_least_one_metric_with_mock(tmp_path: Path) -> None:
    contract = tmp_path / "docs" / "features" / "sample" / "D-CONTRACT.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("# D-CONTRACT\n- endpoint: /api/test\n", encoding="utf-8")

    def fake_runner(role: str, thinking: str, task: str) -> str:
        assert role == "tl"
        assert thinking == "medium"
        return json.dumps(
            {
                "pyramid_targets": {"unit": 65, "integration": 25, "e2e": 10},
                "boundaries": ["Unit: validation", "Integration: DB contract"],
                "metrics_minimum": ["p95 <= 200ms"],
            }
        )

    result = verify_agent.design(str(contract), project_root=tmp_path, codex_runner=fake_runner)

    assert result["pyramid_targets"]["unit"] == 65
    assert len(result["metrics_minimum"]) >= 1


def test_cross_check_identical_plan_has_no_drift(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)

    result = verify_agent.cross_check(str(plan), str(plan), project_root=tmp_path)

    assert result["drifts"] == []
    assert result["fail_close"] is False


def test_cross_check_unclassified_requires_pm_triage_and_fail_close(tmp_path: Path) -> None:
    impl = _write_plan(tmp_path, "PLAN-901-impl.md", "# PLAN-901\n- impl validation\n")
    spec = _write_plan(tmp_path, "PLAN-902-spec.md", "# PLAN-902\n- spec validation\n")

    def fake_runner(role: str, thinking: str, task: str) -> str:
        assert role == "tl"
        assert thinking == "high"
        return json.dumps(
            {
                "drifts": [
                    {
                        "drift_type": "contract-only",
                        "drift_severity": "unknown",
                        "title": "triage needed",
                        "body": "cannot classify",
                    }
                ]
            }
        )

    result = verify_agent.cross_check(str(impl), str(spec), project_root=tmp_path, codex_runner=fake_runner)

    assert result["fail_close"] is True
    assert result["drifts"][0]["drift_severity"] == "unclassified"
    assert result["drifts"][0]["requires_pm_triage"] is True


@pytest.mark.parametrize(
    ("severity", "route"),
    [
        ("P0", "stop, incident 起票"),
        ("P1", "G2/G3 fail-close, scrum (Unit/Sprint) 起票"),
        ("P2", "次工程開始前に解消 or readiness defer"),
        ("P3", "任意 carry, deferred 台帳記録"),
        ("unclassified", "PM/TL 再判定必須 (fail-close)"),
    ],
)
def test_severity_route(severity: str, route: str) -> None:
    assert verify_agent.severity_route(severity) == route


def test_save_to_db_harvest_inserts_row(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)
    result = verify_agent.save_to_db(
        "harvest",
        {"plan_id": "PLAN-999"},
        {"count": 1},
        True,
        project_root=tmp_path,
        input_paths=[plan],
        plan_id="PLAN-999",
        candidates_count=1,
        fallback_used=True,
    )

    assert result["requested"] is True
    assert result["persisted"] is True
    assert result["run_id"].startswith("VR-")
    row = verify_agent.show_run(result["run_id"], project_root=tmp_path)
    assert row["subcommand"] == "harvest"
    assert row["plan_id"] == "PLAN-999"
    assert row["candidates_count"] == 1
    assert row["fallback_used"] is True


def test_save_to_db_cross_check_formats_drift_severity_summary(tmp_path: Path) -> None:
    impl = _write_plan(tmp_path, "PLAN-901-impl.md", "# PLAN-901\n- impl validation\n")
    spec = _write_plan(tmp_path, "PLAN-902-spec.md", "# PLAN-902\n- spec validation\n")

    result = verify_agent.save_to_db(
        "cross-check",
        {"impl": "docs/plans/PLAN-901-impl.md", "spec": "docs/plans/PLAN-902-spec.md"},
        {"fail_close": True},
        True,
        project_root=tmp_path,
        input_paths=[impl, spec],
        plan_id="PLAN-901",
        spec_plan_id="PLAN-902",
        drifts_count=3,
        drift_severity_summary={"P0": 0, "P1": 2, "P2": 1, "P3": 0, "unclassified": 0},
        has_fail_close=True,
    )

    row = verify_agent.show_run(result["run_id"], project_root=tmp_path)
    assert row["drift_severity_summary"] == "P0:0,P1:2,P2:1,P3:0,unclassified:0"
    assert row["has_fail_close"] is True
    assert row["drifts_count"] == 3


def test_save_to_db_allows_duplicate_inputs_hash_with_different_run_id(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)

    first = verify_agent.save_to_db(
        "harvest",
        {"plan_id": "PLAN-999"},
        {"count": 1},
        True,
        project_root=tmp_path,
        input_paths=[plan],
        plan_id="PLAN-999",
    )
    second = verify_agent.save_to_db(
        "harvest",
        {"plan_id": "PLAN-999"},
        {"count": 1},
        True,
        project_root=tmp_path,
        input_paths=[plan],
        plan_id="PLAN-999",
    )

    assert first["run_id"] != second["run_id"]
    rows = verify_agent.list_runs(project_root=tmp_path)["runs"]
    assert len(rows) == 2
    assert {row["inputs_hash"] for row in rows} == {first["inputs_hash"]}


def test_list_runs_empty(tmp_path: Path) -> None:
    result = verify_agent.list_runs(project_root=tmp_path)

    assert result["runs"] == []


def test_list_runs_after_save_returns_one_row(tmp_path: Path) -> None:
    plan = _write_plan(tmp_path)
    saved = verify_agent.save_to_db(
        "harvest",
        {"plan_id": "PLAN-999"},
        {"count": 1},
        True,
        project_root=tmp_path,
        input_paths=[plan],
        plan_id="PLAN-999",
    )

    result = verify_agent.list_runs("harvest", project_root=tmp_path)

    assert [row["run_id"] for row in result["runs"]] == [saved["run_id"]]


def test_show_run_returns_detail_dict(tmp_path: Path) -> None:
    contract = _write_contract(tmp_path)
    saved = verify_agent.save_to_db(
        "design",
        {"contract_path": "docs/features/sample/D-CONTRACT.md"},
        {"pyramid_targets": {"unit": 60, "integration": 30, "e2e": 10}},
        True,
        project_root=tmp_path,
        input_paths=[contract],
        contract_path="docs/features/sample/D-CONTRACT.md",
    )

    row = verify_agent.show_run(saved["run_id"], project_root=tmp_path)

    assert row["run_id"] == saved["run_id"]
    assert row["subcommand"] == "design"
    assert row["contract_path"] == "docs/features/sample/D-CONTRACT.md"


def test_show_run_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(verify_agent.VerifyAgentError):
        verify_agent.show_run("VR-2099-01-01-9999", project_root=tmp_path)
