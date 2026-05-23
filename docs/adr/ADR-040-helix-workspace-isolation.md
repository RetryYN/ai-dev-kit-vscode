---
adr_id: ADR-040
title: helix workspace isolation (git worktree-based per-task sandbox + filtered materialized init)
status: Accepted with conditions
date: 2026-05-23
deciders:
  - PM (Opus)
  - TL-advisor (gpt-5.5 high、本 ADR adversarial check 実施、changes_required 判定)
related_plans:
  - parent: null
  - L2_snapshot_of: PLAN-156
supersedes: []
superseded_by: []
---

# ADR-040: helix workspace isolation (git worktree-based per-task sandbox)

## Status

**Accepted with conditions** — 2026-05-23

tl-advisor adversarial check (2026-05-23) で **P0 指摘 2 件・P1 指摘 4 件・P2 指摘 3 件・P3 指摘 3 件** を受領。**P0/P1 指摘は本 ADR の決定で反映済** (workspace 配置、コピー戦略 D、空 DB → snapshot json、MVP 縮小、drop fail-safe、Codex sandbox E2E 前倒し)。残 P2/P3 は本文末「Acceptance Conditions」section 参照、解消後に **Accepted** へ格上げする。

## Context

### 動機

HELIX (ai-dev-kit-vscode) は AI エージェント (Claude Code + Codex CLI) ベースの開発フレームワーク。複数の Codex 委譲が並列実行されると以下の問題が発生する:

1. **cwd 混乱事故**: Codex CLI が main workspace の cwd を直接編集 → 想定外 file が変更される事故が 2026-05-23 session 第 3 部までで複数回発生 ([[project_2026_05_23_session3_complete_handover.md]])
2. **`.helix/helix.db` 競合**: PLAN-104 で fix した helix-db.lock 5s timeout 問題は症状緩和だが、複数 Codex が同じ db に同時 write する設計自体が脆い
3. **branch 混在**: 複数 task が同じ branch (main) で並行作業すると stash 強要・rebase 必須・コンフリクト多発

### 既存 mitigation の限界

- **conftest fixture 経由 isolation** (PLAN-102 / PLAN-223): pytest test 内のみ有効、Codex 実行は別 process
- **helix-db.lock timeout** (PLAN-104 R-4): db lock 競合の症状緩和、原理的 isolation 不在
- **handover ESCALATION** (PLAN-067): エラー時の引継ぎ仕組、防止策ではない

### 業界動向 (WebSearch 3 query 結果、2026-05-23)

| query | findings |
|---|---|
| git worktree sandbox isolation CI parallel tasks 2026 | **2026 mid 標準**: 4-8 worktree/dev、Claude Code 組込済 (`--worktree` flag)、JetBrains 2026.1 / VS Code 2025.7 対応。worktree は **file isolation のみ** → ports/databases/caches は別途 isolation 必要 |
| SQLite per-process isolation pattern WAL mode 2026 | WAL mode で同時 reader + 単一 writer、cross-process Docker volume sharing 可能、**database-per-tenant pattern が標準** |
| git worktree side-by-side workspace copy strategy AI agent isolation | 標準 = 完全 isolated working dir + shared .git、pnpm + Git Worktrees 統合 pattern、**shared task document pattern** が agent 間 coordination 推奨 |

### 実測

```bash
$ du -sh .helix/
465M
$ du -sh .helix/*  | sort -h | tail -3
3.1M	.helix/cache
32M	.helix/tmp
422M	.helix/audit
```

`.helix/audit` 422MB + `.helix/tmp` 32MB が全体の **98%**。helix.db 自体は 2.6M。

## Decision

git worktree ベースの per-task workspace isolation を採用する。設計詳細は **tl-advisor adversarial check P0/P1 指摘を全て反映した修正版** で凍結する。

### D1: workspace 配置先 (tl-advisor P0-1 反映)

**廃案**: `.helix/workspaces/PLAN-X` (main runtime 領域配下、deep copy 時の再帰コピー事故リスク)

**採用**: `~/.helix/workspaces/<repo_name>/<task_id>/`

理由:
- repo 外配置で再帰コピー事故を防止 (`.helix/` 内に置くと自身を含めてコピーする事故が起きる)
- HOME 配下なので user 単位の isolation が自然
- `<repo_name>` で複数 HELIX repo の workspace を区別

