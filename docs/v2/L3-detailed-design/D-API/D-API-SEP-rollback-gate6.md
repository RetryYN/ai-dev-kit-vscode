---
doc_id: D-API-SEP-rollback-gate6-v0.1
plan_id: PLAN-084
sprint: Phase 4.C.3 / rollback gate 6
status: draft
created: 2026-05-18
primary_drive: be
related_adrs:
  - ADR-018-db-separation-and-event-sourcing
related_designs:
  - D-API-SEP-draft-v0.1
  - D-DB-SEP-draft-v0.1
related_test_designs:
  - PLAN-084-integration-test-design-v0.1
---

# PLAN-084 Phase 4.C.3: rollback orchestrator + gate 6 詳細設計

@helix:index id=plan084.rollback-gate6.design domain=docs/v2 summary=PLAN-084 gate 6 rollback trigger backup integrity diff event handling design

本文書は ADR-018 §Decision.5 gate 6 を `cli/lib/rollback_orchestrator.py` の API と
運用前提へ落とす L3 補助設計である。cutover 後 7 日の rollback window に限定し、
PO 承認 token、legacy backup の整合、diff event 件数、`HELIX_DB_CUTOVER` の復帰条件を
fail-close で固定する。正式採用は Phase 4.C.4 の ADR-020 に carry する。

## §1 位置づけ

### 1.1 対象

- 実装ファイル: `cli/lib/rollback_orchestrator.py`
- テストファイル: `cli/lib/tests/test_rollback_orchestrator_unit.py`
- 既存参照: `cli/lib/compatibility_adapter.py`

### 1.2 gate 6 の責務

gate 6 は「cutover 後に重大 anomaly が出た場合、旧 helix.db を再び write path に戻せるか」を
確認する rollback readiness gate である。ここで扱う rollback は以下に限定する。

- control-plane rollback:
  `HELIX_DB_CUTOVER=1` を `0` に戻し、adapter を dual-write 経路へ復帰させる
- verification rollback:
  legacy backup と integrity manifest が restore 可能な状態で存在することを確認する
- audit rollback:
  diff event 件数と rollback 実行時刻を証跡として返す

以下は本スコープ外とし、PO 承認 runbook / ADR-020 へ carry する。

- projection table drop
- new read model の物理破棄
- 実 DB restore の実行手順
- anomaly severity の最終判定

## §2 API 契約

```python
@dataclass(frozen=True)
class RollbackResult:
    rolled_back: bool
    backup_path: str
    diff_event_count: int
    reverted_at: str

def rollback_preflight() -> dict:
    """rollback 実行前の preflight (HELIX_DB_CUTOVER state 確認 + backup 整合)."""

def rollback_execute(*, confirm_token: str, backup_path: str) -> RollbackResult:
    """実 rollback 実行 (PO 承認 token 必須、本実装は code 完成のみ、実行は PO carry)."""
```

### 2.1 `rollback_preflight()` の戻り値

`dict` は以下の key を必須で返す。

| key | 型 | 意味 |
|---|---|---|
| `cutover_enabled` | `bool` | 現在 `HELIX_DB_CUTOVER=1` か |
| `backup_path` | `str` | rollback 対象 backup の絶対 path |
| `manifest_path` | `str` | `<backup>.rollback.json` の絶対 path |
| `backup_exists` | `bool` | backup file の存在 |
| `manifest_exists` | `bool` | integrity manifest の存在 |
| `backup_integrity_ok` | `bool` | manifest の `expected_sha256` と backup 実 hash が一致するか |
| `cutover_at` | `str | None` | ISO8601 UTC |
| `rollback_window_open` | `bool` | cutover から 7 日以内か |
| `diff_event_count` | `int | None` | rollback 前に残っている diff event 件数 |
| `can_rollback` | `bool` | 上記条件をすべて満たすか |
| `reasons` | `list[str]` | fail-close 理由 |

### 2.2 `rollback_execute()` の挙動

1. `HELIX_DB_ROLLBACK_CONFIRM_TOKEN` と `confirm_token` を `compare_digest` で照合する
2. `rollback_preflight()` を再実行し、`can_rollback=True` でなければ中断する
3. `backup_path` は preflight で解決した path と完全一致しなければ中断する
4. 成功時は `HELIX_DB_CUTOVER=0` を process-local に反映する
5. `RollbackResult` を返し、`reverted_at` は UTC ISO8601 とする

