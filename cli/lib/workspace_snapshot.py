#!/usr/bin/env python3
"""HELIX workspace state snapshot generator (PLAN-156 / ADR-040 D3)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _now_iso8601() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def generate_snapshot(
    project_root: Path,
    target_path: Path,
    *,
    task_id: str,
    base_sha: str,
) -> dict:
    """Generate the minimal workspace snapshot payload and persist it."""
    _ = project_root
    payload = {
        "schema_version": 1,
        "task_id": task_id,
        "base_sha": base_sha,
        "generated_at": _now_iso8601(),
        "plan_registry": [],
        "handover_snapshot": {},
        "memory_links": [],
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload
