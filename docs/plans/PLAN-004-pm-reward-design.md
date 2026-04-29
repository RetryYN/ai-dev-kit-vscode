# PLAN-004: PM 報奨設計 (philosophy shift: 速度 → 正確・精度志向への評価軸調整) (v3)

## 1. 目的

- gate 名称凡例: `G2=設計凍結 / G3=Schema Freeze / G4=Implementation Freeze / G5=Design Freeze / G6=RC / G7=安定性`

- HELIX の評価哲学を、スピード最優先状態から、正確性・精度・再現性を優先する方向へ切替える。
- `PLAN review` の曖昧性と `G3/G4` 判定の甘さを解消し、PLAN-002/003 で観測されたレビュー過剰深掘りループを原則ではなく設計判断で収束させる。
- 本 PLAN は「方向性（方針）を凍結」する PLAN ドキュメントとして成立させ、実装詳細の断定は `G3=Schema Freeze` 時点でのみ確定する。
- コミットは行わない。設計 Freeze が完了した時点で `コミット禁止` の方針を維持する。
- PLAN review 段階（本 v2）では方向性のみを凍結し、精度重視フェーズの評価確定は G3 以降で実施する。

### 1.1 目的を固定する評価観点

- 速度の最大化ではなく、次の 3 点を優先する。
  - 正確性（仕様・実装整合）
  - 精度（レビュー観点の再現性）
  - 安定性（再現可能な再レビュー、運用に耐える再現性）
- 評価が「チェックリストの通過」だけで終了せず、
  「確度が足りないか」を明示的に記録できる状態を構築する。
- 再評価が起きても、
  `deferred` として記録された根拠が残るようにする。

### 1.2 目的達成の非機能条件

- PLAN ドキュメントは 1 ファイルのみ新規作成。
- 本 PLAN では実装ロジックそのものの設計（SQL 詳細、CLI 挙動詳細、テンプレート完全文）は最小限にし、`G3` での `Schema Freeze` を明示。
- `.helix/` 配下は編集しない。
- `helix-plan review` は Opus 実施。

### 1.3 目的外だが必ず明示する制約

- L8 受入では精度未達が本 PLAN の意図どおり扱われているかを確認する。
- 実運用の自動化・ルーティング変更（別レビュアー自動割当など）は本 PLAN では設計のみ。
- モデル変更（例: `gpt-5.4` → `gpt-5.5`）は本 PLAN の対象外。

## 2. 背景

### 2.1 問題定義

- `helix-plan review` が通りやすいと、
  スコープ外の詳細漏れが見逃される。
- `helix-plan review` が厳しすぎると、
  PLAN-002 で v34 まで反復したような停止ループが起きる。
- `G2` 以降のゲートが「項目の有無」に偏り、精度・正確性の強弱が不透明。
- `Codex review` 側（`tl/se/pg/qa/security/dba/devops/docs`）が、
  PLAN レビュー / G3 / G4 の違いを十分に意識しきれず、レビュー観点が画一化。
- 結果として、`deferred` 処理が蓄積されず、
  学習不能な状態が続いている。

### 2.2 背景事実

- PLAN-002 と PLAN-003 において以下が確認され、
  哲学レベルでの修正が必要と判断された。
  - TL が高い厳格性を上げるほど、再レビューで反復増大。
  - TL が低い厳格性を選ぶと、実行時の精度検証が薄くなる。
  - 両者間のバランスを「G レイヤ」ごとに設計しないと、継続的改善が難しい。

### 2.3 現在運用の問題点

- 同じレビュー観点が `G3` と `G4` 両方に使われるため、
  意味が異なるにもかかわらず評価が同じに見える。
- `accuracy` に関する数値化ルールが不十分。
- 将来の継続改善（PLAN-006 以降）で、
  実データを参照しづらい。

### 2.4 本 PLAN での解像度定義

- 本 PLAN は「方針」を定める。
- 技術的な実装詳細の仕様として確定しない範囲（UI文言・出力フォーマットの逐語は除く）を明確化する。
- `G3` で `Schema Freeze` として詳細を固定する前提。

