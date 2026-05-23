---
plan_id: PLAN-163
title: helix workspace CLI subcommand 詳細設計・実装 (PLAN-156 子 PLAN、PLAN-156 で吸収完遂、superseded)
status: superseded
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-156-helix-workspace-worktree-isolation.md   # from dependencies.parent
superseded_by: PLAN-156
status_history:
  - 2026-05-23: draft (前 session 連続起票で作成、PLAN-156 子 PLAN として定義)
  - 2026-05-24: superseded (PLAN-156 Sprint .2-.4 で本 PLAN scope 全実装済、commit 098ba97/1724be5/4e47004 で完遂)
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — Sprint .1-.3 helix workspace subcommand 完全実装 (create / list / merge / drop)"
  - role: qa
    slot_label: "QA — Sprint .4 unit + integration test 設計・実装 (test_workspace_cli.py)"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-156 設計整合確認・lifecycle 設計レビュー・G4 review"
generates:
  - artifact_type: cli_extension
    path: cli/helix-workspace
  - artifact_type: python_module
    path: cli/lib/workspace_manager.py
  - artifact_type: test
    path: cli/lib/tests/test_workspace_cli.py
  - artifact_type: doc_update
    path: docs/commands/index.md
dependencies:
  parent: PLAN-156
  requires:
    - PLAN-156
  blocks: []
related_adr:
  - ADR-059-helix-workspace-isolation-extended
related_docs:
  - docs/plans/PLAN-156-helix-workspace-worktree-isolation.md
  - cli/helix
  - cli/lib/workspace_manager.py
  - docs/commands/index.md
acceptance_criteria:
  - "helix workspace create --task PLAN-X が git worktree + .helix/ コピーで workspace を作成できる"
  - "helix workspace list が現在の workspace 一覧を表示できる"
  - "helix workspace merge --task PLAN-X が workspace の patch を main に適用できる"
  - "helix workspace drop --task PLAN-X が worktree を clean に削除できる"
  - "python3 -m py_compile cli/lib/workspace_manager.py PASS"
  - "bash -n cli/helix-workspace PASS"
  - "pytest cli/lib/tests/test_workspace_cli.py -v 全件 PASS"
  - "cli/helix top-level router に workspace subcommand が登録されている"
  - "docs/commands/index.md に workspace コマンドが記載されている"
---

# PLAN-163: helix workspace CLI subcommand 詳細設計・実装 (PLAN-156 子 PLAN、superseded)

## status: superseded by PLAN-156 (2026-05-24)

本 PLAN は前 session 連続起票時 (2026-05-23) に「PLAN-156 子 PLAN」として `helix workspace` CLI subcommand 詳細設計・実装を担う目的で起票された。しかし PLAN-156 自身が Sprint .2-.4 で本 PLAN scope を完全に吸収する形で完遂したため、本 PLAN は **superseded** となる。

### PLAN-156 完遂状況 (本 PLAN 内容との対応)

| 旧 PLAN-163 Sprint | 実装担当 | 完遂 commit |
|---|---|---|
| Sprint .1 (helix-workspace bash dispatcher + WorkspaceManager skeleton) | PLAN-156 Sprint .2 (Codex se) | `098ba97` |
| Sprint .2 (WorkspaceManager 完全実装: create / list / merge / drop) | PLAN-156 Sprint .3 (Codex se) | `1724be5` |
| Sprint .3 (docs 更新) | PLAN-156 Sprint .3 (Codex se) | `1724be5` |
| Sprint .4 (テスト T1〜T8 8 case) | PLAN-156 Sprint .3-.4 (test_workspace_manager.py 24 case + integration test design 95 case) | `1724be5` / `4e47004` |

### `merge` subcommand 取り扱いの差分

- 旧 PLAN-163 は `merge` を MVP に含めていた
- ADR-040 D4 で `merge` は **MVP 範囲外** と確定 (標準 git flow を正本にする、HELIX 独自 merge は実装複雑度高で却下)
- → `merge` 実装は **Phase 2 (新 PLAN-224)** で別途扱う

### 後継 PLAN

Phase 2 (workspace merge convenience + D8 Layer 3 並列 lock 競合検証 + AC-6 symlink immutable snapshot 限定採用 判定) は **PLAN-224** で起票・管理する。

以下は historical reference として保持 (本 PLAN は status: superseded で実装着手しない):

---

## L2 凍結 (ADR snapshot)

