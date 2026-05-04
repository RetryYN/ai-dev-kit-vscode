# HELIX Intentional Deferred Backlog

> Status: Active
> Owner: TL
> Last reviewed: 2026-05-03

この文書は、HELIX の設計書に残る「未実装」「保留」「段階実装」のうち、現時点で意図的に閉じないものを集約する正本である。

目的:

- 実装漏れと意図的保留を混同しない
- 外部通信・データ破壊・プロバイダ依存など、人間判断が必要な残件を分離する
- Draft / Proposal の文書を読むときの現状判定を一箇所で確認できるようにする

## 分類

| Status | 意味 | 扱い |
|--------|------|------|
| deferred | 意図的保留。現時点では実装しない | 実装漏れ扱いにしない |
| staged | 一部実装済み。残りは別 sprint | 現実装の範囲を明記して運用 |
| proposal | 提案段階。正本化前 | PLAN / ADR 化されるまで通常導線に入れない |
| archive-candidate | 古い設計。現行との差分確認が必要 | 更新または archive 移動を検討 |
| archived | 現行正本に supersede 済み | 完了母数から除外し、履歴参照のみ |

## 意図的保留

| ID | 項目 | Status | 理由 | 正本 / 参照 |
|----|------|--------|------|-------------|
| DEF-DB-001 | DB downgrade | deferred | 破壊的・データ損失リスクがあるため、HELIX は up-only migration を基本方針にする | [D-DB-MIGRATION](../design/D-DB-MIGRATION.md) |
| DEF-DB-002 | migration 前の自動 backup | deferred | backup/restore の環境差が大きく、実装時は rehearsal と権限確認が必要 | [D-DB-MIGRATION](../design/D-DB-MIGRATION.md), [budget migration plan](../features/helix-budget-autothinking/D-MIG-PLAN/migration-plan.md) |
| DEF-DB-003 | 他 DB 形式への移行ツール | deferred | PostgreSQL 等への移行はプロジェクト固有判断が必要 | [D-DB-MIGRATION](../design/D-DB-MIGRATION.md) |
| DEF-REC-001 | recipe remote hub | deferred | HELIX 外への配布・取得を伴う外部通信であり、認証・署名・信頼境界の設計が必要 | [D-RECIPE-SPEC](../design/D-RECIPE-SPEC.md) |
| DEF-SEC-001 | 非公式 API opt-in | deferred | provider 非公式 API 利用はセキュリティ・規約・監査判断が必要 | [budget security verification](../features/helix-budget-autothinking/D-SECV/security-verification.md) |
| DEF-MEM-001 | Claude auto memory 反映 | deferred | `MEMORY.md` / `~/.claude/.../memory` は個人・外部状態。repo 内の実装完了条件には含めず、共有可能な事実だけ docs に保存する | [2026-05-04 memory update](../memory/2026-05-04-helix-completion-memory.md) |

## 段階実装

| ID | 項目 | Status | 実装済み範囲 | 残り |
|----|------|--------|--------------|------|
| STG-RES-001 | Codex / Claude Code resilience | staged | `helix claude` dry-run prompt harness、plan/task/role 前提の文書整理 | retry/backoff、代替モデル選択、品質評価の本実装 |
| STG-AUTO-001 | Auto-thinking Phase B | staged | `effort_classifier.py`、`helix codex --auto-thinking`、`helix skill use --auto-thinking`、`helix skill stats --json` | 長期 telemetry による継続的な学習反映 |
| STG-INT-001 | interrupt history/report | staged | ローカル `record.yaml` の件数・種別・分類・直近履歴集計 | 類似パターン検索、自動分類提案 |
| STG-LEARN-001 | Learning Engine refactor | staged | recipe / promote / discover の既存導線 | GAP-037 本体の別 sprint 実装 |
| STG-BUILD-001 | Builder integration | staged | builder command、8 registered builders、基盤 ADR、command docs | project-local overlay の運用受入と長期履歴評価 |
| STG-QUALITY-001 | Quality spec | staged | gate-policy / verification に主要基準を分散実装 | D-QUALITY-SPEC の正本化または archive |

## Proposal / Draft 管理

| 文書 | Status | 次アクション |
|------|--------|--------------|
| [D-RESILIENCE](../design/D-RESILIENCE.md) | staged | GAP-038 残件の sprint 化 |
| [D-BUILDER-INTEGRATION](../design/D-BUILDER-INTEGRATION.md) | staged | ADR-002 / ADR-008 / L2-builder-system との重複整理 |
| [D-LEARNING-REFACTOR](../design/D-LEARNING-REFACTOR.md) | staged | GAP-037 本体の PLAN 化または archive |
| [D-QUALITY-SPEC](../design/D-QUALITY-SPEC.md) | staged | gate-policy / verification へ統合済み範囲をマーキング |
| [PLAN-001 PoC fallback](../plans/PLAN-001-poc-skill.md) | archived | PoC skill 正本に supersede 済み。PLAN-001 は draft のまま履歴参照のみ |

## 運用ルール

- この台帳にある項目は、単独では「実装漏れ」と判定しない。
- `deferred` を実装対象へ移す場合は、PLAN または ADR を作成し、リスク・検証・rollback を明記する。
- 外部通信、認証、PII、ライセンス、データ破壊に関わる項目は人間判断を必須にする。
- 新しい「未実装」表記を active docs に追加する場合は、この台帳へ同時登録する。
