#!/usr/bin/env python3
"""HELIX workspace manager (PLAN-156 / ADR-040 implementation)."""

from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from . import compatibility_adapter, helix_db, yaml_parser
    from .workspace_snapshot import generate_snapshot
except ImportError:  # pragma: no cover
    REPO_ROOT = Path(__file__).resolve().parents[2]
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from cli.lib import compatibility_adapter, helix_db, yaml_parser  # type: ignore[no-redef]
    from cli.lib.workspace_snapshot import generate_snapshot  # type: ignore[no-redef]


ALLOWLIST_PATHS = [
    ".helix/config",
    ".helix/phase.yaml",
    ".helix/task-plan.yaml",
    ".helix/templates",
]
DENYLIST_PATHS = [
    ".helix/tmp",
    ".helix/backups",
    ".helix/workspaces",
    ".helix/audit/runs",
    ".helix/logs",
    ".helix/cache",
]
DENYLIST_GLOBS = [
    "*.db-wal",
    "*.db-shm",
]


class WorkspaceExistsError(Exception):
    """Raised when a workspace already exists for a task."""


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace cannot be found."""


class GitWorktreeError(Exception):
    """Raised when a git worktree command fails."""


class WorkspaceDropAbortedError(Exception):
    """Raised when a destructive drop is rejected without --force."""


def _now_iso8601() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _strip_helix_prefix(path: str) -> str:
    return path[7:] if path.startswith(".helix/") else path


def _matches_glob(path: Path) -> bool:
    return any(path.match(pattern) for pattern in DENYLIST_GLOBS)


def _is_denied(path: Path) -> bool:
    normalized = path.as_posix().strip("/")
    if not normalized:
        return False
    for deny in DENYLIST_PATHS:
        deny_rel = _strip_helix_prefix(deny).strip("/")
        if normalized == deny_rel or normalized.startswith(f"{deny_rel}/"):
            return True
    return _matches_glob(path)


def _read_yaml_file(path: Path) -> dict[str, Any]:
    payload = yaml_parser.parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid YAML object: {path}")
    return payload


def _write_yaml_file(path: Path, payload: dict[str, Any], header_lines: list[str] | None = None) -> None:
    lines: list[str] = []
    if header_lines:
        lines.extend(header_lines)
    lines.append(yaml_parser.dump_yaml(payload).rstrip())
    body = "\n".join(line for line in lines if line != "") + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _registry_functions() -> dict[str, Any]:
    names = (
        "workspace_registry_insert",
        "workspace_registry_get",
        "workspace_registry_list",
        "workspace_registry_update_status",
    )
    return {name: getattr(helix_db, name, None) for name in names}


def _inject_helix_workspace_env_vars(
    task_id: str,
    workspace_path: Path,
    branch: str,
    *,
    extra_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return env with HELIX workspace metadata injected for subprocess use.

    HELIX_PROJECT_ROOT / HELIX_DB_PATH / HELIX_DIR / PROJECT_ROOT を workspace
    side に明示上書きする。PLAN-224 Sprint .1 tl-advisor adversarial check で
    確認: 親 process の HELIX_PROJECT_ROOT を上書きするだけでは不足で、
    helix_db.resolve_default_db_path() の resolution 順序が

        1. HELIX_DB_PATH (env)
        2. HELIX_PROJECT_ROOT / PROJECT_ROOT (env)
        3. HELIX_DIR (env)
        4. cwd

    のため、HELIX_DB_PATH が親から継承されたままだと workspace 内 helix CLI が
    main の helix.db を read/write してしまう (ADR-040 D3 違反)。同様に
    concurrent_lock._resolve_lock_dir() は HELIX_PROJECT_ROOT を見るので、
    PROJECT_ROOT/HELIX_DIR も含めて workspace 配下に固定する。
    """
    workspace_helix_dir = workspace_path / ".helix"
    workspace_db_path = workspace_helix_dir / "helix.db"
    env = os.environ.copy()
    env.update(
        {
            "HELIX_WORKSPACE_TASK_ID": task_id,
            "HELIX_WORKSPACE_PATH": str(workspace_path),
            "HELIX_WORKSPACE_BRANCH": branch,
            "HELIX_PROJECT_ROOT": str(workspace_path),
            "PROJECT_ROOT": str(workspace_path),
            "HELIX_DIR": str(workspace_helix_dir),
            "HELIX_DB_PATH": str(workspace_db_path),
        }
    )
    if extra_env:
        env.update({str(key): str(value) for key, value in extra_env.items()})
    return env


