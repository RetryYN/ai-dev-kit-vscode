---
plan_id: L7-helix-recover-rollback-applyplan
title: "L7-helix-recover-rollback-applyplan: helix recover rollback --apply 実装 — destructive operation 5 重ガード + audit log 永続化"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-helix-recover-implplan.md
pairs_test_design:
  - docs/plans/L7/L7-helix-recover-rollback-applyplan.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — スコープ確認・人間承認フロー設計レビュー・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — destructive operation 設計 adversarial check (git reset 責務分離・audit schema・confirm prompt UX・cutover_orchestrator 非連携確認)"
  - role: security
    slot_label: "Security — destructive operation 5 重ガード全件セキュリティレビュー (ガード漏れ / audit log tamper-resistance / confirm bypass リスク)"
  - role: se
    slot_label: "SE — cli/helix-recover rollback --apply 実装 + recovery_engine.py apply_rollback() + helix.db v36 migration + test 追加"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 整合チェック・parent_design との仕様連続性確認"
generates:
  - artifact_path: cli/helix-recover
    artifact_type: cli_extension
  - artifact_path: cli/lib/recovery_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/migrations/v36_rollback_audit.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_recovery_engine.py
    artifact_type: test
  - artifact_path: cli/tests/helix-recover.bats
    artifact_type: test
  - artifact_path: docs/commands/index.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires:
    - L7-helix-recover-implplan
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/recovery-workflow.md
  - cli/lib/recovery_engine.py
  - cli/lib/recovery_plan_check.py
  - cli/lib/helix_db.py
  - cli/lib/cutover_orchestrator.py
  - cli/lib/migrations/v35_plan_registry.py
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **parent_design**: [docs/plans/L7/L7-helix-recover-implplan.md](L7-helix-recover-implplan.md) (v3、commit 904c4f6 で recover 実装完遂)
> **本 PLAN の対象**: `helix recover rollback --apply` の実装。parent_design v3 で「rollback は dry-run のみ、`--apply` は exit 2 で error」と意図的に凍結された destructive operation を、**後段 PLAN として安全ガードと共に実装する**。

### parent_design 凍結経緯

L7-helix-recover-implplan (v3) §2.A の tl-advisor P1-1 指摘対応:

> "rollback 責務が危険 (実 git reset と誤解の余地) → `rollback` を **dry-run / 手順提示のみ** に明示限定、実 git reset / DB rollback は別 PLAN"

現状の `cli/lib/recovery_engine.py` における rollback 実装 (抜粋):

```python
# recovery_engine.py line 709-712 (現状)
if args.apply:
    print("use 'helix recover rollback --dry-run' first, then run git/db commands manually", file=sys.stderr)
    sys.exit(2)
```

本 PLAN はこの凍結を解除し、`apply_rollback()` method を実装する。

### cutover_orchestrator 非連携の理由 (事前調査確認)

`cli/lib/cutover_orchestrator.py` は PLAN-084 SEP cutover gate 5 専用 (`docs/v2/L3-detailed-design/D-API/D-API-SEP-cutover-gate5.md`)。Recovery mode の rollback とは設計責務が異なり、本 PLAN では連携しない。rollback の orchestration は本 PLAN 内に最小実装する。

### destructive operation リスク分類

