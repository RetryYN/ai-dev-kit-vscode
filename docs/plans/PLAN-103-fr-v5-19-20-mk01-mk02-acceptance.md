---
plan_id: PLAN-103
title: "FR-V5-19/20/MK01/MK02 Acceptance Criteria 確定 + 実装 hint 提示"
status: draft
kind: design
drive: be
layer: L1
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (claude-sonnet-4-6)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — AC 境界判断・Phase 5 スコープ承認・tl-advisor 5 原則遵守確認"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-091 / PLAN-093 scoped extension 接続点確認・drift チェック"
  - role: tl-advisor
    slot_label: "TL adversarial check — schema 設計妥当性・topology 定義・NSM metric 設計 review"
  - role: se
    slot_label: "SE (Phase 5 実装時) — helix.db schema 拡張・CLI 追加・hook 拡張"
generates:
  - artifact_type: doc_update
    path: docs/v2/L1-REQUIREMENTS.md
  - artifact_type: markdown_doc
    path: docs/v2/phase5-fr-v5-ac-definition.md
dependencies:
  requires:
    - PLAN-091
    - PLAN-093
    - PLAN-100
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - docs/v2/L1-REQUIREMENTS.md §3.10
  - docs/v2/CONCEPT.md §10
  - CLAUDE.md §V5 framework 18 要素
  - docs/plans/PLAN-091-v5-framework-core.md
  - docs/plans/PLAN-093-plan-drift-detection-curator.md
acceptance_criteria:
  - "FR-V5-19 AC: rework_count 計測 schema が helix.db に設計され、測定可能な閾値 (default 3 回 / PLAN) が明記されている"
  - "FR-V5-20 AC: hub-spoke / pipeline / parallel の topology 定義と role 重複 fail-close 化の入力仕様が明記されている"
  - "FR-V5-MK01 AC: session_carry_metric table schema が設計され、`helix metrics nsm` CLI の出力フォーマットが仕様化されている"
  - "FR-V5-MK02 AC: CLAUDE.md / SessionStart hook の段階開示レベル (L0=初心者 / L1=通常 / L2=熟練者) と切替機構が明記されている"
  - "4 FR の実装 hint (接続先 PLAN / sprint 構成案 / 想定 size) が本 PLAN に記載されている"
  - "L1-REQUIREMENTS.md §3.10 の AC-V5-19/20/MK01/MK02 placeholder が本 PLAN 起票後に具体的 AC で置換されている"
---

# PLAN-103: FR-V5-19/20/MK01/MK02 Acceptance Criteria 確定 + 実装 hint 提示

## L2 凍結 (ADR snapshot)

本 PLAN は **既存 V5 framework 内拡張 (scoped extension)** であり、新規アーキテクチャ採用を含まない。L2 大局判断が発生した場合 (topology 実装戦略・NSM schema 設計) は Phase 5 起票時に ADR snapshot を別途起票する。本 PLAN 時点では ADR snapshot 不要。

## 背景

L1-REQUIREMENTS §3.10 (line 479) に「FR-V5-19/20/MK01/MK02 は Phase 5 carry のため AC は Phase 5 起票時に確定」と記載されている。Phase 4 (PLAN-100 系) 完遂後の Phase 5 着手を見据え、4 FR それぞれの:

- **AC 詳細** (測定可能な合格基準)
- **実装 hint** (helix.db schema 変更案 / CLI 拡張案 / hook 拡張案)
- **既存 PLAN との scoped extension 接続点**
- **想定 size / 委譲 role**

を本 PLAN で事前確定する。Phase 5 の PLAN 起票時に本 PLAN を参照し、AC を L1-REQUIREMENTS に反映する。

## WebSearch 履歴

本 PLAN は内部 framework 拡張・既存 doc 反映が目的であり、外部新仕様採用を含まない。PLAN-087 ガードレール判定: WebSearch 3 query 不要 (設計 doc ではなく AC 整理文書)。

## FR-V5-19: DORA mirror-multiplier guard (Curator rework rate)

### 機能概要

同一 PLAN への retroactive 修正回数 (rework_count) を helix.db で計測し、閾値超過で WARN を出力する。DORA framework の "Change Failure Rate" の HELIX 内 analog として、PLAN 管理品質を計測する。

### AC 詳細