## 3. スコープ

### 3.1 含むもの

1. TL prompt のレイヤ分離を PLAN と G2-G7 で維持するための方針確定。
   - `helix-plan review` の方向性
   - `cli/helix-gate` の `G2/G3/G4/G6/G7` 分離観点
   - `PLAN` / `precision freeze` / `implementation freeze` の意味論定義
2. Codex review の観点追加と、ロール横断の統一メタ観点を PLAN で確定。
   - `tl / se / pg / qa / security / dba / devops / docs` 各 role の精度評価文言の標準化
   - `cli/roles/*.conf` の更新時の対象差分点定義
3. `skills/tools/ai-coding/references/gate-policy.md` における
   `accuracy_weight` 方針を確定。
4. `helix.db v10` への `accuracy_score` 追加を前提定義。
   - `timestamp / plan_id / gate / dimension / score` を最小スキーマとして方針化
5. CLI 最小追加機能（可視化）を PLAN で設計。
   - `helix accuracy report` の存在意義、入力・出力粒度を規定
6. Codex が gate 境界で 5 段階フィードバックをユーザープロンプト形式で返す仕組み。
   - `cli/helix-gate` への hook（G2〜G7）
   - `cli/templates/feedback-prompt.md`
   - 評価観点 5 軸（情報の密度 / 深さ / 広さ / 実装の正確性 / 保守性）
   - Lv1 〜 Lv5 基準
7. L8 受入条件に精度凍結の残件扱いを追加する方針確定。
   - `deferred` 記録の成立条件を定義

### 3.2 含まないもの

- 各 gate の checklist そのものを全面的に変更しない。
  - `PLAN-007b` で必要な `Run 工程` での再検討に委譲。
- 自動 reroute や reviewer 交換の実動実装。
  - 本 PLAN では設計のみ、実装は後続 PLAN。
- モデル変更（`gpt-5.4`→他版）
- データ移行の本番影響を伴う大規模 SQL ロジックの実装

### 3.3 スコープ境界（この PLAN の凍結境界）

- `コミット禁止`：本 PLAN は方向性凍結であり、実装手段は原則 G3 で扱う。
- `PLAN-002/003` の既存進捗は前提にし、置換はしない。
- 既存の `.helix/` を変更しない。
- 本 PLAN は `docs/plans/PLAN-004-pm-reward-design.md` のみ新規作成。

### 3.4 成果物（本 PLAN）

- PLAN 文書を継続的に提供する単体として扱う。
- 実装差分やコード変更は持たない。
- 受入目線でのチェックポイント（特に L8）を明示する。

### 3.5 スコープ外（明示）

- 具体的なテンプレート文面の完全版。
- 実際の DB migration 実行順（down / up / rollback）
- CLI 実装における入出力フォーマット最終文言
- Gate policy の重み付けに伴う評価アルゴリズム最終定数

## 4. 採用方針

本章は (a)〜(e) の 5 軸で統一する。

- (a) TL prompt 評価軸
- (b) Codex review prompt 横断
- (c) gate-policy 重み付け
- (d) helix.db scoring DB
- (e) ユーザープロンプト型 5 段階フィードバック

### 4.1 (a) TL prompt 評価軸

#### 4.1.1 方針定義

- `PLAN` レベル評価は「方向性」が主、実装仕様には踏み込みすぎない。
- `G3=Schema Freeze` は精度要件を確定し、`G4=Implementation Freeze` は実装精度の実在性を検証する。
- `G6/G7` は現場適用性（実プロジェクトでの効果）を確認する。

#### 4.1.2 役割別分解

- `helix-plan review`
  - 目的: 計画と価値観の一致、実行妥当性の方向付け。
  - 観点: 対応スコープ、意思決定前提、失敗時の救済条件。
  - 禁止: ここで実装詳細を固定しない（詳細は G3 へ委譲）。

