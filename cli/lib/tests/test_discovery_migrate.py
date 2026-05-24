"""DoD 検証: docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md MT-007-MT-016"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import discovery_migrate


def _write_sample_scrum_dir(base: Path) -> Path:
    src = base / ".helix" / "scrum"
    (src / "verify" / "H001").mkdir(parents=True, exist_ok=True)
    (src / "backlog.yaml").write_text("hypotheses:\n  H001:\n    title: sample\n", encoding="utf-8")
    (src / "sprint.yaml").write_text("current_sprint: 1\n", encoding="utf-8")
    (src / "verify" / "H001" / "check.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    return src


def test_generate_manifest_lists_relative_files(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)

    manifest = discovery_migrate.generate_manifest(src)

    names = [entry["path"] for entry in manifest["files"]]
    assert names == sorted(names)
    assert "backlog.yaml" in names
    assert "verify/H001/check.sh" in names
    assert manifest["file_count"] == len(names)


def test_migrate_dry_run_reports_copy_plan_without_writing(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)
    dst = tmp_path / ".helix" / "discovery"

    result = discovery_migrate.migrate(
        src=src,
        dst=dst,
        dry_run=True,
        smoke_check=lambda path: None,
    )

    assert result.status == "dry_run"
    assert result.file_count >= 3
    assert not dst.exists()


def test_migrate_copies_tree_and_writes_manifest(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)
    dst = tmp_path / ".helix" / "discovery"

    result = discovery_migrate.migrate(src=src, dst=dst, smoke_check=lambda path: None)

    assert result.status == "complete"
    assert (dst / "backlog.yaml").exists()
    manifest_path = dst / ".migration-manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["src"].endswith(".helix/scrum")
    assert payload["dst"].endswith(".helix/discovery")
    assert payload["file_count"] == result.file_count
    readme = (src / "README.deprecated").read_text(encoding="utf-8")
    assert ".helix/discovery/" in readme


def test_migrate_is_idempotent_when_manifest_matches(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)
    dst = tmp_path / ".helix" / "discovery"

    first = discovery_migrate.migrate(src=src, dst=dst, smoke_check=lambda path: None)
    second = discovery_migrate.migrate(src=src, dst=dst, smoke_check=lambda path: None)

    assert first.status == "complete"
    assert second.status == "skipped"


def test_migrate_aborts_on_conflict_without_merge_strategy(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)
    dst = tmp_path / ".helix" / "discovery"
    dst.mkdir(parents=True)
    (dst / "backlog.yaml").write_text("hypotheses:\n  H999:\n    title: existing\n", encoding="utf-8")

    with pytest.raises(discovery_migrate.MigrationError, match="手動"):
        discovery_migrate.migrate(src=src, dst=dst, smoke_check=lambda path: None)


def test_migrate_rejects_symlink_in_source(tmp_path: Path) -> None:
    src = _write_sample_scrum_dir(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    os.symlink(outside, src / "symlink.txt")

    with pytest.raises(discovery_migrate.MigrationError, match="symlink"):
        discovery_migrate.generate_manifest(src)

