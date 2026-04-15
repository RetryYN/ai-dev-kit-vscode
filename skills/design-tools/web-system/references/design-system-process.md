# デザインシステム構築プロセス

> 目的: shadcn/ui ベースのデザインシステムを計画的に立ち上げ・移行するための6ステップ工程を定義する。
> 適用フェーズ: L2 Visual 設計（D-VIS-ARCH 策定時）、L5 Visual Refinement（既存プロジェクトの段階的整備時）。
> 駆動タイプ: fe / fullstack。

---

## 6ステップ全体像

```
Step 1: 監査（Audit）
   ↓ 成果物: 現状スタイル棚卸しシート
Step 2: トークン策定（Token Definition）
   ↓ 成果物: globals.css + tailwind.config.*（Primitive 層）
Step 3: プリミティブコンポーネント（Primitives）
   ↓ 成果物: Button / Input / Badge 等の基礎コンポーネント
Step 4: セマンティックトークン（Semantic Tokens）
   ↓ 成果物: globals.css（Semantic / Component 層）
Step 5: 複合コンポーネント（Composite Components）
   ↓ 成果物: Card / Dialog / Form 等の組み合わせコンポーネント
Step 6: ドキュメント（Documentation）
   ↓ 成果物: Storybook / DESIGN.md / コンポーネント使用ガイド
```

---

## Step 1: 監査（Audit）

**目的**: 現状の UI に散在するスタイル値を棚卸しし、重複・不一致を可視化する。

**作業**:
- CSS / Tailwind クラスからハードコードされた色・フォント・余白値を抽出
- 使用頻度 Top20 の値を特定（これがトークン候補）
- デザインツール（Figma 等）との乖離を確認

**完了基準**:
- ハードコード値の一覧が揃っている
- 重複・類似値がグループ化されている（例: `#1e40af` と `#1d4ed8` は同一トークンに統合可能か判断済み）

**既存プロジェクトへの適用**: まず1画面だけ監査して規模感を掴む。全画面一括は避ける。

---

## Step 2: トークン策定（Token Definition）

**目的**: Primitive トークン（原始値）を CSS 変数と Tailwind テーマで定義する。

**作業**:
- 監査結果から Primitive トークンを決定
- `globals.css` に CSS 変数を定義
- `tailwind.config.*` の `theme.extend` にマッピング

```css
/* globals.css — Primitive 層の例 */
:root {
  --color-blue-500: #3b82f6;
  --color-blue-700: #1d4ed8;
  --color-gray-50:  #f9fafb;
  --color-gray-900: #111827;
  --space-4:  1rem;
  --space-8:  2rem;
  --radius-md: 0.5rem;
}
```

```js
// tailwind.config.ts — theme.extend の例
theme: {
  extend: {
    colors: {
      'blue-500': 'var(--color-blue-500)',
      'blue-700': 'var(--color-blue-700)',
    },
    spacing: {
      '4': 'var(--space-4)',
      '8': 'var(--space-8)',
    },
  },
},
```

**完了基準**:
- ハードコード値がゼロになる（色・余白・フォントはすべてトークン参照）
- `token-scale-guide.md` のスケール設計に従っている

---

## Step 3: プリミティブコンポーネント（Primitives）

**目的**: shadcn/ui の基礎コンポーネントを導入し、Semantic トークンを適用する。

**作業**:
```bash
npx shadcn@latest add button input badge label separator
```

- 各コンポーネントの `className` をトークン参照に置換
- `cn()` ヘルパーと `cva()` で variant を整理

**完了基準**:
- Button / Input / Badge の 3 コンポーネントが Semantic トークン参照になっている
- `components.json` が存在し、設計証跡として保持されている

---

## Step 4: セマンティックトークン（Semantic Tokens）

**目的**: Primitive 値を「役割」として命名した Semantic 層と Component 層を追加する。

```css
/* globals.css — Semantic / Component 層の例 */
:root {
  /* Semantic */
  --color-primary:         var(--color-blue-500);
  --color-primary-hover:   var(--color-blue-700);
  --color-text-base:       var(--color-gray-900);
  --color-surface:         var(--color-gray-50);

  /* Component */
  --color-button-primary-bg:     var(--color-primary);
  --color-button-primary-text:   #ffffff;
  --color-button-primary-hover:  var(--color-primary-hover);
}

.dark {
  --color-primary:       #60a5fa; /* blue-400 — ダークで明るめに */
  --color-text-base:     var(--color-gray-50);
  --color-surface:       var(--color-gray-900);
}
```

**完了基準**:
- Semantic トークンが全 UI ロールをカバーしている（primary / muted / destructive / success / warning）
- ダークモード切替が CSS 変数の上書きで完結している（JS 依存なし）

---

## Step 5: 複合コンポーネント（Composite Components）

**目的**: プリミティブを組み合わせた、プロジェクト固有の複合コンポーネントを実装する。

