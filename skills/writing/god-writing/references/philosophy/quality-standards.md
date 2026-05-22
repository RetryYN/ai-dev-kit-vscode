skill_id: philosophy/quality-standards
category: philosophy
type: knowledge
dependencies:
  - philosophy/principles
  - philosophy/three-nots

chunks:
  - chunk_id: summary
    content: |
      全てのライティング成果物が満たすべき品質基準。
      5階層評価（卓越/優良/合格/不足/不可）と5評価軸
      （目的達成度/読者適合度/論理構造/表現品質/信頼性）で判定。
      目標は常にLevel 4（優良）以上。

  - chunk_id: quality-levels
    tags: [品質, レベル, 階層]
    content: |
      品質5階層：
      Level 5（卓越）：読者の期待を大きく超える
      Level 4（優良）：プロとして十分な品質 ← 目標ライン
      Level 3（合格）：最低限の要件を満たす
      Level 2（不足）：修正が必要
      Level 1（不可）：再作成が必要

  - chunk_id: axis-purpose-achievement
    tags: [評価軸, 目的達成度]
    content: |
      評価軸1：目的達成度（Purpose Achievement）
      Level 5：目的を超えた価値提供、予想外の成果
      Level 4：目的を明確に達成、期待通りの成果
      Level 3：目的をほぼ達成、軽微な改善で完成
      Level 2：目的の一部のみ達成、大幅な修正必要
      Level 1：目的未達成、方向性の見直し必要
      確認項目：目的定義の明確さ、構成の整合性、段落・文の貢献度、CTAの整合

  - chunk_id: axis-reader-fit
    tags: [評価軸, 読者適合度]
    content: |
      評価軸2：読者適合度（Reader Fit）
      Level 5：読者の潜在ニーズまで満たす
      Level 4：読者のニーズを正確に満たす
      Level 3：読者のニーズをほぼ満たす
      Level 2：読者のニーズとズレがある
      Level 1：読者のニーズを無視している
      確認項目：ターゲット明確さ、知識レベル適合、関心・悩みへの回答、行動文脈適合

  - chunk_id: axis-logical-structure
    tags: [評価軸, 論理構造]
    content: |
      評価軸3：論理構造（Logical Structure）
      Level 5：論理的かつ読みやすい、流れが自然
      Level 4：論理的に整合、追跡可能
      Level 3：概ね論理的、一部に飛躍あり
      Level 2：論理の飛躍・矛盾が目立つ
      Level 1：論理構造が破綻している
      確認項目：全体構成の論理性、段落間の繋がり、主張と根拠の対応、結論の整合

  - chunk_id: axis-expression-quality
    tags: [評価軸, 表現品質]
    content: |
      評価軸4：表現品質（Expression Quality）
      Level 5：読者の心に残る、印象的な表現
      Level 4：明確で読みやすい、プロの水準
      Level 3：理解可能、基本的な品質を満たす
      Level 2：不明瞭な表現、誤字脱字あり
      Level 1：意味が通じない、重大なエラー
      確認項目：一文一義、冗長表現排除、誤字脱字、トーン一貫性、専門用語説明

  - chunk_id: axis-credibility
    tags: [評価軸, 信頼性]
    content: |
      評価軸5：信頼性（Credibility）
      Level 5：権威ある情報源、独自の知見
      Level 4：信頼できる情報源、正確な引用
      Level 3：情報の正確性は担保、出典明記
      Level 2：情報の正確性に疑問、出典不明
      Level 1：誤情報・虚偽を含む
      確認項目：事実と意見の区別、出典明記、情報鮮度、誇張・断言の回避

  - chunk_id: media-standard-seo
    tags: [媒体別基準, SEO記事]
    content: |
      SEO記事の品質基準：
      - タイトル：キーワード含有、32字以内、クリック訴求
      - 見出し：H2-H4の階層、キーワード自然配置
      - 本文：読者意図に完全回答、E-E-A-T準拠
      - 構造化：FAQ・リスト・表の適切な使用
      - 文字数：検索意図に応じた適切な長さ

  - chunk_id: media-standard-lp
    tags: [媒体別基準, LP, セールス]
    content: |
      LP/セールスページの品質基準：
      - ヘッドライン：3秒で価値が伝わる
      - ボディコピー：ベネフィット重視、証拠提示
      - CTA：明確な行動指示、視認性確保
      - 信頼要素：実績・事例・保証の提示
      - 緊急性：適切な希少性・期限の訴求

  - chunk_id: media-standard-technical
    tags: [媒体別基準, マニュアル, テクニカル]
    content: |
      マニュアル/テクニカル文書の品質基準：
      - 正確性：手順通りに実行可能
      - 網羅性：必要な情報が全て含まれる
      - 検索性：目次・索引で即座に到達可能
      - 視覚化：図・表・スクリーンショット活用
      - 更新性：版管理・更新履歴の明記

  - chunk_id: checklist-required
    tags: [チェックリスト, 必須]
    content: |
      必須チェックリスト（全て満たすこと）：
      □ 目的が明確に定義されている
      □ ターゲット読者が特定されている
      □ 3NOTへの対策がなされている
      □ 論理構造が破綻していない
      □ 誤字脱字・文法エラーがない
      □ 事実誤認・虚偽がない

  - chunk_id: checklist-recommended
    tags: [チェックリスト, 推奨]
    content: |
      推奨チェックリスト（可能な限り満たすこと）：
      □ 冒頭で価値が伝わる
      □ スキャンで内容が把握できる
      □ 具体例・データで説得力がある
      □ CTAが明確で行動しやすい
      □ 読後感が良い（満足・納得・感謝）

  - chunk_id: qa-process
    tags: [品質保証, プロセス]
    content: |
      品質保証プロセス：
      1. セルフチェック（本チェックリスト使用）
      2. 構造レビュー（目的・論理の確認）
      3. 表現レビュー（読みやすさ・正確性）
      4. 最終確認（3NOT対策・CTA）
      5. リリース
