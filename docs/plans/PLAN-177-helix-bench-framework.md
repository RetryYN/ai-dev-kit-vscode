---
plan_id: PLAN-177
title: "PLAN-177: helix-bench framework (Codex / Skill / Hook 性能ベンチマーク)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — benchmark_runs schema 設計・regression 閾値方針 adversarial check"
  - role: se
    slot_label: "SE — helix-bench CLI 実装・BenchmarkRunner・helix.db migration 起草"
  - role: qa
    slot_label: "QA — pytest fixture 設計・regression 境界テスト・graceful degradation テスト"
  - role: pmo-sonnet
    slot_label: "PMO — helix doctor 統合整合・既存 cli/helix-* パターンとの整合確認"
generates:
  - artifact_path: cli/helix-bench
    artifact_type: cli_extension
  - artifact_path: cli/lib/bench_runner.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_bench_runner.py
    artifact_type: test
  - artifact_path: cli/lib/migrations/v39_benchmark_runs.py
    artifact_type: schema_migration
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
related_plans:
  - PLAN-134
  - PLAN-143
  - PLAN-153
related_adr:
  - ADR-055
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-skill
  - cli/helix-gate
  - docs/v2/L1-REQUIREMENTS.md
reference_docs:
  - docs/plans/PLAN-134-helix-metrics-cli.md
  - docs/plans/PLAN-143-helix-db-v37-event-telemetry.md
  - docs/plans/PLAN-153-helix-security-audit-framework.md
acceptance_criteria:
  - "helix bench codex --role se が実行時間を計測し benchmark_runs に記録する"
  - "helix bench skill recommender が catalog 検索の latency を計測する"
  - "helix bench hook --type PreToolUse が hook 発火から応答までの elapsed_ms を記録する"
  - "helix bench report が前回比 +20% 超過で WARN を出力する"
  - "python3 -m py_compile cli/lib/bench_runner.py PASS"
  - "pytest test_bench_runner.py 全 PASS"
  - "計測対象プロセスが失敗・未インストールの場合も graceful degradation する"
  - "helix doctor が benchmark regression WARN を統合表示する"
---

# PLAN-177: helix-bench framework (Codex / Skill / Hook 性能ベンチマーク)

## L2 凍結 (ADR snapshot)

本 PLAN tree は benchmark regression 閾値 (+20% WARN) の採用と helix.db への時系列蓄積方針を含む。これらは L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-055 (起票予定) | benchmark regression 閾値方針 (+20% WARN / helix.db 時系列蓄積) | Proposed |

双方向 trace:
- 本 PLAN → ADR-055: frontmatter `related_adr` + 本 section
- ADR-055 → 本 PLAN: ADR-055 `## Related` に「PLAN-177 (実装 PLAN、本 ADR が L2 凍結する)」を記載

> ADR-055 は本 PLAN の L4 着手前 (G3 通過後) に起票する。WebSearch 3 query 必須 (benchmark harness OSS 比較 / regression 検出手法 / helix.db 時系列設計)。

---

## 0. 背景

本 session (2026-05-23) の観測データとして pytest sweep 547s・skill catalog rebuild 5-10s・hook 発火遅延等の性能数値が散在しているが、これらを横断的に比較・追跡する基盤がない。HELIX の成熟にともない、各コンポーネント (Codex 委譲 / Skill 推挙 / Hook 発火) の性能劣化を時系列で検出することが重要になった。

本 PLAN は `helix bench` CLI を新設し、以下を統合 benchmark framework として提供する:

1. Codex 委譲 latency (role 別)
2. Skill 推挙 latency (catalog rebuild / search)
3. Hook 発火 latency (PreToolUse / PostToolUse / SessionStart 別)
4. 結果の helix.db 時系列蓄積と regression 検出

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| pytest-benchmark | pytest-benchmark.readthedocs.io | Python benchmark fixture 設計のリファレンス実装 |
| hyperfine | github.com/sharkdp/hyperfine | CLI コマンド latency 計測の標準手法 (warmup / runs 設計) |
| OpenTelemetry metrics | opentelemetry.io/docs/concepts/signals/metrics/ | 計測 signal 種別 (Histogram / Counter / Gauge) の命名規約 |
| Prometheus naming conventions | prometheus.io/docs/practices/naming/ | _ms / _seconds suffix・_total 命名規約 |
| SQLite time-series best practices | sqlite.org/lang_datefunc.html | TEXT ISO 8601 vs INTEGER epoch の選択根拠 |

## 2. 設計方針

### 2.1 アーキテクチャ

```
cli/helix-bench              bash dispatcher
  └── bench subcommand
        └── cli/lib/bench_runner.py   Python ロジック
              ├── CodexBenchmark       Codex 委譲 latency 計測
              ├── SkillBenchmark       skill catalog / search latency 計測
              ├── HookBenchmark        hook 発火 elapsed_ms 計測
              ├── RegressionDetector   前回比較・+20% WARN 判定
              └── BenchmarkStore       helix.db v39 benchmark_runs table
```

### 2.2 計測対象と指標

