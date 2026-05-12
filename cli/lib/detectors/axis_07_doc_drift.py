from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

import helix_db

from .base import BaseDetector, DetectorResult

try:
    from ..yaml_parser import parse_yaml  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script execution
    from yaml_parser import parse_yaml  # type: ignore


MODEL_RE = re.compile(r"\b(?:gpt|claude)[A-Za-z0-9._-]*\b")
PHASE_RE = re.compile(r"\b(?:G\d+(?:\.\d+)?|L\d+(?:\.\d+)?|R\d+|RGC)\b")


def _project_root(db_path: str | Path) -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root)
    target = Path(db_path).resolve()
    if target.parent.name == ".helix":
        return target.parent.parent
    return Path.cwd()


def _read_text(root: Path, rel_path: str) -> str | None:
    path = root / rel_path
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _load_models(models_text: str) -> set[str]:
    try:
        parsed = parse_yaml(models_text)
    except Exception:
        return set()

    models: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                visit(value)
            return
        if isinstance(node, list):
            for value in node:
                visit(value)
            return
        if isinstance(node, str) and MODEL_RE.fullmatch(node.strip()):
            models.add(node.strip())
        if isinstance(node, str):
            for match in MODEL_RE.finditer(node):
                models.add(match.group(0))

    visit(parsed)
    return models


def _load_roles(role_map_text: str) -> set[str]:
    roles: set[str] = set()
    for raw_line in role_map_text.splitlines():
        line = raw_line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        if not first:
            continue
        if first in {"ロール", "role"}:
            continue
        if re.fullmatch(r"[a-z0-9-]+", first):
            roles.add(first)
    return roles


def _extract_role_mentions(skill_map_text: str, canonical_roles: set[str]) -> set[str]:
    allowed = set(canonical_roles)
    allowed.add("pe")
    tokens = {token.lower() for token in re.findall(r"\b[a-z][a-z0-9-]*\b", skill_map_text.lower())}
    return {token for token in tokens if token in allowed}


def _load_phase_tokens(core_text: str) -> set[str]:
    return {token.upper() for token in PHASE_RE.findall(core_text)}


def _extract_phase_mentions(*texts: str) -> set[str]:
    tokens: set[str] = set()
    for text in texts:
        tokens.update(token.upper() for token in PHASE_RE.findall(text))
    return tokens


class Axis07DocDrift(BaseDetector):
    id = "axis-07"
    name = "doc expression drift"
    phase_gate = "G2"
    kind = "detector"

    def run(self, db_path: str | Path) -> DetectorResult:
        started = time.perf_counter()
        root = _project_root(db_path)

        required = {
            "CLAUDE.md": _read_text(root, "CLAUDE.md"),
            "AGENTS.md": _read_text(root, "AGENTS.md"),
            "skills/SKILL_MAP.md": _read_text(root, "skills/SKILL_MAP.md"),
            "cli/config/models.yaml": _read_text(root, "cli/config/models.yaml"),
            "helix/HELIX_CORE.md": _read_text(root, "helix/HELIX_CORE.md"),
            "cli/ROLE_MAP.md": _read_text(root, "cli/ROLE_MAP.md"),
        }
        missing = [path for path, text in required.items() if text is None]
        if missing:
            cost_ms = max(1, int((time.perf_counter() - started) * 1000))
            return DetectorResult(
                verdict="blocked",
                findings=[],
                cost_ms=cost_ms,
                raw={"reason": "missing required doc inputs", "missing": missing, "project_root": str(root)},
            )

        claude_text = required["CLAUDE.md"] or ""
        agents_text = required["AGENTS.md"] or ""
        skill_map_text = required["skills/SKILL_MAP.md"] or ""
        models_text = required["cli/config/models.yaml"] or ""
        core_text = required["helix/HELIX_CORE.md"] or ""
        role_map_text = required["cli/ROLE_MAP.md"] or ""

        canonical_models = _load_models(models_text)
        canonical_roles = _load_roles(role_map_text)
        canonical_phases = _load_phase_tokens(core_text)

        findings: list[dict[str, Any]] = []

        for rel_path, text in ("CLAUDE.md", claude_text), ("AGENTS.md", agents_text):
            observed_models = {match.group(0) for match in MODEL_RE.finditer(text)}
            unknown_models = sorted(token for token in observed_models if token not in canonical_models)
            if unknown_models:
                findings.append(
                    {
                        "kind": "model_drift",
                        "source": rel_path,
                        "expected": sorted(canonical_models),
                        "observed": unknown_models,
                    }
                )

        observed_roles = _extract_role_mentions(skill_map_text, canonical_roles)
        unexpected_roles = sorted(token for token in observed_roles if token not in canonical_roles)
        missing_roles = sorted(token for token in canonical_roles if token not in observed_roles)
        if unexpected_roles or missing_roles:
            findings.append(
                {
                    "kind": "role_drift",
                    "source": "skills/SKILL_MAP.md",
                    "expected": sorted(canonical_roles),
                    "observed": sorted(observed_roles),
                }
            )

        observed_phases = _extract_phase_mentions(claude_text, agents_text, skill_map_text)
        unknown_phases = sorted(token for token in observed_phases if token not in canonical_phases)
        if unknown_phases:
            findings.append(
                {
                    "kind": "term_inconsistency",
                    "source": "CLAUDE.md, AGENTS.md, skills/SKILL_MAP.md",
                    "expected": sorted(canonical_phases),
                    "observed": unknown_phases,
                }
            )

        verdict = "passed" if not findings else "failed"
        cost_ms = max(1, int((time.perf_counter() - started) * 1000))
        return DetectorResult(
            verdict=verdict,
            findings=findings,
            cost_ms=cost_ms,
            raw={
                "project_root": str(root),
                "canonical_models": sorted(canonical_models),
                "canonical_roles": sorted(canonical_roles),
                "canonical_phases": sorted(canonical_phases),
            },
        )
