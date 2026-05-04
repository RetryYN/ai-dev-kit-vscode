# helix dashboard コマンドガイド

`helix dashboard` は `.helix/` 配下の状態を読み取り、現在のフェーズ、ゲート、PLAN、Scrum、Reverse gap、主要成果物数を 1 画面に集約する読み取り専用 snapshot コマンドです。

HELIX の Dashboard 構想管理はスコープ外です。このコマンドは対話型/常設 dashboard ではなく、`helix status` を補助する静的表示として維持します。

## 使い方

```bash
helix dashboard
helix dashboard --json
```

## 表示内容

- `Project / Mode / Phase`
- `Gates`: `passed / failed / pending / skipped / invalidated` の集計
- `Plans`: `.helix/plans/PLAN-*.yaml` の status 集計
- `Scrum`: 現在 sprint と仮説 status 集計
- `Reverse`: `R4-gap-register.yaml` / legacy md / type 別 R4 routing の status 集計
- `Artifacts`: design docs / retros / session summaries / handover / deferred findings / debt の件数
- `Jobs / Schedules`: SQLite にある job / scheduler status 集計
- `Next`: 現在 phase と gate 状態から見た次アクション（L9-L11 を含む）

## JSON 出力

CI や外部集計では `--json` を使います。

```bash
helix dashboard --json
```

出力は `project`, `mode`, `phase`, `gates`, `plans`, `scrum`, `reverse`, `artifacts`, `next_action` を含む JSON object です。
