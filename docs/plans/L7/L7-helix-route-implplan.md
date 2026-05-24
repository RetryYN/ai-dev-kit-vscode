---
plan_id: L7-helix-route-implplan
title: "L7-helix-route-implplan: helix-route CLI 実装 — 検出シグナル → モード自動ルーティング (P1 修正版 v2)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/detection-routing.md
pairs_test_design:
  - HELIX-workflows/helix-process/automation-gate-map.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・スコープ確認・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check・責務分担確認 (route/recover 境界、Incident kind 分岐、degradation 分離)"
  - role: se
    slot_label: "SE — cli/helix-route + cli/lib/route_engine.py + test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 確認・整合チェック"
generates:
  - artifact_path: cli/helix-route
    artifact_type: cli_extension
  - artifact_path: cli/lib/route_engine.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_route_engine.py
    artifact_type: test
  - artifact_path: cli/tests/helix-route.bats
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - HELIX-workflows/helix-process/cross-detection.md
  - cli/helix-detect
  - cli/lib/detectors/registry.py
  - cli/helix-doctor
  - cli/helix
  - docs/plans/L7/L7-helix-recover-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md)
> **本 PLAN の対象**: `cli/helix-route` を新規実装し、`helix detect run --json` が出力する検出シグナル (drift / debt_degradation / regression / runaway / incident / unknown_design) を受け取り、SIGNAL_TO_MODE 固定マップで対応モード (Recovery / Incident / Reverse / Refactor) を決定 + 4 象限評価で priority/action を付与して PLAN 起票 / helix-recover 連携を suggest する CLI を提供する。
> **位置づけ**: integration-map.md §結論と優先順位 **#2** 「コマンド 2 件のうち 2 件目」。detection-routing.md の設計仕様を CLI として実体化する最初の実装 PLAN。
> **本 v2 で確立**: mode は signal で固定、4 象限は priority/action のみ付与 (mode 上書き禁止)。Incident は env で recovery/troubleshoot 分岐。helix-recover との接続は suggest_command schema で実体化。

### parent_design (draft status) を採用する理由

`detection-routing.md` の frontmatter status は `draft` のまま。これは HELIX-workflows が正本化直後 (commit ee1a13a) であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。SE 実装時は親設計を変更しない。

### tl-advisor 第 1 ラウンド指摘の反映 (本 v2 で P1×4 全解消 + P2 主要反映)

| # | tl-advisor 指摘 | 本 v2 での反映 |
|---|---|---|
| P1-1 | `from_detect_output` 入力 schema 未定義 | §2.B: `helix detect run --json` の `[{detector, status, result}, ...]` 形式に凍結。cross-detection / dashboard / route_events は別 adapter (本 PLAN scope 外) |
| P1-2 | Incident kind 片落ち (P0 高位は recovery が必要) | §2.A: `incident` シグナルは `env` 引数 (prod/dev) で kind=recovery (prod) または kind=troubleshoot (dev) に分岐 |
| P1-3 | helix-recover 連携未接続 | §2.A: suggest_command schema に `--condition <id>` `--reopen-point <SHA>` `--auto-routed-from helix-route` を含め、recover の非対話契約と合わせる |
| P1-4 | degradation 曖昧 (Refactor / Incident / Recovery 区別なし) | §2.A: `debt_degradation` (Refactor) と `regression_prod` (Incident) / `regression_dev` (Recovery) に分離、旧 `degradation` は deprecation warning 付き alias |
| P2-1 | 4 象限評価 mode 上書き危険 | §2.E: mode は SIGNAL_TO_MODE で固定、4 象限は priority/action のみ付与 (`drift+high/high` でも Reverse のまま、P0 付与) |
| P2-2 | CLI 表記揺れ (`helix route --signal` vs `helix route eval --signal`) | §2.C: `helix route eval --signal` に統一、subcommand 必須 |
| P2-3 | テスト 8 件不足 | §2.D: 16 unit + 6 bats に拡張 (fixture / stdin / invalid / incident 分岐 / recover 連携 / list-signals / degradation alias warning) |
| P2-4 | DoD `helix commands check` workspace docs drift で fail | §2.A: route 用 scoped check 追加 (`helix commands check --filter route,recover` 想定、または `docs/commands/index.md` への route 行追加で drift fix) |
| P3-1 | `suggest` サブコマンド曖昧 | §2.C: `suggest` を廃止、`eval --format command` に統合 (eval が JSON / eval --format command が string) |
| P3-2 | `unknown_design` の集計閾値未定義 | §2.A: 単発 signal として処理、集計 (多発) は cross-detection 側で集計済シグナルとして input する設計 (本 PLAN は単発のみ) |

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 設計読み込み (detection-routing.md 精読 + helix detect 実機 JSON 確認 + registry.py 確認) | PM | ✅ done |
| 2 | route_engine.py インタフェース設計 (input schema / SIGNAL_TO_MODE / priority/action / Incident env 分岐 / recover 連携) | PM | ✅ done (§2.B) |
| 3 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | ✅ done (needs_revision、本 v2 で P1×4 + P2 主要解消) |
| 4 | tl-advisor adversarial check 第 2 ラウンド | PM → TL | □ pending |
| 5 | TL 第 2 ラウンド指摘反映 (もしあれば) | PM | □ pending |
| 6 | SE 委譲: cli/helix-route + cli/lib/route_engine.py 実装 | PM → SE | □ pending |
| 7 | test_route_engine.py + helix-route.bats 実装 (§2.D) | SE | □ pending |
| 8 | bash -n / py_compile / pytest / bats 全 PASS | SE | □ pending |
| 9 | helix ルーター登録 + docs/commands/index.md 追記 + helix commands check PASS | SE | □ pending |
| 10 | pmo-sonnet 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 11 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A 設計判断 (SIGNAL_TO_MODE / 4 象限 / Incident 分岐 / degradation 分離)

