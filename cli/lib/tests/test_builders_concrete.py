"""Concrete builder and builder CLI tests."""

from __future__ import annotations

import argparse
import copy
import json
import py_compile
import sys
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from builders import cli as builders_cli
from builders.agent_loop import AgentLoopBuilder
from builders.agent_pipeline import AgentPipelineBuilder
from builders.agent_skill import AgentSkillBuilder
from builders.base import BuilderBase
from builders.json_converter import JsonConverterBuilder
from builders.registry import BuilderRegistry
from builders.store import BuilderStore
from builders.sub_agent import SubAgentBuilder
from builders.task_builder import TaskBuilder
from builders.verify_script import VerifyScriptBuilder
from builders.workflow_builder import WorkflowBuilder


def _db_path(tmp_path: Path) -> str:
    return str(tmp_path / "builders.db")


def _store(tmp_path: Path) -> BuilderStore:
    return BuilderStore(_db_path(tmp_path))


def _artifact_path(project_root: Path, artifact: dict) -> Path:
    return project_root / artifact["path"]


def _first_artifact(project_root: Path, artifacts: list[dict]) -> Path:
    return _artifact_path(project_root, artifacts[0])


def _find_artifact(project_root: Path, artifacts: list[dict], kind: str) -> Path:
    for artifact in artifacts:
        if artifact.get("kind") == kind:
            return _artifact_path(project_root, artifact)
    raise AssertionError(f"artifact not found: {kind}")


def _agent_loop_params() -> dict:
    return {
        "name": "qa-loop",
        "role": "qa",
        "task_template": "verify {task}",
        "stop_condition": {"type": "count", "value": 2},
        "max_iterations": 2,
        "on_failure": "retry",
    }


def _agent_pipeline_params() -> dict:
    return {
        "name": "qa-pipeline",
        "stages": [
            {
                "name": "collect",
                "builder": "task",
                "exports": {"payload": "string"},
            },
            {
                "name": "verify",
                "builder": "verify-script",
                "consumes": {"payload": "string"},
            },
        ],
        "error_handling": "retry_stage",
    }


def _agent_skill_params() -> dict:
    return {
        "name": "qa-skill",
        "description": "Builder QA coverage",
        "helix_layer": "L6",
        "triggers": ["test creation"],
        "verification": ["pytest passes"],
        "sections": {
            "Overview": "Used for QA checks.",
            "Checklist": ["happy path", "error path"],
        },
    }


def _sub_agent_params() -> dict:
    return {
        "name": "qa-sub-agent",
        "role": "qa",
        "task_template": "inspect {target}",
        "context_files": ["cli/lib/tests/*.py", "skills/**/*.md"],
        "output_contract": {"summary": "string", "score": "number"},
        "execution": "helix-codex",
    }


def _workflow_params() -> dict:
    return {
        "name": "qa-workflow",
        "nodes": [
            {"id": "prepare", "builder": "task"},
            {"id": "verify", "builder": "verify-script"},
        ],
        "edges": [{"from": "prepare", "to": "verify", "condition": "success"}],
        "failure_policy": "stop_on_first",
    }


def _task_params() -> dict:
    return {
        "category": "qa",
        "task_id": "gap020-builder-tests",
        "name": "Add concrete builder tests",
        "role": "qa",
        "estimate": 2,
        "skill": "testing",
        "actions": [{"type": "test", "desc": "add unit tests"}],
    }


def _verify_script_params() -> dict:
    return {
        "id": "GAP020",
        "slug": "builder-checks",
        "checks": [{"desc": "python works", "cmd": "python3 -c 'print(1)'"}],
        "setup": "touch ready",
        "teardown": "rm -f ready",
    }


def _json_converter_params() -> dict:
    return {
        "name": "qa-converter",
        "source_schema": {"id": "string", "count": "integer"},
        "target_schema": {"id": "string", "total": "integer"},
        "mapping_hints": {"count -> total": "copy count to total"},
    }


def _load_artifact_json(project_root: Path, artifacts: list[dict], kind: str | None = None) -> dict:
    path = _find_artifact(project_root, artifacts, kind) if kind else _first_artifact(project_root, artifacts)
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_agent_loop_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    payload = _load_artifact_json(project_root, artifacts)
    assert payload["name"] == params["name"]
    assert payload["builder_type"] == "agent-loop"
    assert payload["stop_condition"] == params["stop_condition"]


def _assert_agent_pipeline_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    payload = _load_artifact_json(project_root, artifacts)
    assert payload["name"] == params["name"]
    assert payload["builder_type"] == "agent-pipeline"
    assert payload["contract_checks"]["issues"] == []


