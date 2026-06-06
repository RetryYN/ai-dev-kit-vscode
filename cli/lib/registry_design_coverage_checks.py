"""registry_design_coverage detector — zero-omission(B') の機械証明.

functional-registry の全 active entry が設計層へ被覆されているか
(coverage_layer + design_ids + excluded_reason) を検査する。

正本: docs/v2/L1-requirements/helix-workflows-verification-strategy.md §11.7
      docs/v2/L3-requirements/helix-workflows-functional-registry.md §1.6
Process: process-2026-06-07-whole-source-design-coverage-closure

検査 (warn-only=advisory で開始 → Action4 後 ratchet → fail-close):
- unknown_coverage_layer: active entry が coverage_layer を持たない / enum 外 (= 抜け漏れ)
- excluded_reason_invalid: excluded_with_reason が excluded_reason enum を持たない
- design_id_missing: L4/L5/excluded が design_ids 空 (代表 ID 必須)
- l6_design_pending: L6_required が design_ids 空 (Action4 で FN/UT 1:1 付与予定、warn 許容)
- design_id_unresolved: design_id が既知 ID universe (anchor ∪ FN-*/MOD-*/IT-*/NFR-*/IF-*/ST-*) に無い
- wrong_layer: design_id prefix が coverage_layer と不整合
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from registry_checks import DetectorReport, Finding

COVERAGE_LAYERS = {"L6_required", "L5_required", "L4_required", "excluded_with_reason"}
EXCLUDED_REASONS = {"reference_doc", "static_template", "data_registry", "private_glue", "generated"}

# 代表 design anchor (TL: L4/L5/excluded は代表 ID で束ねてよい)。正本 = L3 §1.6。
ANCHORS = {
    "DSN-CMD-FAMILY", "DSN-AGENT-ROLE", "DSN-WORKFLOW-DOC", "DSN-SKILL-OPS",
    "DSN-TEMPLATE-RUNTIME", "DSN-CMD-LOGIC", "DSN-LIB-MODULE", "DSN-L4-OTHER",
    "EXCL-SKILL-REFDOC", "EXCL-STATIC-TEMPLATE", "EXCL-DATA-REGISTRY", "EXCL-OTHER",
}
# coverage_layer ごとに許容する design_id prefix / anchor
LAYER_ALLOWED = {
    "L6_required": ("FN-",),
    "L5_required": ("MOD-", "IT-", "DSN-LIB-MODULE", "DSN-CMD-LOGIC"),
    "L4_required": ("NFR-", "IF-", "ST-", "DSN-CMD-FAMILY", "DSN-AGENT-ROLE",
                    "DSN-WORKFLOW-DOC", "DSN-SKILL-OPS", "DSN-TEMPLATE-RUNTIME", "DSN-L4-OTHER"),
    "excluded_with_reason": ("EXCL-",),
}
REAL_ID_PREFIXES = ("FN-", "MOD-", "IT-", "NFR-", "IF-", "ST-")


def _resolved(design_id: str) -> bool:
    """design_id が既知 universe にあるか (anchor または 実 design ID prefix)."""
    if design_id in ANCHORS:
        return True
    return any(design_id.startswith(p) for p in REAL_ID_PREFIXES)


def _wrong_layer(layer: str, design_id: str) -> bool:
    allowed = LAYER_ALLOWED.get(layer, ())
    return not any(design_id == a or design_id.startswith(a) for a in allowed)


def check_registry_design_coverage(
    registry_path: str | Path,
    repo_root: str | Path | None = None,
) -> DetectorReport:
    path = Path(registry_path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries", [])
    findings: list[Finding] = []
    active = [e for e in entries if e.get("status") == "active"]

    unknown = 0
    for e in active:
        eid = str(e.get("id", "?"))
        layer = e.get("coverage_layer")
        if layer not in COVERAGE_LAYERS:
            unknown += 1
            findings.append(Finding(
                severity="P1", kind="unknown_coverage_layer", entry_id=eid,
                path=_p(path), message=f"coverage_layer 未設定/enum外: {layer!r}",
                remediation="L6_required/L5_required/L4_required/excluded_with_reason を付与 (§11.7)",
            ))
            continue

        design_ids = e.get("design_ids") or []
        if layer == "excluded_with_reason":
            er = e.get("excluded_reason")
            if er not in EXCLUDED_REASONS:
                findings.append(Finding(
                    severity="P2", kind="excluded_reason_invalid", entry_id=eid,
                    path=_p(path), message=f"excluded_reason 無効: {er!r}",
                    remediation=f"enum {sorted(EXCLUDED_REASONS)} のいずれかを付与",
                ))

        if not design_ids:
            if layer == "L6_required":
                findings.append(Finding(
                    severity="P3", kind="l6_design_pending", entry_id=eid,
                    path=_p(path), message="L6_required の FN-*/UT-* が未作成 (Action4 で 1:1 付与)",
                    remediation="L6 機能設計 FN-* + L7 単体テスト UT-* を 1:1 で起こす",
                ))
            else:
                findings.append(Finding(
                    severity="P2", kind="design_id_missing", entry_id=eid,
                    path=_p(path), message=f"{layer} に design_ids が無い",
                    remediation="代表 design_id (anchor) または具体 ID を付与",
                ))
            continue

        for did in design_ids:
            if not _resolved(did):
                findings.append(Finding(
                    severity="P2", kind="design_id_unresolved", entry_id=eid,
                    path=_p(path), message=f"design_id 未解決(実在せず): {did}",
                    remediation="設計 doc の実 ID または既知 anchor を指定",
                ))
            elif _wrong_layer(layer, did):
                findings.append(Finding(
                    severity="P2", kind="wrong_layer", entry_id=eid,
                    path=_p(path), message=f"{layer} に不整合な design_id: {did}",
                    remediation=f"{layer} は {LAYER_ALLOWED.get(layer)} のいずれかに対応させる",
                ))

    metrics = {
        "active_entries": len(active),
        "unknown_coverage_layer": unknown,
        "l6_required": sum(1 for e in active if e.get("coverage_layer") == "L6_required"),
        "design_id_missing": sum(1 for f in findings if f.kind == "design_id_missing"),
        "l6_design_pending": sum(1 for f in findings if f.kind == "l6_design_pending"),
        "wrong_layer": sum(1 for f in findings if f.kind == "wrong_layer"),
        "design_id_unresolved": sum(1 for f in findings if f.kind == "design_id_unresolved"),
    }
    return DetectorReport.build(
        check_name="check_registry_design_coverage",
        domain="registry_design_coverage",
        mode="advisory",
        findings=findings,
        metrics=metrics,
        baseline=set(),
    )


def _p(path: Path) -> str:
    return path.name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-path", default="cli/config/functional-registry.yaml")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    rep = check_registry_design_coverage(args.registry_path, args.repo_root)
    print(rep.render("json") if args.json else rep.render("text"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
