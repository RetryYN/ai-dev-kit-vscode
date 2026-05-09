#!/usr/bin/env python3
"""Atomic finalize helper for PLAN markdown frontmatter and YAML state."""

from __future__ import annotations

import argparse
import fcntl
import os
import shutil
import sys
from pathlib import Path

import yaml_parser


FAIL_STAGE_ENV = "HELIX_PLAN_FRONTMATTER_FAIL_STAGE"


class PlanFrontmatterError(RuntimeError):
    """Raised when PLAN finalize synchronization cannot complete safely."""


def _fail_if_requested(stage: str) -> None:
    if os.environ.get(FAIL_STAGE_ENV) == stage:
        raise OSError(f"forced failure at stage={stage}")


def _validate_iso_date(value: str) -> None:
    parts = value.split("-")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise PlanFrontmatterError(f"invalid ISO date: {value}")
    year, month, day = parts
    if len(year) != 4 or len(month) != 2 or len(day) != 2:
        raise PlanFrontmatterError(f"invalid ISO date: {value}")


def _lock_open(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = path.open("a+", encoding="utf-8")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def _lock_close(lock_fh) -> None:
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
    finally:
        lock_fh.close()


def _project_root_from_plan_file(plan_file: Path) -> Path:
    resolved = plan_file.resolve()
    if resolved.parent.name != "plans" or resolved.parent.parent.name != ".helix":
        raise PlanFrontmatterError(f"unexpected plan file path: {plan_file}")
    return resolved.parent.parent.parent


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise PlanFrontmatterError("PLAN markdown must start with YAML frontmatter")

    end = text.find("\n---\n", 4)
    if end < 0:
        raise PlanFrontmatterError("PLAN markdown frontmatter closing delimiter is missing")

    frontmatter_text = text[4:end]
    body = text[end + 5 :]
    data = yaml_parser.parse_yaml(frontmatter_text)
    if not isinstance(data, dict):
        raise PlanFrontmatterError("PLAN markdown frontmatter must be a mapping")
    return data, body


def _render_frontmatter(frontmatter: dict, body: str) -> str:
    return f"---\n{yaml_parser.dump_yaml(frontmatter)}\n---\n{body}"


def resolve_plan_doc_path(plan_file: Path, plan_data: dict) -> Path:
    project_root = _project_root_from_plan_file(plan_file)
    source_file = plan_data.get("source_file")
    if isinstance(source_file, str) and source_file and source_file != "null":
        candidate = Path(source_file)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        if candidate.is_file():
            return candidate

    plan_id = str(plan_data.get("id") or plan_file.stem)
    candidates = sorted((project_root / "docs" / "plans").glob(f"{plan_id}-*.md"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise PlanFrontmatterError(f"PLAN markdown not found for {plan_id}")
    raise PlanFrontmatterError(f"multiple PLAN markdown files found for {plan_id}")


def _write_temp_file(path: Path, content: str) -> Path:
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    tmp_path.write_text(content, encoding="utf-8")
    shutil.copymode(path, tmp_path)
    return tmp_path


def _cleanup_paths(*paths: Path) -> None:
    for path in paths:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def _apply_atomic_pair_update(
    docs_path: Path,
    docs_text: str,
    plan_path: Path,
    plan_text: str,
) -> None:
    lock_targets = sorted(
        [docs_path.with_suffix(docs_path.suffix + ".lock"), plan_path.with_suffix(plan_path.suffix + ".lock")],
        key=lambda item: str(item),
    )
    lock_handles = []
    for lock_path in lock_targets:
        lock_handles.append(_lock_open(lock_path))

    docs_backup = docs_path.with_name(f"{docs_path.name}.bak.{os.getpid()}")
    plan_backup = plan_path.with_name(f"{plan_path.name}.bak.{os.getpid()}")
    docs_tmp = docs_path.with_name(f"{docs_path.name}.tmp.{os.getpid()}")
    plan_tmp = plan_path.with_name(f"{plan_path.name}.tmp.{os.getpid()}")

    try:
        shutil.copy2(docs_path, docs_backup)
        shutil.copy2(plan_path, plan_backup)
        _fail_if_requested("after_backup")

        docs_tmp = _write_temp_file(docs_path, docs_text)
        _fail_if_requested("docs_tmp_write")
        plan_tmp = _write_temp_file(plan_path, plan_text)
        _fail_if_requested("plan_tmp_write")

        _fail_if_requested("docs_replace")
        os.replace(docs_tmp, docs_path)
        _fail_if_requested("after_docs_replace")
        _fail_if_requested("plan_replace")
        os.replace(plan_tmp, plan_path)
    except Exception as exc:  # pragma: no cover - exercised via tests
        restore_error = None
        try:
            if docs_backup.exists():
                os.replace(docs_backup, docs_path)
            if plan_backup.exists():
                os.replace(plan_backup, plan_path)
        except Exception as restore_exc:  # pragma: no cover - defensive path
            restore_error = restore_exc
        _cleanup_paths(docs_tmp, plan_tmp)
        if restore_error is not None:
            raise PlanFrontmatterError(
                f"finalize rollback failed: {exc}; restore_error={restore_error}"
            ) from exc
        raise PlanFrontmatterError(f"finalize rollback completed after error: {exc}") from exc
    else:
        _cleanup_paths(docs_backup, plan_backup)
    finally:
        _cleanup_paths(docs_tmp, plan_tmp)
        for lock_fh in reversed(lock_handles):
            _lock_close(lock_fh)


def finalize_plan_files(plan_file: str | Path, finalized_on: str) -> Path | None:
    _validate_iso_date(finalized_on)

    plan_path = Path(plan_file)
    plan_text = plan_path.read_text(encoding="utf-8")
    plan_data = yaml_parser.parse_yaml(plan_text)
    if not isinstance(plan_data, dict):
        raise PlanFrontmatterError("PLAN YAML must be a mapping")

    updated_plan = dict(plan_data)
    updated_plan["status"] = "finalized"
    updated_plan["finalized_at"] = finalized_on

    def _yaml_only_finalize() -> None:
        rendered_plan = yaml_parser._build_output_with_header(plan_text, updated_plan)
        tmp_path = _write_temp_file(plan_path, rendered_plan)
        try:
            os.replace(tmp_path, plan_path)
        except Exception:
            _cleanup_paths(tmp_path)
            raise

    try:
        docs_path = resolve_plan_doc_path(plan_path, plan_data)
    except PlanFrontmatterError as exc:
        if "PLAN markdown not found" in str(exc):
            _yaml_only_finalize()
            return None
        raise

    docs_text = docs_path.read_text(encoding="utf-8")
    try:
        frontmatter, body = _parse_frontmatter(docs_text)
    except PlanFrontmatterError as exc:
        if "must start with YAML frontmatter" in str(exc):
            _yaml_only_finalize()
            return None
        raise

    updated_frontmatter = dict(frontmatter)
    updated_frontmatter["status"] = "finalized"
    updated_frontmatter["finalized"] = finalized_on

    rendered_docs = _render_frontmatter(updated_frontmatter, body)
    rendered_plan = yaml_parser._build_output_with_header(plan_text, updated_plan)
    _apply_atomic_pair_update(docs_path, rendered_docs, plan_path, rendered_plan)
    return docs_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize PLAN markdown frontmatter and YAML state.")
    parser.add_argument("command", choices=["finalize"])
    parser.add_argument("plan_file")
    parser.add_argument("finalized_on")
    args = parser.parse_args()

    if args.command == "finalize":
        finalize_plan_files(args.plan_file, args.finalized_on)
        return 0
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PlanFrontmatterError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(1)
