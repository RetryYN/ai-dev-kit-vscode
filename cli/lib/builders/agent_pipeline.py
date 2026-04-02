from __future__ import annotations

import json
import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_ALLOWED_ERROR_HANDLING = {"retry_stage", "skip_stage", "abort"}


class AgentPipelineBuilder(BuilderBase):
    BUILDER_TYPE = "agent-pipeline"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["name", "stages", "error_handling"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        stages = params.get("stages")
        error_handling = str(params.get("error_handling", "")).strip()

        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
        if not isinstance(stages, list) or not stages:
            raise ValueError("stages must be a non-empty array")
        if error_handling not in _ALLOWED_ERROR_HANDLING:
            raise ValueError(f"error_handling must be one of {sorted(_ALLOWED_ERROR_HANDLING)}")

        normalized_stages: list[dict] = []
        stage_names: set[str] = set()
        for index, stage in enumerate(stages, start=1):
            if not isinstance(stage, dict):
                raise ValueError(f"stages[{index}] must be an object")
            stage_name = str(stage.get("name", "")).strip()
            builder = str(stage.get("builder", "")).strip()
            if not stage_name:
                raise ValueError(f"stages[{index}].name is required")
            if stage_name in stage_names:
                raise ValueError(f"duplicate stage name: {stage_name}")
            if not builder:
                raise ValueError(f"stages[{index}].builder is required")
            stage_names.add(stage_name)

            config = stage.get("config", {})
            if config is None:
                config = {}
            if not isinstance(config, dict):
                raise ValueError(f"stages[{index}].config must be an object")

            normalized_stage = dict(stage)
            normalized_stage["name"] = stage_name
            normalized_stage["builder"] = builder
            normalized_stage["config"] = config
            normalized_stages.append(normalized_stage)

        return {
            "name": name,
            "stages": normalized_stages,
            "error_handling": error_handling,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        pipelines_dir = Path(self.project_root) / "builders" / "pipelines"
        pipelines_dir.mkdir(parents=True, exist_ok=True)

        output_path = pipelines_dir / f"{params['name']}.json"
        contract_report = _check_stage_contracts(params["stages"])

        payload = {
            "name": params["name"],
            "builder_type": self.BUILDER_TYPE,
            "stages": params["stages"],
            "error_handling": params["error_handling"],
            "contract_checks": contract_report,
        }

        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return [{"path": str(output_path.relative_to(self.project_root)), "kind": "pipeline-definition"}]

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if len(paths) != 1:
            raise ValueError("agent-pipeline expects one artifact")

        output_path = paths[0]
        if not output_path.exists():
            raise ValueError(f"artifact not found: {output_path}")

        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc}")

        if not isinstance(payload, dict):
            raise ValueError("pipeline definition must be an object")

        stages = payload.get("stages")
        if not isinstance(stages, list) or len(stages) < 1:
            raise ValueError("pipeline must include at least one stage")

        return {
            "valid": True,
            "checked_files": [str(output_path)],
            "quality_score": 100,
        }


def _check_stage_contracts(stages: list[dict]) -> dict:
    issues: list[dict] = []
    adapter_suggestions: list[dict] = []

    for index in range(1, len(stages)):
        prev_stage = stages[index - 1]
        next_stage = stages[index]

        prev_exports = _extract_contract(prev_stage, "exports")
        next_consumes = _extract_contract(next_stage, "consumes")

        if not next_consumes:
            continue

        for field, required_type in next_consumes.items():
            produced_type = prev_exports.get(field)
            if produced_type is None:
                issues.append(
                    {
                        "type": "missing_field",
                        "from_stage": prev_stage.get("name"),
                        "to_stage": next_stage.get("name"),
                        "field": field,
                        "required": required_type,
                    }
                )
                continue

            if not _type_compatible(produced_type, required_type):
                issues.append(
                    {
                        "type": "type_mismatch",
                        "from_stage": prev_stage.get("name"),
                        "to_stage": next_stage.get("name"),
                        "field": field,
                        "produced": produced_type,
                        "required": required_type,
                    }
                )
                adapter_suggestions.append(
                    {
                        "from_stage": prev_stage.get("name"),
                        "to_stage": next_stage.get("name"),
                        "adapter": "json-converter",
                        "reason": f"{field}: {produced_type} -> {required_type}",
                    }
                )

    return {
        "issues": issues,
        "adapter_suggestions": adapter_suggestions,
    }


def _extract_contract(stage: dict, key: str) -> dict[str, str]:
    contract = stage.get(key)
    if contract is None:
        config = stage.get("config", {})
        if isinstance(config, dict):
            contract = config.get(key)

    if not isinstance(contract, dict):
        return {}

    result: dict[str, str] = {}
    for field, value in contract.items():
        field_name = str(field).strip()
        value_name = str(value).strip()
        if field_name and value_name:
            result[field_name] = value_name
    return result


def _type_compatible(produced: str, required: str) -> bool:
    produced_norm = produced.strip().lower()
    required_norm = required.strip().lower()
    if not produced_norm or not required_norm:
        return True
    if produced_norm == required_norm:
        return True
    return produced_norm in {"any", "unknown", "object"} or required_norm in {"any", "unknown"}


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(AgentPipelineBuilder)
