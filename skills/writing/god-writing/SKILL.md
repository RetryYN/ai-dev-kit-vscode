---
name: god-writing
description: フロントエンド / LP / SEO 記事 / コピーライティング / UX 文章 / セールスコピーで「神レベル」のライティングを実現する統合スキル。コピー (AIDA/PAS/BAB) + 心理学 (説得・認知バイアス) + UX writing (Clear/Concise/Contextual) + SEO (E-E-A-T/LLMO) + 日本語修辞 + ロジック を網羅した 11 カテゴリ 96+ スキルのライティング最適化システム。
metadata:
  helix_layer: L5
  triggers:
    - フロントエンド / LP を作る時
    - SEO 記事 / コンテンツマーケティング起草時
    - キャッチコピー / タグライン / CTA 文言を作成する時
    - エラーメッセージ / オンボーディング microcopy を書く時
    - セールスページ / ランディングページのコピーを起草する時
    - 「読まれない」「説得力が弱い」「conversion が低い」と感じた時
    - 日本語の文章品質を上げたい時 (修辞 / トーン / リズム)
    - Codex / Claude に LP / FE コピーを委譲する時
    - 取材記事 / インタビュー記事を起草する時
  verification:
    - "採用 framework を明示 (AIDA / PAS / BAB / FAB のどれを使ったか)"
    - "心理学 trigger を意識した (emotional / cognitive / social proof / urgency 等)"
    - "UX writing 3 原則 (Clear / Concise / Contextual) を満たす"
    - "SEO 観点 (E-E-A-T / LLMO / search intent) を考慮"
    - "認知バイアスの濫用回避 (dark pattern 禁止)"
    - "3NOT 突破を確認 (読まない・信じない・行動しないの克服)"
  compatibility:
    claude: true
    codex: true
---

# God Writing — 神レベルライティング統合スキル

## 適用タイミング

このスキルは以下の場合に読み込む:

- フロントエンド / LP を作る時
- SEO 記事 / コンテンツマーケティング起草時
- キャッチコピー / タグライン / CTA 文言を作成する時
- エラーメッセージ / オンボーディング microcopy を書く時
- セールスページ / ランディングページのコピーを起草する時
- 「読まれない」「説得力が弱い」「conversion が低い」と感じた時
- 日本語の文章品質を上げたい時 (修辞 / トーン / リズム)
- Codex / Claude に LP / FE コピーを委譲する時
- 取材記事 / インタビュー記事を起草する時

---

## 1. 概要

God Writing System は 11 カテゴリ・96 スキルを組み合わせて最高品質の文章を生成するライティング最適化システム。全てのスキルは `philosophy/` の原則に従属し、目的・読者・媒体に応じて必要なスキルを選択・適用する。

**神レベルの定義**:
- 3NOT 突破: 「読まない・信じない・行動しない」の 3 つの壁を全て越える
- E-E-A-T 準拠: 経験・専門性・権威性・信頼性を満たす
- 読者最適化: ターゲットの認知レベル・関心に完全適合
- 構造明確: 論理的で追跡可能な構成
- 行動誘導: 明確な CTA と強力な動機付け

**タスク別スキル組み合わせ**:

| タスク | 必須カテゴリ |
|--------|------------|
| LP / セールスページ | philosophy + copywriting + psychology + sales + japanese |
| SEO 記事 | philosophy + seo + logical + japanese + psychology |
| FE microcopy / UI 文言 | philosophy + ux + japanese |
| 取材記事 | philosophy + interview + japanese + psychology |
| マニュアル / 技術文書 | philosophy + technical + logical + japanese |
| SNS コピー | philosophy + copywriting + psychology + japanese |

---

## 2. HELIX 体系内の責務境界 (重要、近接 skill との分離明示)

