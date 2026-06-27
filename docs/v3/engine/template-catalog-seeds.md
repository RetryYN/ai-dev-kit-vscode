# HELIX V3 — Template Catalog Seed Records

> status: draft seed catalog
> purpose: satisfy G0.5 progress item #14 and provide normalized input for `template_catalog` / `doc_coverage`
> last_checked: 2026-06-27 JST
> storage rule: record source metadata and normalized coverage fields only. Do not copy long-form template bodies into HELIX.

## 1. Normalization Contract

Every external template source is converted into a seed record before it can affect HELIX gates.

Required fields:

| Field | Meaning |
|---|---|
| `template_seed_id` | Stable HELIX seed id. |
| `source_url` | Original URL. |
| `source_label` | `official`, `vendor`, `secondary`, `community`, or `internal`. |
| `source_kind` | `external_web`, `external_repo`, or `internal_doc`. |
| `doc_kinds` | HELIX-normalized document kinds. |
| `layers` | Forward layers where the seed may derive coverage requirements. |
| `pair_test_kind` | Expected test-design pair, if applicable. |
| `normalized_sections` | Abstract section requirements. |
| `quality_rules` | Rules that can become doc coverage checks. |
| `freshness_status` | `checked`, `dated`, `undated`, or `needs_review`. |
| `license_review` | `not_required_for_metadata`, `required_before_body_use`, or `unknown`. |
| `notes` | Scope limits and anti-corruption mapping. |

## 2. Seed Records

| ID | Source | Label | Doc kinds | Layers | Pair test kind | Freshness / license | Normalized coverage value |
|---|---|---|---|---|---|---|---|
| TPL-SEED-001 | https://crexgroup.com/ja/development/project/design-document-templates/ | secondary | requirements, basic_design, detailed_design, db_design, screen_design, batch_design, test_specification | L1,L3,L4,L5,L6,L8,L12 | acceptance_test, integration_test, unit_test | checked / metadata ok, body use review | Japanese SI-style document set; useful for broad L0-L6/L8 coverage and omissions around DB/screen/batch/test docs. |
| TPL-SEED-002 | https://arc42.org/overview | official | architecture_overview, constraints, context, building_blocks, runtime_view, deployment_view, quality_requirements, risks | L2,L4,L5,L9,L10 | system_test, integration_test | checked / metadata ok, template body license review if reused | Strong architecture documentation backbone; maps to L4 system structure and L5 building blocks. |
| TPL-SEED-003 | https://c4model.com/ | official | system_context, container_view, component_view, code_view | L2,L4,L5,L6 | system_test, integration_test, unit_test | checked / metadata ok | Good for visual architecture coverage and layer-to-component trace; complements arc42. |
| TPL-SEED-004 | https://diataxis.fr/ | official | tutorial, how_to, explanation, reference | L0,L1,L3,L4,L5,L6,L13,L14 | doc_review_test | checked / metadata ok | Documentation-type taxonomy; useful for preventing reference/how-to/explanation drift in HELIX docs. |
| TPL-SEED-005 | https://www.atlassian.com/software/confluence/templates/software-design-document | vendor | software_design_document | L3,L4,L5 | acceptance_test, system_test, integration_test | checked / metadata ok, body use review | Product/vendor SDD shape; normalize only headings and review workflow expectations. |
| TPL-SEED-006 | https://www.atlassian.com/software/confluence/templates/test-plan | vendor | test_plan | L7,L8,L9,L12,L14 | test_plan | checked / metadata ok, body use review | Test planning counterpart for V-model closure; maps design artifacts to execution strategy. |
| TPL-SEED-007 | https://www.jamasoftware.com/requirements-management-guide/writing-requirements/how-to-write-an-effective-product-requirements-document/ | vendor | product_requirements_document | L1,L3,L12,L14 | acceptance_test, operational_test | checked / metadata ok | PRD guidance; normalize requirement quality and stakeholder/context sections, not prose. |
| TPL-SEED-008 | https://www.perforce.com/blog/alm/how-write-software-requirements-specification-srs-document | vendor | software_requirements_specification | L1,L3,L12 | acceptance_test | checked / metadata ok | SRS-oriented seed for precise functional/non-functional requirement coverage. |
| TPL-SEED-009 | https://www.testmo.com/test-case-management/ | vendor | test_case_management, test_case_template | L7,L8,L9,L12 | test_case | checked / metadata ok | Test case management view; useful for test case fields, workflow states, folders, tags, and result linkage. |
| TPL-SEED-010 | https://www.testrail.com/blog/how-to-create-test-plans/ | vendor | test_plan, test_case_management | L7,L8,L9,L12,L14 | test_plan, test_case | checked / metadata ok | Complements Testmo with execution and management-oriented test plan fields. |
| TPL-SEED-011 | https://exia.co.jp/bizroute/system_development_template.html | secondary | requirements, basic_design, detailed_design, test_specification | L1,L3,L4,L5,L6,L8,L12 | acceptance_test, integration_test, unit_test | dated / metadata ok, body use review | Japanese Excel template set; normalize doc kinds and section labels only. |
| TPL-SEED-012 | https://github.com/wepay/design_doc_template | community | software_design_document, microservice_design | L3,L4,L5,L6 | acceptance_test, integration_test, unit_test | checked / license review before body use | Community markdown template seed for microservice design; useful as a machine-readable shape, but body reuse requires license review. |
| TPL-SEED-013 | https://learn.microsoft.com/en-us/dynamics365/guidance/patterns/create-functional-technical-design-document | official | functional_design, technical_design | L3,L4,L5,L6,L8,L9 | acceptance_test, integration_test, system_test | dated / metadata ok | Microsoft Dynamics 365 guidance for functional and technical design documents; good for combined business/technical design trace. |
| TPL-SEED-014 | https://ops.fhwa.dot.gov/seits/sections/section6/6_6.html | official | design_specification | L4,L5,L6,L8,L9 | system_test, integration_test | checked / metadata ok | U.S. FHWA ITS design specification guidance; useful for requirements-to-design translation and public-sector style trace. |

