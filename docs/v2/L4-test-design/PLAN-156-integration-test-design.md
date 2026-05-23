---
plan_id: PLAN-156
doc_id: PLAN-156-integration-test-design
title: "PLAN-156 結合テスト設計 (helix workspace isolation)"
status: maintained
artifact_role: "③ テスト設計 (V-model 4 artifact のうち)"
created: 2026-05-23
status_history:
  - 2026-05-23: 初期作成 (Sprint .4)
owner: PM
related_docs:
  - docs/plans/PLAN-156-helix-workspace-worktree-isolation.md
  - docs/adr/ADR-040-helix-workspace-isolation.md
  - cli/lib/workspace_manager.py
  - cli/lib/workspace_snapshot.py
  - cli/lib/workspace_cli.py
  - cli/helix-workspace
  - cli/lib/tests/test_workspace_manager.py
  - cli/lib/tests/test_workspace_registry.py
phases: L4
gates: G4
references_standards:
  - IEEE 829-2008  # software test documentation
  - ISO/IEC/IEEE 29119-3:2021  # test documentation
  - pytest fixture / monkeypatch patterns
  - git worktree isolation patterns (2026 mid 業界 standard)
---

> 本書は PLAN-156 の ③ テスト設計 artifact。① 設計 (PLAN-156 本文書 + ADR-040) と ④ テストコード
> (`cli/lib/tests/test_workspace_manager.py` / `test_workspace_registry.py`)
> を双方向 trace で繋ぐ。

# PLAN-156 結合テスト設計 (③ D-TEST-DESIGN-INT)

## §1 概要

### 1.1 目的

PLAN-156 Sprint .2-.3 で実装した workspace isolation framework の結合テスト設計を確立し、
V-model の ③ テスト設計 artifact として G4 ゲートの受入根拠とする。

対象機能:
- workspace lifecycle (create / list / preflight / drop / prune)
- exec / cwd / env injection 検証
- snapshot 実データ取得 (plan_registry / handover / memory_links)
- helix_db v36 workspace_registry CRUD
- D7 drop fail-safe + D8 E2E sentinel (Codex sandbox 検証)

### 1.2 V-model 4 artifact trace

- **対象設計 (①)**: `docs/plans/PLAN-156-helix-workspace-worktree-isolation.md` §設計方針 + `docs/adr/ADR-040-helix-workspace-isolation.md` §D1-D9
- **対応実装 (②)**: `cli/lib/workspace_manager.py` / `cli/lib/workspace_snapshot.py` / `cli/lib/workspace_cli.py` / `cli/helix-workspace` / `cli/lib/helix_db.py` (workspace_registry_* helper)
- **本文書 (③)**: `docs/v2/L4-test-design/PLAN-156-integration-test-design.md`
- **対応テストコード (④)**: `cli/lib/tests/test_workspace_manager.py` (24 case) / `cli/lib/tests/test_workspace_registry.py` (9 case)

### 1.3 case 命名規則

- `I-156-001`〜`I-156-020`: workspace lifecycle (create / list / preflight / drop / prune)
- `I-156-021`〜`I-156-040`: exec / cwd / env injection
- `I-156-041`〜`I-156-060`: snapshot 実データ取得 (plan_registry / handover / memory_links)
- `I-156-061`〜`I-156-080`: helix_db v36 workspace_registry CRUD
- `I-156-081`〜`I-156-100`: D7 drop fail-safe + D8 E2E sentinel

### 1.4 fixture 方針 (ISO/IEC/IEEE 29119-3:2021 clause 9.2 準拠)

ISO/IEC/IEEE 29119-3:2021 の TestCaseSpecification が要求するフィールドに従い、各 test case は以下を明示する:

- `precondition` (initial conditions): git repo 状態 / .helix/ シード有無 / DB 初期状態
- `input` (test data): task_id / args / monkeypatch 設定 / 環境変数
- `expected output` (expected results): 戻り値 / DB state / filesystem state
- `postcondition`: workspace 残存 / DB row / trash 残骸

fixture 共通パターン:
- `_init_repo(tmp_path)`: git init + initial commit
- `_seed_helix(repo)`: allowlist/denylist 両方を含む `.helix/` 構造を seed
- `_manager(repo, tmp_path)`: `home=tmp_path/home` で WorkspaceManager 初期化
- `_seed_plan_registry_db(repo)`: plan_registry + plan_dependencies を seed
- monkeypatch は `subprocess.run` の差し替えに使用 (env 検証用)
- `tmp_path` は pytest function-scoped (IEEE 829-2008 § test case isolation 原則)

---

## §2 業界 standard 適用

### 2.1 IEEE 829-2008 / ISO/IEC/IEEE 29119-3:2021

**IEEE Std 829-2008** (Software and System Test Documentation) は Test Design Specification (TDS) と Test Case Specification (TCS) の 2 層構造を定義する。Test Case Specification の必須フィールドは:

- `test-case-id`: 一意識別子 (本書では `I-156-NNN` 形式)
- `test-items`: テスト対象の機能/モジュール
- `input-specifications`: 入力データ、初期状態
- `output-specifications`: 期待される出力 + 成功/失敗判定基準
- `environmental-needs`: 実行環境 (OS / git version / Python version)
- `special-procedural-requirements`: 前提手順 (git init, .helix seed)

**ISO/IEC/IEEE 29119-3:2021** は 829-2008 を実質的に継承し、clause 9.2 において TestCaseSpecification の構造を以下に拡張する:

- `identifier`: `I-156-NNN`
- `objective`: テスト目的 (precondition で記述)
- `priority`: H/M/L (本書では PLAN-156 AC に対応する case を H 扱い)
- `initial conditions` (= precondition)
- `test data` (= input)
- `expected results` (= expected output)
- `pass/fail criteria` (= postcondition における assertion)

本書はこの構造を Markdown table / bullet 形式で実装する。

### 2.2 pytest fixture isolation patterns (2026)

**pytest 公式 docs (docs.pytest.org)** + ADR-040 §業界動向 WebSearch 結果に基づく:

- `tmp_path` (function-scoped): 各 test case に独立した一時ディレクトリ。git worktree の isolation を filesystem レベルで保証する上で必須
- `monkeypatch`: `subprocess.run` を差し替えて env injection 内容を検証。`monkeypatch.setenv` で環境変数前提を制御
- `subprocess.run(cwd=...)`: cwd 明示でのプロセス実行。git worktree の cwd isolation を実際の subprocess で検証
- `pytest.raises`: `WorkspaceExistsError` / `WorkspaceNotFoundError` / `WorkspaceDropAbortedError` / `sqlite3.IntegrityError` の exception contract を固定

function-scoped autouse pattern (`conftest.py`) は PLAN-223 で確立 (pytest-xdist 並列実行対応)。

### 2.3 git worktree isolation test patterns (2026 mid 業界 standard)

ADR-040 §業界動向 WebSearch (2026-05-23) + git-scm.com/docs/git-worktree より:

- **side-by-side isolation**: main repo と workspace repo を完全に独立した cwd で扱う
- **orphan detection**: `git worktree list` で存在しない workspace_path を検出 → `preflight` の orphan_worktree check
- **cleanup verification**: `git worktree prune` 後に `.git/worktrees/` の残骸がないことを確認
- **branch divergence**: workspace branch が main より ahead になった状態を `git rev-list` で計測

標準パターン: tmp_path 内に repo を init → `git worktree add -b workspace/PLAN-X` → subprocess で cwd 切替確認 → `git worktree remove` でクリーンアップ

### 2.4 WebSearch 履歴 (PLAN-087 ガード遵守、3 query 実施)

| # | Query | 実施日 | 主な出典 / Findings |
|---|---|---|---|
| Q1 | `pytest integration test git worktree isolation 2026` | 2026-05-23 | pytest 公式 docs (docs.pytest.org) + ADR-040 §業界動向。tmp_path function-scoped / monkeypatch / subprocess.run(cwd=) パターンが 2026 標準。Claude Code `--worktree` flag も同日確認 |
| Q2 | `IEEE 829-2008 test design specification structure precondition input expected output` | 2026-05-23 | IEEE Std 829-2008 §§ TCS 構造 (test-case-id / test-items / input-specifications / output-specifications / pass-fail criteria) + ISO/IEC/IEEE 29119-3:2021 clause 9.2 extension (identifier / initial conditions / test data / expected results) |
| Q3 | `ISO IEC IEEE 29119-3 2021 test case specification software testing documentation standard` | 2026-05-23 | ISO/IEC/IEEE 29119-3:2021 Part 3 Test Documentation。clause 9.2 TestCaseSpecification が 829-2008 を継承・拡張。precondition→initial conditions / input→test data / expected output→expected results へのフィールド対応を確認 |

---

## §3 test case 詳細

### §3.1 workspace lifecycle (I-156-001〜I-156-020)

#### I-156-001: create が git worktree + workspace manifest を生成する

- **precondition**: git repo 初期化済み、.helix/ シード済み (config / phase.yaml / task-plan.yaml / templates/ 含む)
- **input**: `manager.create(task_id="PLAN-156")`
- **expected output**: `workspace_path` 存在 / `.helix/workspace.yaml` 存在 / `workspace_state_snapshot.json` 存在 / branch=`workspace/PLAN-156`; `git worktree list` に PLAN-156 が含まれる
- **postcondition**: workspace ディレクトリが `~home/.helix/workspaces/<repo>/PLAN-156` 以下に存在
- **対応実装 (②)**: `cli/lib/workspace_manager.py` WorkspaceManager.create()
- **対応テストコード (④)**: `test_workspace_manager.py::test_create_creates_worktree_and_workspace_manifest`
- **DoD link**: PLAN-156 AC-1 (workspace create) / ADR-040 D1

#### I-156-002: create 2 回目は WorkspaceExistsError を raise する

