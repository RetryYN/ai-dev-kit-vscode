"""PLAN-098 recovery_plan_check 単体テスト.

契約: docs/plans/PLAN-098-recovery-plan-kind-normalization.md §5 §6 §8 §11
DoD 検証: PLAN-098 §11.1-§11.2
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import recovery_plan_check


def _write_recovery_plan(path: Path, *, headings: list[str], revised: str | None = "2026-05-20") -> None:
    frontmatter = ["---"]
    if revised is not None:
        frontmatter.append(f"revised: {revised}")
    frontmatter.append("kind: recovery")
    frontmatter.append("---")
    body = [f"## {heading}\ncontent" for heading in headings]
    path.write_text("\n".join(frontmatter + [""] + body) + "\n", encoding="utf-8")


def test_template_all_sections_present(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.1 (7 必須 section 完備で欠損なし)"""
    plan_path = tmp_path / "recovery.md"
    _write_recovery_plan(
        plan_path,
        headings=[
            "§1. 事故記録 (Incident Record)",
            "§2. 議論順序 timeline (Discussion Timeline)",
            "§3. 認識訂正履歴 (Recognition Correction History)",
            "§4. 中間結論 list (Intermediate Conclusions)",
            "§5. context 再構築チェックリスト (Context Reconstruction Checklist)",
            "§6. 再開ポイント (Resume Point)",
            "§7. 再発防止策 (Recurrence Prevention)",
        ],
    )

    assert recovery_plan_check.check_recovery_template_sections(plan_path) == []


def test_template_missing_sections(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.1 (欠損 section 名だけを返す)"""
    plan_path = tmp_path / "recovery.md"
    _write_recovery_plan(
        plan_path,
        headings=[
            "§1. 事故記録 (Incident Record)",
            "§2. 議論順序 timeline (Discussion Timeline)",
            "§4. 中間結論 list (Intermediate Conclusions)",
            "§6. 再開ポイント (Resume Point)",
        ],
    )

    assert recovery_plan_check.check_recovery_template_sections(plan_path) == [
        "訂正履歴",
        "context 再構築",
        "再発防止",
    ]


def test_session_exit_all_satisfied() -> None:
    """DoD 検証: PLAN-098 §6 (4 項目がすべて満たされれば空 list)"""
    assert recovery_plan_check.check_session_exit_4items(1, True, True, True) == []


def test_session_exit_partial() -> None:
    """DoD 検証: PLAN-098 §6 (未充足の項目名だけを返す)"""
    assert recovery_plan_check.check_session_exit_4items(1, False, True, True) == [
        "recovery_plan_exists"
    ]


def test_freshness_within_threshold(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.2 (30 日以内なら True)"""
    plan_path = tmp_path / "recent-recovery.md"
    revised = (datetime.now(UTC) - timedelta(days=10)).date().isoformat()
    _write_recovery_plan(plan_path, headings=["§1. 事故記録"], revised=revised)

    assert recovery_plan_check.check_recovery_plan_freshness(plan_path, max_age_days=30) is True


def test_freshness_stale(tmp_path: Path) -> None:
    """DoD 検証: PLAN-098 §11.2 (frontmatter 不在時は mtime fallback で stale 判定)"""
    plan_path = tmp_path / "stale-recovery.md"
    _write_recovery_plan(plan_path, headings=["§1. 事故記録"], revised=None)
    stale_time = datetime.now(UTC) - timedelta(days=31)
    os.utime(plan_path, (stale_time.timestamp(), stale_time.timestamp()))

    assert recovery_plan_check.check_recovery_plan_freshness(plan_path, max_age_days=30) is False
