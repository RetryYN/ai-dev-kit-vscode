# PLAN-005: 運用自動化スキル群（scheduler/job-queue/lock/init-setup/observability）

## 1. 目的

HELIX で発生する定期実行、非同期ジョブ、排他制御、初期化検証、観測を feature をまたいで再利用する
**共通インフラ**として統合する。
PLAN-002 / PLAN-003 の既存設計を前提化し、CLI 仕様、DB スキーマ、スケジュール/ジョブ処理、ロック戦略、観測ルールを PLAN レベルで凍結する。

---

## 2. 前提

- 作成対象: `docs/plans/PLAN-005-ops-automation-skills.md` の新規1ファイル
- 本文書作成時点: `2026-04-30`
- コミット禁止（文書化のみ）
- `.helix/` 配下は編集しない
- 実装は PLAN-005 L3/L4 フェーズで実施
- 対象スコープ: single-host 運用前提（分散実行は対象外）

---

## 3. ユーザー意図の要約（再解釈）

1. 「自動化（cron / queue / lock / setup / observe）」を feature ごとに個別実装するのではなく横断インフラ化する。
2. PLAN-002/003 で重複したロジックを統一し、将来 PLAN-006/008/009 でもそのまま再利用できる土台を作る。
3. L3/L4 の設計・実装を進める前提として API と DB の方向を固定する。
4. 受け口は CLI。外部 daemon 統合や UI 追加は対象外。

---

## 4. 背景

現在の状態は、同一種類の機能が各機能側で異なる実装になっている。

- PLAN-002: 独自のロックと棚卸しジョブ設計
- PLAN-003: auto-restart 側のロック、ハッシュ、観測、再起動関連の独自実装
- 既存機能（将来予定含む）: cron-like、非同期、監査ログ、setup 前提の重複コード

結果として:

- 重複実装 25 通りに近い組み合わせが発生
- 挙動仕様のズレ（期限計算、リトライ、ログ形式、fail-safe）が増える
- テスト設計と migration テストの負債が増加
- PLAN-002/003 の L4 統合作業がボトルネック化

---

## 5. ゴール

### 5.1 PLAN レベルゴール

- 5 skill の API と DB スキーマを本文として確定
- `helix.db` v11 migration を前提化し、既存 v7-v10 段階の整合方針を提示
- PLAN-002 / PLAN-003 の L3 から本 PLANの API を参照できる状態にする
- 本 PLAN で実装を着手しない（skeleton と仕様に留める）

### 5.2 受入ゴール（計画目標）

- G2 まで: 要件・設計・API freeze が完了し、PLAN-002/003 から参照可能
- G3 まで: migration freeze / CLI 仕様 freeze / テスト計画 freeze
- G4 まで: 5 skill 動作確認と統合シナリオ実施
- G6 まで: PLAN-002/003 L4 実利用でエラー再発が発生しないことを確認

---

## 6. スコープ

### 6.1 含める範囲

- `automation/scheduler` skill
- `automation/job-queue` skill
- `automation/lock` skill
- `automation/init-setup` skill
- `automation/observability` skill
- 各 skill の CLI skeleton API 仕様
- `helix.db` v11 DDL 追加計画
- 監査と export の最小実装方針（実装自体は L4）

### 6.2 含めない範囲

- 外部 cron daemon / systemd timer の直接統合
- 外部監視への push ベース連携（`export` は手動）
- multi-host worker
- 実装コード（詳細アルゴリズム、例外分岐の最終実装）
- UI 追加

---

## 7. 設計方針

1. CLI の呼び出し仕様を先に固定し、実装で逸脱しない
2. `helix.db` を観測、ジョブ、スケジュール、ロック共通の状態ソースにする
3. 失敗時はログを残し `error` に集約、silent failure は許容しない
4. 権限と安全に関係する設定（lock / export / setup）は明確な reason_code を返却
5. 既存実装との整合を優先し、破壊的変更は `migration` として扱う

---

## 8. skill 1: `automation/scheduler`

### 8.1 位置付け

cron-like 定期実行 + at-time 単発を共通化。

### 8.2 追加 CLI

