from __future__ import annotations

import json
import py_compile
import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_HINT_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*->\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")


class JsonConverterBuilder(BuilderBase):
    BUILDER_TYPE = "json-converter"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["name", "source_schema", "target_schema", "mapping_hints"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")

        source_schema = params.get("source_schema")
        target_schema = params.get("target_schema")
        mapping_hints = params.get("mapping_hints", {})

        if not isinstance(source_schema, dict) or not source_schema:
            raise ValueError("source_schema must be a non-empty object")
        if not isinstance(target_schema, dict) or not target_schema:
            raise ValueError("target_schema must be a non-empty object")
        if not isinstance(mapping_hints, dict):
            raise ValueError("mapping_hints must be an object")

        hint_rules: list[dict] = []
        for raw_key, raw_hint in mapping_hints.items():
            key = str(raw_key)
            match = _HINT_RE.match(key)
            if not match:
                raise ValueError(f"invalid mapping hint key: {key}")
            source_field, target_field = match.group(1), match.group(2)
            hint_rules.append(
                {
                    "source": source_field,
                    "target": target_field,
                    "hint": str(raw_hint),
                }
            )

        return {
            "name": name,
            "source_schema": source_schema,
            "target_schema": target_schema,
            "mapping_hints": mapping_hints,
            "hint_rules": hint_rules,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        name = params["name"]
        base_dir = Path(self.project_root) / "builders" / "json-converters"
        base_dir.mkdir(parents=True, exist_ok=True)

        definition_path = base_dir / f"{name}.json"
        script_path = base_dir / f"convert_{name}.py"

        rule_map = _build_rule_map(
            source_schema=params["source_schema"],
            target_schema=params["target_schema"],
            hint_rules=params["hint_rules"],
        )

        definition = {
            "name": name,
            "builder_type": self.BUILDER_TYPE,
            "source_schema": params["source_schema"],
            "target_schema": params["target_schema"],
            "mapping_hints": params["mapping_hints"],
            "rules": rule_map,
        }
        definition_path.write_text(json.dumps(definition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        script_code = _render_converter_script(name=name, target_schema=params["target_schema"], hint_rules=params["hint_rules"])
        script_path.write_text(script_code, encoding="utf-8")
        script_path.chmod(0o755)

        return [
            {
                "path": str(definition_path.relative_to(self.project_root)),
                "kind": "json-converter-definition",
            },
            {
                "path": str(script_path.relative_to(self.project_root)),
                "kind": "json-converter-script",
            },
        ]

    def validate_output(self, artifacts: list[dict]) -> dict:
        if not isinstance(artifacts, list) or len(artifacts) < 2:
            raise ValueError("artifacts must include definition json and converter script")

        artifact_paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        for path in artifact_paths:
            if not path.exists():
                raise ValueError(f"artifact not found: {path}")

        converter_paths = [p for p in artifact_paths if p.name.startswith("convert_") and p.suffix == ".py"]
        if len(converter_paths) != 1:
            raise ValueError("converter script artifact is missing")

        py_compile.compile(str(converter_paths[0]), doraise=True)

        return {
            "valid": True,
            "checked_files": [str(path) for path in artifact_paths],
            "quality_score": 100,
        }


def _build_rule_map(source_schema: dict, target_schema: dict, hint_rules: list[dict]) -> list[dict]:
    rules: list[dict] = []
    by_target = {(rule["target"]): rule for rule in hint_rules}

    for target_field, target_type in target_schema.items():
        if target_field in by_target:
            rule = by_target[target_field]
            rules.append(
                {
                    "target": target_field,
                    "target_type": target_type,
                    "source": rule["source"],
                    "strategy": "hint",
                    "hint": rule["hint"],
                }
            )
        elif target_field in source_schema:
            rules.append(
                {
                    "target": target_field,
                    "target_type": target_type,
                    "source": target_field,
                    "strategy": "direct",
                    "hint": "same field name",
                }
            )
        else:
            rules.append(
                {
                    "target": target_field,
                    "target_type": target_type,
                    "source": None,
                    "strategy": "missing",
                    "hint": "fill with null/default",
                }
            )

    return rules


def _render_converter_script(name: str, target_schema: dict, hint_rules: list[dict]) -> str:
    target_fields = list(target_schema.keys())

    lines = [
        "#!/usr/bin/env python3",
        "from __future__ import annotations",
        "",
        "import json",
        "import sys",
        "",
        f"CONVERTER_NAME = {name!r}",
        "",
    ]

    seen_funcs: set[str] = set()
    for rule in hint_rules:
        func_name = _function_name(rule["source"], rule["target"])
        if func_name in seen_funcs:
            continue
        seen_funcs.add(func_name)
        lines.extend(
            [
                f"def {func_name}(value, source):",
                f"    \"\"\"TODO: {rule['source']} -> {rule['target']} ({rule['hint']})\"\"\"",
                "    del source  # source 全体が必要な場合はこの行を削除して使う",
                "    return value",
                "",
            ]
        )

    lines.extend(
        [
            "def convert(source):",
            "    if not isinstance(source, dict):",
            "        raise ValueError('input must be a JSON object')",
            "",
            "    output = {}",
        ]
    )

    for field in target_fields:
        lines.append(f"    output[{field!r}] = source.get({field!r})")

    for rule in hint_rules:
        func_name = _function_name(rule["source"], rule["target"])
        lines.append(
            f"    output[{rule['target']!r}] = {func_name}(source.get({rule['source']!r}), source)"
        )

    lines.extend(
        [
            "    return output",
            "",
            "def main():",
            "    payload = json.load(sys.stdin)",
            "    converted = convert(payload)",
            "    json.dump(converted, sys.stdout, ensure_ascii=False, indent=2)",
            "    sys.stdout.write('\\n')",
            "",
            "",
            "if __name__ == '__main__':",
            "    try:",
            "        main()",
            "    except Exception as exc:",
            "        print(f'Error: {exc}', file=sys.stderr)",
            "        raise SystemExit(1)",
            "",
        ]
    )

    return "\n".join(lines)


def _function_name(source_field: str, target_field: str) -> str:
    source = _sanitize_identifier(source_field)
    target = _sanitize_identifier(target_field)
    return f"map_{source}_to_{target}"


def _sanitize_identifier(text: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", text)
    if not safe:
        safe = "field"
    if safe[0].isdigit():
        safe = f"f_{safe}"
    return safe


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(JsonConverterBuilder)
