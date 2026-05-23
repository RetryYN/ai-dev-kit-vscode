---
plan_id: PLAN-135
title: "PLAN-135: helix slash command 登録 framework (Claude Code IDE 統合)"
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-helix-explorer
    slot_label: "PMO — Sprint .1 既存 .claude/commands/ 棚卸し + helix CLI 対象候補選定"
  - role: tl-advisor
    slot_label: "TL adversarial check — Sprint .2 slash command 仕様と helix doctor 統合設計の妥当性確認"
  - role: docs
    slot_label: "Docs — Sprint .3 .claude/commands/helix-*.md 起草 (5 コマンド)"
  - role: se
    slot_label: "SE — Sprint .4 helix doctor check_slash_commands 実装 + bats test"
generates:
  - artifact_type: config
    path: .claude/commands/helix-doctor.md
  - artifact_type: config
    path: .claude/commands/helix-skill-search.md
  - artifact_type: config
    path: .claude/commands/helix-budget.md
  - artifact_type: config
    path: .claude/commands/helix-sprint-status.md
  - artifact_type: config
    path: .claude/commands/helix-handover-status.md
  - artifact_type: cli_extension
    path: cli/helix-doctor
  - artifact_type: test
    path: cli/tests/test_slash_commands.bats
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_docs:
  - docs/commands/index.md
  - docs/agent-skills/getting-started.md
  - docs/agent-skills/README.md
  - .claude/commands/build.md
acceptance_criteria:
  - ".claude/commands/helix-doctor.md が存在し、Claude Code で /helix-doctor 起動可能"
  - ".claude/commands/helix-skill-search.md が存在し、/helix-skill-search $ARGUMENTS で skill 検索が起動"
  - ".claude/commands/helix-budget.md / helix-sprint-status.md / helix-handover-status.md の計 5 コマンドが存在"
  - "各 slash command の frontmatter に description が設定されている"
  - "helix doctor に check_slash_commands が追加され、登録漏れ検出が機能する"
  - "bats test で check_slash_commands の pass/fail が確認可能"
  - "helix doctor fail 0 件維持"
---

# PLAN-135: helix slash command 登録 framework (Claude Code IDE 統合)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内に L2 大局判断なし。新技術採用なし (Claude Code `.claude/commands/` framework は既存仕様)。**ADR snapshot 不要**。

判断根拠: slash command は Claude Code の既存 framework (`.claude/commands/*.md` 形式)。HELIX PLAN を追加するのみで、framework 採用判断は不要。

## 背景

HELIX CLI (`helix doctor` / `helix skill search` / `helix budget` 等) は現在 terminal 経由のみ起動可能。開発中は Claude Code の IDE 上でコンテキストを切らずに呼び出したい場面が多い。

Claude Code には `.claude/commands/*.md` 形式の slash command framework が存在し、既に本 project でも 7 コマンド (`/build` / `/spec` / `/test` 等) が稼働している (`.claude/commands/` 参照)。

同じ仕組みで `helix doctor` / `helix skill` / `helix budget` 等を `/helix-*` として登録することで:

1. Claude Code IDE 上で `/helix-doctor` 一発で環境診断が起動できる
2. `$ARGUMENTS` 経由でパラメータを渡せる (例: `/helix-skill-search "log report json output"`)
3. helix doctor に `check_slash_commands` を追加し、必須コマンドの登録漏れを自動検出できる

## WebSearch 履歴 (PLAN-087 ガード遵守、3 query 実施)

| # | Query | 発見事項 |
|---|---|---|
| Q1 | `Claude Code slash commands .claude/commands format specification 2024` | フォーマットは `description:` frontmatter + Markdown 本文 + `$ARGUMENTS` プレースホルダー (Anthropic 公式ドキュメント準拠) |
| Q2 | `Claude Code custom slash commands description frontmatter argument syntax` | 既存 7 コマンドは `description:` のみの frontmatter。`$ARGUMENTS` は本文内で参照可能 (`.claude/commands/build.md` で実測確認) |
| Q3 | `Claude Code slash command allowedTools permissions helix CLI integration` | CLI 呼び出しには `allowedTools: [Bash]` 指定が推奨。HELIX は description に「Bash で実行します」と明示する設計にする |

