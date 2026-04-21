---
name: helix-scrum
description: 要件未確定・実現可能性不明の案件で仮説検証駆動で開発を進める。S0 (Backlog) → S1 (Sprint Plan) → S2 (PoC) → S3 (Verify) → S4 (Decide) を回し、confirmed 仮説を Forward HELIX L1 要件へ昇格する。PoC・新規事業・技術検証・リサーチ系タスクで使う。
helix_layer: [S0, S1, S2, S3, S4]
codex_role: tl
tier: 1
upstream: helix (ai-dev-kit-vscode/cli/helix-scrum)
---

# HELIX Scrum (仮説検証駆動)

## Overview

通常の HELIX は L1 要件定義から始めるが、要件や成立条件がまだ固まっていない案件では、そのまま Forward に入ると仮定のまま設計と実装が進んでしまう。
このスキルは、S0-S4 の Scrum モードで仮説を backlog 化し、PoC と検証スクリプトで成立可否を判断してから、confirmed 仮説だけを Forward HELIX の L1 要件へ昇格する。
新規事業、技術検証、研究開発、PoC のように「何を作るべきか」自体が未確定な仕事で使う。

## When to Use

- 要件が不確実で、現時点では L1 要件を確定できない
- 実現可能性が不明で、まず仮説検証や技術検証が必要
- PoC、新規事業、技術調査、リサーチ系タスクを進める
- `helix size --uncertain` によって scrum 判定された
- 利用者価値、性能、運用性、技術成立性のいずれかが未検証である
- 先に最小実験を回さないと、設計判断の前提が置けない

**使わないケース**

- 要件がすでに確定している。通常の Forward HELIX を L1 から開始する
- 単純なバグ修正、局所的なリファクタ、明確な保守変更
- 仕様よりも実装修正が主体で、仮説 backlog を作る必要がない
- 既存仕様に対する軽微な改善で、成功条件がすでに定義済みである

## Core Process (S0-S4)

HELIX Scrum は、仮説を「言語化しただけの案」ではなく、反復可能な検証対象として管理する。
各スプリントで対象仮説を選び、PoC と検証スクリプトを作り、実測に基づいて confirmed / rejected / pivot を判断する。
confirmed になった仮説だけが、Forward HELIX へ接続される。

```text
S0 Backlog
  仮説一覧 + 検証質問 + 成功条件を定義
  ↓
S1 Sprint Plan
  スプリントゴールと対象仮説を選定
  ↓
S2 PoC
  最小実装で仮説を試す
  ↓
S3 Verify
  verify/ スクリプトを全実行し、累積回帰を確認
  ↓
S4 Decide
  confirmed / rejected / pivot を裁定
  ↓
Forward HELIX
  confirmed 仮説を L1 要件に昇格
```

進行原則は次の通り。

1. 仮説は backlog に残す。頭の中だけで管理しない
2. 成功条件は acceptance に定量化する
3. PoC は最小実装に限定し、製品実装と混同しない
4. 検証は必ずスクリプト化し、毎回再実行できる形にする
5. decide は雰囲気で行わず、acceptance と実測結果で判断する

## S0: Backlog 構築

S0 の目的は、仮説を backlog として永続化し、「何を確かめるか」と「何をもって成功とするか」を明確にすること。
Scrum モード開始時はまず初期化し、その後に仮説を登録する。

初期化:

```bash
helix scrum init
```

仮説追加:

```bash
helix scrum backlog add --id H001 --title '仮説' --question '検証内容' --acceptance '成功条件'
```

バックログ確認:

```bash
helix scrum backlog list
```

S0 で最低限そろえる項目は次の 3 つ。

- `title`: 仮説の短い宣言
- `question`: 何を検証するのか
- `acceptance`: 何を満たせば成功と判定するのか

S0 完了の目安:
- backlog に仮説が保存されている
- acceptance が定性的な表現ではなく、実測可能な基準で書かれている
- 仮説ごとに検証スクリプトのひな形が生成されている

## S1: Sprint Plan

S1 の目的は、今スプリントで何を明らかにするかを固定すること。
仮説は backlog に蓄積してよいが、1 スプリントですべてを同時に検証しない。

```bash
helix scrum plan --goal 'ゴール' --hypotheses H001,H002
```

