"""design_id_existence detector.

functional-registry の L6_required entry に紐づく design_ids(FN-*) が
L6 設計 doc 群のどこかに実在するかを検査する advisory detector。
"""

from __future__ import annotations

import argparse
import re
from glob import glob
from pathlib import Path
from typing import Any

import yaml

from registry_checks import DetectorReport, Finding

WAIVER_KEY = "design_id_existence_waivers"
HEADING_FN_RE = re.compile(r"^\s{0,3}#{1,6}\s+(FN-[A-Z0-9-]+)\b")
TABLE_ROW_FN_RE = re.compile(r"^\|\s*(FN-[A-Z0-9-]+)\s*\|")


def _normalize_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    value = str(raw).strip()
    return [value] if value else []


def _resolve_path(path_like: str | Path, root: Path) -> Path:
    path = Path(path_like)
    return path if path.is_absolute() else root / path


def _glob_paths(pattern: str | Path, root: Path) -> list[Path]:
    raw_pattern = str(pattern)
    if Path(raw_pattern).is_absolute():
        matches = glob(raw_pattern)
    else:
        matches = glob(str(root / raw_pattern))
    return sorted(Path(match).resolve() for match in matches)


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _load_waivers(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw_waivers = payload.get(WAIVER_KEY) or []
    if not isinstance(raw_waivers, list):
        return {}

    waivers: dict[str, dict[str, str]] = {}
    for item in raw_waivers:
        if not isinstance(item, dict):
            continue
        fn_id = str(item.get("fn") or "").strip()
        reason = str(item.get("reason") or "").strip()
        owner = str(item.get("owner") or "").strip()
        if fn_id and reason and owner:
            waivers[fn_id] = {"fn": fn_id, "reason": reason, "owner": owner}
    return waivers


def _collect_known_fn_ids(doc_paths: list[Path]) -> set[str]:
    known: set[str] = set()
    for doc_path in doc_paths:
        for line in doc_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            heading_match = HEADING_FN_RE.match(line)
            if heading_match:
                known.add(heading_match.group(1))
                continue
            table_match = TABLE_ROW_FN_RE.match(line)
            if table_match:
                known.add(table_match.group(1))
    return known


def check_design_id_existence(
    registry_path: str | Path,
    design_doc_glob: str | Path,
    root: str | Path,
) -> DetectorReport:
    root_path = Path(root).resolve()
    registry = _resolve_path(registry_path, root_path)
    payload = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    entries = payload.get("entries", [])
    waivers = _load_waivers(payload)
    doc_paths = _glob_paths(design_doc_glob, root_path)
    known_fn_ids = _collect_known_fn_ids(doc_paths)
    findings: list[Finding] = []

    l6_entries = [
        entry
        for entry in entries
        if entry.get("status") == "active" and entry.get("coverage_layer") == "L6_required"
    ]

    checked_fn_ids: set[str] = set()
    for entry in l6_entries:
        entry_id = str(entry.get("id", "?"))
        for fn_id in _normalize_list(entry.get("design_ids")):
            if not fn_id.startswith("FN-"):
                continue
            checked_fn_ids.add(fn_id)
            if fn_id in known_fn_ids or fn_id in waivers:
                continue
            findings.append(
                Finding(
                    severity="P1",
                    kind="missing_design_section",
                    entry_id=entry_id,
                    path=_rel(registry, root_path),
                    message=f"{fn_id} が {design_doc_glob} のどこにも見つからない",
                    remediation="L6 設計 doc に FN section/anchor を追加するか design_id_existence_waivers を登録",
                )
            )

    metrics = {
        "l6_required_entries": len(l6_entries),
        "scanned_docs": len(doc_paths),
        "checked_fn_ids": len(checked_fn_ids),
        "waivers": len(waivers),
        "missing_design_section": sum(1 for finding in findings if finding.kind == "missing_design_section"),
    }
    return DetectorReport.build(
        check_name="check_design_id_existence",
        domain="design_id_existence",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-path", default="cli/config/functional-registry.yaml")
    ap.add_argument("--design-doc-glob", default="docs/v2/L6-functional-design/*.md")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = check_design_id_existence(args.registry_path, args.design_doc_glob, args.root)
    print(report.render("json") if args.json else report.render("text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
