# cli/ レイアウトマップ — 責務境界

## 1. ディレクトリ俯瞰

```text
cli/
├── helix-*               # ユーザー向けエントリ (router)
├── libexec/              # 内部 hook / shim
├── lib/                  # Python helper
├── config/               # YAML 設定
├── roles/                # role 別 conf (正本、ADR-014)
├── templates/            # 配布物 + プロンプト + hook
├── tests/                # bats
└── ROLE_MAP.md           # 12 role 一覧 (周知用)
```

- `cli/prompts` は PLAN-024 Sprint .3 W-3d の移行対象で、現在の実体は後段で `templates/*` へ統合される。
- `templates/` は実体移行後に `prompts/`/`hooks/`/`agents/`/`stage-prompts/`へ整備される前提。
- `helix-*` は `cli` 直下の薄いルータとして `cli/lib*` を起点に delegate する。

### 1.1 実測ポイント（本書作成時）

- `cli/lib`: 68 ファイル（`cli/lib/` 配下に helper 群 + `builders`/`learning` サブツリー）
- `cli/libexec`: 9 ファイル（`helix-pre-bash`、`helix-session-start` を含む）
- `cli/config`: 3 ファイル
- `cli/roles`: 20 ファイル（`tl.conf` を含む各 role の source of truth）
- `cli/templates`: 37 ファイル
- `cli/tests`: 40 ファイル（bats）
- `cli/` 直下 helix-* スクリプト: 40 近傍（主要は `helix`, `helix-*` 系コマンド）

## 2. 各ディレクトリの責務

| ディレクトリ | 責務 | 含むファイル種別 | 例 |
|---|---|---|---|
| `helix-*` | router（薄い CLI glue） | bash | `helix`, `helix-codex`, `helix-skill` |
| `libexec/` | 内部 hook / shim / event hook | bash | `helix-pre-bash`, `helix-session-start` |
| `lib/` | ロジック層（state 集計 / SQLite / LLM 連携 / parser / 命令配線） | python | `llm_classifier_base.py`, `helix_db.py` |
| `config/` | YAML 設定（共通定数 / 周知） | yaml | `models.yaml`, `defaults.yaml`, `plan-limits.yaml` |
| `roles/` | role 別 conf（正本） | shell-style | `tl.conf`, `se.conf`, `pg.conf` |
| `templates/prompts/` | LLM プロンプトの配布元（将来整理後） | md | `skill-search.md`, `effort-classify.md` |
| `templates/hooks/` | git hook 配布物 | bash | `commit-msg`, `pre-commit`, `post-merge` |
| `templates/agents/` | Claude サブエージェント定義 | md | `code-reviewer.md`（FE 系のみ） |
| `templates/stage-prompts/` | 段階別 fragment（PLAN-027 導入） | md | `L4.md`, `R2.md` |
| `templates/*.template` | プロジェクト初期テンプレート | md / yaml | `CLAUDE.md.template`, `config.yaml` |
| `tests/` | Bats テスト | bats | `test-helix-codex.bats`, `test-helix-code.bats` |

### 2.1 `cli/lib/` のカテゴリ例（目的別）

- `audit_*` 系: 監査ログ、監査用イベント、整合性検証の論理
- `budget_*` 系: モデル予算・コスト管理
- `code_*` 系: コード検索・catalog・推薦
- `gate_*` / `phase_*` 系: ゲート・フェーズ遷移・制御
- `helix_*` 系: CLI 補助関数（共通ヘルパ）
- `matrix_*` / `migrate_*` 系: 設計系機能や移行ユーティリティ

### 2.2 `cli/tests/` の種別

- `test-*.bats`: `helix-*` コマンドの振る舞い回帰
- `test-*-manual.sh`: 手動実行や検証補助
- 役割が広いため、bats は対象コマンドごとに最小単位で分離

## 3. 責務境界の原則

- `helix-*` は薄い router。実施責務は CLI 呼び出し、引数 parse、`lib` 呼び出し、exit code 制御に限定。
- `helix-*` にロジックを持たない。原則「5 行未満」の glue 例外を除外。
- ロジックは `lib/*.py` または `libexec/*` に移し、`helix-*` から分離。
- 設定値は `config/*.yaml` または `roles/*.conf` に集約する。
- Python リテラル定数の埋め込みは禁止方向（Sprint .3 W-3a 方針）。
- プロンプトと hook は `templates/prompts` / `templates/hooks` に分離配置。
- `templates/` 直置きの prompt/hook（`*-prompt` / `*-hook`）は原則廃止。
- `templates/agents` は AI エージェント定義を扱い、Core 実装とは分離。
- `lib/*` は import 可能な再利用可能単位を意識し、`helix` で直接 import しない。
- PMO 起票/状態確認系は `helix claude --role pmo --model sonnet|haiku --execute` を経由。

## 4. 命名規約

