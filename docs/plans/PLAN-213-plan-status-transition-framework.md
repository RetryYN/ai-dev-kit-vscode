---
plan_id: PLAN-213
title: "PLAN-213: PLAN draft → ready review framework (status 遷移自動化)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: M
created: "2026-05-23"
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — status enum 拡張 + helix plan ready CLI + helix.db 対応 + pmo-sonnet trigger"
  - role: pmo-sonnet
    slot_label: "PMO — status 遷移フロー・adversarial review 発火条件・既存 plan_validator との整合確認"
  - role: qa
    slot_label: "QA — status 遷移 fixture test + helix plan list --status 動作確認"
generates:
  - artifact_path: cli/helix-plan
    artifact_type: cli_extension
  - artifact_path: cli/lib/plan_status_manager.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_status_manager.py
    artifact_type: test
  - artifact_path: docs/commands/plan-status-transition.md
    artifact_type: markdown_doc
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-148-plan-parent-child-check
  blocks: []
related_adr: []
related_plans:
  - PLAN-148
related_docs:
  - cli/lib/plan_validator.py
  - docs/commands/index.md
---

# PLAN-213: PLAN draft → ready review framework (status 遷移自動化)

## L2 凍結 (ADR snapshot)

既存 plan_validator.py (V5 PLAN-091) および helix plan CLI の拡張実装であり、
status 値の追加は既存フィールドへの enum 拡張にとどまる。
新規 L2 大局判断 (新 framework 採用 / fail-close 設計転換) は発生しないため ADR snapshot は不要。

---

## §0. 背景・位置付け

現在 PLAN の status は `draft` / `complete` の 2 値のみ存在する。
2026-05-23 時点で repo には 110 PLAN が存在し、そのほぼ全てが `draft` に留まっている。
これは以下の問題を生む:

1. **review 待ち可視化なし**: draft == 実装前 / review 待ちが区別不能
2. **pmo-sonnet 発火契機なし**: 明示的な review 依頼シグナルがない
3. **completed 遷移が直接すぎる**: review なし draft → complete が常態化

本 PLAN は status を 5 値に細粒度化し、`helix plan ready` による review 依頼と
`ready → reviewed` での pmo-sonnet 自動 trigger を実装する。

**PLAN-148 との関係**: PLAN-148 = parent/child 整合チェック、本 PLAN = status 遷移追加。依存あり・責務分離。

**WebSearch skip 根拠**: 内部 status machine 実装。外部ライブラリ採用なし。

---

## §1. 設計方針

### status enum 拡張

| status | 意味 | 遷移元 | 遷移先 |
|---|---|---|---|
| `draft` | 起票済み・実装前 (初期値) | — | ready / blocked |
| `ready` | review 依頼済み | draft | reviewed / draft (差し戻し) |
| `reviewed` | pmo-sonnet review 完了 | ready | completed / draft (差し戻し) |
| `completed` | 実装・受入完了 | reviewed | — |
| `blocked` | 阻害要因あり・一時停止 | draft / ready | draft / ready (解除) |

**後退遷移**: `ready → draft` (差し戻し) および `reviewed → draft` (大幅修正時) を許可する。
`completed → *` の後退は禁止。

### plan_validator.py 対応

plan_validator の `VALID_STATUSES` に新 5 値を追加 (既存の `draft` / `complete` は互換性のため維持、
`complete` は `completed` への移行を WARN で促す)。

### plan_status_manager.py インタフェース

```python
def transition_status(plan_path: Path, target_status: str, allow_backward: bool = False) -> None:
    """frontmatter status を更新。不正遷移 (completed → draft 等) は ValueError。"""

def list_plans_by_status(plans_dir: Path, status: str) -> list[Path]:
    """status 一致の PLAN.md 一覧を返す。"""

def trigger_pmo_review(plan_path: Path) -> str:
    """ready 遷移時の pmo-sonnet review コマンド文字列を生成して返す。"""
```

### helix-plan CLI 拡張

```bash
helix plan ready <plan-id>             # draft → ready 遷移 + pmo-sonnet review コマンド提示
helix plan unblock <plan-id>           # blocked → (元の status) 遷移
helix plan list --status <status>      # 特定 status の PLAN 一覧
helix plan list --status ready         # review 待ち PLAN 一覧 (主要ユースケース)
```

`helix plan ready` 実行時の出力フォーマット:

```
PLAN-NNN を draft → ready に遷移しました。
次のコマンドで pmo-sonnet review を起動してください:
  helix claude --role pmo-sonnet --execute --task "PLAN-NNN review: docs/plans/PLAN-NNN-*.md"
```

---

## §2. 実装計画

### Sprint .1: plan_status_manager.py + plan_validator 拡張 (se、size S)

1. `cli/lib/plan_status_manager.py` 新規作成
   - `transition_status` / `list_plans_by_status` / `trigger_pmo_review` の 3 関数
   - 遷移許可テーブルを dict で管理 (拡張容易)
2. `cli/lib/plan_validator.py` の `VALID_STATUSES` に 5 値追加
   - `complete` → WARN で `completed` への移行を促す (互換性維持)
3. `python3 -m py_compile cli/lib/plan_status_manager.py` PASS

受入条件: `transition_status(path, "ready")` で status フィールド更新 /
`transition_status(path, "draft")` when `completed` で ValueError

### Sprint .2: helix-plan CLI 拡張 (se、size S)

1. `cli/helix-plan` に `ready` / `unblock` サブコマンド追加
2. `helix plan list --status <status>` フラグ追加
3. `bash -n cli/helix-plan` PASS

受入条件: `helix plan ready PLAN-NNN` が遷移 + pmo-sonnet コマンド提示 /
`helix plan list --status ready` が ready PLAN 一覧を返す

### Sprint .3: テスト + docs + pmo-sonnet review (qa ∥ docs、size S)

1. `cli/lib/tests/test_plan_status_manager.py` 新規作成 (12 case)
   - 正常遷移 5 パターン / 不正遷移 (completed → draft) / backward allow / list_plans_by_status /
     trigger_pmo_review フォーマット / plan_validator VALID_STATUSES 検証 / `complete` WARN
2. `docs/commands/plan-status-transition.md` 起草 (遷移図 / コマンド一覧 / ユースケース)
3. `pytest cli/lib/tests/test_plan_status_manager.py -v` 全 PASS
4. pmo-sonnet review (遷移フロー整合 / ready → reviewed 発火条件確認)

---

## §3. DoD

- [ ] status enum が 5 値に拡張 (draft / ready / reviewed / completed / blocked)
- [ ] `complete` (旧 2 値) に `completed` への移行 WARN 追加
- [ ] `helix plan ready <id>` で draft → ready 遷移 + pmo-sonnet trigger コマンド提示
- [ ] `helix plan list --status ready` が ready PLAN 一覧を返す
- [ ] `transition_status` が不正遷移を ValueError で拒否する
- [ ] `python3 -m py_compile cli/lib/plan_status_manager.py` PASS
- [ ] `bash -n cli/helix-plan` PASS
- [ ] unit test 12 case 全 PASS
- [ ] `docs/commands/plan-status-transition.md` 存在
- [ ] pmo-sonnet review 完了 (Sprint .3)
- [ ] 既存 plan_validator の WARN 数回帰なし
- [ ] `python3 cli/lib/plan_validator.py docs/plans/PLAN-213-plan-status-transition-framework.md` PASS

---

## §4. デグレ禁止

- 既存 `draft` / `complete` は plan_validator 通過を維持する
- `complete` は deprecated WARN のみ (retrofit は別 PLAN)
- `helix plan list` 既存サブコマンド動作を変更しない
- `transition_status` の write は status フィールドのみ変更する

---

## §5. V-model trace

- ① 設計: `docs/plans/PLAN-213-plan-status-transition-framework.md` (本 file)
- ② 実装: `cli/lib/plan_status_manager.py` / `cli/helix-plan` → docstring に「設計: PLAN-213」
- ③ テスト設計: Sprint .3 entry で §2 Sprint .3 を正本とする
- ④ テストコード: `cli/lib/tests/test_plan_status_manager.py` → docstring に「DoD 検証: PLAN-213 §3」

---

## §6. リスク

| リスク | 緩和策 |
|---|---|
| `complete` 旧値互換性 | WARN のみで即拒否しない。明示的に互換処理 |
| `completed → draft` 誤後退 | 不正遷移は ValueError + CLI エラーメッセージ |
| list スキャン遅延 | glob + frontmatter parse のみ。110 PLAN 程度は許容範囲 |
| pmo-sonnet review の model 誤指定 | `trigger_pmo_review` は model 明示せず frontmatter 自動起動に委ねる |
