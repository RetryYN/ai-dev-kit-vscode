---
name: frontend-test-e2e
description: >-
  クリティカルな操作フロー(ログイン〜決済、登録ウィザード等)を実ユーザー環境で検証する E2E を
  Playwright で実装するスキル。ロケータ戦略(getByRole 等)、web-first assertions による自動待機、
  Page Object Model、最小限に絞る判断、クロスブラウザ実行を扱う。次の場面で起動:「重要フローを
  通しでテストしたい」「ログインから決済までを自動化したい」。E2E は壊れやすく高コストのため
  対象を絞る判断(`02`/`03`)を必ず先に行う。
keywords:
  - E2Eテスト
  - Playwright
  - getByRole
  - web-first assertion
  - Page Object Model
  - クリティカルフロー
  - e2e test
version: 1.0.0
---

# E2E(エンドツーエンド)の実装

実ユーザーと同等の環境で操作フローを検証する。**最も本物に近いが、壊れやすく遅く高コスト**。
したがって対象は **クリティカルフローに限定**する(`02-strategy-selection` / `03-test-design`)。
それ以外は統合粒度(MSW でバックエンドをモック)で代替できないか先に検討する。

## 原則

- **ロケータはロール/ラベル優先**: `getByRole` / `getByLabel` / `getByText`。CSS セレクタや
  `data-testid` への依存を減らし、壊れにくくする。
- **web-first assertions で自動待機**: `await expect(locator).toBeVisible()` は要素が条件を
  満たすまで自動でリトライする。手動 `sleep` を入れない(flaky の元)。
- **対象を絞る**: 1つの「成功する代表フロー」+ 重要な失敗系のみ。網羅は下位粒度に任せる。
- **Page Object Model(POM)** で画面操作を再利用可能にする。

## 例: ログイン〜ダッシュボード表示(完全なコード)

```ts
// e2e/pages/LoginPage.ts
import { type Page, type Locator } from "@playwright/test";

export class LoginPage {
  readonly page: Page;
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;

  constructor(page: Page) {
    this.page = page;
    this.email = page.getByLabel("メールアドレス");
    this.password = page.getByLabel("パスワード");
    this.submit = page.getByRole("button", { name: "ログイン" });
  }

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
  }
}
```

```ts
// e2e/login.spec.ts
import { test, expect } from "@playwright/test";
import { LoginPage } from "./pages/LoginPage";

test.describe("ログインフロー(クリティカル)", () => {
  test("正しい認証情報でダッシュボードに遷移する", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.login("user[at]example.com", "correct-password");

    // web-first assertion: 遷移と表示を自動待機で検証
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(
      page.getByRole("heading", { name: "ダッシュボード" })
    ).toBeVisible();
  });

  test("誤ったパスワードでエラーを表示し遷移しない", async ({ page }) => {
    const login = new LoginPage(page);
    await login.goto();
    await login.login("user[at]example.com", "wrong-password");

    await expect(page.getByRole("alert")).toContainText("認証に失敗しました");
    await expect(page).toHaveURL(/\/login/);
  });
});
```

`playwright.config.ts`(E2E 用の完全な例):

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  // CI では失敗時に1回だけ再試行(flaky の影響を緩和、根本対処は別途)
  retries: process.env.CI ? 1 : 0,
  // 並列実行
  workers: process.env.CI ? 2 : undefined,
  reporter: [["html"], ["list"]],
  use: {
    baseURL: "http://localhost:5173",
    // 失敗時のみトレースを保存(原因調査用)
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    // クロスブラウザが要件なら追加
    // { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    // { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
  // テスト前にアプリを起動
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
  },
});
```

## クロスブラウザ

- 対応ブラウザが要件のときだけ `projects` に firefox/webkit を追加する。
- 全テストを全ブラウザで回すと時間が膨らむ。クロスブラウザは代表フローに限定する。

## 判断のヒント

- E2E に入れる前に「これは本当に実バックエンド/実ブラウザが要るか」を問う。
  要らなければ統合粒度(`07-integration-msw`)へ。
- E2E が遅い/不安定なら `11-ci-flake` の対策を適用する。

## アンチパターン

- すべての機能を E2E で網羅し、CI が遅く不安定になる(アイスクリームコーン)。
- `data-testid` と手動 `sleep` に依存し、UI 変更と実行タイミングで頻繁に壊れる。
- 1テストに長大なフローを詰め、失敗時にどこで壊れたか分からない。
