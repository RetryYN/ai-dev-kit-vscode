# Review Axes Detail Design (FR-VD05/06)

Status: draft review
Scope: docs/v2/B-design/review-axes-detail.md
Source: docs/v2/L1-REQUIREMENTS.md, docs/v2/B-design/vmodel-semantics-spine.yaml
Related: vmodel-semantics-{drive}-draft.yaml, helix qa pair-check, helix gate --pair-check
Version: draft-0.1.0
Created: 2026-05-14

## 0. 目的 / 前提

本書は、FR-VD05（縦軸 review）と FR-VD06（横軸 review）を **実装可能レベル** で定義し、実際の検証器（CLI / schema / detector / record）実装と接続できる形式へ落とし込むことを目的とする。  

対象は `docs/v2/L1-REQUIREMENTS.md` の FR-VD05/06 と、`docs/v2/B-design/vmodel-semantics-spine.yaml` の `design.required` / `test.required` / `pair.required` を実装前提とした設計レビュー構造である。

想定前提:

- `contract_entries`, `test_design_entries`, `design_review`, `test_baseline` は `plan_id` で横断管理される。
- drive は `be / fe / db / fullstack`。
- layer は `planning / requirement / architecture / detailed / functional`。
- `pair` は既定で `vertical_from` / `vertical_to` / `horizontal_rule` / `score_weight` / `promotion` を持つ。

対象検出軸:

1. 縦軸検知軸（FR-VD05）
2. 横軸検知軸（FR-VD06）
3. `review_unit` による 4 drive × 5 layer 完備
4. `design_review` 記録および record-route
5. `helix qa vertical-check` / `helix gate --pair-check` 仕様

---

## 1. 横断前提: layer 間チェイン定義（5 layer）

| 上位設計 | 下位設計 | test layer | 検証対象 |
|---|---|---|---|
| planning | requirement | operational | 目的の具体化 |
| requirement | architecture | acceptance | 要件の構造化 |
| architecture | detailed | system_integration | 全体設計の詳細化 |
| detailed | functional | integration | 詳細仕様の実装接続 |
| functional | (末端) | unit | 仕様の関数化 |

上記ペアは後続の vertical / horizontal rule の比較キーになる。

---

## 2. FR-VD05: 縦軸 review（同脚内 layer 連鎖）

### 2.1 同一 drive 内 chain integrity の定義

縦軸 review は、同じ drive 内で上位 layer から下位 layer への粒度移行が連続し、欠落・skip・急変がないことを検証する。

#### Axiom: 連鎖成立条件

以下を満たせば、layer `L_i` から `L_{i+1}` の「縦連鎖成立」とみなす。

- 上位 layer `L_i` の `design_review` に `review_axis='vertical'` と `verdict='passed'` が存在する。
- 下位 layer `L_{i+1}` の `design_review` に同 drive で `review_axis='vertical'` と `verdict='passed'` が存在する。
- `pair.vertical_to` が上位、`pair.vertical_from` が下位に整合し、`pair.vertical_from = L_i` または `null`（planning のみ）かつ `pair.vertical_to = L_{i+1}` または `null`（functional のみ）。

### 2.2 axis 仕様（縦軸）

#### axis-NN-vertical-skip
- 検出対象: 設計 chain 上で `planning -> requirement -> architecture -> detailed -> functional` の連続性が途切れるケース。
- 検出条件:
  - ある layer で vertical review が pass しているのに、次 layer で review が全くない
  - `pair.vertical_to` / `pair.vertical_from` の期待値不一致
  - `vertical_from` が存在しないのに下位 layer レビューが存在する（逆方向）
- 意味:
  - 直接 jump（e.g., planning -> detailed）を禁止し、設計仕様の漸進化を確保する。

#### axis-NN-spec-loss
- 検出対象: 上位 layer のレビュー対象要件が下位 layer で観測されない。
- 検出条件:
  - 上位 layer の `review_unit` が持つ論点要素を、下位 layer の `review_unit` と `artifacts` の対応表で解決できない。
  - 期待する対応子が 0 件（`design_review` の raw_findings / meta で「未反映」確定）
- 意味:
  - 粒度落下だけではなく、「上位要求の消失」を明示化する。

