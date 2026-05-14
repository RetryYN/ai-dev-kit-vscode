# helix vmodel

## 概要

`helix vmodel` は、V-model ドライバー/レイヤー/ペア（design/test/pair）という設計検証モデルを
CLI から可視化・参照・検証するためのコマンドです。

このコマンドは `docs/v2/B-design/vmodel-semantics-spine.yaml` を起点にした
`cli/config/vmodel-semantics.yaml` の実装モデルを元に、
`helix` の設計管理系コマンド（`gate` / `matrix` / `plan` / `asset`）へ接続されます。

主目的は次の3点です。

- V-model の全体俯瞰（`list`）
- 指定要素の詳細確認（`show`）
- ユーザー定義 YAML の整合性・妥当性検証（`validate`）

## 書式

```text
helix vmodel <subcommand> [--config PATH] [--json] [--drive DRIVE] [OPTIONS]
```

`helix vmodel` は `list`, `show`, `validate` の 3 サブコマンドのみを持ちます。

- 既定値は YAML ファイルとしては `cli/config/vmodel-semantics.yaml`
- 既定言語は日本語で、`--json` 指定時のみ機械可読 JSON を返却
- `--drive` 指定は `list` / `show` に限定

## 前提

- `cli/config/vmodel-semantics.yaml` が存在し、読み取り可能であること。
- `yaml` の schema は `schema_version: 1`。
- 実体の正本は実装 (`cli/lib/vmodel_loader.py`) を参照。

参照: `docs/commands/asset.md`, `docs/commands/matrix.md`, `docs/commands/plan.md`

## 共通オプション

| オプション | 説明 |
| --- | --- |
| `--config PATH` | 参照する vmodel 設定 YAML を上書き。既定は `cli/config/vmodel-semantics.yaml` |
| `--json` | 出力を JSON 形式化（`validate` は構造エラーがある場合も JSON を返却） |
| `--drive DRIVE` | `list`/`show` 対象のドライブを絞り込み。`be` / `fe` / `db` / `fullstack` |

`show` は `--drive` 指定なしでも実行できますが、同名キー衝突がある場合に
`verdict: ambiguous` で停止するため、通常は指定推奨です。

## サブコマンド

### `list`

V-model 全体を要約形式で表示します。

```text
helix vmodel list [--drive DRIVE] [--json] [--config PATH]
```

#### 機能

- 指定ドライブの全レイヤー（planning / requirement / architecture / detailed / functional）一覧
- 各レイヤー内の design / test / pair の有無
- `schema_version`, `lifecycle` の要約

#### 実行例

```bash
$ helix vmodel list
V-model semantic map
  schema_version: 1
  spine drives: be, fe, db, fullstack

  - be
    - planning
    - requirement
    - architecture
    - detailed
    - functional
      design:
        - design_entry
      test:
        - test_entry
      pair:
        - design_test_pair

  - fe
    - planning
    - requirement
    - architecture
    - detailed
    - functional
      ...
```

JSON 版:

```bash
$ helix vmodel list --json
{"schema_version":1,"spine":["be","fe","db","fullstack"],"drives":{...}}
```

#### 想定利用導線

1. 全体把握（`list`）で対象ドライブを確認。
2. 問題が疑われる layer を `show` で深掘り。
3. `validate` 実行で config を先に検証。

### `show`

特定のドライブ/レイヤー/構成の詳細を表示します。

```text
helix vmodel show <item-key> [--drive DRIVE] [--json] [--config PATH]
```

`item-key` は次から指定します。

- `drives`
- `<drive>/<layer>`（例: `be/architecture`）
- `drive/<drive>/design` / `drive/<drive>/test` / `drive/<drive>/pair`
- `drive/<drive>/design/<key>` など、実装内で利用されるエントリキー（例: `be/functional/design/validation`）

#### 実行例

```bash
$ helix vmodel show be/functional/pair/design_validation_pair --drive be
Item: be/functional/pair/design_validation_pair
Drive: be
Layer: functional
Type: pair

horizontal_rule: true
vertical_from: architecture
vertical_to: detailed
score_weight: 1.0
promotion:
  to:
    - pair_test_design
    - pair_test_coverage

checks:
  - entry: architecture
    ok: true
  - entry: detailed
    ok: true
```

JSON 版:

```bash
$ helix vmodel show be/functional/design/acceptance --drive be --json
{"drive":"be","layer":"functional","type":"design","key":"acceptance","...":"..."}
```

### `validate`

V-model YAML を構文・参照整合で検証します。`helix vmodel` の最初に実行推奨。

```text
helix vmodel validate [--config PATH]
```

#### 検証項目（実装準拠）

