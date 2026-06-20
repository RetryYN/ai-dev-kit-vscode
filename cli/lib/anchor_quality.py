from __future__ import annotations

import ast
import importlib
import os
import re
from pathlib import Path
from typing import Any


_PYTHON_TEST_SUFFIXES = {".py"}
_BATS_TEST_SUFFIXES = {".bats"}
_WORD_RE_TEMPLATE = r"(?<![A-Za-z0-9_]){needle}(?![A-Za-z0-9_])"
_COMMENT_RE = re.compile(r"^\s*#")
_BATS_TEST_RE = re.compile(r'^\s*@test\s+"[^"]+"\s*\{')
_BATS_ASSERT_RE = re.compile(r"\b(assert|refute)_[A-Za-z0-9_]+\b")
_PYTHON_SKIP_MARKERS = {"skip", "skipif", "xfail"}


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _contains_needle(text: str, needle: str) -> bool:
    return re.search(_WORD_RE_TEMPLATE.format(needle=re.escape(needle)), text) is not None


def split_anchor_spec(spec: str) -> tuple[str, str | None]:
    if "::" not in spec:
        return spec, None
    rel_path, needle = spec.split("::", 1)
    normalized_needle = needle.strip() or None
    return rel_path.strip(), normalized_needle


def _leading_comment_start(lines: list[str], start_line: int) -> int:
    index = start_line - 2
    while index >= 0 and _COMMENT_RE.match(lines[index]):
        index -= 1
    return index + 2


def _iter_non_nested_nodes(node: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        nodes.append(child)
        nodes.extend(_iter_non_nested_nodes(child))
    return nodes


def _safe_constant_truth(expr: ast.AST) -> bool | None:
    safe_nodes = (
        ast.Expression,
        ast.Constant,
        ast.Tuple,
        ast.List,
        ast.Set,
        ast.Dict,
        ast.UnaryOp,
        ast.BinOp,
        ast.BoolOp,
        ast.Compare,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.FloorDiv,
        ast.Mod,
        ast.Pow,
        ast.Not,
        ast.USub,
        ast.UAdd,
        ast.And,
        ast.Or,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Is,
        ast.IsNot,
        ast.In,
        ast.NotIn,
    )
    if not all(isinstance(node, safe_nodes) for node in ast.walk(expr)):
        return None
    try:
        value = eval(
            compile(ast.Expression(expr), "<anchor-quality>", "eval"),
            {"__builtins__": {}},
            {},
        )
    except Exception:
        return None
    return bool(value)


def _is_trivial_assert(expr: ast.AST) -> bool:
    truth = _safe_constant_truth(expr)
    return truth is True


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        current: ast.AST | None = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        parts.reverse()
        return ".".join(parts)
    return ""


def _has_skip_or_xfail_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call):
            decorator = decorator.func
        if isinstance(decorator, ast.Attribute) and decorator.attr in _PYTHON_SKIP_MARKERS:
            return True
        if isinstance(decorator, ast.Name) and decorator.id in _PYTHON_SKIP_MARKERS:
            return True
    return False


