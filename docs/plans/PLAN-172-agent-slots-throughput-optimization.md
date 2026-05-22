---
plan_id: PLAN-172
title: "PLAN-172: agent_slots throughput optimization (並列上限 8 → 12 段階拡張)"
kind: refactor
layer: L4
drive: be
status: draft
size: M
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — agent_slots.py throughput 計測 + 上限拡張ロジック + helix doctor 監視統合"
  - role: perf
    slot_label: "Perf — bottleneck 分析 (memory / API rate limit) + 段階的上限スケジュール"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-088 との設計整合確認・上限変更影響チェック・G4 review"
generates:
  - artifact_path: cli/lib/agent_slots.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_agent_slots_throughput.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-172-agent-slots-throughput-optimization.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-088
  requires:
    - PLAN-088
  blocks: []
related_plans:
  - PLAN-088-todowrite-agent-slot-framework
  - PLAN-143-helix-db-v37-event-telemetry
related_docs:
  - cli/lib/agent_slots.py
  - cli/helix-agent
  - docs/commands/ai-harness.md
---

# PLAN-172: agent_slots throughput optimization (並列上限 8 → 12 段階拡張)

> **kind**: refactor (agent_slots 並列上限の段階的拡張)
> **layer**: L4
> **drive**: be (Python helper + bash CLI 修正中心)
> **L2 凍結**: 本 PLAN は PLAN-088 で確立した agent slot framework の拡張であり、
> 新 framework 採用ではなくパラメータ調整のため ADR snapshot は不要。

---

## §0. 本 PLAN の位置付け

HELIX の CLAUDE.md は「default 上限 = 8 並列」を規定しており、
`cli/lib/agent_slots.py` がこの上限を実装している。
本 session (2026-05-23) では pmo-sonnet 5 並列 + Codex 4 並列 = 9 が
上限 8 に制約されるケースが複数回発生した。

本 PLAN は現状の上限 8 に至った経緯と bottleneck を計測し、
**段階的に 8 → 10 → 12 へ拡張する framework** を実装する。
PLAN-088 (TodoWrite × agent slot) を parent とし、
slot 管理の可観測性を強化した上で上限値をパラメタライズする。

---

## §1. 目的

1. agent_slots の並列実行数 (同時 in_progress slot 数) を helix.db で計測し、
   bottleneck の実態 (memory 枯渇 / Anthropic API rate limit / context 圧迫) を特定する
2. 上限値を `HELIX_MAX_PARALLEL` 環境変数でオーバーライド可能にし、
   段階的に 8 → 10 → 12 まで拡張できる framework を提供する
3. `helix doctor` に `check_slot_saturation` を追加し、上限貼り付き状態を WARN として検出する
4. 拡張後も CLAUDE.md の「default 上限 = 8」原則は維持し、
   拡張は明示的 opt-in (`HELIX_MAX_PARALLEL=12`) のみで有効化する

---

## §2. 背景

### 2.1 現状の課題

`cli/lib/agent_slots.py` の `MAX_PARALLEL` は定数 `8` でハードコードされている。
以下の状況で上限貼り付きが発生している:

- pmo-sonnet 5 並列 (PLAN retrofit など) + Codex se/pg 4 並列 = 9
- Wave 設計で 8 並列を目標にすると PMO 系が抑制される

上限を超えた依頼は即座に reject されるが、
「何件が上限で止まったか」「上限貼り付き時間は何秒か」を計測する手段がない。

### 2.2 PLAN-088 との関係

PLAN-088 は `agent_type` の prefix 必須化と `in_progress` 件数上限 (Phase 3) を実装した。
本 PLAN はその上限値の **拡張とパラメタライズ** を担当し、
PLAN-088 の audit コマンドに throughput 計測機能を追加する。

### 2.3 拡張の安全性条件

上限拡張は以下がすべて満たされる場合のみ安全:

| 条件 | 確認方法 |
|---|---|
| Anthropic API rate limit に余裕がある | `helix budget status` |
| memory 使用量が 80% 未満 | OS `free` / `vm_stat` |
| 既存 in_progress slot が全て健全 (blocked/stale なし) | `helix agent slots` |

上記が満たされない場合、`HELIX_MAX_PARALLEL` を設定しても上限緩和を拒否する
**adaptive guard** を実装する。

### 2.4 WebSearch skip 理由 (PLAN-087 ガードレール遵守)

本 PLAN は HELIX 内部の定数変更と計測実装であり、外部ライブラリの新規採用なし。
WebSearch **skip**。

---

## §3. 設計方針

### 3.1 上限値のパラメタライズ

```python
# cli/lib/agent_slots.py
import os

_DEFAULT_MAX_PARALLEL = 8
_ABSOLUTE_MAX_PARALLEL = 16  # 安全上限

def get_max_parallel() -> int:
    """環境変数 HELIX_MAX_PARALLEL で上限をオーバーライド。
    adaptive guard が許可した場合のみ default 超過を受け入れる。
    """
    env_val = os.environ.get("HELIX_MAX_PARALLEL")
    if env_val is None:
        return _DEFAULT_MAX_PARALLEL
    try:
        requested = int(env_val)
    except ValueError:
        return _DEFAULT_MAX_PARALLEL
    capped = min(requested, _ABSOLUTE_MAX_PARALLEL)
    if capped <= _DEFAULT_MAX_PARALLEL:
        return capped
    if not _adaptive_guard_passes():
        return _DEFAULT_MAX_PARALLEL
    return capped


def _adaptive_guard_passes() -> bool:
    """budget / memory / stale slot を確認して上限緩和を許可するか判定。"""
    # Phase 1: memory check (80% 未満)
    # Phase 2: stale slot check (blocked/stale 0 件)
    # Phase 3: budget check (helix.db budget 残量)
    ...
```

