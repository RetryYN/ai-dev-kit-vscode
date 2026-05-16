---
plan_id: PLAN-080
doc_id: PLAN-080-unit-test-design
title: "PLAN-080 単体テスト設計 (harness_monitor helper)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-080 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-080-harness-dynamic-monitoring.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§13 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-080-integration-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB EXT §13) と ④ テストコード
> (`cli/lib/tests/test_harness_monitor_unit.py`) を双方向 trace で繋ぐ独立文書。

# PLAN-080 単体テスト設計 (harness_monitor helper)

> 目的: PLAN-080 の `cli/lib/harness_monitor.py` に実装される helper 群を、SQLite 実 DB と最小限のモックに分離して検証する単体テストを設計する。`harness_monitor` は event audit と status 集計の核であり、入力検証、FK 整合、集計境界、時間窓の扱いを個別に押さえる。

## §1 位置付け (HELIX V-model テストピラミッド)

```
        E2E (L6 / CLI 全体・手動 watch)
       /          \
      / Integration \  ← PLAN-080 integration-test-design.md
     /______________\
    /                \
   /   Unit tests     \  ← 本設計の対象 (harness_monitor helper)
  /____________________\
```

PLAN-080 は `harness_check_events` の記録と参照を L4 で進めるが、`record_event()` / `get_active_status()` / `get_session_audit()` / `list_recent_events()` は純粋関数ではなく DB 境界を持つ。そのため、本書では `helix.db` の fresh SQLite を使い、外部 I/O だけを局所的に切り離す。

**HELIX V-model 整合性**:

- L3 詳細設計: D-DB EXT §13 `harness_check_events`
- L4 実装: `cli/lib/harness_monitor.py`
- **L4 テスト設計: 本書**
- L4 テスト実装: `cli/lib/tests/test_harness_monitor_unit.py`
- G4: 単体 + 結合 + 既存回帰 + `helix doctor` 影響なし

### 1.1 4 artifact 双方向 trace

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §13 `harness_check_events` |
| ② 実装コード | L4 実装 | `cli/lib/harness_monitor.py` |
| ③ テスト設計 | L4 設計 | `docs/v2/L4-test-design/PLAN-080-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_harness_monitor_unit.py` |

### 1.2 工程整合

| 層 | 整合内容 | 本書での扱い |
|---|---|---|
| L3 | D-DB EXT §13 の table / helper / filter 条件 | trace 固定 |
| L4 | helper 実装と unit test 実装 | `harness_monitor.py` と `test_harness_monitor_unit.py` を結ぶ |
| G4 | 実装凍結ゲート | 26 case を全通させる前提で設計 |

### 1.3 テスト対象の境界

- 対象: `harness_monitor` helper の挙動
- 非対象: `cli/helix-harness` の CLI 表示整形、hook 自動化、SessionStart / PreToolUse 連携、Phase 2 の push 通知
- 例外: `related_slot_id` の FK 整合だけは D-DB EXT §13 の data integrity の一部として unit で検証する

## §2 対象関数 × case 設計

### 2.1 `record_event(event_kind, severity='info', session_id=None, related_slot_id=None, related_plan_id=None, related_wbs_id=None, metric_value=None, detail=None, payload=None) -> int`

**対象設計 (① D-DB)**: D-DB EXT §13.2 schema / §13.4 validation / §13.6 index  
**実装ファイル (② D-IMPL)**: `cli/lib/harness_monitor.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_harness_monitor_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-HM-EVENT-001 | event_kind=slot_overflow, severity=warning | event id(int) を返す | `datetime('now')` 固定 |
| U-HM-EVENT-002 | event_kind=session_summary, severity=info | event id(int) を返す | `datetime('now')` 固定 |
| U-HM-EVENT-003 | event_kind=invalid | CHECK 違反で失敗 | なし |
| U-HM-EVENT-004 | severity=critical | CHECK 違反で失敗 | なし |
| U-HM-EVENT-005 | severity の空文字 | ValueError か CHECK 失敗 | なし |
| U-HM-EVENT-006 | payload に不正 JSON 文字列 | JSON 検証失敗 | なし |
| U-HM-EVENT-007 | payload に dict 相当 JSON 文字列 | 正常保存し payload を検証可能 | DB row 確認 |
| U-HM-EVENT-008 | related_slot_id の FK 不整合 | IntegrityError | 実 INSERT |

### 2.2 `get_active_status(session_id=None) -> dict`

**対象設計 (① D-DB)**: D-DB EXT §13.3 summary query / §13.6 index  
**実装ファイル (② D-IMPL)**: `cli/lib/harness_monitor.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_harness_monitor_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-HM-STAT-001 | session_id=None | 全 session の active 集計を返す | DB fixture |
| U-HM-STAT-002 | session_id=現セッション | 対象 session のみ集計 | DB fixture |
| U-HM-STAT-003 | session_id=存在しない値 | 空集計または既定形 | DB fixture |
| U-HM-STAT-004 | active 件数 0 | 0 件の状態を返す | DB fixture |
| U-HM-STAT-005 | active 件数が複数 severity 混在 | severity 別内訳が崩れない | DB fixture |
| U-HM-STAT-006 | session_id の空文字 | ValueError | なし |

