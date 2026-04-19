# コンポーネント Props パターンカタログ

> 目的: TypeScript + React における代表的な Props 設計パターン（Compound / Render Props / forwardRef / Discriminated Union / 状態管理分離）を実例とともに整理し、fe-component での型定義時の判断基準を提供する

---

## 1. パターン選択の指針

Props 設計は「コンポーネントをどこで・誰が使うか」から逆算する。コンポーネントの利用者が増えるほど、柔軟性（拡張性）と単純さ（使いやすさ）のトレードオフが大きくなる。

### 選択フロー

```
単純な表示コンポーネントか？
  ↓ Yes → 基本 Props パターン
  ↓ No
複数のサブ要素が協調動作するか？（タブ・アコーディオン・セレクト等）
  ↓ Yes → Compound Components
  ↓ No
呼び出し側がレンダリングをコントロールしたいか？
  ↓ Yes → Render Props または children as function
  ↓ No
DOM 要素を直接操作するか？（フォーカス・スクロール等）
  ↓ Yes → forwardRef
  ↓ No
variant によって Props が排他的に変わるか？
  ↓ Yes → Discriminated Union Props
```

---

## 2. 基本 Props パターン

最もシンプルな形。Atom レベルのコンポーネントに適用する。

### 基本原則

```typescript
// Bad: any を使わない。型安全性が失われる
interface ButtonProps {
  onClick: any
  children: any
}

// Good: 具体的な型を定義する
interface ButtonProps {
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void
  children: React.ReactNode
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}
```

### HTML 属性の継承

ネイティブ要素をラップする Atom は `React.ComponentProps` を活用する。

```typescript
// Button.tsx
// 'button' の全ネイティブ属性を継承しつつ、独自 Props を追加する
interface ButtonProps extends React.ComponentProps<'button'> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  isLoading?: boolean
}

const Button = ({ variant = 'primary', size = 'md', isLoading, children, ...rest }: ButtonProps) => {
  return (
    <button
      {...rest}
      disabled={rest.disabled || isLoading}
      aria-busy={isLoading}
    >
      {isLoading ? <Spinner /> : children}
    </button>
  )
}
```

### チェックリスト（基本 Props）

```
[ ] optional (?) と required の使い分けが意図的か
[ ] デフォルト値が関数シグネチャかコンポーネント内で定義されているか
[ ] children の型が React.ReactNode か（string のみなら string）
[ ] ネイティブ要素をラップする場合、...rest でネイティブ属性を引き継いでいるか
```

---

## 3. Discriminated Union Props

`variant` によって Props の形が変わる場合に使う。型安全に「このvariantにはこのPropが必要」を表現できる。

### 適用場面

- Alert コンポーネント（type: 'info' | 'warning' | 'error' によって icon が変わる）
- Input コンポーネント（type: 'text' | 'password' | 'file' で追加 Props が異なる）
- Card コンポーネント（variant: 'basic' | 'selectable' で onClick の必要性が変わる）

### 実装例: Alert コンポーネント

```typescript
// components/ui/alert/Alert.tsx

type AlertBase = {
  message: string
  onClose?: () => void
}

type InfoAlert = AlertBase & {
  type: 'info' | 'success'
  // confirmText は不要
}

type WarningAlert = AlertBase & {
  type: 'warning'
  confirmText?: string  // 警告時は確認テキストを任意で追加できる
}

type ErrorAlert = AlertBase & {
  type: 'error'
  errorCode: string    // エラー時は必須
  retryAction?: () => void
}

type AlertProps = InfoAlert | WarningAlert | ErrorAlert

const Alert = (props: AlertProps) => {
  // TypeScript は props.type で型を絞り込める
  if (props.type === 'error') {
    // この分岐内で props.errorCode が使える（型安全）
    console.error(props.errorCode)
  }
  return <div role="alert">...</div>
}
```

### チェックリスト（Discriminated Union）

```
[ ] 判別子（discriminant）となるプロパティが string literal union になっているか
[ ] 各 union 型に必須 Props が明確に定義されているか
[ ] コンポーネント内で型絞り込み（type guard）を使っているか
[ ] 呼び出し側で型エラーが即座に出るか（誤った Props の組み合わせ）
```

---

## 4. Compound Components パターン

