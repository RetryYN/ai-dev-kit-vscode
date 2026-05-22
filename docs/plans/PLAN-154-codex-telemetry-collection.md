---
plan_id: PLAN-154
title: "PLAN-154: helix-codex telemetry collection (Codex 委譲統計の helix.db 記録)"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — codex_invocations schema 設計・task_hash 衝突回避 adversarial check"
  - role: se
    slot_label: "SE — helix-codex telemetry hook 実装・python_module 起草・v39 migration"
  - role: qa
    slot_label: "QA — pytest test 設計・exit_code / completion_time 境界テスト"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-134 metrics CLI との統合整合・helix doctor 統合確認"
generates:
  - artifact_path: cli/lib/codex_telemetry.py
    artifact_type: python_module
  - artifact_path: cli/lib/migrations/v39_codex_invocations.py
    artifact_type: schema_migration
  - artifact_path: cli/lib/tests/test_codex_telemetry.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-143
    - PLAN-134
  blocks: []
related_plans:
  - PLAN-134
  - PLAN-143
  - PLAN-137
related_adr: []
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-codex
  - docs/plans/PLAN-134-helix-metrics-cli.md
reference_docs:
  - docs/plans/PLAN-143-helix-db-v37-event-telemetry.md
  - docs/plans/PLAN-137-codex-approved-auto-flag.md
  - docs/plans/PLAN-134-helix-metrics-cli.md
acceptance_criteria:
  - "helix codex 呼び出し時に invocation_id / role / task_hash / start_at / completion_time / exit_code が helix.db codex_invocations table に記録される"
  - "helix metrics --codex が role 別実行回数・平均完了時間・sandbox fail 率を出力する"
  - "sandbox fail 率 > 30% で helix doctor が WARN を出力する"
  - "python3 -m py_compile cli/lib/codex_telemetry.py PASS"
  - "pytest test_codex_telemetry.py 全 PASS"
  - "v39 migration が既存 helix.db v37/v38 に対して idempotent に動作する"
  - "helix codex が telemetry 記録に失敗しても委譲処理自体は abort しない (fail-open)"
---

# PLAN-154: helix-codex telemetry collection (Codex 委譲統計の helix.db 記録)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 helix-codex への telemetry hook 追加** であり、新規の大局判断 (新 framework 採用 / fail-close 化) を含まない。ADR snapshot は不要。

根拠:
- codex_invocations table は既存 helix.db の append-only 追加のみ
- helix-codex への hook は既存 PostToolUse hook パターンに準拠
- helix metrics --codex は PLAN-134 の CLI extension 点に追加するのみ (新 CLI 不要)

## 0. 背景

本 session (2026-05-23) で sandbox fail が多発し、root cause 分析のためのデータが存在しないことが判明した。具体的には:

1. **sandbox fail の可視化不足**: Codex 委譲の exit_code 分布が追跡されていないため、`--approved` フラグ不在 / sandbox 設定 / role 別の fail パターンを定量的に把握できない
2. **委譲効率の改善余地**: role 別の平均完了時間が不明のため、PE (gpt-5.3-codex-spark) vs SE (gpt-5.4) の選択が感覚依存になっている
3. **PLAN-134 metrics との連携不足**: `helix metrics --codex` が PLAN-134 の metrics 体系に未統合のため、session 別の Codex 委譲コストが `carry_consumed` と紐付かない

`codex_invocations` table を helix.db v39 として新設し、helix-codex 呼び出し時に自動記録する。

## 1. 設計方針

### 1.1 アーキテクチャ

```
cli/helix-codex              bash dispatcher (既存)
  │  呼び出し前後に telemetry hook を追加
  └── cli/lib/codex_telemetry.py   Python ロジック
        ├── record_invocation()    開始時記録 (invocation_id 発行)
        ├── update_completion()    完了時記録 (exit_code / completion_time)
        └── get_stats()            集計クエリ (role 別 / period 別)

cli/helix-metrics (PLAN-134)
  └── --codex オプション追加   get_stats() を呼び出し表示
```

### 1.2 helix.db v39 schema

PLAN-143 (v37) / PLAN-153 (v38) の次として v39 migration を追加:

```sql
CREATE TABLE IF NOT EXISTS codex_invocations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    invocation_id    TEXT NOT NULL UNIQUE,  -- uuid4
    session_id       TEXT,                  -- helix session_id (NULL 許容)
    role             TEXT NOT NULL,         -- tl / se / pg / qa / security 等
    task_hash        TEXT,                  -- sha256(task_prompt)[:16]
    start_at         TEXT NOT NULL,         -- ISO8601 UTC
    completion_time  REAL,                  -- seconds (NULL = 未完了)
    exit_code        INTEGER,               -- 0=success / 1=fail / 2=sandbox_fail
    sandbox_mode     TEXT,                  -- "auto" / "approved" / "plan-only"
    model            TEXT,                  -- gpt-5.5 / gpt-5.4 等
    notes            TEXT                   -- エラーメッセージ先頭 256 chars
);
CREATE INDEX IF NOT EXISTS idx_codex_inv_role ON codex_invocations(role);
CREATE INDEX IF NOT EXISTS idx_codex_inv_start ON codex_invocations(start_at);
```

