# PLAN-008: Reverse 5系統化（フルバック追加・設計 Reverse） (v2)

## 1. 目的 / Why

既存 `workflow/reverse-analysis` は現在、`Code から設計復元` の 1 系統（R0-R4）を中心に据えた復元ワークフローとして機能している。

`PLAN-008` は、運用上発生している 3 種類の設計ズレ・再構成ニーズを吸収するため、Reverse を 5 系統化し、実装前後の状態差を同じ実行基盤上で扱えるようにする。

追加する 5 系統は以下。

- Code 復元 Reverse（既存）: 設計書なしレガシーコードから現行設計を復元し、Forward へ接続する。
- バージョンアップ Reverse（新）: 次版実装予定を前提に、現行設計から実装上の想定差分を逆引きし、設計前提と移行計画の起点を作る。
- ノーマライゼーション Reverse（新）: 実装と設計の乖離（drift）を前提に、実装実態を起点として設計を再正規化する。
- フルバック Reverse（新）: 実装完了後に設計と文書を最終整合化し、管理ドキュメントとして成立する状態へ戻す。
- 設計 Reverse（新）: 既存設計書群から依存関係を逆引きし、実装順序（topological sort）と並列実装可能ペアを自動算出する。

## 2. スコープ

### 2.1 含む

- Reverse の処理系を `helix reverse <type>` で拡張し、5 系統の共通入口を持つ。
- 各系統の `Input / Output / 成功条件` を定義し、R0-R4 の既存成果物と RGC への接続を明文化。
- PLAN-004/006/007/009 への接続点を定義し、特に L9-L11 の後段設計整合に対する文脈を追加する。
- `フルバック` を R1-R4（As-Is 復元）と対になる前向き整理フローとして位置づける。

### 2.2 含まない

- 既存 Reverse スキル（reverse-r0/r1/r2/r3/r4/rgc）の具体実装変更。
- API/DB/スキーマの破壊的変更設計。
- 実装コードやテスト追加。
- 本ファイル範囲外の CLI コマンド本体実装。

## 3. 採用方針

### 3.1 5 系統の定義

#### 3.1.1 Code 復元 Reverse（既存）

- 入口: `helix reverse code`
- 観測: 設計書なしの既存コード・設定・運用実態
- 出力: R0→R4 の As-Is 生成物（Evidence / 契約 / ADR仮説 / GAP + Forward）
- 目的: 実装の正しさ検証を前提に、まず現状を仕様化して Forward に接続

#### 3.1.2 バージョンアップ Reverse（新）

- 入口: `helix reverse upgrade`
- 観測: 現行実装・運用制約・既知の障害情報・対象バージョン方針
- 出力: バージョン差分前提書（移行前提、破壊的変更候補、移行ゲート推奨）
- 目的: 将来実装前に「差分の見積もりと受け入れ条件」を作る。

#### 3.1.3 ノーマライゼーション Reverse（新）

- 入口: `helix reverse normalization`
- 観測: 実装 drift（実績と設計文書の不一致箇所）
- 出力: 設計再構成提案（更新必要セクション、依存優先順位、設計更新TODO）
- 目的: 実装差分吸収のための設計自己修正を設計側で先行完了。

#### 3.1.4 フルバック Reverse（新）

- 入口: `helix reverse fullback`
- 観測: `完了実装 + 既存設計 doc + 変更履歴`
- 出力: `management docs` の最終整合版（更新済みの PLAN/D-*/ADR と監査可能な差分履歴）
- 目的: 実装完了後の設計/文書不整合を解消し、L8 受入〜L11 検証側面を再固定する。

#### 3.1.5 設計 Reverse（新）

- 入口: `helix reverse design`
- 観測: `docs/plans/*.md`, `docs/design/D-*.md`, `docs/features/*/D-*.md` などの既存設計書群
- 出力: 依存 DAG（機械可読 YAML / Mermaid 図）、実装順序（topological sort, PLAN ID / D-* 単位）、並列実装可能ペア
- 対応 D-*: `D-DESIGN-DAG`（依存 DAG）, `D-IMPL-ORDER`（実装順序）
- 目的: 既存設計資産から実装順序を抽出し、PLAN-006 からの forward 構築を補完する。

### 3.2 共通基盤としての R0/R4/RGC 再利用

- **R0**（観測収集）を全系統の入り口前提として再利用する。
  - 対象証拠: `evidence map`, 実装ログ, 設計資産, 運用観測
- **R4**（Gap & Routing）を全系統の出力統合点として再利用する。
  - 差分の振り分け先（Forward/Backward）を共通ルールで集約。
- **RGC**（Gap Closure）を最終整合品質チェックとして接続する。
  - 特にフルバックでは、RGC で未解消項目を減らし、再発防止記録を残す。

### 3.3 系統別 I/O・成功条件

- Code 復元 Reverse
  - **Input**: 既存コード、設定、DB スキーマ断片、運用観測
  - **Output**: R1〜R4 成果物、Forward ルーティング
  - **成功条件**: 設計復元観測が明示的な信頼度で接続可能（最低95%トレーサビリティ）

