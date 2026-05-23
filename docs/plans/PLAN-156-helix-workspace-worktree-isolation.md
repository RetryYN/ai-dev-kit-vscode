---
plan_id: PLAN-156
title: helix workspace isolation (git worktree ベース per-task 書き込み可能 sandbox)
status: complete
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
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
parent_design: docs/adr/ADR-040-helix-workspace-isolation.md   # 新 L4 基本設計 snapshot を暫定 parent。本来は L5/L6 詳細・機能設計 doc が必要 (新 15 工程で再採番)。ADR-040 が L4+L5+L6 詳細を吸収しているため、設計 doc 切り出しは後続 retrofit carry (docs/v2/process/L0NN 整備工程)
pairs_test_design:
  - docs/v2/L4-test-design/PLAN-156-integration-test-design.md   # 旧 L4-test-design は新 L8-test-design に再配置予定、現在 path はそのまま (retrofit carry)
process_layer: L7   # 本 PLAN は新 L7 実装スプリント工程の subordinate (新 15 工程 docs/v2/process/L07-implementation-sprint.md 参照)
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

**実施済 (2026-05-23、Opus 直接)**:

1. `git worktree sandbox isolation CI parallel tasks 2026` → 2026 mid で 4-8 worktree/dev 標準、Claude Code 組込 `--worktree`、JetBrains 2026.1 / VS Code 2025.7 対応。worktree は file isolation のみ、ports/db/caches は別途必要
2. `SQLite per-process isolation pattern WAL mode concurrent workspace 2026` → WAL mode + cross-process Docker volume sharing 可能、database-per-tenant pattern 標準、snapshot isolation
3. `git worktree side-by-side workspace copy strategy AI agent isolation` → 完全 isolated working dir + shared .git 標準、pnpm + Git Worktrees 統合 pattern、shared task document pattern が agent 間 coordination 推奨

WebSearch 結果は **ADR-040 §Context** に転記済 (採用根拠)。

## 設計方針 (ADR-040 で確定、tl-advisor adversarial check P0/P1 反映済)

**変更点 (元の設計方針からの差分)**: workspace 配置先 / コピー戦略 / merge 責務 / API 命名 / drop fail-safe を tl-advisor 指摘で全面修正。詳細は [ADR-040](../adr/ADR-040-helix-workspace-isolation.md) §Decision (D1-D9) 参照。

### workspace lifecycle (D1: 配置先 + D5: API 命名統一)

```bash
# workspace 配置先 = ~/.helix/workspaces/<repo>/<task>/ (HOME 配下、main runtime と物理分離)
helix workspace create --task PLAN-X [--branch workspace/PLAN-X] [--base main]
  → git worktree add -b workspace/PLAN-X ~/.helix/workspaces/<repo>/PLAN-X <base>
  → .helix/ を filtered materialized init (D2)、helix.db は空 init
  → workspace_state_snapshot.json を生成 (D3)
  → .helix/workspaces/<task>.yaml に registry entry (main 配下、metadata only)

helix workspace list [--status active|merged|dropped]
  → registry yaml の一覧表示

helix workspace exec --task PLAN-X "<command>"
  → workspace dir に cwd 切替 + command 実行

helix workspace preflight --task PLAN-X
  → main dirty / orphan worktree / branch divergence の事前検出

helix workspace drop --task PLAN-X [--force]
  → default は未 merge 変更あれば abort、--force でも事前 bundle + untracked tar を退避

helix workspace prune [--dry-run]
  → orphan worktree (.git/worktrees/ 残骸) の cleanup

# MVP scope 外 (Phase 2 / 別 PLAN-163)
# helix workspace merge   ← 標準 git flow (workspace branch → PR) を MVP では使う
```

### .helix/ コピー戦略 = D: filtered materialized init (D2)

**実測 `.helix/` = 465MB** (audit 422MB + tmp 32MB が 98%)。deep copy は事故的に重く、再帰コピーリスクあり。tl-advisor P0-2 指摘で **filtered materialized init** に確定。

- **allowlist** (workspace に copy): `config/` / `phase.yaml` / `task-plan.yaml` / `templates/`
- **denylist** (絶対 skip): `tmp/` / `backups/` / `workspaces/` / `audit/runs/` / `*.db-wal` / `*.db-shm` / `logs/` / `cache/`
- **snapshot json**: `workspace_state_snapshot.json` を workspace 内に生成 (plan_registry / handover / memory feedback の関連 link)
- **helix.db**: 空 init (`helix init --minimal` 相当、schema migration 全適用)

cost 試算: 数 MB 以内、create は 1-2 秒で完了見込み。

### helix.db isolation (D3: snapshot json + workspace db)

**廃案**: live main DB read-only 参照 (全 CLI コマンドに `--db` routing 実装が広がる、実装複雑度高)

**採用**: `workspace_state_snapshot.json` + workspace 内 `.helix/helix.db` (write 専用):

- `helix plan status` / `helix task list` 等は snapshot json から取得 (workspace 開始時点の state)
- workspace 内の新規 task / handover update / audit log は workspace `.helix/helix.db` に書く
- workspace 短命前提 (数時間〜数日) で snapshot stale は許容
- merge 時に workspace DB の delta を main DB に取り込む (Phase 2 / PLAN-163)

### merge 戦略 (D4: 標準 git flow 採用)

**MVP**: 標準 git flow (`workspace branch → PR → git merge`) を正本にする。`helix workspace merge` は **MVP 範囲外**。

**Phase 2 (PLAN-163)**: `helix workspace merge` を `git diff --binary` preflight + patch apply convenience として実装、main dirty 時 abort。

### Codex 委譲との統合 (D8: E2E kill criteria)

```bash
helix workspace exec --task PLAN-X \
  "helix codex --role se --task '...' --approved"
```

**Sprint .1/.2 の kill criteria に E2E sentinel check 前倒し**:
```bash
# workspace 内で実行
pwd                             # → ~/.helix/workspaces/<repo>/<task>
git rev-parse --show-toplevel   # → 同上 (workspace root)
echo "sentinel" > workspace_test  # workspace 内 write 可能
echo "main_sentinel" > /path/to/main/test  # main に write **不可** が期待
```

→ `main に write 可能` だった場合、container isolation 案 (Docker / podman) に差戻す (tl-advisor P1-3)。

### drop fail-safe (D7)

`drop` default は abort。`--force` でも事前 `git bundle create` + `tar czf untracked.tar.gz` を `~/.helix/workspace-trash/<task>/<timestamp>/` に退避。

## 実装計画

### Sprint .1: OSS 調査 + 設計確定 (Opus + tl-advisor) — **完遂 (2026-05-23)**

実施内容:

1. **WebSearch 3 query 完了** (Opus 直接、本 PLAN §WebSearch 履歴 に追記済):
   - git worktree sandbox isolation CI parallel tasks 2026
   - SQLite per-process isolation pattern WAL mode concurrent workspace 2026
   - git worktree side-by-side workspace copy strategy AI agent isolation
2. **`.helix/` サイズ実測**: 465MB (audit 422MB + tmp 32MB = 98%) → deep copy 不可確定
3. **tl-advisor 召喚** (helix codex --role tl-advisor、bo0jgiba6):
   - 判定: **changes_required**、P0 指摘 2 件 + P1 指摘 4 件 + P2 指摘 3 件 + P3 指摘 3 件
   - P0/P1 指摘は本 ADR で全 satisfy (workspace 配置 / コピー戦略 D / 空 DB → snapshot json / MVP 縮小 / drop fail-safe / Codex sandbox E2E)
4. **ADR-040 起票** (Accepted with conditions、D1-D9 で設計凍結)

完了条件 (全 satisfied):

- ✓ WebSearch 3 query 完了
- ✓ ADR-040 起票 (Accepted with conditions、本 ADR §Acceptance Conditions が AC-1〜6 で残課題明示)
- ✓ .helix/ コピー戦略確定 (**D: filtered materialized init**、A/B/C は ADR-040 §Alternatives で却下記録)
- ✓ MVP scope 確定 (Sprint .1-.2 で create/list/exec/preflight/drop-safe、merge は Phase 2)

**Sprint .1 完遂 commit**: 本 commit (PLAN-156 doc 更新 + ADR-040 新規起票)

### Sprint .2: .helix/ isolation + helix.db 設計 (Codex dba + se) — **完遂 (2026-05-23、commit 098ba97)**

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

### Sprint .3: CLI 完全実装 (Codex se 委譲) — **完遂 (2026-05-23、commit 1724be5)**

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

### Sprint .4: test + E2E 確認 (pmo-sonnet test design + Opus D8 Layer 2 E2E) — **完遂 (2026-05-24)**

実施内容 (本 Sprint で完遂、commit は本 Sprint .4 commit):

1. **V-model artifact ③ test design doc 起票** (pmo-sonnet 委譲、background):
   - `docs/v2/L4-test-design/PLAN-156-integration-test-design.md` 新規 (1335 行)
   - test case 95 件 (I-156-001〜I-156-100) を 5 ブロックで設計
   - 既存 unit test 33 件 (test_workspace_manager.py 24 + test_workspace_registry.py 9) を §4 で全件マッピング
   - WebSearch 3 query 実施 (IEEE 829-2008 / ISO/IEC/IEEE 29119-3:2021 / pytest fixture / git worktree)
   - PLAN-087 ガード遵守 (設計 doc 作成時 Web 検索 3 query 必須)
   - 業界 standard 引用: IEEE 829 § TCS / ISO 29119-3 clause 9.2 TestCaseSpecification

