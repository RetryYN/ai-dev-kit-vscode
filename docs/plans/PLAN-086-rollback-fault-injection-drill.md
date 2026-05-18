---
plan_id: PLAN-086
title: "PLAN-086: rollback 試演習 (deliberate fault injection を含む rollback fault injection drill)"
layer: L4
drive: db
status: draft
size: M
created: 2026-05-19
revised: 2026-05-19
owner: TL
gates: G6
audit_notes:
  - fault injection で gate 6 運用の最短復旧手順を事前検証する
phases: L1, L2, L3, L4
related_plans:
  - PLAN-085 (cutover staging rehearsal and staged production cutover)
  - PLAN-084 (helix.db 6 分離 + Event Sourcing + projector)
related_docs:
  - docs/adr/ADR-020-cutover-rollback-gates.md
  - cli/lib/rollback_orchestrator.py
  - cli/lib/cutover_orchestrator.py
---

# PLAN-086: rollback 試演習 (deliberate fault injection を含む rollback fault injection drill)

## 1. 目的

PLAN-085 の carry list 末尾で参照されている `PLAN-086` を正式起票し、本番 cutover 前に rollback path を事前検証する。
本 PLAN は gate 6 (rollback gate) の `rollback_preflight`/`rollback_execute` を対象に、
意図的な障害注入を用いた試演習を行い、
- rollback gate 6 の readiness 判定
- backup manifest 検証
- diff_event_count 再現
- 人手対応の最短時間手順
を強化する。

## 2. 前提と制約

- 対象環境は staging で実施し、PII/secret を含む本番データは使用しない。
- fault injection は本番 DB/サービスへの直接 destructive 操作を行わない。
- 実施は `docs/adr/ADR-020-cutover-rollback-gates.md` の gate 6 方針に準拠し、
  `backup_path` / `backup manifest` / `diff_event_count` の整合確認を必須とする。
- 実装コード変更は行わず、ドキュメント起票のみとする。
- 実施環境は `PLAN-085` の staging rehearsal で確立した環境を利用する。

## 3. Phase 1: fault injection 設計（staging 安全検証）

### 3.1 目的

- rollback 試演で再現しやすい障害を定義し、安全に staged で誘発する。
- false-positive でも本番障害に進展しない安全域を固定する。

### 3.2 施策対象（例）

- dual-write 期間中の `new_db` write fail（1回のみ、retry あり）
- projector lag spike（意図的な遅延注入）
- mismatch detector の false-positive 注入（条件付きしきい値破り）
- `shadow_replay` diverge（差分イベント再送時の再現）

### 3.3 DoD

- [ ] 故障注入ケースを 1 画面で一覧化し、各ケースに `注入条件 / 期待結果 / 取り消し手順 / ロールバック` を登録している。
- [ ] すべての fault injection が staging のみで実行され、実データ障害を起こしていない。
- [ ] 注入後の log/メトリクス（write fail 件数 / projector lag / mismatch 件数 / replay 停止状態）が収集可能。
- [ ] 全ケースで rollback 試演のために復元手順が実行可能。

### 3.4 失敗時 escalation

- fault injection で staged DB/アダプタが復元不能になった場合: `TL` が即時停止し `SRE` が影響範囲を確認、`PM` にエスカレーション。
- 注入後の観測が収集不能になった場合: `PO` 承認なしで本番演習に進めない。
- 同一ケースで 2 回目失敗: `TL` は `PLAN-086` を blocker 扱いとして `PLAN-085` 連携スケジュールを再調整。

### 3.5 担当

- PO: staging での stop/continue 判定、障害注入実施可否承認
- PM: ケース作成、実施記録、通知テンプレート
- TL: 注入条件/観測項目設計、再現性検証
- SRE: 監視指標監査、復旧手順事前チェック

## 4. Phase 2: rollback orchestrator 動作確認（gate 6 manual + automated drill）

### 4.1 目的

- `rollback_orchestrator.rollback_preflight()` と `rollback_execute()` を gate 6 path 上で検証する。
- backup manifest と `diff_event_count` を再現条件として固定する。

### 4.2 DoD

- [ ] `rollback_preflight()` が以下項目を必ず返すことを確認する。
  - `backup_exists=true` / `manifest_exists=true`
  - `backup_integrity_ok=true`
  - `diff_event_count` が数値として返る
  - `can_rollback=true`
- [ ] `ROLLBACK_CONFIRM_TOKEN` 未設定時/誤 token 時は `rollback_execute()` が停止し、原因を通知できる。
- [ ] `backup_path` 不一致時に `rollback_execute()` が失敗する。
- [ ] `rollbar / slack / on-call` 含む通知経路で preflight 失敗・実行失敗の 1 事象を再現し、受信先が確認可能。
- [ ] `on-call` チャネル（実稼働通知）へ試演結果 1 つ以上をエスカレーションできる。

### 4.3 失敗時 escalation

- `backup manifest` の不整合/不在は gate 6 停止。
- `rollback_execute()` が token 以外理由で失敗した場合、`TL` が原因を `PLAN-085` に carry し、本番再開を停止。
- `diff_event_count` 未再現の場合、`PM`/`SRE` 合意で注入ケースを見直し再設計。

### 4.4 担当

- PO: rollback 実施ルール確認、confirm token 運用の監査
- PM: 自動試演シナリオ作成、通知テンプレート管理
- TL: orchestrator 仕様確認、結果記録・DoD 判定
- SRE: on-call 受信確認、通知経路検証

## 5. Phase 3: 人手最短時間手順の確定（SLA playbook 化）

