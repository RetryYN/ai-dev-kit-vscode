# WCAG クイックリファレンス

> 目的: WCAG 2.1 A/AA レベルで必ず満たす要件・ARIA 属性の代表ユースケース・キーボード操作パターン（focus trap / skip link / arrow-key navigation）を実装者が即座に参照できる形で整理する

---

## 1. WCAG 2.1 適合レベルの概要

| レベル | 意味 | 対応方針 |
|--------|------|---------|
| A | 最低限。これを満たさないと一部ユーザーが完全に利用不可能 | 全機能で必須 |
| AA | 標準。日本の「令和3年障害者差別解消法」の目安・多くの企業要件 | 全機能で必須 |
| AAA | 高度。特定状況のみ現実的 | 対応可能な範囲で |

本リファレンスは **A と AA** のみを扱う。

---

## 2. 必ず満たす要件一覧（A / AA）

### 2-1. 知覚可能（Perceivable）

#### 1.1 テキストによる代替

```
[ ] (A) 画像・アイコンに alt テキストがある
    - 意味のある画像: 内容を説明する alt
    - 装飾的画像: alt=""（スクリーンリーダーが読み飛ばす）
    - アイコンのみのボタン: aria-label で代替テキストを提供

[ ] (A) フォームのコントロール（input / select / textarea）に label がある
    - htmlFor + id の紐付け、または aria-label / aria-labelledby
```

#### 1.3 適応可能

```
[ ] (A) 情報・構造が HTML の意味論（見出し・リスト・テーブル）で表現されている
    - 見出しは h1〜h6 を順番通りに使う（h1 → h2 → h3。h2 を飛ばして h4 は禁止）
    - リストは ul / ol / dl で表現する
    - データテーブルは caption / th / td を使う

[ ] (A) 色だけで情報を伝えていない
    - エラーを赤色だけで示さない → アイコン・テキストを併用する
    - リンクを色だけで示さない → 下線またはアイコンを併用する

[ ] (AA) 入力フィールドの目的を自動入力で特定できる（autocomplete 属性）
    - 名前: autocomplete="name"
    - メール: autocomplete="email"
    - 電話: autocomplete="tel"
    - 住所: autocomplete="street-address"
```

#### 1.4 判別可能

```
[ ] (AA) 通常テキストのコントラスト比 4.5:1 以上
[ ] (AA) 大きなテキスト（18pt / 14pt bold 以上）のコントラスト比 3:1 以上
[ ] (AA) UI コンポーネント・グラフィックの境界線コントラスト比 3:1 以上
[ ] (AA) テキストを 200% まで拡大しても内容・機能が損なわれない
[ ] (AA) テキストが画像内に埋め込まれていない（ロゴ・グラフ以外）
[ ] (AA) コンテンツが横スクロールなしで 320px 幅に対応する（reflow）
[ ] (AA) 間隔（行間・文字間・段落間・単語間）を変更してもコンテンツが重ならない
```

### 2-2. 操作可能（Operable）

#### 2.1 キーボード操作

```
[ ] (A) すべての機能がキーボードのみで操作できる
[ ] (A) キーボードのフォーカスがトラップされない（モーダル内は例外 → §5 参照）
[ ] (AA) フォーカスの移動が予測可能な順序で行われる（Tab 順序）
```

#### 2.3 発作・体調不良の予防

```
[ ] (A) 1秒間に3回以上点滅するコンテンツがない
```

#### 2.4 ナビゲーション

```
[ ] (A) 繰り返されるナビゲーションをスキップできる（スキップリンク → §4 参照）
[ ] (A) ページのタイトル（title 要素）が内容を説明している
[ ] (A) フォーカス順序が意味的に正しい順番で移動する
[ ] (A) リンクテキストが目的を示している（「こちら」「詳細」だけは禁止）
[ ] (AA) フォーカスインジケータが常に可視である
[ ] (AA) ページに複数のナビゲーション手段がある（ナビゲーション + 検索 + サイトマップ等）
[ ] (AA) 見出しとラベルが内容を説明している
```

