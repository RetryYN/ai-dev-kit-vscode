# DESIGN.md 9セクション形式 — ビジュアル仕様書テンプレート

> **L2 ② 必読**（DESIGNER.md 作成手順書）
> 目的: AI エージェント（Claude Code / Codex / Cursor など）が正確な UI を生成するための**構造化デザイン仕様書**のテンプレート。
> 適用フェーズ: L2 Visual 方針策定時（設計前）、L5 Visual Refinement（実装後の調整）。

## 役割分担: DESIGNER.md vs DESIGN.md

HELIX には2種類のデザイン文書がある。用途が異なるので使い分ける。

| 文書 | 目的 | 作成タイミング | 粒度 |
|------|------|---------------|------|
| **DESIGNER.md**（既存） | **Why** — プロダクト戦略を言語化 | L5 の最初（実装後） | Role / Target / Pain / Solution / Concept / Anti-patterns |
| **DESIGN.md**（本資料） | **How** — 視覚仕様を構造化 | L2 Visual 方針時（設計前） | 9セクション（配色・タイポ・コンポーネント等） |

連動フロー:
1. L2 で DESIGNER.md の skeleton（Role / Target のみ）を作成し、L5 で完成（Why を確定）
2. L2 Visual で DESIGN.md を作成（類似ブランドの `brands-jp/` or `brands-en/` を参照）
3. L4 実装で DESIGN.md を実装の「ソース・オブ・トゥルース」として使う
4. L5 Refinement で DESIGNER.md を完成させ、実装と DESIGN.md を突合

## 適用対象プロジェクト

| 駆動タイプ | DESIGN.md 作成必要性 |
|-----------|--------------------|
| **fe**, **fullstack** | **強く推奨**（L2 Visual 方針策定時に作成） |
| **agent**（AI/UI 付き） | 推奨（会話 UI がある場合） |
| **be**, **db** | UI がある場合のみ（管理画面等） |

## 使用手順

### Step 1: 類似ブランドを特定
`brands-jp/INDEX.md` または `brands-en/INDEX.md` から、カテゴリ・テイスト・情報密度の近いブランドを2-3件選ぶ。

### Step 2: テンプレートをコピー
下記「テンプレート本体」を `docs/DESIGN.md` としてプロジェクトにコピー。

### Step 3: 9セクション全てを埋める
類似ブランドの DESIGN.md の値を参考に、プロジェクト固有の値に置き換える。空欄（`—` や `______`）を残さない。

### Step 4: D-VIS-ARCH（Visual 設計書）に反映
SKILL_MAP.md の fe/fullstack 駆動の L2 成果物 D-VIS-ARCH に DESIGN.md を組み込む。

### Step 5: 実装者・レビュアーに共有
DESIGN.md は L4 実装者の仕様書、L5 Refinement のチェックリストとして機能する。

---

## テンプレート本体

以下をそのままコピーして使用する。

```markdown
# DESIGN.md — [サービス名]

> このファイルは AI エージェントが正確な UI を生成するためのデザイン仕様書です。
> セクションヘッダーは英語、値の説明は日本語で記述しています。

---

## 1. Visual Theme & Atmosphere

- **デザイン方針**: （例: クリーン、プロフェッショナル、温かみのある）
- **密度**: （例: 情報密度が高い業務UI / ゆったりとしたメディア型）
- **キーワード**: （3〜5つの形容詞でデザインの雰囲気を表現）

---

## 2. Color Palette & Roles

### Primary（ブランドカラー）
- **Primary** (`#______`): メインのブランドカラー。CTAボタン、リンク等
- **Primary Dark** (`#______`): ホバー・プレス時

### Semantic（意味的な色）
- **Danger** (`#______`): エラー、削除、危険な操作
- **Warning** (`#______`): 警告、注意喚起
- **Success** (`#______`): 成功、完了

### Neutral（ニュートラル）
- **Text Primary** (`#______`): 本文テキスト
- **Text Secondary** (`#______`): 補足テキスト、ラベル
- **Text Disabled** (`#______`): 無効状態のテキスト
- **Border** (`#______`): 区切り線、入力欄の枠
- **Background** (`#______`): ページ背景
- **Surface** (`#______`): カード、モーダル等の面

---

