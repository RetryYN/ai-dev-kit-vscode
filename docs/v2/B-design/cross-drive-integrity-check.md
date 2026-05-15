# Phase 2 Cross-Drive Integrity Check

Status: draft review  
Scope: `docs/v2/B-design/vmodel-semantics-*.yaml` の cross-drive 整合性検証  
Mode: read-only / no draft modification

## 概要

Phase 2 で起草された 4 drive draft (`be` / `fe` / `db` / `fullstack`) を spine 基準で横断検証した。  
結論は以下の 2 点である。

1. spine 必須項目、pair weight、test level、freeze flag、pair source refs などの**構造的整合**は概ね良好。
2. 一方で、cross-drive で運用すると **命名ゆれ・粒度ずれ・promotion schema 差・role 名の不統一** が後続 CLI/validator 実装でノイズになる。

このため、G2/G3 前の段階で YAML を大きく書き直す必要はないが、G3 実装着手前に glossary / promotion schema / role naming をそろえる修正タスクは必要である。

## 選択肢

| 選択肢 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | 現状維持で実装へ進む | 最速 | validator 実装で例外分岐が増える | 低 |
| B | 命名と schema だけ先に正規化してから実装 | 実装負債を早期に圧縮できる | 追加の整合作業が必要 | 高 |
| C | 4 draft を全面的に共通テンプレートへ再構成 | 最も整然とする | 今回スコープを超える | 中 |

推奨は **B**。構造は既に十分そろっているため、全面再構成よりも cross-drive validator が依存する最小共通語彙を先に固定する方が費用対効果が高い。

## 検証方法

- 入力 5 ファイルを全読
- spine 必須フィールドを drive × layer × sibling (`design/test/pair`) で照合
- `pair_test_levels`、`score_weight` 合計、`promotion`、`requires_functional_freeze` を機械確認
- `artifact` / `review_unit` / `detector` / `role` / `source_refs` を cross-drive 比較
- detector 名の「許容集合」は spine に明示列挙がないため、**4 draft に現れる detector 集合を事実上の許容集合として比較**した

不確実性:

- spine は detector 名の enum を持たない。そのため §3 の detector 系所見は「厳密な invalid」ではなく「schema 正規化不足」の指摘である。

---

## §1 spine 準拠チェック

### 1.1 80 ブロック完備性

- 対象: 4 drive × 5 layer × (`design` + `test` + `pair`) = 60 sibling
- 必須項目セル:  
  `design` 4 + `test` 4 + `pair` 5 = 13 cells / layer  
  13 × 5 layer × 4 drive = **260 required cells**
- 結果: **260/260 充足 (100%)**

### 1.2 drive × layer 完備性表

凡例:

- `D`: design required 4/4
- `T`: test required 4/4
- `P`: pair required 5/5
- `OK`: 欠落なし

| drive | planning | requirement | architecture | detailed | functional | 完備率 |
|---|---|---|---|---|---|---|
| be | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | 100% |
| fe | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | 100% |
| db | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | 100% |
| fullstack | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | D4 T4 P5 OK | 100% |

### 1.3 spine ルール別結果

| ルール | be | fe | db | fullstack | 判定 |
|---|---|---|---|---|---|
| `test.test_level == pair_test_levels[layer]` | OK | OK | OK | OK | PASS |
| 5 layer `score_weight` 合計 = 1.0 | 1.00 | 1.00 | 1.00 | 1.00 | PASS |
| `promotion` は fe/fullstack のみ利用 | OK | OK | OK | OK | PASS |
| `promotion.append_only = true` | N/A | OK | N/A | OK | PASS |
| `requires_functional_freeze` | false | true | true | true | PASS |
| fullstack `tracks` 配列 | N/A | N/A | N/A | 5/5 layer で確認 | PASS |
| pair `source_refs` 非空 | OK | OK | OK | OK | PASS |

### 1.4 80 ブロック観点の補足

- 欠落ブロックは検出されなかった。
- `design/test/pair` の sibling 構造も全 layer で保持されている。
- 構造面の不足より、**意味語彙の揺れ**が次の主要論点である。

---

## §2 命名ゆれ検出

### 2.1 artifact 名

