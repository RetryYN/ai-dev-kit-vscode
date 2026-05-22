---
name: gpt-image
description: SEO記事のアイキャッチ・図解・LPヒーロー画像をGPT Image 2（2026/04/21リリース、Codex CLI default）の構造化プロンプトで生成する。Codex CLI内built-in $imagegen skill経由、またはhelix codex --role docs委譲で使用。最大16 reference images / 4K / 多言語99% typography / Thinking mode（reasoning built-in）を活用する実装層スキル。
metadata:
  helix_layer: L5
  triggers:
    - SEO記事のアイキャッチ画像が必要な時
    - インフォグラフィック・図解を作成する時
    - Codex CLIで $imagegen skillを起動する時
    - brand assets（最大16 ref images）をstyle anchorとして画像生成する時
    - 多言語（日本語 / 中国語 / 韓国語）のテキスト入り画像が必要な時
    - Codexに画像生成プロンプト起案を委譲する時 (helix codex --role docs / pe)
    - ブログ・LP・サムネイル・OGP用の画像が必要な時
    - Thinking modeで1 promptからcoherentな複数画像（最大8）を生成する時
    - 図解（フローチャート / ステップ / 比較 / マトリクス / タイムライン等）を作成する時
  verification:
    - "model指定: gpt-image-2-2026-04-21 (date pin)"
    - "解像度: APIは2Kまでstable、4Kはbeta、サイズは16pxの倍数 + aspect ratio max 3:1"
    - "reference images: 最大16枚、brand assetをstyle anchorとして明示"
    - "多言語テキストはnative対応、日本語フォントは指定可（~99% typography accuracy）"
    - "Thinking modeはplus / pro / business / enterpriseで1 prompt → 最大8 coherent images"
    - "Pricing: token-based ($5/$8/$10/$30 per M tokens)、Batch APIで50%削減"
    - "構造化プロンプトを使用: 背景 / 主題 / 詳細 / 制約の順序を遵守"
    - "テキスト要素はverbatim引用符で囲み明示 (Title text (EXACT, verbatim): \"[テキスト]\")"
    - "用途（アイキャッチ / 図解 / 編集）に応じたtemplateを選択し適用"
    - "後処理仕様（アイキャッチ: 1200x630px・200KB以下 / 図解: PNG推奨・100KB以下）を確認"
compatibility:
  claude: true
  codex: true
---

# GPT Image 2 画像生成スキル

## 適用タイミング

このスキルは以下の場合に読み込む:
- SEO記事向けアイキャッチ画像・図解を作成する時
- Codex CLI内 $imagegen skill を起動する時
- brand assets（最大16枚）をstyle anchorとして使う時
- 多言語テキスト入り画像を生成する時
- Codexに構造化プロンプト起案を委譲する時
- 既存画像を部分編集・改善する時

---

## 1. 概要と対象ツール

**対象ツール:**
- GPT Image 2（OpenAI API: `gpt-image-2`、date-pin: `gpt-image-2-2026-04-21`）
- Codex CLI内 built-in `$imagegen` skill（`gpt-image-2-2026-04-21` をデフォルト使用）

**2026年時点の位置づけ（WebSearch evidence Q1: openai.com/index/introducing-chatgpt-images-2-0/, developers.openai.com/api/docs/models/gpt-image-2）:**
- **2026/04/21**: OpenAIが正式発表（"ChatGPT Images 2.0"）
- **2026/04/22以降**: Codex CLIの画像生成default modelに採用
- **DALL-E 3は retired**: GPT Image 2が後継。既存DALL-E 3依存コードは移行必要
- 前世代（GPT Image 1.5）の約2倍高速
- 解像度: 1K / 2K / 4K native対応（最大4096×4096）、APIは2Kまでstable、4Kはbeta

**Codex CLI統合（WebSearch evidence Q2: developers.openai.com/codex/cli, codex.danielvaughan.com/2026/04/27/codex-cli-image-generation-gpt-image-2-visual-development-workflows/）:**
- `$imagegen` built-in skill で `gpt-image-2-2026-04-21` を呼ぶ
- Codex CLI → gpt-image-2 + Figma MCP integration + Playwright visual verification で **design-to-code-to-asset loop** を実現
- `--refs ./brand/*.png` でbrand assetフォルダをstyle anchorとして渡す

