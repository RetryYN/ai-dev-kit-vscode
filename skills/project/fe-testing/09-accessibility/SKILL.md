---
name: frontend-test-accessibility
description: >-
  アクセシビリティ(a11y)テストを実装するスキル。axe-core を用い、Vitest 環境(vitest-axe/
  jest-axe)でのコンポーネント単位の違反検出、Playwright(@axe-core/playwright)での画面単位監査、
  ロール/ラベル/aria 属性の検証、キーボード操作の検証を扱う。自動チェックの限界(手動検証が
  必要な範囲)も明示する。次の場面で起動:「アクセシビリティを検証したい」「WCAG 準拠を確認したい」
  「キーボード操作をテストしたい」。設計判断は `03-test-design`。
keywords:
  - アクセシビリティテスト
  - a11y
  - axe-core
  - vitest-axe
  - jest-axe
  - WCAG
  - キーボード操作
  - accessibility test
version: 1.0.0
---

# アクセシビリティ(a11y)テストの実装

axe-core を核に、自動検出できる違反を機械的に検査する。
**構造(ロール/ラベル/aria/コントラスト)は安価に自動化**し、**操作系(キーボード)は
インタラクションテストに同居**させる(`03` S5/S6)。

## ツールの使い分け

| 環境 | ライブラリ | 用途 |
| --- | --- | --- |
| Vitest + Testing Library | `vitest-axe`(Jest なら `jest-axe`) | コンポーネント単位の違反検出 |
| Playwright | `@axe-core/playwright` | 実ブラウザでの画面単位監査 |

## 例1: コンポーネント単位の違反検出(Vitest・完全なコード)

```tsx
// src/components/Modal.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { axe } from "vitest-axe";
import { Modal } from "./Modal";

describe("Modal の a11y", () => {
  it("開いた状態で axe 違反がない", async () => {
    const { container } = render(
      <Modal isOpen title="確認">
        <p>実行してよろしいですか?</p>
        <button>キャンセル</button>
        <button>実行</button>
      </Modal>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("dialog ロールと aria-modal を持つ", () => {
    render(
      <Modal isOpen title="確認">
        <p>本文</p>
      </Modal>
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    // タイトルが dialog のラベルになっている
    expect(dialog).toHaveAccessibleName("確認");
  });
});
```

> `toHaveNoViolations` マッチャは `vitest-axe` の expect 拡張を取り込むことで有効になる。
> セットアップで以下を追加する(完全な例):

```ts
// src/test/setup.ts への追記
import { expect } from "vitest";
import * as matchers from "vitest-axe/matchers";

expect.extend(matchers);
```

## 例2: キーボード操作の検証(完全なコード)

```tsx
// src/components/Menu.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Menu } from "./Menu";

describe("Menu のキーボード操作", () => {
  it("Tab でフォーカス移動でき、Enter で項目を選べる", async () => {
    const user = userEvent.setup();
    render(<Menu />);

    // Tab で最初の項目にフォーカス
    await user.tab();
    expect(screen.getByRole("menuitem", { name: "ホーム" })).toHaveFocus();

    // 次の項目へ
    await user.tab();
    expect(screen.getByRole("menuitem", { name: "設定" })).toHaveFocus();

    // Enter で選択結果が反映される
    await user.keyboard("{Enter}");
    expect(screen.getByText("設定を開きました")).toBeInTheDocument();
  });
});
```

## 例3: 画面単位の監査(Playwright・完全なコード)

```ts
// e2e/a11y/home.spec.ts
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("ホーム画面に重大な a11y 違反がない", async ({ page }) => {
  await page.goto("/");

  const results = await new AxeBuilder({ page })
    // 検査対象の WCAG タグを限定する
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

## 自動チェックの限界(重要)

axe-core 等の自動検査は **a11y 問題の一部しか検出できない**。次は人手の検証が要る。

- フォーカス順序が論理的か、フォーカストラップが適切か(モーダル等)。
- スクリーンリーダーでの読み上げが意味として通るか。
- 色だけに依存しない情報伝達になっているか。
- 操作のしやすさ・認知負荷など体験面。

自動チェックは「機械的に検出できる退行を CI で防ぐ」役割と位置づけ、要件が高い場合は
手動監査・実機(支援技術)検証を併用する。

## 判断のヒント

- a11y が要件 or 公共性が高いプロジェクトでは優先度を上げる(`03` S4)。
- 構造の違反検出はユニット〜統合粒度で安価に、操作系は操作テストに同居させる。

## アンチパターン

- 自動チェックの「違反0」をもって「アクセシブル」と断定する。
- 違反を抑えるためだけに aria を過剰付与し、かえって読み上げを壊す。