```bash
helix scheduler add --schedule "*/5 * * * *" --task "<type>:<payload>" [options]
helix scheduler add-at --at "+5m" --task "<type>:<payload>" [options]
helix scheduler list [--status pending|running|success|failed|cancelled|all]
helix scheduler cancel <id>
helix scheduler status <id>
helix scheduler run-due [--max <n>] [--dry-run]
```

### 8.3 オプション

- `--name`（任意）: 表示名
- `--task`（必須）: `"<type>:<payload>"`
  - 例: `helix:command:gate G3`, `shell:script:./inventory.sh`, `http:webhook:https://...`
  - サポート type: `helix:command`（Helix CLI のみ）、`shell:script`（allowlist 登録 script）、`http:webhook`（allowlist URL）
  - allowlist は `~/.config/helix/automation-allowlist.yaml`（Tier A, `$HOME` 配下, mode `0600`）から参照
  - free-form 文字列（旧形式）禁止。`type` 未定義や不正 payload は **fail-closed**
  - L3 freeze 時点で各 executor の引数 schema を固定し、`helix:command`, `shell:script`, `http:webhook` のバリデータを明記する。
    - `helix:command`: `helix <subcommand> ...` のみ許可（内部コマンド）
    - `shell:script`: allowlist の script 名のみ許可（shell 引用/リダイレクト禁止）
    - `http:webhook`: allowlist の HTTPS URL のみ許可
- `--schedule`（add）: cron または `+5m` / `+2h` 形式
- `--at`（add-at）: `2026-04-30T15:00:00Z` または `+90s`
- `--timezone`（任意）: IANA 名（例: `Asia/Tokyo`）
- `--payload`（任意）: JSON（4KB 制限）
- `--retry`（任意）: 失敗時再試行回数
- `--max-retries`（任意）: 最大再試行回数

### 8.4 想定フロー

- `add`: スケジュールを検証して DB へ保存。
- `run-due`: 期限到達を取得、排他を取得、実行、結果記録、次回時刻再計算。
- `cancel`: running を cancelled へ変更。
- `status`: 指定 id の履歴・エラー・次回実行を返す。

### 8.5 status / reason_code

- `SCHED_01`: スケジュール式不正
- `SCHED_02`: next_run_at 未算出
- `SCHED_03`: 排他ロック競合
- `SCHED_04`: 実行中ジョブが過剰
- `SCHED_05`: タイムゾーン不整合

### 8.6 DDL（schedules）

```sql
CREATE TABLE IF NOT EXISTS schedules (
  id TEXT PRIMARY KEY,
  name TEXT,
  task TEXT NOT NULL,
  schedule_expr TEXT NOT NULL,
  schedule_type TEXT NOT NULL CHECK(schedule_type IN ('cron', 'relative', 'at')),
  timezone TEXT NOT NULL DEFAULT 'UTC',
  status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
  next_run_at INTEGER NOT NULL,
  last_run_at INTEGER,
  retry_count INTEGER NOT NULL DEFAULT 0,
  max_retries INTEGER NOT NULL DEFAULT 3,
  last_error TEXT,
  payload_json TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  created_by TEXT,
  CHECK(created_at <= updated_at)
);
CREATE INDEX IF NOT EXISTS idx_schedules_status_next ON schedules(status, next_run_at);
CREATE INDEX IF NOT EXISTS idx_schedules_created_by ON schedules(created_by);
```

### 8.7 監査ルール

- `next_run_at` は UTC epoch 秒
- スケジュールは登録時に 1 回だけ `status` 検証
- `run-due` は失敗ケースもイベント化（reason を保存）

---

## 9. skill 2: `automation/job-queue`

### 9.1 位置付け

ジョブ登録・並列消化・優先度・再試行を共通化。

### 9.2 追加 CLI

```bash
helix job enqueue --task "<type>:<payload>" [--priority 1-10] [--delay <seconds>] [--id <uuid>]
helix job worker [--once] [--sleep <seconds>] [--parallel 1-4]
helix job status <id>
helix job cancel <id>
helix job retry <id>
helix job list [--status pending|running|success|failed|cancelled|all] [--limit <n>]
```

### 9.3 仕様

- `priority`: 1〜10、10 が高
- `delay`: 実行遅延秒
- `parallel`: 同時処理数（最大 4）
- `once`: run-due を1回だけ処理
- `status`: `pending` / `running` / `success` / `failed` / `cancelled`

### 9.4 期待挙動

