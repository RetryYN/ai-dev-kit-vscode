from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from . import discovery_compat
except ImportError:  # pragma: no cover
    import discovery_compat  # type: ignore[no-redef]


VALID_KINDS = {
    "design",
    "impl",
    "poc",
    "reverse",
    "troubleshoot",
    "refactor",
    "retrofit",
    "research",
    "add-design",
    "add-impl",
    "recovery",
    # 新 V2 完全移行 (2026-05-24): HELIX-model 工程別 kind
    "planning",
    "requirements",
    "ui-design",
    "basic-design",
    "detailed-design",
    "function-design",
    "test",
    "ux-refinement",
    "review",
    "deployment",
    "operation",
}
VALID_LAYERS = {
    "L0",
    "L1",
    "L2",
    "L3",
    "L3.5",
    "L4",
    "L4.5",
    "L5",
    "L6",
    "L7",
    "L8",
    "L9",
    "L10",
    "L11",
    "L12",
    "L13",
    "L14",
    "cross",
}
# 新 15 工程 (L0-L14): docs/v2/process/README.md 参照。
# kind=impl は process_layer=L7 を必須 (commit eeb0530)。
VALID_PROCESS_LAYERS = {
    "L0",
    "L1",
    "L2",
    "L3",
    "L4",
    "L5",
    "L6",
    "L7",
    "L8",
    "L9",
    "L10",
    "L11",
    "L12",
    "L13",
    "L14",
}
MISUSED_WORKFLOW_LAYERS = {"S0", "S1", "S2", "S3", "S4", "R0", "R1", "R2", "R3", "R4"}
VALID_DRIVES = {
    "be",
    "fe",
    "fullstack",
    "discovery",
    "scrum",
    "db",
    "agent",
    "reverse",
    "poc",
    "troubleshoot",
}
VALID_WORKFLOW_PHASES = MISUSED_WORKFLOW_LAYERS
VALID_ARTIFACT_TYPES = {
    "design_doc",
    "adr_snapshot",
    "cli_extension",
    "template",
    "python_module",
    "test",
    "hook",
    "schema_migration",
    "config",
    "script",
    "doc_update",
    "markdown_doc",
    "yaml_config",
    "json_config",
    "binary",
    "other",
}
REQUIRED_FIELDS = (
    "plan_id",
    "title",
    "kind",
    "layer",
    "drive",
    "status",
    "agent_slots",
    "generates",
    "dependencies",
)
# V1 (legacy): PLAN-NNN / PLAN-NNN-slug / PLAN-MM-NNN
V1_PLAN_ID_RE = re.compile(r"^PLAN-(?:\d{3}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?|MM-\d{3})$")
# V2 (新、HELIX-model 正本): L<NN>-<slug>plan (例: L0-企画書plan / L7-helix-workspace-mergeplan)
V2_PLAN_ID_RE = re.compile(r"^L(?:[0-9]|1[0-4])-[^\s]+plan$")
# 後方互換: 既存テストや CLI から参照される PLAN_ID_RE は V1 形式のまま (旧仕様維持)。
PLAN_ID_RE = V1_PLAN_ID_RE
ROLE_HEADER_RE = re.compile(r"^\|\s*ロール\s*\|\s*model\s*\|", re.IGNORECASE)


@dataclass(frozen=True)
class PlanFrontmatter:
    plan_id: str | None
    title: str | None
    kind: str | None
    layer: str | None
    drive: str | None
    status: str | None
    workflow_phase: str | None
    process_layer: str | None
    parent_design: str | None
    pairs_test_design: Any
    agent_slots: Any
    generates: Any
    dependencies: Any
    raw: dict[str, Any]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="plan_validator.py",
        description="Validate PLAN markdown frontmatter in V5 P1 warn-only mode.",
    )
    parser.add_argument("plan_file", help="PLAN markdown file to validate")
    return parser.parse_args(argv)


