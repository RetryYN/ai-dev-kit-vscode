# ADR-026: PostToolUse 自動登録 + helix.db v35 schema 採用判断

## Status

Proposed (2026-05-20)

> proposed (2026-05-20) — PLAN-092 Layer B 起票に伴い snapshot 起票。Accepted 遷移は PM (Opus) + PO 承認後。

## 業界 standard 参照 (Web 検索 3 query、PLAN-087 ガードレール準拠)

### Query 1: "SQLite ATTACH DATABASE multi-database transaction 2026"

**参照 URL (4 件)**:
- https://www.sqlite.org/lang_attach.html — SQLite 公式 ATTACH DATABASE リファレンス
- https://sqlite.org/atomiccommit.html — SQLite atomic commit / multi-file コミット仕様
- https://www.sqlite.org/isolation.html — SQLite isolation levels
- https://www.sqlite.org/wal.html — WAL mode と multi-db considerations

**知見**: SQLite の `ATTACH DATABASE` により同一接続で複数 DB を atomic に操作できる。multi-file commit の特性 (atomiccommit.html §5.3) により、PLAN-093 の drift 検出で `helix.db` と `plan.db` (将来) を cross-check する際に参照 consistent を保証できる。アプリ層の自由 ATTACH を禁止し、migration / projector 内部に限定する設計は ADR-018 (helix.db 6 分離) と整合している。

### Query 2: "event sourcing append-only log database design 2026"

**参照 URL (4 件)**:
- https://www.martinfowler.com/eaaDev/EventSourcing.html — Martin Fowler event sourcing pattern
- https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing — MS Azure architecture patterns
- https://eventstore.com/blog/what-is-event-sourcing/ — EventStore event sourcing 解説
- https://www.confluent.io/learn/event-sourcing/ — Confluent event sourcing overview

**知見**: `failure_log` と `hotfix_incident_log` は過去の状態を再構築可能な append-only event log として設計する。Martin Fowler が示す「event sequence から任意の過去状態を replay できる」特性を活かし、PLAN-093 Curator が失敗パターンを集計・分析する際の入力として使う。`plan_registry` 自体は最新状態を upsert する state-store 設計とし、event sourcing は監査ログ系 table に限定することで更新負荷を適正に保つ。

### Query 3: "Claude Code PostToolUse hook workflow automatic registration"

**参照 URL (3 件)**:
- https://docs.anthropic.com/en/docs/claude-code/hooks — Claude Code hooks 公式ドキュメント
- https://github.com/anthropics/claude-code — Claude Code GitHub repository
- https://docs.anthropic.com/en/docs/claude-code/settings — hooks settings.json 設定リファレンス

**知見**: Claude Code の PostToolUse hook は `settings.json` の `hooks[].matcher` で tool 名 (Write|Edit|MultiEdit 等) を指定し、tool 実行後に shell script を呼び出す。PLAN-090 で確立した `decision: continue` + `systemMessage` 形式の JSON output を本 hook も踏襲することで、Claude がフック実行結果をコンテキストとして受け取り次アクションに活かせる。hook 実行エラーは fail-open (exit 0) とし、Claude の作業を止めない設計が推奨される。

---

## Deciders

- PM: Opus (claude-opus-4-7)
- PO: yoshiyuki0907yn@gmail.com (承認待ち)
- TL-advisor: gpt-5.5 (adversarial check 推奨)

> **agent_slots 語彙 note (PLAN-091 Round 2 整合、2026-05-20)**: 本 ADR に関連する PLAN-092 の `agent_slots` は `role` (ROLE_MAP 30 role slug) + `slot_label` の 2 フィールド形式に統一した。`codex-se` → `role: se`、`codex-dba` → `role: dba`。モデル名 frontmatter 直記は禁止、ROLE_MAP 正本 `cli/ROLE_MAP.md` を参照すること (PLAN-091 §5 agent_slots 定義が frontmatter 語彙正本)。

## Related

| 関連 | 関係 |
|---|---|
| ADR-025-v5-framework-core-decision | 本 ADR の前提。V5 framework matrix・種別・frontmatter 語彙を定義 |
| ADR-018-db-separation-and-event-sourcing | SQLite ATTACH 設計・event sourcing 採用の先行 ADR |
| ADR-009 (hook strategy 参照) | Claude Code hook の一般戦略 |
| PLAN-091-v5-framework-core | frontmatter 語彙の定義元 (read-only 参照) |
| PLAN-092-posttooluse-plan-auto-register | 本 ADR の実装計画 |
| PLAN-087-design-doc-web-search-guardrail | PostToolUse 系列の前駆 |
| PLAN-089-gate-fail-close-design-doc-web-search-audit | PostToolUse gate fail-close |
| PLAN-090-posttooluse-continueonblock-refactor | active guidance loop pattern の確立元 |
| PLAN-093-plan-drift-detection-curator | 本 ADR の schema を read して drift 検出 (後段) |
| PLAN-095-poc-scrum-reverse-matrix | poc_validation_log を read (後段) |

