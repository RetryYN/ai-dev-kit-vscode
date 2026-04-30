from __future__ import annotations

import copy
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import helix_db
import yaml_parser
from redaction import REDACTED, redact_value


SEVERITY_TO_LEVEL = {
    "critical": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
}

LEVEL_TO_CARRY_RULE = {
    "P0": "stop",
    "P1": "carry-with-pm-approval",
    "P2": "auto-carry",
    "P3": "optional",
}

LEVEL_TO_DEFAULT_WEIGHT = {
    "P0": 1.00,
    "P1": 0.70,
    "P2": 0.35,
    "P3": 0.10,
}

VALID_STATUSES = ("open", "carried", "resolved", "abandoned")
VALID_DIMENSIONS = ("density", "depth", "breadth", "accuracy", "maintainability")
VALID_ADJUSTMENT_GATES = tuple(f"G{index}" for index in range(2, 12))
DEFAULT_REDACTION_POLICY = "cli/lib/redaction.py + observability denylist"

SECRET_EXTRA_PATTERNS = (
    re.compile(r"\bAKIA[A-Z0-9]{12,}\b"),
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "redaction": {"applied": True, "policy": DEFAULT_REDACTION_POLICY},
        "findings": [],
    }


def _ensure_payload(data: dict[str, Any] | None) -> dict[str, Any]:
    payload = _default_payload()
    if data:
        payload.update(data)
    payload["version"] = int(payload.get("version") or 1)
    redaction = payload.get("redaction")
    if not isinstance(redaction, dict):
        redaction = {}
    redaction["applied"] = True
    redaction.setdefault("policy", DEFAULT_REDACTION_POLICY)
    payload["redaction"] = redaction
    findings = payload.get("findings")
    payload["findings"] = findings if isinstance(findings, list) else []
    return payload


