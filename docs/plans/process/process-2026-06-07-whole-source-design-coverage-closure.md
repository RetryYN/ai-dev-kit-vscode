---
plan_id: process-2026-06-07-whole-source-design-coverage-closure
title: "Process Plan: Whole-source ⊆ Design Coverage Closure — 既存ソース全体を設計層へ明示分類し抜け漏れゼロにする (zero-omission)"
plan_scope: process
workflow_chain: "Action1(Recovery: defer継続不可の認識訂正 + zero-omission=B' 定義凍結) → Action2(Reverse: L3 registry closure — 未登録8件登録 + invalid trace44件解消 + 母数SSoT是正 → check_functional_registry clean baseline) → Action3(Reverse: coverage_layer schema L3追補 + 全active entry分類 unknown=0 + registry_design_coverage detector 新設warn-only) → Action4(Reverse/forward_refreeze: L6_required を FN/UT 1:1 拡張 + L5/L4_required を既存pairへ接続 + required_refreeze_pairs 再凍結)"
kind: planning
layer: L3
drive: reverse
status: draft
tl_review: pending  # 戦略諮問は完了(TL: B'採用/Process分解/detector受領)。PLAN doc 自体の review は起票後に取得
created: 2026-06-07
owner: PM
contains_action_plans:
  - docs/plans/recovery/recovery-2026-06-07-design-coverage-recognition.md
  - docs/plans/reverse/reverse-2026-06-07-l3-registry-closure.md
  - docs/plans/reverse/reverse-2026-06-07-coverage-classification.md
  - docs/plans/reverse/reverse-2026-06-07-layer-refreeze.md
forward_return: "L3（registry/coverage classification の SSoT 凍結）+ 各 Action が触れる設計層 L4/L5/L6 とその対 pair（L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7）。Process 完了 = 全 active registry entry が coverage_layer 明示分類を持ち（unknown=0）、source⊆registry⊆要件 trace が閉じ、L6_required の FN↔UT が 1:1 凍結され、detector_clean AND semantic_gate_pass が成立した状態。V2 roadmap Phase2(設計密度)/Phase3(detector fail-close+CI連動) に内包。required_refreeze_pairs は Action3 分類後に実測確定。"
agent_slots:
  - role: tl-advisor
    slot_label: "TL — B' coverage_layer 判定基準 / Process分解 / detector契約 / 再凍結pair の adversarial check（戦略諮問 2026-06-07 完了=条件付き推奨 B'）"
  - role: se
    slot_label: "SE — registry_design_coverage detector + schema validation + doctor 接続の実装（Codex、TDD）"
  - role: pmo-sonnet
    slot_label: "PMO — 540 active entry の coverage_layer 分類の read-heavy 補助（判定根拠抽出）"
generates:
  - artifact_path: docs/plans/process/process-2026-06-07-whole-source-design-coverage-closure.md
    artifact_type: markdown_doc
  - artifact_path: docs/v2/audit/2026-06-07-whole-source-design-coverage-audit.md
    artifact_type: markdown_doc
dependencies:
  parent: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  requires: []
  blocks: []
related_docs:
  - docs/v2/audit/2026-06-07-whole-source-design-coverage-audit.md
  - docs/v2/L3-requirements/helix-workflows-functional-registry.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - docs/v2/L6-functional-design/helix-workflows-function-design.md
  - cli/config/functional-registry.yaml
  - cli/lib/functional_registry_checks.py
  - cli/lib/trace_symmetry.py
  - HELIX-workflows/helix-process/plan-model.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
  - HELIX-workflows/helix-process/reverse-workflow.md
---

# Whole-source ⊆ Design Coverage Closure — Process（親）

> 駆動 Process（親=行程）。`workflow_chain` の連鎖を `forward_return` で Forward V モデルへ戻す。
> 検証 evidence = [AUDIT-WSDC-001](../../v2/audit/2026-06-07-whole-source-design-coverage-audit.md)。戦略正本 = TL 諮問 2026-06-07（B' 採用）。

## 1. 目的

ユーザー goal「設計に既存ソースのすべてが含まれているか徹底検証し、なければ追加設計をする Recovery を回す。**抜け漏れの一切の禁止**」を満たす。
徹底検証（AUDIT-WSDC-001）で **3 segment の抜け漏れ**を確定済み（seg1 未登録8 / seg2 trace未接続44 / seg3 設計未定義 約524）。本 Process はこれを zero-omission（B' 定義）まで閉じる。

## 2. zero-omission の定義（B'、TL 採用）

```
zero_omission = source ⊆ registry
            AND registry → L1/L3 trace complete
            AND 全 active registry entry が明示的 coverage_layer 分類を持つ（unknown=0）
```

| coverage_layer | 対象 | 設計反映 |
|---|---|---|
| `L6_required` | public callable / 独立した振る舞い契約 / DbC 必要 | FN-* + UT-* 1:1 必須 |
| `L5_required` | module 境界 / 結合 / data flow / 内部 process | MOD-* / IT-* で被覆 |
| `L4_required` | workflow / architecture / NFR / command family / system interaction | NFR-* / IF-* / ST-* で被覆 |
| `excluded_with_reason` | private glue / 生成物 / static template | 上位設計 ID + 除外理由 必須（orphan 禁止） |

