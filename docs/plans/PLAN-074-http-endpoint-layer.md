---
plan_id: PLAN-074
title: "PLAN-074: HTTP endpoint 5 endpoint 実装 (PLAN-072 L4.5 carry、D-API EXT 契約具現化)"
status: draft
size: M-L
drive: be
created: 2026-05-16
owner: PM
phases: L4, L6
gates: G4
acceptance:
  - 5 endpoint (push/pr/hook/audit/telemetry) を HTTP server として実装し、D-API EXT 契約と完全整合
  - 既存 CLI 結合 (helix-push/pr + hooks) と同等の DB 書き込み挙動を HTTP 経由で再現
  - automation_runs lifecycle 遷移 / audit_log 書き込み / session_telemetry UPSERT が HTTP 経由で動作
  - bats / pytest 全 PASS 維持 (回帰 0)
  - G4 entry 条件達成 (実装 + テスト + ドキュメント整備)
related:
  - PLAN-072-l4-5-integration (frozen 親 L4.5、HTTP 層 carry の根拠)
  - PLAN-070-l3-schema-and-contract-design (frozen L3、D-API EXT 契約起源)
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md (5 endpoint 契約正本)
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (v25-v27 schema)
---

# PLAN-074: HTTP endpoint 5 endpoint 実装

## §1 目的と背景

PLAN-072 (L4.5 Phase B 結合) で CLI 結合 (helix-push / helix-pr / hook / gate) と helix.db 書き込みを完遂した (11 commits, pytest 1285 / bats 478 全 PASS、2026-05-16 frozen)。

しかし D-API EXT で凍結した HTTP endpoint 層は未実装のまま carry となった。本 PLAN はその carry を独立 PLAN として具現化し、D-API EXT 契約 (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md) を HTTP server 実装に落とし込む。

### 前提条件

- PLAN-072 frozen 済 (CLI 結合・DB 書き込み完了が前提)
- D-API EXT contract 凍結済 (PLAN-070 SprintE にて確定)
- v25 automation_runs / v26 audit_log / v27 session_telemetry schema は CURRENT_SCHEMA_VERSION=27 で稼働中
- helper 3 件 (`_upsert_row` / `_transition_lifecycle_status` / `_create_append_only_trigger`) が cli/lib/helix_db.py に実装済み

---

## §2 対象 endpoint

D-API EXT (docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md §3) で凍結された 5 endpoint:

| # | method | path | 役割 | 主要 DB テーブル |
|---|--------|------|------|----------------|
| 1 | POST | `/api/v1/automation/push/{plan_id}/trigger` | push 実行開始・automation_runs INSERT + lifecycle | automation_runs, audit_log |
| 2 | POST | `/api/v1/automation/pr/{plan_id}/trigger` | pr 実行開始・automation_runs INSERT + lifecycle | automation_runs, audit_log |
| 3 | POST | `/api/v1/automation/hooks/{hook_kind}/callback` | hook callback (PreToolUse / PostToolUse / Stop / session_start) | audit_log |
| 4 | POST | `/api/v1/automation/audit/log` | audit/footer 受領 | audit_log |
| 5 | POST | `/api/v1/automation/session/telemetry` | Stop hook session-summary 後継 telemetry | session_telemetry |

### endpoint 共通ルール (D-API EXT §3 共通ルール より)

- 成功系: `{ success: true, data: {...}, trace: { trace_id, generated_at } }`
- 失敗系: `{ success: false, error: { code, message, detail } }`
- `X-Trace-Id` header 必須 (補助キー、automation_runs.id 解決に使用)
- push trigger / pr trigger は response.data.run_id を必須返却 (新規 automation_runs.id)
- hook callback / audit / telemetry は request body.run_id 必須 (既存 automation_runs.id を参照)
- error code は 400 / 401 / 404 / 409 / 500 のみ

---

## §3 Sprint 構成

HTTP framework 選定 (Sprint .1 TL 判断) を前段に置き、その結果を受けて endpoint 実装を並列投入する。

### Sprint .0 — 前提確認 + framework 候補整理 (PMO Sonnet)

- D-API EXT 全文 Read + 5 endpoint contract 抽出
- PLAN-072 frozen 状態確認 (helix handover status / pytest / bats)
- framework 候補を DoD 付きで列挙: Python 標準 http.server / Flask / FastAPI
- Sprint .0 成果物: `docs/v2/L4-sprint/PLAN-074-framework-candidates.md`

