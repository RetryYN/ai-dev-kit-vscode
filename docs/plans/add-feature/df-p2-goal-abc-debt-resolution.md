---
plan_id: df-p2-goal-abc-debt-resolution
title: "Action(debt-resolution): goal A/B/C — DF-P2-PLANDEP / DF-DATEROT-BASENOW / DF-P2-EXISTING-CYCLES の deferred-debt 解消 + B-3 compat import surface 修正"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: refactor
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: plan_dependency_gate / import_cycle(dependency_cycle) の L6 設計。本 Action は両 detector の既存債(plan_dependency baseline / import cycle 5件)を root-cause 解消し baseline を 0 へ、harness_monitor の date-rot test を BASE_NOW 基準へ統一する behavior-preserving な debt 解消。registry schema 不変。
forward_return: "DF-P2-PLANDEP: plan_validator.locate_plan_file の path 形式参照 false-positive を root-cause 修正 + reciprocal/malformed 参照を cleanup -> plan-dependency-baseline を 0 へ。DF-DATEROT-BASENOW: harness_monitor 単体テストの時刻基準を BASE_NOW へ統一 + date-rot invariance test 追加。DF-P2-EXISTING-CYCLES: http_api を compat.py / team_definition.py へ抽出して 5 import cycle を一方向化 + import-cycle-baseline を 0 へ -> server.py の未使用 compat import(_CompatClient 等)を除去して Flask installed 環境の ImportError を解消(behavior-preserving)。-> L6↔L7 G7 pending gate evidence に帰属。"
drive: be
status: completed
status_note: "2026-06-21 完遂。goal A/B/C の Phase A(境界/handover retarget)+ Phase B(deferred-debt 解消)。① DF-P2-PLANDEP(feda90b): plan_validator.locate_plan_file が path 形式 blocks 参照を実在でも missing 誤報告する false-positive を _resolve_plan_pointer 経由解決で root-cause 修正 + reciprocal/malformed cleanup + plan-dependency-baseline を 0 へ。② DF-DATEROT-BASENOW(c8c8815): harness_monitor 単体テストの時刻基準を BASE_NOW(固定 datetime)へ統一し date-rot invariance test 追加。③ DF-P2-EXISTING-CYCLES(235865f): http_api を compat.py / team_definition.py へ抽出し 5 import cycle を一方向化 + import-cycle-baseline 5→0(behavior-preserving)。④ B-3 fix(a4c9451): ③で server.py が compat.py の no-Flask fallback path でしか定義されない _CompatClient 等を無条件 import していた問題(Flask installed 環境で http_api.server import が ImportError)を、未使用 dead import 除去で解消。検証: plan_dependency_gate / import_cycle ともに clean(finding 0)、http_api 90 tests pass、fake-Flask installed path で full import + create_app() OK、contract standalone 88 passed。"
current_task_scope: goal_abc_phase_b_debt_resolution
approval_required_before_l7_work: false  # ユーザー /goal「完遂して」+ 本 PLAN 起票(option A)を明示承認(2026-06-21)
tl_review: approve  # tl-advisor impl review(2026-06-21)=changes_required(P0 なし / P1: DF-P2-EXISTING-CYCLES の server.py が Flask installed 環境で _CompatClient ImportError = behavior-preserving 違反)→ a4c9451 で未使用 compat import を除去して P1 解消 → PM 独立検証(TL の fake-Flask 再現シナリオで full import + create_app() OK + http_api 90 tests pass + py_compile OK)。P2/P3 なし(baseline→0 は live check finding 0 で隠蔽でなく実解消)。残 P1 ゼロにつき approve。
ticket_is_completion_evidence: false
created: 2026-06-21
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): plan_dependency_gate の既存債を root-cause 解消し baseline を 0 へ"
  - "L6↔L7 (単体): import_cycle(dependency_cycle) の 5 循環を一方向化し baseline を 0 へ"
  - "L6↔L7 (単体): harness_monitor date-rot test を BASE_NOW 基準へ統一(date-rot invariance)"
design_change_class: pure_impl  # 全 commit が behavior-preserving(import-topology refactor / test 時刻基準統一 / detector false-positive 修正 / 未使用 import 除去)。外部 CLI 出力・exit code・公開 API・registry schema いずれも不変。再凍結 scope: L6-L7 の対 design は不変。
agent_slots:
  - role: se
    slot_label: "SE — DF-P2-PLANDEP / DATEROT / EXISTING-CYCLES 実装(Codex、commit feda90b/c8c8815/235865f)"
  - role: tl-advisor
    slot_label: "TL — 4 commit impl review(behavior-preserving 検証 / baseline→0 の正当性)。P1=B-3 ImportError 検出 → a4c9451 で解消"
---

# goal A/B/C — Phase B deferred-debt 解消 (debt-resolution Action)

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md)。本 Action は goal A/B/C の Phase A(境界/handover を DF-P2-PLANDEP scope へ retarget)+ Phase B(deferred-debt 3 件の解消)を記録する。Phase C(右腕 G9/G12/G14 execution-gate full-close)は別 scope（同 goal で承認済・別途 unlock）。

## 対象 commit (origin/dogfood..HEAD)

| commit | 内容 | debt |
|---|---|---|
| f027b56 | Phase A: handover を landed G14 から DF-P2-PLANDEP scope へ retarget + boundary current_allowed_work を goal-stable 化 | — |
| feda90b | plan_validator.locate_plan_file の path 形式参照 false-positive を root-cause 修正 + reciprocal/malformed cleanup + baseline→0 | DF-P2-PLANDEP |
| c8c8815 | harness_monitor 単体テストの時刻基準を BASE_NOW へ統一 + date-rot invariance test | DF-DATEROT-BASENOW |
| 235865f | http_api を compat.py / team_definition.py へ抽出し 5 import cycle を一方向化 + baseline 5→0 | DF-P2-EXISTING-CYCLES |
| a4c9451 | server.py の未使用 compat import(_CompatClient 等)を除去し Flask installed 環境の ImportError を解消(TL P1) | DF-P2-EXISTING-CYCLES fix |

## 受入条件 / 検証

- plan_dependency_gate clean(finding 0) / import_cycle clean(finding 0)。
- http_api 90 tests pass。fake-Flask installed path で full import + create_app() OK(TL P1 解消の証跡)。
- contract standalone 88 passed(flaky だった失敗を再確認、deterministic green)。
- behavior-preserving: 外部 CLI 出力 / exit code / 公開 API / registry schema 不変。

## TL impl review

tl-advisor impl review(2026-06-21)= changes_required。P0 なし。P1 = DF-P2-EXISTING-CYCLES(235865f)の server.py が `from .compat import ... _CompatClient ...` を無条件 import するが、`_CompatClient` は compat.py の no-Flask fallback path でしか定義されず、Flask installed 環境で `http_api.server` の import が ImportError になり behavior-preserving 条件を満たさない(fake-Flask で再現済み)。→ a4c9451 で server.py の未使用 compat import(server 本体は Flask / request のみ使用、他モジュールもこれら symbol を server から import していない dead import)を除去して解消。PM 独立検証で TL の再現シナリオが通り、http_api 90 tests pass。残 P1 ゼロにつき approve。
