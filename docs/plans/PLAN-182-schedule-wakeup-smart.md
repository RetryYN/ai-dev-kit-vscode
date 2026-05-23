---
plan_id: PLAN-182
title: "PLAN-182: ScheduleWakeup smart scheduling (carry consumption rate ベース動的調整)"
kind: refactor
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・PLAN-114 との設計 drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — moving average 実装設計・carry rate 計測精度・budget AND 条件との優先順位"
  - role: se
    slot_label: "SE — carry_consumption_rate.py 実装・runtime_status.py 拡張・helix-runtime heartbeat 更新"
  - role: qa
    slot_label: "QA — carry rate fixture test 全ケース検証・PLAN-114 回帰確認"
generates:
  - artifact_type: python_module
    artifact_path: cli/lib/carry_consumption_rate.py
  - artifact_type: python_module
    artifact_path: cli/lib/runtime_status.py
  - artifact_type: cli_extension
    artifact_path: cli/helix-runtime
  - artifact_type: test
    artifact_path: cli/lib/tests/test_carry_consumption_rate.py
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-182-schedule-wakeup-smart.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-051-schedule-wakeup-smart-decision.md
dependencies:
  parent: PLAN-114
  requires:
    - PLAN-114
  blocks: []
related_adr:
  - ADR-032
  - ADR-041
  - ADR-051
---

# PLAN-182: ScheduleWakeup smart scheduling

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-051** で凍結 (起票予定):

- carry consumption rate ベースの動的 interval 調整採用判断
- moving average 方式の採用 (ML 不要、simple moving average N=5 で充分な精度)
- carry rate と budget / phase の優先順位確定 (rate は低優先、budget/phase が上位)
- `carry_consumption_rate.py` を独立 module として切り出す設計
- PLAN-114 の `calculate_interval()` を拡張する refactor 方針 (破壊的変更なし)

## 1. 目的

**PLAN-114 (adaptive heartbeat、15/30/5 min 3 段階)** の interval をさらに精緻化する。過去 N 時間の carry 消化速度 (carry consumption rate) を moving average で計測し、rate が高いときは短い heartbeat、rate が低いときは長い heartbeat を自動選択する。

| 動機 | 現状 (PLAN-114) | 改善後 (本 PLAN) |
|---|---|---|
| 固定 15min では粒度が粗い | budget と phase のみで判定 | carry rate も加味した動的 fit |
| 連続作業時の polling 過多 | rate 高でも 15min 固定 | rate 高 → 短縮 (最短 10min) |
| 低速作業時の過剰 wake | rate 低でも 15min 固定 | rate 低 → 延長 (最長 30min) |

**ML 不要の設計原則**: carry 消化数の simple moving average で充分。複雑なモデルは本 PLAN のスコープ外。

## 2. 業界 standard 参照 (PLAN-087 ガード遵守)

本 PLAN は既存 framework (PLAN-114) の設計変更を含むため PLAN-087 ガード対象。

| Query | 出典 | 抽出した知見 |
|---|---|---|
| "adaptive polling interval moving average task consumption rate 2026" | ACM Queue / backoff + USENIX NSDI 2011 (Dogar) | SMA N=5〜10 が rate 推定の実装コスト最小。rate 高 → 短縮 / rate 低 → 延長の線形 fit が標準 |
| "agent heartbeat interval rate based dynamic scheduling python 2026" | claw0 scheduler source + Claude Code CHANGELOG 2.1.143-144 | claw0 は固定 15min。rate-aware dynamic は HELIX 独自拡張。Claude Code 側に heartbeat API なし |
| "schedule wakeup dynamic interval carry rate session agent automation 2026" | HELIX PLAN-099 §9 + PLAN-114 + CLAUDE.md §ScheduleWakeup | ScheduleWakeup = 外部状態 polling 専用。dynamic 調整は P0 guard (候補提示のみ) との整合が必須 |

## 3. 設計方針

### 3.1 carry consumption rate の定義

```
carry_rate = (過去 W 時間で消化した carry 件数) / W
単位: 件 / 時間
```

- `W` = 観測ウィンドウ (default: 1 時間、env: `HELIX_CARRY_RATE_WINDOW_H=1`)
- 消化判定: helix.db の `handover` テーブルから status が `completed` または `cancelled` に遷移したレコードを集計
- `W` 時間内に記録なし → carry_rate = 0.0 (rate 不明扱い)

### 3.2 SMA (simple moving average) ベース計算