#### axis-NN-grain-drift
- 検出対象: 下位 layer の `review_unit` / artifact 粒度が一段ずつではない移行
- 検出条件:
  - 下位が `review_unit` の粒度が上位より粗すぎる（上位で 3+ 論点を含むのに下位で 1 論点化のみ）
  - artifact 数が 4 ブロック以上増減する（意図しない分解/凝集）
  - `test_level` の意味と設計意図のズレ（例: architecture なのに test_level=unit）
- 意味:
  - 粒度崩壊は実装誤差の温床。`pair.score_weight` の分解と整合していることを要件化。

### 2.3 drive 別 vertical 落差ガード

driveごとに仕様化された粒度を分離して持つ。  
全体ルールは共通だが、spec-loss の判定語彙は別定義。

#### 2.3.1 drive=be

- planning→requirement: 目的から要件化への落下、`business_goal` が API 仕様へ接続されること
- requirement→architecture: 要件分解が subsystem レベルに落ちること
- architecture→detailed: subsystem が endpoint/API contract 単位で具体化されること
- detailed→functional: API contract が実装関数（api_function）に落ちること
- axis: API spec / endpoint / schema detail の喪失を厳密に監視

#### 2.3.2 drive=fe

- planning→requirement: IA と UX 価値の具体化、`information_architecture -> user_journey`
- requirement→architecture: 画面/フロー/状態遷移の architectural abstraction
- architecture→detailed: component interface と実装 API 境界の明示
- detailed→functional: component implementation の API contract 対応を確認
- axis: mock/実装境界の spec-loss と `state_event` 忘れを追加重みで検知

#### 2.3.3 drive=db

- planning→requirement: データガバナンス目的の境界定義
- requirement→architecture: data_domain / schema 系統化
- architecture→detailed: ER / relation / key 方針の table_schema 明文化
- detailed→functional: stored procedure / 実行経路の関数化
- axis: 正規化方針の喪失、制約条件消失を強制検知

#### 2.3.4 drive=fullstack

- planning→requirement: track 横断の共通ゴールから `capability` と `track_specific` の要点抽出
- requirement→architecture: `architecture` の track 並列（be / fe / db）と shared design の接続
- architecture→detailed: track間の API / UI / DB 仕様の相互参照確立
- detailed→functional: トラック別実装単位の最終確認（`track_specific` 優先）
- axis: track 非対称での spec-loss、mock 進行情報と実装の齟齬を検知

---

## 3. FR-VD06: 横軸 review（設計 ↔ 検証ペア）

### 3.1 横軸 1:1 対応ルール

各 layer で design layer と test_design layer は下記の一対一対応を基本とする。

| design layer | test_design layer | 要件 |
|---|---|---|
| planning | operational | 運用シナリオで目的が再現される |
| requirement | acceptance | 受入条件が要件をカバーする |
| architecture | system_integration | 統合テストが構造をカバーする |
| detailed | integration | 結合テストが仕様の詳細をカバーする |
| functional | unit | 単体テストが機能を担保する |

### 3.2 horizontal axis 仕様

#### axis-NN-horizontal-orphan
- 検出対象: design または test_design のいずれかが片側のみ存在し、対向が欠損。
- 検出条件:
  - 同 drive / 同 layer に `design.artifacts` / `test.artifacts` の両方が揃っていない
  - `test.test_level` が設計 layer の期待値（spine 対応）を満たしていない
- 既定判定:
  - pair-check 時は `fail`（G2/G3/G4 で fail-close）

#### axis-NN-coverage-mismatch
- 検出対象: 設計と検証で検討範囲の不一致。
- 検出条件:
  - design の `artifacts` うち少なくとも 1 つが test の `artifacts` へトレース可能でない
  - test 側の `baseline_policy` が設計 `review_unit` と整合しない
  - horizontal_rule が required の layer で `horizontal` が pass していない
- 対応:
  - axis mismatch は design review raw_findings に `horizontal_coverage_missing` を必須追加。

---

## 4. review_unit 完備表（drive × layer）

`vmodel-semantics-spine.yaml` / 各 draft における最小必須単位。  
「4 drive × 5 layer」の完全性をレビュー観点で固定化する。

