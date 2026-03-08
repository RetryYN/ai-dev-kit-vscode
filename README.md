# ai-dev-kit-vscode

Claude Code / Codex CLI 向けの HELIX スキルフレームワーク。
`~/.claude/CLAUDE.md` に 1 行追加するだけで、41 のスキルが全プロジェクトで使えるようになる。

## セットアップ

```bash
# 1. クローン
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode

# 2. グローバル CLAUDE.md に追加
mkdir -p ~/.claude
echo '@~/ai-dev-kit-vscode/skills/SKILL_MAP.md' >> ~/.claude/CLAUDE.md
```

これで次回の Claude Code セッションから有効になる。

## しくみ

```
~/.claude/CLAUDE.md          <- 全プロジェクト共通（User レベル）
  └── @import SKILL_MAP.md   <- 41 スキルの一覧（常時読み込み、~100行）
        └── 各 SKILL.md      <- タスクに応じてオンデマンド Read
```

- `~/.claude/CLAUDE.md` は Claude Code が**毎セッション自動で読み込む**
- `@import` で SKILL_MAP.md を取り込み、Claude にスキル一覧を認識させる
- 個々のスキルは triggers に該当したとき Claude が自発的に Read する
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

`~/.claude/CLAUDE.md` に個人設定を追加できる：

```markdown
# Global Settings

@~/ai-dev-kit-vscode/skills/SKILL_MAP.md

- 日本語で応答する
```

プロジェクト固有の設定は各プロジェクトの `CLAUDE.md` または `CLAUDE.local.md` に書く。

## Remote SSH / 複数マシン

`~/.claude/CLAUDE.md` 内のパスは `~` ベースなので、各マシンで同じ手順を実行すれば動く：

```bash
git clone https://github.com/RetryYN/ai-dev-kit-vscode.git ~/ai-dev-kit-vscode
# ~/.claude/CLAUDE.md をコピー or dotfiles で同期
```

## ライセンス

MIT
