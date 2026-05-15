# V-model semantics 仕様（`vmodel-semantics.yaml`）

## 概要

本書は `cli/config/vmodel-semantics.yaml` の利用者向け仕様を定義する。
4 drive × 5 layer の設計/テスト/ペア構造を、`helix vmodel` と `helix gate --subgate functional_freeze`
の実装整合で運用するための公式説明である。

## 参照正本

- 実装: `cli/lib/vmodel_loader.py`
- CLI: `cli/helix-vmodel`
- ゲート連携: `cli/helix-gate`
- 近接設計: `docs/v2/B-design/vmodel-semantics-spine.yaml`
- 要件: `docs/v2/L1-REQUIREMENTS.md`（AC-16）

## ファイル位置

- 利用実体: `cli/config/vmodel-semantics.yaml`（約 823 行）
- 設計参照: `docs/v2/B-design/vmodel-semantics-spine.yaml`

本仕様は実装（Loader + CLI）を正本とし、本文上のサンプルは理解支援用とする。

## 1. YAML 構造
\n
トップレベルは次の 3 項目を持つ。
\n
- `schema_version`\n- `spine`\n- `lifecycle`\n\n
```yaml
schema_version: 1
spine:
  drives:
    - be
    - fe
    - db
    - fullstack
  layers:
    planning:
      code:
        kind: code
      test:
        kind: test
    requirement:
      code:
        kind: code
      test:
        kind: test
    architecture:
      code:
        kind: code
      test:
        kind: test
      pair:
        kind: pair
    detailed:
      code:
        kind: code
      test:
        kind: test
      pair:
        kind: pair
    functional:
      code:
        kind: code
      test:
        kind: test
      pair:
        kind: pair
lifecycle:
  - mock_to_implementation
  - production_handoff
```
\n
`schema_version` は Loader により検証され、現行実装は `1` 専用。

## 2. drives / layers

### 2.1 drives

利用可能ドライブ:
\n
- `be`（backend）\n
- `fe`（frontend）\n
- `db`（database）\n
- `fullstack`（横断）

### 2.2 layers

```text
planning -> requirement -> architecture -> detailed -> functional
```

- `planning`/`requirement`: 主に初期整合、要件抽出\n
- `architecture`/`detailed`/`functional`: design + test + pair の3 sibling を持つ。

## 3. 4 drive × 5 layer の設計モデル
\n
実装上、ドライブごとに 5 layer を持ち、各 layer は種類別ノードを持つ。\n\n
### 3.1 design / test / pair の 3 sibling\n+\n+#### design
\n+- 設計タスク/成果物参照を記述。\n- `code` 系の実装エントリ。\n
#### test
\n+- テスト観点・設計観点を接続。\n+- `pair` が成立するための前段要件。\n
#### pair
\n+- design/test の接続関係を明示。\n+- 以下が必須:\n
  - `horizontal_rule`\n  - `vertical_from`\n  - `vertical_to`\n  - `score_weight`\n  - `promotion`\n
各 pair は一意キー下で `layer` と drive 両方に紐づく。

### 3.2 4 drive × 5 layer の規模感
\n
`planning`, `requirement` は `design/test` が中心。\n`architecture` 以降 `pair` が必須構成に近づき、`pair` 不備は `helix gate --subgate functional_freeze` に影響。\n
## 4. `pair` フィールド仕様
\n
### 4.1 `horizontal_rule`\n
`required` / `optional` / `conditional` の 3 値 enum として定義される (`docs/v2/B-design/vmodel-semantics-spine.yaml:118` の `pair.allowed.horizontal_rule` を正本採用)。\n

- `required`: 同層の横方向連携を必須化し、未接続なら fail-close
- `optional`: 横方向連携は任意 (記録不要)
- `conditional`: drive / size / lifecycle 等の条件付きで required になる

旧版で Boolean (true/false) として記述されていた箇所は本 enum の `required` / `optional` に対応する。

### 4.2 `vertical_from` / `vertical_to`\n
上下レイヤーの参照キー。\n\n
`vertical_from` は起点、`vertical_to` は接続先。\n- from/to は同 drive 内の layer/entry を参照。\n- 参照先不存在は validate fail 対象。\n\n
### 4.3 `score_weight`\n
数値（float）。pair の重み付け。\n\n
`0.0` 未満や文字列は禁止（実装で型/値検証）。\n
### 4.4 `promotion`\n
次フェーズへの接続定義。配列またはオブジェクト。
\n\n
例:\n+
```yaml
promotion:
  to:
    - be/functional/pair/foo
    - be/test/bar
```
\n
### 4.5 `pair_test_levels`\n
`design/test` の接続に対して許可されるテストレベル集合。\n- `unit`\n- `integration`\n- `system`\n
未定義時は運用規約でデフォルト縮退を許可しない構成を推奨。\n\n

