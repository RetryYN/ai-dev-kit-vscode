from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ID_PATTERN = r"(?:FR|NFR|BR|TR|OT|AT|ST|IF)-[A-Z0-9]+(?:-[0-9]+)?"
ID_RE = re.compile(rf"^{ID_PATTERN}$")
ID_SEARCH_RE = re.compile(rf"(?<![A-Z0-9-])({ID_PATTERN})(?![A-Z0-9-])")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
LAYER_RE = re.compile(r"^L[0-9]+$")
PAIR_FIELDS = ("pairs_test_design", "generates", "covers", "parent_design", "pairs_design")
PAIR_LAYERS = {
    "L1-L14": ("L1", "L14"),
    "L3-L12": ("L3", "L12"),
    "L4-L9": ("L4", "L9"),
    "L5-L8": ("L5", "L8"),
    "L6-L7": ("L6", "L7"),
}
REFERENCE_KEYWORDS = ("mapping", "trace", "matrix", "対応", "入出力", "i/o", "input", "output")
TARGET_COLUMN_KEYWORDS = ("対応要件", "対象要件", "要件id", "design_id", "対象 fr", "対象設計")


@dataclass(frozen=True)
class DefinitionEntry:
    doc_path: str
    line_no: int
    entry_id: str
    row_text: str
    kind: str


@dataclass(frozen=True)
class TableRow:
    line_no: int
    cells: tuple[str, ...]


@dataclass(frozen=True)
class TableBlock:
    doc_path: str
    start_line: int
    headers: tuple[str, ...]
    rows: tuple[TableRow, ...]
    heading_path: tuple[str, ...]


@dataclass(frozen=True)
class Document:
    path: Path
    rel_path: str
    process_layer: str | None
    status: str | None
    frontmatter: dict[str, Any]
    heading_entries: list[DefinitionEntry]
    definitions: list[DefinitionEntry]
    tables: list[TableBlock]


def _is_valid_id(value: str) -> bool:
    return bool(ID_RE.fullmatch(value)) and not value.endswith("-ID")


