# FE テストピラミッドと VRT ガイド

> 目的: Unit / Integration / E2E / VRT の比率目安・Storybook play function の活用パターン・Playwright による VRT・axe-core の自動化手順を整理し、fe-test での実装判断を支援する

---

## 1. FE テストピラミッドの全体像

### ピラミッド構造と比率目安

```
                         VRT
                    ─────────────
                 Playwright E2E
              ────────────────────
         Storybook + play function
       ────────────────────────────────
    Unit（Vitest / Jest）: 関数 / hooks
  ──────────────────────────────────────────
```

| 層 | 対象 | ツール | 比率目安 | 実行速度 |
|---|------|-------|---------|---------|
| Unit | utility 関数 / custom hooks | Vitest / Jest | 60〜70% | 超高速（ms） |
| Storybook | Atoms / Molecules / Organisms の状態確認 | Storybook 8 + play function | 20〜25% | 中速（秒） |
| E2E | 主要ユーザーフロー（P0〜P1） | Playwright | 5〜10% | 低速（分） |
| VRT | 画面全体・コンポーネントの見た目の変化検知 | Chromatic / Percy / Playwright screenshot | 5% | 低速（分） |

### 比率が崩れるアンチパターン

```
E2E に偏りすぎ（逆ピラミッド）:
  問題: テストが遅く、失敗箇所の特定が困難。CI が詰まる
  対策: E2E は P0〜P1 フローのみに絞り、ロジックは Unit へ

Unit のみ（平たいピラミッド）:
  問題: コンポーネントの描画・ARIA の動作が検証できない
  対策: Storybook play function で UI の振る舞いを補完
```

---

## 2. Unit テスト（Vitest / Jest）

### 対象範囲

FE における Unit テストの対象は以下に限定する。コンポーネント描画のテストは Storybook play function を使う。

- utility 関数（日付フォーマット・バリデーション・型変換等）
- custom hooks（useXxx）
- 状態管理ロジック（Zustand / Jotai のストア関数等）

### Vitest でのユーティリティ関数テスト例

```typescript
// lib/format.ts
export const formatPrice = (price: number, currency = 'JPY'): string => {
  return new Intl.NumberFormat('ja-JP', { style: 'currency', currency }).format(price)
}

// lib/format.test.ts
import { describe, it, expect } from 'vitest'
import { formatPrice } from './format'

describe('formatPrice', () => {
  it('日本円でフォーマットする', () => {
    expect(formatPrice(1000)).toBe('￥1,000')
    expect(formatPrice(1234567)).toBe('￥1,234,567')
  })

  it('0円をフォーマットする', () => {
    expect(formatPrice(0)).toBe('￥0')
  })

  it('USD でフォーマットする', () => {
    // Intl.NumberFormat の出力は実行環境依存のため snapshot を使う
    expect(formatPrice(100, 'USD')).toMatchSnapshot()
  })
})
```

### Custom Hook のテスト例（renderHook）

```typescript
// hooks/useCounter.ts
export const useCounter = (initialValue = 0) => {
  const [count, setCount] = React.useState(initialValue)
  const increment = () => setCount(c => c + 1)
  const decrement = () => setCount(c => c - 1)
  const reset = () => setCount(initialValue)
  return { count, increment, decrement, reset }
}

// hooks/useCounter.test.ts
import { renderHook, act } from '@testing-library/react'
import { useCounter } from './useCounter'

describe('useCounter', () => {
  it('初期値が正しく設定される', () => {
    const { result } = renderHook(() => useCounter(5))
    expect(result.current.count).toBe(5)
  })

  it('increment で +1 される', () => {
    const { result } = renderHook(() => useCounter())
    act(() => result.current.increment())
    expect(result.current.count).toBe(1)
  })

  it('reset で初期値に戻る', () => {
    const { result } = renderHook(() => useCounter(10))
    act(() => result.current.increment())
    act(() => result.current.reset())
    expect(result.current.count).toBe(10)
  })
})
```

---

## 3. Storybook と play function

### play function の役割

play function は Storybook の Story 内でユーザーインタラクションをシミュレートする仕組み。単純な表示確認から、実際のクリック・入力・フォーカス操作を伴う統合的な確認まで対応する。

play function を使うことで、以下を1つの Story で確認できる:
- コンポーネントの初期表示
- ユーザー操作後の状態変化
- バリデーションエラーの表示
- ARIA 属性の動作確認

### play function の実装例: ログインフォーム

