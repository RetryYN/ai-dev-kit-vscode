---
plan_id: PLAN-080
title: "PLAN-080: Harness Dynamic Monitoring (3 軸 Pull/Push/Audit による Opus 制御 harness 強化)"
status: completed
size: M
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-078 (agent slot v28、本 PLAN は v30、上層 monitoring layer)
  - PLAN-079 (UPS + SRF chain、本 PLAN は metric 取得対象)
  - PLAN-075 (V-model 4 artifact、本 PLAN にも適用)
  - PLAN-027 (helix.db entries/links、harness event 記録の基盤)
trigger: |
  2026-05-17 PLAN-075 Phase 4-5 進行中のユーザー指摘:
  「スロット状況を動的にチェックする管理する方法は？ヘリックス自体の動きとかも
    忘れて進められがちだし、そこがハーネスとして重要な気がするんだけど？」

  本セッションで顕在化した「ヘリックス自体の動きを忘れる」事例:
  - 1 並列で済ませた怠慢 (ユーザー指摘で発覚)
  - pmo-sonnet で 8 PLAN 一括 audit を試み tool_uses 上限破綻
  - skill chain (推挙システム) の呼び忘れ (PLAN-075 Phase 2 開始時)
  - helix codex --wbs-id の reference-doc 必須性を忘れて 4 並列 reject

  これらは Opus 個人の判断ループに dynamic feedback がないことが原因。
  Pull (たまに helix doctor で確認) しかなく、Push (適切タイミング自動警告) がない。
acceptance:
  - 3 軸 (Pull / Push / Audit) で dynamic check 機構が実装される
  - `helix harness status` で現状 (active slot + 走行中 task + 未消化 deferred-findings + skip した skill chain) を pull で取得可能
  - PreToolUse hook で Codex / Agent 呼び出しを捕捉し、現状 slot 数 + 8 並列遵守率 + 独立判定リマインダーを system-reminder で push
  - SessionStart hook で前 session の release 漏れ + carry findings summary を表示
  - helix.db v30 に harness_check_events table 追加 (audit_log 拡張ではなく独立 table、PLAN-078 v28 / PLAN-079 v29 の次)
  - V-model 4 artifact 双方向 trace 完備
  - pytest / bats 全回帰 PASS
---

# PLAN-080: Harness Dynamic Monitoring

## §1 背景

### 1.1 現状 framework の構造的問題

HELIX framework は「Opus を制御する harness」として設計されているが、現状以下が欠落:

| 機能 | Pull (たまに確認) | Push (タイミングで自動警告) | Audit (session 単位 summary) |
|---|---|---|---|
| Agent slot 状況 | ❌ なし (PLAN-078 で予定) | ❌ なし | ❌ なし |
| 走行中 task 一覧 | △ ad-hoc Bash | ❌ なし | ❌ なし |
| 未消化 deferred-findings | △ ad-hoc Read | ❌ なし | ❌ なし |
| skip した skill chain | ❌ なし | ❌ なし | ❌ なし |
| 8 並列遵守率 | ❌ なし | ❌ なし | ❌ なし |
| Helix flow 逸脱 (--wbs-id reject 等) | ❌ なし | ❌ なし | ❌ なし |

### 1.2 本セッションで観察された逸脱事例

| 事例 | 検出機構 | 検出タイミング | あるべき機構 |
|---|---|---|---|
| 1 並列怠慢 (Codex 1 つしか走らせない) | ユーザー指摘 | 30 分後 | Push: PreToolUse hook で 8 並列遵守率を inject |
| pmo-sonnet 8 PLAN 一括 audit が tool_uses 上限破綻 | Codex 内部 | 2 分後 (turn 返却) | Push: Agent 呼び出し時 expected tool_uses を予告 |
| skill chain 呼び忘れ | 自己反省 | 数 turn 後 | Audit: SessionStart で「前 session で skill chain N 回 skip」 |
| --wbs-id reject (4 並列無駄打ち) | Codex stderr | 起動直後 | Push: helix codex 起動時に --reference-doc 推奨 reminder |

### 1.3 harness としての位置付け

「Opus を制御する harness」= Claude Code 実行環境が Opus の判断ループに metadata を inject する仕組み。既存:
- `.claude/hooks/pretooluse-opus-repo-block.sh` (Opus repo Edit を機械 block)
- `.claude/hooks/post-tool-use.sh` (audit_log 書き込み)
- `.claude/hooks/stop.sh` (session_telemetry UPSERT)
- SessionStart hook (HELIX 状態 inject、本セッション冒頭で観察)

