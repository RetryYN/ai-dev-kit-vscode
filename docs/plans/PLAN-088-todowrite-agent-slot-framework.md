---
plan_id: PLAN-088
title: "PLAN-088: TodoWrite × agent slot framework"
layer: L2
status: draft
size: S-M
created: 2026-05-19
revised: 2026-05-19
owner: PM
depends_on:
  - PLAN-087-design-doc-web-search-guardrail
  - PLAN-089-gate-fail-close-design-doc-web-search-audit
related_adr: []
related_docs:
  - .claude/hooks/pretooluse-agent-guard.sh
  - cli/helix-todo
  - cli/lib/todo_parser.py
  - cli/lib/migrations/v34_todo_entries.py
  - .claude/hooks/pretooluse-todowrite-prefix-check.sh
---

# PLAN-088: TodoWrite × agent slot framework

## 1. 目的 / 背景 / 採用根拠

### 1.1 目的

- TodoWrite の content に `[agent_type]` prefix を機械的に必須化し、Codex / PMO / Opus の slot 化を実行時に可観測化する。
- 並列実行時の可視性と衝突回避を強化し、`in_progress` 重複、上限超過、依存不在による待ち行列を削減する。
- PreToolUse フックを用いて作成/更新時の逸脱を早期検知し、最終的に fail-close 化可能な段階的枠組みを作る。

### 1.2 背景

- 本セッション (2026-05-19) で「TodoWrite content に agent prefix 必須」の運用を試行し、並列性上限 8 の達成および追跡性が確認できた。
- 既存の `.claude/hooks/pretooluse-agent-guard.sh` は PMO/PdM 中核 12 種の fail-close を持つが、TodoWrite には未適用だった。
- handover Next Action W2 の要請で Phase 1-4 を統合する。
- 並列実行ルール（上限 8）との監査接続が未整備だった。

### 1.3 採用根拠

- slot を埋めることで混線を低コストで検出する。
- `agent_type` 必須化で監査・履歴・集計を単一化する。
- hook 入口で逸脱を止め、後段修正を減らす。

## 2. 業界 standard 参照

本 PLAN の観点（並列タスク管理・依存可視化・エージェントオーケストレーション・フック/ガード）について、WebSearch ソースを根拠として明記する。

| 参照 | source | 引用用途 |
|---|---|---|
| Linear project dependencies | https://linear.app/docs/project-dependencies | blocking/dependency の視覚化 |
| Trello help: Creating and managing task dependencies | https://support.atlassian.com/trello/docs/creating-and-managing-task-dependencies/ | 代替依存設計の限界比較 |
| Claude Code hooks reference | https://code.claude.com/docs/en/hooks | PreToolUse / PostToolUse のイベント設計 |
| Claude Docs: hooks guide | https://docs.claude.com/en/docs/claude-code/hooks-guide | 実運用の hook 設計指針（matcher, decision, stdout/stderr 取扱い） |
| CrewAI Core Concepts | https://docs.crewai.com/core-concepts/Agents/ | エージェント分業、役割分離、協調実行の基本モデル（agent slot 構想） |
| LangGraph overview | https://docs.langchain.com/langgraph | 状態付き multi-agent / supervisor / routing の業界標準的構成モデル |
| LangGraph Router (Docs) | https://docs.langchain.com/oss/python/langchain/multi-agent/router | ルーティング + 専門 agent へのディスパッチを技術的に言語化 |
| OpenAI Assistants function calling | https://platform.openai.com/docs/assistants/tools/function-calling | 並行 tool call の基本と run state を比較し、tool dispatch の境界を整理 |
| TodoMVC (実装観点) | https://github.com/tastejs/todomvc | タスク状態遷移（todo/アイテム管理）を小規模状態管理例として参照 |

## 3. Phase 1-4 詳細（acceptance criteria / DoD / 試験項目）

### Phase 1: `helix-todo` CLI 新設と `helix.db` v34

#### 目的
- 既存の `cli/helix todo` 系を `cli/helix-todo` へ拡張し、`agent_type` を DB で必須管理。
- `show/add/complete` を最小インターフェースで追加。

#### 作業範囲
- 新規作成: `cli/helix-todo`（入口スクリプトまたはコマンド群）
- Migration 追加: `cli/lib/migrations/v34_todo_entries.py`
- 既存 `todo_entries` テーブル構造の必須列追加（`agent_type`）

#### acceptance criteria
- `agent_type` が空のレコードを DB 層で受け付けない（DB/モデルレベル）。
- `helix-todo add` は prefix 未付与時に CLI 警告を返す。

