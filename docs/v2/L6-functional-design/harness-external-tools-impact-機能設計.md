---
doc_id: L6-FUNCTIONAL-DESIGN-HARNESS-EXTERNAL-TOOLS-IMPACT
title: HARNESS external tools / dependency impact 機能設計
status: draft
layer: L6
pairs_with: L7
next_feature_plan: docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md
parent_design:
  - docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md
  - docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
---

# HARNESS external tools / dependency impact 機能設計

## 1. 目的

HARNESS external tools / dependency impact は、外部ツール候補を安全に登録・審査し、承認済み実行結果だけを HELIX DB feedback と dependency / impact graph に接続する機能群である。

現在フェーズでは L6 機能仕様までを定義し、L7 単体テスト設計・実装・ツール導入は行わない。

## 2. 上位 Trace

| 上位要件 / 設計 | 本機能での役割 |
|---|---|
| OBJ-HARNESS-EXTERNAL-TOOLS | MCP / plugin / external tool 導入候補の調査と HARNESS 内拡張 |
| OBJ-WORKFLOW-AUTOMATION | 自動化基盤の拡張候補 |
| OBJ-HELIX-DB-FEEDBACK | tool finding / impact evidence の DB feedback 接続 |
| coding-rule detector | Semgrep 等の findings を coding-rule hardening evidence として接続 |
| DDD registry detector | doc / term / BC drift と tool findings の関係を接続 |
| DB-backed evidence lifecycle | candidate と closure を分離する evidence lifecycle |

## 3. 機能一覧

| FN-ID | 関数 / surface | 入力 | 出力 | 判定 |
|---|---|---|---|---|
| HEXT-FN-01 | register_tool_candidate | official source, tool metadata | registry draft | official_url / source_id / owner / kind を必須にする |
| HEXT-FN-02 | evaluate_admission_boundary | registry draft, approval context | admission decision | auth / credential / license / network / write capability を評価する |
| HEXT-FN-03 | enforce_harness_allowlist | admission decision, requested command | allow / deny | `approval_status=approved` かつ allowed_commands にある時だけ allow |
| HEXT-FN-04 | normalize_tool_output | SARIF / JSON / log / MCP response | normalized finding | source_category / source_pattern_key / affected_artifact を持つ |
| HEXT-FN-05 | build_dependency_impact_graph | normalized finding, registry links, docs/code links | impact graph | source -> dependency -> artifact -> gate を生成する |
| HEXT-FN-06 | append_feedback_evidence | impact graph, tool finding | events / metrics / feedback payload | append-only、closure_allowed=false |
| HEXT-FN-07 | route_bottleneck_candidate | repeated findings, impact graph | PLAN / PR candidate | candidate_generated 止まりで auto-apply しない |
| HEXT-FN-08 | emit_external_tool_guard_summary | registry, run evidence, feedback state | goal guard summary | installation / connection / adoption / closure を分離する |
| HEXT-FN-09 | verify_web_evidence_freshness | source_id, official_url, fetched_on, confirmed_focus | freshness verdict | official source / date / focus が無い候補を `blocked` または `candidate_requires_research` にする |
| HEXT-FN-10 | evaluate_tool_execution_risk | registry draft, host policy, output contract | execution risk verdict | auth / secret / network / write / tool poisoning / SARIF / CI surface を分離し、未承認なら実行不可 |

## 4. Output Contract

```yaml
harness_external_tool:
  tool_id: string
  source_id: string
  kind: mcp_protocol_admission | mcp_server | plugin | sast | code_scanning | github_actions_workflow_security | dependency_analysis | impact_analysis | repository_security_score | dependency_intelligence | vulnerability_scanning | sbom_generation | source_dependency_graph | shell_static_analysis | markdown_static_analysis | prose_style_analysis | natural_language_lint | python_mutation_testing | python_property_based_testing | python_coverage_measurement | python_test_runner | python_environment_orchestration | python_session_automation | python_architecture_contracts | document_schema_validation | api_contract_lint | python_lint_format | python_type_checking | python_dependency_audit
  approval_status: candidate | approved | rejected | blocked
  install_surface: none | local | ci | remote | mcp_host
  host_support: []
  auth_method: none | oauth | pat | token | env_secret | local_only
  auth_required: bool
  credential_scope: []
  secret_storage_policy: not_allowed_in_current_scope | existing_secret_only | approved_secret_store
  network_required: bool
  data_access_scope: []
  write_capability: bool
  tool_invocation_consent_required: bool
  toolset_scope: []
  tool_poisoning_review_required: bool
  license_review_required: bool
  output_format: [json | sarif | log | mcp_response | code_scanning_alert]
  sarif_supported: bool
  ci_surface: none | local_only | github_actions | external_ci | scheduled
  failure_mode: advisory | fail_close | blocked_until_approved
  allowed_commands: []
  run_evidence_refs: []
  impact_graph_refs: []
  feedback:
    candidate_generated: bool
    plan_or_pr_adopted: false
    closure_allowed: false
```