```typescript
// components/features/auth/LoginForm.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { within, userEvent, expect } from '@storybook/test'
import { LoginForm } from './LoginForm'

const meta: Meta<typeof LoginForm> = {
  title: 'Features/Auth/LoginForm',
  component: LoginForm,
  parameters: { layout: 'centered' },
}
export default meta

type Story = StoryObj<typeof meta>

// 正常フロー: メールとパスワードを入力してログインボタンをクリック
export const SuccessFlow: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)

    // メールアドレスを入力する
    await userEvent.type(
      canvas.getByLabelText('メールアドレス'),
      'user@example.com',
      { delay: 50 }
    )

    // パスワードを入力する
    await userEvent.type(
      canvas.getByLabelText('パスワード'),
      'password123',
      { delay: 50 }
    )

    // ログインボタンをクリックする
    await userEvent.click(canvas.getByRole('button', { name: 'ログイン' }))

    // ローディング状態を確認する（submit 後）
    await expect(canvas.getByRole('button', { name: 'ログイン' })).toHaveAttribute('aria-busy', 'true')
  },
}

// エラーフロー: バリデーションエラーの表示
export const ValidationError: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)

    // 空のままログインボタンをクリックする
    await userEvent.click(canvas.getByRole('button', { name: 'ログイン' }))

    // エラーメッセージが表示されることを確認する
    await expect(canvas.getByText('メールアドレスは必須です')).toBeVisible()
    await expect(canvas.getByRole('textbox', { name: 'メールアドレス' })).toHaveAttribute('aria-invalid', 'true')
  },
}

// a11y 確認: フォーカス操作
export const KeyboardNavigation: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement)

    // Tab キーでフォーカスを移動する
    await userEvent.tab()
    await expect(canvas.getByLabelText('メールアドレス')).toHaveFocus()

    await userEvent.tab()
    await expect(canvas.getByLabelText('パスワード')).toHaveFocus()

    await userEvent.tab()
    await expect(canvas.getByRole('button', { name: 'ログイン' })).toHaveFocus()
  },
}
```

### Storybook 整備の優先順序

```
L4 Sprint .1a（Atoms 実装と同時）:
  Button / Input / Badge / Icon / Label の全 variant Story

L4 Sprint .1b（Molecules 実装と同時）:
  FormField / Card / ListItem の Story（play function で入力・インタラクション確認）

L4 Sprint .2〜.3（Organisms 実装と同時）:
  LoginForm / Header / Modal 等の主要 Organism に play function を追加

L5（Visual Refinement 後）:
  デザインが固まったら VRT の baseline を登録する
```

---

## 4. Playwright E2E テスト

### E2E の対象フロー（優先度別）

| 優先度 | 対象 | 基準 |
|-------|------|------|
| P0 | 認証（ログイン・ログアウト）/ 決済 / コアコンバージョン | 動かないと事業が止まる |
| P1 | CRUD 操作 / フォーム送信 / エラーリカバリー | ユーザーが頻繁に使う |
| P2 | 細部の UI インタラクション | 余裕があれば |

E2E は P0 を優先し、CI 時間を 10 分以内に収めることを目標とする。P2 はバックログに積む。

### テスト設計の原則

```
1. ユーザーの視点で書く（実装詳細ではなくロールやラベルでセレクト）
   良い例: page.getByRole('button', { name: 'ログイン' })
   悪い例: page.locator('#submit-btn')

2. 1テストで1フローを確認する（複数フローを1テストに詰め込まない）

3. テストデータは各テストで独立させる（テスト間の依存を作らない）

4. 待機は明示的に行う（page.waitForURL / page.waitForSelector を使う）
   悪い例: await page.waitForTimeout(1000)
```

### Page Object Model（大規模プロジェクト向け）

```typescript
// e2e/pages/LoginPage.ts
// ページ操作を抽象化し、テストコードの保守性を上げる
export class LoginPage {
  constructor(private readonly page: Page) {}

  async goto() {
    await this.page.goto('/login')
  }

  async fillEmail(email: string) {
    await this.page.getByLabel('メールアドレス').fill(email)
  }

  async fillPassword(password: string) {
    await this.page.getByLabel('パスワード').fill(password)
  }

  async submit() {
    await this.page.getByRole('button', { name: 'ログイン' }).click()
  }

  async login(email: string, password: string) {
    await this.goto()
    await this.fillEmail(email)
    await this.fillPassword(password)
    await this.submit()
  }
}

// e2e/auth.spec.ts
test('ログイン成功 → ダッシュボードへリダイレクト', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.login('user@example.com', 'password123')
  await expect(page).toHaveURL('/dashboard')
})
```

---

## 5. VRT（Visual Regression Test）

VRT は画面スクリーンショットを比較し、意図しない見た目の変化（デザイン回帰）を自動検出する。L5 Visual Refinement 後に baseline を登録し、以降のコード変更で差分が出たときに検出する。

### ツールの選択

| ツール | 特徴 | 選択基準 |
|--------|------|---------|
| Chromatic | Storybook と完全統合。UI レビューワークフローが付属 | Storybook を整備している場合の第一選択 |
| Playwright screenshot | 追加ツール不要。ページ全体またはコンポーネント単位 | Chromatic 契約なし・小規模プロジェクト |
| Percy | Storybook / Playwright 両対応 | エンタープライズ向け |

