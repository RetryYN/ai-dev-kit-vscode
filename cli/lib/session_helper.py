"""PLAN-083 Phase 4: session_id 検出 helper.

session_id を以下の優先順で検出:
1. HELIX_SESSION_ID env
2. CLAUDE_SESSION_ID env
3. /tmp/claude-* path / CLAUDE_PROJECT_DIR env から推定
4. UUID fallback (8 文字 hex prefix)
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid


_TMP_SESSION_PATTERN = re.compile(
    r"/tmp/claude-(?:\d+)/[^/]+/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
)


# @helix:index id=session_helper.detect_session_id domain=cli/lib summary=session_id を 4 fallback で検出
def detect_session_id() -> str:
    """session_id を検出して返す (必ず非空 string)。"""

    # 1. HELIX_SESSION_ID env
    helix_id = os.environ.get("HELIX_SESSION_ID", "").strip()
    if helix_id:
        return helix_id

    # 2. CLAUDE_SESSION_ID env
    claude_id = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if claude_id:
        return claude_id

    # 3. /tmp/claude-* path から推定
    inferred = _infer_from_tmp_path()
    if inferred:
        return inferred

    # 4. UUID fallback
    return _uuid_fallback()


def _infer_from_tmp_path() -> str | None:
    """/tmp/claude-* path / CLAUDE_PROJECT_DIR から session id を推定する。"""
    candidates = [
        os.environ.get("CLAUDE_TASK_OUTPUT_DIR", ""),
        os.environ.get("CLAUDE_PROJECT_DIR", ""),
    ]
    for c in candidates:
        if not c:
            continue
        match = _TMP_SESSION_PATTERN.search(c)
        if match:
            return match.group(1)[:8]
    return None


# @helix:index id=session_helper._uuid_fallback domain=cli/lib summary=session_id 検出失敗時の UUID fallback (8 文字)
def _uuid_fallback() -> str:
    """uuid.uuid4().hex prefix 8 文字を返す (必ず非空)."""
    return f"unknown-{uuid.uuid4().hex[:8]}"


# @helix:index id=session_helper.get_session_meta domain=cli/lib summary=session_id + 推定方法 + env source を返す
def get_session_meta() -> dict[str, str | None]:
    """session_id 検出のメタ情報を返す."""
    return {
        "helix_session_id": os.environ.get("HELIX_SESSION_ID", "") or None,
        "claude_session_id": os.environ.get("CLAUDE_SESSION_ID", "") or None,
        "claude_task_output_dir": os.environ.get("CLAUDE_TASK_OUTPUT_DIR", "") or None,
        "claude_project_dir": os.environ.get("CLAUDE_PROJECT_DIR", "") or None,
        "detected": detect_session_id(),
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--meta" in args or "-m" in args:
        print(json.dumps(get_session_meta(), ensure_ascii=False))
    else:
        print(detect_session_id())
