---
plan_id: PLAN-027
title: "PLAN-027: HELIX らせん式 entries/links 基盤 (code-index 6 軸拡張 + helix-entry CLI)"
status: completed
size: M
drive: be
owner: PM
phases: L1, L2, L3, L4, L6
gates: G2, G3, G4
acceptance:
  - helix.db v17 で entries / links 2 テーブル + 6 index を追加
  - helix.db v18 で code_index に 6 軸メタデータ列 (origin / lifecycle / domain_kind / pair / direction / source) を ALTER ADD COLUMN
  - # @helix:index parser が 6 軸フィールドを認識し catalog に反映
  - code_catalog.sync_to_db が entries テーブルを bulk populate
  - cli/helix-entry CLI が 7 subcommand (search / show / link-add / link-list / matrix / stats / verify) を提供
  - 全網羅 test (pytest +18, bats 15/15) が PASS
  - entries 53 件 / coverage 252 matrix の populate を確認
related:
  - PLAN-011-code-index-system
  - PLAN-012-code-index-coverage
  - PLAN-013-code-index-eligibility-taxonomy
  - PLAN-024 (LLMClassifierBase に entries E2E test 追加)
doc_completed:
  - docs/operator/helix-spiral-operations.md (らせん式 Spiral 運用マニュアル、2026-05-16 起票)
created: 2026-05-07
---

# PLAN-027: HELIX らせん式 entries/links 基盤 (code-index 6 軸拡張 + helix-entry CLI)

## §1 背景・目的

PLAN-011 / PLAN-012 / PLAN-013 で構築された `code_index` を、成果物単位の履歴記録を扱える `entries` テーブルと、記録間の依存・根拠・参照を扱える `links` テーブルとで拡張する。  
この基盤は、実装結果だけでなく、どの判断がどの前提から生まれたかを再現可能にする。

本 PLAN は、Sprint .3 を完了するための 6 回の実装ブロック（W-3a〜W-3f）を、検証可能な証跡で逆起票する。

本基盤の中核は「蓄積された成果物記録」と「記録間の関係」をセットで管理すること。  
それにより、テーブル単位ではなく、意思決定の時系列・関連性・分類を保持したまま分析できる。

### 1.1 追加する記録基盤の意図

`entries` は、以下を 1 行 1 件として蓄積する。

- どのコード上の実装（id）
- どの担当領域（domain）
- どの実装意図（summary）
- 6 軸メタデータ:
  - `origin`: 記録の起点（例: sprint、manual、seed）
  - `lifecycle`: life cycle（initial / addition / modification / migration / deprecation / removed）
  - `domain_kind`: 技術領域（design / plan / code / schema / test / review / evidence）
  - `pair`: 対応関係（例: 同時実装の対）  
  - `direction`: 流れ（upstream / downstream / internal）
  - `source`: 補足の発生元（コメント、テスト、コマンド）

- `links` は `entries` 同士の「つながり」を表現する。  
  たとえば、1 つの test 記録が特定の code 記録に依存する場合など。

### 1.2 `code_index` との接続

`code_index` はすでに PLAN-011〜013 の運用で、シンボル起点の分類と検索体制が導入されている。  
Sprint .3 では `code_index` を壊すことなく、6 軸メタデータを追加して再検索・集計精度を上げる。

追加の接続観点:

- `code_index` はシンボル単位の索引として維持
- `entries` は成果物記録の履歴として追加
- `helix.code.stats` の表示/絞り込みに、`entries` の多面情報を利用
- `cli/helix-entry` で `entries` と `links` を操作し、利用者が検証しやすい形で再利用

### 1.3 実装背景

Sprint .3 開始時点では、`code_index` の 3 軸情報はありながら、成果物の累積履歴と
リンク構造が未整備だったため、以下の制約が残っていた。

- 変更履歴を code symbol から時系列で追いにくい
- 変更の起点と影響を「成果物記録」として突き合わせにくい
- エントリの属性が 3 主要項目だけで、後工程で分類が曖昧
- coverage の全組み合わせ検証が `entries` 内在数で偏る

PLAN-024 への carry として、`LLMClassifierBase` の E2E test でもこの記録基盤が参照される前提を取り込むため、今回の起票は「結果を固定し、次の計画へ接続する」ことを目的とした。

