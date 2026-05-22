skill_id: seo/knowledge/llmo
category: seo
type: knowledge
dependencies:
  - seo/knowledge/search-algorithm
  - seo/knowledge/eeat

chunks:
  - chunk_id: summary
    content: |
      LLMO（Large Language Model Optimization）の概念と実践。
      ChatGPT、Claude、Perplexity等のAIに
      参照・引用されるためのコンテンツ最適化。
      従来SEOの発展形として理解する。

  - chunk_id: llmo-definition
    tags: [LLMO, 定義, AI最適化]
    content: |
      LLMOとは：
      Large Language Model Optimization
      大規模言語モデル（LLM）に最適化すること。
      別名：AIO（AI Optimization）、GEO（Generative Engine Optimization）
      目的：
      - AIアシスタントに情報源として参照される
      - AI検索（Perplexity等）で引用される
      - SGE（Google AI検索）で表示される
      従来SEO＋AIへの最適化が今後の標準。

  - chunk_id: ai-search-landscape
    tags: [AI検索, Perplexity, SGE]
    content: |
      AI検索の現状：
      Perplexity AI：AI検索エンジン、出典を明示
      Google SGE：検索結果上部にAI生成回答
      Bing Chat：Microsoft検索＋ChatGPT
      ChatGPT with Browse：リアルタイム検索機能
      Claude：限定的なWeb検索機能
      共通点：
      - 複数ソースを参照して回答を生成
      - 引用元としてサイトを表示
      - 従来の「リンククリック」から「情報抽出」へ

  - chunk_id: llm-content-preference
    tags: [LLM, 好み, コンテンツ特性]
    content: |
      LLMが好むコンテンツの特徴：
      明確な構造：見出し階層、論理的な流れ
      直接的な回答：質問に対する明確な答え
      事実ベース：数値、日付、具体的な情報
      一次情報：独自データ、調査結果
      権威性：専門家の見解、公式情報
      網羅性：トピックの包括的カバー
      更新性：最新情報、更新日の明記
      引用しやすい形式：定義、箇条書き、表

  - chunk_id: citation-worthy-content
    tags: [引用, 参照価値, コンテンツ]
    content: |
      引用されやすいコンテンツ：
      定義・概念説明：「〇〇とは」の明確な回答
      統計データ：数字、調査結果、比較データ
      手順・ステップ：番号付きの明確な手順
      リスト：「〇〇の種類」「〇〇選」
      比較表：製品・サービスの比較
      専門家の見解：権威ある発言・コメント
      ケーススタディ：具体的な事例・結果
      AIが「このサイトから引用したい」と思う情報を提供。

  - chunk_id: structured-answers
    tags: [構造化, 回答, フォーマット]
    content: |
      構造化された回答の提供：
      質問→回答形式：FAQ、Q&Aを明示
      定義形式：「〇〇とは、〜である。」
      箇条書き：「3つのポイント」「5つの方法」
      表形式：比較情報、仕様情報
      手順形式：「ステップ1:」「ステップ2:」
      サマリー形式：冒頭に要約を配置
      AIが抽出しやすい形式で情報を整理。

  - chunk_id: entity-optimization
    tags: [エンティティ, 固有表現, 認識]
    content: |
      エンティティ最適化：
      エンティティ：人名、組織名、場所、概念などの固有の存在
      LLMはエンティティを認識し、知識グラフと照合。
      最適化方法：
      - 正式名称を使用（略称だけでなく）
      - 関連エンティティとの関係を明示
      - 構造化データでエンティティを明示
      - Wikipediaに載るレベルの認知度を目指す
      ブランド・著者名のエンティティ確立が長期的に重要。

  - chunk_id: freshness-signals
    tags: [鮮度, 更新, 最新情報]
    content: |
      情報鮮度のシグナル：
      LLMは最新情報を優先する傾向。
      鮮度シグナル：
      - 公開日・更新日の明記
      - 「2024年最新」等の時間参照
      - 最新データ・統計の引用
      - 時事トピックへの言及
      更新戦略：
      - 定期的な記事更新
      - 古い情報の削除・修正
      - 年号入りタイトルは毎年更新
      古い情報は引用されにくい。

  - chunk_id: llmo-vs-seo
    tags: [LLMO, SEO, 違い, 共通点]
    content: |
      LLMOとSEOの関係：
      共通点：
      - 高品質コンテンツが基本
      - E-E-A-Tの重要性
      - 構造化・明確化
      - ユーザー意図への回答
      LLMO特有：
      - 引用されやすい形式の重視
      - エンティティ認識の最適化
      - 複数ソース間での優位性
      - AIの文脈理解に合わせた記述
      従来SEOができていればLLMOの70%は対応済み。

  - chunk_id: measurement
    tags: [測定, 効果検証, KPI]
    content: |
      LLMO効果の測定：
      現状、測定は困難だが以下を参考に：
      - Perplexityで検索して引用されるか確認
      - SGEプレビューでの表示確認
      - ブランド名+AIでの検索結果
      - 直接トラフィックの変化
      間接指標：
      - 従来SEO順位（相関あり）
      - E-E-A-Tスコア（ツールで推定）
      - 被リンク・言及数
      今後ツールが発展する見込み。

  - chunk_id: future-outlook
    tags: [将来, 展望, トレンド]
    content: |
      AI検索の将来展望：
      予測されるトレンド：
      - AI回答がデフォルトに（クリック減少）
      - ブランド認知の重要性増大
      - 一次情報・独自性の価値向上
      - 動画・音声コンテンツのAI参照
      - AIエージェントによる自動購買
      対策：
      - 「AIに引用される情報源」を目指す
      - ブランドエンティティの確立
      - 独自データ・研究への投資
      SEO→LLMO→AGO（AIエージェント最適化）へ進化。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      LLMOチェックリスト：
      □ 質問に対する明確な回答があるか
      □ 引用しやすい形式（定義、リスト、表）か
      □ 一次情報・独自データがあるか
      □ 更新日は明記されているか
      □ 情報は最新か
      □ エンティティは正式名称で記載されているか
      □ 構造化データは実装されているか
      □ E-E-A-Tは十分か
