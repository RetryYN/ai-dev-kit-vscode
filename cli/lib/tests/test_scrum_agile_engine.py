"""DoD 検証: L7-cli-helix-scrum-agile-implplan §2."""

from __future__ import annotations

import importlib
import io
import py_compile
from contextlib import redirect_stdout
from pathlib import Path

import pytest
import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(LIB_DIR))

MODULE_PATH = LIB_DIR / "scrum_agile_engine.py"


def _load_module():
    return importlib.import_module("scrum_agile_engine")


def _project_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(root))
    return root


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_module_py_compile() -> None:
    """DoD 検証: scrum_agile_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_init_creates_state_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: init で Scrum Agile state 一式を初期化する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)

    created = engine.init_state()

    assert (root / ".helix" / "scrum-agile").is_dir()
    assert len(created) == 5
    assert all((root / rel).exists() for rel in created)


def test_backlog_add_and_list_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: backlog add/list が product backlog を保持する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)
    engine.init_state()

    item = engine.add_backlog_item("API 契約整理", "契約の認識差分を詰める", priority="high")
    rows = engine.list_backlog()

    assert item["id"] == "SB-001"
    assert rows[0]["title"] == "API 契約整理"
    assert rows[0]["status"] == "todo"


def test_plan_creates_active_sprint_and_marks_items_planned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: plan は active sprint と sprint backlog を作る。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)
    engine.init_state()
    first = engine.add_backlog_item("認証の見直し", "ユーザーと要件を詰める")
    second = engine.add_backlog_item("権限確認", "レビュー観点を詰める")

    sprint = engine.plan_sprint("認証フローの合意形成", [first["id"], second["id"]])
    sprint_payload = _read_yaml(root / ".helix" / "scrum-agile" / "sprint.yaml")
    backlog_payload = _read_yaml(root / ".helix" / "scrum-agile" / "backlog.yaml")

    assert sprint["sprint_id"] == "SPRINT-001"
    assert sprint_payload["active_sprint"]["goal"] == "認証フローの合意形成"
    assert backlog_payload["items"][0]["status"] == "planned"
    assert backlog_payload["items"][1]["status"] == "planned"


def test_review_requires_active_sprint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: active sprint がない review は fail-close。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)
    engine.init_state()

    with pytest.raises(module.ScrumAgileError, match="active sprint"):
        engine.record_review("レビュー要約", "フィードバック")


def test_retro_records_retrospective_for_active_sprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: retro は active sprint の改善アクションを記録する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)
    engine.init_state()
    item = engine.add_backlog_item("UI 文言調整", "利用者ヒアリング反映")
    engine.plan_sprint("文言の方向合わせ", [item["id"]])

    retro = engine.record_retro("素早く共有できた", "レビュー前の整理不足", "DoD を先に確認する")
    payload = _read_yaml(root / ".helix" / "scrum-agile" / "retros.yaml")

    assert retro["action"] == "DoD を先に確認する"
    assert payload["entries"][0]["sprint_id"] == "SPRINT-001"


def test_increment_completes_sprint_and_sets_reverse_fullback_ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: increment は completed increment と reverse fullback 導線を残す。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)
    engine = module.ScrumAgileEngine(project_root=root)
    engine.init_state()
    item = engine.add_backlog_item("レビュー改善", "ユーザー feedback を反映")
    engine.plan_sprint("レビュー反映を完了する", [item["id"]])
    engine.record_review("方向性を確認", "次工程に進める")
    engine.record_retro("早く確認できた", "説明が足りない", "レビュー観点を固定する")

    increment = engine.record_increment("認証 increment", "ユーザー合意済みの変更を完了")
    sprint_payload = _read_yaml(root / ".helix" / "scrum-agile" / "sprint.yaml")
    backlog_payload = _read_yaml(root / ".helix" / "scrum-agile" / "backlog.yaml")

    assert increment["reverse_fullback_ready"] is True
    assert increment["recommended_next_command"] == "helix reverse fullback"
    assert sprint_payload["active_sprint"] is None
    assert backlog_payload["items"][0]["status"] == "done"


def test_main_prints_increment_guidance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DoD 検証: CLI 出力が Reverse fullback 導線を表示する。"""
    module = _load_module()
    root = _project_root(tmp_path, monkeypatch)

    assert module.main(["init"]) == 0
    assert module.main(["backlog", "add", "--title", "契約更新", "--description", "差分を詰める"]) == 0
    assert module.main(["plan", "--goal", "差分解消", "--item", "SB-001"]) == 0
    assert module.main(["review", "--summary", "方向性確認", "--feedback", "継続"]) == 0
    assert module.main(["retro", "--went-well", "早い合意", "--improve", "記録不足", "--action", "テンプレ追加"]) == 0

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        assert module.main(["increment", "--title", "差分解消 increment", "--summary", "完成"]) == 0

    output = buffer.getvalue()
    assert "helix reverse fullback" in output
    assert "reverse_fullback_ready: true" in output
