# HELIX-workflows v2 物理データ設計（L5）

本文書は `L5-helix-workflows-データ詳細設計plan` の `§2.1 doc 構造 candidate` と
`docs/v2/L4-architecture/helix-workflows-functional-design.md`（特に §6.4/§7.4/§8.4/§9.4/§10.4）を
起点に、`pmo-sonnet inventory` 対象 12 table の物理 schema を凍結する。

- Plan reference: `docs/plans/L5/L5-helix-workflows-データ詳細設計plan.md`
- Scope: `v15`/`v35`/`v36` までの既存実装 + 12 table への L5 carry を一体化
- Schema version source of truth: `cli/lib/helix_db.py` の `SCHEMA` と `CURRENT_SCHEMA_VERSION`
- 補助: `cli/lib/migrations/v35_plan_registry.py`（実行中 `plan_registry` 系）

本文書は **既存列名変更禁止** を守るため、既存実装テーブル（`skill_usage`）は現存列のみを採用。

## §0 PLAN reference + scope 宣言

### 0.1 扱う対象

対象 table（C-01〜C-12）:

1. `event_log`
2. `plan_registry`
3. `skill_usage`
4. `mode_transition`
5. `role_audit`
6. `metrics_log`
7. `plan_history`
8. `version_tag`
9. `obsolete_record`
10. `coexist_config`
11. `version_coevolution`
12. `audit_link`

実装状態は `implemented / partial / planned` を保持。

### 0.2 取り扱いルール

- まず read-only で `sqlite3 .helix/helix.db ".schema"` を取得し、実 DB 存在時は実在 schema を参照。
- 現在 `.helix/helix.db` は `helix_db.py` と `v35/v36` 系 migration が反映済みを前提とし、
  対象 12 table は本設計で追加/確定する。
- 実装段階では `schema_version` の後退禁止。
- 破壊変更は `2-stage approval`（approve flag + rollback manifest）を必須とする。

## §1 helix.db 全体方針

### §1.1 SQLite 採用理由

1. 単ファイル化（`helix.db`）で handover/CI/セッション間の移行コストを最小化。
2. hook と CLI 実行の競合を想定し、`WAL` + `busy timeout` で並列実行耐性を確保。
3. 監査証跡（event / metric / trace / migration）を SQL で集約し、
   `.helix/audit/*.yaml` と cross check 可能。
4. `sqlite3` CLI が標準で可搬性高く、運用監査や runbook から再現しやすい。

### §1.2 schema_version table 運用方針

#### 1.2.1 管理方式

- `PRAGMA user_version` は現時点の参照用とし、実状態は `schema_version` テーブルを真実源とする。
- 仕様上の schema version は `CURRENT_SCHEMA_VERSION`（現時点 `36`）を起点。
- migration module は `v31`〜`v35` と本体 `SCHEMA` を混在運用。

#### 1.2.2 ADR-019（履歴）との整合（参照）

本設計では ADR 参照系決定（ADR-019 を含む）に従い、
失敗時は `schema_version` 値をロールバックせず、
追加 migration を idempotent 方式で段階追加する。

### §1.3 backup / restore 戦略

1. 作業前に `sqlite3 .backup`/`cp -p` で `backup_manifest_path` を残す。
2. migration 実行前に以下を最小セットとして保存:
   - `schema_version`
   - 対象 table row count
   - `PRAGMA integrity_check`
3. rollback 時は `backup_manifest_path` を参照し、
   `restore + 監査 YAML 差分差分` を取る。

## §2 既存 implemented table 物理 schema

この章は現時点で実体が確認できる 6 テーブルを採用状態で記載する。

### §2.1 event_log (CREATE TABLE 完全 DDL + index)

#### 2.1.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS event_log (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now','utc')),
    event_type TEXT NOT NULL,
                   -- cli_command / hook_fired / gate_judged / plan_status_changed / sprint_step_checked
    plan_id TEXT,
    session_id TEXT,
    actor TEXT NOT NULL,
                   -- "cli:<subcommand>" / "hook:<hook_name>" / "pmo-sonnet" / "codex-se" など
    actor_role TEXT,
    trace_id TEXT,
    idempotency_key TEXT,
    result TEXT,
                   -- pass / fail / blocked / skipped
    message TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    event_sha256 TEXT,
    schema_version INTEGER NOT NULL DEFAULT 36,
    source_component TEXT,
    source_node TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 2.1.2 column 説明（1 行）

- `event_id`: 事件キー（append-only）
- `timestamp`: 発生時刻（UTC）
- `event_type`: イベント分類
- `plan_id`: PLAN 参照キー
- `session_id`: セッション識別子
- `actor`: 発火主体
- `actor_role`: 発火主体ロール
- `trace_id`: 監査 trace の親キー
- `idempotency_key`: 同一処理再送時の抑制キー
- `result`: 判定結果
- `message`: 1 行要約
- `metadata_json`: 追加情報
- `event_sha256`: payload integrity 用 digest
- `schema_version`: 発生時点の schema
- `source_component`: 送出 component
- `source_node`: 送出ノード
- `created_at`: 永続化時刻