def _filtered_copy(src_root: Path, dst_root: Path) -> dict:
    """Copy allowlisted `.helix/` content while honoring denylist rules."""
    copied_count = 0
    skipped_count = 0
    total_bytes = 0

    if not src_root.exists():
        dst_root.mkdir(parents=True, exist_ok=True)
        return {
            "copied_count": copied_count,
            "skipped_count": skipped_count,
            "total_bytes": total_bytes,
        }

    dst_root.mkdir(parents=True, exist_ok=True)
    for allow_entry in ALLOWLIST_PATHS:
        relative_allow = Path(_strip_helix_prefix(allow_entry))
        source = src_root / relative_allow
        if not source.exists():
            continue
        if source.is_file():
            if _is_denied(relative_allow):
                skipped_count += 1
                continue
            target = dst_root / relative_allow
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied_count += 1
            total_bytes += source.stat().st_size
            continue

        for current_root, dirnames, filenames in os.walk(source):
            current_path = Path(current_root)
            rel_root = current_path.relative_to(src_root)

            kept_dirs: list[str] = []
            for dirname in dirnames:
                rel_dir = rel_root / dirname
                if _is_denied(rel_dir):
                    skipped_count += 1
                    continue
                kept_dirs.append(dirname)
            dirnames[:] = kept_dirs

            target_root = dst_root / rel_root
            target_root.mkdir(parents=True, exist_ok=True)
            for filename in filenames:
                rel_file = rel_root / filename
                if _is_denied(rel_file):
                    skipped_count += 1
                    continue
                source_file = src_root / rel_file
                target_file = dst_root / rel_file
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_file, target_file)
                copied_count += 1
                total_bytes += source_file.stat().st_size

    return {
        "copied_count": copied_count,
        "skipped_count": skipped_count,
        "total_bytes": total_bytes,
    }


