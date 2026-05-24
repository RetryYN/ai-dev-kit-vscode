# helix vmodel

## 概要

`helix vmodel` は、`cli/config/vmodel-semantics.yaml` に定義された V-model semantics を
CLI から参照・検証するためのコマンドです。

主な用途は次の 3 つです。

- drive / layer の全体把握 (`list`)
- 特定 drive / layer の semantics 参照 (`show`)
- YAML 契約の整合性検証 (`validate`)

## 書式

```text
helix vmodel list [--drive DRIVE] [--json]
helix vmodel show <drive> <layer> [--injection-only] [--json]
helix vmodel validate [--config PATH] [--json]
```

## 対象値

### drive

- `be`
- `fe`
- `db`
- `fullstack`

### layer

- `planning`
- `requirement`
- `architecture`
- `detailed`
- `functional`

## サブコマンド

### `list`

drive と layer の一覧を返します。

```text
helix vmodel list [--drive DRIVE] [--json]
```

- `--drive DRIVE` を付けない場合は drive 一覧と layer 一覧を返します
- `--drive DRIVE` を付けた場合は、その drive に対する layer 一覧を返します

例:

```bash
$ helix vmodel list
drives: be, fe, db, fullstack
layers: planning, requirement, architecture, detailed, functional
```

```bash
$ helix vmodel list --drive be
drive: be
layers: planning, requirement, architecture, detailed, functional
```

### `show`

指定した `drive` と `layer` の semantics を返します。

```text
helix vmodel show <drive> <layer> [--injection-only] [--json]
```

- 既定のテキスト出力は `design.*`, `test.*`, `pair.*` を表示します
- `--json` を付けると `design`, `test`, `pair`, `injection` を含む JSON を返します
- `--injection-only` を付けると `injection` ブロックだけを返します
- `--json` と `--injection-only` は併用できます

例:

```bash
$ helix vmodel show be planning
drive: be
layer: planning
design.review_unit: plan
test.test_level: operational
pair.vertical_to: requirement
```

```bash
$ helix vmodel show be planning --json
{
  "drive": "be",
  "layer": "planning",
  "design": { "...": "..." },
  "test": { "...": "..." },
  "pair": { "...": "..." },
  "injection": { "...": "..." }
}
```

```bash
$ helix vmodel show be architecture --injection-only
drive: be
layer: architecture
injection.owner_role: tl
injection.mandatory_agents: pmo-project-scout, pmo-project-explorer
injection.recommended_agents: tl-advisor
injection.recommended_skills: workflow/design-doc, workflow/api-contract, workflow/adversarial-review, workflow/threat-model, agent-skills/api-and-interface-design, agent-skills/system-design-sizing
injection.recommended_commands: helix gate, helix drift-check
injection.orchestration_mode: claude_judge_codex_impl
```

```bash
$ helix vmodel show be architecture --json --injection-only
{
  "drive": "be",
  "layer": "architecture",
  "injection": {
    "owner_role": "tl",
    "mandatory_agents": ["pmo-project-scout", "pmo-project-explorer"],
    "recommended_agents": ["tl-advisor"],
    "recommended_skills": ["workflow/design-doc", "..."],
    "recommended_commands": ["helix gate", "helix drift-check"],
    "orchestration_mode": "claude_judge_codex_impl"
  }
}
```

異常系:

- 不明な drive は `exit 2` で `unknown drive: <value>` を返します
- 不明な layer は `exit 2` で `unknown layer for drive <drive>: <value>` を返します

### `validate`

V-model YAML をロードし、正規化済み契約として妥当かを検証します。

```text
helix vmodel validate [--config PATH] [--json]
```

- `--config PATH` で検証対象 YAML を差し替えできます
- 成功時は `VALIDATION: OK` を返します
- 失敗時は `stderr` に詳細を出して `exit 1` で終了します

例:

```bash
$ helix vmodel validate
VALIDATION: OK
config_path: /path/to/cli/config/vmodel-semantics.yaml
drives: be, fe, db, fullstack
layers: planning, requirement, architecture, detailed, functional
```

## JSON 出力

主なキーは次のとおりです。

- `drive`
- `layer`
- `design`
- `test`
- `pair`
- `injection`

`--injection-only` 付きではトップレベルが `drive`, `layer`, `injection` のみになります。

## 実装連携

- エントリポイント: `cli/helix-vmodel`
- ローダ: `cli/lib/vmodel_loader.py`
- 主要型: `VModelSemantics`

`show` は `VModelSemantics.get_layer()` を使って全体を返し、
`--injection-only` 指定時は `VModelSemantics.get_layer_injection()` を使って
`injection` サブブロックのみを返します。

## 関連コマンド

- `helix commands check`
- `helix gate`
- `helix matrix`

## 注意

- `helix vmodel` は参照系コマンドです。設定変更自体は行いません
- 実装とドキュメントが矛盾した場合は `cli/helix-vmodel` と `cli/lib/vmodel_loader.py` を正とします