本 PLAN は PLAN-156 の子 PLAN として、**ADR-040** (PLAN-156 tree の L2 凍結) の設計方針を実装に落とす。
新規 L2 大局判断なし。ADR-040 で確定された以下の方針を所与として実装する:

- `.helix/` コピー戦略 (A/B/C から ADR-040 で確定)
- helix.db isolation 方針 (workspace 専用 db vs main db read-only mount)
- merge 戦略 (git diff patch apply vs rsync vs git merge)
- cleanup fail-safe 設計

## 背景

PLAN-156 が helix workspace isolation の全体方針・設計・ADR を担う parent PLAN であるのに対し、
本 PLAN は CLI subcommand 詳細設計と実装に特化する子 PLAN。

PLAN-156 では Sprint .1 (OSS 調査・ADR-040) / Sprint .2 (helix.db isolation + workspace_manager.py skeleton) を
担当し、本 PLAN では Sprint .3 以降の CLI 完全実装 + テスト + router 登録を引き受ける。

### WebSearch skip 理由 (PLAN-087 ガードレール遵守)

本 PLAN は PLAN-156 の実装子 PLAN であり、新規 framework 採用判断を含まない。
PLAN-156 Sprint .1 で pmo-tech-fork が WebSearch 3 query を実施済みであり、
その結果を所与として実装を進める。WebSearch **skip**。

## 設計方針

### subcommand 一覧と責務

```
helix workspace create --task <PLAN-X> [--branch workspace/<PLAN-X>]
  → git worktree add .helix/workspaces/<PLAN-X> <branch>
  → ADR-040 確定の .helix/ コピー戦略を適用
  → workspace.yaml に task_id / created_at / base_sha / status を記録

helix workspace list [--json]
  → .helix/workspaces/ 配下の workspace.yaml を走査
  → task_id / created_at / status / base_sha を表示

helix workspace merge --task <PLAN-X> [--strategy patch|rsync]
  → ADR-040 確定の merge 戦略で workspace の diff を main に適用
  → conflict 時は fail-safe (workspace 保持 + エラー出力)

helix workspace drop --task <PLAN-X> [--force]
  → 未 merge workspace には警告 (--force なし時は abort)
  → git worktree remove --force + workspace.yaml entry 削除
```

`drop` を `delete` ではなく選択する根拠: PLAN-156 本体は `delete` を使うが、
CLI 利用者への可逆性の印象から `drop` に統一する (ADR-040 で確認済の場合は PLAN-156 本体表記に合わせる)。

### workspace.yaml スキーマ

```yaml
task_id: PLAN-163
branch: workspace/PLAN-163
base_sha: "abc1234"
created_at: "2026-05-23T10:00:00Z"
status: active          # active | merged | dropped
merged_at: null
```

### cli/helix top-level router 登録

`cli/helix` に以下を追加する (PLAN-100 で確立した routing パターンに準拠):

```bash
workspace)
    exec "$HELIX_HOME/cli/helix-workspace" "$@"
    ;;
```

および `cli/helix help` の subcommand 一覧に `workspace` を追記する。

### patch 同期フロー (merge subcommand)

```
workspace cwd で git diff <base_sha>..HEAD > /tmp/helix-workspace-<task_id>.patch
main workspace cwd で git apply /tmp/helix-workspace-<task_id>.patch
成功: workspace.yaml status = merged, merged_at = <now>
失敗: patch file を .helix/workspaces/<task_id>/merge-conflict.patch に保存してエラー出力
```

## 実装計画

### Sprint .1: helix-workspace bash dispatcher + WorkspaceManager skeleton

**担当**: SE

**前提**: PLAN-156 Sprint .2 完了 (WorkspaceManager class の骨格が `cli/lib/workspace_manager.py` に存在)

**作業**:

1. `cli/helix-workspace` bash dispatcher の完全実装:
   - subcommand parse (`create` / `list` / `merge` / `drop`)
   - `--task` / `--branch` / `--strategy` / `--force` / `--json` flag のパース
   - 各 subcommand を `WorkspaceManager` Python メソッドへ委譲
   - `bash -n cli/helix-workspace` PASS 確認
2. `cli/helix` top-level router への `workspace` 登録 + help 追記
3. `python3 -m py_compile cli/lib/workspace_manager.py` PASS 確認

**受入条件**:

- `bash -n cli/helix-workspace` PASS
- `helix workspace --help` が subcommand 一覧を出力する
- `cli/helix` の router に `workspace` が存在する

