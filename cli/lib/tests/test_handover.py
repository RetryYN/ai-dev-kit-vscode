import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import handover


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "qa@example.com"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "QA"], cwd=repo, check=True, capture_output=True, text=True)
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True, text=True)
    return repo


def _current_json(repo: Path) -> Path:
    return repo / ".helix" / "handover" / "CURRENT.json"


def test_dump_update_and_clear_completed_e2e(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    handover_dir = repo / ".helix" / "handover"

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "dump",
            "--task-id",
            "TASK-001",
            "--task-title",
            "Add regression tests",
            "--phase",
            "L4",
            "--sprint",
            ".1a",
            "--project",
            "helix-cli",
            "--files",
            "cli/lib/handover.py,cli/lib/migrate.py",
            "--tests",
            "pytest cli/lib/tests/test_handover.py;pytest cli/lib/tests/test_migrate.py",
        ]
    )
    capsys.readouterr()

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "update",
            "--owner",
            "codex",
            "--complete",
            "cli/lib/handover.py",
            "--complete-note",
            "done",
            "--sprint",
            ".2",
        ]
    )
    capsys.readouterr()

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "update",
            "--owner",
            "opus",
            "--status",
            "ready_for_review",
        ]
    )
    capsys.readouterr()

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "status",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["owner"] == "opus"
    assert payload["task"]["status"] == "ready_for_review"
    assert payload["files"]["completed_count"] == 1
    assert payload["files"]["pending"] == ["cli/lib/migrate.py"]

    current = json.loads(_current_json(repo).read_text(encoding="utf-8"))
    assert current["revision"] == 3
    assert current["files"]["completed"] == [{"path": "cli/lib/handover.py", "note": "done"}]
    md_text = (handover_dir / "CURRENT.md").read_text(encoding="utf-8")
    assert "owner_change" in md_text
    assert "status_change" in md_text

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "clear",
            "--reason",
            "completed",
        ]
    )
    output = capsys.readouterr().out

    assert "handover cleared:" in output
    assert not (handover_dir / "CURRENT.json").exists()
    archives = list((handover_dir / "archive").iterdir())
    assert len(archives) == 1
    assert (archives[0] / "CURRENT.json").exists()
    assert (archives[0] / "CURRENT.md").exists()


def test_escalate_generates_markdown_and_sets_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    handover_dir = repo / ".helix" / "handover"

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "dump",
            "--task-id",
            "TASK-002",
            "--task-title",
            "Investigate blocker",
            "--phase",
            "L4",
            "--sprint",
            ".3",
            "--project",
            "helix-cli",
            "--files",
            "cli/lib/handover.py",
        ]
    )
    capsys.readouterr()

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "escalate",
            "--reason",
            "design change needed",
            "--context",
            "D-API update required",
        ]
    )
    capsys.readouterr()

    current = json.loads(_current_json(repo).read_text(encoding="utf-8"))
    assert current["owner"] == "codex"
    assert current["task"]["status"] == "escalated"

    escalation = (handover_dir / "ESCALATION.md").read_text(encoding="utf-8")
    assert "design change needed" in escalation
    assert "D-API update required" in escalation
    assert "TASK-002 Investigate blocker" in escalation


def test_update_ready_for_review_detects_fe_drift_and_writes_escalation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    handover_dir = repo / ".helix" / "handover"

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "dump",
            "--task-id",
            "TASK-DRIFT",
            "--task-title",
            "Detect FE drift",
            "--phase",
            "L4",
            "--sprint",
            ".4",
            "--project",
            "helix-cli",
            "--files",
            "cli/lib/handover.py",
        ]
    )
    capsys.readouterr()

    fe_file = repo / "src" / "features" / "ui-kit" / "D-VIS" / "screen.tsx"
    fe_file.parent.mkdir(parents=True, exist_ok=True)
    fe_file.write_text("export const x = 1;\n", encoding="utf-8")

    handover.main(
        [
            "--handover-dir",
            str(handover_dir),
            "--project-root",
            str(repo),
            "update",
            "--status",
            "ready_for_review",
        ]
    )
    captured = capsys.readouterr()

    assert "scope=backend だが FE ファイル変更を検知" in captured.err
    escalation = (handover_dir / "ESCALATION.md").read_text(encoding="utf-8")
    assert "# HELIX Auto Escalation" in escalation
    assert "src/features/ui-kit/D-VIS/screen.tsx" in escalation


def test_atomic_write_json_with_revision_detects_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_json = tmp_path / "CURRENT.json"
    handover.dump_json(current_json, {"revision": 1, "task": {"status": "in_progress"}})
    monkeypatch.setenv("HELIX_HANDOVER_TEST_SLEEP_SEC", "0.2")
    result: dict[str, object] = {}

    def worker() -> None:
        try:
            handover.atomic_write_json_with_revision(
                current_json,
                {"revision": 2, "task": {"status": "blocked"}},
                1,
            )
            result["ok"] = True
        except Exception as exc:  # pragma: no cover - assertion below validates concrete type.
            result["error"] = exc

    thread = threading.Thread(target=worker)
    thread.start()
    time.sleep(0.05)
    handover.dump_json(current_json, {"revision": 2, "task": {"status": "ready_for_review"}})
    thread.join()

    assert "ok" not in result
    assert isinstance(result["error"], handover.HandoverError)
    assert str(result["error"]) == "revision conflict"
    assert json.loads(current_json.read_text(encoding="utf-8"))["revision"] == 2


