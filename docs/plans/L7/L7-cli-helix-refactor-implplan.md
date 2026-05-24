---
plan_id: L7-cli-helix-refactor-impl
title: "L7-cli-helix-refactor-implplan: helix-refactor CLI 実装 — Refactor mode (振る舞い不変・構造改善) 起動コマンド (CLI carry 解消版)"
kind: impl
layer: L7
drive: be
status: completed
created: 2026-05-24
revised: 2026-05-24-R3
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/refactor-workflow.md
parent_design_addenda:
  - docs/adr/ADR-041-drift-type-7-categories-routing-decision.md   # drift_type SoT
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md   # recommended_command SoT
pairs_test_design:
  - HELIX-workflows/helix-process/deviation-plan-map.md
is_reference: false
agent_slots:
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check (CLI 設計・subcommand 責務分離・保護網連携・route 接続契約)"
  - role: se
    slot_label: "SE — cli/helix-refactor + cli/lib/refactor_engine.py 実装 + test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・4 artifact 双方向 trace review"
generates:
  - artifact_path: cli/helix-refactor
    artifact_type: cli_extension
  - artifact_path: cli/lib/refactor_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_refactor_engine.py
    artifact_type: test
  - artifact_path: cli/tests/helix-refactor.bats
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires:
    - L7-helix-route-implplan
    - L7-route-engine-drift-type-retrofit-ext
    - ADR-041   # drift_type SoT
    - ADR-042   # recommended_command SoT
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/refactor-workflow.md
  - HELIX-workflows/helix-process/deviation-plan-map.md
  - HELIX-workflows/helix-process/integration-map.md
  - cli/helix
  - cli/lib/helix_db.py
  - cli/lib/lock_helper.py
  - cli/lib/recovery_engine.py
  - docs/commands/index.md
  - docs/plans/L7/L7-helix-recover-implplan.md
  - docs/plans/L7/L7-helix-route-implplan.md
  - docs/plans/L7/L7-route-engine-drift-type-retrofit-ext.md
  - docs/adr/ADR-041-drift-type-7-categories-routing-decision.md
  - docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/refactor-workflow.md](../../../HELIX-workflows/helix-process/refactor-workflow.md)
> **本 PLAN の対象**: `cli/helix-refactor` コマンドの新規実装。HELIX-workflows V2 で Refactor mode が独立 mode として整理されたが、**「dedicated CLI 未整備」** という carry が CLAUDE.md に明示されたまま残っている。本 PLAN でその carry を解消する。
>
> **carry 根拠** (CLAUDE.md / HELIX_CORE.md の記述):
> > Refactor (kind=`refactor`) → HELIX-workflows/helix-process/refactor-workflow.md
> > **CLI 未整備の警告**: Refactor / Retrofit / Recovery は `helix refactor` 等の CLI が存在しない。エージェントが叩いて失敗するリスク回避のため、必ず workflow doc 正本 + PLAN kind / template で扱う。CLI 契約整理は後続 ADR / PLAN 候補。
>
> **位置づけ**: integration-map.md §結論と優先順位 に連なる CLI 整備 carry の一環。`helix recover` (commit 904c4f6) と同パターンで実装する。**Refactor CLI は refactor-workflow.md が要求するフローを CLI 化するのみ** で、リファクタリング作業そのもの (コード編集) は Codex SE が担う。

### kind: impl (not add-impl) の根拠 (deviation-plan-map.md)

deviation-plan-map で Add-feature は「既存システムへの差分追補」(generates = design 追補 / module 追補)。
本 PLAN は Refactor mode の workflow doc (refactor-workflow.md) が設計凍結済みの状態で、
そのフローを CLI として初期実装する Forward 標準案件。add-impl でなく impl が適切。

### parent_design (accepted status) を採用する理由

`refactor-workflow.md` の frontmatter status は `accepted` (2026-05-24)。HELIX-workflows 正本化群の一部として design-frozen。本 PLAN は親設計を **変更せず** L7 実装を行う。

### generates trace と deviation-plan-map の対応

deviation-plan-map.md における Refactor 行 (kind=refactor) は `generates=module` を想定する。
本 PLAN の frontmatter `generates` フィールドと対応関係:

| generates (本 PLAN) | artifact_type | deviation-plan-map 対応 |
|---|---|---|
| cli/helix-refactor | cli_extension | Refactor mode 起動 CLI (新規モジュール相当) |
| cli/lib/refactor_engine.py | python_module | Refactor session 管理ロジック (module 生成) |
| cli/lib/tests/test_refactor_engine.py | test | V-model テスト成果物 (テストコード artifact) |
| cli/lib/tests/bats/helix_refactor.bats | test | CLI smoke test 成果物 |

### integration-map との接続

