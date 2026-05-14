# helix gate

## 概要

`helix gate` は段階ゲート判定（G0.5 / G1 / ... / G11）を実行するコマンドです。

本ドキュメントは `--subgate functional_freeze` と `--drive` 指定の挙動を定義します。
`helix vmodel` の設計セマンティクス（`docs/v2/B-design/vmodel-semantics-spec.md`）と
`helix_db` の `design_sprint_entries` の実装状態を参照します。

既存の `gatemap` は `docs/commands/asset.md`・`docs/commands/matrix.md`・
`docs/commands/plan.md` の文脈を参照してください。

## サブゲート: `functional_freeze`

```text
helix gate --subgate functional_freeze --plan-id <PLAN> --drive <be|fe|db|fullstack> [--size <S|M|L|XL>]
```

`functional_freeze` は機能フリーズ時点での設計トラック整備状況を判断するゲートです。

- 判定対象: `design_sprint_entries`（`sprint_type='functional'`, `layer='functional'`, `drive` 条件）
- 判定元: vmodel pair と code/test 関係（`helix_db.query_functional_freeze_status`）
- 依存入力: `contract_entries` / `design_sprint_entries` / `design_sprint_artifact_links` / `vmodel semantics`

### 実行前提

- `--plan-id` は必須。
- `--drive` は必須。
- `--subgate functional_freeze` は `--plan-id` と同時指定が必要。
- `--size L` の場合は `--drive` 未指定でも拒否ではなく、強制として実行されます。
- `--size` が `S/M` で `drive in (fe,fullstack,db)` の場合のみ、フローが厳格化されます。
- 不正な `drive` または未対応ゲートは入力エラー（exit code=2）で終了します。

## オプション

| オプション | 必須 | 説明 |
| --- | --- | --- |
| `--subgate functional_freeze` | △ | 本節で扱うサブゲート。\n\t未指定時は通常ゲート（`G`段階）へ戻る |
| `--drive <string>` | ◯ | `be`, `fe`, `db`, `fullstack` のいずれか |
| `--plan-id <string>` | ◯ | 判定対象の plan id |
| `--size <string>` | × | `L` の場合は drive ルールを補強 |
| `--json` | × | 追加で JSON 断片を付与（実装依存） |

## 判定ルール

### 1) 入力検証

以下を満たさない場合は `exit code: 2` で失敗します。

- `subgate` が `functional_freeze` に未対応の文字列
- `drive` 不在／未定義
- `plan-id` 未指定
- `size` / `state` 組合せで本ロジックに矛盾（実装上のチェック）

### 2) 判定収束

`helix_db.query_functional_freeze_status(plan_id, drive)` の返却を使って以下を判定:

- `pair_count` と `failed_count` を算出
- 判定が不十分なら `missing`
- `failed_count > 0` は `failed`
- いずれも問題なければ `passed`

### 3) ドライブ別強制

- `size=L` の場合: 全 drive 対象で実施。\n  ※従来の size 判定より広い範囲を要求。\n
- size in `S/M` でも `drive in {fe, fullstack, db}` の場合は `functional_freeze` が強制される。\n
- `drive=be` は条件次第で任意実行。\n
## 結果モデル

### `verdict` の3値

- `passed`: 対象条件を満たす。\n
- `failed`: 閾値・条件不足または対となる pair の不一致。\n
- `missing`: 対象レコード不足。\n
### 結果コード

`functional_freeze` はコマンドレベルで以下の終了コードを返却します。\n
| Exit code | 意味 | `verdict` |\n+| --- | --- | --- |\n+| `0` | 合格 | `passed` |\n+| `1` | 不合格（失敗） | `failed` |\n+| `2` | 入力エラー | `missing` |\n+\n+## 出力例

### 合格

```text
$ helix gate --subgate functional_freeze --plan-id P-001 --drive be --size L
[warn] [functional_freeze] check starting...
plan_id=P-001 drive=be
pair_count=18 failed_count=0
verdict: passed
severity: ok
```

### 失敗

```text
$ helix gate --subgate functional_freeze --plan-id P-001 --drive fe
[warn] [functional_freeze] check starting...
plan_id=P-001 drive=fe
pair_count=12 failed_count=3
verdict: failed
fail_reasons:
  - pair be/functional/pair/foo: pair_status=failed
  - pair fe/functional/pair/bar: pair_status=failed
severity: fail
```
\n
### 不足

```text
$ helix gate --subgate functional_freeze --plan-id P-999 --drive db --size M
[warn] [functional_freeze] check starting...
plan_id=P-999 drive=db
pair_count=0 missing_count=5
verdict: missing
severity: fail
```

### JSON 付き

```json
{
  "plan_id": "P-001",
  "subgate": "functional_freeze",
  "drive": "fe",
  "verdict": "passed",
  "pair_count": 18,
  "failed_count": 0,
  "missing_count": 0
}
```

## 設定値連携

以下の要素が判定に使われます。

- `helix_db` の `design_sprint_entries`:
  - `sprint_type='functional'`
  - `layer='functional'`
  - `drive=<be|fe|db|fullstack>`
  - `pair_status in {'pending','design_only','test_only','paired','waived','failed'}`
- `vmodel` semantics の pair 定義:
  - `drive` / `layer` が実装と齟齬なし\n
  - `promotion` と `horizontal_rule` による設計順序
- `design_sprint_artifact_links`: 関連 artifact を監査する際に参照される補助情報

## G0.5〜G11 との比較

