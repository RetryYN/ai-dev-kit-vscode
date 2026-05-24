---
plan_id: L7-docs-integration-mappingplan
title: "L7-docs-integration-mappingplan: helix-process/ ワークフロー文書を docs/ / skills/ / .md プロトコル層へ接続 (文書統合 #5)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/integration-map.md
pairs_test_design:
  - HELIX-workflows/helix-process/folder-structure-review.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — スコープ確認・統合方針最終判断・DoD 受入"
  - role: tl-advisor
    slot_label: "TL — INDEX 構造設計・frontmatter schema 整合・cross-reference 正当性 adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — 各 docs/ 配下 cross-reference 整合・folder-structure-review §統合方針との完全一致確認"
  - role: docs
    slot_label: "docs — helix-process/*.md frontmatter 追加・appendix 起草・AGENTS/CLAUDE.md 追記"
generates:
  # INDEX (Sprint .2)
  - artifact_path: docs/architecture/helix-workflows-index.md
    artifact_type: design_doc
  # helix-process/*.md integration_target frontmatter 追加 (Sprint .3) — 45 件 (README 除外)
  - artifact_path: HELIX-workflows/helix-process/L0-concept.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L1-requirements.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L2-ui-design.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L3-requirements-definition.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L4-basic-design.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L5-detailed-design.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L6-functional-design.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L7-implementation.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L8-integration-test.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L9-system-test.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L10-ux-refinement.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L11-final-review.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L12-deployment.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L13-post-deployment-verification.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/L14-operation-verification.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/discovery-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/scrum-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/reverse-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/incident-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/add-feature-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/refactor-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/retrofit-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/research-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/recovery-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/screen-design-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/frontend-design-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/ci-pr-workflow.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/continuous-run-context-management.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/db-auto-registration.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/db-integration.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/deviation-plan-map.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/infra-readiness.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/observability-metrics.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/test-perspective-gate.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/detection-routing.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/learning-engine.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/cross-detection.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/layer-context-injection.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/asset-mapping.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/cross-cutting-mechanisms.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/fe-detector-spec.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/folder-structure-review.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/integration-map.md
    artifact_type: design_doc
  - artifact_path: HELIX-workflows/helix-process/two-stage-agent-design.md
    artifact_type: design_doc
  # appendix 追記 (Sprint .4) — docs domain 各 1 ファイル × 8 件
  - artifact_path: docs/architecture/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/adr/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/research/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/runbook/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/rollback/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/postmortem/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/slo/helix-workflows-appendix.md
    artifact_type: design_doc
  - artifact_path: docs/design/helix-workflows-appendix.md
    artifact_type: design_doc
  # プロトコル層追記 (Sprint .5-.6)
  - artifact_path: AGENTS.md
    artifact_type: design_doc
  - artifact_path: CLAUDE.md
    artifact_type: design_doc
  - artifact_path: skills/SKILL_MAP.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/folder-structure-review.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - docs/architecture/cli-layout.md
---

# L7-docs-integration-mappingplan

helix-process/ ワークフロー文書 (計 46 件、うち処理対象 45 件・README は navigation 扱いで対象外) を、既存 docs/ 構造・skills/SKILL_MAP.md・.md プロトコル層 (AGENTS.md / CLAUDE.md) へ接続する。

integration-map.md §結論と優先順位 **#5 文書統合** を実行する実装 PLAN。

---

## §0 PLAN concept (統合方針)

### 背景

HELIX-workflows/helix-process/ には 46 ファイルの設計文書が存在するが、以下の 3 点で孤立した状態にある:

1. docs/ の既存構造 (adr / research / runbook / architecture / design 等) と接続されていない
2. skills/SKILL_MAP.md にワークフロー文書への cross-reference がない
3. AGENTS.md / CLAUDE.md の §HELIX ワークフロー section に文書統合方針の記載がない

folder-structure-review.md §フォルダ再構成のまとめ が確立した統合方針:

> 再構成の核心は、新規フォルダを増やすことではなく、helix-process/ に作った設計を、既に置き場が用意されている docs/ へ接続することにある。

### 統合方針 (3 原則)

