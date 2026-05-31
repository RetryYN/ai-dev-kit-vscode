---
plan_id: recovery-2026-06-01-context-injection-dist-strategy
title: "recovery-2026-06-01-context-injection-dist-strategy: 未承認・V2外の配布戦略(戦略C)を常時注入 context へ確定記述した自己永続ドリフトの収束 (recovery-log)"
kind: recovery
layer: recovery
drive: be
status: draft
created: 2026-06-01
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 収束方針・本筋復帰の判断"
  - role: tl-advisor
    slot_label: "TL — 処置妥当性 adversarial check / 再発防止住所設計"
  - role: pmo-sonnet
    slot_label: "PMO — 認識訂正履歴・汚染源 timeline 整合確認"
parent_process: HELIX-workflows/helix-process/recovery-workflow.md
generates:
  - artifact_path: docs/plans/recovery/recovery-2026-06-01-context-injection-dist-strategyplan.md
    artifact_type: markdown_doc
  - artifact_path: CLAUDE.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/recovery-workflow.md
  - HELIX-workflows/helix-process/document-topology.md
  - docs/plans/refactor/refactor-2026-06-01-folder-structure-g-p-separation.md
  - docs/plans/PLAN-218-helix-framework-package-export.md
related_memory:
  - feedback_plan_doc_adr_layer_vmodel_order
  - feedback_stay_in_requested_phase_scope
  - feedback_read_integrated_plan_before_carry_list
---

# Recovery Log: 未承認・V2外の配布戦略(戦略C)を常時注入 context へ確定記述した自己永続ドリフトの収束

> mode: Recovery（kind=recovery、L 非属の横断モード）
> 正本: [recovery-workflow.md](../../../HELIX-workflows/helix-process/recovery-workflow.md)
> 本 log の対象: 「dist publish / 戦略C」という V2 移行スコープ外・未承認の配布戦略が、常時注入される project CLAUDE.md と PM auto-memory に「2026-06-01 確定」として焼き込まれ、以降の session で PM が無批判に backlog として復唱した context injection（自己永続ドリフト）。本 log でその収束（excise + park + 再発防止住所設計）を記録し、本筋（柱1 gate-policy）へ Forward 復帰する。

## §1 発火条件（なぜ Recovery が発火したか）

recovery-workflow 入口判定 4 種のうち、本件は以下 2 種に該当する。

- **独断専行で工程・設計から逸脱した**: 配布戦略（戦略C: monorepo + dist publish）は distribution architecture という V モデル外の判断であり、Forward の L1（要求）/ L4（基本設計）を通さず、また ADR（不可逆判断の正本）も起票されないまま、常時注入される project CLAUDE.md に「確定」として記述された。
- **認識のズレが蓄積し収拾がつかない**: 常時注入された「戦略C 確定 / 次=dist publish P1」を毎 session PM が context で読み、優先 backlog として復唱。ユーザーが本 session で「これはそもそもなんだい？ V2 移行に即してない範囲では？ context injection の状態では？」と指摘するまで、PM 自身は逸脱と認識できなかった。

### 逸脱起点の層（recovery-workflow step 3 — 症状の層でなく根の層）

- **症状の層**: PM が毎 session「dist publish は P1」と優先候補に挙げる（= 個別 session の判断ミスに見える）。
- **根の層**: distribution architecture という **Forward 工程外の判断を、V-model 接続先を持たないまま常時注入 context（CLAUDE.md = P-tier always-injected / PM memory）へ「確定」として固定した**こと。個別 session の判断ではなく、注入ソースの汚染が根。
- TL 判定（changes_required, 2026-06-01）: 短期 Forward 接続先 = **L14 運用学習**（再発防止フィードバック）、恒久設計の接続先 = **document-topology（context injection / 常時注入最小化の設計）= L4 基本設計側**。

## §2 認識訂正履歴（軌跡）

| # | ユーザー指摘 | PM の誤り | 訂正 |
|---|---|---|---|
| 1 | 「優先順位は？」 | 引き継ぎ memory の「dist publish P1」を無批判に優先候補へ並べた | explorer 監査で dist publish が V2 移行スコープ外と判明 |
| 2 | 「dist publish はそもそもなんだい？ 過去に謎の起票があって V2 移行に即してない範囲では？」 | スコープ適合を検証せず候補化していた | adversarial 監査で 4 問題（スコープ混入 / 承認証跡なし / 孤児 PLAN-218 / PLAN 自己矛盾）を確認、ユーザー懐疑が妥当と判定 |
| 3 | 「どこかの常時注入に含まれていて勝手に誤解しているのでは？ context injection の状態では？ リファクタリングして V モデルへ整備するのが適切では？」 | 注入ソースの汚染という構造を自分で発見できていなかった | grep で確定: 戦略C は project CLAUDE.md（commit 1980b7a +35 行 / 82910b8 +10 行）+ PM memory に焼き込み。消費側 helix/ core docs には未漏洩（grep 0）。診断「context injection 由来の自己永続ドリフト」が正しいと確認 |
| 4 | 「TL に相談してくれ」 | — | tl-advisor 諮問 → changes_required（doc Refactor でなく Recovery として扱え + 再発防止住所を L4+ADR に設計せよ） |

## §3 収束判断（ロールバックでなく excise + park）

汚染源と処置を以下に確定する。git revert ではなく、正当な部分を残した外科的な excise + park で収束する。

