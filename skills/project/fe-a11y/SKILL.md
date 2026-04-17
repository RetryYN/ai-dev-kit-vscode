---
name: fe-a11y
description: FE アクセシビリティスキル。axe-core 検証と WCAG 2.1 AA 準拠チェックリストを提供し、visual-design の accessibility-design.md 参照と project/ui §6 a11y 項目を統合する
metadata:
  helix_layer: L4
  triggers:
    - "L4 a11y 実装時"
    - "L5 a11y 確認時"
    - "axe-core 検証時"
    - "WCAG 2.1 AA 準拠確認時"
  verification:
    - "axe-core レポートで critical 0 件"
    - "キーボード操作で全機能に到達可能"
    - "コントラスト比 4.5:1 以上 (通常テキスト)"
compatibility:
  claude: true
  codex: true
---

# FE アクセシビリティスキル

## visual-design および project/ui との関係

```
visual-design/references/accessibility-design.md（WCAG 理論・認知 a11y・日本語テキスト）
  ↓
fe-a11y（実装検証・修正手順）
  ↓ 成果物: axe-core レポート / a11y チェックリスト
  ↓
project/ui §6（a11y コード実装パターン参照）
```

---

## WCAG 2.1 AA チェックリスト

### 色コントラスト

```
[ ] 通常テキスト: コントラスト比 4.5:1 以上
[ ] 大きなテキスト (18pt 以上 / 14pt bold 以上): 3:1 以上
[ ] UI コンポーネント（ボタン枠線・フォーカスリング等）: 3:1 以上
[ ] 情報伝達に色のみを使用していない（アイコン・テキスト併用）
```

### キーボード操作

```
[ ] Tab キーで全インタラクティブ要素に到達できる
[ ] フォーカス順序が視覚的な読み順と一致している
[ ] フォーカスインジケータが常に可視（focus-visible:ring-2 等）
[ ] Escape キーでモーダル・ドロップダウンを閉じられる
[ ] Enter / Space キーでボタン・リンクを操作できる
[ ] 矢印キーで選択肢（ラジオ・タブ）を移動できる
```

### ARIA 実装

```
[ ] インタラクティブ要素にアクセシブルな名前がある（aria-label / aria-labelledby）
[ ] 動的コンテンツ更新を aria-live で通知している
[ ] モーダルに role="dialog" と aria-modal="true" が設定されている
[ ] アコーディオン・タブに aria-expanded / aria-selected が設定されている
[ ] エラーメッセージが aria-describedby でフィールドに紐付いている
[ ] 装飾的画像に alt="" が設定されている
[ ] 意味のある画像に具体的な alt テキストがある
```

### フォーム

```
[ ] 全 input に対応する label が存在する (htmlFor / aria-label)
[ ] エラーメッセージがフィールド近傍に配置されている
[ ] 必須項目に aria-required="true" または required 属性がある
[ ] バリデーションエラーは role="alert" または aria-live="assertive" で通知
[ ] タッチターゲットが 44x44px 以上
```

---

## axe-core 検証手順

### ローカル手動検証（ブラウザ拡張）

1. axe DevTools または axe Accessibility Linter をインストールする
2. 対象ページを開き、DevTools → axe タブで "Analyze" を実行する
3. critical / serious を最優先で修正する
4. moderate / minor は P2 として記録する

### Playwright + axe-core 自動検証

```typescript
// e2e/a11y.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('アクセシビリティ検証', () => {
  test('トップページ - WCAG AA 準拠', async ({ page }) => {
    await page.goto('/')
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze()
    expect(results.violations).toEqual([])
  })

  test('ログインフォーム - フォーム a11y', async ({ page }) => {
    await page.goto('/login')
    const results = await new AxeBuilder({ page })
      .include('#login-form')
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()
    expect(results.violations).toEqual([])
  })
})
```

### 優先度分類

| axe 重要度 | 対応優先度 | 対応期限 |
|-----------|---------|---------|
| critical | P0 - ブロッカー | L4 スプリント内に修正 |
| serious | P1 - 要修正 | G4 前に修正 |
| moderate | P2 - 改善提案 | L5 または次スプリント |
| minor | P2 - 改善提案 | バックログへ積む |

---

## よくある実装ミスと修正パターン

### フォーカスリングの消去（禁止）

```css
/* 禁止: フォーカスリングを消さない */
:focus { outline: none; }

/* 推奨: focus-visible で代替 */
:focus-visible { outline: 2px solid var(--color-action-primary); outline-offset: 2px; }
```

### ボタンに aria-label が必要なケース

```tsx
// アイコンのみのボタンは必ず aria-label を付ける
<button aria-label="メニューを開く">
  <MenuIcon />
</button>
```

### スキップリンク（ページ先頭に設置）

```tsx
// すべてのページで設置推奨
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:p-sm focus:bg-bg-surface"
>
  メインコンテンツへスキップ
</a>
```

---

## L5 a11y 確認チェック

L5 Visual Refinement 入場時、以下を追加で確認する:

```
[ ] color-contrast: L5 で変更された配色のコントラスト比を再計測
[ ] focus-visible: 新規追加コンポーネントのフォーカス表示を確認
[ ] motion: prefers-reduced-motion で不要なアニメーションが止まるか
```

---

## チェックリスト

```
[ ] axe-core レポートで critical 0 件か
[ ] キーボードで全機能に到達できるか
[ ] フォーカスインジケータが全インタラクティブ要素で可視か
[ ] タッチターゲットが 44x44px 以上か
[ ] 全フォームフィールドに label または aria-label があるか
[ ] 色のみで情報を伝えていないか
[ ] Playwright + axe の自動検証が CI に組み込まれているか
```
