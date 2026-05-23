---
plan_id: PLAN-167
title: "PLAN-167: PLAN frontmatter schema v2 (V5 拡張 + JSON Schema 化)"
kind: refactor
layer: cross
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — JSON Schema 定義・plan_validator.py schema validation 統合・helix plan new 拡張"
  - role: docs
    slot_label: "Docs — VS Code yaml extension 設定ガイド・schema 利用ドキュメント起草"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 plan_validator.py との整合確認・PLAN-091 enum 正本との差分チェック"
generates:
  - artifact_path: schemas/plan-frontmatter-v2.schema.json
    artifact_type: json_config
  - artifact_path: cli/lib/plan_validator.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_validator.py
    artifact_type: test
  - artifact_path: .vscode/settings.json
    artifact_type: json_config
  - artifact_path: docs/commands/plan-schema.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-091
  requires:
    - PLAN-091-v5-framework-core
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-091-v5-framework-core.md
  - cli/lib/plan_validator.py
  - cli/ROLE_MAP.md
acceptance_criteria:
  - "schemas/plan-frontmatter-v2.schema.json が JSON Schema draft-07 形式で生成され、全 VALID_* enum を網羅している"
  - "plan_validator.py が jsonschema ライブラリで schema validation を実行し、既存 enum check と併用できる"
  - "helix plan new <plan-id> が --schema オプションで schema validation を実行し enum 違反を即時検出する"
  - "VS Code yaml extension (.vscode/settings.json の yaml.schemas 設定) で docs/plans/*.md を auto-complete できる"
  - "python3 -m py_compile cli/lib/plan_validator.py PASS"
  - "unit test 10 case (schema validation / IDE 設定 / helix plan new 統合 / backward 互換) 全 PASS"
  - "既存 PLAN 99 件が schema validation PASS (backward 互換保証)"
---

# PLAN-167: PLAN frontmatter schema v2 (V5 拡張 + JSON Schema 化)

## L2 凍結 (ADR snapshot)

既存 plan_validator.py (PLAN-091) の enum check を JSON Schema で形式化するため新規 L2 大局判断は発生しない。
PLAN-091 で凍結された enum 語彙 (VALID_KINDS / VALID_LAYERS / VALID_DRIVES / VALID_ARTIFACT_TYPES) を
JSON Schema に写す実装であり、ADR snapshot は不要。

## 背景

PLAN-091 (V5 framework core) で確立された PLAN frontmatter 語彙は `plan_validator.py` の Python 定数として管理されている。
この設計には 2 つの課題がある:

1. **IDE 補完なし**: YAML ファイル編集時に enum 違反が即時検出されず、plan_validator 実行まで気づかない
2. **schema 定義が分散**: enum 正本は plan_validator.py の `VALID_*` 定数、必須フィールドは `REQUIRED_FIELDS` タプル、
   role enum は cli/ROLE_MAP.md と複数箇所に散在しており、新フィールド追加時の整合維持コストが高い

JSON Schema (draft-07) 化により:
- VS Code yaml extension が `docs/plans/*.md` の frontmatter を auto-complete / inline validate
- plan_validator.py が schema file を single source of truth として参照
- `helix plan new` 起票時に enum 違反をコマンドライン上で即時検出

## WebSearch 履歴

JSON Schema draft-07 と VS Code yaml extension の設定方法について調査を要するため記録する。

- Query 1: "JSON Schema draft-07 YAML frontmatter validation VS Code yaml extension settings"
  → redhat.vscode-yaml が `yaml.schemas` で glob パターン指定可能、`fileMatch` に `docs/plans/PLAN-*.md` を指定
- Query 2: "jsonschema python library validate yaml frontmatter schema draft-07"
  → `jsonschema` パッケージの `validate(instance, schema)` が標準的実装、`$schema` フィールドで draft 指定
- Query 3: "JSON Schema enum array oneOf required properties YAML frontmatter best practice"
  → `required` 配列 + `properties` + `enum` の組み合わせが標準、`additionalProperties: false` で未知フィールドを warn 推奨

## 設計方針

### schema 構造

`schemas/plan-frontmatter-v2.schema.json` は以下を定義する:

