---
doc_id: D-API-CARRY-draft-v0.1
plan_id: PLAN-071
status: frozen
created: 2026-05-17
source: D-API-draft.md §3.4-§3.14 carry detail
note: >
  D-API-draft.md の §4.4 ±200 行制約（524 行 ±200 = 324-724 行範囲）遵守のため、
  §3.4〜§3.14 の 11 capability 詳細を本ファイルに分離。
  D-API-draft.md §3.4〜§3.14 セクションは本ファイルへの参照リダイレクトに置換済み。
related:
  - docs/v2/L3-detailed-design/D-API/D-API-draft.md (親 doc、§3.1〜§3.3 詳細化済)
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md (§4.6 mock hook 展開表)
  - docs/v2/L2-MASTER.md (§3-§10 capability matrix)
  - docs/plans/PLAN-071-carry-capability-detailing.md
---

# D-API CARRY draft — §3.4〜§3.14 capability endpoint contract（PLAN-071）

本ファイルは `D-API-draft.md` §3.4〜§3.14 の carry capability 11 件（C-01〜C-11）の endpoint contract 詳細を収録する。  
`D-API-draft.md` §3.4〜§3.14 は本ファイルへのリダイレクト参照に置換されている。

---

### 3.4 V-model schema / QA baseline schema（C-01）

#### 3.4.1 GET /api/v1/plan/{plan_id}/vmodel/schema

- path: `/api/v1/plan/{plan_id}/vmodel/schema`
- method: `GET`
- origin_ac: FR-VS01, FR-VS02
- path_schema:
  ```yaml
  type: object
  required: [plan_id]
  properties:
    plan_id:
      type: string
  ```
- query_schema:
  ```yaml
  type: object
  properties:
    include_entries:
      type: boolean
      default: false
    drive:
      type: string
      enum: [be, fe, db, fullstack]
  ```
- header_schema:
  ```yaml
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization:
      type: string
    Content-Type:
      type: string
      enum: [application/json]
    X-Trace-Id:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `$ref: '#/components/schemas/Envelope'`
- data schema（成功）:
  ```yaml
  type: object
  required: [schema_version, phases, gates, entries_count, generated_at]
  properties:
    schema_version:
      type: string
    phases:
      type: array
      items:
        type: string
    gates:
      type: array
      items:
        type: string
    entries_count:
      type: integer
    generated_at:
      type: string
      format: date-time
  ```
- error_codes: `400 validation`, `401 authorization`, `404 not_found`, `500 internal`
- track: be / fullstack(接続)
- layer: requirement / architectural
- pair_status 方向: be detailed ↔ fullstack detailed
- owner: tl
- D-CONTRACT 参照: §3.2 PromotionHook（baseline_promotion kind）

#### 3.4.2 POST /api/v1/plan/{plan_id}/vmodel/baseline-policy

- path: `/api/v1/plan/{plan_id}/vmodel/baseline-policy`
- method: `POST`
- origin_ac: FR-VS02, FR-QA01
- body_schema:
  ```yaml
  type: object
  required: [policy_id, drive, review_unit, pair_status_threshold]
  properties:
    policy_id:
      type: string
    drive:
      type: string
      enum: [be, fe, db, fullstack]
    review_unit:
      type: string
      enum: [table, functional, requirement, architecture, detailed]
    pair_status_threshold:
      type: string
      enum: [paired, waived]
    approved_by:
      type: string
      description: waived 時必須
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict`, `500 internal`
- track: be / fullstack
- layer: architecture / detailed
- pair_status 方向: be detailed ↔ fullstack detailed
- owner: tl

#### 3.4.3 GET /api/v1/plan/{plan_id}/vmodel/baseline-policy/{policy_id}

- path: `/api/v1/plan/{plan_id}/vmodel/baseline-policy/{policy_id}`
- method: `GET`
- path_schema:
  ```yaml
  type: object
  required: [plan_id, policy_id]
  properties:
    plan_id:
      type: string
    policy_id:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `404 not_found`, `500 internal`
- track: be / fullstack
- layer: requirement / detailed
- owner: tl

---

### 3.5 handover protocol（C-02）

#### 3.5.1 GET /api/v1/handover/{plan_id}/status

- path: `/api/v1/handover/{plan_id}/status`
- method: `GET`
- origin_ac: FR-HO01, FR-HO02（L1-REQUIREMENTS）
- path_schema:
  ```yaml
  type: object
  required: [plan_id]
  properties:
    plan_id:
      type: string
  ```