**Pricing（WebSearch evidence Q3: lushbinary.com/blog/chatgpt-images-2-developer-guide-gpt-image-2-api-pricing/, mindwiredai.com/2026/04/22/what-is-gpt-image-2-the-complete-breakdown-features-pricing-and-who-gets-access/）:**
- token-based: text input $5/M / image input $8/M / text output $10/M / image output $30/M tokens
- Per-image概算: 約$0.006-0.21/image（品質・解像度依存）
- 1024×1024: low ~$0.006 / medium ~$0.053 / high ~$0.211
- **Batch API**: 上記コストを50%削減
- 事前見積もりが重要（promptトークン量 / quality / resolutionで大きく変動）

---

## 2. HELIX体系内の責務境界

| スキル | 守備範囲 | 本スキルとの関係 |
|---|---|---|
| **gpt-image（本スキル）** | GPT Image 2での**画像生成実装**（構造化プロンプト + Codex委譲） | 画像生成専用実装層 |
| design-tools/diagram | 図解の**設計**（Mermaid/D2によるテキストベース図表、10種類図解タイプ理論） | 設計層。本スキルは実装層（AI生成） |
| design-tools/graphic | Vercel SatoriによるSVG/OGP画像の動的**自動生成** | コード生成型。本スキルはAI生成型 |
| design-tools/web-system | shadcn/uiデザインシステム構築 | 並列（UIコンポーネント層） |
| common/visual-design | ビジュアル設計原則 / AI品質チェック | 上位。本スキルはその実装手段の一つ |
| writing/explain | 記事コピー起草 | 並列（画像 + コピーの組合せで使う） |

**使い分けルール:**
- **テキストベース図解（Mermaid/D2）**: design-tools/diagram
- **SVG/OGP自動コード生成**: design-tools/graphic
- **AI生成アイキャッチ・インフォグラフィック**: 本スキル（gpt-image）

---

## 3. GPT Image 2の特徴（2026年）

| 特徴 | GPT Image 2（2026/04/21） |
|---|---|
| 解像度 | 1K / 2K / 4K native、最大4096×4096。APIは2Kまでstable、4Kはbeta |
| 参照画像 | 最大**16枚**を1 callで受け取り、style anchorとして扱える |
| 多言語テキスト | 日本語 / 中国語 / 韓国語 / ヒンディー語 / ベンガル語 native対応、~**99% typography accuracy** |
| Reasoning | **Thinking mode** built-in（layout計画 / Web検索 / self-check、OpenAI初の画像モデルreasoning機能） |
| 編集 | API 1 callでgeneration + edit（参照画像 + 指示）可能、別inpainting pipeline不要 |
| 速度 | 前世代（GPT Image 1.5）の約**2倍高速** |
| Pricing | token-based、$0.006-0.21/image、Batch APIで50%削減 |
| Codex統合 | `$imagegen` built-in skill、`--model gpt-image-2-2026-04-21` |
| Quality | Low / Medium / High（3段階、custom resolution範囲: max edge 3840px、16px倍数） |
| Thinking mode制限 | Plus / Pro / Business / Enterprise限定。1 prompt → 最大8 coherent images生成 |

詳細な特性・制限・他モデル比較: [references/characteristics.md](references/characteristics.md)

---

## 4. 構造化プロンプト技法

**基本原則 — 「構造化・レイヤー式で書く」（OpenAI公式推奨順序）:**

```
[用途宣言]: Create a [目的] for [用途].

Background/Scene: [背景・環境]
Subject: [主題・中心要素]
Details: [素材・色・照明・テクスチャ]
Constraints: [除外事項・維持事項]
```

**テキスト要素の指定（必須）:**
```
Text (EXACT, verbatim, no extra characters):
"[表示したい文言]"
Typography: [フォントスタイル], [サイズ感], [配置], [色]
Ensure text appears once and is perfectly legible.
```

**GPT Image 2のThinking mode活用（複雑なlayout）:**
```
Use reasoning to plan the layout before generation.
Layout goal: [複数要素の配置・関係を説明]
Coherence: maintain consistent style across all elements.
```

**16 reference imagesのstyle anchor指定:**
```
Reference images: [./brand/hero-*.png] (style anchor)
Maintain: brand color palette, typography style,
visual weight consistent with reference.
```

**編集時（CHANGE/KEEP分離が重要）:**
```
Edit the image:
CHANGE: [変更する内容]
KEEP: [維持する内容 — 毎回明示]
Do not alter [維持要素のリスト].
```

よくある失敗と対策・詳細プロンプトパターン: [references/prompt-engineering.md](references/prompt-engineering.md)