```
$schema: http://json-schema.org/draft-07/schema#
$id: plan-frontmatter-v2
type: object
required: [plan_id, title, kind, layer, drive, status, agent_slots, generates, dependencies]
properties:
  plan_id:    { type: string, pattern: "^PLAN-..." }
  kind:       { type: string, enum: [design, impl, poc, ...] }
  layer:      { type: string, enum: [L0, L1, ..., cross] }
  drive:      { type: string, enum: [be, fe, fullstack, ...] }
  status:     { type: string }
  size:       { type: string, enum: [S, M, L] }
  agent_slots: { type: array, items: { required: [role, slot_label], ... } }
  generates:  { type: array, items: { required: [artifact_path, artifact_type], ... } }
  dependencies: { type: object, properties: { parent, requires, blocks } }
```

### plan_validator.py 統合

- `VALID_*` 定数は schema.json から動的に生成するか、schema.json と並存させて整合性 test で保証する
- `validate_with_schema(path, schema)` 関数を追加し、既存 `validate_plan(path)` の前段で実行
- `--strict` フラグで `additionalProperties: false` を有効化 (デフォルトは warn-only)

### VS Code 設定

`.vscode/settings.json` の `yaml.schemas` に以下を追加:

```json
{
  "yaml.schemas": {
    "./schemas/plan-frontmatter-v2.schema.json": "docs/plans/PLAN-*.md"
  }
}
```

redhat.vscode-yaml 拡張 (marketplace ID: redhat.vscode-yaml) が前提。

### helix plan new 統合

`helix plan new <plan-id> [--kind <kind>] [--layer <layer>]` に `--validate-schema` フラグを追加し、
template 生成直後に schema validation を実行して enum 違反を即時表示する。

## 実装計画

### Sprint .1: JSON Schema 定義 (Codex se、size S)

`schemas/plan-frontmatter-v2.schema.json` を新規作成。
plan_validator.py の `VALID_*` 定数 + `REQUIRED_FIELDS` を JSON Schema に写す。
`python3 -c "import json, jsonschema; ..."` で既存 PLAN 99 件に対してバリデーション実行し backward 互換確認。
schema validation 99 件 PASS が完了条件。

### Sprint .2: plan_validator.py 統合 (Codex se、size S)

`validate_with_schema()` 関数追加。`python3 -m py_compile` PASS。
unit test 7 case (schema PASS / enum 違反 / 必須 field 欠如 / role 違反 / artifact_type 違反 / backward 互換 / strict モード)。
`python3 -m pytest cli/lib/tests/test_plan_validator.py -q` PASS が完了条件。

### Sprint .3: VS Code 設定 + helix plan new 拡張 + docs (Codex docs、size S)

`.vscode/settings.json` 更新、`helix plan new` に `--validate-schema` フラグ追加。
docs/commands/plan-schema.md 起草 (schema 利用ガイド、VS Code セットアップ手順)。
bats test 3 case (helix plan new --validate-schema) + pmo-sonnet review が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/plan_validator.py` PASS
- [ ] unit test 10 case 全 PASS
- [ ] 既存 PLAN 99 件が schema validation PASS (backward 互換確認)
- [ ] `bash -n` で helix plan new 拡張箇所チェック PASS
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] schemas/plan-frontmatter-v2.schema.json 生成、JSON Schema draft-07 準拠
- [ ] plan_validator.py に schema validation 統合、既存 enum check と並存
- [ ] .vscode/settings.json の yaml.schemas 設定追加
- [ ] helix plan new --validate-schema で enum 違反即時検出
- [ ] unit test 10 case PASS
- [ ] 既存 PLAN 99 件 backward 互換 PASS
- [ ] docs/commands/plan-schema.md 起草完了

## carry / 学び

- `additionalProperties: false` は既存 PLAN が未知フィールドを持つ可能性があるため warn-only で導入し、
  fail-close 化は全件クリーン確認後に PLAN-091 carry として委ねる
- role enum は cli/ROLE_MAP.md を single source of truth とし、schema 生成時に動的読み込みを検討する
- jsonschema ライブラリが未インストール環境では plan_validator.py が graceful fallback する設計とする

## 関連 reference

- PLAN-091 (V5 framework core、enum 正本)
- cli/lib/plan_validator.py (既存実装)
- cli/ROLE_MAP.md (role enum 正本)
- https://json-schema.org/draft-07/schema (JSON Schema draft-07 仕様)
