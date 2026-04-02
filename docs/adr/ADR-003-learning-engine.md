# ADR-003: Learning Engine Foundations

## Status
Accepted

## Context

ADR-001 で成果物駆動の正本を導入し、ADR-002 で Builder System の project-local 優先探索を定義した。次の課題は、実行で得られた成功パターンを構造化して再利用可能にし、プロジェクト横断で学習を蓄積・昇格できる運用基盤を整備することである。

現状はタスク実行ログが `helix.db` に記録されるのみで、成功パターンの再利用単位、重複排除、昇格条件、グローバル同期、将来の配布経路（リモート共有）が統一されていない。このままでは、成功知見がローカルに閉じ、Builder による再利用資産化まで接続できない。

Learning Engine では以下を同時に満たす必要がある。

- project-local / user-global / shared install / remote hub を一貫した探索順で扱えること
- 成功パターンを recipe として構造化し、`pattern_key` で重複排除できること
- N 回成功で昇格候補化し、Builder 生成につなげられること
- グローバル同期時に redaction を必須化し、秘密情報流出を防ぐこと
- 将来のリモートハブ（Git ベース）に拡張可能であること
- 日本語ファースト運用（説明・出力・ローカライズ）を維持すること

## Decision

Learning Engine の基盤決定として、以下を採用する。

### 1. Search Order を 4 層に拡張する

- 検索順序は `project-local → user-global → shared install → remote hub` とする
- `project-local` は `.helix/` 配下を優先する
- `user-global` は `~/.helix/`（`recipes/`, `global.db`）と `~/.claude/skills/` を対象とする
- `shared install` は `HELIX_HOME/` を対象とする
- `remote hub` は将来の Git ベース配布を想定したフォールバック層とする

これにより、プロジェクト文脈を最優先しつつ、個人蓄積、共有資産、外部配布へ段階的に拡張できる。

### 段階的実装

- v1（本リリース）: project-local + user-global の 2 層
- v2（将来）: shared install 層の追加
- v3（将来）: remote hub 層の追加

### 2. Recipe を成功パターンの構造化単位とする

- recipe は `pattern_key`, `steps`, `metrics`, `classification`, `security` を持つ `recipe.json` とする
- ローカル保存先は `.helix/recipes/`、グローバル保存先は `~/.helix/recipes/` とする
- `pattern_key` によりクロスプロジェクトで重複排除する
- notes（`why_it_worked`, `applicability`）は日本語で保持する

これにより、ログの生データを直接再利用するのではなく、再利用可能な学習アセットとして管理できる。

### 3. 昇格パイプラインを定義する

- 同一 `pattern_key` で N 回成功（デフォルト 3 回）を昇格候補条件とする
- 昇格先は Builder System で生成可能な `skill` / `script` / `task` / `sub-agent` を対象とする
- `promote` の自動処理は「候補提案」までとし、実際の生成は明示確認で実行する

これにより、学習の自動集約と、生成実行の安全性を両立する。

### 4. global.db を user-global の正本とする

- `~/.helix/global.db` に `recipe_index` と `promotion_records` を保持する
- ローカル `helix.db` からは成功レコードのみ同期する
- 同期前に redaction を必須化し、秘密情報を除去する

これにより、個人環境内での横断検索と昇格履歴の監査が可能になる。

### 5. リモートハブは v2 以降で導入する

- 配布基盤は Git リポジトリベースを採用し、既存 GitHub 権限モデルを活用する
- `registry.json` で recipe/asset のインデックスを管理する
- 品質メタデータとして `verified`, `use_count`, `success_rate` を保持する
- `~/.helix/config.yaml` によりマルチハブ対応を可能にする

これにより、ローカル中心運用を維持しつつ、将来の組織共有へ拡張できる。

### 6. 日本語ファーストを運用要件とする

- recipe notes（`why_it_worked`, `applicability`）は日本語を正とする
- CLI 出力とエラーメッセージは日本語を正とする
- 海外スキルをフォークする場合は日本語ローカライズを必須とする

これにより、運用現場での理解コストを下げ、暗黙知化を防ぐ。

## Consequences

### Positive

- 成功パターンが recipe として再利用可能になり、プロジェクト横断で知見を蓄積できる
- `pattern_key` 重複排除により、同型パターンの冗長保存を抑制できる
- 昇格候補の条件が明確化され、Builder 生成への接続が標準化される
- `global.db` により個人レベルの学習インデックスと昇格履歴を一元管理できる
- redaction 必須化により、同期時の機密情報漏えいリスクを下げられる
- 日本語ファーストで運用・レビュー・引継ぎの一貫性を維持できる

### Negative

- recipe 抽出・同期・昇格記録の追加により、CLI 実装と運用が複雑化する
- `pattern_key` 設計が不十分だと、過剰統合または過剰分割が発生する
- user-global を導入すると、ローカル差分の追跡責務が増える
- remote hub 導入までの間はローカル/グローバル運用に依存し、共有性に上限がある

### Risks

- redaction の漏れがあると機密情報が `global.db` / recipe に残存する
- 候補提案と生成実行の境界が曖昧だと意図しない生成が行われる
- `success_rate` / `quality_score` の定義が曖昧だと、昇格判定の信頼性が低下する
- マルチハブ導入時に registry 競合解決規則がないと同期不整合が発生する
