import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import workspace_manager
import workspace_snapshot
from workspace_manager import (
    WorkspaceDropAbortedError,
    WorkspaceExistsError,
    WorkspaceMainDirtyError,
    WorkspaceManager,
    WorkspaceMergeConflictError,
    WorkspaceMergeSubmoduleNotSupportedError,
    WorkspaceMergeTargetAheadError,
    WorkspaceNotFoundError,
    WorkspaceUntrackedFilesError,
    _filtered_copy,
    _inject_helix_workspace_env_vars,
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
    (repo / ".gitignore").write_text(
        ".helix/workspaces/\n.helix/helix.db\n.helix/helix.db-*\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "README.md", ".gitignore"],
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


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _commit_seed_state(repo: Path) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed helix state")


def _seed_plan_registry_db(repo: Path) -> None:
    helix_dir = repo / ".helix"
    helix_dir.mkdir(parents=True, exist_ok=True)
    db_path = helix_dir / "helix.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE plan_registry (
                plan_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                kind TEXT NOT NULL,
                layer TEXT NOT NULL,
                drive TEXT NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE plan_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id TEXT NOT NULL,
                dep_type TEXT NOT NULL,
                dep_plan_id TEXT NOT NULL
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO plan_registry (plan_id, title, kind, layer, drive, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("PLAN-156", "Workspace", "impl", "L4", "be", "in_progress"),
                ("PLAN-PARENT", "Parent", "plan", "L3", "be", "accepted"),
                ("PLAN-REQ", "Requirement", "plan", "L3", "be", "accepted"),
                ("PLAN-BLOCK", "Blocked", "plan", "L4", "be", "draft"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO plan_dependencies (plan_id, dep_type, dep_plan_id)
            VALUES (?, ?, ?)
            """,
            [
                ("PLAN-156", "parent", "PLAN-PARENT"),
                ("PLAN-156", "requires", "PLAN-REQ"),
                ("PLAN-156", "blocks", "PLAN-BLOCK"),
            ],
        )


# IT-MOD-02
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


# IT-DB-04
def test_list_workspaces_filters_active_entries(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-ACTIVE")
    manager.create(task_id="PLAN-DROPPED")
    manager._update_registry_status("PLAN-DROPPED", status="dropped", drop_reason="test")

    rows = manager.list_workspaces(status="active")

    assert [row["task_id"] for row in rows] == ["PLAN-ACTIVE"]


def test_exec_in_workspace_returns_exit_code_zero_for_true_command(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-EXEC-TRUE")

    assert manager.exec_in_workspace("PLAN-EXEC-TRUE", "true") == 0


def test_exec_in_workspace_propagates_nonzero_exit_code(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-EXEC-FALSE")

    assert manager.exec_in_workspace("PLAN-EXEC-FALSE", "exit 7") == 7


def test_exec_in_workspace_raises_for_missing_task(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    with pytest.raises(WorkspaceNotFoundError):
        manager.exec_in_workspace("PLAN-MISSING", "true")


def test_exec_in_workspace_raises_for_dropped_status(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-DROPPED")
    manager._update_registry_status("PLAN-DROPPED", status="dropped", drop_reason="test")

    with pytest.raises(ValueError, match="active"):
        manager.exec_in_workspace("PLAN-DROPPED", "true")


def test_exec_in_workspace_injects_helix_workspace_env_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)
    result = manager.create(task_id="PLAN-ENV")
    workspace_path = Path(result["workspace_path"])
    recorded: dict[str, object] = {}

    def fake_run(args, cwd, env, check):  # type: ignore[no-untyped-def]
        recorded["args"] = args
        recorded["cwd"] = cwd
        recorded["env"] = env
        recorded["check"] = check
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr(workspace_manager.subprocess, "run", fake_run)

    exit_code = manager.exec_in_workspace("PLAN-ENV", "printf 'ok'", extra_env={"EXTRA_FLAG": "1"})

    env = recorded["env"]
    assert exit_code == 0
    assert recorded["args"] == ["/bin/bash", "-c", "printf 'ok'"]
    assert recorded["cwd"] == workspace_path
    assert recorded["check"] is False
    assert isinstance(env, dict)
    assert env["HELIX_WORKSPACE_TASK_ID"] == "PLAN-ENV"
    assert env["HELIX_WORKSPACE_PATH"] == str(workspace_path)
    assert env["HELIX_WORKSPACE_BRANCH"] == "workspace/PLAN-ENV"
    assert env["HELIX_PROJECT_ROOT"] == str(workspace_path)
    assert env["EXTRA_FLAG"] == "1"


def test_preflight_detects_main_dirty(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-PREFLIGHT-DIRTY")
    (repo / "README.md").write_text("dirty\n", encoding="utf-8")

    payload = manager.preflight("PLAN-PREFLIGHT-DIRTY")
    issues = {issue["kind"]: issue for issue in payload["issues"]}

    assert payload["task_id"] == "PLAN-PREFLIGHT-DIRTY"
    assert payload["ok"] is True
    assert "checked_at" in payload
    assert issues["main_dirty"]["severity"] == "warn"


## ST-IF-03
def test_preflight_detects_orphan_worktree(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-PREFLIGHT-ORPHAN")
    workspace_path = Path(result["workspace_path"])
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(workspace_path)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = manager.preflight("PLAN-PREFLIGHT-ORPHAN")
    issues = {issue["kind"]: issue for issue in payload["issues"]}

    assert payload["ok"] is False
    assert issues["orphan_worktree"]["severity"] == "error"


def test_preflight_detects_branch_divergence(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-PREFLIGHT-BRANCH")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "README.md").write_text("workspace branch change\n", encoding="utf-8")
    subprocess.run(
        ["git", "commit", "-am", "workspace update"],
        cwd=workspace_path,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = manager.preflight("PLAN-PREFLIGHT-BRANCH")
    issues = {issue["kind"]: issue for issue in payload["issues"]}

    assert payload["ok"] is True
    assert issues["branch_divergence"]["severity"] == "warn"


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


# IT-DB-01
def test_generate_snapshot_extracts_plan_registry(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _seed_plan_registry_db(repo)
    target_path = tmp_path / "snapshot.json"

    payload = workspace_snapshot.generate_snapshot(
        repo,
        target_path,
        task_id="PLAN-156",
        base_sha="deadbeef",
    )

    assert [row["plan_id"] for row in payload["plan_registry"]] == [
        "PLAN-156",
        "PLAN-PARENT",
        "PLAN-REQ",
        "PLAN-BLOCK",
    ]
    assert payload["plan_registry"][0]["parent"] == "PLAN-PARENT"


# IT-IP-03
def test_generate_snapshot_extracts_handover_snapshot(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    handover_dir = repo / ".helix" / "handover"
    handover_dir.mkdir(parents=True, exist_ok=True)
    (handover_dir / "CURRENT.json").write_text(
        json.dumps(
            {
                "task": {
                    "id": "PLAN-156",
                    "title": "workspace",
                    "status": "in_progress",
                },
                "phase": "L4",
                "sprint": ".3",
                "next_actions": ["implement exec", "extend preflight"],
            }
        ),
        encoding="utf-8",
    )
    target_path = tmp_path / "snapshot.json"

    payload = workspace_snapshot.generate_snapshot(
        repo,
        target_path,
        task_id="PLAN-156",
        base_sha="cafebabe",
    )

    assert payload["handover_snapshot"]["task"]["id"] == "PLAN-156"
    assert payload["handover_snapshot"]["phase"] == "L4"
    assert payload["handover_snapshot"]["next_actions"] == ["implement exec", "extend preflight"]


def test_generate_snapshot_extracts_memory_links(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    memory_path = tmp_path / "MEMORY.md"
    memory_path.write_text(
        "\n".join(
            [
                "# Memory",
                "- PLAN-156 keep workspace isolated",
                "- unrelated entry",
                "- PLAN-156 review branch divergence",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HELIX_MEMORY_PATH", str(memory_path))

    payload = workspace_snapshot.generate_snapshot(
        repo,
        tmp_path / "snapshot.json",
        task_id="PLAN-156",
        base_sha="feedface",
    )

    assert payload["memory_links"] == [
        "- PLAN-156 keep workspace isolated",
        "- PLAN-156 review branch divergence",
    ]


def test_generate_snapshot_handles_missing_helix_db_gracefully(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    target_path = tmp_path / "snapshot.json"

    payload = workspace_snapshot.generate_snapshot(
        repo,
        target_path,
        task_id="PLAN-MISSING-DB",
        base_sha="1234567",
    )

    assert payload["plan_registry"] == []
    assert payload["handover_snapshot"] == {}
    assert payload["memory_links"] == []
    assert target_path.exists()


def test_create_writes_registry_file_fallback(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-REGISTRY")

    registry_path = repo / ".helix" / "workspaces" / "PLAN-REGISTRY.yaml"
    assert registry_path.exists()
    payload = workspace_manager._read_yaml_file(registry_path)
    assert payload["status"] == "active"


def test_inject_helix_workspace_env_vars_preserves_os_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BASE_FLAG", "enabled")

    env = _inject_helix_workspace_env_vars(
        "PLAN-156",
        tmp_path / "workspace",
        "workspace/PLAN-156",
        extra_env={"EXTRA_FLAG": "1"},
    )

    assert env["BASE_FLAG"] == "enabled"
    assert env["HELIX_WORKSPACE_TASK_ID"] == "PLAN-156"
    assert env["HELIX_WORKSPACE_BRANCH"] == "workspace/PLAN-156"
    assert env["EXTRA_FLAG"] == "1"
    assert env["HELIX_PROJECT_ROOT"] == str(tmp_path / "workspace")


def test_inject_helix_workspace_env_vars_overrides_parent_helix_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """PLAN-224 Sprint .1: workspace exec で起動した helix CLI が main lock_dir
    を見ないよう、HELIX_PROJECT_ROOT が必ず workspace_path で override されること。
    """
    main_root = tmp_path / "main_repo"
    workspace_path = tmp_path / "workspaces" / "PLAN-X"
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(main_root))

    env = _inject_helix_workspace_env_vars(
        "PLAN-X",
        workspace_path,
        "workspace/PLAN-X",
    )

    assert env["HELIX_PROJECT_ROOT"] == str(workspace_path)
    assert env["HELIX_PROJECT_ROOT"] != str(main_root)


def test_inject_helix_workspace_env_vars_overrides_db_path_dir_project_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """PLAN-224 Sprint .1 tl-advisor P0-2: HELIX_DB_PATH / HELIX_DIR / PROJECT_ROOT
    全てを workspace 側に override し、helix_db.resolve_default_db_path() の
    resolution 順序を踏まえても main DB を見ない保証。
    """
    main_root = tmp_path / "main_repo"
    workspace_path = tmp_path / "workspaces" / "PLAN-Y"

    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(main_root))
    monkeypatch.setenv("PROJECT_ROOT", str(main_root))
    monkeypatch.setenv("HELIX_DIR", str(main_root / ".helix"))
    monkeypatch.setenv("HELIX_DB_PATH", str(main_root / ".helix" / "helix.db"))

    env = _inject_helix_workspace_env_vars(
        "PLAN-Y",
        workspace_path,
        "workspace/PLAN-Y",
    )

    assert env["HELIX_PROJECT_ROOT"] == str(workspace_path)
    assert env["PROJECT_ROOT"] == str(workspace_path)
    assert env["HELIX_DIR"] == str(workspace_path / ".helix")
    assert env["HELIX_DB_PATH"] == str(workspace_path / ".helix" / "helix.db")
    # main 側 path が一切 残っていないこと
    for value in env.values():
        assert str(main_root) not in str(value), f"main root leaked into env: {value}"


def test_merge_aborts_when_main_dirty(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-MERGE-DIRTY")
    (repo / "README.md").write_text("dirty main\n", encoding="utf-8")

    with pytest.raises(WorkspaceMainDirtyError):
        manager.merge("PLAN-MERGE-DIRTY")


def test_merge_aborts_when_workspace_has_untracked(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-UNTRACKED")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "new-untracked.txt").write_text("pending\n", encoding="utf-8")

    with pytest.raises(WorkspaceUntrackedFilesError, match="new-untracked.txt"):
        manager.merge("PLAN-MERGE-UNTRACKED")


def test_merge_aborts_when_target_ref_advanced_without_three_way(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    manager.create(task_id="PLAN-MERGE-AHEAD")
    (repo / "main-only.txt").write_text("advanced\n", encoding="utf-8")
    _git(repo, "add", "main-only.txt")
    _git(repo, "commit", "-m", "advance main")

    with pytest.raises(WorkspaceMergeTargetAheadError):
        manager.merge("PLAN-MERGE-AHEAD")


def test_merge_aborts_on_submodule_patch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)
    subrepo = tmp_path / "subrepo"
    subrepo.mkdir()
    _git(subrepo, "init", "-b", "main")
    _git(subrepo, "config", "user.email", "qa@example.com")
    _git(subrepo, "config", "user.name", "QA")
    (subrepo / "module.txt").write_text("submodule\n", encoding="utf-8")
    _git(subrepo, "add", "module.txt")
    _git(subrepo, "commit", "-m", "init submodule")

    result = manager.create(task_id="PLAN-MERGE-SUBMODULE")
    workspace_path = Path(result["workspace_path"])
    subprocess.run(
        ["git", "-c", "protocol.file.allow=always", "submodule", "add", str(subrepo), "vendor/submodule"],
        cwd=workspace_path,
        check=True,
        capture_output=True,
        text=True,
    )
    _git(workspace_path, "commit", "-m", "add gitlink")

    with pytest.raises(WorkspaceMergeSubmoduleNotSupportedError):
        manager.merge("PLAN-MERGE-SUBMODULE")


def test_merge_success_applies_patch_to_main(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-SUCCESS")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "README.md").write_text("merged from workspace\n", encoding="utf-8")
    _git(workspace_path, "commit", "-am", "workspace change")

    payload = manager.merge("PLAN-MERGE-SUCCESS")
    entry = manager._get_workspace_entry("PLAN-MERGE-SUCCESS")

    assert payload["merged"] is True
    assert Path(payload["patch_path"]).exists()
    assert any(line.endswith("README.md") for line in payload["applied_files"])
    assert (repo / "README.md").read_text(encoding="utf-8") == "merged from workspace\n"
    assert entry is not None
    assert entry["status"] == "merged"
    assert "merged_at" in entry


def test_merge_includes_binary_file_change(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-BINARY")
    workspace_path = Path(result["workspace_path"])
    binary_payload = bytes(range(256))
    (workspace_path / "blob.bin").write_bytes(binary_payload)
    _git(workspace_path, "add", "blob.bin")
    _git(workspace_path, "commit", "-m", "add binary")

    payload = manager.merge("PLAN-MERGE-BINARY")

    assert payload["merged"] is True
    assert (repo / "blob.bin").read_bytes() == binary_payload


def test_merge_conflict_saves_patch_to_trash(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-CONFLICT")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "README.md").write_text("workspace side\n", encoding="utf-8")
    _git(workspace_path, "commit", "-am", "workspace update")

    (repo / "README.md").write_text("main side\n", encoding="utf-8")
    _git(repo, "commit", "-am", "main update")

    with pytest.raises(WorkspaceMergeConflictError, match="merge-conflict.patch"):
        manager.merge("PLAN-MERGE-CONFLICT", three_way=True)

    trash_root = tmp_path / "home" / ".helix" / "workspace-trash" / "PLAN-MERGE-CONFLICT"
    patch_files = list(trash_root.glob("*/merge-conflict.patch"))
    metadata_files = list(trash_root.glob("*/metadata.json"))

    assert patch_files
    assert metadata_files


def test_merge_rename_file(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 P2-1 rename merge fixture."""
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-RENAME")
    workspace_path = Path(result["workspace_path"])
    _git(workspace_path, "mv", "README.md", "RENAMED.md")
    _git(workspace_path, "commit", "-m", "rename readme")

    payload = manager.merge("PLAN-MERGE-RENAME")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "apply rename")
    rename_log = _git(repo, "log", "-M", "--diff-filter=R", "--name-status", "-1").stdout

    assert payload["merged"] is True
    assert not (repo / "README.md").exists()
    assert (repo / "RENAMED.md").read_text(encoding="utf-8") == "hello\n"
    assert "R" in rename_log
    assert "README.md" in rename_log
    assert "RENAMED.md" in rename_log
    assert manager._get_workspace_entry("PLAN-MERGE-RENAME")["status"] == "merged"


def test_merge_chmod_change(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 P2-1 chmod merge fixture."""
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-CHMOD")
    workspace_path = Path(result["workspace_path"])
    readme_path = workspace_path / "README.md"
    readme_path.chmod(0o755)
    _git(workspace_path, "add", "README.md")
    _git(workspace_path, "commit", "-m", "make readme executable")

    payload = manager.merge("PLAN-MERGE-CHMOD")

    assert payload["merged"] is True
    assert (repo / "README.md").stat().st_mode & 0o111
    assert manager._get_workspace_entry("PLAN-MERGE-CHMOD")["status"] == "merged"


def test_merge_symlink_change(tmp_path: Path) -> None:
    """DoD 検証: PLAN-224 Sprint .3 P2-1 symlink merge fixture."""
    repo = _init_repo(tmp_path)
    _seed_helix(repo)
    _commit_seed_state(repo)
    manager = _manager(repo, tmp_path)

    result = manager.create(task_id="PLAN-MERGE-SYMLINK")
    workspace_path = Path(result["workspace_path"])
    (workspace_path / "target.txt").write_text("target\n", encoding="utf-8")
    os.symlink("target.txt", workspace_path / "source-link")
    _git(workspace_path, "add", "target.txt", "source-link")
    _git(workspace_path, "commit", "-m", "add symlink")

    payload = manager.merge("PLAN-MERGE-SYMLINK")

    assert payload["merged"] is True
    assert (repo / "target.txt").read_text(encoding="utf-8") == "target\n"
    assert os.path.islink(repo / "source-link")
    assert os.readlink(repo / "source-link") == "target.txt"
    assert manager._get_workspace_entry("PLAN-MERGE-SYMLINK")["status"] == "merged"
