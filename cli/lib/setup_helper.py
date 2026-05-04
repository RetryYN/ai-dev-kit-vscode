#!/usr/bin/env python3
"""HELIX setup component runner."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import helix_db

EXIT_SUCCESS = 0
EXIT_NEEDS_ATTENTION = 1
EXIT_ERROR = 2
EXIT_NOT_APPLICABLE = 3
VALID_EXIT_CODES = {EXIT_SUCCESS, EXIT_NEEDS_ATTENTION, EXIT_ERROR, EXIT_NOT_APPLICABLE}
COMPONENT_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ACTIONS = ("verify", "install", "repair", "describe")
PACKAGE_SCRIPTS = {
    "textlint": ("setup-textlint.sh", "npm devDependencies for Japanese writing lint"),
    "playwright": ("setup-playwright.sh", "Playwright test runner and Chromium"),
    "axe": ("setup-axe.sh", "axe accessibility CLI and Playwright integration"),
    "marp": ("setup-marp.sh", "Marp CLI for slides"),
    "d2": ("setup-d2.sh", "D2 diagram tool via brew or go"),
    "crawl4ai": ("setup-crawl4ai.sh", "Crawl4AI via pip"),
    "bats": ("setup-bats.sh", "Bats test runner or local bats-lite fallback"),
}


class SetupError(Exception):
    pass


class SetupArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(EXIT_ERROR, f"{self.prog}: error: {message}\n")


@dataclass(frozen=True)
class ComponentResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Component:
    name: str
    path: Path
    project_root: Path | None = None

    def verify(self) -> ComponentResult:
        return self._run("verify")

    def install(self) -> ComponentResult:
        return self._run("install")

    def repair(self) -> ComponentResult:
        return self._run("repair")

    def describe(self) -> ComponentResult:
        return self._run("describe")

    def _run(self, action: str) -> ComponentResult:
        if action not in ACTIONS:
            raise SetupError(f"invalid action: {action}")
        if not self.path.is_file():
            raise SetupError(f"component script not found: {self.path}")
        script = """
set -euo pipefail
source "$1"
if ! declare -F "$2" >/dev/null 2>&1; then
  echo "component function not found: $2" >&2
  exit 2
