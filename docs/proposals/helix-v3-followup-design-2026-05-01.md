# HELIX v3 Followup — 派生実装事前設計

> 日付: 2026-05-01
> 起点: HELIX-V3-FOLLOWUP — handover Next Action #4 派生実装の前提
> TL レビュー: gpt-5.5 (Codex 5.4 系) xhigh / overall Lv4×5 / verdict=approve
> ソース: `/tmp/claude-1001/.../bct6vn9ub.output`

## 目的

PLAN-004 v5 で導入された「P0/P1/P2/P3 carry rule」「accuracy_score への deferred-finding 反映」「readiness exit 判定」の実装契約を確定する。

## §1. `.helix/audit/deferred-findings.yaml` schema (v1)

### 1.1 ヘッダ

```yaml
version: 1
redaction:
  applied: true
  policy: "cli/lib/redaction.py + observability denylist"
findings: [...]
```

### 1.2 finding 単位の field

```yaml
- id: "DF-PLAN-007-L2-001"        # DF-{plan_id}-{phase}-{seq}
  plan_id: "PLAN-007"
  origin:  {plan_id: "PLAN-007", phase: "L2"}     # 発生位置
  current: {plan_id: "PLAN-007", phase: "L2"}     # 現在の保有者
  target:  {plan_id: "PLAN-007", phase: "G3"}     # 解消目標
  level: "P1"                     # P0|P1|P2|P3
  carry_rule: "carry-with-pm-approval"  # stop|carry-with-pm-approval|auto-carry|optional
  phase: "L2"                     # L0..L11|G2..G11
  source: ".helix/reviews/plans/PLAN-007.json#/findings/0"
  severity: "high"                # critical|high|medium|low
  title: "..."
  body: "[REDACTED 済み要約]"      # secret/PII/token は redaction.py で除去
  recommendation: "..."
  dimension_scores:
    - {dimension: "accuracy",        level: 2, comment: "..."}
    - {dimension: "maintainability", level: 3, comment: "..."}
  status: "carried"               # open|carried|resolved|abandoned
  created_at: "2026-04-30T00:00:00Z"
  resolved_at: null
  accuracy_impact_weight: 0.70    # P1=0.70 / P2=0.35 / P3=0.10 (推奨初期値)
  pm_approval: {required: true, approved_by: "PM", approved_at: null, reason: null}
  carry_chain:
    - {from: "PLAN-007:L2", to: "PLAN-007:G3", status: "carried"}
```

### 1.3 carry rule (PLAN-004 §4.5.2 準拠)

| level | carry_rule | gate 挙動 | pm_approval |
|---|---|---|---|
| P0 | stop | 即停止 | required |
| P1 | carry-with-pm-approval | gate stop OR carry | required |
| P2 | auto-carry | 次 L 開始まで OR carry | optional |
| P3 | optional | 任意 carry | optional |

### 1.4 severity → level 自動 mapping (migration 用)

| review severity | deferred level |
|---|---|
| critical | P0 |
| high | P1 |
| medium | P2 |
| low | P3 |

## §2. helix.db 接続 (join 別表方式)

