---
plan_id: L7-vmodel-pair-freeze-skeleton-patchplan
title: "L7-vmodel-pair-freeze-skeleton-patchplan: stale suggestion から markdown skeleton patch 生成"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-25
revised: 2026-05-25
process_layer: L7
parent_design: HELIX-workflows/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-vmodel-pair-freeze-stale-suggestionplan.md
    - docs/plans/L7/L7-test-design-scaffoldplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — generate_stale_patch helper 実装"
  - role: qa
    slot_label: "QA — pytest / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-skeleton-patchplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
---

## §0 PLAN concept

`suggest_stale_revisions()` の結果を起点に、stale pair PLAN ごとの `revised` frontmatter 更新を unified diff 形式で dry-run 生成する `generate_stale_patch()` を追加する。file write や doctor 接続は行わず、review 可能な patch artifact だけを返す。

## §1 背景

- `L7-vmodel-pair-freeze-stale-suggestionplan` で stale PLAN 候補列挙までは自動化された
- `L7-test-design-scaffoldplan` では dry-run scaffold を command 分離で扱っており、今回も同様に write 前の review 可能形式へ寄せる
- carry として残っていた「markdown skeleton patch 生成」を unified diff に限定して先に固定すると、後続 apply / review queue 連携へ繋ぎやすい

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` に `generate_stale_patch(layer, *, project_root, since_days=30)` を追加する
2. helper は `suggest_stale_revisions()` を呼び出し、stale PLAN ごとに `revised` 行の unified diff patch を生成する
3. 返却要素は `plan_id`, `plan_path`, `unified_diff`, `before_revised`, `after_revised` を持つ
4. pair を持たない layer、または paired doc 不在時は空 list を返す
5. pytest 3 件で diff 生成 / recent skip / no-pair を固定する

scope 外:

- patch の file write / apply
- `helix doctor` への CLI 接続
- `revised` 以外の frontmatter / 本文 skeleton 展開

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件追加 (Red) | unified diff 契約が fail-first で固定される | planned |
| .2 | `generate_stale_patch()` 実装 | diff / recent skip / no-pair の 3 条件が helper で判定できる | planned |
| .3 | review / 回帰検証 | pytest 29/29 PASS / py_compile PASS / plan lint PASS / settings 差分 0 | planned |

## §4 受入条件

- `generate_stale_patch("L4", project_root=..., since_days=30)` は `docs/plans/L9/L9-*plan.md` の stale PLAN だけを返す
- `unified_diff` は `---` / `+++` / `@@` を含み、`revised` 更新差分を表現する
- 返却要素の `before_revised` は既存 `revised` がない場合 `None`、`after_revised` は当日 ISO 日付
- 当日または cutoff 以内の PLAN は結果に含めない
- `get_pair(layer) is None` の layer は空 list を返す
- 既存 26 vmodel pytest と doctor baseline 25/0/105 を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/vmodel_pair_freeze.py`
- `python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -q`
- `grep -c 'generate_stale_patch' cli/lib/vmodel_pair_freeze.py cli/lib/tests/test_vmodel_pair_freeze.py`
- `helix plan lint docs/plans/L7/L7-vmodel-pair-freeze-skeleton-patchplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- generated patch を `helix doctor` や review queue に接続する workflow は別 PLAN
- `revised` 欠損時の patch preview を本文 skeleton 補完まで拡張する機能は別 PLAN
