---
doc_id: PLAN-084-integration-test-design-v0.1
plan_id: PLAN-084
sprint: Phase 3.4 / L3-L4 結合テスト設計
status: draft
created: 2026-05-17
primary_drive: be
test_layer: L4 結合テスト設計 (V-model 4 artifact ③)
related_designs:
  - D-DB-SEP-draft-v0.1 (本 doc が対応する schema + migration 設計、双方向 trace)
  - D-API-SEP-draft-v0.1 (本 doc が対応する adapter API 設計、双方向 trace)
  - D-CONTRACT-EVENT-draft-v0.1 (本 doc が対応する event class 設計、双方向 trace)
related_test_implementations:
  - cli/lib/tests/test_db_separation_integration.py (Phase 4.A 起票予定、I-MIGRATION-* を実装)
  - cli/lib/tests/test_dual_write_mismatch.py (Phase 4.B 起票予定、I-DUALWRITE-* を実装)
  - cli/lib/tests/test_shadow_replay.py (Phase 4.C 起票予定、I-REPLAY-* を実装)
  - cli/lib/tests/test_correlation_cross_db.py (Phase 4.B 起票予定、I-CORR-* を実装)
  - cli/tests/db_separation_smoke.bats (Phase 4.A 起票予定、I-SMOKE-* を実装)
---

> **V-model 4 artifact 位置付け** (HELIX_CORE.md §V-model 4 artifact 双方向 trace 原則 / PLAN-075):
> 本書は ③ テスト設計 artifact。以下の 3 設計文書 (①) と ④ テストコード群を双方向 trace で繋ぐ
> 独立文書である。
>
> - ① 設計 1: `docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md` (schema + migration step 正本)
> - ① 設計 2: `docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md` (adapter API 正本)
> - ① 設計 3: `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` (event class 正本)
> - ④ テストコード群: Phase 4.A/4.B/4.C で起票・実装予定 (各 §末尾の carry 表を参照)

# PLAN-084 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 目的とスコープ

### 1.1 本文書の位置づけ

本文書は PLAN-084 (helix.db 6 分離 + Event Sourcing + projector) の **結合テスト設計書** (③ artifact) である。

V-model 4 artifact の原則に従い、3 つの L3 設計文書 (D-DB-SEP / D-API-SEP / D-CONTRACT-EVENT) に対応するテストケース群を、実装前に設計として確定する。Phase 4.A / 4.B / 4.C の実装担当 (Codex qa) は本文書を参照してテストコードを実装し、テストコードの docstring に「DoD 検証: PLAN-084-integration-test-design.md <case-ID>」を明示する。

### 1.2 V-model 4 artifact 双方向 trace

| Artifact | 文書 / ファイル | 状態 |
|---|---|---|
| ① 設計 (schema) | `docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md` | Phase 3.1 draft 起票済 |
| ① 設計 (adapter) | `docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md` | Phase 3.2 draft 起票済 |
| ① 設計 (event) | `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` | Phase 3.3 draft 起票済 |
| ② 実装コード | `cli/lib/compatibility_adapter.py` / `cli/lib/migrations/v31_db_separation.py` 他 | Phase 4.A/4.B 実装 (carry) |
| **③ テスト設計 (本文書)** | `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` | Phase 3.4 draft (本文書) |
| ④ テストコード | `cli/lib/tests/test_db_separation_integration.py` 他 5 ファイル | Phase 4.A/4.B/4.C 実装 (carry) |

双方向 trace 宣言:

- **本文書 → ① 設計**: 各 § で「対象設計: D-DB-SEP §X / D-API-SEP §Y / D-CONTRACT-EVENT §Z」を明示
- **本文書 → ④ テストコード**: 各 § に「テスト実装ファイル: <path>」を明示
- **④ テストコード → 本文書**: テスト docstring に「DoD 検証: PLAN-084-integration-test-design.md <case-ID>」を明示すること (Phase 4.A/4.B/4.C 実装時の必須義務)
- **① 設計 → 本文書**: D-DB-SEP §8 / D-API-SEP §8 に「③ テスト設計: docs/v2/L4-test-design/PLAN-084-integration-test-design.md」の reference を追記予定 (Phase 3.4 完了後に carry 解消)

### 1.3 テスト対象とスコープ

**In-scope** (本文書が設計する結合テスト):

| 領域 | 設計根拠 | case prefix | Phase |
|---|---|---|---|
| migration v30→v31 (gate 1〜6 全 step) | D-DB-SEP §6 | I-MIGRATION-* | 4.A / 4.C |
| dual-write mismatch gate (gate 2) | D-DB-SEP §6.4 + ADR-018 §Decision.5 | I-DUALWRITE-* | 4.B |
| shadow replay (gate 3) | D-DB-SEP §6.5 + ADR-018 §Decision.5 | I-REPLAY-* | 4.C |
| correlation cross-db trace | D-CONTRACT-EVENT §4 | I-CORR-* | 4.B |
| top-level CLI smoke (3 CLI) | D-API-SEP §3 + tl-advisor Round 1-3 必須化 | I-SMOKE-* | 4.A |

**Non-goals** (本文書の対象外):

- 単体テスト (個別 Python function の unit test) → `PLAN-084-unit-test-design.md` で別途設計
- E2E テスト (helix CLI フル実行フロー) → 本 PLAN スコープ外
- HTTP endpoint 層の個別 API テスト → `PLAN-074-integration-test-design.md` で実施済み
- projector の実装詳細テスト → Phase 4.B の Codex qa が単体テストで対応

### 1.4 case 命名規約

