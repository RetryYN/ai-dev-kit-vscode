"""PLAN-095 Scrum hypothesis routing tests.

DoD 検証: docs/plans/PLAN-095-poc-scrum-reverse-matrix.md §8 §9
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import scrum_to_reverse_routing


def test_route_scrum_to_reverse_uses_primary_matrix_mapping(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    backlog = tmp_path / "backlog.yaml"
    backlog.write_text("hypotheses:\n  H001:\n    scrum_type: tech-spike\n", encoding="utf-8")
    monkeypatch.setenv("HELIX_SCRUM_BACKLOG", os.fspath(backlog))

    assert scrum_to_reverse_routing.route_scrum_to_reverse("H001") == ("design", "Primary")


def test_route_scrum_to_reverse_defaults_to_hypothesis_test_when_backlog_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HELIX_SCRUM_BACKLOG", os.fspath(Path("/tmp/nonexistent-scrum-backlog.yaml")))

    assert scrum_to_reverse_routing.route_scrum_to_reverse("H999") == ("code", "Primary")


def test_route_scrum_to_reverse_rejects_unknown_hypothesis_in_existing_backlog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backlog = tmp_path / "backlog.yaml"
    backlog.write_text("hypotheses:\n  H001:\n    scrum_type: design-spike\n", encoding="utf-8")
    monkeypatch.setenv("HELIX_SCRUM_BACKLOG", os.fspath(backlog))

    with pytest.raises(ValueError, match="unknown scrum hypothesis"):
        scrum_to_reverse_routing.route_scrum_to_reverse("H404")


def test_route_scrum_to_reverse_rejects_invalid_scrum_type(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    backlog = tmp_path / "backlog.yaml"
    backlog.write_text("hypotheses:\n  H001:\n    scrum_type: not-a-type\n", encoding="utf-8")
    monkeypatch.setenv("HELIX_SCRUM_BACKLOG", os.fspath(backlog))

    with pytest.raises(ValueError, match="unknown scrum_type"):
        scrum_to_reverse_routing.route_scrum_to_reverse("H001")
