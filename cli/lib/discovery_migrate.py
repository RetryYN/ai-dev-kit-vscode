from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import shutil
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

try:
    from . import discovery_compat
except ImportError:  # pragma: no cover
    import discovery_compat  # type: ignore[no-redef]


DEFAULT_LOCK_NAME = "discovery_migrate.lock"
VALID_MERGE_STRATEGIES = {"abort", "keep-dst", "keep-src"}
IGNORED_MANIFEST_FILES = {"README.deprecated", ".migration-manifest.json"}


class MigrationError(RuntimeError):
    def __init__(self, message: str, *, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class MigrationResult:
    status: str
    src: str
    dst: str
    file_count: int
    total_bytes: int
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _project_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return Path.cwd()


def _helix_dir() -> Path:
    return _project_root() / ".helix"


def default_src_dir() -> Path:
    return _helix_dir() / "scrum"


def default_dst_dir() -> Path:
    return _helix_dir() / "discovery"


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_hash(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _ensure_allowed_path(path: Path) -> Path:
    path = path.resolve(strict=False)
    root = _helix_dir().resolve(strict=False)
    allowed = {
        root / "scrum",
        root / "discovery",
        root / "discovery.tmp",
    }
    if not any(path == candidate or candidate in path.parents for candidate in allowed):
        raise MigrationError(
            f"path outside .helix/{{scrum,discovery}}: {path}",
            exit_code=2,
        )
    return path


def _iter_regular_files(base: Path) -> Iterator[Path]:
    for current in sorted(base.rglob("*")):
        stat = current.lstat()
        if current.is_symlink():
            raise MigrationError(f"symlink は移行対象外です: {current}", exit_code=2)
        if current.is_dir():
            continue
        if current.name in IGNORED_MANIFEST_FILES:
            continue
        if not current.is_file():
            raise MigrationError(f"特殊ファイルは移行対象外です: {current}", exit_code=2)
        yield current


def generate_manifest(base: Path) -> dict[str, object]:
    base = _ensure_allowed_path(base)
    if not base.exists():
        raise MigrationError(f"src が存在しません: {base}", exit_code=2)

    files = []
    total_bytes = 0
    for file_path in _iter_regular_files(base):
        rel = file_path.relative_to(base).as_posix()
        size = file_path.stat().st_size
        total_bytes += size
        files.append(
            {
                "path": rel,
                "size": size,
                "sha256": _sha256_path(file_path),
            }
        )
    manifest = {
        "files": files,
        "file_count": len(files),
        "total_bytes": total_bytes,
    }
    manifest["manifest_hash"] = _manifest_hash(manifest)
    return manifest


def verify_manifest(manifest: dict[str, object], dst: Path) -> None:
    expected_files = manifest["files"]
    if not isinstance(expected_files, list):
        raise MigrationError("manifest files 不正", exit_code=1)

    actual = generate_manifest(dst)
    actual_map = {entry["path"]: entry for entry in actual["files"]}  # type: ignore[index]
    if actual["file_count"] != manifest["file_count"]:
        raise MigrationError("コピー不完全: ファイル数不一致", exit_code=1)

    for entry in expected_files:
        if not isinstance(entry, dict):
            raise MigrationError("manifest entry 不正", exit_code=1)
        rel = entry["path"]
        actual_entry = actual_map.get(rel)
        if actual_entry is None:
            raise MigrationError(f"コピー不完全: 欠落 {rel}", exit_code=1)
        if actual_entry["size"] != entry["size"] or actual_entry["sha256"] != entry["sha256"]:
            raise MigrationError(f"コピー不完全: hash/size 不一致 [{rel}]", exit_code=1)


def _load_saved_manifest(dst: Path) -> dict[str, object] | None:
    path = dst / ".migration-manifest.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def status(src: Path, dst: Path) -> str:
    src = _ensure_allowed_path(src)
    dst = _ensure_allowed_path(dst)
    tmp_dir = dst.with_name(f"{dst.name}.tmp")
    if tmp_dir.exists():
        return "partial"
    if not src.exists() and not dst.exists():
        return "no_data"
    if not src.exists() and dst.exists():
        return "complete_or_clean"
    if src.exists() and not dst.exists():
        return "pending"
    saved_manifest = _load_saved_manifest(dst)
    if saved_manifest is None:
        return "conflict"
    try:
        src_manifest = generate_manifest(src)
    except MigrationError:
        return "conflict"
    if saved_manifest.get("manifest_hash") == src_manifest.get("manifest_hash"):
        return "complete"
    return "conflict"


def _dir_is_empty(dst: Path) -> bool:
    return not any(dst.iterdir())


def _dir_is_readme_only(dst: Path) -> bool:
    entries = [entry.name for entry in dst.iterdir()]
    return entries == ["README.deprecated"]


def check_conflict(src: Path, dst: Path) -> str:
    if not dst.exists():
        return "missing"
    if _dir_is_empty(dst):
        return "empty"
    if _dir_is_readme_only(dst):
        return "readme_only"
    saved_manifest = _load_saved_manifest(dst)
    if saved_manifest is not None:
        src_manifest = generate_manifest(src)
        if saved_manifest.get("manifest_hash") == src_manifest.get("manifest_hash"):
            return "manifest_match"
    return "conflict"


@contextmanager
def acquire_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(fd)
        raise MigrationError("別の migrate が実行中です", exit_code=1) from exc
    try:
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _cleanup_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)


def _overlay_tree(src: Path, dst: Path) -> None:
    for current in sorted(src.rglob("*")):
        rel = current.relative_to(src)
        target = dst / rel
        if current.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current, target)