### 3.2 throughput 計測

`helix.db` の `agent_slots` table に `saturation_events` を記録する。
PLAN-143 の event_log table を活用し、`event_type='slot_saturation'` で書き込む。

```json
{
  "requested_slots": 9,
  "current_max": 8,
  "rejected": 1,
  "timestamp": "2026-05-23T10:00:00Z"
}
```

### 3.3 `helix agent slots` 拡張

```
helix agent slots [--throughput] [--saturation]
```

| サブオプション | 表示内容 |
|---|---|
| `--throughput` | 直近 1h の slot 使用率 (avg / peak / saturation 回数) |
| `--saturation` | 上限貼り付きイベントの一覧 |

### 3.4 `helix doctor` 統合

`check_slot_saturation()` を追加:
- 直近 1h で saturation event が 5 回以上 → WARN
- 直近 1h の peak slot 数が `get_max_parallel()` と一致 → WARN (上限到達)

### 3.5 段階的拡張スケジュール

| Phase | 上限 | 前提条件 |
|---|---|---|
| Sprint .1 | 8 (維持) | 計測基盤実装のみ |
| Sprint .2 | 8 → 10 opt-in | HELIX_MAX_PARALLEL=10 で動作確認 |
| Sprint .3 | 8 → 12 opt-in | saturation 計測で 1 week 安定確認後 |

---

## §4. DoD (Definition of Done)

- [ ] `cli/lib/agent_slots.py` が `get_max_parallel()` / `_adaptive_guard_passes()` /
  `record_saturation_event()` を実装している
- [ ] `HELIX_MAX_PARALLEL=10` 設定時に adaptive guard を通過すれば上限 10 で動作する
- [ ] `helix agent slots --throughput` が saturation 回数と peak 使用率を表示する
- [ ] `helix doctor` が saturation 5 回以上または peak == max で WARN を出力する
- [ ] `cli/lib/tests/test_agent_slots_throughput.py` で T1〜T6 全件 PASS
- [ ] `python3 -m py_compile cli/lib/agent_slots.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_agent_slots_throughput.py -v` 全件 PASS
- [ ] `helix doctor` warn 増加なし (新規 check の warn は正当)
- [ ] PLAN-088 との設計整合確認 (pmo-sonnet レビュー)

---

## §5. 実装計画

### Sprint .1 — 計測基盤 + パラメタライズ

**担当**: SE + Perf

**作業**:
1. `cli/lib/agent_slots.py` 改修:
   - `get_max_parallel()` 実装 (env override + adaptive guard)
   - `_adaptive_guard_passes()` 実装 (memory + stale check)
   - `record_saturation_event(requested, current_max, rejected)` 実装
2. `helix.db` event_log への saturation event 書き込み (PLAN-143 依存)
3. Perf: bottleneck 分析 (memory / API rate limit の実測)
4. `py_compile` PASS 確認

**受入条件**:
- `HELIX_MAX_PARALLEL` 未設定時に get_max_parallel() == 8 を返す
- adaptive guard が memory 80% 超過時に拡張を拒否する
- saturation_event が DB に記録される
- `py_compile` PASS

### Sprint .2 — CLI 拡張 + helix doctor 統合

**担当**: SE

**作業**:
1. `cli/helix-agent` の `slots` サブコマンドに `--throughput` / `--saturation` 追加
2. `cli/helix-doctor` に `check_slot_saturation()` 追加
3. `HELIX_MAX_PARALLEL=10` での動作確認 (手動)
4. `bash -n cli/helix-agent` PASS 確認

**受入条件**:
- `helix agent slots --throughput` が直近 1h の saturation 回数を表示する
- `helix doctor` が saturation 5 回以上で WARN を出力する
- `HELIX_MAX_PARALLEL=10` で上限 10 が有効化される (adaptive guard 通過時)

### Sprint .3 — テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | HELIX_MAX_PARALLEL 未設定時 get_max_parallel | 8 |
| T2 | HELIX_MAX_PARALLEL=10 + adaptive guard pass | 10 |
| T3 | HELIX_MAX_PARALLEL=10 + memory 90% (guard fail) | 8 (fallback) |
| T4 | HELIX_MAX_PARALLEL=20 は _ABSOLUTE_MAX_PARALLEL でキャップ | 16 |
| T5 | record_saturation_event が event_log に書き込む | DB 1 行追加 |
| T6 | check_slot_saturation が saturation 5 回以上で WARN | WARN 出力 |

**受入条件**:
- `pytest cli/lib/tests/test_agent_slots_throughput.py -v` T1〜T6 全件 PASS

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| 上限拡張で Anthropic API rate limit を超過 | Codex 委譲が rate limit エラーになる | adaptive guard の budget check を PLAN-143 event_log の budget_usage と連携。50% 超過で拡張拒否 |
| adaptive guard の誤判定で上限拡張が常に拒否される | HELIX_MAX_PARALLEL 設定が無効化 | `HELIX_FORCE_MAX_PARALLEL=1` バイパス (bypass 時に WARN ログ必須) |
| 上限拡張後に context 枯渇が加速 | 14h idle 事故 ([[feedback_dont_stop_with_carry_remaining]]) 再発リスク | statusLine hook の context % 監視 (PLAN-099 Layer 2) と組み合わせる |
| PLAN-143 未完了時に saturation event 記録不可 | throughput 計測が機能しない | try/except で silent fail。PLAN-143 完了後に自動有効化 |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
