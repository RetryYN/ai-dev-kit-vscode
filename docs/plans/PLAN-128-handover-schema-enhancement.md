---
plan_id: PLAN-128
title: "PLAN-128: handover protocol improvement (CURRENT.json schema 強化)"
layer: L4
kind: refactor
status: draft
size: M
drive: be
created: 2026-05-23
owner: PMO
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 新 schema 設計レビュー・整合確認"
  - role: se
    slot_label: "SE — cli/lib/handover.py 拡張実装 + テスト"
  - role: qa
    slot_label: "QA — bats test 設計・実装"
generates:
  - artifact_path: cli/lib/handover.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_handover_schema.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-111
related_docs:
  - helix/HELIX_CORE.md
  - CLAUDE.md §BE 実装時の Handover ファイル維持
---

# PLAN-128: handover protocol improvement (CURRENT.json schema 強化)

> **kind**: refactor (既存 handover schema への後方互換フィールド追加)
> **layer**: L4 (実装フェーズ。schema 変更 + Python module 拡張 + bats test)
> **drive**: be (CLI / Python helper 実装中心)
> **本 PLAN の役割**: `.helix/handover/CURRENT.json` の schema を強化し、長期 session 跨ぎ・大型 PLAN での handover 情報不足を解消する。既存フィールドとの後方互換を維持しつつ、5 新フィールドを追加する。

---

## §0. 本 PLAN の位置付け

`.helix/handover/CURRENT.json` は Opus セッション間で BE 実装の引き継ぎ情報を保持する。しかし現行 schema は基本フィールド (task_id / title / files / tests / next_action 等) のみで、以下の問題が発生している:

1. **Sprint 進捗の可視化不足**: `plan_id` と Sprint 単位の進捗が記録されず、「どの Sprint まで完了したか」が handover を読むだけでは不明
2. **blocker carry の明示化不足**: 前 session の blocker が `next_action` に埋め込まれており、blocker 専用フィールドがない
3. **PreCompact 連携の未実装**: PLAN-111 (context_snapshot_path) との連携が schema レベルで定義されていない
4. **agent 委譲履歴の不在**: 前 session で何を誰に委譲したかが分からず、再委譲の重複が発生する

---

## §1. 目的

1. 既存 `CURRENT.json` schema との後方互換を保ちつつ、5 新フィールドを追加する (Sprint .1)
2. `cli/lib/handover.py` の `dump` / `update` / `resume` コマンドが新フィールドを扱えるよう拡張する (Sprint .2)
3. 既存 bats test 全 PASS + 新フィールドの unit test / bats test を追加する (Sprint .3)

---

## §2. 背景

### 2.1 追加する 5 新フィールド

| 新フィールド | 型 | 用途 | CLI オプション |
|---|---|---|---|
| `plan_id` | string? | 対応 PLAN ID | dump --plan-id / update --plan-id |
| `progress_percent` | int 0-100? | Sprint 完了度 | dump --progress / update --progress |
| `blocker_list` | list[{id, description, created_at, resolved_at}] | 構造化 blocker carry | update --blocker / update --unblock |
| `context_snapshot_path` | string? | PreCompact 連携 snapshot path (PLAN-111) | update --snapshot-path |
| `agent_slot_history` | list[{role, task_summary, commit_sha, timestamp}] | 委譲履歴 | update --record-slot |

既存フィールド (task_id / title / status / owner / files / tests / next_action / blockers / notes / created_at / updated_at / head_sha) は型・名前とも変更なし。新フィールドは全て optional (None / [] がデフォルト) で後方互換を維持する。

### 2.2 WebSearch skip 根拠

本 PLAN は既存 Python module の後方互換フィールド追加。新 framework 採用・L2 大局判断なし。PLAN-087 ガードレール「設計 doc 新規起票・大幅 scope 変更時」に非該当。**WebSearch skip: refactor (既存 schema 拡張)、新技術採用なし**。

---

## §3. 詳細設計

### 3.1 dataclass 追加

```python
@dataclass
class BlockerEntry:
    id: str            # 例: "BLK-001"
    description: str
    created_at: str    # ISO 8601
    resolved_at: str | None = None

@dataclass
class AgentSlotRecord:
    role: str          # 例: "se", "pmo-sonnet"
    task_summary: str
    commit_sha: str | None = None
    timestamp: str     # ISO 8601
```

`update --blocker "..."` は既存 `blockers` (list[str]) と `blocker_list` 両方に同時追記して後方互換を維持する。

### 3.2 CLI 拡張

| コマンド | 追加オプション |
|---|---|
| `helix handover dump` | `--plan-id`, `--progress` |
| `helix handover update` | `--plan-id`, `--progress`, `--snapshot-path`, `--record-slot` |
| `helix handover resume` | 新フィールドを RESUME.md サマリに含める |
| `helix handover status` | 新フィールドの表示追加 |

---

## §4. 実装方針

### Sprint .1: 新 schema 設計確定

- `cli/lib/handover.py` の既存 schema 定義 (dataclass / dict 構造) を Read して確認
- `BlockerEntry` / `AgentSlotRecord` dataclass を追加
- `load_handover()` / `save_handover()` に後方互換ロード (missing key 補完) を追加
- 担当: se