#### DoD
- `helix.db` v34 がリリース可能状態（現在 schema version と整合）。
- `cli/helix-todo show` で slot/状態集計が表示できる。
- 既知コマンドへの回帰影響がないこと。

#### 試験項目
- T1: 空の `agent_type` で add しようとした時に失敗すること
- T2: `add --agent-type Codex` が作成するエントリを show で検証できること
- T3: complete 後の件数・状態更新が正しいこと

### Phase 2: agent type prefix parse + 自動 dispatch helper

#### 目的
- `cli/lib/todo_parser.py` に prefix 正規化機構を実装し、`[Codex se]` / `[pmo-tech-fork]` / `[Opus bg]` を統一 ID に変換。

#### 作業範囲
- 正規表現ベースの parser 追加
- 未知 prefix の扱いを advisory warn とし、既存データを壊さない

#### acceptance criteria
- 既知 prefix が同値正規化され、`agent_type` に保存。
- 不明 prefix は `warn` のみで継続し `agent_type=unknown:<raw>` を残す。

#### DoD
- 正規化ルールがコード中に集中（単一責務関数に集約）
- parser のユニットテスト仕様が定義済み

#### 試験項目
- T4: `[Codex se]` / `[Codex- se]` / `[codex se]` のノイズを吸収
- T5: 未知 token の warning（処理継続）

### Phase 3: 依存判定 audit

#### 目的
- `cli/helix-todo audit` で同時 in_progress の上限チェックを行う
- `helix doctor check_todo_parallel_violations` による advisory 判定を追加

#### 作業範囲
- `helix-todo` 新規サブコマンド `audit`
- `cli/helix-doctor` に検査関数を追加

#### acceptance criteria
- `in_progress` の同時件数が上限 8 超過時に fail（audit レポート上で明示）
- 依存不明（`blocked_by` が未設定）かつ `in_progress` への遷移を抑止する advisory warning を出力

#### DoD
- `agent_type` / `state` / `blocked_by` 依存を横断した監査レポートを生成
- 閾値は設定値化（将来 8→別値へ変更可能）

#### 試験項目
- T6: 上限 8 で警告なし（正常）
- T7: 上限 9 で audit fail
- T8: 依存 chain が自己循環の場合に `check_todo_parallel_violations` で表示

### Phase 4: PreToolUse hook intercept（4a warn → 4b fail-close）

#### 目的
- `TodoWrite` content の `[agent_type]` prefix 不在をフック段階で検知
- まず advisory warn、次に fail-close へ昇格する 2 段階で導入

#### 作業範囲
- `.claude/hooks/pretooluse-todowrite-prefix-check.sh` 新規作成
- `TodoWrite` tool input を解析し、content 内の prefix 形式を検出
- `cli/.claude/settings.json` 等で登録・適用

#### acceptance criteria
- Phase 4a: 不備レコードがある場合、警告が stderr/stdout に残る
- Phase 4b: fail-close 運用時、prefix 不足で TodoWrite が block される

#### DoD
- 既存 `.claude/hooks/pretooluse-agent-guard.sh` パターンに合わせたログ整形
- bypass 実行時の監査記録（必要時のみ）を残す

#### 試験項目
- T9: prefix あり → hook 通過
- T10: prefix なし + 4a → warn のみ
- T11: prefix なし + 4b → block
- T12: 設定により `Codex` と `PMO` の運用例外を許可できること

## 4. helix.db v34 schema（todo_entries）

```sql
CREATE TABLE IF NOT EXISTS todo_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    content TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    normalized_agent_type TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('pending', 'in_progress', 'blocked', 'done', 'cancelled')),
    blocked_by TEXT,                 -- JSON array of todo_entry ids
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    parallel_slot INTEGER,
    owner TEXT,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_todo_entries_agent_state
  ON todo_entries(agent_type, state);

CREATE INDEX IF NOT EXISTS ix_todo_entries_updated
  on todo_entries(updated_at);
```

補足:
- `agent_type` は空文字不可 (`CHECK(LENGTH(TRIM(agent_type)) > 0)`)。
- `parallel_slot` は将来の視覚化用拡張列。

## 5. CLI 仕様（`cli/helix-todo`）

### 5.1 共通前提

- 対象 DB: `helix.db` v34
- 既定上限: `--max-parallel 8`（環境変数 `HELIX_TODO_MAX_PARALLEL` で上書き）
- 依存表現: `--block` / `--blocked-by` で 1 つ以上受け付け

### 5.2 `show`

