---
name: job-queue
description: HELIX の非同期ジョブ登録、worker、retry、list を管理する automation job-queue。
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

`automation/job-queue` は、HELIX の非同期ジョブ、優先度、遅延実行、再試行制御を共通化する skill です。`helix job` は enqueue / worker / status / cancel / retry / requeue-stale / list を提供し、SQLite の atomic claim で二重実行を防ぎます。`worker` は既定で stale running job を復旧してから次の job を処理します。

## 2. 提供機能

- `helix job enqueue`
- `helix job worker`
- `helix job status`
- `helix job cancel`
- `helix job retry`
- `helix job requeue-stale`
- `helix job list`

## 3. 利用例

```bash
helix job enqueue --task "helix:command:status" --priority 7
helix job worker --max-jobs 1 --idle-sleep 0
helix job worker --max-jobs 1 --no-requeue-stale
helix job requeue-stale --older-than 3600
helix job list --status pending --limit 10
```

`requeue-stale` は worker crash などで `running` のまま残った job を復旧します。retry 可能なら `pending` に戻し、retry 上限を超えている場合は `failed` に倒します。

## 4. トラスト境界

scope は project-local queue を基本とします。payload は task type ごとの allowlist と schema validation を通した後に保存し、ログ出力や observability event では redaction 済み JSON のみ扱います。

## 5. 関連 PLAN

PLAN-005 を起点に job queue を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の非同期処理や再試行処理から再利用します。
