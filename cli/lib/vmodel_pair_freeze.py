from __future__ import annotations

import json
import re
import subprocess
import tempfile
from difflib import unified_diff
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from .paths import project_root as resolve_project_root


VMODEL_PAIRS = {
    "L1": "L14",
    "L2": "L10",
    "L3": "L12",
    "L4": "L9",
    "L5": "L8",
    "L6": "L7",
    "L7": "L6",
    "L8": "L5",
    "L9": "L4",
    "L10": "L2",
    "L12": "L3",
    "L14": "L1",
}

CRITICAL_LAYERS = {"L1", "L3", "L4", "L6"}
WARNING_LAYERS = {"L2", "L5"}
INFO_LAYERS = {"L7", "L8", "L9", "L10", "L12", "L14"}
STATUS_BREAKDOWN_KEYS = ("draft", "in_progress", "completed", "superseded", "other")


def get_pair(layer: str) -> str | None:
    """L1-L14 のうち pair を返す。L0/L11/L13 は None。"""
    return VMODEL_PAIRS.get(layer)


def get_severity(layer: str) -> str | None:
    """Return configured severity for a paired layer."""
    if layer in CRITICAL_LAYERS:
        return "critical"
    if layer in WARNING_LAYERS:
        return "warning"
    if layer in INFO_LAYERS:
        return "info"
    return None


def _load_plan_frontmatter(plan_path: Path) -> dict[str, Any]:
    """Return YAML frontmatter when present."""
    try:
        lines = plan_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    if not lines or lines[0].strip() != "---":
        return {}

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}

    try:
        loaded = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError:
        return {}

    if not isinstance(loaded, dict):
        return {}
    return loaded


def _load_plan_status(plan_path: Path) -> str | None:
    """Return plan status from YAML frontmatter when present."""
    status = _load_plan_frontmatter(plan_path).get("status")
    return status if isinstance(status, str) else None


def _filter_active_plans(plan_paths: list[Path]) -> list[Path]:
    active_statuses = {"draft", "in_progress"}
    return [plan_path for plan_path in plan_paths if _load_plan_status(plan_path) in active_statuses]


def _coerce_frontmatter_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    match = re.match(r"^\s*(\d{4}-\d{2}-\d{2})", value)
    if not match:
        return None

    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def _resolve_plan_date(plan_path: Path) -> date | None:
    frontmatter = _load_plan_frontmatter(plan_path)
    for field_name in ("revised", "created"):
        resolved = _coerce_frontmatter_date(frontmatter.get(field_name))
        if resolved is not None:
            return resolved

    try:
        return datetime.fromtimestamp(plan_path.stat().st_mtime).date()
    except OSError:
        return None


def _stringify_frontmatter_date(value: Any) -> str | None:
    resolved = _coerce_frontmatter_date(value)
    return resolved.isoformat() if resolved is not None else None


def _audit_file_path(project_root: Path) -> Path:
    return project_root / ".helix" / "audit" / "stale-revisions.json"


def _rewrite_frontmatter_revised_text(content: str, new_revised: str | None) -> str:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter missing")

    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise ValueError("frontmatter unterminated")

    revised_pattern = re.compile(r"^(\s*revised\s*:\s*).*$")
    for index in range(1, end_index):
        match = revised_pattern.match(lines[index])
        if match:
            if new_revised is None:
                del lines[index]
            else:
                lines[index] = f"{match.group(1)}{new_revised}\n"
            break
    else:
        if new_revised is not None:
            lines.insert(end_index, f"revised: {new_revised}\n")

    return "".join(lines)


def _rewrite_frontmatter_revised(plan_path: Path, new_revised: str | None) -> None:
    content = plan_path.read_text(encoding="utf-8")
    plan_path.write_text(_rewrite_frontmatter_revised_text(content, new_revised), encoding="utf-8")


def _load_audit_records(audit_path: Path) -> list[dict[str, Any]]:
    try:
        loaded = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(loaded, list):
        return []
    return [record for record in loaded if isinstance(record, dict)]


def _write_audit_records(audit_path: Path, records: list[dict[str, Any]]) -> None:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_audit_record(project_root: Path, record: dict[str, Any]) -> None:
    audit_path = _audit_file_path(project_root)
    records = _load_audit_records(audit_path)
    records.append(record)
    _write_audit_records(audit_path, records)


def _resolve_pair_plan_paths(layer: str, project_root: Path | None = None) -> tuple[str | None, list[Path]]:
    pair = get_pair(layer)
    if pair is None:
        return None, []

    root = Path(project_root) if project_root is not None else resolve_project_root()
    pair_dir = root / "docs" / "plans" / pair
    if not pair_dir.is_dir():
        return pair, []

    return pair, sorted(pair_dir.glob(f"{pair}-*plan.md"))


