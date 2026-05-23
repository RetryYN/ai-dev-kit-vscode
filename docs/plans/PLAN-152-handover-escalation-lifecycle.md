---
plan_id: PLAN-152
title: "PLAN-152: handover ESCALATION lifecycle 自動化 (Codex → Opus 復帰時の auto-resume + 学習)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — auto-resume 設計 adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — handover schema 整合チェック (PLAN-128 との差分確認)"
  - role: se
    slot_label: "SE — SessionStart hook 拡張 + helix handover resume 修正 + helix.db migration"
  - role: qa
    slot_label: "QA — escalation lifecycle 結合テスト"
generates:
  - artifact_path: .claude/hooks/session-start-escalation-notify.sh
    artifact_type: hook
  - artifact_path: cli/helix-handover
    artifact_type: cli_extension
  - artifact_path: cli/lib/handover_escalation.py
    artifact_type: python_module
  - artifact_path: cli/lib/migrations/v36_escalation_log.py
    artifact_type: schema_migration
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-128
    - PLAN-129
  blocks: []
related_plans:
  - PLAN-128
  - PLAN-129
related_adr:
  - ADR-022-todowrite-agent-slot-framework-snapshot
reference_docs:
  - docs/plans/PLAN-128-handover-schema-enhancement.md
  - docs/plans/PLAN-129-pmo-sonnet-stuck-recovery.md
  - helix/HELIX_CORE.md
---

# PLAN-152: handover ESCALATION lifecycle 自動化 (Codex → Opus 復帰時の auto-resume + 学習)

## 0. 起票背景

`.helix/handover/ESCALATION.md` は Codex セッションでエスカレーション発生時に Opus (PM) へ返す通知ファイルであり、現状の復帰フローは以下のように手動工程が多い。

```
[Codex] helix handover escalate → ESCALATION.md 生成
[人間]  Opus セッション起動
[人間]  helix handover status を手動確認
[Opus]  ESCALATION.md を手動 Read → 対応判断
[Opus]  helix handover update --status in_progress --owner opus を手動実行
```

HELIX CODEX_TL_MODE.md §Handover 継続モード で定義された escalation 経路が、SessionStart 自動通知・TodoWrite 自動 populate・履歴学習のいずれも未実装のため復帰漏れや対応遅延が生じている。本 PLAN はこれら 3 点を自動化する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| PagerDuty Incident Response Guide | https://response.pagerduty.com/ | escalation → acknowledge → resolve ライフサイクルの設計根拠 |
| Atlassian Incident Management | https://www.atlassian.com/incident-management/on-call/escalation-policies | escalation policy + auto-notify pattern の業界標準 |
| Claude Code hooks SessionStart reference | https://docs.anthropic.com/claude-code/hooks | SessionStart hook でのセッション開始時状態チェック実装根拠 |
| HELIX handover resume (既存実装) | cli/helix-handover | 既存 resume command の拡張点特定 |
| SQLite Event Sourcing pattern | https://www.sqlite.org/wal.html | helix.db への escalation_log 追記の耐障害性根拠 |

## 2. 前提 + スコープ

- PLAN-128 (handover schema 強化) が前提。escalation_log テーブルは PLAN-128 の schema を拡張する形で追加する
- PLAN-129 (stuck recovery) で確立した `helix handover resume` の挙動を本 PLAN で拡張する
- PLAN-147 (pattern recommender) は不在のため学習連携は本 PLAN scope に含めず carry とする
- SessionStart hook は fail-open 設計 (重い処理は background に逃がす)
- auto-resume は **TodoWrite への populate のみ** — 実装着手は必ず PM (Opus) の明示承認を要する

## 3. 受入条件

- AC-152-01: SessionStart 時に `.helix/handover/ESCALATION.md` が存在する場合、stdout へ通知メッセージが出力されること (fail-open: ESCALATION.md 不在時はサイレント)
- AC-152-02: `helix handover resume --from-escalation` で ESCALATION.md の内容を TodoWrite 形式に変換して出力し、PM が承認後に TodoWrite へ渡せること
- AC-152-03: escalation → resume → in_progress 遷移が helix.db `escalation_log` に記録されること
- AC-152-04: escalation 履歴が `helix handover escalation-history [--json]` で参照できること
- AC-152-05: SessionStart hook が ESCALATION.md 不在時に 100ms 以内に終了すること (performance guard)

## 4. Phase 設計

### Phase 1: SessionStart 自動通知 hook

#### 目的
- Opus セッション開始時に ESCALATION.md の存在を自動検出し、対応忘れを防ぐ

#### 実装
```bash
# .claude/hooks/session-start-escalation-notify.sh
# - ESCALATION.md 存在チェック (< 50ms)
# - 存在する場合: 通知メッセージを stdout へ出力
# - 不在の場合: silent exit 0 (fail-open)
```

#### acceptance criteria
- ESCALATION.md あり → セッション開始メッセージに escalation サマリ (task_id / reason 1 行) を表示
- ESCALATION.md なし → hook が 100ms 以内に exit 0
- hook が重くなった場合に background 移行できる設計にする

### Phase 2: `helix handover resume --from-escalation` 拡張

#### 目的
- ESCALATION.md → TodoWrite 形式変換を自動化し、PM の手動 Read 時間を削減

