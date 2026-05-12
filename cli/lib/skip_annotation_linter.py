from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Iterable


VALID_SKIP_CATEGORIES = {
    "env_dependent",
    "bats_lite_limit",
    "external_blocker",
    "migration_pending",
}
PLAN_ID_RE = re.compile(r"^PLAN-\d{3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HELIX_SKIP_RE = re.compile(
    r"^HELIX-SKIP:\s*(?P<category>[^|]+?)\s*\|\s*(?P<plan_id>[^|]+?)\s*\|\s*due_date:\s*(?P<due_date>.+?)\s*$"
)
SUPPORTED_SKIP_CALLS = {
    "pytest.skip",
    "pytest.mark.skip",
    "pytest.mark.skipif",
    "unittest.skip",
    "unittest.skipif",
    "skip",
    "skipif",
}
SKIP_MARKER_SUFFIXES = (
    ("pytest", "mark", "skip"),
    ("pytest", "mark", "skipif"),
    ("pytest", "skip"),
    ("unittest", "skip"),
    ("unittest", "skipif"),
    ("skip",),
    ("skipif",),
)


@dataclass(frozen=True)
class SkipFinding:
    path: str
    line: int
    column: int
    severity: str
    code: str
    message: str
    reason: str | None
    marker: str
    structured: bool
    category: str | None = None
    plan_id: str | None = None
    due_date: str | None = None
    days_overdue: int | None = None


@dataclass(frozen=True)
class LintResult:
    findings: tuple[SkipFinding, ...]
    scanned_files: tuple[str, ...]
    strict: bool

    @property
    def exit_code(self) -> int:
        return 0 if not self.findings else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint HELIX skip annotations")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        default=None,
        help="scan target path (file or directory). Can be repeated.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat overdue skip annotations as errors",
    )
    return parser.parse_args(argv)


def _iter_python_files(paths: Iterable[str | Path]) -> list[Path]:
    files: set[Path] = set()
    cwd = Path.cwd()
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = cwd / path
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix == ".py":
                files.add(path.resolve())
            continue
        for candidate in path.rglob("*.py"):
            if candidate.is_file():
                files.add(candidate.resolve())
    return sorted(files)


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        if prefix is None:
            return None
        return f"{prefix}.{node.attr}"
    return None


def _is_skip_marker(marker: str) -> bool:
    lowered = marker.lower()
    return any(lowered.endswith(".".join(parts)) for parts in SKIP_MARKER_SUFFIXES)


def _is_supported_skip_call(call: ast.Call) -> bool:
    marker = _extract_marker_name(call)
    return marker is not None and marker.lower() in SUPPORTED_SKIP_CALLS


def _extract_marker_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _dotted_name(node.func)
    return _dotted_name(node)