#### SIGNAL_TO_MODE 固定マップ (本 v2 拡張版)

| signal | mode | kind | subtype | 備考 |
|---|---|---|---|---|
| `drift` | Reverse | reverse | normalization | 設計 ⇔ 実装 drift |
| `debt_degradation` | Refactor | refactor | — | コード劣化・負債 (親設計) |
| `regression_prod` | Incident | recovery | — | 本番デグレ (P0 重大) |
| `regression_dev` | Recovery | recovery | — | 開発中デグレ (認識ズレ) |
| `runaway` | Recovery | recovery | — | AI 暴走・独断専行 |
| `incident` | Incident | (env 依存) | — | env=prod → recovery / env=dev → troubleshoot |
| `unknown_design` | Reverse | reverse | code | 設計不明箇所 (単発) |
| `degradation` (alias) | (warning) | — | — | deprecation warning: "use debt_degradation or regression_{prod,dev}" |

**重要**: mode は signal で **固定**。4 象限評価では mode を上書きしない (P2-1 解消)。

#### Incident の env 分岐 (P1-2 解消)

```python
def evaluate(self, signal: str, uncertainty: str = "low", impact: str = "low",
             env: str = "dev") -> dict:
    ...
    if signal == "incident":
        if env == "prod":
            mode, kind = "Incident", "recovery"   # 本番障害は recover 主体
        else:
            mode, kind = "Incident", "troubleshoot"  # 開発中は hotfix 主体
```

#### 4 象限評価 → priority/action 付与 (P2-1 解消、mode 上書き禁止)

mode は SIGNAL_TO_MODE で固定、4 象限は priority/action のみ付与:

| uncertainty | impact | priority | action |
|---|---|---|---|
| low | low | P3 | suggest_only (記録のみ、起票任意) |
| low | high | P1 | immediate_plan_draft (即時 PLAN 起票) |
| high | low | P2 | discovery_first (Discovery/Scrum 先行) |
| high | high | P0 | emergency_routing (緊急起動 + helix-recover/incident 連携) |

mode は SIGNAL_TO_MODE で決定、priority は 4 象限で決定、両者は独立。`drift + high/high` でも mode=Reverse のまま、priority=P0 を付与する (Incident に上書きしない)。

#### suggest_command schema (P1-3 解消、recover 連携)

evaluate() の戻り値:

```json
{
  "signal": "runaway",
  "mode": "Recovery",
  "kind": "recovery",
  "subtype": null,
  "priority": "P0",
  "action": "emergency_routing",
  "env": "dev",
  "source_schema": "helix_detect_run_json_v1",
  "suggest_command": "helix recover plan --condition runaway --reopen-point HEAD --auto-routed-from helix-route",
  "recover_args": {
    "condition_id": "runaway",
    "reopen_point": "HEAD",
    "auto_routed_from": "helix-route"
  },
  "plan_hint": "AI 暴走検出 (high uncertainty + high impact)。helix recover で Recovery 起動を推奨。"
}
```

signal=runaway / regression_dev / incident(prod) のとき suggest_command は `helix recover plan ...` を返す (recover 連携)。
signal=drift / debt_degradation / regression_dev (低 priority) のとき suggest_command は `helix plan draft --kind <kind>` を返す (plan draft 経由)。

### §2.B cli/lib/route_engine.py 設計 (input schema 凍結版)

```python
# cli/lib/route_engine.py
# @helix:index id=route-engine.evaluate domain=cli/lib summary=検出シグナルを mode 固定 + priority 4 象限評価でルーティング決定

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot"]
Priority = Literal["P0", "P1", "P2", "P3"]
Action = Literal["suggest_only", "immediate_plan_draft", "discovery_first", "emergency_routing"]
Severity = Literal["low", "high"]
Env = Literal["prod", "dev"]


class RouteEngineError(ValueError):
    """未登録 signal / invalid uncertainty/impact"""


@dataclass
class RouteResult:
    signal: str
    mode: Mode
    kind: Kind
    subtype: str | None
    priority: Priority
    action: Action
    env: Env
    source_schema: str
    suggest_command: str
    recover_args: dict | None       # signal が recover 連携時のみ
    plan_hint: str


class RouteEngine:
    """検出シグナル → モード振り分け (detection-routing.md §連携フロー 実装)"""

    SIGNAL_TO_MODE: dict[str, dict] = {
        "drift":             {"mode": "Reverse",  "kind": "reverse",      "subtype": "normalization"},
        "debt_degradation":  {"mode": "Refactor", "kind": "refactor",     "subtype": None},
        "regression_prod":   {"mode": "Incident", "kind": "recovery",     "subtype": None},
        "regression_dev":    {"mode": "Recovery", "kind": "recovery",     "subtype": None},
        "runaway":           {"mode": "Recovery", "kind": "recovery",     "subtype": None},
        # incident は env 依存、evaluate() 内で kind 決定
        "incident":          {"mode": "Incident", "kind": "_env_dependent", "subtype": None},
        "unknown_design":    {"mode": "Reverse",  "kind": "reverse",      "subtype": "code"},
    }

    DEPRECATED_ALIAS: dict[str, str] = {
        "degradation": "debt_degradation or regression_{prod,dev}",
    }

    def evaluate(self, signal: str, uncertainty: Severity = "low",
                 impact: Severity = "low", env: Env = "dev",
                 reopen_point: str = "HEAD") -> RouteResult:
        """単発シグナル評価。mode は SIGNAL_TO_MODE で固定、priority は 4 象限で決定"""

    def from_detect_output(self, detect_run_json: dict | list) -> list[RouteResult]:
        """`helix detect run --json` の出力 (detector/status/result 形式) を一括評価"""

    def list_signals(self) -> list[dict]:
        """登録済シグナル + alias + 各 mode/kind を list で返す"""
```

**入力 schema 凍結 (P1-1 解消)**: `from_detect_output` は **`helix detect run --json` 形式** のみ受ける:

```json
[
  {"detector": "axis_01_drift", "status": "drift", "result": {"uncertainty": "low", "impact": "high", "env": "dev"}},
  {"detector": "axis_07_runaway", "status": "runaway", "result": {"uncertainty": "high", "impact": "high", "env": "prod"}}
]
```

cross-detection / dashboard / route_events など他形式は **別 adapter** で対応 (本 PLAN scope 外、`L7-helix-route-cross-detection-adapterplan` 候補)。

### §2.C cli/helix-route シェルスクリプト + subcommand (P2-2/P3-1 解消、表記統一)

```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/helix-common.sh"
exec python3 "$SCRIPT_DIR/lib/route_engine.py" "$@"
```

subcommand 構成 (`eval --format` で suggest を統合):

