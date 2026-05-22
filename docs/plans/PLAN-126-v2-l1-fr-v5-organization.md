---
plan_id: PLAN-126
title: "PLAN-126: V2 L1-REQUIREMENTS FR-V5 全項目 P0/P1/P2 整理"
layer: L1
kind: retrofit
status: draft
size: M
drive: be
created: 2026-05-23
owner: pmo-sonnet
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — FR-V5 全件 audit・P0/P1/P2 整理・PLAN ID 紐付け"
  - role: docs
    slot_label: "Docs — L1-REQUIREMENTS §3.10 table 形式再構成実装"
  - role: tl
    slot_label: "TL (on-demand) — FR 優先度判断の adversarial check"
generates:
  - artifact_path: docs/v2/L1-REQUIREMENTS.md
    artifact_type: doc_update
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-100
    - PLAN-103
  blocks: []
related_plans:
  - PLAN-100-existing-retrofit-v2-revision
  - PLAN-103-fr-v5-19-20-mk01-mk02-acceptance
  - PLAN-MM-001-v5-framework-master-plan
related_docs:
  - docs/v2/L1-REQUIREMENTS.md
  - docs/v2/CONCEPT.md
  - docs/v2/L2-MASTER.md
---

# PLAN-126: V2 L1-REQUIREMENTS FR-V5 全項目 P0/P1/P2 整理

> **kind**: retrofit (既存 doc を V5 framework 新規約に合わせる更新)
> **layer**: L1 (要件定義層の FR 整理)
> **drive**: be (CLI / framework 要件中心)
> **本 PLAN の役割**: L1-REQUIREMENTS §3.10 の FR-V5-* 全項目に対して、P0/P1/P2 優先度・Phase 配置・PLAN ID 紐付けを整備し、table 形式で再構成する。

---

## §0. 本 PLAN の位置付け

本 PLAN は **PLAN-100 §6 V2 doc 全面見直しのうち L1-REQUIREMENTS §3.10 担当** であり、PLAN-103 (FR-V5-19/20/MK01/MK02 AC 確定) の後段作業。

L1-REQUIREMENTS §3.10 (line 460-485 付近) は FR-V5-1〜22 の記述を持つが、以下の問題が存在する:
- P0/P1/P2 ラベルが付与されていない FR が混在
- 各 FR の対応 PLAN ID が明示されていない
- Phase 配置 (Layer A/B/C) との対応関係が不明
- PLAN-103 で確定した FR-V5-19/20/MK01/MK02 の AC が反映されていない

本 PLAN はこれらを一括解消し、FR-V5-* を機械的に追跡可能な状態にする。

---

## §1. 目的

1. FR-V5-1〜22 全件に P0/P1/P2 優先度ラベルを付与する
2. 各 FR に対応 PLAN ID (PLAN-091〜122 等) を紐付ける
3. §3.10 を table 形式で再構成し、可読性・機械可読性を両立する
4. PLAN-103 で確定した FR-V5-19/20/MK01/MK02 の AC を §3.10 に反映する
5. FR-V5-* ↔ PLAN 間の双方向 trace を確立し、reciprocal 整合を確認する

---

## §2. 背景

### 2.1 FR-V5 現状

L1-REQUIREMENTS §3.10 には FR-V5-1〜22 が記載されている。V5 framework 確立 (2026-05-20) および PLAN-100 Phase 4 (2026-05-22) での V5 19 要素統合を経て、各 FR の実装状況が更新されたが、§3.10 のテキスト記述はリスト形式のままで以下の欠点を持つ:

| 問題点 | 影響 |
|---|---|
| P0/P1/P2 ラベル不在 | gate carry 判定ができない |
| PLAN ID 紐付け不在 | FR → 実装の trace が手動追跡のみ |
| Phase (Layer A/B/C) 配置不明 | V5 3 層構造との整合が不明 |
| FR-V5-19/20/MK01/MK02 AC 未反映 | PLAN-103 成果が §3.10 に到達していない |

### 2.2 PLAN-103 との関係

PLAN-103 は FR-V5-19/20 (PDM subagent 統合・marketing innovation 翻案) および MK01/MK02 の AC 確定に特化した design PLAN。本 PLAN は PLAN-103 の成果を §3.10 に組み込む retrofit であり、かつ全 FR-V5-* の整理を合わせて実施する。

### 2.3 deferred-finding との関係

PLAN-100 Phase 4 readiness audit (2026-05-22) で以下の carry が記録された:

- FR-V5-10〜18 の placeholder 確定 (pmo-sonnet audit で「採番不在」と判定、carry 不要で close 済)
- FR-V5-19/20/MK01/MK02 の AC が §3.10 に未反映

本 PLAN はこれらの carry を最終解消する。

---

## §3. 業界 standard 参照 (WebSearch skip 理由)

本 PLAN は PLAN-100 内拡張 + PLAN-103 後段 retrofit であり、L2 大局判断を新たに含まない。

適用標準:
- **INVEST 原則** (User Stories / FR 設計の業界標準): FR-V5-* の AC 記述が Independent / Negotiable / Valuable / Estimable / Small / Testable を満たすよう整理する。本基準は PLAN-103 §3 で既に引用済み。
- **MoSCoW 優先度付け**: P0 = Must Have / P1 = Should Have / P2 = Could Have の 3 段階は HELIX carry rule と一致。

skip 根拠: 参照すべき業界標準はすべて PLAN-103 §3 で引用済みであり、本 PLAN の retrofit 範囲は §3.10 の再構成のみ (新規方針判断なし)。

---

## §4. スコープ

