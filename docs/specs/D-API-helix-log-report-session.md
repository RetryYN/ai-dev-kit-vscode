# D-API: helix log report session（PLAN-016 Sprint .1）

**Status**: Draft  
**Owner**: docs  
**Date**: 2026-05-03  
**Source**: [docs/plans/PLAN-016-session-summary-helix-log-report.md](../plans/PLAN-016-session-summary-helix-log-report.md)  

## 1. 目的

- Stop hook で `helix-session-summary` が行ってきたセッション集計を、CLI から任意日付で再取得できる形へ切り替える契約を確定する。
- `helix log report session` で Markdown / JSON の2形式を提供し、`session-summaries/*.md` の新規生成依存を減らす。
- 既存データ（`hook_events`, `gate_runs`, `cost_log`）を日付境界で集計し、既存の `helix-session-summary` の集計ロジックを再利用可能な仕様として固定する。

## 2. 非対象

- 実装（`cli/helix-log`, `cli/lib/helix_db.py`, `cli/helix-session-summary`）
- `helix log` の既存 report（`summary|tasks|actions|feedback|quality`）の既定実装変更
- DB migration や本番環境の運用手順

## 3. 対象 CLI 契約

### 3.1 サブコマンド

`helix log report session [options]`

### 3.2 オプション

- `--date <YYYY-MM-DD>`  
  - 対象日付を指定。省略時は `today`。
  - `--date` 不正時は `exit 2` で stderr エラー終了。  
- `--format <md|json>`  
  - 既定値: `md`
- `--no-events`  
  - Hook イベント集計セクションを省略
- `--no-gates`  
  - ゲート実行集計セクションを省略
- `--no-cost`  
  - コスト記録集計セクションを省略

### 3.3 `--date` 境界と TZ

- 集計対象は `date(created_at) = :date` で一致した行のみ。
- `:date` は `YYYY-MM-DD` のローカル日付文字列。
- `created_at` の扱いがローカルタイムベースで既存実装されている前提に合わせ、日付境界はローカル日付（SQLite `date(created_at)`）を使用する。

### 3.4 エラーハンドリング

- 不正日付（正規表現不一致や変換不能）: `exit 2`。stderr へユーザー向け説明を出力。
- DB が未初期化: 既存 `helix log report` と同様に終了コード 1 系（現行挙動継続）で終了。

## 4. 出力フォーマット

### 4.1 `md`（default）

表示フォーマット:

```
## YYYY-MM-DD セッション (最終更新 HH:MM, 終了 N 回)

Hook イベント | count 表
ゲート実行 | result | count 表
コスト記録 | count
```

#### 4.1.1 各セクション

- Hook イベント表:
  - `event_type`, `count`
- ゲート実行表:
  - `gate`, `result`, `count`
- コスト記録表:
  - `role`, `model`, `count`
- レコードが無い場合は各表に以下プレースホルダを表示:
  - `（記録なし）`, `-`, `-`（列数維持）

#### 4.1.2 `終了 N 回` の定義

- `cost_log` の以下件数:
  - `role = 'opus-pm'`
  - `model LIKE 'claude-opus-4-%'`
  - `date(created_at) = :date`
- 上記件数をヘッダ末尾に反映。

#### 4.1.3 最終更新時刻

- `last_updated` は `cost_log` の `MAX(created_at)` を優先的に採用。
- `cost_log` が空の場合は、`hook_events` と `gate_runs` の `MAX(created_at)` から fallback して最新値を決定（未更新時は表示なし）。

### 4.2 `json`

```json
{
  "date": "YYYY-MM-DD",
  "total_session_end": 12,
  "last_updated": "2026-05-03T17:39:00",
  "hook_events": [
    { "event_type": "gate_ready", "count": 3 },
    { "event_type": "design_sync", "count": 1 }
  ],
  "gates": [
    { "gate": "G4", "result": "pass", "count": 4 },
    { "gate": "G4", "result": "fail", "count": 1 }
  ],
  "cost_log": [
    { "role": "opus-pm", "model": "claude-opus-4-6", "count": 12 }
  ]
}
```

- `--no-events/--no-gates/--no-cost` 指定時は該当配列を空配列 `[]` にする。

## 5. DB クエリ定義（UTC/Local 方針に依存せず created_at を比較）

### 5.1 Hook イベント

```sql
SELECT event_type, COUNT(*) AS count
FROM hook_events
WHERE date(created_at) = :date
GROUP BY event_type
ORDER BY event_type;
```

### 5.2 ゲート実行

```sql
SELECT gate, result, COUNT(*) AS count
FROM gate_runs
WHERE date(created_at) = :date
GROUP BY gate, result
ORDER BY gate, result;
```

### 5.3 コスト記録

```sql
SELECT role, model, COUNT(*) AS count
FROM cost_log
WHERE date(created_at) = :date
GROUP BY role, model
ORDER BY role, model;
```

### 5.4 終了回数（セッション数）

```sql
SELECT COUNT(*) 
FROM cost_log
WHERE role = 'opus-pm' AND model LIKE 'claude-opus-4-%' AND date(created_at) = :date;
```

### 5.5 最終更新時刻

```sql
SELECT MAX(created_at)
FROM cost_log
WHERE date(created_at) = :date;
```

必要に応じて `hook_events` / `gate_runs` の最大値へ fallback。

## 6. 既存フォーマットとの互換

- 旧個別ブロック（`## セッション終了: HH:MM`, `### コスト記録` + `- opus-pm: N回`）は本仕様では生成しない。
- 既存 stop hook の既知出力行に依存するドキュメントは、Sprint .2 以降の実装時に利用文言を更新する想定。

## 7. スケッチ（実装向け）

1. `helix log report` のサブタイプ `session` を追加し、`--date`/`--format`/`--no-*` を受け取る。
2. `helix_db.py` に session report 専用処理（md/json の両形式）を追加し、上記 SQL を固定実行。
3. `cli/helix-session-summary` の stop hook 役割は DB INSERT 優先（本仕様では出力契約対象外）。
4. `--format json` のみの自動化用途を想定し、`session` report の既存バリデーションを新規テストで固定。

## 8. 未確定項目（PM 確認待ち）

- `--date` の「今日」のタイムゾーンを明示的にどの時刻系へ固定するか（現行はローカル日付想定）
  - 現時点では既存実装（`helix-session-summary`、`date(created_at)`）に合わせて `local` を暫定採用。
- JSON の `last_updated` フォーマット（`HH:MM` か `YYYY-MM-DDTHH:MM:SS`）を実装時に確定（本仕様では ISO8601 を推奨）。

## 9. 参照

- [PLAN-016: session-summary の md 廃止 — Stop hook を helix log report session 化](../plans/PLAN-016-session-summary-helix-log-report.md)
- [PLAN-016 TL review findings](../../.helix/reviews/plans/PLAN-016.json)
- [cli/helix-log](../../cli/helix-log)
- [cli/helix-session-summary](../../cli/helix-session-summary)
- [cli/lib/helix_db.py](../../cli/lib/helix_db.py)
- [D-HOOK-SPEC](../design/D-HOOK-SPEC.md)
