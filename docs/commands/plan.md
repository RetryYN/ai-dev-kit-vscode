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

## PLAN の種別と住所（Process / Action / L）

PLAN は性質で分かれる。構造の正本は [plan-model.md](../../HELIX-workflows/helix-process/plan-model.md)（Process ⊃ Action 親子モデル）。

| 種別 | 住所 | `plan_scope` | 役割 |
|---|---|---|---|
| **Forward 工程 PLAN** | `docs/plans/L<NN>/L<NN>-…plan.md` | （強制しない） | V-model 工程。L単位はそれ自体が Process（行程）を兼ねる |
| **Process Plan（親=行程）** | `docs/plans/process/process-YYYY-MM-DD-<topic>plan.md` | `process` | 駆動モデル・工程の連鎖。`forward_return` 必須 |
| **Action Plan（子=実行）** | `docs/plans/<workflow>/<workflow>-YYYY-MM-DD-<topic>plan.md` | `action` | 単一 workflow 内部の収束ループ。`parent_process` 必須 |
| **V1 legacy** | `docs/plans/PLAN-NNN…md` | - | 旧形式。`is_reference: true` 必須、V2 strict 対象外（書き直し前提） |

- **親子規律**: `process ⊃ action[]`（1 段）。Process は Forward へ戻す `forward_return` を必須に持つ（Forward 代替正本にしない）。
- **L単位の内包**: L PLAN の中に派生 workflow が出たら、その Action Plan を `parent_process: docs/plans/L<NN>/…` でぶら下げる（L PLAN 自体に `plan_scope` は付けない）。
- **closure 契約**（`mode_transition` 等）は本起票規約に含めない（closure PoC confirmed 後に別途 L4/L5 凍結）。

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

> 上表の `cli/templates/docs/PLAN.md.template` → `docs/plans/PLAN-XXX-*.md` は **V1 legacy 形式**。新規 PLAN は上記「PLAN の種別と住所」と [plan-model.md](../../HELIX-workflows/helix-process/plan-model.md) に従い、`docs/plans/L<NN>/` ・ `docs/plans/process/` ・ `docs/plans/<workflow>/` 配下へ置く。

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
