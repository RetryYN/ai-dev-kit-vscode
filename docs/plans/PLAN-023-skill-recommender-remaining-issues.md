---
plan_id: PLAN-023
title: "PLAN-023: skill 推挙パイプライン 残課題 3 件解消 (effort 伝搬 + sessions hit_rate + policy 誤判定)"
status: completed
size: M
drive: be
created: 2026-05-06
owner: PM
phases: L1, L2, L3, L4, L6
gates: G2, G3, G4
acceptance:
  - 残課題 1: ADR-007 Option A 確定 + effort field の prompt inject 実装
  - 残課題 2: helix.db v15→v16 migration + sessions 単位の真 hit_rate 計測パイプライン
  - 残課題 3: HELIX policy の research 誤判定 (recommender role policy 不整合) を解消
  - 統合 E2E テスト 15/15 PASS
related:
  - PLAN-022 (本 PLAN の親、3 残課題の元)
  - ADR-007
---

# PLAN-023: skill 推挙パイプライン 残課題 3 件解消

## §1 背景・目的

PLAN-022 により、skill 推挙パイプラインの実装基盤は一気に実運用化された。
ただし本稼働後に次の 3 残課題が残った。

1. Sonnet サブエージェントへ effort 情報を渡しても、意図通りの実行分岐に繋がらない問題
2. hit_rate 計測が `subtask` 粒度ではなくセッション粒度として意味を持っておらず、観測値が実運用 KPI とズレる問題
3. `recommender` ロールと policy 判定の不整合による誤判定問題

この PLAN は、PLAN-022 の 1 セッション実行で 3 件を一括解消するための起票を行う。

### 1.1 依頼元と時系列

本件は、2026-05-06 のリリースサイクルとして PLAN-022 から引き継がれた。

- 2026-05-06（Session 記録上）: PLAN-022 完了
  - helix-codex 経由の運用実行へ移行
  - sessions と skill usage 計測の試験基盤を形成
- 直後の 1 週: 実運用計測で誤差と policy ログの継続出力が観測
- 2026-05-06 以降: PLAN-023 として 5 commit で 3 件を一括解決

### 1.2 3 残課題の具体像

#### 1.2.1 effort 伝搬の未達問題

`helix.skill` による呼び出し文脈で effort を想定していたが、サブエージェント側には意図が十分伝搬しない状態だった。
その結果、Sonnet の振る舞いが一部タスクで期待に対してブレ、推挙精度改善ループが回りにくい状態となった。

#### 1.2.2 sessions 単位 hit_rate の未計測

当初のカウントは実質 `subtask` や断片粒度で加算され、実質セッションごとの利用有効性を反映していなかった。
これにより、`hit_rate` が「実セッションで推挙が効いたか」を直接評価できなかった。

#### 1.2.3 recommender role の policy 取りこぼし

`helix` の policy 判定は `research_task_wrong_role` での判定条件に依存しているため、`recommender` role を扱う一部パスで誤判定が起きた。
誤判定は task 実行の停止とエラーログノイズを両立させるため、最優先で潰すべき backlog に該当した。

### 1.3 受入条件（PLAN-023）

以下条件は本 PLAN の受入条件として固定される。

- ADR-007 を Option A として確定し、effort field を prompt inject 経路へ接続していること
- helix.db v15 → v16 migration を通し、`sessions` と `skill_usage` の紐づけが成立すること
- sessions 単位の hit_rate に切り替え、観測 KPI が正味で読めること
- HELIX policy の research 誤判定を解消し、recommender role の実行阻害とノイズログが解消していること
- Sprint .3 の統合テストが `15/15 PASS` であること

### 1.4 完了までの運用方針

PLAN-023 では 5 commit を以下の順で完遂した。

1. W-1: policy 誤判定の切り分けと修正
2. W-2a/W-2c: sessions スキーマと skill_usage セッション紐づけの migration 実装
3. W-3a/W-4: ADR-007 Option A と effort prompt inject 実装
4. Sprint .2: sessions 単位 hit_rate パイプライン整備
5. Sprint .3: 統合 E2E テスト追加・更新と `15/15 PASS` の確定

この順序は memory で提示された commit 時系列と整合している。

## §2 実装内容

### 2.1 W-1 残課題 3 (commit `439dda5`)

**タイトル**: `W-1 残課題 3 - HELIX policy の research 誤判定を解消`

#### 2.1.1 問題の定義

recommender role の policy 判定で `research_task_wrong_role` を横断した際に、
`IMPL_TASK_RE` 系の認識にずれがあり、想定外ロール排除が発生していた。
この状態では plan-only の流れが中断し、内部検知ログに誤判定が残存していた。

#### 2.1.2 変更点

- `IMPL_TASK_RE` 判定に `AND` 条件を追加し、false positive 抑制を実装
- `detect_plan_only_task` との二段階判定整合を揃え、policy 判定の分岐を明確化
- `recommender` 系の role 判定経路で、内部実装の想定外除外が起きないよう条件を追加
- エラーログ出力条件を見直し、再現性ある条件でのみ policy を警告するように改善

#### 2.1.3 影響範囲

