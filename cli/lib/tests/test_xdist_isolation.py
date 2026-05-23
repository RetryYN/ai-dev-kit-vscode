"""PLAN-102: pytest-xdist worker_id 分離 + per-worker HELIX_HOME 検証.

対象設計 (① D-API): docs/plans/PLAN-102 §設計方針 + cli/lib/tests/conftest.py の
helix_worker_home fixture
テスト設計 (③ D-TEST-DESIGN): 本 file docstring inline + DoD AC-3
テストコード (④ D-TEST-CODE): 本 file の test_*
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# PLAN-223: helix_worker_home (session fixture) の env を直接検証するため、
# 後段の helix_function_root (function fixture) による tmp_path override を opt-out
pytestmark = pytest.mark.no_helix_function_root


def test_helix_home_set_to_tmp_dir(helix_worker_home: Path) -> None:
    """helix_worker_home fixture が HELIX_HOME を tmp dir に scope set する."""
    assert os.environ.get("HELIX_HOME") == str(helix_worker_home)
    assert helix_worker_home.exists()
    assert helix_worker_home.is_dir()


def test_helix_project_root_set_to_tmp_dir(helix_worker_home: Path) -> None:
    """HELIX_PROJECT_ROOT も同 tmp dir に scope set されている."""
    assert os.environ.get("HELIX_PROJECT_ROOT") == str(helix_worker_home)


def test_helix_db_path_under_worker_home(helix_worker_home: Path) -> None:
    """HELIX_DB_PATH が worker home 配下に scope set されている."""
    expected = str(helix_worker_home / "helix.db")
    assert os.environ.get("HELIX_DB_PATH") == expected


def test_worker_home_isolated_from_production(helix_worker_home: Path) -> None:
    """worker home が本番 HELIX_HOME (PROJECT_ROOT) と異なる path にある."""
    project_root = Path(__file__).resolve().parents[3]
    assert helix_worker_home != project_root
    assert str(helix_worker_home).startswith("/tmp") or "pytest" in str(helix_worker_home)


def test_helix_db_init_under_worker_home(helix_worker_home: Path) -> None:
    """helix_db.init_db が worker home の db に作成される (本番に書き込まない)."""
    import helix_db

    db_path = helix_worker_home / "isolation-test.db"
    helix_db.init_db(str(db_path))
    assert db_path.exists()
    assert db_path.parent == helix_worker_home
