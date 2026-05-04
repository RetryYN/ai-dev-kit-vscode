---
name: observability
description: HELIX automation の events と metrics を記録・集計・export する observability。
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

`automation/observability` は、HELIX automation の event と metric を共通フォーマットで記録し、report/export まで扱う skill です。記録時と export 時に redaction を適用し、export 先は `~/.helix/quarantine/` 配下へ fail-closed します。

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
