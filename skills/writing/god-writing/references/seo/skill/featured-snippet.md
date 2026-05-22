skill_id: seo/skill/featured-snippet
category: seo
type: skill
dependencies:
  - seo/knowledge/content-structure
  - seo/skill/heading-structure

chunks:
  - chunk_id: summary
    content: |
      強調スニペット（Featured Snippet）を獲得する技法。
      Position Zero と呼ばれる検索結果最上部の特別枠。
      定義、リスト、表、手順など形式別の最適化方法。

  - chunk_id: snippet-types
    tags: [スニペット, 種類, 形式]
    content: |
      強調スニペットの種類：
      段落型（Paragraph）：
      - 最も一般的（約50%）
      - 定義、説明、回答
      - 40〜60語程度が表示
      リスト型（List）：
      - 番号付き/番号なし
      - 手順、ランキング、項目列挙
      表型（Table）：
      - 比較データ、仕様、価格
      - 表形式で表示
      動画型（Video）：
      - YouTube動画のサムネイル＋説明

  - chunk_id: paragraph-snippet
    tags: [段落型, 定義, 回答]
    content: |
      段落型スニペットの獲得：
      対象クエリ：「〇〇とは」「〇〇 意味」「なぜ〇〇」
      構造：
      H2/H3に質問形式の見出し
      →直後に40〜60語の明確な回答
      例：
      H2「SEOとは何か？」
      本文「SEOとは、Search Engine Optimizationの略で、
      検索エンジンで上位表示されるようにWebサイトを
      最適化する施策のことです。」
      ポイント：質問に直接、簡潔に、完全に答える

  - chunk_id: list-snippet
    tags: [リスト型, 手順, 列挙]
    content: |
      リスト型スニペットの獲得：
      対象クエリ：「〇〇の方法」「〇〇の手順」「〇〇 おすすめ」
      番号付きリスト（手順）：
      H2「SEO対策の手順」
      1. キーワードを調査する
      2. コンテンツを作成する
      3. 内部リンクを設置する
      番号なしリスト（列挙）：
      - 特徴A
      - 特徴B
      - 特徴C
      ポイント：5〜8項目程度、各項目は簡潔に

  - chunk_id: table-snippet
    tags: [表型, 比較, データ]
    content: |
      表型スニペットの獲得：
      対象クエリ：「〇〇 比較」「〇〇 一覧」「〇〇 価格」
      表の構造：
      - 明確な列見出し
      - 整理されたデータ
      - HTMLのtableタグを使用
      例：
      | 項目 | プランA | プランB |
      |------|---------|---------|
      | 価格 | 1,000円 | 2,000円 |
      | 機能 | 基本 | 高機能 |
      ポイント：比較しやすい構造、データの正確性

  - chunk_id: question-targeting
    tags: [質問, ターゲット, PAA]
    content: |
      質問キーワードのターゲティング：
      スニペットを獲得しやすいクエリ：
      - 「〇〇とは」「〇〇 意味」
      - 「〇〇 方法」「〇〇 やり方」
      - 「なぜ〇〇」「〇〇 理由」
      - 「〇〇 違い」
      - 「〇〇 おすすめ」
      People Also Ask（PAA）の活用：
      - 検索結果のPAAを確認
      - それらの質問に記事内で回答
      - PAA獲得→スニペット獲得の足がかり

  - chunk_id: content-structure-for-snippet
    tags: [構造, 最適化, フォーマット]
    content: |
      スニペット向けコンテンツ構造：
      基本パターン：
      H2（質問）
      ↓
      直接回答（40〜60語）
      ↓
      詳細説明
      ポイント：
      - 質問と回答の距離を近く
      - 回答は段落の冒頭に
      - 「〇〇とは、〜です。」の形式
      - 回答の後に詳細を続ける構成

  - chunk_id: existing-snippet-analysis
    tags: [分析, 競合, 改善]
    content: |
      既存スニペットの分析：
      手順：
      1. 狙うキーワードで検索
      2. 現在のスニペット保持サイトを確認
      3. スニペット内容の構造を分析
      4. より良い回答を設計
      改善ポイント：
      - より簡潔な回答
      - より正確な情報
      - より新しいデータ
      - より適切な形式
      スニペットは上位10位以内から選ばれる。まず上位表示が前提。

  - chunk_id: schema-markup
    tags: [構造化データ, Schema, マークアップ]
    content: |
      スニペット向け構造化データ：
      FAQPage Schema：
      - 複数のQ&Aを含むページ
      - 検索結果にFAQとして表示される可能性
      HowTo Schema：
      - 手順を含むページ
      - ステップが検索結果に表示
      実装方法：JSON-LD形式でhead内に記述
      効果：スニペット獲得の確率向上

  - chunk_id: monitoring
    tags: [モニタリング, 追跡, 変動]
    content: |
      スニペット獲得のモニタリング：
      確認方法：
      - 定期的に検索して確認
      - Search Consoleの「検索での見え方」
      - ツール（Ahrefs、SEMrush）で追跡
      注意点：
      - スニペットは頻繁に変動
      - 獲得しても維持できるとは限らない
      - 競合の動向を継続監視
      継続的な最適化が必要。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      強調スニペット獲得チェックリスト：
      □ 質問形式の見出しを使っているか
      □ 見出し直後に簡潔な回答があるか
      □ 回答は40〜60語程度か
      □ 適切な形式（段落/リスト/表）を選んでいるか
      □ 構造化データは実装されているか
      □ 既存のスニペットを分析したか
      □ People Also Askをカバーしているか
      □ 上位10位以内に入っているか