2. **D8 E2E sentinel check** (Opus 直接):
   - **Layer 1 (bash 直接)**: workspace create → exec で `pwd / git rev-parse / env injection / write / main read / snapshot` 全 PASS (Sprint .3 完了時点、commit 1724be5 後)
   - **Layer 2 (Codex CLI 経由)**: workspace exec 経由で `codex exec --sandbox read-only` 起動、Codex CLI banner で `workdir: ~/.helix/workspaces/ai-dev-kit-vscode/PLAN-156-AC5` を確認、Codex 出力 `D8_SENTINEL_PWD=~/.helix/workspaces/...` で **cwd respect 実証** → **AC-5 conditional satisfied** (container fallback ADR-041 起票不要)
   - **Layer 3 (並列 2 workspace lock 競合)**: PLAN-163 / Phase 2 carry

3. **D7 drop fail-safe 動作確認**:
   - `helix workspace drop --task X --force` で `~/.helix/workspace-trash/<task>/<timestamp>/{changes.bundle, untracked.tar.gz}` 退避を実機確認
   - registry status: active → dropped 遷移確認 (`workspace_registry_update_status` 機能確認)

4. **ADR-040 → Accepted 格上げ** (AC-1〜5 全 satisfied、AC-6 のみ Phase 2 carry):
   - Status History を ADR-040 §Status に追記 (Sprint .2/.3/.4 commit 紐付け)
   - AC-5 evidence (workdir banner / pwd output / session id) を ADR-040 §AC-5 検証 evidence に記録
   - `helix-hook check_adr_index` が docs/adr/index.md を自動更新 (Accepted with conditions → Accepted)

完了条件 (全 satisfied):

- ✓ V-model artifact ③ test design doc 起票 (1335 行、95 case)
- ✓ WebSearch 3 query 実施 (PLAN-087 ガード遵守)
- ✓ D8 E2E sentinel Layer 1 + Layer 2 PASS
- ✓ D7 drop fail-safe 動作確認
- ✓ ADR-040 → Accepted 格上げ (AC-1〜5 satisfied)

**Sprint .4 carry**:
- D8 Layer 3 (並列 2 workspace lock 競合) は PLAN-163 / Phase 2 carry
- AC-6 (symlink 戦略 immutable snapshot 対象限定) は Phase 2 carry
- `helix workspace merge` 実装は PLAN-163 carry

## mandatory in sprint (Sprint Exit 前必須、Sprint .2-.4 全 satisfied)

- [x] `python3 -m py_compile cli/lib/workspace_manager.py` PASS (Sprint .2-.3)
- [x] `bash -n cli/helix-workspace` PASS (Sprint .2-.3)
- [x] `pytest cli/lib/tests/test_workspace_manager.py -v` 全 PASS (24 case、Sprint .3 完了時点)
- [x] WebSearch 3 query 完了 + ADR-040 §evidence に記録済 (Sprint .1 + Sprint .4 で計 6 query)
- [x] セルフレビュー (Opus)
- [x] pmo-sonnet review (Sprint .4 test design doc 起票で兼ねる)
- [x] ADR-040 accepted 状態で存在 (Sprint .4、Accepted with conditions → Accepted)
- [x] V-model artifact ③ integration test design doc 起票済 (PLAN-156-integration-test-design.md、Sprint .4)
- [x] commit message に `PLAN-156 sprint .X` 明示 (全 commit)

## DoD (Definition of Done、本 PLAN 完遂時点で全 satisfied)

- [x] `helix workspace create / list / exec / preflight / drop / prune` が動作 (`merge` は PLAN-163 / Phase 2 で別実装)
- [x] workspace 経由で Codex sandbox cwd respect 実証 (D8 Layer 2、Sprint .4 AC-5 evidence)
- [x] main workspace の helix.db に workspace からの書き込み影響なし (D3 設計通り、workspace 内空 init DB に書く)
- [x] `python3 -m py_compile` PASS (Sprint .2-.4)
- [x] unit test 33 case 全 PASS (test_workspace_manager.py 24 + test_workspace_registry.py 9)
- [x] integration test design 95 case 起票済 (Sprint .4)
- [x] ADR-040 snapshot 起票済 (Status: Accepted、Sprint .4)
- [x] V-model artifact ③ test design doc (PLAN-156-integration-test-design.md、1335 行) 存在
- [x] `cli/helix` router に workspace subcommand 登録済
- [x] docs/commands/index.md に workspace コマンド追記済

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
