from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml

from coding_rule_lint import (
    collect_coding_rule_lint_full_required_summary,
    collect_coding_rule_lint_gate_summary,
)
from ddd_registry_checks import check_bc_anti_corruption, check_bc_mode_coverage
from dependency_cycle_checks import (
    collect_dependency_cycle_gate_summary,
    collect_import_cycle_baseline_required_summary,
)
from design_id_existence_checks import check_design_id_existence
from fr_uses_checks import collect_fr_uses_full_required_summary, collect_fr_uses_gate_summary
from functional_registry_checks import check_functional_registry
from fn_ut_pair_coverage_checks import check_fn_ut_pair_coverage
from g7_subcheck import collect_g7_subcheck
from g8_subcheck import collect_g8_subcheck
from plan_dependency_gate import (
    collect_plan_dependency_baseline_required_summary,
    collect_plan_dependency_gate_summary,
)
from registry_design_coverage_checks import check_registry_design_coverage
from requirement_drift import collect_requirement_drift
from trace_symmetry import collect_trace_symmetry


PAIR_NAMES = ("L6-L7", "L5-L8", "L4-L9", "L3-L12", "L1-L14")
L2_L10_WAIVER_PATH = Path("docs/v2/L2-screen-design/helix-workflows-ui-absent-waiver.md")
SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS = {"cli/lib/g8_subcheck.py"}
DEFERRED_PAIR_REASONS = {
    "L4-L9": "execution_gate_not_implemented; semantic_gate_required",
    "L3-L12": "execution_gate_not_implemented",
    "L1-L14": "execution_gate_not_implemented",
}
STRICT_FULL_FLOW_VERIFY_COMMAND = (
    "HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json"
)
DEFERRED_PAIR_EXECUTION_GATES = {
    "L5-L8": {
        "gate_id": "G8",
        "source_layer": "L5",
        "target_layer": "L8",
        "target": "Phase5-G8",
        "evidence": "integration test anchor + execution pass + L5-L8 post trace",
        "next_action": "implement G8 integration-test execution gate",
        "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
    },
    "L4-L9": {
        "gate_id": "G9",
        "source_layer": "L4",
        "target_layer": "L9",
        "target": "G9",
        "evidence": "system test anchor + execution pass + L4-L9 semantic post trace",
        "next_action": "implement G9 system-test execution gate",
        "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
    },
    "L3-L12": {
        "gate_id": "G12",
        "source_layer": "L3",
        "target_layer": "L12",
        "target": "G12",
        "evidence": "acceptance test anchor + execution pass + L3-L12 closure",
        "next_action": "implement G12 acceptance-test execution gate",
        "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
    },
    "L1-L14": {
        "gate_id": "G14",
        "source_layer": "L1",
        "target_layer": "L14",
        "target": "G14",
        "evidence": "operational test execution + L1-L14 operational closure",
        "next_action": "implement G14 operational-learning execution gate",
        "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
    },
}

_DEFAULT_COLLECT_FR_USES_GATE_SUMMARY = collect_fr_uses_gate_summary
_DEFAULT_COLLECT_CODING_RULE_LINT_GATE_SUMMARY = collect_coding_rule_lint_gate_summary
_DEFAULT_COLLECT_DEPENDENCY_CYCLE_GATE_SUMMARY = collect_dependency_cycle_gate_summary
_DEFAULT_COLLECT_PLAN_DEPENDENCY_GATE_SUMMARY = collect_plan_dependency_gate_summary


def _coding_rule_lint_required_clean_summary(root: Path) -> dict[str, Any]:
    # Keep legacy monkeypatch points usable in existing tests while production
    # switches the required_clean source to core-only full-required semantics.
    if collect_coding_rule_lint_gate_summary is not _DEFAULT_COLLECT_CODING_RULE_LINT_GATE_SUMMARY:
        return _ratchet_required_clean(collect_coding_rule_lint_gate_summary(repo_root=root))
    return collect_coding_rule_lint_full_required_summary(repo_root=root)


def _fr_uses_required_clean_summary(root: Path) -> dict[str, Any]:
    # Keep legacy monkeypatch points usable in existing tests while production
    # switches the required_clean source to full-scan/full-required semantics.
    if collect_fr_uses_gate_summary is not _DEFAULT_COLLECT_FR_USES_GATE_SUMMARY:
        return collect_fr_uses_gate_summary(repo_root=root)
    return collect_fr_uses_full_required_summary(repo_root=root)


