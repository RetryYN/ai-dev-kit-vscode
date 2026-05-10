from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAN_DIR = ROOT / "docs" / "plans"


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError("frontmatter terminator not found")
    return text[end + len("\n---\n") :]


def body_hash(path: Path) -> str:
    body = strip_frontmatter(path.read_text(encoding="utf-8"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def git_body_hash(repo_path: str) -> str:
    raw = subprocess.check_output(
        ["git", "show", f"HEAD:{repo_path}"],
        cwd=ROOT,
        text=True,
    )
    return hashlib.sha256(strip_frontmatter(raw).encode("utf-8")).hexdigest()


def test_legacy_plan_migration_preserves_body_hashes() -> None:
    files = {
        "PLAN-012": ("docs/plans/PLAN-012-code-index-coverage.md", PLAN_DIR / "PLAN-012-code-index-coverage.md"),
        "PLAN-013": ("docs/plans/PLAN-013-code-index-eligibility-taxonomy.md", PLAN_DIR / "PLAN-013-code-index-eligibility-taxonomy.md"),
        "PLAN-014": ("docs/plans/PLAN-014-stop-hook-idempotency.md", PLAN_DIR / "PLAN-014-stop-hook-idempotency.md"),
        "PLAN-015": ("docs/plans/PLAN-015-stop-hook-test-guard-hack.md", PLAN_DIR / "PLAN-015-stop-hook-test-guard-hack.md"),
        "PLAN-016": ("docs/plans/PLAN-016-session-summary-helix-log-report.md", PLAN_DIR / "PLAN-016-session-summary-helix-log-report.md"),
        "PLAN-028": ("docs/plans/PLAN-028-helix-v2-orchestration.md", PLAN_DIR / "PLAN-028-helix-v2-orchestration.md"),
        "PLAN-002": ("docs/plans/PLAN-002-helix-fullauto-foundation.md", PLAN_DIR / "PLAN-002-helix-fullauto-foundation.md"),
    }

    for plan_id, (repo_path, path) in files.items():
        assert body_hash(path) == git_body_hash(repo_path), plan_id
