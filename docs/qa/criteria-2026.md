# QA Criteria 2026

> 正本: `docs/plans/PLAN-065-qa-strictness.md` §2 軸 E
> 目的: HELIX における QA の合否基準を、計測可能な形で固定する
> 適用範囲: 2026 年版の PLAN、L4 / L6 / G4 / G6 / L8 受入、運用学習まで

## 0. 文書の位置づけ

この文書は QA criteria の正本である。
個別 PLAN の acceptance、テスト設計、回帰 baseline、skip annotation、E2E 定義は、ここに書かれた基準に一致していなければならない。

本書の目的は「テストが通った」という曖昧な状態を避けることにある。
単に実行成功しただけでは十分ではない。
比率、網羅性、回帰の傾向、スキップの正当性、critical path の定義を同時に満たすことを QA 合格とする。

本書は PLAN 単位の個別事情を否定しない。
ただし、個別事情は必ず明文化し、例外は一時的で追跡可能でなければならない。

## 1. 用語

### 1.1 test pyramid

test pyramid とは、Unit / Integration / E2E の 3 層の比率管理を指す。
比率は suite 別件数から算出し、面積や実行時間ではなく件数で扱う。

### 1.2 coverage target

coverage target とは、ファイル単位のカバレッジ目標を指す。
新規ファイル、修正ファイル、core5 の 3 系統で異なる基準を使う。

### 1.3 regression baseline

regression baseline とは、`helix test` 実行時に蓄積される過去結果の基準点である。
PASS / FAIL の遷移と flaky 判定を含めて評価する。

### 1.4 skip discipline

skip discipline とは、skip の理由を自由文にせず、カテゴリ・PLAN・期限を構造化して残す規律である。

### 1.5 E2E critical path

E2E critical path とは、ユーザーが実際に触る主要フロー全体を指す。
CLI の main usage を含む end-to-end の主要経路を、PLAN ごとに明示する。

## 2. QA 原則

### 2.1 仕様と検証を分けない

QA 基準は、仕様書の付録ではない。
受入条件の一部として、計測可能な形で書かれる必要がある。

### 2.2 例外は記録する

例外処理が必要な場合は、理由と期限を記録する。
期限が曖昧な skip は認めない。

### 2.3 失敗は早く止める

曖昧な PASS は認めない。
閾値未達、構造化されていない skip、baseline 退化は早期に止める。

### 2.4 回帰は蓄積として扱う

過去の test baseline は、単なるログではない。
新しい変更が回帰を持ち込んだかどうかを判断する基準である。

### 2.5 E2E は最後ではなく経路である

E2E は「余裕があれば追加するもの」ではない。
critical path は各 PLAN の acceptance に埋め込む。

## 3. test pyramid 比率

### 3.1 目標比率

目標比率は以下とする。

- Unit: 70%
- Integration: 20%
- E2E: 10%

この比率は suite 別件数から算出する。

### 3.2 許容範囲

実運用では以下を許容範囲とする。

- Unit: 60-80%
- Integration: 15-25%
- E2E: 5-15%

許容範囲は「全部が大きく外れていない」ことを確認するためのガードであり、目標の代替ではない。

### 3.3 計測方法

比率は `helix test` の suite 別件数から算出する。
算出式は以下とする。

```text
ratio = suite_count / (unit_count + integration_count + e2e_count)
```

ここで suite_count は各層の件数である。
件数の集計は、同一テストを重複計上しない。
重複定義がある場合は、最も具体的な suite を優先する。

### 3.4 逸脱判定

比率が許容範囲を外れた場合、G4 warning とする。
warning の目的は即失敗ではなく、計画の歪みを可視化することにある。

ただし、3 commit 連続で同一方向の逸脱が続く場合は fail-close とする。
この fail-close は「偶然の偏りではない」と見なすための統制である。

### 3.5 偏りの解釈

Unit 偏重は統合不足の兆候である。
E2E 偏重は保守性低下の兆候である。
Integration 偏重は境界確認の過剰化または unit 不足の兆候である。

## 4. coverage target

### 4.1 新規ファイル

新規ファイルの coverage target は `>=85%` とする。

### 4.2 修正ファイル

修正ファイルは、前回比 0pt 低下禁止とする。
ここでの評価はカバレッジ値の diff を使う。
1pt 未満の端数処理を行う場合でも、低下した扱いを避けるために丸め方向を恣意的に選んではならない。

### 4.3 core5 ファイル

