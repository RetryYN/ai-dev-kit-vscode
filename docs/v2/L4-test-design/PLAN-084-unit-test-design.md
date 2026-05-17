---
doc_id: PLAN-084-unit-test-design-v0.1
plan_id: PLAN-084
sprint: Phase 3.4 / L3-L4 単体テスト設計
status: draft
created: 2026-05-17
primary_drive: be
test_layer: L4 単体テスト設計 (V-model 4 artifact ③)
related_designs:
  - D-DB-SEP-draft-v0.1 (本 doc が対応する schema 設計、双方向 trace)
  - D-API-SEP-draft-v0.1 (本 doc が対応する adapter API 設計、双方向 trace)
  - D-CONTRACT-EVENT-draft-v0.1 (本 doc が対応する event class 設計、双方向 trace)
related_test_implementations:
  - cli/lib/tests/test_compatibility_adapter.py (Phase 4.A 起票予定、本 doc U-ADAPTER-* を実装)
  - cli/lib/tests/test_event_envelope_unit.py (Phase 4.B 起票予定、本 doc U-EVT-* を実装)
  - cli/lib/tests/test_uuid_v7_generator.py (Phase 4.A 起票予定、本 doc U-UUID-* を実装)
  - cli/lib/tests/test_correlation_context.py (Phase 4.B 起票予定、本 doc U-CORR-* を実装)
---

> **V-model 4 artifact 位置付け** (PLAN-075):
> 本書は ③ テスト設計 artifact。① 設計 (D-DB-SEP / D-API-SEP / D-CONTRACT-EVENT) と
> ④ テストコード (test_compatibility_adapter.py / test_event_envelope_unit.py 等) を
> 双方向 trace で繋ぐ独立文書。① 設計文書や ④ テストコードと同一 doc に統合しない。

# PLAN-084 Phase 3: L3-L4 単体テスト設計 (6 db 分離 + Event Sourcing)

---

## §1 目的とスコープ

### 1.1 本文書の位置づけ

本文書は PLAN-084 (helix.db 6 分離 + Event Sourcing + projector) の **単体テスト設計書 (③ artifact)** である。

Phase 4.A/4.B で実装する単体テスト群の設計を確定し、Codex qa が本文書を参照して `test_*.py` ファイルを実装する。V-model 4 artifact の双方向 trace 原則 (HELIX_CORE.md §設計⇔テスト対応) に従い、3 件の L3 詳細設計ドキュメント (D-DB-SEP / D-API-SEP / D-CONTRACT-EVENT) に対応した単体テスト case を設計する。

### 1.2 4 artifact 構造 (HELIX_CORE.md §V-model 4 artifact 双方向 trace)

```
① 設計 (D-DB-SEP / D-API-SEP / D-CONTRACT-EVENT)  ←対応関係→  ③ テスト設計 (本 doc)
        ↓ 実装                                                      ↓ 実装
② 実装コード (compatibility_adapter.py / event_envelope.py 等)  ←対応→  ④ テストコード (test_*.py)
```

| Artifact | 担当層 | ファイル |
|---|---|---|
| ① 設計 | L3 詳細設計 | D-DB-SEP-draft.md / D-API-SEP-draft.md / D-CONTRACT-EVENT-draft.md |
| ② 実装コード | Phase 4.A/4.B 実装 | cli/lib/compatibility_adapter.py / cli/lib/event_envelope.py 等 |
| **③ テスト設計 (本 doc)** | **L3-L4 単体テスト設計** | **docs/v2/L4-test-design/PLAN-084-unit-test-design.md** |
| ④ テストコード | Phase 4.A/4.B 実装 | cli/lib/tests/test_compatibility_adapter.py 等 |

### 1.3 対象コンポーネント

本文書がカバーする単体テスト対象:

| コンポーネント | 設計根拠 | 実装 Phase | テスト設計節 |
|---|---|---|---|
| `compatibility_adapter.py` (write_connection / _route_to_db / _DualWriteConnection) | D-API-SEP-draft §2/3/4 | Phase 4.A | §2 (U-ADAPTER-*) |
| `EventEnvelope` dataclass (frozen / to_sqlite_row / from_sqlite_row / db_name validation) | D-CONTRACT-EVENT-draft §2/5/6 | Phase 4.B | §3 (U-EVT-*) |
| UUID v7 generator (`generate_event_id`) | D-CONTRACT-EVENT-draft §3 | Phase 4.A | §4 (U-UUID-*) |
| `correlation_context` context manager | D-CONTRACT-EVENT-draft §4 | Phase 4.B | §5 (U-CORR-*) |

### 1.4 Non-goals (本文書の対象外)

以下は本文書の対象外とし、別の設計文書で扱う:

- **結合テスト**: `PLAN-084-integration-test-design.md` (Phase 4.A/4.B 着手時に起票予定)
  - migration v30 → v31 の schema 変更全体テスト
  - 6 db 物理分離後の cross-db routing 結合テスト
  - projector lag 監視の結合テスト
