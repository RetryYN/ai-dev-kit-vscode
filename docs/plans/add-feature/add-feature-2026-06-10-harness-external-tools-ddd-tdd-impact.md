---
plan_id: add-feature-2026-06-10-harness-external-tools-ddd-tdd-impact
title: "Action(add-feature): HARNESS external tools + DDD/TDD/impact/dependency feedback expansion"
plan_scope: action
workflow: add-feature
kind: add-design
layer: L6
process_layer: L6
forward_return: "L4-L6 harness external-tools design -> approved L7 test-first implementation -> external-tool/ddd/impact feedback evidence -> HELIX DB feedback closure evidence (L6↔L7 G6/G7 pending gate evidence に帰属)."
drive: be
status: draft
tl_review: approve  # draft boundary ticket の push 承認のみ (TL L1-L6 review 2026-06-13: 境界妥当・prior L1-L6 evidence 有り・design_substitute=0)。L7 実装承認ではない (status=draft 維持、approval_required_before_* 参照)
created: 2026-06-10
owner: TL
current_task_scope: L4_L6_design_closed_feature_ticketed
approval_required_before_install: true
approval_required_before_l7_work: true
approval_boundary: "This PLAN is only a ticket for HARNESS external-tool expansion. L7 artifacts, tool installation/execution, credentials, CI/security surface changes, DB write adoption, and fail-close promotion require explicit approval."
web_research_required: true
external_tool_installation_allowed_now: false
unlock_conditions:
  - external_tool
  - adoption_recheck
  - ingestion
related_objectives:
  - OBJ-HARNESS-EXTERNAL-TOOLS
  - OBJ-ADDITIONAL-IMPROVEMENT-DISCOVERY
  - OBJ-WORKFLOW-AUTOMATION
  - OBJ-HELIX-DB-FEEDBACK
related_docs:
  - docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md
  - docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md
  - docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md
  - docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml
  - docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml
  - docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml
  - docs/v2/L6-functional-design/coding-rule-detector-機能設計.md
  - docs/v2/L6-functional-design/ddd-registry-detector-機能設計.md
  - docs/v2/L6-functional-design/db-backed-evidence-lifecycle-機能設計.md
generates:
  - artifact_path: docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L5-detailed-design/harness-external-tools-impact-詳細設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L6-functional-design/harness-external-tools-impact-機能設計.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/harness-external-tools-impact-単体テスト設計.md
    artifact_type: design_doc
  - artifact_path: cli/config/harness-external-tool-registry.yaml
    artifact_type: yaml_config
  - artifact_path: cli/lib/harness_external_tools.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_harness_external_tools.py
    artifact_type: test
safety:
  schema_migration: false
  destructive_data_operation: false
  auto_install: false
  auto_apply: false
  credential_or_secret_change: false
  external_network_execution: false
---

# HARNESS external tools + DDD/TDD/impact/dependency feedback expansion

## 1. 目的

MCP サーバー、プラグイン、SAST / code scanning / dependency analysis などの外部ツールを HELIX HARNESS 内で扱うための候補登録・審査・実行証跡・HELIX DB feedback 接続を設計する。

現在タスクでは L4-L6 設計のみを閉じ、外部ツールをインストールしない。本 PLAN は、承認後に HARNESS 内で安全に導入するための feature 起票である。

## 2. Web-backed candidates

| Candidate | Official source | 2026-06-12 再確認焦点 | HARNESS use | Boundary |
|---|---|---|---|---|
| GitHub MCP Server | GitHub Docs / GitHub official repository | remote/local、OAuth / PAT、host policy、repo / issue / PR / workflow context、write-capable tool scope | GitHub issue / PR / workflow / repo context を MCP 経由で取得し、PLAN / impact / feedback evidence に接続 | auth / org policy / token scope / write scope が必要なため承認必須 |
| Semgrep CE | Semgrep official docs | `semgrep scan`、CI/local execution、rule license、JSON/SARIF 等の出力正規化 | OSS SAST を `helix harness security-scan` 候補として登録し、findings を HELIX DB events / metrics / feedback へ append | rules license 確認、CI変更は承認必須 |
| CodeQL | GitHub Docs / CodeQL docs | CodeQL database、query results、code scanning alerts、SARIF / third-party route、Actions or external CI | code scanning / query result / SARIF を impact analysis と security feedback に接続 | GitHub security feature / Actions / external CI の扱い確認が必要 |
| zizmor | zizmor official docs / repository | GitHub Actions workflow/action static analysis、offline/online mode、GitHub token permissions、JSON / SARIF / GitHub annotation outputs、persona / fix policy | workflow security findings を workflow hardening / CI policy candidate / HELIX DB workflow-security evidence に接続 | workflow/action scope、token scope、SARIF upload、CI/pre-commit wiring、safe/unsafe fix は承認必須 |
| actionlint | actionlint official repository | GitHub Actions workflow syntax / expression semantics / reusable workflow / ShellCheck / Pyflakes / script injection / credential literal checks | workflow lint findings を workflow hardening / CI maintainability candidate / HELIX DB workflow-lint evidence に接続 | workflow scope、problem matcher / output normalization、CI/pre-commit wiring、license は承認必須 |
| SQLFluff | SQLFluff official docs | SQL lint、dialect reference including SQLite、templater / rule config、pre-commit / GitHub Actions surfaces | SQL/schema/migration lint findings を DB design safety / migration review candidate / HELIX DB SQL-schema evidence に接続 | SQL source scope、dialect / templater policy、fix-mode、CI / pre-commit wiring、license は承認必須 |
| diff-cover | diff-cover official repository / PyPI | changed-line coverage, XML/LCov coverage report comparison with git diff, diff-quality, HTML/JSON/Markdown output, fail-under controls | changed-line coverage / diff-quality findings を TDD strictness / change-impact / HELIX DB diff-coverage evidence に接続 | git diff scope、compare branch、coverage report format、fail-under、CI/pre-commit wiring、license は承認必須 |
| lychee | lychee official repository / docs | broken hyperlink and mail address checking, Markdown/HTML/reStructuredText/website sources, JSON output, GitHub Action and pre-commit surfaces | link/reference rot findings を document auto-registration / glossary・registry refs / HELIX DB doc-connection-gap evidence に接続 | document scope、network/auth/header policy、accepted status、include/exclude、CI/pre-commit wiring、license は承認必須 |
| pytest-testmon | testmon official docs / pytest-testmon official repository | affected test selection, Coverage.py dependency collection, .testmondata, pytest --testmon, noselect/nocollect/forceselect options, hidden dependency and CI surfaces | impacted-test selection findings を change-impact / TDD prioritization / HELIX DB test-impact evidence に接続 | test scope、dependency DB、selection mode、hidden dependency policy、CI/pre-commit wiring、license は承認必須 |
| MCP protocol registry gate | MCP official specification | JSON-RPC 2.0、lifecycle、authorization、resources/prompts/tools、tool invocation consent | MCP server を JSON-RPC / lifecycle / auth / tool-scope で審査し、HARNESS allowlist に登録 | server trust、credential、tool poisoning 対策が必須 |

