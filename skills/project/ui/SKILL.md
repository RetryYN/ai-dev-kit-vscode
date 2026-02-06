---
name: ui
description: ui関連タスク時に使用
metadata:
  helix_layer: L2
  triggers:
    - UI設計時
    - コンポーネント作成時
    - デザインシステム構築時
  verification:
    - UI仕様一致
    - アクセシビリティ確認
compatibility:
  claude: true
  codex: true
---

# UI設計スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- コンポーネント作成時
- 画面設計時
- UIリファクタリング時

---

## 1. コンポーネント設計

### Atomic Design

```
Atoms      → Button, Input, Icon, Label, Badge
Molecules  → FormField, SearchBox, Card, ListItem
Organisms  → Header, Sidebar, Form, Table, Modal
Templates  → PageLayout, AuthLayout, DashboardLayout
Pages      → LoginPage, DashboardPage, SettingsPage
```

### ディレクトリ構造

```
components/
├── ui/                    # 汎用UI（Atoms/Molecules）
│   ├── button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   ├── input/
│   └── ...
├── features/              # 機能別（Organisms）
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── SignupForm.tsx
│   ├── dashboard/
│   └── ...
└── layouts/               # レイアウト（Templates）
    ├── MainLayout.tsx
    └── AuthLayout.tsx
```

### コンポーネント構成

```typescript
// Button.tsx
import { ComponentProps, forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-white hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'border border-input bg-background hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
)

interface ButtonProps
  extends ComponentProps<'button'>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? <Spinner /> : children}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

---

## 2. 状態管理

### コンポーネント状態

```
Default   → 通常状態
Hover     → マウスオーバー
Focus     → キーボードフォーカス
Active    → クリック/タップ中
Disabled  → 操作不可
Loading   → 読み込み中
Error     → エラー状態
Success   → 成功状態
Empty     → データなし
```

### 実装例

```typescript
// 状態に応じたスタイル
const inputStyles = cva(
  'w-full rounded-md border px-3 py-2 transition-colors',
  {
    variants: {
      state: {
        default: 'border-gray-300 focus:border-primary focus:ring-primary',
        error: 'border-red-500 focus:border-red-500 focus:ring-red-500',
        success: 'border-green-500 focus:border-green-500 focus:ring-green-500',
        disabled: 'bg-gray-100 text-gray-500 cursor-not-allowed',
      },
    },
    defaultVariants: {
      state: 'default',
    },
  }
)
```

---

## 3. フォーム設計

### フォーム構造

```typescript
// React Hook Form + Zod
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  email: z.string().email('有効なメールアドレスを入力してください'),
  password: z.string().min(8, '8文字以上で入力してください'),
})

type FormData = z.infer<typeof schema>

export function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    // 送信処理
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <FormField
        label="メールアドレス"
        error={errors.email?.message}
      >
        <Input {...register('email')} type="email" />
      </FormField>

      <FormField
        label="パスワード"
        error={errors.password?.message}
      >
        <Input {...register('password')} type="password" />
      </FormField>

      <Button type="submit" isLoading={isSubmitting}>
        ログイン
      </Button>
    </form>
  )
}
```

### バリデーションタイミング

```
onBlur:   フィールドを離れた時（推奨）
onChange: 入力の度（リアルタイム）
onSubmit: 送信時のみ
```

---

## 4. レイアウト

### グリッドシステム

```typescript
// 12カラムグリッド
<div className="grid grid-cols-12 gap-4">
  <div className="col-span-12 md:col-span-8">メインコンテンツ</div>
  <div className="col-span-12 md:col-span-4">サイドバー</div>
</div>
```

### スペーシング

```
4px単位で統一

xs:  4px   (space-1)
sm:  8px   (space-2)
md:  16px  (space-4)
lg:  24px  (space-6)
xl:  32px  (space-8)
2xl: 48px  (space-12)
3xl: 64px  (space-16)
```

### コンテナ

```typescript
// 最大幅制限
<div className="container mx-auto px-4">
  {/* max-width: 1280px */}
</div>

// セクション間マージン
<section className="py-12 md:py-16 lg:py-24">
  ...
</section>
```

---

## 5. レスポンシブ

### ブレークポイント

```
sm:  640px   スマホ横
md:  768px   タブレット
lg:  1024px  デスクトップ小
xl:  1280px  デスクトップ
2xl: 1536px  大画面
```

### モバイルファースト

```typescript
// ❌ デスクトップファースト
<div className="flex-row md:flex-col">

// ✅ モバイルファースト
<div className="flex-col md:flex-row">
```

### タッチ対応

```typescript
// タップ領域確保（最低44px）
<button className="min-h-[44px] min-w-[44px] p-2">
  タップ
</button>

// ホバー効果はデスクトップのみ
<button className="md:hover:bg-gray-100">
  ボタン
</button>
```

---

## 6. アクセシビリティ

### 必須対応

```typescript
// alt属性
<img src="..." alt="商品画像: 〇〇" />

// ラベル
<label htmlFor="email">メールアドレス</label>
<input id="email" type="email" />

// aria属性
<button aria-label="メニューを開く" aria-expanded={isOpen}>
  <MenuIcon />
</button>

// ロール
<nav role="navigation" aria-label="メインナビゲーション">
  ...
</nav>
```

### キーボード操作

```typescript
// フォーカス可視化
<button className="focus-visible:ring-2 focus-visible:ring-primary">
  ボタン
</button>

// Escapeで閉じる
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }
  window.addEventListener('keydown', handleKeyDown)
  return () => window.removeEventListener('keydown', handleKeyDown)
}, [onClose])
```

### コントラスト

```
テキスト:     4.5:1 以上
大きなテキスト: 3:1 以上
UIコンポーネント: 3:1 以上
```

---

## 7. パフォーマンス

### 遅延読み込み

```typescript
// コンポーネント
const Modal = lazy(() => import('./Modal'))

// 画像
<img loading="lazy" src="..." alt="..." />

// Next.js Image
import Image from 'next/image'
<Image src="..." alt="..." width={400} height={300} />
```

### メモ化

```typescript
// 高コストな計算
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data)
}, [data])

// コールバック
const handleClick = useCallback(() => {
  onClick(id)
}, [onClick, id])

// コンポーネント
const MemoizedList = memo(List)
```

### 仮想スクロール

```typescript
// 大量リスト表示
import { useVirtualizer } from '@tanstack/react-virtual'

const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
})
```

---

## 8. テスト

### コンポーネントテスト

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('should render with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('should call onClick when clicked', () => {
    const onClick = jest.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

---

## チェックリスト

```
[ ] Atomic Designに従っている
[ ] 状態（hover, focus, disabled等）が定義されている
[ ] レスポンシブ対応している
[ ] アクセシビリティ対応している
[ ] キーボード操作可能
[ ] パフォーマンス最適化している
[ ] テストがある
```
