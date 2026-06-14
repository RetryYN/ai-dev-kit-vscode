from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import fr_uses_checks


def _write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    return path


def _write_registry(path: Path, entries: str) -> Path:
    return _write_file(path, f"entries:\n{entries}")


def test_uses_target_exists_and_reverse_link_present_is_clean(tmp_path: Path) -> None:
    """DoD 検証: WI-C uses 先が実在し逆参照もあれば clean。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-B]
          - id: FR-B
            name: beta
            domain: cli
            status: active
            uses: [FR-A]
        """,
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=False,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["finding_count"] == 0


def test_missing_uses_target_fails_close_on_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C uses 先 FR が無い場合だけ gate fail-close。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-MISSING]
        """,
    )
    monkeypatch.setattr(
        fr_uses_checks,
        "changed_files",
        lambda upstream=None: {
            "files": ["cli/config/functional-registry.yaml"],
            "source_status": "available_nonempty",
        },
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=True,
    )

    assert report["exit_code"] == 1
    assert report["clean"] is False
    assert report["blocking_finding_count"] == 1
    assert report["blocking_findings"][0]["kind"] == "missing_uses_target"


def test_missing_reverse_link_stays_warning_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C 逆参照欠落は warning に留まり gate fail しない。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-B]
          - id: FR-B
            name: beta
            domain: cli
            status: active
        """,
    )
    monkeypatch.setattr(
        fr_uses_checks,
        "changed_files",
        lambda upstream=None: {
            "files": ["cli/config/functional-registry.yaml"],
            "source_status": "available_nonempty",
        },
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["blocking_finding_count"] == 0
    assert report["warning_count"] == 1
    assert report["warning_findings"][0]["kind"] == "missing_reverse_reference"


def test_zero_uses_is_clean(tmp_path: Path) -> None:
    """DoD 検証: WI-C uses 宣言ゼロは clean。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
          - id: FR-B
            name: beta
            domain: cli
            status: active
        """,
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=False,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["finding_count"] == 0


def test_gate_treats_available_empty_as_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C FR uses gate は available_empty を clean 扱いする。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-MISSING]
        """,
    )
    monkeypatch.setattr(
        fr_uses_checks,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "available_empty"},
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is True
    assert report["findings"] == []


def test_gate_skips_without_failing_when_changed_files_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: WI-C FR uses gate は unavailable を skip にする。"""

    registry_path = _write_registry(
        tmp_path / "cli/config/functional-registry.yaml",
        """
          - id: FR-A
            name: alpha
            domain: cli
            status: active
            uses: [FR-MISSING]
        """,
    )
    monkeypatch.setattr(
        fr_uses_checks,
        "changed_files",
        lambda upstream=None: {"files": [], "source_status": "unavailable"},
    )

    report = fr_uses_checks.check_fr_uses(
        repo_root=tmp_path,
        registry_path=registry_path,
        gate=True,
    )

    assert report["exit_code"] == 0
    assert report["clean"] is False
    assert report["source_status"] == "unavailable"
    assert report["skipped_reason"] == "changed-files unavailable"
