---
plan_id: PLAN-202
title: "PLAN-202: helix-team team chat orchestration (multi-agent dialogue)"
kind: design
layer: L4
drive: agent
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
created: "2026-05-23"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl
    slot_label: "TL — dialogue loop 設計・turn 永続化スキーマ・終了条件ロジック設計"
  - role: se
    slot_label: "SE — cli/lib/team_chat.py + cli/helix-team-chat 実装・helix.db team_chat_turns 統合"
  - role: qa
    slot_label: "QA — turn 永続化 / acceptance 条件 / mock agent 応答を用いた fixture テスト"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-165 (team workflow framework) との責務重複・drift チェック"
generates:
  - artifact_path: docs/plans/PLAN-202-team-chat-orchestration.md
    artifact_type: design_doc
  - artifact_path: cli/lib/team_chat.py
    artifact_type: python_module
  - artifact_path: cli/helix-team-chat
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_team_chat.py
    artifact_type: test
dependencies:
  parent: PLAN-165
  requires:
    - PLAN-165
  blocks: []
related_plans:
  - PLAN-165 (team workflow framework — 本 PLAN の発展元。role 定義・委譲パターンを継承)
  - PLAN-088 (TodoWrite × agent slot framework — agent_slots テーブルを共有)
  - PLAN-099 (自動走行 framework — session_id 取得の共通基盤)
test_design: docs/v2/L4-test-design/PLAN-202-unit-test-design.md (別 session 起票予定)
---

# PLAN-202: helix-team team chat orchestration

> **位置付け**: PLAN-165 (team workflow) の発展。複数 agent (TL / SE / QA) が
> 対話形式で議論しながら設計を進める dialogue loop orchestration を実装する。
> 各 turn は `.helix/team-chat/<session-id>/turn-N.md` で永続化される。

## 1. 目的

PLAN-165 は role 別 parallel 実行を定義したが、agent 間の **意見交換・反論・収束** という
対話プロセスは対象外だった。本 PLAN は:

1. **TL → SE → TL → QA → 承認** の dialogue loop を CLI で駆動する
2. 各 turn を Markdown で永続化し、セッション跨ぎで会話文脈を維持する
3. 全 participant の acceptance が揃った時点で loop を終了する

## 2. 背景

### 2.1 PLAN-165 との責務分離

| 機能 | PLAN-165 (team workflow) | PLAN-202 (team chat) |
|---|---|---|
| agent 並列実行 | 担当 | 委譲元として参照のみ |
| 設計議論・反論ループ | 対象外 | **新規担当** |
| turn 永続化 | なし | `.helix/team-chat/<sid>/turn-N.md` |
| 終了条件 | task complete | 全 participant acceptance |

## 3. 設計方針

### 3.1 dialogue loop

```
TL 案提示 (turn-1)
  ↓
SE 突っ込み (turn-2)  ←── turn.author = se / turn.type = challenge
  ↓
TL 再提案 (turn-3)    ←── turn.author = tl / turn.type = revision
  ↓
QA 検証コメント (turn-4) ← turn.author = qa / turn.type = verify
  ↓
acceptance 確認:
  全 participant が acceptance: true → loop 終了
  未達 → turn-N+1 へ継続 (上限: max_turns=20)
```

### 3.2 turn ファイル形式

```
.helix/team-chat/<session-id>/
  turn-001.md   # TL 初期案
  turn-002.md   # SE 突っ込み
  turn-003.md   # TL 再提案
  ...
  summary.md    # 最終合意内容 (loop 終了時に自動生成)
```

turn-N.md の先頭 frontmatter:

```yaml
---
turn: 1
author: tl        # tl | se | qa | pm
type: proposal    # proposal | challenge | revision | verify | acceptance
acceptance: false
timestamp: "2026-05-23T10:00:00Z"
---
```

### 3.3 helix.db team_chat_turns

```sql
CREATE TABLE IF NOT EXISTS team_chat_turns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    turn_no      INTEGER NOT NULL,
    author       TEXT NOT NULL,  -- tl | se | qa | pm
    type         TEXT NOT NULL,  -- proposal | challenge | revision | verify | acceptance
    acceptance   INTEGER NOT NULL DEFAULT 0,
    content_path TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now','utc'))
);
```

### 3.4 CLI サブコマンド

```bash
helix team-chat start --participants tl,se,qa --topic "設計議題"
helix team-chat turn  --author tl --type proposal --content "..."
helix team-chat turn  --author se --type challenge --content "..."
helix team-chat accept --author tl    # acceptance: true に更新
helix team-chat status                # 現在の turn / acceptance 状況を表示
helix team-chat summary               # summary.md を生成して出力
```

## 4. 実装 Sprint

### Sprint .1 (tl + se): team_chat.py 骨格 + スキーマ

Entry: PLAN-165 完了確認 / helix.db 存在確認

1. `cli/lib/team_chat.py`: `TurnRecord` dataclass + `start_session()` / `add_turn()` / `check_acceptance()` / `generate_summary()`
2. team_chat_turns テーブル migration 追加 (idempotent)
3. `.helix/team-chat/<session-id>/` + turn-N.md 書き出し
4. `python3 -m py_compile cli/lib/team_chat.py` PASS

### Sprint .2 (se): CLI 実装

Entry: Sprint .1 PASS

1. `cli/helix-team-chat`: start / turn / accept / status / summary
2. `cli/helix` router に `team-chat` 登録
3. `bash -n cli/helix-team-chat` PASS

### Sprint .3 (qa + pmo-sonnet): テスト + G4

Entry: Sprint .2 PASS

1. `test_team_chat.py` 5 シナリオ: start_session / add_turn + DB INSERT / check_acceptance 収束・未達 / generate_summary / max_turns=20 StopIteration
2. pmo-sonnet: PLAN-165 責務 drift 確認
3. tl-advisor: G4 凍結判定

Exit: pytest 全 PASS + 全回帰 PASS + G4 passed

## 5. DoD

- [ ] `cli/lib/team_chat.py` 実装済み (start_session / add_turn / check_acceptance / generate_summary)
- [ ] `cli/helix-team-chat` 実装済み (start / turn / accept / status / summary)
- [ ] `cli/helix` router に team-chat 登録済み
- [ ] team_chat_turns テーブル: 各 turn で INSERT 確認
- [ ] `.helix/team-chat/<sid>/turn-N.md` + `summary.md` 生成確認
- [ ] `test_team_chat.py` 5 シナリオ全 PASS
- [ ] `python3 -m py_compile` + 全回帰 PASS (`helix test`)
- [ ] pmo-sonnet review 承認 / tl-advisor G4 passed

## 6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-202-team-chat-orchestration.md |
| ② 実装コード | 未着手 | cli/helix-team-chat / cli/lib/team_chat.py |
| ③ テスト設計 | 未起票 | docs/v2/L4-test-design/PLAN-202-unit-test-design.md |
| ④ テストコード | 未着手 | cli/lib/tests/test_team_chat.py |

双方向 reference: 本 PLAN → PLAN-165 (parent)。
実装コード → 本 PLAN: docstring に `# 契約: PLAN-202 §3` を明示 (実装時)。

## 7. risks

| リスク | 影響 | 緩和策 |
|---|---|---|
| turn が収束せず max_turns 超過 | loop が永続化ファイルを肥大化させる | StopIteration + summary 自動生成で強制終了 |
| session-id 衝突 (複数 chat 同時) | turn ファイルが混在 | session_id に `uuid4()` を使用 |
| PLAN-165 との責務重複 | 設計 drift 発生 | pmo-sonnet レビューを Sprint .3 mandatory に組み込み |

## 8. 関連リンク

- PLAN-165 (親): docs/plans/PLAN-165-team-workflow-framework.md
- PLAN-088 (agent_slots): docs/plans/PLAN-088-todowrite-agent-slot-framework.md
