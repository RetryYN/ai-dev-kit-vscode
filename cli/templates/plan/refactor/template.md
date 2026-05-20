---
plan_id: PLAN-NNN-refactor-slug
title: "PLAN-NNN: (リファクタタイトル placeholder)"
kind: refactor
layer: L4
drive: be
status: draft
created: 2026-MM-DD
owner: PM
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: se
    slot_label: "SE — リファクタ実装"
  - role: qa
    slot_label: "QA — 回帰確認・機能不変検証"
generates:
  - artifact_path: cli/lib/<module>.py
    artifact_type: python_module
dependencies:
  parent: PLAN-091
  requires: []
  blocks: []
related_adr:
  - ADR-NNN-related
related_docs:
  - docs/plans/PLAN-NNN-parent.md
---

## §0 PLAN
既存実装の改善を、機能不変を守りながら実施するための refactor kind 標準案を定義する。

## §1 目的
可読性・保守性・追従性を高め、振る舞い変更を起こさない形での改善を行う。

## §2 背景
仕様追加のないリファクタリングでは、既存仕様逸脱リスクが高くなるため、前提固定のテンプレート化が必要。

## §3 実装計画
### 機能不変宣言
- 変更対象の振る舞い範囲を明記し、「機能変更なし」を明文化する。

### before/after 構造
- 対象モジュールの構造差分を「before / after」で比較可能化する。

### テスト維持（新規追加なし）
- 既存テストを維持し、新規テストは追加しない方針を記録。

### 回帰確認
- 既存テスト再実行＋必要最小の回帰指標で変更前後一致を確認。

## §4 受入条件 / DoD
- 機能不変が明示され、変更前後の振る舞い差分説明がある。
- before/after の観点が明文化され、既存テスト維持方針が反映される。
- 回帰確認結果が記録済み。

## §5 関連 PLAN / ADR / docs
- PLAN: PLAN-091
- ADR: ADR-023
- docs: `helix/HELIX_CORE.md`, `skills/SKILL_MAP.md`, `skills/workflow/design-doc/SKILL.md`
