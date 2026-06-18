from __future__ import annotations

"""Import/source dependency cycle detector with baseline + changed-files ratchet.

`cli/lib/vg_overview.py` already consumes
`collect_dependency_cycle_gate_summary()` via `required_clean`.
"""

import argparse
import ast
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable, Sequence

from changed_files import changed_files


DEFAULT_BASELINE_PATH = "cli/config/import-cycle-baseline.json"
_ASSIGNMENT_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.+)$")
_SOURCE_RE = re.compile(r"^(?:source|\.)\s+(.+?)(?:\s+#.*)?$")


def _resolve_project_root(repo_root: str | Path | None = None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _normalize_path(path: str | Path, repo_root: Path) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = (repo_root / path_obj).resolve()
    try:
        return path_obj.relative_to(repo_root).as_posix()
    except ValueError:
        return path_obj.as_posix()


def canonicalize_cycle(cycle: Sequence[str]) -> list[str]:
    nodes = [str(item) for item in cycle]
    if len(nodes) > 1 and nodes[0] == nodes[-1]:
        nodes = nodes[:-1]
    if not nodes:
        return []

    candidates: list[tuple[str, ...]] = []
    for variant in (nodes, list(reversed(nodes))):
        for index in range(len(variant)):
            rotated = tuple(variant[index:] + variant[:index])
            candidates.append(rotated)
    best = min(candidates)
    return [*best, best[0]]


def fingerprint_cycle(cycle: Sequence[str], *, language: str) -> str:
    canonical = canonicalize_cycle(cycle)
    raw = f"{language}|{'->'.join(canonical)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _find_cycles(adjacency: dict[str, set[str]]) -> list[list[str]]:
    discovered: dict[str, list[str]] = {}
    visited: set[str] = set()
    stack: list[str] = []
    stack_lookup: set[str] = set()

    def dfs(node: str) -> None:
        visited.add(node)
        stack.append(node)
        stack_lookup.add(node)
        for dependency in sorted(adjacency.get(node, set())):
            if dependency in stack_lookup:
                start_index = stack.index(dependency)
                cycle = canonicalize_cycle(stack[start_index:] + [dependency])
                discovered[fingerprint_cycle(cycle, language="graph")] = cycle
                continue
            if dependency not in visited:
                dfs(dependency)
        stack_lookup.remove(node)
        stack.pop()

    for node in sorted(adjacency):
        if node not in visited:
            dfs(node)
    return sorted(discovered.values())


def _python_files(lib_root: Path) -> list[Path]:
    files: list[Path] = []
    if not lib_root.is_dir():
        return files
    for path in lib_root.rglob("*.py"):
        relative = path.relative_to(lib_root)
        if any(part in {"tests", "__pycache__"} for part in relative.parts):
            continue
        files.append(path.resolve())
    return sorted(files)


def _python_alias_map(lib_root: Path, paths: list[Path]) -> tuple[dict[str, Path], dict[Path, str]]:
    alias_map: dict[str, Path] = {}
    package_map: dict[Path, str] = {}
    for path in paths:
        relative = path.relative_to(lib_root)
        parts = list(relative.parts)
        parent_parts = parts[:-1]
        package_suffix = ".".join(parent_parts)
        package_map[path] = "cli.lib" + (f".{package_suffix}" if package_suffix else "")

        module_parts = parent_parts if path.stem == "__init__" else [*parent_parts, path.stem]
        if not module_parts:
            continue
        dotted = ".".join(module_parts)
        for alias in {dotted, f"cli.lib.{dotted}"}:
            alias_map[alias] = path
    return alias_map, package_map


def _resolve_python_targets(
    node: ast.ImportFrom,
    *,
    current_package: str,
    alias_map: dict[str, Path],
) -> set[Path]:
    if node.level > 0:
        package_parts = current_package.split(".")
        strip_count = max(0, node.level - 1)
        if strip_count >= len(package_parts):
            return set()
        base = ".".join(package_parts[: len(package_parts) - strip_count])
        resolved_module = f"{base}.{node.module}" if node.module else base
    else:
        resolved_module = node.module or ""

    targets: set[Path] = set()
    if not node.module:
        for alias in node.names:
            candidate = f"{resolved_module}.{alias.name}" if resolved_module else alias.name
            target = alias_map.get(candidate)
            if target is not None:
                targets.add(target)
        return targets

    submodule_targets = []
    for alias in node.names:
        candidate = f"{resolved_module}.{alias.name}" if resolved_module else alias.name
        target = alias_map.get(candidate)
        if target is not None:
            submodule_targets.append(target)
    if submodule_targets:
        targets.update(submodule_targets)
        return targets

    base_target = alias_map.get(resolved_module)
    if base_target is not None:
        targets.add(base_target)
    return targets


def _python_adjacency(repo_root: Path) -> dict[str, set[str]]:
    lib_root = repo_root / "cli" / "lib"
    paths = _python_files(lib_root)
    alias_map, package_map = _python_alias_map(lib_root, paths)
    adjacency = {_normalize_path(path, repo_root): set() for path in paths}

    for path in paths:
        node_key = _normalize_path(path, repo_root)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            targets: set[Path] = set()
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias_map.get(alias.name)
                    if target is not None:
                        targets.add(target)
            elif isinstance(node, ast.ImportFrom):
                targets = _resolve_python_targets(
                    node,
                    current_package=package_map[path],
                    alias_map=alias_map,
                )
            if not targets:
                continue
            for target in targets:
                target_key = _normalize_path(target, repo_root)
                if target_key != node_key:
                    adjacency[node_key].add(target_key)
    return adjacency


def _is_shell_script(path: Path) -> bool:
    if path.suffix == ".sh":
        return True
    try:
        first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
    except (IndexError, OSError):
        return False
    return first_line.startswith("#!") and ("bash" in first_line or first_line.endswith("/sh"))


def _bash_files(cli_root: Path) -> list[Path]:
    files: list[Path] = []
    if not cli_root.is_dir():
        return files
    for path in cli_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(cli_root)
        if any(part in {"tests", "__pycache__"} for part in relative.parts):
            continue
        if path.parent == cli_root / "lib":
            continue
        if _is_shell_script(path):
            files.append(path.resolve())
    return sorted(files)


def _substitute_bash_vars(value: str, variables: dict[str, str]) -> str:
    resolved = value
    for key, replacement in variables.items():
        resolved = resolved.replace(f"${{{key}}}", replacement)
        resolved = resolved.replace(f"${key}", replacement)
    return resolved


def _resolve_bash_expression(expr: str, *, path: Path, variables: dict[str, str]) -> Path | None:
    value = expr.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]

    script_dir = path.parent.resolve()
    replacements = {
        '$(cd "$(dirname "$0")" && pwd)': script_dir.as_posix(),
        '$(cd "$(dirname "$0")/.." && pwd)': script_dir.parent.resolve().as_posix(),
        '$(dirname "$0")': script_dir.as_posix(),
    }
    for needle, replacement in replacements.items():
        value = value.replace(needle, replacement)
    value = _substitute_bash_vars(value, variables)
    if "$(" in value or re.search(r"\$[{A-Za-z_]", value):
        return None
    if "/" not in value and not value.startswith("."):
        return None

    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (script_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate if candidate.is_file() else None
    except OSError:
        return None


def _bash_adjacency(repo_root: Path) -> dict[str, set[str]]:
    cli_root = repo_root / "cli"
    paths = _bash_files(cli_root)
    known = {path.resolve() for path in paths}
    adjacency = {_normalize_path(path, repo_root): set() for path in paths}

    for path in paths:
        variables = {"SCRIPT_DIR": path.parent.resolve().as_posix()}
        node_key = _normalize_path(path, repo_root)
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            assignment_match = _ASSIGNMENT_RE.match(line)
            if assignment_match and not line.startswith(("source ", ". ")):
                resolved_value = _resolve_bash_expression(
                    assignment_match.group(2),
                    path=path,
                    variables=variables,
                )
                if resolved_value is not None:
                    variables[assignment_match.group(1)] = resolved_value.as_posix()
                    continue
                value = assignment_match.group(2).strip().strip('"').strip("'")
                variables[assignment_match.group(1)] = _substitute_bash_vars(value, variables)
                continue

            source_match = _SOURCE_RE.match(line)
            if not source_match:
                continue
            resolved_path = _resolve_bash_expression(
                source_match.group(1),
                path=path,
                variables=variables,
            )
            if resolved_path is None or resolved_path not in known:
                continue
            target_key = _normalize_path(resolved_path, repo_root)
            if target_key != node_key:
                adjacency[node_key].add(target_key)
    return adjacency


def collect_dependency_cycle_findings(
    *,
    repo_root: str | Path | None = None,
) -> list[dict[str, object]]:
    repo_root_path = _resolve_project_root(repo_root)
    findings: list[dict[str, object]] = []
    for language, adjacency in (
        ("python", _python_adjacency(repo_root_path)),
        ("bash", _bash_adjacency(repo_root_path)),
    ):
        for cycle in _find_cycles(adjacency):
            findings.append(
                {
                    "language": language,
                    "cycle": cycle,
                    "fingerprint": fingerprint_cycle(cycle, language=language),
                }
            )
    return sorted(findings, key=lambda item: (str(item["language"]), str(item["cycle"])))


def _load_baseline_fingerprints(baseline_path: str | Path, repo_root: Path) -> set[str]:
    path = Path(baseline_path).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    fingerprints: set[str] = set()
    for report in payload.get("reports", []):
        for finding in report.get("findings", []):
            fingerprint = str(finding.get("fingerprint", "")).strip()
            if fingerprint:
                fingerprints.add(fingerprint)
                continue
            cycle = [str(item) for item in finding.get("cycle", [])]
            language = str(finding.get("language", "python"))
            if cycle:
                fingerprints.add(fingerprint_cycle(cycle, language=language))
    return fingerprints


def _filter_changed_cycles(
    findings: list[dict[str, object]],
    changed: Iterable[str],
    repo_root: Path,
) -> list[dict[str, object]]:
    changed_paths = {_normalize_path(path, repo_root) for path in changed}
    relevant: list[dict[str, object]] = []
    for finding in findings:
        cycle_paths = [str(item) for item in finding["cycle"]]
        if any(path in changed_paths for path in cycle_paths):
            relevant.append(finding)
    return relevant


def check_dependency_cycle_gate(
    *,
    repo_root: str | Path | None = None,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    gate: bool = False,
    upstream: str | None = None,
) -> dict[str, object]:
    repo_root_path = _resolve_project_root(repo_root)
    findings = collect_dependency_cycle_findings(repo_root=repo_root_path)
    baseline_fingerprints = _load_baseline_fingerprints(baseline_path, repo_root_path)
    advisory_new = [finding for finding in findings if finding["fingerprint"] not in baseline_fingerprints]

    report: dict[str, object] = {
        "check_name": "check_import_cycle",
        "mode": "gate" if gate else "advisory",
        "exit_code": 0,
        "clean": not findings,
        "finding_count": len(findings),
        "new_finding_count": len(advisory_new),
        "findings": findings,
        "new_findings": advisory_new,
        "source_status": "not_applicable",
        "skipped_reason": None,
    }
    if not gate:
        return report

    changed_payload = changed_files(upstream=upstream)
    source_status = str(changed_payload["source_status"])
    report["source_status"] = source_status
    if source_status == "available_empty":
        report.update(
            {
                "clean": True,
                "finding_count": 0,
                "new_finding_count": 0,
                "findings": [],
                "new_findings": [],
            }
        )
        return report
    if source_status == "unavailable":
        report.update(
            {
                "clean": False,
                "finding_count": 0,
                "new_finding_count": 0,
                "findings": [],
                "new_findings": [],
                "skipped_reason": "changed-files unavailable",
            }
        )
        return report

    changed_findings = _filter_changed_cycles(findings, changed_payload["files"], repo_root_path)
    new_findings = [
        finding for finding in changed_findings if finding["fingerprint"] not in baseline_fingerprints
    ]
    report.update(
        {
            "clean": not new_findings,
            "exit_code": int(bool(new_findings)),
            "finding_count": len(changed_findings),
            "new_finding_count": len(new_findings),
            "findings": changed_findings,
            "new_findings": new_findings,
        }
    )
    return report


def collect_dependency_cycle_gate_summary(
    *,
    repo_root: str | Path | None = None,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
    upstream: str | None = None,
) -> dict[str, object]:
    report = check_dependency_cycle_gate(
        repo_root=repo_root,
        baseline_path=baseline_path,
        gate=True,
        upstream=upstream,
    )
    return {
        "clean": report["clean"],
        "finding_count": report["finding_count"],
        "source_status": report["source_status"],
        "skipped_reason": report["skipped_reason"],
    }


def collect_import_cycle_baseline_required_summary(
    *,
    repo_root: str | Path | None = None,
    baseline_path: str | Path = DEFAULT_BASELINE_PATH,
) -> dict[str, object]:
    repo_root_path = _resolve_project_root(repo_root)
    findings = collect_dependency_cycle_findings(repo_root=repo_root_path)
    baseline_fingerprints = _load_baseline_fingerprints(baseline_path, repo_root_path)
    blocking_findings = [
        finding for finding in findings if finding["fingerprint"] not in baseline_fingerprints
    ]
    warning_count = len(findings) - len(blocking_findings)
    return {
        "clean": len(blocking_findings) == 0,
        "finding_count": len(findings),
        "blocking_finding_count": len(blocking_findings),
        "warning_count": warning_count,
        "source_status": "baseline_required",
        "skipped_reason": None,
        "mode": "baseline_required",
    }


def build_import_cycle_baseline_payload(
    *,
    repo_root: str | Path | None = None,
    generated_by: str = "dependency_cycle_checks.py --write-baseline",
) -> dict[str, object]:
    repo_root_path = _resolve_project_root(repo_root)
    findings = collect_dependency_cycle_findings(repo_root=repo_root_path)
    return {
        "intentional_baseline": True,
        "owner": "codex",
        "created": "2026-06-14",
        "expiry": "2026-09-12",
        "generated_by": generated_by,
        "reports": [
            {
                "check_name": "check_import_cycle",
                "mode": "advisory",
                "findings": findings,
                "metrics": {
                    "cycle_count": len(findings),
                    "languages": sorted({str(finding["language"]) for finding in findings}),
                },
            }
        ],
    }


def write_import_cycle_baseline(
    output_path: str | Path,
    *,
    repo_root: str | Path | None = None,
    generated_by: str = "dependency_cycle_checks.py --write-baseline",
) -> Path:
    payload = build_import_cycle_baseline_payload(
        repo_root=repo_root,
        generated_by=generated_by,
    )
    repo_root_path = _resolve_project_root(repo_root)
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = (repo_root_path / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="dependency cycle helper")
    parser.add_argument("--write-baseline", action="store_true", help="write the current cycle findings as baseline")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--output", default=DEFAULT_BASELINE_PATH, help="baseline output path")
    parser.add_argument(
        "--generated-by",
        default="dependency_cycle_checks.py --write-baseline",
        help="baseline generated_by metadata",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if not args.write_baseline:
        parser.error("no action requested")
    output_path = write_import_cycle_baseline(
        args.output,
        repo_root=args.repo_root,
        generated_by=args.generated_by,
    )
    print(output_path.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