### 汚染源

| 注入ソース | 常時注入 | 汚染内容 | commit |
|---|---|---|---|
| project CLAUDE.md `### 配布戦略 (戦略C)` | ✅ この repo で毎 session | 投機的・V2外・未承認の配布戦略を「2026-06-01 確定」と記述 | 1980b7a |
| project CLAUDE.md `### ブランチ` の dogfood 節 | ✅ | dogfood ブランチを戦略C 依存として説明 | 1980b7a |
| project CLAUDE.md 保存先ルール「最上位原則」格上げ | ✅ | G/P 住所分離（document-topology の配置判断ルール）を HELIX「最上位原則」へ過剰格上げ | 82910b8 |
| PM auto-memory（MEMORY.md index + project_2026_06_01 topic） | ✅ 毎 session | 「戦略C 確定 / 次=dist publish P1」 | （repo 外 S-tier） |

### 巻き込まない正当規律（残す）

TL 確認（Q5）。以下は戦略C と無関係の正当な運用規律であり、除去しない。

- `@~/.helix/core/<path>` 公開 API 破壊禁止 / `helix/core-manifest.tsv` SSoT
- push/PR はユーザー明示時のみ / 委譲 Codex は commit/push しない
- S-tier / secret / PII 非追跡

### 処置（本 Recovery の作業項目）

1. CLAUDE.md `### 配布戦略 (戦略C)` 節を除去、ブランチ節 dogfood を「一時退避/要再判断」に弱める。
2. CLAUDE.md 保存先ルール: G/P 原則は残し「最上位原則」格上げ表現を「保存先判断の原則」へ戻す。
3. PM auto-memory を訂正（戦略C確定/dist P1 → 未承認・V2外・park）。
4. Refactor PLAN を Phase 1-3（フォルダ整理）に縮小、Phase 0(dist) を凍結ブロックへ切り出し（承認+ADR 待ち）。
5. PLAN-218 を park 注記（distribution architecture 確定まで着手禁止）。

ロールバック commit: なし（excise + park で収束。git revert は正当規律を巻き込むため不採用）。

## §4 再開ポイント（Forward 復帰）

- 本 Recovery の処置 1-5 完了後、**柱1 gate-policy（Forward L 単位の機械制約定義）= V2 移行の本筋**へ復帰する。
- 配布戦略は本 Recovery では復活させない。将来必要になった場合のみ §5 の正規住所（L4 基本設計 PLAN + ADR）を通す。

## §5 再発防止（ヒアリングシート + L14 フィードバック）

### 恒久設計（TL Q3 — 配布戦略の正規住所）

将来 dist publish / 配布戦略が本当に必要になった場合、住所は CLAUDE.md ではない。正規ルートは:

- **L4 基本設計 PLAN**（例: `docs/v2/L4-.../distribution-architecture.md` または `docs/design/` 配下）に設計本文を置く。
- **ADR**（例: `docs/adr/ADR-0xx-helix-distribution-architecture.md`）に不可逆判断を記録。
- **migration / retrofit PLAN** で実装を Forward 接続。
- **常時注入 context（CLAUDE.md）には「詳細は ADR/PLAN を参照」程度のポインタのみ**置き、戦略本文を再注入しない。

### L14 運用学習フィードバック（チェックボックス）

- [ ] 未承認・Forward 工程外の判断を常時注入 context（CLAUDE.md / memory）に「確定」として書かない。判断は ADR/PLAN（注入されない P-tier）に置き、context にはポインタのみ。
- [ ] memory carry の優先順位主張（「次=Xが P1」）は、使う前に正本（integration-map §結論）とスコープ適合を verify する（[[feedback_read_integrated_plan_before_carry_list]]）。
- [ ] PLAN に `related_adr` があるのに `docs/adr/ADR-NNN-*.md` が実体不在の場合を検出する detector を整備する（follow-up PLAN、§6 参照）。
- [ ] 「最上位原則」等の格上げ表現は HELIX Core 絶対原則（V-model / Forward 収束）に限定し、配置判断ルールを格上げしない。

### 再発防止の紐付け memory

- [[feedback_plan_doc_adr_layer_vmodel_order]]（ADR 乱発禁止 / いきなり下流から書かない）
- [[feedback_stay_in_requested_phase_scope]]（依頼スコープ厳守 / 芋づる式禁止）
- [[feedback_read_integrated_plan_before_carry_list]]（自前 carry list 禁止 / 正本を読む）

## §6 進捗

- [x] §3 処置 1: CLAUDE.md 配布戦略節除去 + dogfood 弱化
- [x] §3 処置 2: CLAUDE.md 最上位原則表現を戻す（→「保存先判断の原則」）
- [x] §3 処置 3: PM auto-memory 訂正（MEMORY.md index + topic file item4/item6/運用注意）
- [x] §3 処置 4: Refactor PLAN 縮小 + Phase 0 凍結
- [x] §3 処置 5: PLAN-218 park
- [x] TL 検証（cleanup 一式: 第1回 changes_required → 反映 → 第2回 changes_required[memory 旧断定残存] → 再反映で approve 水準）
- [ ] follow-up: 孤児PLAN/missing-ADR detector PLAN 起票（柱周辺、別 PLAN）
- [ ] Forward 復帰: 柱1 gate-policy 着手
