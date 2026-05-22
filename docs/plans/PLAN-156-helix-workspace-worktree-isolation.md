---
plan_id: PLAN-156
title: helix workspace isolation (git worktree ベース per-task 書き込み可能 sandbox)
status: draft
kind: impl
drive: be
layer: L4
size: L
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-tech-fork
    slot_label: "OSS 探索 — git worktree 活用ツール + sandbox isolation パターン調査"
  - role: tl-advisor
    slot_label: "TL adversarial check — worktree 設計の妥当性 + .helix/ コピー戦略確認"
  - role: se
    slot_label: "SE — Sprint .1-.3 helix workspace CLI 実装 (create / merge / delete)"
  - role: qa
    slot_label: "QA — Sprint .4 integration test + Codex 委譲実行でのエンドツーエンド確認"
  - role: dba
    slot_label: "DBA — Sprint .2 .helix/helix.db の worktree 間 isolation 設計"
generates:
  - artifact_type: cli_extension
    path: cli/helix-workspace
  - artifact_type: python_module
    path: cli/lib/workspace_manager.py
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-040-helix-workspace-isolation.md
  - artifact_type: design_doc
    path: docs/v2/L4-test-design/PLAN-156-integration-test-design.md
  - artifact_type: test
    path: cli/lib/tests/test_workspace_manager.py
  - artifact_type: config
    path: cli/templates/workspace/workspace.yaml
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr:
  - ADR-040-helix-workspace-isolation
related_docs:
  - cli/helix
  - cli/lib/helix_db.py
  - docs/plans/PLAN-100-helix-v2-phase4-v2doc-overhaul.md
  - docs/plans/PLAN-099-helix-auto-drive-framework.md
  - docs/commands/index.md
acceptance_criteria:
  - "helix workspace create --task PLAN-X が git worktree + .helix/ コピーで workspace を作成できる"
  - "workspace 内で Codex se / pg が書き込み可能 (sqlite open 可) で実行できる"
  - "helix workspace merge が workspace の patch を main workspace に適用できる"
  - "helix workspace delete が worktree を clean に削除できる"
  - "helix workspace list が現在の workspace 一覧を表示できる"
  - "main workspace の .helix/helix.db に workspace からの書き込みが影響しない"
  - "python3 -m py_compile cli/lib/workspace_manager.py PASS"
  - "unit + integration test 全 PASS"
  - "ADR-040 が accepted 状態で存在する"
---

# PLAN-156: helix workspace isolation (git worktree ベース per-task 書き込み可能 sandbox)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-040** で凍結 (Sprint .2 で採用方針確定後に起票):

- git worktree 採用根拠 (Docker / tmpfs / chroot 等の代替との比較)
- .helix/ コピー戦略 (symlink vs deep copy vs empty init の選択)
- helix.db isolation 方針 (workspace 専用 db vs main db read-only mount)
- merge 戦略 (git diff patch apply vs rsync vs git merge)
- workspace cleanup の fail-safe 設計 (worktree 削除失敗時の回復手順)

## 背景

Codex 委譲が sandbox read-only で fail するケースが本 session で確認された:

```
sqlite3.OperationalError: attempt to write a readonly database
```

Codex 委譲は Claude Code sandbox の制約で `.helix/helix.db` への書き込みが
block される場合がある。これにより:

1. **Codex se / pg が write 必要なタスクで fail**: DB state を更新する sprint 実行、
   helix plan create 等のコマンドが sandbox read-only で動作しない
2. **workaround の複雑化**: `HELIX_CODEX_DB_READONLY=1` フラグ回避や
   mock DB 経由での委譲は実装コストが高く、根本解決にならない
3. **並列委譲の阻害**: 複数 Codex が同一 helix.db に書き込もうとすると
   lock 競合 (helix-db.lock) が発生する

git worktree を使った per-task workspace isolation で、各タスクが
独立した書き込み可能な playground を持つことでこれらを解消する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (git worktree ベース isolation) を含むため、
WebSearch 3 query 必須 (PLAN-087 ガード)。

実施予定 query (Sprint .1 前に pmo-tech-fork が実施):

1. `git worktree sandbox isolation CI 2026` — worktree を sandbox として使う事例
2. `helix workspace per-task sqlite isolation pattern` — SQLite isolation パターン
3. `git worktree .helix copy strategy side-by-side workspace` — .helix/ コピー戦略の実例

WebSearch 結果は ADR-040 §evidence に記録し、採用根拠とする。

