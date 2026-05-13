# FR-INV17 CLI / UX 現状監査

最終更新: 2026-05-14

## 概要

本書は `helix *` CLI の現状棚卸しです。V2 Phase 1 既存整理での命名統一と、Phase 2 以降の help / error / discoverability 改善の入力に使います。

今回の監査対象は **router 配下で `helix <command>` として実行できる top-level command 58 件**です。加えて `plan` / `skill` / `code` / `scrum` / `reverse` / `handover` などの help を読んだところ、**parser ベース概算で 178 個の subcommand / option entry** があり、TASK_INPUT の「60+ サブコマンド」は十分満たしています。

注記:

- `help 有無` は `./cli/helix <command> --help` の成否ベースです。
- `error 品質` は代表的な invalid input を投げて見た結果と help 実装からの**推定**を含みます。
- `V2 Phase 紐付け` は `docs/v2` 既存監査 docs と現在の責務からの**監査用ラベル**です。設計正本ではありません。
- `dry-run` は command help 上で明示されるものを `yes`、破壊操作がないものは `N/A` としました。

## 選択肢

### Option A: 現状の command 名をほぼ維持して help だけ補修

- メリット: 互換性リスクが最小。
- デメリット: `learn/promote/discover` の legacy alias、`session-summary` の名前ずれ、`gate-api-check` の二重 prefix などの負債が残る。
- 推奨度: 中。

### Option B: V2 Phase 1 で命名正規化、互換 alias は暫定維持

- メリット: discoverability と一貫性が大きく改善する。help / docs / error copy も同時に揃えやすい。
- デメリット: alias / deprecation policy の整理が必要。
- 推奨度: 高。

### Option C: V2 で command tree を大きく再編

- メリット: `status/dashboard/bench/log`、`recipe/learn/promote/discover`、`hook/session-*` などの重複概念を根本整理できる。
- デメリット: V1 互換の破壊変更が増え、Phase 1 には重い。
- 推奨度: 低。

## 推奨

**Option B** を推奨します。理由は 4 点です。

1. routed command 58 件は help / docs と整合しており、全面再編よりも **rename + alias + deprecate** が現実的です。
2. 問題の中心は機能不足より **命名の不統一** と **エラーメッセージ品質のばらつき** です。
3. `learn/promote/discover` はすでに deprecated で、V2 Phase 1 で整理しやすい候補です。
4. `session-summary`、`check-claudemd`、`gate-api-check`、`verify-all` などは名前と実体のズレが大きく、Phase 1 で正規名を決めておく価値があります。

## 監査サマリ

| 観点 | 結果 |
|---|---|
| routed top-level command 数 | 58 |
| subcommand / option entry 概算 | 178 |
| `--help` あり | 58/58 |
| `--dry-run` 明示あり | 17/58 |
| `--json` 明示あり | 23/58 |
| default 安全性 | top-level router は引数なしで `help` にフォールバック。破壊系でも即実行より help / error に倒れるものが多い |
| discoverability | routed command と `docs/commands/index.md` は整合。`cli/helix-detect` のように script はあるが router 非公開のものは混乱要因 |
| 互換性リスク | deprecated alias、hook 名露出、略語 command、重複概念 command 群 |

## 主な観察

### 1. help text

- routed command 58 件は全て `--help` を返し、**help 不在 command は 0 件**でした。
- ただし品質差があります。
  - 強い: `plan`, `gate`, `reverse`, `scrum`, `audit`, `handover`
  - 弱い: `review`, `size`, `test`, `verify-all`
- `commands check` による route/help/docs 整合検証があり、基盤としては良いです。

### 2. error message

- top-level の未知 command は `エラー: 不明なコマンド` + `helix help` 誘導で **良**。
- `plan`, `code`, `context` は invalid subcommand 時に usage を返し **良**。
- `size` は `エラー: 不明なオプションです` のみで次アクションが薄く **悪**。
- `review`, `test`, `verify-all` は help が薄く、異常系の誘導改善余地が大きいです。

### 3. discoverability

- `helix help` / `docs/commands/index.md` / route は整合していました。
- 一方で command tree が深く、`status/dashboard/bench/log`、`recipe/learn/promote/discover`、`hook/session-start/session-summary/check-claudemd/context` は初見学習コストが高いです。
- `cli/helix-detect` は実ファイルがある一方で `helix` router からは到達できず、監査視点では **非 discoverable 実装** です。

### 4. naming consistency

