# HELIX Feature / Document Alignment Audit

> Status: Active
> Date: 2026-05-03
> Scope: HELIX CLI 51 commands, public command docs, README, active validation rules

この監査は、実装済み機能が公開ドキュメントと一致しているかを機能単位で確認した記録である。

判定基準:

- `cli/helix` dispatcher に command が routing されている
- `cli/helix-<command>` 実体が存在する
- `helix <command> --help` が exit 0 で usage を返す
- [docs/commands/index.md](../commands/index.md) と [README.md](../../README.md) に公開入口が載っている
- 主要機能は個別 docs または領域別 docs に説明がある

## Summary

| 領域 | Commands | Result |
|------|----------|--------|
| HELIX 全体管理 | 11 | pass |
| HELIX プロジェクト管理 | 14 | pass |
| Codex / Claude Code 管理 harness | 10 | pass |
| Reverse / Scrum / 検証 | 4 | pass |
| 学習・再利用 | 8 | pass |
| 補助・運用 | 4 | pass |

## 修正済みのズレ

| ID | 対象 | 内容 | 対応 |
|----|------|------|------|
| FDA-001 | help usage | `helix-size`, `helix-sprint`, `helix-pr`, `helix-reverse` が公開入口ではなく内部スクリプト名を表示していた | `helix size`, `helix sprint`, `helix pr`, `helix reverse` に修正 |
| FDA-002 | reverse help | `--dry-run` 説明が `helix-codex` 表記だった | `helix codex` に修正 |
| FDA-003 | recipe help | `helix-learn/promote/discover 相当` 表記が旧入口を強調していた | `helix recipe learn/promote/discover` に修正 |
| FDA-004 | SessionStart hook | 追加 context が `~/ai-dev-kit-vscode/cli/helix-*` を案内していた | 公開入口 `helix <command>` に修正 |
| FDA-005 | gate / task / drift-check output | 実行メッセージが `helix-codex` / `helix-gate-api-check` を案内していた | `helix codex` / `helix gate-api-check` に修正 |

## 機能別チェック

### HELIX 全体管理

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix init` | `cli/helix-init` | pass | README + command index | pass |
| `helix status` | `cli/helix-status` | pass | README + command index | pass |
| `helix dashboard` | `cli/helix-dashboard` | pass | [dashboard.md](../commands/dashboard.md) | pass |
| `helix mode` | `cli/helix-mode` | pass | README + command index | pass |
| `helix doctor` | `cli/helix-doctor` | pass | README + command index | pass |
| `helix migrate` | `cli/helix-migrate` | pass | README + command index | pass |
| `helix setup` | `cli/helix-setup` | pass | README + command index | pass |
| `helix test` | `cli/helix-test` | pass | README + command index | pass |
| `helix test-debug` | `cli/helix-test-debug` | pass | README + command index | pass |
| `helix debug` | `cli/helix-debug` | pass | README + command index | pass |
| `helix bench` | `cli/helix-bench` | pass | README + command index | pass |

### HELIX プロジェクト管理

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix size` | `cli/helix-size` | pass | [plan.md](../commands/plan.md) + README + command index | pass |
| `helix plan` | `cli/helix-plan` | pass | [plan.md](../commands/plan.md) | pass |
| `helix matrix` | `cli/helix-matrix` | pass | [matrix.md](../commands/matrix.md) | pass |
| `helix gate` | `cli/helix-gate` | pass | README + command index | pass |
| `helix gate-api-check` | `cli/helix-gate-api-check` / `cli/libexec/helix-gate-api-check` | pass | README + command index | pass |
| `helix readiness` | `cli/helix-readiness` | pass | README + command index | pass |
| `helix sprint` | `cli/helix-sprint` | pass | README + command index | pass |
| `helix task` | `cli/helix-task` | pass | README + command index | pass |
| `helix interrupt` | `cli/helix-interrupt` | pass | [interrupt.md](../commands/interrupt.md) | pass |
| `helix handover` | `cli/helix-handover` | pass | [ai-harness.md](../commands/ai-harness.md) + command index | pass |
| `helix pr` | `cli/helix-pr` | pass | README + command index | pass |
| `helix retro` | `cli/helix-retro` | pass | README + command index | pass |
| `helix debt` | `cli/helix-debt` | pass | README + command index | pass |
| `helix drift-check` | `cli/helix-drift-check` | pass | README + command index | pass |

### Codex / Claude Code 管理 Harness

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix codex` | `cli/helix-codex` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix claude` | `cli/helix-claude` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix team` | `cli/helix-team` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix review` | `cli/helix-review` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix skill` | `cli/helix-skill` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix budget` | `cli/helix-budget` | pass | [ai-harness.md](../commands/ai-harness.md) + feature docs | pass |
| `helix hook` | `cli/helix-hook` / `cli/libexec/helix-hook` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix check-claudemd` | `cli/helix-check-claudemd` / `cli/libexec/helix-check-claudemd` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix session-start` | `cli/helix-session-start` / `cli/libexec/helix-session-start` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |
| `helix session-summary` | `cli/helix-session-summary` | pass | [ai-harness.md](../commands/ai-harness.md) | pass |

### Reverse / Scrum / 検証

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix reverse` | `cli/helix-reverse` | pass | [reverse.md](../commands/reverse.md) | pass |
| `helix scrum` | `cli/helix-scrum` | pass | [scrum.md](../commands/scrum.md) | pass |
| `helix verify-all` | `cli/helix-verify-all` | pass | README + command index | pass |
| `helix verify-agent` | `cli/helix-verify-agent` | pass | README + command index | pass |

### 学習・再利用

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix log` | `cli/helix-log` | pass | README + command index | pass |
| `helix recipe` | `cli/helix-recipe` | pass | [learning.md](../commands/learning.md) | pass |
| `helix learn` | `cli/helix-learn` | pass | [learning.md](../commands/learning.md) + command index as deprecated | pass |
| `helix promote` | `cli/helix-promote` | pass | [learning.md](../commands/learning.md) + command index as deprecated | pass |
| `helix discover` | `cli/helix-discover` | pass | [learning.md](../commands/learning.md) + command index as deprecated | pass |
| `helix builder` | `cli/helix-builder` | pass | [builder.md](../commands/builder.md) | pass |
| `helix code` | `cli/helix-code` | pass | README + command index | pass |
| `helix audit` | `cli/helix-audit` | pass | README + command index | pass |

### 補助・運用

| Command | Implementation | Help | Docs | Result |
|---------|----------------|------|------|--------|
| `helix scheduler` | `cli/helix-scheduler` | pass | README + command index | pass |
| `helix job` | `cli/helix-job` | pass | README + command index | pass |
| `helix lock` | `cli/helix-lock` | pass | README + command index | pass |
| `helix observe` | `cli/helix-observe` | pass | README + command index | pass |

## 再発防止

以下を [test-helix-routing.bats](../../cli/tests/test-helix-routing.bats) で固定している。

- dispatcher / top-level help / README / command index の 51 command 一致
- active docs に古い command 名・API fallback 前提が戻らないこと
- `helix/validate.sh` が link / placeholder / deferred backlog を検査すること
- public help が `Usage: helix-*` や `helix-codex --role` を出さないこと
