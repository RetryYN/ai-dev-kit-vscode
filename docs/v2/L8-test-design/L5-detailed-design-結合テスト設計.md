---
doc_id: L8-test-design-L5-detailed-design-integration-test
title: HELIX-workflows V2 L5 詳細設計 結合テスト設計
status: frozen
freeze_evidence: "2026-06-03 V-model pair-freeze (L5↔L8): IT-* 21 を L5 設計 ID (MOD/IF/IP/DB) へ trace、trace_symmetry detector で coverage100%/uncovered0/orphan0/missing-pair0/balance1.0、tl-advisor adversarial check (P1 修正済)、Reverse 源泉 integration テスト実在確認。coverage は設計 coverage (gap=IT-MOD-06/IT-DB-03/IT-DB-05 は実装で追加)"
owner: QA
process_layer: L8
test_layer: L8
parent_design:
  - docs/v2/L5-detailed-design/モジュール分割設計.md
  - docs/v2/L5-detailed-design/IF詳細設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
  - docs/v2/L5-detailed-design/物理データ設計.md
pairs_design:
  - docs/v2/L5-detailed-design/モジュール分割設計.md
  - docs/v2/L5-detailed-design/IF詳細設計.md
  - docs/v2/L5-detailed-design/内部処理設計.md
  - docs/v2/L5-detailed-design/物理データ設計.md
related_decision: docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

# L5 詳細設計 結合テスト設計（L5↔L8 ペア）

> 本書は L5 詳細設計（モジュール分割 / IF詳細 / 内部処理 / 物理データ）の **結合レベル**検証を設計する L8 正本。HELIX-workflows は稼働中システムのため、結合テストは **既存テスト資産（pytest / Bats / verify）からの Reverse** で観測契約を起こし、未観測の結合点は gap として明示する。各 `IT-*` は L5 の `MOD-* / IF-* / IP-* / DB-*` ID へ trace し、設計↔テストの双方向対称を成立させる（trace_symmetry detector で機械検証）。

## 1. 目的と範囲

- **目的**: L5 で固定したモジュール境界・IF 契約・内部処理フロー・物理データ配置が、**モジュール間結合**で期待どおり連携することを検証する設計を与える。
- **範囲**: 結合粒度（CLI↔lib、route↔helix_db、hook↔harness、orchestration モジュール間、永続化境界）。単体関数粒度は L6↔L7、システム全体動作は L4↔L9 が扱う。
- **対ペア**: L5 4 doc（`pairs_test_design` で本書を相互宣言）。

## 2. 対象設計と検証方針

| L5 設計 doc | 付与 ID 群 | 結合検証の主眼 |
|---|---|---|
| モジュール分割設計 | `MOD-01`〜`MOD-07` | 分類境界・依存方向ルール（shell→Python core、route→envelope/db）の遵守 |
| IF詳細設計 | `IF-CLI-01` / `IF-HARNESS-01` / `IF-HTTP-01` / `IF-DB-01` | I/O 契約・envelope・auth・終了コード・error マッピング |
| 内部処理設計 | `IP-01`〜`IP-05` | Entry→Guard→Orchestration→Persistence→Automation の制御移譲・状態遷移・fail-close |
| 物理データ設計 | `DB-01`〜`DB-05` | 領域別テーブルの状態遷移・整合・additive migration |

## 3. ISO 29119-4 準拠方針

- **テスト技法**: 結合テストは「ユースケースベース」+「状態遷移」+「インターフェース」を主技法とする。
- **観点導出**: L5 の制御フロー（内部処理 §3-§6）と状態遷移表（automation_runs / handover / workspace）から遷移網羅、IF 契約表からインターフェース網羅を導く。
- **観測契約 Reverse**: 既存 pytest/Bats が realize している結合をまず観測契約として固定し、未観測（gap）は L8 実装フェーズで補完する設計とする。

## 4. 結合テスト観点（category）