| 操作 | リスクレベル | 不可逆性 | ガード方式 |
|------|------------|---------|----------|
| `git reset --hard <SHA>` | Critical | 高 (stash なしでは復元不可) | 5 重 |
| `helix.db rollback_audit` 書き込み | Low | なし (append-only) | なし |
| `helix.db` 状態ロールバック | Medium | 中 (helix.db は再生成可) | 5 重に含む |

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|------|---------|------|------|
| 1 | parent_design v3 rollback dry-run 仕様 + 現状 recovery_engine.py Read | PM | ✅ done |
| 2 | cutover_orchestrator 責務分離確認 (非連携確定) | PM | ✅ done |
| 3 | helix.db 既存 migration 体系確認 (v35 まで確認済) | PM | ✅ done |
| 4 | 人間承認ガード 5 重設計 (§2.A) | PM | ✅ done |
| 5 | apply_rollback() method 設計 + migration v36 schema 設計 (§2.B〜§2.C) | PM | ✅ done |
| 6 | テスト設計 6 ケース (§2.D) | PM | ✅ done |
| 7 | tl-advisor adversarial check | PM → TL | pending |
| 8 | security adversarial check | PM → Security | pending |
| 9 | SE 委譲 (cli/helix-recover + recovery_engine.py + migration + test) | PM → SE | pending |
| 10 | 機械検証 (pytest + bats + py_compile) | PM | pending |
| 11 | interactive confirm prompt UI 手動確認 | PM | pending |
| 12 | pmo-sonnet 4 artifact trace 整合チェック | PM → PMO | pending |
| 13 | commit + push | PM | pending |

---

## §2 実装計画

### §2.A 人間承認ガード 5 重設計

destructive operation (`git reset --hard`) を安全に実行するため、以下 5 つのガードを全件通過しない限り実行不可とする。**各ガードは独立して機能し、1 つでも失敗した場合は即時 exit 2**。

#### G1: `--apply` 明示必須

```
helix recover rollback              # exit 2: "--apply required"
helix recover rollback --dry-run    # OK: dry-run (既存動作維持)
helix recover rollback --apply ...  # ガード G2 へ
```

- 現状の exit 2 `"use 'helix recover rollback --dry-run' first"` をより明確なエラーメッセージに差し替える
- dry-run / apply の責務分離を維持し、`args.apply` フラグによって分岐する

#### G2: `--reopen-point <SHA>` 明示必須

```
helix recover rollback --apply                         # exit 2: "--reopen-point required"
helix recover rollback --apply --reopen-point HEAD~3   # ガード G3 へ
```

- default 値を持たせない (任意 default は誤操作リスク)
- SHA は `git rev-parse --verify <SHA>` で存在検証する (不正値 exit 2)

#### G3: interactive confirm prompt

非対話モードの場合は `--confirm-blind` フラグ + audit log 記録でのみ許可。

```
[!] WARNING: This is a destructive operation.
    git reset --hard will be run to: <SHA>
    helix.db state will be rolled back.
    This action cannot be undone without manual git reflog recovery.

Type 'YES I UNDERSTAND' to proceed (Ctrl-C to cancel):
```

- stdin が TTY でない場合かつ `--confirm-blind` 未指定 → exit 2 (CI 誤実行防止)
- `--confirm-blind` 指定時は audit log に `confirm_method: non_interactive` を記録する

#### G4: 事前 recovery-log.md 生成必須

```
helix recover rollback --apply --reopen-point HEAD~3
# 内部で recovery-log.md の存在確認
# -> 未生成なら exit 2: "run 'helix recover plan' first to generate recovery-log.md"
```

- `cli/lib/recovery_plan_check.py` の `REQUIRED_TEMPLATE_SECTIONS` 7 セクション全件検証
- recovery-log の `reopen_point:` 記載値と `--reopen-point` 引数の SHA が一致しない場合も exit 2

#### G5: audit log 永続化 (commit-before-execute)

- `apply_rollback()` は実行前に helix.db `rollback_audit` table へ行を INSERT する (pre-commit)
- INSERT 失敗時は rollback 実行を中止する (fail-close)
- INSERT 成功後に git reset を実行、結果 (success / failure) を UPDATE で反映する

```python
# 実行シーケンス:
# 1. rollback_audit INSERT (pre) → INSERT 失敗なら exit 1
# 2. git reset --hard <SHA> 実行
# 3. rollback_audit UPDATE result=success|failure
# 4. result=failure なら stderr + exit 1
```

---

### §2.B cutover_orchestrator 非連携 + 最小 orchestration

