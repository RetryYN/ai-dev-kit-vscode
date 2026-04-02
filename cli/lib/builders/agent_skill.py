from __future__ import annotations

import re
from pathlib import Path

from .base import BuilderBase
from .registry import BuilderRegistry


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
_ALLOWED_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "R0", "R1", "R2", "R3", "R4", "RGC"}


class AgentSkillBuilder(BuilderBase):
    BUILDER_TYPE = "agent-skill"

    INPUT_SCHEMA = {
        "type": "object",
        "required": ["name", "description", "helix_layer", "triggers", "verification", "sections"],
    }

    def validate_input(self, params: dict) -> dict:
        if not isinstance(params, dict):
            raise ValueError("input must be an object")

        name = str(params.get("name", "")).strip()
        description = str(params.get("description", "")).strip()
        helix_layer = str(params.get("helix_layer", "")).strip()
        triggers = params.get("triggers")
        verification = params.get("verification")
        sections = params.get("sections")

        if not name or not _NAME_RE.match(name):
            raise ValueError("name must match ^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
        if not description:
            raise ValueError("description is required")
        if helix_layer not in _ALLOWED_LAYERS:
            raise ValueError(f"helix_layer must be one of {sorted(_ALLOWED_LAYERS)}")
        if not isinstance(triggers, list) or not triggers:
            raise ValueError("triggers must be a non-empty array")
        if not isinstance(verification, list) or not verification:
            raise ValueError("verification must be a non-empty array")
        if not isinstance(sections, dict) or not sections:
            raise ValueError("sections must be a non-empty object")

        norm_triggers = [str(item).strip() for item in triggers if str(item).strip()]
        norm_verification = [str(item).strip() for item in verification if str(item).strip()]
        if not norm_triggers:
            raise ValueError("triggers must include at least one non-empty item")
        if not norm_verification:
            raise ValueError("verification must include at least one non-empty item")

        return {
            "name": name,
            "description": description,
            "helix_layer": helix_layer,
            "triggers": norm_triggers,
            "verification": norm_verification,
            "sections": sections,
        }

    def generate(self, params: dict, seed: dict | None) -> list[dict]:
        del seed

        content = _render_skill_markdown(params)
        artifacts = []

        # HELIX 独自パス（skills/generated/）
        helix_dir = Path(self.project_root) / "skills" / "generated" / params["name"]
        helix_dir.mkdir(parents=True, exist_ok=True)
        helix_path = helix_dir / "SKILL.md"
        helix_path.write_text(content, encoding="utf-8")
        artifacts.append({"path": str(helix_path.relative_to(self.project_root)), "kind": "generated-skill"})

        # Claude Code 公式パス（.claude/skills/）— /skillname で即呼べる
        claude_dir = Path(self.project_root) / ".claude" / "skills" / params["name"]
        claude_dir.mkdir(parents=True, exist_ok=True)
        claude_path = claude_dir / "SKILL.md"
        claude_path.write_text(content, encoding="utf-8")
        artifacts.append({"path": str(claude_path.relative_to(self.project_root)), "kind": "claude-skill"})

        return artifacts

    def validate_output(self, artifacts: list[dict]) -> dict:
        paths = [_artifact_path(self.project_root, artifact) for artifact in artifacts]
        if not paths:
            raise ValueError("agent-skill expects at least one artifact")

        skill_path = paths[0]
        if not skill_path.exists():
            raise ValueError(f"artifact not found: {skill_path}")

        text = skill_path.read_text(encoding="utf-8")
        frontmatter = _extract_frontmatter(text)
        parsed = _parse_simple_yaml(frontmatter)

        if not isinstance(parsed, dict):
            raise ValueError("frontmatter must be an object")

        metadata = parsed.get("metadata")
        compatibility = parsed.get("compatibility")
        if not isinstance(metadata, dict):
            raise ValueError("frontmatter metadata is required")
        if not isinstance(compatibility, dict):
            raise ValueError("frontmatter compatibility is required")

        for key in ("name", "description"):
            if key not in parsed:
                raise ValueError(f"frontmatter missing key: {key}")
        for key in ("helix_layer", "triggers", "verification"):
            if key not in metadata:
                raise ValueError(f"frontmatter metadata missing key: {key}")
        for key in ("claude", "codex"):
            if key not in compatibility:
                raise ValueError(f"frontmatter compatibility missing key: {key}")

        return {
            "valid": True,
            "checked_files": [str(skill_path)],
            "quality_score": 100,
        }


def _render_skill_markdown(params: dict) -> str:
    lines = [
        "---",
        f"name: {params['name']}",
        f"description: \"{_yaml_escape(params['description'])}\"",
        "metadata:",
        f"  helix_layer: {params['helix_layer']}",
        "  triggers:",
    ]

    for trigger in params["triggers"]:
        lines.append(f"    - \"{_yaml_escape(trigger)}\"")

    lines.append("  verification:")
    for item in params["verification"]:
        lines.append(f"    - \"{_yaml_escape(item)}\"")

    lines.extend(
        [
            "compatibility:",
            "  claude: true",
            "  codex: true",
            "---",
            "",
            f"# {params['name']}",
            "",
        ]
    )

    for section_name, section_content in params["sections"].items():
        heading = str(section_name).strip() or "section"
        lines.append(f"## {heading}")

        if isinstance(section_content, list):
            for item in section_content:
                lines.append(f"- {str(item)}")
        elif isinstance(section_content, dict):
            for key, value in section_content.items():
                lines.append(f"- **{key}**: {value}")
        else:
            lines.append(str(section_content))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _extract_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")

    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("YAML frontmatter closing delimiter is missing")

    return text[4:end]


def _parse_simple_yaml(text: str):
    lines = text.splitlines()
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]

    def next_non_empty_line(start: int) -> tuple[int, str] | None:
        for idx in range(start, len(lines)):
            candidate = lines[idx]
            if candidate.strip() and not candidate.lstrip().startswith("#"):
                return idx, candidate
        return None

    for index, raw in enumerate(lines):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        indent = len(raw) - len(raw.lstrip(" "))
        stripped = raw.strip()

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        container = stack[-1][1]

        if stripped.startswith("- "):
            if not isinstance(container, list):
                raise ValueError("invalid YAML list indentation")
            container.append(_parse_scalar(stripped[2:].strip()))
            continue

        if ":" not in stripped:
            raise ValueError(f"invalid YAML line: {raw}")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if not isinstance(container, dict):
            raise ValueError("invalid YAML structure")

        if value:
            container[key] = _parse_scalar(value)
            continue

        upcoming = next_non_empty_line(index + 1)
        if upcoming is None:
            container[key] = {}
            continue

        next_indent = len(upcoming[1]) - len(upcoming[1].lstrip(" "))
        next_stripped = upcoming[1].strip()
        if next_indent <= indent:
            container[key] = {}
            continue

        if next_stripped.startswith("- "):
            child: object = []
        else:
            child = {}

        container[key] = child
        stack.append((indent, child))

    return root


def _parse_scalar(value: str):
    text = value.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]

    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~", "none"}:
        return None

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    return text


def _yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _artifact_path(project_root: str, artifact: dict) -> Path:
    path_value = artifact.get("path") if isinstance(artifact, dict) else None
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("artifact.path is required")

    path = Path(path_value)
    if not path.is_absolute():
        path = Path(project_root) / path
    return path


BuilderRegistry.register(AgentSkillBuilder)
