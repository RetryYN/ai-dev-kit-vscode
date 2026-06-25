"""V3 engine の実行口: rebuild(projection) → run_doctor(detection) → report。

V2 の `helix doctor` 相当の単一エントリ。engine が usable な product として動くことを示す capstone。
"""

from __future__ import annotations

import os
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass

# v3 package は import 形式が混在(`v3.*` と `cli.lib.v3.*`)するため、cli/lib と repo-root の
# 両方を path に bootstrap し、どの invocation でも解決可能にする。
_HERE = os.path.dirname(os.path.abspath(__file__))  # cli/lib/v3
_CLI_LIB = os.path.dirname(_HERE)  # cli/lib
_REPO_ROOT = os.path.dirname(os.path.dirname(_CLI_LIB))  # repo root
for _path in (_CLI_LIB, _REPO_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from v3.detectors import core, runner
from v3.projection import writer
from v3.schema import ddl

KEY_TABLES = (
    "plan_registry",
    "artifact_registry",
    "test_cases",
    "functional_registry",
    "trace_edges",
)


@dataclass(frozen=True)
class V3DoctorReport:
    ok: bool
    projection_counts: dict[str, int]
    findings_by_detector: dict[str, int]
    total_findings: int


def run_v3_doctor(repo_root: str, db_path: str | None = None) -> V3DoctorReport:
    """repo_root を rebuild → 全 core detector を ok=AND で実行 → 構造化 report。"""
    db = sqlite3.connect(db_path or ":memory:")
    try:
        ddl.migrate(db)
        writer.rebuild_projection(db, repo_root)
        result = runner.run_doctor(db, core.CORE_DETECTORS)
        counts = {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in KEY_TABLES  # 固定 allowlist（injection なし）
        }
        by_detector = dict(Counter(finding.id for finding in result.findings))
        return V3DoctorReport(
            ok=result.ok,
            projection_counts=counts,
            findings_by_detector=by_detector,
            total_findings=len(result.findings),
        )
    finally:
        db.close()


def format_report(report: V3DoctorReport) -> str:
    lines = [f"V3 doctor: ok={report.ok} (findings={report.total_findings})"]
    lines.append("  projection: " + ", ".join(f"{t}={n}" for t, n in report.projection_counts.items()))
    if report.findings_by_detector:
        lines.append("  findings: " + ", ".join(f"{d}={n}" for d, n in sorted(report.findings_by_detector.items())))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="v3-doctor", description="V3 engine: rebuild + detect")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--db", default=None, help="sqlite path (default in-memory)")
    args = parser.parse_args(argv)
    report = run_v3_doctor(args.repo_root, args.db)
    print(format_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
