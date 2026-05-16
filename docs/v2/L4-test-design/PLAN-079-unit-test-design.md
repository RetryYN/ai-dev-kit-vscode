---
plan_id: PLAN-079
doc_id: PLAN-079-unit-test-design
title: "PLAN-079 単体テスト設計 (scrum_local + reverse_local helper)"
status: draft
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-17
status_history:
  - 2026-05-17: 初期作成 (PLAN-079 Sprint .2b)
owner: PM
related_docs:
  - docs/plans/PLAN-079-uncertainty-pocket-scrum-reverse-chain.md
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (§11/§12 対象 ① 設計)
  - docs/v2/L4-test-design/PLAN-079-integration-test-design.md (姉妹 ③)
phases: L4
gates: G4
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB EXT §11/§12) と ④ テストコード
> (`cli/lib/tests/test_scrum_local_unit.py` / `cli/lib/tests/test_reverse_local_unit.py`)
> を双方向 trace で繋ぐ独立文書である。

# PLAN-079 単体テスト設計 (scrum_local + reverse_local helper)

> 目的: PLAN-079 の `cli/lib/scrum_local.py` と `cli/lib/reverse_local.py` に実装される helper を、SQLite の fresh DB と最小限の fixture で検証する単体テストを設計する。UPS と SRF chain の境界値、FK 整合、状態遷移、集計、routing を unit 層で固定し、integration 層へ責務を渡す。

## §1 位置付け (HELIX V-model テストピラミッド)

```
        E2E (L6 / CLI 全体・手動 watch)
       /          \
      / Integration \  ← PLAN-079 integration-test-design.md
     /______________\
    /                \
   /   Unit tests     \  ← 本設計の対象 (scrum_local + reverse_local helper)
  /____________________\
```

PLAN-079 は `scrum_local_loops` と `reverse_local_loops` の v29 schema を L4 で扱うが、helper は DB 境界を持つため、fresh SQLite を使い外部 I/O を局所的に切り離す。本書は unit 層で「ロジックと制約の固定」を担当し、CLI ルーティングや end-to-end の繋ぎ込みは integration test に委ねる。

**HELIX V-model 整合性**:

- L3 詳細設計: D-DB EXT §11 scrum_local_loops / §12 reverse_local_loops
- L4 実装: `cli/lib/scrum_local.py` / `cli/lib/reverse_local.py`
- **L4 テスト設計: 本書**
- L4 テスト実装: `cli/lib/tests/test_scrum_local_unit.py` / `cli/lib/tests/test_reverse_local_unit.py`
- G4: 単体 + 結合 + 既存回帰 + `helix doctor` 影響なし

### 1.1 4 artifact 双方向 trace

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §11 + §12 |
| ② 実装コード | L4 実装 | `cli/lib/scrum_local.py` + `cli/lib/reverse_local.py` |
| ③ テスト設計 | L4 設計 | `docs/v2/L4-test-design/PLAN-079-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_scrum_local_unit.py` + `cli/lib/tests/test_reverse_local_unit.py` |

### 1.2 工程整合

| 層 | 整合内容 | 本書での扱い |
|---|---|---|
| L3 | D-DB EXT §11/§12 の schema / helper / state machine | 変更なし、trace 固定 |
| L4 | helper 実装と unit test 実装 | `scrum_local.py` と `reverse_local.py` を結ぶ |
| G4 | 実装凍結ゲート | 約 60-70 case を全通させる前提で設計 |

### 1.3 テスト対象の境界

- 対象: `scrum_local` と `reverse_local` の helper 挙動
- 非対象: CLI wrapper (`cli/helix-scrum` / `cli/helix-reverse`)、hook 自動化、pretool / session hook、monitoring 系集計
- 例外: `agent_slots.id` / `scrum_local_loops.loop_id` / `reverse_local_loops.parent_scrum_loop_id` の FK 失敗は DB 整合の一部として扱う

## §2 対象関数 × case 設計