core5 ファイルは `>=80%` を維持する。
この基準は PLAN-013 の維持方針を踏襲する。

### 4.4 計測コマンド

core5 の基準確認には、以下のようなコマンドを使う。

```bash
helix code stats --scope core5 --bucket coverage_eligible --fail-under 80
```

この例は最低ラインの確認であり、実際には対象ファイルごとの内訳確認も行う。

### 4.5 低下時の扱い

修正ファイルで前回比 0pt 未満となった場合、原則として G4 warning とし、継続的な低下があれば fail-close の対象にする。
新規ファイルで 85% を下回る場合は、原則として修正を優先する。

### 4.6 coverage の読み方

coverage は「どれだけ実行したか」ではなく「どれだけ意図した挙動を確認できたか」を示す。
そのため、単純な行数だけでなく、分岐や境界条件の確認が含まれているかを併読する。

## 5. regression baseline 接続

### 5.1 記録必須

全 PLAN 完了時には、`helix.db` の `test_baseline` に記録する。
この要件は PLAN-065 W-2 実装後の運用ルールである。

### 5.2 PASS→FAIL の扱い

G4 では PASS→FAIL を flaky 判定ルールで分類する。
直近 5 件の窓で見て flaky かどうかを判定する。

flaky 判定は、直近 5 件のうち 1 件以上 FAIL がある場合に flaky 候補とする。
ただし、3 連続 FAIL の場合は fail-close とする。

### 5.3 G4 失敗条件

次のいずれかに当てはまると fail-close とする。

- 3 連続 FAIL
- flaky ではない PASS→FAIL
- 回帰が再現性を持つ

warning と fail-close は混同しない。
warning は観測継続、fail-close は修正優先である。

### 5.4 baseline diff

baseline diff は以下で確認する。

```bash
helix qa baseline diff --base HEAD~1
```

この diff は、何が改善し、何が悪化したかを確認するために使う。
単なる一覧表示ではなく、回帰判断の入口である。

### 5.5 baseline の扱い

baseline は commit ごとに履歴として残す。
suite、test_name、status、duration、skip_reason を含めて追跡する。
単発の PASS で安心せず、傾向を重視する。

## 6. skip annotation discipline

### 6.1 フォーマット

skip annotation は以下のフォーマットに従う。

```text
HELIX-SKIP: <category> | <PLAN-NNN> | <due_date: 2026-MM-DD>
```

### 6.2 category

許容される category は次の 4 つである。

- env_dependent
- bats_lite_limit
- external_blocker
- migration_pending

### 6.3 期限

due_date は必須である。
期限が 30 日を超えて経過した場合、G6 警告とする。

### 6.4 linter

skip annotation は `cli/lib/skip_annotation_linter.py` で検査する。
この linter は PLAN-065 W-3 実装後の正規チェックである。

### 6.5 移行猶予

既存の 67 件は、PLAN-066 の migration script で対応予定とする。
この猶予は無期限ではない。
移行不能な skip は debt として残し、見える化する。

### 6.6 禁止事項

以下は禁止する。

- 理由が free-text のまま残る skip
- PLAN ID がない skip
- due_date がない skip
- 期限切れを放置したままの skip

## 7. E2E critical path 定義

### 7.1 規則

各 PLAN の acceptance には、`e2e_target` を明示する。
`e2e_target` がない PLAN は、critical path の定義が不足していると見なす。

### 7.2 critical path の定義

critical path は、ユーザーが触る主要フロー全体を意味する。
CLI の end-to-end、特に helix コマンドの main usage を含む。

### 7.3 現状の E2E

現状の E2E テストは bats integration テストである。
これは helix CLI の end-to-end 相当として扱う。

### 7.4 追加 E2E

追加 E2E の実装は、PLAN ごとに acceptance で定義する。
暗黙の E2E 追加は禁止する。
どのフローを守るのか、どの失敗を検知したいのかを明文化する。

### 7.5 受入との関係

L8 受入では、critical path が acceptance と一致していることを確認する。
受入条件が E2E に落ちていない場合、後からの追加ではなく、事前に修正する。

## 8. 性能テスト基準

### 8.1 実施責務

性能テストは perf role が L6 で実施する。
QA は結果の妥当性と閾値設定を確認する。

### 8.2 閾値

baseline 比で `±5%` 以内を基準とする。
baseline がない場合は、まず baseline を作成する。

### 8.3 判定

baseline を超える悪化が継続する場合は、性能回帰として扱う。
一時的な揺れと継続劣化は分けて扱う。

