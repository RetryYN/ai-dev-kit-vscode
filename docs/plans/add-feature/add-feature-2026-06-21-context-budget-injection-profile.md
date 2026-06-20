---
plan_id: add-feature-2026-06-21-context-budget-injection-profile
title: "Action(add-feature): helix context に context budget / injection profile surface を追加(自動走行の tool-call 安定化)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: HELIX-workflows/helix-process/layer-context-injection.md  # 注入プロファイルと予算(kernel/task/implementation/recovery)の設計正本。本 Action はこの設計を additive に凍結し context_guard に surface する。
forward_return: "L4/L5 相当の context-injection 設計(layer-context-injection / continuous-run-context-management)へ injection profile + budget を additive 凍結 -> L7 context_guard.py で check_context()/context_bundle() に context_budget/context_profile を surface(新キー additive、既存キー不変)-> helix context check --json / bundle の実走 evidence -> L6↔L7 G7 pending gate evidence に帰属。"
drive: be
status: completed
status_note: "2026-06-21 完遂(ユーザー /goal 後続: 素性不明の未コミット context-budget 変更 7 ファイルを HELIX 規律に乗せて整備 -> commit -> push)。① context_guard.py に CONTEXT_BUDGET(max_total_tokens=150000 / output_reserve_min=50000 / fresh_session_threshold_pct=0.70 等)+ CONTEXT_PROFILE(profile=task, always_on/dynamic_load/exclude)定数 + _context_budget_report()(core-manifest.tsv エントリ数 + handover status を読む)を追加し、check_context() 出力に context_budget/context_profile キーを additive 追加・context_bundle() に '## HELIX Context Budget' セクションを追加。② layer-context-injection.md に '注入プロファイルと予算'(4 profile 表 + budget 制約)、continuous-run-context-management.md に 'context hygiene baseline'(運用ルール 5 項)を追加。③ 利用導線 doc(ai-harness/index/D-HOOK-SPEC)に budget/profile 言及を追加。④ PM 整備: 新規 test の no-op assert(`assert \"- profile: task\"` の比較対象欠落)を `in text` 付きへ修正。検証: py_compile OK / test_context_guard 16 passed / helix context check --json で context_budget+context_profile(core_manifest_entries=5)surface / helix context bundle で budget セクション描画 / skill_dispatcher は独自 build_context_bundle で無関係(PM 確認)。"
current_task_scope: context_budget_injection_profile_surface
approval_required_before_l7_work: false  # ユーザー「整備してコミットしてプッシュを。」(2026-06-21)= 明示承認
ticket_is_completion_evidence: false
tl_review: approve  # tl-advisor impl review(2026-06-21, run baqprpkdy)= approve / decision: passed。P0/P1/P2 なし。P3 Optional(非ブロッキング)= fresh_session_threshold_pct=0.70 は max_total_tokens=150000 に対し残 45000 < output_reserve_min=50000 で厳密には reserve を下回る(現状は表示用 budget で enforcement でないため非ブロッキング。将来 enforce 時は 0.66 近辺 or reserve 算出式の明文化を検討、ユーザー選定値につき本 Action では 0.70 を維持)。TL 判定: scope=対象7ファイル一致 / check_context は既存キー維持+additive / context_bundle は非安定 JSON でセクション追加のみ / exit code 不変 / D-API/D-DB/D-CONTRACT/schema/env/secret/本番影響なし / doc↔code 値(150000/50000/0.70)一致 / 新規 test は blast radius に十分。
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L4/L5↔L7: context-injection 設計(layer-context-injection / continuous-run-context-management)↔ context_guard.py の budget/profile surface"
design_change_class: contract_extension  # check_context()/context_bundle() に新キー・新セクションを additive 追加 = 振る舞い追加(pure_impl ではない)。再凍結 scope: layer-context-injection / continuous-run-context-management の context-injection 設計 + 対応 test。公開 API 既存キー・exit code・registry schema は不変、新キーは追加のみ。
agent_slots:
  - role: tl-advisor
    slot_label: "TL — context-budget feature の scope / additive 性 / doc↔code 整合 / budget 値妥当性の adversarial check(.helix/tasks/tl-review-context-budget.md)"
