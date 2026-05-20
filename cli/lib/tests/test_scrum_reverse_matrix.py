"""PLAN-095 Scrum × Reverse matrix tests.

DoD 検証: docs/plans/PLAN-095-poc-scrum-reverse-matrix.md §11
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import scrum_reverse_matrix


def test_matrix_complete() -> None:
    assert scrum_reverse_matrix.validate_matrix() == {"cells": 30, "scrum_types": 6, "reverse_types": 5}
    assert sum(len(scrum_reverse_matrix.MATRIX[scrum_type]) for scrum_type in scrum_reverse_matrix.SCRUM_TYPES) == 30


def test_lookup_primary_cell() -> None:
    assert scrum_reverse_matrix.lookup_matrix("tech-spike", "design")["rating"] == "Primary"


def test_lookup_alternative_cell() -> None:
    assert scrum_reverse_matrix.lookup_matrix("design-spike", "fullback")["rating"] == "Alternative"


def test_lookup_invalid_type() -> None:
    with pytest.raises(ValueError, match="unknown scrum_type"):
        scrum_reverse_matrix.lookup_matrix("unknown", "design")
    with pytest.raises(ValueError, match="unknown reverse_type"):
        scrum_reverse_matrix.lookup_matrix("tech-spike", "unknown")


def test_validate_matrix_consistency() -> None:
    for scrum_type in scrum_reverse_matrix.SCRUM_TYPES:
        for reverse_type in scrum_reverse_matrix.REVERSE_TYPES:
            assert scrum_reverse_matrix.lookup_matrix(scrum_type, reverse_type)["rating"] in scrum_reverse_matrix.RATINGS


def test_matrix_immutability() -> None:
    with pytest.raises(TypeError):
        scrum_reverse_matrix.MATRIX["tech-spike"] = {}
    with pytest.raises(TypeError):
        scrum_reverse_matrix.MATRIX["tech-spike"]["design"]["rating"] = "N/A"
