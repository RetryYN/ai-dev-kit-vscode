> 目的: GPT Image 2のための構造化プロンプト設計技法。OpenAI公式推奨パターンの習得と図解・アイキャッチ特化テンプレートを提供する。16 ref images / Thinking mode / 多言語テキスト対応を含む2026年版。
> このreferenceは skills/design-tools/gpt-image/SKILL.md §4 から呼ばれる

skill_id: design/gpt-image/skill/prompt-engineering
category: design
type: skill
dependencies:
  - design/gpt-image/knowledge/gpt-image-characteristics
  - design/gemini-image/knowledge/design-principles

chunks:
  - chunk_id: summary
    content: |
      GPT Image 2のためのプロンプト設計技法。
      OpenAI公式推奨の「構造化プロンプト」パターンを習得。
      Geminiとは異なるアプローチで最大効果を引き出す。
      16 ref images / Thinking mode / 多言語テキスト活用を含む2026年版。
      図解・アイキャッチ特化のテンプレート付き。

  - chunk_id: core-principle
    tags: [原則, 基本, 考え方]
    content: |
      GPT Image 2プロンプトの核心原則：
      「構造化・レイヤー式で書く」
      Gemini：説明的な文章
      GPT Image 2：構造化されたセグメント
      推奨順序（OpenAI公式）：
      背景/シーン → 主題 → 詳細 → 制約条件
      複雑なプロンプトは：
      - ラベル付きセグメントに分割
      - 改行で区切る
      - 1段落に詰め込まない
      GPT Image 2追加原則：
      - Thinking mode活用で複雑layoutは "Use reasoning to plan the layout" を先頭に追加
      - 16 ref imagesを使う場合は "Reference images: [path] (style anchor)" セクションを追加

  - chunk_id: prompt-structure
    tags: [構造, フレームワーク, テンプレート]
    content: |
      プロンプトの基本構造（5層）：
      1. 用途宣言：何を作るか（ad, UI mock, infographic）
      2. シーン/背景：環境、設定
      3. 主題：中心となる要素
      4. 詳細：素材、テクスチャ、色、照明
      5. 制約：除外事項、維持事項
      テンプレート：
      ```
      [用途]: Create a [目的] for [用途].
      
      Scene: [背景説明]
      Subject: [主題説明]
      Details: [素材、色、照明]
      Constraints: [制約、除外事項]
      ```

  - chunk_id: specificity-matters
    tags: [具体性, 詳細, 品質]
    content: |
      具体性が品質を決める：
      曖昧な指示→曖昧な結果
      具体的な指示→意図通りの結果
      悪い例：
      「ビジネス風の画像」
      良い例：
      「モダンなオフィスのガラス会議室、
      自然光が差し込む、ミニマルなインテリア、
      テーブルにMacBookと観葉植物」
      具体化すべき要素：
      - 素材（木、ガラス、金属）
      - テクスチャ（光沢、マット、風化）
      - 形状（角丸、直線的）
      - 色（具体的な色名）

  - chunk_id: quality-cues
    tags: [品質, キュー, 指定]
    content: |
      効果的な品質キューの使い方：
      避けるべき：
      - 「8K」「ultra-detailed」「best quality」
      - 汎用的すぎて効果薄い
      効果的：
      - 具体的なテクスチャ：「natural skin pores」
      - 素材の質感：「weathered wood grain」
      - 撮影技法：「shot on 35mm film」
      - 照明詳細：「soft diffuse morning light」
      写実系の場合：
      - カメラ用語が最も効果的
      - lens, aperture, lighting で制御
      イラスト系の場合：
      - 画材・技法で指定
      - 「textured brushstrokes」「flat vector」

  - chunk_id: text-rendering-prompts
    tags: [テキスト, 文字, 指定, 多言語]
    content: |
      テキスト描画のプロンプト技法（GPT Image 2）：
      基本ルール：
      1. 正確な文言を引用符で囲む
      2. 「verbatim」「exact」を指定
      3. フォントスタイルを明示
      4. 配置を具体的に
      テンプレート：
      ```
      Text (EXACT, verbatim, no extra characters):
      "[表示したい文言]"
      Typography: [フォントスタイル], [サイズ感],
      [配置], [色]
      Ensure text appears once and is perfectly legible.
      ```
      例（英語）：
      「Text: "SEO BASICS" in bold sans-serif,
      white on dark blue, centered at top,
      high contrast, clean kerning.」
      例（日本語 / GPT Image 2 native対応）：
      「Title text (EXACT, verbatim): "SEO完全ガイド2026"
      Typography: bold Japanese sans-serif, white, centered.
      ~99% typography accuracy for Japanese text.
      Verify brand names and proper nouns after generation.」
      多言語テキスト（GPT Image 2新機能）：
      - 日本語 / 中国語 / 韓国語 / ヒンディー語 / ベンガル語はnative対応
      - ~99% typography accuracy（出典: wavespeed.ai/blog/posts/gpt-image-2-2026/）
      - 英語変換不要、そのまま指定可能
      - 固有名詞・brand nameは生成後に再確認推奨

  - chunk_id: composition-instructions
    tags: [構図, 配置, レイアウト]
    content: |
      構図の指示方法：
      フレーミング指定：
      - 「close-up」「wide shot」「full body」
      - 「centered with negative space on left」
      視点指定：
      - 「eye-level」「top-down」「low-angle」
      - 「aerial view」「first-person perspective」
      配置指定：
      - 「subject positioned in right third」
      - 「logo top-right corner」
      - 「text band across bottom」
      照明/ムード：
      - 「soft diffuse light」
      - 「golden hour warm tones」
      - 「high-contrast dramatic」
      アスペクト比：
      - 「16:9 landscape」「1:1 square」
      - 「9:16 portrait for mobile」

  - chunk_id: constraints-negative
    tags: [制約, 除外, ネガティブ]
    content: |
      制約・除外の指定方法：
      明示的な除外：
      - 「No text overlays」
      - 「No watermarks」
      - 「No extra elements」
      - 「No logos」
      維持指定（編集時重要）：
      - 「Do not change the background」
      - 「Preserve the exact composition」
      - 「Keep the original lighting」
      - 「Maintain facial features」
      スタイル制約：
      - 「Photorealistic style only」
      - 「No cartoonish elements」
      - 「Clean, no clutter」
      制約は最後にまとめて記述。

  - chunk_id: infographic-prompts
    tags: [インフォグラフィック, 図解, テンプレート]
    content: |
      インフォグラフィック用プロンプト：
      基本テンプレート：
      ```
      Create a professional infographic.
      
      Topic: [テーマ]
      Layout: [レイアウト説明]
      Sections:
      - [セクション1]: [内容]
      - [セクション2]: [内容]
      
      Style: clean, modern, professional
      Colors: [配色]
      Typography: bold headers, readable body text
      No extra decorations, focused layout.
      ```
      コツ：
      - セクションを明示的にリスト化
      - 各要素の内容を具体的に
      - 「clean」「focused」で余計な装飾を防ぐ

  - chunk_id: diagram-prompts
    tags: [図解, ダイアグラム, テンプレート]
    content: |
      図解用プロンプトテンプレート：
      フローチャート：
      ```
      Create a flowchart diagram.
      
      Steps (left to right):
      1. [Step1] → 2. [Step2] → 3. [Step3]
      
      Style: clean boxes with rounded corners
      Arrows: connecting each step
      Colors: [配色]
      Labels: inside each box, bold text
      Background: white, minimal
      ```
      比較図：
      ```
      Create a comparison chart.
      
      Comparing: [A] vs [B]
      Layout: two columns, side by side
      Items to compare:
      - [項目1]
      - [項目2]
      
      Use checkmarks and X marks for features.
      Clean professional style.
      ```

  - chunk_id: eyecatch-prompts
    tags: [アイキャッチ, バナー, テンプレート]
    content: |
      アイキャッチ用プロンプトテンプレート：
      基本形：
      ```
      Create an eye-catching blog header image.
      
      Purpose: SEO article thumbnail
      Title text (EXACT): "[タイトル]"
      
      Background: [背景説明]
      Layout: title centered, [その他要素]
      
      Typography: bold sans-serif, high contrast
      Colors: [メインカラー] base, white text
      Style: professional, modern, clean
      
      Aspect ratio: 16:9 landscape
      No watermarks, no extra text.
      ```
      写真背景型：
      ```
      Photo-style blog banner.
      
      Scene: [シーン説明]
      Overlay: semi-transparent [色] gradient
      Title: "[タイトル]" in white, centered
      
      Photorealistic, natural lighting.
      16:9 horizontal format.
      ```

  - chunk_id: iterative-editing
    tags: [反復, 編集, 改善]
    content: |
      反復編集のベストプラクティス：
      原則：変更点と維持点を明確に分離
      編集プロンプトの構造：
      ```
      Edit the image:
      
      CHANGE: [変更する内容]
      KEEP: [維持する内容]
      
      Do not alter [維持要素のリスト].
      ```
      例：
      「Edit the image:
      CHANGE: Make the background warmer,
      add golden hour lighting.
      KEEP: The subject's face, pose, clothing,
      and composition exactly as is.
      Do not alter facial features or expression.」
      毎回、維持事項を再記述することでドリフト防止。

  - chunk_id: labeled-segments
    tags: [ラベル, セグメント, 整理]
    content: |
      ラベル付きセグメントの活用：
      複雑なプロンプトを整理する技法
      形式：
      ```
      Scene: [シーン説明]
      Subject: [主題説明]
      Action: [動作・状態]
      Style: [スタイル指定]
      Lighting: [照明]
      Camera: [カメラ設定]
      Constraints: [制約]
      ```
      効果：
      - モデルが各要素を区別しやすい
      - 修正時にどこを変えるか明確
      - 長いプロンプトでも構造維持
      改行やコロンで明確に区切る。

  - chunk_id: common-mistakes
    tags: [失敗, 間違い, 注意]
    content: |
      よくある失敗と対策：
      失敗1：矛盾する指示
      例：「photorealistic cartoon」
      →どちらかに統一、または融合方法を明示
      失敗2：背景の省略
      「赤いスポーツカー」だけでは背景が不定
      →「on an empty desert highway」を追加
      失敗3：汎用的な品質語
      「8K ultra HD best quality」は効果薄
      →具体的なテクスチャ・照明を記述
      失敗4：テキストの曖昧指定
      →引用符で囲み、verbatimを指定
      失敗5：1プロンプトに詰め込みすぎ
      →段階的に生成・編集

  - chunk_id: ref-images-anchor
    tags: [reference images, brand, style anchor]
    content: |
      16 Reference Imagesのstyle anchor活用（GPT Image 2新機能）：
      概要：
      - 1 callで最大16枚のbrand assetをstyle anchorとして渡す
      - brand色・typography・visual weightの一貫性を維持
      プロンプトへの組み込み方：
      ```
      Reference images: [./brand/hero-*.png] (style anchor)
      Maintain: brand color palette from reference,
      typography style from reference,
      visual weight consistent with reference.
      ```
      Codex CLIコマンドでの指定：
      ```
      codex run "$imagegen --model gpt-image-2-2026-04-21 \
        --refs ./brand/hero-*.png \
        --prompt '...'"
      ```
      推奨運用：
      - brand assetsはaspect ratio統一（混在はstyle混乱の原因）
      - 過去のhero / ロゴ / typography specimenなどをフォルダ管理
      - 最大16枚を活用してbrand一貫性を確保

  - chunk_id: thinking-mode-prompts
    tags: [Thinking mode, reasoning, layout計画]
    content: |
      Thinking mode活用のプロンプト技法（GPT Image 2新機能）：
      適用シーン：
      - 複雑な複数要素のlayout計画
      - 1 promptからcoherentな複数画像（最大8）
      - character/object一貫性の維持
      プロンプトへの組み込み方：
      ```
      Use reasoning to plan the layout before generation.
      Layout goal: [複数要素の配置・関係を説明]
      Coherence: maintain consistent style, color palette,
      and visual weight across all elements.
      ```
      複数画像生成（Plus / Pro / Business / Enterprise）：
      ```
      Generate 4 coherent variations of this hero image.
      Use reasoning to maintain character, style,
      and composition consistency across all 4.
      [通常の構造化プロンプト]
      ```
      注意：
      - Thinking modeはPlus / Pro / Business / Enterpriseのみ
      - 利用不可の場合でも通常プロンプトは機能する

  - chunk_id: gemini-vs-gpt-prompting
    tags: [比較, Gemini, スタイル]
    content: |
      Gemini vs GPT Image 2 プロンプトスタイル：
      Gemini向き：
      「クリーンでプロフェッショナルなビジネス
      インフォグラフィックを作成してください。
      青をベースに、右側に棒グラフ、
      左側にテキスト説明を配置。」
      GPT Image 2向き：
      ```
      Use reasoning to plan the layout before generation.
      Create a professional business infographic.
      
      Layout: text on left, bar chart on right
      Colors: blue base, white accents
      Style: clean, minimal, corporate
      Typography: bold headers, readable labels
      
      No decorative elements, focused design.
      ```
      GPTは構造化、Geminiは自然文。
      GPT Image 2はThinking modeで複雑layoutをさらに正確に処理。

  - chunk_id: checklist
    tags: [チェックリスト, 確認, 完了]
    content: |
      GPT Image 2プロンプトチェックリスト：
      構造：
      □ 用途を最初に宣言したか
      □ シーン→主題→詳細→制約の順か
      □ 複雑な場合はラベル付きセグメントか
      □ 改行で適切に区切っているか
      具体性：
      □ 素材・テクスチャを明示したか
      □ 色を具体的に指定したか（HEX値推奨）
      □ カメラ/照明用語を使ったか
      テキスト：
      □ 文言を引用符で囲んだか
      □ verbatim/exactを指定したか
      □ フォント・配置を明示したか
      □ 日本語等多言語テキストはnative指定か（英語変換不要）
      GPT Image 2固有：
      □ 16 ref imagesを使う場合はstyle anchorセクションを追加したか
      □ 複雑layoutはThinking mode（reasoning）を活用したか
      □ model指定: gpt-image-2-2026-04-21（date pin）
      □ --size は16pxの倍数、aspect ratio max 3:1を確認したか
      制約：
      □ 除外事項を明記したか
      □ 編集時は維持事項を再記述したか