| AC ID | 合格基準 | 測定方法 |
|---|---|---|
| AC-19-1 | `plan_rework_log` table が helix.db に存在し、plan_id / session_ts / change_type / author field を持つ | `helix doctor --check plan_rework_log` で table 存在確認 |
| AC-19-2 | 同一 PLAN への修正 commit が default 3 回を超えた場合、`helix doctor` が WARN を出力する | `helix doctor` 実行時 warn count に "rework_rate_exceeded" が含まれること |
| AC-19-3 | 閾値は `HELIX_REWORK_WARN_THRESHOLD` env で上書き可能 (default=3) | env 設定後 `helix doctor` で閾値変更が反映されること |
| AC-19-4 | rework_count は commit hook (PostToolUse) で自動インクリメント。手動入力不要 | PLAN.md の Edit 後に plan_rework_log が自動更新されること |
| AC-19-5 | WARN は `helix doctor report` の "quality metrics" section に出力され、fail-close ではなく advisory | helix doctor exit code が 0 のまま WARN が出力されること |

### 実装 hint

**接続先 PLAN**: PLAN-093 (plan-drift-detection-curator) の scoped extension が最小変更。

```sql
-- helix.db 追加 table (v36 candidate)
CREATE TABLE IF NOT EXISTS plan_rework_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id TEXT NOT NULL,
    session_ts TEXT NOT NULL,
    change_type TEXT DEFAULT 'edit',  -- 'edit' | 'status_change' | 'sprint_update'
    author TEXT,
    notes TEXT,
    recorded_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_plan_rework_log_plan_id ON plan_rework_log(plan_id);
```

**CLI hint**: `helix doctor` の check 関数に `check_plan_rework_rate()` を追加 (PLAN-093 の `check_plan_drift` と同型)。

**hook hint**: `posttooluse-plan-auto-register.sh` (PLAN-092) の PostToolUse hook を拡張し、PLAN.md Edit 検出時に plan_rework_log に INSERT する処理を追加。

**想定 size**: S (1-3 file 変更、helix_db.py + helix-doctor + test)。**委譲 role**: se。

---

## FR-V5-20: Multi-agent topology (agent_slots 拡張)

### 機能概要

PLAN frontmatter の `agent_slots` を topology 別 (hub-spoke / pipeline / parallel) に分類し、topology 制約違反 (role 重複 / 不整合 topology) を `helix plan lint --v5` で fail-close 化する。

### topology 定義

| topology | 意味 | 制約 |
|---|---|---|
| `hub-spoke` | PM (hub) が複数 agent を協調制御 | pm-advisor role が必須、role 重複禁止 |
| `pipeline` | agent が順次実行 (A → B → C) | execution_order field 必須、循環禁止 |
| `parallel` | 複数 agent が独立並列実行 | file 衝突禁止 (generates path 重複禁止) |

### AC 詳細

| AC ID | 合格基準 | 測定方法 |
|---|---|---|
| AC-20-1 | `agent_slots` に `topology` field (optional, default="hub-spoke") が追加され、3 値 (hub-spoke / pipeline / parallel) を受け付ける | plan_validator.py で topology enum validation が PASS すること |
| AC-20-2 | role 重複 (同じ role が 2 回以上登場) を `helix plan lint --v5` が fail-close で検出する | `helix plan lint docs/plans/PLAN-103.md` で role 重複 PLAN が fail すること |
| AC-20-3 | pipeline topology で execution_order が未設定の場合、lint が WARN を出力する | pipeline PLAN の exec order 欠落で warn 出力確認 |
| AC-20-4 | parallel topology で generates path が重複した場合、lint が fail-close で検出する | generates 重複 PLAN で lint fail 確認 |
| AC-20-5 | 既存 PLAN (PLAN-091〜102) の agent_slots は topology 未指定でも validation PASS (backward 互換) | 全既存 PLAN が lint --v5 PASS 維持 |

### 実装 hint

**接続先 PLAN**: PLAN-091 (v5-framework-core) の `plan_validator.py` と `cli/lib/plan_validator.py` に topology validation を追加。

```yaml
# frontmatter 拡張案
agent_slots:
  topology: hub-spoke  # optional, default hub-spoke
  agents:
    - role: pm-advisor
      slot_label: "..."
    - role: se
      slot_label: "..."
      execution_order: 1  # pipeline topology 時必須
```

