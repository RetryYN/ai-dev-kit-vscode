---
name: api-contract
description: APIコントラクト定義（D-API/D-CONTRACT）とスキーマ・レスポンス・エラー整合の検証チェックリストを提供（G3 契約凍結後の整合検証に使用。設計段階は project/api を参照）
metadata:
  helix_layer: L3-L4
  triggers:
    - API契約凍結時
    - D-API/D-CONTRACT 整合検証時
    - 契約ドリフト検知時
  verification:
    - "openapi-diff 破壊的変更 0件"
    - "型生成差分 0件（openapi-typescript → 実装型）"
    - "契約テスト全通過（Consumer-Driven Contract）"
    - "エラーコード: 全エンドポイント×想定エラー 定義済み"
compatibility:
  claude: true
  codex: true
---

# APIコントラクト検証スキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- APIエンドポイント作成・修正時
- フロントエンド・バックエンド間の連携確認時
- 外部APIとの統合時
- L3検証（API整合性）実行時

---

## 1. コントラクト定義

### 必須要素

```yaml
contract:
  endpoint: "/api/v1/resource"
  method: "POST"
  request:
    headers:
      - name: "Authorization"
        required: true
        format: "Bearer {token}"
    body:
      schema: "RequestSchema"
      required_fields: [...]
  response:
    success:
      status: 201
      schema: "ResponseSchema"
    errors:
      - status: 400
        code: "VALIDATION_ERROR"
      - status: 401
        code: "UNAUTHORIZED"
      - status: 404
        code: "NOT_FOUND"
```

---

## 2. スキーマ検証

### OpenAPI/Swagger連携

```yaml
# openapi.yaml
paths:
  /api/v1/users:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
```

### 型定義の同期

```typescript
// フロントエンド型定義
interface CreateUserRequest {
  name: string;
  email: string;
}

// バックエンド型定義（Pydantic）
class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
```

### 検証ポイント

```
□ フィールド名の一致
□ 型の一致（string/str, number/int等）
□ 必須/任意の一致
□ バリデーションルールの一致
□ 列挙型の値の一致
```

---

## 3. レスポンス形式検証

### 標準レスポンス形式

```json
// 成功
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}

// エラー
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [...]
  }
}
```

### 検証チェックリスト

```
□ success フラグの有無
□ data フィールドの構造
□ meta フィールド（ページネーション等）
□ error フィールドの構造
□ タイムスタンプ形式（ISO 8601）
□ ID形式（UUID, 数値等）
```

---

## 4. エラーコード網羅

### 標準エラーコード一覧

| HTTPステータス | エラーコード | 用途 |
|---------------|-------------|------|
| 400 | INVALID_REQUEST | 不正なリクエスト形式 |
| 400 | VALIDATION_ERROR | バリデーションエラー |
| 401 | UNAUTHORIZED | 認証エラー |
| 403 | FORBIDDEN | 権限エラー |
| 404 | NOT_FOUND | リソース未存在 |
| 409 | CONFLICT | 競合（重複等） |
| 422 | UNPROCESSABLE | 処理不能 |
| 429 | RATE_LIMITED | レート制限 |
| 500 | INTERNAL_ERROR | サーバーエラー |

### 網羅性チェック

```
□ 全エンドポイントで想定エラーを定義
□ エラーコードがユニーク
□ エラーメッセージが明確
□ クライアント側でハンドリング可能
```

---

## 5. 契約テスト

### Consumer-Driven Contract

```typescript
// コンシューマ側（フロントエンド）のテスト
describe('User API Contract', () => {
  it('should accept CreateUserRequest and return UserResponse', async () => {
    const request: CreateUserRequest = {
      name: 'Test',
      email: 'test@example.com'
    };

    const response = await api.createUser(request);

    expect(response.success).toBe(true);
    expect(response.data).toMatchSchema(UserResponseSchema);
  });
});
```

### Provider側検証

```python
# プロバイダ側（バックエンド）のテスト
def test_create_user_contract():
    request = {"name": "Test", "email": "test@example.com"}
    response = client.post("/api/v1/users", json=request)

    assert response.status_code == 201
    assert response.json()["success"] == True
    validate(response.json()["data"], UserResponseSchema)
```

---

## 6. 破壊的変更の検出

### 破壊的変更の定義

```
❌ 必須フィールドの追加
❌ フィールドの削除
❌ 型の変更
❌ エンドポイントURLの変更
❌ HTTPメソッドの変更
❌ 必須ヘッダーの追加
```

### 非破壊的変更

```
✅ オプションフィールドの追加
✅ 新規エンドポイントの追加
✅ 新規エラーコードの追加
✅ レスポンスフィールドの追加（後方互換）
```

### バージョニング戦略

```
/api/v1/users  # 現行バージョン
/api/v2/users  # 破壊的変更を含む新バージョン

# 移行期間
v1: 非推奨警告 + 動作継続
v2: 新機能
```

---

## 7. 自動検証ツール

### OpenAPI Diff

```bash
# スキーマ差分の検出
npx openapi-diff old-spec.yaml new-spec.yaml

# 破壊的変更のチェック
npx @openapitools/openapi-diff-cli \
  --old old-spec.yaml \
  --new new-spec.yaml \
  --fail-on-incompatible
```

### 型生成

```bash
# OpenAPIから型生成（TypeScript）
npx openapi-typescript api-spec.yaml -o types/api.d.ts

# Zodスキーマ生成
npx openapi-zod-client api-spec.yaml -o schemas/api.ts
```

---

## チェックリスト

### API追加時

```
□ OpenAPI/Swagger仕様を更新
□ リクエスト・レスポンス型を定義
□ エラーケースを網羅
□ コントラクトテストを追加
□ クライアント型を再生成
```

### API変更時

```
□ 破壊的変更かどうか確認
□ 破壊的な場合はバージョニング
□ 移行ガイドを作成
□ 既存クライアントへの影響を評価
□ テストを更新
```

### レビュー時

```
□ スキーマの整合性
□ エラーコードの網羅性
□ 後方互換性の確認
□ ドキュメントの更新
```

## 8. 詳細設計品質チェックリスト

### API 仕様チェック
- [ ] 全エンドポイントに request/response スキーマ定義
- [ ] 全エンドポイントにエラーコード一覧
- [ ] 認証・認可の要否が明示
- [ ] ページネーション/フィルタの仕様定義
- [ ] レート制限の仕様定義
- [ ] API バージョニング戦略

### DB スキーマチェック
- [ ] 全テーブルに PK 定義
- [ ] FK 制約が適切に設定
- [ ] インデックス設計とクエリパターンの対応
- [ ] マイグレーション手順とロールバック手順
- [ ] シード/初期データの定義

### テスト設計チェック
- [ ] テストピラミッド比率（Unit ≥60%, Integration ≤30%, E2E ≤10%）
- [ ] 全機能要件にテストケースが紐付き
- [ ] エッジケース・境界値テストの設計
- [ ] パフォーマンステストの基準値定義
- [ ] テストデータ管理方針

### 工程表チェック
- [ ] 全タスクに見積工数
- [ ] 依存関係の明示
- [ ] クリティカルパスの特定
- [ ] バッファの計上（不確実性 ×1.2〜2.0）
