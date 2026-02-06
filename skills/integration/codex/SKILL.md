---
name: codex
description: Codex CLIでコード分析・レビュー・大規模リファクタリング実行。PRレビュー、マイグレーション時に使用。Codex未インストールの場合は使用しない。
metadata:
  helix_layer: all
  triggers:
    - PRレビュー時
    - 大規模リファクタリング時
    - コード分析時
  verification:
    - Codex実行成功
    - レビュー結果確認
compatibility:
  claude: true
  codex: true
---

# Codex Integration

## When to Use

| シナリオ | 使用 | 理由 |
|----------|------|------|
| PRセキュリティレビュー | ✅ | Codexの強み（信頼性高い） |
| 大規模リファクタリング | ✅ | 「壊さない」「マージ可能」 |
| マイグレーション | ✅ | 全体把握が得意 |
| アーキテクチャ分析 | ✅ | コードベース理解力 |
| 単純なバグ修正 | ❌ | Claude Codeで十分 |
| 単体テスト作成 | ❌ | Claude CodeのTDDが得意 |
| UI開発 | ❌ | Claude Codeが得意 |

## Prerequisites

```bash
# Codex CLIがインストールされているか確認
codex --version

# 未インストールの場合はこのスキルを使用しない
```

## Execution Commands

### Analysis Mode (read-only)

コードベース分析、レビュー、調査に使用：

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox read-only \
  --full-auto \
  --skip-git-repo-check \
  "分析タスクの内容" 2>/dev/null
```

### Edit Mode (write)

リファクタリング、マイグレーション、コード修正に使用：

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox workspace-write \
  --full-auto \
  "編集タスクの内容" 2>/dev/null
```

### Session Resume

```bash
codex resume --last
```

## Model & Reasoning Options

| モデル | 用途 |
|--------|------|
| `gpt-5-codex` | 標準（推奨）※ Codex 5.3 |
| `gpt-5` | 汎用タスク |

| 推論レベル | 用途 |
|-----------|------|
| `low` | 単純なタスク |
| `medium` | 標準 |
| `high` | 複雑なタスク（推奨） |

## Important: Thinking Tokens

`2>/dev/null` でstderr（thinking tokens）を抑制し、コンテキスト肥大化を防止。

デバッグ時にthinking tokensを見たい場合は `2>/dev/null` を外す。

## Example Workflows

### PRセキュリティレビュー

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox read-only \
  --full-auto \
  "Review the current PR for security vulnerabilities:
   - SQL injection
   - XSS
   - Authentication/Authorization issues
   - Sensitive data exposure
   - Input validation" 2>/dev/null
```

### 大規模リファクタリング

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox workspace-write \
  --full-auto \
  "Refactor the authentication module to use the new JWT library.
   Maintain backward compatibility." 2>/dev/null
```

### アーキテクチャ分析

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox read-only \
  --full-auto \
  "Analyze the codebase architecture:
   - Main components and responsibilities
   - Dependencies between modules
   - Potential improvements
   - Technical debt" 2>/dev/null
```

### マイグレーション

```bash
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox workspace-write \
  --full-auto \
  "Migrate from React class components to functional components with hooks.
   Update all components in src/components/" 2>/dev/null
```

## Role Division: Claude Code vs Codex

```
┌─────────────────────────────────────────┐
│  Claude Code（メインドライバー）          │
│  ・高速実装・イテレーション              │
│  ・TDD                                  │
│  ・デバッグ                              │
│  ・UIコード                              │
│  ・インタラクティブな作業                │
└─────────────┬───────────────────────────┘
              │ 委譲（このスキル）
              ▼
┌─────────────────────────────────────────┐
│  Codex（品質保証）                        │
│  ・コードレビュー（「神レベル」評価あり）   │
│  ・大規模リファクタリング                  │
│  ・マイグレーション                        │
│  ・アーキテクチャ分析                      │
│  ・信頼性が求められる変更                  │
└─────────────────────────────────────────┘
```

## Troubleshooting

### Codex not found
```
Command 'codex' not found
```
→ Codex CLIをインストールするか、このスキルを使用しない

### Permission denied
```
sandbox: permission denied
```
→ `--sandbox workspace-write` を使用（書き込みが必要な場合）

### Rate limit
→ 少し待ってから再実行

### Context too large
→ タスクを分割して実行
