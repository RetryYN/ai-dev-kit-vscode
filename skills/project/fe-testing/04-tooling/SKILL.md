---
name: frontend-test-tooling
description: >-
  2026 年基準でフロントエンドのテストツールを選定し、初期構成を確定する判断+実装スキル。
  テストランナー(Vitest/Jest 30)、DOM テストライブラリ(Testing Library)、API モック
  (MSW 2.0)、コンポーネント隔離(Storybook 9)、E2E/CT/VRT(Playwright)、a11y(axe-core)の
  選定基準とインストール・初期設定を提供する。次の場面で起動:「何のテストツールを入れるべきか」
  「Vitest と Jest どちらか」「Playwright と Cypress どちらか」「初期設定を知りたい」。
keywords:
  - テストツール選定
  - Vitest
  - Jest
  - Playwright
  - Storybook
  - MSW
  - axe-core
  - テスト初期設定
  - test tooling
version: 1.0.0
---

# テストツール選定と初期構成(2026 年基準)

> 本スキルのツール選定は 2026 年時点の公開情報に基づく。バージョンや推奨は変化するため、
> 導入時に各ツール公式ドキュメントで最新を確認すること。

## 役割別の標準ツール

| 役割 | 第一候補 | 代替/補足 |
| --- | --- | --- |
| ユニット/統合 テストランナー | Vitest | Jest 30(レガシー Webpack/Babel・React Native) |
| DOM テスト・ユーザー視点検証 | Testing Library(`@testing-library/react`) | Vue/Svelte 版あり |
| ユーザー操作シミュレーション | `@testing-library/user-event` | — |
| DOM 用カスタムマッチャ | `@testing-library/jest-dom` | — |
| API モック | MSW(Mock Service Worker)2.0 | — |
| コンポーネント隔離・ドキュメント・統合テスト | Storybook 9(Vitest addon) | — |
| E2E / コンポーネントテスト(CT)/ VRT | Playwright | Cypress(既存資産がある場合) |
| アクセシビリティ | axe-core(`vitest-axe`/`jest-axe`、`@axe-core/playwright`) | — |

## 選定の判断基準

### テストランナー: Vitest か Jest か
- **新規・Vite/ESM 構成 → Vitest**。Vite と設定を共有でき、ホットリロードのフィードバックが速い。
  Jest 互換 API のため移行も容易(多くは `globals: true` 設定でアサーションを再利用できる)。
- **レガシー Webpack/Babel・React Native → Jest 30**。巨大なエコシステムと実績。移行コストが
  見合わない場合は無理に乗り換えない。

### E2E: Playwright か Cypress か
- **新規 → Playwright**。複数ブラウザ・トレースビューア・並列実行・自動待機が強力。
  E2E に加えコンポーネントテスト(CT)と VRT(`toHaveScreenshot()`)を同一ツールで賄える。
- Cypress は既存資産がある場合に維持。VRT 目的だけなら Playwright への一本化を検討。

### コンポーネントテスト: Storybook(Vitest addon)か Playwright CT か
- **Storybook**: story を書くことが UI ドキュメントを兼ね、story を再利用して隔離テスト・VRT・
  a11y を回せる。設計システム/UI カタログがあるプロジェクトと相性が良い。
- **Playwright CT**: 実ブラウザで Playwright のセレクタ/トレースをそのまま使える。E2E を既に
  Playwright で書いているチームは学習コストがほぼゼロ。ビルドは Vite のみ対応。
- 両者は競合でなく補完。story を Playwright CT で再利用(portable stories)する構成も取れる。

---

## 初期構成: Vite + TypeScript + React + Vitest

```bash
# テスト関連の開発依存をインストール
npm install -D vitest @testing-library/react @testing-library/dom \
  @testing-library/jest-dom @testing-library/user-event jsdom

# API モック
npm install -D msw

# アクセシビリティ(Vitest 環境)
npm install -D vitest-axe

# E2E / CT / VRT
npm install -D @playwright/test
npx playwright install --with-deps
```

### `vitest.config.ts`(完全な例)

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    // describe / it / expect をインポート不要で使う
    globals: true,
    // DOM をエミュレートする環境
    environment: "jsdom",
    // 全テスト前に読み込むセットアップ
    setupFiles: ["./src/test/setup.ts"],
    // カバレッジ設定
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      // 型のみのファイルやエントリは除外
      exclude: ["**/*.d.ts", "**/main.tsx", "**/*.stories.tsx"],
    },
  },
});
```

### `src/test/setup.ts`(完全な例)

```ts
import "@testing-library/jest-dom/vitest";
import { afterEach, afterAll, beforeAll } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "./msw/server";

// 各テスト後に DOM をクリーンアップ(テスト間の汚染防止)
afterEach(() => {
  cleanup();
});

// MSW: テスト全体でモックサーバを起動
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

> `./msw/server` の実体は `07-integration-msw` を参照。

### `package.json` スクリプト(完全な例)

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

---

## 関連スキルへの接続

- 実装の詳細はランナー設定後、各実装スキル(05〜10)を参照。
- CI 統合・flaky 対策は `11-ci-flake`。
