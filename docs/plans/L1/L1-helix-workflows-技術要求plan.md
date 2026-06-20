---
plan_id: L1-helix-workflows-技術要求plan
title: "L1-helix-workflows-技術要求plan: HELIX-workflows V2 技術要求"
kind: requirements
layer: L1
drive: be
status: finalized
created: 2026-05-26
owner: PM
process_layer: L1
parent_process: HELIX-workflows/helix-process/L1-requirements.md
pairs_test_design: []
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G1 evidence)"
generates:
  - artifact_path: docs/v2/L1-requirements/helix-workflows-technical-requirements.md
    artifact_type: design_doc
dependencies:
  parent: L0-helix-workflows-conceptplan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-要求定義移行plan
  blocks:
    - L3-helix-workflows-機能要件plan
    - L3-helix-workflows-非機能要件plan
    - L4-helix-workflows-方式設計plan
related_docs:
  - HELIX-workflows/helix-process/L1-requirements.md
  - docs/v2/process/L01-requirements-and-operational-test-design.md
  - docs/v2/L0-helix-workflows/concept.md
  - cli/lib/helix_db.py
  - cli/config/vmodel-semantics.yaml
  - cli/config/models.yaml
  - docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
---

## §0 PLAN concept

> **工程**: L1
> **正本**: HELIX-workflows/helix-process/L1-requirements.md
> **本 PLAN の対象**: HELIX-workflows V2 dogfooding における **技術要求 (Technical Requirements)** を起票する。L0 [見直し企画書](../L0/L0-helix-workflows-conceptplan.md) §8 L1 バトンのうち、L1-IN-05/06/07/08/10 を中心に、runtime / DB / CLI / skill injection / mode 回帰 / drift inventory に関する要求を **L4 基本設計の前段要求** として整理する。L1 段階では「要望・制約・互換条件」までを確定し、schema 詳細・migration 手順・event 契約の具体化は L4-L5 で行う。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L0 concept §6.5 / §8、L1 正本、既存 L1 業務要求 PLAN / doc、plan template 精読) | ☑ completed (2026-05-26、必須参照一式確認済) |
| 2 | 既存資産確認 (`cli/lib/helix_db.py` / `cli/config/vmodel-semantics.yaml` / `cli/config/models.yaml` / `cli/helix-*`) | ☑ completed (2026-05-26、現行 schema と注入定義の制約確認済) |
| 3 | ドラフト起草 (`docs/v2/L1-requirements/helix-workflows-technical-requirements.md` + 本 PLAN) | ☑ completed (2026-05-26、本タスクで skeleton 起票) |
| 4 | TL レビュー (`helix review --uncommitted` または同等レビュー、G1 evidence) | □ pending |
| 5 | pmo-sonnet 再 audit (構成漏れ / L1-IN 反映漏れ / frontmatter 整合) | □ pending |
| 6 | 修正反映 + G1 要求定義ゲート判定 + L3/L4 へ引き渡し | □ pending |

## §2 実装計画 (記載項目をどう埋めるか)

### この PLAN が起票する成果物

- **PLAN file (本 PLAN)**: `docs/plans/L1/L1-helix-workflows-技術要求plan.md`
- **製本 doc**: `docs/v2/L1-requirements/helix-workflows-technical-requirements.md`

### §2.1 必須記載項目 (HELIX-workflows L1-requirements.md 正本準拠)

| 項目 | 対象 doc | 内容 |
|---|---|---|
| 採用技術・技術制約 | technical-requirements.md §1 | runtime、model、OS、test framework、DB migration、互換維持方針 |
| 外部連携 / インターフェース要望 | technical-requirements.md §2 | Claude Code / Codex CLI / GitHub / VS Code extension と HELIX harness の接続要望 |
| 既存システム制約 | technical-requirements.md §3 | 現行 helix.db 30+ table、skill 118、cli/helix-* 60、PLAN 324、docs/HELIX-workflows 整合維持 |

### §2.2 L0 §8 L1 バトン振り分け (技術要求 scope)