**integration-map §結論と優先順位 #2 carry 解消**: 本 PLAN は integration-map が「CLI 未整備の警告」として列挙した Refactor / Retrofit / Recovery CLI carry のうち Refactor を解消する。

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | refactor-workflow.md 読み込み + subcommand 要件抽出 | PM | ✅ done |
| 2 | CLI インターフェース設計 (subcommand 構成 / 保護網確認 / state management) | PM | ✅ done (§2.A) |
| 3 | refactor_engine.py 設計 (状態管理 / 保護網判定 / Step 追跡) | PM | ✅ done (§2.B) |
| 4 | 既存 CLI 責務分離の明文化 (recover / route / plan / sprint との境界) | PM | ✅ done (§3) |
| 5 | V3 接続契約設計 (route → refactor signal mapping) | PM | ✅ done (§8) |
| 6 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | ✅ done (needs_revision) |
| 7 | TL 第 1 ラウンド指摘反映 (P1 8 件 + P2 一部) | PM | ✅ done (本 revision) |
| 8 | tl-advisor 第 2 ラウンド (revision 確認) | PM → TL | □ pending |
| 9 | Sprint .2a: failing tests 実装 (T-01〜T-15 先行、TDD) | PM → SE | □ pending |
| 10 | Sprint .2b: cli/helix-refactor + cli/lib/refactor_engine.py 実装 (T-01〜T-15 全 PASS) | PM → SE | □ pending |
| 11 | Sprint .3: T-16〜T-24 追加テスト + bats B-01〜B-06 (cli/tests/helix-refactor.bats) | SE | □ pending |
| 12 | Sprint .4: cli/helix router 登録 + helix help + docs/commands/index.md + helix commands check | SE | □ pending |
| 13 | pmo-sonnet で 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 14 | commit + push | PM | □ pending |

---

## §2 実装計画

### §2.A cli/helix-refactor CLI 設計

#### refactor-workflow.md から抽出した要件

refactor-workflow.md の基本フローを CLI に対応させる:

```
保護網のテスト整備 → 小さなリファクタリング → テスト緑確認 → コミット → 繰り返し
```

対応する CLI フロー:

```
helix refactor init   # 対象範囲・保護網確認・state 初期化
helix refactor check  # 保護網テストを実行し振る舞い不変を確認
helix refactor status # 現在の refactor session 状態を表示
helix refactor done   # session を完了・クリア
```

#### subcommand 構成 (最小設計、workflow doc 要求のみ)

```
helix refactor [subcommand] [options]

subcommand:
  init      対象モジュール・ファイルを登録し、保護網テストを記録して refactor session を開始
  check     保護網テスト (既存テスト) を実行し、振る舞い不変を機械確認
  status    現在 session の状態 (対象ファイル / 保護網テスト / step 進捗) を表示
  done      session 完了を宣言し、最終テスト green 確認後に session state をクリア
```

**設計方針**:
- subcommand は refactor-workflow.md の 5 ステップ (保護網 / 小変更 / テスト緑 / commit / 繰り返し) を支援するのに必要最小限
- `plan` subcommand は **実装しない**: `helix plan` (既存) で kind=refactor PLAN を起票する責務はそちらに委譲
- `rollback` subcommand は **実装しない**: Refactor は振る舞い不変が前提のため、git 操作は手動ガード
- step 間の commit は `git commit` / `helix push` で行う (refactor CLI は wrap しない)

#### subcommand 詳細仕様

##### helix refactor init

```
helix refactor init --target <path> [--target <path>...]
                    [--test-cmd <cmd>]
                    [--plan-id <plan-id>]
                    [--signal-id <signal>]
                    [--auto-routed-from <cli-name>]
                    [--drift-type <drift_type>]
                    [--from-debt-id <debt-id>]

--target           リファクタ対象のファイル / ディレクトリ (複数指定可)
--test-cmd         保護網テストのコマンド (省略不可。必須引数。デフォルトなし)
--plan-id          対応する kind=refactor PLAN ID (省略時は warning + trace_status=unlinked)
--signal-id        route が検出した signal_id (例: drift / debt_degradation)
--auto-routed-from 自動ルーティング元の CLI 名 (例: helix-route)
--drift-type       drift の細分類 (code_smell / structural のみ受付。他は拒否)
--from-debt-id     debt id を指定して連携 (helix debt list 参照)
```

> **P1-8 必須化**: `--test-cmd` は省略不可。省略した場合は `exit 2: --test-cmd is required` を返す。
> `helix test` を指定することで全回帰を保護網にすることも可能だが、
> 速度の観点から対象モジュールのテストに絞ることを推奨する (§7 R-2 参照)。

動作:
1. 対象ファイルが存在するか確認
2. `--test-cmd` を実行し **現在 green かどうか** を確認 (red なら init を中止、エラー出力)
3. `.helix/refactor-session.json` に session state を記録
4. 初期保護網テスト結果 (pass/fail/skip 件数) を state に記録
5. `--auto-routed-from` が指定された場合、session state に `routed_from` / `route_signal` / `drift_type` を記録

exit code:
- `0`: 保護網 green、session 初期化完了
- `1`: 保護網 red (テスト失敗)、init 中止
- `2`: 対象ファイル不在 / 設定エラー

出力例:
```
[helix refactor init]
target: cli/lib/skill_recommender.py
保護網テスト: pytest cli/lib/tests/test_skill_recommender.py -q
  passed: 14 / failed: 0 / skipped: 1
保護網 GREEN ✓ — session 開始 (session_id: refactor-20260524-001)
```

##### helix refactor check

```
helix refactor check [--verbose]
```

動作:
1. `.helix/refactor-session.json` から session state を読む (session なければ `exit 2: no active session`)
2. session 記録の `--test-cmd` を実行
3. 結果を比較表示 (init 時の baseline vs 現在)
4. 失敗件数が増えた場合は `REGRESSION DETECTED` を出力

exit code:
- `0`: 振る舞い不変 (passed >= baseline_passed AND failed == 0 AND total >= baseline_total)
- `1`: リグレッション検出 (failed > 0 または passed < baseline_passed または total < baseline_total)
- `2`: session なし / テスト実行失敗

