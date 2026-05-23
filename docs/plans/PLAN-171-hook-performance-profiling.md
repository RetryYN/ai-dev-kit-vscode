---
plan_id: PLAN-171
title: "PLAN-171: hook performance profiling framework"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — hook_profiler.py 実装 + helix.db hook_invocations 統合 + helix-hook profile CLI"
  - role: dba
    slot_label: "DBA — hook_invocations table DDL 設計 + PLAN-143 event_log との統合方針"
  - role: qa
    slot_label: "QA — profiling 記録シナリオ + regression 検出 (+50% WARN) テスト設計・実装"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-143 v37 event_log との設計整合確認・G4 review"
generates:
  - artifact_path: cli/lib/hook_profiler.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_hook_profiler.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-171-hook-performance-profiling.md
    artifact_type: design_doc
dependencies:
  parent: null
  requires:
    - PLAN-143
  blocks: []
related_plans:
  - PLAN-143-helix-db-v37-event-telemetry
  - PLAN-088-todowrite-agent-slot-framework
related_docs:
  - cli/lib/helix_event_logger.py
  - cli/helix-hook
  - docs/commands/ai-harness.md
---

# PLAN-171: hook performance profiling framework

> **kind**: impl (hook profiling 新規実装)
> **layer**: L4
> **drive**: be (bash glue + Python helper 実装中心)
> **L2 凍結**: 本 PLAN は既存 PLAN-143 v37 event_log の拡張であり、
> 大局判断 (新 framework 採用) を伴わないため ADR snapshot は不要。

---

## §0. 本 PLAN の位置付け

HELIX では PreToolUse / PostToolUse / SessionStart 等の hook が数十個稼働している。
session 開始時の遅延、Edit 時のレスポンス悪化、SessionStart の重さなど、
「どの hook が遅いか」を特定する手段が存在しない。

本 PLAN は PLAN-143 (helix.db v37 event_log) の `hook_invocations` table を記録先として活用し、
**hook ごとの実行時間を自動計測・可視化・regression 検出する profiling framework** を実装する。

---

## §1. 目的

1. 各 hook の実行時間 (ms 単位) を `helix.db` の `hook_invocations` table に記録する
2. `helix hook profile --slow` で遅い hook top 10 を表示し、最適化対象を即座に特定できる
3. 前回実行比 +50% 以上の hook を WARN として `helix doctor` に連携する (regression 検出)
4. profiling overhead を最小化し、hook 本体の動作に影響を与えない

---

## §2. 背景

### 2.1 現状の課題

`.claude/hooks/` 配下には 15 件以上の hook スクリプトが登録されており、
セッション開始時 (SessionStart) や Edit のたびに複数が連鎖実行される。
現状は以下が未実装:

- 各 hook の実行時間計測
- 遅延の原因 hook を特定するコマンド
- 前回実行との比較 (regression 検出)

`helix doctor` は構造的な warn を出すが、パフォーマンス観点の warn はない。

### 2.2 PLAN-143 との関係

PLAN-143 (helix.db v37) が `event_log` table と `telemetry_writer.py` を提供する。
本 PLAN は `hook_invocations` を PLAN-143 の `event_log` table の `event_type='hook'`
として記録する設計とし、専用テーブルの重複作成を避ける。

### 2.3 WebSearch skip 理由 (PLAN-087 ガードレール遵守)

本 PLAN は HELIX 内部の bash/Python 計測実装であり、外部ライブラリの新規採用なし。
`time` コマンド / `datetime.now()` / Python 標準 `time.perf_counter()` のみ使用。
WebSearch **skip**。

---

## §3. 設計方針

### 3.1 計測方式

hook スクリプトの実行時間計測は **wrapper bash function** で行う。
各 hook の entry/exit に `date +%s%N` (nanosecond) を挟み、経過 ms を算出して
`hook_profiler.py` に渡す。

```bash
# helix-hook 内 wrapper パターン
_helix_profile_hook() {
    local hook_name="$1"
    local start_ns
    start_ns=$(date +%s%N)
    shift
    "$@"
    local exit_code=$?
    local end_ns
    end_ns=$(date +%s%N)
    local elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
    python3 -c "
from cli.lib.hook_profiler import record_hook_invocation
record_hook_invocation('$hook_name', $elapsed_ms, $exit_code)
" 2>/dev/null || true
    return $exit_code
}
```

### 3.2 helix.db 記録方式

PLAN-143 の `event_log` table に `event_type='hook_invocation'` で記録する。
追加 column は `event_log.metadata_json` に JSON で格納し、DDL 変更を最小化する。

```json
{
  "hook_name": "pretooluse-design-doc-web-search-guard.sh",
  "elapsed_ms": 42,
  "exit_code": 0,
  "tool_name": "Write"
}
```

