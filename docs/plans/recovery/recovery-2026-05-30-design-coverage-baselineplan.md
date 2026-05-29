---
plan_id: recovery-2026-05-30-design-coverage-baseline
title: "recovery-2026-05-30-design-coverage-baseline: L4-L6 設計を業界標準カバー基準の確定前に着工・freeze した工程逸脱の収束 + やり直し (recovery-log)"
kind: recovery
layer: recovery
drive: be
status: completed
created: 2026-05-30
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・収束方針確定"
  - role: pmo-tech-docs
    slot_label: "PMO — 業界標準カバー基準の精読・確定"
  - role: pmo-project-explorer
    slot_label: "PMO — 現状 9 本設計 doc の audit"
parent_process: HELIX-workflows/helix-process/recovery-workflow.md
generates:
  - artifact_path: docs/plans/recovery/recovery-2026-05-30-design-coverage-baselineplan.md
    artifact_type: doc_update
  - artifact_path: skills/workflow/doc-system-architect/references/design-coverage-baseline.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/A-audit/helix-workflows-L4-L6-coverage-audit.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/recovery-workflow.md
  - skills/workflow/doc-system-architect/SKILL.md
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/v2/L4-architecture/helix-workflows-functional-design.md
  - docs/plans/recovery/recovery-2026-05-30-standards-fix-overreachplan.md
related_memory:
  - feedback_stay_in_requested_phase_scope
  - feedback_plan_doc_adr_layer_vmodel_order
  - feedback_memory_verify_before_act
  - reference_nfr_quality_standards_2026
---

# Recovery Log: L4-L6 設計を業界標準カバー基準の確定前に着工・freeze した工程逸脱の収束 + やり直し

> **mode**: Recovery (kind=recovery)
> **正本**: HELIX-workflows/helix-process/recovery-workflow.md
> **本 log の対象**: HELIX-workflows V2 dogfooding で L4(基本設計)/L5(詳細設計)/L6(機能設計) の設計 9 本を、「業界標準としてどの文書・どの viewpoint・どこまで揃えば充足か」という**カバー基準を確定しないまま着工・frozen 化**した工程逸脱。ユーザー指摘「設計ドキュメント自体のカバー率がそもそも業界基準にそくしていない / L4 からのベース前提が問題」で検出 → カバー基準確定 + audit + 実質欠落の追補で収束させる。
> **前例**: recovery-2026-05-30-standards-fix-overreach (同 session、標準バージョン移行の off-process commit) / recovery-2026-05-28-adr047-overreach (工程逸脱)

## §1 発火条件 + 逸脱起点の特定 (recovery-workflow step 3 状態把握)

Recovery workflow の発火条件 4 種のうち 2 種に該当:

- **工程逸脱**: L4-L6 設計を、業界標準カバー基準 (基本/詳細/機能設計に必要なドキュメント・viewpoint の定義) を**着工前に確定せず**進めた。設計 9 本は事後的に §0.1/§0.5 で 42010/arc42/C4/IEEE 1016/29119-4 への self-alignment を宣言しているが、「この基準を満たすために何を書くか」を先に固めた痕跡がない。
- **認識ズレ蓄積**: カバー基準を持たないまま 9 本すべてを frozen 化したため、「設計は完了」という誤った前提が積み上がった。

### 逸脱起点 = L1/L2 の doc-system-architect ゲート (L4 ではない)

実体確認: `doc-system-architect` は `helix_layer: L1`、「L1 受領直後〜L2 entry に**必ず通る前段ゲート**」で、「何を・どこまで・どの粒度で書くか / 業界標準 (42010/arc42/C4/IEEE1016/25010) への整合」を決める正本スキル。

→ 「基本/詳細/機能設計に何を揃えれば業界標準充足か」(= 設計カバー基準) は **doc-system-architect が L1/L2 で出すべき成果物**。それを出さずに L4 着工したのが逸脱の**根**。L4-L6 設計 9 本の薄いカバー (脅威分析なし / 品質特性→設計戦略 mapping 薄 / コンテキスト view 薄) は**下流の症状**であって原因ではない。「L4 からのベース前提が問題」は症状面では正しいが、根は一段上の L1/L2 ゲート。

