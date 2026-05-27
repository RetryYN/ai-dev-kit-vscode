---
name: frontend-test-visual-regression
description: >-
  見た目の意図しない変化を検出するビジュアルリグレッションテスト(VRT)を実装するスキル。
  Playwright の toHaveScreenshot() による画面/コンポーネントの画像差分、Storybook の story を
  使った部品単位 VRT、ベースライン管理・差分閾値・不安定要素(アニメ/日時/フォント)の固定を扱う。
  次の場面で起動:「見た目の退行を防ぎたい」「スクリーンショット比較を入れたい」「デザイン崩れを
  検出したい」。設計判断は `03-test-design`。
keywords:
  - ビジュアルリグレッション
  - VRT
  - スクリーンショット
  - toHaveScreenshot
  - Playwright
  - Storybook
  - visual regression
version: 1.0.0
---

# ビジュアルリグレッション(VRT)の実装

「振る舞い」ではなく「描画結果(見た目)」の退行を画像差分で検出する。
振る舞いテスト・スナップショットとは **運用サイクルが異なるため分離**する(`03` S6)。

## 粒度の選択

- **部品単位 VRT**: Storybook の story を各状態(default/loading/error/disabled)で用意し、
  story 単位でキャプチャ。デザインシステムや UI カタログがあるなら第一候補。
- **画面全体 VRT**: Playwright で実画面をキャプチャ。クリティカルな画面のレイアウト崩れ検出に。

## 例: Playwright の画像差分(完全なコード)

```ts
// e2e/visual/home.spec.ts
import { test, expect } from "@playwright/test";

test.describe("ホーム画面の見た目", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // フォント読み込み完了を待つ(描画安定化)
    await page.evaluate(() => document.fonts.ready);
  });

  test("初期表示が基準画像と一致する", async ({ page }) => {
    // 初回実行で baseline を生成、2回目以降は差分比較
    await expect(page).toHaveScreenshot("home-default.png", {
      // アンチエイリアス等の微差を許容(0〜1, 既定は厳しめ)
      maxDiffPixelRatio: 0.01,
      // アニメーションを止めてからキャプチャ
      animations: "disabled",
    });
  });

  test("特定コンポーネントだけを比較する", async ({ page }) => {
    const card = page.getByRole("region", { name: "お知らせ" });
    await expect(card).toHaveScreenshot("notice-card.png", {
      animations: "disabled",
    });
  });
});
```

`playwright.config.ts` の関連設定(完全な例):

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:5173",
  },
  expect: {
    toHaveScreenshot: {
      // 全 VRT 共通の差分許容
      maxDiffPixelRatio: 0.01,
    },
  },
  // OS/ブラウザ差を吸収するため、プロジェクトを固定する
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
```

ベースラインの更新:

```bash
# 意図した変更後にベースライン画像を更新する
npx playwright test --update-snapshots
```

## 不安定要素の固定(flaky 防止)

VRT は環境差で壊れやすい。以下を固定してから比較する。

- **アニメーション**: `animations: "disabled"` で停止。
- **フォント**: `document.fonts.ready` を待つ。CI と開発環境でフォントを揃える(Docker 推奨)。
- **日時/乱数**: 時刻や ID をテスト中に固定する(`11-ci-flake` の時刻固定を参照)。
- **動的データ**: API は MSW 等で固定応答にする(`07-integration-msw`)。
- **レンダリング環境**: ベースラインは CI と同一環境(同一 OS/ブラウザ)で生成する。
  ローカルで作った画像を CI と比較しない。

## Storybook 連携(部品単位 VRT)

- Storybook 9 では story を Vitest addon / Playwright から再利用できる。
- story を状態別に用意し、各 story をキャプチャ対象にすることで、状態網羅の VRT を構成できる。
- 外部 VRT サービス(クラウド差分管理)を使う場合も、入力は同じ story 群になる。

## 判断のヒント

- VRT は「見た目の退行が事業影響を持つ画面」に限定する(`03` S4)。全画面に入れない。
- レイアウト/スタイルの正しさは VRT、要素の存在やロールは a11y/インタラクションで分担する。

## アンチパターン

- 動的データ・アニメ・フォントを固定せず、毎回差分が出て誰も差分を見なくなる。
- ローカルと CI で異なる環境のベースラインを比較し、恒常的に失敗する。
- 振る舞い検証を VRT で代替しようとする(画像差分は「なぜ壊れたか」を説明しない)。