| 計測対象 | 計測単位 | 指標 |
|---|---|---|
| `helix bench codex --role <role>` | elapsed_ms (warmup 1 / runs 3 中央値) | role 別 p50 latency |
| `helix bench skill recommender` | elapsed_ms (catalog lookup + LLM call) | p50 / p95 latency |
| `helix bench skill catalog rebuild` | elapsed_ms (全 SKILL.md parse) | rebuild 所要時間 |
| `helix bench hook --type PreToolUse` | elapsed_ms (hook 起動〜exit まで) | フック種別 p50 latency |

warmup 実行数・本計測実行数はオプションで上書き可能 (`--warmup N --runs N`)。

### 2.3 regression 検出

- 前回同一 `bench_target` の中央値と比較
- `(current_median - prev_median) / prev_median > 0.20` で WARN
- `--baseline <run_id>` で比較ベースを明示指定可能
- helix doctor 統合: severity=warn を bench_regression カテゴリで統合表示

### 2.4 helix.db v39 schema

PLAN-153 (v38) の次バージョンとして v39 migration を追加:

```sql
CREATE TABLE IF NOT EXISTS benchmark_runs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id       TEXT NOT NULL UNIQUE,
    run_at       TEXT NOT NULL,            -- ISO 8601 UTC
    bench_target TEXT NOT NULL,            -- "codex:se" / "skill:recommender" / "hook:PreToolUse"
    warmup_runs  INTEGER NOT NULL DEFAULT 1,
    sample_runs  INTEGER NOT NULL DEFAULT 3,
    elapsed_ms   REAL NOT NULL,            -- 中央値 elapsed_ms
    p95_ms       REAL,
    min_ms       REAL,
    max_ms       REAL,
    regression   INTEGER DEFAULT 0,        -- 1 = +20% 超過 WARN
    baseline_run_id TEXT,                  -- 比較に使った前回 run_id
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_bench_runs_target_at
  ON benchmark_runs(bench_target, run_at);
```

### 2.5 graceful degradation

- Codex / skill / hook が未設定・未インストールの場合は該当 bench を skip して WARN を出力
- `--require-target` フラグ指定時のみ abort する

## 3. CLI インターフェース

```bash
# Codex latency 計測
helix bench codex --role se [--warmup N] [--runs N]
helix bench codex --role tl

# Skill latency 計測
helix bench skill recommender [--query "タスク記述"]
helix bench skill catalog rebuild

# Hook latency 計測
helix bench hook --type PreToolUse
helix bench hook --type PostToolUse
helix bench hook --type SessionStart

# 全ターゲット一括計測
helix bench all [--format text|json]

# regression レポート
helix bench report [--target BENCH_TARGET] [--since YYYY-MM-DD]
helix bench report --baseline <run_id>

# helix doctor 統合
helix doctor  # benchmark_regression WARN を統合表示
```

## 4. L4 実装 Sprint 計画

### Sprint .1: skeleton + BenchmarkStore + helix.db v39 migration

- Entry: helix.db 最新 schema version 確認 (PLAN-153 v38 が存在しない場合は v37 or 現行 version 後に付番)
- 実装: cli/helix-bench skeleton + cli/lib/bench_runner.py BenchmarkStore + v39 migration
- チェック: py_compile PASS / bats help PASS
- Exit: `benchmark_runs` table が作成される / `helix bench --help` が動作する

### Sprint .2: CodexBenchmark + SkillBenchmark

- 実装: CodexBenchmark (role 別 elapsed_ms 計測) + SkillBenchmark (catalog rebuild / recommender latency)
- warmup / runs / median 計算ロジック
- Exit: `helix bench codex --role se` / `helix bench skill recommender` が計測結果を出力し DB に記録する

### Sprint .3: HookBenchmark + RegressionDetector

- 実装: HookBenchmark (PreToolUse / PostToolUse / SessionStart elapsed_ms)
- RegressionDetector (+20% WARN 判定 / baseline 比較)
- Exit: `helix bench hook --type PreToolUse` が動作する / `helix bench report` が regression WARN を表示する

### Sprint .4: helix doctor 統合 + レビュー

- 実装: helix doctor への benchmark_regression WARN 統合
- セルフレビュー + pmo-sonnet review
- pytest test_bench_runner.py 全 PASS 確認
- docs/commands/index.md に helix bench コマンド追加
- Exit: acceptance_criteria 全件 PASS

## 5. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| Codex 計測が外部 API call を伴い CI コスト増大 | コスト超過 | `--dry-run` / mock mode を提供、CI では skip デフォルト |
| hook latency 計測が hook 自身を再帰起動 | 無限ループ | `HELIX_BENCH_IN_PROGRESS=1` env で hook skip |
| v39 migration が他 PLAN の v38/v38+ と番号衝突 | DB 破損 | Sprint .1 で現行 schema version を確認して付番 |
| warmup/runs の過剰設定によるローカル CI タイムアウト | G4 阻害 | default を warmup=1 / runs=3 に制限 |

## 6. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- helix doctor に benchmark_regression が表示される
- `helix bench all --format json` が構造化出力を返す
- ADR-055 起票済 (L2 凍結)
- HELIX_BENCH_IN_PROGRESS guard を hook 実装に追加済
