from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from .plan_validator import VALID_LAYERS
    from .skill_catalog import _extract_frontmatter
except ImportError:  # pragma: no cover - script execution fallback
    from plan_validator import VALID_LAYERS  # type: ignore[no-redef]
    from skill_catalog import _extract_frontmatter  # type: ignore[no-redef]


_VALID_HELIX_LAYERS = {layer for layer in VALID_LAYERS if re.fullmatch(r"L(?:[1-9]|1[0-4])", layer)}
_VALID_HELIX_LAYERS.add("all")
_DISTRIBUTION_KEYS = [*sorted(_VALID_HELIX_LAYERS, key=lambda value: (value == "all", value)), "missing"]
_INVALID_LAYER_REASON = "invalid helix_layer: expected one of L1-L14 or all"


def _empty_distribution() -> dict[str, int]:
    return {key: 0 for key in _DISTRIBUTION_KEYS}


def _relative_skill_path(skill_md: Path, skills_root: Path) -> str:
    return skill_md.relative_to(skills_root).as_posix()


def _extract_helix_layer(frontmatter: Any) -> str | None:
    if not isinstance(frontmatter, dict):
        return None
    metadata = frontmatter.get("metadata")
    if not isinstance(metadata, dict):
        return None
    helix_layer = metadata.get("helix_layer")
    if isinstance(helix_layer, str):
        value = helix_layer.strip()
        return value or None
    return None


def audit_skill_helix_layers(skills_root: Path) -> dict[str, Any]:
    """Audit metadata.helix_layer values from SKILL.md files under skills_root."""

    result: dict[str, Any] = {
        "total_skills": 0,
        "with_helix_layer": 0,
        "without_helix_layer": 0,
        "invalid_helix_layer": 0,
        "distribution": _empty_distribution(),
        "invalid_examples": [],
    }

    if not skills_root.exists() or not skills_root.is_dir():
        return result

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        result["total_skills"] += 1

        try:
            frontmatter = _extract_frontmatter(skill_md.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - passthrough safety for malformed files
            result["without_helix_layer"] += 1
            result["distribution"]["missing"] += 1
            result["invalid_examples"].append(
                {
                    "file": _relative_skill_path(skill_md, skills_root),
                    "helix_layer_value": None,
                    "reason": f"frontmatter parse error: {exc}",
                }
            )
            continue

        helix_layer = _extract_helix_layer(frontmatter)
        if helix_layer is None:
            result["without_helix_layer"] += 1
            result["distribution"]["missing"] += 1
            continue

        result["with_helix_layer"] += 1
        if helix_layer in _VALID_HELIX_LAYERS:
            result["distribution"][helix_layer] += 1
            continue

        result["invalid_helix_layer"] += 1
        result["invalid_examples"].append(
            {
                "file": _relative_skill_path(skill_md, skills_root),
                "helix_layer_value": helix_layer,
                "reason": _INVALID_LAYER_REASON,
            }
        )

    return result
