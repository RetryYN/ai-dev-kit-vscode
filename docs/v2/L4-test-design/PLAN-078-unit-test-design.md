---
plan_id: PLAN-078
doc_id: PLAN-078-unit-test-design
title: "PLAN-078 単体テスト設計 (agent_slots helper)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-078 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-078-agent-slot-management.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§10 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-078-integration-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB EXT §10) と ④ テストコード
> (cli/lib/tests/test_agent_slots_unit.py) を双方向 trace で繋ぐ独立文書。

# PLAN-078 単体テスト設計 (agent_slots helper)

> 目的: PLAN-078 の `cli/lib/agent_slots.py` に実装される helper 5 関数を、SQLite 実 DB と最小限のモックに分離して検証する単体テストを設計する。`agent_slots` は invocation 粒度の slot 管理を担うため、境界値、FK 整合、状態遷移、集計軸の検証を分けて押さえる。

## §1 位置付け (HELIX V-model テストピラミッド)

```
        E2E (L6 / CLI 全体・手動 watch)
       /          \
      / Integration \  ← PLAN-078 integration-test-design.md
     /______________\
    /                \
   /   Unit tests     \  ← 本設計の対象 (agent_slots helper)
  /____________________\
```

PLAN-078 は `agent_slots` schema と helper 実装を L4 で進めるが、`fire_slot()` / `release_slot()` / `list_*()` / `get_stats()` は純粋な関数ではなく DB 境界を持つ。そのため、本書では `helix.db` の fresh SQLite を使い、外部 I/O だけを局所的に切り離す。

**HELIX V-model 整合性**:

- L3 詳細設計: D-DB EXT §10 agent_slots
- L4 実装: `cli/lib/agent_slots.py`
- **L4 テスト設計: 本書**
- L4 テスト実装: `cli/lib/tests/test_agent_slots_unit.py`
- G4: 単体 + 結合 + 既存回帰 + `helix doctor` 影響なし

### 1.1 4 artifact 双方向 trace

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §10 agent_slots |
| ② 実装コード | L4 実装 | `cli/lib/agent_slots.py` |
| ③ テスト設計 | L4 設計 | `docs/v2/L4-test-design/PLAN-078-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_agent_slots_unit.py` |

### 1.2 工程整合

| 層 | 整合内容 | 本書での扱い |
|---|---|---|
| L3 | D-DB EXT §10 の schema / helper / state machine | 変更なし、trace 固定 |
| L4 | helper 実装と unit test 実装 | `agent_slots.py` と `test_agent_slots_unit.py` を結ぶ |
| G4 | 実装凍結ゲート | 60 前後の case を全通させる前提で設計 |

### 1.3 テスト対象の境界

- 対象: `agent_slots` helper の挙動
- 非対象: CLI wrapper (`cli/helix-agent`)、hook 自動化、PreToolUse 統合、Phase 2 の timeout 自動遷移
- 例外: `automation_runs` FK の挙動確認だけは DB 整合の一部として扱う

## §2 対象関数 × case 設計

### 2.1 `fire_slot(agent_kind, role=None, subagent_type=None, plan_id=None, task_id=None, sprint=None, session_id=None, automation_run_id=None) -> int`

