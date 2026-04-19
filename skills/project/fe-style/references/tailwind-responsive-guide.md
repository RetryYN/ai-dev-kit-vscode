# Tailwind レスポンシブ設計ガイド

> 目的: mobile-first のブレークポイント戦略・Container Query・ダークモード（class vs media）・CSS カスタムプロパティとのデザイントークン連携を体系化し、fe-style でのスタイリング判断を支援する

---

## 1. mobile-first の原則

Tailwind はデフォルトで mobile-first 設計を採用している。プレフィックスのないユーティリティクラスが最小画面（320px〜）に適用され、ブレークポイントプレフィックス（sm: / md: / lg: / xl:）は「その幅以上」でのみ上書きする。

### 誤った解釈と正しい解釈

```html
<!-- 誤り: 「sm:以下を指定するもの」ではない -->
<div class="sm:hidden"><!-- これは sm(640px) 以上で hidden になる。モバイルでは表示される --></div>

<!-- 正しい: 基本をモバイル向けに書き、大画面で上書きする -->
<div class="block sm:flex lg:grid lg:grid-cols-3">
  <!-- モバイル: block / sm(640px)以上: flex / lg(1024px)以上: 3カラムグリッド -->
</div>
```

### 設計順序

1. モバイル（320〜639px）の表示を先に決める
2. タブレット（640〜1023px）で変更が必要な箇所に `sm:` または `md:` を追加する
3. デスクトップ（1024px以上）で変更が必要な箇所に `lg:` または `xl:` を追加する

---

## 2. ブレークポイント戦略

### 標準ブレークポイント定義

| プレフィックス | 幅 | 典型的なデバイス |
|--------------|-----|----------------|
| （なし） | 0px〜 | スマートフォン縦向き |
| sm: | 640px〜 | スマートフォン横向き / 小型タブレット |
| md: | 768px〜 | タブレット縦向き |
| lg: | 1024px〜 | タブレット横向き / デスクトップ小 |
| xl: | 1280px〜 | デスクトップ標準 |
| 2xl: | 1536px〜 | 大型モニター（一般的なサービスでは不要な場合が多い） |

### ブレークポイントのカスタマイズ

```typescript
// tailwind.config.ts
// プロジェクト固有のブレークポイントを追加する場合
theme: {
  screens: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    // 日本向けの一般的なデスクトップ横幅に合わせる場合
    // '2xl': '1440px',
  },
}
```

### よく使うレスポンシブパターン

#### カラムレイアウトの切り替え

```html
<!-- 1カラム→2カラム→3カラム -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-md">
  <Card />
  <Card />
  <Card />
</div>

<!-- サイドバー付きレイアウト -->
<div class="flex flex-col lg:flex-row gap-xl">
  <main class="flex-1 min-w-0">メインコンテンツ</main>
  <aside class="w-full lg:w-64 shrink-0">サイドバー</aside>
</div>
```

#### テキストサイズのレスポンシブ調整

```html
<!-- モバイルでは小さく、デスクトップで大きくする -->
<h1 class="text-2xl md:text-3xl lg:text-4xl font-bold">
  見出しテキスト
</h1>

<!-- 本文は変更しないケースが多い（可読性は 14〜16px が最適） -->
<p class="text-md leading-relaxed">
  本文テキスト
</p>
```

#### 表示/非表示の切り替え

```html
<!-- モバイルでのみ表示 -->
<div class="block lg:hidden">モバイル専用メニュー</div>

<!-- デスクトップでのみ表示 -->
<nav class="hidden lg:flex">デスクトップナビゲーション</nav>
```

---

## 3. Container Query（コンテナクエリ）

Tailwind v3.2 以降で `@container` ユーティリティが使用可能。画面幅ではなく「親コンテナの幅」に応じてスタイルを変えるため、コンポーネントの再利用性が上がる。

### 従来のレスポンシブとの違い