#### 2.5 入力モダリティ

```
[ ] (AA) タッチターゲットが 24x24px 以上（理想: 44x44px）
[ ] (AA) ドラッグ操作が必要な場合、代替操作手段がある
```

### 2-3. 理解可能（Understandable）

```
[ ] (A) ページの主言語（lang 属性）が設定されている
    例: <html lang="ja">
[ ] (AA) 一貫したナビゲーション（ページ間でナビの位置・順序が同じ）
[ ] (AA) 一貫した識別（同じ機能のコンポーネントが同じ名前・ラベルを持つ）
[ ] (A) 入力エラーを自動検出し、テキストでユーザーに説明する
[ ] (AA) 入力ラベルまたは説明文が提供されている
[ ] (AA) エラーを防ぐための確認・取り消し・修正手段がある（決済・法的コミットメント等）
```

### 2-4. 堅牢（Robust）

```
[ ] (A) HTML が仕様通りに解析できる（開始・終了タグが対応、id が一意）
[ ] (A) カスタム UI コンポーネントの名前・役割・状態がプログラムで特定できる
    → ARIA ロール・プロパティ・状態を適切に設定する
```

---

## 3. ARIA 属性の代表ユースケース

ARIA（Accessible Rich Internet Applications）は HTML のネイティブセマンティクスを補完するための属性群。**ネイティブ HTML で表現できる場合は ARIA を使わない**（第一原則: No ARIA is better than Bad ARIA）。

### 3-1. ロール（role）

| role | 用途 | 使用する状況 |
|------|------|------------|
| `role="alert"` | 緊急の通知 | エラーメッセージ・システム通知 |
| `role="status"` | 非緊急の通知 | 保存完了・処理中メッセージ |
| `role="dialog"` | モーダルダイアログ | `<dialog>` 要素が使えない場合 |
| `role="navigation"` | ナビゲーション領域 | `<nav>` 要素と同等 |
| `role="main"` | メインコンテンツ | `<main>` 要素と同等 |
| `role="banner"` | サイトヘッダー | `<header>` 要素と同等 |
| `role="contentinfo"` | サイトフッター | `<footer>` 要素と同等 |
| `role="tablist"` | タブコンテナ | カスタムタブ UI |
| `role="tab"` | 個別タブ | カスタムタブ UI の各タブ |
| `role="tabpanel"` | タブパネル | カスタムタブ UI のコンテンツ |
| `role="menubar"` | メニューバー | ドロップダウンメニュー全体 |
| `role="menu"` | メニュー | ドロップダウンの中身 |
| `role="menuitem"` | メニュー項目 | ドロップダウンの各項目 |

### 3-2. プロパティ（aria-*）

| 属性 | 用途 | 例 |
|------|------|-----|
| `aria-label` | 可視テキストがない要素に名前を付ける | `<button aria-label="メニューを閉じる">✕</button>` |
| `aria-labelledby` | 別要素のテキストを名前として参照する | `<section aria-labelledby="section-title">` |
| `aria-describedby` | 補足説明を関連付ける | `<input aria-describedby="email-hint">` |
| `aria-required` | 必須入力を示す | `<input aria-required="true">` |
| `aria-invalid` | 入力値が不正であることを示す | `<input aria-invalid="true">` |
| `aria-live` | 動的コンテンツの更新を通知する | 下記参照 |
| `aria-modal` | モーダル外をスクリーンリーダーが読まないようにする | `<div role="dialog" aria-modal="true">` |
| `aria-hidden` | スクリーンリーダーから隠す | `<span aria-hidden="true">★</span>`（装飾） |

### 3-3. 状態（aria-expanded / aria-selected 等）

| 属性 | 用途 | 値 |
|------|------|-----|
| `aria-expanded` | 開閉状態 | `true` / `false` |
| `aria-selected` | 選択状態（タブ・オプション等） | `true` / `false` |
| `aria-checked` | チェック状態（チェックボックス等） | `true` / `false` / `mixed` |
| `aria-disabled` | 無効状態 | `true` / `false` |
| `aria-busy` | 読み込み中 | `true` / `false` |
| `aria-current` | 現在地（ナビ・パンくず） | `page` / `step` / `location` |

