"""契約: PLAN-098 §5 §6 §9.

recovery kind PLAN のテンプレート必須 section、session 終了前チェック、
freshness 判定を行う軽量 helper。
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TEMPLATE_SECTIONS: tuple[str, ...] = (
    "事故記録",
    "timeline",
    "訂正履歴",
    "中間結論",
    "context 再構築",
    "再開ポイント",
    "再発防止",
)

_SECTION_MARKERS: dict[str, tuple[str, ...]] = {
    "事故記録": ("事故記録",),
    "timeline": ("timeline", "タイムライン"),
    "訂正履歴": ("認識訂正履歴", "訂正履歴"),
    "中間結論": ("中間結論",),
    "context 再構築": ("context 再構築", "context reconstruction"),
    "再開ポイント": ("再開ポイント", "resume point"),
    "再発防止": ("再発防止", "recurrence prevention"),
}


def check_recovery_template_sections(filepath: str | Path) -> list[str]:
    """recovery template に不足している必須 section 名を返す。"""
    headings = _load_markdown_headings(Path(filepath))
    missing_sections: list[str] = []

    for section_name in REQUIRED_TEMPLATE_SECTIONS:
        markers = _SECTION_MARKERS[section_name]
        if not any(any(marker in heading for marker in markers) for heading in headings):
            missing_sections.append(section_name)
    return missing_sections


def check_session_exit_4items(
    carry_count: int,
    recovery_plan_exists: bool,
    handover_updated: bool,
    memory_updated: bool,
) -> list[str]:
    """session 終了前 4 項目の未充足名を返す。"""
    missing_items: list[str] = []
    if carry_count <= 0:
        missing_items.append("carry_count")
    if not recovery_plan_exists:
        missing_items.append("recovery_plan_exists")
    if not handover_updated:
        missing_items.append("handover_updated")
    if not memory_updated:
        missing_items.append("memory_updated")
    return missing_items


def check_recovery_plan_freshness(filepath: str | Path, max_age_days: int = 30) -> bool:
    """recovery PLAN が freshness 閾値以内なら True を返す。"""
    plan_path = Path(filepath)
    frontmatter = _load_frontmatter(plan_path)
    revised_date = _extract_revised_date(frontmatter)
    if revised_date is None:
        revised_at = datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC).date()
    else:
        revised_at = revised_date

    today = datetime.now(UTC).date()
    age_days = (today - revised_at).days
    return age_days <= max_age_days


def _load_markdown_headings(path: Path) -> list[str]:
    headings: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            headings.append(stripped.lower())
    return headings


def _load_frontmatter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            payload = yaml.safe_load("\n".join(lines[1:index])) or {}
            return payload if isinstance(payload, dict) else {}
    return {}


def _extract_revised_date(frontmatter: dict[str, Any]) -> date | None:
    revised = frontmatter.get("revised")
    if isinstance(revised, datetime):
        return revised.date()
    if isinstance(revised, date):
        return revised
    if isinstance(revised, str):
        try:
            return date.fromisoformat(revised.strip())
        except ValueError:
            return None
    return None