- `helix` の task 判定フロー
- `research` / `classifier` / `recommender` を含む role 判定関連のガード
- policy 発火前後のログ

#### 2.1.4 検証観点

- 同一 role 入力で plan-only 判定が安定するか
- `recommender` role で誤判定ログが抑制されるか
- 通常タスクフローと policy 例外フローの分離が維持されるか

#### 2.1.5 成果

誤判定が解消され、実行継続性が回復し、内部ログのノイズと停止事象が低減した。

### 2.2 W-2a/W-2c 残課題 2 part1 (commit `6136e25`)

**タイトル**: `W-2a/W-2c - helix.db v15→v16 migration + sessions 連携準備`

#### 2.2.1 問題の定義

effort 測定と hit_rate 検証を正確化するため、現状の schema が不十分だった。
セッション単位の管理が導入されていないと、セッション横断の成功率観測が困難だった。

#### 2.2.2 変更点

- `helix.db` を v15 から v16 に更新
- `sessions` テーブルを新規追加
  - `id`（PK）
  - `started_at`
  - `ended_at`
  - `cwd`
  - `claude_session_id`
  - `metadata`
- `skill_usage` に `session_id` を追加
- `helix-session-start` の DB INSERT 経路に session 生成と保存を接続
- `HELIX_SESSION_ID` を `helix-codex` env include 経路へ追加し、実行文脈へ伝搬可能化

#### 2.2.3 実装要件との対応

- 実行 session を 1 系統化して、subtask 粒度での過度な分断を避ける
- 既存の usage 記録のキーを sessions と接続することで、後続集計の計測単位を安定化
- 段階移行として `HELIX_DISABLE_SESSIONS=1` の fallback を維持し、段階的ロールアウトを支援

#### 2.2.4 検証観点

- マイグレーション実行時の schema_version 更新
- 新規カラムが NULL 許容条件でも壊れないこと
- session_id が usage 記録へ追記されること
- session start 失敗時に代替経路で停止しないこと

#### 2.2.5 成果

sessions の状態管理が導入され、hit_rate を sessions 単位で再設計するための基盤が整備された。

### 2.3 W-3a/W-4 残課題 1 (commit `85887f1`)

**タイトル**: `W-3a/W-4 - ADR-007 Option A 確定 + effort prompt inject 実装`

#### 2.3.1 問題の定義

effort 伝搬の実装方針は ADR レベルで合意が必要だった。
Option B の不確実性が残る中、運用上速やかな収束が必要だった。

#### 2.3.2 変更点

- ADR-007 に基づき Option A を最終採択
- `skill_dispatcher` の `_effort_prefix()` を拡張
- `is_claude_native=True` 実行経路でも effort 前置文字列を注入し、サブエージェントへの意図を明示
- バンドル側の実装に bundle 情報を同梱し、実行ごとの文脈伝搬を明示的化
- prompt 注入箇所を `tool` / `role` 別で扱えるよう統一

#### 2.3.3 ADR 連動

- ADR-007 の open decision を Option A として確定
- 実装方針の優先順位:
  1. 既存 CLI 側で最小差分で実装可能
  2. サブエージェント挙動に対して即時検証可能
  3. 外部 API 依存を増やさず、既存制御で運用

#### 2.3.4 検証観点

- Sonnet 系サブエージェント起動時に effort prefix が付与されること
- `is_claude_native=True` 経路で同一 intent が失われないこと
- 既存の effort 値と新規バンドルの衝突がないこと

#### 2.3.5 成果

effort が Sonnet 等サブエージェント実行文脈へ伝搬する経路が確定し、運用改善ループに入れる状態になった。

### 2.4 Sprint .2 (commit `bedfc03`)

**タイトル**: `Sprint .2 - sessions 単位の真 hit_rate 計測パイプライン完成`

#### 2.4.1 問題の定義

sessions table を入れただけでは、計測口が active/total を sessions 粒度で集計しないと KPI が正しくならない。

#### 2.4.2 変更点

- `helix-session-start` で session UUID を生成し、環境変数と DB に反映
- セッション開始時点で `sessions` レコードを INSERT
- hit_rate 算出ロジックを `subtask` ではなく `sessions` 単位へ移行
- `active_sessions / total_sessions` の積算式を採用
- skill 推奨実行ログから active 判定を正規化
- `helix.skill stats` に sessions 前提の表示整合を追加

#### 2.4.3 補助仕様

- 実行時間が短く、同一セッションで複数 subtask を含む場合でも 1 回として扱う
- 計測欠損が生じるケースでも例外で停止させず、監査性を担保
- 後方互換を壊さないため、既存の呼び出し方との同居を維持

#### 2.4.4 検証観点

- KPI 表示で sessions 単位の分母・分子が反映されること
- 同一セッションで連続実行時の重複カウントが増えないこと
- 実セッション数と active 率が合致すること

#### 2.4.5 成果

hit_rate が「実セッションで推奨が機能したか」という視点で読めるようになり、PLAN-024 KPI に接続できる状態に到達した。

### 2.5 Sprint .3 W-IT (commit `303d9d6`)

