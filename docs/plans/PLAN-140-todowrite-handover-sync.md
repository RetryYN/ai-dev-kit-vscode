---
plan_id: PLAN-140
title: "PLAN-140: TodoWrite 状態と handover Next Action の双方向同期 framework"
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (pmo-sonnet)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 単一実行正本競合解消の大局判断・TodoWrite 廃止禁止方針の確認"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・handover schema drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — 双方向同期の冪等性設計 review・競合 resolution 方針"
  - role: se
    slot_label: "SE — cli/lib/todo_handover_sync.py 実装・helix handover CLI 拡張"
  - role: qa
    slot_label: "QA — pytest fixture test 全ケース検証・冪等性確認・SessionStart 統合 smoke"
generates:
  - artifact_type: python_module
    artifact_path: cli/lib/todo_handover_sync.py
  - artifact_type: cli_extension
    artifact_path: cli/helix-handover
  - artifact_type: hook
    artifact_path: .claude/hooks/sessionstart-todowrite-populate.sh
  - artifact_type: test
    artifact_path: cli/lib/tests/test_todo_handover_sync.py
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-140-todowrite-handover-sync.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-042-todowrite-handover-sync-decision.md
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
    - PLAN-091
    - PLAN-139
  blocks: []
related_adr:
  - ADR-032
  - ADR-042
---

# PLAN-140: TodoWrite 状態と handover Next Action の双方向同期 framework

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-042** で凍結 (起票予定):

- TodoWrite (ephemeral in-session checklist) と handover Next Action (persistent cross-session task list) を双方向同期する設計採用
- TodoWrite を廃止せず ephemeral checklist として維持し、handover を永続 state として正本とする責務分担の確定
- SessionStart hook で handover Next Action → TodoWrite に自動 populate する設計選択
- 冪等性担保: 既存エントリとの突合は `task_id` / content hash で重複防止

---

## 1. 目的

TodoWrite (in-session の visible checklist) と handover Next Action (cross-session の persistent task list) が現状二重管理になっている。

本 session で TodoWrite を頻繁に更新しても handover Next Action は dump 時点で固定されており、次 session 開始時に状態が乖離する問題が継続している。

本 PLAN は双方向同期 framework を導入して以下を実現する:

1. `helix handover update --from-todowrite` — 完了した TodoWrite エントリを handover Next Action から削除
2. `helix handover populate-todo` — handover Next Action を次 session 開始時の TodoWrite に自動展開
3. SessionStart hook で handover → TodoWrite の自動 populate を実行

---

## 2. 背景

### 2.1 二重管理の問題

現状の状態管理は以下 2 層が非同期で運用される:

| 層 | ツール | 特性 | 問題点 |
|---|---|---|---|
| ephemeral (in-session) | TodoWrite | セッション内で可視、PM が随時更新 | セッション終了で消える。handover に反映されない |
| persistent (cross-session) | handover CURRENT.json の next_actions | セッション跨ぎで維持 | dump 時点で固定。session 内の TodoWrite 完了が反映されない |

この乖離により、次 session 開始時に「既に完了した carry」を再度着手しようとする無駄が発生する。

### 2.2 PLAN-099 / PLAN-139 との関係

PLAN-099 §10 (単一実行正本決定) では以下を確定している:

> ephemeral checklist = 既存 TodoWrite (廃止しない)  
> session 引き継ぎ = handover CURRENT.json (既存 handover CLI)

本 PLAN はこの分担を維持しつつ、両者の **状態同期** を追加する。TodoWrite を廃止せず、handover を永続 state の正本とする責務分担を保持する。

PLAN-139 (`helix runtime carry-status`) が handover の next_action_count を参照するため、本 PLAN で handover の状態が正確に維持されることが carry 判定の精度向上にも繋がる。

### 2.3 既存 handover schema

