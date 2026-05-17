"""U-CORR unit tests for cli/lib/correlation_context.py.

設計参照:
- docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md §4
- docs/v2/L4-test-design/PLAN-084-unit-test-design.md §5 (U-CORR-001〜005)

DoD 検証: U-CORR-001〜005
"""

from __future__ import annotations

import queue
import re
import threading

from cli.lib.correlation_context import (
    correlation_context,
    current_correlation_id,
    get_current_correlation_id,
)

UUID_V7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


# @helix:index id=plan084.u-corr.tests domain=cli/lib/tests summary=PLAN-084 correlation_context unit tests
class TestCorrelationContext:
    def test_u_corr_001_issues_new_correlation_id(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-CORR-001 (parent=None で新規発行する)"""
        assert current_correlation_id() is None
        assert get_current_correlation_id() is None

        with correlation_context() as correlation_id:
            assert UUID_V7_PATTERN.fullmatch(correlation_id)
            assert current_correlation_id() == correlation_id
            assert get_current_correlation_id() == correlation_id

        assert current_correlation_id() is None
        assert get_current_correlation_id() is None

    def test_u_corr_002_inherits_parent_correlation_id(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-CORR-002 (parent を渡すと継承する)"""
        parent_id = "018f4a1b-9e1c-7000-a000-0123456789ab"

        with correlation_context(parent=parent_id) as child_id:
            assert child_id == parent_id
            assert current_correlation_id() == parent_id

        assert current_correlation_id() is None

    def test_u_corr_003_same_thread_can_inherit_and_other_thread_is_isolated(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-CORR-003 (同 thread 継承 / 別 thread 独立)"""
        results: queue.Queue[tuple[str | None, str, str | None]] = queue.Queue()

        with correlation_context() as main_correlation_id:
            with correlation_context(parent=main_correlation_id) as inherited_correlation_id:
                assert inherited_correlation_id == main_correlation_id
                assert current_correlation_id() == main_correlation_id

            def worker() -> None:
                before = current_correlation_id()
                with correlation_context() as other_correlation_id:
                    inside = current_correlation_id()
                    results.put((before, other_correlation_id, inside))
                results.put((current_correlation_id(), "", None))

            thread = threading.Thread(target=worker, name="u-corr-worker")
            thread.start()
            thread.join()

            before, other_correlation_id, inside = results.get_nowait()
            after, _, post_inside = results.get_nowait()

            assert before is None
            assert other_correlation_id != main_correlation_id
            assert inside == other_correlation_id
            assert after is None
            assert post_inside is None
            assert current_correlation_id() == main_correlation_id

        assert current_correlation_id() is None

    def test_u_corr_004_cross_db_trace_inherits_outer_context(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-CORR-004 (orchestration 発行 -> vmodel 継承)"""
        assert current_correlation_id() is None

        with correlation_context() as orchestration_correlation_id:
            assert current_correlation_id() == orchestration_correlation_id

            with correlation_context(parent=orchestration_correlation_id) as vmodel_correlation_id:
                assert vmodel_correlation_id == orchestration_correlation_id
                assert current_correlation_id() == orchestration_correlation_id

            assert current_correlation_id() == orchestration_correlation_id

        assert current_correlation_id() is None

    def test_u_corr_005_current_format_is_36_char_uuid_v7(self) -> None:
        """DoD 検証: PLAN-084-unit-test-design.md U-CORR-005 (現状は 36 字 UUID v7 を返す)"""
        with correlation_context() as correlation_id:
            assert len(correlation_id) == 36
            assert UUID_V7_PATTERN.fullmatch(correlation_id)