def _dependency_cycle_required_clean_summary(root: Path) -> dict[str, Any]:
    # Keep legacy monkeypatch points usable in existing tests while production
    # switches the required_clean source to baseline-required semantics.
    if collect_dependency_cycle_gate_summary is not _DEFAULT_COLLECT_DEPENDENCY_CYCLE_GATE_SUMMARY:
        return _ratchet_required_clean(collect_dependency_cycle_gate_summary(repo_root=root))
    return collect_import_cycle_baseline_required_summary(repo_root=root)


def _plan_dependency_required_clean_summary(root: Path) -> dict[str, Any]:
    # Keep legacy monkeypatch points usable in existing tests while production
    # switches the required_clean source to baseline-required semantics.
    if collect_plan_dependency_gate_summary is not _DEFAULT_COLLECT_PLAN_DEPENDENCY_GATE_SUMMARY:
        return _ratchet_required_clean(collect_plan_dependency_gate_summary(repo_root=root))
    return collect_plan_dependency_baseline_required_summary(repo_root=root)


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


def _read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            payload = yaml.safe_load("\n".join(lines[1:index])) or {}
            return payload if isinstance(payload, dict) else {}
    return {}


def _l2_l10_status(root: Path) -> dict[str, Any]:
    waiver_path = root / L2_L10_WAIVER_PATH
    if not waiver_path.is_file():
        return {
            "status": "applicable",
            "clean": False,
            "reason": f"ui waiver missing: {L2_L10_WAIVER_PATH.as_posix()}",
            "waiver": None,
        }

    frontmatter = _read_frontmatter(waiver_path)
    applicability = str(frontmatter.get("applicability", "")).strip()
    reason = str(frontmatter.get("reason", "")).strip()
    pairs_with = str(frontmatter.get("pairs_with", "")).strip()
    owner = str(frontmatter.get("owner", "")).strip()
    process_layer = str(frontmatter.get("process_layer", "")).strip()
    clean = (
        applicability == "not_applicable"
        and reason == "ui_absent"
        and pairs_with == "L10"
        and process_layer == "L2"
        and bool(owner)
    )
    waiver = {
        "path": L2_L10_WAIVER_PATH.as_posix(),
        "doc_id": str(frontmatter.get("doc_id", "")).strip(),
        "applicability": applicability,
        "reason": reason,
        "owner": owner,
        "process_layer": process_layer,
        "pairs_with": pairs_with,
        "reference": "HELIX-workflows/helix-process/automation-gate-map.md",
        "unskip_required_when": [
            "official docs site or web UI is added",
            "interactive UI/TUI/visual mock/dashboard is added",
            "downstream product screens are introduced",
        ],
    }
    return {
        "status": "not_applicable" if clean else "applicable",
        "clean": clean,
        "reason": (
            f"ui_absent waiver={L2_L10_WAIVER_PATH.as_posix()}"
            if clean
            else f"invalid ui waiver: applicability={applicability or '<missing>'} "
            f"reason={reason or '<missing>'} pairs_with={pairs_with or '<missing>'}"
        ),
        "waiver": waiver,
    }


def _requirement_drift_required_clean(root: Path) -> dict[str, Any]:
    report = collect_requirement_drift(root, focus="L6")
    findings = report.get("findings", {})
    summary = report.get("summary", {})
    blocking_count = int(summary.get("blocking_findings", 0))
    return {
        "clean": bool(report.get("blocking_clean")) and blocking_count == 0,
        "finding_count": blocking_count,
        "focus": report.get("focus", "L6"),
        "requirements": summary.get("requirements", 0),
        "design_links": summary.get("design_links", 0),
        "advisory_count": summary.get("advisory_findings", 0),
        "waived_count": len(findings.get("waived_with_reason", [])),
    }


def _ratchet_required_clean(summary: dict[str, Any]) -> dict[str, Any]:
    source_status = str(summary.get("source_status", "not_applicable"))
    skipped_reason = summary.get("skipped_reason")
    entry = {
        "clean": bool(summary.get("clean", False)),
        "finding_count": int(summary.get("finding_count", 0)),
        "source_status": source_status,
        "skipped_reason": skipped_reason,
    }
    if source_status == "unavailable":
        entry["clean"] = True
    return entry


