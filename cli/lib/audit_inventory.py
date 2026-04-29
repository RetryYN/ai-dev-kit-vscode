"""Generate A0 decisions.yaml drafts from inventory discovery output."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

import audit_hash


SUMMARY_LINE_RE = re.compile(r"^([a-z_]+):\s+(.+)$")


def parse_inventory_summary(summary_path: Path) -> dict[str, str]:
    """Parse key/value lines from an inventory-summary log."""
    text = summary_path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for line in text.splitlines():
        match = SUMMARY_LINE_RE.match(line)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def parse_inventory_raw(raw_path: Path) -> list[str]:
    """Extract tracked file paths from an inventory-run raw log."""
    if not raw_path.exists():
        return []
    text = raw_path.read_text(encoding="utf-8")
    files: list[str] = []
    in_tracked_section = False
    for line in text.splitlines():
        if line.startswith("## tracked files"):
            in_tracked_section = True
            continue
        if line.startswith("## ") and in_tracked_section:
            in_tracked_section = False
        if in_tracked_section and line.strip() and not line.startswith("#"):
            files.append(line.strip())
    return files


def generate_decisions_draft(
    summary_path: Path,
    raw_path: Path,
    scope_hash: str,
    schema_version: int = 1,
) -> dict[str, Any]:
    """Generate the decisions.yaml draft structure from A0 inventory output."""
    parse_inventory_summary(summary_path)
    files = parse_inventory_raw(raw_path)

    decisions = []
    for file_path in files:
        decisions.append(
            {
                "candidate_id": file_path,
                "schema_version": schema_version,
                "scope_hash": scope_hash,
                "decision": "keep",
                "rationale": "A0 default; PM review pending",
                "evidence": {
                    "source": file_path,
                    "hash": "",
                    "redacted": True,
                },
                "fail_safe_action": "manual_review",
            }
        )

    return {
        "version": 1,
        "metadata": {
            "scope_hash": scope_hash,
            "source_hash": "",
            "schema_version": schema_version,
        },
        "decisions": decisions,
    }


def dump_decisions_yaml(data: dict[str, Any]) -> str:
    """Dump decisions.yaml with a valid source_hash metadata field."""
    draft = dict(data)
    metadata = dict(draft.get("metadata", {}))
    metadata["source_hash"] = "0" * 64
    draft["metadata"] = metadata

    first_pass = yaml.safe_dump(
        draft,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    metadata["source_hash"] = audit_hash.compute_source_hash(first_pass)
    return yaml.safe_dump(
        draft,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
