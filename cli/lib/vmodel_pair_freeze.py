from __future__ import annotations

from pathlib import Path
from typing import Any

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


def get_pair(layer: str) -> str | None:
    """L1-L14 のうち pair を返す。L0/L11/L13 は None。"""
    return VMODEL_PAIRS.get(layer)


def check_pair_freeze(layer: str, *, project_root: Path | None = None) -> dict[str, Any]:
    """Return V-model pair freeze status for one layer."""
    pair = get_pair(layer)
    if pair is None:
        return {
            "layer": layer,
            "pair": None,
            "pair_doc_exists": False,
            "pair_doc_path": None,
            "status": "no_pair",
            "hint": None,
        }

    root = Path(project_root) if project_root is not None else resolve_project_root()
    pair_dir = root / "docs" / "plans" / pair
    pattern = f"{pair}-*plan.md"
    matches = sorted(pair_dir.glob(pattern)) if pair_dir.is_dir() else []
    pair_doc = matches[0] if matches else None

    if pair_doc is not None:
        return {
            "layer": layer,
            "pair": pair,
            "pair_doc_exists": True,
            "pair_doc_path": str(pair_doc),
            "status": "ok",
            "hint": None,
        }

    return {
        "layer": layer,
        "pair": pair,
        "pair_doc_exists": False,
        "pair_doc_path": None,
        "status": "pair_missing",
        "hint": f"Create pair plan under docs/plans/{pair}/ matching {pattern}",
    }
