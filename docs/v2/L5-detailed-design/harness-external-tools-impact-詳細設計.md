---
doc_id: L5-DETAILED-DESIGN-HARNESS-EXTERNAL-TOOLS-IMPACT
title: HARNESS external tools / dependency impact 詳細設計
status: draft
layer: L5
pairs_with: L8
pairs_test_design: docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md
parent_design:
  - docs/v2/L4-basic-design/harness-external-tools-impact-基本設計.md
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
---

# HARNESS external tools / dependency impact 詳細設計

## 1. 目的

L4 で定義した external tool admission / dependency impact model を、既存 manifest / HELIX DB append 領域へ写像する。新規 schema、外部ツール導入、認証設定、CI 変更は行わない。

## 2. Registry Schema

`harness-external-tool-registry.yaml` の候補 schema:

| field | 型 | 必須 | 意味 |
|---|---|---|---|
| `id` | str | ✓ | `HTOOL-*` |
| `name` | str | ✓ | tool / server 名 |
| `kind` | str | ✓ | `mcp_server / plugin / sast / code_scanning / dependency_analysis / impact_analysis` |
| `official_url` | str | ✓ | 公式情報 |
| `source_id` | str | ✓ | `docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml` の source_id |
| `install_surface` | str | ✓ | `none / local / ci / remote / mcp_host` |
| `host_support` | list[str] | ✓ | 利用可能 host / harness 面。例: `codex / claude / github_copilot / ci / local` |
| `auth_method` | str | ✓ | `none / oauth / pat / token / env_secret / local_only` |
| `auth_required` | bool | ✓ | OAuth / PAT / secret 等が必要か |
| `credential_scope` | list[str] | ✓ | 必要権限。不要時は空 |
| `secret_storage_policy` | str | ✓ | `not_allowed_in_current_scope / existing_secret_only / approved_secret_store` |
| `network_required` | bool | ✓ | 外部通信が必要か |
| `data_access_scope` | list[str] | ✓ | repo / issue / PR / workflow / code / DB / browser 等の読み取り範囲 |
| `write_capability` | bool | ✓ | repo / issue / PR / workflow 等への書込能力 |
| `tool_invocation_consent_required` | bool | ✓ | MCP tool / external command 実行に明示承認が必要か |
| `toolset_scope` | list[str] | ✓ | 有効化する tool / command 名。未承認時は空 |
| `tool_poisoning_review_required` | bool | ✓ | prompt / tool description / repo content injection を審査するか |
| `license_review_required` | bool | ✓ | rule / package / service license 確認が必要か |
| `output_format` | list[str] | ✓ | `json / sarif / log / mcp_response / code_scanning_alert` |
| `sarif_supported` | bool | ✓ | SARIF 取り込み候補か |
| `ci_surface` | str | ✓ | `none / local_only / github_actions / external_ci / scheduled` |
| `failure_mode` | str | ✓ | `advisory / fail_close / blocked_until_approved` |
| `approval_status` | str | ✓ | `candidate / approved / rejected / blocked` |
| `allowed_commands` | list[str] | ✓ | HARNESS が実行可能なコマンド。未承認時は空 |
| `evidence_outputs` | list[str] | ✓ | JSON / SARIF / log / DB event 等 |

## 3. Admission Decision

| Condition | Decision |
|---|---|
| official source がない | `blocked` |
| auth / credential が必要で承認がない | `candidate` のまま |
| write capability があり allowed scope がない | `blocked` |
| license review required かつ未確認 | `candidate` のまま |
| network_required かつ実行面が未定義 | `candidate` のまま |
| tool_invocation_consent_required かつ承認 evidence がない | `candidate` のまま |
| secret_storage_policy が未定義または current scope 外 | `candidate_requires_confirmation` |
| tool_poisoning_review_required かつ review 未実施 | `candidate` のまま |
| sarif_supported だが SARIF 取り込み先 / parser が未定義 | `candidate` のまま |
| ci_surface が `github_actions / external_ci / scheduled` で承認がない | `candidate_requires_confirmation` |
| approval + allowed_commands + rollback + verification がある | `approved` |

### 3.1 Candidate-specific required fields

| Candidate | Required fields |
|---|---|
| MCP server | `host_support`, `auth_method`, `data_access_scope`, `write_capability`, `tool_invocation_consent_required`, `toolset_scope`, `tool_poisoning_review_required` |
| GitHub MCP Server | `auth_method=oauth/pat`, `credential_scope`, `data_access_scope`, `write_capability`, `secret_storage_policy`, `host_support` |
| Semgrep CE | `output_format`, `sarif_supported`, `ci_surface`, `license_review_required`, `failure_mode` |
| CodeQL | `output_format`, `sarif_supported`, `ci_surface`, `data_access_scope`, `failure_mode` |

## 4. Impact Graph Record

```yaml
impact_record:
  source_id: string
  source_type: changed_file | tool_finding | detector_signal | doc_artifact
  dependency_edges:
    - from: string
      to: string
      relation: imports | references | owns_term | enforces_rule | emits_signal | requires_gate
  affected_artifacts:
    - path: string
      layer: L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 | L9 | L10 | L11 | L12 | L13 | L14
      required_gate: string
  feedback:
    event_category: external_tool | dependency_impact | security_scan | mcp_admission
    candidate_generated: bool
    closure_allowed: false
```

## 5. 既存 DB / manifest 写像

| Evidence | 保存先 | 備考 |
|---|---|---|
| tool candidate | `docs/v2/audit/2026-06-12-l1-l6-web-evidence-source-map.yaml`, `additional-improvement-discovery.yaml` | L1-L6 evidence は audit map、将来候補 discovery は別 manifest |
| registry draft | future `harness-external-tool-registry.yaml` | 承認後 |
| admission decision | `events`, `metrics`, `feedback`, handover log | append-only |
| tool run output | `verify_runs`, `automation_runs`, `events` | 実行は承認後 |
| impact graph | `links`, `entries`, `metrics`, generated manifest | schema migration なし |
| feedback candidate | `feedback`, `goal-completion-audit.yaml` | closure ではない |

## 6. 失敗時扱い

| Failure | 判定 | Recovery |
|---|---|---|
| official source 不明 | blocked | Web evidence を追加するまで実行不可 |
| auth / credential 判断が必要 | human confirmation required | secret / token を扱わず停止 |
| license 未確認 | candidate | license review PLAN を起票 |
| CI / network 変更が必要 | candidate_requires_confirmation | infrastructure 承認へ戻す |
| OAuth / PAT / secret が必要 | human confirmation required | secret / token / env を扱わず停止 |
| MCP tool poisoning / prompt injection リスク未評価 | candidate | tool description / prompt / repo-content 境界を審査 |
| SARIF parser / code scanning alert ingestion が未定義 | candidate | output normalization 設計へ戻す |
| tool finding の auto-fix 要求 | blocked | auto-apply 禁止、PLAN 化のみ |
| impact graph が gate に写像できない | partial | dependency-map / reverse analysis へ routing |

## 7. Non-goals

- `schema_migration=false`
- `external_tool_installation_allowed_now=false`
- `credential_or_secret_change=false`
- `external_network_execution=false`
- `auto_install=false`
- `auto_apply=false`
- 外部ツールのインストール。
- MCP server の起動。
- GitHub OAuth / PAT / secret の設定。
- Semgrep / CodeQL の実行。
- CI workflow 変更。
- DB schema migration。
- auto-fix / auto-apply。
