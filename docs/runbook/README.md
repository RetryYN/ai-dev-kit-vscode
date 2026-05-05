# HELIX Runbooks

HELIX framework の運用 runbook 集。各 CLI / 機能の障害対応・復旧手順・点検項目を記録する。

## 構成

| runbook | 対象 | 内容 |
|---|---|---|
| [helix-codex.md](helix-codex.md) | `helix codex` 委譲 | hang / timeout / sandbox エラー対応 |
| [helix-plan.md](helix-plan.md) | `helix plan` lifecycle | draft / review / finalize 失敗対応 |
| [helix-migrate.md](helix-migrate.md) | `helix migrate` テンプレ移行 | dry-run / apply / rollback トラブル |
| [helix-handover.md](helix-handover.md) | Opus ↔ Codex handover | stale 検知 / escalate / resume 復旧 |
| [PLAN-013-runbook.md](PLAN-013-runbook.md) | code-index eligibility taxonomy | 既存 runbook |

## runbook 作成方針

新規機能を実装したら、対応する runbook をここに追加する (helix plan draft で skeleton 自動生成された D-API / D-ARCH と連動)。

各 runbook の最低構成:

1. 概要 (対象 CLI / 機能)
2. 正常系の動作確認手順
3. よくある障害パターンと一次対応
4. ロールバック / リカバリ手順
5. エスカレーション基準
