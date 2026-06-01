---
plan_id: L3-helix-workflows-機能要件plan
title: "L3-helix-workflows-機能要件plan: HELIX-workflows V2 機能要件 (確定版)"
kind: requirements
layer: L3
drive: be
status: finalized
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
  - artifact_path: docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
    artifact_type: design_doc
dependencies:
  parent: L1-helix-workflows-機能要求plan
  requires:
    - L0-helix-workflows-conceptplan
    - L1-helix-workflows-業務要求plan
    - L1-helix-workflows-機能要求plan
    - L1-helix-workflows-技術要求plan
    - L1-helix-workflows-非機能要求plan
    - L3-helix-workflows-業務要件plan
  blocks:
    - L4-helix-workflows-方式設計plan
related_docs:
  - HELIX-workflows/helix-process/L3-requirements-definition.md
  - docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md
  - docs/v2/L0-helix-workflows/concept.md
  - docs/v2/L1-requirements/helix-workflows-business-requirements.md
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
---

## §0 PLAN concept

> **工程**: L3 (L3↔L12 pair freeze)
> **正本**: HELIX-workflows/helix-process/L3-requirements-definition.md
> **本 PLAN の対象**: L1 [機能要求 doc](../../v2/L1-requirements/helix-workflows-functional-requirements.md) FR-01〜FR-12 と [技術要求 doc](../../v2/L1-requirements/helix-workflows-technical-requirements.md) TR-01〜TR-08 を統合し、**機能一覧 (確定版) / 機能仕様 / 入出力定義** として L3 で凍結する。L1 は要望レベル、L3 は CLI 契約・出力・副作用・技術制約まで含む仕様レベルに昇格させる。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (L0 概念、L1 BR/FR/TR、L3 業務要件 doc、L03 template、L12 pair skeleton の精読) | ☑ completed (2026-05-26、本 turn で実施) |
| 2 | L1 FR-01〜FR-13 + TR-01〜TR-08 の統合設計 (L3 FR 再採番、重複統合、不足補完、trace 方針確定) + **ユーザー要求 (機能一覧 + 用語一覧 SSoT) 由来 L3 拡張 FR 追加** | ☑ completed (2026-05-26 / 2026-05-29、core FR 14 件 + L3 拡張 4 件 (FR-DOCREVIEW-01 BR-11 由来 / FR-CHANGEPROP-01 BR-12 由来 / **FR-FNREG-01 ユーザー要求由来 (機能一覧 SSoT) / FR-GLOSSARY-01 ユーザー要求由来 (用語一覧 SSoT)**) + FR-13 統合 mapping = **18 件**へ統合、2026-05-29 ユーザー要求反映) |
| 3 | 製本 doc 起草 (`functional-requirements-detail.md` §1-§4、機能一覧 / 機能仕様 / 入出力定義 / L1→L3 mapping) | ☑ completed (2026-05-26、本 turn で起票) |
| 4 | L12 pair 連携起草 (Codex SE は L12 編集禁止 → PROPOSE 列挙、Opus PM が後段で L12 §2 に一括反映) | ☑ completed (2026-05-26 / 2026-05-29、AC-FR-01〜18 propose → Phase E.B.1 で Opus が L12 §2 に detail 反映済、L3 拡張 4 件 AC-FR-15 (FR-DOCREVIEW-01) + AC-FR-16 (FR-CHANGEPROP-01) + AC-FR-17 (FR-FNREG-01) + AC-FR-18 (FR-GLOSSARY-01) 含む、balance_ratio = 18/18 = 1.0) |
| 5 | TL レビュー (`helix review --uncommitted` + G3 evidence 整理) | ☑ completed (2026-05-29、tl-advisor adversarial check verdict = changes_required、P1 FR-13 mapping / L3 doc 母数不整合 / CLI 契約 `--plan-id`、P2 FR-DOCREVIEW/CHANGEPROP core 包含 + AC-FR 並び・冒頭件数 すべて反映、8 edit) |
| 6 | pmo-sonnet 再 audit + 修正反映 → G3 ゲート判定 → L4 基本設計へ引き渡し | ☑ completed (2026-05-29、pmo-sonnet verdict = yes_with_minor_changes、P-1 PLAN §4 DoD 20→23 件 drift 反映済、P-3 FR-INV-01 line 38 痕跡を FR-GLOSSARY-01 委譲明示済、P-2/P-4/P-5 は軽微で L4 carry。新規 FR-FNREG-01 + FR-GLOSSARY-01 ユーザー要求反映済、core FR 14→18 件、balance_ratio = 18/18 = 1.0) |