def _normalize_label(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _contains_keyword(value: str, keywords: tuple[str, ...]) -> bool:
    normalized = _normalize_label(value)
    return any(keyword in normalized for keyword in keywords)


def _parse_table_cells(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _is_table_divider(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    cells = _parse_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _primary_id_from_cell(cell: str) -> str | None:
    cleaned = cell.strip().strip("*`_ ")
    match = ID_SEARCH_RE.search(cleaned)
    if not match:
        return None
    entry_id = match.group(1)
    return entry_id if cleaned.startswith(entry_id) else None


def _first_id_in_text(text: str) -> str | None:
    match = ID_SEARCH_RE.search(text)
    if not match:
        return None
    entry_id = match.group(1)
    return entry_id if _is_valid_id(entry_id) else None


def load_frontmatter(path: Path) -> tuple[dict[str, Any], list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, lines

    payload = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    if not isinstance(payload, dict):
        return {}, lines[end_index + 1 :]
    return payload, lines[end_index + 1 :]


def _extract_document_structure(
    doc_path: str,
    body_lines: list[str],
) -> tuple[list[DefinitionEntry], list[TableBlock]]:
    heading_entries: list[DefinitionEntry] = []
    tables: list[TableBlock] = []
    heading_stack: list[str] = []
    index = 0

    while index < len(body_lines):
        line = body_lines[index]
        line_no = index + 1
        heading_match = HEADING_RE.match(line)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            stripped = line.lstrip()
            heading_level = len(stripped) - len(stripped.lstrip("#"))
            heading_stack = heading_stack[: heading_level - 1]
            heading_stack.append(heading_text)

            primary_id = _first_id_in_text(heading_text)
            if primary_id:
                remainder = heading_text.replace(primary_id, "", 1).strip(" -:()[]*`_")
                heading_entries.append(
                    DefinitionEntry(
                        doc_path=doc_path,
                        line_no=line_no,
                        entry_id=primary_id,
                        row_text=remainder,
                        kind="heading",
                    )
                )
            index += 1
            continue

        if (
            line.strip().startswith("|")
            and index + 1 < len(body_lines)
            and _is_table_divider(body_lines[index + 1])
        ):
            headers = _parse_table_cells(line)
            row_index = index + 2
            rows: list[TableRow] = []
            while row_index < len(body_lines) and body_lines[row_index].strip().startswith("|"):
                rows.append(
                    TableRow(
                        line_no=row_index + 1,
                        cells=_parse_table_cells(body_lines[row_index]),
                    )
                )
                row_index += 1
            tables.append(
                TableBlock(
                    doc_path=doc_path,
                    start_line=line_no,
                    headers=headers,
                    rows=tuple(rows),
                    heading_path=tuple(heading_stack),
                )
            )
            index = row_index
            continue

        index += 1

    return heading_entries, tables


def extract_definition_entries(
    doc_path: str,
    body_lines: list[str],
) -> tuple[list[DefinitionEntry], list[DefinitionEntry], list[TableBlock]]:
    heading_entries, tables = _extract_document_structure(doc_path, body_lines)
    definitions = list(heading_entries)
    for table in tables:
        for row in table.rows:
            primary_id = _primary_id_from_cell(row.cells[0]) if row.cells else None
            if primary_id and _is_valid_id(primary_id) and any(cell for cell in row.cells[1:]):
                definitions.append(
                    DefinitionEntry(
                        doc_path=doc_path,
                        line_no=row.line_no,
                        entry_id=primary_id,
                        row_text=" | ".join(row.cells[1:]).strip(),
                        kind="table",
                    )
                )
    return heading_entries, definitions, tables


def _project_root(project_root: Path | None = None) -> Path:
    if project_root is not None:
        return project_root.resolve()
    env_root = os.environ.get("HELIX_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _normalize_doc_path(path: str) -> str | None:
    normalized = path.strip()
    if not normalized.endswith(".md"):
        return None
    normalized = normalized.replace("\\", "/").lstrip("./")
    if normalized.startswith("docs/v2/"):
        return normalized
    return None


def _normalize_pair_value(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        normalized = _normalize_doc_path(value)
        if normalized:
            values.append(normalized)
        return values
    if isinstance(value, list):
        for item in value:
            values.extend(_normalize_pair_value(item))
        return values
    if isinstance(value, dict):
        for key in ("artifact_path", "path", "doc_path"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                normalized = _normalize_doc_path(candidate)
                if normalized:
                    values.append(normalized)
        return values
    return values


def _normalize_id_values(value: Any) -> list[str]:
    if isinstance(value, str):
        primary_id = _primary_id_from_cell(value)
        return [primary_id] if primary_id and _is_valid_id(primary_id) else []
    if isinstance(value, list):
        ids: list[str] = []
        for item in value:
            ids.extend(_normalize_id_values(item))
        return ids
    if isinstance(value, dict):
        ids: list[str] = []
        for key in ("id", "ids"):
            ids.extend(_normalize_id_values(value.get(key)))
        return ids
    return []


def _pair_links(doc: Document) -> list[str]:
    links: list[str] = []
    for field in PAIR_FIELDS:
        links.extend(_normalize_pair_value(doc.frontmatter.get(field)))
    return sorted(set(links))


def _load_documents(project_root: Path) -> list[Document]:
    docs_root = project_root / "docs" / "v2"
    documents: list[Document] = []
    for path in sorted(docs_root.rglob("*.md")):
        rel_path = path.relative_to(project_root).as_posix()
        frontmatter, body_lines = load_frontmatter(path)
        heading_entries, definitions, tables = extract_definition_entries(rel_path, body_lines)
        process_layer = frontmatter.get("process_layer")
        status = frontmatter.get("status")
        documents.append(
            Document(
                path=path,
                rel_path=rel_path,
                process_layer=process_layer if isinstance(process_layer, str) else None,
                status=status if isinstance(status, str) else None,
                frontmatter=frontmatter,
                heading_entries=heading_entries,
                definitions=definitions,
                tables=tables,
            )
        )
    return documents


def _table_is_design_reference(table: TableBlock) -> bool:
    heading_text = " ".join(table.heading_path)
    if _contains_keyword(heading_text, REFERENCE_KEYWORDS):
        return True
    for header in table.headers[1:]:
        if _contains_keyword(header, REFERENCE_KEYWORDS) or _contains_keyword(header, TARGET_COLUMN_KEYWORDS):
            return True
    return False


def _table_is_test_reference(table: TableBlock) -> bool:
    heading_text = " ".join(table.heading_path)
    if _contains_keyword(heading_text, REFERENCE_KEYWORDS):
        return True
    return any(_contains_keyword(header, ("mapping", "trace", "matrix")) for header in table.headers)


def _table_has_target_columns(table: TableBlock) -> bool:
    return any(_contains_keyword(header, TARGET_COLUMN_KEYWORDS) for header in table.headers[1:])


def _scheme_signature(entry_id: str) -> tuple[str, ...]:
    parts = entry_id.split("-")
    signature = [parts[0]]
    for part in parts[1:]:
        signature.append("NUM" if part.isdigit() else "TOKEN")
    return tuple(signature)


def _scheme_weight(entry: DefinitionEntry) -> int:
    return 3 if entry.kind == "heading" else 1


def _filter_entries_by_scheme(entries: list[DefinitionEntry]) -> list[DefinitionEntry]:
    if not entries:
        return []

    total_scores: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    heading_scores: dict[str, Counter[tuple[str, ...]]] = defaultdict(Counter)
    for entry in entries:
        family = entry.entry_id.split("-", 1)[0]
        scheme = _scheme_signature(entry.entry_id)
        total_scores[family][scheme] += _scheme_weight(entry)
        if entry.kind == "heading":
            heading_scores[family][scheme] += _scheme_weight(entry)

    allowed_schemes: dict[str, set[tuple[str, ...]]] = {}
    for family, scores in total_scores.items():
        best_heading = max(heading_scores[family].values(), default=0)
        ranked = []
        for scheme, total_score in scores.items():
            ranked.append((heading_scores[family][scheme], total_score, scheme))
        ranked.sort(reverse=True)
        best_heading_score, best_total_score, _ = ranked[0]
        allowed_schemes[family] = {
            scheme
            for heading_score, total_score, scheme in ranked
            if heading_score == best_heading_score
            and total_score == best_total_score
            and (best_heading_score > 0 or total_score == best_total_score)
        }

    return [
        entry
        for entry in entries
        if _scheme_signature(entry.entry_id) in allowed_schemes[entry.entry_id.split("-", 1)[0]]
    ]


def _collect_design_entries(doc: Document) -> list[DefinitionEntry]:
    candidates = list(doc.heading_entries)
    for table in doc.tables:
        if _table_is_design_reference(table):
            continue
        for row in table.rows:
            primary_id = _primary_id_from_cell(row.cells[0]) if row.cells else None
            if primary_id and _is_valid_id(primary_id) and any(cell for cell in row.cells[1:]):
                candidates.append(
                    DefinitionEntry(
                        doc_path=doc.rel_path,
                        line_no=row.line_no,
                        entry_id=primary_id,
                        row_text=" | ".join(row.cells[1:]).strip(),
                        kind="table",
                    )
                )
    return _filter_entries_by_scheme(candidates)


def _collect_test_definition_entries(doc: Document) -> list[DefinitionEntry]:
    candidates = list(doc.heading_entries)
    for table in doc.tables:
        if _table_is_test_reference(table):
            continue
        for row in table.rows:
            primary_id = _primary_id_from_cell(row.cells[0]) if row.cells else None
            if primary_id and _is_valid_id(primary_id) and any(cell for cell in row.cells[1:]):
                candidates.append(
                    DefinitionEntry(
                        doc_path=doc.rel_path,
                        line_no=row.line_no,
                        entry_id=primary_id,
                        row_text=" | ".join(row.cells[1:]).strip(),
                        kind="table",
                    )
                )
    return _filter_entries_by_scheme(candidates)


def _normalize_layer_names(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if LAYER_RE.fullmatch(value.strip()) else set()
    if isinstance(value, list):
        layers: set[str] = set()
        for item in value:
            layers |= _normalize_layer_names(item)
        return layers
    return set()


def _verification_layers(frontmatter: dict[str, Any]) -> dict[str, set[str]]:
    raw = frontmatter.get("verification_layers")
    mapping: dict[str, set[str]] = defaultdict(set)

    if isinstance(raw, dict):
        if all(isinstance(key, str) and LAYER_RE.fullmatch(key) for key in raw):
            for layer, ids in raw.items():
                for entry_id in _normalize_id_values(ids):
                    mapping[entry_id].add(layer)
            return dict(mapping)
        for entry_id, layers in raw.items():
            if isinstance(entry_id, str):
                mapping[entry_id].update(_normalize_layer_names(layers))
        return dict(mapping)

    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            entry_ids = _normalize_id_values(item.get("id")) + _normalize_id_values(item.get("ids"))
            layers = _normalize_layer_names(item.get("layer")) | _normalize_layer_names(item.get("layers"))
            for entry_id in entry_ids:
                mapping[entry_id].update(layers)
    return dict(mapping)


def _verification_applicable(
    design_entries: list[DefinitionEntry],
    doc_index: dict[str, Document],
    *,
    test_layer: str,
) -> tuple[list[DefinitionEntry], list[dict[str, str]]]:
    filtered: list[DefinitionEntry] = []
    excluded: list[dict[str, str]] = []
    for entry in design_entries:
        doc = doc_index[entry.doc_path]
        layers = _verification_layers(doc.frontmatter).get(entry.entry_id)
        if layers and test_layer not in layers:
            excluded.append(
                {
                    "id": entry.entry_id,
                    "doc": entry.doc_path,
                    "reason": f"verification_layers={','.join(sorted(layers))}",
                }
            )
            continue
        filtered.append(entry)
    return filtered, excluded


def _connected_test_docs(
    design_docs: list[Document],
    test_docs: list[Document],
    doc_index: dict[str, Document],
    *,
    expected_design_layer: str,
    expected_test_layer: str,
) -> set[str]:
    connected: set[str] = set()
    design_paths = {doc.rel_path for doc in design_docs}
    test_paths = {doc.rel_path for doc in test_docs}

    for doc in design_docs:
        for link in _pair_links(doc):
            target = doc_index.get(link)
            if target and target.process_layer == expected_test_layer and target.rel_path in test_paths:
                connected.add(target.rel_path)
    for doc in test_docs:
        for link in _pair_links(doc):
            target = doc_index.get(link)
            if target and target.process_layer == expected_design_layer and target.rel_path in design_paths:
                connected.add(doc.rel_path)
    return connected


def _missing_pair_docs(
    design_docs: list[Document],
    test_docs: list[Document],
    doc_index: dict[str, Document],
    *,
    expected_design_layer: str,
    expected_test_layer: str,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for role, docs, target_layer in (
        ("design", design_docs, expected_test_layer),
        ("test", test_docs, expected_design_layer),
    ):
        for doc in docs:
            links = _pair_links(doc)
            if not links:
                findings.append({"doc": doc.rel_path, "role": role, "reason": "missing_pair_frontmatter"})
                continue
            if not any((target := doc_index.get(link)) and target.process_layer == target_layer for link in links):
                findings.append({"doc": doc.rel_path, "role": role, "reason": "missing_target_pair"})
    return findings


def _wrong_layer_docs(
    design_docs: list[Document],
    test_docs: list[Document],
    doc_index: dict[str, Document],
    *,
    expected_design_layer: str,
    expected_test_layer: str,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for role, docs, target_layer in (
        ("design", design_docs, expected_test_layer),
        ("test", test_docs, expected_design_layer),
    ):
        for doc in docs:
            bad_targets = []
            for link in _pair_links(doc):
                target = doc_index.get(link)
                if target is None:
                    continue
                if target.process_layer != target_layer:
                    bad_targets.append(f"{link}:{target.process_layer or 'unknown'}")
            if bad_targets:
                findings.append(
                    {
                        "doc": doc.rel_path,
                        "role": role,
                        "expected_layer": target_layer,
                        "targets": ", ".join(sorted(bad_targets)),
                    }
                )
    return findings


def _duplicate_details(entries: list[DefinitionEntry]) -> tuple[list[str], list[dict[str, Any]]]:
    grouped: dict[str, list[DefinitionEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.entry_id].append(entry)

    duplicate_ids = sorted(entry_id for entry_id, items in grouped.items() if len(items) > 1)
    details = []
    for entry_id in duplicate_ids:
        for item in grouped[entry_id]:
            details.append({"id": entry_id, "doc": item.doc_path, "line": item.line_no})
    return duplicate_ids, details


def _coverage_sources(doc: Document) -> list[TableBlock]:
    return [
        table
        for table in doc.tables
        if _table_is_test_reference(table) or _table_has_target_columns(table)
    ]


def _collect_test_coverage(
    test_docs: list[Document],
    *,
    design_ids: set[str],
) -> tuple[set[str], dict[str, set[str]], set[str]]:
    test_definition_ids: set[str] = set()
    for doc in test_docs:
        test_definition_ids |= {entry.entry_id for entry in _collect_test_definition_entries(doc)}

    covered_design_ids: set[str] = set()
    mapped_test_ids: dict[str, set[str]] = defaultdict(set)

    for doc in test_docs:
        for table in _coverage_sources(doc):
            for row in table.rows:
                row_ids = {
                    match.group(1)
                    for cell in row.cells
                    for match in ID_SEARCH_RE.finditer(cell)
                    if _is_valid_id(match.group(1))
                }
                design_refs = row_ids & design_ids
                if design_refs:
                    covered_design_ids |= design_refs
                first_id = _primary_id_from_cell(row.cells[0]) if row.cells else None
                if first_id in test_definition_ids and design_refs:
                    mapped_test_ids[first_id].update(design_refs)

    return covered_design_ids, mapped_test_ids, test_definition_ids


def _coverage_summary(
    design_entries: list[DefinitionEntry],
    covered_design_ids: set[str],
    test_definition_ids: set[str],
    mapped_test_ids: dict[str, set[str]],
) -> tuple[list[str], list[str], float, float]:
    design_ids = sorted({entry.entry_id for entry in design_entries})
    uncovered = [design_id for design_id in design_ids if design_id not in covered_design_ids]
    orphan_ids = sorted(test_definition_ids - set(mapped_test_ids))
    coverage_pct = round(((len(design_ids) - len(uncovered)) / len(design_ids)) * 100, 2) if design_ids else 0.0
    balance_ratio = round(len(test_definition_ids) / len(design_ids), 2) if design_ids else 0.0
    return uncovered, orphan_ids, coverage_pct, balance_ratio


def collect_trace_symmetry(project_root: Path | None = None) -> dict[str, Any]:
    """Collect advisory trace symmetry metrics from docs/v2.

    Heuristics intentionally distinguish three sources:
    - design-side universe: only the doc's own definition lines
    - cross-layer references: mapping/trace/input-output tables are excluded
    - test-side coverage: only IDs named in target columns or trace-style tables
    """

    root = _project_root(project_root)
    documents = _load_documents(root)
    doc_index = {doc.rel_path: doc for doc in documents}

    report: dict[str, Any] = {
        "advisory": True,
        "exit_code": 0,
        "pairs": {},
        "preflight_fail": {
            "duplicate_id": [],
            "missing_pair_frontmatter": [],
            "wrong_layer_pair": [],
        },
    }

    for pair_name, (design_layer, test_layer) in PAIR_LAYERS.items():
        design_docs = [
            doc
            for doc in documents
            if doc.process_layer == design_layer and doc.status != "deprecated"
        ]
        test_docs = [
            doc
            for doc in documents
            if doc.process_layer == test_layer and doc.status != "deprecated"
        ]
        deprecated_docs = sorted(
            doc.rel_path
            for doc in documents
            if doc.process_layer in {design_layer, test_layer} and doc.status == "deprecated"
        )

        missing_pair = _missing_pair_docs(
            design_docs,
            test_docs,
            doc_index,
            expected_design_layer=design_layer,
            expected_test_layer=test_layer,
        )
        wrong_layer = _wrong_layer_docs(
            design_docs,
            test_docs,
            doc_index,
            expected_design_layer=design_layer,
            expected_test_layer=test_layer,
        )
        connected_test_paths = _connected_test_docs(
            design_docs,
            test_docs,
            doc_index,
            expected_design_layer=design_layer,
            expected_test_layer=test_layer,
        )

        design_entries_raw = [entry for doc in design_docs for entry in _collect_design_entries(doc)]
        duplicate_ids, duplicate_details = _duplicate_details(design_entries_raw)

        design_entries, excluded_entries = _verification_applicable(
            design_entries_raw,
            doc_index,
            test_layer=test_layer,
        )
        connected_test_docs = [doc for doc in test_docs if doc.rel_path in connected_test_paths]
        covered_design_ids, mapped_test_ids, test_definition_ids = _collect_test_coverage(
            connected_test_docs,
            design_ids={entry.entry_id for entry in design_entries},
        )
        uncovered, orphan, coverage_pct, balance_ratio = _coverage_summary(
            design_entries,
            covered_design_ids,
            test_definition_ids,
            mapped_test_ids,
        )

        report["pairs"][pair_name] = {
            "design_layer": design_layer,
            "test_layer": test_layer,
            "uncovered_req": {"count": len(uncovered), "ids": uncovered},
            "orphan_test": {"count": len(orphan), "ids": orphan},
            "coverage_pct": coverage_pct,
            "duplicate_id": {"count": len(duplicate_ids), "ids": duplicate_ids},
            "missing_pair_frontmatter": {
                "count": len(missing_pair),
                "docs": sorted(item["doc"] for item in missing_pair),
            },
            "wrong_layer_pair": {
                "count": len(wrong_layer),
                "docs": sorted(item["doc"] for item in wrong_layer),
            },
            "excluded_with_reason": {
                "count": len(excluded_entries),
                "items": sorted(
                    excluded_entries,
                    key=lambda item: (item["doc"], item["id"], item["reason"]),
                ),
            },
            "deprecated_excluded": {
                "count": len(deprecated_docs),
                "docs": deprecated_docs,
            },
            "balance_ratio": balance_ratio,
        }

        report["preflight_fail"]["duplicate_id"].extend(duplicate_details)
        report["preflight_fail"]["missing_pair_frontmatter"].extend(missing_pair)
        report["preflight_fail"]["wrong_layer_pair"].extend(wrong_layer)

    for key in report["preflight_fail"]:
        report["preflight_fail"][key] = sorted(
            report["preflight_fail"][key],
            key=lambda item: (item.get("id", ""), item.get("doc", ""), item.get("line", 0)),
        )
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Advisory trace symmetry detector for docs/v2.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = collect_trace_symmetry()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