- query_schema:
  ```yaml
  type: object
  properties:
    include_history:
      type: boolean
      default: false
  ```
- header_schema:
  ```yaml
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization:
      type: string
    Content-Type:
      type: string
      enum: [application/json]
    X-Trace-Id:
      type: string
  ```
- data schema（成功）:
  ```yaml
  type: object
  required: [status, owner, task_id, next_action, updated_at]
  properties:
    status:
      type: string
      enum: [in_progress, ready_for_review, blocked, escalated, completed]
    owner:
      type: string
      enum: [opus, codex]
    task_id:
      type: string
    next_action:
      type: string
    blockers:
      type: array
      items:
        type: string
    updated_at:
      type: string
      format: date-time
  ```
- error_codes: `400 validation`, `401 authorization`, `404 not_found`, `500 internal`
- track: be（全 drive 横断）
- layer: requirement
- pair_status 方向: 全 drive pair_status
- owner: tl
- D-CONTRACT 参照: §6 drive 切替契約（handover が drive 切替を跨ぐ場合）

#### 3.5.2 POST /api/v1/handover/{plan_id}/update

- path: `/api/v1/handover/{plan_id}/update`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [status]
  properties:
    status:
      type: string
      enum: [in_progress, ready_for_review, blocked, escalated]
    owner:
      type: string
      enum: [opus, codex]
    note:
      type: string
    blocker:
      type: string
    next_action:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict`, `500 internal`
- owner: tl

#### 3.5.3 POST /api/v1/handover/{plan_id}/escalate

- path: `/api/v1/handover/{plan_id}/escalate`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [reason]
  properties:
    reason:
      type: string
    context:
      type: string
      description: 詳細説明（試みた内容、関連ファイル等）
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict`, `500 internal`
- 副作用: ESCALATION.md 生成、task.status = escalated 遷移
- owner: tl

#### 3.5.4 POST /api/v1/handover/{plan_id}/clear

- path: `/api/v1/handover/{plan_id}/clear`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [reason]
  properties:
    reason:
      type: string
      enum: [completed, abandoned]
    force:
      type: boolean
      default: false
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization`, `409 conflict`, `500 internal`
- 備考: force=true は abandoned 時のみ許可、PM 承認前提
- owner: tl

---

### 3.6 skill 推挙 / skill chain（C-03）

#### 3.6.1 POST /api/v1/skills/search

- path: `/api/v1/skills/search`
- method: `POST`
- origin_ac: PLAN-024, PLAN-043
- body_schema:
  ```yaml
  type: object
  required: [task_description]
  properties:
    task_description:
      type: string
      description: タスク記述（gpt-5.4-mini へ転送）
    top_n:
      type: integer
      default: 5
      minimum: 1
      maximum: 20
    include_cached:
      type: boolean
      default: true
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `502 upstream`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [skills, cache_hit, generated_at]
  properties:
    skills:
      type: array
      items:
        type: object
        required: [skill_id, score, agent, reason]
        properties:
          skill_id:
            type: string
          score:
            type: number
          agent:
            type: string
          reason:
            type: string
    cache_hit:
      type: boolean
    generated_at:
      type: string
      format: date-time
  ```
- track: be
- layer: functional
- pair_status 方向: be functional ↔ fullstack functional
- owner: se

#### 3.6.2 POST /api/v1/skills/chain

- path: `/api/v1/skills/chain`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [task_description]
  properties:
    task_description:
      type: string
    top_n:
      type: integer
      default: 1
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `502 upstream`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [selected_skill, dispatch_target, executed]
  properties:
    selected_skill:
      type: string
    dispatch_target:
      type: string
    executed:
      type: boolean
    dispatch_result:
      type: object
      additionalProperties: true
  ```
- track: be / fullstack
- layer: functional
- owner: se

---

### 3.7 Reverse HELIX（C-04）

共通 path パラメータ:
- `{type}`: `code` / `design` / `upgrade` / `normalization` / `fullback`
- `{phase}`: `r0` / `r1` / `r2` / `r3` / `r4`

#### 3.7.1 POST /api/v1/reverse/{type}/r0

- path: `/api/v1/reverse/{type}/r0`
- method: `POST`
- origin_ac: PLAN-049, workflow/reverse-r0/SKILL.md
- path_schema:
  ```yaml
  type: object
  required: [type]
  properties:
    type:
      type: string
      enum: [code, design, upgrade, normalization, fullback]
  ```
