> 目的: GPT Image 2を使ったSEOアイキャッチ画像作成の6ステップワークフロー。構造化プロンプト例3種・16 ref images活用・Thinking mode応用・後処理仕様・チェックリストを提供する。
> このreferenceは skills/design-tools/gpt-image/SKILL.md §5.1 から呼ばれる

skill_id: design/gpt-image/skill/eyecatch-creation
category: design
type: skill
dependencies:
  - design/gpt-image/skill/prompt-engineering
  - design/gemini-image/knowledge/seo-eyecatch-requirements
  - design/gemini-image/knowledge/design-principles

chunks:
  - chunk_id: summary
    content: |
      GPT Image 2を使ったSEOアイキャッチ画像作成ワークフロー。
      前世代比2倍高速な生成を活かした効率的な制作プロセス。
      16 reference imagesによるbrand asset一貫性と多言語テキスト99%精度を活用。
      Thinking modeで複雑なlayoutのcoherent生成が可能。
      Codex CLI $imagegen skill統合でデザイン→コード→アセットのループを実現。
      テンプレートとプロンプト例で即実践可能。

  - chunk_id: workflow-overview
    tags: [ワークフロー, 全体像, プロセス]
    content: |
      アイキャッチ作成ワークフロー（6ステップ）：
      1. 記事分析：タイトル・キーワード・ターゲット把握
      2. コンセプト設計：タイプ・配色・レイアウト決定
      3. プロンプト構築：構造化プロンプトを組み立て
      4. 生成＆調整：高速生成→編集プロンプトで改善
      5. 後処理：リサイズ・圧縮・形式変換
      6. 最終確認：チェックリストで検証
      所要時間目安：5〜15分/枚（高速化）

  - chunk_id: step1-analysis
    tags: [分析, 記事, インプット]
    content: |
      ステップ1：記事分析
      抽出すべき情報：
      □ 記事タイトル（表示テキスト）
      □ メインキーワード（ビジュアルヒント）
      □ 記事タイプ（How-to/比較/解説/ニュース）
      □ ターゲット読者（トーン決定）
      □ 競合のアイキャッチ（差別化ポイント）
      分析例：
      記事「初心者向けSEO対策完全ガイド」
      →キーワード：SEO、初心者、ガイド
      →タイプ：解説・入門
      →ビジュアル：成長、ステップアップ、チェックリスト

  - chunk_id: step2-concept
    tags: [コンセプト, 設計, 方向性]
    content: |
      ステップ2：コンセプト設計
      決定事項：
      1. ビジュアルタイプ：
        - 写真背景＋テキストオーバーレイ
        - イラスト＋テキスト
        - 図解＋タイトル
        - テキスト中心（ミニマル）
      2. 配色（60-30-10）：
        - ベース：白/紺/黒
        - サブ：グレー/補色
        - アクセント：CTA色
      3. レイアウト：
        - 中央配置（インパクト）
        - 左右分割（情報量多）
        - 下帯（写真活かし）

  - chunk_id: step3-prompt-building
    tags: [プロンプト, 構築, 組み立て]
    content: |
      ステップ3：プロンプト構築
      構造化テンプレートに当てはめる：
      ```
      Create an eye-catching blog header image.
      
      Purpose: [用途]
      Title text (EXACT, verbatim): "[タイトル]"
      
      Background: [背景詳細]
      Layout: [レイアウト説明]
      Subject: [メイン要素]
      
      Typography: [フォント指定]
      Colors: [配色詳細]
      Style: [スタイル]
      
      Aspect ratio: 16:9 landscape (1792x1024)
      Constraints: No watermarks, no extra text,
      clean professional look.
      ```
      各セクションを埋めていく。

  - chunk_id: prompt-example-photo
    tags: [プロンプト例, 写真, サンプル]
    content: |
      プロンプト例：写真背景型
      ビジネス系：
      ```
      Create an eye-catching blog header image.
      
      Purpose: SEO article thumbnail
      Title text (EXACT): "SEO GUIDE 2025"
      
      Background: Modern office with glass walls,
      soft natural light from windows,
      blurred bokeh effect
      Layout: Title centered, background fills frame
      
      Typography: Bold sans-serif, white text,
      subtle shadow for readability
      Colors: Blue-tinted office tones,
      white text with slight glow
      Style: Professional, corporate, clean
      
      Aspect ratio: 16:9 landscape
      No watermarks, no logos, no extra elements.
      ```

  - chunk_id: prompt-example-illustration
    tags: [プロンプト例, イラスト, サンプル]
    content: |
      プロンプト例：イラスト型
      フラットデザイン：
      ```
      Create a blog header illustration.
      
      Purpose: Content marketing article banner
      Title text (EXACT): "CONTENT STRATEGY"
      
      Scene: Abstract flat design composition
      Elements: Laptop, charts, megaphone,
      lightbulb icons floating around title
      Layout: Title in center, icons arranged
      symmetrically around it
      
      Typography: Bold geometric sans-serif,
      dark blue text
      Colors: Coral (#FF6B6B), teal (#4ECDC4),
      white background
      Style: Flat design, minimal shadows,
      clean vector aesthetic
      
      16:9 horizontal, no gradients, no 3D effects.
      ```

  - chunk_id: prompt-example-minimal
    tags: [プロンプト例, ミニマル, サンプル]
    content: |
      プロンプト例：ミニマル・テキスト中心
      ```
      Create a minimalist blog header.
      
      Purpose: Tech article thumbnail
      Title text (EXACT): "AI REVOLUTION"
      
      Background: Solid dark navy (#1a1a2e)
      with subtle gradient to lighter navy
      Layout: Large title centered,
      small accent line below
      
      Typography: Ultra bold sans-serif,
      white (#ffffff), large scale
      filling most of frame
      Accent: Thin coral (#ff6b6b) line
      under title
      
      Style: Minimal, typographic focus,
      high contrast, modern
      
      16:9 landscape, no images, no icons,
      text only design.
      ```

  - chunk_id: step4-generation
    tags: [生成, 調整, 改善]
    content: |
      ステップ4：生成＆調整
      Codex CLI $imagegen skillでの起動（推奨）：
      ```
      codex run "$imagegen --model gpt-image-2-2026-04-21 \
        --size 1536x1024 \
        --quality medium \
        --refs ./brand/hero-*.png \
        --prompt '...(構造化プロンプト)...'"
      ```
      初回生成のチェック：
      □ テキストは正確に描画されたか
      □ レイアウトは意図通りか
      □ 色・トーンは適切か（brand assetと一致するか）
      □ 全体のバランスは良いか
      編集プロンプトの書き方（GPT Image 2の1 call edit）：
      ```
      Edit the image:
      
      CHANGE: [変更点]
      KEEP: Title text, overall composition,
      color scheme exactly as is.
      
      Do not alter text content or position.
      ```
      GPT Image 2は前世代比2倍高速なので、
      気軽に数バリエーション試せる。
      Thinking mode活用（複雑layoutのcoherent複数バリエーション）：
      - subscription（Plus / Pro / Business / Enterprise）限定
      - 1 prompt → 最大8 coherent images
      - "Generate 4 coherent variations" を追加

  - chunk_id: editing-prompts
    tags: [編集, プロンプト, 調整]
    content: |
      編集プロンプト集：
      テキスト調整：
      「CHANGE: Make title text 20% larger.
      KEEP: Everything else exactly as is.」
      背景調整：
      「CHANGE: Make background darker,
      increase contrast with text.
      KEEP: Text, layout, style unchanged.」
      色調整：
      「CHANGE: Shift color scheme from blue to green.
      KEEP: Layout, text, composition identical.」
      要素追加：
      「CHANGE: Add subtle icon elements around title.
      KEEP: Title text exact, center position.」
      簡潔に変更点のみ記述。

  - chunk_id: step5-post-processing
    tags: [後処理, リサイズ, 最適化]
    content: |
      ステップ5：後処理
      サイズ調整：
      - GPT Image 2出力：--size指定値（例: 1536x1024）
      - アイキャッチ推奨：1200×630
      - 必要に応じてトリミング/リサイズ
      - 4K出力時（beta）は特に後処理でのリサイズ推奨
      圧縮：
      - 目標：200KB以下
      - JPEG品質85-90%
      - WebP変換で更に軽量化
      形式：
      - 配信用：WebP（最推奨）
      - フォールバック：JPEG
      - 透過必要時：PNG
      ツール：Squoosh、TinyPNG、ImageOptim

  - chunk_id: step6-final-check
    tags: [最終確認, チェック, 品質]
    content: |
      ステップ6：最終確認
      技術チェック：
      □ 1200×630px以上
      □ 200KB以下
      □ WebP/JPEG形式
      デザインチェック：
      □ タイトルが読める
      □ サムネイル表示で判別可能
      □ ブランド一貫性あり
      テキストチェック：
      □ スペルミスなし
      □ 文字化けなし
      □ コントラスト十分
      OGPチェック：
      □ セーフゾーン内に重要要素
      □ 各SNSでの表示確認

  - chunk_id: batch-workflow
    tags: [大量生成, 効率化, バッチ]
    content: |
      大量生成の効率化（GPT Image 2の強み）：
      前世代比2倍高速を活かした大量生成：
      1. テンプレートプロンプトを準備
      2. タイトル部分のみ差し替え
      3. Codex CLI $imagegen skillで連続生成（待ち時間短縮）
      4. 後処理をバッチで実行
      API活用：
      - quality="low" で高速プロトタイプ（~$0.006/1024×1024）
      - 良いものだけ quality="high" で再生成（~$0.211/1024×1024）
      - Batch APIで50%コスト削減
      コスト最適化（WebSearch evidence Q3: lushbinary.com）：
      - low品質：~$0.006/1024×1024
      - medium品質：~$0.053/1024×1024
      - high品質：~$0.211/1024×1024
      - Batch API活用で全て50%削減
      16 ref imagesでbrand consistency維持：
      - brand assetフォルダ（./brand/*.png）を--refsで指定
      - 全バッチで一貫したbrand asset参照

  - chunk_id: chatgpt-images-tab
    tags: [ChatGPT, UI, 活用]
    content: |
      ChatGPT Images 2.0タブの活用（GPT Image 2）：
      プロンプト不要の生成：
      1. サイドバー「Images」タブを開く
      2. プリセットスタイルを選択
      3. テーマを入力
      4. 生成→カスタマイズ
      アイキャッチ向きプリセット：
      - Bold Typography
      - Minimalist Design
      - Professional Corporate
      - Modern Tech
      使い分け：
      - 探索・アイデア出し→Imagesタブ
      - 精密なコントロール→構造化プロンプト + $imagegen skill
      - brand asset一貫性が必要→Codex CLI $imagegen + --refs

  - chunk_id: troubleshooting
    tags: [トラブル, 問題解決, 対処]
    content: |
      よくある問題と対処：
      問題：テキストが正確に出ない
      →引用符で囲む、verbatim指定、短くする
      問題：日本語テキストが崩れる（GPT Image 2は~99%対応）
      →固有名詞・brand nameは生成後に再確認。99%でも100%ではない
      問題：レイアウトがイメージと違う
      →配置を具体的に（top-right, centered等）
      →複雑layoutは "Use reasoning to plan the layout" (Thinking mode)を追加
      問題：brand assetと一致しない
      →--refs ./brand/*.png で16 ref imagesをstyle anchorとして渡す
      問題：色がくすんでいる
      →具体的なHEX値で指定（brand色は特にHEX推奨）
      問題：余計な要素が入る
      →Constraints で明示的に除外
      問題：編集で全体が変わる
      →KEEP セクションで維持要素を明記（GPT Image 2の1 call edit活用）
      問題：4Kが不安定
      →4KはbetaのためAPIは2K（--size 2048x...）でstable推奨

  - chunk_id: checklist
    tags: [チェックリスト, 確認, 完了]
    content: |
      アイキャッチ作成チェックリスト：
      準備：
      □ 記事タイトル・キーワード把握
      □ ビジュアルタイプ決定
      □ 配色決定
      プロンプト：
      □ 構造化テンプレート使用
      □ タイトルを引用符で囲んだ
      □ 具体的な配置・色指定
      □ 制約条件を明記
      生成：
      □ テキスト正確性確認
      □ 必要に応じて編集プロンプトで調整
      後処理：
      □ 1200×630pxにリサイズ
      □ 200KB以下に圧縮
      □ WebP変換
      最終：
      □ サムネイル表示確認
      □ alt属性テキスト準備