def _filter_recent_plans(plan_paths: list[Path], since_days: int) -> list[Path]:
    cutoff = date.today() - timedelta(days=since_days)
    filtered: list[Path] = []
    for plan_path in plan_paths:
        resolved = _resolve_plan_date(plan_path)
        if resolved is not None and resolved >= cutoff:
            filtered.append(plan_path)
    return filtered


def _count_stale_plans(plan_paths: list[Path], since_days: int) -> int:
    cutoff = date.today() - timedelta(days=since_days)
    stale_count = 0
    for plan_path in plan_paths:
        resolved = _resolve_plan_date(plan_path)
        if resolved is not None and resolved < cutoff:
            stale_count += 1
    return stale_count


def _empty_status_breakdown() -> dict[str, int]:
    return {key: 0 for key in STATUS_BREAKDOWN_KEYS}


def _normalize_plan_status(status: str | None) -> str:
    if status in STATUS_BREAKDOWN_KEYS[:-1]:
        return status
    return "other"


def _build_status_breakdown(plan_paths: list[Path]) -> dict[str, int]:
    breakdown = _empty_status_breakdown()
    for plan_path in plan_paths:
        breakdown[_normalize_plan_status(_load_plan_status(plan_path))] += 1
    return breakdown


def suggest_stale_revisions(
    layer: str,
    *,
    project_root: Path,
    since_days: int = 30,
) -> list[dict[str, str | None]]:
    """Return dry-run revised date suggestions for stale pair plans."""
    pair, plan_paths = _resolve_pair_plan_paths(layer, project_root)
    if pair is None or not plan_paths:
        return []

    cutoff = date.today() - timedelta(days=since_days)
    suggested_revised = date.today().isoformat()
    suggestions: list[dict[str, str | None]] = []
    for plan_path in plan_paths:
        resolved = _resolve_plan_date(plan_path)
        if resolved is None or resolved >= cutoff:
            continue

        frontmatter = _load_plan_frontmatter(plan_path)
        plan_id = frontmatter.get("plan_id")
        suggestions.append(
            {
                "plan_id": plan_id if isinstance(plan_id, str) and plan_id else plan_path.stem,
                "plan_path": str(plan_path),
                "current_revised": _stringify_frontmatter_date(frontmatter.get("revised")),
                "suggested_revised": suggested_revised,
            }
        )
    return suggestions


def generate_stale_patch(
    layer: str,
    *,
    project_root: Path,
    since_days: int = 30,
) -> list[dict[str, str | None]]:
    """Return unified diff patches for stale revised frontmatter updates."""
    suggestions = suggest_stale_revisions(layer, project_root=project_root, since_days=since_days)
    patches: list[dict[str, str | None]] = []

    for suggestion in suggestions:
        plan_path = suggestion.get("plan_path")
        plan_id = suggestion.get("plan_id")
        after_revised = suggestion.get("suggested_revised")
        if not isinstance(plan_path, str) or not isinstance(plan_id, str) or not isinstance(after_revised, str):
            continue

        path = Path(plan_path)
        try:
            before_content = path.read_text(encoding="utf-8")
            after_content = _rewrite_frontmatter_revised_text(before_content, after_revised)
        except (OSError, ValueError):
            continue

        diff = "\n".join(
            unified_diff(
                before_content.splitlines(),
                after_content.splitlines(),
                fromfile=plan_path,
                tofile=plan_path,
                lineterm="",
            )
        )
        patches.append(
            {
                "plan_id": plan_id,
                "plan_path": plan_path,
                "unified_diff": diff,
                "before_revised": suggestion.get("current_revised"),
                "after_revised": after_revised,
            }
        )

    return patches


