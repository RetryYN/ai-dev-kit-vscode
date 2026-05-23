---
plan_id: PLAN-134
title: helix metrics CLI (session 別 carry / PLAN / commit / agent slot 可視化)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: tl-advisor
    slot_label: "TL adversarial check — metrics 設計 (集計粒度 / helix.db schema 依存) 妥当性確認"
  - role: se
    slot_label: "SE — helix-metrics CLI 実装・helix.db 集計クエリ・python_module 起草"
  - role: qa
    slot_label: "QA — pytest test 設計・期間絞り込みの境界テスト・JSON schema 検証"
  - role: pmo-sonnet
    slot_label: "PMO — FR-V5-MK01 AC との整合確認・metrics 種別の要件 trace"
generates:
  - artifact_type: cli_extension
    path: cli/helix-metrics
  - artifact_type: python_module
    path: cli/lib/metrics_collector.py
  - artifact_type: test
    path: cli/lib/tests/test_metrics_collector.py
dependencies:
  requires: []
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-db
  - docs/plans/PLAN-103-fr-v5-19-20-mk01-mk02-acceptance.md
  - docs/v2/L1-REQUIREMENTS.md
acceptance_criteria:
  - "helix metrics --json が session 別 metrics を JSON で出力する"
  - "metrics 種別: carry_consumed / plans_created / commits_count / agent_slots_used / context_consumption_estimate の 5 種を含む"
  - "helix metrics --since YYYY-MM-DD --until YYYY-MM-DD で期間絞り込みが動作する"
  - "python3 -m py_compile cli/lib/metrics_collector.py PASS"
  - "pytest test_metrics_collector.py 全 PASS"
  - "helix metrics --help で usage が表示される"
  - "FR-V5-MK01 (Northstar Metric) の AC である session carry_consumed 集計が PLAN-103 定義と整合する"
---

# PLAN-134: helix metrics CLI (session 別 carry / PLAN / commit / agent slot 可視化)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 helix.db を参照する新規 CLI の追加** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- helix.db 集計クエリは既存 schema (invocation / skill_usage / plan_registry 等) への
  read-only SELECT のみ。schema 変更なし
- CLI 体系は既存 `cli/helix-*` パターンに準拠
- metrics 種別は PLAN-103 の FR-V5-MK01 AC で定義済の範囲内

## 背景

本 session (2026-05-23) 以降、feedback memory / project memory が大量蓄積し、
「session ごとに何件の carry を消化したか」「PLAN を何件起票したか」「agent slot の
使用状況はどうか」を定量的に把握する手段がない。

現状の問題:

1. **carry 消化の可視化不足**: carry_consumed の実績が memory の文章でしか残らず、
   趨勢 (carry が増えているか減っているか) を数値で追えない
2. **PLAN 起票ペースの把握**: FR-V5-MK01 (Northstar Metric) の AC として
   「session ごとの PLAN 起票数」が必要だが CLI が存在しない (PLAN-103 carry)
3. **agent slot 使用量の最適化**: どの role が多用されているかを把握して
   委譲効率を改善するための基盤が未整備
4. **context 消費量の推定**: session ごとのおおよその context 消費を把握し、
   Opus 週間残量管理 (helix budget status) の補完情報として活用したい

`helix metrics` CLI を導入し、helix.db の既存テーブルから session 別 metrics を
集計・出力する framework を確立する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の新規追加** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- helix.db からの SQLite SELECT 集計は標準 Python sqlite3 module のみ使用
- CLI 体系は既存 `cli/helix-*` (bash dispatch + Python helper) パターンと同型
- metrics 種別は PLAN-103 の FR-V5-MK01/MK02 AC で要件定義済

## metrics 設計

### 集計単位

session 単位を基本集計粒度とする。session は helix.db の `invocation` テーブルの
`session_id` をキーとして識別する。

### 5 種の metrics

