from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import deferred_findings
import helix_db
from redaction import redact_value


VALID_SCRUM_TYPES = ("poc", "ui", "unit", "sprint", "post-deploy")
VALID_EVENT_TYPES = ("uncertainty_marker", "new_fact", "pre_impl_uncertain")
VALID_STATUSES = ("pending", "triaged", "adopted", "rejected", "archived")
TRANSITIONS = {
    "pending": ("triaged", "archived"),
    "triaged": ("adopted", "rejected", "archived"),
    "adopted": ("archived",),
    "rejected": ("archived",),
    "archived": (),
}

DB_FIELDS = (
    "trigger_id",
    "scrum_type",
    "source_id",
    "artifact_ref",
    "event_type",
    "plan_id",
    "sprint_id",
    "detected_at",
    "last_seen_at",
    "ttl_at",
    "resolved_at",
    "uncertainty_score",
    "impact_score",
    "confidence",
    "evidence_count",
    "normalized_signature",
    "content_hash",
    "status",
    "status_owner",
    "status_reason",
    "reason_code",
    "evidence_path_hint",
    "source_path",
    "source_line_start",
    "source_line_end",
    "created_by",
    "created_at",
)

REDACTABLE_FIELDS = ("title", "evidence", "reason", "recommendation", "status_reason")
RAW_FIELDS = ("body", "raw", "raw_body", "raw_text", "content")
PII_EXTRA_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+?\d[\d .-]{8,}\d)\b"),
)

