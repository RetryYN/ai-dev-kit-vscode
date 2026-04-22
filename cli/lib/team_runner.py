#!/usr/bin/env python3
"""HELIX Team Runner.

チーム定義 YAML を読み、strategy に応じて複数メンバーを実行する。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml_parser


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'")):
        return v[1:-1]
    return v


def _parse_member_line(line: str) -> tuple[str, str] | None:
    m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.+)$", line.strip())
    if not m:
        return None
    return m.group(1), _strip_quotes(m.group(2))


def _parse_team_yaml(text: str) -> dict[str, Any]:
    """チーム定義 YAML の簡易パース。

    - top-level の `name`/`strategy` は yaml_parser.parse_yaml を利用
    - `members` は list 形式を専用ロジックで抽出
    """

    header_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\s*members\s*:\s*$", line):
            break
        header_lines.append(line)

    header = yaml_parser.parse_yaml("\n".join(header_lines)) if header_lines else {}
    result: dict[str, Any] = {
        "name": _strip_quotes(str(header.get("name", ""))),
        "strategy": _strip_quotes(str(header.get("strategy", "sequential"))),
        "members": [],
    }

    members: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_members = False

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if re.match(r"^members\s*:\s*$", stripped):
            in_members = True
            continue

        if not in_members:
            continue

        if stripped.startswith("- "):
            if current:
                members.append(current)
            current = {}
            rest = stripped[2:].strip()
            if rest:
                parsed = _parse_member_line(rest)
                if parsed:
                    k, v = parsed
                    current[k] = v
            continue

        if current is None:
            continue

        parsed = _parse_member_line(stripped)
        if parsed:
            k, v = parsed
            current[k] = v

    if current:
        members.append(current)

    result["members"] = [m for m in members if "role" in m]
    return result


def _truncate_output(stdout: str, stderr: str) -> str:
    chunks = []
    if stdout:
        chunks.append(stdout.strip())
    if stderr:
        chunks.append(stderr.strip())
    joined = "\n".join(c for c in chunks if c)
    return joined[-500:] if joined else ""


def run_member(
    member: dict[str, str],
    project_root: str,
    helix_home: str,
    timeout: int = 1800,
) -> dict[str, Any]:
    """1 メンバーを実行する。"""

    role = member.get("role", "pg")
    task = member.get("task", "")
    engine = member.get("engine", "codex")
    thinking = member.get("thinking", "")

    if engine == "codex":
        cmd = [f"{helix_home}/cli/helix-codex", "--role", role, "--task", task]
        if thinking:
            cmd.extend(["--thinking", thinking])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os.environ, "HELIX_PROJECT_ROOT": project_root},
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return {
                "role": role,
                "engine": engine,
                "exit_code": 124,
                "status": "timeout",
                "output": _truncate_output(stdout, stderr),
            }
        status = "completed" if result.returncode == 0 else "failed"
        return {
            "role": role,
            "engine": engine,
            "exit_code": result.returncode,
            "status": status,
            "output": _truncate_output(result.stdout or "", result.stderr or ""),
        }

    if engine == "claude":
        print(f"[team] Claude sub-agent 委譲: @{role} {task}")
        return {
            "role": role,
            "engine": engine,
            "exit_code": 0,
            "status": "delegated",
            "output": "claude sub-agent 委譲",
        }

    return {
        "role": role,
        "engine": engine,
        "exit_code": 1,
        "status": "failed",
        "output": f"不明なエンジン: {engine}",
    }


def run_sequential(members: list[dict[str, str]], project_root: str, helix_home: str) -> list[dict[str, Any]]:
    """直列実行。"""

    results: list[dict[str, Any]] = []
    for m in members:
        print(f"[team] {m.get('role', 'unknown')}（{m.get('engine', 'codex')}）を実行中...")
        result = run_member(m, project_root, helix_home)
        results.append(result)
        if result.get("exit_code", 1) != 0:
            print(f"[team] {m.get('role', 'unknown')} 失敗。チーム実行を中断。")
            break
    return results


def run_parallel(members: list[dict[str, str]], project_root: str, helix_home: str) -> list[dict[str, Any]]:
    """並列実行（codex メンバーのみ）。"""

    results: list[dict[str, Any]] = []
    codex_members = [m for m in members if m.get("engine", "codex") == "codex"]
    claude_members = [m for m in members if m.get("engine", "codex") == "claude"]

    for m in claude_members:
        print(f"[team] Claude sub-agent: @{m.get('role', 'unknown')} {m.get('task', '')}")
        results.append(
            {
                "role": m.get("role", "unknown"),
                "engine": "claude",
                "exit_code": 0,
                "status": "delegated",
                "output": "委譲指示",
            }
        )

    if codex_members:
        with ThreadPoolExecutor(max_workers=min(3, len(codex_members))) as executor:
            futures = {
                executor.submit(run_member, m, project_root, helix_home): m for m in codex_members
            }
            for future in as_completed(futures):
                results.append(future.result())

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="HELIX Team Runner")
    parser.add_argument("--definition", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--helix-home", required=True)
    args = parser.parse_args()

    definition_text = Path(args.definition).read_text(encoding="utf-8")
    definition = _parse_team_yaml(definition_text)

    name = definition.get("name", "unnamed")
    strategy = definition.get("strategy", "sequential")
    members = definition.get("members", [])

    print(f"チーム: {name}")
    print(f"戦略: {strategy}")
    print(f"メンバー: {len(members)} 人")
    print("")

    if strategy in ("sequential", "pipeline"):
        results = run_sequential(members, args.project_root, args.helix_home)
    elif strategy in ("parallel", "twin"):
        results = run_parallel(members, args.project_root, args.helix_home)
    else:
        print(f"エラー: 不明な戦略: {strategy}")
        sys.exit(1)

    print("")
    print("=== チーム実行結果 ===")
    for r in results:
        status = "✓" if r.get("exit_code", 1) == 0 else "✗"
        print(f"  {status} {r.get('role', 'unknown')}（{r.get('engine', 'unknown')}）")

    status_path = Path(args.project_root) / ".helix" / "team-status.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps({"name": name, "strategy": strategy, "members": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    failed = [r for r in results if r.get("exit_code", 1) != 0]
    if failed:
        print(f"\n{len(failed)} 件失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