def live_strict_deferred_pairs(project_root: Path | None = None) -> list[dict[str, Any]]:
    root = _project_root(project_root)
    report = collect_vg_overview(root, strict_full_flow=True, execute_g7_tests=False)
    deferred_pairs = report["vg_overview"]["full_flow_execution"]["deferred_pairs"]
    return sorted(
        (dict(item) for item in deferred_pairs),
        key=lambda item: int(str(item["gate_id"])[1:]),
    )


def collect_vg_overview(
    project_root: Path | None = None,
    *,
    strict_full_flow: bool = False,
    execute_g7_tests: bool | None = None,
    execute_g8_tests: bool | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    if execute_g8_tests is None and execute_g7_tests is not None:
        execute_g8_tests = execute_g7_tests
    registry_path = root / "cli" / "config" / "functional-registry.yaml"

    registry_design = check_registry_design_coverage(registry_path, root)
    design_id_existence = check_design_id_existence(
        registry_path,
        "docs/v2/L6-functional-design/*.md",
        root,
    )
    fn_ut_pair = check_fn_ut_pair_coverage(
        registry_path,
        root / "docs" / "v2" / "L7-test-design" / "g7-test-anchor-map.yaml",
        root,
    )
    ddd_bc_reports = (
        check_bc_anti_corruption(root / "cli" / "config" / "ddd-registry.yaml", root),
        check_bc_mode_coverage(root / "cli" / "config" / "ddd-registry.yaml", root),
    )
    coding_rule_lint = _coding_rule_lint_required_clean_summary(root)
    dependency_cycle = _dependency_cycle_required_clean_summary(root)
    plan_dependency = _plan_dependency_required_clean_summary(root)
    fr_uses = _fr_uses_required_clean_summary(root)
    functional_registry = check_functional_registry(registry_path, root)
    trace = collect_trace_symmetry(root)
    g7 = collect_g7_subcheck(root, execute_tests=execute_g7_tests)
    g8 = collect_g8_subcheck(root, execute_tests=execute_g8_tests)
    requirement_drift = _requirement_drift_required_clean(root)

    source_scan_findings = [
        finding
        for finding in _filter_findings(functional_registry, "unregistered_asset")
        if finding.path not in SOURCE_SCAN_ALLOWED_UNREGISTERED_PATHS
    ]
    trace_complete_findings = _filter_findings(functional_registry, "invalid_fr_trace")

    pair_status: dict[str, dict[str, Any]] = {}
    for pair_name in PAIR_NAMES:
        pair = trace["pairs"][pair_name]
        trace_reason = (
            f"coverage={pair['coverage_pct']} "
            f"uncovered={pair['uncovered_req']['count']} "
            f"orphan={pair['orphan_test']['count']}"
        )
        if pair_name == "L5-L8":
            g8_gate_clean = (
                _pair_clean(pair)
                and g8["anchored"]["count"] == g8["it_total"]
                and g8["missing"]["count"] == 0
                and g8["unanchored_but_exists"]["count"] == 0
                and g8["exec_pass"]["count"] == g8["anchored"]["count"]
            )
            pair_status[pair_name] = {
                "status": "applicable" if g8_gate_clean else "approved_deferred",
                "clean": _pair_clean(pair),
                "reason": (
                    f"{trace_reason} "
                    f"anchored={g8['anchored']['count']}/{g8['it_total']} "
                    f"exec_pass={g8['exec_pass']['count']} "
                    f"missing={g8['missing']['count']} "
                    f"unanchored={g8['unanchored_but_exists']['count']}"
                ),
            }
            continue
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
    pair_status["L2-L10"] = _l2_l10_status(root)

    required_clean = {
        "registry_design_coverage": {
            "clean": len(registry_design.findings) == 0,
            "finding_count": len(registry_design.findings),
        },
        "design_id_existence": {
            "clean": len(design_id_existence.findings) == 0,
            "finding_count": len(design_id_existence.findings),
        },
        "fn_ut_pair_coverage": {
            "clean": len(fn_ut_pair.findings) == 0,
            "finding_count": len(fn_ut_pair.findings),
        },
        "ddd_bc_coverage": {
            "clean": sum(len(report.findings) for report in ddd_bc_reports) == 0,
            "finding_count": sum(len(report.findings) for report in ddd_bc_reports),
        },
        "coding_rule_lint": dict(coding_rule_lint),
        "dependency_cycle_checks": dict(dependency_cycle),
        "plan_dependency_gate": dict(plan_dependency),
        "fr_uses_checks": dict(fr_uses),
        "source_scan_vs_registry": {
            "clean": len(source_scan_findings) == 0,
            "finding_count": len(source_scan_findings),
        },
        "registry_trace_complete": {
            "clean": len(trace_complete_findings) == 0,
            "finding_count": len(trace_complete_findings),
        },
        "requirement_drift": requirement_drift,
    }

    deferred_pairs = [
        {
            "pair": pair_name,
            "reason": payload["reason"],
            **DEFERRED_PAIR_EXECUTION_GATES.get(pair_name, {}),
        }
        for pair_name, payload in pair_status.items()
        if payload["status"] == "approved_deferred"
    ]
    not_applicable_pairs = [
        {
            "pair": pair_name,
            "reason": payload["reason"],
            "waiver": payload.get("waiver"),
        }
        for pair_name, payload in pair_status.items()
        if payload["status"] == "not_applicable"
    ]
    full_flow_execution = {
        "enforced": strict_full_flow,
        "clean": len(deferred_pairs) == 0,
        "deferred_count": len(deferred_pairs),
        "deferred_pairs": deferred_pairs,
        "not_applicable_count": len(not_applicable_pairs),
        "not_applicable_pairs": not_applicable_pairs,
    }

    all_required_clean = all(item["clean"] for item in required_clean.values())
    all_applicable_pairs_clean = all(
        payload["clean"]
        for payload in pair_status.values()
        if payload["status"] == "applicable"
    )
    full_flow_execution_clean = (not strict_full_flow) or full_flow_execution["clean"]

    return {
        "advisory": True,
        "exit_code": 0,
        "vg_overview": {
            "required_clean": required_clean,
            "pair_status": pair_status,
            "full_flow_execution": full_flow_execution,
            "block_condition": (
                "approved_deferred execution gate > 0"
                if strict_full_flow
                else "未承認 P0/P1 deferred finding > 0"
            ),
            "wired": ["freeze-pre", "push-pre"],
            "overall_clean": all_required_clean and all_applicable_pairs_clean and full_flow_execution_clean,
        },
        "g7_subcheck": {
            "ut_total": g7["ut_total"],
            "anchored": g7["anchored"]["count"],
            "exec_pass": g7["exec_pass"]["count"],
            "missing": g7["missing"]["count"],
            "unanchored_but_exists": g7["unanchored_but_exists"]["count"],
        },
        "g8_subcheck": {
            "it_total": g8["it_total"],
            "anchored": g8["anchored"]["count"],
            "exec_pass": g8["exec_pass"]["count"],
            "missing": g8["missing"]["count"],
            "unanchored_but_exists": g8["unanchored_but_exists"]["count"],
        },
    }


def render_text(report: dict[str, Any]) -> str:
    vg = report["vg_overview"]
    lines = [
        "VG-overview (advisory)",
        f"overall_clean: {str(vg['overall_clean']).lower()}",
        "full_flow_execution: "
        f"enforced={str(vg['full_flow_execution']['enforced']).lower()} "
        f"clean={str(vg['full_flow_execution']['clean']).lower()} "
        f"deferred={vg['full_flow_execution']['deferred_count']}",
    ]
    for name, payload in vg["required_clean"].items():
        suffix = ""
        if "source_status" in payload:
            suffix += f" source_status={payload['source_status']}"
        if payload.get("skipped_reason"):
            suffix += f" skipped_reason={payload['skipped_reason']}"
        lines.append(
            f"{name}: clean={str(payload['clean']).lower()} findings={payload['finding_count']}{suffix}"
        )
    for pair_name, payload in vg["pair_status"].items():
        lines.append(
            f"{pair_name}: status={payload['status']} clean={str(payload['clean']).lower()} reason={payload['reason']}"
        )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advisory VG-overview aggregator.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--strict-full-flow",
        action="store_true",
        help="treat approved_deferred execution gates as not clean for full L0-L14 completion audit",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = collect_vg_overview(strict_full_flow=args.strict_full_flow)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["vg_overview"]["overall_clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
