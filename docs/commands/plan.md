# helix plan コマンドガイド

## フロー

`draft -> review -> finalize`

```bash
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001
```

補助コマンド:

```bash
helix plan list
helix plan status --id PLAN-001
```

## Plan Consent

Codex / Claude Code が計画、実装順、整理案をユーザーへ提示した場合、ユーザーの明示承認があるまで実装へ進まない。

- 承認例: `OK`、`進めて`、`実装して`、`それで`、`やって`、`apply`、`proceed`
- 承認前に可能: 読み取り専用の調査、grep、状態確認、テスト実行
- 承認前に不可: ファイル編集、依存追加、外部状態変更、工程表外の作業開始

## 管理ドキュメントテンプレート

| テンプレート | 出力先の目安 | 役割 |
|---|---|---|
| `cli/templates/docs/PLAN.md.template` | `docs/plans/PLAN-XXX-*.md` | PLAN 本文の標準構造 |
| `cli/templates/docs/L3-schedule-wbs.md` | `docs/design/L3-schedule-wbs.md` | G3 用の工程表 / WBS |
| `cli/templates/docs/project-status.md.template` | `docs/status/project-status.md` | phase / plan / sprint / blocker の手動 snapshot |

`helix size` で L3 が対象になると、`L3-detailed-design.md` と `L3-schedule-wbs.md` が `docs/design/` にコピーされる。

工程表には `WBS ID`、担当 role、依存、`L4 Sprint`、`HELIX command / delegation`、受入条件を必ず入れる。実装担当は該当 WBS 行を正として、工程表外の変更が必要になったら先に工程表更新またはユーザー確認へ戻る。

## TL レビューの意味

`review` では TL 観点で以下を判定する。

- 技術妥当性
- リスク（API/DB/認証/外部API/移行/セキュリティ）
- 実装可能性と欠落

判定は `approve` または `needs-attention`。

## なぜ提案前レビューが必要か

- 設計未凍結のまま実装に入るのを防ぐ
- 後戻りコスト（G3 以降のやり直し）を減らす
- 仕様・契約の抜け漏れを先に潰す

`finalize` は `approve` 済みプランのみ許可される。
