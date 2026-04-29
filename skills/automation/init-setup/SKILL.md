---
name: init-setup
description: HELIX automation の初期化検証、導入、修復を扱う setup skeleton。
triggers:
  - セットアップ検証時
  - automation 初期化時
  - 環境修復時
metadata:
  helix_layer: cross
  category: automation
---

# automation/init-setup

## 1. 概要

`automation/init-setup` は、HELIX automation 基盤の DB、CLI、設定、権限を検証・導入・修復するための skeleton skill です。Sprint 1 では CLI の受け口のみを提供し、具体的な verify/install/repair 手順は後続 Sprint で実装します。

## 2. 提供機能

- `helix setup verify`
- `helix setup install`
- `helix setup repair`

## 3. 利用例

```bash
helix setup verify
helix setup repair
```

## 4. トラスト境界

scope は project setup を基本とし、home 配下の設定を扱う場合は明示的な user approval と file permission 検証を前提にします。診断結果は redaction 済みの path、reason code、status のみを出力します。

## 5. 関連 PLAN

PLAN-005 を起点に automation setup を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の導入検証と復旧手順から再利用します。
