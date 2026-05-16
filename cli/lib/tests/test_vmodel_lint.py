"""V-model 4 artifact lint 単体テスト (PLAN-075 Phase 5)

対象設計 (① D-API): なし (内部 helper)
対象実装 (② D-IMPL): cli/lib/vmodel_lint.py
テスト設計 (③): 本ファイル docstring 内 inline case (size 限定のため artifact 化省略、PLAN-075 例外)
テストコード (④ D-TEST-CODE-UNIT): cli/lib/tests/test_vmodel_lint.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import vmodel_lint
from vmodel_lint import LintResult, format_text, lint_all, lint_plan, load_grandfather_list


def _write_plan(plans_dir: Path, plan_id: str, body: str, *, filename: str | None = None) -> Path:
    target = plans_dir / (filename or f"{plan_id}-sample.md")
    target.write_text(f"---\nplan_id: {plan_id}\n---\n{body}\n", encoding="utf-8")
    return target


def test_lint_result_complete_when_all_refs_present() -> None:
    """DoD 検証: inline U-001 4 artifact ref が全て > 0 で complete=True"""
    result = LintResult(
        plan_id="PLAN-X",
        path="x.md",
        design_ref=1,
        impl_ref=1,
        test_design_ref=1,
        test_code_ref=1,
    )
    assert result.complete is True


def test_lint_result_incomplete_when_one_missing() -> None:
    """DoD 検証: inline U-002 いずれか 1 つでも 0 で complete=False"""
    result = LintResult(
        plan_id="PLAN-X",
        path="x.md",
        design_ref=1,
        impl_ref=1,
        test_design_ref=0,
        test_code_ref=1,
    )
    assert result.complete is False


def test_load_grandfather_list_returns_only_open_audit_findings(tmp_path: Path) -> None:
    """DoD 検証: inline U-003 deferred-findings から open の audit finding だけを抽出する"""
    deferred_path = tmp_path / "deferred-findings.yaml"
    deferred_path.write_text(
        "\n".join(
            [
                "findings:",
                "  - id: DF-PLAN-067-AUDIT-001",
                "    plan_id: PLAN-067",
                "    status: open",
                "  - id: DF-PLAN-068-AUDIT-001",
                "    plan_id: PLAN-068",
                "    status: resolved",
                "  - id: DF-PLAN-099-G4-001",
                "    plan_id: PLAN-099",
                "    status: open",
            ]
        ),
        encoding="utf-8",
    )

    result = load_grandfather_list(deferred_path)

    assert result == {"PLAN-067"}


def test_load_grandfather_list_returns_empty_without_yaml_support(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: inline U-004 yaml import 不可でも空 set で graceful degrade する"""
    deferred_path = tmp_path / "deferred-findings.yaml"
    deferred_path.write_text("findings: []\n", encoding="utf-8")

    monkeypatch.setattr(vmodel_lint, "yaml", None)

    assert load_grandfather_list(deferred_path) == set()


def test_lint_plan_detects_all_reference_kinds(tmp_path: Path) -> None:
    """DoD 検証: inline U-005 plan 本文から design/impl/test-design/test-code を集計する"""
    plan_path = _write_plan(
        tmp_path,
        "PLAN-123",
        (
            "D-API docs/v2/L3-detailed-design/\n"
            "cli/lib/example_tool.py\n"
            "docs/v2/L4-test-design/PLAN-123-unit-test-design.md\n"
            "cli/lib/tests/test_example_tool.py"
        ),
    )

    result = lint_plan(plan_path, set(), tmp_path)

    assert result.complete is True
    assert result.missing == []
    assert result.design_ref > 0
    assert result.impl_ref > 0
    assert result.test_design_ref > 0
    assert result.test_code_ref > 0


def test_lint_all_filters_plan_id_and_applies_grandfather(tmp_path: Path) -> None:
    """DoD 検証: inline U-006 plan_id filter と grandfather 判定が同時に動作する"""
    plans_dir = tmp_path / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    _write_plan(plans_dir, "PLAN-123", "D-API\ncli/lib/foo.py")
    _write_plan(plans_dir, "PLAN-124", "D-API\ncli/lib/bar.py")
    deferred_path = tmp_path / ".helix" / "audit" / "deferred-findings.yaml"
    deferred_path.parent.mkdir(parents=True)
    deferred_path.write_text(
        "\n".join(
            [
                "findings:",
                "  - id: DF-PLAN-124-AUDIT-001",
                "    plan_id: PLAN-124",
                "    status: open",
            ]
        ),
        encoding="utf-8",
    )

    results = lint_all(
        plan_id_filter="PLAN-124",
        plans_dir=plans_dir,
        deferred_path=deferred_path,
        project_root=tmp_path,
    )

    assert [result.plan_id for result in results] == ["PLAN-124"]
    assert results[0].grandfather is True


def test_format_text_marks_grandfather_and_incomplete() -> None:
    """DoD 検証: inline U-007 text format が grandfather と incomplete を区別表示する"""
    results = [
        LintResult(
            plan_id="PLAN-100",
            path="docs/plans/PLAN-100-sample.md",
            design_ref=1,
            impl_ref=1,
            test_design_ref=1,
            test_code_ref=1,
        ),
        LintResult(
            plan_id="PLAN-101",
            path="docs/plans/PLAN-101-sample.md",
            design_ref=1,
            impl_ref=0,
            test_design_ref=1,
            test_code_ref=0,
            grandfather=True,
            missing=["impl", "test-code"],
        ),
        LintResult(
            plan_id="PLAN-102",
            path="docs/plans/PLAN-102-sample.md",
            design_ref=1,
            impl_ref=0,
            test_design_ref=1,
            test_code_ref=0,
            missing=["impl", "test-code"],
        ),
    ]

    output = format_text(results)

    assert "[✓] PLAN-100: complete" in output
    assert "[○] PLAN-101: grandfather (skip)" in output
    assert "[⚠] PLAN-102: missing impl,test-code" in output
    assert "Summary: total=3, complete=1, incomplete=1 (non-grandfather), grandfather=1" in output


def test_main_json_and_strict_exit_on_incomplete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """DoD 検証: inline U-008 --json と --strict が incomplete PLAN で exit 1 を返す"""
    plans_dir = tmp_path / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    _write_plan(plans_dir, "PLAN-200", "D-API\ncli/lib/only_impl.py")
    deferred_path = tmp_path / ".helix" / "audit" / "deferred-findings.yaml"
    deferred_path.parent.mkdir(parents=True)
    deferred_path.write_text("findings: []\n", encoding="utf-8")

    monkeypatch.setattr(vmodel_lint, "HELIX_ROOT", tmp_path)
    monkeypatch.setattr(vmodel_lint, "PLANS_DIR", plans_dir)
    monkeypatch.setattr(vmodel_lint, "DEFERRED_FINDINGS", deferred_path)

    exit_code = vmodel_lint.main(["--json", "--strict"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload[0]["plan_id"] == "PLAN-200"
    assert payload[0]["complete"] is False
    assert payload[0]["missing"] == ["test-design", "test-code"]
