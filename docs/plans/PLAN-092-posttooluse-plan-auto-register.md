---
plan_id: PLAN-092
title: "PLAN-092: PostToolUse 自動登録 + helix.db v35 schema (V5 Layer B)"
layer: cross
kind: impl
status: draft
size: M
drive: be
created: 2026-05-20
revised: "2026-05-20 (Round 3 反映: revised quote + agent_slots opus→pm-advisor)"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・段階導入 P0 承認境界管理・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・整合確認・drift 観点 read-only"
  - role: se
    slot_label: "SE — hook 実装・plan_parser.py・v35 migration"
  - role: dba
    slot_label: "DBA — schema 設計レビュー・cycle detection 検証"
generates:
  - artifact_path: .claude/hooks/posttooluse-plan-auto-register.sh
    artifact_type: hook
  - artifact_path: cli/lib/migrations/v35_plan_registry.py
    artifact_type: python_module
  - artifact_path: cli/lib/plan_parser.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_plan_parser.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-026-posttooluse-plan-auto-register-decision.md
    artifact_type: adr_snapshot
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-MM-001-v5-framework-master-plan
    - PLAN-090-posttooluse-continueonblock-refactor
    - PLAN-087-design-doc-web-search-guardrail
  blocks:
    - PLAN-093-plan-drift-detection-curator
    - PLAN-095-poc-scrum-reverse-matrix
related_adr:
  - ADR-026-posttooluse-plan-auto-register-decision
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - docs/plans/PLAN-088-todowrite-agent-slot-framework.md
  - docs/plans/PLAN-090-posttooluse-continueonblock-refactor.md
  - docs/plans/PLAN-087-design-doc-web-search-guardrail.md
  - cli/lib/helix_db.py (CURRENT_SCHEMA_VERSION=33 正本)
  - cli/ROLE_MAP.md (agent_slots.role enum の正本、30 role 定義)
  - CLAUDE.md §V5 framework 18 要素 #8
  - CLAUDE.md §V5 framework 3 層構造 Layer B
  - helix/HELIX_CORE.md §Sprint Plan 標準構造
acceptance:
  - PostToolUse hook が docs/plans/PLAN-*.md / docs/adr/ADR-*.md への Write|Edit|MultiEdit 後に frontmatter を parse して plan_registry に upsert すること
  - v35 migration が 10 新規 table を CREATE TABLE IF NOT EXISTS で idempotent 作成すること
  - plan_parser.py が cycle detection (dependencies graph) を実施し、循環依存を検出・報告すること
  - fake PLAN.md fixture を使った test が parse / upsert / cycle detection を検証すること
  - 既存 helix_db.py v33 schema および既存 hook に一切変更を加えないこと (デグレ禁止)
  - PLAN-090 active guidance loop pattern 準拠 (decision: continue + systemMessage 結果通知) を hook 内で実装すること
test_design_ref: docs/v2/L4-test-design/PLAN-092-unit-test-design.md
---

# PLAN-092: PostToolUse 自動登録 + helix.db v35 schema (V5 Layer B)

## L2 凍結 (ADR snapshot)

本 PLAN は `docs/adr/ADR-026-posttooluse-plan-auto-register-decision.md` で L2 大局判断を凍結する。

- ADR-026: PostToolUse hook による PLAN.md 自動解析・DB 登録の採用判断
- V5 framework Layer B (helix.db 型ハーネス) の実体化フェーズ

双方向 trace: 本 PLAN → ADR-026 (設計 → L2 凍結)、ADR-026 → 本 PLAN (判断 → 実装計画)

---

## §1. 目的

V5 framework Layer B の核心として、HELIX 工程の中で PLAN.md を Write / Edit するたびに **PostToolUse hook が自動的に frontmatter を解析し `helix.db v35` の `plan_registry` へ upsert する**基盤を構築する。

目的は 3 点:

1. **PLAN 定義の手動管理から機械管理へ**: 従来は `helix plan import` や `helix plan list` を手動実行しなければ PLAN の進捗・依存・agent_slot が DB に存在しなかった。PostToolUse hook を設けることで、PLAN.md を保存した瞬間に自動登録・更新する。
2. **PLAN-093 drift 検出の入力 DB 供給**: drift 検出は `plan_registry` の `generates` フィールドと実ファイルの存在を突合することで機能する。本 PLAN がその DB を確立する。
3. **PLAN-095 PoC matrix 管理の基盤**: `poc_validation_log` table が `plan_registry` の `plan_id` を外部キー参照する前提を確立する。

---

## §2. 背景・課題

### 2.1 現状の課題

現在の HELIX では PLAN.md は docs/plans/ 配下の Markdown として管理されるが、その内容は **DB に取り込まれない**。

結果として以下の問題が発生している:

- `helix plan status` が実 PLAN.md と乖離する (drift)
- agent_slot・dependency・generates が手動転記になり、更新漏れが生じる
- sprint 進捗が handover CURRENT.json に詰め込まれ、長文化する
- PLAN-093 が予定する drift 検出は DB データなしに機能しない

### 2.2 V5 Layer B の位置づけ

V5 framework は 3 層で構成される (CLAUDE.md §V5 framework 3 層構造):

```
[Layer A] 工程・ドキュメント運用ルール整備  ← PLAN-091 が担当
[Layer B] helix.db 型ハーネス              ← 本 PLAN-092 が担当
[Layer C] 連携自動化ハーネス               ← PLAN-099 が担当
```

Layer B は Layer A (PLAN-091 で定義した frontmatter 語彙・種別・matrix) の実体化であり、Layer C (PostToolUse hook による 5-layer 自動走行) の前提となる。

### 2.3 PLAN-087〜090 との連続性

本 PLAN は PostToolUse 系列の第 4 弾である:

| PLAN | PostToolUse 機能 |
|---|---|
| PLAN-087 | 設計 doc Web 検索ガードレール (PreToolUse 主体、PostToolUse で結果通知) |
| PLAN-089 | gate fail-close 審査 (PostToolUse で audit_log upsert) |
| PLAN-090 | active guidance loop (decision: continue + systemMessage) |
| **PLAN-092** | **PLAN.md 自動 parse → plan_registry upsert (本 PLAN)** |

PLAN-090 の `active guidance loop pattern` (decision: continue + systemMessage で Claude に結果を通知する方式) を本 PLAN も踏襲する。

---

## §3. 業界 standard 参照

本 PLAN の設計は以下の業界 standard を参照する。

### 3.1 SQLite ATTACH DATABASE multi-database transaction

**参照 URL**:
- https://www.sqlite.org/lang_attach.html (SQLite 公式 ATTACH DATABASE)
- https://sqlite.org/atomiccommit.html (SQLite atomic commit / multi-file)
- https://www.sqlite.org/isolation.html (SQLite isolation levels)
- https://www.sqlite.org/wal.html (WAL mode + multi-db considerations)

**採用根拠**: v35 migration は `helix.db` 単一 DB への新規 table 追加であり、`ATTACH DATABASE` による multi-db 参照は migration 内部および将来の drift 検出 (PLAN-093) での read で限定使用する。SQLite の atomic multi-file commit 特性 (atomiccommit.html) を前提に、アプリ層の自由 ATTACH を禁止し migration ・projector 内部のみに限定する方針は ADR-018 で確立済みの設計と一貫している。

### 3.2 event sourcing append-only log database design

**参照 URL**:
- https://www.martinfowler.com/eaaDev/EventSourcing.html (Martin Fowler event sourcing)
- https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing (MS Azure patterns)
- https://eventstore.com/blog/what-is-event-sourcing/ (EventStore blog)
- https://www.confluent.io/learn/event-sourcing/ (Confluent event sourcing overview)

**採用根拠**: `failure_log` / `hotfix_incident_log` は append-only (UPDATE/DELETE 禁止) の event sourcing 設計を採用する。Martin Fowler が示すように、event log は過去の状態を再構築可能にし監査証跡を保証する。`plan_registry` 自体は upsert (state-store) 設計だが、`failure_log` は event-sourced として監査可能性を最大化する。

### 3.3 Claude Code PostToolUse hook workflow

**参照 URL**:
- https://docs.anthropic.com/en/docs/claude-code/hooks (Claude Code hooks 公式)
- https://github.com/anthropics/claude-code (Claude Code GitHub)
- https://docs.anthropic.com/en/docs/claude-code/settings (hooks settings.json)

**採用根拠**: Claude Code の PostToolUse hook は tool 実行後に shell script を呼び出す。`matcher` で `Write|Edit|MultiEdit` を指定し、`tool_result.filePath` で対象 file を判定する。PLAN-090 で確立した `decision: continue` + `systemMessage` 形式の JSON 出力を本 hook でも踏襲し、Claude に登録結果を通知する。