- kebab-case 自体は概ね守られています。
- 問題は case ではなく **語彙の粒度** と **prefix の揺れ** です。
  - `gate-api-check`, `drift-check`, `bats-cleanup`, `test-debug`
  - `session-start`, `session-summary`, `check-claudemd`
  - `pr`, `job`, `entry`, `meta-phase`
- 動詞始まりと名詞始まりが混在し、action か domain かが command ごとに揺れます。

## Inventory

| command | help 有無 | dry-run | error 品質 | 命名問題 | V2 変更計画 | V2 Phase 紐付け | 現状メモ |
|---|---|---|---|---|---|---|---|
| asset | yes | yes | 良 | 名詞のみで生成系と分かりにくい | modify | Phase 5 | 画像 asset preset 生成 |
| audit | yes | yes | 良 | - | as-is | Phase 3 | A1 audit decisions 同期・検証 |
| bats-cleanup | yes | yes | 良 | 固有技術名が表層に出る | rename | Phase 3 | バッチ実行用一時ディレクトリ監査 |
| bench | yes | N/A | 良 | - | modify | Phase 4 | プロジェクトメトリクス表示 |
| budget | yes | N/A | 並 | - | modify | Phase 4 | Claude/Codex 予算管理・モデル推奨 |
| builder | yes | N/A | 並 | 名詞のみで目的が広すぎる | modify | Phase 5 | 成果物ビルダー |
| check-claudemd | yes | no | 良 | vendor 固有 + kebab 不自然 | rename | Phase 5 | PreToolUse hook |
| claude | yes | yes | 良 | - | as-is | Phase 5 | Claude Code 用 plan/task prompt 生成 |
| code | yes | no | 良 | - | as-is | Phase 2 | コードインデックス検索/重複検出/統計 |
| codex | yes | yes | 良 | - | as-is | Phase 5 | Codex への role/task 委譲 |
| commands | yes | N/A | 良 | - | as-is | Phase 1 | コマンド route/help/docs と主要 workflow 連携契約の同期検証 |
| context | yes | N/A | 良 | - | as-is | Phase 5 | context / memory guardrail check |
| dashboard | yes | N/A | 良 | status/bench/log と境界が曖昧 | modify | Phase 4 | 主要状態の静的 snapshot 表示 |
| debt | yes | N/A | 良 | - | as-is | Phase 2 | 技術負債管理 |
| debug | yes | N/A | 並 | 名詞のみで範囲が広い | modify | Phase 3 | デバッグツール |
| discover | yes | N/A | 良 | recipe discover と二重 | deprecate | Phase 5 | パターン検索 (deprecated: helix recipe discover) |
| doctor | yes | N/A | 並 | - | as-is | Phase 3 | 環境診断・修復 |
| drift-check | yes | no | 良 | 動詞後置の複合名 | modify | Phase 3 | 契約ドリフト検知 |
| entry | yes | N/A | 並 | 名詞のみで domain 意味が不明 | modify | Phase 2 | entries/links 中央 DB の CRUD + N 軸 coverage (PLAN-027) |
| gate | yes | yes | 良 | - | as-is | Phase 2 | ゲート自動検証 |
| gate-api-check | yes | no | 並 | gate と api-check の二重 prefix | rename | Phase 3 | API エンドポイント整合チェック |
| handover | yes | no | 良 | - | as-is | Phase 2 | Opus/Codex handover 管理 |
| hook | yes | no | 良 | - | modify | Phase 5 | PostToolUse hook |
| init | yes | no | 良 | - | as-is | Phase 1 | プロジェクト初期化 |
| interrupt | yes | no | 良 | - | as-is | Phase 2 | IIP/CC 中断・復帰管理 |
| job | yes | N/A | 並 | scheduler/observe と境界が曖昧 | modify | Phase 4 | 非同期ジョブキュー管理 |
| learn | yes | N/A | 良 | recipe learn と二重 | deprecate | Phase 5 | 成功パターン学習 (deprecated: helix recipe learn) |
| lock | yes | N/A | 並 | - | modify | Phase 4 | DB lock 管理 |
| log | yes | N/A | 良 | observe との境界が曖昧 | as-is | Phase 4 | ログ・評価システム |
| matrix | yes | no | 並 | - | as-is | Phase 2 | 成果物マトリクス管理 |
| meta-phase | yes | no | 良 | 概念語で学習コストが高い | rename | Phase 1 | PLAN-006 L1 メタ工程の pattern 契約検証 |
| migrate | yes | yes | 並 | - | as-is | Phase 1 | .helix/ テンプレ追従 (--dry-run/--yes/--rollback) |
| mode | yes | yes | 良 | - | as-is | Phase 1 | forward / reverse / scrum 切替 |
| observe | yes | N/A | 良 | - | as-is | Phase 4 | イベント・メトリクス観測 |
| plan | yes | yes | 良 | - | as-is | Phase 2 | 設計計画 |
| pr | yes | yes | 並 | 略語で意味推定が必要 | modify | Phase 4 | PR 自動生成 |
| promote | yes | N/A | 良 | recipe promote と二重 | deprecate | Phase 5 | レシピ昇格 (deprecated: helix recipe promote) |
| readiness | yes | N/A | 良 | 名詞のみで action が見えない | modify | Phase 2 | readiness exit 判定 / deferred-finding 操作 |
| recipe | yes | N/A | 良 | - | as-is | Phase 5 | 成功パターン学習 (learn/promote/discover/list) |
| research | yes | yes | 良 | 調査実行ではなくテーマ生成寄り | modify | Phase 2 | L1-L3 向けの調査テーマ生成と dry-run |
| retro | yes | yes | 良 | - | as-is | Phase 2 | レトロスペクティブ |
| reverse | yes | yes | 良 | - | as-is | Phase 2 | リバース HELIX |
| review | yes | N/A | 悪 | - | as-is | Phase 3 | Codex 自動レビュー |
| scheduler | yes | yes | 並 | - | as-is | Phase 4 | 定期実行スケジュール管理 |
| scrum | yes | no | 良 | - | as-is | Phase 2 | 検証駆動開発 |
| session-start | yes | no | 良 | hook 名そのもの | rename | Phase 5 | SessionStart hook |
| session-summary | yes | no | 良 | summary 実体と不一致 | rename | Phase 5 | Stop hook |
| setup | yes | yes | 並 | - | modify | Phase 3 | 初期化検証・修復 |
| size | yes | N/A | 悪 | - | as-is | Phase 1 | タスクサイジング |
| skill | yes | yes | 良 | - | as-is | Phase 5 | スキル検索・参照 |
| sprint | yes | N/A | 良 | - | as-is | Phase 2 | L4 マイクロスプリント |
| status | yes | N/A | 良 | - | as-is | Phase 1 | プロジェクト状態表示 |
| task | yes | N/A | 良 | - | modify | Phase 2 | タスクオペレーティングシステム |
| team | yes | no | 並 | run が必須で単体意味が弱い | modify | Phase 5 | エージェントチーム実行 |
| test | yes | N/A | 悪 | - | as-is | Phase 3 | セルフテスト |
| test-debug | yes | N/A | 良 | ハイフン接尾で alias 感が強い | rename | Phase 3 | デバッグ有効セルフテスト |
| verify-agent | yes | yes | 良 | verify + agent が曖昧 | rename | Phase 3 | 検証ツール harvest / design / PLAN drift cross-check |
| verify-all | yes | N/A | 悪 | all が抽象的 | rename | Phase 3 | 全レイヤー検証 |