| 系統 | 観測値 | 所見 |
|---|---|---|
| state event 系 | `state_events`, `state-events.md`, `state_event_scope`, `state_transition_*` | snake_case artifact ID とファイル名/文書名が混在 |
| contract fixture 系 | `contract_fixture_set`, `api_fixture_set`, `ui_contract_fixture_set`, `integration_fixture_set` | 近縁概念の語彙が drive ごとに分裂 |
| API overview 系 | `api_overview`, `api_contract`, `d_contract`, `d_contract_overview` | contract と overview の粒度差は妥当だが glossary 未固定 |
| implementation 系 | `component_impl`, `component_impl_map`, `code_symbol_map`, `function_contract` | functional 層の review target が drive 依存で異なる |
| planning artifact 系 | `plan_goal`, `drive_decision`, `scope_boundary`, `phase_strategy`, `twin_track_strategy`, `contract_sync_policy` | be/fullstack は近いが fe/db は別語彙で書かれている |

### 2.2 review_unit 名

| layer | be | fe | db | fullstack | 所見 |
|---|---|---|---|---|---|
| planning | `plan` | `journey_map` | `data_program` | `plan` | planning の基準粒度が 3 通りある |
| requirement | `capability` | `screen_flow` | `data_domain` | `capability` | fullstack は be 側へ寄っている |
| architecture | `api_subsystem` | `approved_mock` | `schema_subsystem` | `feature_slice` | fullstack の shared review unit が cross-drive 正規化の難所 |
| detailed | `api_endpoint` | `component_surface` | `table` | `feature_contract` | fullstack が統合語彙、他 3 drive は実装単位語彙 |
| functional | `function` | `component_impl` | `db_object` | `feature_unit` | 比較は可能だが validator 用の対応表が必要 |

### 2.3 detector 名

- detector 名そのものの typo は未検出。
- ただし spine は detector enum を持たないため、**「何が許容名か」が契約として凍結されていない**。
- 例: `axis-09-test-quality` と `axis-09-refactor-opportunity` は同じ軸番号に別意味が共存しており、番号体系の一貫性に疑義が残る。

---

## §3 矛盾検出 (P1/P2/P3)

| ID | 軸 | drive A | drive B | 矛盾内容 | 修正案 | status |
|---|---|---|---|---|---|---|
| CI-001 | artifact naming | fe | fullstack | FE architecture は `state-events.md`、fullstack architecture は `state_events`、fullstack requirement は `state_event_scope`。artifact ID とファイル名と scope 名が同列に混在。 | artifact ID は snake_case に統一し、実ファイル名は `examples.path` へ退避する。requirement は `state_event_scope`、architecture は `state_events` を正本化。 | **resolved (commit 9fd9af1, fe-draft state-events.md → state_events)** |
| CI-002 | promotion schema | fe | fullstack | FE architecture pair の `promotion` は `from_artifact_kind` / `to_artifact_kind` / `link_kind` を持つが、fullstack は `kind` / `from_layer` / `to_layer` 中心で schema が非対称。 | FE の詳細 schema を正本にし、fullstack 側へ `from_artifact_kind=mock`、`to_artifact_kind=component_impl`、`link_kind=derives_from` を追加。 | **resolved (PLAN-069, commit 62ac1cd)** |
| CI-003 | role naming | fe/fullstack | spine/ROLE_MAP | fullstack metadata `pipelines.fe.implementation: sonnet` は ROLE_MAP の正規 role 名と一致しない。spine/role map は `pg` / `fe` / `impl-sonnet` 系。 | metadata role も ROLE_MAP の正規値に寄せる。少なくとも `sonnet` は alias ではなく CLI role 名へ置換。 | **resolved (PLAN-069, commit 62ac1cd, sonnet→fe)** |
| CI-004 | review granularity | be | fullstack | architecture layer が `api_subsystem` vs `feature_slice`。BE track と fullstack shared layer の比較で review unit 粒度がずれる。 | fullstack architecture に `track_specific.review_unit` を導入し、be track は `api_subsystem`、shared は `feature_slice` と明示分離。 | **resolved (commit 6b69a85, track_specific.shared.review_unit 追加)** |
| CI-005 | fixture naming | be | fullstack | detailed test artifact が `contract_fixture_set` に対し、fullstack は `api_fixture_set` / `ui_contract_fixture_set`。contract fixture の継承関係が見えない。 | `*_fixture_set` の命名規約を追加し、contract family と api/ui 派生の関係を glossary に定義。 | **resolved (commit 6b69a85, spec.md §4.6 + fullstack family 明示)** |
| CI-006 | detector contract | all | spine | spine が detector 名の enum を持たず、各 draft だけが事実上の許容集合になっている。CLI validator 実装時に fail-close できない。 | spine に `allowed_detectors` または `detector_catalog_ref` を追加し、番号/意味/適用 layer を凍結する。 | **resolved (PLAN-069, commit 62ac1cd, 17 detector 列挙)** |
| CI-007 | layer semantics | fe | fullstack | FE requirement は `screen_flow` 中心、fullstack requirement は `capability` 中心。FE 由来要件と API 由来要件の主語が一致していない。 | fullstack requirement を `capability + screen_flow` の複合 review model とし、track_specific へ FE 主語を昇格。 | **resolved (commit 6b69a85, track_specific.fe.review_unit=screen_flow + be.review_unit=capability)** |
| CI-008 | functional baseline semantics | fe/fullstack | db | functional test は全 drive で `unit` だが、baseline policy は FE/fullstack が `snapshot`、DB が `golden_fixture`。score では同列扱いされるが baseline 性質が異質。 | baseline_policy の横比較を想定するなら `snapshot_like` / `fixture_like` の上位分類を spine に追加。 | **resolved (commit e6d575c, spine.yaml baseline_policy_family 追加)** |

