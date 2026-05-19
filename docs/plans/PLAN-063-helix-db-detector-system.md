---
plan_id: PLAN-063
title: "PLAN-063（helix DB 強化: 15 軸 detector + telemetry 基盤）"
status: finalized
created: 2026-05-11
author: "PM (Opus)"
priority: high
size: L
phases_affected: "cli/helix-detect (新規) / cli/lib/* / helix.db v16 / G2/G4/G6 gate / session-start hook"
parent_plan: PLAN-062
acceptance:
  telemetry_foundation:
    verification_commands: { command: "sqlite3 .helix/helix.db 'SELECT type, COUNT(*) FROM invocation_log WHERE timestamp >= date(\"now\", \"-7 days\") GROUP BY type", expected: "5 entrypoint (codex / claude / skill / hook / bash) すべてで ≥1 件記録" }
    entrypoint_list: "5 entrypoint = (1) cli/helix-codex / (2) cli/helix-claude / (3) cli/helix-skill / (4) .claude/hooks/* (PreToolUse/PostToolUse/Stop) / (5) PreToolUse bash auto-mode classifier。subagent type は (4) hook 経路に統合 (Agent tool 自体は v2 で banned のため独立 entrypoint としない)。"
    raw_meta_contract: "raw_meta JSON の保存規約: (a) allowlist 方式で role/model/task_id/plan_id/sprint/decision/cost_cents/duration_ms のみ確実に保存、(b) 任意 free-text フィールドは含めない、(c) prompt 本文 / API key / file content / user secret は禁止フィールドとして必ず redaction (パターン: sk-[a-zA-Z0-9]{20+} / Bearer\\s.+ / token=.+ を regex 削除)、(d) input_bytes/output_bytes はサイズのみ記録し本文は保存しない、(e) G3 までに D-TELEMETRY/redaction-rules.md で詳細仕様 + テスト fixture を凍結。"
  detector_coverage:
    verification_commands: { command: "cli/helix detect --list", expected: "15 軸 (軸 0+14) すべてが implemented で表示、未実装 0 件" }
    mvp_scope: "本 PLAN-063 のスコープは 15 軸完全実装。11 軸 MVP / 4 軸 carry の分割は採用しない (PLAN-064 以降は別 PLAN として独立スコープで切る)。"
  contract_guard_early:
    verification_commands: { command: "cli/helix gate G2 --contract-only", expected: "W-2pre 完了時点で contract_entries.schema_hash 変更検知 → breaking_change_flag=1 caller 列挙 PR comment 自動生成。caller >0 ある breaking change で G2 fail-close" }
    deliverable_3: "(1) contract registry init (D-API/*.yaml bulk scan + schema_hash 計算)、(2) edge extractor init (cli/lib/*.py AST → code_edges)、(3) G2 contract guard 雛形 (PR diff 検知 + caller 列挙)。W-2pre 完了時点で G2 guard が動作開始。"
  gate_integration:
    g2_verification: { command: "cli/helix gate G2 --static-only", expected: "軸 6,7,9-A,9-B,12-A,12-E,12-G を fail-close 評価 (設計凍結時、12-G = 契約破壊検知 W-2pre 由来)" }
    g4_verification: { command: "cli/helix gate G4 --static-only", expected: "軸 1,2,3,4,11,12-B,12-D,12-F を fail-close 評価 (実装凍結時)" }
    g6_verification: { command: "cli/helix gate G6 --static-only", expected: "軸 5,9-E,11-D を fail-close 評価 (RC 判定時)" }
  dashboard:
    verification_commands: { command: "cli/helix detect dashboard --format mermaid", expected: "mermaid 図出力、15 軸 detector の verdict 色分け + invocation_log/code_entries/observe_*/accuracy_score/skill_usage/routing_decisions/detector_runs の 7 テーブル統合 view を表示" }
finalized: 2026-05-11
---

# PLAN-063: helix DB 強化 — 15 軸 detector + telemetry 基盤

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

### Query 1: 設計 doc naming convention industry standard

- Google Developers の Style Guide（`Google Style Guides`）は、命名と文書記述ルールを一貫性重視で定義し、既存の Markdown 文体を維持したまま判定基準を追加する運用上の根拠となる。  
  - https://google.github.io/styleguide/
- Microsoft Learn の Framework Design Guidelines（Naming/GUIDE）も、命名規約を目的別に分け、開発者が即理解できる命名を優先する方針を示す。  
  - https://learn.microsoft.com/en-us/dotnet/standard/design-guidelines/general-naming-conventions
- GitLab Handbook はドキュメントの命名・構造に関して、運用時の衝突回避と一貫した記載を重視する原則を示す。  
  - https://gitlab.com/gitlab-com/content-sites/handbook/-/blob/04b7d02441186f31b2aa87499963b3b8e523bee3/content/handbook/about/style-guide.md

この PLAN は既存の `PLAN-063-helix-db-detector-system.md` という識別子ベースの命名規則を維持し、拡張セクションも既存の章立て（`## §n`）に追加せず、追加トレース性の高いブロックとして独立管理する。

### Query 2: architecture documentation folder structure convention

- arc42 公式資料は、アーキテクチャ文書を再利用しやすい明確な構成（目的・コンテキスト・構成要素・責務）で整理することを基本方針としている。  
  - https://arc42.org/overview
- C4 のモデル説明は、システム分解を Context / Container / Component レベルで階層化する実務的な可視化基準を提供する。  
  - https://en.wikipedia.org/wiki/C4_model
- arc42 資料では、構成内容を階層化してドキュメントへ反映する実践パターンが扱われ、PLAN でも節構造の継続性確認に利用できる。  
  - https://arc42.org/documentation

本 PLAN は現行の `docs/plans/` 直下配置を維持しつつ、`§` 章の意味づけを固定化することで、arc42/C4 の「構造的に理解しやすい分解」の方針と整合する。

### Query 3: ADR PLAN spec doc taxonomy

- ThoughtWorks の Enterprise Architecture Playbook は、ADR を番号付き管理し、`doc/adr/NNNN-...` 形式で追跡性を保つ実務的な分類を示す。  
  - https://www.thoughtworks.com/content/dam/thoughtworks/documents/report/thoughtworks-enterprise-architecture-playbook.pdf
- Mozilla の ADR 文化ガイド（ADR 仕様運用）における共通認識は、決定事項を簡潔に残す軽量化された運用を想定しており、PLAN/ADR の共通ルール化の妥当性を補強する。  
  - https://adr.github.io/
- GitLab のドキュメント/手順文書の運用例は、ADR/仕様文書を他資産と一貫管理する際の粒度設計に有効な実例を与える。  
  - https://gitlab.com/gitlab-org/gitlab/-/tree/51d4c04da9097ad4c153fcbd14dedf3a26b48f81/doc/development/documentation/styleguide

HELIX 採用根拠:
- PLAN 参照は、既存運用の識別子（`PLAN-###`）を維持し、本文は最小差分追加で追記するため、検索・監査可能性を高める。
- フォルダ構造は `docs/plans/` を継続し、追加節の責務を局所化することで他 PLAN との整合性を維持。
- ADR/規約は `docs/adr` 配下既存運用の連携前提を崩さず、PLAN-063 の履歴管理を PLAN 内に閉じることで `PLAN-087` Web 検索ガードレールを満たす。

## §1 背景

PLAN-061/062 で helix code DB の実用性が確認できた:
- LLM 検索が dead code 候補抽出に有効 (代替手段)
- duplicate / coverage gate が機能
- 副次的に実バグ (codex_post_validation:271) 発見

しかし現状の検知は **断片的・手動・1 軸ずつ**。本 PLAN で 15 軸の自動 detector + telemetry foundation を構築し、HELIX を **自己診断 + 自己進化 + 自己可視化** の完全フレームワーク化する。

