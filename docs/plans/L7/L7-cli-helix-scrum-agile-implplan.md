---
plan_id: L7-cli-helix-scrum-agile-implplan
title: "L7-cli-helix-scrum-agile-implplan: Scrum (アジャイル) mode CLI 実装"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-25
revised: 2026-05-25
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/scrum-workflow.md
pairs_test_design:
  - HELIX-workflows/helix-process/scrum-workflow.md
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cli/helix-scrum-agile + scrum_agile_engine.py + test 一式を実装"
  - role: tl-advisor
    slot_label: "TL — Discovery alias と衝突しない CLI 境界を review"
generates:
  - artifact_path: cli/helix-scrum-agile
    artifact_type: cli_extension
  - artifact_path: cli/lib/scrum_agile_engine.py
    artifact_type: python_module
  - artifact_path: cli/tests/test-helix-scrum-agile.bats
    artifact_type: test
  - artifact_path: cli/lib/tests/test_scrum_agile_engine.py
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires:
    - HELIX-workflows/helix-process/scrum-workflow.md
    - cli/helix-discovery
    - cli/helix-scrum
  blocks: []
related_docs:
  - HELIX-workflows/HELIX-process-L0-L14.md
  - HELIX-workflows/helix-process/scrum-workflow.md
  - cli/helix
  - cli/helix-discovery
  - cli/helix-scrum
  - cli/lib/scrum_local.py
  - docs/commands/index.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント  
> **正本設計**: [HELIX-workflows/helix-process/scrum-workflow.md](../../../HELIX-workflows/helix-process/scrum-workflow.md)

本 PLAN は、Discovery legacy alias である `cli/helix-scrum` に触れず、アジャイル Scrum 専用の独立 CLI として `cli/helix-scrum-agile` を追加する。workflow SoT は `scrum-workflow.md` とし、完成インクリメントから `helix reverse fullback` へ接続する導線を CLI 出力に持たせる。

### 命名方針

- `cli/helix-scrum` は Discovery alias のまま維持する
- 新 mode CLI は `cli/helix-scrum-agile` とする
- top-level route も `helix scrum-agile` を追加し、`helix scrum` との混同を避ける

### 実装スコープ

- `cli/helix-scrum-agile`: shell wrapper
- `cli/lib/scrum_agile_engine.py`: state 管理と subcommand 実装
- `cli/lib/tests/test_scrum_agile_engine.py`: engine unit test
- `cli/tests/test-helix-scrum-agile.bats`: CLI sanity test
- `cli/helix` と `docs/commands/index.md`: route/help/docs 配線

### scope 外

- `cli/helix-scrum` の意味変更
- route_engine への `scrum_agile` 追加
- 新 SKILL 作成

## §1 工程表

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | workflow doc / 既存 CLI / task input を読んで SoT を確定 | PM/SE | ✅ done |
| 2 | `helix scrum-agile` 命名を採用し衝突回避方針を固定 | TL/SE | ✅ done |
| 3 | PLAN frontmatter を V2 形式で起票 | PM | ✅ done |
| 4 | failing test 相当の期待挙動を pytest / bats に反映 | SE | ✅ done |
| 5 | engine / wrapper / top-level route を実装 | SE | ✅ done |
| 6 | `bash -n` / `py_compile` / `pytest` / `bats` / `helix plan lint` / `helix doctor` を実行 | SE | ✅ done |
| 7 | PLAN status を completed で製本 | PM | ✅ done |

## §2 実装方針

### 2.1 CLI 契約

`helix scrum-agile <subcommand>` の subcommand は workflow doc のロール・イベント・作成物に合わせて以下とする。

- `init`: `.helix/scrum-agile/` 配下の state を初期化
- `backlog add|list`: product backlog を管理
- `plan`: sprint planning を記録し active sprint を作る
- `review`: sprint review を記録
- `retro`: sprint retrospective を記録
- `increment`: 完成インクリメントを記録し Reverse fullback 導線を出す

### 2.2 状態管理

PoC level の軽量 state として `.helix/scrum-agile/` 配下に YAML を保存する。

- `backlog.yaml`
- `sprint.yaml`
- `reviews.yaml`
- `retros.yaml`
- `increments.yaml`

### 2.3 Vモデル体系への昇華

`increment` 完了時に以下を出力する。

- `reverse_fullback_ready: true`
- `recommended_next_command: helix reverse fullback`

これにより workflow doc の「完成インクリメント → Reverse fullback 接続準備」を CLI 上で明示する。

## §3 完了条件

- `helix scrum-agile init / backlog / plan / review / retro / increment` が動作する
- `helix scrum` は引き続き Discovery alias のまま動作する
- route/help/docs の catalog check を壊さない
- 機械チェックと最小 pytest/bats が PASS する