### 3-4. aria-live の使い分け

```tsx
// assertive: 割り込み通知（エラー・緊急）
// スクリーンリーダーが現在読んでいる内容を中断して読む
<div role="alert" aria-live="assertive" aria-atomic="true">
  {errorMessage}
</div>

// polite: 非割り込み通知（成功・ステータス）
// スクリーンリーダーが現在の読み上げを終えてから読む
<div role="status" aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

---

## 4. スキップリンク（Skip Link）

ページ先頭に設置し、キーボードユーザーが繰り返しナビゲーションを飛ばしてメインコンテンツに直接移動できるようにする。

### 実装パターン

```tsx
// layout.tsx（全ページで設置）
// 通常は視覚的に非表示、フォーカス時に表示
const SkipLink = () => (
  <a
    href="#main-content"
    className="
      sr-only
      focus:not-sr-only
      focus:fixed
      focus:top-2
      focus:left-2
      focus:z-50
      focus:px-md
      focus:py-sm
      focus:bg-bg-surface
      focus:text-text-primary
      focus:rounded-md
      focus:shadow-md
      focus:outline-none
      focus:ring-2
      focus:ring-action-primary
    "
  >
    メインコンテンツへスキップ
  </a>
)

// メインコンテンツのコンテナに id を付与する
const Layout = ({ children }: { children: React.ReactNode }) => (
  <>
    <SkipLink />
    <Header />
    <main id="main-content" tabIndex={-1}>
      {children}
    </main>
    <Footer />
  </>
)
```

### 複数のスキップリンクが必要な場合

```tsx
// ナビゲーション・検索・メインコンテンツの3箇所へのスキップ
<nav aria-label="スキップリンク">
  <a href="#main-content">メインコンテンツへスキップ</a>
  <a href="#site-search">検索へスキップ</a>
</nav>
```

---

## 5. フォーカストラップ（Focus Trap）

モーダル・ドロワー等の重なったコンテキストでは、フォーカスをコンテナ内に閉じ込める必要がある。モーダルが開いているとき、Tab キーでの移動がモーダル外に出ないようにする。

### 実装方針

フォーカストラップの実装は複雑なため、実績あるライブラリを使用することを推奨する。

- `focus-trap-react`（npm: focus-trap-react）
- Radix UI の `Dialog` コンポーネント（内部でフォーカストラップを処理済み）
- Headless UI の `Dialog`（内部でフォーカストラップを処理済み）

### 自前で実装する場合の最小コード

```typescript
// モーダル内でフォーカス可能な要素を取得する
const FOCUSABLE_SELECTORS = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

const useFocusTrap = (containerRef: React.RefObject<HTMLElement>, isActive: boolean) => {
  React.useEffect(() => {
    if (!isActive || !containerRef.current) return

    const container = containerRef.current
    const focusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTORS))
    const first = focusables[0]
    const last = focusables[focusables.length - 1]

    // モーダルを開いたとき、最初のフォーカス可能要素にフォーカスを移す
    first?.focus()

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return
      if (e.shiftKey) {
        // Shift+Tab: 先頭の要素にいたら末尾にループ
        if (document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        }
      } else {
        // Tab: 末尾の要素にいたら先頭にループ
        if (document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    return () => container.removeEventListener('keydown', handleKeyDown)
  }, [isActive, containerRef])
}
```

### モーダルの ARIA 属性セット

```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <h2 id="modal-title">確認</h2>
  <p id="modal-description">この操作は取り消せません。続行しますか？</p>
  <button onClick={onConfirm}>確認</button>
  <button onClick={onClose}>キャンセル</button>
