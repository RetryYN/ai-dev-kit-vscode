# HELIX V3 — Personal Edition Schema Contract

> status: L5/L6 design contract
> scope: personal-edition projection tables only
> runtime note: current `cli/lib/v3/schema` implementation may still be 58-table. This document freezes the L0-L6 design contract for the 4 HELIX personal projection tables before L7 implementation.
> upstream: [schema-registry](schema-registry.md), [L5 detailed design](../L0-L14/L5-detailed-design.md), [personal-edition workflows](personal-edition-workflows.md)

## 1. Contract Boundary

The following tables are HELIX personal-edition projection tables:

- `template_catalog`
- `doc_coverage`
- `prompt_interpretations`
- `learning_candidates`

They are design-level DB contracts, not an applied migration in this document. L7 implementation must add them through the single C1 registry, bump the V3 `SCHEMA_VERSION`, generate DDL from registry only, and add tests before runtime use.

Common invariants:

- `kind = projection`
- rebuild deletes and reprojects rows from source artifacts
- no raw template bodies, raw provider transcripts, secrets, PII, credentials, or license-protected downloadable content are stored
- all external terms pass through [domain-glossary](domain-glossary.md)
- all rows have `source_hash` and `projected_at`

## 2. `template_catalog`

Purpose: normalized external/internal design template metadata and required-section coverage seeds.

| Column | Type | Required | implementation_status | Meaning |
|---|---|---|---|
| `template_id` | TEXT PK | yes | L7-carry | Stable id, e.g. `TPL-SEED-001:requirements`. |
| `seed_id` | TEXT | yes | L7-carry | Seed source id from [template-catalog-seeds](template-catalog-seeds.md). |
| `source_url` | TEXT | yes | L7-carry | Source URL. |
| `source_label` | TEXT | yes | L7-carry | `official`, `vendor`, `secondary`, `community`, or `internal`. |
| `source_kind` | TEXT | yes | L7-carry | `external_web`, `external_repo`, or `internal_doc`. |
| `doc_kind` | TEXT | yes | L7-carry | HELIX-normalized document kind. |
| `layers` | TEXT | yes | L7-carry | Comma-separated Forward layers or JSON array in implementation. |
| `pair_test_kind` | TEXT | no | L7-carry | Required paired test design kind. |
| `normalized_sections` | TEXT | yes | L7-carry | JSON array of abstract required section keys. |
| `quality_rules` | TEXT | yes | L7-carry | JSON array of quality rule keys. |
| `freshness_status` | TEXT | yes | L7-carry | `checked`, `dated`, `undated`, or `needs_review`. |
| `last_checked` | TEXT | yes | L7-carry | ISO date. |
| `license_review` | TEXT | yes | L7-carry | `not_required_for_metadata`, `required_before_body_use`, or `unknown`. |
| `provenance_hash` | TEXT | yes | L7-carry | Hash of normalized source metadata, not body content. |
| `source_hash` | TEXT | yes | L7-carry | Projection source hash. |
| `projected_at` | TEXT | yes | L7-carry | Projection timestamp. |

Identity:

- logical key: (`template_id`)
- stale key: (`provenance_hash`, `source_hash`)
- delete scope: source seed removed

Indexes:

- `idx_template_catalog_doc_layer` on (`doc_kind`, `layers`)
- `idx_template_catalog_seed` on (`seed_id`)

## 3. `doc_coverage`

Purpose: derived coverage requirements from templates, artifacts, V-model pairs, and current subject ids.

| Column | Type | Required | implementation_status | Meaning |
|---|---|---|---|---|
| `coverage_id` | TEXT PK | yes | L7-carry | Stable id from `layer:doc_kind:subject_id:section_key`. |
| `layer` | TEXT | yes | L7-carry | Forward layer. |
| `doc_kind` | TEXT | yes | L7-carry | Required document kind. |
| `subject_id` | TEXT | yes | L7-carry | Requirement, component, module, function, plan, or artifact id. |
| `required_section` | TEXT | yes | L7-carry | Required normalized section key. |
| `pair_test_kind` | TEXT | no | L7-carry | Required V-model test-design pair. |
| `required_by_template_id` | TEXT | yes | L7-carry | Template catalog id that produced the requirement. |
| `artifact_id` | TEXT | no | L7-carry | Matching artifact when present. |
| `coverage_status` | TEXT | yes | L7-carry | `covered`, `missing`, `partial`, `waived`, or `blocked`. |
| `waiver_reason` | TEXT | no | L7-carry | Required when status is `waived`. |
| `finding_id` | TEXT | no | L7-carry | Finding emitted for gap. |
| `source_hash` | TEXT | yes | L7-carry | Projection source hash. |
| `projected_at` | TEXT | yes | L7-carry | Projection timestamp. |

Identity:

- logical key: (`layer`, `doc_kind`, `subject_id`, `required_section`)
- stale key: (`source_hash`, `artifact_id`, `coverage_status`)
- delete scope: template requirement or subject removed

Indexes:

- `idx_doc_coverage_subject` on (`subject_id`, `coverage_status`)
- `idx_doc_coverage_layer_kind` on (`layer`, `doc_kind`, `coverage_status`)

## 4. `prompt_interpretations`

Purpose: multiple-viewpoint prompt interpretation before PLAN execution.

| Column | Type | Required | implementation_status | Meaning |
|---|---|---|---|---|
| `interpretation_id` | TEXT PK | yes | L7-carry | Stable id from `prompt_id:viewpoint`. |
| `prompt_id` | TEXT | yes | L7-carry | Prompt or handover input id. |
| `viewpoint` | TEXT | yes | L7-carry | `scope`, `acceptance`, `risk`, `test`, `doc`, `escalation`, or `subagent`. |
| `summary` | TEXT | yes | L7-carry | Redacted interpretation summary. |
| `risk_level` | TEXT | yes | L7-carry | `none`, `low`, `medium`, `high`, or `critical`. |
| `required_layer` | TEXT | no | L7-carry | Forward layer affected by this viewpoint. |
| `required_doc_kind` | TEXT | no | L7-carry | Document kind required by interpretation. |
| `required_test_kind` | TEXT | no | L7-carry | Test-design kind required by interpretation. |
| `escalation_signal` | TEXT | no | L7-carry | §10 signal when present. |
| `recommended_reviewer` | TEXT | no | L7-carry | Role recommended by deterministic signal. |
| `conflict_status` | TEXT | yes | L7-carry | `none`, `conflict`, `ambiguous`, `resolved`, or `blocked`. |
| `finding_id` | TEXT | no | L7-carry | Finding created for unresolved issue. |
| `source_hash` | TEXT | yes | L7-carry | Projection source hash. |
| `projected_at` | TEXT | yes | L7-carry | Projection timestamp. |

Identity:

- logical key: (`prompt_id`, `viewpoint`)
- stale key: (`source_hash`, `summary`, `conflict_status`)
- delete scope: source prompt/PLAN removed

Indexes:

- `idx_prompt_interpretations_prompt` on (`prompt_id`, `viewpoint`)
- `idx_prompt_interpretations_escalation` on (`escalation_signal`, `conflict_status`)

## 5. `learning_candidates`

Purpose: controlled improvement candidates derived from findings, reviews, tests, and postmortems.

| Column | Type | Required | implementation_status | Meaning |
|---|---|---|---|---|
| `candidate_id` | TEXT PK | yes | L7-carry | Stable candidate id. |
| `candidate_kind` | TEXT | yes | L7-carry | `plan_draft`, `rule_candidate`, `template_gap`, `debt_item`, or `runbook_update`. |
| `source_event_kind` | TEXT | yes | L7-carry | `finding`, `review`, `test_result_event`, `postmortem`, or `gate_run`. |
| `source_event_id` | TEXT | yes | L7-carry | Source row or artifact id. |
| `source_event_hash` | TEXT | yes | L7-carry | Source evidence hash. |
| `summary` | TEXT | yes | L7-carry | Redacted candidate summary. |
| `affected_layer` | TEXT | no | L7-carry | Forward layer affected by promotion. |
| `forward_return` | TEXT | no | L7-carry | Required unless discarded. |
| `discard_reason` | TEXT | no | L7-carry | Required when not returned to Forward. |
| `promotion_status` | TEXT | yes | L7-carry | `candidate`, `promoted`, `deferred`, `discarded`, or `blocked`. |
| `review_evidence_id` | TEXT | no | L7-carry | Review evidence for promotion/discard. |
| `created_at` | TEXT | yes | L7-carry | Creation timestamp. |
| `source_hash` | TEXT | yes | L7-carry | Projection source hash. |
| `projected_at` | TEXT | yes | L7-carry | Projection timestamp. |

Identity:

- logical key: (`candidate_id`)
- stale key: (`source_event_hash`, `promotion_status`, `forward_return`, `discard_reason`)
- delete scope: source event removed

Indexes:

- `idx_learning_candidates_source` on (`source_event_kind`, `source_event_id`)
- `idx_learning_candidates_status` on (`promotion_status`, `candidate_kind`)

## 6. L7 Implementation Acceptance

Before these tables are usable at runtime, L7 must prove:

- C1 registry contains all four table names with `kind=projection`.
- `SCHEMA_VERSION` is bumped from the current implementation version.
- `schema_ddl()` creates all columns from registry only.
- `validate_registry()` rejects invalid identifiers and duplicate columns.
- projection rebuild is idempotent for all four tables.
- detector tests cover missing coverage, prompt escalation, learning return, and upgrade-assist contract.
