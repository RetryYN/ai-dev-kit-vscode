---
plan_id: PLAN-082
title: "PLAN-082: PLAN-076/077 機械化 (subagent fire-mandatory + Sprint 標準 8 ステップ機械化)"
status: completed
size: L
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-075 (V-model lint 機械化、本 PLAN の pattern 起点)
  - PLAN-076 (subagent 工程マッピング、framework only、機械化未着手)
  - PLAN-077 (Sprint Plan 標準化、framework only、機械化未着手)
  - PLAN-078 (Agent Slot 管理、本 PLAN と接続)
---

# PLAN-082: PLAN-076/077 機械化 (subagent fire-mandatory + Sprint 標準 8 ステップ機械化)

## 1. 背景

PLAN-075 Phase 5 で V-model 4 artifact lint を機械化 (vmodel_lint + helix-gate G2/G3/G4 advisory) したのと同じ pattern で、PLAN-076/077 の framework も機械化する。

### 1.1 PLAN-076 現状 (framework のみ)

- subagent 14 種を 2 分類: mandatory by phase (10 種) + on-demand by judgment (4 種)
- `helix/HELIX_CORE.md §工程別 subagent 起動マップ` に分類記載済
- **未実装**:
  - `helix agent fire-mandatory --phase Lx` CLI 不在
  - `helix agent suggest --task "..."` CLI 不在
  - helix.db に subagent invocation audit table 不在 (PLAN-078 v28 agent_slots と関連)
  - G2/G3/G4 で「mandatory subagent 不在 → carry note 強制」lint 不在

### 1.2 PLAN-077 現状 (framework のみ)

- Sprint 標準 8 ステップ確立 (Entry/着手前/実装/機械チェック/テスト/レビュー/commit/Exit)
- `helix/HELIX_CORE.md §Sprint Plan 標準構造` 記載済
- **未実装**:
  - `helix sprint complete --auto-check` CLI (mandatory in sprint 全通過確認)
  - `helix sprint addon <check>` CLI (on-demand step 追加)
  - Sprint Exit 前の py_compile / 該当 test / 全回帰 / レビュー の機械化 lint
  - Sprint 未完遂 → next Sprint blocked の fail-close 機構

### 1.3 PLAN-075 pattern との対比

| 観点 | PLAN-075 (実装済) | PLAN-076 (未実装) | PLAN-077 (未実装) |
|---|---|---|---|
| framework 確立 | Phase 1 | 既存 | 既存 |
| 機械化 CLI | `vmodel_lint` | `helix agent fire-mandatory / suggest` | `helix sprint complete --auto-check` |
| ゲート統合 | helix-gate G2/G3/G4 advisory | 同左、mandatory subagent fire check | Sprint Exit 強制 |
| 段階導入 | advisory → fail-close | 同 | 同 |

## 2. 目的

PLAN-076/077 を framework only から「機械検証 + ゲート統合」まで進める。

## 3. Phase 構成 (L サイズ、5 Phase 想定)

### Phase 1: 設計 (L1-L2)
- subagent invocation 記録 schema (PLAN-078 v28 agent_slots と統合検討)
- Sprint Plan 機械チェック schema (cli/lib/sprint_lint.py 仕様)
- ゲート統合方針 (advisory vs fail-close、段階導入)

### Phase 2: subagent fire-mandatory CLI (PLAN-076 機械化)
- `helix agent fire-mandatory --phase L2|L3|L4|G2|G3|G4`
- `helix agent suggest --task "..."`
- `helix agent audit --phase Lx` (mandatory 呼ばれ済か確認)
- helix.db v28 agent_slots を audit log として活用

### Phase 3: Sprint Plan 8 ステップ機械化 (PLAN-077 機械化)
- `cli/lib/sprint_lint.py` (mandatory in sprint 通過確認)
- `helix sprint complete --auto-check` (py_compile / 該当 test / 全回帰 / レビュー)
- `helix sprint addon <check>` (on-demand step 追加)

### Phase 4: helix-gate / helix-doctor 統合
- G2/G3/G4 で `subagent_audit` section 追加 (mandatory 不在 → warn)
- helix doctor の check_subagent_phase / check_sprint_completion 追加
- Sprint Exit 強制 fail-close (`helix sprint complete --strict`)

### Phase 5: テスト + 過去 PLAN 影響確認 + commit
- pytest + bats 全 PASS
- 過去 Sprint (PLAN-072 〜 PLAN-075) で機械化 check の retrofit 確認
- commit + push

## 3.5 V-model 4 artifact (PLAN-075 準拠、Phase 5 完遂版)

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | helix/HELIX_CORE.md §工程別 subagent 起動マップ (PLAN-076) + §Sprint Plan 標準構造 (PLAN-077) + docs/v2/L3-detailed-design/D-CONCEPT.md |
| ② 実装コード | L4 実装 | cli/lib/agent_mandatory.py + cli/lib/sprint_lint.py + cli/helix-agent (fire-mandatory/suggest/audit subcommand) + cli/helix-sprint (complete --auto-check subcommand) + cli/helix-gate (subagent_audit/sprint_completion advisory) + cli/helix-doctor (check_subagent_phase/check_sprint_completion) |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-082-unit-test-design.md (carry、Phase 6 で正式起票) |
| ④ テストコード | L4 実装 | cli/lib/tests/test_agent_mandatory.py + cli/lib/tests/test_sprint_lint.py + tests/helix-agent-mandatory.bats + tests/helix-sprint-mechanization.bats |

framework 機械化系のため設計 doc は HELIX_CORE.md (PLAN-076/077 framework) で実質代替。Phase 5 完遂状態では ③ テスト設計の正式 doc は carry (Phase 6 で起票予定)、④ テストコードは完備済 (pytest 29 + bats 13 case PASS)。

## 4. 受入条件

- `helix agent fire-mandatory --phase L2` で mandatory 10 種を一括投入 (実投入 or audit のみ)
- `helix sprint complete --auto-check` で Sprint Exit mandatory 4 種 (py_compile / test / 全回帰 / レビュー) を機械確認
- helix-gate G2/G3/G4 で subagent_audit + sprint_completion を advisory 実行
- pytest + bats 全 PASS

## 5. PLAN-078 との接続

- PLAN-078 v28 agent_slots schema を subagent invocation audit log として再利用
- PLAN-078 完遂後 → 本 PLAN Phase 2 着手可能
- 順序: PLAN-078 (v28) → 本 PLAN Phase 2 (agent fire-mandatory) → PLAN-079 (v29) → PLAN-080 (v30)

## 6. carry

- 次セッションは PLAN-078 Sprint .2 以降 (agent_slots 実装) を先に
- 本 PLAN は PLAN-078 完遂後に Phase 1 から着手 (依存)
