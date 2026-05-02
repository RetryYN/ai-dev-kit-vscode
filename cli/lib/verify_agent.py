#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml_parser
from redaction import redact_value


VERIFY_TOOLS_REL_PATH = ".helix/patterns/verify-tools.yaml"
VALID_RUN_TYPES = ("harvest", "design", "cross-check")
VALID_DRIFT_TYPES = ("spec-only", "impl-only", "contract-only", "behavior-only")
VALID_DRIFT_SEVERITIES = ("P0", "P1", "P2", "P3", "unclassified")
FAIL_CLOSE_SEVERITIES = {"P0", "P1", "unclassified"}
HARVEST_REQUIRED_FIELDS = (
    "tool_id",
    "source",
    "official_source",
    "license",
    "last_release_or_activity",
    "maintenance_signal",
    "security_notes",
    "adoption_status",
    "evidence_path",
)
KEYWORD_PATTERN = re.compile(r"(検証|テスト|verify|verification|test|validation)", re.IGNORECASE)
PLAN_ID_PATTERN = re.compile(r"PLAN-\d{3}")

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "unit-test": ("unit", "単体", "pytest", "vitest", "bats", "関数", "バリデーション"),
    "integration": ("integration", "結合", "統合", "service", "db", "データベース"),
    "e2e": ("e2e", "end-to-end", "ユーザー", "画面遷移", "playwright"),
    "lint": ("lint", "静的解析", "ruff", "eslint"),
    "format": ("format", "formatter", "整形"),
    "security": ("security", "脆弱", "owasp", "cve", "ghsa", "secret", "認証", "認可"),
    "dependency": ("dependency", "依存", "license", "ライセンス", "dependabot"),
    "perf": ("perf", "performance", "性能", "p95", "p99", "latency", "slo"),
    "contract": ("contract", "契約", "d-contract", "drift", "schema", "api"),
    "golden": ("golden", "snapshot", "回帰"),
    "fuzz": ("fuzz", "property", "境界値"),
}


class VerifyAgentError(Exception):
    pass


def _project_root(project_root: Path | str | None = None) -> Path:
    return Path(project_root or os.environ.get("HELIX_PROJECT_ROOT") or os.getcwd()).resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _extract_plan_id(text: str, path: Path | None = None) -> str:
    haystack = f"{path or ''}\n{text}"
    match = PLAN_ID_PATTERN.search(haystack)
    return match.group(0) if match else "PLAN-UNKNOWN"


def resolve_plan_path(value: str, project_root: Path | str | None = None) -> Path:
    root = _project_root(project_root)
    raw = Path(value)
    candidates: list[Path] = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.append(root / raw)
        if PLAN_ID_PATTERN.fullmatch(value):
            candidates.extend(sorted((root / "docs" / "plans").glob(f"{value}*.md")))
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise VerifyAgentError(f"plan file not found: {value}")


def resolve_existing_file(value: str, label: str, project_root: Path | str | None = None) -> Path:
    root = _project_root(project_root)
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise VerifyAgentError(f"{label} not found: {value}")
    return path.resolve()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VerifyAgentError(f"failed to read {path}: {exc}") from exc


def extract_verification_requirements(plan_text: str) -> list[dict[str, Any]]:
    lines = plan_text.splitlines()
    requirements: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        if not KEYWORD_PATTERN.search(line):
            continue
        text = line.strip()
        if not text:
            continue
        context = "\n".join(lines[max(0, index - 2) : min(len(lines), index + 1)])
        requirements.append(
            {
                "line": index,
                "text": text,
                "categories": sorted(_categories_for_text(context)),
            }
        )
    return requirements


def _categories_for_text(text: str) -> set[str]:
    lower = text.lower()
    categories = {
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(keyword.lower() in lower for keyword in keywords)
    }
    if not categories and KEYWORD_PATTERN.search(text):
        categories.add("unit-test")
    return categories


def _load_verify_tools(path: Path) -> list[dict[str, Any]]:
    data = yaml_parser.parse_yaml(_read_text(path))
    tools = data.get("tools")
    if not isinstance(tools, list):
        raise VerifyAgentError(f"invalid verify-tools.yaml: tools must be a list ({path})")
    normalized = []
    for item in tools:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def _evidence_path(plan_id: str, tool_id: str) -> str:
    plan_slug = plan_id.lower()
    tool_slug = re.sub(r"[^a-z0-9-]+", "-", str(tool_id).lower()).strip("-") or "candidate"
    return f".helix/research/{plan_slug}/verification.md#{tool_slug}"


