---
name: testing
description: テスト戦略策定でユニット/統合/E2Eテストのテンプレートとカバレッジ目標の検証手順を提供
metadata:
  helix_layer: L5
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
