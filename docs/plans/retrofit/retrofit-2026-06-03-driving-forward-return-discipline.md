---
plan_id: retrofit-2026-06-03-driving-forward-return-discipline
title: "Action: 全駆動 workflow の Forward 引き戻しを V-model 定義へ適合 (共通 forward-return-discipline 新設 + 9 workflow 参照化)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
workflow: retrofit
kind: retrofit
layer: cross
drive: be
status: completed
created: 2026-06-03
owner: PM
tl_review: approve
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 共通規律構造 / 判定基準 / 機械強制段階 / Refactor免除 / 遡及 adversarial check（完了 2026-06-03、changes_required→推奨設計反映）"
generates:
  - artifact_path: HELIX-workflows/helix-process/forward-return-discipline.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/plan-model.md
    artifact_type: doc_update
  - artifact_path: HELIX-workflows/HELIX-process-L0-L14.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - HELIX-workflows/helix-process/forward-return-discipline.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - HELIX-workflows/helix-process/plan-model.md
  - skills/workflow/doc-system-architect/references/design-coverage-baseline.md
---

# Action: 全駆動 workflow の Forward 引き戻しを V-model 定義へ適合

V2 実装計画 Process（親）の貫通要件「Forward + 駆動モデルが全 Phase をフル run しても耐える設計」に属する子 Action。ユーザー goal「全駆動モデルが現在の V-model の定義に準拠しているか見直しを実施して改善をする」を達成する。tl-advisor 2026-06-03 判定（changes_required → 推奨設計反映）に基づく。

## 1. 監査 baseline（pmo-project-explorer ×4、file:line 証跡）

全 9 駆動 workflow（Reverse/Recovery/Incident/Retrofit/Add-feature/Refactor/Research/Discovery/Scrum）の「Forward 接続」section が V-model 絶対原則（R1-R5）を operationalize していない＝**片肺を V-model に持ち込む sanctioned な抜け穴**。

| 駆動 | 判定 | 特記（証跡は監査レポート） |
|---|---|---|
| Reverse | 非適合 | 「実装だけで閉じる→L7」が対 L6 再凍結なし |
| Recovery | 未規定 | 再開点が実装層 → design 整合 unchecked |
| Incident | 最弱 | hotfix 速度優先で片肺リスク最大 |
| Retrofit | 未規定 | 「要件維持=設計不変」の誤解誘発 |
| Add-feature | 非対称 | registry は fail-close exit だが design pair freeze は任意 |
| Refactor | **非適合（明示）** | 「設計 PLAN 起票せず」で design 更新を意図的に禁止 → L5/L6 drift |
| Research | 宙吊り | ADR→L4→L9 pair 再凍結の責任未定義 |
| Discovery | 比較的良 | 設計層昇格は宣言、対の検証層 同時凍結なし |
| Scrum | **構造欠陥** | 昇華先表に L7 単体テスト欠落（L6↔L7 底抜け）+ fullback で Reverse の穴継承 |

**根本原因**: 駆動 workflow doc の「Forward 接続」テンプレート自体が R1-R5 を内包しない（特定 workflow 固有でない）。

## 2. R1-R5 適合 rubric（正本: HELIX-process-L0-L14 / design-coverage-baseline / verification-strategy）
- R1 設計⇔検証の対を同時凍結・片肺禁止
- R2 粒度ペアリング（L4↔L9 system / L5↔L8 module / L6↔L7 関数+DbC）
- R3 design 層成果物の物理存在を G6 等で fail-close
- R4 trace 双方向宣言（推論禁止）
- R5 machine-clean(cov100/uncovered0/orphan0)+semantic-pass

## 3. 改善設計（TL 推奨反映）

**単一 cross-cutting 規律を新設、9 workflow は参照 + 固有差分のみ**（drift 防止 / SSoT、repo の「G 正本一本化・副本は参照」原則）。