## 代表 subcommand 棚卸し

最低 50 command 要件は top-level 58 件で満たしていますが、命名統一の入力として subcommand も観察しました。

| parent | 主な subcommand | 所感 |
|---|---|---|
| `plan` | `draft`, `review`, `finalize`, `reset`, `list`, `status`, `lint`, `import` | 一貫して良い。V2 の naming baseline 候補 |
| `code` | `build`, `list`, `show`, `find`, `dup`, `stats` | domain/action の粒度が比較的揃う |
| `handover` | `dump`, `status`, `update`, `clear`, `escalate`, `resume` | action 指向で分かりやすい |
| `interrupt` | `start`, `apply`, `resume`, `status`, `history`, `report`, `cancel` | `history/report` 二重化あり |
| `scrum` | `init`, `backlog list`, `backlog add`, `plan`, `poc`, `verify`, `decide`, `review`, `status` | command tree は豊富だが learnability は高コスト |
| `reverse` | `run`, `status`, `rgc`, `retry`, `R0..R4` | expert 向け。互換 alias を含み UX はやや特殊 |
| `skill` | `list`, `show`, `catalog rebuild`, `classify`, `search`, `use`, `chain`, `stats`, `review-pending`, `approve` | action が明瞭で比較的強い |
| `audit` | `preflight`, `a0 discover`, `a1 import`, `a1 verify-sync`, `a1 status` | phase prefix 露出は power-user 向け |

## help 不在

- routed command 58 件中 **0 件**

## error 悪い

- `review`
- `size`
- `test`
- `verify-all`

