---
plan_id: L7-cli-helix-retrofit-implplan
title: "L7-cli-helix-retrofit-implplan: helix-retrofit CLI 実装 — Retrofit mode (依存・基盤の段階改修・移行) 起動コマンド (v1 設計版)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/retrofit-workflow.md
parent_design_addenda:
  - docs/adr/ADR-041-drift-type-7-categories-routing-decision.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
  - docs/adr/ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md
pairs_test_design:
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - HELIX-workflows/helix-process/deviation-plan-map.md
is_reference: false
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check (CLI 設計・retrofit-matrix schema・refactor との責務境界・L4/L5 追補連携・回帰テスト連携)"
  - role: se
    slot_label: "SE — cli/helix-retrofit + cli/lib/retrofit_engine.py 実装 + test 拡張"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace review・整合チェック"
generates:
  - artifact_path: cli/helix-retrofit
    artifact_type: cli_extension
  - artifact_path: cli/lib/retrofit_engine.py
    artifact_type: python_module
  - artifact_path: docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/tests/test_retrofit_engine.py
    artifact_type: test
  - artifact_path: cli/lib/tests/bats/helix_retrofit.bats
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/deviation-plan-map.md
  - HELIX-workflows/helix-process/refactor-workflow.md
  - cli/helix
  - cli/lib/helix_db.py
  - cli/helix-recover
  - cli/helix-route
  - docs/commands/index.md
  - docs/plans/L7/L7-helix-recover-implplan.md
  - docs/plans/L7/L7-helix-route-implplan.md
  - docs/adr/ADR-041-drift-type-7-categories-routing-decision.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
  - docs/adr/ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/retrofit-workflow.md](../../../HELIX-workflows/helix-process/retrofit-workflow.md)
> **本 PLAN の対象**: `cli/helix-retrofit` コマンドの新規実装。依存・フレームワーク・基盤を **要件を変えずに段階的に移行** するための CLI エントリーポイントを実体化する。
> **位置づけ**: CLAUDE.md / HELIX_CORE.md で「dedicated CLI 未整備、PLAN kind + retrofit-matrix + config で運用」と carry 明示された案件を本 PLAN で実体化する。retrofit-workflow.md (status: accepted, 2026-05-24) が正本設計。
>
> **[scope 縮小 — tl-advisor R1 反映]**: 本 PLAN は **retrofit CLI 単体 state manager (direct invocation 想定)** に scope を限定する。route_engine 拡張 (drift_type 分岐 / Retrofit mode routing / `helix route suggest` 連携) は **別 PLAN `L7-route-engine-drift-type-retrofit-extplan` (C') に移管済み**。本 PLAN は self-contained (C' への hard dependency なし)。route 連携の有効化は C' 完遂後の carry として §11 C8 に記録する。

### parent_design (accepted) を採用する理由

`retrofit-workflow.md` の frontmatter は `status: accepted` で 2026-05-24 に確定。設計は凍結済みとして扱い、本 PLAN は L7 実装に専念する。**SE 実装時は親設計 (retrofit-workflow.md) を変更しない**。

### kind: impl と generates の根拠 (deviation-plan-map.md との対応)

`deviation-plan-map.md` の Retrofit 行は `kind=retrofit` / `generates=retrofit-matrix+config` として定義されている。これは **Retrofit mode で作業する際に起票される PLAN** (運用 PLAN) の仕様であり、本 PLAN とは異なる。

本 PLAN は Retrofit CLI 自体を実装する **Forward impl 案件** であるため:
- `kind: impl` (CLI 実装 = Forward スプリント)
- `generates`: `cli/helix-retrofit` + `cli/lib/retrofit_engine.py` (CLI 成果物)
- `helix retrofit init` コマンドが実行時に `retrofit-matrix.md` を動的生成するため、deviation-plan-map の `retrofit-matrix` は **実行時生成物** として本 PLAN の間接的 generates となる

### integration-map §結論 carry との接続

本 PLAN は `integration-map.md §結論 #2` (CLI 未整備モード実体化) + `§テンプレートの穴` (retrofit-matrix テンプレート不在) carry を解消する実装である。Sprint .2 の `init` サブコマンド実装により `integration-map §テンプレートの穴` を直接解消し、完了後に `integration-map.md` 側の carry 欄を update する (§11 C5)。

### retrofit と refactor の意味的境界 (本 PLAN 全体の前提)

| 観点 | Refactor | Retrofit |
|---|---|---|
| 目的 | コード内部の構造改善 (振る舞い不変) | 依存・基盤・構成の移行 (環境を変える) |
| 成果物 | コード差分 | retrofit-matrix + config |
| 典型例 | 関数分割・命名整理・パターン統一 | Python 3.9 → 3.12 移行・SQLite → PostgreSQL 移行・フレームワーク更新 |
| PLAN kind | refactor | **retrofit** |
| L1/L3 戻り | 不要 (振る舞い変えない) | 要件変更時のみ戻る |
| 回帰テスト | 既存テストが保護網 (変化なし) | L8/L9 回帰テストで移行後の整合確認 |

