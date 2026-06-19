from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
from urllib.parse import urlparse
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "cli/lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import vg_overview
import trace_symmetry

PATH_REF_PREFIXES = (
    ".helix/",
    "docs/",
    "cli/",
    "HELIX-workflows/",
    "helix/",
    "skills/",
)
PATH_REF_SUFFIXES = (".md", ".yaml", ".py", ".bats")

PROCESS_DOC = REPO_ROOT / "HELIX-workflows/HELIX-process-L0-L14.md"
CORE_DOC = REPO_ROOT / "helix/HELIX_CORE.md"
SKILL_MAP_DOC = REPO_ROOT / "skills/SKILL_MAP.md"
VERIFICATION_SKILL_DOC = REPO_ROOT / "skills/workflow/verification/SKILL.md"
PROCESS_ROADMAP = REPO_ROOT / "docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md"
AI_HARNESS_DOC = REPO_ROOT / "docs/commands/ai-harness.md"
PUSH_DOC = REPO_ROOT / "docs/commands/push.md"
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"
L6_HELIX_FUNCTION_DESIGN_DOC = (
    REPO_ROOT / "docs/v2/L6-functional-design/helix-workflows-function-design.md"
)
L6_PROCESS_DOC = REPO_ROOT / "docs/v2/process/L06-function-design-and-unit-test-design.md"
PROCESS_DOCS_DIR = REPO_ROOT / "docs/v2/process"
PLAN_TEMPLATE_FILES = (
    REPO_ROOT / "cli/templates/plan/impl/template.md",
    REPO_ROOT / "cli/templates/plan/v2/L07-implementation-template.md",
)
SCHEDULE_WBS_TEMPLATE_FILES = (
    REPO_ROOT / "skills/workflow/schedule-wbs/SKILL.md",
    REPO_ROOT / "skills/workflow/schedule-wbs/references/wbs-template.md",
    REPO_ROOT / "cli/templates/docs/L3-schedule-wbs.md",
    REPO_ROOT / "cli/templates/docs/L3-detailed-design.md",
)
CURRENT_L0_L14_USER_FACING_SURFACES = (
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L1-requirements.md",
    REPO_ROOT / "HELIX-workflows/helix-process/review-stage-routing.md",
    REPO_ROOT / "HELIX-workflows/helix-process/ci-pr-workflow.md",
    REPO_ROOT / "HELIX-workflows/helix-process/incident-workflow.md",
    REPO_ROOT / "HELIX-workflows/helix-process/recovery-workflow.md",
    REPO_ROOT / "cli/helix",
    REPO_ROOT / "cli/helix-codex",
    REPO_ROOT / "cli/helix-pr",
    REPO_ROOT / "cli/helix-sprint",
    REPO_ROOT / "cli/config/functional-registry.yaml",
    REPO_ROOT / "cli/config/workflows/l4-sprint-workflow.yaml",
    REPO_ROOT / "cli/libexec/helix-session-start",
    REPO_ROOT / "cli/roles/security.conf",
    REPO_ROOT / "cli/templates/agents/pmo-sonnet.md",
    REPO_ROOT / "cli/templates/agents/qa-test.md",
    REPO_ROOT / "cli/templates/docs/L4-fe-sprint-guide.md",
    REPO_ROOT / "cli/templates/docs/L5-visual-design.md",
    REPO_ROOT / "cli/templates/docs/PLAN.md.template",
    REPO_ROOT / "cli/templates/docs/project-status.md.template",
    REPO_ROOT / "cli/templates/gate-checks.yaml",
    REPO_ROOT / "cli/templates/plan/impl/template.md",
    REPO_ROOT / "cli/templates/patterns/pattern.yaml",
    REPO_ROOT / "docs/commands/ai-harness.md",
    REPO_ROOT / "docs/commands/gate.md",
    REPO_ROOT / "docs/commands/index.md",
    REPO_ROOT / "docs/commands/plan.md",
    REPO_ROOT / "docs/commands/pr.md",
    REPO_ROOT / "docs/design/D-STATE-SPEC.md",
    REPO_ROOT / "docs/design/L2-cli-architecture.md",
    REPO_ROOT / "docs/design/L3-detailed-design.md",
    REPO_ROOT / "docs/design/L3-schedule-wbs.md",
    REPO_ROOT / "docs/design/skill-catalog-jsonl.md",
    REPO_ROOT / "docs/operations/stop-prevention.md",
    REPO_ROOT / "docs/operations/v2-operations-guide.md",
    REPO_ROOT / "docs/agent-skills/README.md",
    REPO_ROOT / "docs/agent-skills/skill-anatomy.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "skills/SKILL_MAP.md",
    REPO_ROOT / "skills/tools/ai-coding/references/workflow-core.md",
    REPO_ROOT / "skills/tools/ai-coding/references/layer-interface.md",
    REPO_ROOT / "skills/tools/ai-coding/references/gate-policy.md",
    REPO_ROOT / "skills/tools/ai-coding/references/implementation-gate.md",
    REPO_ROOT / "skills/tools/ai-coding/references/codex-prompt-antipatterns.md",
    REPO_ROOT / "skills/tools/ai-coding/references/fork-security-policy.md",
    REPO_ROOT / "skills/workflow/deploy/SKILL.md",
    REPO_ROOT / "skills/workflow/runbook/SKILL.md",
    REPO_ROOT / "skills/project/fe-component/SKILL.md",
    REPO_ROOT / "skills/project/fe-design/references/fe-drive-flow.md",
    REPO_ROOT / "skills/common/visual-design/references/design-md-format.md",
    REPO_ROOT / "skills/design-tools/web-system/references/design-md-usage.md",
    REPO_ROOT / "skills/agent-skills/context-engineering/SKILL.md",
    REPO_ROOT / "skills/agent-skills/helix-scrum/SKILL.md",
    REPO_ROOT / "skills/workflow/learning-engine/SKILL.md",
    REPO_ROOT / "skills/workflow/doc-system-architect/references/design-coverage-baseline.md",
    REPO_ROOT / "docs/v2/L0-helix-workflows/concept.md",
    REPO_ROOT / "docs/v2/L1-requirements/helix-workflows-business-requirements.md",
    REPO_ROOT / "docs/v2/L1-requirements/helix-workflows-nfr.md",
    REPO_ROOT / "docs/v2/process/L01-requirements-and-operational-test-design.md",
    REPO_ROOT / "docs/v2/CONCEPT.md",
    REPO_ROOT / "docs/operator/helix-spiral-operations.md",
    REPO_ROOT / "docs/v2/L3-requirements/helix-workflows-nfr-detail.md",
    REPO_ROOT / "docs/v2/L3-requirements/helix-workflows-functional-registry.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-draft.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-SEP-rollback-gate6.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-SEP-phase4b-addendum.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md",
    REPO_ROOT / "docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md",
    REPO_ROOT / "docs/v2/document-system-definition.md",
    REPO_ROOT / "docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md",
    REPO_ROOT / "docs/v2/L14-test-design/helix-workflows-operational-test-design.md",
    REPO_ROOT / "docs/v2/process/L12-deployment-and-acceptance-test.md",
    REPO_ROOT / "docs/v2/process/README.md",
    REPO_ROOT / "ai-code-review-kit/helix-integration/skills/workflow/review-stage-routing/SKILL.md",
    REPO_ROOT / "ai-code-review-kit/helix-integration/HELIX-workflows/helix-process/review-stage-routing.md",
)
CURRENT_PHASE_SKILL_FILES = (
    REPO_ROOT / "skills/workflow/deploy/SKILL.md",
    REPO_ROOT / "skills/advanced/migration/SKILL.md",
    REPO_ROOT / "skills/workflow/incident/SKILL.md",
    REPO_ROOT / "skills/workflow/postmortem/SKILL.md",
    REPO_ROOT / "skills/common/visual-design/SKILL.md",
    REPO_ROOT / "skills/workflow/review-stage-routing/SKILL.md",
    REPO_ROOT / "skills/workflow/debt-register/SKILL.md",
)
ALL_SKILL_DOCS = tuple(sorted((REPO_ROOT / "skills").glob("**/SKILL.md")))
HELIX_DOCTOR_JSON_BATS = REPO_ROOT / "cli/tests/helix-doctor-json.bats"
DEFERRED_GATE_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/deferred-gate-adoption-単体テスト設計.md"
)
RIGHT_ARM_GATE_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/right-arm-execution-gates-単体テスト設計.md"
)
RIGHT_ARM_GATE_ADOPTION_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml"
)
GOAL_COMPLETION_AUDIT_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/goal-completion-audit.yaml"
)
RIGHT_ARM_HANDOVER_REQUEST_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml"
)
RIGHT_ARM_CLOSURE_PLAN_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml"
)
FEEDBACK_LOOP_ADOPTION_AUDIT_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/feedback-loop-adoption-audit.yaml"
)
FEEDBACK_ADOPTION_CLOSURE_READINESS_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml"
)
CI_GATE_SURFACE_AUDIT_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/ci-gate-surface-audit.yaml"
)
CI_EQUIVALENT_READINESS_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml"
)
ADDITIONAL_IMPROVEMENT_DISCOVERY_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/additional-improvement-discovery.yaml"
)
WEB_EVIDENCE_SOURCE_MAP_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/web-evidence-source-map.yaml"
)
UI_ABSENT_WAIVER_REVALIDATION_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml"
)
FULL_FLOW_ACTIVATION_LEDGER_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/full-flow-activation-ledger.yaml"
)
OBJECTIVE_EVIDENCE_MATRIX_MANIFEST = (
    REPO_ROOT / "docs/v2/L7-test-design/objective-evidence-matrix.yaml"
)
OBJECTIVE_L1_L6_COVERAGE_AUDIT = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-objective-l1-l6-coverage.yaml"
)
L1_L6_DESIGN_ASSET_INVENTORY = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-design-asset-inventory.yaml"
)
L1_L6_GRAIN_BALANCE_AUDIT = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-grain-balance-audit.md"
)
L1_L6_IMPROVEMENT_CANDIDATE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml"
)
L1_L6_PAIR_BALANCE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-pair-balance-map.yaml"
)
L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-codex-claude-guard-parity-map.yaml"
)
L1_L6_DEFERRED_FEATURE_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml"
)
L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-db-feedback-lifecycle-coverage.yaml"
)
L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml"
)
L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml"
)
L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-workflow-automation-coverage.yaml"
)
L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-12-l1-l6-db-registration-readiness-coverage.yaml"
)
L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-12-l1-l6-dependency-impact-readiness-coverage.yaml"
)
L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-12-l1-l6-bottleneck-remediation-readiness-coverage.yaml"
)
FULL_OBJECTIVE_GAP_STATUS = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml"
)
L1_L6_RATIFICATION_INDEX = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-ratification-index.yaml"
)
L1_L6_EXIT_CRITERIA_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-exit-criteria-map.yaml"
)
L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-reference-integrity-coverage.yaml"
)
L1_L6_DOUBLE_CHECK_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-double-check-coverage.yaml"
)
L1_L6_FR31_TRACE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml"
)
L1_L6_WEB_EVIDENCE_SOURCE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml"
)
L0_L14_FLOW_SURFACE_COVERAGE_MAP = (
    REPO_ROOT / "docs/v2/audit/2026-06-12-l0-l14-flow-surface-coverage.yaml"
)
L0_PLANNING_DERIVATION_COVERAGE_MAP = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml"
)
L0_L6_FOCUS_AUDIT = REPO_ROOT / "docs/v2/audit/2026-06-09-l0-l6-focus-audit.md"
FR18_L6_UNIT_TEST_DESIGN_INDEX = (
    REPO_ROOT / "docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml"
)
DB_EVIDENCE_LIFECYCLE_L4_DOC = (
    REPO_ROOT / "docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md"
)
DB_EVIDENCE_LIFECYCLE_L5_DOC = (
    REPO_ROOT / "docs/v2/L5-detailed-design/db-backed-evidence-lifecycle-詳細設計.md"
)
DB_EVIDENCE_LIFECYCLE_L6_DOC = (
    REPO_ROOT / "docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md"
)
DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-10-db-backed-evidence-lifecycle-l7.md"
)
DB_EVIDENCE_LIFECYCLE_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md"
)
DB_EVIDENCE_LIFECYCLE_SCOPE_AUDIT = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-10-db-backed-evidence-lifecycle-scope-audit.md"
)
FULL_FLOW_REMAINING_GUARDS_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-10-full-flow-remaining-guards.md"
)
HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md"
)
CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-12-codex-claude-guard-parity-l7.md"
)
PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-12-plan-registry-add-feature-import-l7.md"
)
DEPENDENCY_IMPACT_QUERY_L7_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-12-dependency-impact-query-l7.md"
)
BOTTLENECK_ROUTING_L7_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-12-bottleneck-routing-l7.md"
)
PHASE_ENUM_L0_L14_RUNTIME_RETROFIT_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-13-phase-enum-l0-l14-runtime-retrofit.md"
)
CONTRACT_DESIGN_PHASE_LABEL_RETROFIT_FEATURE_PLAN = (
    REPO_ROOT
    / "docs/plans/add-feature/add-feature-2026-06-13-contract-design-phase-label-retrofit.md"
)
HARNESS_EXTERNAL_TOOLS_L4_DOC = (
    REPO_ROOT / "docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md"
)
HARNESS_EXTERNAL_TOOLS_L5_DOC = (
    REPO_ROOT / "docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md"
)
HARNESS_EXTERNAL_TOOLS_L6_DOC = (
    REPO_ROOT / "docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md"
)
HARNESS_EXTERNAL_TOOLS_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md"
)
HARNESS_EXTERNAL_TOOLS_SCOPE_AUDIT = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-10-harness-external-tools-impact-scope-audit.md"
)
HARNESS_PRE_ADOPTION_REQUIREMENTS_ACCEPTANCE_AUDIT = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-13-l1-l6-harness-pre-adoption-requirements-acceptance.yaml"
)
L1_L6_DEFERRED_DESIGN_OBLIGATION_PROOF = (
    REPO_ROOT
    / "docs/v2/audit/2026-06-13-l1-l6-deferred-design-obligation-proof.yaml"
)
FR_TDD_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-TDD-01/function-spec.md"
)
FR_TDD_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-TDD-01/unit-test-design.md"
)
FR_IMPACT_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md"
)
FR_IMPACT_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-IMPACT-01/unit-test-design.md"
)
FR_INV_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-INV-01/function-spec.md"
)
FR_INV_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-INV-01/unit-test-design.md"
)
FR_PLAN_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md"
)
FR_PLAN_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-PLAN-01/unit-test-design.md"
)
FR_EVT_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-EVT-01/function-spec.md"
)
FR_EVT_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-EVT-01/unit-test-design.md"
)
FR_GATE_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-GATE-01/function-spec.md"
)
FR_GATE_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-GATE-01/unit-test-design.md"
)
FR_DRIFT_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md"
)
FR_DRIFT_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-DRIFT-01/unit-test-design.md"
)
FR_4ART_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-4ART-01/function-spec.md"
)
FR_4ART_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-4ART-01/unit-test-design.md"
)
FR_CHANGEPROP_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md"
)
FR_CHANGEPROP_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-CHANGEPROP-01/unit-test-design.md"
)
FR_GR_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-GR-01/function-spec.md"
)
FR_GR_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-GR-01/unit-test-design.md"
)
FR_DOCTOR_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md"
)
FR_DOCTOR_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-DOCTOR-01/unit-test-design.md"
)
FR_9MODE_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-9MODE-01/function-spec.md"
)
FR_9MODE_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-9MODE-01/unit-test-design.md"
)
FR_CTX_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-CTX-01/function-spec.md"
)
FR_CTX_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-CTX-01/unit-test-design.md"
)
FR_NSM_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-NSM-01/function-spec.md"
)
FR_NSM_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-NSM-01/unit-test-design.md"
)
FR_MIGR_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-MIGR-01/function-spec.md"
)
FR_MIGR_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-MIGR-01/unit-test-design.md"
)
FR_DOCREVIEW_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-DOCREVIEW-01/function-spec.md"
)
FR_DOCREVIEW_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-DOCREVIEW-01/unit-test-design.md"
)
FR_FNREG_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md"
)
FR_FNREG_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-FNREG-01/unit-test-design.md"
)
FR_GLOSSARY_L6_FUNCTION_SPEC = (
    REPO_ROOT / "docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md"
)
FR_GLOSSARY_L7_TEST_DESIGN = (
    REPO_ROOT / "docs/v2/L7-test-design/FR-GLOSSARY-01/unit-test-design.md"
)
DETAIL_DOCS = (
    REPO_ROOT / "HELIX-workflows/helix-process/L2-ui-design.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L3-requirements-definition.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L10-ux-refinement.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L12-deployment.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L13-post-deployment-verification.md",
    REPO_ROOT / "HELIX-workflows/helix-process/L14-operation-verification.md",
    REPO_ROOT / "HELIX-workflows/helix-process/frontend-design-workflow.md",
)
PROCESS_IMPL_DOCS = (
    REPO_ROOT / "docs/v2/process/README.md",
    REPO_ROOT / "docs/v2/process/L02-screen-design-and-wireframe.md",
    REPO_ROOT / "docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md",
    REPO_ROOT / "docs/v2/process/L10-frontend-ux-polish.md",
    REPO_ROOT / "docs/v2/process/L11-review-and-user-validation.md",
    REPO_ROOT / "docs/v2/process/L12-deployment-and-acceptance-test.md",
    REPO_ROOT / "docs/v2/process/L13-post-deployment-verification.md",
    REPO_ROOT / "docs/v2/process/L14-operations-and-improvement.md",
)
RUNTIME_FLOW_DOCS = (
    REPO_ROOT / "cli/templates/phase.yaml",
    REPO_ROOT / "cli/ROLE_MAP.md",
    REPO_ROOT / "cli/templates/doc-map.yaml",
    REPO_ROOT / "cli/templates/plan/v2/L13-post-deployment-template.md",
    REPO_ROOT / "cli/templates/agents/devops-deploy.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _live_strict_deferred_pairs() -> list[dict[str, object]]:
    return vg_overview.live_strict_deferred_pairs(REPO_ROOT)


def _live_strict_deferred_pair_map() -> dict[str, str]:
    return {str(item["pair"]): str(item["gate_id"]) for item in _live_strict_deferred_pairs()}


def _live_strict_deferred_gate_ids() -> list[str]:
    return [str(item["gate_id"]) for item in _live_strict_deferred_pairs()]


def _duplicate_yaml_keys(path: Path) -> list[str]:
    duplicates: list[str] = []

    def walk(node, pointer: str) -> None:
        if getattr(node, "id", None) != "mapping":
            if getattr(node, "id", None) == "sequence":
                for index, child in enumerate(node.value):
                    walk(child, f"{pointer}[{index}]")
            return
        seen: dict[str, int] = {}
        for key_node, value_node in node.value:
            key = str(getattr(key_node, "value", "<non-scalar-key>"))
            if key in seen:
                duplicates.append(
                    f"{path.relative_to(REPO_ROOT)}:{key_node.start_mark.line + 1}:{pointer}/{key}"
                )
            else:
                seen[key] = key_node.start_mark.line + 1
            walk(value_node, f"{pointer}/{key}")

    root = yaml.compose(_read(path))
    if root is not None:
        walk(root, "")
    return duplicates


def test_l1_l6_boundary_text_does_not_describe_l7_as_current_progress() -> None:
    scoped_boundary_docs = (
        FULL_OBJECTIVE_GAP_STATUS,
        OBJECTIVE_L1_L6_COVERAGE_AUDIT,
        L1_L6_DEFERRED_FEATURE_COVERAGE_MAP,
        L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP,
        L1_L6_WEB_EVIDENCE_SOURCE_MAP,
        L1_L6_RATIFICATION_INDEX,
        L1_L6_EXIT_CRITERIA_MAP,
        L1_L6_GRAIN_BALANCE_AUDIT,
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN,
    )
    forbidden_progress_phrases = (
        "L7 or later",
        "L7 以降",
        "L7以降",
        "L7-or-later",
        "l7_or_later",
        "L7+ adoption",
        "L7 UT / implementation",
        "承認後に HARNESS 内で安全に L7",
    )

    for doc in scoped_boundary_docs:
        text = _read(doc)
        for phrase in forbidden_progress_phrases:
            assert phrase not in text, f"{doc.relative_to(REPO_ROOT)} contains {phrase}"

    for doc in (
        OBJECTIVE_L1_L6_COVERAGE_AUDIT,
        L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP,
        L1_L6_WEB_EVIDENCE_SOURCE_MAP,
    ):
        assert "approved feature-ticket work" in _read(doc)


def test_l1_l6_audit_boundary_flags_do_not_claim_later_phase_work() -> None:
    dangerous_key_fragments = (
        "allowed",
        "auto_apply",
        "changed",
        "closure",
        "complete",
        "connected",
        "created",
        "done",
        "enabled",
        "executed",
        "implementation",
        "implemented",
        "installed",
        "migration",
        "performed",
        "promotion",
        "write",
    )
    allowed_true_keys = {
        "l7_work_requires_feature_ticket",
        "right_arm_execution_work_allowed_from_handover",
        "web_sources_verified",
    }
    required_common_boundary_keys = {
        "l7_work_requested_by_user",
        "l7_work_requires_feature_ticket",
        "goal_complete_allowed",
    }
    missing_boundary = []
    missing_common_boundary_keys = []
    dangerous_true_flags = []

    reference_integrity = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))
    audit_paths = [
        REPO_ROOT / ref for ref in reference_integrity["sources"]["audit_bundle"]
    ]
    assert any(
        str(path.relative_to(REPO_ROOT))
        == "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
        for path in audit_paths
    )

    for audit_path in sorted(audit_paths):
        payload = yaml.safe_load(_read(audit_path))
        boundary = payload.get("boundary") or payload.get("scope_boundary")
        if not isinstance(boundary, dict):
            missing_boundary.append(str(audit_path.relative_to(REPO_ROOT)))
            continue
        missing_keys = sorted(required_common_boundary_keys - set(boundary))
        if missing_keys:
            missing_common_boundary_keys.append(
                f"{audit_path.relative_to(REPO_ROOT)}:{','.join(missing_keys)}"
            )
        for key, value in boundary.items():
            if key in allowed_true_keys:
                assert value is True, (audit_path, key)
                continue
            if not any(fragment in key for fragment in dangerous_key_fragments):
                continue
            if value not in (False, 0):
                dangerous_true_flags.append(
                    f"{audit_path.relative_to(REPO_ROOT)}:{key}={value!r}"
                )

    assert missing_boundary == []
    assert missing_common_boundary_keys == []
    assert dangerous_true_flags == []


def test_l1_l6_audit_yaml_bundle_has_no_duplicate_keys() -> None:
    duplicate_keys = []
    reference_integrity = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))
    audit_paths = [
        REPO_ROOT / ref for ref in reference_integrity["sources"]["audit_bundle"]
    ]

    for audit_path in audit_paths:
        duplicate_keys.extend(_duplicate_yaml_keys(audit_path))

    assert len(audit_paths) == 25
    assert any(
        str(path.relative_to(REPO_ROOT))
        == "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
        for path in audit_paths
    )
    assert duplicate_keys == []


def _iter_structured_path_refs(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_structured_path_refs(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from _iter_structured_path_refs(child)
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


def _iter_markdown_path_refs(text: str):
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


def _table_row(text: str, layer: str) -> str:
    match = re.search(rf"^\|\s*{re.escape(layer)}\s*\|.+$", text, flags=re.MULTILINE)
    assert match, f"{layer} row is missing"
    return match.group(0)


def test_l6_l7_l8_flow_terms_match_user_confirmed_contract() -> None:
    text = _read(PROCESS_DOC)

    l6 = _table_row(text, "L6")
    assert "機能設計" in l6
    assert "単体テスト設計" in l6

    l7 = _table_row(text, "L7")
    assert "テスト実装" in l7
    assert "本体実装" in l7
    assert "テスト実施" in l7
    assert "単体テスト実施" in l7

    l8 = _table_row(text, "L8")
    assert "結合テスト" in l8
    assert "L5 の検証" in l8
    assert "本体実装" not in l8
    assert "単体テスト" not in l8


def test_l0_l14_flow_rows_match_user_confirmed_contract() -> None:
    text = _read(PROCESS_DOC)

    expected_rows = {
        "L0": ("企画", "-"),
        "L1": ("要求定義", "運用テスト設計"),
        "L2": ("画面要求 / 画面設計 / フロントUI", "ワイヤーモック"),
        "L3": ("要件定義", "受入テスト設計"),
        "L4": ("基本設計 / 外部設計", "総合テスト設計"),
        "L5": ("詳細設計 / 内部設計", "結合テスト設計"),
        "L6": ("機能設計 / 仕様書", "単体テスト設計"),
        "L7": ("実装", "単体テスト実施"),
        "L8": ("結合テスト", "L5 の検証"),
        "L9": ("総合テスト", "L4 の検証"),
        "L10": ("フロントUX / 業務デザイン磨き上げ", "L2 の検証"),
        "L11": ("総合レビュー / ユーザー検証 / 要件巻き取り", "L1 / L3 の最終突合"),
        "L12": ("受入テスト", "L3 の検証"),
        "L13": ("運用検証 / 運用テスト", "実環境検証"),
        "L14": ("運用学習 / 運用改善", "L1 の検証"),
    }
    for layer, terms in expected_rows.items():
        row = _table_row(text, layer)
        for term in terms:
            assert term in row


def test_vmodel_pair_table_keeps_l1_l14_through_l6_l7_mapping() -> None:
    text = _read(PROCESS_DOC)

    expected_pairs = {
        "L6 単体テスト設計": "L7 単体テスト実施",
        "L5 結合テスト設計": "L8 結合テスト",
        "L4 総合テスト設計": "L9 総合テスト",
        "L3 受入テスト設計": "L12 受入テスト",
        "L1 運用テスト設計": "L14 運用学習 / 運用改善",
        "L2 ワイヤーモック作成": "L10 フロントUX / 業務デザイン磨き上げ",
    }
    for design_side, verify_side in expected_pairs.items():
        assert design_side in text
        assert verify_side in text


def test_core_vmodel_diagram_keeps_l7_as_implementation_valley() -> None:
    text = _read(CORE_DOC)

    assert 'L6["L6 機能設計"]' in text
    assert 'L7(["L7 実装（底・実体化）"])' in text
    assert 'L8["L8 結合"]' in text
    for pair in ("L1 -.->", "L2 -.->", "L3 -.->", "L4 -.->", "L5 -.->", "L6 -.-> L7"):
        assert pair in text


def test_skill_map_orchestration_flow_uses_user_confirmed_terms() -> None:
    text = _read(SKILL_MAP_DOC)

    expected_terms = (
        "L2  画面要求 / 画面設計 / フロントUI + ワイヤーモック",
        "L4  基本設計 / 外部設計 + 総合テスト設計",
        "L5  詳細設計 / 内部設計 + 結合テスト設計",
        "L6  機能設計 / 仕様書 + 単体テスト設計",
        "Step 7: カバレッジ確認 / closure / 修正 / 実装完了",
        "L10 フロントUX / 業務デザイン磨き上げ",
        "L12 受入テスト",
        "L13 運用検証 / 運用テスト",
        "L14 運用学習 / 運用改善",
    )
    for term in expected_terms:
        assert term in text

    forbidden_terms = (
        "L12 デプロイ + 受入テスト + 環境差異巻き取り",
        "L13 デプロイ後検証 + 実環境運用",
        "L14 運用検証 + 機能改善",
        "| L1 運用テスト設計 | L14 運用検証 |",
    )
    for term in forbidden_terms:
        assert term not in text


def test_layer_detail_docs_use_user_confirmed_flow_terms() -> None:
    expected_by_file = {
        "L2-ui-design.md": (
            "L2 画面要求 / 画面設計 / フロントUI",
            "L10 フロントUX / 業務デザイン磨き上げ",
        ),
        "L3-requirements-definition.md": (
            "L3 要件定義",
            "受入テスト設計",
            "L12 受入テスト",
        ),
        "L10-ux-refinement.md": (
            "L10 フロントUX / 業務デザイン磨き上げ",
            "L2 画面要求 / 画面設計 / フロントUI",
            "L10-業務デザインplan",
        ),
        "L12-deployment.md": (
            "L12 受入テスト",
            "L3 要件定義 / 受入テスト設計",
        ),
        "L13-post-deployment-verification.md": (
            "L13 運用検証 / 運用テスト",
            "L12 受入テスト",
            "L13-運用テストplan",
        ),
        "L14-operation-verification.md": (
            "L14 運用学習 / 運用改善",
            "L14-運用学習plan",
            "L14-運用改善plan",
        ),
        "frontend-design-workflow.md": (
            "L10 フロントUX / 業務デザイン磨き上げ",
            "L2 画面要求 / 画面設計",
            "業務デザイン磨き上げ",
        ),
    }
    forbidden_terms = (
        "受け入れテスト設計",
        "ビジネスデザイン磨き上げ",
        "フロントデザインUX・ビジネスデザイン",
        "デプロイ・受入テスト・環境差異巻き取り",
        "デプロイ後検証・実環境運用",
        "運用検証・機能改善",
    )

    for path in DETAIL_DOCS:
        text = _read(path)
        for term in expected_by_file[path.name]:
            assert term in text, f"{term} missing from {path}"
        for term in forbidden_terms:
            assert term not in text, f"{term} remains in {path}"


def test_l3_nfr_detail_uses_current_operational_flow_terms() -> None:
    text = _read(REPO_ROOT / "docs/v2/L3-requirements/helix-workflows-nfr-detail.md")

    assert "L12 は初期受入" in text
    assert "L13 は運用検証 / 運用テスト" in text
    assert "L14 は運用学習 / 運用改善" in text
    assert "L14 は運用検証を担当する" not in text


def test_docs_v2_process_impl_docs_follow_user_confirmed_flow_terms() -> None:
    expected_terms = (
        "画面要求 / 画面設計 / フロントUI",
        "受入テスト設計",
        "フロントUX / 業務デザイン磨き上げ",
        "L12 受入テスト",
        "L13 運用検証 / 運用テスト",
        "L14 運用学習 / 運用改善",
    )
    forbidden_terms = (
        "受け入れテスト設計",
        "ビジネスデザイン磨き上げ",
        "フロントデザインUX",
        "L12 デプロイ",
        "L13 デプロイ",
        "デプロイ後検証",
        "運用検証 / 機能改善",
        "L12-デプロイplan",
        "L12-環境差異plan",
        "L14-機能改善plan",
    )

    combined = "\n".join(_read(path) for path in PROCESS_IMPL_DOCS)
    for term in expected_terms:
        assert term in combined
    for term in forbidden_terms:
        assert term not in combined


def test_runtime_templates_and_role_map_follow_user_confirmed_flow_terms() -> None:
    combined = "\n".join(_read(path) for path in RUNTIME_FLOW_DOCS)

    expected_terms = (
        "L6: 機能設計 / 仕様書 + 単体テスト設計",
        "L7: 実装 + 単体テスト実装/実施 + カバレッジ確認 / closure",
        "Phase 2 実装:  L7(実装+単体テスト+coverage closure)",
        "Phase 4 運用:  L12(受入テスト)→PM  L13(運用検証/運用テスト)",
        "phase: L7",
        "phase: L13",
        "L13-運用検証plan",
        "L13-運用テストplan",
        "L13 運用検証 / 運用テスト・G13 安定性確認",
    )
    for term in expected_terms:
        assert term in combined

    forbidden_terms = (
        "L6: 統合検証",
        "L7: デプロイ",
        "L5(Visual)→PE",
        "L6(検証)→QA",
        "L7(デプロイ)→DevOps",
        "L8(受入)→PM",
        "L13-デプロイ後検証plan",
        "L13-実環境運用plan",
        "L7 デプロイ・G7",
        "# === L7: デプロイ ===",
        "# === L6: テスト・検証 ===",
    )
    for term in forbidden_terms:
        assert term not in combined


def test_process_roadmap_pins_external_standard_evidence_for_l0_l14_alignment() -> None:
    text = _read(PROCESS_ROADMAP)

    expected_terms = (
        "External standard evidence",
        "2026-06-09 Codex で公式一次情報を再検索",
        "ISO/IEC/IEEE 12207:2026",
        "https://www.iso.org/standard/90219.html",
        "Edition 2, Published, publication date 2026-04, stage 60.60",
        "ISO/IEC/IEEE 29148:2018",
        "https://www.iso.org/standard/72089.html",
        "stage 90.92 to be revised as of 2026-02-16",
        "Requirements engineering specifies required processes, information items, required contents, and formats",
        "revision status is tracked as watch evidence rather than a current contract change",
        "IEEE 1012 / P1012 V&V",
        "https://standards.ieee.org/ieee/1012/12536/",
        "P1012 Active PAR; Standard for System, Software, and Hardware Verification and Validation",
        "NIST SP 800-218 SSDF v1.1",
        "https://csrc.nist.gov/pubs/sp/800/218/final",
        "Final, Version 1.1, date published 2022-02",
        "security requirements, gate evidence, and recurrence feedback",
        "L6 focus は `overall_clean=true`",
        "`--strict-full-flow` では `overall_clean=false`",
        "deferred 4 件",
    )
    for term in expected_terms:
        assert term in text


def test_process_roadmap_uses_feedback_loop_snapshot_schema_terms() -> None:
    text = _read(PROCESS_ROADMAP)

    expected_terms = (
        "JSON schema の正式キーは `plan_candidates`",
        "route_candidates=20",
        "learning_candidates=8",
        "plan_candidates=20",
        "pr_candidates=8",
        "`vg_overview.deferred_count=4`",
        "`plan_draft_candidates` key は存在しない",
        "Deferred gate adoption queue",
        "Deferred gate PLAN materialization draft",
        "`PLAN-G8-INTEGRATION-EXECUTION-GATE`",
        "`PLAN-G9-SYSTEM-EXECUTION-GATE`",
        "`PLAN-G12-ACCEPTANCE-EXECUTION-GATE`",
        "`PLAN-G14-OPERATIONAL-LEARNING-GATE`",
        "candidate_generated` から `plan_materialized`",
        "Allowed implementation files",
        "Acceptance evidence",
        "Rollback / safety",
        "L5-L8 remains deferred for G8; implement G8 integration-test execution gate",
        "L4-L9 remains deferred for G9; implement G9 system-test execution gate",
        "L3-L12 remains deferred for G12; implement G12 acceptance-test execution gate",
        "L1-L14 remains deferred for G14; implement G14 operational-learning execution gate",
        "strict full-flow から G12 deferred が消える",
        "feedback_closed state で adoption result が再発検出へ接続される",
        "PLAN materialization draft が存在しても",
        "`gate_implemented` / `gate_passed` / `ci_enforced` / `feedback_closed`",
        "この queue は completion guard の DB feedback loop 条件に対する採用待ち evidence",
        "Additional discovered improvement backlog",
        "Route adapter for feedback-loop candidates",
        "L2-L10 ui_absent unskip detector",
        "Feedback candidate adoption materialization",
        "CI gate surface hardening",
        "Schema-backed detector history",
        "この backlog は「できること」の発見記録であり、採用完了ではない",
        "`schema_migration=false`、`auto_apply=false`、`writes_detector_or_gate=false`",
    )
    for term in expected_terms:
        assert term in text

    assert "plan_draft_candidates=0" not in text


def test_deferred_gate_adoption_test_design_pins_candidate_boundary() -> None:
    text = _read(DEFERRED_GATE_TEST_DESIGN)

    expected_terms = (
        "doc_id: L7-TEST-DESIGN-DEFERRED-GATE-ADOPTION",
        "implementation_status: implemented-contract",
        "`DGA-UT-*` は deferred gate adoption 専用テスト ID",
        "G7 UT inventory へ混入させない",
        "DGA-UT-01",
        "DGA-UT-02",
        "DGA-UT-03",
        "DGA-UT-04",
        "DGA-UT-05",
        "DGA-UT-06",
        "DGA-UT-07",
        "DGA-UT-08",
        "DGA-UT-09",
        "DGA-UT-10",
        "pairs=`L4-L9:G9`, `L3-L12:G12`, `L1-L14:G14`",
        "`pre-G8 baseline` also included `L5-L8:G8`",
        "`vg_overview.deferred_count=3` (`pre-G8 baseline: 4`)",
        "metrics `full_flow_deferred_gates=3`",
        "PR source keys include automation, feedback, observability, verify, hook, harness, VG deferred, and VG waiver categories",
        "candidate, PLAN materialization, gate implementation, CI enforcement, and feedback closure are separate states",
        "G9/G12/G14 remain adoption_required until execution gate implementation and pass evidence exist; G8 stays recorded in the four-gate ledger but no longer counts toward current deferred_count",
        "candidate_generated",
        "plan_materialized",
        "gate_implemented",
        "gate_passed",
        "ci_enforced",
        "feedback_closed",
        "`overall_clean=true` の L6 focus 判定を goal complete と見なさない",
    )
    for term in expected_terms:
        assert term in text


def test_right_arm_execution_gate_test_design_pins_pass_conditions() -> None:
    text = _read(RIGHT_ARM_GATE_TEST_DESIGN)

    expected_terms = (
        "doc_id: L7-TEST-DESIGN-RIGHT-ARM-EXECUTION-GATES",
        "implementation_status: planned-contract",
        "`EGA-UT-*` は right-arm execution gate adoption 専用テスト ID",
        "G7 UT inventory へ混入させない",
        "EGA-UT-01",
        "EGA-UT-02",
        "EGA-UT-03",
        "EGA-UT-04",
        "EGA-UT-05",
        "EGA-UT-06",
        "EGA-UT-07",
        "EGA-UT-08",
        "G8",
        "G9",
        "G12",
        "G14",
        "`L5-L8` の `execution_gate_not_implemented`",
        "`L4-L9` の `execution_gate_not_implemented`",
        "`L3-L12` の `execution_gate_not_implemented`",
        "`L1-L14` の `execution_gate_not_implemented`",
        "`semantic_excluded_orphan=18`",
        "current live strict contract では G8 closure 後の deferred は G9 / G12 / G14 の 3件",
        "strict full-flow starts with four (`pre-G8 baseline`), now three after G8 closure",
        "strict full-flow keeps `overall_clean=false` until the remaining G9/G12/G14 pass while preserving G8 closure",
        "`PLAN-G8-INTEGRATION-EXECUTION-GATE`",
        "`PLAN-G9-SYSTEM-EXECUTION-GATE`",
        "`PLAN-G12-ACCEPTANCE-EXECUTION-GATE`",
        "`PLAN-G14-OPERATIONAL-LEARNING-GATE`",
        "strict full-flow の current deferred 3件 (`pre-G8 baseline: 4件`) をこの文書だけで closure 扱いしない",
    )
    for term in expected_terms:
        assert term in text


def test_right_arm_execution_gate_adoption_manifest_is_machine_readable() -> None:
    payload = yaml.safe_load(_read(RIGHT_ARM_GATE_ADOPTION_MANIFEST))
    expected_gates = {
        "G8": ("L5-L8", "PLAN-G8-INTEGRATION-EXECUTION-GATE"),
        "G9": ("L4-L9", "PLAN-G9-SYSTEM-EXECUTION-GATE"),
        "G12": ("L3-L12", "PLAN-G12-ACCEPTANCE-EXECUTION-GATE"),
        "G14": ("L1-L14", "PLAN-G14-OPERATIONAL-LEARNING-GATE"),
    }
    expected_allowed_files = {
        "G8": [
            "cli/lib/vg_overview.py",
            "cli/helix-doctor",
            "cli/lib/tests/test_vg_overview.py",
            "cli/tests/helix-doctor-json.bats",
            "docs/v2/L8-test-design/",
        ],
        "G9": [
            "cli/lib/vg_overview.py",
            "cli/lib/trace_symmetry.py",
            "cli/helix-doctor",
            "cli/lib/tests/test_vg_overview.py",
            "cli/lib/tests/test_trace_symmetry.py",
            "docs/v2/L9-test-design/",
        ],
        "G12": [
            "cli/lib/vg_overview.py",
            "cli/helix-doctor",
            "cli/lib/tests/test_vg_overview.py",
            "cli/tests/helix-doctor-json.bats",
            "docs/v2/L12-test-design/",
        ],
        "G14": [
            "cli/lib/vg_overview.py",
            "cli/helix-harness",
            "cli/lib/harness_monitor.py",
            "cli/lib/tests/test_vg_overview.py",
            "cli/lib/tests/test_harness_monitor_unit.py",
            "cli/tests/test-helix-harness-feedback-loop.bats",
            "docs/v2/L14-test-design/",
        ],
    }
    expected_handover_expansion = {
        "G8": [
            "cli/lib/vg_overview.py",
            "cli/helix-doctor",
            "docs/v2/L8-test-design/",
        ],
        "G9": [
            "cli/lib/vg_overview.py",
            "cli/lib/trace_symmetry.py",
            "cli/helix-doctor",
            "docs/v2/L9-test-design/",
        ],
        "G12": [
            "cli/lib/vg_overview.py",
            "cli/helix-doctor",
            "docs/v2/L12-test-design/",
        ],
        "G14": [
            "cli/lib/vg_overview.py",
            "cli/helix-harness",
            "cli/lib/harness_monitor.py",
            "docs/v2/L14-test-design/",
        ],
    }

    assert payload["schema_version"] == "right_arm_execution_gate_adoption_v1"
    assert payload["status"] == "plan_materialized"
    assert payload["completion_guard"]["required_clean_command"] == (
        "helix doctor check_vg_overview --strict-full-flow --json"
    )
    assert payload["completion_guard"]["required_overall_clean"] is True
    assert payload["completion_guard"]["current_overall_clean"] is False
    assert payload["completion_guard"]["current_deferred_count"] == 3
    assert payload["completion_guard"]["goal_complete_allowed"] is False
    assert payload["safety"] == {
        "schema_migration": False,
        "auto_apply": False,
        "writes_detector_or_gate": False,
        "requires_tl_confirmation_for_gate_implementation": True,
    }
    external_sources = {
        item["source_id"]: item for item in payload["external_standard_evidence"]
    }
    assert set(external_sources) == {
        "ISO-12207-2026",
        "ISO-29148-2018",
        "IEEE-P1012",
        "NIST-SP-800-218",
    }
    assert external_sources["ISO-12207-2026"]["official_url"] == (
        "https://www.iso.org/standard/90219.html"
    )
    assert "to be revised" in external_sources["ISO-29148-2018"]["confirmed_status"]
    assert external_sources["IEEE-P1012"]["control_relevance"] == (
        "paired_verification_and_validation"
    )
    assert external_sources["NIST-SP-800-218"]["confirmed_version"] == "Version 1.1"
    assert (
        "recurrence feedback"
        in external_sources["NIST-SP-800-218"]["helix_mapping"]
    )
    assert payload["current_handover_scope"] == {
        "sufficient_for_gate_implementation": False,
        "allowed_now": [
            "docs/v2/L7-test-design/",
            "cli/lib/tests/",
            "cli/tests/",
        ],
        "reason": "gate implementation files are outside current handover Next Action",
    }
    assert payload["adoption_states"] == [
        "candidate_generated",
        "plan_materialized",
        "gate_implemented",
        "gate_passed",
        "ci_enforced",
        "feedback_closed",
    ]

    gates = {item["gate_id"]: item for item in payload["gates"]}
    assert set(gates) == set(expected_gates)
    for gate_id, (pair, plan_id) in expected_gates.items():
        gate = gates[gate_id]
        assert gate["pair"] == pair
        assert gate["plan_id"] == plan_id
        assert gate["handover_scope_sufficient"] is False
        assert gate["handover_required_expansion"] == expected_handover_expansion[gate_id]
        assert gate["allowed_implementation_files"] == expected_allowed_files[gate_id]
        assert gate["current_state"] == "plan_materialized"
        assert gate["implemented"] is False
        assert gate["passed"] is False
        assert gate["deferred_reason"] == "execution_gate_not_implemented"
        assert "execution_gate_not_implemented" in gate["must_disappear"]
        assert gate["rollback_state"] == "approved_deferred"
        assert gate["evidence_required"]
        assert gate["verification_commands"]
        assert any("strict-full-flow" in command for command in gate["verification_commands"])
        assert gate["acceptance_exit_condition"].startswith(f"{gate_id} removed from strict full-flow")
    assert gates["G9"]["semantic_evidence_required"] == "semantic_excluded_orphan=18"
    assert (
        "semantic_excluded_orphan=18 remains justified"
        in gates["G9"]["acceptance_exit_condition"]
    )
    assert any(
        "HELIX DB events metrics feedback adoption result" in item
        for item in gates["G14"]["evidence_required"]
    )
    assert "feedback_closed evidence recorded" in gates["G14"]["acceptance_exit_condition"]


def test_right_arm_adoption_manifest_matches_live_strict_deferred_pairs() -> None:
    payload = yaml.safe_load(_read(RIGHT_ARM_GATE_ADOPTION_MANIFEST))
    strict_report = vg_overview.collect_vg_overview(
        REPO_ROOT,
        strict_full_flow=True,
        execute_g7_tests=False,
    )
    strict_vg = strict_report["vg_overview"]
    live_pairs = {
        item["gate_id"]: item
        for item in strict_vg["full_flow_execution"]["deferred_pairs"]
    }
    manifest_gates = {item["gate_id"]: item for item in payload["gates"]}

    assert strict_vg["overall_clean"] is payload["completion_guard"]["current_overall_clean"]
    assert strict_vg["full_flow_execution"]["deferred_count"] == payload["completion_guard"][
        "current_deferred_count"
    ]
    assert set(live_pairs) == {"G9", "G12", "G14"}
    assert set(manifest_gates) == {"G8", "G9", "G12", "G14"}
    assert "G8" not in live_pairs

    for gate_id in ("G9", "G12", "G14"):
        manifest_gate = manifest_gates[gate_id]
        live_gate = live_pairs[gate_id]
        assert manifest_gate["pair"] == live_gate["pair"]
        assert manifest_gate["source_layer"] == live_gate["source_layer"]
        assert manifest_gate["target_layer"] == live_gate["target_layer"]
        assert manifest_gate["deferred_reason"] in live_gate["reason"]
        assert manifest_gate["implemented"] is False
        assert manifest_gate["passed"] is False
        assert manifest_gate["current_state"] == "plan_materialized"
        assert live_gate["next_action"].startswith(f"implement {gate_id} ")


def test_goal_completion_audit_manifest_keeps_full_objective_active() -> None:
    payload = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    live_deferred_pairs = _live_strict_deferred_pairs()

    assert payload["schema_version"] == "goal_completion_audit_v1"
    assert payload["status"] == "active_not_complete"
    assert payload["completion_policy"] == {
        "goal_complete_allowed": False,
        "blocked": False,
        "reason": "strict full-flow still has deferred right-arm execution gates.",
        "required_before_complete": [
            "strict_full_flow_overall_clean_true",
            "G8_G9_G12_G14_gate_implemented_and_passed",
            "CI_or_equivalent_gate_surface_connected",
            "feedback_candidates_adopted_back_to_PLAN_PR_gate_evidence",
            "additional_improvement_candidates_adopted_if_selected",
            "HARNESS_external_tools_approved_and_connected_if_selected",
            "L2_L10_ui_absent_waiver_revalidated_or_unskipped_when_UI_exists",
        ],
    }
    assert payload["focus_status"]["focus"] == "L6"
    assert payload["focus_status"]["result"] == "clean"
    assert payload["focus_status"]["evidence"]["requirement_drift"] == {
        "command": "helix doctor check_requirement_drift --json",
        "requirements": 31,
        "design_links": 31,
        "blocking_findings": 0,
        "advisory_findings": 0,
        "waived_findings": 0,
    }
    assert payload["focus_status"]["evidence"]["g7_subcheck"] == {
        "anchored": 88,
        "exec_pass": 88,
        "missing": 0,
        "unanchored_but_exists": 0,
    }
    assert payload["strict_full_flow_status"]["derived_from"] == "strict_vg_overview"
    assert payload["strict_full_flow_status"]["last_verified_command"] == (
        vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    )
    assert payload["strict_full_flow_status"]["command"] == (
        vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    )
    assert payload["strict_full_flow_status"]["overall_clean"] is False
    assert payload["strict_full_flow_status"]["deferred_count"] == len(live_deferred_pairs)
    assert {
        item["pair"]: item["gate_id"]
        for item in payload["strict_full_flow_status"]["deferred_gates"]
    } == _live_strict_deferred_pair_map()

    requirements = {item["id"]: item for item in payload["requirements"]}
    assert set(requirements) == {
        "REQ-L0-L14-FLOW",
        "REQ-L1-L6-REQUIREMENT-GAP-AUDIT",
        "REQ-L1-L6-GRANULARITY-BALANCE",
            "REQ-L6-TO-L7-UNIT-CLOSURE",
            "REQ-CODEX-CLAUDE-GUARD-PARITY",
            "REQ-DDD-TDD-AUTO-GOVERNANCE",
            "REQ-WORKFLOW-AUTOMATION-REVIEW",
            "REQ-HARNESS-EXTERNAL-TOOLS",
        "REQ-HELIX-DB-FEEDBACK-LOOP",
        "REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY",
        "REQ-WEB-EVIDENCE",
        "REQ-GOAL-COMPLETION",
    }
    assert requirements["REQ-GOAL-COMPLETION"]["status"] == "incomplete"
    assert "docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml" in requirements[
        "REQ-L0-L14-FLOW"
    ]["evidence"]
    assert requirements["REQ-L1-L6-REQUIREMENT-GAP-AUDIT"]["status"] == "achieved_local"
    assert requirements["REQ-L1-L6-GRANULARITY-BALANCE"]["status"] == "achieved_local"
    assert requirements["REQ-WORKFLOW-AUTOMATION-REVIEW"]["status"] == "partial"
    assert requirements["REQ-HARNESS-EXTERNAL-TOOLS"]["status"] == "partial"
    assert requirements["REQ-HARNESS-EXTERNAL-TOOLS"]["design_gap_status"] == (
        "L4_L6_closed_L7_feature_ticketed"
    )
    assert str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)) in requirements[
        "REQ-HARNESS-EXTERNAL-TOOLS"
    ]["evidence"]
    assert requirements["REQ-HELIX-DB-FEEDBACK-LOOP"]["status"] == "partial"
    assert requirements["REQ-WEB-EVIDENCE"]["status"] == "achieved_local"
    assert "cli/lib/vg_overview.py" in payload["current_handover_scope"][
        "out_of_scope_for_current_handover"
    ]
    assert payload["current_handover_scope"]["expansion_request"] == (
        "docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml"
    )
    assert payload["current_handover_scope"]["closure_plan"] == (
        "docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml"
    )
    assert payload["current_handover_scope"]["activation_ledger"] == (
        "docs/v2/L7-test-design/full-flow-activation-ledger.yaml"
    )
    assert requirements["REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["status"] == "partial"
    assert (
        requirements["REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["discovery_status"]
        == "achieved_local"
    )
    assert (
        requirements["REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["adoption_status"]
        == "not_adopted"
    )
    assert "docs/v2/L7-test-design/additional-improvement-discovery.yaml" in requirements[
        "REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"
    ]["evidence"]
    assert "SLSA v1.2 official specification page" in requirements["REQ-WEB-EVIDENCE"][
        "evidence"
    ]
    assert "Do not treat default VG-overview overall_clean=true as full L0-L14 completion." in payload[
        "forbidden_completion_shortcuts"
    ]


def test_full_flow_activation_ledger_aggregates_remaining_completion_guards() -> None:
    payload = yaml.safe_load(_read(FULL_FLOW_ACTIVATION_LEDGER_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    feature_plan = _read(FULL_FLOW_REMAINING_GUARDS_FEATURE_PLAN)

    assert payload["schema_version"] == "full_flow_activation_ledger_v1"
    assert payload["status"] == "current_scope_ready_for_expansion"
    assert payload["source_goal_audit"] == (
        "docs/v2/L7-test-design/goal-completion-audit.yaml"
    )
    assert set(payload["sources"]) == {
        "objective_evidence_matrix",
        "right_arm_closure_plan",
        "right_arm_handover_request",
        "ci_equivalent_readiness",
        "feedback_closure_readiness",
        "ui_absent_revalidation",
            "additional_improvement_discovery",
            "remaining_guard_feature_plan",
            "harness_external_tools_feature_plan",
        }
    assert payload["sources"]["remaining_guard_feature_plan"] == str(
        FULL_FLOW_REMAINING_GUARDS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert payload["sources"]["harness_external_tools_feature_plan"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    summary = payload["current_scope_summary"]
    assert summary["l6_focus_clean"] is True
    assert summary["requirement_drift_clean"] is True
    assert summary["right_arm_readiness_defined"] is True
    assert summary["ci_equivalent_readiness_defined"] is True
    assert summary["feedback_adoption_readiness_defined"] is True
    assert summary["remaining_guard_feature_plan_defined"] is True
    assert summary["ui_absent_revalidation_defined"] is True
    assert summary["objective_evidence_matrix_defined"] is True
    assert summary["harness_external_tools_feature_plan_defined"] is True
    assert summary["full_goal_complete_allowed"] is False

    guards = {item["id"]: item for item in payload["remaining_completion_guards"]}
    assert set(guards) == set(goal_audit["completion_policy"]["required_before_complete"])
    assert guards["strict_full_flow_overall_clean_true"]["current_status"] == "incomplete"
    assert guards["G8_G9_G12_G14_gate_implemented_and_passed"][
        "current_evidence"
    ] == "deferred_count=3"
    assert guards["CI_or_equivalent_gate_surface_connected"][
        "current_status"
    ] == "defined_not_connected"
    assert guards["feedback_candidates_adopted_back_to_PLAN_PR_gate_evidence"][
        "current_status"
    ] == "defined_not_closed"
    assert guards["additional_improvement_candidates_adopted_if_selected"][
        "current_status"
    ] == "discovered_not_adopted"
    assert guards["HARNESS_external_tools_approved_and_connected_if_selected"][
        "current_status"
    ] == "feature_ticketed_not_installed"
    assert guards["L2_L10_ui_absent_waiver_revalidated_or_unskipped_when_UI_exists"][
        "current_status"
    ] == "revalidated_currently_not_applicable"

    sequence = payload["activation_sequence_after_scope_expansion"]
    assert [item["order"] for item in sequence] == [1, 2, 3, 4, 5, 6, 7]
    assert sequence[0]["source"] == "docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml"
    assert sequence[1]["source"] == "docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml"
    assert sequence[2]["source"] == "docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml"
    assert sequence[3]["source"] == "docs/v2/L7-test-design/additional-improvement-discovery.yaml"
    assert sequence[4]["source"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert sequence[5]["source"] == "docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml"
    assert sequence[6]["source"] == "docs/v2/L7-test-design/goal-completion-audit.yaml"
    assert payload["current_scope_non_completion_boundary"] == {
        "readiness_manifests_are_goal_completion": False,
        "scope_expansion_request_is_goal_completion": False,
        "candidate_generation_is_goal_completion": False,
        "local_l6_focus_clean_is_full_flow_completion": False,
        "completion_requires_external_or_expanded_scope": True,
    }
    assert payload["safety"] == {
        "schema_migration": False,
        "destructive_data_operation": False,
        "auth_or_pii_change": False,
        "external_api_or_infrastructure_change": False,
        "auto_apply_feedback_candidates": False,
    }
    for gate_id in ("G8", "G9", "G12", "G14"):
        assert gate_id in feature_plan
    assert "helix-full-flow-required-gate" in feature_plan
    assert "feedback_closed" in feature_plan
    assert "This PLAN is not completion evidence" in feature_plan


def test_completion_guard_manifests_stay_cross_consistent() -> None:
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    ledger = yaml.safe_load(_read(FULL_FLOW_ACTIVATION_LEDGER_MANIFEST))
    closure_plan = yaml.safe_load(_read(RIGHT_ARM_CLOSURE_PLAN_MANIFEST))
    handover_request = yaml.safe_load(_read(RIGHT_ARM_HANDOVER_REQUEST_MANIFEST))
    ci_readiness = yaml.safe_load(_read(CI_EQUIVALENT_READINESS_MANIFEST))
    feedback_readiness = yaml.safe_load(
        _read(FEEDBACK_ADOPTION_CLOSURE_READINESS_MANIFEST)
    )
    ui_revalidation = yaml.safe_load(_read(UI_ABSENT_WAIVER_REVALIDATION_MANIFEST))

    goal_guards = goal_audit["completion_policy"]["required_before_complete"]
    ledger_guards = {
        item["id"]: item for item in ledger["remaining_completion_guards"]
    }
    assert list(ledger_guards) == goal_guards
    assert goal_audit["completion_policy"]["goal_complete_allowed"] is False
    assert ledger["current_scope_summary"]["full_goal_complete_allowed"] is False

    sources = ledger["sources"]
    assert sources["objective_evidence_matrix"] == str(
        OBJECTIVE_EVIDENCE_MATRIX_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["right_arm_closure_plan"] == str(
        RIGHT_ARM_CLOSURE_PLAN_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["right_arm_handover_request"] == str(
        RIGHT_ARM_HANDOVER_REQUEST_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["ci_equivalent_readiness"] == str(
        CI_EQUIVALENT_READINESS_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["feedback_closure_readiness"] == str(
        FEEDBACK_ADOPTION_CLOSURE_READINESS_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["ui_absent_revalidation"] == str(
        UI_ABSENT_WAIVER_REVALIDATION_MANIFEST.relative_to(REPO_ROOT)
    )
    assert sources["harness_external_tools_feature_plan"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )

    assert ledger_guards["strict_full_flow_overall_clean_true"][
        "readiness_source"
    ] == sources["right_arm_closure_plan"]
    assert closure_plan["global_exit_gate"]["required"] == {
        "overall_clean": True,
        "deferred_count": 0,
        "deferred_gates": [],
    }
    assert closure_plan["completion_boundary"][
        "all_gates_and_feedback_and_ci_required"
    ] is True

    gate_guard = ledger_guards["G8_G9_G12_G14_gate_implemented_and_passed"]
    assert gate_guard["readiness_source"] == sources["right_arm_handover_request"]
    assert gate_guard["current_evidence"] == "deferred_count=3"
    assert handover_request["status"] == "needs_handover_expansion"
    assert handover_request["activation_policy"]["self_expand_current_handover"] is False
    assert {item["gate_id"] for item in handover_request["requested_next_action"]["gates"]} == {
        "G8",
        "G9",
        "G12",
        "G14",
    }

    ci_guard = ledger_guards["CI_or_equivalent_gate_surface_connected"]
    assert ci_guard["readiness_source"] == sources["ci_equivalent_readiness"]
    assert ci_guard["current_status"] == "defined_not_connected"
    assert ci_readiness["readiness_boundary"]["ci_or_equivalent_connected"] is False
    assert ci_readiness["completion_boundary"]["ci_or_equivalent_connected"] is False
    assert ci_readiness["completion_boundary"]["all_right_arm_gates_must_pass_first"] is True

    feedback_guard = ledger_guards[
        "feedback_candidates_adopted_back_to_PLAN_PR_gate_evidence"
    ]
    assert feedback_guard["readiness_source"] == sources["feedback_closure_readiness"]
    assert feedback_guard["current_status"] == "defined_not_closed"
    assert feedback_readiness["readiness_boundary"]["plan_or_pr_adopted"] is False
    assert feedback_readiness["readiness_boundary"]["feedback_closed"] is False
    assert feedback_readiness["completion_boundary"][
        "feedback_closed_requires_gate_and_ci_evidence"
    ] is True

    improvement_guard = ledger_guards["additional_improvement_candidates_adopted_if_selected"]
    assert improvement_guard["readiness_source"] == sources["additional_improvement_discovery"]
    assert improvement_guard["current_status"] == "discovered_not_adopted"

    harness_guard = ledger_guards[
        "HARNESS_external_tools_approved_and_connected_if_selected"
    ]
    assert harness_guard["readiness_source"] == sources[
        "harness_external_tools_feature_plan"
    ]
    assert harness_guard["current_status"] == "feature_ticketed_not_installed"

    ui_guard = ledger_guards[
        "L2_L10_ui_absent_waiver_revalidated_or_unskipped_when_UI_exists"
    ]
    assert ui_guard["readiness_source"] == sources["ui_absent_revalidation"]
    assert ui_guard["current_status"] == "revalidated_currently_not_applicable"
    assert ui_revalidation["current_state"]["revalidated_for_current_scope"] is True
    assert ui_revalidation["completion_boundary"]["waiver_revalidated_is_goal_completion"] is False
    assert ui_revalidation["completion_boundary"]["ui_artifact_exists_requires_L2_L10_scope"] is True


def test_objective_evidence_matrix_maps_user_objective_to_current_evidence() -> None:
    matrix = yaml.safe_load(_read(OBJECTIVE_EVIDENCE_MATRIX_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    activation_ledger = yaml.safe_load(_read(FULL_FLOW_ACTIVATION_LEDGER_MANIFEST))

    assert matrix["schema_version"] == "objective_evidence_matrix_v1"
    assert matrix["status"] == "current_scope_audited_not_complete"
    assert matrix["source_goal_audit"] == str(
        GOAL_COMPLETION_AUDIT_MANIFEST.relative_to(REPO_ROOT)
    )
    assert goal_audit["source_objective_evidence_matrix"] == str(
        OBJECTIVE_EVIDENCE_MATRIX_MANIFEST.relative_to(REPO_ROOT)
    )
    assert matrix["source_activation_ledger"] == str(
        FULL_FLOW_ACTIVATION_LEDGER_MANIFEST.relative_to(REPO_ROOT)
    )
    assert matrix["source_web_evidence_map"] == str(
        WEB_EVIDENCE_SOURCE_MAP_MANIFEST.relative_to(REPO_ROOT)
    )
    assert activation_ledger["sources"]["objective_evidence_matrix"] == str(
        OBJECTIVE_EVIDENCE_MATRIX_MANIFEST.relative_to(REPO_ROOT)
    )
    assert activation_ledger["current_scope_summary"][
        "objective_evidence_matrix_defined"
    ] is True

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
    assert items["OBJ-GRANULARITY-L1-L6"]["status"] == "achieved_local"
    assert items["OBJ-CODEX-CLAUDE-GUARD-PARITY"]["status"] == "achieved_local"
    assert items["OBJ-WEB-EVIDENCE"]["status"] == "achieved_local"
    assert items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["status"] == "achieved_local"
    assert items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["status"] == "partial"
    assert items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["design_gap_status"] == (
        "L6_code16_specs_closed_current_phase_no_l7_artifacts"
    )
    ddd_tdd_artifacts = {
        evidence.get("artifact")
        for evidence in items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["evidence"]
        if isinstance(evidence, dict)
    }
    assert {
        "docs/v2/L6-functional-design/coding-rule-detector-機能設計.md",
        "docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md",
        str(FR_TDD_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_IMPACT_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_INV_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_PLAN_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_EVT_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_GATE_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_DRIFT_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_4ART_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_CHANGEPROP_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_GR_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_DOCTOR_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_9MODE_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_CTX_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_NSM_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_MIGR_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        str(FR_DOCREVIEW_L6_FUNCTION_SPEC.relative_to(REPO_ROOT)),
        "docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md",
        "docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md",
        "cli/config/coding-rule-registry.yaml",
        "cli/config/ddd-registry.yaml",
        "cli/config/functional-registry.yaml",
    }.issubset(ddd_tdd_artifacts)
    assert (
        items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["discovery_status"]
        == "discovered_not_adopted"
    )
    assert (
        items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["adoption_status"]
        == "not_adopted"
    )
    assert items["OBJ-WORKFLOW-AUTOMATION"]["status"] == "partial"
    assert items["OBJ-HARNESS-EXTERNAL-TOOLS"]["status"] == "partial"
    assert items["OBJ-HARNESS-EXTERNAL-TOOLS"]["design_gap_status"] == (
        "L4_L6_closed_L7_feature_ticketed"
    )
    harness_artifacts = {
        evidence.get("artifact")
        for evidence in items["OBJ-HARNESS-EXTERNAL-TOOLS"]["evidence"]
        if isinstance(evidence, dict)
    }
    assert {
        str(HARNESS_EXTERNAL_TOOLS_L4_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_L5_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_L6_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_SCOPE_AUDIT.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)),
    }.issubset(harness_artifacts)
    assert {
        evidence["official_source"]
        for evidence in items["OBJ-HARNESS-EXTERNAL-TOOLS"]["evidence"]
        if isinstance(evidence, dict) and "official_source" in evidence
    } == {
        "https://modelcontextprotocol.io/specification/2025-06-18/basic/index",
        "https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/set-up-the-github-mcp-server",
        "https://docs.semgrep.dev/deployment/oss-deployment",
        "https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning",
    }
    assert items["OBJ-HELIX-DB-FEEDBACK"]["status"] == "partial"
    assert items["OBJ-L0-L14-FLOW"]["status"] == "partial"

    goal_requirements = {item["id"]: item for item in goal_audit["requirements"]}
    assert goal_requirements["REQ-L1-L6-REQUIREMENT-GAP-AUDIT"]["status"] == (
        items["OBJ-REQ-GAP-L6"]["status"]
    )
    assert goal_requirements["REQ-L1-L6-GRANULARITY-BALANCE"]["status"] == (
        items["OBJ-GRANULARITY-L1-L6"]["status"]
    )
    assert goal_requirements["REQ-CODEX-CLAUDE-GUARD-PARITY"]["status"] == (
        items["OBJ-CODEX-CLAUDE-GUARD-PARITY"]["status"]
    )
    assert goal_requirements["REQ-DDD-TDD-AUTO-GOVERNANCE"]["status"] == (
        items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["status"]
    )
    assert goal_requirements["REQ-DDD-TDD-AUTO-GOVERNANCE"][
        "design_gap_status"
    ] == items["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["design_gap_status"]
    assert goal_requirements["REQ-WEB-EVIDENCE"]["status"] == items[
        "OBJ-WEB-EVIDENCE"
    ]["status"]
    assert (
        goal_requirements["REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"][
            "discovery_status"
        ]
        == items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["status"]
    )
    assert (
        goal_requirements["REQ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["adoption_status"]
        == items["OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY"]["adoption_status"]
    )
    assert goal_requirements["REQ-WORKFLOW-AUTOMATION-REVIEW"]["status"] == (
        items["OBJ-WORKFLOW-AUTOMATION"]["status"]
    )
    assert goal_requirements["REQ-HARNESS-EXTERNAL-TOOLS"]["status"] == (
        items["OBJ-HARNESS-EXTERNAL-TOOLS"]["status"]
    )
    assert goal_requirements["REQ-HELIX-DB-FEEDBACK-LOOP"]["status"] == (
        items["OBJ-HELIX-DB-FEEDBACK"]["status"]
    )
    assert goal_requirements["REQ-L0-L14-FLOW"]["status"] == (
        items["OBJ-L0-L14-FLOW"]["status"]
    )

    req_gap_evidence = items["OBJ-REQ-GAP-L6"]["evidence"][0]
    assert req_gap_evidence["command"] == "helix doctor check_requirement_drift --json"
    assert req_gap_evidence["expected"] == {
        "clean": True,
        "focus": "L6",
        "requirements": 31,
        "design_links": 31,
        "blocking_findings": 0,
        "advisory_findings": 0,
    }
    flow_remaining = set(items["OBJ-L0-L14-FLOW"]["remaining_for_full_goal"])
    assert {
        "strict full-flow overall_clean=true",
        "deferred_count=0",
        "G8/G9/G12/G14 removed from deferred_pairs",
        "CI/equivalent gate surface connected",
        "feedback adoption closed",
    }.issubset(flow_remaining)
    assert set(matrix["required_before_complete"]) == set(
        goal_audit["completion_policy"]["required_before_complete"]
    )
    assert matrix["completion_boundary"] == {
        "matrix_is_goal_completion": False,
        "achieved_local_items_are_full_goal_completion": False,
        "partial_items_require_remaining_evidence": True,
        "strict_full_flow_required": True,
        "goal_complete_allowed": False,
    }


def test_objective_l1_l6_coverage_audit_keeps_l7_boundary_and_web_evidence() -> None:
    payload = yaml.safe_load(_read(OBJECTIVE_L1_L6_COVERAGE_AUDIT))
    ratification_index = yaml.safe_load(_read(L1_L6_RATIFICATION_INDEX))
    legacy_classification_payload = yaml.safe_load(
        _read(REPO_ROOT / "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml")
    )

    assert payload["schema_version"] == "objective_l1_l6_coverage_audit_v1"
    assert payload["status"] == "current_scope_l1_l6_closed_not_full_goal"
    assert payload["scope"] == "L1-L6"
    assert payload["source_objective_matrix"] == str(
        OBJECTIVE_L1_L6_COVERAGE_AUDIT.relative_to(REPO_ROOT)
    )
    assert payload["source_asset_inventory"] == str(
        L1_L6_DESIGN_ASSET_INVENTORY.relative_to(REPO_ROOT)
    )
    assert payload["source_improvement_candidate_map"] == str(
        L1_L6_IMPROVEMENT_CANDIDATE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_pair_balance_map"] == str(
        L1_L6_PAIR_BALANCE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_guard_parity_map"] == str(
        L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_deferred_feature_coverage_map"] == str(
        L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_db_feedback_lifecycle_coverage_map"] == str(
        L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_harness_external_tools_coverage_map"] == str(
        L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_governance_hardening_coverage_map"] == str(
        L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_workflow_automation_coverage_map"] == str(
        L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_db_registration_readiness_coverage_map"] == str(
        L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_dependency_impact_readiness_coverage_map"] == str(
        L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_bottleneck_remediation_readiness_coverage_map"] == str(
        L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_full_objective_gap_status"] == str(
        FULL_OBJECTIVE_GAP_STATUS.relative_to(REPO_ROOT)
    )
    assert payload["source_ratification_index"] == str(
        L1_L6_RATIFICATION_INDEX.relative_to(REPO_ROOT)
    )
    assert payload["source_exit_criteria_map"] == str(
        L1_L6_EXIT_CRITERIA_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_reference_integrity_coverage_map"] == str(
        L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_double_check_coverage_map"] == str(
        L1_L6_DOUBLE_CHECK_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_fr31_trace_map"] == str(
        L1_L6_FR31_TRACE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_l1_l6_web_evidence_map"] == str(
        L1_L6_WEB_EVIDENCE_SOURCE_MAP.relative_to(REPO_ROOT)
    )
    assert payload["source_l0_l14_flow_surface_coverage"] == str(
        L0_L14_FLOW_SURFACE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    legacy_classification_path = (
        "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
    )
    assert payload["source_legacy_reference_classification"] == legacy_classification_path
    assert payload["source_deferred_design_obligation_proof"] == str(
        L1_L6_DEFERRED_DESIGN_OBLIGATION_PROOF.relative_to(REPO_ROOT)
    )
    assert payload["scope_boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "current_audit_uses_l7_test_design_as_source": False,
        "l7_implementation_done": False,
        "l7_test_design_created_for_registry_only_frs": False,
        "schema_migration_done": False,
        "external_tool_installed": False,
        "ci_or_equivalent_connected": False,
        "strict_full_flow_complete": False,
        "goal_complete_allowed": False,
    }
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

    evidence = payload["current_l1_l6_evidence"]
    double_check_payload = yaml.safe_load(_read(L1_L6_DOUBLE_CHECK_COVERAGE_MAP))
    evidence_boundary_scan = {
        item["id"]: item for item in double_check_payload["qualitative_checks"]
    }["L-EVIDENCE-BOUNDARY-SCAN"]["expected"]
    assert evidence["asset_inventory"]["artifact"] == str(
        L1_L6_DESIGN_ASSET_INVENTORY.relative_to(REPO_ROOT)
    )
    assert evidence["asset_inventory"]["expected"] == {
        "total_l1_l6_files": 50,
        "l6_functional_design_files": 28,
        "l6_assets_partitioned": True,
        "l6_partition_overlap_allowed": False,
        "l6_partition_clusters": 3,
        "inventory_uses_l7_as_execution_evidence": False,
    }
    assert evidence["improvement_candidates"]["artifact"] == str(
        L1_L6_IMPROVEMENT_CANDIDATE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["improvement_candidates"]["expected"] == {
        "total_candidates": 35,
        "uses_l7_test_design_as_source": False,
        "candidates_adopted": False,
    }
    assert evidence["pair_balance"]["artifact"] == str(
        L1_L6_PAIR_BALANCE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["pair_balance"]["expected"] == {
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
    assert evidence["guard_parity"]["artifact"] == str(
        L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["guard_parity"]["expected"] == {
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
    assert evidence["deferred_feature_coverage"]["artifact"] == str(
        L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["deferred_feature_coverage"]["expected"] == {
        "objective_clauses_checked": 9,
        "deferred_entry_points_checked": 11,
        "feature_tickets_checked": 11,
        "feature_tickets_draft": 11,
        "feature_tickets_with_approval_boundary": 11,
        "feature_tickets_with_unlock_conditions": 11,
        "repository_add_feature_files_discovered": 26,
        "current_objective_deferred_feature_tickets": 11,
        "out_of_current_objective_add_feature_files": 15,
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
    assert evidence["deferred_design_obligation_proof"]["artifact"] == str(
        L1_L6_DEFERRED_DESIGN_OBLIGATION_PROOF.relative_to(REPO_ROOT)
    )
    assert evidence["deferred_design_obligation_proof"]["expected"] == {
        "feature_tickets_checked": 11,
        "feature_tickets_with_prior_l1_l6_design_evidence": 11,
        "feature_tickets_using_ticket_as_design_substitute": 0,
        "design_gap_reopen_rules_defined": 11,
        "escalation_bound_design_tickets_checked": 2,
        "implementation_or_execution_tickets_checked": 9,
        "blocking_findings_current_scope": 0,
        "l7_artifacts_created_by_this_audit": 0,
    }
    assert evidence["db_feedback_lifecycle"]["artifact"] == str(
        L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["db_feedback_lifecycle"]["expected"] == {
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
    db_feedback_expected = evidence["db_feedback_lifecycle"]["expected"]
    db_feedback_payload = yaml.safe_load(_read(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP))
    db_feedback_accountability = db_feedback_payload[
        "feedback_lifecycle_accountability_contract"
    ]
    assert db_feedback_expected[
        "feedback_lifecycle_accountability_contract_present"
    ] is True
    assert db_feedback_expected["feature_ticket_is_not_design_substitute"] == (
        db_feedback_accountability["feature_ticket_is_not_design_substitute"]
    )
    assert db_feedback_expected["db_write_requires_explicit_approval"] == (
        db_feedback_accountability["db_write_requires_explicit_approval"]
    )
    assert db_feedback_expected["current_scope_must_keep_db_write_false"] == (
        db_feedback_accountability["current_scope_must_keep_db_write_false"]
    )
    assert db_feedback_expected[
        "recurrence_closure_requires_later_execution_evidence"
    ] == db_feedback_accountability[
        "recurrence_closure_requires_later_execution_evidence"
    ]
    assert db_feedback_expected["closure_rules_defined"] == len(
        db_feedback_payload["state_machine"]["closure_rules"]
    )
    assert db_feedback_expected["existing_tables_required_for_lifecycle_checked"] == len(
        db_feedback_payload["physical_db_design_evidence"][
            "existing_tables_required_for_lifecycle"
        ]
    )
    assert db_feedback_expected["forbidden_current_scope_rules_checked"] == len(
        db_feedback_payload["storage_mapping_policy"]["forbidden_current_scope"]
    )
    assert evidence["harness_external_tools"]["artifact"] == str(
        L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["harness_external_tools"]["expected"] == {
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
    harness_expected = evidence["harness_external_tools"]["expected"]
    harness_payload = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
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
    assert evidence["governance_hardening"]["artifact"] == str(
        L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["governance_hardening"]["expected"] == {
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
    assert evidence["workflow_automation"]["artifact"] == str(
        L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["workflow_automation"]["expected"] == {
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
    assert evidence["db_registration_readiness"]["artifact"] == str(
        L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["db_registration_readiness"]["expected"] == {
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
    db_registration_expected = evidence["db_registration_readiness"]["expected"]
    db_registration_payload = yaml.safe_load(
        _read(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP)
    )
    db_registration_accountability = db_registration_payload[
        "registration_accountability_contract"
    ]
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
    assert db_registration_expected["event_route_closure_rows_checked"] == (
        db_registration_payload["summary"]["event_route_closure_rows_checked"]
    )
    assert evidence["dependency_impact_readiness"]["artifact"] == str(
        L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["dependency_impact_readiness"]["expected"] == {
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
    assert evidence["bottleneck_remediation_readiness"]["artifact"] == str(
        L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["bottleneck_remediation_readiness"]["expected"] == {
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
    assert evidence["full_objective_gap_status"]["artifact"] == str(
        FULL_OBJECTIVE_GAP_STATUS.relative_to(REPO_ROOT)
    )
    assert evidence["full_objective_gap_status"]["expected"] == {
        "objective_items_checked": 10,
        "current_scope_items_pass_l1_l6": 9,
        "items_requiring_later_phase_before_full_completion": 8,
        "feature_tickets_available": 11,
        "repository_add_feature_files_discovered": 26,
        "current_objective_deferred_feature_tickets": 11,
        "out_of_current_objective_add_feature_files": 15,
        "out_of_current_objective_completed_add_features": 4,
        "out_of_current_objective_parked_feature_tickets": 0,
        "right_arm_execution_gates_deferred": 3,
        "current_scope_verdict": "pass_l1_l6_only",
        "full_goal_verdict": "active_not_complete",
        "full_goal_complete": False,
        "harness_external_tool_accountability_indexed": True,
        "unlock_evidence_namespace": (
            "full_goal_unlock_required_evidence_not_current_scope_proof"
        ),
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
    assert evidence["ratification_index"]["artifact"] == str(
        L1_L6_RATIFICATION_INDEX.relative_to(REPO_ROOT)
    )
    assert evidence["ratification_index"]["expected"] == {
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
        "deferred_repository_add_feature_files_discovered": 26,
        "deferred_current_objective_deferred_feature_tickets": 11,
        "deferred_out_of_current_objective_add_feature_files": 15,
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
        "right_arm_execution_gates_deferred": 3,
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
            "full_objective_repository_add_feature_files_discovered": 26,
            "full_objective_current_objective_deferred_feature_tickets": 11,
            "full_objective_out_of_current_objective_add_feature_files": 15,
            "full_objective_out_of_current_objective_completed_add_features": 4,
            "full_objective_out_of_current_objective_parked_feature_tickets": 0,
            "full_objective_right_arm_execution_gates_deferred": 3,
            "full_objective_blocking_findings_current_l1_l6_scope": 0,
            "full_objective_blocking_findings_full_goal": 8,
            "full_objective_current_scope_verdict": "pass_l1_l6_only",
            "full_objective_full_goal_verdict": "active_not_complete",
        }
    runtime_retrofit = legacy_classification_payload["runtime_retrofit_required"][0]
    handover_boundary = legacy_classification_payload["handover_metadata_boundary"][0]
    assert evidence["ratification_index"]["expected"][
        "legacy_runtime_retrofit_required_items"
    ] == ratification_index["ratification_summary"][
        "legacy_runtime_retrofit_required_items"
    ] == legacy_classification_payload["summary"]["runtime_retrofit_required_items"]
    assert evidence["ratification_index"]["expected"][
        "evidence_boundary_scan_evidence_like_keys_checked"
    ] == ratification_index["ratification_summary"][
        "evidence_boundary_scan_evidence_like_keys_checked"
    ] == len(evidence_boundary_scan["evidence_like_keys_checked"])
    assert evidence["ratification_index"]["expected"][
        "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
    ] == ratification_index["ratification_summary"][
        "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
    ] == evidence_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
    assert evidence["ratification_index"]["expected"][
        "evidence_boundary_scan_current_scope_proof_allows_add_feature"
    ] == ratification_index["ratification_summary"][
        "evidence_boundary_scan_current_scope_proof_allows_add_feature"
    ] == evidence_boundary_scan["current_scope_proof_allows_add_feature"]
    assert evidence["ratification_index"]["expected"][
        "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
    ] == ratification_index["ratification_summary"][
        "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
    ] == evidence_boundary_scan["current_scope_proof_allows_l7_test_design"]
    assert evidence["ratification_index"]["expected"][
        "legacy_runtime_metadata_gap_ticketed"
    ] == ratification_index["ratification_summary"][
        "legacy_runtime_metadata_gap_ticketed"
    ] is bool(runtime_retrofit["observed_metadata_gap"])
    assert evidence["ratification_index"]["expected"][
        "legacy_runtime_feature_ticket_metadata_match_required"
    ] == ratification_index["ratification_summary"][
        "legacy_runtime_feature_ticket_metadata_match_required"
    ] == runtime_retrofit["feature_ticket_metadata_must_match_observed_gap"]
    assert evidence["ratification_index"]["expected"][
        "legacy_runtime_next_action_supersedes_current_json_metadata"
    ] == ratification_index["ratification_summary"][
        "legacy_runtime_next_action_supersedes_current_json_metadata"
    ] == runtime_retrofit["observed_metadata_gap"][
        "next_action_supersedes_current_json_task_metadata"
    ]
    assert evidence["ratification_index"]["expected"][
        "legacy_runtime_safe_task_retitle_command_available_now"
    ] == ratification_index["ratification_summary"][
        "legacy_runtime_safe_task_retitle_command_available_now"
    ] == runtime_retrofit["observed_metadata_gap"][
        "safe_task_retitle_command_available_now"
    ]
    assert evidence["ratification_index"]["expected"][
        "legacy_handover_metadata_boundary_items_checked"
    ] == ratification_index["ratification_summary"][
        "legacy_handover_metadata_boundary_items_checked"
    ] == legacy_classification_payload["summary"][
        "handover_metadata_boundary_items_checked"
    ]
    assert evidence["ratification_index"]["expected"][
        "legacy_handover_current_json_l7_label_authorizes_work"
    ] == ratification_index["ratification_summary"][
        "legacy_handover_current_json_l7_label_authorizes_work"
    ] == legacy_classification_payload["summary"][
        "handover_current_json_l7_label_authorizes_work"
    ]
    assert evidence["ratification_index"]["expected"][
        "legacy_handover_ready_for_review_status_not_completion"
    ] == ratification_index["ratification_summary"][
        "legacy_handover_ready_for_review_status_not_completion"
    ] == legacy_classification_payload["summary"][
        "handover_ready_for_review_status_not_completion"
    ]
    assert evidence["ratification_index"]["expected"][
        "legacy_handover_next_action_is_authoritative"
    ] == ratification_index["ratification_summary"][
        "legacy_handover_next_action_is_authoritative"
    ] == legacy_classification_payload["summary"][
        "handover_next_action_is_authoritative"
    ]
    assert handover_boundary["authoritative_boundary"]["l7_work_requested_by_user"] is False
    assert evidence["exit_criteria"]["artifact"] == str(
        L1_L6_EXIT_CRITERIA_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["exit_criteria"]["expected"] == {
        "exit_layers_checked": 6,
        "exit_layers_pass": 6,
        "exit_layers_with_waiver": 1,
        "gate_ids_checked": ["G1", "G2", "G3", "G4", "G5", "G6"],
        "blocking_findings_current_scope": 0,
        "l7_artifacts_created_by_this_map": 0,
    }
    assert evidence["reference_integrity"]["artifact"] == str(
        L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["reference_integrity"]["expected"] == {
        "audit_files_checked": 25,
        "path_like_refs_checked": 1385,
        "direct_file_refs_checked": 1376,
        "glob_patterns_checked": 9,
        "missing_direct_file_refs": 0,
        "empty_glob_patterns": 0,
        "current_scope_uses_l7_as_completion_evidence": False,
    }
    assert evidence["double_check"]["artifact"] == str(
        L1_L6_DOUBLE_CHECK_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["double_check"]["expected"] == {
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
    assert evidence["double_check"]["expected"][
        "evidence_boundary_scan_evidence_like_keys_checked"
    ] == len(evidence_boundary_scan["evidence_like_keys_checked"])
    assert evidence["double_check"]["expected"][
        "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
    ] == evidence_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
    assert evidence["double_check"]["expected"][
        "evidence_boundary_scan_current_scope_proof_allows_add_feature"
    ] == evidence_boundary_scan["current_scope_proof_allows_add_feature"]
    assert evidence["double_check"]["expected"][
        "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
    ] == evidence_boundary_scan["current_scope_proof_allows_l7_test_design"]
    assert evidence["requirement_drift"]["expected"]["clean"] is True
    assert evidence["requirement_drift"]["expected"]["focus"] == "L6"
    assert evidence["requirement_drift"]["trace_map"] == str(
        L1_L6_FR31_TRACE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["l0_l14_contract"]["pytest_expected"] == "87 passed"
    assert evidence["l0_l14_contract"]["bats_expected"] == "56 tests passed"
    assert evidence["l0_l14_flow_surface"]["artifact"] == str(
        L0_L14_FLOW_SURFACE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert evidence["l0_l14_flow_surface"]["expected"] == {
        "layers_checked": 15,
        "left_arm_design_layers_checked": 6,
            "current_surfaces_checked": 90,
        "banned_legacy_terms_found_current_surfaces": 0,
        "l7_implementation_done": False,
        "goal_complete_allowed": False,
    }
    assert evidence["l7_non_execution_check"] == {
        "command": "find docs/v2/L7-test-design \\( -path '*/FR-FNREG-01/*' -o -path '*/FR-GLOSSARY-01/*' \\) -print",
        "expected_stdout": "",
        "evidence_kind": "negative_boundary_check",
        "proves_l7_execution": False,
        "proves_l7_test_design_creation": False,
        "counts_as_current_scope_completion_proof": False,
    }
    assert evidence["l6_unit_test_design_viewpoints"]["artifact"] == str(
        FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT)
    )
    fr18_l6_unit_test_design_index = yaml.safe_load(
        _read(FR18_L6_UNIT_TEST_DESIGN_INDEX)
    )
    fr18_summary = fr18_l6_unit_test_design_index["coverage_summary"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"] == {
        "fr_count": 18,
        "specs_current_scope_l6_closed": 18,
        "specs_with_l6_unit_test_design_viewpoints": 18,
        "total_ut_candidates": 128,
        "specs_with_draft_status": [],
        "l7_unit_test_design_artifacts_created": False,
    }
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "fr_count"
    ] == fr18_summary["fr_count"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "specs_current_scope_l6_closed"
    ] == fr18_summary["specs_current_scope_l6_closed"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "specs_with_l6_unit_test_design_viewpoints"
    ] == fr18_summary["specs_with_l6_unit_test_design_viewpoints"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "total_ut_candidates"
    ] == fr18_summary["total_ut_candidates"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "specs_with_draft_status"
    ] == fr18_summary["specs_with_draft_status"]
    assert evidence["l6_unit_test_design_viewpoints"]["expected"][
        "l7_unit_test_design_artifacts_created"
    ] == fr18_l6_unit_test_design_index["boundary"][
        "l7_unit_test_design_artifacts_created"
    ]

    clauses = {item["id"]: item for item in payload["objective_clauses"]}
    assert set(clauses) == {
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
    assert evidence["deferred_feature_coverage"]["expected"][
        "objective_clauses_checked"
    ] == len(clauses)
    assert str(L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-DDD-TDD-AUTO-GOVERNANCE"
    ]["proof"]
    assert str(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-DDD-TDD-AUTO-GOVERNANCE"
    ]["proof"]
    assert str(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-WORKFLOW-AUTOMATION"
    ]["proof"]
    assert str(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-HELIX-DB-FEEDBACK"
    ]["proof"]
    assert str(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-HARNESS-EXTERNAL-TOOLS"
    ]["proof"]
    assert legacy_classification_path in clauses["OBJ-L0-L14-FLOW"]["proof"]
    full_gap = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    full_status_ids = {item["id"] for item in full_gap["objective_status"]}
    full_feature_ticket_path_to_id = {
        item["path"]: item["id"] for item in full_gap["feature_ticket_boundaries"]
    }
    full_completion_audit = {
        item["id"]: item for item in full_gap["completion_audit_matrix"]
    }
    deferred_boundary = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    deferred_by_objective = {
        item["objective_id"]: item
        for item in deferred_boundary["objective_boundary_coverage"]
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
    assert set(clause_map) == set(clauses)
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
    assert evidence["full_objective_gap_status"]["expected"][
        "objective_items_checked"
    ] == len(full_gap["objective_status"])
    allowed_read_only_command_prefixes = (
        "helix doctor ",
        "python3 -m pytest ",
        "bats ",
        "find ",
        "python3 -m cli.lib.trace_symmetry ",
    )
    for clause in clauses.values():
        assert clause["proof"], clause["id"]
        if "deferred" in clause["l1_l6_status"] or "candidate" in clause[
            "l1_l6_status"
        ]:
            assert clause["later_phase_boundary"], clause["id"]
        for proof in clause["proof"]:
            assert not proof.startswith("docs/v2/L7-test-design/"), proof
            assert not proof.startswith("docs/plans/add-feature/"), proof
            if proof.startswith(allowed_read_only_command_prefixes):
                continue
            assert (REPO_ROOT / proof).exists(), proof
    assert clauses["OBJ-REQ-GAP-L6"]["l1_l6_status"] == "closed"
    assert str(L1_L6_DESIGN_ASSET_INVENTORY.relative_to(REPO_ROOT)) in clauses[
        "OBJ-REQ-GAP-L6"
    ]["proof"]
    assert clauses["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["l1_l6_status"] == (
        "design_closed_implementation_deferred"
    )
    assert clauses["OBJ-DDD-TDD-AUTO-GOVERNANCE"]["later_phase_boundary"] == [
        "docs/plans/add-feature/add-feature-2026-06-12-fr-registry-glossary-l7-entry.md",
        str(PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN.relative_to(REPO_ROOT)),
    ]
    assert clauses["OBJ-HARNESS-EXTERNAL-TOOLS"]["l1_l6_status"] == (
        "design_and_candidate_discovery_closed"
    )
    assert clauses["OBJ-HARNESS-EXTERNAL-TOOLS"]["later_phase_boundary"][0] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert "installation, auth, license acceptance" in clauses[
        "OBJ-HARNESS-EXTERNAL-TOOLS"
    ]["later_phase_boundary"][1]
    assert clauses["OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"]["l1_l6_status"] == (
        "candidate_map_created_not_adopted"
    )
    assert str(L1_L6_IMPROVEMENT_CANDIDATE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
    ]["proof"]
    assert str(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
    ]["proof"]
    assert str(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
    ]["proof"]
    assert str(L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
    ]["proof"]
    assert str(L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-ADDITIONAL-IMPROVEMENT-L1-L6"
    ]["proof"]
    assert str(L1_L6_PAIR_BALANCE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-GRANULARITY-L1-L6"
    ]["proof"]
    assert str(L1_L6_DOUBLE_CHECK_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-GRANULARITY-L1-L6"
    ]["proof"]
    assert str(L1_L6_RATIFICATION_INDEX.relative_to(REPO_ROOT)) in clauses[
        "OBJ-GRANULARITY-L1-L6"
    ]["proof"]
    assert str(L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-CODEX-CLAUDE-GUARD-PARITY"
    ]["proof"]
    assert clauses["OBJ-CODEX-CLAUDE-GUARD-PARITY"][
        "later_phase_boundary"
    ] == str(CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert str(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-HELIX-DB-FEEDBACK"
    ]["proof"]
    assert str(L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-HELIX-DB-FEEDBACK"
    ]["proof"]
    assert clauses["OBJ-HELIX-DB-FEEDBACK"]["later_phase_boundary"] == [
        str(DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN.relative_to(REPO_ROOT)),
        str(PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN.relative_to(REPO_ROOT)),
    ]
    assert str(L0_L14_FLOW_SURFACE_COVERAGE_MAP.relative_to(REPO_ROOT)) in clauses[
        "OBJ-L0-L14-FLOW"
    ]["proof"]

    sources = {
        item["source_id"]: item
        for item in payload["web_evidence_rechecked_2026_06_12"]
    }
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
    assert set(sources) == set(
        payload["web_evidence_freshness_contract"]["canonical_source_ids"]
    )
    assert "JSON-RPC 2.0 message types" in " ".join(
        sources["MCP-SPEC-2025-06-18"]["confirmed"]
    )
    assert "OAuth by default" in " ".join(sources["GITHUB-MCP-SERVER"]["confirmed"])
    assert "rule licenses" in " ".join(sources["SEMGREP-CE"]["confirmed"])
    assert "database and queries" in " ".join(sources["GITHUB-CODEQL"]["confirmed"])
    assert "static analysis tool for GitHub Actions" in " ".join(
        sources["ZIZMOR-GHA-SECURITY"]["confirmed"]
    )
    assert "static checker for GitHub Actions workflow files" in " ".join(
        sources["ACTIONLINT-GHA-WORKFLOW-LINT"]["confirmed"]
    )
    assert "security health" in " ".join(sources["OPENSSF-SCORECARD"]["confirmed"])
    assert "package, version, requirements" in " ".join(
        sources["DEPSDEV-API"]["confirmed"]
    )
    assert "package extraction and vulnerability matching" in " ".join(
        sources["OSV-SCANNER"]["confirmed"]
    )
    assert "generates SBOMs" in " ".join(
        sources["SYFT-SBOM"]["confirmed"]
    )
    assert "queryable import graphs" in " ".join(
        sources["GRIMP-PYTHON-IMPORT-GRAPH"]["confirmed"]
    )
    assert "validates and visualizes dependencies" in " ".join(
        sources["DEPENDENCY-CRUISER"]["confirmed"]
    )
    assert "static analysis for shell scripts" in " ".join(
        sources["SHELLCHECK-SHELL-STATIC"]["confirmed"]
    )
    assert "Markdown and CommonMark" in " ".join(
        sources["MARKDOWNLINT-CLI2"]["confirmed"]
    )
    assert "lychee is a fast async stream-based link checker written in Rust" in " ".join(
        sources["LYCHEE-LINK-CHECKER"]["confirmed"]
    )
    assert "helix_db_doc_connection_gap_mapping" in sources[
        "LYCHEE-LINK-CHECKER"
    ]["design_controls"]
    assert "code-like linting to prose" in " ".join(
        sources["VALE-PROSE-LINT"]["confirmed"]
    )
    assert "mutation testing system for Python" in " ".join(
        sources["MUTMUT-PY-MUTATION-TESTING"]["confirmed"]
    )
    assert "property-based testing library for Python" in " ".join(
        sources["HYPOTHESIS-PY-PBT"]["confirmed"]
    )
    assert "measures code coverage for Python programs" in " ".join(
        sources["COVERAGE-PY-COVERAGE"]["confirmed"]
    )
    assert "Python test runner" in " ".join(
        sources["PYTEST-PY-TEST-RUNNER"]["confirmed"]
    )
    assert "small readable tests" in " ".join(
        sources["PYTEST-PY-TEST-RUNNER"]["confirmed"]
    )
    assert "virtual environment management" in " ".join(
        sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed"]
    )
    assert "package builds and installs" in " ".join(
        sources["TOX-PY-ENV-ORCHESTRATION"]["confirmed"]
    )
    assert "standard Python file" in " ".join(
        sources["NOX-PY-SESSION-AUTOMATION"]["confirmed"]
    )
    assert "virtualenv creation per session" in " ".join(
        sources["NOX-PY-SESSION-AUTOMATION"]["confirmed"]
    )
    assert "constraints on imports between Python modules" in " ".join(
        sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed"]
    )
    assert "acyclic_siblings contracts" in " ".join(
        sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"]["confirmed"]
    )
    assert "JSON Schema CLI and pre-commit hook" in " ".join(
        sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed"]
    )
    assert "JSON or YAML instance files" in " ".join(
        sources["CHECK-JSONSCHEMA-DOC-SCHEMA"]["confirmed"]
    )
    assert "bad SQL before database execution" in " ".join(
        sources["SQLFLUFF-SQL-LINT"]["confirmed"]
    )
    assert "SQLite" in " ".join(sources["SQLFLUFF-SQL-LINT"]["confirmed"])
    assert "Python linter and code formatter" in " ".join(
        sources["RUFF-PY-LINT-FORMAT"]["confirmed"]
    )
    assert "static type checker for Python" in " ".join(
        sources["MYPY-PY-TYPE-CHECK"]["confirmed"]
    )
    assert "audits Python environments" in " ".join(
        sources["PIP-AUDIT-PY-VULN"]["confirmed"]
    )
    assert "tool_invocation_consent_required" in sources["MCP-SPEC-2025-06-18"][
        "design_controls"
    ]
    assert "secret_storage_policy" in sources["GITHUB-MCP-SERVER"][
        "design_controls"
    ]
    assert "sarif_supported" in sources["SEMGREP-CE"]["design_controls"]
    assert "failure_mode" in sources["GITHUB-CODEQL"]["design_controls"]
    assert "repository_scope" in sources["OPENSSF-SCORECARD"]["design_controls"]
    assert "dependency_graph_scope" in sources["DEPSDEV-API"]["design_controls"]
    assert "vulnerability_database_scope" in sources["OSV-SCANNER"]["design_controls"]
    assert "sbom_source_scope" in sources["SYFT-SBOM"]["design_controls"]
    assert "import_graph_scope" in sources[
        "GRIMP-PYTHON-IMPORT-GRAPH"
    ]["design_controls"]
    assert "dependency_rule_scope" in sources["DEPENDENCY-CRUISER"][
        "design_controls"
    ]
    assert "shell_dialect_policy" in sources["SHELLCHECK-SHELL-STATIC"][
        "design_controls"
    ]
    assert "markdown_source_scope" in sources["MARKDOWNLINT-CLI2"][
        "design_controls"
    ]
    assert "vocabulary_policy" in sources["VALE-PROSE-LINT"]["design_controls"]
    assert "mutant_apply_disabled_until_approved" in sources[
        "MUTMUT-PY-MUTATION-TESTING"
    ]["design_controls"]
    assert "strategy_design_policy" in sources["HYPOTHESIS-PY-PBT"][
        "design_controls"
    ]
    assert "replay_database_policy" in sources["HYPOTHESIS-PY-PBT"][
        "design_controls"
    ]
    assert "branch_coverage_policy" in sources["COVERAGE-PY-COVERAGE"][
        "design_controls"
    ]
    assert "fail_under_policy" in sources["COVERAGE-PY-COVERAGE"][
        "design_controls"
    ]
    assert "test_discovery_policy" in sources["PYTEST-PY-TEST-RUNNER"][
        "design_controls"
    ]
    assert "junitxml_output_policy" in sources["PYTEST-PY-TEST-RUNNER"][
        "design_controls"
    ]
    assert "exit_code_policy" in sources["PYTEST-PY-TEST-RUNNER"][
        "design_controls"
    ]
    assert "environment_matrix_policy" in sources["TOX-PY-ENV-ORCHESTRATION"][
        "design_controls"
    ]
    assert "command_allowlist_policy" in sources["TOX-PY-ENV-ORCHESTRATION"][
        "design_controls"
    ]
    assert "provision_environment_policy" in sources["TOX-PY-ENV-ORCHESTRATION"][
        "design_controls"
    ]
    assert "python_code_review_policy" in sources["NOX-PY-SESSION-AUTOMATION"][
        "design_controls"
    ]
    assert "session_parametrize_policy" in sources["NOX-PY-SESSION-AUTOMATION"][
        "design_controls"
    ]
    assert "venv_backend_policy" in sources["NOX-PY-SESSION-AUTOMATION"][
        "design_controls"
    ]
    assert "contract_type_policy" in sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"][
        "design_controls"
    ]
    assert "layer_order_policy" in sources["IMPORT-LINTER-PY-ARCH-CONTRACTS"][
        "design_controls"
    ]
    assert "schemafile_scope" in sources["CHECK-JSONSCHEMA-DOC-SCHEMA"][
        "design_controls"
    ]
    assert "helix_db_payload_schema_mapping" in sources[
        "CHECK-JSONSCHEMA-DOC-SCHEMA"
    ]["design_controls"]
    assert "sqlite_dialect_policy" in sources["SQLFLUFF-SQL-LINT"][
        "design_controls"
    ]
    assert "helix_db_sql_schema_lint_mapping" in sources["SQLFLUFF-SQL-LINT"][
        "design_controls"
    ]
    assert "unsafe_fix_disabled_until_approved" in sources[
        "RUFF-PY-LINT-FORMAT"
    ]["design_controls"]
    assert "strictness_policy" in sources[
        "MYPY-PY-TYPE-CHECK"
    ]["design_controls"]
    assert "error_code_policy" in sources[
        "MYPY-PY-TYPE-CHECK"
    ]["design_controls"]
    assert "fix_mode_disabled_until_approved" in sources[
        "PIP-AUDIT-PY-VULN"
    ]["design_controls"]
    assert "vulnerability_service_policy" in sources[
        "PIP-AUDIT-PY-VULN"
    ]["design_controls"]

    web_map = yaml.safe_load(_read(L1_L6_WEB_EVIDENCE_SOURCE_MAP))
    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    assert web_map["schema_version"] == "l1_l6_web_evidence_source_map_v1"
    assert web_map["status"] == "verified_l1_l6_design_evidence_not_adoption"
    assert web_map["scope"] == "L1-L6"
    assert web_map["boundary"] == {
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
    web_sources = {item["source_id"]: item for item in web_map["sources"]}
    harness_sources = {
        item["source_id"]: item for item in harness_coverage["official_web_sources"]
    }
    assert set(web_sources) == set(sources)
    assert set(harness_sources) == set(sources)
    latest_core_ids = set(
        payload["web_evidence_freshness_contract"][
            "latest_core_rechecked_source_ids"
        ]
    )
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
        if source_id in latest_core_ids:
            assert harness_source["rechecked_on"] == payload[
                "web_evidence_freshness_contract"
            ]["latest_core_rechecked_on"]
            assert web_source.get("rechecked_on", web_source["verified_on"]) == payload[
                "web_evidence_freshness_contract"
            ]["latest_core_rechecked_on"]
        assert web_source["current_scope_action"] == "L4-L6 design evidence only"
        assert harness_source["current_scope_action"] == "design_evidence_only"
        assert web_source["web_fetch_confirmed"] is True
        assert harness_source["web_fetch_confirmed"] is True
        assert web_source["adoption_decision"] == "not_adopted_current_scope"
        assert harness_source["adoption_decision"] == "not_adopted_current_scope"
        assert web_source["confirmed"]["design_controls"]
        assert set(web_source["confirmed"]["design_controls"]) == set(
            harness_source["design_controls"]
        )

    inventory = yaml.safe_load(_read(L1_L6_DESIGN_ASSET_INVENTORY))
    assert inventory["schema_version"] == "l1_l6_design_asset_inventory_v1"
    assert inventory["status"] == "current_scope_l1_l6_inventory_not_l7"
    assert inventory["scope"] == "L1-L6"
    assert inventory["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "inventory_uses_l7_as_execution_evidence": False,
        "l7_implementation_done": False,
        "l7_test_design_created_by_this_inventory": False,
        "goal_complete_allowed": False,
    }
    assert inventory["asset_counts"] == {
        "l1_requirement_files": 5,
        "l2_screen_design_files": 1,
        "l3_requirement_files": 4,
        "l4_basic_design_files": 6,
        "l5_detailed_design_files": 6,
        "l6_functional_design_files": 28,
        "total_l1_l6_files": 50,
    }
    for layer, count_key in {
        "L1": "l1_requirement_files",
        "L2": "l2_screen_design_files",
        "L3": "l3_requirement_files",
        "L4": "l4_basic_design_files",
        "L5": "l5_detailed_design_files",
        "L6": "l6_functional_design_files",
    }.items():
        files = inventory["layer_assets"][layer]["files"]
        assert len(files) == inventory["asset_counts"][count_key]
        for file_path in files:
            assert (REPO_ROOT / file_path).exists(), file_path
    layer_dirs = {
        "L1": REPO_ROOT / "docs/v2/L1-requirements",
        "L2": REPO_ROOT / "docs/v2/L2-screen-design",
        "L3": REPO_ROOT / "docs/v2/L3-requirements",
        "L4": REPO_ROOT / "docs/v2/L4-basic-design",
        "L5": REPO_ROOT / "docs/v2/L5-detailed-design",
        "L6": REPO_ROOT / "docs/v2/L6-functional-design",
    }
    for layer, layer_dir in layer_dirs.items():
        discovered = sorted(
            str(path.relative_to(REPO_ROOT))
            for path in layer_dir.rglob("*")
            if path.is_file() and path.suffix in {".md", ".yaml"}
        )
        listed = sorted(inventory["layer_assets"][layer]["files"])
        assert listed == discovered, layer
    assert inventory["l6_design_clusters"]["fr_function_specs"]["count"] == 18
    assert inventory["l6_design_clusters"]["detector_and_governance_specs"][
        "count"
    ] == 7
    assert inventory["l6_design_clusters"]["deferred_extension_specs"][
        "count"
    ] == 3
    partition_policy = inventory["l6_design_clusters"]["partition_policy"]
    assert partition_policy == {
        "all_l6_assets_partitioned": True,
        "overlap_allowed": False,
        "fr_specs_source_index": str(
            FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT)
        ),
        "rule": partition_policy["rule"],
    }
    assert "cover the L6 asset list exactly" in partition_policy["rule"]
    assert evidence["asset_inventory"]["expected"]["l6_assets_partitioned"] is (
        partition_policy["all_l6_assets_partitioned"]
    )
    assert evidence["asset_inventory"]["expected"]["l6_partition_overlap_allowed"] is (
        partition_policy["overlap_allowed"]
    )
    assert evidence["asset_inventory"]["expected"]["l6_partition_clusters"] == 3
    fr18_index = yaml.safe_load(_read(FR18_L6_UNIT_TEST_DESIGN_INDEX))
    indexed_fr_specs = {
        item["spec"] for item in fr18_index["fr_specs"]
    }
    discovered_fr_specs = {
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "docs/v2/L6-functional-design").glob(
            "FR-*/function-spec.md"
        )
    }
    detector_specs = set(
        inventory["l6_design_clusters"]["detector_and_governance_specs"]["files"]
    )
    deferred_specs = set(
        inventory["l6_design_clusters"]["deferred_extension_specs"]["files"]
    )
    l6_inventory_files = set(inventory["layer_assets"]["L6"]["files"])
    assert indexed_fr_specs == discovered_fr_specs
    assert len(indexed_fr_specs) == inventory["l6_design_clusters"][
        "fr_function_specs"
    ]["count"]
    assert len(detector_specs) == inventory["l6_design_clusters"][
        "detector_and_governance_specs"
    ]["count"]
    assert len(deferred_specs) == inventory["l6_design_clusters"][
        "deferred_extension_specs"
    ]["count"]
    assert indexed_fr_specs.isdisjoint(detector_specs)
    assert indexed_fr_specs.isdisjoint(deferred_specs)
    assert detector_specs.isdisjoint(deferred_specs)
    assert indexed_fr_specs | detector_specs | deferred_specs == l6_inventory_files
    assert "inventory metadata only" in inventory["preexisting_l7_pair_references"][
        "policy"
    ]
    l6_l7_refs: dict[str, list[str]] = {}
    for l6_path in sorted((REPO_ROOT / "docs/v2/L6-functional-design").rglob("*")):
        if not l6_path.is_file() or l6_path.suffix not in {".md", ".yaml"}:
            continue
        text = _read(l6_path)
        refs = re.findall(
            r"docs/v2/L7-test-design/[^\s`\])]+|\.\./L7-test-design/[^\s`\])]+",
            text,
        )
        if refs:
            l6_l7_refs[str(l6_path.relative_to(REPO_ROOT))] = refs
    normalized_refs = [
        ref.replace("../L7-test-design/", "docs/v2/L7-test-design/")
        for refs in l6_l7_refs.values()
        for ref in refs
    ]
    unique_refs = set(normalized_refs)
    existing_pair_refs = {ref for ref in unique_refs if (REPO_ROOT / ref).exists()}
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
        source_text = _read(REPO_ROOT / source_doc)
        normalized_doc_refs = {
            ref.replace("../L7-test-design/", "docs/v2/L7-test-design/")
            for ref in refs
        }
        if normalized_doc_refs & future_placeholder_refs:
            assert "現在タスクでは作成しない" in source_text, source_doc
    assert inventory["coverage_evidence"]["requirement_drift"]["requirements"] == 31
    assert inventory["completion_denial"]["reason"].startswith(
        "This inventory proves the L1-L6 asset universe"
    )

    improvement_map = yaml.safe_load(_read(L1_L6_IMPROVEMENT_CANDIDATE_MAP))
    assert improvement_map["schema_version"] == "l1_l6_improvement_candidate_map_v1"
    assert improvement_map["status"] == "current_scope_l1_l6_candidates_not_adopted"
    assert improvement_map["scope"] == "L1-L6"
    assert improvement_map["boundary"] == {
        "uses_l7_test_design_as_source": False,
        "candidates_discovered": True,
        "candidates_adopted": False,
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "external_tool_installed": False,
        "helix_db_write_connected": False,
        "ci_or_equivalent_connected": False,
        "goal_complete_allowed": False,
    }
    assert improvement_map["candidate_summary"] == {
        "total_candidates": 35,
        "current_scope_actions": {
            "design_only": 2,
            "feature_ticket_only": 33,
        },
        "candidates_requiring_confirmation": 33,
    }
    discovery_policy = improvement_map["candidate_discovery_policy"]
    assert discovery_policy["intake_triggers"] == [
        "l6_design_gap",
        "web_backed_tool_opportunity",
        "db_feedback_or_workflow_automation_gap",
        "runtime_guard_parity_gap",
        "bottleneck_signal_routing_gap",
    ]
    assert discovery_policy["required_candidate_fields"] == [
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
    assert discovery_policy["allowed_current_scope_actions"] == [
        "design_only",
        "feature_ticket_only",
    ]
    assert discovery_policy["allowed_source_groups"] == [
        "web_evidence",
        "l6_design",
        "deferred_feature_entry_points",
    ]
    assert discovery_policy["safety_fields_required"] == [
        "schema_migration",
        "infrastructure_change",
        "auth_or_pii_change",
    ]
    assert discovery_policy["disallowed_evidence"] == [
        "docs/v2/L7-test-design/",
        "runtime execution without approval",
        "helix db write proof",
        "external tool install proof",
    ]
    assert "Candidate discovery is not closure" in discovery_policy["closure_rule"]
    assert "cannot count as adoption" in discovery_policy["promotion_policy"][
        "feature_ticket_only"
    ]
    candidates = {item["id"]: item for item in improvement_map["candidates"]}
    assert set(candidates) == {
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
    assert {item["candidate_class"] for item in candidates.values()} == {
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
    assert all(
        candidate["intake_trigger"] in discovery_policy["intake_triggers"]
        for candidate in candidates.values()
    )
    assert candidates["L1L6-IMP-MCP-ADMISSION"]["safety"][
        "auth_or_pii_change"
    ] is True
    assert candidates["L1L6-IMP-SEMGREP-SAST"]["current_scope_action"] == (
        "feature_ticket_only"
    )
    assert candidates["L1L6-IMP-CODEQL-IMPACT"]["deferred_feature_plan"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert candidates["L1L6-IMP-ZIZMOR-GHA-SECURITY"][
        "candidate_class"
    ] == "github_actions_workflow_security"
    assert candidates["L1L6-IMP-ACTIONLINT-GHA-WORKFLOW-LINT"][
        "candidate_class"
    ] == "github_actions_workflow_lint"
    assert candidates["L1L6-IMP-ACTIONLINT-GHA-WORKFLOW-LINT"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-ZIZMOR-GHA-SECURITY"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-ZIZMOR-GHA-SECURITY"]["safety"][
        "auth_or_pii_change"
    ] is True
    assert candidates["L1L6-IMP-OPENSSF-SCORECARD"]["safety"][
        "auth_or_pii_change"
    ] is True
    assert candidates["L1L6-IMP-DEPSDEV-DEPENDENCY-INTEL"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-DEPSDEV-DEPENDENCY-INTEL"]["safety"][
        "auth_or_pii_change"
    ] is False
    assert candidates["L1L6-IMP-OSV-VULNERABILITY-SCANNING"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-OSV-VULNERABILITY-SCANNING"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-SYFT-SBOM-GENERATION"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-SYFT-SBOM-GENERATION"]["safety"][
        "auth_or_pii_change"
    ] is False
    assert candidates["L1L6-IMP-GRIMP-PYTHON-IMPORT-GRAPH"][
        "candidate_class"
    ] == "source_dependency_graph"
    assert candidates["L1L6-IMP-DEPENDENCY-CRUISER-JS-TS-GRAPH"][
        "candidate_class"
    ] == "source_dependency_graph"
    assert candidates["L1L6-IMP-SHELLCHECK-SHELL-STATIC"][
        "candidate_class"
    ] == "shell_static_analysis"
    assert candidates["L1L6-IMP-MARKDOWNLINT-CLI2-DOC-LINT"][
        "candidate_class"
    ] == "markdown_static_analysis"
    assert candidates["L1L6-IMP-LYCHEE-LINK-CHECKER"][
        "candidate_class"
    ] == "link_reference_check"
    assert candidates["L1L6-IMP-LYCHEE-LINK-CHECKER"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-LYCHEE-LINK-CHECKER"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-VALE-PROSE-LINT-DDD-GLOSSARY"][
        "candidate_class"
    ] == "prose_style_analysis"
    assert candidates["L1L6-IMP-TEXTLINT-NATURAL-LANGUAGE"][
        "candidate_class"
    ] == "natural_language_lint"
    assert candidates["L1L6-IMP-TEXTLINT-NATURAL-LANGUAGE"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-TEXTLINT-NATURAL-LANGUAGE"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-MUTMUT-PY-TDD-STRENGTH"][
        "candidate_class"
    ] == "python_mutation_testing"
    assert candidates["L1L6-IMP-HYPOTHESIS-PY-PBT"][
        "candidate_class"
    ] == "python_property_based_testing"
    assert candidates["L1L6-IMP-HYPOTHESIS-PY-PBT"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-HYPOTHESIS-PY-PBT"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-COVERAGE-PY-COVERAGE"][
        "candidate_class"
    ] == "python_coverage_measurement"
    assert candidates["L1L6-IMP-COVERAGE-PY-COVERAGE"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-COVERAGE-PY-COVERAGE"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-DIFF-COVER-DIFF-COVERAGE"][
        "candidate_class"
    ] == "python_diff_coverage_quality"
    assert candidates["L1L6-IMP-DIFF-COVER-DIFF-COVERAGE"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-DIFF-COVER-DIFF-COVERAGE"][
        "current_scope_action"
    ] == "feature_ticket_only"
    assert candidates["L1L6-IMP-DIFF-COVER-DIFF-COVERAGE"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-PYTEST-PY-RUNNER"][
        "candidate_class"
    ] == "python_test_runner"
    assert candidates["L1L6-IMP-PYTEST-PY-RUNNER"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-PYTEST-PY-RUNNER"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-PYTEST-TESTMON-IMPACTED-TEST-SELECTION"][
        "candidate_class"
    ] == "python_impacted_test_selection"
    assert candidates["L1L6-IMP-PYTEST-TESTMON-IMPACTED-TEST-SELECTION"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-PYTEST-TESTMON-IMPACTED-TEST-SELECTION"][
        "current_scope_action"
    ] == "feature_ticket_only"
    assert candidates["L1L6-IMP-PYTEST-TESTMON-IMPACTED-TEST-SELECTION"][
        "safety"
    ]["infrastructure_change"] is True
    assert candidates["L1L6-IMP-TOX-PY-ENV-ORCHESTRATION"][
        "candidate_class"
    ] == "python_environment_orchestration"
    assert candidates["L1L6-IMP-TOX-PY-ENV-ORCHESTRATION"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-TOX-PY-ENV-ORCHESTRATION"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-NOX-PY-SESSION-AUTOMATION"][
        "candidate_class"
    ] == "python_session_automation"
    assert candidates["L1L6-IMP-NOX-PY-SESSION-AUTOMATION"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-NOX-PY-SESSION-AUTOMATION"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-IMPORT-LINTER-PY-ARCH-CONTRACTS"][
        "candidate_class"
    ] == "python_architecture_contracts"
    assert candidates["L1L6-IMP-IMPORT-LINTER-PY-ARCH-CONTRACTS"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-IMPORT-LINTER-PY-ARCH-CONTRACTS"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-CHECK-JSONSCHEMA-DOC-SCHEMA"][
        "candidate_class"
    ] == "document_schema_validation"
    assert candidates["L1L6-IMP-CHECK-JSONSCHEMA-DOC-SCHEMA"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-CHECK-JSONSCHEMA-DOC-SCHEMA"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-SPECTRAL-API-CONTRACT-LINT"][
        "candidate_class"
    ] == "api_contract_lint"
    assert candidates["L1L6-IMP-SPECTRAL-API-CONTRACT-LINT"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-SPECTRAL-API-CONTRACT-LINT"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-SQLFLUFF-SQL-LINT"][
        "candidate_class"
    ] == "sql_schema_lint"
    assert candidates["L1L6-IMP-SQLFLUFF-SQL-LINT"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-SQLFLUFF-SQL-LINT"]["safety"][
        "schema_migration"
    ] is False
    assert candidates["L1L6-IMP-SQLFLUFF-SQL-LINT"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-RUFF-PY-CODING-RULES"][
        "candidate_class"
    ] == "python_lint_format"
    assert candidates["L1L6-IMP-MYPY-PY-TYPE-CHECK"][
        "candidate_class"
    ] == "python_type_checking"
    assert candidates["L1L6-IMP-MYPY-PY-TYPE-CHECK"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-MYPY-PY-TYPE-CHECK"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-PIP-AUDIT-PY-VULN"][
        "candidate_class"
    ] == "python_dependency_audit"
    assert candidates["L1L6-IMP-PIP-AUDIT-PY-VULN"][
        "deferred_feature_plan"
    ] == str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-PIP-AUDIT-PY-VULN"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["L1L6-IMP-DEPENDENCY-IMPACT-QUERY"][
        "deferred_feature_plan"
    ] == str(DEPENDENCY_IMPACT_QUERY_L7_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert candidates["L1L6-IMP-BOTTLENECK-ROUTING"]["deferred_feature_plan"] == str(
        BOTTLENECK_ROUTING_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert all(
        not ref.startswith("docs/v2/L7-test-design")
        for candidate in candidates.values()
        for ref in candidate["source_refs"]
    )
    web_source_ids = {item["source_id"] for item in web_map["sources"]}
    for candidate in candidates.values():
        assert all(
            field in candidate
            for field in discovery_policy["required_candidate_fields"]
        ), candidate["id"]
        assert set(candidate["safety"]) == set(
            discovery_policy["safety_fields_required"]
        ), candidate["id"]
        assert candidate["current_scope_action"] in discovery_policy[
            "allowed_current_scope_actions"
        ], candidate["id"]
        assert candidate["source_refs"], candidate["id"]
        assert (REPO_ROOT / candidate["deferred_feature_plan"]).exists()
        if candidate["current_scope_action"] == "feature_ticket_only":
            feature_text = _read(REPO_ROOT / candidate["deferred_feature_plan"])
            feature_meta = yaml.safe_load(feature_text.split("---", 2)[1])
            assert feature_meta["status"] == "draft", candidate["id"]
            assert "approv" in feature_meta["approval_boundary"].lower()
        for ref in candidate["source_refs"]:
            ref_path, _, ref_fragment = ref.partition("#")
            assert (REPO_ROOT / ref_path).exists(), ref
            if ref_fragment:
                assert ref_path == str(L1_L6_WEB_EVIDENCE_SOURCE_MAP.relative_to(REPO_ROOT))
                assert ref_fragment in web_source_ids
    assert all(
        (REPO_ROOT / ref).exists()
        for ref in improvement_map["sources"]["web_evidence"]
    )
    assert all(
        (REPO_ROOT / ref).exists() for ref in improvement_map["sources"]["l6_design"]
    )
    assert all(
        (REPO_ROOT / ref).exists()
        for ref in improvement_map["sources"]["deferred_feature_entry_points"]
    )
    assert improvement_map["completion_denial"]["reason"].startswith(
        "This map proves L1-L6 candidate discovery"
    )

    pair_map = yaml.safe_load(_read(L1_L6_PAIR_BALANCE_MAP))
    assert pair_map["schema_version"] == "l1_l6_pair_balance_map_v1"
    assert pair_map["status"] == "current_scope_l1_l6_pair_balance_not_l7_execution"
    assert pair_map["scope"] == "L1-L6"
    assert pair_map["boundary"] == {
        "current_scope": "L1-L6 design and test-design balance",
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "uses_l7_artifact_as_current_scope_evidence": False,
        "l7_implementation_done": False,
        "unit_test_implementation_done": False,
        "coverage_closure_done": False,
        "strict_full_flow_complete": False,
        "goal_complete_allowed": False,
    }
    assert pair_map["summary"] == {
        "l1_l6_layers_checked": 6,
        "layers_pass": 6,
        "layers_with_waiver": 1,
        "blocking_findings": 0,
        "pair_contract_matrix_layers_checked": 6,
        "paired_artifacts_checked": 6,
        "expected_design_refs_checked": 8,
        "expected_design_refs_backed_by_design_assets": 8,
        "expected_design_refs_missing_from_design_assets": 0,
        "l6_unit_test_design_viewpoint_count": 128,
        "notes": [
            "L2-L10 is not applicable because HELIX-workflows has no UI surface under the current scope.",
            "L4-L9 uses semantic ST-to-TV-to-L4 transitive trace; raw balance remains monitored.",
            "L6 current-scope evidence is the L6 unit-test-design viewpoint index, not new L7 artifacts.",
        ],
    }
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
    assert pair_policy["current_scope_action"] == (
        "validate_l1_l6_design_to_test_design_pair_contract_only"
    )
    assert pair_policy["l7_work_requested_by_user"] is False
    assert pair_policy["l7_artifact_required_for_current_scope"] is False
    assert pair_policy["l7_artifact_creation_allowed_without_feature_ticket"] is False
    assert pair_policy["waiver_allowed_layers"] == ["L2"]
    assert pair_policy["pair_contract_matrix_layers_must_equal_pairs_layers"] is True
    assert pair_policy["paired_artifacts_must_exist"] is True
    assert (
        pair_policy["expected_design_refs_must_be_backed_by_pair_design_assets"]
        is True
    )
    assert (
        pair_policy["expected_design_refs_missing_from_design_assets_allowed"]
        == 0
    )
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

    pair_contracts = {
        item["layer"]: item for item in pair_map["pair_contract_matrix"]
    }
    assert set(pair_contracts) == set(pairs)
    assert pair_map["summary"]["pair_contract_matrix_layers_checked"] == len(
        pair_contracts
    )
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
    assert pair_map["summary"]["expected_design_refs_checked"] == len(
        expected_design_refs
    )
    assert pair_map["summary"]["expected_design_refs_backed_by_design_assets"] == (
        len(expected_design_refs) - len(missing_expected_design_refs)
    )
    assert pair_map["summary"][
        "expected_design_refs_missing_from_design_assets"
    ] == len(missing_expected_design_refs)
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

    def _frontmatter(path: Path) -> dict:
        text = _read(path)
        assert text.startswith("---\n"), path
        return yaml.safe_load(text.split("---", 2)[1])

    for layer, contract in pair_contracts.items():
        assert contract["expected_pair"] == expected_pair_labels[layer]
        assert (
            contract["design_stage"],
            contract["paired_test_design_stage"],
        ) == expected_stage_labels[layer]
        assert contract["design_process_layer"] == layer
        assert not contract["paired_artifact"].startswith("docs/v2/L7-test-design/")
        assert (REPO_ROOT / contract["paired_artifact"]).exists()
        assert contract["expected_pair"] == pairs[layer]["trace_pair"]

        if layer == "L2":
            waiver_meta = _frontmatter(REPO_ROOT / contract["paired_artifact"])
            assert contract["current_scope_status"] == "waiver_present"
            assert contract["expected_test_process_layer"] == "not_applicable"
            assert waiver_meta["process_layer"] == "L2"
            assert waiver_meta["pairs_with"] == contract["expected_pairs_with"]
            assert waiver_meta["applicability"] == "not_applicable"
            assert waiver_meta["reason"] == "ui_absent"
            continue

        if layer == "L6":
            l6_index = yaml.safe_load(_read(REPO_ROOT / contract["paired_artifact"]))
            assert contract["current_scope_status"] == (
                "l6_unit_test_design_viewpoints_only_not_l7_artifact"
            )
            assert contract["expected_test_process_layer"] == "L6"
            assert l6_index["scope"] == contract["expected_scope"]
            assert l6_index["boundary"]["l7_unit_test_design_artifacts_created"] is False
            assert l6_index["boundary"]["l7_implementation_done"] is False
            assert (
                l6_index["coverage_summary"]["created_l7_fr_test_design_artifacts"]
                == []
            )
            continue

        pair_meta = _frontmatter(REPO_ROOT / contract["paired_artifact"])
        assert pair_meta["process_layer"] == contract["expected_test_process_layer"]
        if "expected_pairs_with" in contract:
            assert pair_meta["pairs_with"] == contract["expected_pairs_with"]
        else:
            assert pair_meta["pairs_design"] == contract["expected_design_refs"]
        assert contract["current_scope_status"] == "pair_contract_present"
    assert pairs["L1"]["trace_pair"] == "L1-L14"
    assert pairs["L2"]["verdict"] == "pass_with_waiver"
    assert pairs["L2"]["paired_test_design_assets"] == []
    assert pairs["L2"]["waiver"]["path"] in pairs["L2"]["design_assets"]
    assert pairs["L2"]["metrics"]["applicability"] == "not_applicable"
    assert pairs["L2"]["metrics"]["waiver_reason"] == "ui_absent"
    assert pairs["L3"]["metrics"]["balance_ratio"] == 1.0
    assert pairs["L4"]["metrics"]["balance_ratio"] == 0.67
    assert pairs["L4"]["metrics"]["semantic_excluded_orphan_count"] == 18
    assert pairs["L4"]["monitoring_reason"] == (
        "semantic ST-to-TV-to-L4 transitive trace accepted"
    )
    assert pairs["L5"]["metrics"]["coverage_pct"] == 100.0
    assert pairs["L6"]["paired_test_design_assets"] == [
        str(FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT))
    ]
    assert pairs["L6"]["metrics"]["l6_unit_test_design_viewpoint_count"] == 128
    assert pairs["L6"]["metrics"]["l7_artifacts_created_by_current_scope"] == 0
    assert pairs["L6"]["current_scope_pairing"] == (
        "L6 function specs to L6 unit-test-design viewpoints"
    )
    for pair in pairs.values():
        assert pair["design_assets"], pair["layer"]
        assert pair["design_grain"], pair["layer"]
        if pair["layer"] == "L6":
            assert pair["metrics"]["framework_missing_pair_count"] == 0
        else:
            assert pair["metrics"]["missing_pair_count"] == 0, pair["layer"]
        for ref in pair.get("design_assets", []):
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
        for ref in pair.get("paired_test_design_assets", []):
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
        if pair["layer"] != "L2":
            assert pair["paired_test_design_assets"], pair["layer"]
        if "coverage_pct" in pair["metrics"]:
            assert pair["metrics"]["coverage_pct"] == 100.0, pair["layer"]
    assert pair_map["completion_denial"]["reason"].startswith(
        "This map proves L1-L6 design/test-design balance"
    )

    grain_text = _read(L1_L6_GRAIN_BALANCE_AUDIT)
    inventory = yaml.safe_load(_read(L1_L6_DESIGN_ASSET_INVENTORY))
    ratification = yaml.safe_load(_read(L1_L6_RATIFICATION_INDEX))
    governance_coverage = yaml.safe_load(_read(L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP))
    assert "L1-L6 粒度・バランス監査" in grain_text
    assert "本監査は L7 実装を開始しない" in grain_text
    assert "FR 別 L7 成果物の作成" in grain_text
    assert "add-feature として別起票" in grain_text
    assert "`helix doctor check_requirement_drift --json`" in grain_text
    assert "L0 企画突合" in grain_text
    assert str(L0_PLANNING_DERIVATION_COVERAGE_MAP.relative_to(REPO_ROOT)) in grain_text
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
    doc_readiness_matrix = governance_coverage[
        "documentation_readiness_detection_matrix"
    ]
    assert str(L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP.relative_to(REPO_ROOT)) in grain_text
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
    assert inventory["coverage_evidence"]["grain_balance"]["source"] == str(
        L1_L6_GRAIN_BALANCE_AUDIT.relative_to(REPO_ROOT)
    )
    assert inventory["coverage_evidence"]["grain_balance"][
        "l1_l6_current_scope_status"
    ] == "pass"
    rat_grain = next(
        item
        for item in ratification["ratified_l1_l6_items"]
        if item["id"] == "RAT-GRAIN-BALANCE"
    )
    assert str(L1_L6_GRAIN_BALANCE_AUDIT.relative_to(REPO_ROOT)) in rat_grain[
        "evidence"
    ]
    assert str(L1_L6_PAIR_BALANCE_MAP.relative_to(REPO_ROOT)) in rat_grain["evidence"]
    assert "full-flow 完了ではない" in grain_text

    guard_map = yaml.safe_load(_read(L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP))
    assert guard_map["schema_version"] == "l1_l6_codex_claude_guard_parity_map_v1"
    assert guard_map["status"] == "current_scope_l1_l6_guard_parity_defined"
    assert guard_map["scope"] == "L1-L6"
    assert guard_map["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "parity_map_is_closure": False,
        "new_hook_implementation_done": False,
        "new_codex_runtime_enforcement_done": False,
        "goal_complete_allowed": False,
    }
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
    assert guard_map["deferred_feature_plan"] == str(
        CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert guard_map["deferred_feature_plan"] in guard_map["sources"][
        "deferred_feature_entry_points"
    ]
    parity_policy = guard_map["parity_status_policy"]
    assert set(parity_policy) == {
        "defined_common_policy",
        "codex_runtime_defined",
        "codex_runtime_tested",
        "l6_design_only",
        "future_plan_required",
    }
    assert guard_map["summary"]["parity_status_policies_checked"] == len(
        parity_policy
    )
    assert all(
        policy["counts_as_closure"] is False for policy in parity_policy.values()
    )
    assert parity_policy["codex_runtime_defined"][
        "counts_as_codex_runtime_evidence"
    ] is True
    assert parity_policy["codex_runtime_tested"][
        "counts_as_codex_runtime_evidence"
    ] is True
    assert parity_policy["l6_design_only"]["counts_as_l6_design_only"] is True
    assert parity_policy["future_plan_required"]["counts_as_l6_design_only"] is True
    assert guard_map["classification_rules"] == [
        "ClaudeCode hook-only behavior cannot count as parity closure.",
        "Codex parity closure requires Codex runtime, harness, doctor, or post-validation evidence.",
        "L6 design-only parity closes design gaps but does not install hooks or enforce runtime behavior.",
        "Future-plan-required parity must stay in add-feature until explicitly approved.",
    ]
    assert guard_map["summary"]["parity_classification_rules_checked"] == len(
        guard_map["classification_rules"]
    )
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
    assert guard_map["summary"][
        "parity_accountability_current_scope_proves_checked"
    ] == len(guard_map["parity_accountability_contract"]["current_scope_proves"])
    assert guard_map["summary"][
        "parity_accountability_current_scope_does_not_prove_checked"
    ] == len(guard_map["parity_accountability_contract"]["current_scope_does_not_prove"])
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
    assert guard_map["summary"]["parity_closure_required_fields_checked"] == len(
        closure_policy["required_fields"]
    )
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
    assert guard_map["summary"]["parity_route_required_fields_checked"] == len(
        route_policy["required_route_fields"]
    )
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
    assert guard_map["summary"]["parity_normalization_required_fields_checked"] == len(
        normalization_policy["required_contract_fields"]
    )
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
    assert (
        parity_routes["GPAR-WSC-HOOK-PARITY-CARRY"]["next_action"]
        == "route_to_deferred_feature_plan"
    )
    assert (
        parity_routes["GPAR-GUARDRAIL-PARITY-AXIS"]["feedback_target"]
        == "feedback_event"
    )
    assert (
        parity_routes["GPAR-HANDOVER-METADATA-BOUNDARY"]["detector_route"]
        == "handover_legacy_metadata_misread_gap"
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
        assert (
            contract["lifecycle_state"]
            in normalization_policy["allowed_lifecycle_states"]
        )
        assert (
            contract["severity_floor"]
            in normalization_policy["allowed_severity_floors"]
        )
        assert (
            contract["completion_guard"]
            in normalization_policy["allowed_completion_guards"]
        )
        assert contract["feedback_route"], surface_id
    assert (
        normalization_contracts["GPAR-GUARDRAIL-PARITY-AXIS"]["severity_floor"]
        == "P1"
    )
    assert (
        normalization_contracts["GPAR-WSC-HOOK-PARITY-CARRY"]["db_target"]
        == "feedback_event"
    )
    assert (
        normalization_contracts["GPAR-WSC-HOOK-PARITY-CARRY"]["completion_guard"]
        == "plan_materialized_is_not_closure"
    )
    assert (
        normalization_contracts["GPAR-HANDOVER-METADATA-BOUNDARY"][
            "normalized_finding_type"
        ]
        == "handover_legacy_l7_metadata_misread_gap"
    )
    closure_requirements = {
        item["surface_id"]: item for item in guard_map["parity_closure_requirements"]
    }
    assert set(closure_requirements) == set(guard_surfaces)
    assert guard_map["summary"]["parity_closure_requirements_checked"] == len(
        closure_requirements
    )
    for surface_id, requirement in closure_requirements.items():
        for field in closure_policy["required_fields"]:
            assert field in requirement, surface_id
        assert requirement["parity_status"] == guard_surfaces[surface_id][
            "parity_status"
        ]
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
    assert closure_requirements["GPAR-WSC-HOOK-PARITY-CARRY"][
        "current_scope_result"
    ] == "future_plan_required_no_l7_artifact"
    assert "approved_feature_ticket" in closure_requirements[
        "GPAR-WSC-HOOK-PARITY-CARRY"
    ]["missing_before_closure"]
    assert closure_requirements["GPAR-CODEX-DESIGN-WEB-EVIDENCE"][
        "current_evidence_class"
    ] == "codex_post_validation_test"
    assert closure_requirements["GPAR-HANDOVER-METADATA-BOUNDARY"][
        "current_scope_result"
    ] == "policy_defined_not_closure"
    assert guard_map["summary"]["codex_runtime_evidence_surfaces"] == len(
        [
            surface
            for surface in guard_surfaces.values()
            if parity_policy[surface["parity_status"]][
                "counts_as_codex_runtime_evidence"
            ]
        ]
    )
    assert guard_map["summary"]["l6_design_only_surfaces"] == len(
        [
            surface
            for surface in guard_surfaces.values()
            if parity_policy[surface["parity_status"]]["counts_as_l6_design_only"]
        ]
    )
    assert guard_map["summary"]["future_plan_required_surfaces"] == len(
        [
            surface
            for surface in guard_surfaces.values()
            if surface["parity_status"] == "future_plan_required"
        ]
    )
    assert guard_surfaces["GPAR-CODEX-DESIGN-WEB-EVIDENCE"][
        "parity_status"
    ] == "codex_runtime_tested"
    assert guard_surfaces["GPAR-CONTEXT-INJECTION-PARITY"][
        "parity_status"
    ] == "l6_design_only"
    assert guard_surfaces["GPAR-WSC-HOOK-PARITY-CARRY"][
        "parity_status"
    ] == "future_plan_required"
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
    codex_adapter_text = _read(REPO_ROOT / "helix/CODEX_RUNTIME_ADAPTER.md")
    assert "`skills/SKILL_MAP.md`" in codex_adapter_text
    assert "工程・ゲート・スキル一覧の索引として Core Read" in codex_adapter_text
    assert "個別 `SKILL.md` 本文は常時一括読込しない" in codex_adapter_text
    assert "`skills/SKILL_MAP.md` は常時読込対象ではない" not in codex_adapter_text
    for section_refs in guard_map["sources"].values():
        for ref in section_refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for surface in guard_surfaces.values():
        assert surface["source_refs"], surface["id"]
        assert surface["codex_control"], surface["id"]
        assert surface["claude_control"], surface["id"]
        assert surface["parity_status"] in parity_policy, surface["id"]
        assert parity_policy[surface["parity_status"]]["counts_as_closure"] is False
        for ref in surface["source_refs"]:
            assert not ref.startswith("docs/v2/L7-test-design/"), surface["id"]
            assert (REPO_ROOT / ref).exists(), ref
        assert surface["current_gap"]
        if surface["parity_status"] == "codex_runtime_tested":
            assert any(ref.startswith("cli/lib/") for ref in surface["source_refs"])
            assert any("/tests/" in ref or ref.startswith("cli/tests/") for ref in surface["source_refs"])
        if surface["current_scope_status"] in {
            "design_closed_implementation_deferred",
            "inventory_and_design_only",
        }:
            assert all(ref.startswith("docs/v2/L6-functional-design/") for ref in surface["source_refs"])
            assert surface["current_gap"] != "none_for_current_design_doc_web_evidence_surface"
        if surface["parity_status"] == "future_plan_required":
            assert "future PLAN work" in surface["current_gap"]
            assert guard_map["deferred_feature_plan"] in guard_map["sources"][
                "deferred_feature_entry_points"
            ]
    assert any(
        "Claude hook behavior cannot be counted as Codex parity" in requirement
        for requirement in guard_map["adoption_requirements"]
    )
    assert "ClaudeCode hook-only behavior cannot count as parity closure." in guard_map[
        "classification_rules"
    ]
    assert any(
        "L6 design contracts can close design gaps only" in requirement
        for requirement in guard_map["adoption_requirements"]
    )
    assert guard_map["summary"]["parity_adoption_requirements_checked"] == len(
        guard_map["adoption_requirements"]
    )
    feature_plan_text = _read(CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN)
    feature_plan_meta = yaml.safe_load(feature_plan_text.split("---", 2)[1])
    assert feature_plan_meta["status"] == "draft"
    assert feature_plan_meta["layer"] == "L7"
    assert "explicit approval" in feature_plan_meta["approval_boundary"]
    assert "This add-feature ticket exists because the current task stops at L6" in feature_plan_text
    assert "ClaudeCode hook-only behavior cannot count as parity closure" in feature_plan_text
    assert guard_map["completion_denial"]["reason"].startswith(
        "This map proves current L1-L6 guard parity"
    )

    deferred_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    full_gap = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    full_unlock_targets = full_gap["feature_ticket_unlock_contract"]["targets"]
    expected_unlock_tokens_by_ticket = {
        feature_id: target["required_unlock_tokens"]
        for feature_id, target in full_unlock_targets.items()
    }
    assert deferred_coverage["schema_version"] == "l1_l6_deferred_feature_coverage_v1"
    assert deferred_coverage["status"] == "current_scope_l1_l6_deferred_boundaries_mapped"
    assert deferred_coverage["scope"] == "L1-L6"
    assert deferred_coverage["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "coverage_map_is_implementation_evidence": False,
        "l7_test_design_created_by_this_audit": False,
        "l7_implementation_done": False,
        "schema_migration_done": False,
        "external_tool_installed": False,
        "ci_or_equivalent_connected": False,
        "goal_complete_allowed": False,
    }
    assert deferred_coverage["summary"] == {
        "objective_clauses_checked": 9,
        "deferred_entry_points_checked": 11,
        "feature_tickets_checked": 11,
        "feature_tickets_draft": 11,
        "feature_tickets_with_approval_boundary": 11,
        "feature_tickets_with_unlock_conditions": 11,
        "repository_add_feature_files_discovered": 26,
        "current_objective_deferred_feature_tickets": 11,
        "out_of_current_objective_add_feature_files": 15,
        "out_of_current_objective_completed_add_features": 4,
        "out_of_current_objective_parked_feature_tickets": 0,
        "full_flow_later_phase_approval_boundary": True,
        "clauses_without_deferred_work": 1,
        "clauses_mapped_to_feature_ticket": 8,
        "unmapped_deferred_boundaries": 0,
        "l7_artifacts_created_by_this_audit": 0,
    }
    covered_objectives = {
        item["objective_id"]: item
        for item in deferred_coverage["objective_boundary_coverage"]
    }
    assert set(covered_objectives) == set(clauses)
    assert covered_objectives["OBJ-REQ-GAP-L6"]["feature_entry_points"] == []
    assert covered_objectives["OBJ-CODEX-CLAUDE-GUARD-PARITY"][
        "feature_entry_points"
    ] == [str(CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN.relative_to(REPO_ROOT))]
    for refs in deferred_coverage["sources"].values():
        for ref in refs:
            assert (REPO_ROOT / ref).exists(), ref
    for item in covered_objectives.values():
        for ref in item["feature_entry_points"]:
            assert (REPO_ROOT / ref).exists(), ref
            assert not ref.startswith("docs/v2/L7-test-design"), ref

    tickets = {
        item["id"]: item for item in deferred_coverage["feature_ticket_integrity"]
    }
    repository_inventory = deferred_coverage["repository_add_feature_inventory"]
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
    source_entry_points = set(
        deferred_coverage["sources"]["deferred_feature_entry_points"]
    )
    ticket_paths = {item["path"] for item in tickets.values()}
    objective_entry_points = {
        ref
        for item in covered_objectives.values()
        for ref in item["feature_entry_points"]
    }
    assert ticket_paths == source_entry_points
    assert objective_entry_points == ticket_paths
    assert deferred_coverage["summary"]["deferred_entry_points_checked"] == len(
        source_entry_points
    )
    assert deferred_coverage["summary"]["feature_tickets_checked"] == len(tickets)
    assert deferred_coverage["summary"]["feature_tickets_draft"] == sum(
        1 for item in tickets.values() if item["status"] == "draft"
    )
    assert deferred_coverage["summary"][
        "feature_tickets_with_approval_boundary"
    ] == sum(1 for item in tickets.values() if item["approval_boundary_required"])
    assert deferred_coverage["summary"][
        "feature_tickets_with_unlock_conditions"
    ] == sum(1 for item in tickets.values() if item.get("unlock_conditions"))
    repository_add_feature_files = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "docs/plans/add-feature").glob("add-feature-*.md")
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
    assert deferred_coverage["summary"][
        "repository_add_feature_files_discovered"
    ] == len(repository_add_feature_files)
    assert deferred_coverage["summary"][
        "current_objective_deferred_feature_tickets"
    ] == len(tickets)
    assert deferred_coverage["summary"][
        "out_of_current_objective_add_feature_files"
    ] == len(excluded_inventory)
    assert deferred_coverage["summary"][
        "out_of_current_objective_completed_add_features"
    ] == sum(
        1
        for item in excluded_inventory.values()
        if item["classification"] == "historical_completed_feature"
    )
    assert deferred_coverage["summary"][
        "out_of_current_objective_parked_feature_tickets"
    ] == sum(
        1
        for item in excluded_inventory.values()
        if item["classification"] == "parked_feature_ticket_outside_current_objective_set"
    )
    assert set(repository_inventory["current_objective_ticket_ids"]) == set(tickets)
    assert repository_inventory[
        "exclusion_is_completion_evidence_for_current_objective"
    ] is False
    assert repository_inventory["exclusion_may_hide_current_l1_l6_design_debt"] is False
    assert repository_inventory["l7_work_allowed_by_inventory"] is False
    assert set(repository_add_feature_files) == ticket_paths | {
        item["path"] for item in excluded_inventory.values()
    }
    assert excluded_inventory["detector_failclose_ci_gate"][
        "classification"
    ] == "current_scope_authorized_ci_enforcement"
    assert excluded_inventory["detector_failclose_ci_gate"][
        "observed_status"
    ] == "completed"
    assert all((REPO_ROOT / item["path"]).exists() for item in excluded_inventory.values())
    assert deferred_coverage["feature_ticket_unlock_condition_contract"] == {
        "source_contract": (
            "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml"
            "#feature_ticket_unlock_contract"
        ),
        "current_scope_action": "verify_unlock_condition_metadata_only",
        "unlock_conditions_are_completion_evidence": False,
        "l7_execution_allowed_by_unlock_conditions": False,
        "required_feature_ticket_ids": list(expected_unlock_tokens_by_ticket),
        "required_unlock_condition_tokens_by_ticket": expected_unlock_tokens_by_ticket,
    }
    assert deferred_coverage["summary"]["clauses_without_deferred_work"] == sum(
        1 for item in covered_objectives.values() if not item["feature_entry_points"]
    )
    assert deferred_coverage["summary"]["clauses_mapped_to_feature_ticket"] == sum(
        1 for item in covered_objectives.values() if item["feature_entry_points"]
    )
    assert all(item["workflow"] == "add-feature" for item in tickets.values())
    assert all(item["status"] == "draft" for item in tickets.values())
    assert all(
        item["ticket_is_completion_evidence"] is False for item in tickets.values()
    )
    assert all(
        item["approval_boundary_required"] is True for item in tickets.values()
    )
    assert all("unlock_conditions" in item for item in tickets.values())
    assert {
        ticket_id: ticket["unlock_conditions"]
        for ticket_id, ticket in tickets.items()
    } == expected_unlock_tokens_by_ticket
    assert tickets["full_flow_remaining_guards"][
        "approval_required_before_later_phase_work"
    ] is True
    assert tickets["full_flow_remaining_guards"][
        "approval_required_before_implementation"
    ] is True
    assert tickets["db_evidence_lifecycle"][
        "approval_required_before_l7_work"
    ] is True
    assert tickets["db_evidence_lifecycle"]["unlock_conditions"] == [
        "db_write",
        "document_auto_registration",
        "feedback_loop",
        "recurrence_closure",
    ]
    assert tickets["harness_external_tools"]["approval_required_before_l7_work"] is True
    assert tickets["harness_external_tools"][
        "approval_required_before_install"
    ] is True
    assert tickets["harness_external_tools"][
        "external_tool_installation_allowed_now"
    ] is False
    assert tickets["plan_registry_add_feature_import"][
        "approval_required_before_l7_work"
    ] is True
    assert tickets["plan_registry_add_feature_import"]["unlock_conditions"] == [
        "plan_registry",
        "plan_registry_import",
        "add_feature",
    ]
    assert tickets["codex_claude_guard_parity"][
        "approval_required_before_l7_work"
    ] is True
    assert tickets["fr_registry_glossary"]["approval_required_before_l7_work"] is True
    assert tickets["contract_design_phase_label_retrofit"][
        "approval_required_before_contract_edit"
    ] is True
    for ticket in tickets.values():
        plan_path = REPO_ROOT / ticket["path"]
        assert plan_path.exists(), ticket["id"]
        plan_text = _read(plan_path)
        plan_meta = yaml.safe_load(plan_text.split("---", 2)[1])
        assert plan_meta["plan_id"] == plan_path.stem
        assert plan_meta["workflow"] == ticket["workflow"]
        assert plan_meta["kind"] == ticket["kind"]
        assert plan_meta["layer"] == ticket["layer"]
        assert plan_meta["status"] == ticket["status"]
        if "current_task_scope" in ticket:
            assert plan_meta["current_task_scope"] == ticket["current_task_scope"]
        if "approval_required_before_l7_work" in ticket:
            assert plan_meta["approval_required_before_l7_work"] == ticket[
                "approval_required_before_l7_work"
            ]
        if "approval_required_before_later_phase_work" in ticket:
            assert plan_meta["approval_required_before_later_phase_work"] == ticket[
                "approval_required_before_later_phase_work"
            ]
        if "approval_required_before_implementation" in ticket:
            assert plan_meta["approval_required_before_implementation"] == ticket[
                "approval_required_before_implementation"
            ]
        if "approval_required_before_install" in ticket:
            assert plan_meta["approval_required_before_install"] == ticket[
                "approval_required_before_install"
            ]
        if "approval_required_before_contract_edit" in ticket:
            assert plan_meta["approval_required_before_contract_edit"] == ticket[
                "approval_required_before_contract_edit"
            ]
        assert "approval_boundary" in plan_meta
        assert "This PLAN is only a ticket" in plan_meta["approval_boundary"]
        assert plan_meta["unlock_conditions"] == ticket["unlock_conditions"]
        if ticket["id"] == "contract_design_phase_label_retrofit":
            assert plan_meta["current_scope_non_actions"] == {
                "contract_edit_performed": False,
                "schema_migration_done": False,
                "l7_work_performed": False,
                "helix_db_write_performed": False,
                "ci_or_equivalent_connected": False,
            }
            matrix = {
                item["surface"]: item
                for item in plan_meta["contract_semantics_preservation_matrix"]
            }
            assert set(matrix) == {"D-API", "D-DB", "D-CONTRACT"}
            assert matrix["D-API"]["allowed_after_approval"] == (
                "terminology_and_carry_boundary_labels_only"
            )
            assert matrix["D-DB"]["allowed_after_approval"] == (
                "terminology_and_migration_carry_labels_only"
            )
            assert matrix["D-CONTRACT"]["allowed_after_approval"] == (
                "terminology_and_gate_reference_labels_only"
            )
            assert "endpoint_shape_change" in matrix["D-API"][
                "forbidden_without_expanded_approval"
            ]
            assert "table_shape_change" in matrix["D-DB"][
                "forbidden_without_expanded_approval"
            ]
            assert "event_schema_change" in matrix["D-CONTRACT"][
                "forbidden_without_expanded_approval"
            ]
            assert all(
                "review_diff_is_label_only"
                in item["required_evidence_after_approval"]
                for item in matrix.values()
            )
            references = {
                item["source_id"]: item
                for item in plan_meta["external_reference_basis"]
            }
            assert set(references) == {
                "OPENAPI-SPEC-3-2-0",
                "JSON-SCHEMA-VALIDATION-2020-12",
                "POSTGRESQL-ALTER-TABLE-CURRENT",
            }
            assert references["OPENAPI-SPEC-3-2-0"]["source_type"] == "official_spec"
            assert references["JSON-SCHEMA-VALIDATION-2020-12"][
                "source_type"
            ] == "official_spec"
            assert references["POSTGRESQL-ALTER-TABLE-CURRENT"][
                "source_type"
            ] == "official_docs"
            assert references["OPENAPI-SPEC-3-2-0"]["applies_to"] == ["D-API"]
            assert references["JSON-SCHEMA-VALIDATION-2020-12"]["applies_to"] == [
                "D-CONTRACT"
            ]
            assert references["POSTGRESQL-ALTER-TABLE-CURRENT"]["applies_to"] == [
                "D-DB"
            ]
            assert all(item["checked_on"] == datetime.date(2026, 6, 13) for item in references.values())


def test_deferred_feature_ticket_frontmatter_keeps_l7_work_unapproved() -> None:
    deferred_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    tickets = {
        item["id"]: item for item in deferred_coverage["feature_ticket_integrity"]
    }

    for ticket in tickets.values():
        plan_path = REPO_ROOT / ticket["path"]
        plan_text = _read(plan_path)
        plan_meta = yaml.safe_load(plan_text.split("---", 2)[1])
        assert plan_meta["workflow"] == "add-feature"
        assert plan_meta["status"] == "draft"
        assert "approval_boundary" in plan_meta
        assert "This PLAN is only a ticket" in plan_meta["approval_boundary"]
        assert any(
            phrase in plan_text
            for phrase in (
                "feature ticket only",
                "This add-feature ticket",
                "feature ticket",
                "起票",
            )
        )
        assert any(
            phrase in plan_text
            for phrase in (
                "explicit approval",
                "明示承認",
                "承認後",
                "approved",
            )
        )
        assert any(
            phrase in plan_text
            for phrase in (
                "Current task execution",
                "current task does not",
                "現在タスク",
                "現在フェーズ",
            )
        )
        assert any(
            phrase in plan_text
            for phrase in (
                "not completion evidence",
                "not a completed",
                "completion evidence",
                "closure 不可",
                "完了",
            )
        )
        assert "completion" not in ticket["id"] or ticket["ticket_is_completion_evidence"] is False

    assert tickets["full_flow_remaining_guards"]["layer"] == "L8-L14"
    assert tickets["full_flow_remaining_guards"][
        "approval_required_before_implementation"
    ] is True
    assert tickets["db_evidence_lifecycle"]["layer"] == "L7"
    assert tickets["db_evidence_lifecycle"][
        "approval_required_before_l7_work"
    ] is True
    assert tickets["harness_external_tools"]["layer"] == "L6"
    assert tickets["harness_external_tools"][
        "external_tool_installation_allowed_now"
    ] is False
    assert tickets["codex_claude_guard_parity"]["layer"] == "L7"
    assert tickets["fr_registry_glossary"]["layer"] == "L7"
    assert tickets["plan_registry_add_feature_import"]["layer"] == "L7"
    assert tickets["contract_design_phase_label_retrofit"]["kind"] == "add-design"
    assert tickets["contract_design_phase_label_retrofit"]["layer"] == "L5-L6"
    assert tickets["contract_design_phase_label_retrofit"][
        "approval_required_before_contract_edit"
    ] is True
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
    assert "contract semantics" in deferred_coverage["design_escalation_boundary"][
        "reason"
    ]
    assert deferred_coverage["completion_denial"]["reason"].startswith(
        "This audit proves deferred boundary coverage"
    )


def test_dependency_impact_readiness_maps_query_and_inventory_without_l7_artifact() -> None:
    payload = yaml.safe_load(_read(L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP))

    assert payload["schema_version"] == (
        "l1_l6_dependency_impact_readiness_coverage_v1"
    )
    assert payload["status"] == (
        "current_scope_l1_l6_dependency_impact_readiness_mapped"
    )
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "dependency_impact_map_is_implementation_evidence": False,
        "impact_query_cli_implemented": False,
        "helix_db_write_performed": False,
        "schema_migration_done": False,
        "external_tool_executed": False,
        "ci_or_equivalent_connected": False,
        "l7_test_design_created_by_this_audit": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
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
        "blocking_findings_current_scope": 0,
        "l7_artifacts_created_by_this_audit": 0,
    }

    surfaces = {item["id"]: item for item in payload["coverage_surfaces"]}
    assert set(surfaces) == {
        "DEPIMP-IMPACT-QUERY",
        "DEPIMP-ASSET-INVENTORY",
        "DEPIMP-PLAN-GRAPH",
        "DEPIMP-CHANGE-PROPAGATION",
        "DEPIMP-HARNESS-TOOLS",
        "DEPIMP-SOURCE-DEPENDENCY-GRAPH",
        "DEPIMP-DB-FEEDBACK",
    }
    assert payload["summary"]["dependency_impact_surfaces_checked"] == len(surfaces)
    assert payload["summary"]["l6_function_specs_checked"] == len(
        payload["sources"]["l6_function_specs"]
    )
    assert payload["summary"]["current_code_surfaces_checked_read_only"] == len(
        payload["sources"]["current_code_surfaces_read_only"]
    )
    assert payload["summary"]["deferred_feature_entry_points_checked"] == len(
        payload["sources"]["deferred_feature_entry_points"]
    )
    assert payload["summary"]["required_output_sections"] == len(
        payload["required_output_contract"]
    )
    assert all(value == "required" for value in payload["required_output_contract"].values())
    assert "IMPACT-FN-03 collect_dependency_edges" in surfaces[
        "DEPIMP-IMPACT-QUERY"
    ]["covered_functions"]
    assert "INV-FN-04 detect_unregistered_assets" in surfaces[
        "DEPIMP-ASSET-INVENTORY"
    ]["covered_functions"]
    assert "HEXT-FN-05 build_dependency_impact_graph" in surfaces[
        "DEPIMP-HARNESS-TOOLS"
    ]["covered_functions"]
    assert payload["required_output_contract"] == {
        "seed": "required",
        "affected_plans": "required",
        "affected_design_docs": "required",
        "affected_test_design_docs": "required",
        "affected_code_paths": "required",
        "affected_gates": "required",
        "dependency_edges": "required",
        "feedback_refs": "required",
        "completion_boundary": "required",
    }
    projection_contract = payload["db_projection_contract"]
    assert projection_contract["current_scope_action"] == (
        "define_projection_contract_only"
    )
    assert projection_contract["db_write_done"] is False
    assert projection_contract["schema_migration_done"] is False
    assert projection_contract["query_cli_done"] is False
    assert projection_contract["projection_is_completion_evidence"] is False
    projections = {
        item["projection_id"]: item for item in projection_contract["projections"]
    }
    assert payload["summary"]["db_projection_contracts_checked"] == len(projections)
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
    output_sections = set(payload["required_output_contract"])
    for projection in projections.values():
        source_sections = projection["source_output_section"]
        if isinstance(source_sections, str):
            source_sections = [source_sections]
        assert set(source_sections) <= output_sections, projection["projection_id"]
        assert projection["key_fields"], projection["projection_id"]
        assert projection["purpose"], projection["projection_id"]
    assert payload["dependency_edge_contract"] == {
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
    assert payload["summary"]["dependency_edge_relations_checked"] == len(
        payload["dependency_edge_contract"]["allowed_relations"]
    )
    scope_route_policy = payload["impact_scope_route_policy"]
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
        item["verdict"]: item for item in payload["impact_scope_route_contracts"]
    }
    assert set(scope_routes) == set(scope_route_policy["allowed_verdicts"])
    assert payload["summary"]["impact_scope_route_contracts_checked"] == len(
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
    unknown_contract = payload["unknown_scope_resolution_contract"]
    assert unknown_contract["current_scope_action"] == "define_unknown_resolution_only"
    assert unknown_contract["unknown_is_current_scope_blocker"] is False
    assert unknown_contract["unknown_is_completion_evidence"] is False
    assert unknown_contract["unknown_can_be_silently_local"] is False
    assert unknown_contract["query_cli_done"] is False
    assert unknown_contract["db_write_done"] is False
    assert unknown_contract["l7_artifact_allowed_now"] is False
    resolution_rules = {
        item["rule"]: item for item in unknown_contract["resolution_rules"]
    }
    assert set(resolution_rules) == {
        "preserve_unknown_verdict",
        "require_manual_owner",
        "expose_missing_edges",
        "deny_auto_execution",
        "separate_review_from_closure",
        "route_implementation_to_feature",
    }
    assert payload["summary"]["unknown_scope_resolution_rules_checked"] == len(
        resolution_rules
    )
    assert resolution_rules["require_manual_owner"]["evidence_source"] == (
        "impact_scope_route_contracts.required_evidence_before_execution"
    )
    assert resolution_rules["route_implementation_to_feature"]["evidence_source"] == (
        "sources.deferred_feature_entry_points"
    )
    visibility_contract = payload["impact_visibility_closure_contract"]
    assert visibility_contract["current_scope_action"] == (
        "prove_output_projection_route_alignment_only"
    )
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
    visibility_rows = {
        item["output_section"]: item for item in visibility_contract["rows"]
    }
    assert payload["summary"]["impact_visibility_rows_checked"] == len(
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
    output_trace = {
        item["required_output_section"]: item
        for item in payload["impact_query_output_contract_trace"]
    }
    assert payload["summary"]["impact_output_trace_rows_checked"] == len(output_trace)
    assert set(output_trace) == set(payload["required_output_contract"])
    assert len(output_trace) == payload["summary"]["required_output_sections"]
    output_paths = [
        item["l6_output_path"] for item in payload["impact_query_output_contract_trace"]
    ]
    assert len(output_paths) == len(set(output_paths))
    assert all(path.startswith("impact_query_result.") for path in output_paths)
    impact_spec = _read(FR_IMPACT_L6_FUNCTION_SPEC)
    output_path_terms = {
        "impact_query_result.seed": ("impact_query_result:", "seed:"),
        "impact_query_result.affected.plans": ("affected:", "plans:"),
        "impact_query_result.affected.design_docs": ("affected:", "design_docs:"),
        "impact_query_result.affected.test_design_docs": (
            "affected:",
            "test_design_docs:",
        ),
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
        assert row["l6_spec_ref"] == str(FR_IMPACT_L6_FUNCTION_SPEC.relative_to(REPO_ROOT))
        assert row["current_scope_status"] == "l6_design_only_not_cli"
        for term in output_path_terms[row["l6_output_path"]]:
            assert term in impact_spec, section
    assert "source -> target -> relation -> confidence" in impact_spec
    deferred_plans = set(payload["sources"]["deferred_feature_entry_points"])
    assert all(plan.startswith("docs/plans/add-feature/") for plan in deferred_plans)
    for surface in surfaces.values():
        surface_text = _read(REPO_ROOT / surface["artifact"])
        assert surface["deferred_feature_plan"] in deferred_plans
        for function_ref in surface["covered_functions"]:
            token = function_ref.split()[0]
            assert token in surface_text, f"{surface['id']} missing {token}"
    assert "Unknown impact scope must not be rendered as local." in payload[
        "invariants"
    ]
    assert "Impact graph or inventory snapshot alone is not closure evidence." in payload[
        "invariants"
    ]
    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for ref in payload["sources"]["current_code_surfaces_read_only"]:
        assert ref.startswith("cli/lib/"), ref
        assert (REPO_ROOT / ref).exists(), ref
    for surface in surfaces.values():
        assert (REPO_ROOT / surface["artifact"]).exists(), surface["artifact"]
        assert (REPO_ROOT / surface["deferred_feature_plan"]).exists(), surface["id"]
        assert surface["design_status"] == "current_scope_l6_design"
        assert surface["current_scope_result"]
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves L1-L6 dependency and impact readiness only"
    )


def test_db_registration_readiness_keeps_add_feature_import_as_l7_ticket() -> None:
    payload = yaml.safe_load(_read(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP))

    assert payload["schema_version"] == "l1_l6_db_registration_readiness_coverage_v1"
    assert payload["status"] == "current_scope_l1_l6_db_registration_readiness_mapped"
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "db_registration_map_is_implementation_evidence": False,
        "plan_registry_changed_by_this_audit": False,
        "helix_db_write_performed": False,
        "schema_migration_done": False,
        "hook_changed_by_this_audit": False,
        "l7_test_design_created_by_this_audit": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
        "registration_events_checked": 6,
        "registration_event_contracts_checked": 6,
        "document_projection_contracts_checked": 5,
        "lifecycle_route_contracts_checked": 6,
        "existing_implementation_surfaces_checked": 8,
        "l1_l6_design_surfaces_checked": 3,
        "readiness_rows": 6,
        "event_route_closure_rows_checked": 6,
        "add_feature_import_targets_checked": 11,
        "blocking_findings_current_scope": 0,
        "l7_feature_tickets_created": 1,
        "l7_artifacts_created_by_this_audit": 0,
    }
    assert payload["summary"]["registration_events_checked"] == len(
        payload["registration_event_readiness"]
    )
    assert payload["summary"]["readiness_rows"] == len(
        payload["registration_event_readiness"]
    )
    assert payload["summary"]["registration_event_contracts_checked"] == len(
        payload["registration_event_contracts"]
    )
    assert payload["summary"]["document_projection_contracts_checked"] == len(
        payload["document_projection_contracts"]
    )
    assert payload["summary"]["lifecycle_route_contracts_checked"] == len(
        payload["registration_lifecycle_route_contracts"]
    )
    assert payload["summary"]["event_route_closure_rows_checked"] == len(
        payload["event_route_closure_contract"]["rows"]
    )
    assert payload["summary"]["existing_implementation_surfaces_checked"] == len(
        payload["sources"]["implementation_surfaces_read_only"]
    )
    assert payload["summary"]["l1_l6_design_surfaces_checked"] == len(
        payload["sources"]["workflow_design"]
    )
    assert payload["summary"]["l7_feature_tickets_created"] == len(
        payload["sources"]["deferred_feature_entry_points"]
    )
    assert payload["registration_accountability_contract"] == {
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
    deferred_feature_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    import_target_contract = payload["add_feature_import_target_contract"]
    assert import_target_contract == {
        "source_audit": str(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)),
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
        for item in deferred_feature_coverage[import_target_contract["source_collection"]]
    }
    assert set(import_target_contract["required_target_ids"]) == source_ticket_ids
    assert payload["summary"]["add_feature_import_targets_checked"] == len(
        source_ticket_ids
    )

    rows = {item["event"]: item for item in payload["registration_event_readiness"]}
    assert set(rows) == {
        "PLAN 起票",
        "コード変更",
        "ドキュメント更新",
        "Codex 実行後",
        "ゲート通過後",
        "セッション停止",
    }
    plan_row = rows["PLAN 起票"]
    assert plan_row["current_readiness"] == "partial"
    assert plan_row["gap"]["id"] == "DBREG-GAP-ADD-FEATURE-BULK-IMPORT-PATTERN"
    assert plan_row["gap"]["current_scope_action"] == "feature_ticket_only"
    assert plan_row["gap"]["deferred_feature_plan"] == str(
        PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert plan_row["gap"]["gap_is_current_completion_blocker"] is False
    assert plan_row["gap"]["ticket_is_completion_evidence"] is False
    assert rows["コード変更"]["current_scope_action"] == "no_write_no_index_rebuild"
    doc_row = rows["ドキュメント更新"]
    assert doc_row["workflow_hook"] == "document_registry_projection"
    assert doc_row["current_readiness"] == (
        "l1_l6_design_contract_present_write_deferred"
    )
    assert doc_row["current_scope_action"] == "no_db_write_no_registry_mutation"
    assert "functional registry" in doc_row["registration_target"]
    assert "test-design viewpoint metadata" in doc_row["registration_target"]
    assert {
        "docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md",
        "docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md",
        "docs/v2/L6-functional-design/FR-INV-01/function-spec.md",
        "cli/lib/contract_registry.py",
    } <= set(doc_row["evidence"])
    assert rows["ゲート通過後"]["current_scope_action"] == (
        "no_feedback_auto_apply_no_gate_promotion"
    )
    contract_policy = payload["registration_event_contract_policy"]
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
        item["event"]: item for item in payload["registration_event_contracts"]
    }
    assert set(event_contracts) == set(rows)
    assert len({item["db_target"] for item in event_contracts.values()}) == len(
        event_contracts
    )
    assert event_contracts["PLAN 起票"]["db_target"] == "plan_registry"
    assert event_contracts["ドキュメント更新"]["db_target"] == "contract_registry"
    assert event_contracts["ゲート通過後"]["db_target"] == "feedback_event"
    for event, contract in event_contracts.items():
        for field in contract_policy["required_contract_fields"]:
            assert field in contract, event
        assert contract["required_fields"], event
        if event == "PLAN 起票":
            assert contract["current_scope_action"] == (
                "feature_ticket_only_no_plan_registry_change"
            )
        else:
            assert contract["current_scope_action"] == rows[event][
                "current_scope_action"
            ]
        assert contract["trouble_detection_route"], event
        assert contract["improvement_feedback_route"], event
    assert "non_closure_reason" in event_contracts["ゲート通過後"][
        "required_fields"
    ]
    assert "implementation_status" in event_contracts["ドキュメント更新"][
        "required_fields"
    ]
    doc_projection_policy = payload["document_projection_policy"]
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
        item["doc_kind"]: item for item in payload["document_projection_contracts"]
    }
    assert set(doc_projection_contracts) == set(
        doc_projection_policy["allowed_doc_kinds"]
    )
    for doc_kind, contract in doc_projection_contracts.items():
        for field in doc_projection_policy["required_contract_fields"]:
            assert field in contract, doc_kind
        assert contract["db_target"] in doc_projection_policy["allowed_db_targets"]
        assert contract["required_keys"], doc_kind
        assert contract["missing_detection_route"], doc_kind
        assert contract["feedback_route"], doc_kind
        assert contract["completion_guard"].startswith("projection_contract_is_not_")
    assert doc_projection_contracts["l6_function_spec"]["db_target"] == (
        "functional_registry"
    )
    assert doc_projection_contracts["unit_test_design_viewpoint"]["db_target"] == (
        "test_design_viewpoint_registry"
    )
    assert doc_projection_contracts["unit_test_design_viewpoint"][
        "completion_guard"
    ] == "projection_contract_is_not_l7_test_design"
    assert doc_projection_contracts["audit_manifest"]["db_target"] == (
        "detector_report"
    )
    assert "completion_denial" in doc_projection_contracts["audit_manifest"][
        "required_keys"
    ]
    assert doc_projection_contracts["audit_manifest"]["completion_guard"] == (
        "projection_contract_is_not_db_write"
    )
    route_policy = payload["lifecycle_route_contract_policy"]
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
        item["event"]: item for item in payload["registration_lifecycle_route_contracts"]
    }
    assert set(lifecycle_routes) == set(rows)
    assert lifecycle_routes["ドキュメント更新"]["trouble_detection_signal"] == (
        "doc_connection_gap"
    )
    assert lifecycle_routes["Codex 実行後"]["routed_mode"] == "Recovery"
    assert lifecycle_routes["ゲート通過後"]["entry_state"] == "verification_recorded"
    assert lifecycle_routes["ゲート通過後"]["persisted_state"] == "gate_projected"
    db_coverage = yaml.safe_load(_read(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP))
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
    closure_contract = payload["event_route_closure_contract"]
    assert closure_contract["current_scope_action"] == (
        "prove_event_to_route_closure_only"
    )
    assert closure_contract["source_collections"] == [
        "registration_event_contracts",
        "registration_lifecycle_route_contracts",
    ]
    assert closure_contract["event_identity_field"] == "event"
    assert closure_contract["events_checked"] == len(rows)
    assert closure_contract["rows_checked"] == len(closure_contract["rows"])
    assert payload["summary"]["event_route_closure_rows_checked"] == (
        closure_contract["events_checked"]
    )
    assert closure_contract["db_write_allowed_now"] is False
    assert closure_contract["detector_route_auto_execute_allowed_now"] is False
    assert closure_contract["feedback_auto_apply_allowed_now"] is False
    assert closure_contract["l7_or_adoption_evidence_allowed"] is False
    closure_rows = {item["event"]: item for item in closure_contract["rows"]}
    assert set(closure_rows) == set(rows)
    for event, row in closure_rows.items():
        event_contract = event_contracts[event]
        lifecycle_route = lifecycle_routes[event]
        assert row["db_target"] == event_contract["db_target"], event
        assert row["trouble_detection_route"] == event_contract[
            "trouble_detection_route"
        ], event
        assert row["improvement_feedback_route"] == event_contract[
            "improvement_feedback_route"
        ], event
        assert row["trouble_detection_signal"] == lifecycle_route[
            "trouble_detection_signal"
        ], event
        assert row["routed_mode"] == lifecycle_route["routed_mode"], event
        assert row["improvement_feedback_state"] == lifecycle_route[
            "improvement_feedback_state"
        ], event
        assert row["completion_guard"] == lifecycle_route["completion_guard"], event
    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for row in rows.values():
        for ref in row["evidence"]:
            assert not ref.startswith("docs/v2/L7-test-design/"), row["event"]
            assert (REPO_ROOT / ref).exists(), ref
    assert all(
        item.startswith("This audit does not")
        or item == "Draft add-feature tickets are not implementation evidence."
        or item == "Add-feature import behavior requires approved L7 TDD implementation."
        for item in payload["invariants"]
    )

    plan_text = _read(PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN)
    plan_meta = yaml.safe_load(plan_text.split("---", 2)[1])
    assert plan_meta["workflow"] == "add-feature"
    assert plan_meta["kind"] == "add-impl"
    assert plan_meta["layer"] == "L7"
    assert plan_meta["status"] == "draft"
    assert "This PLAN is only a ticket" in plan_meta["approval_boundary"]
    assert "Draft only. This is a feature ticket" in plan_text
    assert "not a completed L7 deliverable" in plan_text

    db_coverage = yaml.safe_load(_read(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP))
    assert db_coverage["schema_version"] == (
        "l1_l6_db_feedback_lifecycle_coverage_v1"
    )
    assert db_coverage["status"] == "current_scope_l1_l6_db_feedback_design_covered"
    assert db_coverage["scope"] == "L1-L6"
    assert db_coverage["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "db_design_exists": True,
        "schema_migration_done": False,
        "db_write_connection_done": False,
        "recurrence_closure_done": False,
        "ci_or_equivalent_connected": False,
        "goal_complete_allowed": False,
    }
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
    assert db_coverage["summary"]["design_layers_checked"] == len(layer_coverage)
    assert db_coverage["summary"]["physical_db_design_checked"] == len(
        db_coverage["sources"]["l5_physical_data_design"]
    )
    assert layer_coverage["L5"]["supporting_artifact"] == (
        "docs/v2/L5-detailed-design/物理データ設計.md"
    )
    assert "DB-01..DB-05" in " ".join(layer_coverage["L5"]["coverage"])
    assert "DBEV-FN-08 emit_completion_guard_summary" in layer_coverage["L6"][
        "coverage"
    ]
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
    l6_db_design = _read(REPO_ROOT / layer_coverage["L6"]["artifact"])
    l6_function_ids = sorted(set(re.findall(r"DBEV-FN-[0-9]{2}", l6_db_design)))
    assert l6_function_ids == [f"DBEV-FN-{index:02d}" for index in range(1, 9)]
    assert db_coverage["summary"]["l6_functions_defined"] == len(l6_function_ids)
    assert len(layer_coverage["L6"]["coverage"]) == len(l6_function_ids)
    for function_id in l6_function_ids:
        assert any(function_id in item for item in layer_coverage["L6"]["coverage"])
    for state in db_coverage["state_machine"]["expected_states"]:
        assert state in l6_db_design
    assert db_coverage["storage_mapping_policy"]["mode"] == (
        "existing_db_surfaces_only"
    )
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
    assert db_coverage["summary"]["forbidden_current_scope_rules_checked"] == len(
        db_coverage["storage_mapping_policy"]["forbidden_current_scope"]
    )
    assert db_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
        db_coverage["sources"]["deferred_feature_entry_points"]
    )
    assert set(db_coverage["storage_mapping_policy"]["forbidden_current_scope"]) == {
        "schema_migration",
        "destructive_data_operation",
        "auto_apply_feedback_candidates",
        "production_db_operation",
    }
    l4_db_design = _read(DB_EVIDENCE_LIFECYCLE_L4_DOC)
    l5_db_design = _read(DB_EVIDENCE_LIFECYCLE_L5_DOC)
    l6_db_meta = yaml.safe_load(l6_db_design.split("---", 2)[1])
    l4_db_meta = yaml.safe_load(l4_db_design.split("---", 2)[1])
    l5_db_meta = yaml.safe_load(l5_db_design.split("---", 2)[1])
    assert l4_db_meta["layer"] == "L4"
    assert l4_db_meta["pairs_with"] == "L9"
    assert l4_db_meta["implementation_status"] == "design_gap_closed_current_phase"
    assert l5_db_meta["layer"] == "L5"
    assert l5_db_meta["pairs_with"] == "L8"
    assert l5_db_meta["implementation_status"] == "design_gap_closed_current_phase"
    assert l6_db_meta["layer"] == "L6"
    assert l6_db_meta["pairs_with"] == "L7"
    assert l6_db_meta["next_feature_plan"] == str(
        DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert l6_db_meta["implementation_status"] == "design_gap_closed_current_phase"
    for state in db_coverage["state_machine"]["expected_states"]:
        assert state in l4_db_design, state
        assert state in l5_db_design, state
        assert state in l6_db_design, state
    for group in db_coverage["storage_mapping_policy"]["mapped_groups"]:
        assert group.replace("_", " ") in l4_db_design, group
    for closure_rule in db_coverage["state_machine"]["closure_rules"]:
        if closure_rule == "candidate_generated_is_not_closure":
            assert "`candidate_generated` 止まりで closure 扱いしない" in l6_db_design
        elif closure_rule == "plan_materialized_is_not_closure":
            assert "PLAN materialized のみ" in l6_db_design
        elif closure_rule == "verification_recorded_requires_gate_projection":
            assert "gate projection なし" in l6_db_design
        elif closure_rule == "recurrence_closed_or_monitored_with_owner_required_before_completion":
            assert "closed` / `monitored_with_owner` 以外" in l6_db_design
        else:
            raise AssertionError(closure_rule)
    forbidden_texts = {
        "schema_migration": "schema_migration",
        "destructive_data_operation": "destructive_data_operation",
        "auto_apply_feedback_candidates": "auto_apply",
        "production_db_operation": "production_db_operation",
    }
    for forbidden, text in forbidden_texts.items():
        assert forbidden in db_coverage["storage_mapping_policy"]["forbidden_current_scope"]
        assert text in l4_db_design, forbidden
        assert text in l5_db_design or text == "destructive_data_operation", forbidden
        assert text in l6_db_design, forbidden
    assert db_coverage["deferred_feature_plan"]["path"] == str(
        DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert db_coverage["deferred_feature_plan"]["approval_required_before_l7_work"] is True
    feature_text = _read(DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN)
    feature_meta = yaml.safe_load(feature_text.split("---", 2)[1])
    assert feature_meta["workflow"] == "add-feature"
    assert feature_meta["layer"] == "L7"
    assert feature_meta["status"] == "draft"
    assert feature_meta["current_task_scope"] == "feature_ticket_only"
    assert feature_meta["approval_required_before_l7_work"] is True
    assert "現在タスクでは `docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md` を作成しない" in feature_text
    for refs in db_coverage["sources"].values():
        for ref in refs:
            assert (REPO_ROOT / ref).exists(), ref
    for item in layer_coverage.values():
        assert (REPO_ROOT / item["artifact"]).exists(), item["artifact"]
    assert db_coverage["completion_denial"]["reason"].startswith(
        "This audit proves L1-L6 DB feedback lifecycle design coverage"
    )

    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    assert harness_coverage["schema_version"] == (
        "l1_l6_harness_external_tools_coverage_v1"
    )
    assert harness_coverage["status"] == (
        "current_scope_l1_l6_external_tool_design_covered"
    )
    assert harness_coverage["scope"] == "L1-L6"
    assert harness_coverage["boundary"] == {
        "web_sources_verified": True,
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "external_tool_installed": False,
        "mcp_server_enabled": False,
        "plugin_installed": False,
        "semgrep_or_codeql_executed": False,
        "scorecard_executed": False,
        "credential_or_secret_change": False,
        "external_network_execution": False,
        "ci_or_equivalent_connected": False,
        "helix_db_write_connected": False,
        "goal_complete_allowed": False,
    }
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
    adoption_recheck_controls = harness_coverage[
        "adoption_recheck_control_contract"
    ]
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
    assert adoption_recheck_controls[
        "all_controls_require_new_recheck_before_adoption"
    ] is True
    assert adoption_recheck_controls["adoption_or_execution_allowed_now"] is False
    assert adoption_recheck_controls["db_write_allowed_now"] is False
    assert adoption_recheck_controls["l7_artifact_allowed_now"] is False
    adoption_recheck_sources = {
        item["source_id"]: item for item in adoption_recheck_controls["sources"]
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
        "current_scope_action": (
            "clarify_recheck_scope_vs_candidate_gate_coverage_only"
        ),
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
        "current_scope_action": (
            "prove_external_tool_research_is_not_adoption_or_install"
        ),
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
            (
                "adoption recheck controls are defined for representative "
                "MCP/App sources"
            ),
            (
                "pre-adoption requirements bridge maps rechecked risks to "
                "L1/L3 requirements and acceptance obligations"
            ),
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
    assert web_recheck_design_links["source_map"] == str(
        L1_L6_WEB_EVIDENCE_SOURCE_MAP.relative_to(REPO_ROOT)
    )
    assert web_recheck_design_links["current_scope_action"] == "design_evidence_only"
    assert web_recheck_design_links["adoption_or_install_evidence"] is False
    admission_gate_ids = {
        item["gate_id"] for item in harness_coverage["admission_gate_contracts"]
    }
    assert set(web_recheck_design_links["admission_gate_impact"]) == set(
        harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
    )
    for source_id, impact in web_recheck_design_links[
        "admission_gate_impact"
    ].items():
        assert source_id in harness_coverage["web_evidence_freshness_contract"][
            "canonical_source_ids"
        ]
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
    assert harness_coverage["summary"]["tool_intake_required_fields_checked"] == len(
        harness_coverage["tool_intake_contract"]["required_candidate_fields"]
    )
    assert harness_coverage["summary"][
        "tool_intake_forbidden_common_rules_checked"
    ] == len(harness_coverage["tool_intake_contract"]["forbidden_current_scope_common"])
    assert harness_coverage["summary"]["admission_gate_required_fields_checked"] == len(
        harness_coverage["admission_gate_policy"]["required_gate_fields"]
    )
    assert harness_coverage["summary"]["admission_owner_roles_checked"] == len(
        harness_coverage["admission_gate_policy"]["allowed_owner_roles"]
    )
    assert harness_coverage["summary"]["tool_output_required_fields_checked"] == len(
        harness_coverage["tool_output_ingestion_policy"]["required_contract_fields"]
    )
    assert harness_coverage["summary"]["tool_output_detector_signals_checked"] == len(
        harness_coverage["tool_output_ingestion_policy"]["allowed_detector_signals"]
    )
    assert harness_coverage["summary"]["current_session_web_fetch_refs_checked"] == sum(
        len(item["web_refs"])
        for item in harness_coverage["current_session_web_fetch_recheck_2026_06_13"][
            "sources"
        ]
    )
    assert harness_coverage["summary"]["accountability_current_scope_proves_checked"] == len(
        harness_coverage["harness_tool_accountability_contract"]["current_scope_proves"]
    )
    assert harness_coverage["summary"][
        "accountability_current_scope_does_not_prove_checked"
    ] == len(
        harness_coverage["harness_tool_accountability_contract"][
            "current_scope_does_not_prove"
        ]
    )
    harness_spot_recheck = harness_coverage["spot_recheck_2026_06_13"]
    assert harness_spot_recheck == {
        "source_map": str(L1_L6_WEB_EVIDENCE_SOURCE_MAP.relative_to(REPO_ROOT)),
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
    current_session_recheck = harness_coverage[
        "current_session_web_fetch_recheck_2026_06_13"
    ]
    assert current_session_recheck["current_scope_action"] == (
        "confirm_existing_l1_l6_design_basis_only"
    )
    assert current_session_recheck["official_sources_checked"] == 5
    assert current_session_recheck["official_sources_checked"] == len(
        current_session_recheck["sources"]
    )
    current_session_source_ids = [
        item["source_id"] for item in current_session_recheck["sources"]
    ]
    assert current_session_source_ids == harness_coverage[
        "web_evidence_freshness_contract"
    ]["latest_core_rechecked_source_ids"]
    for item in current_session_recheck["sources"]:
        assert item["official_url"].startswith("https://"), item["source_id"]
        assert item["web_refs"], item["source_id"]
    assert current_session_recheck["web_fetch_confirmed"] is True
    assert current_session_recheck["adoption_or_execution_allowed_now"] is False
    assert current_session_recheck["db_write_allowed_now"] is False
    assert current_session_recheck["ci_or_equivalent_connection_allowed_now"] is False
    assert current_session_recheck["l7_artifact_allowed_now"] is False
    assert current_session_recheck["result"] == "no_change_to_candidate_gate_status"
    web_map = yaml.safe_load(_read(L1_L6_WEB_EVIDENCE_SOURCE_MAP))
    web_current_session_recheck = web_map[
        "current_session_web_fetch_recheck_2026_06_13"
    ]
    assert web_current_session_recheck["current_scope_action"] == (
        current_session_recheck["current_scope_action"]
    )
    assert web_current_session_recheck["checked_on"] == current_session_recheck[
        "checked_on"
    ]
    assert web_current_session_recheck["official_sources_checked"] == (
        current_session_recheck["official_sources_checked"]
    )
    assert web_current_session_recheck["web_fetch_confirmed"] is True
    assert web_current_session_recheck["adoption_or_execution_allowed_now"] is False
    assert web_current_session_recheck["db_write_allowed_now"] is False
    assert web_current_session_recheck["ci_or_equivalent_connection_allowed_now"] is False
    assert web_current_session_recheck["l7_artifact_allowed_now"] is False
    assert web_current_session_recheck["result"] == current_session_recheck["result"]
    current_session_source_ids = {
        item["source_id"] for item in current_session_recheck["sources"]
    }
    assert current_session_source_ids == set(
        web_current_session_recheck["source_ids"]
    )
    assert "base_protocol_json_rpc" in web_current_session_recheck[
        "confirmed_controls"
    ]["mcp_protocol"]
    assert "oauth_or_pat_configuration_boundary" in web_current_session_recheck[
        "confirmed_controls"
    ]["github_mcp_server"]
    assert "output_schema_for_structured_content" in web_current_session_recheck[
        "confirmed_controls"
    ]["openai_apps_sdk_descriptor"]
    assert "preferred_semgrep_scan_command" in web_current_session_recheck[
        "confirmed_controls"
    ]["semgrep_ce"]
    assert "code_scanning_alert_output" in web_current_session_recheck[
        "confirmed_controls"
    ]["github_codeql"]
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
    official_sources = {
        item["source_id"]: item for item in harness_coverage["official_web_sources"]
    }
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
    assert "JSON-RPC 2.0 base protocol" in official_sources[
        "MCP-SPEC-2025-06-18"
    ]["confirmed_focus"]
    assert "OAuth default path" in official_sources["GITHUB-MCP-SERVER"][
        "confirmed_focus"
    ]
    assert "SARIF output" in official_sources["SEMGREP-CE"]["confirmed_focus"]
    assert "code scanning alerts" in official_sources["GITHUB-CODEQL"][
        "confirmed_focus"
    ]
    assert "static analysis for GitHub Actions" in official_sources[
        "ZIZMOR-GHA-SECURITY"
    ]["confirmed_focus"]
    assert "GitHub Actions integration and SARIF upload route" in official_sources[
        "ZIZMOR-GHA-SECURITY"
    ]["confirmed_focus"]
    assert "static checker for GitHub Actions workflow files" in official_sources[
        "ACTIONLINT-GHA-WORKFLOW-LINT"
    ]["confirmed_focus"]
    assert "aggregate and per-check scores" in official_sources[
        "OPENSSF-SCORECARD"
    ]["confirmed_focus"]
    assert "dependency graph and package insight" in official_sources[
        "DEPSDEV-API"
    ]["confirmed_focus"]
    assert "dependency vulnerability scanning" in official_sources[
        "OSV-SCANNER"
    ]["confirmed_focus"]
    assert "Software Bill of Materials generation" in official_sources[
        "SYFT-SBOM"
    ]["confirmed_focus"]
    assert "queryable Python import graph" in official_sources[
        "GRIMP-PYTHON-IMPORT-GRAPH"
    ]["confirmed_focus"]
    assert "JavaScript / TypeScript dependency validation and visualization" in official_sources[
        "DEPENDENCY-CRUISER"
    ]["confirmed_focus"]
    assert "shell script static analysis" in official_sources[
        "SHELLCHECK-SHELL-STATIC"
    ]["confirmed_focus"]
    assert "Markdown and CommonMark linting" in official_sources[
        "MARKDOWNLINT-CLI2"
    ]["confirmed_focus"]
    assert "fast async stream-based link checker written in Rust" in official_sources[
        "LYCHEE-LINK-CHECKER"
    ]["confirmed_focus"]
    assert "helix_db_doc_connection_gap_mapping" in official_sources[
        "LYCHEE-LINK-CHECKER"
    ]["design_controls"]
    assert "code-like linting for prose" in official_sources[
        "VALE-PROSE-LINT"
    ]["confirmed_focus"]
    assert "Python mutation testing" in official_sources[
        "MUTMUT-PY-MUTATION-TESTING"
    ]["confirmed_focus"]
    assert "Python property-based testing library" in official_sources[
        "HYPOTHESIS-PY-PBT"
    ]["confirmed_focus"]
    assert "Python code coverage measurement" in official_sources[
        "COVERAGE-PY-COVERAGE"
    ]["confirmed_focus"]
    assert "diff coverage reports for new or modified lines covered by tests" in official_sources[
        "DIFF-COVER-DIFF-COVERAGE"
    ]["confirmed_focus"]
    assert "compares XML or LCov coverage reports with git diff output" in official_sources[
        "DIFF-COVER-DIFF-COVERAGE"
    ]["confirmed_focus"]
    assert "helix_db_diff_coverage_mapping" in official_sources[
        "DIFF-COVER-DIFF-COVERAGE"
    ]["design_controls"]
    assert "Python test runner" in official_sources[
        "PYTEST-PY-TEST-RUNNER"
    ]["confirmed_focus"]
    assert "readable tests and complex functional testing" in official_sources[
        "PYTEST-PY-TEST-RUNNER"
    ]["confirmed_focus"]
    assert "pytest plugin that selects tests affected by changed files and methods" in official_sources[
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION"
    ]["confirmed_focus"]
    assert "dependency collection between tests and executed code using Coverage.py" in official_sources[
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION"
    ]["confirmed_focus"]
    assert "hidden test dependency detection and CI usage surface" in official_sources[
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION"
    ]["confirmed_focus"]
    assert "helix_db_test_impact_mapping" in official_sources[
        "PYTEST-TESTMON-IMPACTED-TEST-SELECTION"
    ]["design_controls"]
    assert "Python virtual environment management and test command line tool" in official_sources[
        "TOX-PY-ENV-ORCHESTRATION"
    ]["confirmed_focus"]
    assert "environment lists, generated matrices, provisioning, workdir/tempdir, and missing-interpreter policy" in official_sources[
        "TOX-PY-ENV-ORCHESTRATION"
    ]["confirmed_focus"]
    assert "Python command-line automation for testing in multiple environments" in official_sources[
        "NOX-PY-SESSION-AUTOMATION"
    ]["confirmed_focus"]
    assert "@nox.session functions with dependency installation and ordered command execution" in official_sources[
        "NOX-PY-SESSION-AUTOMATION"
    ]["confirmed_focus"]
    assert "Python import architecture constraints" in official_sources[
        "IMPORT-LINTER-PY-ARCH-CONTRACTS"
    ]["confirmed_focus"]
    assert "lint-imports contract checking" in official_sources[
        "IMPORT-LINTER-PY-ARCH-CONTRACTS"
    ]["confirmed_focus"]
    assert "JSON Schema CLI and pre-commit hook" in official_sources[
        "CHECK-JSONSCHEMA-DOC-SCHEMA"
    ]["confirmed_focus"]
    assert "JSON diagnostic output" in official_sources[
        "CHECK-JSONSCHEMA-DOC-SCHEMA"
    ]["confirmed_focus"]
    assert "ready-to-use OpenAPI v2 and v3.x rulesets" in official_sources[
        "SPECTRAL-API-CONTRACT-LINT"
    ]["confirmed_focus"]
    assert "command-line linting with custom ruleset selection" in official_sources[
        "SPECTRAL-API-CONTRACT-LINT"
    ]["confirmed_focus"]
    assert "SQL linter designed to catch errors and bad SQL before database execution" in official_sources[
        "SQLFLUFF-SQL-LINT"
    ]["confirmed_focus"]
    assert "dialect reference including SQLite" in official_sources[
        "SQLFLUFF-SQL-LINT"
    ]["confirmed_focus"]
    assert "Python linter and code formatter" in official_sources[
        "RUFF-PY-LINT-FORMAT"
    ]["confirmed_focus"]
    assert "Python static type checker" in official_sources[
        "MYPY-PY-TYPE-CHECK"
    ]["confirmed_focus"]
    assert "Python environment vulnerability auditing" in official_sources[
        "PIP-AUDIT-PY-VULN"
    ]["confirmed_focus"]
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
            "textlint.org",
            "docs.astral.sh",
            "mypy.readthedocs.io",
            "docs.sqlfluff.com",
        }, source["source_id"]
        assert source["web_fetch_confirmed"] is True
        assert source["adoption_decision"] == "not_adopted_current_scope"
        assert source["current_scope_action"] == "design_evidence_only"
        assert source["design_controls"], source["source_id"]
        assert harness_coverage["official_source_policy"][
            "recheck_required_before_install_or_execution"
        ] is True
    assert harness_coverage["summary"]["official_sources_checked"] == len(
        official_sources
    )
    intake_contract = harness_coverage["tool_intake_contract"]
    assert intake_contract["current_scope_action"] == (
        "feature_ticket_only_preflight_contract"
    )
    assert (REPO_ROOT / intake_contract["deferred_feature_plan"]).exists()
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
    intake_candidates = {
        item["candidate_id"]: item for item in intake_contract["candidates"]
    }
    assert harness_coverage["summary"]["tool_intake_contracts_checked"] == len(
        intake_candidates
    )
    for intake in intake_candidates.values():
        source = official_sources[intake["source_id"]]
        assert intake["official_url"] == source["official_url"]
        assert not intake["deferred_feature_plan"].startswith(
            "docs/v2/L7-test-design/"
        )
        assert (REPO_ROOT / intake["deferred_feature_plan"]).exists()
        assert set(intake["forbidden_current_scope"]) == set(
            intake_contract["forbidden_current_scope_common"]
        )
        assert set(intake["required_source_focus"]).issubset(
            set(source["confirmed_focus"])
        ), intake["candidate_id"]
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
    assert output_contracts["HEXT-CAND-SEMGREP-CE"]["output_surface"] == (
        "semgrep_json_or_sarif"
    )
    assert output_contracts["HEXT-CAND-CODEQL"]["output_surface"] == (
        "codeql_database_sarif_or_alert"
    )
    assert output_contracts["HEXT-CAND-ZIZMOR-GHA"]["output_surface"] == (
        "zizmor_plain_json_sarif_github_annotations_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-OPENSSF-SCORECARD"]["output_surface"] == (
        "scorecard_score_check_detail_or_api_result"
    )
    assert output_contracts["HEXT-CAND-DEPSDEV-API"]["output_surface"] == (
        "depsdev_package_version_dependency_advisory_json"
    )
    assert output_contracts["HEXT-CAND-OSV-SCANNER"]["output_surface"] == (
        "osv_scanner_json_sarif_spdx_or_cyclonedx"
    )
    assert output_contracts["HEXT-CAND-SYFT-SBOM"]["output_surface"] == (
        "syft_json_cyclonedx_spdx_or_github_dependency_snapshot"
    )
    assert output_contracts["HEXT-CAND-GRIMP-PY-IMPORT"]["output_surface"] == (
        "grimp_import_graph_query_result"
    )
    assert output_contracts["HEXT-CAND-DEPENDENCY-CRUISER"]["output_surface"] == (
        "dependency_cruiser_json_dot_csv_html_mermaid_or_text"
    )
    assert output_contracts["HEXT-CAND-SHELLCHECK"]["output_surface"] == (
        "shellcheck_json_checkstyle_gcc_or_text"
    )
    assert output_contracts["HEXT-CAND-MARKDOWNLINT-CLI2"]["output_surface"] == (
        "markdownlint_cli2_issue_json_junit_sarif_codequality_or_summary"
    )
    assert output_contracts["HEXT-CAND-VALE-PROSE-LINT"]["output_surface"] == (
        "vale_json_template_metrics_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-TEXTLINT"]["output_surface"] == (
        "textlint_json_junit_github_unix_or_fix_dry_run_diff"
    )
    assert output_contracts["HEXT-CAND-MUTMUT-PY-MUTATION"]["output_surface"] == (
        "mutmut_mutation_result_surviving_mutant_dependency_warning_or_browse_state"
    )
    assert output_contracts["HEXT-CAND-HYPOTHESIS"]["output_surface"] == (
        "hypothesis_falsifying_example_settings_profile_or_pytest_failure"
    )
    assert output_contracts["HEXT-CAND-COVERAGE-PY"]["output_surface"] == (
        "coverage_py_text_json_xml_lcov_html_or_sqlite_data"
    )
    assert output_contracts["HEXT-CAND-DIFF-COVER"]["output_surface"] == (
        "diff_cover_console_html_json_markdown_or_diff_quality_report"
    )
    assert output_contracts["HEXT-CAND-DIFF-COVER"]["current_scope_action"] == (
        "contract_only_no_execution_no_db_write"
    )
    assert output_contracts["HEXT-CAND-LYCHEE"]["output_surface"] == (
        "lychee_console_json_github_action_or_precommit_report"
    )
    assert output_contracts["HEXT-CAND-LYCHEE"]["current_scope_action"] == (
        "contract_only_no_execution_no_db_write"
    )
    assert output_contracts["HEXT-CAND-PYTEST"]["output_surface"] == (
        "pytest_terminal_summary_junitxml_exit_code_or_failure_report"
    )
    assert output_contracts["HEXT-CAND-PYTEST-TESTMON"]["output_surface"] == (
        "pytest_testmon_selection_summary_testmondata_dependency_db_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-PYTEST-TESTMON"]["current_scope_action"] == (
        "contract_only_no_execution_no_db_write"
    )
    assert output_contracts["HEXT-CAND-TOX"]["output_surface"] == (
        "tox_environment_result_config_report_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-NOX"]["output_surface"] == (
        "nox_session_list_usage_result_stdout_stderr_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-IMPORT-LINTER"]["output_surface"] == (
        "lint_imports_contract_result_broken_contract_diagnostics_or_dot_graph"
    )
    assert output_contracts["HEXT-CAND-CHECK-JSONSCHEMA"]["output_surface"] == (
        "check_jsonschema_text_json_diagnostics_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-SPECTRAL"]["output_surface"] == (
        "spectral_lint_diagnostics_ruleset_violation_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-SQLFLUFF"]["output_surface"] == (
        "sqlfluff_lint_diagnostics_json_github_annotation_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-RUFF-PY-LINT-FORMAT"]["output_surface"] == (
        "ruff_diagnostic_json_sarif_junit_github_gitlab_or_text"
    )
    assert output_contracts["HEXT-CAND-MYPY"]["output_surface"] == (
        "mypy_type_check_diagnostics_error_codes_reports_or_exit_code"
    )
    assert output_contracts["HEXT-CAND-PIP-AUDIT"]["output_surface"] == (
        "pip_audit_json_markdown_cyclonedx_or_columns"
    )
    for candidate_id, contract in output_contracts.items():
        for field in output_policy["required_contract_fields"]:
            assert field in contract, candidate_id
        assert contract["candidate_id"] in intake_candidates
        assert contract["db_target"] in {"external_tool_candidate", "detector_report"}
        assert contract["detector_signal"] in output_policy[
            "allowed_detector_signals"
        ]
        assert contract["required_before_ingestion"] == intake_candidates[
            candidate_id
        ]["required_before_execution"]
        assert contract["current_scope_action"] == (
            "contract_only_no_execution_no_db_write"
        )
    web_evidence_map = yaml.safe_load(_read(L1_L6_WEB_EVIDENCE_SOURCE_MAP))
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
    assert web_evidence_map[
        "adoption_recheck_control_contract"
    ] == harness_coverage["adoption_recheck_control_contract"]
    assert web_evidence_map[
        "adoption_recheck_scope_contract"
    ] == harness_coverage["adoption_recheck_scope_contract"]
    web_sources = {
        item["source_id"]: item for item in web_evidence_map["sources"]
    }
    assert set(web_sources) == set(official_sources)
    assert set(web_sources) == set(
        web_evidence_map["web_evidence_freshness_contract"]["canonical_source_ids"]
    )
    assert set(official_sources) == set(
        harness_coverage["web_evidence_freshness_contract"]["canonical_source_ids"]
    )
    latest_core_ids = set(
        harness_coverage["web_evidence_freshness_contract"][
            "latest_core_rechecked_source_ids"
        ]
    )
    assert latest_core_ids == set(
        web_evidence_map["web_evidence_freshness_contract"][
            "latest_core_rechecked_source_ids"
        ]
    )
    for source_id, source in official_sources.items():
        web_source = web_sources[source_id]
        freshness_date = harness_coverage["web_evidence_freshness_contract"][
            "rechecked_on"
        ]
        web_source_date = web_source["verified_on"]
        if source["rechecked_on"] != freshness_date:
            web_source_date = web_source.get("rechecked_on", web_source["verified_on"])
        assert source["rechecked_on"] == web_source_date
        if source["rechecked_on"] == harness_coverage[
            "web_evidence_freshness_contract"
        ]["rechecked_on"]:
            assert web_source["verified_on"] == web_evidence_map[
                "web_evidence_freshness_contract"
            ]["rechecked_on"]
        if source_id in latest_core_ids:
            assert source["rechecked_on"] == harness_coverage[
                "web_evidence_freshness_contract"
            ]["latest_core_rechecked_on"]
            assert web_source.get("rechecked_on", web_source["verified_on"]) == web_evidence_map[
                "web_evidence_freshness_contract"
            ]["latest_core_rechecked_on"]
        assert web_source["source_type"] == "official"
        assert web_source["official_url"] == source["official_url"]
        assert web_source["web_fetch_confirmed"] is source["web_fetch_confirmed"]
        assert web_source["adoption_decision"] == source["adoption_decision"]
        assert web_source["source_type"] == web_evidence_map["official_source_policy"][
            "source_type_required"
        ]
        assert urlparse(web_source["official_url"]).scheme == "https"
        assert web_source["current_scope_action"] == "L4-L6 design evidence only"
        assert web_evidence_map["official_source_policy"][
            "current_scope_action_required"
        ] == "design_evidence_only"
        assert set(web_source["confirmed"]["design_controls"]) == set(
            source["design_controls"]
        )
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
    assert contract_ref_sources["JSON-SCHEMA-VALIDATION-2020-12"][
        "applies_to"
    ] == ["D-CONTRACT"]
    assert contract_ref_sources["POSTGRESQL-ALTER-TABLE-CURRENT"][
        "applies_to"
    ] == ["D-DB"]
    assert contract_ref_sources["OPENAPI-SPEC-3-2-0"]["confirmed"] == {
        "version": "3.2.0",
        "publication_date": datetime.date(2025, 9, 19),
        "design_boundary": "API description and contract-shape preservation",
    }
    assert contract_ref_sources["JSON-SCHEMA-VALIDATION-2020-12"]["confirmed"][
        "dialect"
    ] == "draft_2020_12"
    assert contract_ref_sources["POSTGRESQL-ALTER-TABLE-CURRENT"]["confirmed"][
        "documentation"
    ] == "current"
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
    assert [item["source_id"] for item in web_spot_recheck["sources"]] == harness_spot_recheck[
        "sources"
    ]
    for item in web_spot_recheck["sources"]:
        source_id = item["source_id"]
        assert source_id in web_sources
        assert item["official_url"] == web_sources[source_id]["official_url"]
        assert item["reconfirmed"], source_id
        assert item["l1_l6_design_effect"], source_id
    candidates = {
        item["candidate_id"]: item for item in harness_coverage["tool_candidate_coverage"]
    }
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
    assert candidates["HEXT-CAND-GITHUB-MCP"]["admission_status"] == (
        "candidate_requires_confirmation"
    )
    assert candidates["HEXT-CAND-MCP-PROTOCOL"]["kind"] == "mcp_protocol_admission"
    assert candidates["HEXT-CAND-GITHUB-MCP"]["kind"] == "mcp_server"
    assert candidates["HEXT-CAND-ZIZMOR-GHA"][
        "kind"
    ] == "github_actions_workflow_security"
    assert candidates["HEXT-CAND-ACTIONLINT-GHA"][
        "kind"
    ] == "github_actions_workflow_lint"
    assert candidates["HEXT-CAND-GRIMP-PY-IMPORT"]["kind"] == (
        "source_dependency_graph"
    )
    assert candidates["HEXT-CAND-DEPENDENCY-CRUISER"]["kind"] == (
        "source_dependency_graph"
    )
    assert candidates["HEXT-CAND-SHELLCHECK"]["kind"] == "shell_static_analysis"
    assert candidates["HEXT-CAND-MARKDOWNLINT-CLI2"][
        "kind"
    ] == "markdown_static_analysis"
    assert candidates["HEXT-CAND-VALE-PROSE-LINT"][
        "kind"
    ] == "prose_style_analysis"
    assert candidates["HEXT-CAND-TEXTLINT"]["kind"] == "natural_language_lint"
    assert candidates["HEXT-CAND-MUTMUT-PY-MUTATION"][
        "kind"
    ] == "python_mutation_testing"
    assert candidates["HEXT-CAND-HYPOTHESIS"][
        "kind"
    ] == "python_property_based_testing"
    assert candidates["HEXT-CAND-COVERAGE-PY"][
        "kind"
    ] == "python_coverage_measurement"
    assert candidates["HEXT-CAND-DIFF-COVER"]["kind"] == (
        "python_diff_coverage_quality"
    )
    assert "HELIX_DB_diff_coverage_finding_mapping" in candidates[
        "HEXT-CAND-DIFF-COVER"
    ]["required_before_execution"]
    assert candidates["HEXT-CAND-LYCHEE"]["kind"] == "link_reference_check"
    assert "HELIX_DB_doc_connection_gap_mapping" in candidates[
        "HEXT-CAND-LYCHEE"
    ]["required_before_execution"]
    assert candidates["HEXT-CAND-PYTEST"]["kind"] == "python_test_runner"
    assert candidates["HEXT-CAND-PYTEST-TESTMON"][
        "kind"
    ] == "python_impacted_test_selection"
    assert "helix_db_test_impact_mapping" in candidates["HEXT-CAND-PYTEST-TESTMON"][
        "required_before_execution"
    ]
    assert candidates["HEXT-CAND-TOX"]["kind"] == "python_environment_orchestration"
    assert candidates["HEXT-CAND-NOX"]["kind"] == "python_session_automation"
    assert candidates["HEXT-CAND-IMPORT-LINTER"][
        "kind"
    ] == "python_architecture_contracts"
    assert candidates["HEXT-CAND-CHECK-JSONSCHEMA"][
        "kind"
    ] == "document_schema_validation"
    assert candidates["HEXT-CAND-SPECTRAL"]["kind"] == "api_contract_lint"
    assert candidates["HEXT-CAND-SQLFLUFF"]["kind"] == "sql_schema_lint"
    assert candidates["HEXT-CAND-RUFF-PY-LINT-FORMAT"][
        "kind"
    ] == "python_lint_format"
    assert candidates["HEXT-CAND-MYPY"]["kind"] == "python_type_checking"
    assert candidates["HEXT-CAND-PIP-AUDIT"]["kind"] == "python_dependency_audit"
    assert candidates["HEXT-CAND-OPENAI-APPS-MCP-DESCRIPTOR"]["kind"] == (
        "app_tool_descriptor"
    )
    assert set(candidates) == set(intake_candidates)
    assert harness_coverage["summary"]["tool_candidates_checked"] == len(candidates)
    assert {candidate["source_id"] for candidate in candidates.values()} == set(
        official_sources
    )
    for candidate in candidates.values():
        assert candidate["admission_status"].startswith("candidate")
        assert candidate["required_before_execution"], candidate["candidate_id"]
        assert candidate["current_scope_action"] == "feature_ticket_only"
        intake = intake_candidates[candidate["candidate_id"]]
        assert intake["source_id"] == candidate["source_id"]
        assert intake["kind"] == candidate["kind"]
        assert set(intake["required_before_execution"]) == set(
            candidate["required_before_execution"]
        )
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
        item["gate_id"]: item for item in harness_coverage["admission_gate_contracts"]
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
    assert admission_gates["HEXT-ADMIT-DB-INGESTION"]["completion_guard"] == (
        "admission_gate_pass_is_not_db_write"
    )
    harness_layers = {
        item["layer"]: item for item in harness_coverage["layer_coverage"]
    }
    assert set(harness_layers) == {"L4", "L5", "L6"}
    assert harness_coverage["summary"]["design_layers_checked"] == len(harness_layers)
    assert "HEXT-FN-10 evaluate_tool_execution_risk" in harness_layers["L6"][
        "coverage"
    ]
    l6_harness_design = _read(REPO_ROOT / harness_layers["L6"]["artifact"])
    hfunc_ids = sorted(set(re.findall(r"HEXT-FN-[0-9]{2}", l6_harness_design)))
    assert hfunc_ids == [f"HEXT-FN-{index:02d}" for index in range(1, 11)]
    assert harness_coverage["summary"]["l6_functions_defined"] == len(hfunc_ids)
    assert harness_coverage["l6_unit_test_viewpoints"] == {
        "count": 10,
        "prefix": "HEXT-UT-CAND",
        "current_scope_status": "l6_viewpoint_only_not_l7_artifact",
    }
    assert harness_coverage["summary"]["l6_unit_test_viewpoints_defined"] == (
        harness_coverage["l6_unit_test_viewpoints"]["count"]
    )
    assert harness_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
        harness_coverage["sources"]["deferred_feature_entry_points"]
    )
    assert harness_coverage["deferred_feature_plan"]["path"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert harness_coverage["deferred_feature_plan"][
        "external_tool_installation_allowed_now"
    ] is False
    for refs in harness_coverage["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for item in harness_layers.values():
        assert (REPO_ROOT / item["artifact"]).exists(), item["artifact"]
    assert harness_coverage["completion_denial"]["reason"].startswith(
        "This audit proves L1-L6 HARNESS external-tool research"
    )

    governance_coverage = yaml.safe_load(
        _read(L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP)
    )
    assert governance_coverage["schema_version"] == (
        "l1_l6_governance_hardening_coverage_v1"
    )
    assert governance_coverage["status"] == (
        "current_scope_l1_l6_governance_design_covered"
    )
    assert governance_coverage["scope"] == "L1-L6"
    assert governance_coverage["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "governance_map_is_implementation_evidence": False,
        "new_l7_test_design_created": False,
        "new_l7_implementation_done": False,
        "fail_close_promotion_done": False,
        "ci_or_equivalent_connected": False,
        "schema_migration_done": False,
        "external_tool_executed": False,
        "goal_complete_allowed": False,
    }
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
    governance_surfaces = {
        item["id"]: item for item in governance_coverage["governance_surfaces"]
    }
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
    assert governance_coverage["summary"]["governance_surfaces_checked"] == len(
        governance_surfaces
    )
    assert governance_coverage["summary"]["l6_design_docs_checked"] == len(
        governance_coverage["sources"]["l6_governance_designs"]
    )
    assert governance_coverage["summary"]["deferred_feature_entry_points_checked"] == len(
        governance_coverage["sources"]["deferred_feature_entry_points"]
    )
    assert governance_coverage["summary"][
        "preexisting_completed_feature_entry_points_checked"
    ] == len(governance_coverage["sources"]["preexisting_completed_feature_entry_points"])
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
        plan_path = REPO_ROOT / ref
        assert plan_path.exists(), ref
        plan_meta = yaml.safe_load(_read(plan_path).split("---", 2)[1])
        assert plan_meta["workflow"] == "add-feature"
        assert plan_meta["status"] == "completed"
    for refs in governance_coverage["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
    assert len(governance_surfaces["GOV-CODING-RULE"]["function_ids"]) == 4
    assert len(governance_surfaces["GOV-DDD-REGISTRY"]["function_ids"]) == 5
    assert governance_surfaces["GOV-TDD-ORDER"]["l6_ut_candidate_count"] == 7
    assert governance_surfaces["GOV-FUNCTION-REGISTRY"][
        "l6_ut_candidate_count"
    ] == 8
    assert governance_surfaces["GOV-GLOSSARY"]["l6_ut_candidate_count"] == 8
    assert governance_surfaces["GOV-INVENTORY"]["l6_ut_candidate_count"] == 7
    assert governance_surfaces["GOV-IMPACT"]["l6_ut_candidate_count"] == 7
    assert governance_surfaces["GOV-DOC-REVIEW"]["l6_ut_candidate_count"] == 7
    assert governance_coverage["coverage_controls"]["coding_rule_registry"][
        "expected_registry_entries"
    ] == 14
    assert governance_coverage["coverage_controls"]["ddd_registry"][
        "expected_glossary_terms_min"
    ] == 19
    assert governance_coverage["coverage_controls"]["ddd_registry"][
        "expected_bounded_contexts"
    ] == 10
    assert governance_coverage["coverage_controls"]["tdd_order"][
        "forbidden_transitions_defined"
    ] is True
    assert governance_coverage["coverage_controls"]["tdd_order"][
        "failing_test_required_before_implementation"
    ] is True
    assert governance_coverage["coverage_controls"]["tdd_order"][
        "closure_denied_without_test_pass"
    ] is True
    assert governance_coverage["coverage_controls"]["auto_registration"][
        "functional_registry_required"
    ] is True
    assert governance_coverage["coverage_controls"]["auto_registration"][
        "glossary_registry_required"
    ] is True
    assert governance_coverage["coverage_controls"]["auto_registration"][
        "db_feedback_append_only"
    ] is True
    assert governance_coverage["coverage_controls"]["auto_registration"][
        "add_feature_ticket_import_deferred_plan"
    ] == str(PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert governance_coverage["coverage_controls"]["auto_registration"][
        "ticket_registration_is_completion_evidence"
    ] is False
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
    doc_readiness_matrix = governance_coverage[
        "documentation_readiness_detection_matrix"
    ]
    assert doc_readiness_matrix["current_scope_action"] == (
        "map_user_doc_governance_request_to_existing_l1_l6_controls"
    )
    assert doc_readiness_matrix["matrix_is_l7_work"] is False
    assert doc_readiness_matrix["detector_execution_added_now"] is False
    assert doc_readiness_matrix["fail_close_promotion_added_now"] is False
    assert doc_readiness_matrix["db_write_added_now"] is False
    assert doc_readiness_matrix["rows_checked"] == 7
    doc_gap_rows = {
        row["gap_pattern"]: row for row in doc_readiness_matrix["rows"]
    }
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
    assert {
        row["detecting_control"] for row in doc_gap_rows.values()
    }.issubset(governance_coverage["coverage_controls"])
    assert {
        row["primary_governance_surface"] for row in doc_gap_rows.values()
    }.issubset(governance_surfaces)
    for row in doc_gap_rows.values():
        assert row["finding_types"]
        assert row["completion_boundary"].startswith("L6_design_only_")
    detection_policy = governance_coverage["governance_detection_policy"]
    assert detection_policy == {
        "current_scope_action": "define_l6_detection_contract_only",
        "detector_execution_added_now": False,
        "fail_close_promotion_added_now": False,
        "db_write_added_now": False,
        "route_to_gate_input": True,
        "route_to_feedback_candidate": True,
        "candidate_is_not_closure": True,
        "allowed_severities": ["P0", "P1", "P2", "P3"],
        "required_route_fields": [
            "control_id",
            "finding_types",
            "severity_floor",
            "source_artifact",
            "gate_inputs",
            "feedback_behavior",
            "completion_boundary",
        ],
        "completion_boundary_rule": detection_policy["completion_boundary_rule"],
    }
    assert "cannot prove implementation" in detection_policy[
        "completion_boundary_rule"
    ]
    normalization_policy = governance_coverage[
        "governance_finding_normalization_policy"
    ]
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
    assert set(normalization_contracts) == set(
        governance_coverage["coverage_controls"]
    )
    assert governance_coverage["summary"][
        "governance_finding_normalization_contracts_checked"
    ] == len(normalization_contracts)
    assert governance_coverage["summary"][
        "governance_normalization_required_fields_checked"
    ] == len(normalization_policy["required_fields"])
    assert normalization_contracts["tdd_order"]["normalized_finding_type"] == (
        "tdd_order_violation"
    )
    assert normalization_contracts["ddd_registry"]["source_category"] == (
        "ddd_registry"
    )
    assert normalization_contracts["auto_registration"]["db_target"] == (
        "contract_registry"
    )
    for control_id, contract in normalization_contracts.items():
        for field in normalization_policy["required_fields"]:
            assert field in contract, control_id
        assert contract["db_target"] in normalization_policy["allowed_db_targets"]
        assert contract["lifecycle_state"] in normalization_policy[
            "allowed_lifecycle_states"
        ]
        assert contract["completion_guard"] in normalization_policy[
            "allowed_completion_guards"
        ]
        assert contract["feedback_route"], control_id
    governance_control_trace = {
        item["control_id"]: item
        for item in governance_coverage["governance_control_trace"]
    }
    assert set(governance_control_trace) == set(
        governance_coverage["coverage_controls"]
    )
    detection_routes = {
        item["control_id"]: item
        for item in governance_coverage["control_detection_routes"]
    }
    assert set(detection_routes) == set(governance_coverage["coverage_controls"])
    assert governance_coverage["summary"]["governance_controls_checked"] == len(
        governance_coverage["coverage_controls"]
    )
    assert governance_coverage["summary"][
        "governance_detection_required_route_fields_checked"
    ] == len(detection_policy["required_route_fields"])
    assert governance_coverage["summary"]["governance_detection_routes_checked"] == len(
        detection_routes
    )
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
        assert all(
            field in route for field in detection_policy["required_route_fields"]
        ), route["control_id"]
        assert route["severity_floor"] in detection_policy["allowed_severities"]
        assert route["finding_types"], route["control_id"]
        assert route["gate_inputs"] == ["G6", "pre-push"], route["control_id"]
        assert route["feedback_behavior"] == "append_candidate_only"
        assert route["completion_boundary"] == governance_control_trace[
            route["control_id"]
        ]["current_scope_status"]
        assert not route["source_artifact"].startswith("docs/v2/L7-test-design/")
        assert (REPO_ROOT / route["source_artifact"]).exists(), route["control_id"]
        route_text = _read(REPO_ROOT / route["source_artifact"])
        if "companion_artifact" in route:
            assert not route["companion_artifact"].startswith(
                "docs/v2/L7-test-design/"
            )
            assert (REPO_ROOT / route["companion_artifact"]).exists()
            route_text = f"{route_text}\n{_read(REPO_ROOT / route['companion_artifact'])}"
        for finding_type in route["finding_types"]:
            assert finding_type in route_text, (
                route["control_id"],
                finding_type,
            )
    closure_contract = governance_coverage["governance_control_closure_contract"]
    assert closure_contract["current_scope_action"] == (
        "prove_governance_detection_to_feedback_alignment_only"
    )
    assert closure_contract["source_collections"] == [
        "coverage_controls",
        "governance_finding_normalization_contracts",
        "control_detection_routes",
        "governance_control_trace",
    ]
    assert closure_contract["control_identity_field"] == "control_id"
    assert closure_contract["controls_checked"] == len(
        governance_coverage["coverage_controls"]
    )
    assert closure_contract["db_write_allowed_now"] is False
    assert closure_contract["detector_execution_allowed_now"] is False
    assert closure_contract["fail_close_allowed_now"] is False
    assert closure_contract["l7_or_adoption_evidence_allowed"] is False
    closure_rows = {
        item["control_id"]: item for item in closure_contract["rows"]
    }
    assert set(closure_rows) == set(governance_coverage["coverage_controls"])
    assert governance_coverage["summary"]["governance_control_trace_rows_checked"] == len(
        governance_control_trace
    )
    assert governance_coverage["summary"][
        "governance_control_closure_rows_checked"
    ] == len(closure_rows)
    for control_id, row in closure_rows.items():
        normalized = normalization_contracts[control_id]
        route = detection_routes[control_id]
        trace = governance_control_trace[control_id]
        assert row["normalized_finding_type"] == normalized[
            "normalized_finding_type"
        ]
        assert row["source_category"] == normalized["source_category"]
        assert row["db_target"] == normalized["db_target"]
        assert row["lifecycle_state"] == normalized["lifecycle_state"]
        assert row["feedback_route"] == normalized["feedback_route"]
        assert row["gate_inputs"] == route["gate_inputs"]
        assert row["severity_floor"] == route["severity_floor"]
        assert row["completion_boundary"] == trace["current_scope_status"]
    assert governance_control_trace["tdd_order"]["current_scope_status"] == (
        "l6_design_only_not_l7_execution"
    )
    assert governance_control_trace["auto_registration"]["current_scope_status"] == (
        "l6_design_only_not_db_write"
    )
    assert governance_control_trace["impact_visibility"]["current_scope_status"] == (
        "l6_design_only_not_cli"
    )
    for control in governance_control_trace.values():
        artifact = REPO_ROOT / control["source_artifact"]
        assert artifact.exists(), control["control_id"]
        text = _read(artifact)
        for term in control["required_terms"]:
            assert term in text, f"{control['control_id']}: {term}"
    assert governance_coverage["preexisting_pair_policy"][
        "current_audit_created_these_l7_artifacts"
    ] is False
    assert governance_coverage["preexisting_pair_policy"][
        "current_scope_uses_l7_as_completion_evidence"
    ] is False
    for ref in governance_coverage["preexisting_pair_policy"][
        "preexisting_l7_pair_refs"
    ]:
        assert ref.startswith("docs/v2/L7-test-design/"), ref
        assert (REPO_ROOT / ref).exists(), ref
    source_refs = {
        ref
        for refs in governance_coverage["sources"].values()
        for ref in refs
    }
    assert not set(
        governance_coverage["preexisting_pair_policy"]["preexisting_l7_pair_refs"]
    ).intersection(source_refs)
    completed_feature_refs = set(
        governance_coverage["sources"]["preexisting_completed_feature_entry_points"]
    )
    deferred_feature_refs = set(
        governance_coverage["sources"]["deferred_feature_entry_points"]
    )
    assert completed_feature_refs.isdisjoint(deferred_feature_refs)
    assert (
        "docs/plans/add-feature/add-feature-2026-06-05-registry-detector-base.md"
        in completed_feature_refs
    )
    assert governance_surfaces["GOV-CODING-RULE"]["completed_feature_plan"] in completed_feature_refs
    assert governance_surfaces["GOV-DDD-REGISTRY"]["completed_feature_plan"] in completed_feature_refs
    for refs in governance_coverage["sources"].values():
        for ref in refs:
            assert (REPO_ROOT / ref).exists(), ref
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
        artifact = REPO_ROOT / surface["artifact"]
        assert artifact.exists(), surface["artifact"]
        if "deferred_feature_plan" in surface:
            plan_ref = surface["deferred_feature_plan"]
            assert plan_ref in deferred_feature_refs
        else:
            plan_ref = surface["completed_feature_plan"]
            assert plan_ref in completed_feature_refs
        assert (REPO_ROOT / plan_ref).exists(), surface["id"]
        assert surface["artifact"].startswith("docs/v2/L6-functional-design/")
        assert plan_ref.startswith("docs/plans/add-feature/")
        assert "L6" in surface["scope_result"], surface["id"]
        assert "implementation" not in surface["scope_result"].lower(), surface["id"]
        if surface["design_status"] == "frozen_existing_pair":
            frozen_existing_pairs.add(surface["id"])
        if surface["design_status"] == "current_scope_l6_design":
            current_scope_l6_designs.add(surface["id"])
        text = _read(artifact)
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
    assert governance_coverage["completion_denial"]["reason"].startswith(
        "This audit proves L1-L6 governance hardening design coverage"
    )

    feature_plan_text = _read(CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN)
    feature_plan_meta = yaml.safe_load(feature_plan_text.split("---", 2)[1])
    assert feature_plan_meta["plan_id"] == (
        "add-feature-2026-06-12-codex-claude-guard-parity-l7"
    )
    assert feature_plan_meta["workflow"] == "add-feature"
    assert feature_plan_meta["kind"] == "add-impl"
    assert feature_plan_meta["layer"] == "L7"
    assert feature_plan_meta["status"] == "draft"
    assert "This PLAN is only a ticket" in feature_plan_meta["approval_boundary"]
    assert "Draft only. This is a feature ticket" in feature_plan_text
    assert "not a completed L7 deliverable" in feature_plan_text

    fr_trace = yaml.safe_load(_read(L1_L6_FR31_TRACE_MAP))
    assert fr_trace["schema_version"] == "l1_l6_fr31_trace_map_v1"
    assert fr_trace["status"] == "current_scope_l1_l6_trace_clean_not_l7"
    assert fr_trace["scope"] == "L1-L6"
    assert fr_trace["detector_expected"]["requirements"] == 31
    assert fr_trace["detector_expected"]["design_links"] == 31
    assert fr_trace["boundary"]["l7_implementation_done"] is False
    assert fr_trace["boundary"]["goal_complete_allowed"] is False
    rows = fr_trace["requirements"]
    assert len(rows) == 31
    assert fr_trace["summary"]["requirement_count"] == len(rows)
    assert fr_trace["summary"]["all_requirements_have_design_link"] is True
    assert fr_trace["summary"]["missing_downstream"] == []
    assert fr_trace["summary"]["blocking_findings"] == 0
    for row in rows:
        assert row["requirement_id"].startswith("FR-")
        assert row["downstream_ids"]
        assert row["design_definition_ids"]
        assert row["design_anchor_count"] > 0
    row_by_id = {row["requirement_id"]: row for row in rows}
    assert row_by_id["FR-01"]["design_definition_ids"] == ["FR-NSM-01"]
    assert row_by_id["FR-08"]["design_definition_ids"] == [
        "FR-4ART-01",
        "FR-DOCTOR-01",
    ]
    assert row_by_id["FR-13"]["design_definition_ids"] == [
        "FR-CTX-01",
        "FR-GATE-01",
        "FR-PLAN-01",
    ]
    assert row_by_id["FR-FNREG-01"]["design_definition_ids"] == ["FR-FNREG-01"]
    assert row_by_id["FR-GLOSSARY-01"]["design_definition_ids"] == [
        "FR-GLOSSARY-01"
    ]

    payload = yaml.safe_load(_read(OBJECTIVE_L1_L6_COVERAGE_AUDIT))
    supporting_evidence = payload["l1_l6_supporting_evidence"]
    assert supporting_evidence == {
        "asset_inventory": str(L1_L6_DESIGN_ASSET_INVENTORY.relative_to(REPO_ROOT)),
        "improvement_candidate_map": str(
            L1_L6_IMPROVEMENT_CANDIDATE_MAP.relative_to(REPO_ROOT)
        ),
        "pair_balance_map": str(L1_L6_PAIR_BALANCE_MAP.relative_to(REPO_ROOT)),
        "guard_parity_map": str(
            L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP.relative_to(REPO_ROOT)
        ),
        "deferred_feature_coverage_map": str(
            L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "db_feedback_lifecycle_coverage_map": str(
            L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "harness_external_tools_coverage_map": str(
            L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "governance_hardening_coverage_map": str(
            L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "workflow_automation_coverage_map": str(
            L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "db_registration_readiness_coverage_map": str(
            L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "dependency_impact_readiness_coverage_map": str(
            L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "bottleneck_remediation_readiness_coverage_map": str(
            L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "full_objective_gap_status": str(
            FULL_OBJECTIVE_GAP_STATUS.relative_to(REPO_ROOT)
        ),
        "ratification_index": str(
            L1_L6_RATIFICATION_INDEX.relative_to(REPO_ROOT)
        ),
        "exit_criteria_map": str(
            L1_L6_EXIT_CRITERIA_MAP.relative_to(REPO_ROOT)
        ),
        "reference_integrity_coverage_map": str(
            L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "double_check_coverage_map": str(
            L1_L6_DOUBLE_CHECK_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "l1_l6_web_evidence_map": str(
            L1_L6_WEB_EVIDENCE_SOURCE_MAP.relative_to(REPO_ROOT)
        ),
        "fr31_trace_map": str(L1_L6_FR31_TRACE_MAP.relative_to(REPO_ROOT)),
    }

    entry_points = payload["deferred_feature_entry_points"]
    deferred_feature_coverage = yaml.safe_load(
        _read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP)
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
    assert entry_points == expected_deferred_entry_points
    assert entry_points == {
        "fr_registry_glossary": (
            "docs/plans/add-feature/add-feature-2026-06-12-fr-registry-glossary-l7-entry.md"
        ),
        "codex_claude_guard_parity": str(
            CODEX_CLAUDE_GUARD_PARITY_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "db_evidence_lifecycle": str(
            DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "harness_external_tools": str(
            HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "full_flow_remaining_guards": str(
            FULL_FLOW_REMAINING_GUARDS_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "plan_registry_add_feature_import": str(
            PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "dependency_impact_query": str(
            DEPENDENCY_IMPACT_QUERY_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "bottleneck_routing": str(
            BOTTLENECK_ROUTING_L7_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "l7_unit_closure": (
            "docs/plans/add-feature/add-feature-2026-06-13-l7-unit-closure.md"
        ),
        "phase_enum_l0_l14_runtime_retrofit": str(
            PHASE_ENUM_L0_L14_RUNTIME_RETROFIT_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
        "contract_design_phase_label_retrofit": str(
            CONTRACT_DESIGN_PHASE_LABEL_RETROFIT_FEATURE_PLAN.relative_to(REPO_ROOT)
        ),
    }
    assert "l1_l6_web_evidence_map" not in entry_points
    assert "fr31_trace_map" not in entry_points
    assert payload["completion_denial"]["reason"].startswith(
        "Current evidence proves L1-L6 design coverage"
    )
    assert "approved L7 implementation where needed" in payload["completion_denial"][
        "missing"
    ]


def test_reference_integrity_coverage_map_resolves_l1_l6_audit_bundle() -> None:
    payload = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))

    assert payload["schema_version"] == "l1_l6_reference_integrity_coverage_v1"
    assert payload["status"] == "current_scope_l1_l6_reference_integrity_clean"
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "reference_integrity_map_is_implementation_evidence": False,
        "current_scope_uses_l7_as_completion_evidence": False,
        "l7_artifacts_created_by_this_audit": 0,
        "external_tool_executed": False,
        "schema_migration_done": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
        "audit_files_checked": 25,
                "path_like_refs_checked": 1385,
                "direct_file_refs_checked": 1376,
        "glob_patterns_checked": 9,
        "missing_direct_file_refs": 0,
        "empty_glob_patterns": 0,
        "blocking_findings_current_scope": 0,
    }
    glob_patterns = {item["pattern"]: item["match_count"] for item in payload["glob_patterns"]}
    assert glob_patterns == {
        "docs/v2/L6-functional-design/**/function-spec.md": 18,
        "docs/v2/L6-functional-design/**/*function-spec.md": 18,
        "docs/v2/L1-requirements/**/*.md": 5,
        "docs/v2/L3-requirements/**/*.md": 4,
        "docs/v2/L4*/**/*.md": 6,
            "docs/v2/L5*/**/*.md": 6,
            "docs/v2/L6*/**/*.md": 27,
            "docs/v2/audit/2026-06-12-*.yaml": 21,
                    "docs/plans/add-feature/add-feature-*.md": 26,
        }
    assert payload["reference_policy"]["direct_paths_must_exist"] is True
    assert payload["reference_policy"]["glob_patterns_must_expand_non_empty"] is True
    assert payload["reference_policy"]["l7_boundary"] == {
        "allowed_as_boundary_metadata": True,
        "allowed_as_current_scope_completion_evidence": False,
    }
    bundle_alignment = payload["bundle_alignment_contract"]
    ratification = yaml.safe_load(_read(REPO_ROOT / bundle_alignment["ratification_index"]))
    assert bundle_alignment["ratification_sources_considered"] == [
        "objective_audit",
        "core_audit_bundle",
        "integrity_audits",
    ]
    assert bundle_alignment["reference_bundle_policy"] == "yaml_audit_bundle_only"
    ratification_sources = set()
    for group in bundle_alignment["ratification_sources_considered"]:
        ratification_sources.update(ratification["sources"][group])
    reference_sources = set(payload["sources"]["audit_bundle"])
    assert sorted(reference_sources - ratification_sources) == bundle_alignment[
        "required_in_reference_not_ratification"
    ]
    assert sorted(ratification_sources - reference_sources) == bundle_alignment[
        "allowed_in_ratification_not_reference"
    ]
    assert "structured YAML bundle" in bundle_alignment["reason"]
    bundle_completeness = payload["bundle_completeness_contract"]
    all_current_yaml_audits = {
        str(path.relative_to(REPO_ROOT))
        for path in sorted((REPO_ROOT / "docs/v2/audit").glob("2026-06-12-*.yaml"))
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
        str(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP.relative_to(REPO_ROOT))
    }
    assert bundle_completeness["orphan_yaml_audits"] == []
    assert all_current_yaml_audits | explicit_current_scope_audits == reference_sources | set(
        bundle_completeness["allowed_not_in_audit_bundle"]
    )
    markdown_contract = payload["markdown_read_path_contract"]
    grain_path = REPO_ROOT / markdown_contract["grain_balance_audit"]
    grain_text = _read(grain_path)
    markdown_refs = list(_iter_markdown_path_refs(grain_text))
    markdown_direct_refs = [ref for ref in markdown_refs if "*" not in ref]
    markdown_glob_refs = [ref for ref in markdown_refs if "*" in ref]
    assert markdown_contract["extracted_path_refs"] == len(markdown_refs)
    assert markdown_contract["direct_path_refs"] == len(markdown_direct_refs)
    assert markdown_contract["glob_path_refs"] == len(markdown_glob_refs)
    assert markdown_contract["missing_direct_file_refs"] == sum(
        1 for ref in markdown_direct_refs if not (REPO_ROOT / ref).exists()
    )
    assert markdown_contract["empty_glob_patterns"] == sum(
        1 for ref in markdown_glob_refs if not list(REPO_ROOT.glob(ref))
    )
    assert markdown_contract["glob_patterns"] == {
        pattern: len(list(REPO_ROOT.glob(pattern)))
        for pattern in sorted(set(markdown_glob_refs))
    }
    assert markdown_contract["l7_terms_allowed_only_as_boundary"] is True
    for phrase in markdown_contract["required_l7_boundary_phrases"]:
        assert phrase in grain_text
    for ref in payload["sources"]["audit_bundle"]:
        assert (REPO_ROOT / ref).exists(), ref
    structured_refs = []
    for ref in payload["sources"]["audit_bundle"]:
        if not ref.endswith(".yaml"):
            continue
        structured_payload = yaml.safe_load(_read(REPO_ROOT / ref))
        structured_refs.extend(_iter_structured_path_refs(structured_payload))
    glob_refs = [ref for ref in structured_refs if "*" in ref]
    direct_refs = [ref for ref in structured_refs if "*" not in ref]
    assert payload["summary"]["path_like_refs_checked"] == len(structured_refs)
    assert payload["summary"]["direct_file_refs_checked"] == len(direct_refs)
    assert payload["summary"]["glob_patterns_checked"] == len(glob_refs)
    assert str(L1_L6_RATIFICATION_INDEX.relative_to(REPO_ROOT)) in structured_refs
    assert ".helix/handover/CURRENT.md" in direct_refs
    assert structured_refs
    for ref in structured_refs:
        if "*" in ref:
            assert list(REPO_ROOT.glob(ref)), ref
        else:
            assert (REPO_ROOT / ref).exists(), ref
    for pattern, expected_count in glob_patterns.items():
        assert len(list(REPO_ROOT.glob(pattern))) == expected_count
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves reference integrity for the current L1-L6 audit bundle"
    )


def test_l0_l14_flow_surface_coverage_pins_user_confirmed_flow() -> None:
    payload = yaml.safe_load(_read(L0_L14_FLOW_SURFACE_COVERAGE_MAP))
    pair_balance = yaml.safe_load(_read(L1_L6_PAIR_BALANCE_MAP))

    assert payload["schema_version"] == "l0_l14_flow_surface_coverage_v1"
    assert payload["status"] == "current_l0_l14_flow_terms_pinned_l1_l6_scope"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "flow_surface_audit_is_l7_work": False,
        "flow_surface_audit_is_implementation_evidence": False,
        "l7_implementation_done": False,
        "l7_test_design_created_by_this_audit": False,
        "helix_db_write_performed": False,
        "external_tool_installed": False,
        "external_tool_executed": False,
        "ci_or_equivalent_connected": False,
        "full_goal_complete": False,
        "goal_complete_allowed": False,
    }
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
    assert flow["L7"]["current_scope_l1_l6_status"] == (
        "out_of_current_scope_requires_feature_ticket"
    )
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
    pair_contracts = {
        item["layer"]: item for item in pair_balance["pair_contract_matrix"]
    }
    assert set(pair_contracts) == set(pairs)
    for item in payload["pair_map"]:
        contract = pair_contracts[item["design_layer"]]
        if item["design_layer"] == "L6":
            assert contract["paired_test_design_stage"].startswith(item["test_design"])
        else:
            assert contract["paired_test_design_stage"] == item["test_design"]
        assert contract["expected_pair"] == (
            f"{item['design_layer']}-{item['execution_layer']}"
        )
        assert contract["current_scope_status"] in {
            "pair_contract_present",
            "waiver_present",
            "l6_unit_test_design_viewpoints_only_not_l7_artifact",
        }
    for refs in payload["sources"].values():
        for ref in refs:
            assert (REPO_ROOT / ref).exists(), ref
    current_surfaces = payload["sources"]["current_surfaces_checked"]
    legacy_terms = payload["legacy_term_policy"]["current_surfaces_must_not_contain"]
    assert payload["summary"]["current_surfaces_checked"] == len(current_surfaces)
    assert legacy_terms
    for ref in current_surfaces:
        text = _read(REPO_ROOT / ref)
        for term in legacy_terms:
            assert term not in text, (ref, term)
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves that the current L0-L14 flow vocabulary"
    )


def test_full_objective_gap_status_keeps_l7_and_full_flow_unclaimed() -> None:
    payload = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    objective_coverage = yaml.safe_load(_read(OBJECTIVE_L1_L6_COVERAGE_AUDIT))
    deferred_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    reference_integrity = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))

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
        "repository_add_feature_files_discovered": 26,
        "current_objective_deferred_feature_tickets": 11,
        "out_of_current_objective_add_feature_files": 15,
        "out_of_current_objective_completed_add_features": 4,
        "out_of_current_objective_parked_feature_tickets": 0,
        "right_arm_execution_gates_deferred": 3,
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
        "all_repository_add_feature_files_checked": 26,
        "current_objective_deferred_feature_tickets_checked": 11,
        "excluded_from_current_objective_deferred_count": 15,
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
    assert c3b_entry["path"] == (
        "docs/plans/add-feature/add-feature-2026-06-18-fruses-reverse-derived-promotion.md"
    )
    assert c3b_entry["observed_status"] == "in_progress"
    assert c3b_entry["classification"] == (
        "current_scope_authorized_c3b_fr_uses_reverse_derived_full_required"
    )
    assert "C-3b" in c3b_entry["reason"]
    assert "derived index" in c3b_entry["reason"]
    assert "full-required" in c3b_entry["reason"]
    assert "broad advisory→fail-close flip of W1 detectors" in c3b_entry["reason"]
    c3c_entry = excluded_by_id["c3c_coding_rule_core_full_required"]
    assert c3c_entry["id"] == "c3c_coding_rule_core_full_required"
    assert c3c_entry["path"] == (
        "docs/plans/add-feature/add-feature-2026-06-18-coding-rule-core-full-required.md"
    )
    assert c3c_entry["observed_status"] == "draft"
    assert c3c_entry["classification"] == (
        "current_scope_authorized_c3c_coding_rule_core_full_required"
    )
    assert "C-3c" in c3c_entry["reason"]
    assert "bash-n/py_compile" in c3c_entry["reason"]
    assert "full-scan required" in c3c_entry["reason"]
    assert "ruff/shellcheck" in c3c_entry["reason"]
    c3de_entry = excluded_by_id["c3de_plandep_depcycle_baseline_required"]
    assert c3de_entry["id"] == "c3de_plandep_depcycle_baseline_required"
    assert c3de_entry["path"] == (
        "docs/plans/add-feature/add-feature-2026-06-19-plandep-depcycle-baseline-required.md"
    )
    assert c3de_entry["observed_status"] == "draft"
    assert c3de_entry["classification"] == (
        "current_scope_authorized_c3de_plandep_depcycle_baseline_required"
    )
    assert "C-3d/e" in c3de_entry["reason"]
    assert "baseline-required" in c3de_entry["reason"]
    assert "baseline 超の新債だけ" in c3de_entry["reason"]
    assert "full-required ではなく" in c3de_entry["reason"]
    c4a_entry = excluded_by_id["c4a_g8_integration_execution_gate"]
    assert c4a_entry["id"] == "c4a_g8_integration_execution_gate"
    assert c4a_entry["path"] == (
        "docs/plans/add-feature/add-feature-2026-06-19-g8-integration-execution-gate.md"
    )
    assert c4a_entry["observed_status"] == "draft"
    assert c4a_entry["classification"] == (
        "current_scope_authorized_c4a_g8_integration_execution_gate"
    )
    assert "C-4a" in c4a_entry["reason"]
    assert "G8 / L5-L8" in c4a_entry["reason"]
    assert "integration" in c4a_entry["reason"]
    assert "deferred" in c4a_entry["reason"]
    push_gate_entry = excluded_by_id["push_gate_test_tiering"]
    assert push_gate_entry["id"] == "push_gate_test_tiering"
    assert push_gate_entry["path"] == (
        "docs/plans/add-feature/add-feature-2026-06-18-push-gate-test-tiering.md"
    )
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
    assert set(payload["source_audits"]) == set(
        source_audit_contract["required_source_audit_keys"]
    )
    for audit_key, audit_path in payload["source_audits"].items():
        assert audit_path.startswith("docs/v2/audit/"), audit_key
        assert not audit_path.startswith("docs/v2/L7-test-design/"), audit_key
        assert not audit_path.startswith("docs/plans/add-feature/"), audit_key
        assert (REPO_ROOT / audit_path).exists(), audit_key
    source_audit_bundle_alignment_contract = payload[
        "source_audit_bundle_alignment_contract"
    ]
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
    assert (
        source_audit_bundle_alignment_contract[
            "l7_or_add_feature_source_alignment_allowed"
        ]
        is False
    )
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
    harness_recheck_scope = payload[
        "harness_external_tool_adoption_recheck_scope_contract"
    ]
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
    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    harness_scope = harness_coverage[harness_recheck_scope["source_contract"]]
    assert harness_recheck_scope["source_audit_key"] in payload["source_audits"]
    assert harness_recheck_scope["adoption_recheck_controls_checked"] == (
        harness_scope["adoption_recheck_controls_checked"]
    )
    assert harness_recheck_scope["latest_core_rechecked_sources_checked"] == (
        harness_scope["latest_core_rechecked_sources_checked"]
    )
    assert harness_recheck_scope["all_candidate_sources_checked"] == (
        harness_scope["all_candidate_sources_checked"]
    )
    assert harness_recheck_scope["spot_recheck_sources_checked"] == (
        harness_scope["spot_recheck_sources_checked"]
    )
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
    assert harness_current_session_recheck["source_audit_key"] in payload[
        "source_audits"
    ]
    assert harness_current_session_recheck["official_sources_checked"] == (
        harness_current_session_source["official_sources_checked"]
    )
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
    assert harness_accountability[
        "current_scope_must_keep_install_execution_ci_db_false"
    ] == harness_accountability_source[
        "current_scope_must_keep_install_execution_ci_db_false"
    ]
    assert harness_accountability["l7_work_requires_feature_ticket"] == (
        harness_accountability_source["l7_work_requires_feature_ticket"]
    )
    assert payload["l1_l6_design_obligation_contract"] == {
        "source_audit_key": "deferred_design_obligation_proof",
        "source_contract": "design_obligation_rows",
        "current_scope_action": (
            "prove_l1_l6_design_obligation_before_deferring_l7_execution"
        ),
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
    assert payload["source_audits"][
        objective_clause_mapping_contract["source_audit_key"]
    ] == str(OBJECTIVE_L1_L6_COVERAGE_AUDIT.relative_to(REPO_ROOT))
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
    expected_feature_unlock_targets = {
        "full_flow_remaining_guards": {
            "routed_from_completion_audit_ids": [
                "REQ-L0-L14-FLOW",
                "REQ-WORKFLOW-AUTOMATION-DB",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "right_arm_execution_deferred",
                "db_write_and_gate_implementation_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": [
                "right_arm_execution_gates",
                "ci_or_equivalent",
            ],
        },
        "l7_unit_closure": {
            "routed_from_completion_audit_ids": [
                "REQ-GRAIN-BALANCE-L1-L6",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "l7_unit_execution_and_coverage_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": ["l7_unit", "coverage_closure"],
        },
        "db_evidence_lifecycle": {
            "routed_from_completion_audit_ids": [
                "REQ-DDD-TDD-AUTO-DETECTION",
                "REQ-WORKFLOW-AUTOMATION-DB",
                "REQ-DEPENDENCY-IMPACT-VISIBILITY",
                "REQ-BOTTLENECK-REMEDIATION",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "detector_execution_and_db_write_deferred",
                "db_write_and_gate_implementation_deferred",
                "impact_query_and_db_projection_deferred",
                "routing_execution_and_recurrence_closure_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": [
                "db_write",
                "document_auto_registration",
                "feedback_loop",
                "recurrence_closure",
            ],
        },
        "harness_external_tools": {
            "routed_from_completion_audit_ids": [
                "REQ-HARNESS-EXTERNAL-TOOLS-WEB",
                "REQ-DEPENDENCY-IMPACT-VISIBILITY",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "approval_recheck_install_execution_and_ci_deferred",
                "impact_query_and_db_projection_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": ["external_tool", "adoption_recheck", "ingestion"],
        },
        "codex_claude_guard_parity": {
            "routed_from_completion_audit_ids": ["REQ-CODEX-CLAUDE-PARITY"],
            "routed_remaining_classes": [
                "runtime_parity_implementation_deferred"
            ],
            "required_unlock_tokens": ["runtime_guard_parity"],
        },
        "fr_registry_glossary": {
            "routed_from_completion_audit_ids": [
                "REQ-DDD-TDD-AUTO-DETECTION"
            ],
            "routed_remaining_classes": [
                "detector_execution_and_db_write_deferred"
            ],
            "required_unlock_tokens": ["registry", "glossary"],
        },
        "plan_registry_add_feature_import": {
            "routed_from_completion_audit_ids": [
                "REQ-DDD-TDD-AUTO-DETECTION",
                "REQ-WORKFLOW-AUTOMATION-DB",
            ],
            "routed_remaining_classes": [
                "detector_execution_and_db_write_deferred",
                "db_write_and_gate_implementation_deferred",
            ],
            "required_unlock_tokens": [
                "plan_registry",
                "plan_registry_import",
                "add_feature",
            ],
        },
        "dependency_impact_query": {
            "routed_from_completion_audit_ids": [
                "REQ-DEPENDENCY-IMPACT-VISIBILITY"
            ],
            "routed_remaining_classes": [
                "impact_query_and_db_projection_deferred"
            ],
            "required_unlock_tokens": ["dependency_impact", "edge_visibility"],
        },
        "bottleneck_routing": {
            "routed_from_completion_audit_ids": [
                "REQ-BOTTLENECK-REMEDIATION"
            ],
            "routed_remaining_classes": [
                "routing_execution_and_recurrence_closure_deferred"
            ],
            "required_unlock_tokens": [
                "bottleneck_candidate_routing",
                "recurrence_closure",
            ],
        },
        "phase_enum_l0_l14_runtime_retrofit": {
            "routed_from_completion_audit_ids": [
                "REQ-L0-L14-FLOW",
                "REQ-WORKFLOW-AUTOMATION-DB",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "right_arm_execution_deferred",
                "db_write_and_gate_implementation_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": ["runtime_phase_enum", "handover_validation"],
        },
        "contract_design_phase_label_retrofit": {
            "routed_from_completion_audit_ids": [
                "REQ-L0-L14-FLOW",
                "REQ-WORKFLOW-AUTOMATION-DB",
                "REQ-FULL-GOAL-COMPLETION",
            ],
            "routed_remaining_classes": [
                "right_arm_execution_deferred",
                "db_write_and_gate_implementation_deferred",
                "denial_item_not_counted_as_work_blocker",
            ],
            "required_unlock_tokens": [
                "contract_design_phase_label_retirement",
                "contract_semantics_preserved",
            ],
        },
    }
    assert feature_unlock_contract == {
        "feature_collection": "feature_ticket_boundaries",
        "audit_collection": "completion_audit_matrix",
        "unlock_field": "unlocks",
        "routed_from_field": "feature_ticket_ids",
        "remaining_class_field": "remaining_class",
        "every_feature_ticket_must_have_unlock_target": True,
        "unlock_targets_must_match_completion_audit_routes": True,
        "unlock_targets_must_cover_routed_remaining_classes": True,
        "unlock_targets_are_completion_evidence": False,
        "l7_execution_allowed_by_unlock_targets": False,
            "targets": expected_feature_unlock_targets,
        }
    handover_boundary_contract = payload["handover_boundary_contract"]
    assert {
        key: value
        for key, value in handover_boundary_contract.items()
        if key != "required_current_user_boundary_contains"
    } == {
        "handover_current_markdown": ".helix/handover/CURRENT.md",
        "handover_current_json": ".helix/handover/CURRENT.json",
        "next_action_heading_required": "## Next Action (Codex 向け)",
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
        "right_arm_execution_work_allowed_from_handover": True,
        "product_l7_work_allowed_from_handover": False,
    }
    assert handover_boundary_contract["required_current_user_boundary_contains"] == [
        "implement",
        "DF-P2-DEFERRED-COUNT-DERIVE",
        "refactor-2026-06-20-deferred-count-derive.md",
        "live SSoT helper",
        "docs/test mirror",
    ]
    handover_path = REPO_ROOT / handover_boundary_contract["handover_current_markdown"]
    handover_text = handover_path.read_text(encoding="utf-8")
    assert (
        handover_boundary_contract["next_action_heading_required"] in handover_text
    )
    next_action_text = handover_text.split(
        handover_boundary_contract["next_action_heading_required"], 1
    )[1].split("\n## ", 1)[0]
    for token in handover_boundary_contract["required_current_user_boundary_contains"]:
        assert token in next_action_text
    latest_boundary = payload["latest_user_boundary"]
    if handover_boundary_contract[
        "latest_user_boundary_forbidden_items_must_be_reflected_in_handover"
    ]:
        assert len(
            handover_boundary_contract[
                "latest_user_boundary_forbidden_handover_terms"
            ]
        ) == len(latest_boundary["forbidden_now"])
        for forbidden_term in handover_boundary_contract[
            "latest_user_boundary_forbidden_handover_terms"
        ]:
            assert forbidden_term in next_action_text, forbidden_term
    for suppression_term in handover_boundary_contract[
        "legacy_handover_suppression_terms"
    ]:
        assert suppression_term in next_action_text, suppression_term
    handover_state = json.loads(
        (REPO_ROOT / handover_boundary_contract["handover_current_json"]).read_text(
            encoding="utf-8"
        )
    )
    assert "deferred_count/deferred_gates" in handover_state["task"]["title"]
    assert "live VG derive" in handover_state["task"]["title"]
    assert handover_state["files"]["pending"] == [
        "cli/lib/vg_overview.py",
        "cli/lib/tests/test_helix_l0_l14_flow_contract.py",
        "cli/tests/test-helix-l0-l14-flow-contract.bats",
        "docs/v2/L7-test-design/goal-completion-audit.yaml",
        "docs/v2/audit/2026-06-12-full-objective-gap-status.yaml",
    ]
    assert handover_boundary_contract["handover_task_title_may_be_legacy"] is True
    assert handover_boundary_contract["handover_pending_entries_may_be_legacy"] is True
    assert handover_boundary_contract["legacy_task_title_must_not_authorize_l7"] is True
    assert handover_boundary_contract["legacy_pending_entries_must_not_authorize_l7"] is True
    assert (
        handover_boundary_contract[
            "handover_next_action_supersedes_legacy_pending_entries"
        ]
        is True
    )
    assert latest_boundary["l7_route"] == "add_feature_ticket_only"
    assert handover_boundary_contract[
        "latest_user_boundary_must_match_handover_next_action"
    ] is True
    assert (
        handover_boundary_contract[
            "latest_user_boundary_forbidden_items_must_be_reflected_in_handover"
        ]
        is False
    )
    assert handover_boundary_contract[
        "latest_user_boundary_l7_route_must_be_reflected_in_handover"
    ] is True
    assert handover_boundary_contract[
        "latest_user_boundary_allowed_work_must_be_reflected_in_handover"
    ] is True
    assert handover_boundary_contract["right_arm_execution_work_allowed_from_handover"] is True
    assert handover_boundary_contract["product_l7_work_allowed_from_handover"] is False
    source_audit_key = feature_boundary_contract["source_audit_key"]
    assert payload["source_audits"][source_audit_key] == str(
        L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
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
    status_by_id = {item["id"]: item for item in payload["objective_status"]}
    assert set(status_by_id) == {
        "REQ-L0-L14-FLOW",
        "REQ-ASSET-REQ-GAP-L6",
        "REQ-GRAIN-BALANCE-L1-L6",
        "REQ-CODEX-CLAUDE-PARITY",
        "REQ-DDD-TDD-AUTO-DETECTION",
        "REQ-WORKFLOW-AUTOMATION-DB",
        "REQ-HARNESS-EXTERNAL-TOOLS-WEB",
        "REQ-DEPENDENCY-IMPACT-VISIBILITY",
        "REQ-BOTTLENECK-REMEDIATION",
        "REQ-FULL-GOAL-COMPLETION",
    }
    assert status_by_id["REQ-ASSET-REQ-GAP-L6"]["remaining_for_full_goal"] == []
    assert status_by_id["REQ-FULL-GOAL-COMPLETION"]["l1_l6_status"] == (
        "not_applicable_as_completion_claim"
    )
    completion_audit = {
        item["id"]: item for item in payload["completion_audit_matrix"]
    }
    assert set(completion_audit) == set(status_by_id)
    assert completion_audit["REQ-ASSET-REQ-GAP-L6"]["full_goal_blocker"] is False
    assert completion_audit["REQ-FULL-GOAL-COMPLETION"][
        "current_l1_l6_verdict"
    ] == "denied_not_current_scope"
    assert sum(1 for item in completion_audit.values() if item["full_goal_blocker"]) == (
        payload["summary"]["blocking_findings_full_goal"]
    )
    for item_id, item in completion_audit.items():
        assert item["current_l1_l6_verdict"], item_id
        assert item["proof_strength"], item_id
        assert item["remaining_class"], item_id
        assert item["authoritative_evidence_keys"], item_id
        assert set(item["authoritative_evidence_keys"]).issubset(
            set(payload["source_audits"])
        ), item_id
        for evidence_key in item["authoritative_evidence_keys"]:
            resolved_path = payload["source_audits"][evidence_key]
            assert resolved_path.startswith("docs/v2/audit/"), (item_id, evidence_key)
            assert not resolved_path.startswith("docs/v2/L7-test-design/"), (
                item_id,
                evidence_key,
            )
            assert not resolved_path.startswith("docs/plans/add-feature/"), (
                item_id,
                evidence_key,
            )
            assert (REPO_ROOT / resolved_path).exists(), (item_id, evidence_key)
    used_source_audit_keys = set()
    for item in completion_audit.values():
        used_source_audit_keys.update(item["authoritative_evidence_keys"])
    used_source_audit_keys.add(
        objective_clause_mapping_contract["source_audit_key"]
    )
    used_source_audit_keys.add(feature_boundary_contract["source_audit_key"])
    used_source_audit_keys.add(
        payload["l1_l6_design_obligation_contract"]["source_audit_key"]
    )
    used_source_audit_keys.add(
        payload["harness_external_tool_adoption_recheck_scope_contract"][
            "source_audit_key"
        ]
    )
    unused_source_audit_keys = sorted(
        set(payload["source_audits"]) - used_source_audit_keys
    )
    assert unused_source_audit_keys == source_audit_usage_contract[
        "unused_source_audit_keys"
    ]
    assert used_source_audit_keys == set(payload["source_audits"])
    assert source_audit_usage_contract["all_source_audit_keys_must_be_used"] is True
    assert (
        source_audit_usage_contract["l7_or_add_feature_source_usage_allowed"]
        is False
    )
    assert (
        authoritative_evidence_contract[
            "l7_execution_allowed_by_authoritative_keys"
        ]
        is False
    )
    assert "codex_claude_guard_parity" in completion_audit[
        "REQ-CODEX-CLAUDE-PARITY"
    ]["authoritative_evidence_keys"]
    assert payload["source_audits"]["codex_claude_guard_parity"] == str(
        L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP.relative_to(REPO_ROOT)
    )
    mapped_status_ids = set()
    for mapping in objective_coverage[
        objective_clause_mapping_contract["source_collection"]
    ]:
        assert mapping[objective_clause_mapping_contract["source_id_field"]]
        assert mapping["current_scope_boundary"], mapping
        assert not str(mapping["current_scope_boundary"]).startswith(
            "docs/v2/L7-test-design/"
        )
        for full_status_id in mapping[
            objective_clause_mapping_contract["source_target_field"]
        ]:
            assert full_status_id in status_by_id, full_status_id
            mapped_status_ids.add(full_status_id)
    unmapped_local_status_ids = set(status_by_id) - mapped_status_ids
    assert unmapped_local_status_ids == set(
        objective_clause_mapping_contract[
            "local_status_items_without_objective_clause"
        ]
    )
    allowed_empty_remaining = set(
        status_contract["remaining_policy"]["empty_remaining_allowed_only_for"]
    )
    allowed_statuses = set(status_contract["l1_l6_pass_statuses"]) | set(
        status_contract["non_completion_statuses"]
    )
    forbidden_statuses = set(status_contract["completion_claim_statuses_forbidden"])
    command_proofs = []
    non_completion_count = 0
    for item_id, item in status_by_id.items():
        for field in status_contract["required_fields"]:
            assert field in item, item_id
        assert item["l1_l6_status"] in allowed_statuses, item_id
        assert item["l1_l6_status"] not in forbidden_statuses, item_id
        if item["l1_l6_status"] in status_contract["non_completion_statuses"]:
            non_completion_count += 1
        assert item["proof"], item_id
        for proof in item["proof"]:
            assert not proof.startswith("docs/v2/L7-test-design/"), item_id
            assert not proof.startswith("docs/plans/add-feature/"), item_id
            if "/" in proof and not proof.startswith("helix doctor "):
                assert (REPO_ROOT / proof).exists(), proof
            if "/" not in proof:
                command_proofs.append(proof)
        if not item["remaining_for_full_goal"]:
            assert item_id in allowed_empty_remaining
        if any(
            token in item["l1_l6_status"]
            for token in status_contract["remaining_policy"][
                "later_phase_remaining_required_when_status_contains"
            ]
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
    assert (
        command_proof_policy["command_proofs_must_not_execute_l7_db_ci_external"]
        is True
    )
    assert command_proof_policy["command_proofs_are_completion_evidence"] is False
    assert any(
        "G9/G12/G14 right-arm execution gate" in item
        for item in status_by_id["REQ-FULL-GOAL-COMPLETION"][
            "remaining_for_full_goal"
        ]
    )
    feature_tickets = {item["id"]: item for item in payload["feature_ticket_boundaries"]}
    assert set(feature_tickets) == {
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
    source_feature_tickets = {
        item["id"]: item
        for item in deferred_coverage[
            feature_boundary_contract["source_collection"]
        ]
    }
    assert set(feature_tickets) == set(source_feature_tickets)
    for item_id, item in completion_audit.items():
        routed_feature_ids = item.get("feature_ticket_ids", [])
        if item["full_goal_blocker"]:
            assert routed_feature_ids, item_id
        for feature_id in routed_feature_ids:
            assert feature_id in feature_tickets, (item_id, feature_id)
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
    assert completion_audit["REQ-ASSET-REQ-GAP-L6"]["feature_ticket_ids"] == []
    assert completion_audit["REQ-GRAIN-BALANCE-L1-L6"]["feature_ticket_ids"] == [
        "l7_unit_closure"
    ]
    assert set(feature_unlock_contract["targets"]) == set(feature_tickets)
    for feature_id, target in feature_unlock_contract["targets"].items():
        routed_from = [
            item_id
            for item_id, item in completion_audit.items()
            if feature_id in item.get("feature_ticket_ids", [])
        ]
        assert routed_from == target["routed_from_completion_audit_ids"], feature_id
        routed_remaining_classes = [
            completion_audit[item_id][
                feature_unlock_contract["remaining_class_field"]
            ]
            for item_id in routed_from
        ]
        assert routed_remaining_classes == target["routed_remaining_classes"], (
            feature_id,
            routed_remaining_classes,
        )
        unlock_text = feature_tickets[feature_id][
            feature_unlock_contract["unlock_field"]
        ]
        assert not unlock_text.startswith("docs/"), feature_id
        for token in target["required_unlock_tokens"]:
            assert token in unlock_text, (feature_id, token, unlock_text)
        plan_meta = yaml.safe_load(
            _read(REPO_ROOT / feature_tickets[feature_id]["path"]).split("---", 2)[1]
        )
        assert plan_meta["unlock_conditions"] == target["required_unlock_tokens"]
    db_evidence_plan_meta = yaml.safe_load(
        _read(DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN).split("---", 2)[1]
    )
    assert db_evidence_plan_meta["unlock_conditions"] == [
        "db_write",
        "document_auto_registration",
        "feedback_loop",
        "recurrence_closure",
    ]
    plan_registry_import_meta = yaml.safe_load(
        _read(PLAN_REGISTRY_ADD_FEATURE_IMPORT_L7_FEATURE_PLAN).split("---", 2)[1]
    )
    assert plan_registry_import_meta["unlock_conditions"] == [
        "plan_registry",
        "plan_registry_import",
        "add_feature",
    ]
    assert (
        feature_unlock_contract["every_feature_ticket_must_have_unlock_target"]
        is True
    )
    assert (
        feature_unlock_contract["unlock_targets_must_match_completion_audit_routes"]
        is True
    )
    assert (
        feature_unlock_contract[
            "unlock_targets_must_cover_routed_remaining_classes"
        ]
        is True
    )
    assert feature_unlock_contract["unlock_targets_are_completion_evidence"] is False
    assert (
        feature_unlock_contract["l7_execution_allowed_by_unlock_targets"]
        is False
    )
    completion_unlock_contract = payload[
        "full_goal_completion_unlock_evidence_contract"
    ]
    assert completion_unlock_contract["current_scope_action"] == (
        "define_unlock_evidence_only"
    )
    assert completion_unlock_contract["evidence_namespace"] == (
        "full_goal_unlock_required_evidence_not_current_scope_proof"
    )
    assert completion_unlock_contract["full_goal_completion_claim_allowed_now"] is False
    assert completion_unlock_contract[
        "l1_l6_current_scope_pass_is_sufficient_for_full_goal"
    ] is False
    assert completion_unlock_contract["required_evidence_is_current_scope_proof"] is False
    assert (
        completion_unlock_contract["required_evidence_is_completion_evidence_now"]
        is False
    )
    assert completion_unlock_contract[
        "feature_tickets_are_required_routes_not_evidence"
    ] is True
    assert (
        completion_unlock_contract["required_feature_ticket_is_completion_evidence"]
        is False
    )
    assert (
        completion_unlock_contract[
            "may_satisfy_completion_only_after_approval_and_execution"
        ]
        is True
    )
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
    unlock_evidence = {
        item["id"]: item
        for item in completion_unlock_contract["required_evidence"]
    }
    assert completion_unlock_contract["required_evidence_count"] == len(
        unlock_evidence
    )
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
        status_field = completion_unlock_contract["feature_ticket_resolution_contract"][
            "required_feature_ticket_status_field"
        ]
        assert source_feature_tickets[feature_id][status_field] == (
            completion_unlock_contract["feature_ticket_resolution_contract"][
                "required_feature_ticket_status"
            ]
        )
        target_tokens = set(
            feature_unlock_contract["targets"][feature_id][
                "required_unlock_tokens"
            ]
        )
        assert set(evidence["required_unlock_tokens"]) <= target_tokens, evidence_id
        assert evidence["current_status"] == "deferred", evidence_id
    assert unlock_evidence["RIGHT-ARM-EXECUTION-GATES"]["required_gates"] == [
        "G9",
        "G12",
        "G14",
    ]
    assert payload["contract_design_escalation_boundary"] == {
        "source_boundary_map": (
            "docs/v2/audit/2026-06-12-l1-l6-deferred-feature-coverage.yaml"
        ),
        "current_scope_status": (
            "l5_l6_design_debt_identified_contract_edit_approval_required"
        ),
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
    assert "contract semantics" in payload["contract_design_escalation_boundary"][
        "reason"
    ]
    assert payload["contract_design_escalation_boundary"][
        "design_debt_accountability"
    ]["feature_ticket_is_not_design_substitute"] is True
    assert (
        payload["contract_design_escalation_boundary"]["ticket_id"]
        in feature_tickets
    )
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
        assert (REPO_ROOT / item["path"]).exists(), item["id"]
        assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
        assert not item["path"].startswith("docs/v2/L7-test-design/"), item["id"]
        ticket_text = _read(REPO_ROOT / item["path"])
        assert ticket_text.startswith("---\n"), item["id"]
        ticket_meta = yaml.safe_load(ticket_text.split("---", 2)[1])
        assert ticket_meta["workflow"] == feature_ticket_file_contract[
            "workflow_required"
        ], item["id"]
        assert ticket_meta["status"] == feature_ticket_file_contract[
            "status_required"
        ], item["id"]
        assert ticket_meta["current_task_scope"] in feature_ticket_file_contract[
            "current_task_scope_allowed"
        ], item["id"]
        approval_boundary = ticket_meta.get("approval_boundary", "")
        assert approval_boundary, item["id"]
        for token in feature_ticket_file_contract["approval_boundary_must_contain"]:
            assert token in approval_boundary.lower(), item["id"]
        assert any(
            ticket_meta.get(field) is True
            for field in feature_ticket_file_contract[
                "approval_gate_fields_any_required"
            ]
        ), item["id"]
        assert "complete" not in str(ticket_meta["status"]).lower(), item["id"]
        source_item = source_feature_tickets[item["id"]]
        assert item["path"] == source_item["path"], item["id"]
        assert source_item["status"] == feature_boundary_contract[
            "source_status_required"
        ], item["id"]
        assert source_item["approval_boundary_required"] is feature_boundary_contract[
            "source_approval_boundary_required"
        ], item["id"]
        assert source_item["ticket_is_completion_evidence"] is feature_boundary_contract[
            "source_ticket_completion_evidence_allowed"
        ], item["id"]
        assert source_item["current_task_scope"] in feature_boundary_contract[
            "source_current_task_scope_allowed"
        ], item["id"]
        if source_item.get("layer") == "L7":
            assert source_item.get("approval_required_before_l7_work") is True, item[
                "id"
            ]
    right_arm = payload["right_arm_execution_boundaries"]
    assert right_arm["strict_full_flow_current_overall_clean"] is False
    assert right_arm["strict_full_flow_command"] == (
        "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview "
        "--strict-full-flow --json"
    )
    assert right_arm["strict_full_flow_command_is_read_only"] is True
    expected_deferred_gate_details = {
        "G9": {
            "gate_id": "G9",
            "pair": "L4-L9",
            "source_layer": "L4",
            "target_layer": "L9",
            "target": "G9",
            "required_before_full_goal": "system_test_execution_gate_pass",
            "status": "approved_deferred",
            "clean": True,
            "reason": (
                "execution_gate_not_implemented; semantic_gate_required "
                "coverage=100.0 uncovered=0 orphan=0"
            ),
            "next_action": "implement G9 system-test execution gate",
            "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
        },
        "G12": {
            "gate_id": "G12",
            "pair": "L3-L12",
            "source_layer": "L3",
            "target_layer": "L12",
            "target": "G12",
            "required_before_full_goal": "acceptance_test_execution_gate_pass",
            "status": "approved_deferred",
            "clean": True,
            "reason": "execution_gate_not_implemented coverage=100.0 uncovered=0 orphan=0",
            "next_action": "implement G12 acceptance-test execution gate",
            "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
        },
        "G14": {
            "gate_id": "G14",
            "pair": "L1-L14",
            "source_layer": "L1",
            "target_layer": "L14",
            "target": "G14",
            "required_before_full_goal": "operational_learning_gate_pass",
            "status": "approved_deferred",
            "clean": True,
            "reason": "execution_gate_not_implemented coverage=100.0 uncovered=0 orphan=0",
            "next_action": "implement G14 operational-learning execution gate",
            "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
        },
    }
    assert right_arm["deferred_gate_contract"] == {
        "deferred_gate_ids_must_equal": ["G9", "G12", "G14"],
        "deferred_gate_count": 3,
        "status_required": "approved_deferred",
        "clean_required": True,
        "reason_must_contain": ["execution_gate_not_implemented"],
        "next_action_must_start_with": "implement",
        "reference_required": "HELIX-workflows/helix-process/automation-gate-map.md",
        "gate_details_are_completion_evidence": False,
        "l7_or_right_arm_execution_allowed_by_contract": True,
    }
    deferred_gates = {
        item["gate_id"]: item for item in right_arm["deferred_gates"]
    }
    assert deferred_gates == expected_deferred_gate_details
    assert list(deferred_gates) == right_arm["deferred_gate_contract"][
        "deferred_gate_ids_must_equal"
    ]
    for gate_id, gate in deferred_gates.items():
        assert gate["status"] == right_arm["deferred_gate_contract"][
            "status_required"
        ], gate_id
        assert gate["clean"] is right_arm["deferred_gate_contract"][
            "clean_required"
        ], gate_id
        assert all(
            token in gate["reason"]
            for token in right_arm["deferred_gate_contract"][
                "reason_must_contain"
            ]
        ), gate_id
        assert gate["next_action"].startswith(
            right_arm["deferred_gate_contract"]["next_action_must_start_with"]
        ), gate_id
        assert gate["reference"] == right_arm["deferred_gate_contract"][
            "reference_required"
        ], gate_id
    assert right_arm["deferred_gate_contract"][
        "gate_details_are_completion_evidence"
    ] is False
    assert right_arm["deferred_gate_contract"][
        "l7_or_right_arm_execution_allowed_by_contract"
    ] is True
    for refs in payload["source_audits"].values():
        assert (REPO_ROOT / refs).exists(), refs
    assert payload["completion_denial"]["reason"].startswith(
        "L1-L6 current-scope evidence is pass"
    )


def test_l1_l6_ratification_index_is_read_path_not_l7_work() -> None:
    payload = yaml.safe_load(_read(L1_L6_RATIFICATION_INDEX))
    fr31_trace = yaml.safe_load(_read(L1_L6_FR31_TRACE_MAP))
    double_check = yaml.safe_load(_read(L1_L6_DOUBLE_CHECK_COVERAGE_MAP))
    reference_integrity = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))
    asset_inventory = yaml.safe_load(_read(L1_L6_DESIGN_ASSET_INVENTORY))
    deferred_feature_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    guard_map = yaml.safe_load(_read(L1_L6_CODEX_CLAUDE_GUARD_PARITY_MAP))
    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    harness_pre_adoption = yaml.safe_load(
        _read(HARNESS_PRE_ADOPTION_REQUIREMENTS_ACCEPTANCE_AUDIT)
    )
    web_evidence = yaml.safe_load(_read(L1_L6_WEB_EVIDENCE_SOURCE_MAP))
    full_gap_status = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    exit_criteria = yaml.safe_load(_read(L1_L6_EXIT_CRITERIA_MAP))
    pair_balance = yaml.safe_load(_read(L1_L6_PAIR_BALANCE_MAP))
    improvement_candidates = yaml.safe_load(_read(L1_L6_IMPROVEMENT_CANDIDATE_MAP))
    workflow_automation = yaml.safe_load(_read(L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP))
    governance_coverage = yaml.safe_load(_read(L1_L6_GOVERNANCE_HARDENING_COVERAGE_MAP))
    db_feedback_coverage = yaml.safe_load(_read(L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP))
    dependency_impact = yaml.safe_load(_read(L1_L6_DEPENDENCY_IMPACT_READINESS_COVERAGE_MAP))
    db_registration_readiness = yaml.safe_load(
        _read(L1_L6_DB_REGISTRATION_READINESS_COVERAGE_MAP)
    )
    bottleneck_readiness = yaml.safe_load(
        _read(L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP)
    )
    legacy_classification = yaml.safe_load(
        _read(REPO_ROOT / "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml")
    )
    deferred_feature_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))

    assert payload["schema_version"] == "l1_l6_ratification_index_v1"
    assert payload["status"] == "ratified_l1_l6_current_scope_not_full_goal"
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "ratification_index_is_l7_work": False,
        "ratification_index_is_implementation_evidence": False,
        "l7_test_design_created_by_this_index": False,
        "l7_implementation_done": False,
        "l7_unit_test_execution_done": False,
        "coverage_closure_done": False,
        "helix_db_write_performed": False,
        "schema_migration_done": False,
        "external_tool_installed": False,
        "external_tool_executed": False,
        "ci_or_equivalent_connected": False,
        "full_goal_complete": False,
        "goal_complete_allowed": False,
    }
    assert payload["ratification_summary"] == {
        "current_scope_verdict": "pass_l1_l6_only",
        "full_goal_verdict": "active_not_complete",
        "objective_audit_files_indexed": 1,
        "core_audit_bundle_files_indexed": 23,
        "integrity_audits_indexed": 2,
        "double_check_quantitative_checks_total": 21,
        "double_check_quantitative_checks_pass": 21,
        "double_check_qualitative_checks_total": 36,
        "double_check_qualitative_checks_pass": 36,
        "double_check_blocking_findings_current_scope": 0,
        "evidence_boundary_scan_evidence_like_keys_checked": 11,
        "evidence_boundary_scan_boundary_context_refs": 285,
        "evidence_boundary_scan_negative_boundary_check_refs": 1,
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
        "l1_l6_audit_sources_declared": 13,
        "row_audit_refs_checked": 32,
        "unique_row_audit_refs_checked": 11,
        "undeclared_row_audit_refs": 0,
        "fr31_requirement_count": 31,
        "fr31_all_requirements_have_design_link": True,
        "fr31_all_design_definition_ids_present": True,
        "fr31_missing_downstream_count": 0,
        "fr31_orphan_design_count": 0,
        "fr31_blocking_findings": 0,
        "legacy_reference_files_checked": 4,
        "legacy_reference_files_marked_or_already_marked": 4,
        "legacy_runtime_retrofit_required_items": 1,
        "legacy_runtime_files_with_old_enum_ticketed": 2,
            "legacy_runtime_metadata_gap_ticketed": True,
            "legacy_runtime_feature_ticket_metadata_match_required": True,
            "legacy_runtime_next_action_supersedes_current_json_metadata": True,
            "legacy_runtime_safe_task_retitle_command_available_now": False,
            "legacy_handover_metadata_boundary_items_checked": 1,
            "legacy_handover_current_json_l7_label_authorizes_work": False,
            "legacy_handover_ready_for_review_status_not_completion": True,
            "legacy_handover_next_action_is_authoritative": True,
            "legacy_contract_design_retrofit_required_items": 1,
            "legacy_contract_design_files_with_old_phase_labels_classified": 3,
            "legacy_contract_design_feature_tickets_created": 1,
            "legacy_current_sources_of_truth_checked": 5,
            "legacy_blocking_findings_current_l1_l6_scope": 0,
            "legacy_l7_artifacts_created_by_this_audit": 0,
            "guard_surfaces_checked": 8,
            "guard_parity_status_policies_checked": 5,
            "guard_parity_gap_routes_checked": 8,
            "guard_parity_route_required_fields_checked": 7,
            "parity_finding_normalization_contracts_checked": 8,
            "guard_parity_normalization_required_fields_checked": 8,
            "parity_closure_requirements_checked": 8,
            "guard_parity_closure_required_fields_checked": 6,
            "guard_parity_accountability_current_scope_proves_checked": 4,
            "guard_parity_accountability_current_scope_does_not_prove_checked": 4,
            "guard_parity_classification_rules_checked": 4,
            "guard_parity_adoption_requirements_checked": 4,
            "guard_codex_runtime_evidence_surfaces_checked": 3,
            "guard_l6_design_only_surfaces_checked": 3,
            "guard_future_plan_required_surfaces_checked": 1,
            "guard_blocking_findings_current_scope": 0,
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
            "harness_external_tool_design_layers_checked": 3,
            "harness_external_tool_l6_functions_defined": 10,
            "harness_external_tool_l6_unit_test_viewpoints_defined": 10,
            "harness_external_tool_deferred_feature_entry_points_checked": 1,
            "harness_external_tool_blocking_findings_current_scope": 0,
            "harness_external_tool_l7_artifacts_created_by_this_audit": 0,
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
            "web_evidence_sources_verified": True,
            "web_evidence_official_sources_checked": 33,
            "web_evidence_latest_core_rechecked_sources_checked": 5,
            "web_evidence_all_sources_not_adopted_current_scope": True,
            "web_evidence_l7_or_adoption_evidence_allowed": False,
            "reference_integrity_path_like_refs_checked": 1385,
            "reference_integrity_direct_file_refs_checked": 1376,
            "reference_integrity_audit_files_checked": 25,
            "reference_integrity_glob_patterns_checked": 9,
            "reference_integrity_missing_direct_file_refs": 0,
            "reference_integrity_empty_glob_patterns": 0,
            "design_asset_total_l1_l6_files": 50,
            "design_asset_l1_requirement_files": 5,
            "design_asset_l2_screen_design_files": 1,
            "design_asset_l3_requirement_files": 4,
            "design_asset_l4_basic_design_files": 6,
            "design_asset_l5_detailed_design_files": 6,
            "design_asset_l6_functional_design_files": 28,
            "design_asset_l6_assets_partitioned": True,
            "design_asset_l6_partition_clusters": 3,
            "design_asset_l6_l7_ref_occurrences": 31,
            "design_asset_future_placeholder_targets": 18,
            "design_asset_inventory_uses_l7_as_execution_evidence": False,
            "design_asset_l7_artifacts_created_by_this_inventory": False,
            "grain_balance_current_scope_status": "pass",
        "l1_l6_design_layers_ratified": 6,
        "l1_l6_pair_layers_ratified": 6,
        "pair_contract_matrix_layers_checked": 6,
        "pair_l1_l6_layers_checked": 6,
        "pair_layers_pass": 6,
        "pair_layers_with_waiver": 1,
        "pair_blocking_findings": 0,
        "paired_artifacts_checked": 6,
        "expected_design_refs_checked": 8,
            "expected_design_refs_backed_by_design_assets": 8,
            "expected_design_refs_missing_from_design_assets": 0,
            "pair_l6_unit_test_design_viewpoint_count": 128,
            "fr18_specs_current_scope_l6_closed": 18,
            "fr18_specs_with_draft_status": 0,
            "pair_notes_indexed": 3,
            "improvement_candidates_indexed": 35,
            "improvement_candidates_design_only": 2,
        "improvement_candidates_feature_ticket_only": 33,
        "improvement_candidates_adopted": False,
        "workflow_surfaces_checked": 6,
        "automation_surfaces_checked": 9,
        "automation_trigger_contracts_checked": 9,
        "workflow_db_registry_targets_mapped": 9,
        "workflow_detector_gate_routes_mapped": 7,
        "workflow_cross_audit_convergence_rows_checked": 6,
        "workflow_deferred_feature_entry_points_checked": 7,
        "workflow_parked_feature_entry_points_checked": 0,
        "workflow_blocking_findings_current_scope": 0,
        "workflow_l7_artifacts_created_by_this_audit": 0,
        "governance_surfaces_checked": 8,
        "governance_l6_design_docs_checked": 8,
            "governance_l6_function_contracts_checked": 53,
            "governance_l6_ut_candidate_viewpoints": 44,
            "governance_finding_normalization_contracts_checked": 6,
            "governance_normalization_required_fields_checked": 7,
            "governance_documentation_readiness_gap_patterns_checked": 7,
            "governance_controls_checked": 6,
            "governance_detection_required_route_fields_checked": 7,
            "governance_detection_routes_checked": 6,
            "governance_control_trace_rows_checked": 6,
            "governance_control_closure_rows_checked": 6,
            "governance_preexisting_l7_pair_refs": 2,
        "governance_preexisting_completed_feature_entry_points_checked": 3,
        "governance_deferred_feature_entry_points_checked": 4,
        "governance_blocking_findings_current_scope": 0,
        "governance_l7_artifacts_created_by_this_audit": 0,
        "db_feedback_design_layers_checked": 3,
        "db_feedback_physical_db_design_checked": 1,
        "db_feedback_lifecycle_states_defined": 8,
        "db_feedback_closure_rules_defined": 4,
        "db_feedback_l6_functions_defined": 8,
            "db_feedback_existing_storage_groups_mapped": 6,
            "db_feedback_existing_tables_required_for_lifecycle_checked": 9,
            "db_feedback_forbidden_current_scope_rules_checked": 4,
            "db_feedback_deferred_feature_entry_points_checked": 1,
            "db_feedback_blocking_findings_current_scope": 0,
            "db_feedback_l7_artifacts_created_by_this_audit": 0,
            "db_feedback_accountability_indexed": True,
            "db_feedback_feature_ticket_is_not_design_substitute": True,
            "db_feedback_db_write_requires_explicit_approval": True,
            "db_feedback_current_scope_must_keep_db_write_false": True,
            "db_feedback_recurrence_closure_requires_later_execution_evidence": True,
            "db_feedback_schema_migration_done": False,
            "db_feedback_db_write_connection_done": False,
        "dependency_impact_surfaces_checked": 7,
        "dependency_impact_l6_function_specs_checked": 6,
        "dependency_impact_current_code_surfaces_checked_read_only": 5,
        "dependency_impact_required_output_sections": 9,
        "dependency_impact_db_projection_contracts_checked": 5,
        "dependency_impact_dependency_edge_relations_checked": 7,
        "dependency_impact_scope_route_contracts_checked": 3,
        "dependency_impact_unknown_scope_resolution_rules_checked": 6,
        "dependency_impact_visibility_rows_checked": 9,
        "dependency_impact_output_trace_rows_checked": 9,
        "dependency_impact_deferred_feature_entry_points_checked": 4,
        "dependency_impact_blocking_findings_current_scope": 0,
        "dependency_impact_l7_artifacts_created_by_this_audit": 0,
        "db_registration_events_checked": 6,
        "db_registration_event_contracts_checked": 6,
        "db_registration_document_projection_contracts_checked": 5,
        "db_registration_lifecycle_route_contracts_checked": 6,
        "db_registration_existing_implementation_surfaces_checked": 8,
        "db_registration_l1_l6_design_surfaces_checked": 3,
        "db_registration_readiness_rows": 6,
        "db_registration_event_route_closure_rows_checked": 6,
        "db_registration_add_feature_import_targets_checked": 11,
            "db_registration_blocking_findings_current_scope": 0,
            "db_registration_l7_feature_tickets_created": 1,
            "db_registration_l7_artifacts_created_by_this_audit": 0,
            "db_registration_accountability_indexed": True,
            "db_registration_feature_ticket_is_not_design_substitute": True,
            "db_registration_db_write_requires_explicit_approval": True,
            "db_registration_current_scope_must_keep_db_write_false": True,
            "db_registration_plan_registry_changed_by_this_audit": False,
            "db_registration_helix_db_write_performed": False,
            "db_registration_schema_migration_done": False,
        "bottleneck_signal_sources_checked": 7,
        "bottleneck_l6_function_specs_checked": 5,
        "bottleneck_remediation_flow_states_defined": 7,
        "bottleneck_forbidden_current_scope_states_checked": 2,
        "bottleneck_required_signal_fields_checked": 8,
        "bottleneck_cross_axis_aggregation_contracts_checked": 4,
        "bottleneck_signal_route_contracts_checked": 7,
        "bottleneck_current_code_surfaces_checked_read_only": 5,
        "bottleneck_deferred_feature_entry_points_checked": 4,
        "bottleneck_deferred_feature_boundaries_checked": 4,
        "bottleneck_required_output_sections": 8,
        "bottleneck_blocking_findings_current_scope": 0,
        "bottleneck_l7_artifacts_created_by_this_audit": 0,
        "exit_layers_checked": 6,
        "exit_layers_pass": 6,
        "exit_layers_with_waiver": 1,
        "exit_gate_ids_checked": 6,
        "exit_blocking_findings_current_scope": 0,
        "exit_l7_artifacts_created_by_this_map": 0,
        "deferred_objective_clauses_checked": 9,
        "deferred_entry_points_checked": 11,
        "deferred_feature_tickets_checked": 11,
        "deferred_feature_tickets_indexed": 11,
        "deferred_feature_tickets_draft": 11,
        "deferred_feature_tickets_with_approval_boundary": 11,
        "deferred_feature_unlock_conditions_checked": 11,
        "deferred_repository_add_feature_files_discovered": 26,
        "deferred_current_objective_deferred_feature_tickets": 11,
        "deferred_out_of_current_objective_add_feature_files": 15,
        "deferred_out_of_current_objective_completed_add_features": 4,
        "deferred_out_of_current_objective_parked_feature_tickets": 0,
        "deferred_full_flow_later_phase_approval_boundary": True,
        "deferred_clauses_without_deferred_work": 1,
        "deferred_clauses_mapped_to_feature_ticket": 8,
        "deferred_unmapped_deferred_boundaries": 0,
        "deferred_l7_artifacts_created_by_this_audit": 0,
        "deferred_blocking_findings_current_scope": 0,
        "deferred_design_obligation_rows_checked": 11,
        "deferred_design_obligation_rows_with_prior_l1_l6_design_evidence": 11,
        "deferred_design_obligation_escape_findings": 0,
        "deferred_design_gap_reopen_rules_defined": 11,
        "deferred_escalation_bound_design_tickets_checked": 2,
        "deferred_implementation_or_execution_tickets_checked": 9,
        "harness_pre_adoption_representative_sources_rechecked": 5,
        "harness_pre_adoption_requirement_contracts_checked": 5,
        "harness_pre_adoption_l1_l3_requirement_surfaces_reused": 6,
        "harness_pre_adoption_acceptance_design_obligations_defined": 5,
        "harness_pre_adoption_blocking_findings_current_scope": 0,
        "harness_pre_adoption_l7_artifacts_created_by_this_audit": 0,
        "nfr_derivation_requirements_deriver_signals_checked": 9,
        "nfr_derivation_requirements_deriver_signals_with_l1_or_l3_coverage": 9,
        "nfr_derivation_iso_25010_characteristics_checked": 9,
        "nfr_derivation_iso_25010_characteristics_covered": 9,
        "nfr_derivation_l1_nfr_count": 23,
        "nfr_derivation_l3_nfr_count": 27,
        "nfr_derivation_l3_extension_count": 4,
        "nfr_derivation_l3_rederived_characteristics": 3,
        "nfr_derivation_current_scope_blocking_findings": 0,
        "nfr_derivation_l7_artifacts_created_by_this_audit": 0,
        "reference_integrity_blocking_findings_current_scope": 0,
        "full_goal_unlock_evidence_classes_indexed": 8,
            "full_goal_unlock_required_feature_tickets_resolved": 8,
            "right_arm_execution_gates_deferred": 3,
            "blocking_findings_current_l1_l6_scope": 0,
            "l7_artifacts_created_by_this_index": 0,
            "full_objective_objective_items_checked": 10,
            "full_objective_current_scope_items_pass_l1_l6": 9,
            "full_objective_items_requiring_later_phase_before_full_completion": 8,
            "full_objective_feature_tickets_available": 11,
            "full_objective_repository_add_feature_files_discovered": 26,
            "full_objective_current_objective_deferred_feature_tickets": 11,
            "full_objective_out_of_current_objective_add_feature_files": 15,
            "full_objective_out_of_current_objective_completed_add_features": 4,
            "full_objective_out_of_current_objective_parked_feature_tickets": 0,
            "full_objective_right_arm_execution_gates_deferred": 3,
            "full_objective_blocking_findings_current_l1_l6_scope": 0,
            "full_objective_blocking_findings_full_goal": 8,
            "full_objective_current_scope_verdict": "pass_l1_l6_only",
            "full_objective_full_goal_verdict": "active_not_complete",
        }
    assert payload["ratification_summary"]["double_check_quantitative_checks_total"] == (
        double_check["summary"]["quantitative_checks"]
    )
    assert payload["ratification_summary"]["double_check_quantitative_checks_pass"] == (
        double_check["summary"]["quantitative_checks_pass"]
    )
    assert payload["ratification_summary"]["double_check_qualitative_checks_total"] == (
        double_check["summary"]["qualitative_checks"]
    )
    assert payload["ratification_summary"]["double_check_qualitative_checks_pass"] == (
        double_check["summary"]["qualitative_checks_pass"]
    )
    evidence_boundary_scan = {
        item["id"]: item for item in double_check["qualitative_checks"]
    }["L-EVIDENCE-BOUNDARY-SCAN"]["expected"]
    assert payload["ratification_summary"][
        "evidence_boundary_scan_evidence_like_keys_checked"
    ] == len(evidence_boundary_scan["evidence_like_keys_checked"])
    assert payload["ratification_summary"][
        "evidence_boundary_scan_boundary_context_refs"
    ] == evidence_boundary_scan["boundary_context_refs"]
    assert payload["ratification_summary"][
        "evidence_boundary_scan_negative_boundary_check_refs"
    ] == evidence_boundary_scan["negative_boundary_check_refs"]
    assert payload["ratification_summary"][
        "evidence_boundary_scan_add_feature_or_l7_refs_in_proof_or_evidence"
    ] == evidence_boundary_scan["add_feature_or_l7_refs_in_proof_or_evidence"]
    assert payload["ratification_summary"][
        "evidence_boundary_scan_current_scope_proof_allows_add_feature"
    ] == evidence_boundary_scan["current_scope_proof_allows_add_feature"]
    assert payload["ratification_summary"][
        "evidence_boundary_scan_current_scope_proof_allows_l7_test_design"
    ] == evidence_boundary_scan["current_scope_proof_allows_l7_test_design"]
    assert payload["ratification_summary"]["fr31_requirement_count"] == (
        fr31_trace["summary"]["requirement_count"]
    )
    assert payload["ratification_summary"][
        "fr31_all_requirements_have_design_link"
    ] == fr31_trace["summary"]["all_requirements_have_design_link"]
    assert payload["ratification_summary"][
        "fr31_all_design_definition_ids_present"
    ] == fr31_trace["summary"]["all_design_definition_ids_present"]
    assert payload["ratification_summary"]["fr31_missing_downstream_count"] == len(
        fr31_trace["summary"]["missing_downstream"]
    )
    assert payload["ratification_summary"]["fr31_orphan_design_count"] == len(
        fr31_trace["summary"]["orphan_design"]
    )
    assert payload["ratification_summary"]["fr31_blocking_findings"] == (
        fr31_trace["summary"]["blocking_findings"]
    )
    runtime_retrofit = legacy_classification["runtime_retrofit_required"][0]
    handover_boundary = legacy_classification["handover_metadata_boundary"][0]
    assert payload["ratification_summary"][
        "legacy_reference_files_checked"
    ] == legacy_classification["summary"]["legacy_reference_files_checked"]
    assert payload["ratification_summary"][
        "legacy_reference_files_marked_or_already_marked"
    ] == legacy_classification["summary"][
        "legacy_reference_files_marked_or_already_marked"
    ]
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
    ] == legacy_classification["summary"][
        "handover_current_json_l7_label_authorizes_work"
    ]
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
    assert handover_boundary["current_scope_action"] == (
        "classify_handover_metadata_only_no_runtime_edit"
    )
    assert (
        payload["ratification_summary"]["guard_surfaces_checked"]
        == guard_map["summary"]["guard_surfaces"]
    )
    assert (
        payload["ratification_summary"]["guard_parity_gap_routes_checked"]
        == guard_map["summary"]["parity_gap_routes_checked"]
    )
    assert (
        payload["ratification_summary"][
            "parity_finding_normalization_contracts_checked"
        ]
        == guard_map["summary"]["parity_finding_normalization_contracts_checked"]
    )
    assert (
        payload["ratification_summary"]["parity_closure_requirements_checked"]
        == guard_map["summary"]["parity_closure_requirements_checked"]
    )
    assert (
        payload["ratification_summary"][
            "guard_codex_runtime_evidence_surfaces_checked"
        ]
        == guard_map["summary"]["codex_runtime_evidence_surfaces"]
    )
    assert (
        payload["ratification_summary"]["guard_l6_design_only_surfaces_checked"]
        == guard_map["summary"]["l6_design_only_surfaces"]
    )
    assert (
        payload["ratification_summary"]["guard_future_plan_required_surfaces_checked"]
        == guard_map["summary"]["future_plan_required_surfaces"]
    )
    assert (
        payload["ratification_summary"]["guard_blocking_findings_current_scope"]
        == guard_map["summary"]["blocking_findings_current_scope"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_adoption_recheck_controls_checked"
        ]
        == harness_coverage["summary"]["adoption_recheck_controls_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_pre_adoption_requirement_contracts_checked"
        ]
        == harness_coverage["summary"]["pre_adoption_requirement_contracts_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_current_session_web_fetch_sources_checked"
        ]
        == harness_coverage["summary"]["current_session_web_fetch_sources_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_spot_recheck_sources_checked"
        ]
        == harness_coverage["adoption_recheck_scope_contract"][
            "spot_recheck_sources_checked"
        ]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_spot_recheck_subset_of_canonical"
        ]
        == harness_coverage["adoption_recheck_scope_contract"][
            "spot_recheck_sources_are_subset_of_canonical_source_ids"
        ]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_spot_recheck_not_full_candidate_recheck"
        ]
        == harness_coverage["adoption_recheck_scope_contract"][
            "spot_recheck_is_not_full_candidate_recheck"
        ]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_tool_candidates_checked"
        ]
        == harness_coverage["summary"]["tool_candidates_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_intake_contracts_checked"
        ]
        == harness_coverage["summary"]["tool_intake_contracts_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_admission_gate_contracts_checked"
        ]
        == harness_coverage["summary"]["admission_gate_contracts_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_output_ingestion_contracts_checked"
        ]
        == harness_coverage["summary"]["tool_output_ingestion_contracts_checked"]
    )
    assert (
        payload["ratification_summary"]["harness_external_tool_design_layers_checked"]
        == harness_coverage["summary"]["design_layers_checked"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_l6_functions_defined"
        ]
        == harness_coverage["summary"]["l6_functions_defined"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_l6_unit_test_viewpoints_defined"
        ]
        == harness_coverage["summary"]["l6_unit_test_viewpoints_defined"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_blocking_findings_current_scope"
        ]
        == harness_coverage["summary"]["blocking_findings_current_scope"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_l7_artifacts_created_by_this_audit"
        ]
        == harness_coverage["summary"]["l7_artifacts_created_by_this_audit"]
    )
    harness_accountability = harness_coverage["harness_tool_accountability_contract"]
    assert (
        payload["ratification_summary"][
            "harness_external_tool_accountability_indexed"
        ]
        is True
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_web_evidence_is_design_basis_not_adoption"
        ]
        == harness_accountability["web_evidence_is_design_basis_not_adoption"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_current_scope_must_keep_install_execution_ci_db_false"
        ]
        == harness_accountability[
            "current_scope_must_keep_install_execution_ci_db_false"
        ]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_l7_work_requires_feature_ticket"
        ]
        == harness_accountability["l7_work_requires_feature_ticket"]
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_adoption_or_execution_allowed_now"
        ]
        is False
    )
    assert (
        payload["ratification_summary"]["harness_external_tool_db_write_allowed_now"]
        is False
    )
    assert (
        payload["ratification_summary"][
            "harness_external_tool_ci_or_equivalent_connection_allowed_now"
        ]
        is False
    )
    db_feedback_accountability = db_feedback_coverage[
        "feedback_lifecycle_accountability_contract"
    ]
    assert payload["ratification_summary"]["db_feedback_accountability_indexed"] is True
    assert (
        payload["ratification_summary"][
            "db_feedback_feature_ticket_is_not_design_substitute"
        ]
        == db_feedback_accountability["feature_ticket_is_not_design_substitute"]
    )
    assert (
        payload["ratification_summary"][
            "db_feedback_db_write_requires_explicit_approval"
        ]
        == db_feedback_accountability["db_write_requires_explicit_approval"]
    )
    assert (
        payload["ratification_summary"][
            "db_feedback_current_scope_must_keep_db_write_false"
        ]
        == db_feedback_accountability["current_scope_must_keep_db_write_false"]
    )
    assert (
        payload["ratification_summary"][
            "db_feedback_recurrence_closure_requires_later_execution_evidence"
        ]
        == db_feedback_accountability[
            "recurrence_closure_requires_later_execution_evidence"
        ]
    )
    assert payload["ratification_summary"]["db_feedback_schema_migration_done"] == (
        db_feedback_coverage["boundary"]["schema_migration_done"]
    )
    assert (
        payload["ratification_summary"]["db_feedback_db_write_connection_done"]
        == db_feedback_coverage["boundary"]["db_write_connection_done"]
    )
    db_registration_accountability = db_registration_readiness[
        "registration_accountability_contract"
    ]
    assert (
        payload["ratification_summary"]["db_registration_accountability_indexed"]
        is True
    )
    assert (
        payload["ratification_summary"][
            "db_registration_feature_ticket_is_not_design_substitute"
        ]
        == db_registration_accountability["feature_ticket_is_not_design_substitute"]
    )
    assert (
        payload["ratification_summary"][
            "db_registration_db_write_requires_explicit_approval"
        ]
        == db_registration_accountability["db_write_requires_explicit_approval"]
    )
    assert (
        payload["ratification_summary"][
            "db_registration_current_scope_must_keep_db_write_false"
        ]
        == db_registration_accountability["current_scope_must_keep_db_write_false"]
    )
    assert payload["ratification_summary"][
        "db_registration_plan_registry_changed_by_this_audit"
    ] == db_registration_readiness["boundary"]["plan_registry_changed_by_this_audit"]
    assert payload["ratification_summary"][
        "db_registration_helix_db_write_performed"
    ] == db_registration_readiness["boundary"]["helix_db_write_performed"]
    assert payload["ratification_summary"]["db_registration_schema_migration_done"] == (
        db_registration_readiness["boundary"]["schema_migration_done"]
    )
    assert payload["ratification_summary"]["web_evidence_sources_verified"] == (
        web_evidence["boundary"]["web_sources_verified"]
    )
    assert payload["ratification_summary"]["web_evidence_official_sources_checked"] == (
        web_evidence["web_evidence_freshness_contract"]["official_sources_expected"]
    )
    assert payload["ratification_summary"][
        "web_evidence_latest_core_rechecked_sources_checked"
    ] == len(
        web_evidence["web_evidence_freshness_contract"][
            "latest_core_rechecked_source_ids"
        ]
    )
    assert payload["ratification_summary"][
        "web_evidence_all_sources_not_adopted_current_scope"
    ] == web_evidence["web_evidence_freshness_contract"][
        "all_sources_must_remain_not_adopted_current_scope"
    ]
    assert payload["ratification_summary"][
        "web_evidence_l7_or_adoption_evidence_allowed"
    ] == web_evidence["web_evidence_freshness_contract"][
        "l7_or_adoption_evidence_allowed"
    ]
    assert payload["ratification_summary"][
        "reference_integrity_path_like_refs_checked"
    ] == reference_integrity["summary"]["path_like_refs_checked"]
    assert payload["ratification_summary"][
        "reference_integrity_direct_file_refs_checked"
    ] == reference_integrity["summary"]["direct_file_refs_checked"]
    assert payload["ratification_summary"][
        "reference_integrity_audit_files_checked"
    ] == reference_integrity["summary"]["audit_files_checked"]
    assert payload["ratification_summary"][
        "reference_integrity_glob_patterns_checked"
    ] == reference_integrity["summary"]["glob_patterns_checked"]
    assert payload["ratification_summary"][
        "reference_integrity_missing_direct_file_refs"
    ] == reference_integrity["summary"]["missing_direct_file_refs"]
    assert payload["ratification_summary"][
        "reference_integrity_empty_glob_patterns"
    ] == reference_integrity["summary"]["empty_glob_patterns"]
    summary = payload["ratification_summary"]
    assert summary["design_asset_total_l1_l6_files"] == (
        asset_inventory["asset_counts"]["total_l1_l6_files"]
    )
    assert summary["design_asset_l1_requirement_files"] == (
        asset_inventory["asset_counts"]["l1_requirement_files"]
    )
    assert summary["design_asset_l2_screen_design_files"] == (
        asset_inventory["asset_counts"]["l2_screen_design_files"]
    )
    assert summary["design_asset_l3_requirement_files"] == (
        asset_inventory["asset_counts"]["l3_requirement_files"]
    )
    assert summary["design_asset_l4_basic_design_files"] == (
        asset_inventory["asset_counts"]["l4_basic_design_files"]
    )
    assert summary["design_asset_l5_detailed_design_files"] == (
        asset_inventory["asset_counts"]["l5_detailed_design_files"]
    )
    assert summary["design_asset_l6_functional_design_files"] == (
        asset_inventory["asset_counts"]["l6_functional_design_files"]
    )
    assert summary["design_asset_l6_assets_partitioned"] == (
        asset_inventory["l6_design_clusters"]["partition_policy"][
            "all_l6_assets_partitioned"
        ]
    )
    assert summary["design_asset_l6_partition_clusters"] == len(
        [
            asset_inventory["l6_design_clusters"]["fr_function_specs"],
            asset_inventory["l6_design_clusters"]["detector_and_governance_specs"],
            asset_inventory["l6_design_clusters"]["deferred_extension_specs"],
        ]
    )
    assert summary["design_asset_l6_l7_ref_occurrences"] == (
        asset_inventory["l6_l7_reference_boundary"]["l7_ref_occurrences_in_l6_docs"]
    )
    assert summary["design_asset_future_placeholder_targets"] == (
        asset_inventory["l6_l7_reference_boundary"]["future_placeholder_targets"]
    )
    assert summary["design_asset_inventory_uses_l7_as_execution_evidence"] == (
        asset_inventory["boundary"]["inventory_uses_l7_as_execution_evidence"]
    )
    assert summary["design_asset_l7_artifacts_created_by_this_inventory"] == (
        asset_inventory["boundary"]["l7_test_design_created_by_this_inventory"]
    )
    assert summary["grain_balance_current_scope_status"] == (
        asset_inventory["coverage_evidence"]["grain_balance"][
            "l1_l6_current_scope_status"
        ]
    )
    assert summary["objective_audit_files_indexed"] == len(
        payload["sources"]["objective_audit"]
    )
    assert summary["core_audit_bundle_files_indexed"] == len(
        payload["sources"]["core_audit_bundle"]
    )
    assert summary["integrity_audits_indexed"] == len(
        payload["sources"]["integrity_audits"]
    )
    assert summary["exit_layers_checked"] == exit_criteria["summary"][
        "exit_layers_checked"
    ]
    assert summary["exit_layers_pass"] == exit_criteria["summary"]["exit_layers_pass"]
    assert summary["exit_layers_with_waiver"] == exit_criteria["summary"][
        "exit_layers_with_waiver"
    ]
    assert summary["exit_gate_ids_checked"] == len(
        exit_criteria["summary"]["gate_ids_checked"]
    )
    assert summary["exit_blocking_findings_current_scope"] == exit_criteria[
        "summary"
    ]["blocking_findings_current_scope"]
    assert summary["exit_l7_artifacts_created_by_this_map"] == exit_criteria[
        "summary"
    ]["l7_artifacts_created_by_this_map"]
    assert summary["deferred_objective_clauses_checked"] == (
        deferred_feature_coverage["summary"]["objective_clauses_checked"]
    )
    assert summary["deferred_entry_points_checked"] == (
        deferred_feature_coverage["summary"]["deferred_entry_points_checked"]
    )
    assert summary["deferred_feature_tickets_checked"] == (
        deferred_feature_coverage["summary"]["feature_tickets_checked"]
    )
    assert summary["deferred_feature_tickets_indexed"] == len(
        payload["feature_ticket_boundaries"]
    )
    assert summary["deferred_feature_tickets_draft"] == (
        deferred_feature_coverage["summary"]["feature_tickets_draft"]
    )
    assert summary["deferred_feature_tickets_with_approval_boundary"] == (
        deferred_feature_coverage["summary"][
            "feature_tickets_with_approval_boundary"
        ]
    )
    assert summary["deferred_feature_unlock_conditions_checked"] == (
        deferred_feature_coverage["summary"]["feature_tickets_with_unlock_conditions"]
    )
    assert summary["deferred_repository_add_feature_files_discovered"] == (
        deferred_feature_coverage["summary"]["repository_add_feature_files_discovered"]
    )
    assert summary["deferred_current_objective_deferred_feature_tickets"] == (
        deferred_feature_coverage["summary"]["current_objective_deferred_feature_tickets"]
    )
    assert summary["deferred_out_of_current_objective_add_feature_files"] == (
        deferred_feature_coverage["summary"]["out_of_current_objective_add_feature_files"]
    )
    assert summary["deferred_out_of_current_objective_completed_add_features"] == (
        deferred_feature_coverage["summary"][
            "out_of_current_objective_completed_add_features"
        ]
    )
    assert summary["deferred_out_of_current_objective_parked_feature_tickets"] == (
        deferred_feature_coverage["summary"][
            "out_of_current_objective_parked_feature_tickets"
        ]
    )
    assert summary["deferred_full_flow_later_phase_approval_boundary"] == (
        deferred_feature_coverage["summary"][
            "full_flow_later_phase_approval_boundary"
        ]
    )
    assert summary["deferred_clauses_without_deferred_work"] == (
        deferred_feature_coverage["summary"]["clauses_without_deferred_work"]
    )
    assert summary["deferred_clauses_mapped_to_feature_ticket"] == (
        deferred_feature_coverage["summary"]["clauses_mapped_to_feature_ticket"]
    )
    assert summary["deferred_unmapped_deferred_boundaries"] == (
        deferred_feature_coverage["summary"]["unmapped_deferred_boundaries"]
    )
    assert summary["deferred_l7_artifacts_created_by_this_audit"] == (
        deferred_feature_coverage["summary"]["l7_artifacts_created_by_this_audit"]
    )
    deferred_design_obligation = yaml.safe_load(
        _read(L1_L6_DEFERRED_DESIGN_OBLIGATION_PROOF)
    )
    assert summary["deferred_design_obligation_rows_checked"] == (
        deferred_design_obligation["summary"]["feature_tickets_checked"]
    )
    assert summary[
        "deferred_design_obligation_rows_with_prior_l1_l6_design_evidence"
    ] == deferred_design_obligation["summary"][
        "feature_tickets_with_prior_l1_l6_design_evidence"
    ]
    assert summary["deferred_design_obligation_escape_findings"] == (
        deferred_design_obligation["summary"][
            "feature_tickets_using_ticket_as_design_substitute"
        ]
    )
    assert summary["deferred_design_gap_reopen_rules_defined"] == (
        deferred_design_obligation["summary"]["design_gap_reopen_rules_defined"]
    )
    assert summary["deferred_escalation_bound_design_tickets_checked"] == (
        deferred_design_obligation["summary"]["escalation_bound_design_tickets_checked"]
    )
    assert summary["deferred_implementation_or_execution_tickets_checked"] == (
        deferred_design_obligation["summary"][
            "implementation_or_execution_tickets_checked"
        ]
    )
    assert summary["harness_pre_adoption_representative_sources_rechecked"] == (
        harness_pre_adoption["summary"]["representative_sources_rechecked"]
    )
    assert summary["harness_pre_adoption_requirement_contracts_checked"] == (
        harness_pre_adoption["summary"]["pre_adoption_requirement_contracts_checked"]
    )
    assert summary["harness_pre_adoption_l1_l3_requirement_surfaces_reused"] == (
        harness_pre_adoption["summary"]["l1_l3_requirement_surfaces_reused"]
    )
    assert summary["harness_pre_adoption_acceptance_design_obligations_defined"] == (
        harness_pre_adoption["summary"]["acceptance_design_obligations_defined"]
    )
    assert summary["harness_pre_adoption_blocking_findings_current_scope"] == (
        harness_pre_adoption["summary"]["blocking_findings_current_scope"]
    )
    assert summary["harness_pre_adoption_l7_artifacts_created_by_this_audit"] == (
        harness_pre_adoption["summary"]["l7_artifacts_created_by_this_audit"]
    )
    summary_coverage = payload["summary_coverage_index"]
    assert summary_coverage == {
        "current_scope_action": "prove_source_audit_summary_keys_are_indexed",
        "coverage_index_is_l7_work": False,
        "coverage_index_is_implementation_evidence": False,
        "l7_work_requested_by_user": False,
        "source_summary_maps_checked": 19,
            "source_summary_keys_checked": 219,
        "sources_with_unmapped_summary_keys": 0,
        "unmapped_summary_keys": [],
        "key_mapping_policy": summary_coverage["key_mapping_policy"],
        "coverage_rows": summary_coverage["coverage_rows"],
    }
    mapping_policy = summary_coverage["key_mapping_policy"]
    assert mapping_policy["default_transform"] == "identity"
    assert mapping_policy["already_prefixed_source_key_uses_identity"] is True
    assert mapping_policy["supported_transforms"] == ["identity", "length"]
    mapping_rules = {
        rule["source_id"]: rule for rule in mapping_policy["rules"]
    }
    assert summary_coverage["source_summary_maps_checked"] == len(
        summary_coverage["coverage_rows"]
    )
    assert set(mapping_rules) == {
        row["source_id"] for row in summary_coverage["coverage_rows"]
    }
    source_summary_key_count = 0
    for row in summary_coverage["coverage_rows"]:
        rule = mapping_rules[row["source_id"]]
        source_payload = yaml.safe_load(_read(REPO_ROOT / row["source"]))
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
                ratification_key = (
                    source_key if source_key.startswith(prefix) else f"{prefix}{source_key}"
                )
            expected_value = (
                len(source_value)
                if transforms.get(source_key, mapping_policy["default_transform"]) == "length"
                else source_value
            )
            assert ratification_key in summary, (row["source_id"], source_key)
            assert summary[ratification_key] == expected_value, (
                row["source_id"],
                source_key,
                ratification_key,
            )
    assert summary_coverage["source_summary_keys_checked"] == source_summary_key_count
    assert summary_coverage["sources_with_unmapped_summary_keys"] == 0
    assert summary_coverage["unmapped_summary_keys"] == []
    assert summary["pair_contract_matrix_layers_checked"] == pair_balance["summary"][
        "pair_contract_matrix_layers_checked"
    ]
    assert summary["pair_l1_l6_layers_checked"] == pair_balance["summary"][
        "l1_l6_layers_checked"
    ]
    assert summary["pair_layers_pass"] == pair_balance["summary"]["layers_pass"]
    assert summary["pair_layers_with_waiver"] == pair_balance["summary"][
        "layers_with_waiver"
    ]
    assert summary["paired_artifacts_checked"] == pair_balance["summary"][
        "paired_artifacts_checked"
    ]
    assert summary["expected_design_refs_checked"] == pair_balance["summary"][
        "expected_design_refs_checked"
    ]
    assert summary["expected_design_refs_backed_by_design_assets"] == pair_balance[
        "summary"
    ]["expected_design_refs_backed_by_design_assets"]
    assert summary["expected_design_refs_missing_from_design_assets"] == pair_balance[
        "summary"
    ]["expected_design_refs_missing_from_design_assets"]
    assert summary["pair_l6_unit_test_design_viewpoint_count"] == pair_balance[
        "summary"
    ]["l6_unit_test_design_viewpoint_count"]
    fr18_l6_unit_test_design_index = yaml.safe_load(
        _read(FR18_L6_UNIT_TEST_DESIGN_INDEX)
    )
    assert summary["fr18_specs_current_scope_l6_closed"] == (
        fr18_l6_unit_test_design_index["coverage_summary"][
            "specs_current_scope_l6_closed"
        ]
    )
    assert summary["fr18_specs_with_draft_status"] == len(
        fr18_l6_unit_test_design_index["coverage_summary"]["specs_with_draft_status"]
    )
    assert summary["improvement_candidates_indexed"] == (
        improvement_candidates["candidate_summary"]["total_candidates"]
    )
    assert summary["improvement_candidates_design_only"] == (
        improvement_candidates["candidate_summary"]["current_scope_actions"][
            "design_only"
        ]
    )
    assert summary["improvement_candidates_feature_ticket_only"] == (
        improvement_candidates["candidate_summary"]["current_scope_actions"][
            "feature_ticket_only"
        ]
    )
    assert summary["improvement_candidates_adopted"] == (
        improvement_candidates["boundary"]["candidates_adopted"]
    )
    assert summary["workflow_surfaces_checked"] == (
        workflow_automation["summary"]["workflow_surfaces_checked"]
    )
    assert summary["automation_surfaces_checked"] == (
        workflow_automation["summary"]["automation_surfaces_checked"]
    )
    assert summary["automation_trigger_contracts_checked"] == (
        workflow_automation["summary"]["automation_trigger_contracts_checked"]
    )
    assert summary["workflow_db_registry_targets_mapped"] == (
        workflow_automation["summary"]["db_registry_targets_mapped"]
    )
    assert summary["workflow_detector_gate_routes_mapped"] == (
        workflow_automation["summary"]["detector_gate_routes_mapped"]
    )
    assert summary["workflow_cross_audit_convergence_rows_checked"] == (
        workflow_automation["summary"]["cross_audit_convergence_rows_checked"]
    )
    assert summary["workflow_deferred_feature_entry_points_checked"] == (
        workflow_automation["summary"]["deferred_feature_entry_points_checked"]
    )
    assert summary["workflow_parked_feature_entry_points_checked"] == (
        workflow_automation["summary"]["parked_feature_entry_points_checked"]
    )
    assert summary["workflow_blocking_findings_current_scope"] == (
        workflow_automation["summary"]["blocking_findings_current_scope"]
    )
    assert summary["workflow_l7_artifacts_created_by_this_audit"] == (
        workflow_automation["summary"]["l7_artifacts_created_by_this_audit"]
    )
    assert summary["governance_surfaces_checked"] == (
        governance_coverage["summary"]["governance_surfaces_checked"]
    )
    assert summary["governance_l6_design_docs_checked"] == (
        governance_coverage["summary"]["l6_design_docs_checked"]
    )
    assert summary["governance_l6_function_contracts_checked"] == (
        governance_coverage["summary"]["l6_function_contracts_checked"]
    )
    assert summary["governance_l6_ut_candidate_viewpoints"] == (
        governance_coverage["summary"]["current_scope_l6_ut_candidate_viewpoints"]
    )
    assert summary["governance_finding_normalization_contracts_checked"] == (
        governance_coverage["summary"][
            "governance_finding_normalization_contracts_checked"
        ]
    )
    assert summary["governance_normalization_required_fields_checked"] == (
        governance_coverage["summary"][
            "governance_normalization_required_fields_checked"
        ]
    )
    assert summary["governance_documentation_readiness_gap_patterns_checked"] == (
        governance_coverage["summary"][
            "documentation_readiness_gap_patterns_checked"
        ]
    )
    assert summary["governance_controls_checked"] == (
        governance_coverage["summary"]["governance_controls_checked"]
    )
    assert summary["governance_detection_required_route_fields_checked"] == (
        governance_coverage["summary"][
            "governance_detection_required_route_fields_checked"
        ]
    )
    assert summary["governance_detection_routes_checked"] == (
        governance_coverage["summary"]["governance_detection_routes_checked"]
    )
    assert summary["governance_control_trace_rows_checked"] == (
        governance_coverage["summary"]["governance_control_trace_rows_checked"]
    )
    assert summary["governance_control_closure_rows_checked"] == (
        governance_coverage["summary"]["governance_control_closure_rows_checked"]
    )
    assert summary["governance_preexisting_l7_pair_refs"] == (
        governance_coverage["summary"]["preexisting_l7_pair_refs"]
    )
    assert summary["governance_preexisting_completed_feature_entry_points_checked"] == (
        governance_coverage["summary"][
            "preexisting_completed_feature_entry_points_checked"
        ]
    )
    assert summary["governance_blocking_findings_current_scope"] == (
        governance_coverage["summary"]["blocking_findings_current_scope"]
    )
    assert summary["governance_l7_artifacts_created_by_this_audit"] == (
        governance_coverage["summary"]["l7_artifacts_created_by_this_audit"]
    )
    assert summary["db_feedback_design_layers_checked"] == (
        db_feedback_coverage["summary"]["design_layers_checked"]
    )
    assert summary["db_feedback_physical_db_design_checked"] == (
        db_feedback_coverage["summary"]["physical_db_design_checked"]
    )
    assert summary["db_feedback_lifecycle_states_defined"] == (
        db_feedback_coverage["summary"]["lifecycle_states_defined"]
    )
    assert summary["db_feedback_closure_rules_defined"] == (
        db_feedback_coverage["summary"]["closure_rules_defined"]
    )
    assert summary["db_feedback_l6_functions_defined"] == (
        db_feedback_coverage["summary"]["l6_functions_defined"]
    )
    assert summary["db_feedback_existing_storage_groups_mapped"] == (
        db_feedback_coverage["summary"]["existing_storage_groups_mapped"]
    )
    assert summary["db_feedback_existing_tables_required_for_lifecycle_checked"] == (
        db_feedback_coverage["summary"][
            "existing_tables_required_for_lifecycle_checked"
        ]
    )
    assert summary["db_feedback_forbidden_current_scope_rules_checked"] == (
        db_feedback_coverage["summary"]["forbidden_current_scope_rules_checked"]
    )
    assert summary["db_feedback_blocking_findings_current_scope"] == (
        db_feedback_coverage["summary"]["blocking_findings_current_scope"]
    )
    assert summary["db_feedback_l7_artifacts_created_by_this_audit"] == (
        db_feedback_coverage["summary"]["l7_artifacts_created_by_this_audit"]
    )
    assert summary["dependency_impact_surfaces_checked"] == (
        dependency_impact["summary"]["dependency_impact_surfaces_checked"]
    )
    assert summary["dependency_impact_l6_function_specs_checked"] == (
        dependency_impact["summary"]["l6_function_specs_checked"]
    )
    assert summary["dependency_impact_current_code_surfaces_checked_read_only"] == (
        dependency_impact["summary"]["current_code_surfaces_checked_read_only"]
    )
    assert summary["dependency_impact_required_output_sections"] == (
        dependency_impact["summary"]["required_output_sections"]
    )
    assert summary["dependency_impact_db_projection_contracts_checked"] == (
        dependency_impact["summary"]["db_projection_contracts_checked"]
    )
    assert summary["dependency_impact_dependency_edge_relations_checked"] == (
        dependency_impact["summary"]["dependency_edge_relations_checked"]
    )
    assert summary["dependency_impact_scope_route_contracts_checked"] == (
        dependency_impact["summary"]["impact_scope_route_contracts_checked"]
    )
    assert summary["dependency_impact_unknown_scope_resolution_rules_checked"] == (
        dependency_impact["summary"]["unknown_scope_resolution_rules_checked"]
    )
    assert summary["dependency_impact_visibility_rows_checked"] == (
        dependency_impact["summary"]["impact_visibility_rows_checked"]
    )
    assert summary["dependency_impact_output_trace_rows_checked"] == (
        dependency_impact["summary"]["impact_output_trace_rows_checked"]
    )
    assert summary["dependency_impact_blocking_findings_current_scope"] == (
        dependency_impact["summary"]["blocking_findings_current_scope"]
    )
    assert summary["dependency_impact_l7_artifacts_created_by_this_audit"] == (
        dependency_impact["summary"]["l7_artifacts_created_by_this_audit"]
    )
    assert summary["db_registration_events_checked"] == (
        db_registration_readiness["summary"]["registration_events_checked"]
    )
    assert summary["db_registration_event_contracts_checked"] == (
        db_registration_readiness["summary"]["registration_event_contracts_checked"]
    )
    assert summary["db_registration_document_projection_contracts_checked"] == (
        db_registration_readiness["summary"]["document_projection_contracts_checked"]
    )
    assert summary["db_registration_lifecycle_route_contracts_checked"] == (
        db_registration_readiness["summary"]["lifecycle_route_contracts_checked"]
    )
    assert summary["db_registration_existing_implementation_surfaces_checked"] == (
        db_registration_readiness["summary"]["existing_implementation_surfaces_checked"]
    )
    assert summary["db_registration_l1_l6_design_surfaces_checked"] == (
        db_registration_readiness["summary"]["l1_l6_design_surfaces_checked"]
    )
    assert summary["db_registration_readiness_rows"] == (
        db_registration_readiness["summary"]["readiness_rows"]
    )
    assert summary["db_registration_event_route_closure_rows_checked"] == (
        db_registration_readiness["summary"]["event_route_closure_rows_checked"]
    )
    assert summary["db_registration_add_feature_import_targets_checked"] == (
        db_registration_readiness["summary"]["add_feature_import_targets_checked"]
    )
    assert summary["db_registration_blocking_findings_current_scope"] == (
        db_registration_readiness["summary"]["blocking_findings_current_scope"]
    )
    assert summary["db_registration_l7_feature_tickets_created"] == (
        db_registration_readiness["summary"]["l7_feature_tickets_created"]
    )
    assert summary["db_registration_l7_artifacts_created_by_this_audit"] == (
        db_registration_readiness["summary"]["l7_artifacts_created_by_this_audit"]
    )
    assert summary["bottleneck_signal_sources_checked"] == (
        bottleneck_readiness["summary"]["bottleneck_signal_sources_checked"]
    )
    assert summary["bottleneck_l6_function_specs_checked"] == (
        bottleneck_readiness["summary"]["l6_function_specs_checked"]
    )
    assert summary["bottleneck_remediation_flow_states_defined"] == (
        bottleneck_readiness["summary"]["remediation_flow_states_defined"]
    )
    assert summary["bottleneck_forbidden_current_scope_states_checked"] == (
        bottleneck_readiness["summary"]["forbidden_current_scope_states_checked"]
    )
    assert summary["bottleneck_required_signal_fields_checked"] == (
        bottleneck_readiness["summary"]["required_signal_fields_checked"]
    )
    assert summary["bottleneck_cross_axis_aggregation_contracts_checked"] == (
        bottleneck_readiness["summary"]["cross_axis_aggregation_contracts_checked"]
    )
    assert summary["bottleneck_signal_route_contracts_checked"] == (
        bottleneck_readiness["summary"]["signal_route_contracts_checked"]
    )
    assert summary["bottleneck_current_code_surfaces_checked_read_only"] == (
        bottleneck_readiness["summary"]["current_code_surfaces_checked_read_only"]
    )
    assert summary["bottleneck_deferred_feature_entry_points_checked"] == (
        bottleneck_readiness["summary"]["deferred_feature_entry_points_checked"]
    )
    assert summary["bottleneck_deferred_feature_boundaries_checked"] == (
        bottleneck_readiness["summary"]["deferred_feature_boundaries_checked"]
    )
    assert summary["bottleneck_required_output_sections"] == (
        bottleneck_readiness["summary"]["required_output_sections"]
    )
    assert summary["bottleneck_blocking_findings_current_scope"] == (
        bottleneck_readiness["summary"]["blocking_findings_current_scope"]
    )
    assert summary["bottleneck_l7_artifacts_created_by_this_audit"] == (
        bottleneck_readiness["summary"]["l7_artifacts_created_by_this_audit"]
    )
    full_unlock_index = payload["full_goal_unlock_evidence_index"]
    full_unlock_contract = full_gap_status[
        "full_goal_completion_unlock_evidence_contract"
    ]
    assert full_unlock_index == {
        "source": str(FULL_OBJECTIVE_GAP_STATUS.relative_to(REPO_ROOT)),
        "source_contract": "full_goal_completion_unlock_evidence_contract",
        "current_scope_action": "index_unlock_evidence_only",
        "evidence_namespace": (
            "full_goal_unlock_required_evidence_not_current_scope_proof"
        ),
        "required_evidence_count": 8,
        "required_evidence_is_current_scope_proof": False,
        "required_evidence_is_completion_evidence_now": False,
        "required_feature_tickets_resolved": 8,
        "required_feature_ticket_is_completion_evidence": False,
        "may_satisfy_completion_only_after_approval_and_execution": True,
        "feature_ticket_resolution_source": str(
            L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
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
    assert payload["l1_l6_design_obligation_index"] == {
        "source": str(FULL_OBJECTIVE_GAP_STATUS.relative_to(REPO_ROOT)),
        "proof_source": str(
            L1_L6_DEFERRED_DESIGN_OBLIGATION_PROOF.relative_to(REPO_ROOT)
        ),
        "source_contract": "l1_l6_design_obligation_contract",
        "current_scope_action": (
            "prove_l1_l6_design_obligation_before_deferring_l7_execution"
        ),
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
    assert payload["l1_l6_design_obligation_index"][
        "covered_current_scope_surfaces"
    ] == full_gap_status["l1_l6_design_obligation_contract"][
        "covered_current_scope_surfaces"
    ]
    assert summary["full_goal_unlock_evidence_classes_indexed"] == (
        full_unlock_index["required_evidence_count"]
    )
    assert summary["full_goal_unlock_required_feature_tickets_resolved"] == (
        full_unlock_index["required_feature_tickets_resolved"]
    )
    assert full_unlock_index["required_evidence_count"] == full_unlock_contract[
        "required_evidence_count"
    ]
    assert full_unlock_index["evidence_namespace"] == full_unlock_contract[
        "evidence_namespace"
    ]
    assert full_unlock_index["required_evidence_is_current_scope_proof"] == (
        full_unlock_contract["required_evidence_is_current_scope_proof"]
    )
    assert full_unlock_index["required_evidence_is_completion_evidence_now"] == (
        full_unlock_contract["required_evidence_is_completion_evidence_now"]
    )
    assert full_unlock_index["required_feature_ticket_is_completion_evidence"] == (
        full_unlock_contract["required_feature_ticket_is_completion_evidence"]
    )
    assert full_unlock_index[
        "may_satisfy_completion_only_after_approval_and_execution"
    ] == full_unlock_contract[
        "may_satisfy_completion_only_after_approval_and_execution"
    ]
    assert full_unlock_index["indexed_evidence_ids"] == [
        item["id"] for item in full_unlock_contract["required_evidence"]
    ]
    assert summary["l7_artifacts_created_by_this_index"] == 0
    legacy_classification = (
        "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
    )
    assert legacy_classification in payload["sources"]["core_audit_bundle"]
    ratified_items = {item["id"]: item for item in payload["ratified_l1_l6_items"]}
    assert legacy_classification in ratified_items["RAT-L0-L14-FLOW"]["evidence"]
    assert len(payload["ratified_l1_l6_items"]) == 9
    commands = {item["command"]: item["expected"] for item in payload["verification_commands"]}
    assert commands[
        "python3 -m pytest cli/lib/tests/test_helix_l0_l14_flow_contract.py -q"
    ] == "87 passed"
    assert commands["bats cli/tests/test-helix-l0-l14-flow-contract.bats"] == (
        "56 tests passed"
    )
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
        "deferred_execution_gates": ["G9", "G12", "G14"],
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
                "deferred_execution_gates": ["G9", "G12", "G14"],
            },
            "proves_full_goal_completion": False,
        },
    }
    feature_tickets = {item["id"]: item for item in payload["feature_ticket_boundaries"]}
    assert set(feature_tickets) == {
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
    if full_unlock_index["source_feature_tickets_must_exist_in_index"]:
        for evidence in full_unlock_contract["required_evidence"]:
            assert evidence["required_feature_ticket"] in feature_tickets, evidence[
                "id"
            ]
    l7_doc_prefix = "docs/v2/L7-test-design/"
    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith(l7_doc_prefix), ref
            assert (REPO_ROOT / ref).exists(), ref
    for item in payload["ratified_l1_l6_items"]:
        for ref in item["evidence"]:
            if ref.startswith("helix "):
                continue
            assert not ref.startswith(l7_doc_prefix), item["id"]
            assert (REPO_ROOT / ref).exists(), item["id"]
    for item in feature_tickets.values():
        assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
        assert not item["path"].startswith(l7_doc_prefix), item["id"]
        ticket_path = REPO_ROOT / item["path"]
        assert ticket_path.exists(), item["id"]
        ticket_text = _read(ticket_path)
        assert ticket_text.startswith("---"), item["id"]
        ticket_meta = yaml.safe_load(ticket_text.split("---", 2)[1])
        assert ticket_meta["status"] == item["current_status"] == "draft", item["id"]
        assert ticket_meta.get("current_task_scope") in {
            "feature_ticket_only",
            "L4_L6_design_closed_feature_ticketed",
        }, item["id"]
        assert "approval_boundary" in ticket_meta, item["id"]
        assert "This PLAN is only a ticket" in ticket_meta["approval_boundary"], item[
            "id"
        ]
        if "l7" in item["path"] or "l7" in item["unlocks"].lower():
            assert ticket_meta.get("approval_required_before_l7_work") is True, item[
                "id"
            ]
        else:
            assert "explicit approval" in ticket_meta["approval_boundary"], item["id"]
        assert "complete" not in str(ticket_meta["status"]).lower(), item["id"]
    assert payload["completion_denial"]["reason"].startswith(
        "This index ratifies the current L1-L6 audit bundle only"
    )


def test_l1_l6_exit_criteria_map_ratifies_g1_g6_without_l7_work() -> None:
    payload = yaml.safe_load(_read(L1_L6_EXIT_CRITERIA_MAP))

    assert payload["schema_version"] == "l1_l6_exit_criteria_map_v1"
    assert payload["status"] == "current_scope_l1_l6_exit_criteria_ratified"
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "exit_criteria_map_is_l7_work": False,
        "exit_criteria_map_is_implementation_evidence": False,
        "l7_test_design_created_by_this_map": False,
        "l7_implementation_done": False,
        "helix_db_write_performed": False,
        "external_tool_installed": False,
        "external_tool_executed": False,
        "full_goal_complete": False,
        "goal_complete_allowed": False,
    }
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
    assert [criteria[layer]["exit_gate"] for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]] == [
        "G1",
        "G2",
        "G3",
        "G4",
        "G5",
        "G6",
    ]
    assert payload["summary"]["gate_ids_checked"] == [
        criteria[layer]["exit_gate"] for layer in ["L1", "L2", "L3", "L4", "L5", "L6"]
    ]
    assert criteria["L2"]["verdict"] == "pass_with_waiver"
    assert criteria["L2"]["waiver"] == {
        "reason": "ui_absent",
        "path": "docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md",
    }
    assert criteria["L4"]["verdict"] == "pass_with_monitoring"
    assert criteria["L6"]["verdict"] == "pass"
    assert len(criteria["L6"]["required_artifacts"]) == 19
    assert criteria["L6"]["paired_test_design_artifacts"] == [
        str(FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT))
    ]
    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for item in criteria.values():
        assert item["pass_conditions"], item["layer"]
        for ref in item["required_artifacts"]:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), f"{item['layer']} {ref}"
        for ref in item["paired_test_design_artifacts"]:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), f"{item['layer']} {ref}"
        for ref in item["machine_evidence"]:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), f"{item['layer']} {ref}"
        if item["layer"] == "L2":
            assert item["paired_test_design_artifacts"] == []
            assert item["waiver"]["path"] in item["required_artifacts"]
        else:
            assert item["paired_test_design_artifacts"], item["layer"]
    assert payload["completion_denial"]["reason"].startswith(
        "This map proves G1-G6 exit criteria"
    )


def test_bottleneck_remediation_readiness_maps_signals_without_l7_closure() -> None:
    payload = yaml.safe_load(_read(L1_L6_BOTTLENECK_REMEDIATION_READINESS_COVERAGE_MAP))

    assert payload["schema_version"] == "l1_l6_bottleneck_remediation_readiness_v1"
    assert payload["status"] == (
        "current_scope_l1_l6_bottleneck_remediation_readiness_mapped"
    )
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "bottleneck_map_is_implementation_evidence": False,
        "bottleneck_detector_implemented_by_this_audit": False,
        "remediation_auto_apply_done": False,
        "helix_db_write_performed": False,
        "schema_migration_done": False,
        "external_tool_executed": False,
        "ci_or_equivalent_connected": False,
        "l7_test_design_created_by_this_audit": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
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
        "blocking_findings_current_scope": 0,
        "l7_artifacts_created_by_this_audit": 0,
    }
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
    signals = {item["id"]: item for item in payload["bottleneck_signal_sources"]}
    assert set(signals) == {
        "BTL-SIG-REQ-DRIFT",
        "BTL-SIG-PAIR-BALANCE",
        "BTL-SIG-FULL-FLOW-DEFERRED",
        "BTL-SIG-DB-FEEDBACK",
        "BTL-SIG-DEPENDENCY-IMPACT",
        "BTL-SIG-HARNESS-TOOLS",
        "BTL-SIG-PLAN-REGISTRY",
    }
    assert signals["BTL-SIG-FULL-FLOW-DEFERRED"]["current_scope_status"] == (
        "deferred_not_closure"
    )
    assert all(item["candidate_route"] for item in signals.values())
    route_values = {item["candidate_route"] for item in signals.values()}
    assert any(route.endswith("_feature_ticket") for route in route_values)
    assert "route_bottleneck_candidate" in route_values
    assert all(
        item["current_scope_status"]
        not in {"approved_implementation_executed", "recurrence_closed"}
        for item in signals.values()
    )
    remediation_states = set(payload["remediation_flow"]["states"])
    assert payload["remediation_flow"]["current_scope_terminal_state"] == (
        "feature_ticket_or_plan_materialized"
    )
    assert payload["remediation_flow"]["current_scope_terminal_state"] in (
        remediation_states
    )
    assert payload["remediation_flow"]["forbidden_current_scope_states"] == [
        "approved_implementation_executed",
        "recurrence_closed",
    ]
    assert set(payload["remediation_flow"]["forbidden_current_scope_states"]) <= (
        remediation_states
    )
    assert payload["remediation_flow"]["current_scope_terminal_state"] not in set(
        payload["remediation_flow"]["forbidden_current_scope_states"]
    )
    coverage = {item["id"]: item for item in payload["l6_design_coverage"]}
    assert set(coverage) == {
        "BTL-FN-ROUTE",
        "BTL-FN-LIFECYCLE",
        "BTL-FN-GATE",
        "BTL-FN-IMPACT",
        "BTL-FN-CHANGE-PROPAGATION",
    }
    assert set(payload["sources"]["l6_function_specs"]) == {
        item["artifact"] for item in coverage.values()
    }
    assert "HEXT-FN-07 route_bottleneck_candidate" in coverage["BTL-FN-ROUTE"][
        "covered_functions"
    ]
    assert payload["required_output_contract"] == {
        "signal_id": "required",
        "source_evidence": "required",
        "bottleneck_category": "required",
        "affected_layer_or_pair": "required",
        "impact_scope": "required",
        "candidate_owner": "required",
        "next_plan_or_feature_ticket": "required",
        "completion_boundary": "required",
    }
    assert all(value == "required" for value in payload["required_output_contract"].values())
    classification_policy = payload["signal_classification_policy"]
    assert classification_policy["current_scope_action"] == (
        "classify_and_route_design_only"
    )
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
    assert classification_policy["owner_roles"] == [
        "TL",
        "QA",
        "DevOps",
        "Security",
    ]
    assert "cannot become remediation closure" in classification_policy[
        "closure_policy"
    ]
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
    assert aggregate_contracts["BTL-AGG-REGRESSION-DEPENDENCY"][
        "priority_floor"
    ] == "P0"
    assert aggregate_contracts["BTL-AGG-DOC-CONNECTION"]["aggregate_signal"] == (
        "doc_connection_gap"
    )
    for aggregate in aggregate_contracts.values():
        for field in cross_policy["required_fields"]:
            assert field in aggregate, aggregate["aggregate_id"]
        assert set(aggregate["input_axes"]).issubset(set(cross_policy["allowed_axes"]))
        assert set(aggregate["input_signal_ids"]).issubset(set(signals))
        assert aggregate["aggregate_signal"] in cross_policy[
            "allowed_aggregate_signals"
        ]
        assert aggregate["routed_mode"] in cross_policy["allowed_modes"]
        assert aggregate["priority_floor"] in cross_policy["allowed_priority_floor"]
        assert aggregate["completion_boundary"] == (
            "aggregate_signal_is_not_remediation_closure"
        )
        if aggregate["next_plan_or_feature_ticket"].startswith("docs/plans/add-feature/"):
            assert (REPO_ROOT / aggregate["next_plan_or_feature_ticket"]).exists()
    signal_routes = {
        item["signal_id"]: item for item in payload["signal_route_contract"]
    }
    assert payload["summary"]["signal_route_contracts_checked"] == len(signal_routes)
    assert set(signal_routes) == set(signals)
    assert signal_routes["BTL-SIG-FULL-FLOW-DEFERRED"][
        "next_plan_or_feature_ticket"
    ] == str(FULL_FLOW_REMAINING_GUARDS_FEATURE_PLAN.relative_to(REPO_ROOT))
    assert signal_routes["BTL-SIG-HARNESS-TOOLS"]["candidate_owner"] == "Security"
    for route in signal_routes.values():
        assert all(
            field in route for field in classification_policy["required_signal_fields"]
        ), route["signal_id"]
        assert route["bottleneck_category"] in classification_policy[
            "allowed_categories"
        ], route["signal_id"]
        assert route["impact_scope"] in classification_policy[
            "allowed_impact_scope"
        ], route["signal_id"]
        assert route["candidate_owner"] in classification_policy["owner_roles"]
        assert route["completion_boundary"].endswith(
            ("not_closure", "not_done", "not_implemented", "before_execution")
        ), route["signal_id"]
        signal = signals[route["signal_id"]]
        if route["next_plan_or_feature_ticket"].startswith("docs/plans/add-feature/"):
            assert (REPO_ROOT / route["next_plan_or_feature_ticket"]).exists(), route[
                "signal_id"
            ]
        else:
            assert route["next_plan_or_feature_ticket"] == signal["candidate_route"]
    feature_boundaries = {
        item["id"]: item for item in payload["deferred_feature_boundaries"]
    }
    assert set(feature_boundaries) == {
        "db_evidence_lifecycle",
        "harness_external_tools",
        "full_flow_remaining_guards",
        "bottleneck_routing",
    }
    assert feature_boundaries["db_evidence_lifecycle"]["unlocks"] == [
        "document auto-registration projection",
        "bottleneck candidate persistence",
        "feedback loop candidate persistence",
        "recurrence closure evidence",
    ]
    assert set(payload["sources"]["deferred_feature_entry_points"]) == {
        item["path"] for item in feature_boundaries.values()
    }
    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for ref in payload["sources"]["current_code_surfaces_read_only"]:
        assert ref.startswith("cli/lib/"), ref
        assert (REPO_ROOT / ref).exists(), ref
    for signal in signals.values():
        assert (REPO_ROOT / signal["current_l1_l6_evidence"]).exists(), signal["id"]
    for item in coverage.values():
        artifact = REPO_ROOT / item["artifact"]
        assert artifact.exists(), item["id"]
        artifact_text = artifact.read_text(encoding="utf-8")
        for function_ref in item["covered_functions"]:
            searchable_tokens = [
                token.strip("`")
                for token in re.split(r"[\s/\-]+", function_ref)
                if len(token.strip("`")) > 2
            ]
            assert any(token in artifact_text for token in searchable_tokens), (
                item["id"],
                function_ref,
            )
    for item in feature_boundaries.values():
        assert item["path"].startswith("docs/plans/add-feature/"), item["id"]
        assert (REPO_ROOT / item["path"]).exists(), item["id"]
        assert item["unlocks"], item["id"]
    invariant_text = "\n".join(payload["invariants"])
    assert "candidate is not remediation closure" in invariant_text
    assert "must not be auto-applied" in invariant_text
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves L1-L6 bottleneck remediation readiness only"
    )


def test_double_check_coverage_map_aggregates_quantitative_and_qualitative_pass() -> None:
    payload = yaml.safe_load(_read(L1_L6_DOUBLE_CHECK_COVERAGE_MAP))
    reference_integrity = yaml.safe_load(_read(L1_L6_REFERENCE_INTEGRITY_COVERAGE_MAP))
    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    improvement_map = yaml.safe_load(_read(L1_L6_IMPROVEMENT_CANDIDATE_MAP))
    deferred_feature_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
    legacy_classification = yaml.safe_load(
        _read(REPO_ROOT / "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml")
    )

    assert payload["schema_version"] == "l1_l6_double_check_coverage_v1"
    assert payload["status"] == (
        "current_scope_l1_l6_quantitative_and_qualitative_check_pass"
    )
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "double_check_map_is_implementation_evidence": False,
        "quantitative_pass_is_full_completion": False,
        "qualitative_pass_is_full_completion": False,
        "l7_implementation_done": False,
        "external_tool_installed": False,
        "schema_migration_done": False,
        "ci_or_equivalent_connected": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
        "quantitative_checks": 21,
        "quantitative_checks_pass": 21,
        "qualitative_checks": 36,
        "qualitative_checks_pass": 36,
        "blocking_findings_current_scope": 0,
        "current_scope_verdict": "pass_l1_l6_only",
    }

    quantitative = {item["id"]: item for item in payload["quantitative_checks"]}
    qualitative = {item["id"]: item for item in payload["qualitative_checks"]}
    assert payload["summary"]["quantitative_checks"] == len(quantitative)
    assert payload["summary"]["quantitative_checks_pass"] == sum(
        1 for item in quantitative.values() if item["verdict"] == "pass"
    )
    assert payload["summary"]["qualitative_checks"] == len(qualitative)
    assert payload["summary"]["qualitative_checks_pass"] == sum(
        1 for item in qualitative.values() if item["verdict"] == "pass"
    )
    source_groups = set(payload["sources"]["objective_audit"])
    source_groups.update(payload["sources"]["quantitative_sources"])
    source_groups.update(payload["sources"]["qualitative_sources"])
    used_sources = {
        item["source"] for item in list(quantitative.values()) + list(qualitative.values())
    }
    assert used_sources == source_groups
    assert all(
        not ref.startswith("docs/v2/L7-test-design/")
        for refs in payload["sources"].values()
        for ref in refs
    )

    assert set(quantitative) == {
        "Q-L0-L14-FLOW-SURFACE",
        "Q-L0-PLANNING-DERIVATION",
        "Q-REQ-TRACE",
        "Q-ASSET-INVENTORY",
        "Q-L6-ASSET-PARTITION",
        "Q-PAIR-BALANCE",
        "Q-DEFERRED-FEATURES",
        "Q-DEFERRED-DESIGN-OBLIGATION",
        "Q-DB-FEEDBACK",
        "Q-HARNESS-TOOLS",
        "Q-GOVERNANCE",
        "Q-WORKFLOW-AUTOMATION",
        "Q-DB-REGISTRATION-READINESS",
        "Q-DEPENDENCY-IMPACT-READINESS",
        "Q-BOTTLENECK-REMEDIATION-READINESS",
        "Q-FULL-OBJECTIVE-GAP-STATUS",
        "Q-RATIFICATION-INDEX",
        "Q-EXIT-CRITERIA",
        "Q-REFERENCE-INTEGRITY",
        "Q-IMPROVEMENT-CANDIDATES",
        "Q-CONTRACT-TESTS",
    }
    assert all(item["verdict"] == "pass" for item in quantitative.values())
    assert quantitative["Q-L0-L14-FLOW-SURFACE"]["expected"] == {
        "layers_checked": 15,
        "left_arm_design_layers_checked": 6,
        "right_arm_execution_or_verification_layers_checked": 7,
        "current_surfaces_checked": 90,
        "banned_legacy_terms_found_current_surfaces": 0,
        "l7_implementation_done": False,
        "goal_complete_allowed": False,
    }
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
    l0_derivation = yaml.safe_load(_read(L0_PLANNING_DERIVATION_COVERAGE_MAP))
    assert quantitative["Q-L0-PLANNING-DERIVATION"]["expected"][
        "l0_problem_axes_checked"
    ] == l0_derivation["summary"]["l0_problem_axes_checked"]
    assert quantitative["Q-L0-PLANNING-DERIVATION"]["expected"][
        "l0_target_areas_checked"
    ] == l0_derivation["summary"]["l0_target_areas_checked"]
    declared_l1_l6_audits = set(l0_derivation["sources"]["l1_l6_audits"])
    allowed_external_audits = set(
        l0_derivation["source_coverage_contract"]["allowed_external_audit_sources"]
    )
    row_audit_refs = []
    for row in l0_derivation["problem_axis_rows"]:
        row_audit_refs.extend(row["audit_evidence"])
    for row in l0_derivation["target_area_rows"]:
        row_audit_refs.extend(
            ref for ref in row["evidence"] if ref.startswith("docs/v2/audit/")
        )
    undeclared_row_audits = sorted(
        set(row_audit_refs) - declared_l1_l6_audits - allowed_external_audits
    )
    assert l0_derivation["summary"]["l1_l6_audit_sources_declared"] == len(
        declared_l1_l6_audits
    )
    assert l0_derivation["summary"]["row_audit_refs_checked"] == len(
        row_audit_refs
    )
    assert l0_derivation["summary"]["unique_row_audit_refs_checked"] == len(
        set(row_audit_refs)
    )
    assert l0_derivation["summary"]["undeclared_row_audit_refs"] == len(
        undeclared_row_audits
    )
    assert undeclared_row_audits == []
    problem_axis_rows = l0_derivation["problem_axis_rows"]
    target_area_rows = l0_derivation["target_area_rows"]
    assert l0_derivation["summary"][
        "problem_axis_rows_with_mapped_requirements"
    ] == sum(1 for row in problem_axis_rows if row["mapped_l3_requirements"])
    assert l0_derivation["summary"][
        "problem_axis_rows_with_l4_l6_design_evidence"
    ] == sum(1 for row in problem_axis_rows if row["l4_l6_design_evidence"])
    assert l0_derivation["summary"]["problem_axis_rows_with_audit_evidence"] == sum(
        1 for row in problem_axis_rows if row["audit_evidence"]
    )
    assert l0_derivation["summary"][
        "target_area_rows_with_current_scope_evidence"
    ] == sum(1 for row in target_area_rows if row["evidence"])
    assert l0_derivation["summary"]["rows_with_current_scope_result"] == sum(
        1
        for row in problem_axis_rows + target_area_rows
        if row["current_scope_result"] == "covered_l1_l6_design_only"
    )
    assert l0_derivation["derivation_invariants"][
        "all_problem_axes_have_mapped_requirements"
    ] is True
    assert l0_derivation["derivation_invariants"][
        "all_problem_axes_have_l4_l6_design_evidence"
    ] is True
    assert l0_derivation["derivation_invariants"][
        "all_problem_axes_have_audit_evidence"
    ] is True
    assert l0_derivation["derivation_invariants"][
        "all_target_areas_have_current_scope_evidence"
    ] is True
    assert l0_derivation["derivation_invariants"][
        "l7_or_later_phase_evidence_used_for_current_scope"
    ] is False
    assert quantitative["Q-REQ-TRACE"]["expected"]["requirements"] == 31
    assert quantitative["Q-L6-ASSET-PARTITION"]["expected"] == {
        "l6_assets_partitioned": True,
        "l6_partition_overlap_allowed": False,
        "l6_partition_clusters": 3,
        "fr_function_specs": 18,
        "detector_and_governance_specs": 7,
        "deferred_extension_specs": 3,
    }
    assert quantitative["Q-PAIR-BALANCE"]["expected"][
        "l6_unit_test_design_viewpoint_count"
    ] == 128
    assert quantitative["Q-PAIR-BALANCE"]["expected"][
        "expected_design_refs_missing_from_design_assets"
    ] == 0
    assert quantitative["Q-HARNESS-TOOLS"]["expected"] == {
        "official_sources_checked": harness_coverage["summary"][
            "official_sources_checked"
        ],
        "tool_candidates_checked": harness_coverage["summary"][
            "tool_candidates_checked"
        ],
        "tool_intake_contracts_checked": harness_coverage["summary"][
            "tool_intake_contracts_checked"
        ],
        "tool_intake_required_fields_checked": harness_coverage["summary"][
            "tool_intake_required_fields_checked"
        ],
        "tool_intake_forbidden_common_rules_checked": harness_coverage["summary"][
            "tool_intake_forbidden_common_rules_checked"
        ],
        "admission_gate_contracts_checked": harness_coverage["summary"][
            "admission_gate_contracts_checked"
        ],
        "admission_gate_required_fields_checked": harness_coverage["summary"][
            "admission_gate_required_fields_checked"
        ],
        "admission_owner_roles_checked": harness_coverage["summary"][
            "admission_owner_roles_checked"
        ],
        "tool_output_ingestion_contracts_checked": harness_coverage["summary"][
            "tool_output_ingestion_contracts_checked"
        ],
        "tool_output_required_fields_checked": harness_coverage["summary"][
            "tool_output_required_fields_checked"
        ],
        "tool_output_detector_signals_checked": harness_coverage["summary"][
            "tool_output_detector_signals_checked"
        ],
        "l6_functions_defined": harness_coverage["summary"]["l6_functions_defined"],
        "l6_unit_test_viewpoints_defined": harness_coverage["summary"][
            "l6_unit_test_viewpoints_defined"
        ],
            "adoption_recheck_controls_checked": harness_coverage["summary"][
                "adoption_recheck_controls_checked"
            ],
            "pre_adoption_requirement_contracts_checked": harness_coverage["summary"][
                "pre_adoption_requirement_contracts_checked"
            ],
            "current_session_web_fetch_sources_checked": harness_coverage["summary"][
                "current_session_web_fetch_sources_checked"
            ],
            "current_session_web_fetch_refs_checked": harness_coverage["summary"][
                "current_session_web_fetch_refs_checked"
            ],
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
    assert quantitative["Q-GOVERNANCE"]["expected"][
        "governance_finding_normalization_contracts_checked"
    ] == 6
    assert quantitative["Q-CONTRACT-TESTS"]["expected"]["pytest_expected"] == (
        "87 passed"
    )
    assert quantitative["Q-CONTRACT-TESTS"]["expected"]["bats_expected"] == (
        "56 tests passed"
    )
    assert quantitative["Q-EXIT-CRITERIA"]["expected"]["exit_layers_pass"] == 6
    assert quantitative["Q-RATIFICATION-INDEX"]["expected"][
        "full_goal_verdict"
    ] == "active_not_complete"
    assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"][
        "automation_surfaces_checked"
    ] == 9
    assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"][
        "automation_trigger_contracts_checked"
    ] == 9
    assert quantitative["Q-WORKFLOW-AUTOMATION"]["expected"][
        "cross_audit_convergence_rows_checked"
    ] == 6
    assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"][
        "plan_registry_changed_by_this_audit"
    ] is False
    assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"][
        "registration_event_contracts_checked"
    ] == 6
    assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"][
        "document_projection_contracts_checked"
    ] == 5
    assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"][
        "lifecycle_route_contracts_checked"
    ] == 6
    assert quantitative["Q-DB-REGISTRATION-READINESS"]["expected"][
        "event_route_closure_rows_checked"
    ] == 6
    assert quantitative["Q-DEPENDENCY-IMPACT-READINESS"]["expected"][
        "impact_query_cli_implemented"
    ] is False
    assert quantitative["Q-DEPENDENCY-IMPACT-READINESS"]["expected"][
        "impact_scope_route_contracts_checked"
    ] == 3
    assert quantitative["Q-DEPENDENCY-IMPACT-READINESS"]["expected"][
        "unknown_scope_resolution_rules_checked"
    ] == 6
    assert quantitative["Q-BOTTLENECK-REMEDIATION-READINESS"]["expected"][
        "remediation_auto_apply_done"
    ] is False
    assert quantitative["Q-BOTTLENECK-REMEDIATION-READINESS"]["expected"][
        "cross_axis_aggregation_contracts_checked"
    ] == 4
    assert quantitative["Q-REFERENCE-INTEGRITY"]["expected"] == {
        "audit_files_checked": reference_integrity["summary"]["audit_files_checked"],
        "path_like_refs_checked": reference_integrity["summary"][
            "path_like_refs_checked"
        ],
        "direct_file_refs_checked": reference_integrity["summary"][
            "direct_file_refs_checked"
        ],
        "glob_patterns_checked": reference_integrity["summary"][
            "glob_patterns_checked"
        ],
        "missing_direct_file_refs": 0,
        "empty_glob_patterns": 0,
    }
    assert quantitative["Q-FULL-OBJECTIVE-GAP-STATUS"]["expected"][
        "full_goal_verdict"
    ] == "active_not_complete"
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
    assert full_objective_expected[
        "out_of_current_objective_completed_add_features"
    ] == deferred_feature_coverage["summary"][
        "out_of_current_objective_completed_add_features"
    ]
    assert full_objective_expected[
        "out_of_current_objective_parked_feature_tickets"
    ] == deferred_feature_coverage["summary"][
        "out_of_current_objective_parked_feature_tickets"
    ]
    assert quantitative["Q-IMPROVEMENT-CANDIDATES"]["expected"] == {
        "total_candidates": improvement_map["candidate_summary"]["total_candidates"],
        "candidates_adopted": False,
    }

    assert set(qualitative) == {
        "L-BOUNDARY-L7",
        "L-NO-COMPLETION-CLAIM",
        "L-PAIR-SEMANTIC",
        "L-DOC-REVIEW-4C-GRAIN",
        "L-UI-WAIVER",
        "L-CANDIDATE-NOT-ADOPTION",
        "L-WEB-EVIDENCE-ONLY",
        "L-WEB-EVIDENCE-FRESHNESS",
        "L-CONTRACT-DESIGN-WEB-EVIDENCE-SEPARATION",
        "L-CODEX-CLAUDE-PARITY",
        "L-CODEX-CLAUDE-PARITY-ROUTES",
        "L-DB-SAFETY",
        "L-HARNESS-SAFETY",
        "L-HARNESS-ADOPTION-RECHECK",
        "L-HARNESS-CURRENT-SESSION-WEBFETCH-NOT-CLOSURE",
        "L-GOVERNANCE-SAFETY",
        "L-PLAN-REGISTRY-ADD-FEATURE-GAP",
        "L-AUDIT-MANIFEST-PROJECTION",
        "L-DEPENDENCY-IMPACT-NOT-CLOSURE",
        "L-BOTTLENECK-REMEDIATION-NOT-CLOSURE",
        "L-FULL-OBJECTIVE-ACTIVE",
        "L-FEATURE-TICKET-FRONTMATTER",
        "L-FEATURE-TICKET-UNLOCK-CONDITIONS",
        "L-CONTRACT-DESIGN-ESCALATION-BOUNDARY",
        "L-HANDOVER-BOUNDARY",
        "L-RATIFICATION-NOT-CLOSURE",
        "L-FULL-GOAL-UNLOCK-EVIDENCE-INDEX",
        "L-FULL-GOAL-UNLOCK-FEATURE-TICKET-RESOLUTION",
        "L-FULL-GOAL-UNLOCK-NAMESPACE-NOT-PROOF",
        "L-L1-L6-DESIGN-OBLIGATION-NOT-FEATURE-ESCAPE",
        "L-DEFERRED-DESIGN-OBLIGATION-PROOF",
        "L-EXIT-CRITERIA-NOT-CLOSURE",
        "L-LEGACY-REFERENCE-CLASSIFICATION",
        "L-EVIDENCE-BOUNDARY-SCAN",
        "L-AUDIT-BOUNDARY-FLAGS",
        "L-AUDIT-YAML-DUPLICATE-KEYS",
    }
    assert all(item["verdict"] == "pass" for item in qualitative.values())
    assert qualitative["L-DOC-REVIEW-4C-GRAIN"]["expected"] == {
        "correctness": "pass",
        "completeness": "pass",
        "consistency": "pass",
        "clarity": "pass",
        "l7_completion_evidence": False,
    }
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
        _read(REPO_ROOT / runtime_retrofit["feature_ticket"]).split("---", 2)[1]
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
    ] == legacy_classification["summary"][
        "handover_current_json_l7_label_authorizes_work"
    ]
    assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
        "handover_ready_for_review_status_not_completion"
    ] == legacy_classification["summary"][
        "handover_ready_for_review_status_not_completion"
    ]
    assert qualitative["L-LEGACY-REFERENCE-CLASSIFICATION"]["expected"][
        "handover_next_action_is_authoritative"
    ] == legacy_classification["summary"]["handover_next_action_is_authoritative"]
    assert handover_boundary["observed_machine_state"][
        "task_title_contains_l7"
    ] is True
    assert handover_boundary["authoritative_boundary"]["l7_work_requested_by_user"] is False
    assert handover_boundary["authoritative_boundary"][
        "next_action_supersedes_current_json_task_metadata"
    ] is True
    assert "l7_implementation" in handover_boundary["forbidden_in_current_scope"]
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
        "current_json_legacy_task_title": runtime_retrofit[
            "observed_metadata_gap"
        ]["current_json_legacy_task_title_possible"],
        "current_json_legacy_phase_label": runtime_retrofit[
            "observed_metadata_gap"
        ]["current_json_legacy_phase_label_possible"],
        "task_retitle_update_command_available_now": runtime_retrofit[
            "observed_metadata_gap"
        ]["safe_task_retitle_command_available_now"],
        "next_action_must_remain_authoritative": runtime_retrofit[
            "observed_metadata_gap"
        ]["next_action_supersedes_current_json_task_metadata"],
        "force_dump_required_for_retitle_without_runtime_change": True,
        "force_dump_allowed_without_approval": runtime_retrofit[
            "observed_metadata_gap"
        ]["force_dump_without_approval_allowed"],
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
    assert qualitative[
        "L-FULL-GOAL-UNLOCK-FEATURE-TICKET-RESOLUTION"
    ]["expected"] == {
        "full_goal_unlock_required_feature_tickets_resolved": 8,
        "feature_ticket_resolution_source": str(
            L1_L6_DEFERRED_FEATURE_COVERAGE_MAP.relative_to(REPO_ROOT)
        ),
        "feature_ticket_resolution_contract": "full_goal_completion_unlock_evidence_contract.feature_ticket_resolution_contract",
        "feature_tickets_are_routes_not_evidence": True,
        "l7_execution_allowed_by_resolution": False,
    }
    assert qualitative["L-FULL-GOAL-UNLOCK-NAMESPACE-NOT-PROOF"][
        "expected"
    ] == {
        "evidence_namespace": (
            "full_goal_unlock_required_evidence_not_current_scope_proof"
        ),
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
    assert qualitative[
        "L-HARNESS-CURRENT-SESSION-WEBFETCH-NOT-CLOSURE"
    ]["expected"] == {
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
    assert qualitative[
        "L-L1-L6-DESIGN-OBLIGATION-NOT-FEATURE-ESCAPE"
    ]["expected"] == {
        "current_scope_action": (
            "prove_l1_l6_design_obligation_before_deferring_l7_execution"
        ),
        "l1_l6_design_obligation_is_current_scope": True,
        "deferred_feature_tickets_are_not_design_substitute": True,
        "feature_ticket_allowed_only_for_unapproved_l7_or_escalation_bound_execution": True,
        "l1_l6_design_assets_required_before_ticket": True,
        "design_gap_reopened_if_l1_l6_evidence_missing": True,
        "no_feature_escape_for_design_debt": True,
        "l7_or_external_execution_requires_approved_feature_ticket": True,
        "covered_current_scope_surfaces": 6,
    }
    grain_text = _read(L1_L6_GRAIN_BALANCE_AUDIT)
    for term in (
        "Correctness",
        "Completeness",
        "Consistency",
        "Clarity",
        "L7 実装、L7 単体テスト設計、DB write",
    ):
        assert term in grain_text
    assert qualitative["L-AUDIT-MANIFEST-PROJECTION"]["expected"] == {
        "doc_kind": "audit_manifest",
        "db_target": "detector_report",
        "required_key": "completion_denial",
        "missing_completion_denial": [],
        "completion_guard": "projection_contract_is_not_db_write",
        "helix_db_write_performed": False,
    }
    missing_completion_denial = []
    current_audit_paths = [
        REPO_ROOT / ref for ref in reference_integrity["sources"]["audit_bundle"]
    ]
    for audit_path in sorted(current_audit_paths):
        audit_payload = yaml.safe_load(_read(audit_path))
        if not isinstance(audit_payload.get("completion_denial"), dict):
            missing_completion_denial.append(str(audit_path.relative_to(REPO_ROOT)))
    assert missing_completion_denial == []
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
        nonlocal boundary_refs, evidence_refs, negative_boundary_check_refs
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

    current_audit_paths = [
        REPO_ROOT / ref for ref in reference_integrity["sources"]["audit_bundle"]
    ]
    assert any(
        str(path.relative_to(REPO_ROOT))
        == "docs/v2/audit/2026-06-13-l1-l6-legacy-reference-classification.yaml"
        for path in current_audit_paths
    )

    for audit_path in sorted(current_audit_paths):
        walk_boundary_refs(yaml.safe_load(_read(audit_path)), [])

    boundary_scan_expected = qualitative["L-EVIDENCE-BOUNDARY-SCAN"]["expected"]
    assert boundary_scan_expected == {
        "evidence_key_match_policy": "exact_key_or_known_evidence_like_key",
        "evidence_like_keys_checked": evidence_like_keys,
        "boundary_context_refs": boundary_scan_expected["boundary_context_refs"],
        "negative_boundary_check_refs": negative_boundary_check_refs,
        "evidence_context_refs": evidence_refs,
        "add_feature_or_l7_refs_in_proof_or_evidence": evidence_refs,
        "current_scope_proof_allows_add_feature": False,
        "current_scope_proof_allows_l7_test_design": False,
    }
    assert boundary_scan_expected["boundary_context_refs"] in {boundary_refs, boundary_refs - 1}
    assert negative_boundary_check_refs == 1
    assert evidence_refs == 0
    assert qualitative["L-AUDIT-BOUNDARY-FLAGS"]["expected"] == {
        "yaml_audits_checked": len(
            current_audit_paths
        ),
        "audit_selection_policy": "reference_integrity_audit_bundle",
        "required_common_boundary_keys": [
            "l7_work_requested_by_user",
            "l7_work_requires_feature_ticket",
            "goal_complete_allowed",
        ],
        "missing_boundary_or_scope_boundary": [],
        "missing_common_boundary_keys": [],
        "dangerous_boundary_flags_true": [],
        "true_boundary_flags_allowed": [
            "l7_work_requires_feature_ticket",
            "web_sources_verified",
        ],
    }
    assert qualitative["L-AUDIT-YAML-DUPLICATE-KEYS"]["expected"] == {
        "yaml_audits_checked": len(
            current_audit_paths
        ),
        "audit_selection_policy": "reference_integrity_audit_bundle",
        "duplicate_yaml_keys": [],
        "parser": "yaml.compose",
    }
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
    assert qualitative["L-CONTRACT-DESIGN-WEB-EVIDENCE-SEPARATION"][
        "expected"
    ] == {
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
    deferred_feature_coverage = yaml.safe_load(_read(L1_L6_DEFERRED_FEATURE_COVERAGE_MAP))
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
            "forbidden_now_count": 8,
            "forbidden_now": [
                "L7 product feature implementation",
                "L7 product coverage closure",
                "product behavior or product requirement changes outside right-arm execution-gate closure",
                "write/adopt HELIX DB state",
                "D-API/D-DB/D-CONTRACT semantic changes or schema migration",
                "install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate",
                "broad advisory→fail-close flip of W1 detectors",
                "treating PLAN materialization or gate implementation alone as full-goal completion evidence",
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
    full_objective_gap_status = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    assert full_objective_gap_status["latest_user_boundary"] == {
        "l7_requested_now": False,
        "l7_route": "add_feature_ticket_only",
        "current_allowed_work": (
            "Sequential right-arm execution-gate closure via add-feature tickets, starting with G8 L5-L8 integration-test execution gate. This includes gate/subcheck/vg_overview verdict wiring, test-code anchors, execution evidence, and bounded detector/ledger synchronization required to remove the corresponding strict-full-flow deferred_pair only.\n"
        ),
        "forbidden_now": [
            "L7 product feature implementation",
            "L7 product coverage closure",
            "product behavior or product requirement changes outside right-arm execution-gate closure",
            "write/adopt HELIX DB state",
            "D-API/D-DB/D-CONTRACT semantic changes or schema migration",
            "install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate",
            "broad advisory→fail-close flip of W1 detectors",
            "treating PLAN materialization or gate implementation alone as full-goal completion evidence",
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
        "right_arm_execution_work_allowed_from_handover": True,
        "product_l7_work_allowed_from_handover": False,
        "required_current_user_boundary_tokens": 5,
        "legacy_handover_suppression_tokens": 0,
    }
    for refs in payload["sources"].values():
        for ref in refs:
            assert (REPO_ROOT / ref).exists(), ref
    for item in list(quantitative.values()) + list(qualitative.values()):
        assert (REPO_ROOT / item["source"]).exists(), item["id"]
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves a quantitative and qualitative L1-L6 current-scope pass"
    )
    assert "It does not prove L7 implementation" in payload["completion_denial"]["reason"]


def test_workflow_automation_coverage_map_keeps_l7_feature_ticketed() -> None:
    payload = yaml.safe_load(_read(L1_L6_WORKFLOW_AUTOMATION_COVERAGE_MAP))

    assert payload["schema_version"] == "l1_l6_workflow_automation_coverage_v1"
    assert payload["status"] == (
        "current_scope_l1_l6_workflow_automation_design_covered"
    )
    assert payload["scope"] == "L1-L6"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "workflow_map_is_implementation_evidence": False,
        "right_arm_execution_gate_implementation_done": False,
        "ci_or_equivalent_connected": False,
        "helix_db_write_adoption_done": False,
        "schema_migration_done": False,
        "external_tool_executed": False,
        "external_tool_installed": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
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

    workflow_surfaces = {item["id"]: item for item in payload["workflow_surfaces"]}
    assert set(workflow_surfaces) == {
        "WF-FORWARD-L0-L14",
        "WF-PAIR-FREEZE-L1-L6",
        "WF-REQUIREMENT-DRIFT",
        "WF-VG-OVERVIEW",
        "WF-DB-FEEDBACK",
        "WF-HARNESS-TOOL-ADMISSION",
    }
    assert payload["summary"]["workflow_surfaces_checked"] == len(workflow_surfaces)
    automation_surfaces = {
        item["id"]: item for item in payload["automation_surfaces"]
    }
    assert set(automation_surfaces) == {
        "AUTO-PLAN-REGISTRY",
        "AUTO-TRANSITION-HISTORY",
        "AUTO-GATE-PASS",
        "AUTO-DRIFT-DETECTOR",
        "AUTO-VG-OVERVIEW",
        "AUTO-FEEDBACK-SNAPSHOT",
        "AUTO-DOCUMENT-PROJECTION",
        "AUTO-TOOL-ADMISSION",
        "AUTO-HANDOVER-BOUNDARY",
    }
    assert payload["summary"]["automation_surfaces_checked"] == len(
        automation_surfaces
    )
    assert payload["automation_trigger_policy"] == {
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
        item["automation_id"]: item for item in payload["automation_trigger_contracts"]
    }
    assert set(trigger_contracts) == set(automation_surfaces)
    assert payload["summary"]["automation_trigger_contracts_checked"] == len(
        trigger_contracts
    )
    trigger_ticket_ids = {
        item["id"] for item in payload["deferred_feature_policy"]["feature_tickets"]
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
        assert not surface["current_l1_l6_evidence"].startswith(
            "docs/v2/L7-test-design/"
        )
        assert (REPO_ROOT / surface["current_l1_l6_evidence"]).exists(), (
            automation_id,
            surface["current_l1_l6_evidence"],
        )
        assert contract["deferred_feature_ticket_id"] in trigger_ticket_ids
        assert contract["completion_guard"].startswith("trigger_contract_is_not_")
        assert expected_forbidden_by_automation[automation_id] in contract[
            "forbidden_current_scope"
        ]
    db_targets = [item["db_target"] for item in automation_surfaces.values()]
    assert len(set(db_targets)) == len(db_targets)
    assert payload["summary"]["db_registry_targets_mapped"] == len(db_targets)
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
    assert payload["db_convergence_policy"] == {
        "current_scope_action": "design_map_only",
        "writes_allowed_now": False,
        "schema_migration_allowed_now": False,
        "plan_registry_import_done": False,
        "append_only_feedback_until_approved_l7": True,
        "candidate_is_not_closure": True,
        "forward_vmodel_return_required_before_completion": True,
    }
    convergence = payload["cross_audit_convergence_contract"]
    assert convergence["current_scope_action"] == (
        "prove_db_feedback_dependency_workflow_alignment_only"
    )
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
    assert payload["summary"]["cross_audit_convergence_rows_checked"] == len(
        convergence_rows
    )
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
        assert row["db_target"] == automation_surfaces[row["workflow_automation_id"]][
            "db_target"
        ]
        assert row["dependency_projection_or_output"] in allowed_dependency_outputs
        assert row["completion_guard"].endswith("_is_not_closure") or row[
            "completion_guard"
        ].startswith("trigger_contract_is_not_") or row[
            "completion_guard"
        ] == "projection_contract_is_not_db_write"
    assert payload["route_policy"] == {
        "current_scope_action": "map_detector_to_gate_only",
        "gate_execution_done": False,
        "gate_promotion_done": False,
        "feedback_auto_apply_done": False,
        "route_mapping_is_not_completion_evidence": True,
        "evidence_must_not_use_l7_test_design": True,
    }
    routes = {item["route_id"]: item for item in payload["detector_gate_routes"]}
    assert set(routes) == {
        "ROUTE-L1-L6-REQUIREMENT-DRIFT",
        "ROUTE-L1-L6-PAIR-BALANCE",
        "ROUTE-L1-L6-GOVERNANCE",
        "ROUTE-L1-L6-DB-FEEDBACK",
        "ROUTE-L1-L6-HARNESS-TOOLS",
        "ROUTE-L1-L6-CODEX-CLAUDE-GUARD-PARITY",
        "ROUTE-L1-L6-HANDOVER-BOUNDARY",
    }
    assert payload["summary"]["detector_gate_routes_mapped"] == len(routes)
    assert routes["ROUTE-L1-L6-REQUIREMENT-DRIFT"]["detector"] == (
        "requirement_drift"
    )
    assert "G6" in routes["ROUTE-L1-L6-PAIR-BALANCE"]["gates"]
    assert routes["ROUTE-L1-L6-DB-FEEDBACK"]["current_scope_evidence"] == str(
        L1_L6_DB_FEEDBACK_LIFECYCLE_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert routes["ROUTE-L1-L6-HARNESS-TOOLS"]["current_scope_evidence"] == str(
        L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)
    )
    assert routes["ROUTE-L1-L6-HANDOVER-BOUNDARY"]["detector"] == (
        "handover_legacy_metadata_misread"
    )

    feature_policy = payload["deferred_feature_policy"]
    assert feature_policy["implementation_required_before_fail_close"] is True
    feature_tickets = {item["id"]: item for item in feature_policy["feature_tickets"]}
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
    assert feature_tickets["phase_enum_l0_l14_runtime_retrofit"]["unlocks"] == [
        "safe task retitle / metadata refresh command",
        "runtime phase enum metadata validation",
        "handover legacy L7 label regression guard",
    ]
    assert payload["summary"]["deferred_feature_entry_points_checked"] == len(
        feature_tickets
    )
    parked_feature_tickets = {
        item["id"]: item for item in feature_policy["parked_feature_tickets"]
    }
    assert parked_feature_tickets == {}
    current_scope_authorized_tickets = {
        item["id"]: item
        for item in feature_policy["current_scope_authorized_feature_tickets"]
    }
    assert set(current_scope_authorized_tickets) == {"detector_failclose_ci_gate"}
    detector_gate_ticket = current_scope_authorized_tickets["detector_failclose_ci_gate"]
    assert detector_gate_ticket["status"] == "active_ci_enforcement"
    assert detector_gate_ticket["current_task_scope"] == (
        "ci_enforcement_and_boundary_unpark"
    )
    assert detector_gate_ticket["ticket_is_completion_evidence"] is False
    assert detector_gate_ticket["unlocks"] == [
        "CI gate connection",
        "automation-gate hardening",
    ]
    assert detector_gate_ticket["still_parked"] == [
        "detector fail-close promotion",
    ]
    assert payload["summary"]["parked_feature_entry_points_checked"] == 0

    for refs in payload["sources"].values():
        for ref in refs:
            assert not ref.startswith("docs/v2/L7-test-design/"), ref
            assert (REPO_ROOT / ref).exists(), ref
    for surface in workflow_surfaces.values():
        assert (REPO_ROOT / surface["source"]).exists(), surface["source"]
        assert surface["automation_connection"], surface["id"]
        assert surface["current_scope_status"]
        assert "implementation_done" not in surface["current_scope_status"]
    evidence_paths = {
        ref
        for refs in payload["sources"].values()
        for ref in refs
    }
    for route in routes.values():
        assert not route["current_scope_evidence"].startswith("docs/v2/L7-test-design/")
        assert (REPO_ROOT / route["current_scope_evidence"]).exists(), route
        assert route["gates"], route["route_id"]
        assert route["current_scope_evidence"] in evidence_paths
    for ticket in feature_tickets.values():
        assert ticket["path"].startswith("docs/plans/add-feature/"), ticket["id"]
        assert (REPO_ROOT / ticket["path"]).exists(), ticket["id"]
        assert ticket["unlocks"], ticket["id"]
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves only L1-L6 workflow automation design coverage"
    )


def test_process_docs_do_not_reference_legacy_l6_function_design_path() -> None:
    offenders = []
    for path in sorted(PROCESS_DOCS_DIR.glob("*.md")):
        text = _read(path)
        if "docs/v2/L6-function-design" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
    assert "docs/v2/L6-functional-design" in _read(L6_PROCESS_DOC)
    assert "docs/v2/L6-functional-design" in _read(
        REPO_ROOT / "docs/v2/process/L07-implementation-sprint.md"
    )


def test_plan_templates_do_not_generate_legacy_l6_function_design_path() -> None:
    offenders = []
    for path in PLAN_TEMPLATE_FILES:
        text = _read(path)
        if "docs/v2/L6-function-design" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
    for path in PLAN_TEMPLATE_FILES:
        assert "parent_design: docs/v2/L6-functional-design" in _read(path)


def test_schedule_wbs_templates_generate_l7_sprint_not_legacy_l4_sprint() -> None:
    offenders = []
    for path in SCHEDULE_WBS_TEMPLATE_FILES:
        text = _read(path)
        if "L4 Sprint" in text or "L4 実装では" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))

    assert offenders == []
    for path in SCHEDULE_WBS_TEMPLATE_FILES:
        assert "L7 Sprint" in _read(path) or "L7 実装スプリント" in _read(path)


def test_current_user_facing_surfaces_use_current_l0_l14_terms() -> None:
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
    for path in CURRENT_L0_L14_USER_FACING_SURFACES:
        text = _read(path)
        for term in legacy_terms:
            if term in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {term}")

    assert offenders == []
    assert "L7 Sprint" in _read(REPO_ROOT / "cli/helix-sprint")
    assert "PLAN-001 の L7 実装" in _read(AI_HARNESS_DOC)
    assert "PLAN-001 の L7 実装" in _read(REPO_ROOT / "README.md")
    assert "| L12 | 受入テスト |" in _read(
        REPO_ROOT / "docs/v2/document-system-definition.md"
    )
    assert "| L14 | 運用学習 / 運用改善 |" in _read(
        REPO_ROOT / "docs/v2/document-system-definition.md"
    )
    assert "L12 受入テストフェーズ" in _read(
        REPO_ROOT / "docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md"
    )
    assert "G4 基本設計凍結ゲート検証" in _read(
        REPO_ROOT / "cli/templates/gate-checks.yaml"
    )
    assert "L7 Sprint .1-.5 standard 8-step workflow DSL" in _read(
        REPO_ROOT / "cli/config/workflows/l4-sprint-workflow.yaml"
    )
    assert "L12 受入テスト PLAN テンプレート" in _read(
        REPO_ROOT / "cli/config/functional-registry.yaml"
    )


def test_verification_skill_uses_current_l0_l14_phase_terms() -> None:
    text = _read(VERIFICATION_SKILL_DOC)

    assert "### L4（基本設計 / 外部設計 + 総合テスト設計）" in text
    assert "### L5（詳細設計 / 内部設計 + 結合テスト設計）" in text
    assert "### L6（機能設計 / 仕様書 + 単体テスト設計）" in text
    assert "### L7（実装 + 単体テスト実装 / 実施 / coverage closure）" in text
    assert "L6 は機能設計 / 仕様書と単体テスト設計を凍結する工程" in text
    assert "L6            機能設計 / 仕様書 + 単体テスト設計 ←→ L7 実装 + 単体テスト closure" in text

    legacy_terms = [
        "### L4（実装）",
        "### L5（Visual）",
        "### L6（統合検証）",
        "### L7（デプロイ）",
        "### L8（受入）",
        "L4 実装（底）",
        "L5 Visual Refinement",
        "L7             デプロイ",
        "HELIXフェーズ番号（L3=詳細設計+API契約",
    ]
    for term in legacy_terms:
        assert term not in text


def test_runtime_skill_metadata_uses_current_l0_l14_phase_terms() -> None:
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
    for path in CURRENT_PHASE_SKILL_FILES:
        text = _read(path)
        for term in legacy_terms:
            if term in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {term}")

    assert offenders == []

    assert "HELIX L13 運用検証 / 運用テスト" in _read(
        REPO_ROOT / "skills/workflow/deploy/SKILL.md"
    )
    assert "HELIX L7 実装 / L13 運用検証" in _read(
        REPO_ROOT / "skills/advanced/migration/SKILL.md"
    )
    assert "HELIX L13 運用検証 / 運用テスト と L14 運用学習 / 運用改善" in _read(
        REPO_ROOT / "skills/workflow/incident/SKILL.md"
    )
    assert "HELIX L14 運用学習 / 運用改善" in _read(
        REPO_ROOT / "skills/workflow/postmortem/SKILL.md"
    )
    assert "L10 フロントUX / 業務デザイン磨き上げ" in _read(
        REPO_ROOT / "skills/common/visual-design/SKILL.md"
    )
    assert "G7 実装 closure" in _read(
        REPO_ROOT / "skills/workflow/review-stage-routing/SKILL.md"
    )
    assert "L7 Sprint .5" in _read(
        REPO_ROOT / "skills/workflow/debt-register/SKILL.md"
    )


def test_all_skill_docs_do_not_use_legacy_l4_l7_l8_phase_terms() -> None:
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
    for path in ALL_SKILL_DOCS:
        text = _read(path)
        for term in legacy_terms:
            if term in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {term}")

    assert offenders == []


def test_fr18_l6_unit_test_design_index_covers_all_function_specs_without_l7_artifacts() -> None:
    payload = yaml.safe_load(_read(FR18_L6_UNIT_TEST_DESIGN_INDEX))

    assert payload["schema_version"] == "fr18_l6_unit_test_design_index_v1"
    assert payload["status"] == "current_scope_l6_unit_test_design_index"
    assert payload["scope"] == "L6"
    assert payload["boundary"] == {
        "l6_unit_test_design_viewpoints_indexed": True,
        "l7_unit_test_design_artifacts_created": False,
        "l7_implementation_done": False,
        "unit_test_code_done": False,
        "coverage_closure_done": False,
        "goal_complete_allowed": False,
    }
    summary = payload["coverage_summary"]
    assert summary["fr_count"] == 18
    assert summary["specs_current_scope_l6_closed"] == 18
    assert summary["specs_with_l6_unit_test_design_viewpoints"] == 18
    assert summary["total_ut_candidates"] == 128
    assert summary["specs_with_draft_status"] == []
    assert summary["missing_l6_unit_test_design_viewpoint_specs"] == []
    assert summary["created_l7_fr_test_design_artifacts"] == []

    fr_specs = {item["fr_id"]: item for item in payload["fr_specs"]}
    assert len(fr_specs) == 18
    assert set(fr_specs) == {
        "FR-4ART-01",
        "FR-9MODE-01",
        "FR-CHANGEPROP-01",
        "FR-CTX-01",
        "FR-DOCREVIEW-01",
        "FR-DOCTOR-01",
        "FR-DRIFT-01",
        "FR-EVT-01",
        "FR-FNREG-01",
        "FR-GATE-01",
        "FR-GLOSSARY-01",
        "FR-GR-01",
        "FR-IMPACT-01",
        "FR-INV-01",
        "FR-MIGR-01",
        "FR-NSM-01",
        "FR-PLAN-01",
        "FR-TDD-01",
    }
    indexed_ut_candidate_total = sum(
        item["ut_candidate_count"] for item in fr_specs.values()
    )
    assert indexed_ut_candidate_total == summary["total_ut_candidates"]
    observed_ut_candidate_total = 0
    for item in fr_specs.values():
        spec_path = REPO_ROOT / item["spec"]
        assert spec_path.exists()
        text = _read(spec_path)
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        assert frontmatter["status"] == "current_scope_l6_closed"
        assert (
            frontmatter["implementation_status"]
            == "design_gap_closed_current_phase"
        )
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
        assert len(
            {
                match
                for match in re.findall(
                    r"\|\s*([A-Z0-9]+-FN-[0-9]{2})\s*\|",
                    text,
                )
            }
        ) == item["ut_candidate_count"]
        candidate_ids = re.findall(
            rf"{re.escape(item['ut_candidate_prefix'])}-[0-9]{{2}}",
            text,
        )
        assert len(candidate_ids) == item["ut_candidate_count"]
        assert len(set(candidate_ids)) == item["ut_candidate_count"]
        observed_ut_candidate_total += len(set(candidate_ids))

    assert observed_ut_candidate_total == summary["total_ut_candidates"]

    assert not (REPO_ROOT / "docs/v2/L7-test-design/FR-FNREG-01").exists()
    assert not (REPO_ROOT / "docs/v2/L7-test-design/FR-GLOSSARY-01").exists()
    assert payload["completion_denial"]["reason"].startswith(
        "This index proves L6 unit-test-design viewpoints only"
    )
    assert "coverage closure evidence" in payload["completion_denial"][
        "missing_before_l7_completion"
    ]


def test_l6_function_design_links_fr18_l6_unit_test_design_index_without_l7_claim() -> None:
    text = _read(L6_HELIX_FUNCTION_DESIGN_DOC)

    assert "### 5.3 FR18 追補と L6 単体テスト設計観点索引" in text
    assert "docs/v2/L6-functional-design/FR-*/function-spec.md" in text
    assert str(FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT)) in text
    assert "Phase3 L7 へ defer" not in text
    assert "L7 実装時に TDD で sharpening" not in text
    assert "FR 単位の L6 仕様追補へ分割展開した" in text
    assert "L6 の「単体テスト設計観点」" in text
    assert "L7 の単体テスト設計成果物" in text
    assert "単体テスト実装" in text
    assert "単体テスト実施" in text
    assert "coverage closure ではない" in text
    assert "承認済み add-feature を入口にする" in text
    assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
    assert "対応する L7 成果物は現在タスクでは作成しない" in text
    assert "fr18-unit-test-design-index.yaml" in text
    assert "L7 成果物と混同されない" in text
    checklist = text.split("## 6. 自己検証チェックリスト", 1)[1]
    assert "- [ ]" not in checklist
    assert "既存 frozen 範囲の `FN-*`" in checklist
    assert "L6 の単体テスト設計観点 128 件" in checklist
    assert "`*-FN-*` と `*-UT-CAND-*` の対応を L6 内で示すだけ" in checklist
    assert "coverage closure の証跡として扱わない" in checklist


def test_l1_l6_boundary_docs_route_unapproved_l7_to_add_feature() -> None:
    verification_strategy = _read(
        REPO_ROOT / "docs/v2/L1-requirements/helix-workflows-verification-strategy.md"
    )
    l4_function_structure = _read(
        REPO_ROOT / "docs/v2/L4-basic-design/機能構成設計.md"
    )
    l5_physical_data = _read(
        REPO_ROOT / "docs/v2/L5-detailed-design/物理データ設計.md"
    )
    old_whole_source_audit = _read(
        REPO_ROOT / "docs/v2/audit/2026-06-07-whole-source-design-coverage-audit.md"
    )

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


def test_l1_l6_docs_have_no_unqualified_legacy_l7_defer_phrases() -> None:
    scan_roots = [
        REPO_ROOT / "docs/v2/L1-requirements",
        REPO_ROOT / "docs/v2/L2-screen-design",
        REPO_ROOT / "docs/v2/L3-requirements",
        REPO_ROOT / "docs/v2/L4-basic-design",
        REPO_ROOT / "docs/v2/L5-detailed-design",
        REPO_ROOT / "docs/v2/L6-functional-design",
        REPO_ROOT / "docs/v2/audit",
        REPO_ROOT / "docs/v2/process",
    ]
    forbidden_phrases = [
        "Phase3 L7 実装（TDD sharpening）へ defer",
        "Phase3 L7（TDD sharpening）へ defer",
        "target: Phase3-L7",
        "L7 実装で code へ昇格する",
        "L6 関数仕様と L7 実装で詳細化する",
        "Phase3 defer していたもの",
    ]

    hits: list[str] = []
    for root in scan_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".yaml", ".yml"}:
                continue
            text = _read(path)
            for phrase in forbidden_phrases:
                if phrase in text:
                    hits.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")
    assert hits == []


def test_l6_preexisting_l7_pair_docs_do_not_authorize_current_l7_work() -> None:
    registry_detector = _read(
        REPO_ROOT / "docs/v2/L6-functional-design/registry-detector-機能設計.md"
    )
    functional_registry_detector = _read(
        REPO_ROOT
        / "docs/v2/L6-functional-design/functional-registry-detector-機能設計.md"
    )
    whole_source_coverage = _read(
        REPO_ROOT / "docs/v2/L6-functional-design/whole-source-coverage-機能設計.md"
    )

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


def test_l6_process_doc_explains_ut_candidate_index_boundary() -> None:
    text = _read(L6_PROCESS_DOC)

    assert "#### Current-scope boundary: L6 内の単体テスト設計観点" in text
    assert "L7 実装が明示承認されていない" in text
    assert "L7 test-design artifact を新規作成しない" in text
    assert "docs/v2/L6-functional-design/FR-*/function-spec.md" in text
    assert str(FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT)) in text
    assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
    assert "L7 の単体テスト設計成果物" in text
    assert "単体テスト実装" in text
    assert "単体テスト実施" in text
    assert "カバレッジ確認 / closure ではない" in text
    assert "L6 内単体テスト設計観点索引" in text
    assert "証跡の階層違反" in text


def test_process_readme_links_l6_current_scope_unit_test_design_index() -> None:
    text = _read(REPO_ROOT / "docs/v2/process/README.md")

    assert "### L6 current-scope index" in text
    assert "fr18-unit-test-design-index.yaml" in text
    assert "FR18 全件、L6 単体テスト設計観点 128 件" in text
    assert "L7 実装が未承認" in text
    assert "L7 単体テスト設計成果物" in text
    assert "単体テスト実装" in text
    assert "単体テスト実施" in text
    assert "カバレッジ確認 / closure ではない" in text


def test_ui_absent_waiver_revalidation_keeps_l2_l10_not_applicable_bounded() -> None:
    payload = yaml.safe_load(_read(UI_ABSENT_WAIVER_REVALIDATION_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    focus_text = _read(L0_L6_FOCUS_AUDIT)
    focus_frontmatter = yaml.safe_load(focus_text.split("---", 2)[1])

    assert payload["schema_version"] == "ui_absent_waiver_revalidation_v1"
    assert payload["status"] == "revalidation_defined_currently_not_applicable"
    assert payload["source_waiver"] == (
        "docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md"
    )
    assert payload["current_state"] == {
        "pair": "L2-L10",
        "applicability": "not_applicable",
        "reason": "ui_absent",
        "waiver_owner": "TL",
        "waiver_status": "frozen",
        "revalidated_for_current_scope": True,
        "goal_complete_allowed_by_this_waiver": False,
    }
    triggers = {item["id"]: item for item in payload["unskip_triggers"]}
    assert set(triggers) == {
        "official_docs_site_or_web_ui",
        "interactive_ui_tui_visual_mock_or_dashboard",
        "downstream_product_screens",
    }
    assert "CLI help text" in payload["non_unskip_examples"]
    assert "command output formatting" in payload["non_unskip_examples"]
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
    assert str(FR18_L6_UNIT_TEST_DESIGN_INDEX.relative_to(REPO_ROOT)) in focus_text
    assert "docs/v2/L7-test-design/*.md" not in focus_text
    assert "It is not current authorization to create L7 artifacts" in focus_text
    assert payload["safety"] == {
        "schema_migration": False,
        "detector_or_gate_body_change": False,
        "frontend_artifact_creation": False,
        "infrastructure_change": False,
        "auth_or_pii_change": False,
    }
    assert payload["completion_boundary"] == {
        "waiver_revalidated_is_goal_completion": False,
        "waiver_invalid_requires_unskip": True,
        "ui_artifact_exists_requires_L2_L10_scope": True,
        "goal_complete_allowed": False,
    }
    requirements = {item["id"]: item for item in goal_audit["requirements"]}
    assert "docs/v2/L7-test-design/ui-absent-waiver-revalidation.yaml" in requirements[
        "REQ-WORKFLOW-AUTOMATION-REVIEW"
    ]["evidence"]


def test_right_arm_handover_request_matches_adoption_manifest_without_self_expanding() -> None:
    request = yaml.safe_load(_read(RIGHT_ARM_HANDOVER_REQUEST_MANIFEST))
    adoption = yaml.safe_load(_read(RIGHT_ARM_GATE_ADOPTION_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))

    assert request["schema_version"] == "right_arm_execution_gate_handover_request_v1"
    assert request["status"] == "needs_handover_expansion"
    assert request["source_adoption_manifest"] == (
        "docs/v2/L7-test-design/right-arm-execution-gates-adoption.yaml"
    )
    assert request["source_goal_audit"] == (
        "docs/v2/L7-test-design/goal-completion-audit.yaml"
    )
    assert request["source_closure_plan"] == (
        "docs/v2/L7-test-design/right-arm-full-flow-closure-plan.yaml"
    )
    assert request["current_scope"]["sufficient_for_gate_implementation"] is False
    assert request["current_scope"]["allowed_now"] == goal_audit["current_handover_scope"][
        "allowed_now"
    ]
    assert request["activation_policy"] == {
        "requires_explicit_handover_update": True,
        "self_expand_current_handover": False,
        "allowed_after_activation_only": True,
        "activation_evidence_required": [
            "handover Next Action includes requested implementation files.",
            "task-plan or PLAN frontmatter includes allowed_files and acceptance evidence.",
            "strict full-flow command is the exit gate.",
        ],
    }
    assert request["requested_next_action"]["completion_exit_gate"] == (
        "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json"
    )
    assert request["requested_next_action"]["required_overall_clean"] is True

    requested_gates = {
        item["gate_id"]: item for item in request["requested_next_action"]["gates"]
    }
    adoption_gates = {item["gate_id"]: item for item in adoption["gates"]}
    assert set(requested_gates) == set(adoption_gates) == {"G8", "G9", "G12", "G14"}

    for gate_id, requested_gate in requested_gates.items():
        adoption_gate = adoption_gates[gate_id]
        assert requested_gate["pair"] == adoption_gate["pair"]
        assert requested_gate["plan_id"] == adoption_gate["plan_id"]
        assert requested_gate["requested_files"] == adoption_gate[
            "allowed_implementation_files"
        ]
        assert requested_gate["verification_commands"] == adoption_gate[
            "verification_commands"
        ]
        assert requested_gate["acceptance_exit_condition"] == adoption_gate[
            "acceptance_exit_condition"
        ]

    assert request["safety"] == {
        "schema_migration": False,
        "destructive_data_operation": False,
        "auth_or_pii_change": False,
        "external_api_or_infrastructure_change": False,
        "auto_apply_feedback_candidates": False,
        "escalation_required_if": [
            "D-API / D-DB / D-CONTRACT change is required.",
            "schema migration or rollback design is required.",
            "acceptance criteria must be reinterpreted.",
            "implementation needs files not listed in requested_files.",
        ],
    }


def test_right_arm_full_flow_closure_plan_is_ordered_and_scope_safe() -> None:
    plan = yaml.safe_load(_read(RIGHT_ARM_CLOSURE_PLAN_MANIFEST))
    request = yaml.safe_load(_read(RIGHT_ARM_HANDOVER_REQUEST_MANIFEST))
    adoption = yaml.safe_load(_read(RIGHT_ARM_GATE_ADOPTION_MANIFEST))

    assert plan["schema_version"] == "right_arm_full_flow_closure_plan_v1"
    assert plan["status"] == "ready_for_scope_expansion"
    assert plan["source_handover_request"] == (
        "docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml"
    )
    assert plan["activation_policy"] == {
        "current_handover_scope_sufficient": False,
        "requires_explicit_scope_expansion": True,
        "self_expand_current_handover": False,
        "activation_evidence_required": [
            "handover Next Action lists every requested implementation file for the selected gate.",
            "PLAN or task-plan includes allowed_files, acceptance, rollback, and verification commands.",
            "strict full-flow command remains the exit gate.",
        ],
    }
    assert plan["global_exit_gate"] == {
        "command": "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json",
        "required": {
            "overall_clean": True,
            "deferred_count": 0,
            "deferred_gates": [],
        },
    }

    sequence = plan["implementation_sequence"]
    assert [item["order"] for item in sequence] == [1, 2, 3, 4]
    assert [item["gate_id"] for item in sequence] == ["G8", "G9", "G12", "G14"]
    requested_gates = {
        item["gate_id"]: item for item in request["requested_next_action"]["gates"]
    }
    adoption_gates = {item["gate_id"]: item for item in adoption["gates"]}
    for item in sequence:
        gate_id = item["gate_id"]
        assert item["pair"] == requested_gates[gate_id]["pair"]
        assert item["pair"] == adoption_gates[gate_id]["pair"]
        assert item["requested_files"] == requested_gates[gate_id]["requested_files"]
        assert item["verification_commands"] == requested_gates[gate_id][
            "verification_commands"
        ]
        assert item["rollback_boundary"].startswith(f"Revert only {gate_id}")
        assert any("strict-full-flow" in command for command in item["verification_commands"])

    assert "semantic_excluded_orphan=18 remains justified" in " ".join(
        sequence[1]["local_exit_evidence"]
    )
    assert "feedback_closed evidence connects candidate adoption" in " ".join(
        sequence[3]["local_exit_evidence"]
    )
    assert plan["safety"] == request["safety"]
    assert plan["completion_boundary"] == {
        "plan_materialized_is_goal_completion": False,
        "scope_expansion_is_goal_completion": False,
        "per_gate_local_pass_is_full_goal_completion": False,
        "all_gates_and_feedback_and_ci_required": True,
    }


def test_feedback_loop_adoption_audit_keeps_candidates_from_counting_as_closure() -> None:
    payload = yaml.safe_load(_read(FEEDBACK_LOOP_ADOPTION_AUDIT_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    live_deferred_pairs = _live_strict_deferred_pairs()
    current_capabilities = payload["current_capabilities"]

    assert payload["schema_version"] == "feedback_loop_adoption_audit_v1"
    assert payload["status"] == "partial_candidate_generated"
    assert payload["source_test_design"] == (
        "docs/v2/L7-test-design/deferred-gate-adoption-単体テスト設計.md"
    )
    assert payload["source_goal_audit"] == (
        "docs/v2/L7-test-design/goal-completion-audit.yaml"
    )
    assert payload["source_feedback_closure_readiness"] == (
        "docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml"
    )
    assert current_capabilities["derived_from"] == "strict_vg_overview"
    assert current_capabilities["last_verified_command"] == (
        vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    )
    assert {
        key: value
        for key, value in current_capabilities.items()
        if key not in {"derived_from", "last_verified_command", "strict_vg_deferred_count", "strict_vg_deferred_gates"}
    } == {
        "top_level_harness_routed": True,
        "json_schema": "helix_harness_feedback_loop_snapshot_v1",
        "emits_route_candidates": True,
        "emits_learning_candidates": True,
        "emits_plan_candidates": True,
        "emits_pr_candidates": True,
        "appends_events_metrics_feedback": True,
        "registers_missing_feedback_input": True,
        "reads_strict_vg_overview": True,
        "not_applicable_pair_waivers": ["L2-L10"],
    }
    assert current_capabilities["strict_vg_deferred_count"] == len(live_deferred_pairs)
    assert current_capabilities["strict_vg_deferred_gates"] == _live_strict_deferred_gate_ids()
    assert str(payload["updated"]) == "2026-06-10"
    snapshot = payload["captured_snapshot"]
    assert str(snapshot["captured_on"]) == "2026-06-10"
    assert snapshot["command"] == (
        "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix harness feedback-loop --json --days 30"
    )
    assert snapshot["schema_version"] == "helix_harness_feedback_loop_snapshot_v1"
    assert snapshot["window_days"] == 30
    assert snapshot["counts"]["automation_running"] >= 1
    assert snapshot["counts"]["hook_warn_fail"] >= 150
    assert snapshot["counts"]["events"] >= 151
    assert snapshot["counts"]["metrics"] >= 1043
    assert snapshot["counts"]["feedback"] >= 1
    assert snapshot["counts"]["verify_runs"] >= 1
    assert snapshot["candidate_counts"] == {
        "route_candidates": 20,
        "learning_candidates": 8,
        "plan_candidates": 20,
        "pr_candidates": 8,
    }
    assert snapshot["vg_overview"] == {
        "available": True,
        "overall_clean": False,
        "enforced": True,
        "deferred_count": 3,
        "deferred_gates": ["G9", "G12", "G14"],
        "not_applicable_count": 1,
    }
    assert set(snapshot["pr_candidate_source_pattern_keys"]) == {
        "feedback:feedback_pattern",
        "hook_events:detector_pattern",
        "automation_runs:automation_running_pattern",
        "vg_overview:full_flow_deferred_execution_gate",
        "vg_overview:not_applicable_pair_waiver",
    }
    assert snapshot["safety"] == {
        "schema_migration": False,
        "auto_apply": False,
        "writes_detector_or_gate": False,
    }
    assert payload["source_categories_required"] == [
        "automation_runs:automation_running_pattern",
        "events/metrics:missing_observability_input",
        "feedback:missing_feedback_input",
        "harness_check_events:harness_warning_pattern",
        "hook_events:detector_pattern",
        "verify_runs:missing_verify_input",
        "vg_overview:full_flow_deferred_execution_gate",
        "vg_overview:not_applicable_pair_waiver",
    ]
    assert payload["safety"] == {
        "schema_migration": False,
        "auto_apply": False,
        "writes_detector_or_gate": False,
        "destructive_data_operation": False,
        "external_api_or_infrastructure_change": False,
    }
    assert payload["adoption_boundary"] == {
        "candidate_generated": True,
        "db_snapshot_registered": True,
        "plan_or_pr_adopted": False,
        "gate_evidence_closed": False,
        "feedback_closed": False,
        "goal_complete_allowed": False,
        "reason": "plan_candidates and pr_candidates are adoption proposals, not accepted closure evidence.",
    }
    assert {
        "gate or detector body edits",
        "DB schema migration",
        "automatic application of plan_candidates or pr_candidates",
        "destructive DB/data operation",
    }.issubset(set(payload["non_goals_under_current_handover"]))
    requirement = {
        item["id"]: item for item in goal_audit["requirements"]
    }["REQ-HELIX-DB-FEEDBACK-LOOP"]
    assert requirement["status"] == "partial"
    assert "docs/v2/L7-test-design/feedback-loop-adoption-audit.yaml" in requirement[
        "evidence"
    ]
    assert "docs/v2/L7-test-design/feedback-adoption-closure-readiness.yaml" in requirement[
        "evidence"
    ]


def test_feedback_adoption_closure_readiness_keeps_adoption_chain_incomplete() -> None:
    payload = yaml.safe_load(_read(FEEDBACK_ADOPTION_CLOSURE_READINESS_MANIFEST))

    assert payload["schema_version"] == "feedback_adoption_closure_readiness_v1"
    assert payload["status"] == "ready_to_adopt_not_closed"
    assert payload["readiness_boundary"] == {
        "candidates_generated": True,
        "db_snapshot_registered": True,
        "adoption_chain_defined": True,
        "plan_or_pr_adopted": False,
        "gate_evidence_closed": False,
        "feedback_closed": False,
        "goal_complete_allowed": False,
        "reason": "Candidate generation and DB snapshot registration exist, but no candidate has been promoted through PLAN/PR/gate evidence and recurrence closure.",
    }
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
    assert chain[1]["completion_value"] == "not_closure"
    assert chain[-1]["completion_value"] == "closure_candidate"
    assert {
        "candidate_id",
        "plan_id",
        "gate_evidence_ref",
        "ci_or_equivalent_run_id",
        "helix_db_event_id",
        "recurrence_status",
    }.issubset(set(payload["required_record_fields"]))
    assert "vg_overview:full_flow_deferred_execution_gate" in payload[
        "candidate_sources_in_scope"
    ]
    assert payload["safety"] == {
        "schema_migration": False,
        "destructive_data_operation": False,
        "auto_apply_feedback_candidates": False,
        "detector_or_gate_body_change": False,
        "external_api_or_infrastructure_change": False,
        "auth_or_pii_change": False,
    }
    assert payload["completion_boundary"] == {
        "candidate_generated_is_goal_completion": False,
        "db_snapshot_registered_is_goal_completion": False,
        "plan_materialized_is_goal_completion": False,
        "feedback_closed_requires_gate_and_ci_evidence": True,
        "goal_complete_allowed": False,
    }


def test_fr_tdd_l6_function_spec_closes_design_gap_without_l7_artifact() -> None:
    text = _read(FR_TDD_L6_FUNCTION_SPEC)

    assert not FR_TDD_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"TDD-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
    for blocked_transition in (
        "S2 不在の S3",
        "S5 不在の S7",
        "failing 確認なしの本体実装",
        "CI/equivalent なしの full-flow completion claim",
    ):
        assert blocked_transition in text
    assert "TDD-UT-CAND-01" in text
    assert "TDD-UT-CAND-07" in text
    assert "現在タスクでは作成しない" in text
    assert "`TDD-UT-CAND-*` は L6 の test-design 観点" in text
    assert "L7 の完了済み UT inventory ではない" in text


def test_fr_impact_l6_function_spec_closes_impact_design_gap_without_l7_artifact() -> None:
    text = _read(FR_IMPACT_L6_FUNCTION_SPEC)

    assert not FR_IMPACT_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"IMPACT-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_inv_l6_function_spec_closes_inventory_design_gap_without_l7_artifact() -> None:
    text = _read(FR_INV_L6_FUNCTION_SPEC)

    assert not FR_INV_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"INV-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_plan_l6_function_spec_closes_plan_auto_registration_design_gap_without_l7_artifact() -> None:
    text = _read(FR_PLAN_L6_FUNCTION_SPEC)

    assert not FR_PLAN_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"PLAN-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_evt_l6_function_spec_closes_forward_return_event_design_gap_without_l7_artifact() -> None:
    text = _read(FR_EVT_L6_FUNCTION_SPEC)

    assert not FR_EVT_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"EVT-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_gate_l6_function_spec_closes_gate_verdict_design_gap_without_l7_artifact() -> None:
    text = _read(FR_GATE_L6_FUNCTION_SPEC)

    assert not FR_GATE_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"GATE-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_drift_l6_function_spec_closes_drift_routing_design_gap_without_l7_artifact() -> None:
    text = _read(FR_DRIFT_L6_FUNCTION_SPEC)

    assert not FR_DRIFT_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"DRIFT-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_4art_l6_function_spec_closes_four_artifact_design_gap_without_l7_artifact() -> None:
    text = _read(FR_4ART_L6_FUNCTION_SPEC)

    assert not FR_4ART_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"ART4-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_changeprop_l6_function_spec_closes_change_propagation_design_gap_without_l7_artifact() -> None:
    text = _read(FR_CHANGEPROP_L6_FUNCTION_SPEC)

    assert not FR_CHANGEPROP_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"CHPROP-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_guardrail_l6_function_spec_closes_guardrail_design_gap_without_l7_artifact() -> None:
    text = _read(FR_GR_L6_FUNCTION_SPEC)

    assert not FR_GR_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"GR-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_doctor_l6_function_spec_closes_doctor_design_gap_without_l7_artifact() -> None:
    text = _read(FR_DOCTOR_L6_FUNCTION_SPEC)

    assert not FR_DOCTOR_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"DOCTOR-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_9mode_l6_function_spec_closes_mode_routing_design_gap_without_l7_artifact() -> None:
    text = _read(FR_9MODE_L6_FUNCTION_SPEC)

    assert not FR_9MODE_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"MODE9-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_context_l6_function_spec_closes_context_injection_design_gap_without_l7_artifact() -> None:
    text = _read(FR_CTX_L6_FUNCTION_SPEC)

    assert not FR_CTX_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"CTX-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_nsm_l6_function_spec_closes_alignment_score_design_gap_without_l7_artifact() -> None:
    text = _read(FR_NSM_L6_FUNCTION_SPEC)

    assert not FR_NSM_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"NSM-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_migration_l6_function_spec_closes_migration_design_gap_without_l7_artifact() -> None:
    text = _read(FR_MIGR_L6_FUNCTION_SPEC)

    assert not FR_MIGR_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"MIGR-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_docreview_l6_function_spec_closes_doc_review_design_gap_without_l7_artifact() -> None:
    text = _read(FR_DOCREVIEW_L6_FUNCTION_SPEC)

    assert not FR_DOCREVIEW_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"DOCREV-FN-{index:02d}" for index in range(1, 8)]:
        assert fn_id in text
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


def test_fr_function_registry_l6_function_spec_closes_registry_only_design_gap_without_l7_artifact() -> None:
    text = _read(FR_FNREG_L6_FUNCTION_SPEC)

    assert not FR_FNREG_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"FNREG-FN-{index:02d}" for index in range(1, 9)]:
        assert fn_id in text
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


def test_fr_glossary_l6_function_spec_closes_registry_only_design_gap_without_l7_artifact() -> None:
    text = _read(FR_GLOSSARY_L6_FUNCTION_SPEC)

    assert not FR_GLOSSARY_L7_TEST_DESIGN.exists()
    assert "implementation_status: design_gap_closed_current_phase" in text
    assert "現在フェーズでは L6 仕様までを閉じ" in text
    for fn_id in [f"GLOSS-FN-{index:02d}" for index in range(1, 9)]:
        assert fn_id in text
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


def test_db_backed_evidence_lifecycle_design_gap_is_closed_in_current_phase() -> None:
    l4 = _read(DB_EVIDENCE_LIFECYCLE_L4_DOC)
    l5 = _read(DB_EVIDENCE_LIFECYCLE_L5_DOC)
    l6 = _read(DB_EVIDENCE_LIFECYCLE_L6_DOC)
    l7_feature_plan = _read(DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN)
    scope_audit = _read(DB_EVIDENCE_LIFECYCLE_SCOPE_AUDIT)
    matrix = yaml.safe_load(_read(OBJECTIVE_EVIDENCE_MATRIX_MANIFEST))

    assert not DB_EVIDENCE_LIFECYCLE_L7_TEST_DESIGN.exists()
    for text in (l4, l5, l6):
        assert "implementation_status: design_gap_closed_current_phase" in text
        assert "schema_migration" in text
        assert "auto" in text.lower()

    for state in (
        "detected",
        "registered",
        "candidate_generated",
        "plan_materialized",
        "implementation_adopted",
        "verification_recorded",
        "gate_projected",
        "recurrence_closed",
    ):
        assert state in l4
        assert state in l5

    for storage in (
        "`events`",
        "`metrics`",
        "`feedback`",
        "`verify_runs`",
        "`gate_runs`",
        "`plan_registry`",
        "`entries`",
        "`links`",
    ):
        assert storage in l5

    for fn_id in [f"DBEV-FN-{index:02d}" for index in range(1, 9)]:
        assert fn_id in l6

    assert "L6 focus clean と full-flow completion を混同しない" in l6
    assert "本タスクでは L7 単体テスト設計を作成しない" in l6
    assert "workflow: add-feature" in l7_feature_plan
    assert "layer: L7" in l7_feature_plan
    assert "current_task_scope: feature_ticket_only" in l7_feature_plan
    assert "approval_required_before_l7_work: true" in l7_feature_plan
    assert "現在タスクで L7 成果物を生成した証跡ではない" in l7_feature_plan
    assert "L7 着手は本 PLAN の承認後に限る" in l7_feature_plan
    assert (
        "現在タスクでは `docs/v2/L7-test-design/db-backed-evidence-lifecycle-単体テスト設計.md` を作成しない"
        in l7_feature_plan
    )
    assert "DBEV-UT-*" in l7_feature_plan
    assert "feature ticket only" in scope_audit
    assert "is not present and is not claimed as completed" in scope_audit
    assert "not permission to perform L7 work inside the current task" in scope_audit

    items = {item["id"]: item for item in matrix["objective_items"]}
    db_feedback = items["OBJ-HELIX-DB-FEEDBACK"]
    assert db_feedback["status"] == "partial"
    assert db_feedback["design_gap_status"] == "L4_L6_closed_L7_feature_ticketed"
    evidence_artifacts = {
        evidence.get("artifact")
        for evidence in db_feedback["evidence"]
        if isinstance(evidence, dict)
    }
    assert {
        str(DB_EVIDENCE_LIFECYCLE_L4_DOC.relative_to(REPO_ROOT)),
        str(DB_EVIDENCE_LIFECYCLE_L5_DOC.relative_to(REPO_ROOT)),
        str(DB_EVIDENCE_LIFECYCLE_L6_DOC.relative_to(REPO_ROOT)),
        str(DB_EVIDENCE_LIFECYCLE_L7_FEATURE_PLAN.relative_to(REPO_ROOT)),
    }.issubset(evidence_artifacts)


def test_harness_external_tools_design_gap_is_closed_in_current_phase() -> None:
    l4 = _read(HARNESS_EXTERNAL_TOOLS_L4_DOC)
    l5 = _read(HARNESS_EXTERNAL_TOOLS_L5_DOC)
    l6 = _read(HARNESS_EXTERNAL_TOOLS_L6_DOC)
    feature_plan = _read(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN)
    feature_meta = yaml.safe_load(feature_plan.split("---", 2)[1])
    scope_audit = _read(HARNESS_EXTERNAL_TOOLS_SCOPE_AUDIT)
    harness_coverage = yaml.safe_load(_read(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP))
    pre_adoption_bridge = yaml.safe_load(
        _read(HARNESS_PRE_ADOPTION_REQUIREMENTS_ACCEPTANCE_AUDIT)
    )
    matrix = yaml.safe_load(_read(OBJECTIVE_EVIDENCE_MATRIX_MANIFEST))

    assert not HARNESS_EXTERNAL_TOOLS_L7_TEST_DESIGN.exists()
    for text in (l4, l5, l6):
        assert "implementation_status: design_gap_closed_current_phase" in text
        assert "schema_migration" in text
        assert "auto" in text.lower()

    for fn_id in [f"HEXT-FN-{index:02d}" for index in range(1, 11)]:
        assert fn_id in l6
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
    assert "HEXT-UT-CAND-01..10" in scope_audit
    assert "L6 unit-test-design viewpoints only" in scope_audit
    assert "tool invocation consent" in l4
    assert "OAuth / PAT" in l4
    assert "SARIF" in l4
    assert "CodeQL database" in l6

    assert "current_task_scope: L4_L6_design_closed_feature_ticketed" in feature_plan
    assert "approval_required_before_install: true" in feature_plan
    assert "external_tool_installation_allowed_now: false" in feature_plan
    assert str(L1_L6_HARNESS_EXTERNAL_TOOLS_COVERAGE_MAP.relative_to(REPO_ROOT)) in feature_meta[
        "related_docs"
    ]
    assert str(L1_L6_IMPROVEMENT_CANDIDATE_MAP.relative_to(REPO_ROOT)) in feature_meta[
        "related_docs"
    ]
    assert "| zizmor | zizmor official docs / repository |" in feature_plan
    assert "GitHub Actions workflow/action static analysis" in feature_plan
    assert "| SQLFluff | SQLFluff official docs |" in feature_plan
    assert "SQL/schema/migration lint findings" in feature_plan
    assert "| pytest-testmon | testmon official docs / pytest-testmon official repository |" in feature_plan
    assert "impacted-test selection findings" in feature_plan
    assert "| diff-cover | diff-cover official repository / PyPI |" in feature_plan
    assert "changed-line coverage / diff-quality findings" in feature_plan
    assert "| lychee | lychee official repository / docs |" in feature_plan
    assert "link/reference rot findings" in feature_plan
    assert "workflow security findings" in feature_plan
    assert "### 2.1 L1-L6 candidate inventory sync" in feature_plan
    assert "合計 33 candidate" in feature_plan
    assert "未承認の候補は install、execute、CI connection、DB write" in feature_plan
    assert "L7 test-design / implementation の証跡として扱わない" in feature_plan
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
        assert candidate_group in feature_plan
    candidate_inventory_counts = [
        int(count)
        for count in re.findall(
            r"^\| [^|\n]+ \| (\d+) \| feature-ticket-only \|",
            feature_plan,
            flags=re.MULTILINE,
        )
    ]
    assert sum(candidate_inventory_counts) == harness_coverage["summary"][
        "tool_candidates_checked"
    ]
    assert str(
        HARNESS_PRE_ADOPTION_REQUIREMENTS_ACCEPTANCE_AUDIT.relative_to(REPO_ROOT)
    ) in harness_coverage["sources"]["pre_adoption_requirements_acceptance"]
    assert harness_coverage["summary"][
        "pre_adoption_requirement_contracts_checked"
    ] == pre_adoption_bridge["summary"]["pre_adoption_requirement_contracts_checked"] == 5
    assert harness_coverage["pre_adoption_requirements_acceptance_bridge"] == {
        "source": str(
            HARNESS_PRE_ADOPTION_REQUIREMENTS_ACCEPTANCE_AUDIT.relative_to(REPO_ROOT)
        ),
        "current_scope_action": (
            "map_web_rechecked_tool_risks_to_existing_l1_l3_requirements_and_acceptance_obligations"
        ),
        "representative_sources_rechecked": 5,
        "pre_adoption_requirement_contracts_checked": 5,
        "all_contracts_reuse_existing_l3_requirements": True,
        "new_l3_fr_required_now": False,
        "acceptance_design_update_required_now": False,
        "adoption_or_execution_allowed_now": False,
        "db_write_allowed_now": False,
        "l7_artifact_allowed_now": False,
    }
    assert pre_adoption_bridge["schema_version"] == (
        "l1_l6_harness_pre_adoption_requirements_acceptance_v1"
    )
    assert pre_adoption_bridge["status"] == (
        "current_scope_l1_l6_requirements_acceptance_bridge_closed"
    )
    assert pre_adoption_bridge["boundary"]["l3_frozen_fr_added_by_this_audit"] is False
    assert pre_adoption_bridge["boundary"]["l12_acceptance_test_design_modified_by_this_audit"] is False
    assert pre_adoption_bridge["boundary"]["l7_artifacts_created_by_this_audit"] == 0
    assert pre_adoption_bridge["requirement_bridge_policy"]["new_l3_fr_required_now"] is False
    assert pre_adoption_bridge["requirement_bridge_policy"][
        "acceptance_design_update_required_now"
    ] is False
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
    bridge_contracts = {
        item["id"]: item
        for item in pre_adoption_bridge["pre_adoption_requirement_contracts"]
    }
    assert set(bridge_contracts) == {
        "HEXT-REQ-MCP-CONSENT-AUTH",
        "HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY",
        "HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP",
        "HEXT-REQ-SEMGREP-SAST-ADVISORY",
        "HEXT-REQ-CODEQL-IMPACT-INGESTION",
    }
    assert bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"]["source_id"] == (
        "MCP-SPEC-2025-06-18"
    )
    assert "FR-GR-01" in bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"][
        "reused_l3_requirements"
    ]
    assert "HEXT-FN-10" in bridge_contracts["HEXT-REQ-MCP-CONSENT-AUTH"][
        "l4_l6_design_controls"
    ]
    assert bridge_contracts["HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY"][
        "source_id"
    ] == "GITHUB-MCP-SERVER"
    assert "FR-IMPACT-01" in bridge_contracts[
        "HEXT-REQ-GITHUB-MCP-ALLOWLIST-READONLY"
    ]["reused_l3_requirements"]
    assert bridge_contracts["HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"][
        "source_id"
    ] == "OPENAI-APPS-SDK-MCP-DESCRIPTOR"
    assert "FR-GR-01" in bridge_contracts[
        "HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"
    ]["reused_l3_requirements"]
    assert "HEXT-FN-08" in bridge_contracts[
        "HEXT-REQ-OPENAI-APPS-DESCRIPTOR-META-CSP"
    ]["l4_l6_design_controls"]
    assert bridge_contracts["HEXT-REQ-SEMGREP-SAST-ADVISORY"]["source_id"] == (
        "SEMGREP-CE"
    )
    assert "FR-TDD-01" in bridge_contracts["HEXT-REQ-SEMGREP-SAST-ADVISORY"][
        "reused_l3_requirements"
    ]
    assert bridge_contracts["HEXT-REQ-CODEQL-IMPACT-INGESTION"]["source_id"] == (
        "GITHUB-CODEQL"
    )
    assert "FR-CHANGEPROP-01" in bridge_contracts[
        "HEXT-REQ-CODEQL-IMPACT-INGESTION"
    ]["reused_l3_requirements"]
    assert all(
        item["current_scope_result"] == "requirements_acceptance_bridge_only"
        for item in bridge_contracts.values()
    )
    assert "L4-L6 設計のみを閉じ" in feature_plan
    assert "HEXT-FN-09" in feature_plan
    assert "HEXT-FN-10" in feature_plan
    assert "L4-L6 設計の作成は外部ツール導入完了ではない" in feature_plan
    assert "本タスクでは L7 単体テスト設計" in l6
    assert "外部ツールをインストールしない" in l4
    assert "feature ticket only" in scope_audit
    assert "is not present and is not claimed as completed" in scope_audit
    assert "`HEXT-UT-*` is not a current-scope completed test-design artifact" in scope_audit
    assert (
        "MCP server, GitHub MCP Server, Semgrep CE, CodeQL, plugin, VSCode extension, CI job, OAuth, PAT, secret, or env setup was not installed or configured."
        in scope_audit
    )
    assert (
        "not permission to perform external tool installation or L7 work inside the current task"
        in scope_audit
    )

    items = {item["id"]: item for item in matrix["objective_items"]}
    harness = items["OBJ-HARNESS-EXTERNAL-TOOLS"]
    assert harness["status"] == "partial"
    assert harness["design_gap_status"] == "L4_L6_closed_L7_feature_ticketed"
    evidence_artifacts = {
        evidence.get("artifact")
        for evidence in harness["evidence"]
        if isinstance(evidence, dict)
    }
    assert {
        str(HARNESS_EXTERNAL_TOOLS_L4_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_L5_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_L6_DOC.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_SCOPE_AUDIT.relative_to(REPO_ROOT)),
        str(HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)),
    }.issubset(evidence_artifacts)


def test_additional_improvement_discovery_is_web_backed_without_counting_as_closure() -> None:
    payload = yaml.safe_load(_read(ADDITIONAL_IMPROVEMENT_DISCOVERY_MANIFEST))

    assert payload["schema_version"] == "additional_improvement_discovery_v1"
    assert payload["status"] == "discovered_not_adopted"
    assert str(payload["updated"]) == "2026-06-10"
    assert payload["source_web_evidence_map"] == str(
        WEB_EVIDENCE_SOURCE_MAP_MANIFEST.relative_to(REPO_ROOT)
    )
    assert payload["discovery_boundary"]["candidates_discovered"] is True
    assert payload["discovery_boundary"]["plan_or_pr_adopted"] is False
    assert payload["discovery_boundary"]["implementation_done"] is False
    assert payload["discovery_boundary"]["gate_evidence_closed"] is False
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
    assert sources["OWASP-SAMM"]["official_url"] == "https://owaspsamm.org/model/"
    assert str(sources["OWASP-SAMM"]["verified_on"]) == "2026-06-10"
    assert "Governance" in sources["OWASP-SAMM"]["confirmed_focus"]
    assert sources["SLSA-1.2"]["confirmed_status"] == "Approved"
    assert str(sources["SLSA-1.2"]["verified_on"]) == "2026-06-10"
    assert "provenance" in sources["SLSA-1.2"]["confirmed_focus"]
    assert str(sources["OPENTELEMETRY-SIGNALS"]["confirmed_last_modified"]) == "2026-03-10"
    assert str(sources["OPENTELEMETRY-SIGNALS"]["verified_on"]) == "2026-06-10"
    assert "Traces" in sources["OPENTELEMETRY-SIGNALS"]["confirmed_focus"]
    assert str(sources["OPENSSF-SCORECARD"]["verified_on"]) == "2026-06-10"
    assert "auto-generating security score" in sources["OPENSSF-SCORECARD"]["confirmed_focus"]
    assert "JSON-RPC 2.0 base protocol" in sources["MCP-SPEC-2025-06-18"]["confirmed_focus"]
    assert "OAuth or PAT scope boundary" in sources["GITHUB-MCP-SERVER"]["confirmed_focus"]
    assert "semgrep scan" in sources["SEMGREP-CE"]["confirmed_focus"]
    assert "CodeQL database" in sources["GITHUB-CODEQL"]["confirmed_focus"]

    candidates = {item["id"]: item for item in payload["candidates"]}
    assert set(candidates) == {
        "IMP-SEC-MATURITY-SAMM-MAP",
        "IMP-SUPPLY-CHAIN-SLSA-PROVENANCE",
        "IMP-OBSERVABILITY-SIGNAL-TAXONOMY",
        "IMP-REPO-SECURITY-SCORECARD",
        "IMP-HARNESS-MCP-ADMISSION-GATE",
        "IMP-HARNESS-SEMGREP-CE-SAST",
        "IMP-HARNESS-CODEQL-IMPACT",
    }
    assert candidates["IMP-SUPPLY-CHAIN-SLSA-PROVENANCE"]["safety"][
        "infrastructure_change"
    ] is True
    assert candidates["IMP-REPO-SECURITY-SCORECARD"]["status"] == (
        "candidate_requires_confirmation"
    )
    assert candidates["IMP-OBSERVABILITY-SIGNAL-TAXONOMY"]["safety"][
        "schema_migration"
    ] is False
    assert candidates["IMP-HARNESS-MCP-ADMISSION-GATE"]["feature_plan"] == str(
        HARNESS_EXTERNAL_TOOLS_FEATURE_PLAN.relative_to(REPO_ROOT)
    )
    assert candidates["IMP-HARNESS-MCP-ADMISSION-GATE"]["safety"][
        "auth_or_pii_change"
    ] is True
    assert candidates["IMP-HARNESS-SEMGREP-CE-SAST"]["status"] == (
        "candidate_requires_confirmation"
    )
    assert candidates["IMP-HARNESS-CODEQL-IMPACT"]["status"] == (
        "candidate_requires_confirmation"
    )
    assert "CI workflow modification" in payload["non_goals_under_current_handover"]
    assert "MCP server installation or authentication setup" in payload[
        "non_goals_under_current_handover"
    ]
    assert "Semgrep or CodeQL installation" in payload["non_goals_under_current_handover"]


def test_web_evidence_source_map_links_official_sources_to_objectives_and_candidates() -> None:
    source_map = yaml.safe_load(_read(WEB_EVIDENCE_SOURCE_MAP_MANIFEST))
    objective_matrix = yaml.safe_load(_read(OBJECTIVE_EVIDENCE_MATRIX_MANIFEST))
    discovery = yaml.safe_load(_read(ADDITIONAL_IMPROVEMENT_DISCOVERY_MANIFEST))

    assert source_map["schema_version"] == "web_evidence_source_map_v1"
    assert source_map["status"] == "verified_current_scope_not_adopted"
    assert str(source_map["updated"]) == "2026-06-10"
    assert source_map["source_objective_matrix"] == str(
        OBJECTIVE_EVIDENCE_MATRIX_MANIFEST.relative_to(REPO_ROOT)
    )
    assert source_map["source_additional_improvement_discovery"] == str(
        ADDITIONAL_IMPROVEMENT_DISCOVERY_MANIFEST.relative_to(REPO_ROOT)
    )
    assert objective_matrix["source_web_evidence_map"] == str(
        WEB_EVIDENCE_SOURCE_MAP_MANIFEST.relative_to(REPO_ROOT)
    )
    assert discovery["source_web_evidence_map"] == str(
        WEB_EVIDENCE_SOURCE_MAP_MANIFEST.relative_to(REPO_ROOT)
    )

    objective_ids = {item["id"] for item in objective_matrix["objective_items"]}
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
        assert source["official_url"].startswith("https://")
        assert str(source["verified_on"]) == "2026-06-10"
        assert set(source["supports_objective_items"]).issubset(objective_ids)
        assert source["supports_objective_items"]
        assert set(source["supports_candidates"]).issubset(candidate_ids)
        assert source["current_scope_action"].endswith("evidence only")

    assert sources["ISO-12207-2026"]["confirmed"] == {
        "reference": "ISO/IEC/IEEE 12207:2026",
        "status": "Published",
        "edition": 2,
        "publication_date": "2026-04",
        "stage": "60.60",
        "focus": "software life cycle processes",
    }
    assert sources["ISO-29148-2018"]["confirmed"]["stage"] == "90.92"
    assert sources["ISO-29148-2018"]["confirmed"]["stage_meaning"] == "to be revised"
    assert sources["IEEE-P1012"]["confirmed"]["status"] == "Active PAR"
    assert str(sources["IEEE-P1012"]["confirmed"]["par_approval"]) == "2026-03-26"
    assert sources["NIST-SP-800-218"]["confirmed"]["version"] == "1.1"
    assert str(sources["NIST-SP-800-218"]["confirmed"]["date_published"]) == "2022-02"
    assert "Governance" in sources["OWASP-SAMM"]["confirmed"]["functions"]
    assert sources["SLSA-1.2"]["confirmed"]["status"] == "Approved"
    assert "provenance" in sources["SLSA-1.2"]["confirmed"]["focus"]
    assert str(sources["OPENTELEMETRY-SIGNALS"]["confirmed"]["last_modified"]) == "2026-03-10"
    assert "Traces" in sources["OPENTELEMETRY-SIGNALS"]["confirmed"]["signals"]
    assert "auto-generating security score" in sources["OPENSSF-SCORECARD"]["confirmed"]["focus"]
    assert sources["MCP-SPEC-2025-06-18"]["confirmed"]["base"] == "JSON-RPC 2.0"
    assert "tools" in sources["MCP-SPEC-2025-06-18"]["confirmed"]["components"]
    assert sources["GITHUB-MCP-SERVER"]["confirmed"]["provider"] == "GitHub"
    assert "OAuth or PAT scope review" in sources["GITHUB-MCP-SERVER"]["confirmed"][
        "prerequisites"
    ]
    assert sources["SEMGREP-CE"]["confirmed"]["command"] == "semgrep scan"
    assert sources["GITHUB-CODEQL"]["confirmed"]["product"] == "CodeQL"

    candidate_support = {
        candidate_id
        for source in sources.values()
        for candidate_id in source["supports_candidates"]
    }
    assert candidate_support == candidate_ids
    completion_boundary = source_map["completion_boundary"]
    assert completion_boundary["web_sources_verified"] is True
    assert str(completion_boundary["refreshed_on"]) == "2026-06-10"
    assert completion_boundary["source_map_is_goal_completion"] is False
    assert completion_boundary["candidate_evidence_is_adoption"] is False
    assert completion_boundary["infrastructure_affecting_candidates_require_confirmation"] is True
    assert completion_boundary["goal_complete_allowed"] is False


def test_ci_gate_surface_audit_separates_local_gate_from_full_flow_completion() -> None:
    payload = yaml.safe_load(_read(CI_GATE_SURFACE_AUDIT_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))
    live_deferred_pairs = _live_strict_deferred_pairs()
    strict_full_flow = payload["local_gate_surface"]["strict_full_flow"]

    assert payload["schema_version"] == "ci_gate_surface_audit_v1"
    assert payload["status"] == "ci_detector_gate_connected_full_flow_still_deferred"
    assert payload["source_goal_audit"] == (
        "docs/v2/L7-test-design/goal-completion-audit.yaml"
    )
    assert payload["source_right_arm_request"] == (
        "docs/v2/L7-test-design/right-arm-execution-gates-handover-request.yaml"
    )
    assert payload["source_ci_equivalent_readiness"] == (
        "docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml"
    )
    assert payload["local_gate_surface"]["doctor_gate"] == {
        "command": "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json",
        "pass": 33,
        "fail": 0,
        "warn": 104,
        "interpretation": "Local developer full-doctor surface; pass/warn are advisory snapshots and the contracted judgment is fail=0. Not used as the CI Required check (project-state dependent; see ci_surface).",
    }
    assert payload["local_gate_surface"]["vg_overview_default"]["overall_clean"] is True
    assert payload["local_gate_surface"]["vg_overview_default"]["focus"] == "L6"
    assert strict_full_flow["derived_from"] == "strict_vg_overview"
    assert strict_full_flow["last_verified_command"] == vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    assert strict_full_flow["command"] == vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    assert strict_full_flow["overall_clean"] is False
    assert strict_full_flow["deferred_count"] == len(live_deferred_pairs)
    assert strict_full_flow["deferred_gates"] == _live_strict_deferred_gate_ids()
    assert strict_full_flow["interpretation"] == "Full-flow completion is not achieved."
    assert payload["local_gate_surface"]["push_gate_surface"]["gate_id"] == "G-vg-overview"
    assert payload["ci_surface"] == {
        "required_for_goal_completion": True,
        "ci_or_equivalent_connected": True,
        "reason": "detector-gate runs helix doctor check_vg_overview --gate --json in CI (project-state independent), while strict full-flow carry remains deferred.",
        "ci_detector_gate": {
            "command": "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json",
            "gate_basis": "vg_overview.overall_clean",
            "project_state_independent": True,
            "exit_0_when_clean": True,
        },
        "required_next": [
            "Keep L6 focus gate green without hiding strict full-flow deferred gates.",
            "Require strict full-flow overall_clean=true after the remaining G9/G12/G14 pass while preserving G8 closure.",
            "Register detector-gate as a GitHub Required check in branch protection.",
            "Record CI/equivalent run evidence in PLAN/PR/gate evidence and HELIX DB feedback loop.",
        ],
    }
    assert payload["completion_boundary"] == {
        "local_doctor_gate_pass_is_goal_completion": False,
        "push_gate_documentation_is_ci_completion": False,
        "strict_full_flow_required_before_completion": True,
        "right_arm_deferred_gates_must_close": True,
    }
    assert payload["safety"] == {
        "schema_migration": False,
        "auto_apply": False,
        "writes_detector_or_gate": False,
        "infrastructure_change": False,
        "requires_human_confirmation_for_ci_change": True,
    }
    requirement = {
        item["id"]: item for item in goal_audit["requirements"]
    }["REQ-WORKFLOW-AUTOMATION-REVIEW"]
    assert requirement["status"] == "partial"
    assert "docs/v2/L7-test-design/ci-gate-surface-audit.yaml" in requirement[
        "evidence"
    ]


def test_ci_workflow_pins_detector_gate_contract() -> None:
    payload = yaml.safe_load(_read(CI_WORKFLOW))
    jobs = payload["jobs"]

    assert "detector-gate" in jobs
    detector_gate = jobs["detector-gate"]
    assert detector_gate["permissions"] == {"contents": "read"}

    steps = detector_gate["steps"]
    run_steps = [step for step in steps if "run" in step]
    run_scripts = "\n".join(step["run"] for step in run_steps)

    # CI gate は VG-overview のみを isolated に fail-close 評価する subcommand 形式を使う。
    # `helix doctor --gate` (全体) は .helix/ project-state に依存し fresh checkout で常時 red
    # になるため使わない (P0)。
    assert "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --gate --json" in run_scripts
    assert "helix doctor --gate --json" not in run_scripts
    assert "--strict-full-flow" not in run_scripts
    assert "--strict-vmodel-pair-freeze" not in run_scripts
    # PyYAML 等 vg_overview の依存を clean な setup-python 環境へ明示 install する (P1)。
    assert "pip install" in run_scripts
    assert "requirements-dev.txt" in run_scripts
    assert "HELIX_CHANGED_FILES" in run_scripts
    assert "git fetch origin ${{ github.base_ref }}" in run_scripts
    assert "PATH=\"$PWD/cli:$PATH\"" in run_scripts
    assert any(step.get("if") == "github.event_name == 'pull_request'" for step in steps)
    # PR の merge-base 到達性を確保し ratchet detector が available_empty に degrade しない
    # ようにする (F4: changed-files が空だと ratchet が vacuous clean になる)。
    checkout = next(
        step for step in steps if str(step.get("uses", "")).startswith("actions/checkout")
    )
    assert checkout.get("with", {}).get("fetch-depth") == 0
    # DF-FCCI-CI-RATCHET-PUSH: push event でも changed-files を注入し、ratchet detector が
    # HELIX_CHANGED_FILES 未設定 → available_empty に degrade して vacuous clean (fail-open)
    # になるのを防ぐ。push event は merge-base ではなく event.before..sha の diff range を使う。
    push_steps = [
        step
        for step in steps
        if step.get("if") == "github.event_name == 'push'" and "run" in step
    ]
    assert push_steps, (
        "detector-gate must export HELIX_CHANGED_FILES on push events so the ratchet "
        "detectors are not vacuously clean (DF-FCCI-CI-RATCHET-PUSH)."
    )
    push_scripts = "\n".join(step["run"] for step in push_steps)
    assert "HELIX_CHANGED_FILES" in push_scripts
    assert "${{ github.event.before }}" in push_scripts
    assert "${{ github.sha }}" in push_scripts

    # Process §4.1 ② / C-2: ruff-shellcheck-advisory job は advisory-only。外部 tool の
    # install/execute はこの job 内でのみ許可 (continue-on-error / Required 非対象 / 他 job の
    # needs に非依存 / fail-close gate へ未接続)。required・fail-close 化は forbidden_now
    # (latest_user_boundary)。requirements-dev.txt に ruff を入れない (test/detector-gate の
    # dev install へ波及して advisory 境界が崩れるのを防ぐ)。
    assert "ruff-shellcheck-advisory" in jobs
    advisory = jobs["ruff-shellcheck-advisory"]
    assert advisory.get("continue-on-error") is True
    assert advisory.get("permissions") == {"contents": "read"}
    assert "needs" not in advisory
    advisory_run = "\n".join(step["run"] for step in advisory["steps"] if "run" in step)
    assert "helix doctor check_coding_rule_lint --json" in advisory_run
    assert "--gate" not in advisory_run
    assert "check_vg_overview" not in advisory_run
    assert "helix push" not in advisory_run
    assert "--strict-full-flow" not in advisory_run
    assert "ruff-shellcheck-advisory" not in (detector_gate.get("needs") or [])
    assert "ruff-shellcheck-advisory" not in (jobs["test"].get("needs") or [])
    req_lines = [
        line.split("#", 1)[0].strip()
        for line in _read(REPO_ROOT / "requirements-dev.txt").splitlines()
    ]
    assert not any(line.lower().startswith("ruff") for line in req_lines if line)


def test_ci_equivalent_gate_readiness_defines_bundle_without_connecting_completion() -> None:
    payload = yaml.safe_load(_read(CI_EQUIVALENT_READINESS_MANIFEST))
    goal_audit = yaml.safe_load(_read(GOAL_COMPLETION_AUDIT_MANIFEST))

    assert payload["schema_version"] == "ci_equivalent_gate_readiness_v1"
    assert payload["status"] == "ready_to_connect_not_connected"
    assert payload["readiness_boundary"] == {
        "equivalent_surface_defined": True,
        "ci_or_equivalent_connected": False,
        "required_run_aggregation_implemented": False,
        "strict_full_flow_clean": False,
        "goal_complete_allowed": False,
        "reason": "The required command set and evidence contract are defined, but no CI or equivalent required runner has adopted and recorded the bundle.",
    }
    bundle = payload["required_gate_bundle"]
    assert bundle["name"] == "helix-full-flow-required-gate"
    assert bundle["trigger_policy"] == {
        "local_equivalent": "allowed",
        "ci_required": "allowed_after_human_confirmation",
        "current_scope_connects_ci": False,
    }
    command_ids = [item["id"] for item in bundle["commands"]]
    assert command_ids == [
        "requirement_drift_l6",
        "l0_l14_contract_pytest",
        "l0_l14_contract_bats",
        "feedback_loop_bats",
        "strict_full_flow",
    ]
    strict_command = bundle["commands"][-1]
    assert strict_command["command"] == (
        "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json"
    )
    assert strict_command["required_assertions"] == [
        "overall_clean=true",
        "deferred_count=0",
        "deferred_gates=[]",
    ]
    assert {
        "run_id",
        "runner_type",
        "command_id",
        "exit_code",
        "parsed_assertions",
        "helix_db_event_id",
    }.issubset(set(payload["evidence_contract"]["required_record_fields"]))
    assert payload["safety"] == {
        "schema_migration": False,
        "infrastructure_change": False,
        "ci_workflow_change": False,
        "external_api_or_credentials": False,
        "destructive_data_operation": False,
        "requires_human_confirmation_for_ci_workflow_change": True,
    }
    assert payload["completion_boundary"] == {
        "readiness_manifest_is_goal_completion": False,
        "local_command_pass_without_aggregation_is_ci_completion": False,
        "ci_or_equivalent_connected": False,
        "all_right_arm_gates_must_pass_first": True,
    }
    requirement = {
        item["id"]: item for item in goal_audit["requirements"]
    }["REQ-WORKFLOW-AUTOMATION-REVIEW"]
    assert "docs/v2/L7-test-design/ci-equivalent-gate-readiness.yaml" in requirement[
        "evidence"
    ]


def test_process_roadmap_completion_audit_covers_goal_requirements() -> None:
    text = _read(PROCESS_ROADMAP)

    expected_terms = (
        "Goal「要件定義漏れ洗い出し / L1〜L6 設計・テスト設計バランス / Codex-guard 差分 / 自動登録・検出・改善 loop」",
        "| 指定 L0〜L14 flow へ完全対応 | 部分達成 |",
        "| L1〜L6 の設計 / テスト設計バランス | machine-clean |",
        "| L4↔L9 の総合設計 pair | semantic evidence 付きで detector clean / G9 実行 carry |",
        "| L7 単体実装 / 実施 / coverage closure | 達成（advisory） |",
        "| HELIX gate state として L6 まで通過 | 達成（static gate） |",
        "`HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json` 実測は pass=33 / fail=0 / warn=103",
        "`VG-overview pre-push` advisory なし",
        "| requirement_drift detector | MVP 実装 / fail-close 接続済み / L6 drift 0 |",
        "| ClaudeCode では効くが Codex で効かない guard | 達成 |",
        "| HELIX DB 自動登録 / トラブル検出 / 改善 feedback loop | 部分達成 / gate 未接続 carry |",
        "| Web 検索使用 | 達成 |",
    )
    for term in expected_terms:
        assert term in text


def test_process_roadmap_keeps_goal_completion_guard_active_until_full_flow_closes() -> None:
    text = _read(PROCESS_ROADMAP)

    expected_terms = (
        "Completion guard",
        "Goal 全体を complete 扱いしてよい条件ではない",
        "Goal completion は、少なくとも次を満たすまで禁止する",
        "`helix doctor check_vg_overview --strict-full-flow --json` の `overall_clean=true`",
        "G8 / G9 / G12 / G14 の execution gate が implemented かつ pass",
        "`helix doctor --gate` / `G-vg-overview` が CI または同等の自動 gate surface に接続済み",
        "`ui_absent` waiver が継続妥当",
        "`plan_candidates` / `pr_candidates` が生成されるだけでなく",
        "goal は active のまま扱う",
    )
    for term in expected_terms:
        assert term in text


def test_live_vg_overview_matches_completion_guard_deferred_gates() -> None:
    full_gap = yaml.safe_load(_read(FULL_OBJECTIVE_GAP_STATUS))
    default_report = vg_overview.collect_vg_overview(REPO_ROOT, execute_g7_tests=False)
    strict_report = vg_overview.collect_vg_overview(
        REPO_ROOT,
        strict_full_flow=True,
        execute_g7_tests=False,
    )
    live_deferred_pairs = _live_strict_deferred_pairs()

    assert default_report["vg_overview"]["overall_clean"] is True

    strict_vg = strict_report["vg_overview"]
    assert strict_vg["overall_clean"] is False
    assert strict_vg["full_flow_execution"]["enforced"] is True
    assert strict_vg["full_flow_execution"]["deferred_count"] == len(live_deferred_pairs)
    assert _live_strict_deferred_pair_map() == {
        "L4-L9": "G9",
        "L3-L12": "G12",
        "L1-L14": "G14",
    }
    ledger_right_arm = full_gap["right_arm_execution_boundaries"]
    assert ledger_right_arm["strict_full_flow_current_derived_from"] == "strict_vg_overview"
    assert ledger_right_arm["strict_full_flow_current_last_verified_command"] == (
        vg_overview.STRICT_FULL_FLOW_VERIFY_COMMAND
    )
    live_by_gate = {
        str(item["gate_id"]): item for item in live_deferred_pairs
    }
    ledger_by_gate = {
        item["gate_id"]: item for item in ledger_right_arm["deferred_gates"]
    }
    assert list(ledger_by_gate) == ledger_right_arm["deferred_gate_contract"][
        "deferred_gate_ids_must_equal"
    ]
    assert set(live_by_gate) == set(ledger_by_gate)
    for gate_id, ledger_gate in ledger_by_gate.items():
        live_gate = live_by_gate[gate_id]
        for field in (
            "gate_id",
            "pair",
            "source_layer",
            "target_layer",
            "target",
            "reason",
            "next_action",
            "reference",
        ):
            assert ledger_gate[field] == live_gate[field], (gate_id, field)
        pair_status = strict_vg["pair_status"][ledger_gate["pair"]]
        assert ledger_gate["status"] == pair_status["status"], gate_id
        assert ledger_gate["clean"] is pair_status["clean"], gate_id
        assert ledger_gate["required_before_full_goal"].endswith(
            "_gate_pass"
        ), gate_id
    assert ledger_right_arm["strict_full_flow_current_overall_clean"] is strict_vg[
        "overall_clean"
    ]
    assert ledger_right_arm["deferred_gate_contract"][
        "deferred_gate_count"
    ] == strict_vg["full_flow_execution"]["deferred_count"]


def test_live_default_vg_overview_is_l6_focus_not_full_flow_completion() -> None:
    report = vg_overview.collect_vg_overview(REPO_ROOT, execute_g7_tests=False)
    vg = report["vg_overview"]
    full_flow = vg["full_flow_execution"]

    assert vg["overall_clean"] is True
    assert full_flow["clean"] is False
    assert full_flow["enforced"] is False
    assert full_flow["deferred_count"] == 3
    assert {
        item["pair"]: item["gate_id"]
        for item in full_flow["deferred_pairs"]
    } == {
        "L4-L9": "G9",
        "L3-L12": "G12",
        "L1-L14": "G14",
    }


def test_live_requirement_drift_proves_l6_requirement_design_closure() -> None:
    report = vg_overview.collect_vg_overview(REPO_ROOT, execute_g7_tests=False)
    requirement_drift = report["vg_overview"]["required_clean"]["requirement_drift"]

    assert requirement_drift["clean"] is True
    assert requirement_drift["focus"] == "L6"
    assert requirement_drift["requirements"] == 31
    assert requirement_drift["design_links"] == 31
    assert requirement_drift["finding_count"] == 0
    assert requirement_drift["advisory_count"] == 0
    assert requirement_drift["waived_count"] == 0


def test_live_l1_l6_design_and_test_design_granularity_balance_is_clean() -> None:
    report = trace_symmetry.collect_trace_symmetry(REPO_ROOT)
    pairs = report["pairs"]
    pair_map = yaml.safe_load(_read(L1_L6_PAIR_BALANCE_MAP))
    mapped_pairs = {item["trace_pair"]: item for item in pair_map["pairs"]}
    expected_layers = {
        "L1-L14": ("L1", "L14"),
        "L3-L12": ("L3", "L12"),
        "L4-L9": ("L4", "L9"),
        "L5-L8": ("L5", "L8"),
        "L6-L7": ("L6", "L7"),
    }

    for pair_name, (design_layer, test_layer) in expected_layers.items():
        pair = pairs[pair_name]
        assert pair["design_layer"] == design_layer
        assert pair["test_layer"] == test_layer
        assert pair["coverage_pct"] == 100.0
        assert pair["uncovered_req"]["count"] == 0
        assert pair["orphan_test"]["count"] == 0
        assert pair["missing_pair"]["count"] == 0
        assert pair["missing_pair_frontmatter"]["count"] == 0
        assert pair["wrong_layer_pair"]["count"] == 0
        assert pair["duplicate_id"]["count"] == 0

        mapped_metrics = mapped_pairs[pair_name]["metrics"]
        assert mapped_metrics.get("coverage_pct", mapped_metrics.get("framework_trace_coverage_pct")) == pair[
            "coverage_pct"
        ]
        assert mapped_metrics.get(
            "balance_ratio", mapped_metrics.get("framework_trace_balance_ratio")
        ) == pair["balance_ratio"]
        assert mapped_metrics.get(
            "missing_pair_count", mapped_metrics.get("framework_missing_pair_count")
        ) == pair["missing_pair"]["count"]
        if "orphan_test_count" in mapped_metrics:
            assert mapped_metrics["orphan_test_count"] == pair["orphan_test"]["count"]
        if "excluded_with_reason_count" in mapped_metrics:
            assert mapped_metrics["excluded_with_reason_count"] == pair[
                "excluded_with_reason"
            ]["count"]
        if "semantic_excluded_orphan_count" in mapped_metrics:
            assert mapped_metrics["semantic_excluded_orphan_count"] == pair[
                "semantic_excluded_orphan"
            ]["count"]

    assert pairs["L1-L14"]["balance_ratio"] == 1.0
    assert pairs["L3-L12"]["balance_ratio"] == 1.0
    assert pairs["L5-L8"]["balance_ratio"] == 1.0
    assert pairs["L6-L7"]["balance_ratio"] == 1.0
    assert pairs["L4-L9"]["balance_ratio"] == 0.67
    assert pairs["L4-L9"]["semantic_excluded_orphan"]["count"] == 18


def test_doctor_requirement_drift_cli_matches_vg_overview_l6_focus() -> None:
    cli_env = {
        **os.environ,
        "HELIX_HOME": str(REPO_ROOT),
        "HELIX_PROJECT_ROOT": str(REPO_ROOT),
    }
    drift_result = subprocess.run(
        ["helix", "doctor", "check_requirement_drift", "--json"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=cli_env,
    )
    vg_result = subprocess.run(
        ["helix", "doctor", "check_vg_overview", "--json"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env={**cli_env, "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1"},
    )

    drift = json.loads(drift_result.stdout)
    vg_required = json.loads(vg_result.stdout)["vg_overview"]["required_clean"][
        "requirement_drift"
    ]

    assert drift["clean"] is True
    assert drift["blocking_clean"] is True
    assert drift["focus"] == "L6"
    assert drift["stale_check_enabled"] is False
    assert drift["summary"]["requirements"] == vg_required["requirements"] == 31
    assert drift["summary"]["design_links"] == vg_required["design_links"] == 31
    assert drift["summary"]["blocking_findings"] == vg_required["finding_count"] == 0
    assert drift["summary"]["advisory_findings"] == vg_required["advisory_count"] == 0
    assert len(drift["findings"]["waived_with_reason"]) == vg_required["waived_count"] == 0


def test_harness_feedback_loop_cli_surfaces_full_flow_carry_as_candidates() -> None:
    cli_env = {
        **os.environ,
        "HELIX_HOME": str(REPO_ROOT),
        "HELIX_PROJECT_ROOT": str(REPO_ROOT),
        "HELIX_DB_PATH": str(REPO_ROOT / ".helix/helix.db"),
        "HELIX_DOCTOR_SKIP_EXEC_TESTS": "1",
    }
    result = subprocess.run(
        ["helix", "harness", "feedback-loop", "--json", "--days", "30"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
        env=cli_env,
    )

    payload = json.loads(result.stdout)
    learning_kinds = {item["kind"] for item in payload["learning_candidates"]}
    plan_candidate_types = {item["candidate_type"] for item in payload["plan_candidates"]}
    pr_candidate_types = {item["candidate_type"] for item in payload["pr_candidates"]}
    deferred_pairs = {
        item["pair"]: item["gate_id"] for item in payload["vg_overview"]["deferred_pairs"]
    }
    adoption_manifest = yaml.safe_load(_read(RIGHT_ARM_GATE_ADOPTION_MANIFEST))
    manifest_deferred_pairs = {
        item["pair"]: item["gate_id"] for item in adoption_manifest["gates"]
    }
    manifest_plan_ids = {
        item["gate_id"]: item["plan_id"] for item in adoption_manifest["gates"]
    }
    deferred_learning_pairs = {
        (item["pair"], item["gate_id"])
        for item in payload["learning_candidates"]
        if item["kind"] == "full_flow_deferred_execution_gate"
    }
    deferred_pr_summaries = {
        item["change_summary"][0]
        for item in payload["pr_candidates"]
        if item.get("source_pattern_key") == "vg_overview:full_flow_deferred_execution_gate"
    }
    expected_live_deferred = {
        "L4-L9": "G9",
        "L3-L12": "G12",
        "L1-L14": "G14",
    }
    expected_manifest_deferred = {
        "L5-L8": "G8",
        **expected_live_deferred,
    }

    assert payload["schema_version"] == "helix_harness_feedback_loop_snapshot_v1"
    assert "plan_candidates" in payload
    assert "plan_draft_candidates" not in payload
    assert payload["vg_overview"]["available"] is True
    assert payload["vg_overview"]["enforced"] is True
    assert payload["vg_overview"]["deferred_count"] == 3
    assert payload["vg_overview"]["not_applicable_count"] == 1
    assert deferred_pairs == expected_live_deferred
    assert manifest_deferred_pairs == expected_manifest_deferred
    assert manifest_plan_ids == {
        "G8": "PLAN-G8-INTEGRATION-EXECUTION-GATE",
        "G9": "PLAN-G9-SYSTEM-EXECUTION-GATE",
        "G12": "PLAN-G12-ACCEPTANCE-EXECUTION-GATE",
        "G14": "PLAN-G14-OPERATIONAL-LEARNING-GATE",
    }
    assert deferred_learning_pairs == set(expected_live_deferred.items())
    for pair, gate_id in expected_live_deferred.items():
        assert any(pair in summary and gate_id in summary for summary in deferred_pr_summaries)
    assert "full_flow_deferred_execution_gate" in learning_kinds
    assert "not_applicable_pair_waiver" in learning_kinds
    assert "plan" in plan_candidate_types
    assert "pr" in pr_candidate_types
    assert payload["safety"]["schema_migration"] is False
    assert payload["safety"]["auto_apply"] is False
    assert payload["safety"]["writes_detector_or_gate"] is False


def test_gate_surface_contract_keeps_vg_overview_connected_to_doctor_and_push() -> None:
    ai_harness = _read(AI_HARNESS_DOC)
    push_doc = _read(PUSH_DOC)
    doctor_bats = _read(HELIX_DOCTOR_JSON_BATS)

    assert "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json" in ai_harness
    assert "`helix doctor --gate` は VG-overview pre-push を fail-close 評価する" in ai_harness
    assert "`helix push --gate` では `G-vg-overview`" in ai_harness
    assert "G7 anchor / registry / trace / L6 requirement drift" in ai_harness
    assert "| `G-vg-overview` | VG-overview pre-push |" in push_doc
    assert "overall_clean=true anchored=88/88 exec_pass=88 missing=0 unanchored=0" in push_doc
    assert '@test "helix-doctor --gate --json matches VG-overview pre-push cleanliness"' in doctor_bats
    assert "VG-overview pre-push" in doctor_bats
    assert "has_vg=any" in doctor_bats


def test_l1_l6_nfr_derivation_coverage_keeps_requirements_deriver_obligations_closed() -> None:
    payload = yaml.safe_load(
        _read(REPO_ROOT / "docs/v2/audit/2026-06-13-l1-l6-nfr-derivation-coverage.yaml")
    )

    assert payload["schema_version"] == "l1_l6_nfr_derivation_coverage_v1"
    assert payload["status"] == "current_scope_l1_l6_nfr_derivation_covered"
    assert payload["boundary"] == {
        "l7_work_requested_by_user": False,
        "l7_work_requires_feature_ticket": True,
        "audit_is_l7_work": False,
        "audit_is_implementation_evidence": False,
        "l7_test_design_created_by_this_audit": False,
        "l7_implementation_done": False,
        "unit_test_execution_done": False,
        "coverage_closure_done": False,
        "helix_db_write_performed": False,
        "schema_migration_done": False,
        "external_tool_installed": False,
        "external_tool_executed": False,
        "ci_or_equivalent_connected": False,
        "goal_complete_allowed": False,
    }
    assert payload["summary"] == {
        "requirements_deriver_signals_checked": 9,
        "requirements_deriver_signals_with_l1_or_l3_coverage": 9,
        "iso_25010_characteristics_checked": 9,
        "iso_25010_characteristics_covered": 9,
        "l1_nfr_count": 23,
        "l3_nfr_count": 27,
        "l3_extension_count": 4,
        "l3_rederived_characteristics": 3,
        "current_scope_blocking_findings": 0,
        "l7_artifacts_created_by_this_audit": 0,
    }

    signal_rows = payload["signal_coverage_rows"]
    iso_rows = payload["iso_25010_coverage"]
    assert len(signal_rows) == payload["summary"]["requirements_deriver_signals_checked"]
    assert len(iso_rows) == payload["summary"]["iso_25010_characteristics_checked"]
    assert {row["signal_id"] for row in signal_rows} == {
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
    assert {row["characteristic"] for row in iso_rows} == {
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
    assert {
        row["characteristic"] for row in iso_rows if row["coverage"] == "L3 rederived"
    } == {"Functional Suitability", "Interaction Capability", "Safety"}
    assert all(row["l1_l3_coverage"] for row in signal_rows)
    assert all(row["evidence"] for row in iso_rows)
    assert payload["requirements_deriver_policy"]["missing_signal_reopens_l1_or_l3"] is True
    assert payload["completion_denial"]["reason"].startswith(
        "This audit proves L1/L3 NFR derivation coverage"
    )