### 2.1 `init_local_loop(forward_layer, hypothesis, acceptance, *, forward_plan_id=None, parent_loop_id=None, related_agent_slot_id=None) -> str`

**対象設計 (① D-DB)**: D-DB EXT §11.2 schema / §11.3 列詳細 / §11.5 helper  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-INIT-001 | `forward_layer=L4`, 妥当な `hypothesis` / `acceptance` | `H-LOCAL-XXX` を返す | `datetime('now')` 固定 |
| U-SL-INIT-002 | `forward_plan_id=PLAN-079` 指定 | PLAN trace を保存 | DB row 確認 |
| U-SL-INIT-003 | `parent_loop_id=None` で初回 loop | parent 無しで保存 | DB row 確認 |
| U-SL-INIT-004 | `parent_loop_id` が自己参照 | pivot 連鎖として保存 | FK/self reference 確認 |
| U-SL-INIT-005 | `related_agent_slot_id` が既存 FK | INSERT 成功 | 実 INSERT |
| U-SL-INIT-006 | `related_agent_slot_id` が不整合値 | IntegrityError | 実 INSERT |
| U-SL-INIT-007 | `forward_layer` 空文字 | ValueError | なし |
| U-SL-INIT-008 | `hypothesis` / `acceptance` の空文字 | ValueError | なし |

### 2.2 `record_poc(loop_id, *, commit_sha=None, artifact_path=None, notes=None) -> None`

**対象設計 (① D-DB)**: D-DB EXT §11.3 列詳細 / §11.7 関連 table / §11.5 helper  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-POC-001 | running loop に `commit_sha` あり | state を `S1` に更新 | `datetime('now')` 固定 |
| U-SL-POC-002 | `artifact_path` あり | PoC artifact trace を保存 | DB row 確認 |
| U-SL-POC-003 | `notes` あり | notes を保存 | DB row 確認 |
| U-SL-POC-004 | loop_id 不存在 | LookupError か ValueError | なし |
| U-SL-POC-005 | `loop_id` が completed/pivot 済み相当 | 更新拒否 | DB state assert |
| U-SL-POC-006 | `commit_sha` 空文字 | ValueError | なし |

### 2.3 `verify_loop(loop_id, *, result, evidence=None) -> None`

**対象設計 (① D-DB)**: D-DB EXT §11.2 state / §11.6 state machine / §11.5 helper  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-VERIFY-001 | running loop, `result=confirmed` | state を `S2` に更新 | `datetime('now')` 固定 |
| U-SL-VERIFY-002 | running loop, `result=rejected` | state を `S2` に更新 | DB row 確認 |
| U-SL-VERIFY-003 | running loop, `result=pivot` | state を `S2` に更新 | DB row 確認 |
| U-SL-VERIFY-004 | `evidence` あり | verify evidence を保存 | DB row 確認 |
| U-SL-VERIFY-005 | `result` が空文字 | ValueError | なし |
| U-SL-VERIFY-006 | `result=unknown` | CHECK/ValueError で拒否 | なし |

### 2.4 `decide_loop(loop_id, *, result, decided_by=None, decided_note=None) -> None`

**対象設計 (① D-DB)**: D-DB EXT §11.2 decide_result / §11.6 state machine / §11.7 related table  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-DECIDE-001 | `result=confirmed` | `decide_result=confirmed`, `state=S3` | `datetime('now')` 固定 |
| U-SL-DECIDE-002 | `result=rejected` | `decide_result=rejected`, `state=S3` | DB row 確認 |
| U-SL-DECIDE-003 | `result=pivot` | `decide_result=pivot`, `state=S3` | DB row 確認 |
| U-SL-DECIDE-004 | S0/S1/S2 で `result` が NULL 相当 | 許容されることを確認 | DB state 確認 |
| U-SL-DECIDE-005 | S3 で `result` 再更新 | 更新拒否 | terminal guard 確認 |
| U-SL-DECIDE-006 | `result` 空文字 | ValueError | なし |
| U-SL-DECIDE-007 | `result=unknown` | CHECK/ValueError で拒否 | なし |
| U-SL-DECIDE-008 | `decided_note` あり | note を保存 | DB row 確認 |

