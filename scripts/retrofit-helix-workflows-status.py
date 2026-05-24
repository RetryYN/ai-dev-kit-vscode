#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import os
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml


TARGET_DATE = "2026-05-24"
FREEZE_BASIS = "content_frozen_2026-05-24"
MODE_WORKFLOW_FILES = {
    "add-feature-workflow.md",
    "discovery-workflow.md",
    "incident-workflow.md",
    "recovery-workflow.md",
    "refactor-workflow.md",
    "research-workflow.md",
    "retrofit-workflow.md",
    "reverse-workflow.md",
    "scrum-workflow.md",
}
SPECIALIZED_WORKFLOW_FILES = {
    "frontend-design-workflow.md",
    "screen-design-workflow.md",
}


@dataclass
class Summary:
    changed: int = 0
    skipped: int = 0
    errors: int = 0
    status_missing: int = 0
    accepted_date_conflict: int = 0
    double_check_failed: int = 0


@dataclass
class FileResult:
    path: str
    category: str
    freeze_basis: str = FREEZE_BASIS
    exclude_reason: str = "-"
    action: str = "unchanged"
    diff: str = ""
    original_text: str = ""
    updated_text: str = ""
    error: str = ""


@dataclass
class ExecutionResult:
    root: Path
    apply: bool
    force_date: bool
    files: list[FileResult] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)
    ok: bool = True


def collect_target_paths(base_dir: Path) -> list[Path]:
    return sorted(path for path in base_dir.glob("*.md") if path.is_file())


def extract_frontmatter_lines(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter_missing")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], lines[index + 1 :]
    raise ValueError("frontmatter_closing_delimiter_missing")


def classify_path(path: Path) -> str:
    stem = path.stem
    if stem.startswith("L") and "-" in stem and stem[1:2].isdigit():
        return f"{stem.split('-', 1)[0]} 工程 doc"
    if path.name in MODE_WORKFLOW_FILES:
        return "9 mode workflow doc"
    if path.name in SPECIALIZED_WORKFLOW_FILES:
        return "工程専門 doc"
    return "管理・自動化基盤 doc"


def normalize_scalar(value: object) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value).strip()


def split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def detect_newline(lines: list[str]) -> str:
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
        if line.endswith("\n"):
            return "\n"
    return "\n"


def render_diff(path: str, before: str, after: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=path,
        tofile=path,
        n=0,
    )
    return "".join(diff_lines)


def update_frontmatter_text(
    frontmatter_lines: list[str],
    *,
    force_date: bool,
) -> tuple[list[str], str | None]:
    status_index: int | None = None
    accepted_date_index: int | None = None

    for index, line in enumerate(frontmatter_lines):
        raw_line, _newline = split_line_ending(line)
        if raw_line.startswith("status:"):
            status_index = index
        elif raw_line.startswith("accepted_date:"):
            accepted_date_index = index

    if status_index is None:
        return frontmatter_lines, "status_missing"

    status_line, status_newline = split_line_ending(frontmatter_lines[status_index])
    if status_line != "status: draft":
        return frontmatter_lines, "unexpected_status_line"

    updated_lines = list(frontmatter_lines)
    updated_lines[status_index] = f"status: accepted{status_newline}"

    if accepted_date_index is None:
        accepted_date_line = f"accepted_date: {TARGET_DATE}{status_newline or detect_newline(frontmatter_lines)}"
        updated_lines.insert(status_index + 1, accepted_date_line)
        return updated_lines, None

    accepted_line, accepted_newline = split_line_ending(updated_lines[accepted_date_index])
    existing_value = accepted_line.split(":", 1)[1].strip()
    if existing_value != TARGET_DATE and not force_date:
        return frontmatter_lines, "accepted_date_conflict"
    updated_lines[accepted_date_index] = f"accepted_date: {TARGET_DATE}{accepted_newline}"
    return updated_lines, None