def _candidate_from_tool(tool: dict[str, Any], source: str, plan_id: str) -> dict[str, Any]:
    candidate = {
        "tool_id": str(tool.get("id") or "unknown-tool"),
        "source": source,
        "official_source": str(tool.get("official_source") or ""),
        "license": str(tool.get("license") or "unknown"),
        "last_release_or_activity": str(tool.get("last_release_or_activity") or "unknown"),
        "maintenance_signal": str(tool.get("maintenance_signal") or "stale"),
        "security_notes": tool.get("security_notes") if isinstance(tool.get("security_notes"), list) else [],
        "adoption_status": str(tool.get("adoption_status") or "candidate_only"),
        "evidence_path": _evidence_path(plan_id, str(tool.get("id") or "unknown-tool")),
    }
    for optional in ("category", "languages", "helix_alignment"):
        if optional in tool:
            candidate[optional] = tool[optional]
    return _ensure_harvest_candidate(candidate)


def _ensure_harvest_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    item = dict(candidate)
    for field in HARVEST_REQUIRED_FIELDS:
        if field == "security_notes":
            if not isinstance(item.get(field), list):
                item[field] = []
            continue
        item[field] = str(item.get(field) or ("unknown" if field in {"license", "last_release_or_activity"} else ""))
    item["adoption_status"] = "candidate_only" if item["source"] in ("fallback", "llm-suggest") else item["adoption_status"]
    return item


def _fallback_candidate(plan_id: str, reason: str) -> dict[str, Any]:
    return _ensure_harvest_candidate(
        {
            "tool_id": "fallback-verification-candidate",
            "source": "fallback",
            "official_source": "unknown",
            "license": "unknown",
            "last_release_or_activity": "unknown",
            "maintenance_signal": "stale",
            "security_notes": [],
            "adoption_status": "candidate_only",
            "evidence_path": _evidence_path(plan_id, "fallback-verification-candidate"),
            "fallback_reason": reason,
        }
    )


