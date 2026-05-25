from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from .paths import project_root as resolve_project_root
from .vmodel_pair_freeze import get_pair


TEMPLATE = """---
test_design_id: TEST-DESIGN-{pair_layer}-{slug}
title: '{title}'
target_layer: '{pair_layer}'
paired_design_layer: '{layer}'
paired_design_doc: '{paired_design_doc}'
status: draft
created: '{today}'
---

# テスト設計 — {pair_layer}: {title}

## §0 対応設計 (V-model pair freeze)

- 対象設計: [{layer}] {paired_design_doc}
- ペア凍結: V-model {layer}↔{pair_layer}

## §1 受入条件 (DoD)

__ACCEPTANCE_BODY__

## §2 テストケース

__TEST_CASES_BODY__

## §3 トレース

- pair design: {paired_design_doc}
- pair test (本 doc): docs/plans/{pair_layer_dir}/TEST-DESIGN-{pair_layer}-{slug}.md
"""

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
SECTION_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
PYTHON_DEF_RE = re.compile(r"^def ([a-z_]+)\(")
BASH_FUNCTION_RE = re.compile(r"^([a-z_]+)\(\) \{")
INLINE_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(\/[^\s\)]+)")
TABLE_ENDPOINT_RE = re.compile(r"\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*(\/[^\s\|]+)")
ACCEPTANCE_KEYWORDS = ("受入条件", "受入要件", "DoD")
FUNCTION_SPEC_KEYWORDS = ("機能設計", "関数仕様")


def _yaml_quote(value: str) -> str:
    return value.replace("'", "''")


def _infer_title(paired_design_path: Path) -> str:
    if paired_design_path.exists():
        text = paired_design_path.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        if match:
            payload = yaml.safe_load(match.group(1)) or {}
            if isinstance(payload, dict):
                raw_title = payload.get("title")
                if isinstance(raw_title, str) and raw_title.strip():
                    return raw_title.strip()
        for line in text.splitlines():
            if line.startswith("# "):
                heading = line[2:].strip()
                if heading:
                    return heading

    stem = paired_design_path.stem
    stem = re.sub(r"^L\d+(?:\.\d+)?-", "", stem)
    stem = re.sub(r"plan$", "", stem, flags=re.IGNORECASE).strip("-_ ")
    title = stem.replace("-", " ").replace("_", " ").strip()
    return title or "Untitled Test Design"


