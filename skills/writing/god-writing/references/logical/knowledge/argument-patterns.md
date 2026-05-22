skill_id: logical/knowledge/argument-patterns
category: logical
type: knowledge
dependencies:
  - logical/knowledge/logic-basics

chunks:
  - chunk_id: summary
    content: |
      説得力ある議論の構成パターンを理解する。
      PREP、SDS、ピラミッド構造など、
      ビジネス・アカデミックで使われる
      論理的な文章構成の型。

  - chunk_id: prep
    tags: [PREP, 結論先行, 基本]
    content: |
      PREP法：
      最も基本的なビジネス文書の構成。
      P - Point（結論）：言いたいことを最初に
      R - Reason（理由）：なぜそう言えるか
      E - Example（例）：具体的な事例
      P - Point（結論）：再度結論を強調
      例：
      P：この提案を採用すべきです
      R：コストが30%削減できるからです
      E：A社では実際に年間500万円削減しました
      P：よって、この提案を採用すべきです

  - chunk_id: sds
    tags: [SDS, 要約, 詳細]
    content: |
      SDS法：
      全体像→詳細→まとめの構成。
      S - Summary（要約）：概要を先に示す
      D - Details（詳細）：詳しく説明
      S - Summary（要約）：まとめ・結論
      例：
      S：本報告では3つの施策を提案します
      D：施策1は〇〇、施策2は△△、施策3は□□…
      S：以上3施策で売上20%向上を見込みます
      プレゼン、報告書に適する。

  - chunk_id: desc
    tags: [DESC, 問題解決, 提案]
    content: |
      DESC法：
      問題→解決の提案構成。
      D - Describe（描写）：状況・事実を描写
      E - Express（表現）：問題点・感想を述べる
      S - Suggest（提案）：解決策を提案
      C - Consequence（結果）：実行した場合の結果
      主にコンフリクト解決、フィードバックに使用。
      相手を責めずに問題提起できる。

  - chunk_id: pyramid-principle
    tags: [ピラミッド, マッキンゼー, 構造]
    content: |
      ピラミッド原則（Pyramid Principle）：
      マッキンゼー発、論理的構成の基本。
      構造：
      頂点：メインメッセージ（結論）
      第2層：支持する主要論点（3〜5個）
      第3層：各論点を支える根拠・データ
      原則：
      - 結論を先に
      - グループ化・要約
      - 論理的順序（時系列、構造、重要度）
      複雑な内容を整理して伝える。

  - chunk_id: mece
    tags: [MECE, 網羅, 重複なし]
    content: |
      MECE（ミーシー）：
      Mutually Exclusive, Collectively Exhaustive
      相互排他的かつ全体網羅的。
      原則：
      - 重複なく（Mutually Exclusive）
      - 漏れなく（Collectively Exhaustive）
      例（良い分類）：
      性別：男性 / 女性 / その他
      例（悪い分類）：
      顧客：新規 / リピーター / 大口（重複あり）
      論点の整理、フレームワーク作成に必須。

  - chunk_id: so-what-why-so
    tags: [So What, Why So, 深掘り]
    content: |
      So What? / Why So?：
      論理の飛躍を防ぐ思考法。
      So What?（だから何？）：
      事実・データから「だから何が言えるか」を導く
      上向きの思考（帰納）
      Why So?（なぜそう言える？）：
      主張に対して「なぜそう言えるか」を確認
      下向きの思考（演繹）
      両方を繰り返して論理をチェック。

  - chunk_id: thesis-antithesis-synthesis
    tags: [弁証法, テーゼ, 止揚]
    content: |
      弁証法的構成：
      対立する意見を統合する構成。
      Thesis（テーゼ）：ある主張
      Antithesis（アンチテーゼ）：反対の主張
      Synthesis（ジンテーゼ）：両者を統合した新しい主張
      例：
      テーゼ：AIは仕事を奪う
      アンチテーゼ：AIは新しい仕事を生む
      ジンテーゼ：AIは仕事の性質を変える
      複雑なテーマの議論に適する。

  - chunk_id: problem-solution
    tags: [問題解決, 構成, パターン]
    content: |
      問題解決型構成：
      1. 問題の特定：何が問題か
      2. 原因分析：なぜその問題が起きるか
      3. 解決策の提示：どうすれば解決するか
      4. 実行計画：具体的にどう進めるか
      5. 期待効果：解決するとどうなるか
      ビジネス提案、企画書の基本構成。
      問題の深刻さを示してから解決策を提示。

  - chunk_id: comparison-structure
    tags: [比較, 対比, 構成]
    content: |
      比較・対比型構成：
      ブロック型：
      A案の説明（すべて）→B案の説明（すべて）→比較
      ポイント型：
      観点1でA案とB案を比較→観点2で比較→…
      比較の観点例：
      - コスト
      - 効果
      - 実現可能性
      - リスク
      - 時間
      複数案の検討、意思決定に適する。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      論理構成チェックリスト：
      □ 結論は最初に明示されているか
      □ 根拠は結論を支えているか
      □ 論点はMECEか
      □ So What? / Why So? で飛躍はないか
      □ 目的に合った構成パターンを選んでいるか
      □ 読者が理解しやすい順序か
      □ 各要素の関係は明確か
