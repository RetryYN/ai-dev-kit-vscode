#!/usr/bin/env python3
"""新 15 工程 (L0-L14) frontmatter retrofit script.

commit eeb0530 で確立された PLAN 規約に合わせ、既存 kind=impl PLAN に
process_layer: L7 + parent_design を機械的に追加する。

parent_design の決定優先順:
  1. dependencies.parent (PLAN-NNN-*) → docs/plans/<file>.md
  2. related_adr (ADR-NNN) → docs/adr/ADR-NNN-*.md
  3. どちらもなければ TODO placeholder + コメント注記

pairs_test_design は本 script では追加しない (test design doc 実在確認が必要)。

usage:
  python3 scripts/retrofit_v2_process_layer.py --dry-run
  python3 scripts/retrofit_v2_process_layer.py --apply
  python3 scripts/retrofit_v2_process_layer.py --apply --only PLAN-002
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = REPO_ROOT / "docs" / "plans"
ADR_DIR = REPO_ROOT / "docs" / "adr"
TODO_PLACEHOLDER = "docs/v2/process/L07-implementation-sprint.md"  # 仮置き、retrofit pending
PLAN_ID_RE = re.compile(r"^PLAN-(?:MM-)?\d{2,3}[A-Z]?(?:-[a-z0-9-]+)?$", re.IGNORECASE)


def _resolve_parent_plan_path(plan_id_or_path: str) -> str | None:
    """dependencies.parent から docs/plans/<file>.md を解決。"""
    if not plan_id_or_path or not isinstance(plan_id_or_path, str):
        return None
    candidate = plan_id_or_path.strip()
    if candidate.startswith("docs/") and candidate.endswith(".md"):
        if (REPO_ROOT / candidate).exists():
            return candidate
        return None
    if not PLAN_ID_RE.match(candidate.split()[0]):
        return None
    base = candidate.split()[0]
    matches = sorted(PLANS_DIR.glob(f"{base}*.md"))
    if matches:
        return f"docs/plans/{matches[0].name}"
    return None


def _resolve_adr_path(related_adr: str | None) -> str | None:
    """related_adr (ADR-NNN ...) から docs/adr/ADR-NNN-*.md を解決。"""
    if not related_adr or not isinstance(related_adr, str):
        return None
    parts = [part.strip() for part in re.split(r"[,;]", related_adr) if part.strip()]
    for part in parts:
        m = re.match(r"^ADR-(\d{3})", part)
        if not m:
            continue
        adr_num = m.group(1)
        matches = sorted(ADR_DIR.glob(f"ADR-{adr_num}-*.md"))
        if matches:
            return f"docs/adr/{matches[0].name}"
    return None


def _decide_parent_design(fm: dict) -> tuple[str, str]:
    """parent_design path + 理由 を返す。"""
    deps = fm.get("dependencies")
    if isinstance(deps, dict):
        parent = deps.get("parent")
        if isinstance(parent, list):
            for p in parent:
                resolved = _resolve_parent_plan_path(p)
                if resolved:
                    return resolved, "from dependencies.parent"
        else:
            resolved = _resolve_parent_plan_path(parent)
            if resolved:
                return resolved, "from dependencies.parent"

    related = fm.get("related_adr")
    if isinstance(related, list):
        for r in related:
            resolved = _resolve_adr_path(r if isinstance(r, str) else None)
            if resolved:
                return resolved, "from related_adr"
    else:
        resolved = _resolve_adr_path(related if isinstance(related, str) else None)
        if resolved:
            return resolved, "from related_adr"

    return TODO_PLACEHOLDER, "placeholder (TODO: L6 機能設計 doc を後追い指定)"


def _split_frontmatter(text: str) -> tuple[list[str], int, list[str]] | None:
    """frontmatter block + end index + body を返す。frontmatter なしは None。"""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], i, lines[i + 1:]
    return None


def _insert_line(lines: list[str], new_lines: list[str], anchor_field: str = "status") -> list[str]:
    """anchor_field の直後に挿入。anchor が見つからなければ末尾に追加。"""
    result = list(lines)
    for idx, line in enumerate(result):
        if line.startswith(f"{anchor_field}:"):
            return result[: idx + 1] + new_lines + result[idx + 1:]
    return result + new_lines


def retrofit_plan(path: Path, *, apply: bool, only: str | None) -> dict:
    """1 PLAN を retrofit。戻り値は dict (status / reason / diff_lines)."""
    text = path.read_text(encoding="utf-8")
    split = _split_frontmatter(text)
    if split is None:
        return {"path": str(path), "status": "skip", "reason": "no_frontmatter"}
    fm_lines, end_idx, body_lines = split

    try:
        fm = yaml.safe_load("\n".join(fm_lines)) or {}
    except yaml.YAMLError as exc:
        return {"path": str(path), "status": "skip", "reason": f"yaml_error: {exc}"}

    if not isinstance(fm, dict):
        return {"path": str(path), "status": "skip", "reason": "non_mapping"}

    if fm.get("kind") != "impl":
        return {"path": str(path), "status": "skip", "reason": "not_impl"}

    plan_id = fm.get("plan_id") or path.stem
    if only and not (plan_id == only or path.stem == only or path.name == only):
        return {"path": str(path), "status": "skip", "reason": "not_in_only_filter"}

    has_process_layer = bool(fm.get("process_layer"))
    has_parent_design = bool(fm.get("parent_design"))
    if has_process_layer and has_parent_design:
        return {"path": str(path), "status": "skip", "reason": "already_retrofit"}

    insertions: list[str] = []
    if not has_process_layer:
        insertions.append("process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)")

    parent_design_reason = ""
    if not has_parent_design:
        parent_design, parent_design_reason = _decide_parent_design(fm)
        comment = f"# {parent_design_reason}"
        if parent_design_reason.startswith("placeholder"):
            insertions.append(f"parent_design: {parent_design}   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え")
        else:
            insertions.append(f"parent_design: {parent_design}   {comment}")

    new_fm_lines = _insert_line(list(fm_lines), insertions, anchor_field="status")
    new_text = "---\n" + "\n".join(new_fm_lines) + "\n---\n" + "\n".join(body_lines)
    if not new_text.endswith("\n"):
        new_text += "\n"

    if apply:
        path.write_text(new_text, encoding="utf-8")

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "plan_id": plan_id,
        "status": "applied" if apply else "would_apply",
        "added_process_layer": not has_process_layer,
        "added_parent_design": not has_parent_design,
        "parent_design_source": parent_design_reason if not has_parent_design else "(already set)",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V2 15 工程 retrofit script")
    parser.add_argument("--apply", action="store_true", help="実際に書き換える")
    parser.add_argument("--dry-run", action="store_true", help="差分のみ出力")
    parser.add_argument("--only", help="特定 PLAN ID / path のみ対象")
    args = parser.parse_args(argv)

    apply = args.apply and not args.dry_run

    counts = {"applied": 0, "would_apply": 0, "skip": 0}
    by_skip_reason: dict[str, int] = {}
    placeholder_count = 0

    for path in sorted(PLANS_DIR.glob("PLAN-*.md")):
        result = retrofit_plan(path, apply=apply, only=args.only)
        counts[result["status"]] = counts.get(result["status"], 0) + 1
        if result["status"] == "skip":
            by_skip_reason[result["reason"]] = by_skip_reason.get(result["reason"], 0) + 1
        if result.get("parent_design_source", "").startswith("placeholder"):
            placeholder_count += 1
            print(f"  TODO {result['plan_id']}: parent_design=placeholder", file=sys.stderr)

    print(f"Total PLAN scanned: {sum(counts.values())}")
    print(f"  applied: {counts.get('applied', 0)}")
    print(f"  would_apply (dry-run): {counts.get('would_apply', 0)}")
    print(f"  skip: {counts.get('skip', 0)}")
    for reason, count in sorted(by_skip_reason.items()):
        print(f"    skip[{reason}]: {count}")
    print(f"  parent_design as placeholder (TODO): {placeholder_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
