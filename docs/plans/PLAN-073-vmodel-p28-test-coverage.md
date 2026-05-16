---
plan_id: PLAN-073
title: "PLAN-073: V-model P2-8 テスト 3 ケース追加 (PLAN-068 W-6 carry)"
status: completed
size: S
drive: be
created: 2026-05-16
completed_at: 2026-05-16
owner: PM
phases: L4
gates: G4
completion_evidence: |
  Sprint .1-.3 並列実装完了 (commit 3aab4c5):
  - test_vmodel_multi_drive.py (2 cases PASS)
  - test_drive_decisions_idempotent.py (2 cases PASS)
  - test_drive_decisions_atomic.py (3 cases PASS)
  pytest 7 cases、累積 1292 全 PASS、回帰 0。
acceptance:
  - vmodel_loader / helix-gate の drive resolve に対する以下 3 ケースをテスト追加:
    - multi-drive: 同一 plan で be/fe/fullstack が並存する場合の drive 解決
    - idempotent: 同じ drive_decision INSERT が複数回呼び出されても DB state が変化しない
    - atomic: drive switch policy 評価中の例外で部分 commit が起きない
  - 既存テストの回帰なし (pytest 1285 / bats 478 維持)
  - G4 coverage gate (core5 80%) を下回らない
related:
  - PLAN-068-vmodel-strengthening-improvements (W-6 carry 元)
  - PLAN-072-l4-5-integration (frozen、resolve_subgate_drive 実装基盤)
---

# PLAN-073: V-model P2-8 テスト 3 ケース追加

## §1 目的と背景

PLAN-068 (V-model 強化定義 carry 改善) の W-6 (P2-8 テスト) として、`multi-drive` / `idempotent` / `atomic` の 3 ケース pytest/bats テストが未追加のまま残っていた。
PLAN-072 完遂で v24 design_sprint_drive_decisions + helix-plan drive-decision サブコマンドが実装されたため、これらに対する coverage を補強する。

## §2 対象範囲

### 2.1 multi-drive ケース
- 同一 plan_id で be / fe / fullstack の 3 drive にまたがる entry が並存する場合の drive 解決
- `cli/helix-gate` の `resolve_plan_metadata_drive` / `resolve_subgate_drive` (line 326/360) 動作確認
- vmodel_loader.py が DB mutate ゼロで stateless 動作することの確認

### 2.2 idempotent ケース
- `insert_drive_decision` を同 (plan_id, source_entry_id, target_entry_id, decision) で複数回呼び出した時の動作
- DB state は最初の 1 回のみ変化、2 回目以降は no-op or ConflictError (設計判断による)
- pytest で 3 回呼び出しを行い、design_sprint_drive_decisions の行数が 1 のままを確認

### 2.3 atomic ケース
- drive switch policy 評価中に例外発生時、部分 commit が起きないこと
- `helix-plan drive-decision` 実行中に sqlite3 例外を inject → ロールバック確認
- design_sprint_drive_decisions / automation_runs が all-or-nothing で挙動

## §3 Sprint 構成

| Sprint | 目的 | 委譲先 | 対象ファイル |
|--------|------|--------|-------------|
| Sprint .1 | multi-drive テスト追加 | Codex pg | cli/lib/tests/test_vmodel_multi_drive.py |
| Sprint .2 | idempotent テスト追加 | Codex pg | cli/lib/tests/test_drive_decisions_idempotent.py |
| Sprint .3 | atomic テスト追加 | Codex pg | cli/lib/tests/test_drive_decisions_atomic.py |

Sprint .1-.3 は相互独立 → 並列投入可能。

## §4 受入条件詳細

- 各 Sprint で pytest 新規 test 1-3 ケース PASS
- 既存 pytest 1285 + bats 478 回帰なし
- core5 coverage 80% 維持

## §5 リスク

| ID | リスク | 深刻度 | 緩和策 |
|----|--------|--------|--------|
| R-01 | idempotent 動作が UNIQUE 制約違反 + WARNING で no-op か exception かが未定 | P2 | Sprint .2 で TL 判断、CHECK 制約 or UPSERT で挙動固定 |
| R-02 | atomic ロールバックが sqlite トランザクション制御依存 | P2 | helix_db._write_connection の autocommit 挙動を test fixture で確認 |

## §6 依存関係

- PLAN-068 (W-6 carry 元) — completed (本 PLAN への carry 化により)
- PLAN-072 frozen 前提 (helix-plan drive-decision 実装)

## §7 G4 entry 条件チェックリスト

- [ ] Sprint .1 multi-drive テスト PASS
- [ ] Sprint .2 idempotent テスト PASS
- [ ] Sprint .3 atomic テスト PASS
- [ ] coverage gate (core5 80%) 維持
- [ ] G4 ready 宣言

## §8 next action

次セッションで Sprint .1-.3 を Codex pg 3 並列投入。各 Sprint は size=XS-S なので 1 セッション内完遂可能。