---

## Context

### 問題

HELIX V5 framework では PLAN.md を「self-contained workflow ルール doc」として定義する (V5 要素 #1)。しかし現状では:

1. **PLAN が DB に存在しない**: PLAN.md を作成・更新しても `helix.db` には自動で取り込まれない。`helix plan status` は手動 import に依存する。
2. **drift が検出できない**: PLAN の `generates:` に記載したファイルが実際に生成されたか、`status` が正確に反映されているかを機械的に確認できない。
3. **進捗が handover に集約される**: sprint 進捗は handover CURRENT.json に詰め込まれ、PLAN doc と DB の 2 箇所を手動で同期する必要がある。
4. **agent_slot / dependency の管理**: frontmatter に記述された `agent_slots` / `dependencies` / `generates` が DB に格納されないため、PLAN-093 の Curator 入力・PLAN-095 の PoC matrix 管理が機能しない。

### V5 Layer B の必要性

V5 framework 3 層構造 (CLAUDE.md §V5 framework 3 層構造):

```
[Layer A] 工程・ドキュメント運用ルール整備  ← PLAN-091 が担当 (frontmatter 語彙定義)
[Layer B] helix.db 型ハーネス              ← 本 ADR-026 / PLAN-092 が担当
[Layer C] 連携自動化ハーネス               ← ADR-032 / PLAN-099 が担当
```

Layer B は Layer A の「紙上の規約」を実際の DB データとして実体化する。Layer C の 5-layer 自動走行は Layer B の DB を読んで動作するため、Layer B が確立されないと Layer C も機能しない。

---

## Decision

以下を採用する:

### Decision 1: PostToolUse hook による PLAN.md 自動 parse → plan_registry upsert

Claude Code の PostToolUse hook (matcher: Write|Edit|MultiEdit) を `docs/plans/PLAN-*.md` および `docs/adr/ADR-*.md` への書き込み後に発火させ、`cli/lib/plan_parser.py` が frontmatter を parse して `helix.db v35` の `plan_registry` へ upsert する。

**採用理由**:
- PLAN.md の保存と DB 登録を自動同期することで手動 import の必要をなくす
- PLAN-090 で確立した active guidance loop pattern (decision: continue + systemMessage) を踏襲し、Claude にフック結果を通知する
- fail-open 設計により hook エラーが Claude の作業を止めない

**棄却案 A: 手動 `helix plan import` のみ**:
- 手動実行忘れによる drift が解消されない。PLAN-091 で CLI fail-close 化しても手動 import を強制するのは摩擦が大きい。

**棄却案 B: PostToolUse なし、helix doctor 集約のみ**:
- helix doctor はバッチ実行であり、リアルタイムの状態反映ができない。agent が PLAN.md を Write した直後に plan_registry の状態を参照するユースケース (PLAN-093 Curator) に対応できない。

### Decision 2: helix.db v35 に 10 新規 table を追加する

既存 v33 schema (CURRENT_SCHEMA_VERSION = 33) への変更なしに、v35 として 10 新規 table を `CREATE TABLE IF NOT EXISTS` で idempotent に追加する。

10 table の設計根拠:

| table | 目的 | 設計方針 |
|---|---|---|
| plan_registry | PLAN 中心台帳 | upsert (state-store) |
| plan_dependencies | 依存グラフ | cycle detection 対象 |
| plan_agent_slots | agent 割当 | slot_index で順序保持 |
| plan_references | 参照 doc | ref_type で分類 |
| plan_generates | 生成物 trace | exists_check で drift 検出の入力 |
| sprint_progress | Sprint 進捗 | handover 長文化を抑制 |
| failure_log | 失敗記録 | append-only event sourcing |
| poc_validation_log | PoC 検証 | PLAN-095 が参照 |
| refactor_degrade_pattern | 失敗パターン | PLAN-093 Curator が参照 |
| hotfix_incident_log | インシデント | append-only event sourcing |

**v34 との関係**: PLAN-088 が v34 (`todo_entries`) を使用予定。v34 が実装される前に v35 schema 設計を起票することで並行開発を可能にする。v35 migration は v34 適用後に適用する forward-only migration。

### Decision 3: cycle detection を plan_parser.py で実装し、循環依存を hook で block する

dependencies graph (requires + parent エッジ) の BFS cycle detection を `plan_parser.py` に実装する。循環依存検出時は `decision: block` を返してユーザー (Claude) に修正を求める。

**採用理由**: dependency cycle は PLAN の実行順序が決定不能になる致命的な状態であり、write 時点で即座に検出・阻止することが重要。一方で `blocks` エッジは逆方向参照であるため cycle detection の対象外とする。

### Decision 4: 段階導入 P1 (warning) → P2 (upsert 有効) → P3 (drift gate 接続)

V5 framework TL v5 round 5 修正条件 (CLAUDE.md §TL v5 round 5 修正条件) の重要項目 1 に従い、feature flag / warn-only / fail-close の段階を踏む:

- **P1**: hook 配置 + parse のみ (upsert なし) → warning systemMessage で parse 結果通知
- **P2**: v35 migration 適用 + upsert 有効化 → plan_registry 自動登録開始
- **P3**: PLAN-093 drift gate と plan_generates.exists_check を統合 → drift を fail-close 化

---

## Consequences

### Positive

1. **PLAN 手動管理の解消**: PLAN.md を保存するだけで plan_registry が自動更新され、手動 import の必要がなくなる
2. **drift 検出の基盤確立**: plan_generates の exists_check を PLAN-093 が参照することで、設計 doc と実ファイルの乖離を機械的に検出できる
3. **進捗 trace の DB 化**: sprint_progress が handover CURRENT.json の長文化を抑制し、agent のコンテキスト消費を削減する
4. **Curator 入力の供給**: failure_log / refactor_degrade_pattern が PLAN-093 Curator の分析材料となり、ルール昇格・降格を自動化する基盤を提供する
5. **PLAN-095 PoC matrix の土台**: poc_validation_log が plan_registry と連携し、Scrum × Reverse PoC の追跡基盤を確立する

### Negative

1. **hook 性能影響**: PostToolUse hook は PLAN.md / ADR-*.md の Write 後に毎回 python3 を呼び出す。CLI 起動コストが蓄積する可能性がある。緩和: hook は fail-open で Claude の作業を止めない。重い処理は background に追い出す option を P3 で検討する。
2. **migration コスト**: v34 → v35 の migration は 10 table 追加であり、初回適用時に若干の遅延が発生する可能性がある。緩和: `CREATE TABLE IF NOT EXISTS` で idempotent、所要時間は数秒以内と見込む。
3. **failure_log 容量肥大化**: append-only の failure_log / hotfix_incident_log は削除不可のため、長期運用で容量が増加する。緩和: PLAN-093 で retention policy (N 日超過を archive table に move) を定義する。
4. **PLAN-088 v34 との並行開発リスク**: PLAN-088 が v34 を実装するまで v35 は適用できない (schema_version の forward-only 制約)。緩和: PLAN-092 P2 の有効化は PLAN-088 v34 実装後にスケジュールする。

---

## Implementation Plan

本 ADR は PLAN-092 の L2 大局判断 snapshot である。実装詳細は PLAN-092 §6〜§9 および Sprint 計画を参照。

段階導入:
1. **P1 (hook warning)**: PLAN-092 Sprint .1a〜.2 で実装
2. **P2 (upsert 有効化)**: PLAN-092 Sprint .3 で有効化 (PLAN-088 v34 実装後)
3. **P3 (drift gate 接続)**: PLAN-093 Sprint 内で plan_generates.exists_check と統合

Accepted 遷移条件:
- PLAN-092 DoD 全達成
- PO 承認 (yoshiyuki0907yn@gmail.com)
- `helix plan progress --plan-id PLAN-092` が completed を返すこと

---

## 付記: V5 framework 18 要素との対応

本 ADR が実現する V5 要素:

| V5 要素 | 本 ADR / PLAN-092 での実現 |
|---|---|
| #5 生成物 trace | plan_generates table + artifact_path / artifact_type |
| #6 依存関係 graph | plan_dependencies table + cycle detection |
| #7 agent slot 割当 | plan_agent_slots table |
| #8 PostToolUse 自動登録 | posttooluse-plan-auto-register.sh + plan_registry upsert |
| #10 進捗 trace | sprint_progress table |

残りの V5 要素は ADR-025 (PLAN-091)、ADR-027 (PLAN-093)、ADR-032 (PLAN-099) が担当する。