**対象設計 (① D-DB)**: D-DB EXT §10.5 helper 関数 / §10.2 schema / §10.7 関連 table 連携  
**実装ファイル (② D-IMPL)**: `cli/lib/agent_slots.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_agent_slots_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-FIRE-001 | agent_kind=codex, role=tl, plan_id=PLAN-078 | slot_id(int) を返す | `datetime('now')` 固定 |
| U-FIRE-002 | agent_kind=claude_subagent, subagent_type=pmo-sonnet | slot_id(int) を返す | `datetime('now')` 固定 |
| U-FIRE-003 | agent_kind の空文字 | ValueError | なし |
| U-FIRE-004 | agent_kind=None | ValueError | なし |
| U-FIRE-005 | role=None, subagent_type=None, agent_kind=codex | codex 用 default 保存 | DB 検証 |
| U-FIRE-006 | role と subagent_type の両方指定 | 片方のみ保存または ValueError を仕様固定 | DB spy |
| U-FIRE-007 | plan_id 空文字 | NULL ではなく空文字保存可否を仕様固定 | DB 直接確認 |
| U-FIRE-008 | task_id / sprint / session_id の同時保存 | すべて永続化 | DB row 確認 |
| U-FIRE-009 | automation_run_id に存在する FK | INSERT 成功 | 実 INSERT |
| U-FIRE-010 | automation_run_id に不整合値 | IntegrityError | 実 INSERT |
| U-FIRE-011 | 連続 fire 2 回 | 別 slot_id を返す | 一意性確認 |
| U-FIRE-012 | slot_source 既定値 | helix_codex が保存される | DB row 確認 |

### 2.2 `release_slot(slot_id, status='completed', exit_code=None)`

**対象設計 (① D-DB)**: D-DB EXT §10.6 状態遷移 / §10.4 trigger / §10.2 schema  
**実装ファイル (② D-IMPL)**: `cli/lib/agent_slots.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_agent_slots_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-REL-001 | active slot, status=completed, exit_code=0 | released_at と status 更新 | `datetime('now')` 固定 |
| U-REL-002 | active slot, status=failed, exit_code=1 | failed 保存 | DB row 確認 |
| U-REL-003 | status=cancelled | cancelled 保存 | DB row 確認 |
| U-REL-004 | slot_id 不存在 | LookupError か ValueError | なし |
| U-REL-005 | 既に completed の slot | 冪等または更新拒否を仕様固定 | DB spy |
| U-REL-006 | exit_code=None, status=completed | NULL 許容/0 補完の仕様固定 | DB row 確認 |
| U-REL-007 | status の空文字 | ValueError | なし |
| U-REL-008 | status=timed_out | scope 外として拒否 | なし |
| U-REL-009 | append-only trigger を壊さない更新 | DELETE なしで UPDATE 可 | DB 制約確認 |
| U-REL-010 | release 後 duration_ms 相当計算 | started/released 差分が整合 | 時刻固定 |

### 2.3 `list_active_slots() -> list[dict]`

**対象設計 (① D-DB)**: D-DB EXT §10.2 status / §10.6 state machine / §10.8 trace  
**実装ファイル (② D-IMPL)**: `cli/lib/agent_slots.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_agent_slots_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-LIST-001 | running 2 件 + completed 1 件 | running のみ返す | DB fixture |
| U-LIST-002 | 0 件 | 空 list | DB fixture |
| U-LIST-003 | plan_id フィルタ無し | 全 running を返す | DB fixture |
| U-LIST-004 | parent_invocation_id を持つ child | tree 情報を壊さず返す | DB fixture |
| U-LIST-005 | status=failed を含む混在 | running 以外を除外 | DB fixture |
| U-LIST-006 | released_at NULL の running | active として返す | DB fixture |
| U-LIST-007 | sort 順の安定性 | fired_at か id 順で再現可能 | DB fixture |
| U-LIST-008 | 辞書キーの完全性 | 主要列を含む dict を返す | shape assert |

### 2.4 `list_stale_slots(threshold_minutes=5) -> list[dict]`

**対象設計 (① D-DB)**: D-DB EXT §10.6 state machine / §10.9 carry note (Phase 2 の timeout は scope 外)  
**実装ファイル (② D-IMPL)**: `cli/lib/agent_slots.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_agent_slots_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-STALE-001 | 5 分未満の running | 空 list | `datetime('now')` 固定 |
| U-STALE-002 | 5 分ちょうどの running | stale に含める/除外を仕様固定 | 時刻固定 |
| U-STALE-003 | 6 分超の running | stale に含める | 時刻固定 |
| U-STALE-004 | completed slot | 除外 | DB fixture |
| U-STALE-005 | cancelled slot | 除外 | DB fixture |
| U-STALE-006 | threshold_minutes=0 | 全 running が stale 候補 | 時刻固定 |
| U-STALE-007 | threshold_minutes=-1 | ValueError | なし |
| U-STALE-008 | threshold_minutes=None | TypeError or ValueError | なし |
| U-STALE-009 | started_at 欠損レコード | DB 不整合として除外/失敗を固定 | DB fixture |
| U-STALE-010 | 返却順 | 古い順または安定順 | DB fixture |

### 2.5 `get_stats(days=7, by='hour') -> dict`

