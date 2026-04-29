---
name: observability
description: HELIX automation の events と metrics を記録・集計する observability skeleton。
triggers:
  - イベント記録時
  - メトリクス記録時
  - 運用レポート作成時
metadata:
  helix_layer: cross
  category: automation
---

# automation/observability

## 1. 概要

`automation/observability` は、HELIX automation の event と metric を共通フォーマットで記録し、後続 Sprint の report/export 実装につなげるための skeleton skill です。Sprint 1 では `events` / `metrics` table と CLI skeleton を定義します。

## 2. 提供機能

- `helix observe log`
- `helix observe metric`
- `helix observe report`
- `helix observe export`

## 3. 利用例

```bash
helix observe log --event scheduler.run_due --severity info
helix observe metric --name queue.depth --value 3
```

## 4. トラスト境界

scope は project-local observability を基本にします。`data_json` と `tags_json` は redaction 適用後の構造化データのみ保存し、secret、credential、token、個人情報、payload 本文の生値は保存しません。

## 5. 関連 PLAN

PLAN-005 を起点に observability を共通化し、PLAN-002 / PLAN-003 / PLAN-004 の運用ログ、品質測定、migration rehearsal 証跡から再利用します。
