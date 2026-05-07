> 目的: L3 D-API / D-CONTRACT 凍結時に「骨格をどう機械可読 schema (JSON Schema / Pydantic / Zod) に落とすか」で迷うときに開く。前段・後段の型契約を単一ソースに揃える起点。

# [07] スキーマ導出

## 前提となるスキル

- [02] 骨格選択・新規定義
- [06] 出力の指定

## 適用判定

- 骨格と特徴定義を機械可読スキーマに変換する時
- 前段と後段の共通契約を定義する時
- マルチテナント・マルチユースケースで型契約を共有する時

## 担当する判断

骨格と特徴定義から、機械可読スキーマ（JSON Schema / Pydantic / Zod / TypeSpec等）を導出する。

## 中核原則

スキーマは独立に設計するものではなく、骨格から機械的に導出する。骨格の各要素がスキーマのフィールドに対応し、特徴定義がスキーマの制約に対応する。

スキーマは前段と後段の両方から同一定義を参照する。重複定義しない。

## 判断軸

### 軸1：どのスキーマ形式を使うか

```
実装環境は何か？
├── TypeScript/JavaScript → Zod / TypeBox
├── Python → Pydantic
├── 言語非依存 → JSON Schema
├── API契約 → OpenAPI / TypeSpec
└── データベース連携 → SQL DDL + アプリ層スキーマ
```

### 軸2：制約をどこまで表現するか

スキーマで表現できる制約：

- **型**：string / number / boolean / array / object
- **必須/任意**：required / optional
- **列挙値**：enum
- **パターン**：pattern（正規表現）
- **範囲**：min / max / minLength / maxLength / minItems / maxItems
- **入れ子**：ネスト構造（骨格の階層に対応）

```
特徴定義をどこまでスキーマに落とすか？
├── 型・必須・列挙値 → 必ずスキーマに表現
├── 範囲制約 → 数値・文字数・件数があるなら表現
├── パターン → 文字列形式（メール・URL等）があるなら表現
└── トーン・スタイル → スキーマでは表現不可、プロンプトで縛る
```

### 軸3：階層構造の表現

```
骨格は入れ子構造を持つか？
├── Yes → スキーマもネスト構造で表現
│   例：PREP の Point の中身を SDS で書く場合、
│       point: { summary: string, detail: string, summary_restated: string }
└── No → フラット構造
```

## 導出マッピング

骨格から機械可読スキーマへの基本マッピング：

| 骨格・特徴定義の要素 | スキーマでの表現 |
|---|---|
| 骨格の要素名 | フィールド名 |
| 必須要素 | required |
| 自由文 | type: string |
| 箇条書き | type: array, items: string |
| 数値 | type: number |
| 列挙的な値 | enum |
| 文字数の上下限 | minLength / maxLength |
| 件数の上下限 | minItems / maxItems |
| 形式（メール等） | pattern |
| 入れ子構造 | ネストオブジェクト |

## スキーマ管理の原則

- 単一ソース管理：スキーマは1箇所で定義し、前段・後段の両方から参照
- バージョニング：スキーマ変更は明示的にバージョン管理
- 共有可能性：マルチテナントなら共通スキーマと差分スキーマを分離

## 適用手順

1. スキル02の骨格と階層構造を確認
2. スキル06の特徴定義を確認
3. 実装環境に応じたスキーマ形式を選択
4. 骨格の各要素をフィールドに変換
5. 特徴定義を制約として落とし込む（type / required / enum / pattern / min / max）
6. 階層構造があればネスト構造で表現
7. 単一ソースとしてスキーマファイルを作成
8. 前段・後段の両方から参照可能な形で配置

## スキーマ例（Pydantic）

```python
from pydantic import BaseModel, Field
from typing import List

class PREPOutput(BaseModel):
    point: str = Field(..., max_length=100, description="主張、1文")
    reason: str = Field(..., min_length=50, description="主張の根拠")
    examples: List[str] = Field(..., min_items=2, max_items=5, description="具体例")
    conclusion: str = Field(..., max_length=100, description="結論の再述")
```

## アンチパターン

- スキーマを骨格と独立に設計している
- スキーマ定義が前段と後段で別々に書かれている（単一ソースで共有していない）
- スキーマで表現可能な制約（enum / required / pattern等）を書かずに、後段の if 文で書いている
- 特徴定義をすべてスキーマに落とそうとしている（トーン等は表現不可）
- 階層構造があるのにフラットスキーマで済ませている

## 成果物

- 機械可読スキーマ定義（単一ソース）
- 前段で参照するためのアクセス手段
- 後段で参照するためのアクセス手段
- バージョン管理方針

これが揃えば、スキル08（前段の生成制約）に進める。
