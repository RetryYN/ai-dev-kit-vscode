---
name: scheduler
description: HELIX の cron-like 定期実行、単発 at 実行、期限到達 task 実行を管理する automation scheduler。
triggers:
  - スケジュール登録時
  - 定期実行設計時
  - run-due 実行時
metadata:
  helix_layer: L4
  category: automation
---

# automation/scheduler

## 1. 概要

`automation/scheduler` は、HELIX の定期実行、相対時刻実行、期限到達タスク処理を共通化する skill です。`helix scheduler` は cron / `+5m` / `add-at` を受け付け、allowlist 済み task を fail-closed で実行します。`run-due` は既定で stale running schedule を復旧してから due task を処理します。

## 2. 提供機能

- `helix scheduler add`
- `helix scheduler add-at`
- `helix scheduler list`
- `helix scheduler cancel`
- `helix scheduler status`
- `helix scheduler run-due`
- `helix scheduler requeue-stale`

## 3. 利用例

```bash
helix scheduler add --schedule "+5m" --task "helix:command:status"
helix scheduler add-at --at "2026-05-03T12:00:00Z" --task "helix:command:status"
helix scheduler run-due --max 1
helix scheduler run-due --max 1 --no-requeue-stale
helix scheduler requeue-stale --older-than 3600
```

## 4. トラスト境界

scope は `project` を基本とし、将来の shared schedule では `home` scope を明示します。task payload は allowlist と redaction 適用後の構造化データのみ保存し、secret、token、個人情報をログや event data に残さない方針です。

## 5. 関連 PLAN

PLAN-005 を起点に scheduler を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の定期処理や検証処理から再利用します。