- **precondition**: PLAN-156 workspace が active 状態で存在
- **input**: `manager.create(task_id="PLAN-156")` (2 回目)
- **expected output**: `WorkspaceExistsError` が raise される
- **postcondition**: workspace 数は変化しない (1 のまま)
- **対応実装 (②)**: `workspace_manager.py` create() の重複チェックロジック
- **対応テストコード (④)**: `test_create_twice_raises_workspace_exists`
- **DoD link**: PLAN-156 AC-1

#### I-156-003: create が denylist コンテンツをコピーしない

- **precondition**: .helix/ に tmp/ / cache/ / logs/ が存在
- **input**: `manager.create(task_id="PLAN-DENY")`
- **expected output**: workspace `.helix/tmp` / `.helix/cache` / `.helix/logs` が存在しない
- **postcondition**: workspace の .helix/ は allowlist のみ含む
- **対応実装 (②)**: `workspace_manager.py` `_filtered_copy()` denylist 除外ロジック
- **対応テストコード (④)**: `test_create_does_not_copy_denylist_content`
- **DoD link**: ADR-040 D2 (filtered materialized init)

#### I-156-004: create が allowlist コンテンツをコピーする

- **precondition**: .helix/ に config/ / phase.yaml / task-plan.yaml / templates/ が存在
- **input**: `manager.create(task_id="PLAN-ALLOW")`
- **expected output**: workspace `.helix/config/settings.yaml` / `phase.yaml` / `task-plan.yaml` / `templates/base.txt` が全て存在
- **postcondition**: allowlist ファイルが workspace に正確にコピーされている
- **対応実装 (②)**: `workspace_manager.py` `_filtered_copy()` allowlist コピーロジック
- **対応テストコード (④)**: `test_create_copies_allowlist_content`
- **DoD link**: ADR-040 D2

#### I-156-005: _filtered_copy が .db-wal glob をスキップする

- **precondition**: src に `config/state.db-wal` と `config/keep.txt` と `phase.yaml` が存在
- **input**: `_filtered_copy(src, dst)`
- **expected output**: `dst/config/keep.txt` 存在 / `dst/config/state.db-wal` 不在 / stats["skipped_count"] >= 1
- **postcondition**: dst に .db-wal は残らない
- **対応実装 (②)**: `workspace_manager.py` `_filtered_copy()` glob スキップロジック
- **対応テストコード (④)**: `test_filtered_copy_skips_db_wal_glob`
- **DoD link**: ADR-040 D2 (denylist: `*.db-wal`)

#### I-156-006: list_workspaces が active エントリのみを返す

- **precondition**: PLAN-ACTIVE (active) と PLAN-DROPPED (dropped) の 2 workspace が存在
- **input**: `manager.list_workspaces(status="active")`
- **expected output**: `[{"task_id": "PLAN-ACTIVE", ...}]` (1 件)
- **postcondition**: PLAN-DROPPED は結果に含まれない
- **対応実装 (②)**: `workspace_manager.py` list_workspaces() status フィルタ
- **対応テストコード (④)**: `test_list_workspaces_filters_active_entries`
- **DoD link**: PLAN-156 AC-5 (helix workspace list)

#### I-156-007: preflight が main dirty を検出する

- **precondition**: PLAN-PREFLIGHT-DIRTY workspace が active / main repo の README.md を変更 (dirty state)
- **input**: `manager.preflight("PLAN-PREFLIGHT-DIRTY")`
- **expected output**: `payload["ok"] is True` / issues 中に `main_dirty` (severity=warn) が含まれる
- **postcondition**: workspace は変更されない
- **対応実装 (②)**: `workspace_manager.py` preflight() main dirty check
- **対応テストコード (④)**: `test_preflight_detects_main_dirty`
- **DoD link**: ADR-040 D7 (preflight で main dirty 検出)

#### I-156-008: preflight が orphan worktree を検出する

- **precondition**: workspace を作成後に `git worktree remove --force` で worktree のみ削除 (registry は残存)
- **input**: `manager.preflight("PLAN-PREFLIGHT-ORPHAN")`
- **expected output**: `payload["ok"] is False` / issues 中に `orphan_worktree` (severity=error) が含まれる
- **postcondition**: registry は active のまま残る (preflight は read-only)
- **対応実装 (②)**: `workspace_manager.py` preflight() orphan 検出ロジック
- **対応テストコード (④)**: `test_preflight_detects_orphan_worktree`
- **DoD link**: ADR-040 D7

#### I-156-009: preflight が branch divergence を検出する

- **precondition**: workspace 内で commit 追加 (branch が main より ahead)
- **input**: `manager.preflight("PLAN-PREFLIGHT-BRANCH")`
- **expected output**: `payload["ok"] is True` / issues 中に `branch_divergence` (severity=warn) が含まれる
- **postcondition**: workspace は変更されない
- **対応実装 (②)**: `workspace_manager.py` preflight() branch divergence check
- **対応テストコード (④)**: `test_preflight_detects_branch_divergence`
- **DoD link**: ADR-040 D6 (base_sha 記録) + D7

#### I-156-010: drop default が変更ありの workspace で WorkspaceDropAbortedError を raise する

- **precondition**: workspace に README.md の変更が存在 (未コミット変更あり)
- **input**: `manager.drop("PLAN-DROP")` (force=False / default)
- **expected output**: `WorkspaceDropAbortedError` が raise される
- **postcondition**: workspace は削除されない、registry は active のまま
- **対応実装 (②)**: `workspace_manager.py` drop() fail-safe デフォルト動作
- **対応テストコード (④)**: `test_drop_default_aborts_when_workspace_has_changes`
- **DoD link**: ADR-040 D7 (drop default = abort)

#### I-156-011: drop force が bundle + tar を退避して workspace を削除する

- **precondition**: workspace に untracked.txt が存在
- **input**: `manager.drop("PLAN-FORCE", force=True)`
- **expected output**: `drop_result["dropped"] is True` / workspace_path 不在 / `trash_path/changes.bundle` 存在 / `trash_path/untracked.tar.gz` 存在 / list_workspaces(status="dropped") に PLAN-FORCE が含まれる
- **postcondition**: workspace ディレクトリが消え、trash に bundle + tar が残る
- **対応実装 (②)**: `workspace_manager.py` drop(force=True) 退避ロジック
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace`
- **DoD link**: ADR-040 D7 (`~/.helix/workspace-trash/<task>/<timestamp>/`)

#### I-156-012: prune dry-run が orphan candidates を列挙して変更しない

- **precondition**: registry に `PLAN-ORPHAN.yaml` が存在 (workspace_path=/tmp/missing、実在せず)
- **input**: `manager.prune(dry_run=True)`
- **expected output**: `stale == ["PLAN-ORPHAN"]` / registry_path が依然存在
- **postcondition**: filesystem は変更されない
- **対応実装 (②)**: `workspace_manager.py` prune(dry_run=True)
- **対応テストコード (④)**: `test_prune_dry_run_lists_orphan_candidates_without_mutation`
- **DoD link**: ADR-040 D7 (prune subcommand)

#### I-156-013: create が registry ファイル fallback を書き込む

- **precondition**: helix.db が不在 (DB なし環境)
- **input**: `manager.create(task_id="PLAN-REGISTRY")`
- **expected output**: `repo/.helix/workspaces/PLAN-REGISTRY.yaml` 存在 / `status == "active"`
- **postcondition**: YAML ファイルによる registry fallback が機能している
- **対応実装 (②)**: `workspace_manager.py` _write_registry_fallback()
- **対応テストコード (④)**: `test_create_writes_registry_file_fallback`
- **DoD link**: ADR-040 D2 / PLAN-156 AC-1

#### I-156-014: create した workspace で preflight が checked_at を返す

- **precondition**: workspace が active 状態
- **input**: `manager.preflight(task_id)`
- **expected output**: `payload["task_id"] == task_id` / `payload["checked_at"]` が ISO 形式の timestamp
- **postcondition**: preflight は read-only、workspace 状態変化なし
- **対応実装 (②)**: `workspace_manager.py` preflight() return structure
- **対応テストコード (④)**: `test_preflight_detects_main_dirty` (checked_at assertion 含む)
- **DoD link**: ADR-040 D7

#### I-156-015: list_workspaces が全ステータスを status=None で返す

- **precondition**: active 1 件 + dropped 1 件が存在
- **input**: `manager.list_workspaces()` (status 未指定)
- **expected output**: 2 件返る
- **postcondition**: フィルタなし動作
- **対応実装 (②)**: `workspace_manager.py` list_workspaces(status=None)
- **対応テストコード (④)**: 追加 test 推奨 (既存 test は status="active" のみ)
- **DoD link**: PLAN-156 AC-5

#### I-156-016: create が base_sha を workspace manifest に記録する

- **precondition**: git repo に HEAD commit が存在
- **input**: `manager.create(task_id="PLAN-SHA")`
- **expected output**: `workspace.yaml` の `base_sha` が 40 文字 SHA または non-empty string
- **postcondition**: workspace manifest に base_sha が永続化
- **対応実装 (②)**: `workspace_manager.py` create() base_sha 記録
- **対応テストコード (④)**: 追加 test 推奨 (既存は branch 確認のみ)
- **DoD link**: ADR-040 D6 (base_sha 必須記録)

#### I-156-017: create が branch 名を `workspace/<task_id>` に統一する

- **precondition**: git repo が初期化済み
- **input**: `manager.create(task_id="PLAN-BRANCH")` (branch 指定なし)
- **expected output**: `result["branch"] == "workspace/PLAN-BRANCH"`
- **postcondition**: `git branch --list workspace/PLAN-BRANCH` に表示される
- **対応実装 (②)**: `workspace_manager.py` create() branch 命名規則
- **対応テストコード (④)**: `test_create_creates_worktree_and_workspace_manifest` (branch assertion 含む)
- **DoD link**: ADR-040 D6

#### I-156-018: drop 済み workspace に対する exec が ValueError を raise する

- **precondition**: workspace が dropped 状態
- **input**: `manager.exec_in_workspace("PLAN-DROPPED", "true")`
- **expected output**: `ValueError` (message に "active" を含む) が raise される
- **postcondition**: コマンドは実行されない
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() status guard
- **対応テストコード (④)**: `test_exec_in_workspace_raises_for_dropped_status`
- **DoD link**: PLAN-156 AC-2 (workspace exec)

#### I-156-019: 存在しない task_id に対する preflight は WorkspaceNotFoundError を raise する

- **precondition**: PLAN-MISSING は registry に存在しない
- **input**: `manager.preflight("PLAN-MISSING")` (実装次第)
- **expected output**: `WorkspaceNotFoundError` raise (実装に依存)
- **postcondition**: 変更なし
- **対応実装 (②)**: `workspace_manager.py` preflight() not-found guard
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: PLAN-156 AC-5

#### I-156-020: prune 実行 (dry_run=False) が orphan を削除する

- **precondition**: registry に `PLAN-ORPHAN.yaml` が存在 (workspace_path が実在しない)
- **input**: `manager.prune(dry_run=False)`
- **expected output**: registry ファイルが削除される
- **postcondition**: `repo/.helix/workspaces/PLAN-ORPHAN.yaml` が不在
- **対応実装 (②)**: `workspace_manager.py` prune() 実行モード
- **対応テストコード (④)**: 追加 test 推奨 (dry_run=False path)
- **DoD link**: ADR-040 D7

---

### §3.2 exec / cwd / env injection (I-156-021〜I-156-040)

#### I-156-021: exec が `true` コマンドで exit code 0 を返す

- **precondition**: PLAN-EXEC-TRUE workspace が active
- **input**: `manager.exec_in_workspace("PLAN-EXEC-TRUE", "true")`
- **expected output**: return value == 0
- **postcondition**: workspace は変更されない
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace()
- **対応テストコード (④)**: `test_exec_in_workspace_returns_exit_code_zero_for_true_command`
- **DoD link**: ADR-040 D8 (D8 E2E sentinel baseline)

#### I-156-022: exec が nonzero exit code を伝播する

- **precondition**: PLAN-EXEC-FALSE workspace が active
- **input**: `manager.exec_in_workspace("PLAN-EXEC-FALSE", "exit 7")`
- **expected output**: return value == 7
- **postcondition**: exit code が正確に伝播される
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() returncode 伝播
- **対応テストコード (④)**: `test_exec_in_workspace_propagates_nonzero_exit_code`
- **DoD link**: PLAN-156 AC-2

#### I-156-023: 存在しない task_id に対する exec が WorkspaceNotFoundError を raise する

- **precondition**: PLAN-MISSING は registry に存在しない
- **input**: `manager.exec_in_workspace("PLAN-MISSING", "true")`
- **expected output**: `WorkspaceNotFoundError` が raise される
- **postcondition**: コマンドは実行されない
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() not-found guard
- **対応テストコード (④)**: `test_exec_in_workspace_raises_for_missing_task`
- **DoD link**: PLAN-156 AC-2

#### I-156-024: exec が HELIX_WORKSPACE_* 環境変数を注入する

- **precondition**: PLAN-ENV workspace が active / `subprocess.run` を monkeypatch で差し替え
- **input**: `manager.exec_in_workspace("PLAN-ENV", "printf 'ok'", extra_env={"EXTRA_FLAG": "1"})`
- **expected output**: recorded["env"]["HELIX_WORKSPACE_TASK_ID"] == "PLAN-ENV" / ["HELIX_WORKSPACE_PATH"] == str(workspace_path) / ["HELIX_WORKSPACE_BRANCH"] == "workspace/PLAN-ENV" / ["EXTRA_FLAG"] == "1"
- **postcondition**: 環境変数が subprocess に渡される
- **対応実装 (②)**: `workspace_manager.py` `_inject_helix_workspace_env_vars()`
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: ADR-040 D5 (API 命名) + PLAN-156 AC-2

#### I-156-025: exec が cwd を workspace_path に設定する

- **precondition**: PLAN-ENV workspace が active / subprocess monkeypatch
- **input**: `manager.exec_in_workspace("PLAN-ENV", "printf 'ok'")`
- **expected output**: `recorded["cwd"] == workspace_path` (Path オブジェクト)
- **postcondition**: subprocess は workspace cwd で実行される
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() cwd 設定
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars` (cwd assertion 含む)
- **DoD link**: ADR-040 D8 (cwd isolation の核心)

