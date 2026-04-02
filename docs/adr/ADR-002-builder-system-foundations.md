# ADR-002: Builder System Foundations

## Status
Accepted

## Context

現状の HELIX CLI は、`task-catalog.yaml`、`action-types.yaml`、`SKILL.md` の解決先を主に `HELIX_HOME` 配下へ固定している。結果として、Builder がプロジェクト内に生成したタスク定義やスキルを置いても、実行時に参照されず、生成物が実質的に無効化される。

特に、タスクカタログとアクション型は `HELIX_HOME/cli/templates/` を直接参照し、`helix-codex` のスキル解決も `HELIX_HOME/skills/` 固定である。この構造は共有インストールの再利用には有利だが、プロジェクトごとの差分適用、ローカル実験、生成物のシャドウ、CI 上での自己完結性を阻害する。

Builder 導入後は、HELIX 本体が提供する shared install と、プロジェクトが独自に保持する overlay/generated asset を同時に扱う必要がある。ここで探索順序が機能ごとに異なると、同じ名前のタスクやスキルが文脈ごとに別解決され、運用が不安定になる。そのため、project-local を優先し、shared install をフォールバックにする一貫した探索規約が必要である。

あわせて、Builder 自身の内部定義形式も見直す。現行の `yaml_parser.py` は軽量な YAML 読み取りには十分だが、Builder が扱う artifact manifest や pipeline/workflow/loop のような list-heavy かつ deeply nested な構造には不向きである。内部表現まで YAML に寄せると、パーサの複雑化、曖昧な構文差、実装依存の吸収が必要になる。一方で、人間が直接保守する設定や、既存 CLI と互換を維持すべき出力形式では YAML の可読性が依然として有用である。

## Decision

Builder System の基盤決定として、以下を採用する。

### 1. Project Overlay Search Order

- 検索順序は `project-local → shared install` に統一する
- `task-catalog` は `.helix/task-catalog.yaml` を第1候補、`HELIX_HOME/cli/templates/task-catalog.yaml` をフォールバックとする
- `action-types` は `.helix/action-types.yaml` を第1候補、`HELIX_HOME/cli/templates/action-types.yaml` をフォールバックとする
- `skills` はプロジェクトローカル生成物を shared install より優先する
- merge 戦略は「project-local 優先」とし、同一キーの衝突時は project-local が勝つ
- project-local に存在しない項目のみ shared install から補完する

これにより、Builder が生成した overlay をプロジェクト単位で有効化しつつ、共通インストールを安全な既定値として再利用する。

### 2. Skill Search Order

- Builder が生成するスキルの配置先は `PROJECT_ROOT/skills/generated/<name>/SKILL.md` とする
- スキル解決順は `PROJECT_ROOT/skills/generated/ → PROJECT_ROOT/skills/ → HELIX_HOME/skills/` とする
- `helix-codex` の role prompt 組み立て時は、この順序で `SKILL.md` を探索する
- 名前衝突時は、より local な候補を採用する
- この衝突解決は「上書き」ではなく「シャドウ」として扱い、元の shared skill は保持したまま参照順位のみで切り替える

これにより、Builder 生成スキル、プロジェクト固有スキル、共有スキルの責務を分離しながら、実行時には最も文脈に近い定義を採用できる。

### 3. Builder-Native Format = JSON

- Builder の内部定義ファイルは JSON を正とする
- 対象は artifact manifest、pipeline 定義、workflow 定義、loop 定義など、Builder が機械処理する中間表現全般とする
- 採用理由は、`yaml_parser.py` が list-heavy / nested YAML の安定処理に不向きであり、JSON であれば標準ライブラリで厳密かつ一貫して扱えるためである
- 人間が手動編集する必要がある設定は YAML を維持する
- 具体的には `matrix.yaml`、`rules/*.yaml`、Builder 出力としての task-catalog overlay は YAML のままとする
- `SKILL.md` や `verify/*.sh` のように最終成果物が Markdown / Shell であるものは、その最終形式を維持する

これにより、Builder 内部では機械可読性と実装容易性を優先し、外部公開面では既存運用との互換性と人間可読性を維持する。

## Consequences

### Positive

- Builder が生成した project-local overlay と skill が、共有インストールを変更せずに即時有効になる
- 探索順序が統一されるため、タスク、アクション型、スキルで解決規則がずれる問題を避けられる
- skill のシャドウ規則により、共有資産を壊さずにプロジェクト単位の差し替えや実験ができる
- Builder 内部を JSON に統一することで、Python 標準ライブラリのみで安定実装しやすくなり、YAML 特有の曖昧さを減らせる
- 人間編集が前提の設定だけ YAML を残すため、運用者の可読性と既存フォーマット互換を保てる

### Negative

- 同名の task/skill/action-type が複数階層に存在すると、どれが採用されたかを利用者が把握しづらくなる
- project-local 優先は柔軟だが、shared install 側の更新が見えにくくなり、意図せぬシャドウが長期化する可能性がある
- 内部 JSON と外部 YAML/Markdown/Shell が混在するため、Builder 実装者は形式変換責務を明示的に管理する必要がある
- 既存の検証スクリプト、デバッグツール、ラッパー CLI はグローバル固定参照を前提としているため、追随改修が必要になる

### Risks

- 解決結果の provenance を CLI が表示しない場合、誤った overlay や shadow が有効でも原因追跡が難しい
- merge 規則をキー単位で厳密定義しないと、task-catalog や action-types の部分 overlay が不完全結合になり、静かに欠落や競合を起こす
- `helix-codex` だけが新しい探索順序に対応し、周辺 CLI や verify が追随しない場合、設計と実装の間で不整合が残る
- Builder 内部 JSON と外部 YAML の変換境界にバリデーションが不足すると、生成時は成功しても実行時に不整合が顕在化する