## §3 backup / manifest 契約

gate 6 は backup file 単体ではなく companion manifest を必須とする。

### 3.1 backup file

- path 優先順:
  1. `HELIX_DB_ROLLBACK_BACKUP_PATH`
  2. `helix_db._resolve_db_path(None)` から導出する既定 path
- backup file は legacy helix.db の restore 元であり、実行時点で読み取り可能であること

### 3.2 manifest file

path は `<backup_path>.rollback.json` とし、少なくとも以下を含む。

```json
{
  "expected_sha256": "hex digest",
  "diff_event_count": 4,
  "cutover_at": "2026-05-17T01:00:00+00:00"
}
```

制約:

- `expected_sha256`: 空文字不可
- `diff_event_count`: 0 以上の整数
- `cutover_at`: UTC timezone 付き ISO8601

manifest が無い、型が不正、hash 不一致、`cutover_at` 不在のいずれかは fail-close とする。

## §4 rollback trigger と diff event 処理

### 4.1 trigger 条件

rollback 実行トリガは ADR-018 と D-DB-SEP の記述をそのまま採用する。

- cutover 後 7 日以内
- 重大 anomaly:
  - data loss
  - projector down > 1h
- PM 推奨
- PO 承認 token 提示

### 4.2 diff event の扱い

`diff_event_count` は rollback 実行前に解消されていない旧 db / 新 db の差分イベント件数を表す。
gate 6 実装では以下を固定する。

- `diff_event_count` は manifest から読み込む
- 0 件が理想だが、0 件でなくても rollback は可能
- 実行結果 `RollbackResult.diff_event_count` に必ず含める
- 0 件超過時は ADR-020 と runbook で事後処理フローを確定する

### 4.3 projection cleanup の扱い

ADR-018 の「event log は保持、新 projection は drop」は本 module では実施しない。
理由は以下の通り。

- gate 6 の目的は first-step rollback readiness の固定であり、projection drop は data-path 操作
- allowed_files 制約下では projection schema 契約を同時に凍結できない
- PO carry の runbook / ADR-020 で destructive step を明示すべき

## §5 エラー方針

| 条件 | 例外 / 判定 |
|---|---|
| token 未設定 | `RuntimeError` |
| token 空文字 | `ValueError` |
| token 不一致 | `PermissionError` |
| backup path 不一致 | `ValueError` |
| preflight fail | `RuntimeError` |
| manifest JSON 不正 | `ValueError` |
| diff_event_count 型不正 | `ValueError` |
| cutover_at timezone なし | `ValueError` |

すべて fail-close。warn-only 経路は設けない。

## §6 テスト観点

### 6.1 unit test

`cli/lib/tests/test_rollback_orchestrator_unit.py`

- `ROLLBACK-U-001`: preflight success
- `ROLLBACK-U-002`: checksum mismatch fail-close
- `ROLLBACK-U-003`: rollback window 超過 fail-close
- `ROLLBACK-U-004`: invalid token rejection
- `ROLLBACK-U-005`: valid token で cutover flag を dual-write に戻す

### 6.2 integration trace

本文書は既存 `PLAN-084-integration-test-design.md` §2.5 `I-MIGRATION-012` と接続する。

- 本文書 → ③ テスト設計:
  `docs/v2/L4-test-design/PLAN-084-integration-test-design.md` §2.5 `I-MIGRATION-012`
- ④ テストコード:
  本 sprint は unit のみ実装し、integration / runbook は Phase 4.C.4 carry

## §7 V-model trace

| artifact | 対応 |
|---|---|
| ① 設計 | 本文書 + `D-API-SEP-draft.md` + `D-DB-SEP-draft.md` |
| ② 実装コード | `cli/lib/rollback_orchestrator.py` |
| ③ テスト設計 | `PLAN-084-integration-test-design.md` §2.5 |
| ④ テストコード | `cli/lib/tests/test_rollback_orchestrator_unit.py` |

## §8 carry

- Phase 4.C.4:
  ADR-020 へ gate 6 正式採用文言を移植する
- runbook:
  projection drop / restore 実 DB 手順 / anomaly severity matrix を起票する
- integration:
  `I-MIGRATION-012` 実装と、cutover 実環境 smoke を追加する