UNCERTAINTY_MARKERS = (
    "未確定",
    "TBD",
    "要確認",
    "確定不能",
    "要再定義",
    "不確実",
    "未定",
)
NEW_FACT_MARKERS = (
    "新事実",
    "前提崩れ",
    "前提が崩れ",
    "新たに判明",
    "判明した",
)
PRE_IMPL_MARKERS = (
    "実装開始前",
    "実装前",
    "pre-impl",
    "pre implementation",
)
KPI_MARKERS = (
    "KPI 逸脱",
    "KPI逸脱",
    "指標逸脱",
    "SLO 逸脱",
    "SLO逸脱",
    "エラー率",
    "監視指標",
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _db_connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_path or helix_db.resolve_default_db_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = helix_db.get_connection(target)
    if hasattr(helix_db, "_ensure_schema"):
        helix_db._ensure_schema(conn)
    else:
        conn.executescript(helix_db.SCHEMA)
        conn.executescript(helix_db.SCHEMA_VERSION_SCHEMA)
        helix_db.migrate(conn)
    return conn


def _relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _scan_files(scan_paths: Iterable[str | Path], project_root: Path | None = None) -> list[Path]:
    root = Path(project_root or os.environ.get("HELIX_PROJECT_ROOT") or os.getcwd())
    files: list[Path] = []
    for raw_path in scan_paths:
        text_path = str(raw_path)
        if text_path == "review-json":
            path = root / ".helix" / "reviews"
        else:
            path = Path(text_path)
            if not path.is_absolute():
                path = root / path

        if path.is_file():
            files.append(path)
            continue
        if not path.is_dir():
            continue

        for candidate in path.rglob("*"):
            if not candidate.is_file():
                continue
            if _is_scannable_file(candidate, root):
                files.append(candidate)
    return sorted(set(files))


def _is_scannable_file(path: Path, project_root: Path) -> bool:
    rel = _relative_path(path, project_root)
    if re.search(r"(^|/)docs/features/.*/D-[^/]+$", rel) or re.search(r"(^|/)docs/features/.*/D-[^/]+\.", rel):
        return True
    if path.suffix.lower() == ".json" and ("review" in rel.lower() or "/reviews/" in rel.lower()):
        return True
    if path.name in ("backlog.yaml", "sprint.yaml") and "/scrum/" in f"/{rel}":
        return True
    return path.suffix.lower() in (".md", ".txt", ".yaml", ".yml") and (
        rel.startswith("docs/features/") or rel.startswith(".helix/scrum/")
    )


def _artifact_ref(path: Path, rel: str) -> str:
    lower = rel.lower()
    if lower.endswith(".json") or "/reviews/" in lower:
        return "review-json"
    if "backlog.yaml" in lower:
        return "sprint-backlog"
    if Path(rel).name.startswith("D-"):
        return Path(rel).name.split(".", 1)[0]
    return "scrum-artifact"


def _extract_plan_id(text: str, rel: str) -> str | None:
    match = re.search(r"PLAN-\d{3}", f"{rel}\n{text}")
    return match.group(0) if match else None


def _extract_sprint_id(text: str, rel: str) -> str | None:
    match = re.search(r"(?:Sprint|sprint)\s*([A-Za-z0-9_.-]+)", f"{rel}\n{text}")
    if match:
        return match.group(1)
    return None


def _score_impact(rel: str, marker_text: str, event_type: str) -> int:
    target = f"{rel}\n{marker_text}".lower()
    if any(token.lower() in target for token in KPI_MARKERS) or any(token in target for token in ("l9", "l10", "l11")):
        return 5
    if any(token in target for token in ("api", "db", "contract", "schema", "migration", "契約", "スキーマ")):
        return 4
    if event_type == "new_fact":
        return 4
    if any(token in target for token in ("ui", "ux", "a11y", "画面", "導線")):
        return 3
    return 3 if event_type == "pre_impl_uncertain" else 2


def _score_uncertainty(event_type: str, evidence_count: int) -> int:
    if event_type == "pre_impl_uncertain":
        return min(5, 3 + evidence_count // 2)
    if event_type == "new_fact":
        return min(5, 3 + evidence_count // 3)
    return min(5, 2 + evidence_count)


def _event_lines(lines: list[str], markers: tuple[str, ...]) -> list[tuple[int, str]]:
    matched: list[tuple[int, str]] = []
    pattern = re.compile("|".join(re.escape(marker) for marker in markers), re.IGNORECASE)
    for line_no, line in enumerate(lines, start=1):
        if pattern.search(line):
            matched.append((line_no, pattern.search(line).group(0)))
    return matched


def _scrub_marker_text(markers: list[tuple[int, str]]) -> str:
    return "|".join(sorted({marker.lower() for _, marker in markers}))


def _base_trigger(
    *,
    rel: str,
    artifact_ref: str,
    event_type: str,
    line_matches: list[tuple[int, str]],
    text: str,
    now: str,
) -> dict[str, Any]:
    evidence_count = max(1, len(line_matches))
    line_numbers = [line for line, _ in line_matches] or [1]
    marker_signature = _scrub_marker_text(line_matches) or event_type
    line_range = f"{min(line_numbers)}-{max(line_numbers)}"
    source_id = rel
    impact_score = _score_impact(rel, marker_signature, event_type)
    trigger = {
        "trigger_id": None,
        "scrum_type": "poc",
        "source_id": source_id,
        "artifact_ref": artifact_ref,
        "event_type": event_type,
        "plan_id": _extract_plan_id(text, rel),
        "sprint_id": _extract_sprint_id(text, rel),
        "detected_at": now,
        "last_seen_at": now,
        "ttl_at": _format_time(_parse_time(now) + timedelta(days=7)),
        "resolved_at": None,
        "uncertainty_score": _score_uncertainty(event_type, evidence_count),
        "impact_score": impact_score,
        "confidence": min(0.95, 0.55 + (evidence_count * 0.10)),
        "evidence_count": evidence_count,
        "normalized_signature": _sha256(f"{event_type}|{artifact_ref}|{marker_signature}")[:32],
        "content_hash": _sha256(f"{rel}|{event_type}|{line_range}|{marker_signature}")[:32],
        "status": "pending",
        "status_owner": None,
        "status_reason": None,
        "reason_code": marker_signature,
        "evidence_path_hint": f"{rel}:{line_range}",
        "source_path": rel,
        "source_line_start": min(line_numbers),
        "source_line_end": max(line_numbers),
        "created_by": "helix-scrum-trigger",
        "created_at": now,
    }
    evaluation = evaluate_quadrant(trigger)
    trigger["scrum_type"] = evaluation["recommended_scrum_type"]
    return trigger


def detect_triggers(scan_paths: Iterable[str | Path], project_root: Path | str | None = None) -> list[dict[str, Any]]:
    root = Path(project_root or os.environ.get("HELIX_PROJECT_ROOT") or os.getcwd())
    now = _utcnow()
    triggers: list[dict[str, Any]] = []
    default_paths = ("docs/features", "review-json", ".helix/scrum/backlog.yaml")
    for path in _scan_files(scan_paths or default_paths, root):
        rel = _relative_path(path, root)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        artifact = _artifact_ref(path, rel)
        event_matches = {
            "uncertainty_marker": _event_lines(lines, UNCERTAINTY_MARKERS),
            "new_fact": _event_lines(lines, NEW_FACT_MARKERS + KPI_MARKERS),
            "pre_impl_uncertain": _event_lines(lines, PRE_IMPL_MARKERS),
        }
        if event_matches["pre_impl_uncertain"] and event_matches["uncertainty_marker"]:
            event_matches["pre_impl_uncertain"] = sorted(
                set(event_matches["pre_impl_uncertain"] + event_matches["uncertainty_marker"])
            )
        for event_type, matches in event_matches.items():
            if not matches:
                continue
            trigger = _base_trigger(
                rel=rel,
                artifact_ref=artifact,
                event_type=event_type,
                line_matches=matches,
                text=text,
                now=now,
            )
            triggers.append({field: trigger.get(field) for field in DB_FIELDS})
    return triggers


def _context_text(trigger: dict[str, Any]) -> str:
    return " ".join(
        str(trigger.get(field) or "")
        for field in ("scrum_type", "artifact_ref", "event_type", "reason_code", "evidence_path_hint", "source_path")
    ).lower()


def evaluate_quadrant(trigger: dict[str, Any]) -> dict[str, Any]:
    uncertainty = int(trigger.get("uncertainty_score") or 0)
    impact = int(trigger.get("impact_score") or 0)
    evidence_count = int(trigger.get("evidence_count") or 0)
    high_uncertainty = uncertainty >= 3
    high_impact = impact >= 3
    eligible = (high_uncertainty and high_impact) or evidence_count >= 3
    quadrant = ("high" if high_uncertainty else "low") + "/" + ("high" if high_impact else "low")
    context = _context_text(trigger)

    if quadrant == "high/high":
        recommended = "post-deploy" if any(token in context for token in ("post", "deploy", "l9", "l10", "l11", "kpi", "slo", "監視", "本番")) else "sprint"
    elif quadrant == "low/high":
        recommended = "ui" if any(token in context for token in ("ui", "ux", "a11y", "画面", "導線")) else "sprint"
    elif quadrant == "high/low":
        recommended = "unit"
    else:
        recommended = "ui" if any(token in context for token in ("ui", "ux", "a11y", "画面", "導線")) else "unit"

    return {
        "eligible": eligible,
        "quadrant": quadrant,
        "recommended_scrum_type": recommended,
        "priority_score": round((impact * 0.6) + (uncertainty * 0.4), 2),
    }


def redact_trigger_fields(trigger: dict[str, Any]) -> dict[str, Any]:
    redacted = {key: value for key, value in dict(trigger).items() if key not in RAW_FIELDS}
    extra_patterns = deferred_findings.SECRET_EXTRA_PATTERNS + PII_EXTRA_PATTERNS
    for field in REDACTABLE_FIELDS:
        if field in redacted:
            redacted[field] = redact_value(
                redacted[field],
                key_hint=field,
                extra_patterns=extra_patterns,
                tuple_as_list=True,
            )
    return redacted


def _normalize_trigger_for_db(trigger: dict[str, Any], trigger_id: str | None = None) -> dict[str, Any]:
    redacted = redact_trigger_fields(trigger)
    now = _utcnow()
    row = {field: redacted.get(field) for field in DB_FIELDS}
    row["trigger_id"] = trigger_id or row.get("trigger_id")
    row["scrum_type"] = str(row.get("scrum_type") or "poc")
    row["source_id"] = str(row.get("source_id") or row.get("source_path") or "unknown")
    row["event_type"] = str(row.get("event_type") or "uncertainty_marker")
    row["detected_at"] = str(row.get("detected_at") or now)
    row["last_seen_at"] = str(row.get("last_seen_at") or row["detected_at"])
    row["created_at"] = str(row.get("created_at") or row["detected_at"])
    row["ttl_at"] = row.get("ttl_at") or _format_time(_parse_time(row["detected_at"]) + timedelta(days=7))
    row["evidence_count"] = int(row.get("evidence_count") or 1)
    row["normalized_signature"] = str(row.get("normalized_signature") or _sha256(json.dumps(row, sort_keys=True))[:32])
    row["content_hash"] = str(row.get("content_hash") or _sha256(row["normalized_signature"])[:32])
    row["status"] = str(row.get("status") or "pending")
    if row["scrum_type"] not in VALID_SCRUM_TYPES:
        raise ValueError(f"invalid scrum_type: {row['scrum_type']}")
    if row["event_type"] not in VALID_EVENT_TYPES:
        raise ValueError(f"invalid event_type: {row['event_type']}")
    if row["status"] not in VALID_STATUSES:
        raise ValueError(f"invalid status: {row['status']}")
    return row


def _next_trigger_id(conn: sqlite3.Connection, detected_at: str, offset: int = 0) -> str:
    day = (detected_at or _utcnow())[:10]
    prefix = f"ST-{day}-"
    rows = conn.execute(
        "SELECT trigger_id FROM scrum_trigger WHERE trigger_id LIKE ?",
        (f"{prefix}%",),
    ).fetchall()
    max_seq = 0
    for row in rows:
        suffix = str(row["trigger_id"]).removeprefix(prefix)
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    return f"{prefix}{max_seq + offset + 1:04d}"


def save_to_db(triggers: Iterable[dict[str, Any]], db_path: Path | str | None = None) -> dict[str, Any]:
    conn = _db_connect(db_path)
    inserted = 0
    updated = 0
    ids: list[str] = []
    try:
        for offset, trigger in enumerate(triggers):
            existing = conn.execute(
                """
                SELECT trigger_id FROM scrum_trigger
                WHERE scrum_type = ? AND source_id = ? AND normalized_signature = ?
                """,
                (
                    trigger.get("scrum_type"),
                    trigger.get("source_id"),
                    trigger.get("normalized_signature"),
                ),
            ).fetchone()
            trigger_id = existing["trigger_id"] if existing else _next_trigger_id(
                conn, str(trigger.get("detected_at") or _utcnow()), offset
            )
            row = _normalize_trigger_for_db(trigger, trigger_id)
            placeholders = ", ".join("?" for _ in DB_FIELDS)
            columns = ", ".join(DB_FIELDS)
            update_columns = (
                "last_seen_at = excluded.last_seen_at, "
                "ttl_at = excluded.ttl_at, "
                "uncertainty_score = excluded.uncertainty_score, "
                "impact_score = excluded.impact_score, "
                "confidence = excluded.confidence, "
                "evidence_count = scrum_trigger.evidence_count + excluded.evidence_count, "
                "content_hash = excluded.content_hash, "
                "evidence_path_hint = excluded.evidence_path_hint, "
                "source_line_start = excluded.source_line_start, "
                "source_line_end = excluded.source_line_end"
            )
            conn.execute(
                f"""
                INSERT INTO scrum_trigger ({columns})
                VALUES ({placeholders})
                ON CONFLICT(scrum_type, source_id, normalized_signature) DO UPDATE SET
                {update_columns}
                """,
                tuple(row[field] for field in DB_FIELDS),
            )
            ids.append(trigger_id)
            if existing:
                updated += 1
            else:
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    return {"inserted": inserted, "updated": updated, "ids": ids}


def list_triggers(
    db_path: Path | str | None = None,
    *,
    status: str | None = None,
    scrum_type: str | None = None,
) -> list[dict[str, Any]]:
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    if scrum_type is not None and scrum_type not in VALID_SCRUM_TYPES:
        raise ValueError(f"invalid scrum_type: {scrum_type}")
    conn = _db_connect(db_path)
    try:
        where: list[str] = []
        params: list[Any] = []
        if status:
            where.append("status = ?")
            params.append(status)
        if scrum_type:
            where.append("scrum_type = ?")
            params.append(scrum_type)
        sql = "SELECT * FROM scrum_trigger"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY detected_at DESC, trigger_id"
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def get_trigger(db_path: Path | str | None, trigger_id: str) -> dict[str, Any]:
    conn = _db_connect(db_path)
    try:
        row = conn.execute("SELECT * FROM scrum_trigger WHERE trigger_id = ?", (trigger_id,)).fetchone()
        if row is None:
            raise KeyError(f"trigger not found: {trigger_id}")
        return dict(row)
    finally:
        conn.close()


def transition_status(
    trigger_id: str,
    new_status: str,
    owner: str,
    reason: str = "",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    if new_status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {new_status}")
    if not owner:
        raise ValueError("owner is required")
    conn = _db_connect(db_path)
    try:
        row = conn.execute("SELECT status FROM scrum_trigger WHERE trigger_id = ?", (trigger_id,)).fetchone()
        if row is None:
            raise KeyError(f"trigger not found: {trigger_id}")
        current = row["status"]
        if new_status not in TRANSITIONS[current]:
            raise ValueError(f"invalid transition: {current} -> {new_status}")
        resolved_at = _utcnow() if new_status in ("adopted", "rejected", "archived") else None
        status_reason = redact_trigger_fields({"status_reason": reason}).get("status_reason")
        conn.execute(
            """
            UPDATE scrum_trigger
            SET status = ?, status_owner = ?, status_reason = ?, resolved_at = COALESCE(?, resolved_at)
            WHERE trigger_id = ?
            """,
            (new_status, owner, status_reason, resolved_at, trigger_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM scrum_trigger WHERE trigger_id = ?", (trigger_id,)).fetchone()
        return dict(updated)
    finally:
        conn.close()


def check_ttl(
    db_path: Path | str | None = None,
    *,
    apply: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_time = now or datetime.now(timezone.utc)
    conn = _db_connect(db_path)
    actions: list[dict[str, Any]] = []
    try:
        rows = conn.execute("SELECT * FROM scrum_trigger WHERE status != 'archived'").fetchall()
        for row in rows:
            item = dict(row)
            detected_at = _parse_time(item.get("detected_at")) or current_time
            last_seen_at = _parse_time(item.get("last_seen_at")) or detected_at
            status = item["status"]
            target_status = None
            reason = ""

            if current_time - detected_at >= timedelta(days=90):
                target_status = "archived"
                reason = "retention_90d"
            elif status == "pending" and current_time - detected_at >= timedelta(days=7):
                # PLAN-007 は営業日表記だが、CLI は 5 営業日を 7 自然日で近似する。
                target_status = "triaged"
                reason = "pending_5_business_days_approx_7_natural_days"
            elif status == "triaged" and current_time - last_seen_at >= timedelta(days=14):
                # 10 営業日は 14 自然日で近似する。
                target_status = "archived"
                reason = "triaged_10_business_days_approx_14_natural_days"

            if target_status:
                actions.append(
                    {
                        "trigger_id": item["trigger_id"],
                        "from_status": status,
                        "to_status": target_status,
                        "reason": reason,
                    }
                )
        if apply:
            for action in actions:
                conn.execute(
                    """
                    UPDATE scrum_trigger
                    SET status = ?, status_owner = 'system', status_reason = ?, resolved_at = CASE
                        WHEN ? IN ('archived') THEN ?
                        ELSE resolved_at
                    END
                    WHERE trigger_id = ?
                    """,
                    (
                        action["to_status"],
                        action["reason"],
                        action["to_status"],
                        _format_time(current_time),
                        action["trigger_id"],
                    ),
                )
            conn.commit()
    finally:
        conn.close()
    return {"apply": apply, "actions": actions}


def cap_per_sprint(triggers: Iterable[dict[str, Any]], sprint_id: str, cap: int = 5) -> list[dict[str, Any]]:
    scoped = [dict(trigger) for trigger in triggers if str(trigger.get("sprint_id") or "") == str(sprint_id)]
    return sorted(
        scoped,
        key=lambda item: (
            -int(item.get("impact_score") or 0),
            -int(item.get("uncertainty_score") or 0),
            str(item.get("detected_at") or ""),
        ),
    )[:cap]


def _print_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("(empty)")
        return
    print(f"{'ID':<18} {'Status':<9} {'Type':<11} {'Event':<20} Evidence")
    print(f"{'--':<18} {'------':<9} {'----':<11} {'-----':<20} --------")
    for row in rows:
        print(
            f"{row['trigger_id']:<18} {row['status']:<9} {row['scrum_type']:<11} "
            f"{row['event_type']:<20} {row.get('evidence_path_hint') or ''}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HELIX scrum trigger utilities")
    parser.add_argument("--db", default=None, help="helix.db path")
    parser.add_argument("--project-root", default=None, help="project root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect")
    detect_parser.add_argument("--scan", action="append", default=[])
    detect_parser.add_argument("--save", action="store_true")
    detect_parser.add_argument("--json", action="store_true")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=VALID_STATUSES)
    list_parser.add_argument("--type", choices=VALID_SCRUM_TYPES, dest="scrum_type")
    list_parser.add_argument("--json", action="store_true")

    transition_parser = subparsers.add_parser("transition")
    transition_parser.add_argument("--id", required=True, dest="trigger_id")
    transition_parser.add_argument("--status", required=True, choices=("triaged", "adopted", "rejected", "archived"))
    transition_parser.add_argument("--owner", required=True)
    transition_parser.add_argument("--reason", default="")
    transition_parser.add_argument("--json", action="store_true")

    ttl_parser = subparsers.add_parser("ttl")
    ttl_parser.add_argument("--apply", action="store_true")
    ttl_parser.add_argument("--json", action="store_true")

    evaluate_parser = subparsers.add_parser("evaluate")
    evaluate_parser.add_argument("--id", required=True, dest="trigger_id")
    evaluate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "detect":
            triggers = detect_triggers(args.scan, project_root=args.project_root)
            saved = save_to_db(triggers, args.db) if args.save else None
            if args.json:
                print(json.dumps({"triggers": triggers, "save": saved}, ensure_ascii=False, indent=2))
            else:
                print(f"detected: {len(triggers)}")
                _print_table([{**trigger, "trigger_id": trigger.get("trigger_id") or "(unsaved)"} for trigger in triggers])
                if saved:
                    print(f"saved: inserted={saved['inserted']} updated={saved['updated']}")
            return 0
        if args.command == "list":
            rows = list_triggers(args.db, status=args.status, scrum_type=args.scrum_type)
            if args.json:
                print(json.dumps({"triggers": rows}, ensure_ascii=False, indent=2))
            else:
                _print_table(rows)
            return 0
        if args.command == "transition":
            row = transition_status(args.trigger_id, args.status, args.owner, args.reason, args.db)
            if args.json:
                print(json.dumps(row, ensure_ascii=False, indent=2))
            else:
                print(f"transitioned: {row['trigger_id']} {row['status']}")
            return 0
        if args.command == "ttl":
            result = check_ttl(args.db, apply=args.apply)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"ttl actions: {len(result['actions'])}")
                for action in result["actions"]:
                    print(
                        f"  {action['trigger_id']}: {action['from_status']} -> "
                        f"{action['to_status']} ({action['reason']})"
                    )
            return 0
        if args.command == "evaluate":
            row = get_trigger(args.db, args.trigger_id)
            result = {**row, "evaluation": evaluate_quadrant(row)}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                evaluation = result["evaluation"]
                print(f"id: {row['trigger_id']}")
                print(f"quadrant: {evaluation['quadrant']}")
                print(f"eligible: {str(evaluation['eligible']).lower()}")
                print(f"recommended_scrum_type: {evaluation['recommended_scrum_type']}")
                print(f"priority_score: {evaluation['priority_score']}")
            return 0
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=os.sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
