#!/usr/bin/env python3
"""V-model 4 artifact 双方向 trace lint (PLAN-075 Phase 5)

対象設計 (① D-DB): なし (本 module は内部 helper)
本ファイル (② D-IMPL): cli/lib/vmodel_lint.py
テスト設計 (③ D-TEST-DESIGN-UNIT): cli/lib/tests/test_vmodel_lint.py docstring 内 inline case
テストコード (④ D-TEST-CODE-UNIT): cli/lib/tests/test_vmodel_lint.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency path
    yaml = None


HELIX_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = HELIX_ROOT / "docs" / "plans"
DEFERRED_FINDINGS = HELIX_ROOT / ".helix" / "audit" / "deferred-findings.yaml"

PLAN_ID_PATTERN = re.compile(r"\bPLAN-[A-Z0-9]+\b")
DESIGN_PATTERN = re.compile(r"D-API|D-DB|D-CONCEPT|D-FUNC|docs/v2/L3-detailed-design/")
IMPL_PATTERN = re.compile(r"cli/lib/[a-zA-Z0-9_/]+\.py")
TEST_DESIGN_PATTERN = re.compile(
    r"L4-test-design|PLAN-\d+(?:[A-Z])?-(?:unit|integration|system|acceptance)-test-design\.md|D-TEST-DESIGN"
)
TEST_CODE_PATTERN = re.compile(r"cli/lib/tests/test_[a-zA-Z0-9_]+\.py")


@dataclass
class LintResult:
    plan_id: str
    path: str
    design_ref: int = 0
    impl_ref: int = 0
    test_design_ref: int = 0
    test_code_ref: int = 0
    grandfather: bool = False
    missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return all(
            (
                self.design_ref > 0,
                self.impl_ref > 0,
                self.test_design_ref > 0,
                self.test_code_ref > 0,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "path": self.path,
            "complete": self.complete,
            "grandfather": self.grandfather,
            "missing": list(self.missing),
            "references": {
                "design": self.design_ref,
                "impl": self.impl_ref,
                "test_design": self.test_design_ref,
                "test_code": self.test_code_ref,
            },
        }


def _count_refs(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text))


def _extract_plan_id(plan_path: Path, text: str) -> str:
    frontmatter_match = re.search(r"^plan_id:\s*(PLAN-[A-Z0-9]+)\s*$", text, re.MULTILINE)
    if frontmatter_match:
        return frontmatter_match.group(1).upper()

    file_match = PLAN_ID_PATTERN.search(plan_path.stem.upper())
    if file_match:
        return file_match.group(0)

    return plan_path.stem.upper()


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _matches_plan_filter(result: LintResult, plan_id_filter: str | None) -> bool:
    if not plan_id_filter:
        return True
    normalized = plan_id_filter.strip().upper()
    return result.plan_id == normalized


# @helix:index id=vmodel-lint.load-grandfather-list domain=cli/lib summary=deferred-findings から grandfather PLAN 一覧を読む
def load_grandfather_list(path: Path | None = None) -> set[str]:
    deferred_path = path or DEFERRED_FINDINGS
    if yaml is None or not deferred_path.exists():
        return set()

    try:
        data = yaml.safe_load(deferred_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return set()

    if isinstance(data, dict):
        findings = data.get("findings", [])
    elif isinstance(data, list):
        findings = data
    else:
        findings = []

    grandfather: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        finding_id = str(finding.get("id", ""))
        if not (finding_id.startswith("DF-PLAN-") and finding_id.endswith("-AUDIT-001")):
            continue
        if finding.get("status") != "open":
            continue
        plan_id = str(finding.get("plan_id", "")).strip().upper()
        if plan_id:
            grandfather.add(plan_id)
    return grandfather


# @helix:index id=vmodel-lint.lint-plan domain=cli/lib summary=単一 PLAN の 4 artifact 参照を集計する
def lint_plan(plan_path: Path, grandfather: set[str], project_root: Path | None = None) -> LintResult:
    root = project_root or HELIX_ROOT
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    plan_id = _extract_plan_id(plan_path, text)
    result = LintResult(
        plan_id=plan_id,
        path=_display_path(plan_path, root),
        design_ref=_count_refs(DESIGN_PATTERN, text),
        impl_ref=_count_refs(IMPL_PATTERN, text),
        test_design_ref=_count_refs(TEST_DESIGN_PATTERN, text),
        test_code_ref=_count_refs(TEST_CODE_PATTERN, text),
        grandfather=plan_id in grandfather,
    )

    if result.design_ref == 0:
        result.missing.append("design")
    if result.impl_ref == 0:
        result.missing.append("impl")
    if result.test_design_ref == 0:
        result.missing.append("test-design")
    if result.test_code_ref == 0:
        result.missing.append("test-code")
    return result


# @helix:index id=vmodel-lint.lint-all domain=cli/lib summary=PLAN 一覧へ vmodel lint を適用する
def lint_all(
    plan_id_filter: str | None = None,
    plans_dir: Path | None = None,
    deferred_path: Path | None = None,
    project_root: Path | None = None,
) -> list[LintResult]:
    root = project_root or HELIX_ROOT
    target_plans_dir = plans_dir or PLANS_DIR
    grandfather = load_grandfather_list(deferred_path)
    results: list[LintResult] = []
    for plan_path in sorted(target_plans_dir.glob("PLAN-*.md")):
        result = lint_plan(plan_path, grandfather, root)
        if _matches_plan_filter(result, plan_id_filter):
            results.append(result)
    return results


# @helix:index id=vmodel-lint.format-text domain=cli/lib summary=text mode の lint 結果を整形する
def format_text(results: list[LintResult]) -> str:
    lines = ["=== V-model 4 artifact lint (PLAN-075 強化) ===", ""]
    complete_count = sum(1 for result in results if result.complete)
    grandfather_count = sum(1 for result in results if result.grandfather)
    incomplete_count = sum(1 for result in results if not result.complete and not result.grandfather)

    for result in results:
        counts = (
            f"(design={result.design_ref}, impl={result.impl_ref}, "
            f"test-design={result.test_design_ref}, test-code={result.test_code_ref})"
        )
        if result.grandfather:
            lines.append(f"[○] {result.plan_id}: grandfather (skip) {counts}")
            continue
        if result.complete:
            lines.append(f"[✓] {result.plan_id}: complete {counts}")
            continue
        lines.append(f"[⚠] {result.plan_id}: missing {','.join(result.missing)} {counts}")

    lines.extend(
        [
            "",
            (
                "Summary: "
                f"total={len(results)}, complete={complete_count}, "
                f"incomplete={incomplete_count} (non-grandfather), grandfather={grandfather_count}"
            ),
        ]
    )
    return "\n".join(lines)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V-model 4 artifact lint (PLAN-075)")
    parser.add_argument("--plan-id", help="特定 PLAN ID のみ lint")
    parser.add_argument("--strict", action="store_true", help="incomplete (non-grandfather) があれば exit 1")
    parser.add_argument("--json", action="store_true", help="JSON 出力")
    return parser


# @helix:index id=vmodel-lint.main domain=cli/lib summary=vmodel lint CLI entrypoint を実行する
def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    results = lint_all(plan_id_filter=args.plan_id)
    if args.json:
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    else:
        print(format_text(results))

    if args.strict and any(not result.complete and not result.grandfather for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
