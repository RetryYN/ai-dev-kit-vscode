from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from registry_checks import RegistryLoadError
from ddd_registry_checks import (
    build_ddd_registry_baseline_payload,
    check_bc_anti_corruption,
    check_bc_mode_coverage,
    check_glossary_coverage,
    load_ddd_registry,
    main,
)


GLOSSARY_ROWS = [
    ("PLAN", "installed"),
    ("gate", "partial"),
    ("workflow", "installed"),
    ("legacy drive field", "installed / migration target"),
    ("artifact", "installed"),
    ("pair freeze", "installed"),
    ("balance_ratio", "L4-carry"),
    ("NSM", "not-implemented"),
    ("guardrail", "partial"),
    ("trace", "partial"),
    ("drift", "partial"),
    ("carry", "installed"),
    ("readiness", "installed"),
    ("agent_slot", "installed"),
    ("handover", "installed"),
    ("sprint", "installed"),
    ("phase", "installed"),
    ("IIP / deferral", "installed"),
    ("ADR", "partial"),
]

BC_ROWS = [
    ("Forward", "forward"),
    ("Scrum", "derived"),
    ("Discovery", "derived"),
    ("Reverse", "derived"),
    ("Incident", "derived"),
    ("Add-feature", "derived"),
    ("Refactor", "derived"),
    ("Retrofit", "derived"),
    ("Research", "derived"),
    ("Recovery", "derived"),
]


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_yaml(path: Path, body: str) -> Path:
    return _write_file(path, textwrap.dedent(body).strip() + "\n")


def _render_concept_md(glossary_rows: list[tuple[str, str]], bc_rows: list[tuple[str, str]], *, example_count: int = 4) -> str:
    glossary_lines = [
        f"| **{term}** | definition for {term} | `helix {index:02d}` | `path/{index:02d}` | `schema.{index:02d}` | `pattern-{index:02d}` | **{status}** |"
        for index, (term, status) in enumerate(glossary_rows, start=1)
    ]
    bc_lines = [
        f"| **{name}** | entry | layer | term-{index} / alias-{index} | via-{name.lower()} |"
        for index, (name, _kind) in enumerate(bc_rows, start=1)
    ]
    example_lines = [f"- 例 {index}: sample mapping" for index in range(1, example_count + 1)]
    return "\n".join(
        [
            "## §12 Glossary",
            "",
            "### §12.1 主要 19 用語 (機械判定可能化、5 列分割 + implementation_status)",
            "",
            "| 用語 | 定義 | 対応 CLI | file path | schema field | 検出 grep pattern | implementation_status |",
            "|---|---|---|---|---|---|---|",
            *glossary_lines,
            "",
            "## §14 Bounded Context",
            "",
            "### §14.1 BC 一覧 (10 行 = Forward 本体 1 + derived workflow 9)",
            "",
            "| BC | 入口判定 | 対応工程 | 固有用語 (workflow-specific) | anti-corruption 経由先 |",
            "|---|---|---|---|---|",
            *bc_lines,
            "",
            "### §14.2 anti-corruption layer 設計 (BC 越境例 ≥ 3 件)",
            "",
            *example_lines,
            "",
        ]
    )