`cli/lib/cutover_orchestrator.py` は SEP cutover gate 5 専用であり、Recovery rollback には連携しない。本 PLAN では `recovery_engine.py` 内に以下 3 step の最小 orchestration を直接実装する:

1. **preflight step**: G1〜G4 ガード全件通過確認
2. **execute step**: G5 pre-commit + git reset 実行
3. **verify step**: `git rev-parse HEAD` で期待 SHA 到達を確認 + audit log result 更新

orchestration は `apply_rollback()` の内部シーケンスとして実装し、外部 orchestrator への依存は持たない。

---

### §2.C 実装詳細

#### cli/helix-recover 変更 (Bash)

```bash
# rollback subcommand 引数 parser 拡張 (rollback_cmd.add_argument 追記)
rollback_cmd.add_argument("--apply", action="store_true")
rollback_cmd.add_argument("--reopen-point", default=None)  # default=None で必須化
rollback_cmd.add_argument("--confirm-blind", action="store_true")

# rollback ハンドラ書き換え
if args.subcommand == "rollback":
    if args.apply:
        engine.apply_rollback(
            reopen_point=args.reopen_point,
            confirm_blind=getattr(args, "confirm_blind", False),
        )
    else:
        # 既存 dry-run 動作維持
        payload = engine.suggest_rollback_point()
        ...
```

#### recovery_engine.py 変更 (Python)

`RecoveryEngine` クラスに `apply_rollback()` method を追加:

```python
def apply_rollback(
    self,
    reopen_point: str | None,
    confirm_blind: bool = False,
) -> None:
    """G1-G5 ガード全件通過後に git reset --hard を実行する。"""
    # G1: --apply は呼び出し元で確認済みのため skip
    # G2: --reopen-point 存在検証
    if not reopen_point:
        _die("--reopen-point is required for --apply")
    sha = self._resolve_sha(reopen_point)  # git rev-parse --verify

    # G3: interactive confirm
    self._interactive_confirm(sha, confirm_blind)

    # G4: recovery-log.md 存在 + SHA 整合検証
    self._verify_recovery_log(reopen_point=sha)

    # G5: audit log pre-commit + execute + result update
    audit_id = self._pre_commit_audit(sha, confirm_blind)
    result = self._execute_git_reset(sha)
    self._update_audit_result(audit_id, result)

    if not result["success"]:
        _die(f"git reset failed: {result['error']}")
```

補助 method 一覧:

| method | 責務 |
|--------|------|
| `_resolve_sha(ref)` | `git rev-parse --verify <ref>` で SHA 正規化、失敗は exit 2 |
| `_interactive_confirm(sha, confirm_blind)` | TTY 判定 + prompt 表示 + 入力検証 |
| `_verify_recovery_log(reopen_point)` | recovery_plan_check.py 7 セクション + SHA 整合 |
| `_pre_commit_audit(sha, confirm_blind)` | rollback_audit INSERT、失敗は exit 1 |
| `_execute_git_reset(sha)` | subprocess git reset --hard、結果 dict 返却 |
| `_update_audit_result(audit_id, result)` | rollback_audit UPDATE |

#### cli/lib/migrations/v36_rollback_audit.py (新規)

helix.db に `rollback_audit` table を追加する migration module。既存 migration (v35_plan_registry.py) の additive schema パターンに準拠する。

```python
"""v36: rollback_audit table — helix recover rollback --apply の実行ログ。"""

SCHEMA_VERSION = 36

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS rollback_audit (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sha         TEXT    NOT NULL,
    triggered_at TEXT   NOT NULL,   -- ISO8601 UTC
    confirm_method TEXT NOT NULL,   -- 'interactive' | 'non_interactive'
    recovery_log_path TEXT,
    result      TEXT,               -- NULL (pre) | 'success' | 'failure'
    result_detail TEXT,
    session_id  TEXT
);
"""

def ensure_v36_additive_schema(conn) -> None:
    conn.execute(CREATE_SQL)
    conn.commit()
```