親コンポーネントと子コンポーネントが協調して1つの UI を構成するパターン。Tab・Accordion・Select・Dropdown 等の複合コンポーネントに適用する。

### なぜ使うか

通常の Props 設計では、複雑な入れ子構造を全て親の Props に詰め込むことになり、Props が爆発する。Compound Components は「役割を分割して、状態のみ共有する」設計で、これを解決する。

### Context + forwardRef を使った実装例: Tabs

```typescript
// components/ui/tabs/Tabs.tsx

// 共有 Context の型
interface TabsContextValue {
  activeTab: string
  setActiveTab: (id: string) => void
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

// Context を使う際の型安全な Hook
const useTabsContext = () => {
  const ctx = React.useContext(TabsContext)
  if (!ctx) throw new Error('TabsContext の外で使用されています')
  return ctx
}

// 親コンポーネント
interface TabsProps {
  defaultTab: string
  children: React.ReactNode
}

const Tabs = ({ defaultTab, children }: TabsProps) => {
  const [activeTab, setActiveTab] = React.useState(defaultTab)
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div>{children}</div>
    </TabsContext.Provider>
  )
}

// 子コンポーネント群
interface TabListProps {
  children: React.ReactNode
}
const TabList = ({ children }: TabListProps) => (
  <div role="tablist">{children}</div>
)

interface TabProps {
  id: string
  children: React.ReactNode
}
const Tab = ({ id, children }: TabProps) => {
  const { activeTab, setActiveTab } = useTabsContext()
  return (
    <button
      role="tab"
      aria-selected={activeTab === id}
      onClick={() => setActiveTab(id)}
    >
      {children}
    </button>
  )
}

interface TabPanelProps {
  id: string
  children: React.ReactNode
}
const TabPanel = ({ id, children }: TabPanelProps) => {
  const { activeTab } = useTabsContext()
  return activeTab === id ? <div role="tabpanel">{children}</div> : null
}

// 名前空間でまとめる（使用時: <Tabs.List> / <Tabs.Tab> 等）
Tabs.List = TabList
Tabs.Tab = Tab
Tabs.Panel = TabPanel
```

### 呼び出し例

```tsx
<Tabs defaultTab="overview">
  <Tabs.List>
    <Tabs.Tab id="overview">概要</Tabs.Tab>
    <Tabs.Tab id="details">詳細</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel id="overview">概要コンテンツ</Tabs.Panel>
  <Tabs.Panel id="details">詳細コンテンツ</Tabs.Panel>
</Tabs>
```

### チェックリスト（Compound Components）

```
[ ] Context は専用 Hook（useXxxContext）経由で取得しているか
[ ] Context 外での使用時にエラーが出るようになっているか
[ ] 子コンポーネントをネームスペース（親.子）でまとめているか
[ ] ARIA ロール（role="tablist" / role="tab" 等）が適切に設定されているか
```

---

## 5. forwardRef パターン

DOM 要素への ref 転送が必要な場合に使う。フォーカス制御・スクロール位置・サードパーティライブラリとの連携で必要になる。

### 適用場面

- カスタム Input / Select / Textarea: フォームライブラリ（react-hook-form 等）が ref を要求する
- Modal / Dialog: 開いたときにフォーカスを内部要素に移す
- Tooltip / Popover: アンカー要素の位置を計算するために ref が必要

### 実装例: フォームで使えるカスタム Input

```typescript
// components/ui/input/Input.tsx

interface InputProps extends React.ComponentProps<'input'> {
  label?: string
  error?: string
  hint?: string
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, ...rest }, ref) => {
    const inputId = id ?? React.useId()
    const errorId = `${inputId}-error`
    const hintId = `${inputId}-hint`

    return (
      <div>
        {label && <label htmlFor={inputId}>{label}</label>}
        <input
          id={inputId}
          ref={ref}
          aria-describedby={[error && errorId, hint && hintId].filter(Boolean).join(' ') || undefined}
          aria-invalid={!!error}
          {...rest}
        />
        {hint && <p id={hintId}>{hint}</p>}
        {error && <p id={errorId} role="alert">{error}</p>}
      </div>
    )
  }
)

// displayName は React DevTools でのデバッグに必要
Input.displayName = 'Input'
```

### react-hook-form との連携