## §2 実装計画 (機能一覧 / 機能仕様 / 入出力定義)

### この PLAN が起票する成果物

- **PLAN file (本 PLAN)**: `docs/plans/L3/L3-helix-workflows-機能要件plan.md`
- **製本 doc**: `docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md`
- **L12 pair propose**: 製本 doc 内 `## L12 PAIR PROPOSE (§2 機能系 AC-FR-*)`

### §2.1 必須記載項目 (HELIX-workflows L3-requirements-definition.md 正本準拠)

| 項目 | 対象 doc | 内容 |
|---|---|---|
| 機能一覧 (確定版) | functional-requirements-detail.md §1 | L3 FR-* を再採番し、L1 FR + TR の統合結果を 1 行ずつ定義する |
| 機能仕様 | functional-requirements-detail.md §2 | 各 FR の振る舞い、状態遷移、エラー処理を仕様レベルで固定する |
| 入出力定義 | functional-requirements-detail.md §3 | CLI input、CLI output、exit code、副作用、技術制約を各 FR 単位で定義する |
| L1→L3 統合 mapping | functional-requirements-detail.md §4 | L1 FR-01〜13 / TR-01〜08 の 21 件 + **ユーザー要求 2 件 (機能一覧 SSoT / 用語一覧 SSoT)** = 計 23 件 を L3 FR (core 14 + L3 拡張 4 + FR-13 統合 mapping) **= 計 18 件 + FR-13 mapping** へ過不足なく割り付ける (2026-05-29 ユーザー要求 + FR-13 反映) |
| L12 pair propose | functional-requirements-detail.md 本文 | 各 FR に対応する AC-FR-* を 1:1 以上で提案し、L12 側 detail 化のインプットにする |

### §2.2 L1 → L3 統合方針

| L3 FR-ID | 主な統合元 | 詳細化方針 |
|---|---|---|
| FR-NSM-01 | L1 FR-01 + TR-05 | NSM 集計、6 axes 判定、helix.db view/query 契約を固定する |
| FR-GR-01 | L1 FR-02 + TR-02 | Guardrail 3 軸、fail-close 条件、agent throttle 出力を固定する |
| FR-TDD-01 | L1 FR-03 + TR-04 | L7 sprint 7 step の順序強制、pytest/Bats/verify 連携を固定する |
| FR-9MODE-01 | L1 FR-04 + TR-01 | 9 mode 入口判定、runtime 前提、route 判定入力を固定する |
| FR-GATE-01 | L1 FR-05 + TR-05 | gate 合成式、static_subchecks、gate-policy 参照面を固定する |
| FR-IMPACT-01 | L1 FR-06 + TR-05 | 影響範囲 query、trace view、5 秒 SLA を固定する |
| FR-EVT-01 | L1 FR-07 + TR-06 | mode closure event、Forward 復帰先、event metadata を固定する |
| FR-4ART-01 | L1 FR-08 + TR-06 | 4 artifact / pair freeze 監査、trace 欠落判定を固定する |
| FR-INV-01 | L1 FR-09 + TR-06 | inventory / density view、工程別資産登録契約を固定する |
| FR-CTX-01 | L1 FR-10 + TR-02 + TR-07 | layer context injection、models.yaml / vmodel-semantics.yaml 注入契約を固定する |
| FR-DRIFT-01 | L1 FR-11 + TR-03 | discrepancy routing、OS/runtime 差異検出、routing 先提案を固定する |
| FR-PLAN-01 | L1 FR-12 + TR-08 | dependency / generates trace、互換維持、deprecated warning 契約を固定する |
| FR-DOCTOR-01 | L1 FR-08 + FR-11 + TR-04 | helix doctor audit、warn 集約、fail-close entrypoint を固定する |
| FR-MIGR-01 | L1 TR-05 + TR-08 | schema migration、retrofit pipeline、互換期間中の移行契約を固定する |
| FR-DOCREVIEW-01 (L3 拡張、BR-11 由来) | L1 BR-11 | ドキュメント品質レビュー機能 (`helix codex --role doc-reviewer` 召喚 coverage ≥ 95%、4 視点 + 業界標準 + V-model 量閉じ性) |
| FR-CHANGEPROP-01 (L3 拡張、BR-12 由来) | L1 BR-12 | 変更追跡 + デグレ禁止 ratchet 機能 (`helix doctor check_*` 3 軸 pre-commit / CI hook fail-close) |
| **FR-13 (統合 mapping)** | **L1 FR-13** | **PLAN 起票レビュー機能を新 FR でなく `FR-GATE-01 + FR-PLAN-01 + FR-CTX-01` への横断機能として実現 (PLAN 起票時に tl-advisor 自動相談、ユーザー確認の前に正当性レビュー)。tl-advisor 推奨 (2026-05-29) で最小修正・core 16 件維持** |
| **FR-FNREG-01** (L3 拡張) | **ユーザー要求 (2026-05-29) + BR-09 拡張** | 機能一覧 SSoT (`cli/config/functional-registry.yaml`) + 自動チェック (`helix doctor check_fr_sot_alignment`、L4 carry)。FR-INV-01 の FR 特化版、`implementation_status` 列必須は共通、L0 §12.1 用語整合は FR-GLOSSARY-01 連携 |
| **FR-GLOSSARY-01** (L3 拡張) | **ユーザー要求 (2026-05-29) + L0 §12.1 Glossary** | ドメイン用語 SSoT (`cli/config/glossary.yaml` = L0 §12.1 機械可読 mirror) + 自動チェック (`helix doctor check_glossary_coverage`、L4 carry)。DDD ユビキタス言語 + anti-corruption layer 機械強制、子 doc 独自定義禁止 |

