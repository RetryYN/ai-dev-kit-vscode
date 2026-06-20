---
plan_id: L1-helix-workflows-機能要求plan
title: "L1-helix-workflows-機能要求plan: HELIX-workflows V2 機能要求"
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
  - artifact_path: docs/v2/L1-requirements/helix-workflows-functional-requirements.md
    artifact_type: design_doc
dependencies:
  parent: L0-helix-workflows-conceptplan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-要求定義移行plan
  blocks:
    - L3-helix-workflows-機能要件plan
related_docs:
  - HELIX-workflows/helix-process/L1-requirements.md
  - docs/v2/process/L01-requirements-and-operational-test-design.md
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - cli/templates/plan/v2/L01-requirements-template.md
  - docs/plans/L1/L1-helix-workflows-要求定義移行plan.md
---

## §0 PLAN concept

> **工程**: L1
> **正本**: HELIX-workflows/helix-process/L1-requirements.md
> **本 PLAN の対象**: HELIX-workflows V2 dogfooding における **機能要求** (Functional Requirements、FR) を起票する。L0 [見直し企画書](../L0/L0-helix-workflows-conceptplan.md) §8 のうち **L1-IN-01 / 02 / 11** を主 scope とし、L0 §3 / §5 / §6.5 / §8 から導出される周辺機能を FR へ再構成する。業務要求 sibling doc [`helix-workflows-business-requirements.md`](../../v2/L1-requirements/helix-workflows-business-requirements.md) を上位文脈とし、L3 `L3-helix-workflows-機能要件plan` で詳細化する。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L0 concept §5 / §6.5 / §8、L1 業務要求 PLAN、L1 正本、L01 template、CLI help) | ☑ completed (2026-05-26) |
| 2 | 機能要求 scope 正規化 (L1-IN-01/02/11 を主対象に、9 mode / gate / impact query / trace / context injection を周辺 FR として整理) | ☑ completed (2026-05-26) |
| 3 | ドラフト起草 (`docs/v2/L1-requirements/helix-workflows-functional-requirements.md` に FR / UC / flow / I/O を記載) | ☑ completed (2026-05-26) |
| 4 | TL レビュー (tl-advisor、G1 evidence 用 adversarial check) | □ pending |
| 5 | pmo-sonnet 再 audit (構造整合 / carry / downstream 参照整合) | □ pending |
| 6 | 修正反映 + G1 事前確認 + L3 L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) へ引き渡し | □ pending |

## §2 実装計画 (記載項目をどう埋めるか)

### この PLAN が起票する成果物

- **PLAN file (本 PLAN)**: `docs/plans/L1/L1-helix-workflows-機能要求plan.md`
- **製本 doc**: `docs/v2/L1-requirements/helix-workflows-functional-requirements.md`

### §2.1 機能一覧

製本 doc §1 では FR-01 以降を列挙し、最低限以下の機能群をカバーする。

| 機能群 | 主な内容 |
|---|---|
| NSM / Guardrail / TDD | 6 axes NSM 判定、Guardrail 3 軸 fail-close、L7 sprint 7 step 順序強制 |
| Mode / Gate | 9 mode 入口判定、Forward 復帰 event、gate_verdict 合成判定 |
| Trace / Query | 4 artifact / pair freeze 監査、影響範囲 query、inventory / density 可視化 |
| Injection / Routing | layer context injection、discrepancy routing、PLAN dependency / generates trace |

### §2.2 利用シナリオ

製本 doc §2 では、少なくとも以下の利用シナリオを記述する。

| シナリオ群 | 記載観点 |
|---|---|
| PM 業務シナリオ | L0 起票から L1/L3/L4-L14 への主線進行、NSM / Guardrail の観測点 |
| Codex 委譲シナリオ | `helix plan` / `helix gate` / `helix handover` を経由した実装継続 |
| 9 mode 切替シナリオ | Discovery / Incident / Recovery / Reverse から Forward 復帰する経路 |
| 影響範囲分析シナリオ | 改修時に trace query で関連 PLAN / gate / mode_transition を引く流れ |

### §2.3 操作とデータの流れ

製本 doc §3 では、`helix command → helix.db state/view → 次工程` の流れを機能要求レベルで整理する。

| 対象 | 記載方針 |
|---|---|
| PLAN 操作 | `helix plan draft/review/finalize` と `plan_registry` / dependency 連携 |
| Gate 操作 | `helix gate` と `gate_pass` / `decision_trace` / static_subchecks |
| Mode 遷移 | `helix mode` / `helix route` / `helix reverse|discovery|incident|recovery` と `mode_transition` |
| Trace / Query | `helix code find`、impact query、`v_model_alignment_score` / `discrepancy_log` |

