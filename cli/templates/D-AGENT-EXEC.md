# D-AGENT-EXEC

> 大規模 agent の実行層設計テンプレート。tool / prompt / decision tree / failure handling を固定する。

## 1. Scope
- 対象 feature / plan_id:
- 対象 agent / role:
- 非対象:

## 2. Tool Definitions
- tool catalog:
- input schema:
- output schema:
- permission boundary:
- external dependency:

## 3. Prompt Templates
- system prompt:
- user prompt variables:
- few-shot / examples:
- guardrails:
- prompt versioning:

## 4. Decision Tree
- entry conditions:
- branching rules:
- tool selection policy:
- stop / handoff 条件:
- confidence / uncertainty handling:

## 5. Failure Handling
- recoverable failure:
- non-recoverable failure:
- retry / fallback strategy:
- operator escalation:
- user-facing error response:

## 6. Evaluation Criteria
- success metrics:
- quality rubric:
- latency / cost budget:
- regression scenarios:
- acceptance evidence:

## 7. Interfaces
- インフラ層から受け取る context:
- インフラ層へ返す status:
- output validation:

## 8. Verification
- unit / tool tests:
- orchestration integration:
- conversation scenarios:
- adversarial / abuse cases:
