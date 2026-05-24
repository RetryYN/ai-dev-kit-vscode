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
    artifact_type: test_design
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
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/retrofit-workflow.md](../../../HELIX-workflows/helix-process/retrofit-workflow.md)
> **本 PLAN の対象**: `cli/helix-retrofit` コマンドの新規実装。依存・フレームワーク・基盤を **要件を変えずに段階的に移行** するための CLI エントリーポイントを実体化する。
> **位置づけ**: CLAUDE.md / HELIX_CORE.md で「dedicated CLI 未整備、PLAN kind + retrofit-matrix + config で運用」と carry 明示された案件を本 PLAN で実体化する。retrofit-workflow.md (status: accepted, 2026-05-24) が正本設計。

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

> **判定シグナル**: `helix route suggest` が `drift_type=dependency_outdated` / `upgrade` / `config_drift` を返す場合は Retrofit。`drift_type=structural` / `code_smell` を返す場合は Refactor。境界が曖昧な場合は `helix retrofit plan --check-kind` で判定補助を提供する。

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

#### サブコマンド構成

```
helix retrofit [subcommand] [options]

subcommand:
  init         retrofit-matrix.md と config YAML を生成し、PLAN kind=retrofit を draft 起票
  matrix       retrofit-matrix.md の表示・更新 (row の追加・status 変更・一覧)
  config       config YAML の表示・差分確認 (生成は init、適用は手動ガード)
  status       現在の retrofit PLAN 進捗と matrix 完了率を表示
  plan         PLAN kind=retrofit の draft 起票 (矩形が既存なら既存 PLAN と接続)
  check-kind   変更シグナルから retrofit / refactor / forward を判定して提案
  done         指定 matrix 行を completed にマークし、回帰テスト促進メッセージを表示
```

#### サブコマンド詳細仕様

**`helix retrofit init --slug <slug> [--plan-id PLAN-NNN]`**

```
入力:
  --slug: retrofit 識別子 (例: python312-migration、sqlite-to-postgres)
  --plan-id: 既存 PLAN に紐付ける場合の ID (省略時は新規 PLAN draft を生成)
  --drive: be (default) / fullstack / db

出力:
  docs/plans/<slug>-retrofit-matrix.md  (retrofit-matrix テンプレート生成)
  cli/config/<slug>-retrofit.yaml       (config テンプレート生成)
  docs/plans/L7/L7-<slug>-retrofitplan.md  (PLAN draft、--plan-id 省略時)

exit-code:
  0: 成功
  1: slug 重複 (既存 matrix あり、--force で上書き)
  2: 設定エラー
```

**`helix retrofit matrix [list|add|update|show] [options]`**

```
helix retrofit matrix list --slug <slug>
  → retrofit-matrix の全行を表形式で表示 (status 色分け: todo/in-progress/done/blocked)

helix retrofit matrix add --slug <slug> --from "<旧>" --to "<新>" --scope "<影響範囲>" [--phase L4]
  → matrix に新行を追加 (phase は L4/L5/L7 追補先)

helix retrofit matrix update --slug <slug> --row <N> --status <todo|in-progress|done|blocked>
  → 指定行の status を更新 (done 時は done-at タイムスタンプを付与)

helix retrofit matrix show --slug <slug> --summary
  → matrix 完了率 (done/total) + blocked 件数 + pending 件数を表示

exit-code: 0 成功 / 1 slug 不在 / 2 row 番号範囲外
```

**`helix retrofit status [--slug <slug>] [--json]`**

```
入力: --slug (省略時は全 slug)
出力例:
  [retrofit] slug: python312-migration
    plan: L7-python312-migration-retrofitplan (draft)
    matrix: 4/12 done (33%), 2 blocked, 6 pending
    config: cli/config/python312-migration-retrofit.yaml (exists)
    next: matrix row 5 (logging → structlog) [in-progress]

exit-code: 0 (slug 不在でも 0、"no active retrofit" メッセージ)
```

**`helix retrofit check-kind [--signal <drift_type>] [--files <path,...>]`**

