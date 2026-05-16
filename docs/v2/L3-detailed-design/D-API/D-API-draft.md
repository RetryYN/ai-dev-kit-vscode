---
doc_id: D-API-draft-v0.1
plan_id: PLAN-070
sprint: SprintA / .1
status: draft
created: 2026-05-16
drive_scope:
  primary_drive: be
  secondary_drives:
    - fullstack
    - fe
---

# PLAN-070 / D-API Draft

## §1 目的とスコープ

### 1.1 目的

本稿は L2 G2 凍結（commit `e28ca8d`, 2026-05-16）を前提に、PLAN-070 SprintA（L3 D-API）を起票し、capability 起点で endpoint contract / request-response / error model を 1 ファイルで固定する。

### 1.2 スコープ

- be を起点にし、fullstack/fe は接続責務を明示して補助する。
- API 実装コード、hook 実行内部、UI 描画仕様は対象外。
- endpoint 構造、pair/gate 契約、エラー整合を draft で固定する。

### 1.3 Non-goals

- API 実装本体（controller/service/repo）
- D-DB migration 本文 / SQL 本文（SprintB）
- D-CONTRACT の契約 enforcement 実装（SprintC）
- state-events.md の本文更新

## §2.0 共通 API primitive

以下の primitive を §3 の request/response を含む全 schema で優先採用する。

```yaml
components:
  schemas:
    Envelope:
      type: object
      required: [success, data, error, trace]
      properties:
        success:
          type: boolean
        data:
          anyOf:
            - type: object
            - type: array
            - type: string
            - type: number
            - type: integer
            - type: boolean
            - type: null
        error:
          $ref: '#/components/schemas/ErrorModel'
        trace:
          type: object
          required: [trace_id, generated_at]
          properties:
            trace_id:
              type: string
              format: uuid
            generated_at:
              type: string
              format: date-time
    ErrorModel:
      type: object
      required: [code, class, message, details, retryable]
      properties:
        code:
          type: string
        class:
          type: string
          enum: [validation, authorization, not_found, conflict, functional_freeze_violation, promotion_violation, drive_switch_violation, internal]
        message:
          type: string
        details:
          type: object
          additionalProperties: true
        retryable:
          type: boolean
    DetectorRef:
      type: string
      enum:
        - axis-01-dead-code-drift
        - axis-02-coverage-erosion
        - axis-06-naming-confusion
        - axis-07-contract-drift
        - axis-08-plan-integrity
        - axis-09-refactor-opportunity
        - axis-09-test-quality
        - axis-10-relation-graph
        - axis-11-regression
        - axis-12-connection-deficiency
        - axis-12-migration-safety
        - axis-14-orchestration-integrity
        - axis-15-mock-promotion
        - axis-16-design-token-drift
        - axis-17-a11y-regression
        - axis-18-visual-regression
        - axis-19-state-transition-drift
    PairStatusTransition:
      type: object
      required: [from, to, reason, actor, approved_by, enforce_policy]
      properties:
        from:
          type: string
          enum: [pending, paired, waived, failed]
        to:
          type: string
          enum: [pending, paired, waived, failed]
        reason:
          type: string
        actor:
          type: string
        approved_by:
          type: string
        enforce_policy:
          type: string
    PromotionHookRef:
      type: object
      description: SprintC での D-CONTRACT 定義に移譲する placeholder
      required: [pending_for_sprint_c]
      properties:
        pending_for_sprint_c:
          type: string
          enum: ["true"]
```

## §2 capability map

本節は `docs/v2/A-audit/capability-inventory.md` / `capability-matrix.md` 及び `docs/v2/L2-MASTER.md` の設計接続点をそのまま転写する。

### 2.1 capability 一覧（SprintA 収束 + carry）