実装メタデータ (`.helix/workspaces/<task_id>.yaml`) は main 配下に残す (registry only、deep copy 対象外):
```yaml
task_id: PLAN-X
workspace_path: /home/USER/.helix/workspaces/ai-dev-kit-vscode/PLAN-X
branch: workspace/PLAN-X
base_sha: <SHA>
created_at: 2026-05-23T15:00:00+09:00
status: active|merged|dropped
```

### D2: `.helix/` コピー戦略 = **D: filtered materialized init** (tl-advisor P0-2 反映)

**廃案**: A (deep copy) → 465MB の事故的コピーリスク、B (symlink) → 読み取り設定の実行中変更で再現性低下、C (empty init) → 必要 state 不在で UX 破綻

**採用 D: filtered materialized init**

create 時に以下を実行:
1. allowlist 対象を main `.helix/` から workspace `.helix/` に **copy**:
   - `config/` (HELIX 設定、project-local override)
   - `phase.yaml` (現在 phase 状態 snapshot)
   - `task-plan.yaml` (workspace WBS、当該 task に絞り込み可)
   - `templates/` (project template、ない場合は skip)
2. allowlist 対象を **snapshot json** 化 (`.helix/workspace_state_snapshot.json` として workspace 内に書き出し):
   - plan_registry の当該 task 関連 + parent + requires/blocks
   - handover の Next Action snapshot
   - memory feedback の関連 link
3. `helix.db` は **空 init** (`helix init --minimal` 相当、schema migration 全適用)
4. denylist は **絶対 skip**:
   - `tmp/`, `backups/`, `workspaces/`, `audit/runs/`, `*.db-wal`, `*.db-shm`, `logs/`, `cache/`
5. workspace 内 helix CLI は `.helix/helix.db` (空 init) + `workspace_state_snapshot.json` (read-only) を組み合わせて plan_status 等を返す

cost 試算: allowlist 数 MB 以内、create は 1-2 秒で完了見込み。

### D3: helix.db isolation 戦略 (tl-advisor P1-1 反映)

**廃案**: live main DB read-only 参照 (全 CLI コマンドに `--db` routing 実装が広がる、実装複雑度高)

**採用**: `workspace_state_snapshot.json` (D2 で生成) + workspace 内 `.helix/helix.db` (write 専用)

- `helix plan status` / `helix task list` 等は snapshot json から取得 (workspace 開始時点の state)
- workspace 内の新規 task / handover update / audit log は workspace `.helix/helix.db` に書く
- merge 時に workspace DB の delta を main DB に取り込む (将来 Sprint)
- snapshot が古くなる問題は workspace 短命 (task 単位、数時間〜数日) で許容

### D4: workspace merge 戦略 (tl-advisor P1-2 反映)

**MVP (PLAN-156 範囲)**: **標準 git flow** (workspace branch → PR / 通常 `git merge`) を正本にする。HELIX 独自の `helix workspace merge` は **MVP 範囲外**。

理由: rsync/patch ベース merge は dirty state / untracked / rename / binary / submodule / conflict の扱いが曖昧、git 標準で全て解決済。

**Phase 2 (将来 PLAN-163)**: `helix workspace merge` を `git diff --binary` preflight + patch apply convenience として実装。**main が dirty なら必ず abort**、未追跡ファイルを含める契約も明示。

### D5: API 命名統一 (tl-advisor P2-2 反映)

**`drop`** に統一 (破壊的操作の semantics 明示)。`delete` は使わない (alias も作らない、両方 doc 化する drift を防ぐ)。

```bash
helix workspace create --task PLAN-X [--branch workspace/PLAN-X] [--base main]
helix workspace list [--status active|merged|dropped]
helix workspace exec --task PLAN-X "<command>"
helix workspace preflight --task PLAN-X  # main dirty / orphan check
helix workspace drop --task PLAN-X [--force]
```

### D6: branch 作成契約 (tl-advisor P2-3 反映)

`--branch` 指定時は `git worktree add -b workspace/PLAN-X <path> <base>` を標準化:
- branch 不在時の auto 作成 を `-b` で明示
- `<base>` を引数化 (default は `main`)
- workspace.yaml に `base_sha` (作成時の base HEAD SHA) を必ず記録

### D7: drop fail-safe (tl-advisor P1-4 反映)

`drop` の default は **abort** (未 merge 変更があれば失敗)。

