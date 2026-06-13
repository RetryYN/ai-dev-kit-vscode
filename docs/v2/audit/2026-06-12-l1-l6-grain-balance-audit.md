---
doc_id: AUDIT-2026-06-12-L1-L6-GRAIN-BALANCE
title: "L1-L6 grain and pair balance audit"
status: current
created: 2026-06-12
owner: TL
scope: L1-L6
workflow: Forward
---

# L1-L6 粒度・バランス監査

## 1. 目的

本監査は、L1 から L6 までの設計成果物について、要件定義漏れ、設計とテスト設計の片肺、粒度違反が残っていないかを確認する。

本監査は L7 実装を開始しない。FR 別 L7 成果物の作成、単体テスト実装、本体実装、coverage closure は本監査の範囲外であり、必要な場合は add-feature として別起票する。

## 2. 判定基準

| 観点 | 判定基準 | 根拠 |
|---|---|---|
| 要件漏れ | L1 FR が L3 FR と L4-L6 design へ trace され、blocking finding が 0 | `helix doctor check_requirement_drift --json` |
| L0 企画突合 | L0 企画の problem axis / target area が L1/L3 要求面と L4-L6 設計証跡へ落ちている | `docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml` |
| FR31 到達証拠 | 上流 FR 31 件それぞれが L4-L6 の design definition ID を持つ | `docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml` |
| ペア存在 | L1-L14 / L3-L12 / L4-L9 / L5-L8 / L6-L7 の `missing_pair=0` | `python3 -m cli.lib.trace_symmetry --json` |
| 粒度 | L4 はシステム / コンポーネント、L5 はモジュール / 結合、L6 は関数 / 単体粒度 | `HELIX-workflows/HELIX-process-L0-L14.md` |
| L6 仕様化 | L4 FR18 のうち code16 と registry-only2 が L6 `FR-*/function-spec.md` に展開されている | `docs/v2/L4-basic-design/機能構成設計.md` + `docs/v2/L6-functional-design/FR-*/function-spec.md` |
| L6 単体テスト設計観点 | FR18 全件が L6 仕様内で `*-UT-CAND-*` を持つ | `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml` |
| ドキュメント未整備検出 | 未登録資産、doc-review 欠落、DDD/glossary drift、coding-rule metadata 欠落、TDD 順序違反、依存 edge 欠落、document projection metadata 欠落の 7 パターンが L1-L6 governance 設計へ接続されている | `docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml` |
| L7 非実施 | 今回追加分について L7 配下の FR 別成果物を作らない | `find docs/v2/L7-test-design ...` |

## 3. 現在の機械証跡

2026-06-12 時点の実行結果は次の通り。

| Command | Result |
|---|---|
| `helix doctor check_requirement_drift --json` | `clean=true`, `focus=L6`, `requirements=31`, `design_links=31`, `blocking_findings=0`, `advisory_findings=0` |
| `docs/v2/audit/2026-06-13-l0-planning-to-l1-l6-derivation-coverage.yaml` | `docs/v2/L0-helix-workflows/concept.md` の L0 problem axes 10 件 / target areas 10 件が L1-L6 設計証跡へ接続済み。`l0_to_l1_l6_derivation_gaps=0`, `l7_artifacts_created_by_this_audit=0` |
| `docs/v2/audit/2026-06-12-l1-l6-fr31-trace-map.yaml` | FR31 全件で `design_definition_ids` が空でない。`goal_complete_allowed=false` |
| `python3 -m cli.lib.trace_symmetry --json` | L1-L14 / L3-L12 / L5-L8 / L6-L7 は coverage 100.0, balance 1.0, missing 0, orphan 0。L4-L9 は coverage 100.0, missing 0, orphan 0, semantic_excluded_orphan 18, balance 0.67 |
| `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --json` | L1-L6 現在スコープでは L2-L10 は `ui_absent` waiver により not_applicable; L6-L7 は `anchored=88/88`, `exec_pass=88`, `missing=0` |
| `HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json` | `exit_code=0` / advisory。strict full-flow は `overall_clean=false` のまま。G8 / G9 / G12 / G14 は `approved_deferred` であり、L1-L6 pass や L7 実施完了を意味しない |
| `docs/v2/audit/2026-06-12-l1-l6-governance-hardening-coverage.yaml` | `documentation_readiness_gap_patterns_checked=7`。未整備検出は L1-L6 の設計契約として定義済みで、detector 実行、fail-close 昇格、DB write は未実施 |

## 4. L別監査