### 2.5 `list_active_loops(*, forward_layer=None, forward_plan_id=None) -> list[dict]`

**対象設計 (① D-DB)**: D-DB EXT §11.2 state / §11.7 related table / §11.8 trace  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-LIST-001 | running 2 件 + decided 1 件 | running のみ返す | DB fixture |
| U-SL-LIST-002 | 0 件 | 空 list | DB fixture |
| U-SL-LIST-003 | `forward_layer` フィルタ無し | 全 active を返す | DB fixture |
| U-SL-LIST-004 | `forward_plan_id` で絞り込み | PLAN 単位で返す | DB fixture |
| U-SL-LIST-005 | pivot chain の child を含む | tree 情報を壊さず返す | DB fixture |
| U-SL-LIST-006 | 辞書キー完全性 | 主要列を含む dict を返す | shape assert |

### 2.6 `get_stats(*, days=7) -> dict`

**対象設計 (① D-DB)**: D-DB EXT §11.3 trace / §11.6 state machine / §11.8 trace  
**実装ファイル (② D-IMPL)**: `cli/lib/scrum_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_scrum_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-SL-STATS-001 | days=7 | confirmed/rejected/pivot の集計 dict | DB fixture |
| U-SL-STATS-002 | days=1 | 直近 1 日のみ集計 | 時刻固定 |
| U-SL-STATS-003 | days=0 | 当日集計または拒否を仕様固定 | DB fixture |
| U-SL-STATS-004 | days=-1 | ValueError | なし |
| U-SL-STATS-005 | decided_at 欠損の running loop | running 集計に入る | DB fixture |
| U-SL-STATS-006 | `forward_layer` ばらつき | layer 別の内訳が崩れない | DB fixture |

### 2.7 `init_from_scrum(scrum_loop_id, reverse_type='scrum-to-forward') -> str`

**対象設計 (① D-DB)**: D-DB EXT §12.2 schema / §12.3 列詳細 / §12.5 helper  
**実装ファイル (② D-IMPL)**: `cli/lib/reverse_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_reverse_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-RL-INIT-001 | confirmed scrum loop から起動 | `RL-LOCAL-XXX` を返す | `datetime('now')` 固定 |
| U-RL-INIT-002 | `reverse_type=scrum-to-forward` 既定 | type を保存 | DB row 確認 |
| U-RL-INIT-003 | `scrum_loop_id` が不在 | IntegrityError / LookupError | 実 INSERT |
| U-RL-INIT-004 | `scrum_loop_id` が未 confirmed | 起動拒否 | state assert |
| U-RL-INIT-005 | `scrum_loop_id` に pivot 連鎖がある | parent 起点を保持 | FK trace 確認 |
| U-RL-INIT-006 | `reverse_type` 空文字 | ValueError | なし |

### 2.8 `transition_state(loop_id, new_state) -> None`