`helix handover status --json` は CURRENT.json を返し、`next_actions` フィールドが Next Action リストを持つ。`helix handover update --note` / `--complete` で個別更新は可能だが、TodoWrite との一括同期 CLI は存在しない。

---

## 3. 業界 standard 参照

本 PLAN は PLAN-087 ガード対象 (新 CLI / hook 設計を含む)。PLAN-099 §3 を parent として継承しつつ、双方向同期設計の根拠を追加する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "task list sync bidirectional idempotent state merge 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.144) + HELIX CLAUDE.md | SessionStart hook で前回 state を注入するパターンは CHANGELOG 2.1.144 で `/resume` background session 対応として確認。状態同期の冪等性は content hash または task_id による重複排除が標準パターン |
| "Claude Code TodoWrite handover task tracking 2026" | HELIX CLAUDE.md §BE 実装時の Handover ファイル維持 / §PLAN ⊃ ADR | handover は cross-session の永続 state。TodoWrite は ephemeral checklist。「ephemeral checklist = 既存 TodoWrite (廃止しない)」は TL v5 P1 遵守事項 (PLAN-099 §10.1) として確定済み |
| "session state populate todo from persistent context 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.141) | UserPromptSubmit / SessionStart hook で additionalContext / systemMessage に関連 state を bundle 注入するパターンが確認。handover → TodoWrite populate はこの延長線上の実装 |

---

## 4. 設計方針

### 4.1 責務分担 (PLAN-099 §10.1 準拠)

| 概念 | 担当 | 本 PLAN の変更 |
|---|---|---|
| ephemeral checklist | TodoWrite | 廃止しない。populate の target になる |
| cross-session 正本 | handover CURRENT.json | next_actions が sync の source になる |
| 同期ロジック | `todo_handover_sync.py` (新規) | TodoWrite ↔ handover の変換・突合 |

### 4.2 同期方向

**方向 A: TodoWrite → handover (--from-todowrite)**

- TodoWrite の完了エントリ (status=done) を特定
- handover Next Action から対応エントリを削除 (content hash or task_id で突合)
- 突合できない場合はスキップ (strict 削除は行わない)

**方向 B: handover → TodoWrite (populate-todo / SessionStart hook)**

- handover Next Action の未完了エントリを TodoWrite に追加
- 既存 TodoWrite エントリと重複する場合は追加しない (冪等性)
- `HELIX_TODO_MAX_POPULATE=10` (default): 最大追加件数の上限 (暴走防止)

### 4.3 冪等性設計

同期処理は何度実行しても結果が同一であることを保証する:

```
content_hash = sha256(action_text[:200].strip().lower())
既存 TodoWrite に同一 hash があれば追加しない
```

### 4.4 SessionStart hook 統合

`.claude/hooks/sessionstart-todowrite-populate.sh` (新規):

- SessionStart 時に `helix handover populate-todo --max 10` を実行
- handover CURRENT.json が存在しない場合は no-op (fail-open)
- エラー時は fail-open (hook は exit 0 で通過)

---

## 5. 実装計画

### Sprint .1: todo_handover_sync.py 実装 (Codex se 委譲)

**対象ファイル**: `cli/lib/todo_handover_sync.py` (新規)

実装内容:
- `load_todowrite(todo_path: Path) -> list[dict]` — todo.json を読んで entry list を返す
- `load_handover_actions(handover_path: Path) -> list[str]` — CURRENT.json の next_actions を返す
- `sync_todowrite_to_handover(todo_path, handover_path) -> dict` — 方向 A: TodoWrite 完了 → handover 削除
- `populate_todo_from_handover(handover_path, todo_path, max_items: int = 10) -> dict` — 方向 B: handover → TodoWrite 追加
- `content_hash(text: str) -> str` — 冪等性用 hash (sha256 prefix 8 chars)

mandatory in sprint:
- `python3 -m py_compile cli/lib/todo_handover_sync.py` PASS

### Sprint .2: helix handover CLI 拡張 + SessionStart hook (Codex se 委譲)