### §2.3 L3 接続規約 (2026-05-26、L3 3 PLAN 共通)

- **dependencies.requires**: L3 3 PLAN は L0 + L1 4 PLAN を requires に列挙する
- **L3↔L12 pair freeze**: L12 pair artifact は `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` を共有する
- **本 PLAN の pair 方針**: L12 file は編集禁止のため、L12 側へ移管すべき AC-FR-* は製本 doc の propose section に保持する
- **L4 接続**: `L4-helix-workflows-基本設計plan` は L3 業務 / 機能 / 非機能の 3 PLAN を requires に列挙する
- **L4↔L9 pair**: L4 起票時に総合テスト設計 pair artifact を同時起票する

## §3 成果物

- **PLAN file (本 PLAN)**: [`docs/plans/L3/L3-helix-workflows-機能要件plan.md`](L3-helix-workflows-機能要件plan.md)
- **製本 doc**: [`docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md`](../../v2/L3-requirements/helix-workflows-functional-requirements-detail.md)
- **L12 pair artifact (参照のみ)**: [`docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md`](../../v2/L12-test-design/helix-workflows-acceptance-test-design.md)
- **ペア凍結**: L3↔L12 (機能要件 ⇔ 受入テスト設計)

## §4 受入条件 / DoD

- [ ] §1 工程表 Step 1-6 すべて完了
- [ ] §2.1 必須記載項目 5 件が製本 doc に反映済
- [ ] L3 FR-* の unique 件数が 12 件以上
- [ ] L1 FR-01〜FR-13 + TR-01〜TR-08 の **21 件 + ユーザー要求 2 件 (機能一覧 / 用語一覧 SSoT) = 計 23 件** が §4 mapping で過不足なく trace されている (2026-05-29 pmo-sonnet D1 反映、20→23 件)
- [ ] `## L12 PAIR PROPOSE (§2 機能系 AC-FR-*)` に AC-FR-* が定義され、`AC_count / FR_count >= 1.0`
- [x] plan_validator が errors なし (2026-05-29、WARN 1 件 = L4-helix-workflows-基本設計plan 未起票は将来案件で許容)
- [x] tl-advisor / review evidence を残して G3 凍結へ引き渡せる状態 (2026-05-29、tl-advisor + pmo-sonnet audit + drift fix + 新規 FR 2 件追加すべて完遂)

## §5 関連 PLAN / ADR / docs

- **上流 PLAN**: [L1-helix-workflows-機能要求plan](../L1/L1-helix-workflows-機能要求plan.md) / L1 技術要求plan / L1 業務要求plan / L1 非機能要求plan
- **L3 姉妹 PLAN**: [L3-helix-workflows-業務要件plan](./L3-helix-workflows-業務要件plan.md) / `L3-helix-workflows-非機能要件plan`
- **L3 姉妹 doc**: [helix-workflows-business-requirements-detail.md](../../v2/L3-requirements/helix-workflows-business-requirements-detail.md)
- **HELIX-workflows L3 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **工程 doc**: [docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md](../../v2/process/L03-requirements-definition-and-acceptance-test-design.md)
- **L12 ペア相手**: [HELIX-workflows/helix-process/L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md)
- **template**: [cli/templates/plan/v2/L03-requirements-definition-template.md](../../../cli/templates/plan/v2/L03-requirements-definition-template.md)
- **下流 PLAN**: `L4-helix-workflows-基本設計plan`