### Sprint .1 — HTTP framework 選定 (TL)

- 候補 3 種の比較 (依存、型安全、test harness、HELIX CLI との統合コスト)
- 既存 `cli/lib/*.py` との統合方針決定
- 認証方式 (API key / token) の暫定決定
- Sprint .1 成果物: framework 選定 ADR (docs/adr/) + 実装方針ドキュメント

**判断ポイント**:
- Python 標準 http.server: 依存 0 だが routing / validation が手書き
- Flask 2.x: 軽量、既存 Python 環境に馴染む、Blueprint で endpoint 分離しやすい
- FastAPI: Pydantic 型安全、OpenAPI 自動生成、依存追加コストあり

**本 PLAN では決定しない。Sprint .1 で TL が選定し、選定結果を以降の Sprint に注入する。**

### Sprint .2 — push / pr trigger endpoint 実装 (Codex SE)

対象: endpoint #1 / #2

- `POST /api/v1/automation/push/{plan_id}/trigger`
- `POST /api/v1/automation/pr/{plan_id}/trigger`
- 実装内容:
  - path_schema / query_schema / header_schema / request_schema validation
  - `push_gate.run_all_gates()` 呼び出し (execute フラグ連動)
  - `automation_runs` INSERT + lifecycle 遷移 (`_transition_lifecycle_status` 経由)
  - response に `run_id` / `gate_results` / `pair_transition` を含む Envelope 返却
  - audit_log への書き込み (run_id FK)
- テスト: pytest (正常系 / 異常系 / 境界値) + bats (HTTP レイヤ smoke test)

### Sprint .3 — hook callback / audit endpoint 実装 (Codex SE)

対象: endpoint #3 / #4

- `POST /api/v1/automation/hooks/{hook_kind}/callback`
- `POST /api/v1/automation/audit/log`
- 実装内容:
  - hook_kind enum 検証 (PreToolUse / PostToolUse / Stop / session_start)
  - request body の run_id FK 解決 (404 on not found)
  - audit_log append-only 書き込み (trigger は v26 で実装済み)
  - P1-01 対処: invocation_log 型衝突を hook callback と invocation_log の責務分離で解消
- テスト: pytest + bats (hook_kind ごとの分岐テスト含む)

### Sprint .4 — telemetry endpoint 実装 (Codex SE)

対象: endpoint #5

- `POST /api/v1/automation/session/telemetry`
- 実装内容:
  - request body の session_id / run_id 解決
  - `session_telemetry` UPSERT (`_upsert_row` 経由、v27 実装済み)
  - Stop hook 側との二重書き込み防止 (idempotency: session_id UNIQUE)
  - P1-02 対処: `helix_db.resolve_default_db_path()` を HTTP server プロセスでも統一使用
  - P1-03 対処: cost_usd float バリデーション helper を request schema validation に組込
- テスト: pytest (UPSERT 冪等性テスト) + bats

### Sprint .5 — 統合検証 + G4 判定 (TL + PMO Sonnet)

- 5 endpoint 全件 E2E 動作確認 (helix.db 実 DB 使用)
- PLAN-072 CLI 結合との挙動等価性確認 (push → HTTP vs push → CLI)
- `helix doctor` / `helix test` 全 PASS 確認
- D-API EXT 契約との差分 0 確認 (request / response / error code)
- G4 entry 条件チェックリスト (§7) を実施
- 残 debt を `deferred-findings.yaml` に記録

---

## §4 受入条件詳細

1. **endpoint 契約整合**: 全 5 endpoint が D-API EXT §3 の path / method / request_schema / response_schema / error_code と 1:1 整合
2. **DB 書き込み等価性**: HTTP 経由で CLI と同等の automation_runs / audit_log / session_telemetry 書き込みが発生する
3. **lifecycle 遷移**: push / pr trigger が `_transition_lifecycle_status` 経由で `pending → running → completed / failed` を正しく遷移する
4. **append-only 保護**: audit_log に対する UPDATE / DELETE が HTTP 経由でも trigger ブロック (v26 実装済みの確認)
5. **idempotency**: telemetry endpoint が session_id 単位で UPSERT 冪等動作する
6. **P1 解消**: P1-01 (invocation_log 型衝突) / P1-02 (HELIX_DIR 経路) / P1-03 (cost_usd float) を HTTP 実装内で解消
7. **回帰 0**: pytest / bats / helix-test 全 PASS 維持
8. **G4 通過**: §7 チェックリスト全件 passed

