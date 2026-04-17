---
name: mcp-wrapper-template
description: 外部 MCP サーバを HELIX スキルに wrap するテンプレート
metadata:
  helix_layer: L2
  triggers:
    - MCP サーバを SKILL.md で wrap する時
    - 新規 MCP 統合時
    - 外部ツール HELIX 化時
  verification: []
  attribution: anthropics/skills:mcp-builder (Apache 2.0) — https://github.com/anthropics/skills
compatibility:
  claude: true
  codex: true
---

# MCP Wrapper Template

## 目的

このテンプレートは、外部 MCP サーバを HELIX の `SKILL.md` として標準化するための雛形。

- 既存スキルとの frontmatter 互換を維持
- trigger 設計を統一
- attribution とライセンス表記を明確化
- 利用者が迷わない最小構成を提供

---

## SKILL.md 構造テンプレート

以下の順序を基本とする。

1. frontmatter（必須）
2. スキル名見出し
3. 使用タイミング
4. 入出力契約
5. 設定手順（API キー、接続条件）
6. 呼び出し例
7. fallback 方針
8. 出典・安全運用ルール

### 本文テンプレート（抜粋）

```markdown
# <Skill Title>

## 使用タイミング
- <triggerに対応した具体シーン>

## 入出力契約
### 入力
- <必須入力>
### 出力
- <必須出力>

## 設定手順
- <環境変数名>
- <接続前提>

## 呼び出し例
- <ユースケース 1>
- <ユースケース 2>

## fallback
- <MCP不可時の代替手段>
```

---

## frontmatter 必須項目

必ず以下のキーを含める。

```yaml
---
name: <skill-name>
description: <用途を具体的に>
metadata:
  helix_layer: <all/L2/L4/R0など>
  triggers:
    - <trigger>
  verification:
    - <検証項目>  # テンプレート性質で不要なら []
  attribution: <source + license + URL>
compatibility:
  claude: true
  codex: true
---
```

### 記述ルール

- `name`: ディレクトリ名と一致させる
- `description`: 「何に使うか」を1文で明確化
- `helix_layer`: SKILL_MAP のフェーズ語彙に合わせる
- `verification`: 実行可能な判定文にする
- `attribution`: 元リポジトリ名・ライセンス・URLを併記

---

## triggers 命名規約

trigger は「場面」を短文で記述し、検索可能性を優先する。

- 推奨形式: `<フェーズ> <目的>時`
- 例:
  - `G1R 事前調査時`
  - `R0 証拠収集時`
  - `外部 API 調査時`

---

## attribution 記載ルール

外部由来の知見・構成・実装思想を使う場合は attribution を明記する。

- 記載フォーマット:
  - `<project/repo> (<license>) — <URL>`
- 例:
  - `tavily-mcp (MIT) — https://github.com/tavily-ai/tavily-mcp`
- ライセンス不明のソースは採用前に確認

---

## mcp.json 設定手順

このスキルは実装テンプレートであり、`mcp.json` 自体は編集しない。

1. 対象 MCP サーバの起動コマンドを確認
2. 必須環境変数（API キー等）を洗い出す
3. `mcp.json` にサーバ定義を追加する設計を決める
4. 接続確認コマンドと失敗時 fallback を設計する
5. SKILL.md 本文に設定前提だけを記載する

### 記載例（説明用）

```json
{
  "mcpServers": {
    "example": {
      "command": "npx",
      "args": ["-y", "example-mcp"],
      "env": {
        "EXAMPLE_API_KEY": "${EXAMPLE_API_KEY}"
      }
    }
  }
}
```

---

## 動作確認手順

SKILL.md 追加時は、少なくとも以下を確認する。

1. frontmatter の YAML 構文が有効
2. trigger が用途と一致
3. attribution がライセンス付きで明示
4. 本文に設定手順と fallback がある
5. markdown 構文崩れがない

### 最低チェックコマンド例

```bash
# 見出し構造の目視確認
sed -n '1,220p' skills/tools/<skill-name>/SKILL.md
```

---

## 使い方メモ

- 新規 MCP 統合時は本テンプレートを複製して開始する
- サーバ固有仕様は本文に閉じ込め、frontmatter の互換性を崩さない
- 迷った場合は「入力/出力/検証」を先に固定してから本文を埋める
