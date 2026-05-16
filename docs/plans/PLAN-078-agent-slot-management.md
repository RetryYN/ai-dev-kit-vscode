---
plan_id: PLAN-078
title: "PLAN-078: Agent Slot 管理 (helix.db v28 + 並列実行可視化)"
status: completed
size: M
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-075 (V-model 4 artifact、本 PLAN にも同原則を適用)
  - PLAN-027 (helix.db entries/links 基盤、初期実装)
  - PLAN-069 (DNA 二重らせん、agent_slots は record strand 拡張)
  - PLAN-068 (v22/v23 schema migration)
  - PLAN-074 (HTTP endpoint 層、agent_slots と automation_runs の境界)
trigger: |
  2026-05-17 PLAN-075 Phase 2-3 完遂セッション中の気付き:
  - Codex 並列起動 (4-8 並列) の自爆リスク (API rate limit、file 衝突、cost 暴走)
  - background process の release されない slot を検出する仕組みが現状なし
  - 「default 8 並列ルール」の遵守率を機械的に測定できない
  - helix.db は本来「依存関係 / trouble-shoot」集約 DB として設計されている (PLAN-027 / PLAN-069)
  - agent slot 管理はその設計思想と整合する自然な拡張
acceptance:
  - helix.db v28 schema migration で `agent_slots` table 追加 (parent_invocation_id で tree 表現)
  - helix-codex 経由の Codex 起動が agent_slots に fire / release で記録される
  - `helix agent slots --active` で現在 active な slot 一覧が表示される
  - `helix agent stats` で並列度時系列・累積 cost が可視化される
  - V-model 4 artifact 双方向 trace 完備 (D-DB EXT / 実装 / test-design / test-code)
  - pytest / bats 全回帰 PASS
---

# PLAN-078: Agent Slot 管理 (helix.db v28 + 並列実行可視化)

## §1 背景

### 1.1 本セッション (2026-05-17) で観察されたトラブル

PLAN-075 Phase 2-3 完遂中、以下の並列実行関連の課題が顕在化した:

| 観察事象 | 影響 | 既存 機構の不在 |
|---|---|---|
| Codex 4 並列投入後、--wbs-id validation で全 reject (4 並列無駄打ち) | cost / 時間ロス | 起動前 / 起動後の状態記録なし |
| Codex background process の release タイミング検出 | release 漏れの可能性 | start のみ記録、end の保証なし |
| 並列度ピーク時の cost 集計 | budget 把握難 | session_telemetry は session 単位、agent invocation 単位は別軸 |
| 8 並列ルール遵守率 (CLAUDE.md) | 直列化怠慢の検出 | 機械測定なし |

### 1.2 helix.db 設計思想との整合

helix.db は元来 **依存関係 / trouble-shoot 集約** を目的に設計されている (PLAN-027 entries/links、PLAN-069 二重らせん)。本 PLAN は record strand (各 db event 累積) を **agent invocation 粒度** に拡張する。

```
artifact strand (PLAN-027 entries)
     ↕
record strand (本 PLAN agent_slots ← 新規)
```

### 1.3 既存 table との境界

| table | 粒度 | 用途 |
|---|---|---|
| automation_runs | HTTP push/pr/hook trigger 単位 | 業務処理の run 記録 |
| audit_log | event 単位 | 監査 / 改ざん検知 |
| session_telemetry | session 単位 (UPSERT) | Stop hook 由来の累積 telemetry |
| **agent_slots (本 PLAN)** | **agent invocation 単位** | **並列実行の slot 管理** |

automation_runs は HTTP endpoint 経由の業務 run、agent_slots は Opus / Codex / subagent の起動単位 (内部実装層) で粒度が異なる。両者は `parent_invocation_id` / `automation_run_id` FK で連結可能。

## §2 V-model 4 artifact (PLAN-075 準拠)

本 PLAN は PLAN-075 で確立した V-model 4 artifact 双方向 trace 原則を **自身に適用** する (PLAN-074 retrofit の延長)。

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 (詳細) | L3 詳細設計 | docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §10 agent_slots（D-DB EXT へ転記済み） |
| ② 実装コード | L4 実装 | cli/lib/agent_slots.py + cli/helix-agent + cli/helix-codex 統合 |
| ③ テスト設計 (結合) | L4 設計 | docs/v2/L4-test-design/PLAN-078-integration-test-design.md |
| ③ テスト設計 (単体) | L4 設計 | docs/v2/L4-test-design/PLAN-078-unit-test-design.md |
| ④ テストコード | L4 実装 | cli/lib/tests/test_agent_slots*.py |

## §3 schema 設計 (v28)

### 3.1 agent_slots table