`helix_db.py` の migration chain に v36 を追記する (既存 ensure_schema パターンに従う)。

---

### §2.D テスト設計 (6 unit test + 2 bats)

テスト設計は本 PLAN (pairs_test_design: self) に記載。4 artifact 双方向 trace:

- 設計 (§2.A〜§2.C) → 本 §2.D テスト設計
- テスト設計 → `cli/lib/tests/test_recovery_engine.py` (テストコード)
- 設計 → `cli/lib/recovery_engine.py` (実装コード)

#### unit test 6 件 (`cli/lib/tests/test_recovery_engine.py` 追記)

| テスト ID | 検証内容 | 期待動作 |
|-----------|---------|---------|
| `test_apply_requires_reopen_point` | `--reopen-point` なしで `apply_rollback()` 呼び出し | `SystemExit(2)` 発生 |
| `test_apply_rejects_invalid_sha` | 存在しない ref を `--reopen-point` に指定 | `SystemExit(2)` 発生 |
| `test_apply_requires_confirm_in_tty` | TTY なし + `--confirm-blind` 未指定 | `SystemExit(2)` 発生 |
| `test_apply_requires_recovery_log` | recovery-log.md 未生成で `apply_rollback()` 呼び出し | `SystemExit(2)` 発生 |
| `test_apply_audit_log_written` | 全 G 通過後 (subprocess mock) に rollback_audit row 挿入確認 | `rollback_audit` に 1 row、result が `success` |
| `test_dry_run_does_not_call_subprocess` | dry-run 時に `_execute_git_reset` が呼ばれない | subprocess モック呼び出し回数 = 0 |

**実装上の注意**: destructive な `git reset --hard` は subprocess mock 必須。`unittest.mock.patch("subprocess.run")` で subprocess を差し替え、実際の git 操作が走らないことを確認する。

#### bats test 2 件 (`cli/tests/helix-recover.bats` 追記)

| テスト ID | 検証内容 | 期待動作 |
|-----------|---------|---------|
| `rollback_dry_run_vs_apply_distinction` | `--apply` なし → dry-run 出力、`--apply` あり → confirm prompt または exit 2 (G2 未満) | 出力内容で分岐確認 |
| `rollback_apply_without_reopen_exits_2` | `--apply` のみで `--reopen-point` なし | exit 2 確認 |

---

### §2.E 既存 dry-run との責務分離確認

| 観点 | dry-run (既存) | apply (本 PLAN) |
|------|--------------|----------------|
| 実行対象 | `suggest_rollback_point()` — git log 解析のみ | `apply_rollback()` — git reset + helix.db 書き込み |
| 副作用 | なし | git HEAD 移動 + rollback_audit INSERT |
| subprocess | なし | git rev-parse + git reset --hard |
| ガード | なし | G1〜G5 全件 |
| 出力 | JSON (rollback_point / rationale) | 標準出力 + audit log |

---

## §3 成果物一覧

| 成果物 | 種別 | 変更種類 |
|--------|------|---------|
| `cli/helix-recover` | cli_extension | 修正 (rollback --apply 引数 parser + ハンドラ分岐) |
| `cli/lib/recovery_engine.py` | python_module | 修正 (apply_rollback() + 補助 5 method 追加) |
| `cli/lib/migrations/v36_rollback_audit.py` | python_module | 新規 |
| `cli/lib/helix_db.py` | python_module | 修正 (v36 migration chain 追記) |
| `cli/lib/tests/test_recovery_engine.py` | test | 修正 (6 unit test 追加) |
| `cli/tests/helix-recover.bats` | test | 修正 (2 bats 追加) |
| `docs/commands/index.md` | documentation | 修正 (rollback --apply オプション説明追記) |

---

## §4 受入条件 / DoD

### 機械検証 (mandatory)