## 3. Typography Rules

### 3.1 和文フォント
- **ゴシック体**: （例: Noto Sans JP, 游ゴシック, ヒラギノ角ゴ ProN）
- **明朝体**（使用する場合）: （例: Noto Serif JP, 游明朝, ヒラギノ明朝 ProN）

### 3.2 欧文フォント
- **サンセリフ**: （例: Helvetica Neue, Arial）
- **等幅**: （例: SFMono-Regular, Consolas, Menlo）

### 3.3 font-family 指定
```css
/* 本文 */
font-family: "和文フォント", "欧文フォント", sans-serif;

/* 等幅 */
font-family: "等幅フォント", monospace;
```

**フォールバックの考え方**:
- 和文フォントを先に指定（日本語の表示品質を優先）
- 最後に generic family（sans-serif / serif）を指定

### 3.4 文字サイズ・ウェイト階層

| Role | Font | Size | Weight | Line Height | Letter Spacing |
|------|------|------|--------|-------------|----------------|
| Display | — | —px | — | — | — |
| Heading 1 | — | —px | — | — | — |
| Heading 2 | — | —px | — | — | — |
| Heading 3 | — | —px | — | — | — |
| Body | — | —px | — | — | — |
| Caption | — | —px | — | — | — |

### 3.5 行間・字間

- **本文の行間 (line-height)**: 1.5〜2.0（日本語は欧文より広めが標準）
- **見出しの行間**: 1.3〜1.5
- **本文の字間 (letter-spacing)**: 0.04em〜0.1em
- **見出しの字間**: 0〜0.05em

### 3.6 禁則処理・改行ルール

```css
word-break: break-all;         /* または keep-all */
overflow-wrap: break-word;      /* 長い URL・英単語の折り返し */
line-break: strict;             /* 厳格な禁則処理 */
```

**禁則対象**:
- 行頭禁止: `）」』】〕〉》」】、。，．・：；？！`
- 行末禁止: `（「『【〔〈《「【`

### 3.7 OpenType 機能

```css
font-feature-settings: "palt" 1;   /* プロポーショナル字詰め（見出し向け） */
font-feature-settings: "kern" 1;   /* カーニング */
```

- 本文には `palt` を適用しない方が可読性が高い場合がある

### 3.8 縦書き（使用する場合のみ）

```css
writing-mode: vertical-rl;
text-orientation: mixed;
```

---

## 4. Component Stylings

### Buttons

**Primary**
- Background: `#______` / Text: `#______`
- Padding: —px —px / Border Radius: —px
- Font Size: —px / Font Weight: —

**Secondary**
- Background: `transparent` / Text: `#______`
- Border: 1px solid `#______`
- Padding: —px —px / Border Radius: —px

### Inputs
- Background: `#______` / Border: 1px solid `#______`
- Border (focus): 1px solid `#______` / Border Radius: —px
- Padding: —px —px / Font Size: —px / Height: —px

### Cards
- Background: `#______` / Border: 1px solid `#______`
- Border Radius: —px / Padding: —px
- Shadow: （Depth & Elevation 参照）

---

## 5. Layout Principles

### Spacing Scale
| Token | Value |
|-------|-------|
| XS / S / M / L / XL / XXL | —px 各 |

### Container
- Max Width: —px / Padding (horizontal): —px

### Grid
- Columns: — / Gutter: —px

---

## 6. Depth & Elevation

| Level | Shadow | 用途 |
|-------|--------|------|
| 0 | none | フラット |
| 1 | `0 1px 2px rgba(0,0,0,0.1)` | カード・ドロップダウン |
| 2 | `0 4px 8px rgba(0,0,0,0.1)` | モーダル・ポップオーバー |
| 3 | `0 8px 24px rgba(0,0,0,0.15)` | ダイアログ |

---

## 7. Do's and Don'ts

### Do
- `font-family` は必ずフォールバックチェーンを指定
- 日本語本文の `line-height` は 1.5 以上
- 色のコントラスト比は WCAG AA 以上
- 余白は Spacing Scale に従う

### Don't
- `font-family` に和文フォント1つだけ指定しない
- 日本語本文に `line-height: 1.2` 以下を使わない
- 全角・半角スペースを混在させない
- テキスト色に純粋な `#000000` を使わない（コントラスト強すぎ）