| category | 観点 | 対応 L5 ID |
|---|---|---|
| `IT-MOD-*` | モジュール分類境界・依存方向の遵守 | `MOD-01`〜`MOD-07` |
| `IT-IF-*` | IF 契約（request/response/envelope/auth/exit code/error） | `IF-CLI-01`/`IF-HARNESS-01`/`IF-HTTP-01`/`IF-DB-01` |
| `IT-IP-*` | 内部処理パイプラインの制御移譲・状態遷移・fail-close | `IP-01`〜`IP-05` |
| `IT-DB-*` | 領域別データの状態遷移・整合・migration | `DB-01`〜`DB-05` |

## 5. 結合テストケース定義（IT-* ↔ L5 設計）

各 `IT-*` は対象設計（L5 の `MOD/IF/IP/DB` ID）へ対応づける。Reverse 源泉に既存テストがあるものを `observed`、未整備を `gap`（L8 実装で追加）と明示する。本表は IT-* の定義表かつ L5↔L8 双方向対応の正本（detector が test 定義 + coverage 源泉として読む）。

| IT ID | 対象設計 | 結合検証内容 | Reverse 源泉 / 状況 |
|---|---|---|---|
| IT-MOD-01 | MOD-01 | CLI Router の subcommand dispatch が正しい entrypoint へ exec し usage/exit code を返す | `tests/harness-hooks.bats` — observed |
| IT-MOD-02 | MOD-02 | Core Orchestration（route/plan/workspace/handover）のモジュール間連携 | `cli/lib/tests/test_workspace_manager.py`, `test_handover.py` — observed |
| IT-MOD-03 | MOD-03 | Guard/Policy が禁止操作・context 不整合・raw CLI を block | `tests/harness-hooks.bats` — observed |
| IT-MOD-04 | MOD-04 | Persistence の base schema + additive migration 整合 | `cli/lib/tests/test_helix_db_v34_v35.py` — observed |
| IT-MOD-05 | MOD-05 | HTTP Automation route↔`helix_db` の連携 | `cli/lib/tests/test_http_api_routes_push_pr.py` ほか — observed |
| IT-MOD-06 | MOD-06 | Catalog/Trace（code_catalog/contract_registry/doc_map_matcher）の索引整合 | gap（専用結合テスト未整備、L8 実装で追加） |
| IT-MOD-07 | MOD-07 | Hook/Harness の event 連携と wrapper 強制 | `tests/harness-hooks.bats` — observed |
| IT-IF-01 | IF-CLI-01 | CLI IF: subcommand dispatch + 終了コード契約（exit 0 / 不明 command exit 1） | `tests/harness-hooks.bats` — observed |
| IT-IF-02 | IF-HARNESS-01 | Harness IF: codex/claude/hook guard の role/task 注入・summary 収集 | `tests/harness-hooks.bats` — observed（部分） |
| IT-IF-03 | IF-HTTP-01 | HTTP IF: push/pr/hook/audit/telemetry endpoint の I/O 契約 + envelope + localhost/bearer auth + error マッピング | `cli/lib/tests/test_http_api_routes_push_pr.py`, `test_http_api_routes_hooks.py`, `test_http_api_routes_telemetry.py` — observed |
| IT-IF-04 | IF-DB-01 | DB API IF: insert/update helper の永続化契約と例外時 finalize | `cli/lib/tests/test_helix_db_v34_v35.py`, `test_integration_l45.py` — observed |
| IT-IP-01 | IP-01 | Entry pipeline: `helix`→`helix-*` の exec 委譲（router は判断を持たない） | `tests/harness-hooks.bats` — observed |
| IT-IP-02 | IP-02 | Guard pipeline: context/raw CLI/hook 整合の allow/block verdict | `tests/harness-hooks.bats` — observed |
| IT-IP-03 | IP-03 | Orchestration: handover/workspace の状態遷移と継続（stale 判定・merge 整合） | `cli/lib/tests/test_handover.py`, `test_workspace_manager.py` — observed |
| IT-IP-04 | IP-04 | Persistence flow: run/audit/session の SQLite 保存タイミングと整合 | `cli/lib/tests/test_helix_db_v34_v35.py` — observed |
| IT-IP-05 | IP-05 | HTTP automation flow: trigger→`automation_runs` INSERT→gate→`audit_log` の一連 | `cli/lib/tests/test_http_api_routes_push_pr.py`, `test_integration_l45.py` — observed |
| IT-DB-01 | DB-01 | Plan Governance: `plan_registry`/`plan_dependencies`/`plan_generates` の整合 | `cli/lib/tests/test_integration_l45.py` — observed（部分） |
| IT-DB-02 | DB-02 | Execution/Audit: `automation_runs`/`audit_log`/`session_telemetry` の状態遷移・UPSERT | `cli/lib/tests/test_http_api_routes_telemetry.py`, `test_integration_l45.py` — observed |
| IT-DB-03 | DB-03 | Trace Catalog: `code_index`/`entries`/`links`/`contract_entries`/`test_design_entries` の関係整合 | gap（専用結合テスト未整備、L8 実装で追加） |
| IT-DB-04 | DB-04 | Workspace/Continuity: `workspace_registry`/`sessions`/`locks`/`jobs` の継続・排他 | `cli/lib/tests/test_workspace_manager.py` — observed |
| IT-DB-05 | DB-05 | Requirements/Quality: `requirements`/`req_impl_map`/`req_test_map`/`verify_runs` の trace 整合 | gap（専用結合テスト未整備、L8 実装で追加） |

