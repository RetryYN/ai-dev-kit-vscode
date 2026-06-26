# V2 doctor check → V3 detector 対応表（subset 退役 scope の L4 設計）

> 2026-06-27 / 目的: cutover の正しい形「V2 の**検出 subset** だけを V3 detector へ委譲して段階退役、
> CLI コマンドは V2 に残す」の scope を確定する。V2 helix-doctor の各 check を分類した対応表。
> first-cut（Opus 直接作成）。design-intent の不確実点は **要確認** と明示。

## 分類定義

- **A = 検出（V3 が持つべき）**: V-model / trace / drift / 契約の検出。原則 V3 engine が正本化すべき。
- **B = CLI・infra 整合（V2 に残す）**: template/role/mode/lock 等の運用整合。V3 の検出対象でなく V2 継続。
- **C = 既に V3 detector がカバー**。

## 対応表

| V2 check | 何を検出 | 分類 | V3 対応 |
|---|---|---|---|
| check_requirement_drift | FR→design→code/test 縦 trace | **C** | FN-DET-04 ✅ |
| check_vmodel_4artifact | doc/code/test/cov 4-artifact 双方向 trace | C(部分) | FN-DET-12 trace対称 + FN-DET-01 |
| check_l7_worklist | FN↔UT 充足 surfacing | C(部分) | FN-DET-05 fn-ut |
| check_plan_health | PLAN frontmatter 妥当性 | C(部分) | FN-DET-15 doc-contract(plan frontmatter) |
| check_registry_design_coverage | registry ⊆ design | C(部分) | FN-DET-02 projection-coverage |
| check_g7/g8/g9/g12/g14_subcheck | pair_closure 各ゲート | **A** | FN-DET-07 gate-confirm（**N/A**: gate_runs=0）/ 部分は 04/05/12。要確認 |
| check_anchor_quality | UT anchor 品質 | **A** | gap（FN-DET-05 隣接、anchor 品質は未実装） |
| **check_vg_overview** | whole-source ⊆ design（零漏れ） | **A** | **gap**（V3 設計 16 枠に該当なし → 要確認: 畳み or 漏れ） |
| **check_import_cycle** | cli/lib import + bash source 循環 | **A** | **gap**（16 枠該当なし → 要確認） |
| **check_plan_dependency_gate** | PLAN requires/blocks 相互性 | **A** | **gap**（16 枠該当なし → 要確認） |
| check_fr_uses | FR forward 使用 | A | FN-DET-08 forward_return 隣接。要確認 |
| check_vmodel_pair_freeze | 設計⇔検証 pair freeze | A | 部分 04/12。pair freeze gate 自体は gap。要確認 |
| check_design_doc_reference_sections | 設計 doc 必須 section | A(部分) | FN-DET-15（section 名走査は deferred） |
| **check_skill_frontmatter / skill_helix_layer_audit** | skill 契約 | **A** | **gap**（FN-DET-15 は doc/plan のみ。skill は対象外） |
| check_functional_registry / fr_sot_alignment | FR registry SSoT 整合 | A | 部分 04/05。要確認 |
| check_coding_rule_lint/sot/alignment | coding rule drift | A | FN-DET-16 rule-drift（**N/A**: rule registry 空） |
| check_bc_anti_corruption / bc_mode_coverage / glossary_coverage / ddd_registry | DDD 用語・境界 | A | **gap**（16 枠該当なし → 要確認） |
| check_drift_count / document_drift | skills/agents/roles count drift | A | 部分 FN-DET-02。要確認 |
| check_recovery_plan_freshness | recovery PLAN 鮮度 | A/B 要確認 | — |
| check_sprint_completion | sprint 完了整合 | A/B 要確認 | — |
| check_template_version | .helix template drift | **B** | —（V2 残置） |
| check_role_config_consistency / role_effort_consistency | role config mirror | **B** | —（V2 残置） |
| check_mode_phase_consistency | mode/phase runtime 整合 | **B** | —（V2 残置） |
| check_discovery_compat_warnings | discovery 互換 | **B** | —（V2 残置） |
| check_phase_gate_progress_consistency | phase/gate progress | B 要確認 | — |
| check_subagent_phase | subagent 設定 | **B** | —（V2 残置） |
| check_stale_locks | stale lock 整理 | **B** | —（V2 残置・runtime） |
| check_plan_advisory | PLAN advisory | **B**(advisory) | — |

