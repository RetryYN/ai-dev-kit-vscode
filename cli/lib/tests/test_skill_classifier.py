from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import skill_classifier


def _template_file(tmp_path: Path) -> Path:
    path = tmp_path / "skill-classify-prompt.md"
    path.write_text(
        "\n".join(
            [
                "id={{skill_id}}",
                "phases={{allowed_phases}}",
                "agents={{allowed_agents}}",
                "tasks={{known_task_ids}}",
                "body={{skill_md_content}}",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _ok_payload() -> str:
    return (
        '{"phases":["L2"],"tasks":["design-api"],"triggers":["API","設計","契約"],'
        '"anti_triggers":[],"agent":"tl","similar":[],"confidence":0.9}'
    )


def test_classify_skill_returns_expected_dict_with_plain_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)

    def _fake_run(cmd, capture_output, text, timeout, check):
        assert cmd[1:3] == ["--role", "classifier"]
        prompt = cmd[4]
        assert "id=common/security" in prompt
        assert "phases=L2" in prompt
        assert "agents=tl" in prompt
        assert "tasks=design-api" in prompt
        assert "body=# SKILL" in prompt
        return subprocess.CompletedProcess(cmd, 0, stdout=_ok_payload(), stderr="")

    monkeypatch.setattr(skill_classifier.subprocess, "run", _fake_run)

    result = skill_classifier.classify_skill(
        "common/security",
        "# SKILL",
        known_task_ids={"design-api"},
        allowed_agents={"tl"},
        allowed_phases={"L2"},
        template_path=tpl,
        helix_codex_path="helix-codex",
    )

    assert result == {
        "phases": ["L2"],
        "tasks": ["design-api"],
        "triggers": ["API", "設計", "契約"],
        "anti_triggers": [],
        "agent": "tl",
        "similar": [],
        "confidence": 0.9,
    }


def test_classify_skill_extracts_from_fenced_json_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)

    stdout = "前置き\n```json\n" + _ok_payload() + "\n```\n後置き"

    monkeypatch.setattr(
        skill_classifier.subprocess,
        "run",
        lambda cmd, capture_output, text, timeout, check: subprocess.CompletedProcess(
            cmd, 0, stdout=stdout, stderr=""
        ),
    )

    result = skill_classifier.classify_skill(
        "common/security",
        "# SKILL",
        known_task_ids={"design-api"},
        allowed_agents={"tl"},
        allowed_phases={"L2"},
        template_path=tpl,
        helix_codex_path="helix-codex",
    )
    assert result["agent"] == "tl"


def test_classify_skill_retries_after_invalid_json_then_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)
    calls = {"n": 0}

    def _fake_run(cmd, capture_output, text, timeout, check):
        calls["n"] += 1
        if calls["n"] == 1:
            return subprocess.CompletedProcess(cmd, 0, stdout="not-json", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout=_ok_payload(), stderr="")

    monkeypatch.setattr(skill_classifier.subprocess, "run", _fake_run)

    result = skill_classifier.classify_skill(
        "common/security",
        "# SKILL",
        known_task_ids={"design-api"},
        allowed_agents={"tl"},
        allowed_phases={"L2"},
        template_path=tpl,
        helix_codex_path="helix-codex",
    )

    assert calls["n"] == 2
    assert result["tasks"] == ["design-api"]


def test_classify_skill_raises_code8_after_three_validation_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)
    bad_agent = (
        '{"phases":["L2"],"tasks":["design-api"],"triggers":[],"anti_triggers":[],'
        '"agent":"security","similar":[],"confidence":0.7}'
    )
    calls = {"n": 0}

    def _fake_run(cmd, capture_output, text, timeout, check):
        calls["n"] += 1
        return subprocess.CompletedProcess(cmd, 0, stdout=bad_agent, stderr="")

    monkeypatch.setattr(skill_classifier.subprocess, "run", _fake_run)

    with pytest.raises(skill_classifier.ClassifierError) as exc:
        skill_classifier.classify_skill(
            "common/security",
            "# SKILL",
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
            template_path=tpl,
            helix_codex_path="helix-codex",
        )

    assert exc.value.code == 8
    assert calls["n"] == skill_classifier.CLASSIFIER_RETRY_COUNT


