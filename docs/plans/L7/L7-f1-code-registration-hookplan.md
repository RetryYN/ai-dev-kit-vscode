---
plan_id: L7-f1-code-registration-hookplan
title: "L7-f1-code-registration-hookplan: F1-1 code 登録 PostToolUse hook (cli/**/*.py write → code_catalog 増分 + 未登録 advisory surface)"
kind: impl
layer: L7
drive: be
status: completed
process_layer: L7
parent_design: HELIX-workflows/helix-process/db-auto-registration.md
tl_review: approve  # tl-advisor: 初版 changes_required(P1 fail-open import/P1 full rebuild/P2 token) → 修正後 再レビュー approve 2026-06-22 (worker=Codex se ≠ reviewer)
created: 2026-06-22
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "F1 第一増分スコープ + 税回避 PLAN 方針 + P0/P1 落とし穴の諮問"
  - role: se
    slot_label: "実装: posttooluse-code-catalog-register hook + bats/pytest (実証パターン横展開)"
forward_return: "F1(登録自動化 foundation) の第一増分。driving=Reverse(設計-実装乖離=手動登録税の記録)→Add-feature(実装)。設計 SSoT=db-auto-registration.md §F1-1。Forward L7 実装として収束し、source_scan allowlist の再増殖を write 時 surface で防ぐ。"
pairs_test_design: []
generates:
  - artifact_path: .claude/hooks/posttooluse-code-catalog-register.sh
    artifact_type: cli_extension
  - artifact_path: cli/tests/posttooluse-code-catalog-register.bats
    artifact_type: test
dependencies:
  parent: null
  requires:
    - HELIX-workflows/helix-process/db-auto-registration.md
  blocks: []
related_docs:
  - docs/research/2026-06-21-no-leak-foundation-design-review.md
  - docs/plans/L6/L6-source-scan-6detector-registration-closureplan.md
---

# F1-1 code 登録 PostToolUse hook 実装 Plan（第一増分）

## Purpose

F1（登録自動化 foundation）の **第一増分**。設計 SSoT = [db-auto-registration.md §F1-1](../../../HELIX-workflows/helix-process/db-auto-registration.md)。

known_gap「code 変更 → code_catalog 自動 trigger 不在」を、**実証済み PostToolUse hook パターンの横展開**で塞ぐ（`posttooluse-plan-auto-register.sh`＝PLAN→plan_registry / `posttooluse-skill-catalog-rebuild.sh`＝SKILL.md→skill_catalog が稼働済）。

driving = **Reverse（設計-実装乖離の記録）→ Add-feature（実装）**。乖離 = 「設計は auto-registration を要求するが実装は手動」で、2026-06-22 の source_scan allowlist 6 detector 手動登録（[L6-source-scan-6detector-registration-closure](../L6/L6-source-scan-6detector-registration-closureplan.md)）でその税を実証済。本 PLAN はこの自動化に着手し、税の再発（allowlist の silent 再増殖）を write 時に surface で防ぐ。

## Scope（TL 諮問 2026-06-22 で確定した最小縦 slice）

第一増分は **F1-1 のみ**、かつ **advisory surface 止まり**（TL Q2）。FR-LIB / coverage_layer / design_id の自動付与は意味判断・設計帰属を含むため**含めない**（次増分以降）。

- **新規 hook** `.claude/hooks/posttooluse-code-catalog-register.sh`: Edit/Write/MultiEdit の対象が `cli/**/*.py`（`**/tests/**` 除外）のとき発火。
  1. 当該ファイルの **code_catalog 反映**（per-file upsert が困難なら、TL P1 に従い debounce 付き小範囲 rebuild + warning に留め、per-file DB upsert は次増分へ defer）。
  2. 当該ファイルが `cli/config/functional-registry.yaml` の `code_paths` に**未登録なら advisory warning** を `systemMessage` で surface（write は止めない）。
- **二段構え**（F1-1 設計 / TL）: hook は advisory（fail-open `decision=continue`）、未登録の取りこぼしは後段 `source_scan_vs_registry` detector が fail-close で拾う。
- settings 配線（`HELIX_HOOKS` PostToolUse）。既存 hook は大改造せず、新 script + 共有 payload helper 利用に留める（TL リファクタ判断）。

## 必達ガード（TL P0/P1）

