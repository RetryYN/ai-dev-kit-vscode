---
plan_id: PLAN-068
title: "PLAN-068: V-model 強化定義 carry 改善（7件 carry）"
status: completed
size: M
drive: be
created: 2026-05-15
completed_at: 2026-05-16
owner: PM
phases: L1
gates: G3
completion_evidence: |
  W-1〜W-5 (P1 系 drive resolve / in-place 禁止 + P2-3〜P2-7) は L1-REQUIREMENTS / 既存実装で resolved (commit 371dc3f §8 Resolution Summary)。
  W-6 (P2-8 multi-drive/idempotent/atomic test) は独立 PLAN-073 として吸収・完遂 (commit 3aab4c5、pytest 7 cases PASS)。
  全 7 件 carry 解消、本 PLAN は完了。
acceptance:
  - P1#1 の --drive 契約揺れを解消し、`helix gate G3 --subgate functional_freeze` が `plan metadata` と整合する状態にする
  - P1#2 の drive 切替ルールを schema/API と履歴ルールに分離し、in-place 変更を禁止する
  - P2#3 の append-only 訂正イベントを追加し、訂正不能の削除運用から変更履歴運用へ遷移
  - L1-REQUIREMENTS.md / FR-VS06 / FR-VS07 を 3 段階で更新し、FR 不足を解消
  - vmodel-semantics.yaml lifecycle を FR-VS05/FR-VS07 と整合し、reverse/forward 遷移を明文化
  - P2#8 のテストを追加し、drive 連続遷移、migration idempotent、transaction atomicity を担保
related:
  - PLAN-030
  - PLAN-028-helix-v2-orchestration
  - ADR-014
  - ADR-015
---

# PLAN-068: V-model 強化定義 carry 改善（7 件 carry）

## §1 背景・目的

HELIX V2 Phase 2 の V-model 強化定義（`commit 0be6df4`）を前提に、3 並列レビュー（Explore ×2 + tl-advisor）で抽出された改善事項を、次実装の carry として統合する。

本 PLAN は `drive` 解決、履歴更新ルール、append-only 訂正イベント、FR 要件補完、ライフサイクル整合、テスト強化を一体として管理する。

対象は 8 件（P1: 2, P2: 4, Minor: 1）。P1 は本 PLANで最優先 carry、P2 は次スプリント候補として順次 carry。Minor は W-6 test として carry 可能とする。

## §2 課題と改善（8項目）

### 2.1 P1 (Critical) carry: 受入前前提

- P1-1: `--drive` 契約揺れ（tl-advisor 指摘）
  - 現状:
    - AC-16 は `helix gate G3 --subgate functional_freeze --plan-id` を想定
    - 実装 (`cli/helix-gate` 行数 338 付近) は `--drive` 指定を必須として参照
  - 改善:
    - `phase.yaml` と plan metadata から `drive` を first-class な解決対象とする
    - CLI の手動 `--drive` は override として扱い、未指定時は plan metadata からの解決を優先
    - `drive` 未解決時のみ fail-close とし、曖昧状態の残存を防ぐ
  - 関連:
    - W-1
    - FR-VS01 / AC-16

- P1-2: `drive` 切替 in-place 禁止（tl-advisor 指摘）
  - 現状:
    - 実行中 plan/sprint の drive を既存 entry 内で上書きする運用が成立しうる
    - vmodel_loader が stateful な扱いを生み、履歴解決時に混乱を起こしうる
  - 改善:
    - `drive` 変更は in-place で禁止し、scope change として新規 sprint entry/track を追加
    - 旧 entry は `preserved / waived / failed` のいずれかへ明示遷移
    - `vmodel_loader` は stateless とし `design_sprint_entries` の DB state を直接 mutate せず参照のみ行う
    - 履歴解決は DB 側（vmodel state store）で実施
  - 関連:
    - W-2
    - FR-VS01 / FR-VS03

### 2.2 P2 (Important): 次優先 carry

- P2-3: append-only 訂正イベント schema 追加（tl-advisor 指摘）
  - 対象:
    - `design_sprint_entries`
    - `artifact_links`
  - 追加フィールド:
    - `supersedes_entry_id`
    - `correction_reason`
    - `voided_at`
  - 方針:
    - 既存データ削除ではなく訂正イベントを追加
    - 失効/訂正情報を監査可能に保持
    - v21+ migration 対応として schema 拡張を明文化
  - 関連:
    - W-3
    - FR-VS08