> **P2-3**: baseline 比較は `passed >= baseline_passed` だけでなく `total < baseline_total` (テスト件数減少) も regression 扱いとする。テストが削除されて数が合わない場合も REGRESSION DETECTED を出力する。

出力例:
```
[helix refactor check] session: refactor-20260524-001
baseline: passed=14 / failed=0
current:  passed=14 / failed=0
振る舞い不変 ✓ — 次の小変更を実施してください
```

リグレッション例:
```
[helix refactor check] session: refactor-20260524-001
baseline: passed=14 / failed=0
current:  passed=13 / failed=1
REGRESSION DETECTED ✗ — 変更を revert して保護網を緑に戻してください
  failed: test_recommend_with_cache[cache_hit]
```

##### helix refactor status

```
helix refactor status [--json]
```

動作:
1. `.helix/refactor-session.json` を読む (なければ `no active refactor session`)
2. session 情報を表示 (target files / plan_id / test_cmd / baseline / 開始時刻)

exit code: `0` (session あり) / `1` (session なし)

出力例:
```
[helix refactor status]
session_id:   refactor-20260524-001
target:       cli/lib/skill_recommender.py
plan_id:      L7-skill-recommender-refactorplan (optional)
test_cmd:     pytest cli/lib/tests/test_skill_recommender.py -q
baseline:     passed=14 / failed=0 / skipped=1
started:      2026-05-24T14:00:00+09:00
last_check:   2026-05-24T15:30:00+09:00
check_count:  3
```

##### helix refactor done

```
helix refactor done [--force --reason <reason>]
```

> **P2-1**: `--skip-final-check` は削除。強制終了が必要な場合は `--force --reason <理由>` を使用し、
> 理由を session state の `force_close_reason` フィールドに監査ログとして記録する。

動作:
1. `--force` なければ `helix refactor check` を自動実行 (対象テスト + 全回帰または `--test-cmd`)
2. 振る舞い不変 (check: exit 0) でなければ `done` を中止 (`exit 1: regression exists, cannot close session`)
3. 問題なければ session state を `completed` にマークし `.helix/refactor-session.json` を削除
4. `--force` の場合は check をスキップし、`force_close_reason` を audit ログに出力して close

> **P1-8 done 保護網契約**: done 時の自動 check は session 記録の `test_cmd` を実行する。
> `test_cmd` が対象モジュールのみの場合、必要に応じて全回帰 (`helix test`) も併せて実行する運用を推奨。
> done が exit 0 で完了した場合、担当 SE は L8/L9 regression command を別途実行すること (§2.D B-07 参照)。

exit code:
- `0`: 完了
- `1`: 最終 check でリグレッション検出、session 継続
- `2`: session なし / 引数エラー

---

### §2.B cli/lib/refactor_engine.py 設計

Python モジュール。`cli/helix-refactor` のバックエンドロジックを担う。`cli/helix-recover` → `cli/lib/recovery_engine.py` と同パターン。

#### session state schema (.helix/refactor-session.json)

```python
@dataclass(frozen=True, slots=True)
class RefactorSession:
    session_id: str                  # refactor-YYYYMMDD-NNN
    targets: list[str]               # 対象 file/dir path list
    test_cmd: str                    # 保護網テストコマンド (必須)
    plan_id: str | None              # kind=refactor PLAN ID (optional、省略時 trace_status=unlinked)
    baseline_passed: int
    baseline_failed: int
    baseline_skipped: int
    baseline_total: int              # P2-3: total も記録して減少 regression を検出
    started_at: str                  # ISO8601
    last_check_at: str | None
    check_count: int
    status: Literal["active", "completed"]
    # P1-2: route 接続フィールド
    routed_from: str | None          # --auto-routed-from の値 (例: helix-route)
    route_signal: str | None         # --signal-id の値 (例: drift, debt_degradation)
    drift_type: str | None           # --drift-type の値 (code_smell / structural のみ許可)
    # P2-4: 追加 metadata
    schema_version: str              # session schema version (現在: "1")
    project_root: str                # HELIX_PROJECT_ROOT
    created_by: str                  # 起動 user / agent (default: os.getenv("USER"))
    last_result: Literal["pass", "fail", "unknown"] | None
    targets_hash: str                # targets list の sha256 (変更検知用)
    trace_status: Literal["linked", "unlinked"]  # plan_id 不在時は unlinked
    force_close_reason: str | None   # --force 使用時の監査ログ
```

#### 主要関数

```python
def init_session(targets: list[str], test_cmd: str, plan_id: str | None) -> RefactorSession:
    """保護網テスト実行 → session 初期化。テスト失敗なら RefactorInitError を raise。"""

def run_check(session: RefactorSession) -> CheckResult:
    """保護網テスト実行 → baseline と比較。CheckResult(ok: bool, delta: dict) を返す。"""

def load_session() -> RefactorSession | None:
    """`.helix/refactor-session.json` を読む。なければ None。"""

def save_session(session: RefactorSession) -> None:
    """session を `.helix/refactor-session.json` に書く。"""

def close_session(session: RefactorSession) -> None:
    """session を completed にマーク後、JSON を削除。"""

def run_test_cmd(cmd: str) -> TestResult:
    """test_cmd を subprocess で実行し、pass/fail/skip 件数をパース。"""
```

#### テストパース戦略

`test_cmd` は任意コマンドのため、出力形式が多様。以下の順で試行:
1. `pytest` 出力パターン: `(\d+) passed` / `(\d+) failed` / `(\d+) skipped` を grep
2. `bats` 出力パターン: `# tests` / `# failures` を grep
3. どちらも取れない場合: exit code 0 = pass (件数 unknown) / 非 0 = fail (件数 unknown) と記録