### 優先度判断

- P1: CI-002, CI-003, CI-006 (全件 resolved)  
  理由: 後続 validator / CLI / schema 実装を直接不安定化する。
- P2: CI-001, CI-004, CI-005, CI-007 (全件 resolved)  
  理由: すぐ壊れはしないが cross-drive compare の可読性を落とす。
- P3: CI-008 (resolved)  
  理由: 現状でも drive 特性として説明可能だが、score 可視化時に解釈差が残る。

---

## §4 不足検出

### 4.1 spine 必須項目の欠落

結果:

- **欠落 0 件**
- `design_required`, `test_required`, `pair_required` は全 layer・全 drive で充足

### 4.2 構造外の不足

spine required には抵触しないが、cross-drive 運用上の不足はある。

| ID | 種別 | 内容 | 影響 |
|---|---|---|---|
| MG-001 | glossary 不足 | artifact/review_unit の共通語彙表が未定義 | 比較ロジックが ad hoc になる |
| MG-002 | detector catalog 不足 | detector 名の正規集合と説明が spine にない | validator が enum 検査できない |
| MG-003 | role alias 規約不足 | metadata role と CLI role の対応が明文化されていない | `sonnet` のような別名が混入する |
| MG-004 | promotion canonical schema 不足 | fe と fullstack の `promotion` 形が分岐 | parser/renderer が drive 分岐必須になる |
| MG-005 | review_unit crosswalk 不足 | `api_subsystem` と `feature_slice` などの対応表がない | cross-drive review で粒度比較が難しい |

---

## §5 統合修正計画

### 方針

- spine を最小限拡張して「共通契約」を先に固定する
- drive draft は spine に従って追随修正する
- 各 drive のドメイン差は残してよいが、**比較に使う名前**だけは共通化する

### 修正方針表

| 対象 | 正本にする draft / 文書 | 修正内容 | 理由 |
|---|---|---|---|
| artifact naming | spine + fe/fullstack | `state_event_scope` / `state_events` の 2 段階を正本化し、`state-events.md` は examples/path へ移す | artifact ID とファイル名を分離するため |
| promotion schema | fe draft | FE の詳細 `promotion` schema を正本にし、fullstack を合わせる | FE の方が append-only 契約が具体的 |
| role naming | ROLE_MAP.md | metadata でも CLI role 名のみ許可、alias を禁止 | role 解決を単純化できる |
| detector catalog | spine | `allowed_detectors` または外部 catalog 参照を追加 | validator 実装の fail-close 条件が成立する |
| review_unit crosswalk | 新規 glossary 節 or spine 追補 | `plan/journey_map/data_program` のような drive 固有 unit を共通分類へ写像 | comparison UI の軸を固定できる |
| fixture naming | be/fullstack/db | `*_fixture_set` の family 規約を追加 | contract/api/ui fixture の系譜を可視化するため |

### 実施順

1. spine に glossary / detector catalog / promotion canonical schema を追加
2. fullstack draft の `promotion` と metadata role 名を正規化
3. fe draft の `state-events.md` を artifact ID から examples/path へ移す
4. be/fullstack/db の fixture naming を family 規約へ寄せる
5. review_unit crosswalk を別表で追加し、cross-drive compare の正規主語を固定

### 修正優先順位