本サブゲートは、通常の `G3` フロー中で `subgate` の追加判定を担います。\n
- G0.5: 方針/開始判定（事前定義）\n
- G1〜G2: 主要レビュー準備\n
- **G3: 実装前検査**\n
  `functional_freeze` はここでの適合性を厳密化する。\n
- G4以降: 進捗・品質報告に移行。`functional_freeze` の結果は監査トレイルとして残る。\n
\n+`--subgate functional_freeze` で最も重要なのは、design/test pair が実設計と一致しているかです。\n\n
## 利用導線例

### 通常導線

```bash
helix vmodel validate
helix vmodel list --drive fe
helix vmodel show fe/functional/pair/xyz --drive fe
helix gate --subgate functional_freeze --plan-id P-001 --drive fe
```

### CI への組み込み

```bash
for d in be fe db fullstack; do
  helix gate --subgate functional_freeze --plan-id \"$PLAN_ID\" --drive \"$d\" || exit 1
done
```

CI では `exit code` でブロック条件を制御します。\n`2` は入力定義ミスであり、実装バグではなく事前整備不足として扱うことが推奨されます。

## トラブルシューティング
\n
### `verdict: missing` が常時返る\n+- 入力 `plan-id` が未生成、または `functional` sprint が未記録。\n- `design_sprint_entries` の `layer='functional'` に対するレコード欠如。\n- `helix_db` の v21 マイグレーション未反映。\n\n
### `verdict: failed` が復帰しない\n+- `pair_status='failed'` が残存。\n- `pair` が `pending` だけで止まっている。\n- vmodel と DB の `drive/layer` 不一致。\n\n
### `exit code 2` が頻発\n+- `--drive` 未指定または不正値。\n- `--subgate` は `functional_freeze` 以外の誤指定。\n- `plan-id` の紐付け誤り。\n\n
## 既知の制約\n+
- `functional_freeze` は現時点で単一 `subgate` として実装。\n
- `--json` のフィールドは実装更新で拡張される可能性あり。\n
- `drives` の拡張（新 drive 追加）は `vmodel` 側の schema 変更が必要。\n
## 参考\n+\n+- `cli/helix-gate`\n+- `cli/lib/helix_db.py`\n+- `docs/v2/B-design/helix-db-v21-spec.md`\n+- `docs/v2/B-design/vmodel-semantics-spec.md`\n+- `docs/commands/index.md`\n+- `docs/commands/asset.md`\n+\n+## 更新履歴\n+\n+- v1.0: HELIX V2 Phase2 の `functional_freeze` 仕様を追記。\n*** End Patch

## 11. 形式仕様（JSON）

`--json` 実装有効時は、判定結果の JSON を標準出力に混在させる実装とします。
`--json` 非対応環境ではテキストのみを返します。

```json
{
  "plan_id": "P-001",
  "subgate": "functional_freeze",
  "drive": "fullstack",
  "verdict": "failed",
  "pair_count": 14,
  "failed_count": 2,
  "pending_count": 3,
  "waived_count": 1,
  "missing_count": 0,
  "severity": "fail",
  "note": "pair_status=failed at fe/functional/pair/impl_api_contract"
}
```

## 12. リトライ手順（実務）

`functional_freeze` fail が発生した場合は、次順で対応します。

1. `helix vmodel validate` を実行し、構文/参照エラーを先に解消。

2. `helix vmodel show <drive>/<layer>/pair/<key>` で失敗ペアを特定。

3. `helix_db` 側の `design_sprint_entries` を補完。

4. `helix gate --subgate functional_freeze` を再実行。

再試行の際は同一 plan で drive ごとに同一結果が安定するまで反復します。

## 13. 監査観点

`functional_freeze` では単に pass/fail だけでなく、監査として以下を残すことを推奨します。

- 実行時刻

- plan_id / drive / size

- pair_count / failed_count / missing_count / waived_count

- 再実行履歴

- 失敗要因と修正 PR リンク

監査ログを取得する場合は CI で整形済み JSON を保存し、
`gate` 実行時刻と `helix vmodel` 出力の突合を行います。

## 14. よくある質問

### Q. `size=L` でも drive 未指定で実行できる？

A. はい、`L` のときは強制判定対象として動作します。`drive` はあくまで粒度を絞り込む情報です。

### Q. `be` drive のみ失敗した。`fe/fullstack/db` は pass だった場合はどうなる？

A. size や導線ルール次第で build が停止されます。
`size=L` や drive 強制条件を満たす場合は be の fail が全体条件に影響するため、
該当 fail を解消してください。

### Q. 失敗を一時的に回避できるか？

A. `waived` の扱いは一時バイパスではなく監査上の明示的保留として扱います。

## 15. 実例テンプレート（CI）

```bash
#!/usr/bin/env bash
set -euo pipefail

PLANS=("P-001" "P-002")
DRIVES=(be fe db fullstack)

for plan in "${PLANS[@]}"; do
  for drive in "${DRIVES[@]}"; do
    echo "Checking functional_freeze for plan=$plan drive=$drive"
    helix gate --subgate functional_freeze --plan-id "$plan" --drive "$drive"
  done
done
```

CI 上で `set -e` を使っている場合、`exit code 1` と `exit code 2` の双方でジョブが停止します。
必要に応じて `--subgate` 別途実行と `|| exit 1` の分岐を明示します。

## 16. 注意点

- `subgate` 名は現時点で固定です。今後追加時は本書を更新します。
- `--json` を前提にしたログパーサーは、不要フィールド追加に対して寛容にすること。
- `functional_freeze` の実行条件は CLI リリースごとに変化し得るため、
  `docs/commands/index.md` と同時に確認してください。

## 17. 変更履歴

- v1.0: 初版（HELIX V2 Phase2）
