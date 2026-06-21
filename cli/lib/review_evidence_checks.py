"""review_evidence advisory detector.

PLAN frontmatter の review_evidence を検査し、定性レビュー証跡の欠落や
不整合を advisory finding として返す。gate 配線前の standalone PoC のため
常に exit 0 とし、report.mode は advisory に固定する。
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from registry_checks import DetectorReport, Finding

import plan_validator


Report = DetectorReport

REQUIRED_FIELDS = (
    "review_id",
    "review_kind",
    "reviewer_role",
    "reviewer_model",
    "worker_model",
    "reviewed_commit",
    "review_output_path",
    "review_output_sha256",
    "tests_green_at",
    "reviewed_at",
    "verdict",
)
VALID_REVIEW_KINDS = {"cross_agent", "intra_runtime_subagent"}
VALID_VERDICTS = {"approve", "changes_required"}


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _plan_entry_id(plan_path: Path, frontmatter: dict[str, Any]) -> str:
    plan_id = str(frontmatter.get("plan_id") or "").strip()
    return plan_id or plan_path.stem


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _load_review_evidence(frontmatter: dict[str, Any]) -> dict[str, Any] | None:
    if "review_evidence" not in frontmatter:
        return None
    payload = frontmatter.get("review_evidence")
    return payload if isinstance(payload, dict) else {}


def _missing_required_fields(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field_name in REQUIRED_FIELDS:
        if not _as_text(payload.get(field_name)):
            missing.append(field_name)
    return missing


def _parse_iso8601(raw: Any) -> datetime | None:
    value = _as_text(raw)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _resolve_output_path(raw_path: Any, repo_root: Path) -> Path | None:
    value = _as_text(raw_path)
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_review_evidence(
    plan_paths: list[str | Path],
    repo_root: str | Path,
) -> Report:
    root = Path(repo_root).resolve()
    findings: list[Finding] = []
    applicable_plans = 0

    for raw_plan_path in plan_paths:
        plan_path = Path(raw_plan_path)
        if not plan_path.is_absolute():
            plan_path = root / plan_path
        frontmatter = plan_validator.load_frontmatter(plan_path)
        review_evidence = _load_review_evidence(frontmatter)
        if review_evidence is None:
            continue

        applicable_plans += 1
        entry_id = _plan_entry_id(plan_path, frontmatter)
        rel_path = _rel(plan_path, root)

        for field_name in _missing_required_fields(review_evidence):
            findings.append(
                Finding(
                    severity="P1",
                    kind="review_evidence_missing_field",
                    entry_id=entry_id,
                    path=rel_path,
                    message=f"review_evidence 必須フィールド欠落: {field_name}",
                    remediation=f"frontmatter.review_evidence.{field_name} を追加する",
                )
            )

        review_kind = _as_text(review_evidence.get("review_kind"))
        reviewer_model = _as_text(review_evidence.get("reviewer_model"))
        worker_model = _as_text(review_evidence.get("worker_model"))
        if review_kind == "cross_agent" and (not reviewer_model or reviewer_model == worker_model):
            findings.append(
                Finding(
                    severity="P1",
                    kind="review_evidence_not_genuine_cross_agent",
                    entry_id=entry_id,
                    path=rel_path,
                    message=(
                        "cross_agent review は reviewer_model が必須で、"
                        "worker_model と異なる必要がある"
                    ),
                    remediation="reviewer_model を設定し、worker_model と異なる reviewer を使う",
                )
            )

        tests_green_at = _parse_iso8601(review_evidence.get("tests_green_at"))
        reviewed_at = _parse_iso8601(review_evidence.get("reviewed_at"))
        if tests_green_at is not None and reviewed_at is not None and tests_green_at > reviewed_at:
            findings.append(
                Finding(
                    severity="P1",
                    kind="review_evidence_reviewed_before_tests_green",
                    entry_id=entry_id,
                    path=rel_path,
                    message=(
                        "reviewed_at が tests_green_at より前で、"
                        "テスト green 前にレビュー済みになっている"
                    ),
                    remediation="tests_green_at と reviewed_at の実時刻を記録し直す",
                )
            )

        output_path = _resolve_output_path(review_evidence.get("review_output_path"), root)
        expected_sha256 = _as_text(review_evidence.get("review_output_sha256"))
        if output_path is not None:
            actual_sha256 = _file_sha256(output_path) if output_path.is_file() else None
            if actual_sha256 != expected_sha256:
                findings.append(
                    Finding(
                        severity="P1",
                        kind="review_evidence_output_tamper_or_missing",
                        entry_id=entry_id,
                        path=rel_path,
                        message=(
                            f"review output 欠落または sha256 不一致: "
                            f"{_rel(output_path, root)}"
                        ),
                        remediation="review_output_path の実ファイルと review_output_sha256 を再生成する",
                    )
                )

    metrics = {
        "scanned_plans": len(plan_paths),
        "applicable_plans": applicable_plans,
        "missing_field": sum(1 for finding in findings if finding.kind == "review_evidence_missing_field"),
        "not_genuine_cross_agent": sum(
            1
            for finding in findings
            if finding.kind == "review_evidence_not_genuine_cross_agent"
        ),
        "reviewed_before_tests_green": sum(
            1
            for finding in findings
            if finding.kind == "review_evidence_reviewed_before_tests_green"
        ),
        "output_tamper_or_missing": sum(
            1
            for finding in findings
            if finding.kind == "review_evidence_output_tamper_or_missing"
        ),
        "valid_review_kinds": sorted(VALID_REVIEW_KINDS),
        "valid_verdicts": sorted(VALID_VERDICTS),
    }
    return DetectorReport.build(
        check_name="check_review_evidence",
        domain="review_evidence",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_paths", nargs="+")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = check_review_evidence(args.plan_paths, args.repo_root)
    print(report.render("json") if args.json else report.render("text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