def load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter がありません")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise ValueError("frontmatter の終端 `---` がありません")

    payload = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    if not isinstance(payload, dict):
        raise ValueError("frontmatter は mapping である必要があります")
    return payload


def parse_frontmatter(data: dict[str, Any]) -> PlanFrontmatter:
    return PlanFrontmatter(
        plan_id=_string_or_none(data.get("plan_id")),
        title=_string_or_none(data.get("title")),
        kind=_string_or_none(data.get("kind")),
        layer=_string_or_none(data.get("layer")),
        drive=_string_or_none(data.get("drive")),
        status=_string_or_none(data.get("status")),
        workflow_phase=_string_or_none(data.get("workflow_phase")),
        process_layer=_string_or_none(data.get("process_layer")),
        parent_design=_string_or_none(data.get("parent_design")),
        pairs_test_design=data.get("pairs_test_design"),
        agent_slots=data.get("agent_slots"),
        generates=data.get("generates"),
        dependencies=data.get("dependencies"),
        raw=data,
    )


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _classify_plan_format(plan_id: str | None) -> str:
    """plan_id を V1 / V2 / unknown に分類 (V2 完全移行、2026-05-24)."""
    if plan_id is None:
        return "missing"
    if V2_PLAN_ID_RE.fullmatch(plan_id):
        return "v2"
    if V1_PLAN_ID_RE.fullmatch(plan_id):
        return "v1"
    return "unknown"


def role_map_path() -> Path:
    return Path(__file__).resolve().parents[1] / "ROLE_MAP.md"


def load_valid_roles() -> set[str]:
    lines = role_map_path().read_text(encoding="utf-8").splitlines()
    in_role_table = False
    roles: set[str] = set()

    for line in lines:
        if not in_role_table:
            if ROLE_HEADER_RE.match(line):
                in_role_table = True
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"ロール", "--------"}:
            continue
        role = cells[0]
        if re.fullmatch(r"[a-z0-9-]+", role):
            roles.add(role)
    return roles


def warn(plan_ref: str, field: str, reason: str, warnings: list[str]) -> None:
    warnings.append(f"WARN [{plan_ref}] field={field} reason={reason}")


def locate_plan_file(current_plan_path: Path, target_plan_id: str) -> Path | None:
    directories = _plan_search_directories(current_plan_path)

    patterns = (f"{target_plan_id}.md", f"{target_plan_id}-*.md")
    for directory in directories:
        for pattern in patterns:
            for match in sorted(directory.glob(pattern)):
                if match.resolve() != current_plan_path.resolve():
                    return match
    return None


def _plan_search_directories(current_plan_path: Path) -> list[Path]:
    directories = [current_plan_path.parent]
    repo_plans_dir = Path(__file__).resolve().parents[2] / "docs" / "plans"
    if repo_plans_dir not in directories:
        directories.append(repo_plans_dir)
    return directories