**対象設計 (① D-DB)**: D-DB EXT §12.2 state / §12.6 state machine / §12.5 helper  
**実装ファイル (② D-IMPL)**: `cli/lib/reverse_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_reverse_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-RL-TRANS-001 | `R0 -> R1` | state 更新 | `datetime('now')` 固定 |
| U-RL-TRANS-002 | `R1 -> R2` | state 更新 | DB row 確認 |
| U-RL-TRANS-003 | `R2 -> R3` | state 更新 | DB row 確認 |
| U-RL-TRANS-004 | `R3 -> R4` | state 更新 | DB row 確認 |
| U-RL-TRANS-005 | `R0 -> R2` の skip | 拒否 | state machine 制約 |
| U-RL-TRANS-006 | `R4 -> R1` の巻戻し | 拒否 | なし |
| U-RL-TRANS-007 | `new_state` 空文字 | ValueError | なし |
| U-RL-TRANS-008 | `new_state=RX` | CHECK/ValueError で拒否 | なし |

### 2.9 `route_to_forward(loop_id, target_plan, target_layer, artifact_links=None) -> None`

**対象設計 (① D-DB)**: D-DB EXT §12.2 schema / §12.3 列詳細 / §12.7 関連 table  
**実装ファイル (② D-IMPL)**: `cli/lib/reverse_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_reverse_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-RL-ROUTE-001 | `target_plan=PLAN-079`, `target_layer=L4` | routed_at と target を保存 | `datetime('now')` 固定 |
| U-RL-ROUTE-002 | `artifact_links` あり | JSON を保存 | DB row 確認 |
| U-RL-ROUTE-003 | `target_layer=L1/L2/L3/L4` | 許容層のみ保存 | DB row 確認 |
| U-RL-ROUTE-004 | `target_layer=L5` | ValueError | なし |
| U-RL-ROUTE-005 | 未 R4 の loop で route | 更新拒否 | state assert |
| U-RL-ROUTE-006 | `target_plan` 空文字 | ValueError | なし |

### 2.10 `list_active_loops(*, target_forward_plan=None, reverse_type=None) -> list[dict]`

