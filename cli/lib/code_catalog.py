#!/usr/bin/env python3
"""HELIX code index catalog skeleton."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import helix_db
except ImportError:  # pragma: no cover - script execution fallback
    import helix_db


_INDEX_MARKER = "@helix:index"
_FIELD_RE = re.compile(r"(?<!\S)(id|domain|summary|since|related)=")
_TRACKED_SUFFIXES = {".py", ".sh", ".md", ".bats"}
_REJECTION_LOG = "code-catalog-rejected.log"

_DANGER_PATTERNS = [
    (re.compile(r"(auth|api|access|bearer|refresh)[-_. ]?(token|key|secret)", re.IGNORECASE), "danger_pattern"),
    (re.compile(r"password\b", re.IGNORECASE), "danger_pattern.password"),
    (re.compile(r"credential(s)?\b", re.IGNORECASE), "danger_pattern.credential"),
    (re.compile(r"client[-_ ]?secret", re.IGNORECASE), "danger_pattern.client_secret"),
]

_LONG_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+/=_-]{32,}")
_VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
_COMMIT_HASH_PATTERN = re.compile(r"^[0-9a-f]{7,12}$")

_SAFE_WORDS = {"tokenize", "token-based", "passwordless", "credentialing", "passwords-table-doc"}


def _strip_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        return text[1:-1]
    return text


def _parse_key_values(text: str) -> dict[str, str]:
    matches = list(_FIELD_RE.finditer(text))
    parsed: dict[str, str] = {}
    for idx, match in enumerate(matches):
        key = match.group(1)
        value_start = match.end()
        value_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        value = _strip_quotes(text[value_start:value_end].strip())
        if value:
            parsed[key] = value
    return parsed


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_marker_payload(line: str) -> dict[str, str] | None:
    if _INDEX_MARKER not in line:
        return None
    _, payload = line.split(_INDEX_MARKER, 1)
    return _parse_key_values(payload.strip())


def _project_root_for(path: Path) -> Path:
    current = path.resolve()
    for parent in (current, *current.parents):
        if (parent / ".helix").is_dir():
            return parent
    return Path.cwd()


def write_rejection_log(reject_dir: Path, path: str, line_no: int, pattern_name: str, reason: str) -> None:
    reject_dir.mkdir(parents=True, exist_ok=True)
    log_path = reject_dir / _REJECTION_LOG
    with log_path.open("a", encoding="utf-8", newline="\n") as fp:
        fp.write(f"{_now_iso()}\t{path}:{line_no}\t{pattern_name}\t{reason}\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def should_redact(summary: str) -> tuple[bool, str | None]:
    lowered = summary.lower()
    if lowered in _SAFE_WORDS:
        return False, None

    for pattern, reason in _DANGER_PATTERNS:
        if pattern.search(summary):
            return True, reason

    for token in _LONG_TOKEN_PATTERN.findall(summary):
        if _VERSION_PATTERN.fullmatch(token) or _COMMIT_HASH_PATTERN.fullmatch(token):
            continue
        return True, "secret_like_value"

    return False, None


def parse_helix_index_comment(line: str) -> dict[str, Any] | None:
    if _INDEX_MARKER not in line:
        return None

    fields = _parse_marker_payload(line) or {}
    if not {"id", "domain", "summary"} <= set(fields):
        return None

    should_skip, _ = should_redact(fields["summary"])
    if should_skip:
        return None

    related = []
    if fields.get("related"):
        related = [item.strip() for item in fields["related"].split(",") if item.strip()]

    return {
        "id": fields["id"],
        "domain": fields["domain"],
        "summary": fields["summary"],
        "since": fields.get("since"),
        "related": related,
    }


def scan_file(path: Path) -> list[dict[str, Any]]:
    source_hash = _source_hash(path)
    updated_at = _now_iso()
    entries: list[dict[str, Any]] = []
    reject_dir = _project_root_for(path) / ".helix" / "cache"

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        fields = _parse_marker_payload(line) if _INDEX_MARKER in line else None
        if fields is not None and fields.get("summary"):
            should_skip, reason = should_redact(fields["summary"])
            if should_skip:
                write_rejection_log(
                    reject_dir=reject_dir,
                    path=path.as_posix(),
                    line_no=line_no,
                    pattern_name=reason or "unknown",
                    reason="redaction rule matched",
                )
                continue
        parsed = parse_helix_index_comment(line)
        if parsed is None:
            continue
        parsed.update(
            {
                "path": path.as_posix(),
                "line_no": line_no,
                "source_hash": source_hash,
                "updated_at": updated_at,
            }
        )
        entries.append(parsed)

    return entries


def scan_tracked_files(repo_root: Path) -> list[dict[str, Any]]:
    root = repo_root.resolve()
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    entries: list[dict[str, Any]] = []
    for raw_path in result.stdout.splitlines():
        rel_path = Path(raw_path)
        if rel_path.suffix not in _TRACKED_SUFFIXES:
            continue
        full_path = root / rel_path
        if not full_path.is_file():
            continue
        for entry in scan_file(full_path):
            entry["path"] = rel_path.as_posix()
            entries.append(entry)

    return sorted(entries, key=lambda item: str(item.get("id", "")))


def write_jsonl(entries: list[dict], jsonl_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = jsonl_path.with_suffix(jsonl_path.suffix + ".tmp")
    prev_path = jsonl_path.with_suffix(jsonl_path.suffix + ".prev")

    with tmp_path.open("w", encoding="utf-8", newline="\n") as fp:
        for entry in sorted(entries, key=lambda item: str(item.get("id", ""))):
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")

    if jsonl_path.exists():
        shutil.copy2(jsonl_path, prev_path)
    os.replace(tmp_path, jsonl_path)


def sync_to_db(entries: list[dict], db_path: Path) -> None:
    helix_db._prepare_db_path(str(db_path))
    conn = helix_db._connect(str(db_path))
    helix_db._ensure_schema(conn)
    try:
        with conn:
            conn.execute("DELETE FROM code_index")
            conn.executemany(
                """
                INSERT OR REPLACE INTO code_index
                    (id, domain, summary, path, line_no, since, related, source_hash, updated_at)
                VALUES
                    (:id, :domain, :summary, :path, :line_no, :since, :related, :source_hash, :updated_at)
                """,
                [
                    {
                        "id": entry["id"],
                        "domain": entry["domain"],
                        "summary": entry["summary"],
                        "path": entry["path"],
                        "line_no": entry["line_no"],
                        "since": entry.get("since"),
                        "related": json.dumps(entry.get("related", []), ensure_ascii=False),
                        "source_hash": entry.get("source_hash"),
                        "updated_at": entry.get("updated_at"),
                    }
                    for entry in entries
                ],
            )
    finally:
        conn.close()


def rebuild_catalog(repo_root: Path, jsonl_path: Path, db_path: Path) -> dict[str, Any]:
    entries = scan_tracked_files(repo_root)
    write_jsonl(entries, jsonl_path)

    try:
        sync_to_db(entries, db_path)
    except Exception:
        prev_path = jsonl_path.with_suffix(jsonl_path.suffix + ".prev")
        if prev_path.exists():
            os.replace(prev_path, jsonl_path)
        raise

    return {
        "entry_count": len(entries),
        "jsonl_path": jsonl_path.as_posix(),
        "db_path": db_path.as_posix(),
        "updated_at": _now_iso(),
    }