### Sprint .2: dump / update / resume 拡張

- `helix handover dump` に `--plan-id`, `--progress` 追加
- `helix handover update` に `--plan-id`, `--progress`, `--snapshot-path`, `--record-slot` 追加
- `helix handover resume` の RESUME.md 生成に新フィールドのサマリを追加
- `helix handover status` の出力に新フィールドを追加
- 担当: se

### Sprint .3: テスト

- 既存 `cli/lib/tests/test_handover*.py` 全 PASS 確認
- 新フィールド unit test 5 件: backward_compat / blocker_list_append / agent_slot_history_record / progress_percent_update / context_snapshot_path_set
- bats test: `helix handover dump --plan-id PLAN-128` が `plan_id` フィールドを含む JSON を出力することを確認
- 担当: qa

---

## §5. 段階導入

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | 新 schema 設計確定 (dataclass 追加 + 後方互換 load) | se | `cli/lib/handover.py` に新 dataclass が追加され、旧 schema ロードが PASS |
| **Sprint .2** | dump / update / resume / status CLI 拡張 | se | `helix handover dump --plan-id PLAN-X` が新フィールド含む JSON を出力 |
| **Sprint .3** | unit test + bats test 追加 + 既存 test 全 PASS | qa | `pytest cli/lib/tests/test_handover*.py` 全 PASS + bats 全 PASS |

---

## §6. デグレ禁止項目

1. 既存フィールド (task_id / title / status / owner / files / tests / next_action / blockers / notes / created_at / updated_at / head_sha) の型・名前は変更しない
2. `helix handover dump` の既存オプション (`--task-id`, `--task-title`, `--files`, `--tests`, `--next`) の動作は変更しない
3. `helix handover update` の既存オプション (`--complete`, `--blocker`, `--unblock`, `--note`, `--owner`, `--status`) の動作は変更しない
4. `.helix/handover/ESCALATION.md` / `RESUME.md` の既存生成ロジックは維持する
5. PLAN-111 の未実装部分 (context_snapshot_path の実際の snapshot 生成) は本 PLAN のスコープ外。フィールドの schema 定義のみ。

---

## §7. DoD (Definition of Done)

1. Sprint .1: 旧 schema ファイル (新フィールド不在) をロードしても KeyError / Exception が発生しない
2. Sprint .2: `helix handover dump --plan-id PLAN-128 --progress 0` が `plan_id`, `progress_percent` を含む JSON を出力する
3. Sprint .2: `helix handover update --record-slot se "Sprint .1 handover.py 拡張"` が `agent_slot_history` に追記する
4. Sprint .3: `pytest cli/lib/tests/test_handover*.py -q` が全 PASS (既存 + 新規 5 件)
5. Sprint .3: `bash -n cli/helix-handover` が PASS (syntax check)
6. Sprint .3: bats test で `helix handover dump --plan-id X` の CLI 動作が PASS
7. `python3 cli/lib/plan_validator.py docs/plans/PLAN-128-*.md` が PASS

---

## §8. V-model 4 artifact trace

本 PLAN は設計 artifact (①) として機能する。

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-128-handover-schema-enhancement.md |
| ② 実装コード | Sprint .1〜.2 で起票 | cli/lib/handover.py |
| ③ テスト設計 | Sprint .3 entry で策定 | docs/v2/L4-test-design/PLAN-128-handover-test-design.md (予定) |
| ④ テストコード | Sprint .3 で実装 | cli/lib/tests/test_handover_schema.py |

**双方向 reference**:
- 本 PLAN → 実装コード: generates.artifact_path `cli/lib/handover.py`
- 実装コード → 本 PLAN: `handover.py` module docstring に「設計: PLAN-128」を追記
- 本 PLAN → テストコード: generates.artifact_path `cli/lib/tests/test_handover_schema.py`
- テストコード → 本 PLAN: test file docstring に「DoD 検証: PLAN-128 §7」を追記

---

## §9. 関連 PLAN / ADR

### 関連 PLAN
- PLAN-111: context_snapshot_path の実装 (PreCompact 連携 snapshot 生成)。本 PLAN は schema フィールド定義のみ、実際の snapshot 生成は PLAN-111 のスコープ

### 関連 ADR
- なし (後方互換フィールド追加のみ。L2 大局判断なし)

### 関連 docs
- CLAUDE.md §BE 実装時の Handover ファイル維持: handover 運用ルールの正本
- helix/HELIX_CORE.md: handover フェーズと連携ゲートの定義

---

## §10. リスク

| リスク | 緩和策 |
|---|---|
| 旧 CURRENT.json との非互換 | Sprint .1 で後方互換テスト `test_handover_backward_compat_old_schema` を最初に PASS させてから Sprint .2 へ進む |
| blocker / blocker_list の二重管理 | `helix handover status` で blocker_list を優先表示し、blockers は legacy 扱いと注記 |
| PLAN-111 未実装との依存混在 | context_snapshot_path はフィールド定義のみ。snapshot 生成は PLAN-111 スコープ (§6 デグレ禁止 5 で明記) |
| Sprint .3 既存 test 回帰 | Sprint .3 entry で既存 test を単独実行確認してから新規テストを追加 |