- `cli/helix-gate`（G2）
  - 目的: 設計凍結前の方向性整合確認。
  - 観点: 重要な前提が「暫定」か「確定」かを明確化。
  - 追加: `precision freeze` 欠陥リストの初期定義。

- `cli/helix-gate`（G3）
  - 目的: Schema Freeze / テスト設計 / migration への反映可能性確認。
  - 観点: 精度要件の最小充足条件を列挙。
  - 追加: `accuracy_score` DDL freeze の前提整合。

- `cli/helix-gate`（G4）
  - 目的: 実装精度の検証可否。
  - 観点: 実装された証拠がレビュー観点と整合しているか。
  - 追加: PLAN-002/003 改修後の再レビュー結果記録。

- `cli/helix-gate`（G6）
  - 目的: RC 判定前提の実体験評価。
  - 観点: 少なくとも 1 実プロジェクトでの報奨設計適用。

- `cli/helix-gate`（G7）
  - 目的: 安定運用の継続可能性確認。
  - 観点: 簡易化しないレビュー観点の残存を確認。

#### 4.1.3 実施時に残すべき不確実性の表現

- 各レビューで以下を記録する。
  - `確信あり`（明示的な証拠あり）
  - `要追加調査`（G3 または G4 で再確認）
  - `deferred`（G3/G4 で凍結）
- `deferred` は後続で必ず再審査トラックを作る。

### 4.2 (b) Codex review 横断観点の精度軸化

#### 4.2.1 対象ロール

- `tl`: 方針準拠、制約と例外の明示、逸脱理由
- `se`: 実装精度の再現性、例外発生時の戻し条件
- `pg`: 実装粒度、再現手順、テスト観点の粒度
- `qa`: テストケースの網羅と境界条件
- `security`: 脅威モデルとの整合、脆弱性回避の証拠
- `dba`: migration 安全性、可観測性、ロールバック整合
- `devops`: 運用手順と復旧観点
- `docs`: 文書と実態の乖離リスク

#### 4.2.2 追加評価軸（共通）

- 精度（Accuracy）
  - 要件の取りこぼし率
  - エッジケース明示率
  - 失敗再現性
- 安定性（Stability）
  - 環境差分耐性
  - 再試行耐性
  - 回帰観測可能性
- 意図一致（Intent fidelity）
  - 仕様とレビュー指摘の一貫性
  - `deferred` の根拠妥当性

#### 4.2.3 実装方針

- `cli/roles/*.conf` の review hint は、
  各 role ごとの重み比率を持たせた上で、共通の精度軸を先頭に記載。
- `codex-review-prompt` は単一のテンプレート化を想定し、role 別拡張を許容。
- PLAN-004 以降で `codex review` が「チェックリスト記載」から
  「精度検証根拠記載」へ移る。

### 4.3 (c) gate-policy の重み付け導入

#### 4.3.1 方針

- `accuracy_weight` は 0.0〜1.0 の浮動小数で設定する。
- 単調増加を不変条件にはせず、フェーズの役割に応じて重みを固定する。
- `G3 Schema Freeze` / `G4 Implementation Freeze` / `G6 RC` は高く、`G2`（方向性） / `G7`（運用安定性）は中程度に設定する。
- 値は一度固定し、変更は PLAN レベルの再審査でのみ。

#### 4.3.2 重み方針（v3 時点の暫定提案、G2 凍結予定）

| Gate | v3暫定値 | 根拠 | 用途 |
| --- | --- | --- | --- |
| G2 | 0.60 | 方向性 | 方向性レビュー品質の下限設定 |
| G3 | 0.90 | schema 凍結 | 実装前精度の高い保証 |
| G4 | 0.95 | implementation freeze | 実装精度の主評価軸 |
| G5 | 0.70 | 安定性補助 | L5 skip 対象では補助的 |
| G6 | 0.95 | RC 判定 | リリース適格性の重み |
| G7 | 0.70 | 運用安定性 | 運用品質再検証 |

#### 4.3.3 設定値固定ルール

