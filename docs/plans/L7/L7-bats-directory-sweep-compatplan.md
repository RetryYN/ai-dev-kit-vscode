---
plan_id: L7-bats-directory-sweep-compatplan
title: "L7-bats-directory-sweep-compatplan: bats directory invocation compatibility"
kind: troubleshoot
status: completed
layer: L7
drive: be
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-test-failures-triageplan.md
pairs_test_design:
  - cli/tests/test-bats-lite-runner.bats
generates:
  - artifact_path: cli/scripts/bats-lite
    artifact_type: bash_script
---

## 概要

`bats cli/tests/` のような directory 引数での実行時、現行 `bats-lite` が `not ok - missing file` を返す問題を、runner 側で吸収する。
既存の `bats cli/tests/*.bats` での sweep と同等の互換を維持しつつ、CLI 利便性を改善する。

## 実装方針

SE 判断は以下の理由で Option A（`cli/scripts/bats-lite` 拡張）を採用した:

- 契約変更が最小で、既存の `helix` ルータ拡張を伴わない。
- `helix bats cli/tests/` の追加導線は不要で、`bats` 利用側の挙動差分だけで解決できる。
- 既存 fail 分類中の P2 優先対応として、実行失敗理由（missing file）を解消しつつ、既存 9 mode / route_engine 4 mode / E2E テストへの影響を最小化できる。

## 作業

### 1) `cli/scripts/bats-lite`

- 引数展開時に directory を検知した場合、`"$arg"/*.bats` を順序付きで展開。
- 展開先が空なら `not ok - missing file: <dir>` を返却して既存の missing error 仕様を維持。
- 展開済みのファイルリストを従来ループ処理へ引き渡す。

### 2) `cli/tests/test-bats-lite-runner.bats`

- 新規テスト `bats-lite: directory input sweeps *.bats` を追加。
- 一時ディレクトリに `.bats` を 2 件作成し、`bats <dir>` の sweep が pass 2 件で完走することを検証。

### 3) PLAN 更新

- 受入条件を満たすため本 PLAN を `status: completed` として起票完了。

## 受入条件

- `cli/tests/test-bats-lite-runner.bats` 追加
- `bats cli/tests/` 実行時に directory sweep が実行され、`missing file: cli/tests/` が発生しない
- 既存非回帰: `bats cli/tests/test-helix-9mode-e2e-verification.bats` の状態を維持
- `helix doctor` の 0 fail を維持
