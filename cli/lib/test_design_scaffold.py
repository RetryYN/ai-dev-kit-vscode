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


def _render_skeleton(
    layer: str,
    paired_design_doc: str,
    *,
    title: str | None = None,
    slug: str | None = None,
) -> str:
    pair_layer = get_pair(layer)
    if pair_layer is None:
        raise ValueError(f"layer has no V-model pair: {layer}")

    paired_design_path = Path(paired_design_doc)
    resolved_title = title.strip() if isinstance(title, str) and title.strip() else _infer_title(paired_design_path)
    resolved_slug = slug or _slugify(resolved_title, fallback=paired_design_path.stem)
    return TEMPLATE.format(
        pair_layer=pair_layer,
        pair_layer_dir=pair_layer,
        slug=resolved_slug,
        title=_yaml_quote(resolved_title),
        layer=layer,
        paired_design_doc=_yaml_quote(paired_design_doc),
        today=date.today().isoformat(),
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


def _slug_from_output_path(output_path: Path, pair_layer: str) -> str:
    prefix = f"TEST-DESIGN-{pair_layer}-"
    stem = output_path.stem
    if stem.startswith(prefix):
        return stem[len(prefix) :]
    return _slugify(stem, fallback=f"{pair_layer}-draft")


def generate_skeleton(layer: str, paired_design_doc: str, *, title: str | None = None) -> str:
    """
    Returns: テスト設計 doc の skeleton 文字列
    layer: pair の不在 layer (例: L4 design で missing pair L9 なら paired_design_layer=L4, target_layer=L9)
    paired_design_doc: 対応する pair design の path
    title: doc title (default: pair_doc title から推定)
    """
    return _render_skeleton(layer, paired_design_doc, title=title)


def _write_scaffold(
    layer: str,
    paired_design_doc: str,
    *,
    project_root: Path,
    dry_run: bool = True,
    output_path: Path | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    pair_layer = get_pair(layer)
    if pair_layer is None:
        raise ValueError(f"layer has no V-model pair: {layer}")

    root = Path(project_root)
    resolved_output_path = Path(output_path) if output_path is not None else _default_output_path(root, pair_layer)
    slug = _slug_from_output_path(resolved_output_path, pair_layer)
    content = _render_skeleton(layer, paired_design_doc, title=title, slug=slug)

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
    )


def _preview(content: str, *, lines: int = 20) -> str:
    return "\n".join(content.splitlines()[:lines])


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix-test-design-scaffold")
    parser.add_argument("--layer", required=True)
    parser.add_argument("--paired-design", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--title")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = _write_scaffold(
            args.layer,
            args.paired_design,
            project_root=resolve_project_root(),
            dry_run=not args.apply,
            title=args.title,
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
