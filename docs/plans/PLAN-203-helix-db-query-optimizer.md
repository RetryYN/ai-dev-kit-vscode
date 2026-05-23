---
plan_id: PLAN-203
title: "PLAN-203: helix.db query optimizer (slow query 検出・EXPLAIN QUERY PLAN 出力)"
kind: impl
layer: L4
drive: db
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
created: "2026-05-23"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — cli/lib/query_profiler.py + DB API wrapper + slow_queries テーブル統合"
  - role: pmo-sonnet
    slot_label: "PMO — helix.db 既存接続コードとの整合・重複 wrapper チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — wrapper 挿入方針・CI fail-close 閾値・WAL 既存設定との競合評価"
generates:
  - artifact_path: docs/plans/PLAN-203-helix-db-query-optimizer.md
    artifact_type: design_doc
  - artifact_path: cli/lib/query_profiler.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_query_profiler.py
    artifact_type: test
  - artifact_path: cli/helix-db
    artifact_type: cli_extension
dependencies:
  parent: null
  requires:
    - PLAN-092
  blocks: []
related_plans:
  - PLAN-092 (helix.db schema + PostToolUse 自動登録 — DB 接続初期化の正本)
  - PLAN-188 (distributed lock framework — WAL / busy_timeout 設定の共存確認)
test_design: docs/v2/L4-test-design/PLAN-203-unit-test-design.md (別 session 起票予定)
---

# PLAN-203: helix.db query optimizer

> **位置付け**: helix.db テーブル数 70+ で slow query リスクが増大している。
> DB API wrapper で実行時間を計測し、>100ms を WARN・>1s を CI fail-close で検出する。
> `helix db slow-queries` CLI で最適化候補を可視化する。

## 1. 目的

1. **slow query 検出**: DB API wrapper で全クエリの実行時間を自動計測
2. **EXPLAIN QUERY PLAN 出力**: 閾値超過時に最適化ヒントを自動取得
3. **`helix db slow-queries` CLI**: 蓄積ログを時系列・頻度で可視化
4. **CI fail-close**: >1s クエリが存在する場合に CI を fail させる

## 2. 背景

テーブル数 70+ で slow query を検出する手段がなく、性能劣化に気づけない。
対象: `cli/lib/helix_db.py` / `cli/lib/plan_registry.py` 等の全 execute() 呼び出し。

## 3. 設計方針

### 3.1 DB API wrapper

`cli/lib/query_profiler.py` に `ProfiledConnection` クラスを実装する。
既存 `sqlite3.Connection` をラップし、`execute()` を計測付きでオーバーライド。

```python
class ProfiledConnection:
    """sqlite3.Connection をラップし、クエリ実行時間を計測する。"""

    WARN_THRESHOLD_MS = 100
    FAIL_THRESHOLD_MS = 1000

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        start = time.perf_counter()
        cursor = self._conn.execute(sql, params)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self._record(sql, elapsed_ms)
        return cursor

    def _record(self, sql: str, elapsed_ms: float) -> None:
        """slow_queries テーブルへ INSERT し、閾値に応じて WARN ログを出力する。"""
        ...
```

オプトイン方式: `HELIX_PROFILE_QUERIES=1` 環境変数が設定された場合のみ wrapper 有効。
デフォルト off で通常運用への影響ゼロを保証する。

### 3.2 helix.db slow_queries テーブル