</div>
```

---

## 6. 矢印キーナビゲーション

タブ・ラジオボタン・ドロップダウン・メニュー等のウィジェットは、矢印キーで選択肢間を移動する UX を実装する（Tab は次のウィジェットへの移動に使う）。

### タブウィジェットのキーボード操作

| キー | 操作 |
|------|------|
| Tab | タブリストにフォーカスを移動 / タブリストからパネルへ |
| 右矢印 / 下矢印 | 次のタブに移動（末尾では先頭にループ） |
| 左矢印 / 上矢印 | 前のタブに移動（先頭では末尾にループ） |
| Enter / Space | タブを選択してパネルを表示 |
| Home | 最初のタブに移動 |
| End | 最後のタブに移動 |

### 実装例（タブの矢印キー操作）

```tsx
const TabList = ({ tabs, activeTab, onTabChange }: TabListProps) => {
  const handleKeyDown = (e: React.KeyboardEvent, currentIndex: number) => {
    let nextIndex: number | null = null

    switch (e.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        e.preventDefault()
        nextIndex = (currentIndex + 1) % tabs.length
        break
      case 'ArrowLeft':
      case 'ArrowUp':
        e.preventDefault()
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length
        break
      case 'Home':
        e.preventDefault()
        nextIndex = 0
        break
      case 'End':
        e.preventDefault()
        nextIndex = tabs.length - 1
        break
    }

    if (nextIndex !== null) {
      onTabChange(tabs[nextIndex].id)
      // タブ要素にフォーカスを移動する
      const tabElements = document.querySelectorAll('[role="tab"]')
      ;(tabElements[nextIndex] as HTMLElement)?.focus()
    }
  }

  return (
    <div role="tablist">
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`panel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onKeyDown={(e) => handleKeyDown(e, index)}
          onClick={() => onTabChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}
```

### tabIndex の使い方

```
tabIndex={0}:  通常のフォーカス順序に含める
tabIndex={-1}: プログラム的にフォーカスできるが、Tab キーの順序には含めない
              （矢印キーで移動するウィジェット内の非アクティブ要素に使う）
```

---

## 7. よくある実装ミス（禁止パターン）

```
[禁止] フォーカスリングを CSS で消す
  :focus { outline: none; }
  → 代替: :focus-visible でマウス操作時は非表示、キーボード操作時は表示

[禁止] div や span をクリック可能にする（role / keyboard なし）
  <div onClick={handleClick}>送信</div>
  → 代替: <button onClick={handleClick}>送信</button>

[禁止] aria-label の乱用（ネイティブ HTML で表現できる場合）
  <nav aria-label="ナビゲーション">
  → ネイティブ <nav> 要素は既にナビゲーションランドマーク

[禁止] 意味のある画像の alt="" （空にすると装飾扱いになる）
  <img src="company-logo.png" alt="">
  → 代替: <img src="company-logo.png" alt="株式会社○○">

[禁止] aria-hidden="true" をフォーカス可能要素に付与する
  <button aria-hidden="true">送信</button>
  → フォーカスは受けるがスクリーンリーダーに無視される矛盾状態
```

---

## 8. 実装後のチェックリスト

```
[ ] (A)  全画像に適切な alt または alt="" がある
[ ] (A)  全フォームフィールドに label または aria-label がある
[ ] (AA) 通常テキストのコントラスト比 4.5:1 以上
[ ] (AA) 大テキスト（18pt / 14pt bold）のコントラスト比 3:1 以上
[ ] (A)  Tab キーで全インタラクティブ要素に到達できる
[ ] (AA) フォーカスインジケータが全インタラクティブ要素で可視
[ ] (A)  色のみで情報を伝えていない（アイコン・テキスト併用）
[ ] (A)  スキップリンクがページ先頭に存在する
[ ] (A)  モーダルにフォーカストラップが実装されている
[ ] (A)  タブ・ラジオ等のウィジェットに矢印キー操作がある
[ ] (A)  タッチターゲットが 44x44px 以上（推奨）
[ ] (A)  Playwright + axe-core で自動検証が実行されている
[ ] (A)  html 要素に lang="ja" が設定されている
[ ] (A)  aria-live 領域でエラー・成功メッセージを通知している
```