- `python3 -m py_compile cli/lib/recovery_engine.py cli/lib/migrations/v36_rollback_audit.py` → 0 errors
- `pytest cli/lib/tests/test_recovery_engine.py -v` → 全 PASS (新規 6 + 既存 15 以上)
- `bats cli/tests/helix-recover.bats` → 全 PASS (新規 2 + 既存 6 以上)
- `helix plan lint --v5 docs/plans/L7/L7-helix-recover-rollback-applyplan.md` → warnings 0

### 機能確認 (手動)

- `helix recover rollback --apply --reopen-point HEAD~1` でインタラクティブ confirm prompt が表示される
- `YES I UNDERSTAND` 入力で git reset が実行され、`git rev-parse HEAD` が期待 SHA と一致する
- `rollback_audit` table に result=success の行が追加される (`sqlite3 .helix/helix.db "SELECT * FROM rollback_audit;"`)
- `helix recover rollback --apply` のみで exit 2 が返る (`echo $?` で確認)

### セキュリティ確認 (security adversarial check)

- G1〜G5 ガード全件が独立して機能すること (各テストで個別検証済)
- `--confirm-blind` 指定時に audit log の `confirm_method = 'non_interactive'` が記録されること
- TTY なし + `--confirm-blind` なしで exit 2 になること (CI 誤実行防止)
- rollback_audit の pre-commit INSERT 失敗時に git reset が実行されないこと

### ドキュメント整合 (4 artifact trace)

- `docs/commands/index.md` の rollback サブコマンドに `--apply` / `--reopen-point` / `--confirm-blind` オプション説明追記
- 本 PLAN §2.D テスト設計 → `test_recovery_engine.py` の対応確認 (pairs_test_design 自己参照)

---

## §5 関連 PLAN / docs

| 参照先 | 種別 | 関係 |
|--------|------|------|
| `docs/plans/L7/L7-helix-recover-implplan.md` | parent_design | rollback dry-run 凍結の発生源、本 PLAN の前提 |
| `HELIX-workflows/helix-process/recovery-workflow.md` | design | Recovery mode 全体設計の正本 |
| `cli/lib/recovery_plan_check.py` | impl | G4 で参照する 7 セクション検証ロジック |
| `cli/lib/cutover_orchestrator.py` | impl | 非連携確認済 (SEP cutover gate 5 専用) |
| `cli/lib/migrations/v35_plan_registry.py` | impl | v36 migration の参照パターン |
| `cli/lib/helix_db.py` | impl | migration chain 追記対象 |

---

## §6 後続 PLAN 候補

| 候補 | 概要 | 優先度 |
|------|------|--------|
| rollback-history viewer | `helix recover rollback-history` で rollback_audit 一覧表示 | P3 |
| non-interactive rollback (webhook 連携) | helix-route dispatch 経由で人間承認 UI を webhook に外出し | P2 |
| partial rollback | file 単位 / commit range 単位の rollback | P3 |
| helix.db rollback scope 拡張 | rollback_audit に helix.db テーブル別スナップショットを保持 | P2 |

---

## §7 リスク / 緩和策

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| git reset --hard による作業ロスト | Critical | G3 confirm prompt + G4 recovery-log.md 事前必須。git reflog を案内メッセージに含める |
| rollback_audit INSERT 直後の crash (git reset 未完) | Medium | pre-commit INSERT → result=NULL のままの行が残る。次回起動時に `result IS NULL AND triggered_at < now()-5m` を stale として警告 |
| confirm prompt のバイパス (`echo YES I UNDERSTAND \| helix recover rollback --apply`) | Medium | stdin が pipe の場合は TTY 判定 false → `--confirm-blind` フラグ必須 + audit log に記録。CI での意図しない bypass を防止 |
| v36 migration の既存 helix.db との衝突 | Low | `CREATE TABLE IF NOT EXISTS` で additive schema 維持。migration は idempotent |
| `--reopen-point` に誤 ref 指定 | Medium | `git rev-parse --verify` で事前検証 + 正規 SHA を confirm prompt に表示して二重確認 |