---

### §2.C shell wrapper (cli/helix-refactor)

`cli/helix-recover` と同パターン:

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/helix-common.sh"

exec env PYTHONPATH="$HELIX_HOME${PYTHONPATH:+:$PYTHONPATH}" python3 -m cli.lib.refactor_engine "$@"
```

---

### §2.D テスト設計

#### pytest (cli/lib/tests/test_refactor_engine.py)

| # | テストケース | 観点 |
|---|---|---|
| T-01 | init: 対象存在 + テスト green → session 作成 OK | 正常系 |
| T-02 | init: 保護網テスト red → RefactorInitError / exit 1 | 異常系 |
| T-03 | init: 対象ファイル不在 → exit 2 | 異常系 |
| T-04 | check: baseline と現在が一致 → ok=True | 正常系 |
| T-05 | check: failed 増加 → ok=False, REGRESSION DETECTED | 異常系 |
| T-06 | check: session なし → exit 2 | 異常系 |
| T-07 | status: session あり → JSON / テキスト出力 | 正常系 |
| T-08 | status: session なし → exit 1 | 正常系 |
| T-09 | done: check ok → session close / JSON 削除 | 正常系 |
| T-10 | done: check fail → done 中止 / session 継続 | 異常系 |
| T-11 | done: --skip-final-check → check をスキップして close | 境界値 |
| T-12 | run_test_cmd: pytest 出力パース (passed/failed/skipped 件数抽出) | 単体 |
| T-13 | run_test_cmd: bats 出力パース | 単体 |
| T-14 | run_test_cmd: 不明フォーマット → exit code ベースで pass/fail 判定 | 境界値 |
| T-15 | RefactorSession: frozen dataclass / Literal 制約の実行時チェック | 型安全 |

#### bats (cli/tests/helix-refactor.bats)

> **P2-5**: bats artifact は `cli/tests/helix-refactor.bats` (既存 `cli/tests/` に統一)。
> Sprint .2a/.2b では `cli/helix-refactor` 直叩き、Sprint .4 の top-level smoke で `helix refactor` (router 経由) を確認する。

| # | テストケース | 観点 |
|---|---|---|
| B-01 | `cli/helix-refactor --help` → usage 出力 | smoke |
| B-02 | `cli/helix-refactor init` で session ファイル生成確認 | smoke |
| B-03 | `cli/helix-refactor status` で session 表示 | smoke |
| B-04 | `cli/helix-refactor check` で green 確認 | smoke |
| B-05 | `cli/helix-refactor done` で session ファイル削除 | smoke |
| B-06 | session なしで `cli/helix-refactor check` → exit 2 | 異常系 |

---

## §3 既存 CLI 責務分離

| CLI | 責務 | Refactor CLI との境界 |
|---|---|---|
| `helix route` | signal を検出し Reverse / Refactor / Recovery / Incident へ **提案ルーティング** | route は「Refactor モードを使え」と案内する側。route → refactor の接続は §8 参照 |
| `helix recover` | Recovery mode の診断・dump・PLAN 起票 (AI 暴走ガード) | Recover は AI 暴走を対象。Refactor は技術的負債の構造改善。対象が異なる |
| `helix plan` | kind=refactor PLAN の起票 | PLAN 起票は helix plan が担う。helix refactor は session 管理のみ |
| `helix sprint` | L4 スプリント全般の管理 | sprint は全 kind に横断。refactor は kind=refactor 専用の保護網 session 管理 |
| `helix test` | 全回帰テスト | refactor check のデフォルト test_cmd に使えるが、refactor CLI 内部では実行コマンド文字列を保持するだけ |
| `helix push` | 6 ゲート検証 + git push | step ごとの commit は手動 git / helix push。refactor CLI は wrap しない |

**境界の原則**:
- `helix refactor` = 「今 refactor session 中か」「保護網テストが緑か」を管理する **session 管理レイヤー**
- コード編集・commit・PLAN 起票は既存コマンドや手動操作に委譲し、refactor CLI がラップしない

**cross-cutting-mechanisms との位置づけ**:
本 CLI は cross-cutting-mechanisms.md が定義する横断機構 (debt / drift / recovery / learning) とは**別レイヤー**。
横断機構の `debt` 機構が「負債蓄積 → Refactor を案内」する役割を担い、本 CLI はその案内先として起動される。
`helix debt status` (横断機構) → threshold 超過 → `helix refactor init` (本 CLI) という接続フローが正規経路。

---

## §4 Sprint 分割

### Sprint .1: 設計 + tl-advisor (本 §)

**完了条件**: tl-advisor 第 1 ラウンド passed (または needs_revision 指摘を反映して再度 passed)

成果物:
- 本 PLAN draft (L7-cli-helix-refactor-implplan.md) — 本ファイル
- tl-advisor 第 1 ラウンド結果を本 PLAN §10 に記録

### Sprint .2a: テスト実装 (SE 委譲、HELIX TDD 原則：テスト先行)

> **P1-3 修正**: HELIX 全モード共通絶対原則「テスト → 実装」に従い、テスト実装を実装より先に行う。

**対象**: cli/lib/tests/test_refactor_engine.py (pytest 単体テスト)

**SE 委譲プロンプト要件**:
1. §2.D T-01〜T-15 を failing tests として先に実装する
2. `refactor_engine.py` がまだ存在しないため、`unittest.mock` / stub で import を通す
3. 全テストが「期待通り fail」する状態まで実装して SE は止まること
4. `python3 -m pytest cli/lib/tests/test_refactor_engine.py --collect-only` が通ること
5. commit 不要

**完了条件**: T-01〜T-15 が all collected + expected fail (ImportError なし)

> **注意**: bats (B-01〜B-06) は `cli/helix` router 登録が前提のため Sprint .2a ではなく .3 後半に分離する。
> .2a 段階の bats は `cli/helix-refactor` を直叩きするケース (B-02〜B-06 の直叩き版) のみ実装可能。

### Sprint .2b: 実装 (SE 委譲)

**対象**: cli/helix-refactor + cli/lib/refactor_engine.py

**SE 委譲プロンプト要件**:
1. cli/helix-recover / cli/lib/recovery_engine.py を参考実装として参照
2. §2.A subcommand 仕様 (init/check/status/done の exit code / 出力形式) に完全準拠
3. §2.B RefactorSession dataclass + frozen + slots + Literal 型 (新フィールド含む)
4. session state は `.helix/refactor-session.json` (HELIX_PROJECT_ROOT 配下)
5. **P1-5**: `.helix/refactor-session.json` の read-modify-write 全体を `cli/lib/lock_helper.py` の fcntl project scope lock で保護する (atomic write だけでは二重 init / check_count lost update を防げない)
6. `--test-cmd` は必須引数、省略時は `exit 2` を返す
7. `--skip-final-check` は実装しない。`--force --reason` のみ実装
8. `--drift-type` 受領時、code_smell / structural 以外は `exit 2: unsupported drift_type` を返す
9. `python3 -m py_compile` / `shellcheck` を実行して通ること
10. Sprint .2a の pytest T-01〜T-15 が全 PASS になること
11. commit 不要 (PM が検証後 commit)

**完了条件**: T-01〜T-15 全 PASS

### Sprint .3: テスト追加 + bats + smoke (SE 委譲)

**対象**: cli/lib/tests/test_refactor_engine.py (追加テスト) + cli/tests/helix-refactor.bats

> **P2-5**: bats test artifact は `cli/tests/helix-refactor.bats` に配置する (既存 `cli/tests/` ディレクトリに合わせる)。

**追加テスト** (§2.D B 相当の pytest):
| # | テストケース | 観点 |
|---|---|---|
| T-16 | init: --signal-id drift / --drift-type code_smell → routed_from / route_signal / drift_type が session に記録される | P1-2 |
| T-17 | init: --drift-type schema → exit 2: unsupported drift_type | P1-1 |
| T-18 | init: --test-cmd 省略 → exit 2: --test-cmd is required | P1-8 |
| T-19 | 並行 init: fcntl lock により二重 init が防がれる | P1-5 |
| T-20 | 並行 check: 同時実行で check_count lost update が発生しない | P1-5 |
| T-21 | 並行 done: 同時 done で session ファイルが二重削除されない | P1-5 |
| T-22 | check: baseline_total より total 減少 → REGRESSION DETECTED | P2-3 |
| T-23 | done --force --reason "emergency" → force_close_reason が audit ログに残る | P2-1 |
| T-24 | init --plan-id 省略 → trace_status=unlinked が記録され warning が出力 | P2-6 |

**bats (cli/tests/helix-refactor.bats)**:
| # | テストケース | 観点 |
|---|---|---|
| B-01 | `cli/helix-refactor --help` → usage 出力 (router 不要) | smoke |
| B-02 | `cli/helix-refactor init` で session ファイル生成確認 | smoke |
| B-03 | `cli/helix-refactor status` で session 表示 | smoke |
| B-04 | `cli/helix-refactor check` で green 確認 | smoke |
| B-05 | `cli/helix-refactor done` で session ファイル削除 | smoke |
| B-06 | session なしで `cli/helix-refactor check` → exit 2 | 異常系 |

**完了条件**: T-16〜T-24 (pytest) + B-01〜B-06 (bats direct) 全 PASS

### Sprint .4: docs 登録 + router smoke + commit

**対象**: cli/helix router 登録 + `cli/helix help` 確認 + docs/commands/index.md 追記

> **P1-4**: router 行追加と同 Sprint で `cli/helix help` 出力確認および `docs/commands/index.md` 追記を必ず同時に行う。`helix commands check` は route / help / docs 三者整合を見るため、三者が揃ってから実行する。

**router 登録** (cli/helix への追加行):
```bash
  refactor) exec "$SCRIPT_DIR/helix-refactor" "$@" ;;
