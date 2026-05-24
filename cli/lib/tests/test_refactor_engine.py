"""DoD 検証: L7-cli-helix-refactor-implplan §2.D / §4.

Refactor mode の session 管理、保護網比較、router 連携 metadata を固定する。
"""

from __future__ import annotations

import importlib
import json
import os
import py_compile
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

MODULE_PATH = LIB_DIR / "refactor_engine.py"


def _load_module():
    return importlib.import_module("refactor_engine")


def _completed(
    args: list[str] | tuple[str, ...],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(args), returncode, stdout, stderr)


def _make_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("HELIX_HOME", str(Path(__file__).resolve().parents[3]))
    return project_root


def _write_target(project_root: Path, relative_path: str = "cli/lib/sample.py") -> Path:
    target = project_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("print('sample')\n", encoding="utf-8")
    return target


def _make_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_module()
    project_root = _make_project(tmp_path, monkeypatch)
    return module, module.RefactorEngine(project_root=project_root), project_root


def _active_session(project_root: Path) -> dict[str, object]:
    session_path = project_root / ".helix" / "refactor-session.json"
    return json.loads(session_path.read_text(encoding="utf-8"))


def test_module_py_compile() -> None:
    """DoD 検証: refactor_engine.py が py_compile を通る。"""
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_run_test_cmd_parses_pytest_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: pytest summary から passed/failed/skipped を抽出する。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            ["pytest", "-q"],
            stdout="==================== 14 passed, 1 skipped in 0.20s ====================\n",
        ),
    )

    result = engine.run_test_cmd("pytest -q")

    assert result.passed == 14
    assert result.failed == 0
    assert result.skipped == 1
    assert result.total == 15


def test_run_test_cmd_parses_bats_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: bats summary から件数を抽出する。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: _completed(
            ["bats", "sample.bats"],
            stdout="# tests 6\n# pass 5\n# skip 0\n# fail 1\n",
            returncode=1,
        ),
    )

    result = engine.run_test_cmd("bats sample.bats")

    assert result.passed == 5
    assert result.failed == 1
    assert result.skipped == 0
    assert result.total == 6


def test_run_test_cmd_falls_back_to_exit_code_when_counts_unknown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 不明フォーマット時は exit code ベースで扱う。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: _completed(["custom"], stdout="green\n", returncode=0),
    )

    result = engine.run_test_cmd("custom")

    assert result.ok is True
    assert result.total == 0
    assert result.failed == 0


def test_init_session_creates_state_with_linked_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: init は session と baseline を記録する。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=4, failed=0, skipped=1, total=5, stdout="", stderr=""),
    )

    session = engine.init_session(
        targets=[str(target.relative_to(project_root))],
        test_cmd="pytest cli/lib/tests/test_skill_recommender.py -q",
        plan_id="L7-cli-helix-refactor-impl",
    )

    stored = _active_session(project_root)
    assert session.trace_status == "linked"
    assert stored["baseline_passed"] == 4
    assert stored["baseline_total"] == 5
    assert stored["targets"] == ["cli/lib/sample.py"]
    assert stored["status"] == "active"


def test_init_session_rejects_missing_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 対象ファイル不在は fail-close。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)

    with pytest.raises(module.RefactorInputError, match="target not found"):
        engine.init_session(targets=["cli/lib/missing.py"], test_cmd="pytest -q", plan_id="PLAN-X")


def test_init_session_rejects_red_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 保護網が赤なら init を中止する。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=1, passed=3, failed=1, skipped=0, total=4, stdout="", stderr="boom"),
    )

    with pytest.raises(module.RefactorCheckError, match="baseline tests failed"):
        engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")


def test_init_session_records_route_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: route 由来 metadata を session に残す。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=2, failed=0, skipped=0, total=2, stdout="", stderr=""),
    )

    session = engine.init_session(
        targets=[str(target.relative_to(project_root))],
        test_cmd="pytest -q",
        plan_id="PLAN-X",
        signal_id="drift",
        auto_routed_from="helix-route",
        drift_type="code_smell",
    )

    assert session.route_signal == "drift"
    assert session.routed_from == "helix-route"
    assert session.drift_type == "code_smell"


def test_init_session_rejects_unsupported_drift_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: Refactor scope 外 drift_type は拒否する。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )

    with pytest.raises(module.RefactorInputError, match="unsupported drift_type"):
        engine.init_session(
            targets=[str(target.relative_to(project_root))],
            test_cmd="pytest -q",
            plan_id="PLAN-X",
            drift_type="schema",
        )


def test_init_session_without_plan_id_is_unlinked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: plan_id 省略時は trace_status=unlinked。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )

    session = engine.init_session(
        targets=[str(target.relative_to(project_root))],
        test_cmd="pytest -q",
        plan_id=None,
    )

    assert session.trace_status == "unlinked"
    assert _active_session(project_root)["trace_status"] == "unlinked"