| skill | 守備範囲 | 本 skill との関係 |
|-------|---------|-----------------|
| **god-writing (本 skill)** | LP / FE / SEO / コピー / 心理 / UX / 日本語修辞 / ロジック / 取材記事の統合 | 統合層、11 カテゴリ網羅 |
| writing/japanese | textlint 統合による技術文書の日本語品質チェック (ja-technical-writing / ai-writing / JTF-style) | **重複領域**: 本 skill `references/japanese/` に full copy あり。既存 skill は lint ツール駆動の品質チェック中心、本 skill は修辞・トーン・リズムの応用層も含む |
| writing/explain | 技術文書の 4 部構成 (概要・使い方・例・制約) + EEAT コンテンツ品質監査 | **重複領域**: 本 skill `references/seo/knowledge/eeat.md`、`references/technical/` と一部重なる。既存は技術文書 / README / API doc 特化、本 skill は LP / コピー・マーケ文章まで含む |
| writing/social | SNS 投稿テンプレート (X/LinkedIn/Bluesky) + GEO 設計 | **重複領域**: 本 skill `references/copywriting/social-copy.md` と重なる。既存は技術広報の投稿案生成、本 skill はマーケ・セールスコピーを含む広範な範囲 |
| writing/story | ストーリーテリング | **重複領域**: 本 skill `references/copywriting/storytelling.md` と重なる |
| writing/presentation | プレゼン資料文章 | 並列 (LP は重なるが presentation slide は別 scope) |
| design-tools/web-system | shadcn/ui FE 設計・デザイントークン | **接続点**: 本 skill は文章層、web-system は UI コンポーネント・デザイン層 |
| gpt-image | アイキャッチ画像生成 | **接続点**: LP / SEO 記事は画像 + コピーの組み合わせ |
| workflow/requirements-deriver | 非機能要件導出 | **接続点**: LP / FE は使用性・信頼性の非機能要件を持つ |
| common/visual-design | ビジュアル設計原則 / DESIGN.md | **接続点**: LP は文章 + ビジュアルの統合設計 |
| workflow/doc-system-architect | ドキュメントシステム設計 | 並列 (本 skill は文章品質、doc-system-architect は文書構造設計) |

**使い分けルール**:
- **技術文書の日本語 lint チェック** → writing/japanese
- **README / API doc / HANDOVER の構成** → writing/explain
- **SNS 単発投稿 (技術広報)** → writing/social
- **LP / FE / セールスコピー / UX writing / 心理学 trigger を統合して使う** → **本 skill**
- **取材記事 / インタビュー記事** → **本 skill** (`references/interview/`)

**将来統合候補**: 本 skill 統合により writing/japanese / writing/explain / writing/social / writing/story の機能の一部が本 skill に網羅される。既存 skill は基礎 / lint ツール用途で残す、本 skill は応用 / マーケ / LP 用途で使う、という棲み分けで運用。

---

## 3. 11 カテゴリ navigation (references/ 地図)

詳細 file 一覧は `references/INDEX.md` を参照。

| カテゴリ | 守備範囲 | LP/FE 優先度 |
|---------|---------|------------|
| **philosophy** | 神ライティング 5 原則 (読者中心・目的従属・価値密度・信頼構築・構造先行) | 全文章の基盤 |
| **copywriting** ★ | AIDA / PAS / BAB / コピー公式 / power words / ヘッドライン / フック / ストーリーテリング | LP ★★★ |
| **psychology** ★ | 認知バイアス / 説得 / 感情 trigger / social proof / urgency / 信頼構築 / 欲求増幅 | LP ★★★ |
| **sales** ★ | LP 構造 / CTA 設計 / 価格心理 / value proposition / closing / testimonial | LP ★★★ |
| **seo** | E-E-A-T / LLMO / keyword / heading / title / featured snippet / meta description | SEO 記事 ★★★ |
| **ux** ★ | microcopy / error message / onboarding / form / notification | FE ★★★ |
| **logical** | 論理構造 / 主張パターン / 証拠提示 / 反論処理 / 要約 / 比較 / 提案 | 全文章 ★★ |
| **japanese** | 文法 / 漢字仮名バランス / 句読点 / トーン / リズム / 修辞 / 比喩 | 日本語品質 ★★ |
| **technical** | 技術文書 / API doc / specification / tutorial / 技術ブログ | 技術文書 ★★ |
| **interview** | 取材設計 / インタビュー / 事例記事 / 専門家インタビュー | 取材記事 ★★ |
| **meta** | スキル設計 / メタ学習 | スキル設計 |

★ = LP / FE 文章で特に重要

---

## 4. LP / FE 用 quick start

### 4.1 LP コピー起草フロー (推奨)

1. **audience 判定**: problem-aware なら PAS、unaware / lightly aware なら AIDA
   - WebSearch evidence (2026): AIDA は 27% conversion 向上、PAS は問題認識済の audience に強い (出典: universaldigitalservices.com, landy-ai.com/blog/landing-page-copywriting-frameworks)
