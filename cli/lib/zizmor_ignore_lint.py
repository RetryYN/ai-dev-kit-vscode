#!/usr/bin/env python3
"""PLAN-222 AC-5: zizmor:ignore コメント の metadata 機械検査.

ADR-036 D4 で定義した false positive 管理運用を機械強制する。
全 `# zizmor:ignore[...]` コメントが以下の metadata を持つことを検査:

- reason: 1-2 行、人間が読んで判断可能な内容
- owner: 責任者 @username または issue/ADR/PLAN reference
- expires または re-evaluate-when: 期限または再評価条件

対象設計 (① D-API): ADR-036 §D4 + skills/common/security/references/gha-security.md §2
テスト設計 (③ D-TEST-DESIGN): inline docstring + cli/lib/tests/test_zizmor_ignore_lint.py (将来)
テストコード (④ D-TEST-CODE): cli/lib/tests/test_zizmor_ignore_lint.py (将来、PLAN-222 carry)

使い方:

    python3 cli/lib/zizmor_ignore_lint.py [--strict] [paths...]

`--strict` 指定時は metadata 不揃いを exit 1 で fail-close 化する (default は warning のみ)。
paths 省略時は `.github/workflows/` を scan。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ZIZMOR_IGNORE_RE = re.compile(r"#\s*zizmor:ignore(?:\[([^\]]+)\])?\b(.*)$")
REASON_RE = re.compile(r"\breason\s*=\s*([^\s/]+(?:\s+[^\s/]+)*)", re.IGNORECASE)
OWNER_RE = re.compile(r"\bowner\s*=\s*(\S+)", re.IGNORECASE)
EXPIRES_RE = re.compile(r"\bexpires\s*=\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
REEVAL_RE = re.compile(r"\bre-evaluate(?:-when)?\s*=\s*(\S+(?:\s+\S+)*?)(?:\s+\w+\s*=|$)", re.IGNORECASE)


@dataclass(frozen=True)
class IgnoreFinding:
    path: Path
    line_number: int
    raw_line: str
    rule_name: str | None
    has_reason: bool
    has_owner: bool
    has_expiry: bool  # expires または re-evaluate-when

    @property
    def is_compliant(self) -> bool:
        return self.has_reason and self.has_owner and self.has_expiry

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.has_reason:
            missing.append("reason")
        if not self.has_owner:
            missing.append("owner")
        if not self.has_expiry:
            missing.append("expires or re-evaluate-when")
        return missing


def scan_file(path: Path) -> list[IgnoreFinding]:
    """1 file をスキャンし、zizmor:ignore コメントの metadata 検査結果を返す。"""
    findings: list[IgnoreFinding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings
    for line_num, line in enumerate(text.splitlines(), start=1):
        match = ZIZMOR_IGNORE_RE.search(line)
        if not match:
            continue
        rule_name = match.group(1)
        rest = match.group(2)
        findings.append(
            IgnoreFinding(
                path=path,
                line_number=line_num,
                raw_line=line.rstrip(),
                rule_name=rule_name,
                has_reason=bool(REASON_RE.search(rest)),
                has_owner=bool(OWNER_RE.search(rest)),
                has_expiry=bool(EXPIRES_RE.search(rest) or REEVAL_RE.search(rest)),
            )
        )
    return findings


def scan_paths(paths: list[Path]) -> list[IgnoreFinding]:
    """複数 path (file または directory) を再帰的にスキャン。"""
    all_findings: list[IgnoreFinding] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            all_findings.extend(scan_file(path))
            continue
        for yaml_path in sorted(path.rglob("*.yml")):
            all_findings.extend(scan_file(yaml_path))
        for yaml_path in sorted(path.rglob("*.yaml")):
            all_findings.extend(scan_file(yaml_path))
    return all_findings


def format_finding(finding: IgnoreFinding) -> str:
    rel = finding.path
    try:
        rel = finding.path.relative_to(Path.cwd())
    except ValueError:
        pass
    rule_part = f"[{finding.rule_name}]" if finding.rule_name else ""
    missing = ", ".join(finding.missing_fields()) or "none"
    return f"{rel}:{finding.line_number}: zizmor:ignore{rule_part} missing={missing}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zizmor_ignore_lint.py",
        description="Lint zizmor:ignore comments for required metadata (reason / owner / expiry).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".github/workflows")],
        help="Files or directories to scan (default: .github/workflows)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on non-compliant findings (default: warning only)",
    )
    args = parser.parse_args(argv)

    findings = scan_paths(args.paths)
    non_compliant = [f for f in findings if not f.is_compliant]

    if not findings:
        print("zizmor:ignore lint: no ignore comments found")
        return 0

    print(f"zizmor:ignore lint: scanned {len(findings)} ignore comment(s)")
    if non_compliant:
        print(f"zizmor:ignore lint: {len(non_compliant)} non-compliant finding(s):")
        for finding in non_compliant:
            print(f"  {format_finding(finding)}")
        if args.strict:
            return 1
        else:
            print("zizmor:ignore lint: WARN (use --strict for fail-close)")
            return 0
    else:
        print(f"zizmor:ignore lint: all {len(findings)} finding(s) compliant")
        return 0


if __name__ == "__main__":
    sys.exit(main())
