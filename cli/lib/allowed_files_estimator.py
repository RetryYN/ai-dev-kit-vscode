from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import re


_PATH_LIKE_RE = re.compile(r"(?:--)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+|[A-Za-z0-9_.-]+\.[A-Za-z0-9]+")
_TOKEN_RE = re.compile(r"(?:--)?[A-Za-z][A-Za-z0-9_.-]{2,}")
_IGNORED_DIRS = {
    ".git",
    ".helix",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
}
_STOPWORDS = {
    "task",
    "tasks",
    "plan",
    "role",
    "work",
    "flag",
    "input",
    "output",
    "user",
    "users",
    "file",
    "files",
    "path",
    "paths",
    "with",
    "from",
    "into",
    "only",
    "mode",
    "must",
    "should",
    "simple",
    "using",
    "write",
    "read",
    "new",
    "add",
    "adds",
    "added",
    "update",
    "updated",
    "test",
    "tests",
    "pass",
    "runs",
    "workdir",
    "task_input",
    "allowed",
    "auto",
}


@dataclass(frozen=True)
class _Candidate:
    path: Path
    score: float
    matched_keywords: frozenset[str]


def _normalize_token(raw: str) -> str:
    token = raw.strip().strip("`'\"()[]{}<>,:;")
    token = token.rstrip(".")
    if token.startswith("--"):
        token = token[2:]
    return token.lstrip("./").lower()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def extract_keywords(task: str) -> list[str]:
    if not task.strip():
        return []

    exact_tokens: list[str] = []
    broad_tokens: list[str] = []

    for raw in _PATH_LIKE_RE.findall(task):
        token = _normalize_token(raw)
        if not token:
            continue
        exact_tokens.append(token)
        broad_tokens.append(Path(token).name.lower())
        stem = Path(token).stem.lower()
        if stem and stem != Path(token).name.lower():
            broad_tokens.append(stem)

    for raw in _TOKEN_RE.findall(task):
        token = _normalize_token(raw)
        if len(token) < 3 or token in _STOPWORDS:
            continue
        broad_tokens.append(token)
        for piece in re.split(r"[_-]+", token):
            if len(piece) >= 3 and piece not in _STOPWORDS:
                broad_tokens.append(piece)

    return _dedupe(exact_tokens + broad_tokens)


def _iter_repo_files(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            name
            for name in dirs
            if name not in _IGNORED_DIRS and not name.startswith(".")
        ]
        base = Path(root)
        for filename in files:
            if filename.startswith("."):
                continue
            paths.append((base / filename).relative_to(repo_root))
    return paths


def _score_path(path: Path, keywords: list[str]) -> _Candidate | None:
    path_str = path.as_posix().lower()
    basename = path.name.lower()
    stem = path.stem.lower()
    matched_scores: dict[str, float] = {}

    for keyword in keywords:
        score = 0.0
        if "/" in keyword:
            if path_str == keyword:
                score = 12.0
            elif path_str.endswith(f"/{keyword}") or keyword in path_str:
                score = 8.0
        elif "." in keyword and basename == keyword:
            score = 10.0
        elif basename == keyword:
            score = 9.0
        elif stem == keyword:
            score = 8.0
        elif keyword and basename.startswith(f"{keyword}."):
            score = 7.0
        elif keyword and (f"-{keyword}" in basename or f"_{keyword}" in basename):
            score = 6.0
        elif keyword and keyword in basename:
            score = 5.0
        elif keyword and keyword in path_str:
            score = 3.0

        if score > matched_scores.get(keyword, 0.0):
            matched_scores[keyword] = score

    if not matched_scores:
        return None
    return _Candidate(
        path=path,
        score=sum(matched_scores.values()),
        matched_keywords=frozenset(matched_scores),
    )


def _rank_candidates(keywords: list[str], repo_root: Path) -> list[_Candidate]:
    ranked: list[_Candidate] = []
    for path in _iter_repo_files(repo_root):
        candidate = _score_path(path, keywords)
        if candidate is not None:
            ranked.append(candidate)
    ranked.sort(key=lambda item: (-item.score, len(item.path.as_posix()), item.path.as_posix()))
    return ranked


def find_matching_files(keywords: list[str], repo_root: Path, limit: int = 8) -> list[Path]:
    if not keywords:
        return []

    ranked = _rank_candidates(keywords, repo_root)
    if not ranked:
        return []

    top_score = ranked[0].score
    cutoff = max(5.0, top_score * 0.6)
    return [candidate.path for candidate in ranked if candidate.score >= cutoff][:limit]


def compute_confidence(candidates: list[Path], keywords: list[str]) -> float:
    if not candidates or not keywords:
        return 0.0

    scored = [_score_path(path, keywords) for path in candidates]
    usable = [item for item in scored if item is not None]
    if not usable:
        return 0.0

    top_score = max(item.score for item in usable)
    total_score = sum(item.score for item in usable)
    matched_keywords = {
        keyword
        for item in usable
        for keyword in item.matched_keywords
    }
    has_specific_keyword = any("/" in keyword or "." in keyword for keyword in keywords)
    specificity = 1.0 if has_specific_keyword else min(
        1.0,
        sum(1 for keyword in keywords if len(keyword) >= 8) / max(1, len(keywords)),
    )
    score_norm = min(1.0, top_score / 24.0)
    coverage = len(matched_keywords) / max(1, min(len(set(keywords)), 8))
    concentration = top_score / total_score if total_score else 0.0

    confidence = (
        0.4 * score_norm
        + 0.25 * coverage
        + 0.15 * concentration
        + 0.2 * specificity
    )
    return round(min(1.0, confidence), 3)


def estimate_allowed_files(
    task: str,
    repo_root: Path,
    threshold: float = 0.5,
) -> tuple[list[Path], float, bool]:
    keywords = extract_keywords(task)
    candidates = find_matching_files(keywords, repo_root)
    confidence = compute_confidence(candidates, keywords)
    low_confidence = confidence < threshold or not candidates
    if low_confidence:
        return [], confidence, True
    return candidates, confidence, False
