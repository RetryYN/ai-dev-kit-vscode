---
plan_id: add-feature-2026-06-21-context-budget-threshold-derive
title: "Action(add-feature): context budget の fresh_session_threshold_pct を reserve 算出式化 (magic 0.70 -> 1 - output_reserve_min/max_total_tokens = 0.6666) + 全契約サイト SSoT 統一 + drift test"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: HELIX-workflows/helix-process/layer-context-injection.md  # 注入プロファイルと予算(budget)の設計正本。本 Action は budget の fresh_session_threshold_pct を magic number から reserve 算出値へ是正し、context_guard を SSoT 化する additive hardening。
forward_return: "layer-context-injection の budget 制約に『fresh_session_threshold_pct = 1 - output_reserve_min/max_total_tokens (reserve 厳守の上限率)』を明文化 -> L7 context_guard.py を SSoT 化(CONTEXT_BUDGET の fresh_session_threshold_pct を max_total_tokens/output_reserve_min から導出)-> handover_auto_dump.py / helix-stop-hook は context_guard から導出(literal 二重定義を撤去)-> context-budget drift test(全契約サイト一致 + 算出式整合)-> L6↔L7 G7 pending gate evidence に帰属。"
drive: be
status: completed
tl_review: approve  # tl-advisor 再 review (foundation reject→修正後、rollout 06:06:51) = approve。残存0.70 を全契約サイト(context_guard/handover_auto_dump/stop-hook/harness/continuous-run doc/layer-context-injection doc)で SSoT 統一、denylist drift test で fail-close。floor 採用理由(round=0.6667 は reserve 割れ)明記。PM 独立検証: targeted 136 passed / full 2723 passed / bats 57/57 / threshold=0.6666 remaining 50010>=50000。
status_note: "2026-06-21 起票。前 Action add-feature-2026-06-21-context-budget-injection-profile の P3 Optional(非ブロッキング deferred = fresh_session_threshold_pct=0.70 は残 45000 < output_reserve_min=50000 で reserve を下回る)を解消する。ユーザー裁定(2026-06-21)= 『算出式へ修正』(0.70 維持でなく derive 化)。TL 助言(tl-advisor, run bgdjt2cmh)= 固定値でなく算出式 `1 - output_reserve_min/max_total_tokens` 推奨 + context_guard.py 単独変更は契約 drift(同値が handover_auto_dump.py / helix-stop-hook にもある)ため全契約サイト + test を同一 PLAN scope に含めること。"
current_task_scope: context_budget_threshold_derive
approval_required_before_l7_work: false  # ユーザー AskUserQuestion(2026-06-21)= B『算出式へ修正』を明示選択
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L4/L5↔L7: context-injection 設計(layer-context-injection の budget 制約)↔ context_guard.py の fresh_session_threshold_pct 導出 + 契約サイト SSoT 統一"
design_change_class: contract_extension  # surfaced budget 値の算出根拠を明文化 + SSoT 統一 + drift test 追加。max_total_tokens/output_reserve_min(既存値)は不変、threshold はそこから導出に変更(0.70->0.6666)。公開 API キー名・exit code 不変。
agent_slots:
  - role: se
    slot_label: "SE — context_guard.py を threshold SSoT 化(導出) + handover_auto_dump.py / helix-stop-hook を context_guard 由来へ + test_context_guard.py の 0.70 assert を算出式整合 assert へ + drift test 追加 + layer-context-injection.md に式明文化(Codex)"
  - role: tl-advisor
    slot_label: "TL — 算出式の正当性(reserve 厳守) / 全契約サイト一致(no drift) / import cycle 非発生(context_guard <- handover_auto_dump) / advisory 専用で enforcement 副作用なし / 既存キー・exit code 不変 の adversarial check"
generates:
  - artifact_path: cli/lib/context_guard.py
    artifact_type: python_module
  - artifact_path: cli/lib/handover_auto_dump.py
    artifact_type: python_module
  - artifact_path: cli/helix-stop-hook
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_context_guard.py
    artifact_type: test
  - artifact_path: HELIX-workflows/helix-process/layer-context-injection.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires:
    - docs/plans/add-feature/add-feature-2026-06-21-context-budget-injection-profile.md
  blocks: []
---

# context budget threshold を reserve 算出式化 (add-feature Action)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。前 Action [context budget / injection profile surface](add-feature-2026-06-21-context-budget-injection-profile.md) の P3 Optional deferred を解消する後続 Action。

## 1. 背景 / 解く問題

前 Action で `context_guard.py` に `CONTEXT_BUDGET = {max_total_tokens: 150000, output_reserve_min: 50000, fresh_session_threshold_pct: 0.70, ...}` を landing した。TL review(run baqprpkdy)は P3 Optional(非ブロッキング)を残した:

> `fresh_session_threshold_pct=0.70` は `max_total_tokens=150000` に対し残 `45000 < output_reserve_min=50000` で厳密には reserve を下回る。現状は表示用 budget で enforcement でないため非ブロッキング。将来 enforce 時は 0.66 近辺 or reserve 算出式の明文化を検討。

ユーザー裁定(2026-06-21 AskUserQuestion B)= **算出式へ修正**(0.70 維持でなく derive 化)。

