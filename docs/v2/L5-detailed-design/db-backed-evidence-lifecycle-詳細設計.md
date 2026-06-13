---
doc_id: L5-DETAILED-DESIGN-DB-BACKED-EVIDENCE-LIFECYCLE
title: DB-backed evidence lifecycle 詳細設計
status: draft
layer: L5
pairs_with: L8
pairs_test_design: docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md
parent_design:
  - docs/v2/L4-basic-design/db-backed-evidence-lifecycle-基本設計.md
  - docs/v2/L5-detailed-design/物理データ設計.md
implementation_status: design_gap_closed_current_phase
owner: TL
created: 2026-06-10
---

# DB-backed evidence lifecycle 詳細設計

## 1. 目的

L4 で固定した evidence lifecycle を、既存 DB / registry / manifest 上の内部状態遷移として定義する。新規 schema は追加せず、既存の `events`、`metrics`、`feedback`、`verify_runs`、`gate_runs`、`plan_registry`、`entries`、`links` を使う。

## 2. State Machine

| State | Entry 条件 | Exit 条件 | 既存保存先 |
|---|---|---|---|
| `detected` | detector / doctor / hook / harness が finding を返す | signal が正規化される | command output, `hook_events`, `harness_check_events`, `verify_runs` |
| `registered` | `source_signal_id` と payload が DB evidence として保存される | route / learning の入力対象になる | `events`, `metrics`, `feedback`, `audit_log` |
| `candidate_generated` | route / learning / PLAN / PR candidate が出力される | candidate_id が adoption chain に記録される | feedback-loop snapshot, `metrics`, `feedback` |
| `plan_materialized` | PLAN / task が owner、allowed_files、acceptance、rollback を持つ | approved scope で実装に進める | `plan_registry`, handover log |
| `implementation_adopted` | approved files に差分が入り、trace 対象になる | 検証コマンドが実行される | `entries`, `links`, `code_index`, `test_design_entries` |
| `verification_recorded` | pytest / Bats / doctor / CI equivalent の結果が保存される | gate projection が生成される | `verify_runs`, `gate_runs`, `automation_runs` |
| `gate_projected` | original signal が absent / closed / monitored と表示される | recurrence 判定が記録される | doctor JSON, `gate_runs`, `metrics` |
| `recurrence_closed` | 同一 signal が再発しない、または owner 付き監視へ移る | goal audit へ採用可能になる | `feedback`, `metrics`, `goal-completion-audit.yaml` |

## 3. 冪等 key

重複登録を避けるため、正規化時に次の logical key を作る。

```text
candidate_id = sha256(source_category + source_signal_id + detector_name + pair + gate_id)
evidence_id = sha256(candidate_id + state + evidence_ref)
```

| Key | 用途 |
|---|---|
| `source_category` | `requirement_drift`, `vg_overview`, `hook_events`, `harness_check_events`, `verify_runs`, `feedback` |
| `source_signal_id` | finding ID、gate pair、hook event ID、verify run ID |
| `detector_name` | signal を出した検出器 |
| `pair` | `L6-L7`, `L5-L8`, `L4-L9`, `L3-L12`, `L1-L14` |
| `gate_id` | `G6`, `G7`, `G8`, `G9`, `G12`, `G14` など |

## 4. 状態別失敗扱い

| Failure | 判定 | Recovery |
|---|---|---|
| DB evidence 登録失敗 | candidate 生成不可 | `detected` のまま fail-close |
| candidate 生成のみ | closure 不可 | `candidate_generated` として残す |
| PLAN が owner / acceptance 不足 | 実装不可 | `plan_materialized` へ進めない |
| scope 外ファイルが必要 | interrupted / handover expansion | 勝手に実装しない |
| 検証未実行 | gate closure 不可 | `verification_recorded` へ進めない |
| gate に未反映 | recurrence closure 不可 | `gate_projected` へ進めない |
| 再発状態未記録 | full goal completion 不可 | `recurrence_closed` へ進めない |

## 5. 定量 / 定性の二重チェック

| チェック | 内容 | 現在フェーズでの扱い |
|---|---|---|
| 定量 | `requirement_drift`, `trace_symmetry`, `VG-overview`, pytest / Bats | L6 focus の合格判定に使う |
| 定性 | L4/L5/L6 設計書、L7 add-feature 起票、objective evidence matrix、goal audit | 設計漏れと completion boundary を確認する |
| 後半実走 | G8/G9/G12/G14、CI/equivalent、recurrence closure | DB evidence chain が揃った後に閉じる |

## 6. Non-goals

- `schema_migration=false`
- schema migration は行わない。
- `auto_apply=false`
- detector / gate の判定ロジックをこの文書だけで変更しない。
- candidate を自動で PLAN / PR に適用しない。
- `production_db_operation=false`
- production DB operation は現在スコープで行わない。
- L6 focus clean を full-flow completion として扱わない。
