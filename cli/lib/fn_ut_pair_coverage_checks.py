"""fn_ut_pair_coverage detector.

functional-registry の L6_required entry に対して、機能設計 FN-* と
単体テスト設計 UT-* / RD-UT-* の 1:1 対応を検査する advisory detector。

検査:
- missing_test_design: design_ids に対応する test_design_ids が無い
- unanchored_ut: test_design_ids の UT-* が g7-test-anchor-map.yaml に無い
- orphan_ut: anchor map にある UT-* の対応 FN-* が L6_required design_ids に無い
- duplicate_test_design: 同一 UT が複数 entry の test_design_ids に重複
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from g7_subcheck import load_anchor_map, load_ut_inventory
from registry_checks import DetectorReport, Finding

WAIVER_KEY = "fn_ut_pair_waivers"


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


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _expected_ut_for_fn(fn_id: str) -> str | None:
    if fn_id.startswith("FN-RD-"):
        return f"RD-UT-{fn_id.removeprefix('FN-RD-')}"
    if fn_id.startswith("FN-"):
        return f"UT-{fn_id.removeprefix('FN-')}"
    return None


def _expected_fn_for_ut(ut_id: str) -> str | None:
    if ut_id.startswith("RD-UT-"):
        return f"FN-RD-{ut_id.removeprefix('RD-UT-')}"
    if ut_id.startswith("UT-"):
        return f"FN-{ut_id.removeprefix('UT-')}"
    return None


def _load_waivers(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    raw_waivers = payload.get(WAIVER_KEY) or []
    if not isinstance(raw_waivers, list):
        return {}

    waivers: dict[tuple[str, str], dict[str, str]] = {}
    for item in raw_waivers:
        if not isinstance(item, dict):
            continue
        fn_id = str(item.get("fn") or "").strip()
        ut_id = str(item.get("ut") or "").strip()
        reason = str(item.get("reason") or "").strip()
        owner = str(item.get("owner") or "").strip()
        if fn_id and ut_id and reason and owner:
            waivers[(fn_id, ut_id)] = {
                "fn": fn_id,
                "ut": ut_id,
                "reason": reason,
                "owner": owner,
            }
    return waivers


def check_fn_ut_pair_coverage(
    registry_path: str | Path,
    anchor_map_path: str | Path,
    root: str | Path,
) -> DetectorReport:
    root_path = Path(root).resolve()
    registry = _resolve_path(registry_path, root_path)
    anchor_map = _resolve_path(anchor_map_path, root_path)

    payload = yaml.safe_load(registry.read_text(encoding="utf-8")) or {}
    entries = payload.get("entries", [])
    waivers = _load_waivers(payload)
    anchored_tests = set(load_anchor_map(anchor_map))
    l7_design_inventory = set(load_ut_inventory(root_path))
    findings: list[Finding] = []

    l6_entries = [
        entry
        for entry in entries
        if entry.get("status") == "active" and entry.get("coverage_layer") == "L6_required"
    ]

    all_fn_ids: set[str] = set()
    ut_to_entry_ids: dict[str, list[str]] = {}
    total_expected_pairs = 0

    for entry in l6_entries:
        entry_id = str(entry.get("id", "?"))
        design_ids = [item for item in _normalize_list(entry.get("design_ids")) if item.startswith("FN-")]
        test_design_ids = _normalize_list(entry.get("test_design_ids"))
        all_fn_ids.update(design_ids)

        for ut_id in test_design_ids:
            ut_to_entry_ids.setdefault(ut_id, []).append(entry_id)

        for fn_id in design_ids:
            expected_ut = _expected_ut_for_fn(fn_id)
            if expected_ut is None:
                continue
            total_expected_pairs += 1
            if expected_ut not in test_design_ids and (fn_id, expected_ut) not in waivers:
                findings.append(
                    Finding(
                        severity="P1",
                        kind="missing_test_design",
                        entry_id=entry_id,
                        path=_rel(registry, root_path),
                        message=f"{fn_id} に対応する test_design_ids が無い: {expected_ut}",
                        remediation="functional-registry.yaml に test_design_ids を追加するか waiver を登録",
                    )
                )

        for ut_id in test_design_ids:
            if ut_id.startswith("RD-UT-"):
                continue
            expected_fn = _expected_fn_for_ut(ut_id)
            if ut_id not in l7_design_inventory and (expected_fn, ut_id) not in waivers:
                findings.append(
                    Finding(
                        severity="P1",
                        kind="ut_not_in_l7_design",
                        entry_id=entry_id,
                        path="docs/v2/L7-test-design",
                        message=f"test_design_ids の {ut_id} が L7 test-design doc inventory に無い",
                        remediation="docs/v2/L7-test-design/*.md に UT row を追加する",
                    )
                )
            if ut_id not in anchored_tests and (expected_fn, ut_id) not in waivers:
                findings.append(
                    Finding(
                        severity="P1",
                        kind="unanchored_ut",
                        entry_id=entry_id,
                        path=_rel(anchor_map, root_path),
                        message=f"test_design_ids の {ut_id} が anchor map に無い",
                        remediation="g7-test-anchor-map.yaml に UT anchor を追加する",
                    )
                )

    for ut_id, entry_ids in sorted(ut_to_entry_ids.items()):
        if len(entry_ids) <= 1:
            continue
        findings.append(
            Finding(
                severity="P1",
                kind="duplicate_test_design",
                entry_id=",".join(sorted(set(entry_ids))),
                path=_rel(registry, root_path),
                message=f"{ut_id} が複数 entry に重複している: {', '.join(entry_ids)}",
                remediation="test_design_ids の重複を解消し、UT を 1 entry にのみ対応付ける",
            )
        )

    for ut_id in sorted(anchored_tests):
        if ut_id.startswith("RD-UT-"):
            continue
        expected_fn = _expected_fn_for_ut(ut_id)
        if expected_fn is None:
            continue
        if expected_fn not in all_fn_ids and (expected_fn, ut_id) not in waivers:
            findings.append(
                Finding(
                    severity="P1",
                    kind="orphan_ut",
                    entry_id=ut_id,
                    path=_rel(anchor_map, root_path),
                    message=f"{ut_id} は anchor 済みだが対応 FN が L6_required design_ids に無い: {expected_fn}",
                    remediation="対応する L6_required entry に design_ids/test_design_ids を追加するか waiver を登録",
                )
            )

    metrics = {
        "l6_required_entries": len(l6_entries),
        "expected_pairs": total_expected_pairs,
        "test_design_ids": sum(len(_normalize_list(entry.get("test_design_ids"))) for entry in l6_entries),
        "anchored_ut": len([ut_id for ut_id in anchored_tests if ut_id.startswith("UT-")]),
        "waivers": len(waivers),
        "missing_test_design": sum(1 for finding in findings if finding.kind == "missing_test_design"),
        "ut_not_in_l7_design": sum(1 for finding in findings if finding.kind == "ut_not_in_l7_design"),
        "unanchored_ut": sum(1 for finding in findings if finding.kind == "unanchored_ut"),
        "orphan_ut": sum(1 for finding in findings if finding.kind == "orphan_ut"),
        "duplicate_test_design": sum(1 for finding in findings if finding.kind == "duplicate_test_design"),
    }

    return DetectorReport.build(
        check_name="check_fn_ut_pair_coverage",
        domain="fn_ut_pair_coverage",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-path", default="cli/config/functional-registry.yaml")
    ap.add_argument("--anchor-map-path", default="docs/v2/L7-test-design/g7-test-anchor-map.yaml")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = check_fn_ut_pair_coverage(args.registry_path, args.anchor_map_path, args.root)
    print(report.render("json") if args.json else report.render("text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
