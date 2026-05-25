---
plan_id: L7-helix-plan-show-content-previewplan
title: "L7-helix-plan-show-content-previewplan: helix plan show に content preview を追加"
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
    - docs/plans/L7/L7-helix-plan-show-subcommandplan.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-plan show の preview 拡張"
  - role: qa
    slot_label: "QA — bats / lint / plan lint / settings 差分確認"
generates:
  - artifact_path: docs/plans/L7/L7-helix-plan-show-content-previewplan.md
    artifact_type: design_doc
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/tests/test-helix-plan.bats
    artifact_type: bats
---

## §0 PLAN concept

`helix plan show <plan-id-or-path> [--content-preview N]` を追加し、frontmatter は維持したまま human-readable 出力に PLAN body の先頭 N 行だけを軽量付加する。`--json` と `--path-only` の既存契約は維持する。

## §1 scope

1. `cli/helix-plan` の `show` に `--content-preview N` を追加する
2. human-readable 出力時のみ frontmatter の後ろに body preview を表示する
3. `N` 未指定または `0` は frontmatter のみを返す
4. `--json` と `--content-preview` は排他にする
5. bats 1 件を追加し、既存 `helix plan` 系テストを壊さない

## §2 受入条件

- `helix plan show <plan-id-or-path> --content-preview 5` で frontmatter の後に body 先頭 5 行が表示される
- `helix plan show ... --content-preview 0` は既存出力と同じ
- `helix plan show ... --json --content-preview 5` は exit 1 で拒否される
- `helix doctor` と既存 `helix-plan` bats が維持される

## §3 検証

- `git status --short`
- `bash -n cli/helix-plan`
- `bats cli/tests/test-helix-plan.bats`
- `grep -c 'content-preview\\|content_preview' cli/helix-plan cli/tests/test-helix-plan.bats docs/plans/L7/L7-helix-plan-show-content-previewplan.md`
- `helix plan lint docs/plans/L7/L7-helix-plan-show-content-previewplan.md`
- `git diff -- .vscode/settings.json`