- body_schema:
  ```yaml
  type: object
  required: [plan_id, target_paths]
  properties:
    plan_id:
      type: string
    target_paths:
      type: array
      items:
        type: string
    include_db:
      type: boolean
      default: true
    include_config:
      type: boolean
      default: true
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `404 not_found`, `500 internal`
- track: be
- layer: requirement / architecture
- owner: tl

#### 3.7.2〜3.7.5 POST /api/v1/reverse/{type}/{r1〜r4}

各フェーズ共通構造（r1〜r4）:

- path: `/api/v1/reverse/{type}/{phase}` where phase ∈ {r1, r2, r3, r4}
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [plan_id, evidence_from_previous]
  properties:
    plan_id:
      type: string
    evidence_from_previous:
      type: object
      additionalProperties: true
      description: 前フェーズの evidence オブジェクト（R0→R1→R2→R3→R4 と順次渡す）
    reviewer_notes:
      type: string
  ```
- r4 追加 body fields:
  ```yaml
  forward_routing:
    type: string
    enum: [L1, L2, L3, L4]
    description: Forward HELIX への接続先フェーズ
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict（前段 evidence 未完）`, `500 internal`
- track: be
- layer: architecture（r1/r2） / requirement（r3） / architecture（r4）
- owner: tl

---

### 3.8 Scrum HELIX（C-05）

#### 3.8.1 POST /api/v1/scrum/{plan_id}/backlog/add

- path: `/api/v1/scrum/{plan_id}/backlog/add`
- method: `POST`
- origin_ac: PLAN-007, agent-skills/helix-scrum/SKILL.md
- body_schema:
  ```yaml
  type: object
  required: [hypothesis_id, description, success_criteria]
  properties:
    hypothesis_id:
      type: string
    description:
      type: string
    success_criteria:
      type: string
    priority:
      type: string
      enum: [P1, P2, P3]
      default: P2
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict`, `500 internal`
- track: be
- layer: planning
- owner: se

#### 3.8.2 POST /api/v1/scrum/{plan_id}/plan

- path: `/api/v1/scrum/{plan_id}/plan`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [sprint_goal, hypothesis_ids]
  properties:
    sprint_goal:
      type: string
    hypothesis_ids:
      type: array
      items:
        type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict（仮説未登録）`, `500 internal`
- owner: se

#### 3.8.3 POST /api/v1/scrum/{plan_id}/poc

- path: `/api/v1/scrum/{plan_id}/poc`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [hypothesis_id]
  properties:
    hypothesis_id:
      type: string
    verify_script_path:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `404 not_found`, `500 internal`
- owner: se

#### 3.8.4 POST /api/v1/scrum/{plan_id}/decide

- path: `/api/v1/scrum/{plan_id}/decide`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [hypothesis_id, decision]
  properties:
    hypothesis_id:
      type: string
    decision:
      type: string
      enum: [confirmed, rejected, pivot]
    forward_phase:
      type: string
      enum: [L1, L2, L3, L4]
      description: confirmed 時のみ必須（Forward HELIX 接続先）
    pivot_description:
      type: string
      description: pivot 時のみ
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `404 not_found`, `409 conflict`, `500 internal`
- track: be / fullstack
- layer: functional
- owner: se

---

### 3.9 Agent Transformation 散在（C-06）

#### 3.9.1 POST /api/v1/dispatch/codex

- path: `/api/v1/dispatch/codex`
- method: `POST`
- origin_ac: PLAN-028, PLAN-043
- body_schema:
  ```yaml
  type: object
  required: [role, task]
  properties:
    role:
      type: string
      enum: [tl, se, pe, qa, security, dba, devops, docs, research, legacy, perf]
    task:
      type: string
    consent:
      type: string
      enum: [approved, auto]
      default: auto
    thinking:
      type: string
      enum: [low, medium, high, xhigh]
    plan_id:
      type: string
    task_id:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization（consent 未承認）`, `500 internal`
- track: be
- layer: functional
- pair_status 方向: be functional ↔ fullstack functional
- owner: tl

#### 3.9.2 POST /api/v1/dispatch/claude

- path: `/api/v1/dispatch/claude`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [role, task]
  properties:
    role:
      type: string
      enum: [pmo-sonnet, pmo-haiku, pm-advisor, pmo-helix-explorer, pmo-project-explorer]
    task:
      type: string
    allow_paths:
      type: string
    dry_run:
      type: boolean
      default: false
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization`, `500 internal`
- owner: tl

#### 3.9.3 POST /api/v1/dispatch/team

