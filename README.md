# ai-dev-kit-vscode

Claude Code / Codex CLI 向けの HELIX スキルフレームワーク。
41 のスキルが全プロジェクトで使えるようになる。

## セットアップ

### Claude Code

```bash
# 1. クローン
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode

# 2. グローバル CLAUDE.md に追加
mkdir -p ~/.claude
cat >> ~/.claude/CLAUDE.md << 'EOF'
@~/ai-dev-kit-vscode/skills/SKILL_MAP.md
@~/ai-dev-kit-vscode/helix/HELIX_CORE.md
EOF
```

### Codex CLI

```bash
# 1. クローン（済みならスキップ）
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode

# 2. スキルをシンボリックリンク
bash ~/ai-dev-kit-vscode/helix/sync-codex-skills.sh

# 3. AGENTS.md をコピー
cp ~/ai-dev-kit-vscode/helix/AGENTS.md.example ~/.codex/AGENTS.md
```

### 共通設定

`helix/HELIX_CORE.md` に Claude Code / Codex CLI 共通のフロー定義（L1-L8、ゲート、モデル割当）を配置。
ツール固有の設定は `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` にそれぞれ記載。

## しくみ

```
Claude Code:
  ~/.claude/CLAUDE.md           <- @import で SKILL_MAP.md + HELIX_CORE.md を取り込み
    └── 各 SKILL.md             <- タスクに応じてオンデマンド Read

Codex CLI:
  ~/.codex/AGENTS.md            <- HELIX_CORE.md を Read 指示
  ~/.codex/skills/helix-*/      <- 41 スキルのシンボリックリンク
    └── SKILL.md frontmatter    <- name + description で自動発見
```

- 個々のスキルは triggers に該当したとき自発的に Read する
- 全スキル一括読み込みはしない（コンテキストウィンドウ節約）

## HELIX 開発フロー

```
Phase 1: 計画    L1(要件) → L2(設計) → L3(詳細設計+API契約+工程表)
Phase 2: 実装    L4(マイクロスプリント: .1→.2→.3→.4→.5)
Phase 3: 仕上げ  L5(Visual) → L6(検証) → L7(デプロイ) → L8(受入)
```

ゲート: G1→G1.5→G1R→G2→G3→G4→G5→G6→G7→L8

詳細は [SKILL_MAP.md](skills/SKILL_MAP.md) を参照。

## スキル一覧（41 スキル）

| カテゴリ | スキル |
|---------|--------|
| workflow/ (17) | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory |
| common/ (12) | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ (3) | ui, api, db |
| advanced/ (6) | tech-selection, i18n, external-api, ai-integration, migration, legacy |
| tools/ (2) | ai-coding, ide-tools |
| integration/ (1) | agent-teams |

## ディレクトリ構造

```
helix/
├── HELIX_CORE.md             <- 共通コア設定（Claude/Codex 共用）
├── AGENTS.md.example         <- Codex CLI 用テンプレート
└── sync-codex-skills.sh      <- スキルシンボリックリンク生成
skills/
├── SKILL_MAP.md              <- エントリポイント（@import 対象）
├── common/                   <- 汎用スキル（12）
├── workflow/                  <- ワークフロースキル（17）
├── project/                   <- プロジェクト固有スキル（3）
├── advanced/                  <- 高度なスキル（6）
├── tools/                     <- ツール連携スキル（2）
│   └── ai-coding/references/  <- 手順正本（workflow-core, gate-policy 等）
└── integration/               <- マルチエージェント連携（1）
```

## カスタマイズ

`~/.claude/CLAUDE.md`（Claude Code）や `~/.codex/AGENTS.md`（Codex CLI）に個人設定を追加できる。
プロジェクト固有の設定は各プロジェクトの `CLAUDE.md` / `CLAUDE.local.md` に書く。

## Remote SSH / 複数マシン

`~/.claude/CLAUDE.md` 内のパスは `~` ベースなので、各マシンで同じ手順を実行すれば動く：

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
# ~/.claude/CLAUDE.md をコピー or dotfiles で同期
```

## ライセンス

MIT
