---
plan_id: L7-9mode-cli-e2e-verificationplan
title: "L7-9mode-cli-e2e-verificationplan: 9 mode CLI E2E verification bats"
kind: impl
layer: L7
drive: be
status: completed
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "cli/helix (router)"
pairs_test_design:
  - cli/tests/test-helix-9mode-e2e-verification.bats
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 9 mode 一括 E2E の scope 妥当性確認"
  - role: qa
    slot_label: "QA — startup/help/subcommand sanity のテスト設計・実行・品質判定"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN と CLI mode trace の整合確認"
generates:
  - artifact_path: cli/tests/test-helix-9mode-e2e-verification.bats
    artifact_type: test
created: 2026-05-25
revised: 2026-05-25
owner: QA
related_docs:
  - cli/helix
  - cli/helix-mode
  - cli/helix-reverse
  - cli/helix-discovery
  - cli/helix-refactor
  - cli/helix-retrofit
  - cli/helix-recovery
  - cli/helix-scrum-agile
  - cli/helix-incident
  - cli/helix-add-feature
  - cli/tests/_helix-bats-helper.bash
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本コード**: `cli/helix` router と各 `cli/helix-*` mode entrypoint
> **検証 artifact**: `cli/tests/test-helix-9mode-e2e-verification.bats`

本 PLAN は HELIX-workflows V2 の 9 mode CLI について、個別 mode の深い機能テストではなく、router 経由の startup 動作、help 表示、主要 subcommand help の一括 E2E sanity を追加する。

## §1 scope

対象 mode は以下の 9 件:

| mode | router command | 主要 sanity |
|---|---|---|
| Forward | `helix mode` | `--help` / `--drive be --dry-run` |
| Reverse | `helix reverse` | `--help` / `code R0 --help` |
| Discovery | `helix discovery` | `--help` / `init --help` |
| Refactor | `helix refactor` | `--help` / `init --help` |
| Retrofit | `helix retrofit` | `--help` / `init --help` |
| Recovery | `helix recovery` | `help` / `start --help` |
| Scrum | `helix scrum-agile` | `--help` / `init --help` |
| Incident | `helix incident` | `--help` / `detect --help` |
| Add-feature | `helix add-feature` | `--help` / `add-design --help` |

scope 外:

- 各 mode の状態遷移を深く検証すること
- 既存 CLI 実装の変更
- 既存 bats の変更
- 本番環境、外部 API、認証、認可、PII、secret、license に触れる変更

## §2 実装判断

- 既存 `cli/tests/helix-*.bats` は mode 個別の実動作を検証しているため、本 bats は router 経由の薄い E2E に限定する。
- 各 test は isolated temp project を作り、`helix init` 済みの状態で実行する。
- subcommand 名は 2026-05-25 時点の `cli/helix-*` 実装を SoT とし、TASK_INPUT 例より実装を優先する。
- Forward は dedicated `helix forward` command がないため、router SoT の `helix mode` を Forward mode の検証対象にする。

## §3 スプリント

| Step | 内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | router / 9 mode entrypoint / helper / 既存 bats 調査 | subcommand 名と setup pattern が実装側から確定している | completed |
| .2 | 新規 bats 追加 | 9 mode 各 1 test、計 9 test が追加されている | completed |
| .3 | PLAN 起票 | frontmatter が V2 PLAN enum と generates 形式に準拠している | completed |
| .4 | 機械チェック | bash -n / bats / plan lint / doctor が実行される | completed |
| .5 | QA 判定 | 品質 Lv、未検出リスク、G4/G6 pass/fail が summary に残る | completed |

## §4 DoD

- 新規 PLAN が `status: completed` で存在する
- 新規 bats が `cli/tests/test-helix-9mode-e2e-verification.bats` に存在する
- 9 mode 全件の startup/help/subcommand sanity が PASS する
- `helix doctor` の既存 pass/fail 状態を悪化させない
- 既存 bats との overlap は router/help/subcommand sanity に限定される

## §5 検証コマンド

```bash
ls cli/tests/test-helix-9mode-e2e-verification.bats docs/plans/L7/L7-9mode-cli-e2e-verificationplan.md
git status -s cli/tests/test-helix-9mode-e2e-verification.bats
bash -n cli/tests/test-helix-9mode-e2e-verification.bats
bats cli/tests/test-helix-9mode-e2e-verification.bats
helix plan lint docs/plans/L7/L7-9mode-cli-e2e-verificationplan.md
helix doctor
```
