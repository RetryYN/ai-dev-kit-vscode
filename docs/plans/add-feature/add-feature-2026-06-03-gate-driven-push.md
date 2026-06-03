---
plan_id: add-feature-2026-06-03-gate-driven-push
title: "Action: gate-driven push — G-review gate 追加 + raw git push guard + branch 安全化 (毎回承認の撤廃)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
workflow: add-feature
kind: add-impl
layer: L4
drive: be
status: completed
created: 2026-06-03
owner: PM
tl_review: approve
agent_slots:
  - role: tl-advisor
    slot_label: "TL — push gate 契約 / G-review / branch scope / classifier 変更 adversarial check（完了 2026-06-03、changes_required→P1 反映）"
  - role: se
    slot_label: "SE — push_gate.py / helix-push / bash guard / test の実装（Codex）"
generates:
  - artifact_path: cli/lib/push_gate.py
    artifact_type: python_module
  - artifact_path: cli/helix-push
    artifact_type: cli_extension
  - artifact_path: cli/lib/llm_guard.py
    artifact_type: python_module
  - artifact_path: docs/commands/push.md
    artifact_type: doc_update
  - artifact_path: HELIX-workflows/helix-process/github-operations.md
    artifact_type: doc_update
  - artifact_path: cli/lib/tests/test_helix_push.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/commands/push.md
  - HELIX-workflows/helix-process/github-operations.md
  - cli/lib/push_gate.py
---

# Action: gate-driven push（毎回承認の撤廃）

V2 実装計画 Process（親）の Phase 3「CI ↔ V-model gate 紐づけ」に属する子 Action。ユーザー要望「push の毎回手動承認が摩擦。PLAN完遂(TLレビュー+テスト通過)で push を仕組み化」に応える。承認を**消す**のでなく**機械 gate に委譲**する。tl-advisor 2026-06-03 判定（changes_required、P1 反映済）に基づく。

## 1. 現状（grep 裏取り）

- `helix push --gate --execute`（[push_gate.py](../../../cli/lib/push_gate.py) / [helix-push](../../../cli/helix-push)）が 6 gate（G-tests/G-catalog/G-secret/G-ff/G-attr/G-nondestructive）を機械検証し全 PASS で `git push` 自動実行する機構は**既にある**。
- 不足: (a) **raw `git push` の fail-close guard が存在しない**（helix-pre-bash に git push 処理なし＝確認済）→ 承認は私(Claude)の遵守頼みで機械的に止まっていない。(b) gate に「TL review / PLAN完遂」が無い。(c) `helix push` の default branch=main（auto-push と相性最悪）。

## 2. TL 裁定の反映（2026-06-03, changes_required→反映）