| prefix | 領域 |
|---|---|
| `I-MIGRATION-NNN` | migration v30→v31 の各 step 検証 |
| `I-DUALWRITE-NNN` | dual-write 期間中の write 整合・mismatch gate 検証 |
| `I-REPLAY-NNN` | shadow replay の正確性・idempotency 検証 |
| `I-CORR-NNN` | correlation_id の cross-db 発行・継承・trace 検証 |
| `I-SMOKE-NNN` | top-level CLI smoke (helix-pr / helix-push / helix-agent) |

### 1.5 mock 戦略

| mock 対象 | 方針 |
|---|---|
| helix.db / 6 db ファイル | temp dir に生成。`migrate_all()` で v30 まで適用後、migration script を実行 |
| HELIX_DB_CUTOVER 環境変数 | テスト内で `monkeypatch.setenv("HELIX_DB_CUTOVER", "0"/"1")` でスイッチ |
| sqlite3 error injection | `unittest.mock.patch` で `sqlite3.connect` / `Connection.execute` を差し替え |
| UUID v7 generator | `generate_event_id` を patch してテスト用固定値を返す |
| datetime.now | `freezegun` または `monkeypatch` で固定時刻を注入 |
| top-level CLI (bats) | `$BATS_TMPDIR` に `.helix/` を配置し、temp env で CLI を呼び出す |

### 1.6 受入条件との対応 (L1-REQUIREMENTS.md §3.9)

| AC | 検証 case prefix |
|---|---|
| AC-DB-SEP-01 (6 db 物理分離) | I-MIGRATION-004〜006 |
| AC-DB-SEP-02 (event_envelope schema) | I-MIGRATION-001〜003、I-CORR-001〜006 |
| AC-DB-SEP-03 (dual-write + mismatch gate) | I-DUALWRITE-001〜008 |
| AC-DB-SEP-04 (shadow replay gate) | I-REPLAY-001〜008 |
| AC-DB-SEP-05 (API 互換 100%) | I-SMOKE-001〜006 |
| AC-DB-SEP-06 (cutover gate) | I-MIGRATION-010〜011 |
| AC-DB-SEP-07 (rollback gate) | I-MIGRATION-012 |

---

## §2 I-MIGRATION-* 結合テスト設計

**対象設計**: D-DB-SEP-draft §6 (migration v30→v31 の全 step)
**テスト実装ファイル**: `cli/lib/tests/test_db_separation_integration.py` (Phase 4.A)、
`cli/tests/db_separation_smoke.bats` (Phase 4.A、I-SMOKE-* と共用)

### 2.1 dual-write start step 検証 (gate 1 対応)

migration script の §6.2 dual-write start step が idempotent に旧 helix.db を拡張することを検証する。

---

**I-MIGRATION-001: event_envelope table を既存 helix.db (v30) に追加**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.2 (dual-write start: `event_envelope` CREATE TABLE IF NOT EXISTS) |
| 前提条件 | temp dir に v30 相当の helix.db が存在する (既存 table が全て揃っている) |
| 実行手順 | `v31_db_separation.step_dual_write_start(conn)` を呼び出す |
| 期待結果 | `event_envelope` table が helix.db に作成される |
| 検証項目 | 1. `SELECT name FROM sqlite_master WHERE name='event_envelope'` が 1 件返る 2. `event_envelope` の column が D-DB-SEP §3.1 の schema と一致する |
| 非破壊確認 | v30 の既存 table (例: `agent_slots`, `automation_runs`) が削除・変更されていない |
| DoD | 上記検証項目が全て PASS |

---

**I-MIGRATION-002: projection_state table を既存 helix.db (v30) に追加**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.2 (dual-write start: `projection_state` CREATE TABLE IF NOT EXISTS) |
| 前提条件 | temp dir に v30 相当の helix.db が存在する |
| 実行手順 | `v31_db_separation.step_dual_write_start(conn)` を呼び出す |
| 期待結果 | `projection_state` table が helix.db に作成される |
| 検証項目 | 1. `SELECT name FROM sqlite_master WHERE name='projection_state'` が 1 件返る 2. PRIMARY KEY `(projector_id, db_name)` が設定されている |
| DoD | 上記検証項目が全て PASS |

---

**I-MIGRATION-003: migration script の再実行が idempotent (CREATE IF NOT EXISTS)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.1 (idempotent + additive 原則) |
| 前提条件 | I-MIGRATION-001/002 完了後の helix.db |
| 実行手順 | `v31_db_separation.step_dual_write_start(conn)` を **2 回** 連続呼び出す |
| 期待結果 | エラーなく完了し、table 重複エラーが発生しない |
| 検証項目 | 1. 例外が raise されない 2. `event_envelope` / `projection_state` table がそれぞれ 1 件のみ存在する |
| DoD | 上記検証項目が全て PASS |

---

### 2.2 6 db file 分離 step 検証 (gate 1 続き)

migration script の §6.3 step が 6 個の独立 db file を作成することを検証する。

---

**I-MIGRATION-004: 6 db ファイルが `.helix/` 配下に作成される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.3 (`step_create_6_dbs` で 6 db file を初期化) |
| 前提条件 | `.helix/` ディレクトリが存在する temp env |
| 実行手順 | `v31_db_separation.step_create_6_dbs(legacy_conn)` を呼び出す |
| 期待結果 | `.helix/orchestration.db` / `vmodel.db` / `scrum.db` / `plan.db` / `backend.db` / `frontend.db` の 6 ファイルが作成される |
| 検証項目 | 1. 6 ファイルが全て存在する (`os.path.exists`) 2. 各ファイルが SQLite db として接続可能 |
| DoD | 上記検証項目が全て PASS |

---