| capability | 起源 | 状態 | owner role | review_unit | 検知 detectors | pair_status 方向 | be 起点責務 | fullstack/fe 追加責務 |
|---|---|---|---|---|---|---|---|---|
| V-model schema / QA baseline schema | PLAN-065 | 部分実装 | tl | table（detailed/functional） | axis-07-contract-drift, axis-12-connection-deficiency, axis-02-coverage-erosion | be detailed ↔ fullstack detailed | `api_capability_map` と baseline policy を固定 | FE 接続では `state-events` と整合を確認 |
| 14 detector system | PLAN-063 | 実装済 | tl | functional | axis-10-relation-graph, axis-09-refactor-opportunity, axis-01-dead-code-drift, axis-08-plan-integrity | be functional ↔ fullstack functional | detector enum と pair 停止条件を固定 | 可観測イベントを FE 接続で追記 |
| 契約 extractor / contract registry | PLAN-063,065 | 部分実装 | se | detailed | axis-07-contract-drift, axis-08-plan-integrity, axis-12-connection-deficiency | be detailed ↔ fullstack detailed | docs path と contract_entries 記録契約を固定 | contract kind を fe 連携観点で明示 |
| handover protocol | PLAN-016 | 実装済 | tl | requirement | axis-14-orchestration-integrity, axis-08-plan-integrity | 全drive pair_status | CURRENT 系ファイル接続を維持 | 承認移譲時の D-API エビデンス保持 |
| Gate runner | PLAN-063,067 | 部分実装 | tl | functional | axis-07-contract-drift, axis-08-plan-integrity, axis-12-connection-deficiency | be architecture / functional | gate 条件の draft を固定 | `--subgate functional_freeze` の再現フローを追加 |
| code-index + contract registry 追加整合 | PLAN-065,067 | 部分実装 | se | detailed | axis-06-naming-confusion, axis-07-contract-drift | be ↔ fullstack 詳細 | 契約/検証の片方向参照を固定 | FE 追加 artifact を map に明示 |

### 2.2 drive 切替時責務（be -> fullstack/fe）

- be が primary。be 側で design と test のペアを先に freeze したうえで、fullstack は「接続差分（追加）」を持つ。
- fullstack/fe は以下の 3 点を追加する。
  1. `allowed_detectors` を track ごとに明示
  2. `pair_status` 遷移証跡（waived 時は理由）
  3. contract 追加 trace（mock→implementation）

## §3 endpoint contract draft（代表 3 capability）

- `capability-matrix.md`: `review_unit` と `pair_status` 接続点（design / test / functional）を満たす capability を選定。
- 代表 3 capability: 契約 extractor / contract registry、14 detector system、Gate runner。選定根拠は capability-matrix.md の `review_unit` と `pair_status` 接続点に基づく。

### 3.1 契約 extractor / contract registry

- path: `/api/v1/plan/{plan_id}/capabilities/contracts/registry`
- method: `GET`
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
    drive:
      type: string
      enum: [be, fullstack, fe, db]
    include_detectors:
      type: boolean
      default: false
    include_stale:
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
- body_schema:
  ```yaml
  type: object
  properties: {}
  additionalProperties: false
  ```
- response_schema:
  - success:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - partial:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - error:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
- data schema（成功）:
  ```yaml
  type: object
  required: [entries, meta]
  properties:
    entries:
      type: array
      items:
        type: object
        required: [artifact_kind, artifact_id, pair_status, plan_scope, detector_refs]
        properties:
          artifact_kind:
            type: string
          artifact_id:
            type: string
          pair_status:
            type: string
            enum: [pending, design_only, test_only, paired, waived, failed]
          plan_scope:
            type: string
          detector_refs:
            type: array
            items:
              $ref: '#/components/schemas/DetectorRef'
    meta:
      type: object
      required: [trace_id, generated_at]
      properties:
        trace_id:
          type: string
          format: uuid
        generated_at:
          type: string
          format: date-time
  ```
- data schema（partial）:
  ```yaml
  type: object
  required: [entries, warning]
  properties:
    entries:
      type: array
      items:
        type: object
        required: [artifact_id, pair_status]
        properties:
          artifact_id:
            type: string
          pair_status:
            type: string
          reason:
            type: string
    warning:
      type: string
  ```
- error_codes: `400 validation`, `401 authorization`, `404 not_found`, `500 internal`
- track: be / fullstack(接続)
- layer: detailed / architectural
- pair_status 参照: `PairStatusTransition` DTO に従う (waived 時は `approved_by` および `enforce_policy` 必須)

### 3.2 14 detector system（監査トリガ）