**却下**: A（全 557 を FN/UT 化 = 粒度爆発・V-model 粒度誤り）/ C（registry+要件のみ = 設計未反映を温存し goal 未達）。

## 3. Action 連鎖（workflow_chain）

| # | Action | kind | 主作業 | forward_return |
|---|---|---|---|---|
| 1 | [design-coverage-recognition](../recovery/recovery-2026-06-07-design-coverage-recognition.md) | recovery | defer 継続不可の認識訂正、B' を verification-strategy/L3 に凍結 | L3 policy / verification-strategy evidence |
| 2 | [l3-registry-closure](../reverse/reverse-2026-06-07-l3-registry-closure.md) | reverse | 未登録8件登録 + invalid trace44件解消 + 母数 SSoT(557) 是正 | L3（+ 必要なら L3↔L12 semantic re-freeze） |
| 3 | [coverage-classification](../reverse/reverse-2026-06-07-coverage-classification.md) | reverse | coverage_layer/design_ids/excluded_reason schema 追補 + 全 active entry 分類 + registry_design_coverage detector 新設 | L3 schema + 参照設計層 L4/L5/L6 |
| 4 | [layer-refreeze](../reverse/reverse-2026-06-07-layer-refreeze.md) | reverse | L6_required を FN/UT 1:1 拡張、L5/L4_required を既存 pair 接続、required_refreeze_pairs 再凍結 | required_refreeze_pairs（Action3 実測後確定） |

> 段階導入: zero-omission を宣言できるのは **Action3 の unknown=0** と **Action4 の required pair green** 後（TL Q3）。

## 4. 完了判定（exit gate）

| detector | 合格条件 |
|---|---|
| source_scan_vs_registry | unregistered=0 |
| registry_trace_complete | invalid=0、ID 実在 |
| registry_design_coverage（新設） | unknown=0 / design_id missing=0 / wrong_layer=0 |
| trace_symmetry | L6_required は FN↔UT 1:1（balance_ratio≥1.0） |
| semantic_gate | excluded/層割当の妥当性を TL/PM 判定（機械化しない） |

`audit_verdict = detector_clean AND semantic_gate_pass`。`check_functional_registry` は clean baseline 後 ratchet→fail-close 昇格（完了 gate で fail-close 必須）。

## 5. リスク（TL 指摘）

- P1: coverage_layer 分類は初回 human 判断が多く semantic gate 品質に依存（→ pmo-sonnet 補助 + TL/PM 二重判定）。
- P2: registry 件数 drift 548/557 → Action2 冒頭で母数 SSoT を 557 に固定。
- P2: L4/L5 被覆許容が「L6 逃げ」に見えうる → `L6_required` 判定基準を Action1 で明文化。
- P3: `helix code find` が DB open error（read-only 環境）→ rg + 正本精読で代替。

## 6. 進捗

- [x] 徹底検証（AUDIT-WSDC-001、3 segment gap 定量化）
- [x] TL 戦略諮問（B' 採用、Process 分解、detector 受領）
- [x] Action1 recognition（verification-strategy §11.7 + L3 §1.6、commit 8fb53f5）
- [x] Action2 L3 registry closure（未登録8 + invalid trace44 + 母数565、commit d615aba）
- [x] Action3 coverage classification（unknown=0、290/105/65/89）+ registry_design_coverage detector（commit d5067e7）
- [x] Action4a 既存FN接続11 + FN-RDC-01（commit b107bf8）
- [x] Action4b 新規 FN-WSC 54 + UT-WSC 54、design_ids 全接続（l6_design_pending=0）+ L6↔L7 再凍結（refreeze_decision §13）
- [~] Process 収束（detector_clean **成立** / semantic_gate = TL impl review **待ち**）

## 7. 収束状態（2026-06-07）

**zero-omission machine 証明 成立**:
- source ⊆ registry: `check_functional_registry` unregistered=0
- registry ⊆ 要件: invalid_fr_trace=0
- registry ⊆ 設計層: `registry_design_coverage` unknown=0 / design_id_missing=0 / wrong_layer=0 / **l6_design_pending=0**
- L6↔L7: `trace_symmetry` balance1.0 / coverage100% / missing0 / dup0 / orphan0
- doctor: 30 pass / 0 fail / 107 warn（check_registry_design_coverage ✓ 昇格）

**残 carry**（設計 freeze と分離）: `WSC-TEST-IMPL` = 設計済 FN/UT 54 のうち **12 件**のテスト実装 weak（①専用テスト無し 8: hook FN-WSC-03/05/06/10/13/17 + lib FN-WSC-213/218、②Python pytest 済/hook E2E 未 4: FN-WSC-02/04/12/15）。設計の抜け漏れではない（machine-clean な design freeze 成立、test 実装は L7 sprint。L7 doc + verification-strategy §13 台帳と件数一致）。
**最終確定**: TL impl review（2026-06-07 changes_required: P1 carry件数 / P2 L7セル / P2 detector文言 → 反映済）→ approve → status=completed + gate-driven push。`registry_design_coverage` は必要条件 detector（design_id は anchor/prefix 解決、実在は trace_symmetry 担保）。