- `enqueue` はジョブを `pending` で永続化し、`scheduled_at` を計算
- `worker` は `pending` から `running` へ遷移して実行、結果を `success/failed` へ更新
- 失敗時は `retry_count` を加算し `max_retry` に従って再キュー
- worker 再起動でも id の二重実行が起きないよう排他キーを保持

- 5値モデル（`pending / running / success / failed / cancelled`）を前提とし、`queued` / `done` / `cancel_requested` は採用しない。

### 9.5 reason_code

- `JOB_01`: task が空
- `JOB_02`: priority 範囲外
- `JOB_03`: queue overflow（上限超過）
- `JOB_04`: 再試行上限到達
- `JOB_05`: worker conflict

### 9.6 DDL（jobs）

```sql
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  task TEXT NOT NULL,
  payload_json TEXT,
  status TEXT NOT NULL CHECK(
    status IN ('pending','running','success','failed','cancelled')
  ),
  priority INTEGER NOT NULL DEFAULT 5 CHECK(priority BETWEEN 1 AND 10),
  created_at INTEGER NOT NULL,
  scheduled_at INTEGER NOT NULL,
  started_at INTEGER,
  completed_at INTEGER,
  retry_count INTEGER NOT NULL DEFAULT 0,
  max_retry INTEGER NOT NULL DEFAULT 3,
  worker_id TEXT,
  last_error TEXT,
  error_count INTEGER NOT NULL DEFAULT 0,
  locked_at INTEGER,
  CHECK(created_at <= scheduled_at),
  CHECK(scheduled_at <= COALESCE(started_at, scheduled_at)),
  CHECK(started_at <= COALESCE(completed_at, started_at))
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_priority_created ON jobs(status, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_jobs_scheduled_at ON jobs(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_jobs_worker ON jobs(worker_id);
```

### 9.7 利用シナリオ

- PLAN-002 A0 の並列分散
- PLAN-002 A1 の import retry
- PLAN-003 5% dump のジョブ化

---

## 10. skill 3: `automation/lock`

### 10.1 位置付け

排他制御を file lock と DB lock で統合。

### 10.2 追加 CLI

```bash
helix lock acquire --name <key> [--timeout <seconds>] [--scope home|project] [--ttl <seconds>] [--wait]
helix lock release --name <key> [--scope home|project] [--force]
helix lock list [--scope all|home|project] [--status pending|running|success|failed|cancelled|all]
helix lock status --name <key> [--scope home|project]
```

### 10.3 仕様

- `home`:
  - `~/.helix/locks/<key>.lock`
- `project`:
  - `.helix/locks/<key>.lock`

`acquire` では:

- ファイル lock 取得
- 競合時、timeout まで待機（`--wait` 指定時）
- オーナー確認後 DB lock へ接続（実装順序は file -> db）

`release` では:

- owner 一致を確認
- token が一致しなければ失敗

### 10.4 stale 回収

- pid 生存チェック
- lock ファイル古すぎ/期限切れを stale と判定
- 再取得時に再生

### 10.5 reason_code

- `LOCK_01`: key 文字列不正
- `LOCK_02`: timeout
- `LOCK_03`: 権限不足
- `LOCK_04`: stale detect
- `LOCK_05`: circular wait

### 10.6 DDL（locks）

```sql
CREATE TABLE IF NOT EXISTS locks (
  id TEXT PRIMARY KEY,
  lock_name TEXT NOT NULL,
  scope TEXT NOT NULL CHECK(scope IN ('home','project')),
  path TEXT NOT NULL,
  pid INTEGER,
  owner TEXT,
  host TEXT,
  acquired_at INTEGER NOT NULL,
  released_at INTEGER,
  ttl_seconds INTEGER,
  token TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('pending','running','success','failed','cancelled')),
  last_error TEXT,
  CHECK(acquired_at <= COALESCE(released_at, acquired_at))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_locks_active_name_scope
  ON locks(lock_name, scope)
  WHERE status IN ('running', 'pending');
CREATE INDEX IF NOT EXISTS idx_locks_scope_status ON locks(scope, status);
```

---

## 11. skill 4: `automation/init-setup`

### 11.1 位置付け

setup 前提を CLI で統一。

### 11.2 追加 CLI