```
入力:
  --signal: helix route suggest の drift_type 出力を受け取る
  --files: 変更対象ファイル一覧 (省略時は git diff --name-only HEAD)

出力: retrofit / refactor / forward のいずれかと根拠を表示
判定ロジック:
  - requirements.txt / pyproject.toml / Dockerfile / *.yaml (config) 変更 → retrofit 優先
  - import 変更のみ、振る舞い変化なし → refactor 優先
  - 新機能 / 新 API / スキーマ追加 → forward 優先
  - 混在 → retrofit + forward の分離を推奨

exit-code: 0 retrofit / 1 refactor / 2 forward / 3 混在
```

**`helix retrofit done --slug <slug> --row <N> [--run-regression]`**

```
入力: slug + row 番号
動作:
  1. matrix 行を status=done, done-at=<timestamp> に更新
  2. --run-regression 付きの場合: `helix test --scope L8-regression` を起動
  3. 全行 done の場合: retrofit 完了メッセージ + PLAN status=complete 更新促進

exit-code: 0 成功 / 1 slug/row 不在
```

#### 入力源と凍結設計

| サブコマンド | 主入力源 | 凍結理由 |
|---|---|---|
| `init` | CLI 引数 (--slug, --plan-id) | ユーザー明示指定 |
| `matrix list/show` | `docs/plans/<slug>-retrofit-matrix.md` (YAML front + Markdown table) | 人間可読な単一 source of truth |
| `status` | matrix.md + PLAN frontmatter `status` | helix.db 不依存で軽量 |
| `check-kind` | `git diff --name-only HEAD` + `--signal` 引数 | ファイル名パターンで安定判定 |
| `done` | matrix.md row update + helix test | 機械 + 人間の両確認 |

---

### §2.B retrofit_engine.py 設計

#### モジュール構成

```python
# cli/lib/retrofit_engine.py

class RetrofitMatrix:
    """retrofit-matrix.md の YAML front matter + Markdown table を管理"""
    def load(slug: str) -> RetrofitMatrix
    def add_row(from_: str, to: str, scope: str, phase: str = "L7") -> None
    def update_row(row_n: int, status: str) -> None
    def summary() -> dict  # {total, done, in_progress, blocked, pending, completion_pct}
    def save() -> None

class RetrofitConfig:
    """cli/config/<slug>-retrofit.yaml を管理"""
    def load(slug: str) -> RetrofitConfig
    def show_diff(current_path: str) -> str  # 現状 config との差分表示
    def save_template(slug: str, drive: str) -> Path

class KindChecker:
    """変更ファイル + signal から retrofit/refactor/forward を判定"""
    RETROFIT_PATTERNS = [r"requirements.*\.txt", r"pyproject\.toml",
                          r"Dockerfile", r"docker-compose", r"\.ya?ml$"]
    REFACTOR_SIGNALS  = ["structural", "code_smell", "naming"]
    def check(files: list[str], signal: str = "") -> tuple[str, str]
    # returns (kind, reason)

def init_retrofit(slug: str, plan_id: str | None, drive: str) -> dict:
    """init subcommand の実装本体"""

def get_retrofit_status(slug: str | None, as_json: bool) -> dict:
    """status subcommand の実装本体"""
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
    notes: ""
  - id: R002
    from: "datetime.utcnow()"
    to: "datetime.now(timezone.utc)"
    scope: "cli/lib/*.py"
    phase: L7
    status: done
    done_at: "2026-05-24T10:30:00"
    notes: "DeprecationWarning 対応 (Python 3.13+ removal)"
---

# Retrofit Matrix: python312-migration

| ID | From | To | Scope | Phase | Status | Done At |
|---|---|---|---|---|---|---|
| R001 | Python 3.9 | Python 3.12 | 全 .py ファイル | L7 | todo | - |
| R002 | datetime.utcnow() | datetime.now(timezone.utc) | cli/lib/*.py | L7 | done | 2026-05-24 |
```

### config YAML テンプレート (`cli/config/<slug>-retrofit.yaml`)

```yaml
# cli/config/python312-migration-retrofit.yaml
slug: python312-migration
drive: be
phases:
  design_supplement: [L4, L5]   # 追補する設計工程
  regression: [L8, L9]           # 回帰テスト工程
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

### helix route → helix retrofit の連携フロー

```
ユーザー: 依存更新・基盤移行を検討
  ↓
