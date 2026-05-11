from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import helix_db

try:
    from ..yaml_parser import parse_yaml  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script execution
    from yaml_parser import parse_yaml  # type: ignore


STUB_REASON = "not_implemented yet, see PLAN-063 W-3〜W-9"


@dataclass(slots=True)
class DetectorResult:
    verdict: Literal["passed", "failed", "blocked"]
    findings: list[dict[str, Any]]
    cost_ms: int
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["findings"] = list(self.findings)
        payload["raw"] = dict(self.raw)
        return payload


class BaseDetector:
    id: str = ""
    name: str = ""
    phase_gate: str | None = None
    kind: str = "stub"

    def run(self, db_path: str | Path) -> DetectorResult:  # pragma: no cover - overridden in stubs
        return DetectorResult(
            verdict="blocked",
            findings=[],
            cost_ms=0,
            raw={"reason": STUB_REASON},
        )


def load_config(db_path: str | Path | None = None) -> dict[str, Any]:
    target_db = Path(db_path or helix_db.resolve_default_db_path())
    config_path = target_db.parent / "detect-config.yaml"
    if not config_path.exists():
        return {}
    try:
        loaded = parse_yaml(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _ensure_detector_runs_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS detector_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            axis_id TEXT NOT NULL,
            detector_name TEXT NOT NULL,
            phase_gate TEXT,
            verdict TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            cost_ms INTEGER NOT NULL,
            raw_json TEXT NOT NULL,
            config_json TEXT NOT NULL,
            command TEXT NOT NULL,
            db_path TEXT NOT NULL
        )
        """
    )


def record_detector_run(
    db_path: str | Path,
    detector: BaseDetector,
    result: DetectorResult,
    *,
    config: dict[str, Any] | None = None,
    command: str = "run",
) -> int:
    target_db = Path(db_path)
    target_db.parent.mkdir(parents=True, exist_ok=True)
    helix_db._prepare_db_path(str(target_db))
    conn = helix_db.get_connection(target_db)
    try:
        _ensure_detector_runs_table(conn)
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "axis_id": detector.id,
            "detector_name": detector.name,
            "phase_gate": detector.phase_gate,
            "verdict": result.verdict,
            "findings_json": json.dumps(result.findings, ensure_ascii=False, sort_keys=True),
            "cost_ms": int(result.cost_ms),
            "raw_json": json.dumps(result.raw, ensure_ascii=False, sort_keys=True),
            "config_json": json.dumps(config or {}, ensure_ascii=False, sort_keys=True),
            "command": command,
            "db_path": str(target_db),
        }
        conn.execute(
            """
            INSERT INTO detector_runs (
                recorded_at, axis_id, detector_name, phase_gate, verdict,
                findings_json, cost_ms, raw_json, config_json, command, db_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(payload.values()),
        )
        conn.commit()
        row = conn.execute("SELECT last_insert_rowid()").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()

