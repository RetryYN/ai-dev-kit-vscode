---
plan_id: PLAN-129
title: "pmo-sonnet stuck 検出 + auto-recovery hook"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: "2026-05-23"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: se
    slot_label: "SE — agent_slot last_activity_timestamp 追跡 + stuck 判定 logic 実装 + migration"
  - role: pmo-sonnet
    slot_label: "PMO — hook 設計整合・helix.db schema 変更の既存 PLAN との drift 確認"
  - role: tl-advisor
    slot_label: "TL adversarial check — stuck 判定 threshold 設計・fallback 仕様レビュー"
  - role: qa
    slot_label: "QA — fake timeout fixture 4 scenario 検証・回帰テスト確認"
generates:
  - artifact_path: docs/plans/PLAN-129-pmo-sonnet-stuck-recovery.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-045-agent-stuck-detection-decision.md
    artifact_type: adr_snapshot
  - artifact_path: .claude/hooks/agent-stuck-recovery.sh
    artifact_type: hook
  - artifact_path: cli/lib/helix_db.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_stuck_recovery.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-088
  blocks: []
related_adr:
  - ADR-045 (本 PLAN の L2 snapshot、新 framework 採用)
related_plans:
  - PLAN-088 (TodoWrite × agent slot framework — agent_slots テーブル正本)
  - PLAN-099 (自動走行 framework 5-layer — statusLine + heartbeat と stuck 検出の協調)
---

# PLAN-129: pmo-sonnet stuck 検出 + auto-recovery hook

## L2 凍結 (ADR snapshot)

本 PLAN tree は **新規 stuck 検出 framework の採用** を含む。
`last_activity_timestamp` 追跡 + N 分閾値判定 + stale slot 自動 release + fallback 再投入は
既存 PLAN-088 (agent slot lifecycle) には明記されていない新規大局判断。

ADR-045 snapshot として別文書で凍結する。

根拠:
- 既存 agent_slots テーブルに `last_activity_timestamp` カラムが不在 (schema 拡張必要)
- stuck 判定閾値 (10 分) の設計は運用上の合意が必要
- auto-recovery の fallback 先選択 (retry / skip / escalate) はポリシー決定

## 背景

本 session 2026-05-23 で pmo-sonnet (drift audit、agent id a79db5318ed1341cb) が
**30+ 分応答なしで stuck** した事例が発生。SendMessage rapid scan rerun も同様の症状を示した。

具体的な問題:

1. stuck した agent が slot を保持したまま応答しないため、後続 task が blocked される
2. PM / 人間がモニタリングしていない場合、stuck が検出されずに長時間継続する
3. PLAN-099 の 5-layer framework (Layer 5 heartbeat) が carry check を行っても、
   agent slot が stale 状態のままでは再投入の判断ができない

CLAUDE.md の「stale slot」運用 (`helix agent slots release-stale`) は手動実行前提であり、
自動検出・自動 release の仕組みが不在。PLAN-088 の agent slot framework を拡張して
stuck 自動検出と recovery hook を整備する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部の agent slot lifecycle 拡張** であり、
外部ライブラリ / 業界 standard への新規依存なし。WebSearch **skip**。

skip 理由:
- stuck 検出ロジックは POSIX `date` + SQLite timestamp 比較で完結
- helix.db schema 拡張は PLAN-088/PLAN-092 の既存 migration 規約に準拠
- fallback 先選択は HELIX 内部ポリシー (PLAN-099 heartbeat / PLAN-088 slot lifecycle と整合)

## 設計方針

### 1. stuck 検出 logic (Sprint .1)

#### helix.db schema 拡張

`agent_slots` テーブルに `last_activity_timestamp` カラムを追加する (migration v36 相当)。

```sql
ALTER TABLE agent_slots
  ADD COLUMN last_activity_timestamp TEXT DEFAULT NULL;
```

- `last_activity_timestamp` は agent が tool call / 応答を発するたびに更新される
- 既存の `started_at` は agent 起動時刻の記録に留め、activity 追跡は新カラムで分離する

#### stuck 判定閾値

| パラメータ | 値 | 根拠 |
|---|---|---|
| `STUCK_THRESHOLD_MIN` | 10 分 | pmo-sonnet 通常タスク完了時間の 2-3 倍。30 分 stuck 事例の 1/3 |
| `STALE_THRESHOLD_MIN` | 60 分 | session 切断・crash 後の孤児 slot 回収目安 |
| check interval | heartbeat 周期に準拠 (PLAN-099) | 独立 polling 不要 |

判定 SQL:

```sql
SELECT slot_id, agent_id, role, started_at, last_activity_timestamp, task_description
FROM agent_slots
WHERE status = 'active'
  AND (
    last_activity_timestamp IS NOT NULL
    AND (strftime('%s', 'now') - strftime('%s', last_activity_timestamp)) > 600
  )
  OR (
    last_activity_timestamp IS NULL
    AND (strftime('%s', 'now') - strftime('%s', started_at)) > 600
  );
```

### 2. auto-recovery hook 実装 (Sprint .2)

#### hook 概要

`.claude/hooks/agent-stuck-recovery.sh`

- **hook type**: 定期実行 (cron / PLAN-099 heartbeat から呼び出し) または SessionStart
- **trigger**: `helix agent stuck check` CLI から呼び出す形式でも実行可能