## §2 15 軸 mapping

```
基盤 (1):   0  Telemetry foundation (invocation_log)
予防系 (5): 6  Naming / 7 Doc drift / 8 Plan integrity / 12 Connection / 14 Orchestration
発生系 (5): 1  Dead / 2 Coverage / 3 Real dup / 9 Refactor / 11 Regression
学習系 (3): 4  Skill decay / 5 PLAN debt loop / 13 Model&Skill analytics
可視化 (1): 10 Relation graph
```

### 軸 0: Telemetry foundation (前提インフラ)

全 detector の input data 基盤。`helix.db v16` に追加:

```sql
CREATE TABLE invocation_log (
  id INTEGER PRIMARY KEY,
  timestamp TEXT NOT NULL,
  type TEXT NOT NULL,           -- codex / claude / skill / subagent / bash / hook
  role TEXT,
  model TEXT,
  task_id TEXT,
  plan_id TEXT,
  sprint TEXT,
  input_bytes INTEGER,
  output_bytes INTEGER,
  duration_ms INTEGER,
  decision TEXT,
  cost_cents REAL,
  parent_invocation_id INTEGER,
  raw_meta JSON
);
CREATE INDEX idx_invocation_plan ON invocation_log(plan_id, task_id);
CREATE INDEX idx_invocation_timestamp ON invocation_log(timestamp);
```

`cli/helix-codex` / `cli/helix-claude` / `cli/helix-skill` の entrypoint で execve 前後に sqlite3 insert (既存 footer audit json を再利用)。env var `HELIX_PARENT_INVOCATION_ID` で委譲ツリー復元。

### 軸 1〜14: detector 詳細

各 detector のデータソース・ルール・接続点は `docs/features/PLAN-063/D-DETECTORS/*.md` に分離記載 (Sprint W-1 で skeleton 生成、各 detector Sprint で本実装)。

## §2.5 既存 view との位置関係

**現状の `helix log report` の限界 (Codex 指摘、2026-05-11)**: summary 基盤が `task_runs / action_logs` に依存しているため、豊富な他テーブル (`code_entries` / `observe_*` / `accuracy_score` / `skill_usage` / `routing_decisions`) を表現できていない。本 PLAN の **軸 10 + dashboard** はこの限界を解消する集約 view として位置づける。

| view | データソース | 用途 |
|---|---|---|
| 既存 `helix log report` | task_runs / action_logs のみ | runtime 実行履歴のみ |
| 本 PLAN `helix detect dashboard` | invocation_log + code_entries + observe_* + accuracy_score + skill_usage + routing_decisions + detector_runs | **全 DB 集約 view**、15 軸 detector verdict を mermaid/HTML で可視化 |
| 本 PLAN `helix code graph` (軸 10) | code_entries + cross-ref (impl↔test↔doc↔db) | コード資産の関連図 |

→ dashboard は単一エンドポイントで HELIX 全体状態を可視化する **正本集約 view**。

## §2.6 契約 + コード間接続表記の取り込み (軸 10 / 12 deep dive)

helix.db v17 で 2 テーブル追加し、契約レジストリと code edges を統一管理:

```sql
CREATE TABLE contract_entries (
  id INTEGER PRIMARY KEY,
  contract_type TEXT NOT NULL,   -- api | db | type | signature | event
  source_path TEXT NOT NULL,
  symbol_id TEXT,                -- code_entries.id への soft link
  version TEXT,
  schema_hash TEXT,
  breaking_change_flag INTEGER DEFAULT 0,
  introduced_plan TEXT,
  raw_spec JSON
);

CREATE TABLE code_edges (
  id INTEGER PRIMARY KEY,
  from_entry_id INTEGER NOT NULL,
  to_entry_id INTEGER,
  to_external_ref TEXT,
  edge_type TEXT NOT NULL,       -- import | call | inherit | sql_query | hook_invoke | event_dispatch | yaml_ref | bash_call
  weight INTEGER DEFAULT 1,
  source_line INTEGER,
  raw_meta JSON
);
```