| L | 成果物 | 対になるテスト設計 / 検証設計 | 粒度判定 | 判定 |
|---|---|---|---|---|
| L1 | `docs/v2/L1-requirements/*.md` | `docs/v2/L14-test-design/helix-workflows-operational-test-design.md` | 要求 / 運用テスト設計。L14 対象外の FR/TR/NFR は `verification_layers` 理由付きで除外 | pass |
| L2 | `docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md` | L10 not_applicable waiver | HELIX-workflows 自体に UI がないため waiver。UI 追加時は unskip 必須 | pass with waiver |
| L3 | `docs/v2/L3-requirements/*.md` | `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` | 要件 / 受入テスト設計。coverage 100.0, balance 1.0 | pass |
| L4 | `docs/v2/L4-basic-design/*.md` | `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` | システム / コンポーネント粒度。ST は TV 経由の 2 段 trace として semantic pass | pass with monitoring |
| L5 | `docs/v2/L5-detailed-design/*.md` | `docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md` | モジュール / 結合粒度。coverage 100.0, balance 1.0 | pass |
| L6 | `docs/v2/L6-functional-design/*.md` + FR18 `FR-*/function-spec.md` + `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml` | L6 内の `*-UT-CAND-*` 単体テスト設計観点。ただし今回 FR 別 L7 成果物は未作成 | 関数 / 単体粒度。code16 と registry-only2 は function spec 化済み。FR18 全件で単体テスト設計観点あり | pass |

## 5. FR18 L6 仕様化確認

L4 機能構成設計の code16 と registry-only2 は、L6 の FR 別仕様へ展開済みである。

| FR | L6 spec |
|---|---|
| FR-NSM-01 | `docs/v2/L6-functional-design/FR-NSM-01/function-spec.md` |
| FR-GR-01 | `docs/v2/L6-functional-design/FR-GR-01/function-spec.md` |
| FR-TDD-01 | `docs/v2/L6-functional-design/FR-TDD-01/function-spec.md` |
| FR-9MODE-01 | `docs/v2/L6-functional-design/FR-9MODE-01/function-spec.md` |
| FR-GATE-01 | `docs/v2/L6-functional-design/FR-GATE-01/function-spec.md` |
| FR-IMPACT-01 | `docs/v2/L6-functional-design/FR-IMPACT-01/function-spec.md` |
| FR-EVT-01 | `docs/v2/L6-functional-design/FR-EVT-01/function-spec.md` |
| FR-4ART-01 | `docs/v2/L6-functional-design/FR-4ART-01/function-spec.md` |
| FR-INV-01 | `docs/v2/L6-functional-design/FR-INV-01/function-spec.md` |
| FR-CTX-01 | `docs/v2/L6-functional-design/FR-CTX-01/function-spec.md` |
| FR-DRIFT-01 | `docs/v2/L6-functional-design/FR-DRIFT-01/function-spec.md` |
| FR-PLAN-01 | `docs/v2/L6-functional-design/FR-PLAN-01/function-spec.md` |
| FR-DOCTOR-01 | `docs/v2/L6-functional-design/FR-DOCTOR-01/function-spec.md` |
| FR-MIGR-01 | `docs/v2/L6-functional-design/FR-MIGR-01/function-spec.md` |
| FR-DOCREVIEW-01 | `docs/v2/L6-functional-design/FR-DOCREVIEW-01/function-spec.md` |
| FR-CHANGEPROP-01 | `docs/v2/L6-functional-design/FR-CHANGEPROP-01/function-spec.md` |
| FR-FNREG-01 | `docs/v2/L6-functional-design/FR-FNREG-01/function-spec.md` |
| FR-GLOSSARY-01 | `docs/v2/L6-functional-design/FR-GLOSSARY-01/function-spec.md` |

FR-FNREG-01 と FR-GLOSSARY-01 は L4 機能構成設計で registry-only として扱われている。今回、registry-only のまま L6 仕様へ展開した。実行主体へ昇格するには、機械可読 SSoT、専用 check、実行入口を揃える必要があるため、L7 実装ではなく `docs/plans/add-feature/add-feature-2026-06-12-fr-registry-glossary-l7-entry.md` の承認対象とする。

FR18 の L6 単体テスト設計観点は `docs/v2/L6-functional-design/fr18-unit-test-design-index.yaml` に集約した。索引上は FR18 全件、UT 候補 128 件で、これは L6 の test-design 観点であり L7 の単体テスト設計成果物ではない。

## 6. 粒度に関する所見