## 設計方針

### slash command の format (既存踏襲)

既存 `.claude/commands/build.md` を範例とする:

```markdown
---
description: <コマンドリストに表示する説明文>
---

<本文: Claude Code に実行させる指示。$ARGUMENTS でパラメータを受け取る>
```

HELIX helix-* コマンドでは本文内で `helix <subcommand> $ARGUMENTS` を Bash で実行するよう Claude Code に指示する。

### 登録対象 5 コマンド (Sprint .3)

| slash command | 呼び出す CLI | 用途 |
|---|---|---|
| `/helix-doctor` | `helix doctor` | 環境診断 (pass/fail/warn 件数確認) |
| `/helix-skill-search` | `helix skill search "$ARGUMENTS"` | スキル検索 (引数: タスク記述) |
| `/helix-budget` | `helix budget status` | Claude/Codex 消費 % + 枯渇予測 |
| `/helix-sprint-status` | `helix sprint status` | 現在スプリント状態確認 |
| `/helix-handover-status` | `helix handover status` | handover 状態確認 |

### helix doctor 統合 (Sprint .4)

`check_slash_commands` を `cli/helix-doctor` (または `cli/lib/helix_doctor.py`) に追加する:

- `.claude/commands/helix-*.md` が 5 件以上存在することを確認
- 必須 5 コマンドの不在を warn として報告
- doctor suppress.yaml で個別に suppress 可能

## 実装計画

### Sprint .1: 棚卸し + 候補選定 (pmo-helix-explorer 委譲)

**Entry**: なし

実施内容:

1. `.claude/commands/` 全件 Read (現行 10 件: build / code-simplify / innovation-marketing 等)
2. `docs/commands/index.md` を Read し、全 helix CLI コマンドを確認
3. 登録対象 5 コマンドの最終選定 (上記方針を基準とし、Sprint .1 結果で調整)
4. 既存コマンドとの重複がないことを確認 (特に `/spec`, `/build` との責務重複)

Sprint .1 完了条件:

- 登録対象 5 コマンドが確定している
- 既存コマンドとの重複なし

### Sprint .2: TL adversarial check (tl-advisor 委譲)

**Entry**: Sprint .1 完了

実施内容:

```
helix codex --role tl-advisor --task "PLAN-135 slash command 登録設計の adversarial check。
5 コマンドの選定基準・helix doctor 統合方針に設計上の問題がないか確認。
特に: (1) $ARGUMENTS 受け渡しの安全性 (2) helix doctor check の粒度 (3) 既存 .claude/commands との責務重複 を確認してほしい。"
```

Sprint .2 完了条件:

- tl-advisor の助言が得られている
- 設計変更が必要な場合は Sprint .3 前に反映済

### Sprint .3: slash command 5 件起草 (docs 委譲)

**Entry**: Sprint .2 完了

実施内容:

1. `.claude/commands/helix-doctor.md` 起草
2. `.claude/commands/helix-skill-search.md` 起草 (`$ARGUMENTS` でタスク記述を受け取る)
3. `.claude/commands/helix-budget.md` 起草
4. `.claude/commands/helix-sprint-status.md` 起草
5. `.claude/commands/helix-handover-status.md` 起草

各ファイルの最小形式:

```markdown
---
description: <説明文>
---

Run `helix <subcommand>` to <目的の説明>.

Bash を使って以下を実行する:
```bash
helix <subcommand> $ARGUMENTS
```

結果をそのまま表示する。エラーの場合は原因を日本語で説明する。
```

Sprint .3 完了条件:

- 5 件が `.claude/commands/` に存在する
- 各 frontmatter に description が設定されている
- `markdownlint` PASS

### Sprint .4: helix doctor 統合 + bats test (se 委譲)

**Entry**: Sprint .3 完了

実施内容:

1. `cli/helix-doctor` (または `cli/lib/helix_doctor.py`) に `check_slash_commands` を追加
2. check ロジック:
   - `.claude/commands/helix-doctor.md` の存在確認 (必須 5 コマンド)
   - 不在の場合は warn レポート
3. `cli/tests/test_slash_commands.bats` 新規作成:
   - bats test 3 件: check PASS (5 件全存在) / check WARN (1 件不在) / suppress yaml で抑制
4. `bash -n cli/helix-doctor` PASS

Sprint .4 完了条件:

- `helix doctor` 実行後 `check_slash_commands` が pass として表示される
- `cli/tests/test_slash_commands.bats` 全 PASS
- `helix doctor fail 0 件維持

## V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-135-helix-slash-command-registration.md |
| ② 実装 | Sprint .3/.4 で起票 | .claude/commands/helix-*.md / cli/helix-doctor |
| ③ テスト設計 | Sprint .4 entry で策定 | (Sprint .4 内にテスト設計を本 PLAN §テスト設計に追記) |
| ④ テストコード | Sprint .4 で実装 | cli/tests/test_slash_commands.bats |

**双方向 reference**:
- 本 PLAN → 実装コード: generates に `.claude/commands/helix-*.md` 全 5 件を明示
- 実装コード → 本 PLAN: 各 slash command 本文に「設計: PLAN-135」コメントを追記
- 本 PLAN → テストコード: generates に `cli/tests/test_slash_commands.bats` を明示
- テストコード → 本 PLAN: bats test 先頭 comment に「DoD 検証: PLAN-135 §acceptance_criteria」を明示

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `bash -n cli/helix-doctor` PASS (Sprint .4 後)
- [ ] `helix doctor fail 0 件維持`
- [ ] `markdownlint .claude/commands/helix-*.md` PASS (Sprint .3 後)
- [ ] bats test 全 PASS (`cli/tests/test_slash_commands.bats`)
- [ ] セルフレビュー (Sprint .3/.4 完了時)
- [ ] tl-advisor check 完了 (Sprint .2 完了時)

## DoD (Definition of Done)

- [ ] `.claude/commands/helix-doctor.md` / `helix-skill-search.md` / `helix-budget.md` / `helix-sprint-status.md` / `helix-handover-status.md` の 5 件が存在する
- [ ] 各 slash command が description frontmatter を持ち、IDE コマンドリストに表示される
- [ ] `/helix-skill-search "タスク記述"` で `helix skill search "タスク記述"` が Bash で実行される
- [ ] `helix doctor` に `check_slash_commands` が追加され pass として報告される
- [ ] `cli/tests/test_slash_commands.bats` 3 件全 PASS
- [ ] `helix doctor fail 0 件維持`
- [ ] `markdownlint` PASS (5 slash command 全件)
- [ ] WebSearch 3 query 実施済 (本 PLAN §WebSearch 履歴 に記録済)

## carry / リスク

- **`$ARGUMENTS` の空白文字・特殊文字**: `helix skill search "$ARGUMENTS"` で引数に空白を含む場合のクォート処理は Sprint .3 で確認する。必要であれば `eval` ではなく `helix skill search -- $ARGUMENTS` 形式で対処する
- **helix doctor check の粒度**: `check_slash_commands` は warn レベルで実装する。必須 5 コマンドの不在は P2 carry として扱う (fail-close 化は Phase 2 の PLAN で検討)
- **既存コマンドとの責務重複確認**: `/spec` (spec-driven-development) や `/build` (incremental-implementation) は HELIX CLI 直接呼び出しではなくスキル呼び出しなので、`/helix-*` との重複はない。Sprint .1 で再確認する

## 関連 reference

- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は 3 query 実施)
- docs/agent-skills/getting-started.md §Using Commands (slash command 運用の範例)
- docs/agent-skills/README.md (HELIX slash command 一覧の正本)
- PLAN-110 (helix doctor warn 漸減 framework、check_slash_commands 追加は本 PLAN)
- PLAN-124 (helix doctor --json output 標準化、check 出力 format の統一)
