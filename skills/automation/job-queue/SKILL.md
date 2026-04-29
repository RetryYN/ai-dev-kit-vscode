---
name: job-queue
description: HELIX の非同期ジョブ登録、worker、retry を管理する automation job-queue skeleton。
triggers:
  - ジョブ登録時
  - 非同期実行設計時
  - retry 制御時
metadata:
  helix_layer: L4
  category: automation
---

# automation/job-queue

## 1. 概要

`automation/job-queue` は、HELIX の非同期ジョブ、優先度、遅延実行、再試行制御を共通化するための skeleton skill です。Sprint 1 では `jobs` table と CLI skeleton を提供し、worker の排他実行や retry アルゴリズムは後続 Sprint で実装します。

## 2. 提供機能

- `helix job enqueue`
- `helix job worker`
- `helix job status`
- `helix job cancel`
- `helix job retry`

## 3. 利用例

```bash
helix job enqueue --task "helix:command:verify-all" --priority 7
helix job worker --once
```

## 4. トラスト境界

scope は project-local queue を基本とします。payload は task type ごとの allowlist と schema validation を通した後に保存し、ログ出力や observability event では redaction 済み JSON のみ扱います。

## 5. 関連 PLAN

PLAN-005 を起点に job queue を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の非同期処理や再試行処理から再利用します。
