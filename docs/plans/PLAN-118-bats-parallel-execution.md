---
plan_id: PLAN-118
title: bats test parallel 化 (GNU parallel 経由)
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
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
    slot_label: "SE — cli/helix test --parallel flag 実装・bats_parallel_runner.sh 実装"
  - role: qa
    slot_label: "QA — serial vs parallel 回帰確認・benchmark 計測・isolation 確認"
  - role: pmo-sonnet
    slot_label: "PMO — bats fixture isolation 確認・PLAN-102 整合チェック"
generates:
  - artifact_type: cli_extension
    path: cli/helix
  - artifact_type: script
    path: cli/lib/bats_parallel_runner.sh
  - artifact_type: test
    path: cli/lib/tests/test_bats_parallel.bats
dependencies:
  requires:
    - PLAN-102
  blocks: []
  parent: null
related_adr: []
related_docs:
  - docs/plans/PLAN-102-pytest-xdist-parallel-isolation.md
  - docs/plans/PLAN-107-helix-db-lock-refactor.md
  - CLAUDE.md §コマンド
  - cli/helix
acceptance_criteria:
  - "cli/helix test --parallel で bats test が並列実行される"
  - "serial vs parallel で全 bats PASS 数一致 (regression なし)"
  - "並列実行で helix.db / helix-db.lock 衝突 0 件"
  - "benchmark で serial 対比 30%+ 削減実証 (目安 3-5 分 → 2 分以内)"
  - "GNU parallel 未インストール環境では xargs -P N にフォールバックしログ出力"
  - "bash -n cli/lib/bats_parallel_runner.sh PASS"
  - "bats test (5 case) 全 PASS"
---

# PLAN-118: bats test parallel 化 (GNU parallel 経由)

## L2 凍結 (ADR snapshot)

test infra 内部改善のため ADR snapshot は不要。
GNU parallel / xargs -P は既成ツールの組み合わせで新規 framework 採用なし。
PLAN-102 (pytest-xdist) を補完する test infra 改善。

## 背景

PLAN-102 で pytest sweep 530秒 → 200-300秒削減を目指している。
bats test (cli/lib/tests/*.bats / .claude/hooks/tests/*.bats) は直列実行で 3-5 分かかり、
全体 test sweep の bottleneck 候補。

bats test の特性:
- 各 test が `setup()` / `teardown()` で独自 tmp dir を作成し per-test isolation が構造的に担保
- subprocess level で分離済のため pytest-xdist の worker_id fixture 相当の改造が不要
- bats v1.2.0+ には `--jobs N` 組み込みサポートがあり、追加ツールが不要な可能性

**目標**: bats sweep 30%+ 削減 (3-5 分 → 2 分以内)。

## WebSearch — skip

bats 並列化は bats-core docs に `--jobs N` 組み込みの記載あり。PLAN-102 の SQLite WAL /
per-worker isolation パターンを流用可能。外部 API / 新ライブラリへの依存なし。

## 設計方針

### 1. bats 組み込み --jobs 優先 (bats v1.2.0+)

Sprint .1 で `bats --version` を確認し v1.2.0+ であれば `bats --jobs "$(nproc)"` を採用。

### 2. GNU parallel / xargs フォールバック

```
bats < v1.2.0 または組み込みで問題発生時:
  parallel 利用可 → find *.bats | parallel --jobs N bats {}
  parallel 未インストール → find *.bats | xargs -P N bats {}
```

### 3. cli/helix test --parallel flag

`cli/helix test --parallel` で opt-in。default は serial 維持 (既存挙動変更なし)。

## 実装計画

### Sprint .1: bats 環境確認 + isolation チェック (Codex se、size S)

`bats --version` 確認、`--jobs 4` 手動実行で regression / 衝突有無を確認。
helix.db 依存 bats の HELIX_HOME per-test 設定状況を確認 (PLAN-107 完了状況に依存)。
手動実行で大きな regression なし (または問題の特定) が完了条件。

### Sprint .2: wrapper script 実装 (Codex se、size S)

`cli/lib/bats_parallel_runner.sh` 新規: bats v1.2.0+ 組み込み / GNU parallel / xargs -P 自動分岐。
`cli/helix test` に `--parallel` flag 追加。`bash -n` 両 PASS + 手動並列起動確認が完了条件。

### Sprint .3: 回帰確認 + benchmark + bats test (Codex qa、size S)

回帰確認: serial vs `--parallel` PASS 数一致 / helix.db 衝突 0 件。
benchmark: 3 回平均で 30%+ 削減実証。
`test_bats_parallel.bats` 5 case (parallel flag 受付 / fallback / serial default / 回帰 / isolation)。
bats 5 PASS + benchmark 30%+ 記録が完了条件。

## mandatory in sprint

- [ ] `bash -n cli/lib/bats_parallel_runner.sh` PASS
- [ ] `bash -n cli/helix` PASS (wrapper 変更後)
- [ ] bats test 5 case PASS
- [ ] serial vs parallel 回帰確認 PASS
- [ ] helix.db 衝突 0 件確認
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] bats_parallel_runner.sh 実装・`bash -n` PASS
- [ ] `cli/helix test --parallel` で並列実行動作
- [ ] GNU parallel 未インストール時 xargs -P フォールバック + ログ出力
- [ ] benchmark 30%+ 削減実証
- [ ] serial / parallel PASS 数一致 (regression なし)
- [ ] helix.db 衝突 0 件
- [ ] bats test 5 PASS
- [ ] helix doctor pass 数現行以上

## carry / 学び

- bats v1.2.0+ の `--jobs N` 組み込みが使えれば GNU parallel wrapper は不要
- PLAN-107 (helix-db-lock refactor) が未完なら Sprint .2/.3 は PLAN-107 完了後に接続
- CI への -n auto 適用は benchmark 確定後に別 PLAN 起票

## 関連 reference

- PLAN-102 (pytest-xdist 並列化、requires / 設計参照元)
- PLAN-107 (helix-db-lock refactor、bats isolation 前提条件)
- [[feedback_pytest_collection_stop_false_fail]]
- [[feedback_pytest_fixture_time_dependent_flake]]
