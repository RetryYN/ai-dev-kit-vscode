import datetime
import json
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from handover import check_handover_staleness


def test_check_handover_staleness_fresh(tmp_path: Path) -> None:
    """DoD 検証: L7-handover-stale-checkplan fresh 判定"""
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir(parents=True)
    now = datetime.datetime.now().astimezone().replace(microsecond=0)
    (handover_dir / "CURRENT.json").write_text(
        json.dumps({"updated_at": now.isoformat()}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = check_handover_staleness(project_root=tmp_path)

    assert result["status"] == "fresh"
    assert result["updated_at"] == now.isoformat()
    assert result["hours_since_update"] is not None
    assert result["hours_since_update"] >= 0


def test_check_handover_staleness_stale(tmp_path: Path) -> None:
    """DoD 検証: L7-handover-stale-checkplan stale 判定"""
    handover_dir = tmp_path / ".helix" / "handover"
    handover_dir.mkdir(parents=True)
    stale_time = datetime.datetime.now().astimezone().replace(microsecond=0) - datetime.timedelta(days=10)
    (handover_dir / "CURRENT.json").write_text(
        json.dumps({"updated_at": stale_time.isoformat()}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    result = check_handover_staleness(project_root=tmp_path)

    assert result["status"] == "stale"
    assert result["updated_at"] == stale_time.isoformat()
    assert result["hours_since_update"] is not None
    assert result["hours_since_update"] > 24


def test_check_handover_staleness_no_handover(tmp_path: Path) -> None:
    """DoD 検証: L7-handover-stale-checkplan no_handover 判定"""
    result = check_handover_staleness(project_root=tmp_path)

    assert result == {
        "status": "no_handover",
        "updated_at": None,
        "hours_since_update": None,
    }