class WorkspaceManager:
    """Manage git-worktree-backed task workspaces."""

    def __init__(self, project_root: Path, home: Path | None = None):
        self.project_root = project_root.resolve()
        self.home = (home or Path.home()).expanduser().resolve()
        self.project_helix_dir = self.project_root / ".helix"
        self.registry_dir = self.project_helix_dir / "workspaces"
        self.template_path = Path(__file__).resolve().parents[1] / "templates" / "workspace" / "workspace.yaml"

    def workspaces_root(self) -> Path:
        """Return `~/.helix/workspaces/<repo_name>/`."""
        return self.home / ".helix" / "workspaces" / self.project_root.name

    def create(
        self,
        *,
        task_id: str,
        branch: str | None = None,
        base: str = "main",
    ) -> dict:
        """Create a workspace via git worktree + filtered init + snapshot."""
        task_id = task_id.strip()
        if not task_id:
            raise ValueError("task_id is required")

        if self._registry_entry_exists(task_id):
            raise WorkspaceExistsError(f"workspace already exists for task_id={task_id}")

        workspace_path = self.workspaces_root() / task_id
        if workspace_path.exists():
            raise WorkspaceExistsError(f"workspace path already exists: {workspace_path}")

        branch_name = branch or f"workspace/{task_id}"
        base_sha = self._git_stdout(["rev-parse", base], cwd=self.project_root)
        workspace_helix_dir = workspace_path / ".helix"
        snapshot_path = workspace_path / "workspace_state_snapshot.json"
        registry_snapshot_path = str(snapshot_path)
        reserved_resources = {"ports": [], "venv": "", "cache_prefix": ""}
        created_worktree = False

        try:
            workspace_path.parent.mkdir(parents=True, exist_ok=True)
            self._run_git(["worktree", "add", "-b", branch_name, str(workspace_path), base], cwd=self.project_root)
            created_worktree = True

            copy_stats = _filtered_copy(self.project_helix_dir, workspace_helix_dir)
            self._init_workspace_db(workspace_helix_dir / "helix.db")
            generate_snapshot(
                self.project_root,
                snapshot_path,
                task_id=task_id,
                base_sha=base_sha,
            )

            workspace_manifest = {
                "task_id": task_id,
                "workspace_path": str(workspace_path),
                "branch": branch_name,
                "base_sha": base_sha,
                "base_ref": base,
                "status": "active",
                "created_at": _now_iso8601(),
                "updated_at": _now_iso8601(),
                "snapshot_path": "workspace_state_snapshot.json",
                "reserved_resources": reserved_resources,
            }
            self._write_workspace_manifest(workspace_helix_dir / "workspace.yaml", workspace_manifest)
            self._write_registry_entry(
                {
                    **workspace_manifest,
                    "snapshot_path": registry_snapshot_path,
                    "copy_stats": copy_stats,
                }
            )
            self._registry_insert(
                task_id=task_id,
                workspace_path=str(workspace_path),
                branch=branch_name,
                base_sha=base_sha,
                base_ref=base,
                snapshot_path=registry_snapshot_path,
                reserved_resources=reserved_resources,
            )
        except Exception:
            if created_worktree:
                self._cleanup_failed_workspace(workspace_path)
            raise

        return {
            "task_id": task_id,
            "workspace_path": str(workspace_path),
            "branch": branch_name,
            "base_sha": base_sha,
            "snapshot_path": registry_snapshot_path,
        }

    def list_workspaces(self, status: str | None = None) -> list[dict]:
        """Return workspaces from the registry backend or fallback files."""
        registry_api = _registry_functions().get("workspace_registry_list")
        if callable(registry_api):
            with compatibility_adapter.write_connection(helix_db.resolve_default_db_path()) as conn:
                rows = registry_api(conn, status=status)
            return [dict(row) for row in rows]

        workspaces = [
            payload
            for payload in self._load_registry_entries()
            if status is None or payload.get("status") == status
        ]
        return sorted(workspaces, key=lambda item: (str(item.get("task_id", "")), str(item.get("workspace_path", ""))))

    def preflight(self, task_id: str) -> dict:
        """Check main dirty state, orphan worktree state, and branch divergence."""
        issues: list[dict[str, Any]] = []
        checked_at = _now_iso8601()
        if self._git_stdout(["status", "--porcelain"], cwd=self.project_root):
            issues.append(
                {
                    "kind": "main_dirty",
                    "severity": "warn",
                    "detail": f"main workspace has uncommitted changes: {self.project_root}",
                }
            )

        entry = self._get_workspace_entry(task_id)
        if entry is None:
            issues.append(
                {
                    "kind": "workspace_not_found",
                    "severity": "error",
                    "detail": f"workspace registry entry not found for task_id={task_id}",
                }
            )
            return {
                "task_id": task_id,
                "ok": False,
                "checked_at": checked_at,
                "issues": issues,
            }

        status = str(entry.get("status", "")).strip()
        if status != "active":
            issues.append(
                {
                    "kind": "status_not_active",
                    "severity": "error",
                    "detail": f"workspace status is {status or 'unknown'} for task_id={task_id}",
                }
            )

        workspace_path = Path(str(entry["workspace_path"]))
        if not workspace_path.exists():
            issues.append(
                {
                    "kind": "orphan_worktree",
                    "severity": "error",
                    "detail": f"workspace path is missing: {workspace_path}",
                }
            )
        else:
            worktree_paths = self._git_worktree_paths()
            if str(workspace_path.resolve()) not in worktree_paths:
                issues.append(
                    {
                        "kind": "orphan_worktree",
                        "severity": "error",
                        "detail": f"workspace path is not registered in git worktree list: {workspace_path}",
                    }
                )

        branch_name = str(entry.get("branch", "")).strip()
        base_ref = str(entry.get("base_ref", "main")).strip() or "main"
        if branch_name:
            try:
                counts = self._git_stdout(
                    ["rev-list", "--left-right", "--count", f"{base_ref}...{branch_name}"],
                    cwd=self.project_root,
                )
                behind, ahead = self._parse_rev_list_counts(counts)
                if ahead > 0 or behind > 0:
                    issues.append(
                        {
                            "kind": "branch_divergence",
                            "severity": "warn",
                            "detail": (
                                f"workspace branch {branch_name} diverged from {base_ref} "
                                f"(ahead={ahead}, behind={behind})"
                            ),
                        }
                    )
            except (GitWorktreeError, ValueError) as exc:
                issues.append(
                    {
                        "kind": "branch_divergence",
                        "severity": "warn",
                        "detail": f"unable to compare {branch_name} against {base_ref}: {exc}",
                    }
                )

        issues.extend(self._collect_stale_lock_issues())
        has_errors = any(issue.get("severity") == "error" for issue in issues)
        return {
            "task_id": task_id,
            "ok": not has_errors,
            "checked_at": checked_at,
            "issues": issues,
        }

    def exec_in_workspace(
        self,
        task_id: str,
        command: str,
        *,
        extra_env: dict[str, str] | None = None,
    ) -> int:
        """Run command inside workspace cwd. Returns exit code."""
        task_id = task_id.strip()
        command = command.strip()
        if not task_id:
            raise ValueError("task_id is required")
        if not command:
            raise ValueError("command is required")

        entry = self._get_workspace_entry(task_id)
        if entry is None:
            raise WorkspaceNotFoundError(f"workspace not found for task_id={task_id}")

        status = str(entry.get("status", "")).strip()
        if status != "active":
            raise ValueError(f"workspace status must be active for exec: {task_id} ({status or 'unknown'})")

        workspace_path = Path(str(entry["workspace_path"]))
        if not workspace_path.exists():
            raise WorkspaceNotFoundError(f"workspace path is missing: {workspace_path}")

        env = _inject_helix_workspace_env_vars(
            task_id,
            workspace_path,
            str(entry.get("branch", "")).strip(),
            extra_env=extra_env,
        )
        proc = subprocess.run(
            ["/bin/bash", "-c", command],
            cwd=workspace_path,
            env=env,
            check=False,
        )
        return int(proc.returncode)

    def drop(
        self,
        task_id: str,
        *,
        force: bool = False,
    ) -> dict:
        """Drop a workspace, aborting unless forced when changes remain."""
        entry = self._get_workspace_entry(task_id)
        if entry is None:
            raise WorkspaceNotFoundError(f"workspace not found for task_id={task_id}")

        workspace_path = Path(str(entry["workspace_path"]))
        if not workspace_path.exists():
            raise WorkspaceNotFoundError(f"workspace path is missing: {workspace_path}")

        base_ref = str(entry.get("base_ref", "main"))
        if self._workspace_has_unmerged_changes(workspace_path, base_ref=base_ref) and not force:
            raise WorkspaceDropAbortedError(
                f"workspace has unmerged changes: {workspace_path}"
            )

        trash_path = None
        if force:
            trash_path = self._archive_workspace(task_id, workspace_path)

        self._run_git(["worktree", "remove", "--force", str(workspace_path)], cwd=self.project_root)
        self._update_registry_status(task_id, status="dropped", drop_reason="force" if force else "clean")

        return {
            "task_id": task_id,
            "dropped": True,
            "trash_path": str(trash_path) if trash_path else None,
            "drop_reason": "force" if force else "clean",
        }

    def prune(self, *, dry_run: bool = False) -> list[str]:
        """Prune stale registry entries and git worktree metadata."""
        stale_entries: list[str] = []
        for entry in self._load_registry_entries():
            workspace_path = Path(str(entry.get("workspace_path", "")))
            if workspace_path and not workspace_path.exists():
                stale_entries.append(str(entry.get("task_id") or workspace_path))
                if not dry_run:
                    self._update_registry_status(str(entry.get("task_id")), status="dropped", drop_reason="pruned")

        if not dry_run:
            self._run_git(["worktree", "prune"], cwd=self.project_root)
        return stale_entries

    def _cleanup_failed_workspace(self, workspace_path: Path) -> None:
        with contextlib.suppress(Exception):
            self._run_git(["worktree", "remove", "--force", str(workspace_path)], cwd=self.project_root)
        with contextlib.suppress(Exception):
            if workspace_path.exists():
                shutil.rmtree(workspace_path)

    def _run_git(self, args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
            raise GitWorktreeError(f"git {' '.join(args)}: {detail}")
        return proc

    def _git_stdout(self, args: list[str], *, cwd: Path) -> str:
        return self._run_git(args, cwd=cwd).stdout.strip()

    def _git_worktree_paths(self) -> set[str]:
        output = self._git_stdout(["worktree", "list", "--porcelain"], cwd=self.project_root)
        paths: set[str] = set()
        for line in output.splitlines():
            if line.startswith("worktree "):
                paths.add(str(Path(line.split(" ", 1)[1]).resolve()))
        return paths

    def _parse_rev_list_counts(self, counts: str) -> tuple[int, int]:
        parts = counts.split()
        if len(parts) != 2:
            raise ValueError(f"invalid rev-list count payload: {counts!r}")
        return int(parts[0]), int(parts[1])

    def _collect_stale_lock_issues(self) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        lock_dir = self.project_helix_dir / "locks"
        if not lock_dir.exists():
            return issues

        for lock_path in sorted(lock_dir.glob("*")):
            if not lock_path.is_file():
                continue
            pid = self._extract_lock_pid(lock_path)
            if pid is None or self._pid_is_alive(pid):
                continue
            issues.append(
                {
                    "kind": "stale_lock",
                    "severity": "warn",
                    "detail": f"stale lock detected: {lock_path} (pid={pid})",
                }
            )
        return issues

    def _extract_lock_pid(self, lock_path: Path) -> int | None:
        try:
            raw = lock_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if not raw:
            return None

        digits = "".join(ch if ch.isdigit() else " " for ch in raw).split()
        if not digits:
            return None
        try:
            return int(digits[0])
        except ValueError:
            return None

    def _pid_is_alive(self, pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def _workspace_has_unmerged_changes(self, workspace_path: Path, *, base_ref: str) -> bool:
        if self._git_stdout(["status", "--porcelain"], cwd=workspace_path):
            return True
        try:
            counts = self._git_stdout(["rev-list", "--left-right", "--count", f"{base_ref}...HEAD"], cwd=workspace_path)
        except GitWorktreeError:
            return False
        parts = counts.split()
        if len(parts) != 2:
            return False
        ahead = int(parts[1])
        return ahead > 0

    def _archive_workspace(self, task_id: str, workspace_path: Path) -> Path:
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S")
        trash_path = self.home / ".helix" / "workspace-trash" / task_id / timestamp
        trash_path.mkdir(parents=True, exist_ok=True)

        bundle_path = trash_path / "changes.bundle"
        self._run_git(["bundle", "create", str(bundle_path), "--all"], cwd=workspace_path)

        tar_path = trash_path / "untracked.tar.gz"
        untracked_raw = self._git_stdout(["ls-files", "--others", "--exclude-standard"], cwd=workspace_path)
        untracked_files = [line for line in untracked_raw.splitlines() if line.strip()]
        with tarfile.open(tar_path, "w:gz") as archive:
            for rel_path in untracked_files:
                source = workspace_path / rel_path
                if source.exists():
                    archive.add(source, arcname=rel_path)
        return trash_path

    def _workspace_manifest_headers(self) -> list[str]:
        if not self.template_path.exists():
            return []
        return [line for line in self.template_path.read_text(encoding="utf-8").splitlines() if line.startswith("#")]

    def _write_workspace_manifest(self, path: Path, payload: dict[str, Any]) -> None:
        _write_yaml_file(path, payload, header_lines=self._workspace_manifest_headers())

    def _write_registry_entry(self, payload: dict[str, Any]) -> None:
        registry_path = self.registry_dir / f"{payload['task_id']}.yaml"
        _write_yaml_file(registry_path, payload)

    def _load_registry_entries(self) -> list[dict[str, Any]]:
        if not self.registry_dir.exists():
            return []
        entries: list[dict[str, Any]] = []
        for path in sorted(self.registry_dir.glob("*.yaml")):
            payload = _read_yaml_file(path)
            payload.setdefault("task_id", path.stem)
            entries.append(payload)
        return entries

    def _get_workspace_entry(self, task_id: str) -> dict[str, Any] | None:
        registry_api = _registry_functions().get("workspace_registry_get")
        if callable(registry_api):
            with compatibility_adapter.write_connection(helix_db.resolve_default_db_path()) as conn:
                row = registry_api(conn, task_id)
            if row is not None:
                payload = dict(row)
                registry_path = self.registry_dir / f"{task_id}.yaml"
                if registry_path.exists():
                    payload = {**_read_yaml_file(registry_path), **payload}
                return payload

        registry_path = self.registry_dir / f"{task_id}.yaml"
        if not registry_path.exists():
            return None
        return _read_yaml_file(registry_path)

    def _registry_entry_exists(self, task_id: str) -> bool:
        entry = self._get_workspace_entry(task_id)
        return bool(entry and entry.get("status") != "dropped")

    def _registry_insert(
        self,
        *,
        task_id: str,
        workspace_path: str,
        branch: str,
        base_sha: str,
        base_ref: str,
        snapshot_path: str,
        reserved_resources: dict[str, Any],
    ) -> None:
        registry_api = _registry_functions().get("workspace_registry_insert")
        if not callable(registry_api):
            return
        with compatibility_adapter.write_connection(helix_db.resolve_default_db_path()) as conn:
            registry_api(
                conn,
                task_id=task_id,
                workspace_path=workspace_path,
                branch=branch,
                base_sha=base_sha,
                base_ref=base_ref,
                snapshot_path=snapshot_path,
                reserved_resources=reserved_resources,
            )

    def _update_registry_status(self, task_id: str, *, status: str, drop_reason: str) -> None:
        registry_path = self.registry_dir / f"{task_id}.yaml"
        if registry_path.exists():
            payload = _read_yaml_file(registry_path)
            payload["status"] = status
            payload["updated_at"] = _now_iso8601()
            payload["drop_reason"] = drop_reason
            _write_yaml_file(registry_path, payload)

        registry_api = _registry_functions().get("workspace_registry_update_status")
        if not callable(registry_api):
            return
        with compatibility_adapter.write_connection(helix_db.resolve_default_db_path()) as conn:
            registry_api(conn, task_id, status=status, drop_reason=drop_reason)

    def _init_workspace_db(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            helix_db.init_db(str(db_path))
