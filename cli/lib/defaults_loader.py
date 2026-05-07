"""Load shared HELIX CLI defaults from cli/config/defaults.yaml."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from .yaml_parser import parse_yaml
except ImportError:  # pragma: no cover - script execution fallback
    from yaml_parser import parse_yaml


DEFAULTS_PATH = Path(__file__).resolve().parents[1] / "config" / "defaults.yaml"
_FALLBACK_DEFAULTS: dict[str, Any] = {
    "classifier": {
        "cache_ttl_sec": 3600,
        "llm_timeout_sec": 10,
        "boundary_scores": [3, 4, 7, 8, 12, 13],
    },
    "recommender": {
        "cache_ttl_sec": 3600,
        "default_top_n": 5,
    },
}


@lru_cache(maxsize=1)
def load_defaults() -> dict[str, Any]:
    """Return CLI defaults, falling back when the config file is absent."""
    if not DEFAULTS_PATH.is_file():
        return deepcopy(_FALLBACK_DEFAULTS)
    parsed = parse_yaml(DEFAULTS_PATH.read_text(encoding="utf-8"))
    return parsed if isinstance(parsed, dict) else deepcopy(_FALLBACK_DEFAULTS)