---

## 8. Responsive Behavior

### Breakpoints
| Name | Width |
|------|-------|
| Mobile | ≤ —px |
| Tablet | ≤ —px |
| Desktop | > —px |

### タッチターゲット
- 最小 44px × 44px（WCAG）

### フォントサイズ調整
- モバイル本文 14–16px、見出しはデスクトップの 70–80%

---

## 9. Agent Prompt Guide

### クイックリファレンス
```
Primary Color: #______
Text Color: #______
Background: #______
Font: "和文フォント", "欧文フォント", sans-serif
Body Size: __px / Line Height: __
```

### プロンプト例
```
このサービスのデザインシステムに従って、ユーザー一覧テーブルを作成してください。
- プライマリカラー: #______
- フォント: 上記 font-family を使用
- 行間: 本文 line-height: __
- テーブルヘッダー背景: #______
- ボーダー: #______
```
```

---

## 9セクションの各章の重要度

| セクション | 重要度 | 理由 |
|-----------|--------|------|
| 1. Visual Theme | ★★☆ | 方向性の宣言。AI エージェントが全体のトーンを掴む |
| 2. Color Palette | ★★★ | 実装の核心。hex 値で一意に定まる |
| 3. Typography | ★★★ | **日本語 UI で最重要**。font-family/line-height/letter-spacing |
| 4. Components | ★★★ | ボタン・入力・カードは全プロジェクト必須 |
| 5. Layout | ★★☆ | Spacing Scale がトークン設計のベース |
| 6. Depth | ★★☆ | Elevation 階層は UI 全体の質感を左右 |
| 7. Do's / Don'ts | ★★★ | AI が陥りがちな失敗を事前防止 |
| 8. Responsive | ★★☆ | Breakpoint とタッチターゲットが最低限 |
| 9. Agent Prompt | ★★★ | **AI エージェント活用の入口**。クイックリファレンス |

## 英語版との違い

日本版テンプレートは以下の項目が強化されている:
- **3.6 禁則処理** — 行頭/行末の禁則対象リスト
- **3.7 OpenType** — `palt`/`kern` の使い分け
- **3.8 縦書き** — vertical-rl の追加仕様
- **和文フォントフォールバック** — Yu Gothic/ヒラギノ/Noto Sans JP のチェーン順

英語版（[brands-en/INDEX.md](brands-en/INDEX.md)）の DESIGN.md と併用する場合は、日本語 UI ではこれら4項目を必ず補うこと。

## 実例（類似ブランド参照）

配色パターン例:
- **赤×白ベース（EC系）**: [brands-jp/mercari.md](brands-jp/mercari.md), [brands-jp/rakuten.md](brands-jp/rakuten.md)
- **青×グレー（業務SaaS）**: [brands-jp/smarthr.md](brands-jp/smarthr.md), [brands-jp/cybozu.md](brands-jp/cybozu.md)
- **ミニマル白基調**: [brands-jp/muji.md](brands-jp/muji.md), [brands-jp/notion.md](brands-jp/notion.md), [brands-jp/note.md](brands-jp/note.md)
- **ダーク系**: [brands-jp/abema.md](brands-jp/abema.md)
- **緑ベース（メッセージ）**: [brands-jp/line.md](brands-jp/line.md)

タイポグラフィ例:
- **読み物系（行間広め）**: [brands-jp/note.md](brands-jp/note.md), [brands-jp/zenn.md](brands-jp/zenn.md)
- **業務密度高**: [brands-jp/rakuten.md](brands-jp/rakuten.md), [brands-jp/cybozu.md](brands-jp/cybozu.md)
- **明朝体混在**: [brands-jp/wired.md](brands-jp/wired.md)

---

## 出典

- **フォーマット原案**: [Google Stitch DESIGN.md overview](https://stitch.withgoogle.com/docs/design-md/overview/)
- **日本版テンプレート**: [kzhrknt/awesome-design-md-jp](https://github.com/kzhrknt/awesome-design-md-jp) (MIT License)
- **英語版ブランドカタログ**: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) / [getdesign.md](https://getdesign.md/) (MIT License)
- ライセンス: [LICENSE-NOTICE.md](LICENSE-NOTICE.md)
