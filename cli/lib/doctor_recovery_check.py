"""契約: PLAN-098 §9.

recovery kind PLAN の freshness advisory を集計する helper。
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

try:
    from . import recovery_plan_check
except ImportError:  # pragma: no cover
    import recovery_plan_check


RECOVERY_PLAN_GLOB = "PLAN-*-recovery-*.md"


def _project_root() -> Path:
    configured = os.environ.get("HELIX_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.cwd().resolve()


def _docs_plans_dir() -> Path:
    return _project_root() / "docs" / "plans"


def _resolve_revised_at(plan_path: Path) -> date:
    frontmatter = recovery_plan_check._load_frontmatter(plan_path)
    revised_date = recovery_plan_check._extract_revised_date(frontmatter)
    if revised_date is not None:
        return revised_date
    return datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC).date()


def _plan_age_days(plan_path: Path) -> int:
    today = datetime.now(UTC).date()
    return (today - _resolve_revised_at(plan_path)).days


def _plan_id(frontmatter: dict[str, Any], plan_path: Path) -> str:
    plan_id = str(frontmatter.get("plan_id") or "").strip()
    if plan_id:
        return plan_id
    stem = plan_path.stem
    prefix, _sep, _rest = stem.partition("-recovery-")
    return prefix or stem


def run_check_recovery_freshness(max_age_days: int = 30) -> list[dict[str, Any]]:
    """recovery PLAN の freshness advisory rows を返す。"""
    docs_dir = _docs_plans_dir()
    if not docs_dir.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    for plan_path in sorted(docs_dir.glob(RECOVERY_PLAN_GLOB)):
        frontmatter = recovery_plan_check._load_frontmatter(plan_path)
        if str(frontmatter.get("kind") or "").strip() != "recovery":
            continue

        age_days = _plan_age_days(plan_path)
        is_fresh = recovery_plan_check.check_recovery_plan_freshness(
            plan_path,
            max_age_days=max_age_days,
        )
        rows.append(
            {
                "plan_id": _plan_id(frontmatter, plan_path),
                "path": str(plan_path.relative_to(_project_root())),
                "kind": "recovery",
                "doc_status": str(frontmatter.get("status") or ""),
                "last_updated": _resolve_revised_at(plan_path).isoformat(),
                "age_days": age_days,
                "status": "ok" if is_fresh else "warning",
                "reason": "ok" if is_fresh else "stale_recovery_plan",
                "max_age_days": max_age_days,
            }
        )
    return rows