def test_dump_rejects_non_backend_scope(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    args = handover.parse_args(
        [
            "--handover-dir",
            str(repo / ".helix" / "handover"),
            "--project-root",
            str(repo),
            "dump",
            "--task-id",
            "TASK-003",
            "--task-title",
            "Bad scope",
            "--phase",
            "L4",
            "--sprint",
            ".1a",
            "--project",
            "helix-cli",
            "--scope",
            "frontend",
        ]
    )

    with pytest.raises(handover.HandoverError) as exc_info:
        handover.cmd_dump(args)

    assert exc_info.value.exit_code == handover.EXIT_INPUT_ERROR
    assert "scope は backend のみ対応です" in str(exc_info.value)


def test_run_git_timeout_raises_handover_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["git", "status"], timeout=30)

    monkeypatch.setattr(handover.subprocess, "run", _raise_timeout)

    with pytest.raises(handover.HandoverError) as exc_info:
        handover.run_git(tmp_path, ["status"], strict=True)

    assert exc_info.value.exit_code == handover.EXIT_PREREQ_ERROR
    assert str(exc_info.value) == "git timeout"


def test_run_git_timeout_raises_handover_error_when_non_strict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["git", "rev-parse", "HEAD"], timeout=30)

    monkeypatch.setattr(handover.subprocess, "run", _raise_timeout)

    with pytest.raises(handover.HandoverError) as exc_info:
        handover.run_git(tmp_path, ["rev-parse", "HEAD"], strict=False)

    assert exc_info.value.exit_code == handover.EXIT_PREREQ_ERROR
    assert str(exc_info.value) == "git timeout"


def test_run_git_timeout_uses_standard_message(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["git", "fetch"], timeout=30)

    monkeypatch.setattr(handover.subprocess, "run", _raise_timeout)

    with pytest.raises(handover.HandoverError) as exc_info:
        handover.run_git(tmp_path, ["fetch"], strict=True)

    assert str(exc_info.value) == "git timeout"


def test_archive_current_rollback_on_partial_failure(tmp_path: Path) -> None:
    handover_dir = tmp_path / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    paths = handover.current_paths(handover_dir)

    paths["json"].write_text('{"a":1}\n', encoding="utf-8")
    paths["md"].write_text("# current\n", encoding="utf-8")

    original_replace = handover.os.replace
    call_count = {"n": 0}

    def _flaky_replace(src, dst):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise OSError("simulated replace failure")
        return original_replace(src, dst)

    with patch("handover.os.replace", side_effect=_flaky_replace):
        with pytest.raises(handover.HandoverError) as exc_info:
            handover.archive_current(paths)

    assert "archive commit failed" in str(exc_info.value)
    assert paths["json"].exists()
    assert paths["md"].exists()
    assert paths["json"].read_text(encoding="utf-8") == '{"a":1}\n'
    assert paths["md"].read_text(encoding="utf-8") == "# current\n"
    archived_json_files = list(paths["archive"].glob("*/CURRENT.json"))
    assert archived_json_files == []


def test_archive_current_idempotent_on_success(tmp_path: Path) -> None:
    handover_dir = tmp_path / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    paths = handover.current_paths(handover_dir)

    paths["json"].write_text('{"ok":true}\n', encoding="utf-8")
    paths["md"].write_text("# md\n", encoding="utf-8")
    paths["escalation"].write_text("# esc\n", encoding="utf-8")

    archive_dir = handover.archive_current(paths)

    assert archive_dir.exists()
    assert not paths["json"].exists()
    assert not paths["md"].exists()
    assert not paths["escalation"].exists()
    assert (archive_dir / "CURRENT.json").read_text(encoding="utf-8") == '{"ok":true}\n'
    assert (archive_dir / "CURRENT.md").read_text(encoding="utf-8") == "# md\n"
    assert (archive_dir / "ESCALATION.md").read_text(encoding="utf-8") == "# esc\n"


def test_archive_current_no_staged_when_nothing_exists(tmp_path: Path) -> None:
    handover_dir = tmp_path / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    paths = handover.current_paths(handover_dir)

    with pytest.raises(handover.HandoverError) as exc_info:
        handover.archive_current(paths)

    assert str(exc_info.value) == "archive 対象ファイルが存在しません"
    assert list(paths["archive"].glob("*/CURRENT.json")) == []
    assert list(paths["archive"].glob("*/CURRENT.md")) == []
    assert list(paths["archive"].glob("*/ESCALATION.md")) == []
