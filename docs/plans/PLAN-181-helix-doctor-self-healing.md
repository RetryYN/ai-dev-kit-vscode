---
plan_id: PLAN-181
title: "PLAN-181: helix doctor self-healing framework (auto-recovery on fail)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・audit log 仕様チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — auto_fix_handler registry 設計・safe/destructive 判定基準・audit log schema review"
  - role: se
    slot_label: "SE — auto_fix_handler registry 実装・helix doctor --auto-fix CLI 実装・audit log 書き込み実装"
  - role: qa
    slot_label: "QA — auto-fix fixture test 全ケース検証・destructive 禁止ガード確認"
generates:
  - artifact_type: python_module
    artifact_path: cli/lib/doctor_auto_fix.py
  - artifact_type: cli_extension
    artifact_path: cli/helix-doctor
  - artifact_type: test
    artifact_path: cli/lib/tests/test_doctor_auto_fix.py
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-181-helix-doctor-self-healing.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-050-helix-doctor-self-healing-decision.md
dependencies:
  parent: null
  requires: []
  blocks: []
related_plans:
  - PLAN-168 (drift auto-fix proposal — 設計方針の参照元)
  - PLAN-110 (helix doctor warn 漸減 framework — doctor check 改善との共存)
related_adr:
  - ADR-064
---

# PLAN-181: helix doctor self-healing framework

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-050** で凍結 (起票予定):

- `auto_fix_handler` registry 採用判断 (check 別 handler を dict で管理する設計選択)
- safe / destructive 判定基準の確定 (安全な auto-fix の定義と禁止範囲の境界)
- audit log 永続化方針 (helix.db への記録 vs 独立ファイル)
- `helix doctor --auto-fix` flag の単一エントリポイント設計
- P0 guard: destructive 操作は auto-fix 対象外、人間確認必須

## 1. 目的

`helix doctor` が fail / warn を報告した際、現状は手動修正が必要。本 PLAN は **safe な auto-recovery を framework 化** し、開発者の修正コストを削減する。

| 課題 | 症状 | 解決方針 |
|---|---|---|
| stale lock 残存 | `.helix/*.lock` が process 終了後も残り doctor fail | auto-release handler |
| broken symlink | `skills/` 配下の symlink が dangling で doctor warn | symlink 再作成 handler |
| orphan agent slot | helix.db に status=active のまま残る slot が doctor warn | bulk cancel handler |
| ADR index drift | `docs/adr/index.md` が実 ADR file と不整合 | index regenerate handler |

**対象外 (destructive 禁止)**:
- DB レコードの物理削除
- git history 改変
- 設計 doc 内容の自動書き換え

## 2. 業界 standard 参照 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (auto_fix_handler registry) を含むため PLAN-087 ガード対象。

| Query | 出典 | 抽出した知見 |
|---|---|---|
| "self-healing infrastructure auto-fix registry handler 2026" | https://martinfowler.com/bliki/SelfHealingSystem.html + SRE Book §17 | safe の定義: 「観測可能な副作用ゼロ + audit trail 必須」。idempotent のみでは不充分 |
| "health check auto remediation safe destructive boundary python 2026" | https://docs.python.org/3/library/shutil.html + pytest health-check pattern | dry-run 先行 → apply の二段階が community 標準。handler registry は `{name: fn}` dict で管理 |
| "helix doctor CLI check registry plugin pattern 2026" | HELIX PLAN-087 / PLAN-110 / PLAN-168 | PLAN-110 / PLAN-168 が先行。本 PLAN は handler registry を共通基盤として追加し両 PLAN と共存 |

## 3. 設計方針

### 3.1 auto_fix_handler registry

```python
# cli/lib/doctor_auto_fix.py
AUTO_FIX_REGISTRY: dict[str, Callable[[bool], FixResult]] = {
    "stale_lock":        fix_stale_locks,
    "broken_symlink":    fix_broken_symlinks,
    "orphan_agent_slot": fix_orphan_agent_slots,
    "adr_index_drift":   fix_adr_index_drift,
}

@dataclass
class FixResult:
    check_name: str
    status: str        # "fixed" | "skipped" | "error"
    affected: list[str]
    dry_run: bool
    message: str
```

### 3.2 safe / destructive 判定基準

| 操作 | 分類 | 理由 |
|---|---|---|
| `.helix/*.lock` 削除 (stale 判定後) | safe | process 終了確認済み + lock は再生成可能 |
| dangling symlink 削除 + 再作成 | safe | symlink 先 file は無変更、dangling = 実害なし |
| agent slot status を cancelled に更新 | safe | DB soft-delete 相当、物理削除なし |
| ADR index.md 再生成 | safe | 既存 ADR file 無変更、index のみ更新 |
| DB レコード物理削除 | **destructive** | auto-fix 禁止 |
| git commit / revert | **destructive** | auto-fix 禁止 |
| 設計 doc 内容書き換え | **destructive** | auto-fix 禁止 |

**safe の定義**: 以下 3 条件 AND
1. 冪等性: 複数回適用しても最終状態が同一
2. 可逆性: 元の状態に戻す手順が存在する
3. 観測副作用ゼロ: 別プロセス・別ファイルへの意図しない影響なし

### 3.3 `helix doctor --auto-fix` フロー

```
helix doctor --auto-fix [--dry-run] [--check NAMES]
  ↓
  1. helix doctor (通常実行) で fail/warn を収集
  ↓
  2. 各 fail/warn に対して AUTO_FIX_REGISTRY に handler 存在確認
     - handler 不在 → skip (手動対応必要として報告)
  ↓
  3. --dry-run フラグ
     - True  → handler を dry_run=True で呼び出し、変更内容をレポートのみ (適用なし)
     - False → handler を dry_run=False で呼び出し、実際に修正
  ↓
  4. FixResult を audit log に記録
  ↓
  5. 再度 helix doctor 実行 → fix 後の pass/fail/warn カウントを表示
```

