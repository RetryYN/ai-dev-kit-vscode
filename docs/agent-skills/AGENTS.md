# AGENTS.md

このファイルは、このリポジトリで作業する AI コーディングエージェント（Claude Code、Codex CLI、Cursor、Copilot、Antigravity など）向けの運用ガイドです。

## Repository Overview

HELIX 開発フレームワーク専用にフォークされた、Claude Code・Codex CLI・その他 AI コーディングエージェント向けのスキル集。  
上流: addyosmani/agent-skills (MIT)。本フォークでは日本語化 + HELIX 9 フェーズ統合 + Codex 12 ロール対応を追加。

## HELIX Codex Integration

HELIX は Codex CLI (`~/ai-dev-kit-vscode/cli/helix-codex`) 経由で 12 ロール別にスキルを実行します。

### Core Rules

- タスクがスキルに該当する場合、該当スキルを必ず参照する
- スキルは `skills/<skill-name>/SKILL.md` に配置
- スキルが適用可能なら直接実装しない
- スキル手順は完全に従う (部分適用禁止)

### Intent → Skill + Codex ロール マッピング

| ユーザー意図 | 発火スキル | Codex ロール |
|------------|----------|------------|
| 新機能・新規追加 | spec-driven-development → incremental-implementation → test-driven-development | tl (設計) / se (実装) |
| 計画・分解 | planning-and-task-breakdown | tl |
| バグ・想定外の挙動 | debugging-and-error-recovery | se |
| コードレビュー | code-review-and-quality | tl |
| リファクタ・簡素化 | code-simplification | pg |
| API・境界設計 | api-and-interface-design | tl |
| UI 実装 | frontend-ui-engineering | fe |
| セキュリティ | security-and-hardening | security |
| 性能最適化 | performance-optimization | perf |
| DB / スキーマ | (今後追加予定) | dba |
| インフラ / CI | ci-cd-and-automation | devops |
| 調査 | source-driven-development | research |
| レガシー対応 | deprecation-and-migration | legacy |
| ドキュメント | documentation-and-adrs, **technical-writing** | docs |
| システム設計規模 | **system-design-sizing** | tl |
| 設計批判レビュー (G2 必須) | **adversarial-review** | tl |
| 負債台帳 (G4 必須) | **debt-register** | tl |
| FE 駆動モック設計 | **mock-driven-development** | fe |
| 仮説検証駆動 | **helix-scrum** | tl |
| 既存コード逆引き設計 | **reverse-helix** | legacy |

### HELIX 9 フェーズ対応

| HELIX Phase | 発火スキル |
|-------------|----------|
| L1 要件定義 | spec-driven-development, idea-refine |
| L1-L2 設計規模 | **system-design-sizing** (HELIX 独自) |
| L2 設計 + 批判レビュー | planning-and-task-breakdown, api-and-interface-design, **adversarial-review** (G2 必須), **mock-driven-development** (fe/fullstack) |
| L3 詳細設計 | planning-and-task-breakdown, api-and-interface-design |
| L4 実装 | incremental-implementation, test-driven-development, context-engineering, source-driven-development, frontend-ui-engineering, **debt-register** (G4 必須) |
| L6 統合検証 | browser-testing-with-devtools, debugging-and-error-recovery |
| G2 設計凍結 / G4 実装凍結 / G6 RC | code-review-and-quality, security-and-hardening, performance-optimization, code-simplification, **adversarial-review** (G2), **debt-register** (G4) |
| L7 デプロイ | git-workflow-and-versioning, ci-cd-and-automation, shipping-and-launch, deprecation-and-migration, documentation-and-adrs |
| S0-S4 仮説検証 (要件未確定) | **helix-scrum** (HELIX 独自) |
| R0-R4 既存コード逆引き | **reverse-helix** (HELIX 独自) |
| 全フェーズ文書品質 | **technical-writing** (HELIX 独自) |

### 実行モデル (Execution Model)

各リクエストに対して:
1. どのスキルが該当するか判断 (1% でも該当するなら発火)
2. 適切なスキルを呼び出し (該当スキルの SKILL.md を Read)
3. スキル手順を厳格に従う
4. 必須工程 (spec, plan 等) が完了してから実装に進む

### Anti-Rationalization (よくある言い訳)

以下の思考は誤りであり、無視すること:
- 「これは小さいからスキル不要」
- 「さっさと実装した方が早い」
- 「先にコンテキストを集めたい」