def _normalize_redacted_scalar(value: Any) -> Any:
    if isinstance(value, list) and value == ["REDACTED"]:
        return REDACTED
    if isinstance(value, dict):
        return {key: _normalize_redacted_scalar(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_redacted_scalar(item) for item in value]
    return value


def _quote_redacted_scalar(value: Any) -> Any:
    if value == REDACTED:
        return f'"{REDACTED}"'
    if isinstance(value, dict):
        return {key: _quote_redacted_scalar(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_quote_redacted_scalar(item) for item in value]
    return value


def _redact_text_fields(finding: dict[str, Any]) -> dict[str, Any]:
    item = dict(finding)
    for field in ("title", "body", "recommendation"):
        if field in item:
            item[field] = redact_value(
                item[field],
                key_hint=field,
                extra_patterns=SECRET_EXTRA_PATTERNS,
                tuple_as_list=True,
            )
    return item


def _require_non_empty(value: Any, field_name: str) -> str:
    if value is None or str(value).strip() == "":
        raise ValueError(f"{field_name} is required")
    return str(value)


def _validate_level(level: str) -> str:
    if level not in LEVEL_TO_CARRY_RULE:
        raise ValueError(f"invalid level: {level}")
    return level


def _validate_severity(severity: str) -> str:
    if severity not in SEVERITY_TO_LEVEL:
        raise ValueError(f"invalid severity: {severity}")
    return severity


def _validate_carry_rule(carry_rule: str) -> str:
    if carry_rule not in set(LEVEL_TO_CARRY_RULE.values()):
        raise ValueError(f"invalid carry_rule: {carry_rule}")
    return carry_rule


def _validate_status(status: str) -> str:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    return status


def _validate_gate(gate: str) -> str:
    if gate not in VALID_ADJUSTMENT_GATES:
        raise ValueError(f"invalid gate: {gate}")
    return gate


def _validate_dimension(dimension: str) -> str:
    if dimension not in VALID_DIMENSIONS:
        raise ValueError(f"invalid dimension: {dimension}")
    return dimension


def _next_finding_id(findings: list[dict[str, Any]], plan_id: str, phase: str) -> str:
    prefix = f"DF-{plan_id}-{phase}-"
    max_seq = 0
    for finding in findings:
        finding_id = str(finding.get("id", ""))
        if not finding_id.startswith(prefix):
            continue
        suffix = finding_id.removeprefix(prefix)
        if suffix.isdigit():
            max_seq = max(max_seq, int(suffix))
    return f"{prefix}{max_seq + 1:03d}"


def _find_index(findings: list[dict[str, Any]], finding_id: str) -> int:
    for index, finding in enumerate(findings):
        if finding.get("id") == finding_id:
            return index
    raise KeyError(f"finding not found: {finding_id}")


def _target_string(finding: dict[str, Any]) -> str:
    target = finding.get("target") if isinstance(finding.get("target"), dict) else {}
    return f"{target.get('plan_id')}:{target.get('phase')}"


def _event_db_path(yaml_path: Path, db_path: Path | str | None) -> Path | None:
    if db_path is not None:
        return Path(db_path)
    parent = yaml_path.parent
    if parent.name == "audit" and parent.parent.name == ".helix":
        return parent.parent / "helix.db"
    return None


def _insert_audit_event(
    yaml_path: Path,
    operation: str,
    finding: dict[str, Any],
    *,
    db_path: Path | str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    target_db = _event_db_path(yaml_path, db_path)
    if target_db is None:
        return
    data = {
        "finding_id": finding.get("id"),
        "plan_id": finding.get("plan_id"),
        "level": finding.get("level"),
        "status": finding.get("status"),
    }
    if extra:
        data.update(extra)
    helix_db.insert_event(str(target_db), f"deferred_finding.{operation}", data)


def _db_connect(db_path: Path | str):
    if hasattr(helix_db, "_automation_conn"):
        return helix_db._automation_conn(db_path)
    conn = helix_db.get_connection(db_path)
    helix_db.migrate(conn)
    return conn


def _db_row_from_finding(finding: dict[str, Any], synced_at: str) -> dict[str, Any]:
    origin = finding.get("origin") if isinstance(finding.get("origin"), dict) else {}
    current = finding.get("current") if isinstance(finding.get("current"), dict) else {}
    target = finding.get("target") if isinstance(finding.get("target"), dict) else {}
    approval = finding.get("pm_approval") if isinstance(finding.get("pm_approval"), dict) else {}
    return {
        "id": _require_non_empty(finding.get("id"), "id"),
        "plan_id": _require_non_empty(finding.get("plan_id"), "plan_id"),
        "origin_plan_id": _require_non_empty(origin.get("plan_id"), "origin.plan_id"),
        "origin_phase": _require_non_empty(origin.get("phase"), "origin.phase"),
        "current_plan_id": _require_non_empty(current.get("plan_id"), "current.plan_id"),
        "current_phase": _require_non_empty(current.get("phase"), "current.phase"),
        "target_plan_id": target.get("plan_id"),
        "target_phase": target.get("phase"),
        "level": _validate_level(str(finding.get("level"))),
        "carry_rule": _validate_carry_rule(str(finding.get("carry_rule"))),
        "phase": _require_non_empty(finding.get("phase"), "phase"),
        "source": str(finding.get("source") or ""),
        "severity": _validate_severity(str(finding.get("severity"))),
        "status": _validate_status(str(finding.get("status"))),
        "weight": float(finding.get("accuracy_impact_weight", finding.get("weight", 0.0))),
        "created_at": _require_non_empty(finding.get("created_at"), "created_at"),
        "resolved_at": finding.get("resolved_at"),
        "pm_approved_by": approval.get("approved_by"),
        "pm_approved_at": approval.get("approved_at"),
        "pm_reason": approval.get("reason"),
        "yaml_synced_at": synced_at,
    }


def _finding_from_db_row(row: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    finding = dict(existing or {})
    finding.update(
        {
            "id": row["id"],
            "plan_id": row["plan_id"],
            "origin": {"plan_id": row["origin_plan_id"], "phase": row["origin_phase"]},
            "current": {"plan_id": row["current_plan_id"], "phase": row["current_phase"]},
            "target": {"plan_id": row["target_plan_id"], "phase": row["target_phase"]},
            "level": row["level"],
            "carry_rule": row["carry_rule"],
            "phase": row["phase"],
            "source": row["source"],
            "severity": row["severity"],
            "status": row["status"],
            "created_at": row["created_at"],
            "resolved_at": row["resolved_at"],
            "accuracy_impact_weight": row["weight"],
            "pm_approval": {
                "required": row["level"] in ("P0", "P1"),
                "approved_by": row["pm_approved_by"],
                "approved_at": row["pm_approved_at"],
                "reason": row["pm_reason"],
            },
        }
    )
    finding.setdefault("title", "")
    finding.setdefault("body", "")
    finding.setdefault("recommendation", "")
    finding.setdefault("dimension_scores", [])
    finding.setdefault("carry_chain", [])
    return finding


def load_findings(yaml_path: Path) -> dict[str, Any]:
    path = Path(yaml_path)
    if not path.exists():
        return _default_payload()
    text = path.read_text(encoding="utf-8")
    data = yaml_parser.parse_yaml(text)
    return _normalize_redacted_scalar(_ensure_payload(data))


def save_findings(yaml_path: Path, data: dict[str, Any]) -> None:
    path = Path(yaml_path)
    payload = _ensure_payload(copy.deepcopy(data))
    payload["findings"] = [_redact_text_fields(finding) for finding in payload["findings"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    output = yaml_parser.dump_yaml(_quote_redacted_scalar(payload)) + "\n"
    tmp_path = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    tmp_path.write_text(output, encoding="utf-8")
    os.replace(tmp_path, path)


def add_finding(yaml_path: Path, finding: dict[str, Any], db_path: Path | str | None = None) -> str:
    path = Path(yaml_path)
    payload = load_findings(path)
    findings = payload["findings"]
    item = _redact_text_fields(finding)
    plan_id = _require_non_empty(item.get("plan_id"), "plan_id")
    phase = _require_non_empty(item.get("phase"), "phase")
    severity = _validate_severity(str(item.get("severity", "medium")))
    level = _validate_level(str(item.get("level") or SEVERITY_TO_LEVEL.get(severity, "")))
    now = _utcnow()
    item["id"] = item.get("id") or _next_finding_id(findings, plan_id, phase)
    item["plan_id"] = plan_id
    item["phase"] = phase
    item["severity"] = severity
    item["level"] = level
    item["carry_rule"] = item.get("carry_rule") or LEVEL_TO_CARRY_RULE[level]
    item["origin"] = item.get("origin") or {"plan_id": plan_id, "phase": phase}
    item["current"] = item.get("current") or {"plan_id": plan_id, "phase": phase}
    if "target" not in item:
        item["target"] = {"plan_id": plan_id, "phase": phase}
    item["source"] = item.get("source") or ""
    item["status"] = _validate_status(str(item.get("status") or "open"))
    item["created_at"] = item.get("created_at") or now
    item["resolved_at"] = item.get("resolved_at")
    item["accuracy_impact_weight"] = float(
        item.get("accuracy_impact_weight", LEVEL_TO_DEFAULT_WEIGHT[level])
    )
    item["pm_approval"] = item.get("pm_approval") or {
        "required": level in ("P0", "P1"),
        "approved_by": None,
        "approved_at": None,
        "reason": None,
    }
    item["carry_chain"] = item.get("carry_chain") or []
    item.setdefault("dimension_scores", [])
    findings.append(item)
    save_findings(path, payload)
    _insert_audit_event(path, "add", item, db_path=db_path)
    return str(item["id"])


def update_finding(
    yaml_path: Path,
    finding_id: str,
    db_path: Path | str | None = None,
    **patch: Any,
) -> dict[str, Any]:
    path = Path(yaml_path)
    payload = load_findings(path)
    findings = payload["findings"]
    index = _find_index(findings, finding_id)
    item = dict(findings[index])
    from_status = str(item.get("status", "open"))
    patch = _redact_text_fields(patch)
    operation = "update"
    if "status" in patch:
        to_status = _validate_status(str(patch["status"]))
        patch["status"] = to_status
        if to_status in ("resolved", "abandoned"):
            patch.setdefault("resolved_at", _utcnow())
            operation = "resolve" if to_status == "resolved" else "abandon"
    item.update(patch)
    findings[index] = item
    save_findings(path, payload)
    _insert_audit_event(
        path,
        operation,
        item,
        db_path=db_path,
        extra={"from_status": from_status, "to_status": item.get("status")},
    )
    return item


def list_findings(
    yaml_path: Path,
    plan_id: str | None = None,
    level: str | None = None,
    status: str | None = None,
    phase: str | None = None,
) -> list[dict[str, Any]]:
    findings = load_findings(Path(yaml_path))["findings"]
    result = []
    for finding in findings:
        if plan_id is not None and finding.get("plan_id") != plan_id:
            continue
        if level is not None and finding.get("level") != level:
            continue
        if status is not None and finding.get("status") != status:
            continue
        if phase is not None and finding.get("phase") != phase:
            continue
        result.append(dict(finding))
    return result


def carry_finding(
    yaml_path: Path,
    finding_id: str,
    target_plan_id: str,
    target_phase: str,
    approved_by: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    path = Path(yaml_path)
    payload = load_findings(path)
    findings = payload["findings"]
    index = _find_index(findings, finding_id)
    item = dict(findings[index])
    if item.get("level") == "P1" and not approved_by:
        raise ValueError("approved_by is required to carry P1 findings")
    from_status = str(item.get("status", "open"))
    from_target = _target_string(item)
    target_plan_id = _require_non_empty(target_plan_id, "target_plan_id")
    target_phase = _require_non_empty(target_phase, "target_phase")
    item["target"] = {"plan_id": target_plan_id, "phase": target_phase}
    item["current"] = {"plan_id": target_plan_id, "phase": target_phase}
    item["status"] = "carried"
    approval = item.get("pm_approval") if isinstance(item.get("pm_approval"), dict) else {}
    if approved_by:
        approval["approved_by"] = approved_by
        approval["approved_at"] = _utcnow()
    approval.setdefault("required", item.get("level") in ("P0", "P1"))
    approval.setdefault("reason", None)
    item["pm_approval"] = approval
    carry_chain = item.get("carry_chain") if isinstance(item.get("carry_chain"), list) else []
    carry_chain.append(
        {
            "from": from_target,
            "to": f"{target_plan_id}:{target_phase}",
            "status": "carried",
            "approved_by": approved_by,
            "approved_at": approval.get("approved_at"),
        }
    )
    item["carry_chain"] = carry_chain
    findings[index] = item
    save_findings(path, payload)
    _insert_audit_event(
        path,
        "carry",
        item,
        db_path=db_path,
        extra={
            "from_status": from_status,
            "to_status": "carried",
            "target_plan_id": target_plan_id,
            "target_phase": target_phase,
            "approved_by": approved_by,
        },
    )
    return item


def sync_yaml_to_db(yaml_path: Path, db_path: Path) -> dict[str, int]:
    payload = load_findings(Path(yaml_path))
    synced_at = _utcnow()
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    conn = _db_connect(db_path)
    try:
        for finding in payload["findings"]:
            row = _db_row_from_finding(finding, synced_at)
            existing = conn.execute(
                "SELECT * FROM deferred_findings WHERE id = ?",
                (row["id"],),
            ).fetchone()
            if existing is None:
                columns = list(row)
                placeholders = ", ".join("?" for _ in columns)
                conn.execute(
                    f"INSERT INTO deferred_findings ({', '.join(columns)}) VALUES ({placeholders})",
                    tuple(row[column] for column in columns),
                )
                stats["inserted"] += 1
                continue

            existing_dict = dict(existing)
            comparable = {key: row[key] for key in row if key != "yaml_synced_at"}
            current = {key: existing_dict[key] for key in comparable}
            if current == comparable:
                conn.execute(
                    "UPDATE deferred_findings SET yaml_synced_at = ? WHERE id = ?",
                    (synced_at, row["id"]),
                )
                stats["unchanged"] += 1
                continue

            assignments = ", ".join(f"{column} = ?" for column in row if column != "id")
            values = [row[column] for column in row if column != "id"]
            values.append(row["id"])
            conn.execute(f"UPDATE deferred_findings SET {assignments} WHERE id = ?", values)
            stats["updated"] += 1
        conn.commit()
        return stats
    finally:
        conn.close()


def sync_db_to_yaml(db_path: Path, yaml_path: Path) -> dict[str, int]:
    payload = load_findings(Path(yaml_path))
    existing_by_id = {finding.get("id"): finding for finding in payload["findings"]}
    stats = {"inserted": 0, "updated": 0, "unchanged": 0}
    conn = _db_connect(db_path)
    try:
        rows = [
            dict(row)
            for row in conn.execute("SELECT * FROM deferred_findings ORDER BY created_at, id").fetchall()
        ]
    finally:
        conn.close()

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        current = existing_by_id.get(row["id"])
        updated = _finding_from_db_row(row, current)
        merged.append(updated)
        seen.add(row["id"])
        if current is None:
            stats["inserted"] += 1
        elif current == updated:
            stats["unchanged"] += 1
        else:
            stats["updated"] += 1
    for finding in payload["findings"]:
        if finding.get("id") not in seen:
            merged.append(finding)
    payload["findings"] = merged
    save_findings(Path(yaml_path), payload)
    return stats


def adjust_score(
    db_path: Path,
    finding_id: str,
    gate: str,
    dimension: str,
    penalty: float | None = None,
) -> int:
    gate = _validate_gate(gate)
    dimension = _validate_dimension(dimension)
    conn = _db_connect(db_path)
    try:
        finding = conn.execute(
            "SELECT id, plan_id, weight FROM deferred_findings WHERE id = ?",
            (finding_id,),
        ).fetchone()
        if finding is None:
            raise KeyError(f"finding not found: {finding_id}")
        effective_penalty = float(finding["weight"] if penalty is None else penalty)
        conn.execute(
            "INSERT INTO accuracy_score_adjustments "
            "(finding_id, plan_id, gate, dimension, penalty, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (finding_id, finding["plan_id"], gate, dimension, effective_penalty, _utcnow()),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        return int(row_id)
    finally:
        conn.close()


def compute_effective_score(db_path: Path, plan_id: str, gate: str | None = None) -> list[dict[str, Any]]:
    if gate is not None:
        _validate_gate(gate)
    conn = _db_connect(db_path)
    try:
        params: list[Any] = [plan_id]
        sql = "SELECT * FROM accuracy_score_effective WHERE plan_id = ?"
        if gate is not None:
            sql += " AND gate = ?"
            params.append(gate)
        sql += " ORDER BY gate, dimension, accuracy_score_id"
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()
