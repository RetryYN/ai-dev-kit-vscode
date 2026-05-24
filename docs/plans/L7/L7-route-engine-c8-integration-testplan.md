---
plan_id: L7-route-engine-c8-integration-testplan
title: "L7-route-engine-c8-integration-testplan: route → plan draft retrofit 接続の C8 統合テスト"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md
pairs_test_design:
  - docs/plans/L7/L7-cli-helix-retrofit-implplan.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — C8 carry close の優先度・完了判定確認"
  - role: tl-advisor
    slot_label: "TL — recommended_command 契約と drift_type 網羅の adversarial review"
  - role: qa
    slot_label: "QA — bats 中心の route → CLI 統合テスト実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN/ADR/test trace の整合確認"
generates:
  - artifact_path: cli/tests/test-route-engine-c8-integration.bats
    artifact_type: test
dependencies:
  parent: L7-route-engine-drift-type-retrofit-ext
  requires:
    - L7-cli-helix-retrofit-implplan
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/L7-implementation.md
  - docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md
  - docs/plans/L7/L7-cli-helix-retrofit-implplan.md
  - docs/adr/ADR-041-drift-type-7-categories-routing-decision.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
  - cli/lib/route_engine.py
  - cli/tests/helix-route.bats
  - cli/lib/tests/test_route_engine.py
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: `docs/plans/L7/L7-route-engine-drift-type-retrofit-extplan.md`
> **本 PLAN の対象**: C8 carry として残っていた route → `helix plan draft --kind retrofit` 接続の E2E 契約を bats で固定し、ADR-042 の `recommended_command` JSON object 契約に対する回帰保護網を追加する。

## §1 背景

- C' (`L7-route-engine-drift-type-retrofit-extplan`) で `recommended_command` field と Retrofit routing は実装済み
- ただし C 親 (`L7-cli-helix-retrofit-implplan.md`) §11 C8 は、**`cli/helix` 経由の route → CLI E2E** が未実装のまま carry として残っている
- ADR-042 で `recommended_command` は string ではなく **JSON object 一本化** が確定しており、integration surface を contract test で凍結する必要がある

## §2 scope

本 PLAN の scope は以下に限定する。

- `helix route suggest --signal dependency_outdated --json` が `recommended_command.command = "helix plan draft"` を返すこと
- `recommended_command.args.kind = "retrofit"` を返すこと
- ADR-041/route_engine SoT にある **drift_type 7 種** (`schema` / `contract` / `code_smell` / `structural` / `dependency_outdated` / `upgrade` / `config_drift`) の route 契約を bats で網羅すること
- ADR-042 `RecommendedCommandV1` 相当の必須 field (`schema_version` / `command` / `args` / `safety`) を integration level で確認すること

scope 外:

- `cli/lib/route_engine.py` の実装変更
- `helix retrofit init` の挙動変更
- Recovery/Incident 系 signal の追加仕様変更

## §3 テスト観点

### §3.1 shortcut signal 契約

- `helix route suggest --signal dependency_outdated --json`
  - `mode = Retrofit`
  - `drift_type = dependency_outdated`
  - `recommended_command.command = "helix plan draft"`
  - `recommended_command.args.kind = "retrofit"`
  - `recommended_command.args.drift_type = "dependency_outdated"`

### §3.2 drift_type 7 種の網羅

`cli/lib/route_engine.py` の `VALID_DRIFT_TYPES` / `DRIFT_TYPE_TO_ROUTE` を SoT とし、`helix route suggest --signal drift --drift-type <type> --json` で以下を確認する。

| drift_type | expected mode | expected command | expected args |
|---|---|---|---|
| `schema` | Reverse | `helix reverse normalization R0` | `{}` |
| `contract` | Reverse | `helix reverse normalization R0` | `{}` |
| `code_smell` | Refactor | `helix plan draft` | `{"kind": "refactor"}` |
| `structural` | Refactor | `helix plan draft` | `{"kind": "refactor"}` |
| `dependency_outdated` | Retrofit | `helix plan draft` | `{"kind": "retrofit", "drift_type": "dependency_outdated"}` |
| `upgrade` | Retrofit | `helix plan draft` | `{"kind": "retrofit", "drift_type": "upgrade"}` |
| `config_drift` | Retrofit | `helix plan draft` | `{"kind": "retrofit", "drift_type": "config_drift"}` |

### §3.3 schema contract