helix route suggest [--signal dependency_outdated]
  → 出力例: "mode: retrofit — 推奨コマンド: helix retrofit init --slug <slug>"
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

### helix route との境界プロトコル

- `helix route` は **モードの提案のみ** を返し、state 変更をしない (read-only に近い)
- `helix retrofit` は **state を持つ** (matrix.md / config.yaml を生成・更新する)
- `helix route suggest` の出力に `recommended_command` フィールドを追加し、retrofit/recover/refactor へのリンクを返す (route_engine.py の拡張 carry、本 PLAN scope 外)

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
   - `KindChecker.check()` retrofit / refactor / forward 各シグナル
   - `init_retrofit()` matrix + config + PLAN 生成の 3 点セット確認
   - エラー系: slug 重複 / row 番号範囲外 / slug 不在
2. `cli/lib/tests/bats/helix_retrofit.bats`:
   - `helix retrofit init` 出力確認
   - `helix retrofit matrix list` 表形式出力確認
   - `helix retrofit status` JSON 出力確認
   - `helix retrofit check-kind` exit-code 確認
   - `helix retrofit done` status 更新確認
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
   helix retrofit status
   helix retrofit check-kind --files "requirements.txt"
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
| AC-3 | `helix retrofit matrix update --slug <slug> --row R001 --status done` が matrix YAML + Markdown table を更新する |
| AC-4 | `helix retrofit status` が completion_pct と next row を表示する |
| AC-5 | `helix retrofit check-kind --files requirements.txt` が exit-code 0 (retrofit) を返す |
| AC-6 | `helix retrofit check-kind --signal structural` が exit-code 1 (refactor) を返す |
| AC-7 | `helix retrofit done --slug <slug> --row R001` が matrix を更新し、done_at を記録する |
| AC-8 | `helix route suggest` の出力に retrofit の `recommended_command` が含まれる (**本 PLAN scope は確認のみ**、route_engine.py 拡張は別 PLAN carry) |
| AC-9 | 全回帰テスト (`helix test`) が PASS する |

---

## §8 risk / mitigation

| # | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R1 | retrofit-matrix.md の YAML front matter が大規模 retrofit で肥大化し、git diff が読みにくくなる | Medium | rows 数が 50 を超える場合は `<slug>-retrofit-matrix-rows.yaml` に分離するオプションを実装 (Sprint .2 で検討、本 PLAN では暫定 threshold = 50) |
| R2 | `helix retrofit done --run-regression` が長時間実行になり、CI で timeout する | Medium | `--run-regression` は `helix test --scope L8-regression` を**バックグラウンド起動** (`run_in_background: true` 相当) し、PID を表示して非同期に完了を待つ実装にする |
| R3 | `check-kind` の判定が不安定で、refactor を retrofit と誤判定する | Low | KindChecker は **保守的** (混在時は exit-code 3 で「分離推奨」)。過剰な retrofit 起票はコスト高だが、refactor と分離しないより低コスト |
| R4 | slug 命名規則が統一されず、matrix ファイルが散乱する | Low | `helix retrofit init` は slug の形式を `kebab-case` に強制 (正規表現: `^[a-z0-9][a-z0-9-]*[a-z0-9]$`) し、違反時は exit 2 |
| R5 | PLAN kind=retrofit の frontmatter が plan_validator に未登録で drift 警告が出る | **High** | plan_validator の `KIND_ENUM` に `retrofit` がすでに含まれているか確認 (**Sprint .1 で P0 確認、不在なら enum 追加を即 carry 起票**。integration-map §テンプレートの穴と連動、kind 不在は retrofit PLAN 起票を完全に阻害する) |
| R6 | phase 戻りすぎリスク: retrofit 実行中に要件変更が発生し、L1/L3 戻りが不明確なまま実装継続 | High | `helix retrofit matrix update --status blocked --notes "要件変更の可能性、L1/L3 確認が必要"` を明示し、`helix route suggest` で L1/L3 再入を促す。blocked 件数 > 0 の場合は `helix retrofit status` が警告メッセージを表示する |
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

