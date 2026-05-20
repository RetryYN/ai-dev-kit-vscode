"""契約: PLAN-095 §5 §6 §7

Scrum × Reverse 30 cell matrix lookup helpers.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

SCRUM_TYPES: Final = ("hypothesis-test", "tech-spike", "design-spike", "perf-spike", "security-spike", "ux-spike")
REVERSE_TYPES: Final = ("code", "design", "upgrade", "normalization", "fullback")
RATINGS: Final = ("Primary", "Alternative", "N/A")
PRIMARY_BY_SCRUM: Final = {
    "hypothesis-test": "code",
    "tech-spike": "design",
    "design-spike": "design",
    "perf-spike": "upgrade",
    "security-spike": "normalization",
    "ux-spike": "design",
}
ALTERNATIVES_BY_SCRUM: Final = {
    "hypothesis-test": frozenset({"design", "fullback"}),
    "tech-spike": frozenset({"code", "upgrade"}),
    "design-spike": frozenset({"normalization", "fullback"}),
    "perf-spike": frozenset({"normalization", "fullback"}),
    "security-spike": frozenset({"code", "design"}),
    "ux-spike": frozenset({"normalization", "fullback"}),
}
STEP_BY_REVERSE: Final = {"code": "R1", "design": "R2", "upgrade": "R1", "normalization": "R1", "fullback": "R0"}
PRIMARY_STEP_BY_SCRUM: Final = {
    "hypothesis-test": "R1",
    "tech-spike": "R2",
    "design-spike": "R2",
    "perf-spike": "R1",
    "security-spike": "R1",
    "ux-spike": "R2",
}


def _rating(scrum_type: str, reverse_type: str) -> str:
    if reverse_type == PRIMARY_BY_SCRUM[scrum_type]:
        return "Primary"
    if reverse_type in ALTERNATIVES_BY_SCRUM[scrum_type]:
        return "Alternative"
    return "N/A"


def _rationale(scrum_type: str, reverse_type: str, rating: str) -> str:
    if rating == "N/A":
        return f"{scrum_type} では {reverse_type} を通常選択しない。"
    phase = STEP_BY_REVERSE[reverse_type]
    prefix = "既定ルート。" if rating == "Primary" else "代替ルート。"
    return f"{prefix}{reverse_type} の復元を優先し、{phase} から Reverse 合流する。"


MATRIX: Final = MappingProxyType(
    {
        scrum_type: MappingProxyType(
            {
                reverse_type: MappingProxyType(
                    {
                        "rating": rating,
                        "recommended_step": "manual-review" if rating == "N/A" else STEP_BY_REVERSE[reverse_type],
                        "rationale": _rationale(scrum_type, reverse_type, rating),
                    }
                )
                for reverse_type in REVERSE_TYPES
                for rating in (_rating(scrum_type, reverse_type),)
            }
        )
        for scrum_type in SCRUM_TYPES
    }
)


def lookup_matrix(scrum_type: str, reverse_type: str) -> dict[str, str]:
    if scrum_type not in MATRIX:
        raise ValueError(f"unknown scrum_type: {scrum_type}")
    if reverse_type not in MATRIX[scrum_type]:
        raise ValueError(f"unknown reverse_type: {reverse_type}")
    return dict(MATRIX[scrum_type][reverse_type])


def validate_matrix() -> dict[str, int]:
    cell_count = 0
    for scrum_type in SCRUM_TYPES:
        primary_count = 0
        for reverse_type in REVERSE_TYPES:
            cell = MATRIX[scrum_type][reverse_type]
            cell_count += 1
            if cell["rating"] not in RATINGS:
                raise ValueError(f"invalid rating: {scrum_type} x {reverse_type}")
            if cell["rating"] == "Primary":
                primary_count += 1
        if primary_count != 1:
            raise ValueError(f"primary cell mismatch: {scrum_type}")
        if MATRIX[scrum_type][PRIMARY_BY_SCRUM[scrum_type]]["recommended_step"] != PRIMARY_STEP_BY_SCRUM[scrum_type]:
            raise ValueError(f"primary step mismatch: {scrum_type}")
    if cell_count != len(SCRUM_TYPES) * len(REVERSE_TYPES):
        raise ValueError(f"matrix size mismatch: {cell_count}")
    return {"cells": cell_count, "scrum_types": len(SCRUM_TYPES), "reverse_types": len(REVERSE_TYPES)}
