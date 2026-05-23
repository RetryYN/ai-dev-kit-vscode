---
doc_id: v2-plan-templates-readme
title: "V2 PLAN テンプレート (L0-L14)"
status: maintained
created: 2026-05-24
owner: PM
canonical_source: HELIX-workflows/HELIX-process-L0-L14.md
---

# V2 PLAN テンプレート (L0-L14、HELIX-workflows 正本準拠)

> **正本**: [HELIX-workflows/HELIX-process-L0-L14.md](../../../../HELIX-workflows/HELIX-process-L0-L14.md)

## 使い方

新規 PLAN 起票時、該当工程の template を copy して `docs/plans/L<NN>/L<NN>-<slug>plan.md` に配置。

```bash
# 例: L7 実装 PLAN を起票
mkdir -p docs/plans/L7
cp cli/templates/plan/v2/L07-implementation-template.md docs/plans/L7/L7-helix-workspace-mergeplan.md
# frontmatter の placeholder (<NN>, <slug>, <title>) を編集
```

## 命名規則 (HELIX-workflows 正本)

- 形式: `L<工程番号>-○○○plan` (例: `L0-企画書plan` / `L7-helix-workspace-mergeplan`)
- 配置: `docs/plans/L0/` 〜 `docs/plans/L14/` にフォルダ分離

## V2 PLAN frontmatter 必須 field

```yaml
plan_id: L<NN>-<slug>plan
title: "L<NN>-<slug>plan: <タイトル>"
kind: <工程に応じた kind>            # planning/requirements/ui-design/basic-design/detailed-design/function-design/impl/test/ux-refinement/review/deployment/operation
layer: L<NN>                          # plan_validator enum (L0-L14)
drive: <be|fe|fullstack|...>
status: draft
created: YYYY-MM-DD
owner: PM
process_layer: L<NN>                  # 工程番号 (HELIX-workflows)
parent_process: HELIX-workflows/L<NN>-*.md  # 工程定義 doc
parent_design: <L7 のみ>               # L6 機能設計 doc への path (L7 impl のみ必須)
pairs_test_design: []                  # V-model ペア (該当工程のみ)
is_reference: false                    # V2 製本対象 = false
agent_slots: []
generates: []
dependencies:
  parent: null
  requires: []
  blocks: []
```

## V2 PLAN 本文の 2 要素 (内蔵)

PLAN は **工程表 (作業手順 + 進捗) + 実装計画** の 2 要素を内蔵し、作業中断時に再開可能。

```markdown
## §1 工程表 (作業手順 + 進捗)
| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | 参考調査 (Web 検索 / 既存資料整理) | □ pending |
| 2 | ドラフト起草 | □ pending |
| 3 | TL レビュー | □ pending |
| 4 | 確定 | □ pending |

## §2 実装計画 (記載項目をどう埋めるか)
- 項目 A: ...
- 項目 B: ...
```

## template 一覧

| 工程 | template | HELIX-workflows 正本 |
|---|---|---|
| L0 | [L00-planning-template.md](L00-planning-template.md) | [L0-concept.md](../../../../HELIX-workflows/helix-process/L0-concept.md) |
| L1 | [L01-requirements-template.md](L01-requirements-template.md) | [L1-requirements.md](../../../../HELIX-workflows/helix-process/L1-requirements.md) |
| L2 | [L02-ui-design-template.md](L02-ui-design-template.md) | [L2-ui-design.md](../../../../HELIX-workflows/helix-process/L2-ui-design.md) |
| L3 | [L03-requirements-definition-template.md](L03-requirements-definition-template.md) | [L3-requirements-definition.md](../../../../HELIX-workflows/helix-process/L3-requirements-definition.md) |
| L4 | [L04-basic-design-template.md](L04-basic-design-template.md) | [L4-basic-design.md](../../../../HELIX-workflows/helix-process/L4-basic-design.md) |
| L5 | [L05-detailed-design-template.md](L05-detailed-design-template.md) | [L5-detailed-design.md](../../../../HELIX-workflows/helix-process/L5-detailed-design.md) |
| L6 | [L06-function-design-template.md](L06-function-design-template.md) | [L6-functional-design.md](../../../../HELIX-workflows/helix-process/L6-functional-design.md) |
| L7 | [L07-implementation-template.md](L07-implementation-template.md) | [L7-implementation.md](../../../../HELIX-workflows/helix-process/L7-implementation.md) |
| L8 | [L08-integration-test-template.md](L08-integration-test-template.md) | [L8-integration-test.md](../../../../HELIX-workflows/helix-process/L8-integration-test.md) |
| L9 | [L09-system-test-template.md](L09-system-test-template.md) | [L9-system-test.md](../../../../HELIX-workflows/helix-process/L9-system-test.md) |
| L10 | [L10-ux-refinement-template.md](L10-ux-refinement-template.md) | [L10-ux-refinement.md](../../../../HELIX-workflows/helix-process/L10-ux-refinement.md) |
| L11 | [L11-final-review-template.md](L11-final-review-template.md) | [L11-final-review.md](../../../../HELIX-workflows/helix-process/L11-final-review.md) |
| L12 | [L12-deployment-template.md](L12-deployment-template.md) | [L12-deployment.md](../../../../HELIX-workflows/helix-process/L12-deployment.md) |
| L13 | [L13-post-deployment-template.md](L13-post-deployment-template.md) | [L13-post-deployment-verification.md](../../../../HELIX-workflows/helix-process/L13-post-deployment-verification.md) |
| L14 | [L14-operation-verification-template.md](L14-operation-verification-template.md) | [L14-operation-verification.md](../../../../HELIX-workflows/helix-process/L14-operation-verification.md) |