- **E2E / smoke test**: `cli/tests/db_separation_smoke.bats` (Phase 4.A carry、D-API-SEP §7 #5)
  - top-level CLI (helix-pr / helix-push / helix-agent) 経由の bats test
- **shadow replay test**: Phase 4.C 実装対象 (D-DB-SEP §7 carry #7)
- **projector 実装本体のテスト**: Phase 4.B 設計 (cli/lib/projectors/*.py)

### 1.5 テストピラミッド上の位置

```
        E2E / smoke (Phase 4.A、bats × top-level CLI 3 件)
       /                   \
      / Integration tests   \  ← PLAN-084-integration-test-design.md (Phase 4.A/4.B 予定)
     /______________________ \
    /                        \
   /   Unit tests (本 doc)    \  ← 計 35+ cases (U-ADAPTER/EVT/UUID/CORR)
  /____________________________ \
```

---

## §2 U-ADAPTER-* 単体テスト設計 (compatibility_adapter.py 対応)

### 対応設計

- D-API-SEP-draft-v0.1 §2 (write_connection API / routing 規則 / dual-write 制御)
- D-API-SEP-draft-v0.1 §3 (11 file 別 adapter 動作表)
- D-API-SEP-draft-v0.1 §4 (cross-db read helper)
- D-API-SEP-draft-v0.1 §5 (ATTACH 禁止 CI gate)

**テストコード (④ artifact)**: `cli/lib/tests/test_compatibility_adapter.py` (Phase 4.A 起票予定)

**テスト方針**: SQLite の `:memory:` または tmpdir の `.db` ファイルを使い、実 I/O で 6 db routing を検証する。`inspect.stack` を経由する caller 判定は monkeypatch で対象 module の basename を差し替えて検証する (tl-advisor L3 review P3 反映: ラッパー / monkeypatch 後も caller 判定がずれないことを受入条件に明示)。

### 受入条件 (全 U-ADAPTER-* 共通)

- monkeypatch や contextmanager ラッパー適用後も `_route_to_db` の caller 判定がずれない
- dual-write 期間 (HELIX_DB_CUTOVER 未設定) と cutover 後 (HELIX_DB_CUTOVER=1) を環境変数で切り替えて検証できる
- 旧 helix.db (legacy) と新 6 db の write が独立した SQLite file (tmpdir) で確認できる

---

#### U-ADAPTER-001: orchestration.db routing (agent_slots.py)

- **対象**: D-API-SEP §2.2 `_FILE_TO_DB` mapping + D-API-SEP §3 #1
- **入力**: `caller_file = "agent_slots.py"`, `caller_func = "fire_slot"`
- **期待**: `_route_to_db("agent_slots.py", "fire_slot")` → `"orchestration"`
- **受入条件**: mapping 変更なしで `"orchestration"` が返る。monkeypatch 後も同じ結果

#### U-ADAPTER-002: scrum.db routing (scrum_local.py)

- **対象**: D-API-SEP §2.2 `_FILE_TO_DB` mapping + D-API-SEP §3 #3
- **入力**: `caller_file = "scrum_local.py"`, `caller_func = "add_local_hypothesis"`
- **期待**: `_route_to_db(...)` → `"scrum"`
- **受入条件**: `"scrum"` が返る

#### U-ADAPTER-003: backend.db routing (http_api/routes/audit.py)

- **対象**: D-API-SEP §2.2 `_FILE_TO_DB` mapping + D-API-SEP §3 #5
- **入力**: `caller_file = "audit.py"`, `caller_func = "post_audit"`
- **期待**: `_route_to_db(...)` → `"backend"`
- **受入条件**: `"backend"` が返る

#### U-ADAPTER-004: backend.db routing (top-level CLI helix-push)

- **対象**: D-API-SEP §2.2 `_FILE_TO_DB` mapping + D-API-SEP §3 #10
- **入力**: `caller_file = "helix-push"`, `caller_func = "record_push"`
- **期待**: `_route_to_db(...)` → `"backend"`
- **受入条件**: `"backend"` が返る

#### U-ADAPTER-005: orchestration.db routing (top-level CLI helix-agent)

- **対象**: D-API-SEP §2.2 `_FILE_TO_DB` mapping + D-API-SEP §3 #11
- **入力**: `caller_file = "helix-agent"`, `caller_func = "list_slots"`
- **期待**: `_route_to_db(...)` → `"orchestration"`
- **受入条件**: `"orchestration"` が返る

#### U-ADAPTER-006: dual-write 期間中 — legacy + 新 6 db 両方 write (HELIX_DB_CUTOVER 未設定)

- **対象**: D-API-SEP §2.1 write_connection (dual-write path) + §2.3 `_DualWriteConnection`
- **入力**: `HELIX_DB_CUTOVER` 未設定、`caller_file = "agent_slots.py"`
- **期待**: `write_connection()` context に入ると `_DualWriteConnection` が返る。legacy (旧 helix.db tmpdir) と new (orchestration.db tmpdir) の両方に `INSERT` が到達する
- **受入条件**: legacy_conn と new_conn の両方に同じ row が存在する。execute() の戻り値 (lastrowid) は legacy_conn のものと一致する

#### U-ADAPTER-007: dual-write 期間中 — 新 db write 失敗は WARN のみ (legacy は成功)

- **対象**: D-API-SEP §2.3 `_DualWriteConnection.execute()` error handling + §2.5
- **入力**: new_conn に壊れた DB (read-only filesystem など) を設定して INSERT 失敗を注入
- **期待**: 例外は raise されず、legacy_conn への INSERT は成功する。WARN log が出力される
- **受入条件**: legacy DB に row が存在する。新 DB にエラーログが残る。呼び出し元に例外が伝播しない

#### U-ADAPTER-008: dual-write 期間中 — legacy db write 失敗は critical (例外 raise)

- **対象**: D-API-SEP §2.5 error handling (legacy write failure = critical)
- **入力**: legacy_conn に壊れた DB を設定して INSERT 失敗を注入
- **期待**: 例外が呼び出し元に伝播する (critical raise)
- **受入条件**: 例外が `except` で捕捉できる。新 db への write は行われない (または rollback される)

#### U-ADAPTER-009: dual-write 期間中 — executemany も dual-write

- **対象**: D-API-SEP §2.3 `_DualWriteConnection.executemany()`
- **入力**: `HELIX_DB_CUTOVER` 未設定、`executemany(sql, [(row1,), (row2,)])` を呼び出す
- **期待**: legacy と new の両方に 2 row INSERT される。WARN なし (成功時)
- **受入条件**: legacy / new 両 DB の row count が 2

#### U-ADAPTER-010: dual-write 期間中 — cutover フラグで 6 db のみ (helix.db への write 停止)

- **対象**: D-API-SEP §2.1 write_connection (cutover path) + §2.3 切替制御表
- **入力**: `HELIX_DB_CUTOVER=1`、`caller_file = "agent_slots.py"`
- **期待**: `write_connection()` context は `_DualWriteConnection` ではなく single new_conn を返す。orchestration.db tmpdir に INSERT される。旧 helix.db tmpdir への write は発生しない
- **受入条件**: legacy DB に row が存在しない。new DB に row が存在する

#### U-ADAPTER-011: cutover 後 — read helper が orchestration.db の projection_state を返す

- **対象**: D-API-SEP §4.1 `read_cross_db_projection`
- **入力**: tmpdir に orchestration.db を作成し `projection_state` table に row を INSERT。`projector_id="phase_projector"`, `db_name="orchestration"`
- **期待**: `read_cross_db_projection("phase_projector", "orchestration")` → snapshot dict が返る
- **受入条件**: 返り値は `json.loads(snapshot)` の dict と一致する。ATTACH を使わない (直接 connect)

#### U-ADAPTER-012: cutover 後 — projector lag WARN (100 event 超過)

- **対象**: D-API-SEP §4.3 `_check_projector_lag` (lag >= 100 → WARNING log)
- **入力**: `projection_state.last_processed_event_id = "evt-000"` に設定し、`event_envelope` に 101 件の event を INSERT (event_id > "evt-000")
- **期待**: `_check_projector_lag` が WARNING log を出力し、lag=101 を返す
- **受入条件**: `caplog` で WARNING が捕捉できる。戻り値 >= 101

#### U-ADAPTER-013: cutover 後 — db file 不在で read_cross_db_projection が None を返す

- **対象**: D-API-SEP §4.1 (db file not found → None)
- **入力**: 存在しない db_name/path を指定
- **期待**: `read_cross_db_projection(...)` → `None`。例外が raise されない
- **受入条件**: 戻り値が `None`。WARNING log が出力される

#### U-ADAPTER-014: unknown caller の fail-close 動作 (tl-advisor L3 review Round 2 P1 #2 反映、production fail-close 主契約)

- **対象**: D-API-SEP §2.2 `_route_to_db` unknown caller の **production default = fail-close**、discovery mode のみ fallback
- **入力**: `caller_file = "unknown_module.py"`, `caller_func = "unknown_func"` (`_FILE_TO_DB` に存在しない、table prefix も該当なし)
- **期待**:
  - **production default** (`HELIX_DB_DISCOVERY` 未設定 or `0`): `RuntimeError` を raise する fail-close (entity ownership 違反防止)。orchestration.db への fallback は **発生しない**
  - **discovery mode** (`HELIX_DB_DISCOVERY=1`): `"orchestration"` へ fallback + WARNING log を出力。例外は raise しない (移行期の調査用途)
- **受入条件**:
  - production: `RuntimeError` が raise される + error message に「production fail-close (entity ownership 違反防止)」「`_FILE_TO_DB` mapping に追加するか、`HELIX_DB_DISCOVERY=1` で discovery mode を有効化してください」が含まれる
  - discovery mode: WARNING log が出力され `"orchestration"` が返る + WARN message に「discovery mode」が含まれる
- **test case 分割**: `pytest.mark.parametrize` で 2 環境 (`HELIX_DB_DISCOVERY=0` / `HELIX_DB_DISCOVERY=1`) を分岐 case として独立化
- **D-API-SEP §2.2 / §2.5 整合**: 本 case は D-API-SEP §2.2 (実装契約) + §2.5 (error handling 表) と byte-level に一致する (Round 2 P1 #2 反映後)

#### U-ADAPTER-015: cli/libexec/helix-session-start adapter 対象外 smoke

- **対象**: D-API-SEP §6 (helix-session-start は adapter 対象外、明示 db_path 指定)
- **入力**: `db_path="/tmp/test.db"` を明示指定して `write_connection("/tmp/test.db")` を呼ぶ
- **期待**: 旧来の `helix_db._write_connection(db_path)` に委譲される。`_route_to_db` は呼ばれない
- **受入条件**: `/tmp/test.db` に対して write が行われる。6 db routing テーブル (`_FILE_TO_DB`) を経由しない

---

## §3 U-EVT-* 単体テスト設計 (EventEnvelope class 対応)

### 対応設計

- D-CONTRACT-EVENT-draft-v0.1 §2 (EventEnvelope dataclass 定義 / frozen / db_name validation)
- D-CONTRACT-EVENT-draft-v0.1 §5 (payload schema 規約 / event_type 命名)
- D-CONTRACT-EVENT-draft-v0.1 §6 (occurred_at format / UTC 固定)

**テストコード (④ artifact)**: `cli/lib/tests/test_event_envelope_unit.py` (Phase 4.B 起票予定)

**テスト方針**: `EventEnvelope` は frozen dataclass のため、構築・シリアライズ・デシリアライズの境界を独立で検証する。DB アクセスは含まない (unit test として DB を分離)。`from_sqlite_row(to_sqlite_row(envelope))` の round-trip で完全一致を確認する。

### 受入条件 (全 U-EVT-* 共通)

- `EventEnvelope` は immutable (frozen=True) で、field への代入が `FrozenInstanceError` を raise する
- `to_sqlite_row` / `from_sqlite_row` の round-trip で元の instance と完全一致する
- db_name の許可値 (`orchestration` / `vmodel` / `scrum`) 以外は `ValueError` を raise する
- occurred_at は UTC タイムゾーン情報を含む ISO8601 形式

---

#### U-EVT-001: EventEnvelope 構築 — frozen=True で immutable

- **対象**: D-CONTRACT-EVENT-draft §2.2 (frozen=True の設計根拠 §2.3)
- **入力**: 全 field を指定して `EventEnvelope(...)` を構築
- **期待**: インスタンスが生成される。`event.event_id = "new_id"` の代入が `FrozenInstanceError` を raise する
- **受入条件**: `dataclasses.FrozenInstanceError` (または `AttributeError`) が raise される

#### U-EVT-002: EventEnvelope 構築 — db_name 許可値 validation

- **対象**: D-CONTRACT-EVENT-draft §2.4 db_name validation / `_ALLOWED_DB_NAMES`
- **入力A**: `db_name="orchestration"` → 正常構築
- **入力B**: `db_name="vmodel"` → 正常構築
- **入力C**: `db_name="scrum"` → 正常構築
- **入力D**: `db_name="backend"` → `ValueError`
- **入力E**: `db_name="plan"` → `ValueError`
- **入力F**: `db_name=""` → `ValueError`
- **期待**: A/B/C は正常。D/E/F は `ValueError` を raise する
- **受入条件**: 許可値 3 件は全て正常構築できる。禁止値 (state-store / hybrid / 空文字) は全て `ValueError`

#### U-EVT-003: EventEnvelope 構築 — occurred_at UTC format

- **対象**: D-CONTRACT-EVENT-draft §6 occurred_at 規約
- **入力**: `create_event_envelope(...)` factory で EventEnvelope を生成
- **期待**: `envelope.occurred_at` が UTC タイムゾーン情報を含む ISO8601 形式
  - 形式例: `"2026-05-17T18:50:00.123456+00:00"`
  - `datetime.fromisoformat(envelope.occurred_at).tzinfo` が `timezone.utc` と等価
- **受入条件**: `fromisoformat` でパースでき、tzinfo が UTC を示す

#### U-EVT-004: to_sqlite_row — 8 要素 tuple への変換

- **対象**: D-CONTRACT-EVENT-draft §2.2 `to_sqlite_row()` / D-DB-SEP-draft §3 event_envelope table
- **入力**: `payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"}` を持つ EventEnvelope
- **期待**: `to_sqlite_row()` が `(event_id, aggregate_id, aggregate_type, db_name, event_type, payload_json, correlation_id, occurred_at)` の 8 要素 tuple を返す。payload_json は `json.dumps(payload)` と一致する
- **受入条件**: tuple の要素数が 8。payload_json が JSON 形式の文字列 (parse 可能)

#### U-EVT-005: from_sqlite_row — round-trip 完全一致

- **対象**: D-CONTRACT-EVENT-draft §2.2 `from_sqlite_row()` round-trip
- **入力**: `EventEnvelope` を構築し `to_sqlite_row()` で tuple 化 → `from_sqlite_row(tuple)` で復元
- **期待**: 復元した `EventEnvelope` が元のインスタンスと完全一致 (`==` で True)
- **受入条件**: `original == restored` が True。payload dict が深く一致する (ネスト dict / list を含む場合も可)

#### U-EVT-006: payload schema 検証 — phase.transitioned event_type

- **対象**: D-CONTRACT-EVENT-draft §5.5 payload schema 例 (phase.transitioned.json)
- **入力**: `event_type="phase.transitioned"`, `payload={"from_phase": "L3", "to_phase": "L4", "owner": "pm-opus"}`
- **期待**: JSON schema 検証 (jsonschema.validate または手動チェック) が PASS する。必須 field 欠損 (`from_phase` 欠損) は ValidationError を raise する
- **受入条件**: 完全な payload は検証 PASS。必須 field 欠損は `ValueError` または `jsonschema.ValidationError` を raise する (Phase 4.B で jsonschema 導入時)

#### U-EVT-007: payload schema 検証 — gate.passed event_type

- **対象**: D-CONTRACT-EVENT-draft §5.5 payload schema 例 (gate.passed.json)
- **入力A**: `event_type="gate.passed"`, `payload={"gate_name": "G4", "plan_id": "PLAN-084"}` → PASS
- **入力B**: `payload={"gate_name": "G99", "plan_id": "PLAN-084"}` → FAIL (G99 は enum 外)
- **期待**: A は検証 PASS。B は ValidationError
- **受入条件**: gate_name の enum (`G1` 〜 `G11`) 以外は拒否される

#### U-EVT-008: payload schema 検証 — artifact.created event_type

- **対象**: D-CONTRACT-EVENT-draft §5.2 event_type 命名規約 (aggregate_type.verb_past)
- **入力**: `event_type="artifact.created"`, `payload={"artifact_type": "design", "plan_id": "PLAN-084", "file_path": "docs/v2/D-API.md"}`
- **期待**: 構築 PASS。payload が dict であること (schema は Phase 4.B で起票予定)
- **受入条件**: 構築時に例外が raise されない。`event_type` が `<aggregate_type>.<verb_past>` 命名規約に適合

#### U-EVT-009: db_name 不正値 — state-store / hybrid を拒否

- **対象**: D-CONTRACT-EVENT-draft §1.3 対象 db の範囲確認 + §2.4
- **入力**: `db_name="backend"`, `db_name="frontend"`, `db_name="plan"` それぞれで `create_event_envelope(...)` を呼ぶ
- **期待**: 全ての case で `ValueError` が raise される
- **受入条件**: メッセージに許可値 (`orchestration / vmodel / scrum`) が明示されている

#### U-EVT-010: occurred_at UTC format 拒否 — local time は拒否される

- **対象**: D-CONTRACT-EVENT-draft §6.2 生成方法 + §6.4 timezone 固定の理由
- **入力**: `occurred_at` に local time 文字列 (`"2026-05-17T18:50:00"`, timezone info なし) を直接渡す
- **期待**: 構築時または validation 時に `ValueError` が raise される (timezone info 欠損を拒否)
- **受入条件**: `ValueError` が raise される。メッセージに UTC / timezone の記述がある
- **Phase 4.B carry**: `__post_init__` または factory での timezone validation 実装 (D-CONTRACT-EVENT §2.4 実装方針)

---

## §4 U-UUID-* 単体テスト設計 (UUID v7 generator 対応)

### 対応設計

- D-CONTRACT-EVENT-draft-v0.1 §3 (UUID v7 generator 設計 / 採用根拠 / API signature)
- D-DB-SEP-draft-v0.1 §3.3 (UUID v7 generator 責務)

**テストコード (④ artifact)**: `cli/lib/tests/test_uuid_v7_generator.py` (Phase 4.A 起票予定)

**テスト方針**: `generate_event_id()` の外部仕様 (format / 時系列性 / 衝突率) を black-box で検証する。実装 (uuid7 パッケージ or 自前実装) に依存しない設計とし、Phase 4.A での実装切り替えに追随する。

### 受入条件 (全 U-UUID-* 共通)

- `generate_event_id()` が 36 文字の UUID 形式 (`XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`) を返す
- 生成された ID は時系列 sortable (連続生成で lexicographic order が時系列と一致)
- 同一プロセス内での衝突が発生しない (1000 件で重複 0)

---

#### U-UUID-001: generate_event_id() — 36 文字 UUID 形式

- **対象**: D-CONTRACT-EVENT-draft §3.3 generator API signature
- **入力**: `generate_event_id()` を 1 回呼び出す
- **期待**: 36 文字の文字列。正規表現 `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` に適合する
- **受入条件**: `re.match(UUID_PATTERN, result)` が None でない

#### U-UUID-002: generate_event_id() — 時系列 sortable 検証

- **対象**: D-CONTRACT-EVENT-draft §3.1 UUID v7 採用根拠 (時系列 ORDER BY との一致)
- **入力**: `generate_event_id()` を 100 件連続して生成し、生成順と sort 結果を比較
- **期待**: `ids == sorted(ids)` が True (lexicographic sort が生成時系列と一致)
- **受入条件**: 全 100 件で `ids == sorted(ids)` が True。同一 ms 内の衝突分でも順序が保たれる
- **注意**: 同一ミリ秒内に複数件生成される場合、乱数部分での順序保証が必要。`time.sleep(0.001)` を使わない (test 速度のため)

#### U-UUID-003: generate_event_id() — 衝突率 (1000 件で重複 0)

- **対象**: D-CONTRACT-EVENT-draft §3.4 collision 確率と HELIX scale 評価
- **入力**: `generate_event_id()` を 1000 件生成し `set()` に格納
- **期待**: `len(ids_set) == 1000` (重複なし)
- **受入条件**: set のサイズが 1000。衝突 0 件

#### U-UUID-004: generate_event_id() — Python 3.12 環境での動作確認 (tl-advisor L3 review P2 #4 反映)

- **対象**: D-CONTRACT-EVENT-draft §3.2 Python library 選択方針 (Python 3.12 での uuid7 動作)
- **入力**: Python 3.12 環境で `generate_event_id()` を呼ぶ (CI / pytest 実行環境)
- **期待**: 例外が raise されず UUID 形式の文字列が返る
- **受入条件**: Python バージョン `sys.version_info >= (3, 12)` かつ `sys.version_info < (3, 14)` の環境で正常動作する。`uuid7` パッケージ未インストール時は自前実装 fallback が動作する
- **Phase 4.A carry**: 実装選択 (uuid7 パッケージ vs 自前実装) に応じて pytest marker または conftest で Python バージョン条件を設定する

#### U-UUID-005: generate_event_id() — Python 3.14+ stdlib 切替可能性確認 (Phase 6+ 将来 carry)

- **対象**: D-CONTRACT-EVENT-draft §3.2 Python 3.14+ `uuid.uuid7()` (RFC 9562、tl-advisor L3 review Round 2 P2 反映)
- **HELIX 現状契約 (tl-advisor L3 Round 3 P3 反映)**:
  - Phase 4.A 実装: Python 3.12.3 (HELIX local 環境) 向けに **3.12 fallback 設計** を採用 (U-UUID-004 でカバー、`uuid7` パッケージ or 自前実装)
  - 「stdlib 統一」は契約ではなく、**Phase 6+ で Python 3.14 移行検討時の切替可能性確認** が本 case の目的
  - 本 case は `sys.version_info >= (3, 14)` 環境でのみ有効、3.12.3 環境では `pytest.mark.skip(reason="Python 3.14+ required for stdlib uuid7")` で skip
- **入力**: `sys.version_info >= (3, 14)` の環境で `generate_event_id()` を呼ぶ (将来 Python upgrade 時)
- **期待**: `uuid.uuid7()` (stdlib) が呼ばれ、外部依存なしで動作する
- **受入条件**: `uuid7` パッケージなしで UUID 形式の文字列が返る (将来 3.14+ 環境で実行時に PASS)
- **Phase 6+ carry**: HELIX の Python バージョン要件を 3.14+ に引き上げる ADR (将来) で本 case が実 PASS になる切替判断を行う
- **Phase 4.A carry**: `pytest.mark.skipif(sys.version_info < (3, 14), ...)` で条件付き実行。現時点 (Python 3.12 HELIX 環境) では skip 可

---

## §5 U-CORR-* 単体テスト設計 (correlation_context 対応)

### 対応設計

- D-CONTRACT-EVENT-draft-v0.1 §4 (correlation_id 発行・継承規則 / thread-local 管理)

**テストコード (④ artifact)**: `cli/lib/tests/test_correlation_context.py` (Phase 4.B 起票予定)

**テスト方針**: `correlation_context` は thread-local な context manager のため、同一 thread と別 thread での動作を独立して検証する。`threading.Thread` を使った並列テストで thread 間の独立性を確認する。

### 受入条件 (全 U-CORR-* 共通)

- `correlation_context(parent=None)` は新規 UUID を生成し、context 内で `get_current_correlation_id()` が返す
- `correlation_context(parent="...")` は parent の correlation_id を継承する
- context 終了後、`get_current_correlation_id()` は `None` を返す (context 外では取得不可)
- 別 thread の correlation_id は独立している (thread-local の性質)

---

#### U-CORR-001: correlation_context(parent=None) — 新規発行

- **対象**: D-CONTRACT-EVENT-draft §4.2 発行ルール / §4.3 API signature
- **入力**: `with correlation_context() as corr_id:`
- **期待**: `corr_id` が UUID 形式の文字列。`get_current_correlation_id()` が context 内で同じ値を返す。context 終了後は `None` を返す
- **受入条件**: UUID 形式 (`re.match(UUID_PATTERN, corr_id)`)。context 外で `None`

#### U-CORR-002: correlation_context(parent="...") — 継承

- **対象**: D-CONTRACT-EVENT-draft §4.2 継承ルール / §4.3 cross-db trace 例
- **入力**: `parent_id = "018f4a1b-..."` を渡して `with correlation_context(parent=parent_id) as child_id:`
- **期待**: `child_id == parent_id` (継承された場合は同じ値)
- **受入条件**: `child_id == parent_id` が True。新規 UUID は生成されない

#### U-CORR-003: thread-local context — 同 thread 内継承 OK / 別 thread 独立

- **対象**: D-CONTRACT-EVENT-draft §4.3 `_correlation_context = threading.local()`
- **入力**: メインスレッドで `correlation_context()` を開始し `corr_id_main` を取得。同時に別 thread で `correlation_context()` を開始し `corr_id_other` を取得
- **期待**: `corr_id_main != corr_id_other` (別 thread は別の correlation_id を持つ)。別 thread で `get_current_correlation_id()` を呼んでも main の correlation_id は取得されない
- **受入条件**: 2 値が異なる。thread 間で相互汚染なし

#### U-CORR-004: cross-db trace — orchestration で発行 → vmodel に継承

- **対象**: D-CONTRACT-EVENT-draft §4.4 cross-db trace 具体例
- **入力**:
  ```python
  with correlation_context() as corr_id:
      # orchestration event 発行に使う correlation_id
      with correlation_context(parent=corr_id) as child_corr_id:
          # vmodel event 発行に使う correlation_id
  ```
- **期待**: `child_corr_id == corr_id` (継承)。inner context 終了後も outer context の `corr_id` が有効。outer context 終了後は `get_current_correlation_id()` が `None`
- **受入条件**: inner = outer の correlation_id。outer 終了後 `None`

#### U-CORR-005: correlation_id format (UUID v7 36 字 vs 短縮 12 字、Phase 4.B 確定 carry)

- **対象**: D-CONTRACT-EVENT-draft §4.5 correlation_id format (Phase 4.B 確定 carry)
- **入力**: `correlation_context(parent=None)` で新規発行
- **期待 (Phase 4.A 暫定)**: UUID v7 形式 (36 文字) で発行される
- **受入条件**: UUID 形式 (36 文字) が返る。短縮 hash 12 文字形式への切り替えは Phase 4.B での PM 判断を待つ
- **Phase 4.B carry**: format 確定後に test の `expected` を更新する。`pytest.mark.xfail` を使って format 未確定の状態を明示しておく

---

## §6 V-model 双方向 trace

本文書 (③ テスト設計) と他 3 artifact (① 設計 / ② 実装 / ④ テストコード) の対応関係を以下に明示する (HELIX_CORE.md §V-model 4 artifact 双方向 trace 原則準拠)。

| L3 設計 doc (① 設計) | 単体テスト case (本 doc、③) | テスト実装 file (④ テストコード) |
|---|---|---|
| D-API-SEP-draft §2 (write_connection / routing) | U-ADAPTER-001〜005 | cli/lib/tests/test_compatibility_adapter.py |
| D-API-SEP-draft §2.3 (dual-write _DualWriteConnection) | U-ADAPTER-006〜009 | cli/lib/tests/test_compatibility_adapter.py |
| D-API-SEP-draft §2.1 cutover path | U-ADAPTER-010 | cli/lib/tests/test_compatibility_adapter.py |
| D-API-SEP-draft §4 (cross-db read helper) | U-ADAPTER-011〜013 | cli/lib/tests/test_compatibility_adapter.py |
| D-API-SEP-draft §2.2 unknown caller fallback + fail-close | U-ADAPTER-014 | cli/lib/tests/test_compatibility_adapter.py |
| D-API-SEP-draft §6 (session-start adapter 対象外) | U-ADAPTER-015 | cli/lib/tests/test_compatibility_adapter.py |
| D-CONTRACT-EVENT-draft §2 (EventEnvelope frozen / db_name) | U-EVT-001〜003, 009, 010 | cli/lib/tests/test_event_envelope_unit.py |
| D-CONTRACT-EVENT-draft §2 (to_sqlite_row / from_sqlite_row) | U-EVT-004〜005 | cli/lib/tests/test_event_envelope_unit.py |
| D-CONTRACT-EVENT-draft §5 (payload schema 検証) | U-EVT-006〜008 | cli/lib/tests/test_event_envelope_unit.py |
| D-CONTRACT-EVENT-draft §3 (UUID v7 generator) | U-UUID-001〜005 | cli/lib/tests/test_uuid_v7_generator.py |
| D-CONTRACT-EVENT-draft §4 (correlation_context) | U-CORR-001〜005 | cli/lib/tests/test_correlation_context.py |

### 双方向 trace 宣言

- **本 doc → ① 設計**: 各節の「対象設計」に L3 doc § を明示済み (D-API-SEP / D-CONTRACT-EVENT)
- **① 設計 → 本 doc**: D-API-SEP §8 V-model trace に本 doc を reference として記載 (Phase 4.A 着手時に追記)
- **本 doc → ④ テストコード**: 各 U-XXX-NNN に `テストコード` ファイルを明示済み
- **④ テストコード → 本 doc**: 各 test 関数 docstring に `DoD 検証: PLAN-084-unit-test-design.md U-XXX-NNN` を記載する (Phase 4.A/4.B 実装時)
- **④ テストコード → ② 実装コード**: `import compatibility_adapter` / `from event_envelope import EventEnvelope` で実装に接続

---

## §7 carry to Phase 4

Phase 4 実装で確定・実施する事項:

| # | carry 項目 | Phase | 担当 | 依存 |
|---|---|---|---|---|
| 1 | test 実装本体 (U-ADAPTER-001〜005): routing 5 pattern (`test_compatibility_adapter.py`) | 4.A | Codex qa | compatibility_adapter.py 実装 (D-API-SEP §7 carry #1) |
| 2 | test 実装本体 (U-ADAPTER-006〜015): dual-write / cutover / read helper / unknown caller / session-start | 4.A | Codex qa | carry #1 + `_DualWriteConnection` 実装 |
| 3 | adapter test の inspect.stack frame index 実測対応 (D-API-SEP §2.1: `inspect.stack()[2]` は呼び出し階層に依存) | 4.A | Codex qa | monkeypatch 戦略確定 |
| 4 | test 実装本体 (U-EVT-001〜010): EventEnvelope 単体テスト (`test_event_envelope_unit.py`) | 4.B | Codex qa | EventEnvelope dataclass 実装 (D-CONTRACT-EVENT §7 carry #2) |
| 5 | test 実装本体 (U-UUID-001〜005): UUID v7 generator 単体テスト (`test_uuid_v7_generator.py`) | 4.A | Codex qa | generate_event_id() 実装 (D-CONTRACT-EVENT §7 carry #1) |
| 6 | test 実装本体 (U-CORR-001〜005): correlation_context 単体テスト (`test_correlation_context.py`) | 4.B | Codex qa | correlation_context 実装 (D-CONTRACT-EVENT §7 carry #4) |
| 7 | UUID v7 stdlib 切替 (Python 3.14+ で uuid.uuid7() 採用判断、U-UUID-005 の skipif 解除) | 6+ | PM | Python バージョン要件変更 |
| 8 | U-CORR-005 の format 確定 (UUID v7 36 字 vs 短縮 12 字) と test 更新 | 4.B | PM + Codex qa | D-CONTRACT-EVENT §4.5 Phase 4.B 判断 |
| 9 | U-EVT-010 (occurred_at timezone validation) の __post_init__ / factory 実装 (D-CONTRACT-EVENT §2.4 実装方針確定後) | 4.B | Codex qa | EventEnvelope validation 実装 |
| 10 | U-ADAPTER-014 fail-close への切り替え (mapping 完全版確定後の PM 承認) | 4.A 末 | PM + Codex qa | D-API-SEP §7 carry #2 (_FILE_TO_DB 完全版確定) |
| 11 | payload schema 検証 (U-EVT-006〜008) に jsonschema 組み込み (Phase 4.B で jsonschema 導入後) | 4.B | Codex qa | D-CONTRACT-EVENT §7 carry #6 |

**carry 優先度**:

- **Phase 4.A 必須**: #1 (U-ADAPTER routing) / #2 (U-ADAPTER dual-write) / #3 (stack frame 実測) / #5 (U-UUID generator)
- **Phase 4.B 必須**: #4 (U-EVT) / #6 (U-CORR) / #8 (format 確定) / #9 (timezone validation) / #11 (jsonschema)
- **Phase 4.A 末**: #10 (fail-close 切り替え承認)
- **Phase 6+**: #7 (stdlib 切替)

---

## §8 References

| 参照先 | 参照箇所 | 本文書との関係 |
|---|---|---|
| `docs/v2/L3-detailed-design/D-DB/D-DB-SEP-draft.md` §3 | event_envelope table schema / §3.3 UUID v7 / §3.4 correlation_id | U-EVT-*/U-UUID-* の schema 根拠 |
| `docs/v2/L3-detailed-design/D-API/D-API-SEP-draft.md` §2/3/4/5/6 | write_connection API / routing 規則 / dual-write / cross-db read helper / ATTACH 禁止 / session-start 除外根拠 | U-ADAPTER-* 全体の設計根拠 |
| `docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md` §2/3/4/5/6 | EventEnvelope dataclass / UUID v7 / correlation_context / payload schema / occurred_at | U-EVT-*/U-UUID-*/U-CORR-* 全体の設計根拠 |
| `docs/v2/L4-test-design/PLAN-074-unit-test-design.md` | frontmatter 形式 / §構成 / 4 artifact trace 記法 | 本 doc の章立て・記述 pattern 参考 |
| `docs/v2/L4-test-design/PLAN-078-unit-test-design.md` | V-model 4 artifact 位置付け / case 表形式 / 受入条件記法 | 本 doc の case 設計 pattern 参考 |
| `helix/HELIX_CORE.md` §V-model 4 artifact 双方向 trace 原則 | 4 artifact の別文書保持 + 双方向 reference 必須ルール | 本 doc 全体の存在根拠 |
| `docs/plans/PLAN-084-helix-db-separation-and-event-sourcing.md` §3.1 Phase 4.A/4.B | carry 割当の正本 | §7 carry 項目の根拠 |
