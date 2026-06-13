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


ID_PATTERN = r"(?:FR|NFR|BR|TR|OT|AT|ST|IF|IT|UT|IP|DB|MOD|FN|FUNC)-[A-Z0-9]+(?:-[A-Z0-9]+)*"
ID_RE = re.compile(rf"^{ID_PATTERN}$")
ID_SEARCH_RE = re.compile(rf"(?<![A-Z0-9-])({ID_PATTERN})(?![A-Z0-9-])")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
LAYER_RE = re.compile(r"^L[0-9]+$")
PAIR_FIELDS = (
    "pairs_test_design",
    "pair_artifact",
    "generates",
    "covers",
    "parent_design",
    "pairs_design",
)
PAIR_LAYERS = {
    "L1-L14": ("L1", "L14"),
    "L3-L12": ("L3", "L12"),
    "L4-L9": ("L4", "L9"),
    "L5-L8": ("L5", "L8"),
    "L6-L7": ("L6", "L7"),
}
PAIR_DOC_PREFIXES = {
    "L1": "docs/v2/L1-requirements/",
    "L3": "docs/v2/L3-requirements/",
    "L4": "docs/v2/L4-basic-design/",
    "L5": "docs/v2/L5-detailed-design/",
    "L6": "docs/v2/L6-functional-design/",
    "L7": "docs/v2/L7-test-design/",
    "L8": "docs/v2/L8-test-design/",
    "L9": "docs/v2/L9-test-design/",
    "L12": "docs/v2/L12-test-design/",
    "L14": "docs/v2/L14-test-design/",
}
EXCLUDED_DOC_KINDS = {"verification-strategy"}
EXCLUDED_ARTIFACT_TYPES = {"functional_registry"}
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


@dataclass(frozen=True)
class PairTarget:
    path: str | None
    ids: tuple[str, ...] = ()


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