def _string_constant(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_reason_from_call(marker: str, call: ast.Call) -> str | None:
    marker_lower = marker.lower()
    for keyword in call.keywords:
        if keyword.arg == "reason":
            reason = _string_constant(keyword.value)
            if reason is not None:
                return reason
            return None

    if marker_lower in {"pytest.mark.skipif", "unittest.skipif", "skipif"}:
        if len(call.args) >= 2:
            return _string_constant(call.args[1])
        return None

    if marker_lower in {"pytest.skip", "pytest.mark.skip", "unittest.skip", "skip"} and call.args:
        return _string_constant(call.args[0])
    return None


def _build_unstructured_finding(path: Path, line: int, column: int, marker: str, reason: str | None) -> SkipFinding:
    return SkipFinding(
        path=str(path),
        line=line,
        column=column,
        severity="warning",
        code="UNSTRUCTURED_SKIP",
        message="HELIX-SKIP プレフィックスがありません",
        reason=reason,
        marker=marker,
        structured=False,
    )


def _build_invalid_structured_finding(
    path: Path,
    line: int,
    column: int,
    marker: str,
    reason: str,
    message: str,
) -> SkipFinding:
    return SkipFinding(
        path=str(path),
        line=line,
        column=column,
        severity="error",
        code="INVALID_SKIP_ANNOTATION",
        message=message,
        reason=reason,
        marker=marker,
        structured=True,
    )


def _build_overdue_finding(
    path: Path,
    line: int,
    column: int,
    marker: str,
    reason: str,
    category: str,
    plan_id: str,
    due_date: date,
    days_overdue: int,
    strict: bool,
) -> SkipFinding:
    severity = "error" if strict else "warning"
    return SkipFinding(
        path=str(path),
        line=line,
        column=column,
        severity=severity,
        code="OVERDUE_SKIP_ANNOTATION",
        message="skip 期限が 30 日を超過しています",
        reason=reason,
        marker=marker,
        structured=True,
        category=category,
        plan_id=plan_id,
        due_date=due_date.isoformat(),
        days_overdue=days_overdue,
    )


def _parse_structured_reason(reason: str) -> tuple[str, str, date] | None:
    match = HELIX_SKIP_RE.match(reason.strip())
    if not match:
        return None
    category = match.group("category").strip()
    plan_id = match.group("plan_id").strip()
    due_date_text = match.group("due_date").strip()
    if category not in VALID_SKIP_CATEGORIES:
        raise ValueError(f"invalid category: {category}")
    if not PLAN_ID_RE.fullmatch(plan_id):
        raise ValueError(f"invalid plan id: {plan_id}")
    if not DATE_RE.fullmatch(due_date_text):
        raise ValueError(f"invalid due date: {due_date_text}")
    try:
        parsed_due_date = date.fromisoformat(due_date_text)
    except ValueError as exc:
        raise ValueError(f"invalid due date: {due_date_text}") from exc
    return category, plan_id, parsed_due_date


class _SkipAnnotationVisitor(ast.NodeVisitor):
    def __init__(self, path: Path, *, strict: bool, today: date) -> None:
        self.path = path
        self.strict = strict
        self.today = today
        self.findings: list[SkipFinding] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_decorators(node.decorator_list, node)
        for stmt in node.body:
            self.visit(stmt)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_decorators(node.decorator_list, node)
        for stmt in node.body:
            self.visit(stmt)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self._visit_decorators(node.decorator_list, node)
        for stmt in node.body:
            self.visit(stmt)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if _is_supported_skip_call(node):
            self._maybe_record_skip(node, node.lineno, node.col_offset, from_decorator=False)
        self.generic_visit(node)

    def _visit_decorators(self, decorators: list[ast.expr], node: ast.AST) -> None:
        for decorator in decorators:
            if isinstance(decorator, ast.Call) and _is_supported_skip_call(decorator):
                self._maybe_record_skip(
                    decorator,
                    getattr(decorator, "lineno", getattr(node, "lineno", 1)),
                    getattr(decorator, "col_offset", getattr(node, "col_offset", 0)),
                    from_decorator=True,
                )

    def _maybe_record_skip(self, expr: ast.AST, line: int, column: int, *, from_decorator: bool) -> None:
        if not isinstance(expr, ast.Call):
            return

        marker = _extract_marker_name(expr)
        if marker is None or not _is_supported_skip_call(expr):
            return

        reason = _extract_reason_from_call(marker, expr)

        if reason is None or not reason.strip():
            self.findings.append(_build_unstructured_finding(self.path, line, column, marker, reason))
            return

        try:
            structured = _parse_structured_reason(reason)
        except ValueError as exc:
            self.findings.append(
                _build_invalid_structured_finding(
                    self.path,
                    line,
                    column,
                    marker,
                    reason,
                    str(exc),
                )
            )
            return
        if structured is None:
            self.findings.append(_build_unstructured_finding(self.path, line, column, marker, reason))
            return

        category, plan_id, due_date = structured

        days_overdue = (self.today - due_date).days
        if days_overdue >= 30:
            self.findings.append(
                _build_overdue_finding(
                    self.path,
                    line,
                    column,
                    marker,
                    reason,
                    category,
                    plan_id,
                    due_date,
                    days_overdue,
                    self.strict,
                )
            )


def lint_skip_annotations(
    paths: Iterable[str | Path],
    *,
    strict: bool = False,
    today: date | None = None,
) -> LintResult:
    resolved_today = today or date.today()
    files = _iter_python_files(paths)
    findings: list[SkipFinding] = []
    for path in files:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(
                SkipFinding(
                    path=str(path),
                    line=1,
                    column=0,
                    severity="error",
                    code="UNREADABLE_FILE",
                    message=str(exc),
                    reason=None,
                    marker="",
                    structured=False,
                )
            )
            continue

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            findings.append(
                SkipFinding(
                    path=str(path),
                    line=exc.lineno or 1,
                    column=exc.offset or 0,
                    severity="error",
                    code="SYNTAX_ERROR",
                    message=exc.msg,
                    reason=None,
                    marker="",
                    structured=False,
                )
            )
            continue

        visitor = _SkipAnnotationVisitor(path, strict=strict, today=resolved_today)
        visitor.visit(tree)
        findings.extend(visitor.findings)

    return LintResult(findings=tuple(findings), scanned_files=tuple(str(path) for path in files), strict=strict)


def _render_text(result: LintResult) -> str:
    if not result.findings:
        return f"clean: scanned {len(result.scanned_files)} file(s)"

    lines = [
        f"{finding.severity.upper()}: {finding.path}:{finding.line}:{finding.column}: {finding.code}: {finding.message}"
        for finding in result.findings
    ]
    lines.append(
        f"summary: files={len(result.scanned_files)} findings={len(result.findings)} strict={'true' if result.strict else 'false'}"
    )
    return "\n".join(lines)


def _render_json(result: LintResult) -> str:
    payload = {
        "summary": {
            "files_scanned": len(result.scanned_files),
            "findings": len(result.findings),
            "strict": result.strict,
        },
        "findings": [asdict(finding) for finding in result.findings],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    paths = args.paths if args.paths is not None else ["cli", "tests"]
    result = lint_skip_annotations(paths, strict=args.strict)
    rendered = _render_json(result) if args.format == "json" else _render_text(result)
    print(rendered)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