#### I-156-026: exec が bash -c で command を実行する

- **precondition**: subprocess monkeypatch 済み
- **input**: `manager.exec_in_workspace("PLAN-ENV", "printf 'ok'")`
- **expected output**: `recorded["args"] == ["/bin/bash", "-c", "printf 'ok'"]`
- **postcondition**: シェルコマンドとして実行される
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() args 構成
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: PLAN-156 AC-2

#### I-156-027: _inject_helix_workspace_env_vars が OS 環境変数を継承する

- **precondition**: `BASE_FLAG=enabled` が設定済み (monkeypatch.setenv)
- **input**: `_inject_helix_workspace_env_vars("PLAN-156", tmp_path/"workspace", "workspace/PLAN-156", extra_env={"EXTRA_FLAG": "1"})`
- **expected output**: `env["BASE_FLAG"] == "enabled"` / `env["HELIX_WORKSPACE_TASK_ID"] == "PLAN-156"` / `env["EXTRA_FLAG"] == "1"`
- **postcondition**: OS 環境変数が上書きされない
- **対応実装 (②)**: `workspace_manager.py` `_inject_helix_workspace_env_vars()` os.environ.copy()
- **対応テストコード (④)**: `test_inject_helix_workspace_env_vars_preserves_os_environment`
- **DoD link**: PLAN-156 AC-2 / ADR-040 D8

#### I-156-028: exec が check=False で subprocess.run を呼ぶ

- **precondition**: subprocess monkeypatch 済み
- **input**: exec_in_workspace 実行
- **expected output**: `recorded["check"] is False`
- **postcondition**: CalledProcessError は raise されない (exit code を return value で伝播)
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() check=False
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: PLAN-156 AC-2

#### I-156-029: D8 sentinel Layer 1 — workspace 内 write が可能なことを確認する (bash 直接)

- **precondition**: workspace が active / Layer 1 は Sprint .3 で bash 直接実施済 (commit 1724be5 後)
- **input**: `exec_in_workspace(task_id, "echo sentinel > workspace_test.txt")`
- **expected output**: exit code 0 / workspace_test.txt が workspace_path 内に存在
- **postcondition**: workspace への write が成功
- **対応実装 (②)**: WorkspaceManager.exec_in_workspace() + cwd isolation
- **対応テストコード (④)**: Layer 2 (§5) で検証、Layer 1 は Sprint .3 で手動確認済
- **DoD link**: ADR-040 D8

#### I-156-030: exec extra_env が None の場合でも正常動作する

- **precondition**: workspace が active
- **input**: `manager.exec_in_workspace(task_id, "true")` (extra_env 未指定)
- **expected output**: exit code 0、エラーなし
- **postcondition**: 環境変数注入は HELIX_WORKSPACE_* のみ
- **対応実装 (②)**: `workspace_manager.py` extra_env=None のデフォルト処理
- **対応テストコード (④)**: `test_exec_in_workspace_returns_exit_code_zero_for_true_command` (extra_env なし)
- **DoD link**: PLAN-156 AC-2

#### I-156-031: exec が空文字コマンドで呼ばれた場合の挙動

- **precondition**: workspace active
- **input**: `manager.exec_in_workspace(task_id, "")` または `" "`
- **expected output**: 実装依存 (exit code 0 または ValueError)
- **postcondition**: エラーが明示的に伝播するか、空コマンドが安全に実行される
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() input validation
- **対応テストコード (④)**: 追加 test 推奨 (edge case)
- **DoD link**: PLAN-156 AC-2

#### I-156-032: HELIX_WORKSPACE_PATH が workspace_path と一致する

- **precondition**: subprocess monkeypatch 済み / workspace が active
- **input**: exec_in_workspace 呼び出し
- **expected output**: `env["HELIX_WORKSPACE_PATH"] == str(workspace_path)`
- **postcondition**: workspace 内プロセスが自身の path を把握できる
- **対応実装 (②)**: `_inject_helix_workspace_env_vars()` HELIX_WORKSPACE_PATH 設定
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: ADR-040 D5

#### I-156-033: HELIX_WORKSPACE_BRANCH が workspace branch 名と一致する

- **precondition**: workspace が `workspace/PLAN-ENV` branch で作成済み
- **input**: exec_in_workspace 呼び出し (monkeypatch)
- **expected output**: `env["HELIX_WORKSPACE_BRANCH"] == "workspace/PLAN-ENV"`
- **postcondition**: workspace 内プロセスが branch 名を把握できる
- **対応実装 (②)**: `_inject_helix_workspace_env_vars()` HELIX_WORKSPACE_BRANCH 設定
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: ADR-040 D5 / D6

#### I-156-034: exec 結果の exit code が整数で返る

- **precondition**: workspace active
- **input**: `manager.exec_in_workspace(task_id, "exit 42")`
- **expected output**: return value == 42 (int)
- **postcondition**: type(result) == int
- **対応実装 (②)**: exec_in_workspace() returncode 型
- **対応テストコード (④)**: `test_exec_in_workspace_propagates_nonzero_exit_code`
- **DoD link**: PLAN-156 AC-2

#### I-156-035: exec が dropped 以外の non-active ステータスでも ValueError を raise する (merged)

- **precondition**: workspace が merged 状態
- **input**: `manager.exec_in_workspace(task_id, "true")`
- **expected output**: `ValueError` (message に "active" を含む)
- **postcondition**: コマンド未実行
- **対応実装 (②)**: exec_in_workspace() status guard (active のみ許可)
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: PLAN-156 AC-2

#### I-156-036: D8 sentinel Layer 1 — main workspace への write が失敗すること (bash 直接)

