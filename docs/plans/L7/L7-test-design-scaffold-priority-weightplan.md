---
plan_id: L7-test-design-scaffold-priority-weightplan
title: "L7-test-design-scaffold-priority-weightplan: weighted paired design selection"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: HELIX-workflows/helix-process/HELIX-process-L0-L14.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - docs/plans/L7/L7-test-design-scaffold-prefer-kindplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — score_paired_design と weighted auto detect 実装"
  - role: qa
    slot_label: "QA — pytest / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-priority-weightplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
---

## §0 PLAN concept

`prefer_status` と `prefer_kind` の段階 fallback に代えて、`status match=2` と `kind match=1` の重み付け score で paired design 候補を比較できるようにする。`weighted=False` を default に維持し、明示 opt-in 時のみ新ロジックを有効化する。

## §1 背景

- 現状の `auto_detect_paired_design()` は `status+kind` → `status` → `kind` → sorted の固定優先で、best fit の比較軸が限定される
- W26 では helper 化した score 計算で柔軟な選択を導入しつつ、既存 26 pytest を壊さず既定挙動を保持する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `score_paired_design(candidate_frontmatter, *, prefer_status, prefer_kind, status_weight=2, kind_weight=1) -> int` を追加
   - `auto_detect_paired_design(..., weighted=False)` を追加
   - `weighted=True` のときは全候補の score を比較し、最高 score を返す。同点は sorted 最初
2. `cli/lib/tests/test_test_design_scaffold.py`
   - score helper 2件、weighted auto detect 1件の pytest を追加
3. `docs/plans/L7/L7-test-design-scaffold-priority-weightplan.md`
   - W26 の scope / acceptance / verification を記録

scope 外:

- custom weight の CLI 注入
- `weighted=True` を CLI flag で公開する変更
- pair 候補の対話選択 UI

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3件追加 | 追加 test が仕様を固定する | draft |
| .2 | weighted score 実装 | `weighted=False` の既存 fallback を維持 | draft |
| .3 | 検証 + review | py_compile / pytest / plan lint / settings diff / review が揃う | draft |

## §4 受入条件

- `score_paired_design()` は status 一致で `2`、kind 一致で `1`、両一致で `3` を返す
- `auto_detect_paired_design(weighted=True)` は全候補から最高 score を返す
- 同点時は sorted 最初の候補を返す
- `weighted=False` default では既存 fallback chain を維持する
- `helix doctor 25/0/105` baseline を壊す追加変更を入れない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `grep -c 'score_paired_design\\|weighted' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-priority-weightplan.md`
- `git diff --stat .claude/settings.json`
- `helix review --uncommitted`

## §11 carry

- status / kind の custom weight 指定を CLI から受ける機能は別 PLAN で扱う
