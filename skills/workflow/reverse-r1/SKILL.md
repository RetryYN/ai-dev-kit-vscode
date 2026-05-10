---
name: reverse-r1
description: HELIX Reverse R1 Observed Contracts 抽出スキル。API・DB・型の機械抽出 + characterization tests
metadata:
  helix_layer: R1
  triggers:
    - R1 Observed Contracts 時
    - API/DB/型の機械抽出時
    - characterization tests 生成時
    - 契約抽出時
  verification:
    - "API endpoint 一覧が docs/reverse/api-contract.md に存在"
    - "characterization tests が pass する"
compatibility:
  claude: true
  codex: true
---

# Reverse R1: Observed Contracts

> 目的: R0 の証拠を入力に、観測可能な契約（API/DB/型）を機械抽出して検証可能な契約セットに固定する。

## 適用タイミング
- Reverse フローで R0 を完了し R1 に入る時
- API/DB/型の実態をコード起点で再構成する時
- characterization tests で主要パスの現行挙動を固定したい時

---

## R1 の目的

R1 の目的は「観測契約の抽出」であり、仕様策定ではない。
- API: 実装に存在する endpoint、method、request/response を抽出
- DB: テーブル、カラム、制約、リレーションを抽出
- 型: FE/BE/DB の型対応を抽出
- 検証: characterization tests で抽出契約との整合を確認

出力は `observed_contracts` と `r1_gaps` で管理し、次層（R2）で設計復元に使用する。

---

## RG1 通過条件

`gate-policy.md §Reverse ゲート` 準拠で、以下を満たすこと。
- API/DB/型の抽出 coverage が 90% 以上
- confidence `high` が 80% 以上
- 主要パスの characterization tests 実行済み
- 未解決 contradictions が 0

Fail 時の標準対応。
- confidence `low` の契約に追加証拠を紐付ける
- 機械抽出器の再実行（対象範囲を限定して再抽出）
- 抽出結果と実行結果の不一致を `r1_gaps` に記録

---

## 入力契約（R0 からの引き継ぎ）

R1 は R0 成果物 `evidence_map` を必須入力とする。

最低限必要な入力項目。
```yaml
evidence_map:
  modules: []
  db_schema: {}
  runtime_topology: {}
  unknowns: []
```

入力検証チェック。
- `modules` に対象スコープが 100% 含まれる
- DB 実体へ到達可能（DDL/マイグレーション/接続設定）
- API 実装の探索起点（router/controller/handler）が特定済み
- unknowns が未分類のまま放置されていない

---

## API 抽出手順

### 1. OpenAPI 生成

実装フレームワークの標準手段で OpenAPI を生成する。
- FastAPI: `/openapi.json` or `app.openapi()`
- Spring: springdoc-openapi
- Express/NestJS: swagger plugin / decorators

成果物。
- `docs/reverse/api-contract.md` に endpoint 一覧を正規化して記録
- 可能なら `docs/reverse/openapi.generated.json` を保存（任意）

### 2. Swagger 吸出

既存運用環境に Swagger UI/JSON がある場合は優先して取得する。
- `/swagger`, `/swagger-ui`, `/v3/api-docs`, `/openapi.json` を探索
- 実装由来 OpenAPI と差分比較する

### 3. grep endpoint

OpenAPI 非対応または不完全な場合の補完手順。
- `rg` で router 宣言・HTTP メソッド呼び出しを抽出
- path parameter、auth middleware、version prefix を併記
- 内部 API（`/internal` 等）を分離記録

例。
```bash
rg -n "(get|post|put|patch|delete)\(|router\.|@Get\(|@Post\(" src/
```

---

## DB スキーマ抽出

抽出対象。
- テーブル、カラム型、NULL 制約、PK/FK、UNIQUE、INDEX
- migration 履歴と現行実体の差分
- コード未参照カラム、暗黙デフォルト、論理削除フラグ

手順。
1. migration/DDL から宣言スキーマを取得
2. 実 DB から実体スキーマを取得（可能な場合）
3. ORM 定義と照合して `schema_drift` を抽出
4. `docs/reverse/api-contract.md` に DB 契約章を追記

---

## 型抽出

対象。
- API 入出力 DTO
- DB モデル（ORM entity / schema）
- FE 側利用型（存在する場合）

手順。
1. 型定義を自動抽出して一覧化
2. FE→BE→DB の対応マップを作成
3. Nullable/Optional/Enum の不一致を `type_drift` で記録

成果物テンプレート。
```yaml
type_alignment:
  fe_be_match: 0
  be_db_match: 0
  mismatches: []
```

---

## Characterization Tests 生成方針

