# helix scrum 判定管理ガイド

`helix scrum` は要件や実現性が未確定なものを、仮説・PoC・検証スクリプト・判定で管理する検証駆動モードです。Forward HELIX に入る前の不確実性を潰すために使います。

## 入口判定

| 状況 | Scrum に入れる理由 |
|---|---|
| 要件が未確定、成功条件が曖昧 | 先に仮説と acceptance を固定する |
| 技術的にできるか分からない | PoC と verify script で確認する |
| UI / UX の方向性が複数ある | `ui` 系 trigger と PoC で比較する |
| 実装前に新事実が出た | `trigger detect` で差し込み候補化する |
| 本番後に KPI / SLO 逸脱が見つかった | `post-deploy` trigger として扱う |

通常の新規開発で要件・設計・契約が十分明確なら Forward HELIX を使います。既存コードの設計復元が主目的なら Reverse を使います。

## 基本フロー

```bash
helix scrum init
helix scrum backlog add --id H001 --title "仮説" --question "何を検証するか" --acceptance "成功条件"
helix scrum plan --goal "検証ゴール" --hypotheses H001
helix scrum poc --hypothesis H001
helix scrum verify
helix scrum decide --hypothesis H001 --confirmed --strict-promote
helix scrum review
```

検証スクリプトは `verify/` に蓄積され、以後の回帰チェックとして残ります。
`confirmed` と `review` は fail-closed です。`confirmed` は対象 hypothesis の verify script が成功しない限り通らず、`review` は `helix scrum verify` 失敗時に sprint を completed にしません。例外的に人間判断で進める場合だけ `--force` / `--force-complete` を使います。

## Hypothesis 判定

| status | 意味 | 次アクション |
|---|---|---|
| `queued` | backlog にあるが未着手 | `plan` で sprint に入れる |
| `testing` | 現在検証中 | `poc` と `verify` を実行 |
| `confirmed` | acceptance を満たした | handoff、Forward task、promotion plan draft で Forward へ接続 |
| `rejected` | 仮説が成立しない | backlog から外し、学びを記録 |
| `pivot` | 仮説を修正して再検証 | 新しい仮説として次 sprint へ |

`--strict-promote` は confirmed 時に追加の昇格推奨チェックを出します。verify script の成功は `--strict-promote` の有無に関係なく必須です。未検証のまま例外的に進める場合は `helix scrum decide --hypothesis H001 --confirmed --force` とし、出力された warning を handoff / plan に残します。

confirmed 時は `.helix/scrum-handoff.md`、`.helix/tasks/scrum-<HID>-forward.md`、`helix plan draft` の promotion plan を生成し、backlog の `promotion_plan_id` に記録します。

## Trigger 判定

Scrum trigger は、文書・review JSON・`.helix/scrum/` から不確実性や新事実を検出します。

```bash
helix scrum trigger detect --scan docs/features --save
helix scrum trigger list --status pending
helix scrum trigger evaluate --id ST-2026-05-03-0001
helix scrum trigger transition --id ST-2026-05-03-0001 --status triaged --owner tl --reason "次 sprint で検証"
helix scrum trigger transition --id ST-2026-05-03-0001 --status adopted --owner tl --reason "backlog 化"
helix scrum trigger ttl --apply
```

### Trigger status

| status | 意味 | 許可される主な遷移 |
|---|---|---|
| `pending` | 検出直後 | `triaged`, `archived` |
| `triaged` | 検証対象として整理済み | `adopted`, `rejected`, `archived` |
| `adopted` | Scrum backlog / sprint に採用 | `archived` |
| `rejected` | 採用しない | `archived` |
| `archived` | 完了・期限切れ・保管 | なし |

### 4 象限評価

`trigger evaluate` は uncertainty と impact で優先度を決めます。

| quadrant | 推奨 |
|---|---|
| `high/high` | sprint。post / deploy / SLO / 監視系なら post-deploy |
| `low/high` | sprint。UI / UX / a11y 系なら ui |
| `high/low` | unit |
| `low/low` | unit。UI 文脈なら ui |

`eligible=true` は high uncertainty + high impact、または evidence_count が 3 以上の場合です。priority_score は impact 0.6 + uncertainty 0.4 で計算されます。

`transition --status adopted` は既定で `.helix/scrum/backlog.yaml` に trigger 由来の hypothesis を作成します。状態だけを変えたい場合は `--no-backlog` を指定します。

## Forward 接続

`confirmed` にすると `.helix/scrum-handoff.md`、`.helix/tasks/scrum-<HID>-forward.md`、promotion plan draft が生成されます。

```bash
helix size --type new-feature --ui --api
helix plan draft --title "Confirmed hypothesis H001 productionization"
```

Forward に接続するときは、PoC をそのまま本実装扱いにせず、L1/L2/L3 で要件・設計・契約へ昇格させます。verify script は L6 の回帰検証にも残します。

## 使い分け

| 判断 | 使う |
|---|---|
| 「既存コードが何をしているか分からない」 | `helix reverse` |
| 「作るものは明確、実装するだけ」 | Forward HELIX |
| 「そもそも成立するか分からない」 | `helix scrum` |
| 「実装中に設計ギャップが見つかった」 | `helix interrupt` |
| 「検証済み仮説を本番化する」 | Scrum confirmed → Forward HELIX |
