# DESIGN.md → shadcn/ui 適用手順

> 目的: `design-md-format.md` の 9 セクション形式で書かれた DESIGN.md を、
> shadcn/ui プロジェクトの globals.css / Tailwind config / コンポーネントへ変換する具体的手順を示す。
> 適用フェーズ: L4（実装着手時）、L5 Visual Refinement（調整時）。
> 駆動タイプ: fe / fullstack。
>
> 前提: `docs/DESIGN.md` が 9 セクション形式で存在すること。
> 参照: `skills/common/visual-design/references/design-md-format.md`

---

## 全体の流れ

```
DESIGN.md
  § 2. Color Palette     → Step 1: globals.css CSS 変数
  § 3. Typography Rules  → Step 2: Tailwind theme（font / size / line-height）
  § 5. Layout Principles → Step 3: Tailwind spacing + --space-* 変数
  § 4. Component Stylings→ Step 4: shadcn components.json + .tsx クラス属性
  § 7. Do's / Don'ts     → Step 5: ESLint / Stylelint ルール化
  § 9. Agent Prompt Guide→ Step 6: .claude/CLAUDE.md / AGENTS.md 取り込み
```

---

## Step 1: Color Palette → globals.css CSS 変数

DESIGN.md の `§ 2. Color Palette & Roles` を読み、3層トークンに変換する。

```css
/* globals.css */

/* --- Primitive 層 --- */
/* DESIGN.md の hex 値をそのまま変数化 */
:root {
  --color-blue-500: #3b82f6;  /* DESIGN.md Primary */
  --color-blue-700: #1d4ed8;  /* DESIGN.md Primary Dark */
  --color-gray-50:  #f9fafb;  /* DESIGN.md Background */
  --color-gray-900: #111827;  /* DESIGN.md Text Primary */
  --color-red-500:  #ef4444;  /* DESIGN.md Danger */
}

/* --- Semantic 層（shadcn の変数名体系に合わせる） --- */
:root {
  --background:         var(--color-gray-50);
  --foreground:         var(--color-gray-900);
  --primary:            var(--color-blue-500);
  --primary-foreground: #ffffff;
  --muted:              var(--color-gray-100);
  --muted-foreground:   var(--color-gray-400);
  --destructive:        var(--color-red-500);
  --border:             var(--color-gray-200);
  --radius:             0.5rem;
}

/* --- ダークモード --- */
.dark {
  --background:   var(--color-gray-900);
  --foreground:   var(--color-gray-50);
  --primary:      var(--color-blue-400);
  --border:       var(--color-gray-700);
}
```

**注意**: shadcn/ui は `--primary` 等の変数名を内部で使用している。
Primitive 層の名前（`--color-blue-500`）は shadcn と衝突しない。

---

## Step 2: Typography Rules → Tailwind theme

DESIGN.md の `§ 3. Typography Rules` を Tailwind の `theme.extend` に反映する。

```js
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      fontFamily: {
        // DESIGN.md § 3.3 font-family 指定
        sans: [
          '"Noto Sans JP"',
          '"Helvetica Neue"',
          "Arial",
          "sans-serif",
        ],
        mono: [
          "SFMono-Regular",
          "Consolas",
          "monospace",
        ],
      },
      fontSize: {
        // DESIGN.md § 3.4 文字サイズ階層に合わせて調整
        "display": ["2.441rem", { lineHeight: "var(--line-height-ja-heading)" }],
        "h1":      ["1.953rem", { lineHeight: "var(--line-height-ja-heading)" }],
        "h2":      ["1.563rem", { lineHeight: "var(--line-height-ja-heading)" }],
        "h3":      ["1.25rem",  { lineHeight: "var(--line-height-ja-heading)" }],
        "body":    ["1rem",     { lineHeight: "var(--line-height-ja-body)" }],
        "sm":      ["0.875rem", { lineHeight: "var(--line-height-ja-body)" }],
        "caption": ["0.75rem",  { lineHeight: "var(--line-height-ja-body)" }],
      },
      letterSpacing: {
        // DESIGN.md § 3.5 字間
        "ja-heading": "0.05em",
        "ja-body":    "0.04em",
      },
    },
  },
};

export default config;
```

**日本語対応の注意**: `line-height` は CSS 変数で `ja-body: 1.75` / `en-body: 1.5` を分けて定義し（`token-scale-guide.md` 参照）、`fontSize` の第2引数で参照する。

---

## Step 3: Spacing Scale → Tailwind spacing + CSS 変数

DESIGN.md の `§ 5. Layout Principles` の Spacing Scale を変換する。

```css
/* globals.css に追加 */
:root {
  --space-xs:  0.25rem;
  --space-sm:  0.5rem;
  --space-md:  1rem;
  --space-lg:  1.5rem;
  --space-xl:  2rem;
  --space-2xl: 3rem;
  --space-3xl: 4rem;
}
```

```js
// tailwind.config.ts の theme.extend.spacing に追加
spacing: {
  'xs':  'var(--space-xs)',
  'sm':  'var(--space-sm)',
  'md':  'var(--space-md)',
  'lg':  'var(--space-lg)',
  'xl':  'var(--space-xl)',
  '2xl': 'var(--space-2xl)',
  '3xl': 'var(--space-3xl)',
},
```

**既存プロジェクトへの適用**: Tailwind のデフォルト spacing（`p-4`, `mt-8` 等）はそのまま残し、
意味的な名前が必要な箇所から順にトークン参照に切り替える。

