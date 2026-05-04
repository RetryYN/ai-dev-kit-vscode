# L3 実装工程表

> G3 通過条件を満たすための WBS / 依存 / feature flag / rollback / L4 Sprint 接続を固定する。

## 0. 前提

| 項目 | 値 |
|------|----|
| plan_id | PLAN-XXX |
| 対象機能 / scope | |
| API Freeze | YYYY-MM-DD / N/A |
| Schema Freeze | YYYY-MM-DD / N/A |
| 対象リリース | |
| 作成日 | YYYY-MM-DD |
| owner | |

## 1. Gate 前提

| 成果物 | パス | 状態 | 備考 |
|--------|------|------|------|
| D-REQ-F | docs/features/.../D-REQ-F/ | pending / ready / N/A | |
| D-REQ-NF | docs/features/.../D-REQ-NF/ | pending / ready / N/A | |
| D-ACC | docs/features/.../D-ACC/ | pending / ready / N/A | |
| D-API | docs/features/.../D-API/ | pending / ready / N/A | |
| D-CONTRACT | docs/features/.../D-CONTRACT/ | pending / ready / N/A | |
| D-DB | docs/features/.../D-DB/ | pending / ready / N/A | |
| D-TEST | docs/features/.../D-TEST/ | pending / ready / N/A | |

## 2. WBS

| WBS ID | タスク | 担当 role | 依存 | 期間 | 環境 | L4 Sprint | HELIX command / delegation | feature flag | rollback | 受入条件 |
|--------|--------|-----------|------|------|------|-----------|----------------------------|--------------|----------|----------|
| WBS-001 | 影響範囲調査 | tl | N/A | 0.5d | local | .1a | `helix code find`; `helix codex --role legacy --read-only` | N/A | N/A | 影響ファイルと既存テストが列挙済み |
| WBS-002 | 変更計画固定 | tl/se | WBS-001 | 0.5d | local | .1b | `helix plan status`; `helix task status`; `helix codex --role tl --read-only` | N/A | N/A | 実装順・依存・テスト方針が確定 |
| WBS-003 | 最小実装 | se/pg | WBS-002 | 1.0d | dev | .2 | `helix codex --role se`; `helix review --uncommitted` | ff_<domain>_<feature> | flag off | 主要 happy path が通る |
| WBS-004 | 安全性・例外処理 | se/security | WBS-003 | 0.5d | dev | .3 | `helix codex --role security`; `helix review --uncommitted` | ff_<domain>_<feature> | flag off | 異常系・権限・入力検証が通る |
| WBS-005 | 検証固定 | qa | WBS-004 | 0.5d | local/ci | .4 | `helix codex --role qa`; project tests | N/A | test baseline restore | unit/integration が通る |
| WBS-006 | 仕上げ・docs sync | docs/tl | WBS-005 | 0.5d | local | .5 | `helix codex --role docs`; `helix review --uncommitted` | N/A | revert docs patch | docs と gate evidence が同期済み |

## 3. L4 Sprint 接続

| Sprint | 目的 | 対象 WBS | 完了条件 |
|--------|------|----------|----------|
| .1a | コード調査 | WBS-001 | 影響範囲、既存テスト、依存が明確 |
| .1b | 変更計画 | WBS-002 | 実装順、担当、受入条件が明確 |
| .2 | 骨格実装 | WBS-003 | 最小動作と flag 配下実装が完了 |
| .3 | 強化実装 | WBS-004 | セキュリティ、互換性、例外処理が完了 |
| .4 | 検証固定 | WBS-005 | テストと合否基準が固定 |
| .5 | 仕上げ | WBS-006 | review、docs、残課題管理が完了 |

## 4. クリティカルパス

```text
WBS-001 -> WBS-002 -> WBS-003 -> WBS-004 -> WBS-005 -> WBS-006
```

## 5. feature flag 定義

| flag | default | scope | rollout | owner | metrics | cleanup deadline |
|------|---------|-------|---------|-------|---------|------------------|
| ff_<domain>_<feature> | false | all / tenant / user | internal -> beta -> all | | error_rate, latency_p95 | YYYY-MM-DD |

flag 不要の場合も、WBS の `feature flag` 列に `N/A` を明記する。

## 6. Rollback Plan

### 発火条件

- エラーレートが既存比で悪化:
- p95 latency が既存比で悪化:
- Sev1 / Sev2:
- 契約テスト失敗:

### 手順

1. feature flag を OFF。
2. 新規 routing / job / UI entrypoint を旧経路へ戻す。
3. DB 変更がある場合は down 可否とデータ整合方針に従う。
4. smoke test と contract test を再実行する。
5. 監視値が復帰したことを確認する。

### 体制

| 役割 | 担当 |
|------|------|
| 実行者 | |
| 承認者 | |
| 連絡先 | |

## 7. リスクと緩和

| リスク | 影響 | 緩和策 | owner | 期限 |
|--------|------|--------|-------|------|
| | high / medium / low | | | |

## 8. G3 チェック

- [ ] 全 WBS に担当 role、依存、期間、環境がある。
- [ ] 全 WBS に L4 Sprint がある。
- [ ] 全 WBS に HELIX command / delegation がある。
- [ ] 全 WBS に feature flag または `N/A` がある。
- [ ] 全 WBS に rollback または `N/A` がある。
- [ ] API / Schema Freeze の状態が明記されている。
- [ ] クリティカルパスと高リスク対策が明記されている。

## 9. TL 実行規律

- Codex / Claude Code はこの WBS の順序、依存、受入条件に従って実装する。
- WBS 外の変更が必要になった場合、実装を止めて工程表を更新するか、ユーザー確認へ戻る。
- ユーザーへ実装計画を提示した場合、明示承認があるまで編集へ進まない。
- 各 WBS 完了時は、実行した HELIX command / delegation とテスト証跡を final または gate evidence に残す。
