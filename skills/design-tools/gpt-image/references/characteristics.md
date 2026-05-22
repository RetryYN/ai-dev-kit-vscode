> 目的: GPT Image 2のモデル特性・強み・制約・他モデル比較の知識ベース。Geminiとの使い分け判断にも役立つ。
> このreferenceは skills/design-tools/gpt-image/SKILL.md §3 から呼ばれる

skill_id: design/gpt-image/knowledge/gpt-image-characteristics
category: design
type: knowledge
dependencies:
  - design/gemini-image/knowledge/design-principles

chunks:
  - chunk_id: summary
    content: |
      GPT Image 2の特性・能力・制約の知識ベース。
      OpenAI最新の画像生成モデルの強み・弱みを理解し、
      効果的なプロンプト設計と用途選定に活かす。
      Codex CLI統合・Thinking mode・16 ref imagesを含む2026年版。
      Geminiとの使い分け判断にも役立つ。

  - chunk_id: model-overview
    tags: [概要, モデル, 特徴]
    content: |
      GPT Image 2の概要：
      リリース：2026年4月21日（正式発表: openai.com/index/introducing-chatgpt-images-2-0/）
      位置づけ：OpenAI最新フラッグシップ画像モデル
      date-pin：gpt-image-2-2026-04-21
      Codex CLI default：2026/04/22以降
      アクセス方法：
      - Codex CLI：$imagegen built-in skill（gpt-image-2-2026-04-21 default）
      - API：gpt-image-2（developers.openai.com/api/docs/models/gpt-image-2）
      - ChatGPT：Plus / Pro / Business / Enterprise
      進化の流れ：
      DALL-E 3（retired） → GPT-4o Image → GPT Image 1 → GPT Image 1.5 → **GPT Image 2**
      重要：DALL-E 3はretired。既存DALL-E 3依存コードはGPT Image 2に移行必要。
      特徴：ネイティブマルチモーダル / Thinking mode built-in / 16 ref images / 多言語native

  - chunk_id: core-strengths
    tags: [強み, 得意, 能力]
    content: |
      GPT Image 2の主な強み（出典: wavespeed.ai/blog/posts/gpt-image-2-2026/）：
      1. 速度：
        - 前世代（GPT Image 1.5）の約2倍高速
        - 反復改善・バッチ生成がスムーズ
      2. Thinking mode（reasoning built-in）：
        - OpenAI初の画像モデルreasoning機能
        - 生成前にlayout計画 / Web検索 / self-checkが可能
        - 複雑なレイアウトの coherent 生成に有効
      3. 16 Reference Images：
        - 1 callで最大16枚のbrand assetをstyle anchorとして受け取る
        - brand色・typography・visual weightの一貫性を維持
      4. 多言語テキスト描画：
        - 日本語 / 中国語 / 韓国語 / ヒンディー語 / ベンガル語 native対応
        - ~99% typography accuracy（WebSearch evidence Q1）
        - non-Latin文字をnative処理
      5. 高解像度：
        - 1K / 2K / 4K native対応（max 4096×4096）
        - APIは2Kまでstable、4Kはbeta
      6. 編集統合：
        - API 1 callでgeneration + edit
        - 別inpainting pipeline不要
        - CHANGE/KEEP分離で部分編集が正確

  - chunk_id: codex-cli-integration
    tags: [Codex, CLI, 統合, $imagegen]
    content: |
      Codex CLI統合の詳細（出典: codex.danielvaughan.com/2026/04/27/codex-cli-image-generation-gpt-image-2-visual-development-workflows/）：
      built-in skill：
      - `$imagegen` skillでgpt-image-2を呼ぶ
      - helix codex経由でも透過的に利用可能
      コマンド例：
      ```
      codex run "$imagegen --model gpt-image-2-2026-04-21 \
        --size 1536x1024 \
        --quality high \
        --refs ./brand/hero-*.png \
        --prompt 'Hero layout, brand teal #0F766E. Title: \"Pricing\".' "
      ```
      design-to-code-to-asset loop：
      - gpt-image-2 → Figma MCP integration → Playwright visual verification
      - 前段設計と後段検証を含む自動化フロー
      16 ref imagesのフォルダ指定：
      - `--refs ./brand/*.png` でbrand assetsフォルダ全体を指定
      - aspect ratio統一推奨（混在はstyle混乱の原因）

  - chunk_id: thinking-mode
    tags: [Thinking mode, reasoning, 複数画像]
    content: |
      Thinking mode（reasoning built-in）の詳細：
      概要：
      - OpenAI初の画像モデルreasoning機能
      - 生成前にlayout計画を実行
      - Web検索とself-checkが組み込み
      主な用途：
      - 複雑なlayout（複数要素の配置計画）
      - coherent複数画像生成（1 prompt → 最大8 images）
      - character/object一貫性の維持
      利用条件：
      - Plus / Pro / Business / Enterpriseプランのみ
      - Freeプランでは利用不可
      プロンプトでの指定：
      - "Use reasoning to plan the layout before generation."
      - "Coherence: maintain consistent style across all elements."
      制限：
      - subscription限定機能
      - 通常のAPI callとは別の扱い

  - chunk_id: text-rendering
    tags: [テキスト, 文字, レンダリング, 多言語]
    content: |
      テキストレンダリング能力（GPT Image 2）：
      改善点（GPT Image 1.5比）：
      - 多言語native対応（日本語 / 中国語 / 韓国語 / ヒンディー語 / ベンガル語）
      - ~99% typography accuracy（WebSearch evidence Q1: wavespeed.ai）
      - non-Latin文字をnative処理（英語変換不要）
      できること：
      - 英語テキスト：高精度で描画
      - 日本語テキスト：native対応、約99%精度
      - 密度の高いテキスト：対応
      - タイポグラフィ指定：反映可能
      注意事項：
      - 固有名詞・brand nameは生成後に再確認推奨（99%でも100%ではない）
      - 特殊文字・数式は精度低下の場合あり
      コツ：
      - 正確な文言を引用符で囲む
      - 「verbatim」（そのまま）を指定
      - フォントスタイル・配置を明示
      - 日本語フォントは指定可能

  - chunk_id: output-specifications
    tags: [出力, サイズ, 仕様, 解像度]
    content: |
      出力仕様（出典: evolink.ai/gpt-image-2、mindwiredai.com）：
      解像度オプション：
      - 1K：1024×1024（正方形）等
      - 2K：2048px範囲（APIでstable）
      - 4K：最大4096×4096（beta、production非推奨）
      サイズ制約：
      - 両辺：16pxの倍数
      - max edge：3840px
      - aspect ratio：最大3:1
      - total pixel範囲：655,360〜8,294,400
      品質設定（API）：
      - low：高速、コスト低 / 約$0.006/1024×1024
      - medium：バランス / 約$0.053/1024×1024
      - high：最高品質 / 約$0.211/1024×1024
      形式：PNG、JPEG
      Batch API：通常コストの50%削減

  - chunk_id: pricing-detail
    tags: [Pricing, コスト, token]
    content: |
      Pricingの詳細（token-based、出典: lushbinary.com/blog/chatgpt-images-2-developer-guide-gpt-image-2-api-pricing/）：
      token単価：
      - text input：$5 / M tokens
      - image input：$8 / M tokens
      - text output：$10 / M tokens
      - image output：$30 / M tokens
      Per-image概算（品質・サイズ依存）：
      - 1024×1024 low：~$0.006
      - 1024×1024 medium：~$0.053
      - 1024×1024 high：~$0.211
      - 1024×1536 low：~$0.005
      - 1024×1536 medium：~$0.041
      - 1024×1536 high：~$0.165
      Batch API：上記コストを50%削減
      重要：
      - promptトークン量 / quality / resolutionで大きく変動
      - 事前見積もりが重要
      - 1 image単純計算では不正確

  - chunk_id: quality-latency-tradeoff
    tags: [品質, 速度, トレードオフ]
    content: |
      品質と速度のトレードオフ：
      API設定：qualityパラメータ
      low：
      - 最速
      - 大量生成・プロトタイプ向き
      - ~$0.006/1024×1024
      medium：
      - バランス
      - 多くの用途に適切
      - ~$0.053/1024×1024
      high：
      - 最高品質
      - 重要なビジュアルに
      - ~$0.211/1024×1024
      選択基準：
      - 速度重視→lowから試す
      - 品質重視→high
      - 通常はmediumで十分
      Batch API活用：
      - 大量生成はBatch APIで50%削減
      - prototyping→low、finalはhigh

  - chunk_id: style-capabilities
    tags: [スタイル, 画風, 表現]
    content: |
      対応スタイル・画風：
      写実系：
      - フォトリアリスティック
      - スタジオ撮影風
      - ドキュメンタリー風
      イラスト系：
      - フラットデザイン
      - 3Dレンダリング
      - 水彩、油絵風
      図解系：
      - インフォグラフィック
      - テクニカルイラスト
      - UIモックアップ
      GPT Image 2の強み（brand consistency）：
      - 16 ref imagesでbrand assetのstyle anchorを設定
      - Thinking modeでlayout coherenceを保証
      スタイル指定のコツ：
      - 具体的な媒体を明示（photo, watercolor, 3D render）
      - カメラ用語が効く（lens, aperture, lighting）
      - brand色はHEX値で明示

  - chunk_id: camera-terminology
    tags: [カメラ, アングル, 構図]
    content: |
      効果的なカメラ・撮影用語：
      フレーミング：
      - close-up（クローズアップ）
      - wide shot（ワイドショット）
      - top-down（真上から）
      - eye-level（目線の高さ）
      アングル：
      - low-angle（ローアングル）
      - high-angle（ハイアングル）
      - Dutch angle（傾き）
      照明：
      - soft volumetric light（ソフトボリューメトリック）
      - soft diffuse light（柔らかい拡散光）
      - golden hour（ゴールデンアワー）
      - high-contrast（ハイコントラスト）
      - dramatic lighting（ドラマチック）
      レンズ：
      - 35mm lens（標準）
      - shallow depth of field（浅い被写界深度）

  - chunk_id: limitations
    tags: [制限, 苦手, 注意点]
    content: |
      GPT Image 2の制限・注意点：
      4K解像度：
      - 4K（max 4096×4096）はbeta扱い
      - production用途は2Kまでstable推奨
      Thinking mode制限：
      - Plus / Pro / Business / Enterpriseのみ
      - Freeプランでは利用不可
      多言語テキスト：
      - ~99%精度だが100%ではない
      - 固有名詞・brand nameは再確認推奨
      キャラクター一貫性：
      - 改善されたが完全ではない
      - 重要な場合は参照画像を使う
      16 ref images：
      - aspect ratio混在はstyle混乱の原因
      - 同一ratio・同一スタイルのasset推奨
      コンテンツポリシー：
      - 実在人物の生成は制限
      - 成人向けコンテンツは年齢確認必要
      - C2PAメタデータ自動付与
      物理的リアリズム：
      - 重力・支持構造が不自然な場合あり

  - chunk_id: vs-gemini
    tags: [比較, Gemini, 使い分け]
    content: |
      Gemini vs GPT Image 2：
      GPT Image 2が優位：
      - 速度（前世代比2倍高速）
      - 多言語テキスト（日本語/中国語/韓国語 native、~99%）
      - 16 reference imagesのstyle anchor
      - Thinking mode（reasoning built-in、layout計画）
      - 4K native（max 4096×4096）
      - Codex CLI $imagegen skill統合
      - 構造化プロンプトへの追従
      - 編集時の一貫性保持（CHANGE/KEEP）
      Geminiが優位：
      - 会話型の段階的改善
      - 自然言語での指示
      - Google AI Studioとの統合
      使い分け：
      - brand asset consistency / 多言語 / 4K→GPT Image 2
      - 会話・探索的→Gemini

  - chunk_id: vs-other-models
    tags: [比較, Midjourney, DALL-E]
    content: |
      他モデルとの比較：
      vs DALL-E 3：
      - DALL-E 3はretired（2026/04/21以降）
      - GPT Image 2が後継、全面的に上位互換
      - 既存DALL-E 3依存コードは移行必要
      vs GPT Image 1.5（前世代）：
      - 速度：GPT Image 2が約2倍高速
      - 多言語：GPT Image 2がnative 99%（1.5は要確認）
      - ref images：GPT Image 2が最大16枚（1.5は制限あり）
      - Thinking mode：GPT Image 2のみ
      - 4K：GPT Image 2のみ（beta）
      vs Midjourney：
      - GPT優位：テキスト描画、指示追従、Codex統合
      - MJ優位：芸術的表現、美的品質
      vs Stable Diffusion：
      - GPT優位：使いやすさ、テキスト、多言語
      - SD優位：カスタマイズ、ローカル実行
      SEO用途の結論：
      - インフォグラフィック・多言語→GPT Image 2
      - アート性重視→Midjourney
      - 会話的探索→Gemini

  - chunk_id: checklist
    tags: [チェックリスト, 確認, 完了]
    content: |
      GPT Image 2特性理解チェックリスト：
      □ DALL-E 3がretiredであることを把握したか
      □ Codex CLI $imagegen skillの使い方を理解したか
      □ 16 reference imagesのstyle anchor活用を把握したか
      □ Thinking modeの利用条件（subscription限定）を理解したか
      □ 多言語テキスト~99%精度と固有名詞再確認の重要性を把握したか
      □ 4KはbetaでAPIは2Kまでstableを理解したか
      □ token-based pricingと事前見積もりの重要性を把握したか
      □ Batch APIで50%削減できることを理解したか
      □ Geminiとの使い分けを判断できるか
      □ 16 ref imagesのaspect ratio統一推奨を把握したか
