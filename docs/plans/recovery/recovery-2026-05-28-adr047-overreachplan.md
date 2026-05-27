---
plan_id: recovery-2026-05-28-adr047-overreach
title: "recovery-2026-05-28-adr047-overreach: ADR-047 過剰起票・工程逸脱の収束 (recovery-log)"
kind: recovery
layer: recovery
drive: be
status: completed
created: 2026-05-28
owner: PM
parent_process: HELIX-workflows/helix-process/recovery-workflow.md
generates:
  - artifact_path: docs/plans/recovery/recovery-2026-05-28-adr047-overreachplan.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/recovery-workflow.md
  - HELIX-workflows/helix-process/add-feature-workflow.md
related_memory:
  - feedback_plan_doc_adr_layer_vmodel_order
  - feedback_vmodel_pair_judge_by_trace_not_file
---

# Recovery Log: ADR-047 過剰起票・工程逸脱の収束

> **mode**: Recovery (kind=recovery)
> **正本**: HELIX-workflows/helix-process/recovery-workflow.md
> **本 log の対象**: 2026-05-28 session で AI エージェント (Claude Code) が起こした独断専行・暴走を、ガード → 収束 → 再開ポイント確定の手順で収束させた記録。

## §1 発火条件 (なぜ Recovery が発火したか)

Recovery workflow の発火条件 4 種のうち 3 種に該当:
- **認識のズレが蓄積し収拾がつかない**: PLAN / doc / ADR の役割と V モデルの設計順序・粒度を取り違えたまま作業を継続
- **工程逸脱**: V モデルの順番 (L1 要求 → L3 → L4 → L5 → L6) を無視し、いきなり L4 / ADR から手をつけた
- **想定外大規模変更**: ADR-047 (740 行) + L9 4 PLAN + L6 1 PLAN を過剰起票

## §2 認識訂正履歴 (軌跡)

ユーザーが 10+ ターンで段階的に是正した認識のズレ:

| # | ユーザー指摘 | 訂正された認識 |
|---|---|---|
| 1 | 「V-model 守ってる? PLAN 起票雑」 | 場当たり起票への警告 (ガード検出) |
| 2 | 「テスト要件作るの楽そう」 | L8/L9 doc は既に揃っている (L4 PLAN が generates 済)、L9 PLAN は過剰 |
| 3 | 「V2 完全移行と旧プラン」 | 旧資産 (ADR-041/042 旧形式) を正本扱いしていた |
| 4 | 「041/042 みたいな番号」 | ADR 42 個の乱立 (Proposed 16 滞留) |
| 5 | 「旧は参考、正本にしないルール」 | 旧 ADR を amend/supersede する発想自体が誤り |
| 6 | 「どういう順序で進める?」 | 場当たり対応で工程順序がない |
| 7 | 「PLAN は設計書ではない」 | PLAN を設計書と混同していた |
| 8 | 「設計書を作るための進め方」 | PLAN = 工程間変換の進め方 |
| 9 | 「PLAN は手順と軌跡」 | PLAN の本質定義 |
| 10 | 「メモから設計 doc に昇華しないと散らばる」 | 「削除」でなく「doc に昇華」が正解 |
| 11 | 「進め方と要点書、ヒアリングシート」 | PLAN の中身 = 進め方 + 要点書 + ヒアリングシート |
| 12 | 「いきなり L4 直すな、L1 から」 | V モデルは L1 から積む |
| 13 | 「判断を ADR に? V モデルの順番ってなんだよ」 | 判断を ADR に分離は誤り、判断は PLAN 要点書 + doc に |
| 14 | 「ADR は機能設計の粒度じゃないのか」 | ADR-047 の中身 (Routing/schema) は L6 機能設計の粒度 |
| 15 | 「これは要求だろ」 | Reverse Gateway Profile は要求 (L1) が起点 |
| 16 | 「機能要求の話だろ」 | L1 機能要求 (FR) |
| 17 | 「追加機能モデルワークフローがあるだろ」 | 既存システムへの追加機能 = Add-feature mode |
| 18 | 「暴走の時のリカバリーワークフローだろ」 | 今 session の暴走 = Recovery mode |

## §3 ロールバック (実施済)

| commit | 内容 |
|---|---|
| a3ad0dd | 過剰起票した L9 4 PLAN + L6 概要 PLAN を revert |
| 7df2ea3 | ADR-047 撤回 (設計内容を ADR に詰めた誤り) + L0 sibling_adr revert + index.md entry 削除 |

## §4 再開ポイント (進め方 — 標準フロー復帰)

- **現状の正本**: HELIX-workflows V2 dogfooding は L0-L9 設計書 (doc) が正本として揃っている。PLAN は進め方 (工程表 + 進捗) として機能している
- **次の作業**: Reverse Gateway Profile (= 既存システムへの追加機能) を **Add-feature mode** で扱う
  1. 影響範囲特定 (既存 L1 FR / L4 §2.4 / L6 / route_engine のどこに影響するか)
  2. 追加要求: L1 機能要求 (functional-requirements.md §1「Mode/Gate: Forward 復帰 event」) に FR 追補
  3. 追加設計 (kind=add-design): L4 §2.4 / L5 / L6 機能設計に追補、既存 design PLAN に requires
  4. 追加実装 (kind=add-impl): L7 route_engine 契約拡張、既存 impl PLAN に requires
  5. 既存テスト影響確認 + 追加テスト: L8 / L9
- Add-feature も Non-Forward mode のため、Reverse 経由で L0-L14 正本に追補反映 (双方向 trace)

## §5 再発防止 (ヒアリングシート + L14 フィードバック)

### 確定済の再発防止策
- memory feedback 記録済: [[feedback_plan_doc_adr_layer_vmodel_order]] (PLAN/doc/ADR 役割 + V モデル順・粒度) / [[feedback_vmodel_pair_judge_by_trace_not_file]] (片肺判定は trace 精査)

### L14 運用検証へフィードバックする確認事項 (ヒアリングシート)
- [ ] 「ユーザーが求めたもの = 要求 (L1)」を起点に置く習慣を framework lint で機械強制できるか
- [ ] ADR 起票前に「これは要求/機能設計/単なる doc ではないか」粒度チェックを gate 化できるか
- [ ] 既存システムへの変更は Add-feature mode を default にする判定を route_engine に組めるか
- [ ] AI が「いきなり下流 (L4/ADR) から書く」のを PreToolUse hook で警告できるか