**validation hint**: `check_agent_slots_topology()` を plan_validator.py に追加 (100 行以内)。

**想定 size**: S (plan_validator.py + test + 既存 PLAN retrofit は P3 任意)。**委譲 role**: se。

---

## FR-V5-MK01: Northstar Metric (NSM) — carry consumed/session

### 機能概要

HELIX 開発効率の NSM (Northstar Metric) として `carry consumed/session` を定義し、helix.db `session_carry_metric` table で計測する。`helix metrics nsm` CLI でトレンドを表示する。

### NSM 定義

- **metric 名**: carry_consumed_per_session
- **計算式**: `(セッション開始時の carry 件数 - セッション終了時の carry 件数) / セッション時間 (分)`
- **理想値**: 1 session で carry を net 消化している (= 値 > 0)
- **WARN 基準**: 直近 5 session の移動平均が 0 以下 (carry が増加傾向)

### AC 詳細

| AC ID | 合格基準 | 測定方法 |
|---|---|---|
| AC-MK01-1 | `session_carry_metric` table が helix.db に存在し、session_id / carry_start / carry_end / session_duration_min / carry_delta field を持つ | `SELECT * FROM session_carry_metric LIMIT 1` で schema 確認 |
| AC-MK01-2 | `helix metrics nsm` で直近 10 session のトレンドが ASCII グラフで表示される | コマンド実行後 stdout に trend 行が出力されること |
| AC-MK01-3 | `helix metrics nsm --json` で JSON 出力が可能 (CI 連携用) | JSON output が valid JSON で carry_delta / session_ts field を含むこと |
| AC-MK01-4 | 直近 5 session の移動平均が 0 以下の場合、`helix metrics nsm` が exit code 1 で WARN 表示する | mock data で移動平均 0 以下を simulate して exit code 確認 |
| AC-MK01-5 | SessionStart hook が session 開始時の carry 件数を自動記録する (手動入力不要) | SessionStart hook 発火後に session_carry_metric に行が追加されること |

### 実装 hint

**接続先 PLAN**: PLAN-099 (autonomous-runtime-framework-5layer) の SessionStart hook 拡張が起点。

```sql
-- helix.db 追加 table (v36 candidate)
CREATE TABLE IF NOT EXISTS session_carry_metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    carry_start INTEGER DEFAULT 0,
    carry_end INTEGER,
    session_duration_min REAL,
    carry_delta INTEGER,
    recorded_at TEXT DEFAULT (datetime('now'))
);
```

**CLI hint**: `cli/helix-metrics` (新規 bash script) で `nsm` subcommand を実装。Python helper `cli/lib/metrics_helper.py` (新規) で trend 計算・ASCII グラフ出力。

**想定 size**: M (helix_db.py + helix-metrics + metrics_helper.py + test + SessionStart hook 拡張)。**委譲 role**: se (schema / CLI) + pe (ASCII グラフ軽実装)。

---

## FR-V5-MK02: Progressive disclosure (CLAUDE.md / SessionStart 段階開示)

### 機能概要

CLAUDE.md と SessionStart hook を初心者 → 熟練者で段階開示する。開示レベルを `HELIX_DISCLOSURE_LEVEL` env で制御し、context 過多を防ぐ。Reforge "Bowling Alley framework" の内部 dev tool 翻案。

### 開示レベル定義

| Level | 対象ユーザー | 開示内容 |
|---|---|---|
| L0 (初心者) | HELIX 初体験 | 基本 4 コマンド (init / plan / sprint / test) + フェーズ概要のみ |
| L1 (通常、default) | 日常利用者 | 現行 CLAUDE.md full (変更なし) |
| L2 (熟練者) | HELIX 設計者 | L1 + V5 framework 全詳細 + ADR 索引 + 全 subagent 一覧 |

### AC 詳細

