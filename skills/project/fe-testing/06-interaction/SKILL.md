---
name: frontend-test-interaction
description: >-
  ユーザー操作(クリック/入力/フォーカス/キーボード)を起点としたインタラクションテストを実装する
  スキル。Testing Library + user-event を用い、ロール優先のクエリ、操作→結果の検証、非同期 UI の
  findBy/waitFor を扱う。次の場面で起動:「ボタン操作や入力の挙動をテストしたい」「フォームの
  バリデーション表示をテストしたい」。設計判断は `03-test-design`、API 連動は `07-integration-msw`。
keywords:
  - インタラクションテスト
  - user-event
  - Testing Library
  - getByRole
  - フォームテスト
  - interaction test
version: 1.0.0
---

# インタラクションテストの実装

操作起点の振る舞いを検証する。**実ユーザーに近い操作と、ユーザーから見える結果**を扱う。
Testing Library + `@testing-library/user-event` を前提とする。

## 原則

- **クエリはロール優先**: `getByRole` を最優先し、次に `getByLabelText` / `getByText`。
  `getByTestId` は最後の手段。アクセシビリティと整合する書き方が、壊れにくく a11y も兼ねる。
- **操作は user-event**: `fireEvent` ではなく `userEvent` を使う。実際の操作(フォーカス遷移・
  入力イベント列)を忠実に再現する。`userEvent.setup()` を各テスト冒頭で呼ぶ。
- **非同期 UI は findBy / waitFor**: 表示が遅延する要素は `findBy*`(Promise)で待つ。
- 「操作 → その結果の表示確認」は同居可(`03` S6)。ロジック検証とは分離する。

## 例1: ボタン操作とコールバック(完全なコード)

```tsx
// src/components/Counter.tsx
import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p>現在値: {count}</p>
      <button onClick={() => setCount((c) => c + 1)}>増やす</button>
      <button onClick={() => setCount(0)}>リセット</button>
    </div>
  );
}
```

```tsx
// src/components/Counter.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Counter } from "./Counter";

describe("Counter", () => {
  it("『増やす』を押すと表示値が増える", async () => {
    const user = userEvent.setup();
    render(<Counter />);

    // 操作
    await user.click(screen.getByRole("button", { name: "増やす" }));
    await user.click(screen.getByRole("button", { name: "増やす" }));

    // 結果の表示確認(同居可)
    expect(screen.getByText("現在値: 2")).toBeInTheDocument();
  });

  it("『リセット』を押すと0に戻る", async () => {
    const user = userEvent.setup();
    render(<Counter />);

    await user.click(screen.getByRole("button", { name: "増やす" }));
    await user.click(screen.getByRole("button", { name: "リセット" }));

    expect(screen.getByText("現在値: 0")).toBeInTheDocument();
  });
});
```

## 例2: フォーム入力とバリデーション表示(完全なコード)

```tsx
// src/components/LoginForm.tsx
import { useState } from "react";

type Props = { onSubmit: (email: string) => void };

export function LoginForm({ onSubmit }: Props) {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!email.includes("@")) {
      setError("メールアドレスの形式が正しくありません");
      return;
    }
    setError(null);
    onSubmit(email);
  };

  return (
    <div>
      <label htmlFor="email">メールアドレス</label>
      <input
        id="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      {error && <p role="alert">{error}</p>}
      <button onClick={handleSubmit}>ログイン</button>
    </div>
  );
}
```

```tsx
// src/components/LoginForm.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "./LoginForm";

describe("LoginForm", () => {
  it("不正な形式だとエラーを表示し送信しない", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("メールアドレス"), "invalid");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    // 結果: エラーが出る / コールバックは呼ばれない
    expect(screen.getByRole("alert")).toHaveTextContent(
      "メールアドレスの形式が正しくありません"
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("正しい形式だと送信されエラーは消える", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("メールアドレス"), "user[at]example.com");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(onSubmit).toHaveBeenCalledWith("user[at]example.com");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
```

## 例3: 非同期表示の待機(完全なコード)

```tsx
// src/components/AsyncMessage.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AsyncMessage } from "./AsyncMessage";

describe("AsyncMessage", () => {
  it("操作後に遅延表示されるメッセージを待って検証する", async () => {
    const user = userEvent.setup();
    render(<AsyncMessage />);

    await user.click(screen.getByRole("button", { name: "読み込み" }));

    // findBy* は要素が現れるまで待つ(Promise)
    expect(await screen.findByText("完了しました")).toBeInTheDocument();
  });
});
```

## アンチパターン

- `getByTestId` を多用し、ユーザーから見えない実装構造に結合する。
- `fireEvent` で個別イベントだけ発火させ、実際の操作列(フォーカス等)を再現しない。
- 非同期表示を待たずに同期的にアサートし、flaky になる(`11-ci-flake` 参照)。