### 3.3 `helix hook profile` CLI 仕様

```
helix hook profile [--slow] [--top N] [--since HOURS] [--json]
```

| flag | 意味 | default |
|---|---|---|
| `--slow` | 直近 1h の平均 elapsed_ms を降順ソート | 常に有効 |
| `--top N` | 上位 N 件表示 | 10 |
| `--since HOURS` | 集計対象の時間幅 | 1 |
| `--json` | JSON 出力 | off |

表示例:
```
hook                                     avg_ms  calls  p95_ms  regression
pretooluse-design-doc-web-search-guard   187     23     310     +62% WARN
posttooluse-helix-job-enqueue            45      18     89      ok
pretooluse-agent-guard                   12      41     21      ok
```

### 3.4 regression 検出ルール

- 集計単位: hook 名 × 直近 1h vs 前 1h の avg_ms 比較
- WARN 閾値: `(current_avg - prev_avg) / prev_avg >= 0.50`
- `helix doctor` に `check_hook_regression()` 関数として組み込み

---

## §4. DoD (Definition of Done)

- [ ] `cli/lib/hook_profiler.py` が `record_hook_invocation` / `get_slow_hooks` /
  `check_regression` を実装している
- [ ] `helix hook profile --slow` が helix.db から集計して top 10 を表示する
- [ ] +50% 以上の hook に `WARN` ラベルが付く
- [ ] `helix doctor` の check_hook_regression が warn を出力する
- [ ] `cli/lib/tests/test_hook_profiler.py` で T1〜T5 全件 PASS
- [ ] `python3 -m py_compile cli/lib/hook_profiler.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_hook_profiler.py -v` 全件 PASS
- [ ] `helix doctor` warn 増加なし (profiling 自体の warn は想定なし)
- [ ] PLAN-143 との依存整合確認 (pmo-sonnet レビュー)

---

## §5. 実装計画

### Sprint .1 — hook_profiler.py 実装

**担当**: SE

**作業**:
1. `cli/lib/hook_profiler.py` 新規作成:
   - `record_hook_invocation(hook_name, elapsed_ms, exit_code, tool_name=None) -> None`
   - `get_slow_hooks(top_n=10, since_hours=1) -> list[dict]`
   - `check_regression(hook_name, threshold=0.50) -> float | None`
2. PLAN-143 `event_log` table への書き込み (HelixEventLogger 経由)
3. `py_compile` PASS 確認

**受入条件**:
- 全 3 関数が定義されている
- `record_hook_invocation` が DB 書き込みエラー時に silent fail (hook 本体を停止させない)
- `check_regression` が前 1h データ不足時に None を返す
- `py_compile` PASS

### Sprint .2 — CLI + wrapper 統合

**担当**: SE

**作業**:
1. `cli/helix-hook` に `profile` サブコマンド追加
2. `_helix_profile_hook` wrapper を `cli/lib/helix-hook-wrapper.sh` として切り出し
3. 既存 hook invoke パスへの wrapper 統合 (opt-in flag `HELIX_HOOK_PROFILE=1`)
4. `helix doctor` に `check_hook_regression` 追加
5. `bash -n cli/helix-hook` PASS 確認

**受入条件**:
- `helix hook profile --slow` が top 10 を表示する
- `HELIX_HOOK_PROFILE=0` (default) のとき profiling overhead = 0
- `helix doctor` が +50% regression hook を WARN 出力する

### Sprint .3 — テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | record_hook_invocation が event_log に書き込む | DB に 1 行追加 |
| T2 | get_slow_hooks が avg_ms 降順で top 10 を返す | sorted list |
| T3 | check_regression が +60% のとき 0.60 を返す | float 0.60 |
| T4 | check_regression が prev データなしのとき None を返す | None |
| T5 | record_hook_invocation が DB 接続失敗時に例外を上げない | silent fail |

**受入条件**:
- `pytest cli/lib/tests/test_hook_profiler.py -v` T1〜T5 全件 PASS

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| profiling DB 書き込みが hook 本体の遅延を増幅 | 計測値が実態より大きくなる | `record_hook_invocation` を非同期 write または fire-and-forget で実装。overhead < 5ms 目標 |
| PLAN-143 が未完了の場合 event_log table が存在しない | ImportError / DB エラー | `try/except` で silent fail。PLAN-143 完了後に有効化する feature flag を追加 |
| 大量呼び出し時に event_log が肥大化 | disk 圧迫 | `helix db clean --event-type hook_invocation --older-than 7d` を PLAN-143 側で提供 |
| regression 閾値 50% が厳しすぎてノイズ化 | WARN 連打で疲労 | `HELIX_HOOK_REGRESSION_THRESHOLD` env で調整可能に。初期値 0.50 |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
