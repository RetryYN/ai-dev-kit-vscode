# ai-dev-kit-vscode

Claude Code / Codex CLI 向けの HELIX スキルフレームワーク。
42 のスキルが全プロジェクトで使えるようになる。

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

### 手動セットアップ（setup.sh を使わない場合）

<details>
<summary>Claude Code</summary>

```bash
mkdir -p ~/.claude
cat >> ~/.claude/CLAUDE.md << 'EOF'
@~/ai-dev-kit-vscode/skills/SKILL_MAP.md
@~/ai-dev-kit-vscode/helix/HELIX_CORE.md
EOF
```

`~/.claude/settings.json` の hooks に SessionStart / PreToolUse / PostToolUse を手動追加する必要がある。
</details>

<details>
<summary>Codex CLI</summary>

```bash
bash ~/ai-dev-kit-vscode/helix/sync-codex-skills.sh
cp ~/ai-dev-kit-vscode/helix/AGENTS.md.example ~/.codex/AGENTS.md
```
</details>

### 共通設定

`helix/HELIX_CORE.md` に Claude Code / Codex CLI 共通のガイダンス（タスク受領・スキル・原則）を配置。
`helix/CODEX_TL_MODE.md` に Codex CLI 単体利用時の TL 主導読み替えルールを配置。
L1-L8 フロー・ゲートは `SKILL_MAP.md`、モデル割当は各ツール設定に記載。
ツール固有の設定は `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` にそれぞれ記載。

## しくみ

```
Claude Code:
  ~/.claude/CLAUDE.md           <- @import で SKILL_MAP.md + HELIX_CORE.md を取り込み
    └── 各 SKILL.md             <- タスクに応じてオンデマンド Read

Codex CLI:
  ~/.codex/AGENTS.md            <- HELIX_CORE.md + CODEX_TL_MODE.md を Read 指示
  ~/.codex/skills/helix-*/      <- 42 スキルのシンボリックリンク
    └── SKILL.md frontmatter    <- name + description で自動発見
```

- 個々のスキルは triggers に該当したとき自発的に Read する
- 全スキル一括読み込みはしない（コンテキストウィンドウ節約）

## HELIX 開発フロー

```
Phase 1: 計画    L1(要件) → L2(設計) → L3(詳細設計+API契約+工程表)
Phase 2: 実装    L4(マイクロスプリント: .1a→.1b→.2→.3→.4→.5)
Phase 3: 仕上げ  L5(Visual) → L6(検証) → L7(デプロイ) → L8(受入)
Phase R: リバース R0(証拠収集) → R1(契約抽出) → R2(設計復元) → R3(仮説) → R4(Gap)
Phase S: スクラム HS0(仮説) → HS1(計画) → HS2(PoC) → HS3(検証) → HS4(判定) → HS5(レビュー)
```

ゲート: G1→G1.5→G1R→G2→G3→G4→G5→G6→G7→L8

### HELIX Scrum（検証駆動開発）

要件未確定・実現可能性不明な場合に使う検証駆動開発モデル。

```bash
helix scrum init                          # Scrum モード初期化
helix scrum backlog add --id H001 \       # 仮説登録
  --title "JSON to Image" \
  --question "JSONで画像生成できるか" \
  --acceptance "1024x1024が3秒以内"
helix scrum plan --goal "画像生成検証" \  # スプリント開始
  --hypotheses "H001,H002"
helix scrum poc --hypothesis H001         # PoC 実装を Codex に委譲
helix scrum verify                        # 全検証スクリプト実行
helix scrum decide --hypothesis H001 \    # 判定
  --confirmed
helix scrum review                        # スプリントレビュー + レトロ
```

検証スクリプト（`verify/*.sh`）は蓄積され、毎回全実行でリグレッション検出。
confirmed な仮説は Forward HELIX（L2→）に接続。

詳細は [SKILL_MAP.md](skills/SKILL_MAP.md) を参照。

## スキル一覧（42 スキル）

| カテゴリ | スキル |
|---------|--------|
| workflow/ (18) | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory, reverse-analysis |
| common/ (12) | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ (3) | ui, api, db |
| advanced/ (6) | tech-selection, i18n, external-api, ai-integration, migration, legacy |
| tools/ (2) | ai-coding, ide-tools |
| integration/ (1) | agent-teams |

## CLI ツール

`helix <command>` で統一的に呼び出し可能。PATH に `~/ai-dev-kit-vscode/cli/` を追加するか、`HELIX_HOME` 環境変数を設定。