### 1.4 この PLAN 文書の目的

この PLAN の主目的は、実装結果の「完成」を受け、以下を満たした状態を証跡付きでまとめること。

1. 何を追加したか（commit 単位）
2. なぜ追加したか（問題起点）
3. どこまでテストで確認したか
4. 他 PLAN との接続点をどこに置いたか
5. 受入条件との整合性

このため、文書は §1〜§4 を最短で網羅し、`PLAN-068` の体裁準拠を維持する。

## §2 実装内容 (Sprint .3 commits 順)

Sprint .3 は 6 ブロックで完遂済み。  
順序は仕様の整合上必須のため、W-3a→W-3f の順で管理する。

### 2.1 W-3a (commit: 085cd66)

タイトル: `Sprint .3 W-3a - helix.db v17 migration (entries + links + 6 index)`

このブロックは最初の構造追加を担当。

変更内容:

- `helix.db` スキーマを v17 へ更新
- `entries` テーブルを新規作成
- `links` テーブルを新規作成
- `entries` / `links` 運用で不足しやすい参照と検索を補う 6 index を追加
- 参照整合:
  - `links.entry_id` と `links.target_entry_id` の関連づけ
  - 見つけやすさ重視で axis/stack/sprint/agent/lifecycle/links_kind 各 index

#### schema spec（要点）

- `entries.id`（主キー）
- `entries.domain`（文字列）
- `entries.summary`（短文）
- `entries.axis`（CHECK 制約）
- `entries.stack`（CHECK 制約）
- `entries.sprint`（文字列）
- `entries.agent`（文字列）
- `entries.created_at` / `updated_at`（監査）
- `links.id`（主キー）
- `links.entry_id` / `links.target_entry_id`（FK 形式）
- `links.link_kind`（関係種別）
- `links.created_at`（監査）
- 各 index は `axis`, `stack`, `sprint`, `agent`, `lifecycle`, `link_kind` 系
- `entries` は `INSERT` 頻度が高い前提で運用を想定し、`links` は参照削除時の整合を保持

補足:

- W-3a の時点では運用方針として `entries` + `links` 追加に集中し、`code_index` 側の列追加は次ブロックへ分離
- v17 は additive 追加に限定し、既存履歴・既存テーブルを壊さない方式を採用

受入対応:

- 受入条件 1: `helix.db v17 で entries / links 2 テーブル + 6 index` の追加が満たされる
- 該当 commit と対応: `085cd66`
- 追加検証点: 作成・既定値・参照整合の基本動作確認（migration 実行経路）

### 2.2 W-3b (commit: 8aa473e)

タイトル: `Sprint .3 W-3b - # @helix:index parser に 6 軸フィールド追加`

内容:

- `# @helix:index` parser 側の field 定義を拡張
- 既存 `{id, domain, summary}` に加えて 6 軸を認識
  - `origin`
  - `lifecycle`
  - `domain_kind`
  - `pair`
  - `direction`
  - `source`
- 既存の後方互換性を維持（既存の必須 3 項目の形式は継続）
- catalog へ反映される metadata に 6 軸を含める

実装上の工夫:

- parser の再構成は最小変更で、既存の `axis / summary / domain` 周辺の処理を壊さない
- 受理順序は既存形式互換を優先し、新規項目は optional 追加として取り込む
- 欠損時の既定値は既存設計と一致する扱いにして、静的解析の破壊を避ける

受入対応:

- 受入条件 2: 6 軸を認識し catalog に反映
- 該当 commit と対応: `8aa473e`
- catalog 集計・検索の見直し時に 6 軸が metadata へ見える状態を想定

### 2.3 W-3c (commit: 61eef44)

タイトル: `Sprint .3 W-3c - helix.db v18 migration (code_index に 6 列 ALTER ADD COLUMN)`

内容:

- `code_index` テーブルへ 6 軸列の `ALTER ADD COLUMN` を追加
- 既存行への影響が出ない additive 方式を採用
- 新規列:
  - `origin`
  - `lifecycle`
  - `domain_kind`
  - `pair`
  - `direction`
  - `source`
- v17 → v18 の移行でデータ移行の破壊を避ける

実装意図:

- v18 は `code_index` 自体を再作成するのではなく拡張したため、ロールバック・再適用が容易
- 既存の coverage と catalog に対して「新しい軸を後付け」し、既存の分類ロジックは継続維持