### 2.3 `get_session_audit(session_id) -> dict`

**対象設計 (① D-DB)**: D-DB EXT §13.3 session summary / §13.5 audit projection  
**実装ファイル (② D-IMPL)**: `cli/lib/harness_monitor.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_harness_monitor_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-HM-AUDIT-001 | session_id=既存 session | summary dict を返す | DB fixture |
| U-HM-AUDIT-002 | session 内に info/warning/error 混在 | severity 集計が正しい | DB fixture |
| U-HM-AUDIT-003 | session 内に event_kind 複数種 | kind 別件数が正しい | DB fixture |
| U-HM-AUDIT-004 | session_id=None | TypeError or ValueError | なし |
| U-HM-AUDIT-005 | session_id=空文字 | ValueError | なし |
| U-HM-AUDIT-006 | session に event が 0 件 | 空 summary または既定形 | DB fixture |

### 2.4 `list_recent_events(days=7, severity=None) -> list[dict]`

**対象設計 (① D-DB)**: D-DB EXT §13.3 time window / §13.6 index  
**実装ファイル (② D-IMPL)**: `cli/lib/harness_monitor.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_harness_monitor_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-HM-LIST-001 | days=7, severity=None | 直近 7 日の全 event を返す | DB fixture |
| U-HM-LIST-002 | days=1, severity=warning | warning のみ返す | DB fixture |
| U-HM-LIST-003 | days=0 | 当日分のみ or 拒否を仕様固定 | DB fixture |
| U-HM-LIST-004 | days=-1 | ValueError | なし |
| U-HM-LIST-005 | days が大値 | 上限内で正常に絞り込む | DB fixture |
| U-HM-LIST-006 | severity=invalid | ValueError | なし |

### 2.5 case 数集計

| 関数 | case 数 |
|---|---|
| record_event | 8 |
| get_active_status | 6 |
| get_session_audit | 6 |
| list_recent_events | 6 |
| **合計** | **26 cases** |

## §3 fixture / mock 戦略

### 3.1 DB fixture

- `helix.db` は temp dir 上に fresh SQLite を作る
- `migrate_all` を実行して `harness_check_events` と `agent_slots` を有効化する
- Flask は使わない
- 可能なら `sqlite3.connect` を本物で使い、モックは時間固定と外部例外のみに限定する

### 3.2 時刻固定

- `datetime('now')` は monkey-patch で固定する
- `created_at` / 集計 window / audit summary の判定を同じ固定時刻に揃える
- recent window の境界値は 6 日 23 時間 59 分 / 7 日 / 7 日 1 分 を必ず通す

### 3.3 FK / 整合性

- `related_slot_id` は実 INSERT で存在確認する
- 不整合値は SQLite の FK 失敗として検証する
- `session_id` は plan / slot と独立した audit key として扱い、NULL 許容範囲を設計どおりに確認する

### 3.4 mock 方針

| 対象 | 方針 | 理由 |
|---|---|---|
| `datetime('now')` | monkey-patch | 境界値再現のため |
| `sqlite3.IntegrityError` | 実例外 or 最小 mock | FK 不整合の固定 |
| DB cursor / connection | 実 DB 優先、必要時だけ spy | helper の SQL 断面を保持 |
| `harness_monitor.py` 内 helper 相互 | 原則 mock しない | 単体の意味を壊さない |

### 3.5 アンチパターン

- integration test を unit 化して流用するのは NG
- helper 本体を mock してケースだけ通すのは NG
- spy なしで戻り値だけ見るのは NG

## §4 DoD (受入条件)

- [ ] 本書の 26 cases を `cli/lib/tests/test_harness_monitor_unit.py` で全実装する
- [ ] case ID が test docstring で参照される
- [ ] `migrate_all` + fresh SQLite で再現可能
- [ ] `related_slot_id` の FK 不整合を unit で検証する
- [ ] `list_recent_events()` の days 境界が固定される
- [ ] `record_event()` の `event_kind` / `severity` / `payload` 検証が固定される
- [ ] `helix doctor` に影響しない
- [ ] 既存 integration / regression の挙動を壊さない

## §5 4 artifact 双方向 trace 表

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §13 |
| ② 実装コード | L4 実装 | `cli/lib/harness_monitor.py` |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-080-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_harness_monitor_unit.py` |

### 5.1 trace ルール

- D-DB EXT §13 の helper 名と case ID を 1:1 で追えるようにする
- `record_event()` の case は `U-HM-EVENT-*`
- `get_active_status()` の case は `U-HM-STAT-*`
- `get_session_audit()` の case は `U-HM-AUDIT-*`
- `list_recent_events()` の case は `U-HM-LIST-*`

### 5.2 Next Action

1. 本書を基準に `cli/lib/tests/test_harness_monitor_unit.py` を作成する
2. `migrate_all` を使う fixture を共通化する
3. `related_slot_id` FK と days 境界の case を先に固める
4. integration test 設計と相互に trace を確認する
