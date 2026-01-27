---
name: coding
description: コード品質改善、命名規則確認、リファクタリング時に使用。単純な実装時は不要。
---

# コーディング規約

## 型安全

```typescript
// ❌ any禁止
const data: any = fetch()

// ❌ 暗黙的any禁止
function process(data) { }

// ✅ 明示的な型定義
interface User {
  id: string
  name: string
}

// ✅ unknown + 型ガード
function process(data: unknown): User {
  if (isUser(data)) return data
  throw new Error('Invalid data')
}
```

## 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| 変数・関数 | camelCase | `getUserById` |
| クラス・型 | PascalCase | `UserService` |
| 定数 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| ファイル | kebab-case | `user-service.ts` |
| DB | snake_case | `user_profiles` |

## 関数設計

1. **単一責任**: 1関数1責務
2. **引数3つまで**: 超える場合はオブジェクト化
3. **早期リターン**: ネスト深くしない

```typescript
// ❌ NG
function process(a, b, c, d, e) {
  if (condition) {
    if (another) {
      // deep nest
    }
  }
}

// ✅ OK
interface ProcessInput { a: string; b: number }

function process(input: ProcessInput): Result {
  if (!condition) return earlyResult
  if (!another) return earlyResult
  return mainProcess(input)
}
```

## エラーハンドリング

```typescript
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E }

async function fetchUser(id: string): Promise<Result<User>> {
  try {
    const user = await db.users.findById(id)
    if (!user) return { success: false, error: new Error('Not found') }
    return { success: true, data: user }
  } catch (e) {
    return { success: false, error: e as Error }
  }
}
```

## インポート順序

```typescript
// 1. 外部ライブラリ
import { useState } from 'react'

// 2. 内部モジュール（絶対パス）
import { UserService } from '@/services/user'

// 3. 相対パス
import { helper } from './helper'
```

## コメント

**書くべき**: WHY、複雑なビジネスロジック、ワークアラウンド
**書かない**: WHAT（コードが説明している）、自明な処理