---

## 5. 用途別 quick start

### 5.1 アイキャッチ作成（最短フロー）

```
Create an eye-catching blog header image.

Purpose: SEO article thumbnail
Title text (EXACT, verbatim): "[タイトル]"

Background: [背景説明]
Layout: title centered, [その他要素]

Typography: bold sans-serif, white, high contrast
Colors: [メインカラー] base
Style: professional, modern, clean

Aspect ratio: 16:9 landscape
No watermarks, no extra text.
```

詳細ワークフロー（6ステップ・プロンプト例3種・後処理・チェックリスト）:
[references/eyecatch-creation.md](references/eyecatch-creation.md)

### 5.2 図解作成（最短フロー）

```
Create a professional [図解タイプ] diagram.

Topic: [テーマ]

Elements:
1. "[要素1]"
2. "[要素2]"
3. "[要素3]"

Layout: [レイアウト説明]
Typography: bold labels, readable
Colors: [配色]
Style: clean, professional

No extra decorations.
```

詳細ワークフロー（6種の図解タイプ別テンプレート・チェックリスト）:
[references/diagram-creation.md](references/diagram-creation.md)

---

## 6. Codex委譲 prompt template（HELIX統合の核）

本スキルは**Codex CLIで $imagegen skill を直接起動するか、Codexに画像生成プロンプト起案を委譲する**時の運用スキル。

### Codex CLI内で gpt-image-2 を直接呼ぶ場合（$imagegen skill活用）

```bash
# アイキャッチ（16:9、brand assets参照）
codex run "$imagegen --model gpt-image-2-2026-04-21 \
  --size 1536x1024 \
  --quality high \
  --refs ./brand/hero-*.png \
  --prompt 'Hero for /pricing. Three-tier card layout, soft volumetric light, brand teal #0F766E. Title text (EXACT, verbatim): \"Simple pricing for every team\". Subtitle: \"From startup to enterprise\".' "

# 多言語テキスト入り（日本語 native対応）
codex run "$imagegen --model gpt-image-2-2026-04-21 \
  --size 1200x630 \
  --quality medium \
  --prompt 'Blog header. Title text (EXACT, verbatim): \"SEO完全ガイド2026\". Background: dark navy gradient. Typography: bold Japanese sans-serif, white, centered. No watermarks.' "

# 図解（Thinking mode想定、複雑layout）
codex run "$imagegen --model gpt-image-2-2026-04-21 \
  --size 1024x1024 \
  --quality high \
  --prompt 'Use reasoning to plan the layout. Create a 4-step flowchart. Steps: \"要件定義\" → \"設計\" → \"実装\" → \"検証\". Rounded rectangles, arrows, teal #0F766E, white background, Japanese labels, professional infographic.' "
```

**コマンドオプション一覧:**
- `--model gpt-image-2-2026-04-21`: date pin必須（model family固定）
- `--size WxH`: 16pxの倍数、max edge 3840px、aspect ratio max 3:1
- `--quality low|medium|high`: コスト/品質トレードオフ
- `--refs [path pattern]`: 最大16枚のbrand asset（style anchor）
- `--prompt "..."`: 構造化プロンプト（英語推奨）

### helix codex経由でプロンプト起案を委譲する場合

#### アイキャッチ起案の委譲

```bash
helix codex --role docs --task "$(cat <<'EOF'
GPT Image 2 でアイキャッチ画像を生成するための構造化プロンプトとCodex CLI起動コマンドを起案してください。

タイトル: [タイトル]
ターゲット: [読者 / 目的]
背景: [背景説明]
ブランド色: [hex]
参照画像（任意）: [./brand/ 配下のパス、最大16枚]
多言語テキストの要否: [日本語 / 英語 / 中国語等]

出力フォーマット:
1. 構造化プロンプト（英語、verbatim引用符でテキスト要素を明示、Thinking mode想定でlayout指示を明確化）
2. 推奨設定: --size / --quality / --refs（枚数）
3. Codex CLI起動コマンド（codex run "$imagegen --model gpt-image-2-2026-04-21 ..."）
4. 推定コスト（Pricing token-based、$0.006-0.21/image、Batch APIで50%削減可）
5. 注意事項（多言語はnativeだが日本語固有名詞は再確認、4Kはbeta、Thinking modeはsubscription限定機能）
EOF
)"
```

#### 図解起案の委譲