## 6. 合格基準（G8）

- L5 設計 ID（`MOD/IF/IP/DB` 計 21）が **全て 1 つ以上の `IT-*` で trace される**（trace_symmetry detector で L5↔L8 coverage 100% / uncovered 0 / missing-pair 0）。
- `observed` の IT は既存テストが green を維持する。
- `gap` の IT（IT-MOD-06 / IT-DB-03 / IT-DB-05）は L8 実装フェーズで結合テストを追加し、`observed` へ昇格する（§7 リスク参照）。
- L5↔L8 の双方向 frontmatter（L5 `pairs_test_design` ↔ 本書 `parent_design`/`pairs_design`）が解決する。

> **gate evidence の注記**: 本 coverage 100% は **設計 coverage**（21 の L5 設計 ID が `IT-*` で trace される）であり、**実装済テスト coverage ではない**。`gap`（IT-MOD-06 / IT-DB-03 / IT-DB-05）は L8 実装で結合テストを追加して `observed` へ昇格する（実装 coverage は反芻機構で別途追跡）。

## 7. 未検出リスク（gap）

| gap | 内容 | 暫定対応 |
|---|---|---|
| IT-MOD-06 | Catalog/Trace 系（code_catalog/contract_registry）の結合テスト未整備 | L8 実装で `helix code`/`helix entry` 経路の結合テストを追加 |
| IT-DB-03 | Trace Catalog テーブル群の関係整合テスト未整備 | code_index↔links↔contract_entries の結合検証を追加 |
| IT-DB-05 | Requirements/Quality（req_*_map/verify_runs）の結合テスト未整備 | requirements↔trace の結合検証を追加 |

> gap は「設計はしたが観測テスト未整備」を意味し、L8 設計 coverage（21/21）には含むが**実装 coverage は部分的**である。この区別を反芻機構で追跡する。

## 8. 自己検証チェックリスト

- [ ] `python3 cli/lib/trace_symmetry.py --json` で L5-L8 が missing-pair 0 / coverage 100% / orphan 0。
- [ ] 全 `IT-*`（21）が対象 L5 ID を 1 つ以上参照（orphan なし）。
- [ ] 全 L5 ID（21）が 1 つ以上の `IT-*` から参照（uncovered なし）。
- [ ] `observed` の Reverse 源泉ファイルが実在する。
- [ ] frontmatter の双方向 trace（L5 ↔ 本書）が解決する。
