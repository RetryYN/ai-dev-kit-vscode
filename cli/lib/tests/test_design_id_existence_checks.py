"""design_id_existence detector の単体テスト."""

import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from design_id_existence_checks import check_design_id_existence  # noqa: E402


def _write_registry(
    tmp_path: Path,
    entries: list[dict],
    waivers: list[dict] | None = None,
) -> Path:
    payload = {"entries": entries}
    if waivers is not None:
        payload["design_id_existence_waivers"] = waivers
    path = tmp_path / "cli/config/functional-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _write_design_doc(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / "docs/v2/L6-functional-design" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _entry(entry_id: str, fn_id: str) -> dict:
    return {
        "id": entry_id,
        "name": entry_id.lower(),
        "domain": "lib",
        "status": "active",
        "coverage_layer": "L6_required",
        "design_ids": [fn_id],
        "test_design_ids": [f"UT-{fn_id.removeprefix('FN-')}"],
        "code_paths": [f"cli/lib/{entry_id.lower()}.py"],
        "doc_paths": [],
    }


def _kinds(report) -> set[str]:
    return {finding.kind for finding in report.findings}


def test_missing_design_section_is_reported(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, [_entry("FR-A", "FN-WSC-222")])
    _write_design_doc(tmp_path, "registry-detector-機能設計.md", "# Existing\n\nFN-WSC-221 only\n")

    report = check_design_id_existence(
        registry_path,
        "docs/v2/L6-functional-design/*.md",
        tmp_path,
    )

    assert "missing_design_section" in _kinds(report)


def test_prose_only_fn_reference_is_not_treated_as_design_section(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, [_entry("FR-A", "FN-WSC-222")])
    _write_design_doc(
        tmp_path,
        "registry-detector-機能設計.md",
        "# Existing\n\nThis paragraph mentions FN-WSC-222, but it is not a heading or table row.\n",
    )

    report = check_design_id_existence(
        registry_path,
        "docs/v2/L6-functional-design/*.md",
        tmp_path,
    )

    assert "missing_design_section" in _kinds(report)


def test_waived_fn_suppresses_missing_design_section(tmp_path: Path) -> None:
    registry_path = _write_registry(
        tmp_path,
        [_entry("FR-A", "FN-WSC-222")],
        waivers=[
            {
                "fn": "FN-WSC-222",
                "reason": "L6 design section pending",
                "owner": "TL",
            }
        ],
    )
    _write_design_doc(tmp_path, "registry-detector-機能設計.md", "# Existing\n\nFN-WSC-221 only\n")

    report = check_design_id_existence(
        registry_path,
        "docs/v2/L6-functional-design/*.md",
        tmp_path,
    )

    assert report.findings == []


def test_existing_design_section_is_clean(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path, [_entry("FR-A", "FN-WSC-222")])
    _write_design_doc(
        tmp_path,
        "registry-detector-機能設計.md",
        "# FN-WSC-222\n\nDetector contract.\n",
    )

    report = check_design_id_existence(
        registry_path,
        "docs/v2/L6-functional-design/*.md",
        tmp_path,
    )

    assert report.findings == []