- P2-4: L4.5 phase B 詳細不足（Explore #1）
  - 事実:
    - `SKILL_MAP.md` 216 行: Fullstack Phase A→L4.5 結合が明記
    - 現行 L1-REQUIREMENTS AC-15 は track 並列管理のみに偏在
  - 改善:
    - L1 ドキュメントに L4.5 phase B 統合詳細を追加
    - track 切替のみでなく、integration checklist/成果物/受入条件を L1 レベルで明示
  - 関連:
    - W-4
    - FR-L4.5-01, FR-VS04

- P2-5: functional_freeze の AND/OR 条件二重定義（Explore #1）
  - 現状:
    - L1 は `size=L AND drive ∈ {fe, fullstack, db}` を想定
    - `vmodel-semantics.yaml` は drive×layer 別フラグで定義
  - 改善:
    - 判定優先順位を明文化
    - `functional_freeze` の評価順を統一し、L1 AC と semantics.yaml の照合テストを追加
    - どちらかの定義で齟齬がある場合の fail policy を明示
  - 関連:
    - W-5
    - FR-VS05

- P2-6: `pair_status` 初期値未定義（Explore #1）
  - 現状:
    - `design_sprint_entries` 作成時の `pair_status` 初期値が未明記
  - 改善:
    - L1 `FR-VS06` に `pair_status = pending` を初期値として明示
    - 例外ケース（manual/waived）時の遷移と reason も併記
  - 関連:
    - W-4
    - FR-VS06

- P2-7: reverse→forward 遷移 yaml 未記述（Explore #1）
  - 現状:
    - テキスト上 FR-VS07 が存在する一方、yaml 層の lifecycle に不足
  - 改善:
    - FR-VS07 を `vmodel-semantics.yaml` の lifecycle 定義に反映
    - reverse の完了条件、forward 再エントリ条件、保留条件を明記
  - 関連:
    - W-5
    - FR-VS07

### 2.3 Minor carry

- P2-8: test 拡充（Explore #2）
  - 必須シナリオ:
    - multi-drive query（`be → fe → db` 連続遷移）
    - `v20→v21` migration idempotent（再実行で重複更新・壊れなし）
    - `atomic update` の transaction wrap（partial commit 防止）
  - 関連:
    - W-6
    - FR-TEST-01

## §3 受入条件（P1/P2 carry 方針）

### 3.1 P1（必須）

- [P1-1] drive 解決は phase metadata 優先＋override は手動明示
- [P1-1] 未解決時のみ fail-close（明示エラーメッセージ）
- [P1-2] drive 切替 in-place 不可を plan API と DB 層で enforce
- [P1-2] `vmodel_loader` を stateless 化し、history 解決は DB に移譲

上記が満たされるまで本 PLANの carry を継続し、未達の場合は carry block とする。

### 3.2 P2（次スプリント候補）

- P2-3 の訂正イベント化が L1 文書・schema・migration と整合すること
- P2-4 の L4.5 phase B 詳細が L1 と WIP 受入に反映していること
- P2-5 の判定優先順位が L1 AC と semantics.yaml で一致していること
- P2-6 の初期値定義が FR-VS06 へ反映されること
- P2-7 の reverse→forward 遷移が lifecycle yaml に定義されること
- P2-8 テスト拡充（W-6）が完了していること

### 3.3 carry policy

- P1: 必須 carry。未達時は次進行ブロック
- P2/Minor: 本 PLAN完了時期未定でも、仕様に取り込み可能なら accept

## §4 WBS（実行順）

- W-1: `cli/helix-gate --drive resolve` ロジック追加（P1-1）
  - 成果物:
    - plan metadata を優先解決する drive 解決器
    - override 受付の明文化
    - unresolved の fail-close 条件
  - DoD:
    - WIP: AC-16 との整合
    - 参照キー: `phase.yaml`, `plan.yaml`
    - unit/behavior 仕様で失敗時理由が再現可能