---

## Step 4: Component Stylings → shadcn components.json + .tsx

DESIGN.md の `§ 4. Component Stylings` を shadcn コンポーネントに反映する。

### components.json の設定

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

`"cssVariables": true` が shadcn の CSS 変数モードを有効にする。これにより Step 1 で定義した
`--primary` 等が shadcn コンポーネント内で自動適用される。

### .tsx コンポーネントへの反映例

```tsx
// DESIGN.md § 4 の Button Primary 仕様を shadcn Button に反映
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// デフォルト shadcn Button の variant="default" が --primary を使用するため、
// globals.css で --primary を DESIGN.md の値に設定するだけで反映される。

// カスタム variant が必要な場合（DESIGN.md に ghost/outline 仕様がある場合）:
function ActionButton({ className, ...props }: React.ComponentProps<typeof Button>) {
  return (
    <Button
      className={cn(
        "font-medium tracking-ja-heading",  // DESIGN.md の letter-spacing 反映
        className
      )}
      {...props}
    />
  );
}
```

---

## Step 5: Do's / Don'ts → ESLint / Stylelint ルール化

DESIGN.md の `§ 7. Do's and Don'ts` をツールで強制できる範囲でルール化する。

**自動化できるもの** (Stylelint):
```json
// .stylelintrc.json
{
  "rules": {
    "color-no-invalid-hex": true,
    "declaration-property-value-disallowed-list": {
      "color": ["/^#[0-9a-fA-F]{3,6}$/"],
      "background-color": ["/^#[0-9a-fA-F]{3,6}$/"]
    }
  }
}
```

**自動化できるもの** (ESLint + eslint-plugin-tailwindcss):
```json
// .eslintrc.json
{
  "plugins": ["tailwindcss"],
  "rules": {
    "tailwindcss/no-custom-classname": "warn"
  }
}
```

**自動化が難しいもの**（コードレビューで担保）:
- `font-family` のフォールバックチェーン漏れ
- 和文 `line-height: 1.2` 以下の使用
- WCAG コントラスト比の確認（axe-core を CI に組み込む）

---

## Step 6: Agent Prompt Guide → .claude/CLAUDE.md 取り込み

DESIGN.md の `§ 9. Agent Prompt Guide` クイックリファレンスを `.claude/CLAUDE.md` に取り込む。

```markdown
<!-- .claude/CLAUDE.md への追記例 -->

## デザインシステム（DESIGN.md 由来）

UI生成時は以下の値を使用すること:

- Primary Color: var(--primary)（globals.css 参照）
- Font Family: "Noto Sans JP", "Helvetica Neue", sans-serif
- Body Font Size: 1rem / Line Height: 1.75（和文）
- Spacing: var(--space-*) トークン参照（ハードコード禁止）
- Border Radius: var(--radius-md) をデフォルトとする

詳細は docs/DESIGN.md § 9 を参照。
```

`AGENTS.md`（Codex 向け）にも同内容を追記することで、BE/FE 両エージェントが
デザインシステムを前提にコードを生成する。

---

## マッピング表: DESIGN.md 9セクション ⇄ shadcn/ui 構成要素

| DESIGN.md セクション | shadcn/ui 対応物 | 変換手順 |
|---------------------|-----------------|---------|
| 1. Visual Theme | — | DESIGNER.md に転記（方針として） |
| 2. Color Palette | `globals.css` の CSS 変数 | Step 1 |
| 3. Typography Rules | `tailwind.config.*` の fontFamily / fontSize / lineHeight / letterSpacing | Step 2 |
| 4. Component Stylings | `components.json` + 各 .tsx のクラス属性 | Step 4 |
| 5. Layout Principles | `tailwind.config.*` の spacing + `--space-*` 変数 | Step 3 |
| 6. Depth & Elevation | `globals.css` の `--shadow-*` 変数 | `token-scale-guide.md` §Elevation 参照 |
| 7. Do's / Don'ts | ESLint / Stylelint ルール + コードレビューチェック | Step 5 |
| 8. Responsive Behavior | `tailwind.config.*` の screens + コンポーネント内 breakpoint class | 別途実装 |
| 9. Agent Prompt Guide | `.claude/CLAUDE.md` / `AGENTS.md` | Step 6 |

---

## D-VIS-ARCH への組み込み方

L2 Visual 設計書（D-VIS-ARCH）に以下のセクションを追加する:

```markdown
## デザインシステム方針

- DESIGN.md: docs/DESIGN.md（9セクション形式）
- トークン: globals.css（Primitive / Semantic 層）
- コンポーネント: shadcn/ui + components.json
- 変換手順: skills/design-tools/web-system/references/design-md-usage.md

### トークン体系
（token-scale-guide.md の3層設計を記載）

### ダークモード方針
（globals.css の .dark / data-theme 切替方針を記載）
```

---

## 関連資料

- [design-system-process.md](./design-system-process.md) — 6ステップ構築プロセス（本手順の位置づけ）
- [token-scale-guide.md](./token-scale-guide.md) — トークン詳細設計（スケール・命名規則）
- [../SKILL.md](../SKILL.md) — FEデザインシステム基盤スキル（shadcn/ui セットアップ）
- [../../common/visual-design/SKILL.md](../../common/visual-design/SKILL.md) — ビジュアルデザインスキル
- [../../common/visual-design/references/design-md-format.md](../../common/visual-design/references/design-md-format.md) — DESIGN.md 9セクション形式テンプレート
