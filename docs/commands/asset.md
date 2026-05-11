# `helix asset`

`helix asset` は、README や LP、SNS 用の画像 asset preset を生成するためのコマンドです。
preset ごとに解像度とテンプレートを切り替え、Codex 経由で一貫した生成指示を組み立てます。

## 使い方

```bash
helix asset <preset> [options]
```

## Presets

| preset | size | 用途 |
|---|---|---|
| `banner` | 1200x400 | README / OG banner |
| `logo` | 512x512 | brand mark |
| `hero` | 1920x1080 | LP hero section |
| `card` | 800x600 | service / feature card |
| `thumb` | 1200x630 | blog / article thumbnail |
| `icon` | 256x256 | UI icon set |
| `bg` | 1920x1080 | background pattern |

## 共通 options

| option | 説明 |
|---|---|
| `--style <minimal|tech|playful|corp>` | ベースのスタイル指定 |
| `--palette <hex,hex,hex>` | カラーパレット指定 |
| `--motif <text>` | モチーフ説明 |
| `--text <text>` | 画像内テキスト |
| `--out <path>` | 出力先パス |
| `--variants N` | 生成する variant 数 |
| `--model <model>` | 生成モデル上書き |
| `--dry-run` | 実行せず解決後 prompt を表示 |

## 振る舞い

- preset が未指定なら usage を表示して終了します。
- `--variants` は `1-8` の範囲に制限されます。
- `--out` を省略した場合は `docs/assets/<preset>-<timestamp>.png` を使います。
- `--dry-run` は、最終的な prompt と出力先、model、variants を表示します。
- preset ごとの prompt template は `cli/templates/assets/<preset>.md` を参照します。

## 生成フロー

1. preset と options を受け取る
2. preset に応じた size を解決する
3. template を読み込み、`{{preset}}` などの変数を展開する
4. prompt が空なら標準テンプレートを補完する
5. `helix-codex` に task を渡して PNG 生成を依頼する

## 使用例

### banner

```bash
helix asset banner \
  --style corp \
  --palette "#0f172a,#38bdf8,#f8fafc" \
  --motif "code routing dashboard" \
  --text "HELIX Commands" \
  --out docs/assets/banner.png
```

### logo

```bash
helix asset logo \
  --style minimal \
  --palette "#111827,#10b981,#f9fafb" \
  --motif "geometric helix mark" \
  --out docs/assets/logo.png
```

## 関連

- 実装: [`cli/helix-asset`](../../cli/helix-asset)
- テンプレート: [`cli/templates/assets/banner.md`](../../cli/templates/assets/banner.md)
- テンプレート: [`cli/templates/assets/logo.md`](../../cli/templates/assets/logo.md)
- 参照計画: [`PLAN-064`](../plans/PLAN-064-helix-asset-cli.md)

## 補足

- `banner` / `logo` / `hero` / `card` / `thumb` / `icon` / `bg` は、`cli/templates/assets/` 配下の個別テンプレートと連動します。
- `helix asset` は README 画像やブランド asset の初期生成に使う前提で、汎用画像編集ツールではありません。
