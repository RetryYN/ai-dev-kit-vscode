# ADR-006: テンプレートコピーアーキテクチャ

> Status: Accepted
> Date: 2026-04-05
> Deciders: PM, TL

---

## Context

HELIX CLI はプロジェクト初期化時に複数の設定ファイル・状態ファイル・ルール定義を `.helix/` ディレクトリに配置する必要がある。これらのファイルは:

- 初期値が定まっている（phase.yaml の `current_phase: L1`, gates の各 status: pending 等）
- プロジェクトごとにカスタマイズされる（config.yaml の gate_skip, default_drive 等）
- フレームワーク更新時に新しいテンプレートが追加される可能性がある

テンプレートの管理方式として、コピー方式、参照方式（シンボリックリンク）、コード生成方式の選択肢がある。

---

## Decision

**`helix init` 実行時にテンプレートファイルを `.helix/` にコピー（cp）する方式** を採用する。

### テンプレート -> ランタイム対応表

| テンプレート (`cli/templates/`) | ランタイム (`.helix/`) | コピー方式 |
|-------------------------------|----------------------|-----------|
| `phase.yaml` | `phase.yaml` | cp（直接コピー） |
| `matrix.yaml` | `matrix.yaml` | cp |
| `gate-checks.yaml` | `gate-checks.yaml` | cp |
| `config.yaml` | `config.yaml` | cp |
| `doc-map.yaml` | `doc-map.yaml` | cp |
| `state-machine.yaml` | `state-machine.yaml` | cp |
| `rules/*.yaml` | `rules/*.yaml` | cp（ディレクトリごと） |
| `task-catalog.yaml` | — | 参照（helix-task が直接読む） |
| `action-types.yaml` | — | 参照（helix-task が直接読む） |
| `teams/*.yaml` | — | 参照（helix-team が直接読む） |
| `agents/*.md` | — | 参照（helix-codex が直接読む） |
| `CLAUDE.md.template` | プロジェクト直下の `CLAUDE.md` | テンプレート展開 |
| `pre-commit-hook` | `.git/hooks/pre-commit` | cp + chmod +x |
| `commit-msg-hook` | `.git/hooks/commit-msg` | cp + chmod +x |
| `post-merge-hook` | `.git/hooks/post-merge` | cp + chmod +x |

### 派生生成（matrix_compiler.py）

コピー後、`matrix_compiler.py` がランタイムファイルから派生ファイルを生成する:

```
.helix/matrix.yaml
  |--[compile]--->      .helix/runtime/index.json       全成果物カタログ
  |--[auto-detect]--->  .helix/state/deliverables.json  各成果物の状態
  |--[gate_check_generator]--->  .helix/gate-checks.yaml (更新)
  |--[gate_check_generator]--->  .helix/doc-map.yaml (更新)
```

---

## Alternatives

### A1: シンボリックリンク方式

- 利点: テンプレート更新が即座にランタイムに反映
- 欠点: プロジェクトごとのカスタマイズができない。`.helix/phase.yaml` を書き換えるとテンプレート自体が変わってしまう。git で追跡した場合にシンボリックリンクの扱いが複雑

### A2: コード生成方式（Python で動的生成）

- 利点: 条件分岐（駆動タイプ別、サイズ別）で初期値を動的に変えられる
- 欠点: テンプレートの可読性が低下。「最終的にどんなファイルが生成されるか」が分かりにくい。デバッグが困難

### A3: テンプレートエンジン方式（Jinja2 等）

- 利点: 変数展開、条件分岐、ループが可能
- 欠点: 外部依存（Jinja2）が増える。HELIX の YAML テンプレートは単純な構造であり、テンプレートエンジンはオーバースペック

### A4: overlay 方式（base + project diff）

- 利点: テンプレート更新時に差分マージが可能
- 欠点: マージコンフリクトの解決が複雑。実装コストが高い

---

## Consequences

### 正の影響

- **単純性**: `cp` は最も単純なファイル配置方式。理解・デバッグが容易
- **独立性**: コピー後のファイルはプロジェクト固有。テンプレートの変更がランタイムに影響しない
- **可読性**: `.helix/` 内のファイルをそのまま読めば現在の設定が分かる
- **git 管理**: `.helix/phase.yaml` 等を git 管理することでフェーズ進行の履歴を残せる
- **カスタマイズ**: コピー後に自由に編集可能（config.yaml の gate_skip 等）

### 負の影響

- **テンプレート更新の非伝播**: フレームワーク更新で `cli/templates/phase.yaml` が変わっても、既存プロジェクトの `.helix/phase.yaml` には反映されない
- **ファイル数の増加**: プロジェクトごとに同じ構造のファイルが複製される
- **初期化の冪等性**: `helix init` の再実行時に既存ファイルを上書きするかどうかの判断が必要

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| テンプレート更新の非伝播 | `helix doctor` でテンプレートとの差分検出を提供。手動更新をガイド |
| 初期化の冪等性 | `helix init` は既存ファイルがある場合スキップ。`--force` で上書き |
| schema_validator.py との整合性 | JSON Schema (`cli/schemas/`) でランタイムファイルの構造を検証。テンプレート変更時は Schema も更新 |
| 空ファイル問題 | `deliverable_gate.py` が 10 バイト未満のファイルを空として検出。形式的なコピーだけでは通過しない |

---

## 補足: JSON Schema による構造検証

テンプレートコピー後のランタイムファイルは、以下の JSON Schema で構造検証される:

| スキーマ | 対象 |
|---------|------|
| `cli/schemas/phase.schema.json` | `.helix/phase.yaml` |
| `cli/schemas/matrix.schema.json` | `.helix/matrix.yaml` |
| `cli/schemas/gate-checks.schema.json` | `.helix/gate-checks.yaml` |
| `cli/schemas/doc-map.schema.json` | `.helix/doc-map.yaml` |
| `cli/schemas/review-output.schema.json` | レビュー出力 |

`schema_validator.py` が `helix gate` 実行時等に自動検証する。テンプレートとスキーマの整合性はフレームワーク側のテスト（`helix test`）で保証する。

---

## References

- `cli/helix-init` (初期化コマンド)
- `cli/templates/` (テンプレートディレクトリ)
- `cli/schemas/` (JSON Schema ディレクトリ)
- `cli/lib/schema_validator.py` (スキーマ検証)
- `cli/lib/matrix_compiler.py` (派生生成)
- `cli/lib/deliverable_gate.py` (空ファイル検出)