- **precondition**: Sprint .3 bash sentinel 実施済 / main workspace と workspace 両方が存在
- **input**: workspace exec で `echo test > <main_path>/test_write`
- **expected output**: git worktree が cwd を workspace に限定 → Codex CLI が main path への write を行わない (Layer 2 で正式検証)
- **postcondition**: main workspace は clean
- **対応実装 (②)**: WorkspaceManager.exec_in_workspace() cwd 設定
- **対応テストコード (④)**: Layer 2 (§5) で正式検証
- **DoD link**: ADR-040 D8

#### I-156-037: exec が subprocess.run の戻り値の returncode を返す

- **precondition**: subprocess monkeypatch 済み (returncode=42 を返す)
- **input**: `manager.exec_in_workspace(task_id, "...")`
- **expected output**: return value == 42
- **postcondition**: monkeypatch.returncode が正確に伝播
- **対応実装 (②)**: exec_in_workspace() `return result.returncode`
- **対応テストコード (④)**: 追加 test 推奨 (monkeypatch returncode 明示)
- **DoD link**: PLAN-156 AC-2

#### I-156-038: extra_env に HELIX_WORKSPACE_* を含む場合に上書きされないこと

- **precondition**: extra_env に `HELIX_WORKSPACE_TASK_ID: "OVERWRITE"` を指定
- **input**: `_inject_helix_workspace_env_vars("PLAN-156", ..., extra_env={"HELIX_WORKSPACE_TASK_ID": "OVERWRITE"})`
- **expected output**: 実装依存 (PLAN-156 優先か OVERWRITE 優先か明示)
- **postcondition**: 環境変数上書きポリシーが明確
- **対応実装 (②)**: `_inject_helix_workspace_env_vars()` merge ポリシー
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: PLAN-156 AC-2

#### I-156-039: exec が長時間実行コマンドの stdout を返さない (fire-and-forget)

- **precondition**: workspace active
- **input**: `manager.exec_in_workspace(task_id, "sleep 0.01 && true")`
- **expected output**: exit code 0 (stdout は capture しない)
- **postcondition**: exec は exit code のみ返す (output は caller の stdout に出力される)
- **対応実装 (②)**: exec_in_workspace() capture_output=False
- **対応テストコード (④)**: `test_exec_in_workspace_returns_exit_code_zero_for_true_command`
- **DoD link**: PLAN-156 AC-2

#### I-156-040: exec が /bin/bash を使う (sh ではない)

- **precondition**: subprocess monkeypatch 済み
- **input**: exec_in_workspace 呼び出し
- **expected output**: `recorded["args"][0] == "/bin/bash"`
- **postcondition**: bash 拡張構文 (exit, arrays 等) が使用可能
- **対応実装 (②)**: exec_in_workspace() args = ["/bin/bash", "-c", command]
- **対応テストコード (④)**: `test_exec_in_workspace_injects_helix_workspace_env_vars`
- **DoD link**: PLAN-156 AC-2

---

### §3.3 snapshot 実データ取得 (I-156-041〜I-156-060)

#### I-156-041: generate_snapshot が schema_version=1 を設定する

- **precondition**: .helix/ シード済み / helix.db は不在
- **input**: `manager.create(task_id="PLAN-SNAPSHOT")` → snapshot_path を read
- **expected output**: `snapshot["schema_version"] == 1` / `snapshot["task_id"] == "PLAN-SNAPSHOT"`
- **postcondition**: snapshot ファイルが workspace 内に存在
- **対応実装 (②)**: `workspace_snapshot.py` generate_snapshot() schema_version
- **対応テストコード (④)**: `test_generate_snapshot_minimal_schema_version_one`
- **DoD link**: ADR-040 D3 (workspace_state_snapshot.json)

#### I-156-042: generate_snapshot が plan_registry を抽出する

- **precondition**: helix.db に plan_registry + plan_dependencies がシード済み (PLAN-156 + PARENT + REQ + BLOCK)
- **input**: `workspace_snapshot.generate_snapshot(repo, target_path, task_id="PLAN-156", base_sha="deadbeef")`
- **expected output**: `payload["plan_registry"]` に PLAN-156 / PLAN-PARENT / PLAN-REQ / PLAN-BLOCK が含まれる / PLAN-156 の `parent == "PLAN-PARENT"`
- **postcondition**: snapshot ファイルに plan_registry が JSON 化されている
- **対応実装 (②)**: `workspace_snapshot.py` `_extract_plan_registry()`
- **対応テストコード (④)**: `test_generate_snapshot_extracts_plan_registry`
- **DoD link**: ADR-040 D3 / D2 (snapshot json で plan_registry 取得)

#### I-156-043: generate_snapshot が handover snapshot を抽出する

- **precondition**: `.helix/handover/CURRENT.json` が存在 (task.id=PLAN-156 / phase=L4 / next_actions あり)
- **input**: `workspace_snapshot.generate_snapshot(repo, target_path, task_id="PLAN-156", base_sha="cafebabe")`
- **expected output**: `payload["handover_snapshot"]["task"]["id"] == "PLAN-156"` / `["phase"] == "L4"` / `["next_actions"] == ["implement exec", "extend preflight"]`
- **postcondition**: snapshot に handover が JSON 化されている
- **対応実装 (②)**: `workspace_snapshot.py` `_extract_handover_snapshot()`
- **対応テストコード (④)**: `test_generate_snapshot_extracts_handover_snapshot`
- **DoD link**: ADR-040 D2 (handover の Next Action snapshot)

#### I-156-044: generate_snapshot が memory_links を抽出する

- **precondition**: `HELIX_MEMORY_PATH` に PLAN-156 関連エントリを含む MEMORY.md が設定されている
- **input**: `workspace_snapshot.generate_snapshot(repo, target_path, task_id="PLAN-156", base_sha="feedface")`
- **expected output**: `payload["memory_links"]` に PLAN-156 を含む 2 行が抽出される ("unrelated entry" は除外)
- **postcondition**: snapshot に memory_links が含まれる
- **対応実装 (②)**: `workspace_snapshot.py` `_extract_memory_links()`
- **対応テストコード (④)**: `test_generate_snapshot_extracts_memory_links`
- **DoD link**: ADR-040 D2 (memory feedback の関連 link snapshot)

#### I-156-045: generate_snapshot が helix.db 不在時に空値で graceful に処理する

- **precondition**: helix.db が .helix/ に存在しない
- **input**: `workspace_snapshot.generate_snapshot(repo, target_path, task_id="PLAN-MISSING-DB", base_sha="1234567")`
- **expected output**: `payload["plan_registry"] == []` / `payload["handover_snapshot"] == {}` / `payload["memory_links"] == []` / target_path が存在する
- **postcondition**: snapshot ファイルが空値で生成される (crash しない)
- **対応実装 (②)**: `workspace_snapshot.py` generate_snapshot() graceful degradation
- **対応テストコード (④)**: `test_generate_snapshot_handles_missing_helix_db_gracefully`
- **DoD link**: ADR-040 D3

#### I-156-046: snapshot が base_sha を記録する

- **precondition**: helix.db シード済み
- **input**: `generate_snapshot(..., base_sha="deadbeef")`
- **expected output**: `payload["base_sha"] == "deadbeef"`
- **postcondition**: snapshot に base_sha が永続化される
- **対応実装 (②)**: `workspace_snapshot.py` generate_snapshot() base_sha 記録
- **対応テストコード (④)**: `test_generate_snapshot_extracts_plan_registry` (base_sha confirmation)
- **DoD link**: ADR-040 D6

#### I-156-047: snapshot が task_id を記録する

- **precondition**: 任意の .helix/ 状態
- **input**: `generate_snapshot(..., task_id="PLAN-156")`
- **expected output**: `payload["task_id"] == "PLAN-156"`
- **postcondition**: snapshot に task_id が永続化される
- **対応実装 (②)**: `workspace_snapshot.py` generate_snapshot() task_id 記録
- **対応テストコード (④)**: `test_generate_snapshot_minimal_schema_version_one`
- **DoD link**: ADR-040 D2

#### I-156-048: snapshot ファイルが有効な JSON として読み込める

- **precondition**: create 実行後 snapshot_path が存在
- **input**: `json.loads(Path(snapshot_path).read_text())`
- **expected output**: dict オブジェクトとして parse 成功 / `json.JSONDecodeError` が raise されない
- **postcondition**: snapshot が有効な JSON
- **対応実装 (②)**: `workspace_snapshot.py` json.dump() 書き出し
- **対応テストコード (④)**: `test_generate_snapshot_minimal_schema_version_one`
- **DoD link**: ADR-040 D2

#### I-156-049: snapshot が HELIX_MEMORY_PATH 未設定時に memory_links=[] を返す

- **precondition**: `HELIX_MEMORY_PATH` が未設定
- **input**: `generate_snapshot(repo, target_path, task_id="PLAN-X", base_sha="abc")`
- **expected output**: `payload["memory_links"] == []`
- **postcondition**: 環境変数なしでも crash しない
- **対応実装 (②)**: `_extract_memory_links()` os.environ.get() graceful fallback
- **対応テストコード (④)**: `test_generate_snapshot_handles_missing_helix_db_gracefully` (memory_links == [])
- **DoD link**: ADR-040 D2

#### I-156-050: plan_registry 抽出が parent / requires / blocks の依存関係を含む

- **precondition**: plan_dependencies に (PLAN-156, parent, PLAN-PARENT) などが存在
- **input**: `generate_snapshot(..., task_id="PLAN-156")`
- **expected output**: `payload["plan_registry"][0]["parent"] == "PLAN-PARENT"`
- **postcondition**: 依存関係が snapshot に含まれる
- **対応実装 (②)**: `_extract_plan_registry()` JOIN ロジック
- **対応テストコード (④)**: `test_generate_snapshot_extracts_plan_registry`
- **DoD link**: ADR-040 D3

#### I-156-051: handover が存在しない場合 handover_snapshot が {} になる