### 5.1 目的

- rollback 発動時の人的手順を 3 段階で短縮し、実運用の初動時間を縮める。

### 5.2 SLA（段階別）

- 5 分: 初動通知受理〜`rollback_preflight()` 完了
- 15 分: rollback execute 準備（token, backup manifest, diff_event_count, 環境状態）完了
- 30 分: rollback 実行判定→実行結果サマリ共有

### 5.3 DoD

- [ ] S1, S2, S3 それぞれの手順書に、実行者、確認者、ロール、実行コマンド、成功/失敗分岐を明記。
- [ ] `backup manifest` 検証と `diff_event_count` 再現が playbook 内の必須必達チェックに含まれる。
- [ ] 計測で 5/15/30 分 SLA を超えた事例を 1 つ以上登録し、再発防止策を添付。
- [ ] 演習当日に各ロールが 1 回以上アクティブに起動し、handover 可能なログが残る。

### 5.4 失敗時 escalation

- 5 分以内に preflight に失敗した場合: PO/TL/SRE が同時に `rollback_pause` を実施、`PLAN-085` に影響を連携。
- 15 分以内に token/manifest/diff が揃わない場合: PM が復旧可否を再判定し、`hot rollback` 条件を再評価。
- 30 分で `rollback_execute()` を完了できない場合: 本番入場前 gate 判定を hold（`can_rollback=false`）。

### 5.5 担当

- PO: 指示権限、最終停止判断
- PM: Playbook 実行ログと時間計測
- TL: 技術手順化、失敗条件の分岐ルール設計
- SRE: オンコール手順、通知/エスカレーション運用

## 6. Phase 4: PLAN-085 接続（gate 6 ready 判定への組み込み）

### 6.1 目的

- PLAN-085 に対し、`PLAN-085` gate 6 ready 判定の受入条件を追加し、試演結果を運用判断に反映する。

### 6.2 DoD

- [ ] PLAN-085 の `Phase 1/2/3` に、`PLAN-086` 結果を反映する carry 受入リンクを追加。
- [ ] PLAN-085 gate 6 判定項目に以下を追加:
  - rollback preflight の `can_rollback` true
  - manifest 署名（sha256）一致
  - `diff_event_count` ログ保存
  - on-call 通知 path が生存
- [ ] 試演結果レポート（Pass/Fail, 根本原因, 再試験日）を 1 文書に纏める。
- [ ] 本番 cutover 前提条件に「PLAN-086 成果の承認」を追加する。

### 6.3 失敗時 escalation

- `PLAN-085` の carry 判定が満たせない場合は gate 6 を hold、次回 slot に carry 継続。
- リハーサル結果の欠落が発覚した場合は `TL` が承認前に再演習要求。

### 6.4 担当

- PO: PLAN-085 反映同意、hold 判断
- PM: 連携記録、carry 更新
- TL: 判定条件最終化、受入条件反映
- SRE: 実運用連携項目の妥当性確認

## 7. 受入条件（Acceptance Criteria）

- AC-086-01: Phase 1 の fault injection 4 ケースを staging で再現し、再現手順と巻き戻し手順を `docs/` 内に記録している。
- AC-086-02: 全 fault injection ケースで障害注入中に「本番資産不変」「PII/secret 非接触」を満たす。
- AC-086-03: gate 6 manual 試演で `rollback_preflight` が `can_rollback=true` を返すことを 1 回以上確認する。
- AC-086-04: gate 6 実行経路で `rollback_execute` の認可エラー、backup 不一致、backup 破損など 3 種の失敗シナリオを再現し、原因通知が残る。
- AC-086-05: backup manifest の `expected_sha256` 一致チェックが必須項目としてドキュメント化され、検証結果が保存される。
- AC-086-06: `diff_event_count` を再計算し、最終結果が実行ログと一致することを確認する。
- AC-086-07: 人手 playbook の 5/15/30 分 SLA を 1 回ずつ検証し、実績を報告する。
- AC-086-08: PLAN-085 gate 6 判定に `PLAN-086` の受入完了条件を組み込み、承認者がレビュー可能な状態にする。

## 8. リスク

- R-086-01: staging fault injection が予期しない本物の障害を起こし、staging で復元不能になる。
  - 緩和: 事前に停止条件を固定し、最小データセットで1ケースずつ実施。
- R-086-02: backup manifest の整合性不一致により `can_rollback=false` となり、再演習頻度が上がる。
  - 緩和: manifest 生成と保存手順を事前固定し、sha256 検証手順を playbook 化。
- R-086-03: rollback 後に forward 再進行可否判断が不明瞭で、再 cutover 方針が遅れる。
  - 緩和: `diff_event_count` と replay 方針を事前に合意し、PLAN-085 側で hold 条件へ反映。
- R-086-04: 人手手順の SLA 超過で判断が遅延し、対応時間が目標を超える。
  - 緩和: RACI とコマンド実行順序を固定し、各ステップの責任者を明記。

## 9. carry list

- [ ] 本番環境での chaos engineering (game day 演習) を別 PLAN として作成し、`PLAN-087` へ carry。
  - 目的: 本番規模での fault injection / rollback readiness / on-call 対応を game day 形式で検証する。
  - 反映先: 本 PLAN 成果の承認済み項目を継承し、PLAN-085 本番切替後に実施。

## 10. 参照

- docs/adr/ADR-020-cutover-rollback-gates.md
- docs/plans/PLAN-085-cutover-staging-rehearsal.md
- cli/lib/cutover_orchestrator.py
- cli/lib/rollback_orchestrator.py