- 予備検証では一時値変更禁止は維持するが、G2 設計凍結時に最終値を確定する。
- v3 は暫定提案として扱う（根拠: G3/G4/G6 を精度重視、G2/G7 は方向性・運用重視）。
- 運用上の再調整は `PLAN-xxxx` での設計変更として扱う。

### 4.4 (d) helix.db scoring DB 集積（PLAN-004 G3）

#### 4.4.1 取得観点

- `timestamp`: 収集時刻
- `plan_id`: PLAN 単位での関連付け
- `gate`: G2/G3/G4/G6/G7 の記録対象
- `dimension`: 情報の密度 / 深さ / 広さ / 実装の正確性 / 保守性
- `score`: 0〜1 の正規化値
- `improvement_level`: 前 PLAN/sprint と比較した改善度

#### 4.4.2 収集ルール

- 記録は `deferred` 含みを残せる形式。
- 評価は「完了 / 未完了 / 保留」の 3 値ではなく、
  `score` + 根拠 `comment`（別途保存）で残す。
- PLAN-002/003 の v8/v9 後に `helix.db v10` を適用する前提。
- 参照は本 PLAN では `helix accuracy report` のみに限定。
- `DDL freeze` は本 PLAN の G3 で実施する。
- 保存前 redaction は L3 で redaction adapter を freeze し適用する（PLAN-002 の redaction-denylist と共通正規表現ライブラリを採用）。
- `CHECK` 制約は構造的検証（NOT NULL、enum 一致、長さ、型）に限定する。

#### 4.4.3 活用範囲（本 PLAN）

- 集積は設計 freeze と受入監査を助けるログ基盤。
- 自動的な自動ルーティング変更は行わない。
- `helix accuracy report` は閲覧に特化し、意思決定ロジックは次 PLAN。

#### 4.4.4 L3 freeze: redaction adapter 仕様

- redaction 対象: `accuracy_score` の `comment` / `evidence`。
- L3 で redaction adapter を freeze し、対象カラム・正規表現・除外ワードを固定。
- 保存前に `password|token|apikey|secret` 系を伏字化し、`CHECK` 制約は構造検証のみで担保する。

### 4.5 (e) ユーザープロンプト型 5 段階フィードバック

- 方針（verbatim）: 報酬は各工程の境界に Codex にユーザープロンプトとして返させる仕組みをいれて、情報の密度、深さ、広さ、実装の正確性、保守性、みたいなレビュー観点で返させて教訓とする。フィードバック基準を5段階に設けて、改善度レベルで管理するのはどうかな？Claude のユーザーが喜びに対して振る舞いを変えるを逆手に取る。
- 5 段階評価基準
  - Lv1 (poor): 観点に対して欠落・不正確
  - Lv2 (insufficient): 部分的、補強必要
  - Lv3 (acceptable): 標準的、可
  - Lv4 (good): 充実、模範的
  - Lv5 (excellent): 卓越、横展開すべき
- `cli/helix-gate` は G2〜G7 通過直後に `helix-codex --role tl --task "review-feedback ..."` を実行し、上記 5 軸を `cli/templates/feedback-prompt.md` テンプレートでユーザー向けプロンプトとして返す。
- `accuracy_score` に `improvement_level` を保存し、前回との差分で改善度を蓄積する。
- なお gate 別に 5 軸の weighting と文面 fixture を分岐し、画一化を抑制する。

## 5. ゲート

### 5.1 前提: この章は G1〜G7 に対する PLAN-level 条件

- 本節は `gate-policy.md` の必須条件を上位化し、
  `PLAN-004` 独自条件を追加する。
- 詳細実装の仕様は G3 Freeze として `Schema`/`migration` に移譲。
- なお G2〜G7 の通過時は、`cli/helix-gate` で `helix-codex --role tl --task "review-feedback ..."` を実行し、ユーザープロンプト形式で「教訓」を返し、`accuracy_score` へ保存する。

### 5.2 G1 要件完了（PM 確認）

