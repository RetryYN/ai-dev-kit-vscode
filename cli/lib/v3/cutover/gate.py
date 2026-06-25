from __future__ import annotations

import ast
import os
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from typing import Any

try:
    from v3.projection import writer
    from v3.schema import ddl
except ImportError:  # pragma: no cover - repo-local fallback until top-level v3 package is wired.
    from cli.lib.v3.projection import writer
    from cli.lib.v3.schema import ddl


_CHECK_ORDER = ("pin_inventory", "dangling", "rollback_preflight", "rebuild_dry_run")
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_PLAN_ID_RE = re.compile(r"^\s*plan_id:\s*(.+?)\s*$", re.MULTILINE)
_ARTIFACT_PATH_RE = re.compile(r"^\s*artifact_path:\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    subject: str
    missing: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "severity": self.severity,
            "subject": self.subject,
            "missing": list(self.missing),
        }


@dataclass(frozen=True)
class CheckResult:
    id: str
    ok: bool
    severity: str
    subject: str
    missing: tuple[str, ...]
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class CutoverInput:
    existing_paths: tuple[str, ...]
    surviving_surface: tuple[str, ...]
    retired_inventory: tuple[str, ...]
    retired_actual: tuple[str, ...]
    unresolved_links: tuple[str, ...]
    unresolved_imports: tuple[str, ...]
    unresolved_plan_references: tuple[str, ...]
    archive_writable: bool
    v2_paths_unchanged: bool
    promote_reverse_defined: bool
    window_expiry_defined: bool
    restore_dry_run_ok: bool
    rebuild_exception: str | None
    detector_gap_policy: dict[str, str] | None
    enabled_checks: tuple[str, ...]


@dataclass(frozen=True)
class CutoverResult:
    ok: bool
    checks: dict[str, CheckResult]
    accepted_gap: CheckResult | None
    enabled_checks: tuple[str, ...]


def _make_check_result(
    check_id: str,
    *,
    ok: bool,
    severity: str,
    subject: str,
    missing: list[str] | tuple[str, ...],
) -> CheckResult:
    finding = Finding(
        id=check_id,
        severity=severity,
        subject=subject,
        missing=tuple(missing),
    )
    return CheckResult(
        id=check_id,
        ok=ok,
        severity=severity,
        subject=subject,
        missing=tuple(missing),
        findings=(finding,),
    )


def _normalize_list(values: object) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(str(value) for value in values)


def _git_repo_files(repo_root: str, roots: tuple[str, ...]) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", *roots],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths: list[str] = []
    for line in completed.stdout.splitlines():
        candidate = line.strip().replace(os.sep, "/")
        if candidate:
            paths.append(candidate)
    return sorted(set(paths))


def _walk_repo_files(repo_root: str, roots: tuple[str, ...]) -> list[str]:
    paths: list[str] = []
    for root in roots:
        absolute_root = os.path.join(repo_root, root)
        if not os.path.exists(absolute_root):
            continue
        if os.path.isfile(absolute_root):
            paths.append(root.replace(os.sep, "/"))
            continue
        for dirpath, dirnames, filenames in os.walk(absolute_root):
            dirnames[:] = [name for name in dirnames if name not in {".git", "__pycache__", ".pytest_cache"}]
            for filename in filenames:
                absolute_path = os.path.join(dirpath, filename)
                relative = os.path.relpath(absolute_path, repo_root).replace(os.sep, "/")
                paths.append(relative)
    return sorted(set(paths))


def _scan_repo_files(repo_root: str, roots: tuple[str, ...]) -> list[str]:
    paths: list[str] = []
    for root in roots:
        absolute_root = os.path.join(repo_root, root)
        if not os.path.exists(absolute_root):
            continue
        if os.path.isfile(absolute_root):
            paths.append(root.replace(os.sep, "/"))
            continue

        def _visit(directory: str) -> None:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if entry.name in {".git", "__pycache__", ".pytest_cache"}:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        _visit(entry.path)
                        continue
                    relative = os.path.relpath(entry.path, repo_root).replace(os.sep, "/")
                    paths.append(relative)

        _visit(absolute_root)
    return sorted(set(paths))


def _enumerate_repo_files(repo_root: str, roots: tuple[str, ...]) -> tuple[str, ...]:
    try:
        return tuple(_git_repo_files(repo_root, roots))
    except (OSError, subprocess.SubprocessError):
        walked = _walk_repo_files(repo_root, roots)
        scanned = _scan_repo_files(repo_root, roots)
        if set(walked) != set(scanned):
            return ()
        return tuple(walked)


def _read_text(repo_root: str, relative_path: str) -> str:
    with open(os.path.join(repo_root, relative_path), encoding="utf-8") as handle:
        return handle.read()


def _resolve_markdown_target(source_path: str, raw_target: str) -> str | None:
    target = raw_target.strip()
    if not target or target.startswith("#"):
        return None
    if "://" in target or target.startswith("mailto:"):
        return None
    target = target.split("#", 1)[0]
    if target.startswith("/"):
        return target.lstrip("/").replace(os.sep, "/")
    resolved = os.path.normpath(os.path.join(os.path.dirname(source_path), target))
    return resolved.replace(os.sep, "/")


def _scan_markdown_links(repo_root: str, markdown_files: tuple[str, ...], existing_paths: set[str]) -> tuple[str, ...]:
    missing: list[str] = []
    for relative_path in markdown_files:
        text = _read_text(repo_root, relative_path)
        for match in _LINK_RE.finditer(text):
            target = _resolve_markdown_target(relative_path, match.group(1))
            if target is None:
                continue
            if target not in existing_paths and not os.path.exists(os.path.join(repo_root, target)):
                missing.append(f"{relative_path} -> {target}")
    return tuple(sorted(set(missing)))


def _module_names_from_path(relative_path: str) -> tuple[str, ...]:
    stem = relative_path.replace("/", ".")
    if stem.endswith(".__init__.py"):
        module = stem[: -len(".__init__.py")]
    else:
        module = stem[: -len(".py")]
    names = {module}
    if module.startswith("cli.lib.v3"):
        names.add(module.replace("cli.lib.", "", 1))
    return tuple(sorted(names))


def _build_module_index(python_files: tuple[str, ...]) -> set[str]:
    modules: set[str] = set()
    for relative_path in python_files:
        modules.update(_module_names_from_path(relative_path))
    return modules


def _resolve_relative_import(current_package: str, module: str | None, level: int) -> str:
    package_parts = current_package.split(".")
    if level > len(package_parts):
        return ""
    base = package_parts[: len(package_parts) - (level - 1)]
    if module:
        base.extend(module.split("."))
    return ".".join(part for part in base if part)


def _is_internal_module(module_name: str) -> bool:
    return module_name == "v3" or module_name.startswith("v3.") or module_name == "cli.lib.v3" or module_name.startswith("cli.lib.v3.")


