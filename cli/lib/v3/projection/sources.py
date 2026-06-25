from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass

import yaml


class SourceEnumerationError(RuntimeError):
    """Raised when filesystem fallback appears to have narrowed the source set."""


@dataclass(frozen=True)
class SourceRecord:
    path: str
    text: str
    body: str
    frontmatter: dict[str, object]
    content_hash: str
    parse_error: str | None = None


def _is_source_candidate(path: str) -> bool:
    if "/.git/" in path or path.startswith(".git/"):
        return False
    if "/__pycache__/" in path or path.endswith("/__pycache__"):
        return False
    # .md = doc/PLAN (frontmatter parsed); .py/.bats = code/test; .yaml = config/registry (FR 等)
    # 非 .md は frontmatter parse せず text+hash のみ(load_sources)
    return path.endswith((".md", ".py", ".bats", ".yaml"))


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


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    start_index = 0
    while start_index < len(lines) and not lines[start_index].strip():
        start_index += 1
    if start_index >= len(lines) or lines[start_index].strip() != "---":
        return {}, normalized.strip()

    end_index = None
    for index in range(start_index + 1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, normalized.strip()

    frontmatter_block = "\n".join(lines[start_index + 1 : end_index]).strip()
    try:
        loaded = yaml.safe_load(frontmatter_block) if frontmatter_block else {}
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise ValueError("frontmatter must be a mapping")
    body = "\n".join(lines[end_index + 1 :]).strip()
    return loaded, body


def load_sources(root: os.PathLike[str] | str) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    for path in enumerate_source_files(root):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        relative = os.path.relpath(path, root).replace(os.sep, "/")
        # frontmatter parse は .md のみ(.py/.bats/.yaml は text-only、YAML doc marker '---' の誤 parse を回避)
        if not relative.endswith(".md"):
            records.append(
                SourceRecord(path=relative, text=text, body=text, frontmatter={}, content_hash=digest)
            )
            continue
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