def _normalize_pair_targets(value: Any) -> list[PairTarget]:
    values: list[PairTarget] = []
    if isinstance(value, str):
        normalized = _normalize_doc_path(value)
        if normalized:
            values.append(PairTarget(path=normalized))
        return values
    if isinstance(value, list):
        for item in value:
            values.extend(_normalize_pair_targets(item))
        return values
    if isinstance(value, dict):
        paths: list[str | None] = []
        for key in ("artifact_path", "path", "doc_path"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                normalized = _normalize_doc_path(candidate)
                if normalized:
                    paths.append(normalized)
        if not paths:
            paths.append(None)
        ids = tuple(_normalize_id_values(value.get("id")) + _normalize_id_values(value.get("ids")))
        for path in paths:
            if path or ids:
                values.append(PairTarget(path=path, ids=ids))
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


def _pair_targets(doc: Document) -> list[PairTarget]:
    targets: list[PairTarget] = []
    for field in PAIR_FIELDS:
        targets.extend(_normalize_pair_targets(doc.frontmatter.get(field)))

    deduped: dict[tuple[str | None, tuple[str, ...]], PairTarget] = {}
    for target in targets:
        deduped[(target.path, tuple(sorted(set(target.ids))))] = PairTarget(
            path=target.path,
            ids=tuple(sorted(set(target.ids))),
        )
    return sorted(
        deduped.values(),
        key=lambda item: (item.path or "", item.ids),
    )


def _pair_links(doc: Document) -> list[str]:
    return [target.path for target in _pair_targets(doc) if target.path]


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


def _entry_priority(entry: DefinitionEntry) -> tuple[int, int]:
    info_score = len([token for token in re.split(r"\W+", entry.row_text) if token])
    return (2 if entry.kind == "heading" else 1, info_score)


def _collapse_doc_duplicate_entries(entries: list[DefinitionEntry]) -> list[DefinitionEntry]:
    grouped: dict[tuple[str, str], list[DefinitionEntry]] = defaultdict(list)
    for entry in entries:
        grouped[(entry.doc_path, entry.entry_id)].append(entry)

    collapsed: list[DefinitionEntry] = []
    for items in grouped.values():
        if len(items) == 1:
            collapsed.extend(items)
            continue
        ranked = sorted(items, key=lambda item: (_entry_priority(item), -item.line_no), reverse=True)
        best_score = _entry_priority(ranked[0])
        best_items = [item for item in ranked if _entry_priority(item) == best_score]
        collapsed.extend(best_items)
    return sorted(
        collapsed,
        key=lambda entry: (entry.doc_path, entry.line_no, entry.entry_id, entry.kind),
    )


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

    filtered = [
        entry
        for entry in entries
        if _scheme_signature(entry.entry_id) in allowed_schemes[entry.entry_id.split("-", 1)[0]]
    ]
    return _collapse_doc_duplicate_entries(filtered)


def _pair_prefix(layer: str) -> str:
    return PAIR_DOC_PREFIXES.get(layer, "")


def _is_pair_artifact_doc(doc: Document, layer: str) -> bool:
    prefix = _pair_prefix(layer)
    if doc.process_layer != layer or doc.status == "deprecated":
        return False
    if prefix and not doc.rel_path.startswith(prefix):
        return False
    if doc.frontmatter.get("doc_kind") in EXCLUDED_DOC_KINDS:
        return False
    if doc.frontmatter.get("artifact_type") in EXCLUDED_ARTIFACT_TYPES:
        return False
    return True


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


def _collect_test_reference_ids(test_docs: list[Document]) -> set[str]:
    test_definition_ids: set[str] = set()
    for doc in test_docs:
        test_definition_ids |= {entry.entry_id for entry in _collect_test_definition_entries(doc)}

    referenced_design_ids: set[str] = set()
    for doc in test_docs:
        for table in _coverage_sources(doc):
            for row in table.rows:
                row_ids = {
                    match.group(1)
                    for cell in row.cells
                    for match in ID_SEARCH_RE.finditer(cell)
                    if _is_valid_id(match.group(1))
                }
                referenced_design_ids |= (row_ids - test_definition_ids)
    return referenced_design_ids


def _relevant_pair_docs(
    design_docs: list[Document],
    test_docs: list[Document],
) -> tuple[list[Document], list[Document]]:
    design_entries_by_doc = {
        doc.rel_path: _collect_design_entries(doc)
        for doc in design_docs
    }
    referenced_design_ids = _collect_test_reference_ids(test_docs)

    direct_design_paths = {
        doc.rel_path
        for doc in design_docs
        if _pair_targets(doc)
    }
    direct_design_paths |= {
        link
        for doc in test_docs
        for link in _pair_links(doc)
    }

    relevant_design_docs = [
        doc
        for doc in design_docs
        if doc.rel_path in direct_design_paths
        or any(entry.entry_id in referenced_design_ids for entry in design_entries_by_doc[doc.rel_path])
    ]
    relevant_design_ids = {
        entry.entry_id
        for doc in relevant_design_docs
        for entry in design_entries_by_doc[doc.rel_path]
    }
    relevant_design_paths = {doc.rel_path for doc in relevant_design_docs}
    forward_linked_test_paths = {
        link
        for design_doc in relevant_design_docs
        for link in _pair_links(design_doc)
    }

    relevant_test_docs = [
        doc
        for doc in test_docs
        if any(link in relevant_design_paths for link in _pair_links(doc))
        or bool(_collect_test_reference_ids([doc]) & relevant_design_ids)
        or doc.rel_path in forward_linked_test_paths
    ]
    return relevant_design_docs, relevant_test_docs


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


def _semantic_orphan_exclusions(
    test_docs: list[Document],
    orphan_ids: list[str],
) -> dict[str, str]:
    if not orphan_ids:
        return {}

    exclusions: dict[str, str] = {}
    for doc in test_docs:
        text = doc.path.read_text(encoding="utf-8")
        normalized = text.replace("->", "→")
        has_semantic_pass = "audit_verdict" in text and "pass" in text.lower()
        has_transitive_trace = "ST→TV→L4" in normalized or "ST-* → TV-* → L4" in normalized
        if not (has_semantic_pass and has_transitive_trace):
            continue

        doc_test_ids = {entry.entry_id for entry in _collect_test_definition_entries(doc)}
        for orphan_id in orphan_ids:
            if orphan_id in doc_test_ids:
                exclusions[orphan_id] = (
                    f"{doc.rel_path}: semantic_gate transitive trace accepted "
                    "(ST→TV→L4, audit_verdict=pass)"
                )
    return exclusions


def _definition_ids_by_doc(
    docs: list[Document],
    collector: Any,
) -> dict[str, set[str]]:
    return {
        doc.rel_path: {entry.entry_id for entry in collector(doc)}
        for doc in docs
    }


def _missing_pair_docs(
    design_docs: list[Document],
    test_docs: list[Document],
    doc_index: dict[str, Document],
    *,
    expected_design_layer: str,
    expected_test_layer: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    design_ids_by_doc = _definition_ids_by_doc(design_docs, _collect_design_entries)
    test_ids_by_doc = _definition_ids_by_doc(test_docs, _collect_test_definition_entries)

    if not design_docs:
        findings.append(
            {
                "role": "design",
                "reason": "missing_layer_docs",
                "target_dir": _pair_prefix(expected_design_layer),
            }
        )
    if not test_docs:
        findings.append(
            {
                "role": "test",
                "reason": "missing_layer_docs",
                "target_dir": _pair_prefix(expected_test_layer),
            }
        )

    for role, docs, target_layer, known_ids in (
        ("design", design_docs, expected_test_layer, test_ids_by_doc),
        ("test", test_docs, expected_design_layer, design_ids_by_doc),
    ):
        for doc in docs:
            targets = _pair_targets(doc)
            if not targets:
                findings.append({"doc": doc.rel_path, "role": role, "reason": "missing_pair_frontmatter"})
                continue

            matched_any = False
            reported_target_issue = False
            for target in targets:
                if not target.path:
                    continue
                target_doc = doc_index.get(target.path)
                if target_doc is None:
                    findings.append(
                        {
                            "doc": doc.rel_path,
                            "role": role,
                            "reason": "missing_target_pair",
                            "target": target.path,
                        }
                    )
                    reported_target_issue = True
                    continue
                if target_doc.process_layer != target_layer:
                    reported_target_issue = True
                    continue
                matched_any = True
                if target.ids:
                    missing_ids = sorted(set(target.ids) - known_ids.get(target.path, set()))
                    if missing_ids:
                        findings.append(
                            {
                                "doc": doc.rel_path,
                                "role": role,
                                "reason": "missing_target_ids",
                                "target": target.path,
                                "ids": missing_ids,
                            }
                        )
                        reported_target_issue = True
            if not matched_any and not reported_target_issue:
                findings.append(
                    {
                        "doc": doc.rel_path,
                        "role": role,
                        "reason": "missing_target_pair",
                    }
                )
    return findings


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
            if _is_pair_artifact_doc(doc, design_layer)
        ]
        test_docs = [
            doc
            for doc in documents
            if _is_pair_artifact_doc(doc, test_layer)
        ]
        design_docs, test_docs = _relevant_pair_docs(design_docs, test_docs)
        deprecated_docs = sorted(
            doc.rel_path
            for doc in documents
            if doc.process_layer in {design_layer, test_layer}
            and doc.status == "deprecated"
            and (
                (_pair_prefix(doc.process_layer) and doc.rel_path.startswith(_pair_prefix(doc.process_layer)))
                or not _pair_prefix(doc.process_layer)
            )
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

        design_entries_raw = [entry for doc in design_docs for entry in _collect_design_entries(doc)]
        duplicate_ids, duplicate_details = _duplicate_details(design_entries_raw)

        design_entries, excluded_entries = _verification_applicable(
            design_entries_raw,
            doc_index,
            test_layer=test_layer,
        )
        covered_design_ids, mapped_test_ids, test_definition_ids = _collect_test_coverage(
            test_docs,
            design_ids={entry.entry_id for entry in design_entries},
        )
        uncovered, orphan, coverage_pct, balance_ratio = _coverage_summary(
            design_entries,
            covered_design_ids,
            test_definition_ids,
            mapped_test_ids,
        )
        semantic_orphan_exclusions = _semantic_orphan_exclusions(test_docs, orphan)
        effective_orphan = [
            orphan_id for orphan_id in orphan if orphan_id not in semantic_orphan_exclusions
        ]

        report["pairs"][pair_name] = {
            "design_layer": design_layer,
            "test_layer": test_layer,
            "uncovered_req": {"count": len(uncovered), "ids": uncovered},
            "orphan_test": {"count": len(effective_orphan), "ids": effective_orphan},
            "semantic_excluded_orphan": {
                "count": len(semantic_orphan_exclusions),
                "items": [
                    {"id": orphan_id, "reason": reason}
                    for orphan_id, reason in sorted(semantic_orphan_exclusions.items())
                ],
            },
            "coverage_pct": coverage_pct,
            "duplicate_id": {"count": len(duplicate_ids), "ids": duplicate_ids},
            "missing_pair_frontmatter": {
                "count": len(missing_pair),
                "docs": sorted({item["doc"] for item in missing_pair if "doc" in item}),
            },
            "missing_pair": {
                "count": len(missing_pair),
                "items": sorted(
                    missing_pair,
                    key=lambda item: (
                        item.get("role", ""),
                        item.get("doc", ""),
                        item.get("reason", ""),
                        item.get("target", ""),
                    ),
                ),
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
