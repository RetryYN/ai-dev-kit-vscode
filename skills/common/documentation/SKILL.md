---
name: documentation
description: documentation関連タスク時に使用
metadata:
  helix_layer: L2
  triggers:
    - README作成時
    - API仕様書作成時
    - 技術文書作成時
  verification:
    - ドキュメント完成
    - レビュー完了
compatibility:
  claude: true
  codex: true
---

# ドキュメント作成スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- README作成時
- API仕様書作成時
- 技術文書作成時

---

## 1. ドキュメントの種類

| 種類 | 目的 | 対象者 |
|------|------|--------|
| README | プロジェクト概要、導入方法 | 新規参加者、利用者 |
| API仕様書 | エンドポイント詳細 | フロントエンド、外部連携 |
| 設計書 | アーキテクチャ、設計判断 | 開発者 |
| 運用手順書 | デプロイ、障害対応 | 運用担当 |
| ADR | 技術的意思決定記録 | 将来の開発者 |

---

## 2. README テンプレート

```markdown
# プロジェクト名

簡潔な説明（1-2文）

## 特徴

- 特徴1
- 特徴2
- 特徴3

## 必要条件

- Node.js 20+
- PostgreSQL 16+
- Redis 7+

## セットアップ

### 1. リポジトリクローン

```bash
git clone https://github.com/org/project.git
cd project
```

### 2. 依存関係インストール

```bash
npm install
```

### 3. 環境変数設定

```bash
cp .env.example .env
# .env を編集
```

### 4. データベース準備

```bash
npm run db:migrate
npm run db:seed
```

### 5. 起動

```bash
npm run dev
```

http://localhost:3000 でアクセス

## 開発コマンド

| コマンド | 説明 |
|---------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | ビルド |
| `npm run test` | テスト実行 |
| `npm run lint` | Lint実行 |

## ディレクトリ構成

```
src/
├── app/          # ページ
├── components/   # コンポーネント
├── lib/          # ユーティリティ
└── api/          # APIクライアント
```

## 技術スタック

- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.12
- Database: PostgreSQL 16, Prisma
- Infrastructure: Docker, AWS

## 貢献方法

1. Fork
2. ブランチ作成 (`git checkout -b feature/amazing`)
3. コミット (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Pull Request作成

## ライセンス

MIT
```

---

## 3. API仕様書

### OpenAPI (Swagger)

```yaml
openapi: 3.0.3
info:
  title: Project API
  version: 1.0.0
  description: プロジェクトのREST API

servers:
  - url: https://api.example.com/v1
    description: 本番
  - url: https://staging-api.example.com/v1
    description: ステージング

paths:
  /users:
    get:
      summary: ユーザー一覧取得
      tags: [Users]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
    
    post:
      summary: ユーザー作成
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: 作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
      required: [id, name, email, createdAt]
    
    CreateUser:
      type: object
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
      required: [name, email, password]
    
    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
      required: [code, message]

  responses:
    BadRequest:
      description: 不正なリクエスト
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

### Markdown形式

```markdown
# API仕様書

## 認証

すべてのAPIはBearer認証が必要です。

```
Authorization: Bearer <access_token>
```

## エンドポイント

### POST /api/v1/auth/login

ログイン認証

#### リクエスト

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| email | string | ✅ | メールアドレス |
| password | string | ✅ | パスワード（8文字以上） |

#### レスポンス

##### 200 OK

```json
{
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresIn": 900
}
```

##### 401 Unauthorized

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "メールアドレスまたはパスワードが正しくありません"
  }
}
```

#### エラーコード

| コード | 説明 |
|--------|------|
| INVALID_CREDENTIALS | 認証情報が不正 |
| ACCOUNT_LOCKED | アカウントがロック中 |
| RATE_LIMITED | レート制限 |
```

---


---

## テンプレート詳細

以下は references/templates.md を参照:
- ADR（Architecture Decision Record）
- 運用手順書

---

## 6. 良いドキュメントの原則

### 原則

```
1. 対象読者を明確に
   - 誰が読むのか
   - 何を知りたいのか

2. 最新を維持
   - コードと同時に更新
   - 古い情報は削除

3. 簡潔に
   - 必要な情報だけ
   - 重複を避ける

4. 具体的に
   - 例を示す
   - コードサンプル

5. 検索しやすく
   - 適切な見出し
   - 目次
```

### アンチパターン

```
❌ 避けるべきこと
- 更新されないドキュメント
- 長すぎて読まれない
- コードと乖離している
- 抽象的すぎる
- 専門用語の説明なし
```

---

## チェックリスト

### README

```
[ ] プロジェクト概要がある
[ ] セットアップ手順が完全
[ ] 動作確認までできる
[ ] コマンド一覧がある
```

### API仕様書

```
[ ] 全エンドポイントが記載
[ ] リクエスト/レスポンス例がある
[ ] エラーケースが記載
[ ] 認証方法が説明されている
```

### 運用手順書

```
[ ] 手順が順序立っている
[ ] コマンドがコピペ可能
[ ] ロールバック手順がある
[ ] 緊急連絡先がある
```
