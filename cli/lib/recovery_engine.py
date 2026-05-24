"""Recovery mode CLI backend.

契約: docs/plans/L7/L7-helix-recover-implplan.md §2 / §4
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

try:
    from . import agent_mandatory, helix_db, recovery_plan_check
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    import agent_mandatory
    import helix_db
    import recovery_plan_check
    from paths import project_root as detect_project_root


ConditionId = Literal["C1", "C2", "C3", "C4"]
Severity = Literal["CLEAR", "WARN", "FAIL", "UNKNOWN"]
SourceKey = Literal[
    "git_diff_numstat",
    "agent_mandatory_audit",
    "handover_current_json",
    "budget_status_json",
]

VALID_CONDITIONS: tuple[ConditionId, ...] = ("C1", "C2", "C3", "C4")
VALID_SEVERITIES: tuple[Severity, ...] = ("CLEAR", "WARN", "FAIL", "UNKNOWN")
DISPLAY_HEADING_OVERRIDES = {"訂正履歴": "認識訂正履歴"}


@dataclass(frozen=True, slots=True)
class RecoveryCondition:
    condition_id: ConditionId
    severity: Severity
    source: SourceKey
    metric_value: float | int | str | None
    threshold: float | int | str | None
    evidence: str
    detail: str

    def __post_init__(self) -> None:
        if self.condition_id not in VALID_CONDITIONS:
            raise TypeError(f"invalid condition_id: {self.condition_id!r}")
        if self.severity not in VALID_SEVERITIES:
            raise TypeError(f"invalid severity: {self.severity!r}")

    @property
    def triggered(self) -> bool:
        return self.severity in ("WARN", "FAIL")

    @property
    def requires_attention(self) -> bool:
        return self.triggered or self.severity == "UNKNOWN"


class RecoveryEngine:
    def __init__(
        self,
        helix_db_path: str | Path | None = None,
        phase_yaml_path: str | Path | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.helix_home = Path(os.environ.get("HELIX_HOME", Path(__file__).resolve().parents[2])).expanduser().resolve()
        self.helix_dir = self.project_root / ".helix"
        self.helix_db_path = Path(helix_db_path or (self.helix_dir / "helix.db")).expanduser().resolve()
        self.phase_yaml_path = Path(phase_yaml_path or (self.helix_dir / "phase.yaml")).expanduser().resolve()

    def _run_command(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(cwd or self.project_root),
            capture_output=True,
            text=True,
            check=False,
        )

    def _now_iso(self) -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    def _load_phase(self) -> dict[str, Any]:
        if not self.phase_yaml_path.exists():
            return {}
        payload = yaml.safe_load(self.phase_yaml_path.read_text(encoding="utf-8")) or {}
        return payload if isinstance(payload, dict) else {}

    def _load_frontmatter(self, path: Path) -> dict[str, Any]:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            return {}
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                payload = yaml.safe_load("\n".join(lines[1:index])) or {}
                return payload if isinstance(payload, dict) else {}
        return {}

    def _revised_date(self, frontmatter: dict[str, Any], path: Path) -> date:
        revised = frontmatter.get("revised") or frontmatter.get("created")
        if isinstance(revised, datetime):
            return revised.date()
        if isinstance(revised, date):
            return revised
        if isinstance(revised, str):
            try:
                return date.fromisoformat(revised.strip())
            except ValueError:
                pass
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).date()

    def _iter_recovery_plans(self) -> list[tuple[Path, dict[str, Any]]]:
        docs_dir = self.project_root / "docs" / "plans"
        if not docs_dir.is_dir():
            return []
        rows: list[tuple[Path, dict[str, Any]]] = []
        for path in sorted(docs_dir.rglob("*.md")):
            frontmatter = self._load_frontmatter(path)
            if str(frontmatter.get("kind") or "").strip() != "recovery":
                continue
            rows.append((path, frontmatter))
        return rows

    def check_conditions(self, since_commits: int = 1) -> list[RecoveryCondition]:
        return [
            self._check_c1(since_commits=since_commits),
            self._check_c2(),
            self._check_c3(),
            self._check_c4(),
        ]

    def _check_c1(self, since_commits: int = 1) -> RecoveryCondition:
        diff_args = ["git", "diff", "--numstat"]
        if since_commits <= 0:
            diff_args.append("HEAD")
        else:
            diff_args.append(f"HEAD~{since_commits}..HEAD")
        result = self._run_command(diff_args, cwd=self.project_root)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "git diff unavailable").strip()
            return RecoveryCondition(
                "C1",
                "UNKNOWN",
                "git_diff_numstat",
                None,
                "30 files / 1500 lines warn, 50 files / 3000 lines fail",
                message,
                message,
            )

        file_count = 0
        line_count = 0
        for raw_line in result.stdout.splitlines():
            if not raw_line.strip():
                continue
            parts = raw_line.split("\t", 2)
            if len(parts) != 3:
                continue
            added, deleted, _path = parts
            file_count += 1
            if added.isdigit():
                line_count += int(added)
            if deleted.isdigit():
                line_count += int(deleted)

        if file_count > 50 or line_count > 3000:
            severity: Severity = "FAIL"
        elif file_count > 30 or line_count > 1500:
            severity = "WARN"
        else:
            severity = "CLEAR"
        metric = f"{file_count} files / {line_count} lines"
        return RecoveryCondition(
            "C1",
            severity,
            "git_diff_numstat",
            metric,
            "30 files / 1500 lines warn, 50 files / 3000 lines fail",
            f"{metric} changed",
            f"git diff source: {' '.join(diff_args)}",
        )

    def _doctor_counts(self, payload: dict[str, Any]) -> tuple[int, int] | None:
        if "fail" in payload and "warn" in payload:
            return int(payload["fail"] or 0), int(payload["warn"] or 0)
        summary = payload.get("summary")
        if isinstance(summary, dict) and "fail" in summary and "warn" in summary:
            return int(summary["fail"] or 0), int(summary["warn"] or 0)
        return None

    def _check_c2(self) -> RecoveryCondition:
        phase = str(self._load_phase().get("current_phase") or "").strip()
        audit_unknown = False
        missing_count = 0
        if not phase:
            audit_unknown = True
        else:
            try:
                audit = agent_mandatory.audit_phase(phase)
                missing_count = int(audit.get("missing_count", 0))
            except Exception as exc:  # pragma: no cover - defensive
                audit_unknown = True
                audit_error = str(exc)
            else:
                audit_error = ""

        doctor_result = self._run_command([str(self.helix_home / "cli" / "helix-doctor"), "--json"], cwd=self.project_root)
        doctor_unknown = False
        fail_count = 0
        warn_count = 0
        doctor_error = ""
        if doctor_result.returncode != 0:
            doctor_unknown = True
            doctor_error = (doctor_result.stderr or doctor_result.stdout or "doctor command failed").strip()
        else:
            try:
                payload = json.loads(doctor_result.stdout or "{}")
                counts = self._doctor_counts(payload if isinstance(payload, dict) else {})
                if counts is None:
                    doctor_unknown = True
                    doctor_error = "doctor JSON shape unsupported"
                else:
                    fail_count, warn_count = counts
            except json.JSONDecodeError:
                doctor_unknown = True
                doctor_error = "doctor JSON parse failed"

        if missing_count >= 3 or fail_count > 0:
            severity: Severity = "FAIL"
        elif missing_count > 0 or warn_count > 0:
            severity = "WARN"
        elif audit_unknown or doctor_unknown:
            severity = "UNKNOWN"
        else:
            severity = "CLEAR"

        evidence_parts: list[str] = []
        if missing_count:
            evidence_parts.append(f"missing_count={missing_count}")
        if fail_count or warn_count:
            evidence_parts.append(f"doctor fail={fail_count} warn={warn_count}")
        if audit_unknown:
            evidence_parts.append(audit_error or "phase/audit unavailable")
        if doctor_unknown:
            evidence_parts.append(doctor_error or "doctor unavailable")
        evidence = ", ".join(evidence_parts) if evidence_parts else "mandatory audit all fired, doctor clean"
        return RecoveryCondition(
            "C2",
            severity,
            "agent_mandatory_audit",
            missing_count if missing_count else f"fail={fail_count}, warn={warn_count}",
            "audit missing >=1 warn / >=3 fail, doctor fail>0 fail, warn>0 warn",
            evidence,
            f"phase={phase or '(unknown)'}",
        )

    def _check_c3(self) -> RecoveryCondition:
        handover_path = self.project_root / ".helix" / "handover" / "CURRENT.json"
        handover_unknown = False
        handover_escalated = False
        handover_message = ""
        if handover_path.exists():
            try:
                payload = json.loads(handover_path.read_text(encoding="utf-8"))
                task = payload.get("task", {}) if isinstance(payload, dict) else {}
                handover_escalated = str(task.get("status") or "").strip() == "escalated"
            except json.JSONDecodeError:
                handover_unknown = True
                handover_message = "CURRENT.json parse failed"

        stale_drafts: list[str] = []
        today = datetime.now(UTC).date()
        for path, frontmatter in self._iter_recovery_plans():
            status = str(frontmatter.get("status") or "").strip()
            if status != "draft":
                continue
            age_days = (today - self._revised_date(frontmatter, path)).days
            if age_days > 7:
                plan_id = str(frontmatter.get("plan_id") or path.stem)
                stale_drafts.append(f"{plan_id} ({age_days}d)")

        if handover_escalated or stale_drafts:
            severity: Severity = "WARN"
        elif handover_unknown:
            severity = "UNKNOWN"
        else:
            severity = "CLEAR"

        evidence_parts: list[str] = []
        if handover_escalated:
            evidence_parts.append("handover status=escalated")
        if stale_drafts:
            evidence_parts.append("stale draft recovery plans: " + ", ".join(stale_drafts[:3]))
        if handover_unknown:
            evidence_parts.append(handover_message)
        evidence = ", ".join(evidence_parts) if evidence_parts else "handover clear, no stale recovery drafts"
        return RecoveryCondition(
            "C3",
            severity,
            "handover_current_json",
            "escalated" if handover_escalated else len(stale_drafts),
            "handover escalated or recovery draft older than 7 days",
            evidence,
            evidence,
        )

    def _check_c4(self) -> RecoveryCondition:
        result = self._run_command(
            [str(self.helix_home / "cli" / "helix-budget"), "status", "--json", "--no-cache"],
            cwd=self.project_root,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "budget status failed").strip()
            return RecoveryCondition(
                "C4",
                "UNKNOWN",
                "budget_status_json",
                None,
                "either >=80 warn, both >=80 fail",
                message,
                message,
            )
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return RecoveryCondition(
                "C4",
                "UNKNOWN",
                "budget_status_json",
                None,
                "either >=80 warn, both >=80 fail",
                "budget JSON parse failed",
                "budget JSON parse failed",
            )

        claude = payload.get("claude", {}) if isinstance(payload, dict) else {}
        codex = payload.get("codex", {}) if isinstance(payload, dict) else {}
        if "weekly_used_pct" not in claude or "weekly_used_pct" not in codex:
            return RecoveryCondition(
                "C4",
                "UNKNOWN",
                "budget_status_json",
                None,
                "either >=80 warn, both >=80 fail",
                "missing weekly_used_pct in budget payload",
                "budget payload missing required keys",
            )

        claude_pct = int(claude.get("weekly_used_pct") or 0)
        codex_pct = int(codex.get("weekly_used_pct") or 0)
        if claude_pct >= 80 and codex_pct >= 80:
            severity: Severity = "FAIL"
        elif claude_pct >= 80 or codex_pct >= 80:
            severity = "WARN"
        else:
            severity = "CLEAR"
        metric = f"claude={claude_pct}, codex={codex_pct}"
        return RecoveryCondition(
            "C4",
            severity,
            "budget_status_json",
            metric,
            "either >=80 warn, both >=80 fail",
            metric,
            metric,
        )

    def _recent_task_rows(self, limit: int = 5) -> list[str]:
        if not self.helix_db_path.exists():
            return ["- helix.db not found"]
        try:
            conn = helix_db.get_connection(self.helix_db_path)
            try:
                tables = {
                    row[0]
                    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                if "task_runs" not in tables:
                    return ["- task_runs table not found"]
                rows = conn.execute(
                    """
                    SELECT task_id, role, status, started_at, completed_at
                    FROM task_runs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            finally:
                conn.close()
        except sqlite3.Error as exc:
            return [f"- helix.db read failed: {type(exc).__name__}"]
        if not rows:
            return ["- no task_runs"]
        return [
            "- {task_id} role={role} status={status} started={started_at} completed={completed_at}".format(
                task_id=row["task_id"],
                role=row["role"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"] or "-",
            )
            for row in rows
        ]

    def _git_log_lines(self, limit: int = 5) -> list[str]:
        result = self._run_command(["git", "log", "--oneline", "-n", str(limit)], cwd=self.project_root)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "git log unavailable").strip()
            return [f"- {message}"]
        lines = [f"- {line}" for line in result.stdout.splitlines() if line.strip()]
        return lines or ["- no commits"]

    def dump_state(
        self,
        output_path: str | Path,
        conditions: list[RecoveryCondition],
        auto_routed_from: str | None = None,
        route_signal: str | None = None,
    ) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        generated_at = self._now_iso()
        mapping = self.signal_to_condition(route_signal) if route_signal else None
        sections: dict[str, list[str]] = {
            "事故記録": [
                *(f"- {cond.condition_id}: {cond.severity} [{cond.source}] metric={cond.metric_value} threshold={cond.threshold}" for cond in conditions),
                *(f"- {cond.condition_id} detail: {cond.detail}" for cond in conditions),
            ] or ["- no conditions"],
            "timeline": [
                "### task_runs",
                *self._recent_task_rows(),
                "",
                "### git log",
                *self._git_log_lines(),
            ],
            "訂正履歴": [
                "- 誤認識なし / 追加訂正待ち" if not any(cond.condition_id == "C3" for cond in conditions) else "- C3 検出: handover / recovery draft を再確認",
            ],
            "中間結論": [
                f"- attention_count={sum(1 for cond in conditions if cond.requires_attention)}",
                "- WARN/FAIL があるため recovery PLAN draft を確認",
            ],
            "context 再構築": [
                "- 1. HELIX-workflows/helix-process/recovery-workflow.md を読む",
                "- 2. helix recover check を再実行する",
                "- 3. 関連 PLAN と handover を再確認する",
            ],
            "再開ポイント": [
                "- reopen_point: helix recover plan --reopen-point HEAD",
                "- next_step: Recovery PLAN draft を確認して再開地点を1つに絞る",
            ],
            "再発防止": [
                "- handover / memory / todo を更新してから中断する",
                "- 大規模変更前に helix size / review を通す",
            ],
        }
        if auto_routed_from or route_signal:
            sections["再発防止"].append(f"- route_signal: {route_signal or '-'}")
            sections["再発防止"].append(f"- routed_from: {auto_routed_from or '-'}")
            sections["再発防止"].append(
                f"- signal_to_condition_mapping: {route_signal or '-'} -> {mapping or 'None'}"
            )

        body: list[str] = [
            "---",
            f"recovery_log_id: recovery-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            f"created: {generated_at}",
            "generator: cli/helix-recover dump",
            f"helix_db_snapshot_at: {generated_at}",
            "---",
            "",
            f"# Recovery Log — {generated_at}",
            "",
        ]
        for section_name in recovery_plan_check.REQUIRED_TEMPLATE_SECTIONS:
            heading = DISPLAY_HEADING_OVERRIDES.get(section_name, section_name)
            body.append(f"## {heading}")
            body.extend(sections.get(section_name, ["- pending"]))
            body.append("")

        output.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
        assert recovery_plan_check.check_recovery_template_sections(output) == []
        return str(output)

    def signal_to_condition(self, signal_id: str | None) -> ConditionId | None:
        mapping = {
            "runaway": "C2",
            "regression_dev": "C3",
            "incident": "C3",
        }
        if signal_id is None:
            return None
        return mapping.get(signal_id)

    def suggest_rollback_point(self) -> dict[str, Any]:
        commit_result = self._run_command(["git", "log", "--format=%H", "-n", "3"], cwd=self.project_root)
        commits = [line.strip() for line in commit_result.stdout.splitlines() if line.strip()] if commit_result.returncode == 0 else []
        plans = [
            str(frontmatter.get("plan_id") or path.stem)
            for path, frontmatter in self._iter_recovery_plans()[:3]
        ]
        return {
            "git_commit_candidates": commits,
            "plan_candidates": plans,
            "phase_snapshot": self._load_phase(),
            "note": "実行は手動ガード、--apply 不可",
        }

    def draft_recovery_plan(
        self,
        conditions: list[RecoveryCondition],
        reopen_point: str,
        auto_routed_from: str | None = None,
    ) -> str:
        lines = [
            "---",
            "plan_id: PLAN-NNN-recovery-draft",
            'title: "PLAN-NNN: recovery draft"',
            "kind: recovery",
            "layer: cross",
            "drive: troubleshoot",
            "status: draft",
            f"created: {datetime.now(UTC).date().isoformat()}",
            f"reopen_point: {reopen_point}",
        ]
        if auto_routed_from:
            lines.append(f"auto_routed_from: {auto_routed_from}")
        lines.extend(
            [
                "---",
                "",
                "## 事故記録",
                *(f"- {cond.condition_id}: {cond.severity} / {cond.evidence}" for cond in conditions),
                "",
                "## timeline",
                "- dump_state の recovery-log を参照",
                "",
                "## 認識訂正履歴",
                "- 初回 draft",
                "",
                "## 中間結論",
                "- recovery 実行前に再開地点を 1 つに固定する",
                "",
                "## context 再構築",
                "- recovery-log と関連 PLAN を読み直す",
                "",
                "## 再開ポイント",
                f"- reopen_point: {reopen_point}",
                "",
                "## 再発防止",
                "- route / review / handover の証跡を残す",
                "",
            ]
        )
        return "\n".join(lines)

    def status_payload(self) -> dict[str, Any]:
        recovery_dir = self.helix_dir / "recovery"
        logs = sorted(recovery_dir.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True) if recovery_dir.is_dir() else []
        plans = self._iter_recovery_plans()
        return {
            "logs": [str(path.relative_to(self.project_root)) for path in logs],
            "plans": [str(path.relative_to(self.project_root)) for path, _frontmatter in plans],
        }