def test_classify_skill_raises_code7_on_subprocess_network_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)
    calls = {"n": 0}

    def _fake_run(cmd, capture_output, text, timeout, check):
        calls["n"] += 1
        return subprocess.CompletedProcess(cmd, 7, stdout="", stderr="network")

    monkeypatch.setattr(skill_classifier.subprocess, "run", _fake_run)

    with pytest.raises(skill_classifier.ClassifierError) as exc:
        skill_classifier.classify_skill(
            "common/security",
            "# SKILL",
            known_task_ids={"design-api"},
            template_path=tpl,
            helix_codex_path="helix-codex",
        )

    assert exc.value.code == 7
    assert calls["n"] == 1


def test_classify_skill_retries_on_invalid_phase_value(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)
    bad_phase = (
        '{"phases":["L9"],"tasks":["design-api"],"triggers":[],"anti_triggers":[],'
        '"agent":"tl","similar":[],"confidence":0.7}'
    )
    calls = {"n": 0}

    monkeypatch.setattr(
        skill_classifier.subprocess,
        "run",
        lambda cmd, capture_output, text, timeout, check: (
            calls.__setitem__("n", calls["n"] + 1)
            or subprocess.CompletedProcess(cmd, 0, stdout=bad_phase, stderr="")
        ),
    )

    with pytest.raises(skill_classifier.ClassifierError) as exc:
        skill_classifier.classify_skill(
            "common/security",
            "# SKILL",
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
            template_path=tpl,
            helix_codex_path="helix-codex",
        )

    assert exc.value.code == 8
    assert calls["n"] == skill_classifier.CLASSIFIER_RETRY_COUNT


def test_classify_skill_retries_on_unknown_task_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tpl = _template_file(tmp_path)
    unknown_task = (
        '{"phases":["L2"],"tasks":["unknown-task"],"triggers":[],"anti_triggers":[],'
        '"agent":"tl","similar":[],"confidence":0.7}'
    )
    calls = {"n": 0}

    def _fake_run(cmd, capture_output, text, timeout, check):
        calls["n"] += 1
        return subprocess.CompletedProcess(cmd, 0, stdout=unknown_task, stderr="")

    monkeypatch.setattr(skill_classifier.subprocess, "run", _fake_run)

    with pytest.raises(skill_classifier.ClassifierError) as exc:
        skill_classifier.classify_skill(
            "common/security",
            "# SKILL",
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
            template_path=tpl,
            helix_codex_path="helix-codex",
        )

    assert exc.value.code == 8
    assert calls["n"] == skill_classifier.CLASSIFIER_RETRY_COUNT


def test_render_prompt_replaces_template_variables() -> None:
    template = "A={{skill_id}} B={{allowed_agents}} C={{missing}}"
    rendered = skill_classifier._render_prompt(
        template,
        {"skill_id": "common/security", "allowed_agents": "tl,se"},
    )

    assert rendered == "A=common/security B=tl,se C={{missing}}"


def test_extract_json_block_handles_surrounding_text() -> None:
    text = "説明文\nJSONはこちら: {\"phases\":[\"L2\"],\"tasks\":[\"design-api\"],\"triggers\":[],\"anti_triggers\":[],\"agent\":\"tl\",\"similar\":[],\"confidence\":0.5}\n補足"
    extracted = skill_classifier._extract_json_block(text)

    assert extracted is not None
    assert extracted["agent"] == "tl"


def test_validate_classification_checks_phase_task_and_agent() -> None:
    payload = {
        "phases": ["L2"],
        "tasks": ["design-api"],
        "triggers": [],
        "anti_triggers": [],
        "agent": "tl",
        "similar": [],
        "confidence": 0.4,
    }

    ok = skill_classifier._validate_classification(
        payload,
        known_task_ids={"design-api"},
        allowed_agents={"tl"},
        allowed_phases={"L2"},
    )
    assert ok["agent"] == "tl"

    with pytest.raises(skill_classifier.JsonlSchemaError):
        skill_classifier._validate_classification(
            {**payload, "phases": ["L9"]},
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
        )

    with pytest.raises(skill_classifier.JsonlSchemaError):
        skill_classifier._validate_classification(
            {**payload, "tasks": ["unknown-task"]},
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
        )

    with pytest.raises(skill_classifier.JsonlSchemaError):
        skill_classifier._validate_classification(
            {**payload, "agent": "security"},
            known_task_ids={"design-api"},
            allowed_agents={"tl"},
            allowed_phases={"L2"},
        )