#### recovery 3 段階ポリシー

| フェーズ | 条件 | アクション |
|---|---|---|
| **detect** | `last_activity_timestamp` が 10 分超過 | stuck candidate に mark、warn ログ出力 |
| **release** | detect 後 5 分経過 (合計 15 分) | `agent_slots.release_slot(status='stuck')` で自動 release |
| **fallback** | release 完了後 | task_description を元に同 role で再投入 (helix agent fire) または PM escalation |

fallback 先選択ロジック:

```bash
case "$RETRY_COUNT" in
  0) ACTION="retry"   ;;   # 初回: 同 role で再投入
  1) ACTION="escalate" ;;  # 2 回目: PM に escalation (ESCALATION.md 生成)
  *) ACTION="skip"    ;;   # 3 回目以上: skip + debt log
esac
```

`RETRY_COUNT` は `agent_slots` テーブルの `retry_count` カラムで追跡する。

#### helix agent CLI 拡張

```bash
helix agent stuck check         # stuck candidate 一覧表示
helix agent stuck release       # stuck slot を一括 release
helix agent stuck status        # 現在の stuck/stale slot サマリ
```

既存の `helix agent slots release-stale` との関係:
- `release-stale`: manual trigger、stale (60 分超) を対象
- `stuck check / release`: 自動 / 手動両対応、stuck (10-15 分) を対象

### 3. 検証 (Sprint .3)

4 scenario fixture で動作確認:

| scenario | 初期状態 | 期待結果 |
|---|---|---|
| `active_normal` | `last_activity` = 3 分前 | stuck 判定なし |
| `stuck_candidate` | `last_activity` = 11 分前 | detect 発火、warn log 出力 |
| `auto_released` | `last_activity` = 16 分前 | release 実行、status=stuck |
| `orphan_slot` | `started_at` = 70 分前、activity = NULL | stale 判定で release |

## 実装計画

### Sprint .1: stuck 検出 logic + DB schema (Codex se 委譲、size M)

**Entry 条件**: PLAN-088 status 確認 (agent_slots テーブル現状把握)

実施内容:

1. `cli/lib/helix_db.py` に `get_stuck_slots(threshold_sec)` + `mark_stuck(slot_id)` 追加
2. helix.db migration (v36 相当): `agent_slots` に `last_activity_timestamp` / `retry_count` 追加
3. `helix agent stuck check / release / status` CLI stub 実装
4. `python3 -m py_compile cli/lib/helix_db.py` PASS (mandatory in sprint)

受入条件:
- `get_stuck_slots(threshold_sec=600)` が正しい stuck slot を返す
- migration が idempotent (二重実行で error なし)
- `helix agent stuck check` が一覧を返す

### Sprint .2: auto-recovery hook 実装 (Codex se 委譲、size M)

**Entry 条件**: Sprint .1 migration PASS + `get_stuck_slots` 動作確認済

実施内容:

1. `.claude/hooks/agent-stuck-recovery.sh` 新規作成
   - stuck slot 取得 (`helix agent stuck check --json`)
   - release + fallback ポリシー適用 (retry_count 参照)
   - ESCALATION.md 生成 (retry_count >= 1 時)
2. `helix agent stuck release` CLI 本実装
3. `bash -n .claude/hooks/agent-stuck-recovery.sh` PASS (mandatory in sprint)
4. settings.json への登録 (SessionStart matcher)

受入条件:
- stuck slot が 15 分超で自動 release される
- retry_count=0 で同 role 再投入
- retry_count=1 で ESCALATION.md 生成

### Sprint .3: fixture 検証 (Codex qa 委譲、size S)

**Entry 条件**: Sprint .2 hook 実装完了

実施内容:

1. `cli/lib/tests/test_agent_stuck_recovery.py` 新規作成
   - 4 scenario fixture (fake timestamp 注入)
   - `datetime.now(timezone.utc)` ベースで動的 timestamp 生成 (固定値 flake 防止)
2. `python3 -m pytest cli/lib/tests/test_agent_stuck_recovery.py -v` 全 PASS

受入条件:
- 4 scenario 全 PASS
- flake なし (動的 timestamp 使用)

## DoD (Definition of Done)

- [ ] helix.db migration v36 相当が idempotent で PASS
- [ ] `get_stuck_slots` / `mark_stuck` / `release_slot` が正しく動作
- [ ] `.claude/hooks/agent-stuck-recovery.sh` bash -n PASS
- [ ] `helix agent stuck check / release / status` CLI 動作確認
- [ ] 4 scenario fixture テスト全 PASS
- [ ] ADR-045 snapshot 起票済
- [ ] `helix doctor` warn 増加なし

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| 誤検出 (正常 agent を stuck 判定) | 実行中タスクが中断 | detect → release の 5 分猶予 + warn log を PM 確認 |
| retry loop (stuck → 再投入 → 再 stuck) | 無限 retry | retry_count >= 2 で skip + debt log に転記 |
| migration 失敗 (本番 helix.db) | schema 不整合 | idempotent migration + rollback テスト必須 |
| ESCALATION.md 過多生成 | PM notification 埋没 | retry_count=1 のみ生成、0 は warn log のみ |