- PM 確認が必須（本 PLAN が哲学変更であるためユーザーレビュー必須）。
- `PM 報奨設計` であることの説明責任を明示。
- 受入条件:
  - 目的・背景・スコープ・採用方針が一貫している。
  - `PLAN 〜` の範囲が実装対象と重複しない。
  - 1 ファイル新規作成の前提が維持される。

### 5.3 G2 設計凍結

#### 5.3.1 gate-policy 準拠条件

- 要件トレース、ADR、threat-model、adversarial-review、ミニレトロ、セキュリティ①
  が満たされる。

#### 5.3.2 PLAN 追加条件

- `TL prompt` 改修方針（PLAN レベル）を明確化。
- `Codex review` 改修方針を明確化。
- `accuracy_weight` 根拠を明記。
- G2 通過時に 5 段階（情報の密度、深さ、広さ、実装の正確性、保守性）で教訓を出力。

#### 5.3.3 G2 Freeze 条件

- `PLAN review` と `G2 gate review` が「方向性」と「厳密さ」の違いを明言。
- `precision freeze` の意味が文書化されている。

### 5.4 G3 Schema Freeze（実装着手）

#### 5.4.1 gate-policy 準拠条件

- Schema Freeze / テスト設計 / WBS / migration/rollback / 事前調査。

#### 5.4.2 PLAN 追加条件

- `helix.db v10 migration spec` を Freeze。
- `accuracy_score` DDL Freeze。
- CLI 仕様 (`helix accuracy report`) を Freeze。
- `accuracy_score` には G3 時点で `comment` / `evidence` の redaction を義務付ける。
- `accuracy_score` の redaction 未適用は G3 合格条件を阻害する。
- PLAN-002 の hash 正規化規則に準拠し、構造的 `CHECK` 制約（NOT NULL / enum / 長さ）を `DDL freeze` に組み込む。
- redaction は L3 freeze で `PLAN-002` redaction-denylist と共通正規表現ライブラリを適用するアダプタ仕様を `freeze` する。

#### 5.4.3 G3 Freeze 条件

- ここで初めて本 PLAN の技術的実装粒度（スキーマ、入出力、検知粒度）を固定。
- `PLAN-004` 以外の文書に対して、詳細実装上の差し替えは禁止。
- `5段階基準` の `DDL freeze` と、ユーザープロンプト `template freeze`（`cli/templates/feedback-prompt.md`）を成立させる。

### 5.5 G4 Implementation Freeze（実装凍結）

#### 5.5.1 gate-policy 準拠条件

- CI、回帰、セキュリティ②、debt 証跡、ミニレトロ。

#### 5.5.2 PLAN 追加条件

- TL/Codex prompt の改修完了。
- `helix accuracy report` の目視確認（表示可能性）。
- PLAN-002/003 で改修後の prompt が再 review されている。
- G4 通過時もユーザープロンプト形式で教訓出力（Lv1-5）。

#### 5.5.3 受入条件

- `PLAN-004` と `PLAN-002/003` の接続が文書上整合。
- `precision layer` ごとの判定記録が追跡可能。

### 5.6 G5 デザイン凍結

- UI 未導入のため、適用条件（UI なし）を満たす。
- 残存する要件は次フェーズへ継承しない。
- ただし、必要に応じて `PLAN-004` のレビュー証跡を更新。
- G5 適用時にも `review-feedback` hook を履歴として残す。

### 5.7 G6 RC 判定

#### 5.7.1 gate-policy 準拠条件

- gate-policy G6 条件、RC 判定の前提。

#### 5.7.2 PLAN 追加条件

- `実プロジェクト 1 件` 以上で報奨設計を適用。
- 効果確認（例: review loop 長さ、deferred の明示率、再発見率）が確認される。
- `G6` 判定前に、改善度レベル（前PLAN比）が可視であることを確認。

#### 5.7.3 G6 判断ポイント

- 運用導入における過剰厳格化の有無。
- 過不足を評価し、次 PLAN 向け修正提案を作成。

### 5.8 G7 安定性

#### 5.8.1 gate-policy 準拠条件

- セキュリティ④ を含めた安定性観点が確認済み。

#### 5.8.2 PLAN 追加条件

- 運用上の `deferred` 残件を記録し、
  次の評価へ引き継ぐ。
- `L8` が本 PLAN効果を参照する。
- `G7` 判定後に `review-feedback` hook を実行し、過度な自己改善駆動（Lv1-2 連発）時の cooldown 条件を確認する。

## 6. L8 受入条件への組み込み（追加ルール）

### 6.1 追加チェック

- `G3/G4` における精度未達の `finding` が `deferred` として記録されているか。
- `deferred` に対して、
  1) 根拠 2) 再評価計画 3) 次アクション があるか。
- 未記録の精度未達が存在しないか。
- `accuracy_score` テーブルの `comment` / `evidence` から未 redacted 値が存在しないことを fixture で検証できるか。

### 6.2 判定観点

- L8 では、`deferred` を「失敗」と断定せず、
  次アクションがあるかどうかで評価。
- `deferred` がないことが絶対条件ではない。
- ただし、deferred は必ず traceability 可能であることが必須。

### 6.3 受入失敗条件（厳密）

- 精度未達が 1 件でも未記録で見過ごされた場合は fail。
- 同一 finding が `G3` と `G4` で同じ未解決として残存する場合は fail。
- 既存 PLAN への引き継ぎが存在しない場合は fail。
- `accuracy_score` の `comment` / `evidence` へ secret/PII が未 redacted で永続化される状態があれば fail。

## 7. 主要リスク

### 7.1 R-01: 改修が逆方向へ倒れる

- **リスク内容**: TL/Codex の厳しさを変えたことで、再び loop または緩和による精度低下。
- **兆候**:
  - レビューラウンド数が急増
  - 同一 finding の再指摘増加
  - `deferred` が説明なしで増加
- **対策**:
  - PLAN-002/003 で先行実証。
  - `G2` を「方向性の整合」へ限定し、
    `G3/G4` で精度検査を強化。
  - A/B比較により閾値調整。

### 7.2 R-02: `accuracy_weight` の値が恣意的

- **リスク内容**: 重み設定が経験則依存で再現しない。
- **対策**:
  - G2 で根拠提示（過去の retro / 既存成熟フレーム参照）。
  - 将来見直しフローを明文化。
  - 重みは最初の v1 では固定運用。

### 7.3 R-03: migration 競合

- **リスク内容**: PLAN-002/003 の `v8/v9` と `v10` が競合。
- **対策**:
  - PLAN-002/003 finalize 後に `PLAN-004` へ進行。
  - `cli/lib/helix_db.py` で逐次 migration を前提化。

### 7.4 R-04: accuracy_score の comment/evidence に secret/PII 混入リスク

- **リスク内容**: `accuracy_score.comment` / `accuracy_score.evidence` が redaction 無しで永続化されると、secret/PII がログ/再利用データとして残留する。
- **対策**:
  - G3 で `accuracy_score` 保存前 redaction を PLAN-002 の hash 正規化規則に準拠して実施する。
  - `accuracy_score` の `comment` / `evidence` は構造制約（長さ上限等）に留め、保存前 redaction を必須化する。
  - L8 受入では fixture で未 redacted 値を検知し、残存時は fail。

### 7.5 R-05: 5 段階フィードバックが画一化して教訓価値が下がる

- **リスク内容**: gate やロールを問わず同一フォーマットでの出力が続くことで、教訓の具体性が低下する。
- **対策**:
  - gate 種別ごとに 5 軸の weighting を分岐。
  - `cli/templates/feedback-prompt.md` に fixture を追加し、言い回しのバリエーションを固定。
  - `Lv1-2` と `Lv4-5` の指導密度を分離して、次の改善に直接効く形を維持する。

### 7.6 R-06: スコープ拡大

- **リスク内容**: 心理メカニズム逆手の倫理的・運用的リスク（過度な自己改善駆動）。
- **対策**:
  - `Lv1-2` 連発時でも builder が萎縮しないよう、建設的トーンをテンプレート固定する。
  - `Lv1-2` 連続時の cooldown 条件を hook レベルで規定。
  - `想定外作業 = なし` を維持し、境界外要件は次 PLAN へ分離。

