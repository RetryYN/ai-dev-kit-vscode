---
name: frontend-test-unit-logic
description: >-
  純粋ロジック(関数・reducer・状態遷移)とカスタムフックのユニットテストを実装するスキル。
  Vitest を用い、AAA(Arrange-Act-Assert)パターン、境界値・異常系の網羅、renderHook による
  フックのテストを扱う。次の場面で起動:「この関数/reducer/カスタムフックをテストしたい」
  「ロジックのユニットテストを書きたい」。設計判断は `03-test-design` で行い、本スキルは実装を担う。
keywords:
  - ユニットテスト
  - ロジックテスト
  - カスタムフック
  - reducer
  - Vitest
  - renderHook
  - unit test
version: 1.0.0
---

# ユニット × ロジックの実装

対象は種別 A(純粋ロジック)/ B(独立フック)。Vitest を前提とする。
**型で保証される検査は書かない**(`03-test-design` S3)。検証するのは実行時の振る舞い・分岐・状態遷移。

## 原則

- **AAA パターン**: Arrange(準備)→ Act(実行)→ Assert(検証)を1テスト内で明確に分ける。
- **1テスト1関心**: ロジックとインタラクションを混ぜない(`03` S6)。
- **境界値・異常系を網羅**: 正常系だけでなく、0・空・最大・null/undefined・例外を検証する。
- テスト名は「何が起きるべきか」を日本語/英語で具体的に書く。

## 例1: 純粋関数(完全なコード)

```ts
// src/lib/discount.ts
export function applyDiscount(price: number, rate: number): number {
  if (price < 0) throw new Error("price must be >= 0");
  if (rate < 0 || rate > 1) throw new Error("rate must be between 0 and 1");
  return Math.round(price * (1 - rate));
}
```

```ts
// src/lib/discount.test.ts
import { describe, it, expect } from "vitest";
import { applyDiscount } from "./discount";

describe("applyDiscount", () => {
  it("通常の割引を計算して四捨五入する", () => {
    // Arrange / Act
    const result = applyDiscount(1000, 0.2);
    // Assert
    expect(result).toBe(800);
  });

  it("端数は四捨五入される", () => {
    expect(applyDiscount(999, 0.1)).toBe(899); // 899.1 -> 899
  });

  it("割引率0なら価格そのまま", () => {
    expect(applyDiscount(1000, 0)).toBe(1000);
  });

  it("割引率1なら0になる", () => {
    expect(applyDiscount(1000, 1)).toBe(0);
  });

  it("負の価格は例外を投げる", () => {
    expect(() => applyDiscount(-1, 0.2)).toThrow("price must be >= 0");
  });

  it("範囲外の割引率は例外を投げる", () => {
    expect(() => applyDiscount(1000, 1.5)).toThrow("rate must be between 0 and 1");
  });
});
```

## 例2: reducer(完全なコード)

```ts
// src/state/cartReducer.ts
export type CartState = { items: { id: string; qty: number }[] };
export type CartAction =
  | { type: "add"; id: string }
  | { type: "remove"; id: string }
  | { type: "clear" };

export function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "add": {
      const existing = state.items.find((i) => i.id === action.id);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.id === action.id ? { ...i, qty: i.qty + 1 } : i
          ),
        };
      }
      return { items: [...state.items, { id: action.id, qty: 1 }] };
    }
    case "remove":
      return { items: state.items.filter((i) => i.id !== action.id) };
    case "clear":
      return { items: [] };
    default:
      return state;
  }
}
```

```ts
// src/state/cartReducer.test.ts
import { describe, it, expect } from "vitest";
import { cartReducer, type CartState } from "./cartReducer";

describe("cartReducer", () => {
  const empty: CartState = { items: [] };

  it("新規商品を追加すると qty=1 で入る", () => {
    const next = cartReducer(empty, { type: "add", id: "a" });
    expect(next.items).toEqual([{ id: "a", qty: 1 }]);
  });

  it("既存商品を追加すると qty が増える", () => {
    const state: CartState = { items: [{ id: "a", qty: 1 }] };
    const next = cartReducer(state, { type: "add", id: "a" });
    expect(next.items).toEqual([{ id: "a", qty: 2 }]);
  });

  it("remove で該当商品が消える", () => {
    const state: CartState = { items: [{ id: "a", qty: 1 }, { id: "b", qty: 1 }] };
    const next = cartReducer(state, { type: "remove", id: "a" });
    expect(next.items).toEqual([{ id: "b", qty: 1 }]);
  });

  it("clear で空になる", () => {
    const state: CartState = { items: [{ id: "a", qty: 1 }] };
    expect(cartReducer(state, { type: "clear" })).toEqual({ items: [] });
  });

  it("元の state を破壊しない(イミュータブル)", () => {
    const state: CartState = { items: [{ id: "a", qty: 1 }] };
    cartReducer(state, { type: "add", id: "a" });
    expect(state.items).toEqual([{ id: "a", qty: 1 }]);
  });
});
```

## 例3: カスタムフック(完全なコード)

```ts
// src/hooks/useCounter.ts
import { useState, useCallback } from "react";

export function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  const increment = useCallback(() => setCount((c) => c + 1), []);
  const decrement = useCallback(() => setCount((c) => c - 1), []);
  const reset = useCallback(() => setCount(initial), [initial]);
  return { count, increment, decrement, reset };
}
```

```ts
// src/hooks/useCounter.test.ts
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "./useCounter";

describe("useCounter", () => {
  it("初期値を反映する", () => {
    const { result } = renderHook(() => useCounter(5));
    expect(result.current.count).toBe(5);
  });

  it("increment で +1 される", () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => {
      result.current.increment();
    });
    expect(result.current.count).toBe(1);
  });

  it("reset で初期値に戻る", () => {
    const { result } = renderHook(() => useCounter(3));
    act(() => {
      result.current.increment();
      result.current.reset();
    });
    expect(result.current.count).toBe(3);
  });
});
```

## アンチパターン

- 型で保証される値検証を書く(`number` 型なのに「数値であること」をテスト)。
- 実装詳細(内部変数名・呼び出し回数)に結合し、リファクタで壊れる。
- 1テストに複数の関心を詰め、失敗時に原因が特定できない。
