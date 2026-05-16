"""PLAN-082 Phase 2 単体テスト: agent_mandatory.

契約: helix/HELIX_CORE.md §工程別 subagent 起動マップ (PLAN-076 framework)
"""

import os
import sqlite3
from pathlib import Path

import pytest

from cli.lib import agent_mandatory, helix_db


@pytest.fixture
def fresh_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "test_helix.db"
    monkeypatch.setenv("HELIX_DB_PATH", str(db_path))
    conn = sqlite3.connect(str(db_path))
    try:
        helix_db.migrate_all(conn)
    finally:
        conn.close()
    return db_path


class TestListMandatoryForPhase:
    def test_known_phase_g0_5_returns_3_pdm(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("G0.5")
        assert len(result) == 3
        names = {r["subagent"] for r in result}
        assert names == {"pdm-tech-innovation", "pdm-marketing-innovation", "pdm-innovation-manager"}

    def test_known_phase_l2_returns_4_pmo(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("L2")
        assert len(result) == 4
        names = {r["subagent"] for r in result}
        assert "pmo-tech-fork" in names
        assert "pmo-helix-explorer" in names

    def test_known_phase_l3_returns_2(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("L3")
        assert len(result) == 2
        names = {r["subagent"] for r in result}
        assert names == {"pmo-project-explorer", "pmo-helix-explorer"}

    def test_known_phase_l4_returns_2(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("L4")
        assert len(result) == 2

    def test_g2_returns_pmo_sonnet(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("G2")
        assert len(result) == 1
        assert result[0]["subagent"] == "pmo-sonnet"

    def test_g4_returns_pmo_sonnet(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("G4")
        assert result[0]["subagent"] == "pmo-sonnet"

    def test_l8_returns_pmo_sonnet(self) -> None:
        result = agent_mandatory.list_mandatory_for_phase("L8")
        assert result[0]["subagent"] == "pmo-sonnet"

    def test_unknown_phase_returns_empty(self) -> None:
        assert agent_mandatory.list_mandatory_for_phase("L99") == []
        assert agent_mandatory.list_mandatory_for_phase("") == []


class TestSuggestForTask:
    def test_web_keyword_matches_pmo_haiku(self) -> None:
        result = agent_mandatory.suggest_for_task("Web 検索したい")
        assert len(result) >= 1
        assert result[0]["subagent"] == "pmo-haiku"

    def test_news_keyword_matches_tech_news(self) -> None:
        result = agent_mandatory.suggest_for_task("最新動向を教えて")
        names = [r["subagent"] for r in result]
        assert "pmo-tech-news" in names

    def test_pm_keyword_matches_pm_advisor(self) -> None:
        result = agent_mandatory.suggest_for_task("PM判断 スコープ 優先度")
        names = [r["subagent"] for r in result]
        assert "pm-advisor" in names

    def test_tl_keyword_matches_tl_advisor(self) -> None:
        result = agent_mandatory.suggest_for_task("契約と設計の判断が必要")
        names = [r["subagent"] for r in result]
        assert "tl-advisor" in names

    def test_no_match_returns_empty(self) -> None:
        result = agent_mandatory.suggest_for_task("zzz_no_match_xxx")
        assert result == []

    def test_empty_task_returns_empty(self) -> None:
        assert agent_mandatory.suggest_for_task("") == []

    def test_confidence_sorted_desc(self) -> None:
        result = agent_mandatory.suggest_for_task("PM判断 スコープ 優先度 advisor")
        for i in range(len(result) - 1):
            assert result[i]["confidence"] >= result[i + 1]["confidence"]


class TestAuditPhase:
    @staticmethod
    def _insert_subagent_call(db_path: Path, subagent_type: str, session_id: str) -> None:
        conn = sqlite3.connect(str(db_path))
        try:
            conn.execute(
                "INSERT INTO agent_slots (slot_key, agent_kind, subagent_type, session_id) "
                "VALUES (?, ?, ?, ?)",
                (f"{session_id}:{subagent_type}", "claude_subagent", subagent_type, session_id),
            )
            conn.commit()
        finally:
            conn.close()

    def test_empty_db_all_missing(self, fresh_db: Path) -> None:
        result = agent_mandatory.audit_phase("L2")
        assert result["phase"] == "L2"
        assert result["missing_count"] == 4
        assert result["warning"] is True
        assert all(r["called"] is False for r in result["mandatory"])

    def test_unknown_phase_returns_empty_audit(self, fresh_db: Path) -> None:
        result = agent_mandatory.audit_phase("L99")
        assert result["missing_count"] == 0
        assert result["warning"] is False
        assert result["mandatory"] == []

    def test_one_subagent_called_reduces_missing(self, fresh_db: Path) -> None:
        # agent_slots に pmo-helix-explorer を挿入
        conn = sqlite3.connect(str(fresh_db))
        try:
            conn.execute(
                "INSERT INTO agent_slots (slot_key, agent_kind, subagent_type) "
                "VALUES (?, ?, ?)",
                ("subagent:pmo-helix-explorer", "claude_subagent", "pmo-helix-explorer"),
            )
            conn.commit()
        finally:
            conn.close()

        result = agent_mandatory.audit_phase("L2")
        # L2 mandatory 4 種 - 1 called = 3 missing
        assert result["missing_count"] == 3
        called_subs = [r["subagent"] for r in result["mandatory"] if r["called"]]
        assert "pmo-helix-explorer" in called_subs

    def test_audit_with_session_id_filters_by_session(self, fresh_db: Path) -> None:
        self._insert_subagent_call(fresh_db, "pmo-tech-fork", "session-A")
        self._insert_subagent_call(fresh_db, "pmo-helix-explorer", "session-B")

        result = agent_mandatory.audit_phase("L2", session_id="session-A")

        assert result["missing_count"] == 3
        called_subs = [r["subagent"] for r in result["mandatory"] if r["called"]]
        assert called_subs == ["pmo-tech-fork"]

    def test_audit_without_session_id_returns_all_sessions(self, fresh_db: Path) -> None:
        self._insert_subagent_call(fresh_db, "pmo-tech-fork", "session-A")
        self._insert_subagent_call(fresh_db, "pmo-helix-explorer", "session-B")

        result = agent_mandatory.audit_phase("L2")

        assert result["missing_count"] == 2
        called_subs = {r["subagent"] for r in result["mandatory"] if r["called"]}
        assert called_subs == {"pmo-tech-fork", "pmo-helix-explorer"}

    def test_audit_with_unknown_session_returns_all_missing(self, fresh_db: Path) -> None:
        self._insert_subagent_call(fresh_db, "pmo-tech-fork", "session-A")

        result = agent_mandatory.audit_phase("L2", session_id="session-Z")

        assert result["missing_count"] == 4
        assert all(r["called"] is False for r in result["mandatory"])


class TestFireMandatoryAudit:
    def test_dry_run_returns_audit_action(self) -> None:
        result = agent_mandatory.fire_mandatory_audit("L2", dry_run=True)
        assert result["action"] == "audit"
        assert len(result["subagents"]) == 4

    def test_list_action_without_dry_run(self) -> None:
        result = agent_mandatory.fire_mandatory_audit("L2", dry_run=False)
        assert result["action"] == "list"

    def test_unknown_phase_noop(self) -> None:
        result = agent_mandatory.fire_mandatory_audit("L99")
        assert result["action"] == "noop"
        assert result["subagents"] == []
