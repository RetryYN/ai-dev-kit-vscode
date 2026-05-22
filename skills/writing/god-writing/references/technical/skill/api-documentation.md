skill_id: technical/skill/api-documentation
category: technical
type: skill
dependencies:
  - technical/knowledge/technical-writing-basics
  - technical/skill/documentation-writing

chunks:
  - chunk_id: summary
    content: |
      開発者向けAPIドキュメントの作成技法。
      エンドポイント、パラメータ、レスポンスなど
      API利用に必要な情報を整理するスキル。

  - chunk_id: api-doc-audience
    tags: [対象, 開発者, 読者]
    content: |
      APIドキュメントの読者：
      主な読者：開発者
      特徴：
      - 技術的に詳しい
      - 目的が明確（実装したい）
      - 時間がない（素早く答えを求める）
      - コピペして試したい
      求めること：
      - 正確な仕様
      - 動くコード例
      - エラーの対処法
      開発者目線で「すぐ使える」ドキュメントを。

  - chunk_id: api-doc-structure
    tags: [構成, 構造, セクション]
    content: |
      APIドキュメントの構成：
      1. 概要：APIの目的と機能
      2. 認証：APIキー、OAuth等
      3. クイックスタート：最初のリクエスト
      4. エンドポイント一覧
      5. 各エンドポイントの詳細
      6. エラーコード一覧
      7. レート制限
      8. SDK/ライブラリ
      9. 変更履歴
      探しやすい構造が重要。

  - chunk_id: endpoint-documentation
    tags: [エンドポイント, 詳細, 仕様]
    content: |
      エンドポイントの記述：
      必要な情報：
      - HTTPメソッド（GET/POST等）
      - URL/パス
      - 説明（何をするか）
      - パラメータ（必須/任意）
      - リクエスト例
      - レスポンス例
      - エラーケース
      形式例：
      「## ユーザー情報取得
      GET /api/v1/users/{id}
      指定されたIDのユーザー情報を取得します」

  - chunk_id: parameter-documentation
    tags: [パラメータ, 引数, 入力]
    content: |
      パラメータの記述：
      表形式が見やすい：
      | 名前 | 型 | 必須 | 説明 |
      |------|------|------|------|
      | id | string | Yes | ユーザーID |
      | limit | integer | No | 取得件数（デフォルト: 20）|
      記載内容：
      - パラメータ名
      - データ型
      - 必須/任意
      - 説明
      - デフォルト値
      - 制約（最大値、形式等）

  - chunk_id: code-examples
    tags: [コード例, サンプル, 実装]
    content: |
      コード例の提供：
      複数言語で：
      ```bash
      curl -X GET "https://api.example.com/users/123" \
        -H "Authorization: Bearer YOUR_API_KEY"
      ```
      ```python
      import requests
      response = requests.get(
          "https://api.example.com/users/123",
          headers={"Authorization": "Bearer YOUR_API_KEY"}
      )
      ```
      原則：
      - コピペで動く
      - 実際の値に近い例
      - エラー処理も含める

  - chunk_id: response-documentation
    tags: [レスポンス, 出力, 結果]
    content: |
      レスポンスの記述：
      成功時のレスポンス例：
      ```json
      {
        "id": "123",
        "name": "サンプル ユーザー",
        "email": "user@example.com",
        "created_at": "2024-01-15T10:30:00Z"
      }
      ```
      フィールド説明：
      | フィールド | 型 | 説明 |
      |------------|------|------|
      | id | string | ユーザーID |
      | name | string | ユーザー名 |
      HTTPステータスコードも明記。

  - chunk_id: error-documentation
    tags: [エラー, ハンドリング, コード]
    content: |
      エラードキュメント：
      エラーコード一覧：
      | コード | HTTPステータス | 説明 |
      |--------|---------------|------|
      | AUTH_001 | 401 | 認証エラー |
      | RATE_001 | 429 | レート制限超過 |
      エラーレスポンス例：
      ```json
      {
        "error": {
          "code": "AUTH_001",
          "message": "Invalid API key"
        }
      }
      ```
      対処法も記載すると親切。

  - chunk_id: interactive-docs
    tags: [インタラクティブ, 試用, Swagger]
    content: |
      インタラクティブドキュメント：
      ブラウザ上でAPIを試せる仕組み。
      ツール：
      - Swagger UI / OpenAPI
      - Postman
      - ReadMe
      メリット：
      - 読みながら試せる
      - 理解が深まる
      - 実装前の検証
      可能であれば提供を検討。

  - chunk_id: checklist
    tags: [チェックリスト, 確認]
    content: |
      APIドキュメントチェックリスト：
      □ 認証方法は明記したか
      □ クイックスタートはあるか
      □ 全エンドポイントを網羅しているか
      □ パラメータは表形式で整理したか
      □ コード例は動くか
      □ レスポンス例は実際のデータに近いか
      □ エラーコードは一覧化したか
      □ バージョン/変更履歴はあるか
