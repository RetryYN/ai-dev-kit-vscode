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