**Retrofit / Refactor / Reverse の drift_type 分岐**:
- `drift_type=dependency_outdated` → **Retrofit** = 依存バージョンの更新・基盤移行
- `drift_type=upgrade` → **Retrofit** = version 移行 (Reverse type=upgrade と連動)
- `drift_type=config_drift` → **Retrofit** = 設定ファイル乖離解消
- `drift_type=code_smell` / `structural` → **Refactor** (振る舞い不変の構造改善、Refactor scope)
- `drift_type=schema` / `contract` → **Reverse normalization** (既存 Reverse path)

`cross-cutting-mechanisms.md` が定義する drift-check 横断機構は上記分岐の **上流トリガー** であり、本 CLI は横断機構と別レイヤーに位置する (横断機構がシグナルを生成 → route_engine が分類 → 本 CLI が Retrofit state を管理)。

### helix route → helix retrofit 接続

`helix route suggest` が以下の drift_type を検出した場合に retrofit を提案する:

| drift_type (route_engine.py) | retrofit への接続条件 | 推奨コマンド |
|---|---|---|
| `dependency_outdated` | 依存バージョンの更新が必要 | `helix retrofit init --slug <inferred_slug>` |
| `upgrade` (Reverse type=upgrade) | 既存 system + 新版の差分対応 | `helix retrofit init --slug <inferred_slug>` |
| `config_drift` | 設定ファイルと実態の乖離 | `helix retrofit init --slug <inferred_slug> --no-plan` |

**接続契約の拡張 (carry)**:
`route_engine.py` に `recommended_command` フィールドを追加する拡張は **本 PLAN scope 外**。
→ `L7-helix-route-implplan.md §11 carry` に追記して連携する。

### helix refactor (未実装) との信号分岐

将来の `helix refactor` 実装時に、`helix retrofit check-kind` の exit-code を信号として利用できる:

```bash
kind=$(helix retrofit check-kind --files "$CHANGED_FILES"; echo $?)
case $kind in
  0) helix retrofit init --slug ... ;;   # retrofit
  1) helix refactor init --slug ... ;;   # refactor (未実装)
  2) helix plan draft ... ;;             # forward
  3) echo "mixed: split recommended" ;;  # 分離推奨
esac
```

### L4/L5 追補との連携

retrofit-workflow.md が定義する Forward 接続:
> 影響範囲に応じて L4 基本設計・L5 詳細設計・L7 実装へ追補する。検証は L8 結合テスト・L9 総合テスト（回帰）。要件自体が変わる場合のみ L1 / L3 へ戻す。

これを CLI でサポートする:
- `config.yaml` の `phases.design_supplement` フィールドに `[L4]` / `[L5]` を記録し、追補が必要な設計工程を明示
- `helix retrofit status` が `design_supplement` の未完了追補を警告として表示
- `helix retrofit done --run-regression` が `config.yaml` の `regression.phases` (L8/L9) でテストを実行

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
| C2 | plan_validator の `KIND_ENUM` に `retrofit` が含まれているか確認。不在の場合は enum 追加 PR を即起票 | **P0** (Sprint .1 最優先確認、integration-map §テンプレートの穴と連動) | SE (Sprint .1 着手時に最初に確認) |
| C3 | `helix doctor` で retrofit-matrix と PLAN status の乖離検出を追加 | P2 | 別 PLAN (helix doctor 拡張) |
| C4 | rows 数 > 50 の場合に `<slug>-retrofit-matrix-rows.yaml` へ分離するオプション | P3 | Sprint .2 時点で暫定判断 |
| C5 | `helix refactor` CLI が実装された際に `check-kind` exit-code との自動連携フローを確立 | P3 | refactor CLI 実装 PLAN が起票された時点で連携 |
| C6 | retrofit-matrix のスキーマ lint (required field 欠損 / status enum 違反) を `helix doctor` に追加 | P2 | 別 PLAN (helix doctor 拡張) |
| C7 (new) | Sprint .2 `init` サブコマンド実装完了後、`integration-map.md §テンプレートの穴` の retrofit-matrix 不在 carry を update し、本 PLAN 完遂を証跡として記録する | P1 (Sprint .2 完了後即) | PM |
