---
plan_id: PLAN-209
title: "PLAN-209: handover diff/merge UI (web-based viewer + manual merge、PLAN-166 拡張)"
kind: impl
layer: L4
drive: fe
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
created: 2026-05-23
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — Flask/FastAPI 選定 + LCS diff アルゴリズム設計 adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-128/166 との schema 整合・UI scope 確認"
  - role: se
    slot_label: "SE — diff engine (LCS-based) + apply-merge CLI バックエンド実装"
  - role: fe
    slot_label: "FE — Flask テンプレート + diff viewer HTML/CSS 実装"
  - role: qa
    slot_label: "QA — diff engine unit test + merge apply bats test"
generates:
  - artifact_path: cli/lib/handover_diff.py
    artifact_type: python_module
  - artifact_path: cli/helix-handover
    artifact_type: cli_extension
  - artifact_path: cli/templates/handover_diff_viewer.html
    artifact_type: template
  - artifact_path: cli/lib/tests/test_handover_diff.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-128
    - PLAN-166
  blocks: []
related_plans:
  - PLAN-128
  - PLAN-166
related_adr: []
---

# PLAN-209: handover diff/merge UI (web-based viewer + manual merge、PLAN-166 拡張)

> **kind**: impl / **layer**: L4 / **drive**: fe
> **本 PLAN の役割**: PLAN-128/166 の UI 層として、localhost Flask サーバーで複数 handover を視覚的に比較・手動 merge できる環境を提供する。PM が差分を目視確認し、`helix handover apply-merge` で適用するまでの承認フローを実現する。

---

## §0. 起票背景

PLAN-166 (handover protocol v2 CRDT merge) が実装済みでも、merge 結果の人間確認 UI が存在せず 3 課題がある: (1) 複数 handover の比較が CLI テキストでは見落としやすい、(2) `helix handover update` 直接書き換えで next_action/blocker_list が誤上書きされるリスク、(3) CRDT auto-merge を PM が視覚確認してから apply する承認ステップが不在。本 PLAN は localhost Flask diff viewer で (1)-(3) を解消する。

---

## §1. 目的

1. LCS-based diff engine を `cli/lib/handover_diff.py` に実装する (Sprint .1)
2. Flask localhost server + HTML diff viewer template を実装する (Sprint .2)
3. `helix handover apply-merge` CLI で merge 結果を CURRENT.json に適用する (Sprint .3)
4. unit test + bats test を追加し既存 test 全 PASS を維持する (Sprint .4)

---

## §2. 業界 standard 参照

| 参照 | 用途 |
|---|---|
| Python `difflib.SequenceMatcher` (stdlib) | LCS-based diff の実装根拠。外部依存なしで diff を実現 |
| Flask 公式 docs | localhost server の軽量選択根拠。FastAPI より依存が少ない |
| git diff --word-diff 出力形式 | diff viewer の UX 参考 (additions/deletions 色分け) |
| HELIX PLAN-128/166 | diff 対象フィールド + merge engine 接続点の正本定義 |

---

## §3. 設計

### 3.1 diff engine (cli/lib/handover_diff.py)

```python
# handover_diff.py が提供する主要 API
def diff_handovers(base: dict, current: dict) -> HandoverDiff:
    """LCS-based field-level diff を返す。"""
    ...

def merge_handovers(base: dict, current: dict, patch: dict) -> dict:
    """diff 結果 + PM パッチを適用した merged dict を返す。"""
    ...
```

- フィールド単位の diff: `next_action` / `blocker_list` / `notes` / `agent_slot_history` を LCS で比較
- scalar フィールド (`status` / `owner` / `progress_percent`) は単純 before/after
- diff 結果は `HandoverDiff` dataclass (field / before / after / change_type) のリストとして返す

### 3.2 Flask server + diff viewer

```
helix handover diff-ui [--port 7788] [--base FILE] [--current FILE]
```

- Flask app を localhost:7788 で起動
- `/` : 現在の CURRENT.json と指定 base の diff を HTML で表示
- `/apply` (POST): PM が確認・編集したフォームデータを受け取り、merge 候補 JSON を `/tmp/helix-merge-candidate.json` に保存
- サーバーは Ctrl+C または `/shutdown` (GET) で終了

HTML template (`cli/templates/handover_diff_viewer.html`):
- additions を緑、deletions を赤でハイライト (git diff スタイル)
- フィールドごとに「採用 / 破棄 / 手動編集」のラジオボタン
- Submit ボタンで `/apply` に POST、merge candidate を保存

### 3.3 apply-merge CLI

```
helix handover apply-merge [--candidate FILE] [--dry-run]
```

