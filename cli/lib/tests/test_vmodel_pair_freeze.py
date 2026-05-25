"""Tests for cli.lib.vmodel_pair_freeze."""

from __future__ import annotations

import subprocess
from datetime import date, timedelta

from cli.lib.vmodel_pair_freeze import (
    apply_stale_patches,
    VMODEL_PAIRS,
    apply_stale_revisions,
    check_pair_freeze,
    generate_stale_patch,
    get_pair,
    rollback_stale_revisions,
    suggest_stale_revisions,
)


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


def test_check_pair_freeze_since_days_filters_old(tmp_path) -> None:
    """DoD 検証: W17 U-001 since_days は古い revised PLAN を除外する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L7-old-plan.md").write_text(
        "---\nrevised: 2000-01-01\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    today = date.today().isoformat()
    (pair_dir / "L7-new-plan.md").write_text(
        f"---\nrevised: {today}\nstatus: draft\n---\n",
        encoding="utf-8",
    )

    result = check_pair_freeze("L6", project_root=tmp_path, since_days=30)

    assert result["status"] == "ok"
    assert result["pair_doc_exists"] is True
    assert result["pair_doc_path"] == str(pair_dir / "L7-new-plan.md")


def test_check_pair_freeze_since_days_handles_missing_revised(tmp_path) -> None:
    """DoD 検証: W17 U-002 revised 不在時は created を使う。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    created = (date.today() - timedelta(days=1)).isoformat()
    (pair_dir / "L7-created-only-plan.md").write_text(
        f"---\ncreated: {created}\nstatus: draft\n---\n",
        encoding="utf-8",
    )

    result = check_pair_freeze("L6", project_root=tmp_path, since_days=30)

    assert result["status"] == "ok"
    assert result["pair_doc_exists"] is True
    assert result["pair_doc_path"] == str(pair_dir / "L7-created-only-plan.md")


def test_check_pair_freeze_since_days_field_in_result(tmp_path) -> None:
    """DoD 検証: W17 U-003 result に since_days field を含む。"""
    result = check_pair_freeze("L0", project_root=tmp_path, since_days=30)

    assert "since_days" in result
    assert result["since_days"] == 30


def test_check_pair_freeze_stale_count_when_since_days_set(tmp_path) -> None:
    """DoD 検証: W19 U-001 since_days 指定時は期間外 PLAN 数を stale_count に集計する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L7-old-plan.md").write_text(
        "---\nrevised: 2000-01-01\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    today = date.today().isoformat()
    (pair_dir / "L7-new-plan.md").write_text(
        f"---\nrevised: {today}\nstatus: draft\n---\n",
        encoding="utf-8",
    )

    result = check_pair_freeze("L6", project_root=tmp_path, since_days=30)

    assert result["status"] == "ok"
    assert result["stale_count"] == 1


def test_check_pair_freeze_stale_count_zero_when_since_days_none(tmp_path) -> None:
    """DoD 検証: W19 U-002 since_days=None では stale_count=0。"""
    pair_dir = tmp_path / "docs" / "plans" / "L7"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L7-old-plan.md").write_text(
        "---\nrevised: 2000-01-01\nstatus: draft\n---\n",
        encoding="utf-8",
    )

    result = check_pair_freeze("L6", project_root=tmp_path)

    assert result["status"] == "ok"
    assert result["stale_count"] == 0


def test_check_pair_freeze_stale_count_field_in_result(tmp_path) -> None:
    """DoD 検証: W19 U-003 result に stale_count field を含む。"""
    result = check_pair_freeze("L0", project_root=tmp_path, since_days=30)

    assert "stale_count" in result
    assert result["stale_count"] == 0


def test_suggest_stale_revisions_finds_old_plans(tmp_path) -> None:
    """DoD 検証: W29 U-001 古い pair PLAN に revised 更新候補を返す。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    plan_path = pair_dir / "L9-old-plan.md"
    plan_path.write_text(
        "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\n---\n",
        encoding="utf-8",
    )

    result = suggest_stale_revisions("L4", project_root=tmp_path, since_days=30)

    assert len(result) == 1
    assert result[0] == {
        "plan_id": "L9-old-plan",
        "plan_path": str(plan_path),
        "current_revised": "2000-01-01",
        "suggested_revised": date.today().isoformat(),
    }


