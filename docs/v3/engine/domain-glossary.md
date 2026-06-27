# HELIX V3 — Domain Glossary And Bounded Contexts

> status: draft contract
> layer: L1-L6 support
> purpose: satisfy NFR-V3-08 and make V3 personal-edition terms machine-checkable
> upstream: [HELIX_CORE §5 DDD](../../../helix/HELIX_CORE.md), [HELIX_RUNTIME_RULES §5](../../../helix/HELIX_RUNTIME_RULES.md), [L1 NFR-V3-08](../L0-L14/L1-requirements.md)

## 1. Principle

HELIX V3 uses DDD to prevent terminology drift between Forward, drive workflows, documents, DB projection, detectors, and review evidence.

Rules:

- A term becomes a HELIX term only when it is mapped to a bounded context and a source artifact.
- Terms imported from external templates, UT harness, web articles, or provider tooling must pass through this glossary before they are used as canonical terms in Forward documents.
- A context boundary crossing must name its anti-corruption mapping. Direct reuse of another context's term as a canonical field is a doc-contract violation.
- Machine contracts use the canonical term. Human-facing docs may include aliases, but aliases must point back to one canonical term.

## 2. Bounded Contexts

| Context | Responsibility | Owns | Does not own |
|---|---|---|---|
| Forward Control | L0-L14 spine, gate state, V-model closure, Forward DB convergence | layer, gate, trace, forward_return, V-pair | external template semantics, provider runtime details |
| Artifact Registry | Documents, PLANs, workflow artifacts, and their parseable metadata | artifact, doc_kind, sub_doc, required_section, status | semantic review verdicts |
| Schema Registry | DB table/column/index definitions and table kind classification | table, column, index, projection, append_event, config | workflow routing or human approval |
| Projection Writer | Deterministic artifact-to-DB projection | projection run, rebuild, idempotence, deletion, stale | detector policy decisions |
| Detector | Pure findings from expected-vs-actual state | finding, severity, source_kind, fail_close | remediation planning |
| Template Catalog | External/internal design templates normalized into coverage requirements | template, source_url, provenance, freshness, pair_test_kind | copied template body or license approval |
| Review Evidence | Role-separated review proof and finding closure | review_viewpoint, reviewer, worker, tests_green_at, closure | implementation edits |
| Prompt Interpretation | Multiple-view interpretation of user instructions before PLAN execution | prompt_viewpoint, ambiguity, risk, escalation_signal | final scope approval for §10 boundaries |
| Learning Maintenance | Conversion of findings/reviews/tests/postmortems into future improvement candidates | learning_candidate, candidate_kind, forward_return, discard_reason | direct mutation of Forward canon |
| Drive Model | Non-Forward entry modes and their return contract | drive_mode, routing_signal, approval_required, forward_return | final DB convergence; Forward owns convergence |
| Upgrade Assist | Future version/dependency/provider/platform delta assessment | version_delta, impact_scope, rollback_condition, staged_gate | destructive cutover approval |
| Security Boundary | Human approval boundary for irreversible or sensitive operations | escalation_signal, approval_required, redacted_summary | storing secrets/PII/raw transcript |

## 3. Canonical Terms

| Canonical term | Context | Definition | Aliases / imported terms | Machine field candidates |
|---|---|---|---|---|
| HELIX personal edition | Forward Control | AI self-orchestrated development system constrained by gate/workflow/DB/detector guardrails | personal dev edition, AI safe autonomous development | project_kind |
| UT harness | Forward Control | Human/team-driven harness for using AI safely and comprehensively | UT-TDD Agent Harness, harness | source_system |
| Forward spine | Forward Control | L0-L14 canonical convergence path for all drive models | Forward backbone, spine | forward_return |
| Drive mode | Drive Model | Non-Forward workflow entry with required return to Forward | drive, workflow mode | drive_mode |
| Upgrade assist | Upgrade Assist | Auxiliary drive for future version/provider/platform changes with staged evaluation and rollback | upgrade drive, auxiliary drive | drive_mode=upgrade_assist |
| Template catalog | Template Catalog | Normalized external/internal template source records used to derive doc coverage | design template collection | template_catalog |
| Template body | Template Catalog | Original template content owned by the source. HELIX does not store copied long-form bodies by default | sample text, article body | not stored |
| Provenance | Template Catalog | Evidence of source URL, source kind, hash, freshness, and license note | source evidence | source_url, provenance_hash, freshness_status |
| Doc coverage | Artifact Registry | Required document kinds and sections derived from templates and current artifacts | design-doc coverage | doc_coverage |
| Pair test kind | Forward Control | Required test-design counterpart for a design artifact at the same V-model grain | test pair, paired test design | pair_test_kind |
| Review viewpoint | Review Evidence | Role or specialty lens used to review work independently | PM/TL/SE/QA/security/docs/perf/UX review | review_viewpoint |
| Prompt viewpoint | Prompt Interpretation | Interpretation lens for scope, acceptance, risk, test, doc coverage, or escalation | prompt lens | viewpoint |
| Escalation signal | Security Boundary | Signal that requires human approval before auto-run proceeds | §10 boundary, approval trigger | escalation_signal |
| Learning candidate | Learning Maintenance | Improvement proposal derived from finding/review/test/postmortem evidence | rule candidate, template gap, PLAN draft | learning_candidates |
| Forward return | Forward Control | Required mapping from a drive/workflow/candidate back to a Forward layer or explicit discard | convergence, mainline return | forward_return |
| Staged gate | Upgrade Assist | Ordered gate sequence used to safely evaluate and adopt an upgrade delta | staged cutover gate | staged_gate |
| Red-first evidence | Forward Control | Proof that a test failed for the intended reason before implementation | TDD red evidence | test_result_events |

## 4. Anti-Corruption Mappings

| Source context | Imported term | Canonical HELIX term | Mapping rule |
|---|---|---|---|
| External web template | template, sample, format | Template catalog entry | Store source metadata and normalized required sections, not copied body |
| UT harness | team-driven review | Review viewpoint | Convert role/team review into machine evidence fields |
| UT harness | harness workflow mode | Drive mode | Keep only mode contract: signal, approval, forward_return |
| Provider/runtime | raw model output | Prompt interpretation evidence | Store digest/summary and risk view; do not store secrets, PII, or raw transcript |
| Incident/recovery flow | fix result | Learning candidate | Convert to candidate with forward_return or discard_reason |
| Upgrade tooling | dependency update | Upgrade assist version_delta | Treat as future delta, not direct schema/config mutation |

## 5. Machine Checks

The DDD contract is checked by doc-contract and DDD coverage rules:

| Check | Input | Fails when |
|---|---|---|
| glossary-delta | changed docs / new terms | a new canonical-looking term is introduced without glossary entry or alias |
| bounded-context-coverage | artifact frontmatter + glossary | an artifact uses a term from another context without anti-corruption mapping |
| template-term-normalization | template_catalog | external template labels are stored as canonical terms without mapping |
| drive-forward-return | drive_runs / plan_registry | a drive mode produces output without Forward return or explicit discard |
| security-boundary-language | prompt_interpretations / findings | escalation terms are softened into auto-approved language |

## 6. Open Gaps

- The current document is a design contract. Runnable glossary/bounded-context detectors are still required.
- Existing V2 glossary references remain as legacy inputs; V3 should not depend on V2 path stability for its canonical terms.
- Template catalog expansion must append source-specific aliases here when the source introduces new document kinds.