## 5. 判定ルール

| Rule | 判定 |
|---|---|
| official source なし | `blocked` |
| approval_status が `approved` 以外 | 実行不可 |
| auth_required かつ credential_scope 未承認 | 実行不可 |
| auth_method が `oauth / pat / token / env_secret` で承認 evidence が無い | 実行不可 |
| secret_storage_policy が `not_allowed_in_current_scope` | 実行不可 |
| write_capability あり、allowed scope なし | 実行不可 |
| tool_invocation_consent_required かつ consent evidence が無い | 実行不可 |
| tool_poisoning_review_required かつ review evidence が無い | 実行不可 |
| license_review_required かつ未確認 | 実行不可 |
| sarif_supported だが output normalization / parser 未定義 | 実行不可 |
| ci_surface が `github_actions / external_ci / scheduled` で承認が無い | 実行不可 |
| tool output のみ | closure 不可 |
| impact graph のみ | closure 不可 |
| PLAN / gate / recurrence evidence なし | full goal completion 不可 |

## 6. Tool candidate 初期値

| Tool | kind | 初期 admission | 2026-06-12 official evidence focus | 理由 |
|---|---|---|---|---|
| MCP protocol admission gate | `mcp_protocol_admission` | `candidate` | JSON-RPC 2.0、lifecycle、authorization、resources/prompts/tools | protocol / lifecycle / auth / tool scope / tool poisoning の審査が必要 |
| GitHub MCP Server | `mcp_server` | `candidate_requires_confirmation` | remote/local、OAuth / PAT、host policy、GitHub repo/issue/PR/workflow context | OAuth / PAT / org policy / write capability / data access 境界が必要 |
| Semgrep CE | `sast` | `candidate_requires_confirmation` | `semgrep scan`、CI/local、rule license、static findings | rule license / CI or local execution boundary / SARIF or JSON output normalization が必要 |
| CodeQL | `code_scanning` | `candidate_requires_confirmation` | CodeQL database、query results、code scanning alerts、Actions or external CI | GitHub security feature / Actions / external CI route / SARIF ingestion が必要 |
| zizmor | `github_actions_workflow_security` | `candidate_requires_confirmation` | GitHub Actions workflow/action static analysis、offline/online mode、JSON / SARIF / GitHub annotation outputs、template-injection / excessive-permissions / dangerous-triggers / unpinned-uses / secrets handling audit focus | workflow/action scope / offline-online mode / token scope / SARIF or JSON output normalization / persona policy / fix-mode prohibition / CI or pre-commit surface / HELIX DB workflow-security mapping が必要 |
| OpenSSF Scorecard | `repository_security_score` | `candidate_requires_confirmation` | GitHub Action / REST API / badge / CLI、PAT or GitHub App auth、aggregate / per-check score | repo scope / auth scope / REST API data license / score output normalization / CI or CLI route が必要 |
| deps.dev API | `dependency_intelligence` | `candidate_requires_confirmation` | package/version/license/requirement/dependency/project/advisory APIs、JSON HTTP / gRPC / BigQuery | package ecosystem scope / API route / license-advisory ingestion / output normalization / HELIX DB mapping が必要 |
| OSV-Scanner | `vulnerability_scanning` | `candidate_requires_confirmation` | source/container/lockfile/manifest/SBOM/license scanning、JSON / SARIF / SPDX / CycloneDX outputs | artifact scope / vulnerability DB route / license policy / output normalization / CI or pre-commit surface / guided remediation risk が必要 |
| Syft | `sbom_generation` | `candidate_requires_confirmation` | container image / filesystem / directory / file / archive / registry sources、Syft JSON / CycloneDX / SPDX outputs | SBOM source scope / cataloger selection / registry access / output normalization / license handling / attestation policy / HELIX DB mapping が必要 |
| Grimp | `source_dependency_graph` | `candidate_requires_confirmation` | Python import graph、children / descendants / directly imported / upstream / shortest chain / import details | Python package scope / external package inclusion / import edge normalization / license policy / HELIX DB dependency edge mapping が必要 |
| dependency-cruiser | `source_dependency_graph` | `candidate_requires_confirmation` | JS/TS dependency validation、rule violation reporting、dot / json / csv / html / mermaid graph outputs、circular/orphan/package manifest signals | JS/TS source scope / dependency rule scope / graph output normalization / circular/orphan/package manifest policy / HELIX DB dependency edge mapping が必要 |
| ShellCheck | `shell_static_analysis` | `candidate_requires_confirmation` | shell script static analysis、bash / sh warnings、syntax / semantic / pitfall detection、JSON / CheckStyle XML / GCC-compatible / text outputs | shell script scope / shell dialect policy / severity policy / output normalization / CI or pre-commit surface / license policy / HELIX DB shell finding mapping が必要 |
| markdownlint-cli2 | `markdown_static_analysis` | `candidate_requires_confirmation` | Markdown / CommonMark linting、config-based rule checking、glob / file scope、JSON / JUnit XML / SARIF / GitLab Code Quality / summary outputs | Markdown source scope / rule scope / config file policy / fix-mode prohibition / output normalization / CI or pre-commit surface / license policy / HELIX DB markdown finding mapping が必要 |
| Vale CLI | `prose_style_analysis` | `candidate_requires_confirmation` | prose linting、YAML style rules、vocabulary accept/reject、markup-aware linting、JSON / template / metrics / exit-code outputs | prose source scope / style rule scope / vocabulary policy / Glossary mapping / package sync prohibition / output normalization / CI or pre-commit surface / license policy / HELIX DB prose finding mapping が必要 |
| mutmut | `python_mutation_testing` | `candidate_requires_confirmation` | Python mutation testing、pytest workflow、coverage.py filtering、mypy / pyrefly filtering、dependency/config change detection、mutant browse/apply workflow | Python source scope / mutation operator scope / pytest command policy / coverage and type-checker filtering / dependency-change policy / timeout and parallelism / mutant apply prohibition / output normalization / CI or pre-commit surface / license policy / HELIX DB mutation finding mapping が必要 |
| Ruff | `python_lint_format` | `candidate_requires_confirmation` | Python linter / formatter、pyproject.toml support、900+ built-in rules、`ruff check`、rule selection、fix safety / unsafe-fix controls、JSON output with applicability | Python source scope / rule selection / config file policy / fix and unsafe-fix prohibition / suppression policy / output normalization / CI or pre-commit surface / license policy / HELIX DB coding-rule finding mapping が必要 |

