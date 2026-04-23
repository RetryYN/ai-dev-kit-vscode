# textlint Baseline（日本語技術文書向け）
> 目的: textlint Baseline（日本語技術文書向け） の要点を把握し、設計・実装判断を行う際のクイックリファレンスとして参照

`writing/japanese` スキルで使用する基準設定。

## 1. デフォルト有効プリセット

- `textlint-rule-preset-ja-technical-writing`
- `textlint-rule-preset-ai-writing`
- `textlint-rule-preset-jtf-style`

## 2. severity 設定

運用基準：

- `error`: 意味解釈を誤らせる問題、規約違反、公開品質を損なう問題
- `warning`: 文体改善、推奨表現、軽微な可読性問題

推奨例：

- `ja-no-weak-phrase`: `warning`
- `no-mix-dearu-desumasu`: `error`
- `ai-writing` 全般: `error`
- `JTF-style` 全般: `error`

## 3. コードブロック除外

- `textlint-filter-rule-comments` を有効化
- コード例は `textlint-disable` コメントで局所除外
- 除外理由をコメントで残す

例：

````markdown
<!-- textlint-disable -->
```bash
npm run build
```
<!-- textlint-enable -->
````

## 4. allowlist テンプレート（技術用語）

```json
{
  "filters": {
    "allowlist": {
      "allow": [
        "CI/CD",
        "OpenAPI",
        "TypeScript",
        "Playwright",
        "Mermaid",
        "D2",
        "SLO",
        "SLA"
      ]
    }
  }
}
```

ルール：

- プロジェクト固有語のみ登録
- 一般語を安易に登録しない
- 使わなくなった語は定期削除

## 5. CI 設定サンプル（`.textlintrc`）

```json
{
  "filters": {
    "comments": true,
    "allowlist": {
      "allow": [
        "CI/CD",
        "OpenAPI",
        "Playwright",
        "TypeScript"
      ]
    }
  },
  "rules": {
    "preset-ja-technical-writing": {
      "ja-no-weak-phrase": { "severity": "warning" },
      "no-mix-dearu-desumasu": { "severity": "error" }
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

実行例：

```bash
npx textlint "**/*.{md,mdx,txt}" "!node_modules/**"
```
