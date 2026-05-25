from __future__ import annotations

import argparse
import re
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

TODO: pair design doc から DoD を引き写す

## §2 テストケース

### TC-001: <初期ケース>

- 入力: TODO
- 期待結果: TODO
- 検証手順: TODO

## §3 トレース

- pair design: {paired_design_doc}
- pair test (本 doc): docs/plans/{pair_layer_dir}/TEST-DESIGN-{pair_layer}-{slug}.md
"""

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
SECTION_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
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


def _inject_extracted_sections(template: str, sections: dict[str, str]) -> str:
    result = template
    acceptance = sections["acceptance"].strip()
    if acceptance:
        acceptance_block = f"引用:\n\n{_as_blockquote(acceptance)}\n\nTODO: pair design doc から DoD を引き写す"
        result = result.replace(
            "TODO: pair design doc から DoD を引き写す",
            acceptance_block,
            1,
        )

    function_spec = sections["function_spec"].strip()
    if function_spec:
        function_block = (
            "### 関連 design sections\n\n"
            f"{_as_blockquote(function_spec)}\n\n"
            "TODO: 上記 function spec を参照して TC-001 を具体化する\n\n"
            "### TC-001: <初期ケース>"
        )
        result = result.replace("### TC-001: <初期ケース>", function_block, 1)
    return result


def _render_skeleton(
    layer: str,
    paired_design_doc: str,
    *,
    title: str | None = None,
    slug: str | None = None,
    extract_sections: bool = False,
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
    if not extract_sections:
        return rendered

    sections = extract_paired_design_sections(paired_design_path)
    return _inject_extracted_sections(rendered, sections)


def _default_output_path(project_root: Path, pair_layer: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return (
        Path(project_root)
        / "docs"
        / "plans"
        / pair_layer
        / f"TEST-DESIGN-{pair_layer}-auto-{timestamp}.md"
    )


def auto_detect_paired_design(layer: str, *, project_root: Path) -> str | None:
    """
    Return the first pair PLAN path relative to project_root, if one exists.
    """
    pair_layer = get_pair(layer)
    if pair_layer is None:
        return None

    root = Path(project_root)
    pair_dir = root / "docs" / "plans" / pair_layer
    matches = sorted(pair_dir.glob(f"{pair_layer}-*plan.md")) if pair_dir.is_dir() else []
    if not matches:
        return None

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
) -> str:
    """
    Returns: テスト設計 doc の skeleton 文字列
    layer: pair の不在 layer (例: L4 design で missing pair L9 なら paired_design_layer=L4, target_layer=L9)
    paired_design_doc: 対応する pair design の path
    title: doc title (default: pair_doc title から推定)
    extract_sections=True: paired design doc の relevant section を template に引用する
    """
    return _render_skeleton(
        layer,
        paired_design_doc,
        title=title,
        extract_sections=extract_sections,
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
    )


def _preview(content: str, *, lines: int = 20) -> str:
    return "\n".join(content.splitlines()[:lines])


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix-test-design-scaffold")
    parser.add_argument("--layer", required=True)
    parser.add_argument("--paired-design")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--extract-sections", action="store_true")
    parser.add_argument("--title")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    project_root = resolve_project_root()
    paired_design = args.paired_design or auto_detect_paired_design(args.layer, project_root=project_root)

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