```
従来（ビューポート基準）:
  グローバルな画面幅に反応 → コンポーネントを単独で再利用しにくい

Container Query（コンテナ基準）:
  親要素の幅に反応 → コンポーネントがどの文脈に置かれても適切なレイアウトを選択できる
```

### 実装例: カードコンポーネント

```html
<!-- 親要素に @container を設定 -->
<div class="@container">
  <!-- コンテナが sm(384px) 以上なら横並び、未満なら縦積み -->
  <div class="flex flex-col @sm:flex-row gap-md">
    <img class="w-full @sm:w-40 @sm:shrink-0" src="..." alt="..." />
    <div>
      <h3 class="text-lg font-semibold">カードタイトル</h3>
      <p class="text-secondary">説明テキスト</p>
    </div>
  </div>
</div>
```

### Container Query のブレークポイント

| プレフィックス | コンテナ幅 |
|--------------|---------|
| @xs: | 320px〜 |
| @sm: | 384px〜 |
| @md: | 448px〜 |
| @lg: | 512px〜 |
| @xl: | 576px〜 |

### 使い分けの判断基準

```
ビューポートベースを使う場面:
- ページ全体のレイアウト（グリッド列数・ナビゲーション表示）
- ヘッダー・フッター・サイドバーの表示切り替え

Container Query を使う場面:
- カード・リストアイテム等の再利用コンポーネント
- サイドバーに入れても・メインエリアに入れても適切に見えるコンポーネント
- ダッシュボードのウィジェット
```

---

## 4. ダークモード戦略

### 2 つのアプローチの比較

| アプローチ | 設定 | メリット | デメリット |
|-----------|-----|---------|---------|
| class ベース | `darkMode: 'class'` | JavaScript でモード切り替え可能・ユーザー設定を永続化できる | class='dark' をルート要素に付与する実装が必要 |
| media ベース | `darkMode: 'media'` | OS 設定に自動追従・実装がシンプル | ユーザーがサービス内でモードを切り替えられない |

### 推奨: class ベース（多くの SaaS / Web サービス向け）

```typescript
// tailwind.config.ts
export default {
  darkMode: 'class',
  // ...
}
```

```tsx
// ルート要素（layout.tsx や _app.tsx）で class を制御する
// next-themes 等のライブラリで管理するのが一般的
<html lang="ja" className={isDark ? 'dark' : ''}>
```

```html
<!-- コンポーネント内での記述 -->
<div class="bg-bg-base dark:bg-gray-900 text-text-primary dark:text-gray-100">
  <!-- モードに応じて自動で背景・テキスト色が切り替わる -->
</div>
```

### CSS カスタムプロパティとの組み合わせ（推奨アーキテクチャ）

ダークモードの切り替えを CSS 変数（カスタムプロパティ）で行い、Tailwind はトークン経由で参照する構成。直接 `dark:` クラスを各コンポーネントに書く方法よりも保守性が高い。

```css
/* globals.css */
:root {
  --color-bg-base: #FFFFFF;
  --color-bg-surface: #F3F4F6;
  --color-text-primary: #111827;
  --color-text-secondary: #4B5563;
  --color-action-primary: #3B82F6;
  --color-status-error: #EF4444;
}

.dark {
  --color-bg-base: #111827;
  --color-bg-surface: #1F2937;
  --color-text-primary: #F9FAFB;
  --color-text-secondary: #9CA3AF;
  --color-action-primary: #60A5FA;
  --color-status-error: #F87171;
}
```

```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      'bg-base': 'var(--color-bg-base)',
      'bg-surface': 'var(--color-bg-surface)',
      'text-primary': 'var(--color-text-primary)',
      'text-secondary': 'var(--color-text-secondary)',
      'action-primary': 'var(--color-action-primary)',
      'status-error': 'var(--color-status-error)',
    },
  },
}
```