- `schema_version` が `1`
- `spine.drives` が定義済みかつ 4 ドライブの重複なし
- `lifecycle` で必要状態が定義されているか
- 各 drive / layer の 3 sibling（`design`, `test`, `pair`）存在
- pair の必須フィールド
  - `horizontal_rule`
  - `vertical_from`
  - `vertical_to`
  - `score_weight`
  - `promotion`

#### 実行例

```bash
$ helix vmodel validate
Validating vmodel semantics: cli/config/vmodel-semantics.yaml
Result: passed
schema_version: 1
spine drives: [be, fe, db, fullstack]
lifecycle: [mock_to_implementation]
entries: 128
pairs: 64
```

失敗例:

```bash
$ helix vmodel validate
Validating vmodel semantics: cli/config/vmodel-semantics.yaml
Result: failed
error: pair entry 'be/functional/pair/foo' missing required field 'promotion'
```

`--json` 時:

```bash
$ helix vmodel validate --json
{"verdict":"failed","errors":["pair entry ... missing required field"]}
```

## 出力の意味

### `Result` と `verdict`

`list` / `show` は表示中心、`validate` のみ `Result/verdict` の明確な合否を返します。

- `passed`: 形式と参照整合が正しい。
- `failed`: YAML 自体のパース or 必須条件不満足。
- `missing`: 該当キーが見つからない/不明。

### `--json` 時の主なキー

- `schema_version`: schema 定義番号
- `spine`: drive 定義配列
- `lifecycle`: 運用状態配列
- `drives`: ドライブ別の構造木

## 関連コマンド

- `helix gate --subgate functional_freeze` は本コマンドの semantics を参照し、
  drive/レイヤー条件を評価します。
- `helix matrix` は vmodel ベースの検証結果を集約するための上位導線です。
- `helix plan` はドライブ別進捗設計の管理に、`helix asset` は監査ログ連携に向きます。

## 代表的な導線（典型フロー）

```text
helix vmodel validate
└─ まず実装整合を確認

helix vmodel list
└─ 対象 drive と layer を特定

helix vmodel show <item>
└─ 期待エントリの構造と score ルールを確認

helix gate --subgate functional_freeze --drive <drive>
└─ 実案件での機能フリーズ判定へ接続
```

## 入力ファイル設計との接続

`vmodel` の入力ファイルは既定で
`cli/config/vmodel-semantics.yaml` を使います。
設計的背景や原型は
`docs/v2/B-design/vmodel-semantics-spine.yaml`
の spine 定義に遡ります。

`drives` は 4 種（`be`, `fe`, `db`, `fullstack`）で、
`layers` は 5 層（`planning`, `requirement`, `architecture`, `detailed`, `functional`）。

## CLI API 実装連携

実装は `cli/helix-vmodel` から起動され、
内部ローダは `cli/lib/vmodel_loader.py` の `VModelLoader` を通じます。

### ローダ API の主な関心

- YAML をパースして `schema_version` を検証
- spine / layer / lifecycle を正規化
- `drives` と layer の参照整合チェック
- `pair` の `promotion` / `horizontal_rule` などの必須キー検証

## 典型エラーと対処

| エラー | 原因 | 対処 |
| --- | --- | --- |
| `schema version mismatch` | `schema_version` が想定値でない | `schema_version: 1` に統一 |
| `missing pair field` | `horizontal_rule` 等不足 | 対象 pair へキー追加 |
| `unknown drive` | `--drive` と定義ドライブ不一致 | `be|fe|db|fullstack` を使用 |
| `ambiguous show key` | 重複キーを短縮指定 | 完全キーへ拡張 |

## FAQ

### Q1. JSON 出力は必ず英語？

A1. はい、JSON は固定キーに寄るため言語非依存で扱いやすい形式を保持します。

### Q2. `validate` で失敗したが `list` は表示できる？

A2. 一部条件の欠落は一覧表示が可能ですが、`validate` は `pair` の厳密検証も行うため失敗し得ます。

### Q3. `--drive` なしで `show` が重複して見つからない

A3. 同一キーを複数 drive が持つ場合は `ambiguous` になります。`
--drive` を指定して明示してください。

## 利用上の注意

- `helix vmodel` は vmodel セマンティクスの参照系であり、
  設計状態の更新・反映は `plan` 系コマンドや DB への記録で行ってください。
- `validate` は保存前セルフチェックに使い、CI では `--json` 判定を推奨します。
- `fullstack` や `functional` などの導線は `subgate functional_freeze` へ直接影響します。

## 変更履歴

本書は実装に追随して更新します。

- v1.0: 初版（HELIX V2 Phase2）

