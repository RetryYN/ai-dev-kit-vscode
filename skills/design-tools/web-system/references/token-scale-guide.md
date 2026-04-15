# デザイントークン詳細設計

> 目的: カラー・タイポグラフィ・スペーシング・Elevation・Border Radius のスケールを体系化し、
> globals.css と Tailwind theme の命名規則を統一する。
> 適用フェーズ: L2 Visual 設計（トークン策定）、L5 Visual Refinement（既存値の正規化）。
> 駆動タイプ: fe / fullstack。

---

## カラートークン3層設計

### 層の役割

| 層 | 命名例 | 目的 |
|----|--------|------|
| Primitive | `--color-blue-500` | 原始値。特定の意味を持たない純粋な色値 |
| Semantic | `--color-primary` | UI ロールに対応した意味付き変数 |
| Component | `--color-button-primary-bg` | コンポーネント固有の変数（多用禁止） |

Primitive → Semantic → Component の順に参照する。Component 層は乱立を防ぐため、
「Semantic では表現できない固有の制約がある場合」にのみ作成する。

### 命名規則

```css
/* --- Primitive 層 --- */
:root {
  /* パターン: --color-{hue}-{shade} */
  --color-blue-50:   #eff6ff;
  --color-blue-100:  #dbeafe;
  --color-blue-400:  #60a5fa;
  --color-blue-500:  #3b82f6;
  --color-blue-700:  #1d4ed8;
  --color-blue-900:  #1e3a8a;

  --color-gray-50:   #f9fafb;
  --color-gray-100:  #f3f4f6;
  --color-gray-400:  #9ca3af;
  --color-gray-700:  #374151;
  --color-gray-900:  #111827;

  --color-red-500:   #ef4444;
  --color-green-500: #22c55e;
  --color-yellow-400: #facc15;
}

/* --- Semantic 層 --- */
:root {
  /* パターン: --color-{role} */
  --color-primary:          var(--color-blue-500);
  --color-primary-hover:    var(--color-blue-700);
  --color-primary-subtle:   var(--color-blue-50);

  --color-text-base:        var(--color-gray-900);
  --color-text-muted:       var(--color-gray-400);
  --color-text-disabled:    var(--color-gray-400);
  --color-text-on-primary:  #ffffff;

  --color-surface:          #ffffff;
  --color-surface-raised:   var(--color-gray-50);
  --color-border:           var(--color-gray-100);
  --color-border-strong:    var(--color-gray-400);

  --color-danger:           var(--color-red-500);
  --color-success:          var(--color-green-500);
  --color-warning:          var(--color-yellow-400);
}

/* --- Component 層（最小限） --- */
:root {
  /* パターン: --color-{component}-{element}-{state} */
  --color-button-primary-bg:    var(--color-primary);
  --color-button-primary-text:  var(--color-text-on-primary);
  --color-button-primary-hover: var(--color-primary-hover);
}
```

### ダークモード対応

**推奨: `data-theme` 属性 + CSS 変数の上書き方式**（`light-` / `dark-` プレフィックスは非推奨）

```css
/* data-theme 属性方式 — Semantic 層を上書きするだけでダークモード完結 */
[data-theme="dark"] {
  --color-primary:       var(--color-blue-400); /* ダークでは明るめのシェード */
  --color-text-base:     var(--color-gray-50);
  --color-surface:       var(--color-gray-900);
  --color-surface-raised: var(--color-gray-700);
  --color-border:        var(--color-gray-700);
}
```

`light-` / `dark-` プレフィックスを分ける方式は変数名が2倍になり、追加/変更コストが高い。
Semantic 層を上書きする方式なら Primitive・Component 層に変更不要。

---

## タイポグラフィスケール

### Modular Scale の選定基準

| スケール比率 | 用途 | 特徴 |
|------------|------|------|
| 1.25（Major Third） | 業務系・情報密度高め | 階層差が小さく、コンパクトに収まる |
| 1.333（Perfect Fourth） | 汎用・バランス型 | Web での事実標準に近い |
| 1.5（Minor Sixth） | LP・読み物系 | 階層差が大きく、見出しが目立つ |

```css
/* 1.25 スケール（ベース 16px）の例 */
:root {
  --font-size-xs:   0.64rem;   /* 10.24px */
  --font-size-sm:   0.8rem;    /* 12.8px  */
  --font-size-base: 1rem;      /* 16px    */
  --font-size-md:   1.25rem;   /* 20px    */
  --font-size-lg:   1.563rem;  /* 25px    */
  --font-size-xl:   1.953rem;  /* 31.25px */
  --font-size-2xl:  2.441rem;  /* 39px    */
  --font-size-3xl:  3.052rem;  /* 48.8px  */
}
```

### 日本語タイポ対応 — line-height トークン

欧文と和文で適切な行間が異なる。トークンで明示的に分ける。

```css
:root {
  /* 欧文 */
  --line-height-en-body:    1.5;
  --line-height-en-heading: 1.25;

  /* 和文 — 行間を広めに取る */
  --line-height-ja-body:    1.75;  /* 読み物: 1.8〜2.0 も検討 */
  --line-height-ja-heading: 1.4;

  /* コード */
  --line-height-code:       1.6;
}
```

```js
// tailwind.config.ts
theme: {
  extend: {
    lineHeight: {
      'en-body':    'var(--line-height-en-body)',
      'en-heading': 'var(--line-height-en-heading)',
      'ja-body':    'var(--line-height-ja-body)',
      'ja-heading': 'var(--line-height-ja-heading)',
    },
  },
},
```