```bash
helix codex --role docs --task "$(cat <<'EOF'
GPT Image 2 で図解を生成するための構造化プロンプトとCodex CLI起動コマンドを起案してください。

図解テーマ: [テーマを記入]
図解タイプ: [フローチャート / 比較表 / 階層図 / タイムライン / マトリクス / インフォグラフィック]
要素（3〜7個）: [要素をリストアップ]
配色: [配色の希望]
多言語テキスト: [日本語 / 英語等]

出力フォーマット:
1. 構造化プロンプト（英語、各要素のラベルをverbatim引用符で明示）
2. quality推奨値（Highを基本）
3. resolution推奨値（サイズは16pxの倍数）
4. Codex CLI起動コマンド（codex run "$imagegen --model gpt-image-2-2026-04-21 ..."）
5. 後処理仕様（PNG推奨・100KB以下目標）
EOF
)"
```

**委譲先の選択:**
- `--role docs`: プロンプト起案・設計（gpt-5.3-codex-spark）
- `--role pe`: 大量バッチプロンプト生成・速度重視（gpt-5.3-codex）

---

## 7. Geminiとの使い分け

GPT Image 2の強みを踏まえた再評価（WebSearch evidence Q1: openai.com/index/introducing-chatgpt-images-2-0/）:

| 用途 | 推奨モデル | 理由 |
|---|---|---|
| 高速大量生成（バッチ） | **GPT Image 2** | 前世代比2倍高速、Batch API 50%削減 |
| 複雑なインフォグラフィック | **GPT Image 2** | Thinking mode + 多要素一貫性 |
| 構造化された図解 | **GPT Image 2** | 構造化プロンプトへの高精度追従 |
| 多言語テキスト入り画像 | **GPT Image 2** | 日本語 / 中国語 / 韓国語 native 99%精度 |
| brand asset consistency（16 ref） | **GPT Image 2** | 16 reference images style anchor |
| 4K高解像度（beta） | **GPT Image 2** | native 4K、max 4096×4096 |
| Codex CLIフロー統合 | **GPT Image 2** | $imagegen built-in skill直結 |
| 会話型の探索的生成・段階的改善 | Gemini | 自然言語指示、会話継続 |
| Google AI Studio連携 | Gemini | Google ecosystemとの統合 |

---

## 8. 注意事項（制約）

- **DALL-E 3 retired**: 既存DALL-E 3依存コードはGPT Image 2への移行が必要（出典: Q1 openai.com/index/introducing-chatgpt-images-2-0/）
- **4Kはbeta**: production用途は2K（2048px）までstable推奨。4K（4096px）はbeta扱い
- **Thinking modeはsubscription限定**: Plus / Pro / Business / Enterprise。1 prompt → 最大8 coherent images生成はThinking mode依存機能
- **日本語テキスト**: native対応で~99%精度だが、固有名詞・brand nameは生成後に再確認推奨（100%ではない）
- **16 ref imagesの制約**: aspect ratio混在はstyle混乱の原因になる場合あり。同一ratioのbrand assetで統一推奨
- **Pricingはtoken-based**: 1 image単純計算ではなくpromptトークン量 / quality / resolutionで変動。事前見積もり重要
- **サイズ制約**: 両辺16pxの倍数、aspect ratio max 3:1、total pixel 655,360〜8,294,400（WebSearch evidence Q3: evolink.ai/gpt-image-2）
- **キャラクター一貫性**: Thinking modeで改善されたが完全ではない。重要な場合は参照画像を使う
- **コンテンツポリシー**: 実在人物・成人向けコンテンツは制限あり。C2PAメタデータ自動付与

---

## 9. 関連スキル

- `design-tools/diagram` — テキストベース図解設計（Mermaid/D2、設計層）
- `design-tools/graphic` — SVG/OGP自動コード生成（Satori、コード生成型）
- `common/visual-design` — ビジュアル設計原則・AI品質チェック
- `writing/explain` — 記事コピー起草（画像 + コピーの組合せで使う）

---

## 10. 更新履歴

- 2026-05-23: GPT Image 2（2026/04/21リリース）ベースに全面更新。Codex CLI $imagegen skill統合 / 16 ref images / Thinking mode / 多言語99% / DALL-E 3 retired反映。WebSearch 3 query evidence inline追加
- 2026-05-23（初版）: HELIX skill体系へ統合。frontmatter / 責務境界 / Codex委譲template / WebSearch evidence追加（GPT Image 1.5ベース）
- 2025-12: 初版作成（GPT Image 1.5リリース対応）
