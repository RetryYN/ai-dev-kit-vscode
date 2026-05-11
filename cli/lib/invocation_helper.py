#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import math
import os
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parent
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


ENV_PREFIX = "HELIX_INVOCATION_"
ALLOWLIST = helix_db.INVOCATION_META_ALLOWLIST


def _clean_text(value: object, default: str | None = None) -> str | None:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def build_payload(
    type: object,
    role: object,
    model: object,
    task_id: object,
    plan_id: object,
    sprint: object,
    input_bytes: object,
    output_bytes: object,
    duration_ms: object,
    decision: object,
    parent_invocation_id: object,
    cost_cents: object,
) -> dict:
    payload = {
        "type": _clean_text(type, "unknown") or "unknown",
        "role": _clean_text(role),
        "model": _clean_text(model),
        "task_id": _clean_text(task_id),
        "plan_id": _clean_text(plan_id),
        "sprint": _clean_text(sprint),
        "input_bytes": _to_int(input_bytes),
        "output_bytes": _to_int(output_bytes),
        "duration_ms": _to_int(duration_ms),
        "decision": _clean_text(decision),
        "parent_invocation_id": _to_int(parent_invocation_id),
        "cost_cents": _to_float(cost_cents),
    }
    payload["raw_meta"] = {
        key: payload[key]
        for key in ALLOWLIST
        if payload.get(key) is not None
    }
    return payload


def emit(payload_json: dict, db_path: str | Path | None) -> None:
    if not isinstance(payload_json, dict) or not db_path:
        return
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            helix_db.record_invocation(db_path, payload_json)
    except Exception:
        return


def _env_value(name: str) -> str | None:
    value = os.environ.get(f"{ENV_PREFIX}{name}")
    return value if value not in ("", None) else None


def _payload_from_env() -> tuple[dict, str]:
    payload = build_payload(
        _env_value("TYPE"),
        _env_value("ROLE"),
        _env_value("MODEL"),
        _env_value("TASK_ID"),
        _env_value("PLAN_ID"),
        _env_value("SPRINT"),
        _env_value("INPUT_BYTES"),
        _env_value("OUTPUT_BYTES"),
        _env_value("DURATION_MS"),
        _env_value("DECISION"),
        _env_value("PARENT_INVOCATION_ID"),
        _env_value("COST_CENTS"),
    )
    db_path = _env_value("DB_PATH") or helix_db.resolve_default_db_path()
    return payload, db_path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] != "emit-from-env":
        print("usage: invocation_helper.py emit-from-env", file=sys.stderr)
        return 1

    payload, db_path = _payload_from_env()
    emit(payload, db_path)
    print(json.dumps({"ok": True, "db_path": db_path, "payload": payload}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