def _slugify(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if slug:
        return slug
    fallback_slug = re.sub(r"[^a-z0-9]+", "-", fallback.lower()).strip("-")
    return fallback_slug or "draft"


def _normalize_heading(heading: str) -> str:
    return re.sub(r"\s+", "", heading)


def _extract_section(text: str, *, keywords: tuple[str, ...]) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = SECTION_HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        heading = _normalize_heading(match.group(2))
        if not any(keyword in heading for keyword in keywords):
            continue

        body_lines: list[str] = []
        for next_line in lines[index + 1 :]:
            next_match = SECTION_HEADING_RE.match(next_line)
            if next_match and len(next_match.group(1)) <= level:
                break
            body_lines.append(next_line)
        return "\n".join(body_lines).strip()
    return ""


def _as_blockquote(text: str) -> str:
    return "\n".join("> " if line == "" else f"> {line}" for line in text.splitlines())


def _default_acceptance_body() -> str:
    return "TODO: pair design doc から DoD を引き写す"


def _default_test_cases_body() -> str:
    return """### TC-001: <初期ケース>

- 入力: TODO
- 期待結果: TODO
- 検証手順: TODO"""


def extract_paired_design_sections(paired_design_path: Path) -> dict[str, str]:
    """
    Returns: {'acceptance': str, 'function_spec': str}
    paired_design_path が存在しない or 該当 section なし → 空 string
    """
    sections = {"acceptance": "", "function_spec": ""}
    if not paired_design_path.exists():
        return sections

    text = paired_design_path.read_text(encoding="utf-8")
    text = FRONTMATTER_RE.sub("", text, count=1)
    sections["acceptance"] = _extract_section(text, keywords=ACCEPTANCE_KEYWORDS)
    sections["function_spec"] = _extract_section(text, keywords=FUNCTION_SPEC_KEYWORDS)
    return sections


def extract_function_signatures(paired_design_path: Path, *, max_count: int = 5) -> list[dict[str, str]]:
    """
    Returns: [{'name': str, 'signature': str, 'context': str}]
    paired_design_path が存在しない → 空 list
    """
    if not paired_design_path.exists() or max_count <= 0:
        return []

    text = paired_design_path.read_text(encoding="utf-8")
    text = FRONTMATTER_RE.sub("", text, count=1)
    lines = text.splitlines()
    signatures: list[dict[str, str]] = []

    for index, line in enumerate(lines):
        match = PYTHON_DEF_RE.match(line) or BASH_FUNCTION_RE.match(line)
        if match is None:
            continue
        context_start = max(0, index - 1)
        context_end = min(len(lines), index + 2)
        signatures.append(
            {
                "name": match.group(1),
                "signature": line.strip(),
                "context": "\n".join(lines[context_start:context_end]).strip(),
            }
        )
        if len(signatures) >= max_count:
            break

    return signatures


def extract_api_endpoints(paired_design_path: Path, *, max_count: int = 5) -> list[dict[str, str]]:
    """
    Returns: [{'method': str, 'path': str, 'context': str}]
    paired_design_path が存在しない → 空 list
    """
    if not paired_design_path.exists() or max_count <= 0:
        return []

    text = paired_design_path.read_text(encoding="utf-8")
    text = FRONTMATTER_RE.sub("", text, count=1)
    lines = text.splitlines()
    endpoints: list[dict[str, str]] = []

    for index, line in enumerate(lines):
        match = TABLE_ENDPOINT_RE.search(line) or INLINE_ENDPOINT_RE.search(line)
        if match is None:
            continue
        context_start = max(0, index - 1)
        context_end = min(len(lines), index + 2)
        endpoints.append(
            {
                "method": match.group(1),
                "path": match.group(2),
                "context": "\n".join(lines[context_start:context_end]).strip(),
            }
        )
        if len(endpoints) >= max_count:
            break

    return endpoints


def _extract_openapi_parameter(parameter: dict[str, Any]) -> dict[str, Any] | None:
    raw_name = parameter.get("name")
    if not isinstance(raw_name, str):
        return None
    name = raw_name.strip()
    if not name:
        return None

    raw_in = parameter.get("in")
    parameter_in = raw_in.strip() if isinstance(raw_in, str) else ""
    parameter_schema = parameter.get("schema")
    parameter_type = "unknown"
    if isinstance(parameter_schema, dict):
        raw_type = parameter_schema.get("type")
        if isinstance(raw_type, str) and raw_type.strip():
            parameter_type = raw_type.strip()

    raw_required = parameter.get("required")
    required = raw_required if isinstance(raw_required, bool) else False
    raw_example = parameter.get("example")
    if raw_example is None and isinstance(parameter_schema, dict):
        raw_example = parameter_schema.get("example")
    example = "" if raw_example is None else str(raw_example)

    return {
        "name": name,
        "in": parameter_in,
        "type": parameter_type,
        "required": required,
        "example": example,
    }


def _format_openapi_parameter(parameter: Any) -> str:
    if isinstance(parameter, str):
        return parameter.strip()
    if not isinstance(parameter, dict):
        return ""

    raw_name = parameter.get("name")
    if not isinstance(raw_name, str):
        return ""
    name = raw_name.strip()
    if not name:
        return ""

    raw_type = parameter.get("type")
    parameter_type = raw_type.strip() if isinstance(raw_type, str) and raw_type.strip() else "unknown"
    requirement = "required" if parameter.get("required") is True else "optional"
    return f"{name} ({parameter_type}, {requirement})"


def extract_openapi_endpoints(spec_path: Path, *, max_count: int = 10) -> list[dict[str, Any]]:
    """
    Returns: [{'method': 'GET', 'path': '/api/users/{id}', 'summary': str,
               'parameters': list[str | dict[str, Any]], 'responses': list[str], 'request_body': str}]
    spec_path 不在 or parse error → 空 list
    """
    if not spec_path.exists() or max_count <= 0:
        return []

    try:
        raw_text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []

    try:
        payload = json.loads(raw_text) if spec_path.suffix.lower() == ".json" else yaml.safe_load(raw_text)
    except (json.JSONDecodeError, yaml.YAMLError):
        return []

    if not isinstance(payload, dict):
        return []

    raw_paths = payload.get("paths")
    if not isinstance(raw_paths, dict):
        return []

    endpoints: list[dict[str, Any]] = []
    for path, methods in raw_paths.items():
        if not isinstance(path, str) or not isinstance(methods, dict):
            continue
        path_level_parameters = methods.get("parameters")
        for method_name, operation in methods.items():
            if not isinstance(method_name, str):
                continue
            normalized_method = method_name.upper()
            if normalized_method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            summary = ""
            parameters: list[dict[str, Any]] = []
            responses: list[str] = []
            request_body = ""
            if isinstance(operation, dict):
                raw_summary = operation.get("summary")
                if isinstance(raw_summary, str):
                    summary = raw_summary.strip()
                raw_parameters = operation.get("parameters")
                combined_parameters = []
                if isinstance(path_level_parameters, list):
                    combined_parameters.extend(path_level_parameters)
                if isinstance(raw_parameters, list):
                    combined_parameters.extend(raw_parameters)
                for parameter in combined_parameters:
                    if not isinstance(parameter, dict):
                        continue
                    extracted = _extract_openapi_parameter(parameter)
                    if extracted is None:
                        continue
                    if any(
                        existing.get("name") == extracted["name"] and existing.get("in") == extracted["in"]
                        for existing in parameters
                    ):
                        continue
                    parameters.append(extracted)

                raw_responses = operation.get("responses")
                if isinstance(raw_responses, dict):
                    for status_code in raw_responses:
                        responses.append(str(status_code))

                raw_request_body = operation.get("requestBody")
                if isinstance(raw_request_body, dict):
                    raw_description = raw_request_body.get("description")
                    if isinstance(raw_description, str) and raw_description.strip():
                        request_body = raw_description.strip()
                    else:
                        request_body = "present"
            endpoints.append(
                {
                    "method": normalized_method,
                    "path": path,
                    "summary": summary,
                    "parameters": parameters,
                    "responses": responses,
                    "request_body": request_body,
                }
            )
            if len(endpoints) >= max_count:
                return endpoints

    return endpoints


def _acceptance_body_from_sections(sections: dict[str, str]) -> str:
    acceptance = sections["acceptance"].strip()
    if not acceptance:
        return _default_acceptance_body()
    return f"引用:\n\n{_as_blockquote(acceptance)}\n\nTODO: pair design doc から DoD を引き写す"


def _test_cases_body(
    sections: dict[str, str],
    *,
    functions: list[dict[str, str]],
    endpoints: list[dict[str, str]],
    openapi_endpoints: list[dict[str, Any]],
) -> str:
    blocks: list[str] = []
    function_spec = sections["function_spec"].strip()
    if function_spec:
        blocks.append(
            "### 関連 design sections\n\n"
            f"{_as_blockquote(function_spec)}\n\n"
            "TODO: 上記 function spec を参照して TC-001 を具体化する\n\n"
        )

    if functions:
        for index, function in enumerate(functions, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"### TC-{index:03d}: `{function['name']}`",
                        "",
                        "引用:",
                        "",
                        f"> function: `{function['name']}`",
                        f"> signature: `{function['signature']}`",
                        "",
                        "- 入力: TODO",
                        "- 期待結果: TODO",
                        "- 検証手順: TODO",
                    ]
                )
            )

    if endpoints:
        for index, endpoint in enumerate(endpoints, start=1):
            blocks.append(
                "\n".join(
                    [
                        f"### TC-API-{index:03d}: `{endpoint['method']} {endpoint['path']}`",
                        "",
                        "引用:",
                        "",
                        f"> endpoint: `{endpoint['method']} {endpoint['path']}`",
                        "",
                        "- 入力: TODO",
                        "- 期待結果: TODO",
                        "- 検証手順: TODO",
                    ]
                )
            )

    if openapi_endpoints:
        for index, endpoint in enumerate(openapi_endpoints, start=1):
            quote_lines = [f"> endpoint: `{endpoint['method']} {endpoint['path']}`"]
            summary = endpoint.get("summary", "").strip()
            if summary:
                quote_lines.append(f"> summary: {summary}")
            parameters = endpoint.get("parameters", [])
            if parameters:
                rendered_parameters = [
                    rendered for rendered in (_format_openapi_parameter(parameter) for parameter in parameters) if rendered
                ]
                if rendered_parameters:
                    quote_lines.append(f"> parameters: {', '.join(rendered_parameters)}")
            responses = endpoint.get("responses", [])
            if responses:
                quote_lines.append(f"> responses: {', '.join(responses)}")
            request_body = endpoint.get("request_body", "").strip()
            if request_body:
                quote_lines.append(f"> request_body: {request_body}")
            blocks.append(
                "\n".join(
                    [
                        f"### TC-OPENAPI-{index:03d}: `{endpoint['method']} {endpoint['path']}`",
                        "",
                        "引用:",
                        "",
                        *quote_lines,
                        "",
                        "- 入力: TODO",
                        "- 期待結果: TODO",
                        "- 検証手順: TODO",
                    ]
                )
            )

    if not functions and not endpoints and not openapi_endpoints:
        blocks.append(_default_test_cases_body())

    return "\n\n".join(blocks)


