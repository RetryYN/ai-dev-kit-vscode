---
plan_id: PLAN-179
title: skill recommender accuracy metrics (precision / recall 計測)
status: draft
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — skill_recommendation_outcomes テーブル実装 + weekly report CLI"
  - role: qa
    slot_label: "QA — precision / recall 計算ロジック検証 + helix doctor 統合テスト"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・既存 skill_usage テーブルとの差分チェック"
generates:
  - artifact_type: schema_migration
    path: cli/lib/migrations/v36_skill_recommendation_outcomes.py
  - artifact_type: python_module
    path: cli/lib/skill_accuracy_reporter.py
  - artifact_type: cli_extension
    path: cli/helix-skill
  - artifact_type: test
    path: cli/lib/tests/test_skill_accuracy_reporter.py
dependencies:
  parent: PLAN-121
  requires:
    - PLAN-121
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-121-skill-recommender-improvement.md
  - cli/lib/skill_recommender.py
  - cli/lib/skill_dispatcher.py
  - cli/lib/helix_db.py
acceptance_criteria:
  - "helix.db に skill_recommendation_outcomes テーブルが存在し、推挙 skill と実利用 skill を記録できる"
  - "helix skill stats --accuracy で weekly precision / recall レポートが出力される"
  - "helix doctor check_recommender_accuracy が precision < 70% で WARN を出す"
  - "python3 -m py_compile cli/lib/skill_accuracy_reporter.py PASS"
  - "pytest test_skill_accuracy_reporter.py (6 case) 全 PASS"
  - "既存 skill_usage テーブル・helix doctor pass 数に回帰なし"
---

# PLAN-179: skill recommender accuracy metrics (precision / recall 計測)

## L2 凍結 (ADR snapshot)

既存 helix.db schema 拡張 + helix doctor 統合パターンの繰り返し適用のため ADR snapshot は不要。
計測ロジックの設計は PLAN-121 で確立されており、本 PLAN はその実装続行である。

## 背景

PLAN-121 (skill recommender improvement) は推挙精度を「precision +10%」と目標に置いているが、
2026-05-23 時点では precision / recall を継続計測する仕組みが存在しない。
実 task 入力 → 推挙 skill → 実際に利用された skill の合致率を蓄積・集計する framework を整備することで、
PLAN-121 の改善ループを定量的に駆動できるようにする。

## WebSearch 履歴 — skip

内部 helix.db 拡張 + Python 計算モジュールのみ。外部ライブラリ新規依存なし。

## 設計方針

### helix.db テーブル設計

```sql
CREATE TABLE IF NOT EXISTS skill_recommendation_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    task_description TEXT NOT NULL,
    recommended_skills TEXT NOT NULL,   -- JSON array of skill IDs
    used_skills TEXT NOT NULL,          -- JSON array of skill IDs (実利用)
    precision_at_k REAL,                -- 推挙上位 k 件中の正解割合
    recall_at_k REAL,                   -- 正解セット中の推挙カバー割合
    recorded_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_skill_rec_outcomes_session
  ON skill_recommendation_outcomes(session_id);

CREATE INDEX IF NOT EXISTS ix_skill_rec_outcomes_recorded_at
  ON skill_recommendation_outcomes(recorded_at);
```

- `recommended_skills` / `used_skills` は JSON 配列文字列で保存
- `precision_at_k` / `recall_at_k` は記録時点で計算して保存（再集計コスト削減）
- `k` のデフォルト値は 5（`helix skill search -n 5` の既定値に準拠）

### 計測ロジック (cli/lib/skill_accuracy_reporter.py)

```python
precision_at_k = len(set(recommended[:k]) & set(used)) / min(k, len(recommended))
recall_at_k    = len(set(recommended[:k]) & set(used)) / max(len(used), 1)
```

- `used_skills` は `skill_dispatcher.py` の dispatch 完了フック (helix.db `skill_usage` テーブル) から取得
- weekly 集計は `recorded_at >= datetime("now", "-7 days")` の平均値

### helix doctor 統合

`helix doctor check_recommender_accuracy`:
- `skill_recommendation_outcomes` に週 3 件以上のサンプルがある場合のみ評価
- weekly precision 平均 < 70% → advisory WARN
- weekly recall 平均 < 50% → advisory WARN
- サンプル不足 (< 3 件) → SKIP (WARN 抑制)

## 実装計画

### Sprint .1: schema migration + Python helper (Codex se、size S)

`cli/lib/migrations/v36_skill_recommendation_outcomes.py` を新規作成。
`cli/lib/skill_accuracy_reporter.py` に以下の関数を実装:
- `record_outcome(session_id, task_desc, recommended, used, k=5) -> None`
- `weekly_precision_recall(k=5) -> dict`
- `check_accuracy_threshold(precision_warn=0.70, recall_warn=0.50) -> list[str]`

`python3 -m py_compile` PASS + migration idempotent 確認が完了条件。

### Sprint .2: CLI 統合 + helix doctor 接続 (Codex se、size S)

`cli/helix-skill` に `stats --accuracy` サブコマンドを追加。
`helix doctor` に `check_recommender_accuracy` 関数を追加。
`bash -n cli/helix-skill` PASS + `helix doctor` advisory WARN 動作確認が完了条件。

### Sprint .3: テスト + pmo-sonnet review (Codex qa、size S)

`cli/lib/tests/test_skill_accuracy_reporter.py` で 6 case:
- T1: precision_at_k 計算正確性 (完全一致)
- T2: precision_at_k 計算正確性 (部分一致)
- T3: recall_at_k 計算正確性
- T4: used_skills 空配列 (ゼロ除算ガード)
- T5: weekly_precision_recall — サンプル不足で SKIP
- T6: check_accuracy_threshold — 閾値境界値 (precision=0.699 で WARN、0.700 で pass)

pytest 6 PASS + helix doctor pass 数現行以上が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/skill_accuracy_reporter.py` PASS
- [ ] migration idempotent 確認 (`python3 -c "import cli.lib.migrations.v36_skill_recommendation_outcomes"`)
- [ ] pytest test_skill_accuracy_reporter.py 6 PASS
- [ ] 既存 `helix skill stats` / `helix doctor` 回帰なし
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] `skill_recommendation_outcomes` テーブル migration 実装済み
- [ ] `skill_accuracy_reporter.py` precision / recall 計算 + DB 記録 実装済み
- [ ] `helix skill stats --accuracy` で weekly レポート出力
- [ ] `helix doctor check_recommender_accuracy` advisory WARN 実装済み
- [ ] pytest 6 case 全 PASS
- [ ] helix doctor pass 数現行以上

## carry / 学び

- `used_skills` の自動収集は `skill_dispatcher.py` の `helix.db skill_usage` 側 hook に依存。
  PLAN-121 で dispatch 完了記録が未整備なら本 PLAN Sprint .1 前に確認が必要。
- precision / recall の `k` 値は将来的に CLI オプション化を検討 (carry)。
- weekly 集計の時間帯依存 (UTC/JST) は `datetime.now(timezone.utc)` で統一
  (`datetime.utcnow()` は Python 3.13+ removal 対象、[[feedback_pytest_fixture_time_dependent_flake]] 参照)。

## 関連 reference

- PLAN-121 (skill recommender improvement、parent)
- [[feedback_pytest_fixture_time_dependent_flake]] (時刻依存テストの動的生成)
- cli/lib/skill_recommender.py (推挙エンジン)
- cli/lib/skill_dispatcher.py (dispatch + skill_usage 記録)
