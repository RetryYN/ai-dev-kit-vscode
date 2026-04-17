---
name: fe-test
description: FE テストスキル。Storybook / Playwright E2E / VRT (Visual Regression Test) の設計と実装を担い、common/testing スキルの FE 特化版として機能する
metadata:
  helix_layer: L4
  triggers:
    - "L4 FE テスト実装時"
    - "L6 FE E2E 時"
    - "Storybook 整備時"
    - "VRT (Visual Regression Test) 導入時"
  verification:
    - "Storybook が起動する"
    - "主要フロー E2E が pass"
    - "VRT baseline が commit 済み"
compatibility:
  claude: true
  codex: true
---

# FE テストスキル

## common/testing との差分

common/testing は BE/FE 共通のテスト戦略全体を扱う。fe-test は FE に特化した以下の 3 領域を担当する:

- Storybook によるコンポーネントカタログ + 単体確認
- Playwright E2E によるユーザーフロー検証
- VRT（Visual Regression Test）による見た目の変化検知

```
common/testing（全体テスト戦略・TDD・ユニットテスト原則）
  ↓
fe-test（FE 特化: Storybook / E2E / VRT）
```

---

## テスト戦略（FE テストピラミッド）

```
                VRT
              ─────────
            Playwright E2E
          ─────────────────
        Storybook (コンポーネント確認)
      ──────────────────────────────
    Unit (ユーティリティ関数 / hooks)
  ──────────────────────────────────────
```

| 層 | 対象 | ツール | 目的 |
|---|------|-------|------|
| Unit | utility 関数 / custom hooks | Vitest / Jest | ロジック正確性 |
| Storybook | Atoms / Molecules / Organisms | Storybook 8 | コンポーネント動作・状態確認 |
| E2E | 主要ユーザーフロー | Playwright | フロー全体の結合確認 |
| VRT | 画面全体・コンポーネント | Chromatic / Percy | デザイン回帰防止 |

---

## Storybook Story テンプレート

```typescript
// components/ui/button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: { layout: 'centered' },
  tags: ['autodocs'],
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'outline', 'ghost', 'destructive'] },
    size: { control: 'radio', options: ['sm', 'md', 'lg'] },
  },
}

export default meta
type Story = StoryObj<typeof meta>

export const Primary: Story = {
  args: {
    variant: 'primary',
    size: 'md',
    children: 'ボタン',
  },
}

export const Loading: Story = {
  args: { variant: 'primary', isLoading: true, children: '読み込み中' },
}

export const Disabled: Story = {
  args: { variant: 'primary', disabled: true, children: '無効' },
}
```

### Storybook 整備優先順

1. Atoms 全種（Button, Input, Badge, Icon 等）
2. Molecules（FormField, Card, ListItem 等）
3. Organisms（ページの主要フォーム・ナビゲーション）

---

## Playwright E2E テンプレート

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'

test.describe('認証フロー', () => {
  test('ログイン成功 → ダッシュボードへリダイレクト', async ({ page }) => {
    await page.goto('/login')

    await page.getByLabel('メールアドレス').fill('user@example.com')
    await page.getByLabel('パスワード').fill('password123')
    await page.getByRole('button', { name: 'ログイン' }).click()

    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByRole('heading', { level: 1 })).toContainText('ダッシュボード')
  })

  test('ログイン失敗 → エラーメッセージ表示', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('メールアドレス').fill('wrong@example.com')
    await page.getByLabel('パスワード').fill('wrongpassword')
    await page.getByRole('button', { name: 'ログイン' }).click()
    await expect(page.getByRole('alert')).toBeVisible()
    await expect(page).toHaveURL('/login')
  })
})
```

### E2E カバレッジ基準

| 優先度 | 対象フロー |
|-------|---------|
| P0 | 認証（ログイン・ログアウト）・決済・主要コンバージョン |
| P1 | CRUD 操作・フォーム送信・エラー回復 |
| P2 | 細部の UI インタラクション |

---

## VRT 導入手順（Chromatic）

```bash
# 1. インストール
npm install --save-dev chromatic

# 2. 初回 baseline 登録（project-token は Chromatic 管理画面で取得）
npx chromatic --project-token=<TOKEN>
```

CI（GitHub Actions）では `CHROMATIC_PROJECT_TOKEN` をシークレットに登録し、
`npx chromatic --project-token=${{ secrets.CHROMATIC_PROJECT_TOKEN }}` を実行する。

Percy を使用する場合は `@percy/cli @percy/playwright` をインストールし、
`percy exec -- playwright test` で実行する。

---

## L6 統合検証時の FE テスト

L6 フェーズでは以下を追加実行する:

```
[ ] 本番相当環境（staging）で E2E 全 P0 フローを再実行
[ ] VRT の baseline を staging で更新・承認
[ ] パフォーマンス計測（Lighthouse / Web Vitals）と閾値確認
[ ] モバイル（375px）・タブレット（768px）での E2E 実行
```

---

## チェックリスト

```
[ ] Storybook が起動し全 Atoms/Molecules の Story が存在するか
[ ] 主要フロー（P0）の E2E テストが pass しているか
[ ] VRT baseline が main ブランチに commit されているか
[ ] CI で Storybook build と E2E が自動実行されているか
[ ] axe-core a11y 検証が E2E に組み込まれているか (fe-a11y 参照)
[ ] 各テストの役割分担が明確か (Unit / Storybook / E2E / VRT)
```