このコマンドは次を行う。

- `current_sprint` を更新する
- `.helix/scrum/sprint.yaml` にゴールと仮説一覧を保存する
- 対象仮説の `status` を `testing` に更新する

S1 で決めるべき内容:
- このスプリントで解消したい不確実性は何か
- どの仮説を先に検証すべきか
- 失敗した場合に pivot すべき境界はどこか
- verify スクリプトで観測すべき指標は何か

良い S1 の条件:

- ゴールが「何を学習するか」で書かれている
- 仮説選定に優先順位がある
- 1 スプリントで扱う仮説数が多すぎない
- decide 時の基準が S0/S1 の時点で共有されている

## S2: PoC 実装

S2 の目的は、仮説を検証する最小限のコードと検証スクリプトを用意すること。
ここで作るのは製品版ではなく、acceptance を機械的に確認するための最小の PoC である。

```bash
helix scrum poc --hypothesis H001
```

現行 CLI は PoC 実装を `helix-codex --role pg` に委譲し、対象仮説の `title`、`question`、`acceptance`、および検証スクリプトのパスをプロンプトに渡す。
PoC 実装では、対象仮説だけでなく、既存の `verify/` 配下のスクリプトも全実行する前提で進める。これにより、新しい PoC が以前の検証結果を壊していないかを確認できる。

S2 の責務:
- 仮説を試す最小限のコードを書く
- `verify/*.sh` の形で自動検証を実装する
- acceptance を PASS/FAIL に落とし込む
- 実行可能な状態まで整え、S3 に渡す

S2 で避けること:

- 製品完成度を目指して設計を広げる
- 仮説検証に不要な抽象化を増やす
- 検証不能な手動確認だけで済ませる
- verify スクリプト未実装のまま decide に進む

## S3: Verify

S3 の目的は、累積した検証スクリプトを実行し、対象仮説だけでなく既存の学習資産に対する回帰も検出すること。

```bash
helix scrum verify
```

指定スクリプトのみ実行したい場合:

```bash
helix scrum verify h001-latency.sh
```

特徴:

- 引数なしの `helix scrum verify` は `verify/` 配下の `.sh` を全実行する
- PASS/FAIL と失敗したスクリプト名を出力する
- 蓄積されたスクリプトを毎回全実行するため、回帰検出ができる
- `review` サブコマンドでも内部的に verify が走る

S3 で確認する観点:
- 対象仮説の acceptance を満たしているか
- 以前に confirmed と判断した前提を壊していないか
- 再実行しても同じ結果になるか
- 失敗理由が学習として記録可能な粒度になっているか

## S4: Decide

S4 の目的は、verify の結果をもとに仮説を裁定すること。
裁定は `confirmed`、`rejected`、`pivot` の 3 択で行う。

```bash
helix scrum decide --hypothesis H001 --confirmed
```

```bash
helix scrum decide --hypothesis H001 --rejected --learnings '外部APIの平均応答が 95th 450ms で要件未達'
```

```bash
helix scrum decide --hypothesis H001 --pivot --learnings '検索精度は成立したがコスト条件を満たさないため別案へ切替'
```

現行 CLI の `decide` は仮説 status を更新し、`--learnings` があれば backlog に追記する。
運用上は rejected / pivot の判断理由を `.helix/scrum/decisions/` に別記してもよい。
`confirmed` の場合は Forward HELIX への接続案内が表示され、検証スクリプトはそのまま回帰テストとして残る。

裁定基準:
- `confirmed`: acceptance を満たし、次の設計に使える前提として固定できる
- `rejected`: acceptance 未達で、仮説自体を採用しない
- `pivot`: 学びは得たが、仮説の問いや手段を組み替える必要がある

裁定時の原則:

- 実測と acceptance に基づく
- 感覚的な「いけそう」は根拠にしない
- rejected と pivot も学習として残す
- confirmed した仮説は、後続 L1 の入力として言語化し直す

## Forward HELIX 接続

confirmed 仮説は、探索フェーズの成果として終わらせない。
Forward HELIX の L1 要件へ昇格し、通常の設計と実装フローに接続する。

基本の接続手順:

```bash
helix size --api --db --ui
```

