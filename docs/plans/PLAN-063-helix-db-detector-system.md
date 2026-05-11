---
plan_id: PLAN-063
title: "PLAN-063（helix DB 強化: 15 軸 detector + telemetry 基盤）"
status: draft
created: 2026-05-11
author: "PM (Opus)"
priority: high
size: L
phases_affected: "cli/helix-detect (新規) / cli/lib/* / helix.db v16 / G2/G4/G6 gate / session-start hook"
parent_plan: PLAN-062
acceptance:
  telemetry_foundation:
    verification_commands: { command: "sqlite3 .helix/helix.db 'SELECT COUNT(*) FROM invocation_log WHERE timestamp >= date(\"now\", \"-7 days\")'", expected: "≥ 1 (helix codex / claude / skill 各経路で 1 件以上記録)" }
  detector_coverage:
    verification_commands: { command: "cli/helix detect --list", expected: "15 軸 (軸 0+14) のうち最低 11 軸が implemented で表示" }
  gate_integration:
    verification_commands: { command: "cli/helix gate G4 --static-only", expected: "軸 1,2,9,11 を fail-close 評価" }
  dashboard:
    verification_commands: { command: "cli/helix detect dashboard --format mermaid", expected: "mermaid 図出力、各 detector の verdict 色分け" }
---

# PLAN-063: helix DB 強化 — 15 軸 detector + telemetry 基盤

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

## §3 Sprint 構成 (11 Sprint、size=L)

| Sprint | 内容 | 委譲先 | 並列性 |
|---|---|---|---|
| W-0 | draft + TL R1-R2 + finalize | PM | - |
| W-1 | 軸 0 telemetry 基盤 (db schema v16 + 5 entrypoint instrumentation) | SE | (前提) |
| W-2 | router `helix detect` CLI + 各 detector skeleton + `D-DETECTORS/*.md` 雛形 | PG | W-1 後 |
| W-3 | 軸 1,2 dead+coverage detector | PG | W-2 後 並列 |
| W-4 | 軸 3,9 dup+refactor 静的 detector | PG | W-2 後 並列 |
| W-5 | 軸 4,6 skill decay+naming detector | PG | W-2 後 並列 |
| W-6 | 軸 7,8,12 doc drift+plan integrity+connection detector | PG | W-2 後 並列 |
| W-7 | 軸 5,11 PLAN debt loop+regression detector | SE | W-1 直列依存 後 並列 |
| W-8 | 軸 13 model&skill analytics (-A〜-F) | SE | W-1 直列依存 後 並列 |
| W-9 | 軸 14 orchestration integrity detector | SE | W-1 直列依存 後 並列 |
| W-10 | 軸 10 relation graph (Stage1+2 cross-ref 抽出 + mermaid 出力) | SE | W-3〜W-9 全完了後 |
| W-11 | gate 統合 (G2/G4/G6 fail-close) + session-start dashboard + `helix detect dashboard` 集約 view (全 DB テーブル統合: invocation_log + code_entries + observe_* + accuracy_score + skill_usage + routing_decisions + detector_runs) | PG | W-10 後 |
| W-final | 統合検証 + retro + push | Opus | - |

### 並列可否 detail

- W-1 (telemetry) は全 detector の前提 → 直列必須
- W-2 (router skeleton) も全 detector の前提 → 直列必須
- W-3, W-4, W-5, W-6 は別 detector ファイル → 完全並列 (4 ワーカー)
- W-7, W-8, W-9 は telemetry 依存だが別 detector ファイル → 完全並列 (3 ワーカー)
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