- path: `/api/v1/dispatch/team`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [definition, task]
  properties:
    definition:
      type: string
      description: helix team --definition の定義ファイルパス
    task:
      type: string
    parallel:
      type: boolean
      default: true
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- owner: tl

---

### 3.10 PMO / advisor role system（C-07）

#### 3.10.1 POST /api/v1/advisor/pm

- path: `/api/v1/advisor/pm`
- method: `POST`
- origin_ac: PLAN-028, CLAUDE.md §Advisor 召喚
- body_schema:
  ```yaml
  type: object
  required: [task]
  properties:
    task:
      type: string
      description: PM 級判断の質問（スコープ/優先度/大局リスク/フェーズ整合/委譲先）
    context:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `502 upstream`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [advice, model, generated_at]
  properties:
    advice:
      type: string
    model:
      type: string
      enum: [claude-opus-4-7]
    generated_at:
      type: string
      format: date-time
  ```
- track: be
- layer: planning / requirement
- owner: se
- 備考: read-only。実装変更・状態変更なし

#### 3.10.2 POST /api/v1/advisor/tl

- path: `/api/v1/advisor/tl`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [task]
  properties:
    task:
      type: string
      description: TL 級判断の質問（設計選択/契約/テスト戦略/リファクタ）
    context:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `502 upstream`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [advice, model, generated_at]
  properties:
    advice:
      type: string
    model:
      type: string
      enum: [gpt-5.5]
    generated_at:
      type: string
      format: date-time
  ```
- owner: se
- 備考: read-only。実装変更・状態変更なし

---

### 3.11 Codex / Claude harness + PreToolUse guard（C-08）

#### 3.11.1 POST /api/v1/harness/codex/exec

- path: `/api/v1/harness/codex/exec`
- method: `POST`
- origin_ac: PLAN-028, PLAN-043
- body_schema:
  ```yaml
  type: object
  required: [role, prompt, consent]
  properties:
    role:
      type: string
    prompt:
      type: string
    consent:
      type: string
      enum: [approved, auto]
    thinking:
      type: string
      enum: [low, medium, high, xhigh]
    allowed_files:
      type: array
      items:
        type: string
    plan_id:
      type: string
    task_id:
      type: string
    acceptance:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization（consent=auto 時 plan-only guard 発火）`, `500 internal`
- track: be
- layer: functional
- owner: tl

#### 3.11.2 POST /api/v1/harness/claude/exec

- path: `/api/v1/harness/claude/exec`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [role, prompt]
  properties:
    role:
      type: string
      enum: [pmo-sonnet, pmo-haiku, pm-advisor]
    prompt:
      type: string
    execute:
      type: boolean
      default: false
    allow_paths:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization`, `500 internal`
- owner: tl

#### 3.11.3 POST /api/v1/harness/guard/pre-tool-use

