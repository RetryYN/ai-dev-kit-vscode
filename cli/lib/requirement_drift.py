from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


FR_ID_RE = re.compile(r"\bFR-[A-Z0-9][A-Z0-9-]*\b")
PLACEHOLDER_FR_IDS = {"FR-ID", "FR-NN", "FR-XX", "FR-XXX"}
WAIVER_PATH = Path(".helix/requirement-drift-waivers.yaml")
BLOCKING_FINDING_TYPES = {"missing_downstream", "orphan_design", "orphan_code"}
GENERIC_DOWNSTREAM_LABELS = {"code", "doc", "docs", "registry", "registry-only", "design", "test"}


@dataclass(frozen=True)
class Anchor:
    requirement_id: str
    label: str
    path: str
    line: int
    is_definition: bool = False


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _iter_files(root: Path, patterns: Iterable[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            yield path


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _is_placeholder_req_id(req_id: str) -> bool:
    if req_id in PLACEHOLDER_FR_IDS:
        return True
    parts = req_id.split("-")[1:]
    return any(part in {"NN", "XX", "XXX", "ID"} for part in parts)


def _valid_req_ids(line: str) -> list[str]:
    return sorted({req_id for req_id in FR_ID_RE.findall(line) if not _is_placeholder_req_id(req_id)})


def _is_l1_numeric_id(req_id: str) -> bool:
    return bool(re.fullmatch(r"FR-\d+", req_id))


def _is_example_line(line: str) -> bool:
    return "例 `" in line or "example `" in line.lower()


def _split_table_cells(stripped_line: str) -> list[str] | None:
    if not stripped_line.startswith("|") or "|" not in stripped_line[1:]:
        return None
    cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
    if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
        return None
    return cells


def _label_from_table_cells(cells: list[str], req_id: str) -> str:
    for cell in cells:
        if cell and cell != req_id and not FR_ID_RE.fullmatch(cell):
            return cell
    return ""


def _label_from_line(line: str, req_id: str) -> tuple[str, bool, bool]:
    stripped = line.strip()
    cells = _split_table_cells(stripped)
    if cells is not None:
        if len(cells) < 2:
            return "", cells[0] == req_id, True
        is_definition = cells[0] == req_id
        return _label_from_table_cells(cells, req_id), is_definition, False

    heading_match = re.match(r"^#+\s+(" + re.escape(req_id) + r")\b\s*(.*)$", stripped)
    if heading_match:
        return heading_match.group(2).strip(" :-|#[]()")[:120], True, False

    after = stripped.split(req_id, 1)[-1].strip(" :-|#[]()")
    return after[:120], False, False


def _collect_anchors(root: Path, patterns: Iterable[str]) -> tuple[dict[str, list[Anchor]], list[dict[str, Any]]]:
    anchors: dict[str, list[Anchor]] = {}
    parse_warnings: list[dict[str, Any]] = []
    for path in _iter_files(root, patterns):
        relative = path.relative_to(root).as_posix()
        for line_no, line in enumerate(_safe_read(path).splitlines(), start=1):
            if _is_example_line(line):
                continue
            ids = _valid_req_ids(line)
            if not ids:
                continue
            for req_id in ids:
                label, is_definition, malformed = _label_from_line(line, req_id)
                anchors.setdefault(req_id, []).append(Anchor(req_id, label, relative, line_no, is_definition))
                if malformed:
                    parse_warnings.append(
                        {
                            "path": relative,
                            "line": line_no,
                            "requirement_id": req_id,
                            "message": "malformed markdown table row",
                        }
                    )
    return anchors, parse_warnings


def _definition_anchors(anchors: dict[str, list[Anchor]]) -> dict[str, list[Anchor]]:
    return {
        req_id: definitions
        for req_id, items in anchors.items()
        if (definitions := [anchor for anchor in items if anchor.is_definition])
    }


def _collect_parent_child_links(root: Path, patterns: Iterable[str]) -> dict[str, set[str]]:
    links: dict[str, set[str]] = {}
    for path in _iter_files(root, patterns):
        for line in _safe_read(path).splitlines():
            if _is_example_line(line):
                continue
            cells = _split_table_cells(line.strip())
            if not cells or len(cells) < 3:
                continue
            first_ids = _valid_req_ids(cells[0])
            if len(first_ids) != 1:
                continue
            first_id = first_ids[0]
            remaining_ids = _valid_req_ids("|".join(cells[1:]))
            if _is_l1_numeric_id(first_id):
                for child_id in remaining_ids:
                    if child_id != first_id and not _is_l1_numeric_id(child_id):
                        links.setdefault(first_id, set()).add(child_id)
            else:
                for parent_id in remaining_ids:
                    if parent_id != first_id and _is_l1_numeric_id(parent_id):
                        links.setdefault(parent_id, set()).add(first_id)
    return links


def _downstream_ids(req_id: str, child_links: dict[str, set[str]]) -> set[str]:
    return {req_id, *child_links.get(req_id, set())}


def _has_downstream(req_id: str, design: dict[str, list[Anchor]], child_links: dict[str, set[str]]) -> bool:
    return any(candidate in design for candidate in _downstream_ids(req_id, child_links))


def _first_label(anchors: list[Anchor]) -> str:
    for anchor in anchors:
        if anchor.label:
            return anchor.label
    return ""


def _tokenize(label: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9一-龥ぁ-んァ-ン]+", label) if len(token) > 1}


def _semantic_mismatch(upstream_label: str, downstream_label: str) -> bool:
    if not upstream_label or not downstream_label:
        return False
    if downstream_label.strip().lower() in GENERIC_DOWNSTREAM_LABELS:
        return False
    upstream_tokens = _tokenize(upstream_label)
    downstream_tokens = _tokenize(downstream_label)
    if not upstream_tokens or not downstream_tokens:
        return False
    return upstream_tokens.isdisjoint(downstream_tokens)


def _load_valid_waivers(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = root / WAIVER_PATH
    if not path.is_file():
        return [], []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_waivers = payload.get("waivers", []) if isinstance(payload, dict) else []
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if not isinstance(raw_waivers, list):
        return [], [{"path": WAIVER_PATH.as_posix(), "message": "waivers must be a list"}]
    for waiver in raw_waivers:
        if not isinstance(waiver, dict):
            invalid.append({"path": WAIVER_PATH.as_posix(), "message": "waiver must be a mapping"})
            continue
        reason = str(waiver.get("reason") or "").strip()
        owner = str(waiver.get("owner") or "").strip()
        expires = str(waiver.get("expires") or "").strip()
        if reason and owner and expires:
            valid.append(dict(waiver))
        else:
            invalid.append({**waiver, "message": "waiver requires reason, owner, and expires"})
    return valid, invalid


def _finding(finding_type: str, req_id: str, anchors: list[Anchor] | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": finding_type, "requirement_id": req_id}
    if anchors:
        payload["anchors"] = [anchor.__dict__ for anchor in anchors]
    payload.update(extra)
    return payload


def _apply_waivers(
    findings: dict[str, list[dict[str, Any]]],
    valid_waivers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    waived: list[dict[str, Any]] = []
    for waiver in valid_waivers:
        req_id = str(waiver.get("requirement_id") or "").strip()
        finding_type = str(waiver.get("finding_type") or "").strip()
        if not req_id or not finding_type or finding_type not in findings:
            continue
        remaining = []
        for finding in findings[finding_type]:
            if finding.get("requirement_id") == req_id:
                waived.append({**finding, "waiver": waiver})
            else:
                remaining.append(finding)
        findings[finding_type] = remaining
    return waived


def collect_requirement_drift(
    project_root: Path | None = None,
    *,
    focus: str = "L6",
    check_stale: bool = False,
) -> dict[str, Any]:
    root = _project_root(project_root)
    normalized_focus = focus.upper()
    if normalized_focus not in {"L6", "L7"}:
        raise ValueError("focus must be L6 or L7")
    upstream, upstream_warnings = _collect_anchors(
        root,
        (
            "docs/v2/L1-requirements/**/*.md",
            "docs/v2/L3-requirements/**/*.md",
        ),
    )
    upstream_definitions = _definition_anchors(upstream)
    child_links = _collect_parent_child_links(
        root,
        (
            "docs/v2/L3-requirements/**/*.md",
        ),
    )
    design, design_warnings = _collect_anchors(
        root,
        (
            "docs/v2/L4*/**/*.md",
            "docs/v2/L5*/**/*.md",
            "docs/v2/L6*/**/*.md",
        ),
    )
    design_definitions = _definition_anchors(design)
    code: dict[str, list[Anchor]] = {}
    tests: dict[str, list[Anchor]] = {}
    code_warnings: list[dict[str, Any]] = []
    test_warnings: list[dict[str, Any]] = []
    if normalized_focus == "L7":
        code, code_warnings = _collect_anchors(
            root,
            (
                "cli/lib/**/*.py",
                "cli/helix*",
            ),
        )
        tests, test_warnings = _collect_anchors(
            root,
            (
                "cli/lib/tests/**/*.py",
                "cli/tests/**/*",
            ),
        )

    findings: dict[str, list[dict[str, Any]]] = {
        "missing_downstream": [],
        "orphan_design": [],
        "orphan_code": [],
        "semantic_label_mismatch": [],
        "stale_freeze": [],
        "waived_with_reason": [],
    }

    for req_id, anchors in sorted(upstream_definitions.items()):
        if not _has_downstream(req_id, design, child_links):
            findings["missing_downstream"].append(_finding("missing_downstream", req_id, anchors))
        upstream_label = _first_label(anchors)
        design_definition_ids = _downstream_ids(req_id, child_links).intersection(design_definitions)
        design_label = _first_label(
            [
                anchor
                for candidate in sorted(design_definition_ids)
                for anchor in design_definitions.get(candidate, [])
            ]
        )
        if design_label and _semantic_mismatch(upstream_label, design_label):
            findings["semantic_label_mismatch"].append(
                _finding(
                    "semantic_label_mismatch",
                    req_id,
                    anchors
                    + [
                        anchor
                        for candidate in sorted(design_definition_ids)
                        for anchor in design_definitions.get(candidate, [])
                    ],
                    upstream_label=upstream_label,
                    downstream_label=design_label,
                )
            )

        stale_definition_ids = _downstream_ids(req_id, child_links).intersection(design_definitions)
        if check_stale and stale_definition_ids:
            newest_upstream = max((root / anchor.path).stat().st_mtime for anchor in anchors if (root / anchor.path).exists())
            newest_design = max(
                (root / anchor.path).stat().st_mtime
                for candidate in stale_definition_ids
                for anchor in design_definitions[candidate]
                if (root / anchor.path).exists()
            )
            if newest_upstream > newest_design:
                findings["stale_freeze"].append(
                    _finding(
                        "stale_freeze",
                        req_id,
                        anchors
                        + [
                            anchor
                            for candidate in sorted(stale_definition_ids)
                            for anchor in design_definitions[candidate]
                        ],
                        upstream_mtime=newest_upstream,
                        downstream_mtime=newest_design,
                    )
                )

    for req_id, anchors in sorted(design.items()):
        if req_id not in upstream_definitions and not any(req_id in children for children in child_links.values()):
            findings["orphan_design"].append(_finding("orphan_design", req_id, anchors))

    if normalized_focus == "L7":
        for req_id, anchors in sorted(code.items()):
            if req_id not in upstream and req_id not in design:
                findings["orphan_code"].append(_finding("orphan_code", req_id, anchors))

    valid_waivers, invalid_waivers = _load_valid_waivers(root)
    findings["waived_with_reason"] = _apply_waivers(findings, valid_waivers)

    parse_warnings = upstream_warnings + design_warnings + code_warnings + test_warnings + invalid_waivers
    unwaived_finding_count = sum(
        len(items) for name, items in findings.items() if name != "waived_with_reason"
    )
    blocking_finding_count = sum(
        len(items) for name, items in findings.items() if name in BLOCKING_FINDING_TYPES
    )
    advisory = "no FR requirements found" if not upstream_definitions else ""

    return {
        "scope": (
            "L1_FR -> L3_FR -> L4-L6_design"
            if normalized_focus == "L6"
            else "L1_FR -> L3_FR -> L4-L6_design -> L7_code -> test"
        ),
        "focus": normalized_focus,
        "stale_check_enabled": check_stale,
        "requirement_kind": ["FR"],
        "clean": unwaived_finding_count == 0,
        "blocking_clean": blocking_finding_count == 0,
        "findings": findings,
        "summary": {
            "requirements": len(upstream_definitions),
            "design_links": sum(
                1 for req_id in upstream_definitions if _has_downstream(req_id, design, child_links)
            ),
            "code_links": sum(1 for req_id in upstream if req_id in code),
            "test_links": sum(1 for req_id in upstream if req_id in tests),
            "parent_child_links": sum(len(children) for children in child_links.values()),
            "blocking_findings": blocking_finding_count,
            "advisory_findings": unwaived_finding_count - blocking_finding_count,
        },
        "advisory": advisory,
        "parse_warnings": parse_warnings,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "requirement_drift",
        f"clean: {str(report['clean']).lower()}",
        f"focus: {report['focus']}",
        f"stale_check_enabled: {str(report['stale_check_enabled']).lower()}",
        "summary: "
        + " ".join(f"{key}={value}" for key, value in report["summary"].items()),
    ]
    if report.get("advisory"):
        lines.append(f"advisory: {report['advisory']}")
    for name, items in report["findings"].items():
        lines.append(f"{name}: {len(items)}")
    if report["parse_warnings"]:
        lines.append(f"parse_warnings: {len(report['parse_warnings'])}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect vertical requirement drift from FR to L4-L6 design.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--project-root", type=Path, default=None)
    parser.add_argument("--focus", choices=("L6", "L7"), default="L6", help="downstream focus; L7 also scans code/test")
    parser.add_argument(
        "--check-stale",
        action="store_true",
        help="enable mtime-based stale freeze advisory; disabled by default to avoid dirty worktree noise",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = collect_requirement_drift(args.project_root, focus=args.focus, check_stale=args.check_stale)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
