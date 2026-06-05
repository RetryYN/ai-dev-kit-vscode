from __future__ import annotations

from pathlib import Path
import sys


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import push_gate


def _write_plan(
    root: Path,
    plan_id: str,
    *,
    status: str = "completed",
    tl_review: str | None = "approve",
    subdir: str = "add-feature",
    plan_scope: str | None = None,
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
        f"status: {status}",
    ]
    if plan_scope is not None:
        lines.append(f"plan_scope: {plan_scope}")
    if tl_review is not None:
        lines.append(f"tl_review: {tl_review}")
    lines.extend(["---", "", "# body", ""])
    plan_path.write_text("\n".join(lines), encoding="utf-8")
    return plan_path


def _stub_ahead(monkeypatch, plan_ids: list[str]) -> None:
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: plan_ids)


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


def test_run_gate_review_fails_when_plan_id_cannot_be_resolved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
    monkeypatch.setattr(push_gate, "_ahead_commit_plan_ids", lambda project_root: [])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is False
    assert "plan_id" in result["detail"]


def test_run_gate_review_fails_when_ahead_commit_has_multiple_plan_candidates(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
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
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
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
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
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
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
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
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
    _stub_ahead(monkeypatch, [representative, sibling])

    result = push_gate.run_gate_review("add-feature-2026-06-03-outside-scope", tmp_path)

    assert result["passed"] is False
    assert "explicit=add-feature-2026-06-03-outside-scope" in result["detail"]


def test_run_gate_review_uses_single_ahead_plan_for_backward_compatibility(
    tmp_path: Path, monkeypatch
) -> None:
    plan_id = "add-feature-2026-06-03-gate-driven-push"
    _write_plan(tmp_path, plan_id)
    monkeypatch.setattr(push_gate, "_load_handover_plan_id", lambda project_root: None)
    _stub_ahead(monkeypatch, [plan_id])

    result = push_gate.run_gate_review(None, tmp_path)

    assert result["passed"] is True
    assert result["detail"] == f"{plan_id} scope=action status=completed tl_review=approve"


def test_run_all_gates_accepts_plan_id_and_allow_main(monkeypatch) -> None:
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(push_gate, "run_gate_tests", lambda: push_gate._result("G-tests", True, "ok", "なし"))
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
    ]
    assert payload["plan_id"] == "add-feature-2026-06-03-gate-driven-push"
    assert payload["allow_main"] is True
    assert calls == [("add-feature-2026-06-03-gate-driven-push", Path("/tmp/repo"))]


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