または、案件の性質に合わせて次のように再判定する。

```bash
helix size --type new-feature --ui
```

```bash
helix size --type new-feature --api --db
```

- confirmed 仮説を L1 要件の前提条件に変換する
- 駆動タイプを `fe` / `be` / `fullstack` / `db` / `agent` のいずれかで再判定する
- `helix plan draft` など通常の Forward HELIX の流れへ進む
- `verify/*.sh` は L6 統合検証でも再利用できる学習資産として持ち込む

Forward へつなぐときに必要な整理:
- confirmed した仮説
- rejected した代替案
- pivot が必要だった理由
- verify で使った指標としきい値
- 量産実装に必要な追加設計項目

## 仮説 (Hypothesis) の書き方

仮説は、曖昧な思いつきではなく、検証可能な文として書く。
最低限 `H001` 形式の ID、仮説文、検証質問、成功条件をそろえる。

書式:

- `id`: `H001` のような連番
- `title`: 1 行で仮説を表す
- `question`: 何を確かめるのかを明示する
- `acceptance`: 定量条件または明確な合否条件を書く

- 「〇〇は△△できる」
- 「〇〇を使うと△△を満たせる」
- 「△△方式で○○コスト以内に運用できる」

例 1:

```yaml
id: H001
title: "RAG なしでも FAQ 80% を自己解決できる"
question: "直近 200 件の問い合わせで、既存ナレッジ検索のみで一次回答を完結できるか"
acceptance: "200 件中 160 件以上で human escalation 不要"
```

例 2:

```yaml
id: H002
title: "推論キャッシュにより 95th percentile 100ms 未満を維持できる"
question: "実トラフィック相当の負荷で、応答遅延を 95th 100ms 未満に保てるか"
acceptance: "95th percentile < 100ms, error rate < 1%"
```

例 3:

```yaml
id: H003
title: "1 人日以内で OAuth プロバイダ追加を標準化できる"
question: "Google と GitHub の 2 プロバイダを共通アダプタで追加できるか"
acceptance: "2 provider 実装 + 回帰テスト追加を 1 人日以内で完了"
```

悪い仮説の例:

- `title`: "速くなるはず"
- `question`: "たぶんいけるか"
- `acceptance`: "うまくいくこと"

## 検証スクリプト (verify/) の設計

検証スクリプトは HELIX Scrum の中核である。PoC コードだけでは学習資産にならない。
acceptance を機械的に再検証できる `verify/*.sh` を必ず残す。

現行 CLI 実装での配置:

- backlog / sprint / retro: `.helix/scrum/` 配下
- 検証スクリプト: プロジェクト直下 `verify/` 配下

命名規則:

- `<hypothesis-id>-<name>.sh`
- 例: `H001-latency.sh`
- CLI が自動生成する初期名は小文字化される場合があるため、リポジトリ内では一貫した命名規則を維持する

設計ルール:

- 成功は `exit 0`
- 失敗は `exit 1` 以上
- 何度実行しても同じ結果になる冪等性を持たせる
- 外部依存がある場合は前提条件を冒頭コメントに書く
- 1 本あたり 60 秒以内を目安に保つ
- acceptance を PASS/FAIL に直結させる

基本形:

```bash
#!/bin/bash
set -euo pipefail

echo "=== H001: latency ==="

# 例: 計測や API 呼び出し
# 条件を満たしたら exit 0
# 満たさなければ exit 1

exit 0
```

検証スクリプトの品質基準:

- 出力だけで何を測っているか分かる
- 人手解釈に依存しすぎない
- 失敗時に次の改善ポイントが分かる
- 継続的な回帰検出に耐える

## Scrum モード の特徴 (Forward との違い)

Scrum モードは、Forward HELIX の簡略版ではない。探索のための独立した Phase S であり、目的も成果物も異なる。

主な違い:

- Forward HELIX の L1-L8 フェーズ進行は走らない
- `.helix/scrum/` と `verify/` を中心に独立管理する
- ゲート判定ではなく、S4 の `decide` を主軸に進める
- 正式要件ではなく、仮説 backlog を起点にする
- `db` や `agent` のような特殊駆動でも、前段の仮説検証フェーズとして使える

比較表:

| 項目 | HELIX Scrum | Forward HELIX |
|---|---|---|
| 開始条件 | 要件不確実 | 要件確定済み |
| 起点 | 仮説 backlog | L1 要件 |
| 検証方法 | verify/ スクリプトで実験 | フェーズ別レビューとテスト |
| 裁定 | decide | gate |
| 成果物 | confirmed 仮説 + 学習 | 実装可能な仕様と成果物 |
| 終了条件 | Forward へ接続できる前提が固まる | L8 受入まで完了 |

## Common Rationalizations

| 言い訳 | 実態 |
|---|---|
| 「仮説と言っても明らかだから S4 即 confirmed」 | acceptance に照らした実測が必要。検証スクリプトが通って初めて confirmed と言える |
| 「PoC コードはテスト不要」 | HELIX Scrum では `verify/*.sh` がテストそのもの。これがないと decide できない |
| 「rejected 仮説は破棄でよい」 | rejected も学習資産である。なぜ捨てたかを残さないと同じ失敗を繰り返す |
| 「pivot は失敗」 | pivot は探索の正常動作であり、より良い問いに更新するための判断である |
| 「今回は手動確認で十分」 | 再現できない確認は sprint をまたいで再利用できず、回帰検出にも使えない |

## Red Flags

- acceptance 条件が定性的である
- `verify/*.sh` が 1 本もない状態で decide している
- 同一仮説が 3 スプリント以上繰り返されている
- confirmed 仮説が Forward HELIX L1 に昇格されていない
- rejected 仮説の学習が記録されていない
- rejected / pivot の判断理由が `.helix/scrum/decisions/` などに残っていない
- スプリントゴールが「何を学ぶか」ではなく「何を作るか」だけで書かれている
- PoC 実装が大きくなり、本番実装との境界が曖昧になっている

Red Flag が出たときの対応:

1. S0 の仮説定義を見直す
2. acceptance を定量化し直す
3. verify スクリプトを先に補強する
4. pivot か Forward 接続かを再判断する

## Verification

Scrum スキル適用後、次を確認する。

- [ ] `helix scrum init` 済みである
- [ ] S0 で backlog が `.helix/scrum/backlog.yaml` に存在する
- [ ] 各仮説に `title` / `question` / `acceptance` がある
- [ ] `acceptance` が定量的または明確な合否条件である
- [ ] S1 で `.helix/scrum/sprint.yaml` にスプリント情報が保存されている
- [ ] S2 で `verify/*.sh` が実装されている
- [ ] S3 で `helix scrum verify` が PASS している
- [ ] S4 で `confirmed` / `rejected` / `pivot` のいずれかに裁定されている
- [ ] confirmed の場合、Forward HELIX L1 に接続されている
- [ ] rejected または pivot の学習が backlog、retro、または `.helix/scrum/decisions/` に残っている

```bash
helix scrum status
```

```bash
helix scrum review
```

`review` は verify を再実行し、スプリント完了とレトロ生成まで行う。
スプリント単位の学習整理が必要な場合は、decide だけで終えず review まで回す。

## HELIX 連携

HELIX Scrum は、要件が不確実な案件に対する前段モードである。
探索で得た仮説を、そのまま製品実装へ流し込むのではなく、Forward HELIX が扱える設計入力へ変換する。

連携ポイント:

- 発火フェーズ: S0-S4
- 推奨 Codex ロール: `tl` (仮説設計・裁定) / `research` (先行事例調査) / `se` または `pg` (PoC 実装)
- `helix size --uncertain` で scrum 判定できる
- `helix scrum init` で Scrum モードを初期化する
- `helix scrum verify` で累積スクリプトを全実行する
- `confirmed` 仮説は Forward HELIX の L1 要件化に渡す

関連スキル:

- `spec-driven-development`
- `planning-and-task-breakdown`
- `source-driven-development`

接続の考え方:

1. Scrum で confirmed 仮説を得る
2. confirmed 仮説を要求・制約・成功条件へ翻訳する
3. Forward HELIX の L1/L2/L3 に引き渡す
4. `verify/*.sh` を L6 統合検証でも再利用する

このスキルの終了条件は、PoC が終わることではない。
Forward HELIX に安全に接続できるだけの、確定仮説と学習資産がそろうことである。