**対象設計 (① D-DB)**: D-DB EXT §10.2 index / §10.7 related table / §10.8 trace  
**実装ファイル (② D-IMPL)**: `cli/lib/agent_slots.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_agent_slots_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-STATS-001 | days=7, by=hour | hour 集計の dict | DB fixture |
| U-STATS-002 | days=1, by=hour | 直近 1 日のみ集計 | 時刻固定 |
| U-STATS-003 | by=agent_kind | 軸別集計を返す | DB fixture |
| U-STATS-004 | by=role | role 別集計を返す | DB fixture |
| U-STATS-005 | by=plan_id | PLAN trace 別集計を返す | DB fixture |
| U-STATS-006 | by の空文字 | ValueError | なし |
| U-STATS-007 | by=minute | 未対応値として ValueError | なし |
| U-STATS-008 | days=0 | 当日集計または拒否を仕様固定 | DB fixture |
| U-STATS-009 | days=-1 | ValueError | なし |
| U-STATS-010 | tokens/cost 未実装時 | 数値なしでも集計骨格は返る | DB fixture |
| U-STATS-011 | completed/failed/cancelled の状態混在 | status 別内訳が崩れない | DB fixture |
| U-STATS-012 | automation_run_id 紐付けあり | run 連携 slot も集計対象 | DB fixture |

### 2.6 case 数集計

| 関数 | case 数 |
|---|---|
| fire_slot | 12 |
| release_slot | 10 |
| list_active_slots | 8 |
| list_stale_slots | 10 |
| get_stats | 12 |
| **合計** | **52 cases** |

## §3 fixture / mock 戦略

### 3.1 DB fixture

- `helix.db` は temp dir 上に fresh SQLite を作る
- `migrate_all` を実行して `SCHEMA_VERSION = 28` と `agent_slots` / `automation_runs` を有効化する
- Flask は使わない
- 可能なら `sqlite3.connect` を本物で使い、モックは時間固定と外部例外のみに限定する

### 3.2 時刻固定

- `datetime('now')` は monkey-patch で固定する
- `started_at` / `fired_at` / `released_at` / 集計 window の判定を同じ固定時刻に揃える
- stale 判定の境界値は 4 分 59 秒 / 5 分 / 5 分 1 秒 を必ず通す

### 3.3 FK / 整合性

- `automation_run_id` は実 INSERT で存在確認する
- 不整合値は SQLite の FK 失敗として検証する
- `parent_invocation_id` は tree 表現の trace に使うが、本書の unit では深い再帰は追わない

### 3.4 mock 方針

| 対象 | 方針 | 理由 |
|---|---|---|
| `datetime('now')` | monkey-patch | 境界値再現のため |
| `sqlite3.IntegrityError` | 実例外 or 最小 mock | FK 不整合の固定 |
| DB cursor / connection | 実 DB 優先、必要時だけ spy | helper の SQL 断面を保持 |
| `agent_slots.py` 内 helper 相互 | 原則 mock しない | 単体の意味を壊さない |

### 3.5 アンチパターン

- integration test を unit 化して流用するのは NG
- helper 本体を mock してケースだけ通すのは NG
- spy なしで戻り値だけ見るのは NG

## §4 DoD (受入条件)

- [ ] 本書の 52 cases を `cli/lib/tests/test_agent_slots_unit.py` で全実装する
- [ ] case ID が test docstring で参照される
- [ ] `migrate_all` + fresh SQLite で再現可能
- [ ] `automation_run_id` の FK 不整合を unit で検証する
- [ ] `list_stale_slots()` の threshold 境界が固定される
- [ ] `get_stats()` の `by` 値検証が固定される
- [ ] `helix doctor` に影響しない
- [ ] 既存 integration / regression の挙動を壊さない

## §5 4 artifact 双方向 trace 表

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §10 |
| ② 実装コード | L4 実装 | `cli/lib/agent_slots.py` |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-078-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_agent_slots_unit.py` |

### 5.1 trace ルール

- D-DB EXT §10 の helper 名と case ID を 1:1 で追えるようにする
- `fire_slot()` の case は `U-FIRE-*`
- `release_slot()` の case は `U-REL-*`
- `list_active_slots()` の case は `U-LIST-*`
- `list_stale_slots()` の case は `U-STALE-*`
- `get_stats()` の case は `U-STATS-*`

### 5.2 Next Action

1. 本書を基準に `cli/lib/tests/test_agent_slots_unit.py` を作成する
2. `migrate_all` を使う fixture を共通化する
3. `automation_runs` FK と stale 境界の case を先に固める
4. integration test 設計と相互に trace を確認する