- `cli/helix-todo show [--agent-type] [--state] [--json]`
- `in_progress` 件数などの集計、未解決依存を表示

### 5.3 `add`

- `cli/helix-todo add <content> [--agent-type] [--blocked-by ...] [--slot N]`
- `--agent-type` 省略時は content 先頭の prefix を parser で解決

### 5.4 `complete`

- `cli/helix-todo complete <id> [--unlock]`
- `complete` 時に依存関係の遷移可能性を監査
- `--unlock` 指定で依存解除を一括処理

### 5.5 `audit`

- `cli/helix-todo audit [--strict|--json] [--agent-type]`
- `in_progress` 超過、自己循環、未確定依存、prefix 欠損を表示
- Strict 時は非 0 終了コード

## 6. Hook 仕様（`.claude/hooks/pretooluse-todowrite-prefix-check.sh`）

- 対象イベント: `PreToolUse`
- 対象 tool: `TodoWrite`
- matcher: tool `TodoWrite`、`^\[(.+?)\]` で `agent_type` を検知
- 判定:
  1. prefix 未検出は warn/fail 対象
  2. 未知 prefix は warn
  3. `HELIX_TODO_TODOWRITE_FAIL_CLOSE=true` で fail-close
- 監査:
- `~/.helix/hooks/todowrite-prefix.log` に日時・判定・入力・session を追記

運用:
- Phase 4a（initial）：warn しつつ通過
- Phase 4b（成熟）：fail-close 有効化
- bypass: `HELIX_TODO_PREFIX_BYPASS=true` のみ受理。理由必須

## 7. carry / rollback / migration 手順

### carry
- Phase 4 fail-close の有効化は PLAN-089（または次 PLAN）へ carry
- v34 migration 運用ログと rollback 可否の実測は運用ログで追加検証

### rollback
- **非破壊方針**: v34 schema 変更後、ロールバックは `helix.db` の schema downgrade を伴わず、互換 shim で吸収
- 重大障害時:
  1. `pretooluse-todowrite-prefix-check.sh` を一時的に warn-only モードへ
  2. `helix-todo` を read-only 監査モードへ退避
  3. 既存 todo 規約エントリを `agent_type='unknown:legacy'` 補完

### migration
- 新規環境:
  1. migration v34 実行
  2. 運用ルール（prefix）と互換手順を更新
- 既存環境:
  1. 既存 `todo_entries` の prefix 文字列から `agent_type` を抽出
  2. 失敗レコードは修復待ちリストに追加
  3. `helix-todo audit --strict` が初回成功する状態を確認してから 4b へ移行

## 8. V-model 4 artifact trace（設計 / 実装 / テスト設計 / テストコード）

| 層 | 対応 |
|---|---|
| 設計 | `docs/plans/PLAN-088-todowrite-agent-slot-framework.md` |
| 実装 | `cli/helix-todo`, `cli/lib/migrations/v34_todo_entries.py`, `cli/lib/todo_parser.py`, `.claude/hooks/pretooluse-todowrite-prefix-check.sh` |
| テスト設計 | Plan セクション 3（T1-T12） |

## 9. 完了基準

以下を満たすことを最終完了基準とする。

1. `helix.db` v34 migration が定義・レビュー済みで、`todo_entries.agent_type` が必須化されていること
2. CLI `show/add/complete/audit` の仕様が整合し、受入項目を満たすこと
3. `pretooluse-todowrite-prefix-check.sh` が 4a/4b の切替運用可能状態で、対象 event 解析が可能なこと
4. `helix doctor check_todo_parallel_violations` による依存監査が運用に組み込まれること
5. WIP 上限 8 を超える状況で fail 判定が安定すること
6. メモリー/履歴フィードバックの照合:
   - [[feedback_design_doc_web_search_required]]
   - `docs/plans/PLAN-087-design-doc-web-search-guardrail.md`
   - `docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md`

## 10. TODO 残存確認 / リンク整合

- リンク整合: 参照 URL は公式中心を採用。`status` は frontmatter のみ更新し、本文では冪等記述を避ける。
- TODO:
  - [ ] v34 migration の最終 SQL 差分は `cli/lib/migrations/v34_todo_entries.py` 実装時に本 PLANとの列順/型整合を最終検証する
  - [ ] `helix-todo audit` の `strict` 実装を `exit` コード規約に合わせて固定化
  - [ ] Phase 4b fail-close 化の有効化タイミングは PLAN-089 の節と整合して手動で切替
  - [ ] hook ログ保全先（パーミッション・ローテーション）を `.claude/hooks/` 運用ルールへ追加