```bash
helix setup verify --name <component>
helix setup install --name <component>
helix setup repair --name <component>
helix setup list [--status pending|running|success|failed|cancelled|all]
helix setup status [--name <component>]
```

### 11.3 前提

各 component は以下を持つ。

- `cli/setup/<name>.sh`
- `verify()` / `install()` / `repair()`
- 標準出力の JSON 形式は同一（state, message, details）

### 11.4 API 期待

- `verify` / `install` / `repair` は `pending` / `running` / `success` / `failed` / `cancelled` を返却

### 11.5 典型 component

- `gitleaks`
- `gitignore`
- `redaction_denylist`
- `helix_auto_restart`
- `auto_restart_settings`

### 11.6 DDL（setup_checks/setup_events）

```sql
CREATE TABLE IF NOT EXISTS setup_checks (
  component TEXT PRIMARY KEY,
  verify_state TEXT NOT NULL CHECK(verify_state IN ('pending', 'running', 'success', 'failed', 'cancelled')),
  installed INTEGER NOT NULL DEFAULT 0,
  last_verify_at INTEGER,
  last_install_at INTEGER,
  last_repair_at INTEGER,
  verify_error TEXT,
  install_version TEXT,
  install_path TEXT,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS setup_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  component TEXT NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('verify','install','repair')),
  status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
  outcome TEXT,
  details_json TEXT,
  created_at INTEGER NOT NULL,
  FOREIGN KEY(component) REFERENCES setup_checks(component) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_setup_events_component_created ON setup_events(component, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_setup_events_status ON setup_events(status);
```

---

## 12. skill 5: `automation/observability`

### 12.1 位置付け

構造化ログと metric を共通 DB ベースで集計。

### 12.2 追加 CLI

```bash
helix observe log --event <name> --data <json> [--component <name>] [--level info|warn|error]
helix observe metric --name <name> --value <num> [--tags k=v] [--component <name>] [--unit count|ms|bytes|percent|ratio]
helix observe report [--event <name>] [--metric <name>] [--since <time>] [--component <name>]
helix observe export --format prometheus|json [--since <time>] [--out <path>] [--include-secrets]
```

### 12.3 log API 仕様

- `event`: snake_case
- `data`: JSON（16KB）
- `component`: 任意
- `level`: `info|warn|error`
- PLAN-003 連携前提の `token` 系イベントについては
  - `input_tokens` / `output_tokens` / `total_tokens` は数値のみ保存
  - `context` 文字列は保存しない（token 計算用 transcript は保存前 redaction）

### 12.4 metric API 仕様

- `name`: snake_case
- `value`: float を許容
- `unit`: 任意
- `tags`: `k=v`（最大 20）
- `--unit` 未指定時は `count`

### 12.5 report/export

- report は集計（count / p50 / p95 / sum）を出力
- export/prometheus は `HELIX` 命名接頭辞を付与し、metric 形式に変換
- export/json は時系列情報を含む

### 12.6 reason_code

- `OBS_01`: event 名不正
- `OBS_02`: 数値変換失敗
- `OBS_03`: tags 形式エラー
- `OBS_04`: retention 超過
- `OBS_05`: export path 書込不可

### 12.7 データ取扱方針（秘匿情報境界）

- 記録時 redaction
  - `helix observe log --data` は `PLAN-002 の redaction-denylist.example/local.yaml` + 共通正規表現で redaction 適用。
  - deny-list ベースで実行し、unknown フィールドは保留扱いとする。
- trust boundary
  - `events` / `metrics` は PLAN-002 の trust boundary を継承。
  - project-local `helix.db` は mode `0600` を前提とし、HOME 配置オプションは同等制約。
- export 安全策
  - `helix observe export --format prometheus|json` は redaction 済みデータのみ export
  - `--out` 先が `~/.helix/quarantine/` 以外なら **fail-closed**
  - `--include-secrets` は PM-only 承認フロー必須（監査ログに記録）
- 主要リスク対策
  - `R-06` として、任意 JSON 経路の秘匿情報持出しリスクを明示し、L3 での redaction fixture preflight を必須化

### 12.8 retention / vacuum

- events: 90 日（超過は `VACUUM`）
- metrics: 90 日（超過は `VACUUM`）
- scheduler / job / lock の運用タスクと連携し、定期 cleanup を実施

### 12.9 DDL（events / metrics）

