---
plan_id: PLAN-148
title: "helix plan complete 時の parent/child status 整合チェック (child draft 放置 drift 防止)"
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — plan_parent_child_checker.py 実装・helix-plan complete フック統合"
  - role: pmo-sonnet
    slot_label: "PMO — helix doctor 統合方針確認・既存 validate_dependencies との境界整合"
generates:
  - artifact_type: python_module
    path: cli/lib/plan_parent_child_checker.py
  - artifact_type: cli_extension
    path: cli/helix-plan
  - artifact_type: test
    path: cli/lib/tests/test_plan_parent_child_checker.py
dependencies:
  parent: null
  requires:
    - PLAN-093
    - PLAN-117
  blocks: []
related_docs:
  - cli/lib/plan_validator.py
  - cli/lib/plan_drift_checker.py
  - docs/plans/PLAN-093-plan-drift-detection-curator.md
acceptance_criteria:
  - "helix plan complete <PLAN-X> 実行時、frontmatter parent=<PLAN-X> な child PLAN が存在すれば一覧を表示する"
  - "child PLAN に status=draft/proposed/active が 1 件以上あれば WARN を出力する (default: advisory)"
  - "helix doctor check_plan_parent_child_consistency が open child を検出して WARN を返す"
  - "python3 -m py_compile cli/lib/plan_parent_child_checker.py PASS"
  - "pytest cli/lib/tests/test_plan_parent_child_checker.py 全 PASS"
  - "既存 helix plan / helix doctor の動作に影響がない (既存テスト全 PASS)"
---

# PLAN-148: helix plan complete 時の parent/child status 整合チェック

## §1 背景・目的

### 1.1 問題状況

HELIX の PLAN frontmatter には `dependencies.parent` フィールドがあり、
子 PLAN が `parent: PLAN-X` を宣言することで親子関係を表現できる。

しかし、**parent の status を completed に変更する際、child PLAN の状態を検証する仕組みがない**。

典型的な drift パターン:

- PLAN-MM-001 (V5 全体構想) を `completed` にしようとするが、
  子 PLAN-091〜099 の一部が `draft` のまま
- PLAN-093 親が close しても、下位 sprint が未完で子 PLAN が `active` のまま放置される

この drift は `helix doctor` の既存 check (check_plan_drift / check_plan_freshness) では
検出できない: これらは generates の成果物や freshness を見るが、
parent/child の status 整合を見ない。

### 1.2 解決ゴール

1. `helix plan complete <PLAN-X>` 実行時に child PLAN の status を確認し、
   open child (draft/proposed/active) があれば WARN を表示する
2. `helix doctor check_plan_parent_child_consistency` として独立 check を追加し、
   定期的な整合確認を可能にする
3. 既存の `cli/lib/plan_validator.py` の依存 cycle 検出とは **責務を分離**する:
   - plan_validator.py: frontmatter の静的 lint (cycle / enum / reciprocal)
   - plan_parent_child_checker.py: 実ファイル横断の動的 status 整合確認

## §2 L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 framework 内の拡張実装** であり、新規の大局判断を含まない。
ADR snapshot は不要。

根拠:

- 実装は既存 `cli/lib/plan_drift_checker.py` (PLAN-093 成果物) の横への拡張
- helix doctor check の追加は既存 advisory pattern を踏襲 (新 pattern なし)
- `helix plan complete` コマンドへの統合は既存 CLI 拡張パターンと同一

## §3 設計方針

### 3.1 plan_parent_child_checker.py

```python
# cli/lib/plan_parent_child_checker.py

OPEN_STATUSES = {"draft", "proposed", "active"}


class ParentChildChecker:
    """
    docs/plans/ 配下の PLAN frontmatter を横断し、
    指定 parent_id の children を収集して status を確認する
    """

    def find_children(self, parent_id: str, plans_dir: Path) -> list[dict]:
        """
        plans_dir 配下の全 .md を走査し、
        frontmatter.dependencies.parent == parent_id な PLAN を返す
        返却形式: [{"plan_id": ..., "status": ..., "path": ...}]
        """

    def check_open_children(
        self, parent_id: str, plans_dir: Path
    ) -> dict:
        """
        find_children を呼び出し、open status (draft/proposed/active) の
        child 一覧と warn フラグを返す
        返却形式:
        {
            "parent_id": str,
            "children": list[dict],
            "open_children": list[dict],
            "has_open": bool
        }
        """
```

### 3.2 helix plan complete 統合

`cli/helix-plan` の `complete` サブコマンドに以下を追加:

```bash
# helix plan complete PLAN-X の末尾に実行
if python3 -c "
from cli.lib.plan_parent_child_checker import ParentChildChecker
result = ParentChildChecker().check_open_children('$PLAN_ID', '$PLANS_DIR')
if result['has_open']:
    print('WARN: open child PLANs detected:')
    for c in result['open_children']:
        print(f\"  {c['plan_id']} ({c['status']})\")
    print('Run: helix plan complete <child-id> or update status manually.')
" 2>/dev/null; then
    :
fi
```

