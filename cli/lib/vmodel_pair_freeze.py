from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .paths import project_root as resolve_project_root


VMODEL_PAIRS = {
    "L1": "L14",
    "L2": "L10",
    "L3": "L12",
    "L4": "L9",
    "L5": "L8",
    "L6": "L7",
    "L7": "L6",
    "L8": "L5",
    "L9": "L4",
    "L10": "L2",
    "L12": "L3",
    "L14": "L1",
}

CRITICAL_LAYERS = {"L1", "L3", "L4", "L6"}
WARNING_LAYERS = {"L2", "L5"}
INFO_LAYERS = {"L7", "L8", "L9", "L10", "L12", "L14"}
STATUS_BREAKDOWN_KEYS = ("draft", "in_progress", "completed", "superseded", "other")


def get_pair(layer: str) -> str | None:
    """L1-L14 のうち pair を返す。L0/L11/L13 は None。"""
    return VMODEL_PAIRS.get(layer)


def get_severity(layer: str) -> str | None:
    """Return configured severity for a paired layer."""
    if layer in CRITICAL_LAYERS:
        return "critical"
    if layer in WARNING_LAYERS:
        return "warning"
    if layer in INFO_LAYERS:
        return "info"
    return None


def _load_plan_status(plan_path: Path) -> str | None:
    """Return plan status from YAML frontmatter when present."""
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    if not lines or lines[0].strip() != "---":
        return None

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return None

    try:
        loaded = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError:
        return None

    if not isinstance(loaded, dict):
        return None
    status = loaded.get("status")
    return status if isinstance(status, str) else None


def _filter_active_plans(plan_paths: list[Path]) -> list[Path]:
    active_statuses = {"draft", "in_progress"}
    return [plan_path for plan_path in plan_paths if _load_plan_status(plan_path) in active_statuses]


def _empty_status_breakdown() -> dict[str, int]:
    return {key: 0 for key in STATUS_BREAKDOWN_KEYS}


def _normalize_plan_status(status: str | None) -> str:
    if status in STATUS_BREAKDOWN_KEYS[:-1]:
        return status
    return "other"


def _build_status_breakdown(plan_paths: list[Path]) -> dict[str, int]:
    breakdown = _empty_status_breakdown()
    for plan_path in plan_paths:
        breakdown[_normalize_plan_status(_load_plan_status(plan_path))] += 1
    return breakdown


def check_pair_freeze(
    layer: str,
    *,
    project_root: Path | None = None,
    active_only: bool = False,
) -> dict[str, Any]:
    """Return V-model pair freeze status for one layer."""
    pair = get_pair(layer)
    severity = get_severity(layer)
    if pair is None:
        return {
            "layer": layer,
            "pair": None,
            "severity": severity,
            "active_only": active_only,
            "status_breakdown": {},
            "pair_doc_exists": False,
            "pair_doc_path": None,
            "status": "no_pair",
            "hint": None,
        }

    root = Path(project_root) if project_root is not None else resolve_project_root()
    pair_dir = root / "docs" / "plans" / pair
    pattern = f"{pair}-*plan.md"
    matches = sorted(pair_dir.glob(pattern)) if pair_dir.is_dir() else []
    if active_only:
        matches = _filter_active_plans(matches)
    status_breakdown = _build_status_breakdown(matches)
    pair_doc = matches[0] if matches else None

    if pair_doc is not None:
        return {
            "layer": layer,
            "pair": pair,
            "severity": severity,
            "active_only": active_only,
            "status_breakdown": status_breakdown,
            "pair_doc_exists": True,
            "pair_doc_path": str(pair_doc),
            "status": "ok",
            "hint": None,
        }

    return {
        "layer": layer,
        "pair": pair,
        "severity": severity,
        "active_only": active_only,
        "status_breakdown": status_breakdown,
        "pair_doc_exists": False,
        "pair_doc_path": None,
        "status": "pair_missing",
        "hint": f"Create pair plan under docs/plans/{pair}/ matching {pattern}",
    }