def _format_check_text(conditions: list[RecoveryCondition]) -> str:
    labels = {
        "C1": "大規模変更",
        "C2": "工程逸脱",
        "C3": "認識ズレ",
        "C4": "予算過剰",
    }
    lines = [f"[HELIX Recovery Check] ({datetime.now().astimezone().isoformat(timespec='seconds')})"]
    for cond in conditions:
        lines.append(
            f"{cond.condition_id} {labels[cond.condition_id]}: {cond.severity:<7} ({cond.evidence}) [{cond.source}]"
        )
    warn_ids = [cond.condition_id for cond in conditions if cond.severity in {"WARN", "FAIL"}]
    unknown_ids = [cond.condition_id for cond in conditions if cond.severity == "UNKNOWN"]
    lines.append("")
    lines.append(
        f"{len(warn_ids)} 条件 WARN/FAIL ({', '.join(warn_ids) if warn_ids else '-'}) / "
        f"{len(unknown_ids)} 条件 UNKNOWN ({', '.join(unknown_ids) if unknown_ids else '-'})"
    )
    lines.append("推奨: helix recover dump で状態 dump を取得し、helix recover plan で PLAN を起票")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helix recover",
        usage="helix recover <subcommand> [options]",
        description="Recovery mode の診断・dump・PLAN 起票",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    check_cmd = sub.add_parser("check")
    check_cmd.add_argument("--since-commits", type=int, default=1)
    check_cmd.add_argument("--json", action="store_true")

    dump_cmd = sub.add_parser("dump")
    dump_cmd.add_argument("--output")
    dump_cmd.add_argument("--since-commits", type=int, default=1)
    dump_cmd.add_argument("--auto-routed-from")
    dump_cmd.add_argument("--signal-id")

    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("--condition", choices=VALID_CONDITIONS)
    plan_cmd.add_argument("--signal-id")
    plan_cmd.add_argument("--reopen-point", default="HEAD")
    plan_cmd.add_argument("--auto-routed-from")
    plan_cmd.add_argument("--output")

    rollback_cmd = sub.add_parser("rollback")
    rollback_cmd.add_argument("--dry-run", action="store_true")
    rollback_cmd.add_argument("--apply", action="store_true")

    status_cmd = sub.add_parser("status")
    status_cmd.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = RecoveryEngine()

    if args.subcommand == "check":
        conditions = engine.check_conditions(since_commits=args.since_commits)
        if args.json:
            print(
                json.dumps(
                    [
                        {
                            "condition_id": condition.condition_id,
                            "severity": condition.severity,
                            "source": condition.source,
                            "metric_value": condition.metric_value,
                            "threshold": condition.threshold,
                            "evidence": condition.evidence,
                            "detail": condition.detail,
                            "triggered": condition.triggered,
                            "requires_attention": condition.requires_attention,
                        }
                        for condition in conditions
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(_format_check_text(conditions))
        return 0

    if args.subcommand == "dump":
        conditions = engine.check_conditions(since_commits=args.since_commits)
        output = args.output or str(engine.helix_dir / "recovery" / "recovery-log.md")
        generated = engine.dump_state(
            output,
            conditions,
            auto_routed_from=args.auto_routed_from,
            route_signal=args.signal_id,
        )
        print(generated)
        return 0

    if args.subcommand == "plan":
        conditions = engine.check_conditions()
        if args.signal_id:
            resolved = engine.signal_to_condition(args.signal_id)
            if resolved is not None:
                conditions = [cond for cond in conditions if cond.condition_id == resolved]
        elif args.condition:
            conditions = [cond for cond in conditions if cond.condition_id == args.condition]
        output = args.output or str(engine.helix_dir / "recovery" / "recovery-log.md")
        engine.dump_state(
            output,
            conditions,
            auto_routed_from=args.auto_routed_from,
            route_signal=args.signal_id,
        )
        draft = engine.draft_recovery_plan(
            conditions,
            reopen_point=args.reopen_point,
            auto_routed_from=args.auto_routed_from,
        )
        print(draft)
        return 0

    if args.subcommand == "rollback":
        if args.apply:
            print("use 'helix recover rollback --dry-run' first, then run git/db commands manually", file=sys.stderr)
            return 2
        payload = engine.suggest_rollback_point()
        print("[dry-run]")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.subcommand == "status":
        payload = engine.status_payload()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if not payload["logs"]:
            print("No recovery logs found")
        else:
            print("Recovery logs:")
            for path in payload["logs"]:
                print(f"  {path}")
        if payload["plans"]:
            print("Recovery plans:")
            for path in payload["plans"]:
                print(f"  {path}")
        return 0

    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
