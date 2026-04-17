---
name: fe-style
description: FE スタイル実装スキル。デザイントークン 3 層定義 (primitive/semantic/component) と CSS/Tailwind の実装方針を担い、visual-design §⑤design の実装層として機能する
metadata:
  helix_layer: L4
  triggers:
    - "L4 スタイル実装時"
    - "L5 Visual Refinement 実装時"
    - "デザイントークン定義時"
    - "Tailwind / styled-components 設計時"
  verification:
    - "design-tokens ファイルが存在する (tokens.json または tailwind.config)"
    - "semantic レイヤーが定義済み"
    - "ハードコード値がトークン参照に置換されている"
compatibility:
  claude: true
  codex: true
---

# FE スタイル実装スキル

## visual-design および design-tools/web-system との関係

```
visual-design §⑤design（配色・タイポ・質感の方針）
  ↓
fe-style（デザイントークン実装 + スタイリング）
  ↓ 成果物: tokens.json / tailwind.config.ts
  ↓
design-tools/web-system（shadcn/ui 等のデザインシステム構築）
```

---

## デザイントークン 3 層構造

### Layer 1: Primitive（原始値）

色・サイズの具体値を定義する。直接コンポーネントからは参照しない。

```json
{
  "color": {
    "blue-50": "#EFF6FF",
    "blue-500": "#3B82F6",
    "blue-900": "#1E3A5F",
    "gray-100": "#F3F4F6",
    "gray-600": "#4B5563",
    "gray-900": "#111827",
    "red-500": "#EF4444",
    "green-500": "#22C55E"
  },
  "spacing": {
    "1": "4px",
    "2": "8px",
    "4": "16px",
    "6": "24px",
    "8": "32px",
    "12": "48px"
  }
}
```

### Layer 2: Semantic（意味付け）

用途に名前を付ける。コンポーネントはこの層を参照する。

```json
{
  "color": {
    "bg-base": "{color.gray-100}",
    "bg-surface": "#FFFFFF",
    "text-primary": "{color.gray-900}",
    "text-secondary": "{color.gray-600}",
    "action-primary": "{color.blue-500}",
    "action-primary-hover": "{color.blue-900}",
    "status-error": "{color.red-500}",
    "status-success": "{color.green-500}"
  },
  "spacing": {
    "xs": "{spacing.1}",
    "sm": "{spacing.2}",
    "md": "{spacing.4}",
    "lg": "{spacing.6}",
    "xl": "{spacing.8}",
    "2xl": "{spacing.12}"
  }
}
```

### Layer 3: Component（コンポーネント固有）

特定コンポーネントの変数。Semantic を参照する。

```json
{
  "button": {
    "bg": "{color.action-primary}",
    "bg-hover": "{color.action-primary-hover}",
    "text": "#FFFFFF",
    "padding-x": "{spacing.md}",
    "padding-y": "{spacing.sm}",
    "radius": "6px"
  }
}
```

---

## Tailwind config テンプレート（抜粋）

```typescript
// tailwind.config.ts — semantic トークンを CSS 変数経由で注入する
theme: {
  extend: {
    colors: {
      'bg-base': 'var(--color-bg-base)',
      'text-primary': 'var(--color-text-primary)',
      'action-primary': 'var(--color-action-primary)',
      'status-error': 'var(--color-status-error)',
    },
    spacing: {
      xs: 'var(--spacing-xs)',   // 4px
      sm: 'var(--spacing-sm)',   // 8px
      md: 'var(--spacing-md)',   // 16px
      lg: 'var(--spacing-lg)',   // 24px
      xl: 'var(--spacing-xl)',   // 32px
      '2xl': 'var(--spacing-2xl)', // 48px
    },
  },
}
```

---

## スタイリング手法の選択基準

| 手法 | 採用条件 | 備考 |
|------|---------|------|
| Tailwind CSS | 新規プロジェクト / デザインシステム統一 | トークンを CSS 変数経由で注入 |
| CSS Modules | チーム内に CSS 知識が深い場合 | スコープ分離が明確 |
| styled-components | コンポーネントと密結合なスタイルが必要な場合 | 動的スタイルに強い |
| shadcn/ui + Tailwind | UI コンポーネントライブラリ活用時 | design-tools/web-system 参照 |

---

## L5 Visual Refinement 時の対応

L5 入場後にスタイル修正が発生した場合の分類:

| 変更種別 | 定義 | 対応 |
|---------|------|------|
| V0 | 見た目のみ（色・余白・フォントサイズ調整） | トークン値の変更のみで対応 |
| V1 | UI 構造変更（コンポーネント追加・削除） | fe-component と連携 |
| V2 | API・契約影響（データ構造変更が必要） | TL へエスカレーション |

---

## ハードコード禁止ルール

```
# 禁止
<div style={{ color: '#3B82F6', padding: '16px' }}>

# 推奨
<div className="text-action-primary p-md">
```

L5 レビュー時、以下を検出して修正依頼する:
- `#` から始まるカラー値のハードコード
- px 値の直書き（tailwind の任意値 `[16px]` 含む）
- `style={}` によるインラインスタイル（動的変数の注入を除く）

---

## チェックリスト

```
[ ] tokens.json または tailwind.config にデザイントークンが定義されているか
[ ] primitive / semantic / component の 3 層が分離されているか
[ ] semantic レイヤーが用途名で命名されているか（色名での命名禁止）
[ ] コンポーネントがトークン参照でスタイリングされているか
[ ] ハードコードカラー・px 値が残存していないか
[ ] L5 時の変更が V0/V1/V2 に分類されているか
```
