from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from functional_registry_checks import check_functional_registry
from g7_subcheck import collect_g7_subcheck
from registry_design_coverage_checks import check_registry_design_coverage
from trace_symmetry import collect_trace_symmetry


PAIR_NAMES = ("L6-L7", "L5-L8", "L4-L9", "L3-L12", "L1-L14")
DEFERRED_PAIR_REASONS = {
    "L5-L8": "execution_gate_not_implemented",
    "L4-L9": "execution_gate_not_implemented; semantic_gate_required",
    "L3-L12": "execution_gate_not_implemented",
    "L1-L14": "execution_gate_not_implemented",
}


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _filter_findings(report: Any, kind: str) -> list[dict[str, Any]]:
    return [finding for finding in report.findings if finding.kind == kind]


def _pair_clean(pair: dict[str, Any]) -> bool:
    return all(
        [
            pair.get("uncovered_req", {}).get("count", 0) == 0,
            pair.get("orphan_test", {}).get("count", 0) == 0,
            pair.get("duplicate_id", {}).get("count", 0) == 0,
            pair.get("missing_pair_frontmatter", {}).get("count", 0) == 0,
            pair.get("missing_pair", {}).get("count", 0) == 0,
            pair.get("wrong_layer_pair", {}).get("count", 0) == 0,
        ]
    )


def collect_vg_overview(project_root: Path | None = None) -> dict[str, Any]:
    root = _project_root(project_root)
    registry_path = root / "cli" / "config" / "functional-registry.yaml"

    registry_design = check_registry_design_coverage(registry_path, root)
    functional_registry = check_functional_registry(registry_path, root)
    trace = collect_trace_symmetry(root)
    g7 = collect_g7_subcheck(root, execute_tests=None)

    source_scan_findings = _filter_findings(functional_registry, "unregistered_asset")
    trace_complete_findings = _filter_findings(functional_registry, "invalid_fr_trace")

    pair_status: dict[str, dict[str, Any]] = {}
    for pair_name in PAIR_NAMES:
        pair = trace["pairs"][pair_name]
        trace_reason = (
            f"coverage={pair['coverage_pct']} "
            f"uncovered={pair['uncovered_req']['count']} "
            f"orphan={pair['orphan_test']['count']}"
        )
        if pair_name in DEFERRED_PAIR_REASONS:
            pair_status[pair_name] = {
                "status": "approved_deferred",
                "clean": _pair_clean(pair),
                "reason": f"{DEFERRED_PAIR_REASONS[pair_name]} {trace_reason}",
            }
            continue
        pair_status[pair_name] = {
            "status": "applicable",
            "clean": _pair_clean(pair),
            "reason": trace_reason,
        }

    pair_status["L6-L7"] = {
        "status": "applicable",
        "clean": (
            pair_status["L6-L7"]["clean"]
            and g7["missing"]["count"] == 0
            and g7["unanchored_but_exists"]["count"] == 0
            and g7["anchored"]["count"] == g7["exec_pass"]["count"]
        ),
        "reason": (
            f"anchored={g7['anchored']['count']}/{g7['ut_total']} "
            f"exec_pass={g7['exec_pass']['count']} "
            f"missing={g7['missing']['count']} "
            f"unanchored={g7['unanchored_but_exists']['count']}"
        ),
    }
    pair_status["L2-L10"] = {
        "status": "not_applicable",
        "clean": True,
        "reason": "ui_absent",
    }

    required_clean = {
        "registry_design_coverage": {
            "clean": len(registry_design.findings) == 0,
            "finding_count": len(registry_design.findings),
        },
        "source_scan_vs_registry": {
            "clean": len(source_scan_findings) == 0,
            "finding_count": len(source_scan_findings),
        },
        "registry_trace_complete": {
            "clean": len(trace_complete_findings) == 0,
            "finding_count": len(trace_complete_findings),
        },
    }

    all_required_clean = all(item["clean"] for item in required_clean.values())
    all_applicable_pairs_clean = all(
        payload["clean"]
        for payload in pair_status.values()
        if payload["status"] == "applicable"
    )

    return {
        "advisory": True,
        "exit_code": 0,
        "vg_overview": {
            "required_clean": required_clean,
            "pair_status": pair_status,
            "block_condition": "未承認 P0/P1 deferred finding > 0",
            "wired": ["freeze-pre", "push-pre"],
            "overall_clean": all_required_clean and all_applicable_pairs_clean,
        },
        "g7_subcheck": {
            "ut_total": g7["ut_total"],
            "anchored": g7["anchored"]["count"],
            "exec_pass": g7["exec_pass"]["count"],
            "missing": g7["missing"]["count"],
            "unanchored_but_exists": g7["unanchored_but_exists"]["count"],
        },
    }


def render_text(report: dict[str, Any]) -> str:
    vg = report["vg_overview"]
    lines = [
        "VG-overview (advisory)",
        f"overall_clean: {str(vg['overall_clean']).lower()}",
    ]
    for name, payload in vg["required_clean"].items():
        lines.append(f"{name}: clean={str(payload['clean']).lower()} findings={payload['finding_count']}")
    for pair_name, payload in vg["pair_status"].items():
        lines.append(
            f"{pair_name}: status={payload['status']} clean={str(payload['clean']).lower()} reason={payload['reason']}"
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advisory VG-overview aggregator.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = collect_vg_overview()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
