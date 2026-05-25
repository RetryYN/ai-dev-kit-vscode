"""Tests for cli.lib.vmodel_pair_freeze."""

from __future__ import annotations

from cli.lib.vmodel_pair_freeze import VMODEL_PAIRS, check_pair_freeze, get_pair


def test_get_pair_returns_expected() -> None:
    """DoD 検証: W6-B U-001 V-model pair の往復対応を返す。"""
    assert VMODEL_PAIRS["L1"] == "L14"
    assert get_pair("L1") == "L14"
    assert get_pair("L2") == "L10"
    assert get_pair("L6") == "L7"
    assert get_pair("L7") == "L6"
    assert get_pair("L14") == "L1"


def test_get_pair_returns_none_for_unpaired() -> None:
    """DoD 検証: W6-B U-002 pair 非対象 layer は None。"""
    assert get_pair("L0") is None
    assert get_pair("L11") is None
    assert get_pair("L13") is None
    assert get_pair("unknown") is None


def test_check_pair_freeze_status_ok(tmp_path) -> None:
    """DoD 検証: W6-B U-003 pair doc が存在すると status=ok。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    pair_doc = pair_dir / "L7-sampleplan.md"
    pair_doc.write_text("# sample\n", encoding="utf-8")

    result = check_pair_freeze("L6", project_root=tmp_path)

    assert result["layer"] == "L6"
    assert result["pair"] == "L7"
    assert result["pair_doc_exists"] is True
    assert result["pair_doc_path"] == str(pair_doc)
    assert result["status"] == "ok"
    assert result["hint"] is None


def test_check_pair_freeze_status_pair_missing(tmp_path) -> None:
    """DoD 検証: W6-B U-004 pair doc 不在なら status=pair_missing。"""
    result = check_pair_freeze("L6", project_root=tmp_path)

    assert result["layer"] == "L6"
    assert result["pair"] == "L7"
    assert result["pair_doc_exists"] is False
    assert result["pair_doc_path"] is None
    assert result["status"] == "pair_missing"
    assert "docs/plans/L7/" in result["hint"]
    assert "L7-*plan.md" in result["hint"]


def test_check_pair_freeze_severity_critical(tmp_path) -> None:
    """DoD 検証: W7-C U-001 L4 の pair_missing は critical。"""
    result = check_pair_freeze("L4", project_root=tmp_path)

    assert result["status"] == "pair_missing"
    assert result["severity"] == "critical"


def test_check_pair_freeze_severity_warning(tmp_path) -> None:
    """DoD 検証: W7-C U-002 L2 の pair_missing は warning。"""
    result = check_pair_freeze("L2", project_root=tmp_path)

    assert result["status"] == "pair_missing"
    assert result["severity"] == "warning"


def test_check_pair_freeze_severity_info(tmp_path) -> None:
    """DoD 検証: W7-C U-003 L7 の pair_missing は info。"""
    orphan_root = tmp_path / "empty"
    orphan_root.mkdir()

    result = check_pair_freeze("L7", project_root=orphan_root)

    assert result["status"] == "pair_missing"
    assert result["severity"] == "info"


def test_check_pair_freeze_status_no_pair(tmp_path) -> None:
    """DoD 検証: W6-B U-005 pair 非対象 layer は status=no_pair。"""
    result = check_pair_freeze("L0", project_root=tmp_path)

    assert result["layer"] == "L0"
    assert result["pair"] is None
    assert result["pair_doc_exists"] is False
    assert result["pair_doc_path"] is None
    assert result["status"] == "no_pair"
    assert result["hint"] is None


def test_check_pair_freeze_active_only_filters_completed(tmp_path) -> None:
    """DoD 検証: W12 U-001 active_only は completed plan を除外する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    completed_plan = pair_dir / "L7-completed-sampleplan.md"
    draft_plan = pair_dir / "L7-draft-sampleplan.md"
    completed_plan.write_text("---\nstatus: completed\n---\n", encoding="utf-8")
    draft_plan.write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    result_all = check_pair_freeze("L6", project_root=tmp_path)
    result_active = check_pair_freeze("L6", project_root=tmp_path, active_only=True)

    assert result_all["pair_doc_exists"] is True
    assert result_all["status"] == "ok"
    assert result_all["active_only"] is False
    assert result_active["pair_doc_exists"] is True
    assert result_active["pair_doc_path"] == str(draft_plan)
    assert result_active["status"] == "ok"
    assert result_active["active_only"] is True


def test_check_pair_freeze_active_only_returns_pair_missing_when_only_completed(tmp_path) -> None:
    """DoD 検証: W12 U-002 active_only では completed only を missing と判定する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    completed_plan = pair_dir / "L7-completed-onlyplan.md"
    completed_plan.write_text("---\nstatus: completed\n---\n", encoding="utf-8")

    result = check_pair_freeze("L6", project_root=tmp_path, active_only=True)

    assert result["pair_doc_exists"] is False
    assert result["pair_doc_path"] is None
    assert result["status"] == "pair_missing"
    assert result["active_only"] is True


def test_check_pair_freeze_active_only_field_in_result(tmp_path) -> None:
    """DoD 検証: W12 U-003 result に active_only field を含む。"""
    result = check_pair_freeze("L0", project_root=tmp_path, active_only=True)

    assert "active_only" in result
    assert result["active_only"] is True


def test_check_pair_freeze_status_breakdown_counts(tmp_path) -> None:
    """DoD 検証: W15 U-001 pair PLAN の status 別件数を返す。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L7-draft-sampleplan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    (pair_dir / "L7-in-progress-sampleplan.md").write_text(
        "---\nstatus: in_progress\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L7-completed-sampleplan.md").write_text(
        "---\nstatus: completed\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L7-superseded-sampleplan.md").write_text(
        "---\nstatus: superseded\n---\n",
        encoding="utf-8",
    )

    result = check_pair_freeze("L6", project_root=tmp_path)

    assert result["status_breakdown"] == {
        "draft": 1,
        "in_progress": 1,
        "completed": 1,
        "superseded": 1,
        "other": 0,
    }


def test_check_pair_freeze_status_breakdown_handles_missing_status(tmp_path) -> None:
    """DoD 検証: W15 U-002 status 欠損は other に集計する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L7-missing-statusplan.md").write_text("---\nplan_id: sample\n---\n", encoding="utf-8")

    result = check_pair_freeze("L6", project_root=tmp_path)

    assert result["status_breakdown"]["other"] == 1


def test_check_pair_freeze_status_breakdown_field_present_in_no_pair(tmp_path) -> None:
    """DoD 検証: W15 U-003 no_pair でも status_breakdown field を返す。"""
    result = check_pair_freeze("L0", project_root=tmp_path)

    assert "status_breakdown" in result
    assert result["status_breakdown"] == {}