def _body_without_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.stmt]:
    statements = list(node.body)
    if statements:
        first = statements[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            return statements[1:]
    return statements


def _assess_python_candidate(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    if _has_skip_or_xfail_decorator(node):
        return {"genuine": False, "reason": "python_skip_or_xfail"}

    body = _body_without_docstring(node)
    if body and all(isinstance(statement, ast.Pass) for statement in body):
        return {"genuine": False, "reason": "python_pass_only"}

    non_nested_nodes = _iter_non_nested_nodes(node)
    for child in non_nested_nodes:
        if isinstance(child, (ast.With, ast.AsyncWith)):
            for item in child.items:
                context_expr = item.context_expr
                if isinstance(context_expr, ast.Call) and _call_name(context_expr).endswith("raises"):
                    return {"genuine": True, "reason": "python_pytest_raises_detected"}

    asserts = [child for child in non_nested_nodes if isinstance(child, ast.Assert)]
    if not asserts:
        return {"genuine": False, "reason": "python_no_assertions"}
    if all(_is_trivial_assert(assertion.test) for assertion in asserts):
        return {"genuine": False, "reason": "python_trivial_assert_only"}
    return {"genuine": True, "reason": "python_assertion_detected"}


def _python_candidates(text: str, needle: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines()
    candidates: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        decorator_start = min(
            [item.lineno for item in node.decorator_list] or [node.lineno]
        )
        comment_start = _leading_comment_start(lines, decorator_start)
        end_lineno = getattr(node, "end_lineno", node.lineno)
        block_text = "\n".join(lines[comment_start - 1 : end_lineno])
        if _contains_needle(block_text, needle):
            candidates.append(
                {
                    "start_line": comment_start,
                    "end_line": end_lineno,
                    **_assess_python_candidate(node),
                }
            )
    return sorted(candidates, key=lambda item: int(item["start_line"]))


def _meaningful_bats_lines(body_lines: list[str]) -> list[str]:
    return [
        line.strip()
        for line in body_lines
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _bats_has_assertion(lines: list[str]) -> bool:
    for line in lines:
        if line.startswith("[") or line.startswith("[["):
            return True
        if _BATS_ASSERT_RE.search(line):
            return True
        if "$status" in line or "$output" in line:
            return True
    return False


def _assess_bats_candidate(body_lines: list[str]) -> dict[str, Any]:
    meaningful_lines = _meaningful_bats_lines(body_lines)
    if not meaningful_lines:
        return {"genuine": False, "reason": "bats_empty_body"}
    if all(line.startswith("skip") for line in meaningful_lines):
        return {"genuine": False, "reason": "bats_skip_only"}
    if _bats_has_assertion(meaningful_lines):
        return {"genuine": True, "reason": "bats_assertion_detected"}
    if any(line.startswith("run ") for line in meaningful_lines):
        return {"genuine": False, "reason": "bats_run_without_checks"}
    return {"genuine": False, "reason": "bats_no_assertions"}


def _bats_candidates(text: str, needle: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    candidates: list[dict[str, Any]] = []
    line_count = len(lines)
    index = 0
    while index < line_count:
        line = lines[index]
        if not _BATS_TEST_RE.match(line):
            index += 1
            continue
        start_line = index + 1
        comment_start = _leading_comment_start(lines, start_line)
        end_index = index + 1
        while end_index < line_count and lines[end_index].strip() != "}":
            end_index += 1
        end_line = min(end_index + 1, line_count)
        block_text = "\n".join(lines[comment_start - 1 : end_line])
        if _contains_needle(block_text, needle):
            candidates.append(
                {
                    "start_line": comment_start,
                    "end_line": end_line,
                    **_assess_bats_candidate(lines[index + 1 : end_line - 1]),
                }
            )
        index = end_index + 1
    return candidates


def assess_anchor(test_path: str | Path, needle: str) -> dict[str, Any]:
    path = Path(test_path)
    if not path.is_file():
        return {"genuine": False, "reason": "missing_file"}
    if not needle:
        return {"genuine": False, "reason": "missing_needle"}

    text = path.read_text(encoding="utf-8", errors="ignore")
    if not _contains_needle(text, needle):
        return {"genuine": False, "reason": "missing_needle"}

    if path.suffix in _PYTHON_TEST_SUFFIXES:
        candidates = _python_candidates(text, needle)
        if not candidates:
            return {"genuine": False, "reason": "python_marker_only"}
    elif path.suffix in _BATS_TEST_SUFFIXES:
        candidates = _bats_candidates(text, needle)
        if not candidates:
            return {"genuine": False, "reason": "bats_marker_only"}
    else:
        return {"genuine": False, "reason": "unsupported_test_type"}

    for candidate in candidates:
        if candidate["genuine"]:
            return {"genuine": True, "reason": candidate["reason"]}
    return {"genuine": False, "reason": str(candidates[0]["reason"])}


def evaluate_anchor_specs(project_root: Path, specs: list[str]) -> dict[str, Any]:
    genuine_paths: list[str] = []
    candidate_paths: list[str] = []
    details: list[dict[str, Any]] = []

    for spec in specs:
        rel_path, needle = split_anchor_spec(spec)
        path = project_root / rel_path
        candidate = {
            "spec": spec,
            "path": rel_path,
            "needle": needle,
            "file_exists": path.is_file(),
            "structural_match": False,
            "genuine": False,
            "reason": "",
        }
        if not path.is_file():
            candidate["reason"] = "missing_file"
            details.append(candidate)
            continue

        candidate_paths.append(rel_path)
        if not needle:
            candidate["reason"] = "missing_needle"
            details.append(candidate)
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        if not _contains_needle(text, needle):
            candidate["reason"] = "missing_needle"
            details.append(candidate)
            continue

        candidate["structural_match"] = True
        assessment = assess_anchor(path, needle)
        candidate["genuine"] = bool(assessment["genuine"])
        candidate["reason"] = str(assessment["reason"])
        if assessment["genuine"]:
            genuine_paths.append(rel_path)
        details.append(candidate)

    unique_genuine_paths = [item for item in dict.fromkeys(genuine_paths)]
    unique_candidate_paths = [item for item in dict.fromkeys(candidate_paths)]
    all_structurally_present = bool(specs) and all(
        detail["structural_match"] for detail in details
    )
    all_genuine = bool(specs) and all(detail["genuine"] for detail in details)
    weak_details = [
        detail for detail in details if detail["structural_match"] and not detail["genuine"]
    ]
    return {
        "all_structurally_present": all_structurally_present,
        "all_genuine": all_genuine,
        "genuine_paths": unique_genuine_paths if all_genuine else [],
        "candidate_paths": unique_candidate_paths,
        "details": details,
        "weak_details": weak_details,
    }


def _import_subcheck_module(module_name: str) -> Any:
    package = __package__
    candidates = [module_name]
    if package:
        candidates.insert(0, f"{package}.{module_name}")

    last_error: ImportError | None = None
    for candidate in candidates:
        try:
            return importlib.import_module(candidate)
        except ImportError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def _default_subchecks(root: Path) -> dict[str, dict[str, Any]]:
    g7_subcheck = _import_subcheck_module("g7_subcheck")
    g8_subcheck = _import_subcheck_module("g8_subcheck")
    g9_subcheck = _import_subcheck_module("g9_subcheck")
    g12_subcheck = _import_subcheck_module("g12_subcheck")
    g14_subcheck = _import_subcheck_module("g14_subcheck")

    g7_anchor_path = g7_subcheck._default_anchor_map_path(root)
    return {
        "G7": {
            "anchor_map_ref": g7_anchor_path.relative_to(root).as_posix(),
            "anchors": g7_subcheck.load_anchor_map(g7_anchor_path),
        },
        "G8": {
            "anchor_map_ref": g8_subcheck.ANCHOR_MAP_REF,
            "anchors": g8_subcheck.G8_ANCHOR_MAP,
        },
        "G9": {
            "anchor_map_ref": g9_subcheck.ANCHOR_MAP_REF,
            "anchors": g9_subcheck.G9_ANCHOR_MAP,
        },
        "G12": {
            "anchor_map_ref": g12_subcheck.ANCHOR_MAP_REF,
            "anchors": g12_subcheck.G12_ANCHOR_MAP,
        },
        "G14": {
            "anchor_map_ref": g14_subcheck.ANCHOR_MAP_REF,
            "anchors": g14_subcheck.G14_ANCHOR_MAP,
        },
    }


def collect_anchor_quality(
    project_root: Path | None = None,
    *,
    subchecks: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = _project_root(project_root)
    subcheck_map = subchecks or _default_subchecks(root)

    findings: list[dict[str, Any]] = []
    per_gate: dict[str, dict[str, Any]] = {}
    severity_counts = {"P0": 0, "P1": 0}

    for gate, config in subcheck_map.items():
        anchors: dict[str, list[str]] = config.get("anchors", {})
        anchor_map_ref = str(config.get("anchor_map_ref", ""))
        weak_ids: list[str] = []
        items: list[dict[str, Any]] = []
        for anchor_id in sorted(anchors):
            evaluation = evaluate_anchor_specs(root, anchors[anchor_id])
            weak_details = evaluation["weak_details"]
            if not weak_details:
                continue
            weak_ids.append(anchor_id)
            severity = "P0" if evaluation["all_structurally_present"] else "P1"
            for detail in weak_details:
                finding = {
                    "gate": gate,
                    "id": anchor_id,
                    "severity": severity,
                    "anchor_map": anchor_map_ref,
                    "spec": detail["spec"],
                    "path": detail["path"],
                    "needle": detail["needle"],
                    "reason": detail["reason"],
                }
                items.append(finding)
                findings.append(finding)
                severity_counts[severity] += 1
        per_gate[gate] = {
            "anchor_map": anchor_map_ref,
            "total_ids": len(anchors),
            "weak_count": len(weak_ids),
            "weak_ids": weak_ids,
            "findings": items,
        }

    return {
        "advisory": True,
        "exit_code": 0,
        "passed": not findings,
        "weak_anchor_count": len(findings),
        "severity_counts": severity_counts,
        "findings": findings,
        "per_gate": per_gate,
    }