### Sprint .2: WorkspaceManager 完全実装

**担当**: SE

**作業**:

1. `WorkspaceManager.create(task_id, branch)`:
   - `git worktree add .helix/workspaces/<task_id> <branch>` 実行
   - ADR-040 確定コピー戦略で `.helix/` を workspace に配置
   - `workspace.yaml` 生成
2. `WorkspaceManager.list(as_json=False)`:
   - `.helix/workspaces/` 配下の `workspace.yaml` を走査して一覧返却
3. `WorkspaceManager.merge(task_id, strategy)`:
   - diff → patch → apply フローの完全実装
   - conflict 時の fail-safe (merge-conflict.patch 保存)
4. `WorkspaceManager.drop(task_id, force=False)`:
   - 未 merge 警告ロジック
   - `git worktree remove --force` 実行
   - `workspace.yaml` entry 削除
5. `python3 -m py_compile cli/lib/workspace_manager.py` PASS 確認

**受入条件**:

- `helix workspace create --task PLAN-999` が実際に worktree を作成する (手動確認)
- `helix workspace list` が作成済み workspace を表示する
- `helix workspace drop --task PLAN-999` が worktree を削除する

### Sprint .3: docs 更新

**担当**: SE (または pmo-sonnet)

**作業**:

1. `docs/commands/index.md` に `helix workspace` コマンドを追記
2. 既存 `docs/commands/ai-harness.md` に workspace exec 連携の説明追記 (あれば)

**受入条件**:

- `docs/commands/index.md` に `workspace` subcommand の説明が存在する

### Sprint .4: テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | create が worktree ディレクトリを作成する | `.helix/workspaces/<task>` が存在 |
| T2 | create が workspace.yaml を生成する | task_id / base_sha / status=active が記録 |
| T3 | list が作成済み workspace を返す | task_id が含まれるリスト |
| T4 | drop が worktree を削除する | `.helix/workspaces/<task>` が消える |
| T5 | drop が未 merge workspace に警告を出す (--force なし) | exit 非 0 + エラーメッセージ |
| T6 | merge が patch を main に適用できる | workspace の変更が main に反映 |
| T7 | merge conflict 時に workspace が保持される | merge-conflict.patch が生成 |
| T8 | list --json が JSON を返す | valid JSON 出力 |

**受入条件**:

- `pytest cli/lib/tests/test_workspace_cli.py -v` T1〜T8 全件 PASS

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/workspace_manager.py` PASS
- [ ] `bash -n cli/helix-workspace` PASS
- [ ] `pytest cli/lib/tests/test_workspace_cli.py -v` 全件 PASS
- [ ] セルフレビュー (SE)
- [ ] pmo-sonnet review (Sprint .4 完了時)
- [ ] `cli/helix` router に workspace 登録確認
- [ ] commit message に `PLAN-163 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `helix workspace create / list / merge / drop` が動作する
- [ ] `python3 -m py_compile cli/lib/workspace_manager.py` PASS
- [ ] `bash -n cli/helix-workspace` PASS
- [ ] `pytest cli/lib/tests/test_workspace_cli.py -v` T1〜T8 全件 PASS
- [ ] `cli/helix` router に workspace subcommand 登録済
- [ ] `docs/commands/index.md` に workspace コマンド記載済
- [ ] pmo-sonnet G4 review 完了

## carry / 学び

- **PLAN-156 Sprint .2 依存**: Sprint .1 は PLAN-156 Sprint .2 完了後に着手する。
  WorkspaceManager skeleton が存在しないと本 PLAN の dispatcher 実装が宙に浮く
- **drop vs delete 表記統一**: CLI 利用者への一貫性のため、本 PLAN では `drop` で統一。
  PLAN-156 本体が `delete` を採用している場合は Sprint .1 着手前に Opus に確認する
- **patch strategy と rsync strategy の実装コスト差**: rsync strategy は rsync コマンドへの
  外部依存が生じる。環境依存を避けるため patch strategy を default とし、rsync は opt-in にする

## 関連 reference

- [[PLAN-156]] (parent PLAN、worktree isolation 全体設計・ADR-040)
- [[feedback_codex_parallel_dependency_check]] (Sprint .1/.2 並列化時の衝突判定根拠)
- ADR-040 (本 PLAN が参照する L2 凍結 snapshot)
- cli/helix (top-level router、workspace 登録先)
- cli/lib/workspace_manager.py (本 PLAN が完全実装するモジュール)
