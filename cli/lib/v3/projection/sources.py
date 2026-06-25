from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass


class SourceEnumerationError(RuntimeError):
    """Raised when filesystem fallback appears to have narrowed the source set."""


@dataclass(frozen=True)
class SourceRecord:
    path: str
    text: str
    body: str
    frontmatter: dict[str, str]
    content_hash: str
    parse_error: str | None = None


def _is_source_candidate(path: str) -> bool:
    if "/.git/" in path or path.startswith(".git/"):
        return False
    if "/__pycache__/" in path or path.endswith("/__pycache__"):
        return False
    return path.endswith(".md")


def _walk_source_files(root: str) -> list[str]:
    results: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in {".git", "__pycache__", ".pytest_cache"}]
        for filename in filenames:
            candidate = os.path.join(dirpath, filename)
            relative = os.path.relpath(candidate, root).replace(os.sep, "/")
            if _is_source_candidate(relative):
                results.append(candidate)
    return sorted(results)


def _scan_source_files(root: str) -> list[str]:
    results: list[str] = []

    def _visit(directory: str) -> None:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.name in {".git", "__pycache__", ".pytest_cache"}:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    _visit(entry.path)
                    continue
                relative = os.path.relpath(entry.path, root).replace(os.sep, "/")
                if _is_source_candidate(relative):
                    results.append(entry.path)

    _visit(root)
    return sorted(results)


def _git_source_files(root: str) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    results: list[str] = []
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        normalized = candidate.replace(os.sep, "/")
        if not _is_source_candidate(normalized):
            continue
        absolute = os.path.join(root, candidate)
        if os.path.isfile(absolute):
            results.append(absolute)
    return sorted(set(results))


def enumerate_source_files(root: os.PathLike[str] | str) -> list[str]:
    root_path = os.fspath(root)
    try:
        return _git_source_files(root_path)
    except (OSError, subprocess.SubprocessError):
        walked = _walk_source_files(root_path)
        scanned = _scan_source_files(root_path)
        if set(walked) != set(scanned):
            raise SourceEnumerationError("filesystem fallback narrowed the source set")
        return walked


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter start")
    lines = text.splitlines()
    frontmatter: dict[str, str] = {}
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            end_index = index
            break
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()
    if end_index is None:
        raise ValueError("missing frontmatter end")
    body = "\n".join(lines[end_index + 1 :]).strip()
    return frontmatter, body


def load_sources(root: os.PathLike[str] | str) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    for path in enumerate_source_files(root):
        text = open(path, encoding="utf-8").read()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        relative = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            frontmatter, body = _parse_frontmatter(text)
            records.append(
                SourceRecord(
                    path=relative,
                    text=text,
                    body=body,
                    frontmatter=frontmatter,
                    content_hash=digest,
                )
            )
        except ValueError as exc:
            records.append(
                SourceRecord(
                    path=relative,
                    text=text,
                    body="",
                    frontmatter={},
                    content_hash=digest,
                    parse_error=str(exc),
                )
            )
    return records
