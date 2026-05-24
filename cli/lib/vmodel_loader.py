"""V-model semantics loader (PLAN V2-PHASE-2 Task B)."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import sys
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cli.lib.agent_mandatory import MANDATORY_SUBAGENTS, ON_DEMAND_SUBAGENTS
from cli.lib.command_catalog import build_catalog as build_command_catalog, repo_root


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "vmodel-semantics.yaml"
SKILLS_ROOT = REPO_ROOT / "skills"
INJECTION_REQUIRED_FIELDS = (
    "owner_role",
    "mandatory_agents",
    "recommended_agents",
    "recommended_skills",
    "recommended_commands",
    "orchestration_mode",
)


def _require_string_list(value: Any, field_path: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field_path} must be a list[str]")
    if not allow_empty and not value:
        raise ValueError(f"{field_path} must not be empty")
    return value


def _require_non_empty_string(value: Any, field_path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_path} must be a non-empty string")
    return value


@lru_cache(maxsize=1)
def _known_agent_set() -> set[str]:
    mandatory = {
        entry["subagent"]
        for entries in MANDATORY_SUBAGENTS.values()
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("subagent"), str)
    }
    on_demand = {
        entry["subagent"]
        for entry in ON_DEMAND_SUBAGENTS
        if isinstance(entry, dict) and isinstance(entry.get("subagent"), str)
    }
    return mandatory | on_demand


@lru_cache(maxsize=1)
def _known_skill_set() -> set[str]:
    skill_ids: set[str] = set()
    for skill_md in SKILLS_ROOT.rglob("SKILL.md"):
        relative = skill_md.relative_to(SKILLS_ROOT)
        if len(relative.parts) >= 3:
            skill_ids.add(f"{relative.parts[0]}/{relative.parts[1]}")
    return skill_ids


@lru_cache(maxsize=1)
def _known_command_set() -> set[str]:
    return {entry.name for entry in build_command_catalog(repo_root())}


class VmodelInjectionError(ValueError):
    """Raised when an injection block is malformed or references unknown IDs."""


class VModelSemantics:
    def __init__(self, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise ValueError("V-model semantics top-level must be a mapping")
        self.data = data
        self.spine = data.get("spine", {})
        self.drives = data.get("drives", {})
        self.lifecycle = data.get("lifecycle", {})

    @classmethod
    def load(cls, path: Path | str | None = None) -> "VModelSemantics":
        config_path = Path(path) if path else DEFAULT_CONFIG_PATH
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if data is None:
            raise ValueError(f"V-model semantics config is empty: {config_path}")
        if not isinstance(data, dict):
            raise ValueError(f"V-model semantics top-level must be a mapping: {config_path}")
        instance = cls(data)
        instance.validate()
        return instance

    def validate(self) -> None:
        """Validate the normalized V-model semantic contract."""
        errors: list[str] = []

        if self.data.get("schema_version") != 1:
            errors.append("schema_version must be 1")
        if not isinstance(self.spine, dict):
            errors.append("spine must be a mapping")
        if not isinstance(self.drives, dict):
            errors.append("drives must be a mapping")
        if not isinstance(self.lifecycle, dict):
            errors.append("lifecycle must be a mapping")
        if errors:
            self._raise_validation_error(errors)

        allowed_drives = self._allowed_from_mapping(self.spine.get("drives"), "spine.drives.allowed")
        allowed_layers = self.list_layers()
        design_required = self._required_field_list("design_required")
        test_required = self._required_field_list("test_required")
        pair_required = self._required_field_list("pair_required")
        pair_test_levels = self._pair_test_levels()
        allowed_values = self._allowed_values()

        self._validate_lifecycle(errors)

        actual_drives = set(self.drives.keys())
        expected_drives = set(allowed_drives)
        if actual_drives != expected_drives:
            missing = sorted(expected_drives - actual_drives)
            extra = sorted(actual_drives - expected_drives)
            if missing:
                errors.append(f"drives missing entries: {', '.join(missing)}")
            if extra:
                errors.append(f"drives has unexpected entries: {', '.join(extra)}")

        for drive in allowed_drives:
            drive_data = self.drives.get(drive)
            drive_path = f"drives.{drive}"
            if not isinstance(drive_data, dict):
                errors.append(f"{drive_path} must be a mapping")
                continue

            layers = drive_data.get("layers")
            if not isinstance(layers, dict):
                errors.append(f"{drive_path}.layers must be a mapping")
                continue

            actual_layers = set(layers.keys())
            expected_layers = set(allowed_layers)
            if actual_layers != expected_layers:
                missing = sorted(expected_layers - actual_layers)
                extra = sorted(actual_layers - expected_layers)
                if missing:
                    errors.append(f"{drive_path}.layers missing entries: {', '.join(missing)}")
                if extra:
                    errors.append(f"{drive_path}.layers has unexpected entries: {', '.join(extra)}")

            for layer in allowed_layers:
                layer_data = layers.get(layer)
                layer_path = f"{drive_path}.layers.{layer}"
                if not isinstance(layer_data, dict):
                    errors.append(f"{layer_path} must be a mapping")
                    continue

                design = layer_data.get("design")
                test = layer_data.get("test")
                pair = layer_data.get("pair")
                if not isinstance(design, dict):
                    errors.append(f"{layer_path}.design must be a mapping")
                    continue
                if not isinstance(test, dict):
                    errors.append(f"{layer_path}.test must be a mapping")
                    continue
                if not isinstance(pair, dict):
                    errors.append(f"{layer_path}.pair must be a mapping")
                    continue

                self._validate_required_keys(errors, f"{layer_path}.design", design, design_required)
                self._validate_required_keys(errors, f"{layer_path}.test", test, test_required)
                self._validate_required_keys(errors, f"{layer_path}.pair", pair, pair_required)

                self._validate_design(errors, f"{layer_path}.design", design, allowed_values["review_axes"])
                self._validate_test(
                    errors,
                    f"{layer_path}.test",
                    test,
                    expected_level=pair_test_levels[layer],
                    allowed_baseline_policy=allowed_values["baseline_policy"],
                )
                self._validate_pair(
                    errors,
                    f"{layer_path}.pair",
                    pair,
                    allowed_layers=set(allowed_layers),
                    allowed_horizontal_rule=allowed_values["horizontal_rule"],
                    score_range=allowed_values["score_weight"],
                )
                self._validate_injection(
                    layer_data.get("injection"),
                    drive,
                    layer,
                    allowed_values,
                    _known_agent_set(),
                    _known_skill_set(),
                    _known_command_set(),
                )

        if errors:
            self._raise_validation_error(errors)

    def get_layer(self, drive: str, layer: str) -> dict[str, Any]:
        """Return the design/test/pair block for the requested drive and layer."""
        if drive not in self.drives:
            raise KeyError(f"unknown drive: {drive}")
        drive_data = self.drives[drive]
        if not isinstance(drive_data, dict):
            raise KeyError(f"invalid drive mapping: {drive}")
        layers = drive_data.get("layers", {})
        if not isinstance(layers, dict) or layer not in layers:
            raise KeyError(f"unknown layer for drive {drive}: {layer}")
        layer_data = layers[layer]
        if not isinstance(layer_data, dict):
            raise KeyError(f"invalid layer mapping for drive {drive}: {layer}")
        return deepcopy(layer_data)

    def get_layer_injection(self, drive: str, layer: str) -> dict[str, Any]:
        """Return only the injection block for the requested drive and layer."""
        layer_data = self.get_layer(drive, layer)
        injection = layer_data.get("injection")
        if injection is None:
            raise KeyError(f"injection not defined for drive={drive} layer={layer}")
        if not isinstance(injection, dict):
            raise ValueError(f"injection must be a mapping for drive={drive} layer={layer}")
        return deepcopy(injection)

    def list_drives(self) -> list[str]:
        drives_cfg = self.spine.get("drives")
        if isinstance(drives_cfg, dict) and isinstance(drives_cfg.get("allowed"), list):
            return list(drives_cfg["allowed"])
        return list(self.drives.keys())

    def list_layers(self) -> list[str]:
        layers_cfg = self.spine.get("layers")
        if isinstance(layers_cfg, dict) and isinstance(layers_cfg.get("allowed"), list):
            return list(layers_cfg["allowed"])
        return []

    def origin_modes(self) -> list[str]:
        origin_mode = self.lifecycle.get("origin_mode")
        return list(origin_mode) if isinstance(origin_mode, list) else []

    def evidence_statuses(self) -> list[str]:
        evidence_status = self.lifecycle.get("evidence_status")
        return list(evidence_status) if isinstance(evidence_status, list) else []

    def _allowed_from_mapping(self, mapping: Any, field_path: str) -> list[str]:
        if not isinstance(mapping, dict):
            raise ValueError(f"{field_path.rsplit('.', 1)[0]} must be a mapping")
        return _require_string_list(mapping.get("allowed"), field_path)

    def _required_field_list(self, field_name: str) -> list[str]:
        return _require_string_list(self.spine.get(field_name), f"spine.{field_name}")

    def _pair_test_levels(self) -> dict[str, str]:
        layers_cfg = self.spine.get("layers")
        if not isinstance(layers_cfg, dict):
            raise ValueError("spine.layers must be a mapping")
        pair_test_levels = layers_cfg.get("pair_test_levels")
        if not isinstance(pair_test_levels, dict):
            raise ValueError("spine.layers.pair_test_levels must be a mapping")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in pair_test_levels.items()):
            raise ValueError("spine.layers.pair_test_levels must be dict[str, str]")
        return dict(pair_test_levels)

    def _allowed_values(self) -> dict[str, Any]:
        allowed_values = self.spine.get("allowed_values")
        if not isinstance(allowed_values, dict):
            raise ValueError("spine.allowed_values must be a mapping")
        review_axes = set(_require_string_list(allowed_values.get("review_axes"), "spine.allowed_values.review_axes"))
        owner_role = set(_require_string_list(allowed_values.get("owner_role"), "spine.allowed_values.owner_role"))
        orchestration_mode = set(
            _require_string_list(
                allowed_values.get("orchestration_mode"),
                "spine.allowed_values.orchestration_mode",
            )
        )
        baseline_policy = set(
            _require_string_list(allowed_values.get("baseline_policy"), "spine.allowed_values.baseline_policy")
        )
        horizontal_rule = set(
            _require_string_list(allowed_values.get("horizontal_rule"), "spine.allowed_values.horizontal_rule")
        )
        score_weight = allowed_values.get("score_weight")
        if not isinstance(score_weight, dict):
            raise ValueError("spine.allowed_values.score_weight must be a mapping")
        minimum = score_weight.get("min")
        maximum = score_weight.get("max")
        if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
            raise ValueError("spine.allowed_values.score_weight.min/max must be numbers")
        return {
            "review_axes": review_axes,
            "owner_role": owner_role,
            "orchestration_mode": orchestration_mode,
            "baseline_policy": baseline_policy,
            "horizontal_rule": horizontal_rule,
            "score_weight": (float(minimum), float(maximum)),
        }

    def _validate_lifecycle(self, errors: list[str]) -> None:
        try:
            _require_string_list(self.lifecycle.get("origin_mode"), "lifecycle.origin_mode")
            _require_string_list(self.lifecycle.get("evidence_status"), "lifecycle.evidence_status")
            _require_string_list(self.lifecycle.get("direction"), "lifecycle.direction")
        except ValueError as exc:
            errors.append(str(exc))

        origin_mode_transitions = self.lifecycle.get("origin_mode_transitions")
        if not isinstance(origin_mode_transitions, dict):
            errors.append("lifecycle.origin_mode_transitions must be a mapping")
        else:
            reverse_to_forward = origin_mode_transitions.get("reverse_to_forward")
            if not isinstance(reverse_to_forward, dict):
                errors.append("lifecycle.origin_mode_transitions.reverse_to_forward must be a mapping")
            else:
                try:
                    _require_non_empty_string(
                        reverse_to_forward.get("trigger"),
                        "lifecycle.origin_mode_transitions.reverse_to_forward.trigger",
                    )
                    _require_non_empty_string(
                        reverse_to_forward.get("notes"),
                        "lifecycle.origin_mode_transitions.reverse_to_forward.notes",
                    )
                except ValueError as exc:
                    errors.append(str(exc))
                automatic = reverse_to_forward.get("automatic")
                if not isinstance(automatic, bool):
                    errors.append(
                        "lifecycle.origin_mode_transitions.reverse_to_forward.automatic must be a boolean"
                    )

        evidence_status_transitions = self.lifecycle.get("evidence_status_transitions")
        if not isinstance(evidence_status_transitions, dict):
            errors.append("lifecycle.evidence_status_transitions must be a mapping")
        else:
            for key in ("observed_to_inferred", "inferred_to_confirmed"):
                try:
                    _require_non_empty_string(
                        evidence_status_transitions.get(key),
                        f"lifecycle.evidence_status_transitions.{key}",
                    )
                except ValueError as exc:
                    errors.append(str(exc))

        functional_freeze_applicability = self.lifecycle.get("functional_freeze_applicability")
        if not isinstance(functional_freeze_applicability, dict):
            errors.append("lifecycle.functional_freeze_applicability must be a mapping")
        else:
            for key in ("reverse_mode", "forward_mode"):
                try:
                    _require_non_empty_string(
                        functional_freeze_applicability.get(key),
                        f"lifecycle.functional_freeze_applicability.{key}",
                    )
                except ValueError as exc:
                    errors.append(str(exc))

    @staticmethod
    def _validate_required_keys(errors: list[str], field_path: str, data: dict[str, Any], required_keys: list[str]) -> None:
        missing = [key for key in required_keys if key not in data]
        if missing:
            errors.append(f"{field_path} missing required fields: {', '.join(missing)}")

    @staticmethod
    def _validate_design(
        errors: list[str],
        field_path: str,
        design: dict[str, Any],
        allowed_review_axes: set[str],
    ) -> None:
        try:
            _require_string_list(design.get("artifacts"), f"{field_path}.artifacts")
            review_axes = _require_string_list(design.get("review_axes"), f"{field_path}.review_axes")
            detectors = _require_string_list(design.get("detectors"), f"{field_path}.detectors")
        except ValueError as exc:
            errors.append(str(exc))
            return

        review_unit = design.get("review_unit")
        if not isinstance(review_unit, str) or not review_unit:
            errors.append(f"{field_path}.review_unit must be a non-empty string")
        invalid_axes = sorted(set(review_axes) - allowed_review_axes)
        if invalid_axes:
            errors.append(f"{field_path}.review_axes has unsupported values: {', '.join(invalid_axes)}")
        if not detectors:
            errors.append(f"{field_path}.detectors must not be empty")

    @staticmethod
    def _validate_test(
        errors: list[str],
        field_path: str,
        test: dict[str, Any],
        *,
        expected_level: str,
        allowed_baseline_policy: set[str],
    ) -> None:
        try:
            _require_string_list(test.get("artifacts"), f"{field_path}.artifacts")
            detectors = _require_string_list(test.get("detectors"), f"{field_path}.detectors")
        except ValueError as exc:
            errors.append(str(exc))
            return

        test_level = test.get("test_level")
        if test_level != expected_level:
            errors.append(f"{field_path}.test_level must be {expected_level!r}, got {test_level!r}")
        baseline_policy = test.get("baseline_policy")
        if not isinstance(baseline_policy, str) or baseline_policy not in allowed_baseline_policy:
            allowed = ", ".join(sorted(allowed_baseline_policy))
            errors.append(f"{field_path}.baseline_policy must be one of: {allowed}")
        if not detectors:
            errors.append(f"{field_path}.detectors must not be empty")

    @staticmethod
    def _validate_pair(
        errors: list[str],
        field_path: str,
        pair: dict[str, Any],
        *,
        allowed_layers: set[str],
        allowed_horizontal_rule: set[str],
        score_range: tuple[float, float],
    ) -> None:
        horizontal_rule = pair.get("horizontal_rule")
        if not isinstance(horizontal_rule, str) or horizontal_rule not in allowed_horizontal_rule:
            allowed = ", ".join(sorted(allowed_horizontal_rule))
            errors.append(f"{field_path}.horizontal_rule must be one of: {allowed}")

        for key in ("vertical_from", "vertical_to"):
            value = pair.get(key)
            if value is not None and (not isinstance(value, str) or value not in allowed_layers):
                errors.append(f"{field_path}.{key} must be null or one of: {', '.join(sorted(allowed_layers))}")

        score_weight = pair.get("score_weight")
        minimum, maximum = score_range
        if not isinstance(score_weight, (int, float)) or not (minimum <= float(score_weight) <= maximum):
            errors.append(f"{field_path}.score_weight must be between {minimum} and {maximum}")

        if "promotion" not in pair:
            errors.append(f"{field_path}.promotion must be present")
        elif pair["promotion"] is not None:
            promotion = pair["promotion"]
            if not isinstance(promotion, dict):
                errors.append(f"{field_path}.promotion must be a mapping or null")
            elif promotion.get("append_only") is not True:
                errors.append(f"{field_path}.promotion.append_only must be true")

    @staticmethod
    def _validate_injection(
        injection: Any,
        drive: str,
        layer: str,
        allowed_values: dict[str, Any],
        agent_set: set[str],
        skill_set: set[str],
        command_set: set[str],
    ) -> None:
        field_path = f"{drive}/{layer}/injection"
        if not isinstance(injection, dict):
            raise VmodelInjectionError(f"{field_path}: must be a mapping")

        missing = [field for field in INJECTION_REQUIRED_FIELDS if field not in injection]
        if missing:
            raise VmodelInjectionError(f"{field_path}: missing required fields: {', '.join(missing)}")

        owner_role = _require_non_empty_string(injection.get("owner_role"), f"{field_path}.owner_role")
        if owner_role not in allowed_values["owner_role"]:
            raise VmodelInjectionError(f"{field_path}: unknown owner_role {owner_role!r}")

        orchestration_mode = _require_non_empty_string(
            injection.get("orchestration_mode"),
            f"{field_path}.orchestration_mode",
        )
        if orchestration_mode not in allowed_values["orchestration_mode"]:
            raise VmodelInjectionError(f"{field_path}: unknown orchestration_mode {orchestration_mode!r}")

        for list_name in ("mandatory_agents", "recommended_agents"):
            values = _require_string_list(injection.get(list_name), f"{field_path}.{list_name}", allow_empty=True)
            for agent in values:
                if agent not in agent_set:
                    raise VmodelInjectionError(f"{field_path}: unknown agent {agent!r} in {list_name}")

        recommended_skills = _require_string_list(
            injection.get("recommended_skills"),
            f"{field_path}.recommended_skills",
            allow_empty=True,
        )
        for skill_id in recommended_skills:
            if skill_id not in skill_set:
                raise VmodelInjectionError(f"{field_path}: unknown skill {skill_id!r} in recommended_skills")

        recommended_commands = _require_string_list(
            injection.get("recommended_commands"),
            f"{field_path}.recommended_commands",
            allow_empty=True,
        )
        for command in recommended_commands:
            prefix = "helix "
            if not command.startswith(prefix):
                raise VmodelInjectionError(
                    f"{field_path}: recommended_commands entries must start with 'helix '"
                )
            subcommand = command[len(prefix) :]
            if not subcommand or subcommand not in command_set:
                raise VmodelInjectionError(f"{field_path}: unknown command {command!r} in recommended_commands")

    @staticmethod
    def _raise_validation_error(errors: list[str]) -> None:
        raise ValueError("V-model semantics validation failed:\n- " + "\n- ".join(errors))


def load_default() -> VModelSemantics:
    return VModelSemantics.load()
