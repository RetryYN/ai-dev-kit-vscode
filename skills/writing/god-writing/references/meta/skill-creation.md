skill_id: meta/skill-creation
category: meta
type: skill
dependencies:
  - philosophy/principles
  - logical/knowledge/information-architecture

chunks:
  - chunk_id: summary
    content: |
      AIエージェント用スキルファイルの作成技法。
      YAML形式のチャンク構造で知識・技術を体系化し、
      再利用可能なスキルベースを構築するメタスキル。
      本God Writingシステム自体を作った手法。

  - chunk_id: skill-philosophy
    tags: [思想, 設計原則, 目的]
    content: |
      スキル設計の思想：
      目的：AIが「呼び出せる」形で知識を格納
      原則：
      - チャンク単位で独立性を持たせる
      - 依存関係を明示して階層構造を作る
      - 検索・参照しやすいタグ付け
      - 人間が読んでも理解できる形式
      スキル＝「AIの長期記憶」として機能させる。

  - chunk_id: yaml-structure
    tags: [YAML, 構造, フォーマット]
    content: |
      YAMLファイルの基本構造：
      ```yaml
      skill_id: カテゴリ/サブカテゴリ/スキル名
      category: カテゴリ名
      type: knowledge または skill
      dependencies:
        - 依存スキル1
        - 依存スキル2

      chunks:
        - chunk_id: チャンクID
          tags: [タグ1, タグ2, タグ3]
          content: |
            チャンク内容をここに記述
      ```
      拡張子は.mdでMarkdownとしても読める。

  - chunk_id: skill-id-design
    tags: [ID, 命名, パス]
    content: |
      skill_idの設計：
      形式：カテゴリ/サブカテゴリ/スキル名
      例：
      - japanese/basic/knowledge/grammar-structure
      - seo/skill/keyword-research
      - psychology/knowledge/cognitive-bias
      命名規則：
      - 小文字英数字とハイフン
      - 階層は/で区切る
      - 具体的で検索しやすい名前
      ディレクトリ構造と一致させる。

  - chunk_id: chunk-design
    tags: [チャンク, 設計, 粒度]
    content: |
      チャンク設計の原則：
      粒度：1チャンク＝1概念・1トピック
      理想的なチャンク数：9〜13個/ファイル
      必須チャンク：
      - summary：スキル全体の要約（最初に配置）
      - checklist：実践時の確認項目（最後に配置）
      チャンク内容：
      - 箇条書きと短文の組み合わせ
      - 具体例を含める
      - 40〜150字程度を目安
      独立して参照されても意味が通じること。

  - chunk_id: tag-strategy
    tags: [タグ, 検索, メタデータ]
    content: |
      タグ付け戦略：
      目的：チャンク単位での検索・参照を可能に
      タグ数：3〜5個/チャンク
      タグの種類：
      - 概念タグ：そのチャンクの主題
      - 関連タグ：関連する概念
      - 用途タグ：いつ使うか
      例：
      tags: [見出し, SEO, クリック率]
      tags: [エラーメッセージ, UX, 解決策]
      日本語タグ推奨（検索精度向上）。

  - chunk_id: dependency-design
    tags: [依存関係, 階層, 参照]
    content: |
      依存関係の設計：
      目的：スキル間の関係を明示
      記述方法：
      dependencies:
        - philosophy/principles（基礎原則）
        - japanese/basic/sentence-construction（前提スキル）
      設計原則：
      - 循環参照を避ける
      - 上位→下位の階層構造
      - 基礎スキルは広く参照される
      依存関係でスキルツリーが形成される。

  - chunk_id: category-organization
    tags: [カテゴリ, 分類, 構造]
    content: |
      カテゴリ構成の例（God Writing）：
      philosophy（3）：原則、3NOT、品質基準
      japanese（18）：basic/advanced/rhetoric
      seo（12）：アルゴリズム、最適化、LLMO
      sales（10）：価値提案、LP、クロージング
      copywriting（10）：公式、見出し、ストーリー
      logical（11）：論理、証拠、提案書
      psychology（12）：バイアス、説得、信頼
      ux（7）：UXライティング、マイクロコピー
      technical（6）：ドキュメント、API、仕様書
      interview（7）：取材、質問、事例作成
      knowledge/skill の2層構造を各カテゴリに。

  - chunk_id: content-writing
    tags: [内容, 書き方, スタイル]
    content: |
      チャンク内容の書き方：
      スタイル：
      - 体言止め・箇条書き中心
      - 冗長な説明を避ける
      - 例を必ず含める
      - 「〜である」より「〜だ」「〜する」
      構成パターン：
      1. 定義・概念説明
      2. 具体例・パターン
      3. 注意点・例外
      4. 実践のコツ
      AIが処理しやすい簡潔な形式で。

  - chunk_id: batch-creation
    tags: [一括作成, 効率, プロセス]
    content: |
      大量スキル作成のプロセス：
      1. 全体設計：カテゴリ・スキル一覧を作成
      2. 依存関係マップ：どれが基礎か整理
      3. 基礎から作成：philosophyなど上位から
      4. カテゴリ単位で進行：集中して品質統一
      5. 都度確認：文字化け・構造チェック
      6. ZIP化：完成後にまとめて納品
      God Writing 96スキルは約3時間で作成。

  - chunk_id: quality-check
    tags: [品質, チェック, 検証]
    content: |
      品質チェック項目：
      構造チェック：
      □ YAMLヘッダーが正しいか
      □ チャンク数は適切か（9〜13）
      □ tagsは各チャンクにあるか
      内容チェック：
      □ 日本語が十分含まれているか
      □ 文字化けがないか
      □ 具体例が含まれているか
      □ checklistチャンクがあるか
      一括検証スクリプトで効率化。

  - chunk_id: skill-md-example
    tags: [SKILL.md, 説明書, 使い方]
    content: |
      SKILL.md（説明書）の作成：
      スキルフォルダのルートに配置。
      内容：
      - システム概要
      - 使い方（呼び出し方）
      - カテゴリ一覧
      - 依存関係の説明
      - 活用例
      AIがスキルを使う際の「取扱説明書」。
      最初に読み込ませることで全体を把握。

  - chunk_id: checklist
    tags: [チェックリスト, 確認, 完了]
    content: |
      スキル作成チェックリスト：
      □ skill_idは一意で階層的か
      □ type（knowledge/skill）は適切か
      □ dependenciesは正しく設定したか
      □ summaryチャンクは最初にあるか
      □ checklistチャンクは最後にあるか
      □ 各チャンクにtagsがあるか
      □ 内容は簡潔で例を含むか
      □ 文字化け・構造エラーはないか
      □ SKILL.md説明書を作成したか
