---
name: lock
description: HELIX の single-host DB lock を管理する automation lock skeleton。
triggers:
  - 排他制御時
  - DB lock 取得時
  - 並列実行防止時
metadata:
  helix_layer: cross
  category: automation
---

# automation/lock

## 1. 概要

`automation/lock` は、HELIX の single-host 前提の DB lock を共通化するための skeleton skill です。Sprint 1 では `locks` table と CLI skeleton を提供し、期限切れ lock の再取得や競合時 reason code は後続 Sprint で実装します。

## 2. 提供機能

- `helix lock acquire`
- `helix lock release`
- `helix lock list`
- `helix lock status`

## 3. 利用例

```bash
helix lock acquire plan-005 --scope project
helix lock release plan-005
```

## 4. トラスト境界

scope は `home` と `project` の 2 種類に限定します。lock 名、pid、期限以外の詳細情報は保存せず、観測イベントに出す場合も process や path 由来の機密値を redaction します。

## 5. 関連 PLAN

PLAN-005 を起点に lock を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の二重実行防止と migration rehearsal から再利用します。