正しい振る舞い:
- 常にスキルを確認してから着手する

## Orchestration: Personas, Skills, and Commands

このリポジトリには、組み合わせ可能な 3 つのレイヤーがあります。役割が異なるため混同しないでください。

- **Skills** (`skills/<name>/SKILL.md`) — 手順と終了条件を持つワークフロー。How（どう進めるか）。
- **Personas** (`agents/<role>.md`) — 視点と出力形式を定義する役割。Who（誰の視点か）。
- **Slash commands** (`.claude/commands/*.md`) — ユーザー向け起動点。When（いつ起動するか）。

合成ルール: **オーケストレーターはユーザー（または slash command）** です。Persona が他 Persona を呼び出すことはありません。Persona は必要に応じて Skill を呼び出せます。

このリポジトリで推奨するマルチ Persona 構成は **並列 fan-out + merge** のみです。`/ship` では `code-reviewer`、`security-auditor`、`test-engineer` を並列実行し、結果を統合します。どの Persona を呼ぶかを決める「ルーター Persona」は作らず、slash command と意図マッピングで制御してください。

[agents/README.md](agents/README.md) に意思決定マトリクス、[references/orchestration-patterns.md](references/orchestration-patterns.md) に全パターンを記載しています。

HELIX では Opus = PM として Claude Code サブエージェント（`fe-design` / `fe-component` / `fe-style` / `fe-a11y` / `fe-test`）と Codex 12 ロール（`helix-codex --role X`）を組み合わせて運用します。  
また、3 Personas（`code-reviewer` / `test-engineer` / `security-auditor`）は Codex の `tl` / `qa` / `security` ロール視点として使用します。

**Claude Code interop:** `agents/` 内の Persona は Claude Code サブエージェント（このプラグインの `agents/` から自動検出）および Agent Teams のチームメイトとして動作します。プラットフォーム制約として、サブエージェントは他サブエージェントを起動できず、チームの多重ネストもできません。プラグインエージェントは frontmatter の `hooks` / `mcpServers` / `permissionMode` を無視します。

## Creating a New Skill

### Directory Structure

```text
skills/
  <skill-name>/         # kebab-case ディレクトリ名
    SKILL.md            # 必須: スキル定義
    references/         # 任意: 詳細資料
```

### Naming Conventions

- **Skill ディレクトリ**: `kebab-case`（例: `web-quality`）
- **SKILL.md**: 常に大文字、必ずこのファイル名
- **関連ファイル命名**: 用途が伝わる `kebab-case` を推奨

### SKILL.md Format

```markdown
---
name: skill-name
description: 〇〇を通じてエージェントを導く。△△のときに使う。
helix_layer: [L4]
helix_gate: [G4]
codex_role: se
tier: 1
upstream: addyosmani/agent-skills
---

# スキル名

このスキルが扱う目的を簡潔に説明する。

## How It Works（実行手順）

1. 実行前チェック
2. 実行
3. 検証
4. 出力

## Usage（例）

```bash
bash scripts/example.sh [args]
```

**Arguments:**
- `arg1` - 説明（デフォルト: X）

**Examples:**
2-3 個の典型例を記載する。

## Output（出力）

ユーザーが受け取る結果の形式例を記載する。

## Present Results to User（提示形式）

結果の提示テンプレートを記載する。

## Troubleshooting（トラブル時）

よくある失敗と対処法を記載する。
```

### Best Practices for Context Efficiency

スキルはオンデマンドで読み込まれます。起動時に読み込まれるのは名前と description のみで、`SKILL.md` 全文は必要時にのみ読み込まれます。コンテキストを節約するために、以下を守ってください。

- **SKILL.md は 500 行未満を推奨** — 詳細資料は別ファイルへ分離
- **description は具体的に書く** — 発火判定の精度を上げる
- **段階的開示を使う** — 必要な参照だけを読む構造にする
- **大量コードは scripts/ に逃がす** — 会話コンテキスト消費を抑える
- **参照リンクは浅く保つ** — SKILL.md から直接必要資料へ到達させる

### End-User Installation

利用者向けには、以下 2 パターンを案内してください。

**Claude Code:**
```bash
cp -r skills/<skill-name> ~/.claude/skills/
```

**HELIX 本体 (`~/ai-dev-kit-vscode`) からの参照:**
`helix-agent-skills` をサブモジュール or symlink で配置し、`helix skill catalog rebuild` で認識させる。