これらは限定的。本 PLAN で 3 軸 dynamic check に拡張。

## §2 V-model 4 artifact (PLAN-075 準拠)

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | docs/v2/L3-detailed-design/D-DB/D-DB-EXTENDED-draft.md §13 harness_check_events |
| ② 実装コード | L4 実装 | cli/lib/harness_monitor.py + cli/helix-harness + .claude/hooks/pretooluse-codex-slot-check.sh + .claude/hooks/sessionstart-harness-summary.sh |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-080-unit-test-design.md + docs/v2/L4-test-design/PLAN-080-integration-test-design.md |
| ④ テストコード | L4 実装 | cli/lib/tests/test_harness_monitor_unit.py + cli/lib/tests/test_harness_monitor_integration.py + tests/harness-hooks.bats |

## §3 3 軸設計

### 3.1 Pull: `helix harness status`

オンデマンドで現状取得。Opus が判断に迷ったとき / セッション開始時に手動実行。

```
$ helix harness status
=== Harness Status (2026-05-17 03:35) ===

[Active Slots] (PLAN-078 統合、v28 待ち)
  9f3a1b2c codex pg PLAN-075/WBS-075-P3-007 running 2m38s
  a7e8c4d5 claude_subagent pmo-sonnet PLAN-075 running 12s

[Running Background Tasks] (Bash run_in_background)
  barho97up T503 vmodel_lint impl (started 8m12s ago, expected ~10min)
  b6xj7e4ce PLAN-078 .1b D-DB EXT (started 3m05s ago)

[8 並列遵守率 (現セッション)]
  peak_parallel=4 (default 上限 8 に対し 50%)
  serial_ratio=0.65 (改善余地)

[未消化 Deferred Findings] (open, severity >= medium)
  DF-PLAN-068-AUDIT-001 (test-code docstring 追記、carry)
  DF-PLAN-072-AUDIT-001 (実装系で ③ 不在、別 PLAN 待ち)

[skip した Skill Chain (現セッション)]
  L4 Phase 2 開始時に helix skill chain 呼び忘れ (1 回)

[最近の逸脱イベント]
  2026-05-17 02:00 helix codex --wbs-id reject (4 並列無駄打ち、--reference-doc 不足)
  2026-05-17 02:15 pmo-sonnet tool_uses 上限 (8 PLAN 一括 audit 試行)
```

### 3.2 Push: PreToolUse hook で system-reminder inject

`.claude/hooks/pretooluse-codex-slot-check.sh` (新規):
- Bash tool 呼び出しを捕捉
- `helix-codex` または `helix codex` を含む場合:
  - 現在 active slot 数を `helix harness status --json` で取得
  - 8 並列遵守率を計算
  - `--wbs-id` 引数が含まれるが `--reference-doc` がない場合は警告
  - 結果を stderr / system-reminder で Opus に push

```bash
# 擬似コード
if [[ "$TOOL_NAME" == "Bash" && "$TOOL_INPUT" == *"helix codex"* ]]; then
  active=$(helix harness status --json | jq '.active_slot_count')
  if [[ "$active" -ge 6 ]]; then
    cat <<EOF >&2
<system-reminder>
警告: 現在 active slot=$active、8 並列ルールに近い。
新規 Codex 投入前に依存判定を再確認してください。
EOF
  fi
  if [[ "$TOOL_INPUT" == *"--wbs-id"* && "$TOOL_INPUT" != *"--reference-doc"* ]]; then
    cat <<EOF >&2
<system-reminder>
警告: --wbs-id 指定時は --reference-doc も必要 (helix codex は task-plan.yaml を lookup 対象外)。
EOF
  fi
fi
```

### 3.3 Audit: SessionStart hook + Stop hook

`.claude/hooks/sessionstart-harness-summary.sh` (新規、既存 SessionStart hook 拡張):
- 前 session の `harness_check_events` から逸脱イベント / skill chain skip / stale slot を集計
- summary を session 開始時の system context に inject

`.claude/hooks/stop.sh` 既存に追加:
- stale slot (5 分以上 release されない agent_slots) 検出 → `harness_check_events` に INSERT
- 現セッションの逸脱イベント集計を `harness_check_events` に保存

## §4 helix.db schema (v30)

PLAN-078 v28 + PLAN-079 v29 の次:

```sql
CREATE TABLE harness_check_events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    event_kind        TEXT NOT NULL,    -- 'slot_overflow' / 'wbs_reject' / 'skill_chain_skip' / 'tool_uses_overflow' / 'stale_slot' / 'session_summary'
    severity          TEXT NOT NULL DEFAULT 'info', -- info / warning / error
    session_id        TEXT,
    related_slot_id   INTEGER,           -- FK agent_slots.id (PLAN-078)
    related_plan_id   TEXT,
    related_wbs_id    TEXT,
    metric_value      REAL,              -- 並列度 / 遵守率 / etc
    detail            TEXT,              -- 1 行サマリ
    payload           TEXT,              -- JSON で context (任意)
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (related_slot_id) REFERENCES agent_slots(id)
);

CREATE INDEX idx_harness_events_kind ON harness_check_events(event_kind);
CREATE INDEX idx_harness_events_session ON harness_check_events(session_id);
CREATE INDEX idx_harness_events_severity ON harness_check_events(severity);
```

## §5 Phase 構成

| Phase | スコープ | size | Gate |
|---|---|---|---|
| **Phase 1** | Pull (helix harness status CLI) + helix.db v30 migration | M | G4 |
| Phase 2 | Push (PreToolUse hook 3 種、Codex/Agent 捕捉 + reminder inject) | M | 別 PLAN |
| Phase 3 | Audit (SessionStart + Stop hook 拡張、session 単位 summary) | S | 別 PLAN |

段階導入。Phase 1 で「現状取得」のみ可能化、Phase 2 で「自動警告」、Phase 3 で「session 単位記憶」と拡張。

## §6 受入条件 (Phase 1)

- [ ] helix.db v30 migration で harness_check_events table 追加
- [ ] cli/lib/harness_monitor.py + cli/helix-harness CLI 新規
- [ ] `helix harness status` で 3.1 のフォーマット出力可能
- [ ] V-model 4 artifact 完備 (PLAN-075 原則を自身に適用)
- [ ] pytest / bats 全回帰 PASS
- [ ] vmodel_lint で complete 判定

## §7 リスク

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | hook 増加で Claude Code 全体動作 latency 増加 | UX 低下 | hook 内処理は数 ms 以下、helix-codex CLI 呼び出しは async (background) |
| R-02 | system-reminder inject が頻繁すぎて Opus が無視するようになる | 警告無効化 | severity / threshold 制御、warning は 8 並列遵守率 < 50% 等の重要場面のみ |
| R-03 | PLAN-078 v28 / PLAN-079 v29 と FK 依存、順序依存 | 開発 timing 制約 | Phase 1 (v30 migration + Pull のみ) は agent_slots FK を nullable で実装可能、PLAN-078 完遂後に FK 制約有効化 |
| R-04 | session 概念が helix.db 内で曖昧 (PLAN-074 session_telemetry の session_id と整合) | データ不整合 | session_id は HELIX_SESSION_ID env で統一、既存 session_telemetry と同 source |

## §8 依存関係

- 並走可能: PLAN-078 Phase 1 (v28) / PLAN-079 Phase 1 (v29) / PLAN-080 Phase 1 (v30) — schema 番号は順序依存だが、それ以外の実装は独立
- 後続: Phase 2/3 で hook 実装、`.claude/hooks/` 拡張

## §9 Sprint 構成 (Phase 1)

| Sprint | 内容 | role | estimate |
|---|---|---|---|
| .1a | 既存 .claude/hooks/ 実装調査 + harness 設計議論 | pm | 20 |
| .1b | D-DB EXT §X harness_check_events 起票 | docs | 25 |
| .2 | ③ test-design (unit + integration) 起票 | docs | 40 |
| .3a | v30 migration + harness_monitor.py 実装 | se | 35 |
| .3b | cli/helix-harness CLI 実装 | se | 25 |
| .4 | ④ test 実装 | qa/pg | 45 |
| .5 | 4 artifact 確認 + 全回帰 | pm | 20 |
| .6 | commit + push | pm | 5 |

Phase 1 total estimate: 約 215 分 (size M)

## §10 Next Action

1. **本 commit**: PLAN-080 draft 起票のみ
2. **次セッション以降**: PLAN-078 / PLAN-079 と並行可能 (3 並列 scope)
3. **dogfooding**: 本 PLAN 完遂後、本 framework 拡張運用で skill chain skip / 並列怠慢が機械検出される