def validate_frontmatter(text: str) -> dict[str, object]:
    frontmatter_lines, _body_lines = extract_frontmatter_lines(text)
    loaded = yaml.safe_load("".join(frontmatter_lines)) or {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter_must_be_mapping")
    return loaded


def read_text_preserve_newlines(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def process_file(path: Path, *, root: Path, force_date: bool) -> FileResult:
    relative_path = str(path.relative_to(root))
    result = FileResult(path=relative_path, category=classify_path(path))

    try:
        text = read_text_preserve_newlines(path)
        frontmatter_lines, body_lines = extract_frontmatter_lines(text)
        loaded = yaml.safe_load("".join(frontmatter_lines)) or {}
        if not isinstance(loaded, dict):
            result.action = "error"
            result.error = "frontmatter_must_be_mapping"
            result.exclude_reason = "frontmatter_must_be_mapping"
            return result
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result.action = "error"
        result.error = str(exc)
        result.exclude_reason = "read_or_parse_error"
        return result

    status_value = normalize_scalar(loaded.get("status", ""))
    if not status_value:
        result.action = "status_missing"
        result.exclude_reason = "status_missing"
        return result
    if status_value == "accepted":
        result.action = "skip"
        result.exclude_reason = "already_accepted"
        return result
    if status_value != "draft":
        result.action = "error"
        result.error = f"unexpected_status:{status_value}"
        result.exclude_reason = f"unexpected_status:{status_value}"
        return result

    updated_frontmatter_lines, update_error = update_frontmatter_text(
        frontmatter_lines,
        force_date=force_date,
    )
    if update_error == "status_missing":
        result.action = "status_missing"
        result.exclude_reason = "status_missing"
        return result
    if update_error == "accepted_date_conflict":
        result.action = "accepted_date_conflict"
        result.exclude_reason = "accepted_date_conflict"
        return result
    if update_error is not None:
        result.action = "error"
        result.error = update_error
        result.exclude_reason = update_error
        return result

    updated_text = "---" + detect_newline(frontmatter_lines)
    updated_text += "".join(updated_frontmatter_lines)
    updated_text += f"---{detect_newline(frontmatter_lines)}"
    updated_text += "".join(body_lines)

    try:
        updated_loaded = validate_frontmatter(updated_text)
    except (ValueError, yaml.YAMLError) as exc:
        result.action = "error"
        result.error = f"validation_failed:{exc}"
        result.exclude_reason = "validation_failed"
        return result

    if normalize_scalar(updated_loaded.get("status", "")) != "accepted":
        result.action = "error"
        result.error = "validation_failed:status_not_accepted"
        result.exclude_reason = "validation_failed"
        return result
    if normalize_scalar(updated_loaded.get("accepted_date", "")) != TARGET_DATE:
        result.action = "error"
        result.error = "validation_failed:accepted_date_mismatch"
        result.exclude_reason = "validation_failed"
        return result

    result.action = "change"
    result.original_text = text
    result.updated_text = updated_text
    result.diff = render_diff(relative_path, text, updated_text)
    return result


def write_changes(changed_files: list[FileResult]) -> None:
    tmp_paths: list[Path] = []
    try:
        for file_result in changed_files:
            path = Path(file_result.path)
            absolute_path = file_result.root / path  # type: ignore[attr-defined]
            tmp_path = absolute_path.parent / f".{absolute_path.name}.tmp.{os.getpid()}"
            with tmp_path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(file_result.updated_text)
            tmp_paths.append(tmp_path)
        for file_result in changed_files:
            path = Path(file_result.path)
            absolute_path = file_result.root / path  # type: ignore[attr-defined]
            tmp_path = absolute_path.parent / f".{absolute_path.name}.tmp.{os.getpid()}"
            os.replace(tmp_path, absolute_path)
    finally:
        for tmp_path in tmp_paths:
            if tmp_path.exists():
                tmp_path.unlink()


def double_check_files(root: Path, paths: list[Path]) -> int:
    failures = 0
    for path in paths:
        try:
            validate_frontmatter(read_text_preserve_newlines(path))
        except (OSError, ValueError, yaml.YAMLError):
            failures += 1
    return failures


def execute(
    *,
    root: Path,
    apply: bool,
    force_date: bool,
    verbose: bool,
) -> ExecutionResult:
    base_dir = root / "HELIX-workflows" / "helix-process"
    result = ExecutionResult(root=root, apply=apply, force_date=force_date)

    for path in collect_target_paths(base_dir):
        file_result = process_file(path, root=root, force_date=force_date)
        setattr(file_result, "root", root)
        result.files.append(file_result)
        if file_result.action == "change":
            result.summary.changed += 1
        elif file_result.action == "skip":
            result.summary.skipped += 1
        elif file_result.action == "status_missing":
            result.summary.status_missing += 1
            result.ok = False
        elif file_result.action == "accepted_date_conflict":
            result.summary.accepted_date_conflict += 1
            result.ok = False
        elif file_result.action == "error":
            result.summary.errors += 1
            result.ok = False

    changed_files = [item for item in result.files if item.action == "change"]
    if apply and result.ok and changed_files:
        try:
            write_changes(changed_files)
        except OSError as exc:
            result.summary.errors += 1
            result.ok = False
            changed_files[0].error = str(exc)
            changed_files[0].exclude_reason = "write_failed"
        else:
            double_check_failures = double_check_files(
                root,
                [root / item.path for item in changed_files],
            )
            result.summary.double_check_failed = double_check_failures
            if double_check_failures:
                result.ok = False

    if verbose:
        for item in result.files:
            print(f"[{item.action}] {item.path} ({item.exclude_reason})", file=sys.stderr)

    return result


def render_result(result: ExecutionResult) -> str:
    lines: list[str] = []
    if not result.apply:
        lines.append("=== DRY-RUN MODE (pass --apply to apply) ===")
        lines.append("")
    for item in result.files:
        if item.diff:
            lines.append(item.diff.rstrip("\n"))
            lines.append("")
    lines.append("[REPORT] file × category × freeze_basis × exclude_reason:")
    for item in result.files:
        lines.append(
            f"  {item.path:<55} | {item.category:<20} | {item.freeze_basis} | {item.exclude_reason}"
        )
    lines.append("")
    lines.append("Summary:")
    lines.append(f"  changed: {result.summary.changed}")
    lines.append(f"  skipped: {result.summary.skipped}")
    lines.append(f"  errors: {result.summary.errors}")
    lines.append(f"  status_missing: {result.summary.status_missing}")
    lines.append(
        f"  accepted_date_conflict: {result.summary.accepted_date_conflict}"
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrofit HELIX workflow frontmatter status from draft to accepted."
    )
    parser.add_argument("--apply", action="store_true", help="更新を実ファイルへ反映する")
    parser.add_argument(
        "--force-date",
        action="store_true",
        help="accepted_date が TARGET_DATE と異なる場合も上書きする",
    )
    parser.add_argument("--verbose", action="store_true", help="処理詳細を stderr に出力する")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    result = execute(
        root=repo_root,
        apply=args.apply,
        force_date=args.force_date,
        verbose=args.verbose,
    )
    sys.stdout.write(render_result(result))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
