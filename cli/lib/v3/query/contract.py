"""Phase 4 (HELIX 独自強化): 内部 query contract pattern の検出機構。

agent system の unit 境界をまたぐ問い合わせを型付き contract にし、worker≠reviewer/tier-router が
効く境界として扱う(設計正本 = docs/v3/helix-w-design.md §3.5)。本 module は **pure-function** の
3 検査を提供する(unresolved-query / contract-drift / query-without-handler)。

重要(TL 契約): 既存 mcp_server_* table は流用しない。投影は artifact_registry/trace_edges/
review_evidence_registry へ(本 module は schema を持たず、検出ロジックのみ)。query contract が
存在しない repo(= pattern 未使用)では **not-applicable = ok**(opt-in)。
"""

from __future__ import annotations

from dataclasses import dataclass

try:  # Finding は detector framework と共通形式
    from v3.detectors.runner import Finding
except ImportError:  # pragma: no cover
    from cli.lib.v3.detectors.runner import Finding

UNRESOLVED_QUERY = "INTQ-DET-01-unresolved-query"
CONTRACT_DRIFT = "INTQ-DET-02-contract-drift"
QUERY_WITHOUT_HANDLER = "INTQ-DET-03-query-without-handler"
HARD = "hard"


@dataclass(frozen=True)
class QueryContract:
    query_id: str
    boundary: str  # またぐ unit 境界(例 "agentA->toolB")
    request_schema_hash: str
    response_schema_hash: str
    handler_id: str


@dataclass(frozen=True)
class HandlerSpec:
    handler_id: str
    request_schema_hash: str
    response_schema_hash: str


@dataclass(frozen=True)
class QueryGraphInput:
    contracts: tuple[QueryContract, ...]
    handlers: tuple[HandlerSpec, ...]


@dataclass(frozen=True)
class QueryCheckResult:
    ok: bool
    unresolved: tuple[str, ...]  # contract.query_id (handler 解決不能)
    drift: tuple[str, ...]  # contract.query_id (schema mismatch)
    dead_handlers: tuple[str, ...]  # handler_id (対応 contract なし)


def analyze_query_graph(input_data: QueryGraphInput) -> QueryCheckResult:
    """pure: contracts↔handlers の整合を計算。pattern 未使用(両方空)= ok(not-applicable)。"""
    handler_by_id = {handler.handler_id: handler for handler in input_data.handlers}
    referenced_handlers = {contract.handler_id for contract in input_data.contracts}

    unresolved = tuple(
        contract.query_id
        for contract in input_data.contracts
        if contract.handler_id not in handler_by_id
    )
    drift = tuple(
        contract.query_id
        for contract in input_data.contracts
        if contract.handler_id in handler_by_id
        and (
            contract.request_schema_hash != handler_by_id[contract.handler_id].request_schema_hash
            or contract.response_schema_hash != handler_by_id[contract.handler_id].response_schema_hash
        )
    )
    dead_handlers = tuple(
        sorted(handler.handler_id for handler in input_data.handlers if handler.handler_id not in referenced_handlers)
    )
    return QueryCheckResult(
        ok=not unresolved and not drift and not dead_handlers,
        unresolved=unresolved,
        drift=drift,
        dead_handlers=dead_handlers,
    )


def query_graph_messages(result: QueryCheckResult) -> list[Finding]:
    findings: list[Finding] = []
    for query_id in result.unresolved:
        findings.append(Finding(id=UNRESOLVED_QUERY, severity=HARD, subject=query_id, missing=("handler unresolved",)))
    for query_id in result.drift:
        findings.append(Finding(id=CONTRACT_DRIFT, severity=HARD, subject=query_id, missing=("request/response schema mismatch",)))
    for handler_id in result.dead_handlers:
        findings.append(Finding(id=QUERY_WITHOUT_HANDLER, severity=HARD, subject=handler_id, missing=("no query contract references this handler",)))
    return findings