```

**docs/commands/index.md** への追記 (§2. HELIX プロジェクト管理テーブルに追加):
```markdown
| `helix refactor` | Refactor mode の session 管理 (保護網確認・振る舞い不変 check) |
```

**top-level smoke test** (SE が実行):
```bash
helix refactor --help        # router 経由で help が出力されるか確認
helix commands check         # route / help / docs 三者整合確認
```

> **P1-4 補足**: `helix commands check` PASS には cli/helix への routing 行 + help 出力 + docs/commands/index.md の三者が揃っている必要がある。Sprint .3 の bats は `cli/helix-refactor` 直叩き、本 Sprint .4 は `helix refactor` (router 経由) を対象とする。

---

## §5 DoD

- [ ] automation-gate-map の gate-checks.yaml static チェック適用範囲外であることを確認済み (Refactor mode は workflow doc 固有 DoD で代替、gate-checks.yaml は Forward / Reverse モードが対象)
- [ ] `cli/helix-refactor` 実装済み、`bash -n` / `shellcheck` PASS
- [ ] `cli/lib/refactor_engine.py` 実装済み、`python3 -m py_compile` PASS
- [ ] fcntl project scope lock (`cli/lib/lock_helper.py`) による load-modify-save 保護を実装済み (P1-5)
- [ ] pytest T-01〜T-15 全 PASS (Sprint .2b)
- [ ] pytest T-16〜T-24 全 PASS (Sprint .3、lock 並行テスト含む)
- [ ] bats B-01〜B-06 全 PASS (`cli/tests/helix-refactor.bats`)
- [ ] cli/helix router に `refactor)` 行追加
- [ ] `cli/helix help` に `refactor` が表示されることを確認 (P1-4)
- [ ] docs/commands/index.md に `helix refactor` 行追加
- [ ] `helix commands check` PASS (route / help / docs 三者整合)
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認済み
- [ ] CLAUDE.md / HELIX_CORE.md の「dedicated CLI 未整備」警告文から `Refactor` 削除 (別 PR でも可)

---

## §6 受入条件

### 機械検証

```bash
# 構文チェック
bash -n cli/helix-refactor
shellcheck cli/helix-refactor
python3 -m py_compile cli/lib/refactor_engine.py

# 単体テスト
python3 -m pytest cli/lib/tests/test_refactor_engine.py -v --tb=short

# bats
bats cli/tests/helix-refactor.bats

# routing 確認
helix commands check
helix refactor --help
```

### 動作検証 (smoke)

```bash
# session 開始 → check → done の一連
helix refactor init --target cli/lib/skill_recommender.py --test-cmd "pytest cli/lib/tests/test_skill_recommender.py -q"
helix refactor status
helix refactor check
helix refactor done
```

### 全回帰

```bash
# 既存テスト影響なし確認
python3 -m pytest cli/lib/tests/ -q --tb=short
```

### ADR SoT 整合確認

- `--drift-type` 受付値が ADR-041 §Decision の Refactor 対象 2 種 (code_smell / structural) に限定されていること
- `recommended_command` の JSON parse が ADR-042 RecommendedCommandV1 schema に準拠していること (schema_version / command / args / safety フィールドの存在確認)

---

## §7 risk / mitigation

> **ADR SoT 参照**: drift_type 別ルーティングのリスクは ADR-041 §Consequences、recommended_command 機械契約のリスクは ADR-042 §Consequences を参照。

| # | リスク | 影響度 | mitigation |
|---|---|---|---|
| R-1 | `.helix/refactor-session.json` が複数プロセスで同時書き込まれる (helix lock と競合) | Medium | **P1-5**: atomic write (tempfile → rename) だけでは二重 init / check_count lost update / done 同時実行を防げない。`cli/lib/lock_helper.py` の project scope fcntl lock を load-modify-save 全体に必ず適用する。並行 init/check/done テスト (T-19〜T-21) で検証必須。 |
| R-2 | `test_cmd` が長時間実行のテスト (全回帰 530 秒) を指定された場合に check が毎回重い | Low | ドキュメントで「--test-cmd には対象モジュールのテストのみ指定を推奨」を明記。helix test は全回帰なので sprint exit 時に使う旨を案内 |
| R-3 | session 中に別 session を init しようとした場合の二重起動 | Medium | init 時に既存 `.helix/refactor-session.json` が存在すれば `exit 2: active session exists, run 'helix refactor status' or 'helix refactor done'` を返す |
| R-4 | bats テストで `.helix/refactor-session.json` が test 間で残留する | Low | bats の setup/teardown で session ファイルをクリーンアップ (cli/helix-recover bats のパターンを踏襲) |
| R-5 | `--test-cmd` に shell injection が可能な文字列が渡される | Medium | subprocess.run でシェル展開せず (`shell=False`)、shlex.split でコマンドをパース。README に「信頼できるコマンドのみ指定」と明記 |
| R-6 | drift_type 分類が ADR-041 SoT と乖離した場合の実装 drift | Low | `--drift-type` の受付値は ADR-041 §Decision の 7 種のみを真値とし、それ以外は `exit 2: unsupported drift_type` で明示拒否。ADR-041 改訂時は本 PLAN §8 の scope 記述のみ更新すれば表 copy が不要なため drift が発生しない。 |
| R-7 | recommended_command JSON schema が ADR-042 RecommendedCommandV1 と乖離する | Low | 本 PLAN は JSON parse する受領側のみ実装。出力側 (route_engine / PLAN C') が ADR-042 §Decision schema に従うことを PLAN C' のレビューで確認する。 |

---

## §8 V3 接続契約 (route → refactor)

### 入口 signal の定義

`helix route` が detect した signal を `helix refactor` へ接続する際の契約。`helix recover` の `signal_to_condition` と対称的に設計する。

**drift シグナルの分岐根拠 (detection-routing.md §検出→モードルーティング より)**:

detection-routing.md は「設計⇔実装 drift → Reverse(normalization)」を正規経路として定義する。
本 PLAN の `drift` signal を Refactor に接続するのは drift_type で細分化された結果。

> **drift_type 分岐契約** (本 PLAN scope 限定): **ADR-041 §Decision 参照**。
> drift_type の完全定義 (7 種) と各種ルーティング先は ADR-041 を SoT とする。本 PLAN に表を copy しない (PLAN 間 drift risk 回避)。
>
> 本 PLAN は `drift_type ∈ {code_smell, structural}` のみを Refactor 対象として受領する。
> - `schema / contract` は Reverse (normalization) が担当
> - `dependency_outdated / upgrade / config_drift` は Retrofit (L7-cli-helix-retrofit-impl) が担当
>
> route_engine の drift_type 7 種全対応拡張は **別 PLAN (L7-route-engine-drift-type-retrofit-ext)** に分離済み。本 PLAN では code_smell/structural→Refactor scope のみ実装する。

本 PLAN の §8 接続契約は drift_type ∈ {code_smell, structural} に限定する。
上位 signal `drift` 単独受領時は、refactor init より先に `helix route eval --signal drift`
を実行して drift_type を確定すること。

| signal_id | refactor への接続 | 理由 |
|---|---|---|
| `drift` (drift_type=code_smell) | `helix refactor init --target <drift-path> --drift-type code_smell` を案内 | コード品質劣化 drift → Refactor (振る舞い不変の構造改善) が対処 |
| `drift` (drift_type=structural) | `helix refactor init --target <drift-path> --drift-type structural` を案内 | 内部構造の乱れ → Refactor で整理 |
| `drift` (drift_type=schema/contract) | **Refactor 対象外 → Reverse (normalization) へ委譲** | 設計⇔実装乖離は Reverse 領域 (detection-routing.md 正規経路) |
| `drift` (drift_type=dependency_outdated/upgrade/config_drift) | **Refactor 対象外 → Retrofit へ委譲 (L7-route-engine-drift-type-retrofit-ext 後)** | Retrofit 領域。route_engine 拡張 PLAN 完遂まで現行どおり Reverse 残し |
| `debt_degradation` | `helix refactor init --target <debt-path> --from-debt-id <id>` を案内 | 技術的負債の悪化 → Refactor が直接の対処 |
| `runaway` | **Refactor 対象外 → recover へ委譲** | AI 暴走は Recovery で対処、Refactor ではない |
| `regression_dev` | **Refactor 対象外 → recover へ委譲** | デグレは振る舞い変化あり → Refactor (振る舞い不変) の前提と矛盾 |
| `regression_prod` | **Refactor 対象外 → Incident へ委譲** | 本番障害は Incident |

> **P1-7 修正**: `unknown_design → Refactor` は削除。設計不明の場合は既存動作・契約が不明のため保護網テストを整備できず、Refactor (振る舞い不変) の前提と矛盾する。`unknown_design` は `Reverse(code)` 固定 (detection-routing.md 正規経路) で既存コード・契約を復元してから Refactor を検討すること。Refactor 許可条件 (既存テストまたは golden master あり + 対象が内部構造に限定) の判定は別 carry。

**debt 横断機構との接続 (cross-cutting-mechanisms.md §4つの横断機構)**:

> **P1-6 修正**: `helix debt status` / threshold 超過の自動連携は現行 `cli/helix-debt` の `list/add/resolve` に存在しない (status/threshold サブコマンドが未実装)。この接続は **future (別 PLAN 依存)** とし、本 PLAN では直接参照しない。

現時点で実装可能な debt 接続は `--from-debt-id <id>` による手動指定に限定する:
```bash
# helix debt list で debt-id を確認
helix refactor init --target cli/lib/skill_recommender.py \
  --test-cmd "pytest cli/lib/tests/test_skill_recommender.py -q" \
  --from-debt-id debt-2026-001