**作業**:
```bash
npx shadcn@latest add card dialog form table tabs
```

- 各コンポーネントに Semantic トークンを適用
- D-UI（コンポーネント設計書）の採用理由に記録

**完了基準**:
- 主要画面の全コンポーネントがデザインシステム経由でスタイルを得ている
- 直接色指定（`text-[#123456]` 等）が残存していない

---

## Step 6: ドキュメント（Documentation）

**目的**: チームが迷わず使えるよう、コンポーネントの使い方と意図を記録する。

**作業**:
- `docs/DESIGN.md` を `design-md-format.md` の 9 セクション形式で作成・更新
- Storybook または README にコンポーネントごとの使用例を追加
- D-VIS-ARCH（L2 Visual 設計書）に本ドキュメントを組み込む

**完了基準**:
- DESIGN.md の 9 セクションが全て埋まっている
- Do's / Don'ts が明文化されている

---

## 既存プロジェクトへの段階的移行パターン

いきなり全取替は現実的でない。以下の「Strangler Fig パターン」で段階移行する。

### フェーズ A: 観察（1〜2週間）
- Step 1（監査）のみ実施
- 既存コードは変更しない
- 棚卸しシートを作るだけで終わる

### フェーズ B: 基盤整備（1〜2週間）
- Step 2（トークン策定）を実施
- `globals.css` にトークン追加のみ（既存コード未変更）
- 新規コンポーネントはトークン参照で書く

### フェーズ C: 置換（スプリントごと）
- 変更が必要な画面・コンポーネントのスタイルをトークン参照に置換
- Step 3〜5 を画面単位で進める
- 「触ったファイルはトークン参照にする」ルールを徹底

### フェーズ D: 完成・ドキュメント化
- Step 6 を実施
- 全画面の置換完了を確認

---

## shadcn/ui との親和性マッピング

| 本プロセスのステップ | shadcn/ui の対応概念 |
|---------------------|-------------------|
| Step 1（監査） | — |
| Step 2（Primitive トークン） | `globals.css` の CSS 変数（`:root` セクション） |
| Step 3（プリミティブコンポーネント） | `npx shadcn@latest add` で追加する基礎コンポーネント |
| Step 4（Semantic トークン） | `globals.css` の `.dark` セクション・shadcn の色変数名体系 |
| Step 5（複合コンポーネント） | 複数 shadcn コンポーネントを組み合わせた独自コンポーネント |
| Step 6（ドキュメント） | `components.json` + DESIGN.md + Storybook |

shadcn/ui の変数命名（`--primary`, `--muted`, `--destructive`）は Semantic トークン層に相当する。
Primitive 層（`--color-blue-500` 等）は shadcn が提供しないため、プロジェクト側で追加する。

---

## チームサイズ別の運用

### 1人（個人開発）
- Step 1〜4 を1日で終わらせる（完璧でなくてよい）
- Step 6 は省略可（DESIGN.md の最低限だけ書く）
- 「触ったファイルは直す」の習慣だけ守る

### 3〜5人（小チーム）
- Step 1 は全員でレビュー（認識合わせが目的）
- Step 2〜4 はフロントリード1人が担当
- Step 6 は PR レビューを通じてコンポーネント単位で更新

### 10人以上（中〜大チーム）
- Step 1〜2 にデザイナーが参加（トークン名の合意が重要）
- Step 3〜5 はコンポーネントオーナー制を設ける
- Step 6 は Storybook を必須化し、変更プロセスを ADR で管理
- トークン変更時は「影響コンポーネント一覧」の更新を必須とする

---

## 実在システムの参考

| システム | 特徴 | 参考にしやすい点 |
|---------|------|--------------|
| Material Design 3 | Google 製。トークン3層設計の教科書 | Ref / Sys / Comp トークン命名体系 |
| Radix UI | shadcn の基盤。アクセシビリティ優先 | 複合コンポーネント設計パターン |
| Primer（GitHub） | 実務規模の大型DS。オープンソース | チーム運用・ドキュメント構造 |
| Atlassian Design System | エンタープライズ向け。密度高め | Elevation・色の意味体系 |
| Ant Design | 日本語実績も多い。コンポーネント数が多い | 業務系 UI のコンポーネント設計 |

---

## 関連資料

- [token-scale-guide.md](./token-scale-guide.md) — デザイントークン詳細設計（スケール・命名規則）
- [design-md-usage.md](./design-md-usage.md) — DESIGN.md → shadcn/ui への変換手順
- [../SKILL.md](../SKILL.md) — FEデザインシステム基盤スキル（shadcn/ui セットアップ）
- [../../common/visual-design/SKILL.md](../../common/visual-design/SKILL.md) — ビジュアルデザインスキル（原則・配色・タイポグラフィ）
- [../../common/visual-design/references/design-md-format.md](../../common/visual-design/references/design-md-format.md) — DESIGN.md 9セクション形式テンプレート