**I-MIGRATION-005: 各 db に D-DB-SEP §2.X の table が ATTACH 経由で作成される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §2.1〜§2.6 (各 db の table 定義) |
| 前提条件 | I-MIGRATION-004 完了後の 6 db ファイル環境 |
| 実行手順 | 各 db ファイルに接続し、`SELECT name FROM sqlite_master WHERE type='table'` を実行 |
| 期待結果 | 各 db に必要な table 群が存在する |
| 検証項目 (db 別) | orchestration.db: `phases` / `gates` / `agent_slots` / `harness_monitor_events` / `event_envelope` / `projection_state` が存在する。vmodel.db: `artifacts` / `artifact_links` / `cross_drive_integrity` / `event_envelope` が存在する。scrum.db: `hypotheses` / `scrum_loops` / `scrum_local_loops` / `event_envelope` が存在する。plan.db: `plans` / `sprints` / `tasks` / `plan_change_log` が存在する。backend.db: `automation_runs` / `audit_log` / `session_telemetry` が存在する。frontend.db: table なし (空 schema) として接続可能 |
| DoD | 全 db で 上記 table 存在確認が PASS |

---

**I-MIGRATION-006: 旧 helix.db と 6 db ファイルが coexist する (既存 table 破壊なし)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.1 (additive only 原則、既存 v30 table 破壊禁止) |
| 前提条件 | I-MIGRATION-004/005 完了後の環境 |
| 実行手順 | 旧 helix.db に接続し、v30 既存 table に SELECT を実行する |
| 期待結果 | 旧 helix.db の既存 table が全て維持されている |
| 検証項目 | 1. `agent_slots` / `automation_runs` / `audit_log` 等の v30 table が旧 helix.db に存在する 2. 旧 helix.db と 6 db ファイルが同時に接続可能 |
| DoD | 上記検証項目が全て PASS |

---

### 2.3 dual-write trigger 検証 (gate 2 前提)

compatibility_adapter が HELIX_DB_CUTOVER=0 の状態で両 db に write することを検証する。

---

**I-MIGRATION-007: compatibility_adapter が旧 helix.db と orchestration.db 両方に write する**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.1〜§2.3 (dual-write `_DualWriteConnection`) |
| 前提条件 | 旧 helix.db + orchestration.db が存在する temp env。`HELIX_DB_CUTOVER=0` |
| 実行手順 | `agent_slots.py` の `fire_slot` を呼び出す (compatibility_adapter 経由) |
| 期待結果 | `agent_slots` INSERT が旧 helix.db と orchestration.db の両方に記録される |
| 検証項目 | 1. 旧 helix.db の `agent_slots` に INSERT が存在する 2. orchestration.db の `agent_slots` に同一 `slot_id` で INSERT が存在する |
| DoD | 上記検証項目が全て PASS |

---

**I-MIGRATION-008: 11 file × 30+ callsite で dual-write が正しく routing される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §3 (11 file 別 routing 表) |
| 前提条件 | 6 db + 旧 helix.db が存在する temp env。`HELIX_DB_CUTOVER=0` |
| 実行手順 | D-API-SEP §3 の各 file (11 件) に対し、代表的な write callsite を 1〜2 件実行する |
| 期待結果 | 各 callsite が §3 の routing 先 db に write される |
| 検証項目 | 各 file / routing 先 db の pair が D-API-SEP §3 の表と一致する。以下は代表的な確認対象: `agent_slots.py` → orchestration.db / `push_pr.py` → backend.db / `scrum_local.py` → scrum.db / `audit.py` → backend.db |
| DoD | 11 file 全 routing 先が D-API-SEP §3 と一致 |

---

**I-MIGRATION-009: HELIX_DB_CUTOVER=0 で dual-write が維持される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.3 (cutover switch: `HELIX_DB_CUTOVER` 環境変数) |
| 前提条件 | 6 db + 旧 helix.db が存在する temp env |
| 実行手順 | `HELIX_DB_CUTOVER=0` を設定し、`agent_slots.fire_slot` を実行 |
| 期待結果 | 旧 helix.db と orchestration.db の両方に write される (`_DualWriteConnection` が起動する) |
| 検証項目 | 両 db に同一 `slot_id` の record が存在する |
| DoD | 上記検証項目が PASS |

---

### 2.4 cutover step 検証 (gate 5 対応)

HELIX_DB_CUTOVER=1 に切り替えた後、6 db のみへの write となることを検証する。

---

**I-MIGRATION-010: HELIX_DB_CUTOVER=1 で旧 helix.db への write が停止し 6 db のみへの write になる**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.3 (cutover 後: 6 db のみへ write) / D-DB-SEP §6.6 |
| 前提条件 | 6 db + 旧 helix.db が存在する temp env |
| 実行手順 | `HELIX_DB_CUTOVER=1` を設定し、`agent_slots.fire_slot` を実行 |
| 期待結果 | orchestration.db に write される。旧 helix.db には write されない |
| 検証項目 | 1. orchestration.db の `agent_slots` に新規 record が存在する 2. 旧 helix.db の `agent_slots` に同一 `slot_id` の record が存在しない |
| DoD | 上記検証項目が全て PASS |

---

**I-MIGRATION-011: cutover 後も既存 pytest 全 PASS が維持される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §1.1 (API 互換 100% 維持) / L1-REQUIREMENTS.md §3.9 NFR-03 |
| 前提条件 | `HELIX_DB_CUTOVER=1` 環境で全 pytest を実行可能な状態 |
| 実行手順 | `HELIX_DB_CUTOVER=1` 環境で `python3 -m pytest cli/lib/tests/ -q` を実行 |
| 期待結果 | 既存テストが全 PASS (PLAN-084 実装以前からのテストを含む) |
| 検証項目 | pytest の exit code = 0、FAILED = 0 |
| DoD | pytest 全 PASS |

---

### 2.5 rollback step 検証 (gate 6 対応)

cutover 後に HELIX_DB_CUTOVER=0 に戻すことで旧 helix.db への write が復活することを検証する。

