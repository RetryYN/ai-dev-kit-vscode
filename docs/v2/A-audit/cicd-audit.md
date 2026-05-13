# FR-INV14: CI/CD / 自動実行 capability 監査

最終更新: 2026-05-14

## 概要

本監査は、現行 repo に存在する CI/CD と自動実行の実装を `Git hooks / Claude Code hooks / GitHub Actions / scheduler / cleanup / manual trigger / failure handling / cost` の観点で棚卸しし、V2 Phase 5 自動化の入力にするものです。

結論は次のとおりです。

- 現状の強みは `PreToolUse` 系の fail-close ガード、`commit-msg` / `pre-commit` テンプレート、`GitHub Actions CI` の基本検証線です。
- 一方で `schedule/cron` は **基盤実装はあるが実運用はほぼ未接続** です。
- `helix sync`、`SessionStart auto-sync`、`PostToolUse auto-record`、`Gate auto-detect` は **仕様・PLAN はあるが統合導線が未完** です。
- ローカル `.git/hooks` は `commit-msg` と `post-merge` はある一方、`pre-commit` は実インストールされておらず、配布テンプレート先行です。
- CI cost / Codex API consumption は **ローカル budget/cost_log 基盤はあるが、GitHub Actions と一体化した可視化はない** 状態です。

## 選択肢

### Option A: 現状維持

- メリット: 追加作業が最小。
- デメリット: automation の入口が `hooks / CLI / workflow / planned-only spec` に分散したままで、V2 Phase 5 の統合起点にならない。
- 推奨度: 低。

### Option B: 既存 hook/CI を温存しつつ、`helix sync` と scheduler を統合入口に昇格

- メリット: 既存の guard を壊さず、`SessionStart / PostToolUse / Gate / sync / scheduler` を一本化しやすい。
- デメリット: Phase 5 で command layer の再配線が必要。
- 推奨度: 高。

### Option C: GitHub Actions 中心に寄せ、ローカル hook を軽量化

- メリット: ローカル差異を減らせる。
- デメリット: HELIX の即時 guard が弱まり、修正ループが PR 後ろ倒しになる。
- 推奨度: 中。

## 推奨

**Option B** を推奨します。

理由:

1. 既に最も価値が出ているのは `PreToolUse` の fail-close と `pre-commit` の secret / drift / lint ガードで、これを消す理由がない。
2. `PLAN-067` と `docs/v2/CONCEPT.md` は `helix sync` を自動化の統合入口とする前提で揃っているが、実装が未追従である。
3. `scheduler`、`budget`、`cost_log`、`skill/code recommender TTL` などの基盤は部分的に存在するため、全面作り直しより接続不足の解消が合理的。

## 監査表

注記:

- `状態` は `稼働中 / 仕組み倒れ / 廃止候補` の 3 値で評価した。
- `fail-close 度` は `strict / loose / 不在` で評価した。
- `V2 Phase` は本監査用途の整理で、概ね `Phase 1=棚卸し`, `Phase 2=正本化`, `Phase 3=検出強化`, `Phase 4=統合`, `Phase 5=自動化` として割り当てた。
- `推定` はコード上の直接証跡は弱いが、周辺 docs/PLAN からそう読むのが妥当な項目。