def test_suggest_stale_revisions_skips_recent(tmp_path) -> None:
    """DoD 検証: W29 U-002 直近 revised の pair PLAN は候補から除外する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    pair_dir.joinpath("L9-new-plan.md").write_text(
        f"---\nplan_id: L9-new-plan\nrevised: {date.today().isoformat()}\n---\n",
        encoding="utf-8",
    )

    result = suggest_stale_revisions("L4", project_root=tmp_path, since_days=30)

    assert result == []


def test_suggest_stale_revisions_returns_empty_when_no_pair(tmp_path) -> None:
    """DoD 検証: W29 U-003 pair を持たない layer は空 list を返す。"""
    result = suggest_stale_revisions("L0", project_root=tmp_path, since_days=30)

    assert result == []


def test_apply_stale_revisions_dry_run(tmp_path) -> None:
    """DoD 検証: W35 U-001 dry_run は候補だけ返し frontmatter を更新しない。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    plan_path = pair_dir / "L9-old-plan.md"
    original = "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\nstatus: draft\n---\n"
    plan_path.write_text(original, encoding="utf-8")

    result = apply_stale_revisions("L4", project_root=tmp_path, since_days=30, dry_run=True)

    assert result == [
        {
            "plan_id": "L9-old-plan",
            "plan_path": str(plan_path),
            "status": "dry_run",
            "new_revised": date.today().isoformat(),
        }
    ]
    assert plan_path.read_text(encoding="utf-8") == original


