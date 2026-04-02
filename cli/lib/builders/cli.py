#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    import builders.agent_loop
    import builders.agent_pipeline
    import builders.agent_skill
    import builders.json_converter
    import builders.sub_agent
    import builders.task_builder
    import builders.verify_script
    import builders.workflow_builder

    from builders.history import BuilderHistory
    from builders.registry import BuilderRegistry
    from builders.store import BuilderStore
else:
    from . import agent_loop
    from . import agent_pipeline
    from . import agent_skill
    from . import json_converter
    from . import sub_agent
    from . import task_builder
    from . import verify_script
    from . import workflow_builder

    from .history import BuilderHistory
    from .registry import BuilderRegistry
    from .store import BuilderStore


EXCLUDE_MODULES = {"__init__", "base", "store", "history", "registry", "cli"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="helix-builder dispatcher")
    parser.add_argument("--project-root", required=True, help="project root path")
    parser.add_argument("--db", required=True, help="helix db path")

    parser.add_argument("target", help="list or builder type")
    parser.add_argument("action", nargs="?", help="schema/generate/validate/history")

    parser.add_argument("--input", dest="input_payload", help="input JSON text or file path")
    parser.add_argument("--seed", dest="seed_execution_id", help="seed execution id")
    parser.add_argument("--out", dest="output_path", help="output path for artifacts JSON")
    parser.add_argument("--artifact", dest="artifact_path", help="artifact JSON path")
    parser.add_argument("--task-id", default="", help="task id used by generate")
    parser.add_argument("--limit", type=int, default=5, help="history limit")
    return parser.parse_args()


def _auto_discover_builders():
    builders_dir = Path(__file__).resolve().parent
    for module_path in builders_dir.glob("*.py"):
        module_name = module_path.stem
        if module_name in EXCLUDE_MODULES:
            continue
        importlib.import_module(f"builders.{module_name}")


def _load_json_input(raw: str) -> Any:
    path = Path(raw)
    if path.exists() and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(raw)


def _print_json(payload: Any):
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _cmd_list():
    types = BuilderRegistry.list_types()
    print("Available builders:")
    if not types:
        print("  (none registered)")
        return
    for builder_type in types:
        print(f"  - {builder_type}")


def _cmd_schema(builder_type: str):
    builder_cls = BuilderRegistry.get(builder_type)
    schema = getattr(builder_cls, "INPUT_SCHEMA", {})
    _print_json(schema)


def _cmd_generate(
    store: BuilderStore,
    project_root: str,
    builder_type: str,
    input_payload: str,
    seed_execution_id: str | None,
    task_id: str,
    output_path: str | None,
):
    builder_cls = BuilderRegistry.get(builder_type)
    builder = builder_cls(store, project_root)
    params = _load_json_input(input_payload)
    if not isinstance(params, dict):
        raise ValueError("--input must be a JSON object")

    result = builder.build(
        task_id=task_id or f"{builder_type}-generate",
        input_params=params,
        seed_execution_id=seed_execution_id,
    )

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(result["artifacts"], ensure_ascii=False, indent=2), encoding="utf-8")
        result["output_path"] = str(out_file)

    _print_json(result)


def _cmd_validate(store: BuilderStore, project_root: str, builder_type: str, artifact_path: str):
    builder_cls = BuilderRegistry.get(builder_type)
    builder = builder_cls(store, project_root)

    payload = _load_json_input(artifact_path)
    artifacts: list[dict]
    if isinstance(payload, list):
        artifacts = payload
    elif isinstance(payload, dict):
        artifacts = [payload]
    else:
        raise ValueError("artifact must be JSON object or array")

    validation = builder.validate_output(artifacts)
    _print_json(validation)


def _cmd_history(store: BuilderStore, builder_type: str, limit: int, query_payload: str | None):
    query = {}
    if query_payload:
        loaded = _load_json_input(query_payload)
        if not isinstance(loaded, dict):
            raise ValueError("history query must be a JSON object")
        query = loaded

    history = BuilderHistory(store).search(builder_type=builder_type, query=query, limit=limit)
    _print_json(history)


def main() -> int:
    args = parse_args()
    _auto_discover_builders()

    if args.target == "list":
        if args.action:
            raise SystemExit("list command does not accept action")
        _cmd_list()
        return 0

    if not args.action:
        raise SystemExit("builder action is required")

    store = BuilderStore(args.db)
    builder_type = args.target

    if args.action == "schema":
        _cmd_schema(builder_type)
        return 0

    if args.action == "generate":
        if not args.input_payload:
            raise SystemExit("generate requires --input")
        _cmd_generate(
            store=store,
            project_root=args.project_root,
            builder_type=builder_type,
            input_payload=args.input_payload,
            seed_execution_id=args.seed_execution_id,
            task_id=args.task_id,
            output_path=args.output_path,
        )
        return 0

    if args.action == "validate":
        if not args.artifact_path:
            raise SystemExit("validate requires --artifact")
        _cmd_validate(
            store=store,
            project_root=args.project_root,
            builder_type=builder_type,
            artifact_path=args.artifact_path,
        )
        return 0

    if args.action == "history":
        _cmd_history(
            store=store,
            builder_type=builder_type,
            limit=args.limit,
            query_payload=args.input_payload,
        )
        return 0

    raise SystemExit(f"Unknown action: {args.action}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON input ({exc})", file=sys.stderr)
        raise SystemExit(1)
