---
name: frontend-test-integration-msw
description: >-
  API に依存する複合 UI のインテグレーションテストを、MSW(Mock Service Worker)2.0 で
  ネットワーク層をモックして実装するスキル。setupServer によるテスト用サーバ、http ハンドラ定義、
  per-test でのエラー/エッジケース上書き、ローディング/成功/失敗状態の検証を扱う。次の場面で起動:
  「API を叩く画面/フォームをテストしたい」「fetch をモックしたい」「ローディングやエラー表示を
  検証したい」。設計判断は `03-test-design`、操作部分は `06-interaction` を併用する。
keywords:
  - インテグレーションテスト
  - MSW
  - Mock Service Worker
  - APIモック
  - setupServer
  - http handler
  - integration test
version: 1.0.0
---

# インテグレーション + API モック(MSW)の実装

複合 UI(種別 C/D)で、API 依存を **MSW でネットワーク層ごと差し替えて** テストする。
`fetch` や axios を直接スタブせず、「ネットワークがどう振る舞うか」を記述するのが MSW の思想。
これにより、アプリ側は実際の HTTP リクエストを発行したまま、応答だけを制御できる。

## ディレクトリ構成

```
src/
  test/
    msw/
      handlers.ts   # 既定のリクエストハンドラ
      server.ts     # Node(テスト)用サーバ
  components/
    UserProfile.tsx
    UserProfile.test.tsx
```

## ハンドラとサーバ(完全なコード)

```ts
// src/test/msw/handlers.ts
import { http, HttpResponse } from "msw";

export const handlers = [
  http.get("/api/user/:id", ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: "山田太郎",
      email: "taro[at]example.com",
    });
  }),
];
```

```ts
// src/test/msw/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

// テストプロセスで起動するモックサーバ
export const server = setupServer(...handlers);
```

> サーバの `listen` / `resetHandlers` / `close` は `04-tooling` の `src/test/setup.ts` で
> 全テスト共通に登録済み。`onUnhandledRequest: "error"` により、未定義のリクエストは
> テスト失敗として検出される(モック漏れの早期発見)。

## テスト対象(完全なコード)

```tsx
// src/components/UserProfile.tsx
import { useEffect, useState } from "react";

type User = { id: string; name: string; email: string };

export function UserProfile({ id }: { id: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetch(`/api/user/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("failed");
        return res.json();
      })
      .then((data: User) => {
        if (active) setUser(data);
      })
      .catch(() => {
        if (active) setError("ユーザー情報の取得に失敗しました");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [id]);

  if (loading) return <p>読み込み中...</p>;
  if (error) return <p role="alert">{error}</p>;
  return (
    <div>
      <h2>{user!.name}</h2>
      <p>{user!.email}</p>
    </div>
  );
}
```

## テスト(完全なコード)

```tsx
// src/components/UserProfile.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../test/msw/server";
import { UserProfile } from "./UserProfile";

describe("UserProfile", () => {
  it("成功時: ローディング後にユーザー情報を表示する", async () => {
    render(<UserProfile id="1" />);

    // 最初はローディング
    expect(screen.getByText("読み込み中...")).toBeInTheDocument();

    // 取得完了後に名前が出る(findBy で待機)
    expect(await screen.findByRole("heading", { name: "山田太郎" })).toBeInTheDocument();
    expect(screen.getByText("taro[at]example.com")).toBeInTheDocument();
  });

  it("失敗時: サーバ500ならエラー表示する(per-test 上書き)", async () => {
    // このテストだけ 500 を返すよう上書き
    server.use(
      http.get("/api/user/:id", () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    render(<UserProfile id="1" />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "ユーザー情報の取得に失敗しました"
    );
  });

  it("空応答などのエッジケースも per-test で表現できる", async () => {
    server.use(
      http.get("/api/user/:id", () => {
        return HttpResponse.json({ id: "1", name: "", email: "" });
      })
    );

    render(<UserProfile id="1" />);
    // 名前が空でも heading 要素自体は存在する
    expect(await screen.findByRole("heading")).toBeInTheDocument();
  });
});
```

## MSW のベストプラクティス

- ハンドラは **リソース単位で集中管理**(`handlers.ts`)。テストごとの差分は `server.use()` で上書きする。
- **リクエスト内容を直接アサートしない**。検証は「アプリが応答をどう扱うか(表示・状態)」に置く。
- ローディング → 成功 / 失敗 / 空 の各状態を分けてテストする(`03` S6 に従い状態ごとに分離)。
- ブラウザ実行(Storybook/Playwright CT)では `setupWorker`(`msw/browser`)、Node テストでは
  `setupServer`(`msw/node`)を使い分ける。

## アンチパターン

- `global.fetch` を直接モックして、ネットワーク層の実挙動から乖離する。
- すべての状態を1テストに詰める(失敗時に原因が特定できない)。
- `onUnhandledRequest` を緩めてモック漏れを見逃す。