加えて同値の `0.70` が **3 契約サイトに重複** している(grep 実測):
- `cli/lib/context_guard.py:40` — `fresh_session_threshold_pct: 0.70`
- `cli/lib/handover_auto_dump.py:21` — `DEFAULT_THRESHOLD = 0.70`
- `cli/helix-stop-hook:8` — `threshold="${HELIX_CONTEXT_COMPACT_THRESHOLD:-0.70}"`(+ :28 python fallback `"0.70"` / `"70%"`)

固定値を一箇所だけ変えると **context budget 契約 drift**(TL P1 指摘)。本 Action は算出式化 + SSoT 統一 + drift test で一括是正する。

## 2. スコープ

### In
- **context_guard.py を SSoT 化**: `CONTEXT_BUDGET["fresh_session_threshold_pct"]` を `max_total_tokens` / `output_reserve_min` から導出する(`math.floor((1 - output_reserve_min / max_total_tokens) * 10**4) / 10**4` = `0.6666`(round だと 0.6667 で remaining=49995 < reserve 50000 を割るため floor 採用))。dict literal の magic `0.70` を撤去し、dict 構築後に導出代入 or 導出 helper で定義。`max_total_tokens` / `output_reserve_min` の既存値は不変。
- **handover_auto_dump.py**: `DEFAULT_THRESHOLD = 0.70` を `from cli.lib.context_guard import CONTEXT_BUDGET; DEFAULT_THRESHOLD = CONTEXT_BUDGET["fresh_session_threshold_pct"]` へ(literal 撤去)。import cycle 非発生を確認(context_guard は handover_auto_dump を import しない)。
- **helix-stop-hook**: bash default(:8)と python fallback(:28)を context_guard 由来へ。bash は `threshold="${HELIX_CONTEXT_COMPACT_THRESHOLD:-$(python3 -c '...print(CONTEXT_BUDGET["fresh_session_threshold_pct"])' 2>/dev/null || echo 0.6666)}"` のように導出(失敗時 fallback literal は算出値と一致)。python fallback の `"0.70"` / `"70%"` も `0.6666` / `66%` 系に揃える。
- **test_context_guard.py**: `assert payload["context_budget"]["fresh_session_threshold_pct"] == 0.7`(:259)を **算出式整合 assert** へ(`== math.floor((1 - 50000/150000)*10**4)/10**4` かつ remaining `>= output_reserve_min`(reserve floor 厳守))。
- **drift test 追加**: 全契約サイトの threshold が一致することを機械検証(context_guard 導出値 == handover_auto_dump.DEFAULT_THRESHOLD、helix-stop-hook の fallback literal も算出値と一致)。`cli/lib/tests/test_core_manifest_drift.py` 同様の drift-guard pattern。
- **layer-context-injection.md**: budget 制約に算出式 `fresh_session_threshold_pct = floor((1 - output_reserve_min/max_total_tokens)×10^4)/10^4 (reserve 厳守の上限率)` を明文化。

### Out(forbidden_now / 別 Action)
- threshold の **enforcement 化**(現状 advisory 表示専用を維持。判定ロジック新設は別 scope)。
- `max_total_tokens` / `output_reserve_min` / 他 budget 値の変更。
- injection profile(CONTEXT_PROFILE)の変更。

## 3. 受入条件
1. `context_guard.CONTEXT_BUDGET["fresh_session_threshold_pct"]` が `math.floor((1 - 50000/150000)*10**4)/10**4 = 0.6666` を返す(round=0.6667 は reserve 割れのため floor)(magic literal 0.70 撤去)。
2. `handover_auto_dump.DEFAULT_THRESHOLD` が context_guard 由来で同値(literal 二重定義なし)。import cycle 非発生(py_compile + import 実行 OK)。
3. helix-stop-hook の threshold default / fallback が算出値と一致(`bash -n` + 実走 smoke で `66%` 系表示)。
4. drift test: 全契約サイト一致 + 算出式整合を assert(意図的に 1 サイトを書き換えると test が fail することで非 gameable 性を実証)。
5. advisory 専用のまま(enforcement 副作用ゼロ、exit code 不変、既存キー名不変)。
6. 全 pytest(cli/lib/tests)+ 全 bats green。

## 4. forward_return
L6↔L7 G7 pending gate evidence へ帰属。layer-context-injection の budget 制約に算出式を明文化(設計↔code 値整合の再凍結証跡)。前 Action の P3 deferred を本 Action で close。

## 5. 検証コマンド
- `python3 -m py_compile cli/lib/context_guard.py cli/lib/handover_auto_dump.py`
- `bash -n cli/helix-stop-hook`
- `python3 -m pytest cli/lib/tests/test_context_guard.py -q`
- `python3 -c "from cli.lib.handover_auto_dump import DEFAULT_THRESHOLD; from cli.lib.context_guard import CONTEXT_BUDGET; assert DEFAULT_THRESHOLD == CONTEXT_BUDGET['fresh_session_threshold_pct']; print('drift OK', DEFAULT_THRESHOLD)"`
- `helix context check --json | python3 -c "import sys,json; print(json.load(sys.stdin)['context_budget']['fresh_session_threshold_pct'])"`