**対象ファイル**:
- `cli/helix-handover` (Edit: サブコマンド追加)
- `.claude/hooks/sessionstart-todowrite-populate.sh` (新規)

`helix handover` 拡張:
- `update --from-todowrite` サブコマンド: `sync_todowrite_to_handover()` を呼び出す
- `populate-todo [--max N]` サブコマンド: `populate_todo_from_handover()` を呼び出す

SessionStart hook:
- `helix handover populate-todo --max 10` を呼び出し
- CURRENT.json 不在時は no-op + 終了 (fail-open)

mandatory in sprint:
- `bash -n cli/helix-handover` PASS
- `bash -n .claude/hooks/sessionstart-todowrite-populate.sh` PASS

### Sprint .3: pytest fixture test + DoD 確認 (Codex qa 委譲)

**対象ファイル**: `cli/lib/tests/test_todo_handover_sync.py` (新規)

テストケース:

| ケース | 内容 |
|---|---|
| T-001 | TodoWrite 2 件 done → handover Next Action から対応エントリが削除される |
| T-002 | TodoWrite done エントリが handover に存在しない → スキップ (strict 削除なし) |
| T-003 | handover next_actions 3 件 → TodoWrite に populate される (重複なし時) |
| T-004 | 既に TodoWrite に同一 hash のエントリあり → 追加しない (冪等性) |
| T-005 | `populate-todo --max 2` で最大 2 件のみ追加 (暴走防止) |
| T-006 | handover CURRENT.json 不在 → no-op で正常終了 |
| T-007 | todo.json 不在 → no-op で正常終了 |
| T-008 | content_hash が同一テキストに対して常に同一値を返す (deterministic) |

mandatory in sprint:
- `python3 -m pytest cli/lib/tests/test_todo_handover_sync.py -q` 全ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (G4 相当)

---

## 6. DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/todo_handover_sync.py` PASS
- [ ] `bash -n cli/helix-handover` PASS (拡張後)
- [ ] `bash -n .claude/hooks/sessionstart-todowrite-populate.sh` PASS
- [ ] pytest T-001〜T-008 全 PASS
- [ ] `helix handover update --from-todowrite` が TodoWrite 完了エントリを handover から削除する
- [ ] `helix handover populate-todo` が冪等に TodoWrite を populate する
- [ ] SessionStart hook: handover 存在時に populate 実行、不在時は no-op (fail-open)
- [ ] `HELIX_TODO_MAX_POPULATE` を超えた populate は行わない
- [ ] 既存 `helix handover` コマンド (status / update / dump / clear) の回帰なし
- [ ] ADR-042 起票 (L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

---

## 7. V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §4 設計方針 / §5 実装計画 |
| ③ テスト設計 | 本 PLAN §5 Sprint .3 ケース一覧 (T-001〜T-008) |
| ② 実装コード | cli/lib/todo_handover_sync.py / cli/helix-handover 拡張 / SessionStart hook (Sprint .1-.2) |
| ④ テストコード | cli/lib/tests/test_todo_handover_sync.py (Sprint .3) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T-NNN 番号明記
- テストコード → 設計: pytest docstring に「PLAN-140 T-NNN」明記 (Sprint .3 実装時)
- テスト設計 → テストコード: test 関数名で T-NNN 対応 (Sprint .3 実装時)

---

## 8. 関連 reference

- PLAN-099 §10 (単一実行正本決定、TodoWrite = ephemeral / handover = persistent の責務分担)
- PLAN-128 (handover schema enhancement、next_actions フィールド正本)
- PLAN-139 (carry-status: handover next_action_count を参照するため本 PLAN の精度に依存)
- CLAUDE.md §BE 実装時の Handover ファイル維持 (handover ライフサイクル)
- [[feedback_dont_stop_with_carry_remaining]] (二重管理の根本課題)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-042 (本 PLAN の L2 snapshot、起票予定)