| コマンド | 用途 |
|---------|------|
| `helix init` | プロジェクト初期化（.helix/ + CLAUDE.md + gitignore + agents） |
| `helix codex --role <role> --task "..."` | ロール別 Codex 委譲（12ロール） |
| `helix gate <G2-G7>` | ゲート自動検証（static + AI チェック） |
| `helix size --files N --lines N [--api] [--db] [--ui]` | タスクサイジング + フェーズスキップ |
| `helix sprint <status\|next\|complete\|reset>` | L4 マイクロスプリント管理 |
| `helix pr [--dry-run]` | ゲート結果から PR 自動生成 |
| `helix reverse <R0-R4\|status>` | Reverse HELIX パイプライン |
| `helix status` | プロジェクト全体の状態表示 |
| `helix test` | 全ツールのセルフテスト |

### Codex ロール（12種）

| ロール | model | 担当 |
|--------|-------|------|
| tl | gpt-5.4 | 設計・レビュー・ゲート判定 |
| se | gpt-5.3-codex | 上級実装（スコア4+） |
| pg | gpt-5.3-codex-spark | 通常実装（スコア1-3） |
| fe | gpt-5.4 | フロントエンド |
| qa | gpt-5.4 | テスト・検証 |
| security | gpt-5.4 | セキュリティ監査 |
| dba | gpt-5.3-codex | DB設計・最適化 |
| devops | gpt-5.3-codex | デプロイ・インフラ |
| docs | gpt-5.3-codex-spark | ドキュメント |
| research | gpt-5.4 | 技術調査 |
| legacy | gpt-5.4 | レガシー分析・Reverse |
| perf | gpt-5.4 | パフォーマンス |

### Claude サブエージェント（FE特化 5種）

| エージェント | 担当 |
|---|---|
| fe-design | UI/UXデザイン・配色・レイアウト |
| fe-component | コンポーネント実装 |
| fe-style | CSS/スタイリング |
| fe-a11y | アクセシビリティ |
| fe-test | フロントテスト |

### Hooks（自動発火）

| Hook | タイミング | 動作 |
|------|----------|------|
| SessionStart | セッション開始時 | HELIX コンテキスト注入 |
| PreToolUse (Write) | CLAUDE.md 作成時 | テンプレート使用を強制 |
| PostToolUse (Edit/Write) | コード変更時 | 設計整合チェック + freeze-break + ADR index |

## ディレクトリ構造

```
setup.sh                          <- ワンライナーセットアップ
cli/
├── helix                     <- 統一エントリポイント
├── helix-codex               <- Codex ロール別委譲
├── helix-gate                <- ゲート自動検証
├── helix-gate-api-check      <- API契約実装突合
├── helix-init                <- プロジェクト初期化
├── helix-size                <- タスクサイジング
├── helix-sprint              <- L4 スプリント管理
├── helix-pr                  <- PR 自動生成
├── helix-reverse             <- Reverse HELIX パイプライン
├── helix-status              <- 全体状態表示
├── helix-test                <- セルフテスト
├── helix-hook                <- PostToolUse hook
├── helix-check-claudemd      <- PreToolUse hook
├── helix-session-start       <- SessionStart hook
├── ROLE_MAP.md               <- 全ロール共通参照
├── lib/
│   ├── yaml_parser.py        <- 軽量YAMLパーサー（PyYAML不要）
│   └── merge_settings.py     <- settings.json hooks マージ
├── roles/                    <- 12ロール定義（.conf）
└── templates/                <- プロジェクト初期化テンプレート
    ├── CLAUDE.md.template
    ├── doc-map.yaml
    ├── gate-checks.yaml
    ├── phase.yaml
    ├── retro.md.template
    └── agents/               <- FE サブエージェント定義
helix/
├── HELIX_CORE.md             <- 共通コア設定（Claude/Codex 共用）
├── CODEX_TL_MODE.md          <- Codex CLI の TL 主導読み替え
├── AGENTS.md.example         <- Codex CLI 用テンプレート
└── sync-codex-skills.sh      <- スキルシンボリックリンク生成
skills/
├── SKILL_MAP.md              <- エントリポイント（@import 対象）
├── common/                   <- 汎用スキル（12）
├── workflow/                  <- ワークフロースキル（18）
├── project/                   <- プロジェクト固有スキル（3）
├── advanced/                  <- 高度なスキル（6）
├── tools/                     <- ツール連携スキル（2）
│   └── ai-coding/references/  <- 手順正本（9ファイル）
└── integration/               <- マルチエージェント連携（1）
```

## カスタマイズ

| ツール | グローバル設定 | プロジェクト固有 |
|--------|--------------|----------------|
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md` / `CLAUDE.local.md` |
| Codex CLI | `~/.codex/AGENTS.md` + `~/.codex/config.toml` | プロジェクトルートの `AGENTS.md` |

Codex CLI のモデル・推論設定は `~/.codex/config.toml` で管理：

```toml
model = "gpt-5.4"
model_reasoning_effort = "xhigh"
```

## Remote SSH / 複数マシン

パスは `~` ベースなので、各マシンで同じ手順を実行すれば動く：

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
bash ~/ai-dev-kit-vscode/setup.sh
```

## ライセンス

MIT