**5 種 extractor (W-10 内で実装)**

| extractor | 入力 | 出力 edge type |
|---|---|---|
| Python AST | cli/lib/*.py | import / call / inherit |
| Bash trace | cli/helix-* | bash_call / yaml_ref |
| SQL grep | cursor.execute literal | sql_query (table 名) |
| YAML schema | D-API yaml / models.yaml | api endpoint / type signature |
| Hook config | .claude/settings.json + hooks/*.sh | hook_invoke |

**軸 12 拡張 sub** (PLAN-063 既存軸を強化):
- **12-A2 dead edge**: code_edges の to が実在しない (削除済 module への参照)
- **12-B2 contract drift**: contract_entries.schema_hash 変更 vs code_edges.sql_query の table 集合差
- **12-G 契約破壊検知**: contract_entries.breaking_change_flag=1 で caller > 0 検出 → G2 fail-close

**軸 10 拡張**: code_edges を mermaid edge として出力。contract / impl / test / db / PLAN の 5 軸が単一 graph で見える dashboard 統合。

## §2.7 契約 registry 前倒し戦略 (ユーザー指示 2026-05-12)

接続漏れの **70% は契約系** (型 / スキーマ / 関数 signature mismatch) という分析に基づき、契約レジストリを後段 W-10 ではなく **W-2pre として前倒し** する。これにより:

- 後段 detector (軸 7 Doc drift / 軸 12 Connection / 軸 10 Relation) が contract_entries / code_edges を前提として実装できる
- G2 contract guard を最速 W-2pre 完了時点で動作可能化 → PR ごとに「壊れる caller 列挙」を自動提示できる状態を早期確立
- 5 種 extractor のうち契約系 3 種 (Python AST / SQL grep / YAML schema) を最優先実装、残り 2 種 (Bash trace / Hook config) は W-10 で吸収

W-2pre の deliverable 3 件:
1. **contract registry init**: 既存 `docs/features/*/D-API/*.yaml` を bulk scan → contract_entries 投入 + 初期 schema_hash 計算
2. **edge extractor init**: 既存 `cli/lib/*.py` の AST から code_edges bulk insert (import / call / sql_query 3 edge type)
3. **G2 contract guard**: PR diff で contract_entries.schema_hash 変更検知 → `breaking_change_flag=1` 自動付与 → code_edges join で caller 列挙 → `helix gate G2` fail-close で表示

## §3 Sprint 構成 (12 Sprint、size=L)

| Sprint | 内容 | 委譲先 | 並列性 |
|---|---|---|---|
| W-0 | draft + TL R1-R2 + finalize (再 review 含む) | PM | - |
| W-1a | 軸 0 telemetry 基盤 (db schema v16 invocation_log + helix-codex 1 entrypoint instrumentation + redaction-rules.md fixture) | SE | (前提) |
| W-1b | 残 4 entrypoint instrumentation (helix-claude / helix-skill / hooks/* / bash classifier) | SE | W-1a 後 並列可 |
| W-1c | redaction extension + invocation_log 集計 helper + tests | SE | W-1a 後 並列可 |
| **W-2pre** | **契約 registry 前倒し: db schema v17 (contract_entries + code_edges) + 3 種 extractor (Python AST / SQL grep / YAML schema) + G2 contract guard 雛形** | **SE** | **W-1a 後 並列可** |
| W-2 | router `helix detect` CLI + 各 detector skeleton + `D-DETECTORS/*.md` 雛形 | PG | W-1a + W-2pre 後 |
| W-3 | 軸 1,2 dead+coverage detector | PG | W-2 後 並列 |
| W-4 | 軸 3,9 dup+refactor 静的 detector | PG | W-2 後 並列 |
| W-5 | 軸 4,6 skill decay+naming detector | PG | W-2 後 並列 |
| W-6 | 軸 7,8,12 doc drift+plan integrity+connection detector | PG | W-2 後 並列 |
| W-7 | 軸 5,11 PLAN debt loop+regression detector | SE | W-1 + W-2 後 並列 |
| W-8 | 軸 13 model&skill analytics (-A〜-F) | SE | W-1 + W-2 後 並列 |
| W-9 | 軸 14 orchestration integrity detector | SE | W-1 + W-2 後 並列 |
| W-10 | 軸 10 relation graph (Bash trace + Hook config extractor 追加 + mermaid 出力。contract_entries / code_edges は W-2pre で投入済を前提) | SE | W-3〜W-9 全完了後 |
| W-11 | gate 統合 (G2/G4/G6 fail-close) + session-start dashboard + `helix detect dashboard` 集約 view (全 DB テーブル統合: invocation_log + code_entries + observe_* + accuracy_score + skill_usage + routing_decisions + detector_runs) | PG | W-10 後 |
| W-final | 統合検証 + retro + push | Opus | - |

### 並列可否 detail

- W-1a (telemetry schema v16 + helix-codex instrumentation) は全 detector の前提 → 直列必須
- W-1b / W-1c / W-2pre は W-1a 後に 3 並列実行可能 (異なる allowed_files、schema migration は W-1a の v16 / W-2pre の v17 を順次積上げ。W-2pre は v16 を破壊せず CREATE TABLE のみ追加)
- W-2 (router skeleton) は W-1a + W-2pre 両方の依存後に着手 → 直列必須
- W-3, W-4, W-5, W-6 は別 detector ファイル → 完全並列 (4 ワーカー)
- W-7, W-8, W-9 は telemetry (W-1) + router skeleton (W-2) 両方の依存後、別 detector ファイル → 完全並列 (3 ワーカー)。W-2 を飛ばして先行できる先行設計タスクは無いため必ず W-2 後に着手する
- W-10 は全 detector の verdict を集約 → 直列
- W-11 は gate config に触る → 直列

## §4 Acceptance (各 detector)

各 detector は以下の最低 4 つを満たす:
1. `cli/helix detect <axis-name>` で単独実行可能 (exit 0=clean / exit 1=findings あり / exit 2=blocked)
2. `--json` で structured output (timestamp / detector / verdict / findings[] / cost_ms)
3. helix.db `detector_runs` テーブルに記録
4. README または D-DETECTORS/<axis>.md に検知ルール + 期待入力 + サンプル出力を明文化

## §5 Out of Scope

- 軸 10 Stage 3 (HTML force-directed graph、d3.js) → PLAN-064 carry
- AI 自動修正 (detector が候補 fix を生成する) → PLAN-065 carry
- 外部システム連携 (Slack / GitHub Issues 自動起票) → PLAN-066 carry
- PLAN-062 tests-only callers 17 件削除 (本 PLAN scope 外、別 PLAN carry)

## §6 リスク

- **telemetry overhead**: 全 entrypoint で sqlite insert は I/O コスト。回避策: WAL mode + batch insert (5 件まとめて commit)
- **detector false positive 過多**: 早期に flag 機構を入れる (`.helix/detect-config.yaml` で各軸 thresholds 調整可能化)
- **db schema 互換性**: v15→v16 移行で既存 entries を壊さない。Sprint W-1 で migration script + rollback 手順を必須化
- **並列 Sprint の commit 衝突**: 各 detector は独立ファイル (`cli/lib/detectors/<axis>.py`) として分離、テストも独立 dir
- **軸 14-D Concurrency violation 検知の自己適用**: 本 PLAN 自身が 7 軸 detector を並列実装するため、自己テストとしても機能 (dogfooding)

## Revision History

- 2026-05-19 業界 standard 引用 retrofit (W5c-2、PLAN-087 ガードレール準拠)