**既存プロジェクトへの適用**: まず本文の `line-height` だけトークン化し、見出しは次スプリント以降。

---

## スペーシングスケール

### 4px / 8px ベース（推奨）、Fibonacci、T-shirt サイズの比較

| 方式 | 値の例 | 向いているケース |
|------|--------|--------------|
| 4px ベース | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 | 情報密度が高い業務系 |
| 8px ベース | 8 / 16 / 24 / 32 / 48 / 64 / 96 | 汎用（shadcn/ui のデフォルト） |
| Fibonacci | 4 / 8 / 12 / 20 / 32 / 52 / 84 | 有機的な見た目を好む場合 |
| T-shirt（xs〜3xl） | 4 / 8 / 16 / 24 / 32 / 48 / 64 | 変数名を覚えやすくしたい場合 |

**推奨**: 8px ベースの T-shirt 命名。Tailwind のデフォルトと親和性が高い。

```css
/* 8px ベース + T-shirt 命名 */
:root {
  --space-xs:  0.25rem;   /* 4px  */
  --space-sm:  0.5rem;    /* 8px  */
  --space-md:  1rem;      /* 16px */
  --space-lg:  1.5rem;    /* 24px */
  --space-xl:  2rem;      /* 32px */
  --space-2xl: 3rem;      /* 48px */
  --space-3xl: 4rem;      /* 64px */
}
```

```js
// tailwind.config.ts
theme: {
  extend: {
    spacing: {
      'xs':  'var(--space-xs)',
      'sm':  'var(--space-sm)',
      'md':  'var(--space-md)',
      'lg':  'var(--space-lg)',
      'xl':  'var(--space-xl)',
      '2xl': 'var(--space-2xl)',
      '3xl': 'var(--space-3xl)',
    },
  },
},
```

---

## Elevation / Shadow スケール

5段階で定義する。算出式: `y-offset = level × 2px`, `blur = level × 4px`, `opacity = 0.06 + level × 0.02`。

```css
:root {
  --shadow-0: none;
  --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.08);   /* カード・入力欄 */
  --shadow-2: 0 2px 8px rgba(0, 0, 0, 0.10);   /* ドロップダウン */
  --shadow-3: 0 4px 16px rgba(0, 0, 0, 0.12);  /* モーダル・シート */
  --shadow-4: 0 8px 32px rgba(0, 0, 0, 0.14);  /* ダイアログ */
}
```

| Level | 変数 | 用途 |
|-------|------|------|
| 0 | `--shadow-0` | フラット（ボーダーで区切る） |
  | 1 | `--shadow-1` | カード、インライン入力欄 |
| 2 | `--shadow-2` | ドロップダウン、Popover |
| 3 | `--shadow-3` | モーダル、Sheet |
| 4 | `--shadow-4` | フルスクリーンダイアログ |

**ダークモードの注意**: ダーク背景では影が視覚的に消える。Level 1〜2 は Elevation の代わりに
`border: 1px solid var(--color-border)` で区切りを表現する方が実用的。

---

## Border Radius スケール

```css
:root {
  --radius-none: 0;
  --radius-sm:   0.25rem;  /* 4px  — 入力欄・Badge */
  --radius-md:   0.5rem;   /* 8px  — Card（shadcn デフォルト） */
  --radius-lg:   0.75rem;  /* 12px — Dialog */
  --radius-xl:   1rem;     /* 16px — Sheet・大きめCard */
  --radius-2xl:  1.5rem;   /* 24px — BottomSheet */
  --radius-full: 9999px;   /* 完全な円 — Avatar・Pill Badge */
}
```

```js
// tailwind.config.ts — shadcn の --radius との共存
theme: {
  extend: {
    borderRadius: {
      sm:   'var(--radius-sm)',
      md:   'var(--radius-md)',
      lg:   'var(--radius-lg)',  // shadcn がデフォルト使用
      xl:   'var(--radius-xl)',
      '2xl':'var(--radius-2xl)',
    },
  },
},
```

**使い分けの原則**:
- `none` / `sm`: ビジネス・業務系（シャープな印象）
- `md` / `lg`: 汎用（shadcn のデフォルト）
- `xl` / `2xl` / `full`: コンシューマー向け・フレンドリーな UI

---

## globals.css / tailwind.config の命名規則まとめ

```
CSS変数:  --{category}-{name}-{modifier}
            category: color / space / font-size / line-height / radius / shadow / z
            name:     役割名 or スケール名
            modifier: hover / focus / disabled / dark (Semantic 層のみ)

Tailwind: theme.extend.{property}.'{name}'
          property と name は CSS 変数の category / name に対応させる
```

**禁止パターン**:
- `--c-primary`（省略しすぎ）
- `--colorPrimary`（camelCase、CSS 変数は kebab-case）
- `--primary-color`（category が後ろ）

---

## 関連資料

- [design-system-process.md](./design-system-process.md) — トークン策定の位置づけ（Step 2/4）
- [design-md-usage.md](./design-md-usage.md) — DESIGN.md → globals.css / Tailwind 変換手順
- [../SKILL.md](../SKILL.md) — FEデザインシステム基盤スキル（shadcn/ui）
- [../../common/visual-design/SKILL.md](../../common/visual-design/SKILL.md) — ビジュアルデザインスキル（配色・タイポグラフィ原則）
- [../../common/visual-design/references/design-md-format.md](../../common/visual-design/references/design-md-format.md) — DESIGN.md 9セクション形式テンプレート
