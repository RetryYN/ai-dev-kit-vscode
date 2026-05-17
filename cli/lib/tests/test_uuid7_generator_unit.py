"""U-UUID unit tests for cli/lib/uuid7_generator.py.

設計参照:
- docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md §3
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md §4 (U-UUID-001〜005)

DoD 検証: PLAN-084-unit-test-design.md U-UUID-001〜005
"""

from __future__ import annotations

import re
import sys
import uuid

import pytest

from cli.lib import uuid7_generator

UUID_V7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.fixture(autouse=True)
def reset_uuid7_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(uuid7_generator, "_LAST_TIMESTAMP_MS", 0)
    monkeypatch.setattr(uuid7_generator, "_COUNTER", 0)


# @helix:index id=plan084.u-uuid.tests domain=cli/lib/tests summary=PLAN-084 UUID v7 generator unit tests
class TestUuid7Generator:
    def test_u_uuid_001_returns_36_char_uuid_v7_string(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-UUID-001 (36 文字 UUID 形式を返す)"""
        event_id = uuid7_generator.generate_event_id()

        assert len(event_id) == 36
        assert UUID_V7_PATTERN.fullmatch(event_id)

    def test_u_uuid_002_is_lexicographically_sorted_within_same_millisecond(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-UUID-002 (同一 ms 内でも生成順と sort 順が一致)"""
        monkeypatch.setattr(uuid7_generator, "_timestamp_ms", lambda: 1_700_000_000_000)

        event_ids = [uuid7_generator.generate_event_id() for _ in range(1000)]

        assert event_ids == sorted(event_ids)

    def test_u_uuid_003_has_no_collisions_for_1000_generations(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-UUID-003 (1000 件生成で重複 0)"""
        monkeypatch.setattr(uuid7_generator, "_timestamp_ms", lambda: 1_700_000_000_000)

        event_ids = [uuid7_generator.generate_event_id() for _ in range(1000)]

        assert len(set(event_ids)) == 1000

    @pytest.mark.skipif(
        sys.version_info < (3, 12) or sys.version_info >= (3, 14),
        reason="HELIX-SKIP: env_dependent | PLAN-084 | due_date: 2026-12-31",
    )
    def test_u_uuid_004_uses_fallback_on_python_3_12(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-UUID-004 (Python 3.12 で fallback 経路が動作する)"""
        assert uuid7_generator._HAS_STDLIB_UUID7 is False
        assert UUID_V7_PATTERN.fullmatch(uuid7_generator.generate_event_id())

    @pytest.mark.skipif(
        sys.version_info < (3, 14),
        reason="HELIX-SKIP: env_dependent | PLAN-084 | due_date: 2026-12-31",
    )
    def test_u_uuid_005_can_switch_to_stdlib_uuid7(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-UUID-005 (Python 3.14+ で stdlib uuid7 に切替可能)"""
        expected = "018f4a1b-9e1c-7000-a000-0123456789ab"

        monkeypatch.setattr(uuid7_generator, "_HAS_STDLIB_UUID7", True)
        monkeypatch.setattr(uuid7_generator, "_uuid7_fallback", lambda: pytest.fail("fallback should not be used"))
        monkeypatch.setattr(uuid7_generator.uuid, "uuid7", lambda: uuid.UUID(expected))

        assert uuid7_generator.generate_event_id() == expected