## 8. L4 Sprint 構成

### 8.1 Sprint 1: Shared 基盤（Schema 予約）

- 目的: `helix.db v10` `accuracy_score` の DDL 設計を固定。
- 主要成果:
  - `plan_id / gate / dimension / score` の意味と制約。
  - `helix.db` の段階移行順序の前提。
- DoD:
  - DDL 方針の不変条件が文書化。
  - `PLAN-004` で依存順を明記。
  - 実行依存が明示される。

### 8.2 Sprint 2: TL prompt 分離

- 目的: `helix-plan review` と `cli/helix-gate` の layer 区別を文書化。
- 対象:
  - PLAN レビュー: 方向性
  - G2/G3/G4/G6/G7 review: 精度凍結/実装精度
- DoD:
  - 方向性と実装精度の役割が混在しない。
  - 各 gate の入力/出力観点が区別される。

### 8.3 Sprint 3: Codex review 横断

- 目的: role 横断観点で精度項目を追加。
- 対象:
  - `cli/templates/codex-review-prompt.md`（または同等の prompt 供給点）の仕様化。
  - `cli/roles/*.conf` の精度ヒント拡張方針。
- DoD:
  - role 横断で同一語彙を使用。
  - `PLAN/G3/G4` の違いが明示される。

### 8.4 Sprint 4: gate-policy 重み化

- 目的: `accuracy_weight` と採点ルールのガバナンス固定。
- 対象:
  - `skills/tools/ai-coding/references/gate-policy.md` の更新方針。
  - 今後の再調整窓口。
- DoD:
  - 変更条件（値の変更ルール）が明文化。
  - G2 根拠の説明が追加される。

### 8.5 Sprint 5: CLI 最小可視化

- 目的: `helix accuracy report` を最小仕様として明確化。
- 対象:
  - 出力フォーマットの粒度。
  - plan_id/gate/dimension 単位の集計。
  - `deferred` 検出補助。
- DoD:
  - 実装しなくてもレビュー可能な受入仕様が成立。
  - 次 PLAN の実装項目分解がしやすい。

### 8.6 Sprint 6: 実証・運用検証

- 目的: PLAN-002/003 に対して改修後 prompt 再 review。
- 対象:
  - 効果確認レポート作成
  - 学習ログ（deferred、再現率、レビュー回数）確認
- DoD:
  - 実証事実が本文に保存される。
  - 次 PLAN への引継ぎが明確。

### 8.7 Sprint 依存関係

- Sprint 1 と 2 は独立に開始可能。
- Sprint 3 は Sprint 2 の方針が安定した後に確定。
- Sprint 4 は Sprint 3/2 の成果を受けて重み運用を確定。
- Sprint 5 は Sprint 1 + 4 の前提で実施。
- Sprint 6 は 1〜5 の成果が整ってから実行。

### 8.8 Sprint 成果物一覧（PLAN だけ）

- 本PLAN本文の節内に結果記載。
- 追加の実装/設定ファイルは本 PLAN では作成しない。

### 8.9 Sprint 各項目のトレーサビリティ

- Sprint 1 → G3 `Schema Freeze`
- Sprint 2 → G2 / G3 / G4 判定差分
- Sprint 3 → G2〜G7 横断レビュー
- Sprint 4 → gate-policy 実施
- Sprint 5 → L8 report 拡張方針
- Sprint 6 → PLAN-002/003 実証

## 9. 主要トレーサビリティ（本 PLAN と他 PLAN の接続）

### 9.1 前提 PLAN

- [PLAN-002-helix-inventory-foundation.md](PLAN-002-helix-inventory-foundation.md)
- [PLAN-003-auto-restart-foundation.md](PLAN-003-auto-restart-foundation.md)

### 9.2 この PLAN 後段への受け渡し先

- [PLAN-005 運用自動化スキル群](PLAN-005-ops-automation-skills.md)
- PLAN-006/007/008/009（上流・Scrum・Reverse・Run）

