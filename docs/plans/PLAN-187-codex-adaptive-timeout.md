---
plan_id: PLAN-187
title: "helix codex 委譲 timeout adaptive 化 (size S/M/L × 5/15/30 min)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
created: "2026-05-23"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: se
    slot_label: "SE — helix-codex timeout flag 実装 + size 別デフォルト値 logic"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-146 adaptive threshold 設計との整合確認・既存 CLI 仕様 drift チェック"
  - role: qa
    slot_label: "QA — size 別 timeout 境界値テスト (S=5min / M=15min / L=30min / override)"
generates:
  - artifact_path: docs/plans/PLAN-187-codex-adaptive-timeout.md
    artifact_type: design_doc
  - artifact_path: cli/helix-codex
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_codex_adaptive_timeout.py
    artifact_type: test
dependencies:
  parent: null
  requires:
    - PLAN-146
  blocks: []
related_plans:
  - PLAN-146 (agent slot timeout 段階遷移 — adaptive timeout 思想の正本)
  - PLAN-088 (TodoWrite × agent slot framework — agent_slots lifecycle 正本)
  - PLAN-099 (自動走行 framework 5-layer — heartbeat と timeout の協調)
---

# PLAN-187: helix codex 委譲 timeout adaptive 化

## L2 凍結 (ADR snapshot)

本 PLAN は **helix codex timeout の size 別 adaptive 化** という新規大局判断を含む。
既存の固定 8 min timeout を廃止し、S=5 / M=15 / L=30 min を size から自動決定する。

根拠:
- 本 session で pytest sweep が 547s (~9 分) かかり、8 min 固定で切断された実測知見がある
- size S/M/L の 3 段階は SKILL_MAP.md §タスクサイジングで確立済みの分類軸
- `--timeout N` override は緊急時 / CI 用途の逃げ道として必須

## 背景

`helix codex` が委譲する Codex CLI には現状 **固定 8 分** 程度の暗黙 timeout が存在する。

問題:
1. size L タスク (pytest sweep 547s 等) が途中で SIGTERM され成果物が欠落する
2. size S タスクに 8 min を割り当てると並列 slot を長時間占有する
3. timeout 値が暗黙であり、委譲失敗が timeout か実装エラーか区別不能

## WebSearch skip

HELIX 内部 CLI 引数拡張。外部ライブラリ / 新規 framework 採用なし。Bash `timeout` コマンドは POSIX 標準。skip 理由を本 PLAN §背景の実測知見に記録済み。

## 設計方針

### size 別 timeout デフォルト値

| size | timeout | 根拠 |
|---|---|---|
| S | 5 min (300 s) | 1-3 ファイル / ~100 行変更 |
| M | 15 min (900 s) | 4-10 ファイル / ~500 行変更 |
| L | 30 min (1800 s) | 11+ ファイル / 501+ 行。pytest sweep 547s を包含 |

全値を env 変数で外部化:

```bash
HELIX_CODEX_TIMEOUT_S="${HELIX_CODEX_TIMEOUT_S:-300}"
HELIX_CODEX_TIMEOUT_M="${HELIX_CODEX_TIMEOUT_M:-900}"
HELIX_CODEX_TIMEOUT_L="${HELIX_CODEX_TIMEOUT_L:-1800}"
```

### --timeout N 手動 override

```bash
helix codex --role se --task "..." --timeout 600
# --timeout 0 = timeout 無効 (CI / 長時間処理用)
```

優先順位: `--timeout N` > size 別デフォルト > task-plan.yaml の size > M fallback (900s)

### helix-codex 変更箇所

```bash
# 既存 (暗黙)
timeout 480 codex exec "$PROMPT" ...

# 変更後
TIMEOUT_SEC=$(helix_codex_resolve_timeout "$SIZE" "$TIMEOUT_OVERRIDE")
timeout "$TIMEOUT_SEC" codex exec "$PROMPT" ...
```

`helix_codex_resolve_timeout` は `cli/lib/helix_codex_timeout.sh` に切り出す (unit test 可能)。

### timeout 超過時の挙動

SIGTERM 後に `helix handover update --note "timeout_exceeded size=$SIZE limit=${TIMEOUT_SEC}s"` を呼び出す (handover 不在時は fail-open)。`helix doctor` WARN に積む。

## 実装計画

### Sprint .1: timeout 決定ロジック (Codex se 委譲)

1. `cli/helix-codex` に `--timeout N` / `--size S|M|L` フラグ追加
2. `cli/lib/helix_codex_timeout.sh` に `helix_codex_resolve_timeout(size, override)` 実装
3. env 変数 3 種読み込み + `.helix/task-plan.yaml` から size 自動取得
4. `bash -n` 対象ファイル PASS (mandatory in sprint)

受入条件: `--timeout 600` が env デフォルト優先 / `--size L` が 1800s を返す

### Sprint .2: timeout 超過 carry note (Codex se 委譲)

Entry 条件: Sprint .1 フラグ実装 PASS

1. SIGTERM 後処理に carry note 書き込み追加 (fail-open)
2. `helix doctor` WARN 積み込み
3. `bash -n cli/helix-codex` PASS (mandatory in sprint)

### Sprint .3: fixture テスト (Codex qa 委譲)

Entry 条件: Sprint .2 PASS

`cli/lib/tests/test_codex_adaptive_timeout.py` に 5 シナリオ:

| T ID | シナリオ | 期待 timeout (s) |
|---|---|---|
| T187-001 | `--size S` | 300 |
| T187-002 | `--size M` | 900 |
| T187-003 | `--size L` | 1800 |
| T187-004 | `--size M --timeout 600` | 600 |
| T187-005 | `--timeout 0` | timeout コマンドなし |

`subprocess.run` mock で Codex 起動なし (CI 友好)。全 PASS 必須。

## DoD

- [ ] `bash -n cli/helix-codex` PASS
- [ ] `bash -n cli/lib/helix_codex_timeout.sh` PASS
- [ ] env 変数 3 種で閾値を外部化
- [ ] timeout 超過時に carry note 記録 (fail-open)
- [ ] T187-001〜T187-005 全 PASS
- [ ] `helix doctor` warn 増加なし

## risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| size 自動判定失敗 (task-plan.yaml 不在) | M デフォルト (safe default) | fallback M + warn log |
| L=30 min が slot を長時間占有 | 並列効率低下 | `--timeout 0` override で無効化可能 |
| SIGTERM 後 carry note が handover 競合 | 書き込み失敗 | fail-open (WARN のみ) |
