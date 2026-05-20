#!/usr/bin/env python3
"""契約: PLAN-092 §5 / §7 / §8

PLAN/ADR frontmatter を parse し、v35 plan registry schema へ upsert する。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import yaml

try:
    from .migrations import v35_plan_registry
except ImportError:  # pragma: no cover
    from migrations import v35_plan_registry


TARGET_PREFIXES = ("PLAN-", "ADR-")
REQUIRED_FIELDS = ("plan_id", "kind", "layer")
FRONTMATTER_DELIMITER = "---"


def _warn(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _is_target_document(path: Path) -> bool:
    return path.suffix == ".md" and path.name.startswith(TARGET_PREFIXES)


def _load_frontmatter_block(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return "\n".join(lines[1:index])
    return None


def _normalize_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _compact_json(payload: dict) -> str:
    normalized = {key: value for key, value in payload.items() if not key.startswith("_")}
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)


def _insert_failure_log(conn, *, doc_path: str, failure_type: str, context: str, plan_id: str | None = None) -> None:
    conn.execute(
        """
        INSERT INTO failure_log (failure_type, context, plan_id)
        VALUES (?, ?, ?)
        """,
        (failure_type, context, plan_id),
    )


def _delete_related_rows(conn, plan_id: str) -> None:
    for table_name in (
        "plan_dependencies",
        "plan_agent_slots",
        "plan_references",
        "plan_generates",
    ):
        conn.execute(f"DELETE FROM {table_name} WHERE plan_id = ?", (plan_id,))


def _iter_dependencies(frontmatter: dict) -> list[tuple[str, str]]:
    dependencies = frontmatter.get("dependencies") or {}
    if not isinstance(dependencies, dict):
        return []

    rows: list[tuple[str, str]] = []
    for dep_type in ("requires", "parent", "blocks"):
        for dep_plan_id in _normalize_list(dependencies.get(dep_type)):
            if isinstance(dep_plan_id, str) and dep_plan_id.strip():
                rows.append((dep_type, dep_plan_id.strip()))
    return rows


def _iter_agent_slots(frontmatter: dict) -> list[tuple[str, str | None, int]]:
    rows: list[tuple[str, str | None, int]] = []
    for index, slot in enumerate(_normalize_list(frontmatter.get("agent_slots"))):
        if not isinstance(slot, dict):
            continue
        role = str(slot.get("role") or "").strip()
        if not role:
            continue
        slot_label = slot.get("slot_label")
        rows.append((role, str(slot_label).strip() if isinstance(slot_label, str) else None, index))
    return rows


def _iter_references(frontmatter: dict) -> list[tuple[str, str | None, str]]:
    rows: list[tuple[str, str | None, str]] = []

    def append_many(values, ref_type: str) -> None:
        for value in _normalize_list(values):
            if isinstance(value, str) and value.strip():
                rows.append((value.strip(), None, ref_type))
            elif isinstance(value, dict):
                doc_path = str(value.get("doc_path") or "").strip()
                if not doc_path:
                    continue
                section = value.get("section")
                rows.append((doc_path, str(section).strip() if isinstance(section, str) else None, ref_type))

    append_many(frontmatter.get("related_docs"), "related_docs")
    append_many(frontmatter.get("related_memories"), "related_memories")
    append_many(frontmatter.get("test_design_ref"), "test_design_ref")
    return rows


def _iter_generates(frontmatter: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for artifact in _normalize_list(frontmatter.get("generates")):
        if not isinstance(artifact, dict):
            continue
        artifact_path = str(artifact.get("artifact_path") or "").strip()
        artifact_type = str(artifact.get("artifact_type") or "").strip()
        if artifact_path and artifact_type:
            rows.append((artifact_path, artifact_type))
    return rows


def parse_frontmatter(filepath: str) -> dict | None:
    """YAML frontmatter を parse して dict を返す。非対象 file は空 dict。"""
    path = Path(filepath)
    if not _is_target_document(path):
        return {}

    try:
        frontmatter_block = _load_frontmatter_block(path)
    except OSError as exc:
        _warn(f"frontmatter read failed: {path} ({exc})")
        return None

    if frontmatter_block is None:
        _warn(f"frontmatter missing: {path}")
        return None

    try:
        loaded = yaml.safe_load(frontmatter_block) or {}
    except yaml.YAMLError as exc:
        _warn(f"frontmatter parse failed: {path} ({exc})")
        return None

    if not isinstance(loaded, dict):
        _warn(f"frontmatter must be a mapping: {path}")
        return None

    warnings = [field for field in REQUIRED_FIELDS if not loaded.get(field)]
    if warnings:
        loaded["_warnings"] = [f"missing required field: {field}" for field in warnings]
        _warn(f"missing required fields in {path}: {', '.join(warnings)}")

    return loaded


def upsert_plan(conn, frontmatter: dict | None, doc_path: str) -> dict:
    """plan_registry と関連 table に upsert する。戻り値: {plan_id, status, counts}"""
    counts = {"dependencies": 0, "agent_slots": 0, "references": 0, "generates": 0}
    if not frontmatter:
        with conn:
            _insert_failure_log(
                conn,
                doc_path=doc_path,
                failure_type="parse_error",
                context=json.dumps({"doc_path": doc_path, "reason": "frontmatter is empty"}, ensure_ascii=False),
            )
        return {"plan_id": None, "status": "parse_error", "counts": counts}

    plan_id = str(frontmatter.get("plan_id") or "").strip()
    missing = [field for field in REQUIRED_FIELDS if not frontmatter.get(field)]
    if not plan_id or missing:
        with conn:
            _insert_failure_log(
                conn,
                doc_path=doc_path,
                failure_type="parse_error",
                plan_id=plan_id or None,
                context=json.dumps(
                    {"doc_path": doc_path, "reason": f"missing required fields: {', '.join(missing)}"},
                    ensure_ascii=False,
                ),
            )
        return {"plan_id": plan_id or None, "status": "parse_error", "counts": counts}

    dependencies = _iter_dependencies(frontmatter)
    agent_slots = _iter_agent_slots(frontmatter)
    references = _iter_references(frontmatter)
    generates = _iter_generates(frontmatter)

    registry_payload = (
        plan_id,
        str(frontmatter.get("title") or ""),
        str(frontmatter.get("kind") or ""),
        str(frontmatter.get("layer") or ""),
        str(frontmatter.get("drive") or ""),
        str(frontmatter.get("status") or "draft"),
        frontmatter.get("size"),
        frontmatter.get("owner"),
        ", ".join(str(item).strip() for item in _normalize_list(frontmatter.get("related_adr")) if str(item).strip()),
        _compact_json(frontmatter),
        doc_path,
    )

    with conn:
        conn.execute(
            """
            INSERT INTO plan_registry (
                plan_id, title, kind, layer, drive, status, size, owner,
                related_adr, frontmatter_json, doc_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(plan_id) DO UPDATE SET
                title = excluded.title,
                kind = excluded.kind,
                layer = excluded.layer,
                drive = excluded.drive,
                status = excluded.status,
                size = excluded.size,
                owner = excluded.owner,
                related_adr = excluded.related_adr,
                frontmatter_json = excluded.frontmatter_json,
                doc_path = excluded.doc_path,
                updated_at = datetime('now')
            """,
            registry_payload,
        )
        _delete_related_rows(conn, plan_id)

        for dep_type, dep_plan_id in dependencies:
            conn.execute(
                """
                INSERT INTO plan_dependencies (plan_id, dep_type, dep_plan_id)
                VALUES (?, ?, ?)
                """,
                (plan_id, dep_type, dep_plan_id),
            )
        for role, slot_label, slot_index in agent_slots:
            conn.execute(
                """
                INSERT INTO plan_agent_slots (plan_id, role, slot_label, slot_index)
                VALUES (?, ?, ?, ?)
                """,
                (plan_id, role, slot_label, slot_index),
            )
        for ref_path, section, ref_type in references:
            conn.execute(
                """
                INSERT INTO plan_references (plan_id, doc_path, section, ref_type)
                VALUES (?, ?, ?, ?)
                """,
                (plan_id, ref_path, section, ref_type),
            )
        for artifact_path, artifact_type in generates:
            conn.execute(
                """
                INSERT INTO plan_generates (plan_id, artifact_path, artifact_type)
                VALUES (?, ?, ?)
                """,
                (plan_id, artifact_path, artifact_type),
            )

    counts["dependencies"] = len(dependencies)
    counts["agent_slots"] = len(agent_slots)
    counts["references"] = len(references)
    counts["generates"] = len(generates)
    return {"plan_id": plan_id, "status": str(frontmatter.get("status") or "draft"), "counts": counts}


def detect_cycle(conn, plan_id: str) -> list[str]:
    """Sprint .1b で実装予定。Sprint .1a は stub として空 list を返す。"""
    del conn, plan_id
    return []


def _resolve_db_path(filepath: str) -> Path:
    path = Path(filepath).resolve()
    for parent in path.parents:
        helix_dir = parent / ".helix"
        if helix_dir.is_dir():
            return helix_dir / "helix.db"
    return Path.cwd() / ".helix" / "helix.db"


def main(filepath: str, mode: str = "upsert") -> int:
    """CLI エントリポイント。mode: upsert / check / validate"""
    frontmatter = parse_frontmatter(filepath)
    if frontmatter is None:
        return 0
    if frontmatter == {}:
        return 0
    if mode in {"check", "validate"}:
        return 0
    if mode != "upsert":
        print(f"ERROR: unsupported mode: {mode}", file=sys.stderr)
        return 1

    db_path = _resolve_db_path(filepath)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        v35_plan_registry.migrate_v34_to_v35(conn)
        result = upsert_plan(conn, frontmatter, filepath)
    except sqlite3.Error as exc:
        _warn(f"plan_registry upsert failed: {filepath} ({exc})")
        return 0
    finally:
        conn.close()

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PLAN / ADR frontmatter parser")
    parser.add_argument("filepath")
    parser.add_argument("--mode", default="upsert")
    args = parser.parse_args()
    sys.exit(main(args.filepath, mode=args.mode))