def validate_plan(path: Path) -> list[str]:
    warnings: list[str] = []
    try:
        payload = load_frontmatter(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        warn(path.stem, "frontmatter", str(exc), warnings)
        return warnings

    frontmatter = parse_frontmatter(payload)
    plan_ref = frontmatter.plan_id or path.stem
    valid_roles = load_valid_roles()

    for field in REQUIRED_FIELDS:
        if field not in frontmatter.raw:
            warn(plan_ref, field, "missing required field", warnings)

    # V2 完全移行 (2026-05-24): plan_id format で V1 (legacy) / V2 を判定。
    # V2 製本対象は V2 format のみ。V1 (PLAN-NNN-slug) は legacy 参考扱い → 厳格検証は skip。
    is_reference = bool(frontmatter.raw.get("is_reference"))
    plan_format = _classify_plan_format(frontmatter.plan_id)
    if frontmatter.plan_id is not None and plan_format == "unknown":
        warn(
            plan_ref,
            "plan_id",
            "expected V2 format 'L<NN>-<slug>plan' or V1 legacy 'PLAN-NNN[-slug]'",
            warnings,
        )

    if plan_format == "v1" and not is_reference:
        warn(
            plan_ref,
            "plan_id",
            "V1 (legacy) PLAN must declare is_reference: true (V2 製本対象外、書き直し前提)",
            warnings,
        )

    # V1 legacy reference の扱い (V2 完全移行、2026-05-24):
    #   - V2 専用 field (process_layer / parent_design / pairs_test_design) の検証 skip
    #   - cycle / reciprocal / agent_slots / generates の検証は走らせる (循環参照などは legacy でも検出すべき)
    skip_v2_strict = is_reference and plan_format == "v1"

    if frontmatter.kind is not None and frontmatter.kind not in VALID_KINDS:
        warn(frontmatter.plan_id or plan_ref, "kind", f"unsupported value: {frontmatter.kind}", warnings)

    if frontmatter.layer is not None:
        if frontmatter.layer in MISUSED_WORKFLOW_LAYERS:
            warn(
                plan_ref,
                "layer",
                f"{frontmatter.layer} must be expressed via workflow_phase, not layer",
                warnings,
            )
        elif frontmatter.layer not in VALID_LAYERS:
            warn(plan_ref, "layer", f"unsupported value: {frontmatter.layer}", warnings)

    if frontmatter.drive is not None and frontmatter.drive not in VALID_DRIVES:
        warn(plan_ref, "drive", f"unsupported value: {frontmatter.drive}", warnings)
    elif discovery_compat.is_drive_deprecated(frontmatter.drive):
        replacement = discovery_compat.DEPRECATED_DRIVES[frontmatter.drive]
        warn(
            plan_ref,
            "drive",
            f"DEPRECATED_DRIVES: '{frontmatter.drive}' は将来削除予定 (Stage 4)、drive: {replacement} に移行推奨",
            warnings,
        )

    if frontmatter.workflow_phase is not None:
        if frontmatter.workflow_phase not in VALID_WORKFLOW_PHASES:
            warn(plan_ref, "workflow_phase", f"unsupported value: {frontmatter.workflow_phase}", warnings)
        if frontmatter.kind not in {"poc", "reverse"}:
            warn(
                plan_ref,
                "workflow_phase",
                "workflow_phase is only allowed when kind is poc or reverse",
                warnings,
            )
        if frontmatter.kind in {"poc", "reverse"} and frontmatter.layer != "cross":
            warn(plan_ref, "layer", "kind=poc/reverse should use layer=cross", warnings)

    validate_agent_slots(plan_ref, frontmatter.agent_slots, valid_roles, warnings)
    validate_generates(plan_ref, frontmatter.generates, warnings)
    validate_dependencies(path, frontmatter, warnings)
    if not skip_v2_strict:
        validate_process_layer(path, frontmatter, warnings)

    return warnings


def validate_process_layer(
    path: Path,
    frontmatter: PlanFrontmatter,
    warnings: list[str],
) -> None:
    """新 15 工程 (L0-L14) 規約: kind=impl は process_layer=L7 + parent_design 必須。"""
    plan_ref = frontmatter.plan_id or path.stem
    process_layer = frontmatter.process_layer

    if process_layer is not None and process_layer not in VALID_PROCESS_LAYERS:
        warn(
            plan_ref,
            "process_layer",
            f"unsupported value: {process_layer} (expected one of {sorted(VALID_PROCESS_LAYERS)})",
            warnings,
        )

    if frontmatter.kind == "impl":
        if process_layer is None:
            warn(
                plan_ref,
                "process_layer",
                "kind=impl requires process_layer=L7 (docs/v2/process/L07-implementation-sprint.md)",
                warnings,
            )
        elif process_layer != "L7":
            warn(
                plan_ref,
                "process_layer",
                f"kind=impl must have process_layer=L7 (got {process_layer})",
                warnings,
            )

        if frontmatter.parent_design is None:
            warn(
                plan_ref,
                "parent_design",
                "kind=impl requires parent_design (path to L6 function design doc)",
                warnings,
            )

    if frontmatter.parent_design is not None:
        _validate_path_exists(path, plan_ref, "parent_design", frontmatter.parent_design, warnings)

    pairs = frontmatter.pairs_test_design
    if pairs is not None:
        if not isinstance(pairs, list):
            warn(plan_ref, "pairs_test_design", "expected list[string] (test design doc paths)", warnings)
            return
        for index, pair_path in enumerate(pairs):
            if not isinstance(pair_path, str):
                warn(plan_ref, f"pairs_test_design[{index}]", "expected string", warnings)
                continue
            _validate_path_exists(
                path,
                plan_ref,
                f"pairs_test_design[{index}]",
                pair_path,
                warnings,
            )


def _validate_path_exists(
    plan_path: Path,
    plan_ref: str,
    field: str,
    target_rel: str,
    warnings: list[str],
) -> None:
    """parent_design / pairs_test_design の path が repo root 起点で存在するか確認 (warn-only)."""
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / target_rel
    if not target.exists():
        warn(
            plan_ref,
            field,
            f"path does not exist: {target_rel}",
            warnings,
        )


def validate_agent_slots(
    plan_ref: str,
    agent_slots: Any,
    valid_roles: set[str],
    warnings: list[str],
) -> None:
    if agent_slots is None:
        return
    if not isinstance(agent_slots, list):
        warn(plan_ref, "agent_slots", "expected list", warnings)
        return

    for index, slot in enumerate(agent_slots):
        if not isinstance(slot, dict):
            warn(plan_ref, f"agent_slots[{index}]", "expected mapping", warnings)
            continue
        role = slot.get("role")
        if not isinstance(role, str):
            warn(plan_ref, f"agent_slots[{index}].role", "expected string", warnings)
            continue
        if role not in valid_roles:
            warn(plan_ref, f"agent_slots[{index}].role", f"unsupported value: {role}", warnings)


def validate_generates(plan_ref: str, generates: Any, warnings: list[str]) -> None:
    if generates is None:
        return
    if not isinstance(generates, list):
        warn(plan_ref, "generates", "expected list", warnings)
        return

    for index, item in enumerate(generates):
        if not isinstance(item, dict):
            warn(plan_ref, f"generates[{index}]", "expected mapping", warnings)
            continue
        artifact_type = item.get("artifact_type")
        if not isinstance(artifact_type, str):
            warn(plan_ref, f"generates[{index}].artifact_type", "expected string", warnings)
            continue
        if artifact_type not in VALID_ARTIFACT_TYPES:
            warn(
                plan_ref,
                f"generates[{index}].artifact_type",
                f"unsupported value: {artifact_type}",
                warnings,
            )


def validate_dependencies(path: Path, frontmatter: PlanFrontmatter, warnings: list[str]) -> None:
    plan_ref = frontmatter.plan_id or path.stem
    dependencies = frontmatter.dependencies
    if dependencies is None:
        return
    if not isinstance(dependencies, dict):
        warn(plan_ref, "dependencies", "expected mapping", warnings)
        return

    parent = dependencies.get("parent")
    if parent is not None and not isinstance(parent, str):
        warn(plan_ref, "dependencies.parent", "expected string or null", warnings)

    if not _is_string_list(dependencies.get("requires")):
        warn(plan_ref, "dependencies.requires", "expected list[string]", warnings)
    requires = dependencies.get("requires")
    if isinstance(frontmatter.plan_id, str) and isinstance(requires, list):
        if frontmatter.plan_id in requires:
            warn(plan_ref, "dependencies.requires", "self-edge in requires forbidden", warnings)

    blocks = dependencies.get("blocks")
    if not _is_string_list(blocks):
        warn(plan_ref, "dependencies.blocks", "expected list[string]", warnings)
        blocks = None

    if isinstance(frontmatter.plan_id, str):
        if isinstance(blocks, list):
            _validate_reciprocal_blocks(path, frontmatter.plan_id, blocks, warnings)

        cycle = detect_dependency_cycle(path, frontmatter.plan_id)
        if cycle:
            warn(plan_ref, "dependencies", f"cycle detected: {' -> '.join(cycle)}", warnings)


def _validate_reciprocal_blocks(
    path: Path,
    plan_id: str,
    blocks: list[str],
    warnings: list[str],
) -> None:
    for blocked_plan_id in blocks:
        if blocked_plan_id == plan_id:
            warn(plan_id, "dependencies.blocks", "self-edge in blocks forbidden", warnings)
            continue

        blocked_plan_file = locate_plan_file(path, blocked_plan_id)
        if blocked_plan_file is None:
            warn(
                plan_id,
                "dependencies.blocks",
                f"{blocked_plan_id} does not exist (referenced in blocks)",
                warnings,
            )
            continue
        try:
            blocked_payload = load_frontmatter(blocked_plan_file)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            warn(
                plan_id,
                "dependencies.blocks",
                f"{blocked_plan_id} could not be read: {exc}",
                warnings,
            )
            continue

        blocked_dependencies = blocked_payload.get("dependencies")
        blocked_requires = None
        if isinstance(blocked_dependencies, dict):
            blocked_requires = blocked_dependencies.get("requires")
        if not _is_string_list(blocked_requires):
            warn(
                plan_id,
                "dependencies.blocks",
                f"{blocked_plan_id} is missing requires list for reciprocal dependency check",
                warnings,
            )
            continue
        if plan_id not in blocked_requires:
            warn(
                plan_id,
                "dependencies.blocks",
                f"{blocked_plan_id} does not require {plan_id}",
                warnings,
            )


def detect_dependency_cycle(path: Path, plan_id: str) -> list[str] | None:
    adjacency = _build_dependency_graph(path, plan_id)
    if plan_id not in adjacency:
        return None

    visited: set[str] = set()
    recursion_stack: set[str] = set()
    traversal_path: list[str] = []

    def dfs(node: str) -> list[str] | None:
        visited.add(node)
        recursion_stack.add(node)
        traversal_path.append(node)

        for dependency in adjacency.get(node, []):
            if dependency in recursion_stack:
                cycle_start = traversal_path.index(dependency)
                return traversal_path[cycle_start:] + [dependency]
            if dependency in visited:
                continue
            cycle = dfs(dependency)
            if cycle:
                return cycle

        recursion_stack.remove(node)
        traversal_path.pop()
        return None

    return dfs(plan_id)


def _build_dependency_graph(path: Path, root_plan_id: str) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}
    visited_paths: set[Path] = set()

    def visit(plan_file: Path, current_plan_id: str) -> None:
        resolved = plan_file.resolve()
        if resolved in visited_paths:
            return
        visited_paths.add(resolved)

        try:
            payload = load_frontmatter(plan_file)
        except (OSError, ValueError, yaml.YAMLError):
            adjacency.setdefault(current_plan_id, [])
            return

        frontmatter = parse_frontmatter(payload)
        node_id = frontmatter.plan_id or current_plan_id
        edges = [edge for edge in _dependency_edges(frontmatter) if edge != node_id]
        adjacency[node_id] = edges

        for dependency in edges:
            if dependency == node_id:
                continue
            adjacency.setdefault(dependency, [])
            dependency_path = locate_plan_file(plan_file, dependency)
            if dependency_path is not None:
                visit(dependency_path, dependency)

    root_path = path.resolve()
    visit(root_path, root_plan_id)
    return adjacency


def _dependency_edges(frontmatter: PlanFrontmatter) -> list[str]:
    if not isinstance(frontmatter.dependencies, dict):
        return []

    edges: list[str] = []
    parent = frontmatter.dependencies.get("parent")
    if isinstance(parent, str):
        edges.append(parent)

    requires = frontmatter.dependencies.get("requires")
    if _is_string_list(requires):
        edges.extend(requires)

    # Preserve declaration order while removing duplicates.
    return list(dict.fromkeys(edges))


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    warnings = validate_plan(Path(args.plan_file))
    for line in warnings:
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
