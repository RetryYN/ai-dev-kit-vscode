# D-AGENT-INFRA

> 大規模 agent のインフラ層設計テンプレート。runtime / state / orchestrator / observability を固定する。

## 1. Scope
- 対象 feature / plan_id:
- 対象 agent 群:
- 非対象:

## 2. Agent Runtime
- 実行形態: single process / worker pool / external runtime
- 実行単位: session / task / tool call
- concurrency / queueing 方針:
- timeout / cancellation 方針:

## 3. State Management
- 永続状態:
- 一時状態:
- state store:
- checkpoint / resume 方針:
- state schema versioning:

## 4. Orchestrator Pattern
- orchestration type: sequential / DAG / supervisor / event-driven
- routing rules:
- handoff 条件:
- retry / fallback の責務境界:
- human escalation 条件:

## 5. Observability
- trace / span 単位:
- logging 方針:
- metrics:
- cost / token tracking:
- audit trail:

## 6. Fault Tolerance
- failure class:
- retry budget:
- degraded mode:
- circuit breaker / backpressure:
- dead-letter / recovery 手順:

## 7. Interfaces
- 実行層への入力契約:
- 実行層からの出力契約:
- security / secret boundary:

## 8. Verification
- smoke:
- load / soak:
- fault injection:
- rollback / recovery:
