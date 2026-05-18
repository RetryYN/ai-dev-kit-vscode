---
plan_id: PLAN-085
title: "PLAN-085: cutover staging rehearsal and staged production cutover"
layer: L4
status: draft
size: M
drive: db
created: 2026-05-18
revised: 2026-05-18
owner: PM
phases: L1, L2, L3, L4, L7, L10
gates: G5, G6, G7
related_plans:
  - PLAN-084 (helix.db 6 分離 + Event Sourcing + projector)
  - PLAN-086 (rollback fault injection drill)
related_docs:
  - docs/adr/ADR-020-cutover-rollback-gates.md
  - cli/lib/cutover_orchestrator.py
  - cli/lib/rollback_orchestrator.py
  - cli/lib/shadow_replay.py
---

# PLAN-085: cutover staging 演習 → 本番投入 → 24h 監視 → 採用

## 1. 目的

ADR-020 で採用した cutover gate 5 + rollback gate 6 を、**staging 演習 → 本番 cutover → 24h 監視 → 採用**の順で実施し、`PLAN-084` の実装成果を本番適用する。

本計画のゴールは、以下を満たす事前演習済みの順序で採用を安全に確定すること。

- gate 5 (cutover) を stage 環境で `shadow_replay + 模擬 cutover` を伴う手順検証により再現
- gate 6 (rollback) を切替判定条件/操作性を含めて検証
- 本番切替後 24h の監視窓を確保し、`mismatch detector + projector lag` を継続監視
- carry 前提を PLAN-086 に分離し、実運用への影響を抑制

## 2. 前提と制約

- `docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md` の `Phase 4.C`（shadow replay / cutover orchestrator / rollback orchestrator）を前提とする。
- 本 PLAN は **PLAN-085 本体**として、PLAN-086（故障注入による rollback 試演習）を carry 末尾に分離する。
- `@helix:index` は本 PLAN doc では付与しない（code 資産のみ対象）。
- 本計画対象の編集は `docs/plans/PLAN-085-cutover-staging-rehearsal.md` のみ。
- cutover/rollback 実行の最終手順は PO 承認と外部 runbook に従う。

## 3. 受入条件

### Phase 1: staging 演習（shadow_replay + 模擬 cutover）

#### DoD
- 本番 dataset の sanitize copy（PII/secret 除去済み）を staging 用に用意し、`shadow_replay.replay_to_shadow_db()` が 1 回以上成功して `failed_count=0` を満たす。
- 連続 replay 実行時に「skip/failed/mismatch」率が事前閾値（failed 0、skip 可）に収まる。
- 模擬 cutover で `cutover_orchestrator.cutover_preflight()` が `ready=True` を通過。
- 監査ログ（preflight 出力、mismatch count、replay 時刻、実行者）を残す。

#### Rollback trigger
- sanitize copy 作成前後でデータ不整合（行数差分 > 1% など）を検知した場合。
- replay result の `failed_count > 0` が観測された場合。
- `replay limit` 到達前に projector 例外が 2 回以上発生した場合。

#### 監視 metric
- `shadow_replay` 実行件数、`failed_count`、`skipped_count`
- replay 実行時間（P95）と完了率
- replay 入力イベント数（event_id 増分）

#### 担当
- PO: 演習開始日と停止条件の承認、停止/継続判断
- PM: 対象データの sanitize copy 作成・保管・実行日程
- TL: 予測不能差分の root cause 分類、replay pipeline 健全性確認

### Phase 2: 本番 cutover（gate 5 通過後）

#### DoD
- 本番実施前に `cutover_orchestrator.cutover_preflight()` が blocker なしを満たす。
- PO 承認済み `confirm_token` を含む gate 5 実行 API/CLI を実施し、切替結果を `po_carry_required`/実施完了ステータスとして記録。
- 全 6 DB の write 経路切替が完了し、dual-write 期間中の write 到達率が 100% 監査できる。
- `cutover` 実施後 1h 時点で `projector lag` 警告が閾値内（既定: warn 100 / fail 1000）であることを確認。

#### Rollback trigger
- `cutover_preflight` が ready=False になった
- confirm token 未発行/不整合
- 実行直後に最初の 60 分で projection lag が fail-close 境界（1000）を超えた

#### 監視 metric
- `cutover_orchestrator.cutover_execute()` 実行結果（status / confirmed / preflight ブロッカー）
- dual-write write-through 成功率（6 db）
- `projector lag`（WARN 100 / FAIL 1000）

#### 担当
- PO: confirm_token 発行・承認・最終実行承認
- PM: 切替手順実行、イベント観測、運用連絡
- TL: 事前 checklist 監査、実行後 1h 側における障害診断

### Phase 3: 24h 監視

#### DoD
- 24h 継続監視の間、`mismatch detector` の critical 連続検知 0 回。
- projector lag が `warn=100` を超えるイベントを 24h 内で 1 回以下に抑制。
- `dual-write write-through` と `rollback preflight` を 24h 時点で再実行し、`can_rollback=True` を維持。
- 監視結果を時系列で記録し、PM 宛に 8h/16h/24h レポートを提出。

#### Rollback trigger
- mismatch detector critical が 24h 内に 2 連続以上発生
- projector lag が fail-close 境界（1000）到達
- `rollback_preflight()` が `can_rollback=False` へ遷移

#### 監視 metric
- mismatch count（critical / warning）
- projector lag（last_processed_event_id 差分）
- 24h 滞在中の write/replication 失敗率

#### 担当
- PO: 監視結果の受領可否判断（必要時「hot rollback」判断）
- PM: 監視運用、8h ごとのステータス更新と carry 作成
- TL: メトリクス異常時の技術診断と rollback 可否判断資料作成

### Phase 4: 採用宣言

#### DoD
- 24h 監視完了後に `ADR-020` を active 化するための採用判定資料を PM/PO/TL で共有。
- `PLAN-085` の AC すべてに対し green を付与。
- legacy db deprecation（停止計画/通知/監査）を開始し、`rollback window` 監視の継続責任を明示。

#### Rollback trigger
- 採用判定時点で PO が「hot rollback」を指示
- legacy rollback 不能を示唆する監査結果（backup 不整合、重要 event 欠損）

#### 監視 metric
- AC 通過率（100%）
- 監査レポート未処理項目数
- legacy deprecation 進捗（停止対象 DB / 予定日 / 監査完了）

#### 担当
- PO: 採用可否最終承認
- PM: LEGACY 停止計画実行
- TL: ADR 更新内容と実行証跡の技術レビュー

## 4. AC（Acceptance Criteria）

- AC-085-01: Stage rehearsal で sanitize copy を用いた shadow replay が `failed_count=0` で完了し、差分レポートが保存されること。
- AC-085-02: gate 5 preflight の blocker が消去されること（dual-write 健全性、mismatch 0、shadow replay 完了）。
- AC-085-03: 本番 cutover 実行時に PO 承認 token で実行され、preflight が ready の状態であること。
- AC-085-04: 本番 cutover 後 24h の `mismatch detector critical` が 0 件であり、`projector lag` fail-close（1000）未到達であること。
- AC-085-05: 24h 監視期間中に rollback preflight を再実行した際、`can_rollback=True` を維持し、rollback path 証跡（backup path / backup hash / diff_event_count）を保存すること。
- AC-085-06: 24h 監視完了時点で ADR-020 active 化可否を評価し、採用時は legacy db deprecation の開始報告が PM から承認されること。

## 5. リスク

- R-01: dual-write 期間が想定より延長し、dual-write 由来の読み書き競合が増加する（監視ノイズ・処理遅延）
  - 緩和: gate 4.2 で lag・mismatch・write error を可視化し、閾値超過時は cutover 延期を優先。
- R-02: mismatch alert の noise 増加で障害判定が遅延する
  - 緩和: 初回 24h は critical 直列監査を強化し、warning の上限値を文書化した playbook で抑制。
- R-03: 24h 監視中の hot rollback が発生し、運用 window と rollback window が競合する
  - 緩和: ロールバック演習（PLAN-086）で責務分離とオペ手順を事前固定し、実行手順を短縮。
- R-04: 本番 traffic で shadow replay を追加実施した場合の遅延増
  - 緩和: stage rehearsal と監視対象を分離し、本番直前は replay を観測ログ連携中心に縮退実行。

## 6. carry list

- [ ] PLAN-086: rollback 試演習（deliberate fault injection を含む rollback fault injection drill）を別 Plan として起票し実施する。
  - 目的: gate 6 の人手最短時間手順、backup manifest 検証、差分イベント数再現を強化する。

## 7. 参照

- docs/adr/ADR-020-cutover-rollback-gates.md
- docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md
- cli/lib/cutover_orchestrator.py
- cli/lib/rollback_orchestrator.py
- cli/lib/shadow_replay.py
