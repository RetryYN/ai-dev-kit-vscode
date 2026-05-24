from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEPRECATED_DRIVES: dict[str, str] = {
    "scrum": "discovery",
}

PHASE_DISPLAY_MAP = {
    "S0": "D0",
    "S1": "D1",
    "S2": "D2",
    "S3": "D3",
    "D0": "S0",
    "D1": "S1",
    "D2": "S2",
    "D3": "S3",
}

VALID_COMPAT_STAGES = {1, 2, 3, 4}


def _project_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root)
    return Path.cwd()


def helix_dir() -> Path:
    return _project_root() / ".helix"


def config_path() -> Path:
    return helix_dir() / "config.yaml"


def _load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def get_compat_stage() -> int:
    """Resolve compat stage from env > config > default."""
    env_value = os.environ.get("HELIX_DISCOVERY_COMPAT_STAGE")
    if env_value is not None:
        try:
            stage = int(env_value)
        except ValueError as exc:  # pragma: no cover - exercised via invalid path
            raise ValueError(f"HELIX_DISCOVERY_COMPAT_STAGE 不正値: {env_value}") from exc
        if stage not in VALID_COMPAT_STAGES:
            raise ValueError(f"HELIX_DISCOVERY_COMPAT_STAGE 不正値: {stage}")
        return stage

    config = _load_config()
    stage = ((config.get("discovery") or {}) if isinstance(config.get("discovery"), dict) else {}).get(
        "compat_stage",
        1,
    )
    if stage not in VALID_COMPAT_STAGES:
        raise ValueError(f".helix/config.yaml discovery.compat_stage 不正値: {stage}")
    return int(stage)


def is_drive_deprecated(drive: str | None) -> bool:
    return bool(drive) and drive in DEPRECATED_DRIVES


def normalize_drive(drive: str | None) -> str | None:
    if drive is None:
        return None
    return DEPRECATED_DRIVES.get(drive, drive)


def normalize_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    if mode == "scrum":
        return "discovery"
    return mode


def resolve_runtime_dir(helix_root: Path | str | None = None) -> Path:
    root = Path(helix_root) if helix_root is not None else helix_dir()
    discovery = root / "discovery"
    if discovery.exists():
        return discovery
    return root / "scrum"


def phase_to_display(phase: str | None, decide_result: str | None = None) -> str | None:
    if phase is None:
        return None
    if phase == "S3" and decide_result == "confirmed":
        return "D4"
    return PHASE_DISPLAY_MAP.get(phase, phase)


def display_to_phase(display: str | None) -> str | None:
    if display is None:
        return None
    if display == "D4":
        raise ValueError("D4 は DB state ではありません。decide_result から派生して表示します。")
    return PHASE_DISPLAY_MAP.get(display, display)