### 2.1 L1-L6 candidate inventory sync

L1-L6 現在スコープの候補正本は `docs/v2/audit/2026-06-12-l1-l6-harness-external-tools-coverage.yaml` と `docs/v2/audit/2026-06-12-l1-l6-improvement-candidate-map.yaml` に置く。本 PLAN は承認後導入の入口であり、下記の候補群を承認後に HARNESS registry / output normalization / HELIX DB feedback へ接続するための feature ticket である。

| Class | Candidate count | Current action | Approved feature-ticket adoption boundary |
|---|---:|---|---|
| MCP / plugin / protocol admission | 3 | feature-ticket-only | auth、tool consent、tool poisoning、write capability、Apps SDK descriptor 審査後 |
| SAST / code scanning / workflow security | 4 | feature-ticket-only | license、SARIF、CI surface、secret/token scope 審査後 |
| repository / dependency / vulnerability / SBOM intelligence | 4 | feature-ticket-only | network、package scope、advisory DB、output normalization 審査後 |
| source dependency graph | 2 | feature-ticket-only | graph scope、edge model、impact query mapping 審査後 |
| shell / markdown / prose / natural-language document lint | 5 | feature-ticket-only | source scope、rule/preset/plugin、fix-mode、Japanese docs policy、link/reference rot 審査後 |
| Python TDD / coverage / runner / environment automation | 8 | feature-ticket-only | test scope、dependency install、venv/session、coverage threshold、impacted-test selection、diff coverage 審査後 |
| Python architecture / schema / API / lint / type / vuln contracts | 6 | feature-ticket-only | contract scope、ruleset、schema source、output and DB mapping 審査後 |
| database / SQL schema / migration lint | 1 | feature-ticket-only | SQL source scope、dialect、templater、fix-mode、schema/migration DB mapping 審査後 |

合計 33 candidate は L1-L6 では候補・契約・境界の定義までに止める。未承認の候補は install、execute、CI connection、DB write、auto-fix / auto-apply、L7 test-design / implementation の証跡として扱わない。

## 3. Scope

### In

- `harness-external-tool-registry.yaml` に候補ツール、公式URL、license/auth/credential/network/scope を登録する。
- HARNESS 導入前の approval gate を定義する。
- DDD / coding-rule / TDD / dependency / impact / feedback の各 detector と外部ツール出力の接続点を定義する。
- tool run result を HELIX DB の events / metrics / feedback へ append する evidence contract を定義する。
- dependency graph / impact graph の出力を、修正影響範囲の説明に使える形で登録する。
- MCP / plugin / SAST / code scanning ごとに `host_support`, `auth_method`, `secret_storage_policy`, `data_access_scope`, `write_capability`, `tool_invocation_consent_required`, `tool_poisoning_review_required`, `output_format`, `sarif_supported`, `ci_surface`, `failure_mode` を registry に持たせる。
- `HEXT-FN-09` / `HEXT-FN-10` に対応する Web evidence freshness と execution risk 判定を、承認後の feature ticket に接続する。

### Out

- MCP サーバー、VSCode拡張、プラグイン、Semgrep、CodeQL の実インストール。
- GitHub token / OAuth / secret / env の追加。
- CI workflow 変更。
- DB schema migration。
- tool findings の auto-fix / auto-apply。

## 4. Acceptance

- 各 external tool candidate が official source、license / auth / credential / network / data access / write capability / approval status を持つ。
- 各 candidate が host / consent / toolset scope / secret storage / tool poisoning / SARIF / CI surface / failure mode を持つ。
- HARNESS は未承認 candidate を実行しない。
- DDD / coding-rule / TDD の既存 detector と競合せず、外部ツールは advisory evidence として扱われる。
- dependency / impact graph は `source -> target -> affected artifact -> required gate` の形で説明できる。
- `helix harness feedback-loop --json` に external tool source_pattern_key を追加しても、candidate は closure として扱われない。
- official source freshness が失われた candidate は `candidate_requires_research` へ戻る。

## 5. Completion boundary

- この PLAN の作成は導入完了ではない。
- L4-L6 設計の作成は外部ツール導入完了ではない。
- 外部ツールの実導入は、承認、allowed_files、rollback、verification commands、license / credential / network boundary を満たす別 Sprint で行う。
- full objective completion には、採用された tool candidate が PLAN / implementation / gate evidence / HELIX DB feedback / recurrence closure まで進む必要がある。