## 設計方針

### workspace lifecycle

```
helix workspace create --task PLAN-X [--branch workspace/PLAN-X]
  → git worktree add .helix/workspaces/PLAN-X <branch>
  → .helix/ を workspace ディレクトリに deep copy (helix.db は空 init)
  → workspace.yaml に task_id / created_at / base_sha を記録

helix workspace list
  → .helix/workspaces/ の workspace.yaml 一覧を表示

helix workspace merge --task PLAN-X [--strategy patch|rsync]
  → workspace の変更差分を main workspace に適用
  → ADR-040 で確定した merge 戦略を使用

helix workspace delete --task PLAN-X
  → git worktree remove .helix/workspaces/PLAN-X --force
  → workspace.yaml の entry を削除
```

### .helix/ コピー戦略 (ADR-040 で確定)

候補:

- **A: deep copy** (推奨): `.helix/` を workspace に全コピー、helix.db は空 init
  - pros: 完全 isolation、phase.yaml 等の読み取りも可能
  - cons: .helix/ サイズ次第でコピーコスト
- **B: symlink**: 読み取り専用 file を symlink、db のみ workspace に配置
  - pros: コスト低
  - cons: symlink 先変更が workspace に影響するリスク
- **C: empty init**: workspace は新規 `.helix/` を `helix init --minimal` で作成
  - pros: 最軽量
  - cons: phase.yaml 等の状態が引き継がれない

Sprint .2 で tl-advisor + dba に確認して ADR-040 で凍結する。

### helix.db isolation

workspace の `.helix/helix.db` は main の helix.db から独立した空 db として初期化する。
main db の read が必要なコマンド (helix plan status 等) は workspace 内で動作させるか、
`--db` フラグで main db を read-only 参照させる設計を採用 (ADR-040 で確定)。

### Codex 委譲との統合

```bash
# Codex を workspace 内で実行する場合
helix workspace exec --task PLAN-X \
  "helix codex --role se --task '...' --approved"
```

`helix workspace exec` は worktree ディレクトリに cwd を切り替えてから
コマンドを実行する wrapper。Codex はその cwd の `.helix/helix.db` に書き込む。

## 実装計画

### Sprint .1: OSS 調査 + 設計確定 (pmo-tech-fork + Opus)

実施内容:

1. pmo-tech-fork が WebSearch 3 query を実施:
   - git worktree sandbox isolation 事例収集
   - SQLite per-process isolation パターン
   - side-by-side workspace の .helix/ コピー戦略事例
2. 調査結果を本 PLAN §WebSearch 履歴 に追記
3. tl-advisor 召喚で worktree ベース設計の adversarial check
4. ADR-040 起票 (採用根拠 + .helix/ コピー戦略 + merge 戦略 + cleanup fail-safe)

完了条件:

- WebSearch 3 query 完了 + ADR-040 accepted
- .helix/ コピー戦略が A/B/C から 1 つに確定

### Sprint .2: .helix/ isolation + helix.db 設計 (Codex dba + se)

実施内容 (並列 2 Codex):

- **Codex dba**: helix.db isolation 設計
  1. workspace db の schema 初期化方針 (migrate.py の workspace モード追加)
  2. main db read-only 参照が必要な command の特定と `--db` フラグ設計
  3. helix-db.lock の workspace 内 isolation 確認
- **Codex se**: workspace.yaml schema + `cli/lib/workspace_manager.py` skeleton
  1. `WorkspaceManager` class: create / list / delete の骨格
  2. `workspace.yaml` schema 設計 (task_id / branch / created_at / base_sha / status)
  3. `cli/helix-workspace` bash dispatcher の skeleton

衝突判定: dba は `cli/lib/helix_db.py` + `cli/lib/migrate.py`、
se は `cli/lib/workspace_manager.py` (新規) + `cli/helix-workspace` (新規)。
ファイル衝突なし → 並列 OK。

完了条件:

- `WorkspaceManager` class が create / list / delete を骨格実装
- workspace.yaml schema が確定
- helix.db isolation 方針が code comment で記録済

### Sprint .3: CLI 完全実装 (Codex se 委譲)

実施内容:

1. `helix workspace create` の完全実装:
   - `git worktree add` 実行
   - ADR-040 確定の .helix/ コピー戦略を実装
   - workspace.yaml 作成
2. `helix workspace merge` の実装:
   - ADR-040 確定の merge 戦略 (patch / rsync) を実装
   - conflict 検出時の fail-safe (workspace 保持 + エラー報告)
3. `helix workspace delete` の完全実装:
   - `git worktree remove --force` + workspace.yaml cleanup
   - 未 merge workspace に対する警告
4. `helix workspace list` の実装
5. `helix workspace exec` の実装 (cwd 切替 wrapper)
6. `cli/helix` top-level router に `workspace` subcommand 登録

完了条件:

- `python3 -m py_compile cli/lib/workspace_manager.py` PASS
- `bash -n cli/helix-workspace` PASS
- `helix workspace create --task PLAN-999` が実際に worktree を作成できる (手動確認)

### Sprint .4: test + E2E 確認 (Codex qa 委譲)

実施内容:

1. `docs/v2/L4-test-design/PLAN-156-integration-test-design.md` 新規作成 (V-model artifact ③)
2. `cli/lib/tests/test_workspace_manager.py` 新規作成 (V-model artifact ④) 10 case:
   - create が worktree を作成すること
   - create が workspace.yaml を生成すること
   - create した workspace の .helix/helix.db が main と独立していること
   - list が workspace 一覧を返すこと
   - delete が worktree を削除すること
   - delete が未 merge workspace に対して警告を出すこと
   - merge が patch を main に適用できること
   - merge conflict 時に fail-safe で workspace が保持されること
   - exec が worktree cwd でコマンドを実行すること
   - 並列 create が lock 競合なく完了すること
3. `pytest cli/lib/tests/test_workspace_manager.py -v` 全 PASS
4. Codex se を workspace exec 経由で実行し、helix.db 書き込みが成功することを確認

完了条件:

- unit test 10 case 全 PASS
- Codex exec での E2E 確認済

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/workspace_manager.py` PASS
- [ ] `bash -n cli/helix-workspace` PASS
- [ ] `pytest cli/lib/tests/test_workspace_manager.py -v` 全 PASS
- [ ] WebSearch 3 query 完了 + ADR-040 §evidence に記録済
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .4 完了時)
- [ ] ADR-040 accepted 状態で存在 (Sprint .1 完了時)
- [ ] V-model artifact ③ integration test design doc 起票済 (PLAN-156-integration-test-design.md)
- [ ] commit message に `PLAN-156 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `helix workspace create / list / merge / delete / exec` が動作する
- [ ] workspace 内 Codex 委譲で helix.db 書き込みが成功する
- [ ] main workspace の helix.db に workspace からの書き込みが影響しない
- [ ] `python3 -m py_compile` PASS
- [ ] unit + integration test 全 PASS (10 case)
- [ ] ADR-040 snapshot 起票済 (accepted)
- [ ] V-model artifact ③ test design doc (PLAN-156-integration-test-design.md) 存在
- [ ] `cli/helix` router に workspace subcommand 登録済
- [ ] docs/commands/index.md に workspace コマンド追記済

## carry / 学び (起票時記録)

- **L サイズの並列分割**: Sprint .2 の dba + se 並列が本 PLAN の key 並列ポイント。
  dba と se のファイル衝突を sprint 前に確認する (衝突なし確認済、§Sprint .2 参照)
- **git worktree の branch 運用**: `workspace/PLAN-X` branch を作るか、
  detached HEAD で worktree を作るかは ADR-040 で確定する。
  detached HEAD は merge 時の branch tracking が不要で簡潔だが、
  変更追跡が git log で難しくなるトレードオフがある
- **helix-db.lock の競合**: Sprint .4 の並列 create テストで
  lock 競合が発生する場合は、lock file を workspace 内に配置する設計変更が必要。
  Sprint .2 で dba が事前に検証する
- **Codex sandbox の制約確認**: Codex が worktree cwd で動作できるかは
  Claude Code sandbox の cwd 制約に依存する。Sprint .4 の E2E で
  実際に確認してから G4 通過判断を行う

## 関連 reference

- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否、本 PLAN は Sprint .1 で起票)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は 3 query 必須)
- [[feedback_codex_parallel_dependency_check]] (Sprint .2 並列衝突判定の根拠)
- ADR-040 (本 PLAN tree の L2 snapshot、Sprint .1 で起票)
- PLAN-099 (自動走行 framework、workspace exec との統合候補)
- PLAN-151 (gate fail-close 卒業 framework、workspace merge 後の gate 連動候補)
- cli/lib/helix_db.py (helix.db isolation 設計の参照先)
- cli/helix (top-level router、workspace subcommand 登録先)
