---
name: frontend-test-ci-flake
description: >-
  テストを CI に統合し、安定して高速に運用するためのスキル。GitHub Actions 等での実行、flaky
  (不安定)テストの原因と対策(自動待機・時刻/乱数固定・テスト分離・retry の扱い)、カバレッジの
  計測と目標の置き方、実行の高速化(並列・shard)を扱う。次の場面で起動:「テストが遅い/不安定」
  「CI に載せたい」「カバレッジ目標をどうするか」「flaky を直したい」。
keywords:
  - CI統合
  - flakyテスト
  - GitHub Actions
  - カバレッジ
  - テスト高速化
  - retry
  - 並列実行
  - test ci
version: 1.0.0
---

# CI 統合・flaky 対策・カバレッジ運用

## CI への統合(GitHub Actions の完全な例)

```yaml
# .github/workflows/test.yml
name: test

on:
  push:
    branches: [main]
  pull_request:

jobs:
  unit-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - name: Lint & Typecheck（静的解析: 最下層ゲート）
        run: |
          npm run lint
          npm run typecheck
      - name: Unit & Integration
        run: npm run test:coverage
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm ci
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      - name: E2E
        run: npm run test:e2e
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

> 静的解析(lint/typecheck)を最初に走らせ、安価なゲートで早期に弾く。
> E2E は別ジョブに分離し、ユニット/統合の速いフィードバックを妨げない。

## flaky(不安定)テスト対策

flaky は「コード変更なしに成功/失敗が揺れる」テスト。信頼を損ねるため根本対処する。

| 原因 | 対策 |
| --- | --- |
| 非同期表示を待たずにアサート | `findBy*` / `await expect().toBeVisible()` で自動待機。手動 sleep 禁止 |
| 時刻・タイムゾーン依存 | テスト中に時刻を固定(下記) |
| 乱数・ID 依存 | seed 固定、または ID を注入可能にする |
| テスト間の状態汚染 | `afterEach(cleanup)`、MSW の `resetHandlers`、グローバル状態のリセット |
| ネットワーク実依存 | MSW で固定応答(`07-integration-msw`) |
| アニメ/フォント未固定(VRT) | `animations: "disabled"`、フォント待機(`08-visual-regression`) |
| 並列実行での共有リソース競合 | テストを独立させる。共有ファイル/DB を使わない |

### 時刻の固定(Vitest・完全なコード)

```ts
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

describe("時刻に依存する処理", () => {
  beforeEach(() => {
    // 固定時刻を設定
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("現在時刻に基づく表示が安定する", () => {
    expect(new Date().getFullYear()).toBe(2026);
  });
});
```

### retry の扱い(重要)

- CI の `retries: 1`(`10-e2e` の Playwright 設定)は **影響緩和であって根本対処ではない**。
- retry で通ったテストは「flaky」として記録・可視化し、原因を潰す対象にする。
- retry を増やして握りつぶさない。隠れた不安定が積み上がる。

## カバレッジの考え方

- カバレッジは **目安であって目的ではない**。100% を強制しない。
- 重要度の高いロジック・分岐に焦点を当て、型で保証される箇所は除外する(`04-tooling` の
  `coverage.exclude`)。
- 目標値を置く場合はチームで合意し、段階的に引き上げる。数値達成のための無意味なテストを
  生まないこと。
- 「カバーされていない重要分岐」を発見する道具として使うのが本来の用途。

## 高速化

- **Vitest はデフォルトで並列実行**。重いセットアップはファイル単位で共有する。
- E2E は `workers` で並列化、規模が大きければ `--shard` で複数ジョブに分割する。

```bash
# Playwright を3分割し、CI の matrix で並列実行する例
npx playwright test --shard=1/3
```

- 変更影響範囲のみ実行(関連テスト実行)で PR のフィードバックを短縮する。

## HELIX 統合(要確認)

- lint/typecheck・ユニット・統合・E2E の各ステップを、HELIX の 5 層ゲートのどのゲートに
  対応させるかを定義する(正規定義に従う)。
- flaky 検出ログを Learning Engine に渡し、不安定テストの再発防止に活用する設計も検討できる
  (具体は HELIX 側の仕様に合わせる)。