- helix-command 系: `helix-{動詞}` / `helix-{名詞}`
  - 動詞系: `helix-codex`, `helix-test`, `helix-init`
  - 名詞系: `helix-skill`, `helix-handover`
- `libexec` script: `libexec/helix-{event}`。
  - 例: `helix-pre-bash`, `helix-session-start`, `helix-post-tool-use`
- `lib/{module}.py`: `snake_case`。
  - 1 ファイル 1 責務、CLI 由来の分岐より前に構造化ロジック化
- テンプレート: `templates/prompts/{purpose}.md`
  - `-prompt` サフィックスは不要（ディレクトリで意味を担保）
- Hook テンプレート: `templates/hooks/{event}`
  - `-hook` サフィックスは不要
- 設定: `snake_case` + 役割別接頭辞（例: `models.yaml`, `defaults.yaml`）
- テストファイル: `test-*.bats`（bats）または `test_*.py`（pytest）
- `helix-claude`: `helix-claude --role <role> --model <model> --task \"<task>\" --execute [--allow-paths \"docs/**\"]`

## 5. 横断ルール

- Bash: `set -euo pipefail` を前提とする
- Python: 型ヒントを推奨。外部依存は最小化。
- Python 外部入力は validator 経由に寄せ、直 parse 回避
- DB 操作は標準 `sqlite3` 経路を基本として実装
- YAML 読み込みは内製 `yaml_parser.py` 経由を優先
- `cli/tests/` のみが Bats 対象
- `cli/lib/tests/` のみが pytest 対象
- ドキュメント記述のファイルパスは「リポジトリルート相対」のみを使用
- `docs/architecture/cli-layout.md` は PLAN-024 W-3d 完了時点の論理構造を記載
- 主要責務の移譲先は本文と実体配置（`cli/`）でクロス検証する

## 6. 参考（PLAN 及び ADR）

- ADR-006: [docs/adr/ADR-006-template-copy-architecture.md](docs/adr/ADR-006-template-copy-architecture.md)
- ADR-009: [docs/adr/ADR-009-hook-strategy.md](docs/adr/ADR-009-hook-strategy.md)
- ADR-014: [docs/adr/ADR-014-roles-config-format.md](docs/adr/ADR-014-roles-config-format.md)
- PLAN-024 Sprint .3 W-3d: `cli/templates/` 物理整理の完了状態を前提とする

## 7. メンテナンス目線の確認事項

- `docs/architecture/cli-layout.md` を更新する際は、`helix` / `lib` / `templates` の実体移動前後で責務境界の齟齬がないか確認する。
- `libexec` と `templates` の追加変更は必ず `.bats` または導線テストで参照先を検証する。
- `roles/*.conf` の変更は ADR-014 と `ROLE_MAP.md` の整合性チェックを行う。
- テンプレファイル変更時は `docs/commands/` の導線破壊（`helix init` 配布パス）を横断確認する。

## 8. 参照元と依存の確認手順（例）

1. `ls cli` と `rg --files cli/helix-*` で router 数を把握する。
2. `ls cli/libexec` と `ls cli/lib` で責務の寄せ先を確認する。
3. `ls cli/config` / `ls cli/roles` / `ls cli/templates` を確認し、実体と命名規約を合わせる。
4. `ls cli/tests` で Bats 配下のテスト網羅を確認する。
5. `docs/architecture/cli-layout.md` と `HELIX` 実装要件の `ADR-006/009/014` を突き合わせる。

## 9. 対象ファイルの責務境界チェックリスト

### 9.1 追加時

- `helix-*` を追加する場合
  - `PATH` から呼び出し可能な entry か
  - lib 依存が薄い call chain であるか
  - exit code が明示されるか

- `lib/*.py` を追加する場合
  - 1 機能 1 モジュールか
  - `TYPE` / 例外の扱いが明示されているか
  - テスト対象が `cli/lib/tests` か、`bats` なら stub 戦略があるか

### 9.2 移動時

- `templates` を追加・移動する場合
  - 命名規約（`{目的}.md`）に一致しているか
  - 配布先が実際の配布ルート（`helix init` 配線）と一致しているか
  - 既存参照の path を一緒に更新しているか

- `roles/*.conf` を追加する場合
  - 役割命名（`tl/se/pg/...`）が `ROLE_MAP.md` と一致するか
  - `roles/` 正本ルールに反していないか

## 10. PLAN-024 Sprint .3 で扱う境界（W-3c 観点）

- W-3a: `cli/config/defaults.yaml` への値集約、既存ロジック側のリテラル撤去
- W-3b: `docs/adr/ADR-014-roles-config-format.md` 起票（role conf の正本明文化）
- W-3c: 本ドキュメント（cli責務境界）作成（本タスク）
- W-3d: `templates` の物理再配置・参照置換（破壊的変更）

本書は W-3c 完了時点では、W-3d を見据えた最終分離状態を含めて記載する。