### Chromatic による VRT

```bash
# インストール
npm install --save-dev chromatic

# 初回 baseline 登録（Chromatic 管理画面でトークン取得後）
npx chromatic --project-token=<TOKEN>
```

```yaml
# .github/workflows/chromatic.yml
name: Chromatic VRT
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  chromatic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Chromatic は git 履歴が必要
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx chromatic --project-token=${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

### Playwright screenshot による VRT

```typescript
// e2e/visual.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Visual Regression Test', () => {
  test('ログインページのスクリーンショット', async ({ page }) => {
    await page.goto('/login')
    // 動的要素（日時等）をマスクする
    await expect(page).toHaveScreenshot('login.png', {
      mask: [page.locator('.dynamic-content')],
      maxDiffPixelRatio: 0.02,  // 2% までの差異は許容
    })
  })

  test('ダッシュボードのスクリーンショット（認証後）', async ({ page }) => {
    // 認証状態を設定してからスクリーンショットを撮る
    await page.context().addCookies([/* 認証クッキー */])
    await page.goto('/dashboard')
    await expect(page).toHaveScreenshot('dashboard.png')
  })

  test('Button コンポーネントの全 variant', async ({ page }) => {
    await page.goto('/storybook/iframe.html?id=ui-button--primary')
    await expect(page.locator('#storybook-root')).toHaveScreenshot('button-primary.png')
  })
})
```

```bash
# 初回 baseline を生成（--update-snapshots で上書き）
npx playwright test e2e/visual.spec.ts --update-snapshots

# 以降の CI では差分がないことを確認
npx playwright test e2e/visual.spec.ts
```

### VRT 運用のポイント

```
[ ] baseline は L5 Visual Refinement 完了後に main ブランチへ commit する
[ ] デザイン変更は意図的な変更として --update-snapshots で baseline を更新する
[ ] 動的コンテンツ（日時・ランダム要素）は mask オプションで除外する
[ ] maxDiffPixelRatio を設定してアンチエイリアス差異による誤検知を減らす
[ ] CI でフォントのレンダリング差異が出る場合は Docker / CI 専用環境を統一する
```

---

## 6. axe-core の E2E への統合

fe-a11y の Playwright + axe-core 設定を E2E テストに組み込む。

```typescript
// e2e/a11y.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

// 主要ページを列挙してまとめて検証する
const PAGES_TO_TEST = [
  { name: 'トップページ', url: '/' },
  { name: 'ログインページ', url: '/login' },
  { name: '新規登録ページ', url: '/register' },
]

for (const { name, url } of PAGES_TO_TEST) {
  test(`${name} - WCAG AA 準拠`, async ({ page }) => {
    await page.goto(url)
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze()

    // 違反がある場合は内容を出力してデバッグしやすくする
    if (results.violations.length > 0) {
      console.log(JSON.stringify(results.violations, null, 2))
    }

    expect(results.violations).toEqual([])
  })
}
```

---

## 7. CI 統合の全体像

```yaml
# .github/workflows/fe-test.yml（概要）
jobs:
  unit:
    # Vitest: utility / hooks
    run: npx vitest run --coverage

  storybook-build:
    # Storybook ビルドの成功確認 + play function 実行
    run: |
      npm run build-storybook
      npx storybook test --url http://localhost:6006

  e2e:
    # Playwright E2E（P0 フロー）
    run: npx playwright test e2e/

  a11y:
    # axe-core 自動検証（E2E と並列実行可）
    run: npx playwright test e2e/a11y.spec.ts

  vrt:
    # VRT（PR 時のみ実行。main へのマージ後に baseline 更新）
    if: github.event_name == 'pull_request'
    run: npx chromatic --project-token=${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

### CI 時間の目安と上限

| ジョブ | 目安 | 上限 |
|--------|------|------|
| Unit | 30秒以内 | 2分 |
| Storybook build | 2〜3分 | 5分 |
| E2E（P0 のみ） | 3〜5分 | 10分 |
| a11y | 2〜3分 | 5分 |
| VRT | 5〜10分 | 15分 |

E2E + a11y は並列実行することで合計 10 分以内に収めることを目標とする。

---

## 8. チェックリスト

```
[ ] Unit テストが utility 関数 / hooks に対して存在するか
[ ] Storybook が起動し、全 Atoms / Molecules の Story が存在するか
[ ] play function で主要 Organism のユーザー操作が確認できるか
[ ] P0 フローの E2E テストが pass しているか
[ ] a11y テスト（axe-core）が E2E に統合されているか
[ ] VRT の baseline が main ブランチに commit されているか
[ ] CI で全ジョブが自動実行されているか
[ ] E2E + a11y の合計 CI 時間が 10 分以内か
[ ] テストセレクタがロール / ラベル基準で書かれているか（id / class セレクタでないか）
[ ] 動的コンテンツ（日時等）が VRT の mask で除外されているか
```
