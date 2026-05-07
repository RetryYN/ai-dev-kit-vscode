# ADR-014: cli/roles/*.conf を正本とする決定 (conf vs yaml 二重管理の整理)

## Status

Accepted (2026-05-08)

## Deciders

PM, TL

---

## Context

PLAN-024 以前に `cli/roles/<role>.conf` への role 定義の書き出しが、運用的に安定してきた。
`skill_recommender` / `effort_classifier` などの LLM 分類器系導入では、role ごとの `model` と `thinking` が
この conf を単位に設定される形になっている。

一方で同一情報は `cli/config/models.yaml` の `roles:` セクションにも並行して記述されている。
このため実体は `cli/roles/*.conf`、周知は `cli/config/models.yaml` という二系統管理になっている。

Sprint .1 の運用中、`cli/roles/research.conf` に対して `config/models.yaml` 側で変更が入る事故が発生した。
事故時には conf では `5.4`、yaml では `5.2-codex`、さらに `CLAUDE.md` 側では `5.2` という 3 重の不一致となり、実装動作と仕様ドキュメントが分岐した。

ADR-007（3モード統合）では `models.yaml` を周知用途、`conf` を実行用途として扱う前提が暗黙的に共有されていたが、文言の形式化は行われていなかった。
そのため、今回の事故は「正本をどちらに置くか」の合意不在に起因する、運用上の曖昧性が原因であると判断できる。

また、運用観点では `helix` の shell エントリ周辺は最小依存を保つ方針であり、起点読み込みを安定化する必要が高い。
本 ADR はこの意思決定を明文化し、今後の追加・追従ルールに反映することを目的とする。

## Decision

`cli/roles/<role>.conf` を権威ある **正本** として扱う。
この決定は、`helix-codex` が実行時に直接参照する実体が conf であり、shell ベースの起動系で YAML パーサを常時導入しない方針と整合するため採択する。

同時に、`cli/config/models.yaml` は以下の運用役割を維持する。

- 周知用カタログ（README/AGENTS/CLAUDE で共有する情報の一貫性担保）
- `helix doctor` が利用する整合チェックの基準ソース
- 変更差分の可視化・レビュー支援（差分レビュー前提）

`CLAUDE.md` と `AGENTS.md` の「モデル割当表」は **周知用途** であることを明記する。
conf の内容を唯一の実行判定として優先し、yaml/Markdown の記述は後追いで同期する。

以降、実体の不一致が発生した場合は conf を正として扱う。
`models.yaml` と `CLAUDE.md` / `AGENTS.md` の整合は運用とレビューで是正する前提とする。

## Consequences

1. conf 変更時は、Sprint .1 で実装された `helix doctor` が `models.yaml` との差分を検出して警告する。
   これにより、運用開始時点での誤設定混入を早期に止血できる。

2. `cli/config/models.yaml` を単独変更しても実行挙動は変わらない。
   役割側の運用では「yaml だけを書き換えたから動作が更新される」という期待をしないこととする。

3. 新規 role を追加する場合は以下を必須ルールとする。

   1. `cli/roles/<role>.conf` を先に作成し、`model` と `thinking` を確定
   2. `cli/config/models.yaml` に同内容で同期
   3. `helix doctor` を実行し、乖離がないことを確認

4. L3 の詳細設計レビュー時には、role 整合性を `doctor` ベースで fail-close 扱いに拡張検討する。
   Sprint .4 以降で運用導入を検討し、構成変更時のレビュー品質を改善する。

5. ADR 更新時には、既存 ADR / 設定ドキュメントを同時更新し、周知チャネルの更新漏れを最小化する。
   特に `cli/roles` 追加・削除時に、関連文脈（`docs/adr/index.md` 含む）への反映をルール化する。

## Alternatives considered

### A: yaml を正本にする（不採用）

- 利点: 設定情報が一元化される見た目
- 欠点: `helix-codex` の shell 起動系の最短経路が複雑化し、YAML パーサ導入による起動コスト増が見込まれる

### B: conf を廃止し yaml に一元化（不採用）

- 利点: 設定ファイル数は減る
- 欠点: `helix-codex` が yaml パース基盤を持つ必要が生じ、shim shell 系との互換性と起動安定性の懸念が増える

### C: conf 正本 + yaml 周知カタログ（採用）

- 利点: 実行ルートに寄せた正確性（conf）とドキュメント整合の可読性（yaml）を両立
- 欠点: 2 系統の定義を維持し、運用的に doctor 側の整合監査が必要になる

## Related

- ADR-007: three-mode integration
- PLAN-024 Sprint .1 retrospective（research.conf 乖離事故）
- PLAN-024 Sprint .3 spec (`.helix/tmp/plan-024-sprint3.md`)
- ADR-013: R4 専用ゲートの要否（運用整備のための補助的参照）

## References

- `cli/roles/*.conf`
- `cli/config/models.yaml`
- `cli/config/models.yaml`（`roles:` セクション）
- `helix doctor`（整合チェック）
- `cli/helix-codex`