2. **psychology layer**: emotional trigger / social proof / urgency / trust を組み込む (`references/psychology/skill/`)
3. **sales layer**: LP 構造 / CTA 設計 / value proposition (`references/sales/skill/lp-structure.md`)
4. **copywriting layer**: ヘッドライン / フック / power words (`references/copywriting/`)
5. **UX layer**: form microcopy / error message / CTA copy (`references/ux/skill/`)
6. **SEO layer**: E-E-A-T / search intent (`references/seo/`)
7. **日本語修辞 layer**: トーン / リズム / 漢字仮名バランス (`references/japanese/`)

**Layering 推奨**: 広告コピーは PAS → LP 全体は AIDA という Layering が最高効果 (出典: thrivethemes.com/copywriting-formulas)

### 4.2 FE microcopy 起草フロー

1. **UX 3 原則 (Clear / Concise / Contextual)** を適用 (`references/ux/knowledge/ux-writing-basics.md`)
   - WebSearch evidence (2026): Slack onboarding で 93% 完遂達成、エラーメッセージ解決誘導で Google Pay サポート 15% 減 (出典: ericwongcontentstrategist.com 2026 guide)
2. **エラーメッセージは解決誘導**: "invalid input" → "Please enter a valid phone number" 形式 (`references/ux/skill/error-message-design.md`)
3. **オンボーディング microcopy**: ステップ進捗 / 価値の即時提示 (`references/ux/skill/onboarding-writing.md`)
4. **dark pattern 禁止**: psychology 濫用回避 (false urgency / fake testimonial / misleading CTA)

### 4.3 SEO 記事起草フロー

1. **キーワード調査 + search intent 判定** (`references/seo/skill/keyword-research.md`)
2. **コンテンツ構造設計 + 見出し最適化** (`references/seo/skill/heading-structure.md`)
3. **E-E-A-T 準拠**: 経験・専門性・権威性・信頼性を満たす (`references/seo/knowledge/eeat.md`)
4. **LLMO 対応**: AI 検索エンジン最適化 (`references/seo/knowledge/llmo.md`)
5. **ロジック強化**: 論理構造 / 証拠提示 (`references/logical/skill/logical-structuring.md`)

---

## 5. 実行順序 (元素材 SKILL.md 踏襲)

```
1. philosophy/ で原則確認 (5 原則 + 3 法則)
2. {category}/knowledge/ で理論把握
3. {category}/skill/ で技法適用
4. japanese/ で表現最適化 (トーン / リズム / 漢字仮名バランス)
5. verification チェック (frontmatter §verification 全項目)
```

---

## 6. Codex / Claude 委譲 prompt template

```bash
helix codex --role docs --task "$(cat <<'EOF'
LP の hero section コピーを起案してください。

製品: [製品名 / カテゴリ]
ターゲット: [problem-aware / unaware / lightly aware]
USP: [unique selling point]
CTA: [メイン CTA 文言]

採用 framework: AIDA / PAS / BAB のいずれかを選定 (理由を明示)
心理 trigger: emotional / social proof / urgency / trust から 2-3 個選定
日本語修辞: トーン (formal / casual)、リズム (短文中心 / 長文混在)

参照 references:
- skills/writing/god-writing/references/copywriting/knowledge/copy-formulas.md
- skills/writing/god-writing/references/psychology/skill/
- skills/writing/god-writing/references/sales/skill/lp-structure.md

出力フォーマット:
- 採用 framework と理由 (1-2 行)
- ヘッドライン 3 案 + 推奨理由
- subheadline (採用 framework を踏まえて 1 案)
- bullet 3-5 個 (benefit / feature の書き分けを明示)
- CTA 文言 2 案 + UX writing 3 原則 (Clear / Concise / Contextual) チェック
- 採用しない dark pattern を 1 つ明示
EOF
)"
```

**UX microcopy 委譲 template**:

```bash
helix codex --role docs --task "$(cat <<'EOF'
FE の [画面名] のマイクロコピーを設計してください。

対象要素: [error message / onboarding / form / notification / CTA]
状況: [具体的な状況説明]

UX writing 3 原則を適用:
- Clear: 誰が何をすべきか明確
- Concise: 最少の言葉で最大の情報
- Contextual: 表示タイミングと文脈に適合

参照: skills/writing/god-writing/references/ux/skill/
dark pattern 禁止 (false urgency / misleading CTA 等)

出力:
- 推奨文言 (日本語 + 必要に応じて英語)
- 3 原則チェック結果
- アンチパターン 1 例
EOF
)"
```

---

## 7. 注意事項 / アンチパターン

- **dark pattern 禁止**: 認知バイアス濫用 (false urgency / fake testimonial / misleading CTA 等) は信頼喪失につながる
- **AI 生成は drafting 加速のみ**: emotion / context 理解は人間が担う (出典: ericwongcontentstrategist.com 2026)。AI 生成コピーは必ず人間が感情・文脈の観点でレビューする
- **日本語精度**: 修辞・トーン・リズムは `references/japanese/advanced/` を必ず参照
- **Copywriting 公式は不変**: 人間心理に基づくため 2026 年現在も AIDA / PAS / BAB は有効 (出典: medium.com/2026 complete guide)
- **3NOT チェック必須**: 「読まない・信じない・行動しない」全てを突破できているか確認 (`references/philosophy/three-nots.md`)

---

## 8. 品質チェックリスト (LP / FE / SEO 共通)

### LP コピー完了判定

```
□ 採用 framework (AIDA / PAS / BAB) を明示した
□ ヘッドラインが読者の pain point または desire を直撃している
□ social proof (数字 / testimonial / 事例) を含む
□ urgency / scarcity が自然かつ honest (false urgency 禁止)
□ CTA が Clear / Concise / Contextual を満たす
□ 3NOT 突破: 読む理由・信じる根拠・行動動機が揃っている
□ dark pattern を含まない
□ 日本語のトーン・リズムが対象読者に適合している
```

### FE microcopy 完了判定

```
□ Clear: 誰が何をすべきか 1 文で明確
□ Concise: 余分な言葉がない (動詞から始まる)
□ Contextual: 表示タイミングと文脈に適合
□ エラーメッセージは解決誘導型 (「何が問題か」より「どう直すか」)
□ 日本語と英語の使い分けがブランドガイドラインに沿っている
□ misleading / false urgency の文言がない
```

### SEO 記事完了判定

```
□ E-E-A-T: 経験・専門性・権威性・信頼性が文章に現れている
□ search intent と記事内容が一致している
□ 見出し構造 (H1/H2/H3) が論理的
□ タイトルとメタディスクリプションが最適化されている
□ LLMO 対応: AI 検索エンジンに拾われる構造化
□ 冗長な表現を削除し価値密度が高い
```

---

## 9. タスク判定フロー (どのカテゴリを使うか迷ったとき)

```
文章タスク受領
  ↓
主目的は何か？
  ├── 販売 / conversion → sales + copywriting + psychology (LP フロー)
  ├── SEO 流入 → seo + logical + japanese
  ├── UI 誘導 / 操作支援 → ux + japanese
  ├── 情報提供 → logical + japanese + technical
  └── 取材記録 → interview + japanese + psychology
  ↓
媒体は何か？
  ├── LP / セールスページ → sales/skill/lp-structure.md 最重要
  ├── FE 画面 → ux/skill/ 全般
  ├── SEO 記事 → seo/skill/ + logical/skill/
  └── 技術文書 → technical/skill/ + logical/skill/
  ↓
読者は誰か？
  ├── unaware (問題未認識) → AIDA framework
  ├── problem-aware → PAS framework
  └── solution-aware → FAB / benefit-writing
  ↓
philosophy/principles.md で 5 原則を確認して執筆開始
```

---

## 10. 関連スキル

- writing/japanese — 技術文書の日本語 lint チェック (基礎)
- writing/explain — 技術文書の 4 部構成 / README / API doc
- writing/social — SNS 単発投稿 (技術広報)
- writing/story — ストーリーテリング (基礎)
- writing/presentation — プレゼン資料
- design-tools/web-system — FE UI コンポーネント / デザイントークン
- common/visual-design — LP ビジュアル設計
- gpt-image — アイキャッチ画像生成 (LP / SEO 記事との組み合わせ)
- workflow/requirements-deriver — 非機能要件導出 (使用性・信頼性)

---

> 詳細 references INDEX: `skills/writing/god-writing/references/INDEX.md`
