---
plan_id: L1-helix-workflows-非機能要求plan
title: "L1-helix-workflows-非機能要求plan: HELIX-workflows V2 非機能要求"
kind: requirements
layer: L1
drive: be
status: draft
created: 2026-05-26
owner: PM
process_layer: L1
parent_process: HELIX-workflows/helix-process/L1-requirements.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 非機能要求の優先度・carry 判定"
  - role: pmo-sonnet
    slot_label: "PMO — IPA × ISO 25010 整合チェック"
  - role: tl-advisor
    slot_label: "TL — NFR 妥当性レビュー"
generates:
  - artifact_path: docs/v2/L1-requirements/helix-workflows-nfr.md
    artifact_type: design_doc
dependencies:
  parent: L0-helix-workflows-conceptplan
  requires:
    - L0-helix-workflows-conceptplan
  blocks:
    - L3-helix-workflows-非機能要件plan
    - L4-helix-workflows-基本設計plan
related_docs:
  - docs/v2/L0-helix-workflows/concept.md
  - docs/plans/L1/L1-helix-workflows-業務要求plan.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - HELIX-workflows/helix-process/L1-requirements.md
  - docs/v2/process/L01-requirements-and-operational-test-design.md
  - docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
---

## §0 PLAN concept

> **工程**: L1 (NFR 正本起票、L4 基本設計で pair freeze を具体化)
> **正本**: HELIX-workflows/helix-process/L1-requirements.md
> **本 PLAN の対象**: HELIX-workflows V2 dogfooding の **非機能要求 (NFR)** を、IPA 非機能要求グレード 2018 の 6 大項目と ISO/IEC 25010:2023 の 9 特性で二軸整理し、L0 concept の `L1-IN-12` と `L1-IN-15` を L1 成果物へ落とし込む。L1 では `pairs_test_design: []` を維持しつつ、L4 基本設計起票時に L9/L13/L14 の検証設計へ接続する前提を固定する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査: L0 concept / L1 業務要求 PLAN・製本 doc / HELIX-workflows L1 正本 / L1 工程 doc / requirements-deriver skill を読んで NFR 導出根拠を固める | ☑ completed (2026-05-26) |
| 2 | `workflow/requirements-deriver` の R1-R14 シグナルを当て、L0 §8 の `L1-IN-12` と `L1-IN-15` を NFR scope に振り分ける | ☑ completed (2026-05-26) |
| 3 | 製本 doc `docs/v2/L1-requirements/helix-workflows-nfr.md` を起草し、IPA 6 大項目ごとに NFR-* を定義する | ☑ completed (2026-05-26) |
| 4 | IPA × ISO/IEC 25010:2023 の 9 特性を前提に二軸タグ表を整備し、現れない ISO 特性の carry を整理する | ☑ completed (2026-05-26) |
| 5 | validator / grep / git status / diff で自己検証し、下流計画 (`L3` / `L4`) への block を確認する | ☑ completed (2026-05-26) |
| 6 | TL 観点レビュー結果を反映し、G1 入力として L3 requirements / L4 基本設計へ引き渡す | □ pending |

## §2 実装計画 + L0 §8 L1-IN-12 振り分け

### 本 PLAN が扱う L1 scope

- `L1-IN-12` ★: **排泄系 (excretion)** を NFR-OP-* の核心として扱う
- `L1-IN-15`: 逆引き audit 11 穴は本 doc では段階対応 carry とし、運用・保守性 / 移行性 / セキュリティへ配分する
- BR-02 / BR-03 / BR-06 / BR-07 / BR-08 で定義済みの業務要求を非機能要求へ展開する

### 記載項目の埋め方