def _render_registry_yaml(
    glossary_rows: list[tuple[str, str]],
    bc_rows: list[tuple[str, str]],
    *,
    glossary_overrides: dict[str, dict[str, str]] | None = None,
    bc_overrides: dict[str, dict[str, object]] | None = None,
) -> str:
    glossary_overrides = glossary_overrides or {}
    bc_overrides = bc_overrides or {}
    lines: list[str] = ["glossary:"]
    for index, (term, status) in enumerate(glossary_rows, start=1):
        override = glossary_overrides.get(term, {})
        lines.extend(
            [
                "  - term: " + json.dumps(term, ensure_ascii=False),
                "    definition: " + json.dumps(str(override.get("definition", f"definition for {term}")), ensure_ascii=False),
                "    cli: " + json.dumps(str(override.get("cli", f"helix {index:02d}")), ensure_ascii=False),
                "    file_path: " + json.dumps(str(override.get("file_path", f"path/{index:02d}")), ensure_ascii=False),
                "    schema_field: " + json.dumps(str(override.get("schema_field", f"schema.{index:02d}")), ensure_ascii=False),
                "    grep_pattern: " + json.dumps(str(override.get("grep_pattern", f"pattern-{index:02d}")), ensure_ascii=False),
                "    implementation_status: " + json.dumps(str(override.get("implementation_status", status)), ensure_ascii=False),
            ]
        )
    lines.append("bounded_contexts:")
    for index, (name, kind) in enumerate(bc_rows, start=1):
        override = bc_overrides.get(name, {})
        unique_terms = override.get("unique_terms", [f"term-{index}", f"alias-{index}"])
        lines.extend(
            [
                "  - name: " + json.dumps(str(override.get("name", name)), ensure_ascii=False),
                "    kind: " + json.dumps(str(override.get("kind", kind)), ensure_ascii=False),
            ]
        )
        if unique_terms:
            lines.append("    unique_terms:")
            for term in unique_terms:
                lines.append("      - " + json.dumps(str(term), ensure_ascii=False))
        else:
            lines.append("    unique_terms: []")
        lines.append("    anti_corruption_via: " + json.dumps(str(override.get("anti_corruption_via", f"via-{name.lower()}")), ensure_ascii=False))
    return "\n".join(lines) + "\n"


def _write_concept_md(path: Path, glossary_rows: list[tuple[str, str]], bc_rows: list[tuple[str, str]], *, example_count: int = 4) -> Path:
    return _write_file(path, _render_concept_md(glossary_rows, bc_rows, example_count=example_count))


def _write_registry(
    path: Path,
    glossary_rows: list[tuple[str, str]],
    bc_rows: list[tuple[str, str]],
    *,
    glossary_overrides: dict[str, dict[str, str]] | None = None,
    bc_overrides: dict[str, dict[str, object]] | None = None,
) -> Path:
    return _write_file(path, _render_registry_yaml(glossary_rows, bc_rows, glossary_overrides=glossary_overrides, bc_overrides=bc_overrides))