- **precondition**: `.helix/handover/CURRENT.json` が不在
- **input**: `generate_snapshot(repo, target_path, task_id="PLAN-NOHANDOVER", base_sha="abc")`
- **expected output**: `payload["handover_snapshot"] == {}`
- **postcondition**: handover 不在でも crash しない
- **対応実装 (②)**: `_extract_handover_snapshot()` graceful fallback
- **対応テストコード (④)**: `test_generate_snapshot_handles_missing_helix_db_gracefully`
- **DoD link**: ADR-040 D2

#### I-156-052: snapshot が created_at を ISO timestamp で記録する

- **precondition**: 任意の .helix/ 状態
- **input**: `generate_snapshot(...)`
- **expected output**: `payload["created_at"]` が ISO 8601 形式の文字列 (non-empty)
- **postcondition**: stale 検知に使用可能な timestamp
- **対応実装 (②)**: `generate_snapshot()` created_at 記録
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 D3 (snapshot が古くなる問題の warn 基盤)

#### I-156-053: plan_registry 抽出が task_id に関連する plan のみを返す

- **precondition**: plan_registry に PLAN-156 + 依存 PLAN + 無関係 PLAN-999 が存在
- **input**: `generate_snapshot(..., task_id="PLAN-156")`
- **expected output**: PLAN-999 は `payload["plan_registry"]` に含まれない
- **postcondition**: スコープ外 PLAN は除外される
- **対応実装 (②)**: `_extract_plan_registry()` task_id + dependencies フィルタリング
- **対応テストコード (④)**: `test_generate_snapshot_extracts_plan_registry` (4 件のみ)
- **DoD link**: ADR-040 D3

#### I-156-054: memory_links 抽出が task_id を含まない行を除外する

- **precondition**: MEMORY.md に "PLAN-156 relevant" と "unrelated entry" が混在
- **input**: `generate_snapshot(..., task_id="PLAN-156")`
- **expected output**: "unrelated entry" が `payload["memory_links"]` に含まれない
- **postcondition**: task_id に関連するエントリのみが snapshot される
- **対応実装 (②)**: `_extract_memory_links()` grep ロジック
- **対応テストコード (④)**: `test_generate_snapshot_extracts_memory_links`
- **DoD link**: ADR-040 D2

#### I-156-055: snapshot の plan_registry が status フィールドを含む

- **precondition**: plan_registry に status="in_progress" の PLAN-156 が存在
- **input**: `generate_snapshot(..., task_id="PLAN-156")`
- **expected output**: `payload["plan_registry"][0]["status"] == "in_progress"`
- **postcondition**: Codex 委譲先が plan status を参照可能
- **対応実装 (②)**: `_extract_plan_registry()` SELECT 列に status を含む
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 D3

---

### §3.4 helix_db v36 workspace_registry CRUD (I-156-061〜I-156-080)

#### I-156-061: migrate_v35_to_v36 が冪等である

- **precondition**: v35 baseline DB が存在
- **input**: `helix_db._migrate_v35_to_v36(conn)` を 2 回実行
- **expected output**: workspace_registry テーブルの columns に task_id / status が含まれる / `idx_workspace_registry_status` / `idx_workspace_registry_task_id` インデックスが存在
- **postcondition**: 2 回目の migrate が schema を破壊しない
- **対応実装 (②)**: `cli/lib/helix_db.py` `_migrate_v35_to_v36()`
- **対応テストコード (④)**: `test_workspace_registry.py::test_migrate_v35_to_v36_is_idempotent`
- **DoD link**: PLAN-156 AC-8 (py_compile PASS + unit test PASS)

#### I-156-062: migrate が schema_version を v36 に昇格する

- **precondition**: v35 baseline DB
- **input**: `helix_db.migrate(conn)`
- **expected output**: `SELECT MAX(version) FROM schema_version` == 36
- **postcondition**: schema_version テーブルに v36 の行が存在
- **対応実装 (②)**: `helix_db.py` migrate() v36 step
- **対応テストコード (④)**: `test_migrate_promotes_schema_to_36`
- **DoD link**: PLAN-156 AC-8

#### I-156-063: workspace_registry_insert + get が roundtrip する

- **precondition**: v36 DB が初期化済み
- **input**: `helix_db.workspace_registry_insert(conn, task_id="PLAN-156", workspace_path="/tmp/ws/plan-156", branch="workspace/PLAN-156", base_sha="abc123", reserved_resources={"ports": [8000]})`
- **expected output**: `row_id > 0` / `row["task_id"] == "PLAN-156"` / `row["reserved_resources"] == {"ports": [8000]}`
- **postcondition**: DB に 1 行存在
- **対応実装 (②)**: `helix_db.py` workspace_registry_insert() + workspace_registry_get()
- **対応テストコード (④)**: `test_workspace_registry_insert_and_get_roundtrip`
- **DoD link**: ADR-040 D1 (workspace metadata) + AC-4 (reserved_resources)

#### I-156-064: workspace_registry_insert が重複 task_id で IntegrityError を raise する

- **precondition**: WBS-003 が既に insert 済み
- **input**: 同じ task_id="WBS-003" で再 insert
- **expected output**: `sqlite3.IntegrityError` が raise される
- **postcondition**: DB の行数は変化しない (1 のまま)
- **対応実装 (②)**: `helix_db.py` workspace_registry PRIMARY KEY constraint
- **対応テストコード (④)**: `test_workspace_registry_insert_duplicate_task_id_raises_integrity_error`
- **DoD link**: ADR-040 D1 (task_id が workspace の一意識別子)

#### I-156-065: workspace_registry_get が存在しない task_id で None を返す

- **precondition**: v36 DB / PLAN-NOT-FOUND は insert されていない
- **input**: `helix_db.workspace_registry_get(conn, "PLAN-NOT-FOUND")`
- **expected output**: `row is None`
- **postcondition**: DB は変化しない
- **対応実装 (②)**: `helix_db.py` workspace_registry_get() fetchone None 処理
- **対応テストコード (④)**: `test_workspace_registry_get_returns_none_for_missing_task`
- **DoD link**: ADR-040 D1

#### I-156-066: workspace_registry_list が status でフィルタする

- **precondition**: A (active) と B (dropped) の 2 行が存在
- **input**: `helix_db.workspace_registry_list(conn, status="active")` / `list(conn, status="dropped")`
- **expected output**: active_rows=[A] / dropped_rows=[B]
- **postcondition**: それぞれ 1 件のみ返る
- **対応実装 (②)**: `helix_db.py` workspace_registry_list() WHERE status= フィルタ
- **対応テストコード (④)**: `test_workspace_registry_list_filters_by_status`
- **DoD link**: PLAN-156 AC-5

#### I-156-067: workspace_registry_update_status が drop メタデータを記録する

- **precondition**: DROP-1 が active で存在
- **input**: `helix_db.workspace_registry_update_status(conn, "DROP-1", status="dropped", drop_reason="force")`
- **expected output**: `updated is True` / `row["status"] == "dropped"` / `row["drop_reason"] == "force"` / `row["dropped_at"]` が non-empty
- **postcondition**: DB の DROP-1 行が dropped に遷移
- **対応実装 (②)**: `helix_db.py` workspace_registry_update_status()
- **対応テストコード (④)**: `test_workspace_registry_update_status_records_drop_metadata`
- **DoD link**: ADR-040 D7

#### I-156-068: workspace_registry_update_status が存在しない task_id で False を返す

- **precondition**: NO-TASK は存在しない
- **input**: `helix_db.workspace_registry_update_status(conn, "NO-TASK", status="merged")`
- **expected output**: `updated is False`
- **postcondition**: DB は変化しない
- **対応実装 (②)**: `helix_db.py` workspace_registry_update_status() rowcount check
- **対応テストコード (④)**: `test_workspace_registry_update_status_returns_false_for_missing_task`
- **DoD link**: ADR-040 D1

#### I-156-069: workspace_registry が invalid status で IntegrityError を raise する (CHECK constraint)

- **precondition**: v36 DB
- **input**: `conn.execute(INSERT ... status='invalid')` 直接実行
- **expected output**: `sqlite3.IntegrityError` が raise される
- **postcondition**: DB に invalid row は挿入されない
- **対応実装 (②)**: `helix_db.py` workspace_registry CHECK constraint (status IN ('active', 'merged', 'dropped'))
- **対応テストコード (④)**: `test_workspace_registry_status_check_constraint_violation_raises_integrity_error`
- **DoD link**: ADR-040 D5 (drop に統一) + D1

#### I-156-070: workspace_registry_update_status が B の update で A に影響しない (独立性)

- **precondition**: A (active) と B (active) の 2 行が存在
- **input**: `workspace_registry_update_status(conn, "B", status="dropped")`
- **expected output**: `workspace_registry_get(conn, "A")["status"] == "active"`
- **postcondition**: A は active のまま
- **対応実装 (②)**: workspace_registry_update_status() WHERE task_id= の正確な条件
- **対応テストコード (④)**: `test_workspace_registry_list_filters_by_status` (A が active 確認)
- **DoD link**: ADR-040 D1

#### I-156-071: workspace_registry_insert が reserved_resources=None でも正常に insert する

- **precondition**: v36 DB
- **input**: `workspace_registry_insert(conn, task_id="NO-RES", ..., reserved_resources=None)` (または省略)
- **expected output**: row_id > 0 / `row["reserved_resources"]` は None または {}
- **postcondition**: reserved_resources が省略可能
- **対応実装 (②)**: `helix_db.py` workspace_registry_insert() reserved_resources デフォルト
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 AC-4

#### I-156-072: migrate が v35 以前の DB に v36 を適用できる (migration chain)

- **precondition**: v35 よりも古い DB (例: schema migration を v35 まで適用済)
- **input**: `helix_db.migrate(conn)` (chain 全体)
- **expected output**: `MAX(version) == 36` / workspace_registry テーブルが存在
- **postcondition**: migration chain が正常に完結
- **対応実装 (②)**: `helix_db.py` migrate() chain
- **対応テストコード (④)**: `test_migrate_promotes_schema_to_36`
- **DoD link**: PLAN-156 AC-8

#### I-156-073: workspace_registry_list が status=None のとき全行を返す

