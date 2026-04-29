"""A1 state machine: decisions.yaml → audit_decisions / import_runs 同期。

PLAN-002 v3-v5 で凍結された Case A/B/C ロジック:
- Case A: 同一 (candidate_id, schema_version, scope_hash, decision_hash) → no-op
- Case B: 同一 (candidate_id, schema_version, scope_hash) で異 decision_hash
         → 旧 active 行を historical 化 + 新 active INSERT
- Case C: 異 scope_hash → 旧 active を historical 化 + 新 active INSERT
- new: 全く新しい entry → 単純 INSERT

Transaction 境界 (PLAN-002 v5 で凍結):
- Step 1 (trx 1): import_runs INSERT status='started' → COMMIT
- Step 2 (trx 2): audit_decisions INSERT/UPDATE 全部 → COMMIT or ROLLBACK
- Step 3 (success): import_runs UPDATE status='success' + completed_at + imported_rows → COMMIT
- Step 4 (failed): import_runs UPDATE status='failed' + error_summary → COMMIT
"""
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

_LIB_DIR = Path(__file__).parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

import audit_hash  # noqa: E402
import audit_validator  # noqa: E402
import helix_db  # noqa: E402


@dataclass
class DecisionClassification:
    decision: dict
    case: Literal["case_a", "case_b", "case_c", "new", "error"]
    reason: str = ""
    existing_decision_id: int | None = None


@dataclass
class DryRunReport:
    classifications: list[DecisionClassification] = field(default_factory=list)
    case_counts: dict[str, int] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.validation_errors) > 0 or any(
            c.case == "error" for c in self.classifications
        )


@dataclass
class ImportResult:
    run_id: str
    success: bool
    imported_rows: int
    error_summary: str | None = None
    case_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class VerifySyncResult:
    in_sync: bool
    yaml_count: int
    db_active_count: int
    missing_in_db: list[str] = field(default_factory=list)
    extra_in_db: list[str] = field(default_factory=list)
    hash_mismatch: list[str] = field(default_factory=list)