- `--candidate` 未指定時は `/tmp/helix-merge-candidate.json` をデフォルト参照
- `--dry-run` (default): merge 結果を stdout のみ出力、CURRENT.json を変更しない
- `--apply` フラグで CURRENT.json を上書き適用 (backup を `.helix/handover/CURRENT.json.bak` に作成)

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| Sprint .1 | diff engine 実装 (handover_diff.py) | se | `HandoverDiff` が 2 handover を field-level diff して返す pytest PASS |
| Sprint .2 | Flask server + HTML template 実装 | fe | `helix handover diff-ui` で localhost:7788 が起動し diff が表示される |
| Sprint .3 | apply-merge CLI 実装 | se | `helix handover apply-merge --dry-run` が merge preview を stdout 出力 |
| Sprint .4 | unit test + bats test + 既存回帰 PASS | qa | `pytest cli/lib/tests/test_handover_diff.py -q` 全 PASS |

---

## §5. 段階導入と安全ガード

| 操作 | 自動化 | 理由 |
|---|---|---|
| diff 計算 + HTML 表示 | O (read-only) | CURRENT.json 変更なし |
| merge candidate 生成 (/apply POST) | O (tmp file のみ) | CURRENT.json 変更なし |
| CURRENT.json 上書き (apply-merge) | X (--apply は PM 明示後のみ) | Plan Consent 必須 |

`--apply` 実行時は CURRENT.json を `.helix/handover/CURRENT.json.bak` にバックアップしてから適用する。backup が存在する場合は `--force-backup` を要求して誤操作を防ぐ。

---

## §6. デグレ禁止項目

1. `helix handover dump` / `update` / `resume` / `status` の既存動作は変更しない
2. PLAN-128 で追加した新フィールド (`plan_id` / `progress_percent` / `blocker_list` / `context_snapshot_path` / `agent_slot_history`) の型は変更しない
3. Flask server は HELIX 本体の必須依存にしない。`flask` 未インストール時は案内メッセージを返して gracefully 終了する。
4. CURRENT.json の backup は apply-merge 実行時のみ作成する。通常の update では作成しない。

---

## §7. DoD (Definition of Done)

1. Sprint .1: `HandoverDiff` が `next_action` フィールドの変更を additions/deletions で返す pytest PASS
2. Sprint .2: `helix handover diff-ui --port 7788` で browser から diff viewer にアクセスできる
3. Sprint .3: `helix handover apply-merge --dry-run` が merge preview を stdout 出力し、`--apply` 実行後に CURRENT.json.bak が作成される
5. Sprint .4: `pytest cli/lib/tests/test_handover_diff.py -q` が全 PASS (diff engine + merge 5 件以上)
6. Sprint .4: `bash -n cli/helix-handover` が syntax check PASS
7. `python3 cli/lib/plan_validator.py docs/plans/PLAN-209-*.md` が PASS

---

## §8. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-209-handover-diff-merge-ui.md |
| ② 実装コード | Sprint .1〜.3 で起票 | cli/lib/handover_diff.py / cli/helix-handover / cli/templates/handover_diff_viewer.html |
| ③ テスト設計 | Sprint .4 entry で策定 | docs/v2/L4-test-design/PLAN-209-handover-diff-test-design.md (予定) |
| ④ テストコード | Sprint .4 で実装 | cli/lib/tests/test_handover_diff.py |

**双方向 reference**:
- 本 PLAN → 実装: generates.artifact_path `cli/lib/handover_diff.py`
- 実装 → 本 PLAN: module docstring に「設計: PLAN-209」を追記
- 本 PLAN → テストコード: generates.artifact_path `cli/lib/tests/test_handover_diff.py`
- テストコード → 本 PLAN: test docstring に「DoD 検証: PLAN-209 §7」を追記

---

## §9. リスク

| リスク | 緩和策 |
|---|---|
| flask 未インストールで diff-ui が起動不能 | ImportError 時に `pip install flask` 案内メッセージを出力して gracefully 終了 |
| LCS diff が大きな handover で遅くなる | `difflib.SequenceMatcher` は stdlib 実装。next_action が 5000 文字超の場合は先頭 2000 文字のみ diff して warn |
| apply-merge で CURRENT.json が破損 | backup (.bak) 作成 + `--dry-run` default で 2 重ガード |
| PLAN-166 未完了時の merge engine 依存 | diff engine は PLAN-166 なしで独立動作可能。merge_handovers() は PLAN-166 完了後に接続するキャリー |

---

## §10. carry list + 関連 PLAN

**carry**:
- [ ] PLAN-166 完了後に `merge_handovers()` を CRDT merge engine に接続
- [ ] `--apply` フラグに `HELIX_MERGE_APPLY_APPROVED=1` env guard を追加 (PLAN-152 guard と統一)

**関連 PLAN**: PLAN-128 (diff 対象フィールド正本) / PLAN-166 (merge engine バックエンド)
