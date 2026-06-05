#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from yaml_parser import parse_yaml

try:
    import yaml as pyyaml
except ImportError:  # pragma: no cover - fallback path is verified via parse_yaml
    pyyaml = None


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DOC = REPO_ROOT / "docs/v2/L3-requirements/helix-workflows-functional-registry.md"
OUTPUT_YAML = REPO_ROOT / "cli/config/functional-registry.yaml"

DOMAIN_SECTION_MARKERS = (
    ("## §3.", "## §4.", "cli"),
    ("## §4.", "## §5.", "lib"),
    ("## §5.", "## §6.", "hook"),
    ("## §6.", "## §7.", "agent"),
    ("## §7.", "## §8.", "skill"),
    ("## §8.", "## §9.", "workflow"),
    ("## §9.", "## §10.", "template"),
)
DOMAIN_ID_PREFIX = {
    "cli": "CLI",
    "lib": "LIB",
    "hook": "HOOK",
    "agent": "AGENT",
    "skill": "SKILL",
    "workflow": "WORKFLOW",
    "template": "TEMPLATE",
}
ALLOWED_DOMAINS = set(DOMAIN_ID_PREFIX)
ALLOWED_STATUSES = {"active", "deprecated", "legacy_alias", "mandatory", "experimental"}
FR_PATTERN = re.compile(r"\bFR-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
GROUPED_ROW_PATTERN = re.compile(r"^(?P<start>.+?)〜(?P<end>.+?)\s+\((?P<count>\d+)\s+file\)$")
SUMMARY_TOTAL = 548


class SeedError(RuntimeError):
    pass


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _extract_fr_ids(raw: str) -> list[str]:
    return _unique(FR_PATTERN.findall(raw or ""))


def _normalize_status(raw: str | None) -> str:
    value = (raw or "active").strip().strip("`").lower()
    if value in {"", "-"}:
        return "active"
    value = value.replace(" ", "_")
    aliases = {
        "legacy_alias": "legacy_alias",
        "legacy-alias": "legacy_alias",
    }
    normalized = aliases.get(value, value)
    if normalized not in ALLOWED_STATUSES:
        raise SeedError(f"unsupported status value: {raw!r}")
    return normalized


def _split_markdown_row(line: str, headers: list[str] | None = None) -> list[str]:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if headers is None or len(cells) <= len(headers):
        return cells

    if "関連 L1 FR" not in headers:
        return cells

    l1_index = headers.index("関連 L1 FR")
    tail_count = len(headers) - l1_index
    if l1_index <= 1 or len(cells) <= tail_count:
        return cells

    prefix = cells[: l1_index - 1]
    merged = " | ".join(cells[l1_index - 1 : len(cells) - tail_count])
    suffix = cells[len(cells) - tail_count :]
    realigned = prefix + [merged] + suffix
    return realigned if len(realigned) == len(headers) else cells


def _parse_tables(section_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = section_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|---"):
            headers = _split_markdown_row(line)
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                values = _split_markdown_row(lines[index], headers)
                if len(values) == len(headers):
                    rows.append(dict(zip(headers, values)))
                index += 1
            continue
        index += 1
    return rows


def _section_slice(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def _iter_domain_rows() -> list[tuple[str, dict[str, str]]]:
    text = SOURCE_DOC.read_text(encoding="utf-8")
    rows: list[tuple[str, dict[str, str]]] = []
    for start_marker, end_marker, domain in DOMAIN_SECTION_MARKERS:
        section = _section_slice(text, start_marker, end_marker)
        for row in _parse_tables(section):
            rows.append((domain, row))
    return rows


def _derive_description(row: dict[str, str]) -> str:
    headers = list(row.keys())
    ignored = {headers[0], "関連 L1 FR", "関連 L3 FR", "状態"}
    parts = [row[header] for header in headers[1:] if header not in ignored and row[header] and row[header] != "-"]
    return " / ".join(parts)


def _template_is_doc(path: Path) -> bool:
    return ".md" in path.suffixes


def _classify_template_path(relative_path: str) -> tuple[list[str], list[str]]:
    resolved = REPO_ROOT / relative_path
    if not resolved.exists():
        return [], []
    if _template_is_doc(resolved):
        return [], [relative_path]
    return [relative_path], []


def _resolve_paths(domain: str, name: str, explicit_relative_path: str | None = None) -> tuple[list[str], list[str]]:
    if explicit_relative_path is not None:
        return _classify_template_path(explicit_relative_path)

    code_paths: list[str] = []
    doc_paths: list[str] = []

    if domain == "cli":
        candidate = REPO_ROOT / "cli" / (name if name.startswith("helix-") else f"helix-{name}")
        if candidate.exists():
            code_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    elif domain == "lib":
        module_name = name if name.endswith(".py") else f"{name}.py"
        candidate = REPO_ROOT / "cli/lib" / module_name
        if candidate.exists():
            code_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    elif domain == "hook":
        for candidate in (
            REPO_ROOT / ".claude/hooks" / name,
            REPO_ROOT / "cli/libexec" / name,
        ):
            if candidate.exists():
                code_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
                break
    elif domain == "agent":
        agent_name = name if name.endswith(".md") else f"{name}.md"
        candidate = REPO_ROOT / ".claude/agents" / agent_name
        if candidate.exists():
            doc_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    elif domain == "skill":
        candidate = REPO_ROOT / "skills" / name / "SKILL.md"
        if candidate.exists():
            doc_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    elif domain == "workflow":
        if name == "HELIX-process-L0-L14.md":
            candidate = REPO_ROOT / "HELIX-workflows" / name
        else:
            candidate = REPO_ROOT / "HELIX-workflows/helix-process" / name
        if candidate.exists():
            doc_paths.append(candidate.relative_to(REPO_ROOT).as_posix())
    elif domain == "template":
        return _classify_template_path(f"cli/templates/{name}")
    else:  # pragma: no cover - protected by validate_entries
        raise SeedError(f"unsupported domain: {domain}")

    return code_paths, doc_paths


def _expand_grouped_template_row(
    row_name: str,
    description: str,
    l1_fr: list[str],
    l3_fr: list[str],
    status: str,
    grouped_row_counts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    match = GROUPED_ROW_PATTERN.match(row_name)
    if not match:
        raise SeedError(f"invalid grouped row syntax: {row_name}")

    prefix = Path(match.group("start").strip())
    directory = prefix.parent.as_posix()
    expected_count = int(match.group("count"))
    target_dir = REPO_ROOT / "cli/templates" / directory
    if not target_dir.is_dir():
        raise SeedError(f"grouped row directory is missing: {target_dir.relative_to(REPO_ROOT).as_posix()}")

    files = sorted(path for path in target_dir.iterdir() if path.is_file())
    grouped_row_counts.append(
        {
            "row": row_name,
            "directory": target_dir.relative_to(REPO_ROOT).as_posix(),
            "expected": expected_count,
            "actual": len(files),
        }
    )

    entries: list[dict[str, Any]] = []
    for path in files:
        relative_path = path.relative_to(REPO_ROOT).as_posix()
        code_paths, doc_paths = _classify_template_path(relative_path)
        entries.append(
            {
                "name": path.name,
                "description": description,
                "l1_fr": list(l1_fr),
                "l3_fr": list(l3_fr),
                "status": status,
                "code_paths": code_paths,
                "doc_paths": doc_paths,
            }
        )
    return entries


def _build_entry_payloads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _iter_domain_rows()
    per_domain_seen: dict[str, set[str]] = defaultdict(set)
    duplicate_rows: list[dict[str, str]] = []
    grouped_row_counts: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []

    for domain, row in rows:
        headers = list(row.keys())
        name = row[headers[0]]
        description = _derive_description(row)
        l1_fr = _extract_fr_ids(row.get("関連 L1 FR", ""))
        l3_fr = _extract_fr_ids(row.get("関連 L3 FR", ""))
        status = _normalize_status(row.get("状態"))

        expanded_rows: list[dict[str, Any]]
        if domain == "template" and GROUPED_ROW_PATTERN.match(name):
            expanded_rows = _expand_grouped_template_row(name, description, l1_fr, l3_fr, status, grouped_row_counts)
        else:
            code_paths, doc_paths = _resolve_paths(domain, name)
            expanded_rows = [
                {
                    "name": name,
                    "description": description,
                    "l1_fr": l1_fr,
                    "l3_fr": l3_fr,
                    "status": status,
                    "code_paths": code_paths,
                    "doc_paths": doc_paths,
                }
            ]

        for payload in expanded_rows:
            key = payload["name"]
            if key in per_domain_seen[domain]:
                duplicate_rows.append({"domain": domain, "name": key})
                continue
            per_domain_seen[domain].add(key)
            entries.append(
                {
                    "domain": domain,
                    "name": payload["name"],
                    "description": payload["description"],
                    "l1_fr": payload["l1_fr"],
                    "l3_fr": payload["l3_fr"],
                    "status": payload["status"],
                    "code_paths": payload["code_paths"],
                    "doc_paths": payload["doc_paths"],
                }
            )

    counters: dict[str, int] = defaultdict(int)
    finalized: list[dict[str, Any]] = []
    for entry in entries:
        domain = entry["domain"]
        counters[domain] += 1
        finalized.append(
            {
                "id": f"FR-{DOMAIN_ID_PREFIX[domain]}-{counters[domain]:03d}",
                "name": entry["name"],
                "domain": domain,
                "description": entry["description"],
                "l1_fr": entry["l1_fr"],
                "l3_fr": entry["l3_fr"],
                "status": entry["status"],
                "code_paths": entry["code_paths"],
                "doc_paths": entry["doc_paths"],
            }
        )

    metadata = {
        "generated_counts": dict(sorted(Counter(entry["domain"] for entry in finalized).items())),
        "duplicate_rows": duplicate_rows,
        "grouped_row_counts": grouped_row_counts,
        "missing_primary_paths": [
            f"{entry['domain']}:{entry['name']}" for entry in finalized if not entry["code_paths"] and not entry["doc_paths"]
        ],
    }
    return finalized, metadata


def _render_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _render_list(items: list[str], indent: int) -> list[str]:
    prefix = " " * indent
    return [f"{prefix}- {_render_string(item)}" for item in items]


def _render_keyed_list(key: str, items: list[str], indent: int) -> list[str]:
    prefix = " " * indent
    if not items:
        return [f"{prefix}{key}: []"]
    lines = [f"{prefix}{key}:"]
    lines.extend(_render_list(items, indent + 2))
    return lines


def _render_yaml(entries: list[dict[str, Any]]) -> str:
    lines = ["entries:"]
    for entry in entries:
        lines.append(f"  - id: {_render_string(entry['id'])}")
        lines.append(f"    name: {_render_string(entry['name'])}")
        lines.append(f"    domain: {_render_string(entry['domain'])}")
        lines.append(f"    description: {_render_string(entry['description'])}")
        lines.extend(_render_keyed_list("l1_fr", entry["l1_fr"], 4))
        lines.extend(_render_keyed_list("l3_fr", entry["l3_fr"], 4))
        lines.append(f"    status: {_render_string(entry['status'])}")
        lines.extend(_render_keyed_list("code_paths", entry["code_paths"], 4))
        lines.extend(_render_keyed_list("doc_paths", entry["doc_paths"], 4))
    return "\n".join(lines) + "\n"


def _load_rendered_yaml(text: str) -> dict[str, Any]:
    if pyyaml is not None:
        payload = pyyaml.safe_load(text) or {}
    else:
        payload = parse_yaml(text)
    if not isinstance(payload, dict):
        raise SeedError("rendered YAML must load as a mapping")
    return payload


def _validate_entries(entries: list[dict[str, Any]]) -> None:
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise SeedError("duplicate id detected in generated entries")

    required_fields = {"id", "name", "domain", "description", "l1_fr", "l3_fr", "status", "code_paths", "doc_paths"}
    for entry in entries:
        if set(entry) != required_fields:
            raise SeedError(f"schema field mismatch for {entry.get('id', '<unknown>')}: {sorted(entry)}")
        if entry["domain"] not in ALLOWED_DOMAINS:
            raise SeedError(f"unsupported domain: {entry['domain']}")
        if entry["status"] not in ALLOWED_STATUSES:
            raise SeedError(f"unsupported status: {entry['status']}")
        for key in ("l1_fr", "l3_fr", "code_paths", "doc_paths"):
            if not isinstance(entry[key], list) or not all(isinstance(item, str) for item in entry[key]):
                raise SeedError(f"{entry['id']} field must be list[str]: {key}")
        for key in ("id", "name", "description"):
            if not isinstance(entry[key], str) or not entry[key]:
                raise SeedError(f"{entry['id']} field must be non-empty string: {key}")


def _disk_counts() -> dict[str, int]:
    return {
        "cli": len(
            [
                path
                for path in (REPO_ROOT / "cli").glob("helix-*")
                if path.is_file() and path.stat().st_mode & 0o111
            ]
        ),
        "lib": len(list((REPO_ROOT / "cli/lib").glob("*.py"))),
        "hook": len([path for path in (REPO_ROOT / ".claude/hooks").iterdir() if path.is_file()]),
        "agent": len(list((REPO_ROOT / ".claude/agents").glob("*.md"))),
        "skill": len(list((REPO_ROOT / "skills").glob("**/SKILL.md"))),
        "workflow": len(
            {
                *{
                    path.relative_to(REPO_ROOT).as_posix()
                    for path in (REPO_ROOT / "HELIX-workflows").glob("*.md")
                    if path.is_file()
                },
                *{
                    path.relative_to(REPO_ROOT).as_posix()
                    for path in (REPO_ROOT / "HELIX-workflows/helix-process").glob("*.md")
                    if path.is_file()
                },
            }
        ),
        "template": len([path for path in (REPO_ROOT / "cli/templates").glob("**/*") if path.is_file()]),
    }


def _print_summary(entries: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    generated_counts = metadata["generated_counts"]
    disk_counts = _disk_counts()
    total = len(entries)
    diff = total - SUMMARY_TOTAL
    lib_disk_only = sorted(
        path.name
        for path in (REPO_ROOT / "cli/lib").glob("*.py")
        if path.name not in {entry["name"] for entry in entries if entry["domain"] == "lib"}
    )
    skill_missing = sorted(
        entry["name"] for entry in entries if entry["domain"] == "skill" and not entry["doc_paths"]
    )

    print(f"generated_entries={total}")
    print(f"summary_declared_entries={SUMMARY_TOTAL}")
    print(f"summary_diff={diff:+d}")
    print("generated_counts=" + json.dumps(generated_counts, ensure_ascii=False, sort_keys=True))
    print("disk_counts=" + json.dumps(disk_counts, ensure_ascii=False, sort_keys=True))

    diff_reasons: list[str] = []
    if generated_counts.get("lib") == 140:
        diff_reasons.append("md §2 summary の lib=139 に対して §4 表は 140 行")
    if metadata["duplicate_rows"]:
        duplicate_text = ", ".join(f"{item['domain']}:{item['name']}" for item in metadata["duplicate_rows"])
        diff_reasons.append(f"重複行は 1 entry に畳み込み ({duplicate_text})")
    for grouped in metadata["grouped_row_counts"]:
        marker = "ok" if grouped["expected"] == grouped["actual"] else "mismatch"
        diff_reasons.append(
            f"grouped row {grouped['row']} => {grouped['directory']} {grouped['actual']}/{grouped['expected']} ({marker})"
        )
    if disk_counts.get("lib", 0) != generated_counts.get("lib", 0):
        diff_reasons.append(
            f"cli/lib の disk-only module は {', '.join(lib_disk_only)} で、yaml は md §4 source row の 140 entry を採用"
        )
    if disk_counts.get("workflow", 0) != generated_counts.get("workflow", 0):
        diff_reasons.append(
            "workflow は md §8 に列挙された 49 entry を採用し、disk-only doc は detector 向け未登録差分として残す"
        )
    if skill_missing:
        diff_reasons.append(
            f"skill の source-only row は {', '.join(skill_missing)} で、doc_paths 空のまま保持"
        )
    print("diff_reasons=" + json.dumps(diff_reasons, ensure_ascii=False))


def main() -> int:
    entries, metadata = _build_entry_payloads()
    _validate_entries(entries)

    yaml_text = _render_yaml(entries)
    loaded = _load_rendered_yaml(yaml_text)
    if not isinstance(loaded.get("entries"), list):
        raise SeedError("rendered YAML must contain entries list")
    _validate_entries(loaded["entries"])

    OUTPUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_YAML.write_text(yaml_text, encoding="utf-8")
    _print_summary(entries, metadata)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SeedError as exc:
        print(f"functional_registry_seed error: {exc}", file=sys.stderr)
        raise SystemExit(1)