### 4.6 `fixture_set` 命名規約\n
`*_fixture_set` ファミリーは以下の親子関係を持つ。\n
\n+| family | parent | 用途 |\n+|---|---|---|\n+| `contract_fixture_set` | (root) | drive 共通の契約レベル fixture |\n+| `api_fixture_set` | extends `contract_fixture_set` | BE API テスト用 contract 派生 |\n+| `ui_contract_fixture_set` | extends `contract_fixture_set` | UI 契約テスト用 contract 派生 |\n+
派生 fixture は親 fixture の互換性を維持する。\n
fixture 名は `<scope>_fixture_set` の snake_case 形式で揃える。\n
## 5. `mock_to_implementation` lifecycle\n+\n+`lifecycle` のデフォルト集合として `mock_to_implementation` がある。\n+
この経路では:
\n
- mock 段階から実装段階へ遷移する。\n- `g2_evidence_preserved` が基本原則。\n- 破壊的な再生成はしない（append-only）を推奨。\n\n
`g2_evidence_preserved` は `AC-16` 要件との整合上、証跡保持要件を担保する。\n\n
## 6. `schema_version` とバリデーション\n+\n+`vmodel_loader.py` は以下を検証:
\n
1. `schema_version` は整数かつ `1`\n2. `spine.drives` が設定されている\n3. `lifecycle` が空でない\n4. pair の必須キー存在\n5. `drives` と `layers` の参照整合\n\n
検証時の典型エラー:\n+\n+- `schema_version` mismatch\n- pair の必須キー不足\n- 不明な drive/layer\n- 存在しないキーへの参照\n\n
## 7. ローダ API (`cli/lib/vmodel_loader.py`)

### クラス構造

- `VModelLoader`: YAML パース、キャッシュ、クエリ API を提供。\n
  - `load()`\n  - `validate()`\n  - `get_spine()`\n  - `get_drives()`\n  - `get_drive(drive)`\n  - `get_layer(drive, layer)`\n  - `get_item(path)`\n\n
### API 連携の実用
\n
`helix vmodel` コマンドは本ローダ経由で以下を実行:
\n
- `list`: `get_drives/get_layer` 経由で表示\n- `show`: `get_item` 経由で詳細取得\n- `validate`: `validate` の結果を CLI に返却

## 8. 実際の入力例
\n
### 8.1 ドライブ別 layer 参照
\n
```bash
# 全体俯瞰
helix vmodel list
\n# 特定 key の確認
helix vmodel show be/functional/pair/xx --drive be
```\n
### 8.2 セマンティクス検証
\n
```bash
helix vmodel validate --json
```
\n
出力例:\n+
```json
{
  "verdict": "passed",
  "errors": [],
  "schema_version": 1,
  "drives": 4,
  "layers": 5
}
```

## 9. ドライブ/レイヤーガイダンス（設計者向け）
\n
### be\n
- API 境界、ドメイン設計、データアクセスの仕様準拠性を重視。\n
### fe\n
- UI 状態遷移と API 呼び出し仕様の整合。\n
### db\n
- テーブル制約、マイグレーション、fixture まで含む。\n
### fullstack\n
- be/fe/db 横断のインターフェース整合とデプロイ境界。\n

### layer 方針
\n
- planning: 進め方と責務分解\n
- requirement: 監査要件と合意条件\n
- architecture: 全体構造\n
- detailed: 実装分割設計\n
- functional: 受け入れ可能状態、pair 集約点\n
## 10. gate 連携（重要）

`helix gate --subgate functional_freeze` は vmodel 仕様と連携する。

- 判定対象は `functional` レイヤー上の `pair`。\n
- `drive=be/fe/db/fullstack` が対象。\n
- pair の `score_weight` / `promotion` / `pair_status` が状態として反映される。\n
欠落は `pair_count=0`、不一致は `failed` へ影響しうる。

## 11. 参照リンク（relative）
\n
- [../commands/vmodel.md](../commands/vmodel.md)\n
- [../commands/gate.md](../commands/gate.md)\n
- [../B-design/v21-migration-sql-draft.sql](v21-migration-sql-draft.sql)\n
- [../B-design/helix-db-v21-spec.md](helix-db-v21-spec.md)\n
- [../../cli/helix-vmodel](../../cli/helix-vmodel)\n
- [../../cli/lib/vmodel_loader.py](../../cli/lib/vmodel_loader.py)\n
## 12. 運用チェックリスト\n+\n
- [ ] `schema_version` が 1\n
- [ ] drives は `be fe db fullstack` を満たす\n
- [ ] 各 drive の functional 層で design/test/pair が揃う\n
- [ ] pair の必須キーが全件揃う\n
- [ ] `mock_to_implementation` が参照されている\n
- [ ] `helix vmodel validate` が成功\n
- [ ] `helix gate --subgate functional_freeze` で合格\n\n
## 13. 変更時の注意\n+\n
本仕様変更は契約・設計変更に該当しうるため、`\n`AC-16`, ゲートルール、vmodel loader のテストを更新してから反映する。\n
## 14. 付録: 簡易サンプル（抜粋）
\n
```yaml
schema_version: 1
spine:
  drives:
    - be
    - fe
    - db
    - fullstack
  layers:
    functional:
      design:
        architecture:
          id: functional_design_base
      test:
        architecture:
          id: functional_test_base
      pair:
        architecture:
          horizontal_rule: required
          vertical_from: detailed
          vertical_to: architecture
          score_weight: 1.0
          promotion:
            to:
              - be/functional/pair/x
          pair_test_levels:
            - unit
            - integration
lifecycle:
  - mock_to_implementation
  - g2_evidence_preserved
```
\n
## 15. 変更履歴\n+\n
- v1.0: HELIX V2 Phase2 として追加。\n