def test_apply_stale_revisions_writes_when_not_dry_run(tmp_path) -> None:
    """DoD 検証: W35 U-002 dry_run=False は revised を当日に更新する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    plan_path = pair_dir / "L9-old-plan.md"
    plan_path.write_text(
        "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )

    result = apply_stale_revisions("L4", project_root=tmp_path, since_days=30, dry_run=False)

    assert result == [
        {
            "plan_id": "L9-old-plan",
            "plan_path": str(plan_path),
            "status": "updated",
            "new_revised": date.today().isoformat(),
        }
    ]
    updated_text = plan_path.read_text(encoding="utf-8")
    assert f"revised: {date.today().isoformat()}" in updated_text
    assert "status: draft" in updated_text
    assert updated_text.endswith("---\nbody\n")


def test_apply_stale_revisions_returns_empty_when_no_pair(tmp_path) -> None:
    """DoD 検証: W35 U-003 pair を持たない layer は空 list を返す。"""
    result = apply_stale_revisions("L0", project_root=tmp_path, since_days=30, dry_run=False)

    assert result == []


def test_generate_stale_patch_returns_unified_diff(tmp_path) -> None:
    """DoD 検証: W38 U-001 stale PLAN から revised 更新 patch を生成する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    plan_path = pair_dir / "L9-old-plan.md"
    plan_path.write_text(
        "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )

    result = generate_stale_patch("L4", project_root=tmp_path, since_days=30)

    assert len(result) == 1
    assert result[0]["plan_id"] == "L9-old-plan"
    assert result[0]["plan_path"] == str(plan_path)
    assert result[0]["before_revised"] == "2000-01-01"
    assert result[0]["after_revised"] == date.today().isoformat()
    assert "@@" in result[0]["unified_diff"]
    assert "-revised: 2000-01-01" in result[0]["unified_diff"]
    assert f"+revised: {date.today().isoformat()}" in result[0]["unified_diff"]


def test_generate_stale_patch_skips_recent(tmp_path) -> None:
    """DoD 検証: W38 U-002 当日 revised の PLAN は patch 対象外。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    pair_dir.joinpath("L9-new-plan.md").write_text(
        f"---\nplan_id: L9-new-plan\nrevised: {date.today().isoformat()}\nstatus: draft\n---\n",
        encoding="utf-8",
    )

    result = generate_stale_patch("L4", project_root=tmp_path, since_days=30)

    assert result == []


def test_generate_stale_patch_returns_empty_when_no_pair(tmp_path) -> None:
    """DoD 検証: W38 U-003 pair を持たない layer は空 list を返す。"""
    result = generate_stale_patch("L0", project_root=tmp_path, since_days=30)

    assert result == []


def test_apply_stale_patches_dry_run(tmp_path) -> None:
    """DoD 検証: W44 U-001 dry_run は patch のみ返し frontmatter を変更しない。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    plan_path = pair_dir / "L9-old-plan.md"
    original = "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\nstatus: draft\n---\nbody\n"
    plan_path.write_text(original, encoding="utf-8")

    result = apply_stale_patches("L4", project_root=tmp_path, since_days=30, dry_run=True)

    assert result["status"] == "dry_run"
    assert result["errors"] == []
    assert len(result["patches"]) == 1
    assert result["patches"][0]["plan_path"] == str(plan_path)
    assert plan_path.read_text(encoding="utf-8") == original


def test_apply_stale_patches_no_patches(tmp_path) -> None:
    """DoD 検証: W44 U-002 pair doc 不在なら status=no_patches。"""
    result = apply_stale_patches("L4", project_root=tmp_path, since_days=30, dry_run=True)

    assert result == {"status": "no_patches", "patches": [], "errors": []}


def test_apply_stale_patches_handles_apply_error(tmp_path, monkeypatch) -> None:
    """DoD 検証: W44 U-003 git apply 失敗時は status=failed と errors を返す。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    pair_dir.joinpath("L9-old-plan.md").write_text(
        "---\nplan_id: L9-old-plan\nrevised: 2000-01-01\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout="", stderr="apply failed")

    monkeypatch.setattr("cli.lib.vmodel_pair_freeze.subprocess.run", fake_run)

    result = apply_stale_patches("L4", project_root=tmp_path, since_days=30, dry_run=False)

    assert result["status"] == "failed"
    assert len(result["patches"]) == 1
    assert len(result["errors"]) == 1
    assert "apply failed" in result["errors"][0]


def test_rollback_stale_revisions_dry_run(tmp_path) -> None:
    """DoD 検証: W43 U-001 dry_run は rollback 候補だけ返し frontmatter を更新しない。"""
    plan_path = tmp_path / "docs" / "plans" / "L9" / "L9-old-plan.md"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(
        f"---\nplan_id: L9-old-plan\nrevised: {date.today().isoformat()}\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )
    audit_dir = tmp_path / ".helix" / "audit"
    audit_dir.mkdir(parents=True)
    audit_dir.joinpath("stale-revisions.json").write_text(
        '[{"applied_at":"2026-05-25T00:00:00+09:00","layer":"L4","changes":[{"plan_path":"'
        + str(plan_path)
        + '","before_revised":"2000-01-01","after_revised":"'
        + date.today().isoformat()
        + '"}]}]',
        encoding="utf-8",
    )

    result = rollback_stale_revisions(project_root=tmp_path, dry_run=True)

    assert result == {
        "status": "dry_run",
        "rolled_back": [{"plan_path": str(plan_path), "restored_revised": "2000-01-01"}],
    }
    assert f"revised: {date.today().isoformat()}" in plan_path.read_text(encoding="utf-8")


def test_rollback_stale_revisions_writes_when_not_dry_run(tmp_path) -> None:
    """DoD 検証: W43 U-002 dry_run=False は latest audit に従って revised を復元する。"""
    plan_path = tmp_path / "docs" / "plans" / "L9" / "L9-old-plan.md"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(
        f"---\nplan_id: L9-old-plan\nrevised: {date.today().isoformat()}\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )
    audit_dir = tmp_path / ".helix" / "audit"
    audit_dir.mkdir(parents=True)
    audit_dir.joinpath("stale-revisions.json").write_text(
        '[{"applied_at":"2026-05-25T00:00:00+09:00","layer":"L4","changes":[{"plan_path":"'
        + str(plan_path)
        + '","before_revised":"2000-01-01","after_revised":"'
        + date.today().isoformat()
        + '"}]}]',
        encoding="utf-8",
    )

    result = rollback_stale_revisions(project_root=tmp_path, dry_run=False)

    assert result == {
        "status": "rolled_back",
        "rolled_back": [{"plan_path": str(plan_path), "restored_revised": "2000-01-01"}],
    }
    assert "revised: 2000-01-01" in plan_path.read_text(encoding="utf-8")


def test_rollback_stale_revisions_no_audit(tmp_path) -> None:
    """DoD 検証: W43 U-003 audit 不在時は no_audit を返す。"""
    result = rollback_stale_revisions(project_root=tmp_path, dry_run=False)

    assert result == {"status": "no_audit", "rolled_back": []}