def _scan_python_imports(repo_root: str, python_files: tuple[str, ...], module_index: set[str]) -> tuple[str, ...]:
    missing: list[str] = []
    for relative_path in python_files:
        text = _read_text(repo_root, relative_path)
        tree = ast.parse(text, filename=relative_path)
        current_module = _module_names_from_path(relative_path)[0]
        current_package = current_module if relative_path.endswith("__init__.py") else current_module.rsplit(".", 1)[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not _is_internal_module(alias.name):
                        continue
                    if alias.name not in module_index:
                        missing.append(f"{relative_path} -> {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    resolved = _resolve_relative_import(current_package, node.module, node.level)
                    if resolved and resolved not in module_index:
                        missing.append(f"{relative_path} -> {resolved}")
                    continue
                if node.module and _is_internal_module(node.module) and node.module not in module_index:
                    missing.append(f"{relative_path} -> {node.module}")
    return tuple(sorted(set(missing)))


def _plan_id_map(repo_root: str, plan_files: tuple[str, ...]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for relative_path in plan_files:
        text = _read_text(repo_root, relative_path)
        match = _PLAN_ID_RE.search(text)
        if match:
            mapping[match.group(1).strip()] = relative_path
        mapping[os.path.splitext(os.path.basename(relative_path))[0]] = relative_path
    return mapping


def _scan_plan_references(repo_root: str, selected_plan_files: tuple[str, ...], all_plan_files: tuple[str, ...], existing_paths: set[str]) -> tuple[str, ...]:
    if not selected_plan_files:
        return ()
    plan_ids = _plan_id_map(repo_root, all_plan_files)
    missing: list[str] = []
    for relative_path in selected_plan_files:
        if relative_path not in existing_paths:
            missing.append(f"{relative_path} -> missing-plan-file")
            continue
        text = _read_text(repo_root, relative_path)
        for match in _ARTIFACT_PATH_RE.finditer(text):
            artifact_path = match.group(1).strip()
            if artifact_path not in existing_paths and not os.path.exists(os.path.join(repo_root, artifact_path)):
                missing.append(f"{relative_path} -> {artifact_path}")
        in_requires = False
        requires_indent = 0
        for line in text.splitlines():
            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()
            if stripped == "requires:":
                in_requires = True
                requires_indent = indent
                continue
            if not in_requires:
                continue
            if stripped.startswith("- "):
                plan_ref = stripped[2:].strip()
                if plan_ref not in plan_ids:
                    missing.append(f"{relative_path} -> {plan_ref}")
                continue
            if stripped and indent <= requires_indent:
                in_requires = False
    return tuple(sorted(set(missing)))


def _is_writable_directory(path: str | None) -> bool:
    if not path:
        return False
    absolute = os.path.abspath(path)
    return os.path.isdir(absolute) and os.access(absolute, os.W_OK)


def _run_restore_dry_run(candidate: object) -> bool:
    if callable(candidate):
        try:
            return bool(candidate())
        except Exception:
            return False
    return bool(candidate)


def load_cutover_input(
    repo: os.PathLike[str] | str,
    db: sqlite3.Connection | None,
    config: dict[str, object] | None = None,
) -> CutoverInput:
    del db
    repo_root = os.path.abspath(os.fspath(repo))
    config = dict(config or {})

    doc_roots = _normalize_list(config.get("doc_roots") or ("docs/v3",))
    code_roots = _normalize_list(config.get("code_roots") or ("cli/lib/v3",))
    plan_roots = _normalize_list(config.get("plan_roots") or ("docs/plans/L7",))
    selected_plan_paths = _normalize_list(config.get("plan_paths"))
    scan_roots = tuple(dict.fromkeys((*doc_roots, *code_roots, *plan_roots, *selected_plan_paths)))

    existing_paths = _enumerate_repo_files(repo_root, scan_roots)
    existing_path_set = set(existing_paths)

    markdown_files = tuple(path for path in existing_paths if path.endswith(".md") and any(path.startswith(root.rstrip("/") + "/") or path == root for root in (*doc_roots, *selected_plan_paths)))
    python_files = tuple(path for path in existing_paths if path.endswith(".py") and any(path.startswith(root.rstrip("/") + "/") or path == root for root in code_roots))
    all_plan_files = tuple(path for path in existing_paths if path.endswith(".md") and any(path.startswith(root.rstrip("/") + "/") or path == root for root in plan_roots))
    selected_plan_files = selected_plan_paths or tuple(path for path in all_plan_files if "v3" in os.path.basename(path))

    unresolved_links = _scan_markdown_links(repo_root, markdown_files + tuple(path for path in selected_plan_files if path not in markdown_files), existing_path_set)
    module_index = _build_module_index(python_files)
    unresolved_imports = _scan_python_imports(repo_root, python_files, module_index)
    unresolved_plan_references = _scan_plan_references(repo_root, selected_plan_files, all_plan_files, existing_path_set)

    rebuild_exception: str | None = None
    try:
        throwaway = sqlite3.connect(":memory:")
        try:
            ddl.migrate(throwaway)
            writer.rebuild_projection(throwaway, config.get("sources_root", repo_root))
        finally:
            throwaway.close()
    except Exception as exc:
        rebuild_exception = str(exc) or exc.__class__.__name__

    surviving_surface = _normalize_list(config.get("surviving_surface"))
    retired_inventory = _normalize_list(config.get("retired_inventory"))
    retired_actual = _normalize_list(config.get("retired_actual") or retired_inventory)
    v2_path_inventory = _normalize_list(config.get("v2_path_inventory"))
    current_v2_paths = _normalize_list(config.get("current_v2_paths") or v2_path_inventory)
    enabled_checks = _normalize_list(config.get("enabled_checks") or _CHECK_ORDER)
    raw_gap_policy = config.get("detector_gap_policy")
    detector_gap_policy = None if raw_gap_policy is None else {str(key): str(value) for key, value in dict(raw_gap_policy).items()}

    return CutoverInput(
        existing_paths=existing_paths,
        surviving_surface=surviving_surface,
        retired_inventory=retired_inventory,
        retired_actual=retired_actual,
        unresolved_links=unresolved_links,
        unresolved_imports=unresolved_imports,
        unresolved_plan_references=unresolved_plan_references,
        archive_writable=_is_writable_directory(config.get("archive_dir") if isinstance(config.get("archive_dir"), str) else config.get("archive_dir")),
        v2_paths_unchanged=current_v2_paths == v2_path_inventory,
        promote_reverse_defined=bool(config.get("promote_reverse")),
        window_expiry_defined=bool(config.get("window_expiry")),
        restore_dry_run_ok=_run_restore_dry_run(config.get("restore_dry_run")),
        rebuild_exception=rebuild_exception,
        detector_gap_policy=detector_gap_policy,
        enabled_checks=enabled_checks,
    )


def _analyze_pin_inventory(cutover_input: CutoverInput) -> CheckResult:
    existing = set(cutover_input.existing_paths)
    missing: list[str] = []
    for path in sorted(set(cutover_input.surviving_surface) - existing):
        missing.append(f"surviving:{path}")

    expected_retired = set(cutover_input.retired_inventory)
    actual_retired = set(cutover_input.retired_actual)
    for path in sorted(expected_retired - actual_retired):
        missing.append(f"missing_retired:{path}")
    for path in sorted(actual_retired - expected_retired):
        missing.append(f"unexpected_retired:{path}")

    return _make_check_result(
        "pin_inventory",
        ok=not missing,
        severity="hard",
        subject="cutover.pin_inventory",
        missing=missing,
    )


def _analyze_dangling(cutover_input: CutoverInput) -> CheckResult:
    missing = list(cutover_input.unresolved_links + cutover_input.unresolved_imports + cutover_input.unresolved_plan_references)
    return _make_check_result(
        "dangling",
        ok=not missing,
        severity="hard",
        subject="cutover.dangling",
        missing=missing,
    )


def _analyze_rollback_preflight(cutover_input: CutoverInput) -> CheckResult:
    missing: list[str] = []
    if not cutover_input.archive_writable:
        missing.append("archive_dir")
    if not cutover_input.v2_paths_unchanged:
        missing.append("v2_path_inventory")
    if not cutover_input.promote_reverse_defined:
        missing.append("promote_reverse")
    if not cutover_input.window_expiry_defined:
        missing.append("window_expiry")
    if not cutover_input.restore_dry_run_ok:
        missing.append("restore_dry_run")
    return _make_check_result(
        "rollback_preflight",
        ok=not missing,
        severity="hard",
        subject="cutover.rollback_preflight",
        missing=missing,
    )


def _analyze_rebuild_dry_run(cutover_input: CutoverInput) -> CheckResult:
    missing = [] if cutover_input.rebuild_exception is None else [cutover_input.rebuild_exception]
    return _make_check_result(
        "rebuild_dry_run",
        ok=not missing,
        severity="hard",
        subject="cutover.rebuild_dry_run",
        missing=missing,
    )


def _analyze_accepted_gap(cutover_input: CutoverInput) -> CheckResult | None:
    if cutover_input.detector_gap_policy is None:
        return None
    missing = [
        field
        for field in ("deadline", "owner", "bridge")
        if not cutover_input.detector_gap_policy.get(field, "").strip()
    ]
    return _make_check_result(
        "accepted_gap",
        ok=not missing,
        severity="soft" if not missing else "hard",
        subject="cutover.detector_gap",
        missing=missing,
    )


def analyze_cutover(cutover_input: CutoverInput) -> CutoverResult:
    checks = {
        "pin_inventory": _analyze_pin_inventory(cutover_input),
        "dangling": _analyze_dangling(cutover_input),
        "rollback_preflight": _analyze_rollback_preflight(cutover_input),
        "rebuild_dry_run": _analyze_rebuild_dry_run(cutover_input),
    }
    accepted_gap = _analyze_accepted_gap(cutover_input)
    enabled_checks = tuple(check_id for check_id in cutover_input.enabled_checks if check_id in checks)
    ok = all(checks[check_id].ok for check_id in enabled_checks)
    if accepted_gap is not None:
        ok = ok and accepted_gap.ok
    return CutoverResult(ok=ok, checks=checks, accepted_gap=accepted_gap, enabled_checks=enabled_checks)


def cutover_messages(result: CutoverResult) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for check_id in result.enabled_checks:
        findings.extend(finding.as_dict() for finding in result.checks[check_id].findings)
    if result.accepted_gap is not None:
        findings.extend(finding.as_dict() for finding in result.accepted_gap.findings)
    return findings
