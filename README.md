# HELIX — AI エージェント制御開発システム

> 開発における OpenClaw。AI エージェントを効果的にシステマティックに制御する。

## 特徴

- **フェーズ制御**: L1-L11 + Phase Guard ですっ飛ばし防止
- **ゲート強制**: 成果物が揃わないと次に進めない
- **成果物駆動**: Deliverable Matrix で設計と実装を 1:1 対応
- **自己改善**: Learning Engine で成功/失敗パターンを蓄積・昇格
- **マルチモデル制御**: TL/SE/PG/FE の役割別委譲（thinking level 最適化）
- **設計駆動強制**: PLAN draft 時に D-shard 5 種（D-API / D-DB / D-ARCH / D-TEST / D-THREAT）の skeleton を自動生成、G2 で設計証跡 3 件以上 mandatory
- **委譲 Codex コミット禁止**: `helix codex` 経由の委譲先は git commit を実行しない（PM/TL がコミット判断）
- **5 駆動タイプ**: be/fe/db/fullstack/agent
- **105 スキル**: 開発・ライティング・デザイン・ブラウザ操作・エージェント運用
- **8 ビルダー**: エージェント開発の検証済みパーツ
- **日本語ファースト**: 日本の開発水準底上げ

## セットアップ

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
bash ~/ai-dev-kit-vscode/setup.sh
```

これだけで以下が自動設定される:

| 対象 | 処理 |
|------|------|
| 依存チェック | python3, bash 4+, git, sqlite3 CLI, codex CLI |
| Claude Code | `~/.claude/CLAUDE.md` に @import 追記 + `settings.json` に hooks マージ |
| Codex CLI | スキル symlink + `~/.codex/AGENTS.md` コピー（codex がある場合のみ） |

何度実行しても安全（冪等）。アンインストール: `bash ~/ai-dev-kit-vscode/setup.sh --uninstall`

> **配布物の境界**: 本リポジトリの `.helix/` 配下は git untracked（PLAN-021 で完全分離済）。clone 時には HELIX framework 本体（cli / skills / docs / templates）のみが降ります。各プロジェクトでは `helix init` で `.helix/` を初期化して使ってください。

## プロジェクトでの使い方（3 段階セットアップ）

`setup.sh` はホスト環境（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` / グローバル hook）の設定だけを行います。**各プロジェクトの `CLAUDE.md` / `AGENTS.md` / `.claude/settings.json` の生成・追従は `helix init` と `helix migrate` で行います**。