目的は「理想仕様の担保」ではなく「現行挙動の固定」。
- 主要ユースケースを優先して Golden Master を生成
- 副作用（DB更新、外部API呼び出し）を観測可能にする
- flaky を避けるため時刻・乱数・外部I/O を固定
- 失敗時は実装修正より先に契約再評価を行う

---

## 出力フォーマット

R1 の標準出力。
```yaml
observed_contracts:
  api: {}
  db: {}
  types: {}
r1_gaps: []
```

ドキュメント出力。
- `docs/reverse/api-contract.md`（必須）
- 必要に応じて抽出ログを `docs/reverse/evidence/` に保存

---

## R2 への引き渡し

R2 に渡す最小セット。
- `observed_contracts`（API/DB/型 + confidence）
- `r1_gaps`（undocumented_endpoint / schema_drift / type_drift）
- characterization tests 実行結果（pass/fail と失敗理由）

引き渡し契約。
- R2 は R1 契約を前提として As-Is 設計を復元する
- R2 で契約矛盾を発見した場合は R1 に差し戻し可能
- 差し戻し時は対象契約 ID と根拠証拠を必ず添付する

---

## チェックリスト

```text
[ ] R0 evidence_map を入力として受領済み
[ ] API endpoint 一覧が docs/reverse/api-contract.md に記載済み
[ ] DB スキーマ抽出（宣言/実体）差分を記録済み
[ ] 型対応マップ（FE/BE/DB）を記録済み
[ ] characterization tests が主要パスをカバー
[ ] contradictions 未解決 0
[ ] RG1 判定結果を記録済み
[ ] R2 引き渡しパッケージを作成済み
```

## type 別 operational notes

| type | phase-specific action | skip / gate note |
|---|---|---|
| code | OpenAPI/DB 抽出を実施 | RG1 必須 |
| design | (skip) | RG1 不要、R2 へ直行 |
| upgrade | version diff の影響分析 | RG1 必須 |
| normalization | (skip) | RG1 不要、R2 で drift map |
| fullback | 文書 gap の抽出 | RG1 必須 |

## 機械抽出ツールチェーン

R1 で観測契約を抽出するための具体ツール選択肢。

### API 抽出
- FastAPI / Express / Spring などフレームワーク内蔵の OpenAPI generator
- 既存 swagger / OpenAPI spec があればそれを正本に補完
- swagger-jsdoc (Express)、drf-yasg (Django REST)、springdoc-openapi (Spring)

### DB 抽出
- PostgreSQL: `psql -d <db> -c '\d+'`
- MySQL: `SELECT * FROM INFORMATION_SCHEMA.COLUMNS`
- SQLite: `sqlite3 <db> '.schema'`
- ORM introspection: SQLAlchemy reflect、Prisma db pull、Sequelize sequelize-auto

### 型抽出
- TypeScript: `tsc --emitDeclarationOnly --outDir types/`
- Python: pyright (型情報抽出 JSON)、`mypy --reveal-locals`
- Java: javadoc / JSON Schema generator
- Rust: `cargo expand` / `rustdoc --output-format json`
- Go: `go doc -all <package>`

### 選択基準 (decision tree)

```text
既存の OpenAPI / Swagger spec がある?
├─ YES → spec を正本にして observed_contracts へ写経
└─ NO
   └─ monorepo か?
      ├─ YES → 言語別 extractor を順次実行 (API は OpenAPI、DB は ORM、型は言語別)
      └─ NO
         └─ 言語混在?
            ├─ YES → API は OpenAPI、型は言語別
            └─ NO → 単一言語の標準 introspection (例: TypeScript なら tsc)
```

### 制約
- 機械抽出は public な signature 中心。internal helper / runtime-only 契約は別手段 (R2 で人手補完)
- 抽出結果と実行時挙動の不一致は `r1_gaps` に記録 (RG1 通過条件)

## helix code 連携

R1 observed_contracts の補完と矛盾検出に helix code を活用する。

### 利用パターン

| コマンド | 目的 | R1 での使い方 |
|---|---|---|
| `helix code find "<keyword>"` | 類似実装検索 | observed_contracts への evidence link 補強 |
| `helix code dup --threshold 0.85` | 重複検出 | 同一契約の重複定義を r1_gaps として事前検出 |
| `helix code show <id>` | symbol 詳細表示 | API endpoint / DB column の実装位置確認 |
| `helix code stats --by since` | 変更頻度分布 | 直近変更が多い契約を high-risk としてマーク |

### 制約
- `helix code find` は keyword match、意味的類似性は別途人手で確認
- monorepo の場合は `--domain` 指定で範囲を絞る
- 抽出済 OpenAPI spec があるなら spec を正本に、helix code は補完用

### 例: API endpoint 抽出後の補強
```bash
helix code find "login"        # auth 関連 symbol を列挙
helix code dup --threshold 0.85 --domain api/auth   # 重複定義の検出
```