```

`debt_degradation` signal は cross-cutting-mechanisms 由来であり、detection-routing の
「劣化（コード品質）= axis-01〜14 detector」と対応する。
signal 経由での自動接続 (`helix route` → `helix refactor`) は route_engine 接続時に確立する。

### route からの呼び出し形式 (refactor CLI 側の受け口)

`helix refactor init` は `--signal-id` / `--auto-routed-from` / `--drift-type` を受け付ける:

```bash
helix refactor init \
  --target <path> \
  --test-cmd "pytest <target-test> -q" \
  --signal-id drift \
  --drift-type code_smell \
  --auto-routed-from helix-route
```

内部動作: `--auto-routed-from` が付いている場合、session state に `routed_from` / `route_signal` / `drift_type` を記録する。これにより done 時のサマリに route 経緯が残る。

### 接続契約テーブル (route 側との双方向確認)

| route 出力フィールド | refactor init 引数 | 備考 |
|---|---|---|
| `signal_id` | `--signal-id` | drift (code_smell/structural のみ) / debt_degradation のみ受け付け。unknown_design は Refactor 対象外 (P1-7) |
| `drift_type` | `--drift-type` | code_smell / structural のみ受付。schema/contract/dependency_outdated/upgrade/config_drift は exit 2 |
| `target_path` | `--target` | route が検出した対象ファイル/ディレクトリ |
| `debt_id` | `--from-debt-id` | debt 機構連携時のみ。helix debt list から id を取得 |
| `cli_hint` 値 | `helix refactor init ...` のコマンド文字列 | route は hint を表示するだけ、自動実行しない |

### recommended_command 契約 (ADR-042 RecommendedCommandV1 schema)

route_engine (PLAN C') が本 PLAN B へ渡す `recommended_command` は JSON object 形式で出力する。詳細は **ADR-042 §Decision** を SoT とする。

```json
{
  "schema_version": "v1",
  "command": "helix plan draft",
  "args": {
    "kind": "refactor",
    "drift_type": "code_smell",
    "signal_id": "drift",
    "slug": "<auto>"
  },
  "safety": {
    "auto_apply": false,
    "requires_human_approval": false
  }
}
```

`drift_type` は `"code_smell"` または `"structural"` のいずれか。本 PLAN B は JSON parse して `--drift-type` 引数として `helix refactor init` に渡す受領側実装とする。

### 接続コマンド統一 (ADR-042 §Decision)

- route_engine は `helix plan draft --kind refactor --drift-type ...` を `recommended_command` として返す
- 各 mode CLI (`helix refactor init`) は **PLAN 起票後の手動着手** に限定する
- route_engine → 直接 `helix refactor init` の自動連携は **行わない** (PLAN-first 原則)
- 本 PLAN B / PLAN C / PLAN C' の §V3 (接続契約) は本 ADR SoT 参照とし、recommended_command 形式の表 copy は drift risk のため禁止する

---

## §9 関連 doc / 関連 PLAN

### 正本 / 設計

- [HELIX-workflows/helix-process/refactor-workflow.md](../../../HELIX-workflows/helix-process/refactor-workflow.md) — 本 PLAN の parent_design
- [HELIX-workflows/helix-process/deviation-plan-map.md](../../../HELIX-workflows/helix-process/deviation-plan-map.md) — kind 別の逸脱判定 map
- [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md) — drift / 劣化 signal 分岐根拠 (§8 CRITICAL 1 の証拠、schema/contract → Reverse / code_smell/structural → Refactor)
- [HELIX-workflows/helix-process/cross-cutting-mechanisms.md](../../../HELIX-workflows/helix-process/cross-cutting-mechanisms.md) — debt 横断機構との接続 (debt_degradation signal の由来)
- [HELIX-workflows/helix-process/automation-gate-map.md](../../../HELIX-workflows/helix-process/automation-gate-map.md) — Refactor mode の gate 不在確認 (workflow doc 固有 DoD で代替、§5 DoD 参照)

### 参考実装 (同パターン CLI)

- [docs/plans/L7/L7-helix-recover-implplan.md](./L7-helix-recover-implplan.md) — V3 接続契約 + 設計パターンの先行例
- [docs/plans/L7/L7-helix-route-implplan.md](./L7-helix-route-implplan.md) — route 側の signal 設計

### 登録先

- [cli/helix](../../../cli/helix) — router (Sprint .4 で追加)
- [docs/commands/index.md](../../../docs/commands/index.md) — CLI 索引 (Sprint .4 で追加)

### 依存 PLAN

- `L7-helix-route-implplan` (requires): route の signal_id 定義が確定していること
- `L7-route-engine-drift-type-retrofit-ext` (requires): drift_type 7 種の route_engine 拡張。本 PLAN の drift_type=code_smell/structural→Refactor 接続は同 PLAN 完遂後に有効化される (P1-1 carry)
- `L7-helix-workflows-parent-acceptedplan` (parent): HELIX-workflows V2 正本化

---

## §10 carry / 残課題

| # | 内容 | 優先度 | 状態 |
|---|---|---|---|
| C-01 | tl-advisor 第 1 ラウンド: needs_revision → 本 §10 revision 反映済 (P1 8 件 + P2 一部) | P1 | ✅ revised |
| C-02 | tl-advisor 第 2 ラウンド実施 (revision 反映後に再度 adversarial check、SE 委譲前に passed 確認) | P1 | □ pending |
| C-03 | CLAUDE.md / HELIX_CORE.md の「dedicated CLI 未整備」警告から `Refactor` を削除 (commit 後に別 PR か本 PR に含める) | P2 | □ pending |
| C-04 | `helix retrofit` (Retrofit mode) / `helix recovery` (Recovery mode) の dedicated CLI 未整備 carry は本 PLAN の範囲外。別 PLAN で解消 | P3 | □別 PLAN |
| C-05 | drift_type=dependency_outdated/upgrade/config_drift → Retrofit のルーティング有効化は `L7-route-engine-drift-type-retrofit-ext` 完遂後 | P1 | □ 別 PLAN 待ち |
| C-06 | `helix debt status` / threshold 超過自動連携 (P1-6) は helix-debt サブコマンド拡張後の future。現在は --from-debt-id 手動指定に限定 | P2 | □ 別 PLAN 待ち |
| C-07 | unknown_design → Refactor 接続は Reverse(code) で契約復元後に既存テスト整備を前提とした別 carry として検討 | P3 | □ carry |
| C-08 | P2-2: test_cmd の shlex.split + shell=False 方針では pipe/env/redirect 不可。代替として --test-arg 配列または trusted shell opt-in の実装は別 PR 候補 | P3 | □ carry |
| C-09 | `helix route suggest --signal drift --drift-type code_smell --format json` の `recommended_command.args.drift_type` exact match は route_engine 拡張 (C' 担当) の rerun で最終確認する。本 PLAN は受け口 (`helix refactor`) 実装と router/help/docs 登録までを完了 | P1 | □ C' rerun 待ち |
| C-NEW | **R3 revision (ADR SoT 参照置換) 記録**: §8 drift_type 7 種表 → ADR-041 §Decision 参照に置換 (行削除 -11 行 + reference 追記 +10 行)。recommended_command JSON object 形式 + 接続コマンド統一 (ADR-042 §Decision) を §8 末尾に追記 (+28 行)。frontmatter dependencies.requires に ADR-041/042 追加、parent_design を list 化して同追加、related_docs に同追加。本 R3 変更一覧は Phase 3 tl-advisor R3 round confirm 対象。 | P1 | ✅ R3 revised |
