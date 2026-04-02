---
name: browser-script
description: Playwright codegenによるブラウザ操作記録からE2Eテスト雛形を自動生成し、L6統合検証の効率化を支援
metadata:
  helix_layer: L6
  triggers:
    - E2Eテスト設計(D-E2E)時
    - 統合検証(L6)時
    - ユーザーフロー検証時
  verification:
    - "生成テスト: npx playwright test 成功"
    - "主要フローの操作記録完了"
    - "テスト対象URLが allowlist に登録済み"
compatibility:
  claude: true
  codex: true
---

# 操作記録テスト化スキル（Playwright codegen）

## 適用タイミング

このスキルは以下の場合に読み込む：
- E2Eテスト設計（D-E2E）時
- 統合検証（L6）時
- ユーザーフロー検証時

---

## 1. セットアップ手順

```bash
npm init playwright@latest
npx playwright install
```

推奨ディレクトリ：

- `tests/e2e/`（仕様ベース）
- `tests/e2e/generated/`（codegen生ファイル）
- `tests/e2e/pages/`（ページオブジェクト）

---

## 2. codegen の使い方

```bash
npx playwright codegen https://example.com
```

記録時のルール：

1. 1シナリオ1目的で記録する
2. 不安定な操作（hover依存、曖昧セレクタ）を避ける
3. 記録後に `expect` を追加して検証を明示する

複数環境の切替例：

```bash
BASE_URL=https://staging.example.com npx playwright codegen "$BASE_URL"
```

---

## 3. Playwright MCP 設定（Claude Code 連携）

`mcp.json` 例：

```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {
        "PLAYWRIGHT_BASE_URL": "https://staging.example.com",
        "PLAYWRIGHT_ALLOWED_ORIGINS": "https://staging.example.com"
      }
    }
  }
}
```

運用ルール：

- allowlist 未登録URLは記録対象にしない
- 機密操作（決済、本番管理画面）は人間確認を必須にする

---

## 4. 記録からテストへの変換パターン

### 変換前（codegen 生）

- セレクタが冗長
- 待機条件が暗黙
- アサーション不足

### 変換後（推奨）

1. セレクタを `getByRole` / `getByTestId` に置換
2. 意図的な待機（`expect(...).toBeVisible()`）を追加
3. テストデータを fixture 化
4. 失敗時スクリーンショットを有効化

```typescript
test('ログイン後にダッシュボードへ遷移する', async ({ page }) => {
  const email = process.env.E2E_EMAIL ?? ''
  const password = process.env.E2E_PASSWORD ?? ''
  await page.goto('/login')
  await page.getByLabel('メールアドレス').fill(email)
  await page.getByLabel('パスワード').fill(password)
  await page.getByRole('button', { name: 'ログイン' }).click()
  await expect(page).toHaveURL(/\/dashboard/)
  await expect(page.getByRole('heading', { name: 'ダッシュボード' })).toBeVisible()
})
```

---

## 5. ページオブジェクトパターン

`tests/e2e/pages/login-page.ts` 例：

```typescript
import { expect, type Page } from '@playwright/test'

export class LoginPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/login')
  }

  async signIn(email: string, password: string) {
    await this.page.getByLabel('メールアドレス').fill(email)
    await this.page.getByLabel('パスワード').fill(password)
    await this.page.getByRole('button', { name: 'ログイン' }).click()
  }

  async expectDashboard() {
    await expect(this.page).toHaveURL(/\/dashboard/)
  }
}
```

適用基準：

- 同一画面を3回以上操作する場合に導入
- 画面責務ごとにクラスを分割

---

## 6. HELIX L6 D-E2E との統合

1. D-E2Eで主要フロー（ログイン、登録、購入など）を定義
2. codegen で雛形を生成
3. ページオブジェクト化して保守性を上げる
4. `npx playwright test` を L6 検証に組み込む
5. 失敗結果を G6 判定資料に添付する

最小実行：

```bash
npx playwright test
```

---

## 7. セキュリティ制約

必須ルール：

- 対象URLは allowlist で明示
- 認証情報は環境変数で注入し、テストコードに直書きしない
- `auth.json` / `storage-state.json` は `.gitignore` に登録
- private network（`localhost`, `10.*`, `192.168.*`）は明示許可がない限り対象外

`.gitignore` 例：

```gitignore
auth.json
storage-state.json
test-results/
playwright-report/
```

---

## 8. 完了判定

- `npx playwright test` 成功
- 主要フローの操作記録完了
- テスト対象URLの allowlist 登録済み