| metric 名 | 説明 | 集計元テーブル | 備考 |
|---|---|---|---|
| `carry_consumed` | session 内で status=completed に遷移した task 数 | `plan_registry` / `task_queue` | FR-V5-MK01 AC と対応 |
| `plans_created` | session 内で新規 INSERT された PLAN 数 | `plan_registry` | status 不問 |
| `commits_count` | session 内のコミット数 (推定) | `invocation` (tool=Bash + git commit pattern) | 推定値 |
| `agent_slots_used` | session 内で使用された agent slot の role 別集計 | `agent_slots` | role ごとの count |
| `context_consumption_estimate` | session 内 invocation の input_tokens 合計 (推定) | `invocation` | token_count field がある場合のみ |

### 出力形式

#### JSON (--json フラグ)

```json
{
  "generated_at": "2026-05-23T14:30:00Z",
  "period": {
    "since": "2026-05-01",
    "until": "2026-05-23"
  },
  "sessions": [
    {
      "session_id": "abc123",
      "date": "2026-05-23",
      "carry_consumed": 5,
      "plans_created": 2,
      "commits_count": 3,
      "agent_slots_used": {
        "se": 4,
        "pmo-sonnet": 2,
        "qa": 1
      },
      "context_consumption_estimate": 45000
    }
  ],
  "totals": {
    "carry_consumed": 42,
    "plans_created": 18,
    "commits_count": 31,
    "agent_slots_used": {
      "se": 28,
      "pmo-sonnet": 15
    },
    "context_consumption_estimate": 380000
  }
}
```

#### テキスト (デフォルト)

```
$ helix metrics --since 2026-05-01
Period: 2026-05-01 to 2026-05-23 (23 days, 12 sessions)

Session metrics (newest first):
  2026-05-23 [abc123]:  carry=5  plans=2  commits=3  slots=se:4,pmo:2
  2026-05-22 [def456]:  carry=8  plans=4  commits=6  slots=se:6,pmo:3
  ...

Totals:
  carry_consumed:              42
  plans_created:               18
  commits_count:               31
  agent_slots_used (top 3):   se:28, pmo-sonnet:15, qa:9
  context_estimate (tokens):  380,000
```

### CLI インターフェース

```
helix metrics [OPTIONS]

Options:
  --since YYYY-MM-DD    集計開始日 (default: 30 日前)
  --until YYYY-MM-DD    集計終了日 (default: 今日)
  --session SESSION_ID  特定 session のみ表示
  --json                JSON 形式で出力
  --top N               agent_slots_used の上位 N role のみ表示 (default: 5)
  --help                usage 表示
```

## 実装計画

### Sprint .1: metrics_collector.py 実装 (Codex se 委譲、size M)

実施内容:

1. `cli/lib/metrics_collector.py` 新規作成:
   - `collect_session_metrics(db_path, since, until)` → list[SessionMetrics]
   - `SessionMetrics` dataclass (session_id / date / 5 metric fields)
   - `aggregate_totals(sessions)` → TotalMetrics
   - helix.db の schema 確認後、集計可能な field に限定して SELECT
   - テーブル不在 / field 不在は graceful degradation (0 として扱う)

2. 集計クエリ設計:
   - `carry_consumed`: `SELECT COUNT(*) FROM plan_registry WHERE session_id=? AND status='completed'`
     (または task_queue の completed count、Sprint .1 着手時に schema 確認)
   - `plans_created`: `SELECT COUNT(*) FROM plan_registry WHERE session_id=? AND created_at >= ?`
   - `commits_count`: invocation テーブルを `git commit` pattern で grep (推定)
   - `agent_slots_used`: `SELECT role, COUNT(*) FROM agent_slots WHERE session_id=? GROUP BY role`
   - `context_consumption_estimate`: `SELECT SUM(token_count) FROM invocation WHERE session_id=?`

3. `python3 -m py_compile cli/lib/metrics_collector.py` PASS を mandatory in sprint とする

Sprint .1 完了条件:
- `py_compile` PASS
- `collect_session_metrics` が helix.db から 5 metric を返す

### Sprint .2: helix-metrics CLI bash ディスパッチャ (Codex se 委譲、size S)

実施内容:

1. `cli/helix-metrics` 新規作成 (bash):
   - `--since` / `--until` / `--session` / `--json` / `--top` 引数パース
   - `python3 cli/lib/metrics_collector.py` への委譲
   - `helix metrics --help` 表示