#### 2.1.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_log_event_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_plan_id ON event_log(plan_id);
CREATE INDEX IF NOT EXISTS idx_event_log_session_id ON event_log(session_id);
CREATE INDEX IF NOT EXISTS idx_event_log_actor ON event_log(actor);
CREATE INDEX IF NOT EXISTS idx_event_log_result ON event_log(result);
CREATE INDEX IF NOT EXISTS idx_event_log_created_at ON event_log(created_at);
CREATE INDEX IF NOT EXISTS idx_event_log_trace_id ON event_log(trace_id);
CREATE INDEX IF NOT EXISTS idx_event_log_sid_type ON event_log(session_id, event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_plan_ts ON event_log(plan_id, created_at DESC);
```

#### 2.1..4 FK 設定

- `plan_id` → `plan_registry(plan_id)`（存在する場合）
  - on delete: `SET NULL`（履歴保持）
- `event_id` は `audit_link`/`metrics_log`/`obsolete_record` から参照される想定
  - on delete: `SET NULL`

#### 2.1.5 想定 row 数 + 増加率

- 想定: `1.5k/日`（既存チーム）
- 推定増加率: 週次稼働比で 5〜10% / 30日
- retention 方針: §8.1 参照（90日推奨、監査保全分は延長）

#### 2.1.6 代表 query（5-10）

```sql
SELECT event_type, COUNT(*) AS c FROM event_log WHERE date(timestamp)=date('now') GROUP BY event_type;
SELECT * FROM event_log WHERE plan_id=? ORDER BY created_at DESC LIMIT 50;
SELECT session_id, COUNT(*) FROM event_log WHERE result='fail' AND created_at >= datetime('now','-7 day') GROUP BY session_id;
SELECT event_type, AVG(CAST(json_extract(metadata_json,'$.duration_ms') AS REAL)) FROM event_log WHERE event_type='gate_judged' GROUP BY event_type;
SELECT e.event_id, m.metric_name FROM event_log e LEFT JOIN metrics_log m ON m.source_event_id=e.event_id WHERE e.event_type='hook_fired' AND m.sampled_at>datetime('now','-1 day');
SELECT plan_id, COUNT(*) FROM event_log WHERE created_at >= datetime('now','-30 day') AND result!='pass' GROUP BY plan_id ORDER BY COUNT(*) DESC;
SELECT event_sha256, COUNT(*) FROM event_log WHERE event_sha256 IS NOT NULL GROUP BY event_sha256 HAVING COUNT(*)>1;
SELECT actor, COUNT(*) FROM event_log WHERE timestamp >= datetime('now','-90 day') GROUP BY actor ORDER BY COUNT(*) DESC LIMIT 20;
```

### §2.2 plan_registry (CREATE TABLE 完全 DDL + index)

#### 2.2.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS plan_registry (
    plan_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    layer TEXT NOT NULL,
    drive TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    size TEXT,
    owner TEXT,
    related_adr TEXT,
    frontmatter_json TEXT NOT NULL,
    doc_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

#### 2.2.2 column 説明

- `plan_id`: PLAN 識別子
- `title`: PLAN タイトル
- `kind`: PLAN kind
- `layer`: 工程レイヤ（L0-L14）
- `drive`: ドライブ識別子
- `status`: `draft/review/in_progress/completed` 等
- `size`: サイズ種別（任意）
- `owner`: オーナー
- `related_adr`: 参照 ADR
- `frontmatter_json`: frontmatter 全文の JSON
- `doc_path`: DOC の path
- `created_at`: 作成時刻
- `updated_at`: 更新時刻

#### 2.2.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_plan_registry_status ON plan_registry(status);
CREATE INDEX IF NOT EXISTS idx_plan_registry_kind ON plan_registry(kind);
CREATE INDEX IF NOT EXISTS idx_plan_registry_layer ON plan_registry(layer);
CREATE INDEX IF NOT EXISTS idx_plan_registry_drive ON plan_registry(drive);
CREATE INDEX IF NOT EXISTS idx_plan_registry_owner ON plan_registry(owner);
CREATE INDEX IF NOT EXISTS idx_plan_registry_updated_at ON plan_registry(updated_at);
```

#### 2.2.4 FK 設定

- 自表の子テーブルは以下で参照:
  - `plan_dependencies.plan_id` → `plan_registry(plan_id)`（CASCADE）
  - `sprint_progress.plan_id` → `plan_registry(plan_id)`（CASCADE）
  - 本章外の `plan_dependencies`, `plan_agent_slots`, `plan_generates`, `plan_references` と整合

#### 2.2.5 想定 row 数 + 増加率

- 想定: `2000/年`
- 増加率: 大型 session で月 100〜300

#### 2.2.6 代表 query

```sql
SELECT status, COUNT(*) FROM plan_registry GROUP BY status;
SELECT plan_id, title, updated_at FROM plan_registry WHERE status='in_progress' ORDER BY updated_at DESC;
SELECT owner, COUNT(*) AS n FROM plan_registry GROUP BY owner ORDER BY n DESC;
SELECT plan_id, title FROM plan_registry WHERE kind='L5' AND layer='L5' AND status='in_progress';
SELECT plan_id, json_extract(frontmatter_json,'$.dependencies') AS deps FROM plan_registry WHERE json_valid(frontmatter_json) AND json_extract(frontmatter_json,'$.dependencies') IS NOT NULL;
```

### §2.3 skill_usage (CREATE TABLE 完全 DDL + index)

#### 2.3.1 CREATE TABLE（既存列名維持）

```sql
CREATE TABLE IF NOT EXISTS skill_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_text TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    references_used TEXT,
    agent_used TEXT,
    match_score REAL,
    match_reason TEXT,
    outcome TEXT,
    user_feedback TEXT,
    result_stdout TEXT,
    result_stderr TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

#### 2.3.2 column 説明

- `id`: 行キー
- `task_text`: 対象タスク本文
- `skill_id`: 呼び出し skill
- `references_used`: 参照情報（text）
- `agent_used`: 実行エージェント
- `match_score`: 適合スコア
- `match_reason`: 理由
- `outcome`: 成否
- `user_feedback`: フィードバック
- `result_stdout`: 標準出力保存
- `result_stderr`: 標準エラー出力保存
- `created_at`: 作成時刻
- `completed_at`: 完了時刻

#### 2.3.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_skill_usage_skill ON skill_usage(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_usage_outcome ON skill_usage(outcome);
CREATE INDEX IF NOT EXISTS idx_skill_usage_agent ON skill_usage(agent_used);
CREATE INDEX IF NOT EXISTS idx_skill_usage_created_at ON skill_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_skill_usage_match_score ON skill_usage(match_score);
```

#### 2.3.4 FK 設定

- 現実装上、外部 FK 未設定。
- 推奨: 将来 `plan_id` を追加して `plan_registry` を参照（現在は追加しない）。

#### 2.3.5 想定 row 数 + 増加率

- 想定: `3k/月`
- 増加率: usage 需要に比例し月 1.2〜1.6 倍

#### 2.3.6 代表 query

```sql
SELECT skill_id, COUNT(*) AS n FROM skill_usage GROUP BY skill_id ORDER BY n DESC;
SELECT outcome, COUNT(*) FROM skill_usage WHERE created_at >= datetime('now','-30 day') GROUP BY outcome;
SELECT skill_id, AVG(match_score) FROM skill_usage WHERE match_score IS NOT NULL GROUP BY skill_id HAVING COUNT(*)>=10;
SELECT agent_used, COUNT(*) FROM skill_usage WHERE outcome='fail' GROUP BY agent_used;
SELECT * FROM skill_usage WHERE task_text LIKE '%mutation%' ORDER BY created_at DESC LIMIT 20;
```

### §2.4 mode_transition (partial)

#### 2.4.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS mode_transition (
    transition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    mode_from TEXT NOT NULL,
    mode_to TEXT NOT NULL,
    mode_to_close TEXT,
    event_id INTEGER,
    payload_yaml TEXT,
    payload_sha256 TEXT,
    transition_result TEXT NOT NULL DEFAULT 'closed',
    evidence_path TEXT,
    closure_state TEXT NOT NULL DEFAULT 'closed',
    started_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    closed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 2.4.2 column 説明

- `transition_id`: 9 mode 遷移キー
- `plan_id`: 対象 PLAN
- `mode_from`: 開始 mode
- `mode_to`: 終了先 mode
- `mode_to_close`: 閉塞 mode
- `event_id`: event_log 連携キー
- `payload_yaml`: closure payload
- `payload_sha256`: payload integrity
- `transition_result`: 実行結果
- `evidence_path`: audit YAML path
- `closure_state`: close 状態
- `started_at`: 開始時刻
- `closed_at`: 終了時刻
- `created_at`: 監査登録時刻

#### 2.4.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_mode_transition_plan_id ON mode_transition(plan_id);
CREATE INDEX IF NOT EXISTS idx_mode_transition_from_to ON mode_transition(mode_from, mode_to);
CREATE INDEX IF NOT EXISTS idx_mode_transition_result ON mode_transition(transition_result);
CREATE INDEX IF NOT EXISTS idx_mode_transition_started_at ON mode_transition(started_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mode_transition_trace ON mode_transition(plan_id, mode_from, mode_to, started_at);
```

#### 2.4.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`：`CASCADE`
- `event_id` → `event_log(event_id)`：`SET NULL`

#### 2.4.5 想定 row 数 + 増加率

- 想定: `100/年`
- 増加率: 運用期間に比例し `+20%/四半期`

#### 2.4.6 代表 query

```sql
SELECT plan_id, mode_from, mode_to, transition_result FROM mode_transition WHERE created_at>=datetime('now','-14 day') ORDER BY created_at DESC;
SELECT mode_to, COUNT(*) FROM mode_transition WHERE transition_result='closed' GROUP BY mode_to;
SELECT plan_id, COUNT(*) FROM mode_transition GROUP BY plan_id HAVING COUNT(*)>3 ORDER BY COUNT(*) DESC;
SELECT transition_id FROM mode_transition WHERE closure_state='closed' AND closed_at IS NULL;
```

### §2.5 role_audit (partial)

#### 2.5.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS role_audit (
    role_audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_actor TEXT NOT NULL,
    to_actor TEXT NOT NULL,
    from_role TEXT NOT NULL,
    to_role TEXT NOT NULL,
    plan_id TEXT,
    artifact_id TEXT,
    handover_id TEXT,
    from_session_id TEXT,
    to_session_id TEXT,
    delegation_cmd TEXT,
    reason TEXT,
    decision TEXT,
    compliance_json TEXT,
    risk_level TEXT DEFAULT 'medium',
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 2.5.2 column 説明

- `role_audit_id`: 監査キー
- `from_actor`: 送出者
- `to_actor`: 受信者
- `from_role`: 送出ロール
- `to_role`: 受信ロール
- `plan_id`: 対象 PLAN
- `artifact_id`: 対象 artifact
- `handover_id`: handover 紐付け
- `from_session_id`: 送出 session
- `to_session_id`: 受信 session
- `delegation_cmd`: 委譲コマンド
- `reason`: 理由
- `decision`: 承認結果
- `compliance_json`: 監査 JSON
- `risk_level`: リスクレベル
- `created_at`: 記録時刻

#### 2.5.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_role_audit_from_actor ON role_audit(from_actor);
CREATE INDEX IF NOT EXISTS idx_role_audit_to_actor ON role_audit(to_actor);
CREATE INDEX IF NOT EXISTS idx_role_audit_plan_id ON role_audit(plan_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_roles ON role_audit(from_role, to_role);
CREATE INDEX IF NOT EXISTS idx_role_audit_handover_id ON role_audit(handover_id);
CREATE INDEX IF NOT EXISTS idx_role_audit_created_at ON role_audit(created_at);
```

#### 2.5.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`：`SET NULL`
- `role_audit_id` は `mode_transition` / `audit_link` が参照可

#### 2.5.5 想定 row 数 + 増加率

- 想定: `100/年`
- 増加率: 委譲回数に比例し `+15%/q`

#### 2.5.6 代表 query

```sql
SELECT from_actor, to_actor, COUNT(*) FROM role_audit GROUP BY from_actor, to_actor ORDER BY COUNT(*) DESC;
SELECT plan_id, decision, COUNT(*) FROM role_audit WHERE decision='approved' GROUP BY plan_id, decision;
SELECT handover_id FROM role_audit WHERE decision='rejected' AND created_at>=datetime('now','-7 day');
SELECT from_role, to_role, risk_level, COUNT(*) FROM role_audit GROUP BY from_role, to_role, risk_level;
```

### §2.6 audit_link (partial)

#### 2.6.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS audit_link (
    audit_link_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_artifact_type TEXT NOT NULL,
    from_artifact_id TEXT NOT NULL,
    to_artifact_type TEXT NOT NULL,
    to_artifact_id TEXT NOT NULL,
    link_type TEXT NOT NULL DEFAULT 'references',
                   -- references / supports / validates / supersedes / deprecates
    weight REAL DEFAULT 1.0,
    valid_from TEXT NOT NULL DEFAULT (datetime('now','utc')),
    valid_until TEXT,
    event_id INTEGER,
    role_audit_id INTEGER,
    version INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 2.6.2 column 説明

- `audit_link_id`: リンクキー
- `from_artifact_type`: 発信系統
- `from_artifact_id`: 発信 ID
- `to_artifact_type`: 受信系統
- `to_artifact_id`: 受信 ID
- `link_type`: リンク種別
- `weight`: 参照重要度
- `valid_from`: 有効開始
- `valid_until`: 有効終了
- `event_id`: event 連携
- `role_audit_id`: 委譲監査連携
- `version`: スキーマバージョン
- `is_active`: 生存フラグ
- `created_at`: 作成時刻

#### 2.6.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_audit_link_from_artifact ON audit_link(from_artifact_type, from_artifact_id);
CREATE INDEX IF NOT EXISTS idx_audit_link_to_artifact ON audit_link(to_artifact_type, to_artifact_id);
CREATE INDEX IF NOT EXISTS idx_audit_link_type ON audit_link(link_type);
CREATE INDEX IF NOT EXISTS idx_audit_link_active ON audit_link(is_active);
CREATE INDEX IF NOT EXISTS idx_audit_link_event_id ON audit_link(event_id);
CREATE INDEX IF NOT EXISTS idx_audit_link_role_audit_id ON audit_link(role_audit_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_link_pair ON audit_link(from_artifact_type, from_artifact_id, to_artifact_type, to_artifact_id, link_type);
```

#### 2.6.4 FK 設定

- `event_id` → `event_log(event_id)`（`SET NULL`）
- `role_audit_id` → `role_audit(role_audit_id)`（`SET NULL`）

#### 2.6.5 想定 row 数 + 増加率

- 想定: `800/四半期`
- 増加率: trace 追加により `+10~20%/四半期`

#### 2.6.6 代表 query

```sql
SELECT from_artifact_type, to_artifact_type, COUNT(*) FROM audit_link GROUP BY from_artifact_type, to_artifact_type;
SELECT * FROM audit_link WHERE from_artifact_type='PLAN' AND from_artifact_id=? AND is_active=1;
SELECT to_artifact_id FROM audit_link WHERE link_type='validates' AND to_artifact_type='event_log' ORDER BY created_at DESC;
SELECT from_artifact_id, to_artifact_id FROM audit_link WHERE event_id IS NOT NULL;
```

## §3 新規 planned table 物理 schema（F6-F10）

### §3.1 metrics_log (F6 homeostasis)

#### 3.1.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS metrics_log (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT,
    metric_name TEXT NOT NULL,
                   -- context_usage_ratio / workspace_size_mb / codex_token_consumption / parallel_count など
    metric_scope TEXT NOT NULL DEFAULT 'global',
    metric_unit TEXT,
    metric_value REAL NOT NULL,
    dimension_json TEXT,
    source TEXT DEFAULT 'collector',
    measured_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    window_start TEXT,
    window_end TEXT,
    session_id TEXT,
    source_event_id INTEGER,
    run_id TEXT,
    is_derived INTEGER DEFAULT 0,
    source_role TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 3.1.2 column 説明

- `metric_id`: 指標キー
- `plan_id`: 対象 PLAN（任意）
- `metric_name`: 指標名
- `metric_scope`: global / plan / session / function
- `metric_unit`: 単位
- `metric_value`: 値
- `dimension_json`: 多次元ラベル
- `source`: 収集元
- `measured_at`: 測定時刻
- `window_start`: 集計窓開始
- `window_end`: 集計窓終了
- `session_id`: セッション
- `source_event_id`: event 参照
- `run_id`: homeostasis run 識別子
- `is_derived`: 集計値フラグ
- `source_role`: 収集ロール
- `created_at`: 永続化時刻

#### 3.1.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics_log(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_plan_scope ON metrics_log(plan_id, metric_scope);
CREATE INDEX IF NOT EXISTS idx_metrics_measured_at ON metrics_log(measured_at);
CREATE INDEX IF NOT EXISTS idx_metrics_session_id ON metrics_log(session_id);
CREATE INDEX IF NOT EXISTS idx_metrics_source_role ON metrics_log(source_role);
CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics_log(run_id);
CREATE INDEX IF NOT EXISTS idx_metrics_derived ON metrics_log(is_derived);
```

#### 3.1.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`：`SET NULL`
- `source_event_id` → `event_log(event_id)`：`SET NULL`

#### 3.1.5 想定 row 数 + 増加率

- 想定: `12k/月`
- 増加率: homeostasis 導入後 `+120%`、週次で平準化

#### 3.1.6 代表 query（6）

```sql
SELECT metric_name, AVG(metric_value) AS avg_v FROM metrics_log WHERE measured_at >= datetime('now','-7 day') GROUP BY metric_name;
SELECT metric_name, MAX(metric_value) FROM metrics_log WHERE measured_at >= datetime('now','-1 day') GROUP BY metric_name;
SELECT * FROM metrics_log WHERE metric_name='context_usage_ratio' AND measured_at >= datetime('now','-24 hour') ORDER BY measured_at DESC LIMIT 200;
SELECT session_id, COUNT(*) FROM metrics_log WHERE metric_scope='session' GROUP BY session_id ORDER BY COUNT(*) DESC LIMIT 20;
SELECT metric_name, AVG(metric_value) FROM metrics_log WHERE is_derived=1 GROUP BY metric_name;
SELECT plan_id, metric_name, MAX(metric_value) FROM metrics_log WHERE metric_name='parallel_count' AND plan_id IS NOT NULL GROUP BY plan_id;
```

### §3.2 plan_history (F7 evolution)

#### 3.2.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS plan_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    prev_version TEXT,
    next_version TEXT,
    mutation_type TEXT NOT NULL DEFAULT 'fork',
    source_mode TEXT,
    score REAL,
    gate_pass_rate REAL,
    diff_summary TEXT,
    parent_plan_id TEXT,
    actor TEXT,
    cause TEXT,
    decision_json TEXT,
    event_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    effective_from TEXT,
    effective_to TEXT,
    promoted_at TEXT,
    deprecated_at TEXT,
    status TEXT NOT NULL DEFAULT 'active'
);
```

#### 3.2.2 column 説明

- `history_id`: 履歴キー
- `plan_id`: 対象 PLAN
- `prev_version`: 前バージョン
- `next_version`: 次バージョン
- `mutation_type`: fork / mutate / promote / deprecate / archive
- `source_mode`: 進化トリガ
- `score`: 評価スコア
- `gate_pass_rate`: gate 通過率
- `diff_summary`: 変更要約
- `parent_plan_id`: 親 PLAN
- `actor`: 操作者
- `cause`: 原因
- `decision_json`: decide 判定
- `event_id`: event 連動
- `created_at`: 作成時刻
- `effective_from/to`: 適用期間
- `promoted_at`: promote 時刻
- `deprecated_at`: 非推奨時刻
- `status`: active/superseded/deprecated

#### 3.2.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_plan_history_plan_id ON plan_history(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_history_status ON plan_history(status);
CREATE INDEX IF NOT EXISTS idx_plan_history_mutation ON plan_history(mutation_type);
CREATE INDEX IF NOT EXISTS idx_plan_history_created_at ON plan_history(created_at);
CREATE INDEX IF NOT EXISTS idx_plan_history_event_id ON plan_history(event_id);
CREATE INDEX IF NOT EXISTS idx_plan_history_prev_next ON plan_history(prev_version, next_version);
```

#### 3.2.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`：`SET NULL`
- `parent_plan_id` → `plan_registry(plan_id)`：`SET NULL`
- `event_id` → `event_log(event_id)`：`SET NULL`

#### 3.2.5 想定 row 数 + 増加率

- 想定: `150/月`
- 増加率: evolve cycle 活性化時 `+25%/q`

#### 3.2.6 代表 query

```sql
SELECT plan_id, mutation_type, status, COUNT(*) FROM plan_history GROUP BY plan_id, mutation_type, status;
SELECT plan_id, MAX(score) FROM plan_history WHERE mutation_type='promote' GROUP BY plan_id;
SELECT mutation_type, COUNT(*) FROM plan_history WHERE created_at>=datetime('now','-30 day') GROUP BY mutation_type;
SELECT * FROM plan_history WHERE status='pending' ORDER BY created_at ASC;
SELECT parent_plan_id, COUNT(*) FROM plan_history WHERE parent_plan_id IS NOT NULL GROUP BY parent_plan_id;
```

### §3.3 version_tag (F8 reproduction)

#### 3.3.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS version_tag (
    version_tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL DEFAULT 'helix-db',
    artifact_name TEXT,
    version_semver TEXT,
    version_code INTEGER,
    migration_id TEXT,
    migration_sql_hash TEXT,
    schema_version INTEGER,
    checksum TEXT NOT NULL,
    release_notes_path TEXT,
    migration_status TEXT NOT NULL DEFAULT 'planned',
    is_required INTEGER DEFAULT 0,
    is_breaking INTEGER DEFAULT 0,
    from_version_tag_id INTEGER,
    plan_id TEXT,
    snapshot_path TEXT,
    rollback_manifest_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    applied_at TEXT,
    owner TEXT,
    approved_by TEXT,
    notes TEXT
);
```

#### 3.3.2 column 説明

- `version_tag_id`: バージョンキー
- `artifact_id`: 対象アーティファクト ID
- `artifact_type`: `helix-db` / `plan` / `portable` 等
- `artifact_name`: 対象名
- `version_semver`: semver
- `version_code`: 数値表現
- `migration_id`: migration 識別子
- `migration_sql_hash`: migration スクリプト hash
- `schema_version`: 適用 schema version
- `checksum`: 整合ハッシュ
- `release_notes_path`: release notes
- `migration_status`: planned/applied/failed/rollback
- `is_required`: 必須更新フラグ
- `is_breaking`: breaking change フラグ
- `from_version_tag_id`: 前版リンク
- `plan_id`: 関連 plan
- `snapshot_path`: snapshot path
- `rollback_manifest_path`: rollback evidence（必要）
- `created_at`: 作成時刻
- `applied_at`: 適用時刻
- `owner`: 申請者
- `approved_by`: 承認者
- `notes`: 補足

#### 3.3.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_version_tag_artifact ON version_tag(artifact_id, artifact_type);
CREATE INDEX IF NOT EXISTS idx_version_tag_status ON version_tag(migration_status);
CREATE INDEX IF NOT EXISTS idx_version_tag_semver ON version_tag(version_semver);
CREATE INDEX IF NOT EXISTS idx_version_tag_created_at ON version_tag(created_at);
CREATE INDEX IF NOT EXISTS idx_version_tag_is_breaking ON version_tag(is_breaking);
CREATE INDEX IF NOT EXISTS idx_version_tag_plan_id ON version_tag(plan_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_version_tag_artifact_version ON version_tag(artifact_id, artifact_type, version_semver);
```

#### 3.3.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`（SET NULL）
- `from_version_tag_id` → `version_tag(version_tag_id)`（SET NULL）

#### 3.3.5 想定 row 数 + 増加率

- 想定: `20/年`
- 増加率: migration 発生時に集中（発生月のみ急増）

#### 3.3.6 代表 query

```sql
SELECT artifact_type, migration_status, COUNT(*) FROM version_tag GROUP BY artifact_type, migration_status;
SELECT artifact_id, MAX(version_code) FROM version_tag GROUP BY artifact_id;
SELECT * FROM version_tag WHERE is_breaking=1 AND migration_status='applied';
SELECT * FROM version_tag WHERE migration_status='planned' ORDER BY created_at;
```

### §3.4 obsolete_record (F9 apoptosis)

#### 3.4.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS obsolete_record (
    obsolete_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_type TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    plan_id TEXT,
    obsolete_reason TEXT NOT NULL,
    approved_by TEXT,
    approved_at TEXT,
    actor TEXT,
    dry_run_batch_id TEXT,
    retention_policy TEXT,
    evidence_json TEXT,
    replacement_artifact_id TEXT,
    rollback_manifest_path TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    detected_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    executed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 3.4.2 column 説明

- `obsolete_id`: 廃止キー
- `artifact_type`: PLAN / event_log / metrics_log / audit_link / skill_usage
- `artifact_id`: 対象 ID
- `plan_id`: 関連 PLAN
- `obsolete_reason`: 廃止理由
- `approved_by`: 承認者
- `approved_at`: 承認時刻
- `actor`: 実行者
- `dry_run_batch_id`: dry-run 紐付け
- `retention_policy`: policy タグ
- `evidence_json`: 廃止証拠
- `replacement_artifact_id`: 置換先
- `rollback_manifest_path`: rollback manifest
- `status`: pending/approved/executed/failed/reverted
- `detected_at`: 発見時刻
- `executed_at`: 実施時刻
- `created_at`: 作成時刻

#### 3.4.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_obsolete_status ON obsolete_record(status);
CREATE INDEX IF NOT EXISTS idx_obsolete_artifact ON obsolete_record(artifact_type, artifact_id);
CREATE INDEX IF NOT EXISTS idx_obsolete_plan_id ON obsolete_record(plan_id);
CREATE INDEX IF NOT EXISTS idx_obsolete_detected_at ON obsolete_record(detected_at);
CREATE INDEX IF NOT EXISTS idx_obsolete_actor ON obsolete_record(actor);
```

#### 3.4.4 FK 設定

- `plan_id` → `plan_registry(plan_id)`（SET NULL）

#### 3.4.5 想定 row 数 + 増加率

- 想定: `30/四半期`
- 増加率: clean ルーチン成熟で `+30%/q`

#### 3.4.6 代表 query

```sql
SELECT status, COUNT(*) FROM obsolete_record GROUP BY status;
SELECT artifact_type, COUNT(*) FROM obsolete_record WHERE status='pending' GROUP BY artifact_type;
SELECT artifact_id, obsolete_reason FROM obsolete_record WHERE approved_by IS NULL AND created_at>=datetime('now','-7 day');
SELECT * FROM obsolete_record WHERE dry_run_batch_id IS NOT NULL ORDER BY created_at DESC LIMIT 50;
```

### §3.5 coexist_config (F10 symbiosis)

#### 3.5.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS coexist_config (
    coexist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    namespace TEXT NOT NULL,
    framework_name TEXT NOT NULL,
    framework_version TEXT,
    adapter_name TEXT,
    compatibility_level TEXT NOT NULL DEFAULT 'low',
    acl_enabled INTEGER NOT NULL DEFAULT 1,
    acl_entrypoint TEXT,
    namespace_conflict_policy TEXT DEFAULT 'reject',
    acceptance_status TEXT DEFAULT 'draft',
    compatibility_adr_id TEXT,
    boundary_contract_json TEXT,
    input_schema_json TEXT,
    output_schema_json TEXT,
    error_semantics_json TEXT,
    namespace_map_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    actor TEXT,
    status TEXT NOT NULL DEFAULT 'active'
);
```

#### 3.5.2 column 説明

- `coexist_id`: 共生キー
- `namespace`: 名前空間
- `framework_name`: framework 名
- `framework_version`: framework バージョン
- `adapter_name`: adapter 名
- `compatibility_level`: low/medium/high/blocked
- `acl_enabled`: ACL 有効フラグ
- `acl_entrypoint`: ACL entrypoint
- `namespace_conflict_policy`: 衝突時処理
- `acceptance_status`: draft/active/revoked
- `compatibility_adr_id`: 互換 ADR
- `boundary_contract_json`: boundary 契約
- `input_schema_json`: 入力 schema
- `output_schema_json`: 出力 schema
- `error_semantics_json`: エラー約束
- `namespace_map_json`: name mapping
- `created_at`: 作成時刻
- `updated_at`: 更新時刻
- `actor`: 更新者
- `status`: 実効状態

#### 3.5.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_coexist_namespace ON coexist_config(namespace);
CREATE INDEX IF NOT EXISTS idx_coexist_framework ON coexist_config(framework_name);
CREATE INDEX IF NOT EXISTS idx_coexist_compatibility_level ON coexist_config(compatibility_level);
CREATE INDEX IF NOT EXISTS idx_coexist_acceptance_status ON coexist_config(acceptance_status);
CREATE INDEX IF NOT EXISTS idx_coexist_status ON coexist_config(status);
CREATE INDEX IF NOT EXISTS idx_coexist_adr ON coexist_config(compatibility_adr_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_coexist_namespace_framework ON coexist_config(namespace, framework_name, framework_version);
```

#### 3.5.4 FK 設定

- 将来: `compatibility_adr_id` → `plan_registry(plan_id)`（`SET NULL`）
- 将来: `namespace` 同一 namespace の競合検知はユニークインデックスで代替（重複拒否）

#### 3.5.5 想定 row 数 + 増加率

- 想定: `40/年`
- 増加率: `+10%/q` 程度（採用 project 追加に伴う）

#### 3.5.6 代表 query

```sql
SELECT framework_name, compatibility_level, COUNT(*) FROM coexist_config GROUP BY framework_name, compatibility_level;
SELECT * FROM coexist_config WHERE acceptance_status='active' AND acl_enabled=1 ORDER BY updated_at DESC;
SELECT namespace, framework_name FROM coexist_config WHERE status='active';
SELECT compatibility_adr_id, COUNT(*) FROM coexist_config GROUP BY compatibility_adr_id;
```

### §3.6 version_coevolution (F8 co-evolution audit)

#### 3.6.1 CREATE TABLE

```sql
CREATE TABLE IF NOT EXISTS version_coevolution (
    version_coevolution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    upstream_version_tag_id INTEGER NOT NULL,
    downstream_version_tag_id INTEGER NOT NULL,
    upstream_node TEXT NOT NULL,
    downstream_node TEXT NOT NULL,
    coevolution_type TEXT NOT NULL DEFAULT 'fork_merge',
    policy_json TEXT,
    resolution_strategy TEXT,
    source_type TEXT DEFAULT 'manual',
    actor TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    trigger_event_id INTEGER,
    audit_link_id INTEGER,
    started_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    finished_at TEXT,
    rollback_manifest_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now','utc')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

#### 3.6.2 column 説明

- `version_coevolution_id`: 共進化キー
- `upstream_version_tag_id`: 上流バージョン
- `downstream_version_tag_id`: 下流バージョン
- `upstream_node`: 上流ノード
- `downstream_node`: 下流ノード
- `coevolution_type`: fork_merge / parallel_adopt / reconciliation / backport
- `policy_json`: 方針
- `resolution_strategy`: 解決戦略
- `source_type`: manual/auto/ci
- `actor`: 実行者
- `status`: running/blocked/ok/reverted
- `trigger_event_id`: トリガイベント
- `audit_link_id`: audit 参照
- `started_at`: 開始時刻
- `finished_at`: 終了時刻
- `rollback_manifest_path`: rollback evidence path（重要）
- `created_at`: 作成時刻
- `updated_at`: 更新時刻

#### 3.6.3 CREATE INDEX

```sql
CREATE INDEX IF NOT EXISTS idx_version_coevolution_status ON version_coevolution(status);
CREATE INDEX IF NOT EXISTS idx_version_coevolution_upstream ON version_coevolution(upstream_version_tag_id);
CREATE INDEX IF NOT EXISTS idx_version_coevolution_downstream ON version_coevolution(downstream_version_tag_id);
CREATE INDEX IF NOT EXISTS idx_version_coevolution_nodes ON version_coevolution(upstream_node, downstream_node);
CREATE INDEX IF NOT EXISTS idx_version_coevolution_trigger ON version_coevolution(trigger_event_id);
CREATE INDEX IF NOT EXISTS idx_version_coevolution_actor ON version_coevolution(actor);
```

#### 3.6.4 FK 設定

- `upstream_version_tag_id` → `version_tag(version_tag_id)`（`CASCADE`）
- `downstream_version_tag_id` → `version_tag(version_tag_id)`（`CASCADE`）
- `trigger_event_id` → `event_log(event_id)`（`SET NULL`）
- `audit_link_id` → `audit_link(audit_link_id)`（`SET NULL`）

#### 3.6.5 想定 row 数 + 増加率

- 想定: `10/四半期`
- 増加率: 上流/下流採用増加で `+15%/q`

#### 3.6.6 代表 query

```sql
SELECT status, COUNT(*) FROM version_coevolution GROUP BY status;
SELECT upstream_node, downstream_node, coevolution_type FROM version_coevolution WHERE status='running';
SELECT upstream_version_tag_id, downstream_version_tag_id FROM version_coevolution WHERE finished_at IS NULL AND status='running';
SELECT actor, COUNT(*) FROM version_coevolution GROUP BY actor ORDER BY COUNT(*) DESC;
```

## §4 index 戦略

### §4.1 一覧（table × index）

| テーブル | index | 用途 |
|---|---|---|
| event_log | idx_event_log_timestamp / _event_type / _plan_id / _session_id / _actor / _result / _created_at / _trace_id / _sid_type / _plan_ts | 時系列検索・監査横断 |
| plan_registry | idx_plan_registry_status / _kind / _layer / _drive / _owner / _updated_at | plan 分類・状態参照 |
| skill_usage | idx_skill_usage_skill / _outcome / _agent / _created_at / _match_score | 推奨性能・品質分析 |
| mode_transition | idx_mode_transition_plan_id / _from_to / _result / _started_at / uq_mode_transition_trace | 9 mode closure 追跡 |
| role_audit | idx_role_audit_from_actor / _to_actor / _plan_id / _roles / _handover_id / _created_at | 委譲監査 |
| audit_link | idx_audit_link_from_artifact / _to_artifact / _type / _active / _event_id / _role_audit_id / uq_audit_link_pair | 双方向 trace |
| metrics_log | idx_metrics_name / _plan_scope / _measured_at / _session_id / _source_role / _run_id / _derived | homeostasis 取得 |
| plan_history | idx_plan_history_plan_id / _status / _mutation / _created_at / _event_id / _prev_next | 進化履歴 |
| version_tag | idx_version_tag_artifact / _status / _semver / _created_at / _is_breaking / _plan_id / uq_version_tag_artifact_version | バージョン移行 |
| obsolete_record | idx_obsolete_status / _artifact / _plan_id / _detected_at / _actor | apoptosis 管理 |
| coexist_config | idx_coexist_namespace / _framework / _compatibility_level / _acceptance_status / _status / _adr / uq_coexist_namespace_framework | ACL 管理 |
| version_coevolution | idx_version_coevolution_status / _upstream / _downstream / _nodes / _trigger / _actor | 共進化監査 |

合計 index/partial unique 目安: `35+`

### §4.2 covering index

以下の covering index は集計 query を高速化する。

- `event_log`: `CREATE INDEX idx_event_log_plan_ts ON event_log(plan_id, created_at DESC)`
- `metrics_log`: `CREATE INDEX idx_metrics_plan_name_time ON metrics_log(plan_id, metric_name, measured_at)`
- `plan_history`: `CREATE INDEX idx_plan_history_plan_status ON plan_history(plan_id, status, created_at DESC)`
- `version_tag`: `CREATE INDEX idx_version_tag_art_plan ON version_tag(artifact_type, artifact_id, migration_status)`
- `obsolete_record`: `CREATE INDEX idx_obsolete_status_created ON obsolete_record(status, created_at DESC)`

### §4.3 unique constraint

以下は logical uniqueness を担保する。意図的に `version_tag` と `audit_link` は厳密重複禁止。

- `uq_plan_registry_plan_id`: `plan_id`（PK）
- `uq_mode_transition_trace`: `(plan_id, mode_from, mode_to, started_at)`
- `uq_audit_link_pair`: `(from_artifact_type, from_artifact_id, to_artifact_type, to_artifact_id, link_type)`
- `uq_version_tag_artifact_version`: `(artifact_id, artifact_type, version_semver)`
- `uq_coexist_namespace_framework`: `(namespace, framework_name, framework_version)`

## §5 FK 設計

### §5.1 FK 一覧

1. `mode_transition.plan_id` → `plan_registry.plan_id` (`CASCADE`)
2. `mode_transition.event_id` → `event_log.event_id` (`SET NULL`)
3. `role_audit.plan_id` → `plan_registry.plan_id` (`SET NULL`)
4. `audit_link.event_id` → `event_log.event_id` (`SET NULL`)
5. `audit_link.role_audit_id` → `role_audit.role_audit_id` (`SET NULL`)
6. `metrics_log.plan_id` → `plan_registry.plan_id` (`SET NULL`)
7. `metrics_log.source_event_id` → `event_log.event_id` (`SET NULL`)
8. `plan_history.plan_id` → `plan_registry.plan_id` (`SET NULL`)
9. `plan_history.parent_plan_id` → `plan_registry.plan_id` (`SET NULL`)
10. `plan_history.event_id` → `event_log.event_id` (`SET NULL`)
11. `version_tag.plan_id` → `plan_registry.plan_id` (`SET NULL`)
12. `version_tag.from_version_tag_id` → `version_tag.version_tag_id` (`SET NULL`)
13. `version_coevolution.upstream_version_tag_id` → `version_tag.version_tag_id` (`CASCADE`)
14. `version_coevolution.downstream_version_tag_id` → `version_tag.version_tag_id` (`CASCADE`)
15. `version_coevolution.trigger_event_id` → `event_log.event_id` (`SET NULL`)
16. `version_coevolution.audit_link_id` → `audit_link.audit_link_id` (`SET NULL`)
17. `obsolete_record.plan_id` → `plan_registry.plan_id` (`SET NULL`)

### §5.2 CASCADE 戦略

- `CASCADE`:
  - バージョン体系の一貫削除（`version_tag` 系）
  - `plan_registry` のライフサイクルで消滅する計画の副産物（mode_transition 等）
- `SET NULL`:
  - 監査証跡を残しつつ参照先が残っても履歴可観測を保つ
  - `event_log` / `plan` 削除時の監査断絶防止
- `RESTRICT`:
 - 本章では運用上不採用（将来、`plan_registry` を根幹の保護対象にした場合のみ検討）

## §6 migration script

### §6.1 schema_version v<N> → v<N+1> migration template

```python
def up(conn):
    conn.execute("PRAGMA foreign_keys = ON")
    # idempotent
    conn.executescript(EVENT_LOG_SCHEMA)
    conn.executescript(METRICS_LOG_SCHEMA)
    conn.executescript(PLAN_HISTORY_SCHEMA)
    conn.execute("INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, datetime('now','utc'))", (37,))
    conn.commit()

def down(conn):
    # rollback は destructive 検討が必要。1-stage only で明示実行。
    conn.execute("DROP TABLE IF EXISTS metrics_log")
    conn.execute("DROP TABLE IF EXISTS plan_history")
```

テンプレート実行順:

1. `SCHEMA` 追加
2. INDEX 作成（`IF NOT EXISTS`）
3. `schema_version` 更新
4. `integrity` / `pragma foreign_keys=ON` / `pragma quick_check`

### §6.2 destructive migration の人間承認境界

以下は直近 1 スイッチで承認必須（破壊変更）。

- `DROP TABLE`
- カラム型変更（整数/実数の型差し替え）
- null 制約変更・主キー/一意制約の厳格化
- データの暗黙集約（`metrics`/`event` 廃止）

### §6.3 backward compat 1 stage + breaking change cap

- 1-release に 1 回まで schema bump。
- 旧 version table は後方互換読み取りを保証（vN-1 → vN）。
- breaking change は `BREAKING.md` と `--approved` を必須とする。

## §7 rollback strategy

### §7.1 dry-run + backup manifest

#### 7.1.1 dry-run

`migration preview` は `ALTER` 前に以下を提示。

```sql
SELECT name FROM sqlite_master WHERE type='table' AND name IN (...);
SELECT COUNT(*) AS row_count FROM <target_table>;
```

#### 7.1.2 backup manifest

`schema_version` 変更時の manifest を `.helix/audit/migration-YYYYMMDD.yaml` に記録。
必須キー:

- target_db
- from_version
- to_version
- changed_sql
- backup_path
- checksums
- pre_checks
- post_checks

### §7.2 rollback evidence 連動

`obsolete_record.rollback_manifest_path` へ保存し、
`audit_link` と `event_log` の関連で追跡。

```sql
CREATE INDEX IF NOT EXISTS idx_version_tag_rollback_manifest ON version_tag(rollback_manifest_path);
CREATE INDEX IF NOT EXISTS idx_obsolete_rollback_manifest ON obsolete_record(rollback_manifest_path);
```

## §8 retention policy

### §8.1 event_log retention

- 基準: 90 日（ADR-045 §2.1）
- 例外: 監査で `is_protected=1`（保留実装）を持つ行は 1 年まで保持
- 実装: 月次ジョブで chunk delete（`created_at` フィルタ + 監査保護フラグ）

### §8.2 metrics_log retention

- raw: 30 日
- aggregate: 1 年（daily / weekly の集約）
- 集約計画:
  - `raw` → `daily_metrics_agg`（将来 table）
  - もしくは `is_derived=1` テーブル内保存で兼用

### §8.3 plan_history retention

- `plan_history` は原則永続
- `obsolescence` に伴う状態遷移のみ保持
- `status='obsolete'` かつ `executed_at` 120 日以上は別 archive file へ出力

## §9 セキュリティ

### §9.1 file permission

- 本体 DB は `umask 0600` を推奨（read/write owner only）。
- `.helix/audit/*.yaml` も同一準拠。
- 実行ユーザ検査: migration ログに `os.getuid()/git user` を残す。

### §9.2 secret column 取り扱い

- 現状、12 table に `secret` 専有列は未配置。
- 将来 `compliance` / `coexist` で認証情報を保存する場合:
  1. 平文非保存（token hash / envelope encryption）
  2. `violation` 時は `NULL` 埋め + 参照用別 file
  3. `event_log` に masking 前提を明示し監査時再現を保つ

## §10 4 artifact 双方向 trace

### §10.1 Plan / ADR / metric / event の 4 artifact map

| from → to | table / col | index | 補足 |
|---|---|---|---|
| PLAN → event | `plan_registry.plan_id` → `event_log.plan_id` | `idx_event_log_plan_id` | 計画履歴連携 |
| event → metric | `event_log.event_id` → `metrics_log.source_event_id` | `idx_metrics_plan_scope` | 監査連動指標 |
| metric → plan_history | `metrics_log.metric_name` + 集計結果 → `plan_history.decision_json` | `idx_plan_history_created_at` | F7 promote 判定材料 |
| mode_transition → plan_registry | `mode_transition.plan_id` → `plan_registry.plan_id` | `idx_mode_transition_plan_id` | 9 mode 成果 |
| role_audit → audit_link | `role_audit.role_audit_id` → `audit_link.role_audit_id` | `idx_audit_link_role_audit_id` | 委譲 trace |

### §10.2 event / artifact 逆参照例

```sql
SELECT e.event_id, p.plan_id, a.from_artifact_id, a.to_artifact_id
FROM event_log e
LEFT JOIN audit_link a ON a.event_id = e.event_id
LEFT JOIN plan_registry p ON p.plan_id = e.plan_id
WHERE e.timestamp >= datetime('now','-7 day');
```

### §10.3 ADR 追跡

- 本設計は `ADR-044`（構造・永続化）と `ADR-045`（F6-F10 governance）を参照。
- 特に `version_tag` と `obsolete_record` の `rollback_manifest_path` は ADR-045 決定の証拠キー。

## §11 implementation_status 表（12 table）

| table | status | 根拠 |
|---|---|---|
| event_log | implemented (planned) | `PLAN-143` 由来、v37 想定、L5 にて物理 DDL 固定 |
| plan_registry | implemented (partial) | v35 migration 実装あり + 本書で index 補強 |
| skill_usage | implemented (partial) | `helix_db.py` 実装列固定 |
| mode_transition | partial | 設計定義はあるが CLI/実装の追加が必要 |
| role_audit | implemented (partial) | 委譲監査の骨格あり、F5 機能拡張予定 |
| audit_link | partial | ADR-044 §6.8 補完対象を含め L5 化 |
| metrics_log | planned | ADR-045 Decision-1 と F6 実装 carry |
| plan_history | planned | ADR-045 Decision-3 carry |
| version_tag | planned | ADR-045 Decision-4 carry |
| obsolete_record | planned | ADR-045 Decision-2 carry |
| coexist_config | planned | ADR-045 Decision-5 carry |
| version_coevolution | planned | F8 上下流 parallel coevolution の新規監査テーブル（U-08） |
| audit_link | partial | 4 artifact trace 監査基盤として実装継続 |

**注:** `audit_link` は上記でも触れるため、C-12 で「partial→implemented」化を明示。

## §12 ADR-044 §6.8「11 table」retrofit 提案（C-01〜C-12）

### §12.1 U-08 明記

- `version_coevolution` は本 ADR で新規追加し、ADR-045 F8（reproduction + migration order）を補強する。
- `ADR-044 §6.8` に対して、`12 table` へ拡張し 
  - C-12: `version_coevolution` を追加し、`version_tag` の上下流 coevolution 監査を明文化。
- 併せて `rollback_manifest_path` を `version_tag / obsolete_record / version_coevolution` で標準化。

### §12.2 U-09 Retrofit 表

| C-ID | table | 現在 status | ADR-044 retrofit 行動 |
|---|---|---|---|
| C-01 | event_log | implemented | audit-link trace と idempotency 追加を維持 |
| C-02 | plan_registry | implemented | v35 schema 維持 + L5 固定 view |
| C-03 | skill_usage | implemented(partial) | drift 回避のため列固定 |
| C-04 | mode_transition | partial | 9 mode closure event との完全整合を追加 |
| C-05 | role_audit | implemented(partial) | 委譲 chain の FK を保全 |
| C-06 | metrics_log | planned | F6 homeostasis の持続監視 table |
| C-07 | plan_history | planned | promote/degenerative fork 履歴 |
| C-08 | version_tag | planned | migration + rollback evidence を追加 |
| C-09 | obsolete_record | planned | apoptosis / autophagy 監査証跡 |
| C-10 | coexist_config | planned | ADR-045 DDD ACL + namespace 管理 |
| C-11 | version_coevolution | planned | F8 上下流 PR 並走監査 |
| C-12 | audit_link | partial | 4 artifact 双方向 trace と保全 |

### §12.3 監査 evidence への mapping

各 table は以下 evidence file へ接続される。

- `event_log`: `.helix/audit/event-log-YYYYMMDD.yaml`
- `metrics_log`: `.helix/audit/homeostasis-YYYYMMDD.yaml`
- `mode_transition`: `.helix/audit/mode-transition-YYYYMMDD.yaml`
- `obsolete_record`: `.helix/audit/apoptosis-YYYYMMDD.yaml`
- `version_tag`: `.helix/audit/migration-YYYYMMDD.yaml`

## 付録 A: 追加補助 DDL（設計上の前提）

### A.1 PRAGMA / vacuum / integrity

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA auto_vacuum = INCREMENTAL;
```

### A.2 統計 SQL テンプレート

```sql
SELECT name, tbl_name, sql FROM sqlite_master WHERE type='table' AND name LIKE '%_log' OR name LIKE '%plan%' OR name LIKE '%audit%';
SELECT m.name, p."seq" AS fk_count FROM sqlite_master m LEFT JOIN pragma_foreign_key_list(m.name) p WHERE m.type='table';
```

### A.3 セーフガード SQL

```sql
SELECT table_name, sql FROM sqlite_master WHERE type='table' AND sql LIKE '%CREATE TABLE%plan_registry%';
SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('event_log','metrics_log','plan_history','version_tag');
```

