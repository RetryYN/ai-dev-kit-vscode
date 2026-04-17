---
name: web-system
description: shadcn/uiベースのデザインシステム構築でコンポーネント選定・テーマ設定・トークン管理の標準手順を提供
metadata:
  helix_layer: L2
  triggers:
    - FE駆動のプロジェクト設計時
    - コンポーネント設計(D-UI)時
    - Visual設計(D-VIS-ARCH)時
  verification:
    - "components.json 存在"
    - "デザイントークン定義済み"
    - "採用コンポーネントと選定理由の記録"
compatibility:
  claude: true
  codex: true
---

# FEデザインシステム基盤スキル（shadcn/ui）

## 適用タイミング

このスキルは以下の場合に読み込む：
- FE駆動プロジェクトの設計時
- コンポーネント設計（D-UI）時
- Visual設計（D-VIS-ARCH）時

---

## 1. セットアップ手順

前提：Tailwind CSS が導入済みの React/Next.js プロジェクト。

```bash
npx shadcn@latest init
```

初期化で確認する項目：

- `components.json` が生成される
- `tailwind.config.*` の content path が適切
- `src/lib/utils.ts`（`cn` ヘルパー）が作成される

コンポーネント追加例：

```bash
npx shadcn@latest add button input card dialog table tabs form
```

---

## 2. コンポーネント選定ガイド（用途別）

| 用途 | 推奨セット | 判断基準 |
|------|-----------|---------|
| 認証画面 | `form`, `input`, `button`, `alert` | バリデーションとエラー表示の一貫性 |
| 一覧管理 | `table`, `badge`, `dropdown-menu`, `pagination` | 行操作と状態表示の明確さ |
| ダッシュボード | `card`, `tabs`, `separator`, `skeleton` | 情報階層とローディング体験 |
| 設定画面 | `switch`, `select`, `textarea`, `tooltip` | 変更影響の理解しやすさ |
| モーダル操作 | `dialog`, `sheet`, `popover` | 破壊的操作の誤実行防止 |

選定記録テンプレート（D-UIに記載）：

```markdown
- component: dialog
- 採用理由: 破壊的操作の確認を強制できる
- 代替案: popover
- 不採用理由: 誤操作リスクが高い
```

---

## 3. テーマカスタマイズ（CSS変数・ダークモード）

### CSS変数の基本

`app/globals.css` 例：

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;
}
```

### ダークモード方針

- class戦略（`class="dark"`）を標準採用
- 初期値は `system`、ユーザー選択を優先
- コントラスト比は WCAG 4.5:1 以上を維持

---

## 4. デザイントークン管理

### 管理対象

- Color（semantic token: `primary`, `muted`, `destructive`）
- Typography（`font-size`, `line-height`, `font-weight`）
- Spacing（4/8ベース）
- Radius / Shadow / Z-index

### 推奨運用

1. トークンは `globals.css` と設計書の両方に記録。
2. 直接色指定（`text-[#123456]`）を禁止し、semantic token経由に統一。
3. 変更時は「影響コンポーネント一覧」を更新。

---

## 5. HELIX FE駆動タイプとの統合

### D-VIS-ARCH の前提成果物

D-VIS-ARCH を作る前に以下が揃っていること：
- D-IA（`docs/fe/D-IA.md`）
- D-UX-FLOW（`docs/fe/D-UX-FLOW.md`）

### L2（設計）

- D-UI にコンポーネント一覧と採用理由を記載
- D-VIS-ARCH にテーマ方針とトークン方針を記載

### L3（詳細設計）

- Component Contract（Props, States, Variants）を固定
- `components.json` を設計証跡として保持

### L4/L5（実装・Visual）

- L4 で骨格実装
- L5 でトークン調整のみを優先（V0対応）
- 構造変更（V1/V2）が発生したらゲートルールに従って差し戻す

---

## 6. Tailwind CSS ベストプラクティス

1. 長い class 文字列は `cn()` と variant関数で分離する。
2. マジックナンバーを避け、`spacing` と token を使う。
3. `@apply` は再利用が明確な場合のみ使用する。
4. レスポンシブは `mobile first` で定義する。
5. 状態（hover/focus/disabled）をコンポーネント側で完結させる。

---

## 7. 完了判定

- `components.json` が存在
- トークン（color/spacing/typography）が定義済み
- 採用コンポーネントの選定理由がD-UIに記録済み
