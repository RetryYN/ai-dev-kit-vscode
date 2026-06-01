---
plan_id: L1-helix-workflows-業務要求plan
title: "L1-helix-workflows-業務要求plan: HELIX-workflows V2 業務要求"
kind: requirements
layer: L1
drive: be
status: finalized
created: 2026-05-26
owner: PM
process_layer: L1
parent_process: HELIX-workflows/helix-process/L1-requirements.md
pairs_test_design:
  - docs/v2/L14-test-design/helix-workflows-operational-test-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G1 evidence)"
generates:
  - artifact_path: docs/v2/L1-requirements/helix-workflows-business-requirements.md
    artifact_type: design_doc
dependencies:
  parent: L0-helix-workflows-conceptplan
  requires:
    - L0-helix-workflows-conceptplan
  blocks:
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
    - L3-helix-workflows-業務要件plan
related_docs:
  - HELIX-workflows/helix-process/L1-requirements.md
  - docs/v2/process/L01-requirements-and-operational-test-design.md
  - docs/v2/L0-helix-workflows/concept.md
  - HELIX-workflows/helix-process/L14-operation-verification.md
  - docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
---

## §0 PLAN concept

> **工程**: L1 (L1↔L14 pair freeze)
> **正本**: HELIX-workflows/helix-process/L1-requirements.md
> **本 PLAN の対象**: HELIX-workflows V2 完全移行後の dogfooding として、HELIX-workflows 自体の **業務要求** (Business Requirements、誰が / 何のために / どんな業務で使うか) を定義する。L0 [見直し企画書](../L0/L0-helix-workflows-conceptplan.md) §8 L1 バトン 17 件のうち業務要求関連 (BR-*) を抽出し、L14 運用検証で実行可能な運用テスト設計とペア凍結する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L0 §8 L1 バトン 17 件 + IPA 業務要求書 雛形 + HELIX-workflows 既存運用 hearing) | ☑ completed (2026-05-26、L0 + L1 template + L1-requirements 正本 + L01 工程 doc 精読済) |
| 2 | ヒアリング (PM = ユーザー本人 / TL = Codex gpt-5.5 / SE = Codex 5.4 / QA = Codex / 想定 user = HELIX 採用 project owners) | ☑ completed (2026-05-26、L0 conditional_approve 時点でユーザー確認済、ステークホルダーは §4 で確定) |
| 3 | ドラフト起草 (`docs/v2/L1-requirements/helix-workflows-business-requirements.md` BR-01〜BR-08 + 業務フロー + ステークホルダー) + L14 pair artifact skeleton (`docs/v2/L14-test-design/helix-workflows-operational-test-design.md` OT-01〜OT-03) | ☑ completed (2026-05-26、BR-01〜BR-08 + 業務フロー + §4 ステークホルダー + §5 NSM/Guardrail/Cascade mapping + L14 OT-01〜OT-03 完成) |
| 4 | TL レビュー (helix codex --role tl-advisor、adversarial check 1 回必須、G1 evidence) | □ pending (Phase B 並走 3 PLAN 完了後にまとめて adversarial check 投入予定) |
| 5 | pmo-sonnet 再 audit (反映漏れ / 二次 drift / AC 充足、[[feedback_two_round_audit_for_design_docs]]) | □ pending (Phase C で全 4 PLAN + L14 pair の整合 audit) |
| 6 | 修正反映 + 確定 → G1 ゲート判定 → L3 要件定義へ引き渡し | □ pending |

## §2 実装計画 (記載項目をどう埋めるか)

### この PLAN が起票する成果物

- **PLAN file (本 PLAN)**: `docs/plans/L1/L1-helix-workflows-業務要求plan.md` (工程表 + 実装計画)
- **製本 doc**: `docs/v2/L1-requirements/helix-workflows-business-requirements.md` (BR-* 一覧 + 業務フロー + ステークホルダー + 現状課題 → あるべき姿)
- **L14 pair artifact**: `docs/v2/L14-test-design/helix-workflows-operational-test-design.md` (各 BR-* に対する運用テスト設計、L14 運用検証で実行)

### §2.1 必須記載項目 (HELIX-workflows L1-requirements.md 正本準拠)

| 項目 | 対象 doc | 内容 |
|---|---|---|
| 目的・背景 (WHY / WHAT / WHO) | business-requirements.md §1 | HELIX-workflows V2 を **誰が** (PM/TL/SE/QA + 採用 project) **何のために** (AI 暴走削減 / 配線機械判定 / 量閉じ性保証 / 影響範囲分析) **どんな業務で** 使うか |
| 対象業務一覧 | business-requirements.md §2 | (a) HELIX 自身の dogfooding 開発業務 / (b) HELIX 採用 project の開発業務 / (c) 9 mode 入口判定 / (d) ペア凍結監査 / (e) Forward 復帰 / (f) gate 機械判定 |
| 業務フロー | business-requirements.md §3 | L0 企画 → L1 要求定義 → L3 要件定義 → L4 基本設計 → L5 詳細設計 → L6 機能設計 → L7 実装スプリント → L8 結合 → L9 総合 → L11 RC → L12 デプロイ → L13 安定性 → L14 運用検証 の **15 工程主線** + 9 mode 分岐 + cross-cutting 横断機構 |
| ステークホルダー | business-requirements.md §4 | PM (Opus、大局判断) / TL (Codex gpt-5.5、設計レビュー) / SE (Codex 5.4、高度実装) / PE (Codex 5.3-spark、単機能実装) / QA (Codex、テスト) / PMO (Sonnet/Haiku、状況把握) / 採用 project owners |
| 現状課題 → あるべき姿 | business-requirements.md §5 | L0 §2 課題 10 軸を BR 単位に再整理 + あるべき姿 (L0 §6.5 Diagram 7 図) を業務観点で記述 |