### 8.4 記録

性能テストの結果は、対象 PLAN の acceptance に紐づく形で残す。

## 9. セキュリティテスト基準

### 9.1 実施責務

セキュリティテストは security role が G2 / G4 / G6 の 3 段階で実施する。

### 9.2 3 段階

- G2: 設計段階の脅威と境界確認
- G4: 実装後の脆弱性・誤用確認
- G6: RC 前の総合確認

### 9.3 PLAN-066 との関係

詳細な security criteria は PLAN-066 候補で拡張する。
この文書では、3 段階で確認する原則を固定する。

### 9.4 例外

認証、認可、個人情報、ライセンスに触れる場合は、自己判断を避ける。
必要なら人間確認へ戻す。

## 10. QA ゲート早見表

### 10.1 G1

- 要件に test acceptance があるか
- PLAN に `e2e_target` があるか
- 主要フローが不明瞭でないか

### 10.2 G2

- test pyramid の目標比率が見えるか
- coverage target があるか
- security 3 段階の前提があるか

### 10.3 G3

- baseline 接続が明示されているか
- skip discipline が定義されているか
- acceptance が検証可能か

### 10.4 G4

- Unit / Integration / E2E の比率が許容範囲か
- coverage が維持されているか
- baseline 退化がないか
- skip annotation が構造化されているか

### 10.5 G6

- RC 前の総合確認が終わっているか
- performance / security / E2E の総合結果が揃っているか
- 長期化した skip がないか

## 11. 違反時のエスカレーション

### 11.1 即時停止条件

次の条件に当てはまるときは、作業を止める。

- test pyramid が著しく逸脱している
- coverage 低下が継続している
- regression baseline で 3 連続 FAIL が出ている
- skip annotation が不正
- critical path が未定義

### 11.2 報告内容

停止時には、次を簡潔に報告する。

- 何が違反したか
- どの基準に対して逸脱したか
- どの PLAN / どの acceptance に影響するか
- どのゲートで止めるべきか

### 11.3 修正順序

修正は、影響の大きいものから順に行う。
まず acceptance と baseline を合わせ、その後に個別テストの修正を行う。

### 11.4 再開条件

再開するには、違反箇所が再計測可能な形で修正されている必要がある。
口頭説明だけでは再開しない。

## 12. PLAN への落とし込み

### 12.1 acceptance に書くこと

各 PLAN の acceptance には少なくとも次を入れる。

- test_pyramid
- coverage_target
- regression_baseline
- skip_discipline
- e2e_target

### 12.2 個別調整

個別 PLAN の事情で数値を変える場合は、理由を明記する。
ただし、基準を弱めるだけの変更は認めない。

### 12.3 複数 PLAN の比較

複数 PLAN を比較するときは、同じ算出ルールを使う。
算出ルールが違うと比較できない。

## 13. 運用ルール

### 13.1 レビュー前

レビュー前に、QA criteria が acceptance に反映されていることを確認する。
ズレがあれば、レビューに出さずに戻す。

### 13.2 実装中

実装中は、テスト追加を後回しにしない。
先に実装し、最後にテストを書く運用は、回帰を見逃しやすい。

### 13.3 完了時

完了時は、比率、coverage、baseline、skip、E2E の 5 軸を揃える。
1 軸でも欠けた場合、QA 完了とは言わない。

## 14. 監査ポイント

### 14.1 監査対象

監査では次を確認する。

- acceptance に `e2e_target` があるか
- 仕様上の test pyramid と実測が一致するか
- coverage target が新規 / 修正 / core5 で分かれているか
- baseline が記録されているか
- skip annotation が構造化されているか

### 14.2 監査の合否

監査で基準に合わないものは、個別の例外を除き不合格とする。
例外は次回までの改善計画と対にして扱う。

## 15. まとめ

QA criteria は、テストの有無を問うだけの文書ではない。
どの比率で、どの基準で、どの回帰を止めるかを固定するための文書である。

この基準に従わない場合、PASS 表示は信頼できない。
したがって、各 PLAN は acceptance に QA 条件を埋め込み、実行結果を baseline と照合し、skip を構造化し、critical path を明示すること。

## 16. 参照

- `docs/plans/PLAN-065-qa-strictness.md`
- `cli/templates/plan/acceptance.yaml`
- `cli/lib/skip_annotation_linter.py`
- `cli/lib/helix_db.py`
- `docs/architecture/plan-template.md`