def test_load_ddd_registry_normalizes_sections_and_fails_closed(tmp_path: Path) -> None:
    """DoD 検証: ddd-registry-detector-単体テスト設計.md UT-DDD-01"""
    registry_path = _write_registry(tmp_path / "ddd-registry.yaml", GLOSSARY_ROWS, BC_ROWS)

    registry = load_ddd_registry(registry_path)

    assert len(registry.glossary) == 19
    assert len(registry.bounded_contexts) == 10
    assert registry.glossary[0].term == "PLAN"
    assert registry.bounded_contexts[0].name == "Forward"
    assert registry.bounded_contexts[0].kind == "forward"

    missing_section_path = _write_yaml(
        tmp_path / "broken-missing.yaml",
        """
        glossary:
          - term: "PLAN"
            definition: "x"
            cli: "helix plan"
            file_path: "docs/plans/L1/L1-exampleplan.md"
            schema_field: "plan_registry"
            grep_pattern: "^plan$"
            implementation_status: "installed"
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_ddd_registry(missing_section_path)

    invalid_kind_path = _write_yaml(
        tmp_path / "broken-kind.yaml",
        """
        glossary:
          - term: "PLAN"
            definition: "x"
            cli: "helix plan"
            file_path: "docs/plans/L1/L1-exampleplan.md"
            schema_field: "plan_registry"
            grep_pattern: "^plan$"
            implementation_status: "installed"
        bounded_contexts:
          - name: "Forward"
            kind: "root"
            unique_terms:
              - "plan"
            anti_corruption_via: "§12 PLAN"
        """,
    )
    with pytest.raises(RegistryLoadError):
        load_ddd_registry(invalid_kind_path)


def test_check_glossary_coverage_reports_drift_duplicates_missing_columns_and_status_gap(tmp_path: Path) -> None:
    """DoD 検証: ddd-registry-detector-単体テスト設計.md UT-DDD-02"""
    concept_path = _write_concept_md(tmp_path / "concept.md", GLOSSARY_ROWS, BC_ROWS)
    glossary_rows = [GLOSSARY_ROWS[0], GLOSSARY_ROWS[0], *GLOSSARY_ROWS[2:18]]
    registry_path = _write_registry(
        tmp_path / "ddd-registry.yaml",
        glossary_rows,
        BC_ROWS,
        glossary_overrides={
            "PLAN": {
                "cli": "",
                "schema_field": "",
                "grep_pattern": "",
                "implementation_status": "invalid",
            }
        },
    )

    before_registry = registry_path.read_text(encoding="utf-8")
    report = check_glossary_coverage(registry_path=registry_path, concept_md_path=concept_path)

    finding_kinds = {finding.kind for finding in report.findings}

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert {
        "glossary_count_mismatch",
        "glossary_term_drift",
        "duplicate_term",
        "missing_glossary_field",
        "invalid_implementation_status",
    }.issubset(finding_kinds)
    assert registry_path.read_text(encoding="utf-8") == before_registry


def test_check_bc_anti_corruption_reports_missing_fields_and_example_shortage(tmp_path: Path) -> None:
    """DoD 検証: ddd-registry-detector-単体テスト設計.md UT-DDD-03"""
    concept_path = _write_concept_md(tmp_path / "concept.md", GLOSSARY_ROWS, BC_ROWS, example_count=2)
    registry_path = _write_registry(
        tmp_path / "ddd-registry.yaml",
        GLOSSARY_ROWS,
        BC_ROWS,
        bc_overrides={
            "Discovery": {"unique_terms": []},
            "Research": {"anti_corruption_via": ""},
        },
    )

    report = check_bc_anti_corruption(registry_path=registry_path, concept_md_path=concept_path)
    finding_kinds = {finding.kind for finding in report.findings}

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert {"bc_example_shortage", "missing_bc_field"}.issubset(finding_kinds)


def test_check_bc_mode_coverage_reports_missing_and_unexpected_modes(tmp_path: Path) -> None:
    """DoD 検証: ddd-registry-detector-単体テスト設計.md UT-DDD-04"""
    concept_path = _write_concept_md(tmp_path / "concept.md", GLOSSARY_ROWS, BC_ROWS)
    bc_rows = [row for row in BC_ROWS if row[0] != "Recovery"] + [("Chaos", "derived")]
    registry_path = _write_registry(tmp_path / "ddd-registry.yaml", GLOSSARY_ROWS, bc_rows)

    report = check_bc_mode_coverage(registry_path=registry_path, concept_md_path=concept_path)

    assert report.mode == "advisory"
    assert report.exit_policy == 0
    assert {finding.kind for finding in report.findings} == {"missing_bc_mode", "unexpected_bc_mode"}


def test_build_ddd_registry_baseline_payload_is_deterministic_and_main_writes_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DoD 検証: ddd-registry-detector-単体テスト設計.md UT-DDD-05"""
    concept_path = _write_concept_md(tmp_path / "concept.md", GLOSSARY_ROWS, BC_ROWS)
    registry_path = _write_registry(tmp_path / "ddd-registry.yaml", GLOSSARY_ROWS, BC_ROWS)

    first = build_ddd_registry_baseline_payload(
        registry_path=registry_path,
        concept_md_path=concept_path,
        created="2026-06-06",
        expiry="2026-09-04",
    )
    second = build_ddd_registry_baseline_payload(
        registry_path=registry_path,
        concept_md_path=concept_path,
        created="2026-06-06",
        expiry="2026-09-04",
    )

    assert first == second
    assert first["created"] == "2026-06-06"
    assert first["expiry"] == "2026-09-04"
    assert len(first["reports"]) == 3
    for report in first["reports"]:
        for finding in report["findings"]:
            assert finding["fingerprint"]

    output_path = tmp_path / "ddd-registry-baseline.json"
    rc = main(
        [
            "--emit-baseline",
            "--registry-path",
            registry_path.as_posix(),
            "--concept-md-path",
            concept_path.as_posix(),
            "--repo-root",
            tmp_path.as_posix(),
            "--output",
            output_path.as_posix(),
            "--created",
            "2026-06-06",
            "--expiry",
            "2026-09-04",
        ]
    )

    written_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert rc == 0
    assert written_payload == first
    assert capsys.readouterr().out.strip() == output_path.as_posix()