### 9.2a PLAN-002/003 実証前提

- PLAN-004 G6 RC 判定は、PLAN-002/003 で 5 段階フィードバック（ユーザープロンプト）実証を前提とする。
- 実証項目: `review-feedback` hook、Lv1〜Lv5 の収束、改善度推移（`improvement_level`）。

### 9.3 参照する基準資料

- [gate-policy](../../skills/tools/ai-coding/references/gate-policy.md)
- [implementation-gate](../../skills/tools/ai-coding/references/implementation-gate.md)
- [workflow-core](../../skills/tools/ai-coding/references/workflow-core.md)
- [Role Map](../../cli/ROLE_MAP.md)
- [Documentation Skill](../../skills/common/documentation/SKILL.md)
- [API Contract Skill](../../skills/workflow/api-contract/SKILL.md)
- [Design-doc Skill](../../skills/workflow/design-doc/SKILL.md)

### 9.4 関連コマンド・対象領域

- `helix-plan review`
- `helix gate`
- `helix accuracy report`
- `helix db`
- `helix-codex`

### 9.5 本PLAN からの引き継ぎルール

- 今回の PLAN で「方向性」は凍結。
- 実装の詳細は G3 以降の実装ドキュメントまたは次 PLAN で確定。
- 参照外部 PLAN の更新要件は、本 PLAN の L8 受入レポートに追記。

## 10. 想定外作業

- なし

## 11. 未解決項目（PLAN フェーズ）

- なし

## 12. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v3 | TL レビュー P1×1 + P2×2 + P3×1 を反映、ユーザー Q3 方針（(e) ユーザープロンプト型 5 段階 feedback）を採用。G2-G7 hook、精度改善度蓄積、secret/PII redaction の app-layer 実装方針、R-05/R-06 追加、改訂履歴 v3 を追記。 | Docs (Codex) |
| 2026-04-30 | v2 | TL レビュー P1×2 / P2×1 / P3×1 を反映。`accuracy_weight` の単調増加記述を撤回し重み根拠を明文化、`PLAN-004` と `G3` 境界を G3 freeze の文言で統一、secret/PII redaction 対策（保存前 redaction / 列単位 `CHECK`）と L8 fixture 条件を追加。 | Docs (Codex) |
| 2026-04-30 | v1 | 初版。`HELIX` の評価哲学を「速度→正確・精度」へ再定義。TL/Codex prompt レイヤ分離、Codex 横断観点、`accuracy_weight`、`accuracy_score` 集約、`helix accuracy report` 設計、L8 組込条件を確定。 | Docs (Codex) |

## 13. 変更管理メモ（PLAN 目的外だが維持）

- 本 PLAN は 1 ファイルで完結。
- 本 PLAN の承認後、実装 Plan は別の PLAN か次の実装ワークで展開。
- 本 PLAN はコミットを伴わずレビュー起点としてのみ使用。

## 14. 監査向けチェックリスト（付録）

### 14.1 本 PLANの確認観点

- [ ] 1 章から 10 章までが整合している。
- [ ] 設計凍結の境界が明示されている。
- [ ] G2/G3/G4/G6/G7 の追加条件が明確。
- [ ] L8 受入条件が `deferred` と traceability を要求している。
- [ ] 主要リスクへの対策（R-01〜R-06）が示されている。
- [ ] `.helix/` 変更なし。
- [ ] `PLAN-004` の 1 ファイル新規作成に収束している。

### 14.2 本 PLANで未解決なまま残らないための記録テンプレート

- `[Gate]` 対象
- `[Finding]` 要点
- `[Evidence]` 証拠（ログ、レビュー指摘、再現手順）
- `[Action]` 次アクション
- `[Owner]` 担当者
- `[Due]` 期限
- `[Deferred]` yes/no

### 14.3 非機能的品質条件

- 仕様用語の統一: `deferred`, `precision freeze`, `accuracy_weight`, `accuracy_score`
- リンク先参照の整合確認。
- 未解決項目を残置しない。