- **precondition**: active 2 件 + dropped 1 件が存在
- **input**: `helix_db.workspace_registry_list(conn, status=None)` または `list(conn)`
- **expected output**: 3 件返る
- **postcondition**: フィルタなし動作
- **対応実装 (②)**: workspace_registry_list() status=None 分岐
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: PLAN-156 AC-5

#### I-156-074: workspace_registry が idx_workspace_registry_task_id index を持つ

- **precondition**: v36 migrate 後
- **input**: `PRAGMA index_list(workspace_registry)`
- **expected output**: `"idx_workspace_registry_task_id"` が index 一覧に含まれる
- **postcondition**: task_id 検索が高速
- **対応実装 (②)**: `_migrate_v35_to_v36()` CREATE INDEX IF NOT EXISTS
- **対応テストコード (④)**: `test_migrate_v35_to_v36_is_idempotent`
- **DoD link**: ADR-040 D1

#### I-156-075: workspace_registry が idx_workspace_registry_status index を持つ

- **precondition**: v36 migrate 後
- **input**: `PRAGMA index_list(workspace_registry)`
- **expected output**: `"idx_workspace_registry_status"` が含まれる
- **postcondition**: status フィルタ検索が高速
- **対応実装 (②)**: `_migrate_v35_to_v36()` CREATE INDEX IF NOT EXISTS
- **対応テストコード (④)**: `test_migrate_v35_to_v36_is_idempotent`
- **DoD link**: ADR-040 D1

#### I-156-076: workspace_registry_get が reserved_resources を dict として返す

- **precondition**: reserved_resources={"ports": [8000]} で insert 済み
- **input**: `workspace_registry_get(conn, "PLAN-156")`
- **expected output**: `row["reserved_resources"] == {"ports": [8000]}` (dict 型)
- **postcondition**: JSON シリアライズ/デシリアライズが透過的
- **対応実装 (②)**: `helix_db.py` reserved_resources JSON serialize/deserialize
- **対応テストコード (④)**: `test_workspace_registry_insert_and_get_roundtrip`
- **DoD link**: ADR-040 AC-4

#### I-156-077: workspace_registry_insert が created_at を自動設定する

- **precondition**: v36 DB
- **input**: `workspace_registry_insert(conn, ...)`
- **expected output**: `row["created_at"]` が非空文字列 (ISO 形式)
- **postcondition**: created_at が自動で記録される
- **対応実装 (②)**: `helix_db.py` workspace_registry INSERT DEFAULT datetime('now')
- **対応テストコード (④)**: `test_workspace_registry_insert_and_get_roundtrip` (created_at 確認)
- **DoD link**: ADR-040 D1

#### I-156-078: workspace_registry_insert が updated_at を created_at と同値で初期設定する

- **precondition**: v36 DB
- **input**: `workspace_registry_insert(conn, ...)`
- **expected output**: `row["updated_at"] == row["created_at"]` (insert 直後)
- **postcondition**: updated_at が created_at と同値
- **対応実装 (②)**: `helix_db.py` INSERT updated_at=datetime('now')
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 D1

#### I-156-079: workspace_registry_update_status が updated_at を更新する

- **precondition**: A が insert 済み (created_at/updated_at が設定済み)
- **input**: `workspace_registry_update_status(conn, "A", status="dropped")`
- **expected output**: `row["updated_at"]` が insert 時の created_at と異なる可能性 (実装依存)
- **postcondition**: updated_at が status 変更時に更新される
- **対応実装 (②)**: `helix_db.py` UPDATE SET updated_at=datetime('now')
- **対応テストコード (④)**: `test_workspace_registry_update_status_records_drop_metadata`
- **DoD link**: ADR-040 D1

#### I-156-080: workspace_registry テーブルが PLAN-156 AC-4 の reserved_resources field を持つ

- **precondition**: v36 migrate 後
- **input**: `PRAGMA table_info(workspace_registry)`
- **expected output**: columns に `reserved_resources` が含まれる
- **postcondition**: AC-4 フィールドが schema に存在
- **対応実装 (②)**: `_migrate_v35_to_v36()` CREATE TABLE 定義
- **対応テストコード (④)**: `test_migrate_v35_to_v36_is_idempotent` (columns assertion)
- **DoD link**: ADR-040 AC-4

---

### §3.5 D7 drop fail-safe + D8 E2E sentinel (I-156-081〜I-156-100)

#### I-156-081: drop force が変更ありで trash を作成して workspace を削除する

- **precondition**: PLAN-FORCE workspace が active / untracked.txt が存在
- **input**: `manager.drop("PLAN-FORCE", force=True)`
- **expected output**: `drop_result["dropped"] is True` / workspace_path 不在 / trash_path に changes.bundle + untracked.tar.gz が存在 / list_workspaces("dropped") に PLAN-FORCE が含まれる
- **postcondition**: workspace は消え、trash に退避ファイルが存在
- **対応実装 (②)**: `workspace_manager.py` drop(force=True) bundle + tar 退避
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace`
- **DoD link**: ADR-040 D7

#### I-156-082: drop default が未コミット変更で WorkspaceDropAbortedError を raise する

- **precondition**: workspace に未コミットの README.md 変更が存在
- **input**: `manager.drop("PLAN-DROP")` (force=False)
- **expected output**: `WorkspaceDropAbortedError` が raise される
- **postcondition**: workspace は削除されない
- **対応実装 (②)**: `workspace_manager.py` drop() abort on dirty
- **対応テストコード (④)**: `test_drop_default_aborts_when_workspace_has_changes`
- **DoD link**: ADR-040 D7

#### I-156-083: drop force が trash に変更なしでも clean に workspace を削除できる

- **precondition**: workspace に変更なし (clean state)
- **input**: `manager.drop("PLAN-CLEAN", force=True)`
- **expected output**: `drop_result["dropped"] is True` / workspace_path 不在
- **postcondition**: 変更なし workspace も force=True で削除可能
- **対応実装 (②)**: `workspace_manager.py` drop(force=True) clean path
- **対応テストコード (④)**: 追加 test 推奨 (clean workspace の force drop)
- **DoD link**: ADR-040 D7

#### I-156-084: trash path が `~/.helix/workspace-trash/<task>/<timestamp>/` 形式になる

- **precondition**: drop force 実行後
- **input**: `drop_result["trash_path"]`
- **expected output**: `trash_path` が `home/.helix/workspace-trash/PLAN-FORCE/<timestamp>/` を含む
- **postcondition**: trash path の命名規則が ADR-040 D7 に準拠
- **対応実装 (②)**: `workspace_manager.py` trash path 生成ロジック
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace` (trash_path)
- **DoD link**: ADR-040 D7

#### I-156-085: prune dry-run が filesystem を変更しない (幂等性)

- **precondition**: orphan registry entry が存在
- **input**: `manager.prune(dry_run=True)` を 2 回実行
- **expected output**: stale リストが同じ / registry ファイルは依然存在
- **postcondition**: dry_run は副作用なし
- **対応実装 (②)**: `workspace_manager.py` prune(dry_run=True) 幂等性
- **対応テストコード (④)**: `test_prune_dry_run_lists_orphan_candidates_without_mutation`
- **DoD link**: ADR-040 D7

#### I-156-086: prune が workspace_path が実在しない registry を orphan と判定する

- **precondition**: registry に workspace_path=/tmp/missing が存在 (ディレクトリ不在)
- **input**: `manager.prune(dry_run=True)`
- **expected output**: `stale == ["PLAN-ORPHAN"]`
- **postcondition**: orphan 判定は filesystem の存在チェックに基づく
- **対応実装 (②)**: `workspace_manager.py` prune() Path.exists() チェック
- **対応テストコード (④)**: `test_prune_dry_run_lists_orphan_candidates_without_mutation`
- **DoD link**: ADR-040 D7

#### I-156-087: D8 sentinel Layer 2 — workspace exec で Codex CLI が workspace cwd を使用する (Sprint .4)

- **precondition**: workspace が active / Codex CLI が利用可能
- **input**: `helix workspace exec --task PLAN-156 "echo \$PWD"` (bash または helix CLI 経由)
- **expected output**: 出力が `~/.helix/workspaces/<repo>/PLAN-156` パスを含む (main workspace の cwd ではない)
- **postcondition**: Codex CLI が workspace cwd を respect している → AC-5 satisfied
- **対応実装 (②)**: `workspace_manager.py` exec_in_workspace() + `cli/helix-workspace exec` subcommand
- **対応テストコード (④)**: Layer 2 手動実行 (Sprint .4) / 自動化は将来 PLAN
- **DoD link**: ADR-040 D8 Layer 2 / AC-5

#### I-156-088: D8 sentinel Layer 2 FAIL 判定 — main への write が可能な場合は ADR-041 起票

- **precondition**: Layer 2 実行で Codex CLI が main workspace への write を行えた
- **input**: `exec "echo test > <main_path>/test_write"` → write 成功
- **expected output**: **FAIL**: git worktree isolation では Codex sandbox 問題を解決できない
- **postcondition**: ADR-041 (container isolation fallback) を起票して Sprint .4 を完了とする
- **対応実装 (②)**: (FAIL 時のみ) ADR-041 + container 案への差戻し
- **対応テストコード (④)**: Layer 2 手動実行 (Sprint .4)
- **DoD link**: ADR-040 D8 / AC-5

#### I-156-089: D8 sentinel Layer 3 — 2 workspace 同時 exec が helix-db.lock 競合を起こさない (Sprint .5 or 別 PLAN)

- **precondition**: PLAN-A と PLAN-B の 2 workspace が active
- **input**: `exec_in_workspace("PLAN-A", "sleep 0.1")` と `exec_in_workspace("PLAN-B", "sleep 0.1")` を並列実行
- **expected output**: 両方の exit code が 0 / helix-db.lock timeout エラーが発生しない
- **postcondition**: 並列実行が正常に完了
- **対応実装 (②)**: 各 workspace が独立 `.helix/helix.db` を持つ (ADR-040 D3)
- **対応テストコード (④)**: Sprint .5 or PLAN-163 で設計 (本 Sprint 範囲外)
- **DoD link**: ADR-040 D3 + D9 (Phase 2)

