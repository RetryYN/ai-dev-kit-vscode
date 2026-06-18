#!/usr/bin/env bats

setup() {
  HELIX_ROOT="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"
  export HELIX_HOME="$HELIX_ROOT"
  export PYTHONPATH="$HELIX_ROOT${PYTHONPATH:+:$PYTHONPATH}"
}

@test "HELIX L0-L14 flow contract stays pinned by pytest" {
  run python3 -m pytest "$HELIX_ROOT/cli/lib/tests/test_helix_l0_l14_flow_contract.py" -q
  [ "$status" -eq 0 ]
  [[ "$output" == *"88 passed"* ]]
}

@test "CI workflow pins detector-gate contract" {
  run python3 - \
    "$HELIX_ROOT/.github/workflows/ci.yml" <<'PY'
from pathlib import Path
import sys
import yaml

payload = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
jobs = payload["jobs"]
assert "detector-gate" in jobs
detector_gate = jobs["detector-gate"]
assert detector_gate["permissions"] == {"contents": "read"}
steps = detector_gate["steps"]
run_scripts = "\n".join(step["run"] for step in steps if "run" in step)
assert "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json" in run_scripts
assert "helix doctor --gate --json" not in run_scripts
assert "--strict-full-flow" not in run_scripts
assert "--strict-vmodel-pair-freeze" not in run_scripts
assert "requirements-dev.txt" in run_scripts
assert "HELIX_CHANGED_FILES" in run_scripts
assert "git fetch origin ${{ github.base_ref }}" in run_scripts
assert "PATH=\"$PWD/cli:$PATH\"" in run_scripts
assert any(step.get("if") == "github.event_name == 'pull_request'" for step in steps)
checkout = next(step for step in steps if str(step.get("uses", "")).startswith("actions/checkout"))
assert checkout.get("with", {}).get("fetch-depth") == 0
push_steps = [step for step in steps if step.get("if") == "github.event_name == 'push'" and "run" in step]
assert push_steps, "detector-gate must export HELIX_CHANGED_FILES on push events (DF-FCCI-CI-RATCHET-PUSH)."
push_scripts = "\n".join(step["run"] for step in push_steps)
assert "HELIX_CHANGED_FILES" in push_scripts
assert "${{ github.event.before }}" in push_scripts
assert "${{ github.sha }}" in push_scripts
PY
  [ "$status" -eq 0 ]
}

@test "full objective gap status keeps L7 and full-flow completion unclaimed" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-full-objective-gap-status.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml" <<'PY'
import re
import re
import sys
import re
import json
from pathlib import Path
import yaml

path = Path(sys.argv[1])
objective_coverage_path = Path(sys.argv[2])
deferred_path = Path(sys.argv[3])
root = path.resolve().parents[3]
payload = yaml.safe_load(path.read_text(encoding="utf-8"))
objective_coverage = yaml.safe_load(objective_coverage_path.read_text(encoding="utf-8"))
deferred_coverage = yaml.safe_load(deferred_path.read_text(encoding="utf-8"))
reference_integrity = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml").read_text(encoding="utf-8")
)

assert payload["schema_version"] == "full_objective_gap_status_v1"
assert payload["status"] == "active_goal_l1_l6_current_scope_pass_later_phase_deferred"
assert payload["scope"] == "full_objective_status_with_current_l1_l6_boundary"
assert payload["boundary"] == {
    "l7_work_requested_by_user": False,
    "l7_work_requires_feature_ticket": True,
    "this_ledger_is_l7_work": False,
    "this_ledger_is_implementation_evidence": False,
    "l7_implementation_done": False,
    "l7_test_design_created_by_this_ledger": False,
    "helix_db_write_performed": False,
    "schema_migration_done": False,
    "external_tool_installed": False,
    "external_tool_executed": False,
    "ci_or_equivalent_connected": False,
    "full_goal_complete": False,
    "goal_complete_allowed": False,
}
assert payload["summary"] == {
    "objective_items_checked": 10,
    "current_scope_items_pass_l1_l6": 9,
    "items_requiring_later_phase_before_full_completion": 8,
    "feature_tickets_available": 11,
    "repository_add_feature_files_discovered": 24,
    "current_objective_deferred_feature_tickets": 11,
    "out_of_current_objective_add_feature_files": 13,
    "out_of_current_objective_completed_add_features": 4,
    "out_of_current_objective_parked_feature_tickets": 0,
    "right_arm_execution_gates_deferred": 4,
    "blocking_findings_current_l1_l6_scope": 0,
    "blocking_findings_full_goal": 8,
    "current_scope_verdict": "pass_l1_l6_only",
    "full_goal_verdict": "active_not_complete",
}
assert payload["summary_contract"] == {
    "objective_items_checked_source": "objective_status_count",
    "current_scope_items_pass_l1_l6_rule": "objective_status_count_minus_non_completion_status_count",
    "items_requiring_later_phase_rule": "objective_status_count_minus_empty_remaining_allowed_count_minus_non_completion_status_count",
    "blocking_findings_full_goal_rule": "same_as_items_requiring_later_phase_before_full_completion",
    "feature_tickets_available_source": "feature_ticket_boundaries_count",
    "repository_add_feature_inventory_source": "deferred_feature_coverage.repository_add_feature_inventory",
    "current_objective_deferred_feature_tickets_rule": "same_as_feature_tickets_available",
    "out_of_current_objective_add_feature_files_rule": "repository_inventory_excluded_from_current_objective_deferred_count",
    "inventory_exclusion_is_completion_evidence": False,
    "inventory_exclusion_allows_l7_work": False,
    "right_arm_execution_gates_deferred_source": "right_arm_execution_boundaries.deferred_gates_count",
    "current_l1_l6_blocking_findings_rule": "zero_when_all_objective_status_proofs_exist_and_no_forbidden_l7_proofs",
    "full_goal_verdict_rule": "active_not_complete_until_l7_db_auto_registration_feedback_loop_ci_external_tool_adoption_recheck_and_right_arm_gates_close",
    "summary_is_completion_evidence": False,
}
repository_inventory = deferred_coverage["repository_add_feature_inventory"]
excluded_inventory = repository_inventory["excluded_from_current_objective"]
excluded_by_id = {item["id"]: item for item in excluded_inventory}
assert payload["repository_add_feature_inventory_contract"] == {
    "source_audit_key": "deferred_feature_coverage",
    "source_contract": "repository_add_feature_inventory",
    "current_scope_action": "classify_all_add_feature_files_without_expanding_l7_scope",
    "all_repository_add_feature_files_checked": 24,
    "current_objective_deferred_feature_tickets_checked": 11,
    "excluded_from_current_objective_deferred_count": 13,
    "historical_completed_feature_count": 4,
    "parked_feature_ticket_outside_current_objective_count": 0,
    "exclusion_is_completion_evidence_for_current_objective": False,
    "exclusion_may_hide_current_l1_l6_design_debt": False,
    "l7_work_allowed_by_inventory": False,
}
assert payload["summary"]["repository_add_feature_files_discovered"] == (
    deferred_coverage["summary"]["repository_add_feature_files_discovered"]
)
assert payload["summary"]["current_objective_deferred_feature_tickets"] == payload[
    "summary"
]["feature_tickets_available"]
assert payload["summary"]["current_objective_deferred_feature_tickets"] == (
    repository_inventory["current_objective_deferred_feature_tickets_checked"]
)
assert payload["summary"]["out_of_current_objective_add_feature_files"] == (
    repository_inventory["excluded_from_current_objective_deferred_count"]
)
assert payload["summary"]["out_of_current_objective_add_feature_files"] == len(
    excluded_inventory
)
c3b_entry = excluded_by_id["c3b_fr_uses_reverse_derived_full_required"]
assert c3b_entry["id"] == "c3b_fr_uses_reverse_derived_full_required"
assert c3b_entry["path"] == "docs/plans/add-feature/add-feature-2026-06-18-fruses-reverse-derived-promotion.md"
assert c3b_entry["observed_status"] == "in_progress"
assert c3b_entry["classification"] == "current_scope_authorized_c3b_fr_uses_reverse_derived_full_required"
assert "C-3b" in c3b_entry["reason"]
assert "derived index" in c3b_entry["reason"]
assert "full-required" in c3b_entry["reason"]
assert "broad advisory→fail-close flip of W1 detectors" in c3b_entry["reason"]
c3c_entry = excluded_by_id["c3c_coding_rule_core_full_required"]
assert c3c_entry["id"] == "c3c_coding_rule_core_full_required"
assert c3c_entry["path"] == "docs/plans/add-feature/add-feature-2026-06-18-coding-rule-core-full-required.md"
assert c3c_entry["observed_status"] == "draft"
assert c3c_entry["classification"] == "current_scope_authorized_c3c_coding_rule_core_full_required"
assert "C-3c" in c3c_entry["reason"]
assert "bash-n/py_compile" in c3c_entry["reason"]
assert "full-scan required" in c3c_entry["reason"]
assert "ruff/shellcheck" in c3c_entry["reason"]
push_gate_entry = excluded_by_id["push_gate_test_tiering"]
assert push_gate_entry["id"] == "push_gate_test_tiering"
assert push_gate_entry["path"] == "docs/plans/add-feature/add-feature-2026-06-18-push-gate-test-tiering.md"
assert push_gate_entry["observed_status"] == "draft"
assert push_gate_entry["classification"] == "current_scope_authorized_push_gate_test_tiering"
assert "shared-core push gate hardening action" in push_gate_entry["reason"]
assert "dogfood/feature CI full backstop" in push_gate_entry["reason"]
assert "fail-close" in push_gate_entry["reason"]
assert payload["summary"]["out_of_current_objective_completed_add_features"] == sum(
    1
    for item in excluded_inventory
    if item["classification"] == "historical_completed_feature"
)
assert payload["summary"]["out_of_current_objective_parked_feature_tickets"] == sum(
    1
    for item in excluded_inventory
    if item["classification"] == "parked_feature_ticket_outside_current_objective_set"
)
assert repository_inventory["exclusion_is_completion_evidence_for_current_objective"] is False
assert repository_inventory["exclusion_may_hide_current_l1_l6_design_debt"] is False
assert repository_inventory["l7_work_allowed_by_inventory"] is False
source_audit_contract = payload["source_audit_contract"]
assert source_audit_contract == {
    "required_source_audit_keys": [
        "l0_l14_flow_surface",
        "l0_planning_derivation",
        "objective_l1_l6_coverage",
        "double_check",
        "reference_integrity",
        "deferred_feature_coverage",
        "deferred_design_obligation_proof",
        "dependency_impact_readiness",
        "bottleneck_remediation_readiness",
        "ratification_index",
        "exit_criteria",
        "workflow_automation",
        "db_registration_readiness",
        "governance_hardening",
        "codex_claude_guard_parity",
        "harness_external_tools",
        "nfr_derivation",
    ],
    "source_path_class_required": "l1_l6_audit_doc",
    "source_files_must_exist": True,
    "source_files_must_be_current_scope_audits": True,
    "source_files_must_not_be_l7_artifacts": True,
    "source_files_must_not_be_add_feature_plans": True,
    "source_audits_are_completion_evidence": False,
}
assert set(payload["source_audits"]) == set(source_audit_contract["required_source_audit_keys"])
for audit_key, audit_path in payload["source_audits"].items():
    assert audit_path.startswith("docs/v2/audit/"), audit_key
    assert not audit_path.startswith("docs/v2/L7-test-design/"), audit_key
    assert not audit_path.startswith("docs/plans/add-feature/"), audit_key
    assert (root / audit_path).exists(), audit_key
source_audit_bundle_alignment_contract = payload["source_audit_bundle_alignment_contract"]
assert source_audit_bundle_alignment_contract == {
    "reference_integrity_source_audit_key": "reference_integrity",
    "source_audit_paths_must_be_in_reference_integrity_bundle_or_self_reference_integrity": True,
    "self_reference_integrity_source_path_allowed_outside_bundle": True,
    "outside_bundle_source_audits_allowed_count": 1,
    "source_audit_paths_outside_bundle_must_equal_reference_integrity_source": True,
    "bundle_alignment_is_completion_evidence": False,
    "l7_or_add_feature_source_alignment_allowed": False,
}
source_audit_paths = set(payload["source_audits"].values())
reference_bundle_paths = set(reference_integrity["sources"]["audit_bundle"])
reference_integrity_source_path = payload["source_audits"][
    source_audit_bundle_alignment_contract["reference_integrity_source_audit_key"]
]
outside_bundle_paths = sorted(source_audit_paths - reference_bundle_paths)
assert outside_bundle_paths == [reference_integrity_source_path]
assert len(outside_bundle_paths) == source_audit_bundle_alignment_contract[
    "outside_bundle_source_audits_allowed_count"
]
for audit_path in source_audit_paths:
    assert audit_path in reference_bundle_paths or audit_path == reference_integrity_source_path
assert source_audit_bundle_alignment_contract["l7_or_add_feature_source_alignment_allowed"] is False
source_audit_usage_contract = payload["source_audit_usage_contract"]
assert source_audit_usage_contract == {
    "source_collection": "source_audits",
    "usage_surfaces": [
        "completion_audit_matrix.authoritative_evidence_keys",
        "objective_clause_mapping_contract.source_audit_key",
        "feature_boundary_contract.source_audit_key",
        "l1_l6_design_obligation_contract.source_audit_key",
        "harness_external_tool_adoption_recheck_scope_contract.source_audit_key",
        "harness_external_tool_current_session_web_fetch_recheck.source_audit_key",
        "harness_external_tool_accountability_contract.source_audit_key",
    ],
    "all_source_audit_keys_must_be_used": True,
    "unused_source_audit_keys": [],
    "source_audit_usage_is_completion_evidence": False,
    "l7_or_add_feature_source_usage_allowed": False,
}
assert payload["completion_audit_policy"] == {
    "preserve_full_objective_scope": True,
    "current_scope_is_l1_l6_only": True,
    "weak_or_indirect_evidence_counts_as_complete": False,
    "l1_l6_pass_may_not_be_rewritten_as_full_goal_complete": True,
    "later_phase_work_requires_feature_ticket": True,
    "add_feature_tickets_are_boundaries_not_proof": True,
    "source_audit_keys_must_exist": True,
}
harness_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml").read_text(encoding="utf-8")
)
harness_recheck_scope = payload["harness_external_tool_adoption_recheck_scope_contract"]
assert harness_recheck_scope == {
    "source_audit_key": "harness_external_tools",
    "source_contract": "adoption_recheck_scope_contract",
    "current_scope_action": "index_later_phase_adoption_recheck_gap_only",
    "adoption_recheck_controls_checked": 3,
    "latest_core_rechecked_sources_checked": 5,
    "all_candidate_sources_checked": 33,
    "spot_recheck_sources_checked": 8,
    "adoption_control_sources_are_subset_of_latest_core_rechecked_sources": True,
    "adoption_control_sources_are_subset_of_spot_recheck_sources": True,
    "all_candidate_source_ids_must_match_canonical_source_ids": True,
    "spot_recheck_sources_are_subset_of_canonical_source_ids": True,
    "spot_recheck_is_not_full_candidate_recheck": True,
    "all_candidates_remain_gated_by_admission_gate_contracts": True,
    "non_core_candidates_require_new_recheck_before_adoption": True,
    "required_before_full_goal_completion": [
        "approved_feature_ticket",
        "fresh_official_source_recheck",
        "auth_license_network_ci_db_ingestion_approval",
        "install_or_execution_evidence_if_selected",
        "output_ingestion_and_feedback_evidence_if_selected",
    ],
    "current_scope_is_completion_evidence": False,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
harness_scope = harness_coverage[harness_recheck_scope["source_contract"]]
assert harness_recheck_scope["source_audit_key"] in payload["source_audits"]
assert harness_recheck_scope["adoption_recheck_controls_checked"] == harness_scope[
    "adoption_recheck_controls_checked"
]
assert harness_recheck_scope["latest_core_rechecked_sources_checked"] == harness_scope[
    "latest_core_rechecked_sources_checked"
]
assert harness_recheck_scope["all_candidate_sources_checked"] == harness_scope[
    "all_candidate_sources_checked"
]
assert harness_recheck_scope["spot_recheck_sources_checked"] == harness_scope[
    "spot_recheck_sources_checked"
]
assert harness_recheck_scope["l7_artifact_allowed_now"] is False
harness_current_session_recheck = payload[
    "harness_external_tool_current_session_web_fetch_recheck"
]
assert harness_current_session_recheck == {
    "source_audit_key": "harness_external_tools",
    "source_contract": "current_session_web_fetch_recheck_2026_06_13",
    "current_scope_action": "index_l1_l6_design_basis_recheck_only",
    "official_sources_checked": 5,
    "web_fetch_confirmed": True,
    "source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
    ],
    "current_scope_is_completion_evidence": False,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "result": "no_change_to_candidate_gate_status",
}
harness_current_session_source = harness_coverage[
    harness_current_session_recheck["source_contract"]
]
assert harness_current_session_recheck["source_audit_key"] in payload["source_audits"]
assert harness_current_session_recheck["official_sources_checked"] == harness_current_session_source[
    "official_sources_checked"
]
assert set(harness_current_session_recheck["source_ids"]) == {
    item["source_id"] for item in harness_current_session_source["sources"]
}
assert harness_current_session_recheck["l7_artifact_allowed_now"] is False
harness_accountability = payload["harness_external_tool_accountability_contract"]
assert harness_accountability == {
    "source_audit_key": "harness_external_tools",
    "source_contract": "harness_tool_accountability_contract",
    "current_scope_action": "index_external_tool_research_as_design_basis_only",
    "feature_ticket_is_not_design_substitute": True,
    "web_evidence_is_design_basis_not_adoption": True,
    "all_candidates_require_admission_gate_before_install_or_execution": True,
    "mcp_plugin_install_requires_explicit_approval": True,
    "output_ingestion_requires_explicit_db_ingestion_approval": True,
    "current_scope_must_keep_install_execution_ci_db_false": True,
    "l7_work_requires_feature_ticket": True,
    "current_scope_is_completion_evidence": False,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
harness_accountability_source = harness_coverage[
    harness_accountability["source_contract"]
]
assert harness_accountability["source_audit_key"] in payload["source_audits"]
assert harness_accountability["feature_ticket_is_not_design_substitute"] == (
    harness_accountability_source["feature_ticket_is_not_design_substitute"]
)
assert harness_accountability["web_evidence_is_design_basis_not_adoption"] == (
    harness_accountability_source["web_evidence_is_design_basis_not_adoption"]
)
assert harness_accountability["current_scope_must_keep_install_execution_ci_db_false"] == (
    harness_accountability_source["current_scope_must_keep_install_execution_ci_db_false"]
)
assert harness_accountability["l7_work_requires_feature_ticket"] == (
    harness_accountability_source["l7_work_requires_feature_ticket"]
)
assert payload["l1_l6_design_obligation_contract"] == {
    "source_audit_key": "deferred_design_obligation_proof",
    "source_contract": "design_obligation_rows",
    "current_scope_action": "prove_l1_l6_design_obligation_before_deferring_l7_execution",
    "l1_l6_design_obligation_is_current_scope": True,
    "deferred_feature_tickets_are_not_design_substitute": True,
    "feature_ticket_allowed_only_for_unapproved_l7_or_escalation_bound_execution": True,
    "l1_l6_design_assets_required_before_ticket": True,
    "design_gap_reopened_if_l1_l6_evidence_missing": True,
    "no_feature_escape_for_design_debt": True,
    "l7_or_external_execution_requires_approved_feature_ticket": True,
    "covered_current_scope_surfaces": [
        "requirement_gap_detection",
        "ddd_tdd_governance_design",
        "helix_db_registration_design",
        "dependency_impact_design",
        "bottleneck_detection_design",
        "codex_claude_guard_parity_design",
    ],
}
authoritative_evidence_contract = payload["authoritative_evidence_contract"]
assert authoritative_evidence_contract == {
    "source_collection": "completion_audit_matrix",
    "evidence_key_field": "authoritative_evidence_keys",
    "evidence_keys_must_resolve_to_source_audits": True,
    "resolved_source_paths_must_exist": True,
    "resolved_source_paths_must_be_l1_l6_audit_docs": True,
    "resolved_source_paths_must_not_be_l7_artifacts": True,
    "resolved_source_paths_must_not_be_add_feature_plans": True,
    "authoritative_evidence_keys_are_completion_evidence": False,
    "l7_execution_allowed_by_authoritative_keys": False,
}
objective_clause_mapping_contract = payload["objective_clause_mapping_contract"]
assert objective_clause_mapping_contract == {
    "source_audit_key": "objective_l1_l6_coverage",
    "source_collection": "objective_clause_to_full_status_map",
    "local_collection": "objective_status",
    "source_id_field": "objective_clause_id",
    "source_target_field": "full_objective_status_ids",
    "local_id_field": "id",
    "local_status_items_without_objective_clause": [
        "REQ-FULL-GOAL-COMPLETION"
    ],
    "local_without_clause_reason": "full_goal_completion_is_a_denial_item_not_a_current_scope_objective_clause",
    "every_non_completion_local_status_must_be_mapped": True,
    "mapped_status_ids_must_exist_locally": True,
    "source_mapping_boundaries_must_not_be_l7_artifact_paths": True,
    "mapping_is_completion_evidence": False,
}
assert payload["source_audits"][objective_clause_mapping_contract["source_audit_key"]] == str(objective_coverage_path.relative_to(root))
feature_boundary_contract = payload["feature_boundary_contract"]
assert feature_boundary_contract == {
    "source_audit_key": "deferred_feature_coverage",
    "source_collection": "feature_ticket_integrity",
    "local_collection": "feature_ticket_boundaries",
    "identity_fields": ["id", "path"],
    "source_status_required": "draft",
    "source_approval_boundary_required": True,
    "source_ticket_completion_evidence_allowed": False,
    "source_current_task_scope_allowed": [
        "feature_ticket_only",
        "L4_L6_design_closed_feature_ticketed",
    ],
    "local_ticket_set_must_equal_source_ticket_set": True,
    "local_paths_must_exist": True,
    "local_paths_must_be_add_feature_plans": True,
    "l7_artifacts_allowed_as_boundary_sources": False,
    "contract_is_completion_evidence": False,
}
feature_ticket_file_contract = payload["feature_ticket_file_contract"]
assert feature_ticket_file_contract == {
    "frontmatter_required": True,
    "workflow_required": "add-feature",
    "status_required": "draft",
    "current_task_scope_allowed": [
        "feature_ticket_only",
        "L4_L6_design_closed_feature_ticketed",
    ],
    "approval_boundary_text_required": True,
    "approval_boundary_must_contain": ["approv"],
    "approval_gate_fields_any_required": [
        "approval_required_before_l7_work",
        "approval_required_before_implementation",
        "approval_required_before_install",
        "approval_required_before_contract_edit",
    ],
    "ticket_must_not_claim_completion": True,
    "ticket_is_completion_evidence": False,
    "current_scope_may_parse_ticket_metadata_only": True,
}
remaining_mapping_contract = payload["remaining_feature_ticket_mapping_contract"]
assert remaining_mapping_contract == {
    "source_collection": "objective_status",
    "audit_collection": "completion_audit_matrix",
    "feature_collection": "feature_ticket_boundaries",
    "remaining_add_feature_paths_must_map_to_feature_ticket_ids": True,
    "feature_ticket_ids_must_map_to_existing_ticket_paths": True,
    "every_feature_ticket_boundary_must_be_referenced_by_completion_audit": True,
    "unused_feature_ticket_boundary_ids": [],
    "text_only_remaining_items_allowed_when_not_add_feature_paths": True,
    "mapping_is_completion_evidence": False,
    "l7_execution_allowed_by_mapping": False,
}
feature_unlock_contract = payload["feature_ticket_unlock_contract"]
assert feature_unlock_contract["feature_collection"] == "feature_ticket_boundaries"
assert feature_unlock_contract["audit_collection"] == "completion_audit_matrix"
assert feature_unlock_contract["unlock_field"] == "unlocks"
assert feature_unlock_contract["routed_from_field"] == "feature_ticket_ids"
assert feature_unlock_contract["remaining_class_field"] == "remaining_class"
assert feature_unlock_contract["every_feature_ticket_must_have_unlock_target"] is True
assert feature_unlock_contract["unlock_targets_must_match_completion_audit_routes"] is True
assert feature_unlock_contract["unlock_targets_must_cover_routed_remaining_classes"] is True
assert feature_unlock_contract["unlock_targets_are_completion_evidence"] is False
assert feature_unlock_contract["l7_execution_allowed_by_unlock_targets"] is False
completion_unlock_contract = payload["full_goal_completion_unlock_evidence_contract"]
assert completion_unlock_contract["feature_ticket_resolution_contract"] == {
    "feature_boundary_collection": "feature_ticket_boundaries",
    "source_feature_collection": "deferred_feature_coverage.feature_ticket_integrity",
    "required_feature_ticket_field": "required_feature_ticket",
    "required_feature_ticket_ids_must_exist": True,
    "required_feature_ticket_status_field": "status",
    "required_feature_ticket_status": "draft",
    "feature_tickets_are_routes_not_evidence": True,
    "l7_execution_allowed_by_resolution": False,
    "unresolved_required_feature_tickets": [],
}
assert payload["contract_design_escalation_boundary"] == {
    "source_boundary_map": "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml",
    "current_scope_status": "l5_l6_design_debt_identified_contract_edit_approval_required",
    "ticket_id": "contract_design_phase_label_retrofit",
    "ticket_kind": "add-design",
    "ticket_layer": "L5-L6",
    "not_feature_escape": True,
    "reason": payload["contract_design_escalation_boundary"]["reason"],
    "design_debt_accountability": {
        "design_debt_is_current_l1_l6_scope": True,
        "feature_ticket_is_not_design_substitute": True,
        "approval_blocker_is_contract_surface_risk_not_l7_boundary": True,
        "current_scope_has_recorded_gap_and_reopen_rule": True,
        "contract_edit_requires_explicit_approval_before_change": True,
    },
    "escalation_required_for": ["D-API", "D-DB", "D-CONTRACT"],
    "current_scope_action": "record_boundary_only_no_contract_edit",
    "approval_required_before_contract_edit": True,
    "contract_edit_performed": False,
    "schema_migration_done": False,
    "l7_work_performed": False,
    "ticket_is_completion_evidence": False,
    "full_goal_completion_effect": "active_not_complete",
}
assert "contract semantics" in payload["contract_design_escalation_boundary"]["reason"]
assert payload["contract_design_escalation_boundary"]["design_debt_accountability"]["feature_ticket_is_not_design_substitute"] is True
handover_boundary_contract = payload["handover_boundary_contract"]
assert handover_boundary_contract == {
    "handover_current_markdown": ".helix/handover/CURRENT.md",
    "handover_current_json": ".helix/handover/CURRENT.json",
    "next_action_heading_required": "## Next Action (Codex 向け)",
    "required_current_user_boundary_contains": [
        "add-feature-2026-06-18-coding-rule-core-full-required.md",
        "PLAN",
        "Codex se",
        "TDD 実装",
    ],
    "latest_user_boundary_must_match_handover_next_action": True,
    "latest_user_boundary_forbidden_items_must_be_reflected_in_handover": False,
    "latest_user_boundary_forbidden_handover_terms": [],
    "latest_user_boundary_l7_route_must_be_reflected_in_handover": True,
    "latest_user_boundary_allowed_work_must_be_reflected_in_handover": True,
    "handover_task_title_may_be_legacy": True,
    "handover_pending_entries_may_be_legacy": True,
    "handover_next_action_supersedes_legacy_task_title": True,
    "handover_next_action_supersedes_legacy_pending_entries": True,
    "legacy_task_title_must_not_authorize_l7": True,
    "legacy_pending_entries_must_not_authorize_l7": True,
    "legacy_handover_suppression_terms": [],
    "handover_is_completion_evidence": False,
    "l7_work_allowed_from_handover": False,
}
handover_text = (root / handover_boundary_contract["handover_current_markdown"]).read_text(encoding="utf-8")
assert handover_boundary_contract["next_action_heading_required"] in handover_text
next_action_text = handover_text.split(
    handover_boundary_contract["next_action_heading_required"], 1
)[1].split("\n## ", 1)[0]
for token in handover_boundary_contract["required_current_user_boundary_contains"]:
    assert token in next_action_text
latest_boundary = payload["latest_user_boundary"]
if handover_boundary_contract["latest_user_boundary_forbidden_items_must_be_reflected_in_handover"]:
    assert len(
        handover_boundary_contract["latest_user_boundary_forbidden_handover_terms"]
    ) == len(latest_boundary["forbidden_now"])
    for forbidden_term in handover_boundary_contract["latest_user_boundary_forbidden_handover_terms"]:
        assert forbidden_term in next_action_text, forbidden_term
for suppression_term in handover_boundary_contract["legacy_handover_suppression_terms"]:
    assert suppression_term in next_action_text, suppression_term
handover_state = json.loads(
    (root / handover_boundary_contract["handover_current_json"]).read_text(encoding="utf-8")
)
assert "coding_rule_lint core(bash-n/py_compile)" in handover_state["task"]["title"]
assert any(path == "cli/lib/coding_rule_lint.py" for path in handover_state["files"]["pending"])
assert handover_boundary_contract["handover_task_title_may_be_legacy"] is True
assert handover_boundary_contract["handover_pending_entries_may_be_legacy"] is True
assert handover_boundary_contract["legacy_task_title_must_not_authorize_l7"] is True
assert handover_boundary_contract["legacy_pending_entries_must_not_authorize_l7"] is True
assert handover_boundary_contract["handover_next_action_supersedes_legacy_pending_entries"] is True
assert "add-feature" in next_action_text
assert latest_boundary["l7_route"] == "add_feature_ticket_only"
assert handover_boundary_contract["latest_user_boundary_must_match_handover_next_action"] is True
assert handover_boundary_contract["latest_user_boundary_forbidden_items_must_be_reflected_in_handover"] is False
assert handover_boundary_contract["latest_user_boundary_l7_route_must_be_reflected_in_handover"] is True
assert handover_boundary_contract["latest_user_boundary_allowed_work_must_be_reflected_in_handover"] is True
assert handover_boundary_contract["l7_work_allowed_from_handover"] is False
source_audit_key = feature_boundary_contract["source_audit_key"]
assert payload["source_audits"][source_audit_key] == str(deferred_path.relative_to(root))
status_contract = payload["objective_status_contract"]
assert status_contract["required_fields"] == [
    "id",
    "requested",
    "l1_l6_status",
    "proof",
    "remaining_for_full_goal",
]
assert status_contract["proof_policy"] == {
    "proof_must_be_non_empty": True,
    "local_file_proofs_must_exist": True,
    "command_proofs_allowed": True,
    "l7_test_design_proof_allowed": False,
    "later_phase_artifact_proof_allowed_for_current_scope": False,
    "add_feature_plan_proof_allowed_for_current_scope": False,
    "add_feature_plan_allowed_as_remaining_boundary": True,
}
assert status_contract["command_proof_policy"] == {
    "allowed_commands": ["helix doctor check_requirement_drift --json"],
    "command_proofs_must_be_read_only": True,
    "command_proofs_must_not_execute_l7_db_ci_external": True,
    "command_proofs_are_completion_evidence": False,
    "forbidden_command_fragments": [
        "docs/v2/L7-test-design",
        "docs/plans/add-feature",
        "helix handover update",
        "helix codex",
        "helix harness",
        "helix db",
        "npm",
        "pytest",
        "bats",
        "coverage",
        "ci",
    ],
}
assert status_contract["current_scope_boundary"] == {
    "l7_work_requested_by_user": False,
    "l7_work_requires_feature_ticket": True,
    "helix_db_write_performed": False,
    "external_tool_installed": False,
    "full_goal_complete": False,
}
assert len(payload["objective_status"]) == 10
status_by_id = {item["id"]: item for item in payload["objective_status"]}
completion_audit = {item["id"]: item for item in payload["completion_audit_matrix"]}
assert set(completion_audit) == set(status_by_id)
assert completion_audit["REQ-ASSET-REQ-GAP-L6"]["full_goal_blocker"] is False
assert completion_audit["REQ-FULL-GOAL-COMPLETION"]["current_l1_l6_verdict"] == "denied_not_current_scope"
assert sum(1 for item in completion_audit.values() if item["full_goal_blocker"]) == (
    payload["summary"]["blocking_findings_full_goal"]
)
for item_id, item in completion_audit.items():
    assert item["current_l1_l6_verdict"], item_id
    assert item["proof_strength"], item_id
    assert item["remaining_class"], item_id
    assert item["authoritative_evidence_keys"], item_id
    assert set(item["authoritative_evidence_keys"]).issubset(set(payload["source_audits"])), item_id
    for evidence_key in item["authoritative_evidence_keys"]:
        resolved_path = payload["source_audits"][evidence_key]
        assert resolved_path.startswith("docs/v2/audit/"), (item_id, evidence_key)
        assert not resolved_path.startswith("docs/v2/L7-test-design/"), (item_id, evidence_key)
        assert not resolved_path.startswith("docs/plans/add-feature/"), (item_id, evidence_key)
        assert (root / resolved_path).exists(), (item_id, evidence_key)
used_source_audit_keys = set()
for item in completion_audit.values():
    used_source_audit_keys.update(item["authoritative_evidence_keys"])
used_source_audit_keys.add(objective_clause_mapping_contract["source_audit_key"])
used_source_audit_keys.add(feature_boundary_contract["source_audit_key"])
used_source_audit_keys.add(
    payload["l1_l6_design_obligation_contract"]["source_audit_key"]
)
used_source_audit_keys.add(
    payload["harness_external_tool_adoption_recheck_scope_contract"][
        "source_audit_key"
    ]
)
unused_source_audit_keys = sorted(set(payload["source_audits"]) - used_source_audit_keys)
assert unused_source_audit_keys == source_audit_usage_contract["unused_source_audit_keys"]
assert used_source_audit_keys == set(payload["source_audits"])
assert source_audit_usage_contract["all_source_audit_keys_must_be_used"] is True
assert source_audit_usage_contract["l7_or_add_feature_source_usage_allowed"] is False
assert authoritative_evidence_contract["l7_execution_allowed_by_authoritative_keys"] is False
assert "codex_claude_guard_parity" in completion_audit[
    "REQ-CODEX-CLAUDE-PARITY"
]["authoritative_evidence_keys"]
assert payload["source_audits"]["codex_claude_guard_parity"] == (
    "docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml"
)
mapped_status_ids = set()
for mapping in objective_coverage[objective_clause_mapping_contract["source_collection"]]:
    assert mapping[objective_clause_mapping_contract["source_id_field"]]
    assert mapping["current_scope_boundary"], mapping
    assert not str(mapping["current_scope_boundary"]).startswith("docs/v2/L7-test-design/")
    for full_status_id in mapping[objective_clause_mapping_contract["source_target_field"]]:
        assert full_status_id in status_by_id, full_status_id
        mapped_status_ids.add(full_status_id)
unmapped_local_status_ids = set(status_by_id) - mapped_status_ids
assert unmapped_local_status_ids == set(
    objective_clause_mapping_contract["local_status_items_without_objective_clause"]
)
allowed_empty_remaining = set(status_contract["remaining_policy"]["empty_remaining_allowed_only_for"])
allowed_statuses = (
    set(status_contract["l1_l6_pass_statuses"])
    | set(status_contract["non_completion_statuses"])
)
non_completion_count = 0
command_proofs = []
for item_id, item in status_by_id.items():
    for field in status_contract["required_fields"]:
        assert field in item, item_id
    assert item["l1_l6_status"] in allowed_statuses, item_id
    assert item["l1_l6_status"] not in status_contract["completion_claim_statuses_forbidden"], item_id
    if item["l1_l6_status"] in status_contract["non_completion_statuses"]:
        non_completion_count += 1
    assert item["proof"], item_id
    for proof in item["proof"]:
        assert not proof.startswith("docs/v2/L7-test-design/"), item_id
        assert not proof.startswith("docs/plans/add-feature/"), item_id
        if "/" in proof and not proof.startswith("helix doctor "):
            assert (root / proof).exists(), proof
        if "/" not in proof:
            command_proofs.append(proof)
    if not item["remaining_for_full_goal"]:
        assert item_id in allowed_empty_remaining
    if any(
        token in item["l1_l6_status"]
        for token in status_contract["remaining_policy"]["later_phase_remaining_required_when_status_contains"]
    ):
        assert item["remaining_for_full_goal"], item_id
empty_remaining_allowed_count = len(allowed_empty_remaining)
assert payload["summary"]["objective_items_checked"] == len(status_by_id)
assert payload["summary"]["current_scope_items_pass_l1_l6"] == (
    len(status_by_id) - non_completion_count
)
assert payload["summary"]["items_requiring_later_phase_before_full_completion"] == (
    len(status_by_id) - empty_remaining_allowed_count - non_completion_count
)
assert payload["summary"]["blocking_findings_full_goal"] == payload["summary"][
    "items_requiring_later_phase_before_full_completion"
]
assert payload["summary"]["blocking_findings_current_l1_l6_scope"] == 0
command_proof_policy = status_contract["command_proof_policy"]
assert sorted(command_proofs) == command_proof_policy["allowed_commands"]
for command in command_proofs:
    assert command.startswith("helix doctor "), command
    assert all(
        fragment not in command
        for fragment in command_proof_policy["forbidden_command_fragments"]
    ), command
assert command_proof_policy["command_proofs_must_be_read_only"] is True
assert command_proof_policy["command_proofs_must_not_execute_l7_db_ci_external"] is True
assert command_proof_policy["command_proofs_are_completion_evidence"] is False
assert len(payload["feature_ticket_boundaries"]) == 11
feature_tickets = {item["id"]: item for item in payload["feature_ticket_boundaries"]}
source_feature_tickets = {
    item["id"]: item
    for item in deferred_coverage[feature_boundary_contract["source_collection"]]
}
assert set(feature_tickets) == set(source_feature_tickets)
assert payload["contract_design_escalation_boundary"]["ticket_id"] in feature_tickets
used_feature_ticket_ids = {
    feature_id
    for item in completion_audit.values()
    for feature_id in item.get("feature_ticket_ids", [])
}
unused_feature_ticket_ids = sorted(set(feature_tickets) - used_feature_ticket_ids)
assert unused_feature_ticket_ids == remaining_mapping_contract[
    "unused_feature_ticket_boundary_ids"
]
assert (
    remaining_mapping_contract[
        "every_feature_ticket_boundary_must_be_referenced_by_completion_audit"
    ]
    is True
)
assert set(feature_unlock_contract["targets"]) == set(feature_tickets)
for feature_id, target in feature_unlock_contract["targets"].items():
    routed_from = [
        item_id
        for item_id, item in completion_audit.items()
        if feature_id in item.get("feature_ticket_ids", [])
    ]
    assert routed_from == target["routed_from_completion_audit_ids"], feature_id
    routed_remaining_classes = [
        completion_audit[item_id][feature_unlock_contract["remaining_class_field"]]
        for item_id in routed_from
    ]
    assert routed_remaining_classes == target["routed_remaining_classes"], feature_id
    unlock_text = feature_tickets[feature_id][feature_unlock_contract["unlock_field"]]
    assert not unlock_text.startswith("docs/"), feature_id
    for token in target["required_unlock_tokens"]:
        assert token in unlock_text, (feature_id, token, unlock_text)
completion_unlock_contract = payload["full_goal_completion_unlock_evidence_contract"]
assert completion_unlock_contract["current_scope_action"] == "define_unlock_evidence_only"
assert completion_unlock_contract["evidence_namespace"] == (
    "full_goal_unlock_required_evidence_not_current_scope_proof"
)
assert completion_unlock_contract["full_goal_completion_claim_allowed_now"] is False
assert completion_unlock_contract[
    "l1_l6_current_scope_pass_is_sufficient_for_full_goal"
] is False
assert completion_unlock_contract["required_evidence_is_current_scope_proof"] is False
assert completion_unlock_contract["required_evidence_is_completion_evidence_now"] is False
assert completion_unlock_contract["feature_tickets_are_required_routes_not_evidence"] is True
assert completion_unlock_contract["required_feature_ticket_is_completion_evidence"] is False
assert completion_unlock_contract[
    "may_satisfy_completion_only_after_approval_and_execution"
] is True
unlock_evidence = {
    item["id"]: item for item in completion_unlock_contract["required_evidence"]
}
assert completion_unlock_contract["required_evidence_count"] == len(unlock_evidence)
assert set(unlock_evidence) == {
    "L7-UNIT-CLOSURE",
    "RIGHT-ARM-EXECUTION-GATES",
    "HELIX-DB-WRITE-ADOPTION",
    "RECURRENCE-CLOSURE",
    "EXTERNAL-TOOL-ADOPTION",
    "RUNTIME-GUARD-PARITY",
    "DEPENDENCY-IMPACT-QUERY",
    "BOTTLENECK-ROUTING",
}
for evidence_id, evidence in unlock_evidence.items():
    feature_id = evidence["required_feature_ticket"]
    assert feature_id in feature_tickets, evidence_id
    target_tokens = set(
        feature_unlock_contract["targets"][feature_id]["required_unlock_tokens"]
    )
    assert set(evidence["required_unlock_tokens"]) <= target_tokens, evidence_id
    assert evidence["current_status"] == "deferred", evidence_id
assert unlock_evidence["RIGHT-ARM-EXECUTION-GATES"]["required_gates"] == [
    "G8",
    "G9",
    "G12",
    "G14",
]
if remaining_mapping_contract["remaining_add_feature_paths_must_map_to_feature_ticket_ids"]:
    for item_id, item in status_by_id.items():
        remaining_add_feature_paths = {
            remaining
            for remaining in item["remaining_for_full_goal"]
            if str(remaining).startswith("docs/plans/add-feature/")
        }
        routed_ticket_paths = {
            feature_tickets[feature_id]["path"]
            for feature_id in completion_audit[item_id].get("feature_ticket_ids", [])
        }
        assert remaining_add_feature_paths.issubset(routed_ticket_paths), item_id
assert remaining_mapping_contract["l7_execution_allowed_by_mapping"] is False
for item in feature_tickets.values():
    assert (root / item["path"]).exists(), item["path"]
    assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
    assert not item["path"].startswith("docs/v2/L7-test-design/"), item["id"]
    ticket_text = (root / item["path"]).read_text(encoding="utf-8")
    assert ticket_text.startswith("---\n"), item["id"]
    ticket_meta = yaml.safe_load(ticket_text.split("---", 2)[1])
    assert ticket_meta["workflow"] == feature_ticket_file_contract["workflow_required"], item["id"]
    assert ticket_meta["status"] == feature_ticket_file_contract["status_required"], item["id"]
    assert ticket_meta["current_task_scope"] in feature_ticket_file_contract["current_task_scope_allowed"], item["id"]
    approval_boundary = ticket_meta.get("approval_boundary", "")
    assert approval_boundary, item["id"]
    for token in feature_ticket_file_contract["approval_boundary_must_contain"]:
        assert token in approval_boundary.lower(), item["id"]
    assert any(
        ticket_meta.get(field) is True
        for field in feature_ticket_file_contract["approval_gate_fields_any_required"]
    ), item["id"]
    assert "complete" not in str(ticket_meta["status"]).lower(), item["id"]
    source_item = source_feature_tickets[item["id"]]
    assert item["path"] == source_item["path"], item["id"]
    assert source_item["status"] == feature_boundary_contract["source_status_required"], item["id"]
    assert source_item["approval_boundary_required"] is feature_boundary_contract["source_approval_boundary_required"], item["id"]
    assert source_item["ticket_is_completion_evidence"] is feature_boundary_contract["source_ticket_completion_evidence_allowed"], item["id"]
    assert source_item["current_task_scope"] in feature_boundary_contract["source_current_task_scope_allowed"], item["id"]
    if source_item.get("layer") == "L7":
        assert source_item.get("approval_required_before_l7_work") is True, item["id"]
right_arm = payload["right_arm_execution_boundaries"]
assert right_arm["strict_full_flow_current_overall_clean"] is False
assert right_arm["strict_full_flow_command"] == (
    "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview "
    "--strict-full-flow --json"
)
assert right_arm["strict_full_flow_command_is_read_only"] is True
assert right_arm["deferred_gate_contract"] == {
    "deferred_gate_ids_must_equal": ["G8", "G9", "G12", "G14"],
    "deferred_gate_count": 4,
    "status_required": "approved_deferred",
    "clean_required": True,
    "reason_must_contain": ["execution_gate_not_implemented"],
    "next_action_must_start_with": "implement",
    "reference_required": "HELIX-workflows/helix-process/automation-gate-map.md",
    "gate_details_are_completion_evidence": False,
    "l7_or_right_arm_execution_allowed_by_contract": False,
}
deferred_gates = {item["gate_id"]: item for item in right_arm["deferred_gates"]}
assert list(deferred_gates) == right_arm["deferred_gate_contract"]["deferred_gate_ids_must_equal"]
assert len(deferred_gates) == right_arm["deferred_gate_contract"]["deferred_gate_count"]
assert deferred_gates["G8"]["pair"] == "L5-L8"
assert deferred_gates["G9"]["pair"] == "L4-L9"
assert deferred_gates["G12"]["pair"] == "L3-L12"
assert deferred_gates["G14"]["pair"] == "L1-L14"
for gate_id, gate in deferred_gates.items():
    assert gate["status"] == right_arm["deferred_gate_contract"]["status_required"], gate_id
    assert gate["clean"] is right_arm["deferred_gate_contract"]["clean_required"], gate_id
    assert gate["reason"].startswith("execution_gate_not_implemented"), gate_id
    assert gate["next_action"].startswith("implement"), gate_id
    assert gate["reference"] == right_arm["deferred_gate_contract"]["reference_required"], gate_id
    assert gate["source_layer"].startswith("L"), gate_id
    assert gate["target_layer"].startswith("L"), gate_id
for ref in payload["source_audits"].values():
    assert (root / ref).exists(), ref
assert payload["completion_denial"]["reason"].startswith(
    "L1-L6 current-scope evidence is pass"
)
PY
  [ "$status" -eq 0 ]
}

@test "bottleneck remediation readiness stays L1-L6 design evidence only" {
  run python3 - "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml" <<'PY'
import re
import sys
import datetime
from pathlib import Path
from urllib.parse import urlparse
import yaml

path = Path(sys.argv[1])
root = path.resolve().parents[3]
payload = yaml.safe_load(path.read_text(encoding="utf-8"))
with open(root / "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml", encoding="utf-8") as handle:
    pair_balance = yaml.safe_load(handle)

assert payload["schema_version"] == "l1_l6_bottleneck_remediation_readiness_v1"
assert payload["status"] == "current_scope_l1_l6_bottleneck_remediation_readiness_mapped"
assert payload["boundary"]["l7_work_requested_by_user"] is False
assert payload["boundary"]["l7_work_requires_feature_ticket"] is True
assert payload["boundary"]["bottleneck_detector_implemented_by_this_audit"] is False
assert payload["boundary"]["remediation_auto_apply_done"] is False
assert payload["boundary"]["helix_db_write_performed"] is False
assert payload["boundary"]["external_tool_executed"] is False
assert payload["boundary"]["goal_complete_allowed"] is False
assert payload["summary"]["bottleneck_signal_sources_checked"] == 7
assert payload["summary"]["l6_function_specs_checked"] == 5
assert payload["summary"]["remediation_flow_states_defined"] == 7
assert payload["summary"]["forbidden_current_scope_states_checked"] == 2
assert payload["summary"]["required_signal_fields_checked"] == 8
assert payload["summary"]["cross_axis_aggregation_contracts_checked"] == 4
assert payload["summary"]["signal_route_contracts_checked"] == 7
assert payload["summary"]["required_output_sections"] == 8
assert payload["summary"]["deferred_feature_boundaries_checked"] == 4
assert len(payload["bottleneck_signal_sources"]) == 7
assert len(payload["l6_design_coverage"]) == 5
assert len(payload["deferred_feature_boundaries"]) == 4
assert payload["summary"]["bottleneck_signal_sources_checked"] == len(
    payload["bottleneck_signal_sources"]
)
assert payload["summary"]["l6_function_specs_checked"] == len(
    payload["sources"]["l6_function_specs"]
)
assert payload["summary"]["remediation_flow_states_defined"] == len(
    payload["remediation_flow"]["states"]
)
assert payload["summary"]["forbidden_current_scope_states_checked"] == len(
    payload["remediation_flow"]["forbidden_current_scope_states"]
)
assert payload["summary"]["current_code_surfaces_checked_read_only"] == len(
    payload["sources"]["current_code_surfaces_read_only"]
)
assert payload["summary"]["deferred_feature_entry_points_checked"] == len(
    payload["deferred_feature_boundaries"]
)
assert payload["summary"]["deferred_feature_boundaries_checked"] == len(
    payload["deferred_feature_boundaries"]
)
assert payload["summary"]["required_output_sections"] == len(
    payload["required_output_contract"]
)
assert all(value == "required" for value in payload["required_output_contract"].values())
signals = {item["id"]: item for item in payload["bottleneck_signal_sources"]}
route_values = {item["candidate_route"] for item in signals.values()}
assert any(route.endswith("_feature_ticket") for route in route_values)
assert "route_bottleneck_candidate" in route_values
assert all(
    item["current_scope_status"]
    not in {"approved_implementation_executed", "recurrence_closed"}
    for item in signals.values()
)
classification_policy = payload["signal_classification_policy"]
assert classification_policy["current_scope_action"] == "classify_and_route_design_only"
assert classification_policy["detector_execution_added_now"] is False
assert classification_policy["auto_apply_allowed_now"] is False
assert classification_policy["db_write_allowed_now"] is False
assert classification_policy["recurrence_closure_allowed_now"] is False
assert classification_policy["required_signal_fields"] == list(
    payload["required_output_contract"]
)
assert payload["summary"]["required_signal_fields_checked"] == len(
    classification_policy["required_signal_fields"]
)
assert classification_policy["allowed_categories"] == [
    "requirement_trace",
    "pair_balance",
    "deferred_execution_gate",
    "feedback_lifecycle",
    "dependency_impact",
    "external_tool_admission",
    "plan_registry",
]
assert classification_policy["allowed_impact_scope"] == [
    "local",
    "broad",
    "unknown",
    "full_flow_deferred",
]
assert classification_policy["owner_roles"] == ["TL", "QA", "DevOps", "Security"]
assert "cannot become remediation closure" in classification_policy["closure_policy"]
cross_policy = payload["cross_axis_aggregation_policy"]
assert cross_policy == {
    "current_scope_action": "define_cross_detection_contract_only",
    "cross_detector_implemented_now": False,
    "route_auto_execute_allowed_now": False,
    "db_write_allowed_now": False,
    "required_fields": [
        "aggregate_id",
        "input_axes",
        "input_signal_ids",
        "aggregate_signal",
        "routed_mode",
        "priority_floor",
        "next_plan_or_feature_ticket",
        "completion_boundary",
    ],
    "allowed_axes": ["axis-07", "axis-10", "axis-11", "axis-12"],
    "allowed_aggregate_signals": [
        "drift_degradation",
        "doc_connection_gap",
        "regression_dependency",
        "runaway_feedback_loop",
    ],
    "allowed_modes": ["Reverse", "Recovery", "Incident"],
    "allowed_priority_floor": ["P0", "P1", "P2"],
}
aggregate_contracts = {
    item["aggregate_id"]: item
    for item in payload["cross_axis_aggregation_contracts"]
}
assert payload["summary"]["cross_axis_aggregation_contracts_checked"] == len(
    aggregate_contracts
)
assert set(item["aggregate_signal"] for item in aggregate_contracts.values()) == set(
    cross_policy["allowed_aggregate_signals"]
)
assert aggregate_contracts["BTL-AGG-REGRESSION-DEPENDENCY"]["priority_floor"] == "P0"
assert aggregate_contracts["BTL-AGG-DOC-CONNECTION"]["aggregate_signal"] == "doc_connection_gap"
for aggregate in aggregate_contracts.values():
    for field in cross_policy["required_fields"]:
        assert field in aggregate, aggregate["aggregate_id"]
    assert set(aggregate["input_axes"]).issubset(set(cross_policy["allowed_axes"]))
    assert set(aggregate["input_signal_ids"]).issubset(set(signals))
    assert aggregate["aggregate_signal"] in cross_policy["allowed_aggregate_signals"]
    assert aggregate["routed_mode"] in cross_policy["allowed_modes"]
    assert aggregate["priority_floor"] in cross_policy["allowed_priority_floor"]
    assert aggregate["completion_boundary"] == "aggregate_signal_is_not_remediation_closure"
    if aggregate["next_plan_or_feature_ticket"].startswith("docs/plans/add-feature/"):
        assert (root / aggregate["next_plan_or_feature_ticket"]).exists()
signal_routes = {
    item["signal_id"]: item for item in payload["signal_route_contract"]
}
assert payload["summary"]["signal_route_contracts_checked"] == len(signal_routes)
assert set(signal_routes) == set(signals)
assert signal_routes["BTL-SIG-FULL-FLOW-DEFERRED"][
    "next_plan_or_feature_ticket"
] == "docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md"
assert signal_routes["BTL-SIG-HARNESS-TOOLS"]["candidate_owner"] == "Security"
for route in signal_routes.values():
    assert all(field in route for field in classification_policy["required_signal_fields"]), route["signal_id"]
    assert route["bottleneck_category"] in classification_policy["allowed_categories"], route["signal_id"]
    assert route["impact_scope"] in classification_policy["allowed_impact_scope"], route["signal_id"]
    assert route["candidate_owner"] in classification_policy["owner_roles"], route["signal_id"]
    assert route["completion_boundary"].endswith(
        ("not_closure", "not_done", "not_implemented", "before_execution")
    ), route["signal_id"]
    signal = signals[route["signal_id"]]
    if route["next_plan_or_feature_ticket"].startswith("docs/plans/add-feature/"):
        assert (root / route["next_plan_or_feature_ticket"]).exists(), route["signal_id"]
    else:
        assert route["next_plan_or_feature_ticket"] == signal["candidate_route"], route["signal_id"]
assert payload["remediation_flow"]["current_scope_terminal_state"] == "feature_ticket_or_plan_materialized"
assert payload["remediation_flow"]["forbidden_current_scope_states"] == [
    "approved_implementation_executed",
    "recurrence_closed",
]
remediation_states = set(payload["remediation_flow"]["states"])
assert payload["remediation_flow"]["current_scope_terminal_state"] in remediation_states
assert set(payload["remediation_flow"]["forbidden_current_scope_states"]) <= remediation_states
assert payload["remediation_flow"]["current_scope_terminal_state"] not in set(
    payload["remediation_flow"]["forbidden_current_scope_states"]
)
assert {item["artifact"] for item in payload["l6_design_coverage"]} == set(
    payload["sources"]["l6_function_specs"]
)
assert {item["path"] for item in payload["deferred_feature_boundaries"]} == set(
    payload["sources"]["deferred_feature_entry_points"]
)
feature_boundaries = {item["id"]: item for item in payload["deferred_feature_boundaries"]}
assert feature_boundaries["db_evidence_lifecycle"]["unlocks"] == [
    "document auto-registration projection",
    "bottleneck candidate persistence",
    "feedback loop candidate persistence",
    "recurrence closure evidence",
]
for refs in payload["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for ref in payload["sources"]["current_code_surfaces_read_only"]:
    assert ref.startswith("cli/lib/"), ref
    assert (root / ref).exists(), ref
for item in payload["bottleneck_signal_sources"]:
    assert (root / item["current_l1_l6_evidence"]).exists(), item["id"]
    assert item["candidate_route"], item["id"]
for item in payload["l6_design_coverage"]:
    artifact = root / item["artifact"]
    assert artifact.exists(), item["id"]
    artifact_text = artifact.read_text(encoding="utf-8")
    for function_ref in item["covered_functions"]:
        tokens = [
            token.strip("`")
            for token in re.split(r"[\s/\-]+", function_ref)
            if len(token.strip("`")) > 2
        ]
        assert any(token in artifact_text for token in tokens), (item["id"], function_ref)
for item in payload["deferred_feature_boundaries"]:
    assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
    assert (root / item["path"]).exists(), item["id"]
    assert item["unlocks"], item["id"]
invariant_text = "\n".join(payload["invariants"])
assert "candidate is not remediation closure" in invariant_text
assert "must not be auto-applied" in invariant_text
assert payload["completion_denial"]["reason"].startswith(
    "This audit proves L1-L6 bottleneck remediation readiness only"
)
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 ratification index is read path, not L7 work" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
root = path.resolve().parents[3]
payload = yaml.safe_load(path.read_text(encoding="utf-8"))
fr31_trace = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml").read_text(
        encoding="utf-8"
    )
)
double_check = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))
reference_integrity = yaml.safe_load(Path(sys.argv[3]).read_text(encoding="utf-8"))
asset_inventory = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-design-asset-inventory.yaml").read_text(
        encoding="utf-8"
    )
)
pair_balance = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml").read_text(
        encoding="utf-8"
    )
)
fr18_l6_unit_test_design_index = yaml.safe_load(
    (root / "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml").read_text(
        encoding="utf-8"
    )
)
web_evidence = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml").read_text(
        encoding="utf-8"
    )
)
guard_map = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml").read_text(
        encoding="utf-8"
    )
)
harness_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
harness_pre_adoption = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-13-l1-l6-harness-pre-adoption-requirements-acceptance.yaml").read_text(
        encoding="utf-8"
    )
)
improvement_candidates = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml").read_text(
        encoding="utf-8"
    )
)
workflow_automation = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
governance_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
db_feedback_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
dependency_impact = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
db_registration_readiness = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
bottleneck_readiness = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
full_gap_status = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml").read_text(
        encoding="utf-8"
    )
)
exit_criteria = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml").read_text(
        encoding="utf-8"
    )
)
deferred_feature_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml").read_text(
        encoding="utf-8"
    )
)
deferred_design_obligation = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml").read_text(
        encoding="utf-8"
    )
)
legacy_classification = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml").read_text(
        encoding="utf-8"
    )
)

assert payload["schema_version"] == "l1_l6_ratification_index_v1"
assert payload["status"] == "ratified_l1_l6_current_scope_not_full_goal"
assert payload["scope"] == "L1-L6"
assert payload["boundary"]["l7_work_requested_by_user"] is False
assert payload["boundary"]["l7_work_requires_feature_ticket"] is True
assert payload["boundary"]["ratification_index_is_l7_work"] is False
assert payload["boundary"]["ratification_index_is_implementation_evidence"] is False
assert payload["boundary"]["l7_test_design_created_by_this_index"] is False
assert payload["boundary"]["l7_implementation_done"] is False
assert payload["boundary"]["helix_db_write_performed"] is False
assert payload["boundary"]["external_tool_executed"] is False
assert payload["boundary"]["full_goal_complete"] is False
assert payload["ratification_summary"]["current_scope_verdict"] == "pass_l1_l6_only"
assert payload["ratification_summary"]["full_goal_verdict"] == "active_not_complete"
assert payload["ratification_summary"]["core_audit_bundle_files_indexed"] == 23
assert payload["ratification_summary"]["integrity_audits_indexed"] == 2
assert payload["ratification_summary"]["double_check_quantitative_checks_total"] == double_check["summary"]["quantitative_checks"]
assert payload["ratification_summary"]["double_check_quantitative_checks_pass"] == 21
assert payload["ratification_summary"]["double_check_qualitative_checks_total"] == double_check["summary"]["qualitative_checks"]
assert payload["ratification_summary"]["double_check_qualitative_checks_pass"] == 36
evidence_boundary_scan = {
    item["id"]: item for item in double_check["qualitative_checks"]
}["L-EVIDENCE-BOUNDARY-SCAN"]["expected"]
assert payload["ratification_summary"]["evidence_boundary_scan_evidence_like_keys_checked"] == len(evidence_boundary_scan["evidence_like_keys_checked"])
assert payload["ratification_summary"]["evidence_boundary_scan_boundary_context_refs"] == evidence_boundary_scan["boundary_context_refs"]
assert payload["ratification_summary"]["evidence_boundary_scan_negative_boundary_check_refs"] == evidence_boundary_scan["negative_boundary_check_refs"]
assert payload["ratification_summary"]["evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"] == evidence_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
assert payload["ratification_summary"]["evidence_boundary_scan_current_scope_proof_allows_add_feature"] == evidence_boundary_scan["current_scope_proof_allows_add_feature"]
assert payload["ratification_summary"]["evidence_boundary_scan_current_scope_proof_allows_l7_test_design"] == evidence_boundary_scan["current_scope_proof_allows_l7_test_design"]
assert payload["ratification_summary"]["l0_problem_axes_checked"] == 10
assert payload["ratification_summary"]["l0_problem_axes_with_l1_l6_design_evidence"] == 10
assert payload["ratification_summary"]["l0_problem_axis_rows_with_mapped_requirements"] == 10
assert payload["ratification_summary"]["l0_problem_axis_rows_with_l4_l6_design_evidence"] == 10
assert payload["ratification_summary"]["l0_problem_axis_rows_with_audit_evidence"] == 10
assert payload["ratification_summary"]["l0_target_areas_checked"] == 10
assert payload["ratification_summary"]["l0_target_areas_with_l1_l6_design_evidence"] == 10
assert payload["ratification_summary"]["l0_target_area_rows_with_current_scope_evidence"] == 10
assert payload["ratification_summary"]["l0_rows_with_current_scope_result"] == 20
assert payload["ratification_summary"]["legacy_runtime_retrofit_required_items"] == 1
assert payload["ratification_summary"]["legacy_runtime_metadata_gap_ticketed"] is True
assert payload["ratification_summary"]["legacy_runtime_feature_ticket_metadata_match_required"] is True
assert payload["ratification_summary"]["legacy_runtime_next_action_supersedes_current_json_metadata"] is True
assert payload["ratification_summary"]["legacy_runtime_safe_task_retitle_command_available_now"] is False
assert payload["ratification_summary"]["legacy_handover_metadata_boundary_items_checked"] == 1
assert payload["ratification_summary"]["legacy_handover_current_json_l7_label_authorizes_work"] is False
assert payload["ratification_summary"]["legacy_handover_ready_for_review_status_not_completion"] is True
assert payload["ratification_summary"]["legacy_handover_next_action_is_authoritative"] is True
runtime_retrofit = legacy_classification["runtime_retrofit_required"][0]
handover_boundary = legacy_classification["handover_metadata_boundary"][0]
assert payload["ratification_summary"][
    "legacy_runtime_retrofit_required_items"
] == legacy_classification["summary"]["runtime_retrofit_required_items"]
assert payload["ratification_summary"][
    "legacy_runtime_files_with_old_enum_ticketed"
] == legacy_classification["summary"]["runtime_files_with_old_enum_ticketed"]
assert payload["ratification_summary"][
    "legacy_runtime_metadata_gap_ticketed"
] is bool(runtime_retrofit["observed_metadata_gap"])
assert payload["ratification_summary"][
    "legacy_runtime_feature_ticket_metadata_match_required"
] == runtime_retrofit["feature_ticket_metadata_must_match_observed_gap"]
assert payload["ratification_summary"][
    "legacy_runtime_next_action_supersedes_current_json_metadata"
] == runtime_retrofit["observed_metadata_gap"][
    "next_action_supersedes_current_json_task_metadata"
]
assert payload["ratification_summary"][
    "legacy_runtime_safe_task_retitle_command_available_now"
] == runtime_retrofit["observed_metadata_gap"][
    "safe_task_retitle_command_available_now"
]
assert payload["ratification_summary"][
    "legacy_handover_metadata_boundary_items_checked"
] == legacy_classification["summary"]["handover_metadata_boundary_items_checked"]
assert payload["ratification_summary"][
    "legacy_handover_current_json_l7_label_authorizes_work"
] == legacy_classification["summary"]["handover_current_json_l7_label_authorizes_work"]
assert payload["ratification_summary"][
    "legacy_handover_ready_for_review_status_not_completion"
] == legacy_classification["summary"]["handover_ready_for_review_status_not_completion"]
assert payload["ratification_summary"][
    "legacy_handover_next_action_is_authoritative"
] == legacy_classification["summary"]["handover_next_action_is_authoritative"]
assert payload["ratification_summary"][
    "legacy_contract_design_retrofit_required_items"
] == legacy_classification["summary"]["contract_design_retrofit_required_items"]
assert payload["ratification_summary"][
    "legacy_contract_design_files_with_old_phase_labels_classified"
] == legacy_classification["summary"][
    "contract_design_files_with_old_phase_labels_classified"
]
assert payload["ratification_summary"][
    "legacy_contract_design_feature_tickets_created"
] == legacy_classification["summary"]["contract_design_feature_tickets_created"]
assert payload["ratification_summary"][
    "legacy_current_sources_of_truth_checked"
] == legacy_classification["summary"]["current_sources_of_truth_checked"]
assert payload["ratification_summary"][
    "legacy_blocking_findings_current_l1_l6_scope"
] == legacy_classification["summary"]["blocking_findings_current_l1_l6_scope"]
assert payload["ratification_summary"][
    "legacy_l7_artifacts_created_by_this_audit"
] == legacy_classification["summary"]["l7_artifacts_created_by_this_audit"]
assert handover_boundary["current_scope_action"] == "classify_handover_metadata_only_no_runtime_edit"
assert payload["ratification_summary"]["guard_surfaces_checked"] == guard_map["summary"]["guard_surfaces"]
assert payload["ratification_summary"]["guard_parity_gap_routes_checked"] == guard_map["summary"]["parity_gap_routes_checked"]
assert payload["ratification_summary"]["parity_finding_normalization_contracts_checked"] == guard_map["summary"]["parity_finding_normalization_contracts_checked"]
assert payload["ratification_summary"]["parity_closure_requirements_checked"] == guard_map["summary"]["parity_closure_requirements_checked"]
assert payload["ratification_summary"]["guard_codex_runtime_evidence_surfaces_checked"] == guard_map["summary"]["codex_runtime_evidence_surfaces"]
assert payload["ratification_summary"]["guard_l6_design_only_surfaces_checked"] == guard_map["summary"]["l6_design_only_surfaces"]
assert payload["ratification_summary"]["guard_future_plan_required_surfaces_checked"] == guard_map["summary"]["future_plan_required_surfaces"]
assert payload["ratification_summary"]["guard_blocking_findings_current_scope"] == guard_map["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["harness_external_tool_adoption_recheck_controls_checked"] == harness_coverage["summary"]["adoption_recheck_controls_checked"]
assert payload["ratification_summary"]["harness_external_tool_pre_adoption_requirement_contracts_checked"] == harness_coverage["summary"]["pre_adoption_requirement_contracts_checked"]
assert payload["ratification_summary"]["harness_external_tool_current_session_web_fetch_sources_checked"] == harness_coverage["summary"]["current_session_web_fetch_sources_checked"]
assert payload["ratification_summary"]["harness_external_tool_latest_core_rechecked_sources_checked"] == 5
assert payload["ratification_summary"]["harness_external_tool_all_candidate_sources_checked"] == 33
assert payload["ratification_summary"]["harness_external_tool_spot_recheck_sources_checked"] == 8
assert payload["ratification_summary"]["harness_external_tool_spot_recheck_subset_of_canonical"] is True
assert payload["ratification_summary"]["harness_external_tool_spot_recheck_not_full_candidate_recheck"] is True
assert payload["ratification_summary"]["harness_external_tool_scope_contract_l7_artifact_allowed"] is False
assert payload["ratification_summary"]["harness_external_tool_tool_candidates_checked"] == harness_coverage["summary"]["tool_candidates_checked"]
assert payload["ratification_summary"]["harness_external_tool_intake_contracts_checked"] == harness_coverage["summary"]["tool_intake_contracts_checked"]
assert payload["ratification_summary"]["harness_external_tool_admission_gate_contracts_checked"] == harness_coverage["summary"]["admission_gate_contracts_checked"]
assert payload["ratification_summary"]["harness_external_tool_output_ingestion_contracts_checked"] == harness_coverage["summary"]["tool_output_ingestion_contracts_checked"]
assert payload["ratification_summary"]["harness_external_tool_design_layers_checked"] == harness_coverage["summary"]["design_layers_checked"]
assert payload["ratification_summary"]["harness_external_tool_l6_functions_defined"] == harness_coverage["summary"]["l6_functions_defined"]
assert payload["ratification_summary"]["harness_external_tool_l6_unit_test_viewpoints_defined"] == harness_coverage["summary"]["l6_unit_test_viewpoints_defined"]
assert payload["ratification_summary"]["harness_external_tool_blocking_findings_current_scope"] == harness_coverage["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["harness_external_tool_l7_artifacts_created_by_this_audit"] == harness_coverage["summary"]["l7_artifacts_created_by_this_audit"]
harness_accountability = harness_coverage["harness_tool_accountability_contract"]
assert payload["ratification_summary"]["harness_external_tool_accountability_indexed"] is True
assert payload["ratification_summary"]["harness_external_tool_web_evidence_is_design_basis_not_adoption"] == harness_accountability["web_evidence_is_design_basis_not_adoption"]
assert payload["ratification_summary"]["harness_external_tool_current_scope_must_keep_install_execution_ci_db_false"] == harness_accountability["current_scope_must_keep_install_execution_ci_db_false"]
assert payload["ratification_summary"]["harness_external_tool_l7_work_requires_feature_ticket"] == harness_accountability["l7_work_requires_feature_ticket"]
assert payload["ratification_summary"]["harness_external_tool_adoption_or_execution_allowed_now"] is False
assert payload["ratification_summary"]["harness_external_tool_db_write_allowed_now"] is False
assert payload["ratification_summary"]["harness_external_tool_ci_or_equivalent_connection_allowed_now"] is False
assert payload["ratification_summary"]["web_evidence_sources_verified"] == web_evidence["boundary"]["web_sources_verified"]
assert payload["ratification_summary"]["web_evidence_official_sources_checked"] == web_evidence["web_evidence_freshness_contract"]["official_sources_expected"]
assert payload["ratification_summary"]["web_evidence_latest_core_rechecked_sources_checked"] == len(web_evidence["web_evidence_freshness_contract"]["latest_core_rechecked_source_ids"])
assert payload["ratification_summary"]["web_evidence_all_sources_not_adopted_current_scope"] == web_evidence["web_evidence_freshness_contract"]["all_sources_must_remain_not_adopted_current_scope"]
assert payload["ratification_summary"]["web_evidence_l7_or_adoption_evidence_allowed"] == web_evidence["web_evidence_freshness_contract"]["l7_or_adoption_evidence_allowed"]
assert payload["ratification_summary"]["reference_integrity_path_like_refs_checked"] == 1384
assert payload["ratification_summary"]["reference_integrity_direct_file_refs_checked"] == 1375
assert payload["ratification_summary"]["reference_integrity_audit_files_checked"] == reference_integrity["summary"]["audit_files_checked"]
assert payload["ratification_summary"]["reference_integrity_glob_patterns_checked"] == reference_integrity["summary"]["glob_patterns_checked"]
assert payload["ratification_summary"]["reference_integrity_missing_direct_file_refs"] == reference_integrity["summary"]["missing_direct_file_refs"]
assert payload["ratification_summary"]["reference_integrity_empty_glob_patterns"] == reference_integrity["summary"]["empty_glob_patterns"]
assert payload["ratification_summary"]["design_asset_total_l1_l6_files"] == asset_inventory["asset_counts"]["total_l1_l6_files"]
assert payload["ratification_summary"]["design_asset_l1_requirement_files"] == asset_inventory["asset_counts"]["l1_requirement_files"]
assert payload["ratification_summary"]["design_asset_l2_screen_design_files"] == asset_inventory["asset_counts"]["l2_screen_design_files"]
assert payload["ratification_summary"]["design_asset_l3_requirement_files"] == asset_inventory["asset_counts"]["l3_requirement_files"]
assert payload["ratification_summary"]["design_asset_l4_basic_design_files"] == asset_inventory["asset_counts"]["l4_basic_design_files"]
assert payload["ratification_summary"]["design_asset_l5_detailed_design_files"] == asset_inventory["asset_counts"]["l5_detailed_design_files"]
assert payload["ratification_summary"]["design_asset_l6_functional_design_files"] == asset_inventory["asset_counts"]["l6_functional_design_files"]
assert payload["ratification_summary"]["design_asset_l6_assets_partitioned"] == asset_inventory["l6_design_clusters"]["partition_policy"]["all_l6_assets_partitioned"]
assert payload["ratification_summary"]["design_asset_l6_partition_clusters"] == 3
assert payload["ratification_summary"]["design_asset_l6_l7_ref_occurrences"] == asset_inventory["l6_l7_reference_boundary"]["l7_ref_occurrences_in_l6_docs"]
assert payload["ratification_summary"]["design_asset_future_placeholder_targets"] == asset_inventory["l6_l7_reference_boundary"]["future_placeholder_targets"]
assert payload["ratification_summary"]["design_asset_inventory_uses_l7_as_execution_evidence"] == asset_inventory["boundary"]["inventory_uses_l7_as_execution_evidence"]
assert payload["ratification_summary"]["design_asset_l7_artifacts_created_by_this_inventory"] == asset_inventory["boundary"]["l7_test_design_created_by_this_inventory"]
assert payload["ratification_summary"]["grain_balance_current_scope_status"] == asset_inventory["coverage_evidence"]["grain_balance"]["l1_l6_current_scope_status"]
assert payload["ratification_summary"]["double_check_quantitative_checks_pass"] == double_check["summary"]["quantitative_checks_pass"]
assert payload["ratification_summary"]["double_check_qualitative_checks_pass"] == double_check["summary"]["qualitative_checks_pass"]
assert payload["ratification_summary"]["reference_integrity_path_like_refs_checked"] == reference_integrity["summary"]["path_like_refs_checked"]
assert payload["ratification_summary"]["reference_integrity_direct_file_refs_checked"] == reference_integrity["summary"]["direct_file_refs_checked"]
assert payload["ratification_summary"]["objective_audit_files_indexed"] == len(payload["sources"]["objective_audit"])
assert payload["ratification_summary"]["core_audit_bundle_files_indexed"] == len(payload["sources"]["core_audit_bundle"])
assert payload["ratification_summary"]["integrity_audits_indexed"] == len(payload["sources"]["integrity_audits"])
assert payload["ratification_summary"]["l0_problem_axes_checked"] == 10
assert payload["ratification_summary"]["l0_target_areas_checked"] == 10
assert payload["ratification_summary"]["l1_l6_audit_sources_declared"] == 13
assert payload["ratification_summary"]["row_audit_refs_checked"] == 32
assert payload["ratification_summary"]["unique_row_audit_refs_checked"] == 11
assert payload["ratification_summary"]["undeclared_row_audit_refs"] == 0
assert payload["ratification_summary"]["fr31_requirement_count"] == fr31_trace["summary"]["requirement_count"]
assert payload["ratification_summary"]["fr31_all_requirements_have_design_link"] == fr31_trace["summary"]["all_requirements_have_design_link"]
assert payload["ratification_summary"]["fr31_all_design_definition_ids_present"] == fr31_trace["summary"]["all_design_definition_ids_present"]
assert payload["ratification_summary"]["fr31_missing_downstream_count"] == len(fr31_trace["summary"]["missing_downstream"])
assert payload["ratification_summary"]["fr31_orphan_design_count"] == len(fr31_trace["summary"]["orphan_design"])
assert payload["ratification_summary"]["fr31_blocking_findings"] == fr31_trace["summary"]["blocking_findings"]
assert payload["ratification_summary"]["legacy_reference_files_checked"] == legacy_classification["summary"]["legacy_reference_files_checked"]
assert payload["ratification_summary"]["legacy_reference_files_marked_or_already_marked"] == legacy_classification["summary"]["legacy_reference_files_marked_or_already_marked"]
assert payload["ratification_summary"]["exit_layers_checked"] == exit_criteria["summary"]["exit_layers_checked"]
assert payload["ratification_summary"]["exit_layers_pass"] == exit_criteria["summary"]["exit_layers_pass"]
assert payload["ratification_summary"]["exit_layers_with_waiver"] == exit_criteria["summary"]["exit_layers_with_waiver"]
assert payload["ratification_summary"]["exit_gate_ids_checked"] == len(exit_criteria["summary"]["gate_ids_checked"])
assert payload["ratification_summary"]["exit_blocking_findings_current_scope"] == exit_criteria["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["exit_l7_artifacts_created_by_this_map"] == exit_criteria["summary"]["l7_artifacts_created_by_this_map"]
assert payload["ratification_summary"]["deferred_objective_clauses_checked"] == deferred_feature_coverage["summary"]["objective_clauses_checked"]
assert payload["ratification_summary"]["deferred_entry_points_checked"] == deferred_feature_coverage["summary"]["deferred_entry_points_checked"]
assert payload["ratification_summary"]["deferred_feature_tickets_checked"] == deferred_feature_coverage["summary"]["feature_tickets_checked"]
assert payload["ratification_summary"]["deferred_feature_tickets_indexed"] == len(payload["feature_ticket_boundaries"])
assert payload["ratification_summary"]["deferred_feature_tickets_indexed"] == 11
assert payload["ratification_summary"]["deferred_feature_tickets_draft"] == deferred_feature_coverage["summary"]["feature_tickets_draft"]
assert payload["ratification_summary"]["deferred_feature_tickets_with_approval_boundary"] == deferred_feature_coverage["summary"]["feature_tickets_with_approval_boundary"]
assert payload["ratification_summary"]["deferred_feature_unlock_conditions_checked"] == 11
assert payload["ratification_summary"]["deferred_feature_unlock_conditions_checked"] == deferred_feature_coverage["summary"]["feature_tickets_with_unlock_conditions"]
assert payload["ratification_summary"]["deferred_repository_add_feature_files_discovered"] == deferred_feature_coverage["summary"]["repository_add_feature_files_discovered"]
assert payload["ratification_summary"]["deferred_current_objective_deferred_feature_tickets"] == deferred_feature_coverage["summary"]["current_objective_deferred_feature_tickets"]
assert payload["ratification_summary"]["deferred_out_of_current_objective_add_feature_files"] == deferred_feature_coverage["summary"]["out_of_current_objective_add_feature_files"]
assert payload["ratification_summary"]["deferred_out_of_current_objective_completed_add_features"] == deferred_feature_coverage["summary"]["out_of_current_objective_completed_add_features"]
assert payload["ratification_summary"]["deferred_out_of_current_objective_parked_feature_tickets"] == deferred_feature_coverage["summary"]["out_of_current_objective_parked_feature_tickets"]
assert payload["ratification_summary"]["deferred_full_flow_later_phase_approval_boundary"] == deferred_feature_coverage["summary"]["full_flow_later_phase_approval_boundary"]
assert payload["ratification_summary"]["deferred_clauses_without_deferred_work"] == deferred_feature_coverage["summary"]["clauses_without_deferred_work"]
assert payload["ratification_summary"]["deferred_clauses_mapped_to_feature_ticket"] == deferred_feature_coverage["summary"]["clauses_mapped_to_feature_ticket"]
assert payload["ratification_summary"]["deferred_unmapped_deferred_boundaries"] == deferred_feature_coverage["summary"]["unmapped_deferred_boundaries"]
assert payload["ratification_summary"]["deferred_l7_artifacts_created_by_this_audit"] == deferred_feature_coverage["summary"]["l7_artifacts_created_by_this_audit"]
assert payload["ratification_summary"]["deferred_design_obligation_rows_checked"] == deferred_design_obligation["summary"]["feature_tickets_checked"]
assert payload["ratification_summary"]["deferred_design_obligation_rows_with_prior_l1_l6_design_evidence"] == deferred_design_obligation["summary"]["feature_tickets_with_prior_l1_l6_design_evidence"]
assert payload["ratification_summary"]["deferred_design_obligation_escape_findings"] == deferred_design_obligation["summary"]["feature_tickets_using_ticket_as_design_substitute"]
assert payload["ratification_summary"]["deferred_design_gap_reopen_rules_defined"] == deferred_design_obligation["summary"]["design_gap_reopen_rules_defined"]
assert payload["ratification_summary"]["deferred_escalation_bound_design_tickets_checked"] == deferred_design_obligation["summary"]["escalation_bound_design_tickets_checked"]
assert payload["ratification_summary"]["deferred_implementation_or_execution_tickets_checked"] == deferred_design_obligation["summary"]["implementation_or_execution_tickets_checked"]
assert payload["ratification_summary"]["harness_pre_adoption_representative_sources_rechecked"] == harness_pre_adoption["summary"]["representative_sources_rechecked"]
assert payload["ratification_summary"]["harness_pre_adoption_requirement_contracts_checked"] == harness_pre_adoption["summary"]["pre_adoption_requirement_contracts_checked"]
assert payload["ratification_summary"]["harness_pre_adoption_l1_l3_requirement_surfaces_reused"] == harness_pre_adoption["summary"]["l1_l3_requirement_surfaces_reused"]
assert payload["ratification_summary"]["harness_pre_adoption_acceptance_design_obligations_defined"] == harness_pre_adoption["summary"]["acceptance_design_obligations_defined"]
assert payload["ratification_summary"]["harness_pre_adoption_blocking_findings_current_scope"] == harness_pre_adoption["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["harness_pre_adoption_l7_artifacts_created_by_this_audit"] == harness_pre_adoption["summary"]["l7_artifacts_created_by_this_audit"]
summary_coverage = payload["summary_coverage_index"]
assert summary_coverage["current_scope_action"] == "prove_source_audit_summary_keys_are_indexed"
assert summary_coverage["coverage_index_is_l7_work"] is False
assert summary_coverage["coverage_index_is_implementation_evidence"] is False
assert summary_coverage["l7_work_requested_by_user"] is False
assert summary_coverage["source_summary_maps_checked"] == 19
assert summary_coverage["source_summary_maps_checked"] == len(summary_coverage["coverage_rows"])
mapping_policy = summary_coverage["key_mapping_policy"]
assert mapping_policy["default_transform"] == "identity"
assert mapping_policy["already_prefixed_source_key_uses_identity"] is True
assert mapping_policy["supported_transforms"] == ["identity", "length"]
mapping_rules = {rule["source_id"]: rule for rule in mapping_policy["rules"]}
assert set(mapping_rules) == {row["source_id"] for row in summary_coverage["coverage_rows"]}
source_summary_key_count = 0
for row in summary_coverage["coverage_rows"]:
    rule = mapping_rules[row["source_id"]]
    source_payload = yaml.safe_load((root / row["source"]).read_text(encoding="utf-8"))
    source_summary = source_payload["summary"]
    source_summary_key_count += len(source_summary)
    assert row["summary_keys_checked"] == len(source_summary)
    assert row["coverage_status"] == "pass"
    assert row["unmapped_summary_keys"] == []
    overrides = rule.get("key_overrides", {})
    transforms = rule.get("value_transforms", {})
    for source_key, source_value in source_summary.items():
        ratification_key = overrides.get(source_key)
        if ratification_key is None:
            prefix = rule["ratification_key_prefix"]
            ratification_key = source_key if source_key.startswith(prefix) else f"{prefix}{source_key}"
        expected_value = (
            len(source_value)
            if transforms.get(source_key, mapping_policy["default_transform"]) == "length"
            else source_value
        )
        assert ratification_key in payload["ratification_summary"], (row["source_id"], source_key)
        assert payload["ratification_summary"][ratification_key] == expected_value, (
            row["source_id"],
            source_key,
            ratification_key,
        )
assert summary_coverage["source_summary_keys_checked"] == source_summary_key_count
assert summary_coverage["source_summary_keys_checked"] == 219
assert summary_coverage["sources_with_unmapped_summary_keys"] == 0
assert summary_coverage["unmapped_summary_keys"] == []
assert payload["ratification_summary"]["pair_contract_matrix_layers_checked"] == pair_balance["summary"]["pair_contract_matrix_layers_checked"]
assert payload["ratification_summary"]["pair_l1_l6_layers_checked"] == pair_balance["summary"]["l1_l6_layers_checked"]
assert payload["ratification_summary"]["pair_layers_pass"] == pair_balance["summary"]["layers_pass"]
assert payload["ratification_summary"]["pair_layers_with_waiver"] == pair_balance["summary"]["layers_with_waiver"]
assert payload["ratification_summary"]["paired_artifacts_checked"] == pair_balance["summary"]["paired_artifacts_checked"]
assert payload["ratification_summary"]["expected_design_refs_checked"] == pair_balance["summary"]["expected_design_refs_checked"]
assert payload["ratification_summary"]["expected_design_refs_backed_by_design_assets"] == pair_balance["summary"]["expected_design_refs_backed_by_design_assets"]
assert payload["ratification_summary"]["expected_design_refs_missing_from_design_assets"] == pair_balance["summary"]["expected_design_refs_missing_from_design_assets"]
assert payload["ratification_summary"]["pair_l6_unit_test_design_viewpoint_count"] == pair_balance["summary"]["l6_unit_test_design_viewpoint_count"]
assert payload["ratification_summary"]["fr18_specs_current_scope_l6_closed"] == fr18_l6_unit_test_design_index["coverage_summary"]["specs_current_scope_l6_closed"]
assert payload["ratification_summary"]["fr18_specs_with_draft_status"] == len(fr18_l6_unit_test_design_index["coverage_summary"]["specs_with_draft_status"])
assert payload["ratification_summary"]["improvement_candidates_indexed"] == improvement_candidates["candidate_summary"]["total_candidates"]
assert payload["ratification_summary"]["improvement_candidates_design_only"] == improvement_candidates["candidate_summary"]["current_scope_actions"]["design_only"]
assert payload["ratification_summary"]["improvement_candidates_feature_ticket_only"] == improvement_candidates["candidate_summary"]["current_scope_actions"]["feature_ticket_only"]
assert payload["ratification_summary"]["improvement_candidates_adopted"] == improvement_candidates["boundary"]["candidates_adopted"]
assert payload["ratification_summary"]["workflow_surfaces_checked"] == workflow_automation["summary"]["workflow_surfaces_checked"]
assert payload["ratification_summary"]["automation_surfaces_checked"] == workflow_automation["summary"]["automation_surfaces_checked"]
assert payload["ratification_summary"]["automation_trigger_contracts_checked"] == workflow_automation["summary"]["automation_trigger_contracts_checked"]
assert payload["ratification_summary"]["workflow_db_registry_targets_mapped"] == workflow_automation["summary"]["db_registry_targets_mapped"]
assert payload["ratification_summary"]["workflow_detector_gate_routes_mapped"] == workflow_automation["summary"]["detector_gate_routes_mapped"]
assert payload["ratification_summary"]["workflow_cross_audit_convergence_rows_checked"] == workflow_automation["summary"]["cross_audit_convergence_rows_checked"]
assert payload["ratification_summary"]["workflow_deferred_feature_entry_points_checked"] == workflow_automation["summary"]["deferred_feature_entry_points_checked"]
assert payload["ratification_summary"]["workflow_parked_feature_entry_points_checked"] == workflow_automation["summary"]["parked_feature_entry_points_checked"]
assert payload["ratification_summary"]["workflow_blocking_findings_current_scope"] == workflow_automation["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["workflow_l7_artifacts_created_by_this_audit"] == workflow_automation["summary"]["l7_artifacts_created_by_this_audit"]
assert payload["ratification_summary"]["governance_surfaces_checked"] == governance_coverage["summary"]["governance_surfaces_checked"]
assert payload["ratification_summary"]["governance_l6_design_docs_checked"] == governance_coverage["summary"]["l6_design_docs_checked"]
assert payload["ratification_summary"]["governance_l6_function_contracts_checked"] == governance_coverage["summary"]["l6_function_contracts_checked"]
assert payload["ratification_summary"]["governance_l6_ut_candidate_viewpoints"] == governance_coverage["summary"]["current_scope_l6_ut_candidate_viewpoints"]
assert payload["ratification_summary"]["governance_finding_normalization_contracts_checked"] == governance_coverage["summary"]["governance_finding_normalization_contracts_checked"]
assert payload["ratification_summary"]["governance_normalization_required_fields_checked"] == governance_coverage["summary"]["governance_normalization_required_fields_checked"]
assert payload["ratification_summary"]["governance_documentation_readiness_gap_patterns_checked"] == governance_coverage["summary"]["documentation_readiness_gap_patterns_checked"]
assert payload["ratification_summary"]["governance_controls_checked"] == governance_coverage["summary"]["governance_controls_checked"]
assert payload["ratification_summary"]["governance_detection_required_route_fields_checked"] == governance_coverage["summary"]["governance_detection_required_route_fields_checked"]
assert payload["ratification_summary"]["governance_detection_routes_checked"] == governance_coverage["summary"]["governance_detection_routes_checked"]
assert payload["ratification_summary"]["governance_control_trace_rows_checked"] == governance_coverage["summary"]["governance_control_trace_rows_checked"]
assert payload["ratification_summary"]["governance_control_closure_rows_checked"] == governance_coverage["summary"]["governance_control_closure_rows_checked"]
assert payload["ratification_summary"]["governance_preexisting_l7_pair_refs"] == governance_coverage["summary"]["preexisting_l7_pair_refs"]
assert payload["ratification_summary"]["governance_preexisting_completed_feature_entry_points_checked"] == governance_coverage["summary"]["preexisting_completed_feature_entry_points_checked"]
assert payload["ratification_summary"]["governance_blocking_findings_current_scope"] == governance_coverage["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["governance_l7_artifacts_created_by_this_audit"] == governance_coverage["summary"]["l7_artifacts_created_by_this_audit"]
assert payload["ratification_summary"]["db_feedback_design_layers_checked"] == db_feedback_coverage["summary"]["design_layers_checked"]
assert payload["ratification_summary"]["db_feedback_physical_db_design_checked"] == db_feedback_coverage["summary"]["physical_db_design_checked"]
assert payload["ratification_summary"]["db_feedback_lifecycle_states_defined"] == db_feedback_coverage["summary"]["lifecycle_states_defined"]
assert payload["ratification_summary"]["db_feedback_closure_rules_defined"] == db_feedback_coverage["summary"]["closure_rules_defined"]
assert payload["ratification_summary"]["db_feedback_l6_functions_defined"] == db_feedback_coverage["summary"]["l6_functions_defined"]
assert payload["ratification_summary"]["db_feedback_existing_storage_groups_mapped"] == db_feedback_coverage["summary"]["existing_storage_groups_mapped"]
assert payload["ratification_summary"]["db_feedback_existing_tables_required_for_lifecycle_checked"] == db_feedback_coverage["summary"]["existing_tables_required_for_lifecycle_checked"]
assert payload["ratification_summary"]["db_feedback_forbidden_current_scope_rules_checked"] == db_feedback_coverage["summary"]["forbidden_current_scope_rules_checked"]
assert payload["ratification_summary"]["db_feedback_blocking_findings_current_scope"] == db_feedback_coverage["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["db_feedback_l7_artifacts_created_by_this_audit"] == db_feedback_coverage["summary"]["l7_artifacts_created_by_this_audit"]
db_feedback_accountability = db_feedback_coverage["feedback_lifecycle_accountability_contract"]
assert payload["ratification_summary"]["db_feedback_accountability_indexed"] is True
assert payload["ratification_summary"]["db_feedback_feature_ticket_is_not_design_substitute"] == db_feedback_accountability["feature_ticket_is_not_design_substitute"]
assert payload["ratification_summary"]["db_feedback_db_write_requires_explicit_approval"] == db_feedback_accountability["db_write_requires_explicit_approval"]
assert payload["ratification_summary"]["db_feedback_current_scope_must_keep_db_write_false"] == db_feedback_accountability["current_scope_must_keep_db_write_false"]
assert payload["ratification_summary"]["db_feedback_recurrence_closure_requires_later_execution_evidence"] == db_feedback_accountability["recurrence_closure_requires_later_execution_evidence"]
assert payload["ratification_summary"]["db_feedback_schema_migration_done"] == db_feedback_coverage["boundary"]["schema_migration_done"]
assert payload["ratification_summary"]["db_feedback_db_write_connection_done"] == db_feedback_coverage["boundary"]["db_write_connection_done"]
assert payload["ratification_summary"]["dependency_impact_surfaces_checked"] == dependency_impact["summary"]["dependency_impact_surfaces_checked"]
assert payload["ratification_summary"]["dependency_impact_l6_function_specs_checked"] == dependency_impact["summary"]["l6_function_specs_checked"]
assert payload["ratification_summary"]["dependency_impact_current_code_surfaces_checked_read_only"] == dependency_impact["summary"]["current_code_surfaces_checked_read_only"]
assert payload["ratification_summary"]["dependency_impact_required_output_sections"] == dependency_impact["summary"]["required_output_sections"]
assert payload["ratification_summary"]["dependency_impact_db_projection_contracts_checked"] == dependency_impact["summary"]["db_projection_contracts_checked"]
assert payload["ratification_summary"]["dependency_impact_dependency_edge_relations_checked"] == dependency_impact["summary"]["dependency_edge_relations_checked"]
assert payload["ratification_summary"]["dependency_impact_scope_route_contracts_checked"] == dependency_impact["summary"]["impact_scope_route_contracts_checked"]
assert payload["ratification_summary"]["dependency_impact_unknown_scope_resolution_rules_checked"] == dependency_impact["summary"]["unknown_scope_resolution_rules_checked"]
assert payload["ratification_summary"]["dependency_impact_visibility_rows_checked"] == dependency_impact["summary"]["impact_visibility_rows_checked"]
assert payload["ratification_summary"]["dependency_impact_output_trace_rows_checked"] == dependency_impact["summary"]["impact_output_trace_rows_checked"]
assert payload["ratification_summary"]["dependency_impact_blocking_findings_current_scope"] == dependency_impact["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["dependency_impact_l7_artifacts_created_by_this_audit"] == dependency_impact["summary"]["l7_artifacts_created_by_this_audit"]
assert payload["ratification_summary"]["db_registration_events_checked"] == db_registration_readiness["summary"]["registration_events_checked"]
assert payload["ratification_summary"]["db_registration_event_contracts_checked"] == db_registration_readiness["summary"]["registration_event_contracts_checked"]
assert payload["ratification_summary"]["db_registration_document_projection_contracts_checked"] == db_registration_readiness["summary"]["document_projection_contracts_checked"]
assert payload["ratification_summary"]["db_registration_lifecycle_route_contracts_checked"] == db_registration_readiness["summary"]["lifecycle_route_contracts_checked"]
assert payload["ratification_summary"]["db_registration_existing_implementation_surfaces_checked"] == db_registration_readiness["summary"]["existing_implementation_surfaces_checked"]
assert payload["ratification_summary"]["db_registration_l1_l6_design_surfaces_checked"] == db_registration_readiness["summary"]["l1_l6_design_surfaces_checked"]
assert payload["ratification_summary"]["db_registration_readiness_rows"] == db_registration_readiness["summary"]["readiness_rows"]
assert payload["ratification_summary"]["db_registration_event_route_closure_rows_checked"] == db_registration_readiness["summary"]["event_route_closure_rows_checked"]
assert payload["ratification_summary"]["db_registration_add_feature_import_targets_checked"] == db_registration_readiness["summary"]["add_feature_import_targets_checked"]
assert payload["ratification_summary"]["db_registration_blocking_findings_current_scope"] == db_registration_readiness["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["db_registration_l7_feature_tickets_created"] == db_registration_readiness["summary"]["l7_feature_tickets_created"]
assert payload["ratification_summary"]["db_registration_l7_artifacts_created_by_this_audit"] == db_registration_readiness["summary"]["l7_artifacts_created_by_this_audit"]
db_registration_accountability = db_registration_readiness["registration_accountability_contract"]
assert payload["ratification_summary"]["db_registration_accountability_indexed"] is True
assert payload["ratification_summary"]["db_registration_feature_ticket_is_not_design_substitute"] == db_registration_accountability["feature_ticket_is_not_design_substitute"]
assert payload["ratification_summary"]["db_registration_db_write_requires_explicit_approval"] == db_registration_accountability["db_write_requires_explicit_approval"]
assert payload["ratification_summary"]["db_registration_current_scope_must_keep_db_write_false"] == db_registration_accountability["current_scope_must_keep_db_write_false"]
assert payload["ratification_summary"]["db_registration_plan_registry_changed_by_this_audit"] == db_registration_readiness["boundary"]["plan_registry_changed_by_this_audit"]
assert payload["ratification_summary"]["db_registration_helix_db_write_performed"] == db_registration_readiness["boundary"]["helix_db_write_performed"]
assert payload["ratification_summary"]["db_registration_schema_migration_done"] == db_registration_readiness["boundary"]["schema_migration_done"]
assert payload["ratification_summary"]["bottleneck_signal_sources_checked"] == bottleneck_readiness["summary"]["bottleneck_signal_sources_checked"]
assert payload["ratification_summary"]["bottleneck_l6_function_specs_checked"] == bottleneck_readiness["summary"]["l6_function_specs_checked"]
assert payload["ratification_summary"]["bottleneck_remediation_flow_states_defined"] == bottleneck_readiness["summary"]["remediation_flow_states_defined"]
assert payload["ratification_summary"]["bottleneck_forbidden_current_scope_states_checked"] == bottleneck_readiness["summary"]["forbidden_current_scope_states_checked"]
assert payload["ratification_summary"]["bottleneck_required_signal_fields_checked"] == bottleneck_readiness["summary"]["required_signal_fields_checked"]
assert payload["ratification_summary"]["bottleneck_cross_axis_aggregation_contracts_checked"] == bottleneck_readiness["summary"]["cross_axis_aggregation_contracts_checked"]
assert payload["ratification_summary"]["bottleneck_signal_route_contracts_checked"] == bottleneck_readiness["summary"]["signal_route_contracts_checked"]
assert payload["ratification_summary"]["bottleneck_current_code_surfaces_checked_read_only"] == bottleneck_readiness["summary"]["current_code_surfaces_checked_read_only"]
assert payload["ratification_summary"]["bottleneck_deferred_feature_entry_points_checked"] == bottleneck_readiness["summary"]["deferred_feature_entry_points_checked"]
assert payload["ratification_summary"]["bottleneck_deferred_feature_boundaries_checked"] == bottleneck_readiness["summary"]["deferred_feature_boundaries_checked"]
assert payload["ratification_summary"]["bottleneck_required_output_sections"] == bottleneck_readiness["summary"]["required_output_sections"]
assert payload["ratification_summary"]["bottleneck_blocking_findings_current_scope"] == bottleneck_readiness["summary"]["blocking_findings_current_scope"]
assert payload["ratification_summary"]["bottleneck_l7_artifacts_created_by_this_audit"] == bottleneck_readiness["summary"]["l7_artifacts_created_by_this_audit"]
assert payload["ratification_summary"]["full_goal_unlock_evidence_classes_indexed"] == 8
assert payload["ratification_summary"]["full_goal_unlock_required_feature_tickets_resolved"] == 8
assert payload["ratification_summary"]["right_arm_execution_gates_deferred"] == 4
assert payload["ratification_summary"]["l7_artifacts_created_by_this_index"] == 0
full_unlock_index = payload["full_goal_unlock_evidence_index"]
full_unlock_contract = full_gap_status["full_goal_completion_unlock_evidence_contract"]
assert full_unlock_index == {
    "source": "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
    "source_contract": "full_goal_completion_unlock_evidence_contract",
    "current_scope_action": "index_unlock_evidence_only",
    "evidence_namespace": "full_goal_unlock_required_evidence_not_current_scope_proof",
    "required_evidence_count": 8,
    "required_evidence_is_current_scope_proof": False,
    "required_evidence_is_completion_evidence_now": False,
    "required_feature_tickets_resolved": 8,
    "required_feature_ticket_is_completion_evidence": False,
    "may_satisfy_completion_only_after_approval_and_execution": True,
    "feature_ticket_resolution_source": "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml",
    "feature_ticket_resolution_contract": "full_goal_completion_unlock_evidence_contract.feature_ticket_resolution_contract",
    "indexed_evidence_ids": [
        "L7-UNIT-CLOSURE",
        "RIGHT-ARM-EXECUTION-GATES",
        "HELIX-DB-WRITE-ADOPTION",
        "RECURRENCE-CLOSURE",
        "EXTERNAL-TOOL-ADOPTION",
        "RUNTIME-GUARD-PARITY",
        "DEPENDENCY-IMPACT-QUERY",
        "BOTTLENECK-ROUTING",
    ],
    "source_feature_tickets_must_exist_in_index": True,
    "index_is_completion_evidence": False,
    "l7_db_ci_external_execution_allowed_by_index": False,
}
assert full_unlock_index["required_evidence_count"] == full_unlock_contract[
    "required_evidence_count"
]
assert full_unlock_index["evidence_namespace"] == full_unlock_contract[
    "evidence_namespace"
]
assert full_unlock_index["required_evidence_is_current_scope_proof"] == full_unlock_contract[
    "required_evidence_is_current_scope_proof"
]
assert full_unlock_index["required_evidence_is_completion_evidence_now"] == full_unlock_contract[
    "required_evidence_is_completion_evidence_now"
]
assert full_unlock_index["required_feature_ticket_is_completion_evidence"] == full_unlock_contract[
    "required_feature_ticket_is_completion_evidence"
]
assert full_unlock_index[
    "may_satisfy_completion_only_after_approval_and_execution"
] == full_unlock_contract["may_satisfy_completion_only_after_approval_and_execution"]
assert full_unlock_index["indexed_evidence_ids"] == [
    item["id"] for item in full_unlock_contract["required_evidence"]
]
l1_l6_design_obligation_index = payload["l1_l6_design_obligation_index"]
l1_l6_design_obligation_contract = full_gap_status["l1_l6_design_obligation_contract"]
assert l1_l6_design_obligation_index == {
    "source": "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
    "proof_source": "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml",
    "source_contract": "l1_l6_design_obligation_contract",
    "current_scope_action": "prove_l1_l6_design_obligation_before_deferring_l7_execution",
    "l1_l6_design_obligation_is_current_scope": True,
    "deferred_feature_tickets_are_not_design_substitute": True,
    "feature_ticket_allowed_only_for_unapproved_l7_or_escalation_bound_execution": True,
    "l1_l6_design_assets_required_before_ticket": True,
    "design_gap_reopened_if_l1_l6_evidence_missing": True,
    "no_feature_escape_for_design_debt": True,
    "l7_or_external_execution_requires_approved_feature_ticket": True,
    "feature_tickets_checked": 11,
    "feature_tickets_with_prior_l1_l6_design_evidence": 11,
    "feature_tickets_using_ticket_as_design_substitute": 0,
    "covered_current_scope_surfaces": [
        "requirement_gap_detection",
        "ddd_tdd_governance_design",
        "helix_db_registration_design",
        "dependency_impact_design",
        "bottleneck_detection_design",
        "codex_claude_guard_parity_design",
    ],
    "index_is_completion_evidence": False,
}
assert l1_l6_design_obligation_index["covered_current_scope_surfaces"] == (
    l1_l6_design_obligation_contract["covered_current_scope_surfaces"]
)
legacy_classification = "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
assert legacy_classification in payload["sources"]["core_audit_bundle"]
ratified_items = {item["id"]: item for item in payload["ratified_l1_l6_items"]}
assert legacy_classification in ratified_items["RAT-L0-L14-FLOW"]["evidence"]
assert len(payload["ratified_l1_l6_items"]) == 9
assert len(payload["feature_ticket_boundaries"]) == 11
feature_tickets = {item["id"]: item for item in payload["feature_ticket_boundaries"]}
if full_unlock_index["source_feature_tickets_must_exist_in_index"]:
    deferred_coverage = yaml.safe_load((root / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml").read_text())
    source_feature_tickets = {
        item["id"]: item for item in deferred_coverage["feature_ticket_integrity"]
    }
    for evidence in full_unlock_contract["required_evidence"]:
        assert evidence["required_feature_ticket"] in feature_tickets, evidence["id"]
        status_field = full_unlock_contract["feature_ticket_resolution_contract"][
            "required_feature_ticket_status_field"
        ]
        assert source_feature_tickets[evidence["required_feature_ticket"]][status_field] == (
            full_unlock_contract["feature_ticket_resolution_contract"][
                "required_feature_ticket_status"
            ]
        )
commands = {item["command"]: item["expected"] for item in payload["verification_commands"]}
assert commands["python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q"] == "87 passed"
assert commands["bats cli/tests/test-helix-l0-l14-flow-contract.bats"] == "56 tests passed"
assert commands["helix doctor check_requirement_drift --json"] == {
    "clean": True,
    "focus": "L6",
    "requirements": 31,
    "design_links": 31,
    "blocking_findings": 0,
    "advisory_findings": 0,
}
assert commands[
    "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json"
] == {
    "exit_status": 0,
    "overall_clean": False,
    "deferred_execution_gates": ["G8", "G9", "G12", "G14"],
}
assert payload["verification_command_contract"] == {
    "current_scope_only": True,
    "commands_must_not_execute_l7_db_ci_external": True,
    "expected_results_are_machine_readable": True,
    "pytest_l0_l14_flow_contract": {
        "command": "python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q",
        "expected_passed_count": 86,
        "expected_output_contains": "87 passed",
        "proves_l7_work": False,
    },
    "bats_l0_l14_flow_contract": {
        "command": "bats cli/tests/test-helix-l0-l14-flow-contract.bats",
        "expected_test_count": 55,
        "expected_tap_plan": "1..55",
        "proves_l7_work": False,
    },
    "requirement_drift_l6_focus": {
        "command": "helix doctor check_requirement_drift --json",
        "expected_json_subset": {
            "clean": True,
            "focus": "L6",
            "requirements": 31,
            "design_links": 31,
            "blocking_findings": 0,
            "advisory_findings": 0,
        },
        "proves_l7_work": False,
    },
    "strict_full_flow_skip_exec": {
        "command": "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json",
        "execution_guard_env": "HELIX_DOCTOR_SKIP_EXEC_TESTS",
        "expected_json_subset": {
            "overall_clean": False,
            "deferred_execution_gates": ["G8", "G9", "G12", "G14"],
        },
        "proves_full_goal_completion": False,
    },
}
l7_doc_prefix = "docs/v2/L7-test-design/"
for refs in payload["sources"].values():
    for ref in refs:
        assert not ref.startswith(l7_doc_prefix), ref
        assert (root / ref).exists(), ref
for item in payload["ratified_l1_l6_items"]:
    for ref in item["evidence"]:
        if ref.startswith("helix "):
            continue
        assert not ref.startswith(l7_doc_prefix), item["id"]
        assert (root / ref).exists(), item["id"]
for item in payload["feature_ticket_boundaries"]:
    assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
    assert not item["path"].startswith(l7_doc_prefix), item["id"]
    ticket_path = root / item["path"]
    assert ticket_path.exists(), item["id"]
    ticket_text = ticket_path.read_text(encoding="utf-8")
    assert ticket_text.startswith("---"), item["id"]
    ticket_meta = yaml.safe_load(ticket_text.split("---", 2)[1])
    assert ticket_meta["status"] == item["current_status"] == "draft", item["id"]
    assert ticket_meta.get("current_task_scope") in {
        "feature_ticket_only",
        "L4_L6_design_closed_feature_ticketed",
    }, item["id"]
    assert "approval_boundary" in ticket_meta, item["id"]
    assert "This PLAN is only a ticket" in ticket_meta["approval_boundary"], item["id"]
    if "l7" in item["path"] or "l7" in item["unlocks"].lower():
        assert ticket_meta.get("approval_required_before_l7_work") is True, item["id"]
    else:
        assert "explicit approval" in ticket_meta["approval_boundary"], item["id"]
    assert "complete" not in str(ticket_meta["status"]).lower(), item["id"]
assert payload["completion_denial"]["reason"].startswith(
    "This index ratifies the current L1-L6 audit bundle only"
)
PY
  [ "$status" -eq 0 ]
}

@test "L0-L14 flow surface coverage pins user-confirmed flow" {
  run python3 - "$HELIX_ROOT/docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
root = path.resolve().parents[3]
payload = yaml.safe_load(path.read_text(encoding="utf-8"))
pair_balance = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml").read_text(
        encoding="utf-8"
    )
)

assert payload["schema_version"] == "l0_l14_flow_surface_coverage_v1"
assert payload["status"] == "current_l0_l14_flow_terms_pinned_l1_l6_scope"
assert payload["boundary"]["l7_work_requested_by_user"] is False
assert payload["boundary"]["l7_work_requires_feature_ticket"] is True
assert payload["boundary"]["flow_surface_audit_is_l7_work"] is False
assert payload["boundary"]["l7_implementation_done"] is False
assert payload["boundary"]["l7_test_design_created_by_this_audit"] is False
assert payload["boundary"]["goal_complete_allowed"] is False
assert payload["summary"] == {
    "layers_checked": 15,
    "left_arm_design_layers_checked": 6,
    "right_arm_execution_or_verification_layers_checked": 7,
    "ui_absent_layer_count": 1,
    "current_surfaces_checked": 90,
    "banned_legacy_terms_found_current_surfaces": 0,
    "blocking_findings_current_scope": 0,
}
flow = {item["layer"]: item for item in payload["current_flow"]}
assert list(flow) == [f"L{idx}" for idx in range(15)]
assert flow["L0"]["stage"] == "企画"
assert flow["L1"]["test_design_or_verification"] == "運用テスト設計"
assert flow["L2"]["stage"] == "画面要求 / 画面設計 / フロントUI"
assert flow["L3"]["test_design_or_verification"] == "受入テスト設計"
assert flow["L4"]["test_design_or_verification"] == "総合テスト設計"
assert flow["L5"]["test_design_or_verification"] == "結合テスト設計"
assert flow["L6"]["test_design_or_verification"] == "単体テスト設計"
assert flow["L7"]["current_scope_l1_l6_status"] == "out_of_current_scope_requires_feature_ticket"
assert flow["L12"]["stage"] == "受入テスト"
assert flow["L14"]["stage"] == "運用学習 / 運用改善"
pairs = {item["design_layer"]: item["execution_layer"] for item in payload["pair_map"]}
assert pairs == {
    "L1": "L14",
    "L2": "L10",
    "L3": "L12",
    "L4": "L9",
    "L5": "L8",
    "L6": "L7",
}
pair_contracts = {item["layer"]: item for item in pair_balance["pair_contract_matrix"]}
assert set(pair_contracts) == set(pairs)
for item in payload["pair_map"]:
    contract = pair_contracts[item["design_layer"]]
    if item["design_layer"] == "L6":
        assert contract["paired_test_design_stage"].startswith(item["test_design"])
    else:
        assert contract["paired_test_design_stage"] == item["test_design"]
    assert contract["expected_pair"] == f"{item['design_layer']}-{item['execution_layer']}"
    assert contract["current_scope_status"] in {
        "pair_contract_present",
        "waiver_present",
        "l6_unit_test_design_viewpoints_only_not_l7_artifact",
    }
for refs in payload["sources"].values():
    for ref in refs:
        assert (root / ref).exists(), ref
current_surfaces = payload["sources"]["current_surfaces_checked"]
legacy_terms = payload["legacy_term_policy"]["current_surfaces_must_not_contain"]
assert payload["summary"]["current_surfaces_checked"] == len(current_surfaces)
assert legacy_terms
for ref in current_surfaces:
    text = (root / ref).read_text(encoding="utf-8")
    for term in legacy_terms:
        assert term not in text, (ref, term)
assert payload["completion_denial"]["reason"].startswith(
    "This audit proves that the current L0-L14 flow vocabulary"
)
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 exit criteria map ratifies G1-G6 without L7 work" {
  run python3 - "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml" <<'PY'
import sys
from pathlib import Path
import yaml

path = Path(sys.argv[1])
root = path.resolve().parents[3]
payload = yaml.safe_load(path.read_text(encoding="utf-8"))

assert payload["schema_version"] == "l1_l6_exit_criteria_map_v1"
assert payload["status"] == "current_scope_l1_l6_exit_criteria_ratified"
assert payload["boundary"]["l7_work_requested_by_user"] is False
assert payload["boundary"]["l7_work_requires_feature_ticket"] is True
assert payload["boundary"]["exit_criteria_map_is_l7_work"] is False
assert payload["boundary"]["exit_criteria_map_is_implementation_evidence"] is False
assert payload["boundary"]["l7_test_design_created_by_this_map"] is False
assert payload["boundary"]["l7_implementation_done"] is False
assert payload["boundary"]["helix_db_write_performed"] is False
assert payload["boundary"]["external_tool_executed"] is False
assert payload["boundary"]["full_goal_complete"] is False
assert payload["summary"] == {
    "exit_layers_checked": 6,
    "exit_layers_pass": 6,
    "exit_layers_with_waiver": 1,
    "gate_ids_checked": ["G1", "G2", "G3", "G4", "G5", "G6"],
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_map": 0,
}
criteria = {item["layer"]: item for item in payload["exit_criteria"]}
assert set(criteria) == {"L1", "L2", "L3", "L4", "L5", "L6"}
assert payload["summary"]["exit_layers_checked"] == len(criteria)
assert payload["summary"]["exit_layers_pass"] == sum(
    1 for item in criteria.values() if item["verdict"].startswith("pass")
)
assert payload["summary"]["exit_layers_with_waiver"] == sum(
    1 for item in criteria.values() if "waiver" in item
)
assert payload["summary"]["gate_ids_checked"] == [
    criteria[layer]["exit_gate"] for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]
]
assert criteria["L2"]["verdict"] == "pass_with_waiver"
assert criteria["L2"]["waiver"] == {
    "reason": "ui_absent",
    "path": "docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md",
}
assert criteria["L4"]["verdict"] == "pass_with_monitoring"
assert len(criteria["L6"]["required_artifacts"]) == 19
for refs in payload["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for item in criteria.values():
    assert item["pass_conditions"], item["layer"]
    for ref in item["required_artifacts"]:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), f"{item['layer']} {ref}"
    for ref in item["paired_test_design_artifacts"]:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), f"{item['layer']} {ref}"
    for ref in item["machine_evidence"]:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), f"{item['layer']} {ref}"
    if item["layer"] == "L2":
        assert item["paired_test_design_artifacts"] == []
        assert item["waiver"]["path"] in item["required_artifacts"]
    else:
        assert item["paired_test_design_artifacts"], item["layer"]
assert payload["completion_denial"]["reason"].startswith(
    "This map proves G1-G6 exit criteria"
)
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 objective coverage audit keeps L7 work feature-ticketed" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-design-asset-inventory.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-full-objective-gap-status.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml" \
"$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml" <<'PY'
import re
import sys
import datetime
from pathlib import Path
from urllib.parse import urlparse
import yaml

PATH_REF_PREFIXES = (
    ".helix/",
    "docs/",
    "cli/",
    "HELIX-workflows/",
    "helix/",
    "skills/",
)
PATH_REF_SUFFIXES = (".md", ".yaml", ".py", ".bats")


def iter_structured_path_refs(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_structured_path_refs(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from iter_structured_path_refs(child)
        return
    if not isinstance(value, str):
        return
    ref = value.strip().strip("\"'`,;()[]")
    if not ref.startswith(PATH_REF_PREFIXES):
        return
    if " " in ref or "\n" in ref or ":" in ref:
        return
    if "*" in ref or ref.endswith(PATH_REF_SUFFIXES):
        yield ref


def iter_markdown_path_refs(text):
    candidates = []
    candidates.extend(match.group(1).strip() for match in re.finditer(r"`([^`]+)`", text))
    candidates.extend(match.group(1).strip() for match in re.finditer(r"\(([^)]+)\)", text))
    for value in candidates:
        ref = value.strip().strip("\"'`,;()[]")
        if not ref.startswith(PATH_REF_PREFIXES):
            continue
        if " " in ref or "\n" in ref or ":" in ref:
            continue
        if "*" in ref or ref.endswith(PATH_REF_SUFFIXES):
            yield ref


path = sys.argv[1]
root = Path(path).resolve().parents[3]
web_path = sys.argv[2]
fr_trace_path = sys.argv[3]
inventory_path = sys.argv[4]
improvement_path = sys.argv[5]
pair_path = sys.argv[6]
guard_path = sys.argv[7]
deferred_coverage_path = sys.argv[8]
db_coverage_path = sys.argv[9]
harness_coverage_path = sys.argv[10]
governance_coverage_path = sys.argv[11]
workflow_coverage_path = sys.argv[12]
db_registration_readiness_path = sys.argv[13]
dependency_impact_readiness_path = sys.argv[14]
bottleneck_remediation_readiness_path = sys.argv[15]
full_objective_gap_status_path = sys.argv[16]
ratification_index_path = sys.argv[17]
exit_criteria_path = sys.argv[18]
reference_integrity_path = sys.argv[19]
double_check_path = sys.argv[20]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)
with open(web_path, encoding="utf-8") as handle:
    web_map = yaml.safe_load(handle)
with open(fr_trace_path, encoding="utf-8") as handle:
    fr_trace = yaml.safe_load(handle)
with open(inventory_path, encoding="utf-8") as handle:
    inventory = yaml.safe_load(handle)
with open(improvement_path, encoding="utf-8") as handle:
    improvement = yaml.safe_load(handle)
with open(pair_path, encoding="utf-8") as handle:
    pair_map = yaml.safe_load(handle)
with open(guard_path, encoding="utf-8") as handle:
    guard_map = yaml.safe_load(handle)
with open(deferred_coverage_path, encoding="utf-8") as handle:
    deferred_coverage = yaml.safe_load(handle)
with open(db_coverage_path, encoding="utf-8") as handle:
    db_coverage = yaml.safe_load(handle)
with open(harness_coverage_path, encoding="utf-8") as handle:
    harness_coverage = yaml.safe_load(handle)
with open(governance_coverage_path, encoding="utf-8") as handle:
    governance_coverage = yaml.safe_load(handle)
with open(workflow_coverage_path, encoding="utf-8") as handle:
    workflow_coverage = yaml.safe_load(handle)
with open(db_registration_readiness_path, encoding="utf-8") as handle:
    db_registration_readiness = yaml.safe_load(handle)
with open(dependency_impact_readiness_path, encoding="utf-8") as handle:
    dependency_impact_readiness = yaml.safe_load(handle)
with open(bottleneck_remediation_readiness_path, encoding="utf-8") as handle:
    bottleneck_remediation_readiness = yaml.safe_load(handle)
with open(full_objective_gap_status_path, encoding="utf-8") as handle:
    full_objective_gap_status = yaml.safe_load(handle)
with open(ratification_index_path, encoding="utf-8") as handle:
    ratification_index = yaml.safe_load(handle)
with open(exit_criteria_path, encoding="utf-8") as handle:
    exit_criteria = yaml.safe_load(handle)
with open(reference_integrity_path, encoding="utf-8") as handle:
    reference_integrity = yaml.safe_load(handle)
with open(double_check_path, encoding="utf-8") as handle:
    double_check = yaml.safe_load(handle)
double_check_boundary_scan = {
    item["id"]: item for item in double_check["qualitative_checks"]
}["L-EVIDENCE-BOUNDARY-SCAN"]["expected"]
legacy_classification = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml").read_text(encoding="utf-8")
)
deferred_design_obligation = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml").read_text(encoding="utf-8")
)
fr18_l6_unit_test_design_index = yaml.safe_load(
    (root / "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml").read_text(encoding="utf-8")
)

assert payload["schema_version"] == "objective_l1_l6_coverage_audit_v1"
assert payload["status"] == "current_scope_l1_l6_closed_not_full_goal"
assert payload["source_objective_matrix"] == "docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml"
assert payload["source_asset_inventory"] == "docs/v2/audit/2026-06-12-l1-l6-design-asset-inventory.yaml"
assert payload["source_improvement_candidate_map"] == "docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml"
assert payload["source_pair_balance_map"] == "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml"
assert payload["source_guard_parity_map"] == "docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml"
assert payload["source_deferred_feature_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml"
assert payload["source_db_feedback_lifecycle_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml"
assert payload["source_harness_external_tools_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml"
assert payload["source_governance_hardening_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml"
assert payload["source_workflow_automation_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml"
assert payload["source_db_registration_readiness_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml"
assert payload["source_dependency_impact_readiness_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml"
assert payload["source_bottleneck_remediation_readiness_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml"
assert payload["source_full_objective_gap_status"] == "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml"
assert payload["source_ratification_index"] == "docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml"
assert payload["source_exit_criteria_map"] == "docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml"
assert payload["source_reference_integrity_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml"
assert payload["source_double_check_coverage_map"] == "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml"
assert payload["source_fr31_trace_map"] == "docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml"
assert payload["source_l1_l6_web_evidence_map"] == "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml"
assert payload["source_l0_l14_flow_surface_coverage"] == "docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml"
assert payload["source_l0_planning_derivation_coverage"] == "docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml"
assert payload["source_legacy_reference_classification"] == "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
assert payload["source_deferred_design_obligation_proof"] == "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml"
assert payload["scope_boundary"]["l7_work_requested_by_user"] is False
assert payload["scope_boundary"]["l7_work_requires_feature_ticket"] is True
assert payload["scope_boundary"]["current_audit_uses_l7_test_design_as_source"] is False
assert payload["scope_boundary"]["l7_implementation_done"] is False
assert payload["scope_boundary"]["external_tool_installed"] is False
assert payload["scope_boundary"]["goal_complete_allowed"] is False
assert payload["objective_clause_trace_policy"] == {
    "objective_clauses_must_have_proof": True,
    "file_path_proofs_must_exist": True,
    "l7_test_design_allowed_as_proof": False,
    "later_phase_boundary_required_for_deferred_status": True,
    "add_feature_plan_allowed_as_current_scope_proof": False,
    "add_feature_plan_allowed_as_later_phase_boundary": True,
    "command_proof_must_be_read_only": True,
    "full_goal_completion_claim_allowed": False,
    "objective_clause_to_full_status_map_required": True,
}
objective_clauses = {item["id"]: item for item in payload["objective_clauses"]}
assert set(objective_clauses) == {
    "OBJ-REQ-GAP-L6",
    "OBJ-GRANULARITY-L1-L6",
    "OBJ-CODEX-CLAUDE-GUARD-PARITY",
    "OBJ-DDD-TDD-AUTO-GOVERNANCE",
    "OBJ-WORKFLOW-AUTOMATION",
    "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6",
    "OBJ-HELIX-DB-FEEDBACK",
    "OBJ-HARNESS-EXTERNAL-TOOLS",
    "OBJ-L0-L14-FLOW",
}
assert "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml" in objective_clauses[
    "OBJ-DDD-TDD-AUTO-GOVERNANCE"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml" in objective_clauses[
    "OBJ-DDD-TDD-AUTO-GOVERNANCE"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml" in objective_clauses[
    "OBJ-WORKFLOW-AUTOMATION"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml" in objective_clauses[
    "OBJ-HELIX-DB-FEEDBACK"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml" in objective_clauses[
    "OBJ-HARNESS-EXTERNAL-TOOLS"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml" in objective_clauses[
    "OBJ-GRANULARITY-L1-L6"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml" in objective_clauses[
    "OBJ-GRANULARITY-L1-L6"
]["proof"]
assert "docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml" in objective_clauses[
    "OBJ-L0-L14-FLOW"
]["proof"]
assert "docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml" in objective_clauses[
    "OBJ-L0-L14-FLOW"
]["proof"]
assert "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml" in objective_clauses[
    "OBJ-L0-L14-FLOW"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml" in objective_clauses[
    "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml" in objective_clauses[
    "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml" in objective_clauses[
    "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
]["proof"]
assert "docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml" in objective_clauses[
    "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
]["proof"]
full_status_ids = {item["id"] for item in full_objective_gap_status["objective_status"]}
full_feature_ticket_path_to_id = {
    item["path"]: item["id"]
    for item in full_objective_gap_status["feature_ticket_boundaries"]
}
full_completion_audit = {
    item["id"]: item
    for item in full_objective_gap_status["completion_audit_matrix"]
}
deferred_by_objective = {
    item["objective_id"]: item
    for item in deferred_coverage["objective_boundary_coverage"]
}
mapping_contract = payload["objective_clause_to_full_status_contract"]
assert mapping_contract == {
    "required_fields": [
        "objective_clause_id",
        "full_objective_status_ids",
        "mapping_reason",
        "current_scope_boundary",
    ],
    "objective_clauses_mapped": 9,
    "full_status_items_checked": 10,
    "full_status_items_without_objective_clause": ["REQ-FULL-GOAL-COMPLETION"],
    "full_status_without_clause_reason": "full_goal_completion_is_a_denial_item_not_a_current_scope_objective_clause",
    "mapping_is_completion_evidence": False,
    "l7_artifact_allowed_as_mapping_proof": False,
}
clause_map = {
    item["objective_clause_id"]: item
    for item in payload["objective_clause_to_full_status_map"]
}
assert set(clause_map) == set(objective_clauses)
assert mapping_contract["objective_clauses_mapped"] == len(clause_map)
mapped_full_status_ids = set()
for clause_id, item in clause_map.items():
    for field in mapping_contract["required_fields"]:
        assert field in item, clause_id
    assert item["full_objective_status_ids"], clause_id
    assert item["mapping_reason"], clause_id
    assert item["current_scope_boundary"], clause_id
    assert not item["current_scope_boundary"].startswith("docs/v2/L7-test-design/")
    assert set(item["full_objective_status_ids"]) <= full_status_ids, clause_id
    source_feature_ids = {
        full_feature_ticket_path_to_id[path]
        for path in deferred_by_objective[clause_id]["feature_entry_points"]
    }
    routed_feature_ids = set().union(
        *(
            set(full_completion_audit[status_id].get("feature_ticket_ids", []))
            for status_id in item["full_objective_status_ids"]
        )
    )
    assert source_feature_ids <= routed_feature_ids, clause_id
    mapped_full_status_ids.update(item["full_objective_status_ids"])
assert full_status_ids - mapped_full_status_ids == set(
    mapping_contract["full_status_items_without_objective_clause"]
)
assert mapping_contract["full_status_items_checked"] == len(full_status_ids)
allowed_read_only_command_prefixes = (
    "helix doctor ",
    "python3 -m pytest ",
    "bats ",
    "find ",
    "python3 -m cli.lib.trace_symmetry ",
)
for clause in objective_clauses.values():
    assert clause["proof"], clause["id"]
    if "deferred" in clause["l1_l6_status"] or "candidate" in clause["l1_l6_status"]:
        assert clause["later_phase_boundary"], clause["id"]
    for proof in clause["proof"]:
        assert not proof.startswith("docs/v2/L7-test-design/"), proof
        assert not proof.startswith("docs/plans/add-feature/"), proof
        if proof.startswith(allowed_read_only_command_prefixes):
            continue
        assert (root / proof).exists(), proof
assert payload["current_l1_l6_evidence"]["l0_l14_contract"]["pytest_expected"] == "87 passed"
assert payload["current_l1_l6_evidence"]["l0_l14_contract"]["bats_expected"] == "56 tests passed"
assert payload["current_l1_l6_evidence"]["l0_planning_derivation"]["expected"] == {
    "l0_problem_axes_checked": 10,
    "l0_problem_axes_with_l1_l6_design_evidence": 10,
    "problem_axis_rows_with_mapped_requirements": 10,
    "problem_axis_rows_with_l4_l6_design_evidence": 10,
    "problem_axis_rows_with_audit_evidence": 10,
    "l0_target_areas_checked": 10,
    "l0_target_areas_with_l1_l6_design_evidence": 10,
    "target_area_rows_with_current_scope_evidence": 10,
    "rows_with_current_scope_result": 20,
    "l0_to_l1_l6_derivation_gaps": 0,
    "l1_l6_audit_sources_declared": 13,
    "row_audit_refs_checked": 32,
    "unique_row_audit_refs_checked": 11,
    "undeclared_row_audit_refs": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"] == {
    "fr_count": 18,
    "specs_current_scope_l6_closed": 18,
    "specs_with_l6_unit_test_design_viewpoints": 18,
    "total_ut_candidates": 128,
    "specs_with_draft_status": [],
    "l7_unit_test_design_artifacts_created": False,
}
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["fr_count"] == fr18_l6_unit_test_design_index["coverage_summary"]["fr_count"]
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["specs_current_scope_l6_closed"] == fr18_l6_unit_test_design_index["coverage_summary"]["specs_current_scope_l6_closed"]
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["specs_with_l6_unit_test_design_viewpoints"] == fr18_l6_unit_test_design_index["coverage_summary"]["specs_with_l6_unit_test_design_viewpoints"]
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["total_ut_candidates"] == fr18_l6_unit_test_design_index["coverage_summary"]["total_ut_candidates"]
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["specs_with_draft_status"] == fr18_l6_unit_test_design_index["coverage_summary"]["specs_with_draft_status"]
assert payload["current_l1_l6_evidence"]["l6_unit_test_design_viewpoints"]["expected"]["l7_unit_test_design_artifacts_created"] == fr18_l6_unit_test_design_index["boundary"]["l7_unit_test_design_artifacts_created"]
assert payload["current_l1_l6_evidence"]["l7_non_execution_check"] == {
    "command": "find docs/v2/L7-test-design \\( -path '*/FR-FNREG-01/*' -o -path '*/FR-GLOSSARY-01/*' \\) -print",
    "expected_stdout": "",
    "evidence_kind": "negative_boundary_check",
    "proves_l7_execution": False,
    "proves_l7_test_design_creation": False,
    "counts_as_current_scope_completion_proof": False,
}
assert payload["current_l1_l6_evidence"]["asset_inventory"]["expected"] == {
    "total_l1_l6_files": 50,
    "l6_functional_design_files": 28,
    "l6_assets_partitioned": True,
    "l6_partition_overlap_allowed": False,
    "l6_partition_clusters": 3,
    "inventory_uses_l7_as_execution_evidence": False,
}
assert payload["current_l1_l6_evidence"]["improvement_candidates"]["expected"] == {
    "total_candidates": 35,
    "uses_l7_test_design_as_source": False,
    "candidates_adopted": False,
}
assert payload["current_l1_l6_evidence"]["pair_balance"]["expected"] == {
    "l1_l6_layers_checked": 6,
    "layers_pass": 6,
    "blocking_findings": 0,
    "pair_contract_matrix_layers_checked": 6,
    "paired_artifacts_checked": 6,
    "expected_design_refs_checked": 8,
    "expected_design_refs_backed_by_design_assets": 8,
    "expected_design_refs_missing_from_design_assets": 0,
    "uses_l7_artifact_as_current_scope_evidence": False,
}
assert payload["current_l1_l6_evidence"]["guard_parity"]["expected"] == {
    "guard_surfaces": 8,
    "parity_status_policies_checked": 5,
    "codex_runtime_evidence_surfaces": 3,
    "l6_design_only_surfaces": 3,
    "parity_gap_routes_checked": 8,
    "parity_route_required_fields_checked": 7,
    "parity_finding_normalization_contracts_checked": 8,
    "parity_normalization_required_fields_checked": 8,
    "parity_closure_requirements_checked": 8,
    "parity_closure_required_fields_checked": 6,
    "parity_accountability_current_scope_proves_checked": 4,
    "parity_accountability_current_scope_does_not_prove_checked": 4,
    "parity_classification_rules_checked": 4,
    "parity_adoption_requirements_checked": 4,
    "parity_map_is_closure": False,
}
assert payload["current_l1_l6_evidence"]["deferred_feature_coverage"]["expected"] == {
    "objective_clauses_checked": 9,
    "deferred_entry_points_checked": 11,
    "feature_tickets_checked": 11,
    "feature_tickets_draft": 11,
    "feature_tickets_with_approval_boundary": 11,
    "feature_tickets_with_unlock_conditions": 11,
    "repository_add_feature_files_discovered": 24,
    "current_objective_deferred_feature_tickets": 11,
    "out_of_current_objective_add_feature_files": 13,
    "out_of_current_objective_completed_add_features": 4,
    "out_of_current_objective_parked_feature_tickets": 0,
    "full_flow_later_phase_approval_boundary": True,
    "unmapped_deferred_boundaries": 0,
    "l7_artifacts_created_by_this_audit": 0,
    "l5_l6_add_design_feature_tickets_checked": 1,
    "contract_design_phase_label_retrofit": {
        "kind": "add-design",
        "layer": "L5-L6",
        "approval_required_before_contract_edit": True,
        "current_scope_action": "record_boundary_only_no_contract_edit",
        "contract_edit_performed": False,
        "schema_migration_done": False,
        "l7_work_performed": False,
    },
}
assert payload["current_l1_l6_evidence"]["deferred_feature_coverage"]["expected"][
    "objective_clauses_checked"
] == len(objective_clauses)
assert payload["current_l1_l6_evidence"]["deferred_design_obligation_proof"]["expected"] == {
    "feature_tickets_checked": 11,
    "feature_tickets_with_prior_l1_l6_design_evidence": 11,
    "feature_tickets_using_ticket_as_design_substitute": 0,
    "design_gap_reopen_rules_defined": 11,
    "escalation_bound_design_tickets_checked": 2,
    "implementation_or_execution_tickets_checked": 9,
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
assert payload["current_l1_l6_evidence"]["deferred_design_obligation_proof"]["expected"][
    "feature_tickets_checked"
] == deferred_design_obligation["summary"]["feature_tickets_checked"]
assert payload["current_l1_l6_evidence"]["deferred_design_obligation_proof"]["expected"][
    "feature_tickets_using_ticket_as_design_substitute"
] == deferred_design_obligation["summary"]["feature_tickets_using_ticket_as_design_substitute"]
assert payload["current_l1_l6_evidence"]["db_feedback_lifecycle"]["expected"] == {
    "design_layers_checked": 3,
    "physical_db_design_checked": 1,
    "lifecycle_states_defined": 8,
    "closure_rules_defined": 4,
    "l6_functions_defined": 8,
    "existing_tables_required_for_lifecycle_checked": 9,
    "forbidden_current_scope_rules_checked": 4,
    "schema_migration_done": False,
    "db_write_connection_done": False,
    "feedback_lifecycle_accountability_contract_present": True,
    "feature_ticket_is_not_design_substitute": True,
    "db_write_requires_explicit_approval": True,
    "current_scope_must_keep_db_write_false": True,
    "recurrence_closure_requires_later_execution_evidence": True,
}
db_feedback_expected = payload["current_l1_l6_evidence"]["db_feedback_lifecycle"]["expected"]
db_feedback_accountability = db_coverage["feedback_lifecycle_accountability_contract"]
assert db_feedback_expected["feedback_lifecycle_accountability_contract_present"] is True
assert db_feedback_expected["feature_ticket_is_not_design_substitute"] == (
    db_feedback_accountability["feature_ticket_is_not_design_substitute"]
)
assert db_feedback_expected["db_write_requires_explicit_approval"] == (
    db_feedback_accountability["db_write_requires_explicit_approval"]
)
assert db_feedback_expected["current_scope_must_keep_db_write_false"] == (
    db_feedback_accountability["current_scope_must_keep_db_write_false"]
)
assert db_feedback_expected["recurrence_closure_requires_later_execution_evidence"] == (
    db_feedback_accountability["recurrence_closure_requires_later_execution_evidence"]
)
assert db_feedback_expected["closure_rules_defined"] == len(
    db_coverage["state_machine"]["closure_rules"]
)
assert db_feedback_expected["existing_tables_required_for_lifecycle_checked"] == len(
    db_coverage["physical_db_design_evidence"]["existing_tables_required_for_lifecycle"]
)
assert db_feedback_expected["forbidden_current_scope_rules_checked"] == len(
    db_coverage["storage_mapping_policy"]["forbidden_current_scope"]
)
assert payload["current_l1_l6_evidence"]["harness_external_tools"]["expected"] == {
    "official_sources_checked": 33,
    "tool_candidates_checked": 33,
    "tool_intake_contracts_checked": 33,
    "tool_intake_required_fields_checked": 9,
    "tool_intake_forbidden_common_rules_checked": 7,
    "admission_gate_contracts_checked": 5,
    "admission_gate_required_fields_checked": 7,
    "admission_owner_roles_checked": 3,
    "tool_output_ingestion_contracts_checked": 33,
    "tool_output_required_fields_checked": 8,
    "tool_output_detector_signals_checked": 5,
    "l6_functions_defined": 10,
    "l6_unit_test_viewpoints_defined": 10,
    "adoption_recheck_controls_checked": 3,
    "pre_adoption_requirement_contracts_checked": 5,
    "current_session_web_fetch_sources_checked": 5,
    "current_session_web_fetch_refs_checked": 10,
    "latest_core_rechecked_sources_checked": 5,
    "all_candidate_sources_checked": 33,
    "spot_recheck_sources_checked": 8,
    "adoption_control_sources_are_subset_of_latest_core_rechecked_sources": True,
    "adoption_control_sources_are_subset_of_spot_recheck_sources": True,
    "all_candidate_source_ids_must_match_canonical_source_ids": True,
    "spot_recheck_sources_are_subset_of_canonical_source_ids": True,
    "spot_recheck_is_not_full_candidate_recheck": True,
    "harness_tool_accountability_contract_present": True,
    "accountability_current_scope_proves_checked": 5,
    "accountability_current_scope_does_not_prove_checked": 8,
    "web_evidence_is_design_basis_not_adoption": True,
    "current_scope_must_keep_install_execution_ci_db_false": True,
    "l7_work_requires_feature_ticket": True,
    "external_tool_installed": False,
}
harness_expected = payload["current_l1_l6_evidence"]["harness_external_tools"]["expected"]
harness_payload = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml").read_text(encoding="utf-8")
)
harness_accountability = harness_payload["harness_tool_accountability_contract"]
assert harness_expected["harness_tool_accountability_contract_present"] is True
assert harness_expected["web_evidence_is_design_basis_not_adoption"] == (
    harness_accountability["web_evidence_is_design_basis_not_adoption"]
)
assert harness_expected["current_scope_must_keep_install_execution_ci_db_false"] == (
    harness_accountability["current_scope_must_keep_install_execution_ci_db_false"]
)
assert harness_expected["l7_work_requires_feature_ticket"] == (
    harness_accountability["l7_work_requires_feature_ticket"]
)
assert payload["current_l1_l6_evidence"]["governance_hardening"]["expected"] == {
    "governance_surfaces_checked": 8,
    "l6_function_contracts_checked": 53,
    "current_scope_l6_ut_candidate_viewpoints": 44,
    "governance_finding_normalization_contracts_checked": 6,
    "governance_normalization_required_fields_checked": 7,
    "documentation_readiness_gap_patterns_checked": 7,
    "governance_controls_checked": 6,
    "governance_detection_required_route_fields_checked": 7,
    "governance_detection_routes_checked": 6,
    "governance_control_trace_rows_checked": 6,
    "governance_control_closure_rows_checked": 6,
    "preexisting_completed_feature_entry_points_checked": 3,
    "deferred_feature_entry_points_checked": 4,
    "new_l7_implementation_done": False,
    "fail_close_promotion_done": False,
}
assert payload["current_l1_l6_evidence"]["workflow_automation"]["expected"] == {
    "workflow_surfaces_checked": 6,
    "automation_surfaces_checked": 9,
    "automation_trigger_contracts_checked": 9,
    "db_registry_targets_mapped": 9,
    "detector_gate_routes_mapped": 7,
    "cross_audit_convergence_rows_checked": 6,
    "deferred_feature_entry_points_checked": 7,
    "parked_feature_entry_points_checked": 0,
    "right_arm_execution_gate_implementation_done": False,
    "ci_or_equivalent_connected": False,
}
assert payload["current_l1_l6_evidence"]["db_registration_readiness"]["expected"] == {
    "registration_events_checked": 6,
    "registration_event_contracts_checked": 6,
    "document_projection_contracts_checked": 5,
    "lifecycle_route_contracts_checked": 6,
    "existing_implementation_surfaces_checked": 8,
    "l1_l6_design_surfaces_checked": 3,
    "add_feature_import_targets_checked": 11,
    "event_route_closure_rows_checked": 6,
    "l7_feature_tickets_created": 1,
    "plan_registry_changed_by_this_audit": False,
    "helix_db_write_performed": False,
    "registration_accountability_contract_present": True,
    "feature_ticket_is_not_design_substitute": True,
    "db_write_requires_explicit_approval": True,
    "current_scope_must_keep_db_write_false": True,
}
db_registration_expected = payload["current_l1_l6_evidence"]["db_registration_readiness"]["expected"]
db_registration_accountability = db_registration_readiness["registration_accountability_contract"]
assert db_registration_expected["registration_accountability_contract_present"] is True
assert db_registration_expected["feature_ticket_is_not_design_substitute"] == (
    db_registration_accountability["feature_ticket_is_not_design_substitute"]
)
assert db_registration_expected["db_write_requires_explicit_approval"] == (
    db_registration_accountability["db_write_requires_explicit_approval"]
)
assert db_registration_expected["current_scope_must_keep_db_write_false"] == (
    db_registration_accountability["current_scope_must_keep_db_write_false"]
)
assert payload["current_l1_l6_evidence"]["dependency_impact_readiness"]["expected"] == {
    "dependency_impact_surfaces_checked": 7,
    "l6_function_specs_checked": 6,
    "current_code_surfaces_checked_read_only": 5,
    "deferred_feature_entry_points_checked": 4,
    "required_output_sections": 9,
    "db_projection_contracts_checked": 5,
    "dependency_edge_relations_checked": 7,
    "impact_scope_route_contracts_checked": 3,
    "unknown_scope_resolution_rules_checked": 6,
    "impact_visibility_rows_checked": 9,
    "impact_output_trace_rows_checked": 9,
    "impact_query_cli_implemented": False,
    "helix_db_write_performed": False,
}
output_trace = {
    item["required_output_section"]: item
    for item in dependency_impact_readiness["impact_query_output_contract_trace"]
}
assert set(output_trace) == set(dependency_impact_readiness["required_output_contract"])
surfaces = {
    item["id"]: item
    for item in dependency_impact_readiness["coverage_surfaces"]
}
assert dependency_impact_readiness["summary"]["dependency_impact_surfaces_checked"] == len(surfaces)
assert dependency_impact_readiness["summary"]["l6_function_specs_checked"] == len(
    dependency_impact_readiness["sources"]["l6_function_specs"]
)
assert dependency_impact_readiness["summary"]["current_code_surfaces_checked_read_only"] == len(
    dependency_impact_readiness["sources"]["current_code_surfaces_read_only"]
)
assert dependency_impact_readiness["summary"]["deferred_feature_entry_points_checked"] == len(
    dependency_impact_readiness["sources"]["deferred_feature_entry_points"]
)
assert dependency_impact_readiness["summary"]["required_output_sections"] == len(
    dependency_impact_readiness["required_output_contract"]
)
assert all(value == "required" for value in dependency_impact_readiness["required_output_contract"].values())
projection_contract = dependency_impact_readiness["db_projection_contract"]
assert projection_contract["current_scope_action"] == "define_projection_contract_only"
assert projection_contract["db_write_done"] is False
assert projection_contract["schema_migration_done"] is False
assert projection_contract["query_cli_done"] is False
assert projection_contract["projection_is_completion_evidence"] is False
projections = {
    item["projection_id"]: item
    for item in projection_contract["projections"]
}
assert dependency_impact_readiness["summary"]["db_projection_contracts_checked"] == len(projections)
assert set(projections) == {
    "impact_seed",
    "impact_affected_artifacts",
    "impact_dependency_edges",
    "impact_gate_refs",
    "impact_feedback_refs",
}
assert {item["db_target"] for item in projections.values()} == {
    "detector_report",
    "gate_projection",
    "dependency_edges",
    "feedback_event",
}
output_sections = set(dependency_impact_readiness["required_output_contract"])
for projection in projections.values():
    source_sections = projection["source_output_section"]
    if isinstance(source_sections, str):
        source_sections = [source_sections]
    assert set(source_sections) <= output_sections, projection["projection_id"]
    assert projection["key_fields"], projection["projection_id"]
    assert projection["purpose"], projection["projection_id"]
assert dependency_impact_readiness["dependency_edge_contract"] == {
    "required_edge_fields": ["source", "target", "relation", "confidence"],
    "allowed_relations": [
        "trace",
        "dependency",
        "generates",
        "parent",
        "blocks",
        "evidence",
        "tool_finding",
    ],
    "allowed_confidence": ["high", "medium", "low"],
    "direction_required": True,
    "unknown_scope_policy": "unknown_must_route_to_manual_review",
    "closure_policy": "edge_presence_is_not_closure",
}
assert dependency_impact_readiness["summary"]["dependency_edge_relations_checked"] == len(
    dependency_impact_readiness["dependency_edge_contract"]["allowed_relations"]
)
scope_route_policy = dependency_impact_readiness["impact_scope_route_policy"]
assert scope_route_policy == {
    "current_scope_action": "define_scope_route_contract_only",
    "query_cli_done": False,
    "db_write_done": False,
    "route_auto_execute_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "allowed_verdicts": ["local", "broad", "unknown"],
    "allowed_modes": [
        "add-feature",
        "refactor",
        "retrofit",
        "reverse",
        "manual_review",
    ],
    "allowed_owner_roles": ["TL", "QA", "DevOps", "Security"],
    "allowed_priority_floor": ["P1", "P2", "P3"],
    "required_contract_fields": [
        "verdict",
        "trigger_condition",
        "owner_role",
        "priority_floor",
        "next_route",
        "required_evidence_before_execution",
        "completion_boundary",
    ],
}
scope_routes = {
    item["verdict"]: item
    for item in dependency_impact_readiness["impact_scope_route_contracts"]
}
assert set(scope_routes) == set(scope_route_policy["allowed_verdicts"])
assert dependency_impact_readiness["summary"]["impact_scope_route_contracts_checked"] == len(
    scope_routes
)
for verdict, route in scope_routes.items():
    for field in scope_route_policy["required_contract_fields"]:
        assert field in route, verdict
    assert route["owner_role"] in scope_route_policy["allowed_owner_roles"]
    assert route["priority_floor"] in scope_route_policy["allowed_priority_floor"]
    assert route["required_evidence_before_execution"], verdict
    assert route["completion_boundary"].endswith(("not_closure", "not_execution"))
assert scope_routes["local"]["priority_floor"] == "P3"
assert scope_routes["broad"]["priority_floor"] == "P1"
assert scope_routes["unknown"]["next_route"] == "route_to_manual_review_or_reverse"
unknown_contract = dependency_impact_readiness["unknown_scope_resolution_contract"]
assert unknown_contract["current_scope_action"] == "define_unknown_resolution_only"
assert unknown_contract["unknown_is_current_scope_blocker"] is False
assert unknown_contract["unknown_is_completion_evidence"] is False
assert unknown_contract["unknown_can_be_silently_local"] is False
assert unknown_contract["query_cli_done"] is False
assert unknown_contract["db_write_done"] is False
assert unknown_contract["l7_artifact_allowed_now"] is False
resolution_rules = {item["rule"]: item for item in unknown_contract["resolution_rules"]}
assert set(resolution_rules) == {
    "preserve_unknown_verdict",
    "require_manual_owner",
    "expose_missing_edges",
    "deny_auto_execution",
    "separate_review_from_closure",
    "route_implementation_to_feature",
}
assert dependency_impact_readiness["summary"]["unknown_scope_resolution_rules_checked"] == len(
    resolution_rules
)
assert resolution_rules["require_manual_owner"]["evidence_source"] == (
    "impact_scope_route_contracts.required_evidence_before_execution"
)
assert resolution_rules["route_implementation_to_feature"]["evidence_source"] == (
    "sources.deferred_feature_entry_points"
)
visibility_contract = dependency_impact_readiness["impact_visibility_closure_contract"]
assert visibility_contract["current_scope_action"] == "prove_output_projection_route_alignment_only"
assert visibility_contract["output_sections_checked"] == len(output_sections)
assert visibility_contract["db_write_done"] is False
assert visibility_contract["query_cli_done"] is False
assert visibility_contract["route_auto_execute_allowed_now"] is False
assert visibility_contract["l7_or_adoption_evidence_allowed"] is False
assert visibility_contract["alignment_rules"] == {
    "every_required_output_section_has_row": True,
    "every_projection_source_section_has_row": True,
    "every_route_required_evidence_links_to_output_sections": True,
    "completion_boundary_is_guard_only": True,
}
visibility_rows = {item["output_section"]: item for item in visibility_contract["rows"]}
assert dependency_impact_readiness["summary"]["impact_visibility_rows_checked"] == len(
    visibility_rows
)
assert set(visibility_rows) == output_sections
projection_sections = set()
for projection in projections.values():
    source_sections = projection["source_output_section"]
    if isinstance(source_sections, str):
        source_sections = [source_sections]
    projection_sections.update(source_sections)
assert projection_sections <= set(visibility_rows)
route_aliases = visibility_contract["route_evidence_aliases"]
for verdict, route in scope_routes.items():
    for evidence_key in route["required_evidence_before_execution"]:
        assert evidence_key in route_aliases, (verdict, evidence_key)
        assert set(route_aliases[evidence_key]) <= output_sections
for output_section, row in visibility_rows.items():
    assert set(row["route_verdicts"]) <= set(scope_routes)
    assert row["visibility_purpose"], output_section
    if output_section == "completion_boundary":
        assert row["projection_ids"] == []
    else:
        assert row["projection_ids"], output_section
    for projection_id in row["projection_ids"]:
        assert projection_id in projections, (output_section, projection_id)
assert len(output_trace) == dependency_impact_readiness["summary"]["required_output_sections"]
assert dependency_impact_readiness["summary"]["impact_output_trace_rows_checked"] == len(output_trace)
output_paths = [
    item["l6_output_path"]
    for item in dependency_impact_readiness["impact_query_output_contract_trace"]
]
assert len(output_paths) == len(set(output_paths))
assert all(path.startswith("impact_query_result.") for path in output_paths)
impact_spec_path = root / "docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md"
impact_spec = impact_spec_path.read_text(encoding="utf-8")
output_path_terms = {
    "impact_query_result.seed": ("impact_query_result:", "seed:"),
    "impact_query_result.affected.plans": ("affected:", "plans:"),
    "impact_query_result.affected.design_docs": ("affected:", "design_docs:"),
    "impact_query_result.affected.test_design_docs": ("affected:", "test_design_docs:"),
    "impact_query_result.affected.code_paths": ("affected:", "code_paths:"),
    "impact_query_result.affected.gates": ("affected:", "gates:"),
    "impact_query_result.dependency_edges": ("dependency_edges:",),
    "impact_query_result.affected.feedback_refs": ("affected:", "feedback_refs:"),
    "impact_query_result.completion": (
        "completion:",
        "query_result_is_goal_completion: false",
    ),
}
for section, row in output_trace.items():
    assert row["l6_spec_ref"] == "docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md"
    assert row["current_scope_status"] == "l6_design_only_not_cli"
    for term in output_path_terms[row["l6_output_path"]]:
        assert term in impact_spec, section
assert "source -> target -> relation -> confidence" in impact_spec
deferred_plans = set(dependency_impact_readiness["sources"]["deferred_feature_entry_points"])
assert all(plan.startswith("docs/plans/add-feature/") for plan in deferred_plans)
for surface in surfaces.values():
    surface_text = (root / surface["artifact"]).read_text(encoding="utf-8")
    assert surface["design_status"] == "current_scope_l6_design"
    assert surface["current_scope_result"]
    assert surface["deferred_feature_plan"] in deferred_plans
    for function_ref in surface["covered_functions"]:
        token = function_ref.split()[0]
        assert token in surface_text, f"{surface['id']} missing {token}"
for refs in dependency_impact_readiness["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for ref in dependency_impact_readiness["sources"]["current_code_surfaces_read_only"]:
    assert ref.startswith("cli/lib/"), ref
    assert (root / ref).exists(), ref
assert payload["current_l1_l6_evidence"]["bottleneck_remediation_readiness"]["expected"] == {
    "bottleneck_signal_sources_checked": 7,
    "l6_function_specs_checked": 5,
    "remediation_flow_states_defined": 7,
    "forbidden_current_scope_states_checked": 2,
    "required_signal_fields_checked": 8,
    "cross_axis_aggregation_contracts_checked": 4,
    "signal_route_contracts_checked": 7,
    "current_code_surfaces_checked_read_only": 5,
    "deferred_feature_entry_points_checked": 4,
    "deferred_feature_boundaries_checked": 4,
    "required_output_sections": 8,
    "bottleneck_detector_implemented_by_this_audit": False,
    "remediation_auto_apply_done": False,
}
assert payload["current_l1_l6_evidence"]["full_objective_gap_status"]["expected"] == {
    "objective_items_checked": 10,
    "current_scope_items_pass_l1_l6": 9,
    "items_requiring_later_phase_before_full_completion": 8,
    "feature_tickets_available": 11,
    "repository_add_feature_files_discovered": 24,
    "current_objective_deferred_feature_tickets": 11,
    "out_of_current_objective_add_feature_files": 13,
    "out_of_current_objective_completed_add_features": 4,
    "out_of_current_objective_parked_feature_tickets": 0,
    "right_arm_execution_gates_deferred": 4,
    "current_scope_verdict": "pass_l1_l6_only",
    "full_goal_verdict": "active_not_complete",
    "full_goal_complete": False,
    "harness_external_tool_accountability_indexed": True,
    "unlock_evidence_namespace": "full_goal_unlock_required_evidence_not_current_scope_proof",
    "required_evidence_is_current_scope_proof": False,
    "required_evidence_is_completion_evidence_now": False,
    "required_feature_ticket_is_completion_evidence": False,
    "may_satisfy_completion_only_after_approval_and_execution": True,
    "l1_l6_design_obligation_is_current_scope": True,
    "deferred_feature_tickets_are_not_design_substitute": True,
    "feature_ticket_allowed_only_for_unapproved_l7_or_escalation_bound_execution": True,
    "no_feature_escape_for_design_debt": True,
    "db_feedback_accountability_indexed": True,
    "db_registration_accountability_indexed": True,
    "repository_add_feature_inventory_indexed": True,
    "repository_add_feature_inventory_allows_l7_work": False,
}
assert payload["current_l1_l6_evidence"]["full_objective_gap_status"]["expected"][
    "objective_items_checked"
] == len(full_objective_gap_status["objective_status"])
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"] == {
    "current_scope_verdict": "pass_l1_l6_only",
    "full_goal_verdict": "active_not_complete",
    "core_audit_bundle_files_indexed": 23,
    "integrity_audits_indexed": 2,
    "double_check_quantitative_checks_pass": 21,
    "double_check_qualitative_checks_pass": 36,
    "evidence_boundary_scan_evidence_like_keys_checked": 11,
    "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence": 0,
    "evidence_boundary_scan_current_scope_proof_allows_add_feature": False,
    "evidence_boundary_scan_current_scope_proof_allows_l7_test_design": False,
    "l0_problem_axes_checked": 10,
    "l0_problem_axes_with_l1_l6_design_evidence": 10,
    "l0_problem_axis_rows_with_mapped_requirements": 10,
    "l0_problem_axis_rows_with_l4_l6_design_evidence": 10,
    "l0_problem_axis_rows_with_audit_evidence": 10,
    "l0_target_areas_checked": 10,
    "l0_target_areas_with_l1_l6_design_evidence": 10,
    "l0_target_area_rows_with_current_scope_evidence": 10,
    "l0_rows_with_current_scope_result": 20,
    "guard_parity_gap_routes_checked": 8,
    "guard_parity_route_required_fields_checked": 7,
    "parity_finding_normalization_contracts_checked": 8,
    "guard_parity_normalization_required_fields_checked": 8,
    "parity_closure_requirements_checked": 8,
    "guard_parity_closure_required_fields_checked": 6,
    "harness_external_tool_adoption_recheck_controls_checked": 3,
    "harness_external_tool_pre_adoption_requirement_contracts_checked": 5,
    "harness_external_tool_current_session_web_fetch_sources_checked": 5,
    "harness_external_tool_latest_core_rechecked_sources_checked": 5,
    "harness_external_tool_all_candidate_sources_checked": 33,
    "harness_external_tool_spot_recheck_sources_checked": 8,
    "harness_external_tool_spot_recheck_subset_of_canonical": True,
    "harness_external_tool_spot_recheck_not_full_candidate_recheck": True,
    "harness_external_tool_scope_contract_l7_artifact_allowed": False,
    "harness_external_tool_tool_candidates_checked": 33,
    "harness_external_tool_intake_contracts_checked": 33,
    "harness_external_tool_tool_intake_required_fields_checked": 9,
    "harness_external_tool_tool_intake_forbidden_common_rules_checked": 7,
    "harness_external_tool_admission_gate_contracts_checked": 5,
    "harness_external_tool_admission_gate_required_fields_checked": 7,
    "harness_external_tool_admission_owner_roles_checked": 3,
    "harness_external_tool_output_ingestion_contracts_checked": 33,
    "harness_external_tool_tool_output_required_fields_checked": 8,
    "harness_external_tool_tool_output_detector_signals_checked": 5,
    "harness_external_tool_accountability_indexed": True,
    "harness_external_tool_current_session_web_fetch_refs_checked": 10,
    "harness_external_tool_accountability_current_scope_proves_checked": 5,
    "harness_external_tool_accountability_current_scope_does_not_prove_checked": 8,
    "harness_external_tool_web_evidence_is_design_basis_not_adoption": True,
    "harness_external_tool_current_scope_must_keep_install_execution_ci_db_false": True,
    "harness_external_tool_l7_work_requires_feature_ticket": True,
    "harness_external_tool_adoption_or_execution_allowed_now": False,
    "harness_external_tool_db_write_allowed_now": False,
    "harness_external_tool_ci_or_equivalent_connection_allowed_now": False,
    "l1_l6_design_layers_ratified": 6,
    "l1_l6_pair_layers_ratified": 6,
    "deferred_feature_tickets_indexed": 11,
    "deferred_feature_unlock_conditions_checked": 11,
    "deferred_repository_add_feature_files_discovered": 24,
    "deferred_current_objective_deferred_feature_tickets": 11,
    "deferred_out_of_current_objective_add_feature_files": 13,
    "deferred_out_of_current_objective_completed_add_features": 4,
    "deferred_out_of_current_objective_parked_feature_tickets": 0,
    "deferred_design_obligation_rows_checked": 11,
    "deferred_design_obligation_escape_findings": 0,
    "legacy_runtime_retrofit_required_items": 1,
    "legacy_runtime_metadata_gap_ticketed": True,
    "legacy_runtime_feature_ticket_metadata_match_required": True,
    "legacy_runtime_next_action_supersedes_current_json_metadata": True,
    "legacy_runtime_safe_task_retitle_command_available_now": False,
    "legacy_handover_metadata_boundary_items_checked": 1,
    "legacy_handover_current_json_l7_label_authorizes_work": False,
    "legacy_handover_ready_for_review_status_not_completion": True,
    "legacy_handover_next_action_is_authoritative": True,
    "full_goal_unlock_evidence_classes_indexed": 8,
    "full_goal_unlock_required_feature_tickets_resolved": 8,
    "right_arm_execution_gates_deferred": 4,
    "l1_l6_design_obligation_is_current_scope": True,
    "deferred_feature_tickets_are_not_design_substitute": True,
    "no_feature_escape_for_design_debt": True,
    "dependency_impact_db_projection_contracts_checked": 5,
    "dependency_impact_dependency_edge_relations_checked": 7,
    "dependency_impact_visibility_rows_checked": 9,
    "dependency_impact_output_trace_rows_checked": 9,
    "db_feedback_accountability_indexed": True,
    "db_feedback_feature_ticket_is_not_design_substitute": True,
    "db_feedback_db_write_requires_explicit_approval": True,
    "db_feedback_current_scope_must_keep_db_write_false": True,
    "db_feedback_recurrence_closure_requires_later_execution_evidence": True,
    "db_feedback_closure_rules_defined": 4,
    "db_feedback_existing_tables_required_for_lifecycle_checked": 9,
    "db_feedback_forbidden_current_scope_rules_checked": 4,
    "db_feedback_schema_migration_done": False,
    "db_feedback_db_write_connection_done": False,
    "db_registration_accountability_indexed": True,
    "db_registration_feature_ticket_is_not_design_substitute": True,
    "db_registration_db_write_requires_explicit_approval": True,
    "db_registration_current_scope_must_keep_db_write_false": True,
    "db_registration_plan_registry_changed_by_this_audit": False,
    "db_registration_helix_db_write_performed": False,
    "db_registration_schema_migration_done": False,
    "l7_artifacts_created_by_this_index": 0,
    "full_objective_objective_items_checked": 10,
    "full_objective_current_scope_items_pass_l1_l6": 9,
    "full_objective_items_requiring_later_phase_before_full_completion": 8,
    "full_objective_feature_tickets_available": 11,
    "full_objective_repository_add_feature_files_discovered": 24,
    "full_objective_current_objective_deferred_feature_tickets": 11,
    "full_objective_out_of_current_objective_add_feature_files": 13,
    "full_objective_out_of_current_objective_completed_add_features": 4,
    "full_objective_out_of_current_objective_parked_feature_tickets": 0,
    "full_objective_right_arm_execution_gates_deferred": 4,
    "full_objective_blocking_findings_current_l1_l6_scope": 0,
    "full_objective_blocking_findings_full_goal": 8,
    "full_objective_current_scope_verdict": "pass_l1_l6_only",
    "full_objective_full_goal_verdict": "active_not_complete",
}
runtime_retrofit = legacy_classification["runtime_retrofit_required"][0]
handover_boundary = legacy_classification["handover_metadata_boundary"][0]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_runtime_retrofit_required_items"
] == ratification_index["ratification_summary"][
    "legacy_runtime_retrofit_required_items"
] == legacy_classification["summary"]["runtime_retrofit_required_items"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "evidence_boundary_scan_evidence_like_keys_checked"
] == ratification_index["ratification_summary"][
    "evidence_boundary_scan_evidence_like_keys_checked"
] == len(double_check_boundary_scan["evidence_like_keys_checked"])
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
] == ratification_index["ratification_summary"][
    "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
] == double_check_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "evidence_boundary_scan_current_scope_proof_allows_add_feature"
] == ratification_index["ratification_summary"][
    "evidence_boundary_scan_current_scope_proof_allows_add_feature"
] == double_check_boundary_scan["current_scope_proof_allows_add_feature"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
] == ratification_index["ratification_summary"][
    "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
] == double_check_boundary_scan["current_scope_proof_allows_l7_test_design"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_runtime_metadata_gap_ticketed"
] == ratification_index["ratification_summary"][
    "legacy_runtime_metadata_gap_ticketed"
] is bool(runtime_retrofit["observed_metadata_gap"])
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_runtime_feature_ticket_metadata_match_required"
] == ratification_index["ratification_summary"][
    "legacy_runtime_feature_ticket_metadata_match_required"
] == runtime_retrofit["feature_ticket_metadata_must_match_observed_gap"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_runtime_next_action_supersedes_current_json_metadata"
] == ratification_index["ratification_summary"][
    "legacy_runtime_next_action_supersedes_current_json_metadata"
] == runtime_retrofit["observed_metadata_gap"][
    "next_action_supersedes_current_json_task_metadata"
]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_handover_metadata_boundary_items_checked"
] == ratification_index["ratification_summary"][
    "legacy_handover_metadata_boundary_items_checked"
] == legacy_classification["summary"]["handover_metadata_boundary_items_checked"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_handover_current_json_l7_label_authorizes_work"
] == ratification_index["ratification_summary"][
    "legacy_handover_current_json_l7_label_authorizes_work"
] == legacy_classification["summary"]["handover_current_json_l7_label_authorizes_work"]
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_handover_next_action_is_authoritative"
] == ratification_index["ratification_summary"][
    "legacy_handover_next_action_is_authoritative"
] == legacy_classification["summary"]["handover_next_action_is_authoritative"]
assert handover_boundary["authoritative_boundary"]["l7_work_requested_by_user"] is False
assert payload["current_l1_l6_evidence"]["ratification_index"]["expected"][
    "legacy_runtime_safe_task_retitle_command_available_now"
] == ratification_index["ratification_summary"][
    "legacy_runtime_safe_task_retitle_command_available_now"
] == runtime_retrofit["observed_metadata_gap"][
    "safe_task_retitle_command_available_now"
]
assert payload["current_l1_l6_evidence"]["exit_criteria"]["expected"] == {
    "exit_layers_checked": 6,
    "exit_layers_pass": 6,
    "exit_layers_with_waiver": 1,
    "gate_ids_checked": ["G1", "G2", "G3", "G4", "G5", "G6"],
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_map": 0,
}
assert payload["current_l1_l6_evidence"]["reference_integrity"]["expected"] == {
    "audit_files_checked": 25,
    "path_like_refs_checked": 1384,
    "direct_file_refs_checked": 1375,
    "glob_patterns_checked": 9,
    "missing_direct_file_refs": 0,
    "empty_glob_patterns": 0,
    "current_scope_uses_l7_as_completion_evidence": False,
}
assert payload["current_l1_l6_evidence"]["double_check"]["expected"] == {
    "quantitative_checks": 21,
    "quantitative_checks_pass": 21,
    "qualitative_checks": 36,
    "qualitative_checks_pass": 36,
    "evidence_boundary_scan_evidence_like_keys_checked": 11,
    "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence": 0,
    "evidence_boundary_scan_current_scope_proof_allows_add_feature": False,
    "evidence_boundary_scan_current_scope_proof_allows_l7_test_design": False,
    "current_scope_verdict": "pass_l1_l6_only",
}
assert payload["current_l1_l6_evidence"]["double_check"]["expected"]["evidence_boundary_scan_evidence_like_keys_checked"] == len(double_check_boundary_scan["evidence_like_keys_checked"])
assert payload["current_l1_l6_evidence"]["double_check"]["expected"]["evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"] == double_check_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
assert payload["current_l1_l6_evidence"]["double_check"]["expected"]["evidence_boundary_scan_current_scope_proof_allows_add_feature"] == double_check_boundary_scan["current_scope_proof_allows_add_feature"]
assert payload["current_l1_l6_evidence"]["double_check"]["expected"]["evidence_boundary_scan_current_scope_proof_allows_l7_test_design"] == double_check_boundary_scan["current_scope_proof_allows_l7_test_design"]
sources = {item["source_id"]: item for item in payload["web_evidence_rechecked_2026_06_12"]}
assert payload["web_evidence_freshness_contract"] == {
    "rechecked_on": datetime.date(2026, 6, 12),
    "latest_core_rechecked_on": datetime.date(2026, 6, 13),
    "latest_core_rechecked_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
    ],
    "canonical_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
        "ZIZMOR-GHA-SECURITY",
        "ACTIONLINT-GHA-WORKFLOW-LINT",
        "OPENSSF-SCORECARD",
        "DEPSDEV-API",
        "OSV-SCANNER",
        "SYFT-SBOM",
        "GRIMP-PYTHON-IMPORT-GRAPH",
        "DEPENDENCY-CRUISER",
        "SHELLCHECK-SHELL-STATIC",
        "MARKDOWNLINT-CLI2",
        "LYCHEE-LINK-CHECKER",
        "VALE-PROSE-LINT",
        "TEXTLINT-NATURAL-LANGUAGE-LINT",
        "MUTMUT-PY-MUTATION-TESTING",
        "HYPOTHESIS-PY-PBT",
        "COVERAGE-PY-COVERAGE",
        "DIFF-COVER-DIFF-COVERAGE",
        "PYTEST-PY-TEST-RUNNER",
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
        "TOX-PY-ENV-ORCHESTRATION",
        "NOX-PY-SESSION-AUTOMATION",
        "IMPORT-LINTER-PY-ARCH-CONTRACTS",
        "CHECK-JSONSCHEMA-DOC-SCHEMA",
        "SPECTRAL-API-CONTRACT-LINT",
        "SQLFLUFF-SQL-LINT",
        "RUFF-PY-LINT-FORMAT",
        "MYPY-PY-TYPE-CHECK",
        "PIP-AUDIT-PY-VULN",
    ],
    "official_sources_expected": 33,
    "must_match_sources": [
        "web_evidence_rechecked_2026_06_12",
        "source_l1_l6_web_evidence_map.sources",
        "source_harness_external_tools_coverage_map.official_web_sources",
    ],
    "source_id_url_and_recheck_date_must_match": True,
    "latest_core_recheck_must_match_supporting_evidence": True,
    "all_sources_must_be_official_https_and_web_fetch_confirmed": True,
    "all_sources_must_remain_not_adopted_current_scope": True,
    "current_scope_revalidation_is_design_evidence_only": True,
    "install_execution_or_ci_connection_requires_new_recheck": True,
    "l7_or_adoption_evidence_allowed": False,
}
assert set(sources) == {
    "MCP-SPEC-2025-06-18",
    "GITHUB-MCP-SERVER",
    "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
    "SEMGREP-CE",
    "GITHUB-CODEQL",
    "ZIZMOR-GHA-SECURITY",
    "ACTIONLINT-GHA-WORKFLOW-LINT",
    "OPENSSF-SCORECARD",
    "DEPSDEV-API",
    "OSV-SCANNER",
    "SYFT-SBOM",
    "GRIMP-PYTHON-IMPORT-GRAPH",
    "DEPENDENCY-CRUISER",
    "SHELLCHECK-SHELL-STATIC",
    "MARKDOWNLINT-CLI2",
    "LYCHEE-LINK-CHECKER",
    "VALE-PROSE-LINT",
    "TEXTLINT-NATURAL-LANGUAGE-LINT",
    "MUTMUT-PY-MUTATION-TESTING",
    "HYPOTHESIS-PY-PBT",
    "COVERAGE-PY-COVERAGE",
    "DIFF-COVER-DIFF-COVERAGE",
    "PYTEST-PY-TEST-RUNNER",
    "PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
    "TOX-PY-ENV-ORCHESTRATION",
    "NOX-PY-SESSION-AUTOMATION",
    "IMPORT-LINTER-PY-ARCH-CONTRACTS",
    "CHECK-JSONSCHEMA-DOC-SCHEMA",
    "SPECTRAL-API-CONTRACT-LINT",
    "SQLFLUFF-SQL-LINT",
    "RUFF-PY-LINT-FORMAT",
    "MYPY-PY-TYPE-CHECK",
    "PIP-AUDIT-PY-VULN",
}
assert set(sources) == set(payload["web_evidence_freshness_contract"]["canonical_source_ids"])
assert "tool_invocation_consent_required" in sources["MCP-SPEC-2025-06-18"]["design_controls"]
assert "secret_storage_policy" in sources["GITHUB-MCP-SERVER"]["design_controls"]
assert "sarif_supported" in sources["SEMGREP-CE"]["design_controls"]
assert "failure_mode" in sources["GITHUB-CODEQL"]["design_controls"]
assert "static analysis tool for GitHub Actions" in " ".join(sources["ZIZMOR-GHA-SECURITY"]["confirmed"])
assert "static checker for GitHub Actions workflow files" in " ".join(sources["ACTIONLINT-GHA-WORKFLOW-LINT"]["confirmed"])
assert "github_actions_workflow_scope" in sources["ZIZMOR-GHA-SECURITY"]["design_controls"]
assert "workflow_syntax_policy" in sources["ACTIONLINT-GHA-WORKFLOW-LINT"]["design_controls"]
assert "repository_scope" in sources["OPENSSF-SCORECARD"]["design_controls"]
assert "dependency_graph_scope" in sources["DEPSDEV-API"]["design_controls"]
assert "vulnerability_database_scope" in sources["OSV-SCANNER"]["design_controls"]
assert "sbom_source_scope" in sources["SYFT-SBOM"]["design_controls"]
assert "import_graph_scope" in sources["GRIMP-PYTHON-IMPORT-GRAPH"]["design_controls"]
assert "dependency_rule_scope" in sources["DEPENDENCY-CRUISER"]["design_controls"]
assert "shell_dialect_policy" in sources["SHELLCHECK-SHELL-STATIC"]["design_controls"]
assert "markdown_source_scope" in sources["MARKDOWNLINT-CLI2"]["design_controls"]
assert "lychee is a fast async stream-based link checker written in Rust" in " ".join(sources["LYCHEE-LINK-CHECKER"]["confirmed"])
assert "helix_db_doc_connection_gap_mapping" in sources["LYCHEE-LINK-CHECKER"]["design_controls"]
assert "vocabulary_policy" in sources["VALE-PROSE-LINT"]["design_controls"]
assert "pluggable linting tool for natural language" in " ".join(sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["confirmed"])
assert "textlint can be started as an MCP server" in " ".join(sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["confirmed"])
assert "natural_language_source_scope" in sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["design_controls"]
assert "mcp_server_disabled_until_approved" in sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["design_controls"]
assert "mutant_apply_disabled_until_approved" in sources["MUTMUT-PY-MUTATION-TESTING"]["design_controls"]
assert "property-based testing library for Python" in " ".join(sources["HYPOTHESIS-PY-PBT"]["confirmed"])
assert "strategy_design_policy" in sources["HYPOTHESIS-PY-PBT"]["design_controls"]
assert "replay_database_policy" in sources["HYPOTHESIS-PY-PBT"]["design_controls"]
assert "measures code coverage for Python programs" in " ".join(sources["COVERAGE-PY-COVERAGE"]["confirmed"])
assert "branch_coverage_policy" in sources["COVERAGE-PY-COVERAGE"]["design_controls"]
assert "fail_under_policy" in sources["COVERAGE-PY-COVERAGE"]["design_controls"]
assert "diff-cover reports coverage for new or modified lines covered by tests" in " ".join(sources["DIFF-COVER-DIFF-COVERAGE"]["confirmed"])
assert "it compares XML or LCov coverage reports with git diff output" in " ".join(sources["DIFF-COVER-DIFF-COVERAGE"]["confirmed"])
assert "helix_db_diff_coverage_mapping" in sources["DIFF-COVER-DIFF-COVERAGE"]["design_controls"]
assert "Python test runner" in " ".join(sources["PYTEST-PY-TEST-RUNNER"]["confirmed"])
assert "small readable tests" in " ".join(sources["PYTEST-PY-TEST-RUNNER"]["confirmed"])
assert "virtual environment management" in " ".join(sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed"])
assert "package builds and installs" in " ".join(sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed"])
assert "standard Python file" in " ".join(sources["NOX-PY-SESSION-AUTOMATION"]["confirmed"])
assert "virtualenv creation per session" in " ".join(sources["NOX-PY-SESSION-AUTOMATION"]["confirmed"])
assert "constraints on imports between Python modules" in " ".join(sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed"])
assert "acyclic_siblings contracts" in " ".join(sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed"])
assert "JSON Schema CLI and pre-commit hook" in " ".join(sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed"])
assert "JSON or YAML instance files" in " ".join(sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed"])
assert "ready-to-use OpenAPI v2 and v3.x rulesets" in " ".join(sources["SPECTRAL-API-CONTRACT-LINT"]["confirmed"])
assert "spectral lint can use local or explicitly selected ruleset files" in " ".join(sources["SPECTRAL-API-CONTRACT-LINT"]["confirmed"])
assert "bad SQL before database execution" in " ".join(sources["SQLFLUFF-SQL-LINT"]["confirmed"])
assert "SQLite" in " ".join(sources["SQLFLUFF-SQL-LINT"]["confirmed"])
assert "test_discovery_policy" in sources["PYTEST-PY-TEST-RUNNER"]["design_controls"]
assert "junitxml_output_policy" in sources["PYTEST-PY-TEST-RUNNER"]["design_controls"]
assert "exit_code_policy" in sources["PYTEST-PY-TEST-RUNNER"]["design_controls"]
assert "environment_matrix_policy" in sources["TOX-PY-ENV-ORCHESTRATION"]["design_controls"]
assert "command_allowlist_policy" in sources["TOX-PY-ENV-ORCHESTRATION"]["design_controls"]
assert "provision_environment_policy" in sources["TOX-PY-ENV-ORCHESTRATION"]["design_controls"]
assert "python_code_review_policy" in sources["NOX-PY-SESSION-AUTOMATION"]["design_controls"]
assert "session_parametrize_policy" in sources["NOX-PY-SESSION-AUTOMATION"]["design_controls"]
assert "venv_backend_policy" in sources["NOX-PY-SESSION-AUTOMATION"]["design_controls"]
assert "contract_type_policy" in sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["design_controls"]
assert "layer_order_policy" in sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["design_controls"]
assert "schemafile_scope" in sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["design_controls"]
assert "helix_db_payload_schema_mapping" in sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["design_controls"]
assert "api_spec_file_scope" in sources["SPECTRAL-API-CONTRACT-LINT"]["design_controls"]
assert "helix_db_api_contract_mapping" in sources["SPECTRAL-API-CONTRACT-LINT"]["design_controls"]
assert "sqlite_dialect_policy" in sources["SQLFLUFF-SQL-LINT"]["design_controls"]
assert "helix_db_sql_schema_lint_mapping" in sources["SQLFLUFF-SQL-LINT"]["design_controls"]
assert "unsafe_fix_disabled_until_approved" in sources["RUFF-PY-LINT-FORMAT"]["design_controls"]
assert "strictness_policy" in sources["MYPY-PY-TYPE-CHECK"]["design_controls"]
assert "error_code_policy" in sources["MYPY-PY-TYPE-CHECK"]["design_controls"]
assert "fix_mode_disabled_until_approved" in sources["PIP-AUDIT-PY-VULN"]["design_controls"]
assert "vulnerability_service_policy" in sources["PIP-AUDIT-PY-VULN"]["design_controls"]
assert web_map["schema_version"] == "l1_l6_web_evidence_source_map_v1"
assert web_map["status"] == "verified_l1_l6_design_evidence_not_adoption"
assert web_map["scope"] == "L1-L6"
assert web_map["boundary"]["source_map_is_l7_artifact"] is False
assert web_map["boundary"]["external_tool_installed"] is False
assert web_map["boundary"]["goal_complete_allowed"] is False
web_sources = {item["source_id"]: item for item in web_map["sources"]}
harness_sources = {item["source_id"]: item for item in harness_coverage["official_web_sources"]}
assert set(web_sources) == set(sources)
assert set(harness_sources) == set(sources)
for source_id, objective_source in sources.items():
    web_source = web_sources[source_id]
    harness_source = harness_sources[source_id]
    assert objective_source["official_url"] == web_source["official_url"]
    assert objective_source["official_url"] == harness_source["official_url"]
    assert objective_source["official_url"].startswith("https://")
    assert web_source["source_type"] == "official"
    freshness_date = payload["web_evidence_freshness_contract"]["rechecked_on"]
    web_source_date = web_source["verified_on"]
    if harness_source["rechecked_on"] != freshness_date:
        web_source_date = web_source.get("rechecked_on", web_source["verified_on"])
    assert harness_source["rechecked_on"] == web_source_date
    if harness_source["rechecked_on"] == freshness_date:
        assert str(web_source["verified_on"]) == str(freshness_date)
    assert web_source["current_scope_action"] == "L4-L6 design evidence only"
    assert harness_source["current_scope_action"] == "design_evidence_only"
    assert web_source["web_fetch_confirmed"] is True
    assert harness_source["web_fetch_confirmed"] is True
    assert web_source["adoption_decision"] == "not_adopted_current_scope"
    assert harness_source["adoption_decision"] == "not_adopted_current_scope"
    assert web_source["confirmed"]["design_controls"]
    assert set(web_source["confirmed"]["design_controls"]) == set(harness_source["design_controls"])
assert fr_trace["schema_version"] == "l1_l6_fr31_trace_map_v1"
assert fr_trace["status"] == "current_scope_l1_l6_trace_clean_not_l7"
assert fr_trace["detector_expected"]["requirements"] == 31
assert fr_trace["detector_expected"]["design_links"] == 31
assert fr_trace["boundary"]["l7_implementation_done"] is False
assert fr_trace["boundary"]["goal_complete_allowed"] is False
rows = fr_trace["requirements"]
assert len(rows) == 31
assert fr_trace["summary"]["all_requirements_have_design_link"] is True
assert fr_trace["summary"]["missing_downstream"] == []
for row in rows:
    assert row["downstream_ids"]
    assert row["design_definition_ids"]
    assert row["design_anchor_count"] > 0
row_by_id = {row["requirement_id"]: row for row in rows}
assert row_by_id["FR-01"]["design_definition_ids"] == ["FR-NSM-01"]
assert row_by_id["FR-FNREG-01"]["design_definition_ids"] == ["FR-FNREG-01"]
assert row_by_id["FR-GLOSSARY-01"]["design_definition_ids"] == ["FR-GLOSSARY-01"]
assert inventory["schema_version"] == "l1_l6_design_asset_inventory_v1"
assert inventory["status"] == "current_scope_l1_l6_inventory_not_l7"
assert inventory["boundary"]["inventory_uses_l7_as_execution_evidence"] is False
assert inventory["asset_counts"]["total_l1_l6_files"] == 50
assert inventory["asset_counts"]["l6_functional_design_files"] == 28
assert len(inventory["layer_assets"]["L6"]["files"]) == 28
layer_dirs = {
    "L1": root / "docs/v2/L1-requirements",
    "L2": root / "docs/v2/L2-screen-design",
    "L3": root / "docs/v2/L3-requirements",
    "L4": root / "docs/v2/L4-basic-design",
    "L5": root / "docs/v2/L5-detailed-design",
    "L6": root / "docs/v2/L6-functional-design",
}
for layer, layer_dir in layer_dirs.items():
    discovered = sorted(
        str(path.relative_to(root))
        for path in layer_dir.rglob("*")
        if path.is_file() and path.suffix in {".md", ".yaml"}
    )
    assert sorted(inventory["layer_assets"][layer]["files"]) == discovered, layer
assert inventory["l6_design_clusters"]["fr_function_specs"]["count"] == 18
assert inventory["l6_design_clusters"]["detector_and_governance_specs"]["count"] == 7
assert inventory["l6_design_clusters"]["deferred_extension_specs"]["count"] == 3
partition_policy = inventory["l6_design_clusters"]["partition_policy"]
assert partition_policy["all_l6_assets_partitioned"] is True
assert partition_policy["overlap_allowed"] is False
assert partition_policy["fr_specs_source_index"] == "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml"
assert "cover the L6 asset list exactly" in partition_policy["rule"]
assert payload["current_l1_l6_evidence"]["asset_inventory"]["expected"]["l6_assets_partitioned"] is (
    partition_policy["all_l6_assets_partitioned"]
)
assert payload["current_l1_l6_evidence"]["asset_inventory"]["expected"]["l6_partition_overlap_allowed"] is (
    partition_policy["overlap_allowed"]
)
assert payload["current_l1_l6_evidence"]["asset_inventory"]["expected"]["l6_partition_clusters"] == 3
fr18_index = yaml.safe_load(
    (root / "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml").read_text(
        encoding="utf-8"
    )
)
indexed_fr_specs = {item["spec"] for item in fr18_index["fr_specs"]}
discovered_fr_specs = {
    str(path.relative_to(root))
    for path in (root / "docs/v2/L6-functional-design").glob("FR-*/function-spec.md")
}
detector_specs = set(inventory["l6_design_clusters"]["detector_and_governance_specs"]["files"])
deferred_specs = set(inventory["l6_design_clusters"]["deferred_extension_specs"]["files"])
l6_inventory_files = set(inventory["layer_assets"]["L6"]["files"])
assert indexed_fr_specs == discovered_fr_specs
assert len(indexed_fr_specs) == inventory["l6_design_clusters"]["fr_function_specs"]["count"]
assert len(detector_specs) == inventory["l6_design_clusters"]["detector_and_governance_specs"]["count"]
assert len(deferred_specs) == inventory["l6_design_clusters"]["deferred_extension_specs"]["count"]
assert indexed_fr_specs.isdisjoint(detector_specs)
assert indexed_fr_specs.isdisjoint(deferred_specs)
assert detector_specs.isdisjoint(deferred_specs)
assert indexed_fr_specs | detector_specs | deferred_specs == l6_inventory_files
assert "inventory metadata only" in inventory["preexisting_l7_pair_references"]["policy"]
l6_l7_refs = {}
for l6_path in sorted((root / "docs/v2/L6-functional-design").rglob("*")):
    if not l6_path.is_file() or l6_path.suffix not in {".md", ".yaml"}:
        continue
    text = l6_path.read_text(encoding="utf-8")
    refs = re.findall(
        r"docs/v2/L7-test-design/[^\s`\])]+|\.\./L7-test-design/[^\s`\])]+",
        text,
    )
    if refs:
        l6_l7_refs[str(l6_path.relative_to(root))] = refs
normalized_refs = [
    ref.replace("../L7-test-design/", "docs/v2/L7-test-design/")
    for refs in l6_l7_refs.values()
    for ref in refs
]
unique_refs = set(normalized_refs)
existing_pair_refs = {ref for ref in unique_refs if (root / ref).exists()}
future_placeholder_refs = unique_refs - existing_pair_refs
boundary = inventory["l6_l7_reference_boundary"]
assert boundary["l6_docs_with_l7_refs"] == len(l6_l7_refs)
assert boundary["l7_ref_occurrences_in_l6_docs"] == len(normalized_refs)
assert boundary["unique_l7_ref_targets"] == len(unique_refs)
assert boundary["existing_pair_artifact_targets"] == len(existing_pair_refs)
assert boundary["future_placeholder_targets"] == len(future_placeholder_refs)
assert boundary["current_audit_created_l7_pair_artifacts"] is False
assert boundary["current_scope_uses_l7_refs_as_completion_evidence"] is False
resolution = inventory["future_pair_reference_resolution_contract"]
assert resolution["current_scope_action"] == "classify_only_no_l7_creation"
assert resolution["future_refs_are_design_placeholders"] is False
assert resolution["future_refs_are_unapproved_pair_targets"] is True
assert resolution["future_refs_are_completion_evidence"] is False
assert resolution["l7_artifact_creation_allowed_now"] is False
assert resolution["required_source_statement"] == "現在タスクでは作成しない"
assert resolution["required_resolution_routes"] == [
    "approved_add_feature_ticket",
    "approved_l7_plan",
]
assert resolution["unlock_conditions"] == [
    "user_explicitly_requests_l7_work",
    "approved_feature_ticket_names_the_l7_target",
    "acceptance_criteria_include_unit_test_design_artifact",
]
assert "pair metadata only" in resolution["route_policy"]
assert len(existing_pair_refs) == 8
assert len(future_placeholder_refs) == 18
assert all("/FR-" in ref and ref.endswith("/unit-test-design.md") for ref in future_placeholder_refs)
for source_doc, refs in l6_l7_refs.items():
    source_text = (root / source_doc).read_text(encoding="utf-8")
    normalized_doc_refs = {
        ref.replace("../L7-test-design/", "docs/v2/L7-test-design/")
        for ref in refs
    }
    if normalized_doc_refs & future_placeholder_refs:
        assert "現在タスクでは作成しない" in source_text, source_doc
assert improvement["schema_version"] == "l1_l6_improvement_candidate_map_v1"
assert improvement["status"] == "current_scope_l1_l6_candidates_not_adopted"
assert improvement["boundary"]["uses_l7_test_design_as_source"] is False
assert improvement["boundary"]["candidates_adopted"] is False
assert improvement["boundary"]["external_tool_installed"] is False
assert improvement["candidate_summary"]["total_candidates"] == 35
assert improvement["candidate_summary"]["current_scope_actions"]["design_only"] == 2
assert improvement["candidate_summary"]["current_scope_actions"]["feature_ticket_only"] == 33
assert improvement["candidate_summary"]["candidates_requiring_confirmation"] == 33
policy = improvement["candidate_discovery_policy"]
assert policy["intake_triggers"] == [
    "l6_design_gap",
    "web_backed_tool_opportunity",
    "db_feedback_or_workflow_automation_gap",
    "runtime_guard_parity_gap",
    "bottleneck_signal_routing_gap",
]
assert policy["required_candidate_fields"] == [
    "id",
    "title",
    "objective_mapping",
    "source_refs",
    "l1_l6_design_status",
    "current_scope_action",
    "deferred_feature_plan",
    "why_it_matters",
    "safety",
]
assert policy["allowed_current_scope_actions"] == ["design_only", "feature_ticket_only"]
assert policy["allowed_source_groups"] == [
    "web_evidence",
    "l6_design",
    "deferred_feature_entry_points",
]
assert policy["safety_fields_required"] == [
    "schema_migration",
    "infrastructure_change",
    "auth_or_pii_change",
]
assert policy["disallowed_evidence"] == [
    "docs/v2/L7-test-design/",
    "runtime execution without approval",
    "helix db write proof",
    "external tool install proof",
]
assert "Candidate discovery is not closure" in policy["closure_rule"]
assert "cannot count as adoption" in policy["promotion_policy"]["feature_ticket_only"]
candidate_ids = {item["id"] for item in improvement["candidates"]}
assert candidate_ids == {
    "L1L6-IMP-DOC-AUTO-REGISTRY",
    "L1L6-IMP-DB-EVIDENCE-LIFECYCLE",
    "L1L6-IMP-MCP-ADMISSION",
    "L1L6-IMP-SEMGREP-SAST",
    "L1L6-IMP-CODEQL-IMPACT",
    "L1L6-IMP-ZIZMOR-GHA-SECURITY",
    "L1L6-IMP-ACTIONLINT-GHA-WORKFLOW-LINT",
    "L1L6-IMP-OPENSSF-SCORECARD",
    "L1L6-IMP-DEPSDEV-DEPENDENCY-INTEL",
    "L1L6-IMP-OSV-VULNERABILITY-SCANNING",
    "L1L6-IMP-SYFT-SBOM-GENERATION",
    "L1L6-IMP-GRIMP-PYTHON-IMPORT-GRAPH",
    "L1L6-IMP-DEPENDENCY-CRUISER-JS-TS-GRAPH",
    "L1L6-IMP-SHELLCHECK-SHELL-STATIC",
    "L1L6-IMP-MARKDOWNLINT-CLI2-DOC-LINT",
    "L1L6-IMP-LYCHEE-LINK-CHECKER",
    "L1L6-IMP-VALE-PROSE-LINT-DDD-GLOSSARY",
    "L1L6-IMP-TEXTLINT-NATURAL-LANGUAGE",
    "L1L6-IMP-MUTMUT-PY-TDD-STRENGTH",
    "L1L6-IMP-HYPOTHESIS-PY-PBT",
    "L1L6-IMP-COVERAGE-PY-COVERAGE",
    "L1L6-IMP-DIFF-COVER-DIFF-COVERAGE",
    "L1L6-IMP-PYTEST-PY-RUNNER",
    "L1L6-IMP-PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
    "L1L6-IMP-TOX-PY-ENV-ORCHESTRATION",
    "L1L6-IMP-NOX-PY-SESSION-AUTOMATION",
    "L1L6-IMP-IMPORT-LINTER-PY-ARCH-CONTRACTS",
    "L1L6-IMP-CHECK-JSONSCHEMA-DOC-SCHEMA",
    "L1L6-IMP-SPECTRAL-API-CONTRACT-LINT",
    "L1L6-IMP-SQLFLUFF-SQL-LINT",
    "L1L6-IMP-RUFF-PY-CODING-RULES",
    "L1L6-IMP-MYPY-PY-TYPE-CHECK",
    "L1L6-IMP-PIP-AUDIT-PY-VULN",
    "L1L6-IMP-DEPENDENCY-IMPACT-QUERY",
    "L1L6-IMP-BOTTLENECK-ROUTING",
}
web_source_ids = {item["source_id"] for item in web_map["sources"]}
assert {item["candidate_class"] for item in improvement["candidates"]} == {
    "document_auto_registration",
    "db_feedback_lifecycle",
    "harness_external_tool_admission",
    "advisory_static_analysis",
    "code_scanning_feedback",
    "github_actions_workflow_security",
    "github_actions_workflow_lint",
    "repository_security_score",
    "dependency_intelligence",
    "vulnerability_scanning",
    "sbom_generation",
    "source_dependency_graph",
    "shell_static_analysis",
    "markdown_static_analysis",
    "link_reference_check",
    "prose_style_analysis",
    "natural_language_lint",
    "python_mutation_testing",
    "python_property_based_testing",
    "python_coverage_measurement",
    "python_diff_coverage_quality",
    "python_test_runner",
    "python_impacted_test_selection",
    "python_environment_orchestration",
    "python_session_automation",
    "python_architecture_contracts",
    "document_schema_validation",
    "api_contract_lint",
    "sql_schema_lint",
    "python_lint_format",
    "python_type_checking",
    "python_dependency_audit",
    "dependency_impact_query",
    "bottleneck_routing",
}
for candidate in improvement["candidates"]:
    assert all(field in candidate for field in policy["required_candidate_fields"]), candidate["id"]
    assert set(candidate["safety"]) == set(policy["safety_fields_required"]), candidate["id"]
    assert candidate["current_scope_action"] in policy["allowed_current_scope_actions"], candidate["id"]
    assert candidate["intake_trigger"] in policy["intake_triggers"], candidate["id"]
    assert candidate["source_refs"], candidate["id"]
    assert not any(
        ref.startswith("docs/v2/L7-test-design") for ref in candidate["source_refs"]
    )
    assert (root / candidate["deferred_feature_plan"]).exists()
    if candidate["current_scope_action"] == "feature_ticket_only":
        feature_text = (root / candidate["deferred_feature_plan"]).read_text(encoding="utf-8")
        feature_meta = yaml.safe_load(feature_text.split("---", 2)[1])
        assert feature_meta["status"] == "draft", candidate["id"]
        assert "approv" in feature_meta["approval_boundary"].lower(), candidate["id"]
    for ref in candidate["source_refs"]:
        ref_path, _, ref_fragment = ref.partition("#")
        assert (root / ref_path).exists(), ref
        if ref_fragment:
            assert ref_path == "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml"
            assert ref_fragment in web_source_ids
for source_group in (
    improvement["sources"]["web_evidence"],
    improvement["sources"]["l6_design"],
    improvement["sources"]["deferred_feature_entry_points"],
):
    for ref in source_group:
        assert (root / ref).exists(), ref
assert pair_map["schema_version"] == "l1_l6_pair_balance_map_v1"
assert pair_map["status"] == "current_scope_l1_l6_pair_balance_not_l7_execution"
assert pair_map["boundary"]["uses_l7_artifact_as_current_scope_evidence"] is False
assert pair_map["boundary"]["coverage_closure_done"] is False
assert pair_map["summary"]["l1_l6_layers_checked"] == 6
assert pair_map["summary"]["layers_pass"] == 6
assert pair_map["summary"]["blocking_findings"] == 0
assert pair_map["summary"]["pair_contract_matrix_layers_checked"] == 6
assert pair_map["summary"]["paired_artifacts_checked"] == 6
assert pair_map["summary"]["expected_design_refs_checked"] == 8
assert pair_map["summary"]["expected_design_refs_backed_by_design_assets"] == 8
assert pair_map["summary"]["expected_design_refs_missing_from_design_assets"] == 0
assert pair_map["summary"]["l6_unit_test_design_viewpoint_count"] == 128
pairs = {item["layer"]: item for item in pair_map["pairs"]}
assert set(pairs) == {"L1", "L2", "L3", "L4", "L5", "L6"}
assert pair_map["summary"]["l1_l6_layers_checked"] == len(pairs)
assert pair_map["summary"]["layers_pass"] == sum(
    1 for item in pairs.values() if item["verdict"].startswith("pass")
)
assert pair_map["summary"]["layers_with_waiver"] == sum(
    1 for item in pairs.values() if "waiver" in item
)
assert [pairs[layer]["trace_pair"] for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]] == [
    "L1-L14",
    "L2-L10",
    "L3-L12",
    "L4-L9",
    "L5-L8",
    "L6-L7",
]
pair_policy = pair_map["pair_contract_policy"]
assert pair_policy["current_scope_action"] == "validate_l1_l6_design_to_test_design_pair_contract_only"
assert pair_policy["l7_work_requested_by_user"] is False
assert pair_policy["l7_artifact_required_for_current_scope"] is False
assert pair_policy["l7_artifact_creation_allowed_without_feature_ticket"] is False
assert pair_policy["waiver_allowed_layers"] == ["L2"]
assert pair_policy["pair_contract_matrix_layers_must_equal_pairs_layers"] is True
assert pair_policy["paired_artifacts_must_exist"] is True
assert pair_policy["expected_design_refs_must_be_backed_by_pair_design_assets"] is True
assert pair_policy["expected_design_refs_missing_from_design_assets_allowed"] == 0
assert set(pair_policy["required_pair_fields"]) == {
    "layer",
    "design_stage",
    "paired_test_design_stage",
    "design_process_layer",
    "expected_pair",
    "paired_artifact",
    "current_scope_status",
}
assert "require an approved feature ticket" in pair_policy["completion_boundary"]
pair_contracts = {item["layer"]: item for item in pair_map["pair_contract_matrix"]}
assert set(pair_contracts) == set(pairs)
assert pair_map["summary"]["pair_contract_matrix_layers_checked"] == len(pair_contracts)
expected_design_refs = [
    ref
    for contract in pair_contracts.values()
    for ref in contract.get("expected_design_refs", [])
]
missing_expected_design_refs = []
for layer, contract in pair_contracts.items():
    pair_design_assets = set(pairs[layer]["design_assets"])
    for ref in contract.get("expected_design_refs", []):
        if ref not in pair_design_assets:
            missing_expected_design_refs.append((layer, ref))
assert pair_map["summary"]["paired_artifacts_checked"] == len(pair_contracts)
assert pair_map["summary"]["expected_design_refs_checked"] == len(expected_design_refs)
assert pair_map["summary"]["expected_design_refs_backed_by_design_assets"] == (
    len(expected_design_refs) - len(missing_expected_design_refs)
)
assert pair_map["summary"]["expected_design_refs_missing_from_design_assets"] == len(missing_expected_design_refs)
assert missing_expected_design_refs == []
expected_pair_labels = {
    "L1": "L1-L14",
    "L2": "L2-L10",
    "L3": "L3-L12",
    "L4": "L4-L9",
    "L5": "L5-L8",
    "L6": "L6-L7",
}
expected_stage_labels = {
    "L1": ("要求定義", "運用テスト設計"),
    "L2": ("画面要求 / 画面設計 / フロントUI", "ワイヤーモック"),
    "L3": ("要件定義", "受入テスト設計"),
    "L4": ("基本設計（外部設計）", "総合テスト設計"),
    "L5": ("詳細設計（内部設計）", "結合テスト設計"),
    "L6": ("機能設計（仕様書）", "単体テスト設計観点"),
}

def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    return yaml.safe_load(text.split("---", 2)[1])

for layer, contract in pair_contracts.items():
    assert contract["expected_pair"] == expected_pair_labels[layer]
    assert (contract["design_stage"], contract["paired_test_design_stage"]) == expected_stage_labels[layer]
    assert contract["design_process_layer"] == layer
    assert not contract["paired_artifact"].startswith("docs/v2/L7-test-design/")
    assert (root / contract["paired_artifact"]).exists()
    assert contract["expected_pair"] == pairs[layer]["trace_pair"]
    if layer == "L2":
        waiver_meta = frontmatter(root / contract["paired_artifact"])
        assert contract["current_scope_status"] == "waiver_present"
        assert contract["expected_test_process_layer"] == "not_applicable"
        assert waiver_meta["process_layer"] == "L2"
        assert waiver_meta["pairs_with"] == contract["expected_pairs_with"]
        assert waiver_meta["applicability"] == "not_applicable"
        assert waiver_meta["reason"] == "ui_absent"
        continue
    if layer == "L6":
        l6_index = yaml.safe_load((root / contract["paired_artifact"]).read_text(encoding="utf-8"))
        assert contract["current_scope_status"] == "l6_unit_test_design_viewpoints_only_not_l7_artifact"
        assert contract["expected_test_process_layer"] == "L6"
        assert l6_index["scope"] == contract["expected_scope"]
        assert l6_index["boundary"]["l7_unit_test_design_artifacts_created"] is False
        assert l6_index["boundary"]["l7_implementation_done"] is False
        assert l6_index["coverage_summary"]["created_l7_fr_test_design_artifacts"] == []
        continue
    pair_meta = frontmatter(root / contract["paired_artifact"])
    assert pair_meta["process_layer"] == contract["expected_test_process_layer"]
    if "expected_pairs_with" in contract:
        assert pair_meta["pairs_with"] == contract["expected_pairs_with"]
    else:
        assert pair_meta["pairs_design"] == contract["expected_design_refs"]
    assert contract["current_scope_status"] == "pair_contract_present"
assert pairs["L2"]["verdict"] == "pass_with_waiver"
assert pairs["L2"]["paired_test_design_assets"] == []
assert pairs["L2"]["waiver"]["path"] in pairs["L2"]["design_assets"]
assert pairs["L2"]["metrics"]["applicability"] == "not_applicable"
assert pairs["L2"]["metrics"]["waiver_reason"] == "ui_absent"
assert pairs["L4"]["metrics"]["semantic_excluded_orphan_count"] == 18
assert pairs["L4"]["monitoring_reason"] == "semantic ST-to-TV-to-L4 transitive trace accepted"
assert pairs["L6"]["paired_test_design_assets"] == [
    "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml"
]
assert pairs["L6"]["metrics"]["l7_artifacts_created_by_current_scope"] == 0
for pair in pairs.values():
    assert pair["design_assets"], pair["layer"]
    assert pair["design_grain"], pair["layer"]
    if pair["layer"] == "L6":
        assert pair["metrics"]["framework_missing_pair_count"] == 0
    else:
        assert pair["metrics"]["missing_pair_count"] == 0, pair["layer"]
    for ref in pair.get("design_assets", []):
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
    for ref in pair.get("paired_test_design_assets", []):
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
    if pair["layer"] != "L2":
        assert pair["paired_test_design_assets"], pair["layer"]
    if "coverage_pct" in pair["metrics"]:
        assert pair["metrics"]["coverage_pct"] == 100.0, pair["layer"]
grain_path = root / "docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md"
grain_text = grain_path.read_text(encoding="utf-8")
assert "L1-L6 粒度・バランス監査" in grain_text
assert "本監査は L7 実装を開始しない" in grain_text
assert "FR 別 L7 成果物の作成" in grain_text
assert "add-feature として別起票" in grain_text
assert "`helix doctor check_requirement_drift --json`" in grain_text
assert "L0 企画突合" in grain_text
assert "docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml" in grain_text
assert "L0 problem axes 10 件 / target areas 10 件" in grain_text
assert "`l0_to_l1_l6_derivation_gaps=0`" in grain_text
assert "`l7_artifacts_created_by_this_audit=0`" in grain_text
assert "`python3 -m cli.lib.trace_symmetry --json`" in grain_text
assert "`HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --json`" in grain_text
assert (
    "`HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview "
    "--strict-full-flow --json`"
) in grain_text
assert "strict full-flow は `overall_clean=false` のまま" in grain_text
for gate_id in ("G8", "G9", "G12", "G14"):
    assert gate_id in grain_text
assert "`approved_deferred`" in grain_text
assert "focus=L6" in grain_text
assert "requirements=31" in grain_text
assert "design_links=31" in grain_text
assert "blocking_findings=0" in grain_text
assert "advisory_findings=0" in grain_text
assert "FR18 全件" in grain_text
assert "UT 候補 128 件" in grain_text
assert "ドキュメント未整備検出" in grain_text
assert "documentation_readiness_gap_patterns_checked=7" in grain_text
assert "detector 実行、fail-close 昇格、DB write は未実施" in grain_text
assert "HELIX DB 書き込み、CI 接続は行わない" in grain_text
doc_readiness_matrix = governance_coverage["documentation_readiness_detection_matrix"]
assert "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml" in grain_text
assert str(doc_readiness_matrix["rows_checked"]) in grain_text
for row in doc_readiness_matrix["rows"]:
    assert row["gap_pattern"] in grain_text
    assert row["detecting_control"] in grain_text
    assert row["completion_boundary"] in grain_text
assert "FR 別 L7 成果物は未作成" in grain_text
assert "schema migration" in grain_text
assert "MCP server / plugin / 外部ツールの install" in grain_text
expected_grain_terms = {
    "L1": "要求 / 運用テスト設計",
    "L2": "UI がないため waiver",
    "L3": "要件 / 受入テスト設計",
    "L4": "システム / コンポーネント粒度",
    "L5": "モジュール / 結合粒度",
    "L6": "関数 / 単体粒度",
}
for layer in pairs:
    assert f"| {layer} |" in grain_text, layer
    assert expected_grain_terms[layer] in grain_text, layer
assert "L10 not_applicable waiver" in grain_text
assert "pass with waiver" in grain_text
assert pairs["L4"]["monitoring_reason"] in grain_text
assert "semantic_excluded_orphan 18" in grain_text
assert "pass with monitoring" in grain_text
assert inventory["coverage_evidence"]["grain_balance"]["source"] == (
    "docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md"
)
assert inventory["coverage_evidence"]["grain_balance"]["l1_l6_current_scope_status"] == "pass"
rat_grain = next(
    item
    for item in ratification_index["ratified_l1_l6_items"]
    if item["id"] == "RAT-GRAIN-BALANCE"
)
assert "docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md" in rat_grain["evidence"]
assert "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml" in rat_grain["evidence"]
assert "full-flow 完了ではない" in grain_text
assert guard_map["schema_version"] == "l1_l6_codex_claude_guard_parity_map_v1"
assert guard_map["status"] == "current_scope_l1_l6_guard_parity_defined"
assert guard_map["scope"] == "L1-L6"
assert guard_map["boundary"]["l7_work_requested_by_user"] is False
assert guard_map["boundary"]["l7_work_requires_feature_ticket"] is True
assert guard_map["boundary"]["parity_map_is_closure"] is False
assert guard_map["boundary"]["new_hook_implementation_done"] is False
assert guard_map["boundary"]["new_codex_runtime_enforcement_done"] is False
assert guard_map["boundary"]["goal_complete_allowed"] is False
assert guard_map["summary"] == {
    "guard_surfaces": 8,
    "parity_status_policies_checked": 5,
    "codex_runtime_evidence_surfaces": 3,
    "l6_design_only_surfaces": 3,
    "future_plan_required_surfaces": 1,
    "parity_gap_routes_checked": 8,
    "parity_route_required_fields_checked": 7,
    "parity_finding_normalization_contracts_checked": 8,
    "parity_normalization_required_fields_checked": 8,
    "parity_closure_requirements_checked": 8,
    "parity_closure_required_fields_checked": 6,
    "parity_accountability_current_scope_proves_checked": 4,
    "parity_accountability_current_scope_does_not_prove_checked": 4,
    "parity_classification_rules_checked": 4,
    "parity_adoption_requirements_checked": 4,
    "blocking_findings_current_scope": 0,
}
assert guard_map["deferred_feature_plan"] == (
    "docs/plans/add-feature/add-feature-2026-06-12-codex-claude-guard-parity-l7.md"
)
assert guard_map["deferred_feature_plan"] in guard_map["sources"]["deferred_feature_entry_points"]
parity_policy = guard_map["parity_status_policy"]
assert set(parity_policy) == {
    "defined_common_policy",
    "codex_runtime_defined",
    "codex_runtime_tested",
    "l6_design_only",
    "future_plan_required",
}
assert all(policy["counts_as_closure"] is False for policy in parity_policy.values())
assert parity_policy["codex_runtime_defined"]["counts_as_codex_runtime_evidence"] is True
assert parity_policy["codex_runtime_tested"]["counts_as_codex_runtime_evidence"] is True
assert parity_policy["l6_design_only"]["counts_as_l6_design_only"] is True
assert parity_policy["future_plan_required"]["counts_as_l6_design_only"] is True
assert guard_map["classification_rules"] == [
    "ClaudeCode hook-only behavior cannot count as parity closure.",
    "Codex parity closure requires Codex runtime, harness, doctor, or post-validation evidence.",
    "L6 design-only parity closes design gaps but does not install hooks or enforce runtime behavior.",
    "Future-plan-required parity must stay in add-feature until explicitly approved.",
]
assert guard_map["parity_accountability_contract"] == {
    "current_scope_action": "prove_guard_parity_is_not_feature_escape",
    "claude_hook_only_behavior_counts_as_gap": True,
    "feature_ticket_is_not_design_substitute": True,
    "l6_design_gap_closed_only_when_surface_has_route_normalization_and_closure_requirement": True,
    "runtime_enforcement_requires_explicit_approval": True,
    "codex_parity_closure_requires_codex_evidence": True,
    "current_scope_must_keep_closure_false": True,
    "current_scope_proves": [
        "each guard surface has a detector or feedback route",
        "each guard surface has a normalized finding contract",
        "each guard surface has a closure requirement with missing evidence",
        "ClaudeCode-only guard behavior cannot be treated as Codex parity",
    ],
    "current_scope_does_not_prove": [
        "new Codex runtime enforcement",
        "hook parity closure",
        "fail-close promotion",
        "CI or gate connection",
    ],
}
closure_policy = guard_map["parity_closure_requirement_policy"]
assert closure_policy == {
    "current_scope_action": "define_closure_requirements_only",
    "closure_allowed_now": False,
    "db_write_allowed_now": False,
    "hook_change_allowed_now": False,
    "runtime_enforcement_change_allowed_now": False,
    "ci_or_gate_connection_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "required_fields": [
        "surface_id",
        "parity_status",
        "current_evidence_class",
        "missing_before_closure",
        "allowed_closure_evidence",
        "current_scope_result",
    ],
}
route_policy = guard_map["parity_gap_route_policy"]
assert route_policy == {
    "current_scope_action": "route_parity_surface_to_detection_and_feedback_only",
    "db_write_allowed_now": False,
    "hook_change_allowed_now": False,
    "fail_close_promotion_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "required_route_fields": [
        "surface_id",
        "parity_status",
        "detector_route",
        "feedback_target",
        "owner_role",
        "next_action",
        "current_scope_boundary",
    ],
}
normalization_policy = guard_map["parity_finding_normalization_policy"]
assert normalization_policy == {
    "current_scope_action": "define_parity_finding_contract_only",
    "db_write_allowed_now": False,
    "hook_change_allowed_now": False,
    "runtime_enforcement_change_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "counts_as_closure": False,
    "allowed_db_targets": ["detector_report", "feedback_event"],
    "allowed_lifecycle_states": ["detected", "candidate_generated"],
    "allowed_severity_floors": ["P1", "P2", "P3"],
    "allowed_completion_guards": [
        "candidate_generated_is_not_closure",
        "plan_materialized_is_not_closure",
    ],
    "required_contract_fields": [
        "surface_id",
        "parity_status",
        "normalized_finding_type",
        "db_target",
        "lifecycle_state",
        "severity_floor",
        "feedback_route",
        "completion_guard",
    ],
}
guard_surfaces = {item["id"]: item for item in guard_map["guard_surfaces"]}
assert set(guard_surfaces) == {
    "GPAR-COMMON-RUNTIME-RULES",
    "GPAR-CODEX-HARNESS-CONSENT",
    "GPAR-HANDOVER-METADATA-BOUNDARY",
    "GPAR-CODEX-DESIGN-WEB-EVIDENCE",
    "GPAR-CODEX-ALLOWED-FILES-BASELINE",
    "GPAR-CONTEXT-INJECTION-PARITY",
    "GPAR-GUARDRAIL-PARITY-AXIS",
    "GPAR-WSC-HOOK-PARITY-CARRY",
}
assert guard_map["summary"]["guard_surfaces"] == len(guard_surfaces)
parity_routes = {item["surface_id"]: item for item in guard_map["parity_gap_routes"]}
assert set(parity_routes) == set(guard_surfaces)
assert guard_map["summary"]["parity_gap_routes_checked"] == len(parity_routes)
for surface_id, route in parity_routes.items():
    for field in route_policy["required_route_fields"]:
        assert field in route, surface_id
    assert route["parity_status"] == guard_surfaces[surface_id]["parity_status"]
    assert route["detector_route"], surface_id
    assert route["feedback_target"] in {"detector_report", "feedback_event"}
    assert route["owner_role"] == "TL"
    assert route["current_scope_boundary"], surface_id
assert parity_routes["GPAR-WSC-HOOK-PARITY-CARRY"]["next_action"] == "route_to_deferred_feature_plan"
assert parity_routes["GPAR-GUARDRAIL-PARITY-AXIS"]["feedback_target"] == "feedback_event"
assert parity_routes["GPAR-HANDOVER-METADATA-BOUNDARY"]["detector_route"] == (
    "handover_legacy_metadata_misread_gap"
)
normalization_contracts = {
    item["surface_id"]: item
    for item in guard_map["parity_finding_normalization_contracts"]
}
assert set(normalization_contracts) == set(guard_surfaces)
assert guard_map["summary"]["parity_finding_normalization_contracts_checked"] == len(
    normalization_contracts
)
for surface_id, contract in normalization_contracts.items():
    for field in normalization_policy["required_contract_fields"]:
        assert field in contract, surface_id
    assert contract["parity_status"] == guard_surfaces[surface_id]["parity_status"]
    assert contract["db_target"] in normalization_policy["allowed_db_targets"]
    assert contract["lifecycle_state"] in normalization_policy["allowed_lifecycle_states"]
    assert contract["severity_floor"] in normalization_policy["allowed_severity_floors"]
    assert contract["completion_guard"] in normalization_policy["allowed_completion_guards"]
    assert contract["feedback_route"], surface_id
assert normalization_contracts["GPAR-GUARDRAIL-PARITY-AXIS"]["severity_floor"] == "P1"
assert normalization_contracts["GPAR-WSC-HOOK-PARITY-CARRY"]["db_target"] == "feedback_event"
assert (
    normalization_contracts["GPAR-WSC-HOOK-PARITY-CARRY"]["completion_guard"]
    == "plan_materialized_is_not_closure"
)
assert normalization_contracts["GPAR-HANDOVER-METADATA-BOUNDARY"]["normalized_finding_type"] == (
    "handover_legacy_l7_metadata_misread_gap"
)
closure_requirements = {
    item["surface_id"]: item
    for item in guard_map["parity_closure_requirements"]
}
assert set(closure_requirements) == set(guard_surfaces)
assert guard_map["summary"]["parity_closure_requirements_checked"] == len(
    closure_requirements
)
for surface_id, requirement in closure_requirements.items():
    for field in closure_policy["required_fields"]:
        assert field in requirement, surface_id
    assert requirement["parity_status"] == guard_surfaces[surface_id]["parity_status"]
    assert requirement["missing_before_closure"], surface_id
    assert requirement["allowed_closure_evidence"], surface_id
    assert (
        "not_closure" in requirement["current_scope_result"]
        or "not_full" in requirement["current_scope_result"]
        or "not_global" in requirement["current_scope_result"]
        or "not_hook" in requirement["current_scope_result"]
        or "deferred" in requirement["current_scope_result"]
        or "no_l7_artifact" in requirement["current_scope_result"]
    ), surface_id
assert closure_requirements["GPAR-WSC-HOOK-PARITY-CARRY"]["current_scope_result"] == (
    "future_plan_required_no_l7_artifact"
)
assert "approved_feature_ticket" in closure_requirements[
    "GPAR-WSC-HOOK-PARITY-CARRY"
]["missing_before_closure"]
assert closure_requirements["GPAR-CODEX-DESIGN-WEB-EVIDENCE"][
    "current_evidence_class"
] == "codex_post_validation_test"
assert closure_requirements["GPAR-HANDOVER-METADATA-BOUNDARY"]["current_scope_result"] == (
    "policy_defined_not_closure"
)
assert guard_map["summary"]["codex_runtime_evidence_surfaces"] == len([
    surface
    for surface in guard_surfaces.values()
    if parity_policy[surface["parity_status"]]["counts_as_codex_runtime_evidence"]
])
assert guard_map["summary"]["l6_design_only_surfaces"] == len([
    surface
    for surface in guard_surfaces.values()
    if parity_policy[surface["parity_status"]]["counts_as_l6_design_only"]
])
assert guard_map["summary"]["future_plan_required_surfaces"] == len([
    surface
    for surface in guard_surfaces.values()
    if surface["parity_status"] == "future_plan_required"
])
assert guard_surfaces["GPAR-CODEX-DESIGN-WEB-EVIDENCE"]["parity_status"] == "codex_runtime_tested"
assert guard_surfaces["GPAR-CONTEXT-INJECTION-PARITY"]["parity_status"] == "l6_design_only"
assert guard_surfaces["GPAR-WSC-HOOK-PARITY-CARRY"]["parity_status"] == "future_plan_required"
common_runtime = guard_surfaces["GPAR-COMMON-RUNTIME-RULES"]
handover_boundary = guard_surfaces["GPAR-HANDOVER-METADATA-BOUNDARY"]
assert handover_boundary["parity_status"] == "defined_common_policy"
assert ".helix/handover/CURRENT.md" in handover_boundary["source_refs"]
assert ".helix/handover/CURRENT.json" in handover_boundary["source_refs"]
assert any(
    "Legacy CURRENT.json L7 task title" in control
    for control in handover_boundary["codex_control"]
)
assert "skills/SKILL_MAP.md" in common_runtime["source_refs"]
for ref in [
    "AGENTS.md",
    "skills/tools/ai-coding/references/gate-policy.md",
    "skills/tools/ai-coding/references/implementation-gate.md",
    "skills/tools/ai-coding/references/codex-prompt-antipatterns.md",
    "skills/tools/ai-coding/references/fork-security-policy.md",
]:
    assert ref in guard_map["sources"]["runtime_rules"]
    assert ref in common_runtime["source_refs"]
assert any(
    "read SKILL_MAP as the workflow/gate/skill index" in control
    for control in common_runtime["codex_control"]
)
assert any("AGENTS.md carries Codex-specific" in control for control in common_runtime["codex_control"])
assert any("ai-coding references carry shared gate policy" in control for control in common_runtime["codex_control"])
codex_adapter_text = (root / "helix/CODEX_RUNTIME_ADAPTER.md").read_text(encoding="utf-8")
assert "`skills/SKILL_MAP.md`" in codex_adapter_text
assert "工程・ゲート・スキル一覧の索引として Core Read" in codex_adapter_text
assert "個別 `SKILL.md` 本文は常時一括読込しない" in codex_adapter_text
assert "`skills/SKILL_MAP.md` は常時読込対象ではない" not in codex_adapter_text
for refs in guard_map["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for surface in guard_surfaces.values():
    assert surface["source_refs"], surface["id"]
    assert surface["codex_control"], surface["id"]
    assert surface["claude_control"], surface["id"]
    assert surface["current_gap"]
    assert surface["parity_status"] in parity_policy, surface["id"]
    assert parity_policy[surface["parity_status"]]["counts_as_closure"] is False
    for ref in surface["source_refs"]:
        assert not ref.startswith("docs/v2/L7-test-design/"), surface["id"]
        assert (root / ref).exists(), ref
    if surface["parity_status"] == "codex_runtime_tested":
        assert any(ref.startswith("cli/lib/") for ref in surface["source_refs"])
        assert any("/tests/" in ref or ref.startswith("cli/tests/") for ref in surface["source_refs"])
    if surface["current_scope_status"] in {"design_closed_implementation_deferred", "inventory_and_design_only"}:
        assert all(ref.startswith("docs/v2/L6-functional-design/") for ref in surface["source_refs"])
        assert surface["current_gap"] != "none_for_current_design_doc_web_evidence_surface"
    if surface["parity_status"] == "future_plan_required":
        assert "future PLAN work" in surface["current_gap"]
        assert guard_map["deferred_feature_plan"] in guard_map["sources"]["deferred_feature_entry_points"]
assert any(
    "Claude hook behavior cannot be counted as Codex parity" in requirement
    for requirement in guard_map["adoption_requirements"]
)
assert "ClaudeCode hook-only behavior cannot count as parity closure." in guard_map["classification_rules"]
assert any(
    "L6 design contracts can close design gaps only" in requirement
    for requirement in guard_map["adoption_requirements"]
)
feature_plan_path = root / guard_map["deferred_feature_plan"]
assert feature_plan_path.exists()
feature_plan_text = feature_plan_path.read_text(encoding="utf-8")
feature_plan_meta = yaml.safe_load(feature_plan_text.split("---", 2)[1])
assert feature_plan_meta["plan_id"] == (
    "add-feature-2026-06-12-codex-claude-guard-parity-l7"
)
assert feature_plan_meta["workflow"] == "add-feature"
assert feature_plan_meta["kind"] == "add-impl"
assert feature_plan_meta["layer"] == "L7"
assert feature_plan_meta["status"] == "draft"
assert "explicit approval" in feature_plan_meta["approval_boundary"]
assert "This add-feature ticket exists because the current task stops at L6" in feature_plan_text
assert "ClaudeCode hook-only behavior cannot count as parity closure" in feature_plan_text
assert feature_plan_meta["status"] == "draft"
assert "This PLAN is only a ticket" in feature_plan_meta["approval_boundary"]
assert "Draft only. This is a feature ticket" in feature_plan_text
assert "not a completed L7 deliverable" in feature_plan_text
full_unlock_targets = full_objective_gap_status["feature_ticket_unlock_contract"]["targets"]
expected_unlock_tokens_by_ticket = {
    feature_id: target["required_unlock_tokens"]
    for feature_id, target in full_unlock_targets.items()
}
assert deferred_coverage["schema_version"] == "l1_l6_deferred_feature_coverage_v1"
assert deferred_coverage["status"] == "current_scope_l1_l6_deferred_boundaries_mapped"
assert deferred_coverage["boundary"]["l7_work_requested_by_user"] is False
assert deferred_coverage["boundary"]["l7_work_requires_feature_ticket"] is True
assert deferred_coverage["boundary"]["coverage_map_is_implementation_evidence"] is False
assert deferred_coverage["boundary"]["l7_test_design_created_by_this_audit"] is False
assert deferred_coverage["boundary"]["l7_implementation_done"] is False
assert deferred_coverage["boundary"]["goal_complete_allowed"] is False
assert deferred_coverage["summary"] == {
    "objective_clauses_checked": 9,
    "deferred_entry_points_checked": 11,
    "feature_tickets_checked": 11,
    "feature_tickets_draft": 11,
    "feature_tickets_with_approval_boundary": 11,
    "feature_tickets_with_unlock_conditions": 11,
    "repository_add_feature_files_discovered": 24,
    "current_objective_deferred_feature_tickets": 11,
    "out_of_current_objective_add_feature_files": 13,
    "out_of_current_objective_completed_add_features": 4,
    "out_of_current_objective_parked_feature_tickets": 0,
    "full_flow_later_phase_approval_boundary": True,
    "clauses_without_deferred_work": 1,
    "clauses_mapped_to_feature_ticket": 8,
    "unmapped_deferred_boundaries": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
clauses = {item["id"] for item in payload["objective_clauses"]}
covered = {item["objective_id"]: item for item in deferred_coverage["objective_boundary_coverage"]}
assert set(covered) == clauses
assert covered["OBJ-REQ-GAP-L6"]["feature_entry_points"] == []
assert covered["OBJ-CODEX-CLAUDE-GUARD-PARITY"]["feature_entry_points"] == [
    "docs/plans/add-feature/add-feature-2026-06-12-codex-claude-guard-parity-l7.md"
]
for refs in deferred_coverage["sources"].values():
    for ref in refs:
        assert (root / ref).exists(), ref
for item in covered.values():
    for ref in item["feature_entry_points"]:
        assert (root / ref).exists(), ref
        assert not ref.startswith("docs/v2/L7-test-design"), ref
tickets = {item["id"]: item for item in deferred_coverage["feature_ticket_integrity"]}
assert set(tickets) == {
    "full_flow_remaining_guards",
    "l7_unit_closure",
    "db_evidence_lifecycle",
    "harness_external_tools",
    "codex_claude_guard_parity",
    "fr_registry_glossary",
    "plan_registry_add_feature_import",
    "dependency_impact_query",
    "bottleneck_routing",
    "phase_enum_l0_l14_runtime_retrofit",
    "contract_design_phase_label_retrofit",
}
source_entry_points = set(deferred_coverage["sources"]["deferred_feature_entry_points"])
ticket_paths = {item["path"] for item in tickets.values()}
objective_entry_points = {
    ref
    for item in covered.values()
    for ref in item["feature_entry_points"]
}
assert ticket_paths == source_entry_points
assert objective_entry_points == ticket_paths
assert deferred_coverage["summary"]["deferred_entry_points_checked"] == len(source_entry_points)
assert deferred_coverage["summary"]["feature_tickets_checked"] == len(tickets)
assert deferred_coverage["summary"]["feature_tickets_draft"] == sum(
    1 for item in tickets.values() if item["status"] == "draft"
)
assert deferred_coverage["summary"]["feature_tickets_with_approval_boundary"] == sum(
    1 for item in tickets.values() if item["approval_boundary_required"]
)
assert deferred_coverage["summary"]["feature_tickets_with_unlock_conditions"] == sum(
    1 for item in tickets.values() if item.get("unlock_conditions")
)
repository_inventory = deferred_coverage["repository_add_feature_inventory"]
repository_add_feature_files = sorted(
    str(path.relative_to(root))
    for path in (root / "docs/plans/add-feature").glob("add-feature-*.md")
)
excluded_inventory = {
    item["id"]: item
    for item in repository_inventory["excluded_from_current_objective"]
}
assert repository_inventory["inventory_scope"] == "docs/plans/add-feature"
assert (
    repository_inventory["current_scope_action"]
    == "classify_all_add_feature_files_without_expanding_l7_scope"
)
assert repository_inventory["all_repository_add_feature_files_checked"] == len(
    repository_add_feature_files
)
assert repository_inventory[
    "current_objective_deferred_feature_tickets_checked"
] == len(tickets)
assert repository_inventory[
    "excluded_from_current_objective_deferred_count"
] == len(excluded_inventory)
assert deferred_coverage["summary"]["repository_add_feature_files_discovered"] == len(
    repository_add_feature_files
)
assert deferred_coverage["summary"]["current_objective_deferred_feature_tickets"] == len(tickets)
assert deferred_coverage["summary"]["out_of_current_objective_add_feature_files"] == len(
    excluded_inventory
)
assert deferred_coverage["summary"]["out_of_current_objective_completed_add_features"] == sum(
    1
    for item in excluded_inventory.values()
    if item["classification"] == "historical_completed_feature"
)
assert deferred_coverage["summary"]["out_of_current_objective_parked_feature_tickets"] == sum(
    1
    for item in excluded_inventory.values()
    if item["classification"] == "parked_feature_ticket_outside_current_objective_set"
)
assert set(repository_inventory["current_objective_ticket_ids"]) == set(tickets)
assert repository_inventory["exclusion_is_completion_evidence_for_current_objective"] is False
assert repository_inventory["exclusion_may_hide_current_l1_l6_design_debt"] is False
assert repository_inventory["l7_work_allowed_by_inventory"] is False
assert set(repository_add_feature_files) == ticket_paths | {
    item["path"] for item in excluded_inventory.values()
}
assert excluded_inventory["detector_failclose_ci_gate"][
    "classification"
] == "current_scope_authorized_ci_enforcement"
assert excluded_inventory["detector_failclose_ci_gate"]["observed_status"] == "completed"
assert all((root / item["path"]).exists() for item in excluded_inventory.values())
assert deferred_coverage["feature_ticket_unlock_condition_contract"] == {
    "source_contract": "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml#feature_ticket_unlock_contract",
    "current_scope_action": "verify_unlock_condition_metadata_only",
    "unlock_conditions_are_completion_evidence": False,
    "l7_execution_allowed_by_unlock_conditions": False,
    "required_feature_ticket_ids": list(expected_unlock_tokens_by_ticket),
    "required_unlock_condition_tokens_by_ticket": expected_unlock_tokens_by_ticket,
}
assert deferred_coverage["summary"]["clauses_without_deferred_work"] == sum(
    1 for item in covered.values() if not item["feature_entry_points"]
)
assert deferred_coverage["summary"]["clauses_mapped_to_feature_ticket"] == sum(
    1 for item in covered.values() if item["feature_entry_points"]
)
assert all(item["workflow"] == "add-feature" for item in tickets.values())
assert all(item["status"] == "draft" for item in tickets.values())
assert all(item["ticket_is_completion_evidence"] is False for item in tickets.values())
assert all(item["approval_boundary_required"] is True for item in tickets.values())
assert all("unlock_conditions" in item for item in tickets.values())
assert {
    ticket_id: ticket["unlock_conditions"]
    for ticket_id, ticket in tickets.items()
} == expected_unlock_tokens_by_ticket
assert tickets["full_flow_remaining_guards"]["approval_required_before_later_phase_work"] is True
assert tickets["full_flow_remaining_guards"]["approval_required_before_implementation"] is True
assert tickets["db_evidence_lifecycle"]["approval_required_before_l7_work"] is True
assert tickets["db_evidence_lifecycle"]["unlock_conditions"] == [
    "db_write",
    "document_auto_registration",
    "feedback_loop",
    "recurrence_closure",
]
assert tickets["harness_external_tools"]["approval_required_before_l7_work"] is True
assert tickets["harness_external_tools"]["approval_required_before_install"] is True
assert tickets["harness_external_tools"]["external_tool_installation_allowed_now"] is False
assert tickets["codex_claude_guard_parity"]["approval_required_before_l7_work"] is True
assert tickets["fr_registry_glossary"]["approval_required_before_l7_work"] is True
assert tickets["plan_registry_add_feature_import"]["approval_required_before_l7_work"] is True
assert tickets["plan_registry_add_feature_import"]["unlock_conditions"] == [
    "plan_registry",
    "plan_registry_import",
    "add_feature",
]
assert tickets["dependency_impact_query"]["approval_required_before_l7_work"] is True
assert tickets["bottleneck_routing"]["approval_required_before_l7_work"] is True
assert tickets["l7_unit_closure"]["approval_required_before_l7_work"] is True
assert tickets["l7_unit_closure"]["approval_required_before_implementation"] is True
assert tickets["contract_design_phase_label_retrofit"]["kind"] == "add-design"
assert tickets["contract_design_phase_label_retrofit"]["layer"] == "L5-L6"
assert tickets["contract_design_phase_label_retrofit"]["approval_required_before_contract_edit"] is True
assert deferred_coverage["design_escalation_boundary"] == {
    "l5_l6_add_design_feature_tickets_checked": 1,
    "ticket_ids": ["contract_design_phase_label_retrofit"],
    "escalation_required_for": ["D-API", "D-DB", "D-CONTRACT"],
    "reason": deferred_coverage["design_escalation_boundary"]["reason"],
    "current_scope_action": "record_boundary_only_no_contract_edit",
    "approval_required_before_contract_edit": True,
    "contract_edit_performed": False,
    "schema_migration_done": False,
    "l7_work_performed": False,
}
assert "contract semantics" in deferred_coverage["design_escalation_boundary"]["reason"]
for ticket in tickets.values():
    plan_path = root / ticket["path"]
    assert plan_path.exists(), ticket["id"]
    text = plan_path.read_text(encoding="utf-8")
    meta = yaml.safe_load(text.split("---", 2)[1])
    assert meta["plan_id"] == plan_path.stem
    assert meta["workflow"] == ticket["workflow"]
    assert meta["kind"] == ticket["kind"]
    assert meta["layer"] == ticket["layer"]
    assert meta["status"] == ticket["status"]
    if "current_task_scope" in ticket:
        assert meta["current_task_scope"] == ticket["current_task_scope"]
    if "approval_required_before_l7_work" in ticket:
        assert meta["approval_required_before_l7_work"] == ticket["approval_required_before_l7_work"]
    if "approval_required_before_later_phase_work" in ticket:
        assert meta["approval_required_before_later_phase_work"] == ticket["approval_required_before_later_phase_work"]
    if "approval_required_before_implementation" in ticket:
        assert meta["approval_required_before_implementation"] == ticket["approval_required_before_implementation"]
    if "approval_required_before_install" in ticket:
        assert meta["approval_required_before_install"] == ticket["approval_required_before_install"]
    if "approval_required_before_contract_edit" in ticket:
        assert meta["approval_required_before_contract_edit"] == ticket["approval_required_before_contract_edit"]
    assert meta["unlock_conditions"] == ticket["unlock_conditions"]
    if ticket["id"] == "contract_design_phase_label_retrofit":
        assert meta["current_scope_non_actions"] == {
            "contract_edit_performed": False,
            "schema_migration_done": False,
            "l7_work_performed": False,
            "helix_db_write_performed": False,
            "ci_or_equivalent_connected": False,
        }
        matrix = {
            item["surface"]: item
            for item in meta["contract_semantics_preservation_matrix"]
        }
        assert set(matrix) == {"D-API", "D-DB", "D-CONTRACT"}
        assert matrix["D-API"]["allowed_after_approval"] == "terminology_and_carry_boundary_labels_only"
        assert matrix["D-DB"]["allowed_after_approval"] == "terminology_and_migration_carry_labels_only"
        assert matrix["D-CONTRACT"]["allowed_after_approval"] == "terminology_and_gate_reference_labels_only"
        assert "endpoint_shape_change" in matrix["D-API"]["forbidden_without_expanded_approval"]
        assert "table_shape_change" in matrix["D-DB"]["forbidden_without_expanded_approval"]
        assert "event_schema_change" in matrix["D-CONTRACT"]["forbidden_without_expanded_approval"]
        assert all(
            "review_diff_is_label_only" in item["required_evidence_after_approval"]
            for item in matrix.values()
        )
        references = {
            item["source_id"]: item
            for item in meta["external_reference_basis"]
        }
        assert set(references) == {
            "OPENAPI-SPEC-3-2-0",
            "JSON-SCHEMA-VALIDATION-2020-12",
            "POSTGRESQL-ALTER-TABLE-CURRENT",
        }
        assert references["OPENAPI-SPEC-3-2-0"]["source_type"] == "official_spec"
        assert references["JSON-SCHEMA-VALIDATION-2020-12"]["source_type"] == "official_spec"
        assert references["POSTGRESQL-ALTER-TABLE-CURRENT"]["source_type"] == "official_docs"
        assert references["OPENAPI-SPEC-3-2-0"]["applies_to"] == ["D-API"]
        assert references["JSON-SCHEMA-VALIDATION-2020-12"]["applies_to"] == ["D-CONTRACT"]
        assert references["POSTGRESQL-ALTER-TABLE-CURRENT"]["applies_to"] == ["D-DB"]
        assert all(item["checked_on"] == datetime.date(2026, 6, 13) for item in references.values())
    assert "approval_boundary" in meta
    assert "This PLAN is only a ticket" in meta["approval_boundary"]
    assert any(
        phrase in text
        for phrase in (
            "feature ticket only",
            "This add-feature ticket",
            "feature ticket",
            "起票",
        )
    )
    assert any(
        phrase in text
        for phrase in (
            "explicit approval",
            "明示承認",
            "承認後",
            "approved",
        )
    )
    assert any(
        phrase in text
        for phrase in (
            "Current task execution",
            "current task does not",
            "現在タスク",
            "現在フェーズ",
        )
    )
    assert any(
        phrase in text
        for phrase in (
            "not completion evidence",
            "not a completed",
            "completion evidence",
            "closure 不可",
            "完了",
        )
    )
assert db_registration_readiness["schema_version"] == "l1_l6_db_registration_readiness_coverage_v1"
assert db_registration_readiness["status"] == "current_scope_l1_l6_db_registration_readiness_mapped"
assert db_registration_readiness["boundary"]["l7_work_requested_by_user"] is False
assert db_registration_readiness["boundary"]["l7_work_requires_feature_ticket"] is True
assert db_registration_readiness["boundary"]["db_registration_map_is_implementation_evidence"] is False
assert db_registration_readiness["boundary"]["plan_registry_changed_by_this_audit"] is False
assert db_registration_readiness["boundary"]["helix_db_write_performed"] is False
assert db_registration_readiness["boundary"]["schema_migration_done"] is False
assert db_registration_readiness["boundary"]["hook_changed_by_this_audit"] is False
assert db_registration_readiness["boundary"]["l7_test_design_created_by_this_audit"] is False
assert db_registration_readiness["summary"]["registration_events_checked"] == len(
    db_registration_readiness["registration_event_readiness"]
)
assert db_registration_readiness["summary"]["registration_event_contracts_checked"] == len(
    db_registration_readiness["registration_event_contracts"]
)
assert db_registration_readiness["summary"]["document_projection_contracts_checked"] == len(
    db_registration_readiness["document_projection_contracts"]
)
assert db_registration_readiness["summary"]["lifecycle_route_contracts_checked"] == len(
    db_registration_readiness["registration_lifecycle_route_contracts"]
)
assert db_registration_readiness["summary"]["event_route_closure_rows_checked"] == len(
    db_registration_readiness["event_route_closure_contract"]["rows"]
)
assert db_registration_readiness["summary"]["readiness_rows"] == len(
    db_registration_readiness["registration_event_readiness"]
)
assert db_registration_readiness["summary"]["add_feature_import_targets_checked"] == 11
assert db_registration_readiness["summary"]["existing_implementation_surfaces_checked"] == len(
    db_registration_readiness["sources"]["implementation_surfaces_read_only"]
)
assert db_registration_readiness["summary"]["l1_l6_design_surfaces_checked"] == len(
    db_registration_readiness["sources"]["workflow_design"]
)
assert db_registration_readiness["summary"]["l7_feature_tickets_created"] == len(
    db_registration_readiness["sources"]["deferred_feature_entry_points"]
)
assert db_registration_readiness["registration_accountability_contract"] == {
    "current_scope_action": "prove_registration_design_is_not_feature_escape",
    "feature_ticket_is_not_design_substitute": True,
    "registration_event_requires_contract_and_lifecycle_route": True,
    "document_projection_requires_missing_detection_and_feedback_route": True,
    "db_write_requires_explicit_approval": True,
    "current_scope_must_keep_db_write_false": True,
    "current_scope_proves": [
        "each registration event has a db target and required fields",
        "each registration event has a trouble detection route",
        "each registration event has an improvement feedback route",
        "each registration event maps to lifecycle and closure guards",
        "document projection can detect missing function registry, glossary, trace, test-design viewpoint, and audit manifest metadata",
    ],
    "current_scope_does_not_prove": [
        "plan_registry add-feature import implementation",
        "HELIX DB write adoption",
        "registry mutation",
        "hook changes",
        "detector auto-execution",
    ],
}
import_target_contract = db_registration_readiness["add_feature_import_target_contract"]
assert import_target_contract == {
    "source_audit": "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml",
    "source_collection": "feature_ticket_integrity",
    "import_glob_after_approval": "docs/plans/add-feature/add-feature-*.md",
    "target_db": "plan_registry",
    "target_status_now": "draft_boundary_only",
    "targets_checked": 11,
    "required_target_ids": [
        "full_flow_remaining_guards",
        "l7_unit_closure",
        "db_evidence_lifecycle",
        "harness_external_tools",
        "codex_claude_guard_parity",
        "fr_registry_glossary",
        "plan_registry_add_feature_import",
        "dependency_impact_query",
        "bottleneck_routing",
        "phase_enum_l0_l14_runtime_retrofit",
        "contract_design_phase_label_retrofit",
    ],
    "import_implemented_now": False,
    "db_write_allowed_now": False,
    "ticket_is_completion_evidence": False,
    "current_scope_action": "map_import_targets_only",
}
source_ticket_ids = {
    item["id"]
    for item in deferred_coverage[import_target_contract["source_collection"]]
}
assert set(import_target_contract["required_target_ids"]) == source_ticket_ids
assert db_registration_readiness["summary"]["add_feature_import_targets_checked"] == len(
    source_ticket_ids
)
db_rows = {item["event"]: item for item in db_registration_readiness["registration_event_readiness"]}
assert set(db_rows) == {
    "PLAN 起票",
    "コード変更",
    "ドキュメント更新",
    "Codex 実行後",
    "ゲート通過後",
    "セッション停止",
}
plan_row = db_rows["PLAN 起票"]
assert plan_row["gap"]["current_scope_action"] == "feature_ticket_only"
assert plan_row["gap"]["gap_is_current_completion_blocker"] is False
assert plan_row["gap"]["ticket_is_completion_evidence"] is False
assert db_rows["コード変更"]["current_scope_action"] == "no_write_no_index_rebuild"
doc_row = db_rows["ドキュメント更新"]
assert doc_row["workflow_hook"] == "document_registry_projection"
assert doc_row["current_readiness"] == "l1_l6_design_contract_present_write_deferred"
assert doc_row["current_scope_action"] == "no_db_write_no_registry_mutation"
assert "functional registry" in doc_row["registration_target"]
assert "test-design viewpoint metadata" in doc_row["registration_target"]
assert {
    "docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-INV-01/function-spec.md",
    "cli/lib/contract_registry.py",
} <= set(doc_row["evidence"])
assert db_rows["ゲート通過後"]["current_scope_action"] == "no_feedback_auto_apply_no_gate_promotion"
contract_policy = db_registration_readiness["registration_event_contract_policy"]
assert contract_policy == {
    "current_scope_action": "map_event_contracts_only",
    "db_write_allowed_now": False,
    "schema_migration_allowed_now": False,
    "hook_change_allowed_now": False,
    "auto_apply_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "required_contract_fields": [
        "event",
        "db_target",
        "required_fields",
        "trouble_detection_route",
        "improvement_feedback_route",
        "current_scope_action",
    ],
}
event_contracts = {
    item["event"]: item for item in db_registration_readiness["registration_event_contracts"]
}
assert set(event_contracts) == set(db_rows)
assert len({item["db_target"] for item in event_contracts.values()}) == len(event_contracts)
assert event_contracts["PLAN 起票"]["db_target"] == "plan_registry"
assert event_contracts["ドキュメント更新"]["db_target"] == "contract_registry"
assert event_contracts["ゲート通過後"]["db_target"] == "feedback_event"
for event, contract in event_contracts.items():
    for field in contract_policy["required_contract_fields"]:
        assert field in contract, event
    assert contract["required_fields"], event
    if event == "PLAN 起票":
        assert contract["current_scope_action"] == "feature_ticket_only_no_plan_registry_change"
    else:
        assert contract["current_scope_action"] == db_rows[event]["current_scope_action"]
    assert contract["trouble_detection_route"], event
    assert contract["improvement_feedback_route"], event
assert "non_closure_reason" in event_contracts["ゲート通過後"]["required_fields"]
assert "implementation_status" in event_contracts["ドキュメント更新"]["required_fields"]
doc_projection_policy = db_registration_readiness["document_projection_policy"]
assert doc_projection_policy == {
    "current_scope_action": "define_document_projection_contract_only",
    "db_write_allowed_now": False,
    "registry_mutation_allowed_now": False,
    "detector_auto_execute_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "allowed_doc_kinds": [
        "l6_function_spec",
        "glossary_registry",
        "design_trace",
        "unit_test_design_viewpoint",
        "audit_manifest",
    ],
    "allowed_db_targets": [
        "functional_registry",
        "glossary_registry",
        "contract_registry",
        "test_design_viewpoint_registry",
        "detector_report",
    ],
    "required_contract_fields": [
        "doc_kind",
        "source_pattern",
        "db_target",
        "required_keys",
        "missing_detection_route",
        "feedback_route",
        "completion_guard",
    ],
}
doc_projection_contracts = {
    item["doc_kind"]: item
    for item in db_registration_readiness["document_projection_contracts"]
}
assert set(doc_projection_contracts) == set(doc_projection_policy["allowed_doc_kinds"])
for doc_kind, contract in doc_projection_contracts.items():
    for field in doc_projection_policy["required_contract_fields"]:
        assert field in contract, doc_kind
    assert contract["db_target"] in doc_projection_policy["allowed_db_targets"]
    assert contract["required_keys"], doc_kind
    assert contract["missing_detection_route"], doc_kind
    assert contract["feedback_route"], doc_kind
    assert contract["completion_guard"].startswith("projection_contract_is_not_")
assert doc_projection_contracts["l6_function_spec"]["db_target"] == "functional_registry"
assert (
    doc_projection_contracts["unit_test_design_viewpoint"]["db_target"]
    == "test_design_viewpoint_registry"
)
assert (
    doc_projection_contracts["unit_test_design_viewpoint"]["completion_guard"]
    == "projection_contract_is_not_l7_test_design"
)
assert doc_projection_contracts["audit_manifest"]["db_target"] == "detector_report"
assert "completion_denial" in doc_projection_contracts["audit_manifest"]["required_keys"]
assert (
    doc_projection_contracts["audit_manifest"]["completion_guard"]
    == "projection_contract_is_not_db_write"
)
route_policy = db_registration_readiness["lifecycle_route_contract_policy"]
assert route_policy == {
    "current_scope_action": "map_event_to_lifecycle_and_route_only",
    "lifecycle_write_allowed_now": False,
    "detector_route_auto_execute_allowed_now": False,
    "allowed_signals": [
        "drift",
        "debt_degradation",
        "regression_dev",
        "runaway",
        "unknown_design",
        "doc_connection_gap",
        "runaway_feedback_loop",
    ],
    "allowed_modes": ["Reverse", "Refactor", "Recovery"],
    "required_contract_fields": [
        "event",
        "entry_state",
        "persisted_state",
        "candidate_state",
        "trouble_detection_signal",
        "routed_mode",
        "improvement_feedback_state",
        "completion_guard",
    ],
}
lifecycle_routes = {
    item["event"]: item
    for item in db_registration_readiness["registration_lifecycle_route_contracts"]
}
assert set(lifecycle_routes) == set(db_rows)
assert lifecycle_routes["ドキュメント更新"]["trouble_detection_signal"] == "doc_connection_gap"
assert lifecycle_routes["Codex 実行後"]["routed_mode"] == "Recovery"
assert lifecycle_routes["ゲート通過後"]["entry_state"] == "verification_recorded"
assert lifecycle_routes["ゲート通過後"]["persisted_state"] == "gate_projected"
valid_states = set(db_coverage["state_machine"]["expected_states"])
valid_closure_rules = set(db_coverage["state_machine"]["closure_rules"])
for event, route in lifecycle_routes.items():
    for field in route_policy["required_contract_fields"]:
        assert field in route, event
    assert route["entry_state"] in valid_states, event
    assert route["persisted_state"] in valid_states, event
    assert route["candidate_state"] in valid_states, event
    assert route["improvement_feedback_state"] in valid_states, event
    assert route["completion_guard"] in valid_closure_rules, event
    assert route["trouble_detection_signal"] in route_policy["allowed_signals"], event
    assert route["routed_mode"] in route_policy["allowed_modes"], event
closure_contract = db_registration_readiness["event_route_closure_contract"]
assert closure_contract["current_scope_action"] == "prove_event_to_route_closure_only"
assert closure_contract["source_collections"] == [
    "registration_event_contracts",
    "registration_lifecycle_route_contracts",
]
assert closure_contract["event_identity_field"] == "event"
assert closure_contract["events_checked"] == len(db_rows)
assert closure_contract["rows_checked"] == len(closure_contract["rows"])
assert db_registration_readiness["summary"]["event_route_closure_rows_checked"] == (
    closure_contract["events_checked"]
)
assert closure_contract["db_write_allowed_now"] is False
assert closure_contract["detector_route_auto_execute_allowed_now"] is False
assert closure_contract["feedback_auto_apply_allowed_now"] is False
assert closure_contract["l7_or_adoption_evidence_allowed"] is False
closure_rows = {item["event"]: item for item in closure_contract["rows"]}
assert set(closure_rows) == set(db_rows)
for event, row in closure_rows.items():
    event_contract = event_contracts[event]
    lifecycle_route = lifecycle_routes[event]
    assert row["db_target"] == event_contract["db_target"], event
    assert row["trouble_detection_route"] == event_contract["trouble_detection_route"], event
    assert row["improvement_feedback_route"] == event_contract["improvement_feedback_route"], event
    assert row["trouble_detection_signal"] == lifecycle_route["trouble_detection_signal"], event
    assert row["routed_mode"] == lifecycle_route["routed_mode"], event
    assert row["improvement_feedback_state"] == lifecycle_route["improvement_feedback_state"], event
    assert row["completion_guard"] == lifecycle_route["completion_guard"], event
for refs in db_registration_readiness["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for row in db_rows.values():
    for ref in row["evidence"]:
        assert not ref.startswith("docs/v2/L7-test-design/"), row["event"]
        assert (root / ref).exists(), ref
assert all(
    item.startswith("This audit does not")
    or item == "Draft add-feature tickets are not implementation evidence."
    or item == "Add-feature import behavior requires approved L7 TDD implementation."
    for item in db_registration_readiness["invariants"]
)
assert db_coverage["schema_version"] == "l1_l6_db_feedback_lifecycle_coverage_v1"
assert db_coverage["status"] == "current_scope_l1_l6_db_feedback_design_covered"
assert db_coverage["boundary"]["l7_work_requested_by_user"] is False
assert db_coverage["boundary"]["l7_work_requires_feature_ticket"] is True
assert db_coverage["boundary"]["db_design_exists"] is True
assert db_coverage["boundary"]["schema_migration_done"] is False
assert db_coverage["boundary"]["db_write_connection_done"] is False
assert db_coverage["boundary"]["recurrence_closure_done"] is False
assert db_coverage["boundary"]["goal_complete_allowed"] is False
assert db_coverage["summary"] == {
    "design_layers_checked": 3,
    "physical_db_design_checked": 1,
    "lifecycle_states_defined": 8,
    "closure_rules_defined": 4,
    "l6_functions_defined": 8,
    "existing_storage_groups_mapped": 6,
    "existing_tables_required_for_lifecycle_checked": 9,
    "forbidden_current_scope_rules_checked": 4,
    "deferred_feature_entry_points_checked": 1,
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
assert db_coverage["feedback_lifecycle_accountability_contract"] == {
    "current_scope_action": "prove_feedback_lifecycle_design_is_not_db_write_adoption",
    "feature_ticket_is_not_design_substitute": True,
    "lifecycle_design_requires_l4_l5_l6_evidence": True,
    "state_machine_requires_non_closure_rules": True,
    "db_write_requires_explicit_approval": True,
    "recurrence_closure_requires_later_execution_evidence": True,
    "current_scope_must_keep_db_write_false": True,
    "current_scope_proves": [
        "L4 external lifecycle from detector signal to recurrence state is designed",
        "L5 state machine and physical DB domain mapping are designed",
        "L6 DBEV functions and completion guard summary are designed",
        "candidate and plan materialization states are not closure",
    ],
    "current_scope_does_not_prove": [
        "schema migration",
        "database write connection",
        "recurrence closure",
        "auto-apply of feedback candidates",
        "full-flow completion",
    ],
}
layer_coverage = {item["layer"]: item for item in db_coverage["layer_coverage"]}
assert set(layer_coverage) == {"L4", "L5", "L6"}
assert db_coverage["summary"]["physical_db_design_checked"] == len(
    db_coverage["sources"]["l5_physical_data_design"]
)
assert layer_coverage["L5"]["supporting_artifact"] == "docs/v2/L5-detailed-design/物理データ設計.md"
assert "DB-01..DB-05" in " ".join(layer_coverage["L5"]["coverage"])
assert "DBEV-FN-08 emit_completion_guard_summary" in layer_coverage["L6"]["coverage"]
assert db_coverage["state_machine"]["expected_states"] == [
    "detected",
    "registered",
    "candidate_generated",
    "plan_materialized",
    "implementation_adopted",
    "verification_recorded",
    "gate_projected",
    "recurrence_closed",
]
assert db_coverage["summary"]["lifecycle_states_defined"] == len(
    db_coverage["state_machine"]["expected_states"]
)
assert db_coverage["summary"]["closure_rules_defined"] == len(
    db_coverage["state_machine"]["closure_rules"]
)
assert db_coverage["storage_mapping_policy"]["mode"] == "existing_db_surfaces_only"
physical = db_coverage["physical_db_design_evidence"]
assert physical["artifact"] == "docs/v2/L5-detailed-design/物理データ設計.md"
assert physical["current_scope_action"] == "read_only_schema_design_evidence"
assert physical["schema_change_required_current_scope"] is False
assert physical["schema_design_is_db_write_evidence"] is False
assert physical["db_domains_checked"] == [
    "DB-01 Plan Governance",
    "DB-02 Execution / Audit",
    "DB-03 Trace Catalog",
    "DB-04 Workspace / Continuity",
    "DB-05 Requirements / Quality",
]
for table in (
    "plan_registry",
    "automation_runs",
    "audit_log",
    "gate_runs",
    "code_index",
    "entries",
    "links",
    "test_design_entries",
    "verify_runs",
):
    assert table in physical["existing_tables_required_for_lifecycle"]
assert db_coverage["summary"]["existing_tables_required_for_lifecycle_checked"] == len(
    physical["existing_tables_required_for_lifecycle"]
)
assert db_coverage["summary"]["existing_storage_groups_mapped"] == len(
    db_coverage["storage_mapping_policy"]["mapped_groups"]
)
assert set(db_coverage["storage_mapping_policy"]["forbidden_current_scope"]) == {
    "schema_migration",
    "destructive_data_operation",
    "auto_apply_feedback_candidates",
    "production_db_operation",
}
assert db_coverage["summary"]["forbidden_current_scope_rules_checked"] == len(
    db_coverage["storage_mapping_policy"]["forbidden_current_scope"]
)
l4 = (root / "docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md").read_text(
    encoding="utf-8"
)
l5 = (root / "docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md").read_text(
    encoding="utf-8"
)
l6 = (root / "docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md").read_text(
    encoding="utf-8"
)
for state in db_coverage["state_machine"]["expected_states"]:
    assert state in l4, state
    assert state in l5, state
    assert state in l6, state
for group in db_coverage["storage_mapping_policy"]["mapped_groups"]:
    assert group.replace("_", " ") in l4, group
for closure_rule in db_coverage["state_machine"]["closure_rules"]:
    if closure_rule == "candidate_generated_is_not_closure":
        assert "`candidate_generated` 止まりで closure 扱いしない" in l6
    elif closure_rule == "plan_materialized_is_not_closure":
        assert "PLAN materialized のみ" in l6
    elif closure_rule == "verification_recorded_requires_gate_projection":
        assert "gate projection なし" in l6
    elif closure_rule == "recurrence_closed_or_monitored_with_owner_required_before_completion":
        assert "closed` / `monitored_with_owner` 以外" in l6
    else:
        raise AssertionError(closure_rule)
for forbidden, text in {
    "schema_migration": "schema_migration",
    "destructive_data_operation": "destructive_data_operation",
    "auto_apply_feedback_candidates": "auto_apply",
    "production_db_operation": "production_db_operation",
}.items():
    assert forbidden in db_coverage["storage_mapping_policy"]["forbidden_current_scope"]
    assert text in l4, forbidden
    assert text in l5 or text == "destructive_data_operation", forbidden
    assert text in l6, forbidden
assert db_coverage["deferred_feature_plan"]["path"] == (
    "docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md"
)
assert db_coverage["deferred_feature_plan"]["approval_required_before_l7_work"] is True
for refs in db_coverage["sources"].values():
    for ref in refs:
        assert (root / ref).exists(), ref
for item in layer_coverage.values():
    assert (root / item["artifact"]).exists(), item["artifact"]
assert harness_coverage["schema_version"] == "l1_l6_harness_external_tools_coverage_v1"
assert harness_coverage["status"] == "current_scope_l1_l6_external_tool_design_covered"
assert harness_coverage["boundary"]["web_sources_verified"] is True
assert harness_coverage["boundary"]["l7_work_requested_by_user"] is False
assert harness_coverage["boundary"]["external_tool_installed"] is False
assert harness_coverage["boundary"]["mcp_server_enabled"] is False
assert harness_coverage["boundary"]["semgrep_or_codeql_executed"] is False
assert harness_coverage["boundary"]["credential_or_secret_change"] is False
assert harness_coverage["boundary"]["external_network_execution"] is False
assert harness_coverage["boundary"]["goal_complete_allowed"] is False
assert harness_coverage["official_source_policy"] == {
    "source_type_required": "official",
    "https_required": True,
    "web_fetch_confirmed_required": True,
    "adoption_decision_required": "not_adopted_current_scope",
    "recheck_required_before_install_or_execution": True,
    "l7_test_design_allowed_as_source": False,
    "current_scope_action_required": "design_evidence_only",
    "credential_or_secret_change_allowed": False,
    "ci_or_equivalent_connection_allowed": False,
}
assert harness_coverage["web_evidence_freshness_contract"] == {
    "rechecked_on": datetime.date(2026, 6, 12),
    "latest_core_rechecked_on": datetime.date(2026, 6, 13),
    "latest_core_rechecked_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
    ],
    "canonical_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
        "ZIZMOR-GHA-SECURITY",
        "ACTIONLINT-GHA-WORKFLOW-LINT",
        "OPENSSF-SCORECARD",
        "DEPSDEV-API",
        "OSV-SCANNER",
        "SYFT-SBOM",
        "GRIMP-PYTHON-IMPORT-GRAPH",
        "DEPENDENCY-CRUISER",
        "SHELLCHECK-SHELL-STATIC",
        "MARKDOWNLINT-CLI2",
        "LYCHEE-LINK-CHECKER",
        "VALE-PROSE-LINT",
        "TEXTLINT-NATURAL-LANGUAGE-LINT",
        "MUTMUT-PY-MUTATION-TESTING",
        "HYPOTHESIS-PY-PBT",
        "COVERAGE-PY-COVERAGE",
        "DIFF-COVER-DIFF-COVERAGE",
        "PYTEST-PY-TEST-RUNNER",
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
        "TOX-PY-ENV-ORCHESTRATION",
        "NOX-PY-SESSION-AUTOMATION",
        "IMPORT-LINTER-PY-ARCH-CONTRACTS",
        "CHECK-JSONSCHEMA-DOC-SCHEMA",
        "SPECTRAL-API-CONTRACT-LINT",
        "SQLFLUFF-SQL-LINT",
        "RUFF-PY-LINT-FORMAT",
        "MYPY-PY-TYPE-CHECK",
        "PIP-AUDIT-PY-VULN",
    ],
    "official_sources_expected": 33,
    "source_id_url_and_recheck_date_must_match_web_evidence_map": True,
    "latest_core_recheck_must_match_web_evidence_map": True,
    "all_sources_must_be_https_official_and_web_fetch_confirmed": True,
    "all_sources_must_remain_not_adopted_current_scope": True,
    "install_execution_or_ci_connection_requires_new_recheck": True,
    "current_scope_revalidation_is_design_evidence_only": True,
    "l7_or_adoption_evidence_allowed": False,
}
adoption_recheck_controls = harness_coverage["adoption_recheck_control_contract"]
assert adoption_recheck_controls["current_scope_action"] == (
    "define_pre_adoption_recheck_controls_only"
)
assert adoption_recheck_controls["controls_checked"] == 3
assert adoption_recheck_controls["controls_apply_before"] == [
    "install",
    "enable_mcp_server",
    "plugin_adoption",
    "external_execution",
    "ci_or_equivalent_connection",
    "helix_db_ingestion",
]
assert adoption_recheck_controls["all_controls_require_new_recheck_before_adoption"] is True
assert adoption_recheck_controls["adoption_or_execution_allowed_now"] is False
assert adoption_recheck_controls["db_write_allowed_now"] is False
assert adoption_recheck_controls["l7_artifact_allowed_now"] is False
adoption_recheck_sources = {
    item["source_id"]: item
    for item in adoption_recheck_controls["sources"]
}
assert set(adoption_recheck_sources) == {
    "MCP-SPEC-2025-06-18",
    "GITHUB-MCP-SERVER",
    "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
}
assert all(
    item["rechecked_on"] == datetime.date(2026, 6, 13)
    for item in adoption_recheck_sources.values()
)
assert "explicit_user_consent_for_data_access_and_tool_calls" in (
    adoption_recheck_sources["MCP-SPEC-2025-06-18"]["controls"]
)
assert "read_only_mode_precedence_review" in adoption_recheck_sources[
    "GITHUB-MCP-SERVER"
]["controls"]
assert "output_schema_and_structured_content_validation" in (
    adoption_recheck_sources["OPENAI-APPS-SDK-MCP-DESCRIPTOR"]["controls"]
)
adoption_recheck_scope = harness_coverage["adoption_recheck_scope_contract"]
assert adoption_recheck_scope == {
    "current_scope_action": "clarify_recheck_scope_vs_candidate_gate_coverage_only",
    "adoption_recheck_controls_checked": 3,
    "latest_core_rechecked_sources_checked": 5,
    "all_candidate_sources_checked": 33,
    "spot_recheck_sources_checked": 8,
    "adoption_control_sources_are_subset_of_latest_core_rechecked_sources": True,
    "adoption_control_sources_are_subset_of_spot_recheck_sources": True,
    "latest_core_rechecked_sources_must_match_freshness_contract": True,
    "latest_core_rechecked_sources_are_subset_of_spot_recheck_sources": True,
    "all_candidate_source_ids_must_match_canonical_source_ids": True,
    "spot_recheck_sources_must_match_spot_recheck_section": True,
    "spot_recheck_sources_are_subset_of_canonical_source_ids": True,
    "spot_recheck_is_not_full_candidate_recheck": True,
    "non_adoption_control_core_sources_remain_admission_gated": True,
    "all_candidates_remain_gated_by_admission_gate_contracts": True,
    "all_candidates_remain_gated_by_tool_intake_contract": True,
    "all_candidates_remain_gated_by_tool_output_ingestion_policy": True,
    "non_core_candidates_require_new_recheck_before_adoption": True,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
assert adoption_recheck_scope["adoption_recheck_controls_checked"] == (
    adoption_recheck_controls["controls_checked"]
)
assert adoption_recheck_scope["latest_core_rechecked_sources_checked"] == len(
    harness_coverage["web_evidence_freshness_contract"][
        "latest_core_rechecked_source_ids"
    ]
)
assert adoption_recheck_scope["all_candidate_sources_checked"] == (
    harness_coverage["summary"]["official_sources_checked"]
)
assert set(adoption_recheck_sources).issubset(
    set(
        harness_coverage["web_evidence_freshness_contract"][
            "latest_core_rechecked_source_ids"
        ]
    )
)
assert adoption_recheck_scope["all_candidate_sources_checked"] == len(
    harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
)
accountability = harness_coverage["harness_tool_accountability_contract"]
assert accountability == {
    "current_scope_action": "prove_external_tool_research_is_not_adoption_or_install",
    "feature_ticket_is_not_design_substitute": True,
    "web_evidence_is_design_basis_not_adoption": True,
    "all_candidates_require_admission_gate_before_install_or_execution": True,
    "mcp_plugin_install_requires_explicit_approval": True,
    "output_ingestion_requires_explicit_db_ingestion_approval": True,
    "current_scope_must_keep_install_execution_ci_db_false": True,
    "l7_work_requires_feature_ticket": True,
    "current_scope_proves": [
        "official Web evidence exists for all 33 candidates",
        "each candidate has intake and output ingestion contracts",
        "each candidate remains not_adopted_current_scope",
        "adoption recheck controls are defined for representative MCP/App sources",
        "pre-adoption requirements bridge maps rechecked risks to L1/L3 requirements and acceptance obligations",
    ],
    "current_scope_does_not_prove": [
        "MCP server enablement",
        "plugin installation",
        "external tool execution",
        "credential or secret configuration",
        "CI/equivalent connection",
        "HELIX DB ingestion",
        "L7 implementation or unit test execution",
        "full-flow completion",
    ],
}
assert accountability["l7_work_requires_feature_ticket"] == (
    harness_coverage["boundary"]["l7_work_requires_feature_ticket"]
)
assert accountability["current_scope_must_keep_install_execution_ci_db_false"]
assert harness_coverage["boundary"]["external_tool_installed"] is False
assert harness_coverage["boundary"]["ci_or_equivalent_connected"] is False
assert harness_coverage["boundary"]["helix_db_write_connected"] is False
web_recheck_design_links = harness_coverage["web_recheck_design_links"]
assert web_recheck_design_links["source_map"] == "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml"
assert web_recheck_design_links["current_scope_action"] == "design_evidence_only"
assert web_recheck_design_links["adoption_or_install_evidence"] is False
admission_gate_ids = {item["gate_id"] for item in harness_coverage["admission_gate_contracts"]}
assert set(web_recheck_design_links["admission_gate_impact"]) == set(
    harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
)
for source_id, impact in web_recheck_design_links["admission_gate_impact"].items():
    assert source_id in harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
    assert set(impact["gates"]).issubset(admission_gate_ids), source_id
    assert impact["reason"], source_id
assert harness_coverage["summary"] == {
    "official_sources_checked": 33,
    "tool_candidates_checked": 33,
    "tool_intake_contracts_checked": 33,
    "tool_intake_required_fields_checked": 9,
    "tool_intake_forbidden_common_rules_checked": 7,
    "admission_gate_contracts_checked": 5,
    "admission_gate_required_fields_checked": 7,
    "admission_owner_roles_checked": 3,
    "tool_output_ingestion_contracts_checked": 33,
    "tool_output_required_fields_checked": 8,
    "tool_output_detector_signals_checked": 5,
    "design_layers_checked": 3,
    "l6_functions_defined": 10,
    "l6_unit_test_viewpoints_defined": 10,
    "adoption_recheck_controls_checked": 3,
    "pre_adoption_requirement_contracts_checked": 5,
    "current_session_web_fetch_sources_checked": 5,
    "current_session_web_fetch_refs_checked": 10,
    "accountability_current_scope_proves_checked": 5,
    "accountability_current_scope_does_not_prove_checked": 8,
    "deferred_feature_entry_points_checked": 1,
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
harness_spot_recheck = harness_coverage["spot_recheck_2026_06_13"]
assert harness_spot_recheck == {
    "source_map": "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml",
    "source_map_section": "spot_recheck_2026_06_13",
    "checked_on": datetime.date(2026, 6, 13),
    "source_count": 8,
    "sources": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
        "ZIZMOR-GHA-SECURITY",
        "ACTIONLINT-GHA-WORKFLOW-LINT",
        "LYCHEE-LINK-CHECKER",
    ],
    "current_scope_action": "design_evidence_only",
    "admission_effect": "keep_existing_gates",
    "adoption_or_install_evidence": False,
    "external_tool_executed": False,
    "mcp_server_enabled": False,
    "ci_or_equivalent_connected": False,
    "helix_db_write_connected": False,
    "l7_or_execution_evidence_allowed": False,
}
current_session_recheck = harness_coverage["current_session_web_fetch_recheck_2026_06_13"]
assert current_session_recheck["current_scope_action"] == "confirm_existing_l1_l6_design_basis_only"
assert current_session_recheck["official_sources_checked"] == 5
assert current_session_recheck["official_sources_checked"] == len(current_session_recheck["sources"])
current_session_source_ids = [item["source_id"] for item in current_session_recheck["sources"]]
assert current_session_source_ids == harness_coverage["web_evidence_freshness_contract"]["latest_core_rechecked_source_ids"]
for item in current_session_recheck["sources"]:
    assert item["official_url"].startswith("https://"), item["source_id"]
    assert item["web_refs"], item["source_id"]
assert current_session_recheck["web_fetch_confirmed"] is True
assert current_session_recheck["adoption_or_execution_allowed_now"] is False
assert current_session_recheck["db_write_allowed_now"] is False
assert current_session_recheck["ci_or_equivalent_connection_allowed_now"] is False
assert current_session_recheck["l7_artifact_allowed_now"] is False
assert current_session_recheck["result"] == "no_change_to_candidate_gate_status"
web_current_session_recheck = web_map["current_session_web_fetch_recheck_2026_06_13"]
assert web_current_session_recheck["current_scope_action"] == current_session_recheck["current_scope_action"]
assert web_current_session_recheck["checked_on"] == current_session_recheck["checked_on"]
assert web_current_session_recheck["official_sources_checked"] == current_session_recheck["official_sources_checked"]
assert web_current_session_recheck["web_fetch_confirmed"] is True
assert web_current_session_recheck["adoption_or_execution_allowed_now"] is False
assert web_current_session_recheck["db_write_allowed_now"] is False
assert web_current_session_recheck["ci_or_equivalent_connection_allowed_now"] is False
assert web_current_session_recheck["l7_artifact_allowed_now"] is False
assert web_current_session_recheck["result"] == current_session_recheck["result"]
current_session_source_ids = {item["source_id"] for item in current_session_recheck["sources"]}
assert current_session_source_ids == set(web_current_session_recheck["source_ids"])
assert "base_protocol_json_rpc" in web_current_session_recheck["confirmed_controls"]["mcp_protocol"]
assert "oauth_or_pat_configuration_boundary" in web_current_session_recheck["confirmed_controls"]["github_mcp_server"]
assert "output_schema_for_structured_content" in web_current_session_recheck["confirmed_controls"]["openai_apps_sdk_descriptor"]
assert "preferred_semgrep_scan_command" in web_current_session_recheck["confirmed_controls"]["semgrep_ce"]
assert "code_scanning_alert_output" in web_current_session_recheck["confirmed_controls"]["github_codeql"]
spot_recheck_sources = set(harness_spot_recheck["sources"])
latest_core_sources = set(
    harness_coverage["web_evidence_freshness_contract"][
        "latest_core_rechecked_source_ids"
    ]
)
canonical_sources = set(
    harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
)
assert adoption_recheck_scope["spot_recheck_sources_checked"] == len(
    spot_recheck_sources
)
assert latest_core_sources.issubset(spot_recheck_sources)
assert set(adoption_recheck_sources).issubset(spot_recheck_sources)
assert spot_recheck_sources.issubset(canonical_sources)
assert spot_recheck_sources != canonical_sources
official_sources = {item["source_id"]: item for item in harness_coverage["official_web_sources"]}
assert set(official_sources) == {
    "MCP-SPEC-2025-06-18",
    "GITHUB-MCP-SERVER",
    "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
    "SEMGREP-CE",
    "GITHUB-CODEQL",
    "ZIZMOR-GHA-SECURITY",
    "ACTIONLINT-GHA-WORKFLOW-LINT",
    "OPENSSF-SCORECARD",
    "DEPSDEV-API",
    "OSV-SCANNER",
    "SYFT-SBOM",
    "GRIMP-PYTHON-IMPORT-GRAPH",
    "DEPENDENCY-CRUISER",
    "SHELLCHECK-SHELL-STATIC",
    "MARKDOWNLINT-CLI2",
    "LYCHEE-LINK-CHECKER",
    "VALE-PROSE-LINT",
    "TEXTLINT-NATURAL-LANGUAGE-LINT",
    "MUTMUT-PY-MUTATION-TESTING",
    "HYPOTHESIS-PY-PBT",
    "COVERAGE-PY-COVERAGE",
    "DIFF-COVER-DIFF-COVERAGE",
    "PYTEST-PY-TEST-RUNNER",
    "PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
    "TOX-PY-ENV-ORCHESTRATION",
    "NOX-PY-SESSION-AUTOMATION",
    "IMPORT-LINTER-PY-ARCH-CONTRACTS",
    "CHECK-JSONSCHEMA-DOC-SCHEMA",
    "SPECTRAL-API-CONTRACT-LINT",
    "SQLFLUFF-SQL-LINT",
    "RUFF-PY-LINT-FORMAT",
    "MYPY-PY-TYPE-CHECK",
    "PIP-AUDIT-PY-VULN",
}
assert "JSON-RPC 2.0 base protocol" in official_sources["MCP-SPEC-2025-06-18"]["confirmed_focus"]
assert "OAuth default path" in official_sources["GITHUB-MCP-SERVER"]["confirmed_focus"]
assert "SARIF output" in official_sources["SEMGREP-CE"]["confirmed_focus"]
assert "code scanning alerts" in official_sources["GITHUB-CODEQL"]["confirmed_focus"]
assert "static analysis for GitHub Actions" in official_sources["ZIZMOR-GHA-SECURITY"]["confirmed_focus"]
assert "GitHub Actions integration and SARIF upload route" in official_sources["ZIZMOR-GHA-SECURITY"]["confirmed_focus"]
assert "static checker for GitHub Actions workflow files" in official_sources["ACTIONLINT-GHA-WORKFLOW-LINT"]["confirmed_focus"]
assert "aggregate and per-check scores" in official_sources["OPENSSF-SCORECARD"]["confirmed_focus"]
assert "dependency graph and package insight" in official_sources["DEPSDEV-API"]["confirmed_focus"]
assert "dependency vulnerability scanning" in official_sources["OSV-SCANNER"]["confirmed_focus"]
assert "Software Bill of Materials generation" in official_sources["SYFT-SBOM"]["confirmed_focus"]
assert "queryable Python import graph" in official_sources["GRIMP-PYTHON-IMPORT-GRAPH"]["confirmed_focus"]
assert "JavaScript / TypeScript dependency validation and visualization" in official_sources["DEPENDENCY-CRUISER"]["confirmed_focus"]
assert "shell script static analysis" in official_sources["SHELLCHECK-SHELL-STATIC"]["confirmed_focus"]
assert "Markdown and CommonMark linting" in official_sources["MARKDOWNLINT-CLI2"]["confirmed_focus"]
assert "fast async stream-based link checker written in Rust" in official_sources["LYCHEE-LINK-CHECKER"]["confirmed_focus"]
assert "helix_db_doc_connection_gap_mapping" in official_sources["LYCHEE-LINK-CHECKER"]["design_controls"]
assert "code-like linting for prose" in official_sources["VALE-PROSE-LINT"]["confirmed_focus"]
assert "pluggable linting tool for natural language" in official_sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["confirmed_focus"]
assert "optional Model Context Protocol server mode" in official_sources["TEXTLINT-NATURAL-LANGUAGE-LINT"]["confirmed_focus"]
assert "Python mutation testing" in official_sources["MUTMUT-PY-MUTATION-TESTING"]["confirmed_focus"]
assert "Python property-based testing library" in official_sources["HYPOTHESIS-PY-PBT"]["confirmed_focus"]
assert "Python code coverage measurement" in official_sources["COVERAGE-PY-COVERAGE"]["confirmed_focus"]
assert "diff coverage reports for new or modified lines covered by tests" in official_sources["DIFF-COVER-DIFF-COVERAGE"]["confirmed_focus"]
assert "compares XML or LCov coverage reports with git diff output" in official_sources["DIFF-COVER-DIFF-COVERAGE"]["confirmed_focus"]
assert "helix_db_diff_coverage_mapping" in official_sources["DIFF-COVER-DIFF-COVERAGE"]["design_controls"]
assert "Python test runner" in official_sources["PYTEST-PY-TEST-RUNNER"]["confirmed_focus"]
assert "readable tests and complex functional testing" in official_sources["PYTEST-PY-TEST-RUNNER"]["confirmed_focus"]
assert "pytest plugin that selects tests affected by changed files and methods" in official_sources["PYTEST-TESTMON-IMPACTED-TEST-SELECTION"]["confirmed_focus"]
assert "dependency collection between tests and executed code using Coverage.py" in official_sources["PYTEST-TESTMON-IMPACTED-TEST-SELECTION"]["confirmed_focus"]
assert "hidden test dependency detection and CI usage surface" in official_sources["PYTEST-TESTMON-IMPACTED-TEST-SELECTION"]["confirmed_focus"]
assert "helix_db_test_impact_mapping" in official_sources["PYTEST-TESTMON-IMPACTED-TEST-SELECTION"]["design_controls"]
assert "Python virtual environment management and test command line tool" in official_sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed_focus"]
assert "environment lists, generated matrices, provisioning, workdir/tempdir, and missing-interpreter policy" in official_sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed_focus"]
assert "Python command-line automation for testing in multiple environments" in official_sources["NOX-PY-SESSION-AUTOMATION"]["confirmed_focus"]
assert "@nox.session functions with dependency installation and ordered command execution" in official_sources["NOX-PY-SESSION-AUTOMATION"]["confirmed_focus"]
assert "Python import architecture constraints" in official_sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed_focus"]
assert "lint-imports contract checking" in official_sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed_focus"]
assert "JSON Schema CLI and pre-commit hook" in official_sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed_focus"]
assert "JSON diagnostic output" in official_sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed_focus"]
assert "ready-to-use OpenAPI v2 and v3.x rulesets" in official_sources["SPECTRAL-API-CONTRACT-LINT"]["confirmed_focus"]
assert "command-line linting with custom ruleset selection" in official_sources["SPECTRAL-API-CONTRACT-LINT"]["confirmed_focus"]
assert "SQL linter designed to catch errors and bad SQL before database execution" in official_sources["SQLFLUFF-SQL-LINT"]["confirmed_focus"]
assert "dialect reference including SQLite" in official_sources["SQLFLUFF-SQL-LINT"]["confirmed_focus"]
assert "Python linter and code formatter" in official_sources["RUFF-PY-LINT-FORMAT"]["confirmed_focus"]
assert "Python static type checker" in official_sources["MYPY-PY-TYPE-CHECK"]["confirmed_focus"]
assert "Python environment vulnerability auditing" in official_sources["PIP-AUDIT-PY-VULN"]["confirmed_focus"]
for source in official_sources.values():
    parsed = urlparse(source["official_url"])
    assert parsed.scheme == "https", source["source_id"]
    assert parsed.netloc in {
        "modelcontextprotocol.io",
    "docs.github.com",
    "developers.openai.com",
    "docs.semgrep.dev",
        "github.com",
        "docs.zizmor.sh",
        "docs.deps.dev",
        "google.github.io",
        "vale.sh",
        "mutmut.readthedocs.io",
        "hypothesis.readthedocs.io",
        "coverage.readthedocs.io",
        "docs.pytest.org",
        "www.testmon.org",
        "tox.wiki",
        "nox.thea.codes",
        "import-linter.readthedocs.io",
        "check-jsonschema.readthedocs.io",
        "docs.astral.sh",
        "textlint.org",
        "mypy.readthedocs.io",
        "docs.sqlfluff.com",
    }, source["source_id"]
    assert source["web_fetch_confirmed"] is True
    assert source["adoption_decision"] == "not_adopted_current_scope"
    assert source["current_scope_action"] == "design_evidence_only"
    assert source["design_controls"], source["source_id"]
    assert harness_coverage["official_source_policy"]["recheck_required_before_install_or_execution"] is True
assert harness_coverage["summary"]["official_sources_checked"] == len(official_sources)
intake_contract = harness_coverage["tool_intake_contract"]
assert intake_contract["current_scope_action"] == "feature_ticket_only_preflight_contract"
assert (root / intake_contract["deferred_feature_plan"]).exists()
assert set(intake_contract["required_candidate_fields"]) == {
    "candidate_id",
    "source_id",
    "kind",
    "admission_status",
    "official_url",
    "required_before_execution",
    "required_source_focus",
    "forbidden_current_scope",
    "deferred_feature_plan",
}
assert set(intake_contract["forbidden_current_scope_common"]) == {
    "install_or_enable_tool",
    "configure_oauth_pat_secret_or_env",
    "execute_external_network_or_scanner",
    "connect_ci_or_equivalent_gate",
    "write_helix_db_or_schema",
    "create_l7_test_design_or_implementation",
    "count_candidate_as_completion",
}
intake_candidates = {item["candidate_id"]: item for item in intake_contract["candidates"]}
assert harness_coverage["summary"]["tool_intake_contracts_checked"] == len(intake_candidates)
for intake in intake_candidates.values():
    source = official_sources[intake["source_id"]]
    assert intake["official_url"] == source["official_url"]
    assert not intake["deferred_feature_plan"].startswith("docs/v2/L7-test-design/")
    assert (root / intake["deferred_feature_plan"]).exists()
    assert set(intake["forbidden_current_scope"]) == set(intake_contract["forbidden_current_scope_common"])
    assert set(intake["required_source_focus"]).issubset(set(source["confirmed_focus"])), intake["candidate_id"]
    assert intake["required_before_execution"], intake["candidate_id"]
    assert intake["admission_status"].startswith("candidate")
output_policy = harness_coverage["tool_output_ingestion_policy"]
assert output_policy == {
    "current_scope_action": "normalize_output_contract_only",
    "execution_allowed_now": False,
    "helix_db_write_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "required_contract_fields": [
        "candidate_id",
        "output_surface",
        "normalized_artifact",
        "db_target",
        "detector_signal",
        "feedback_route",
        "required_before_ingestion",
        "current_scope_action",
    ],
    "allowed_detector_signals": [
        "drift",
        "debt_degradation",
        "regression_dev",
        "unknown_design",
        "doc_connection_gap",
    ],
}
output_contracts = {
    item["candidate_id"]: item
    for item in harness_coverage["tool_output_ingestion_contracts"]
}
assert set(output_contracts) == set(intake_candidates)
assert harness_coverage["summary"]["tool_output_ingestion_contracts_checked"] == len(
    output_contracts
)
assert output_contracts["HEXT-CAND-SEMGREP-CE"]["output_surface"] == "semgrep_json_or_sarif"
assert output_contracts["HEXT-CAND-CODEQL"]["output_surface"] == "codeql_database_sarif_or_alert"
assert output_contracts["HEXT-CAND-ZIZMOR-GHA"]["output_surface"] == "zizmor_plain_json_sarif_github_annotations_or_exit_code"
assert output_contracts["HEXT-CAND-OPENSSF-SCORECARD"]["output_surface"] == "scorecard_score_check_detail_or_api_result"
assert output_contracts["HEXT-CAND-DEPSDEV-API"]["output_surface"] == "depsdev_package_version_dependency_advisory_json"
assert output_contracts["HEXT-CAND-OSV-SCANNER"]["output_surface"] == "osv_scanner_json_sarif_spdx_or_cyclonedx"
assert output_contracts["HEXT-CAND-SYFT-SBOM"]["output_surface"] == "syft_json_cyclonedx_spdx_or_github_dependency_snapshot"
assert output_contracts["HEXT-CAND-GRIMP-PY-IMPORT"]["output_surface"] == "grimp_import_graph_query_result"
assert output_contracts["HEXT-CAND-DEPENDENCY-CRUISER"]["output_surface"] == "dependency_cruiser_json_dot_csv_html_mermaid_or_text"
assert output_contracts["HEXT-CAND-SHELLCHECK"]["output_surface"] == "shellcheck_json_checkstyle_gcc_or_text"
assert output_contracts["HEXT-CAND-MARKDOWNLINT-CLI2"]["output_surface"] == "markdownlint_cli2_issue_json_junit_sarif_codequality_or_summary"
assert output_contracts["HEXT-CAND-VALE-PROSE-LINT"]["output_surface"] == "vale_json_template_metrics_or_exit_code"
assert output_contracts["HEXT-CAND-TEXTLINT"]["output_surface"] == "textlint_json_junit_github_unix_or_fix_dry_run_diff"
assert output_contracts["HEXT-CAND-MUTMUT-PY-MUTATION"]["output_surface"] == "mutmut_mutation_result_surviving_mutant_dependency_warning_or_browse_state"
assert output_contracts["HEXT-CAND-HYPOTHESIS"]["output_surface"] == "hypothesis_falsifying_example_settings_profile_or_pytest_failure"
assert output_contracts["HEXT-CAND-COVERAGE-PY"]["output_surface"] == "coverage_py_text_json_xml_lcov_html_or_sqlite_data"
assert output_contracts["HEXT-CAND-DIFF-COVER"]["output_surface"] == "diff_cover_console_html_json_markdown_or_diff_quality_report"
assert output_contracts["HEXT-CAND-DIFF-COVER"]["current_scope_action"] == "contract_only_no_execution_no_db_write"
assert output_contracts["HEXT-CAND-LYCHEE"]["output_surface"] == "lychee_console_json_github_action_or_precommit_report"
assert output_contracts["HEXT-CAND-LYCHEE"]["current_scope_action"] == "contract_only_no_execution_no_db_write"
assert output_contracts["HEXT-CAND-PYTEST"]["output_surface"] == "pytest_terminal_summary_junitxml_exit_code_or_failure_report"
assert output_contracts["HEXT-CAND-PYTEST-TESTMON"]["output_surface"] == "pytest_testmon_selection_summary_testmondata_dependency_db_or_exit_code"
assert output_contracts["HEXT-CAND-PYTEST-TESTMON"]["current_scope_action"] == "contract_only_no_execution_no_db_write"
assert output_contracts["HEXT-CAND-TOX"]["output_surface"] == "tox_environment_result_config_report_or_exit_code"
assert output_contracts["HEXT-CAND-NOX"]["output_surface"] == "nox_session_list_usage_result_stdout_stderr_or_exit_code"
assert output_contracts["HEXT-CAND-IMPORT-LINTER"]["output_surface"] == "lint_imports_contract_result_broken_contract_diagnostics_or_dot_graph"
assert output_contracts["HEXT-CAND-CHECK-JSONSCHEMA"]["output_surface"] == "check_jsonschema_text_json_diagnostics_or_exit_code"
assert output_contracts["HEXT-CAND-SPECTRAL"]["output_surface"] == "spectral_lint_diagnostics_ruleset_violation_or_exit_code"
assert output_contracts["HEXT-CAND-SQLFLUFF"]["output_surface"] == "sqlfluff_lint_diagnostics_json_github_annotation_or_exit_code"
assert output_contracts["HEXT-CAND-RUFF-PY-LINT-FORMAT"]["output_surface"] == "ruff_diagnostic_json_sarif_junit_github_gitlab_or_text"
assert output_contracts["HEXT-CAND-MYPY"]["output_surface"] == "mypy_type_check_diagnostics_error_codes_reports_or_exit_code"
assert output_contracts["HEXT-CAND-PIP-AUDIT"]["output_surface"] == "pip_audit_json_markdown_cyclonedx_or_columns"
for candidate_id, contract in output_contracts.items():
    for field in output_policy["required_contract_fields"]:
        assert field in contract, candidate_id
    assert contract["candidate_id"] in intake_candidates
    assert contract["db_target"] in {"external_tool_candidate", "detector_report"}
    assert contract["detector_signal"] in output_policy["allowed_detector_signals"]
    assert contract["required_before_ingestion"] == intake_candidates[candidate_id][
        "required_before_execution"
    ]
    assert contract["current_scope_action"] == "contract_only_no_execution_no_db_write"
with open(root / "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml", encoding="utf-8") as handle:
    web_evidence_map = yaml.safe_load(handle)
assert web_evidence_map["boundary"] == {
    "l7_work_requested_by_user": False,
    "l7_work_requires_feature_ticket": True,
    "web_sources_verified": True,
    "source_map_is_l7_artifact": False,
    "candidate_evidence_is_adoption": False,
    "external_tool_installed": False,
    "mcp_server_enabled": False,
    "semgrep_or_codeql_executed": False,
    "scorecard_executed": False,
    "ci_or_equivalent_connected": False,
    "goal_complete_allowed": False,
}
assert web_evidence_map["official_source_policy"] == {
    "source_type_required": "official",
    "https_required": True,
    "web_fetch_confirmed_required": True,
    "adoption_decision_required": "not_adopted_current_scope",
    "recheck_required_before_install_or_execution": True,
    "l7_test_design_allowed_as_source": False,
    "current_scope_action_required": "design_evidence_only",
    "credential_or_secret_change_allowed": False,
    "ci_or_equivalent_connection_allowed": False,
}
assert web_evidence_map["web_evidence_freshness_contract"] == {
    "rechecked_on": datetime.date(2026, 6, 12),
    "latest_core_rechecked_on": datetime.date(2026, 6, 13),
    "latest_core_rechecked_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
    ],
    "canonical_source_ids": [
        "MCP-SPEC-2025-06-18",
        "GITHUB-MCP-SERVER",
        "OPENAI-APPS-SDK-MCP-DESCRIPTOR",
        "SEMGREP-CE",
        "GITHUB-CODEQL",
        "ZIZMOR-GHA-SECURITY",
        "ACTIONLINT-GHA-WORKFLOW-LINT",
        "OPENSSF-SCORECARD",
        "DEPSDEV-API",
        "OSV-SCANNER",
        "SYFT-SBOM",
        "GRIMP-PYTHON-IMPORT-GRAPH",
        "DEPENDENCY-CRUISER",
        "SHELLCHECK-SHELL-STATIC",
        "MARKDOWNLINT-CLI2",
        "LYCHEE-LINK-CHECKER",
        "VALE-PROSE-LINT",
        "TEXTLINT-NATURAL-LANGUAGE-LINT",
        "MUTMUT-PY-MUTATION-TESTING",
        "HYPOTHESIS-PY-PBT",
        "COVERAGE-PY-COVERAGE",
        "DIFF-COVER-DIFF-COVERAGE",
        "PYTEST-PY-TEST-RUNNER",
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION",
        "TOX-PY-ENV-ORCHESTRATION",
        "NOX-PY-SESSION-AUTOMATION",
        "IMPORT-LINTER-PY-ARCH-CONTRACTS",
        "CHECK-JSONSCHEMA-DOC-SCHEMA",
        "SPECTRAL-API-CONTRACT-LINT",
        "SQLFLUFF-SQL-LINT",
        "RUFF-PY-LINT-FORMAT",
        "MYPY-PY-TYPE-CHECK",
        "PIP-AUDIT-PY-VULN",
    ],
    "official_sources_expected": 33,
    "source_id_url_and_recheck_date_must_match_harness_coverage": True,
    "latest_core_recheck_must_match_harness_coverage": True,
    "all_sources_must_be_https_official_and_web_fetch_confirmed": True,
    "all_sources_must_remain_not_adopted_current_scope": True,
    "install_execution_or_ci_connection_requires_new_recheck": True,
    "current_scope_revalidation_is_design_evidence_only": True,
    "l7_or_adoption_evidence_allowed": False,
}
assert web_evidence_map["adoption_recheck_control_contract"] == harness_coverage[
    "adoption_recheck_control_contract"
]
assert web_evidence_map["adoption_recheck_scope_contract"] == harness_coverage[
    "adoption_recheck_scope_contract"
]
web_sources = {item["source_id"]: item for item in web_evidence_map["sources"]}
assert set(web_sources) == set(official_sources)
assert set(web_sources) == set(web_evidence_map["web_evidence_freshness_contract"]["canonical_source_ids"])
assert set(official_sources) == set(harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"])
for source_id, source in official_sources.items():
    web_source = web_sources[source_id]
    freshness_date = harness_coverage["web_evidence_freshness_contract"]["rechecked_on"]
    web_source_date = web_source["verified_on"]
    if source["rechecked_on"] != freshness_date:
        web_source_date = web_source.get("rechecked_on", web_source["verified_on"])
    assert source["rechecked_on"] == web_source_date
    if source["rechecked_on"] == harness_coverage["web_evidence_freshness_contract"]["rechecked_on"]:
        assert web_source["verified_on"] == web_evidence_map["web_evidence_freshness_contract"]["rechecked_on"]
    assert web_source["source_type"] == "official"
    assert web_source["official_url"] == source["official_url"]
    assert web_source["web_fetch_confirmed"] is source["web_fetch_confirmed"]
    assert web_source["adoption_decision"] == source["adoption_decision"]
    assert web_source["source_type"] == web_evidence_map["official_source_policy"]["source_type_required"]
    assert urlparse(web_source["official_url"]).scheme == "https"
    assert web_source["current_scope_action"] == "L4-L6 design evidence only"
    assert web_evidence_map["official_source_policy"]["current_scope_action_required"] == "design_evidence_only"
    assert set(web_source["confirmed"]["design_controls"]) == set(source["design_controls"])
    assert web_source["current_scope_action"] == "L4-L6 design evidence only"
contract_refs = web_evidence_map["contract_design_reference_sources"]
assert contract_refs == {
    "current_scope_action": "official_reference_basis_only_no_contract_edit",
    "linked_ticket_id": "contract_design_phase_label_retrofit",
    "linked_ticket_status": "draft",
    "sources_are_harness_tool_candidates": False,
    "sources_are_completion_evidence": False,
    "contract_edit_performed": False,
    "schema_migration_done": False,
    "l7_work_performed": False,
    "references": contract_refs["references"],
}
contract_ref_sources = {
    item["source_id"]: item for item in contract_refs["references"]
}
assert set(contract_ref_sources) == {
    "OPENAPI-SPEC-3-2-0",
    "JSON-SCHEMA-VALIDATION-2020-12",
    "POSTGRESQL-ALTER-TABLE-CURRENT",
}
assert set(contract_ref_sources).isdisjoint(web_sources)
assert contract_ref_sources["OPENAPI-SPEC-3-2-0"]["applies_to"] == ["D-API"]
assert contract_ref_sources["JSON-SCHEMA-VALIDATION-2020-12"]["applies_to"] == ["D-CONTRACT"]
assert contract_ref_sources["POSTGRESQL-ALTER-TABLE-CURRENT"]["applies_to"] == ["D-DB"]
assert contract_ref_sources["OPENAPI-SPEC-3-2-0"]["confirmed"] == {
    "version": "3.2.0",
    "publication_date": datetime.date(2025, 9, 19),
    "design_boundary": "API description and contract-shape preservation",
}
assert contract_ref_sources["JSON-SCHEMA-VALIDATION-2020-12"]["confirmed"]["dialect"] == "draft_2020_12"
assert contract_ref_sources["POSTGRESQL-ALTER-TABLE-CURRENT"]["confirmed"]["documentation"] == "current"
assert all(
    urlparse(item["official_url"]).scheme == "https"
    and item["web_fetch_confirmed"] is True
    and item["checked_on"] == datetime.date(2026, 6, 13)
    for item in contract_ref_sources.values()
)
web_spot_recheck = web_evidence_map["spot_recheck_2026_06_13"]
assert web_spot_recheck["checked_on"] == datetime.date(2026, 6, 13)
assert web_spot_recheck["source_count"] == 8
assert web_spot_recheck["current_scope_action"] == "design_evidence_only"
assert web_spot_recheck["adoption_or_install_evidence"] is False
assert web_spot_recheck["l7_or_execution_evidence_allowed"] is False
assert [item["source_id"] for item in web_spot_recheck["sources"]] == harness_spot_recheck["sources"]
for item in web_spot_recheck["sources"]:
    source_id = item["source_id"]
    assert source_id in web_sources
    assert item["official_url"] == web_sources[source_id]["official_url"]
    assert item["reconfirmed"], source_id
    assert item["l1_l6_design_effect"], source_id
candidates = {item["candidate_id"]: item for item in harness_coverage["tool_candidate_coverage"]}
assert set(candidates) == {
    "HEXT-CAND-MCP-PROTOCOL",
    "HEXT-CAND-GITHUB-MCP",
    "HEXT-CAND-SEMGREP-CE",
    "HEXT-CAND-CODEQL",
    "HEXT-CAND-ZIZMOR-GHA",
    "HEXT-CAND-ACTIONLINT-GHA",
    "HEXT-CAND-OPENSSF-SCORECARD",
    "HEXT-CAND-DEPSDEV-API",
    "HEXT-CAND-OSV-SCANNER",
    "HEXT-CAND-SYFT-SBOM",
    "HEXT-CAND-GRIMP-PY-IMPORT",
    "HEXT-CAND-DEPENDENCY-CRUISER",
    "HEXT-CAND-SHELLCHECK",
    "HEXT-CAND-MARKDOWNLINT-CLI2",
    "HEXT-CAND-VALE-PROSE-LINT",
    "HEXT-CAND-TEXTLINT",
    "HEXT-CAND-MUTMUT-PY-MUTATION",
    "HEXT-CAND-HYPOTHESIS",
    "HEXT-CAND-COVERAGE-PY",
    "HEXT-CAND-DIFF-COVER",
    "HEXT-CAND-LYCHEE",
    "HEXT-CAND-PYTEST",
    "HEXT-CAND-PYTEST-TESTMON",
    "HEXT-CAND-TOX",
    "HEXT-CAND-NOX",
    "HEXT-CAND-IMPORT-LINTER",
    "HEXT-CAND-CHECK-JSONSCHEMA",
    "HEXT-CAND-SPECTRAL",
    "HEXT-CAND-SQLFLUFF",
    "HEXT-CAND-RUFF-PY-LINT-FORMAT",
    "HEXT-CAND-MYPY",
    "HEXT-CAND-PIP-AUDIT",
    "HEXT-CAND-OPENAI-APPS-MCP-DESCRIPTOR",
}
assert candidates["HEXT-CAND-GITHUB-MCP"]["admission_status"] == "candidate_requires_confirmation"
assert candidates["HEXT-CAND-MCP-PROTOCOL"]["kind"] == "mcp_protocol_admission"
assert candidates["HEXT-CAND-GITHUB-MCP"]["kind"] == "mcp_server"
assert candidates["HEXT-CAND-ZIZMOR-GHA"]["kind"] == "github_actions_workflow_security"
assert candidates["HEXT-CAND-ACTIONLINT-GHA"]["kind"] == "github_actions_workflow_lint"
assert candidates["HEXT-CAND-GRIMP-PY-IMPORT"]["kind"] == "source_dependency_graph"
assert candidates["HEXT-CAND-DEPENDENCY-CRUISER"]["kind"] == "source_dependency_graph"
assert candidates["HEXT-CAND-SHELLCHECK"]["kind"] == "shell_static_analysis"
assert candidates["HEXT-CAND-MARKDOWNLINT-CLI2"]["kind"] == "markdown_static_analysis"
assert candidates["HEXT-CAND-VALE-PROSE-LINT"]["kind"] == "prose_style_analysis"
assert candidates["HEXT-CAND-TEXTLINT"]["kind"] == "natural_language_lint"
assert candidates["HEXT-CAND-MUTMUT-PY-MUTATION"]["kind"] == "python_mutation_testing"
assert candidates["HEXT-CAND-HYPOTHESIS"]["kind"] == "python_property_based_testing"
assert candidates["HEXT-CAND-COVERAGE-PY"]["kind"] == "python_coverage_measurement"
assert candidates["HEXT-CAND-DIFF-COVER"]["kind"] == "python_diff_coverage_quality"
assert "HELIX_DB_diff_coverage_finding_mapping" in candidates["HEXT-CAND-DIFF-COVER"]["required_before_execution"]
assert candidates["HEXT-CAND-LYCHEE"]["kind"] == "link_reference_check"
assert "HELIX_DB_doc_connection_gap_mapping" in candidates["HEXT-CAND-LYCHEE"]["required_before_execution"]
assert candidates["HEXT-CAND-PYTEST"]["kind"] == "python_test_runner"
assert candidates["HEXT-CAND-PYTEST-TESTMON"]["kind"] == "python_impacted_test_selection"
assert "helix_db_test_impact_mapping" in candidates["HEXT-CAND-PYTEST-TESTMON"]["required_before_execution"]
assert candidates["HEXT-CAND-TOX"]["kind"] == "python_environment_orchestration"
assert candidates["HEXT-CAND-NOX"]["kind"] == "python_session_automation"
assert candidates["HEXT-CAND-IMPORT-LINTER"]["kind"] == "python_architecture_contracts"
assert candidates["HEXT-CAND-CHECK-JSONSCHEMA"]["kind"] == "document_schema_validation"
assert candidates["HEXT-CAND-SPECTRAL"]["kind"] == "api_contract_lint"
assert candidates["HEXT-CAND-SQLFLUFF"]["kind"] == "sql_schema_lint"
assert candidates["HEXT-CAND-RUFF-PY-LINT-FORMAT"]["kind"] == "python_lint_format"
assert candidates["HEXT-CAND-MYPY"]["kind"] == "python_type_checking"
assert candidates["HEXT-CAND-PIP-AUDIT"]["kind"] == "python_dependency_audit"
assert candidates["HEXT-CAND-OPENAI-APPS-MCP-DESCRIPTOR"]["kind"] == "app_tool_descriptor"
assert set(candidates) == set(intake_candidates)
assert harness_coverage["summary"]["tool_candidates_checked"] == len(candidates)
assert {candidate["source_id"] for candidate in candidates.values()} == set(official_sources)
for candidate in candidates.values():
    assert candidate["admission_status"].startswith("candidate")
    assert candidate["required_before_execution"], candidate["candidate_id"]
    assert candidate["current_scope_action"] == "feature_ticket_only"
    intake = intake_candidates[candidate["candidate_id"]]
    assert intake["source_id"] == candidate["source_id"]
    assert intake["kind"] == candidate["kind"]
    assert set(intake["required_before_execution"]) == set(candidate["required_before_execution"])
admission_policy = harness_coverage["admission_gate_policy"]
assert admission_policy == {
    "current_scope_action": "define_admission_gate_contract_only",
    "install_allowed_now": False,
    "credential_or_secret_change_allowed_now": False,
    "external_network_execution_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "helix_db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "allowed_owner_roles": ["TL", "Security", "DevOps"],
    "required_gate_fields": [
        "gate_id",
        "applies_to_candidate_kinds",
        "required_decision",
        "blocking_when_missing",
        "owner_role",
        "escalation_condition",
        "completion_guard",
    ],
}
admission_gates = {
    item["gate_id"]: item
    for item in harness_coverage["admission_gate_contracts"]
}
assert set(admission_gates) == {
    "HEXT-ADMIT-AUTH-SCOPE",
    "HEXT-ADMIT-LICENSE-RULES",
    "HEXT-ADMIT-NETWORK-EXECUTION",
    "HEXT-ADMIT-CI-GATE",
    "HEXT-ADMIT-DB-INGESTION",
}
assert harness_coverage["summary"]["admission_gate_contracts_checked"] == len(
    admission_gates
)
candidate_kinds = {candidate["kind"] for candidate in candidates.values()}
candidate_kinds.update(intake["kind"] for intake in intake_candidates.values())
for gate_id, gate in admission_gates.items():
    for field in admission_policy["required_gate_fields"]:
        assert field in gate, gate_id
    assert set(gate["applies_to_candidate_kinds"]) <= candidate_kinds
    assert gate["blocking_when_missing"] is True
    assert gate["owner_role"] in admission_policy["allowed_owner_roles"]
    assert gate["required_decision"], gate_id
    assert gate["escalation_condition"], gate_id
    assert gate["completion_guard"].startswith("admission_gate_pass_is_not_")
assert admission_gates["HEXT-ADMIT-AUTH-SCOPE"]["owner_role"] == "Security"
assert admission_gates["HEXT-ADMIT-CI-GATE"]["owner_role"] == "DevOps"
assert (
    admission_gates["HEXT-ADMIT-DB-INGESTION"]["completion_guard"]
    == "admission_gate_pass_is_not_db_write"
)
harness_layers = {item["layer"]: item for item in harness_coverage["layer_coverage"]}
assert set(harness_layers) == {"L4", "L5", "L6"}
assert harness_coverage["summary"]["design_layers_checked"] == len(harness_layers)
assert "HEXT-FN-10 evaluate_tool_execution_risk" in harness_layers["L6"]["coverage"]
l6_harness_design = (root / harness_layers["L6"]["artifact"]).read_text(encoding="utf-8")
hfunc_ids = sorted(set(re.findall(r"HEXT-FN-[0-9]{2}", l6_harness_design)))
assert hfunc_ids == [f"HEXT-FN-{index:02d}" for index in range(1, 11)]
assert harness_coverage["summary"]["l6_functions_defined"] == len(hfunc_ids)
assert harness_coverage["l6_unit_test_viewpoints"] == {
    "count": 10,
    "prefix": "HEXT-UT-CAND",
    "current_scope_status": "l6_viewpoint_only_not_l7_artifact",
}
assert harness_coverage["summary"]["l6_unit_test_viewpoints_defined"] == harness_coverage["l6_unit_test_viewpoints"]["count"]
assert harness_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
    harness_coverage["sources"]["deferred_feature_entry_points"]
)
assert harness_coverage["deferred_feature_plan"]["path"] == (
    "docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md"
)
assert harness_coverage["deferred_feature_plan"]["external_tool_installation_allowed_now"] is False
for refs in harness_coverage["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
for item in harness_layers.values():
    assert (root / item["artifact"]).exists(), item["artifact"]
assert governance_coverage["schema_version"] == "l1_l6_governance_hardening_coverage_v1"
assert governance_coverage["status"] == "current_scope_l1_l6_governance_design_covered"
assert governance_coverage["boundary"]["l7_work_requested_by_user"] is False
assert governance_coverage["boundary"]["new_l7_test_design_created"] is False
assert governance_coverage["boundary"]["new_l7_implementation_done"] is False
assert governance_coverage["boundary"]["fail_close_promotion_done"] is False
assert governance_coverage["boundary"]["goal_complete_allowed"] is False
assert governance_coverage["summary"] == {
    "governance_surfaces_checked": 8,
    "l6_design_docs_checked": 8,
    "l6_function_contracts_checked": 53,
    "current_scope_l6_ut_candidate_viewpoints": 44,
    "governance_finding_normalization_contracts_checked": 6,
    "governance_normalization_required_fields_checked": 7,
    "documentation_readiness_gap_patterns_checked": 7,
    "governance_controls_checked": 6,
    "governance_detection_required_route_fields_checked": 7,
    "governance_detection_routes_checked": 6,
    "governance_control_trace_rows_checked": 6,
    "governance_control_closure_rows_checked": 6,
    "preexisting_l7_pair_refs": 2,
    "preexisting_completed_feature_entry_points_checked": 3,
    "deferred_feature_entry_points_checked": 4,
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
governance_surfaces = {item["id"]: item for item in governance_coverage["governance_surfaces"]}
assert set(governance_surfaces) == {
    "GOV-CODING-RULE",
    "GOV-DDD-REGISTRY",
    "GOV-TDD-ORDER",
    "GOV-FUNCTION-REGISTRY",
    "GOV-GLOSSARY",
    "GOV-INVENTORY",
    "GOV-IMPACT",
    "GOV-DOC-REVIEW",
}
assert governance_coverage["summary"]["governance_surfaces_checked"] == len(governance_surfaces)
assert governance_coverage["summary"]["l6_design_docs_checked"] == len(
    governance_coverage["sources"]["l6_governance_designs"]
)
assert governance_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
    governance_coverage["sources"]["deferred_feature_entry_points"]
)
assert governance_coverage["summary"]["preexisting_completed_feature_entry_points_checked"] == len(
    governance_coverage["sources"]["preexisting_completed_feature_entry_points"]
)
assert governance_coverage["summary"]["preexisting_l7_pair_refs"] == len(
    governance_coverage["preexisting_pair_policy"]["preexisting_l7_pair_refs"]
)
assert all(
    ref.startswith("docs/v2/L6-functional-design/")
    for ref in governance_coverage["sources"]["l6_governance_designs"]
)
assert all(
    ref.startswith("docs/plans/add-feature/")
    for ref in governance_coverage["sources"]["deferred_feature_entry_points"]
)
for ref in governance_coverage["sources"]["preexisting_completed_feature_entry_points"]:
    plan_path = root / ref
    assert plan_path.exists(), ref
    plan_meta = yaml.safe_load(plan_path.read_text(encoding="utf-8").split("---", 2)[1])
    assert plan_meta["workflow"] == "add-feature"
    assert plan_meta["status"] == "completed"
for refs in governance_coverage["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
assert len(governance_surfaces["GOV-CODING-RULE"]["function_ids"]) == 4
assert len(governance_surfaces["GOV-DDD-REGISTRY"]["function_ids"]) == 5
assert governance_surfaces["GOV-TDD-ORDER"]["l6_ut_candidate_count"] == 7
assert governance_surfaces["GOV-FUNCTION-REGISTRY"]["l6_ut_candidate_count"] == 8
assert governance_surfaces["GOV-GLOSSARY"]["l6_ut_candidate_count"] == 8
assert governance_surfaces["GOV-INVENTORY"]["l6_ut_candidate_count"] == 7
assert governance_surfaces["GOV-IMPACT"]["l6_ut_candidate_count"] == 7
assert governance_surfaces["GOV-DOC-REVIEW"]["l6_ut_candidate_count"] == 7
assert governance_coverage["coverage_controls"]["coding_rule_registry"]["expected_registry_entries"] == 14
assert governance_coverage["coverage_controls"]["ddd_registry"]["expected_glossary_terms_min"] == 19
assert governance_coverage["coverage_controls"]["ddd_registry"]["expected_bounded_contexts"] == 10
assert governance_coverage["coverage_controls"]["tdd_order"]["forbidden_transitions_defined"] is True
assert governance_coverage["coverage_controls"]["tdd_order"]["failing_test_required_before_implementation"] is True
assert governance_coverage["coverage_controls"]["tdd_order"]["closure_denied_without_test_pass"] is True
assert governance_coverage["coverage_controls"]["auto_registration"]["functional_registry_required"] is True
assert governance_coverage["coverage_controls"]["auto_registration"]["glossary_registry_required"] is True
assert governance_coverage["coverage_controls"]["auto_registration"]["db_feedback_append_only"] is True
assert governance_coverage["coverage_controls"]["auto_registration"]["ticket_registration_is_completion_evidence"] is False
assert governance_coverage["coverage_controls"]["impact_visibility"] == {
    "dependency_edges_required": True,
    "affected_artifacts_and_gates_separated": True,
    "unknown_scope_not_treated_as_local": True,
}
assert governance_coverage["coverage_controls"]["doc_review_quality"] == {
    "four_viewpoints_required": True,
    "blocked_result_not_advisory": True,
    "review_evidence_is_completion": False,
    "reviewer_read_only_required": True,
}
doc_readiness_matrix = governance_coverage["documentation_readiness_detection_matrix"]
assert doc_readiness_matrix["current_scope_action"] == "map_user_doc_governance_request_to_existing_l1_l6_controls"
assert doc_readiness_matrix["matrix_is_l7_work"] is False
assert doc_readiness_matrix["detector_execution_added_now"] is False
assert doc_readiness_matrix["fail_close_promotion_added_now"] is False
assert doc_readiness_matrix["db_write_added_now"] is False
assert doc_readiness_matrix["rows_checked"] == 7
doc_gap_rows = {row["gap_pattern"]: row for row in doc_readiness_matrix["rows"]}
assert set(doc_gap_rows) == {
    "missing_function_registry_entry",
    "missing_document_review_or_quality_scope",
    "missing_ddd_or_glossary_registry_coverage",
    "missing_coding_rule_or_enforcement_metadata",
    "tdd_order_violation_or_test_after_implementation",
    "missing_dependency_or_impact_edge",
    "missing_asset_inventory_or_document_projection_metadata",
}
assert doc_readiness_matrix["rows_checked"] == len(doc_gap_rows)
assert {row["detecting_control"] for row in doc_gap_rows.values()}.issubset(governance_coverage["coverage_controls"])
assert {row["primary_governance_surface"] for row in doc_gap_rows.values()}.issubset(governance_surfaces)
for row in doc_gap_rows.values():
    assert row["finding_types"]
    assert row["completion_boundary"].startswith("L6_design_only_")
detection_policy = governance_coverage["governance_detection_policy"]
assert detection_policy["current_scope_action"] == "define_l6_detection_contract_only"
assert detection_policy["detector_execution_added_now"] is False
assert detection_policy["fail_close_promotion_added_now"] is False
assert detection_policy["db_write_added_now"] is False
assert detection_policy["route_to_gate_input"] is True
assert detection_policy["route_to_feedback_candidate"] is True
assert detection_policy["candidate_is_not_closure"] is True
assert detection_policy["allowed_severities"] == ["P0", "P1", "P2", "P3"]
assert detection_policy["required_route_fields"] == [
    "control_id",
    "finding_types",
    "severity_floor",
    "source_artifact",
    "gate_inputs",
    "feedback_behavior",
    "completion_boundary",
]
assert "cannot prove implementation" in detection_policy["completion_boundary_rule"]
normalization_policy = governance_coverage["governance_finding_normalization_policy"]
assert normalization_policy == {
    "current_scope_action": "define_normalized_finding_contract_only",
    "db_write_allowed_now": False,
    "detector_execution_allowed_now": False,
    "fail_close_allowed_now": False,
    "required_fields": [
        "control_id",
        "source_category",
        "normalized_finding_type",
        "db_target",
        "lifecycle_state",
        "feedback_route",
        "completion_guard",
    ],
    "allowed_db_targets": [
        "detector_report",
        "feedback_event",
        "contract_registry",
    ],
    "allowed_lifecycle_states": [
        "detected",
        "registered",
        "candidate_generated",
    ],
    "allowed_completion_guards": [
        "candidate_generated_is_not_closure",
        "plan_materialized_is_not_closure",
    ],
}
normalization_contracts = {
    item["control_id"]: item
    for item in governance_coverage["governance_finding_normalization_contracts"]
}
assert set(normalization_contracts) == set(governance_coverage["coverage_controls"])
assert governance_coverage["summary"]["governance_finding_normalization_contracts_checked"] == len(
    normalization_contracts
)
assert normalization_contracts["tdd_order"]["normalized_finding_type"] == "tdd_order_violation"
assert normalization_contracts["ddd_registry"]["source_category"] == "ddd_registry"
assert normalization_contracts["auto_registration"]["db_target"] == "contract_registry"
for control_id, contract in normalization_contracts.items():
    for field in normalization_policy["required_fields"]:
        assert field in contract, control_id
    assert contract["db_target"] in normalization_policy["allowed_db_targets"]
    assert contract["lifecycle_state"] in normalization_policy["allowed_lifecycle_states"]
    assert contract["completion_guard"] in normalization_policy["allowed_completion_guards"]
    assert contract["feedback_route"], control_id
governance_control_trace = {
    item["control_id"]: item
    for item in governance_coverage["governance_control_trace"]
}
assert set(governance_control_trace) == set(governance_coverage["coverage_controls"])
detection_routes = {
    item["control_id"]: item
    for item in governance_coverage["control_detection_routes"]
}
assert set(detection_routes) == set(governance_coverage["coverage_controls"])
assert detection_routes["tdd_order"]["finding_types"] == [
    "missing_test_design_or_stub",
    "missing_failing_test_observation",
    "implementation_before_test",
    "closure_without_test_pass",
]
assert detection_routes["auto_registration"]["finding_types"] == [
    "undefined_fr",
    "duplicate_fr",
    "registry_drift",
    "missing_asset",
    "reverse_leak",
    "undefined_term",
    "term_variant",
    "anti_corruption_violation",
]
for route in detection_routes.values():
    assert all(field in route for field in detection_policy["required_route_fields"]), route["control_id"]
    assert route["severity_floor"] in detection_policy["allowed_severities"], route["control_id"]
    assert route["finding_types"], route["control_id"]
    assert route["gate_inputs"] == ["G6", "pre-push"], route["control_id"]
    assert route["feedback_behavior"] == "append_candidate_only", route["control_id"]
    assert route["completion_boundary"] == governance_control_trace[
        route["control_id"]
    ]["current_scope_status"], route["control_id"]
    assert not route["source_artifact"].startswith("docs/v2/L7-test-design/")
    assert (root / route["source_artifact"]).exists(), route["control_id"]
    route_text = (root / route["source_artifact"]).read_text(encoding="utf-8")
    if "companion_artifact" in route:
        assert not route["companion_artifact"].startswith("docs/v2/L7-test-design/")
        assert (root / route["companion_artifact"]).exists(), route["control_id"]
        route_text = (
            route_text
            + "\n"
            + (root / route["companion_artifact"]).read_text(encoding="utf-8")
        )
    for finding_type in route["finding_types"]:
        assert finding_type in route_text, (route["control_id"], finding_type)
closure_contract = governance_coverage["governance_control_closure_contract"]
assert (
    closure_contract["current_scope_action"]
    == "prove_governance_detection_to_feedback_alignment_only"
)
assert closure_contract["source_collections"] == [
    "coverage_controls",
    "governance_finding_normalization_contracts",
    "control_detection_routes",
    "governance_control_trace",
]
assert closure_contract["control_identity_field"] == "control_id"
assert closure_contract["controls_checked"] == len(governance_coverage["coverage_controls"])
assert closure_contract["db_write_allowed_now"] is False
assert closure_contract["detector_execution_allowed_now"] is False
assert closure_contract["fail_close_allowed_now"] is False
assert closure_contract["l7_or_adoption_evidence_allowed"] is False
closure_rows = {item["control_id"]: item for item in closure_contract["rows"]}
assert set(closure_rows) == set(governance_coverage["coverage_controls"])
for control_id, row in closure_rows.items():
    normalized = normalization_contracts[control_id]
    route = detection_routes[control_id]
    trace = governance_control_trace[control_id]
    assert row["normalized_finding_type"] == normalized["normalized_finding_type"]
    assert row["source_category"] == normalized["source_category"]
    assert row["db_target"] == normalized["db_target"]
    assert row["lifecycle_state"] == normalized["lifecycle_state"]
    assert row["feedback_route"] == normalized["feedback_route"]
    assert row["gate_inputs"] == route["gate_inputs"]
    assert row["severity_floor"] == route["severity_floor"]
    assert row["completion_boundary"] == trace["current_scope_status"]
assert governance_control_trace["tdd_order"]["current_scope_status"] == "l6_design_only_not_l7_execution"
assert governance_control_trace["auto_registration"]["current_scope_status"] == "l6_design_only_not_db_write"
assert governance_control_trace["impact_visibility"]["current_scope_status"] == "l6_design_only_not_cli"
for control in governance_control_trace.values():
    artifact = root / control["source_artifact"]
    assert artifact.exists(), control["control_id"]
    text = artifact.read_text(encoding="utf-8")
    for term in control["required_terms"]:
        assert term in text, f"{control['control_id']}: {term}"
assert governance_coverage["preexisting_pair_policy"]["current_audit_created_these_l7_artifacts"] is False
assert governance_coverage["preexisting_pair_policy"]["current_scope_uses_l7_as_completion_evidence"] is False
for ref in governance_coverage["preexisting_pair_policy"]["preexisting_l7_pair_refs"]:
    assert ref.startswith("docs/v2/L7-test-design/"), ref
    assert (root / ref).exists(), ref
source_refs = {ref for refs in governance_coverage["sources"].values() for ref in refs}
assert not set(governance_coverage["preexisting_pair_policy"]["preexisting_l7_pair_refs"]).intersection(source_refs)
completed_feature_refs = set(governance_coverage["sources"]["preexisting_completed_feature_entry_points"])
deferred_feature_refs = set(governance_coverage["sources"]["deferred_feature_entry_points"])
assert completed_feature_refs.isdisjoint(deferred_feature_refs)
assert "docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md" in completed_feature_refs
assert governance_surfaces["GOV-CODING-RULE"]["completed_feature_plan"] in completed_feature_refs
assert governance_surfaces["GOV-DDD-REGISTRY"]["completed_feature_plan"] in completed_feature_refs
for refs in governance_coverage["sources"].values():
    for ref in refs:
        assert (root / ref).exists(), ref
deferred_feature_entry_points = set(
    governance_coverage["sources"]["deferred_feature_entry_points"]
)
assert {
    surface["deferred_feature_plan"]
    for surface in governance_surfaces.values()
    if "deferred_feature_plan" in surface
}.issubset(deferred_feature_entry_points)
observed_function_contracts = 0
observed_ut_candidates = 0
frozen_existing_pairs = set()
current_scope_l6_designs = set()
for surface in governance_surfaces.values():
    artifact = root / surface["artifact"]
    assert artifact.exists(), surface["artifact"]
    if "deferred_feature_plan" in surface:
        plan_ref = surface["deferred_feature_plan"]
        assert plan_ref in deferred_feature_refs
    else:
        plan_ref = surface["completed_feature_plan"]
        assert plan_ref in completed_feature_refs
    assert (root / plan_ref).exists(), surface["id"]
    assert surface["artifact"].startswith("docs/v2/L6-functional-design/")
    assert plan_ref.startswith("docs/plans/add-feature/")
    assert "L6" in surface["scope_result"], surface["id"]
    assert "implementation" not in surface["scope_result"].lower(), surface["id"]
    if surface["design_status"] == "frozen_existing_pair":
        frozen_existing_pairs.add(surface["id"])
    if surface["design_status"] == "current_scope_l6_design":
        current_scope_l6_designs.add(surface["id"])
    text = artifact.read_text(encoding="utf-8")
    for function_id in surface["function_ids"]:
        assert function_id in text, f"{surface['id']}: {function_id}"
    observed_function_contracts += len(surface["function_ids"])
    if "l6_ut_candidate_count" in surface:
        prefix = surface["function_ids"][0].split("-FN-")[0]
        candidate_ids = set(re.findall(rf"{re.escape(prefix)}-UT-CAND-[0-9]{{2}}", text))
        assert len(candidate_ids) == surface["l6_ut_candidate_count"]
        observed_ut_candidates += len(candidate_ids)
assert frozen_existing_pairs == {"GOV-CODING-RULE", "GOV-DDD-REGISTRY"}
assert current_scope_l6_designs == set(governance_surfaces) - frozen_existing_pairs
assert governance_coverage["summary"]["l6_function_contracts_checked"] == observed_function_contracts
assert governance_coverage["summary"]["current_scope_l6_ut_candidate_viewpoints"] == observed_ut_candidates
assert workflow_coverage["schema_version"] == "l1_l6_workflow_automation_coverage_v1"
assert workflow_coverage["status"] == "current_scope_l1_l6_workflow_automation_design_covered"
assert workflow_coverage["boundary"]["l7_work_requested_by_user"] is False
assert workflow_coverage["boundary"]["l7_work_requires_feature_ticket"] is True
assert workflow_coverage["boundary"]["workflow_map_is_implementation_evidence"] is False
assert workflow_coverage["boundary"]["right_arm_execution_gate_implementation_done"] is False
assert workflow_coverage["boundary"]["ci_or_equivalent_connected"] is False
assert workflow_coverage["boundary"]["helix_db_write_adoption_done"] is False
assert workflow_coverage["boundary"]["schema_migration_done"] is False
assert workflow_coverage["boundary"]["external_tool_executed"] is False
assert workflow_coverage["boundary"]["external_tool_installed"] is False
assert workflow_coverage["boundary"]["goal_complete_allowed"] is False
assert workflow_coverage["summary"] == {
    "workflow_surfaces_checked": 6,
    "automation_surfaces_checked": 9,
    "automation_trigger_contracts_checked": 9,
    "db_registry_targets_mapped": 9,
    "detector_gate_routes_mapped": 7,
    "cross_audit_convergence_rows_checked": 6,
    "deferred_feature_entry_points_checked": 7,
    "parked_feature_entry_points_checked": 0,
    "blocking_findings_current_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
workflow_surfaces = {item["id"]: item for item in workflow_coverage["workflow_surfaces"]}
assert set(workflow_surfaces) == {
    "WF-FORWARD-L0-L14",
    "WF-PAIR-FREEZE-L1-L6",
    "WF-REQUIREMENT-DRIFT",
    "WF-VG-OVERVIEW",
    "WF-DB-FEEDBACK",
    "WF-HARNESS-TOOL-ADMISSION",
}
assert workflow_coverage["summary"]["workflow_surfaces_checked"] == len(workflow_surfaces)
automation_surfaces = {item["id"]: item for item in workflow_coverage["automation_surfaces"]}
assert workflow_coverage["summary"]["automation_surfaces_checked"] == len(automation_surfaces)
assert workflow_coverage["automation_trigger_policy"] == {
    "current_scope_action": "define_trigger_contract_only",
    "trigger_execution_added_now": False,
    "db_write_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "external_tool_execution_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "required_contract_fields": [
        "automation_id",
        "trigger_source",
        "required_input",
        "normalized_output",
        "db_target",
        "detector_or_gate_route",
        "deferred_feature_ticket_id",
        "forbidden_current_scope",
        "completion_guard",
    ],
}
trigger_contracts = {
    item["automation_id"]: item
    for item in workflow_coverage["automation_trigger_contracts"]
}
assert set(trigger_contracts) == set(automation_surfaces)
assert workflow_coverage["summary"]["automation_trigger_contracts_checked"] == len(trigger_contracts)
trigger_ticket_ids = {
    item["id"]
    for item in workflow_coverage["deferred_feature_policy"]["feature_tickets"]
}
expected_forbidden_by_automation = {
    "AUTO-PLAN-REGISTRY": "plan_registry_import",
    "AUTO-TRANSITION-HISTORY": "transition_history_write",
    "AUTO-GATE-PASS": "gate_pass_write",
    "AUTO-DRIFT-DETECTOR": "detector_auto_execution",
    "AUTO-VG-OVERVIEW": "right_arm_gate_execution",
    "AUTO-FEEDBACK-SNAPSHOT": "feedback_event_write_adoption",
    "AUTO-DOCUMENT-PROJECTION": "contract_registry_write",
    "AUTO-TOOL-ADMISSION": "external_tool_execution",
    "AUTO-HANDOVER-BOUNDARY": "handover_metadata_write",
}
for automation_id, contract in trigger_contracts.items():
    surface = automation_surfaces[automation_id]
    assert contract["db_target"] == surface["db_target"]
    assert contract["required_input"] == surface["required_input"]
    assert not surface["current_l1_l6_evidence"].startswith("docs/v2/L7-test-design/")
    assert (root / surface["current_l1_l6_evidence"]).exists(), (
        automation_id,
        surface["current_l1_l6_evidence"],
    )
    assert contract["deferred_feature_ticket_id"] in trigger_ticket_ids
    assert contract["completion_guard"].startswith("trigger_contract_is_not_")
    assert expected_forbidden_by_automation[automation_id] in contract["forbidden_current_scope"]
db_targets = [item["db_target"] for item in automation_surfaces.values()]
assert len(set(db_targets)) == len(db_targets)
assert workflow_coverage["summary"]["db_registry_targets_mapped"] == len(db_targets)
assert set(db_targets) == {
    "plan_registry",
    "transition_history",
    "gate_pass",
    "detector_report",
    "gate_projection",
    "feedback_event",
    "contract_registry",
    "external_tool_candidate",
    "handover_state",
}
assert workflow_coverage["db_convergence_policy"] == {
    "current_scope_action": "design_map_only",
    "writes_allowed_now": False,
    "schema_migration_allowed_now": False,
    "plan_registry_import_done": False,
    "append_only_feedback_until_approved_l7": True,
    "candidate_is_not_closure": True,
    "forward_vmodel_return_required_before_completion": True,
}
convergence = workflow_coverage["cross_audit_convergence_contract"]
assert convergence["current_scope_action"] == "prove_db_feedback_dependency_workflow_alignment_only"
assert convergence["sources_checked"] == [
    "db_registration_readiness",
    "db_feedback_lifecycle",
    "dependency_impact_readiness",
    "workflow_automation",
]
assert convergence["rows_checked"] == 6
assert convergence["db_write_done"] is False
assert convergence["schema_migration_done"] is False
assert convergence["query_cli_done"] is False
assert convergence["trigger_execution_added_now"] is False
assert convergence["feedback_auto_apply_done"] is False
assert convergence["l7_or_external_execution_allowed_now"] is False
assert convergence["required_alignment_fields"] == [
    "db_target",
    "registration_or_projection_source",
    "workflow_automation_id",
    "dependency_projection_or_output",
    "feedback_lifecycle_state",
    "detector_or_route",
    "completion_guard",
]
convergence_rows = {item["db_target"]: item for item in convergence["rows"]}
assert set(convergence_rows) == {
    "plan_registry",
    "detector_report",
    "gate_projection",
    "feedback_event",
    "contract_registry",
    "handover_state",
}
assert workflow_coverage["summary"]["cross_audit_convergence_rows_checked"] == len(convergence_rows)
allowed_dependency_outputs = {
    "affected_plans",
    "impact_seed",
    "affected_gates",
    "feedback_refs",
    "affected_design_docs",
    "resume_state_candidate",
}
for row in convergence_rows.values():
    assert row["workflow_automation_id"] in automation_surfaces
    assert row["db_target"] == automation_surfaces[row["workflow_automation_id"]]["db_target"]
    assert row["dependency_projection_or_output"] in allowed_dependency_outputs
    assert (
        row["completion_guard"].endswith("_is_not_closure")
        or row["completion_guard"].startswith("trigger_contract_is_not_")
        or row["completion_guard"] == "projection_contract_is_not_db_write"
    )
assert workflow_coverage["route_policy"] == {
    "current_scope_action": "map_detector_to_gate_only",
    "gate_execution_done": False,
    "gate_promotion_done": False,
    "feedback_auto_apply_done": False,
    "route_mapping_is_not_completion_evidence": True,
    "evidence_must_not_use_l7_test_design": True,
}
routes = {item["route_id"]: item for item in workflow_coverage["detector_gate_routes"]}
assert set(routes) == {
    "ROUTE-L1-L6-REQUIREMENT-DRIFT",
    "ROUTE-L1-L6-PAIR-BALANCE",
    "ROUTE-L1-L6-GOVERNANCE",
    "ROUTE-L1-L6-DB-FEEDBACK",
    "ROUTE-L1-L6-HARNESS-TOOLS",
    "ROUTE-L1-L6-CODEX-CLAUDE-GUARD-PARITY",
    "ROUTE-L1-L6-HANDOVER-BOUNDARY",
}
assert workflow_coverage["summary"]["detector_gate_routes_mapped"] == len(routes)
feature_tickets = {
    item["id"]: item
    for item in workflow_coverage["deferred_feature_policy"]["feature_tickets"]
}
assert set(feature_tickets) == {
    "full_flow_remaining_guards",
    "db_evidence_lifecycle",
    "harness_external_tools",
    "codex_claude_guard_parity",
    "fr_registry_glossary",
    "plan_registry_add_feature_import",
    "phase_enum_l0_l14_runtime_retrofit",
}
assert feature_tickets["db_evidence_lifecycle"]["unlocks"] == [
    "DB write connection",
    "document auto-registration projection",
    "feedback loop candidate persistence",
    "recurrence closure implementation",
]
assert workflow_coverage["summary"]["deferred_feature_entry_points_checked"] == len(feature_tickets)
parked_feature_tickets = {
    item["id"]: item
    for item in workflow_coverage["deferred_feature_policy"]["parked_feature_tickets"]
}
assert parked_feature_tickets == {}
current_scope_authorized_tickets = {
    item["id"]: item
    for item in workflow_coverage["deferred_feature_policy"]["current_scope_authorized_feature_tickets"]
}
assert set(current_scope_authorized_tickets) == {"detector_failclose_ci_gate"}
detector_gate_ticket = current_scope_authorized_tickets["detector_failclose_ci_gate"]
assert detector_gate_ticket["status"] == "active_ci_enforcement"
assert detector_gate_ticket["current_task_scope"] == "ci_enforcement_and_boundary_unpark"
assert detector_gate_ticket["ticket_is_completion_evidence"] is False
assert detector_gate_ticket["unlocks"] == [
    "CI gate connection",
    "automation-gate hardening",
]
assert detector_gate_ticket["still_parked"] == [
    "detector fail-close promotion",
]
assert workflow_coverage["summary"]["parked_feature_entry_points_checked"] == 0
for refs in workflow_coverage["sources"].values():
    for ref in refs:
        assert not ref.startswith("docs/v2/L7-test-design/"), ref
        assert (root / ref).exists(), ref
evidence_paths = {ref for refs in workflow_coverage["sources"].values() for ref in refs}
for surface in workflow_surfaces.values():
    assert (root / surface["source"]).exists(), surface["source"]
    assert surface["automation_connection"], surface["id"]
    assert surface["current_scope_status"]
    assert "implementation_done" not in surface["current_scope_status"]
for route in routes.values():
    assert not route["current_scope_evidence"].startswith("docs/v2/L7-test-design/")
    assert (root / route["current_scope_evidence"]).exists(), route
    assert route["gates"], route["route_id"]
    assert route["current_scope_evidence"] in evidence_paths
for ticket in feature_tickets.values():
    assert ticket["path"].startswith("docs/plans/add-feature/"), ticket["id"]
    assert (root / ticket["path"]).exists(), ticket["id"]
    assert ticket["unlocks"], ticket["id"]
assert reference_integrity["schema_version"] == "l1_l6_reference_integrity_coverage_v1"
assert reference_integrity["status"] == "current_scope_l1_l6_reference_integrity_clean"
assert reference_integrity["boundary"]["l7_work_requested_by_user"] is False
assert reference_integrity["boundary"]["current_scope_uses_l7_as_completion_evidence"] is False
assert reference_integrity["boundary"]["goal_complete_allowed"] is False
assert reference_integrity["summary"] == {
    "audit_files_checked": 25,
    "path_like_refs_checked": 1384,
    "direct_file_refs_checked": 1375,
    "glob_patterns_checked": 9,
    "missing_direct_file_refs": 0,
    "empty_glob_patterns": 0,
    "blocking_findings_current_scope": 0,
}
glob_patterns = {
    item["pattern"]: item["match_count"]
    for item in reference_integrity["glob_patterns"]
}
assert glob_patterns == {
    "docs/v2/L6-functional-design/**/function-spec.md": 18,
    "docs/v2/L6-functional-design/**/*function-spec.md": 18,
    "docs/v2/L1-requirements/**/*.md": 5,
    "docs/v2/L3-requirements/**/*.md": 4,
    "docs/v2/L4*/**/*.md": 6,
    "docs/v2/L5*/**/*.md": 6,
    "docs/v2/L6*/**/*.md": 27,
    "docs/v2/audit/2026-06-12-*.yaml": 21,
    "docs/plans/add-feature/add-feature-*.md": 24,
}
bundle_alignment = reference_integrity["bundle_alignment_contract"]
ratification = yaml.safe_load((root / bundle_alignment["ratification_index"]).read_text(encoding="utf-8"))
assert bundle_alignment["ratification_sources_considered"] == [
    "objective_audit",
    "core_audit_bundle",
    "integrity_audits",
]
assert bundle_alignment["reference_bundle_policy"] == "yaml_audit_bundle_only"
ratification_sources = set()
for group in bundle_alignment["ratification_sources_considered"]:
    ratification_sources.update(ratification["sources"][group])
reference_sources = set(reference_integrity["sources"]["audit_bundle"])
assert sorted(reference_sources - ratification_sources) == bundle_alignment[
    "required_in_reference_not_ratification"
]
assert sorted(ratification_sources - reference_sources) == bundle_alignment[
    "allowed_in_ratification_not_reference"
]
assert "structured YAML bundle" in bundle_alignment["reason"]
bundle_completeness = reference_integrity["bundle_completeness_contract"]
all_current_yaml_audits = {
    str(path.relative_to(root))
    for path in sorted((root / "docs/v2/audit").glob("2026-06-12-*.yaml"))
}
assert bundle_completeness["glob_pattern"] == "docs/v2/audit/2026-06-12-*.yaml"
assert bundle_completeness["glob_match_count"] == len(all_current_yaml_audits)
explicit_current_scope_audits = set(
    bundle_completeness["explicit_current_scope_audits"]
)
assert explicit_current_scope_audits == {
    "docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml",
    "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml",
    "docs/v2/audit/2026-06-13-l1-l6-harness-pre-adoption-requirements-acceptance.yaml",
    "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml",
    "docs/v2/audit/2026-06-13-l1-l6-nfr-derivation-coverage.yaml",
}
assert bundle_completeness["policy"] == (
    "every_current_date_yaml_audit_and_explicit_current_scope_audit_is_indexed_or_self_reference_integrity"
)
assert set(bundle_completeness["allowed_not_in_audit_bundle"]) == {
    "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml"
}
assert bundle_completeness["orphan_yaml_audits"] == []
assert all_current_yaml_audits | explicit_current_scope_audits == reference_sources | set(
    bundle_completeness["allowed_not_in_audit_bundle"]
)
markdown_contract = reference_integrity["markdown_read_path_contract"]
grain_text = (root / markdown_contract["grain_balance_audit"]).read_text(encoding="utf-8")
markdown_refs = list(iter_markdown_path_refs(grain_text))
markdown_direct_refs = [ref for ref in markdown_refs if "*" not in ref]
markdown_glob_refs = [ref for ref in markdown_refs if "*" in ref]
assert markdown_contract["extracted_path_refs"] == len(markdown_refs)
assert markdown_contract["direct_path_refs"] == len(markdown_direct_refs)
assert markdown_contract["glob_path_refs"] == len(markdown_glob_refs)
assert markdown_contract["missing_direct_file_refs"] == sum(
    1 for ref in markdown_direct_refs if not (root / ref).exists()
)
assert markdown_contract["empty_glob_patterns"] == sum(
    1 for ref in markdown_glob_refs if not list(root.glob(ref))
)
assert markdown_contract["glob_patterns"] == {
    pattern: len(list(root.glob(pattern)))
    for pattern in sorted(set(markdown_glob_refs))
}
assert markdown_contract["l7_terms_allowed_only_as_boundary"] is True
for phrase in markdown_contract["required_l7_boundary_phrases"]:
    assert phrase in grain_text
for ref in reference_integrity["sources"]["audit_bundle"]:
    assert (root / ref).exists(), ref
structured_refs = []
for ref in reference_integrity["sources"]["audit_bundle"]:
    if not ref.endswith(".yaml"):
        continue
    with open(root / ref, encoding="utf-8") as handle:
        structured_refs.extend(iter_structured_path_refs(yaml.safe_load(handle)))
glob_refs = [ref for ref in structured_refs if "*" in ref]
direct_refs = [ref for ref in structured_refs if "*" not in ref]
assert reference_integrity["summary"]["path_like_refs_checked"] == len(structured_refs)
assert reference_integrity["summary"]["direct_file_refs_checked"] == len(direct_refs)
assert reference_integrity["summary"]["glob_patterns_checked"] == len(glob_refs)
assert ".helix/handover/CURRENT.md" in direct_refs
for pattern, expected_count in glob_patterns.items():
    assert len(list(root.glob(pattern))) == expected_count
assert double_check["schema_version"] == "l1_l6_double_check_coverage_v1"
assert double_check["status"] == "current_scope_l1_l6_quantitative_and_qualitative_check_pass"
assert double_check["boundary"]["l7_work_requested_by_user"] is False
assert double_check["boundary"]["quantitative_pass_is_full_completion"] is False
assert double_check["boundary"]["qualitative_pass_is_full_completion"] is False
assert double_check["boundary"]["goal_complete_allowed"] is False
assert double_check["summary"] == {
    "quantitative_checks": 21,
    "quantitative_checks_pass": 21,
    "qualitative_checks": 36,
    "qualitative_checks_pass": 36,
    "blocking_findings_current_scope": 0,
    "current_scope_verdict": "pass_l1_l6_only",
}
quantitative = {item["id"]: item for item in double_check["quantitative_checks"]}
qualitative = {item["id"]: item for item in double_check["qualitative_checks"]}
assert len(quantitative) == 21
assert double_check["summary"]["quantitative_checks"] == len(quantitative)
assert double_check["summary"]["quantitative_checks_pass"] == sum(
    1 for item in quantitative.values() if item["verdict"] == "pass"
)
assert double_check["summary"]["qualitative_checks"] == len(qualitative)
assert double_check["summary"]["qualitative_checks_pass"] == sum(
    1 for item in qualitative.values() if item["verdict"] == "pass"
)
source_groups = set(double_check["sources"]["objective_audit"])
source_groups.update(double_check["sources"]["quantitative_sources"])
source_groups.update(double_check["sources"]["qualitative_sources"])
used_sources = {
    item["source"]
    for item in list(quantitative.values()) + list(qualitative.values())
}
assert used_sources == source_groups
assert all(
    not ref.startswith("docs/v2/L7-test-design/")
    for refs in double_check["sources"].values()
    for ref in refs
)
assert "Q-L0-L14-FLOW-SURFACE" in quantitative
assert "Q-L0-PLANNING-DERIVATION" in quantitative
assert quantitative["Q-L0-PLANNING-DERIVATION"]["expected"] == {
    "l0_problem_axes_checked": 10,
    "l0_problem_axes_with_l1_l6_design_evidence": 10,
    "problem_axis_rows_with_mapped_requirements": 10,
    "problem_axis_rows_with_l4_l6_design_evidence": 10,
    "problem_axis_rows_with_audit_evidence": 10,
    "l0_target_areas_checked": 10,
    "l0_target_areas_with_l1_l6_design_evidence": 10,
    "target_area_rows_with_current_scope_evidence": 10,
    "rows_with_current_scope_result": 20,
    "l0_to_l1_l6_derivation_gaps": 0,
    "l1_l6_audit_sources_declared": 13,
    "row_audit_refs_checked": 32,
    "unique_row_audit_refs_checked": 11,
    "undeclared_row_audit_refs": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
assert quantitative["Q-L6-ASSET-PARTITION"]["expected"] == {
    "l6_assets_partitioned": True,
    "l6_partition_overlap_allowed": False,
    "l6_partition_clusters": 3,
    "fr_function_specs": 18,
    "detector_and_governance_specs": 7,
    "deferred_extension_specs": 3,
}
assert quantitative["Q-REFERENCE-INTEGRITY"]["expected"] == {
    "audit_files_checked": reference_integrity["summary"]["audit_files_checked"],
    "path_like_refs_checked": reference_integrity["summary"]["path_like_refs_checked"],
    "direct_file_refs_checked": reference_integrity["summary"]["direct_file_refs_checked"],
    "glob_patterns_checked": reference_integrity["summary"]["glob_patterns_checked"],
    "missing_direct_file_refs": 0,
    "empty_glob_patterns": 0,
}
assert quantitative["Q-HARNESS-TOOLS"]["expected"] == {
    "official_sources_checked": harness_coverage["summary"]["official_sources_checked"],
    "tool_candidates_checked": harness_coverage["summary"]["tool_candidates_checked"],
    "tool_intake_contracts_checked": harness_coverage["summary"]["tool_intake_contracts_checked"],
    "tool_intake_required_fields_checked": harness_coverage["summary"]["tool_intake_required_fields_checked"],
    "tool_intake_forbidden_common_rules_checked": harness_coverage["summary"]["tool_intake_forbidden_common_rules_checked"],
    "admission_gate_contracts_checked": harness_coverage["summary"]["admission_gate_contracts_checked"],
    "admission_gate_required_fields_checked": harness_coverage["summary"]["admission_gate_required_fields_checked"],
    "admission_owner_roles_checked": harness_coverage["summary"]["admission_owner_roles_checked"],
    "tool_output_ingestion_contracts_checked": harness_coverage["summary"]["tool_output_ingestion_contracts_checked"],
    "tool_output_required_fields_checked": harness_coverage["summary"]["tool_output_required_fields_checked"],
    "tool_output_detector_signals_checked": harness_coverage["summary"]["tool_output_detector_signals_checked"],
    "l6_functions_defined": harness_coverage["summary"]["l6_functions_defined"],
    "l6_unit_test_viewpoints_defined": harness_coverage["summary"]["l6_unit_test_viewpoints_defined"],
    "adoption_recheck_controls_checked": harness_coverage["summary"]["adoption_recheck_controls_checked"],
    "pre_adoption_requirement_contracts_checked": harness_coverage["summary"]["pre_adoption_requirement_contracts_checked"],
    "current_session_web_fetch_sources_checked": harness_coverage["summary"]["current_session_web_fetch_sources_checked"],
    "current_session_web_fetch_refs_checked": harness_coverage["summary"]["current_session_web_fetch_refs_checked"],
    "latest_core_rechecked_sources_checked": harness_coverage[
        "adoption_recheck_scope_contract"
    ]["latest_core_rechecked_sources_checked"],
    "all_candidate_sources_checked": harness_coverage[
        "adoption_recheck_scope_contract"
    ]["all_candidate_sources_checked"],
    "spot_recheck_sources_checked": harness_coverage[
        "adoption_recheck_scope_contract"
    ]["spot_recheck_sources_checked"],
    "adoption_control_sources_are_subset_of_latest_core_rechecked_sources": (
        harness_coverage["adoption_recheck_scope_contract"][
            "adoption_control_sources_are_subset_of_latest_core_rechecked_sources"
        ]
    ),
    "adoption_control_sources_are_subset_of_spot_recheck_sources": (
        harness_coverage["adoption_recheck_scope_contract"][
            "adoption_control_sources_are_subset_of_spot_recheck_sources"
        ]
    ),
    "all_candidate_source_ids_must_match_canonical_source_ids": (
        harness_coverage["adoption_recheck_scope_contract"][
            "all_candidate_source_ids_must_match_canonical_source_ids"
        ]
    ),
    "spot_recheck_sources_are_subset_of_canonical_source_ids": (
        harness_coverage["adoption_recheck_scope_contract"][
            "spot_recheck_sources_are_subset_of_canonical_source_ids"
        ]
    ),
    "spot_recheck_is_not_full_candidate_recheck": (
        harness_coverage["adoption_recheck_scope_contract"][
            "spot_recheck_is_not_full_candidate_recheck"
        ]
    ),
}
assert quantitative["Q-GOVERNANCE"]["expected"]["governance_finding_normalization_contracts_checked"] == 6
assert quantitative["Q-GOVERNANCE"]["expected"]["governance_detection_routes_checked"] == 6
assert quantitative["Q-GOVERNANCE"]["expected"]["governance_control_closure_rows_checked"] == 6
assert quantitative["Q-IMPROVEMENT-CANDIDATES"]["expected"] == {
    "total_candidates": improvement["candidate_summary"]["total_candidates"],
    "candidates_adopted": False,
}
assert len(qualitative) == 36
assert "Q-BOTTLENECK-REMEDIATION-READINESS" in quantitative
assert quantitative["Q-BOTTLENECK-REMEDIATION-READINESS"]["expected"]["cross_axis_aggregation_contracts_checked"] == 4
assert "Q-FULL-OBJECTIVE-GAP-STATUS" in quantitative
deferred_feature_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml").read_text(encoding="utf-8")
)
full_objective_expected = quantitative["Q-FULL-OBJECTIVE-GAP-STATUS"]["expected"]
assert full_objective_expected["repository_add_feature_files_discovered"] == (
    deferred_feature_coverage["summary"]["repository_add_feature_files_discovered"]
)
assert full_objective_expected["current_objective_deferred_feature_tickets"] == (
    deferred_feature_coverage["summary"]["current_objective_deferred_feature_tickets"]
)
assert full_objective_expected["out_of_current_objective_add_feature_files"] == (
    deferred_feature_coverage["summary"]["out_of_current_objective_add_feature_files"]
)
assert full_objective_expected["out_of_current_objective_completed_add_features"] == (
    deferred_feature_coverage["summary"]["out_of_current_objective_completed_add_features"]
)
assert full_objective_expected["out_of_current_objective_parked_feature_tickets"] == (
    deferred_feature_coverage["summary"]["out_of_current_objective_parked_feature_tickets"]
)
assert "Q-RATIFICATION-INDEX" in quantitative
assert "Q-EXIT-CRITERIA" in quantitative
assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"]["automation_surfaces_checked"] == 9
assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"]["automation_trigger_contracts_checked"] == 9
assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"]["cross_audit_convergence_rows_checked"] == 6
assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"]["registration_event_contracts_checked"] == 6
assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"]["document_projection_contracts_checked"] == 5
assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"]["lifecycle_route_contracts_checked"] == 6
assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"]["event_route_closure_rows_checked"] == 6
assert "L-BOTTLENECK-REMEDIATION-NOT-CLOSURE" in qualitative
current_audit_paths = [
    root / ref for ref in reference_integrity["sources"]["audit_bundle"]
]
missing_completion_denial = []
for audit_path in sorted(current_audit_paths):
    with open(audit_path, encoding="utf-8") as handle:
        audit_payload = yaml.safe_load(handle)
    if not isinstance(audit_payload.get("completion_denial"), dict):
        missing_completion_denial.append(str(audit_path.relative_to(root)))
assert qualitative["L-AUDIT-MANIFEST-PROJECTION"]["expected"] == {
    "doc_kind": "audit_manifest",
    "db_target": "detector_report",
    "required_key": "completion_denial",
    "missing_completion_denial": [],
    "completion_guard": "projection_contract_is_not_db_write",
    "helix_db_write_performed": False,
}
assert missing_completion_denial == qualitative["L-AUDIT-MANIFEST-PROJECTION"][
    "expected"
]["missing_completion_denial"]
assert "L-FULL-OBJECTIVE-ACTIVE" in qualitative
assert "L-WEB-EVIDENCE-FRESHNESS" in qualitative
assert "L-CONTRACT-DESIGN-WEB-EVIDENCE-SEPARATION" in qualitative
assert "L-FEATURE-TICKET-FRONTMATTER" in qualitative
assert "L-FEATURE-TICKET-UNLOCK-CONDITIONS" in qualitative
assert "L-CONTRACT-DESIGN-ESCALATION-BOUNDARY" in qualitative
assert "L-HANDOVER-BOUNDARY" in qualitative
assert "L-RATIFICATION-NOT-CLOSURE" in qualitative
assert "L-FULL-GOAL-UNLOCK-EVIDENCE-INDEX" in qualitative
assert "L-FULL-GOAL-UNLOCK-FEATURE-TICKET-RESOLUTION" in qualitative
assert "L-FULL-GOAL-UNLOCK-NAMESPACE-NOT-PROOF" in qualitative
assert "L-L1-L6-DESIGN-OBLIGATION-NOT-FEATURE-ESCAPE" in qualitative
assert "L-HARNESS-ADOPTION-RECHECK" in qualitative
assert "L-HARNESS-CURRENT-SESSION-WEBFETCH-NOT-CLOSURE" in qualitative
assert "L-EXIT-CRITERIA-NOT-CLOSURE" in qualitative
assert "L-LEGACY-REFERENCE-CLASSIFICATION" in qualitative
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"] == {
    "legacy_reference_files_checked": 4,
    "legacy_reference_files_marked_or_already_marked": 4,
    "runtime_retrofit_required_items": 1,
    "runtime_metadata_gap_ticketed": True,
    "handover_metadata_boundary_items_checked": 1,
    "handover_current_json_l7_label_authorizes_work": False,
    "handover_ready_for_review_status_not_completion": True,
    "handover_next_action_is_authoritative": True,
    "next_action_supersedes_current_json_task_metadata": True,
    "safe_task_retitle_command_available_now": False,
    "force_dump_without_approval_allowed": False,
    "feature_ticket_metadata_matches_classification": True,
    "required_future_controls_checked": 4,
    "blocking_findings_current_l1_l6_scope": 0,
    "l7_artifacts_created_by_this_audit": 0,
}
runtime_retrofit = legacy_classification["runtime_retrofit_required"][0]
handover_boundary = legacy_classification["handover_metadata_boundary"][0]
runtime_feature_meta = yaml.safe_load(
    (root / runtime_retrofit["feature_ticket"]).read_text(encoding="utf-8").split("---", 2)[1]
)
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "runtime_retrofit_required_items"
] == legacy_classification["summary"]["runtime_retrofit_required_items"]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "runtime_metadata_gap_ticketed"
] is bool(runtime_retrofit["observed_metadata_gap"])
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "handover_metadata_boundary_items_checked"
] == legacy_classification["summary"]["handover_metadata_boundary_items_checked"]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "handover_current_json_l7_label_authorizes_work"
] == legacy_classification["summary"]["handover_current_json_l7_label_authorizes_work"]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "handover_ready_for_review_status_not_completion"
] == legacy_classification["summary"]["handover_ready_for_review_status_not_completion"]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "handover_next_action_is_authoritative"
] == legacy_classification["summary"]["handover_next_action_is_authoritative"]
assert handover_boundary["observed_machine_state"]["task_title_contains_l7"] is True
assert handover_boundary["authoritative_boundary"]["l7_work_requested_by_user"] is False
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "next_action_supersedes_current_json_task_metadata"
] == runtime_retrofit["observed_metadata_gap"][
    "next_action_supersedes_current_json_task_metadata"
]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "safe_task_retitle_command_available_now"
] == runtime_retrofit["observed_metadata_gap"][
    "safe_task_retitle_command_available_now"
]
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "force_dump_without_approval_allowed"
] == runtime_retrofit["observed_metadata_gap"][
    "force_dump_without_approval_allowed"
]
assert runtime_retrofit["feature_ticket_metadata_must_match_observed_gap"] is True
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "feature_ticket_metadata_matches_classification"
] is True
assert runtime_feature_meta["observed_metadata_gap"] == {
    "current_json_legacy_task_title": runtime_retrofit["observed_metadata_gap"][
        "current_json_legacy_task_title_possible"
    ],
    "current_json_legacy_phase_label": runtime_retrofit["observed_metadata_gap"][
        "current_json_legacy_phase_label_possible"
    ],
    "task_retitle_update_command_available_now": runtime_retrofit[
        "observed_metadata_gap"
    ]["safe_task_retitle_command_available_now"],
    "next_action_must_remain_authoritative": runtime_retrofit[
        "observed_metadata_gap"
    ]["next_action_supersedes_current_json_task_metadata"],
    "force_dump_required_for_retitle_without_runtime_change": True,
    "force_dump_allowed_without_approval": runtime_retrofit["observed_metadata_gap"][
        "force_dump_without_approval_allowed"
    ],
}
assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
    "required_future_controls_checked"
] == len(runtime_retrofit["required_future_controls"])
assert qualitative["L-FULL-GOAL-UNLOCK-EVIDENCE-INDEX"]["expected"] == {
    "full_goal_unlock_evidence_classes_indexed": 8,
    "source_contract": "full_goal_completion_unlock_evidence_contract",
    "index_is_completion_evidence": False,
    "l7_db_ci_external_execution_allowed_by_index": False,
}
assert qualitative["L-FULL-GOAL-UNLOCK-FEATURE-TICKET-RESOLUTION"]["expected"] == {
    "full_goal_unlock_required_feature_tickets_resolved": 8,
    "feature_ticket_resolution_source": "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml",
    "feature_ticket_resolution_contract": "full_goal_completion_unlock_evidence_contract.feature_ticket_resolution_contract",
    "feature_tickets_are_routes_not_evidence": True,
    "l7_execution_allowed_by_resolution": False,
}
assert qualitative["L-FULL-GOAL-UNLOCK-NAMESPACE-NOT-PROOF"]["expected"] == {
    "evidence_namespace": "full_goal_unlock_required_evidence_not_current_scope_proof",
    "required_evidence_is_current_scope_proof": False,
    "required_evidence_is_completion_evidence_now": False,
    "required_feature_ticket_is_completion_evidence": False,
    "may_satisfy_completion_only_after_approval_and_execution": True,
}
assert qualitative["L-HARNESS-ADOPTION-RECHECK"]["expected"] == {
    "controls_checked": 3,
    "controls_apply_before": [
        "install",
        "enable_mcp_server",
        "plugin_adoption",
        "external_execution",
        "ci_or_equivalent_connection",
        "helix_db_ingestion",
    ],
    "all_controls_require_new_recheck_before_adoption": True,
    "latest_core_rechecked_sources_checked": 5,
    "all_candidate_sources_checked": 33,
    "spot_recheck_sources_checked": 8,
    "adoption_control_sources_are_subset_of_latest_core_rechecked_sources": True,
    "adoption_control_sources_are_subset_of_spot_recheck_sources": True,
    "all_candidate_source_ids_must_match_canonical_source_ids": True,
    "spot_recheck_sources_are_subset_of_canonical_source_ids": True,
    "spot_recheck_is_not_full_candidate_recheck": True,
    "non_core_candidates_require_new_recheck_before_adoption": True,
    "all_candidates_remain_gated_by_admission_gate_contracts": True,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
assert qualitative["L-HARNESS-CURRENT-SESSION-WEBFETCH-NOT-CLOSURE"]["expected"] == {
    "source_contract": "current_session_web_fetch_recheck_2026_06_13",
    "official_sources_checked": 5,
    "web_fetch_confirmed": True,
    "current_scope_is_completion_evidence": False,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "ci_or_equivalent_connection_allowed_now": False,
    "l7_artifact_allowed_now": False,
    "result": "no_change_to_candidate_gate_status",
}
assert qualitative["L-L1-L6-DESIGN-OBLIGATION-NOT-FEATURE-ESCAPE"]["expected"] == {
    "current_scope_action": "prove_l1_l6_design_obligation_before_deferring_l7_execution",
    "l1_l6_design_obligation_is_current_scope": True,
    "deferred_feature_tickets_are_not_design_substitute": True,
    "feature_ticket_allowed_only_for_unapproved_l7_or_escalation_bound_execution": True,
    "l1_l6_design_assets_required_before_ticket": True,
    "design_gap_reopened_if_l1_l6_evidence_missing": True,
    "no_feature_escape_for_design_debt": True,
    "l7_or_external_execution_requires_approved_feature_ticket": True,
    "covered_current_scope_surfaces": 6,
}
assert "L-EVIDENCE-BOUNDARY-SCAN" in qualitative
assert "L-DOC-REVIEW-4C-GRAIN" in qualitative
assert qualitative["L-DOC-REVIEW-4C-GRAIN"]["expected"] == {
    "correctness": "pass",
    "completeness": "pass",
    "consistency": "pass",
    "clarity": "pass",
    "l7_completion_evidence": False,
}
grain_text = (root / "docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md").read_text(encoding="utf-8")
for term in (
    "Correctness",
    "Completeness",
    "Consistency",
    "Clarity",
    "L7 実装、L7 単体テスト設計、DB write",
):
    assert term in grain_text
evidence_keys = {
    "proof",
    "evidence",
    "current_scope_evidence",
    "current_l1_l6_evidence",
    "source_evidence",
    "machine_evidence",
    "coverage_evidence",
    "authoritative_evidence_keys",
    "evidence_refs",
    "evidence_paths",
    "evidence_files",
    "proof_source",
    "proof_sources",
    "proof_refs",
    "proof_paths",
    "proof_files",
    "evidence_source",
    "evidence_sources",
}
evidence_like_keys = [
    "authoritative_evidence_keys",
    "evidence_refs",
    "evidence_paths",
    "evidence_files",
    "proof_source",
    "proof_sources",
    "proof_refs",
    "proof_paths",
    "proof_files",
    "evidence_source",
    "evidence_sources",
]
boundary_refs = 0
evidence_refs = 0
negative_boundary_check_refs = 0

def walk_boundary_refs(value, key_stack):
    global boundary_refs, evidence_refs, negative_boundary_check_refs
    if isinstance(value, dict):
        negative_boundary_context = (
            value.get("evidence_kind") == "negative_boundary_check"
            and value.get("counts_as_current_scope_completion_proof") is False
        )
        for key, child in value.items():
            next_stack = key_stack + [str(key)]
            if negative_boundary_context:
                next_stack = next_stack + ["negative_boundary_check_allowed"]
            walk_boundary_refs(child, next_stack)
        return
    if isinstance(value, list):
        for child in value:
            walk_boundary_refs(child, key_stack)
        return
    if not isinstance(value, str):
        return
    if not (
        "docs/plans/add-feature/" in value
        or "docs/v2/L7-test-design" in value
        or "../L7-test-design" in value
    ):
        return
    if any(key in evidence_keys for key in key_stack):
        if "negative_boundary_check_allowed" in key_stack:
            negative_boundary_check_refs += 1
        else:
            evidence_refs += 1
    else:
        boundary_refs += 1

assert any(
    str(path.relative_to(root))
    == "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
    for path in current_audit_paths
)

for audit_path in sorted(current_audit_paths):
    with open(audit_path, encoding="utf-8") as handle:
        walk_boundary_refs(yaml.safe_load(handle), [])
assert qualitative["L-EVIDENCE-BOUNDARY-SCAN"]["expected"] == {
    "evidence_key_match_policy": "exact_key_or_known_evidence_like_key",
    "evidence_like_keys_checked": evidence_like_keys,
    "boundary_context_refs": boundary_refs,
    "negative_boundary_check_refs": negative_boundary_check_refs,
    "evidence_context_refs": evidence_refs,
    "add_feature_or_l7_refs_in_proof_or_evidence": evidence_refs,
    "current_scope_proof_allows_add_feature": False,
    "current_scope_proof_allows_l7_test_design": False,
}
assert negative_boundary_check_refs == 1
assert evidence_refs == 0
assert qualitative["L-CODEX-CLAUDE-PARITY-ROUTES"]["expected"] == {
    "parity_gap_routes_checked": 8,
    "parity_route_required_fields_checked": 7,
    "parity_finding_normalization_contracts_checked": 8,
    "parity_normalization_required_fields_checked": 8,
    "parity_closure_requirements_checked": 8,
    "parity_closure_required_fields_checked": 6,
    "parity_accountability_current_scope_proves_checked": 4,
    "parity_accountability_current_scope_does_not_prove_checked": 4,
    "db_write_allowed_now": False,
    "hook_change_allowed_now": False,
    "fail_close_promotion_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
assert qualitative["L-WEB-EVIDENCE-FRESHNESS"]["expected"] == {
    "canonical_source_ids_checked": 33,
    "source_id_url_and_recheck_date_match": True,
    "install_execution_or_ci_connection_requires_new_recheck": True,
    "current_scope_revalidation_is_design_evidence_only": True,
}
assert qualitative["L-CONTRACT-DESIGN-WEB-EVIDENCE-SEPARATION"]["expected"] == {
    "linked_ticket_id": "contract_design_phase_label_retrofit",
    "reference_sources_checked": 3,
    "expected_source_ids": [
        "OPENAPI-SPEC-3-2-0",
        "JSON-SCHEMA-VALIDATION-2020-12",
        "POSTGRESQL-ALTER-TABLE-CURRENT",
    ],
    "applies_to": ["D-API", "D-CONTRACT", "D-DB"],
    "sources_are_harness_tool_candidates": False,
    "sources_are_completion_evidence": False,
    "contract_edit_performed": False,
    "schema_migration_done": False,
    "l7_work_performed": False,
}
deferred_feature_coverage = yaml.safe_load((root / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml").read_text())
assert qualitative["L-FEATURE-TICKET-FRONTMATTER"]["expected"] == {
    "feature_tickets_checked": 11,
    "workflow_required": "add-feature",
    "status_required": "draft",
    "ticket_is_completion_evidence": False,
    "current_scope_may_parse_ticket_metadata_only": True,
    "feature_unlock_routes_checked": 10,
    "feature_unlock_targets_are_completion_evidence": False,
    "latest_user_boundary": {
        "l7_requested_now": False,
        "l7_route": "add_feature_ticket_only",
        "forbidden_now_count": 5,
        "forbidden_now": [
            "L7 product feature implementation",
            "L7 product coverage closure",
            "write/adopt HELIX DB state",
            "install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate",
            "broad advisory→fail-close flip of W1 detectors",
        ],
    },
}
assert qualitative["L-FEATURE-TICKET-UNLOCK-CONDITIONS"]["expected"] == {
    "feature_tickets_with_unlock_conditions": 11,
    "required_feature_ticket_ids": deferred_feature_coverage[
        "feature_ticket_unlock_condition_contract"
    ]["required_feature_ticket_ids"],
    **{
        f"{ticket_id}_unlock_conditions": tokens
        for ticket_id, tokens in deferred_feature_coverage[
            "feature_ticket_unlock_condition_contract"
        ]["required_unlock_condition_tokens_by_ticket"].items()
    },
    "unlock_conditions_are_completion_evidence": False,
    "l7_execution_allowed_by_unlock_conditions": False,
}
assert qualitative["L-FEATURE-TICKET-UNLOCK-CONDITIONS"]["expected"][
    "feature_tickets_with_unlock_conditions"
] == deferred_feature_coverage["summary"]["feature_tickets_with_unlock_conditions"]
assert qualitative["L-FEATURE-TICKET-UNLOCK-CONDITIONS"]["expected"][
    "required_feature_ticket_ids"
] == deferred_feature_coverage["feature_ticket_unlock_condition_contract"][
    "required_feature_ticket_ids"
]
assert qualitative["L-CONTRACT-DESIGN-ESCALATION-BOUNDARY"]["expected"] == {
    "ticket_id": "contract_design_phase_label_retrofit",
    "ticket_kind": "add-design",
    "ticket_layer": "L5-L6",
    "escalation_required_for": ["D-API", "D-DB", "D-CONTRACT"],
    "current_scope_action": "record_boundary_only_no_contract_edit",
    "approval_required_before_contract_edit": True,
    "contract_edit_performed": False,
    "schema_migration_done": False,
    "l7_work_performed": False,
    "ticket_is_completion_evidence": False,
}
full_objective_gap_status = yaml.safe_load((root / "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml").read_text())
assert full_objective_gap_status["latest_user_boundary"] == {
    "l7_requested_now": False,
    "l7_route": "add_feature_ticket_only",
    "current_allowed_work": "L1-L6 audit/design/evidence cleanup, pre-L7 gate-hardening, current-scope CI enforcement, and add-feature ticket boundary mapping\n",
    "forbidden_now": [
        "L7 product feature implementation",
        "L7 product coverage closure",
        "write/adopt HELIX DB state",
        "install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate",
        "broad advisory→fail-close flip of W1 detectors",
    ],
}
assert deferred_feature_coverage["latest_user_boundary"] == full_objective_gap_status[
    "latest_user_boundary"
]
double_check_boundary = qualitative["L-FEATURE-TICKET-FRONTMATTER"]["expected"][
    "latest_user_boundary"
]
assert double_check_boundary["l7_requested_now"] == full_objective_gap_status[
    "latest_user_boundary"
]["l7_requested_now"]
assert double_check_boundary["l7_route"] == full_objective_gap_status[
    "latest_user_boundary"
]["l7_route"]
assert double_check_boundary["forbidden_now"] == full_objective_gap_status[
    "latest_user_boundary"
]["forbidden_now"]
assert double_check_boundary["forbidden_now_count"] == len(
    full_objective_gap_status["latest_user_boundary"]["forbidden_now"]
)
assert qualitative["L-HANDOVER-BOUNDARY"]["expected"] == {
    "handover_current_markdown": ".helix/handover/CURRENT.md",
    "handover_current_json": ".helix/handover/CURRENT.json",
    "handover_next_action_supersedes_legacy_task_title": True,
    "handover_next_action_supersedes_legacy_pending_entries": True,
    "legacy_task_title_must_not_authorize_l7": True,
    "legacy_pending_entries_must_not_authorize_l7": True,
    "l7_work_allowed_from_handover": False,
    "required_current_user_boundary_tokens": 4,
    "legacy_handover_suppression_tokens": 2,
}
assert all(item["verdict"] == "pass" for item in quantitative.values())
assert all(item["verdict"] == "pass" for item in qualitative.values())
for item in quantitative.values():
    assert item["id"].startswith("Q-"), item["id"]
    assert item["metric"], item["id"]
    assert item["expected"], item["id"]
    assert item["source"] in source_groups, item["id"]
    assert not item["source"].startswith("docs/v2/L7-test-design/"), item["id"]
for item in qualitative.values():
    assert item["id"].startswith("L-"), item["id"]
    assert item["check"], item["id"]
    assert item["source"] in source_groups, item["id"]
    assert not item["source"].startswith("docs/v2/L7-test-design/"), item["id"]
assert qualitative["L-BOUNDARY-L7"]["source"] == (
    "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml"
)
for refs in double_check["sources"].values():
    for ref in refs:
        assert (root / ref).exists(), ref
for item in list(quantitative.values()) + list(qualitative.values()):
    assert (root / item["source"]).exists(), item["id"]
assert "It does not prove L7 implementation" in double_check["completion_denial"]["reason"]
assert payload["l1_l6_supporting_evidence"]["asset_inventory"] == (
    "docs/v2/audit/2026-06-12-l1-l6-design-asset-inventory.yaml"
)
assert payload["l1_l6_supporting_evidence"]["improvement_candidate_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml"
)
assert payload["l1_l6_supporting_evidence"]["pair_balance_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml"
)
assert payload["l1_l6_supporting_evidence"]["guard_parity_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml"
)
assert payload["l1_l6_supporting_evidence"]["deferred_feature_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["db_feedback_lifecycle_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["harness_external_tools_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["governance_hardening_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["workflow_automation_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["db_registration_readiness_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["dependency_impact_readiness_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["bottleneck_remediation_readiness_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["full_objective_gap_status"] == (
    "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml"
)
assert payload["l1_l6_supporting_evidence"]["exit_criteria_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml"
)
assert payload["l1_l6_supporting_evidence"]["reference_integrity_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["double_check_coverage_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml"
)
assert payload["l1_l6_supporting_evidence"]["l1_l6_web_evidence_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml"
)
assert payload["l1_l6_supporting_evidence"]["fr31_trace_map"] == (
    "docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml"
)
deferred_feature_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml").read_text(encoding="utf-8")
)
expected_deferred_entry_points = {
    item["id"]: item["path"]
    for item in deferred_feature_coverage["feature_ticket_integrity"]
}
assert payload["deferred_feature_entry_points_contract"] == {
    "source": "source_deferred_feature_coverage_map",
    "source_collection": "feature_ticket_integrity",
    "source_key_field": "id",
    "source_path_field": "path",
    "expected_count": 11,
    "exact_match_required": True,
    "entries_are_boundary_metadata_only": True,
    "entries_are_completion_evidence": False,
    "l7_execution_allowed_by_entries": False,
}
assert payload["deferred_feature_entry_points"] == expected_deferred_entry_points
assert payload["deferred_feature_entry_points"] == {
    "fr_registry_glossary": "docs/plans/add-feature/add-feature-2026-06-12-fr-registry-glossary-l7-entry.md",
    "codex_claude_guard_parity": "docs/plans/add-feature/add-feature-2026-06-12-codex-claude-guard-parity-l7.md",
    "db_evidence_lifecycle": "docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md",
    "harness_external_tools": "docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md",
    "full_flow_remaining_guards": "docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md",
    "plan_registry_add_feature_import": "docs/plans/add-feature/add-feature-2026-06-12-plan-registry-add-feature-import-l7.md",
    "dependency_impact_query": "docs/plans/add-feature/add-feature-2026-06-12-dependency-impact-query-l7.md",
    "bottleneck_routing": "docs/plans/add-feature/add-feature-2026-06-12-bottleneck-routing-l7.md",
    "l7_unit_closure": "docs/plans/add-feature/add-feature-2026-06-13-l7-unit-closure.md",
    "phase_enum_l0_l14_runtime_retrofit": "docs/plans/add-feature/add-feature-2026-06-13-phase-enum-l0-l14-runtime-retrofit.md",
    "contract_design_phase_label_retrofit": "docs/plans/add-feature/add-feature-2026-06-13-contract-design-phase-label-retrofit.md",
}
assert "l1_l6_web_evidence_map" not in payload["deferred_feature_entry_points"]
assert "fr31_trace_map" not in payload["deferred_feature_entry_points"]
assert "approved L7 implementation where needed" in payload["completion_denial"]["missing"]
PY
  [ "$status" -eq 0 ]
}

@test "FR18 L6 unit-test-design index covers all specs without L7 artifacts" {
  run python3 - "$HELIX_ROOT/docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml" <<'PY'
import re
import sys
from pathlib import Path

import yaml

path = sys.argv[1]
root = Path(path).resolve().parents[3]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "fr18_l6_unit_test_design_index_v1"
assert payload["status"] == "current_scope_l6_unit_test_design_index"
assert payload["boundary"]["l6_unit_test_design_viewpoints_indexed"] is True
assert payload["boundary"]["l7_unit_test_design_artifacts_created"] is False
assert payload["boundary"]["goal_complete_allowed"] is False
assert payload["coverage_summary"]["fr_count"] == 18
assert payload["coverage_summary"]["specs_current_scope_l6_closed"] == 18
assert payload["coverage_summary"]["specs_with_l6_unit_test_design_viewpoints"] == 18
assert payload["coverage_summary"]["total_ut_candidates"] == 128
assert payload["coverage_summary"]["specs_with_draft_status"] == []
assert payload["coverage_summary"]["missing_l6_unit_test_design_viewpoint_specs"] == []
assert payload["coverage_summary"]["created_l7_fr_test_design_artifacts"] == []
assert len(payload["fr_specs"]) == 18
assert {
    item["fr_id"] for item in payload["fr_specs"]
} >= {"FR-FNREG-01", "FR-GLOSSARY-01", "FR-TDD-01", "FR-IMPACT-01"}
indexed_ut_candidate_total = sum(
    item["ut_candidate_count"] for item in payload["fr_specs"]
)
assert indexed_ut_candidate_total == payload["coverage_summary"]["total_ut_candidates"]
observed_ut_candidate_total = 0
for item in payload["fr_specs"]:
    spec_path = root / item["spec"]
    assert spec_path.exists()
    text = spec_path.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["status"] == "current_scope_l6_closed"
    assert frontmatter["implementation_status"] == "design_gap_closed_current_phase"
    assert frontmatter["process_layer"] == "L6"
    assert item["fr_id"] in text
    assert "## 3. Function Contract" in text
    assert ("| Function ID | surface | 入力 | 出力 | invariant |" in text) or (
        "| FN-ID | surface | 入力 | 出力 | invariant |" in text
    )
    assert "判定ルール" in text
    assert "L6 単体テスト設計観点" in text
    assert "Completion Boundary" in text
    assert "現在タスクでは L7 test-design artifact を作成しない" in text
    assert "L7 の完了済み UT inventory ではない" in text
    function_ids = {
        match
        for match in re.findall(r"\|\s*([A-Z0-9]+-FN-[0-9]{2})\s*\|", text)
    }
    assert len(function_ids) == item["ut_candidate_count"]
    candidate_ids = re.findall(
        rf"{re.escape(item['ut_candidate_prefix'])}-[0-9]{{2}}",
        text,
    )
    assert len(candidate_ids) == item["ut_candidate_count"]
    assert len(set(candidate_ids)) == item["ut_candidate_count"]
    observed_ut_candidate_total += len(set(candidate_ids))
assert observed_ut_candidate_total == payload["coverage_summary"]["total_ut_candidates"]
assert payload["completion_denial"]["reason"].startswith(
    "This index proves L6 unit-test-design viewpoints only"
)
assert "coverage closure evidence" in payload["completion_denial"][
    "missing_before_l7_completion"
]
PY
  [ "$status" -eq 0 ]
}

@test "L6 function design links FR18 unit-test-design index without L7 claim" {
  run python3 - "$HELIX_ROOT/docs/v2/L6-functional-design/helix-workflows-function-design.md" <<'PY'
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

assert "### 5.3 FR18 追補と L6 単体テスト設計観点索引" in text
assert "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml" in text
assert "Phase3 L7 へ defer" not in text
assert "L7 実装時に TDD で sharpening" not in text
assert "FR 単位の L6 仕様追補へ分割展開した" in text
assert "L6 の「単体テスト設計観点」" in text
assert "L7 の単体テスト設計成果物" in text
assert "coverage closure ではない" in text
assert "承認済み add-feature を入口にする" in text
assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
assert "対応する L7 成果物は現在タスクでは作成しない" in text
checklist = text.split("## 6. 自己検証チェックリスト", 1)[1]
assert "- [ ]" not in checklist
assert "既存 frozen 範囲の `FN-*`" in checklist
assert "L6 の単体テスト設計観点 128 件" in checklist
assert "`*-FN-*` と `*-UT-CAND-*` の対応を L6 内で示すだけ" in checklist
assert "coverage closure の証跡として扱わない" in checklist
PY
  [ "$status" -eq 0 ]
}

@test "L6 process doc explains UT candidate index boundary" {
  run python3 - "$HELIX_ROOT/docs/v2/process/L06-function-design-and-unit-test-design.md" <<'PY'
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

assert "#### Current-scope boundary: L6 内の単体テスト設計観点" in text
assert "L7 実装が明示承認されていない" in text
assert "L7 test-design artifact を新規作成しない" in text
assert "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml" in text
assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
assert "L7 の単体テスト設計成果物" in text
assert "カバレッジ確認 / closure ではない" in text
assert "証跡の階層違反" in text
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 boundary docs route unapproved L7 to add-feature" {
  run python3 - "$HELIX_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
verification_strategy = (
    root / "docs/v2/L1-requirements/helix-workflows-verification-strategy.md"
).read_text(encoding="utf-8")
l4_function_structure = (
    root / "docs/v2/L4-basic-design/機能構成設計.md"
).read_text(encoding="utf-8")
l5_physical_data = (
    root / "docs/v2/L5-detailed-design/物理データ設計.md"
).read_text(encoding="utf-8")
old_whole_source_audit = (
    root / "docs/v2/audit/2026-06-07-whole-source-design-coverage-audit.md"
).read_text(encoding="utf-8")

combined = "\n".join(
    [verification_strategy, l4_function_structure, l5_physical_data]
)
assert "Phase3 L7 実装（TDD sharpening）へ defer" not in combined
assert "Phase3 L7（TDD sharpening）へ defer" not in combined
assert "target: Phase3-L7" not in combined
assert "L7 実装で code へ昇格する" not in combined
assert "L6 関数仕様と L7 実装で詳細化する" not in combined
assert "FR18 の L6 仕様 + `UT-CAND` 索引に分割展開済み" in verification_strategy
assert "承認済み add-feature / PLAN を入口にする" in verification_strategy
assert "routing: {kind: add_feature_boundary, target: approved_L7_feature_or_PLAN" in verification_strategy
assert "code への昇格は L7 実装だが、現在スコープでは実施せず" in l4_function_structure
assert "承認済み add-feature / PLAN を入口にする" in l4_function_structure
assert "L7 実装での具体化は現在スコープでは行わず" in l5_physical_data
assert "historical audit evidence" in old_whole_source_audit
assert "current-scope 側へ巻き取り済み" in old_whole_source_audit
assert "この historical audit からは許可されない" in old_whole_source_audit
assert "L7 実装、FR 別 L7 単体テスト設計成果物、単体テスト実施、coverage closure は承認済み add-feature / PLAN を入口にする" in old_whole_source_audit
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 docs have no unqualified legacy L7 defer phrases" {
  run python3 - "$HELIX_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
scan_roots = [
    root / "docs/v2/L1-requirements",
    root / "docs/v2/L2-screen-design",
    root / "docs/v2/L3-requirements",
    root / "docs/v2/L4-basic-design",
    root / "docs/v2/L5-detailed-design",
    root / "docs/v2/L6-functional-design",
    root / "docs/v2/audit",
    root / "docs/v2/process",
]
forbidden_phrases = [
    "Phase3 L7 実装（TDD sharpening）へ defer",
    "Phase3 L7（TDD sharpening）へ defer",
    "target: Phase3-L7",
    "L7 実装で code へ昇格する",
    "L6 関数仕様と L7 実装で詳細化する",
    "Phase3 defer していたもの",
]

hits = []
for scan_root in scan_roots:
    for path in scan_root.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            if phrase in text:
                hits.append(f"{path.relative_to(root)}: {phrase}")
assert hits == []
PY
  [ "$status" -eq 0 ]
}

@test "L6 preexisting L7 pair docs do not authorize current L7 work" {
  run python3 - "$HELIX_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
registry_detector = (
    root / "docs/v2/L6-functional-design/registry-detector-機能設計.md"
).read_text(encoding="utf-8")
functional_registry_detector = (
    root / "docs/v2/L6-functional-design/functional-registry-detector-機能設計.md"
).read_text(encoding="utf-8")
whole_source_coverage = (
    root / "docs/v2/L6-functional-design/whole-source-coverage-機能設計.md"
).read_text(encoding="utf-8")

assert "add-feature-2026-06-05-registry-detector-base" in registry_detector
for text in [
    registry_detector,
    functional_registry_detector,
    whole_source_coverage,
]:
    assert "現在の L1-L6 監査で新規 L7 作業を許可するものではない" in text
    assert "承認済み add-feature / PLAN を入口にする" in text
assert "historical pair reference" in registry_detector
assert "historical pair reference" in functional_registry_detector
assert "現在監査の completion evidence" in registry_detector
assert "現在監査の completion evidence" in functional_registry_detector
PY
  [ "$status" -eq 0 ]
}

@test "process README links L6 current-scope unit-test-design index" {
  run python3 - "$HELIX_ROOT/docs/v2/process/README.md" <<'PY'
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

assert "### L6 current-scope index" in text
assert "fr18-unit-test-design-index.yaml" in text
assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
assert "L7 実装が未承認" in text
assert "L7 単体テスト設計成果物" in text
assert "カバレッジ確認 / closure ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "process docs do not reference legacy L6 function-design path" {
  run python3 - "$HELIX_ROOT/docs/v2/process" <<'PY'
import pathlib
import sys

process_dir = pathlib.Path(sys.argv[1])
offenders = []
for path in sorted(process_dir.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    if "docs/v2/L6-function-design" in text:
        offenders.append(path.name)

assert offenders == []
assert "docs/v2/L6-functional-design" in (
    process_dir / "L06-function-design-and-unit-test-design.md"
).read_text(encoding="utf-8")
assert "docs/v2/L6-functional-design" in (
    process_dir / "L07-implementation-sprint.md"
).read_text(encoding="utf-8")
PY
  [ "$status" -eq 0 ]
}

@test "plan templates do not generate legacy L6 function-design path" {
  run python3 - \
    "$HELIX_ROOT/cli/templates/plan/impl/template.md" \
    "$HELIX_ROOT/cli/templates/plan/v2/L07-implementation-template.md" <<'PY'
import pathlib
import sys

offenders = []
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    text = path.read_text(encoding="utf-8")
    if "docs/v2/L6-function-design" in text:
        offenders.append(str(path))
    assert "parent_design: docs/v2/L6-functional-design" in text

assert offenders == []
PY
  [ "$status" -eq 0 ]
}

@test "schedule WBS templates generate L7 Sprint not legacy L4 Sprint" {
  run python3 - \
    "$HELIX_ROOT/skills/workflow/schedule-wbs/SKILL.md" \
    "$HELIX_ROOT/skills/workflow/schedule-wbs/references/wbs-template.md" \
    "$HELIX_ROOT/cli/templates/docs/L3-schedule-wbs.md" \
    "$HELIX_ROOT/cli/templates/docs/L3-detailed-design.md" <<'PY'
import pathlib
import sys

offenders = []
for raw_path in sys.argv[1:]:
    path = pathlib.Path(raw_path)
    text = path.read_text(encoding="utf-8")
    if "L4 Sprint" in text or "L4 実装では" in text:
        offenders.append(str(path))
    assert "L7 Sprint" in text or "L7 実装スプリント" in text

assert offenders == []
PY
  [ "$status" -eq 0 ]
}

@test "current user-facing surfaces use current L0-L14 terms" {
  run python3 - "$HELIX_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
files = [
    root / "AGENTS.md",
    root / "HELIX-workflows/helix-process/L1-requirements.md",
    root / "HELIX-workflows/helix-process/review-stage-routing.md",
    root / "HELIX-workflows/helix-process/incident-workflow.md",
    root / "HELIX-workflows/helix-process/recovery-workflow.md",
    root / "cli/helix",
    root / "cli/helix-codex",
    root / "cli/helix-pr",
    root / "cli/helix-sprint",
    root / "cli/config/functional-registry.yaml",
    root / "cli/config/workflows/l4-sprint-workflow.yaml",
    root / "cli/libexec/helix-session-start",
    root / "cli/roles/security.conf",
    root / "cli/templates/agents/pmo-sonnet.md",
    root / "cli/templates/agents/qa-test.md",
    root / "cli/templates/docs/L4-fe-sprint-guide.md",
    root / "cli/templates/docs/L5-visual-design.md",
    root / "cli/templates/docs/PLAN.md.template",
    root / "cli/templates/docs/project-status.md.template",
    root / "cli/templates/gate-checks.yaml",
    root / "cli/templates/plan/impl/template.md",
    root / "docs/commands/ai-harness.md",
    root / "docs/commands/gate.md",
    root / "docs/commands/index.md",
    root / "docs/commands/plan.md",
    root / "docs/commands/pr.md",
    root / "docs/design/D-STATE-SPEC.md",
    root / "docs/design/L2-cli-architecture.md",
    root / "docs/design/L3-detailed-design.md",
    root / "docs/design/L3-schedule-wbs.md",
    root / "docs/design/skill-catalog-jsonl.md",
    root / "README.md",
    root / "skills/SKILL_MAP.md",
    root / "skills/tools/ai-coding/references/workflow-core.md",
    root / "skills/tools/ai-coding/references/layer-interface.md",
    root / "skills/tools/ai-coding/references/gate-policy.md",
    root / "skills/tools/ai-coding/references/implementation-gate.md",
    root / "skills/tools/ai-coding/references/codex-prompt-antipatterns.md",
    root / "skills/tools/ai-coding/references/fork-security-policy.md",
    root / "skills/workflow/deploy/SKILL.md",
    root / "skills/workflow/runbook/SKILL.md",
    root / "skills/project/fe-design/references/fe-drive-flow.md",
    root / "skills/common/visual-design/references/design-md-format.md",
    root / "skills/design-tools/web-system/references/design-md-usage.md",
    root / "skills/workflow/learning-engine/SKILL.md",
    root / "skills/workflow/doc-system-architect/references/design-coverage-baseline.md",
    root / "docs/v2/L0-helix-workflows/concept.md",
    root / "docs/v2/L1-requirements/helix-workflows-business-requirements.md",
    root / "docs/v2/L1-requirements/helix-workflows-nfr.md",
    root / "docs/v2/process/L01-requirements-and-operational-test-design.md",
    root / "docs/v2/CONCEPT.md",
    root / "docs/operator/helix-spiral-operations.md",
    root / "docs/v2/L3-requirements/helix-workflows-nfr-detail.md",
    root / "docs/v2/L3-requirements/helix-workflows-functional-registry.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-draft.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-SEP-rollback-gate6.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md",
    root / "docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md",
    root / "docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md",
    root / "docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md",
    root / "docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md",
    root / "docs/v2/document-system-definition.md",
    root / "docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md",
    root / "docs/v2/process/L12-deployment-and-acceptance-test.md",
    root / "docs/v2/process/README.md",
    root / "ai-code-review-kit/helix-integration/skills/workflow/review-stage-routing/SKILL.md",
    root / "ai-code-review-kit/helix-integration/HELIX-workflows/helix-process/review-stage-routing.md",
]
legacy_terms = [
    "L4 Sprint",
    "L4 マイクロスプリント",
    "G1..G11",
    "G0.5-G11",
    "G0.5〜G11",
    "6 ゲート機械検証",
    "PLAN-001 の L4 実装",
    "L12 デプロイ受入",
    "L12 | デプロイ",
    "デプロイ・受入",
    "| L14 | 運用検証 |",
    "L14 運用検証",
    "13 工程主線",
    "13工程主線",
    "G4 実装凍結",
    "G6 RC",
    "G7 安定性",
    "L5 Visual Refinement",
    "L6 統合検証",
    "L7 デプロイ",
    "L8 受入",
    "L9 デプロイ検証",
    "L10 観測",
    "L11 運用学習",
]
offenders = []
for path in files:
    text = path.read_text(encoding="utf-8")
    for term in legacy_terms:
        if term in text:
            offenders.append(f"{path.relative_to(root)}: {term}")
assert offenders == []

assert "L7 Sprint" in (root / "cli/helix-sprint").read_text(encoding="utf-8")
assert "PLAN-001 の L7 実装" in (root / "docs/commands/ai-harness.md").read_text(encoding="utf-8")
assert "PLAN-001 の L7 実装" in (root / "README.md").read_text(encoding="utf-8")
assert "| L12 | 受入テスト |" in (root / "docs/v2/document-system-definition.md").read_text(encoding="utf-8")
assert "| L14 | 運用学習 / 運用改善 |" in (root / "docs/v2/document-system-definition.md").read_text(encoding="utf-8")
assert "L12 受入テストフェーズ" in (
    root / "docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md"
).read_text(encoding="utf-8")
assert "G4 基本設計凍結ゲート検証" in (root / "cli/templates/gate-checks.yaml").read_text(encoding="utf-8")
assert "L7 Sprint .1-.5 standard 8-step workflow DSL" in (
    root / "cli/config/workflows/l4-sprint-workflow.yaml"
).read_text(encoding="utf-8")
assert "L12 受入テスト PLAN テンプレート" in (
    root / "cli/config/functional-registry.yaml"
).read_text(encoding="utf-8")
PY
  [ "$status" -eq 0 ]
}

@test "verification skill uses current L0-L14 phase terms" {
  run python3 - "$HELIX_ROOT/skills/workflow/verification/SKILL.md" <<'PY'
import sys

text = open(sys.argv[1], encoding="utf-8").read()

assert "### L4（基本設計 / 外部設計 + 総合テスト設計）" in text
assert "### L5（詳細設計 / 内部設計 + 結合テスト設計）" in text
assert "### L6（機能設計 / 仕様書 + 単体テスト設計）" in text
assert "### L7（実装 + 単体テスト実装 / 実施 / coverage closure）" in text
assert "L6 は機能設計 / 仕様書と単体テスト設計を凍結する工程" in text
assert "L6            機能設計 / 仕様書 + 単体テスト設計 ←→ L7 実装 + 単体テスト closure" in text

for term in [
    "### L4（実装）",
    "### L5（Visual）",
    "### L6（統合検証）",
    "### L7（デプロイ）",
    "### L8（受入）",
    "L4 実装（底）",
    "L5 Visual Refinement",
    "L7             デプロイ",
    "HELIXフェーズ番号（L3=詳細設計+API契約",
]:
    assert term not in text
PY
  [ "$status" -eq 0 ]
}

@test "runtime skill metadata uses current L0-L14 phase terms" {
  run python3 - "$HELIX_ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
files = [
    root / "skills/workflow/deploy/SKILL.md",
    root / "skills/advanced/migration/SKILL.md",
    root / "skills/workflow/incident/SKILL.md",
    root / "skills/workflow/postmortem/SKILL.md",
    root / "skills/common/visual-design/SKILL.md",
    root / "skills/workflow/review-stage-routing/SKILL.md",
    root / "skills/workflow/debt-register/SKILL.md",
]
legacy_terms = [
    "HELIX L4 実装",
    "HELIX L7 デプロイ",
    "L7 デプロイ",
    "L6 統合検証",
    "L9 デプロイ検証",
    "L10 観測",
    "L11 運用学習",
    "L5 Visual Refinement",
    "G4 実装凍結",
    "L4 実装完了時",
    "L4 Sprint",
]
offenders = []
for path in files:
    text = path.read_text(encoding="utf-8")
    for term in legacy_terms:
        if term in text:
            offenders.append(f"{path.relative_to(root)}: {term}")
assert offenders == []

assert "HELIX L13 運用検証 / 運用テスト" in (root / "skills/workflow/deploy/SKILL.md").read_text(encoding="utf-8")
assert "HELIX L7 実装 / L13 運用検証" in (root / "skills/advanced/migration/SKILL.md").read_text(encoding="utf-8")
assert "HELIX L13 運用検証 / 運用テスト と L14 運用学習 / 運用改善" in (root / "skills/workflow/incident/SKILL.md").read_text(encoding="utf-8")
assert "HELIX L14 運用学習 / 運用改善" in (root / "skills/workflow/postmortem/SKILL.md").read_text(encoding="utf-8")
assert "L10 フロントUX / 業務デザイン磨き上げ" in (root / "skills/common/visual-design/SKILL.md").read_text(encoding="utf-8")
assert "G7 実装 closure" in (root / "skills/workflow/review-stage-routing/SKILL.md").read_text(encoding="utf-8")
assert "L7 Sprint .5" in (root / "skills/workflow/debt-register/SKILL.md").read_text(encoding="utf-8")
PY
  [ "$status" -eq 0 ]
}

@test "all skill docs do not use legacy L4/L7/L8 phase terms" {
  run python3 - "$HELIX_ROOT/skills" <<'PY'
import pathlib
import sys

skills_root = pathlib.Path(sys.argv[1])
legacy_terms = [
    "HELIX L4 実装",
    "HELIX L7 デプロイ",
    "L7 デプロイ",
    "L6 統合検証",
    "L8 受入",
    "L4 実装",
    "L4 Sprint",
    "L5 Visual Refinement",
    "G4 実装凍結",
    "L10 観測",
    "L11 運用学習",
]
offenders = []
for path in sorted(skills_root.glob("**/SKILL.md")):
    text = path.read_text(encoding="utf-8")
    for term in legacy_terms:
        if term in text:
            offenders.append(f"{path.relative_to(skills_root.parent)}: {term}")
assert offenders == []
PY
  [ "$status" -eq 0 ]
}

@test "right-arm execution gate adoption manifest stays machine-readable" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

expected = {
    "G8": ("L5-L8", "PLAN-G8-INTEGRATION-EXECUTION-GATE"),
    "G9": ("L4-L9", "PLAN-G9-SYSTEM-EXECUTION-GATE"),
    "G12": ("L3-L12", "PLAN-G12-ACCEPTANCE-EXECUTION-GATE"),
    "G14": ("L1-L14", "PLAN-G14-OPERATIONAL-LEARNING-GATE"),
}
expected_expansion = {
    "G8": ["cli/lib/vg_overview.py", "cli/helix-doctor", "docs/v2/L8-test-design/"],
    "G9": [
        "cli/lib/vg_overview.py",
        "cli/lib/trace_symmetry.py",
        "cli/helix-doctor",
        "docs/v2/L9-test-design/",
    ],
    "G12": ["cli/lib/vg_overview.py", "cli/helix-doctor", "docs/v2/L12-test-design/"],
    "G14": [
        "cli/lib/vg_overview.py",
        "cli/helix-harness",
        "cli/lib/harness_monitor.py",
        "docs/v2/L14-test-design/",
    ],
}

assert payload["schema_version"] == "right_arm_execution_gate_adoption_v1"
assert payload["status"] == "plan_materialized"
assert payload["completion_guard"]["current_overall_clean"] is False
assert payload["completion_guard"]["current_deferred_count"] == 4
assert payload["completion_guard"]["goal_complete_allowed"] is False
assert payload["safety"]["schema_migration"] is False
assert payload["safety"]["auto_apply"] is False
assert payload["safety"]["writes_detector_or_gate"] is False
external_sources = {
    item["source_id"]: item for item in payload["external_standard_evidence"]
}
assert set(external_sources) == {
    "ISO-12207-2026",
    "ISO-29148-2018",
    "IEEE-P1012",
    "NIST-SP-800-218",
}
assert external_sources["ISO-12207-2026"]["official_url"] == "https://www.iso.org/standard/90219.html"
assert "to be revised" in external_sources["ISO-29148-2018"]["confirmed_status"]
assert external_sources["IEEE-P1012"]["control_relevance"] == "paired_verification_and_validation"
assert external_sources["NIST-SP-800-218"]["confirmed_version"] == "Version 1.1"
assert "recurrence feedback" in external_sources["NIST-SP-800-218"]["helix_mapping"]
assert payload["current_handover_scope"]["sufficient_for_gate_implementation"] is False
assert payload["current_handover_scope"]["allowed_now"] == [
    "docs/v2/L7-test-design/",
    "cli/lib/tests/",
    "cli/tests/",
]

gates = {item["gate_id"]: item for item in payload["gates"]}
assert set(gates) == set(expected)
for gate_id, (pair, plan_id) in expected.items():
    gate = gates[gate_id]
    assert gate["pair"] == pair
    assert gate["plan_id"] == plan_id
    assert gate["handover_scope_sufficient"] is False
    assert gate["handover_required_expansion"] == expected_expansion[gate_id]
    assert gate["current_state"] == "plan_materialized"
    assert gate["implemented"] is False
    assert gate["passed"] is False
    assert gate["deferred_reason"] == "execution_gate_not_implemented"
    assert gate["rollback_state"] == "approved_deferred"
    assert gate["allowed_implementation_files"]
    assert gate["verification_commands"]
    assert any("strict-full-flow" in command for command in gate["verification_commands"])
    assert gate["acceptance_exit_condition"].startswith(f"{gate_id} removed from strict full-flow")
assert "cli/lib/trace_symmetry.py" in gates["G9"]["allowed_implementation_files"]
assert "docs/v2/L9-test-design/" in gates["G9"]["handover_required_expansion"]
assert "cli/helix-harness" in gates["G14"]["allowed_implementation_files"]
assert "cli/lib/harness_monitor.py" in gates["G14"]["handover_required_expansion"]
assert "semantic_excluded_orphan=18 remains justified" in gates["G9"]["acceptance_exit_condition"]
assert "feedback_closed evidence recorded" in gates["G14"]["acceptance_exit_condition"]
PY
  [ "$status" -eq 0 ]
}

@test "ci gate surface audit keeps local gate separate from full-flow completion" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/ci-gate-surface-audit.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "ci_gate_surface_audit_v1"
assert payload["status"] == "ci_detector_gate_connected_full_flow_still_deferred"
assert payload["source_ci_equivalent_readiness"] == "docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml"
assert payload["local_gate_surface"]["doctor_gate"]["pass"] == 33
assert payload["local_gate_surface"]["doctor_gate"]["fail"] == 0
assert payload["local_gate_surface"]["doctor_gate"]["warn"] == 104
assert payload["ci_surface"]["ci_detector_gate"]["command"] == "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json"
assert payload["ci_surface"]["ci_detector_gate"]["project_state_independent"] is True
assert payload["ci_surface"]["ci_detector_gate"]["gate_basis"] == "vg_overview.overall_clean"
assert payload["local_gate_surface"]["vg_overview_default"]["overall_clean"] is True
assert payload["local_gate_surface"]["vg_overview_default"]["focus"] == "L6"
assert payload["local_gate_surface"]["strict_full_flow"]["overall_clean"] is False
assert payload["local_gate_surface"]["strict_full_flow"]["deferred_count"] == 4
assert payload["local_gate_surface"]["strict_full_flow"]["deferred_gates"] == ["G8", "G9", "G12", "G14"]
assert payload["local_gate_surface"]["push_gate_surface"]["gate_id"] == "G-vg-overview"
assert payload["ci_surface"]["required_for_goal_completion"] is True
assert payload["ci_surface"]["ci_or_equivalent_connected"] is True
assert payload["completion_boundary"]["local_doctor_gate_pass_is_goal_completion"] is False
assert payload["completion_boundary"]["push_gate_documentation_is_ci_completion"] is False
assert payload["completion_boundary"]["strict_full_flow_required_before_completion"] is True
assert payload["safety"]["requires_human_confirmation_for_ci_change"] is True
PY
  [ "$status" -eq 0 ]
}

@test "ci equivalent readiness defines required bundle without connecting completion" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "ci_equivalent_gate_readiness_v1"
assert payload["status"] == "ready_to_connect_not_connected"
assert payload["readiness_boundary"]["equivalent_surface_defined"] is True
assert payload["readiness_boundary"]["ci_or_equivalent_connected"] is False
assert payload["readiness_boundary"]["goal_complete_allowed"] is False
bundle = payload["required_gate_bundle"]
assert bundle["trigger_policy"]["current_scope_connects_ci"] is False
assert [item["id"] for item in bundle["commands"]] == [
    "requirement_drift_l6",
    "l0_l14_contract_pytest",
    "l0_l14_contract_bats",
    "feedback_loop_bats",
    "strict_full_flow",
]
assert bundle["commands"][-1]["required_assertions"] == [
    "overall_clean=true",
    "deferred_count=0",
    "deferred_gates=[]",
]
assert payload["safety"]["ci_workflow_change"] is False
assert payload["safety"]["requires_human_confirmation_for_ci_workflow_change"] is True
assert payload["completion_boundary"]["readiness_manifest_is_goal_completion"] is False
assert payload["completion_boundary"]["ci_or_equivalent_connected"] is False
PY
  [ "$status" -eq 0 ]
}

@test "feedback-loop adoption audit keeps candidates from counting as closure" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/feedback-loop-adoption-audit.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "feedback_loop_adoption_audit_v1"
assert payload["status"] == "partial_candidate_generated"
assert payload["source_feedback_closure_readiness"] == "docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml"
assert payload["current_capabilities"]["json_schema"] == "helix_harness_feedback_loop_snapshot_v1"
assert payload["current_capabilities"]["emits_route_candidates"] is True
assert payload["current_capabilities"]["emits_learning_candidates"] is True
assert payload["current_capabilities"]["emits_plan_candidates"] is True
assert payload["current_capabilities"]["emits_pr_candidates"] is True
assert payload["current_capabilities"]["appends_events_metrics_feedback"] is True
assert payload["current_capabilities"]["strict_vg_deferred_count"] == 4
assert payload["current_capabilities"]["strict_vg_deferred_gates"] == ["G8", "G9", "G12", "G14"]
assert str(payload["updated"]) == "2026-06-10"
snapshot = payload["captured_snapshot"]
assert str(snapshot["captured_on"]) == "2026-06-10"
assert snapshot["schema_version"] == "helix_harness_feedback_loop_snapshot_v1"
assert snapshot["counts"]["automation_running"] >= 1
assert snapshot["counts"]["hook_warn_fail"] >= 150
assert snapshot["counts"]["events"] >= 151
assert snapshot["counts"]["metrics"] >= 1043
assert snapshot["candidate_counts"]["route_candidates"] == 20
assert snapshot["candidate_counts"]["learning_candidates"] == 8
assert snapshot["candidate_counts"]["plan_candidates"] == 20
assert snapshot["candidate_counts"]["pr_candidates"] == 8
assert snapshot["vg_overview"]["deferred_gates"] == ["G8", "G9", "G12", "G14"]
assert "vg_overview:not_applicable_pair_waiver" in snapshot["pr_candidate_source_pattern_keys"]
assert snapshot["safety"]["schema_migration"] is False
assert snapshot["safety"]["auto_apply"] is False
assert payload["safety"]["schema_migration"] is False
assert payload["safety"]["auto_apply"] is False
assert payload["safety"]["writes_detector_or_gate"] is False
assert payload["adoption_boundary"]["candidate_generated"] is True
assert payload["adoption_boundary"]["db_snapshot_registered"] is True
assert payload["adoption_boundary"]["plan_or_pr_adopted"] is False
assert payload["adoption_boundary"]["gate_evidence_closed"] is False
assert payload["adoption_boundary"]["feedback_closed"] is False
assert payload["adoption_boundary"]["goal_complete_allowed"] is False
assert "vg_overview:full_flow_deferred_execution_gate" in payload["source_categories_required"]
assert "automatic application of plan_candidates or pr_candidates" in payload[
    "non_goals_under_current_handover"
]
PY
  [ "$status" -eq 0 ]
}

@test "feedback adoption closure readiness keeps chain incomplete until evidence closes" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "feedback_adoption_closure_readiness_v1"
assert payload["status"] == "ready_to_adopt_not_closed"
assert payload["readiness_boundary"]["candidates_generated"] is True
assert payload["readiness_boundary"]["db_snapshot_registered"] is True
assert payload["readiness_boundary"]["plan_or_pr_adopted"] is False
assert payload["readiness_boundary"]["feedback_closed"] is False
chain = payload["adoption_chain"]
assert [item["order"] for item in chain] == [1, 2, 3, 4, 5]
assert [item["state"] for item in chain] == [
    "candidate_generated",
    "plan_materialized",
    "implementation_adopted",
    "gate_evidence_closed",
    "feedback_closed",
]
assert chain[0]["completion_value"] == "proposal_only"
assert chain[-1]["completion_value"] == "closure_candidate"
assert "ci_or_equivalent_run_id" in payload["required_record_fields"]
assert "recurrence_status" in payload["required_record_fields"]
assert payload["safety"]["auto_apply_feedback_candidates"] is False
assert payload["completion_boundary"]["candidate_generated_is_goal_completion"] is False
assert payload["completion_boundary"]["feedback_closed_requires_gate_and_ci_evidence"] is True
PY
  [ "$status" -eq 0 ]
}

@test "db-backed evidence lifecycle design closes current-phase design gap" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md" \
    "$HELIX_ROOT/docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md" \
    "$HELIX_ROOT/docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md" \
    "$HELIX_ROOT/docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/objective-evidence-matrix.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-10-db-backed-evidence-lifecycle-scope-audit.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md" <<'PY'
import re
import sys
import datetime
import yaml
from pathlib import Path

l4_path, l5_path, l6_path, feature_path, matrix_path, audit_path, l7_path = map(Path, sys.argv[1:8])
root = l4_path.parents[3]
l4 = l4_path.read_text(encoding="utf-8")
l5 = l5_path.read_text(encoding="utf-8")
l6 = l6_path.read_text(encoding="utf-8")
feature = feature_path.read_text(encoding="utf-8")
audit = audit_path.read_text(encoding="utf-8")
matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
db_coverage = yaml.safe_load(
    (root / "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml").read_text(encoding="utf-8")
)

assert not l7_path.exists()
for text in (l4, l5, l6):
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "schema_migration" in text
    assert "auto" in text.lower()

for state in [
    "detected",
    "registered",
    "candidate_generated",
    "plan_materialized",
    "implementation_adopted",
    "verification_recorded",
    "gate_projected",
    "recurrence_closed",
]:
    assert state in l4
    assert state in l5

for fn in [f"DBEV-FN-{index:02d}" for index in range(1, 9)]:
    assert fn in l6
layer_coverage = {item["layer"]: item for item in db_coverage["layer_coverage"]}
assert set(layer_coverage) == {"L4", "L5", "L6"}
assert db_coverage["summary"]["design_layers_checked"] == len(layer_coverage)
assert db_coverage["summary"]["lifecycle_states_defined"] == len(
    db_coverage["state_machine"]["expected_states"]
)
l6_function_ids = sorted(set(re.findall(r"DBEV-FN-[0-9]{2}", l6)))
assert l6_function_ids == [f"DBEV-FN-{index:02d}" for index in range(1, 9)]
assert db_coverage["summary"]["l6_functions_defined"] == len(l6_function_ids)
assert len(layer_coverage["L6"]["coverage"]) == len(l6_function_ids)
for function_id in l6_function_ids:
    assert any(function_id in item for item in layer_coverage["L6"]["coverage"])
for state in db_coverage["state_machine"]["expected_states"]:
    assert state in l6
assert db_coverage["summary"]["existing_storage_groups_mapped"] == len(
    db_coverage["storage_mapping_policy"]["mapped_groups"]
)
assert db_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
    db_coverage["sources"]["deferred_feature_entry_points"]
)
assert "workflow: add-feature" in feature
assert "layer: L7" in feature
assert "current_task_scope: feature_ticket_only" in feature
assert "approval_required_before_l7_work: true" in feature
assert "現在タスクで L7 成果物を生成した証跡ではない" in feature
assert "L7 着手は本 PLAN の承認後に限る" in feature
assert "現在タスクでは `docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md` を作成しない" in feature
assert "DBEV-UT-*" in feature
assert "feature ticket only" in audit
assert "is not present and is not claimed as completed" in audit
assert "not permission to perform L7 work inside the current task" in audit

items = {item["id"]: item for item in matrix["objective_items"]}
db_feedback = items["OBJ-HELIX-DB-FEEDBACK"]
assert db_feedback["status"] == "partial"
assert db_feedback["design_gap_status"] == "L4_L6_closed_L7_feature_ticketed"
evidence = {item.get("artifact") for item in db_feedback["evidence"] if isinstance(item, dict)}
assert str(l4_path.relative_to(l4_path.parents[3])) in evidence
assert str(l5_path.relative_to(l5_path.parents[3])) in evidence
assert str(l6_path.relative_to(l6_path.parents[3])) in evidence
assert str(feature_path.relative_to(feature_path.parents[3])) in evidence
PY
  [ "$status" -eq 0 ]
}

@test "ui absent waiver revalidation keeps L2-L10 bounded" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-09-l0-l6-focus-audit.md" <<'PY'
import sys
import yaml

path, focus_path = sys.argv[1:3]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)
with open(focus_path, encoding="utf-8") as handle:
    focus_text = handle.read()
focus_frontmatter = yaml.safe_load(focus_text.split("---", 2)[1])

assert payload["schema_version"] == "ui_absent_waiver_revalidation_v1"
assert payload["status"] == "revalidation_defined_currently_not_applicable"
assert payload["current_state"]["pair"] == "L2-L10"
assert payload["current_state"]["applicability"] == "not_applicable"
assert payload["current_state"]["reason"] == "ui_absent"
triggers = {item["id"] for item in payload["unskip_triggers"]}
assert triggers == {
    "official_docs_site_or_web_ui",
    "interactive_ui_tui_visual_mock_or_dashboard",
    "downstream_product_screens",
}
assert "CLI help text" in payload["non_unskip_examples"]
assert {
    item["path"] for item in payload["revalidation_sources"]
} >= {
    "docs/v2/audit/2026-06-09-l0-l6-focus-audit.md",
}
assert focus_frontmatter["status"] == "superseded_reference"
assert focus_frontmatter["superseded_by"] == [
    "docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml",
    "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml",
    "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
]
assert "Current boundary: L7 is not requested" in focus_text
assert "Historical non-strict evidence only" in focus_text
assert "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml" in focus_text
assert "docs/v2/L7-test-design/*.md" not in focus_text
assert "It is not current authorization to create L7 artifacts" in focus_text
assert payload["completion_boundary"]["waiver_revalidated_is_goal_completion"] is False
assert payload["completion_boundary"]["waiver_invalid_requires_unskip"] is True
assert payload["safety"]["frontend_artifact_creation"] is False
assert "changing VG-overview waiver logic" in payload["non_goals_under_current_handover"]
PY
  [ "$status" -eq 0 ]
}

@test "full-flow activation ledger aggregates remaining guards without completing goal" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/full-flow-activation-ledger.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/goal-completion-audit.yaml" \
    "$HELIX_ROOT/docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md" <<'PY'
import sys
import yaml

ledger_path, goal_path, feature_path = sys.argv[1:4]
with open(ledger_path, encoding="utf-8") as handle:
    ledger = yaml.safe_load(handle)
with open(goal_path, encoding="utf-8") as handle:
    goal = yaml.safe_load(handle)
with open(feature_path, encoding="utf-8") as handle:
    feature = handle.read()

assert ledger["schema_version"] == "full_flow_activation_ledger_v1"
assert ledger["status"] == "current_scope_ready_for_expansion"
assert ledger["current_scope_summary"]["l6_focus_clean"] is True
assert ledger["current_scope_summary"]["full_goal_complete_allowed"] is False
assert ledger["current_scope_summary"]["remaining_guard_feature_plan_defined"] is True
assert ledger["current_scope_summary"]["harness_external_tools_feature_plan_defined"] is True
assert ledger["sources"]["remaining_guard_feature_plan"] == "docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md"
assert ledger["sources"]["harness_external_tools_feature_plan"] == "docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md"
guards = {item["id"]: item for item in ledger["remaining_completion_guards"]}
assert set(guards) == set(goal["completion_policy"]["required_before_complete"])
assert guards["strict_full_flow_overall_clean_true"]["current_status"] == "incomplete"
assert guards["CI_or_equivalent_gate_surface_connected"]["current_status"] == "defined_not_connected"
assert guards["feedback_candidates_adopted_back_to_PLAN_PR_gate_evidence"]["current_status"] == "defined_not_closed"
assert guards["additional_improvement_candidates_adopted_if_selected"]["current_status"] == "discovered_not_adopted"
assert guards["HARNESS_external_tools_approved_and_connected_if_selected"]["current_status"] == "feature_ticketed_not_installed"
assert [item["order"] for item in ledger["activation_sequence_after_scope_expansion"]] == [1, 2, 3, 4, 5, 6, 7]
assert ledger["current_scope_non_completion_boundary"]["readiness_manifests_are_goal_completion"] is False
assert ledger["current_scope_non_completion_boundary"]["completion_requires_external_or_expanded_scope"] is True
assert ledger["safety"]["schema_migration"] is False
for gate_id in ("G8", "G9", "G12", "G14"):
    assert gate_id in feature
assert "helix-full-flow-required-gate" in feature
assert "This PLAN is not completion evidence" in feature
PY
  [ "$status" -eq 0 ]
}

@test "completion guard manifests agree across current-scope readiness sources" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/goal-completion-audit.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/full-flow-activation-ledger.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml" <<'PY'
import sys
import yaml

goal_path, ledger_path, ci_path, feedback_path, ui_path = sys.argv[1:6]
with open(goal_path, encoding="utf-8") as handle:
    goal = yaml.safe_load(handle)
with open(ledger_path, encoding="utf-8") as handle:
    ledger = yaml.safe_load(handle)
with open(ci_path, encoding="utf-8") as handle:
    ci = yaml.safe_load(handle)
with open(feedback_path, encoding="utf-8") as handle:
    feedback = yaml.safe_load(handle)
with open(ui_path, encoding="utf-8") as handle:
    ui = yaml.safe_load(handle)

guards = {item["id"]: item for item in ledger["remaining_completion_guards"]}
assert list(guards) == goal["completion_policy"]["required_before_complete"]
assert goal["completion_policy"]["goal_complete_allowed"] is False
assert ledger["current_scope_summary"]["full_goal_complete_allowed"] is False
assert guards["CI_or_equivalent_gate_surface_connected"]["current_status"] == "defined_not_connected"
assert ci["readiness_boundary"]["ci_or_equivalent_connected"] is False
assert ci["completion_boundary"]["all_right_arm_gates_must_pass_first"] is True
assert guards["feedback_candidates_adopted_back_to_PLAN_PR_gate_evidence"]["current_status"] == "defined_not_closed"
assert feedback["readiness_boundary"]["plan_or_pr_adopted"] is False
assert feedback["completion_boundary"]["feedback_closed_requires_gate_and_ci_evidence"] is True
assert guards["additional_improvement_candidates_adopted_if_selected"]["current_status"] == "discovered_not_adopted"
assert guards["HARNESS_external_tools_approved_and_connected_if_selected"]["current_status"] == "feature_ticketed_not_installed"
assert guards["L2_L10_ui_absent_waiver_revalidated_or_unskipped_when_UI_exists"]["current_status"] == "revalidated_currently_not_applicable"
assert ui["completion_boundary"]["waiver_revalidated_is_goal_completion"] is False
assert ui["completion_boundary"]["ui_artifact_exists_requires_L2_L10_scope"] is True
PY
  [ "$status" -eq 0 ]
}

@test "objective evidence matrix maps user clauses to current evidence" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/objective-evidence-matrix.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/goal-completion-audit.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/full-flow-activation-ledger.yaml" <<'PY'
import sys
import yaml

matrix_path, goal_path, ledger_path = sys.argv[1:4]
with open(matrix_path, encoding="utf-8") as handle:
    matrix = yaml.safe_load(handle)
with open(goal_path, encoding="utf-8") as handle:
    goal = yaml.safe_load(handle)
with open(ledger_path, encoding="utf-8") as handle:
    ledger = yaml.safe_load(handle)

assert matrix["schema_version"] == "objective_evidence_matrix_v1"
assert matrix["status"] == "current_scope_audited_not_complete"
assert goal["source_objective_evidence_matrix"] == "docs/v2/L7-test-design/objective-evidence-matrix.yaml"
assert ledger["sources"]["objective_evidence_matrix"] == "docs/v2/L7-test-design/objective-evidence-matrix.yaml"
assert ledger["current_scope_summary"]["objective_evidence_matrix_defined"] is True
items = {item["id"]: item for item in matrix["objective_items"]}
assert set(items) == {
    "OBJ-REQ-GAP-L6",
    "OBJ-GRANULARITY-L1-L6",
    "OBJ-CODEX-CLAUDE-GUARD-PARITY",
    "OBJ-DDD-TDD-AUTO-GOVERNANCE",
    "OBJ-WORKFLOW-AUTOMATION",
    "OBJ-HARNESS-EXTERNAL-TOOLS",
    "OBJ-HELIX-DB-FEEDBACK",
    "OBJ-WEB-EVIDENCE",
    "OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY",
    "OBJ-L0-L14-FLOW",
}
assert items["OBJ-REQ-GAP-L6"]["status"] == "achieved_local"
assert items["OBJ-WEB-EVIDENCE"]["status"] == "achieved_local"
assert items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["status"] == "achieved_local"
assert items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["adoption_status"] == "not_adopted"
assert items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["status"] == "partial"
assert items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["design_gap_status"] == "L6_code16_specs_closed_current_phase_no_l7_artifacts"
assert {
    "docs/v2/L6-functional-design/coding-rule-detector-機能設計.md",
    "docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md",
    "docs/v2/L6-functional-design/FR-TDD-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-INV-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-EVT-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-GATE-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-4ART-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-GR-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-9MODE-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-CTX-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-NSM-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-MIGR-01/function-spec.md",
    "docs/v2/L6-functional-design/FR-DOCREVIEW-01/function-spec.md",
    "docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md",
    "docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md",
}.issubset({
    item.get("artifact") for item in items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["evidence"]
})
assert items["OBJ-WORKFLOW-AUTOMATION"]["status"] == "partial"
assert items["OBJ-HARNESS-EXTERNAL-TOOLS"]["status"] == "partial"
assert items["OBJ-HARNESS-EXTERNAL-TOOLS"]["design_gap_status"] == "L4_L6_closed_L7_feature_ticketed"
assert {
    "docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md",
    "docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md",
    "docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md",
    "docs/v2/audit/2026-06-10-harness-external-tools-impact-scope-audit.md",
}.issubset({
    item.get("artifact") for item in items["OBJ-HARNESS-EXTERNAL-TOOLS"]["evidence"]
})
assert items["OBJ-HELIX-DB-FEEDBACK"]["status"] == "partial"
assert items["OBJ-L0-L14-FLOW"]["status"] == "partial"
assert "IMP-OBSERVABILITY-SIGNAL-TAXONOMY" in {
    item.get("candidate") for item in items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["evidence"]
}
assert "https://modelcontextprotocol.io/specification/2025-06-18/basic/index" in {
    item.get("official_source") for item in items["OBJ-HARNESS-EXTERNAL-TOOLS"]["evidence"]
}
assert items["OBJ-REQ-GAP-L6"]["evidence"][0]["expected"]["focus"] == "L6"
assert items["OBJ-REQ-GAP-L6"]["evidence"][0]["expected"]["requirements"] == 31
assert "strict full-flow overall_clean=true" in items["OBJ-L0-L14-FLOW"]["remaining_for_full_goal"]
assert "feedback adoption closed" in items["OBJ-L0-L14-FLOW"]["remaining_for_full_goal"]
assert set(matrix["required_before_complete"]) == set(goal["completion_policy"]["required_before_complete"])
assert matrix["completion_boundary"]["matrix_is_goal_completion"] is False
assert matrix["completion_boundary"]["goal_complete_allowed"] is False
PY
  [ "$status" -eq 0 ]
}

@test "FR-TDD-01 L6 function spec closes TDD design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-TDD-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-TDD-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"TDD-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for blocked in (
    "S2 不在の S3",
    "S5 不在の S7",
    "failing 確認なしの本体実装",
    "CI/equivalent なしの full-flow completion claim",
):
    assert blocked in text
assert "TDD-UT-CAND-01" in text
assert "TDD-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`TDD-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-IMPACT-01 L6 function spec closes impact design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-IMPACT-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"IMPACT-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "BR-06",
    "FR-IMPACT-01",
    "FR-INV-01",
    "FR-PLAN-01",
    "FR-EVT-01",
    "dependency edge",
    "source -> target -> relation -> confidence",
    "5 秒 SLA 超過",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "IMPACT-UT-CAND-01" in text
assert "IMPACT-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`IMPACT-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-INV-01 L6 function spec closes inventory design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-INV-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-INV-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"INV-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-INV-01",
    "FR-FNREG-01",
    "FR-GLOSSARY-01",
    "functional-registry",
    "coding-rule registry",
    "DDD registry",
    "asset_inventory_summary",
    "unregistered_asset",
    "self_asset_reverse_leak",
):
    assert term in text
assert "INV-UT-CAND-01" in text
assert "INV-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`INV-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-PLAN-01 L6 function spec closes plan auto-registration design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-PLAN-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"PLAN-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-PLAN-01",
    "plan_registry",
    "posttooluse-plan-auto-register.sh",
    "plan_parser.py",
    "plan_registry.py",
    "dependency / generates",
    "cycle_detected",
    "auto-register 成功だけでは closure 不可",
):
    assert term in text
assert "PLAN-UT-CAND-01" in text
assert "PLAN-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`PLAN-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-EVT-01 L6 function spec closes forward return event design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-EVT-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-EVT-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"EVT-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-EVT-01",
    "Forward return event",
    "source_workflow",
    "target_forward_layer",
    "design_change_class",
    "required_refreeze_pairs",
    "R1-R5",
    "idempotency key",
    "route / PLAN / PR candidate のみ",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "EVT-UT-CAND-01" in text
assert "EVT-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`EVT-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-GATE-01 L6 function spec closes gate verdict design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-GATE-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-GATE-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"GATE-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-GATE-01",
    "Gate verdict synthesis",
    "pass / warn / fail / approved_deferred / not_applicable",
    "定量 / 定性 Double Check",
    "blocking detector",
    "semantic gate 未実施を pass にしない",
    "candidate_generated / plan_materialized を pass と混同しない",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "GATE-UT-CAND-01" in text
assert "GATE-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`GATE-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-DRIFT-01 L6 function spec closes drift routing design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-DRIFT-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"DRIFT-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-DRIFT-01",
    "Drift routing",
    "interrupt / recovery / reverse / refactor / incident / add-feature / manual_review",
    "Forward return layer",
    "blocking drift を advisory に降格しない",
    "route_candidate_is_closure: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "DRIFT-UT-CAND-01" in text
assert "DRIFT-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`DRIFT-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-4ART-01 L6 function spec closes four artifact trace design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-4ART-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-4ART-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"ART4-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-4ART-01",
    "Four artifact trace audit",
    "設計、実装、テスト設計、テストコード",
    "missing / orphan / wrong_layer",
    "coverage 100 と balance 1.0 を別値として保持する",
    "four_artifact_trace_is_goal_completion: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "ART4-UT-CAND-01" in text
assert "ART4-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`ART4-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-CHANGEPROP-01 L6 function spec closes change propagation design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-CHANGEPROP-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"CHPROP-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-CHANGEPROP-01",
    "Change propagation ratchet",
    "上流変更に対して下流",
    "baseline なしで改善 claim を許可しない",
    "coverage / balance / blocking count の悪化",
    "baseline_snapshot_is_closure: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "CHPROP-UT-CAND-01" in text
assert "CHPROP-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`CHPROP-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-GR-01 L6 function spec closes guardrail design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-GR-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-GR-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"GR-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-GR-01",
    "Guardrail fail-close",
    "pass / warn / block / throttle",
    "policy 欠落を暗黙 pass にしない",
    "Codex では効かず ClaudeCode だけ効く guard",
    "block > throttle > warn > pass",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "GR-UT-CAND-01" in text
assert "GR-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`GR-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-DOCTOR-01 L6 function spec closes doctor aggregate design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-DOCTOR-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"DOCTOR-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-DOCTOR-01",
    "Doctor aggregate audit",
    "docs / plan / vmodel / db / skill / security / locks / inventory",
    "unknown type を all に丸めない",
    "critical 1 件以上で success にしない",
    "summary_is_goal_completion: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "DOCTOR-UT-CAND-01" in text
assert "DOCTOR-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`DOCTOR-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-9MODE-01 L6 function spec closes mode routing design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-9MODE-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-9MODE-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"MODE9-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-9MODE-01",
    "Nine-mode routing",
    "SIGNAL_TO_MODE",
    "signal 不足を Forward 既定にしない",
    "fixed map で mode を決め、4 象限で上書きしない",
    "route_candidate_is_closure: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "MODE9-UT-CAND-01" in text
assert "MODE9-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`MODE9-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-CTX-01 L6 function spec closes context injection design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-CTX-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-CTX-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"CTX-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-CTX-01",
    "Layer context injection",
    "owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode",
    "6 field 欠落を pass にしない",
    "ClaudeCode だけ効く注入を parity finding にする",
    "bundle_generated_is_closure: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "CTX-UT-CAND-01" in text
assert "CTX-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`CTX-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-NSM-01 L6 function spec closes alignment score design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-NSM-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-NSM-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"NSM-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-NSM-01",
    "NSM alignment score",
    "layer / kind / pair_freeze / 4artifact / gate_pass / done",
    "必須 input 欠落をゼロ点成功にしない",
    "trace 欠落時は published にしない",
    "score_published_is_goal_completion: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "NSM-UT-CAND-01" in text
assert "NSM-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`NSM-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-MIGR-01 L6 function spec closes migration design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-MIGR-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-MIGR-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"MIGR-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-MIGR-01",
    "Migration retrofit control",
    "destructive migration",
    "unknown を additive に丸めない",
    "rollback 不在で completed にしない",
    "migration_plan_is_closure: false",
    "schema migration が必要",
):
    assert term in text
assert "MIGR-UT-CAND-01" in text
assert "MIGR-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`MIGR-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-DOCREVIEW-01 L6 function spec closes doc-review design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-DOCREVIEW-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-DOCREVIEW-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"DOCREV-FN-{index:02d}" for index in range(1, 8)]:
    assert fn in text
for term in (
    "FR-DOCREVIEW-01",
    "Doc-review quality gate",
    "Correctness / Completeness / Consistency / Clarity",
    "P0 を conditional に降格しない",
    "read-only / no-write 制約を保持する",
    "review_evidence_is_goal_completion: false",
    "strict full-flow deferred が残る場合に completion を deny",
):
    assert term in text
assert "DOCREV-UT-CAND-01" in text
assert "DOCREV-UT-CAND-07" in text
assert "現在タスクでは作成しない" in text
assert "`DOCREV-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-FNREG-01 L6 function spec closes registry-only design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-FNREG-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"FNREG-FN-{index:02d}" for index in range(1, 9)]:
    assert fn in text
for term in (
    "FR-FNREG-01",
    "機能一覧 SSoT + 自動チェック",
    "registry-only と code-backed を混同しない",
    "未定義 FR 0 件を合格条件にする",
    "L6設計閉塞と L7実装完了を分離する",
    "goal_completion_allowed: false",
):
    assert term in text
assert "FNREG-UT-CAND-01" in text
assert "FNREG-UT-CAND-08" in text
assert "現在タスクでは作成しない" in text
assert "`FNREG-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "FR-GLOSSARY-01 L6 function spec closes registry-only design gap without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md" \
    "$HELIX_ROOT/docs/v2/L7-test-design/FR-GLOSSARY-01/unit-test-design.md" <<'PY'
import sys
from pathlib import Path

l6_path, l7_path = map(Path, sys.argv[1:3])
text = l6_path.read_text(encoding="utf-8")

assert not l7_path.exists()
assert "implementation_status: design_gap_closed_current_phase" in text
assert "現在フェーズでは L6 仕様までを閉じ" in text
for fn in [f"GLOSS-FN-{index:02d}" for index in range(1, 9)]:
    assert fn in text
for term in (
    "FR-GLOSSARY-01",
    "ドメイン用語 SSoT + 自動チェック",
    "L0 §12 を原本として",
    "anti-corruption violation",
    "L6設計閉塞と L7実装完了を分離する",
    "goal_completion_allowed: false",
):
    assert term in text
assert "GLOSS-UT-CAND-01" in text
assert "GLOSS-UT-CAND-08" in text
assert "現在タスクでは作成しない" in text
assert "`GLOSS-UT-CAND-*` は L6 の test-design 観点" in text
assert "L7 の完了済み UT inventory ではない" in text
PY
  [ "$status" -eq 0 ]
}

@test "harness external tools design closes current-phase L4-L6 without L7 artifact" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md" \
    "$HELIX_ROOT/docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md" \
    "$HELIX_ROOT/docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md" \
    "$HELIX_ROOT/docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-10-harness-external-tools-impact-scope-audit.md" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml" \
    "$HELIX_ROOT/docs/v2/audit/2026-06-13-l1-l6-harness-pre-adoption-requirements-acceptance.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md" <<'PY'
import re
import sys
from pathlib import Path

import yaml

l4_path, l5_path, l6_path, feature_path, audit_path, harness_coverage_path, improvement_map_path, pre_adoption_bridge_path, l7_path = map(Path, sys.argv[1:10])
l4 = l4_path.read_text(encoding="utf-8")
l5 = l5_path.read_text(encoding="utf-8")
l6 = l6_path.read_text(encoding="utf-8")
feature = feature_path.read_text(encoding="utf-8")
feature_meta = yaml.safe_load(feature.split("---", 2)[1])
audit = audit_path.read_text(encoding="utf-8")
with open(harness_coverage_path, encoding="utf-8") as handle:
    harness_coverage = yaml.safe_load(handle)
with open(pre_adoption_bridge_path, encoding="utf-8") as handle:
    pre_adoption_bridge = yaml.safe_load(handle)

assert not l7_path.exists()
for text in (l4, l5, l6):
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "schema_migration" in text
    assert "auto" in text.lower()
for fn in [f"HEXT-FN-{index:02d}" for index in range(1, 11)]:
    assert fn in l6
for field in [
    "host_support",
    "auth_method",
    "secret_storage_policy",
    "data_access_scope",
    "tool_invocation_consent_required",
    "tool_poisoning_review_required",
    "output_format",
    "sarif_supported",
    "ci_surface",
    "failure_mode",
]:
    assert field in l5
    assert field in l6
assert "HEXT-UT-CAND-01..10" in audit
assert "L6 unit-test-design viewpoints only" in audit
assert "tool invocation consent" in l4
assert "OAuth / PAT" in l4
assert "SARIF" in l4
assert "CodeQL database" in l6
assert "current_task_scope: L4_L6_design_closed_feature_ticketed" in feature
assert "approval_required_before_install: true" in feature
assert "external_tool_installation_allowed_now: false" in feature
repo_root = feature_path.parents[3]
assert str(harness_coverage_path.relative_to(repo_root)) in feature_meta["related_docs"]
assert str(improvement_map_path.relative_to(repo_root)) in feature_meta["related_docs"]
assert "| zizmor | zizmor official docs / repository |" in feature
assert "GitHub Actions workflow/action static analysis" in feature
assert "| SQLFluff | SQLFluff official docs |" in feature
assert "SQL/schema/migration lint findings" in feature
assert "| pytest-testmon | testmon official docs / pytest-testmon official repository |" in feature
assert "impacted-test selection findings" in feature
assert "| diff-cover | diff-cover official repository / PyPI |" in feature
assert "changed-line coverage / diff-quality findings" in feature
assert "| lychee | lychee official repository / docs |" in feature
assert "link/reference rot findings" in feature
assert "workflow security findings" in feature
assert "### 2.1 L1-L6 candidate inventory sync" in feature
assert "合計 33 candidate" in feature
assert "未承認の候補は install、execute、CI connection、DB write" in feature
assert "L7 test-design / implementation の証跡として扱わない" in feature
for candidate_group in (
    "| MCP / plugin / protocol admission | 3 | feature-ticket-only |",
    "| SAST / code scanning / workflow security | 4 | feature-ticket-only |",
    "| repository / dependency / vulnerability / SBOM intelligence | 4 | feature-ticket-only |",
    "| source dependency graph | 2 | feature-ticket-only |",
    "| shell / markdown / prose / natural-language document lint | 5 | feature-ticket-only |",
    "| Python TDD / coverage / runner / environment automation | 8 | feature-ticket-only |",
    "| Python architecture / schema / API / lint / type / vuln contracts | 6 | feature-ticket-only |",
    "| database / SQL schema / migration lint | 1 | feature-ticket-only |",
):
    assert candidate_group in feature
candidate_inventory_counts = [
    int(count)
    for count in re.findall(
        r"^\| [^|\n]+ \| (\d+) \| feature-ticket-only \|",
        feature,
        flags=re.MULTILINE,
    )
]
assert sum(candidate_inventory_counts) == harness_coverage["summary"]["tool_candidates_checked"]
assert str(pre_adoption_bridge_path.relative_to(repo_root)) in harness_coverage["sources"]["pre_adoption_requirements_acceptance"]
assert harness_coverage["summary"]["pre_adoption_requirement_contracts_checked"] == pre_adoption_bridge["summary"]["pre_adoption_requirement_contracts_checked"] == 5
assert harness_coverage["pre_adoption_requirements_acceptance_bridge"] == {
    "source": str(pre_adoption_bridge_path.relative_to(repo_root)),
    "current_scope_action": "map_web_rechecked_tool_risks_to_existing_l1_l3_requirements_and_acceptance_obligations",
    "representative_sources_rechecked": 5,
    "pre_adoption_requirement_contracts_checked": 5,
    "all_contracts_reuse_existing_l3_requirements": True,
    "new_l3_fr_required_now": False,
    "acceptance_design_update_required_now": False,
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
assert pre_adoption_bridge["schema_version"] == "l1_l6_harness_pre_adoption_requirements_acceptance_v1"
assert pre_adoption_bridge["status"] == "current_scope_l1_l6_requirements_acceptance_bridge_closed"
assert pre_adoption_bridge["boundary"]["l3_frozen_fr_added_by_this_audit"] is False
assert pre_adoption_bridge["boundary"]["l12_acceptance_test_design_modified_by_this_audit"] is False
assert pre_adoption_bridge["boundary"]["l7_artifacts_created_by_this_audit"] == 0
assert pre_adoption_bridge["requirement_bridge_policy"]["new_l3_fr_required_now"] is False
assert pre_adoption_bridge["requirement_bridge_policy"]["acceptance_design_update_required_now"] is False
assert pre_adoption_bridge["acceptance_bridge_invariants"] == {
    "all_contracts_have_source_id": True,
    "all_contracts_reuse_existing_l3_requirements": True,
    "all_contracts_define_l4_l6_design_controls": True,
    "all_contracts_define_acceptance_obligation": True,
    "all_contracts_current_scope_result": "requirements_acceptance_bridge_only",
    "adoption_or_execution_allowed_now": False,
    "db_write_allowed_now": False,
    "l7_artifact_allowed_now": False,
}
bridge_contracts = {item["id"]: item for item in pre_adoption_bridge["pre_adoption_requirement_contracts"]}
assert set(bridge_contracts) == {
    "HEXT-REQ-MCP-CONSENT-AUTH",
    "HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY",
    "HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP",
    "HEXT-REQ-SEMGREP-SAST-ADVISORY",
    "HEXT-REQ-CODEQL-IMPACT-INGESTION",
}
assert bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"]["source_id"] == "MCP-SPEC-2025-06-18"
assert "FR-GR-01" in bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"]["reused_l3_requirements"]
assert "HEXT-FN-10" in bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"]["l4_l6_design_controls"]
assert bridge_contracts["HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY"]["source_id"] == "GITHUB-MCP-SERVER"
assert "FR-IMPACT-01" in bridge_contracts["HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY"]["reused_l3_requirements"]
assert bridge_contracts["HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"]["source_id"] == "OPENAI-APPS-SDK-MCP-DESCRIPTOR"
assert "FR-GR-01" in bridge_contracts["HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"]["reused_l3_requirements"]
assert "HEXT-FN-08" in bridge_contracts["HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"]["l4_l6_design_controls"]
assert bridge_contracts["HEXT-REQ-SEMGREP-SAST-ADVISORY"]["source_id"] == "SEMGREP-CE"
assert "FR-TDD-01" in bridge_contracts["HEXT-REQ-SEMGREP-SAST-ADVISORY"]["reused_l3_requirements"]
assert bridge_contracts["HEXT-REQ-CODEQL-IMPACT-INGESTION"]["source_id"] == "GITHUB-CODEQL"
assert "FR-CHANGEPROP-01" in bridge_contracts["HEXT-REQ-CODEQL-IMPACT-INGESTION"]["reused_l3_requirements"]
assert all(
    item["current_scope_result"] == "requirements_acceptance_bridge_only"
    for item in bridge_contracts.values()
)
assert "L4-L6 設計のみを閉じ" in feature
assert "HEXT-FN-09" in feature
assert "HEXT-FN-10" in feature
assert "本タスクでは L7 単体テスト設計" in l6
assert "feature ticket only" in audit
assert "is not present and is not claimed as completed" in audit
assert "`HEXT-UT-*` is not a current-scope completed test-design artifact" in audit
assert "MCP server, GitHub MCP Server, Semgrep CE, CodeQL, plugin, VSCode extension, CI job, OAuth, PAT, secret, or env setup was not installed or configured." in audit
assert "not permission to perform external tool installation or L7 work inside the current task" in audit
PY
  [ "$status" -eq 0 ]
}

@test "additional improvement discovery stays web-backed without counting as closure" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/additional-improvement-discovery.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "additional_improvement_discovery_v1"
assert payload["status"] == "discovered_not_adopted"
assert str(payload["updated"]) == "2026-06-10"
assert payload["source_web_evidence_map"] == "docs/v2/L7-test-design/web-evidence-source-map.yaml"
assert payload["discovery_boundary"]["candidates_discovered"] is True
assert payload["discovery_boundary"]["plan_or_pr_adopted"] is False
assert payload["discovery_boundary"]["implementation_done"] is False
assert payload["discovery_boundary"]["goal_complete_allowed"] is False
sources = {item["source_id"]: item for item in payload["web_evidence"]}
assert set(sources) == {
    "OWASP-SAMM",
    "SLSA-1.2",
    "OPENTELEMETRY-SIGNALS",
    "OPENSSF-SCORECARD",
    "MCP-SPEC-2025-06-18",
    "GITHUB-MCP-SERVER",
    "SEMGREP-CE",
    "GITHUB-CODEQL",
}
assert sources["SLSA-1.2"]["confirmed_status"] == "Approved"
assert str(sources["SLSA-1.2"]["verified_on"]) == "2026-06-10"
assert str(sources["OPENTELEMETRY-SIGNALS"]["confirmed_last_modified"]) == "2026-03-10"
assert str(sources["OPENTELEMETRY-SIGNALS"]["verified_on"]) == "2026-06-10"
candidates = {item["id"]: item for item in payload["candidates"]}
assert candidates["IMP-SUPPLY-CHAIN-SLSA-PROVENANCE"]["safety"]["infrastructure_change"] is True
assert candidates["IMP-REPO-SECURITY-SCORECARD"]["status"] == "candidate_requires_confirmation"
assert candidates["IMP-HARNESS-MCP-ADMISSION-GATE"]["safety"]["auth_or_pii_change"] is True
assert candidates["IMP-HARNESS-SEMGREP-CE-SAST"]["status"] == "candidate_requires_confirmation"
assert candidates["IMP-HARNESS-CODEQL-IMPACT"]["status"] == "candidate_requires_confirmation"
assert "CI workflow modification" in payload["non_goals_under_current_handover"]
assert "MCP server installation or authentication setup" in payload["non_goals_under_current_handover"]
PY
  [ "$status" -eq 0 ]
}

@test "web evidence source map links official sources to objectives and candidates" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/web-evidence-source-map.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/objective-evidence-matrix.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/additional-improvement-discovery.yaml" <<'PY'
import sys
import yaml

source_path, matrix_path, discovery_path = sys.argv[1:4]
with open(source_path, encoding="utf-8") as handle:
    source_map = yaml.safe_load(handle)
with open(matrix_path, encoding="utf-8") as handle:
    matrix = yaml.safe_load(handle)
with open(discovery_path, encoding="utf-8") as handle:
    discovery = yaml.safe_load(handle)

assert source_map["schema_version"] == "web_evidence_source_map_v1"
assert source_map["status"] == "verified_current_scope_not_adopted"
assert str(source_map["updated"]) == "2026-06-10"
assert matrix["source_web_evidence_map"] == "docs/v2/L7-test-design/web-evidence-source-map.yaml"
assert discovery["source_web_evidence_map"] == "docs/v2/L7-test-design/web-evidence-source-map.yaml"
objective_ids = {item["id"] for item in matrix["objective_items"]}
candidate_ids = {item["id"] for item in discovery["candidates"]}
sources = {item["source_id"]: item for item in source_map["sources"]}
assert set(sources) == {
    "ISO-12207-2026",
    "ISO-29148-2018",
    "IEEE-P1012",
    "NIST-SP-800-218",
    "OWASP-SAMM",
    "SLSA-1.2",
    "OPENTELEMETRY-SIGNALS",
    "OPENSSF-SCORECARD",
    "MCP-SPEC-2025-06-18",
    "GITHUB-MCP-SERVER",
    "SEMGREP-CE",
    "GITHUB-CODEQL",
}
for source in sources.values():
    assert source["source_type"] == "official"
    assert str(source["verified_on"]) == "2026-06-10"
    assert set(source["supports_objective_items"]).issubset(objective_ids)
assert sources["ISO-29148-2018"]["confirmed"]["stage"] == "90.92"
assert sources["IEEE-P1012"]["confirmed"]["status"] == "Active PAR"
assert sources["SLSA-1.2"]["confirmed"]["status"] == "Approved"
assert str(sources["OPENTELEMETRY-SIGNALS"]["confirmed"]["last_modified"]) == "2026-03-10"
assert sources["MCP-SPEC-2025-06-18"]["confirmed"]["base"] == "JSON-RPC 2.0"
assert sources["GITHUB-MCP-SERVER"]["confirmed"]["provider"] == "GitHub"
assert sources["SEMGREP-CE"]["confirmed"]["command"] == "semgrep scan"
assert sources["GITHUB-CODEQL"]["confirmed"]["product"] == "CodeQL"
candidate_support = {
    candidate_id
    for source in sources.values()
    for candidate_id in source["supports_candidates"]
}
assert candidate_support == candidate_ids
assert source_map["completion_boundary"]["source_map_is_goal_completion"] is False
assert source_map["completion_boundary"]["candidate_evidence_is_adoption"] is False
assert str(source_map["completion_boundary"]["refreshed_on"]) == "2026-06-10"
assert source_map["completion_boundary"]["goal_complete_allowed"] is False
PY
  [ "$status" -eq 0 ]
}

@test "right-arm handover request does not self-expand scope" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml" <<'PY'
import sys
import yaml

request_path, adoption_path = sys.argv[1:3]
with open(request_path, encoding="utf-8") as handle:
    request = yaml.safe_load(handle)
with open(adoption_path, encoding="utf-8") as handle:
    adoption = yaml.safe_load(handle)

assert request["schema_version"] == "right_arm_execution_gate_handover_request_v1"
assert request["status"] == "needs_handover_expansion"
assert request["source_closure_plan"] == "docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml"
assert request["current_scope"]["sufficient_for_gate_implementation"] is False
assert request["activation_policy"]["requires_explicit_handover_update"] is True
assert request["activation_policy"]["self_expand_current_handover"] is False
assert request["requested_next_action"]["required_overall_clean"] is True
assert request["requested_next_action"]["completion_exit_gate"].endswith(
    "helix doctor check_vg_overview --strict-full-flow --json"
)

requested_gates = {
    item["gate_id"]: item for item in request["requested_next_action"]["gates"]
}
adoption_gates = {item["gate_id"]: item for item in adoption["gates"]}
assert set(requested_gates) == {"G8", "G9", "G12", "G14"}
assert set(requested_gates) == set(adoption_gates)
for gate_id, gate in requested_gates.items():
    assert gate["pair"] == adoption_gates[gate_id]["pair"]
    assert gate["plan_id"] == adoption_gates[gate_id]["plan_id"]
    assert gate["requested_files"] == adoption_gates[gate_id]["allowed_implementation_files"]
    assert gate["verification_commands"] == adoption_gates[gate_id]["verification_commands"]
    assert gate["acceptance_exit_condition"] == adoption_gates[gate_id]["acceptance_exit_condition"]
assert "cli/lib/vg_overview.py" in requested_gates["G8"]["requested_files"]
assert "cli/lib/trace_symmetry.py" in requested_gates["G9"]["requested_files"]
assert "docs/v2/L12-test-design/" in requested_gates["G12"]["requested_files"]
assert "cli/lib/harness_monitor.py" in requested_gates["G14"]["requested_files"]
assert request["safety"]["schema_migration"] is False
assert request["safety"]["auto_apply_feedback_candidates"] is False
assert "implementation needs files not listed in requested_files." in request["safety"][
    "escalation_required_if"
]
PY
  [ "$status" -eq 0 ]
}

@test "right-arm full-flow closure plan keeps gate order and scope boundary" {
  run python3 - \
    "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml" \
    "$HELIX_ROOT/docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml" <<'PY'
import sys
import yaml

plan_path, request_path = sys.argv[1:3]
with open(plan_path, encoding="utf-8") as handle:
    plan = yaml.safe_load(handle)
with open(request_path, encoding="utf-8") as handle:
    request = yaml.safe_load(handle)

assert plan["schema_version"] == "right_arm_full_flow_closure_plan_v1"
assert plan["status"] == "ready_for_scope_expansion"
assert plan["activation_policy"]["current_handover_scope_sufficient"] is False
assert plan["activation_policy"]["requires_explicit_scope_expansion"] is True
assert plan["activation_policy"]["self_expand_current_handover"] is False
assert plan["global_exit_gate"]["required"]["overall_clean"] is True
assert plan["global_exit_gate"]["required"]["deferred_count"] == 0
sequence = plan["implementation_sequence"]
assert [item["order"] for item in sequence] == [1, 2, 3, 4]
assert [item["gate_id"] for item in sequence] == ["G8", "G9", "G12", "G14"]
requested_gates = {
    item["gate_id"]: item for item in request["requested_next_action"]["gates"]
}
for item in sequence:
    gate_id = item["gate_id"]
    assert item["requested_files"] == requested_gates[gate_id]["requested_files"]
    assert item["verification_commands"] == requested_gates[gate_id]["verification_commands"]
    assert item["rollback_boundary"].startswith(f"Revert only {gate_id}")
assert plan["completion_boundary"]["plan_materialized_is_goal_completion"] is False
assert plan["completion_boundary"]["all_gates_and_feedback_and_ci_required"] is True
assert plan["safety"] == request["safety"]
PY
  [ "$status" -eq 0 ]
}

@test "goal completion audit manifest keeps full objective active" {
  run python3 - "$HELIX_ROOT/docs/v2/L7-test-design/goal-completion-audit.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "goal_completion_audit_v1"
assert payload["status"] == "active_not_complete"
assert payload["completion_policy"]["goal_complete_allowed"] is False
assert payload["completion_policy"]["blocked"] is False
assert payload["focus_status"]["focus"] == "L6"
assert payload["focus_status"]["result"] == "clean"
assert payload["focus_status"]["evidence"]["requirement_drift"]["requirements"] == 31
assert payload["focus_status"]["evidence"]["requirement_drift"]["design_links"] == 31
assert payload["focus_status"]["evidence"]["g7_subcheck"]["anchored"] == 88
assert payload["focus_status"]["evidence"]["g7_subcheck"]["exec_pass"] == 88
assert payload["strict_full_flow_status"]["overall_clean"] is False
assert payload["strict_full_flow_status"]["deferred_count"] == 4
assert {
    item["pair"]: item["gate_id"]
    for item in payload["strict_full_flow_status"]["deferred_gates"]
} == {
    "L5-L8": "G8",
    "L4-L9": "G9",
    "L3-L12": "G12",
    "L1-L14": "G14",
}
requirements = {item["id"]: item for item in payload["requirements"]}
assert requirements["REQ-L1-L6-REQUIREMENT-GAP-AUDIT"]["status"] == "achieved_local"
assert requirements["REQ-L1-L6-GRANULARITY-BALANCE"]["status"] == "achieved_local"
assert requirements["REQ-WORKFLOW-AUTOMATION-REVIEW"]["status"] == "partial"
assert requirements["REQ-HELIX-DB-FEEDBACK-LOOP"]["status"] == "partial"
assert requirements["REQ-GOAL-COMPLETION"]["status"] == "incomplete"
assert "cli/lib/vg_overview.py" in payload["current_handover_scope"]["out_of_scope_for_current_handover"]
assert "Do not treat right-arm PLAN materialization as gate pass evidence." in payload[
    "forbidden_completion_shortcuts"
]
PY
  [ "$status" -eq 0 ]
}

@test "L1-L6 NFR derivation audit covers requirements-deriver signals and ISO 25010" {
  run python3 - "$HELIX_ROOT/docs/v2/audit/2026-06-13-l1-l6-nfr-derivation-coverage.yaml" <<'PY'
import sys
import yaml

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    payload = yaml.safe_load(handle)

assert payload["schema_version"] == "l1_l6_nfr_derivation_coverage_v1"
assert payload["status"] == "current_scope_l1_l6_nfr_derivation_covered"
assert payload["boundary"]["l7_work_requested_by_user"] is False
assert payload["boundary"]["l7_implementation_done"] is False
assert payload["boundary"]["helix_db_write_performed"] is False
assert payload["boundary"]["external_tool_executed"] is False
assert payload["boundary"]["ci_or_equivalent_connected"] is False
assert payload["summary"]["requirements_deriver_signals_checked"] == 9
assert payload["summary"]["requirements_deriver_signals_with_l1_or_l3_coverage"] == 9
assert payload["summary"]["iso_25010_characteristics_checked"] == 9
assert payload["summary"]["iso_25010_characteristics_covered"] == 9
assert payload["summary"]["current_scope_blocking_findings"] == 0
assert payload["summary"]["l7_artifacts_created_by_this_audit"] == 0
assert {row["signal_id"] for row in payload["signal_coverage_rows"]} == {
    "R4",
    "R5",
    "R6",
    "R8",
    "R9",
    "R11",
    "R12",
    "R13",
    "R14",
}
assert {row["characteristic"] for row in payload["iso_25010_coverage"]} == {
    "Functional Suitability",
    "Performance Efficiency",
    "Compatibility",
    "Interaction Capability",
    "Reliability",
    "Security",
    "Maintainability",
    "Flexibility",
    "Safety",
}
assert payload["completion_denial"]["reason"].startswith(
    "This audit proves L1/L3 NFR derivation coverage"
)
PY
  [ "$status" -eq 0 ]
}