---

**I-MIGRATION-012: HELIX_DB_CUTOVER=0 復帰で旧 helix.db への write が再開される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.7 (rollback step) / D-API-SEP §2.3 (cutover switch) |
| 前提条件 | `HELIX_DB_CUTOVER=1` で cutover 済みの環境 |
| 実行手順 | 1. `HELIX_DB_CUTOVER=1` で `fire_slot` を実行し cutover 後の動作を確認 2. `HELIX_DB_CUTOVER=0` に変更して `fire_slot` を実行 |
| 期待結果 | 手順 2 の実行後、旧 helix.db と orchestration.db の両方に write される |
| 検証項目 | 1. 手順 2 で生成した `slot_id` が旧 helix.db と orchestration.db の両方に存在する 2. 6 db ファイルは維持されている |
| DoD | 上記検証項目が全て PASS |

---

## §3 I-DUALWRITE-* 結合テスト設計

**対象設計**: D-DB-SEP §6.4 + ADR-018 §Decision.5 gate 2 (mismatch gate)
**テスト実装ファイル**: `cli/lib/tests/test_dual_write_mismatch.py` (Phase 4.B)

### 3.1 設計意図

dual-write 期間中 (HELIX_DB_CUTOVER=0) において、旧 helix.db と 6 db の write 結果が乖離していないかを継続的に検証する。gate 2 は「10000 write 連続で divergence 0 件」が PASS 条件 (D-DB-SEP §6.4)。本節のテストは gate 2 の検証ロジックと error injection 時の recovery を設計する。

---

**I-DUALWRITE-001: 旧 helix.db と新 6 db の write 結果が byte-level 一致する**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.3 (`_DualWriteConnection.execute`) |
| 前提条件 | temp env、`HELIX_DB_CUTOVER=0` |
| 実行手順 | `agent_slots.fire_slot(slot_id="test-001", role="tl")` を実行 |
| 期待結果 | 旧 helix.db と orchestration.db の `agent_slots` に同一 record が存在する |
| 検証項目 | `slot_id` / `role` / `status` / `fired_at` が byte-level で一致する (`==` 比較) |
| DoD | byte-level 一致が確認される |

---

**I-DUALWRITE-002: mismatch が 1 件でも検出された場合に mismatch gate が fail-close する**

| 項目 | 内容 |
|---|---|
| 対象設計 | ADR-018 §Decision.5 gate 2 (divergence 検出 → fail-close) |
| 前提条件 | dual-write mismatch 検出ロジックが実装済みの状態 |
| 実行手順 | 1. 旧 helix.db の record を直接 UPDATE して人工的な mismatch を作成 2. mismatch gate checker を呼び出す |
| 期待結果 | mismatch gate が fail-close を返す |
| 検証項目 | 1. mismatch gate の戻り値が `FAIL` または `False` 2. `harness_monitor_events` に mismatch 記録が INSERT される |
| DoD | 上記検証項目が全て PASS |

---