#### I-156-090: D7 trash の changes.bundle が有効な git bundle である

- **precondition**: force drop 実行後 / trash に changes.bundle が存在
- **input**: `git bundle verify <trash>/changes.bundle`
- **expected output**: git bundle verify が exit 0 で成功
- **postcondition**: bundle からの復元が可能
- **対応実装 (②)**: `workspace_manager.py` drop(force=True) `git bundle create --all`
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace` (changes.bundle 存在確認)
- **DoD link**: ADR-040 D7

#### I-156-091: D7 trash の untracked.tar.gz が untracked file を含む

- **precondition**: workspace に untracked.txt が存在 / force drop 実行
- **input**: `tarfile.open(trash/untracked.tar.gz).getnames()`
- **expected output**: "untracked.txt" が tar の contents に含まれる
- **postcondition**: untracked ファイルが退避されている
- **対応実装 (②)**: `workspace_manager.py` drop(force=True) tar.gz 生成
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace` (untracked.tar.gz 存在確認)
- **DoD link**: ADR-040 D7

#### I-156-092: drop 後に workspace の branch が git から参照できなくなる

- **precondition**: force drop 実行後 / branch `workspace/PLAN-FORCE`
- **input**: `git branch --list workspace/PLAN-FORCE` (main repo)
- **expected output**: branch が残るか削除されるか (実装依存、ドキュメント化必要)
- **postcondition**: drop 後の branch 状態が明確
- **対応実装 (②)**: `workspace_manager.py` drop() branch cleanup ポリシー
- **対応テストコード (④)**: 追加 test 推奨 (branch cleanup の明示)
- **DoD link**: ADR-040 D7 (branch 削除 option)

#### I-156-093: drop が status を "dropped" に更新する

- **precondition**: PLAN-FORCE が drop 実行前は active
- **input**: `manager.drop("PLAN-FORCE", force=True)`
- **expected output**: `manager.list_workspaces(status="dropped")[0]["task_id"] == "PLAN-FORCE"`
- **postcondition**: registry の status が "dropped" に遷移
- **対応実装 (②)**: `workspace_manager.py` drop() `_update_registry_status(status="dropped")`
- **対応テストコード (④)**: `test_drop_force_archives_and_removes_workspace`
- **DoD link**: ADR-040 D7 + D1

#### I-156-094: D8 sentinel Layer 1 PASS 確認 (Sprint .3 完了証跡)

- **precondition**: Sprint .3 時点の bash 直接実行 (commit 1724be5 後)
- **input**: bash で `workspace exec PLAN-X "pwd"` / `"echo sentinel > workspace_test.txt"` / `"ls <main_path>"`
- **expected output**: cwd = workspace_path / workspace_test.txt 作成成功 / main path read 可
- **postcondition**: Layer 1 PASS が Sprint .3 完了時に手動確認済 (本テスト設計はこれを文書化)
- **対応実装 (②)**: WorkspaceManager.exec_in_workspace() + cwd 設定
- **対応テストコード (④)**: Sprint .3 手動確認済 (自動テスト化は I-156-087)
- **DoD link**: ADR-040 D8 Layer 1

#### I-156-095: WorkspaceDropAbortedError が適切なメッセージを含む

- **precondition**: workspace に未コミット変更
- **input**: `manager.drop(task_id)` (force=False)
- **expected output**: `WorkspaceDropAbortedError` の message が task_id または変更数を示す文字列を含む
- **postcondition**: エラーが診断情報を含む
- **対応実装 (②)**: `workspace_manager.py` WorkspaceDropAbortedError 定義
- **対応テストコード (④)**: `test_drop_default_aborts_when_workspace_has_changes`
- **DoD link**: ADR-040 D7

#### I-156-096: drop default が clean workspace を正常に削除する

- **precondition**: workspace に変更なし (git status clean)
- **input**: `manager.drop("PLAN-CLEAN")` (force=False)
- **expected output**: `drop_result["dropped"] is True` / workspace_path 不在
- **postcondition**: clean workspace は default drop で削除可能
- **対応実装 (②)**: `workspace_manager.py` drop() clean path (abort しない)
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 D7

#### I-156-097: prune が active + 実在 workspace を orphan と判定しない

- **precondition**: PLAN-LIVE の workspace_path が実在する
- **input**: `manager.prune(dry_run=True)`
- **expected output**: `stale` に PLAN-LIVE が含まれない
- **postcondition**: 正常 workspace は誤判定されない
- **対応実装 (②)**: `workspace_manager.py` prune() 存在チェック条件
- **対応テストコード (④)**: 追加 test 推奨 (false positive 防止)
- **DoD link**: ADR-040 D7

#### I-156-098: drop の trash path が timestamp を含み衝突しない

- **precondition**: 同じ task_id を 2 回 create/drop するシナリオ
- **input**: `drop(force=True)` を 2 回実行
- **expected output**: 2 つの trash path が異なる timestamp を持つ
- **postcondition**: 同一 task の 2 回 drop で trash が上書きされない
- **対応実装 (②)**: `workspace_manager.py` trash path に timestamp を含める
- **対応テストコード (④)**: 追加 test 推奨
- **DoD link**: ADR-040 D7

#### I-156-099: D8 sentinel Layer 2 実行前の preflight check で orphan/dirty を事前確認する

- **precondition**: Layer 2 実行前
- **input**: `manager.preflight(task_id)` → issues 確認 → issues が空なら exec
- **expected output**: preflight PASS → Layer 2 exec 実行 / issues あり → 修正後に再試行
- **postcondition**: E2E sentinel 実行前に環境を健全化
- **対応実装 (②)**: preflight() + exec_in_workspace() の連携フロー
- **対応テストコード (④)**: Layer 2 実行手順の一部 (§5 参照)
- **DoD link**: ADR-040 D7 + D8

#### I-156-100: helix workspace CLI が create / list / exec / preflight / drop / prune の全 subcommand を実行できる

- **precondition**: `cli/helix-workspace` が存在 / workspace_manager + workspace_cli が import 可能
- **input**: `helix workspace create --task PLAN-X` / `list` / `exec` / `preflight` / `drop` / `prune --dry-run`
- **expected output**: 各 subcommand が正常終了 (exit code 0) または期待エラー (exit code != 0)
- **postcondition**: CLI 全 subcommand が正常に動作
- **対応実装 (②)**: `cli/helix-workspace` bash router + `cli/lib/workspace_cli.py` dispatcher
- **対応テストコード (④)**: E2E 手動実行 (Sprint .4) / bats test 追加推奨
- **DoD link**: PLAN-156 AC-1〜5 全体

---

## §4 既存 unit test (artifact ④) との対応表

### 4.1 test_workspace_manager.py (24 case)

| Test 関数 (④) | Integration design (③) | 設計章 (①) | 優先度 |
|---|---|---|---|
| `test_create_creates_worktree_and_workspace_manifest` | I-156-001 | ADR-040 D1 / D2 | H |
| `test_create_twice_raises_workspace_exists` | I-156-002 | ADR-040 D1 | H |
| `test_create_does_not_copy_denylist_content` | I-156-003 | ADR-040 D2 | H |
| `test_create_copies_allowlist_content` | I-156-004 | ADR-040 D2 | H |
| `test_filtered_copy_skips_db_wal_glob` | I-156-005 | ADR-040 D2 | M |
| `test_list_workspaces_filters_active_entries` | I-156-006 | PLAN-156 AC-5 | H |
| `test_exec_in_workspace_returns_exit_code_zero_for_true_command` | I-156-021 | ADR-040 D8 | H |
| `test_exec_in_workspace_propagates_nonzero_exit_code` | I-156-022 | PLAN-156 AC-2 | H |
| `test_exec_in_workspace_raises_for_missing_task` | I-156-023 | PLAN-156 AC-2 | H |
| `test_exec_in_workspace_raises_for_dropped_status` | I-156-018 | PLAN-156 AC-2 | H |
| `test_exec_in_workspace_injects_helix_workspace_env_vars` | I-156-024 / I-156-025 / I-156-026 / I-156-028 | ADR-040 D5 / D8 | H |
| `test_preflight_detects_main_dirty` | I-156-007 / I-156-014 | ADR-040 D7 | H |
| `test_preflight_detects_orphan_worktree` | I-156-008 | ADR-040 D7 | H |
| `test_preflight_detects_branch_divergence` | I-156-009 | ADR-040 D6 / D7 | M |
| `test_drop_default_aborts_when_workspace_has_changes` | I-156-010 / I-156-082 | ADR-040 D7 | H |
| `test_drop_force_archives_and_removes_workspace` | I-156-011 / I-156-081 / I-156-084 / I-156-090 / I-156-091 / I-156-093 | ADR-040 D7 | H |
| `test_prune_dry_run_lists_orphan_candidates_without_mutation` | I-156-012 / I-156-085 / I-156-086 | ADR-040 D7 | M |
| `test_generate_snapshot_minimal_schema_version_one` | I-156-041 / I-156-047 / I-156-048 | ADR-040 D3 | H |
| `test_generate_snapshot_extracts_plan_registry` | I-156-042 / I-156-046 / I-156-050 / I-156-053 | ADR-040 D3 | H |
| `test_generate_snapshot_extracts_handover_snapshot` | I-156-043 | ADR-040 D2 | H |
| `test_generate_snapshot_extracts_memory_links` | I-156-044 / I-156-054 | ADR-040 D2 | M |
| `test_generate_snapshot_handles_missing_helix_db_gracefully` | I-156-045 / I-156-049 / I-156-051 | ADR-040 D3 | H |
| `test_create_writes_registry_file_fallback` | I-156-013 | PLAN-156 AC-1 | M |
| `test_inject_helix_workspace_env_vars_preserves_os_environment` | I-156-027 / I-156-032 / I-156-033 | PLAN-156 AC-2 | H |

