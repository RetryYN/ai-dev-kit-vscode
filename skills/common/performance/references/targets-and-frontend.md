> 目的: パフォーマンス目標とフロント最適化戦術を参照すべき場面

## 適用タイミング

このスキルは以下の場合に読み込む：
- パフォーマンス改善時
- ボトルネック調査時
- 負荷テスト時

---

## 1. パフォーマンス目標

### Core Web Vitals（2026年基準）

| 指標 | 良好 | 要改善 | 不良 |
|------|------|--------|------|
| **LCP**（最大コンテンツ描画） | ≤2.5s | ≤4.0s | >4.0s |
| **INP**（次の描画への応答性） | ≤200ms | ≤500ms | >500ms |
| **CLS**（累積レイアウトシフト） | ≤0.1 | ≤0.25 | >0.25 |

### バックエンド目標

| 指標 | 目標 | 警告 | 危険 |
|------|------|------|------|
| API応答時間（p95） | <200ms | <500ms | >1s |
| API応答時間（p99） | <500ms | <1s | >2s |
| エラー率 | <0.1% | <1% | >1% |
| スループット | 要件依存 | - | - |

---

## 2. フロントエンド最適化

### バンドルサイズ

```bash
# 分析
npx next build
npx @next/bundle-analyzer

# 目標
- 初期JS: <100KB（gzip）
- 初期CSS: <20KB（gzip）
- 画像: WebP/AVIF使用
```

### コード分割

```typescript
// 動的インポート
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />,
  ssr: false  // 必要に応じて
})

// ルートベース分割（Next.js App Router）
// app/dashboard/page.tsx → 自動的に分割
```

### 画像最適化

```tsx
// Next.js Image
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority  // LCP画像
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>

// サイズ指定
// - モバイル: 640w
// - タブレット: 1024w
// - デスクトップ: 1920w
```

### レンダリング最適化

```typescript
// メモ化
const MemoizedComponent = memo(ExpensiveComponent)

// useMemo
const computed = useMemo(() => {
  return expensiveCalculation(data)
}, [data])

// useCallback
const handleClick = useCallback(() => {
  doSomething(id)
}, [id])

// 仮想スクロール（大量リスト）
import { useVirtualizer } from '@tanstack/react-virtual'
```

### リソースヒント

```html
<!-- プリロード（重要リソース） -->
<link rel="preload" href="/fonts/main.woff2" as="font" crossorigin>

<!-- プリコネクト（外部ドメイン） -->
<link rel="preconnect" href="https://api.example.com">

<!-- プリフェッチ（次のページ） -->
<link rel="prefetch" href="/dashboard">
```

---