```tsx
// forwardRef で定義した Input は register() と直接連携できる
import { useForm } from 'react-hook-form'

const Form = () => {
  const { register, formState: { errors } } = useForm<{ email: string }>()
  return (
    <Input
      label="メールアドレス"
      error={errors.email?.message}
      {...register('email', { required: 'メールアドレスは必須です' })}
    />
  )
}
```

### チェックリスト（forwardRef）

```
[ ] React.forwardRef の型引数（<DOM要素型, Props型>）が正確か
[ ] displayName が設定されているか
[ ] ref が正しい DOM 要素（input / button 等）に渡されているか
[ ] フォームライブラリの register との連携を確認しているか
```

---

## 6. 状態管理の分離パターン

コンポーネントを「表示専念（Presentational）」と「状態保持（Container）」に分離する設計方針。

### なぜ分離するか

- テスタビリティ: Presentational コンポーネントは Props だけで動くため、単体テストが容易
- 再利用性: 表示ロジックを別のデータソースに接続しやすい
- Storybook: 状態なしで全 variant を列挙できる

### 分離の境界

```
Custom Hook（useXxx）— データ取得・状態管理・副作用
  ↓ state / handlers を返す
Organism（Container 相当）— Hook を呼び出し、Presentational に渡す
  ↓ Props として渡す
Molecules / Atoms（Presentational）— Props のみで描画
```

### 実装例: ユーザー一覧

```typescript
// hooks/useUserList.ts（状態管理を担当）
interface UseUserListReturn {
  users: User[]
  isLoading: boolean
  error: string | null
  refetch: () => void
}

const useUserList = (): UseUserListReturn => {
  const [users, setUsers] = React.useState<User[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  const fetchUsers = React.useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.getUsers()
      setUsers(data)
    } catch {
      setError('ユーザー情報の取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => { fetchUsers() }, [fetchUsers])

  return { users, isLoading, error, refetch: fetchUsers }
}

// components/features/users/UserList.tsx（Organism: Container 相当）
const UserList = () => {
  const { users, isLoading, error, refetch } = useUserList()
  return <UserListView users={users} isLoading={isLoading} error={error} onRetry={refetch} />
}

// components/features/users/UserListView.tsx（Presentational）
interface UserListViewProps {
  users: User[]
  isLoading: boolean
  error: string | null
  onRetry: () => void
}

const UserListView = ({ users, isLoading, error, onRetry }: UserListViewProps) => {
  if (isLoading) return <Skeleton />
  if (error) return <ErrorState message={error} onRetry={onRetry} />
  if (users.length === 0) return <EmptyState />
  return <ul>{users.map(u => <UserItem key={u.id} user={u} />)}</ul>
}
```

### チェックリスト（状態管理の分離）

```
[ ] Presentational コンポーネントが Props だけで完結しているか（Hook を直接呼ばない）
[ ] Custom Hook が返す型（Return 型）が明示されているか
[ ] ローディング / エラー / 空状態 の全 3 状態が Presentational に Props として渡されているか
[ ] Storybook の Story を Presentational コンポーネントに対して書いているか
```

---

## 7. Props 設計の禁止パターン

### 避けるべきパターン

```typescript
// 禁止1: any の使用
interface BadProps {
  data: any
}

// 禁止2: Props のバケツリレー（3層以上同じ Props を渡す）
// → Context または Compound Components で解決する

// 禁止3: boolean でバリアントを表現する（複数の boolean が排他的になる）
interface BadButtonProps {
  isPrimary?: boolean
  isSecondary?: boolean   // isPrimary と同時に true になれてしまう
  isOutline?: boolean
}
// → Discriminated Union または variant: 'primary' | 'secondary' | 'outline' で解決

// 禁止4: onXxx 系ハンドラの Props 過多
interface BadProps {
  onHover: () => void
  onFocus: () => void
  onBlur: () => void
  onMouseEnter: () => void
  onMouseLeave: () => void
}
// → React.ComponentProps<'div'> を extends して ...rest で解決
```

### まとめ: パターン選択表

| 状況 | 採用パターン |
|------|------------|
| 単純な Atom | 基本 Props + HTML 属性継承 |
| variant で型が変わる | Discriminated Union |
| 複合コンポーネント（タブ・セレクト等） | Compound Components |
| フォームライブラリ連携・DOM操作 | forwardRef |
| データ取得・副作用あり | 状態管理分離 + Custom Hook |