既存の `complete` 処理 (status 更新) は変更しない。
WARN はあくまで advisory 表示であり、complete 自体を block しない (P2 phase で fail-close 化を検討)。

### 3.3 helix doctor check 追加

`check_plan_parent_child_consistency` を helix doctor に追加する。

```
目的: 全 PLAN を横断し、parent=X かつ X.status=completed な child が open status の場合を検出
入力: docs/plans/*.md 全 frontmatter
判定:
  - parent PLAN.status == completed AND child.status IN (draft/proposed/active)
    → WARNING: child open after parent completed
  - parent PLAN が存在しない (orphan parent)
    → WARNING: orphan parent reference
出力: {parent_id, child_id, child_status, message}[]
fail-close: なし (advisory のみ、Phase 2 で fail-close 昇格検討)
```

## §4 実装 Sprint 計画

### Sprint .1: plan_parent_child_checker.py 実装

- 担当: SE
- 対象: `cli/lib/plan_parent_child_checker.py`
- 作業: ParentChildChecker クラス実装 (find_children / check_open_children)
- 検証: `python3 -m py_compile` PASS
- 想定: 45 分

### Sprint .2: helix doctor 統合 + テスト

- 担当: SE
- 対象: `cli/helix-doctor` (check 追加), `cli/lib/tests/test_plan_parent_child_checker.py`
- 作業: check_plan_parent_child_consistency 追加 + pytest 8 ケース実装
- 検証: `bash -n cli/helix-doctor` + `pytest test_plan_parent_child_checker.py` PASS
- 想定: 60 分

### Sprint .3: helix plan complete 統合 + DoD 確認

- 担当: SE / PMO
- 対象: `cli/helix-plan` (complete サブコマンドに WARN 追加)
- 作業: complete 時の child check 表示統合 + 既存テスト回帰確認
- 検証: fake PLAN fixture での E2E + 既存テスト全 PASS
- 想定: 45 分

## §5 テスト設計

### test_plan_parent_child_checker.py

| テスト ID | シナリオ | 期待値 |
|---|---|---|
| U-148-001 | parent=PLAN-X の child 2 件 (両方 completed) | has_open=False |
| U-148-002 | parent=PLAN-X の child 2 件 (1 件 draft) | has_open=True, open_children=1 件 |
| U-148-003 | parent=PLAN-X の child なし | children=[] / has_open=False |
| U-148-004 | parent=PLAN-X の child 3 件 (全 active) | open_children=3 件 |
| U-148-005 | parent 参照先 PLAN が存在しない (orphan) | orphan warning 検出 |
| U-148-006 | parent=PLAN-X (status=active) の child 1 件 draft | has_open=True (parent active でも検出) |
| U-148-007 | parent=PLAN-X (status=completed) の child 全 completed | has_open=False |
| U-148-008 | plans_dir が空ディレクトリ | children=[] / エラーなし |

## §6 DoD (完了条件)

- [ ] Sprint .1: `cli/lib/plan_parent_child_checker.py` 実装完了、`py_compile` PASS
- [ ] Sprint .2: helix doctor に `check_plan_parent_child_consistency` が advisory mode で追加される
- [ ] Sprint .2: `pytest cli/lib/tests/test_plan_parent_child_checker.py` 全 PASS (8 ケース)
- [ ] Sprint .3: `helix plan complete <PLAN-X>` 実行時に open child が存在すれば WARN 表示される
- [ ] Sprint .3: 既存 `helix plan` / `helix doctor` の既存 check に影響がない (既存テスト全 PASS)
- [ ] helix doctor warn 増加なし (新 check 自体は warn 追加するが、既存 check は変化なし)

## §7 V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 (本 PLAN §3-§5) | docs/plans/PLAN-148-plan-parent-child-completion-check.md |
| ② 実装コード | cli/lib/plan_parent_child_checker.py / cli/helix-plan / cli/helix-doctor |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-148-test-design.md (Sprint .2 完了後に起票) |
| ④ テストコード | cli/lib/tests/test_plan_parent_child_checker.py |

- 設計 → テスト設計: テスト設計ファイル `docs/v2/L4-test-design/PLAN-148-test-design.md`
- テスト設計 → 設計: 対象設計 `PLAN-148 §3-§5`
- 設計 → 実装コード: 実装ファイル `cli/lib/plan_parent_child_checker.py`
- テストコード → テスト設計: DoD 検証 `PLAN-148 U-148-001〜008`

## §8 関連

- PLAN-093: drift 検出 + helix doctor 拡張 (本 PLAN requires / 類似 helix doctor check の先行実装)
- PLAN-117: drift detect 基盤 (本 PLAN requires)
- `cli/lib/plan_validator.py`: 静的 lint (本 PLAN と責務を分離)
- `cli/lib/plan_drift_checker.py`: 動的 status チェック (本 PLAN の横展開)
