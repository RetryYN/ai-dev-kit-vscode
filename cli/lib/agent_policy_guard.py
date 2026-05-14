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


ALLOWED_ROLES = {
    "tl",
    "se",
    "pg",
    "fe",
    "qa",
    "security",
    "dba",
    "devops",
    "docs",
    "research",
    "legacy",
    "perf",
    "impl-sonnet",
    "pdm-tech-innovation",
    "pdm-marketing-innovation",
    "pdm-innovation-manager",
    "pm-advisor",
    "tl-advisor",
    "recommender",
    "classifier",
    "effort-classifier",
}
ALLOWED_ENGINES = {"codex", "claude"}
ALLOWED_STRATEGIES = {"sequential", "pipeline", "parallel", "twin"}
BLOCKED_SELF_DELEGATION = {"opus", "orchestrator", "pm", "po"}
RESEARCH_GUARD_TARGET_ROLES = {"pg", "se", "fe", "qa", "security", "dba", "devops"}
RESEARCH_TASK_RE = re.compile(
    r"research|investigate|web\s*search|web検索|Web検索|リサーチ|外部\s*api|外部api|"
    r"ライブラリ比較|技術選定|先行事例|一次ソース|公式.*調査|SDK.*調査|"
    r"OSS.*比較|検索.*(公式|外部|SDK|ライブラリ|最新)",
    re.IGNORECASE,
)
# PLAN-023 W-1: 実装意図キーワードがあれば research 誤判定を上書き。
# detect_plan_only_task() の execute_pattern と同じ 2 段階構造に揃える。
IMPL_TASK_RE = re.compile(
    r"実装|修正|削除|編集|変更|追加|適用|作成|"
    r"implement|edit|delete|remove|fix|apply|modify|update|create",
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


def validate_member(member: dict[str, Any], index: int | None = None) -> list[PolicyFinding]:
    findings: list[PolicyFinding] = []
    if not isinstance(member, dict):
        return [PolicyFinding("invalid_member", "member must be an object", index)]

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
    if (
        task
        and RESEARCH_TASK_RE.search(task)
        and not IMPL_TASK_RE.search(task)  # PLAN-023 W-1: 実装意図があれば緩和
        and role in RESEARCH_GUARD_TARGET_ROLES
    ):
        findings.append(
            PolicyFinding(
                "research_task_wrong_role",
                "research/search tasks must be routed to role=research before implementation proceeds",
                index,
            )
        )

    return findings


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
        findings.extend(validate_member(member, index))

    return findings


def check_team_definition(definition: dict[str, Any]) -> dict[str, object]:
    errors = validate_team_definition(definition)
    return {"ok": not errors, "errors": [asdict(item) for item in errors]}


def check_member(role: str, engine: str, task: str, model: str = "") -> dict[str, object]:
    errors = validate_member({"role": role, "engine": engine, "task": task, "model": model}, None)
    return {"ok": not errors, "errors": [asdict(item) for item in errors]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_policy_guard")
    parser.add_argument("--definition")
    parser.add_argument("--role")
    parser.add_argument("--engine", default="codex")
    parser.add_argument("--task", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.definition:
        lib_dir = Path(__file__).resolve().parent
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))
        import team_runner  # pylint: disable=import-outside-toplevel

        definition = team_runner._parse_team_yaml(Path(args.definition).read_text(encoding="utf-8"))
        payload = check_team_definition(definition)
    elif args.role:
        payload = check_member(args.role, args.engine, args.task, args.model)
    else:
        parser.error("--definition or --role is required")

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