> **判定シグナル**: `helix route suggest` が `drift_type=dependency_outdated` / `upgrade` / `config_drift` を返す場合は Retrofit。`drift_type=structural` / `code_smell` を返す場合は Refactor。本 PLAN の CLI surface は **5 subcommand (init / matrix / status / done / plan) に固定**する。drift_type 判定補助は route_engine (C') が担当する。

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査 (retrofit-workflow.md / integration-map.md / deviation-plan-map.md / cli/helix router 確認) | PM | ✅ done |
| 2 | CLI サブコマンド設計 (subcommand 構成 / retrofit-matrix schema / PLAN kind=retrofit 連携) | PM | ✅ done (§2.A) |
| 3 | retrofit_engine.py 設計 (matrix YAML 管理 / phase 追補連携 / config 管理) | PM | ✅ done (§2.B) |
| 4 | 責務分離設計 (helix-recover / helix-route / helix-refactor との境界明示) | PM | ✅ done (§4) |
| 5 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 6 | TL 第 1 ラウンド指摘反映 | PM | □ pending |
| 7 | tl-advisor adversarial check 第 2 ラウンド (必要な場合) | PM → TL | □ pending |
| 8 | SE 委譲: cli/helix-retrofit + cli/lib/retrofit_engine.py 実装 | PM → SE | □ pending |
| 9 | bash -n / shellcheck / python3 -m py_compile 確認 | SE | □ pending |
| 10 | pytest test_retrofit_engine.py + bats helix_retrofit.bats 全 PASS | SE | □ pending |
| 11 | cli/helix router 登録 + docs/commands/index.md 追記 + `helix commands check` 確認 | SE | □ pending |
| 12 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 13 | commit + push | PM | □ pending |

---

## §2 実装計画

### §2.A cli/helix-retrofit CLI 設計

#### サブコマンド構成 (正式 CLI surface — 5 本、tl-advisor R1 P1-3 反映)

```
helix retrofit [subcommand] [options]

subcommand:
  init     retrofit-matrix.md と config YAML を生成し、PLAN kind=retrofit を draft 起票
  matrix   retrofit-matrix.md の表示・更新 (row の追加・status 変更・一覧)
  status   現在の retrofit PLAN 進捗と matrix 完了率を表示
  done     指定 matrix 行 (--row R001) を completed にマーク。--run-regression で回帰実行
  plan     PLAN kind=retrofit の draft 起票 (既存 PLAN に紐付ける場合は --plan-id 指定)
           Usage: helix retrofit plan [--slug <name>]
           責務: kind=retrofit の PLAN draft を retrofit-workflow.md template から生成
           exit code: 0=success / 1=template 不在 / 2=duplicate plan_id
           init との差分:
             init は retrofit-matrix.md (row 操作) + config YAML を生成する matrix 管理コマンド
             plan は docs/plans/L7/L7-<slug>plan.md (workflow 計画文書) を生成する PLAN 起票コマンド
           generates: docs/plans/L7/L7-<slug>plan.md
             frontmatter: kind=retrofit / drift_type (CLI 引数から取得) / process_layer=L7

削除 subcommand:
  config     (init が生成、show は status で代替可能、独立 subcommand 不要)
  check-kind (route 連携 C' 移管のため削除。KindChecker ロジック自体は内部ユーティリティとして残存)
```

> **注**: `helix route suggest` 連携 / `--no-plan` フラグ / `check-kind` の exit-code ブリッジは **C' PLAN (`L7-route-engine-drift-type-retrofit-extplan`)** で実装する。

#### サブコマンド詳細仕様

**`helix retrofit init --slug <slug> [--plan-id PLAN-NNN]`**

```
入力:
  --slug:    retrofit 識別子 (例: python312-migration、sqlite-to-postgres)
             形式強制: kebab-case 正規表現 ^[a-z0-9][a-z0-9-]*[a-z0-9]$ 違反は exit 2
  --plan-id: 既存 PLAN に紐付ける場合の ID (省略時は新規 PLAN draft を生成)
  --drive:   be (default) / fullstack / db

出力:
  docs/plans/<slug>-retrofit-matrix.md     (retrofit-matrix テンプレート生成)
  cli/config/<slug>-retrofit.yaml          (config テンプレート生成)
  docs/plans/L7/L7-<slug>-retrofitplan.md (PLAN draft、--plan-id 省略時)

  PLAN draft frontmatter 例:
    kind: retrofit
    process_layer: L7
    parent_design: HELIX-workflows/helix-process/retrofit-workflow.md
    generates: [<slug>-retrofit-matrix.md, <slug>-retrofit.yaml]
    pairs_test_design: [docs/v2/L7-test-design/...]

  ※ upgrade kind の row を含む場合、Reverse upgrade (R0-R4) の完遂 evidence が要求される
     (evidence 不在 = row status を blocked で作成し警告表示)

exit-code:
  0: 成功
  1: slug 重複 (既存 matrix あり、--force で上書き)
  2: 設定エラー (slug 形式違反 / drive 不正)
```

**`helix retrofit matrix [list|add|update|show] [options]`**

> **[P1-4 反映]** YAML frontmatter `rows` が **唯一の正本 (Single Source of Truth)**。Markdown table は `rows` から自動生成されるビューであり直接編集禁止。
> table 先頭行に `<!-- DO NOT EDIT TABLE — regenerated from frontmatter rows -->` を自動挿入する。
> `helix retrofit status` が matrix table と frontmatter `rows` の不整合を検出した場合は警告を表示する。

```
helix retrofit matrix list --slug <slug>
  → retrofit-matrix の全行を表形式で表示 (status 色分け: todo/in_progress/done/blocked)

helix retrofit matrix add --slug <slug> --from "<旧>" --to "<新>" --scope "<影響範囲>" [--phase L4]
  → matrix に新行を追加 (phase は L4/L5/L7 追補先)
  → ID は R001 から始まる連番を自動採番 (frontmatter rows に追記 → table 再生成)

helix retrofit matrix update --slug <slug> --row R001 --status <todo|in_progress|done|blocked>
  → 指定行 (R001 形式 ID) の status を更新 (done 時は done-at タイムスタンプを付与)
  → frontmatter rows を更新 → Markdown table を再生成

helix retrofit matrix show --slug <slug> --summary
  → matrix 完了率 (done/total) + blocked 件数 + pending 件数を表示

exit-code: 0 成功 / 1 slug 不在 / 2 row ID 不在
```

**`helix retrofit status [--slug <slug>] [--json]`**

```
入力: --slug (省略時は全 slug)
出力例:
  [retrofit] slug: python312-migration
    plan: L7-python312-migration-retrofitplan (draft)
    matrix: 4/12 done (33%), 2 blocked, 6 pending
    config: cli/config/python312-migration-retrofit.yaml (exists)
    next: R005 (logging → structlog) [in_progress]
    [WARNING] 2 blocked rows — review L1/L3 re-entry conditions before proceeding

--json 出力フィールド (P2-2 反映):
  slug, plan_id, plan_status, done, total, completion_pct,
  blocked_count, pending_count, next_row_id, next_row_desc,
  config_exists, regression_phases, has_missing_evidence (bool)

exit-code: 0 (slug 不在でも 0、"no active retrofit" メッセージ)
```

**`helix retrofit done --slug <slug> --row R001 [--run-regression]`**

> **[P1-5 反映]** row 指定は `R001` 形式 ID 必須 (整数 index 廃止)。
> **[P1-8 反映]** blocked 行がある場合は `done` を禁止 (exit 2 で fail-close)。
> **[P1-10 反映]** `--run-regression` 失敗時は row を `in_progress` に巻き戻す。

```
入力: --slug + --row R001 形式 ID
動作:
  0. 前提チェック: blocked 行が存在する場合は exit 2 で禁止
     ("blocked rows exist — resolve before marking done")
  1. matrix 行を status=done, done-at=<timestamp> に更新 (frontmatter rows → table 再生成)
  2. --run-regression 付きの場合:
     - config の phases.regression に指定された回帰テストを同期実行
       (初期実装では同期のみ。非同期は別 PLAN 対応)
     - 成功: done 状態を確定
     - 失敗: row を status=in_progress に巻き戻し、regression_failed=true を row に記録
             exit code 3 で失敗内容を表示
  3. 全行 done の場合: retrofit 完了メッセージ + PLAN status=complete 更新促進

L1/L3 再入条件:
  - blocked 理由が「要件変更の可能性」の場合は L1/L3 再確認を促すメッセージを表示
  - 未解消 blocked > 0 の場合、done は完全禁止

exit-code:
  0: 成功
  1: slug / row ID 不在
  2: blocked 行あり (fail-close)
  3: --run-regression 失敗 (row 巻き戻し済)
```

#### 入力源と凍結設計

| サブコマンド | 主入力源 | 凍結理由 |
|---|---|---|
| `init` | CLI 引数 (--slug, --plan-id) | ユーザー明示指定 |
| `matrix list/show` | `docs/plans/<slug>-retrofit-matrix.md` (YAML frontmatter `rows` が正本) | Single SoT — table はビュー生成、直接編集禁止 |
| `status` | matrix.md frontmatter `rows` + PLAN frontmatter `status` | helix.db 不依存で軽量 |
| `done` | matrix.md row update (R001 ID) + phases.regression config | 機械 + 人間の両確認、回帰失敗で巻き戻し |
| `plan` | CLI 引数 + retrofit-workflow.md template | PLAN draft 生成のみ、state 変更なし |

---

### §2.B retrofit_engine.py 設計

#### モジュール構成

```python
# cli/lib/retrofit_engine.py

class RetrofitMatrix:
    """retrofit-matrix.md の YAML frontmatter rows が正本、Markdown table はビュー"""
    def load(slug: str) -> RetrofitMatrix
    def add_row(from_: str, to: str, scope: str, phase: str = "L7") -> None
    def update_row(row_id: str, status: str, regression_failed: bool = False) -> None
    # row_id は "R001" 形式 (整数 index 廃止、P1-5 反映)
    # status=done 時に done_at タイムスタンプを自動付与
    # status 変更後に Markdown table を frontmatter rows から再生成 (P1-4 反映)
    def summary() -> dict  # {total, done, in_progress, blocked, pending, completion_pct}
    def has_blocked() -> bool  # done 前チェック用 (P1-8 反映)
    def save() -> None

class RetrofitConfig:
    """cli/config/<slug>-retrofit.yaml を管理"""
    def load(slug: str) -> RetrofitConfig
    def save_template(slug: str, drive: str) -> Path
    def regression_command() -> list[str]  # phases.regression から回帰テストコマンド生成 (P1-6)

class KindChecker:
    """変更ファイル + signal から retrofit/refactor/forward を判定 (内部ユーティリティ)
    
    [P1-9 反映] 判定優先順:
      1. signal 最優先: dependency_outdated/upgrade/config_drift → retrofit
                        structural/code_smell/naming → refactor
                        (signal 指定時はファイルパターン判定を行わない)
      2. signal なし時のみ file pattern 補助:
         requirements*.txt / pyproject.toml / Dockerfile / docker-compose → retrofit
         import のみ変更 (振る舞い変化なし) → refactor
         新機能 / 新 API / スキーマ追加 → forward
      3. schema / contract 変更 → Reverse normalization 推奨 (exit 3)
      4. 混在 → 分割推奨 (exit 3)
      ※ *.yaml 一律 retrofit / import 一律 refactor は廃止
    """
    RETROFIT_SIGNALS  = ["dependency_outdated", "upgrade", "config_drift"]
    REFACTOR_SIGNALS  = ["structural", "code_smell", "naming"]
    REVERSE_SIGNALS   = ["schema", "contract"]
    def check(files: list[str], signal: str = "") -> tuple[str, str]
    # returns (kind, reason) — kind: retrofit/refactor/forward/reverse/mixed

def init_retrofit(slug: str, plan_id: str | None, drive: str) -> dict:
    """init subcommand の実装本体"""

def get_retrofit_status(slug: str | None, as_json: bool) -> dict:
    """status subcommand の実装本体"""

def run_regression(config: RetrofitConfig) -> bool:
    """phases.regression の回帰テスト同期実行 (P1-10)
    失敗時は False を返す (呼び出し元が row を in_progress に巻き戻す)"""
```

#### retrofit-matrix.md ファイル形式 (§3 参照)

retrofit_engine.py は matrix.md の YAML front matter を Python dict として読み書きし、
Markdown table は front matter の `rows` リストから自動生成する。

---

## §3 retrofit-matrix data 形式

### 設計判断: YAML front matter + Markdown table (混在形式)

**採用**: `docs/plans/<slug>-retrofit-matrix.md` に YAML front matter + Markdown table を共存させる。

**理由**:
1. retrofit-workflow.md は「retrofit-matrix を docs/plans/ 配下の .md として生成」と明示
2. HELIX の他 PLAN/doc 群と形式を統一 (YAML front matter が HELIX 標準)
3. Markdown table は人間が直接閲覧・編集可能 (git blame / PR review で差分が読める)
4. helix.db に追加 table を新設せず、ファイルが source of truth となる (状態管理の二層構造 = 宣言的状態は YAML ファイル)

**却下**: SQLite table への格納
- helix.db schema 変更 (migration 追加) のコストが高い
- matrix は人間が確認・編集する成果物であり、DB は閲覧性が低い
- 宣言的状態は phase.yaml / PLAN.md (ファイル) が正本という HELIX 設計原則と矛盾

### retrofit-matrix.md テンプレート

> **[P1-4 反映]** YAML frontmatter `rows` が **唯一の正本 (Single Source of Truth)**。
> Markdown table は `rows` から自動生成されるビューであり、直接編集禁止。
> `<!-- DO NOT EDIT TABLE — regenerated from frontmatter rows -->` を table 直前行に自動挿入する。

```markdown
---
slug: python312-migration
plan_id: L7-python312-migration-retrofitplan
drive: be
created: 2026-05-24
updated: 2026-05-24
rows:
  - id: R001
    from: "Python 3.9"
    to: "Python 3.12"
    scope: "全 .py ファイル"
    phase: L7
    status: todo
    done_at: null
    regression_failed: false
    notes: ""
  - id: R002
    from: "datetime.utcnow()"
    to: "datetime.now(timezone.utc)"
    scope: "cli/lib/*.py"
    phase: L7
    status: done
    done_at: "2026-05-24T10:30:00"
    regression_failed: false
    notes: "DeprecationWarning 対応 (Python 3.13+ removal)"
---

# Retrofit Matrix: python312-migration

<!-- DO NOT EDIT TABLE — regenerated from frontmatter rows -->
| ID | From | To | Scope | Phase | Status | Done At |
|---|---|---|---|---|---|---|
| R001 | Python 3.9 | Python 3.12 | 全 .py ファイル | L7 | todo | - |
| R002 | datetime.utcnow() | datetime.now(timezone.utc) | cli/lib/*.py | L7 | done | 2026-05-24 |
```

### config YAML テンプレート (`cli/config/<slug>-retrofit.yaml`)

> **[P1-6 反映]** `phases.regression` を正本フィールドとして統一。`regression.phases` 形式は廃止。
> `done --run-regression` は `phases.regression` の値でテストを実行する。
> 実行コマンドは Sprint .1 で `helix test --help` 確認後に正式 option を固定する
> (暫定: `helix test --layer L8 --regression` または `helix test L8`)。

```yaml
# cli/config/python312-migration-retrofit.yaml
slug: python312-migration
drive: be
phases:
  design_supplement: [L4, L5]   # 追補する設計工程
  regression: [L8, L9]           # 回帰テスト工程 (phases.regression が正本、P1-6)
rollback:
  strategy: git-revert            # git-revert / branch-cutover / feature-flag
  checkpoint: HEAD~3              # ロールバック起点 (手動更新)
parallel_run:
  enabled: false                  # 並行稼働フラグ (旧環境を残す場合 true)
  old_config: null
regression_scope:
  bats: "cli/lib/tests/bats/"
  pytest: "cli/lib/tests/"
  filter: ""                      # 追加フィルタ (例: "-k retrofit")
```

---

## §4 既存 CLI 責務分離

### CLI 責務境界マップ

| CLI | 責務 | 入口判定シグナル |
|---|---|---|
| `helix route` | 検出シグナル → モード (Reverse / Refactor / Recovery / Retrofit / Incident / Forward) の**提案** | 全 drift_type を受け付け、最適 mode を提案して次コマンドへ誘導 |
| `helix recover` | Recovery mode 確定後の**実行・状態保存・再開支援** (AI 暴走ガード) | route が `recovery` を返した後 |
| `helix retrofit` | Retrofit mode 確定後の**matrix 管理・config 管理・進捗追跡** | route が `retrofit` を返した後、または直接 retrofit と確定している場合 |
| `helix refactor` (未実装) | Refactor mode の**実行補助** (振る舞い不変の構造改善) | route が `refactor` を返した後 |

### helix retrofit direct invocation フロー (本 PLAN scope)

```
ユーザー: 依存更新・基盤移行を確定 (モード判断済み)
  ↓
helix retrofit init --slug python312-migration
  → retrofit-matrix.md + config.yaml + PLAN draft を生成
  ↓
helix retrofit matrix add ... (移行項目を追記)
  ↓
[実装: Codex SE または helix codex --role se]
  ↓
helix retrofit done --slug python312-migration --row R001 [--run-regression]
  ↓
helix retrofit status  (完了率確認)
```

### helix route との境界プロトコル (scope 限定)

- `helix route` は **モードの提案のみ** を返し、state 変更をしない (read-only に近い)
- `helix retrofit` は **state を持つ** (matrix.md / config.yaml を生成・更新する)
- `helix route suggest` の出力に `recommended_command` フィールドを追加し retrofit へ誘導するフローは **C' PLAN (`L7-route-engine-drift-type-retrofit-extplan`) scope**。本 PLAN では実装しない。
- C' 完遂後に本 PLAN の route 連携を有効化する (§11 carry C8)。

### helix recover との責務境界

| 観点 | helix recover | helix retrofit |
|---|---|---|
| 発火条件 | AI エージェントの暴走・独断専行を検出 (C1-C4 条件) | 依存・基盤の移行が必要と判断 |
| matrix | recovery-log.md (7 必須セクション、recovery_plan_check.py 準拠) | retrofit-matrix.md (from/to/scope/phase/status) |
| rollback | dry-run 表示のみ (実適用は別 PLAN) | rollback strategy は config に宣言、実適用は手動 |
| 状態保存先 | helix.db + .helix/handover/ | docs/plans/<slug>-retrofit-matrix.md (ファイル) |

---

## §5 Sprint 分割

### Sprint .1: 設計確定 + matrix/config schema 確定

**目標**: SE 委譲前に完全な設計仕様を確定し、tl-advisor R1 を通過する

**作業**:
1. 本 PLAN §2-§4 の確定 (tl-advisor R1 フィードバック反映)
2. `docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md` の起草
   - subcommand I/O 仕様 (exit-code / stdout format)
   - retrofit_engine.py クラス設計 (メソッドシグネチャ + 型)
   - retrofit-matrix.md schema (YAML front matter 定義)
   - config YAML schema (フィールド定義)
3. `docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md` の起草
   - 単体テスト一覧 (U-001〜U-030 目安)
   - bats テスト一覧 (B-001〜B-020 目安)
4. tl-advisor R1 実施

**完了条件**: tl-advisor R1 passed / passed_with_minor_changes

### Sprint .2: CLI + engine 実装

**目標**: cli/helix-retrofit + cli/lib/retrofit_engine.py の実装完了

**委譲先**: `helix codex --role se --task "..."`

**作業** (SE 担当):
1. `cli/helix-retrofit` (bash shim、9 行以内):
   ```bash
   #!/bin/bash
   set -euo pipefail
   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
   source "$SCRIPT_DIR/lib/helix-common.sh"
   exec env PYTHONPATH="$HELIX_HOME${PYTHONPATH:+:$PYTHONPATH}" python3 -m cli.lib.retrofit_engine "$@"
   ```
2. `cli/lib/retrofit_engine.py`:
   - `RetrofitMatrix` クラス (load / add_row / update_row / summary / save)
   - `RetrofitConfig` クラス (load / show_diff / save_template)
   - `KindChecker` クラス (check メソッド)
   - subcommand ディスパッチ (argparse)
   - `init_retrofit()` / `get_retrofit_status()` 関数
3. bash -n + shellcheck + python3 -m py_compile 確認

**完了条件**:
- `bash -n cli/helix-retrofit` PASS
- `shellcheck cli/helix-retrofit` PASS (warn 以上 0)
- `python3 -m py_compile cli/lib/retrofit_engine.py` PASS

### Sprint .3: テスト実装

**目標**: pytest + bats の全テスト PASS

**委譲先**: SE (Sprint .2 継続) または 独立 SE

**作業**:
1. `cli/lib/tests/test_retrofit_engine.py`:
   - `RetrofitMatrix.load()` 正常系 + schema validation
   - `RetrofitMatrix.add_row()` 追記 + save 往復テスト
   - `RetrofitMatrix.update_row()` status 変更 + done_at 付与
   - `RetrofitMatrix.summary()` 各カウント正確性
   - `RetrofitConfig.save_template()` ファイル生成 + 必須キー検証
   - `KindChecker.check()` signal 優先 / file pattern 補助の各シグナル (内部 unit)
   - `init_retrofit()` matrix + config + PLAN 生成の 3 点セット確認
   - `run_regression()` 成功時の done 確定 / 失敗時の in_progress 巻き戻し
   - エラー系: slug 重複 / row ID 不在 / slug 不在 / blocked 行での done 禁止
2. `cli/lib/tests/bats/helix_retrofit.bats`:
   - `helix retrofit init` 出力確認 (matrix + config + PLAN 3 点生成)
   - `helix retrofit matrix list` 表形式出力確認
   - `helix retrofit matrix update --row R001 --status done` 更新確認
   - `helix retrofit status` JSON 出力確認
   - `helix retrofit done --row R001` status 更新確認
   - `helix retrofit done --row R001` blocked 行あり exit 2 確認
   - `helix retrofit --help` ヘルプ出力確認

**完了条件**:
- `pytest cli/lib/tests/test_retrofit_engine.py -v` 全 PASS
- `bats cli/lib/tests/bats/helix_retrofit.bats` 全 PASS

### Sprint .4: router 登録 + docs 更新 + smoke test

**目標**: `helix retrofit` が `helix` router から呼べる状態にし、docs を更新する

**作業**:
1. `cli/helix` router に `retrofit) exec "$SCRIPT_DIR/helix-retrofit" "$@" ;;` を追加
2. `docs/commands/index.md` に `helix retrofit` 行を追加 (§2 HELIX プロジェクト管理 テーブル)
3. `helix commands check` PASS 確認
4. smoke test:
   ```bash
   helix retrofit --help
   helix retrofit init --slug smoke-test-$(date +%s)
   helix retrofit matrix list --slug smoke-test-$(date +%s) || true
   helix retrofit status
   ```
5. pmo-sonnet 4 artifact 双方向 trace 確認

**完了条件**:
- `helix commands check` PASS
- smoke test 全項目 exit-code 0
- pmo-sonnet レビュー PASS

---

## §6 DoD (Definition of Done)

| # | 条件 |
|---|---|
| D1 | `cli/helix-retrofit` が存在し `bash -n` + `shellcheck` PASS |
| D2 | `cli/lib/retrofit_engine.py` が存在し `python3 -m py_compile` PASS |
| D3 | `pytest cli/lib/tests/test_retrofit_engine.py` 全 PASS |
| D4 | `bats cli/lib/tests/bats/helix_retrofit.bats` 全 PASS |
| D5 | `cli/helix` router に `retrofit` エントリが存在する |
| D6 | `docs/commands/index.md` に `helix retrofit` が記載されている |
| D7 | `helix commands check` PASS |
| D8 | `docs/v2/L7-design/L7-cli-helix-retrofit-impl-design.md` が存在し、subcommand I/O + schema を網羅している |
| D9 | `docs/v2/L7-test-design/L7-cli-helix-retrofit-impl-test-design.md` が存在し、テスト一覧を網羅している |
| D10 | tl-advisor R1 passed または passed_with_minor_changes を記録している |
| D11 | `helix retrofit init --slug smoke-<slug>` が matrix + config + PLAN を正しく生成する |
| D12 | 4 artifact の双方向 trace が確立されている (pmo-sonnet review PASS) |
| D13 | gate-checks.yaml の static チェック適用範囲外 (本 CLI は workflow doc 固有 DoD で代替、automation-gate-map と整合) |

---

## §7 受入条件

| AC | 条件 |
|---|---|
| AC-1 | `helix retrofit init --slug <slug>` が `docs/plans/<slug>-retrofit-matrix.md` + `cli/config/<slug>-retrofit.yaml` + PLAN draft (オプション) を生成する |
| AC-2 | `helix retrofit matrix list --slug <slug>` が matrix 全行を表形式で表示する |
| AC-3 | `helix retrofit matrix update --slug <slug> --row R001 --status done` が matrix YAML frontmatter `rows` と Markdown table (ビュー) を両方更新する |
| AC-4 | `helix retrofit status` が completion_pct と next row (R001 形式 ID) を表示する |
| AC-5 | `helix retrofit done --slug <slug> --row R001 --run-regression` が回帰失敗時に row を `in_progress` に巻き戻し、exit-code 3 を返す |
| AC-6 | `helix retrofit done --slug <slug> --row R001` が blocked 行存在時に exit-code 2 で禁止される |
| AC-7 | `helix retrofit done --slug <slug> --row R001` (blocked なし) が matrix を更新し、done_at を記録する |
| AC-8 | *(削除 — route 連携は C' PLAN scope。本 PLAN では実装しない)* |
| AC-9 | 全回帰テスト (`helix test`) が PASS する |

---

## §8 risk / mitigation

| # | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R1 | retrofit-matrix.md の YAML front matter が大規模 retrofit で肥大化し、git diff が読みにくくなる | Medium | rows 数が 50 を超える場合は `<slug>-retrofit-matrix-rows.yaml` に分離するオプションを実装 (Sprint .2 で検討、本 PLAN では暫定 threshold = 50) |
| R2 | `helix retrofit done --run-regression` が長時間実行になり、CI で timeout する | Medium | 初期実装は**同期実行のみ**。timeout 対策として回帰テストスコープを `phases.regression` で絞り込む。非同期バックグラウンド実行は別 PLAN carry (P2-3 反映) |
| R3 | KindChecker の判定が不安定で、refactor を retrofit と誤判定する | Low | KindChecker は **signal 最優先** (P1-9)、file pattern は補助のみ。混在は exit-code 3 で「分離推奨」。check-kind は内部 utility に降格済みのため外部 API 安定性は不要 |
| R4 | slug 命名規則が統一されず、matrix ファイルが散乱する | Low | `helix retrofit init` は slug の形式を `kebab-case` に強制 (正規表現: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`) し、違反時は exit 2 |
| R5 | PLAN kind=retrofit の frontmatter が plan_validator に未登録で drift 警告が出る | **Low (resolved)** | `cli/lib/plan_validator.py` の `VALID_KINDS` に `retrofit` が含まれることを確認済み。Sprint .1 で `grep VALID_KINDS retrofit` で再確認する手順だけ残す (P1-1 反映、P0 取消) |
| R6 | phase 戻りすぎリスク: retrofit 実行中に要件変更が発生し、L1/L3 戻りが不明確なまま実装継続 | High | **fail-close 強化 (P1-8 反映)**: blocked 行が存在する場合は `done` を exit 2 で完全禁止。blocked 理由が「要件変更の可能性」の場合は L1/L3 再入メッセージを表示。`helix retrofit status` が blocked 件数 > 0 を警告表示。L1/L3 再入条件: blocked row の notes に「L1/L3 確認済」を記録してから `--status in_progress` に戻す |
| R7 | retrofit-matrix.md と PLAN frontmatter の status が乖離する | Medium | `helix retrofit status` が matrix completion_pct と PLAN status の不整合を検出し、警告を表示する (helix doctor への carry 候補) |

---

## §9 V3 接続契約

### signal vocabulary の出典と 3 段構造

**detection-routing.md → route_engine.py → retrofit の 3 段接続**:

`detection-routing.md` が上位シグナル語彙を定義する (drift / 劣化 / 暴走 / 本番障害 / 設計 unknown 多発 等)。本節の `drift_type = dependency_outdated / upgrade / config_drift` は `route_engine.py` (L7-helix-route-implplan §signal 分類) が下位に定義するサブカテゴリである。

```
detection-routing.md の「drift (設計⇔実装乖離)」
  ↓ route_engine.py が drift_type で細分化
    → dependency_outdated / upgrade / config_drift → Retrofit (本 PLAN scope)
    → code_smell / structural              → Refactor (L7-cli-helix-refactor scope)
    → schema / contract                    → Reverse normalization (既存 path)
  ↓ helix retrofit init --slug <slug> で Retrofit に接続
```

**drift_type 分岐契約** (本 PLAN scope 限定): ADR-041 §Decision 参照。
本 PLAN は `drift_type ∈ {dependency_outdated, upgrade, config_drift}` のみを Retrofit 対象として受領する。
- `schema` / `contract` は Reverse (normalization) が担当
- `code_smell` / `structural` は Refactor (L7-cli-helix-refactor-impl) が担当

**upgrade 例外**: ADR-041 で「uncertainty=high または impact=high の場合は Reverse upgrade R0-R4 を前段」と明示済み。本 PLAN は低リスク時のみ Retrofit 直行。

**config_drift 例外**: ADR-041 で「env/infra/prod は人間承認必須、`safety.requires_human_approval=true`」と明示済み。

`cross-cutting-mechanisms.md` が定義する drift-check 横断機構は上記分岐の **上流トリガー** であり、本 CLI は横断機構と別レイヤーに位置する (横断機構がシグナルを生成 → route_engine が分類 → 本 CLI が Retrofit state を管理)。

### helix route との接続契約 (本 PLAN scope 外)

> **[P0-1 反映 — C' 移管]** `helix route suggest` の `drift_type` 分岐 / `recommended_command` フィールド追加 / Retrofit mode routing は **`L7-route-engine-drift-type-retrofit-extplan` (C') scope**。本 PLAN では実装しない。

**recommended_command 契約** (ADR-042 RecommendedCommandV1 schema):

```json
{
  "schema_version": "v1",
  "command": "helix plan draft",
  "args": {
    "kind": "retrofit",
    "drift_type": "dependency_outdated",
    "signal_id": "drift"
  },
  "safety": {
    "auto_apply": false,
    "requires_human_approval": false,
    "requires_preflight": false
  }
}
```

詳細は ADR-042 §Decision RecommendedCommandV1 schema 参照。
`helix retrofit init` は PLAN 確定後の手動着手コマンドであり、route から自動誘導される recommended_command ではない (C' 完遂後の接続は C8 carry 参照)。

本 PLAN (C) と C' の接続ポイント:
- C 完遂後: `helix retrofit init --slug <slug>` が direct invocation で動作
- C' 完遂後: `helix route suggest --signal dependency_outdated` が `recommended_command` (ADR-042 RecommendedCommandV1 形式) を返し、`helix plan draft --kind retrofit` で PLAN 起票へ誘導
- C + C' 統合後の route → `helix plan draft --kind retrofit` E2E フロー確認は §11 carry C8 として記録

### KindChecker 内部ユーティリティと将来連携

`KindChecker` は `retrofit_engine.py` の内部 utility として維持する (公開 subcommand `check-kind` は削除済み)。
将来の `helix refactor` 実装時または C' 連携時に、signal / file pattern を受け付けて判定結果を返す API として再利用できる:

```python
# 内部呼び出し例 (route_engine.py または他 CLI から)
from cli.lib.retrofit_engine import KindChecker
kind, reason = KindChecker().check(files=changed_files, signal="dependency_outdated")
# kind: "retrofit" / reason: "signal=dependency_outdated (priority 1)"
```

判定優先順 (P1-9 反映):
1. signal 最優先 → retrofit / refactor / reverse を確定
2. signal なし時のみ file pattern 補助
3. 混在 → exit 3 で分割推奨 (schema/contract は Reverse normalization を案内)

### L4/L5 追補との連携

retrofit-workflow.md が定義する Forward 接続:
> 影響範囲に応じて L4 基本設計・L5 詳細設計・L7 実装へ追補する。検証は L8 結合テスト・L9 総合テスト（回帰）。要件自体が変わる場合のみ L1 / L3 へ戻す。

これを CLI でサポートする:
- `config.yaml` の `phases.design_supplement` フィールドに `[L4]` / `[L5]` を記録し、追補が必要な設計工程を明示
- `helix retrofit status` が `phases.design_supplement` の未完了追補を警告として表示
- `helix retrofit done --run-regression` が `config.yaml` の `phases.regression` (L8/L9) でテストを実行 (P1-6 反映、`phases.regression` が正本フィールド)

---

## §10 関連 doc / 関連 PLAN

| 種別 | パス | 関係 |
|---|---|---|
| 正本設計 | HELIX-workflows/helix-process/retrofit-workflow.md | parent_design (accepted) |
| mode 全体 | HELIX-workflows/helix-process/integration-map.md | mode 間連携の全体地図。§結論 #2 + §テンプレートの穴 (retrofit-matrix) carry 解消の根拠 |
| 逸脱種別 | HELIX-workflows/helix-process/deviation-plan-map.md | retrofit kind の逸脱定義。kind=impl + retrofit-matrix generates 根拠 |
| 参考 PLAN | docs/plans/L7/L7-helix-recover-implplan.md | 同パターン CLI 実装 (recover) |
| 参考 PLAN | docs/plans/L7/L7-helix-route-implplan.md | route との責務分担 |
| refactor 設計 | HELIX-workflows/helix-process/refactor-workflow.md | refactor との意味的境界 |
| シグナル語彙出典 | HELIX-workflows/helix-process/detection-routing.md | §9 接続契約 signal vocabulary 上位出典 (drift / 劣化 / 暴走 等の上位シグナル定義) |
| 横断機構境界 | HELIX-workflows/helix-process/cross-cutting-mechanisms.md | drift-check 横断機構との責務境界 (Reverse vs Retrofit の分岐点) |
| router | cli/helix | Sprint .4 で追記対象 |
| DB 状態管理 | cli/lib/helix_db.py | helix.db は参照のみ (matrix は YAML ファイルが正本) |
| commands 索引 | docs/commands/index.md | Sprint .4 で追記対象 |

---

## §11 carry / 残課題

| # | carry | 優先度 | 担当先 |
|---|---|---|---|
| C1 | `helix route suggest` に `recommended_command: "helix retrofit init --slug ..."` フィールドを追加する拡張 | P2 | L7-helix-route-implplan.md §11 carry に追記 |
| C2 | plan_validator `VALID_KINDS` に `retrofit` が含まれることを Sprint .1 で `grep -n 'retrofit' cli/lib/plan_validator.py` で確認。**resolved / Sprint .1 verification evidence**: R5 参照 (VALID_KINDS 含有確認済み、P0 carry 取消、Low risk に降格) | ~~P0~~ **resolved** | SE (Sprint .1 着手時に再確認のみ) |
| C3 | `helix doctor` で retrofit-matrix と PLAN status の乖離検出を追加 | P2 | 別 PLAN (helix doctor 拡張) |
| C4 | rows 数 > 50 の場合に `<slug>-retrofit-matrix-rows.yaml` へ分離するオプション | P3 | Sprint .2 時点で暫定判断 |
| C5 | `helix refactor` CLI が実装された際に `check-kind` exit-code との自動連携フローを確立 | P3 | refactor CLI 実装 PLAN が起票された時点で連携 |
| C6 | retrofit-matrix のスキーマ lint (required field 欠損 / status enum 違反) を `helix doctor` に追加 | P2 | 別 PLAN (helix doctor 拡張) |
| C7 (new) | Sprint .2 `init` サブコマンド実装完了後、`integration-map.md §テンプレートの穴` の retrofit-matrix 不在 carry を update し、本 PLAN 完遂を証跡として記録する | P1 (Sprint .2 完了後即) | PM |
| C8 (new) | C' (`L7-route-engine-drift-type-retrofit-extplan`) 完遂後: route → `helix plan draft --kind retrofit` 統一 (ADR-042 採用) の E2E テスト追加。`helix route suggest --signal dependency_outdated` が `recommended_command: {"command": "helix plan draft", "args": {"kind": "retrofit"}}` を返すことを bats で確認。`helix retrofit init` は PLAN 確定後の手動着手として位置付けを明文化 | P2 | next session (C' 完遂後) |