| Pair | 所見 | 判定 |
|---|---|---|
| L1-L14 | L14 に直接属さない FR/TR/NFR は `verification_layers` で除外され、運用テスト対象は balance 1.0 | 問題なし |
| L3-L12 | 要件と受入テスト設計が 1:1 で閉じている | 問題なし |
| L4-L9 | raw `balance_ratio=0.67`。ただし ST-* は TV-* を検証し、TV-* が L4 trace を持つ 2 段構造。`semantic_excluded_orphan=18` として機械的に区別済み。machine key: `semantic ST-to-TV-to-L4 transitive trace accepted` | blocking ではないが継続監視 |
| L5-L8 | モジュール / 結合粒度で coverage 100.0, balance 1.0 | 問題なし |
| L6-L7 | L6 は関数 / surface 単位の `FN-*` / `*-FN-*` / FR function spec へ分解済み。今回の registry-only2 追補も L6 のみで、FR 別 L7 成果物は作成していない | 問題なし |

## 6.1 ドキュメント未整備検出の粒度

ドキュメント未整備の検出は、単一の「文書がある / ない」判定ではなく、L1-L6 の governance 設計で次の 7 パターンに分けて扱う。

| Gap pattern | detecting_control | completion_boundary | L1-L6 での扱い |
|---|---|---|---|
| `missing_function_registry_entry` | `auto_registration` | `L6_design_only_l7_cli_db_ci_deferred` | 設計契約あり、registry write は後続 |
| `missing_document_review_or_quality_scope` | `doc_review_quality` | `L6_design_only_reviewer_runtime_deferred` | 4 視点 review 契約あり、runtime reviewer enforcement は後続 |
| `missing_ddd_or_glossary_registry_coverage` | `ddd_registry` | `L6_design_only_glossary_cli_db_deferred` | finding 語彙あり、glossary CLI / DB 投影は後続 |
| `missing_coding_rule_or_enforcement_metadata` | `coding_rule_registry` | `L6_design_only_fail_close_deferred` | finding 語彙あり、fail-close 昇格は後続 |
| `tdd_order_violation_or_test_after_implementation` | `tdd_order` | `L6_design_only_unit_execution_deferred` | TDD 順序の検出語彙あり、unit execution closure は後続 |
| `missing_dependency_or_impact_edge` | `impact_visibility` | `L6_design_only_impact_query_runtime_deferred` | dependency edge / affected artifact 契約あり、impact query runtime は後続 |
| `missing_asset_inventory_or_document_projection_metadata` | `auto_registration` | `L6_design_only_document_projection_write_deferred` | projection metadata 契約あり、HELIX DB write は後続 |

この 7 パターンは `documentation_readiness_gap_patterns_checked=7` として集計される。現在スコープでは、未整備検出の分類・経路・フィードバック先を L1-L6 設計に含めたことを証跡とし、detector 実行、fail-close 昇格、HELIX DB 書き込み、CI 接続は行わない。

## 7. Doc-review 4視点

| 視点 | 確認内容 | 判定 |
|---|---|---|
| Correctness | 機械証跡の数値は `requirement_drift` / FR31 trace / pair balance / vg_overview の現在値と一致し、L7 実装や coverage closure を主張していない | pass |
| Completeness | L0 企画突合、L1-L6 の全6層、設計成果物、対になるテスト設計または waiver、粒度判定、L7 非実施境界を持つ | pass |
| Consistency | ユーザー確認済みの L0-L14 用語、L6=機能設計 / 仕様書 + 単体テスト設計観点、L7=未依頼 feature-ticket-only の境界と矛盾しない | pass |
| Clarity | L4-L9 の raw balance 0.67 は semantic trace による monitoring と明記し、pass と full-flow 完了を混同しない | pass |

この 4 視点は doc-review 用の定性監査であり、L7 実装、L7 単体テスト設計、DB write、CI 接続、外部ツール実行の証跡ではない。

## 8. 結論

L1-L6 の現在スコープでは、要件定義漏れ、設計とテスト設計の片肺、L6 FR18 の機能設計漏れは検出されない。

ただし、これは full-flow 完了ではない。G8 / G9 / G12 / G14 の実行 gate、CI/equivalent 接続、feedback adoption closure、外部ツール候補の承認・導入は別フェーズであり、承認済み feature ticket または後続 PLAN の作業として扱う。

## 9. L7 非実施の明示

今回の範囲で作成した成果物はこの audit doc と L6 FR 別仕様である。今回の範囲では、次を行っていない。

- L7 実装
- FR 別 L7 単体テスト設計の新規作成
- 単体テスト実装
- schema migration
- MCP server / plugin / 外部ツールの install または CI 接続

L7 へ進める場合の入口は `docs/plans/add-feature/add-feature-2026-06-12-fr-registry-glossary-l7-entry.md` であり、この PLAN は未承認 draft である。
