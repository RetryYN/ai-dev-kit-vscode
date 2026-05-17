#!/usr/bin/env python3
"""Stop hook 用 handover auto dump + compact recommendation."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cli.lib import handover as handover_core
from cli.lib import session_helper
from cli.lib import agent_slots

DEFAULT_THRESHOLD = 0.70
DEFAULT_MESSAGE_LIMIT = 2000


def _project_root_from_helix_dir(helix_dir: Path | None) -> Path:
    return helix_dir.resolve().parent if helix_dir else Path.cwd()


def _run_text(project_root: Path, command: list[str], timeout_sec: int = 5) -> str:
    try:
        proc = subprocess.run(
            command,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _session_line_count() -> tuple[int | None, float | None]:
    session_file = os.environ.get("CLAUDE_SESSION_FILE", "").strip()
    if not session_file:
        return None, None
    try:
        line_count = sum(1 for _ in Path(session_file).expanduser().open(encoding="utf-8"))
    except OSError:
        return None, None
    raw_limit = os.environ.get("HELIX_CONTEXT_MESSAGE_LIMIT", str(DEFAULT_MESSAGE_LIMIT)).strip()
    try:
        limit = max(1, int(raw_limit))
    except ValueError:
        limit = DEFAULT_MESSAGE_LIMIT
    return line_count, min(line_count / limit, 1.0)


def _release_running_slots_for_session(session_id: str | None) -> int:
    if not session_id:
        return 0
    released = 0
    try:
        slots = [s for s in agent_slots.list_active_slots() if s.get("session_id") == session_id]
    except Exception:
        return 0
    for slot in slots:
        try:
            agent_slots.release_slot(slot["id"], status="cancelled")
        except Exception:
            continue
        released += 1
    return released


def _build_summary(state: dict[str, Any], dirty_lines: list[str], commits: list[str]) -> str:
    task = state.get("task", {})
    pending = state.get("files", {}).get("pending", [])
    commit_head = commits[0] if commits else "no-commit"
    dirty_count = len(dirty_lines)
    return (
        f"{task.get('id', '?')} {task.get('title', '')} | "
        f"dirty={dirty_count} pending={len(pending)} head={commit_head}"
    ).strip()


# @helix:index id=handover-auto-dump.recommend-compact domain=cli/lib summary=context proxy で compact 推奨判定
def recommend_compact(*, threshold: float = DEFAULT_THRESHOLD) -> dict[str, Any]:
    line_count, context_pct = _session_line_count()
    return {
        "ok": True,
        "message_count": line_count,
        "context_pct_estimate": context_pct,
        "compact_recommended": bool(context_pct is not None and context_pct >= threshold),
        "threshold": threshold,
    }


# @helix:index id=handover-auto-dump.auto-dump-current domain=cli/lib summary=Stop hook 向け CURRENT 自動更新
def auto_dump_current(
    *,
    helix_dir: Path | None = None,
    detect_compact_threshold: float = DEFAULT_THRESHOLD,
    release_running_slots: bool = False,
    release_session_id: str | None = None,
) -> dict[str, Any]:
    project_root = _project_root_from_helix_dir(helix_dir)
    current_json = project_root / ".helix" / "handover" / "CURRENT.json"
    try:
        state = handover_core.load_json(current_json)
        branch = _run_text(project_root, ["git", "branch", "--show-current"]) or state.get("git", {}).get("branch", "")
        head_sha = _run_text(project_root, ["git", "rev-parse", "HEAD"]) or state.get("git", {}).get("head_sha", "")
        dirty_text = _run_text(project_root, ["bash", "-lc", "git status --porcelain | head -20"])
        dirty_lines = [line for line in dirty_text.splitlines() if line.strip()]
        commits = _run_text(project_root, ["git", "log", "--oneline", "-10"], timeout_sec=10).splitlines()
        recommendation = recommend_compact(threshold=detect_compact_threshold)
        updated = json.loads(json.dumps(state, ensure_ascii=False))
        updated.setdefault("git", {})
        updated["git"]["branch"] = branch
        updated["git"]["head_sha"] = head_sha
        updated["git"]["dirty"] = bool(dirty_lines)
        updated["updated_at"] = handover_core.now_iso()
        updated["revision"] = int(state.get("revision", 0)) + 1
        release_session = release_session_id or (None if not release_running_slots else session_helper.detect_session_id())
        released_count = (
            _release_running_slots_for_session(release_session)
            if release_running_slots
            else 0
        )
        handover_core.validate_state(updated)
        handover_core.atomic_write_json_with_revision(
            current_json,
            updated,
            expected_revision=int(state.get("revision", 0)),
        )
        return {
            "ok": True,
            "revision": updated["revision"],
            "compact_recommended": recommendation["compact_recommended"],
            "context_pct_estimate": recommendation["context_pct_estimate"],
            "released_count": released_count,
            "session_id": release_session,
            "summary": _build_summary(updated, dirty_lines, commits),
        }
    except Exception as exc:
        return {
            "ok": False,
            "revision": None,
            "compact_recommended": False,
            "context_pct_estimate": None,
            "summary": "",
            "error_msg": str(exc),
        }


def _print_result(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"revision={result.get('revision')}, "
            f"recommended={result.get('compact_recommended')}"
        )
    return 0


# @helix:index id=handover-auto-dump.build-parser domain=cli/lib summary=CLI parser を構築する
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handover_auto_dump")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_auto = sub.add_parser("auto-dump")
    p_auto.add_argument("--json", action="store_true")
    p_auto.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    p_auto.add_argument("--release-running", action="store_true")
    p_auto.add_argument("--session-id", default=None)

    p_compact = sub.add_parser("recommend-compact")
    p_compact.add_argument("--json", action="store_true")
    p_compact.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    return parser


# @helix:index id=handover-auto-dump.main domain=cli/lib summary=CLI entrypoint を実行する
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "auto-dump":
        return _print_result(
            auto_dump_current(
                detect_compact_threshold=args.threshold,
                release_running_slots=args.release_running,
                release_session_id=args.session_id,
            ),
            args.json,
        )
    if args.cmd == "recommend-compact":
        return _print_result(recommend_compact(threshold=args.threshold), args.json)
    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
