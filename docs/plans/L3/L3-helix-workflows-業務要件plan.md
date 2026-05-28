---
plan_id: L3-helix-workflows-業務要件plan
title: "L3-helix-workflows-業務要件plan: HELIX-workflows V2 業務要件 (確定版)"
kind: requirements
layer: L3
drive: be
status: draft
created: 2026-05-26
owner: PM
process_layer: L3
parent_process: HELIX-workflows/helix-process/L3-requirements-definition.md
pairs_test_design:
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G3 evidence)"
generates:
  - artifact_path: docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
    artifact_type: design_doc
dependencies:
  parent: L1-helix-workflows-業務要求plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
  blocks:
    - L3-helix-workflows-機能要件plan
    - L3-helix-workflows-非機能要件plan
    - L4-helix-workflows-基本設計plan
related_docs:
  - HELIX-workflows/helix-process/L3-requirements-definition.md
  - docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L0-helix-workflows/concept.md
  - HELIX-workflows/helix-process/L12-deployment.md
---

## §0 PLAN concept

> **工程**: L3 (L3↔L12 pair freeze)
> **正本**: HELIX-workflows/helix-process/L3-requirements-definition.md
> **本 PLAN の対象**: L1 [業務要求 doc](../../v2/L1-requirements/helix-workflows-business-requirements.md) **BR-01〜BR-12** (BR-01〜08 = 2026-05-26 Phase E.A 確定、**BR-09〜12 = 2026-05-29 L3 取り込み、L1-IN-18〜21 由来**) を **業務フロー (確定版) + 業務ルール + 対象業務範囲** で詳細化し、L12 受入テスト設計とペア凍結する。HELIX-workflows V2 dogfooding における L3 の「業務要件」を確定する。L1 では要望レベル、L3 で実装可能な確定版に昇格。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L1 業務要求 BR-01〜BR-12 詳細精読 + L0 概念 + L1 4 PLAN G1 結果 + L3 template) | ☑ completed (2026-05-26 BR-01〜08 / 2026-05-29 BR-09〜12 追加調査 = tl-advisor P0 反映、L1 commit aa86a22 受け継ぎ) |
| 2 | 業務フロー (確定版) 起票 (各 BR-* に対する業務フロー mermaid + step-by-step) | ☑ completed (2026-05-26、business-requirements-detail.md §1 起票、BR-01/02/03 詳細 mermaid + BR-04〜08 要約) |
| 3 | 業務ルール定義 (条件分岐 / 制約 / 例外処理) + 対象業務範囲 (in/out scope) 確定 | ☑ completed (2026-05-26、§2 BR-RULE-01〜08 + §3 in/out scope) |
| 4 | L12 受入テスト設計 pair artifact 起草 (各 BR-* → AC-BR-* mapping、`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md`) | ☑ completed (2026-05-26、§1 AC-BR-01〜08 detail 化、2026-05-29 BR-09〜12 追加で AC-BR-01〜12 detail 化、balance_ratio = 12/12 = 1.0) |
| 5 | TL レビュー (helix codex --role tl-advisor、adversarial check 1 回必須、G3 evidence) | ☑ completed (2026-05-29、tl-advisor adversarial check verdict = changes_required、P0 BR-09〜12 L3 取り込み / P1 BR-04〜08 詳細 mermaid carry / P2 AC-BR-08 carry / P3 AC-* → AC-BR-* 統一 すべて反映、9 edit) |
| 6 | pmo-sonnet 再 audit + 修正反映 → G3 ゲート判定 → L4 基本設計へ引き渡し | ☑ completed (2026-05-29、pmo-sonnet verdict = yes_with_minor_changes、D1 L12 §0 header 57 AC → 59 AC drift 反映済、D2 (AC-FR 並び順) は P2 既知として carry、D3 は確認 OK = FR-CTX-01 PdM 拡張は機能 doc §2 仕様で明示済) |

## §2 実装計画 (記載項目をどう埋めるか)

### この PLAN が起票する成果物

- **PLAN file (本 PLAN)**: `docs/plans/L3/L3-helix-workflows-業務要件plan.md` (工程表 + 実装計画)
- **製本 doc**: `docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md` (業務フロー確定版 + 業務ルール + 対象業務範囲)
- **L12 pair artifact**: `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` (各 BR-*/FR-*/NFR-* に対する受入テスト設計、L3 3 PLAN 共通 pair artifact、L12 受入テストで実行)