**重要 (デグレ判定)**: 設計 9 本は個々には厚く (合計 ~7,800 行)、標準参照も持つため「中身が間違っている」わけではない。問題は**個々の出来ではなく、L1/L2 でカバー基準を出さずに L4 着工した前提崩壊**。ロールバックではなく、L1/L2 で基準確定 → L4-L6 を forward-replay audit → 実質欠落の追補で収束する。

> **AI のゴミ判断 (3)**: 当初この発火条件を「L4 着工前」と起点を誤って書いた。recovery-workflow step 3 (どこから逸脱したか特定) を飛ばして PLAN を先に書いたため。ユーザー指摘「リカバリーはどの L から発生するの / どこからの修正が必要なの」で、起点 = L1/L2 doc-system-architect、Recovery 自体は L に属さない横断モードと訂正。

## §2 認識訂正履歴 (軌跡 — AI のゴミ判断を含む)

| # | ユーザー指摘 | 訂正された認識 |
|---|---|---|
| 1 | 「設計ドキュメントのカバー率が業界基準にそくしていない / L4 からのベース前提が問題」 | L4-L6 をカバー基準確定前に着工した工程逸脱。これは Recovery drive 案件 |
| 2 | 「プラン起票のルールが間違っている / リカバリープランで起票してない / PLAN-227 で立ち上げたらクビ」 | 番号付き V1 PLAN (PLAN-NNN) は誤り。Recovery は `docs/plans/recovery/recovery-<date>-<descriptor>plan.md` + kind=recovery で起票する |
| 3 | 「見ているのあってるの？」 | **AI のゴミ判断 (1)**: partial read の explorer 報告 (前半 745 行のみ) を鵜呑みにし「G2/G3/G4 は 9 本中ゼロ」と誤断していた。実物 grep で stakeholder/concern/NFR/25010/security/context が**実在**することを確認 → 「ゼロ」ではなく「薄い/専用節無し」に訂正 ([[feedback_memory_verify_before_act]] = 主張は使う前に verify) |
| 4 | 「お前は何をしているの？」 | **AI のゴミ判断 (2)**: ユーザーが承認したスコープ (G1-G4 全部) を勝手に「過剰」と覆して 3 回目の質問をした。承認済み判断を尊重し、質問をやめて Recovery PLAN 起票を実行する |

## §3 収束判断 (基準確定 + audit + 実質欠落の追補、スコープ = G1〜G4 全部)

ロールバックはせず、標準参照を持つ frozen 9 本を保持した上で、カバー基準を確定し audit して実質欠落を追補する。

### grep 実証ベースの正確な gap 状態

| # | 項目 | 実証された現状 (grep) | 扱い |
|---|---|---|---|
| G1 | **カバー基準そのもの** | 9 本は §0.1/§0.5 で標準 self-alignment を宣言済。だが**再利用可能なカバー基準チェックリストが doc-system-architect に不在** = 根本原因 | **新規確定** |
| G2 | Stakeholder × Concern | system-architecture §0.1 に 42010 要素テーブル実在 (Stakeholder=PM/TL/SE/PO/owners, Concern=品質/セキュリティ/保守性/相互作用) | フル matrix へ**拡充** |
| G3 | NFR(25010) ↔ アーキ設計戦略 | arc42 §10 + Concern で実在だが L3 非機能要件plan への pointer 中心で薄い | L4 で品質特性→設計戦略の明示を**追補** |
| G4 | 脅威分析 / セキュリティ viewpoint | security は concern/role/CI として散在するが**専用 threat model 節が無い** = 実質的欠落 | **追補 (最優先)** |
| G5 | システムコンテキスト / scope view | arc42 §3 は mapping 表にあるが本体に外部境界・アクターの専用節・図が薄い | L4 に context/scope 節を**追補** |

## §4 再開ポイント (recovery-workflow step 4 — L1/L2 doc-system-architect から forward-replay)

> **再開ポイント = L1/L2 (doc-system-architect)**。L4 を直接いじらず、まず L1/L2 でカバー基準を出し、それを持って L4→L5→L6 を forward-replay audit する。全段階を本 recovery 1 本で追跡し、各段階完了時に §6 進捗を更新。委譲は HELIX 標準に従う (標準精読=pmo-tech-docs、audit=pmo-project-explorer、設計追補本体=Codex 委譲 or 設計 doc 起草、PM=Opus は統合・承認のみ)。