| subcommand | 説明 |
|---|---|
| `helix route eval --signal <type> [--uncertainty low/high] [--impact low/high] [--env prod/dev] [--reopen-point <SHA>]` | 単発シグナル評価、JSON 出力 (default) |
| `helix route eval --signal <type> --format command` | suggest_command 文字列のみ stdout に出力 (旧 `suggest` 統合) |
| `helix route eval --from-json <path>` または `--from-json /dev/stdin` | `helix detect run --json` 形式を一括評価 |
| `helix route list-signals [--json]` | 登録済シグナル + alias 一覧 |
| `helix route help` | 使い方 |

helix ルーター登録 (cli/helix への追加):
```bash
route)    exec "$SCRIPT_DIR/helix-route" "$@" ;;
```

`docs/commands/index.md` に route 行追加 (P2-4 解消: `helix commands check` drift fix)。

### §2.D cli/lib/tests/test_route_engine.py + helix-route.bats テスト設計 (拡張版)

**unit test 16 件** (旧 8 + P2-3 で追加 8):

旧 8:
- `test_drift_routes_to_reverse_normalization`
- `test_debt_degradation_routes_to_refactor`
- `test_runaway_routes_to_recovery`
- `test_unknown_design_routes_to_reverse_code`
- `test_suggest_command_format`
- `test_from_detect_output_batch`
- `test_invalid_signal_raises`
- `test_list_signals_returns_all`

追加 8:
- `test_incident_prod_routes_to_recovery`: env=prod / signal=incident で kind=recovery
- `test_incident_dev_routes_to_troubleshoot`: env=dev / signal=incident で kind=troubleshoot
- `test_regression_prod_routes_to_incident_recovery`: signal=regression_prod で mode=Incident / kind=recovery
- `test_regression_dev_routes_to_recovery`: signal=regression_dev で mode=Recovery / kind=recovery
- `test_4_quadrant_priority_not_mode_override`: drift+high/high で mode=Reverse のまま priority=P0
- `test_suggest_command_recover_connection`: signal=runaway で suggest_command が `helix recover plan ...` 形式
- `test_degradation_alias_warning`: signal=degradation で deprecation warning + 例外なし (alias 動作)
- `test_invalid_uncertainty_raises`: uncertainty=invalid で RouteEngineError
- `test_from_detect_output_helix_detect_run_fixture`: `helix detect run --json` fixture を読んで batch evaluate

**bats test 6 件**:
- `helix route help` usage 出力
- `helix route eval --signal drift` JSON 出力
- `helix route eval --signal drift --format command` suggest_command 文字列のみ
- `helix route eval --from-json /dev/stdin` で `helix detect run --json` パイプ入力
- `helix route list-signals` で全 signal + alias 出力
- `helix commands check` PASS (`route` / `recover` が docs/commands/index.md に登録済、drift なし)

### §2.E helix-recover との責務分担 (P1-3 接続契約版)

| CLI | 責務 | 入口/出口 |
|---|---|---|
| `helix-route` (本 PLAN) | **全モード入口判断** (suggest のみ) | 入口 |
| `helix-recover` (対 PLAN) | **Recovery 確定後の実行** (dump / log / PLAN draft) | 出口 |

接続契約:
- route の suggest_command 出力 = `helix recover plan --condition <id> --reopen-point <SHA> --auto-routed-from helix-route` (recover が受ける契約と一致)
- route は recover を起動しない (suggest のみ)、recover は route を呼ばない (独立実行可能)
- 自動連携が必要な場合は別 PLAN で `route → recover` パイプライン CLI (`helix orchestrate route-to-recover` 候補) を実装

## §3 成果物

- **製本対象 1**: `cli/helix-route` (新規 thin Bash wrapper、推定 10-15 行)
- **製本対象 2**: `cli/lib/route_engine.py` (新規 Python モジュール、推定 200-280 行)
- **製本対象 3**: `cli/lib/tests/test_route_engine.py` (新規 pytest 16 test、推定 250-320 行)
- **製本対象 4**: `cli/tests/helix-route.bats` (新規 bats 6 ケース、推定 60-80 行)
- **副次成果物**:
  - `cli/helix` への `route` ルーティング行追加
  - `docs/commands/index.md` に route 行追加 (helix commands check drift fix)
  - `cli/helix help` の Commands テーブルに route 行追加