| 対象 section | 埋め方 | 根拠 |
|---|---|---|
| §1 可用性 | CLI 起動成功率、DB 整合性、中断時 handover dump を信頼性要求として定義 | L0 §5.3 / BR-01 / BR-03 |
| §2 性能・拡張性 | `helix doctor`、影響範囲 query、並列 Codex 実行、PLAN 起票速度を数値化 | L0 §5.3 / BR-06 / BR-07 |
| §3 運用・保守性 | `L1-IN-12` を中核に auto-deprecation、warn 上限、memory verify-before-act、進化系統 trace を定義 | L0 §8 `L1-IN-12` / `L1-IN-15` |
| §4 移行性 | V1→V2 retrofit、schema migration idempotency、portable package 化を定義 | L0 §6.5.6 / BR-04 / BR-08 |
| §5 セキュリティ | secret 禁止、settings drift、tool guard、commit/push guard、人間確認境界を明文化 | AGENTS / HELIX Core / BR-03 |
| §6 システム環境 | Linux/macOS、Claude/Codex、Python/Bash/SQLite/git の実行基盤を固定 | BR-08 / 既存 runtime |
| §7 二軸タグ表 | NFR-* 全件を IPA + ISO/IEC 25010:2023 で再掲し、`相互作用能力 (Interaction Capability、旧 Usability)` / `柔軟性 (Flexibility、旧 Portability)` / 安全性を含む 9 特性の carry を明示 | requirements-deriver |
| §8 関連 doc | L4/L9/L13/L14 の接続先と `pairs_test_design: []` の理由を残す | L1 工程 doc / HELIX-workflows 正本 |

### L0 §8 バトン振り分け

- `L1-IN-12` は **NFR-OP-01** として即時採択する
- `L1-IN-15` は本 doc で一括解決せず、以下へ carry する
- 進化 / 老化 / 共生 / 代謝は `NFR-OP-*`
- 既存資産継承と schema 互換は `NFR-MG-*`
- audit 穴のうち secret / 権限制御 / destructive guard は `NFR-SC-*`

## §3 成果物

- **PLAN file**: [`docs/plans/L1/L1-helix-workflows-非機能要求plan.md`](L1-helix-workflows-%E9%9D%9E%E6%A9%9F%E8%83%BD%E8%A6%81%E6%B1%82plan.md)
- **製本 doc**: [`docs/v2/L1-requirements/helix-workflows-nfr.md`](../../v2/L1-requirements/helix-workflows-nfr.md)
- **L4 接続**: `L4-helix-workflows-基本設計plan` で NFR 検証方式と総合テスト設計を pair freeze する

## §4 DoD

- [x] §1 工程表 Step 1-5 完了
- [x] `docs/v2/L1-requirements/helix-workflows-nfr.md` に §1-§8 の 8 section が存在する
- [x] NFR-* が 15 件以上定義されている
- [x] `L1-IN-12` が本文に明示されている
- [x] `python3` + `plan_validator.validate_plan(...)` で frontmatter を検証済み
- [ ] L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) / `L4-helix-workflows-基本設計plan` 起票後の reciprocal dependency 追記
- [ ] tl-advisor / pmo-sonnet による最終レビュー

## §5 関連

- **上流 PLAN**: [L0-helix-workflows-conceptplan](../L0/L0-helix-workflows-conceptplan.md)
- **並走 PLAN**: [L1-helix-workflows-業務要求plan](./L1-helix-workflows-%E6%A5%AD%E5%8B%99%E8%A6%81%E6%B1%82plan.md)
- **製本済み業務要求**: [helix-workflows-business-requirements.md](../../v2/L1-requirements/helix-workflows-business-requirements.md)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../../v2/process/L01-requirements-and-operational-test-design.md)
- **skill**: `skills/workflow/requirements-deriver/SKILL.md`

## §6 L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 PLAN 共通)

- **L3 PLAN 起票時の dependencies.requires**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務要求 / 機能要求 / 技術要求 / 非機能要求) を `dependencies.requires` に列挙する
- **L3↔L12 pair freeze**: L3 起票時に `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票し、L3 非機能要件 (IPA グレード値) と L12 受入テスト設計 (NFR 系 AC-*) を pair freeze する (本 doc は L13 安定性 + L14 運用検証でも多層検証、`next_pair_freeze: L4` を製本 doc frontmatter に明記)
