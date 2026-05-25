---
plan_id: L7-test-design-scaffold-output-formatplan
title: "L7-test-design-scaffold-output-formatplan: output_dir and JSON export"
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
    - docs/plans/L7/L7-test-design-scaffoldplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — output_dir / JSON export 実装"
  - role: qa
    slot_label: "QA — pytest / bats / plan lint / settings diff 検証"
generates:
  - artifact_path: docs/plans/L7/L7-test-design-scaffold-output-formatplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/test_design_scaffold.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_test_design_scaffold.py
    artifact_type: test
  - artifact_path: cli/helix-test-design-scaffold
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-test-design-scaffold.bats
    artifact_type: bats
---

## §0 PLAN concept

`write_scaffold()` の出力先制御を `output_path` 優先のまま拡張し、`output_dir` 指定時の自動ファイル生成と `--json` による JSON skeleton export を追加する。

## §1 背景

- 現状は apply 時の出力先が既定ディレクトリか `output_path` に固定され、任意の出力ディレクトリへまとめて生成できない
- scaffold 内容は Markdown 固定で、後段ツールが機械的に扱える JSON export がない
- W39 では既存 37 pytest / 7 bats の互換を維持しつつ、出力形式だけを追加する

## §2 scope

1. `cli/lib/test_design_scaffold.py`
   - `write_scaffold(..., output_dir=None, as_json=False)` を追加
   - `output_path` 未指定かつ `output_dir` 指定時は `output_dir/TEST-DESIGN-{pair_layer}-auto-{datetime}.md|json` を生成
   - `as_json=True` 時は `{metadata, sections}` 形式で書き出す
2. `cli/lib/tests/test_test_design_scaffold.py`
   - output_dir 書き込み、JSON export、missing directory 作成の pytest 3件を追加
3. `cli/helix-test-design-scaffold`
   - `--output-dir` と `--json` を Python module へ透過する
4. `cli/tests/test-helix-test-design-scaffold.bats`
   - `--json` の smoke test 1件を追加

scope 外:

- 既存 Markdown template の章立て変更
- doctor / auto-apply 連携
- JSON schema の外部公開

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + pytest 3件 + bats 1件追加 | output_dir / JSON export の期待挙動が fail で固定される | draft |
| .2 | `write_scaffold` / CLI 実装 | default 挙動を維持したまま output_dir / JSON export が動作する | draft |
| .3 | 検証 + review | py_compile / pytest / bats / plan lint / settings diff / review が揃う | draft |

## §4 受入条件

- `write_scaffold(..., output_dir=Path(...), output_path=None)` は指定 directory 配下に `TEST-DESIGN-{pair_layer}-auto-*.md` を生成する
- `write_scaffold(..., as_json=True)` は JSON parse 可能な content を返し、`metadata` と `sections` を含む
- `output_dir` が未作成でも apply 時に自動作成される
- `output_path` 指定時は従来どおり `output_dir` より優先される
- `helix-test-design-scaffold --layer L4 --json` は JSON content preview を返す
- 既存 37 pytest / 7 bats と doctor baseline を壊さない

## §5 検証

- `git status --short`
- `python3 -m py_compile cli/lib/test_design_scaffold.py`
- `python3 -m pytest cli/lib/tests/test_test_design_scaffold.py -v`
- `bats cli/tests/test-helix-test-design-scaffold.bats`
- `grep -c 'output_dir\\|as_json' cli/lib/test_design_scaffold.py`
- `helix plan lint docs/plans/L7/L7-test-design-scaffold-output-formatplan.md`
- `git diff --stat .claude/settings.json`
- `helix review --uncommitted`