| 項目 | path | trigger | 目的 | 状態 | fail-close 度 | V2 変更計画 | V2 Phase 紐付け |
|---|---|---|---|---|---|---|---|
| Claude SessionStart 登録 | `.claude/settings.json` | `SessionStart` | HELIX context を注入する | 稼働中 | strict | extend | Phase 4-5 |
| Claude PreToolUse Write | `.claude/settings.json` | `PreToolUse: Write` | `CLAUDE.md` テンプレ逸脱を防ぐ | 稼働中 | strict | modify | Phase 2-3 |
| Claude PreToolUse Bash | `.claude/settings.json` | `PreToolUse: Bash` | raw LLM CLI 実行をガードする | 稼働中 | strict | as-is | Phase 3 |
| Claude PreToolUse WebSearch/WebFetch | `.claude/settings.json` | `PreToolUse: WebSearch|WebFetch` | research tool 利用を role 境界で制御する | 稼働中 | strict | extend | Phase 3-5 |
| Claude PreToolUse repo edit block | `.claude/settings.json` | `PreToolUse: Edit|Write|MultiEdit` | Opus の repo 直接編集を遮断する | 稼働中 | strict | as-is | Phase 2-3 |
| Claude PostToolUse 登録 | `.claude/settings.json` | `PostToolUse: Edit|Write|MultiEdit` | 編集後の設計同期チェックを起動する | 稼働中 | strict | extend | Phase 4-5 |
| Claude Stop 登録 | `.claude/settings.json` | `Stop` | 終了時 accounting を記録する | 稼働中 | loose | modify | Phase 4-5 |
| SessionStart 実体 | `cli/libexec/helix-session-start` | `SessionStart` | setup check、progress 生成、skill hint 注入、session insert を行う | 稼働中 | loose | extend | Phase 4-5 |
| SessionStart wrapper | `cli/helix-session-start` | `SessionStart` | 旧 entrypoint 互換を維持する | 稼働中 | 不在 | deprecate | Phase 2 |
| CLAUDE.md check wrapper | `cli/libexec/helix-check-claudemd` | `PreToolUse: Write` | Write 前に `CLAUDE.md` 作成規約を検証する | 稼働中 | strict | as-is | Phase 3 |
| Bash guard 実体 | `cli/libexec/helix-pre-bash` | `PreToolUse: Bash` | harness 逸脱コマンドを止める | 稼働中 | strict | as-is | Phase 3 |
| Research guard 実体 | `cli/libexec/helix-pre-research` | `PreToolUse: WebSearch|WebFetch` | research role 外の検索を止める | 稼働中 | strict | extend | Phase 3-5 |
| Opus repo block 実体 | `.claude/hooks/pretooluse-opus-repo-block.sh` | `PreToolUse: Edit|Write|MultiEdit` | repo 編集を block し、必要時 audit log を出す | 稼働中 | strict | as-is | Phase 2-3 |
| PostToolUse wrapper | `cli/libexec/helix-post-tool-use` | `PostToolUse` | payload から changed path を抽出し `helix-hook` に渡す | 稼働中 | strict | extend | Phase 4-5 |
| PostToolUse telemetry | `.claude/hooks/post-tool-use.sh` | `PostToolUse` | invocation telemetry を `helix.db` に記録する | 稼働中 | loose | extend | Phase 4-5 |
| Stop telemetry | `.claude/hooks/stop.sh` | `Stop` | Stop invocation telemetry を `helix.db` に記録する | 稼働中 | loose | extend | Phase 4-5 |
| Session summary accounting | `cli/helix-session-summary` | `Stop` | `cost_log` に session 終了行を insert する | 稼働中 | loose | modify | Phase 4-5 |
| Git pre-commit template | `cli/templates/hooks/pre-commit` | `git pre-commit` | secret scan / drift-check / skip annotation lint を行う | 稼働中 | strict | extend | Phase 3-5 |
| Git commit-msg template | `cli/templates/hooks/commit-msg` | `git commit-msg` | Conventional Commits を強制する | 稼働中 | strict | as-is | Phase 2 |
| Git post-merge template | `cli/templates/hooks/post-merge` | `git post-merge` | merge 後に matrix compile / auto-detect を走らせる | 稼働中 | loose | modify | Phase 4 |
| Local commit-msg hook | `.git/hooks/commit-msg` | `git commit-msg` | ローカル commit message を強制する | 稼働中 | strict | as-is | Phase 2 |
| Local post-merge hook | `.git/hooks/post-merge` | `git post-merge` | ローカル merge 後に matrix 再コンパイルする | 稼働中 | loose | modify | Phase 4 |
| Local pre-commit backup | `.git/hooks/pre-commit.helix.bak` | 手動復旧時のみ | 旧 pre-commit の予約枠 | 仕組み倒れ | 不在 | deprecate | Phase 2 |
| GitHub Actions CI | `.github/workflows/ci.yml` | `push main`, `pull_request main` | test / bats / verify / pytest を実行する | 稼働中 | strict | extend | Phase 3-5 |
| PR changed-design detect | `.github/workflows/ci.yml` | `pull_request` 条件分岐 | 変更された D-API/D-CONTRACT/D-DB を検出する | 稼働中 | loose | extend | Phase 3-4 |
| PR drift-check step | `.github/workflows/ci.yml` | `pull_request && design change` | design 変更時に drift-check を advisory 実行する | 稼働中 | loose | modify | Phase 3-4 |
| `helix test` manual trigger | `cli/helix-test` | 手動 CLI | bats / pytest / wrapper smoke を横断実行する | 稼働中 | strict | as-is | Phase 3-4 |
| `helix gate` manual trigger | `cli/helix-gate` | 手動 CLI | gate ごとの静的/AI 検証を行う | 稼働中 | strict | as-is | Phase 3-4 |
| `helix review --uncommitted` 運用 | `.claude/commands/sdd-review.md` | 手動 CLI 運用 | 差分レビュー工程を起動する | 稼働中 | 不在 | extend | Phase 3-4 |
| `helix sync` 統合入口 | `docs/features/PLAN-067/D-API/helix-sync.md` | 想定: 手動/自動 | 各 sync を 1 入口に統合する | 仕組み倒れ | 不在 | new | Phase 5 |
| Scheduler CLI | `cli/helix-scheduler` | 手動 CLI / 将来自動 | DB-backed schedule を登録・実行する | 仕組み倒れ | loose | extend | Phase 5 |
| Scheduler stale requeue | `cli/lib/scheduler_helper.py` | `run-due` 前処理 | stale running schedule を pending に戻す | 稼働中 | loose | extend | Phase 5 |
| stale lock cleanup | `cli/lib/concurrent_lock.py` | 手動 CLI (`helix doctor`) | dead PID lock を cleanup する | 稼働中 | loose | as-is | Phase 4 |
| bats tmp cleanup audit | `cli/helix-bats-cleanup` | 手動 CLI / `helix test` 後 | `/tmp/bats-*` を列挙/削除する | 稼働中 | loose | extend | Phase 4-5 |
| `helix test` post-run cleanup check | `cli/helix-test` | `helix test` 完了後 | bats cleanup 候補を警告する | 稼働中 | loose | modify | Phase 4-5 |
| recommender TTL cache GC | `cli/lib/skill_recommender.py` | recommender 実行時 | 期限切れ cache を自動削除する | 稼働中 | loose | as-is | Phase 4 |
| code recommender TTL cache GC | `cli/lib/code_recommender.py` | code find 実行時 | 期限切れ code cache を自動削除する | 稼働中 | loose | as-is | Phase 4 |
| classifier/recommender TTL default | `cli/lib/defaults_loader.py` | config 読み込み時 | 3600s TTL を共通設定する | 稼働中 | 不在 | as-is | Phase 4 |
| budget cache | `cli/lib/budget.py` | `helix-budget` 実行時 | cost snapshot を cache する | 稼働中 | loose | extend | Phase 4-5 |
| Claude cost source | `cli/lib/budget.py` | 手動 CLI | `ccusage` / jsonl fallback から Claude 消費を読む | 稼働中 | loose | modify | Phase 5 |
| Codex cost source | `cli/lib/budget.py` | 手動 CLI | `~/.codex/state.db` から Codex 消費を読む | 稼働中 | loose | modify | Phase 5 |

