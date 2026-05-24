---
plan_id: L7-codex-allowed-files-regression-fixplan
title: "L7-codex-allowed-files-regression-fixplan: codex allowed-files post-validation regression fix"
kind: troubleshoot
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: SE
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-test-failures-triageplan.md
pairs_test_design:
  - cli/tests/test_helix_codex_allowed_files.bats
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM advisor - release blocker scope and close criteria confirmation"
  - role: tl-advisor
    slot_label: "TL advisor - fail-close contract drift review"
  - role: se
    slot_label: "SE - allowed-files regression fix owner"
  - role: qa
    slot_label: "QA - bats and non-regression verification"
  - role: security
    slot_label: "Security - fail-close boundary preservation review"
generates:
  - artifact_path: docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/tests/test_helix_codex_allowed_files.bats
    artifact_type: test
dependencies:
  parent: L7-test-failures-triageplan
  requires:
    - docs/plans/L7/L7-test-failures-triageplan.md
  blocks: []
related_docs:
  - docs/plans/L7/L7-test-failures-triageplan.md
  - cli/tests/test_helix_codex_allowed_files.bats
  - cli/helix-codex
  - cli/lib/codex_post_validation.py
---

## §1 背景

- triage SoT (`docs/plans/L7/L7-test-failures-triageplan.md` §4 D, §5) で本件は P0 / release blocker と判定された
- `cli/helix-codex` は `--allowed-files` 指定時に post-validation を実行し、許可外の new/modified file を fail-close する
- 既存 bats は一部ケースで `status=0` を期待しており、現行契約と drift している

## §2 scope

- `cli/tests/test_helix_codex_allowed_files.bats` の期待値を fail-close 契約へ合わせる
- `different plan` / `no plan-id` / `stale pid` / `forged baseline` / `symlink baseline` / `new file` の 6 case で status non-zero と violation message を期待する
- `same plan positive auto-detect` と `baseline existing untracked file touch is ignored` は既存の success 契約を維持する

scope 外:

- `cli/lib/codex_post_validation.py` の許可外変更検出 logic の緩和
- `cli/helix-codex` の auto-detect trust boundary 変更
- 他の P1/P2 triage follow-up 修正

## §3 DoD

- 新規 PLAN が起票され、最終 status が `completed` である
- `bats cli/tests/test_helix_codex_allowed_files.bats` が PASS する
- fail-close 契約は実装側で維持される
- `bash -n` / `helix plan lint` / `helix doctor` を実行し、結果を記録する
- 9 mode E2E と route_engine 4 mode 接続の既存回帰確認を実施する

## §4 実装方針

1. triage SoT と `cli/lib/codex_post_validation.py` を再読して fail-close 契約を確認する
2. bats helper の status 判定を `0` / `nonzero` の両方に対応させる
3. drift している 6 case を non-zero + violation message 期待へ更新する
4. 実装側 (`cli/helix-codex`, `cli/lib/codex_post_validation.py`) は証跡確認のみとし、変更しない
5. 検証完了後に PLAN status を `completed` へ更新する

## §5 成果物

- `docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md`
- `cli/tests/test_helix_codex_allowed_files.bats`

## §6 検証コマンド

```bash
bash -n cli/tests/test_helix_codex_allowed_files.bats
bats cli/tests/test_helix_codex_allowed_files.bats
grep -n 'fail-close|fail_close|requires_human_approval' cli/lib/codex_post_validation.py
helix plan lint docs/plans/L7/L7-codex-allowed-files-regression-fixplan.md
helix doctor
```