- **P0 無限ループ/再入防止**: hook 自身の DB/JSONL/cache 書き込みが再発火しない経路。`HELIX_HOOK_RUNNING` 相当の再入 guard、対象 glob 限定。
- **P0 write block 化しない**: 失敗時も `{"decision":"continue"}` を返す fail-open。python3 不在等でも exit 0。
- **P1 冪等性**: 同一 path の再 write で code_catalog の重複 id が増えない。

## Acceptance（F1-5 由来 + テスト実走）

- **Bats** `cli/tests/posttooluse-code-catalog-register.bats`: payload path 抽出 / 対象 glob（cli/lib/x.py 発火）・非対象（tests/、docs/、.md 非発火） / fail-open（不正 payload でも continue） / 再入 guard。
- **pytest**: 新規 .py を hook 経由で処理 → code_catalog に当該 module/symbol が現れる / 同一 path 二重処理で重複 id が増えない。
- `bash -n` + 既存 hook 回帰（merge_settings / hook 配線テスト）green。
- 全 gate（vg_overview overall_clean=true 維持、source_scan_vs_registry clean 維持）。
- tl_review = approve（worker≠reviewer）。

## 非スコープ（次増分）

F1-2（yaml→md view 生成）/ F1-3（設計定義 DbC 登録）/ F1-4（generates 反映）/ per-file 精密 upsert / FR-LIB・coverage_layer 自動付与。物理 schema は登録要求が detector で観測されてから（推測 schema 回避）。

## Result

実装: Codex se 委譲。新規 hook `.claude/hooks/posttooluse-code-catalog-register.sh` + bats + pytest + settings/merge_settings 配線 + 新 hook 自身の registry 登録。

- **guard 実装確認**（PM read）: 再入 guard（`HELIX_HOOK_RUNNING` token, L20）/ fail-open（空 payload・python3 不在・全例外経路で `{"decision":"continue"}` exit 0）/ glob 限定（cli/**/*.py のみ、tests/・docs 除外）。settings は `blockOnFailure:false`、merge_settings canonical source と整合（auto-regen noise でない）。
- **二段構え**: hook=advisory（write 非 block）、未登録取りこぼしは後段 `source_scan_vs_registry` fail-close。
- **スコープ厳守**: advisory surface 止まり。FR-LIB/coverage_layer/design_id 自動付与は未実施（次増分）。
- **検証 green**（PM 独立実走）: bats 5/5（glob 発火・非対象 skip・不正/空 payload fail-open・再入 guard）/ pytest 34 passed（新 hook + merge_settings + security_hardening 回帰）/ vg_overview `overall_clean=true`・source_scan/registry/fr_uses/trace 全 clean / bash -n PASS。
- **forward 収束**: F1-1（code→code_catalog auto-trigger 不在）を実証パターン横展開で実装。allowlist の silent 再増殖を write 時 surface で防ぐ。次増分=F1-2（yaml→md view 生成）/ per-file 精密 upsert / 設計定義登録。

**TL review changes_required → 修正対応**（worker=Codex se、reviewer=tl-advisor）:
- P1-1 fail-open import 漏れ → shell `OUT=$(python3...)` 捕捉 + 非ゼロ/無出力で `emit_continue_json` 二重防御。
- P1-2 フル rebuild → `code_catalog.upsert_catalog_paths` で target file のみ scoped upsert（全 rebuild 撤廃）。
- P2 token 部分一致 → `hook_running_exact_match`（comma split + exact ==）。
- 再検証 green: bats 9/9（import/jsonl/DB 失敗 fail-open + scoped 追加）/ pytest 41 passed / vg overall_clean=true / bash -n PASS。

**regression 修正**（gate-push G-tests が捕捉）: 初回 push で `helix code stats --uncovered`（test-helix-code.bats 15-34）が全滅 → causation 実証（code_catalog.py のみ baseline 復帰で復活）= sync_to_db リファクタ起因。修正: sync_to_db を baseline 実装へ撤回し `upsert_catalog_paths`/`sync_paths_to_db` を additive 化（proven パス不変）。再検証: test-helix-code.bats 44/44 / hook bats 9/9 / pytest 64 passed / vg overall_clean=true。

status: draft → completed（TL 再レビュー approve、regression 修正は test-verified 後 push）。