def _write_legacy_readme(src: Path) -> None:
    src.mkdir(parents=True, exist_ok=True)
    src.joinpath("README.deprecated").write_text(
        (
            "このディレクトリは .helix/discovery/ へ移行されました。\n"
            f"migration: {datetime.now(timezone.utc).date().isoformat()}\n"
            "helix discovery コマンドを使用してください。\n"
        ),
        encoding="utf-8",
    )


def _write_saved_manifest(src: Path, dst: Path) -> dict[str, object]:
    payload = generate_manifest(dst)
    saved = {
        "src": str(src),
        "dst": str(dst),
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": payload["file_count"],
        "total_bytes": payload["total_bytes"],
        "manifest_hash": payload["manifest_hash"],
    }
    (dst / ".migration-manifest.json").write_text(
        json.dumps(saved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return saved


def migrate(
    *,
    src: Path,
    dst: Path,
    dry_run: bool = False,
    force: bool = False,
    merge_strategy: str = "abort",
    auto: bool = False,  # noqa: ARG001 - kept for CLI parity
    smoke_check: Callable[[Path], None] | None = None,
) -> MigrationResult:
    if merge_strategy not in VALID_MERGE_STRATEGIES:
        raise MigrationError(f"unsupported merge strategy: {merge_strategy}", exit_code=2)

    src = _ensure_allowed_path(src)
    dst = _ensure_allowed_path(dst)
    manifest = generate_manifest(src)
    message = f"migration {src} -> {dst}"
    if dry_run:
        return MigrationResult(
            status="dry_run",
            src=str(src),
            dst=str(dst),
            file_count=int(manifest["file_count"]),
            total_bytes=int(manifest["total_bytes"]),
            message=message,
        )

    tmp_dir = dst.with_name(f"{dst.name}.tmp")
    backup_dir = dst.with_name(f"{dst.name}.backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}")
    lock_path = _helix_dir() / DEFAULT_LOCK_NAME

    with acquire_lock(lock_path):
        if tmp_dir.exists():
            _cleanup_path(tmp_dir)

        conflict = check_conflict(src, dst)
        if conflict == "manifest_match" and not force:
            saved = _load_saved_manifest(dst) or {}
            return MigrationResult(
                status="skipped",
                src=str(src),
                dst=str(dst),
                file_count=int(saved.get("file_count", manifest["file_count"])),
                total_bytes=int(saved.get("total_bytes", manifest["total_bytes"])),
                message="already migrated",
            )
        if conflict == "conflict" and merge_strategy == "abort":
            raise MigrationError(
                ".helix/discovery/ が既に存在します。手動で --merge-strategy [keep-dst|keep-src|abort] を指定してください。",
                exit_code=2,
            )

        try:
            if conflict in {"missing", "empty", "readme_only", "manifest_match"} and not (
                conflict == "manifest_match" and force
            ):
                _copy_tree(src, tmp_dir)
                verify_manifest(manifest, tmp_dir)
                if dst.exists():
                    _cleanup_path(dst)
            else:
                if merge_strategy == "keep-dst":
                    _copy_tree(src, tmp_dir)
                    if dst.exists():
                        _overlay_tree(dst, tmp_dir)
                elif merge_strategy == "keep-src":
                    if dst.exists():
                        _copy_tree(dst, tmp_dir)
                        _overlay_tree(src, tmp_dir)
                    else:
                        _copy_tree(src, tmp_dir)
                else:
                    _copy_tree(src, tmp_dir)
                    verify_manifest(manifest, tmp_dir)
                    if dst.exists():
                        _cleanup_path(dst)

            if dst.exists():
                try:
                    os.rename(dst, backup_dir)
                except OSError as exc:
                    _cleanup_path(tmp_dir)
                    raise MigrationError(f"backup 作成失敗: {exc}", exit_code=1) from exc

            try:
                os.rename(tmp_dir, dst)
            except OSError as exc:
                if exc.errno == errno.EXDEV:
                    if backup_dir.exists():
                        os.rename(backup_dir, dst)
                    raise MigrationError(
                        "EXDEV: dst と src が異なる FS 上にあります。.helix/ を同一 FS 上に配置してください。",
                        exit_code=2,
                    ) from exc
                if backup_dir.exists():
                    os.rename(backup_dir, dst)
                raise

            if backup_dir.exists():
                _cleanup_path(backup_dir)

            _write_legacy_readme(src)
            saved_manifest = _write_saved_manifest(src, dst)
            if smoke_check is not None:
                smoke_check(dst)
            return MigrationResult(
                status="complete",
                src=str(src),
                dst=str(dst),
                file_count=int(saved_manifest["file_count"]),
                total_bytes=int(saved_manifest["total_bytes"]),
                message="migration completed",
            )
        except MigrationError:
            _cleanup_path(tmp_dir)
            raise
        except Exception as exc:  # pragma: no cover - defensive path
            _cleanup_path(tmp_dir)
            raise MigrationError(str(exc), exit_code=1) from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="discovery_migrate.py")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--merge-strategy", choices=sorted(VALID_MERGE_STRATEGIES), default="abort")
    parser.add_argument("--src", default=str(default_src_dir()))
    parser.add_argument("--dst", default=str(default_dst_dir()))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    src = Path(args.src)
    dst = Path(args.dst)
    try:
        if args.status:
            payload = {
                "status": status(src, dst),
                "src": str(src),
                "dst": str(dst),
            }
            print(json.dumps(payload, ensure_ascii=False))
            return 0

        result = migrate(
            src=src,
            dst=dst,
            dry_run=args.dry_run,
            force=args.force,
            merge_strategy=args.merge_strategy,
            auto=args.auto,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False))
        return 0
    except MigrationError as exc:
        print(str(exc), file=os.sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