| AC ID | 合格基準 | 測定方法 |
|---|---|---|
| AC-MK02-1 | `HELIX_DISCLOSURE_LEVEL=L0` 設定時、SessionStart hook が L0 用要約メッセージ (500 文字以内) を出力する | env 設定後 hook 発火で stdout 文字数確認 |
| AC-MK02-2 | `HELIX_DISCLOSURE_LEVEL=L1` (default) は現行動作と変化なし (backward 互換) | env 未設定 / L1 設定で既存 bats test 全 PASS |
| AC-MK02-3 | `HELIX_DISCLOSURE_LEVEL=L2` 設定時、SessionStart hook が V5 framework 19 要素 + ADR 索引 URL を追加出力する | env 設定後に L1 比で 10 行以上の追加出力が存在すること |
| AC-MK02-4 | CLAUDE.md に `<!-- DISCLOSURE:L0 --> ... <!-- /DISCLOSURE:L0 -->` マーカーで L0 専用セクションを定義できる | マーカー付き CLAUDE.md で `helix session-start --level L0` が L0 セクションのみ出力すること |
| AC-MK02-5 | `helix disclosure --level L0 preview` コマンドで L0 開示内容を事前確認できる | コマンド実行後に L0 相当出力が stdout に出ること |

### 実装 hint

**接続先 PLAN**: PLAN-099 (SessionStart hook) の拡張。`cli/helix-session-start` または `.claude/hooks/session-start.sh` に level 分岐を追加。

**CLAUDE.md 構造 hint**: 既存 CLAUDE.md を変更せず、`cli/helix-disclosure` (新規 CLI) が level に応じて CLAUDE.md の section を filter して出力する設計が backward 互換かつ最小侵襲。

**想定 size**: M (session-start hook 拡張 + helix-disclosure CLI + CLAUDE.md マーカー追加 + test)。**委譲 role**: se + docs。

---

## 実装 Sprint 構成 (Phase 5 着手時)

本 PLAN はフェーズ **L1 = AC 確定 (design)** であり、L4 実装は Phase 5 の別 PLAN (PLAN-091/093 scoped extension) で実施する。

| Sprint | 内容 | role | 想定 size |
|---|---|---|---|
| Sprint .1 | L1-REQUIREMENTS §3.10 の AC-V5-19/20/MK01/MK02 placeholder を本 PLAN 内容で置換 | docs | XS |
| Sprint .2 | tl-advisor に 4 FR の実装 hint review を依頼、schema / topology 設計の adversarial check | tl-advisor | — |
| Sprint .3 | PLAN-091 / PLAN-093 / PLAN-099 へのスコープ追記 (L4 実装起票前の事前 alignment) | pmo-sonnet | XS |
| Sprint .4 | Phase 5 L4 PLAN 起票 (FR-V5-19 → PLAN-091-ext / FR-V5-MK01 → PLAN-099-ext 等) | pm-advisor | M |

## DoD (Definition of Done)

- [ ] 本 PLAN frontmatter が `helix plan lint --v5` PASS
- [ ] FR-V5-19/20/MK01/MK02 それぞれに測定可能な AC が 5 件以上記載
- [ ] 実装 hint (schema / CLI / hook) が各 FR に記載
- [ ] 接続先 PLAN (PLAN-091 / PLAN-093 / PLAN-099) との scoped extension 接続点が明記
- [ ] L1-REQUIREMENTS §3.10 の AC placeholder が更新 (Sprint .1 完了後)
- [ ] tl-advisor adversarial check 結果が本 PLAN carry / 学び に記録 (Sprint .2 完了後)

## carry / 学び

- **topology 実装で ADR snapshot が必要になるか**: hub-spoke / pipeline / parallel の topology 制約実装が L2 大局判断に相当する場合、Phase 5 起票時に ADR snapshot を PLAN-091 tree に追加する
- **NSM の carry_start 計測タイミング**: SessionStart hook が carry 数を計測するには handover や carry register との連携が必要。PLAN-099 との依存を Phase 5 で整理する
- **Progressive disclosure と CLAUDE.md サイズ**: CLAUDE.md が既に 1000 行超のため L0 filter の実装は parse コストとの兼ね合いを確認必要

## 関連 reference

- L1-REQUIREMENTS §3.10 (FR-V5-19/20/MK01/MK02 定義)
- docs/v2/CONCEPT.md §10 (V5 framework 19 要素)
- PLAN-091 (agent_slots 定義、FR-V5-20 接続先)
- PLAN-093 (drift Curator、FR-V5-19 接続先)
- PLAN-099 (SessionStart hook、FR-V5-MK01/MK02 接続先)
- PLAN-MM-001 (V5 framework master)