def _inject_extracted_sections(
    rendered: str,
    *,
    sections: dict[str, str],
    functions: list[dict[str, str]],
    endpoints: list[dict[str, str]],
    openapi_endpoints: list[dict[str, str]],
) -> str:
    return rendered.replace(
        "__ACCEPTANCE_BODY__",
        _acceptance_body_from_sections(sections),
        1,
    ).replace(
        "__TEST_CASES_BODY__",
        _test_cases_body(
            sections,
            functions=functions,
            endpoints=endpoints,
            openapi_endpoints=openapi_endpoints,
        ),
        1,
    )


def _render_skeleton(
    layer: str,
    paired_design_doc: str,
    *,
    title: str | None = None,
    slug: str | None = None,
    extract_sections: bool = False,
    extract_functions: bool = False,
    extract_endpoints: bool = False,
    openapi_spec_path: Path | str | None = None,
) -> str:
    pair_layer = get_pair(layer)
    if pair_layer is None:
        raise ValueError(f"layer has no V-model pair: {layer}")

    paired_design_path = Path(paired_design_doc)
    resolved_title = title.strip() if isinstance(title, str) and title.strip() else _infer_title(paired_design_path)
    resolved_slug = slug or _slugify(resolved_title, fallback=paired_design_path.stem)
    rendered = TEMPLATE.format(
        pair_layer=pair_layer,
        pair_layer_dir=pair_layer,
        slug=resolved_slug,
        title=_yaml_quote(resolved_title),
        layer=layer,
        paired_design_doc=_yaml_quote(paired_design_doc),
        today=date.today().isoformat(),
    )
    if not extract_sections and not extract_functions and not extract_endpoints and openapi_spec_path is None:
        return _inject_extracted_sections(
            rendered,
            sections={"acceptance": "", "function_spec": ""},
            functions=[],
            endpoints=[],
            openapi_endpoints=[],
        )

    sections = (
        extract_paired_design_sections(paired_design_path)
        if extract_sections
        else {"acceptance": "", "function_spec": ""}
    )
    functions = extract_function_signatures(paired_design_path) if extract_functions else []
    endpoints = extract_api_endpoints(paired_design_path) if extract_endpoints else []
    openapi_endpoints = (
        extract_openapi_endpoints(Path(openapi_spec_path))
        if openapi_spec_path is not None
        else []
    )
    return _inject_extracted_sections(
        rendered,
        sections=sections,
        functions=functions,
        endpoints=endpoints,
        openapi_endpoints=openapi_endpoints,
    )