受入対応:

- 受入条件 3: v18 で 6 軸列を ALTER ADD COLUMN
- 該当 commit と対応: `61eef44`
- 既存検索・集計との整合は既存テストを通じて担保

### 2.4 W-3d (commit: be7514d)

タイトル: `Sprint .3 W-3d - code_catalog.sync_to_db で entries テーブル bulk populate`

内容:

- `code_catalog.sync_to_db` の処理を拡張し、`entries` へ bulk insert を追加
- index を増やした `entries` を、`code` 系 index 走査から再構築できるようにした
- 重複防止と再実行時の副作用を避ける仕組みを採用
- `axis='code'` の既定運用を補完
- `metadata` は JSON 形式で拡張

実装詳細:

- 既存の sync ループの中で `entries` 向けの収集・変換を追加
- `origin` / `lifecycle` / `domain_kind` / `pair` / `direction` / `source` を metadata としてセット
- 一定条件で `INSERT OR IGNORE` を使い、二重 insert を防止

受入対応:

- 受入条件 4: `code_catalog.sync_to_db` による entries bulk populate が成立
- 該当 commit と対応: `be7514d`
- 追加検証: E2E 側から 53 件を参照できる状態（後述 §3）

### 2.5 W-3e (commit: 1c2146e)

タイトル: `Sprint .3 W-3e - cli/helix-entry CLI 新規実装 (7 subcommand + Python helper)`

内容:

`cli/helix-entry` コマンド群を新設し、`entries` と `links` の実務操作を CLI に一本化。

提供 subcommand:

- `search`: 軸やフィルタで entries を検索
- `show`: 指定 entry の詳細を表示
- `link-add`: entry 間リンクを追加
- `link-list`: リンク一覧を表示
- `matrix`: 3軸組み合わせの集計を表示
- `stats`: 全体件数や分布統計を表示
- `verify`: 整合検証

Python helper:

- 共通ヘルパーで entries・links の入出力整形を共通化
- CLI 側の重複処理を排し、coverage やテストから使える形に分離

実装上のポイント:

- 命令口（CLI）とデータ口（DB 更新）を明確に分離
- 検索と一覧の結果に軸情報を標準表示
- link 種別に応じて human-readable な表示を選択
- verify は最低限の整合性検証を自動化

受入対応:

- 受入条件 5: 7 サブコマンドを提供
- 該当 commit と対応: `1c2146e`
- bats 側 `test-helix-entry` からの実行経路が成立する前提

### 2.6 W-3f (commit: dd75547)

タイトル: `Sprint .3 W-3f - 全網羅 test 追加 + coverage --triplet 完全 matrix 化`

内容:

- pytest / bats の最終網羅を整えるテスト追加
- coverage `--triplet` の matrix 化を修正し、軸数に依存しない完全網羅を実装
- 既存失敗ケースを吸収し、matrix が空セルを落とさず返すように変更
- `coverage` 側の GROUP BY 偏りを潰し、軸・stack・lifecycle の 252 組み合わせの完全返却へ

主要効果:

- `pytest` の件数増加 (+18)
- `bats cli/tests/test-helix-entry` の PASS 安定
- `coverage --triplet --json` で 252 セル確認
- `links` 側の整合も coverage で確認しやすく

受入対応:

- 受入条件 6: 全網羅 test の追加と PASS
- 受入条件 7: coverage 252 matrix の確証
- 該当 commit と対応: `dd75547`
- 追加テストの重複は避け、既存テストの網羅性を壊さない運用

### 2.7 WBS 単位での整合ログ（Sprint .3）

Sprint .3 の WBS は W-3a 〜 W-3f で連続実施し、以下を前提に完了扱いとする。

- W-3a で DB 2 テーブル追加
- W-3b で parser 6 軸化
- W-3c で code_index 6 列追加
- W-3d で bulk populate
- W-3e で CLI 実装
- W-3f で matrix 完備テスト

順序を崩すと、W-3e 以前に 6 軸を参照しようとした際の整合不備が起きるため、この順序を保った。

## §3 完遂結果・検証

### 3.1 完成実績

