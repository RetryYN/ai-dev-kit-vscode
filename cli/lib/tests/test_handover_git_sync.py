import json
import subprocess
import sys
from pathlib import Path

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


def _handover_dir(repo: Path) -> Path:
    return repo / ".helix" / "handover"


def _current_json(repo: Path) -> Path:
    return _handover_dir(repo) / "CURRENT.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _dump_handover(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    handover.main(
        [
            "--handover-dir",
            str(_handover_dir(repo)),
            "--project-root",
            str(repo),
            "dump",
            "--task-id",
            "TASK-GIT-SYNC",
            "--task-title",
            "Git sync regression",
            "--phase",
            "L4",
            "--sprint",
            ".2",
            "--project",
            "helix-cli",
            "--files",
            "cli/lib/handover.py",
        ]
    )
    capsys.readouterr()


def _commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    path = repo / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", rel_path], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True, text=True)


def test_cmd_update_refreshes_git_snapshot_when_state_changes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    _dump_handover(repo, capsys)
    before = json.loads(_current_json(repo).read_text(encoding="utf-8"))

    _commit_file(repo, "feature.txt", "next\n", "advance head")
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    expected = {
        "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "head_sha": _git(repo, "rev-parse", "HEAD"),
        "dirty": True,
    }

    handover.main(
        [
            "--handover-dir",
            str(_handover_dir(repo)),
            "--project-root",
            str(repo),
            "update",
            "--owner",
            "codex",
        ]
    )
    capsys.readouterr()

    current = json.loads(_current_json(repo).read_text(encoding="utf-8"))
    assert current["git"]["branch"] == expected["branch"]
    assert current["git"]["head_sha"] == expected["head_sha"]
    assert current["git"]["dirty"] is expected["dirty"]
    assert current["git"]["previous_head_sha"] == before["git"]["head_sha"]


def test_cmd_resume_refreshes_git_snapshot_to_current_head(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _init_repo(tmp_path)
    _dump_handover(repo, capsys)
    before = json.loads(_current_json(repo).read_text(encoding="utf-8"))

    _commit_file(repo, "feature.txt", "next\n", "advance head")
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    expected = {
        "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "head_sha": _git(repo, "rev-parse", "HEAD"),
        "dirty": True,
    }

    handover.main(
        [
            "--handover-dir",
            str(_handover_dir(repo)),
            "--project-root",
            str(repo),
            "resume",
            "--note",
            "refresh git snapshot",
        ]
    )
    capsys.readouterr()

    current = json.loads(_current_json(repo).read_text(encoding="utf-8"))
    assert current["owner"] == "opus"
    assert current["task"]["status"] == "in_progress"
    assert current["git"]["branch"] == expected["branch"]
    assert current["git"]["head_sha"] == expected["head_sha"]
    assert current["git"]["dirty"] is expected["dirty"]


def test_stale_check_uses_merge_base_reachability(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    state = {
        "git": {"branch": "main", "head_sha": "a" * 40},
        "updated_at": handover.now_iso(),
    }

    def _fake_run_git(project_root: Path, args: list[str], strict: bool = True) -> str | None:
        calls.append(args)
        if args == ["rev-parse", "--abbrev-ref", "HEAD"]:
            return "main"
        if args == ["cat-file", "-e", f"{'a' * 40}^{{commit}}"]:
            return ""
        if args == ["merge-base", "--is-ancestor", "a" * 40, "HEAD"]:
            return ""
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(handover, "run_git", _fake_run_git)

    stale, reasons = handover.stale_check(state, tmp_path, True)

    assert stale is False
    assert reasons == []
    assert not any(args and args[0] == "log" for args in calls)