1. **新規フォルダ増設禁止**: 既存 docs/ 構造 (adr / research / runbook / rollback / postmortem / slo / architecture / design / requirements / specs) へ接続のみ
2. **実体移動なし**: helix-process/*.md を docs/ へ移動しない。reference link と frontmatter による論理接続に限定
3. **双方向接続**: docs/ 側から helix-process/ への link + helix-process/ 側から docs/ への integration_target frontmatter

### 統合先 mapping (folder-structure-review.md §統合方針正本)

> **分類ルール確定 (P1-1 修正)**: 対象 = 45 files (README 除外)。README は navigation 文書として out_of_scope。カテゴリ = 7 (下表)。incident/recovery は「モードワークフロー」に固定 (二重所属なし)。docs_path = docs/runbook を個別割当で区別。

| helix-process/ 文書カテゴリ | 文書数 | 統合先 docs/ | 対象ファイル |
|---|---|---|---|
| L0–L14 工程 | 15 | docs/requirements または docs/design または docs/specs | L0-concept.md 〜 L14-operation-verification.md |
| モードワークフロー | 9 | docs/design (基本)、incident/recovery は docs/runbook | discovery / scrum / reverse / incident / add-feature / refactor / retrofit / research / recovery -workflow.md |
| 工程専門 | 2 | docs/design | screen-design-workflow.md / frontend-design-workflow.md |
| 管理・自動化 | 9 | docs/architecture | automation-gate-map.md / ci-pr-workflow.md / continuous-run-context-management.md / db-auto-registration.md / db-integration.md / deviation-plan-map.md / infra-readiness.md / observability-metrics.md / test-perspective-gate.md |
| 検出・学習・注入 | 4 | docs/architecture | detection-routing.md / learning-engine.md / cross-detection.md / layer-context-injection.md |
| ADR/research 関連 | 6 | docs/architecture または docs/adr / docs/research | asset-mapping.md / cross-cutting-mechanisms.md / fe-detector-spec.md / folder-structure-review.md / integration-map.md / two-stage-agent-design.md |
| README | 1 | **out_of_scope** (ナビゲーション文書) | README.md |
| **合計** | **46** | — | **処理対象 45、README 1** |

---

## §1 工程表 (作業手順 + 進捗)

### Sprint .1 — 前提確認・INDEX 設計 (PM + TL)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 1.1 | folder-structure-review.md §統合方針 精読・45 ファイル分類確定 (README 除外) | PM (pmo-sonnet) | 全 45 ファイルが §0 mapping table の 7 カテゴリに割り当て済み (incident/recovery はモードワークフロー固定) |
| 1.2 | docs/architecture/helix-workflows-index.md の INDEX 構造設計 | TL (tl-advisor) | カテゴリ別 table + docs/ 統合先列 + 文書 link 列の 3 列構成が承認済み |
| 1.3 | integration_target frontmatter schema 定義 | TL | schema = `integration_target: {docs_path: str, category: str}` |
| 1.4 | tl-advisor adversarial check | TL | P0/P1 指摘なし または 解消済み |

### Sprint .2 — INDEX 作成 (docs)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 2.1 | docs/architecture/helix-workflows-index.md 新規作成 | docs | 全 45 ファイル × (file / primary_category / docs_path / appendix_file / link) の 5 列 table に収録 (README 除外) |
| 2.2 | INDEX の docs/ 統合先列が §0 mapping table と完全一致 | pmo-sonnet | diff 0 件 |
| 2.3 | INDEX に「実体移動なし・参照のみ」方針を注記 | docs | 注記あり |

### Sprint .3 — helix-process/*.md frontmatter 追加 (docs)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 3.1 | 全 46 ファイルに integration_target frontmatter 追加 | docs | `grep -l "integration_target" HELIX-workflows/helix-process/*.md \| wc -l` = 45 (README 除く) |
| 3.2 | integration_target.docs_path が INDEX と一致 | pmo-sonnet | 不一致 0 件 |
| 3.3 | 既存 frontmatter の破壊がない | docs | yaml lint PASS |

### Sprint .4 — docs/ appendix 新規作成 (docs) — 8 件

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 4.1 | docs/architecture/helix-workflows-appendix.md 新規作成 (中央 index 兼) | docs | 管理・自動化 / 検出・学習・注入 / ADR/research 関連の参照 table 存在 |
| 4.2 | docs/adr/helix-workflows-appendix.md 新規作成 | docs | integration-map.md / folder-structure-review.md / two-stage-agent-design.md への link 存在 |
| 4.3 | docs/research/helix-workflows-appendix.md 新規作成 | docs | asset-mapping.md / cross-cutting-mechanisms.md / fe-detector-spec.md への link 存在 |
| 4.4 | docs/runbook/helix-workflows-appendix.md 新規作成 | docs | recovery-workflow.md / incident-workflow.md への link 存在 |
| 4.5 | docs/rollback/helix-workflows-appendix.md 新規作成 | docs | recovery-workflow.md (ロールバック観点) への link 存在 |
| 4.6 | docs/postmortem/helix-workflows-appendix.md 新規作成 | docs | incident-workflow.md (postmortem 観点) への link 存在 |
| 4.7 | docs/slo/helix-workflows-appendix.md 新規作成 | docs | observability-metrics.md / infra-readiness.md への link 存在 |
| 4.8 | docs/design/helix-workflows-appendix.md 新規作成 | docs | モードワークフロー 9 件 + 工程専門 2 件 + L0-L14 工程 15 件への link 存在 |
| 4.9 | 全 8 appendix ファイルを INDEX §appendix 追記済みファイル section に反映 | docs | INDEX 更新済み |

### Sprint .5 — AGENTS.md / CLAUDE.md 追記 (docs)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 5.1 | AGENTS.md §HELIX ワークフロー section に「文書統合方針」項追記 | docs | `docs/architecture/helix-workflows-index.md` への参照リンクが AGENTS.md に存在 |
| 5.2 | CLAUDE.md §HELIX ワークフロー section に「文書統合方針」項追記 | docs | `docs/architecture/helix-workflows-index.md` への参照リンクが CLAUDE.md に存在 |
| 5.3 | AGENTS.md / CLAUDE.md の既存 §HELIX ワークフロー 内容を破壊していない | pmo-sonnet | 既存文 diff 確認 / 追記のみ |

### Sprint .6 — SKILL_MAP.md 追記 (docs)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 6.1 | SKILL_MAP.md に「ワークフロー文書統合 cross-reference」section 追加 | docs | `docs/architecture/helix-workflows-index.md` への参照リンクが SKILL_MAP.md に存在 |
| 6.2 | 既存 SKILL_MAP.md の内容を破壊していない | pmo-sonnet | grep で既存 section title 全件一致 |

### Sprint .7 — lint・review・DoD 確認 (PM + TL + PMO)

| Step | 作業 | 担当 | 受入条件 |
|---|---|---|---|
| 7.1 | helix plan lint PASS | PM | warnings 0 |
| 7.2 | INDEX の 45 ファイル × docs/ 統合先 table 整合性確認 | pmo-sonnet | 不一致 0 件 (README は out_of_scope 確認) |
| 7.3 | folder-structure-review.md §統合方針との完全一致確認 | pmo-sonnet | diff 0 件 |
| 7.4 | AGENTS.md / CLAUDE.md 追記内容が既存方針と矛盾しない | pmo-sonnet | 矛盾 0 件 |
| 7.5 | tl-advisor 最終 adversarial check | TL | P0/P1 指摘なし または 解消済み |

---

## §2 実装計画

### §2.A docs/architecture/helix-workflows-index.md (新規、Sprint .2)

INDEX は以下の構成で新規作成する。列構成: `file / primary_category / docs_path / appendix_file / link` の 5 列。

```markdown
# HELIX-workflows INDEX

本ファイルは docs/architecture/ から HELIX-workflows/helix-process/ の全設計文書への
論理的接続インデックス。実体ファイルは移動しない (reference link のみ)。
対象: 45 files (README は navigation 扱いで対象外)。

## カテゴリ別一覧 (45 ファイル)

| ファイル | primary_category | docs_path | appendix_file | link |
|---|---|---|---|---|
| L0-concept.md | L0-L14 工程 | docs/requirements | docs/design/helix-workflows-appendix.md | [link](../../HELIX-workflows/helix-process/L0-concept.md) |
| L1-requirements.md | L0-L14 工程 | docs/requirements | docs/design/helix-workflows-appendix.md | [link] |
| L2-ui-design.md | L0-L14 工程 | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| ... (L3〜L14 同様) | L0-L14 工程 | docs/requirements または docs/design | docs/design/helix-workflows-appendix.md | [link] |
| discovery-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| scrum-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| reverse-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| incident-workflow.md | モードワークフロー | docs/runbook | docs/runbook/helix-workflows-appendix.md | [link] |
| add-feature-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| refactor-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| retrofit-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| research-workflow.md | モードワークフロー | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| recovery-workflow.md | モードワークフロー | docs/runbook | docs/runbook/helix-workflows-appendix.md | [link] |
| screen-design-workflow.md | 工程専門 | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| frontend-design-workflow.md | 工程専門 | docs/design | docs/design/helix-workflows-appendix.md | [link] |
| automation-gate-map.md | 管理・自動化 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| ... (管理・自動化 残 8 件) | 管理・自動化 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| detection-routing.md | 検出・学習・注入 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| learning-engine.md | 検出・学習・注入 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| cross-detection.md | 検出・学習・注入 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| layer-context-injection.md | 検出・学習・注入 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| asset-mapping.md | ADR/research 関連 | docs/architecture | docs/research/helix-workflows-appendix.md | [link] |
| cross-cutting-mechanisms.md | ADR/research 関連 | docs/architecture | docs/architecture/helix-workflows-appendix.md | [link] |
| fe-detector-spec.md | ADR/research 関連 | docs/architecture | docs/research/helix-workflows-appendix.md | [link] |
| folder-structure-review.md | ADR/research 関連 | docs/architecture | docs/adr/helix-workflows-appendix.md | [link] |
| integration-map.md | ADR/research 関連 | docs/architecture | docs/adr/helix-workflows-appendix.md | [link] |
| two-stage-agent-design.md | ADR/research 関連 | docs/architecture | docs/adr/helix-workflows-appendix.md | [link] |

## appendix 追記済みファイル (Sprint .4 完了後更新)

| docs/ ファイル (literal path) | 参照先カテゴリ |
|---|---|
| docs/architecture/helix-workflows-appendix.md | 管理・自動化 / 検出・学習・注入 / ADR/research 関連 (中央 index 兼) |
| docs/adr/helix-workflows-appendix.md | ADR/research 関連 (integration-map / folder-structure-review / two-stage-agent-design) |
| docs/research/helix-workflows-appendix.md | ADR/research 関連 (asset-mapping / cross-cutting-mechanisms / fe-detector-spec) |
| docs/runbook/helix-workflows-appendix.md | recovery-workflow.md / incident-workflow.md |
| docs/rollback/helix-workflows-appendix.md | recovery-workflow.md (ロールバック観点) |
| docs/postmortem/helix-workflows-appendix.md | incident-workflow.md (postmortem 観点) |
| docs/slo/helix-workflows-appendix.md | observability-metrics.md / infra-readiness.md |
| docs/design/helix-workflows-appendix.md | モードワークフロー 9 件 + 工程専門 2 件 + L0-L14 工程 15 件 |
```

### §2.B helix-process/*.md integration_target frontmatter 追加 (Sprint .3)

対象 45 ファイル (README 除外)。追加 frontmatter schema:

```yaml
integration_target:
  docs_path: "docs/architecture"   # §0 mapping table の統合先 (カテゴリ別)
  category: "検出・学習・注入"      # 7 カテゴリのいずれか (下表)
```

> **上書きルール**: `integration_target` key が既存 frontmatter に無ければ追加する。既に存在し値が同じならスキップ。値が異なる場合は fail して手動判断を要求する (自動上書き禁止)。

カテゴリ別 docs_path 対応 (7 カテゴリ、計 45 件):

| カテゴリ | 件数 | docs_path | 対象ファイル |
|---|---|---|---|
| L0-L14 工程 | 15 | docs/requirements または docs/design または docs/specs | L0-concept.md〜L14-operation-verification.md |
| モードワークフロー | 9 | docs/design (基本)、incident/recovery は docs/runbook | discovery / scrum / reverse / incident / add-feature / refactor / retrofit / research / recovery-workflow.md |
| 工程専門 | 2 | docs/design | screen-design-workflow.md / frontend-design-workflow.md |
| 管理・自動化 | 9 | docs/architecture | automation-gate-map.md / ci-pr-workflow.md / continuous-run-context-management.md / db-auto-registration.md / db-integration.md / deviation-plan-map.md / infra-readiness.md / observability-metrics.md / test-perspective-gate.md |
| 検出・学習・注入 | 4 | docs/architecture | detection-routing.md / learning-engine.md / cross-detection.md / layer-context-injection.md |
| ADR/research 関連 | 6 | docs/architecture または docs/adr / docs/research | asset-mapping.md / cross-cutting-mechanisms.md / fe-detector-spec.md / folder-structure-review.md / integration-map.md / two-stage-agent-design.md |
| README | 1 | **out_of_scope** | README.md (frontmatter 追加対象外) |
| **合計** | **46** | — | **処理対象 45** |

### §2.C docs/ 既存配下 appendix 追記 (Sprint .4)

各 docs domain に新規ファイル **1 件** (`helix-workflows-appendix.md`) を作成し、対応する helix-process/ 文書への参照を記載する。既存ファイル内容を変更しない。

appendix 8 件の対応表 (P1-3 修正):

| 新規ファイル (literal path) | 参照先 helix-process/ 文書 |
|---|---|
| docs/architecture/helix-workflows-appendix.md | 管理・自動化 (9 件) + 検出・学習・注入 (4 件) + ADR/research 関連 (6 件) + 中央 index 兼 |
| docs/adr/helix-workflows-appendix.md | ADR/research 関連のうち integration-map.md / folder-structure-review.md / two-stage-agent-design.md |
| docs/research/helix-workflows-appendix.md | asset-mapping.md / cross-cutting-mechanisms.md / fe-detector-spec.md |
| docs/runbook/helix-workflows-appendix.md | recovery-workflow.md / incident-workflow.md |
| docs/rollback/helix-workflows-appendix.md | recovery-workflow.md (ロールバック観点) |
| docs/postmortem/helix-workflows-appendix.md | incident-workflow.md (postmortem 観点) |
| docs/slo/helix-workflows-appendix.md | observability-metrics.md / infra-readiness.md |
| docs/design/helix-workflows-appendix.md | モードワークフロー 9 件 + 工程専門 2 件 + L0-L14 工程 15 件 |

各ファイル構成: タイトル + 参照先 table (file / link / 説明 3 列) + 「実体ファイルは移動しない」方針注記。

### §2.D AGENTS.md / CLAUDE.md §HELIX ワークフロー 追記 (Sprint .5)

追記内容 (両ファイル共通):

```markdown
### 文書統合方針 (helix-process/ → docs/)

helix-process/ の 46 ファイルは新規フォルダ増設なしに docs/ へ論理接続済み。
統合 INDEX: [docs/architecture/helix-workflows-index.md](docs/architecture/helix-workflows-index.md)
```

CLAUDE.md は `§HELIX ワークフロー` 末尾への 3–5 行追記。AGENTS.md は対応 section 末尾への同等追記。

### §2.E SKILL_MAP.md cross-reference 追加 (Sprint .6)

SKILL_MAP.md §オーケストレーションフロー の末尾または適切な section 末尾に追加:

```markdown
### ワークフロー文書統合 cross-reference

helix-process/ 全 46 ファイルの docs/ 統合 INDEX:
[docs/architecture/helix-workflows-index.md](../docs/architecture/helix-workflows-index.md)
```

---

## §3 成果物 (generates)

| 成果物 | 種別 | Sprint | 備考 |
|---|---|---|---|
| docs/architecture/helix-workflows-index.md | design_doc (新規) | .2 | 5 列 INDEX、全 45 件収録 |
| HELIX-workflows/helix-process/L0-concept.md 〜 L14-operation-verification.md (15 件) | design_doc (frontmatter 追記) | .3 | integration_target 追加 |
| HELIX-workflows/helix-process/ モードワークフロー 9 件 | design_doc (frontmatter 追記) | .3 | discovery〜recovery |
| HELIX-workflows/helix-process/ 工程専門 2 件 | design_doc (frontmatter 追記) | .3 | screen / frontend |
| HELIX-workflows/helix-process/ 管理・自動化 9 件 | design_doc (frontmatter 追記) | .3 | automation-gate-map 等 |
| HELIX-workflows/helix-process/ 検出・学習・注入 4 件 | design_doc (frontmatter 追記) | .3 | detection-routing 等 |
| HELIX-workflows/helix-process/ ADR/research 関連 6 件 | design_doc (frontmatter 追記) | .3 | asset-mapping 等 |
| docs/architecture/helix-workflows-appendix.md | design_doc (新規) | .4 | 中央 index 兼 |
| docs/adr/helix-workflows-appendix.md | design_doc (新規) | .4 | ADR/research 関連参照 |
| docs/research/helix-workflows-appendix.md | design_doc (新規) | .4 | research 関連参照 |
| docs/runbook/helix-workflows-appendix.md | design_doc (新規) | .4 | recovery / incident 参照 |
| docs/rollback/helix-workflows-appendix.md | design_doc (新規) | .4 | recovery ロールバック観点 |
| docs/postmortem/helix-workflows-appendix.md | design_doc (新規) | .4 | incident postmortem 観点 |
| docs/slo/helix-workflows-appendix.md | design_doc (新規) | .4 | observability / infra 参照 |
| docs/design/helix-workflows-appendix.md | design_doc (新規) | .4 | mode / 工程専門 / L0-L14 参照 |
| AGENTS.md | design_doc (追記) | .5 | §HELIX ワークフロー 末尾 |
| CLAUDE.md | design_doc (追記) | .5 | §HELIX ワークフロー 末尾 |
| skills/SKILL_MAP.md | design_doc (追記) | .6 | cross-reference 追加 |

---

## §4 受入条件 / DoD

### 機械検証

```bash
# 1. helix plan lint PASS
helix plan lint docs/plans/L7/L7-docs-integration-mappingplan.md

# 2. INDEX ファイル存在確認
test -f docs/architecture/helix-workflows-index.md && echo "INDEX OK"

# 3. helix-process/*.md 全件 integration_target frontmatter 確認 (README 除く)
grep -l "integration_target" HELIX-workflows/helix-process/*.md | grep -v README | wc -l
# 期待値: 45

# 4. AGENTS.md / CLAUDE.md に INDEX link 存在確認
grep -l "helix-workflows-index" AGENTS.md CLAUDE.md | wc -l
# 期待値: 2

# 5. SKILL_MAP.md に INDEX link 存在確認
grep "helix-workflows-index" skills/SKILL_MAP.md | wc -l
# 期待値: >= 1

# 6. appendix 8 件 存在確認
for f in \
  docs/architecture/helix-workflows-appendix.md \
  docs/adr/helix-workflows-appendix.md \
  docs/research/helix-workflows-appendix.md \
  docs/runbook/helix-workflows-appendix.md \
  docs/rollback/helix-workflows-appendix.md \
  docs/postmortem/helix-workflows-appendix.md \
  docs/slo/helix-workflows-appendix.md \
  docs/design/helix-workflows-appendix.md; do
  test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done

# 7. yaml lint (frontmatter 追記ファイル全件)
python3 -c "
import yaml, glob, sys
errors = []
for f in glob.glob('HELIX-workflows/helix-process/*.md'):
    try:
        content = open(f).read()
        if content.startswith('---'):
            fm = content.split('---')[1]
            yaml.safe_load(fm)
    except Exception as e:
        errors.append(f'{f}: {e}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print('yaml lint PASS')
"
```

### review 検証

| 確認観点 | 担当 | 合否基準 |
|---|---|---|
| INDEX の 45 ファイル × docs/ 統合先 整合 (README out_of_scope 確認) | pmo-sonnet | §0 mapping table との diff 0 件 |
| helix-process/*.md integration_target.docs_path と INDEX 一致 | pmo-sonnet | 不一致 0 件 |
| AGENTS.md / CLAUDE.md 既存内容の破壊なし | pmo-sonnet | 追記以外の変更 0 件 |
| SKILL_MAP.md 既存 section title 一致 | pmo-sonnet | grep で全件一致 |
| tl-advisor adversarial check (P0/P1 指摘なし) | TL | passed または 指摘解消済み |

---

## §5 関連 doc

- [integration-map.md §結論と優先順位 #5](HELIX-workflows/helix-process/integration-map.md)
- [folder-structure-review.md §フォルダ再構成のまとめ](HELIX-workflows/helix-process/folder-structure-review.md)
- [HELIX-process-L0-L14.md](HELIX-workflows/HELIX-process-L0-L14.md)
- [docs/architecture/cli-layout.md](docs/architecture/cli-layout.md)
- [docs/architecture/test-layout.md](docs/architecture/test-layout.md)

---

## §6 後続 PLAN 候補

| 候補 | 内容 | 前提 |
|---|---|---|
| L7-docs-integration-phase2plan (仮) | docs/ 既存文書のより深い統合 (移動・リネーム・統廃合) | 本 PLAN 完遂後、必要性評価 |
| skills/ への新ワークフロースキル追加 | integration-map §3 スキル穴埋め (retrofit / detection-routing 等) | 別 PLAN (L7-skill-retrofit-implplan 等) で管理 |

---

## §7 リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| helix-process/*.md に既存 frontmatter が多様で yaml parse 失敗 | Sprint .3 で yaml lint エラー | 追記前に全件 yaml lint → 問題ファイル個別修正 |
| AGENTS.md / CLAUDE.md 追記が既存ルールと矛盾 | §2.D で方針衝突 | pmo-sonnet review を Sprint .5 完了直後に実施 |
| docs/ 既存ファイルへの appendix 追記が CI / markdownlint で reject | Sprint .4 で lint 失敗 | 追記前に markdownlint dry-run + 既存ファイルの lint ルール確認 |
| INDEX の 46 ファイル分類が folder-structure-review.md と乖離 | Sprint .2 で不一致 | Sprint .1.1 でカテゴリ割り当て PM 承認を先行 |