def _assert_agent_skill_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    generated = _find_artifact(project_root, artifacts, "generated-skill")
    claude = _find_artifact(project_root, artifacts, "claude-skill")
    generated_text = generated.read_text(encoding="utf-8")
    claude_text = claude.read_text(encoding="utf-8")
    assert generated_text == claude_text
    assert f"name: {params['name']}" in generated_text
    assert f"# {params['name']}" in generated_text


def _assert_sub_agent_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    payload = _load_artifact_json(project_root, artifacts)
    assert payload["builder_type"] == "sub-agent"
    assert payload["execution_template"]["tool"] == "helix-codex"
    assert params["task_template"] in payload["execution_template"]["command"]


def _assert_workflow_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    payload = _load_artifact_json(project_root, artifacts)
    assert payload["name"] == params["name"]
    assert payload["builder_type"] == "workflow"
    assert payload["edges"] == params["edges"]


def _assert_task_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    path = _first_artifact(project_root, artifacts)
    text = path.read_text(encoding="utf-8")
    assert f"{params['category']}:" in text
    assert f"  {params['task_id']}:" in text
    assert '    actions:' in text


def _assert_verify_script_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    path = _first_artifact(project_root, artifacts)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/bash\nset -euo pipefail")
    assert f"SETUP_CMD='{params['setup']}'" in text
    assert "run_check 'python works'" in text
    assert path.stat().st_mode & 0o111


def _assert_json_converter_generated(project_root: Path, artifacts: list[dict], params: dict) -> None:
    definition = _load_artifact_json(project_root, artifacts, "json-converter-definition")
    script = _find_artifact(project_root, artifacts, "json-converter-script")
    assert definition["builder_type"] == "json-converter"
    assert definition["rules"][0]["strategy"] == "direct"
    assert definition["rules"][1]["strategy"] == "hint"
    assert "def map_count_to_total" in script.read_text(encoding="utf-8")


def _make_agent_loop_generate_invalid(params: dict) -> dict:
    params["stop_condition"] = object()
    return params


def _make_agent_pipeline_generate_invalid(params: dict) -> dict:
    params["stages"] = [object()]
    return params


def _make_agent_skill_generate_invalid(params: dict) -> dict:
    params["sections"] = []
    return params


def _make_sub_agent_generate_invalid(params: dict) -> dict:
    params["output_contract"] = object()
    return params


def _make_workflow_generate_invalid(params: dict) -> dict:
    params["nodes"] = object()
    return params


def _make_task_generate_invalid(params: dict) -> dict:
    params["actions"] = [None]
    return params


def _make_verify_script_generate_invalid(params: dict) -> dict:
    params["checks"] = [None]
    return params


def _make_json_converter_generate_invalid(params: dict) -> dict:
    params["target_schema"] = {"bad": object()}
    return params