1. **【L1/L2 起点】G1 カバー基準確定 (doc-system-architect 成果物)**: `skills/workflow/doc-system-architect/references/design-coverage-baseline.md` を起票。L4/L5/L6 別に「この文書/viewpoint が揃えば業界標準カバー充足」のチェックリスト (典拠標準 + 必須/推奨 + HELIX 既存カバー状況) を確定。これが本来 L1/L2 で出すべきだった成果物であり、今後の設計工程の前段関所になる。
2. **audit**: `docs/v2/A-audit/helix-workflows-L4-L6-coverage-audit.md` を起票。G1 基準で 9 本を採点し、ギャップ表を frozen 化。
3. **G4 追補 (最優先)**: L4 に threat model / セキュリティ viewpoint を追補 (system-architecture の新節 or 専用 doc)。pair test design (L9 総合 / L8 結合の security 観点) との trace も確認。
4. **G3 + G5 追補**: L4 に「品質特性(25010:2023 9 特性) → 設計戦略」mapping と context/scope view を追補。
5. **G2 拡充**: stakeholder × concern を full matrix へ拡充 (42010 §5.2 準拠)。
6. **frozen 整合**: 追補で触れた L4 doc の pair (L9) と status・双方向 trace を再確認。

## §5 再発防止 (ヒアリングシート + L14 フィードバック)

### 確定済の再発防止策
- 本 recovery で「**設計工程は着工前にカバー基準 (どの文書・viewpoint が必須か) を確定する**」を明文化
- G1 の design-coverage-baseline.md 自体が、今後の L4-L6 設計の前段関所として機能する
- AI のゴミ判断 2 件を §2 に記録: ① partial read 鵜呑み ([[feedback_memory_verify_before_act]])、② 承認済みスコープの勝手な覆し

### L14 運用検証へフィードバックする確認事項 (ヒアリングシート)
- [ ] 設計工程 (L4/L5/L6) entry で design-coverage-baseline チェックリストを通す gate を helix doctor / gate-policy に組めるか (`helix doctor check_design_coverage` 候補)
- [ ] 設計 doc を frozen 化する前に「カバー基準を満たすか」を機械 lint できるか (脅威分析節の有無 / NFR↔arch mapping の有無 / context view の有無)
- [ ] subagent の partial read 報告を成果物根拠にする前に、Opus 側で grep verify する運用を徹底できるか
- [ ] ユーザー承認済みスコープを AI が勝手に縮小/拡大しないよう、scope 変更時は再承認を必須化する gate を設けられるか

## §6 進捗

| 段階 | 状態 | 完了 commit / 備考 |
|---|---|---|
| recovery-log 起票 | done | 本 doc (plan_lint PASS、validator は recovery 命名の既知 WARN のみ) |
| G1 カバー基準確定 | done | `skills/workflow/doc-system-architect/references/design-coverage-baseline.md` (74→76行、L4-01〜09/L5-01〜09/L6-01〜05 = 23 成果物 + 充足判定 + ゲート運用)。PM レビューで L4-09 脅威分析行を追補 (G4 と整合) |
| audit (9 本採点) | done | `docs/v2/A-audit/helix-workflows-L4-L6-coverage-audit.md` (全文採点。最低充足セット全層 YES、必須欠落 L4-09 + 部分 7 件特定) |
| G4 脅威分析追補 | done | system-architecture §9 (STRIDE×信頼境界6 + 25010:2023 Security/Safety、grep 実証済) |
| G3+G5 追補 | done | §10 NFR↔arch mapping (25010:2023 9特性) / §11 context (arc42§3) + L5-02 §15 sequenceDiagram / L5-08 §13 SLO / L5-06 §14 横断的関心事 / L6-04 §15 event_type enum |
| G2 拡充 | done | §12 Stakeholder×Concern 6×6 matrix |
| frozen 整合再確認 | done | audit §5 再採点 = 8 項目全 closed。L4/L5/L6 は基準全項目充足 → Forward L6 再開可能。forward carry (L9 security pair / SLO 実測 / check_design_coverage lint) は L6 再開に不要 |