```sql
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  component TEXT,
  level TEXT NOT NULL CHECK(level IN ('info','warn','error')),
  data_json TEXT,
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_name_created ON events(name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_component_created ON events(component, created_at DESC);

CREATE TABLE IF NOT EXISTS metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  component TEXT,
  value REAL NOT NULL,
  unit TEXT NOT NULL DEFAULT 'count',
  tags_json TEXT,
  created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_name_created ON metrics(name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_component_created ON metrics(component, created_at DESC);
```

---

## 13. `helix.db v11`（migration 方針）

### 13.1 現状前提

- `schema_version` で現行バージョンを管理
- PLAN-002 v8、PLAN-003 v9、PLAN-004 v10 完了を前提条件とする
- 現在バージョン別の移行前提:
  - `current ≤ 7` → `v8 → v9 → v10 → v11`（PLAN 必要条件未満なら fail-closed）
  - `current = 8` → `v9 → v10 → v11`
  - `current = 9` → `v10 → v11`
  - `current = 10` → `v11 のみ`
  - `current = 11` → no-op
  - `current > 11` → fail-closed
- 本 PLAN は v11 で5テーブルを追加

### 13.2 migration 概要

- v11 へのアップグレードは `cli/lib/helix_db.py` の逐次 migration を使い順次適用
- 既存 v1-v10 は後方互換のまま再現し、ダウングレードは未実装
- migration は冪等（create-if-not-exists / insert or ignore）

### 13.3 v10→v11 追加テーブル

- `schedules`
- `jobs`
- `locks`
- `setup_checks`, `setup_events`
- `events`, `metrics`

### 13.4 v10→v11 DDL まとめ

```sql
CREATE TABLE IF NOT EXISTS schedules (...);
CREATE TABLE IF NOT EXISTS jobs (...);
CREATE TABLE IF NOT EXISTS locks (...);
CREATE TABLE IF NOT EXISTS setup_checks (...);
CREATE TABLE IF NOT EXISTS setup_events (...);
CREATE TABLE IF NOT EXISTS events (...);
CREATE TABLE IF NOT EXISTS metrics (...);
```

（各 SQL 定義は本計画 §8, §9, §10, §11, §12 を参照）

### 13.5 migration 試験方針

1. L3 rehearsal matrix: `current ≤ 10` からの up migration を必須化（7/8/9/10）
2. `current = 11` の no-op を検証
3. `current > 11` の fail-closed 検証
4. 既知の壊れ DB（legacy / schema 欠落）を使った fail-closed 確認
5. 再実行で冪等

---

## 14. `lock` と `scheduler` の安全ルール

- Acquisition order（固定）: file lock → db lock
- 既定では複数 lock 同時取得時に名前順ソート
- PID 未生存時のみ stale 判定
- スケジューラは同一 job を二重実行しない
- 5 個別 skill のデータ破壊時は他 skill への影響最小化

---

## 15. 受入ゲート

### 15.1 G1

- PM 確認（本文 freeze）

### 15.2 G2（要件）

- gate-policy §G2 準拠
- 本 PLAN 追加（5 skill API freeze）
- PLAN-002/003 の統合方針 freeze
- 各 skill SKILL.md skeleton freeze
- 主要 API / DDL への承認を得る

### 15.3 G3（要件）

- 各 skill の DDL freeze（v11）
- CLI 仕様 freeze（本 PLAN 章を変更不可）
- `helix.db` v11 migration spec freeze
- テスト計画 freeze（L3 で受け入れ）

### 15.4 G4（要件）

- 5 skill 全部の動作確認（dry 実行含む）
- PLAN-002/003 での実利用テスト（計画的な最小ケース）
- performance baseline を取得（最小指標）

### 15.5 G5

- UI がないため skip

### 15.6 G6（要件）

- PLAN-002/PLAN-003 L4 で本 skill を実利用し、再発エラーの有無を確認
- 主要ユースケースを 1 件以上実行

### 15.7 G7

- 既定どおり（通常運用）

---

## 16. PLAN-002/PLAN-003 接続（スケルトン仕様）

### 16.1 PLAN-002 からの参照

- A0 preflight: `setup verify/install/repair` を前提追加
- A1 import_runs: 再試行ジョブとして job-queue / lock 使用
- 監査ログ: observability でイベント統合

