skill_id: seo/knowledge/search-algorithm
category: seo
type: knowledge
dependencies:
  - philosophy/principles

chunks:
  - chunk_id: summary
    content: |
      検索エンジンのアルゴリズムと評価基準を理解する。
      Google検索の仕組み、ランキング要因、
      主要なアルゴリズムアップデートの影響など、
      SEOライティングの基盤となる知識。

  - chunk_id: how-search-works
    tags: [検索エンジン, 仕組み, 基本]
    content: |
      検索エンジンの基本動作：
      1. クロール：Googlebotがウェブページを巡回・発見
      2. インデックス：ページ内容を解析・データベース化
      3. ランキング：検索クエリに対して最適な順序で表示
      4. 表示：検索結果ページ（SERP）にタイトル・説明を表示
      各段階で最適化が必要。発見されなければ存在しないのと同じ。

  - chunk_id: ranking-factors
    tags: [ランキング要因, 順位, 評価]
    content: |
      主要なランキング要因（200以上と言われる）：
      コンテンツ関連：
      - 検索意図との一致度
      - コンテンツの質・深さ・独自性
      - E-E-A-T（経験・専門性・権威性・信頼性）
      技術関連：
      - ページ速度・Core Web Vitals
      - モバイルフレンドリー
      - HTTPS対応
      外部要因：
      - 被リンクの質と量
      - ブランド認知度

  - chunk_id: search-intent
    tags: [検索意図, インテント, 分類]
    content: |
      検索意図（Search Intent）の4分類：
      Informational（情報型）：「〇〇とは」「〇〇 方法」
      →情報を知りたい。記事・解説コンテンツ向け。
      Navigational（案内型）：「Amazon ログイン」「YouTube」
      →特定サイトに行きたい。ブランドSEO向け。
      Commercial（商業型）：「〇〇 おすすめ」「〇〇 比較」
      →購入検討中。比較・レビュー記事向け。
      Transactional（取引型）：「〇〇 購入」「〇〇 申し込み」
      →今すぐ行動したい。LP・商品ページ向け。

  - chunk_id: algorithm-updates
    tags: [アップデート, Panda, Penguin, BERT]
    content: |
      主要なアルゴリズムアップデート：
      Panda（2011）：低品質コンテンツのペナルティ
      Penguin（2012）：不自然なリンクのペナルティ
      Hummingbird（2013）：意味理解の向上
      RankBrain（2015）：機械学習の導入
      BERT（2019）：自然言語理解の大幅向上
      Helpful Content（2022）：人のためのコンテンツ評価
      Core Updates（随時）：全体的な品質評価の更新
      傾向：コンテンツ品質と検索意図の一致がより重視。

  - chunk_id: helpful-content
    tags: [Helpful Content, 有用性, 人のため]
    content: |
      Helpful Content Update（2022〜）：
      「人のために書かれたコンテンツ」を評価。
      評価されるコンテンツ：
      - 読者に実際の価値を提供
      - 一次情報・独自の知見を含む
      - 読者の疑問を完全に解決
      評価されないコンテンツ：
      - 検索エンジン向けに書かれた
      - 他サイトのまとめ・寄せ集め
      - AIで大量生産された低品質コンテンツ
      サイト全体が評価対象（低品質が多いとサイト全体に影響）

  - chunk_id: core-web-vitals
    tags: [Core Web Vitals, 速度, UX]
    content: |
      Core Web Vitals（2021〜ランキング要因）：
      LCP（Largest Contentful Paint）：最大コンテンツの表示速度
      →2.5秒以内が良好
      FID（First Input Delay）：初回入力遅延
      →100ミリ秒以内が良好（INPに移行中）
      CLS（Cumulative Layout Shift）：レイアウトのずれ
      →0.1以下が良好
      ライティングとの関係：画像最適化、構造化、読み込み順序

  - chunk_id: mobile-first
    tags: [モバイルファースト, スマホ, 対応]
    content: |
      モバイルファーストインデックス：
      Googleはモバイル版ページを基準に評価。
      ライティングへの影響：
      - 短いパラグラフ（スマホ画面に収まる）
      - スキャンしやすい構造
      - タップしやすいCTA
      - 画像の最適化
      日本のモバイル検索比率は70%以上。
      スマホで読みやすいことが必須。

  - chunk_id: semantic-search
    tags: [セマンティック検索, 意味理解, 関連語]
    content: |
      セマンティック検索（意味理解）：
      キーワードの文字列一致ではなく、意味を理解。
      共起語・関連語を含むコンテンツが評価される。
      例：「ダイエット」の記事には「カロリー」「運動」「食事」が自然に含まれる
      対策：
      - 単一キーワードの詰め込みは逆効果
      - トピックを網羅的に解説
      - 自然な文脈で関連語を使用
      キーワード密度より「意味の網羅度」が重要。

  - chunk_id: serp-features
    tags: [SERP, 検索結果, 強調スニペット]
    content: |
      SERP機能（検索結果の特殊表示）：
      強調スニペット（Position Zero）：質問への直接回答
      ナレッジパネル：右側の情報ボックス
      People Also Ask：関連質問
      画像パック：画像検索結果
      動画カルーセル：動画検索結果
      ローカルパック：地図と店舗情報
      対策：構造化データ、FAQ形式、適切なマークアップ
      1位より上の「0位」を狙える。

  - chunk_id: ai-search-impact
    tags: [AI検索, SGE, 生成AI]
    content: |
      AI検索・SGE（Search Generative Experience）：
      GoogleがAI生成の回答を検索結果上部に表示。
      影響：
      - 従来の「10本の青いリンク」から変化
      - クリック率の変動
      - より詳細・独自のコンテンツが重要に
      対策：
      - AIが引用したくなる権威あるコンテンツ
      - 一次情報・独自データの提供
      - E-E-A-Tの強化
      「AIに参照される」コンテンツを目指す。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      検索アルゴリズム対応チェックリスト：
      □ 検索意図を正しく把握しているか
      □ 人のために書かれたコンテンツか
      □ E-E-A-Tは満たしているか
      □ モバイルで読みやすいか
      □ トピックを網羅的にカバーしているか
      □ 一次情報・独自の価値があるか
      □ 構造化データは適切か
