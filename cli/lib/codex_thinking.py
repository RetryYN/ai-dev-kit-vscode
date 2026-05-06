#!/usr/bin/env python3
"""Resolve HELIX Codex thinking level from CLI, auto classification, or role config."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)

VALID_THINKING = {"low", "medium", "high", "xhigh"}


def _cli_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _role_conf_path(role: str) -> Path:
    role_name = (role or "").strip()
    if not role_name:
        raise ValueError("role is required")
    path = _cli_root() / "roles" / f"{role_name}.conf"
    roles_dir = (_cli_root() / "roles").resolve()
    resolved = path.resolve(strict=False)
    if roles_dir != resolved.parent:
        raise ValueError(f"invalid role path: {role}")
    if not path.is_file():
        raise ValueError(f"role not found: {role}")
    return path


def _read_role_default(role: str) -> str:
    role_file = _role_conf_path(role)
    for line in role_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("codex_thinking="):
            value = line.split("=", 1)[1].strip()
            return _validate_thinking(value, f"role {role} codex_thinking")
    raise ValueError(f"role {role} codex_thinking is not defined")


def _validate_thinking(value: str | None, label: str) -> str:
    level = (value or "").strip()
    if level not in VALID_THINKING:
        raise ValueError(f"invalid {label}: {value!r} (expected low|medium|high|xhigh)")
    return level


def _auto_thinking(task: str, role: str) -> tuple[str, str] | None:
    try:
        try:
            from .effort_classifier import classify
        except ImportError:  # pragma: no cover - direct script execution
            from effort_classifier import classify

        result = classify(task, role=role, size=None, files=None, lines=None, use_llm=False)
        level = _validate_thinking(result.get("recommended_thinking"), "auto-thinking result")
        details = f"effort={result.get('effort')} score={result.get('score')}"
        return level, details
    except Exception as exc:
        logger.warning("auto-thinking classifier failed: %s", exc)
        return None


def resolve_thinking(
    role: str,
    cli_explicit: str | None = None,
    auto_thinking: bool = False,
    task: str | None = None,
) -> str:
    """Resolve thinking level using CLI explicit, auto classifier, then role default."""
    sprint = os.environ.get("HELIX_CURRENT_SPRINT", "")
    agent = os.environ.get("HELIX_CURRENT_AGENT", "")

    source = "role-default"
    details = ""
    if cli_explicit:
        selected = _validate_thinking(cli_explicit, "cli_explicit")
        source = "cli-explicit"
    elif auto_thinking and task:
        auto = _auto_thinking(task, role)
        if auto is not None:
            selected, details = auto
            source = "auto-thinking"
        else:
            selected = _read_role_default(role)
            source = "role-default-after-auto-failure"
    else:
        selected = _read_role_default(role)

    logger.info(
        "resolved thinking=%s source=%s role=%s sprint=%s agent=%s%s",
        selected,
        source,
        role,
        sprint,
        agent,
        f" {details}" if details else "",
    )
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve HELIX Codex thinking level")
    parser.add_argument("--role", required=True)
    parser.add_argument("--cli-explicit", default=None)
    parser.add_argument("--auto-thinking", action="store_true")
    parser.add_argument("--task", default=None)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="[codex-thinking] %(message)s")
    try:
        print(
            resolve_thinking(
                args.role,
                cli_explicit=args.cli_explicit,
                auto_thinking=args.auto_thinking,
                task=args.task,
            )
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