### §2.1 必須記載項目 (HELIX-workflows L3-requirements-definition.md 正本準拠)

| 項目 | 対象 doc | 内容 |
|---|---|---|
| 業務フロー (確定版) | business-requirements-detail.md §1 | 各 BR-* (BR-01 dogfooding 〜 BR-08 採用展開) に対する **mermaid flowchart + step-by-step 業務フロー**、L1 で示した粗フローを実装可能な粒度に詳細化 |
| 業務ルール | business-requirements-detail.md §2 | 条件分岐 / 制約 / 例外処理 (例: BR-01 dogfooding で「新規 PLAN 起票 → V-model 整合 check 不合格 → 自動差戻し」の rule) |
| 対象業務範囲 | business-requirements-detail.md §3 | in scope (HELIX 自身 + 採用 project) / out scope (人間判断 / セキュリティ事故対応等) を明示、L1 で示した境界を確定 |

### §2.2 L1 → L3 業務要件 詳細化 mapping

| L1 BR-* | L3 詳細化方針 | L12 受入テスト pair (AC-*) |
|---|---|---|
| BR-01 dogfooding 稼働 | 新規 PLAN 起票 → V-model 整合 check → fail-close 自動差戻し業務フロー | AC-BR-01: NSM 計測 SQL + Guardrail GR-1 fail-close 動作確認 |
| BR-02 4 artifact retrofit | 既存 PLAN scan → 4 artifact 不在検出 → retrofit 自動 stub 生成業務フロー | AC-BR-02: helix doctor warn 数推移 + retrofit 完遂率 |
| BR-03 drift 解消 | 週次 detector → 新規 drift → Reverse normalization mode 自動切替業務フロー | AC-BR-03: detector 検出 + normalization 完了時間 |
| BR-04 9 mode → Forward 回帰 | mode closure event → helix.db.mode_transition 登録 → 適切 L 工程接続業務フロー | AC-BR-04: mode_transition event 登録率 + Forward 接続成功率 |
| BR-05 ペア凍結監査 | parent_design / pairs_test_design 不在検出 → frontmatter 自動 lint 業務フロー | AC-BR-05: ペア凍結 coverage 5 pair `balance_ratio` 計測 |
| BR-06 影響範囲分析 | 機能改修 trigger → 4 artifact 双方向 trace query → 影響範囲 視覚化業務フロー | AC-BR-06: query 応答時間 + trace 網羅率 |
| BR-07 AI agent 配線 | L 工程 entry → vmodel-semantics.yaml 読込 → mandatory_skills/commands 自動注入業務フロー | AC-BR-07: 注入セット利用率 + AI 判断削減率 |
| BR-08 採用 project 展開 | HELIX-workflows portable package → 採用 project 取込 → 各 project の dogfooding 起動業務フロー | AC-BR-08: 採用 project 数 + 各 project の OT-01 相当稼働率 (実行可能性 carry: Phase β 以降に確定) |
| BR-09 既存資産整理・マッピング (2026-05-29 取り込み、L1-IN-18 由来) | 設計 doc 内で「対応 CLI / file path / schema field / table / view / config」主張時 implementation_status 列充足を fail-close 強制 (BR-RULE-09 / §2.4) | AC-BR-09: inventory drift 監査 + implementation_status 列充足率 |
| BR-10 既存資産の段階移行・retrofit (2026-05-29 取り込み、L1-IN-19 由来) | Strangler Fig Pattern 段階置換、Phase 別残量 dashboard 管理 (BR-RULE-10 / §2.4) | AC-BR-10: V1→V2 移行率 + Phase 別残量 + kill criteria 突合 |
| BR-11 doc 品質レビュー継続化 (2026-05-29 取り込み、L1-IN-20 由来) | 大規模 doc 改定 (~500 行+) で helix codex --role doc-reviewer 召喚必須 (BR-RULE-11) | AC-BR-11: 召喚 coverage + 判定 evidence 残置率 |
| BR-12 デグレ禁止ガードレール (2026-05-29 取り込み、L1-IN-21 由来) | 上流 ID 追加 commit で下流対応・balance_ratio・trace 切れ を fail-close (BR-RULE-12 + FR-CHANGEPROP-01) | AC-BR-12: 違反 commit hook block 率 + ratchet baseline 更新動作 |