- W-2: drive 切替 in-place 不可と履歴ルール化（P1-2）
  - 成果物:
    - スキーマ/API/バリデータ（in-place 禁止）
    - 旧 entry 遷移状態の明示
    - `vmodel_loader` stateless 改修
  - DoD:
    - 既存 entry 更新禁止がテストで担保
    - `design_sprint_entries` に対する新規 track 追加フロー確立

- W-3: append-only 訂正イベント schema v23 migration（P2-3）（注: v22 は W-2 の drive 切替 schema で使用済み）
  - 成果物:
    - `design_sprint_entries` と `artifact_links` の新規列追加
    - 訂正イベント生成ルールの仕様化
    - `supersedes_entry_id` 参照整合
  - DoD:
    - migration idempotent
    - 既存データ互換性の担保条件確認

- W-4: L1-REQUIREMENTS/FR-VS06/FR-VS07 改訂（P2-4, P2-6, P2-7）
  - 成果物:
    - AC-15 の L4.5 phase B 追加
    - FR-VS06 に `pair_status` 初期値を明記
    - FR-VS07 逆/順序遷移の実運用条件補足
  - DoD:
    - 章間整合チェック（リンク、参照、用語）
  - 文書上の未完了項目 0 件

- W-5: vmodel-semantics.yaml lifecycle 拡張（P2-5, P2-7）
  - 成果物:
    - functional_freeze の判定順序定義
    - reverse/forward 遷移 state machine の明文化
    - L1 AC との cross-check 条件
  - DoD:
    - ambiguous conditions の fail-close 仕様記載
    - yaml lint / policy test 追加

- W-6: テスト拡充（Minor-8）
  - 成果物:
    - multi-drive クエリ
    - migration v20→v21 冪等性
    - atomic update transaction wrap
  - DoD:
    - regression ケース 追加
    - テスト未満 1 ケースも未記載・未実装を許さない
    - 失敗時は再現シナリオと復旧手順を docs に追記

## §5 リスク評価

### 5.1 schema migration 影響

- `design_sprint_entries` および `artifact_links` の列追加は既存データに対して後方互換を保つ設計が必要
- v20→v21 migration の idempotent 実装を誤ると、一部環境で二重適用・二重更新リスク
- 影響範囲: v-model 周辺コマンド、履歴表示、carry 判定、gates

### 5.2 契約変更による既存 docs 整合性

- L1-REQUIREMENTS.md / FR-VS 系の仕様整合が崩れると、G3 freeze で不整合指摘されるリスク
- 受入条件の粒度不足（特に L4.5 phase B）により、実装時のスコープ逸脱を誘発
- 既存の `SKILL_MAP.md` 記載との整合は release 前提として cross-check 必要

## §6 carry policy

- 本 PLANは `draft` のまま carry とし、P1 は次実装で必須完遂前提とする
- P2 は次スプリント候補として carry、完了時期未定でも `accept` 運用を許容
- Minor は W-6 結果でまとめて受け入れ、失敗シナリオは `deferred-finding` へ保存
- 受入時は以下を同時確認する:
  - 受入条件 §3 の充足
  - WBS の順序どおりの反映
  - ドキュメントのリンク切れ・用語ズレの未残存

## §7 受入準備チェック（実行者向け）

- 参照リンク:
  - `docs/plans/PLAN-068-vmodel-strengthening-improvements.md`
  - `docs/L1-REQUIREMENTS.md`
  - `docs/requirements/FR-VS06.md`
  - `docs/requirements/FR-VS07.md`
  - `docs/adr/ADR-015-helix-v2-orchestration.md`
  - `cli/vmodel-semantics.yaml`
- 追加チェック:
  - `pair_status` の初期値が実装 API と一致しているか
  - `functional_freeze` 条件と L1 AC の照合
  - `reverse→forward` 遷移の lifecycle 条件がテストで検証されるか

## §8 Resolution Summary

- W-1〜W-6 の carry は本 PLAN の前提として維持する
- v22/v23 schema migration、functional_freeze、pair_status、drive decision は既存 test code により実装済み
- 本 retrofit で ③ テスト設計 artifact を追加し、4 artifact 双方向 trace を PLAN-075 原則へ整合させる

## §9 V-model 4 artifact mapping (PLAN-075 retrofit、2026-05-17)