| L0 §8 項目 | 本 PLAN での扱い | 対象 section |
|---|---|---|
| L1-IN-05 | HELIX-workflows ↔ CLI / skill / helix.db drift 解消方針を技術要求化 | technical-requirements.md §7 |
| L1-IN-06 | 工程別 inventory schema と双方向 mapping を技術要求化 | technical-requirements.md §7 |
| L1-IN-07 | `helix-context` 強化 + `vmodel-semantics.yaml` 正本化 + `helix doctor` audit を技術要求化 | technical-requirements.md §5 |
| L1-IN-08 | R0-R4 + RGC を 9 mode 共通の closure pipeline とする要求を定義 | technical-requirements.md §6 |
| L1-IN-10 | helix.db 二層構造 (V モデル DB + 補助 DB) の要求を整理 | technical-requirements.md §4 |

### §2.3 L4 基本設計への引き渡し

| L1 技術要求 | L4 で具体化するもの |
|---|---|
| TR-01〜TR-05 | 実行環境、model routing、テスト運用、schema migration 手順 |
| L1-IN-10 | core table / audit-event / derived view / auxiliary mode tables の論理 schema、migration 分割 |
| L1-IN-07 | `helix-context` / `helix doctor` / `vmodel-semantics.yaml` の enforcement point |
| L1-IN-08 | closure event の state machine、idempotency_key、rollback / conflict resolution |
| L1-IN-05/06 | detector cadence、inventory registration 契約、drift remediation routing |

### §2.5 L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 PLAN 共通)

- **L3 PLAN 起票時の dependencies.requires**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務要求 / 機能要求 / 技術要求 / 非機能要求) を `dependencies.requires` に列挙する
- **L3↔L12 pair freeze**: L3 起票時に `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票し、L3 技術要件 (採用技術・制約) と L12 受入テスト設計 (技術系 AC-*) を pair freeze する

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L1/L1-helix-workflows-技術要求plan.md`](L1-helix-workflows-技術要求plan.md)
- **製本 doc**: [`docs/v2/L1-requirements/helix-workflows-technical-requirements.md`](../../v2/L1-requirements/helix-workflows-technical-requirements.md)
- **ペア凍結方針**: 技術要求は L1↔L14 の直接ペアではなく、L4 基本設計で具体化し L9 総合テスト設計とペア凍結する (`next_pair_freeze: L4` を製本 doc frontmatter に明記)

## §4 受入条件 / DoD

- [ ] §1 工程表 Step 1-6 すべて完了
- [ ] `docs/plans/L1/L1-helix-workflows-技術要求plan.md` と `docs/v2/L1-requirements/helix-workflows-technical-requirements.md` の 2 ファイルが起票されている
- [ ] technical-requirements.md に `## §1` 〜 `## §8` の 8 section が存在する
- [ ] technical-requirements.md に `TR-` が 5 件以上存在する
- [ ] L1-IN-05/06/07/08/10 が technical-requirements.md 内で明示されている
- [ ] `plan_validator.validate_plan(...)` が pass する
- [ ] TL レビュー evidence が残る (`helix review --uncommitted` または代替セルフレビュー)

## §5 関連 PLAN / ADR / docs

- **上流 PLAN**: [L0-helix-workflows-conceptplan](../L0/L0-helix-workflows-conceptplan.md)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../../v2/process/L01-requirements-and-operational-test-design.md)
- **並走 PLAN**:
  - [L1-helix-workflows-業務要求plan](L1-helix-workflows-業務要求plan.md)
  - L1-helix-workflows-機能要求plan
  - L1-helix-workflows-非機能要求plan
- **下流 PLAN**:
  - L3-helix-workflows-業務要件plan
  - L3-helix-workflows-機能要件plan
  - L3-helix-workflows-非機能要件plan
  - L4-helix-workflows-基本設計plan
- **技術参照**:
  - [cli/lib/helix_db.py](../../../cli/lib/helix_db.py)
  - [cli/config/vmodel-semantics.yaml](../../../cli/config/vmodel-semantics.yaml)
  - [cli/config/models.yaml](../../../cli/config/models.yaml)