- path: `/api/v1/plan/{plan_id}/detectors/registry`
- method: `POST`
- 理由: 監査トリガを起動し、`detector_runs` を append-only で記録するため POST。
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
    include_stale:
      type: boolean
      default: false
    drive:
      type: string
      enum: [be, fe, db, fullstack]
    layer:
      type: string
      enum: [planning, requirement, architecture, detailed, functional]
  required: [drive, layer]
  description: drive / layer は cross-cutting parameter、query 経由で柔軟に指定
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
- body_schema:
  ```yaml
  type: object
  required: [allowed_detectors]
  properties:
    allowed_detectors:
      type: array
      items:
        $ref: '#/components/schemas/DetectorRef'
    requires_functional_freeze:
      type: boolean
  ```
- response_schema:
  - success:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - partial:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - error: `400 validation`, `403 authorization`, `404 not_found`
- track: be / fullstack
- layer: architecture（required）/functional
- pair_status 参照: `PairStatusTransition` DTO に従う (waived 時は `approved_by` および `enforce_policy` 必須)

### 3.3 Gate runner（freeze / gate 起点）

- path: `/api/v1/plan/{plan_id}/gates/{drive}`
- method: `POST`
- path_schema:
  ```yaml
  type: object
  required: [plan_id, drive]
  properties:
    plan_id:
      type: string
    drive:
      type: string
      enum: [be, fe, db, fullstack]
  ```
- query_schema:
  ```yaml
  type: object
  properties:
    include_trace:
      type: boolean
      default: true
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
- body_schema:
  ```yaml
  type: object
  required: [gate_id, size, include_freeze]
  properties:
    gate_id:
      type: string
    size:
      type: string
      enum: [S, M, L]
    include_freeze:
      type: boolean
    approved_by:
      type: string
      description: when pair_status is waived
    enforce_policy:
      type: string
      description: when pair_status is waived
    transition:
      $ref: '#/components/schemas/PairStatusTransition'
  ```
- response_schema:
  - success:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - partial:
    ```yaml
    $ref: '#/components/schemas/Envelope'
    ```
  - error: `401 authorization`, `409 conflict`, `500 internal`
- track: be / fullstack
- layer: architecture / functional
- pair_status 参照: `PairStatusTransition` DTO に従う (waived 時は `approved_by` および `enforce_policy` 必須)

## §3.4〜§3.14 carry capability endpoint contract（PLAN-071）

詳細は `D-API-CARRY-draft.md` を参照（分離理由: D-API-draft.md の §4.4 ±200 行制約遵守）。

## §4 共通 error model

### 4.1 標準形式

- envelope 形式は `#/components/schemas/Envelope` を採用。
- `Trace` は `#/components/schemas/Envelope` の `trace` を参照。

### 4.2 error class と retry / observable

- validation: 400, retry なし, metrics(error_code), spans(error.kind=validation)
- authorization: 401/403, retry なし, logs warn
- not_found: 404, retry なし, metrics(not_found)
- conflict: 409, retry 1回のみ, spans(error.kind=conflict)
- functional_freeze_violation: 409, retry なし, logs error
- promotion_violation: 409, retry なし, logs error
- drive_switch_violation: 409, retry なし, logs error
- internal: 500, retry 指数バックオフ, logs critical

### 4.3 D-CONTRACT 先取り制約

- `/promotions/{from_artifact_kind}/to/{to_artifact_kind}` 記述は SprintC へ遷移。
- 本 sprint では `PromotionHookRef` を placeholder のみ定義し、実体は D-CONTRACT で確定。
- 参照: `docs/v2/L2-MASTER.md` §3.4, FR-VD04。

## §5 role 別責務表

### 5.1 RACI Matrix（5 軸分離）

| capability | decision | implementation | verification | approval | documentation |
|---|---|---|---|---|---|
| V-model schema / QA baseline schema | TL | SE | QA | TL | Docs |
| 14 detector system | TL | SE | QA / FE | TL | Docs |
| 契約 extractor / contract registry | TL | SE | QA | TL | Docs |
| handover protocol | TL | SE | TL | PM | Docs |
| Gate runner | TL | SE | QA | TL | Docs |
| code-index + contract registry 追加整合 | TL | SE | QA | TL | Docs |

- A=Accountable / R=Responsible / C=Consulted / I=Informed は機能別 role に再展開し、`who owns` を列外し `who approves` を分離。
- functional_freeze 判定 ownership: TL
- waiver 承認 ownership: PM
- se 実装は endpoint schema / route 実装、qa gate 検証は functional freeze / pair 判定、fe mock contract は `docs/v2/L3-detailed-design/D-API/D-API-draft.md` と §6.4 接続、PM waiver は `approved_by` と `reason` を必須化。

