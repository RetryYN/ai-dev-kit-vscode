from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SETUP_SH = REPO_ROOT / "setup.sh"
CORE_MANIFEST = REPO_ROOT / "helix" / "core-manifest.tsv"
GLOBAL_CLAUDE_MD = REPO_ROOT / ".claude" / "CLAUDE.md"
PROJECT_CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

VALID_SCOPES = {"common", "claude", "codex"}
EXPECTED_CLAUDE_CORE_IMPORTS = [
    "@~/.helix/core/helix/HELIX_CORE.md",
    "@~/.helix/core/helix/HELIX_RUNTIME_RULES.md",
    "@~/.helix/core/HELIX-workflows/HELIX-process-L0-L14.md",
    "@~/.helix/core/helix/CLAUDE_RUNTIME_ADAPTER.md",
]


def _manifest_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for lineno, raw_line in enumerate(CORE_MANIFEST.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = raw_line.split("\t")
        assert len(parts) == 2, f"core-manifest.tsv:{lineno} must have exactly 2 TSV columns"
        scope, import_path = parts
        rows.append((scope, import_path))
    return rows


def _manifest_imports(*scopes: str) -> list[str]:
    allowed_scopes = set(scopes)
    return [import_path for scope, import_path in _manifest_rows() if scope in allowed_scopes]


def _setup_core_imports() -> list[str]:
    command = "\n".join(
        [
            "set -euo pipefail",
            f"export HELIX_HOME={shlex.quote(str(REPO_ROOT))}",
            f"source {shlex.quote(str(SETUP_SH))}",
            "load_core_imports >/dev/null",
            'printf "%s\\n" "${CORE_IMPORTS[@]}"',
        ]
    )
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return [line for line in result.stdout.splitlines() if line]


def _import_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("@")
    ]


def test_core_manifest_schema_and_scopes() -> None:
    assert CORE_MANIFEST.exists(), "helix/core-manifest.tsv must exist"
    rows = _manifest_rows()
    assert rows, "core-manifest.tsv must define at least one import"
    for scope, import_path in rows:
        assert scope in VALID_SCOPES
        assert import_path.startswith("@~/.helix/core/")


def test_setup_core_imports_follow_manifest_and_are_not_hardcoded() -> None:
    manifest_imports = _manifest_imports("common", "claude")
    assert _setup_core_imports() == manifest_imports

    setup_text = SETUP_SH.read_text(encoding="utf-8")
    assert "core-manifest.tsv" in setup_text
    for import_path in EXPECTED_CLAUDE_CORE_IMPORTS:
        assert import_path not in setup_text


def test_loader_imports_do_not_use_clone_paths() -> None:
    for path in (GLOBAL_CLAUDE_MD, PROJECT_CLAUDE_MD):
        for import_line in _import_lines(path):
            assert not import_line.startswith("@~/ai-dev-kit-vscode/")


def test_manifest_common_claude_matches_distribution_contract() -> None:
    assert _manifest_imports("common", "claude") == EXPECTED_CLAUDE_CORE_IMPORTS