### 1.3 task_hash 設計

task prompt の sha256 先頭 16 chars を task_hash とする。目的:
- 同一タスクを retry した場合の識別
- PII / secret を DB に保存しない (hash のみ)
- 衝突確率は 16^16 ≒ 1.8e19 で実用上無視可能

### 1.4 helix-codex への hook 追加

既存 `cli/helix-codex` bash dispatcher に 2 箇所の telemetry call を追加:

```bash
# 呼び出し前
INVOCATION_ID=$(python3 -m cli.lib.codex_telemetry record_invocation \
    --role "$ROLE" --task-hash "$(echo "$TASK" | sha256sum | cut -c1-16)" \
    --sandbox-mode "$SANDBOX_MODE" --model "$MODEL" 2>/dev/null || true)

# 呼び出し後 (fail-open: telemetry 失敗は無視)
python3 -m cli.lib.codex_telemetry update_completion \
    --invocation-id "$INVOCATION_ID" --exit-code "$EXIT_CODE" \
    --completion-time "$ELAPSED" 2>/dev/null || true
```

`|| true` で telemetry 失敗を fail-open にする。

### 1.5 helix metrics --codex 統合

PLAN-134 の `helix metrics` CLI に `--codex` オプションを追加:

```bash
helix metrics --codex [--since YYYY-MM-DD] [--role tl|se|pg|...]

# 出力例 (text format)
Codex Invocations Summary (last 30 days)
  total:        42 invocations
  success rate: 78.6% (33/42)
  sandbox fail: 11.9% (5/42) ← > 30% で helix doctor WARN
  avg time:     127.3 sec

By role:
  se:  18 invocations, avg 143s, fail 16.7%
  tl:   9 invocations, avg 198s, fail  0.0%
  pg:  12 invocations, avg  72s, fail 16.7%
  qa:   3 invocations, avg  88s, fail  0.0%
```

### 1.6 helix doctor 統合

`helix doctor` に `check_codex_sandbox_fail_rate` を追加:

- sandbox fail 率 > 30%: WARN (原因特定を促す)
- sandbox fail 率 > 60%: FAIL (--approved 設定確認を要求)
- 直近 7 日間のデータが 0 件: INFO (telemetry 未記録の通知)

## 2. L4 実装 Sprint 計画

### Sprint .1: codex_telemetry.py skeleton + v39 migration

- Entry: PLAN-143 v37 / PLAN-153 v38 migration 完了確認
- 実装: cli/lib/codex_telemetry.py (record_invocation / update_completion / get_stats)
- 実装: cli/lib/migrations/v39_codex_invocations.py
- チェック: py_compile PASS / migration idempotent 確認
- Exit: `python3 -m cli.lib.codex_telemetry record_invocation --role tl ...` が DB に記録する

### Sprint .2: helix-codex hook 追加

- 実装: cli/helix-codex に telemetry call 2 箇所追加 (fail-open)
- bats smoke test (helix codex --dry-run で invocation 記録を確認)
- Exit: `helix codex --role tl --task "test" --dry-run` 後に `codex_invocations` に 1 件記録

### Sprint .3: helix metrics --codex + helix doctor 統合

- 実装: PLAN-134 cli/helix-metrics に --codex オプション追加
- 実装: helix doctor check_codex_sandbox_fail_rate
- Exit: pytest test_codex_telemetry.py 全 PASS / helix doctor 統合動作確認

### Sprint .4: レビュー + ドキュメント整合

- セルフレビュー + pmo-sonnet review
- docs/commands/index.md に helix metrics --codex 追加
- task_hash の PII 非保存設計を security review で確認

## 3. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| v39 migration が v38 と競合 | DB 破損 | requires: PLAN-153 を明示、migration version check |
| telemetry hook が helix-codex を遅延 | 委譲効率低下 | fail-open (`\|\| true`) + timeout 2s |
| task_hash が衝突してデータ汚染 | 集計誤差 | invocation_id (uuid4) を主キーにするため集計には影響しない |
| session_id が取得できない環境 | 集計粒度低下 | NULL 許容、session 別集計は session_id IS NOT NULL で絞込 |

## 4. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- helix metrics --codex が sandbox fail 率を表示する
- helix doctor が fail 率 > 30% で WARN を出力する
- task_hash の PII 非保存が security review で確認済
- PLAN-134 / PLAN-143 の related_plans に PLAN-154 が相互参照済
