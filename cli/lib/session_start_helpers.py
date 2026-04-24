#!/usr/bin/env python3
"""SessionStart hook 用の進捗サマリ生成。"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
CLI_DIR = SCRIPT_DIR.parent
HELIX_BIN = CLI_DIR / "helix"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from yaml_parser import get_nested, parse_yaml  # noqa: E402


def build_progress_block(project_root: Path) -> str:
    """phase.yaml + interrupt + handover を読んで AI 向けサマリを生成する。"""
    phase_file = project_root / ".helix" / "phase.yaml"
    if not phase_file.exists():
        return ""

    try:
        phase_data = parse_yaml(phase_file.read_text(encoding="utf-8"))
        current_phase = get_nested(phase_data, "current_phase") or "L1"
        current_mode = get_nested(phase_data, "current_mode") or "forward"
        current_step = _format_sprint(get_nested(phase_data, "sprint.current_step"))
        sprint_status = get_nested(phase_data, "sprint.status") or "active"
        drive = get_nested(phase_data, "sprint.drive")
    except Exception:
        return ""

    lines = [
        "## HELIX 現在の進捗",
        f"- Phase: {current_phase} / Sprint: {current_step or 'N/A'} / Mode: {current_mode}",
    ]
    if drive:
        lines.append(f"- Drive: {drive}")
    lines.append("")

    if sprint_status == "interrupted":
        interrupt_info = _load_interrupt_status(project_root)
        open_interrupts = [
            item for item in interrupt_info if item.get("status") not in {"resumed", "cancelled"}
        ]
        if open_interrupts:
            lines.append("## ⚠️ 前回セッション中断中")
            for item in open_interrupts[:3]:
                interrupt_id = item.get("id", "?")
                reason = item.get("reason", "")
                lines.append(f"- Interrupt ID: {interrupt_id} (reason: {reason})")
                lines.append(f"  復帰コマンド: `helix interrupt resume --id {interrupt_id}`")
            lines.append("")

    handover_json = project_root / ".helix" / "handover" / "CURRENT.json"
    if handover_json.exists():
        handover_info = _load_handover_status(project_root)
        if handover_info and handover_info.get("exists") is not False:
            task = handover_info.get("task", {})
            owner = handover_info.get("owner", "?")
            status = task.get("status", "?")
            task_id = task.get("id", "?")
            title = task.get("title", "")
            lines.append("## 🤝 Handover 引き継ぎ中")
            lines.append(f'- Task: {task_id} "{title}" (owner={owner}, status={status})')
            if owner == "codex" and status == "ready_for_review":
                lines.append("- 復帰コマンド: `helix handover resume`")
            else:
                lines.append("- 状態確認: `helix handover status`")
            lines.append("")

    return "\n".join(lines).rstrip()


def _load_interrupt_status(project_root: Path) -> list[dict[str, Any]]:
    payload = _run_helix_json(project_root, ["interrupt", "status", "--json"], [])
    return payload if isinstance(payload, list) else []


def _load_handover_status(project_root: Path) -> dict[str, Any]:
    payload = _run_helix_json(project_root, ["handover", "status", "--json"], {})
    return payload if isinstance(payload, dict) else {}


def _format_sprint(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.startswith("0."):
        return "." + text.split(".", 1)[1]
    return text


def _run_helix_json(project_root: Path, args: list[str], fallback: Any) -> Any:
    try:
        res = subprocess.run(
            [str(HELIX_BIN), *args],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return json.loads(res.stdout)
    except Exception:
        pass
    return fallback


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "progress":
        root = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path.cwd()
        sys.stdout.write(build_progress_block(root))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