def _default_output_path(project_root: Path, pair_layer: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return (
        Path(project_root)
        / "docs"
        / "plans"
        / pair_layer
        / f"TEST-DESIGN-{pair_layer}-auto-{timestamp}.md"
    )


def _read_plan_metadata(plan_path: Path) -> dict[str, str]:
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    payload = yaml.safe_load(match.group(1)) or {}
    if not isinstance(payload, dict):
        return {}

    metadata: dict[str, str] = {}
    for key in ("status", "kind"):
        raw_value = payload.get(key)
        if not isinstance(raw_value, str):
            continue
        value = raw_value.strip()
        if value:
            metadata[key] = value
    return metadata


def score_paired_design(
    candidate_frontmatter: dict[str, str],
    *,
    prefer_status: str | None = None,
    prefer_kind: str | None = None,
    status_weight: int = 2,
    kind_weight: int = 1,
) -> int:
    """Return a weighted score for a paired design candidate."""
    score = 0
    if prefer_status is not None and candidate_frontmatter.get("status") == prefer_status:
        score += status_weight
    if prefer_kind is not None and candidate_frontmatter.get("kind") == prefer_kind:
        score += kind_weight
    return score


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def auto_detect_paired_design(
    layer: str,
    *,
    project_root: Path,
    prefer_status: str | None = "draft",
    prefer_kind: str | None = None,
    weighted: bool = False,
    status_weight: int = 2,
    kind_weight: int = 1,
) -> str | None:
    """
    Return the preferred pair PLAN path relative to project_root, if one exists.
    """
    pair_layer = get_pair(layer)
    if pair_layer is None:
        return None

    root = Path(project_root)
    pair_dir = root / "docs" / "plans" / pair_layer
    matches = sorted(pair_dir.glob(f"{pair_layer}-*plan.md")) if pair_dir.is_dir() else []
    if not matches:
        return None

    candidates = [(match, _read_plan_metadata(match)) for match in matches]

    if weighted:
        best_match = matches[0]
        best_score = -1
        for match, metadata in candidates:
            score = score_paired_design(
                metadata,
                prefer_status=prefer_status,
                prefer_kind=prefer_kind,
                status_weight=status_weight,
                kind_weight=kind_weight,
            )
            if score > best_score:
                best_match = match
                best_score = score
        return str(best_match.relative_to(root))

    if prefer_status is not None and prefer_kind is not None:
        for match, metadata in candidates:
            if metadata.get("status") == prefer_status and metadata.get("kind") == prefer_kind:
                return str(match.relative_to(root))

    if prefer_status is not None:
        for match, metadata in candidates:
            if metadata.get("status") == prefer_status:
                return str(match.relative_to(root))

    if prefer_kind is not None:
        for match, metadata in candidates:
            if metadata.get("kind") == prefer_kind:
                return str(match.relative_to(root))

    return str(matches[0].relative_to(root))


def _slug_from_output_path(output_path: Path, pair_layer: str) -> str:
    prefix = f"TEST-DESIGN-{pair_layer}-"
    stem = output_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return _slugify(stem, fallback=f"{pair_layer}-draft")


def generate_skeleton(
    layer: str,
    paired_design_doc: str,
    *,
    title: str | None = None,
    extract_sections: bool = False,
    extract_functions: bool = False,
    extract_endpoints: bool = False,
    openapi_spec_path: Path | str | None = None,
) -> str:
    """
    Returns: テスト設計 doc の skeleton 文字列
    layer: pair の不在 layer (例: L4 design で missing pair L9 なら paired_design_layer=L4, target_layer=L9)
    paired_design_doc: 対応する pair design の path
    title: doc title (default: pair_doc title から推定)
    extract_sections=True: paired design doc の relevant section を template に引用する
    extract_functions=True: paired design doc の function 定義ごとに TC 雛形を展開する
    extract_endpoints=True: paired design doc の API endpoint ごとに TC 雛形を展開する
    openapi_spec_path 指定: OpenAPI spec file から endpoint ごとに TC-OPENAPI 雛形を展開する
    """
    return _render_skeleton(
        layer,
        paired_design_doc,
        title=title,
        extract_sections=extract_sections,
        extract_functions=extract_functions,
        extract_endpoints=extract_endpoints,
        openapi_spec_path=openapi_spec_path,
    )


def _write_scaffold(
    layer: str,
    paired_design_doc: str,
    *,
    project_root: Path,
    dry_run: bool = True,
    output_path: Path | None = None,
    title: str | None = None,
    extract_sections: bool = False,
    extract_functions: bool = False,
    extract_endpoints: bool = False,
) -> dict[str, Any]:
    pair_layer = get_pair(layer)
    if pair_layer is None:
        raise ValueError(f"layer has no V-model pair: {layer}")

    root = Path(project_root)
    resolved_output_path = Path(output_path) if output_path is not None else _default_output_path(root, pair_layer)
    slug = _slug_from_output_path(resolved_output_path, pair_layer)
    content = _render_skeleton(
        layer,
        paired_design_doc,
        title=title,
        slug=slug,
        extract_sections=extract_sections,
        extract_functions=extract_functions,
        extract_endpoints=extract_endpoints,
    )

    result = {
        "status": "dry_run" if dry_run else "applied",
        "output_path": str(resolved_output_path),
        "content": content,
        "reason": "dry run" if dry_run else "",
    }
    if dry_run:
        return result

    if resolved_output_path.exists():
        result["status"] = "skipped"
        result["reason"] = "file exists"
        return result

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(content, encoding="utf-8")
    return result


def write_scaffold(
    layer: str,
    paired_design_doc: str,
    *,
    project_root: Path,
    dry_run: bool = True,
    output_path: Path | None = None,
    extract_sections: bool = False,
    extract_functions: bool = False,
    extract_endpoints: bool = False,
) -> dict[str, Any]:
    """
    Returns: {'status': 'dry_run'|'applied'|'skipped', 'output_path': str, 'content': str, 'reason': str}
    dry_run=True: 内容を返すだけ、書き込みなし
    dry_run=False (--apply): output_path に write、既存 path なら status='skipped'
    output_path 未指定なら docs/plans/{pair_layer_dir}/TEST-DESIGN-{pair_layer}-auto-{datetime}.md 自動生成
    """
    return _write_scaffold(
        layer,
        paired_design_doc,
        project_root=project_root,
        dry_run=dry_run,
        output_path=output_path,
        extract_sections=extract_sections,
        extract_functions=extract_functions,
        extract_endpoints=extract_endpoints,
    )


def _preview(content: str, *, lines: int = 20) -> str:
    return "\n".join(content.splitlines()[:lines])


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix-test-design-scaffold")
    parser.add_argument("--layer", required=True)
    parser.add_argument("--paired-design")
    parser.add_argument(
        "--prefer-status",
        choices=("draft", "in_progress", "completed", "none"),
        default="draft",
    )
    parser.add_argument(
        "--prefer-kind",
        choices=("design", "impl", "poc", "none"),
        default="none",
    )
    parser.add_argument("--weighted", action="store_true")
    parser.add_argument("--status-weight", type=_positive_int, default=2)
    parser.add_argument("--kind-weight", type=_positive_int, default=1)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--extract-sections", action="store_true")
    parser.add_argument("--title")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    cli_args = argv if argv is not None else None
    args = parser.parse_args(cli_args)
    raw_args = cli_args if cli_args is not None else sys.argv[1:]
    weights_specified = "--status-weight" in raw_args or "--kind-weight" in raw_args
    if weights_specified and not args.weighted:
        parser.error("--status-weight/--kind-weight require --weighted")
    project_root = resolve_project_root()
    prefer_status = None if args.prefer_status == "none" else args.prefer_status
    prefer_kind = None if args.prefer_kind == "none" else args.prefer_kind
    paired_design = args.paired_design or auto_detect_paired_design(
        args.layer,
        project_root=project_root,
        prefer_status=prefer_status,
        prefer_kind=prefer_kind,
        weighted=args.weighted,
        status_weight=args.status_weight,
        kind_weight=args.kind_weight,
    )

    if paired_design is None:
        print(f"error: paired design could not be auto-detected for layer {args.layer}")
        return 1

    try:
        result = _write_scaffold(
            args.layer,
            paired_design,
            project_root=project_root,
            dry_run=not args.apply,
            title=args.title,
            extract_sections=args.extract_sections,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    print(f"status: {result['status']}")
    print(f"output_path: {result['output_path']}")
    if result.get("reason"):
        print(f"reason: {result['reason']}")
    print("content_preview:")
    print(_preview(result["content"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