def apply_stale_patches(
    layer: str,
    *,
    project_root: Path,
    since_days: int = 30,
    dry_run: bool = True,
) -> dict[str, str | list[Any]]:
    """Return dry-run patch previews or apply generated stale patches with git apply."""
    patches = generate_stale_patch(layer, project_root=project_root, since_days=since_days)
    if not patches:
        return {"status": "no_patches", "patches": [], "errors": []}
    if dry_run:
        return {"status": "dry_run", "patches": patches, "errors": []}

    errors: list[str] = []
    for patch in patches:
        unified_diff_text = patch.get("unified_diff")
        plan_path = patch.get("plan_path")
        if not isinstance(unified_diff_text, str) or not isinstance(plan_path, str):
            errors.append(f"invalid patch payload: {patch!r}")
            continue

        tmp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".patch",
                delete=False,
                dir=project_root,
            ) as tmp_file:
                tmp_file.write(unified_diff_text + "\n")
                tmp_name = tmp_file.name

            completed = subprocess.run(
                ["git", "apply", "--unidiff-zero", "--allow-empty", tmp_name],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip() or f"git apply failed for {plan_path}"
                errors.append(f"{plan_path}: {detail}")
        except OSError as exc:
            errors.append(f"{plan_path}: {exc}")
        finally:
            if tmp_name is not None:
                try:
                    Path(tmp_name).unlink()
                except OSError:
                    pass

    return {
        "status": "failed" if errors else "applied",
        "patches": patches,
        "errors": errors,
    }


def apply_stale_revisions(
    layer: str,
    *,
    project_root: Path,
    since_days: int = 30,
    dry_run: bool = True,
) -> list[dict[str, str]]:
    """Apply or preview revised date updates for stale pair plans."""
    suggestions = suggest_stale_revisions(layer, project_root=project_root, since_days=since_days)
    new_revised = date.today().isoformat()
    results: list[dict[str, str]] = []
    audit_changes: list[dict[str, str | None]] = []

    for suggestion in suggestions:
        plan_path = suggestion.get("plan_path")
        plan_id = suggestion.get("plan_id")
        if not isinstance(plan_path, str) or not isinstance(plan_id, str):
            continue

        result = {
            "plan_id": plan_id,
            "plan_path": plan_path,
            "status": "dry_run" if dry_run else "updated",
            "new_revised": new_revised,
        }
        if dry_run:
            results.append(result)
            continue

        try:
            _rewrite_frontmatter_revised(Path(plan_path), new_revised)
            audit_changes.append(
                {
                    "plan_path": plan_path,
                    "before_revised": suggestion.get("current_revised"),
                    "after_revised": new_revised,
                }
            )
        except (OSError, ValueError) as exc:
            result["status"] = "skipped"
            result["reason"] = str(exc)
        results.append(result)

    if not dry_run and audit_changes:
        _append_audit_record(
            project_root,
            {
                "applied_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "layer": layer,
                "changes": audit_changes,
            },
        )

    return results


def rollback_stale_revisions(
    *,
    project_root: Path,
    dry_run: bool = True,
) -> dict[str, str | list[dict[str, str | None]]]:
    """Preview or rollback stale revised updates from the latest audit record."""
    audit_path = _audit_file_path(project_root)
    if not audit_path.is_file():
        return {"status": "no_audit", "rolled_back": []}

    records = _load_audit_records(audit_path)
    if not records:
        return {"status": "no_audit", "rolled_back": []}

    latest_record = records[-1]
    changes = latest_record.get("changes")
    if not isinstance(changes, list):
        return {"status": "no_audit", "rolled_back": []}

    rolled_back: list[dict[str, str | None]] = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        plan_path = change.get("plan_path")
        restored_revised = change.get("before_revised")
        if not isinstance(plan_path, str):
            continue
        if restored_revised is not None and not isinstance(restored_revised, str):
            continue

        if not dry_run:
            _rewrite_frontmatter_revised(Path(plan_path), restored_revised)
        rolled_back.append({"plan_path": plan_path, "restored_revised": restored_revised})

    return {
        "status": "dry_run" if dry_run else "rolled_back",
        "rolled_back": rolled_back,
    }


def check_pair_freeze(
    layer: str,
    *,
    project_root: Path | None = None,
    active_only: bool = False,
    since_days: int | None = None,
) -> dict[str, Any]:
    """Return V-model pair freeze status for one layer."""
    pair = get_pair(layer)
    severity = get_severity(layer)
    if pair is None:
        return {
            "layer": layer,
            "pair": None,
            "severity": severity,
            "active_only": active_only,
            "since_days": since_days,
            "stale_count": 0,
            "status_breakdown": {},
            "pair_doc_exists": False,
            "pair_doc_path": None,
            "status": "no_pair",
            "hint": None,
        }

    _, matches = _resolve_pair_plan_paths(layer, project_root)
    pattern = f"{pair}-*plan.md"
    if active_only:
        matches = _filter_active_plans(matches)
    stale_count = 0
    if since_days is not None:
        stale_count = _count_stale_plans(matches, since_days)
        matches = _filter_recent_plans(matches, since_days)
    status_breakdown = _build_status_breakdown(matches)
    pair_doc = matches[0] if matches else None

    if pair_doc is not None:
        return {
            "layer": layer,
            "pair": pair,
            "severity": severity,
            "active_only": active_only,
            "since_days": since_days,
            "stale_count": stale_count,
            "status_breakdown": status_breakdown,
            "pair_doc_exists": True,
            "pair_doc_path": str(pair_doc),
            "status": "ok",
            "hint": None,
        }

    return {
        "layer": layer,
        "pair": pair,
        "severity": severity,
        "active_only": active_only,
        "since_days": since_days,
        "stale_count": stale_count,
        "status_breakdown": status_breakdown,
        "pair_doc_exists": False,
        "pair_doc_path": None,
        "status": "pair_missing",
        "hint": f"Create pair plan under docs/plans/{pair}/ matching {pattern}",
    }