### §2.4 入出力

製本 doc §4 では、CLI help と concept 正本を基に command ごとの入出力と副作用を整理する。

| 対象 command | 記載方針 |
|---|---|
| `helix plan draft` | frontmatter / template から PLAN file を生成、dependency を登録 |
| `helix gate G1` | PLAN + 製本 doc から pass/fail/block を返し、gate 記録を残す |
| `helix mode` / `helix route` | detector / signal から mode 決定、Forward 復帰候補を返す |
| `helix reverse` / `helix discovery` / `helix incident` / `helix add-feature` / `helix retrofit` / `helix recovery` | 各 mode の state 更新と closure 後の復帰 event を記載 |
| `helix handover` / `helix interrupt` / `helix code find` | 継続運用・差し戻し・流用候補探索の入出力を記載 |

### §2.4.1 L3 接続規約 (2026-05-26 tl-advisor G1 P1 #2/#3 反映、4 L1 PLAN 共通)

- **L3 PLAN 起票時の dependencies.requires**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件) は L1 4 PLAN 全件 (業務要求 / 機能要求 / 技術要求 / 非機能要求) を `dependencies.requires` に列挙する
- **L3↔L12 pair freeze**: L3 起票時に `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を pair artifact として同時起票し、L3 FR-* / NFR-* と L12 受入テスト設計 (AC-*) を pair freeze する (L1↔L14 で運用テストペア凍結したのと同じ構造)

### §2.5 L0 §8 振り分け

| L0 §8 項目 | 本 PLAN での扱い | 製本 doc 反映先 |
|---|---|---|
| L1-IN-01 | 主 scope | FR-01 |
| L1-IN-02 | 主 scope | FR-02 |
| L1-IN-11 | 主 scope | FR-03 |
| L1-IN-06 / 07 / 08 / 10 | 周辺機能として導出、詳細 schema は技術要求 / L3 に carry | FR-04〜FR-11 |
| L1-IN-03 / 04 / 05 / 09 / 12 | 業務要求・技術要求・非機能要求との接続条件として参照 | §5 carry / 関連 doc |

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L1/L1-helix-workflows-機能要求plan.md`](L1-helix-workflows-機能要求plan.md)
- **製本 doc**: [`docs/v2/L1-requirements/helix-workflows-functional-requirements.md`](../../v2/L1-requirements/helix-workflows-functional-requirements.md)
- **ペア凍結 carry**: 本 doc 自体は L14 運用テストの直接ペア artifact ではない。L1↔L14 ペアは業務要求 doc 側で担保し、本 doc の FR 詳細化は L3 要件定義で行い、L12 受入テスト設計の pair artifact 化へ引き渡す。

## §4 受入条件 / DoD

- [ ] §1 工程表 Step 1-6 すべて完了
- [ ] 製本 doc に `## §1`〜`## §6` の 6 セクションが存在する
- [ ] 製本 doc に FR-* が 7 件以上記載され、L1-IN-01 / 02 / 11 が明示対応している
- [ ] CLI help 参照に基づく command input / output / side effect が §4 に記載されている
- [ ] PLAN file `generates.artifact_path` と製本 doc 実体 path が一致している
- [ ] 製本 doc `parent_plan` が `L1-helix-workflows-機能要求plan` と一致している
- [ ] tl-advisor review / pmo-sonnet audit に耐える carry と downstream 境界が明示されている

## §5 関連 PLAN / ADR / docs

- **上流 PLAN**: [L0-helix-workflows-conceptplan](../L0/L0-helix-workflows-conceptplan.md)
- **sibling PLAN / doc**: [L1-helix-workflows-業務要求plan](L1-helix-workflows-業務要求plan.md) / [helix-workflows-business-requirements.md](../../v2/L1-requirements/helix-workflows-business-requirements.md)
- **HELIX-workflows 正本**: [HELIX-workflows/helix-process/L1-requirements.md](../../../HELIX-workflows/helix-process/L1-requirements.md)
- **工程 doc**: [docs/v2/process/L01-requirements-and-operational-test-design.md](../../v2/process/L01-requirements-and-operational-test-design.md)
- **template**: [cli/templates/plan/v2/L01-requirements-template.md](../../../cli/templates/plan/v2/L01-requirements-template.md)
- **integration-map**: [HELIX-workflows/helix-process/integration-map.md](../../../HELIX-workflows/helix-process/integration-map.md)
- **下流 PLAN**: L3 3 PLAN (業務要件 / 機能要件 / 非機能要件)
