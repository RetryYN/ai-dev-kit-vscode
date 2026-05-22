---
plan_id: PLAN-178
title: "PLAN-178: ファイル変更追跡 + edit history framework (helix history)"
kind: impl
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: tl-advisor
    slot_label: "TL — edit_history schema 設計・PostToolUse hook 性能影響 adversarial check"
  - role: se
    slot_label: "SE — helix-history CLI 実装・EditHistoryStore・PostToolUse hook 起草"
  - role: qa
    slot_label: "QA — pytest fixture 設計・hook 非同期記録のテスト・skill 影響度集計テスト"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 PostToolUse hook 群との衝突確認・helix doctor 統合整合"
generates:
  - artifact_path: cli/helix-history
    artifact_type: cli_extension
  - artifact_path: cli/lib/edit_history.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_edit_history.py
    artifact_type: test
  - artifact_path: .claude/hooks/posttooluse-edit-history.sh
    artifact_type: hook
  - artifact_path: cli/lib/migrations/v40_edit_history.py
    artifact_type: schema_migration
dependencies:
  parent: PLAN-MM-001
  requires: []
  blocks: []
related_plans:
  - PLAN-088
  - PLAN-143
  - PLAN-177
related_adr:
  - ADR-056 候補 (edit_history 記録方針 L2 snapshot、本 PLAN 起票後に起票)
related_docs:
  - cli/lib/helix_db.py
  - .claude/hooks/posttooluse-helix-job-enqueue.sh
  - docs/v2/L1-REQUIREMENTS.md
reference_docs:
  - docs/plans/PLAN-088-todowrite-agent-slot-framework.md
  - docs/plans/PLAN-143-helix-db-v37-event-telemetry.md
  - docs/plans/PLAN-177-helix-bench-framework.md
acceptance_criteria:
  - "PostToolUse hook が Edit/Write/MultiEdit 完了時に edit_history を helix.db に記録する"
  - "helix history file <path> がファイル別 edit ストーリー (PLAN_ID / SKILL_ID / 日時) を表示する"
  - "helix history skill <skill_id> が skill 別 edit 件数・対象ファイル一覧を表示する"
  - "helix history plan <plan_id> が PLAN 別 edit 件数・対象ファイル一覧を表示する"
  - "python3 -m py_compile cli/lib/edit_history.py PASS"
  - "pytest test_edit_history.py 全 PASS"
  - "hook が失敗しても Edit/Write 本体はブロックしない (fail-open)"
  - "PLAN_ID / SKILL_ID 未設定環境でも記録が継続し unknown として保存する"
---

# PLAN-178: ファイル変更追跡 + edit history framework (helix history)

## L2 凍結 (ADR snapshot)

本 PLAN tree は PostToolUse hook による edit 追跡の採用と helix.db 記録方針 (fail-open / PLAN_ID / SKILL_ID context 付与) を含む。これらは L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-056 (起票予定) | edit_history 記録方針 (PostToolUse fail-open + context 付与 + helix.db 蓄積) | Proposed |

双方向 trace:
- 本 PLAN → ADR-056: frontmatter `related_adr` + 本 section
- ADR-056 → 本 PLAN: ADR-056 `## Related` に「PLAN-178 (実装 PLAN、本 ADR が L2 凍結する)」を記載

> ADR-056 は本 PLAN の L4 着手前 (G3 通過後) に起票する。WebSearch 3 query 必須 (git blame と外部 audit log の比較 / PostToolUse hook 設計事例 / SQLite append-only log 設計)。

---

## 0. 背景

git log はコミット単位の変更追跡を提供するが、HELIX runtime レベルの文脈—どの PLAN や skill の推挙が特定ファイルの Edit を駆動したか—は記録されない。複数の Codex / PMO が並列動作する環境では、ファイル変更の因果追跡が困難になっており、以下の課題がある:

1. 設計 drift 原因の特定が困難 (どの PLAN 実行が ADR ファイルを変更したか不明)
2. skill 影響度評価ができない (どの skill 推挙が最もファイル変更に直結したか不明)
3. HELIX doctor が警告を出しても変更元 context が追跡できない

本 PLAN は `helix history` CLI と PostToolUse hook を新設し、Edit/Write/MultiEdit 完了時に PLAN_ID / SKILL_ID context 付きで edit_history を記録する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| Git blame / git log --follow | git-scm.com/docs/git-blame | commit 単位追跡の限界と本 framework の差別化根拠 |
| OpenTelemetry trace / span | opentelemetry.io/docs/concepts/signals/traces/ | 因果追跡 (causality chain) の設計思想参照 |
| Audit Log design patterns | cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet | who/what/when/why の 4W 記録規約 |
| SQLite WAL mode | sqlite.org/wal.html | 高頻度 append-only write の concurrency 設計根拠 |
| Claude Code PostToolUse hooks | docs.claude.com/en/docs/claude-code/hooks-guide | hook 設計パターン・fail-open 実装 |

## 2. 設計方針

### 2.1 アーキテクチャ

```
.claude/hooks/posttooluse-edit-history.sh    PostToolUse hook (bash)
  └── Edit / Write / MultiEdit 完了時に起動
        └── cli/lib/edit_history.py           Python ロジック
              ├── EditHistoryStore             helix.db v40 記録
              ├── ContextResolver              PLAN_ID / SKILL_ID を env / phase.yaml から解決
              └── InfluenceAnalyzer            skill 影響度 (edit_count / file_list 集計)

cli/helix-history                            bash dispatcher
  └── history subcommand
        ├── file <path>                      ファイル別 edit ストーリー
        ├── skill <skill_id>                 skill 別影響度
        └── plan <plan_id>                   PLAN 別変更ファイル
```

### 2.2 記録するコンテキスト