class A1ImportEngine:
    def __init__(self, db_path: str, decisions_yaml_path):
        self.db_path = str(db_path)
        self.yaml_path = Path(decisions_yaml_path)

    def _classify_decision(
        self, conn, decision: dict
    ) -> DecisionClassification:
        """1 decision を Case A/B/C/new に分類 (DB query)。"""
        decision_hash = audit_hash.compute_decision_hash(decision)
        candidate_id = decision["candidate_id"]
        schema_version = decision["schema_version"]
        scope_hash = decision["scope_hash"]

        # Case A: 同一 4 組合せ existing
        row = conn.execute(
            "SELECT id, status FROM audit_decisions "
            "WHERE candidate_id=? AND schema_version=? "
            "AND scope_hash=? AND decision_hash=?",
            (candidate_id, schema_version, scope_hash, decision_hash),
        ).fetchone()
        if row:
            return DecisionClassification(
                decision=decision,
                case="case_a",
                reason="既存と同一 decision_hash、no-op",
                existing_decision_id=row[0],
            )

        # Case B: 同一 (cand, sv, scope) で active かつ異 decision_hash
        row = conn.execute(
            "SELECT id FROM audit_decisions "
            "WHERE candidate_id=? AND schema_version=? "
            "AND scope_hash=? AND status='active'",
            (candidate_id, schema_version, scope_hash),
        ).fetchone()
        if row:
            return DecisionClassification(
                decision=decision,
                case="case_b",
                reason="同一 scope_hash で decision 内容が変更",
                existing_decision_id=row[0],
            )

        # Case C: 異 scope_hash で同一 (cand, sv) active 行
        row = conn.execute(
            "SELECT id, scope_hash FROM audit_decisions "
            "WHERE candidate_id=? AND schema_version=? "
            "AND status='active'",
            (candidate_id, schema_version),
        ).fetchone()
        if row:
            return DecisionClassification(
                decision=decision,
                case="case_c",
                reason=f"scope_hash 変更 (旧: {row[1]} → 新: {scope_hash})",
                existing_decision_id=row[0],
            )

        # new: 全く新しい
        return DecisionClassification(
            decision=decision, case="new", reason="新規"
        )

    def dry_run(self) -> DryRunReport:
        """validation + Case A/B/C 判定 (実 INSERT なし)。"""
        report = DryRunReport()

        validation = audit_validator.validate_decisions_yaml(self.yaml_path)
        if not validation.success:
            report.validation_errors = validation.errors
            return report

        conn = helix_db._connect(self.db_path)
        try:
            helix_db._ensure_schema(conn)
            for decision in validation.decisions:
                cls = self._classify_decision(conn, decision)
                report.classifications.append(cls)
                report.case_counts[cls.case] = (
                    report.case_counts.get(cls.case, 0) + 1
                )
        finally:
            conn.close()

        return report

    def import_sync(self) -> ImportResult:
        """実 import 実行 (transaction 境界分離)。"""
        run_id = str(uuid.uuid4())
        now_epoch = int(time.time())

        validation = audit_validator.validate_decisions_yaml(self.yaml_path)
        if not validation.success:
            return ImportResult(
                run_id=run_id,
                success=False,
                imported_rows=0,
                error_summary=(
                    "validation: " + "; ".join(validation.errors[:5])
                ),
            )

        yaml_text = self.yaml_path.read_text(encoding="utf-8")
        source_hash = audit_hash.compute_source_hash(yaml_text)
        scope_hash = validation.metadata["scope_hash"]

        # Step 1: import_runs INSERT status='started' (trx 1)
        helix_db.insert_import_run(
            self.db_path, run_id, source_hash, scope_hash, status="started"
        )

        # Step 2: audit_decisions 操作 (trx 2)
        case_counts: dict[str, int] = {}
        imported_rows = 0
        conn = helix_db._connect(self.db_path)
        try:
            helix_db._ensure_schema(conn)
            conn.execute("BEGIN")
            for decision in validation.decisions:
                cls = self._classify_decision(conn, decision)
                case_counts[cls.case] = case_counts.get(cls.case, 0) + 1

                if cls.case == "case_a":
                    continue  # no-op

                if cls.case in ("case_b", "case_c"):
                    conn.execute(
                        "UPDATE audit_decisions "
                        "SET status='historical', updated_at=? "
                        "WHERE id=?",
                        (now_epoch, cls.existing_decision_id),
                    )

                decision_hash = audit_hash.compute_decision_hash(decision)
                evidence_str = audit_hash.canonical_json(
                    decision.get("evidence", {})
                )
                conn.execute(
                    "INSERT INTO audit_decisions "
                    "(candidate_id, schema_version, scope_hash, decision, "
                    " evidence, rationale, fail_safe_action, status, "
                    " import_run_id, source_hash, decision_hash, "
                    " imported_at, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'active', "
                    "        ?, ?, ?, ?, ?, ?)",
                    (
                        decision["candidate_id"],
                        decision["schema_version"],
                        decision["scope_hash"],
                        decision["decision"],
                        evidence_str,
                        decision["rationale"],
                        decision["fail_safe_action"],
                        run_id,
                        source_hash,
                        decision_hash,
                        now_epoch,
                        now_epoch,
                        now_epoch,
                    ),
                )
                imported_rows += 1
            conn.execute("COMMIT")
        except Exception as e:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            error_msg = str(e)[:500]
            helix_db.update_import_run(
                self.db_path,
                run_id,
                status="failed",
                completed_at=int(time.time()),
                imported_rows=0,
                error_summary=error_msg,
            )
            return ImportResult(
                run_id=run_id,
                success=False,
                imported_rows=0,
                error_summary=error_msg,
                case_counts=case_counts,
            )
        finally:
            conn.close()

        helix_db.update_import_run(
            self.db_path,
            run_id,
            status="success",
            completed_at=int(time.time()),
            imported_rows=imported_rows,
            error_summary=None,
        )
        return ImportResult(
            run_id=run_id,
            success=True,
            imported_rows=imported_rows,
            case_counts=case_counts,
        )

    def verify_sync(self) -> VerifySyncResult:
        """G4 用: decisions.yaml と audit_decisions active 行の差分検証。"""
        validation = audit_validator.validate_decisions_yaml(self.yaml_path)
        yaml_decisions = {
            d["candidate_id"]: d for d in validation.decisions
        }

        conn = helix_db._connect(self.db_path)
        try:
            helix_db._ensure_schema(conn)
            rows = conn.execute(
                "SELECT candidate_id, decision_hash FROM audit_decisions "
                "WHERE status='active'"
            ).fetchall()
            db_active = {row[0]: row[1] for row in rows}
        finally:
            conn.close()

        missing = sorted(set(yaml_decisions.keys()) - set(db_active.keys()))
        extra = sorted(set(db_active.keys()) - set(yaml_decisions.keys()))
        hash_mismatch = []
        for cid in set(yaml_decisions.keys()) & set(db_active.keys()):
            yaml_hash = audit_hash.compute_decision_hash(
                yaml_decisions[cid]
            )
            if yaml_hash != db_active[cid]:
                hash_mismatch.append(cid)

        return VerifySyncResult(
            in_sync=(
                len(missing) == 0
                and len(extra) == 0
                and len(hash_mismatch) == 0
            ),
            yaml_count=len(yaml_decisions),
            db_active_count=len(db_active),
            missing_in_db=missing,
            extra_in_db=extra,
            hash_mismatch=hash_mismatch,
        )