#### 実装
- `cli/lib/handover_escalation.py` に escalation_to_todowrite_items() 関数を追加
- `helix handover resume` が `--from-escalation` オプション時に:
  1. ESCALATION.md をパース
  2. Next Action / context / reason を TodoWrite 候補 list に変換
  3. dry-run 形式で stdout 出力 (PM 承認後に実行)
- 自動 TodoWrite 書き込みは **しない** — PM 明示承認フローを維持

#### acceptance criteria
- ESCALATION.md の `reason` / `context` / `next_steps` が TodoWrite content に変換されること
- `--dry-run` (default) では TodoWrite 書き込みが発生しないこと
- `--apply` フラグで PM 承認後に TodoWrite 実行すること

### Phase 3: helix.db escalation_log + history CLI

#### 目的
- escalation → resume → in_progress → resolved の lifecycle を DB に蓄積し、パターン分析基盤を作る

#### schema

```sql
CREATE TABLE IF NOT EXISTS escalation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    escalated_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    context TEXT,
    owner_at_escalation TEXT NOT NULL DEFAULT 'codex',
    resumed_at TEXT,
    resolved_at TEXT,
    status TEXT NOT NULL CHECK(status IN (
        'pending', 'acknowledged', 'in_progress', 'resolved', 'abandoned'
    )),
    session_id TEXT,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_escalation_log_task_status
  ON escalation_log(task_id, status);
```

#### CLI
```
helix handover escalation-history [--task-id TASK_ID] [--status STATUS] [--json] [--limit N]
```

## 5. 実装ファイル構成

| ファイル | 役割 |
|---|---|
| `.claude/hooks/session-start-escalation-notify.sh` | SessionStart hook、ESCALATION.md 検出通知 |
| `cli/lib/handover_escalation.py` | escalation_to_todowrite_items() / escalation_log CRUD |
| `cli/helix-handover` | resume --from-escalation / escalation-history 拡張 |
| `cli/lib/migrations/v36_escalation_log.py` | escalation_log テーブル追加 migration |

## 6. TodoWrite populate 設計 (自動化上限)

HELIX discipline で「承認なし task pop は Plan Consent を超える」(V5 TL v5 P0 指摘) ため、自動化の上限を明示する:

| 操作 | 自動化 | 理由 |
|---|---|---|
| ESCALATION.md 検出 + 通知 | O (SessionStart hook) | read-only、承認不要 |
| TodoWrite 候補生成 (dry-run) | O (--from-escalation) | 生成のみ、書き込みなし |
| TodoWrite 書き込み | X (--apply は PM 明示後のみ) | Plan Consent 必須 |
| helix handover update --owner opus | X (PM 手動) | 所有権移転は PM 判断 |

## 7. リスク

- R-152-01: SessionStart hook が重くなりセッション開始遅延を引き起こす
  - 対応: Phase 1 を fail-open 設計、ESCALATION.md チェックのみ (stat コール 1 回) に限定
- R-152-02: PLAN-128 の schema と escalation_log が競合する
  - 対応: PLAN-128 実装後に migration 番号 (v36?) を確定、事前に helix.db 最新 version を確認する
- R-152-03: --apply フラグを PM 以外が誤使用する
  - 対応: --apply 実行時に `HELIX_ESCALATION_APPLY_APPROVED=1` env を必須化 (pretooluse hook で guard)
- R-152-04: escalation_log への記録漏れで lifecycle が追跡不能になる
  - 対応: ESCALATION.md 存在時に escalation_log へ行を INSERT する SessionStart hook 内処理を fail-open で追加

## 8. carry list

- [ ] PLAN-147 (pattern recommender) 起票後に escalation_log → 学習 pipeline 接続
- [ ] PLAN-128 schema version 確定後に migration 番号を v36? → 正式番号へ更新
- [ ] --apply フラグの pretooluse guard hook 実装 (HELIX_ESCALATION_APPLY_APPROVED=1 必須化)
- [ ] escalation-history の出力形式を helix handover status --json と統一

## 9. V-model 4 artifact trace

| 層 | 対応 |
|---|---|
| 設計 | `docs/plans/PLAN-152-handover-escalation-lifecycle.md` (本 file) |
| 実装 | `cli/lib/handover_escalation.py`, `cli/helix-handover`, `cli/lib/migrations/v36_escalation_log.py`, `.claude/hooks/session-start-escalation-notify.sh` |
| テスト設計 | §3 受入条件 AC-152-01〜05 |
| テストコード | `cli/lib/tests/test_handover_escalation.py` (実装 Sprint で起票) |

## 10. 完了基準

1. SessionStart hook が ESCALATION.md 検出時に 1 行通知を出力し、不在時は 100ms 以内に silent exit すること
2. `helix handover resume --from-escalation --dry-run` が TodoWrite 候補 list を stdout に出力すること
3. helix.db `escalation_log` migration が idempotent で適用されること
4. `helix handover escalation-history` が直近 10 件を正しく返すこと
5. 上記 AC-152-01〜05 がすべて pytest で検証されること

## 11. 関連 memory

- [[feedback_dont_stop_with_carry_remaining]] (lifecycle 自動化による中断防止)
- [[feedback_no_user_ask_tl_advisor_self_drive]] (TL 相談で設計判断)
- [[project_2026_05_23_session_handover]] (本 session の carry list 確認)
