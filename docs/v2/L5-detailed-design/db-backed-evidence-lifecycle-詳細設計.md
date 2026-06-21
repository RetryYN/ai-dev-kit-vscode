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
freeze_readiness: design_closed_tl_rereviewed_approve_2026_06_21  # TL re-review approve (P0/P1=0)。status frozen flip は次の gate ceremony
closure_ledger: docs/v2/audit/2026-06-21-l1-l6-design-closure-ledger.yaml
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

## 6. 実行証跡の詳細（F2 — L4 §7 実行証跡コントラクトの L5 詳細化）

L4 §7（F2-1〜F2-3）を、既存 `verify_runs` / `gate_runs` / `automation_runs` 上の内部表現として詳細化する。新規 schema は追加しない（物理データ設計の既存列 + JSON payload を使う）。

### 6.1 exec status enum と遷移

`verification_recorded` への遷移を実行結果 status で分岐する（§2 の同状態を status 粒度で厳密化）。

| exec status | 意味 | `verification_recorded` 遷移 | pass 算入 |
|---|---|---|---|
| `exec_pass` | genuine artifact 裏付けの green | 可（6.3 の genuine 条件成立時のみ） | ○ |
| `exec_fail` | exit_code ≠ 0 | 不可（`implementation_adopted` へ差し戻し） | × |
| `exec_skipped` | `SKIP_EXEC_TESTS` 等で実行せず | **不可** | × |
| `exec_missing_evidence` | 実行主張はあるが artifact 不在 / 不整合 | **不可（fail-close）** | × |

`exec_skipped` / `exec_missing_evidence` は `verification_recorded` へ**遷移しない** = §4「検証未実行 → `verification_recorded` へ進めない」を status 粒度で厳密化（skip を pass に数えない）。

### 6.2 実行証跡の冪等 key

§3 の `candidate_id` / `evidence_id` に加え、実行証跡固有の key を作る：

```text
exec_evidence_id = sha256(run_id + commit_sha + target_pair + gate_id)
```

| Key | 用途 |
|---|---|
| `run_id` | `automation_runs` の実行 ID |
| `commit_sha` | 実行時 HEAD commit |
| `target_pair` | 検証対象 L-pair / UT-ID |

同一 `(run_id, commit_sha, target_pair)` の重複登録を排し、**別 commit の green を流用させない**。

### 6.3 artifact_sha256 の算出 / 検証

- **算出**: 実行出力（pytest / Bats stdout、JUnit XML 等）を正規化し sha256。
- **保存**: `automation_runs` / `verify_runs` の payload に `run_id` と紐付けて格納（既存列 + JSON、新規 schema なし）。
- **検証（genuine 条件）**: gate は `exec_evidence_id` で artifact を引き、`artifact_sha256` が実体と一致し かつ `exit_code=0` のときのみ `exec_pass` を genuine と判定（改ざん検知）。不一致 / 不在 = `exec_missing_evidence`。

### 6.4 gate 参照（再実行しない）

gate は変更 pair の exec_evidence を**参照のみ**で判定する（L4 §7 F2-2）。artifact が無い / genuine でなければ fail-close。gate 内で test を再実行しない（速度維持）。

### 6.5 定性レビュー証跡の詳細（F3 — L4 §F3-1 の L5 詳細化）

F3 `review_evidence`（L4 §F3-1 / L6 §3.2）を既存 DB 上の内部表現として詳細化する。新規 schema は追加しない。

- **保存**: review record を既存 `events` / `audit_log` の payload（JSON）に `review_id` と紐付けて格納。`review_output_sha256` はレビュー出力実体（tl-advisor / code-review JSON）を正規化した content hash。
- **冪等 key**: `review_evidence_id = sha256(review_id + reviewed_commit + review_output_sha256)`。同一レビューの重複登録を排し、別 commit のレビュー流用を弾く（F2 の `exec_evidence_id` と同型）。
- **検証**: detector（`review_evidence_checks.py`、実装済）が reviewer≠worker / sha256 一致 / commit 一致 / `tests_green_at <= reviewed_at` を判定。いずれか不成立は `review_genuine=false`（fail-close）。`tl_review=="approve"` の文字列一致のみでは genuine としない。

## 7. Non-goals

- `schema_migration=false`
- schema migration は行わない。
- `auto_apply=false`
- detector / gate の判定ロジックをこの文書だけで変更しない。
- candidate を自動で PLAN / PR に適用しない。
- `production_db_operation=false`
- production DB operation は現在スコープで行わない。
- L6 focus clean を full-flow completion として扱わない。