### 16.2 PLAN-003 からの参照

- 30 日 key rotation: scheduler
- 90 日 retention / vacuum: observability の retention と連動
- 5% 残量チェック: scheduler の監査で `token` 系イベント記録
- handover dump: job-queue に移管

---

## 17. リスク

### 17.1 R-01: 5 skill 同時新設

- 対策: Sprint 1 で skeleton 一括 + 以後 skill 単位で実装

### 17.2 R-02: migration 順序事故

- 対策: v10→v11 の rehearsal matrix を固定

### 17.3 R-03: 既存実装との衝突

- 対策: Sprint 4 で PLAN-002/003 との接続時に feature 側 code を段階的置換

### 17.4 R-04: API が使いにくい（過不足）

- 対策: PLAN-002/003 L3 固定前に実需レビューを実施

### 17.5 R-05: file / db lock 混在

- 対策: acquisition order の固定と循環検出テストを必須化

### 17.6 R-06: observability の任意 JSON 経路が秘匿情報持ち出し経路になり得る

- 対策: §12.7（データ取扱方針）を適用し、記録時 redaction + trust boundary + export redaction だけを許可

### 17.7 R-07: link drift

- 対策: 本PLANの末尾で参照リンクを固定し、定期チェック（docs link check）を実施

---

## 18. Sprint 構成（L4）

- **Sprint 1**
  - `helix.db` v11 migration 下地
  - 5 skill SKILL.md skeleton
  - CLI skeleton（空実装）追加
- **Sprint 2**
  - lock: file + db lock
  - stale detect、テスト
- **Sprint 3**
  - scheduler: cron parse + run-due
- **Sprint 4**
  - job-queue: FIFO, priority, retry
- **Sprint 5**
  - init-setup: verify / install / repair
- **Sprint 6**
  - observability: events/metrics/report/export
- **Sprint 7**
  - 統合: PLAN-002, PLAN-003 から実利用

---

## 19. テスト観点（L3 freeze の前提）

- lock:
  - stale reclaim
  - 同名重複取得拒否
  - acquisition order
- scheduler:
  - cron/relative/at-time 解析
  - run-due の再試行
  - next_run 再計算
- job-queue:
  - priority order
  - delay, retry, worker並列
  - cancel/retry
  - task 実行モデル（`type:payload`）のパースと allowlist fail-closed
  - status フィルタの 5 値固定
- init-setup:
  - component verify/repair 成否
  - スクリプト未存在時の reason_code
- observability:
  - event/metric record
  - report summary
  - export json/prometheus
- migration:
  - current 列に対する v11 up テスト（v7/8/9/10/11/>11）
  - 冪等
  - fail-closed

---

## 20. 受入判定チェックリスト（最終）

- [ ] 5 skill の CLI/API 仕様が記載済み
- [ ] DDL と migration 方針が明確
- [ ] 各 skill のエラーコードが明示済み
- [ ] PLAN-002/003 参照接続点が明示済み
- [ ] task 実行モデルと allowlist, fail-closed 仕様が固定済み
- [ ] 5値 status の CLI/filter/DDL CHECK 制約が全 skill で一致済み
- [ ] G1〜G7 の受け入れ条件定義済み

---

## 21. 受入済み変更履歴

2026-04-30 | v2 | TLレビュー反映（P1: observability データ境界、P2: task実行モデル・migration前提、P3: status列挙統一）
2026-04-30 | v1 | 初版: 5 shared infra skills の PLAN レベル本文を新規作成

---

## 22. 参照リンク

- [PLAN-002-helix-inventory-foundation.md](PLAN-002-helix-inventory-foundation.md)
- [PLAN-003-auto-restart-foundation.md](PLAN-003-auto-restart-foundation.md)
- [docs/design/D-DB-MIGRATION.md](../design/D-DB-MIGRATION.md)
- [docs/design/D-HOOK-SPEC.md](../design/D-HOOK-SPEC.md)
- [docs/design/L2-cli-architecture.md](../design/L2-cli-architecture.md)
- [docs/design/D-STATE-SPEC.md](../design/D-STATE-SPEC.md)

---

## 23. 未完了項目の残存確認

- この版: 未完了なし
- 今後（PLAN-005 L3 以降）: `cli/lib/tests/` 追加テスト設計、`docs/research` 系観測値の反映