既存 `accuracy_score` テーブルは `gate` カラムが enum CHECK 固定（[cli/lib/helix_db.py:289](cli/lib/helix_db.py#L289)）のため**直接改変しない**。

```text
.helix/audit/deferred-findings.yaml
  ↓ sync (helix-readiness defer/accept)
deferred_findings(id, plan_id, origin_phase, current_phase, target_phase,
                  level, carry_rule, status, source, severity, weight,
                  created_at, resolved_at)
  ↓ join
accuracy_score_adjustments(finding_id, plan_id, gate, dimension, penalty)
  ↓ join
accuracy_score (既存、無改変)
  ↓ view
accuracy_score_effective VIEW (= accuracy_score - SUM(adjustments.penalty))
```

migration は `helix.db v11` で実施。

## §3. `helix-readiness` CLI

### 3.1 subcommand (MVP)

```text
helix readiness check  [--phase L4] [--json]
helix readiness list   [--plan PLAN-007] [--level P1,P2] [--status open,carried]
helix readiness report [--plan PLAN-009] [--phase L9] [--json]
helix readiness defer  --finding DF-... --to PLAN-009:L9 [--approved-by PM]
helix readiness accept --finding DF-... --status resolved|abandoned --evidence <path> [--approved-by PM]
```

`reset` は MVP 除外（audit が曖昧になるため、`helix plan reset` に分離）。

### 3.2 exit code

| code | 意味 |
|---|---|
| 0 | ready |
| 1 | not-ready (条件未達、要追加作業) |
| 2 | blocking-finding (P0 or P1 未承認) |
| 3 | missing-evidence (deliverable 不在) |

### 3.3 各 L の readiness exit 条件 (TL 確定)

| L | exit 条件 |
|---|---|
| L0 | phase/config 初期化 |
| L1 | 要件/受入条件 |
| L2 | ADR/設計/threat model |
| L3 | API/Schema/WBS/test plan |
| L4 | sprint .1-.5/CI |
| L5 | UI/visual/a11y or waived |
| L6 | E2E/性能/セキュリティ |
| L7 | runbook/release/rollback |
| L8 | 受入/deferred handover |
| L9 | smoke/rollback/metrics |
| L10 | SLO/SLI/異常ログ |
| L11 | postmortem/run-learning/next-cycle proposal |

### 3.4 helix-gate 接続

```text
before: gate prereq + deliverable + static + AI                       → pass
after:  gate prereq + deliverable + static + AI + readiness_exit(L)   → pass
```

[cli/helix-gate:1217](cli/helix-gate#L1217) で phase 更新前に `helix readiness check --phase <mapped>` を AND 結合する fail-close 経路を追加。`gate-policy.md` にも readiness AND 条件を追記する。

## §4. `helix plan reset`

### 4.1 usage

```text
helix plan reset --id PLAN-008 --to draft    --reason "v2 改訂"
helix plan reset --id PLAN-008 --to reviewed --reason "finalize のみ取り消し"
```

受付: `status ∈ {finalized, reviewed, approved}`（既存 finalize 条件は `review.status=approve` のため、`approved` は互換 alias として扱う — [cli/helix-plan:487](cli/helix-plan#L487)）。

### 4.2 状態遷移

```yaml
state:
  finalized:
    reset_to_draft:    {status: draft,    finalized_at: null, review: pending/null}
    reset_to_reviewed: {status: reviewed, finalized_at: null, review: keep}
  reviewed:
    reset_to_draft:    {status: draft,    finalized_at: null, review: pending/null}
```

### 4.3 revision_history schema (yaml に追記)

```yaml
revision_history:
  - revision: 1
    action: "plan_reset"
    from_status: "finalized"
    to_status: "draft"
    reset_at: "2026-05-01T00:00:00Z"
    reason: "v2 改訂"
    reviewed_at: "2026-04-30T15:57:16Z"   # 直前の review.reviewed_at をスナップショット
    verdict: "approve"
    review_file: ".helix/reviews/plans/PLAN-008.json"
    finalized_at: "2026-04-30T15:57:34Z"
```

### 4.4 audit ログ

`helix.db events(event_name='plan_reset', data_json={plan_id, from_status, to_status, reason, revision})` に記録。

## §5. 残 finding (TL P2/P3)

- **P2**: `accuracy_score.gate` は G9-G11 / readiness を直接受けられない → §2 の **join 別表 + VIEW** で対応（本設計に既に反映済み）
- **P3**: `helix readiness reset` は MVP 除外（必要なら別途 audit 付き admin command として後続設計）

## §6. 実装委譲計画

| # | 委譲対象 | 委譲先 | 依存 |
|---|---|---|---|
| 1 | `helix.db v11 migration` (deferred_findings + accuracy_score_adjustments + view) | Codex DBA | — |
| 2 | `cli/lib/deferred_findings.py` (YAML I/O + redaction + DB sync) | Codex SE | 1 |
| 3 | `cli/helix-readiness` (新規 bash CLI、subcommand 5種) | Codex SE | 2 |
| 4 | `cli/helix-plan` reset サブコマンド追加 | Codex SE | — |
| 5 | `.helix/audit/deferred-findings.yaml` 初版（既存 PLAN-002〜010 review.json から 28 件 import） | Codex SE | 2 |
| 6 | `cli/helix-gate` に readiness AND 条件追加 ([helix-gate:1217](cli/helix-gate#L1217)) | Codex SE | 3 |
| 7 | `skills/tools/ai-coding/references/gate-policy.md` 追記 (readiness AND 明文化) | Codex Docs | 6 |
| 8 | helix-test 追加 (readiness check / migration / plan reset の単体テスト) | Codex QA | 1-6 |

## §7. 5 軸スコア (TL 設計レビュー)

`density Lv4 / depth Lv4 / breadth Lv4 / accuracy Lv4 / maintainability Lv4`

すべて Lv3 以上、致命欠陥なし → **PM (Opus) 承認 → 実装委譲フェーズ移行**。