---

## §5 リスク

| ID | リスク | 影響 | 緩和策 |
|----|--------|------|--------|
| R-01 | HTTP framework 選定 (Sprint .1) が遅延し後続 Sprint がブロック | 全体遅延 | Sprint .0 で比較表を事前作成、TL 判断を 1 Sprint に集約 |
| R-02 | 認証方式未定 (API key / token / 無認証) が実装に波及 | 設計変更 | Sprint .1 で暫定 API key 認証として決定。本番認証は PLAN-075 carry 可 |
| R-03 | CORS / network binding (localhost only vs 0.0.0.0) | セキュリティ | 初期実装は localhost only + 127.0.0.1 bind。外部公開は別 PLAN |
| R-04 | push_gate.run_all_gates() が同期 long-run になり HTTP timeout | 性能 | async / subprocess dispatch を Sprint .2 で検討。timeout 30s 上限設定 |
| R-05 | P1-01〜03 の carry が Sprint .3〜.4 で想定外に複雑化 | 工数超過 | PLAN-072 exit-validation notes (phase-4.5-integration-notes.md) を Sprint .3 entry で必ず Read |
| R-06 | CLI 結合 (PLAN-072) との DB 書き込み二重発火 (CLI + HTTP 両方使用時) | データ整合 | Sprint .5 で二重書き込みシナリオを明示テスト。UNIQUE constraint を確認 |

---

## §6 依存関係

```
PLAN-070 (frozen) — L3 D-API EXT 契約起源
  └── PLAN-072 (frozen) — CLI 結合 + helix.db v27 稼働
        └── PLAN-074 (本 PLAN) — HTTP endpoint 層実装
              └── (未定) PLAN-075 — 認証強化 / 本番 network 設定 (carry 想定)
```

- PLAN-072 frozen が本 PLAN の entry 前提。未 frozen の場合は本 PLAN の Sprint .0 で blocked とする
- D-API EXT は契約のみ。HTTP server の framework / routing 実装は本 PLAN で初出
- D-DB EXT (v25-v27) は schema + helper 実装済み。本 PLAN では schema 変更を行わない

---

## §7 G4 entry 条件チェックリスト

G4 は Sprint .5 で実施する。全件 passed で G4 通過とする。

- [ ] 5 endpoint 全件が HTTP 200 / 400 / 409 / 500 を正しく返す (pytest 実証)
- [ ] `automation_runs.id` (run_id) が push / pr trigger レスポンスで返却される
- [ ] `audit_log` に trigger ごとの行が INSERT されている (bats 実証)
- [ ] `session_telemetry` が UPSERT 冪等で動作する (pytest 実証)
- [ ] P1-01 / P1-02 / P1-03 が全件 resolved (exit-validation notes 更新確認)
- [ ] `helix doctor` 0 fail (8 warn は既存 drift で許容済み)
- [ ] `python3 -m pytest cli/lib/tests/ -q --tb=short` 全 PASS
- [ ] `cli/helix test --no-pytest --bats-only` 全 PASS
- [ ] `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` 通過
- [ ] deferred-findings.yaml に残 debt が記録されている (または空)

---

## §8 Next Action

1. PMO Sonnet: D-API EXT 全文 Read + framework 候補整理 (Sprint .0)
2. TL: framework 選定 ADR 起草 (Sprint .1) — Flask / FastAPI / http.server の比較判断
3. TL 選定結果確認後、Sprint .2〜.4 を Codex SE 並列投入 (push/pr ∥ hook/audit ∥ telemetry は独立)
4. Sprint .5: TL + PMO Sonnet で統合検証 → G4 判定 → Opus commit
5. commit は Opus が Sprint .5 完了確認後に実施 (Codex は commit 禁止)

**並列可否**: Sprint .2 / Sprint .3 / Sprint .4 は framework 選定 (Sprint .1) 完了後に同時投入可能 (ファイル衝突なし、DB schema 変更なし)。
