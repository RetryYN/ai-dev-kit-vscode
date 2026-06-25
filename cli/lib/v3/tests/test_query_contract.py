from __future__ import annotations

from cli.lib.v3.query.contract import (
    HandlerSpec,
    QueryContract,
    QueryGraphInput,
    analyze_query_graph,
    query_graph_messages,
)


def _contract(qid="q1", handler="h1", req="r1", resp="s1"):
    return QueryContract(query_id=qid, boundary="a->b", request_schema_hash=req, response_schema_hash=resp, handler_id=handler)


def _handler(hid="h1", req="r1", resp="s1"):
    return HandlerSpec(handler_id=hid, request_schema_hash=req, response_schema_hash=resp)


def test_not_applicable_when_no_contracts_or_handlers():
    res = analyze_query_graph(QueryGraphInput(contracts=(), handlers=()))
    assert res.ok is True  # opt-in: pattern 未使用 = ok


def test_matched_contract_handler_is_ok():
    res = analyze_query_graph(QueryGraphInput(contracts=(_contract(),), handlers=(_handler(),)))
    assert res.ok is True


def test_unresolved_query_when_handler_missing():
    res = analyze_query_graph(QueryGraphInput(contracts=(_contract(handler="ghost"),), handlers=(_handler(),)))
    assert res.ok is False
    assert res.unresolved == ("q1",)


def test_contract_drift_on_schema_mismatch():
    res = analyze_query_graph(
        QueryGraphInput(contracts=(_contract(req="r1", resp="s1"),), handlers=(_handler(req="r1", resp="DIFFERENT"),))
    )
    assert res.ok is False
    assert res.drift == ("q1",)


def test_query_without_handler_flags_dead_handler():
    res = analyze_query_graph(QueryGraphInput(contracts=(_contract(handler="h1"),), handlers=(_handler("h1"), _handler("dead"))))
    assert res.ok is False
    assert res.dead_handlers == ("dead",)


def test_messages_are_machine_readable():
    res = analyze_query_graph(QueryGraphInput(contracts=(_contract(handler="ghost"),), handlers=()))
    findings = query_graph_messages(res)
    assert findings and all(f.id and f.subject for f in findings)
