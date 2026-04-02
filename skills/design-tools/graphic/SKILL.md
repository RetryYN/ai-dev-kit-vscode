---
name: graphic
description: Vercel Satori等によるSVG/OGP画像の動的生成でブログ・リリースのアイキャッチ画像を自動作成
metadata:
  helix_layer: L8
  triggers:
    - ブログ記事公開時
    - リリースノート作成時
    - OGP画像が必要な時
  verification:
    - "SVG/PNG レンダリング成功"
    - "フォント埋め込み確認"
compatibility:
  claude: true
  codex: true
---

# SVG/OGP画像生成スキル（Satori）

## 適用タイミング

このスキルは以下の場合に読み込む：
- ブログ記事公開時
- リリースノート作成時
- OGP画像が必要な時

---

## 1. Satori セットアップ手順

```bash
npm install satori @resvg/resvg-js
```

最低構成：
- `scripts/ogp/generate.ts`（生成ロジック）
- `assets/fonts/`（日本語フォント）
- `public/ogp/`（出力先）

実行例（TypeScript）：

```bash
npx tsx scripts/ogp/generate.ts
```

---

## 2. OGPテンプレート（ブログ用・リリース用）

### ブログ用

- 主タイトル
- サブタイトル（カテゴリ）
- 公開日
- サイト名

### リリース用

- バージョン
- 主要変更点（3点まで）
- リリース日
- プロダクト名

テンプレート設計ルール：
- 1200x630 を標準サイズにする
- テキストは2行以内を基本にし、省略記号で崩れを防ぐ
- 背景と文字色のコントラストを確保する

---

## 3. SVG テンプレートパターン

最小例：

```ts
import satori from 'satori'
import { Resvg } from '@resvg/resvg-js'
import fs from 'node:fs/promises'

const svg = await satori(
  {
    type: 'div',
    props: {
      style: {
        width: '1200px',
        height: '630px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: '#0b132b',
        color: '#ffffff',
        padding: '48px',
      },
      children: [
        { type: 'div', props: { children: 'Release v1.2.0' } },
        { type: 'div', props: { children: '認証フローを改善' } },
      ],
    },
  },
  {
    width: 1200,
    height: 630,
    fonts: [],
  }
)

const png = new Resvg(svg).render().asPng()
await fs.writeFile('public/ogp/release-v1-2-0.png', png)
```

---

## 4. 日本語フォントの埋め込み方法

推奨手順：
1. `assets/fonts/NotoSansJP-Regular.ttf` を配置
2. 生成時に `fonts` 配列へ読み込んで渡す
3. 日本語長文でレンダリング確認する

フォント設定例：

```ts
import fs from 'node:fs'

const fontData = fs.readFileSync('assets/fonts/NotoSansJP-Regular.ttf')

const options = {
  width: 1200,
  height: 630,
  fonts: [
    {
      name: 'Noto Sans JP',
      data: fontData,
      weight: 400,
      style: 'normal',
    },
  ],
}
```

確認観点：
- 文字化けがない
- 太字/通常の切替が想定通り
- 環境差分でレイアウト崩れがない

---

## 5. CIでの自動生成（ブログdeploy連携）

例: GitHub Actions

```yaml
name: ogp-generate
on:
  push:
    paths:
      - "content/blog/**"
      - "scripts/ogp/**"
      - "assets/fonts/**"
jobs:
  build-ogp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx tsx scripts/ogp/generate.ts
      - run: test -f public/ogp/latest.png
```

運用ルール：
- 記事 slug ごとに OGP を生成する
- 既存画像は差分更新のみ行う
- 失敗時は deploy を止め、原因をログ化する

---

## 6. 出力使い分け

| 形式 | 用途 | 備考 |
|------|------|------|
| SVG | 中間生成物、再編集向け | 軽量で差分管理しやすい |
| PNG | OGP配布向け | SNS表示互換性が高い |

推奨フロー：
1. SatoriでSVG生成
2. ResvgでPNG化
3. `public/ogp` へ保存

---

## 7. 完了判定

- SVG/PNG のレンダリング成功
- フォント埋め込み確認済み
- ブログ deploy 時に OGP 自動生成フローが実行可能
