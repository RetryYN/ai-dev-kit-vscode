#!/usr/bin/env python3
"""Policy checks for HELIX team delegation definitions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ALLOWED_ROLES = {"tl", "se", "pg", "fe", "qa", "security", "dba", "devops", "docs", "research", "legacy", "perf"}
ALLOWED_ENGINES = {"codex", "claude"}
ALLOWED_STRATEGIES = {"sequential", "pipeline", "parallel", "twin"}
BLOCKED_SELF_DELEGATION = {"opus", "orchestrator", "pm", "po"}
RESEARCH_TASK_RE = re.compile(
    r"research|investigate|web\s*search|web検索|検索|調査|リサーチ|外部\s*api|外部api|ライブラリ比較|技術選定",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PolicyFinding:
    code: str
    message: str
    member: int | None = None


def _value(member: dict[str, Any], key: str) -> str:
    raw = member.get(key, "")
    return str(raw).strip().lower()


def validate_team_definition(definition: dict[str, Any]) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    strategy = str(definition.get("strategy", "sequential")).strip().lower()
    members = definition.get("members", [])

    if strategy not in ALLOWED_STRATEGIES:
        findings.append(PolicyFinding("invalid_strategy", f"strategy must be one of {sorted(ALLOWED_STRATEGIES)}"))
    if not isinstance(members, list) or not members:
        findings.append(PolicyFinding("missing_members", "team definition must include at least one member"))
        return findings

    for index, member in enumerate(members):
        if not isinstance(member, dict):
            findings.append(PolicyFinding("invalid_member", "member must be an object", index))
            continue

        role = _value(member, "role")
        engine = _value(member, "engine") or "codex"
        model = _value(member, "model")
        task = str(member.get("task", "")).strip()

        if role not in ALLOWED_ROLES:
            findings.append(PolicyFinding("invalid_role", f"role must be one of {sorted(ALLOWED_ROLES)}", index))
        if engine not in ALLOWED_ENGINES:
            findings.append(PolicyFinding("invalid_engine", f"engine must be one of {sorted(ALLOWED_ENGINES)}", index))
        if role in BLOCKED_SELF_DELEGATION or engine in BLOCKED_SELF_DELEGATION or model in BLOCKED_SELF_DELEGATION:
            findings.append(
                PolicyFinding(
                    "blocked_self_delegation",
                    "orchestrator/PM/Opus-style self delegation is blocked; route work to an execution or review role",
                    index,
                )
            )
        if model and model in {"gpt-5.4", "gpt-5.5"} and role in {"pg", "se"}:
            findings.append(
                PolicyFinding(
                    "overpowered_execution_model",
                    "implementation roles must not pin TL-class models in team definitions; use role defaults",
                    index,
                )
            )
        if task and RESEARCH_TASK_RE.search(task) and role != "research":
            findings.append(
                PolicyFinding(
                    "research_task_wrong_role",
                    "research/search tasks must be routed to role=research before implementation proceeds",
                    index,
                )
            )

    return findings


def check_team_definition(definition: dict[str, Any]) -> dict[str, object]:
    errors = validate_team_definition(definition)
    return {"ok": not errors, "errors": [asdict(item) for item in errors]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_policy_guard")
    parser.add_argument("--definition", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    lib_dir = Path(__file__).resolve().parent
    if str(lib_dir) not in sys.path:
        sys.path.insert(0, str(lib_dir))
    import team_runner  # pylint: disable=import-outside-toplevel

    definition = team_runner._parse_team_yaml(Path(args.definition).read_text(encoding="utf-8"))
    payload = check_team_definition(definition)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif payload["ok"]:
        print("[agent-policy] OK")
    else:
        print("[agent-policy] FAIL: team delegation policy violation", file=sys.stderr)
        for item in payload["errors"]:
            suffix = f" member={item['member']}" if item.get("member") is not None else ""
            print(f"  - {item['code']}: {item['message']}{suffix}", file=sys.stderr)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