- path: `/api/v1/harness/guard/pre-tool-use`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [tool_name, model, file_path]
  properties:
    tool_name:
      type: string
      enum: [Edit, Write, Bash]
    model:
      type: string
    file_path:
      type: string
    requested_by:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `403 authorization（Opus 直接編集ブロック）`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [allowed, block_reason]
  properties:
    allowed:
      type: boolean
    block_reason:
      type: string
      nullable: true
  ```
- track: be
- layer: functional
- owner: tl

---

### 3.12 code-index（C-09）

#### 3.12.1 GET /api/v1/code-index/find

- path: `/api/v1/code-index/find`
- method: `GET`
- origin_ac: PLAN-011, PLAN-012, PLAN-013
- query_schema:
  ```yaml
  type: object
  required: [query]
  properties:
    query:
      type: string
    top_n:
      type: integer
      default: 5
    bucket:
      type: string
      enum: [coverage_eligible, private_helper, excluded]
    seed_candidate:
      type: boolean
    seed_promotable:
      type: boolean
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [results, total]
  properties:
    results:
      type: array
      items:
        type: object
        required: [id, path, domain, summary, bucket]
        properties:
          id:
            type: string
          path:
            type: string
          domain:
            type: string
          summary:
            type: string
          bucket:
            type: string
            enum: [coverage_eligible, private_helper, excluded]
    total:
      type: integer
  ```
- track: be
- layer: detailed / functional
- pair_status 方向: be detailed ↔ fullstack detailed
- owner: se

#### 3.12.2 POST /api/v1/code-index/build

- path: `/api/v1/code-index/build`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  properties:
    scope:
      type: string
      enum: [all, core5, cli-lib]
      default: all
    dry_run:
      type: boolean
      default: false
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- owner: se

#### 3.12.3 GET /api/v1/code-index/stats

- path: `/api/v1/code-index/stats`
- method: `GET`
- query_schema:
  ```yaml
  type: object
  properties:
    scope:
      type: string
      enum: [all, core5, cli-lib]
      default: all
    bucket:
      type: string
      enum: [coverage_eligible, private_helper, excluded]
    fail_under:
      type: integer
      minimum: 0
      maximum: 100
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [scope, total, covered, uncovered, coverage_pct, gate_passed]
  properties:
    scope:
      type: string
    total:
      type: integer
    covered:
      type: integer
    uncovered:
      type: integer
    coverage_pct:
      type: number
    gate_passed:
      type: boolean
    fail_under_threshold:
      type: integer
      nullable: true
  ```
- track: be
- layer: functional
- owner: se

---

### 3.13 budget guard / auto-thinking support（C-10）

#### 3.13.1 GET /api/v1/budget/status

- path: `/api/v1/budget/status`
- method: `GET`
- origin_ac: PLAN-024, budget guard feature
- query_schema:
  ```yaml
  type: object
  properties:
    period:
      type: string
      enum: [daily, weekly]
      default: weekly
  ```
- header_schema:
  ```yaml
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization:
      type: string
    Content-Type:
      type: string
      enum: [application/json]
    X-Trace-Id:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [claude_pct, codex_pct, period, exhaustion_forecast]
  properties:
    claude_pct:
      type: number
      minimum: 0
      maximum: 100
    codex_pct:
      type: number
      minimum: 0
      maximum: 100
    period:
      type: string
    exhaustion_forecast:
      type: string
      format: date-time
      nullable: true
  ```
- track: be
- layer: functional
- owner: se

#### 3.13.2 POST /api/v1/budget/simulate

- path: `/api/v1/budget/simulate`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  required: [task]
  properties:
    task:
      type: string
    size:
      type: string
      enum: [S, M, L]
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [recommended_model, recommended_thinking, estimated_cost_usd, delegate_to]
  properties:
    recommended_model:
      type: string
    recommended_thinking:
      type: string
      enum: [low, medium, high, xhigh]
    estimated_cost_usd:
      type: number
    delegate_to:
      type: string
  ```
- track: be
- layer: functional
- owner: se

---

### 3.14 code-index + contract registry 追加整合（C-11）

#### 3.14.1 GET /api/v1/code-index/contract-alignment

- path: `/api/v1/code-index/contract-alignment`
- method: `GET`
- origin_ac: PLAN-065, PLAN-067
- query_schema:
  ```yaml
  type: object
  properties:
    plan_id:
      type: string
    drive:
      type: string
      enum: [be, fe, db, fullstack]
    include_resolved:
      type: boolean
      default: false
  ```
- header_schema:
  ```yaml
  type: object
  required: [Authorization, Content-Type, X-Trace-Id]
  properties:
    Authorization:
      type: string
    Content-Type:
      type: string
      enum: [application/json]
    X-Trace-Id:
      type: string
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `404 not_found`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [aligned, misaligned, generated_at]
  properties:
    aligned:
      type: array
      items:
        type: object
        required: [code_index_id, contract_entry_id, status]
        properties:
          code_index_id:
            type: string
          contract_entry_id:
            type: string
          status:
            type: string
            enum: [aligned, stale, orphan]
    misaligned:
      type: array
      items:
        type: object
        required: [code_index_id, reason]
        properties:
          code_index_id:
            type: string
          reason:
            type: string
    generated_at:
      type: string
      format: date-time
  ```
- track: be / fullstack
- layer: detailed / functional
- pair_status 方向: be ↔ fullstack 詳細
- owner: se

#### 3.14.2 POST /api/v1/code-index/contract-alignment/sync

- path: `/api/v1/code-index/contract-alignment/sync`
- method: `POST`
- body_schema:
  ```yaml
  type: object
  properties:
    plan_id:
      type: string
    dry_run:
      type: boolean
      default: false
    target_ids:
      type: array
      items:
        type: string
      description: 対象 code_index_id を限定する（空なら全件）
  ```
- response_schema:
  - success: `$ref: '#/components/schemas/Envelope'`
  - error: `400 validation`, `409 conflict`, `500 internal`
- data schema（成功）:
  ```yaml
  type: object
  required: [synced_count, skipped_count, dry_run]
  properties:
    synced_count:
      type: integer
    skipped_count:
      type: integer
    dry_run:
      type: boolean
  ```
- track: be / fullstack
- layer: functional
- owner: se