---

## §4. V5 framework 担当要素

本 PLAN が実装する V5 18 要素 (CLAUDE.md §V5 framework 18 要素):

| V5 要素 | 本 PLAN の実装 |
|---|---|
| #5 生成物 trace (generates) | plan_generates table に artifact_path / artifact_type を格納 |
| #6 依存関係 graph (dependencies) | plan_dependencies table + cycle detection |
| #7 agent slot 割当 (agent_slots) | plan_agent_slots table |
| #8 PostToolUse hook → helix.db 自動登録 | posttooluse-plan-auto-register.sh + plan_registry upsert |
| #10 進捗 trace | sprint_progress table |

残りの要素 (#1〜4, #9, #11〜18) は PLAN-091 / PLAN-093〜099 が担当する。

---

## §5. helix.db v35 schema (新規 10 table)

**前提**: 既存 `CURRENT_SCHEMA_VERSION = 33` (cli/lib/helix_db.py §246) を変更しない。v35 は PLAN-088 が v34 (`todo_entries`) を使用予定であるため次の空き番号。

### 5.1 plan_registry

PLAN の中心台帳。frontmatter の key 情報を格納し、状態遷移の source of truth となる。

```sql
CREATE TABLE IF NOT EXISTS plan_registry (
    plan_id         TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    kind            TEXT NOT NULL,      -- design/impl/poc/reverse/troubleshoot/refactor/retrofit/research/add-design/add-impl/recovery
    layer           TEXT NOT NULL,      -- cross / L0〜L11 / comma-separated
    drive           TEXT NOT NULL,      -- be/fe/fullstack/scrum/reverse/db/agent/poc/troubleshoot
    status          TEXT NOT NULL DEFAULT 'draft',  -- draft/active/blocked/completed/cancelled
    size            TEXT,               -- S/M/L
    owner           TEXT,
    related_adr     TEXT,               -- comma-separated ADR ids
    frontmatter_json TEXT NOT NULL,     -- 全 frontmatter を JSON 文字列で保持 (柔軟な追加 field 対応)
    doc_path        TEXT NOT NULL,      -- docs/plans/PLAN-NNN-*.md
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_plan_registry_status ON plan_registry(status);
CREATE INDEX IF NOT EXISTS idx_plan_registry_kind ON plan_registry(kind);
```

### 5.2 plan_dependencies

依存関係グラフ。cycle detection の対象。

```sql
CREATE TABLE IF NOT EXISTS plan_dependencies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    dep_type        TEXT NOT NULL,      -- requires / parent / blocks
    dep_plan_id     TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, dep_type, dep_plan_id)
);
CREATE INDEX IF NOT EXISTS idx_plan_deps_plan_id ON plan_dependencies(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_deps_dep_plan_id ON plan_dependencies(dep_plan_id);
```

### 5.3 plan_agent_slots

agent_slots frontmatter の展開。role / model ごとに 1 行。

```sql
CREATE TABLE IF NOT EXISTS plan_agent_slots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    role            TEXT NOT NULL,      -- ROLE_MAP 30 role slug 準拠: opus / pmo-sonnet / se / dba / tl-advisor 等 (cli/ROLE_MAP.md 正本)
    slot_label      TEXT,               -- frontmatter agent_slots.slot_label の表示名 (role の補足説明)
    slot_index      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plan_slots_plan_id ON plan_agent_slots(plan_id);
```

### 5.4 plan_references

related_docs / related_memories の参照先を格納。

```sql
CREATE TABLE IF NOT EXISTS plan_references (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    doc_path        TEXT NOT NULL,
    section         TEXT,               -- §N や line 番号など任意
    ref_type        TEXT NOT NULL DEFAULT 'related_docs',  -- related_docs / related_memories / test_design_ref
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_plan_refs_plan_id ON plan_references(plan_id);
```

### 5.5 plan_generates

generates frontmatter の展開。artifact ごとに 1 行。

```sql
CREATE TABLE IF NOT EXISTS plan_generates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    artifact_path   TEXT NOT NULL,
    artifact_type   TEXT NOT NULL,      -- cli_extension / python_module / test / hook_shell / template / adr_snapshot / migration
    exists_check    INTEGER NOT NULL DEFAULT 0,  -- 0: 未確認 / 1: 存在 / 2: 不在 (drift 検出で更新)
    last_checked_at TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, artifact_path)
);
CREATE INDEX IF NOT EXISTS idx_plan_generates_plan_id ON plan_generates(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_generates_artifact ON plan_generates(artifact_path);
```

### 5.6 sprint_progress

Sprint 単位の進捗 trace。handover CURRENT.json の長文化を抑制する。

```sql
CREATE TABLE IF NOT EXISTS sprint_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         TEXT NOT NULL,
    sprint_id       TEXT NOT NULL,      -- "Sprint .1a" / "Sprint .1b" / "Sprint .2" 等
    status          TEXT NOT NULL DEFAULT 'not_started',  -- not_started / in_progress / completed / blocked / skipped
    completed_files TEXT,               -- comma-separated 完了ファイルリスト
    blocker_note    TEXT,
    session_id      TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE CASCADE,
    UNIQUE (plan_id, sprint_id)
);
CREATE INDEX IF NOT EXISTS idx_sprint_progress_plan_id ON sprint_progress(plan_id);
CREATE INDEX IF NOT EXISTS idx_sprint_progress_status ON sprint_progress(status);
```

### 5.7 failure_log

append-only の失敗・エラー記録。event sourcing 設計 (UPDATE/DELETE 禁止)。

```sql
CREATE TABLE IF NOT EXISTS failure_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT,
    failure_type    TEXT NOT NULL,      -- hook_error / parse_error / cycle_detected / migration_fail / sprint_blocked / gate_fail
    context         TEXT,               -- エラー詳細 (JSON or 自由文)
    plan_id         TEXT,               -- 関連 PLAN (optional)
    recovery_plan_id TEXT,             -- kind=recovery の PLAN id (optional)
    severity        TEXT NOT NULL DEFAULT 'warn',  -- info / warn / error / critical
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    -- append-only: UPDATE / DELETE 禁止
);
CREATE INDEX IF NOT EXISTS idx_failure_log_session ON failure_log(session_id);
CREATE INDEX IF NOT EXISTS idx_failure_log_type ON failure_log(failure_type);
CREATE INDEX IF NOT EXISTS idx_failure_log_created ON failure_log(created_at);
```

### 5.8 poc_validation_log

Scrum × Reverse PoC 検証記録。PLAN-095 が参照する。

```sql
CREATE TABLE IF NOT EXISTS poc_validation_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id   TEXT NOT NULL,
    scrum_type      TEXT NOT NULL,      -- hypothesis-test / tech-spike / design-spike / perf-spike / security-spike / ux-spike
    reverse_type    TEXT,               -- code / design / upgrade / normalization / fullback (決定後)
    plan_id         TEXT,               -- 関連 PLAN
    result          TEXT NOT NULL,      -- pending / confirmed / rejected / pivot
    evidence        TEXT,               -- 検証結果の根拠
    forward_layer   TEXT,               -- Forward HELIX 接続先 (L1/L2/L3/L4)
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES plan_registry(plan_id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_poc_validation_hypothesis ON poc_validation_log(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_poc_validation_result ON poc_validation_log(result);
```

### 5.9 refactor_degrade_pattern

PLAN-093 Curator が失敗パターンを分析するための基礎データ。

```sql
CREATE TABLE IF NOT EXISTS refactor_degrade_pattern (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id      TEXT UNIQUE NOT NULL,
    trigger         TEXT NOT NULL,      -- hook_name / cli_command / 状況説明
    description     TEXT,
    escalation_level TEXT NOT NULL DEFAULT 'warn',  -- ignore / warn / error / block
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    promoted_at     TEXT,               -- warn → error 等の昇格日時
    demoted_at      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_degrade_pattern_id ON refactor_degrade_pattern(pattern_id);
CREATE INDEX IF NOT EXISTS idx_degrade_escalation ON refactor_degrade_pattern(escalation_level);
```

### 5.10 hotfix_incident_log

本番相当 (critical / hotfix) インシデントの記録。append-only。

```sql
CREATE TABLE IF NOT EXISTS hotfix_incident_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id     TEXT UNIQUE NOT NULL,
    severity        TEXT NOT NULL,      -- sev1 / sev2 / sev3
    title           TEXT NOT NULL,
    root_cause      TEXT,
    recovery_ref    TEXT,               -- recovery kind PLAN id
    resolved_at     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    -- append-only: UPDATE/DELETE は severity/resolved_at を除き禁止
);
CREATE INDEX IF NOT EXISTS idx_hotfix_incident_id ON hotfix_incident_log(incident_id);
CREATE INDEX IF NOT EXISTS idx_hotfix_severity ON hotfix_incident_log(severity);
```

---

## §6. PostToolUse hook 実装方針

### 6.1 hook 概要

```
ファイル: .claude/hooks/posttooluse-plan-auto-register.sh
matcher:  Write|Edit|MultiEdit (PostToolUse)
対象:     tool_result の filePath が docs/plans/PLAN-*.md または docs/adr/ADR-*.md
処理:     frontmatter parse → plan_parser.py 呼び出し → plan_registry upsert
出力:     decision: continue + systemMessage (登録結果)
```

### 6.2 hook フロー

```
PostToolUse (Write|Edit|MultiEdit 完了後)
  ↓
1. tool_result.filePath を取得
2. PLAN-*.md または ADR-*.md にマッチするか判定
   └─ 非対象 → exit 0 (pass-through)
3. python3 cli/lib/plan_parser.py <filepath> --mode upsert を呼び出す
4. 戻り値を受け取る
   ├─ success → systemMessage: "plan_registry 登録完了: {plan_id} (status: {status})"
   ├─ parse_error → systemMessage: "WARNING: frontmatter parse 失敗 ({filepath})"
   └─ cycle_detected → systemMessage: "ERROR: dependency cycle 検出 ({plan_id} → ... → {plan_id})"
5. JSON 出力: {"decision": "continue", "systemMessage": "<上記メッセージ>"}
```

### 6.3 PLAN-090 active guidance loop pattern 準拠

PLAN-090 (PostToolUse continueOnBlock active guidance loop) で確立したパターンに従い、本 hook も以下の出力形式を使う:

```json
{
  "decision": "continue",
  "systemMessage": "plan_registry 登録完了: PLAN-092 (status: draft, dependencies: 5, generates: 5)"
}
```

`decision: block` は原則使用しない。登録失敗は warning systemMessage で Claude に通知し、Claude が次のアクションを判断する。ただし cycle detection で循環依存が検出された場合は `decision: block` を使い、修正を促す:

```json
{
  "decision": "block",
  "message": "dependency cycle detected: PLAN-092 → PLAN-091 → PLAN-092. 循環依存を解消してから再保存してください。"
}
```

### 6.4 hook の fail-open 設計

hook 実行中のエラー (python3 未インストール / helix.db 未初期化 / plan_parser.py 例外) は `exit 0` の fail-open とし、`failure_log` に記録したうえで `systemMessage` で警告を返す。hook のエラーで Claude の作業が中断されないことを優先する。

---

## §7. cli/lib/plan_parser.py

### 7.1 責務

- PLAN.md / ADR-*.md の YAML frontmatter を parse して dict に変換する
- dependencies / agent_slots / generates の構造化
- helix.db v35 の plan_registry / plan_dependencies / plan_agent_slots / plan_generates へ upsert
- cycle detection (dependencies graph で directed cycle 検出、業界 standard は **DFS + recStack** を推奨、BFS Kahn's algorithm (in-degree 0 削減方式) も同等可)

### 7.2 主要関数 (public API)

```python
def parse_frontmatter(filepath: str) -> dict:
    """YAML frontmatter を parse して dict を返す。非 PLAN file は空 dict を返す。"""

def upsert_plan(conn, frontmatter: dict, doc_path: str) -> dict:
    """plan_registry および関連 table に upsert する。戻り値: {plan_id, status, counts}"""

def detect_cycle(conn, plan_id: str) -> list[str]:
    """dependencies graph で directed cycle を検出。循環パス list を返す (空なら cycle なし)。
    実装は DFS + recStack 推奨 (業界 standard)、BFS Kahn's algorithm 代替可。test_design_ref §3.3 参照"""

def main(filepath: str, mode: str = "upsert") -> int:
    """CLI エントリポイント。mode: upsert / check / validate"""
```

### 7.3 cycle detection アルゴリズム

業界 standard (GeeksforGeeks / W3Schools / IEEE algorithms 多数) に従い、directed graph (PLAN dependencies) の cycle detection は以下 2 方式のいずれかで実装する。本書 test_design_ref `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` §3.3 と整合。

**方式 A: DFS + recStack (推奨、業界 standard)**

```
1. plan_dependencies から requires / parent エッジを全取得し adjacency list を構築
2. visited set と recStack (recursion stack) set を維持
3. 各 plan_id を起点に DFS で再帰探索
4. dep_plan_id が recStack にある場合 → directed cycle detected (back edge)
5. DFS 完了時に plan_id を recStack から削除 (sibling 探索のため visited は維持)
6. 検出した cycle パスを list で返す
```

**方式 B: BFS Kahn's algorithm (代替、topological sort 利用)**

```
1. 全 plan_id の in-degree (依存される数) を計算
2. in-degree=0 の node を queue に入れる
3. queue から node を取り出し、出辺先の in-degree を 1 減らす
4. in-degree=0 になった node を queue に追加
5. 全 node を処理後、未処理 node が残る場合 → cycle detected
6. cycle に含まれる plan_id (未処理) を list で返す
```

実装時にいずれかを選択 (Sprint .1b で確定)。本書 test 設計は spec 抽象度 (`detect_cycle` 関数の入出力契約) で検証し、内部アルゴリズム実装には依存しない。

blocks エッジは cycle detection の対象外 (blocks は逆方向参照であり、PLAN-A.blocks=[PLAN-B] は PLAN-B.requires=[PLAN-A] と等価で重複)。

---

## §8. migration v35 (cli/lib/migrations/v35_plan_registry.py)

### 8.1 方針

- 10 table を `CREATE TABLE IF NOT EXISTS` で idempotent に作成する
- `INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (35, datetime('now'))` で version 記録
- PLAN-088 が v34 を使用予定のため v35 が次の空き (v34 は PLAN-088 実装後に確定)
- 既存 v33 schema への変更は一切行わない (デグレ禁止)

### 8.2 migration 順序

既存 PLAN-084〜088 が実装する v31〜v34 の後に v35 を適用する。migration は forward-only (rollback は v35 table DROP による undo migration として別途対応)。

### 8.3 既存 PLAN-001〜090 の retrofit

v35 migration は schema 追加のみ。既存 PLAN の plan_registry への取り込みは **PLAN-100 (retrofit) で別 task** として実施する。本 migration は新規 table 作成のみで PLAN-100 への入力を提供する。

---

## §9. 段階導入計画

### Phase 1 (P1): hook 配置 + warning モード

- `.claude/hooks/posttooluse-plan-auto-register.sh` を配置
- `settings.json` に PostToolUse hook を登録 (matcher: Write|Edit|MultiEdit)
- `plan_parser.py` は parse のみ (DB upsert なし)
- 出力: systemMessage で parse 結果を warning 表示
- 目的: hook が正常に起動することを確認し、parse エラーを発見する

### Phase 2 (P2): plan_registry 自動登録

- v35 migration を適用 (10 table 作成)
- plan_parser.py に upsert 機能を追加
- PostToolUse 後に plan_registry / plan_dependencies / plan_agent_slots / plan_generates への upsert を有効化
- cycle detection を有効化
- テスト: fake PLAN.md fixture で upsert / cycle detection を検証

### Phase 3 (P3): drift gate 接続

- PLAN-093 の helix doctor check と plan_generates の exists_check を統合
- sprint_progress の CLI 参照 (helix plan progress --plan-id PLAN-NNN) を追加
- `failure_log` を helix doctor の警告集計に統合

---

## §10. テスト戦略

### 10.1 単体テスト (cli/lib/tests/test_plan_parser.py)

V-model テスト設計 (詳細は docs/v2/L4-test-design/PLAN-092-unit-test-design.md 起票予定):

| テスト ID | 対象関数 | 内容 |
|---|---|---|
| U-092-001 | parse_frontmatter | 正常 PLAN.md から frontmatter dict を parse できる |
| U-092-002 | parse_frontmatter | ADR-*.md から frontmatter dict を parse できる |
| U-092-003 | parse_frontmatter | frontmatter なし file で空 dict を返す |
| U-092-004 | upsert_plan | plan_registry に新規 upsert できる |
| U-092-005 | upsert_plan | plan_registry に既存 plan_id を update (upsert) できる |
| U-092-006 | upsert_plan | plan_dependencies に requires/parent/blocks を正確に展開できる |
| U-092-007 | upsert_plan | plan_generates に artifact list を展開できる |
| U-092-008 | detect_cycle | 循環依存なし の場合に空 list を返す |
| U-092-009 | detect_cycle | A→B→A の循環依存を検出して cycle パスを返す |
| U-092-010 | detect_cycle | A→B→C→A の 3 段循環を検出できる |

### 10.2 統合テスト

- fake helix.db (`:memory:` SQLite) + v35 migration 適用 → upsert → detect_cycle の一連フロー
- PostToolUse hook smoke: `echo '{"tool":"Write","tool_result":{"filePath":"docs/plans/PLAN-092-test.md"}}' | bash .claude/hooks/posttooluse-plan-auto-register.sh`

---

## §11. DoD (完了条件)

Sprint Exit 前に以下を全通過すること:

- [ ] `.claude/hooks/posttooluse-plan-auto-register.sh` 配置 + settings.json 登録
- [ ] `cli/lib/plan_parser.py` 実装 (parse / upsert / cycle_detect / main)
- [ ] `cli/lib/migrations/v35_plan_registry.py` 実装 (10 table CREATE TABLE IF NOT EXISTS)
- [ ] `cli/lib/tests/test_plan_parser.py` 実装 (U-092-001〜010 全通過)
- [ ] `python3 -m py_compile cli/lib/plan_parser.py cli/lib/migrations/v35_plan_registry.py` PASS
- [ ] 既存 `cli/lib/tests/` の全回帰テスト PASS (デグレなし確認)
- [ ] PostToolUse hook smoke test PASS
- [ ] `docs/adr/ADR-026-posttooluse-plan-auto-register-decision.md` 起票完了

---

## §12. V-model 4 artifact trace

本 PLAN の 4 artifact:

| Artifact | ファイル |
|---|---|
| ① 設計 | 本 PLAN-092 §5〜§9 |
| ② 実装コード | `.claude/hooks/posttooluse-plan-auto-register.sh` / `cli/lib/plan_parser.py` / `cli/lib/migrations/v35_plan_registry.py` |
| ③ テスト設計 | `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` (起票予定) |
| ④ テストコード | `cli/lib/tests/test_plan_parser.py` |

双方向 trace:
- 本設計 → ② 実装: `generates` frontmatter に明示
- 本設計 → ③ テスト設計: `test_design_ref` frontmatter で `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` を明示 (Sprint .1a 着手前に起票完了、V-model TDD pair freeze 遵守)
- ③ テスト設計 → 本設計: `docs/v2/L4-test-design/PLAN-092-unit-test-design.md` §0 で「対応 ① 設計 doc: PLAN-092 §5 §7」明示済
- ④ テストコード → ③ テスト設計: test docstring に「DoD 検証: U-092-001〜010」明示予定

---

## §13. 実装 Sprint 計画

### Sprint .1a: plan_parser.py 基礎実装

- cli/lib/plan_parser.py (parse_frontmatter / upsert_plan 基礎)
- cli/lib/migrations/v35_plan_registry.py (10 table CREATE)
- テスト U-092-001〜005

### Sprint .1b: cycle detection + テスト完備

- plan_parser.py detect_cycle 実装
- テスト U-092-006〜010
- py_compile / 全回帰確認

### Sprint .2: PostToolUse hook 実装

- .claude/hooks/posttooluse-plan-auto-register.sh
- settings.json PostToolUse 登録
- hook smoke test

### Sprint .3: Phase 2 有効化 + 検証

- v35 migration 適用確認
- upsert 有効化
- cycle detection 有効化
- 全テスト通過確認

### Sprint .4: ADR-026 起票 + DoD 全確認

- ADR-026 起票完了確認 (別 file で既に起票)
- DoD チェックリスト全通過
- pmo-sonnet 整合チェック

---

## §14. 関連 PLAN / ADR

| 関連 | 関係 |
|---|---|
| PLAN-MM-001 | 親 PLAN |
| PLAN-091 | frontmatter 語彙・matrix を定義 (本 PLAN は read-only 参照) |
| PLAN-087 | PostToolUse 系列の前駆、設計 doc Web 検索ガードレール |
| PLAN-089 | PostToolUse 系列、gate fail-close |
| PLAN-090 | PostToolUse active guidance loop pattern (本 PLAN が踏襲) |
| PLAN-088 | v34 schema 定義 (v35 は次の空き) |
| PLAN-093 | 本 PLAN の plan_generates / failure_log を read して drift 検出 |
| PLAN-100 | 既存 PLAN-001〜090 を plan_registry へ retrofit (本 PLAN の schema を前提) |
| PLAN-095 | poc_validation_log を read |
| ADR-026 | 本 PLAN の L2 大局判断 snapshot |
| ADR-018 | SQLite ATTACH 設計方針 (本 PLAN が踏襲) |
