---
plan_id: L6-source-scan-6detector-registration-closure
title: "source_scan allowlist 6 detector を functional-registry へ正規登録 (FN-WSC/UT-WSC/FR-LIB backfill, allowlist=0)"
kind: function-design
layer: L6
process_layer: L6
drive: be
status: completed
tl_review: approve  # tl-advisor 実 diff review 2026-06-22 = approve / P0 P1 none (worker=Codex se ≠ reviewer)。P2: review_evidence 文言 reviewer≠worker は model差分の意 (非ブロッキング・将来)
created: 2026-06-21
owner: PM
forward_return: "L6 機能設計 (FN-WSC-229..234) + L7 単体テスト設計 (UT-WSC-229..234) + L3 functional-registry (FR-LIB-160..165) へ既存 detector 実装を正規降下。source_scan_vs_registry の手動 allowlist 税 (SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS) を 0 化し、whole-source⊆design の honest baseline を確立する。F1 (自動登録 foundation) 着手前提の clean inventory。"
generates:
  - artifact_path: docs/v2/L6-functional-design/whole-source-coverage-機能設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L7-test-design/g7-test-anchor-map.yaml
    artifact_type: doc_update
  - artifact_path: cli/config/functional-registry.yaml
    artifact_type: doc_update
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: python_module
pairs_with:
  - L7
dependencies:
  parent: process-2026-06-08-verification-forward-gate
  requires: []
  blocks: []
related_docs:
  - docs/v2/audit/2026-06-14-weakness-forward-integration-map.yaml
  - docs/v2/L6-functional-design/whole-source-coverage-機能設計.md
---

# source_scan allowlist 6 detector 正規登録 closure Plan

## Purpose

ユーザーゴール「現在の実装をすべて棚卸しして機能一覧と紐づける」「実装に入れる障壁を全クリア」への対応。

`cli/lib/vg_overview.py` の `SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS`（L41-52）= 未登録実装 backlog の手動 suppress リスト（コメント明記「temporarily allowlisted until registry registration is handled in one action」「allowlist は F1(自動登録)が解消すべき税の一部」）。この 6 detector を functional-registry へ正規登録し allowlist を 0 化する＝棚卸しの完遂であり、whole-source⊆design の honest baseline 確立（F1 実装着手前の clean 状態）。

事前設計済み: `docs/v2/audit/2026-06-14-weakness-forward-integration-map.yaml:363-364` が「detector を whole-source-coverage docs に FN-WSC↔UT-WSC として正規登録 (L6 機能設計 + L7 単体テスト設計)」を解消方針として記録。本 PLAN はその残バッチ（FN-WSC-219..228 = 既登録 / 229..234 = 本 PLAN）を閉じる。

## Scope（6 detector、ID 連番）

| 実装ファイル | FN-WSC | UT-WSC | FR-LIB | test |
|---|---|---|---|---|
| cli/lib/anchor_quality.py | FN-WSC-229 | UT-WSC-229 | FR-LIB-160 | test_anchor_quality.py (21) |
| cli/lib/g8_subcheck.py | FN-WSC-230 | UT-WSC-230 | FR-LIB-161 | test_g8_subcheck.py (10) |
| cli/lib/g9_subcheck.py | FN-WSC-231 | UT-WSC-231 | FR-LIB-162 | test_g9_subcheck.py (11) |
| cli/lib/g12_subcheck.py | FN-WSC-232 | UT-WSC-232 | FR-LIB-163 | test_g12_subcheck.py (11) |
| cli/lib/g14_subcheck.py | FN-WSC-233 | UT-WSC-233 | FR-LIB-164 | test_g14_subcheck.py (11) |
| cli/lib/review_evidence_checks.py | FN-WSC-234 | UT-WSC-234 | FR-LIB-165 | test_review_evidence_checks.py (7) |

coverage_layer = `L6_required`（g7=FN-WSC-219 の sibling、FN↔UT 1:1）。l1_fr/l3_fr は gate-mechanism family として g7 に倣い `FR-08` / `FR-4ART-01`（review_evidence は description に即した最適 FR を選定、無ければ同 family）。

## 成果物（4 種 + allowlist 除去、in-place）

1. L6 `whole-source-coverage-機能設計.md`: FN-WSC-228 行直後に FN-WSC-229..234 を追加（FN-WSC-228 と同形式: module / signature / requires / ensures / invariant / test）。
2. L7 `whole-source-coverage-単体テスト設計.md`: UT-WSC-228 行直後に UT-WSC-229..234（UT-WSC-220 と同形式: UT↔FN / module / 反証内容 / 実装済）。
3. `g7-test-anchor-map.yaml`: UT-WSC-229..234 を該当 test_file path list で追加。
4. `cli/config/functional-registry.yaml`: FR-LIB-160..165 を FR-LIB-149 構造で追加（id/name/domain=lib/description/l1_fr/l3_fr/status=active/coverage_layer=L6_required/design_ids/test_design_ids/code_paths/doc_paths=[]）。
5. `cli/lib/vg_overview.py`: `SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS` から 6 path を全削除（空集合化）。

## Acceptance（機械検証）

- `helix doctor check_vg_overview --gate --json` で `required_clean` 全 green（特に `source_scan_vs_registry` / `registry_design_coverage` / `design_id_existence` / `fn_ut_pair_coverage` / `fr_uses_checks` / `registry_trace_complete`）かつ `overall_clean=True`。
- `SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS` が空（allowlist=0、suppress なしで clean）。
- 6 entry が registry に存在し coverage_layer=L6_required / design_ids↔test_design_ids が 1:1 / FN-WSC が L6 doc に出現 / UT-WSC が anchor map に存在。
- 全 pytest green（`python3 -m pytest cli/lib/tests/ -q`）。count-pin ripple（g7 canonical inventory / 各種件数）が出れば同 commit で同期。
- tl_review = approve（worker≠reviewer）。

## Result

実行: Codex se 委譲で 5 ファイル編集（131 insertions / 12 deletions）。

- **登録完遂**: FR-LIB-160..165（6 entry, coverage_layer=L6_required）/ FN-WSC-229..234（L6 機能設計）/ UT-WSC-229..234（L7 単体テスト設計 + anchor map）を正規登録。`SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS` を空集合化（allowlist=0）。
- **検証 green**: `helix doctor check_vg_overview --gate --json` = `overall_clean=true` / `required_clean` 全 true（`source_scan_vs_registry` は allowlist 逃がしでなく**真の登録**で clean）。`py_compile` PASS。`grep -c FN-WSC-23`=6 / `grep -c FR-LIB-16`=6。
- **flow_contract 89 passed**（我々の変更 + canonical handover）。当初の 5 failed は **本 diff 起因でないことを stash baseline で実証**（baseline でも 5/5 失敗＝「我々起因」ゼロ）。内訳: 4件＝`.helix/handover/CURRENT.{md,json}` 不在（8 missing_direct_file_refs が全て CURRENT.*、参照元は 2026-06-12/13 audit YAML で本 diff 未編集）、1件＝handover Next Action の boundary トークン契約。fa210be commit(23:09) 時は handover 存在 → green、その後 `2026-06-21T23-19-52` archive で露出した pre-existing 環境要因。canonical handover 復元で解消（gitignored S-tier のため commit 無影響）。
- **forward 収束**: 既存 detector 実装を L6 機能設計 + L7 単体テスト設計 + L3 registry へ正規降下し、whole-source⊆design の honest baseline（allowlist=0）を確立。F1（自動登録 foundation）着手前の clean inventory を達成。