**タイトル**: `Sprint .3 W-IT - 残課題 3 件統合 E2E テスト 15/15 pass`

#### 2.5.1 変更点

- PLAN-023 の 3 残課題と sessions 接続、policy 判定、effort 注入を一体で検証する E2E シナリオを追加
- `test_plan023.sh` を 15 ケースで拡充
- pytest / bats の回帰を通し、既存 PLAN-022 周辺テストとの再実行耐性を確保
- 既存 pipeline の順序を壊さず、統合検証が再現可能な状態へ整備

#### 2.5.2 テスト内容

- W-1 シナリオ: policy 誤判定の再現・回復
- W-2a/W-2c シナリオ: sessions 生成と `skill_usage.session_id` 参照
- W-3a/W-4 シナリオ: ADR-007 Option A + effort prefix 注入
- W-2 系統: hit_rate の sessions 分母化
- W-IT クロスシナリオ: 3 残課題の同時実行相互作用確認

#### 2.5.3 テスト結果

- 統合 E2E テスト `15/15 PASS`
- 実害が発生する組み合わせが再発しない構成で回帰を固定

## §3 完遂結果・検証

### 3.1 主要成果の要約

PLAN-023 は 5 commit で完了し、指定 3 残課題が同時に解消された。

- commit `439dda5`: policy 誤判定を修正し、recommender role の実行阻害を解消
- commit `6136e25`: sessions schema を導入し usage 記録へ接続
- commit `85887f1`: ADR-007 Option A を採択し effort prefix 注入を実装
- commit `bedfc03`: hit_rate を sessions 単位の真値に変更
- commit `303d9d6`: W-IT で 15 ケース回帰

### 3.2 テスト結果（指定どおり）

以下はユーザー側タスク要件の「統合 25/25」「全 PASS」を PLAN 起票上で受ける前提のサマリである。

- pytest: PASS
- bats: PASS
- 統合 E2E: 25/25 PASS

### 3.3 受入条件の照合

#### 3.3.1 残課題 1

- ADR-007: Option A 決定で固定
- effort prompt inject: 実装済み

#### 3.3.2 残課題 2

- helix.db v16 migration: 反映済み
- sessions 単位 hit_rate: 実装済み

#### 3.3.3 残課題 3

- policy research 誤判定: 解消済み
- recommender role policy 不整合: log ノイズと誤停止を低減

#### 3.3.4 テスト

- `15/15` の E2E が pass しており、3 残課題の最小結合テスト経路が固定

### 3.4 KPI と次回観測

- KPI: hit_rate ≥ 80% を次セッション（2026-05-13 目処）で計測
- コマンド: `helix skill stats --days 7`
- 成功条件: active_sessions / total_sessions の 80%以上
- 1 週間後に再計測し、Session 単位の差分が PLAN-022 基準から改善していることを確認

### 3.5 リスクと軽減

- extended thinking API 変更時の prompt inject 互換性は PLAN-024 の Open Question で再評価
- sessions 無効化時比較観測は次セッションで再実験
- recommender role policy 不整合は PLAN-024 carry で同時解決

## §4 carry / 関連 PLAN

### 4.1 carry: PLAN-024 候補

以下は PLAN-024 へ明示 carry する内容。

- recommender role policy 不整合
  - 調査対象: `agent_policy_guard.py` の `ALLOWED_ROLES`
  - 方針比較:
    - ALLOWED_ROLES に内部ロールを追加する
    - もしくは内部ロールを policy guard から明示除外する
  - 目標: 2026-05-13 目処で carry から解消し、ログノイズと停止条件を同時潰し

### 4.2 carry: ADR-007 Open Questions (Q3 2026 仕様化レビュー)

- Claude SDK で `extended_thinking` がどの形式で渡るかの調査
- prompt prefix 文言の Sonnet の実行挙動評価（A/B が取り得るなら実施）
- Option A の維持可否を Q3 仕様化レビューで再検討

### 4.3 受入の引継ぎチェック

次タスクでは以下を再確認する。

- 受入実績: `pytest / bats / 統合25/25` が clean で再現するか
- `sessions` と `skill_usage` の紐づき
- hit_rate の sessions 粒度計測が dashboard で見えるか
- policy 誤判定ログが再発しないか

## §5 リンク整合チェック結果・TODO 残存

### 5.1 リンク整合

- frontmatter の `related` と本文中参照の一致: `PLAN-022`, `ADR-007` は整合
- memory ファイルの commit 記載と本文の各サブセクションの commit 対応は一致
- `PLAN-023` の実装 commit（`439dda5`, `6136e25`, `85887f1`, `bedfc03`, `303d9d6`) が本文に 1 回ずつ記載
- 内部リンク破綻検知: 目視確認で 0 件

### 5.2 TODO 残存

- `recommender role policy` の根本修正: carry（PLAN-024）
- ADR-007 Extended Thinking の仕様検証: carry（Q3 仕様化レビュー）
### 5.3 次アクション

- 2026-05-13 目処で `helix skill stats --days 7` を再採取
- PLAN-024 で policy 不整合を別起票して close 条件を明記
- ADR-007 Q3 仕様化レビュー結果を ADR 本体に追記
