---
doc_id: L7-TEST-DESIGN-REQUIREMENT-DRIFT
title: "requirement_drift detector 単体テスト設計"
status: draft
layer: L7
pairs_design: docs/v2/L6-functional-design/requirement-drift-機能設計.md
pairs_with: L6-functional-design
implementation_status: implemented-mvp
owner: TL
created: 2026-06-09
---

# requirement_drift detector 単体テスト設計

## 1. 目的

`requirement_drift` は、`trace_symmetry` が扱う設計↔テスト設計の ID 対称性ではなく、L1/L3 要件から L4-L6 設計までの縦方向の意味 trace を検出する detector である。L7 code / test の照合は `--focus L7` 指定時だけ有効にする。

本書は `cli/lib/requirement_drift.py` MVP の単体テスト受入条件を固定する。2026-06-09 時点で Python API / CLI JSON / doctor JSON surface は実装済みであり、`VG-overview.required_clean.requirement_drift` 経由で `helix doctor --gate` / `helix push --gate` の fail-close に接続済みである。

`RD-UT-*` は requirement_drift 専用テスト ID である。`g7_subcheck` は `UT-*` を実装済み L7 inventory として読むため、requirement_drift 専用テストは `RD-UT-*` のまま管理し、G7 UT inventory へ混入させない。

## 2. MVP Scope

| Scope | 対象 | 判定 |
|---|---|---|
| requirement kind | FR のみ | BR / NFR / 運用要件は後続拡張 |
| upstream | L1 / L3 requirement docs | `FR-*` ID と見出し / table row label を抽出 |
| downstream design | L4 / L5 / L6 docs | requirement ID または design ID 経由で trace |
| downstream code | `cli/lib/`, `cli/helix*` | `--focus L7` 指定時のみ docstring / comment / registry anchor / test anchor 由来の trace |
| downstream test | `cli/lib/tests/`, `cli/tests/` | `--focus L7` 指定時のみ pytest / Bats の requirement or design anchor |
| waiver | 明示 reason 必須 | waived finding は pass ではなく `waived_with_reason` に分離 |

## 3. Output Contract

```yaml
requirement_drift:
  scope: L1_FR -> L3_FR -> L4-L6_design
  focus: L6
  stale_check_enabled: false
  requirement_kind: [FR]
  clean: true | false
  blocking_clean: true | false
  findings:
    missing_downstream: []
    orphan_design: []
    orphan_code: []
    semantic_label_mismatch: []
    stale_freeze: []
    waived_with_reason: []
  summary:
    requirements: 0
    design_links: 0
    code_links: 0
    test_links: 0
    parent_child_links: 0
    blocking_findings: 0
    advisory_findings: 0
```

## 4. Unit Test Matrix

| Planned Test ID | Name | Fixture | Expected |
|---|---|---|---|
| RD-UT-01 | clean L6 vertical trace | L1/L3 FR が L6 design に接続 | `clean=true`, `focus=L6`, code/test links 0 |
| RD-UT-02 | missing downstream design | L3 FR に対応する L4-L6 design が無い | `missing_downstream` に FR ID |
| RD-UT-03 | orphan design | L6 design が上流 FR に戻れない | `orphan_design` に design ID |
| RD-UT-04 | orphan code | `--focus L7` で code anchor が要件 / 設計に戻れない | `orphan_code` に file + symbol |
| RD-UT-05 | semantic label mismatch | ID 接続はあるが FR label と design label が不一致 | `semantic_label_mismatch` に pair |
| RD-UT-06 | stale freeze opt-in | `check_stale=true` で upstream frozen 後に L3 FR が更新され、下流が古い | `stale_freeze` に FR ID |
| RD-UT-07 | waiver requires reason | waiver に reason が無い | `clean=false`, finding remains unwaived |
| RD-UT-08 | waiver with reason | waiver に reason / owner / expires がある | `waived_with_reason` に移動、unwaived finding 0 |
| RD-UT-09 | no FR docs | FR 入力が無い project | detector error ではなく `requirements=0`, `clean=true`, advisory message |
| RD-UT-10 | malformed table row | 壊れた Markdown table | detector は落ちず `parse_warnings` に記録 |
| RD-UT-11 | L6 focus ignores code/test | L6 focus で code/test anchor のみが存在 | `clean=true`, `orphan_code=[]` |
| RD-UT-12 | L7 focus counts code/test | `--focus L7` で code/test anchor が存在 | `code_links=1`, `test_links=1` |
| RD-UT-13 | L1 parent to L3 child trace | L1 数字式 FR が L3 名前ベース FR に詳細化され、子が L6 design に接続 | parent 側も `design_links` に含め、`missing_downstream=[]` |
| RD-UT-14 | placeholder FR ignored | `FR-NN` / `FR-XX` などの説明用 ID が存在 | 要件数・finding に含めない |
| RD-UT-15 | generic downstream label ignored | L6 design label が `code` / `registry-only` などの総称値 | `semantic_label_mismatch=[]`, `clean=true` |
| RD-UT-16 | stale check opt-in default off | mtime 上は upstream が新しいが `check_stale=false` | `stale_check_enabled=false`, `stale_freeze=[]`, `clean=true` |
| RD-UT-17 | CLI stale check option | CLI に `--check-stale` を指定 | `stale_check_enabled=true`, `stale_freeze` に FR ID |

## 5. CLI / Gate Acceptance

| Surface | Acceptance |
|---|---|
| Python API | `collect_requirement_drift(project_root)` が L6 既定の Output Contract を返す |
| CLI | `python3 -m cli.lib.requirement_drift --json` が L6 既定の JSON を返す |
| doctor | `helix doctor check_requirement_drift --json` が L6 既定の advisory 集計を返す |
| focus extension | `--focus L7` 指定時のみ code/test trace を集計する |
| stale extension | `--check-stale` 指定時のみ mtime stale advisory を集計する |
| push gate | `G-vg-overview` が `required_clean.requirement_drift.clean=false` を block |
| VG-overview | `required_clean.requirement_drift` が L6 focus / requirements / design_links / finding_count を返す |

## 6. Verification Commands

```bash
python3 -m pytest cli/lib/tests/test_requirement_drift.py -q
python3 -m py_compile cli/lib/requirement_drift.py
python3 -m cli.lib.requirement_drift --json
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_requirement_drift --json
```

## 7. Non-goals

- BR / NFR / OT の full semantic drift は MVP 外。
- L11 / G11 のユーザー検証フィードバック巻き取りは MVP 外。
- DB schema migration は行わない。既存 DB へ記録する場合は既存 events / metrics / feedback table のみ使う。