```html
<!-- コンポーネント: dark: クラスを書く必要がない -->
<div class="bg-bg-base text-text-primary">
  <p class="text-text-secondary">CSS変数が自動で切り替わる</p>
</div>
```

### ダークモードの検証チェックリスト

```
[ ] ダークモードでコントラスト比 4.5:1 以上を維持しているか
[ ] 画像・SVG がダークモードで視認できるか（白い SVG は暗背景で消える）
[ ] シャドウ（box-shadow）がダークモードで適切か（濃い色では影が見えにくい）
[ ] status-error / status-success がダークモードで読みやすいか
```

---

## 5. CSS カスタムプロパティとデザイントークン連携

### 3 層トークンと CSS 変数のマッピング

fe-style の「デザイントークン 3 層構造」と CSS カスタムプロパティの接続を確認する。

```
Layer 1: Primitive（tokens.json の原始値）
  ↓ 具体的な HEX / px 値を定義
Layer 2: Semantic（CSS カスタムプロパティ）
  ↓ :root / .dark で定義 → Tailwind config で参照
Layer 3: Component（Tailwind クラスまたはコンポーネント固有 CSS）
  → Tailwind ユーティリティクラスを使う限り、ここはほぼ不要
```

### スペーシングトークンの CSS 変数化

```css
/* globals.css */
:root {
  --spacing-xs:  4px;
  --spacing-sm:  8px;
  --spacing-md:  16px;
  --spacing-lg:  24px;
  --spacing-xl:  32px;
  --spacing-2xl: 48px;
  --spacing-3xl: 64px;
}
```

```typescript
// tailwind.config.ts
theme: {
  extend: {
    spacing: {
      xs:   'var(--spacing-xs)',
      sm:   'var(--spacing-sm)',
      md:   'var(--spacing-md)',
      lg:   'var(--spacing-lg)',
      xl:   'var(--spacing-xl)',
      '2xl':'var(--spacing-2xl)',
      '3xl':'var(--spacing-3xl)',
    },
  },
}
```

```html
<!-- 使用例 -->
<div class="p-md gap-lg">
  <!-- padding: 16px / gap: 24px がトークン経由で適用される -->
</div>
```

### 角丸・シャドウのトークン化

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}
```

---

## 6. よくある実装ミスと対策

### ミス1: ハードコードされた任意値の使用

```html
<!-- 禁止: 任意値はトークンの外 -->
<div class="p-[18px] text-[#3B82F6]">

<!-- 推奨: トークン経由 -->
<div class="p-md text-action-primary">
```

### ミス2: モバイルファーストの逆転

```html
<!-- 禁止: デスクトップ基準でモバイルを上書き（Tailwind は機能しない） -->
<div class="flex-row sm-max:flex-col"><!-- sm-max: は標準Tailwindにない -->

<!-- 推奨: モバイルを基本に、ブレークポイントで上書き -->
<div class="flex-col sm:flex-row">
```

### ミス3: 過多な sm: 指定

```html
<!-- 過剰: 全プロパティに sm: が付いていると複雑すぎる -->
<div class="p-sm sm:p-md sm:text-md sm:leading-relaxed sm:rounded-md">

<!-- 整理: モバイルで問題なければ全画面共通で書く -->
<div class="p-sm text-md leading-relaxed rounded-md">
```

---

## 7. チェックリスト

```
[ ] 全スタイルが mobile-first の順序（小画面→大画面）で記述されているか
[ ] ブレークポイントプレフィックスが「○○px以上」として理解されているか
[ ] 再利用コンポーネントで Container Query の検討を行ったか
[ ] ダークモード方式（class / media）がプロジェクト方針と一致しているか
[ ] ダークモードが CSS カスタムプロパティ経由で切り替わるか
[ ] Tailwind の任意値（[16px] 等）を使わず、すべてトークン経由になっているか
[ ] デザイントークンが globals.css の :root と tailwind.config.ts の両方に定義されているか
[ ] ダークモードでコントラスト比が 4.5:1 以上か
```