- **HELIX-workflows 正本**: [detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md) §連携フロー を CLI として実体化
- **製本対象外** (別 PLAN 候補):
  - cross-detection / dashboard 入力 adapter (`L7-helix-route-cross-detection-adapterplan`)
  - route → recover 自動パイプライン (`L7-orchestrate-route-to-recoverplan`)
  - `helix route watch` 常駐モード

## §4 受入条件 / DoD

### 機械検証 (必須)

- [ ] `bash -n cli/helix-route` 構文エラーなし
- [ ] `python3 -m py_compile cli/lib/route_engine.py` 成功
- [ ] `python3 -m pytest cli/lib/tests/test_route_engine.py -v` **16 test 全 PASS**
- [ ] `bats cli/tests/helix-route.bats` **6 ケース全 PASS**
- [ ] `helix route list-signals` が 7 signal + 1 alias (degradation) を表示
- [ ] `helix route eval --signal drift` JSON を stdout に返す
- [ ] `helix route eval --signal drift --format command` で suggest_command 文字列のみ stdout
- [ ] `helix route eval --from-json /dev/stdin` でパイプ入力受付 (`helix detect run --json` 形式)
- [ ] `helix route eval --signal incident --env prod` で kind=recovery、`--env dev` で kind=troubleshoot
- [ ] `helix route eval --signal degradation` で stderr に deprecation warning
- [ ] `helix commands check` PASS (`route` + `recover` の docs/commands/index.md drift なし)
- [ ] `helix plan lint docs/plans/L7/L7-helix-route-implplan.md` PASS
- [ ] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-helix-route-implplan.md` warnings 0
- [ ] 既存 pytest 全回帰 PASS

### review 検証

- [ ] tl-advisor adversarial check 第 2 ラウンド passed
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認
  - ① 正本設計 (detection-routing.md) ↔ ③ テスト設計 (test_route_engine.py docstring)
  - ② 実装コード (helix-route + route_engine.py) ↔ ④ bats テストコード
- [ ] helix-recover との責務分担が実装レベルで衝突しないこと (route=suggest のみ、recover=実行、suggest_command schema 一致)
- [ ] mode 上書き禁止 (4 象限は priority/action のみ付与) が test で fail-close に検証されること

## §5 関連 PLAN / ADR / docs

- **正本設計**: HELIX-workflows/helix-process/detection-routing.md (本 PLAN の parent_design)
- **関連設計**: HELIX-workflows/helix-process/cross-detection.md (cross-detection adapter 別 PLAN)
- **企画書 roadmap**: HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #2
- **検出 CLI 既存**: cli/helix-detect (helix-common.sh + Python 委譲パターン)
- **registry**: cli/lib/detectors/registry.py (本 PLAN の input source、from_detect_output 接続先)
- **自動化ゲートマップ**: HELIX-workflows/helix-process/automation-gate-map.md
- **helix ルーター**: cli/helix (route 行追加対象)
- **対 PLAN**: docs/plans/L7/L7-helix-recover-implplan.md (Recovery モード実行側、suggest_command schema 一致)
- **plan_validator enum 確認**: cli/lib/plan_validator.py (kind enum: reverse/refactor/recovery/troubleshoot すべて一致)

## §6 後続 PLAN 候補 (本 PLAN 完遂後)

- **L7-helix-recover-implplan** (並行起草中、本 v2 と接続契約一致): Recovery モード実行側 CLI
- **L7-helix-route-cross-detection-adapterplan** (本 PLAN scope 外): cross-detection / dashboard / route_events JSON 形式を helix detect run --json 形式に変換する adapter
- **L7-orchestrate-route-to-recoverplan**: route が suggest した recovery を auto-routing で recover に実行させる pipeline (人間承認ガード付き)
- **L7-helix-route-watch-modeplan**: helix.db detect イベント subscribe 常駐モード (自律的整合ループの自動化)
- **#3 残件**: detection-routing / learning-engine / cross-detection / layer-context-injection の 4 件を skills/workflow/ に追加 (integration-map.md §優先順位 #3)