def invoke_codex(role: str, thinking: str, task: str, *, helix_codex: str | None = None) -> str:
    cmd = [helix_codex or os.environ.get("HELIX_CODEX") or "helix-codex", "--role", role, "--thinking", thinking, "--task", task]
    completed = subprocess.run(cmd, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise VerifyAgentError(f"helix-codex failed (exit={completed.returncode}): {detail}")
    return completed.stdout


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise VerifyAgentError("codex output is empty")
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise VerifyAgentError("codex output does not contain JSON") from None
        data = json.loads(stripped[start : end + 1])
    if not isinstance(data, dict):
        raise VerifyAgentError("codex output JSON must be an object")
    return data


def _llm_prompt(plan_id: str, requirements: list[dict[str, Any]]) -> str:
    return (
        "PLAN の検証要件から追加検証ツール候補を JSON だけで返してください。\n"
        "schema: {\"candidates\":[{\"tool_id\":\"...\",\"official_source\":\"...\",\"license\":\"...\","
        "\"last_release_or_activity\":\"YYYY-MM-DD|unknown\",\"maintenance_signal\":\"active|maintenance|stale|deprecated\","
        "\"security_notes\":[]}]}\n"
        f"plan_id: {plan_id}\nrequirements:\n{_json_dump({'requirements': requirements})}"
    )


def _llm_candidates(
    plan_id: str,
    requirements: list[dict[str, Any]],
    codex_runner: Callable[..., str] | None,
) -> list[dict[str, Any]]:
    runner = codex_runner or invoke_codex
    output = runner("research", "low", _llm_prompt(plan_id, requirements))
    data = _extract_json_object(output)
    raw_candidates = data.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return []
    candidates: list[dict[str, Any]] = []
    for raw in raw_candidates:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        item.setdefault("tool_id", item.get("id") or "llm-suggest-candidate")
        item["source"] = "llm-suggest"
        item["adoption_status"] = "candidate_only"
        item.setdefault("evidence_path", _evidence_path(plan_id, str(item["tool_id"])))
        candidates.append(_ensure_harvest_candidate(item))
    return candidates


def harvest(
    plan: str,
    *,
    llm_suggest: bool = False,
    save: bool = False,
    project_root: Path | str | None = None,
    verify_tools_path: Path | str | None = None,
    codex_runner: Callable[..., str] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    plan_path = resolve_plan_path(plan, root)
    plan_text = _read_text(plan_path)
    plan_id = _extract_plan_id(plan_text, plan_path)
    requirements = extract_verification_requirements(plan_text)
    categories = sorted({category for req in requirements for category in req.get("categories", [])})
    tools_path = Path(verify_tools_path) if verify_tools_path else root / VERIFY_TOOLS_REL_PATH
    source_value = VERIFY_TOOLS_REL_PATH
    candidates: list[dict[str, Any]] = []
    fallback_reason = ""

    if tools_path.is_file():
        tools = _load_verify_tools(tools_path)
        matched = [tool for tool in tools if not categories or str(tool.get("category") or "") in categories]
        candidates.extend(_candidate_from_tool(tool, source_value, plan_id) for tool in matched)
        if not candidates:
            fallback_reason = "no matching tool in verify-tools.yaml"
    else:
        fallback_reason = "verify-tools.yaml not yet provisioned"

    if fallback_reason:
        candidates.append(_fallback_candidate(plan_id, fallback_reason))

    if llm_suggest:
        candidates.extend(_llm_candidates(plan_id, requirements, codex_runner))

    result = {
        "subcommand": "harvest",
        "plan_id": plan_id,
        "plan_path": _rel(plan_path, root),
        "requirements": requirements,
        "matched_categories": categories,
        "candidates": candidates,
        "save": save_to_db("harvest", {"plan_id": plan_id, "plan_path": _rel(plan_path, root)}, result_summary(candidates), save),
    }
    return result


def _design_prompt(contract_path: Path, contract_text: str) -> str:
    return (
        "D-CONTRACT / D-API / D-DB から検証方法設計を JSON だけで返してください。\n"
        "schema: {\"pyramid_targets\":{\"unit\":60,\"integration\":30,\"e2e\":10},"
        "\"boundaries\":[\"...\"],\"metrics_minimum\":[\"...\"]}\n"
        "metrics_minimum は p95/p99 / エラーレート / 回帰再現率 / 契約 drift 率のうち最低 1 つ必須。\n"
        f"contract_path: {contract_path}\n\n{contract_text}"
    )


def _normalize_design(data: dict[str, Any]) -> dict[str, Any]:
    targets = data.get("pyramid_targets")
    if not isinstance(targets, dict):
        targets = {}
    normalized_targets = {
        "unit": int(targets.get("unit", 60) or 60),
        "integration": int(targets.get("integration", 30) or 30),
        "e2e": int(targets.get("e2e", 10) or 10),
    }
    boundaries = data.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        boundaries = [
            "Unit: 純粋関数・バリデーション・変換・エッジケース",
            "Integration: サービス間契約・DB 参照・認可境界",
            "E2E: 主要ユーザートリガー + API 成功/失敗分岐",
        ]
    metrics = data.get("metrics_minimum")
    if not isinstance(metrics, list) or not metrics:
        metrics = ["契約 drift 率 <= 0 for P0/P1"]
    return {
        "pyramid_targets": normalized_targets,
        "boundaries": [str(item) for item in boundaries],
        "metrics_minimum": [str(item) for item in metrics],
    }


def design(
    contract: str,
    *,
    save: bool = False,
    project_root: Path | str | None = None,
    dry_run: bool = False,
    codex_runner: Callable[..., str] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    contract_path = resolve_existing_file(contract, "contract", root)
    contract_text = _read_text(contract_path)
    if dry_run:
        design_result = _normalize_design({})
        source = "dry-run"
    else:
        runner = codex_runner or invoke_codex
        data = _extract_json_object(runner("tl", "medium", _design_prompt(contract_path, contract_text)))
        design_result = _normalize_design(data)
        source = "helix-codex"
    return {
        "subcommand": "design",
        "contract_path": _rel(contract_path, root),
        "source": source,
        **design_result,
        "save": save_to_db("design", {"contract_path": _rel(contract_path, root)}, result_summary(design_result), save),
    }


def _cross_check_prompt(impl_path: Path, impl_text: str, spec_path: Path, spec_text: str) -> str:
    return (
        "以下 2 つの PLAN を比較し drift を検出してください。JSON だけで返してください。\n"
        "schema: {\"drifts\":[{\"drift_type\":\"spec-only|impl-only|contract-only|behavior-only\","
        "\"drift_severity\":\"P0|P1|P2|P3|unclassified\",\"title\":\"...\",\"body\":\"...\"}]}\n"
        "severity 判定不能時は drift_severity=unclassified と requires_pm_triage=true を必ず付与。\n\n"
        f"impl_path: {impl_path}\n{impl_text}\n\n---SPEC---\n"
        f"spec_path: {spec_path}\n{spec_text}"
    )


def severity_route(severity: str) -> str:
    routes = {
        "P0": "stop, incident 起票",
        "P1": "G2/G3 fail-close, scrum (Unit/Sprint) 起票",
        "P2": "次工程開始前に解消 or readiness defer",
        "P3": "任意 carry, deferred 台帳記録",
        "unclassified": "PM/TL 再判定必須 (fail-close)",
    }
    if severity not in routes:
        raise ValueError(f"invalid severity: {severity}")
    return routes[severity]


def _normalize_drift(raw: dict[str, Any], index: int) -> dict[str, Any]:
    severity = str(raw.get("drift_severity") or raw.get("severity") or "unclassified")
    if severity not in VALID_DRIFT_SEVERITIES:
        severity = "unclassified"
    drift_type = str(raw.get("drift_type") or "behavior-only")
    if drift_type not in VALID_DRIFT_TYPES:
        drift_type = "behavior-only"
    item = {
        "id": str(raw.get("id") or f"DRIFT-{index:03d}"),
        "drift_type": drift_type,
        "drift_severity": severity,
        "title": str(raw.get("title") or "drift"),
        "body": redact_value(str(raw.get("body") or raw.get("description") or ""), key_hint="body", tuple_as_list=True),
        "next_action": severity_route(severity),
    }
    if severity == "unclassified":
        item["requires_pm_triage"] = True
    elif "requires_pm_triage" in raw:
        item["requires_pm_triage"] = bool(raw.get("requires_pm_triage"))
    return item


def _normalize_cross_check(data: dict[str, Any]) -> dict[str, Any]:
    raw_drifts = data.get("drifts", [])
    if not isinstance(raw_drifts, list):
        raw_drifts = []
    drifts = [_normalize_drift(item, index) for index, item in enumerate(raw_drifts, start=1) if isinstance(item, dict)]
    severity_summary = {severity: 0 for severity in VALID_DRIFT_SEVERITIES}
    for drift in drifts:
        severity_summary[drift["drift_severity"]] += 1
    fail_close = any(drift["drift_severity"] in FAIL_CLOSE_SEVERITIES for drift in drifts)
    return {"drifts": drifts, "drift_severity_summary": severity_summary, "fail_close": fail_close}


def cross_check(
    impl: str,
    spec: str,
    *,
    save: bool = False,
    project_root: Path | str | None = None,
    dry_run: bool = False,
    codex_runner: Callable[..., str] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    impl_path = resolve_plan_path(impl, root)
    spec_path = resolve_plan_path(spec, root)
    impl_text = _read_text(impl_path)
    spec_text = _read_text(spec_path)
    if dry_run or _sha256(impl_text) == _sha256(spec_text):
        normalized = _normalize_cross_check({"drifts": []})
        source = "dry-run" if dry_run else "local-identical-plan"
    else:
        runner = codex_runner or invoke_codex
        data = _extract_json_object(runner("tl", "high", _cross_check_prompt(impl_path, impl_text, spec_path, spec_text)))
        normalized = _normalize_cross_check(data)
        source = "helix-codex"
    inputs = {"impl": _rel(impl_path, root), "spec": _rel(spec_path, root)}
    return {
        "subcommand": "cross-check",
        "inputs": inputs,
        "source": source,
        **normalized,
        "save": save_to_db("cross-check", inputs, result_summary(normalized), save),
    }


def result_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return {"count": len(value)}
    if isinstance(value, dict):
        return {key: value.get(key) for key in ("fail_close", "drift_severity_summary", "pyramid_targets") if key in value}
    return {}


def save_to_db(subcommand: str, inputs: dict[str, Any], output_summary: dict[str, Any], save: bool) -> dict[str, Any]:
    inputs_hash = _sha256(json.dumps(inputs, ensure_ascii=False, sort_keys=True))
    return {
        "requested": bool(save),
        "persisted": False,
        "reason": "helix.db persistence is deferred to schema v13; raw output is not stored",
        "subcommand": subcommand,
        "inputs_hash": inputs_hash,
        "output_summary": output_summary,
    }


def list_runs(run_type: str | None = None) -> dict[str, Any]:
    if run_type is not None and run_type not in VALID_RUN_TYPES:
        raise VerifyAgentError(f"invalid type: {run_type}")
    return {
        "runs": [],
        "type": run_type,
        "persistence": "helix.db persistence is planned for schema v13; current implementation is JSON/no-op only",
    }


def show_run(run_id: str) -> dict[str, Any]:
    raise VerifyAgentError(f"run not found: {run_id} (helix.db persistence is planned for schema v13)")


def _print_harvest_table(candidates: list[dict[str, Any]]) -> None:
    if not candidates:
        print("(empty)")
        return
    print(f"{'Tool':<34} {'Source':<34} {'Status':<16} License")
    print(f"{'----':<34} {'------':<34} {'------':<16} -------")
    for item in candidates:
        print(f"{item['tool_id']:<34} {item['source']:<34} {item['adoption_status']:<16} {item['license']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HELIX verification agent: harvest tools, design verification methods, and cross-check PLAN drift."
    )
    parser.add_argument("--project-root", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    harvest_parser = subparsers.add_parser("harvest", help="collect verification tool candidates from PLAN requirements")
    harvest_parser.add_argument("--plan", required=True)
    harvest_parser.add_argument("--llm-suggest", action="store_true")
    harvest_parser.add_argument("--save", action="store_true")
    harvest_parser.add_argument("--json", action="store_true")

    design_parser = subparsers.add_parser("design", help="design test pyramid, boundaries, and minimum metrics from D-*")
    design_parser.add_argument("--contract", required=True)
    design_parser.add_argument("--save", action="store_true")
    design_parser.add_argument("--json", action="store_true")
    design_parser.add_argument("--dry-run", action="store_true")

    cross_parser = subparsers.add_parser("cross-check", help="detect drift between implementation PLAN and spec PLAN")
    cross_parser.add_argument("--impl", required=True)
    cross_parser.add_argument("--spec", required=True)
    cross_parser.add_argument("--save", action="store_true")
    cross_parser.add_argument("--json", action="store_true")
    cross_parser.add_argument("--dry-run", action="store_true")

    list_parser = subparsers.add_parser("list", help="list saved verify-agent runs")
    list_parser.add_argument("--type", choices=VALID_RUN_TYPES)
    list_parser.add_argument("--json", action="store_true")

    show_parser = subparsers.add_parser("show", help="show a saved verify-agent run")
    show_parser.add_argument("run_id")

    args = parser.parse_args(argv)
    try:
        if args.command == "harvest":
            result = harvest(
                args.plan,
                llm_suggest=args.llm_suggest,
                save=args.save,
                project_root=args.project_root,
            )
            if args.json:
                print(_json_dump(result))
            else:
                print(f"plan: {result['plan_id']} ({result['plan_path']})")
                print(f"requirements: {len(result['requirements'])}")
                _print_harvest_table(result["candidates"])
            return 0
        if args.command == "design":
            result = design(args.contract, save=args.save, project_root=args.project_root, dry_run=args.dry_run)
            if args.json:
                print(_json_dump(result))
            else:
                print(f"contract: {result['contract_path']}")
                print(f"pyramid_targets: {result['pyramid_targets']}")
                print("metrics_minimum:")
                for metric in result["metrics_minimum"]:
                    print(f"  - {metric}")
            return 0
        if args.command == "cross-check":
            result = cross_check(
                args.impl,
                args.spec,
                save=args.save,
                project_root=args.project_root,
                dry_run=args.dry_run,
            )
            if args.json:
                print(_json_dump(result))
            else:
                print(f"drifts: {len(result['drifts'])}")
                print(f"fail_close: {str(result['fail_close']).lower()}")
                for drift in result["drifts"]:
                    print(f"  {drift['id']} {drift['drift_type']} {drift['drift_severity']}: {drift['title']}")
            return 1 if result["fail_close"] else 0
        if args.command == "list":
            result = list_runs(args.type)
            if args.json:
                print(_json_dump(result))
            else:
                print("(empty)")
                print(result["persistence"])
            return 0
        if args.command == "show":
            result = show_run(args.run_id)
            print(_json_dump(result))
            return 0
    except (VerifyAgentError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
