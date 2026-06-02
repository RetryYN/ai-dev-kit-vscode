---
plan_id: reverse-2026-06-03-l1-l3-trace-hardening
title: "Action: V2 Phase1 — L1/L3 trace 契約 normalization + L3↔L12 acceptance gap closure + registry Reverse routing"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
workflow: reverse
kind: reverse
layer: L3
drive: reverse
status: in_progress
created: 2026-06-03
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 片肺判定 / 検証層契約 / 再凍結ゲート adversarial check"
  - role: se
    slot_label: "SE — AT/OT 追補・frontmatter 契約修正の bulk 編集（Codex、必要時）"
generates:
  - artifact_path: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/L1-requirements/helix-workflows-functional-requirements.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
  - docs/v2/L14-test-design/helix-workflows-operational-test-design.md
---

# Phase1 Action: L1/L3 trace 契約 normalization + acceptance gap closure

V2 実装計画 Process（親）の Phase 1 子 Action。`workflow: reverse`（normalization/design）で、frozen 化した L1/L3 要件の **trace 契約の不整合・片肺**を既存実態から復元・正規化し、Forward 再凍結へ戻す。tl-advisor 2026-06-03 判定（条件付き推奨 / P0 なし）に基づく。

## 1. baseline（grep 裏取り + pmo-sonnet + 再 verify、2026-06-03 訂正版）

> **重要訂正**: 初版 baseline の「L3↔L12 で FR-02〜14 uncovered」「L1↔L14 片肺」は **いずれも false positive**（自己反省 §4 #2/#3）。再 verify で両ペアとも健全と確定。TL の初回 Phase1 判定（L3↔L12 P1 真片肺）は私が渡した誤った前提に基づくため void。

### L1↔L14（運用テスト設計）= ✅ 健全
- L14（OT-01〜20）は BR-01〜12 + NFR-OP-01〜05 + NFR-AV-01〜03 の **20 件を balance_ratio 1.00 でカバー**。§1 で運用 scope に明示限定。
- L1 functional-requirements.md §「L14/L3 ペア凍結の扱い」(line 108-112) が明記: **FR の詳細化・受入検証は設計上 L3↔L12 へ routing**。`pairs_test_design: L14` は V-model 構造宣言で coverage 誤主張ではない。→ 片肺でない。

### L3↔L12（受入テスト設計）= ✅ 健全
- L3 の FR は **名前ベース ID**（FR-NSM-01 / FR-GR-01 … FR-GLOSSARY-01 の 18 件）。私が L1 数字式 `FR-02〜14` で grep したため 0 ヒット → false positive 化していた。
- L12 §3 trace matrix が 18 名前ベース FR を **全て AT-13〜30 に割当、balance_ratio = 57/57 = 1.00**（grep 各 ID 3 ヒットで裏取り）。→ 片肺でない。
- 残る微小事項（P2/P3、Phase1 必須でない）: FR-MIGR-01 AT-26 の検証層 nuance（実 migration 安全性は L9/L13）、L1 FR-13 横断実現の AT trace label 散在。

### L4↔L9（参考、Phase 2 対象）= 🔴 実在片肺
- 前ターン grep 確証: NFR 23ID→L9 観点2個、IF-05 個別 trace 欠落。**これが唯一の確証済片肺で、Phase 2 の対象**。

### L0 / インベントリ scope
- L0 concept は「既存全洗い出し→要求」scope を捕捉済（L1-IN-06/18「既存整理は要求の中に含まれる」、AC-01）。functional-registry.md（854行 draft）が inventory 実体。
- ただし L0 の inventory 数値が **stale**: `cli/helix-* 約60 / 81` と記載だが実数 94（helix-* prefix）/ 118（拡張子なし全体）。→ 軽微 drift。

## 2. 作業（訂正版 — 両ペア健全のため「片肺 closure」は不要、軸足はワークフロー改善）
- **B'（旧 B は撤回）**: L3↔L12 は covered 1.00 のため closure 不要。残微小事項（FR-MIGR-01 AT-26 検証層注記 / FR-13 横断 AT trace label）は P2/P3 carry。
- **A'（契約明確化、任意・要再凍結）**: L1 functional/technical/nfr の `pairs_test_design: L14` は構造宣言として正しい。誤検出再発防止のため `verification_layers` frontmatter を追加し「pair_layer=L14 ≠ 検証層」を機械識別可能にする。frozen doc 改変→G1 再凍結を伴うため、Phase1 必須か Phase2 carry かは TL final で判断。
- **C（最重要 = ワークフロー改善）**: detector の ID-universe 分離 refine（[[poc-2026-06-03-trace-symmetry-detector]]）。自層定義 ID と上流参照を分離し、over-report を解消。refine 後に走らせ、L3↔L12=covered / L4↔L9=片肺 を機械再現できれば信頼できる baseline 成立。
- **D（軽微）**: L0 concept の inventory 数値 stale 修正（cli/helix-* 60/81 → 実数 94）。
- **E（scope 確認）**: functional-registry.md（draft 854行）が「既存全洗い出し→機能要件」の inventory 実体であることを確認。TL 方針どおり即 frozen 化せず draft 維持、Reverse design evidence として扱う。