補足:

- `size __invalid__` は `不明なオプション` のみで、`--help` 再誘導がありません。
- `review`, `test`, `verify-all` は help 自体が短く、失敗時の推奨アクションが弱いです。

## naming 問題一覧

- `bats-cleanup`
- `builder`
- `check-claudemd`
- `dashboard`
- `debug`
- `discover`
- `drift-check`
- `entry`
- `gate-api-check`
- `job`
- `learn`
- `log`
- `meta-phase`
- `pr`
- `promote`
- `readiness`
- `research`
- `session-start`
- `session-summary`
- `team`
- `test-debug`
- `verify-agent`
- `verify-all`

## V2 で rename / deprecate 候補 top-10

1. `discover` → deprecate
   - `recipe discover` と二重。discoverability を悪化させる。
2. `learn` → deprecate
   - `recipe learn` の legacy alias。
3. `promote` → deprecate
   - `recipe promote` の legacy alias。
4. `session-summary` → rename
   - 実体は summary 生成でなく accounting / logging shim。
5. `check-claudemd` → rename
   - vendor 固有名が強すぎ、hook の意味が見えにくい。
6. `gate-api-check` → rename
   - `gate` と `api-check` の二重 prefix。
7. `verify-all` → rename
   - `all` が抽象的で対象範囲を想像しにくい。
8. `verify-agent` → rename
   - 実体は agent というより verification design / harvest。
9. `test-debug` → rename
   - `test --debug` 形式へ寄せた方が体系的。
10. `meta-phase` → rename
   - expert 用語で、初見では機能が伝わりにくい。

## default 挙動

- `helix` 単体は `help` にフォールバックし、安全側です。
- 多くの command は invalid input で即変更せず error/usage を返します。
- ただし destructive 系の統一ルールはまだ弱く、`--dry-run` 明示は 17/58 に留まります。
- `migrate`, `pr`, `gate`, `codex`, `claude`, `research`, `retro`, `verify-agent`, `scheduler` は `--dry-run` 文化が見えます。

## JSON output 対応

- `--json` 明示ありは 23/58。
- 観測系・状態系 (`status`, `bench`, `dashboard`, `commands`, `context`, `handover`, `interrupt`, `readiness`, `skill`, `sprint`, `meta-phase`, `verify-agent`) に比較的集まっています。
- command tree 全体の機械可読性は「部分的に強いが一貫してはいない」状態です。

## 互換性: V1 → V2 で破壊変更しそうな箇所

1. legacy alias 群
   - `learn`, `promote`, `discover`
2. hook 露出 command 群
   - `check-claudemd`, `session-start`, `session-summary`, `hook`
3. status 系の役割重複
   - `status`, `dashboard`, `bench`, `log`, `observe`
4. verification 系の命名揺れ
   - `test`, `test-debug`, `verify-all`, `verify-agent`, `review`
5. orchestration 専門語
   - `meta-phase`, `entry`, `readiness`

## 推奨アクション

1. V2 Phase 1 で command naming policy を先に固定する
   - `verb-noun` か `domain-action` のどちらを主軸にするか決める
2. alias / deprecated policy を文書化する
   - `learn/promote/discover` は早めに 1 系統へ寄せる
3. error copy の最低基準を設ける
   - `何が悪いか`、`次に何を打つか`、`--help` 誘導を必須化
4. dry-run / json の適用方針を整理する
   - state changing command に `--dry-run`、state reporting command に `--json` を原則付与
5. 非公開 script と公開 route の差分を解消する
   - `cli/helix-detect` のような実体の扱いを決める

## ソース

- [cli/helix](/home/tenni/ai-dev-kit-vscode/cli/helix:1)
- [cli/lib/command_catalog.py](/home/tenni/ai-dev-kit-vscode/cli/lib/command_catalog.py:1)
- [docs/commands/index.md](/home/tenni/ai-dev-kit-vscode/docs/commands/index.md:1)
- [docs/commands/ai-harness.md](/home/tenni/ai-dev-kit-vscode/docs/commands/ai-harness.md:1)
- [docs/v2/A-audit/capability-inventory.md](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/capability-inventory.md:1)
- [docs/v2/A-audit/hooks-commands-subagents.md](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/hooks-commands-subagents.md:1)
- `./cli/helix --help`
- `./cli/helix <command> --help`
- `./cli/helix foo`
- `./cli/helix plan __invalid__`
- `./cli/helix size __invalid__`
- `./cli/helix context __invalid__`
- `./cli/helix code __invalid__`
