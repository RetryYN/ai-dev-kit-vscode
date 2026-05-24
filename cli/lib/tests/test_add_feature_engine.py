"""DoD 検証: docs/plans/L7/L7-cli-helix-add-feature-implplan.md §4."""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import add_feature_engine


MODULE_PATH = LIB_DIR / "add_feature_engine.py"


def _engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> add_feature_engine.AddFeatureEngine:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))
    return add_feature_engine.AddFeatureEngine(project_root=root)


def test_module_py_compile() -> None:
    """DoD 検証: add_feature_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_add_design_creates_session_and_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: add-design は CURRENT.json と markdown log を初期化する。"""
    engine = _engine(tmp_path, monkeypatch)

    session = engine.add_design(
        feature_id="user-auth",
        summary="認証 feature の設計追補",
        requires_plan="PLAN-BASE-DESIGN",
        design_docs=["docs/design/user-auth.md"],
        requirement_layers=["L1"],
    )

    assert session.status == "design_supplemented"
    assert engine.current_path.exists()
    assert (engine.project_root / session.log_path).exists()
    assert session.route_targets[0]["layer"] == "L1"


def test_add_impl_requires_active_design(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: add-impl 単独実行は fail-close。"""
    engine = _engine(tmp_path, monkeypatch)

    with pytest.raises(add_feature_engine.AddFeatureError, match="No active add-feature session"):
        engine.add_impl(
            feature_id="user-auth",
            summary="認証 feature の実装追補",
            requires_plan="PLAN-BASE-IMPL",
            modules=["cli/lib/auth.py"],
        )


def test_add_impl_updates_session_and_route_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: add-impl 後は L8/L9 回帰に進める route payload を返す。"""
    engine = _engine(tmp_path, monkeypatch)
    engine.add_design(
        feature_id="user-auth",
        summary="認証 feature の設計追補",
        requires_plan="PLAN-BASE-DESIGN",
        requirement_layers=["L3"],
    )

    session = engine.add_impl(
        feature_id="user-auth",
        summary="認証 feature の実装追補",
        requires_plan="PLAN-BASE-IMPL",
        modules=["cli/lib/auth.py"],
        test_paths=["cli/lib/tests/test_auth.py"],
    )
    payload = engine.build_route_payload()

    assert session.status == "implementation_supplemented"
    assert session.modules == ["cli/lib/auth.py"]
    assert session.test_paths == ["cli/lib/tests/test_auth.py"]
    assert payload["ready_for_integration"] is True
    assert [item["layer"] for item in payload["routes"]][-2:] == ["L8", "L9"]


def test_main_status_emits_feature_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DoD 検証: status は現在の add-feature session を表示する。"""
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))

    assert (
        add_feature_engine.main(
            [
                "add-design",
                "--feature",
                "user-auth",
                "--summary",
                "認証 feature の設計追補",
                "--requires-plan",
                "PLAN-BASE-DESIGN",
            ]
        )
        == 0
    )

    rc = add_feature_engine.main(["status"])
    output = capsys.readouterr().out

    assert rc == 0
    assert "[HELIX Add-feature] user-auth (design_supplemented)" in output
