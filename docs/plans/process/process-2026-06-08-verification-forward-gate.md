---
plan_id: process-2026-06-08-verification-forward-gate
title: "Process Plan: 検証 = Forward 内在ゲート（ロードマップ廃止後の検証機構確立）"
plan_scope: process
workflow_chain: "設計正本(automation-gate-map/verification-strategy §14/L0-L14 原則) → MVP-A(G7 subcheck + VG-overview、advisory) → MVP-B(DF-G7-MISSING 解消 → fail-close flip + push 接続) → G8/G9/G12/G14 ratchet → requirement_drift(新規 detector) → 全 pair strict + L2↔L10/FE detector"
kind: planning
layer: L7
process_layer: L7
drive: be
status: in_progress
tl_review: approve  # 設計正本=TL review changes_required(P1 MVP順序/P2 G0・VG-overview/P3)→反映 / MVP-A 実装=TL impl review changes_required(P1 doctor --json guard/P3 台帳・bats)→反映→検証 green。design+impl 両 TL approve。
created: 2026-06-08
owner: PM
forward_return: "Forward V-model L0-L14 の各 L exit を検証ゲートで通す状態に収束（ロードマップの Phase として追いかけず Forward 内在化）。pair_closure = design + test_design + test_code_anchor + test_execution_pass + trace_symmetry + semantic_gate。最終 = 各 L-pair が applicable な範囲で gate green、横断（要件ずれ/全体俯瞰）が push 前 fail-close。これは廃止した 6-phase 永続ロードマップとは別物（bounded・forward_return 明示・退化防止規律つき）。"
contains_action_plans:
  - docs/plans/add-feature/add-feature-2026-06-08-detector-failclose-ci-gate.md  # parked（registry-detector fail-close、検証ゲート閉合後に automation-gate-map gate hardening として再開）
agent_slots:
  - role: se
    slot_label: "SE — detector/gate/runner 実装（Codex、MVP-A/B・requirement_drift）"
  - role: tl-advisor
    slot_label: "TL — gate 体系設計・pair_closure 判定式・公開API/exit 契約・退化防止 の adversarial check"
generates:
  - artifact_path: cli/lib/g7_subcheck.py
    artifact_type: python_module
  - artifact_path: cli/lib/vg_overview.py
    artifact_type: python_module
  - artifact_path: docs/v2/L7-test-design/g7-test-anchor-map.yaml
    artifact_type: yaml_config
  - artifact_path: docs/v2/L7-test-design/requirement-drift-単体テスト設計.md
    artifact_type: test_design_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
---

# 検証 = Forward 内在ゲート — Process

> ユーザー方針（2026-06-08）「ロードマップは廃止。検証は Forward 内の検証サイクル＝ゲートとして機能させる」を受けた検証機構確立 Process。**廃止した [6-phase V2 ロードマップ](process-2026-06-03-v2-implementation-roadmap.md)（deprecated）とは別物**: 常時目指す目標台帳でなく、Forward V-model の各 L exit を通すゲートを bounded に実装する。

## 1. 背景 / 是正の経緯
- /goal「1と2の完遂」で Phase3 を「detector gate 機能実装」と誤フレーミング → ユーザー指摘で「Phase3=検証（L7 単体テスト実施）」「Phase2 は設計+テスト設計の凍結で検証実行は未実施」と是正 → 「ロードマップ廃止、検証=Forward ゲート」へ転換。
- verify-first 実測: L7 の「58 untraced UT」は大半 tested-but-unanchored（実テスト在り・anchor 未）。真 MISSING は 4（[[DF-G7-MISSING-001]] = UT-WSC-07/08/10/11）。

## 2. ゲート体系（設計正本へリンク、重複させない）
- 原則・L/G 対応: [HELIX-process-L0-L14 §検証ゲート](../../../HELIX-workflows/HELIX-process-L0-L14.md)
- 判定式・evidence schema: [verification-strategy §14](../../v2/L1-requirements/helix-workflows-verification-strategy.md)
- detector↔gate↔push 配線・enforcement 段階: [automation-gate-map](../../../HELIX-workflows/helix-process/automation-gate-map.md)