```sql
CREATE TABLE agent_slots (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    invocation_id        TEXT NOT NULL UNIQUE,           -- 自動生成 UUID
    agent_kind           TEXT NOT NULL,                  -- codex / claude_subagent / agent_tool / opus_self
    role                 TEXT NOT NULL,                  -- tl / se / pe / qa / docs / pmo-sonnet / pdm-* 等
    model                TEXT,                           -- gpt-5.4 / gpt-5.5 / claude-opus-4-7 / claude-sonnet-4-6 等
    status               TEXT NOT NULL DEFAULT 'running', -- running / completed / failed / timed_out / cancelled
    started_at           TEXT NOT NULL,                  -- ISO8601 UTC
    completed_at         TEXT,                           -- ISO8601 UTC、status 遷移時に記録
    duration_ms          INTEGER,                        -- completed_at - started_at の派生値
    parent_invocation_id TEXT,                           -- FK 自己参照、tree 表現 (NULL = root)
    plan_id              TEXT,                           -- 関連 PLAN-XXX (任意)
    wbs_id               TEXT,                           -- 関連 WBS-XXX (任意)
    task_summary         TEXT,                           -- 1 行要約 (検索 / 表示用)
    prompt_hash          TEXT,                           -- SHA256 (内容 reference、prompt 全文は保存しない)
    tokens_input         INTEGER,                        -- Codex / Claude API 完了時に記録
    tokens_output        INTEGER,
    cost_usd             REAL,                           -- 完了時に集計 (Codex は --cost 経由)
    automation_run_id    INTEGER,                        -- FK automation_runs.id (HTTP endpoint 経由起動の場合)
    error_kind           TEXT,                           -- failed/timed_out 時の分類 (rate_limit / sandbox / output_truncated 等)
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (parent_invocation_id) REFERENCES agent_slots(invocation_id),
    FOREIGN KEY (automation_run_id) REFERENCES automation_runs(id)
);

CREATE INDEX idx_agent_slots_status ON agent_slots(status);
CREATE INDEX idx_agent_slots_started_at ON agent_slots(started_at);
CREATE INDEX idx_agent_slots_parent ON agent_slots(parent_invocation_id);
CREATE INDEX idx_agent_slots_plan ON agent_slots(plan_id);
```

### 3.2 状態遷移

```
running ──┬─→ completed (正常終了)
          ├─→ failed (exit != 0)
          ├─→ timed_out (起動から X 分 release されない、Phase 1 では検出のみ)
          └─→ cancelled (Ctrl+C 等、ユーザー中断)
```

Phase 1 スコープでは `timed_out` 自動遷移は実装せず、`helix agent slots --stale` で 5 分以上 running の slot を一覧表示する read-only 機能のみ。

## §4 fire / release 統合点

### 4.1 helix-codex 統合 (Phase 1 主スコープ)

```bash
# cli/helix-codex の wrap (擬似コード)
slot_id=$(helix-agent fire \
  --agent-kind codex \
  --role "$ROLE" \
  --model "$MODEL" \
  --plan-id "$PLAN_ID" \
  --wbs-id "$WBS_ID" \
  --task-summary "$TASK_SUMMARY_FIRST_LINE")

trap "helix-agent release --slot-id $slot_id --status cancelled" INT TERM
( codex exec ... ) && status=completed || status=failed
helix-agent release --slot-id $slot_id --status $status \
  --tokens-input $TOK_IN --tokens-output $TOK_OUT --cost-usd $COST
```

### 4.2 Agent tool 統合 (Opus 自身が CLI 規約)

```python
# Opus が Agent tool 呼び出し前に CLI fire、戻り値 invocation_id を覚える
# 完了通知後に release
helix agent fire --agent-kind claude_subagent --role pmo-sonnet --plan-id PLAN-075 --task-summary "..."
# → invocation_id 出力
# (Agent tool 実行)
helix agent release --slot-id <id> --status completed
```

Phase 1 では PreToolUse hook 自動統合は **carry**。Opus 規約遵守に依存する。

### 4.3 Stop hook 連携 (release 漏れ対策の補助)

セッション終了時の Stop hook で「running 状態の slot」を `cancelled` に自動遷移する safety net。詳細は §6 Phase 2 で。

## §5 CLI コマンド (Phase 1 スコープ)

### 5.1 `helix agent fire` / `helix agent release` (内部 API)

主に helix-codex から呼ばれる。手動運用も可能。

### 5.2 `helix agent slots`

```
helix agent slots [--active|--stale|--all] [--plan-id PLAN-XXX] [--since 1h] [--json]
```

例:
```
$ helix agent slots --active
INVOCATION                          AGENT     ROLE         STATUS    STARTED_AT          PLAN/WBS
9f3a1b2c-...  codex                gpt-5.4 se   running   2026-05-17 01:55:12  PLAN-075/WBS-075-P3-007
a7e8c4d5-...  claude_subagent      pmo-sonnet   running   2026-05-17 01:56:03  PLAN-075/WBS-075-P3-001
```

### 5.3 `helix agent stats`

```
helix agent stats [--days 7] [--by agent_kind|role|plan_id|hour] [--json]
```