def _corrupt_agent_loop(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("name")
    path.write_text(json.dumps(payload), encoding="utf-8")


def _corrupt_agent_pipeline(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["stages"] = []
    path.write_text(json.dumps(payload), encoding="utf-8")


def _corrupt_agent_skill(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("compatibility:\n", "compatibility_removed:\n", 1), encoding="utf-8")


def _corrupt_sub_agent(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["execution"] = "unknown-runner"
    path.write_text(json.dumps(payload), encoding="utf-8")


def _corrupt_workflow(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["edges"] = [
        {"from": "prepare", "to": "verify", "condition": "success"},
        {"from": "verify", "to": "prepare", "condition": "success"},
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")


def _corrupt_task_builder(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("    actions:\n", "", 1), encoding="utf-8")


def _corrupt_verify_script(project_root: Path, artifacts: list[dict]) -> None:
    path = _first_artifact(project_root, artifacts)
    path.write_text("#!/bin/bash\nif then\n", encoding="utf-8")


def _corrupt_json_converter(project_root: Path, artifacts: list[dict]) -> None:
    path = _find_artifact(project_root, artifacts, "json-converter-script")
    path.write_text("def broken(:\n", encoding="utf-8")


BUILDER_SPECS = {
    "agent-loop": {
        "cls": AgentLoopBuilder,
        "params": _agent_loop_params,
        "missing_key": "name",
        "assert_generated": _assert_agent_loop_generated,
        "make_invalid_generate": _make_agent_loop_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_agent_loop,
        "validate_error": ValueError,
    },
    "agent-pipeline": {
        "cls": AgentPipelineBuilder,
        "params": _agent_pipeline_params,
        "missing_key": "name",
        "assert_generated": _assert_agent_pipeline_generated,
        "make_invalid_generate": _make_agent_pipeline_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_agent_pipeline,
        "validate_error": ValueError,
    },
    "agent-skill": {
        "cls": AgentSkillBuilder,
        "params": _agent_skill_params,
        "missing_key": "name",
        "assert_generated": _assert_agent_skill_generated,
        "make_invalid_generate": _make_agent_skill_generate_invalid,
        "generate_error": AttributeError,
        "corrupt": _corrupt_agent_skill,
        "validate_error": ValueError,
    },
    "sub-agent": {
        "cls": SubAgentBuilder,
        "params": _sub_agent_params,
        "missing_key": "execution",
        "assert_generated": _assert_sub_agent_generated,
        "make_invalid_generate": _make_sub_agent_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_sub_agent,
        "validate_error": ValueError,
    },
    "workflow": {
        "cls": WorkflowBuilder,
        "params": _workflow_params,
        "missing_key": "name",
        "assert_generated": _assert_workflow_generated,
        "make_invalid_generate": _make_workflow_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_workflow,
        "validate_error": ValueError,
    },
    "task": {
        "cls": TaskBuilder,
        "params": _task_params,
        "missing_key": "task_id",
        "assert_generated": _assert_task_generated,
        "make_invalid_generate": _make_task_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_task_builder,
        "validate_error": ValueError,
    },
    "verify-script": {
        "cls": VerifyScriptBuilder,
        "params": _verify_script_params,
        "missing_key": "id",
        "assert_generated": _assert_verify_script_generated,
        "make_invalid_generate": _make_verify_script_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_verify_script,
        "validate_error": ValueError,
    },
    "json-converter": {
        "cls": JsonConverterBuilder,
        "params": _json_converter_params,
        "missing_key": "name",
        "assert_generated": _assert_json_converter_generated,
        "make_invalid_generate": _make_json_converter_generate_invalid,
        "generate_error": TypeError,
        "corrupt": _corrupt_json_converter,
        "validate_error": py_compile.PyCompileError,
    },
}


@pytest.fixture(autouse=True)
def _registered_builders() -> None:
    BuilderRegistry._builders = {}
    for spec in BUILDER_SPECS.values():
        BuilderRegistry.register(spec["cls"])


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_concrete_builders_inherit_builder_base(builder_type: str) -> None:
    assert issubclass(BUILDER_SPECS[builder_type]["cls"], BuilderBase)


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_build_completes_and_records_execution(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))

    result = builder.build(
        task_id=f"{builder_type}-task",
        input_params=spec["params"](),
    )

    execution = builder.store.get_execution(result["execution_id"])
    assert execution["builder_type"] == builder.BUILDER_TYPE
    assert execution["status"] == "completed"
    assert execution["step_count"] == 3
    assert [step["name"] for step in execution["step_trace"]] == [
        "validate_input",
        "generate",
        "validate_output",
    ]
    assert execution["quality_score"] == 100.0
    assert result["artifacts"]


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_generate_creates_expected_artifacts(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))

    artifacts = builder.generate(spec["params"](), None)

    assert artifacts
    for artifact in artifacts:
        path = _artifact_path(tmp_path, artifact)
        assert path.exists()
        assert artifact["kind"]


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_generate_writes_expected_builder_content(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    params = spec["params"]()

    artifacts = builder.generate(params, None)

    spec["assert_generated"](tmp_path, artifacts, params)


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_generate_rejects_missing_required_key(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    params = copy.deepcopy(spec["params"]())
    params.pop(spec["missing_key"])

    with pytest.raises((KeyError, ValueError, TypeError)):
        builder.generate(params, None)


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_generate_rejects_invalid_runtime_shape(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    params = spec["make_invalid_generate"](copy.deepcopy(spec["params"]()))

    with pytest.raises(spec["generate_error"]):
        builder.generate(params, None)


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_validate_output_accepts_generated_artifacts(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    artifacts = builder.generate(spec["params"](), None)

    validation = builder.validate_output(artifacts)

    assert validation["valid"] is True
    assert validation["quality_score"] == 100
    assert validation["checked_files"]


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_validate_output_accepts_absolute_artifact_paths(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    artifacts = builder.generate(spec["params"](), None)
    absolute_artifacts = [{**artifact, "path": str(_artifact_path(tmp_path, artifact))} for artifact in artifacts]

    validation = builder.validate_output(absolute_artifacts)

    assert validation["valid"] is True
    assert validation["quality_score"] == 100


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_validate_output_rejects_corrupted_artifacts(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    artifacts = builder.generate(spec["params"](), None)
    spec["corrupt"](tmp_path, artifacts)

    with pytest.raises(spec["validate_error"]):
        builder.validate_output(artifacts)


@pytest.mark.parametrize("builder_type", list(BUILDER_SPECS))
def test_validate_output_rejects_missing_artifact_file(builder_type: str, tmp_path: Path) -> None:
    spec = BUILDER_SPECS[builder_type]
    builder = spec["cls"](_store(tmp_path), str(tmp_path))
    artifacts = builder.generate(spec["params"](), None)
    _artifact_path(tmp_path, artifacts[0]).unlink()

    with pytest.raises(ValueError, match="not found"):
        builder.validate_output(artifacts)


def test_cli_generate_writes_artifact_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path)
    output_path = tmp_path / "artifacts.json"

    builders_cli._cmd_generate(
        store=store,
        project_root=str(tmp_path),
        builder_type="agent-loop",
        input_payload=json.dumps(_agent_loop_params()),
        seed_execution_id=None,
        task_id="cli-generate",
        output_path=str(output_path),
    )

    payload = json.loads(capsys.readouterr().out)
    saved = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["execution_id"].startswith("be-")
    assert saved == payload["artifacts"]


def test_cli_generate_rejects_non_object_input(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="JSON object"):
        builders_cli._cmd_generate(
            store=store,
            project_root=str(tmp_path),
            builder_type="agent-loop",
            input_payload=json.dumps(["not-an-object"]),
            seed_execution_id=None,
            task_id="cli-generate",
            output_path=None,
        )


def test_cli_validate_prints_validation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path)
    builder = AgentLoopBuilder(store, str(tmp_path))
    artifacts = builder.generate(_agent_loop_params(), None)
    artifact_file = tmp_path / "artifact.json"
    artifact_file.write_text(json.dumps(artifacts), encoding="utf-8")

    builders_cli._cmd_validate(
        store=store,
        project_root=str(tmp_path),
        builder_type="agent-loop",
        artifact_path=str(artifact_file),
    )

    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["quality_score"] == 100


def test_cli_validate_rejects_invalid_artifact_payload(tmp_path: Path) -> None:
    store = _store(tmp_path)
    artifact_file = tmp_path / "artifact.json"
    artifact_file.write_text(json.dumps("bad-artifact"), encoding="utf-8")

    with pytest.raises(ValueError, match="artifact must be JSON object or array"):
        builders_cli._cmd_validate(
            store=store,
            project_root=str(tmp_path),
            builder_type="agent-loop",
            artifact_path=str(artifact_file),
        )


def test_cli_list_prints_registered_builders(capsys: pytest.CaptureFixture[str]) -> None:
    builders_cli._cmd_list()

    output = capsys.readouterr().out
    assert "Available builders:" in output
    assert "agent-loop" in output
    assert "workflow" in output


def test_cli_schema_prints_builder_schema(capsys: pytest.CaptureFixture[str]) -> None:
    builders_cli._cmd_schema("agent-loop")

    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "object"
    assert "max_iterations" in payload["required"]


def test_cli_history_prints_results(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path)
    builder = AgentLoopBuilder(store, str(tmp_path))
    builder.build(task_id="history-agent-loop", input_params=_agent_loop_params())

    builders_cli._cmd_history(
        store=store,
        builder_type="agent-loop",
        limit=3,
        query_payload=json.dumps({"pattern_tags": []}),
    )

    payload = json.loads(capsys.readouterr().out)
    assert len(payload) == 1
    assert payload[0]["builder_type"] == "agent-loop"
    assert "_score" in payload[0]


def test_cli_history_rejects_non_object_query(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(ValueError, match="history query must be a JSON object"):
        builders_cli._cmd_history(
            store=store,
            builder_type="agent-loop",
            limit=3,
            query_payload=json.dumps(["bad-query"]),
        )


def test_cli_load_json_input_supports_file_path(tmp_path: Path) -> None:
    payload = {"name": "from-file", "count": 2}
    payload_file = tmp_path / "payload.json"
    payload_file.write_text(json.dumps(payload), encoding="utf-8")

    loaded = builders_cli._load_json_input(str(payload_file))

    assert loaded == payload


def test_cli_main_list_command_returns_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        builders_cli,
        "parse_args",
        lambda: argparse.Namespace(
            project_root="unused",
            db="unused",
            target="list",
            action=None,
            input_payload=None,
            seed_execution_id=None,
            output_path=None,
            artifact_path=None,
            task_id="",
            limit=5,
        ),
    )
    called = {"auto_discover": False, "list": False}

    def fake_auto_discover() -> None:
        called["auto_discover"] = True

    def fake_list() -> None:
        called["list"] = True

    monkeypatch.setattr(builders_cli, "_auto_discover_builders", fake_auto_discover)
    monkeypatch.setattr(builders_cli, "_cmd_list", fake_list)

    result = builders_cli.main()

    assert result == 0
    assert called == {"auto_discover": True, "list": True}


def test_cli_main_requires_action(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        builders_cli,
        "parse_args",
        lambda: argparse.Namespace(
            project_root="unused",
            db="unused",
            target="agent-loop",
            action=None,
            input_payload=None,
            seed_execution_id=None,
            output_path=None,
            artifact_path=None,
            task_id="",
            limit=5,
        ),
    )
    monkeypatch.setattr(builders_cli, "_auto_discover_builders", lambda: None)

    with pytest.raises(SystemExit, match="builder action is required"):
        builders_cli.main()