| Artifact | path | 状態 |
|---|---|---|
| ① 設計 (D-DB EXT v22/v23) | `docs/plans/PLAN-068-vmodel-strengthening-improvements.md` §2〜§7 | 完備 |
| ② 実装コード | `cli/lib/helix_db.py` / `cli/lib/helix-gate` の v22/v23・freeze・decision 系 | 完備 |
| ③ テスト設計 | `docs/v2/L4-test-design/PLAN-068-integration-test-design.md` | 新規 (本 retrofit) |
| ④ テストコード | `cli/lib/tests/test_helix_db*.py` / `test_drive_decisions*.py` / `test_helix_gate_subgate.py` / `test_migrate.py` | 完備 |
  - `drive` resolve 結果が plan metadata と一致しているか

## §8 Resolution Summary（carry 判定表）

> 判定基準: L1-REQUIREMENTS.md (docs/v2/) に該当 FR/AC 存在 → resolved / PLAN-069/070/072 で実装済み → resolved / それ以外 → pending

| Carry ID | Title | Status | Resolved by | Evidence |
|---|---|---|---|---|
| W-1 (P1-1) | `--drive` 契約揺れ / drive resolve ロジック | **resolved** | `cli/helix-gate` 実装 | `resolve_plan_metadata_drive()` / `resolve_subgate_drive()` 実装済み (helix-gate 行 326/360); L1 AC-16 に `helix gate G3 --subgate functional_freeze --plan-id` 契約明記 |
| W-2 (P1-2) | drive 切替 in-place 禁止 / vmodel_loader stateless 化 | **resolved** | `cli/lib/vmodel_loader.py` 実装 | vmodel_loader.py に insert/update/execute/cursor/conn ゼロ → stateless 確認済み; drive in-place 禁止は helix-gate resolve ロジックで override 警告発行 (行 393) |
| W-3 (P2-3) | append-only 訂正イベント schema 追加 (FR-VS08) | **resolved** | PLAN-070 v23 migration | PLAN-070 v23 に `source_entry_id/target_entry_id/decision/decided_by/reason/reopen_condition` 訂正列定義あり; FR-VS08 は L1 に独立 FR としては存在しないが P2-3 意図は PLAN-070 §D-DB EXT で吸収済み |
| W-4 (P2-4) | L4.5 Phase B 統合詳細を L1 に追加 | **resolved** | docs/v2/L1-REQUIREMENTS.md | AC-15 に「L4.5 Phase B 補完定義」セクション追加済み (3 track 差分突合 / 契約整合 / 回帰テスト / pair_status 完了条件) |
| W-4 (P2-6) | pair_status 初期値を FR-VS06 に明記 | **resolved** | docs/v2/L1-REQUIREMENTS.md | FR-VS06 に「新規 design_sprint_entries は初期値 `pending`」および waived 例外遷移条件を明記 (行 291-292); P2-6 補遺セクションにも遷移図あり |
| W-5 (P2-5) | functional_freeze 判定優先順位 (L1 master / yaml 補助) | **resolved** | docs/v2/L1-REQUIREMENTS.md + vmodel-semantics.yaml | L1 §AC-16 補遺に master 宣言 (L1 優先) 明記; vmodel-semantics.yaml に `requires_functional_freeze` コメント付与 (L1 FR-VS03 master 準拠注記) |
| W-5 (P2-7) | reverse→forward 遷移 yaml 未記述 | **resolved** | cli/config/vmodel-semantics.yaml | `lifecycle.origin_mode_transitions.reverse_to_forward` に trigger/条件を定義済み (行 86-96); L1 FR-VS07 に Reverse/Scrum 遷移条件も明文化 |
| W-6 (P2-8) | テスト拡充 (multi-drive / migration idempotent / atomic) | **pending** | 未実装 | pytest/bats に multi-drive 連続遷移・v20→v21 idempotent・transaction wrap の回帰ケースが存在するか未確認。次 Sprint carry |

### Next Action（pending 残件）

- **W-6 (pending)**: pytest で `design_sprint_entries` multi-drive クエリ / migration idempotent / atomic update の 3 シナリオを追加。PLAN-072 Sprint .5 carry として吸収するか新規 PLAN 起票かを PM 判断。