### In scope
- L1-REQUIREMENTS §3.10 の全 FR-V5-* に対する P0/P1/P2 付与
- 各 FR に対する対応 PLAN ID の紐付け
- §3.10 の table 形式再構成
- PLAN-103 成果 (FR-V5-19/20/MK01/MK02 AC) の §3.10 反映

### Out of scope
- §3.10 以外の §3.* セクションの変更
- FR の新規追加・削除 (本 PLAN は整理のみ)
- PLAN の frontmatter 変更 (PLAN 側の `generates` / `related_docs` 追記は後続 carry)
- L2-MASTER の変更 (PLAN-125 外の別 carry)

---

## §5. 実装計画

### Sprint .1: FR-V5 全件 audit (pmo-sonnet 担当)

**作業内容**:
1. L1-REQUIREMENTS §3.10 を Read し、FR-V5-* 全件を抽出する
2. 各 FR に対して以下を判定・収集する:
   - 現在の P0/P1/P2 (記載なしは「未定」)
   - 対応 PLAN ID (docs/plans/ を grep で照合)
   - Layer A/B/C いずれに属するか (V5 3 層構造との対応)
   - PLAN-103 で AC が確定した FR (V5-19/20/MK01/MK02)
3. audit 結果を table 形式でまとめ、Sprint .2 の委譲 prompt に組み込む

**成果物**: FR-V5 audit table (FR ID / 現 P ラベル / 対応 PLAN / Layer / AC 有無)

受入条件:
- FR-V5-1〜22 + MK01/MK02 全件の audit 結果が揃っている
- 対応 PLAN ID が不明な FR は「未紐付け」として明示されている

### Sprint .2: §3.10 table 形式再構成 (Codex docs 委譲)

**委譲内容** (Sprint .1 audit 結果を bundle として提供):
- §3.10 現行テキストを以下の 2-part 構造に再構成する:
  1. **FR-V5-* master table** (FR ID / title / P0/P1/P2 / 対応 PLAN / Layer / AC link)
  2. **FR-V5-19/20/MK01/MK02 AC 詳細** (PLAN-103 の成果を verbatim で引用)
- 既存の §3.1〜§3.9 の記法を踏襲し、§3.10 のみを変更する
- table の列定義:
  ```
  | FR ID | タイトル | 優先度 | 対応 PLAN | V5 Layer | AC / 状態 |
  ```

受入条件:
- §3.10 に FR-V5-* master table が存在する
- P0/P1/P2 が全 FR に付与されている
- FR-V5-19/20/MK01/MK02 に AC link が記載されている
- §3.10 外の §3.* は変更されていない

### Sprint .3: 検証 (pmo-sonnet 担当)

1. L1-REQUIREMENTS §3.10 再 Read で table 完整性を確認
2. 対応 PLAN ID の実在確認 (`ls docs/plans/PLAN-NNN*.md` で spot check)
3. helix doctor 実行で pass / fail 数確認
4. reciprocal 確認: FR-V5-19/20/MK01/MK02 の AC が PLAN-103 の DoD と整合しているか照合

受入条件:
- helix doctor fail = 0
- §3.10 table の PLAN ID 全件が実在確認済み

---

## §6. 依存・前提

| 依存 | 理由 |
|---|---|
| PLAN-100 complete | §3.10 整理の親コンテキスト確認 |
| PLAN-103 status | FR-V5-19/20/MK01/MK02 AC を §3.10 に verbatim 引用するため、PLAN-103 の DoD が確定していることを前提とする |

**注意**: PLAN-103 が draft 状態の場合、Sprint .2 では「AC 確定済み部分のみ反映、draft 部分は pending 明記」とする。

---

## §7. リスク

| リスク | P | I | 緩和策 |
|---|---|---|---|
| FR-V5-10〜18 の対応 PLAN が存在しない (未実装) | H | M | audit で「未紐付け」として記録し、master table に status=unassigned を明示。P3 carry として defer |
| Codex docs が §3.10 以外のセクションを誤変更する | M | H | 委譲 prompt に `allowed_files: [docs/v2/L1-REQUIREMENTS.md]` + §3.10 行範囲を明示。Sprint .3 で diff check |
| P0/P1/P2 判定で PMO と PM の認識が乖離する | M | M | tl-advisor (on-demand) を Sprint .1 後に発火し、audit 結果の adversarial check を実施する |
| FR の AC が PLAN-103 draft から変化している | L | M | Sprint .1 で PLAN-103 の最新 DoD を Read し、AC は PLAN-103 正本から引用する |

---

## §8. DoD (完了条件)

- [ ] L1-REQUIREMENTS §3.10 が table 形式で再構成されており、FR-V5-1〜22 + MK01/MK02 全件が掲載されている
- [ ] 全 FR に P0/P1/P2 ラベルが付与されている
- [ ] FR-V5-19/20/MK01/MK02 に AC link (PLAN-103 参照) が記載されている
- [ ] 対応 PLAN ID が全件 (または「未紐付け」として明示) 記載されている
- [ ] helix doctor fail = 0
- [ ] plan_validator: `python3 cli/lib/plan_validator.py --file docs/plans/PLAN-126-v2-l1-fr-v5-organization.md` が errors = 0

---

## §9. 関連資産

- `docs/v2/L1-REQUIREMENTS.md` — 編集対象 (§3.10 のみ)
- `docs/plans/PLAN-103-fr-v5-19-20-mk01-mk02-acceptance.md` — FR-V5-19/20/MK01/MK02 AC 正本
- `docs/plans/PLAN-100-existing-retrofit-v2-revision.md` — parent retrofit PLAN
- `docs/plans/PLAN-MM-001-v5-framework-master-plan.md` — 最上位 master plan