generates:
  - artifact_path: cli/lib/context_guard.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_context_guard.py
    artifact_type: test
  - artifact_path: HELIX-workflows/helix-process/layer-context-injection.md
    artifact_type: doc_update
  - artifact_path: HELIX-workflows/helix-process/continuous-run-context-management.md
    artifact_type: doc_update
  - artifact_path: docs/commands/ai-harness.md
    artifact_type: doc_update
  - artifact_path: docs/commands/index.md
    artifact_type: doc_update
  - artifact_path: docs/design/D-HOOK-SPEC.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks: []
---

# context budget / injection profile surface (add-feature Action)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。本 Action は、自動走行(continuous run)時の tool-call 安定性を守るため、注入予算(context budget)と注入プロファイル(injection profile)を機械可読で surface する additive feature を landing する。

## 背景

自動走行ではセッション context が単調増加し、tool-call 失敗の温床になる。HELIX は注入量を「必要なものを増やす」だけでなく「常時注入しないものを決める」機構を持つべきで、その予算と profile を `helix context check` / `helix context bundle` から観測可能にする。

本 Action は、素性が PLAN/handover に紐づかないまま working tree に残っていた context-budget 変更 7 ファイル(2026-06-21 00:00-02 編集)を、ユーザー指示「整備してコミットしてプッシュを。」に従い HELIX 規律(PLAN + TL review + 検証 + gate push)へ収束させるものである。

## 変更内容

| ファイル | 種別 | 内容 |
|---|---|---|
| cli/lib/context_guard.py | python_module | CONTEXT_BUDGET / CONTEXT_PROFILE 定数 + `_context_budget_report()` を追加。check_context() に context_budget/context_profile キーを additive 追加、context_bundle() に budget セクション追加 |
| cli/lib/tests/test_context_guard.py | test | budget セクション描画 + check_context budget/profile キーの test 追加(PM が no-op assert を修正) |
| HELIX-workflows/helix-process/layer-context-injection.md | doc_update | 「注入プロファイルと予算」節(kernel/task/implementation/recovery profile 表 + budget 制約) |
| HELIX-workflows/helix-process/continuous-run-context-management.md | doc_update | 「context hygiene baseline」節(budget を context check --json の正とする運用ルール 5 項) |
| docs/commands/ai-harness.md / index.md | doc_update | helix context の説明に budget/profile 言及を追加 |
| docs/design/D-HOOK-SPEC.md | doc_update | context budget 超過行を budget/profile 表示へ更新 |

## 受入条件 / 検証

- `python3 -m py_compile cli/lib/context_guard.py` OK。
- `python3 -m pytest cli/lib/tests/test_context_guard.py` 16 passed(新規 2 + assert 修正含む)。
- `helix context check --json` が context_budget(max_total_tokens=150000 等)と context_profile(profile=task, core_manifest_entries=5)を返す。
- `helix context bundle` が `## HELIX Context Budget` セクションを描画する。
- behavior-preserving の境界: check_context()/context_bundle() の既存キー・既存出力・exit code は不変、追加は新キー・新セクションのみ(additive)。skill_dispatcher の独自 build_context_bundle とは無関係(PM 確認済)。

## TL impl review

tl-advisor impl review(2026-06-21, run baqprpkdy)= **approve / decision: passed**。P0/P1/P2 なし。

- **scope**: PLAN scope `context_budget_injection_profile_surface` と対象 7 ファイルが一致。新規処理は context_guard.py の定数 / `_context_budget_report()` / check_context の additive merge に閉じる。
- **契約/API**: check_context() は既存キー維持で context_budget/context_profile を追加するのみ、exit code 不変。context_bundle() は human-readable bundle(非安定 JSON API)へセクション追加で許容。D-API/D-DB/D-CONTRACT/schema/env/secret/本番影響なし。
- **doc↔code 整合**: 150000 / 50000 / 0.70 が continuous-run-context-management.md・layer-context-injection.md・コード定数で一致。profile 表の task 行も always_on/dynamic_load/exclude と矛盾なし。
- **P3 Optional(非ブロッキング・deferred)**: fresh_session_threshold_pct=0.70 では残 45000 < output_reserve_min=50000。現状は表示用 budget で enforcement でないため非ブロッキング。将来 enforce する場合は 0.66 近辺へ調整 or reserve 算出式を明文化。**0.70 はユーザー選定値のため本 Action では維持**し、enforcement 化時に再検討する(L6↔L7 G7 follow-up)。

PM 独立検証: py_compile OK / test_context_guard 16 passed(assert 修正後)/ helix context check --json で context_budget+context_profile surface / helix context bundle で budget セクション描画。