**I-DUALWRITE-003: 10000 write 連続で divergence 0 件 → gate 2 PASS**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.4 (10000 write 連続、divergence 0 件 が gate 2 PASS 条件) |
| 前提条件 | temp env、`HELIX_DB_CUTOVER=0`。error injection なし |
| 実行手順 | 10000 回の write (INSERT / UPDATE 混在) を compatibility_adapter 経由で実行し、全件で mismatch 検証を行う |
| 期待結果 | divergence 0 件で gate 2 PASS |
| 検証項目 | 1. 全 10000 write で旧 helix.db と 6 db の record が一致する 2. mismatch gate の戻り値が `PASS` |
| 備考 | 10000 write は CI 環境での実行時間を考慮し、100 write 連続 × 100 batch で分割実行してもよい。CI 短縮設計は Phase 4.B carry (§8 carry #4) |
| DoD | gate 2 PASS が確認される |

---

**I-DUALWRITE-004: sqlite3.OperationalError 発生時の recovery (新 6 db 側エラー)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.5 (error handling: 新 6 db 失敗 → WARN、処理継続) |
| 前提条件 | temp env、`HELIX_DB_CUTOVER=0` |
| 実行手順 | orchestration.db への write で `sqlite3.OperationalError` を inject (`mock.patch`) し、`fire_slot` を呼び出す |
| 期待結果 | 旧 helix.db への write は成功し、WARN ログが出力される。呼び出し元への例外は発生しない |
| 検証項目 | 1. 旧 helix.db に record が存在する 2. logger.warning が呼ばれた (mock で確認) 3. 例外が呼び出し元に伝播しない |
| DoD | 上記検証項目が全て PASS |

---

**I-DUALWRITE-005: sqlite3.IntegrityError 発生時の recovery (新 6 db 側エラー)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.5 (error handling: IntegrityError も WARN 扱い) |
| 前提条件 | temp env、`HELIX_DB_CUTOVER=0` |
| 実行手順 | orchestration.db への write で `sqlite3.IntegrityError` を inject し、`fire_slot` を呼び出す |
| 期待結果 | 旧 helix.db への write は成功し、WARN ログが出力される |
| 検証項目 | 1. 旧 helix.db に record が存在する 2. logger.warning が呼ばれた |
| DoD | 上記検証項目が全て PASS |

---

**I-DUALWRITE-006: connection drop (新 6 db 側) での recovery**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.5 (新 6 db write 失敗は WARN 止まり) |
| 前提条件 | temp env、`HELIX_DB_CUTOVER=0` |
| 実行手順 | orchestration.db への接続を `mock.patch` で強制失敗させ (`side_effect=Exception("connection dropped")`)、`fire_slot` を呼び出す |
| 期待結果 | 旧 helix.db への write は成功し、WARN ログが出力される |
| 検証項目 | 1. 旧 helix.db に record が存在する 2. logger.warning が呼ばれた |
| DoD | 上記検証項目が全て PASS |

---

**I-DUALWRITE-007: divergence 検出時に harness_monitor_events へ record が INSERT される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §4.3 (lag 監視: WARN → `harness_monitor_events` に record) |
| 前提条件 | dual-write mismatch 検出ロジック + harness_monitor_events table が実装済みの状態 |
| 実行手順 | 人工的な mismatch を作成し、mismatch checker を呼び出す |
| 期待結果 | `orchestration.db` の `harness_monitor_events` に divergence record が INSERT される |
| 検証項目 | 1. `harness_monitor_events` に `event_type='dualwrite_divergence'` の record が存在する 2. record の `payload` に `target_db` と `slot_id` (または相当の識別子) が含まれる |
| DoD | 上記検証項目が全て PASS |

---

**I-DUALWRITE-008: divergence 解消後の retry で gate 2 通過**

| 項目 | 内容 |
|---|---|
| 対象設計 | ADR-018 §Decision.5 gate 2 (divergence 解消 → gate retry) |
| 前提条件 | I-DUALWRITE-002 で fail-close した状態 |
| 実行手順 | 1. mismatch を修正 (旧 helix.db を 6 db と同期) 2. mismatch gate checker を再実行 |
| 期待結果 | gate 2 が PASS を返す |
| 検証項目 | gate checker の戻り値が `PASS` |
| DoD | gate 2 retry PASS が確認される |

---

## §4 I-REPLAY-* 結合テスト設計

**対象設計**: D-DB-SEP §6.5 + ADR-018 §Decision.5 gate 3 (shadow replay)
**テスト実装ファイル**: `cli/lib/tests/test_shadow_replay.py` (Phase 4.C)

### 4.1 設計意図

shadow replay は、過去 N 件の event を新 projector で再生 (replay) し、derived state が旧 helix.db の state と byte-level で一致するかを検証するゲートである (D-DB-SEP §6.5)。gate 3 PASS 条件は「過去 1000 event replay 全 PASS (24h 連続)」。本節のテストは replay の正確性・idempotency・lag 監視を設計する。

---

**I-REPLAY-001: 過去 1000 event を新 projector で replay → derived state が byte-level 一致**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.5 (`step_shadow_replay` + gate 3 PASS 条件) |
| 前提条件 | orchestration.db に 1000 件の event_envelope が INSERT 済みの temp env。projector が実装済み |
| 実行手順 | `step_shadow_replay(legacy_conn, orchestration_conn, replay_limit=1000)` を呼び出す |
| 期待結果 | replay 完了し、例外なし |
| 検証項目 | 1. projector が生成した derived state の `status` / `count` 等が旧 helix.db の state と一致する 2. 戻り値または gate 判定が PASS |
| DoD | byte-level 一致確認が全 1000 event で PASS |

---

**I-REPLAY-002: orchestration.db の event replay が正確**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §2.1 (orchestration.db の event-sourced 設計) |
| 前提条件 | orchestration.db に `phase.transitioned` / `gate.passed` event を 100 件 INSERT した temp env |
| 実行手順 | `phase_projector` を起動し、event を ORDER BY `event_id` で replay する |
| 期待結果 | `projection_state` の snapshot が最終 phase 状態を正しく反映する |
| 検証項目 | 1. `projection_state.snapshot` の `current_phase` が最後に INSERT した `phase.transitioned` event の `to_phase` と一致する 2. gate 通過数が INSERT した `gate.passed` event 数と一致する |
| DoD | 上記検証項目が全て PASS |

---

**I-REPLAY-003: vmodel.db の event replay が正確**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §2.2 (vmodel.db の event-sourced 設計) |
| 前提条件 | vmodel.db に `artifact.created` / `artifact.linked` event を 50 件 INSERT した temp env |
| 実行手順 | vmodel projector を起動し、event を replay する |
| 期待結果 | `artifacts` snapshot が INSERT された artifact 数と一致する |
| 検証項目 | 1. snapshot の artifact count が INSERT 件数と一致する 2. artifact_link の trace が正しく復元される |
| DoD | 上記検証項目が全て PASS |

---

**I-REPLAY-004: scrum.db の event replay が正確**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §2.3 (scrum.db の event-sourced 設計) |
| 前提条件 | scrum.db に `hypothesis.confirmed` / `scrum_loop.started` event を 30 件 INSERT した temp env |
| 実行手順 | scrum projector を起動し、event を replay する |
| 期待結果 | `hypotheses` snapshot が INSERT された hypothesis の最終 status を反映する |
| 検証項目 | snapshot の `confirmed_count` が INSERT した `hypothesis.confirmed` event 数と一致する |
| DoD | 上記検証項目が PASS |

---

**I-REPLAY-005: projector idempotency (同 event を 2 回 replay しても結果が同一)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.5 (replay は idempotent であること) |
| 前提条件 | I-REPLAY-002 完了後の orchestration.db |
| 実行手順 | `phase_projector` を **2 回** 連続で replay する |
| 期待結果 | 2 回目の replay 後も snapshot が 1 回目と同一 |
| 検証項目 | 1. 2 回目の replay で例外が発生しない 2. `projection_state.snapshot` が 1 回目と同一の JSON |
| DoD | 上記検証項目が全て PASS |

---

**I-REPLAY-006: replay 中の lag 監視 (last_processed_event_id の更新確認)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §4.3 (lag 監視: `last_processed_event_id` 更新) |
| 前提条件 | orchestration.db に 100 件の event_envelope が存在する temp env |
| 実行手順 | `phase_projector` を replay 中に `projection_state.last_processed_event_id` を観測する |
| 期待結果 | replay 完了後に `last_processed_event_id` が最新 `event_id` と一致する |
| 検証項目 | 1. replay 開始前の `last_processed_event_id` と完了後の値が変化している 2. 完了後の値が event_envelope の最大 `event_id` と一致する |
| DoD | 上記検証項目が全て PASS |

---

**I-REPLAY-007: replay 不一致時に fail-close (projector bug 模擬後 retry)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-DB-SEP §6.5 (replay 不一致 → fail-close、cutover 不可) |
| 前提条件 | orchestration.db に 100 件の event_envelope が存在し、projector に意図的なバグを inject した状態 |
| 実行手順 | 1. バグ注入 projector で replay し、不一致を生成 2. gate 3 checker を呼び出す |
| 期待結果 | gate 3 が fail-close を返す |
| 検証項目 | 1. gate 3 の戻り値が `FAIL` 2. projector バグ修正後に retry で PASS になること |
| DoD | fail-close → retry PASS の流れが確認される |

---

**I-REPLAY-008: gate 3 PASS = 過去 1000 event replay 全 PASS の判定**

| 項目 | 内容 |
|---|---|
| 対象設計 | ADR-018 §Decision.5 gate 3 (PASS 条件: 過去 1000 event replay 全 PASS) |
| 前提条件 | orchestration.db / vmodel.db / scrum.db に合計 1000 件の event_envelope が存在する temp env |
| 実行手順 | 3 db の projector を順次 replay し、gate 3 checker を呼び出す |
| 期待結果 | gate 3 PASS を返す |
| 検証項目 | gate 3 checker の戻り値が `PASS` |
| 備考 | 24h 連続 PASS の CI 短縮設計は Phase 4.C carry (§8 carry #5) |
| DoD | gate 3 PASS が確認される |

---

## §5 I-CORR-* 結合テスト設計

**対象設計**: D-CONTRACT-EVENT-draft §4 (correlation_id 発行・継承・cross-db trace)
**テスト実装ファイル**: `cli/lib/tests/test_correlation_cross_db.py` (Phase 4.B)

### 5.1 設計意図

`correlation_id` は cross-db trace の必須フィールドである (ADR-018 §Decision.1)。orchestration.db で発行された `correlation_id` が、同一 CLI command 内で vmodel.db / scrum.db に継承され、後から `SELECT * WHERE correlation_id = ?` で 3 db を横断検索できることを検証する。

---

**I-CORR-001: orchestration.db で correlation_id を発行 → vmodel.db に継承される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-CONTRACT-EVENT §4.2 (発行ルール: orchestration で発行、他 db は継承) |
| 前提条件 | orchestration.db + vmodel.db が存在する temp env。`correlation_context` が実装済み |
| 実行手順 | `with correlation_context() as corr_id:` ブロック内で orchestration.db と vmodel.db の両方に event を書き込む |
| 期待結果 | orchestration.db と vmodel.db の event_envelope が同一 `correlation_id` を持つ |
| 検証項目 | 1. orchestration.db の event の `correlation_id` が `corr_id` と一致する 2. vmodel.db の event の `correlation_id` が同一の `corr_id` と一致する |
| DoD | 上記検証項目が全て PASS |

---

**I-CORR-002: 同一 CLI command 内の全 event が同一 correlation_id を共有する**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-CONTRACT-EVENT §4.2 (同一 request 内の全 event は同一 correlation_id を持つ) |
| 前提条件 | 3 db が存在する temp env |
| 実行手順 | 1 つの `correlation_context()` ブロック内で orchestration / vmodel / scrum の 3 db に各 1 件の event を書き込む |
| 期待結果 | 3 件すべての event が同一 `correlation_id` を持つ |
| 検証項目 | 各 db の event_envelope の `correlation_id` が全て同一 |
| DoD | 上記検証項目が PASS |

---

**I-CORR-003: cross-db query で 2 db を横断して correlation_id 検索ができる**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-CONTRACT-EVENT §4.4 (cross-db trace 具体例) |
| 前提条件 | I-CORR-001 完了後の orchestration.db + vmodel.db |
| 実行手順 | orchestration.db と vmodel.db に対し `SELECT * FROM event_envelope WHERE correlation_id = ?` を各々実行し結果を結合する |
| 期待結果 | 2 db から合計 2 件 (各 1 件) の event が取得される |
| 検証項目 | 1. orchestration.db から 1 件、vmodel.db から 1 件が取得される 2. 両件の `correlation_id` が同一 |
| DoD | 上記検証項目が全て PASS |

---

**I-CORR-004: thread 分離 (別 thread で別 correlation_id が発行される)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-CONTRACT-EVENT §4.3 (correlation_context: thread-local で管理) |
| 前提条件 | 2 thread が並行して `correlation_context()` ブロックを実行できる状態 |
| 実行手順 | Thread A と Thread B が同時に `correlation_context()` を起動し、各 thread で orchestration.db に event を書き込む |
| 期待結果 | Thread A と Thread B の event が異なる `correlation_id` を持つ |
| 検証項目 | Thread A と Thread B の `correlation_id` が不一致 (`!=`) |
| DoD | 上記検証項目が PASS |

---

**I-CORR-005: nested context (parent context 内で child context が parent の correlation_id を継承)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-CONTRACT-EVENT §4.3 (nested context: `parent` 引数で継承) |
| 前提条件 | `correlation_context(parent=...)` が実装済みの状態 |
| 実行手順 | `with correlation_context() as parent_id:` の中に `with correlation_context(parent=parent_id) as child_id:` をネストして実行 |
| 期待結果 | `child_id == parent_id` (parent の correlation_id が継承される) |
| 検証項目 | `child_id == parent_id` |
| DoD | 上記検証項目が PASS |

---

**I-CORR-006: cross-db query helper (read_cross_db_projection) と correlation trace の統合**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §4.1 (`read_cross_db_projection`) + D-CONTRACT-EVENT §4.4 (統合点の区別) |
| 前提条件 | orchestration.db に projection_state が存在し、event_envelope に correlation_id 付き event が存在する temp env |
| 実行手順 | 1. `read_cross_db_projection("phase_projector", "orchestration")` で snapshot を取得 2. 同一 `correlation_id` で `SELECT * FROM event_envelope` を実行 |
| 期待結果 | projection_state 経由の参照と event trace が独立して機能する (用途が異なる) |
| 検証項目 | 1. `read_cross_db_projection` が snapshot dict を返す 2. event trace が `correlation_id` で event を返す 3. 両者が相互に干渉しない (ATTACH を使用しない) |
| DoD | 上記検証項目が全て PASS |

---

## §6 I-SMOKE-* 結合テスト設計

**対象設計**: D-API-SEP §3 (11 file routing、top-level CLI 3 件) + tl-advisor Round 1-3 助言 (CLI smoke 必須化)
**テスト実装ファイル**: `cli/tests/db_separation_smoke.bats` (Phase 4.A)

### 6.1 設計意図

tl-advisor は 3 ラウンドの review を通じて top-level CLI 3 件 (helix-pr / helix-push / helix-agent) の smoke test を必須化した。これらは D-API-SEP §3 の #9 / #10 / #11 に対応し、CLI 実行経路が compatibility_adapter を経由して正しい 6 db に到達することを end-to-end で確認する。

### 6.2 mock 戦略 (bats 固有)

```bash
# bats の共通 setup
setup() {
  export HELIX_HOME="$BATS_TMPDIR/.helix"
  mkdir -p "$HELIX_HOME"
  # temp helix.db を v30 相当に初期化
  python3 -c "import sys; sys.path.insert(0, 'cli/lib'); from helix_db import migrate_all; migrate_all('$HELIX_HOME/helix.db')"
  # 6 db 分離 migration を実行
  python3 -c "from migrations.v31_db_separation import run; run('$HELIX_HOME/helix.db', '$HELIX_HOME')"
  export HELIX_DB="$HELIX_HOME/helix.db"
  export HELIX_DB_CUTOVER="0"
}
```

---

**I-SMOKE-001: helix-pr で PR 作成 → backend.db の automation_run に record が作成される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §3 #9 (`helix-pr` → backend.db routing) |
| 前提条件 | bats setup 完了。`HELIX_DB_CUTOVER=0` |
| 実行手順 | `run cli/helix-pr create --plan-id PLAN-084 --branch test-branch` (または相当のサブコマンド) |
| 期待結果 | exit code 0 かつ backend.db の `automation_runs` に `run_kind='pr'` の record が INSERT される |
| 検証項目 | `sqlite3 $HELIX_HOME/backend.db "SELECT run_kind FROM automation_runs WHERE run_kind='pr'"` が 1 件以上返す |
| DoD | 上記検証項目が PASS |

---

**I-SMOKE-002: helix-push で push event → backend.db の automation_run に record が作成される**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §3 #10 (`helix-push` → backend.db routing) |
| 前提条件 | bats setup 完了。`HELIX_DB_CUTOVER=0` |
| 実行手順 | `run cli/helix-push` (または相当のサブコマンド) |
| 期待結果 | exit code 0 かつ backend.db の `automation_runs` に `run_kind='push'` の record が INSERT される |
| 検証項目 | `sqlite3 $HELIX_HOME/backend.db "SELECT run_kind FROM automation_runs WHERE run_kind='push'"` が 1 件以上返す |
| DoD | 上記検証項目が PASS |

---

**I-SMOKE-003: helix-agent list で agent_slots を SELECT → orchestration.db からの読み出し**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §3 #11 (`helix-agent` → orchestration.db routing、read-only path) |
| 前提条件 | bats setup 完了。orchestration.db の `agent_slots` に 1 件 INSERT 済み |
| 実行手順 | `run cli/helix-agent list` |
| 期待結果 | exit code 0 かつ output に agent_slot の情報が含まれる |
| 検証項目 | 1. exit code = 0 2. output に `slot_id` または `role` が含まれる |
| DoD | 上記検証項目が PASS |

---

**I-SMOKE-004: 3 CLI 連続実行で API 互換 100% 維持 (既存 bats 全 PASS)**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §1.1 (API 互換 100% 維持) / L1-REQUIREMENTS.md §3.9 NFR-03 |
| 前提条件 | bats setup 完了。`HELIX_DB_CUTOVER=0` |
| 実行手順 | `helix-pr` → `helix-push` → `helix-agent list` の順で 3 CLI を連続実行する |
| 期待結果 | 3 CLI すべてが exit code 0 で完了する |
| 検証項目 | 3 コマンドの exit code がすべて 0 |
| DoD | 全 PASS |

---

**I-SMOKE-005: dual-write 期間中 (HELIX_DB_CUTOVER=0) の 3 CLI 動作確認**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.3 (dual-write 期間中の I/O 経路) |
| 前提条件 | bats setup 完了。`HELIX_DB_CUTOVER=0` |
| 実行手順 | I-SMOKE-001〜003 と同じ 3 CLI を `HELIX_DB_CUTOVER=0` 環境で実行 |
| 期待結果 | 旧 helix.db と対応する 6 db の両方に record が存在する |
| 検証項目 | `helix-pr` 実行後: 旧 helix.db と backend.db の両方に `automation_runs` の record が存在する |
| DoD | 上記検証項目が PASS |

---

**I-SMOKE-006: cutover 後 (HELIX_DB_CUTOVER=1) の 3 CLI 動作確認**

| 項目 | 内容 |
|---|---|
| 対象設計 | D-API-SEP §2.3 (cutover 後: 6 db のみへ write) |
| 前提条件 | bats setup 完了。`HELIX_DB_CUTOVER=1` |
| 実行手順 | I-SMOKE-001〜003 と同じ 3 CLI を `HELIX_DB_CUTOVER=1` 環境で実行 |
| 期待結果 | 6 db に record が存在し、旧 helix.db には新規 write がない |
| 検証項目 | `helix-pr` 実行後: backend.db に record が存在し、旧 helix.db の該当 table に新規 record が存在しない |
| DoD | 上記検証項目が PASS |

---

## §7 V-model 双方向 trace まとめ

| L3 設計 doc | セクション | 結合テスト case | テスト実装 file | Phase |
|---|---|---|---|---|
| D-DB-SEP-draft §6.2 (dual-write start) | §2.1 | I-MIGRATION-001〜003 | `test_db_separation_integration.py` | 4.A |
| D-DB-SEP-draft §6.3 (6 db 分離) | §2.2 | I-MIGRATION-004〜006 | `test_db_separation_integration.py` | 4.A |
| D-API-SEP-draft §2.1〜§2.3 (dual-write) | §2.3 | I-MIGRATION-007〜009 | `test_db_separation_integration.py` | 4.A |
| D-DB-SEP-draft §6.6 / D-API-SEP §2.3 (cutover) | §2.4 | I-MIGRATION-010〜011 | `test_db_separation_integration.py` | 4.A/4.C |
| D-DB-SEP-draft §6.7 (rollback) | §2.5 | I-MIGRATION-012 | `test_db_separation_integration.py` | 4.C |
| D-DB-SEP-draft §6.4 + ADR-018 §Decision.5 gate 2 | §3 | I-DUALWRITE-001〜008 | `test_dual_write_mismatch.py` | 4.B |
| D-DB-SEP-draft §6.5 + ADR-018 §Decision.5 gate 3 | §4 | I-REPLAY-001〜008 | `test_shadow_replay.py` | 4.C |
| D-CONTRACT-EVENT-draft §4 (correlation) | §5 | I-CORR-001〜006 | `test_correlation_cross_db.py` | 4.B |
| D-API-SEP-draft §3 (11 file routing + CLI 3 件) | §6 | I-SMOKE-001〜006 | `db_separation_smoke.bats` | 4.A |

**case 数集計**:

| prefix | case 数 |
|---|---|
| I-MIGRATION | 12 件 |
| I-DUALWRITE | 8 件 |
| I-REPLAY | 8 件 |
| I-CORR | 6 件 |
| I-SMOKE | 6 件 |
| **合計** | **40 件** |

---

## §8 carry to Phase 4

| # | carry 項目 | Phase | 担当 | 依存 |
|---|---|---|---|---|
| 1 | test 実装本体 (I-MIGRATION-001〜009、I-SMOKE-001〜006) | 4.A | Codex qa | `v31_db_separation.py` + `compatibility_adapter.py` 実装完了 |
| 2 | test 実装本体 (I-DUALWRITE-001〜008、I-CORR-001〜006) | 4.B | Codex qa | dual-write mismatch checker + `correlation_context` 実装完了 |
| 3 | test 実装本体 (I-REPLAY-001〜008、I-MIGRATION-010〜012) | 4.C | Codex qa | shadow replay projector + cutover/rollback script 実装完了 |
| 4 | dual-write gate 2 PASS 条件 (10000 write 連続) の CI 短縮設計 | 4.B | Codex qa | I-DUALWRITE-003 は 100 write × 100 batch 分割 or CI 専用 fixture |
| 5 | shadow replay 24h gate 3 PASS の CI 短縮 soak 設計 | 4.C | Codex qa | CI で 24h → 1000 event replay に短縮する判断は Phase 4.C で確定 |
| 6 | error injection framework の共通 fixture 化 | 4.B | Codex qa | `sqlite3.OperationalError` / `IntegrityError` / connection drop を共通 `@pytest.fixture` として切り出す |
| 7 | top-level CLI smoke の既存 bats 統合 (cli/tests/*.bats 既存 PASS 維持を CI gate 化) | 4.A | Codex qa | `db_separation_smoke.bats` と既存 `helix-agent.bats` / `helix-push.bats` の衝突確認 |

---

## §9 References

| 文書 | 参照箇所 | 本文書との関係 |
|---|---|---|
| `docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md` §6 | migration step 7 段階 (gate 1〜6) | 本文書 §2 (I-MIGRATION-*) の根拠 |
| `docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md` §2〜§3 | dual-write + 11 file routing | 本文書 §2.3〜§2.4 + §6 (I-SMOKE-*) の根拠 |
| `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` §4 | correlation_id 発行・継承・thread-local | 本文書 §5 (I-CORR-*) の根拠 |
| `docs/adr/ADR-018-db-separation-and-event-sourcing.md` §Decision.5 | gate 2/3 (mismatch gate / shadow replay) の PASS 条件 | 本文書 §3 + §4 の gate 判定基準の根拠 |
| `docs/v2/L4-test-design/PLAN-074-integration-test-design.md` | frontmatter / 章立て pattern | 本文書の構造 template として参照 |
| `docs/v2/L4-test-design/PLAN-078-integration-test-design.md` | bats mock 戦略・CLI 結合テスト pattern | 本文書 §6 の bats setup pattern の参考 |
| `helix/HELIX_CORE.md` §V-model 4 artifact 双方向 trace 原則 | 4 artifact 別文書化 + 双方向 reference ルール | 本文書全体の設計原則の根拠 |
| `docs/v2/L1-REQUIREMENTS.md` §3.9 AC-DB-SEP-01〜07 | 受入条件 7 件 | 本文書 §1.6 の case ↔ AC 対応表の根拠 |
