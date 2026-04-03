# helix interrupt コマンドガイド

## IIP / CC とは

- `IIP`: 実装中断を伴う追加設計・仕様補完
- `CC`: 追加要件や制約変更に伴うコース修正

`helix interrupt start` は内容を解析して優先度を `P0-P3` に分類する。

## フロー

`start -> apply -> resume`

```bash
# 1) 割り込み開始
helix interrupt start --reason "DB設計が足りない" --kind design_gap --scope user-auth

# 2) 提案適用 + matrix compile
helix interrupt apply --id INT-001

# 3) 再開
helix interrupt resume --id INT-001
```

状態確認:

```bash
helix interrupt status
helix interrupt status --id INT-001 --json
```

誤検知取り消し:

```bash
helix interrupt cancel --id INT-001
```

## `kind` の使い分け

- `design_gap`: 設計不足
- `new_requirement`: 要件追加
- `constraint`: 制約変更
- `po_change`: PO判断による方針変更

## 注意点

- `apply` は `helix matrix compile` を実行する
- human escalation が必要と判定された割り込みは `resume` 不可