## サマリ（3 行）

- **A で未カバー = V3 が追加実装すべき検出 gap（要 design-intent 確認）**: vg_overview（whole-source⊆design）/ import_cycle / plan_dependency_gate / skill_frontmatter+layer_audit / ddd(glossary/bc) / anchor_quality。**これらは V3 設計 16 枠に対応 id が無い** → ①16 枠に意図的に畳んだ ②別レイヤで扱う ③設計が見落とした、のどれかを確認要。
- **B = V2 に残す CLI・infra 整合**: template_version / role_config / role_effort / mode_phase / discovery_compat / subagent_phase / stale_locks / plan_advisory（+ phase_gate_progress 要確認）。
- **C = 既カバー（部分含む）**: requirement_drift(04) / vmodel_4artifact(12+01) / l7_worklist(05) / plan_health(15) / registry_design_coverage(02)。

## cutover scope への含意

- **段階退役できる subset = C の検出 check**（V3 が確実にカバー済の軸）。まずここだけを V2 doctor から「V3 へ委譲済」と marking し、二重実行を避ける段階退役の最初の候補。
- **A-gap（vg_overview / import_cycle / plan_dependency / skill / ddd / anchor）は退役不可**。V3 が未カバーなので、退役すれば検出が穴になる。これらは「V3 設計の追加 detector 枠が要るか／V2 残置か」を **L4 で design-intent 確認**してから。
- **B は退役対象外**（V3 の検出領域でない。恒久的に V2 継続）。

> 次アクション: A-gap の design-intent（16 枠への畳み込み可否）を V3 charter / L6-functional-design と突合して確定。
> 確定後、C subset の段階退役 scope（どの V2 check を no-op 化し V3 に委譲するか）を PLAN 化。破壊（退役）は §10 人間 go まで実行しない。

## A-gap design-intent 確定（2026-06-27、実装前 V2 精読で解決）

V2 各 check の実装を精読し、A-gap 6 軸を再分類（憶測でなく実装根拠）:

| A-gap 軸 | V2 実装の実態 | 判定 |
|---|---|---|
| **vg_overview** | registry/trace/G7-G14 pair-closure を集約する **overall_clean ゲート**（単一検出でなく aggregate） | **既カバー**: V3 `run_doctor` の **ok=AND 集約**が構造的に等価。新 detector 不要 |
| **import_cycle** | cli/lib import + bash source の循環依存（file scan） | **真の gap → 新規 FN-DET-17 import-cycle** |
| **plan_dependency** | PLAN requires/blocks の相互性・存在（plan frontmatter） | **真の gap → 新規 FN-DET-18 plan-dependency** |
| skill_frontmatter / layer_audit | skill 契約 lint | **V2 残置**（FN-DET-15 doc-contract は doc/plan 対象。skill は別軸、当面 V2） |
| ddd（glossary/bc） | DDD 用語・境界 coverage | **V2 残置**（governance 寄り、V3 検出 scope 外と判断） |
| anchor_quality | UT anchor 品質 | **FN-DET-05 拡張で将来吸収**（当面 V2 残置） |

**決定（可逆な設計拡張、PM/architect 直接判断）**: V3 detector corpus を **16→18 に拡張**（import-cycle / plan-dependency を追加）。vg_overview は ok=AND 集約で既カバーと記録。skill/ddd/anchor は当面 V2 残置（恒久排除でなく deferred、source/需要が立てば再検討）。

> これで repo-applicable な検出軸は **C（既カバー）+ FN-DET-17/18 + ok=AND 集約** で実質充足。残る cutover 作業は「C subset + 17/18 を V2 doctor から no-op 化する段階退役 PLAN（§10 人間 go 必須）」。