- **新設 `forward-return-discipline.md`**（正本本体）: R1-R5 を operationalize + forward_return contract + design_change_class 判定 + 再凍結 pair map + exit 条件 + waiver + 段階導入。
- **`plan-model.md`**: forward_return contract に `touched_layers` / `design_change_class` / `required_refreeze_pairs` / `refreeze_evidence` / `waiver` を追記。
- **`HELIX-process-L0-L14.md`**: Workflow 入口表近傍に「全 workflow は forward-return-discipline を通す」短参照。
- **9 workflow doc**: Forward 接続 section を本規律参照へ寄せる + 固有 fix（Refactor=「設計 PLAN 起票せず」撤回 + pure/structural/contract routing、Scrum=昇華先表に L6↔L7 追加 + fullback 後に共通規律必須）。

**design_change_class 判定（fail-close の核）**: `pure_impl`（L7 で閉じ可）= 公開挙動/IO/API・DB・契約/関数責務/モジュール境界/テスト期待値/trace ID universe が全て不変を証明できる時のみ。証明できなければ `unknown`→design 変更側に倒し対 design 層を再凍結。**default は再凍結、純実装は例外**。

## 4. 段階導入（TL: 全面 fail-close は後段）
- **Phase A（本 Action）**: 文書正本化（規律 doc + plan-model contract + L0-L14 参照 + 9 workflow 参照化/固有 fix）。
- **Phase B（carry）**: PLAN lint で forward_return 拡張フィールド欠落を warning。
- **Phase C（carry）**: trace_symmetry + design-coverage §5 で対象 pair の machine-clean を必要条件化。
- **Phase D（carry）**: gate/RGC/G6 等価へ fail-close 接続（semantic は機械化せず detector clean AND TL/PM gate）。

## 5. acceptance（Phase A closure 条件）
- forward-return-discipline.md が R1-R5 + contract + 判定基準 + pair map + waiver + 段階導入を含む。
- 9 workflow doc が本規律を参照し、Refactor/Scrum の固有 gap が修正されている。
- plan-model.md / L0-L14 が contract / 参照を反映。
- plan validator / lint PASS、`helix doctor` baseline（24-0-105）維持。
- 私の reverse-stop-hook PLAN の遡及対応（§6）が記録されている。

## 6. forward_return
HELIX-process-L0-L14 入口表 + 各 helix-process/*-workflow.md + plan-model.md（+ 必要なら automation-gate-map.md）。既存駆動 doc を現行 V-model 正本へ合わせ直す Retrofit であり、機能追加ではない。

## 7. 遡及（reverse-stop-hook PLAN）
reverse-2026-06-03-stop-hook-state-sync は forward_return=L7→L8 で L6 機能設計を再凍結していない。本 Action が新設する判定基準で再評価し、純実装証明 or L6 DbC 遡及再凍結 or deferred finding を記録する（completed 放置しない）。

## 8. carry
- Phase B-D（機械強制の段階導入）。
- push gate の G-tests flakiness（test_audit_log state 汚染 + agent_slots timing）で gate-driven push が block される件は別 carry（本 Action と独立）。

## 9. closure（Phase A 完了、2026-06-03、commit 7b4cfad）

- **見直し**: 全 9 駆動 workflow を pmo-project-explorer ×4 で監査、V-model 非適合（forward_return が対 design 層を再凍結しない片肺抜け穴）を file:line 証跡で確定。
- **改善（Phase A）**: `forward-return-discipline.md` 新設（R1-R5 operationalize + design_change_class fail-close 判定 + 再凍結 pair map + waiver + 段階導入）。9 workflow 全てを参照化（全 9 = 1 参照確認）。Refactor「設計 PLAN 起票せず」を pure_impl 限定へ修正、Scrum 昇華先表の L7 単体テスト欠落を解消。plan-model contract / L0-L14 入口表に反映。
- **遡及**: reverse-stop-hook PLAN を design_or_contract_changed と再評価、L6 DbC 再凍結を deferred finding `DF-FRD-001` として記録（completed 放置せず）。
- **検証**: plan validator PASS（retrofit / reverse 両 exit 0）、`helix doctor` 24-0-105 維持。tl-advisor changes_required → 推奨設計を全反映。
- **carry**: Phase B-D（lint warning → detector 必要条件 → gate fail-close）。push gate flakiness は独立 carry。