## 3. 進捗
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-08 | ロードマップ廃止（deprecate）+ CLAUDE.md §V2 を verification-as-gate に書換。設計正本 3 doc author。**TL design review changes_required（P1 MVP 2段順序=anchor 未閉で fail-close は CI red / P2 G0・VG-overview pair_status / P3 requirement_kind・退化防止 static check）→反映**。 | PM (Opus) + TL |
| 2026-06-08 | **MVP-A 実装（Codex se、advisory）**: G7 subcheck（UT-ID anchor + test_execution_pass、yaml SSoT）+ VG-overview aggregator + doctor 配線。**anchor 31→84/88・exec_pass 84・missing 4**（真 gap=DF-G7-MISSING-001）。PM 独立検証で regression 検出（新 .py 2本未登録→functional_registry △）→ Codex 再委譲で registry 登録→✓ 復帰。**TL impl review changes_required（P1 doctor --json guard exit2 / P3 台帳`実装済`→`未実装` / P3 subcommand bats）→反映→検証**: g7/vg --json rc=0・default rc=0・bats 8/8・pytest 2399・coverage✓・0 fail・ci/push_gate 不変。 | PM (Opus) + Codex se + TL |
| 2026-06-09 | **MVP-B missing closure 完了（advisory）**: DF-G7-MISSING-001 の真 missing 4 件（UT-WSC-07/08/10/11）を `cli/tests/test-wsc-hooks-pretooluse-agent-and-design-guards.bats` で実装し、`docs/v2/L7-test-design/g7-test-anchor-map.yaml` へ anchor 登録。`helix doctor check_vg_overview --json` で G7 summary `anchored=88` / `exec_pass=88` / `missing=0` / `unanchored_but_exists=0`、VG-overview `overall_clean=true`、`L6-L7.status=applicable` を確認。`trace_symmetry` は L1-L14 / L3-L12 / L5-L8 / L6-L7 が coverage100%・missing_pair0・orphan0。L4-L9 は 2026-06-09 Codex で semantic evidence を detector 化し、coverage100%・missing_pair0・orphan0・semantic_excluded_orphan18・balance0.67。`registry_design_coverage` は active_entries=551 / l6_required=67 / findings=0。`.helix/phase.yaml` は `plan_id=process-2026-06-08-verification-forward-gate`、`gates.G6.5/G6.7/G6.9/G7.status=passed`。 | Codex |
| 2026-06-09 | **G7 execution stability guard**。G7 full subcheck が外側 timeout で落ちると子 pytest / Bats が残る問題を確認し、`execute_test_file()` に per-file timeout と process group stop を追加。`HELIX_G7_TEST_TIMEOUT_SECONDS`（既定 120 秒）で制御し、timeout 時は `returncode=124` / `timed_out=true` を `test_results` に記録する。検証: `python3 -m pytest cli/lib/tests/test_g7_subcheck.py -q` 4 passed、`python3 -m py_compile cli/lib/g7_subcheck.py` pass、`python3 -m cli.lib.g7_subcheck --json --no-exec` は `anchored=88` / `exec_pass=88` / `missing=0`、`HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --json` は `overall_clean=true`。 | Codex |
| 2026-06-09 | **MVP-B fail-close + push 接続**。`helix doctor --gate` に VG-overview pre-push fail-close 評価を追加し、`helix push --gate` に `G-vg-overview` を接続。push 側は既存の full pytest/Bats 実行後に structural VG-overview を確認し、G7 anchor / registry / trace applicable pair が clean でなければ push を block する。 | Codex |
| 2026-06-09 | **L0-L6 focus audit + L2 waiver 証跡化**。ユーザー確認により L6 までを focus として再整理。`docs/v2/audit/2026-06-09-l0-l6-focus-audit.md` を追加し、L0/L1/L3/L4/L5/L6 の実体と L2 `ui_absent` waiver を明示。`VG-overview` は `docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md` を読んで `L2-L10.status=not_applicable` を返すように変更。 | Codex |
| 2026-06-09 | **requirement_drift MVP 実装 + fail-close 接続 + L6 closure**。`docs/v2/L6-functional-design/requirement-drift-機能設計.md` と `docs/v2/L7-test-design/requirement-drift-単体テスト設計.md` を追加し、`cli/lib/requirement_drift.py` を L6 detector として `cli/config/functional-registry.yaml` に登録。Python API / CLI JSON / `helix doctor check_requirement_drift --json` を実装し、RD-UT-01〜17 相当の pytest + Bats surface を追加。既定は `focus=L6` で、L7 code/test は `--focus L7` 明示時だけ見る。L1 数字式 FR → L3 名前ベース FR の parent-child mapping と placeholder FR 除外、総称 downstream label 除外、mtime stale の `--check-stale` opt-in を実装し、`VG-overview.required_clean.requirement_drift` 経由で `G-vg-overview` に接続。実リポジトリ evidence は `requirements=31` / `design_links=31` / `blocking_findings=0` / `advisory_findings=0`、VG-overview `overall_clean=true`。`RD-UT-*` は requirement_drift 専用 ID として維持し、G7 inventory の `UT-*` には混入させない。 | Codex |
| 2026-06-09 | **L6 phase display alignment**。G6/G7 gate evidence に対して `.helix/phase.yaml` が `current_mode=scrum` / `current_phase=L4` のまま残り、`doctor --gate` に phase/mode warning が出ていたため、active phase display を `current_mode=forward` / `current_phase=L6` に更新。検証: `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json` は `pass=33` / `fail=0` / `warn=103` で phase/mode warning 0、`python3 -m pytest cli/lib/tests/test_helix_doctor_phase_mode.py -q` は 9 passed。handover の `phase=L4` は引継ぎタスク metadata として残る。 | Codex |
| 2026-06-09 | **strict full-flow execution visibility**。L6 focus の `overall_clean=true` と L0-L14 完全対応の未完を混同しないため、`VG-overview.full_flow_execution` と `--strict-full-flow` を追加。通常 `helix doctor check_vg_overview --json` は L6 focus / applicable pair clean を維持し、`--strict-full-flow` 指定時は `approved_deferred` execution gate が残る限り `overall_clean=false`。実リポジトリ evidence は `full_flow_execution.deferred_count=4`（L5-L8→G8、L4-L9→G9、L3-L12→G12、L1-L14→G14）で、各 item は `gate_id` / `target` / `next_action` / `reference` を持つ。L2-L10 は `not_applicable_count=1` として `ui_absent` waiver object（path / owner / process_layer / pairs_with / unskip_required_when）を返す。検証: `python3 -m pytest cli/lib/tests/test_vg_overview.py cli/lib/tests/test_push_gate.py -q` 26 passed、`bats cli/tests/helix-doctor-json.bats` 12 passed。 | Codex |
| 2026-06-09 | **strict full-flow feedback-loop 接続**。`helix harness feedback-loop` が `VG-overview` を `strict_full_flow=True` / `execute_g7_tests=False` で読み、snapshot の `vg_overview`、learning candidate の `full_flow_deferred_execution_gate` / `not_applicable_pair_waiver`、metrics の `harness.feedback_loop.full_flow_deferred_gates` / `harness.feedback_loop.not_applicable_pairs` として出力するように接続。L6 focus の clean と L8/L9/L12/L14 実行ゲート残を DB feedback-loop で同時に追跡可能にした。検証: `python3 -m py_compile cli/lib/harness_monitor.py cli/lib/vg_overview.py`、`python3 -m pytest cli/lib/tests/test_harness_monitor_unit.py::TestFeedbackLoopSnapshot cli/lib/tests/test_vg_overview.py -q`、`bats cli/tests/test-helix-harness-feedback-loop.bats`。 | Codex |

## 4. 残（後続）
- **MVP-B 残**: DF-G7-MISSING-001 の真 missing UT 4、G7 timeout guard、VG-overview fail-close、push 接続は解消済み。残りは CI 接続。
- G8/G9/G12/G14 ratchet（右腕 execution gate）/ 全 pair strict（G9 ST 実行 gate、L5-L8 deferred 等の右腕実行 gap 解消後）/ L2↔L10 FE detector 本実装。右腕 execution gate の deferred は `helix doctor check_vg_overview --strict-full-flow --json` の `full_flow_execution.deferred_pairs[]`、L2-L10 waiver は `not_applicable_pairs[]` で machine-visible。
- 退化防止 static check 実装（deprecated Process を新 Action parent にしない 等）。

## 5. forward_return
frontmatter `forward_return` の通り、Forward V-model 各 L exit の検証ゲート内在化へ収束。本 Process は bounded（MVP-A/B + 段階拡大で完了）であり、永続ロードマップ化させない（automation-gate-map §8 退化防止）。