| フィールド | 取得元 | 未設定時 |
|---|---|---|
| plan_id | 環境変数 `HELIX_CURRENT_PLAN` / `.helix/phase.yaml` | `unknown` |
| skill_id | 環境変数 `HELIX_CURRENT_SKILL` | `unknown` |
| session_id | 環境変数 `CLAUDE_SESSION_ID` | `unknown` |
| agent_role | 環境変数 `HELIX_AGENT_ROLE` | `unknown` |
| tool_name | PostToolUse `tool_name` フィールド | 必須 |
| file_path | PostToolUse `tool_input.path` フィールド | `unknown` |

### 2.3 skill 影響度の定義

```
influence_score(skill_id) =
    edit_count_by_skill / total_edit_count
```

`helix history skill <skill_id>` は edit_count・unique_file_count・top_5_files を出力する。

### 2.4 fail-open 原則

PostToolUse hook は Edit/Write/MultiEdit の **完了後** に発火する。記録失敗 (DB lock / Python エラー) は stderr に WARN を出力するのみで、元の tool 実行には影響しない。hook は常に exit 0 で終了する。

### 2.5 helix.db v40 schema

```sql
CREATE TABLE IF NOT EXISTS edit_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at  TEXT NOT NULL,       -- ISO 8601 UTC
    session_id   TEXT NOT NULL DEFAULT 'unknown',
    tool_name    TEXT NOT NULL,       -- "Edit" / "Write" / "MultiEdit"
    file_path    TEXT NOT NULL,
    plan_id      TEXT NOT NULL DEFAULT 'unknown',
    skill_id     TEXT NOT NULL DEFAULT 'unknown',
    agent_role   TEXT NOT NULL DEFAULT 'unknown',
    edit_size    INTEGER,             -- lines changed (差分行数、取得可能な場合)
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_edit_history_file
  ON edit_history(file_path, recorded_at);

CREATE INDEX IF NOT EXISTS ix_edit_history_plan
  ON edit_history(plan_id, recorded_at);

CREATE INDEX IF NOT EXISTS ix_edit_history_skill
  ON edit_history(skill_id, recorded_at);
```

## 3. CLI インターフェース

```bash
# ファイル別 edit ストーリー
helix history file <path> [--since YYYY-MM-DD] [--format text|json]

# skill 影響度
helix history skill <skill_id> [--top N] [--format text|json]
helix history skill --all [--sort influence]

# PLAN 別変更ファイル
helix history plan <plan_id> [--format text|json]

# セッション別サマリー
helix history session [<session_id>] [--format text|json]

# 全体統計
helix history stats [--since YYYY-MM-DD]
```

## 4. Hook 仕様 (posttooluse-edit-history.sh)

- 対象イベント: `PostToolUse`
- 対象 tool: `Edit` / `Write` / `MultiEdit`
- 処理:
  1. `tool_input` の `path` を抽出
  2. 環境変数から PLAN_ID / SKILL_ID / SESSION_ID / AGENT_ROLE を解決
  3. `python3 -c "from cli.lib.edit_history import record; record(...)"` で非同期記録
  4. 記録成功/失敗に関わらず exit 0 で終了
- ログ: `~/.helix/hooks/edit-history.log` にサマリー追記 (成功/失敗/unknown context)

## 5. L4 実装 Sprint 計画

### Sprint .1: skeleton + EditHistoryStore + helix.db v40 migration

- Entry: 既存 PostToolUse hook 一覧確認 (衝突チェック)
- 実装: cli/helix-history skeleton + cli/lib/edit_history.py EditHistoryStore + v40 migration
- チェック: py_compile PASS / bats help PASS
- Exit: `edit_history` table が作成される / `helix history --help` が動作する

### Sprint .2: posttooluse-edit-history.sh + ContextResolver

- 実装: PostToolUse hook bash + ContextResolver (env / phase.yaml からの PLAN_ID / SKILL_ID 解決)
- fail-open (exit 0 保証) の実装
- Exit: hook が Edit/Write 完了後に DB へ記録する / unknown context でも記録が継続する

### Sprint .3: CLI サブコマンド + InfluenceAnalyzer

- 実装: `helix history file` / `helix history skill` / `helix history plan` / `helix history stats`
- InfluenceAnalyzer (skill 影響度集計)
- Exit: `helix history file <path>` が edit ストーリーを出力する

### Sprint .4: テスト + レビュー + ドキュメント整合

- pytest test_edit_history.py 全 PASS 確認
- セルフレビュー + pmo-sonnet review
- docs/commands/index.md に helix history コマンド追加
- .claude/settings.json への hook 登録確認
- Exit: acceptance_criteria 全件 PASS

## 6. リスクと緩和策

| リスク | 影響 | 緩和 |
|---|---|---|
| 高頻度 Edit により DB lock 競合が多発 | 記録漏れ / hook WARN 増大 | SQLite WAL mode 有効化 / helix_db.py の既存 lock 設計に準拠 |
| PLAN_ID / SKILL_ID が常に unknown で記録 | 影響度分析が機能しない | SessionStart hook で HELIX_CURRENT_PLAN を phase.yaml から自動設定する運用を推奨 |
| hook が Edit 本体に遅延を与える | 体感速度低下 | Python 起動を `subprocess(background)` に変更、hook timeout 設定 |
| v40 migration 番号が PLAN-177 v39 と競合 | DB 破損 | Sprint .1 で現行 schema version を確認して付番、競合時は v41 に繰り上げ |

## 7. DoD (Definition of Done)

- acceptance_criteria 全件 PASS
- `helix history skill --all --sort influence` が skill 影響度ランキングを出力する
- PostToolUse hook が exit 0 を保証 (fail-open)
- ADR-056 起票済 (L2 凍結)
- docs/commands/index.md に helix history コマンド登録済
