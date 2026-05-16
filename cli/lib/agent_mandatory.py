"""PLAN-082 Phase 2: subagent fire-mandatory + suggest + audit (PLAN-076 機械化).

契約: helix/HELIX_CORE.md §工程別 subagent 起動マップ (PLAN-076 framework)
PLAN-078 v28 agent_slots を audit log として再利用する.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from cli.lib import helix_db


# PLAN-076 §工程明示的サブエージェント (mandatory by phase, 10 種)
MANDATORY_SUBAGENTS: dict[str, list[dict[str, str]]] = {
    "G0.5": [
        {"subagent": "pdm-tech-innovation", "purpose": "海外技術思想翻案"},
        {"subagent": "pdm-marketing-innovation", "purpose": "海外マーケ思想翻案"},
        {"subagent": "pdm-innovation-manager", "purpose": "統合判断"},
    ],
    "L2": [
        {"subagent": "pmo-tech-fork", "purpose": "OSS 採用判断時"},
        {"subagent": "pmo-tech-docs", "purpose": "設計手法精読時"},
        {"subagent": "pmo-helix-explorer", "purpose": "HELIX 内資産探索"},
        {"subagent": "pmo-helix-scout", "purpose": "HELIX 内軽量目星"},
    ],
    "L3": [
        {"subagent": "pmo-project-explorer", "purpose": "project 内資産探索"},
        {"subagent": "pmo-helix-explorer", "purpose": "HELIX 内資産探索"},
    ],
    "L4": [
        {"subagent": "pmo-project-scout", "purpose": "軽量目星"},
        {"subagent": "pmo-project-explorer", "purpose": "project 内資産探索"},
    ],
    "G2": [{"subagent": "pmo-sonnet", "purpose": "G2 review"}],
    "G4": [{"subagent": "pmo-sonnet", "purpose": "G4 review"}],
    "L8": [{"subagent": "pmo-sonnet", "purpose": "受入レビュー"}],
}

# PLAN-076 §実行選択サブエージェント (on-demand by judgment, 4 種)
ON_DEMAND_SUBAGENTS: list[dict[str, str | list[str]]] = [
    {
        "subagent": "pmo-haiku",
        "purpose": "Web 検索 / docs/** 軽修正",
        "keywords": ["web", "検索", "search", "docs", "軽作業"],
    },
    {
        "subagent": "pmo-tech-news",
        "purpose": "最新 Tech 動向 sweep (週次想定)",
        "keywords": ["最新", "動向", "news", "週次", "trend", "tech動向"],
    },
    {
        "subagent": "pm-advisor",
        "purpose": "PM 級難判断 adversarial check",
        "keywords": ["pm判断", "スコープ", "優先度", "advisor", "判断"],
    },
    {
        "subagent": "tl-advisor",
        "purpose": "TL 級難判断 adversarial check",
        "keywords": ["契約", "技術選択", "設計", "tl", "リファクタ", "テスト戦略"],
    },
]

ALLOWED_PHASES = tuple(MANDATORY_SUBAGENTS.keys())


# @helix:index id=agent_mandatory.list_mandatory_for_phase domain=cli/lib summary=phase に対する mandatory subagent 一覧返却
def list_mandatory_for_phase(phase: str) -> list[dict[str, str]]:
    """phase ('G0.5' / 'L2' / 'L3' / 'L4' / 'G2' / 'G4' / 'L8') に対する mandatory subagent 一覧.

    未知 phase は空 list を返す (CHECK でない).
    """
    return list(MANDATORY_SUBAGENTS.get(phase, []))


# @helix:index id=agent_mandatory.audit_phase domain=cli/lib summary=現セッションで該当 phase の mandatory subagent 呼び出し audit
def audit_phase(phase: str, *, since_hours: int = 24, session_id: str | None = None) -> dict[str, Any]:
    """現 phase の mandatory subagent が呼ばれたか agent_slots から audit.

    PLAN-078 agent_slots を `agent_kind='claude_subagent'` フィルタ + `fired_at` 過去 since_hours で参照.
    session_id 指定時は該当 session のみ対象にする.

    返り値: {
        "phase": str,
        "mandatory": [{"subagent": str, "required": bool, "called": bool, "last_called_at": str | None}, ...],
        "missing_count": int,
        "warning": bool,
    }
    """
    mandatory = list_mandatory_for_phase(phase)
    if not mandatory:
        return {
            "phase": phase,
            "mandatory": [],
            "missing_count": 0,
            "warning": False,
        }

    threshold = datetime.utcnow() - timedelta(hours=since_hours)
    threshold_iso = threshold.strftime("%Y-%m-%d %H:%M:%S")

    called_map: dict[str, str | None] = {}
    try:
        conn = helix_db.get_connection()
        conn.row_factory = sqlite3.Row
        try:
            where_clauses = ["agent_kind = 'claude_subagent'", "fired_at >= ?"]
            params: list[object] = [threshold_iso]
            if session_id is not None:
                where_clauses.append("session_id = ?")
                params.append(session_id)
            rows = conn.execute(
                f"""
                SELECT subagent_type, MAX(fired_at) AS last_fired
                FROM agent_slots
                WHERE {' AND '.join(where_clauses)}
                GROUP BY subagent_type
                """,
                params,
            ).fetchall()
            for row in rows:
                if row["subagent_type"]:
                    called_map[row["subagent_type"]] = row["last_fired"]
        finally:
            conn.close()
    except sqlite3.Error:
        called_map = {}

    audit_rows: list[dict[str, Any]] = []
    missing = 0
    for entry in mandatory:
        sub = entry["subagent"]
        last = called_map.get(sub)
        called = last is not None
        if not called:
            missing += 1
        audit_rows.append(
            {
                "subagent": sub,
                "required": True,
                "called": called,
                "last_called_at": last,
            }
        )

    return {
        "phase": phase,
        "mandatory": audit_rows,
        "missing_count": missing,
        "warning": missing > 0,
    }


# @helix:index id=agent_mandatory.suggest_for_task domain=cli/lib summary=task description から on-demand subagent 推奨
def suggest_for_task(task_description: str) -> list[dict[str, Any]]:
    """task description に基づき on-demand subagent を推奨 (簡易 keyword match).

    返り値: [{"subagent": str, "reason": str, "confidence": float}, ...] (confidence 高い順)
    """
    if not task_description:
        return []

    lowered = task_description.lower()
    matches: list[dict[str, Any]] = []
    for entry in ON_DEMAND_SUBAGENTS:
        keywords = entry["keywords"]
        assert isinstance(keywords, list)
        hits = [kw for kw in keywords if kw.lower() in lowered]
        if hits:
            confidence = min(1.0, len(hits) / max(len(keywords), 1) * 2)
            matches.append(
                {
                    "subagent": entry["subagent"],
                    "reason": f"keyword match: {', '.join(hits)} ({entry['purpose']})",
                    "confidence": round(confidence, 2),
                }
            )

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches


# @helix:index id=agent_mandatory.fire_mandatory_audit domain=cli/lib summary=fire-mandatory subcommand の audit-only 実装
def fire_mandatory_audit(phase: str, *, dry_run: bool = True) -> dict[str, Any]:
    """fire-mandatory subcommand の audit-only 実装 (Phase 1 では実 fire しない).

    --dry-run なし時も「呼ぶべき subagent 一覧」を返すだけで、実 fire は Opus / Codex セッション側に委ねる.
    """
    mandatory = list_mandatory_for_phase(phase)
    if not mandatory:
        return {
            "phase": phase,
            "action": "noop",
            "reason": f"phase '{phase}' に mandatory subagent 定義なし",
            "subagents": [],
        }
    return {
        "phase": phase,
        "action": "audit" if dry_run else "list",
        "subagents": mandatory,
        "note": "Phase 1 (本 PLAN-082) は audit/list のみ、実 fire は呼び出し側 (Opus / Codex) の責務",
    }


def _main_cli(argv: list[str] | None = None) -> int:
    """`python3 -m cli.lib.agent_mandatory` 用の最小 CLI entry."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="PLAN-082 agent mandatory helper CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fire = sub.add_parser("fire-mandatory")
    p_fire.add_argument("--phase", required=True)
    p_fire.add_argument("--dry-run", action="store_true")
    p_fire.add_argument("--json", action="store_true")

    p_suggest = sub.add_parser("suggest")
    p_suggest.add_argument("--task", required=True)
    p_suggest.add_argument("--json", action="store_true")

    p_audit = sub.add_parser("audit")
    p_audit.add_argument("--phase", required=True)
    p_audit.add_argument("--since-hours", type=int, default=24)
    p_audit.add_argument("--session-id")
    p_audit.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "fire-mandatory":
        result = fire_mandatory_audit(args.phase, dry_run=args.dry_run)
    elif args.cmd == "suggest":
        result = suggest_for_task(args.task)
    elif args.cmd == "audit":
        result = audit_phase(args.phase, since_hours=args.since_hours, session_id=args.session_id)
    else:
        parser.print_help()
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if args.cmd == "suggest":
            if not result:
                print("(該当なし)")
            else:
                for m in result:
                    print(f"{m['subagent']:25s} conf={m['confidence']:.2f}  {m['reason']}")
        elif args.cmd == "audit":
            print(f"phase: {result['phase']}  missing: {result['missing_count']}  warning: {result['warning']}")
            for row in result["mandatory"]:
                mark = "✓" if row["called"] else "✗"
                last = row["last_called_at"] or "(never)"
                print(f"  {mark} {row['subagent']:25s} last_called={last}")
        else:  # fire-mandatory
            print(f"phase: {result['phase']}  action: {result['action']}")
            if result.get("reason"):
                print(f"  reason: {result['reason']}")
            for entry in result.get("subagents", []):
                print(f"  - {entry['subagent']:25s} {entry['purpose']}")
            if result.get("note"):
                print(f"\nnote: {result['note']}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_main_cli())
