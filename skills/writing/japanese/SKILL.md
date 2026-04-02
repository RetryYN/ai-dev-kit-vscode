---
name: japanese
description: textlint統合による日本語技術文書の品質自動チェック・AI生成文の不自然さ検出・JTF表記ルール準拠を提供
metadata:
  helix_layer: all
  triggers:
    - ドキュメント作成・更新時
    - README/ADR/API仕様/報告書のレビュー時
    - AI生成テキストの品質確認時
  verification:
    - "textlint --preset ja-technical-writing 0 errors（allowlist 管理済み）"
    - "textlint --preset ai-writing 0 errors"
    - "textlint --preset JTF-style 0 errors"
compatibility:
  claude: true
  codex: true
---

# 日本語技術文書品質スキル（textlint）

## 適用タイミング

このスキルは以下の場合に読み込む：
- ドキュメント作成・更新時
- README/ADR/API仕様/報告書のレビュー時
- AI生成テキストの品質確認時

---

## 1. セットアップ

### インストール

```bash
npm install -D textlint \
  textlint-rule-preset-ja-technical-writing \
  textlint-rule-preset-ai-writing \
  textlint-rule-preset-jtf-style \
  textlint-filter-rule-comments \
  textlint-filter-rule-allowlist
```

### 最小実行

```bash
npx textlint "docs/**/*.md" "README.md"
```

### ベースライン

共通ベースラインは `skills/tools/ai-coding/references/textlint-baseline.md` を参照。

---

## 2. 3プリセットの使い分け

| プリセット | 目的 | 主な検出対象 | 適用優先度 |
|-----------|------|-------------|-----------|
| `ja-technical-writing` | 技術文書の可読性向上 | 冗長表現、読点過多、曖昧語 | 常時 |
| `ai-writing` | AI生成文の不自然さ検出 | 定型句の繰り返し、過剰な断定、意味重複 | AI生成文が含まれるとき必須 |
| `JTF-style` | 日本語表記の統一 | 全角半角、句読点、表記ゆれ | リリース前必須 |

実運用の基本：
1. 作業中は `ja-technical-writing` を中心に回す。
2. PR前に `ai-writing` を追加して機械生成文を精査する。
3. リリース対象文書では `JTF-style` を必ず通す。

---

## 3. allowlist / severity 設定（誤検知対策）

### 方針

- `error`: 誤解を生む表現、規約違反、リリース阻害項目
- `warning`: 文体改善、推奨スタイル、表現上の軽微な差分
- allowlist は「技術用語のみ」を登録し、一般語の除外は避ける

### `.textlintrc` 例

```json
{
  "filters": {
    "comments": true,
    "allowlist": {
      "allow": [
        "CI/CD",
        "OpenAPI",
        "Playwright",
        "TypeScript",
        "SLO"
      ]
    }
  },
  "rules": {
    "preset-ja-technical-writing": {
      "no-mix-dearu-desumasu": { "severity": "error" },
      "ja-no-weak-phrase": { "severity": "warning" }
    },
    "preset-ai-writing": {
      "severity": "error"
    },
    "preset-jtf-style": {
      "severity": "error"
    }
  }
}
```

---

## 4. コードブロック除外設定

### 基本

- `textlint-filter-rule-comments` を有効化する
- Markdown のコードブロックやサンプル出力はルール適用対象から外す

### 局所除外（最小化する）

````markdown
<!-- textlint-disable -->
```bash
curl -H "Authorization: Bearer TOKEN" https://api.example.com
```
<!-- textlint-enable -->
````

運用ルール：
- 除外範囲は最小行数に限定
- 除外理由を直前コメントで明示
- 恒常的な除外は allowlist に寄せる

---

## 5. CI 統合（pre-commit / GitHub Actions）

### pre-commit（Husky + lint-staged）

```bash
npm install -D husky lint-staged
npx husky init
```

`.husky/pre-commit`:

```bash
npx lint-staged
```

`package.json` 例:

```json
{
  "lint-staged": {
    "*.{md,mdx,txt}": "textlint"
  }
}
```

### GitHub Actions

```yaml
name: textlint
on: [pull_request]
jobs:
  textlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx textlint "**/*.{md,mdx,txt}" "!node_modules/**"
```

---

## 6. HELIX ゲート統合（G2/G3/G4/G6）

静的チェックに以下を追加する。

| ゲート | 対象 | 追加チェック |
|-------|------|-------------|
| G2 | 設計書（D-ARCH, ADR） | `textlint`（3プリセット） |
| G3 | 実装前文書（README, D-API, D-DB） | `textlint`（3プリセット） |
| G4 | 実装関連文書（変更された docs） | 差分文書に対する `textlint` |
| G6 | リリース文書（Runbook, 手順書） | `textlint`（3プリセット） |

推奨運用：
- G2/G3 は `warning` 許容可（要記録）
- G4/G6 は `error=0` を必須

---

## 7. よくある日本語品質問題と修正パターン

| 問題 | 典型例 | 修正パターン |
|------|--------|--------------|
| 文体混在 | 「です/である」が混在 | 文書単位で文体を統一 |
| 主語欠落 | 「実行すると成功する」 | 「本コマンドを実行すると...」 |
| 指示語過多 | 「これ」「それ」が多い | 対象名を明示する |
| 表記ゆれ | 「ログイン」「log in」混在 | 用語集を定義して統一 |
| AI特有の冗長 | 同義文の反復 | 一文一義に分割 |
| 曖昧語 | 「適切に」「必要に応じて」 | 条件・閾値を数値化 |

---

## 8. 実行チェックリスト

```bash
npx textlint "**/*.{md,mdx,txt}" "!node_modules/**"
```

- `error` 0件
- allowlist は技術用語のみ
- 局所除外に理由コメントあり