fi
"$2"
"""
        env = os.environ.copy()
        env["COMPONENT_NAME"] = self.name
        if self.project_root is not None:
            env["HELIX_PROJECT_ROOT"] = str(self.project_root)
        completed = subprocess.run(
            ["bash", "-c", script, "helix-setup-component", str(self.path), action],
            cwd=str(self.project_root or Path.cwd()),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        code = completed.returncode if completed.returncode in VALID_EXIT_CODES else EXIT_ERROR
        return ComponentResult(code, completed.stdout, completed.stderr)


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    status: str
    detail: str
    fix: str = ""


@dataclass(frozen=True)
class BootstrapStep:
    name: str
    status: str
    command: str
    detail: str = ""


def _check(name: str, ok: bool, detail: str, fix: str = "", *, warn: bool = False) -> PreflightCheck:
    if ok:
        return PreflightCheck(name=name, status="pass", detail=detail, fix=fix)
    return PreflightCheck(name=name, status="warn" if warn else "fail", detail=detail, fix=fix)


def _command_exists(command: str) -> bool:
    return subprocess.run(
        ["bash", "-lc", f"command -v {command} >/dev/null 2>&1"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _bash4_available() -> bool:
    return subprocess.run(
        ["bash", "-lc", "bash --version | grep -qE 'version [4-9]'"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _inside_git_repo(project_root: Path) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0


def _read_yaml_value(project_root: Path, dotted_path: str) -> str:
    parser = Path(__file__).resolve().with_name("yaml_parser.py")
    phase_file = project_root / ".helix" / "phase.yaml"
    if not phase_file.exists():
        return ""
    proc = subprocess.run(
        [sys.executable, str(parser), "read", str(phase_file), dotted_path],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _template_checks(setup_dir: Path) -> list[PreflightCheck]:
    cli_dir = setup_dir.parent
    templates = cli_dir / "templates"
    required = [
        "phase.yaml",
        "matrix.yaml",
        "doc-map.yaml",
        "gate-checks.yaml",
        "CLAUDE.md.template",
        "AGENTS.md.template",
    ]
    return [
        _check(
            f"template:{name}",
            (templates / name).exists(),
            f"{templates / name}",
            "HELIX_HOME / checkout を確認",
        )
        for name in required
    ]


def project_preflight(project_root: Path, setup_dir: Path) -> list[PreflightCheck]:
    helix_dir = project_root / ".helix"
    checks = [
        _check("project-root", project_root.exists() and project_root.is_dir(), str(project_root)),
        _check("project-root-writable", os.access(project_root, os.W_OK), str(project_root), "書き込み権限を確認"),
        _check("python3", _command_exists("python3"), "python3 command", "python3 をインストール"),
        _check("bash4", _bash4_available(), "bash >= 4", "bash 4+ をインストール"),
        _check("git", _command_exists("git"), "git command", "git をインストール"),
        _check(
            "git-worktree",
            _inside_git_repo(project_root),
            "git repository",
            "git init を実行すると git hooks まで有効化できます",
            warn=True,
        ),
    ]
    checks.extend(_template_checks(setup_dir))

    if helix_dir.exists():
        for name in ("phase.yaml", "matrix.yaml", "doc-map.yaml", "gate-checks.yaml"):
            checks.append(
                _check(
                    f"helix:{name}",
                    (helix_dir / name).exists(),
                    str(helix_dir / name),
                    "helix init または helix init --force",
                )
            )
        checks.append(
            _check(
                "helix-runtime-index",
                (helix_dir / "runtime" / "index.json").exists(),
                ".helix/runtime/index.json",
                "helix matrix compile && helix matrix auto-detect",
                warn=True,
            )
        )
    else:
        checks.append(
            _check(
                "helix-initialized",
                False,
                ".helix/ not found",
                "helix init を実行",
                warn=True,
            )
        )
    return checks


def reverse_preflight(
    project_root: Path,
    setup_dir: Path,
    reverse_type: str,
    target: str | None,
) -> list[PreflightCheck]:
    supported_types = {"code", "design", "upgrade", "normalization", "fullback"}
    helix_dir = project_root / ".helix"
    checks = [
        _check("reverse-type", reverse_type in supported_types, reverse_type, "code/design/upgrade/normalization/fullback を指定"),
        _check("helix-initialized", helix_dir.exists(), str(helix_dir), "helix init を実行"),
        _check("phase.yaml", (helix_dir / "phase.yaml").exists(), str(helix_dir / "phase.yaml"), "helix init を実行"),
        _check("helix-codex-wrapper", (setup_dir.parent / "helix-codex").exists(), str(setup_dir.parent / "helix-codex")),
        _check("codex-cli", _command_exists("codex"), "codex command", "Codex CLI をインストール。--dry-run のみなら不要", warn=True),
        _check("reverse-output-dir-writable", os.access(helix_dir, os.W_OK), str(helix_dir), ".helix/ の書き込み権限を確認"),
    ]
    current_mode = _read_yaml_value(project_root, "current_mode")
    checks.append(
        _check(
            "mode",
            current_mode == "reverse",
            f"current_mode={current_mode or 'unknown'}",
            "R0 実行時に reverse へ自動切替されます",
            warn=True,
        )
    )

    if reverse_type == "code":
        target_path = (project_root / target).resolve() if target and not Path(target).is_absolute() else Path(target or project_root)
        checks.append(
            _check(
                "reverse-code-target",
                target_path.exists(),
                str(target_path),
                "--target に既存 path を指定",
                warn=not bool(target),
            )
        )
    elif reverse_type == "design":
        for rel in ("docs/plans", "docs/design", "docs/features"):
            checks.append(
                _check(
                    f"reverse-design-source:{rel}",
                    (project_root / rel).exists(),
                    rel,
                    "設計資産がない場合は code/fullback/normalization type を検討",
                    warn=True,
                )
            )
    elif reverse_type == "fullback":
        if target:
            target_path = (project_root / target).resolve() if not Path(target).is_absolute() else Path(target)
            checks.append(
                _check("fullback-artifact", target_path.exists(), str(target_path), "--artifact/--target に完了成果物を指定")
            )
        else:
            checks.append(_check("fullback-artifact", False, "not specified", "--target または --artifact を指定", warn=True))
    return checks


def _preflight_summary(checks: list[PreflightCheck]) -> dict[str, int]:
    return {
        "pass": sum(1 for check in checks if check.status == "pass"),
        "warn": sum(1 for check in checks if check.status == "warn"),
        "fail": sum(1 for check in checks if check.status == "fail"),
    }


def format_preflight(profile: str, checks: list[PreflightCheck]) -> str:
    lines = [f"=== HELIX setup preflight: {profile} ===", ""]
    for check in checks:
        label = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}[check.status]
        line = f"{label}: {check.name} — {check.detail}"
        if check.fix:
            line += f" ({check.fix})"
        lines.append(line)
    summary = _preflight_summary(checks)
    lines.extend(["", f"Result: pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}"])
    return "\n".join(lines)


def preflight_payload(profile: str, checks: list[PreflightCheck]) -> dict[str, object]:
    summary = _preflight_summary(checks)
    return {
        "profile": profile,
        "status": "fail" if summary["fail"] else "pass",
        "summary": summary,
        "checks": [check.__dict__ for check in checks],
    }


def _run_project_command(project_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HELIX_PROJECT_ROOT"] = str(project_root)
    return subprocess.run(
        [str(part) for part in command],
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _step_from_proc(name: str, command: list[str], proc: subprocess.CompletedProcess[str]) -> BootstrapStep:
    output = (proc.stdout + proc.stderr).strip()
    first = _first_line(output)
    return BootstrapStep(
        name=name,
        status="pass" if proc.returncode == 0 else "fail",
        command=" ".join(str(part) for part in command),
        detail=first or f"exit {proc.returncode}",
    )


def bootstrap_project(
    project_root: Path,
    setup_dir: Path,
    db_path: str | None,
    *,
    project_name: str | None = None,
    start_phase: str = "L1",
    force: bool = False,
    skip_components: bool = False,
) -> tuple[list[BootstrapStep], list[PreflightCheck]]:
    cli_dir = setup_dir.parent
    steps: list[BootstrapStep] = []

    preflight = project_preflight(project_root, setup_dir)
    preflight_status = preflight_payload("project", preflight)["status"]
    steps.append(
        BootstrapStep(
            name="preflight-before",
            status="pass" if preflight_status == "pass" else "fail",
            command="helix setup preflight --profile project",
            detail=f"fail={_preflight_summary(preflight)['fail']} warn={_preflight_summary(preflight)['warn']}",
        )
    )
    if preflight_status == "fail":
        return steps, preflight

    init_cmd = [cli_dir / "helix-init", "--project-name", project_name or project_root.name, "--start-phase", start_phase]
    if force:
        init_cmd.append("--force")
    init_proc = _run_project_command(project_root, init_cmd)
    steps.append(_step_from_proc("helix-init", init_cmd, init_proc))
    if init_proc.returncode != 0:
        return steps, project_preflight(project_root, setup_dir)

    log_cmd = [cli_dir / "helix-log", "init"]
    log_proc = _run_project_command(project_root, log_cmd)
    steps.append(_step_from_proc("helix-log-init", log_cmd, log_proc))

    if not skip_components:
        components = discover_components(setup_dir, project_root=project_root)
        for component_name in ("redaction-denylist", "gitignore-helix"):
            component = find_component(components, component_name)
            result = component.install()
            if db_path:
                record_setup_result(db_path, component, "install", result)
            steps.append(
                BootstrapStep(
                    name=f"component:{component_name}",
                    status="pass" if result.returncode == EXIT_SUCCESS else "fail",
                    command=f"helix setup install --name {component_name}",
                    detail=_first_line(result.stdout) or _first_line(result.stderr) or f"exit {result.returncode}",
                )
            )
            if result.returncode != EXIT_SUCCESS:
                return steps, project_preflight(project_root, setup_dir)

    for name, command in (
        ("matrix-compile", [cli_dir / "helix-matrix", "compile"]),
        ("matrix-auto-detect", [cli_dir / "helix-matrix", "auto-detect"]),
    ):
        proc = _run_project_command(project_root, command)
        steps.append(_step_from_proc(name, command, proc))

    final_preflight = project_preflight(project_root, setup_dir)
    final_status = preflight_payload("project", final_preflight)["status"]
    steps.append(
        BootstrapStep(
            name="preflight-after",
            status="pass" if final_status == "pass" else "fail",
            command="helix setup preflight --profile project",
            detail=f"fail={_preflight_summary(final_preflight)['fail']} warn={_preflight_summary(final_preflight)['warn']}",
        )
    )
    return steps, final_preflight


def format_bootstrap(steps: list[BootstrapStep], final_checks: list[PreflightCheck]) -> str:
    lines = ["=== HELIX setup bootstrap ===", ""]
    for step in steps:
        label = "PASS" if step.status == "pass" else "FAIL"
        lines.append(f"{label}: {step.name} — {step.detail}")
    summary = _preflight_summary(final_checks)
    lines.extend(["", f"Final preflight: pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}"])
    return "\n".join(lines)


def bootstrap_payload(steps: list[BootstrapStep], final_checks: list[PreflightCheck]) -> dict[str, object]:
    summary = _preflight_summary(final_checks)
    return {
        "status": "fail" if any(step.status == "fail" for step in steps) or summary["fail"] else "pass",
        "steps": [step.__dict__ for step in steps],
        "final_preflight": preflight_payload("project", final_checks),
    }


def package_scripts_dir(setup_dir: Path) -> Path:
    return setup_dir.parent / "scripts"


def list_packages(setup_dir: Path) -> list[dict[str, str]]:
    scripts_dir = package_scripts_dir(setup_dir)
    rows = []
    for name, (script_name, description) in sorted(PACKAGE_SCRIPTS.items()):
        script_path = scripts_dir / script_name
        rows.append(
            {
                "name": name,
                "script": str(script_path),
                "available": "yes" if script_path.exists() else "no",
                "description": description,
            }
        )
    return rows


def format_packages(rows: list[dict[str, str]]) -> str:
    lines = ["name\tavailable\tdescription"]
    for row in rows:
        lines.append(f"{row['name']}\t{row['available']}\t{row['description']}")
    return "\n".join(lines)


def install_package(
    setup_dir: Path,
    project_root: Path,
    name: str,
    *,
    yes: bool = False,
) -> dict[str, object]:
    if name not in PACKAGE_SCRIPTS:
        raise SetupError(f"unknown package: {name}")
    script_name, description = PACKAGE_SCRIPTS[name]
    script_path = package_scripts_dir(setup_dir) / script_name
    if not script_path.exists():
        raise SetupError(f"package script not found: {script_path}")

    command = [str(script_path)]
    payload: dict[str, object] = {
        "name": name,
        "description": description,
        "command": " ".join(command),
        "executed": bool(yes),
    }
    if not yes:
        payload["status"] = "dry-run"
        payload["detail"] = "pass --yes to execute"
        return payload

    proc = _run_project_command(project_root, command)
    payload.update(
        {
            "status": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    )
    return payload


def format_package_install(payload: dict[str, object]) -> str:
    if payload["status"] == "dry-run":
        return "\n".join(
            [
                "=== HELIX setup packages install (dry-run) ===",
                f"name: {payload['name']}",
                f"command: {payload['command']}",
                "実行する場合は --yes を付けてください。",
            ]
        )
    lines = [
        "=== HELIX setup packages install ===",
        f"name: {payload['name']}",
        f"status: {payload['status']}",
    ]
    if payload.get("stdout"):
        lines.extend(["", str(payload["stdout"]).rstrip()])
    if payload.get("stderr"):
        lines.extend(["", str(payload["stderr"]).rstrip()])
    return "\n".join(lines)


def validate_component_name(name: str) -> str:
    if not name or not COMPONENT_NAME_RE.fullmatch(name):
        raise SetupError(f"invalid component name: {name}")
    return name


def discover_components(setup_dir: Path, project_root: Path | None = None) -> list[Component]:
    if not setup_dir.exists():
        return []
    if not setup_dir.is_dir():
        raise SetupError(f"setup path is not a directory: {setup_dir}")
    components = []
    for path in sorted(setup_dir.glob("*.sh")):
        name = path.stem
        if COMPONENT_NAME_RE.fullmatch(name):
            components.append(Component(name=name, path=path.resolve(), project_root=project_root))
    return components


def find_component(components: list[Component], name: str) -> Component:
    validated = validate_component_name(name)
    for component in components:
        if component.name == validated:
            return component
    raise SetupError(f"unknown component: {validated}")


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _status_name(code: int) -> str:
    return {
        EXIT_SUCCESS: "ok",
        EXIT_NEEDS_ATTENTION: "needs_attention",
        EXIT_ERROR: "error",
        EXIT_NOT_APPLICABLE: "not_applicable",
    }.get(code, "error")


def format_status_table(components: list[Component]) -> str:
    rows = ["name\tstatus\tdescription"]
    for component in components:
        verify_result = component.verify()
        describe_result = component.describe()
        description = _first_line(describe_result.stdout) if describe_result.returncode == EXIT_SUCCESS else ""
        rows.append(f"{component.name}\t{_status_name(verify_result.returncode)}\t{description}")
    return "\n".join(rows)


def format_component_list(components: list[Component]) -> str:
    rows = ["name\tdescription"]
    for component in components:
        result = component.describe()
        description = _first_line(result.stdout) if result.returncode == EXIT_SUCCESS else ""
        rows.append(f"{component.name}\t{description}")
    return "\n".join(rows)


def _print_result(result: ComponentResult) -> None:
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


def _automation_status(code: int) -> str:
    if code == EXIT_SUCCESS:
        return "success"
    if code == EXIT_NOT_APPLICABLE:
        return "cancelled"
    return "failed"


def _ensure_db(db_path: str) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        helix_db.init_db(db_path)


def record_setup_result(db_path: str, component: Component, action: str, result: ComponentResult) -> None:
    if action not in {"verify", "install", "repair"}:
        return
    _ensure_db(db_path)
    now = int(time.time())
    status = _automation_status(result.returncode)
    details = {
        "stdout": result.stdout[:2000],
        "stderr": result.stderr[:2000],
        "returncode": result.returncode,
    }
    installed = 1 if (action == "install" and result.returncode == EXIT_SUCCESS) else 0
    verify_state = status if action == "verify" else "pending"
    verify_error = result.stderr[:2000] if action == "verify" and result.returncode != EXIT_SUCCESS else None
    timestamp_column = {
        "verify": "last_verify_at",
        "install": "last_install_at",
        "repair": "last_repair_at",
    }[action]
    conn = helix_db.get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT installed, verify_state, verify_error FROM setup_checks WHERE component = ?",
            (component.name,),
        ).fetchone()
        if existing:
            installed = 1 if installed else int(existing["installed"] or 0)
            if action != "verify":
                verify_state = existing["verify_state"]
                verify_error = existing["verify_error"]
        conn.execute(
            f"""
            INSERT INTO setup_checks
                (component, verify_state, installed, {timestamp_column}, verify_error, install_path, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(component) DO UPDATE SET
                verify_state = excluded.verify_state,
                installed = excluded.installed,
                {timestamp_column} = excluded.{timestamp_column},
                verify_error = excluded.verify_error,
                install_path = excluded.install_path,
                updated_at = excluded.updated_at
            """,
            (component.name, verify_state, installed, now, verify_error, str(component.path), now),
        )
        conn.execute(
            """
            INSERT INTO setup_events (component, action, status, outcome, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                component.name,
                action,
                status,
                _first_line(result.stdout) or _first_line(result.stderr),
                json.dumps(details, ensure_ascii=False, sort_keys=True),
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _name_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", required=True, help="component name")


def build_parser() -> argparse.ArgumentParser:
    parser = SetupArgumentParser(description="HELIX setup component runner")
    parser.add_argument("--setup-dir", required=True, type=Path)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--db-path")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "install", "repair"):
        _name_arg(subparsers.add_parser(command))
    subparsers.add_parser("list")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--name")
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--profile", required=True, choices=("project", "reverse"))
    preflight_parser.add_argument("--reverse-type", default="code", choices=("code", "design", "upgrade", "normalization", "fullback"))
    preflight_parser.add_argument("--target")
    preflight_parser.add_argument("--json", action="store_true")
    bootstrap_parser = subparsers.add_parser("bootstrap")
    bootstrap_parser.add_argument("--project-name")
    bootstrap_parser.add_argument("--start-phase", default="L1", choices=[f"L{i}" for i in range(1, 12)])
    bootstrap_parser.add_argument("--force", action="store_true")
    bootstrap_parser.add_argument("--skip-components", action="store_true")
    bootstrap_parser.add_argument("--json", action="store_true")
    packages_parser = subparsers.add_parser("packages")
    package_subparsers = packages_parser.add_subparsers(dest="package_command", required=True)
    package_list = package_subparsers.add_parser("list")
    package_list.add_argument("--json", action="store_true")
    package_install = package_subparsers.add_parser("install")
    package_install.add_argument("--name", required=True, choices=sorted(PACKAGE_SCRIPTS))
    package_install.add_argument("--dry-run", action="store_true")
    package_install.add_argument("--yes", action="store_true")
    package_install.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = args.project_root.resolve()
    components = discover_components(args.setup_dir.resolve(), project_root=project_root)
    try:
        if args.command == "list":
            print(format_component_list(components))
            return EXIT_SUCCESS
        if args.command == "status":
            if args.name:
                component = find_component(components, args.name)
                print(format_status_table([component]))
            else:
                print(format_status_table(components))
            return EXIT_SUCCESS
        if args.command == "preflight":
            if args.profile == "project":
                checks = project_preflight(project_root, args.setup_dir.resolve())
            else:
                checks = reverse_preflight(project_root, args.setup_dir.resolve(), args.reverse_type, args.target)
            payload = preflight_payload(args.profile, checks)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(format_preflight(args.profile, checks))
            return EXIT_NEEDS_ATTENTION if payload["status"] == "fail" else EXIT_SUCCESS
        if args.command == "bootstrap":
            steps, final_checks = bootstrap_project(
                project_root,
                args.setup_dir.resolve(),
                args.db_path,
                project_name=args.project_name,
                start_phase=args.start_phase,
                force=args.force,
                skip_components=args.skip_components,
            )
            payload = bootstrap_payload(steps, final_checks)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(format_bootstrap(steps, final_checks))
            return EXIT_NEEDS_ATTENTION if payload["status"] == "fail" else EXIT_SUCCESS
        if args.command == "packages":
            if args.package_command == "list":
                rows = list_packages(args.setup_dir.resolve())
                if args.json:
                    print(json.dumps({"packages": rows}, ensure_ascii=False, indent=2, sort_keys=True))
                else:
                    print(format_packages(rows))
                return EXIT_SUCCESS
            payload = install_package(
                args.setup_dir.resolve(),
                project_root,
                args.name,
                yes=args.yes and not args.dry_run,
            )
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
            else:
                print(format_package_install(payload))
            return EXIT_NEEDS_ATTENTION if payload["status"] == "fail" else EXIT_SUCCESS
        component = find_component(components, args.name)
        result = getattr(component, args.command)()
        if args.db_path:
            record_setup_result(args.db_path, component, args.command, result)
        _print_result(result)
        return result.returncode
    except (SetupError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
