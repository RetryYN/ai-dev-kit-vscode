from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import push_gate
import coding_rule_lint


def _write_plan(
    root: Path,
    plan_id: str,
    *,
    status: str = "completed",
    tl_review: str | None = "approve",
    subdir: str = "add-feature",
    plan_scope: str | None = None,
    workflow: str = "add-feature",
    extra_frontmatter: dict[str, object] | None = None,
) -> Path:
    plan_path = root / "docs" / "plans" / subdir / f"{plan_id}.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"plan_id: {plan_id}",
        f"title: {plan_id}",
        "kind: add-impl",
        "layer: L4",
        "drive: be",
        f"workflow: {workflow}",
        f"status: {status}",
    ]
    if plan_scope is not None:
        lines.append(f"plan_scope: {plan_scope}")
    if tl_review is not None:
        lines.append(f"tl_review: {tl_review}")
    for key, value in (extra_frontmatter or {}).items():
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                lines.extend(f"  - {json.dumps(item)}" for item in value)
            else:
                lines.append(f"{key}: []")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    lines.extend(["---", "", "# body", ""])
    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


def _write_approved_boundary_plan(
    root: Path,
    plan_id: str,
    *,
    status: str = "draft",
    tl_review: str | None = "approve",
    workflow: str = "add-feature",
    plan_scope: str = "action",
    extra_frontmatter: dict[str, object] | None = None,
) -> Path:
    boundary_frontmatter: dict[str, object] = {
        "approval_boundary": "This PLAN is only a ticket and requires explicit approval before implementation.",
        "approval_required_before_l7_work": True,
        "current_task_scope": "feature_ticket_only",
        "unlock_conditions": ["explicit approval"],
    }
    for key, value in (extra_frontmatter or {}).items():
        if value is None:
            boundary_frontmatter.pop(key, None)
        else:
            boundary_frontmatter[key] = value
    return _write_plan(
        root,
        plan_id,
        status=status,
        tl_review=tl_review,
        workflow=workflow,
        plan_scope=plan_scope,
        extra_frontmatter=boundary_frontmatter,
    )


def _write_handover_review_state(
    root: Path,
    *,
    task_id: str = "GOAL-V3-PERSONAL-L0-L6",
    task_status: str = "completed",
    tl_review: str | None = "approve",
    review_status: str | None = "completed",
    reviewed_at: str | None = "2026-06-27T21:22:14+09:00",
    reviewed_by: str | None = "tl",
    extra_payload: dict[str, object] | None = None,
) -> None:
    handover_dir = root / ".helix" / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "task": {
            "id": task_id,
            "status": task_status,
        }
    }
    review: dict[str, object] = {}
    if tl_review is not None:
        review["tl_review"] = tl_review
    if review_status is not None:
        review["review_status"] = review_status
    if reviewed_at is not None:
        review["reviewed_at"] = reviewed_at
    if reviewed_by is not None:
        review["reviewed_by"] = reviewed_by
    if review:
        payload["review"] = review
    if extra_payload:
        payload.update(extra_payload)
    (handover_dir / "CURRENT.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _stub_ahead(monkeypatch, plan_ids: list[str]) -> None:
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: plan_ids)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Codex",
        "GIT_AUTHOR_EMAIL": "codex@example.com",
        "GIT_COMMITTER_NAME": "Codex",
        "GIT_COMMITTER_EMAIL": "codex@example.com",
    }
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc


def _write_push_gate_vg_assets(repo: Path) -> None:
    anchor_path = repo / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml"
    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    anchor_path.write_text("anchors: {}\n", encoding="utf-8")

    config_dir = repo / "cli" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "functional-registry.yaml").write_text("entries: []\n", encoding="utf-8")
    (config_dir / "coding-rule-registry.yaml").write_text(
        "\n".join(
            [
                "entries:",
                "  - id: CR-CODE-PY",
                "    rule: python scripts stay mechanically linted",
                "    sot_section: コーディング規約",
                "    linter_tool:",
                "      - py_compile",
                "    enforcement:",
                "      kind: ci_gate",
                "      paths: []",
                "      status: partial",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (config_dir / "coding-rule-registry-baseline.json").write_text(
        json.dumps(
            {
                "intentional_baseline": True,
                "owner": "codex",
                "created": "2026-06-14",
                "expiry": "2026-09-12",
                "generated_by": "test",
                "reports": [
                    {
                        "check_name": "check_coding_rule_lint",
                        "mode": "advisory",
                        "findings": [],
                        "metrics": {"finding_count": 0},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _init_repo_with_bare_origin(tmp_path: Path, *, branch: str) -> tuple[Path, Path]:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    origin.mkdir(parents=True, exist_ok=True)
    _git(tmp_path, "init", "--bare", origin.as_posix())
    _git(tmp_path, "init", "--initial-branch", branch, repo.as_posix())
    _git(repo, "remote", "add", "origin", origin.as_posix())
    return repo, origin


def test_run_gate_review_passes_with_explicit_plan_id(tmp_path: Path) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result == {
        "id": "G-review",
        "passed": True,
        "detail": f"{plan_id} scope=action status=completed tl_review=approve",
        "fix": "なし",
    }


def test_run_gate_review_process_scope_passes_with_draft_and_approve(tmp_path: Path) -> None:
    # 長命 process-scope PLAN は status 未完了でも tl_review=approve なら pass (TL 判定A)
    plan_id = "process-2026-06-05-registration-detection-cluster"
    _write_plan(tmp_path, plan_id, status="draft", subdir="process", plan_scope="process")

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is True
    assert "scope=process" in result["detail"]


def test_run_gate_review_process_scope_fails_when_tl_review_missing(tmp_path: Path) -> None:
    # process-scope でも tl_review=approve は必須
    plan_id = "process-2026-06-05-registration-detection-cluster"
    _write_plan(tmp_path, plan_id, status="draft", tl_review=None, subdir="process", plan_scope="process")

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "tl_review" in result["detail"] or "tl_review" in result.get("detail", "")


def test_run_gate_review_action_scope_fails_with_draft_even_if_approved(tmp_path: Path) -> None:
    # action-scope は status 完了が必須 (gate を緩めていないことの回帰)
    plan_id = "add-feature-2026-06-05-registry-detector-base"
    _write_plan(tmp_path, plan_id, status="draft", plan_scope="action")

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


def test_run_gate_review_action_scope_boundary_passes_with_approved_deferred_add_feature(
    tmp_path: Path,
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(tmp_path, plan_id)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is True
    assert result["detail"] == f"{plan_id} scope=action status=draft tl_review=approve"


def test_run_gate_review_action_scope_boundary_fails_with_missing_plan_scope(
    tmp_path: Path,
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(tmp_path, plan_id, plan_scope=None)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert result["detail"] == f"review prerequisites missing: {plan_id} status=draft"


@pytest.mark.parametrize("tl_review", [None, "changes_required"])
def test_run_gate_review_action_scope_boundary_fails_without_approve_tl_review(
    tmp_path: Path, tl_review: str | None
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(tmp_path, plan_id, tl_review=tl_review)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "tl_review" in result["detail"]


@pytest.mark.parametrize(
    ("field_value", "expected_fragment"),
    [
        (None, "status=draft"),
        ("", "status=draft"),
        ("ticket only", "status=draft"),
    ],
)
def test_run_gate_review_action_scope_boundary_fails_without_valid_approval_boundary(
    tmp_path: Path, field_value: str | None, expected_fragment: str
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    extra_frontmatter = {"approval_boundary": field_value}
    _write_approved_boundary_plan(tmp_path, plan_id, extra_frontmatter=extra_frontmatter)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert expected_fragment in result["detail"]


@pytest.mark.parametrize(
    "extra_frontmatter",
    [
        {"approval_required_before_l7_work": False},
        {"approval_required_before_l7_work": "true"},
        {"approval_required_before_l7_work": False, "approval_required_before_ci": False},
    ],
)
def test_run_gate_review_action_scope_boundary_fails_without_true_boolean_approval_required(
    tmp_path: Path, extra_frontmatter: dict[str, object]
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(tmp_path, plan_id, extra_frontmatter=extra_frontmatter)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


def test_run_gate_review_action_scope_boundary_fails_without_any_approval_required_key(
    tmp_path: Path,
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(
        tmp_path,
        plan_id,
        extra_frontmatter={
            "approval_required_before_l7_work": None,
            "approval_boundary": "This ticket still requires explicit approval.",
            "current_task_scope": "feature_ticket_only",
            "unlock_conditions": ["explicit approval"],
        },
    )

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


def test_run_gate_review_action_scope_boundary_fails_when_workflow_is_not_add_feature(
    tmp_path: Path,
) -> None:
    plan_id = "process-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(tmp_path, plan_id, workflow="refactor")

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


@pytest.mark.parametrize("current_task_scope", ["parked_feature_ticket_only", "implementation"])
def test_run_gate_review_action_scope_boundary_fails_with_disallowed_current_task_scope(
    tmp_path: Path, current_task_scope: str
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    _write_approved_boundary_plan(
        tmp_path,
        plan_id,
        extra_frontmatter={"current_task_scope": current_task_scope},
    )

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


@pytest.mark.parametrize(
    "unlock_conditions",
    [
        None,
        "",
        [],
    ],
)
def test_run_gate_review_action_scope_boundary_fails_without_unlock_conditions(
    tmp_path: Path, unlock_conditions: object
) -> None:
    plan_id = "add-feature-2026-06-13-l7-unit-closure"
    extra_frontmatter = {"unlock_conditions": unlock_conditions}
    _write_approved_boundary_plan(tmp_path, plan_id, extra_frontmatter=extra_frontmatter)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "status=draft" in result["detail"]


def test_run_gate_review_mixed_action_completed_and_process_draft_passes(tmp_path: Path, monkeypatch) -> None:
    # action(completed+approve) + process(draft+approve) の 2 PLAN ahead は pass
    action_id = "add-feature-2026-06-05-registry-detector-base"
    process_id = "process-2026-06-05-registration-detection-cluster"
    _write_plan(tmp_path, action_id, status="completed", plan_scope="action")
    _write_plan(tmp_path, process_id, status="draft", subdir="process", plan_scope="process")
    _stub_ahead(monkeypatch, [action_id, process_id])

    result = push_gate.run_gate_review(action_id, tmp_path)

    assert result["passed"] is True
    assert "scope=process" in result["detail"]
    assert "scope=action" in result["detail"]


def test_run_gate_review_fails_when_status_is_not_completed(tmp_path: Path) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id, status="in_progress")

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert result["id"] == "G-review"
    assert "status=in_progress" in result["detail"]


def test_run_gate_review_fails_when_tl_review_is_missing(tmp_path: Path) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id, tl_review=None)

    result = push_gate.run_gate_review(plan_id, tmp_path)

    assert result["passed"] is False
    assert "tl_review" in result["detail"]


def test_run_gate_review_uses_handover_active_plan_id(tmp_path: Path) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id)
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    (handover_dir / "CURRENT.json").write_text(
        '{"plan_id": "add-feature-2026-06-03-gate-driven-push"}',
        encoding="utf-8",
    )

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is True
    assert plan_id in result["detail"]


def test_run_gate_review_falls_back_to_handover_review_when_no_plan_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path)
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is True
    assert result["detail"] == (
        "GOAL-V3-PERSONAL-L0-L6 kind=handover_task "
        "status=completed tl_review=approve review_status=completed"
    )


def test_run_gate_review_handover_fails_closed_when_handover_plan_id_is_ambiguous(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(
        tmp_path,
        extra_payload={
            "plan_id": "add-feature-2026-06-03-gate-driven-push",
            "related": [{"plan_id": "add-feature-2026-06-03-gate-driven-push-docs"}],
        },
    )
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "plan_id" in result["detail"]


def test_run_gate_review_handover_fails_closed_when_review_status_is_changes_required(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, review_status="changes_required")
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "review_status=changes_required" in result["detail"]


def test_run_gate_review_handover_fails_closed_when_review_status_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, review_status=None)
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "review_status=<missing>" in result["detail"]


def test_run_gate_review_handover_fails_closed_when_reviewed_at_is_invalid(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, reviewed_at="invalid-iso-datetime")
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "reviewed_at=invalid-iso-datetime" in result["detail"]


def test_run_gate_review_handover_fails_closed_when_reviewed_by_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, reviewed_by=None)
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "reviewed_by=<missing>" in result["detail"]


def test_run_gate_review_handover_passes_with_completed_review_cross_fields(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, review_status="finalized")
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is True
    assert result["detail"] == (
        "GOAL-V3-PERSONAL-L0-L6 kind=handover_task "
        "status=completed tl_review=approve review_status=finalized"
    )


def test_run_gate_review_handover_fails_closed_when_tl_review_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(tmp_path, tl_review=None)
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert result["detail"] == (
        "review prerequisites missing: GOAL-V3-PERSONAL-L0-L6 tl_review=<missing>"
    )


def test_run_gate_review_handover_fails_closed_when_status_is_ready_for_review(
    tmp_path: Path, monkeypatch
) -> None:
    _write_handover_review_state(
        tmp_path,
        task_status="ready_for_review",
        tl_review="approve",
        review_status="completed",
    )
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert result["detail"] == (
        "review prerequisites missing: GOAL-V3-PERSONAL-L0-L6 status=ready_for_review"
    )


def test_run_gate_review_fails_when_plan_id_cannot_be_resolved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "plan_id" in result["detail"]


def test_run_gate_review_fails_when_ahead_commit_has_multiple_plan_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        push_gate,
        "_ahead_commit_plan_ids",
        lambda project_root: ["add-feature-2026-06-03-a", "add-feature-2026-06-03-b"],
    )

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "multiple" in result["detail"]


def test_run_gate_review_passes_when_all_ahead_plans_are_approved(
    tmp_path: Path, monkeypatch
) -> None:
    representative = "add-feature-2026-06-03-gate-driven-push"
    sibling = "add-feature-2026-06-03-gate-driven-push-docs"
    _write_plan(tmp_path, representative)
    _write_plan(tmp_path, sibling, status="finalized")
    _stub_ahead(monkeypatch, [representative, sibling])

    result = push_gate.run_gate_review(representative, tmp_path)

    assert result["passed"] is True
    assert representative in result["detail"]
    assert sibling in result["detail"]


def test_run_gate_review_fails_when_any_ahead_plan_is_missing_tl_review(
    tmp_path: Path, monkeypatch
) -> None:
    representative = "add-feature-2026-06-03-gate-driven-push"
    missing_review = "add-feature-2026-06-03-gate-driven-push-docs"
    _write_plan(tmp_path, representative)
    _write_plan(tmp_path, missing_review, tl_review=None)
    _stub_ahead(monkeypatch, [representative, missing_review])

    result = push_gate.run_gate_review(representative, tmp_path)

    assert result["passed"] is False
    assert missing_review in result["detail"]
    assert "tl_review=<missing>" in result["detail"]


def test_run_gate_review_fails_when_any_ahead_plan_status_is_not_completed_or_finalized(
    tmp_path: Path, monkeypatch
) -> None:
    representative = "add-feature-2026-06-03-gate-driven-push"
    incomplete = "add-feature-2026-06-03-gate-driven-push-docs"
    _write_plan(tmp_path, representative)
    _write_plan(tmp_path, incomplete, status="in_progress")
    _stub_ahead(monkeypatch, [representative, incomplete])

    result = push_gate.run_gate_review(representative, tmp_path)

    assert result["passed"] is False
    assert incomplete in result["detail"]
    assert "status=in_progress" in result["detail"]


def test_run_gate_review_fails_when_explicit_plan_id_is_not_in_ahead_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    representative = "add-feature-2026-06-03-gate-driven-push"
    sibling = "add-feature-2026-06-03-gate-driven-push-docs"
    _write_plan(tmp_path, representative)
    _write_plan(tmp_path, sibling)
    _stub_ahead(monkeypatch, [representative, sibling])

    result = push_gate.run_gate_review("add-feature-2026-06-03-outside-scope", tmp_path)

    assert result["passed"] is False
    assert "explicit=add-feature-2026-06-03-outside-scope" in result["detail"]


def test_run_gate_review_uses_single_ahead_plan_for_backward_compatibility(
    tmp_path: Path, monkeypatch
) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id)
    _stub_ahead(monkeypatch, [plan_id])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is True
    assert result["detail"] == f"{plan_id} scope=action status=completed tl_review=approve"


def test_collect_vg_overview_changed_files_context_falls_back_to_default_branch_merge_base(
    tmp_path: Path,
) -> None:
    repo, _origin = _init_repo_with_bare_origin(tmp_path, branch="main")
    tracked = repo / "tracked.py"
    tracked.write_text("print('base')\n", encoding="utf-8")
    _git(repo, "add", "tracked.py")
    _git(repo, "commit", "-m", "base")
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature/no-upstream")

    tracked.write_text("print('feature change')\n", encoding="utf-8")
    _git(repo, "add", "tracked.py")
    _git(repo, "commit", "-m", "feature change")
    (repo / "scratch.py").write_text("print('untracked')\n", encoding="utf-8")

    payload = push_gate._collect_vg_overview_changed_files_context(
        repo,
        remote="origin",
        branch="feature/no-upstream",
    )

    assert payload["status"] == "available"
    assert payload["source"] == "merge-base"
    assert payload["base_ref"] == "origin/main"
    assert payload["files"] == ["tracked.py", "scratch.py"]
    assert payload["env_value"] == "tracked.py\nscratch.py"


def test_run_gate_vg_overview_injects_changed_files_context_and_restores_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, _origin = _init_repo_with_bare_origin(tmp_path, branch="dogfood")
    _write_push_gate_vg_assets(repo)
    (repo / "stable.py").write_text("print('stable')\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(repo, "push", "-u", "origin", "dogfood")

    (repo / "new_bad.py").write_text("def broken(\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "new_bad.py")
    _git(repo, "commit", "-m", "new violation")
    (repo / "scratch.py").write_text("print('scratch')\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def _fake_collect(root: Path) -> dict[str, object]:
        captured["env_value"] = os.environ.get("HELIX_CHANGED_FILES")
        summary = coding_rule_lint.collect_coding_rule_lint_gate_summary(
            repo_root=root,
            registry_path=Path(root) / "cli/config/coding-rule-registry.yaml",
            baseline_path=Path(root) / "cli/config/coding-rule-registry-baseline.json",
        )
        captured["summary"] = summary
        return {
            "vg_overview": {
                "overall_clean": False,
                "required_clean": {"coding_rule_lint": summary},
                "pair_status": {},
            },
            "g7_subcheck": {},
        }

    monkeypatch.setattr(push_gate, "collect_vg_overview", _fake_collect)
    monkeypatch.setenv("HELIX_CHANGED_FILES", "keep-me")

    result = push_gate.run_gate_vg_overview(repo, remote="origin", branch="dogfood")

    assert result["passed"] is False
    assert captured["env_value"] == "new_bad.py\nscratch.py"
    assert captured["summary"] == {
        "clean": False,
        "finding_count": 1,
        "source_status": "available_nonempty",
        "skipped_reason": None,
    }
    assert os.environ["HELIX_CHANGED_FILES"] == "keep-me"


def test_run_gate_vg_overview_reports_unavailable_changed_files_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_push_gate_vg_assets(tmp_path)
    monkeypatch.setattr(
        push_gate,
        "_collect_vg_overview_changed_files_context",
        lambda project_root, remote, branch: {
            "status": "unavailable",
            "source": "unresolved",
            "base_ref": None,
            "files": [],
            "env_value": None,
            "reason": "changed-files unavailable: upstream origin/topic missing; merge-base with origin/main unavailable",
        },
    )
    monkeypatch.setattr(
        push_gate,
        "collect_vg_overview",
        lambda root: {
            "vg_overview": {
                "overall_clean": True,
                "required_clean": {
                    "coding_rule_lint": {
                        "clean": True,
                        "finding_count": 0,
                        "source_status": "unavailable",
                        "skipped_reason": "changed-files unavailable",
                    }
                },
                "pair_status": {},
            },
            "g7_subcheck": {
                "ut_total": 88,
                "anchored": 88,
                "exec_pass": 88,
                "missing": 0,
                "unanchored_but_exists": 0,
            },
        },
    )

    result = push_gate.run_gate_vg_overview(tmp_path, remote="origin", branch="topic")

    assert result["passed"] is True
    assert "changed-files unavailable" in result["detail"]
    assert "origin/topic missing" in result["detail"]


def test_run_gate_nondestructive_ignores_cli_helix_test_tmpdir_cleanup(monkeypatch) -> None:
    diff_output = "\n".join(
        [
            "diff --git a/cli/helix-test b/cli/helix-test",
            "--- a/cli/helix-test",
            "+++ b/cli/helix-test",
            '@@ -10,0 +11 @@',
            '+rm -rf "$tmp"',
        ]
    )
    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, diff_output, ""),
    )

    result = push_gate.run_gate_nondestructive()

    assert result == {
        "id": "G-nondestructive",
        "passed": True,
        "detail": "no destructive pattern",
        "fix": "なし",
    }


def test_run_gate_nondestructive_still_blocks_nonexcluded_cli_script(monkeypatch) -> None:
    diff_output = "\n".join(
        [
            "diff --git a/cli/helix-foo b/cli/helix-foo",
            "--- a/cli/helix-foo",
            "+++ b/cli/helix-foo",
            '@@ -10,0 +11 @@',
            '+rm -rf "$tmp"',
        ]
    )
    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate,
        "_run_command",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, diff_output, ""),
    )

    result = push_gate.run_gate_nondestructive()

    assert result["passed"] is False
    assert result["detail"] == 'destructive pattern: rm -rf in cli/helix-foo'


def test_run_all_gates_accepts_plan_id_and_allow_main(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        push_gate,
        "run_gate_tests",
        lambda **kwargs: push_gate._result("G-tests", True, "ok", "なし"),
    )
    monkeypatch.setattr(push_gate, "run_gate_catalog", lambda: push_gate._result("G-catalog", True, "ok", "なし"))
    monkeypatch.setattr(push_gate, "run_gate_secret", lambda: push_gate._result("G-secret", True, "ok", "なし"))
    monkeypatch.setattr(
        push_gate,
        "run_gate_ff",
        lambda remote, branch: push_gate._result("G-ff", True, f"{remote}/{branch}", "なし"),
    )
    monkeypatch.setattr(
        push_gate,
        "run_gate_attr",
        lambda remote, branch: push_gate._result("G-attr", True, f"{remote}/{branch}", "なし"),
    )
    monkeypatch.setattr(
        push_gate,
        "run_gate_nondestructive",
        lambda remote, branch: push_gate._result("G-nondestructive", True, f"{remote}/{branch}", "なし"),
    )

    def fake_review(plan_id: str | None, project_root: Path) -> dict:
        calls.append((plan_id or "", project_root))
        return push_gate._result("G-review", True, "ok", "なし")

    monkeypatch.setattr(push_gate, "run_gate_review", fake_review)
    monkeypatch.setattr(
        push_gate,
        "run_gate_vg_overview",
        lambda project_root, remote, branch: push_gate._result(
            "G-vg-overview",
            True,
            f"{remote}/{branch}",
            "なし",
        ),
    )
    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))

    payload = push_gate.run_all_gates(
        execute=False,
        remote="origin",
        branch="dogfood",
        plan_id="add-feature-2026-06-03-gate-driven-push",
        allow_main=True,
    )

    assert payload["ok"] is True
    assert [gate["id"] for gate in payload["gates"]] == [
        "G-tests",
        "G-catalog",
        "G-secret",
        "G-ff",
        "G-attr",
        "G-nondestructive",
        "G-review",
        "G-vg-overview",
    ]
    assert payload["plan_id"] == "add-feature-2026-06-03-gate-driven-push"
    assert payload["allow_main"] is True
    assert calls == [("add-feature-2026-06-03-gate-driven-push", Path("/tmp/repo"))]


def test_decide_test_tier_returns_full_for_explicit_full_request() -> None:
    selector = {
        "pytest_targets": ["cli/lib/tests/test_push_gate.py"],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/push_gate.py"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": True, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


@pytest.mark.parametrize("branch", ["main", "release/2026.06"])
def test_decide_test_tier_returns_full_for_protected_branches(branch: str) -> None:
    selector = {
        "pytest_targets": ["cli/lib/tests/test_push_gate.py"],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/push_gate.py"], "source_status": "available_nonempty"},
        branch,
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_when_allow_main_is_set() -> None:
    selector = {
        "pytest_targets": ["cli/lib/tests/test_push_gate.py"],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/push_gate.py"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": True},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_when_changed_files_are_unavailable() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": [], "source_status": "unavailable"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_when_source_status_is_missing() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["docs/commands/push.md"]},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


@pytest.mark.parametrize("source_status", ["", "weird", " AVAILABLE_NONEMPTY "])
def test_decide_test_tier_returns_full_for_unknown_source_status(source_status: str) -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["docs/commands/push.md"], "source_status": source_status},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_when_payload_is_not_a_dict() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(  # type: ignore[arg-type]
        ["docs/commands/push.md"],
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


@pytest.mark.parametrize("files_value", [None, "cli/lib/push_gate.py", {"path": "cli/lib/push_gate.py"}])
def test_decide_test_tier_returns_full_when_files_payload_is_malformed(files_value: object) -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": files_value, "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


@pytest.mark.parametrize(
    "selector",
    [
        [],
        {"pytest_targets": "cli/lib/tests/test_push_gate.py", "bats_targets": [], "has_code_changes": True, "unmapped_code_files": []},
        {"pytest_targets": [], "bats_targets": [], "has_code_changes": "false", "unmapped_code_files": []},
    ],
)
def test_decide_test_tier_returns_full_when_selector_payload_is_malformed(selector: object) -> None:
    tier = push_gate.decide_test_tier(
        {"files": ["docs/commands/push.md"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,  # type: ignore[arg-type]
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_for_full_trigger_paths() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {
            "files": ["docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md"],
            "source_status": "available_nonempty",
        },
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_auto_for_docs_only_known_good_payload() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": False,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {
            "files": ["docs/plans/add-feature/sample.md"],
            "source_status": "available_nonempty",
        },
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "auto"


def test_decide_test_tier_returns_full_when_selector_is_empty_for_code_changes() -> None:
    selector = {
        "pytest_targets": [],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/some_module.py"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "full"


def test_decide_test_tier_returns_full_when_test_files_were_deleted_or_renamed() -> None:
    selector = {
        "pytest_targets": ["cli/lib/tests/test_push_gate.py"],
        "bats_targets": [],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/tests/test_push_gate.py"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
        has_deleted_or_renamed_tests=True,
    )

    assert tier == "full"


def test_decide_test_tier_returns_auto_for_localized_changes() -> None:
    selector = {
        "pytest_targets": ["cli/lib/tests/test_coding_rule_lint.py"],
        "bats_targets": ["cli/tests/helix-push.bats"],
        "has_code_changes": True,
        "unmapped_code_files": [],
    }

    tier = push_gate.decide_test_tier(
        {"files": ["cli/lib/coding_rule_lint.py", "cli/helix-push"], "source_status": "available_nonempty"},
        "dogfood",
        {"full": False, "test_tier": "auto", "allow_main": False},
        selector=selector,
    )

    assert tier == "auto"


def test_run_gate_tests_uses_selected_targets_and_reports_auto_tier(monkeypatch) -> None:
    commands: list[list[str]] = []

    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "changed_files",
        lambda upstream=None: {
            "files": ["cli/lib/coding_rule_lint.py", "cli/helix-push"],
            "source_status": "available_nonempty",
        },
    )
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "select_test_targets",
        lambda files, repo_root=None: {
            "pytest_targets": ["cli/lib/tests/test_coding_rule_lint.py"],
            "bats_targets": ["cli/tests/helix-push.bats"],
            "has_code_changes": True,
            "unmapped_code_files": [],
        },
    )
    monkeypatch.setattr(
        push_gate,
        "_has_deleted_or_renamed_tests",
        lambda project_root, upstream: False,
    )

    def _fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        commands.append(command)
        if command[:3] == ["python3", "-m", "pytest"]:
            return subprocess.CompletedProcess(command, 0, stdout="1 passed\n", stderr="")
        if command[0] == "bats":
            return subprocess.CompletedProcess(command, 0, stdout="1..1\nok 1 sample\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(push_gate, "_run_command", _fake_run)

    result = push_gate.run_gate_tests(remote="origin", branch="dogfood", test_tier="auto")

    assert result == {
        "id": "G-tests",
        "passed": True,
        "detail": "tier=auto, pytest 1 + bats 1",
        "fix": "なし",
    }
    assert commands == [
        ["python3", "-m", "pytest", "cli/lib/tests/test_coding_rule_lint.py", "-q"],
        ["bats", "cli/tests/helix-push.bats"],
    ]
    assert "-n" not in commands[0]


def test_run_gate_tests_falls_back_to_full_when_selector_is_unmapped(monkeypatch) -> None:
    commands: list[list[str]] = []

    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "changed_files",
        lambda upstream=None: {
            "files": ["cli/lib/unknown_module.py"],
            "source_status": "available_nonempty",
        },
    )
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "select_test_targets",
        lambda files, repo_root=None: {
            "pytest_targets": [],
            "bats_targets": [],
            "has_code_changes": True,
            "unmapped_code_files": ["cli/lib/unknown_module.py"],
        },
    )
    monkeypatch.setattr(
        push_gate,
        "_has_deleted_or_renamed_tests",
        lambda project_root, upstream: False,
    )

    def _fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        commands.append(command)
        if command == push_gate.PYTEST_FULL_TESTS_CMD:
            return subprocess.CompletedProcess(command, 0, stdout="7 passed\n", stderr="")
        if command[:1] == ["bats"]:
            return subprocess.CompletedProcess(command, 0, stdout="1..2\nok 1 a\nok 2 b\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(push_gate, "_run_command", _fake_run)
    monkeypatch.setattr(
        Path,
        "glob",
        lambda self, pattern: [Path("/tmp/repo/cli/tests/a.bats"), Path("/tmp/repo/cli/tests/b.bats")]
        if self == Path("/tmp/repo/cli/tests")
        else [],
    )

    result = push_gate.run_gate_tests(remote="origin", branch="dogfood", test_tier="auto")

    assert result == {
        "id": "G-tests",
        "passed": True,
        "detail": "tier=full, pytest 7 + bats 2",
        "fix": "なし",
    }
    assert commands[0] == push_gate.PYTEST_FULL_TESTS_CMD
    assert commands[0][-2:] == ["-n", "auto"]


def test_run_gate_tests_keeps_docs_only_changes_in_auto_without_running_tests(monkeypatch) -> None:
    commands: list[list[str]] = []

    monkeypatch.setattr(push_gate, "_repo_root", lambda: Path("/tmp/repo"))
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "changed_files",
        lambda upstream=None: {
            "files": ["docs/plans/add-feature/sample.md"],
            "source_status": "available_nonempty",
        },
    )
    monkeypatch.setattr(
        push_gate.changed_files_module,
        "select_test_targets",
        lambda files, repo_root=None: {
            "pytest_targets": [],
            "bats_targets": [],
            "has_code_changes": False,
            "unmapped_code_files": [],
        },
    )
    monkeypatch.setattr(
        push_gate,
        "_has_deleted_or_renamed_tests",
        lambda project_root, upstream: False,
    )

    def _fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        commands.append(command)
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(push_gate, "_run_command", _fake_run)

    result = push_gate.run_gate_tests(remote="origin", branch="dogfood", test_tier="auto")

    assert result == {
        "id": "G-tests",
        "passed": True,
        "detail": "tier=auto, pytest 0 + bats 0",
        "fix": "なし",
    }
    assert commands == []


def test_gate_ids_match_contract_enum() -> None:
    contract_path = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "v2"
        / "L3-detailed-design"
        / "D-CONTRACT"
        / "D-CONTRACT-draft.md"
    )

    assert push_gate._contract_gate_ids(contract_path) == list(push_gate.GATE_IDS)


def test_run_gate_vg_overview_skips_when_assets_are_absent(tmp_path: Path) -> None:
    result = push_gate.run_gate_vg_overview(tmp_path)

    assert result["passed"] is True
    assert result["id"] == "G-vg-overview"
    assert "not applicable" in result["detail"]


def test_run_gate_vg_overview_passes_when_overall_clean(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "docs" / "v2" / "L7-test-design").mkdir(parents=True)
    (tmp_path / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml").write_text(
        "anchors: {}\n",
        encoding="utf-8",
    )
    (tmp_path / "cli" / "config").mkdir(parents=True)
    (tmp_path / "cli" / "config" / "functional-registry.yaml").write_text("entries: []\n", encoding="utf-8")
    monkeypatch.setattr(
        push_gate,
        "collect_vg_overview",
        lambda root: {
            "vg_overview": {"overall_clean": True},
            "g7_subcheck": {
                "ut_total": 88,
                "anchored": 88,
                "exec_pass": 88,
                "missing": 0,
                "unanchored_but_exists": 0,
            },
        },
    )

    result = push_gate.run_gate_vg_overview(tmp_path)

    assert result["passed"] is True
    assert "overall_clean=true" in result["detail"]
    assert "anchored=88/88" in result["detail"]


def test_run_gate_vg_overview_fails_when_applicable_pair_is_dirty(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "docs" / "v2" / "L7-test-design").mkdir(parents=True)
    (tmp_path / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml").write_text(
        "anchors: {}\n",
        encoding="utf-8",
    )
    (tmp_path / "cli" / "config").mkdir(parents=True)
    (tmp_path / "cli" / "config" / "functional-registry.yaml").write_text("entries: []\n", encoding="utf-8")
    monkeypatch.setattr(
        push_gate,
        "collect_vg_overview",
        lambda root: {
            "vg_overview": {
                "overall_clean": False,
                "required_clean": {
                    "registry_design_coverage": {"clean": True, "finding_count": 0},
                },
                "pair_status": {
                    "L6-L7": {
                        "status": "applicable",
                        "clean": False,
                        "reason": "missing=1",
                    },
                    "L5-L8": {
                        "status": "approved_deferred",
                        "clean": False,
                        "reason": "execution_gate_not_implemented",
                    },
                },
            },
            "g7_subcheck": {},
        },
    )

    result = push_gate.run_gate_vg_overview(tmp_path)

    assert result["passed"] is False
    assert "L6-L7:missing=1" in result["detail"]
    assert "L5-L8" not in result["detail"]


def test_run_gate_vg_overview_fails_when_requirement_drift_is_dirty(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "docs" / "v2" / "L7-test-design").mkdir(parents=True)
    (tmp_path / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml").write_text(
        "anchors: {}\n",
        encoding="utf-8",
    )
    (tmp_path / "cli" / "config").mkdir(parents=True)
    (tmp_path / "cli" / "config" / "functional-registry.yaml").write_text("entries: []\n", encoding="utf-8")
    monkeypatch.setattr(
        push_gate,
        "collect_vg_overview",
        lambda root: {
            "vg_overview": {
                "overall_clean": False,
                "required_clean": {
                    "registry_design_coverage": {"clean": True, "finding_count": 0},
                    "requirement_drift": {
                        "clean": False,
                        "finding_count": 2,
                        "focus": "L6",
                    },
                },
                "pair_status": {
                    "L6-L7": {
                        "status": "applicable",
                        "clean": True,
                        "reason": "missing=0",
                    },
                },
            },
            "g7_subcheck": {},
        },
    )

    result = push_gate.run_gate_vg_overview(tmp_path)

    assert result["passed"] is False
    assert "requirement_drift:2" in result["detail"]