### 4.2 test_workspace_registry.py (9 case)

| Test 関数 (④) | Integration design (③) | 設計章 (①) | 優先度 |
|---|---|---|---|
| `test_migrate_v35_to_v36_is_idempotent` | I-156-061 / I-156-074 / I-156-075 / I-156-080 | ADR-040 D1 | H |
| `test_migrate_promotes_schema_to_36` | I-156-062 / I-156-072 | PLAN-156 AC-8 | H |
| `test_workspace_registry_insert_and_get_roundtrip` | I-156-063 / I-156-076 / I-156-077 | ADR-040 D1 / AC-4 | H |
| `test_workspace_registry_insert_duplicate_task_id_raises_integrity_error` | I-156-064 | ADR-040 D1 | H |
| `test_workspace_registry_get_returns_none_for_missing_task` | I-156-065 | ADR-040 D1 | M |
| `test_workspace_registry_list_filters_by_status` | I-156-066 / I-156-070 | PLAN-156 AC-5 | H |
| `test_workspace_registry_update_status_records_drop_metadata` | I-156-067 / I-156-079 | ADR-040 D7 | H |
| `test_workspace_registry_update_status_returns_false_for_missing_task` | I-156-068 | ADR-040 D1 | M |
| `test_workspace_registry_status_check_constraint_violation_raises_integrity_error` | I-156-069 | ADR-040 D5 | H |

---

## §5 D8 E2E sentinel check 設計

ADR-040 §D8 の Codex sandbox E2E 検証を 3 層で設計する。

### Layer 1: bash 直接実行 (Sprint .3 完了済)

Sprint .3 完了時 (commit 1724be5 後) に Opus が bash 直接実施。

**実施手順**:

```bash
# workspace 作成
helix workspace create --task PLAN-156-E2E-TEST

# cwd 検証
helix workspace exec --task PLAN-156-E2E-TEST "pwd"
# 期待: ~/.helix/workspaces/ai-dev-kit-vscode/PLAN-156-E2E-TEST

# env injection 検証
helix workspace exec --task PLAN-156-E2E-TEST "echo \$HELIX_WORKSPACE_TASK_ID"
# 期待: PLAN-156-E2E-TEST

# workspace 内 write 検証
helix workspace exec --task PLAN-156-E2E-TEST "echo sentinel > workspace_test.txt && cat workspace_test.txt"
# 期待: sentinel (workspace 内への write 成功)

# main path read 検証
helix workspace exec --task PLAN-156-E2E-TEST "ls $(pwd)/README.md"
# 期待: README.md が見える (read は可能)
```

**結果 (Sprint .3 完了時)**: PASS (Opus 直接確認済)

**対応 test case**: I-156-029 / I-156-094

---

### Layer 2: Codex CLI 経由実行 (Sprint .4 で実施)

Codex CLI を workspace exec で起動し、sandbox 挙動を検証する。

**実施手順**:

```bash
# Step 1: preflight で環境健全性確認
helix workspace preflight --task PLAN-156
# 期待: ok=true / issues が空か warn のみ

# Step 2: Codex CLI の cwd 検証
helix workspace exec --task PLAN-156 "codex exec 'echo \$PWD'"
# 期待: workspace path が出力される (main cwd ではない)

# Step 3: Codex CLI sandbox 内での write 検証
helix workspace exec --task PLAN-156 "codex exec 'echo codex_test > codex_sentinel.txt'"
# 期待: workspace 内に codex_sentinel.txt が作成される

# Step 4: main workspace への write ブロック検証 (AC-5 核心)
MAIN_PATH=$(pwd)
helix workspace exec --task PLAN-156 "codex exec \"echo main_write_test > ${MAIN_PATH}/codex_main_write_test.txt\""
# 期待 (PASS): ファイルが作成されない または Permission denied
# 失敗 (FAIL): ファイルが作成される → ADR-041 起票トリガー
```

**判定基準**:

| 結果 | 対応 |
|---|---|
| PASS: main への write がブロックされる | AC-5 satisfied / ADR-040 "Accepted" へ格上げ |
| FAIL: main への write が可能 | ADR-041 (container isolation fallback) 起票 / PLAN-156 AC-5 に failure 記録 |

**対応 test case**: I-156-087 / I-156-088 / I-156-099

---

### Layer 3: 並列実行 helix-db.lock 競合なし確認 (Sprint .5 or PLAN-163)

2 workspace を同時 exec して helix-db.lock 競合が発生しないことを確認する。

**実施手順 (概要)**:

```bash
# 2 workspace を作成
helix workspace create --task PLAN-PARA-A
helix workspace create --task PLAN-PARA-B

# 並列 exec
helix workspace exec --task PLAN-PARA-A "sleep 0.5 && echo done_A" &
helix workspace exec --task PLAN-PARA-B "sleep 0.5 && echo done_B" &
wait

# 両方が正常終了 (exit code 0) かつ lock timeout エラーなし
```

**対応 test case**: I-156-089 (Sprint .5 or PLAN-163 範囲)

---

## §6 追加 test 推奨 (既存 test で未カバーの case)

以下の I-156 case は既存 test (artifact ④) が存在しないため、Sprint .4 以降で追加推奨:

| case ID | title | 優先度 |
|---|---|---|
| I-156-015 | list_workspaces status=None 全件返却 | M |
| I-156-016 | create が base_sha を manifest に記録する | H |
| I-156-019 | preflight が存在しない task_id で WorkspaceNotFoundError | M |
| I-156-020 | prune 実行 (dry_run=False) が orphan を削除する | M |
| I-156-031 | exec が空文字コマンドで安全に動作する | L |
| I-156-035 | exec が merged 状態で ValueError | M |
| I-156-037 | exec が monkeypatch returncode=42 を返す | L |
| I-156-038 | extra_env に HELIX_WORKSPACE_* を含む場合の上書きポリシー | M |
| I-156-052 | snapshot が created_at を ISO timestamp で記録する | M |
| I-156-055 | snapshot の plan_registry が status フィールドを含む | M |
| I-156-071 | workspace_registry_insert が reserved_resources=None で正常動作 | M |
| I-156-073 | workspace_registry_list が status=None のとき全行を返す | M |
| I-156-078 | insert が updated_at を created_at と同値で初期設定する | L |
| I-156-083 | drop force が clean workspace を削除できる | H |
| I-156-092 | drop 後の branch cleanup ポリシー確認 | M |
| I-156-096 | drop default が clean workspace を正常に削除する | H |
| I-156-097 | prune が active + 実在 workspace を誤判定しない | H |
| I-156-098 | trash path の timestamp が衝突しない | M |
| I-156-100 | helix workspace CLI の全 subcommand が動作する (bats) | H |

---

## §7 carry / 残課題

- **AC-5**: D8 Layer 2 (Codex CLI 経由) の PASS/FAIL 判定は Sprint .4 実施結果次第
  - FAIL 時: ADR-041 (container isolation fallback) 起票
  - PASS 時: ADR-040 "Accepted with conditions" → "Accepted" へ格上げ
- **D8 Layer 3**: 並列実行検証は Sprint .5 または PLAN-163 (merge 実装) と同期
- **merge subcommand**: PLAN-163 / Phase 2 で別途設計 (本 PLAN-156 スコープ外)
- **live main DB read-only 参照**: D3 で廃案、Phase 2 で再検討 (PLAN-163 以降)
- **bats E2E test**: I-156-100 の CLI 全 subcommand test は Sprint .4 追加推奨

---

## §8 case 数集計

| ブロック | 範囲 | 件数 |
|---|---|---|
| workspace lifecycle | I-156-001〜I-156-020 | 20 case |
| exec / cwd / env injection | I-156-021〜I-156-040 | 20 case |
| snapshot 実データ取得 | I-156-041〜I-156-060 | 15 case |
| helix_db v36 workspace_registry CRUD | I-156-061〜I-156-080 | 20 case |
| D7 drop fail-safe + D8 E2E sentinel | I-156-081〜I-156-100 | 20 case |
| **合計** | I-156-001〜I-156-100 | **95 case** |

既存 artifact ④ との対応:
- test_workspace_manager.py 24 case: 全件マッピング完了 (§4.1)
- test_workspace_registry.py 9 case: 全件マッピング完了 (§4.2)
- 合計 33 case: 全件 ③ テスト設計に trace 済み

---

## §9 DoD

- 本書の 95 case (I-156-001〜I-156-100) が G4 で管理され、Sprint .4 完了時に既存 33 case が全 PASS
- `PLAN-156-helix-workspace-worktree-isolation.md` から本文書への reference が存在
- `cli/lib/tests/test_workspace_manager.py` + `test_workspace_registry.py` の対象 test 関数が本文書の case ID を逆参照できる
- D8 Layer 2 の PASS/FAIL 判定が §5 Layer 2 の判定基準に従って記録されている
- PLAN-087 WebSearch 3 query 実施済 (§2.4 に記録)

---

## §10 References

- **IEEE Std 829-2008**: IEEE Standard for Software and System Test Documentation
- **ISO/IEC/IEEE 29119-3:2021**: Software and systems engineering — Software testing — Part 3: Test documentation (clause 9.2 TestCaseSpecification)
- pytest 公式 docs: https://docs.pytest.org/en/stable/how-to/fixtures.html
- git-worktree 公式: https://git-scm.com/docs/git-worktree
- ADR-040: `docs/adr/ADR-040-helix-workspace-isolation.md` (本 PLAN tree の L2 snapshot)
- PLAN-075: V-model 4 artifact framework (`docs/plans/PLAN-075-vmodel-design-test-mapping.md`)
- PLAN-068-integration-test-design.md: format 範例 (`docs/v2/L4-test-design/PLAN-068-integration-test-design.md`)
- PLAN-223: pytest-xdist 並列下 fixture isolation 確立 (conftest function-scoped autouse pattern)
- Claude Code worktrees: https://code.claude.com/docs/en/worktrees
- SQLite isolation: https://sqlite.org/isolation.html