**対象設計 (① D-DB)**: D-DB EXT §12.2 state / §12.7 related table / §12.8 trace  
**実装ファイル (② D-IMPL)**: `cli/lib/reverse_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_reverse_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-RL-LIST-001 | R0-R3 2 件 + R4 1 件 | 未 route の active のみ返す | DB fixture |
| U-RL-LIST-002 | 0 件 | 空 list | DB fixture |
| U-RL-LIST-003 | `target_forward_plan` フィルタ無し | 全 active を返す | DB fixture |
| U-RL-LIST-004 | `reverse_type=scrum-to-forward` | type 別に返す | DB fixture |

### 2.11 `get_routing_stats(*, days=7) -> dict`

**対象設計 (① D-DB)**: D-DB EXT §12.3 trace / §12.6 state machine / §12.7 related table  
**実装ファイル (② D-IMPL)**: `cli/lib/reverse_local.py`  
**テストコード (④ D-TEST-CODE-UNIT)**: `cli/lib/tests/test_reverse_local_unit.py`

| case | 入力 | 期待出力 | mock |
|---|---|---|---|
| U-RL-STATS-001 | days=7 | R0-R4 / routed 先の集計 dict | DB fixture |
| U-RL-STATS-002 | days=1 | 直近 1 日のみ集計 | 時刻固定 |
| U-RL-STATS-003 | days=0 | 当日集計または拒否を仕様固定 | DB fixture |
| U-RL-STATS-004 | days=-1 | ValueError | なし |

### 2.12 case 数集計

| 関数 | case 数 |
|---|---|
| init_local_loop | 8 |
| record_poc | 6 |
| verify_loop | 6 |
| decide_loop | 8 |
| list_active_loops (scrum_local) | 6 |
| get_stats | 6 |
| init_from_scrum | 6 |
| transition_state | 8 |
| route_to_forward | 6 |
| list_active_loops (reverse_local) | 4 |
| get_routing_stats | 4 |
| **合計** | **68 cases** |

## §3 fixture / mock 戦略

### 3.1 DB fixture

- `helix.db` は temp dir 上に fresh SQLite を作る
- `migrate_all` を実行して `scrum_local_loops` / `reverse_local_loops` / `agent_slots` / `automation_runs` を有効化する
- Flask は使わない
- 可能なら `sqlite3.connect` を本物で使い、モックは時間固定と外部例外のみに限定する

### 3.2 時刻固定

- `datetime('now')` は monkey-patch で固定する
- `started_at` / `decided_at` / `routed_at` / 集計 window の判定を同じ固定時刻に揃える
- UPS の境界値は 4 分 59 秒 / 5 分 / 5 分 1 秒 を通し、SRF の routing 固定時刻も同一 fixture で再現する

### 3.3 FK / 整合性

- `related_agent_slot_id` は実 INSERT で存在確認する
- `parent_loop_id` の自己参照は pivot 連鎖の trace として扱う
- `parent_scrum_loop_id` は実 INSERT で存在確認する
- 不整合値は SQLite の FK 失敗として検証する

### 3.4 mock 方針

| 対象 | 方針 | 理由 |
|---|---|---|
| `datetime('now')` | monkey-patch | 境界値再現のため |
| `sqlite3.IntegrityError` | 実例外 or 最小 mock | FK 不整合の固定 |
| DB cursor / connection | 実 DB 優先、必要時だけ spy | helper の SQL 断面を保持 |
| `scrum_local.py` / `reverse_local.py` 内 helper 相互 | 原則 mock しない | 単体の意味を壊さない |

### 3.5 アンチパターン

- integration test を unit 化して流用するのは NG
- helper 本体を mock して case だけ通すのは NG
- spy なしで戻り値だけ見るのは NG
- reverse 側で state machine を飛ばして `route_to_forward()` を直接通すのは NG

## §4 DoD (受入条件)

- [ ] 本書の 68 cases を `cli/lib/tests/test_scrum_local_unit.py` と `cli/lib/tests/test_reverse_local_unit.py` で全実装する
- [ ] case ID が test docstring で参照される
- [ ] `migrate_all` + fresh SQLite で再現可能
- [ ] `related_agent_slot_id` と `parent_scrum_loop_id` の FK 不整合を unit で検証する
- [ ] `init_local_loop()` の pivot 連鎖と自己参照が固定される
- [ ] `decide_loop()` の `confirmed` / `rejected` / `pivot` を全網羅する
- [ ] `transition_state()` の R0→R1→R2→R3→R4 以外の skip が拒否される
- [ ] `route_to_forward()` の target layer 制約が固定される
- [ ] `helix doctor` に影響しない
- [ ] 既存 integration / regression の挙動を壊さない

## §5 4 artifact 双方向 trace 表

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | `docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md` §11 + §12 |
| ② 実装コード | L4 実装 | `cli/lib/scrum_local.py` + `cli/lib/reverse_local.py` |
| ③ テスト設計 (本書) | L4 設計 | `docs/v2/L4-test-design/PLAN-079-unit-test-design.md` |
| ④ テストコード | L4 実装 | `cli/lib/tests/test_scrum_local_unit.py` + `cli/lib/tests/test_reverse_local_unit.py` |

### 5.1 trace ルール

- D-DB EXT §11 の helper 名と case ID を 1:1 で追えるようにする
- `init_local_loop()` の case は `U-SL-INIT-*`
- `record_poc()` の case は `U-SL-POC-*`
- `verify_loop()` の case は `U-SL-VERIFY-*`
- `decide_loop()` の case は `U-SL-DECIDE-*`
- `list_active_loops()` (scrum_local) の case は `U-SL-LIST-*`
- `get_stats()` の case は `U-SL-STATS-*`
- `init_from_scrum()` の case は `U-RL-INIT-*`
- `transition_state()` の case は `U-RL-TRANS-*`
- `route_to_forward()` の case は `U-RL-ROUTE-*`
- `list_active_loops()` (reverse_local) の case は `U-RL-LIST-*`
- `get_routing_stats()` の case は `U-RL-STATS-*`

### 5.2 Next Action

1. 本書を基準に `cli/lib/tests/test_scrum_local_unit.py` と `cli/lib/tests/test_reverse_local_unit.py` を作成する
2. `migrate_all` を使う fixture を共通化する
3. `related_agent_slot_id` と `parent_scrum_loop_id` の FK case を先に固める
4. integration test 設計と相互に trace を確認する

### 5.3 TODO 残存確認

- TODO 文字列の残存なし
- 未完了項目は DoD のチェックボックスで明示し、設計上の未確定事項は残していない