### §2.3 L3 接続規約 (2026-05-26 L1 G1 反映、L3 3 PLAN 共通)

- **L3 3 PLAN 起票時の dependencies.requires**: 業務要件 / 機能要件 / 非機能要件すべての L3 PLAN は L0 + L1 4 PLAN を `dependencies.requires` に列挙する (本 PLAN frontmatter 反映済)
- **L3↔L12 pair freeze**: L3 3 PLAN 共通の pair artifact `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を本 PLAN で起票し、L3 機能要件 / 非機能要件 PLAN は同 file を pair として共有 (artifact path は同一、AC-* の業務系/機能系/NFR 系で section 分割)
- **L4 接続**: L3 確定後、`L4-helix-workflows-基本設計plan` 起票時に L3 3 PLAN 全件を `dependencies.requires` に列挙、L4↔L9 総合テスト設計 pair artifact を同時起票

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L3/L3-helix-workflows-業務要件plan.md`](L3-helix-workflows-業務要件plan.md)
- **製本 doc**: [`docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md`](../../v2/L3-requirements/helix-workflows-business-requirements-detail.md) (Step 2-3 で起草)
- **L12 pair artifact**: [`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md`](../../v2/L12-test-design/helix-workflows-acceptance-test-design.md) (Step 4 で同時起票、L3 3 PLAN 共通 pair)
- **ペア凍結**: L3↔L12 (V-model ペア凍結)

## §4 受入条件 / DoD

- [ ] §1 工程表 Step 1-6 すべて完了
- [ ] §2.1 必須記載項目 3 件 (業務フロー / 業務ルール / 対象業務範囲) すべて業務要件 doc に反映
- [ ] §2.2 L1 → L3 詳細化 mapping **12 件 (BR-01〜BR-12)** すべて確定 (2026-05-29 BR-09〜12 追加で母数 8→12 件、tl-advisor P0 反映)
- [ ] L12 pair artifact に AC-* (業務系) 定義済 + BR-* との 1:1 対応確立 (balance_ratio = 1.0)
- [x] tl-advisor adversarial check pass (2026-05-29、changes_required → P0/P1/P2/P3 全反映 9 edit)
- [x] pmo-sonnet 再 audit pass (2026-05-29、yes_with_minor_changes → D1 即修正 + D2 P2 carry + D3 確認 OK)
- [x] G3 要件凍結ゲート acceptance criteria 満足 (2026-05-29、業務要件 + 受入テスト設計 L3↔L12 ペア凍結成立、PM 判定: pass with minor carry / PO 判定は次工程で)
- [ ] L4 接続準備完了 (`L4-helix-workflows-基本設計plan` 起票準備)

## §5 関連 PLAN / ADR / docs

- **上流 PLAN**: [L1-helix-workflows-業務要求plan](../L1/L1-helix-workflows-業務要求plan.md) (G1 conditional_approve 取得済、commit aa86a22) + L1 機能/技術/非機能要求plan (並走 L1 PLAN)
- **HELIX-workflows L3 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **工程 doc**: [docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md](../../v2/process/L03-requirements-definition-and-acceptance-test-design.md)
- **L12 ペア凍結相手**: [HELIX-workflows/helix-process/L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md)
- **template**: [cli/templates/plan/v2/L03-requirements-definition-template.md](../../../cli/templates/plan/v2/L03-requirements-definition-template.md)
- **並走 L3 PLAN** (Phase E.B 起票予定):
  - L3-helix-workflows-機能要件plan (FR 詳細化 + 機能仕様 + 入出力定義、L1 機能要求 + 技術要求 を統合)
  - L3-helix-workflows-非機能要件plan (NFR IPA グレード値確定)
- **下流 PLAN**: L4-helix-workflows-基本設計plan (本 PLAN + 並走 2 PLAN 完遂後に起票)
- **skill**: workflow/requirements-handover / workflow/requirements-deriver / workflow/doc-system-architect / workflow/design-doc
