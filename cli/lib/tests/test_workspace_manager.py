import json
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import workspace_manager
from workspace_manager import (
    WorkspaceDropAbortedError,
    WorkspaceExistsError,
    WorkspaceManager,
    _filtered_copy,
)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "qa@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "QA"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo


def _seed_helix(repo: Path) -> None:
    helix_dir = repo / ".helix"
    (helix_dir / "config").mkdir(parents=True, exist_ok=True)
    (helix_dir / "templates").mkdir(parents=True, exist_ok=True)
    (helix_dir / "tmp").mkdir(parents=True, exist_ok=True)
    (helix_dir / "workspaces").mkdir(parents=True, exist_ok=True)
    (helix_dir / "cache").mkdir(parents=True, exist_ok=True)
    (helix_dir / "logs").mkdir(parents=True, exist_ok=True)
    (helix_dir / "audit" / "runs").mkdir(parents=True, exist_ok=True)
    (helix_dir / "config" / "settings.yaml").write_text("name: sample\n", encoding="utf-8")
    (helix_dir / "phase.yaml").write_text("current_phase: L4\n", encoding="utf-8")
    (helix_dir / "task-plan.yaml").write_text("plan_id: PLAN-156\n", encoding="utf-8")
    (helix_dir / "templates" / "base.txt").write_text("template\n", encoding="utf-8")
    (helix_dir / "tmp" / "large.bin").write_bytes(b"x" * 2048)
    (helix_dir / "config" / "session.db-wal").write_text("skip\n", encoding="utf-8")


def _manager(repo: Path, tmp_path: Path) -> WorkspaceManager:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    return WorkspaceManager(project_root=repo, home=home)


def test_create_creates_worktree_and_workspace_manifest(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-156")

    workspace_path = Path(result["workspace_path"])
    manifest_path = workspace_path / ".helix" / "workspace.yaml"
    assert workspace_path.exists()
    assert manifest_path.exists()
    assert (workspace_path / "workspace_state_snapshot.json").exists()
    assert "workspace/PLAN-156" == result["branch"]
    assert "PLAN-156" in subprocess.run(
        ["git", "worktree", "list"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_create_twice_raises_workspace_exists(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-156")
    with pytest.raises(WorkspaceExistsError):
        manager.create(task_id="PLAN-156")


def test_create_does_not_copy_denylist_content(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-DENY")
    workspace_path = Path(result["workspace_path"])

    assert not (workspace_path / ".helix" / "tmp").exists()
    assert not (workspace_path / ".helix" / "cache").exists()
    assert not (workspace_path / ".helix" / "logs").exists()


def test_create_copies_allowlist_content(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-ALLOW")
    workspace_path = Path(result["workspace_path"])

    assert (workspace_path / ".helix" / "config" / "settings.yaml").exists()
    assert (workspace_path / ".helix" / "phase.yaml").exists()
    assert (workspace_path / ".helix" / "task-plan.yaml").exists()
    assert (workspace_path / ".helix" / "templates" / "base.txt").exists()


def test_filtered_copy_skips_db_wal_glob(tmp_path: Path) -> None:
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "config").mkdir(parents=True)
    (src / "config" / "state.db-wal").write_text("skip\n", encoding="utf-8")
    (src / "config" / "keep.txt").write_text("keep\n", encoding="utf-8")
    (src / "phase.yaml").write_text("phase: L4\n", encoding="utf-8")

    stats = _filtered_copy(src, dst)

    assert (dst / "config" / "keep.txt").exists()
    assert not (dst / "config" / "state.db-wal").exists()
    assert stats["skipped_count"] >= 1


def test_list_workspaces_filters_active_entries(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-ACTIVE")
    manager.create(task_id="PLAN-DROPPED")
    manager._update_registry_status("PLAN-DROPPED", status="dropped", drop_reason="test")

    rows = manager.list_workspaces(status="active")

    assert [row["task_id"] for row in rows] == ["PLAN-ACTIVE"]


def test_preflight_reports_main_dirty_and_orphan(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-PREFLIGHT")
    workspace_path = Path(result["workspace_path"])
    (repo / "README.md").write_text("dirty\n", encoding="utf-8")
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(workspace_path)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = manager.preflight("PLAN-PREFLIGHT")
    codes = {issue["code"] for issue in payload["issues"]}
    assert payload["ok"] is False
    assert "main_dirty" in codes
    assert "orphan_worktree" in codes


def test_drop_default_aborts_when_workspace_has_changes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-DROP")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "README.md").write_text("changed\n", encoding="utf-8")

    with pytest.raises(WorkspaceDropAbortedError):
        manager.drop("PLAN-DROP")


def test_drop_force_archives_and_removes_workspace(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-FORCE")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "untracked.txt").write_text("keep\n", encoding="utf-8")
    drop_result = manager.drop("PLAN-FORCE", force=True)

    trash_path = Path(drop_result["trash_path"])
    assert drop_result["dropped"] is True
    assert not workspace_path.exists()
    assert (trash_path / "changes.bundle").exists()
    assert (trash_path / "untracked.tar.gz").exists()
    assert manager.list_workspaces(status="dropped")[0]["task_id"] == "PLAN-FORCE"


def test_prune_dry_run_lists_orphan_candidates_without_mutation(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)
    registry_path = repo / ".helix" / "workspaces" / "PLAN-ORPHAN.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        "task_id: PLAN-ORPHAN\nworkspace_path: /tmp/missing\nstatus: active\n",
        encoding="utf-8",
    )

    stale = manager.prune(dry_run=True)

    assert stale == ["PLAN-ORPHAN"]
    assert registry_path.exists()


def test_generate_snapshot_minimal_schema_version_one(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-SNAPSHOT")
    snapshot = json.loads(Path(result["snapshot_path"]).read_text(encoding="utf-8"))

    assert snapshot["schema_version"] == 1
    assert snapshot["task_id"] == "PLAN-SNAPSHOT"


def test_create_writes_registry_file_fallback(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-REGISTRY")

    registry_path = repo / ".helix" / "workspaces" / "PLAN-REGISTRY.yaml"
    assert registry_path.exists()
    payload = workspace_manager._read_yaml_file(registry_path)
    assert payload["status"] == "active"
