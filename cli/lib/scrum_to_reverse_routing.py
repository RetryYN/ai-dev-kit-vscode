"""契約: PLAN-095 §8 §9

Scrum hypothesis から Reverse type の Primary routing を決定する。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

try:
    from . import scrum_reverse_matrix, yaml_parser
except ImportError:  # pragma: no cover
    import scrum_reverse_matrix  # type: ignore[no-redef]
    import yaml_parser  # type: ignore[no-redef]


DEFAULT_SCRUM_TYPE = "hypothesis-test"


def _default_backlog_path() -> Path:
    return Path(__file__).resolve().parents[2] / ".helix" / "scrum" / "backlog.yaml"


def _load_backlog(path: Path) -> dict:
    if not path.exists():
        return {}
    parsed = yaml_parser.parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"invalid scrum backlog: {path}")
    return parsed


def _resolve_scrum_type(scrum_hypothesis_id: str) -> str:
    hypothesis_id = str(scrum_hypothesis_id).strip()
    if not hypothesis_id:
        raise ValueError("scrum_hypothesis_id must be non-empty")

    backlog_path = Path(os.environ.get("HELIX_SCRUM_BACKLOG") or _default_backlog_path())
    backlog = _load_backlog(backlog_path)
    hypotheses = backlog.get("hypotheses")
    if not isinstance(hypotheses, dict):
        return DEFAULT_SCRUM_TYPE
    if hypothesis_id not in hypotheses:
        raise ValueError(f"unknown scrum hypothesis: {hypothesis_id}")
    hypothesis = hypotheses[hypothesis_id]
    if not isinstance(hypothesis, dict):
        return DEFAULT_SCRUM_TYPE
    scrum_type = str(hypothesis.get("scrum_type") or DEFAULT_SCRUM_TYPE).strip()
    if scrum_type not in scrum_reverse_matrix.SCRUM_TYPES:
        raise ValueError(f"unknown scrum_type: {scrum_type}")
    return scrum_type


def route_scrum_to_reverse(scrum_hypothesis_id: str) -> tuple[str, str]:
    scrum_type = _resolve_scrum_type(scrum_hypothesis_id)
    for reverse_type in scrum_reverse_matrix.REVERSE_TYPES:
        cell = scrum_reverse_matrix.lookup_matrix(scrum_type, reverse_type)
        if cell["rating"] == "Primary":
            return reverse_type, cell["rating"]
    raise ValueError(f"primary reverse route not found for scrum_type: {scrum_type}")
