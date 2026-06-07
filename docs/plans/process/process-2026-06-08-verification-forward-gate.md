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

## 4. 残（後続）
- **MVP-B**: DF-G7-MISSING-001（真 missing UT 4）解消 → anchored 88/88 → G7 + VG-overview-pre-push を fail-close flip + push 接続（今 advisory）。
- G8/G9/G12/G14 ratchet（右腕 execution gate）/ requirement_drift 新規 detector（要件ずれ縦 trace）/ 全 pair strict（L4-L9 orphan18 等 gap 解消後）/ L2↔L10 + FE detector（waiver schema）。
- 退化防止 static check 実装（deprecated Process を新 Action parent にしない 等）。

## 5. forward_return
frontmatter `forward_return` の通り、Forward V-model 各 L exit の検証ゲート内在化へ収束。本 Process は bounded（MVP-A/B + 段階拡大で完了）であり、永続ロードマップ化させない（automation-gate-map §8 退化防止）。