## 3. acceptance（Phase1 closure 条件、訂正版）
- L1↔L14 / L3↔L12 が健全であることを **refine 済 detector で機械再現**（L3↔L12 uncovered≈0、L4↔L9 片肺検出）。
- L0 が「既存全洗い出し→要求」scope を捕捉していることを確認（捕捉済、数値 stale のみ）。
- detector が信頼できる baseline を出す（over-report 解消）= ワークフロー改善成立。
- 実在片肺 L4↔L9 は Phase2 carry として明示。
- 必要に応じ L1 verification_layers 契約 + 再凍結（TL final 判断）。

## 4. 駆動発火 / 未発火 / 脱線 / トラブル ログ（自己反省、継続追記）
| # | 事象 | 種別 | 反省 / 発火要件への学び |
|---|---|---|---|
| 1 | pmo-tech-docs（外部調査）発火 → OFT/sphinx-traceability/ISO 26262 から detector 設計知見を取得 | 駆動発火=成功 | 外部調査は WebFetch 一次情報精読まで指示すると質が出る。発火要件: detector/方法論設計の前段で外部調査を起動 |
| 2 | pmo-project-explorer が 40 tool_uses 後に最終報告を返さず truncate（memory 既知症例） | トラブル | **決定的 read（件数/grep）は explorer に投げず PM 直接 grep が確実**。発火要件: 判断を伴わない件数取得は explorer 非発火、PM 直接実行 |
| 3 | tl-advisor 2 回発火（roadmap check / Phase1 片肺判定）→ 条件付き推奨 + P1 群 | 駆動発火=成功 | 設計↔テスト trace 判定は V-model semantics の機微（運用 vs 受入）があり TL 必須。発火要件: pair 片肺判定・driving model 確定の前に tl-advisor 必須 |
| 4 | フォワード脱線: なし。TL が「親=Forward 精緻化、Retrofit を親にしない、Reverse は子」と driving model を確定 | 正常 | 駆動モデル選定は self-judge せず TL 確認。Retrofit 早合点を回避できた |
| 5 | **L3↔L12「FR-02〜14 uncovered」= false positive**。L3 FR は名前ベース(FR-NSM-01 等)、私が L1 数字式で grep し 0 ヒット化。pmo-sonnet が指摘、再 grep で 18 FR 全カバー(1.00) と確定 | **重大トラブル/誤検出** | trace 判定前に**各層の実 ID universe を確定**せよ。層間で ID 連続(数字)を仮定するな |
| 6 | **L1↔L14 片肺 = false positive**。L1 functional の §L14/L3 pair handling を読まず「FR uncovered」と誤断。実際は FR 検証を L3↔L12 へ routing と doc 明記 | **重大トラブル/誤検出** | 片肺宣言前に**対象 doc 自身の pair-routing 節を読む**。frontmatter の pair 宣言=構造、coverage は別 |
| 7 | detector PoC も同 ID-universe バグで L3↔L12 を over-report(uncovered 33)。**PoC として核心問題を機械実証** | 駆動発火=部分成功 | detector は「自層の設計 ID」と「mapping/trace 列の上流参照」を分離抽出する必要。要 refine |
| 8 | 誤検出 3 連発を TL に渡し、TL が誤前提で判定 | **プロセス反省** | **検出結果は TL 諮問前に PM が自己 verify**。誤前提を advisor に渡すと判定全体が汚染される([[feedback_memory_verify_before_act]] [[feedback_vmodel_pair_judge_by_trace_not_file]] 再発) |

### 発火要件への蓄積（ワークフロー改善 input）
- **trace 対称判定の発火前提**: ①対象 pair 両層の実 ID universe を grep 確定 ②各層の ID 命名規約(数字 vs 名前ベース)を識別 ③対象 doc の pair-routing 節を読む ④detector で自層定義 ID と上流参照 ID を分離。これらを満たさない trace 判定は発火させない(誤検出の温床)。
- **detector が満たすべき発火要件**: design-ID universe = その doc の定義行のみ(mapping/IO 表の上流参照を除外)、`verification_layers` frontmatter で「pair_layer ≠ 検証層」を機械識別。

## 5. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-03 | Action 起票。baseline + TL 判定反映。detector PoC baseline 後に B→A→C の順で着手予定。 | PM (Opus) |
| 2026-06-03 | **訂正**: baseline 初版「両ペア片肺」は false positive 3 連発（§4 #5-8）。再 verify で **L1↔L14 / L3↔L12 とも健全**と確定。detector refine 完了（L3↔L12 uncovered=0 / L4↔L9 片肺検出を機械再現、pytest 3 passed、PM 自己 verify 済）。軸足を「片肺 closure」から「detector を信頼水準へ磨く=ワークフロー改善」へ移し達成。検証方法論を [[verification-strategy]] に正本化。残: L1 verification_layers 契約+G1 再凍結（任意）/ L0 inventory 数値 stale / detector L5-L6 抽出 は carry。 | PM (Opus) |
