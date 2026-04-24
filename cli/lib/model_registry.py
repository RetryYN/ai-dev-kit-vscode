#!/usr/bin/env python3
"""models.yaml からロール別モデルを解決する。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from yaml_parser import parse_yaml
except ImportError:  # pragma: no cover
    parse_yaml = None  # type: ignore[assignment]


def _default_models_path() -> Path:
    explicit = os.environ.get("HELIX_MODELS_CONFIG", "").strip()
    if explicit:
        return Path(explicit).expanduser().resolve()

    helix_home = os.environ.get("HELIX_HOME", "").strip()
    if helix_home:
        from_home = Path(helix_home).expanduser().resolve() / "cli" / "config" / "models.yaml"
        if from_home.exists():
            return from_home

    return Path(__file__).resolve().parents[1] / "config" / "models.yaml"


def load_models_config(path: str | Path | None = None) -> dict[str, Any]:
    model_path = Path(path).expanduser().resolve() if path is not None else _default_models_path()
    if not model_path.exists() or parse_yaml is None:
        return {}

    try:
        payload = parse_yaml(model_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}


def _clean_model(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def get_default_primary(*, default: str = "") -> str:
    config = load_models_config()
    primary = _clean_model(config.get("default_primary"))
    return primary or default


def get_default_fallback(*, default: str = "") -> str:
    config = load_models_config()
    fallback = _clean_model(config.get("default_fallback"))
    return fallback or default


def resolve_role_model(
    role: str,
    *,
    default: str = "",
    allow_override: bool = True,
    override_env: str = "HELIX_MODEL_OVERRIDE",
) -> str:
    if allow_override:
        override_model = _clean_model(os.environ.get(override_env))
        if override_model:
            return override_model

    config = load_models_config()
    roles = config.get("roles")
    if isinstance(roles, dict):
        role_config = roles.get(role)
        if isinstance(role_config, dict):
            for key in ("primary", "model"):
                role_model = _clean_model(role_config.get(key))
                if role_model:
                    return role_model
            models = role_config.get("models")
            if isinstance(models, list):
                for item in models:
                    role_model = _clean_model(item)
                    if role_model:
                        return role_model
        else:
            role_model = _clean_model(role_config)
            if role_model:
                return role_model

    primary = _clean_model(config.get("default_primary"))
    if primary:
        return primary
    return default
