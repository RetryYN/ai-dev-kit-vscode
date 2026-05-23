---
plan_id: PLAN-206
title: "PLAN-206: SKILL.md frontmatter JSON Schema (PLAN-167 並列)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-167-plan-frontmatter-v2-schema.md   # from dependencies.parent
size: S
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — schemas/skill-frontmatter.schema.json 新規作成・skill_catalog.py 統合・helix skill validate 実装"
  - role: docs
    slot_label: "Docs — VS Code yaml extension 設定ガイド・docs/commands/skill-schema.md 起草"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-167 との schema 設計整合確認・SKILL.md 107 件 backward 互換チェック方針レビュー"
generates:
  - artifact_path: schemas/skill-frontmatter.schema.json
    artifact_type: json_config
  - artifact_path: cli/lib/skill_catalog.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_skill_schema_validation.py
    artifact_type: test
  - artifact_path: docs/commands/skill-schema.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-167
  requires:
    - PLAN-167
  blocks: []
related_adr: []
related_plans:
  - PLAN-167 (PLAN frontmatter schema v2 — 同思想の先行 PLAN、Sprint .3 で .vscode/settings.json が競合するため直列)
  - PLAN-091 (V5 framework core — VALID_LAYERS / VALID_DRIVES enum 正本)
acceptance_criteria:
  - "schemas/skill-frontmatter.schema.json が JSON Schema draft-07 形式で生成され、name / description / metadata.helix_layer / triggers / verification / compatibility フィールドを網羅している"
  - "helix skill validate <skill-id> が schema check を実行し、frontmatter 違反を即時検出する"
  - ".vscode/settings.json の yaml.schemas で skills/**/SKILL.md を auto-complete できる"
  - "python3 -m py_compile cli/lib/skill_catalog.py PASS"
  - "unit test 8 case 全 PASS"
  - "既存 SKILL.md 107 件が schema validation PASS (backward 互換保証)"
---

# PLAN-206: SKILL.md frontmatter JSON Schema (PLAN-167 並列)

## L2 凍結 (ADR snapshot)

本 PLAN は PLAN-167 で確立した JSON Schema 化パターンを SKILL.md に適用する実装。
新規 L2 大局判断は発生しないため ADR snapshot は不要。

## 背景

PLAN-167 が PLAN frontmatter の JSON Schema 化を完遂する。同じ思想を SKILL.md (107 件)
にも適用し、HELIX の 2 大文書 (PLAN / SKILL) に一貫した schema validation 基盤を持たせる。

現状の課題:

1. **IDE 補完なし**: frontmatter のフィールド名・型・値の誤りが
   `helix skill catalog rebuild` 実行まで検出されず、スキル推挙精度が低下する
2. **schema 定義が CLI 実装に埋め込まれている**: `skill_catalog.py` の parser が
   型チェックを兼任しており、schema 正本と実装が一体化している

## WebSearch 履歴

- Query 1: "JSON Schema draft-07 nested object metadata helix_layer YAML frontmatter validation"
  → `properties.metadata` に nested object schema を定義、`helix_layer` を `enum` で指定が標準
- Query 2: "JSON Schema array string triggers verification yaml VS Code auto-complete"
  → `type: array, items: {type: string}` で定義、`minItems: 1` 推奨
- Query 3: "jsonschema python validate nested YAML additionalProperties false best practice"
  → 外側は warn-only で導入、段階的に fail-close 化するパターンが推奨

## 設計方針

### schema 構造

`schemas/skill-frontmatter.schema.json` (JSON Schema draft-07):

- `required`: name / description / metadata
- `metadata.helix_layer` enum: plan_validator.py の `VALID_LAYERS` と同期
- `compatibility.drive` enum: `VALID_DRIVES` と同期
- `triggers` / `verification`: `array of string`
- enum 正本は plan_validator.py、schema 生成時に動的読み込みを検討

### skill_catalog.py 統合

- `validate_skill_frontmatter(path, schema)` 関数を追加し、既存 parse ロジックの前段に配置
- jsonschema ライブラリ未インストール時は graceful fallback (validation skip + warn)
- `helix skill validate <skill-id>` サブコマンドで単独実行可能

### VS Code 設定

PLAN-167 Sprint .3 と `.vscode/settings.json` が競合するため直列実施 (PLAN-167 完了後):

```json
"yaml.schemas": {
  "./schemas/plan-frontmatter-v2.schema.json": "docs/plans/PLAN-*.md",
  "./schemas/skill-frontmatter.schema.json": "skills/**/SKILL.md"
}
```

## 実装計画

### Sprint .1: JSON Schema 定義 (Codex se、size S)

`schemas/skill-frontmatter.schema.json` 新規作成。
既存 SKILL.md 107 件に対して backward 互換確認 (107 件 PASS が完了条件)。

### Sprint .2: skill_catalog.py 統合 + helix skill validate (Codex se、size S)

`validate_skill_frontmatter()` 追加。`helix skill validate <skill-id>` 実装。
`python3 -m py_compile` PASS + unit test 8 case PASS が完了条件。

### Sprint .3: VS Code 設定 + docs (Codex docs、size S)

PLAN-167 Sprint .3 完了後に `.vscode/settings.json` 追記。
`docs/commands/skill-schema.md` 起草。pmo-sonnet review が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/skill_catalog.py` PASS
- [ ] unit test 8 case 全 PASS
- [ ] 既存 SKILL.md 107 件 backward 互換 PASS
- [ ] `bash -n cli/helix-skill` PASS (validate サブコマンド追加箇所)
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] schemas/skill-frontmatter.schema.json 生成 (JSON Schema draft-07)
- [ ] skill_catalog.py に schema validation 統合
- [ ] helix skill validate で frontmatter 違反即時検出
- [ ] .vscode/settings.json に skills/**/SKILL.md エントリ追加
- [ ] unit test 8 case PASS
- [ ] docs/commands/skill-schema.md 起草完了

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 | 本 PLAN §設計方針 |
| ③ テスト設計 | cli/lib/tests/test_skill_schema_validation.py (Sprint .2 同時起票) |
| ② 実装コード | schemas/skill-frontmatter.schema.json + cli/lib/skill_catalog.py |
| ④ テストコード | cli/lib/tests/test_skill_schema_validation.py |

双方向 trace:
- 本 PLAN → テストコード: acceptance_criteria に 8 case の検証観点を記載
- テストコード → 本 PLAN: docstring に「PLAN-206 §acceptance_criteria」明記

## 関連 reference

- PLAN-167 (先行 PLAN、Sprint .3 直列依存)
- PLAN-091 (VALID_LAYERS / VALID_DRIVES enum 正本)
- cli/lib/skill_catalog.py (既存 frontmatter parser)
- cli/lib/plan_validator.py (enum 正本参照元)
- https://json-schema.org/draft-07/schema
