---
doc_id: asset-mapping
title: "既存資産の整理と設計マッピング"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# 既存資産の整理と設計マッピング

## 既存資産の棚卸し

| カテゴリ | 資産 | 規模 |
|---|---|---|
| コマンド | helix-*（plan / gate / detect / verify / learn / context / matrix / doctor / drift-check / interrupt / debt / readiness 他） | 71 |
| スキル | workflow 33 / agent-skills 23 / common 12 / advanced 9 / project 8 / automation 8 / design-tools 6 / writing 5 / tools 4 / integration 3 | 111 |
| detector | axis-01〜14（実装）/ axis-15〜19（FE stub） | 14 + 5 |
| PLAN template | design / impl / poc / reverse / troubleshoot / refactor / retrofit / research / add-design / add-impl / recovery | 11 kind |
| 工程 template | docs L1 / L2 / L3 / L4(sprint-guide 5) / L5 | 一部 |
| DB 資産 | helix_db ＋ catalog/registry 6種（code / command / contract / model / plan / skill）＋ db_cli ＋ drift_db_diff | — |
| hook 資産 | codex_post_hook / feedback_hook / hook_payload ＋ libexec（post-tool-use / pre-bash / pre-research / session-start） | — |
| docs | adr 37 / plans 233 / design 17 / runbook 9 / architecture 4 / research 1 / requirements 1 ほか | 472 |
| tests | cli/lib/tests 213 / cli/tests 82 / tests 9 / .claude/hooks/tests 3 | 307 |
| config | vmodel-semantics ほか | 5 |

## 設計 ⇔ 既存資産マッピング（充足度）

| 本セッション設計 | 対応する既存資産 | 充足度 | 不足 |
|---|---|---|---|
| Forward L0–L14 | docs template L1–L5、docs/requirements・design | 部分 | L0 / L6–L14 の雛形 |
| 入口モード9 | PLAN template 11全、skill（recovery / incident / reverse / refactor / research / context） | 部分 | retrofit skill |
| Recovery | recovery template、agent_mandatory、budget、stop-hook、cutover_orchestrator | 部分 | helix-recover コマンド |
| detection-routing | drift-check、detector、doctor | 部分 | helix-route コマンド |
| cross-detection | axis-10 / 07 / 12 / 11、doctor | 充足 | — |
| learning-engine | helix-learn、learning_engine、feedback_hook | 充足 | — |
| layer-context-injection | helix-context、agent_mandatory、skill_catalog、command_catalog、helix-matrix | 部分 | vmodel-semantics 注入セット |
| db-integration | helix_db、catalog/registry 6種、db_cli | 充足 | — |
| db-auto-registration | codex_post_hook、feedback_hook、hook_payload、libexec hooks、plan_registry.bulk_import | 充足 | 一部の配線 |
| test-perspective-gate | vmodel テストレベル、双方向 trace、axis-02 / 11 | 部分 | 観点ゲートの実装 |
| ADR / research | docs/adr（37本）、docs/research | 部分 | 雛形テンプレートのみ |

## 整理の結論

充足（既存資産だけで設計が成立）するのは cross-detection / learning-engine / db-integration / db-auto-registration。DB の catalog/registry 6種と hook 群がすでに揃っているためで、本セッションで設計した「自動登録 → 検出 → 学習」のループは、既存資産の上にそのまま乗る。

部分（既存資産＋一部不足）は Forward 雛形 / モード / Recovery / detection-routing / layer-context-injection / test-perspective-gate / ADR。これらの不足は、新規の設計ではなく、すべて integration-map.md の穴（注入セット定義・helix-recover / helix-route・retrofit ほかスキル化・generates / 工程テンプレート）に集約される。

つまり設計の大半は既存資産の上に成立しており、新規に作るべきは穴の部分に限られる。既存の docs/adr（37）・docs/plans（233）という蓄積もあるため、本セッションの設計は「ゼロから作る」のではなく「既存資産へ接続し、穴を埋める」作業として進められる。