## 3. Derived HELIX Coverage Map

| HELIX doc kind | Minimum seed coverage | Pair test requirement | Gate impact |
|---|---|---|---|
| `requirements` | CREX, Jama PRD, Perforce SRS | acceptance_test / operational_test | G1/G3 rejects missing stakeholder, scope, NFR, acceptance sections. |
| `basic_design` | CREX, Bizroute, arc42, C4 | system_test | G4 rejects missing context, constraints, component boundary, deployment/runtime view. |
| `detailed_design` | CREX, Bizroute, arc42, C4, SDD templates | integration_test | G5 rejects missing module responsibility, interface, data flow, error handling, dependency boundary. |
| `db_design` | CREX, Bizroute | integration_test / migration_test | G5 rejects missing entity/table ownership, logical refs, migration/rollback note. |
| `screen_design` | CREX, Bizroute, C4 context when UI-facing | system_test / E2E | G4/G10 rejects missing screen flow, state transition, a11y, visual/token relation. |
| `batch_design` | CREX | integration_test / operational_test | G5/G14 rejects missing trigger, retry, idempotency, monitoring, rollback. |
| `test_specification` | CREX, Atlassian test plan, Testmo, TestRail | test_plan / test_case | G3/G6/G7 rejects missing design-pair trace and red-first plan. |
| `documentation_taxonomy` | Diátaxis | doc_review_test | doc-review rejects docs that mix tutorial/how-to/reference/explanation responsibilities. |

## 4. Projection Rules

`template_catalog` projection:

- one row per seed id and normalized doc kind;
- `source_url`, `source_label`, `source_kind`, `last_checked`, `freshness_status`, `license_review`, and `provenance_hash` are mandatory;
- copied body content is prohibited unless license review explicitly permits it;
- community sources set `license_review=required_before_body_use`.

`doc_coverage` projection:

- derive required docs by `(layer, doc_kind, subject_id)`;
- derive required sections from the union of applicable seeds;
- preserve source provenance for every required section group;
- if two sources disagree on structure, record both as alternatives and require a reviewer to choose before gate freeze.

## 5. Freshness And Review Policy

| Policy | Rule |
|---|---|
| Freshness interval | External web seeds are rechecked every 180 days or when a gate depends on a new doc kind. |
| Source reliability | Official sources can define baseline taxonomy; vendor/secondary/community sources can enrich section coverage but cannot override HELIX canonical terms without glossary mapping. |
| License boundary | HELIX stores metadata and normalized requirements by default. Template bodies, examples, or downloadable files require explicit license review before inclusion. |
| Learning loop | If a gate finds repeated missing sections, create `learning_candidate(candidate_kind=template_gap)` and either add a seed/section or record `discard_reason`. |

## 6. Open Gaps

- Convert these seed records into actual `template_catalog` fixture rows once C1 table columns are finalized.
- Add Japanese screen/API/interface design sources with explicit license metadata.
- Add downloadable file license evidence for sources that provide Excel/Word/Markdown bodies.
- Wire `template-coverage` rule to fail when required doc kinds or pair test kinds are missing.
