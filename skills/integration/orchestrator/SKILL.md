---
name: orchestrator
description: 複数AIエージェント（Claude Code, Codex, Gemini）を協調実行。大規模プロジェクト、多角的分析、パイプライン処理時に使用。
metadata:
  helix_layer: all
  triggers:
    - 複数AI協調時
    - 大規模プロジェクト時
    - パイプライン処理時
  verification:
    - エージェント連携成功
    - 結果統合完了
compatibility:
  claude: true
  codex: true
---

# Multi-Agent Orchestration

## When to Use

| シナリオ | 使用 | パターン |
|----------|------|----------|
| 複数の視点でレビュー | ✅ | 並列分析 |
| 計画してから実装 | ✅ | シーケンシャル |
| GeminiとCodexで協調レビュー | ✅ | 協調分析 |
| 大規模システム設計 | ✅ | マルチエージェント |
| 単純なバグ修正 | ❌ | 単一エージェントで十分 |

## Agent Capabilities

| エージェント | 得意タスク | CLI |
|-------------|-----------|-----|
| **Claude Code** | 高速実装、TDD、UI開発、デバッグ | `claude` |
| **Codex** | コードレビュー、大規模リファクタ、品質保証 | `codex exec` |
| **Gemini CLI** | プラン作成、フロント検証、ブラウザテスト | `gemini` |

## Execution Patterns

### Pattern 1: 協調分析（Collaborative Analysis）

複数エージェントが同じタスクを分析し、結果を統合。

```
User: "Use Gemini and Codex to collaboratively review the authentication flow"

実行フロー:
1. gemini CLI → 認証フロー分析（設計観点）
2. codex exec → 認証フロー分析（コード品質観点）
3. Claude Code → 両方の結果を統合してレポート
```

**実行コマンド例:**

```bash
# Step 1: Gemini分析
gemini "Review the authentication flow for design issues and security concerns"

# Step 2: Codex分析
codex exec -m gpt-5-codex \
  --sandbox read-only \
  --full-auto \
  "Review the authentication flow for code quality and security vulnerabilities" 2>/dev/null

# Step 3: Claude Codeが統合（自動）
```

### Pattern 2: 並列実行（Parallel Execution）

複数エージェントが同時に異なる観点で分析。

```
User: "Have all available CLIs analyze this architecture in parallel"

実行フロー:
1. gemini CLI → アーキテクチャ分析（設計観点）
2. codex exec → アーキテクチャ分析（コード品質観点）
3. Claude Code → アーキテクチャ分析（実装観点）
4. マージレポート生成
```

### Pattern 3: シーケンシャルパイプライン（Sequential Pipeline）

各エージェントが順番にタスクを処理。前のエージェントの出力を次が引き継ぐ。

```
User: "Use Gemini to plan, then Codex to implement"

実行フロー:
1. gemini CLI → 計画作成
2. 計画をファイルに保存（plan.md）
3. codex exec → plan.mdを参照して実装
4. Claude Code → 結果を検証
```

**実行コマンド例:**

```bash
# Step 1: Geminiで計画
gemini "Create a detailed refactoring plan for the user module" > plan.md

# Step 2: Codexで実装
codex exec -m gpt-5-codex \
  --sandbox workspace-write \
  --full-auto \
  "Implement the refactoring plan in plan.md" 2>/dev/null
```

## Workflow Levels

| レベル | 説明 | 例 | エージェント数 |
|--------|------|-----|---------------|
| Level 1 | 即座実行 | "Fix typo" | 1 |
| Level 2 | 軽量計画 | "Add JWT auth" | 1 |
| Level 3 | 標準計画+セッション | "Payment integration" | 1-2 |
| Level 4 | マルチエージェント | "Design real-time system" | 2-3 |

## Best Practices

### 1. 適切なエージェント選択

- **実装** → Claude Code（高速、インタラクティブ）
- **レビュー** → Codex（信頼性、品質保証）
- **計画** → Gemini（ブラウザ、フロント検証）

### 2. コンテキスト引き継ぎ

エージェント間でコンテキストを引き継ぐ場合、明示的にファイルに保存：

```bash
# 計画をファイルに保存
gemini "Create plan" > plan.md

# 計画を参照して実装
codex exec "Implement plan.md" 2>/dev/null
```

### 3. 結果の統合

複数エージェントの結果は Claude Code が統合してユーザーに報告。

### 4. エラーハンドリング

エージェントが利用不可能な場合、利用可能なエージェントのみで実行。

## Prerequisites

### Gemini CLI
```bash
gemini --version
```

### Codex CLI
```bash
codex --version
```

## Troubleshooting

### エージェントが見つからない
→ 該当CLIをインストールするか、利用可能なエージェントのみで実行

### コンテキスト引き継ぎ失敗
→ 中間結果をファイルに保存して明示的に参照

### タイムアウト
→ タスクを小さく分割して順次実行

### 結果の矛盾
→ 両方の観点を併記し、ユーザーに判断を委ねる
