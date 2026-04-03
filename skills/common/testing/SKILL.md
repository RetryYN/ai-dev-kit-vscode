---
name: testing
description: テスト戦略策定でユニット/統合/E2Eテストのテンプレートとカバレッジ目標の検証手順を提供
metadata:
  helix_layer: L4
  triggers:
    - テスト作成時
    - 機能実装完了時
    - バグ修正時
  verification:
    - "npm run test 0 errors"
    - "Unit カバレッジ ≥80%"
    - "Integration: 主要フロー網羅"
    - "E2E: クリティカルパス網羅"
compatibility:
  claude: true
  codex: true
---

# テストスキル

## 適用タイミング

このスキルは以下の場合に読み込む：
- テスト作成時
- 機能実装完了時
- バグ修正時

---

## テストピラミッド

```
        /\
       /  \      E2E (少)
      /----\     - ユーザーフロー全体
     /      \    
    /--------\   Integration (中)
   /          \  - API、DB連携
  /------------\ Unit (多)
 /              \ - 関数、クラス単体
```

---

## テスト種別

### Unit Test

**対象**: 関数、クラス、ユーティリティ

```typescript
// 例: バリデーション関数
describe('validateEmail', () => {
  it('should return true for valid email', () => {
    expect(validateEmail('test@example.com')).toBe(true)
  })

  it('should return false for invalid email', () => {
    expect(validateEmail('invalid')).toBe(false)
  })
})
```

### Integration Test

**対象**: API、DB、外部サービス連携

```typescript
// 例: APIエンドポイント
describe('POST /api/users', () => {
  it('should create user and return 201', async () => {
    const res = await request(app)
      .post('/api/users')
      .send({ name: 'Test', email: 'test@example.com' })
    
    expect(res.status).toBe(201)
    expect(res.body.id).toBeDefined()
  })
})
```

### E2E Test

**対象**: ユーザーフロー全体

```typescript
// 例: ログインフロー
test('user can login', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[name="email"]', 'test@example.com')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')
  
  await expect(page).toHaveURL('/dashboard')
})
```

---

## テスト作成ルール

### 必須ケース

```
✅ 正常系（happy path）
✅ 異常系（エラーケース）
✅ 境界値（0, 1, max, max+1）
✅ null/undefined
```

### 命名規則

```typescript
// should [期待動作] when [条件]
it('should return error when email is invalid', () => {})
it('should create user when all fields are valid', () => {})
```

### AAA パターン

```typescript
it('should calculate total', () => {
  // Arrange（準備）
  const cart = new Cart()
  cart.add({ price: 100, quantity: 2 })

  // Act（実行）
  const total = cart.getTotal()

  // Assert（検証）
  expect(total).toBe(200)
})
```

---

## モック戦略

### モックするもの

```
✅ 外部API
✅ DB（Unitテスト時）
✅ 時間（Date.now）
✅ ランダム値
```

### モックしないもの

```
❌ テスト対象自体
❌ 単純なユーティリティ
❌ Integrationテストでの内部実装
```

### 例

```typescript
// 外部APIモック
jest.mock('@/services/external-api', () => ({
  fetchData: jest.fn().mockResolvedValue({ data: 'mocked' })
}))

// 時間モック
jest.useFakeTimers()
jest.setSystemTime(new Date('2025-01-01'))
```

---

## カバレッジ目標

| 種別 | 目標 | 優先度 |
|------|------|--------|
| Unit | 80%+ | 高 |
| Integration | 主要フロー | 中 |
| E2E | クリティカルパス | 低 |

```
⚠️ カバレッジ100%は目標にしない
⚠️ 重要なロジックを優先的にカバー
```

---

## 実行コマンド

```bash
# Unit + Integration
npm run test

# カバレッジ付き
npm run test:coverage

# E2E
npm run test:e2e

# 特定ファイル
npm run test -- path/to/file.test.ts

# ウォッチモード
npm run test:watch
```

---

## CI/CD連携

```yaml
# GitHub Actions例
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: npm ci
    - run: npm run lint
    - run: npm run test:coverage
    - run: npm run build
```

### マージ条件

```
[ ] lint通過
[ ] テスト全通過
[ ] カバレッジ低下なし
```

---

## テスト自動生成

関数シグネチャから、正常系・異常系・境界値を含むユニットテストを自動生成する。

### 入力フォーマット

```yaml
function_name: create_user
parameters:
  - name: email
    type: string
  - name: age
    type: int
return_type: User
dependencies:
  - user_repository.save
  - email_validator.validate
```

### 生成プロンプトテンプレート

```markdown
あなたはテスト設計者です。以下の関数仕様からユニットテストを生成してください。

## 入力
- 関数名: {{function_name}}
- パラメータ: {{parameters}}
- 戻り値型: {{return_type}}
- 依存関係: {{dependencies}}

## 要件
1. 正常系テストを最低1件
2. 異常系テストを最低2件（バリデーション失敗、依存関係エラー等）
3. 境界値テストを最低2件（min/max, 空文字, null相当）
4. AAA パターンで記述
5. モックは依存関係のみに限定

## 出力形式
- 実行可能なテストコード
- テストケース一覧（意図を1行ずつ）
```

### フレームワーク別テンプレート

#### `pytest`

```python
def test_create_user_success(mocker):
    # Arrange
    repo = mocker.Mock()
    validator = mocker.Mock(return_value=True)

    # Act
    result = create_user("user@example.com", 20, repo, validator)

    # Assert
    assert result.email == "user@example.com"
    repo.save.assert_called_once()
```

#### `Jest`

```typescript
describe('createUser', () => {
  it('should return user when input is valid', async () => {
    // Arrange
    const repo = { save: jest.fn().mockResolvedValue(true) }

    // Act
    const result = await createUser('user@example.com', 20, repo)

    // Assert
    expect(result.email).toBe('user@example.com')
    expect(repo.save).toHaveBeenCalledTimes(1)
  })
})
```

#### `Go testing`

```go
func TestCreateUser_Success(t *testing.T) {
    repo := &MockRepo{}

    got, err := CreateUser("user@example.com", 20, repo)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if got.Email != "user@example.com" {
        t.Fatalf("email mismatch: %s", got.Email)
    }
}
```

### HELIX Builder 連携

```
- Verify Script Builder で関数シグネチャを入力し、初期テストを生成
- 生成後に testing スキルの必須ケース（正常系/異常系/境界値）で不足分を追記
- G4 前に自動生成テストを手動レビューし、偽陽性・過剰モックを除去
```