```python
# cli/lib/carry_consumption_rate.py
# N_WINDOW=5, env: HELIX_CARRY_RATE_SMA_N

def get_carry_rate(window_hours: float = 1.0) -> float:
    """helix.db から N 期間の消化件数を取得して SMA で rate を返す (件/h)。"""
    ...

def get_rate_category(rate: float) -> str:
    """rate を high / normal / low / unknown に分類する。"""
    ...
```

rate カテゴリ閾値:

| カテゴリ | 条件 | 意味 |
|---|---|---|
| high | rate ≥ 3.0 件/h | 活発に作業中 |
| normal | 1.0 ≤ rate < 3.0 件/h | 通常ペース |
| low | 0 < rate < 1.0 件/h | 低速作業 |
| unknown | rate == 0.0 | 計測期間内にデータなし |

閾値は env variable で外部化 (`HELIX_CARRY_RATE_HIGH_THRESHOLD=3.0` 等)。

### 3.3 interval 計算 (PLAN-114 の `calculate_interval()` 拡張)

PLAN-114 の優先順位ルールを維持しつつ、通常 tier (15min) を carry rate で細分化する:

```
優先順位 (高 → 低):
  1. active task 中          → 無効 (PLAN-114 維持)
  2. carry 0 または時間枠満了 → 停止 (PLAN-114 維持)
  3. budget 枯渇             → 停止 (PLAN-114 維持)
  4. critical / hotfix phase → 5 min (PLAN-114 維持)
  5. 低予算 (≤ 30%)         → 30 min (PLAN-114 維持)
  6. carry rate = high       → 10 min  (本 PLAN 追加)
  7. carry rate = normal     → 15 min  (PLAN-114 通常と同値)
  8. carry rate = low        → 20 min  (本 PLAN 追加)
  9. carry rate = unknown    → 15 min  (PLAN-114 通常 fallback)
```

**PLAN-114 破壊的変更なし**: 優先順位 1-5 は完全維持。carry rate は 6-9 の tier 内調整のみ。

### 3.4 `helix runtime status` 拡張

PLAN-114 の `helix runtime status --json` に `carry_rate` フィールドを追加:

```json
{
  "carry": 3,
  "budget_pct": 65.0,
  "bg_task_active": false,
  "phase": "normal",
  "time_window_active": true,
  "carry_rate": 2.1,
  "carry_rate_category": "normal"
}
```

後方互換: `carry_rate` / `carry_rate_category` は PLAN-114 未実装時は `null` を返す (fallback)。

### 3.5 P0 guard (PLAN-114 継承、CRITICAL)

carry rate 調整後も P0 guard は完全維持:
```
heartbeat wake → systemMessage に候補提示のみ
自律 pop は禁止 (TL v5 P0)
承認フロー: PM 承認 → helix job / handover Next Action 経由で実行
```

## 4. 実装計画

### Sprint .1: carry_consumption_rate.py 実装 (Codex se 委譲)

**対象ファイル**: `cli/lib/carry_consumption_rate.py` (新規)

実装内容:
- `get_carry_rate(window_hours: float, sma_n: int) -> float`: helix.db から消化件数集計 → SMA
- `get_rate_category(rate: float) -> str`: high / normal / low / unknown 分類
- env variable: `HELIX_CARRY_RATE_WINDOW_H` / `HELIX_CARRY_RATE_SMA_N` / 閾値 3 変数

mandatory in sprint:
- `python3 -m py_compile cli/lib/carry_consumption_rate.py` PASS

### Sprint .2: runtime_status.py 拡張 + helix-runtime 更新 (Codex se 委譲)

**対象ファイル**: `cli/lib/runtime_status.py` (PLAN-114 成果物を拡張), `cli/helix-runtime` (同)

実装内容:
- `RuntimeStatus` dataclass に `carry_rate: float` / `carry_rate_category: str` フィールド追加
- `get_runtime_status()` 内で `get_carry_rate()` を呼び出し
- `calculate_interval()` に carry rate tier (優先順位 6-9) を追加
- `helix runtime status --json` の出力に `carry_rate` / `carry_rate_category` フィールド追加
- PLAN-114 未実装環境での fallback: `carry_rate=null, carry_rate_category="unknown"`

mandatory in sprint:
- `python3 -m py_compile cli/lib/runtime_status.py` PASS
- `bash -n cli/helix-runtime` PASS
- PLAN-114 T5-001〜T5-007 全ケース regression なし

### Sprint .3: pytest fixture test 実装 (Codex qa 委譲)