```sql
CREATE TABLE IF NOT EXISTS slow_queries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sql_hash    TEXT NOT NULL,   -- sha256 prefix 8 chars
    sql_text    TEXT NOT NULL,
    elapsed_ms  REAL NOT NULL,
    explain_out TEXT,            -- EXPLAIN QUERY PLAN の出力
    recorded_at TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

EXPLAIN QUERY PLAN は elapsed_ms > WARN_THRESHOLD_MS の場合のみ実行し
`explain_out` に格納する。

### 3.3 `helix db slow-queries` CLI

```bash
helix db slow-queries               # 直近 50 件を elapsed_ms 降順で表示
helix db slow-queries --since 1h    # 直近 1 時間のみ
helix db slow-queries --since 24h --min-ms 500   # 500ms 超過を抽出
helix db slow-queries --explain     # explain_out カラムも表示
helix db slow-queries --ci          # >1s が 1 件でも存在すれば exit 1 (CI 用)
```

既存 `cli/helix-db` の `slow-queries` サブコマンドとして追加する。

### 3.4 CI fail-close 統合

```bash
# .helix/gate-check.sh または helix test 内に追加
HELIX_PROFILE_QUERIES=1 helix db slow-queries --ci
```

>1s クエリが存在 → exit 1 → G4 ゲートで fail-close。

## 4. 実装 Sprint

### Sprint .1 (se): query_profiler.py 実装

Entry: PLAN-092 完了確認 / helix.db 存在確認

1. `cli/lib/query_profiler.py`: `ProfiledConnection` + `HELIX_PROFILE_QUERIES` opt-in
2. slow_queries テーブル migration 追加 (idempotent)
3. EXPLAIN QUERY PLAN 取得ロジック実装
4. `python3 -m py_compile cli/lib/query_profiler.py` PASS

### Sprint .2 (se): CLI + CI fail-close

Entry: Sprint .1 PASS

1. `cli/helix-db` に `slow-queries` サブコマンド (list / --since / --min-ms / --explain / --ci)
2. `bash -n cli/helix-db` PASS
3. `--ci` フラグ: >1s レコードで exit 1

### Sprint .3 (pmo-sonnet + tl-advisor): テスト + G4

Entry: Sprint .2 PASS

1. `test_query_profiler.py` 5 シナリオ: opt-in off / fast (< 100ms) / slow (100〜999ms) + explain_out / very slow (>= 1s) + --ci exit 1 / 動的 timestamp (datetime.now(timezone.utc))
2. pmo-sonnet: 既存接続コードとの整合確認
3. tl-advisor: G4 凍結判定

Exit: pytest 全 PASS + 全回帰 PASS + G4 passed

## 5. DoD

- [ ] `cli/lib/query_profiler.py` 実装済み (`ProfiledConnection` + opt-in env)
- [ ] slow_queries テーブル: 閾値超過時に INSERT + explain_out 格納確認
- [ ] `helix db slow-queries` サブコマンド動作確認 (list / --since / --ci)
- [ ] `--ci` フラグ: >1s レコードで exit 1 確認
- [ ] `test_query_profiler.py` 5 シナリオ全 PASS
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 / tl-advisor G4 passed

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-203-helix-db-query-optimizer.md |
| ② 実装コード | 未着手 | cli/lib/query_profiler.py / cli/helix-db |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-203-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_query_profiler.py |

双方向 reference: 本 PLAN → PLAN-092 (requires)。
実装コード → 本 PLAN: docstring に `# 契約: PLAN-203 §3` を明示 (実装時)。

## 7. risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| wrapper オーバーヘッドで全クエリ遅延 | 通常運用の性能劣化 | `HELIX_PROFILE_QUERIES=1` opt-in、デフォルト off |
| slow_queries テーブル肥大化 | DB ファイルサイズ増大 | `--since` で定期 purge CLI 提供 (P2 carry) |
| EXPLAIN QUERY PLAN の頻発 | 追加 I/O オーバーヘッド | WARN 閾値 (100ms) 超過時のみ実行 |
| PLAN-188 WAL 設定との競合 | busy_timeout 二重設定 | helix_db.py の接続初期化で一元管理 (P1 確認) |

## 8. 関連リンク

| 文書 | パス |
|---|---|
| PLAN-092 (helix.db schema 正本) | docs/plans/PLAN-092-helix-db-schema-posttooluse.md |
| PLAN-188 (distributed lock + WAL) | docs/plans/PLAN-188-distributed-lock-framework.md |