`--force` でも事前 **bundle + untracked tar** を `~/.helix/workspace-trash/<task>/<timestamp>/` に退避:
```bash
git -C <workspace> bundle create <trash>/changes.bundle --all
tar czf <trash>/untracked.tar.gz <未追跡ファイル一覧>
```

`git worktree prune` (orphan 残骸の cleanup) は **明示 subcommand**:
```bash
helix workspace prune --dry-run  # 確認
helix workspace prune  # 実行
```

### D8: Codex sandbox E2E 前倒し (tl-advisor P1-3 反映)

Sprint .1 / .2 の **kill criteria** に以下 E2E を前倒し追加:

```bash
# workspace 内で実行
pwd                             # → ~/.helix/workspaces/<repo>/<task>
git rev-parse --show-toplevel   # → 同上 (workspace root)
echo "sentinel" > workspace_test  # workspace 内に write 可能
ls /path/to/main_workspace/  # 別 path にある main は触れる (read 可)
echo "main_sentinel" > /path/to/main_workspace/test  # main に write **不可** が期待 (検証)
```

→ `main に write 可能` だった場合、git worktree isolation では Codex sandbox 問題を解決できない。その場合 container isolation 案 (Docker / podman) に差戻す。

### D9: MVP 縮小 (tl-advisor P2-1 反映)

**PLAN-156 MVP scope**: `create / list / exec / preflight / drop-safe` のみ。

**Phase 2 (別 PLAN)**:
- `helix workspace merge` (PLAN-163 で実装、standard git flow との棲み分け確定後)
- `--main-db-readonly` (D3 live DB 参照モード)
- port / venv / cache prefix 予約 (tl-advisor P3 残課題)

PLAN-156 Sprint 構成:
- Sprint .1: OSS 調査 + 本 ADR-040 起票 ← **本コミットで完了**
- Sprint .2: workspace_manager 実装 (create / list / drop-safe、DB snapshot 生成) ← MVP P0
- Sprint .3: CLI 完全実装 (exec / preflight、E2E E2E sentinel check 含む) ← MVP P1
- Sprint .4: test + Codex 委譲 integration test ← MVP 完了

## Consequences

### Positive

1. **Codex cwd 混乱事故の根本解決** (P0 効果): 各 Codex 委譲が独立 cwd で動作、main workspace を直接編集不可能
2. **並列 Codex 同時実行** (8 並列上限の活用): 各 task が独立 db / branch / cwd で動く → 真の並列実行
3. **業界 best practice 準拠**: Claude Code `--worktree` / JetBrains 2026.1 / pnpm worktree integration と方向性一致
4. **MVP 軽量化** (D9): Sprint .1-.2 で create/list/exec/preflight/drop-safe まで、merge は別 PLAN
5. **standard git flow 維持** (D4): workspace branch → PR で merge は標準 git、HELIX 独自仕様の表面積最小化

### Negative

1. **`~/.helix/workspaces/` 配下のディスク消費**: 各 workspace が allowlist のみ filtered copy でも HOME 領域を占有 → 自動 prune 機構 (D7) で対応
2. **workspace 内 state は snapshot 時点**: workspace 開始後の main 側 plan / handover 更新は workspace 内 helix CLI に反映されない (snapshot 静的)
3. **branch 管理コスト**: workspace ごとに branch が増える → `git worktree prune` 励行、drop 時 branch 削除も option
4. **Codex CLI の cwd respect 前提**: Codex CLI が起動後に cwd を勝手に main に戻す挙動なら無効化 → D8 E2E で検証必須、failure 時は container 案

### Risk

| risk | 影響 | 緩和策 |
|---|---|---|
| `.helix/audit` 等の denylist 漏れで再帰コピー事故 | workspace 作成 OOM / disk full | D2 で denylist 明示、create 時 dry-run option で件数 assert |
| Codex CLI が worktree cwd を respect しない | sandbox 問題 解決失敗 | D8 E2E sentinel check で early detection、container 案へ差戻し |
| workspace branch の orphan 残骸 | `.git/worktrees/` 累積 | D7 prune subcommand + drop 時 branch 削除 option |
| snapshot stale で plan status が古い | UX 低下 | workspace 短命前提 (数時間〜数日)、stale 検知 warn |
| main dirty 時の workspace create / merge | コンフリクト誘発 | D4 で main dirty 時 abort、D7 preflight で事前検出 |

## Alternatives Considered

### Alt-1: deep copy (元 PLAN-156 案 A)