例:
```
$ helix agent stats --days 1 --by hour
HOUR                  TOTAL  PEAK_PARALLEL  AVG_DURATION_S  TOTAL_COST_USD
2026-05-17 00:00      12     3              45.2            0.34
2026-05-17 01:00      18     5              68.7            0.52
2026-05-17 02:00      24     8              52.1            0.71
```

`PEAK_PARALLEL` が CLAUDE.md「default 8 並列」ルールの遵守率測定指標になる。

## §6 Phase 構成

| Phase | スコープ | size | Gate |
|---|---|---|---|
| **Phase 1 (本 PLAN)** | 記録 + 可視化のみ (block / warning なし) | M | G4 |
| Phase 2 (carry) | 上限超過 warning + stale slot 自動 timeout 遷移 + PreToolUse hook 統合 | M | 別 PLAN |
| Phase 3 (carry) | block / queue 化 (上限超過時の自動 deferral) | L | 別 PLAN |

block / queue は誤検知時の事故が大きいので、Phase 1 の運用データを 1-2 週間集めてから判断する。

## §7 受入条件 (Phase 1)

- [ ] helix.db v28 migration で `agent_slots` table 追加、`SCHEMA_VERSION = 28` 反映
- [ ] cli/lib/agent_slots.py (fire / release / list / stats の Python helper) 実装
- [ ] cli/helix-agent CLI (Bash wrapper) 実装
- [ ] cli/helix-codex に fire / release 統合 (--no-record で opt-out 可能)
- [ ] `helix agent slots --active` / `--stale` / `--all` 動作確認
- [ ] `helix agent stats --by hour` で並列度時系列出力
- [ ] V-model 4 artifact 完備 (本 PLAN 自身に PLAN-075 原則適用):
  - ① D-DB EXT に agent_slots schema 記載
  - ③ PLAN-078-unit-test-design.md + integration-test-design.md 新規
  - ④ test_agent_slots*.py 新規 (pytest 全 PASS)
- [ ] pytest / bats 全回帰 PASS
- [ ] helix doctor 影響なし

## §8 リスク

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | helix-codex wrap で既存 Codex 起動経路に副作用 | 既存 PLAN 群の進行が止まる | --no-record で opt-out、回帰テスト必須、段階導入 (まず helix-codex のみ、CLI 別経路は Phase 2 carry) |
| R-02 | background process の release 漏れ | running 状態の slot が増殖 | trap + Stop hook + stale 検出で 3 層防御 |
| R-03 | helix.db 書き込み競合 | 並列 fire で race condition | 既存 lock 機構 (PLAN-038/042/045) 活用、agent_slots INSERT は短時間 |
| R-04 | invocation_id 採番衝突 | 同一 ID で 2 slot | UUID v4 採番、UNIQUE 制約で fail-fast |
| R-05 | Opus 規約遵守失敗 (Agent tool で fire/release 打ち忘れ) | 統計から欠落 | Phase 1 では受容、Phase 2 で PreToolUse hook 自動統合 |
| R-06 | task-plan.yaml の WBS と agent_slots の wbs_id 不一致 | trace 断絶 | helix-codex --wbs-id 経路は agent_slots にも wbs_id 自動転記 ([[helix-codex-wbs-reference-doc]] と整合) |

## §9 依存

- PLAN-075 Phase 4-5 と **独立並行可能** (ファイル衝突なし、scope 別軸)
- PLAN-027 entries/links 基盤を前提 (既に v23 で確立済)
- helix.db v27 → v28 migration (PLAN-074 v27 完遂が前提、達成済)

## §10 Sprint 構成 (HELIX 標準粒度準拠)

| Sprint | 内容 | role | 並列 | estimate |
|---|---|---|---|---|
| .1a | 既存実装調査 (helix.db schema / helix-codex / pmo-project-explorer 委譲) | pm | 単独 | 15 |
| .1b | D-DB EXT §X agent_slots schema 設計 + state-machine | pm/tl | 単独 | 20 |
| .2a | D-DB EXT §X 起票 (cli/helix-codex --role docs) | docs | 単独 | 25 |
| .2b | ③ test-design (unit + integration) 起票 (Codex docs 2 並列) | docs | 2 並列 | 40 |
| .3a | v28 migration スクリプト + agent_slots.py 実装 | se | 単独 | 40 |
| .3b | cli/helix-agent CLI 実装 + helix-codex wrap | se | .3a 完了後 | 30 |
| .4 | ④ test 実装 (unit + integration、Codex pg 2 並列) | qa/pg | 2 並列 | 50 |
| .5 | 4 artifact 双方向 trace 確認 + 全回帰 + helix doctor | pm | 単独 | 20 |
| .6 | commit + push (Phase 1 完遂) | pm | 単独 | 5 |

**total estimate**: 約 245 分 (size M 上限近く、Sprint 分割で吸収)

## §11 Next Action

1. **本 commit**: PLAN-078 draft 起票のみ
2. **次セッション以降**: Sprint .1a から段階実装
3. **Phase 4-5 (PLAN-075 残) と並行**: ファイル衝突なし、独立 scope