- **G-review gate 追加**（P1）。`--plan-id` explicit first。複数候補/0/handover 不一致は fail-close。
- **承認撤廃の範囲**: `helix push --gate --execute` 全 PASS = standing authorization。ただし **HELIX harness 経由の push のみ**。raw `git push` は deny 維持。`--execute` without `--gate` も deny。
- **branch scope**: dogfood / feature/* / hotfix/* は auto-push 可。**main は auto-push 不可**（`--allow-main --reason` + 人間判断）。default branch を main → current branch へ。
- **契約 drift 防止**（P1）: G-review 追加は gate id enum 変更を伴う → D-CONTRACT 同時更新。
- **正本**: push policy SSoT = `github-operations.md`。`docs/commands/push.md` = 利用導線（7 gate 化）。`CLAUDE.md` = リンク + 要約。

## 3. G-review の判定源（ユーザー承認 案A、2026-06-03）

我々の named PLAN（`reverse-...` 等）は `.helix/plans` registry にも `.helix/reviews` にも記録が無く、TL review も ad-hoc（`helix codex --role tl-advisor`）で機械記録されていない。よって v1 は **PLAN frontmatter を判定源**とする:

- G-review PASS 条件（対象 `--plan-id`）:
  1. PLAN frontmatter `status ∈ {completed, finalized}`。
  2. PLAN frontmatter `tl_review: approve`（TL review 通過時に PM が記録）。
  3. PLAN 特定: `--plan-id` → handover の active plan_id → ahead commit が touch した単一 PLAN の順。複数/0/不一致は fail-close。
- TL の「.helix 主・frontmatter 補助」志向とは **v1 で意図的に外す**（理由＝named PLAN に .helix 記録が無い現実）。frontmatter は plan_validator で機械検査される SSoT。
- **carry**: 番号 PLAN 向け `.helix/reviews/plans/<PLAN>.json`（`helix plan review` verdict）の正式統合を G-review の二次ソースに格上げ（v2）。

## 4. 作業

### 4a. 実装（Codex se 委譲）
1. **G-review gate**: `push_gate.py` に `run_gate_review(plan_id, project_root)` 追加（PLAN frontmatter の status + tl_review を read-only 検査、DB write しない）。`run_all_gates(..., plan_id=None, allow_main=False)` へ拡張。PLAN 特定 explicit-first + fail-close。
2. **helix-push**: `--plan-id PLAN-xxx` 追加。default branch を `main` → 現在 branch（`git rev-parse --abbrev-ref HEAD`）へ。`--branch main` かつ `--allow-main --reason` 無しは fail-close。`--execute` は `--gate` 必須維持。
3. **raw git push guard**: `cli/lib/llm_guard.py` の `inspect_command()`（line 3534。PreToolUse Bash guard `cli/libexec/helix-pre-bash` → `check-bash` の実体。既存の anti-evasion tokenizer + `GuardResult` + `HELIX_ALLOW_RAW_*` bypass 様式を再利用）に追加。`git push` / `git push --force` / `git push origin main` 等の raw push を **deny**。`helix push --gate --execute` は allow。`helix push --execute`（--gate 無し）は deny。bypass は `HELIX_ALLOW_RAW_PUSH=1` + 理由を evidence。
4. **test**（必須）: Python unit（G-review pass/fail、status 不一致、tl_review 欠落、plan-id 未指定/複数/不一致）/ bats（`--plan-id ... --branch dogfood` allow、`--branch main` block、`--allow-main` 扱い）/ guard test（raw `git push` deny、`helix push --gate --execute` allow、`--execute` without `--gate` deny）/ 契約 sync test（D-CONTRACT gate enum ⇔ push_gate gate ids 一致）。

### 4b. doc / 契約 正本（Opus 直接）
5. `D-CONTRACT`（gate id enum に G-review 追加）。
6. `docs/commands/push.md`（6→7 gate、--plan-id / --allow-main / default branch 変更を反映）。
7. `github-operations.md`（push policy SSoT 化: gate-routed push = authorized / raw push guarded / main PR-only / branch scope）。
8. `CLAUDE.md`（push rules を「helix push --gate --execute 全 PASS = 承認。raw git push は guarded。main は PR」へ更新、SSoT は github-operations.md へリンク）。

## 5. acceptance / 検証

- 新 gate test + guard test + 契約 sync test 全 PASS。`bash -n` / 対象 pytest / 対象 bats / `helix doctor`（24-0-105 維持か改善）。
- `helix push --gate --execute --plan-id <PLAN> --branch dogfood` が 7 gate 検証して push（dry-run で全 PASS 確認）。
- raw `git push` が guard で deny されること（手動 smoke）。
- main への auto-push が `--allow-main` 無しで block されること。
- D-CONTRACT enum と push_gate gate ids が一致（契約 drift ゼロ）。

## 6. forward_return

L4（gate 契約 enum）→ L7（push_gate / helix-push / guard 実装）→ L8（統合検証: gate 動作 + guard + 契約 sync）。親 Process の Phase 3「CI↔gate 紐づけ」へ収束。要件追加（add-feature）。

## 7. 適用（dogfood）

本機構完成後、**新ルール自身**で push する: handover-state-sync の 2 commit（`10a6412`+`8c5a027`）+ 本 Action の commit を、各 PLAN に `tl_review: approve` + `status: completed` を確認の上、`helix push --gate --execute --plan-id <PLAN> --branch dogfood` で origin/dogfood へ。

## 8. carry

- `.helix/reviews/plans/<PLAN>.json`（番号 PLAN の formal review）を G-review 二次ソースへ統合（v2）。
- 消費側配布: CLAUDE/AGENTS template・hook/settings 配布・setup/migrate 導線への反映（TL 指摘、本 repo 確定後）。
- **G-nondestructive 自己参照 false-positive**: 防御的 `--force`/`--no-verify` 記述（push-guard の doc/test）が destructive pattern scan に hit する。dry-run で実 block を確認し、必要なら gate を doc/test 除外へ refine（本 PLAN or 別 carry）。

## 9. closure（実装完了、2026-06-03）

- **PM 独立検証**（Codex summary 鵜呑みにせず実体確認）:
  - **guard smoke**: raw `git push`(+ `--force`/`-f`/`$(printf git)` 回避形) DENY、`helix push --gate --execute` allow、`helix push --execute`(--gate 無し) DENY、`git status`/`commit` 非過剰 block（9 cases ALL EXPECTED）。
  - 独立 pytest **111 passed**（llm_guard anti-evasion 回帰 + push_gate + helix_push + command_catalog 同期）。
  - bats helix-push **7/7**（main は `--allow-main`+`--reason` 必須 / 受理 / G-review 動作）。
  - 契約 sync test `test_gate_ids_match_contract_enum`（push_gate gate ids == D-CONTRACT §4.5 enum 7 件）PASS。
  - `helix doctor` 24-0-105 維持。Codex が `$(printf git) push` 回避形の guard 漏れを自己検出・解消。
- 承認の機械 guard 不在を解消: raw push は fail-close deny、`helix push --gate --execute` 7 gate 全 PASS = authorized。
- **forward_return**: L4(gate enum)→L7(実装)→L8(検証 passed)。Phase 3「CI↔gate 紐づけ」へ収束。