### §2.2 L0 §8 L1 バトン振り分け (業務要求 scope)

| L0 §8 項目 | 本 PLAN での扱い | 対象 BR |
|---|---|---|
| L1-IN-03 (L0-L14 全工程 PLAN dir 整備) | dogfooding 工程表として BR-01 化 | BR-01 dogfooding |
| L1-IN-04 (4 artifact 双方向 trace retrofit) | 既存 PLAN 再整備の業務として BR-02 化 | BR-02 retrofit 業務 |
| L1-IN-05 (HELIX-workflows ↔ CLI/skill/helix.db drift 解消) | 体系整合維持業務として BR-03 化 | BR-03 drift 解消 |
| (他は 技術要求 / 非機能要求 / 機能要求 plan に振り分け) | — | — |

### §2.3 L14 pair artifact 内容 (運用テスト設計)

| L1 業務要求 | L14 運用テスト |
|---|---|
| BR-01 dogfooding | 毎週 V-model 整合 PLAN 完遂数 (NSM) 測定、< 50 / month で alert (Guardrail GR-1 fail-close) |
| BR-02 4 artifact retrofit | warn 数の月次推移、86 → 20 以下を Phase α 終了条件 |
| BR-03 drift 解消 | drift detector 出力件数の週次推移、新規発生 0 を運用維持 |
| BR-04〜08 | OT-04 mode_transition 登録率 / OT-05 ペア凍結 coverage 5 pair / OT-06 影響範囲 query 時間 / OT-07 注入セット利用率 / OT-08 採用 project 稼働率 (2026-05-26 tl-advisor G1 P0 #1 反映で追加) |

### §2.4 L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 PLAN 共通)

- **L3 PLAN 起票時の dependencies.requires**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務要求 / 機能要求 / 技術要求 / 非機能要求) を `dependencies.requires` に列挙する
- **L3↔L12 pair freeze**: L3 起票時に `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票し、L3 FR-* / NFR-* / 業務要件 の AC-* と L12 受入テスト設計を pair freeze する (L1↔L14 で運用テストペア凍結したのと同じ構造)

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L1/L1-helix-workflows-業務要求plan.md`](L1-helix-workflows-業務要求plan.md)
- **製本 doc**: [`docs/v2/L1-requirements/helix-workflows-business-requirements.md`](../../v2/L1-requirements/helix-workflows-business-requirements.md) (Step 3 で起草)
- **L14 pair artifact**: [`docs/v2/L14-test-design/helix-workflows-operational-test-design.md`](../../v2/L14-test-design/helix-workflows-operational-test-design.md) (Step 3 で同時起票、本 PLAN 完遂で L14 ペア凍結確立)
- **ペア凍結**: L1↔L14 (V-model ペア凍結)

## §4 受入条件 / DoD

- [ ] §1 工程表 Step 1-6 すべて完了
- [ ] §2.1 必須記載項目 5 件すべて業務要求 doc に反映
- [ ] §2.3 L14 pair artifact 各 BR-* に対する運用テスト記述あり
- [ ] tl-advisor adversarial check pass (passed / passed_with_minor_changes / conditional_approve のいずれか)
- [ ] pmo-sonnet 再 audit pass (反映漏れ 0 / 二次 drift 0)
- [ ] G1 要求定義ゲート acceptance criteria 満足 (PM + PO 判定、業務要求 + 運用テスト設計 ペア凍結)
- [ ] L3 接続準備完了 (L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) 起票準備)

## §5 関連 PLAN / ADR / docs

- **上流 PLAN**: [L0-helix-workflows-conceptplan](../L0/L0-helix-workflows-conceptplan.md) (見直し企画書、G0.5 conditional_approve 取得済)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../../v2/process/L01-requirements-and-operational-test-design.md)
- **L14 ペア凍結相手**: [HELIX-workflows/helix-process/L14-operation-verification.md](../../../HELIX-workflows/helix-process/L14-operation-verification.md)
- **template**: [cli/templates/plan/v2/L01-requirements-template.md](../../../cli/templates/plan/v2/L01-requirements-template.md)
- **並走 PLAN** (Phase B 起票予定):
  - L1-helix-workflows-機能要求plan (機能一覧 / シナリオ / 入出力)
  - L1-helix-workflows-技術要求plan (helix.db schema / 9 mode 基盤 / drift 解消)
  - L1-helix-workflows-非機能要求plan (IPA × ISO 25010、auto-deprecation 含む)
  - 画面要求は L2 skip により対象外
- **下流 PLAN**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) (本 PLAN + 並走 3 PLAN 完遂後に起票)
- **skill**: workflow/requirements-handover / workflow/requirements-deriver / workflow/doc-system-architect