却下理由: `.helix/` 465MB / 556 files の deep copy は事故的に重い。tmp / backups / audit / workspaces 自身を含めると create が 数 GB / 数十秒 になる。D2 で denylist + allowlist filter 必須 → これは案 D (filtered materialized init) と同等になる。

### Alt-2: symlink (元 PLAN-156 案 B)

却下理由: 読み取り設定の実行中変更が workspace に反映される → 再現性低下。tl-advisor P3 でも「採用するなら immutable snapshot 対象だけ」と限定推奨。D2 で snapshot json 採用すれば不要。

### Alt-3: empty init (元 PLAN-156 案 C)

却下理由: 必要 state (phase / task-plan / plan_registry) 不在で UX 破綻。`helix plan status` 空で Codex 「計画なし」誤認 (tl-advisor P1-1)。D2 で allowlist + snapshot 採用で解決。

### Alt-4: container isolation (Docker / podman)

```bash
docker run --rm -v $(pwd):/work:ro -v workspace:/work/.helix --workdir /work <image> <command>
```

却下理由: HELIX CLI / DB / agent harness のローカル統合コストが高い (image 構築 / GitHub Actions 連携 / Codex CLI の docker 化)。**ただし D8 E2E sentinel check が fail した場合の fallback として保持** (tl-advisor P3 推奨)。

### Alt-5: branch だけ切る (worktree なし)

却下理由: cwd が main と同じ → Codex cwd 混乱事故を防げない。stash / checkout 強要で並列実行不可。

## Acceptance Conditions (Accepted with conditions → Accepted 化までに必要)

tl-advisor adversarial check (2026-05-23) で受領した P2/P3 指摘を解消する条件 (P0/P1 は本 ADR で satisfy 済):

| # | 条件 | 対応 |
|---|---|---|
| AC-1 (P2) | API 命名 `drop` に統一、`delete` は doc 内も含めて使用禁止 | PLAN-156 Sprint .2 で実装、`delete` の grep が 0 件であること |
| AC-2 (P2) | `--branch` 指定時 `git worktree add -b` 標準化、`base_sha` が workspace.yaml に必ず記録 | PLAN-156 Sprint .2 実装で satisfy |
| AC-3 (P2) | MVP scope を Sprint .1-.2 に縮小 (`merge` は PLAN-163 以降に分離) | 本 ADR D9 で確定済、PLAN-156 doc 更新で satisfy |
| AC-4 (P3) | ports / venv / node_modules / cache / test DB 予約を workspace manifest に記録 | PLAN-156 Sprint .2 で `reserved_resources:` field を workspace.yaml に追加 |
| AC-5 (P3) | container isolation 案を ADR-041 で fallback 案として保持 (D8 E2E fail 時の代替) | D8 E2E 検証後、fail なら ADR-041 起票、PASS なら本 AC は無条件 satisfied |
| AC-6 (P3) | symlink 戦略 (Alt-2) は immutable snapshot 対象のみに限定して採用検討 | Phase 2 (PLAN-163 以降) で検討、本 PLAN-156 では完全採用見送り |

## Related Documents

- PLAN-156 (本 ADR の trigger PLAN、L4 実装計画)
- ADR-036 (zizmor、本 ADR の直前範例)
- skills/common/security/SKILL.md (workspace の security implication で参照)
- [[feedback_pytest_function_scoped_autouse_pattern]] (PLAN-223、conftest fixture isolation の先行 pattern)
- [[project_2026_05_23_session3_complete_handover.md]] (Codex sandbox 事故の motivation)

## References

- git worktree 公式: https://git-scm.com/docs/git-worktree
- Claude Code worktrees: https://code.claude.com/docs/en/worktrees
- Git Worktrees Need Runtime Isolation for Parallel AI Agent Development (Penligent): https://www.penligent.ai/hackinglabs/git-worktrees-need-runtime-isolation-for-parallel-ai-agent-development/
- Git Worktree Isolation Patterns for Parallel AI Agent Development (Zylos Research): https://zylos.ai/research/2026-02-22-git-worktree-parallel-ai-development
- SQLite Isolation: https://sqlite.org/isolation.html
- SQLite WAL Mode Across Docker Containers (Simon Willison): https://simonwillison.net/2026/Apr/7/sqlite-wal-docker-containers/
- pnpm + Git Worktrees: https://pnpm.io/next/git-worktrees