### 3.4 audit log スキーマ

```sql
-- helix.db migration (追加)
CREATE TABLE IF NOT EXISTS doctor_auto_fix_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at     TEXT    NOT NULL,  -- ISO 8601 UTC
    check_name TEXT    NOT NULL,
    status     TEXT    NOT NULL,  -- "fixed" | "skipped" | "error"
    dry_run    INTEGER NOT NULL,  -- 0=applied, 1=dry-run
    affected   TEXT,              -- JSON array
    message    TEXT,
    session_id TEXT
);
```

### 3.5 P0 guard (CRITICAL)

- `--auto-fix` は safe handler のみ実行。destructive 操作は handler を登録しない
- `--dry-run` は default 推奨。CI / 自動実行では `--dry-run` を強制するオプション `HELIX_DOCTOR_AUTO_FIX_DRY_RUN_ONLY=1` を用意
- audit log への記録は apply / dry-run の両方で必須 (証跡なしの auto-fix 禁止)

## 4. 実装計画

### Sprint .1: doctor_auto_fix.py skeleton + stale_lock handler (Codex se)

**対象**: `cli/lib/doctor_auto_fix.py` (新規)。`FixResult` dataclass + `AUTO_FIX_REGISTRY` dict + `fix_stale_locks` + `run_auto_fix` dispatcher。
mandatory: `python3 -m py_compile cli/lib/doctor_auto_fix.py` PASS

### Sprint .2: 残 3 handler + audit log (Codex se)

**対象**: `doctor_auto_fix.py` 拡張 + `helix_db.py` migration 追加。`fix_broken_symlinks` / `fix_orphan_agent_slots` / `fix_adr_index_drift` + `write_audit_log` → helix.db INSERT。
mandatory: `py_compile` 両 file PASS

### Sprint .3: `helix doctor --auto-fix` CLI 統合 (Codex se)

**対象**: `cli/helix-doctor` (既存 CLI に `--auto-fix` / `--dry-run` / `--check NAMES` flag 追加)。fix 前後の doctor カウント diff 表示。
mandatory: `bash -n cli/helix-doctor` PASS + `--help` に `--auto-fix` 表示確認

### Sprint .4: pytest fixture test 全ケース (Codex qa)

**対象ファイル**: `cli/lib/tests/test_doctor_auto_fix.py` (新規)

テストケース:

| ケース | 内容 |
|---|---|
| T1-001 | stale lock file 存在 + process なし → dry_run=True: 削除内容をレポート、実際には削除なし |
| T1-002 | stale lock file 存在 + process なし → dry_run=False: 削除実施、status=fixed |
| T1-003 | lock file に対応 process が active → skip (safe 判定 false)、status=skipped |
| T2-001 | dangling symlink 存在 → dry_run=True: 再作成内容をレポート |
| T2-002 | dangling symlink 存在 → dry_run=False: 削除+再作成、status=fixed |
| T3-001 | orphan agent slot (status=active, process なし) → bulk cancel 対象にリスト |
| T3-002 | orphan agent slot → dry_run=False: cancelled に更新、audit log に記録 |
| T4-001 | ADR index drift → dry_run=True: 差分レポート |
| T4-002 | ADR index drift → dry_run=False: index.md 再生成、status=fixed |
| T5-001 | destructive 操作 (DB 物理削除) → handler 未登録 → skip、エラーなし |
| T5-002 | audit log 書き込み → helix.db に INSERT 確認、affected JSON 配列正常 |
| T6-001 | `HELIX_DOCTOR_AUTO_FIX_DRY_RUN_ONLY=1` → dry_run=False 指定でも dry_run=True で実行 |

mandatory in sprint:
- `python3 -m pytest cli/lib/tests/test_doctor_auto_fix.py -v` 全 12 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit)

## 5. DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/doctor_auto_fix.py` PASS
- [ ] `bash -n cli/helix-doctor` PASS
- [ ] pytest 全 12 ケース PASS (T1〜T6)
- [ ] dry_run=True で実際の変更が発生しないこと確認 (T1-001 PASS)
- [ ] destructive 操作が handler 未登録で skip されること確認 (T5-001 PASS)
- [ ] audit log が helix.db に記録されること確認 (T5-002 PASS)
- [ ] `HELIX_DOCTOR_AUTO_FIX_DRY_RUN_ONLY=1` ガードが機能すること確認 (T6-001 PASS)
- [ ] ADR-050 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## 6. V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §3 設計方針 / §4 実装計画 |
| ③ テスト設計 | §4 Sprint .4 テストケース一覧 (T1〜T6) |
| ② 実装コード | cli/lib/doctor_auto_fix.py + cli/helix-doctor (Sprint .1-.3 で実装) |
| ④ テストコード | cli/lib/tests/test_doctor_auto_fix.py (Sprint .4 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .4 ケース一覧に T 番号明記
- テストコード → 設計: pytest test に `# PLAN-181 T{N}-{NNN}` コメントで対応付け (Sprint .4 実装時)
- テスト設計 → テストコード: test 関数名で T 番号対応 (Sprint .4 実装時)

## 7. 関連 reference

- PLAN-168 (drift auto-fix proposal — 設計方針の参照元、handler 共通基盤の先行事例)
- PLAN-110 (helix doctor warn 漸減 — doctor check 改善との共存)
- ADR-050 (本 PLAN の L2 snapshot、起票予定)
- SRE Book §17 (self-healing の安全性原則)
- HELIX CLAUDE.md §コーディング規約 (テストなしの完了宣言禁止)