## §6 receiving gates との対応

### 6.1 L1 master AC-16 / functional_freeze 判定式

- 判定式（公式）: `size=L AND drive in (fe/fullstack/db)`
- 出典: L1-REQUIREMENTS AC-16, L2-MASTER §10
- L3 契約反映:
  - 条件成立時: functional_freeze 必須（hard fail）
- 非成立時: waived の場合のみ通過可（`approved_by` / `enforce_policy` 必須）

### 6.2 CLI 契約

- `helix gate --subgate functional_freeze --plan-id <id> --drive <drive>`
- SprintA 固定例:
  - `helix gate --subgate functional_freeze --plan-id PLAN-070 --drive fe`
  - `helix gate --subgate functional_freeze --plan-id PLAN-070 --drive fullstack`
  - `helix gate --subgate functional_freeze --plan-id PLAN-070 --drive db`
- 注記: be は AC-16 適用外（functional_freeze 判定対象外）、動作確認用途のみ。

### 6.3 D-API pair_status trigger

- `pending`: 受け付け可、入門 gate 前提不可。
- `paired`: G2/G3 entry gate 直行可能。
- `waived`: PM waiver 承認と `approved_by` / `enforce_policy` が整合している場合のみ通過。
- `failed`: 修正なしに先へ進行不可。

### 6.4 D-API と L2-MASTER §3, §6, §10 の接続

- §3（5×5）: review_unit / driver / layer を本稿の section3 と一致化。
- §6: 5 層介入（PM, Orchestration, Command, Skill, Verify）を検査失敗時の stop 条件として採用。
- §10: G2 の `80% / 100%` 閾値と `pair_status` 条件を受ける。

## §7 carry / open questions

### 7.1 carry: 未詳細化 capability

**PLAN-071 完了: 全 carry capability 詳細化済（2026-05-17）**

PLAN-071 Sprint .1/.2 により C-01〜C-11 の endpoint contract を §3.4〜§3.14 に追記済。
残 carry は以下のみ（次 PLAN での対応を推奨）:

- state-events（D-CONTRACT 連携対象）: PLAN-072 Phase B 結合時に接続確認
- C-10 budget guard: `cli/lib/cost_guard.py` 未実装部分は L4 実装 PLAN で確定

旧 carry（すべて解消済）:
- ~~skill 推挙 / skill chain~~ → §3.6 詳細化済
- ~~Reverse HELIX~~ → §3.7 詳細化済
- ~~Scrum HELIX~~ → §3.8 詳細化済
- ~~Agent Transformation 散在~~ → §3.9 詳細化済
- ~~code-index~~ → §3.12 詳細化済
- ~~PMO / advisor role system~~ → §3.10 詳細化済
- ~~budget guard / auto-thinking~~ → §3.13 詳細化済（partial done）
- ~~V-model schema / QA baseline schema~~ → §3.4 詳細化済
- ~~handover protocol~~ → §3.5 詳細化済
- ~~Codex / Claude harness + PreToolUse guard~~ → §3.11 詳細化済
- ~~code-index + contract registry 追加整合~~ → §3.14 詳細化済

### 7.2 Sprint C（D-CONTRACT） carry

- `mock_to_implementation` の実装 path パラメータを確定化
  - `from_artifact_kind` / `to_artifact_kind` / `link_kind` / `append_only`
- `g2_evidence_preserved: true` の例外条件
- `promotions` の衝突時再解決順序
- 先取り実装なし、`PromotionHookRef` は SprintC で本実装定義。

### 7.3 Sprint B（D-DB） carry

- `evidence_status` の placeholder enum の型決定
- `design_sprint_entry` / `design_sprint_artifact_links` のキー最小限仕様
- migration 前提 (`v22+` 相当) の追加列を本稿から引き継ぐ

### 7.4 L2-MASTER / capability inventory 接続確認

- `docs/v2/L2-MASTER.md` §3（`api_capability_map`, `promotion`）を参照し、track/layer/pair を一致させる。
- `docs/v2/L2-MASTER.md` §6（ガードレール）を stop 条件に接続。
- `docs/v2/L2-MASTER.md` §10（G2 条件）を AC-16 含む L1 entry 条件へ写像。