## 評価メモ

### 1. Git hooks

- template 側の `pre-commit` は最も中身が厚く、secret scan は fail-close、skip annotation lint も fail-close。
- ただし drift-check は `WARN` に留めて commit 継続であり、ここは strict ではなく loose。
- local `.git/hooks` には `pre-commit` 本体がなく、`.git/hooks/pre-commit.helix.bak` が `exit 0` の予約ファイルとして残る。つまり **配布テンプレートはあるが、この clone では pre-commit enforce が有効化されていない**。

### 2. Claude Code hooks

- `PreToolUse` は最も堅く、Bash / WebSearch / repo edit block で `blockOnFailure=true` が掛かっている。
- `SessionStart` は設定上 strict だが、実体は setup/progress/skill hint 生成の失敗を極力握りつぶすため、**体験優先の fail-open 実装** に寄っている。
- `Stop` は設定・実装の両方で loose。accounting を落としても session 終了は止めない。

### 3. GitHub Actions

- workflow は `ci.yml` の 1 本のみで、schedule/cron は未定義。
- main push と PR に対して `helix-test`、Bats、`helix-verify-all`、条件付き pytest が走るため、基本線はある。
- PR drift-check は `|| true` で advisory なので fail-close ではない。
- GitHub Actions minutes の収集や閾値監視は見当たらない。

### 4. scheduled / cron / cleanup

- cron 実行基盤は `cli/helix-scheduler` と `cli/lib/scheduler_helper.py` にあるが、repo から自動起動される導線は確認できなかった。
- stale running schedule の requeue、stale lock cleanup、TTL cache GC は個別には存在する。
- ただし **定期実行を束ねる orchestrator は未接続** で、実態としては「自動 cleanup」より「手動保守補助」に近い。

### 5. manual trigger

- `helix test` と `helix gate` は実体があり、運用上の中心 command になっている。
- `helix sync` は docs/PLAN 上は重要だが、実装コマンドは見つからなかった。
- `helix review --uncommitted` は docs 上の運用導線として存在するが、この監査では実体コマンドの中身までは未追跡。

### 6. failure handling

- strict: `PreToolUse` guard、`commit-msg`、secret scan、skip annotation lint、CI の主要 test step。
- loose: `SessionStart` 内部処理、`Stop`、`post-merge` matrix recompile、PR drift-check advisory、cleanup 系。
- 不在: `helix sync`、未配備の local pre-commit、GitHub Actions cost guard。

