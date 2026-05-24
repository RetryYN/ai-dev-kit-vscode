"""Retrofit mode CLI backend.

契約: docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


ROW_STATUSES = ("todo", "in_progress", "done", "blocked")
RETROFIT_SIGNALS = {"dependency_outdated", "upgrade", "config_drift"}
REFACTOR_SIGNALS = {"code_smell", "structural", "debt_degradation"}
REVERSE_SIGNALS = {"schema", "contract"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
PHASE_RE = re.compile(r"^L\d+(?:\.\d+)?$")
TABLE_MARKER = "<!-- DO NOT EDIT TABLE — regenerated from frontmatter rows -->"


class RetrofitError(RuntimeError):
    """Raised when retrofit input or state is invalid."""


@dataclass(frozen=True, slots=True)
class RegressionResult:
    success: bool
    commands: list[str]
    failures: list[str]


def _today_iso() -> str:
    return datetime.now().astimezone().date().isoformat()


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _project_root() -> Path:
    return Path(detect_project_root()).expanduser().resolve()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _validate_slug(slug: str) -> str:
    normalized = slug.strip()
    if not SLUG_RE.fullmatch(normalized):
        raise RetrofitError("slug must be kebab-case (^[a-z0-9][a-z0-9-]*[a-z0-9]$)")
    return normalized


def _validate_phase(phase: str) -> str:
    normalized = phase.strip()
    if not PHASE_RE.fullmatch(normalized):
        raise RetrofitError(f"unsupported phase: {phase}")
    return normalized


def _validate_status(status: str) -> str:
    normalized = status.strip()
    if normalized not in ROW_STATUSES:
        raise RetrofitError(f"unsupported status: {status}")
    return normalized


def _load_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise RetrofitError(f"frontmatter missing: {path}")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise RetrofitError(f"frontmatter closing delimiter missing: {path}")
    payload = yaml.safe_load(text[4:end]) or {}
    if not isinstance(payload, dict):
        raise RetrofitError(f"frontmatter must be a mapping: {path}")
    return payload, text[end + 5 :]


def _render_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    dumped = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).rstrip()
    return f"---\n{dumped}\n---\n{body}"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def matrix_path_for_slug(project_root: Path, slug: str) -> Path:
    return project_root / "docs" / "plans" / f"{slug}-retrofit-matrix.md"


def config_path_for_slug(project_root: Path, slug: str) -> Path:
    return project_root / "cli" / "config" / f"{slug}-retrofit.yaml"


def default_plan_id(slug: str) -> str:
    return f"L7-{slug}-retrofitplan"


def plan_path_for_id(project_root: Path, plan_id: str) -> Path:
    return project_root / "docs" / "plans" / "L7" / f"{plan_id}.md"


def find_active_matrix(project_root: Path) -> Path | None:
    candidates = sorted((project_root / "docs" / "plans").rglob("*-retrofit-matrix.md"))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


class RetrofitMatrix:
    """retrofit-matrix frontmatter rows を正本とする state manager."""

    def __init__(
        self,
        path: Path,
        *,
        slug: str,
        plan_id: str,
        drive: str,
        created: str,
        updated: str,
        rows: list[dict[str, Any]],
    ) -> None:
        self.path = path
        self.slug = slug
        self.plan_id = plan_id
        self.drive = drive
        self.created = created
        self.updated = updated
        self.rows = rows

    @classmethod
    def create(cls, path: Path, *, slug: str, plan_id: str, drive: str) -> "RetrofitMatrix":
        return cls(
            path,
            slug=slug,
            plan_id=plan_id,
            drive=drive,
            created=_today_iso(),
            updated=_today_iso(),
            rows=[
                {
                    "id": "R001",
                    "from": "legacy state",
                    "to": "target state",
                    "scope": "describe affected files or runtime surface",
                    "phase": "L7",
                    "status": "todo",
                    "done_at": None,
                    "regression_failed": False,
                    "notes": "",
                }
            ],
        )

    @classmethod
    def load(cls, path: Path) -> "RetrofitMatrix":
        frontmatter, _body = _load_frontmatter(path)
        rows = frontmatter.get("rows") or []
        if not isinstance(rows, list):
            raise RetrofitError(f"rows must be a list: {path}")
        normalized_rows = [cls._normalize_row(row, index + 1) for index, row in enumerate(rows)]
        return cls(
            path,
            slug=str(frontmatter.get("slug") or path.stem.removesuffix("-retrofit-matrix")),
            plan_id=str(frontmatter.get("plan_id") or default_plan_id(path.stem.removesuffix("-retrofit-matrix"))),
            drive=str(frontmatter.get("drive") or "be"),
            created=str(frontmatter.get("created") or _today_iso()),
            updated=str(frontmatter.get("updated") or _today_iso()),
            rows=normalized_rows,
        )

    @staticmethod
    def _normalize_row(row: Any, ordinal: int) -> dict[str, Any]:
        if not isinstance(row, dict):
            raise RetrofitError(f"row {ordinal} must be a mapping")
        normalized = {
            "id": str(row.get("id") or f"R{ordinal:03d}"),
            "from": str(row.get("from") or ""),
            "to": str(row.get("to") or ""),
            "scope": str(row.get("scope") or ""),
            "phase": _validate_phase(str(row.get("phase") or "L7")),
            "status": _validate_status(str(row.get("status") or "todo")),
            "done_at": row.get("done_at"),
            "regression_failed": bool(row.get("regression_failed", False)),
            "notes": str(row.get("notes") or ""),
        }
        if normalized["status"] != "done":
            normalized["done_at"] = None
        return normalized

    def _next_row_id(self) -> str:
        max_id = 0
        for row in self.rows:
            match = re.fullmatch(r"R(\d{3})", str(row.get("id") or ""))
            if match:
                max_id = max(max_id, int(match.group(1)))
        return f"R{max_id + 1:03d}"

    def find_row(self, row_id: str) -> dict[str, Any]:
        for row in self.rows:
            if row["id"] == row_id:
                return row
        raise RetrofitError(f"row not found: {row_id}")

    def add_row(self, *, from_value: str, to_value: str, scope: str, phase: str, notes: str = "") -> dict[str, Any]:
        row = {
            "id": self._next_row_id(),
            "from": from_value.strip(),
            "to": to_value.strip(),
            "scope": scope.strip(),
            "phase": _validate_phase(phase),
            "status": "todo",
            "done_at": None,
            "regression_failed": False,
            "notes": notes.strip(),
        }
        self.rows.append(row)
        self.updated = _today_iso()
        return row

    def update_row(
        self,
        row_id: str,
        *,
        status: str,
        notes: str | None = None,
        regression_failed: bool | None = None,
    ) -> dict[str, Any]:
        row = self.find_row(row_id)
        normalized_status = _validate_status(status)
        row["status"] = normalized_status
        row["done_at"] = _now_iso() if normalized_status == "done" else None
        if normalized_status != "done" and regression_failed is None:
            row["regression_failed"] = False
        elif regression_failed is not None:
            row["regression_failed"] = regression_failed
        if notes is not None:
            row["notes"] = notes
        self.updated = _today_iso()
        return row

    def summary(self) -> dict[str, Any]:
        counts = {status: 0 for status in ROW_STATUSES}
        for row in self.rows:
            counts[row["status"]] += 1
        total = len(self.rows)
        done = counts["done"]
        completion_pct = int((done / total) * 100) if total else 0
        next_row = next((row["id"] for row in self.rows if row["status"] != "done"), None)
        return {
            "slug": self.slug,
            "plan_id": self.plan_id,
            "counts": counts,
            "total_rows": total,
            "completion_pct": completion_pct,
            "next_row": next_row,
            "blocked_rows": counts["blocked"],
        }

    def render_table(self) -> str:
        header = [
            "| ID | From | To | Scope | Phase | Status | Done At |",
            "|---|---|---|---|---|---|---|",
        ]
        body = [
            "| {id} | {from_} | {to} | {scope} | {phase} | {status} | {done_at} |".format(
                id=_escape_cell(str(row["id"])),
                from_=_escape_cell(str(row["from"])),
                to=_escape_cell(str(row["to"])),
                scope=_escape_cell(str(row["scope"])),
                phase=_escape_cell(str(row["phase"])),
                status=_escape_cell(str(row["status"])),
                done_at=_escape_cell(str(row["done_at"] or "-")[:10] if row["done_at"] else "-"),
            )
            for row in self.rows
        ]
        return "\n".join(header + body)

    def save(self) -> None:
        frontmatter = {
            "slug": self.slug,
            "plan_id": self.plan_id,
            "drive": self.drive,
            "created": self.created,
            "updated": self.updated,
            "rows": self.rows,
        }
        body = (
            f"# Retrofit Matrix: {self.slug}\n\n"
            f"{TABLE_MARKER}\n"
            f"{self.render_table()}\n"
        )
        _ensure_parent(self.path)
        self.path.write_text(_render_frontmatter(frontmatter, body), encoding="utf-8")


class RetrofitConfig:
    """retrofit config YAML を管理する."""

    def __init__(self, path: Path, payload: dict[str, Any]) -> None:
        self.path = path
        self.payload = payload

    @classmethod
    def template_payload(cls, slug: str, drive: str) -> dict[str, Any]:
        return {
            "slug": slug,
            "drive": drive,
            "phases": {
                "design_supplement": ["L4", "L5"],
                "regression": ["L8", "L9"],
            },
            "rollback": {
                "strategy": "git-revert",
                "checkpoint": "HEAD~1",
            },
            "parallel_run": {
                "enabled": False,
                "old_config": None,
            },
            "regression_scope": {
                "bats": "cli/lib/tests/bats/",
                "pytest": "cli/lib/tests/",
                "filter": "",
            },
        }

    @classmethod
    def load(cls, path: Path) -> "RetrofitConfig":
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, dict):
            raise RetrofitError(f"config must be a mapping: {path}")
        return cls(path, payload)

    def save_template(self) -> None:
        _ensure_parent(self.path)
        self.path.write_text(
            yaml.safe_dump(self.payload, allow_unicode=True, sort_keys=False).rstrip() + "\n",
            encoding="utf-8",
        )

    def show_diff(self) -> dict[str, Any]:
        phases = self.payload.get("phases") or {}
        if not isinstance(phases, dict):
            phases = {}
        return {
            "design_supplement": list(phases.get("design_supplement") or []),
            "regression": list(phases.get("regression") or []),
            "rollback": dict(self.payload.get("rollback") or {}),
        }


class KindChecker:
    """変更ファイル + signal から retrofit/refactor/forward を判定する."""

    RETROFIT_HINTS = (
        "requirements.txt",
        "requirements-dev.txt",
        "poetry.lock",
        "pyproject.toml",
        "Dockerfile",
        "docker-compose",
        ".github/workflows",
        "config/",
        ".env",
    )
    REVERSE_HINTS = ("schema", "contract", "migration", "openapi")

    def check(self, *, files: list[str] | None = None, signal: str | None = None) -> tuple[str, str]:
        if signal:
            if signal in RETROFIT_SIGNALS:
                return ("retrofit", f"signal={signal} (priority 1)")
            if signal in REFACTOR_SIGNALS:
                return ("refactor", f"signal={signal} (priority 1)")
            if signal in REVERSE_SIGNALS:
                return ("reverse", f"signal={signal} (priority 1)")
        normalized = [item.strip() for item in (files or []) if item and item.strip()]
        if not normalized:
            return ("forward", "no files/signal provided")
        if any(any(hint in item for hint in self.REVERSE_HINTS) for item in normalized):
            return ("reverse", "file pattern indicates schema/contract drift")
        if any(any(hint in item for hint in self.RETROFIT_HINTS) for item in normalized):
            return ("retrofit", "file pattern indicates dependency/config change")
        if all(item.endswith((".py", ".sh", ".md")) for item in normalized):
            return ("refactor", "code/document-only change set")
        return ("mixed", "change set spans multiple categories")


def _render_plan_doc(slug: str, *, drive: str, plan_id: str, drift_type: str | None) -> str:
    frontmatter: dict[str, Any] = {
        "plan_id": plan_id,
        "title": f"L7 {slug} retrofit plan",
        "kind": "retrofit",
        "layer": "cross",
        "drive": drive,
        "status": "draft",
        "created": _today_iso(),
        "owner": "PM",
        "parent_design": "HELIX-workflows/helix-process/retrofit-workflow.md",
        "agent_slots": [
            {"role": "pm-advisor", "slot_label": "PM — 大局判断・最終 finalize"},
            {"role": "docs", "slot_label": "Docs — 文書整合更新"},
            {"role": "pmo-sonnet", "slot_label": "PMO — 4 artifact trace review"},
        ],
        "generates": [
            {
                "artifact_path": f"docs/plans/{slug}-retrofit-matrix.md",
                "artifact_type": "markdown_doc",
            },
            {
                "artifact_path": f"cli/config/{slug}-retrofit.yaml",
                "artifact_type": "yaml_config",
            },
        ],
        "dependencies": {"parent": "PLAN-091", "requires": [], "blocks": []},
        "related_docs": [
            "HELIX-workflows/helix-process/retrofit-workflow.md",
            f"docs/plans/{slug}-retrofit-matrix.md",
            f"cli/config/{slug}-retrofit.yaml",
        ],
    }
    if drift_type:
        frontmatter["drift_type"] = drift_type
    body = (
        "## §0 PLAN\n"
        f"{slug} 向けの Retrofit 実行計画。\n\n"
        "## §1 目的\n"
        "依存・基盤・構成の段階改修を管理する。\n\n"
        "## §2 実装計画\n"
        "- retrofit-matrix を更新しながら段階移行する\n"
        "- config の regression scope と rollback checkpoint を管理する\n"
    )
    return _render_frontmatter(frontmatter, body)


def draft_retrofit_plan(
    slug: str,
    *,
    plan_id: str | None = None,
    drive: str = "be",
    drift_type: str | None = None,
    project_root: Path | None = None,
) -> Path:
    root = project_root or _project_root()
    normalized_slug = _validate_slug(slug)
    resolved_plan_id = plan_id or default_plan_id(normalized_slug)
    path = plan_path_for_id(root, resolved_plan_id)
    if path.exists():
        raise RetrofitError(f"plan already exists: {_relative_path(path, root)}")
    _ensure_parent(path)
    path.write_text(
        _render_plan_doc(normalized_slug, drive=drive, plan_id=resolved_plan_id, drift_type=drift_type),
        encoding="utf-8",
    )
    return path


def init_retrofit(
    slug: str,
    *,
    plan_id: str | None = None,
    drive: str = "be",
    drift_type: str | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    root = project_root or _project_root()
    normalized_slug = _validate_slug(slug)
    resolved_plan_id = plan_id or default_plan_id(normalized_slug)

    matrix_path = matrix_path_for_slug(root, normalized_slug)
    config_path = config_path_for_slug(root, normalized_slug)
    plan_path = plan_path_for_id(root, resolved_plan_id)

    if matrix_path.exists() or config_path.exists() or plan_path.exists():
        raise RetrofitError("retrofit artifacts already exist for this slug/plan_id")

    matrix = RetrofitMatrix.create(matrix_path, slug=normalized_slug, plan_id=resolved_plan_id, drive=drive)
    matrix.save()
    config = RetrofitConfig(config_path, RetrofitConfig.template_payload(normalized_slug, drive))
    config.save_template()
    drafted_path = draft_retrofit_plan(
        normalized_slug,
        plan_id=resolved_plan_id,
        drive=drive,
        drift_type=drift_type,
        project_root=root,
    )
    return {
        "slug": normalized_slug,
        "plan_id": resolved_plan_id,
        "matrix": _relative_path(matrix_path, root),
        "config": _relative_path(config_path, root),
        "plan": _relative_path(drafted_path, root),
    }


def _status_payload(slug: str | None, *, project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or _project_root()
    matrix_path = matrix_path_for_slug(root, slug) if slug else find_active_matrix(root)
    if matrix_path is None or not matrix_path.exists():
        return {"active": False, "message": "no active retrofit"}

    matrix = RetrofitMatrix.load(matrix_path)
    config_path = config_path_for_slug(root, matrix.slug)
    plan_path = plan_path_for_id(root, matrix.plan_id)
    summary = matrix.summary()
    warnings: list[str] = []
    if summary["blocked_rows"] > 0:
        warnings.append(f"blocked rows present: {summary['blocked_rows']}")
    if config_path.exists():
        config = RetrofitConfig.load(config_path)
        design_supplement = config.show_diff()["design_supplement"]
        if design_supplement:
            warnings.append("design supplement pending: " + ", ".join(design_supplement))
    else:
        warnings.append("config file missing")

    plan_status = None
    if plan_path.exists():
        frontmatter, _body = _load_frontmatter(plan_path)
        plan_status = str(frontmatter.get("status") or "")
        if summary["completion_pct"] == 100 and plan_status != "completed":
            warnings.append(f"plan status mismatch: {plan_status or 'unknown'}")
    else:
        warnings.append("plan draft missing")

    return {
        "active": True,
        "slug": matrix.slug,
        "plan_id": matrix.plan_id,
        "plan_status": plan_status,
        "matrix": _relative_path(matrix_path, root),
        "config": _relative_path(config_path, root),
        "plan": _relative_path(plan_path, root),
        "summary": summary,
        "warnings": warnings,
    }


def get_retrofit_status(slug: str | None = None, *, as_json: bool = False, project_root: Path | None = None) -> str | dict[str, Any]:
    payload = _status_payload(slug, project_root=project_root)
    if as_json:
        return payload
    if not payload["active"]:
        return "no active retrofit"
    summary = payload["summary"]
    root = project_root or _project_root()
    config_exists = (root / payload["config"]).exists()
    lines = [
        f"[retrofit] slug: {payload['slug']}",
        f"  plan: {payload['plan_id']} ({payload['plan_status'] or 'draft'})",
        f"  matrix: {payload['matrix']}",
        f"  config: {payload['config']}{' (exists)' if config_exists else ''}",
        f"  completion: {summary['completion_pct']}% ({summary['counts']['done']}/{summary['total_rows']} done)",
        f"  next_row: {summary['next_row'] or '-'}",
    ]
    if payload["warnings"]:
        lines.append("  warnings: " + "; ".join(payload["warnings"]))
    return "\n".join(lines)


def run_regression(config: RetrofitConfig, *, project_root: Path | None = None) -> RegressionResult:
    root = project_root or _project_root()
    scope = config.payload.get("regression_scope") or {}
    if not isinstance(scope, dict):
        scope = {}
    commands: list[str] = []
    failures: list[str] = []

    pytest_target = str(scope.get("pytest") or "").strip()
    bats_target = str(scope.get("bats") or "").strip()
    filter_expr = str(scope.get("filter") or "").strip()
    extra_args = shlex.split(filter_expr) if filter_expr else []

    if pytest_target:
        args = ["pytest", pytest_target, *extra_args]
        commands.append(" ".join(args))
        result = subprocess.run(args, cwd=str(root), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(result.stderr.strip() or result.stdout.strip() or "pytest failed")

    if bats_target:
        args = ["bats", bats_target]
        commands.append(" ".join(args))
        result = subprocess.run(args, cwd=str(root), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            failures.append(result.stderr.strip() or result.stdout.strip() or "bats failed")

    return RegressionResult(success=not failures, commands=commands, failures=failures)


def _format_matrix_summary(matrix: RetrofitMatrix) -> str:
    summary = matrix.summary()
    return (
        f"slug={summary['slug']} total={summary['total_rows']} "
        f"done={summary['counts']['done']} blocked={summary['blocked_rows']} "
        f"completion={summary['completion_pct']}% next={summary['next_row'] or '-'}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helix retrofit",
        usage="helix retrofit <subcommand> [options]",
        description="Retrofit mode の matrix/config/plan を管理する",
    )
    sub = parser.add_subparsers(dest="subcommand")

    init_cmd = sub.add_parser("init")
    init_cmd.add_argument("--slug", required=True)
    init_cmd.add_argument("--plan-id")
    init_cmd.add_argument("--drive", default="be")
    init_cmd.add_argument("--drift-type")

    matrix_cmd = sub.add_parser("matrix")
    matrix_sub = matrix_cmd.add_subparsers(dest="matrix_command")

    matrix_list = matrix_sub.add_parser("list")
    matrix_list.add_argument("--slug", required=True)

    matrix_add = matrix_sub.add_parser("add")
    matrix_add.add_argument("--slug", required=True)
    matrix_add.add_argument("--from", dest="from_value", required=True)
    matrix_add.add_argument("--to", dest="to_value", required=True)
    matrix_add.add_argument("--scope", required=True)
    matrix_add.add_argument("--phase", default="L7")
    matrix_add.add_argument("--notes", default="")

    matrix_update = matrix_sub.add_parser("update")
    matrix_update.add_argument("--slug", required=True)
    matrix_update.add_argument("--row", required=True)
    matrix_update.add_argument("--status", required=True, choices=ROW_STATUSES)
    matrix_update.add_argument("--notes")

    matrix_show = matrix_sub.add_parser("show")
    matrix_show.add_argument("--slug", required=True)
    matrix_show.add_argument("--summary", action="store_true")

    status_cmd = sub.add_parser("status")
    status_cmd.add_argument("--slug")
    status_cmd.add_argument("--json", action="store_true")

    done_cmd = sub.add_parser("done")
    done_cmd.add_argument("--slug", required=True)
    done_cmd.add_argument("--row", required=True)
    done_cmd.add_argument("--run-regression", action="store_true")

    plan_cmd = sub.add_parser("plan")
    plan_cmd.add_argument("--slug", required=True)
    plan_cmd.add_argument("--plan-id")
    plan_cmd.add_argument("--drive", default="be")
    plan_cmd.add_argument("--drift-type")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.subcommand is None:
        parser.print_help()
        return 0

    try:
        root = _project_root()

        if args.subcommand == "init":
            payload = init_retrofit(
                args.slug,
                plan_id=args.plan_id,
                drive=args.drive,
                drift_type=args.drift_type,
                project_root=root,
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.subcommand == "plan":
            path = draft_retrofit_plan(
                args.slug,
                plan_id=args.plan_id,
                drive=args.drive,
                drift_type=args.drift_type,
                project_root=root,
            )
            print(_relative_path(path, root))
            return 0

        if args.subcommand == "matrix":
            if args.matrix_command is None:
                parser.parse_args(["matrix", "--help"])
                return 0
            matrix = RetrofitMatrix.load(matrix_path_for_slug(root, _validate_slug(args.slug)))
            if args.matrix_command == "list":
                print(matrix.render_table())
                return 0
            if args.matrix_command == "add":
                row = matrix.add_row(
                    from_value=args.from_value,
                    to_value=args.to_value,
                    scope=args.scope,
                    phase=args.phase,
                    notes=args.notes,
                )
                matrix.save()
                print(json.dumps(row, ensure_ascii=False, indent=2))
                return 0
            if args.matrix_command == "update":
                row = matrix.update_row(args.row, status=args.status, notes=args.notes)
                matrix.save()
                print(json.dumps(row, ensure_ascii=False, indent=2))
                return 0
            if args.matrix_command == "show":
                print(_format_matrix_summary(matrix) if args.summary else matrix.render_table())
                return 0

        if args.subcommand == "status":
            payload = get_retrofit_status(args.slug, as_json=args.json, project_root=root)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(payload)
            return 0

        if args.subcommand == "done":
            matrix = RetrofitMatrix.load(matrix_path_for_slug(root, _validate_slug(args.slug)))
            if matrix.summary()["blocked_rows"] > 0:
                print("blocked rows exist; resolve them before marking rows done", file=sys.stderr)
                return 2
            matrix.update_row(args.row, status="done")
            config = RetrofitConfig.load(config_path_for_slug(root, matrix.slug))
            if args.run_regression:
                regression = run_regression(config, project_root=root)
                if not regression.success:
                    matrix.update_row(
                        args.row,
                        status="in_progress",
                        regression_failed=True,
                        notes="regression failed: " + " | ".join(regression.failures),
                    )
                    matrix.save()
                    print(
                        json.dumps({"commands": regression.commands, "failures": regression.failures}, ensure_ascii=False, indent=2),
                        file=sys.stderr,
                    )
                    return 3
            matrix.save()
            payload = matrix.summary()
            if payload["completion_pct"] == 100:
                print("retrofit complete; update PLAN status to completed")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

    except RetrofitError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"エラー: missing file: {exc.filename}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