### Step 1: ホスト環境セットアップ（一度だけ）

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
bash ~/ai-dev-kit-vscode/setup.sh
```

### Step 2: 新規プロジェクトで HELIX を有効化

```bash
cd /path/to/new-project
helix init
# → CLAUDE.md / AGENTS.md / .claude/settings.json + .helix/ skeleton を生成
# → CLAUDE.md / AGENTS.md は HELIX-MANAGED-START/END マーカーで HELIX 管理範囲を明示
```

### Step 3: 既存プロジェクトを最新テンプレに追従（テンプレ更新時）

HELIX 本体を更新した後、各プロジェクトで:

```bash
cd /path/to/existing-project
helix migrate --dry-run    # 差分確認 (CLAUDE.md / AGENTS.md / .claude/settings.json)
helix migrate --yes        # 適用 (.helix/migrate-backups/<timestamp>/ に自動 backup)
helix migrate --rollback   # 直前の backup から戻す
```

`helix migrate` は冪等です。HELIX-MANAGED-START/END マーカー範囲内のみ最新版に置換し、マーカー外のユーザー記述は保持します。何度実行しても二重化しません。
本リポジトリ（HELIX framework 本体）自身で `helix migrate` を走らせた場合は self-host detection で `claude_md` / `agents_md` / `claude_settings` が skip されます（本体ドキュメントを壊さないため）。

### トラブルシューティング

| 症状 | 原因 / 対応 |
|---|---|
| `helix migrate` で CLAUDE.md / AGENTS.md が二重追記される | template が古い HELIX 版（マーカーなし）。`helix migrate --rollback` → HELIX 本体を最新化 → 再度 `helix migrate --yes` |
| `.claude/settings.json` が invalid JSON で fail-close | 手動で構文修正後に再実行。fail-close なので破壊はない |
| `.helix/handover/CURRENT.json` が stale | [docs/runbook/helix-handover.md](docs/runbook/helix-handover.md) 参照 |
| Codex 委譲が hang | [docs/runbook/helix-codex.md](docs/runbook/helix-codex.md) 参照 |

このリポジトリ自体のエージェント向け project rules は [CLAUDE.md](CLAUDE.md) と [AGENTS.md](AGENTS.md) が正本です。個人差分は `CLAUDE.local.md` / `AGENTS.override.md` に置きます。

このリポジトリへ clone した後は、Git hook を有効化するために `bash scripts/install-git-hooks.sh` を追加で実行してください。  
`pre-commit` は staged 内容の secret 混入を、`pre-push` は `CLAUDE.md` / `SKILL.md` / `references/*.md` の機密・PII 混入を検知します。  
運用境界は [docs/security-guidelines.md](docs/security-guidelines.md) を参照してください。
意図的に保留している未実装・Draft 管理は [docs/backlog/intentional-deferred.md](docs/backlog/intentional-deferred.md) を正本とします。

## 開発者セットアップ（pytest）

`helix test` は shell テストに加えて `cli/lib/tests/` の pytest も実行します。

```bash
# 1) pip が使えることを確認
python3 -m pip --version

# 2) 開発依存をインストール
python3 -m pip install --user -r requirements-dev.txt

# 3) 動作確認
python3 -m pytest --version
```

pytest を導入していない環境では `helix test` は pytest を警告付きで skip します。  
未導入を失敗扱いにしたい場合は `helix test --pytest-strict` を使用します。

## クイックスタート

```bash
# 1. プロジェクト初期化
helix setup bootstrap --project-name "$(basename "$PWD")"

# 手動で段階実行する場合
helix setup preflight --profile project
helix init

# 開発支援パッケージは明示実行（既定 dry-run）
helix setup packages list
helix setup packages install --name textlint --yes

# 旧まとめスクリプトも実インストールは --yes 必須
bash ~/ai-dev-kit-vscode/cli/scripts/setup-all.sh --yes

# 2. タスクサイジング
helix size --files 10 --lines 300 --api --type new-feature --drive be

# 3. 成果物対照表の有効化
helix matrix init && helix matrix compile

# 4. 設計提案（TL レビュー付き）
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001

# 5. 実装（Codex 委譲）
helix codex --role se --task "ユーザー認証の実装"

# 6. ゲート検証
helix gate G4

# 7. PR 作成
helix pr
```

## モノレポでの使い方

特定パッケージだけを HELIX 管理対象にできます。

```bash
# リポジトリルートで実行
helix init --monorepo-package packages/api

# 以降のコマンドは対象パッケージをプロジェクトルートとして扱う
HELIX_PROJECT_ROOT="$(pwd)/packages/api" helix size --files 5 --lines 120 --type bugfix --drive be
HELIX_PROJECT_ROOT="$(pwd)/packages/api" helix gate G4 --static-only
```

## CLI 機能マップ

HELIX の入口は 6 領域に分けて使う。全コマンドの索引は [docs/commands/index.md](docs/commands/index.md) を参照。

### 1. HELIX 全体管理

| コマンド | 使う場面 |
|---------|----------|
| `helix init` | プロジェクトを HELIX 管理下に置く |
| `helix status` | 現在地、次アクション、主要状態を見る |
| `helix dashboard` | 静的な読み取り専用 snapshot を出す（Dashboard 構想管理の対象外） |
| `helix mode` | forward / reverse / scrum を切り替える |
| `helix doctor` / `helix migrate` / `helix commands` / `helix setup` | 環境診断、テンプレ追従、コマンド同期検証、初期化検証 |
| `helix test` / `helix test-debug` | CLI 全体の回帰確認 |
| `helix debug` / `helix bench` | 調査、メトリクス確認 |

### 2. HELIX プロジェクト管理

| コマンド | 使う場面 |
|---------|----------|
| `helix size` | タスクサイズ、drive、フェーズスキップ判定 |
| `helix plan` | 設計提案を draft → review → finalize で凍結 |
| `helix matrix` | 成果物対照表、doc-map、gate-checks を管理 |
| `helix gate` / `helix gate-api-check` | ゲート、API 契約整合を検証 |
| `helix readiness` | deferred finding と readiness exit を管理 |
| `helix sprint` / `helix task` | L4 実装スプリントとタスク OS |
| `helix interrupt` / `helix handover` | IIP/CC と Opus/Codex handover |
| `helix pr` / `helix retro` / `helix debt` | PR、ミニレトロ、技術負債 |
| `helix drift-check` | D-API / D-CONTRACT / D-DB のドリフト検知 |

### 3. Codex / Claude Code 管理 harness

| コマンド | 使う場面 |
|---------|----------|
| `helix codex --role <role> --task "..."` | Codex CLI への role/task 委譲 |
| `helix claude --role <role> --task "..." --dry-run` | Claude Code 用 plan/task prompt 生成 |
| `helix team run --definition .helix/teams/<team>.yaml` | 複数 role のチーム委譲 |
| `helix review [--uncommitted]` | Codex 自動レビュー |
| `helix skill` | HELIX スキル検索・参照 |
| `helix budget` | Claude/Codex の消費・モデル推奨 |
| `helix hook` / `helix check-claudemd` | Claude Code hook の入口 |
| `helix session-start` / `helix session-summary` | SessionStart / Stop hook |

--thinking オプション:

| ロール | デフォルト思考レベル |
|--------|-------------------|
| tl/security/legacy | xhigh |
| se/fe/qa/perf | high |
| pg/dba/devops | medium |
| docs/research | low |

詳細: [docs/commands/ai-harness.md](docs/commands/ai-harness.md)

### 4. Reverse / Scrum / 検証

| コマンド | 説明 |
|---------|------|
| `helix reverse <type> <R0-R4>` | code / design / upgrade / normalization / fullback の Reverse HELIX |
| `helix scrum` | 仮説検証、PoC、verify、Forward 接続 |
| `helix verify-all` | verify/ 配下の検証スクリプト実行 |
| `helix verify-agent` | 検証ツール harvest / design / PLAN drift cross-check |

判定管理: [docs/commands/reverse.md](docs/commands/reverse.md), [docs/commands/scrum.md](docs/commands/scrum.md)

### 5. 学習・再利用

| コマンド | 説明 |
|---------|------|
| `helix log` | SQLite ログ・評価・session report |
| `helix recipe` | learn / promote / discover / list の正規入口 |
| `helix learn` / `helix promote` / `helix discover` | recipe 旧入口（deprecated） |
| `helix builder list` | 利用可能なビルダー一覧 |
| `helix builder <type> generate` | ビルダーでアーティファクト生成 |
| `helix code` | コード index 検索・重複検出・統計 |
| `helix audit` | A1 audit decisions 同期・検証 |

8 種: json-converter, verify-script, agent-loop, task, workflow, agent-pipeline, agent-skill, sub-agent

### 6. 補助・運用

| コマンド | 説明 |
|---------|------|
| `helix scheduler` | 定期実行スケジュール |
| `helix job` | 非同期ジョブキュー |
| `helix lock` | DB lock 管理 |
| `helix observe` | イベント・メトリクス観測 |

## スキル（105 本、10 カテゴリ）

| カテゴリ | スキル数 | 主な内容 |
|---------|---------|---------|
| workflow/ | 31 | プロジェクト管理・設計・検証・デプロイ・Reverse |
| common/ | 12 | コーディング・レビュー・テスト・セキュリティ |
| project/ | 8 | UI・API・DB・FE サブエージェント |
| advanced/ | 6 | 技術選定・i18n・レガシー・マイグレーション |
| tools/ | 4 | AI コーディング・IDE ツール・検索 |
| integration/ | 1 | エージェントチーム |
| writing/ | 5 | 日本語品質・ストーリー・プレゼン・SNS |
| design-tools/ | 5 | 図表・Web デザイン・PPTX・画像 |
| automation/ | 8 | サイトマッピング・ブラウザ操作・フロー最適化・scheduler/job/lock/setup/observe |
| agent-skills/ | 25 | 上流 agent-skills 統合・HELIX 独自拡張 |

## 駆動タイプ（5 種）

| タイプ | 起点 | 典型プロジェクト |
|-------|------|----------------|
| be | API/ロジック | 業務系、SaaS バックエンド |
| fe | デザイン/UX | LP、ダッシュボード |
| db | スキーマ/データ | マスタ管理、データ基盤 |
| fullstack | BE+FE 同時 | SaaS、EC、管理画面+API |
| agent | ツール/プロンプト | AI アプリ、自動化 |

## ガバナンス 4 層

1. **サンドボックス**: 実行環境分離（workspace-write / read-only）
2. **ガードレール**: Phase Guard + Deliverable Gate + Plan Review
3. **モニタリング**: Advisory Hook + Freeze-break 検知
4. **監査**: SQLite ログ + ミニレトロ + Learning Engine

## Runbook（運用手順）

主要 CLI の障害対応・復旧手順は [docs/runbook/](docs/runbook/) を参照。

- [helix-codex.md](docs/runbook/helix-codex.md) — 委譲 Codex の hang / plan-only guard / 勝手 commit 対応
- [helix-plan.md](docs/runbook/helix-plan.md) — PLAN draft / G2 fail / plan id 衝突対応
- [helix-migrate.md](docs/runbook/helix-migrate.md) — テンプレ移行の dry-run / apply / rollback / invalid JSON 対応
- [helix-handover.md](docs/runbook/helix-handover.md) — Opus ↔ Codex handover の stale 検知 / ESCALATION / resume 復旧

## ADR（設計判断記録）

- ADR-001: Deliverable Matrix as Source of Truth
- ADR-002: Builder System Foundations
- ADR-003: Learning Engine Foundations
- ADR-004: Bash-Python ハイブリッドアーキテクチャ
- ADR-005: YAML-SQLite 二重状態管理
- ADR-006: テンプレートコピーアーキテクチャ
- ADR-007: 3モード統合（Forward / Reverse / Scrum）
- ADR-008: ビルダーシステムによる成果物生成の抽象化
- ADR-009: Hook 戦略（doc-map トリガー中心）
- ADR-010: Task OS（2層構造: タスク→アクション）

詳細: [docs/adr/](docs/adr/)

## ライセンス

MIT