| drive | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| be | business_goal | api_endpoint_spec | api_subsystem | api_module | api_function |
| fe | information_architecture | user_journey | screen_or_flow | component_spec | component_impl |
| db | data_governance_goal | data_model | er_diagram | table_schema | stored_procedure |
| fullstack | track_shared_goal | track_capability | track_architecture | track_contract | track_feature_unit |

補助: fullstack は track 並列（be + fe + db）を束ねるため、`track_specific.review_unit` を別途保持する。

---

## 5. 設計 axis 定義（検知ルールの最小共通スキーマ）

### 5.1 対象フィールド

`vmodel-semantics-spine.yaml` の `spine.pair_required` と以下を必須化:

- `pair.horizontal_rule`
- `pair.vertical_from`
- `pair.vertical_to`
- `pair.score_weight`
- `pair.promotion`

各 layer record は最低次を保持:

- design: `artifacts`, `review_unit`, `review_axes`, `detectors`
- test: `test_level`, `artifacts`, `baseline_policy`, `detectors`
- pair: `horizontal_rule`, `vertical_from`, `vertical_to`, `score_weight`, `promotion`

### 5.2 検証 axis 名と判定値

- `axis-<NN>-vertical-skip`
- `axis-<NN>-vertical-spec-loss`
- `axis-<NN>-vertical-grain-drift`
- `axis-<NN>-horizontal-orphan`
- `axis-<NN>-horizontal-coverage-mismatch`

`design_review` では axis 名は「観測 axis」として `raw_findings` に JSON で保持する想定。

---

## 6. 記録経路（design_review route）

### 6.1 縦軸記録

縦軸は同 drive の layer 間を記録する。`review_axis='vertical'` で layer ごとの pass/warn/fail を保持。

必須列:

- `plan_id`: PLAN-NNN
- `drive`: be / fe / db / fullstack
- `layer`: planning|requirement|architecture|detailed|functional
- `review_axis`: vertical
- `verdict`: passed|warn|failed
- `vertical_from`: null または上位 layer
- `vertical_to`: null または下位 layer
- `reviewed_at`: ISO8601
- `reviewer`: user or agent
- `raw_findings`: JSON（axis 判定結果）
- `direction`: forward（初期）

### 6.2 横軸記録

横軸は design と test のペア化を示す。`review_axis='horizontal'` で coverage/ペア成立を保持する。

必須列:

- `plan_id`
- `drive`
- `layer`
- `review_axis`: horizontal
- `source_layer`: design layer 名
- `target_id`: test_design entry 識別子
- `verdict`: passed|warn|failed
- `raw_findings`: JSON（orphan/mismatch 詳細）
- `direction`: forward（既定）

### 6.3 `review_axis` 列への明記規約

同一 `plan_id`,`drive`,`layer` について:

- vertical/horizontal の双方に 1 レコード（最小）以上
- G 系列検査は双方が `passed` であることを前提に gate 判定

### 6.4 direction

vertical/horizontal は共通で `forward / reverse` を許容する。reverse では `raw_findings.ref_source` を必須化（観測 root）。

---

## 7. CLI 仕様

### 7.1 縦軸 CLI: `helix qa vertical-check`

```bash
helix qa vertical-check --plan-id PLAN-NNN [--drive be|fe|db|fullstack] [--strict]
```

入力:

- plan_id: 必須
- drive: 任意。未指定時は 4 drive を順次検査
- strict: 任意。strict では warn を fail 扱い

出力:

- layer ごとの verdict（passed/warn/failed）
- vertical_from/to 期待値との一致
- axis 単位差分（skip/spec-loss/grain-drift）
- fail-close 判定（G2-G6 の連動トリガ）

終了コード:

- 0: all pass
- 2: one or more failed
- 3: db/schema not found

### 7.2 横軸 CLI: `helix gate` 拡張

既存の横軸判定 `--pair-check` を維持し、drive 指定を必須化または default 全 drive 化。

```bash
helix gate G2 --pair-check architecture --drive be --plan-id PLAN-NNN
helix gate G3 --pair-check detailed --drive be --plan-id PLAN-NNN
helix gate G3 --subgate functional_freeze --drive be --plan-id PLAN-NNN
```

判定:

- layer ごとの vertical + horizontal の pair が両方 `passed` かつ fail-close 条件を満たすこと。
- drive 指定により、対象 table/records を絞りこむ。
- horizontal_orphan と coverage_mismatch を axis として含める。

---

## 8. 失敗条件（fail-close）

### 8.1 横軸 fail-close

- pair 成立しない (片側のみ)
- test_design が存在しないのに horizontal 設計済み
- `horizontal_rule='required'` なのに horizontal pass がない

横軸失敗時: 関連 gate（FR-GRxx 要件）を失敗扱い。

### 8.2 縦軸 fail-close

- 連鎖崩壊（上位 only / 下位 only）
- `vertical_to` / `vertical_from` の整合不整合
- spec-loss や grain-drift が critical と判定

縦軸失敗時: vertical-check は fail とし、G2-G6 の連動でレビュー停止。

### 8.3 G2-G6 fail-close 連動（FR-V03）

- FR-V03 の原則に従い、pair-check で失敗時は gate 失敗に直結。
- G2/G3/G4/G6 は vertical-check / horizontal pair-check を precondition とみなす。

---

## 9. 実装 Step と受け入れ

実装順:

1. Phase 2: `vmodel-semantics.yaml` の review_axes / review_unit 確定  
   - 5 layer × 4 drive の review_unit 完備  
   - axis 名の規約凍結
2. Phase 3: `design_review` schema 拡張  
   - `vertical_from`, `vertical_to` 追加  
   - `review_axis` に vertical/horizontal 2 系統明示
3. Phase 4: detector 追加  
   - vertical-skip, horizontal-orphan を最優先追加  
   - spec-loss/grain-drift を追加して DR 可視化
4. Phase 4: `helix qa vertical-check` 新規 CLI 実装  
   - plan_id 驱動 + ドライブ選択  
   - strict + summary output
5. Phase 4: `helix gate --pair-check` の縦横 axis 拡張  
   - axis 判定を design_review へ委譲  
   - fail-close の厳格化

受け入れ条件:

- 5 layer × 4 drive の review_unit が `design` 側で欠損 0
- `vertical-check` が連鎖崩壊を検知可能
- `pair-check` が orphan/mismatch を検知し、設計 axis と test axis が 1:1 を満たす
- `design_review` INSERT が vertical/horizontal に応じて `vertical_from / vertical_to / direction` を保存

---

## 10. 参照実装への接続（記録・検証の流れ）

### 10.1 レビュー完了時の write flow

1. レビュー対象の drive/layer を確定。
2. `design_review` に horizontal と vertical を同時記録。
3. `direction=forward` を既定として保存。
4. raw_findings に axis 結果を JSON 追加。
5. gate 実行時に `query_design_review_pair` と `vertical-check` を連携。

### 10.2 クエリ観点

`helix qa vertical-check` は `design_review` から drive/layer 軸で 5 層 chain を構築し、
`vertical_from/to` が NULL でないところだけを厳密検証し、
NULL が許容される端点（planning/functional）でのみ leniency を許可する。

`helix gate --pair-check` は layer 指定で vertical+horizontal 両方を確認し、
どちらか欠損なら `pair missing` として exit 2 を返す。

---

## 11. TODO / 未解決項目

- 実検知閾値 axis-NN の粒度値（例: grain-drift 許容上下限）を detector policy へ具体化
- DB への direction=reverse 記録時、raw_findings.ref_source の最小形式定義（json schema）
- fullstack における `track_specific` の正規キー一覧を `helix qa vertical-check` 側で参照する API 化
- FE 軸における `state_events` の artifact 命名統一（`state_events` vs ファイル名）

---

## 12. チェック済みリンク

- docs/v2/L1-REQUIREMENTS.md
- docs/v2/B-design/vmodel-semantics-spine.yaml
- docs/v2/B-design/vmodel-semantics-be-draft.yaml
- docs/v2/B-design/vmodel-semantics-fe-draft.yaml
- docs/v2/B-design/vmodel-semantics-db-draft.yaml
- docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml
- cli/lib/tests/test_design_review_pair_check.py
- cli/helix-gate

最終的には本書の axis 名と field map を元に、`docs/v2/B-design` の既存草案と実装器の整合性差分を継続監視する。

---
