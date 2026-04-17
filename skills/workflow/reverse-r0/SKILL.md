---
name: reverse-r0
description: HELIX Reverse R0 証拠収集スキル。code/DB/config/ops の4軸で evidence_map を作成し RG0 通過可否を判定する
metadata:
  helix_layer: R0
  triggers:
    - R0 Evidence Acquisition 時
    - 既存コード逆引き開始時
    - evidence_map 生成時
  verification:
    - "evidence_map が docs/reverse/ に存在"
    - "coverage / confidence / unknowns が明記"
    - "4軸すべてで証拠 ≥1件"
compatibility:
  claude: true
  codex: true
---

# Reverse R0 スキル（Evidence Acquisition）

## 目的
HELIX Reverse の R0 で、
システム実態を証拠ベースで収集し、
R1 に渡せる `evidence_map` を作成する。

R0 は推測を最小化し、
`coverage / confidence / unknowns` の3指標で
証拠十分性を評価する。

---

## RG0 通過条件（正本準拠）

RG0（R0 出口）の通過条件は次の 4 点。

1. coverage 100%
2. 依存グラフ完成
3. DB スキーマ取得済み
4. unknowns cataloged

上記を 1 つでも満たさない場合は RG0 fail。

---

## 用語統一（gate-policy 準拠）

- `coverage`: 対象モジュール/対象領域の分析済み割合
- `confidence`: 各証拠/仮説の確度（high/medium/low）
- `unknowns`: 分類不能または未検証の項目

`confidence` は証拠の強さを示す。
件数の多さや実装量の多さを意味しない。

---

## 証拠収集 4軸（必須）

R0 では次の 4 軸すべてで証拠を収集する。

1. code: ソース、依存、主要エントリポイント
2. DB: スキーマ、マイグレーション、主要テーブル/制約
3. config: 環境変数、設定ファイル、feature flag
4. ops: ログ、監視、ジョブ、運用手順

各軸で最低 1 件の証拠が必要。

---

## evidence_map.yaml テンプレート

`docs/reverse/` 配下に保存する。

```yaml
evidence_map:
  generated_at: "YYYY-MM-DD"
  target: "system-or-module"
  coverage:
    overall: 100
    by_axis:
      code: 100
      db: 100
      config: 100
      ops: 100
  entries:
    - path: "src/api/auth.ts"
      kind: "code"
      source: "repository"
      confidence: "high"
      reviewed_by: "tl"
      unknowns: []
    - path: "db/schema.sql"
      kind: "db"
      source: "database-dump"
      confidence: "medium"
      reviewed_by: "dba"
      unknowns:
        - "一部テーブル用途不明"
    - path: "config/app.yaml"
      kind: "config"
      source: "runtime-config"
      confidence: "high"
      reviewed_by: "tl"
      unknowns: []
    - path: "ops/grafana-dashboard.json"
      kind: "ops"
      source: "monitoring"
      confidence: "high"
      reviewed_by: "devops"
      unknowns: []
  dependency_graph:
    status: "completed"
    artifact: "docs/reverse/dependency-graph.md"
  db_schema:
    status: "acquired"
    artifact: "docs/reverse/db-schema.md"
  unknowns_catalog:
    - id: "UNK-001"
      item: "legacy batch の実行条件"
      owner: "tl"
      next_action: "R1 で契約抽出時に追跡"
```

必須キー:

- `path`
- `kind`
- `source`
- `confidence`
- `reviewed_by`
- `unknowns`

---

## 信頼度評価の優先順位（重要）

信頼度の高さは次を基準とする。

`本番ログ > 設定 > コード > DB > テスト`

これは「証拠の信頼度順」であり、
**収集順序ではない**。

実務では収集容易性に応じて順番を入れ替えてよいが、
評価時は上記順位で確度を判定する。

---

## tools/web-search 連携

不足情報が外部仕様に依存する場合は
`tools/web-search` で一次情報を補完する。

用途例:

- 外部 API の実際の挙動確認
- OSS 既知仕様/既知制約の確認
- 廃止済み設定の真偽確認

注意:

- 収集した URL は evidence_map か補助メモに記録する
- 社内機密情報をクエリへ含めない

---

## R1 引き渡し契約

R0 から R1 へは以下を満たして引き渡す。

- `evidence_map` が `docs/reverse/` に存在
- `coverage / confidence / unknowns` が明示
- 依存グラフ成果物の参照先がある
- DB スキーマ成果物の参照先がある
- 4軸すべてで証拠が 1 件以上ある

R1 はこの成果物を入力として
API/DB/型の観測契約抽出へ進む。

---

## 実行手順（推奨）

1. 対象境界を定義（システム/モジュール）
2. 4軸ごとに証拠収集
3. 依存グラフを作成
4. DB スキーマを取得
5. unknowns を catalog 化
6. evidence_map を出力
7. RG0 通過判定

---

## エスカレーション基準

以下は人間確認にエスカレーションする。

- 本番影響のある調査操作が必要
- 認証・決済・個人情報・ライセンスに関与
- DB 実体へ破壊的アクセスが必要
- unknowns が多く RG0 判定不能

提出物:

- evidence_map
- 未解決 unknowns 一覧
- 推奨する次アクション

---

## RG0 判定チェック（実務用）

- coverage 100%
- 依存グラフ完成
- DB スキーマ取得済み
- unknowns cataloged
- docs/reverse/ に evidence_map が存在
- 4軸（code/DB/config/ops）で各 1 件以上の証拠あり

R0 の完了条件は「読んだ量」ではなく、
「証拠網羅を再現可能な形で残せたか」。
