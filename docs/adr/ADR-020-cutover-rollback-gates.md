# ADR-020: PLAN-084 cutover gate 5 + rollback gate 6 採用

## Status

Accepted (2026-05-18)

> proposed (2026-05-18) → Accepted (2026-05-18) PO 承認。本 ADR 起票同日に PLAN-084 Phase 4 完遂後の PO 承認で Accepted 遷移。本番 cutover 実行は別 PLAN-085 (staging 演習 → 本番 → 24h 監視 → 採用) で実行する。

## Deciders

- PM (Opus)
- TL (Codex tl-advisor、Phase 4.B-.C wave 1 並列実装後)
- PO (yoshiyuki0907yn@gmail.com、2026-05-18 承認)

## Supersedes

なし

## Related

- ADR-018 (helix.db 6 分離 + Event Sourcing + projector 境界)
- ADR-019 (Double Helix 命名原則)

---

## Context

ADR-018 §Decision.5 で確立した 6 段階 migration gate のうち、**gate 5 (cutover)** と **gate 6 (rollback ready)** の運用詳細を本 ADR で確定する。Phase 4.C.2/.C.3 で実装した `cutover_orchestrator.py` / `rollback_orchestrator.py` は code 完成しているが、本番実行は PO 承認を伴う運用フェーズに属するため、ADR レベルで gate の入退場条件・承認境界・rollback trigger を凍結する必要がある。

PLAN-084 Phase 4.A-.B-.C wave 1 までで以下が完成:
- 6 db 分離 skeleton + adapter (Phase 4.A)
- EventEnvelope / UUID v7 / correlation_context (Phase 4.B.1-.3)
- dual-write `_DualWriteConnection` + projector 3 件 + mismatch detector + I-CORR (Phase 4.B.4-.8)
- shadow replay + cutover orchestrator + rollback orchestrator (Phase 4.C.1-.3)

残りは **gate 5 / gate 6 の本番運用判断** で、これは Opus 単独確定不可。

---

## Decision

### Decision.1: gate 5 (cutover) 採用

cutover の本番実行は `cutover_orchestrator.cutover_execute(confirm_token=...)` 経由のみ許可する。

**Entry 条件** (preflight、`cutover_preflight() -> CutoverPreflightResult`):
- dual-write 健全性確認 (直近 7 日間の mismatch ≤ 0 critical / ≤ N warn)
- shadow replay 完遂確認 (`replay_to_shadow_db` が直近で `failed_count == 0` で完走)
- `_DualWriteConnection` の lag < `LAG_CRITICAL_THRESHOLD` (1000 event)
- backup 整合確認 (gate 6 前提)

**Execute** (cutover):
- `confirm_token` (例: `"PO-APPROVED-YYYY-MM-DD-<hash>"`) 必須、不在 → `RuntimeError`
- token 形式は PO が発行 (PR に「Approved by PO」コメント + commit SHA)
- 実行: `HELIX_DB_CUTOVER=1` 永続化 (環境設定 or config commit)
- 実行後 24h は `dual-write` 経路を残し (mirror only)、48h で legacy helix.db 接続を停止

**Exit 条件**:
- 6 db すべてに write 到達確認 (各 db の `event_envelope` row count > 0)
- mismatch detector 6h 連続 critical 0
- gate 6 ready 状態 (rollback path 検証済)

### Decision.2: gate 6 (rollback ready) 採用

cutover 後の retreat path として `rollback_orchestrator.rollback_execute(confirm_token=..., backup_path=...)` 経由のみ許可する。

**Entry 条件** (preflight、`rollback_preflight() -> dict`):
- `HELIX_DB_CUTOVER=1` 状態確認 (cutover 後でないと rollback は意味なし)
- backup 整合確認 (gate 5 entry 時に取得した backup_path が読める)
- diff event 数算出 (cutover 後の new db への write event 数)

**Execute** (rollback):
- `confirm_token` 必須 (cutover と同じ format、新規発行)
- `backup_path` 必須 (gate 5 で記録した legacy helix.db backup)
- 実行: `HELIX_DB_CUTOVER=0` に戻し、6 db を read-only に閉じる
- diff event は別途 `RollbackResult.diff_event_count` で報告、運用判断で replay or discard

**rollback trigger 条件** (運用):
- mismatch detector が critical 連続検出 (24h 以上)
- 6 db いずれかが破損 / 読み書き不能
- PO が明示判断で rollback 要請

---

## Consequences

### 採用メリット

- cutover/rollback の運用手続きが ADR で明文化、code (orchestrator) と doc (gate5/gate6 spec) が一致
- PO 承認境界の機械化 (`confirm_token` validation で無人実行を防止)
- rollback path が常に preflight 可能で、ステージング演習可能

### リスク

- PO 承認の non-blocking 化が起きると無人 cutover/rollback が発生 (`confirm_token` を git commit に埋め込めば bypass 可能)
- backup_path が紛失すると rollback 不能
- cutover 後 24h の dual-write 期間で legacy 経路から write 漏れ発生の可能性

### 緩和

- `confirm_token` は PR レビュー必須 (Opus single-PR commit 禁止、PO + TL 2 名 reviewer required)
- backup_path は cutover 実行時に S3/secure store に複製
- cutover 後 24h 監視 + dual-write log 監査 (Phase 4.B.6 mismatch detector 連続実行)
- 環境変数 `HELIX_DB_CUTOVER` の永続化は config commit 経由のみ (env vars 直書きを CI gate で禁止)

---

## Approval Carry

- 本 ADR は `status: proposed` で起票。
- `status: Accepted` への遷移は **PO 承認 PR** で別 commit。
- Accepted 後の本番実行は別 PLAN で起票し、cutover 演習 (staging) → 本番 cutover → 監視 24h → 本番採用 のステップで進行。

---

## References

- ADR-018 §Decision.5 (6 段階 migration gate)
- `cli/lib/cutover_orchestrator.py` (Phase 4.C.2 commit f7c08dc)
- `cli/lib/rollback_orchestrator.py` (Phase 4.C.3 commit f7c08dc)
- `docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md` (gate 5 spec)
- `docs/v2/L3-detailed-design/D-API/D-API-SEP-rollback-gate6.md` (gate 6 spec)
- `cli/lib/dual_write_mismatch.py` (mismatch detector、24h soak で gate 5 preflight 入力)
- `cli/lib/shadow_replay.py` (gate 5 preflight 入力)
