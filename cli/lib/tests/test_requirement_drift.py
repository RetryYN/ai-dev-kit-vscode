from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from cli.lib.requirement_drift import collect_requirement_drift


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCTOR = REPO_ROOT / "cli/helix-doctor"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    _write(
        tmp_path / "docs/v2/L3-requirements/fr.md",
        "| ID | Name |\n|---|---|\n| FR-001 | Export reports |\n",
    )
    _write(
        tmp_path / "docs/v2/L6-functional-design/spec.md",
        "| ID | Name |\n|---|---|\n| FR-001 | Export reports |\n",
    )
    _write(tmp_path / "cli/lib/reports.py", "# FR-001 Export reports\n")
    _write(tmp_path / "cli/lib/tests/test_reports.py", "# FR-001 Export reports\n")
    return tmp_path


def _run_doctor(project_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HELIX_PROJECT_ROOT": str(project_root)}
    return subprocess.run(
        [str(DOCTOR), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_collect_requirement_drift_clean_vertical_trace(tmp_path: Path) -> None:
    report = collect_requirement_drift(_project(tmp_path))

    assert report["clean"] is True
    assert report["blocking_clean"] is True
    assert report["focus"] == "L6"
    assert report["scope"] == "L1_FR -> L3_FR -> L4-L6_design"
    assert report["summary"]["requirements"] == 1
    assert report["summary"]["design_links"] == 1
    assert report["summary"]["code_links"] == 0
    assert report["summary"]["test_links"] == 0
    assert all(not items for items in report["findings"].values() if isinstance(items, list))


def test_collect_requirement_drift_reports_missing_downstream_design(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-002 | Import CSV |\n")
    _write(tmp_path / "cli/lib/importer.py", "# FR-002 Import CSV\n")
    _write(tmp_path / "cli/lib/tests/test_importer.py", "# FR-002 Import CSV\n")

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is False
    assert report["findings"]["missing_downstream"][0]["requirement_id"] == "FR-002"
    assert report["summary"]["design_links"] == 0
    assert report["summary"]["blocking_findings"] == 1


def test_collect_requirement_drift_resolves_l1_parent_to_l3_named_child(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/v2/L1-requirements/fr.md",
        "| FR-ID | Name |\n|---|---|\n| FR-01 | NSM |\n",
    )
    _write(
        tmp_path / "docs/v2/L3-requirements/fr-detail.md",
        "| L3 FR-ID | Name | Source |\n|---|---|---|\n| FR-NSM-01 | NSM score | L1 FR-01 |\n",
    )
    _write(
        tmp_path / "docs/v2/L6-functional-design/spec.md",
        "| Component | Trace |\n|---|---|\n| score | FR-NSM-01 |\n",
    )

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert report["blocking_clean"] is True
    assert report["summary"]["requirements"] == 2
    assert report["summary"]["design_links"] == 2
    assert report["summary"]["parent_child_links"] == 1
    assert not report["findings"]["missing_downstream"]


def test_collect_requirement_drift_ignores_placeholder_fr_ids(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/v2/L3-requirements/fr.md",
        "| ID | Name |\n|---|---|\n| FR-NN | Placeholder |\n| FR-REAL-01 | Real |\n",
    )
    _write(
        tmp_path / "docs/v2/L6-functional-design/spec.md",
        "| ID | Name |\n|---|---|\n| FR-REAL-01 | Real |\n",
    )

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert report["summary"]["requirements"] == 1
    assert "FR-NN" not in report["findings"]["missing_downstream"]


def test_collect_requirement_drift_reports_orphan_design_and_code(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-003 | Known |\n")
    _write(tmp_path / "docs/v2/L6-functional-design/spec.md", "| ID | Name |\n| FR-999 | Orphan design |\n")
    _write(tmp_path / "cli/lib/orphan.py", "# FR-998 Orphan code\n")

    report = collect_requirement_drift(tmp_path, focus="L7")

    assert report["clean"] is False
    assert report["blocking_clean"] is False
    assert report["findings"]["orphan_design"][0]["requirement_id"] == "FR-999"
    assert report["findings"]["orphan_code"][0]["requirement_id"] == "FR-998"


def test_collect_requirement_drift_l6_focus_ignores_code_and_test_links(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-003 | Known |\n")
    _write(tmp_path / "docs/v2/L6-functional-design/spec.md", "| ID | Name |\n| FR-003 | Known |\n")
    _write(tmp_path / "cli/lib/orphan.py", "# FR-998 Orphan code\n")
    _write(tmp_path / "cli/lib/tests/test_orphan.py", "# FR-998 Orphan test\n")

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert report["summary"]["code_links"] == 0
    assert report["summary"]["test_links"] == 0
    assert not report["findings"]["orphan_code"]


def test_collect_requirement_drift_l7_focus_counts_code_and_test_links(tmp_path: Path) -> None:
    report = collect_requirement_drift(_project(tmp_path), focus="L7")

    assert report["focus"] == "L7"
    assert report["scope"] == "L1_FR -> L3_FR -> L4-L6_design -> L7_code -> test"
    assert report["summary"]["code_links"] == 1
    assert report["summary"]["test_links"] == 1


def test_collect_requirement_drift_reports_semantic_label_mismatch(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-004 | Export reports |\n")
    _write(tmp_path / "docs/v2/L6-functional-design/spec.md", "| ID | Name |\n| FR-004 | Delete users |\n")
    _write(tmp_path / "cli/lib/reports.py", "# FR-004 Export reports\n")
    _write(tmp_path / "cli/lib/tests/test_reports.py", "# FR-004 Export reports\n")

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is False
    assert report["blocking_clean"] is True
    mismatch = report["findings"]["semantic_label_mismatch"][0]
    assert mismatch["requirement_id"] == "FR-004"
    assert mismatch["upstream_label"] == "Export reports"
    assert mismatch["downstream_label"] == "Delete users"


def test_collect_requirement_drift_ignores_generic_downstream_labels(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-004 | Export reports |\n")
    _write(tmp_path / "docs/v2/L6-functional-design/spec.md", "| ID | Name |\n| FR-004 | registry-only |\n")

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert report["blocking_clean"] is True
    assert not report["findings"]["semantic_label_mismatch"]


def test_collect_requirement_drift_reports_stale_freeze_by_mtime(tmp_path: Path) -> None:
    root = _project(tmp_path)
    design = root / "docs/v2/L6-functional-design/spec.md"
    upstream = root / "docs/v2/L3-requirements/fr.md"
    os.utime(design, (100, 100))
    os.utime(upstream, (200, 200))

    report = collect_requirement_drift(root, check_stale=True)

    assert report["clean"] is False
    assert report["blocking_clean"] is True
    assert report["stale_check_enabled"] is True
    assert report["findings"]["stale_freeze"][0]["requirement_id"] == "FR-001"


def test_collect_requirement_drift_stale_check_is_opt_in(tmp_path: Path) -> None:
    root = _project(tmp_path)
    design = root / "docs/v2/L6-functional-design/spec.md"
    upstream = root / "docs/v2/L3-requirements/fr.md"
    os.utime(design, (100, 100))
    os.utime(upstream, (200, 200))

    report = collect_requirement_drift(root)

    assert report["clean"] is True
    assert report["stale_check_enabled"] is False
    assert not report["findings"]["stale_freeze"]



def test_collect_requirement_drift_requires_waiver_reason(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-005 | Import CSV |\n")
    _write(
        tmp_path / ".helix/requirement-drift-waivers.yaml",
        yaml.safe_dump(
            {"waivers": [{"requirement_id": "FR-005", "finding_type": "missing_downstream"}]},
            allow_unicode=True,
        ),
    )

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is False
    assert report["findings"]["missing_downstream"]
    assert not report["findings"]["waived_with_reason"]


def test_collect_requirement_drift_accepts_waiver_with_reason(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-006 | Import CSV |\n")
    _write(
        tmp_path / ".helix/requirement-drift-waivers.yaml",
        yaml.safe_dump(
            {
                "waivers": [
                    {
                        "requirement_id": "FR-006",
                        "finding_type": "missing_downstream",
                        "reason": "L6 design is intentionally deferred",
                        "owner": "TL",
                        "expires": "2026-12-31",
                    }
                ]
            },
            allow_unicode=True,
        ),
    )

    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert not report["findings"]["missing_downstream"]
    assert report["findings"]["waived_with_reason"][0]["requirement_id"] == "FR-006"


def test_collect_requirement_drift_no_fr_docs_is_clean_advisory(tmp_path: Path) -> None:
    report = collect_requirement_drift(tmp_path)

    assert report["clean"] is True
    assert report["summary"]["requirements"] == 0
    assert "no FR requirements found" in report["advisory"]


def test_collect_requirement_drift_malformed_table_does_not_crash(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-007 |\n")

    report = collect_requirement_drift(tmp_path)

    assert report["summary"]["requirements"] == 1
    assert report["parse_warnings"]


def test_requirement_drift_cli_json(tmp_path: Path) -> None:
    root = _project(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "cli.lib.requirement_drift", "--json", "--project-root", str(root)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = yaml.safe_load(result.stdout)
    assert payload["clean"] is True
    assert payload["focus"] == "L6"
    assert payload["stale_check_enabled"] is False
    assert payload["summary"]["requirements"] == 1


def test_requirement_drift_cli_check_stale_json(tmp_path: Path) -> None:
    root = _project(tmp_path)
    design = root / "docs/v2/L6-functional-design/spec.md"
    upstream = root / "docs/v2/L3-requirements/fr.md"
    os.utime(design, (100, 100))
    os.utime(upstream, (200, 200))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.lib.requirement_drift",
            "--json",
            "--check-stale",
            "--project-root",
            str(root),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = yaml.safe_load(result.stdout)
    assert payload["stale_check_enabled"] is True
    assert payload["findings"]["stale_freeze"][0]["requirement_id"] == "FR-001"


def test_requirement_drift_gate_fails_closed_on_blocking_findings(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-002 | Import CSV |\n")

    result = _run_doctor(tmp_path, "check_requirement_drift", "--gate", "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["blocking_clean"] is False


def test_requirement_drift_gate_keeps_advisory_only_findings_non_blocking(tmp_path: Path) -> None:
    _write(tmp_path / "docs/v2/L3-requirements/fr.md", "| ID | Name |\n| FR-004 | Export reports |\n")
    _write(tmp_path / "docs/v2/L6-functional-design/spec.md", "| ID | Name |\n| FR-004 | Delete users |\n")

    result = _run_doctor(tmp_path, "check_requirement_drift", "--gate", "--json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["clean"] is False
    assert payload["blocking_clean"] is True
