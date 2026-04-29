"""Helpers for reading gate accuracy weights from gate-policy.md."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


WEIGHT_PATTERN = re.compile(r"\|\s*accuracy_weight\s*\|\s*([0-9.]+)\s*\|")
SECTION_PATTERN = re.compile(
    r"^#{2,3}\s+(G0\.5|G1\.5|G1R|G[1-7]|L8)[\s　].*?$",
    re.MULTILINE,
)


def load_accuracy_weights(policy_path: Path) -> dict[str, float]:
    """Parse gate-policy.md and return ``{gate_name: accuracy_weight}``.

    Missing files return an empty mapping so gate feedback can fail open.
    ``PLAN_REVIEW`` is intentionally excluded because gate-policy.md defines it
    as a review record rather than a HELIX gate.
    """
    try:
        text = policy_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}

    weights: dict[str, float] = {}
    sections = list(SECTION_PATTERN.finditer(text))
    for index, match in enumerate(sections):
        gate_name = match.group(1).strip()
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        weight_match = WEIGHT_PATTERN.search(text[start:end])
        if weight_match:
            weights[gate_name] = float(weight_match.group(1))
    return weights


def compute_weighted_score(scores: list[dict[str, Any]], weight: float) -> float:
    """Return the average Lv1-5 score multiplied by the gate weight."""
    if not scores:
        return 0.0

    levels = [score["level"] for score in scores if type(score.get("level")) is int]
    if not levels:
        return 0.0

    average = sum(levels) / len(levels)
    return round(average * weight, 4)


def resolve_gate_policy_path() -> Path:
    """Return the default absolute path for HELIX gate-policy.md."""
    helix_home = os.environ.get("HELIX_HOME", "").strip()
    if not helix_home:
        helix_home = str(Path.home() / "ai-dev-kit-vscode")
    return (
        Path(helix_home)
        / "skills"
        / "tools"
        / "ai-coding"
        / "references"
        / "gate-policy.md"
    )
