---
plan_id: PLAN-NNN-impl-slug
title: "PLAN-NNN: (実装タイトル placeholder)"
kind: impl
layer: L7              # 新 15 工程: L7 実装スプリント (旧 L4 から再採番、docs/v2/process/README.md §既存資産との関係 参照)
drive: be
status: draft
created: 2026-MM-DD
owner: PM
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程の subordinate (docs/v2/process/L07-implementation-sprint.md 参照)
parent_design: docs/v2/L6-function-design/<feature>/<function>.md   # ★必須: L6 機能設計 doc への path (L0-L6 設計工程で確定済の親 doc)
pairs_test_design:                                                    # ★必須: V-model 4 artifact ③ への path
  - docs/v2/L7-test-design/<feature>-unit-test-design.md               #   単体テスト設計 (L6 機能設計とペア凍結済、本工程で実装+実施)
  - docs/v2/L8-test-design/<feature>-integration-test-design.md        #   結合テスト設計 (L5 詳細設計とペア凍結済、L8 で実施)
  - docs/v2/L9-test-design/<feature>-system-test-design.md             #   総合テスト設計 (L4 基本設計とペア凍結済、L9 で実施)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: se
    slot_label: "SE — CLI / 機能実装"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・整合確認"
generates:
  - artifact_path: cli/lib/<module>.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_<module>.py
    artifact_type: test
  - artifact_path: cli/helix-<command>
    artifact_type: cli_extension
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-NNN-design
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
PLAN-091 の実装準備として、kind 固有の 8 ステップ実行形を確立し、design artifact とのリンクを前提化する。

## §1 目的
実装対象を最小差分で起票し、機械チェック・テスト・レビューまでを Plan テンプレート単位で再現可能な流れに定着させる。

## §2 背景
- 既存 Plan の種類別 Step 定義が実装向けに不均一であるため、PLAN-091 で種別別標準を固定する。
- L4 実装では Entry → Exit の検証順序をテンプレート上で固定し、再現可能性を上げる。

## §3 実装計画
### Step 1: Entry
- 直前 PLAN の完了確認、依存条件の明示、ロール整合の再確認を行う。

### Step 2: 着手前調査
- `helix code find` による再利用候補、重複シンボル、既存テストの有無を確認する。

### Step 3: 機能設計+テスト設計 pair freeze
- design と test-design の対応先を固定し、変更対象の範囲外を明確化する。

### Step 4: 実装
- 対象 artifact（CLI コード/ドキュメント）を最小単位で更新し、既存仕様を崩さないよう差分を抑える。

### Step 5: 機械チェック
- `shellcheck` / `markdownlint` / `yamllint`、`helix code stats` 及び関連 lint・静的検査を実行し結果を記録。

### Step 6: テスト
- 対象範囲単体・関連回帰・必要なら全回帰を実行し、失敗時は再現手順を記載する。

### Step 7: レビュー
- セルフレビュー + 1 段階の高信頼レビュー観点（安全性、v-model trace、既存契約）を実施。

### Step 8: DoD
- 受入条件を checklist 化し、関連 PLAN / ADR / docs 参照整合まで完了したら実装 DoD とする。

## §4 受入条件 / DoD
- Step 1〜8 のすべてが該当セクションに存在。
- `dependencies` に設計 PLAN が示され、`implements` 先が明示されている。
- 受入: `frontmatter kind == impl`、`§0〜§5` 完備、テスト結果が記録済み。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-021〜ADR-024
- docs: `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`, `skills/workflow/design-doc/SKILL.md`