## 6.1 Unit-test design viewpoints within L6

`HEXT-UT-CAND-*` は L6 の単体テスト設計観点であり、L7 の単体テスト設計成果物ではない。

| UT-CAND | Covers | Viewpoint |
|---|---|---|
| HEXT-UT-CAND-01 | HEXT-FN-01 | official source / source_id / owner 欠落時に registry draft を block |
| HEXT-UT-CAND-02 | HEXT-FN-02 | OAuth / PAT / secret / write scope 未承認時に candidate から昇格しない |
| HEXT-UT-CAND-03 | HEXT-FN-03 | allowed_commands 空の tool 実行を deny |
| HEXT-UT-CAND-04 | HEXT-FN-04 | SARIF / JSON / MCP response を closure ではなく normalized finding に留める |
| HEXT-UT-CAND-05 | HEXT-FN-05 | source -> dependency -> artifact -> gate の impact graph 形を保つ |
| HEXT-UT-CAND-06 | HEXT-FN-06 | feedback append は closure に昇格しない |
| HEXT-UT-CAND-07 | HEXT-FN-07 | repeated findings は PLAN / PR candidate までで auto-apply しない |
| HEXT-UT-CAND-08 | HEXT-FN-08 | guard summary が installation / connection / adoption / closure を分離する |
| HEXT-UT-CAND-09 | HEXT-FN-09 | official URL / fetched_on / confirmed_focus 欠落時に candidate_requires_research |
| HEXT-UT-CAND-10 | HEXT-FN-10 | tool poisoning / CI / SARIF / secret 境界が未承認なら execution を block |

## 7. L7 起票

安全境界:

- `schema_migration=false`
- `external_tool_installation_allowed_now=false`
- `credential_or_secret_change=false`
- `external_network_execution=false`
- `auto_install=false`
- `auto_apply=false`

本タスクでは L7 単体テスト設計、HARNESS registry 実装、外部ツール導入、MCP server 起動、Semgrep / CodeQL 実行を行わない。L7 以降で `HEXT-UT-*` を定義し、allowlist / registry / output normalization / impact graph / feedback append を実装する作業は `docs/plans/add-feature/add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact.md` で承認後に扱う。