- `entries` 件数: 53 件
- `coverage --triplet` 結果: 252 組み合わせ（空セル含む）を確認
- `pytest` 実行: 875 → 893（+18）
- `bats` 実行: 15/15 PASS
- `core5` coverage ゲート維持を前提とする
- `cli/helix-entry` による検索・リンク・行列集計の実行が成立

### 3.2 受入条件の対応表

| 条件 | 証跡 |
|------|------|
| helix.db v17 で entries / links + 6 index | W-3a (`085cd66`) |
| helix.db v18 で 6 軸列追加 | W-3c (`61eef44`) |
| parser が 6 軸を認識 | W-3b (`8aa473e`) |
| entries bulk populate | W-3d (`be7514d`) |
| 7 subcommand CLI 提供 | W-3e (`1c2146e`) |
| pytest/bats 全網羅 | W-3f (`dd75547`) |
| entries / matrix 確認 | W-3f + 記録検証 |

### 3.3 変更の安全性

- 破壊的な migration は行わず、すべて additive で追加
- 既存 `code_index` の運用を壊さず、後付けで高解像度情報を増量
- `links` と `entries` は既存実行経路の補完として運用し、既存 CLI の既定動作を壊さない
- テストは commit ごとに増分確認し、最終的な regression を抑制

### 3.4 最終状態

- Plan status: `completed`
- 追加したスキーマと CLI は次セッションの PLAN-024 で利用される前提
- 追加した links/tracking 情報は、レビュー、検証、テスト再利用の共通言語として使用

### 3.5 DoD および L8 接続

Sprint .3 の DoD は、仕様通り以下を満たして終了。

- 条件を 1 つずつハッシュで追跡可能
- `entries` 53 件 / matrix 252 の数値を確認
- `pytest` と bats の両方を通過
- status を `completed` とした文書に集約
- 以降の PLAN-024 の受入条件に必要な carry を明示

## §4 carry / 関連 PLAN

### 4.1 受け口としての carry

本 PLAN が carry した主な接続先:

- PLAN-024: Sprint .2 W-2d の entries E2E test を受ける（connection point）
- PLAN-013: eligibility taxonomy と `entries.bucket` / taxonomy の整合を担保
- PLAN-024 の W-2 系列では、`entries` が LLMClassifierBase の決定ログで利用可能

### 4.2 未起票項目（carry）

未起票の PLAN-020〜PLAN-026 は、同質の carry として後続セッションで順次起票予定。  
本体起票では、本 PLANは完了として記録し、次の順序制御を外在化する。

### 4.3 関連 PLAN 一覧

- PLAN-011-code-index-system
- PLAN-012-code-index-coverage
- PLAN-013-code-index-eligibility-taxonomy
- PLAN-024
- PLAN-027 Sprint .3 完遂（過去メモ）

### 4.4 次セッションへの受け渡しメモ

- 実装側で増えた `entries` メタデータは PLAN-024 で「再利用可能な検証ログ」として扱う
- coverage の matrix 化を前提に、PLAN-024 側テストの成否判定を固定
- `cli/helix-entry` の 7 サブコマンドを前提に、`helix` 運用を `entries` 参照中心へ拡張可能

---

## 付録 A: 主要コミット一覧（hash + 1 行サマリ）

- `085cd66` feat(plan-027): Sprint .3 W-3a - helix.db v17 migration (entries + links + 6 index)
- `8aa473e` feat(plan-027): Sprint .3 W-3b - # @helix:index parser に 6 軸フィールド追加
- `61eef44` feat(plan-027): Sprint .3 W-3c - helix.db v18 migration (code_index に 6 列 ALTER ADD COLUMN)
- `be7514d` feat(plan-027): Sprint .3 W-3d - code_catalog.sync_to_db で entries テーブル bulk populate
- `1c2146e` feat(plan-027): Sprint .3 W-3e - cli/helix-entry CLI 新規実装 (7 subcommand + Python helper)
- `dd75547` feat(plan-027): Sprint .3 W-3f - 全網羅 test 追加 + coverage --triplet 完全 matrix 化

## 付録 B: 本文中の制約遵守チェック

- 禁止用語を使用していないことを本文上で確認できる状態
- `frontmatter` は YAML 形式
- `§1 / §2 / §3 / §4` の見出しを含む
- `acceptance` 全項目を本文内に対応させている
- commit hash と 1 行サマリの追跡が可能
