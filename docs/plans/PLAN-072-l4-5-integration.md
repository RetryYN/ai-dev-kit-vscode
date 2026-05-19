---
plan_id: PLAN-072
title: "PLAN-072: L4.5 Phase B 結合 (v24-v27 helix.db 実 endpoint/hook/CLI 統合)"
status: frozen
size: L
drive: fullstack
created: 2026-05-16
frozen_at: 2026-05-16
owner: PM
phases: L4.5, L5, L6
gates: G4
gate_status: G4_ready
凍結根拠: |
  Sprint .1〜.6 全完遂 (11 commits, 1c1bc8b..dce1b5f)。pytest 1285 / bats 478 / shell 614 全 PASS。
  helix doctor 0 fail (8 warn は既存 PLAN 群の drift、PLAN-072 と無関係)。
  P0/P1 エラーなし。実装スコープは CLI (helix-push/pr/plan) + hook (.claude/hooks/*.sh + libexec/helix-session-start) の結合。
  HTTP endpoint (push/pr/hook/audit/telemetry 5 endpoint) の HTTP 層実装は別 PLAN carry とする (D-API EXT は契約のみ凍結済)。
acceptance:
  - v24 design_sprint_drive_decisions を drive switch policy 評価フローに結合 (helix-plan / helix-codex で書き込み)
  - v25 automation_runs を helix-push / helix-pr / hook / gate 実行フローに結合 (lifecycle 遷移を `_transition_lifecycle_status` 経由で実施)
  - v26 audit_log を全 endpoint / hook / CLI 実行時に書き込み (run_id FK 経由で automation_runs 紐付け)
  - v27 session_telemetry を Stop hook / SessionStart hook で UPSERT 書き込み (session_id 単位)
  - P1-01 (invocation_log 型衝突) 対処: hook callback endpoint と invocation_log の責務分離設計
  - P1-02 (HELIX_DIR 解決経路) 対処: hook プロセスと HTTP endpoint プロセスで `helix_db.resolve_default_db_path()` 統一
  - P1-03 (_validate_positive_number) 対処: cost_usd float バリデーション helper 追加
  - bats / pytest 全 PASS 維持 (回帰 0)
  - G4 entry 条件達成 (実装 + テスト + ドキュメント整備)
related:
  - PLAN-070-l3-schema-and-contract-design (frozen 親 L3)
  - PLAN-071-carry-capability-detailing (draft, 並行進行)
  - docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md (Sprint .5 endpoint contract)
  - docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md (v25-v27 schema)
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md (mock_to_implementation + functional_freeze CLI 契約)
  - docs/v2/L3-detailed-design/exit-validation/phase-4.5-integration-notes.md (P0/P1 解消マップ)
---

# PLAN-072: L4.5 Phase B 結合

## §1 目的と背景

PLAN-070 L4 (Phase 5-9) で v24-v27 helix.db テーブル + helper 3 件 + trigger 7 件を完遂した
(commit f8fd0a9)。しかし以下の統合 work は未着手のまま:

- v24 `design_sprint_drive_decisions`: drive switch policy 評価時の INSERT 呼び出し元なし
- v25 `automation_runs`: helix-push / helix-pr / hook / gate 実行フローとの接続なし
- v26 `audit_log`: 全 endpoint / hook / CLI からの書き込みなし
- v27 `session_telemetry`: Stop hook / SessionStart hook からの UPSERT なし

D-API EXT / D-CONTRACT は契約のみ凍結済み (PLAN-070 L3)。
本 PLAN でその契約を実実装に落とし込み、G4 ready 状態を達成する。

## §2 対象範囲

### 2.1 v24 design_sprint_drive_decisions 結合

対象テーブル: `design_sprint_drive_decisions`
- `helix-plan` の drive switch policy 評価フロー内で decision (preserved/waived/failed) を INSERT
- `source_entry_id` / `target_entry_id` は `design_sprint_entries` から FK 取得
- 書き込み関数: `helix_db.insert_drive_decision(plan_id, source_entry_id, target_entry_id, decision, reason)`

### 2.2 v25 automation_runs 結合

対象テーブル: `automation_runs`
- `helix-push` / `helix-pr` / hook / gate 実行開始時に `INSERT` (status=pending)
- 実行中: `_transition_lifecycle_status(run_id, 'pending', 'running')` を呼び出し
- 完了時: `_transition_lifecycle_status(run_id, 'running', 'completed')` または `'failed'` / `'cancelled'`
- `trigger_source` は呼び出し元 (helix-push / helix-pr / hook / gate) を識別文字列で設定
- `run_id` は `audit_log` / `session_telemetry` の FK として伝播

### 2.3 v26 audit_log 結合

対象テーブル: `audit_log`
- 全 endpoint / hook / CLI 実行時に `kind` 別で INSERT
  - hook 実行: kind=`hook_exec`
  - gate 実行: kind=`gate_eval`
  - CLI 実行: kind=`cli_invocation`
  - endpoint 呼び出し: kind=`endpoint_call`
- `run_id` FK で `automation_runs` の対応行に紐付け
- `actor` は呼び出し元 (session_id / hook_type / cli_name) を設定

### 2.4 v27 session_telemetry 結合

対象テーブル: `session_telemetry`
- `.claude/hooks/stop.sh` の Python heredoc 内で session_id 単位 UPSERT
- `tool_uses_count` / `tokens_total` / `cost_usd` を Stop hook の環境変数 / stdout から集計
- `cli/libexec/helix-session-start` で session 開始レコードを先行 INSERT (cost_usd=0.0 初期値)
- `_upsert_row('session_telemetry', {'session_id': ...}, update_fields)` を使用
- 実装注: hooks は bash + Python heredoc 構成 (実態に合わせる)。`.py` 表記は誤り。

## §3 Sprint 構成

| Sprint | 目的 | 委譲先 | 対象ファイル (主) |
|--------|------|--------|-----------------|
| Sprint .1 | helix-push / helix-pr に automation_runs INSERT + lifecycle 遷移統合 | Codex SE | `cli/helix-push`, `cli/helix-pr`, `cli/lib/helix_db.py` |
| Sprint .2 | `.claude/hooks/` に audit_log 書き込み統合 (hook_exec / gate_eval kind) | Codex SE | `.claude/hooks/*.sh` (Python heredoc 部), `cli/lib/helix_db.py` |
| Sprint .3 | Stop hook / SessionStart hook に session_telemetry UPSERT 統合 | Codex SE | `.claude/hooks/stop.sh`, `cli/libexec/helix-session-start` |
| Sprint .4 | helix-plan drive switch policy 評価フローに design_sprint_drive_decisions INSERT 結合 | Codex SE | `cli/helix-plan`, `cli/lib/helix_db.py` |
| Sprint .5 | P1-01/02/03 一括解消 (invocation_log 責務分離 / HELIX_DIR 統一 / cost_usd validation helper) | Codex SE | `cli/lib/helix_db.py`, `.claude/hooks/*.sh`, `cli/lib/validation.py` |
| Sprint .6 | E2E test: helix-push 実行 → automation_runs + audit_log + session_telemetry 3 テーブル一括書き込み確認 | Codex SE | `cli/lib/tests/test_integration_l45.py`, `cli/tests/l45_integration.bats` |
| Sprint .7 | exit validation (cross-doc + bats + pytest + helix doctor) + G4 ready 判定 | TL/PM | — |

Sprint .1-.4 は相互ファイル衝突なし → **並列投入可能**。Sprint .5 は .1-.4 完了後に直列。
Sprint .6 は .5 完了後。Sprint .7 は .6 完了後。

## §4 受入条件詳細

### Sprint .1 DoD
- `helix-push` 実行時に `automation_runs` に `trigger_source='helix-push'` で INSERT されること
- `helix-pr` 実行時に同様に INSERT されること
- `_transition_lifecycle_status` 経由で pending→running→completed/failed が遷移すること
- `pytest cli/lib/tests/test_automation_runs.py` PASS

### Sprint .2 DoD
- hook 実行ごとに `audit_log` に `kind='hook_exec'` で INSERT されること
- `run_id` FK が `automation_runs` の対応行を参照すること
- gate 実行時に `kind='gate_eval'` で INSERT されること
- 既存 hook の latency 増大が +50ms 以内であること (測定記録)

### Sprint .3 DoD
- Stop hook 実行後に `session_telemetry` が UPSERT されること
- `cost_usd` が float として格納されること (P1-03 解消を前提)
- SessionStart hook で先行 INSERT が行われること
- `pytest cli/lib/tests/test_session_telemetry.py` PASS

### Sprint .4 DoD
- `helix-plan` の drive switch policy 評価時に `design_sprint_drive_decisions` に INSERT されること
- `decision` が preserved/waived/failed の正しい値で格納されること
- `source_entry_id` / `target_entry_id` が `design_sprint_entries` の実在 FK であること
- `pytest cli/lib/tests/test_drive_decisions.py` PASS

### Sprint .5 DoD
- P1-01: `invocation_log` と hook callback endpoint の責務を分離し型衝突が解消されること
- P1-02: hook プロセスと HTTP endpoint プロセスで `helix_db.resolve_default_db_path()` を統一使用していること
- P1-03: `_validate_positive_number(value, field_name)` helper が `cli/lib/helix_db.py` に追加され、`cost_usd` 書き込み前に呼び出されること
- `pytest cli/lib/tests/test_validation.py` PASS

### Sprint .6 DoD
- `helix-push` を実際に実行し、以下が 1 run で同時充足されること:
  - `automation_runs` に 1 行 INSERT
  - `audit_log` に 1 行以上 INSERT (run_id FK 参照)
  - `session_telemetry` に UPSERT
- `cli/tests/l45_integration.bats` が PASS
- `pytest cli/lib/tests/test_integration_l45.py` が PASS

### Sprint .7 DoD
- `helix doctor` が P0/P1 エラーなし
- `bats cli/tests/` 全 PASS (回帰 0)
- `pytest cli/lib/tests/` 全 PASS (回帰 0)
- cross-doc 整合 (D-API EXT / D-DB EXT / D-CONTRACT と実装の乖離なし)
- G4 entry 条件チェックリスト全項目 checked

## §5 リスク

| ID | リスク | 深刻度 | 緩和策 |
|----|--------|--------|--------|
| R-01 | 既存 `invocation_log` への型衝突 (P1-01 未解消の場合) | P1 | Sprint .5 で先行解消、.1-.4 では invocation_log に触れない |
| R-02 | HELIX_DIR 解決経路の hook ↔ endpoint 乖離 (P1-02) | P1 | Sprint .5 で `resolve_default_db_path()` 統一前に hook 書き込みを実装しない |
| R-03 | audit_log 書き込みによる hook latency 増大 | P2 | Sprint .2 DoD で +50ms 以内計測、超過時は async write 検討 |
| R-04 | automation_runs FK 参照エラー (run_id 未挿入タイミング) | P1 | INSERT 順序を automation_runs → audit_log の順序で固定 |
| R-05 | session_telemetry の cost_usd が NULL / 負値 | P2 | Sprint .5 P1-03 (_validate_positive_number) で事前 guard |
| R-06 | backward compatibility: 既存 helix-push 利用者への挙動変化 | P2 | automation_runs 書き込み失敗時は WARNING のみ、push 処理は中断しない |

## §6 依存関係

- **PLAN-070 (L3 frozen)** — 完了 (D-API EXT / D-DB EXT / D-CONTRACT 凍結済み)
- **PLAN-070 L4 (Phase 5-9 完遂)** — 完了 (commit f8fd0a9、v24-v27 テーブル + helper + trigger 実装済み)
- **PLAN-071 (capability detailing)** — 並行進行可能 (独立ファイル群、衝突なし)

Sprint .1-.4 は相互独立 → 並列投入。Sprint .5 は .1-.4 全完了後。

## §7 G4 entry 条件チェックリスト

- [x] Sprint .1: helix-push / helix-pr automation_runs 統合 PASS (commits 1c1bc8b, 981ce45)
- [x] Sprint .2: hook audit_log 統合 PASS (commit ed548f2、hook latency delta +43.29ms <50ms)
- [x] Sprint .3: session_telemetry UPSERT 統合 PASS (commits 25bd341, 4001059、hook latency delta +45.51ms <50ms)
- [x] Sprint .4: design_sprint_drive_decisions 統合 PASS (commit 3a3b5a0)
- [x] Sprint .5: P1-01/02/03 一括解消 PASS (commits 14075c6, 672cc2e, f465a2b)
- [x] Sprint .6: E2E test 3 テーブル一括書き込み確認 PASS (commit dce1b5f、pytest 2 + bats 1)
- [x] Sprint .7: bats + pytest 全 PASS + helix doctor 0 fail + cross-doc 整合確認 (本 Sprint)
- [x] G4 ready 宣言 (TL/PM 承認、2026-05-16)

### G4 ready 整合性検証 (Sprint .7)

| 項目 | 状態 | 根拠 |
|------|------|------|
| pytest 全 PASS | ✅ 1285/1285 (+24) | Sprint .1〜.6 で test 24 件追加、全回帰 0 fail |
| bats 全 PASS | ✅ 478/478 (+7) | Sprint .1〜.6 で test 7 件追加、全回帰 0 fail |
| shell-based 全 PASS | ✅ 614/614 | 既存維持 |
| helix doctor | ✅ 14 pass, 0 fail, 8 warn | warn は既存 PLAN 群の drift (PLAN-072 と無関係) |
| D-DB EXT vs 実装 | ✅ 一致 | automation_runs.plan_id 列存在 / trigger_source は summary JSON 格納で一致 |
| 実装スコープ | ✅ CLI + hook 結合 | HTTP endpoint (5 endpoint) の HTTP 層実装は別 PLAN carry |
| hook latency | ✅ max +45.51ms | DoD <=50ms 内 |

### carry / 次 PLAN への引継ぎ

- HTTP endpoint (push/pr/hook/audit/telemetry 5 endpoint) の HTTP 層実装 → 別 PLAN
- PLAN-071 (capability detailing、L3 carry 11 件詳細化) → 別 PLAN、独立進行
- helix doctor warn (skills/agents/roles count drift、phase.yaml v3→v4) → 別 PLAN または保守 PLAN
- `_main__` 後の helper 配置 (cli/lib/helix_db.py line 3247+) の refactor → 別 PLAN
- [ ] G4 ready 宣言 (TL/PM 承認)

## §8 next action

次セッションで Sprint .1-.4 並列投入から着手する。

並列投入前の衝突確認:
- Sprint .1 (helix-push, helix-pr): ファイル衝突なし
- Sprint .2 (.claude/hooks/*.sh): ファイル衝突なし
- Sprint .3 (.claude/hooks/stop.sh, cli/libexec/helix-session-start): Sprint .2 と hooks/*.sh が重複 → Sprint .2 完了後に直列
- Sprint .4 (helix-plan): ファイル衝突なし

修正: Sprint .1 ∥ Sprint .2 ∥ Sprint .4 を並列、Sprint .3 は Sprint .2 完了後。

投入順序:
1. Sprint .1 ∥ Sprint .2 ∥ Sprint .4 (並列)
2. Sprint .3 (Sprint .2 完了後)
3. Sprint .5 (.1-.4 完了後)
4. Sprint .6 (.5 完了後)
5. Sprint .7 (.6 完了後)

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

- 監査ログ（Audit Log）
  - PostgreSQL の公式コミュニティ資料では、変更トリガ関数を介して DML（INSERT/UPDATE/DELETE）イベントを監査テーブルへ記録する実装例が示されており、`audit_log` をイベントとして扱う PLAN-072 の方針と整合する。
  - SQLite の `CREATE TRIGGER` 仕様は、行単位でのイベント処理（`AFTER` / `BEFORE`）を前提としているため、`automation_runs` / `session_telemetry` のトランジションログ追加方針を補強する。
  - 両方の運用で示される append-only 中心設計（更新・削除権限の分離）を踏まえ、監査データの保全性設計を PLAN-072 の監査トレース運用ルールに反映する。
- CI/CD 可観測性（Automation Runs Telemetry）
  - GitLab CI/CD Observability は pipeline/job/step の実行フロー観測を前提としており、PLAN-072 の `automation_runs` 集約と一致する評価軸を提供する。
  - Buildkite はパイプラインイベントを OpenTelemetry へ送る統合パターンを示しており、将来の自動計測エクスポート設計と整合する。
  - GitHub Actions は workflow run ログと実行状態の取得 API を前提にした可観測性基盤があるため、本 PLAN の運用監査ログ設計と親和性が高い。
- イベント統合（Event-driven Integration）
  - Martin Fowler のイベント駆動アーキテクチャ定義は、イベント生成と購読の分離を主張し、`automation_runs` → `audit_log` → `session_telemetry` のデータフロー分離方針を支持する。
  - Amazon EventBridge はイベントスキーマ・ルーティング前提のイベントバス、Kafka は高スループットのストリーミング統合基盤として、PLAN-072 の将来外部連携設計（carry）に適合する比較対象を提供する。

### 主要参照リンク

- PostgreSQL Audit Trigger: https://wiki.postgresql.org/wiki/Audit_trigger
- SQLite CREATE TRIGGER: https://www.sqlite.org/lang_createtrigger.html
- GitLab CI/CD Observability: https://docs.gitlab.com/operations/observability/ci_cd/
- GitLab Observability overview: https://docs.gitlab.com/operations/observability/observability/
- Amazon EventBridge event reference: https://docs.aws.amazon.com/eventbridge/latest/userguide/event-reference.html
- Amazon EventBridge schema: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schema.html
- Apache Kafka design: https://docs.confluent.io/kafka/design/index.html
- Buildkite observability: https://buildkite.com/docs/pipelines/best-practices/monitoring-and-observability
- GitHub Actions workflow run logs: https://docs.github.com/en/actions/how-tos/monitoring-and-troubleshooting-workflows/monitoring-workflows/using-workflow-run-logs
- Martin Fowler Event-driven: https://martinfowler.com/articles/201701-event-driven.html

## Revision History

- W5c-7 (2026-05-19): `docs/plans/PLAN-072-l4-5-integration.md` に「業界 standard 参照 (Web 検索 retrofit 2026-05-19)」を追加し、`W5c-7` の履歴を追記。既存 section は変更せず、末尾追記のみ反映。