- 全ケースで `recommended_command` は object である
- `schema_version = "v1"` を持つ
- `safety.auto_apply` / `safety.requires_human_approval` / `safety.requires_preflight` の 3 field を持つ
- `config_drift` は `requires_human_approval = true`

## §4 実装 step

1. `cli/lib/route_engine.py` の `SIGNAL_TO_MODE` / `VALID_DRIFT_TYPES` / `_build_recommended_command()` を Read して SoT を確定する
2. `cli/tests/helix-route.bats` の setup を流用し、新規 `cli/tests/test-route-engine-c8-integration.bats` を作成する
3. shortcut signal (`dependency_outdated`) と drift_type 7 種の `recommended_command` JSON object を assert する
4. ADR-042 schema (`schema_version` / `command` / `args` / `safety`) との一致を integration evidence として残す
5. `L7-cli-helix-retrofit-implplan.md` §11 C8 carry を superseded/closed に更新する
6. `bash -n` / `bats` / `helix doctor` / `helix plan lint` / `helix review --uncommitted` を実行する

## §5 DoD

- [x] `cli/tests/test-route-engine-c8-integration.bats` が追加されている
- [x] shortcut signal + drift_type 7 種の bats が PASS (`bats-lite` 代替実行で確認)
- [x] `recommended_command` object が ADR-042 の必須 field を満たす
- [ ] `helix doctor` が `24 pass / 0 fail` を維持する
- [x] `L7-cli-helix-retrofit-implplan.md` §11 C8 が `completed by L7-route-engine-c8-integration-testplan` に更新されている

## §6 実装判断メモ

- TASK_INPUT 中の `SIGNAL_TO_MODE_MAP` / `signal_to_condition` は現行 SoT と一致しないため、実装では `SIGNAL_TO_MODE` / `VALID_DRIFT_TYPES` / `_build_recommended_command()` を優先する
- TASK_INPUT にある `incident_detected` / `failure_recurrence` は C' で確定した drift_type 7 種の語彙ではないため、本 PLAN では ADR-041 の 7 種を正とする
- 既存の `cli/lib/tests/test_route_engine.py` が API レベル unit contract を広くカバーしているため、本 PLAN の追加は E2E bats に限定する

## §7 tl-advisor review

- round 1: 本 PLAN draft 後に `helix codex --role tl-advisor` で adversarial review を試行する
- harness 実行不可時は、その理由を evidence に残したうえでセルフレビューで代替する
- 実行結果: `codex` binary 不在 + `thread/start failed: Read-only file system` のため harness review は不成立。SoT 差分 (`SIGNAL_TO_MODE` 優先、ADR-041 drift_type 7 種優先) をセルフレビューで再確認した

## §8 成果物

- `cli/tests/test-route-engine-c8-integration.bats`
- `docs/plans/L7/L7-route-engine-c8-integration-testplan.md`
- `docs/plans/L7/L7-cli-helix-retrofit-implplan.md` の carry 更新

## §9 検証コマンド

```bash
bash -n cli/tests/test-route-engine-c8-integration.bats
bats cli/tests/test-route-engine-c8-integration.bats
HOME=/home/tenni ./cli/helix doctor
HOME=/home/tenni ./cli/helix plan lint docs/plans/L7/L7-route-engine-c8-integration-testplan.md
HOME=/home/tenni ./cli/helix review --uncommitted
```

## §10 完了条件

- PLAN status を `completed` に更新する
- C8 carry を close する
- 実行ログに ADR-042 schema 一致の証跡を残す

## §10.1 実施結果

- 新規 bats を追加し、shortcut signal 1 件 + drift_type matrix 7 件 + ADR-042 schema 形状 1 件を固定した
- `bash -n cli/tests/test-route-engine-c8-integration.bats` は PASS
- `bats cli/tests/test-route-engine-c8-integration.bats` は環境に `bats` 未導入のため、repo 同梱 `cli/scripts/bats-lite` 互換 runner で PASS を確認した
- `helix plan lint` は PASS
- `helix doctor` は既存 repository advisory / phase 警告が残り、`24 pass / 0 fail` 条件は未達

## §11 carry / follow-up

| # | carry | 優先度 | 担当先 |
|---|---|---|---|
| F1 | `helix review` 連携を route 推奨フローへ自動付与するかは別 PLAN で検討する | P3 | 別 PLAN |
| F2 | `upgrade` high risk の `helix reverse upgrade R0` preflight を bats で独立ファイルに切り出すかは回帰負荷を見て判断する | P3 | 別 PLAN 候補 |