- バージョンアップ Reverse
  - **Input**: 現行設計、移行目標、既知制約、既存依存
  - **Output**: 変更影響一覧、移行シーケンス、互換性判定
  - **成功条件**: 破壊変更を事前分類し、各移行ステップに検証条件が紐付く

- ノーマライゼーション Reverse
  - **Input**: 直近実装、現行設計、差分履歴
  - **Output**: 設計再正規化提案、優先順位付き是正アクション
  - **成功条件**: drift の再発リスクを低減する設計更新計画が定義される

- フルバック Reverse
  - **Input**: 完了実装、既存設計 doc、開発中変更履歴
  - **Output**: 整合済み管理文書（PLAN/ADR/D-API/D-CONTRACT/D-HANDOVER）
  - **成功条件**: 実装状態と文書状態が相互追跡可能で、L8/L9-L11 の受入条件に接続できる

- 設計 Reverse
  - **Input**: 既存設計書群（`docs/plans/*.md`、`docs/design/D-*.md`、`docs/features/*/D-*.md`）
  - **Output**: 依存 DAG（YAML / Mermaid）、実装順序（topological sort、PLAN ID / D-* 単位）、並列実装可能ペア
  - **成功条件**: 依存抽出が監査可能で、循環依存の検知・分割ルールに接続される

### 3.4 CLI `helix reverse <type>` の type 拡張

- 追加型: `code | upgrade | normalization | fullback | design`
- デフォルト継続: `code`
- 既存挙動（`reverse-r*` 系）は内部ルーティングとして吸収し、表示結果に `reverse_type` を明示。
- 例:
  - `helix reverse code`
  - `helix reverse upgrade --from <ver> --to <ver>`
  - `helix reverse normalization --target drift`
  - `helix reverse fullback --artifact <path>`
  - `helix reverse design --plans docs/plans/ --design docs/design/ [--output dag.yaml]`
  - `helix reverse design --plans docs/plans/ --topological-sort`

## 4. 関連 PLAN

- `docs/plans/PLAN-004-pm-reward-design.md`
  - `L1 / 設計前提` と `G2/G3/G4 の受け渡し条件` を前提として反映。
- `docs/plans/PLAN-006-upstream-meta-phase.md`
  - メタフェーズにおける前提解像度とドキュメント依存管理を継承。
  - `設計 Reverse` は PLAN-006 の forward 構築を reverse 補完し、`D-DESIGN-DAG / D-IMPL-ORDER` を相互参照。
- `docs/plans/PLAN-007-scrum-multitype-trigger.md`
  - 差し込み条件と Q5 トリガーの思想を、4 系統の例外処理・遅延処理に接続。
- `docs/plans/PLAN-010-verification-agent.md`
  - 設計 Reverse の依存 DAG から `cross-validation` 対象ペアを自動列挙する連携を追加。
- `docs/plans/PLAN-009-?`
  - フルバック後段（デプロイ後工程）の接続先として参照。現時点では案内先不在（未作成）。

## 5. リスク

- フルバック工数膨張
  - 対策: 実施対象を `Sprint` 単位に分割し、I/O と成功条件を `exit criteria` 化。
- バージョンアップ Reverse の影響面見落とし
  - 対策: 互換性カテゴリ（互換/保守/破壊）を前提評価に必須化し、移行シナリオを分離記録。
- 4 系統運用時の責務境界混線
  - 対策: 各 type の入出力と最終成果物を固定し、R0-R4-RGC の共通出口で再統合。
- 逆引き誤判定
  - 対策: 人手レビュー（docs/verification）と PO 依存前提の明示的再確認を強制。
- 設計 Reverse 特有: 既存設計書の記述揺れによる DAG 誤検出
  - 対策: 参照表現の同義語正規化、低信頼度検出の再確認ループを追加。
- 設計 Reverse 特有: 循環依存の検出と解消手順不足
  - 対策: SCC 分解手順と再実行順序定義を D-IMPL-ORDER に明示。
- 設計 Reverse 特有: 頻繁な再生成コスト
  - 対策: 差分再生成、キャッシュ、再生成頻度ガードを設計運用として明文化。

## 6. Sprint 計画概要（L1〜L4）

### Sprint L1

- 5 系統定義の最終確定
- `helix reverse <type>` 入力/出力仕様の固定
- 既存 `workflow/reverse-analysis` との接続ポリシー更新

### Sprint L2

- バージョンアップ Reverse とノーマライゼーション Reverse の観測テンプレート整備
- 設計 Reverse の設計書抽出ルール（識別子正規化/同義語）整備

### Sprint L3

- フルバック Reverse の成功条件検証（実装完了前提）
- 進捗/例外の監査ログ設計
- PLAN-004/006/007/010 への接続イベント定義

### Sprint L4

- 5 系統を通した `L1〜L11` 受入連携レビュー
- 運用ガイドラインと実施可否境界の確定

## 7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v1 | Reverse 4 系統（Code/Upgrade/Normalization/Fullback）定義を追加し、フルバック Reverse を L8↔L11 区間の管理整合プロセスとして定義。 | Docs (Codex) |
| 2026-05-01 | v2 | 設計 Reverse を第5系統として追加。PLAN-006 補完関係、PLAN-010 連携、CLI `design` type、および `D-DESIGN-DAG / D-IMPL-ORDER` を明示。 | Docs (Codex) |
