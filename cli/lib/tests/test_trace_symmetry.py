from __future__ import annotations

import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import trace_symmetry


def _write_doc(path: Path, frontmatter_lines: list[str], body_lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(["---", *frontmatter_lines, "---", "", *body_lines, ""]) + "\n",
        encoding="utf-8",
    )


def test_collect_trace_symmetry_uses_definition_rows_and_test_target_columns(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L3-requirements" / "business.md",
        [
            "doc_id: business",
            "status: frozen",
            "process_layer: L3",
            "pairs_test_design: docs/v2/L12-test-design/acceptance.md",
        ],
        [
            "# Business detail",
            "",
            "### BR-01 稼働フロー",
            "",
            "業務要件の定義見出し。",
            "",
            "## §2 rule",
            "",
            "| rule ID | 条件 | action |",
            "| --- | --- | --- |",
            "| BR-RULE-01 | policy violation | fail-close |",
        ],
    )
    _write_doc(
        docs_root / "L3-requirements" / "functional.md",
        [
            "doc_id: functional",
            "status: frozen",
            "process_layer: L3",
            "pairs_test_design: docs/v2/L12-test-design/acceptance.md",
        ],
        [
            "# Functional detail",
            "",
            "## §1 機能一覧",
            "",
            "| L3 FR-ID | 機能名 | 概要 |",
            "| --- | --- | --- |",
            "| FR-NSM-01 | score | covered functional definition |",
            "| FR-GR-01 | guardrail | covered functional definition |",
            "",
            "## §3 入出力定義",
            "",
            "| FR-ID | CLI input | CLI output |",
            "| --- | --- | --- |",
            "| FR-NSM-01 | --score | json |",
            "| FR-GR-01 | --guardrail | json |",
            "",
            "## §4 L1 -> L3 統合 mapping",
            "",
            "| L1 ID | L3 FR-ID | 統合内容 |",
            "| --- | --- | --- |",
            "| FR-01 | FR-NSM-01 | upstream mapping only |",
            "| FR-02 | FR-GR-01 | upstream mapping only |",
        ],
    )
    _write_doc(
        docs_root / "L12-test-design" / "acceptance.md",
        [
            "doc_id: acceptance",
            "status: frozen",
            "process_layer: L12",
            "pairs_design:",
            "  - docs/v2/L3-requirements/business.md",
            "  - docs/v2/L3-requirements/functional.md",
        ],
        [
            "# Acceptance",
            "",
            "| AT-ID | 対応要件ID | 受入シナリオ |",
            "| --- | --- | --- |",
            "| AT-01 | BR-01 | business trace from target column |",
            "| AT-02 | FR-NSM-01 | functional trace from target column |",
            "| AT-03 | FR-GR-01 | functional trace from target column |",
            "",
            "## §3 trace matrix",
            "",
            "| 要件ID | AT-ID |",
            "| --- | --- |",
            "| BR-01 | AT-01 |",
            "| FR-NSM-01 | AT-02 |",
            "| FR-GR-01 | AT-03 |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)
    pair = report["pairs"]["L3-L12"]

    assert pair["uncovered_req"]["count"] == 0
    assert pair["uncovered_req"]["ids"] == []
    assert pair["orphan_test"]["count"] == 0
    assert pair["orphan_test"]["ids"] == []
    assert pair["coverage_pct"] == 100.0
    assert pair["balance_ratio"] == 1.0


def test_collect_trace_symmetry_respects_verification_layers(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L1-requirements" / "functional.md",
        [
            "doc_id: functional",
            "status: frozen",
            "process_layer: L1",
            "pairs_test_design: docs/v2/L14-test-design/operational.md",
            "verification_layers:",
            "  FR-02:",
            "    - L12",
        ],
        [
            "# Functional",
            "",
            "| FR-ID | 機能名 | 概要 |",
            "| --- | --- | --- |",
            "| FR-01 | operational | verified at L14 |",
            "| FR-02 | acceptance | verified at L12 only |",
        ],
    )
    _write_doc(
        docs_root / "L14-test-design" / "operational.md",
        [
            "doc_id: operational",
            "status: frozen",
            "process_layer: L14",
            "pairs_design: docs/v2/L1-requirements/functional.md",
        ],
        [
            "# Operational",
            "",
            "| OT-ID | 対応要件ID | シナリオ |",
            "| --- | --- | --- |",
            "| OT-01 | FR-01 | operational coverage |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)
    pair = report["pairs"]["L1-L14"]

    assert pair["uncovered_req"]["count"] == 0
    assert pair["uncovered_req"]["ids"] == []
    assert pair["coverage_pct"] == 100.0
    assert pair["orphan_test"]["count"] == 0


def test_collect_trace_symmetry_reports_duplicate_wrong_layer_and_deprecated_exclusion(
    tmp_path: Path,
) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L1-requirements" / "active.md",
        [
            "doc_id: active",
            "status: frozen",
            "process_layer: L1",
            "pairs_test_design: docs/v2/L12-test-design/wrong.md",
        ],
        [
            "# Active",
            "",
            "| BR-ID | summary | description |",
            "| --- | --- | --- |",
            "| BR-01 | same definition | duplicated left-column key |",
            "| BR-01 | same definition | duplicated left-column key |",
        ],
    )
    _write_doc(
        docs_root / "L1-requirements" / "deprecated.md",
        [
            "doc_id: deprecated",
            "status: deprecated",
            "process_layer: L1",
            "pairs_test_design: docs/v2/L14-test-design/tests.md",
        ],
        [
            "# Deprecated",
            "",
            "| BR-ID | summary | description |",
            "| --- | --- | --- |",
            "| BR-02 | should be excluded | deprecated definition |",
        ],
    )
    _write_doc(
        docs_root / "L12-test-design" / "wrong.md",
        [
            "doc_id: wrong",
            "status: frozen",
            "process_layer: L12",
            "pairs_design: docs/v2/L1-requirements/active.md",
        ],
        [
            "# Wrong layer test",
            "",
            "| AT-ID | 対応要件ID |",
            "| --- | --- |",
            "| AT-01 | BR-01 |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)
    l1_l14 = report["pairs"]["L1-L14"]

    assert l1_l14["duplicate_id"]["count"] == 1
    assert l1_l14["duplicate_id"]["ids"] == ["BR-01"]
    assert l1_l14["wrong_layer_pair"]["docs"] == ["docs/v2/L1-requirements/active.md"]
    assert l1_l14["deprecated_excluded"]["count"] == 1
    assert l1_l14["deprecated_excluded"]["docs"] == ["docs/v2/L1-requirements/deprecated.md"]
    assert report["preflight_fail"]["duplicate_id"][0]["id"] == "BR-01"
    assert report["preflight_fail"]["wrong_layer_pair"][0]["doc"] == "docs/v2/L1-requirements/active.md"


def test_collect_trace_symmetry_supports_whole_coverage_pairs(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L5-detailed-design" / "module.md",
        [
            "doc_id: module",
            "status: frozen",
            "process_layer: L5",
            "pairs_test_design:",
            "  path: docs/v2/L8-test-design/integration.md",
            "  ids:",
            "    - IT-MOD-01",
        ],
        [
            "# Module",
            "",
            "| MOD-ID | 概要 | 詳細 |",
            "| --- | --- | --- |",
            "| MOD-01 | module split | pair to integration design |",
        ],
    )
    _write_doc(
        docs_root / "L8-test-design" / "integration.md",
        [
            "doc_id: integration",
            "status: frozen",
            "process_layer: L8",
            "pairs_design: docs/v2/L5-detailed-design/module.md",
        ],
        [
            "# Integration",
            "",
            "| IT-ID | 対象設計ID | シナリオ |",
            "| --- | --- | --- |",
            "| IT-MOD-01 | MOD-01 | integration coverage |",
        ],
    )
    _write_doc(
        docs_root / "L6-functional-design" / "function.md",
        [
            "doc_id: function",
            "status: frozen",
            "process_layer: L6",
            "pairs_test_design:",
            "  path: docs/v2/L7-test-design/unit.md",
            "  ids:",
            "    - UT-FN-01",
        ],
        [
            "# Function",
            "",
            "| FN-ID | 関数 | 契約 |",
            "| --- | --- | --- |",
            "| FN-ORDER-01 | evaluate_route | returns normalized route |",
        ],
    )
    _write_doc(
        docs_root / "L7-test-design" / "unit.md",
        [
            "doc_id: unit",
            "status: frozen",
            "process_layer: L7",
            "pairs_design: docs/v2/L6-functional-design/function.md",
        ],
        [
            "# Unit",
            "",
            "| UT-ID | 対象設計ID | シナリオ |",
            "| --- | --- | --- |",
            "| UT-FN-01 | FN-ORDER-01 | unit coverage |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)

    assert report["pairs"]["L5-L8"]["coverage_pct"] == 100.0
    assert report["pairs"]["L5-L8"]["missing_pair"]["count"] == 0
    assert report["pairs"]["L6-L7"]["coverage_pct"] == 100.0
    assert report["pairs"]["L6-L7"]["missing_pair"]["count"] == 0


def test_collect_trace_symmetry_reports_missing_pair_docs_and_ids(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L5-detailed-design" / "if.md",
        [
            "doc_id: if",
            "status: frozen",
            "process_layer: L5",
            "pairs_test_design:",
            "  path: docs/v2/L8-test-design/integration.md",
            "  ids:",
            "    - IT-IF-01",
            "    - IT-IF-02",
        ],
        [
            "# IF",
            "",
            "| IF-ID | 対象 | 詳細 |",
            "| --- | --- | --- |",
            "| IF-01 | cli | declared pair ids must exist |",
        ],
    )
    _write_doc(
        docs_root / "L8-test-design" / "integration.md",
        [
            "doc_id: integration",
            "status: frozen",
            "process_layer: L8",
            "pairs_design: docs/v2/L5-detailed-design/if.md",
        ],
        [
            "# Integration",
            "",
            "| IT-ID | 対象設計ID | シナリオ |",
            "| --- | --- | --- |",
            "| IT-IF-01 | IF-01 | only one test id exists |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)
    pair = report["pairs"]["L5-L8"]

    assert pair["missing_pair"]["count"] == 1
    assert pair["missing_pair"]["items"][0]["reason"] == "missing_target_ids"
    assert pair["missing_pair"]["items"][0]["ids"] == ["IT-IF-02"]


def test_collect_trace_symmetry_ignores_meta_docs_and_reference_tables(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs" / "v2"
    _write_doc(
        docs_root / "L3-requirements" / "detail.md",
        [
            "doc_id: detail",
            "status: frozen",
            "process_layer: L3",
            "pair_artifact: docs/v2/L12-test-design/acceptance.md",
        ],
        [
            "# Detail",
            "",
            "### FR-ALPHA-01 Coverage target",
            "",
            "| L1 ID | L3 FR-ID | 統合内容 |",
            "| --- | --- | --- |",
            "| FR-01 | FR-ALPHA-01 | mapping only |",
        ],
    )
    _write_doc(
        docs_root / "L3-requirements" / "registry.md",
        [
            "status: draft",
            "process_layer: L3",
            "artifact_type: functional_registry",
        ],
        [
            "# Registry",
            "",
            "| FR-ID | 説明 |",
            "| --- | --- |",
            "| FR-ALPHA-01 | registry mirror only |",
        ],
    )
    _write_doc(
        docs_root / "L1-requirements" / "strategy.md",
        [
            "status: draft",
            "process_layer: L1",
            "doc_kind: verification-strategy",
        ],
        [
            "# Strategy",
            "",
            "| FR-ID | 説明 |",
            "| --- | --- |",
            "| FR-01 | should not be counted in L1 pair universe |",
        ],
    )
    _write_doc(
        docs_root / "L12-test-design" / "acceptance.md",
        [
            "doc_id: acceptance",
            "status: frozen",
            "process_layer: L12",
            "pairs_design: docs/v2/L3-requirements/detail.md",
        ],
        [
            "# Acceptance",
            "",
            "| AT-ID | 対象要件ID | シナリオ |",
            "| --- | --- | --- |",
            "| AT-01 | FR-ALPHA-01 | covered requirement |",
        ],
    )

    report = trace_symmetry.collect_trace_symmetry(project_root=tmp_path)
    pair = report["pairs"]["L3-L12"]

    assert pair["duplicate_id"]["count"] == 0
    assert pair["coverage_pct"] == 100.0
    assert pair["uncovered_req"]["ids"] == []