**対象ファイル**: `cli/lib/tests/test_carry_consumption_rate.py` (新規)

テストケース:

| ケース | 内容 |
|---|---|
| T1-001 | window_hours=1 の間に 5 件消化 → carry_rate=5.0, category=high |
| T1-002 | window_hours=1 の間に 2 件消化 → carry_rate=2.0, category=normal |
| T1-003 | window_hours=1 の間に 0.5 件 (半分の期間で 0.5 相当) → category=low |
| T1-004 | 計測期間内に消化 0 件 → carry_rate=0.0, category=unknown |
| T2-001 | SMA N=5: 過去 5 期間のカウント [3,2,4,1,5] → SMA=3.0, category=high |
| T2-002 | SMA N=5: 直近 1 期間のみデータあり → N=1 で計算 (window 不足時の fallback) |
| T3-001 | calculate_interval: carry rate=high (≥3.0) + budget 正常 + phase=normal → 10min |
| T3-002 | calculate_interval: carry rate=normal + budget 正常 + phase=normal → 15min (PLAN-114 維持) |
| T3-003 | calculate_interval: carry rate=low + budget 正常 + phase=normal → 20min |
| T3-004 | calculate_interval: carry rate=unknown + budget 正常 + phase=normal → 15min (fallback) |
| T3-005 | calculate_interval: budget ≤ 30% + carry rate=high → 30min (budget 優先、PLAN-114 T5-002 回帰) |
| T3-006 | calculate_interval: HELIX_PHASE=critical + carry rate=low → 5min (phase 優先、PLAN-114 T5-003 回帰) |
| T4-001 | PLAN-114 T5-001〜T5-007 全ケース: runtime_status.py 拡張後も PASS (回帰テスト) |

mandatory in sprint:
- `python3 -m pytest cli/lib/tests/test_carry_consumption_rate.py -v` 全 13 ケース PASS
- `python3 -m pytest cli/lib/tests/test_runtime_heartbeat.py -v` PLAN-114 T5-007 全 PASS (回帰)
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit)

## 5. DoD (Definition of Done)

- [ ] `python3 -m py_compile cli/lib/carry_consumption_rate.py` PASS
- [ ] `python3 -m py_compile cli/lib/runtime_status.py` PASS
- [ ] `bash -n cli/helix-runtime` PASS
- [ ] pytest 全 13 ケース PASS (T1〜T4 carry rate)
- [ ] PLAN-114 T5-001〜T5-007 全 7 ケース回帰 PASS
- [ ] carry rate=high 時に 10min interval を選択 (T3-001 PASS)
- [ ] carry rate=low 時に 20min interval を選択 (T3-003 PASS)
- [ ] budget / phase の優先順位が carry rate より高いこと確認 (T3-005 / T3-006 PASS)
- [ ] `helix runtime status --json` に `carry_rate` フィールドが追加されていること確認
- [ ] PLAN-114 破壊的変更なし (優先順位 1-5 完全維持、T4-001 PASS)
- [ ] ADR-051 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## 6. V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §3 設計方針 / §4 実装計画 |
| ③ テスト設計 | §4 Sprint .3 テストケース一覧 (T1〜T4) |
| ② 実装コード | cli/lib/carry_consumption_rate.py + cli/lib/runtime_status.py + cli/helix-runtime (Sprint .1-.2) |
| ④ テストコード | cli/lib/tests/test_carry_consumption_rate.py (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T 番号明記
- テストコード → 設計: pytest test に `# PLAN-182 T{N}-{NNN}` コメントで対応付け (Sprint .3 実装時)
- テスト設計 → テストコード: test 関数名で T 番号対応 (Sprint .3 実装時)

## 7. 関連 reference

- PLAN-114 (parent — adaptive heartbeat 4 段階、本 PLAN の拡張元)
- PLAN-099 §9 (Layer 5 設計、ScheduleWakeup 発火条件の根拠)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-041 (PLAN-114 の L2 snapshot)
- ADR-051 (本 PLAN の L2 snapshot、起票予定)
- ACM Queue "rate-based scheduling" (SMA window 推奨 N=5〜10)
- CLAUDE.md §ScheduleWakeup 運用ルール (発火条件の HELIX 原則正本)
- CLAUDE.md §TL v5 round 5 修正条件 補助 #8 (adaptive heartbeat、P0 guard)
- [[feedback_dont_stop_with_carry_remaining]] (14h idle 事故の根本原因、本 PLAN の存在理由)