### 7. CI cost

- GitHub Actions minutes の計測や budget gate は repo 内で未確認。
- Claude 消費は `ccusage` / jsonl fallback、Codex 消費は `~/.codex/state.db` 参照ロジックがある。
- `cost_log` テーブルと `session-summary` insert はあるが、**workflow minutes + local LLM cost を 1 画面で見る仕組みはまだない**。

## 機能していない / 弱い一覧

- `helix sync` は D-API / PLAN はあるが、実コマンド未実装。
- local `.git/hooks/pre-commit` が存在せず、配布テンプレートの enforce がこの clone では有効でない。
- `.git/hooks/pre-commit.helix.bak` は `exit 0` の予約ファイルで実機能なし。
- GitHub Actions に `schedule:` がなく、cron 自動運転は未稼働。
- `PostToolUse auto-record` は telemetry / router まではあるが、統合 sync は未完。
- `SessionStart auto-sync` は `docs/v2/CONCEPT.md` の想定に対して未実装。
- `Gate auto-detect` は一部 advisory / docs 上の方針に留まり、全入口統合ではない。
- GitHub Actions minutes の収集・警告・上限制御がない。
- Codex API consumption は取得基盤のみで、CI/CD 判断へ未接続。
- scheduler は手動 CLI とテストはあるが、定常実行の起動元が見当たらない。

## V2 で追加すべき自動化 Top 10

1. `helix sync --auto` 実装と SessionStart / PostToolUse / Gate からの共通呼び出し。
2. PostToolUse 変更ファイルを `plan / skill / code / detector` registrar に自動反映する auto-record。
3. SessionStart で `plan / skill / code catalog` の差分 auto-sync。
4. `helix gate` 実行前の auto-detect で関連 detector / docs drift-check を自動選択。
5. GitHub Actions に `schedule:` を追加し、nightly で `helix test --bats-only` と detector 群を回す。
6. `helix-scheduler run-due` の常設 runner を作り、cleanup / sync / audit を cron 管理に乗せる。
7. local hook installer を用意し、`pre-commit` template を `.git/hooks/pre-commit` へ確実配備する。
8. GitHub Actions minutes と `ccusage/state.db` を同じレポートに集約する cost dashboard。
9. stale lock cleanup と bats cleanup を `helix doctor` / scheduler から自動実行する保守ジョブ。
10. advisory のままになっている drift-check を、対象変更種別に応じて strict/loose 切替できる policy 化。

## 件数集計

- Claude Code hook 登録件数: 7
- runtime hook script / wrapper 件数: 10
- git hook template 件数: 3
- local 非 sample git hook 件数: 3
- GitHub Actions workflow 件数: 1
- 本監査表の CI/CD 項目数: 42

## ソース

- `.claude/settings.json`
- `.claude/hooks/pretooluse-opus-repo-block.sh`
- `.claude/hooks/post-tool-use.sh`
- `.claude/hooks/stop.sh`
- `.github/workflows/ci.yml`
- `cli/libexec/helix-session-start`
- `cli/libexec/helix-post-tool-use`
- `cli/libexec/helix-pre-bash`
- `cli/libexec/helix-pre-research`
- `cli/libexec/helix-check-claudemd`
- `cli/helix-session-summary`
- `cli/helix-test`
- `cli/helix-gate`
- `cli/helix-scheduler`
- `cli/helix-bats-cleanup`
- `cli/templates/hooks/pre-commit`
- `cli/templates/hooks/commit-msg`
- `cli/templates/hooks/post-merge`
- `.git/hooks/commit-msg`
- `.git/hooks/post-merge`
- `.git/hooks/pre-commit.helix.bak`
- `cli/lib/scheduler_helper.py`
- `cli/lib/concurrent_lock.py`
- `cli/lib/skill_recommender.py`
- `cli/lib/code_recommender.py`
- `cli/lib/defaults_loader.py`
- `cli/lib/budget.py`
- `docs/adr/ADR-009-hook-strategy.md`
- `docs/plans/PLAN-067-helix-automation-layer.md`
- `docs/features/PLAN-067/D-API/helix-sync.md`
- `docs/v2/CONCEPT.md`
- `docs/v2/A-audit/hooks-commands-subagents.md`

## 不確実な点

- `helix review --uncommitted` の実装本体までは今回未読で、manual trigger としての存在は docs 証跡中心。
- `cli/libexec/helix-check-claudemd` は settings と wrapper の関係から実在前提で評価したが、中身の詳細確認は省略した。
- GitHub Actions minutes の課金実績は repo 内コードからは確定できず、ここでは「計測導線がない」という評価に留めた。
