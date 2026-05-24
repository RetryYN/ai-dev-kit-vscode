#!/usr/bin/env python3
"""Generate HELIX workflow appendix docs and integration_target frontmatter."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
HELIX_PROCESS_DIR = REPO_ROOT / "HELIX-workflows" / "helix-process"

ARCHITECTURE_APPENDIX = "docs/architecture/helix-workflows-appendix.md"
ADR_APPENDIX = "docs/adr/helix-workflows-appendix.md"
RESEARCH_APPENDIX = "docs/research/helix-workflows-appendix.md"
RUNBOOK_APPENDIX = "docs/runbook/helix-workflows-appendix.md"
ROLLBACK_APPENDIX = "docs/rollback/helix-workflows-appendix.md"
POSTMORTEM_APPENDIX = "docs/postmortem/helix-workflows-appendix.md"
SLO_APPENDIX = "docs/slo/helix-workflows-appendix.md"
DESIGN_APPENDIX = "docs/design/helix-workflows-appendix.md"


def _entry(file_name: str, primary_category: str, docs_path: str, appendix_file: str) -> dict[str, str]:
    return {
        "file": file_name,
        "primary_category": primary_category,
        "docs_path": docs_path,
        "appendix_file": appendix_file,
    }


WORKFLOW_ENTRIES: list[dict[str, str]] = [
    _entry("L0-concept.md", "L0-L14 工程", "docs/requirements", DESIGN_APPENDIX),
    _entry("L1-requirements.md", "L0-L14 工程", "docs/requirements", DESIGN_APPENDIX),
    _entry("L2-ui-design.md", "L0-L14 工程", "docs/design", DESIGN_APPENDIX),
    _entry("L3-requirements-definition.md", "L0-L14 工程", "docs/requirements", DESIGN_APPENDIX),
    _entry("L4-basic-design.md", "L0-L14 工程", "docs/design", DESIGN_APPENDIX),
    _entry("L5-detailed-design.md", "L0-L14 工程", "docs/design", DESIGN_APPENDIX),
    _entry("L6-functional-design.md", "L0-L14 工程", "docs/design", DESIGN_APPENDIX),
    _entry("L7-implementation.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L8-integration-test.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L9-system-test.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L10-ux-refinement.md", "L0-L14 工程", "docs/design", DESIGN_APPENDIX),
    _entry("L11-final-review.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L12-deployment.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L13-post-deployment-verification.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("L14-operation-verification.md", "L0-L14 工程", "docs/specs", DESIGN_APPENDIX),
    _entry("discovery-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("scrum-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("reverse-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("incident-workflow.md", "モードワークフロー", "docs/runbook", RUNBOOK_APPENDIX),
    _entry("add-feature-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("refactor-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("retrofit-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("research-workflow.md", "モードワークフロー", "docs/design", DESIGN_APPENDIX),
    _entry("recovery-workflow.md", "モードワークフロー", "docs/runbook", RUNBOOK_APPENDIX),
    _entry("screen-design-workflow.md", "工程専門", "docs/design", DESIGN_APPENDIX),
    _entry("frontend-design-workflow.md", "工程専門", "docs/design", DESIGN_APPENDIX),
    _entry("automation-gate-map.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("ci-pr-workflow.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("continuous-run-context-management.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("db-auto-registration.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("db-integration.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("deviation-plan-map.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("infra-readiness.md", "管理・自動化基盤", "docs/architecture", SLO_APPENDIX),
    _entry("observability-metrics.md", "管理・自動化基盤", "docs/architecture", SLO_APPENDIX),
    _entry("test-perspective-gate.md", "管理・自動化基盤", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("detection-routing.md", "検出・学習・注入", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("learning-engine.md", "検出・学習・注入", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("cross-detection.md", "検出・学習・注入", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("layer-context-injection.md", "検出・学習・注入", "docs/architecture", ARCHITECTURE_APPENDIX),
    _entry("asset-mapping.md", "ADR・research 関連", "docs/architecture", RESEARCH_APPENDIX),
    _entry("cross-cutting-mechanisms.md", "ADR・research 関連", "docs/architecture", RESEARCH_APPENDIX),
    _entry("fe-detector-spec.md", "ADR・research 関連", "docs/architecture", RESEARCH_APPENDIX),
    _entry("folder-structure-review.md", "ADR・research 関連", "docs/architecture", ADR_APPENDIX),
    _entry("integration-map.md", "ADR・research 関連", "docs/architecture", ADR_APPENDIX),
    _entry("two-stage-agent-design.md", "ADR・research 関連", "docs/architecture", ADR_APPENDIX),
]

CATEGORY_ROWS: list[dict[str, str | int]] = [
    {"category": "L0-L14 工程", "count": 15, "notes": "L0-concept.md 〜 L14-operation-verification.md"},
    {"category": "モードワークフロー", "count": 9, "notes": "discovery / scrum / reverse / incident / add-feature / refactor / retrofit / research / recovery"},
    {"category": "工程専門", "count": 2, "notes": "screen-design / frontend-design"},
    {"category": "管理・自動化基盤", "count": 9, "notes": "automation / db / CI / observability / readiness"},
    {"category": "検出・学習・注入", "count": 4, "notes": "routing / learning / detection / context injection"},
    {"category": "Recovery/Incident 運用", "count": 2, "notes": "incident-workflow / recovery-workflow"},
    {"category": "ADR・research 関連", "count": 6, "notes": "asset / folder review / integration map / FE detector / W design"},
]

DOMAIN_TARGETS: dict[str, list[str]] = {
    ARCHITECTURE_APPENDIX: [
        "automation-gate-map.md",
        "ci-pr-workflow.md",
        "continuous-run-context-management.md",
        "db-auto-registration.md",
        "db-integration.md",
        "deviation-plan-map.md",
        "infra-readiness.md",
        "observability-metrics.md",
        "test-perspective-gate.md",
        "detection-routing.md",
        "learning-engine.md",
        "cross-detection.md",
        "layer-context-injection.md",
        "asset-mapping.md",
        "cross-cutting-mechanisms.md",
        "fe-detector-spec.md",
        "folder-structure-review.md",
        "integration-map.md",
        "two-stage-agent-design.md",
    ],
    ADR_APPENDIX: [
        "folder-structure-review.md",
        "integration-map.md",
        "two-stage-agent-design.md",
    ],
    RESEARCH_APPENDIX: [
        "asset-mapping.md",
        "cross-cutting-mechanisms.md",
        "fe-detector-spec.md",
    ],
    RUNBOOK_APPENDIX: [
        "incident-workflow.md",
        "recovery-workflow.md",
    ],
    ROLLBACK_APPENDIX: [
        "recovery-workflow.md",
    ],
    POSTMORTEM_APPENDIX: [
        "incident-workflow.md",
    ],
    SLO_APPENDIX: [
        "infra-readiness.md",
        "observability-metrics.md",
    ],
    DESIGN_APPENDIX: [
        "L0-concept.md",
        "L1-requirements.md",
        "L2-ui-design.md",
        "L3-requirements-definition.md",
        "L4-basic-design.md",
        "L5-detailed-design.md",
        "L6-functional-design.md",
        "L7-implementation.md",
        "L8-integration-test.md",
        "L9-system-test.md",
        "L10-ux-refinement.md",
        "L11-final-review.md",
        "L12-deployment.md",
        "L13-post-deployment-verification.md",
        "L14-operation-verification.md",
        "discovery-workflow.md",
        "scrum-workflow.md",
        "reverse-workflow.md",
        "incident-workflow.md",
        "add-feature-workflow.md",
        "refactor-workflow.md",
        "retrofit-workflow.md",
        "research-workflow.md",
        "recovery-workflow.md",
        "screen-design-workflow.md",
        "frontend-design-workflow.md",
    ],
}

DOMAIN_OVERVIEWS = {
    ARCHITECTURE_APPENDIX: "HELIX-workflows の管理・自動化、検出、学習、注入、および横断アーキテクチャ資料の中央 INDEX 兼 appendix。",
    ADR_APPENDIX: "HELIX-workflows のうち ADR 判断や構造方針の根拠となる文書群への導線。",
    RESEARCH_APPENDIX: "HELIX-workflows のうち調査・比較・設計探索の補助資料として参照する文書群への導線。",
    RUNBOOK_APPENDIX: "HELIX-workflows のうち運用時の Incident / Recovery 実践に直結する文書群への導線。",
    ROLLBACK_APPENDIX: "HELIX-workflows のうちロールバック判断と復旧手順の観点で参照する文書への導線。",
    POSTMORTEM_APPENDIX: "HELIX-workflows のうち postmortem や恒久対策整理の観点で参照する文書への導線。",
    SLO_APPENDIX: "HELIX-workflows のうち可観測性、SLO、運用品質の判断に使う文書群への導線。",
    DESIGN_APPENDIX: "HELIX-workflows のうち工程定義、モード、工程専門 workflow を設計導線として束ねる appendix。",
}

DOMAIN_POLICIES = {
    ARCHITECTURE_APPENDIX: "設計判断・コマンド統合・自動化基盤の全体像を確認するときは本 appendix を起点にし、詳細は各 workflow 文書へ降りる。",
    ADR_APPENDIX: "設計変更や統合判断の背景が必要なときに参照し、ここで見つけた文書を ADR や PLAN の根拠としてリンクする。",
    RESEARCH_APPENDIX: "技術調査や構造比較の入口として使い、意思決定前に関連 workflow 文書の前提条件を確認する。",
    RUNBOOK_APPENDIX: "運用対応手順の入口として使い、incident / recovery の実行前提や流れを確認する。",
    ROLLBACK_APPENDIX: "ロールバック判断が必要なときに recovery workflow の該当箇所へ最短で到達する導線として使う。",
    POSTMORTEM_APPENDIX: "障害収束後の振り返りや恒久対策整理で incident workflow の該当箇所を参照する。",
    SLO_APPENDIX: "SLO / readiness / observability を確認するときの起点として使い、運用品質の観測粒度を揃える。",
    DESIGN_APPENDIX: "HELIX の工程・モード・工程専門 workflow を横断参照するときの設計ナビゲーションとして使う。",
}


def _entry_map() -> dict[str, dict[str, str]]:
    return {entry["file"]: entry for entry in WORKFLOW_ENTRIES}


def _validate_configuration() -> None:
    names = [entry["file"] for entry in WORKFLOW_ENTRIES]
    if len(names) != 45:
        raise ValueError(f"expected 45 workflow entries, found {len(names)}")
    if len(set(names)) != len(names):
        raise ValueError("workflow entries contain duplicate file names")
    if "README.md" in names:
        raise ValueError("README.md must stay out of scope")


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("frontmatter closing delimiter not found")
    payload = yaml.safe_load(text[4:end]) or {}
    if not isinstance(payload, dict):
        raise ValueError("frontmatter must be a mapping")
    return payload, text[end + 5 :]


def _render_frontmatter(frontmatter: dict[str, object], body: str) -> str:
    dumped = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    ).rstrip()
    return f"---\n{dumped}\n---\n{body}"


def apply_integration_target(path: Path, docs_path: str, category: str, *, write: bool) -> str:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    new_value = {"docs_path": docs_path, "category": category}
    existing = frontmatter.get("integration_target")
    if existing is None:
        frontmatter["integration_target"] = new_value
        rendered = _render_frontmatter(frontmatter, body)
        if write:
            path.write_text(rendered, encoding="utf-8")
        return "updated"
    if existing == new_value:
        return "skipped"
    raise ValueError(f"{path}: conflicting integration_target={existing!r}")


def _link_for_doc(file_name: str) -> str:
    return f"[{file_name}](../../HELIX-workflows/helix-process/{file_name})"


def _matrix_rows(entries: Iterable[dict[str, str]]) -> list[str]:
    rows = []
    for entry in entries:
        rows.append(
            f"| {entry['file']} | {entry['primary_category']} | {entry['docs_path']} | "
            f"{entry['appendix_file']} | {_link_for_doc(entry['file'])} |"
        )
    return rows


def _domain_rows(entries: Iterable[dict[str, str]]) -> list[str]:
    rows = []
    for entry in entries:
        rows.append(
            f"| {entry['file']} | {entry['primary_category']} | {_link_for_doc(entry['file'])} |"
        )
    return rows


def render_appendix_documents() -> dict[str, str]:
    _validate_configuration()
    entry_map = _entry_map()
    architecture_targets = [entry_map[name] for name in DOMAIN_TARGETS[ARCHITECTURE_APPENDIX]]

    architecture_lines = [
        "# HELIX-workflows Appendix",
        "",
        "## 概要",
        DOMAIN_OVERVIEWS[ARCHITECTURE_APPENDIX],
        "",
        "## 中央 INDEX",
        "HELIX-workflows/helix-process/ の 45 file を docs/ 側の導線へ論理接続する。README.md は navigation 文書のため out_of_scope。",
        "",
        "| file | primary_category | docs_path | appendix_file | link |",
        "|---|---|---|---|---|",
        *_matrix_rows(WORKFLOW_ENTRIES),
        "",
        "## README 取扱い",
        "- `README.md` は navigation 文書として扱い、frontmatter 追加対象外・INDEX table 対象外とする。",
        "",
        "## カテゴリ一覧",
        "| category | count | notes |",
        "|---|---:|---|",
        *[
            f"| {row['category']} | {row['count']} | {row['notes']} |"
            for row in CATEGORY_ROWS
        ],
        "",
        "## 対象 file list",
        "| file | primary_category | link |",
        "|---|---|---|",
        *_domain_rows(architecture_targets),
        "",
        "## 参照方針",
        f"- {DOMAIN_POLICIES[ARCHITECTURE_APPENDIX]}",
        "- 実体ファイルは移動せず、appendix と frontmatter による論理接続のみを行う。",
        "",
    ]

    documents = {
        ARCHITECTURE_APPENDIX: "\n".join(architecture_lines),
    }

    for appendix_path, file_names in DOMAIN_TARGETS.items():
        if appendix_path == ARCHITECTURE_APPENDIX:
            continue
        entries = [entry_map[name] for name in file_names]
        lines = [
            "# HELIX-workflows Appendix",
            "",
            "## 概要",
            DOMAIN_OVERVIEWS[appendix_path],
            "",
            "## 対象 file list",
            "| file | primary_category | link |",
            "|---|---|---|",
            *_domain_rows(entries),
            "",
            "## 参照方針",
            f"- {DOMAIN_POLICIES[appendix_path]}",
            "- 実体ファイルは移動せず、必要な workflow 文書へリンクで到達する。",
            "",
        ]
        documents[appendix_path] = "\n".join(lines)

    return documents


def write_appendix_documents(*, write: bool) -> dict[str, int]:
    documents = render_appendix_documents()
    written = 0
    for relative_path, content in documents.items():
        path = REPO_ROOT / relative_path
        if write:
            path.write_text(content, encoding="utf-8")
        written += 1
    return {"appendix_files": written}


def apply_all(*, write: bool) -> dict[str, int]:
    _validate_configuration()
    updated = 0
    skipped = 0
    for entry in WORKFLOW_ENTRIES:
        result = apply_integration_target(
            HELIX_PROCESS_DIR / entry["file"],
            entry["docs_path"],
            entry["primary_category"],
            write=write,
        )
        if result == "updated":
            updated += 1
        else:
            skipped += 1
    summary = write_appendix_documents(write=write)
    return {
        "frontmatter_updated": updated,
        "frontmatter_skipped": skipped,
        **summary,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write changes to disk")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    results = apply_all(write=args.apply)
    print(f"frontmatter_updated={results['frontmatter_updated']}")
    print(f"frontmatter_skipped={results['frontmatter_skipped']}")
    print(f"appendix_files={results['appendix_files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