def test_check_session_passes_when_baseline_is_maintained(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: baseline と同等以上なら green。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=3, failed=0, skipped=0, total=3, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")

    result = engine.check_session()

    assert result.ok is True
    assert result.regression_reason is None
    assert _active_session(project_root)["check_count"] == 1


def test_check_session_detects_failed_regression(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: failed 増加は regression。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=3, failed=0, skipped=0, total=3, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=1, passed=2, failed=1, skipped=0, total=3, stdout="", stderr=""),
    )

    result = engine.check_session()

    assert result.ok is False
    assert result.regression_reason == "failed_count"


def test_check_session_detects_total_drop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: テスト総数減少も regression。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=4, failed=0, skipped=0, total=4, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=3, failed=0, skipped=0, total=3, stdout="", stderr=""),
    )

    result = engine.check_session()

    assert result.ok is False
    assert result.regression_reason == "total_count"


def test_check_session_requires_active_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: session なしの check は入力エラー。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)

    with pytest.raises(module.RefactorInputError, match="no active refactor session"):
        engine.check_session()


def test_status_session_supports_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: status は JSON 化できる。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=2, failed=0, skipped=0, total=2, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")

    payload = engine.status_payload()

    assert payload["targets"] == ["cli/lib/sample.py"]
    assert payload["baseline"]["passed"] == 2
    assert payload["plan_id"] == "PLAN-X"


def test_status_session_requires_active_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: session なしの status は入力エラー。"""
    module, engine, _project_root = _make_engine(tmp_path, monkeypatch)

    with pytest.raises(module.RefactorInputError, match="no active refactor session"):
        engine.status_payload()


def test_done_session_clears_file_after_green_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: done は最終 check 緑で session を閉じる。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")

    engine.done_session(force=False, reason=None)

    assert not (project_root / ".helix" / "refactor-session.json").exists()


def test_done_session_rejects_regression_and_keeps_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: regression 時は close せず session を保持する。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=2, failed=0, skipped=0, total=2, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=1, passed=1, failed=1, skipped=0, total=2, stdout="", stderr=""),
    )

    with pytest.raises(module.RefactorCheckError, match="regression exists"):
        engine.done_session(force=False, reason=None)

    assert (project_root / ".helix" / "refactor-session.json").exists()


def test_done_session_force_records_audit_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: force close は理由を audit log に残す。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")

    engine.done_session(force=True, reason="emergency")

    audit_log = (project_root / ".helix" / "refactor-session.audit.log").read_text(encoding="utf-8")
    assert "emergency" in audit_log
    assert "force_close_reason" in audit_log


def test_concurrent_init_allows_only_one_active_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 並行 init で二重 session を作らない。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)

    def fake_run(cmd: str):
        time.sleep(0.05)
        return module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr="")

    monkeypatch.setattr(engine, "run_test_cmd", fake_run)
    outcomes: list[str] = []

    def worker() -> None:
        try:
            engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")
            outcomes.append("ok")
        except Exception:
            outcomes.append("error")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["error", "ok"]
    assert (project_root / ".helix" / "refactor-session.json").exists()


def test_concurrent_check_updates_count_without_lost_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 並行 check でも check_count が欠落しない。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")

    def slow_green(cmd: str):
        time.sleep(0.05)
        return module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr="")

    monkeypatch.setattr(engine, "run_test_cmd", slow_green)
    threads = [threading.Thread(target=engine.check_session) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert _active_session(project_root)["check_count"] == 4


def test_concurrent_done_keeps_single_close(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD 検証: 並行 done で session 削除が壊れない。"""
    module, engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)
    monkeypatch.setattr(
        engine,
        "run_test_cmd",
        lambda cmd: module.TestResult(command=cmd, returncode=0, passed=1, failed=0, skipped=0, total=1, stdout="", stderr=""),
    )
    engine.init_session(targets=[str(target.relative_to(project_root))], test_cmd="pytest -q", plan_id="PLAN-X")
    outcomes: list[str] = []

    def worker() -> None:
        try:
            engine.done_session(force=True, reason="parallel close")
            outcomes.append("ok")
        except Exception:
            outcomes.append("error")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["error", "ok"]
    assert not (project_root / ".helix" / "refactor-session.json").exists()


def test_main_requires_test_cmd_for_init(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DoD 検証: init は --test-cmd 必須。"""
    module, _engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)

    exit_code = module.main(["init", "--target", str(target.relative_to(project_root))])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--test-cmd is required" in captured.err


def test_main_status_json_and_done_force_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DoD 検証: CLI main で init/status/done を通せる。"""
    module, _engine, project_root = _make_engine(tmp_path, monkeypatch)
    target = _write_target(project_root)

    def fake_run(*args, **kwargs):
        return _completed(args[0], stdout="1 passed\n", returncode=0)

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.main(["init", "--target", str(target.relative_to(project_root)), "--test-cmd", "pytest -q", "--plan-id", "PLAN-X"]) == 0
    capsys.readouterr()

    assert module.main(["status", "--json"]) == 0
    status_payload = json.loads(capsys.readouterr().out)
    assert status_payload["plan_id"] == "PLAN-X"

    assert module.main(["done", "--force", "--reason", "manual override"]) == 0
    done_output = capsys.readouterr().out
    assert "manual override" in done_output
    assert not (project_root / ".helix" / "refactor-session.json").exists()