2. `cli/helix` のルーターに `metrics` サブコマンド登録:
   - `cli/helix` の case 文に `metrics)` 追加
   - `docs/commands/index.md` に `helix metrics` エントリ追加

Sprint .2 完了条件:
- `helix metrics --help` で usage 表示
- `helix metrics --json` で JSON 出力
- `helix metrics --since 2026-05-01` で期間絞り込みが動作

### Sprint .3: pytest test + FR-V5-MK01 AC 整合確認 (Codex qa 委譲、size S)

実施内容:

1. `cli/lib/tests/test_metrics_collector.py` 新規作成:
   - `test_collect_session_metrics_basic`: fixture DB で 2 session を集計し結果を検証
   - `test_since_until_filter`: 期間外 session が除外される
   - `test_empty_db_returns_zero`: 空 DB で全 metric が 0
   - `test_aggregate_totals`: 複数 session の totals が正確
   - `test_graceful_degradation_missing_table`: テーブル不在で例外なし
   - `test_agent_slots_group_by_role`: role 別集計が正確

2. PLAN-103 (FR-V5-MK01 AC) との整合確認:
   - pmo-sonnet が PLAN-103 の `carry_consumed` AC 定義を Read し、
     metrics_collector.py の集計ロジックが AC を満たすかを確認
   - 不整合があれば Sprint .1 の集計クエリを修正

Sprint .3 完了条件:
- pytest test 全 case PASS
- pmo-sonnet による FR-V5-MK01 AC 整合確認完了

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/metrics_collector.py` PASS
- [ ] pytest `test_metrics_collector.py` 全 PASS
- [ ] `helix metrics --help` 表示確認
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時、FR-V5-MK01 AC 整合含む)
- [ ] tl-advisor adversarial check (Sprint .1 完了後、集計 schema 依存の妥当性)
- [ ] commit message に `PLAN-134 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `cli/lib/metrics_collector.py` 実装済、`py_compile` PASS
- [ ] `cli/helix-metrics` 実装済、`helix metrics --help` 表示
- [ ] `cli/helix` ルーターに `metrics` サブコマンド登録済
- [ ] `docs/commands/index.md` に `helix metrics` エントリ追加済
- [ ] 5 metrics (carry_consumed / plans_created / commits_count / agent_slots_used / context_consumption_estimate) が集計される
- [ ] `--since` / `--until` 期間絞り込みが動作する
- [ ] `--json` で JSON 出力が動作する
- [ ] pytest test 全 PASS
- [ ] FR-V5-MK01 (PLAN-103) の carry_consumed AC と整合確認済
- [ ] helix doctor pass 数が現行以上

## carry / 学び (起票時記録)

- **helix.db schema 確認必須**: Sprint .1 着手前に `helix db status` または
  `sqlite3 .helix/helix.db ".tables"` で実在テーブルと field を確認する。
  plan_registry / agent_slots / invocation の各テーブルが持つ field は
  migration 版数によって異なる可能性がある
- **commits_count の推定精度**: invocation テーブルの Bash call ログから
  `git commit` pattern を grep する方法は推定であり、実際のコミット数と
  乖離する可能性がある。将来的には git log を直接 parse する実装への移行を
  carry として記録する
- **context_consumption_estimate の精度**: invocation テーブルに token_count field が
  存在しない場合は 0 または null を返す graceful degradation とする。
  field が存在しても input/output token の分離が必要かは Sprint .1 で確認する
- **FR-V5-MK01 AC との整合**: PLAN-103 の accept 時点で carry_consumed の
  定義が変更された場合は本 PLAN の集計クエリも追随する必要がある。
  pmo-sonnet の Sprint .3 確認工程で齟齬を検出する

## 関連 reference

- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- PLAN-103 (FR-V5-MK01/MK02 AC、carry_consumed の要件定義)
- PLAN-MM-001 (V5 framework master plan、metrics は V5 可視化層に位置付け)
- PLAN-087 (Web 検索ガード framework)
- cli/lib/helix_db.py (SQLite access layer、schema 定義の正本)
- cli/helix-db (helix db サブコマンド、metrics との住み分け)
- docs/v2/L1-REQUIREMENTS.md (FR-V5-MK01 要件定義)
