---
plan_id: L7-vmodel-pair-freeze-stale-suggestionplan
title: "L7-vmodel-pair-freeze-stale-suggestionplan: stale PLAN revised suggestion dry-run"
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
    - docs/plans/L7/L7-vmodel-pair-freeze-stale-detectionplan.md
    - docs/plans/L7/L7-test-design-scaffold-template-extplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — suggest_stale_revisions helper と doctor hint 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings 差分検証"
generates:
  - artifact_path: docs/plans/L7/L7-vmodel-pair-freeze-stale-suggestionplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/vmodel_pair_freeze.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_pair_freeze.py
    artifact_type: test
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-doctor-pmo.bats
    artifact_type: test
---

## §0 PLAN concept

`check_pair_freeze(..., since_days=N)` で stale と判定された pair PLAN を対象に、`revised` 更新候補を dry-run で提案する `suggest_stale_revisions()` を追加する。`helix doctor --suggest-revisions` は stale 件数の直後に hint を表示するが、実 PLAN file の自動更新や `--apply` 実行までは行わない。

## §1 背景

- `L7-vmodel-pair-freeze-stale-detectionplan` で stale 件数の可視化までは入ったが、次に何を直すべきかは人間が都度判断している
- stale 判定に `revised` frontmatter が使われるため、候補日付を dry-run で並べるだけでも運用判断が速くなる
- `L7-test-design-scaffold-template-extplan` の template 連携方針を踏まえ、将来の revised skeleton 生成へ接続できる形で helper 契約を先に固定する

## §2 scope

1. `cli/lib/vmodel_pair_freeze.py` に `suggest_stale_revisions(layer, *, project_root, since_days=30)` を追加する
2. helper は pair layer の `docs/plans/L{pair}/L{pair}-*plan.md` を走査し、`revised` または `created` が cutoff より古い PLAN を `{plan_id, plan_path, current_revised, suggested_revised}` で返す
3. pair がない layer は空 list を返し、paired doc 不在も空 list とする
4. `cli/helix-doctor` に `--suggest-revisions` flag を追加し、`--vmodel-pair-freeze-since-days N` と併用したときだけ stale 件数の後に suggest hints を表示する
5. pytest 3 件と bats 1 件で dry-run 契約を固定する

scope 外:

- stale PLAN file の自動更新
- `--apply` での frontmatter rewrite
- revised 候補から本文 skeleton を直接生成する高度 template 展開

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3 件 / bats 1 件追加 (Red) | suggestion 契約と doctor flag 契約が test で固定される | planned |
| .2 | `suggest_stale_revisions()` 実装 | old/recent/no-pair の 3 条件が helper で判定できる | planned |
| .3 | `helix doctor --suggest-revisions` 表示追加 + 回帰検証 | pytest 23 件以上 PASS / bats 9 件以上 PASS / plan lint PASS | planned |

## §4 受入条件

- `suggest_stale_revisions("L4", project_root=..., since_days=30)` は `docs/plans/L9/L9-*plan.md` を対象にし、stale PLAN のみ返す
- 返却要素は `plan_id`, `plan_path`, `current_revised`, `suggested_revised` の 4 key を持ち、`suggested_revised` は当日 ISO 日付
- `revised` が当日または cutoff 以内の PLAN は返さない
- `get_pair(layer) is None` の layer は空 list を返す
- `helix doctor --vmodel-pair-freeze-since-days 30 --suggest-revisions` は既存の stale count 行を維持しつつ、提案があるときだけ hint 行を追記する
- 既存 31 pytest / 8 bats と doctor baseline 25/0/105 を破壊しない

## §5 検証

- `python3 -m py_compile cli/lib/vmodel_pair_freeze.py`
- `python3 -m pytest cli/lib/tests/test_vmodel_pair_freeze.py -v`
- `bats cli/tests/test-helix-doctor-pmo.bats`
- `grep -c 'suggest_stale_revisions\\|suggest-revisions' cli/lib/vmodel_pair_freeze.py cli/helix-doctor cli/tests/test-helix-doctor-pmo.bats`
- `helix plan lint docs/plans/L7/L7-vmodel-pair-freeze-stale-suggestionplan.md`
- `git diff --stat .claude/settings.json`

## §11 carry

- `revised` 候補を実 PLAN file へ自動反映する `--apply` 連携は別 PLAN
- suggestion 結果から markdown skeleton を生成して patch 化する機能は別 PLAN