- 先行着手: CI-002, CI-003, CI-006 (全件 resolved, PLAN-069 commit 62ac1cd)
- 次点: CI-001, CI-004, CI-005 (全件 resolved, commits 9fd9af1 / 6b69a85)
- 後回し可: CI-007, CI-008 (CI-007 resolved commit 6b69a85, CI-008 resolved commit e6d575c)

---

## §6 cross-drive score 計算

前提:

- spine score 式: `100 - 15*missing_test_design - 10*missing_baseline - 20*failing_baseline`
- layer weights: planning 0.10 / requirement 0.20 / architecture 0.25 / detailed 0.20 / functional 0.25
- 以下は **仮想例 PLAN-XXX**。実測値ではない。

### 6.1 仮定

| drive | 仮定 |
|---|---|
| be | detailed で `missing_test_design=1`、他 0 |
| fe | architecture で `missing_baseline=1`、functional で `failing_baseline=1` |
| db | requirement で `missing_baseline=1`、functional で `missing_test_design=1` |
| fullstack | architecture で `missing_test_design=1`、functional で `failing_baseline=1` |

### 6.2 layer 別 raw score

計算式:

- `missing_test_design=1` → 85
- `missing_baseline=1` → 90
- `failing_baseline=1` → 80
- 問題なし → 100

| drive | planning | requirement | architecture | detailed | functional |
|---|---|---|---|---|---|
| be | 100 | 100 | 100 | 85 | 100 |
| fe | 100 | 100 | 90 | 100 | 80 |
| db | 100 | 90 | 100 | 100 | 85 |
| fullstack | 100 | 100 | 85 | 100 | 80 |

### 6.3 weight 適用後の合計

| drive | 計算 | score |
|---|---|---|
| be | `100*0.10 + 100*0.20 + 100*0.25 + 85*0.20 + 100*0.25` | **97.0** |
| fe | `100*0.10 + 100*0.20 + 90*0.25 + 100*0.20 + 80*0.25` | **92.5** |
| db | `100*0.10 + 90*0.20 + 100*0.25 + 100*0.20 + 85*0.25` | **94.25** |
| fullstack | `100*0.10 + 100*0.20 + 85*0.25 + 100*0.20 + 80*0.25` | **91.25** |

### 6.4 解釈

- fullstack は architecture と functional の weight が重いため、contract freeze 失敗や L4.5 readiness 失敗の影響を強く受ける。
- be は detailed の 1 欠落だけでは大きく下がらない。
- db は functional を `unit` と呼んでいても、baseline が fixture 系なので score の意味づけが FE とやや異なる。

---

## 推奨

推奨は次の通り。

1. **spine を先に補強する**  
   detector catalog、promotion canonical schema、review glossary を spine 側へ追加する。
2. **fullstack を cross-drive の合わせ先ではなく、spine へ合わせる**  
   fullstack は統合 drive のため語彙が広く、他 drive の正本にしにくい。共通契約は spine に置く方が安定する。
3. **FE の promotion schema を canonical に採用する**  
   append-only の意味が最も具体的に書かれている。
4. **artifact ID と文書 path を分離する**  
   `state-events.md` のようなファイル名は artifact 名に持ち込まない。

---

## ソース

- [vmodel-semantics-spine.yaml](/home/tenni/ai-dev-kit-vscode/docs/v2/B-design/vmodel-semantics-spine.yaml)
- [vmodel-semantics-be-draft.yaml](/home/tenni/ai-dev-kit-vscode/docs/v2/B-design/vmodel-semantics-be-draft.yaml)
- [vmodel-semantics-fe-draft.yaml](/home/tenni/ai-dev-kit-vscode/docs/v2/B-design/vmodel-semantics-fe-draft.yaml)
- [vmodel-semantics-db-draft.yaml](/home/tenni/ai-dev-kit-vscode/docs/v2/B-design/vmodel-semantics-db-draft.yaml)
- [vmodel-semantics-fullstack-draft.yaml](/home/tenni/ai-dev-kit-vscode/docs/v2/B-design/vmodel-semantics-fullstack-draft.yaml)
- [ROLE_MAP.md](/home/tenni/ai-dev-kit-vscode/cli/ROLE_MAP.md)

## 最終判定

- spine 準拠: PASS
- 構造欠落: なし
- cross-drive naming/schema consistency: **changes recommended**
- 実装着手可否: **可。ただし validator 実装前に CI-002 / CI-003 / CI-006 の解消を推奨**
