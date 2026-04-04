#!/usr/bin/env python3
"""JSON Schema の簡易バリデータ（標準ライブラリのみ）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"


def validate(data: dict[str, Any], schema_name: str) -> list[str]:
    """指定スキーマでデータを検証し、エラー一覧を返す。"""
    schema_path = _resolve_schema_path(schema_name)
    if not schema_path.exists():
        return [f"schema not found: {schema_path}"]

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"failed to load schema '{schema_path.name}': {exc}"]

    errors: list[str] = []
    _validate_node(data, schema, "$", schema, errors)
    return errors


def _resolve_schema_path(schema_name: str) -> Path:
    name = schema_name.strip()
    if name.endswith(".json"):
        return _SCHEMAS_DIR / name
    if name.endswith(".schema"):
        return _SCHEMAS_DIR / f"{name}.json"
    return _SCHEMAS_DIR / f"{name}.schema.json"


def _validate_node(value: Any, schema: dict[str, Any], path: str, root: dict[str, Any], errors: list[str]) -> None:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_ref(ref, root)
        if resolved is None:
            errors.append(f"{path}: unresolved ref '{ref}'")
            return
        _validate_node(value, resolved, path, root, errors)
        return

    expected_type = schema.get("type")
    if expected_type is not None and not _type_matches(value, expected_type):
        errors.append(f"{path}: expected type {expected_type}, got {_type_name(value)}")
        return

    enum_values = schema.get("enum")
    if isinstance(enum_values, list) and value not in enum_values:
        errors.append(f"{path}: expected one of {enum_values}, got {value!r}")

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{path}: string length must be >= {min_length}")

    if _is_number(value):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and float(value) < float(minimum):
            errors.append(f"{path}: value must be >= {minimum}")
        if isinstance(maximum, (int, float)) and float(value) > float(maximum):
            errors.append(f"{path}: value must be <= {maximum}")

    if isinstance(value, dict):
        _validate_object(value, schema, path, root, errors)
    elif isinstance(value, list):
        _validate_array(value, schema, path, root, errors)


def _validate_object(value: dict[str, Any], schema: dict[str, Any], path: str, root: dict[str, Any], errors: list[str]) -> None:
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if isinstance(key, str) and key not in value:
                errors.append(f"{path}: missing required property '{key}'")

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    additional = schema.get("additionalProperties", True)
    for key, item in value.items():
        child_path = f"{path}.{key}"
        if key in properties:
            prop_schema = properties.get(key)
            if isinstance(prop_schema, dict):
                _validate_node(item, prop_schema, child_path, root, errors)
        elif additional is False:
            errors.append(f"{path}: additional property '{key}' is not allowed")
        elif isinstance(additional, dict):
            _validate_node(item, additional, child_path, root, errors)


def _validate_array(value: list[Any], schema: dict[str, Any], path: str, root: dict[str, Any], errors: list[str]) -> None:
    items = schema.get("items")
    if not isinstance(items, dict):
        return
    for idx, item in enumerate(value):
        _validate_node(item, items, f"{path}[{idx}]", root, errors)


def _resolve_ref(ref: str, root: dict[str, Any]) -> dict[str, Any] | None:
    if not ref.startswith("#/"):
        return None
    node: Any = root
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, dict) else None


def _type_matches(value: Any, expected: str | list[Any]) -> bool:
    if isinstance(expected, list):
        return any(_type_matches(value, item) for item in expected)
    if not isinstance(expected, str):
        return True

    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return _is_number(value)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__
