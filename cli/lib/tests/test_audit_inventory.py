import sys
import textwrap
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_inventory import (
    dump_decisions_yaml,
    generate_decisions_draft,
    parse_inventory_raw,
    parse_inventory_summary,
)


SHA = "a" * 64


def test_parse_inventory_summary_extracts_keys(tmp_path: Path) -> None:
    summary = tmp_path / "summary.log"
    summary.write_text(
        textwrap.dedent(
            """\
            ## inventory-summary
            head_sha: abc123
            tracked_count: 2
            untracked_count: 1
            gitleaks_summary: no leaks detected
            completed_at: 2026-04-30T00:00:00Z
            """
        ),
        encoding="utf-8",
    )

    result = parse_inventory_summary(summary)

    assert result["head_sha"] == "abc123"
    assert result["tracked_count"] == "2"
    assert result["gitleaks_summary"] == "no leaks detected"


def test_parse_inventory_raw_extracts_tracked_files(tmp_path: Path) -> None:
    raw = tmp_path / "raw.log"
    raw.write_text(
        textwrap.dedent(
            """\
            ## inventory-run
            head_sha: abc123

            ## tracked files (git ls-files)
            cli/helix-audit
            cli/lib/audit_a1.py

            ## untracked (excluding .gitignore)
            scratch.txt
            """
        ),
        encoding="utf-8",
    )

    assert parse_inventory_raw(raw) == [
        "cli/helix-audit",
        "cli/lib/audit_a1.py",
    ]


def test_generate_decisions_draft_default_keep(tmp_path: Path) -> None:
    summary = tmp_path / "summary.log"
    raw = tmp_path / "raw.log"
    summary.write_text("tracked_count: 1\n", encoding="utf-8")
    raw.write_text(
        "## tracked files (git ls-files)\nsrc/a.py\n## untracked (excluding .gitignore)\n",
        encoding="utf-8",
    )

    draft = generate_decisions_draft(summary, raw, SHA)

    assert draft["decisions"][0]["candidate_id"] == "src/a.py"
    assert draft["decisions"][0]["decision"] == "keep"
    assert draft["decisions"][0]["fail_safe_action"] == "manual_review"
    assert draft["decisions"][0]["evidence"]["redacted"] is True


def test_generate_decisions_draft_includes_scope_hash(tmp_path: Path) -> None:
    summary = tmp_path / "summary.log"
    raw = tmp_path / "raw.log"
    summary.write_text("tracked_count: 1\n", encoding="utf-8")
    raw.write_text(
        "## tracked files (git ls-files)\nsrc/a.py\n## untracked (excluding .gitignore)\n",
        encoding="utf-8",
    )

    draft = generate_decisions_draft(summary, raw, SHA)

    assert draft["metadata"]["scope_hash"] == SHA
    assert draft["decisions"][0]["scope_hash"] == SHA


def test_dump_decisions_yaml_writes_valid_source_hash(tmp_path: Path) -> None:
    summary = tmp_path / "summary.log"
    raw = tmp_path / "raw.log"
    summary.write_text("tracked_count: 1\n", encoding="utf-8")
    raw.write_text(
        "## tracked files (git ls-files)\nsrc/a.py\n## untracked (excluding .gitignore)\n",
        encoding="utf-8",
    )

    text = dump_decisions_yaml(generate_decisions_draft(summary, raw, SHA))
    data = yaml.safe_load(text)

    assert len(data["metadata"]["source_hash"]) == 64
    assert data["metadata"]["source_hash"] != ""
