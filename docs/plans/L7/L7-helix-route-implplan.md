---
plan_id: L7-helix-route-implplan
title: "L7-helix-route-implplan: helix-route CLI 実装 — 検出シグナル → モード (Recovery / Incident / Reverse / Refactor) 自動ルーティング"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
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
    slot_label: "TL — 設計判断 adversarial check・責務分担確認"
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
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - cli/helix-detect
  - cli/lib/detectors/registry.py
  - cli/helix-doctor
  - cli/helix
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md)
> **本 PLAN の対象**: `cli/helix-route` を新規実装し、helix-detect / helix-doctor / drift-check / cross-detection が出力する検出シグナル (drift / 劣化 / 暴走 / 障害) を受け取り、4 象限評価 (uncertainty × impact) で対応モード (Recovery / Incident / Reverse / Refactor) を決定して PLAN 起票を suggest する CLI を提供する。
> **位置づけ**: integration-map.md §結論と優先順位 **#2** 「コマンド 2 件のうち 2 件目」。detection-routing.md の設計仕様を CLI として実体化する最初の実装 PLAN。

### parent_design (draft status) を採用する理由

`detection-routing.md` の frontmatter status は `draft` のまま。これは HELIX-workflows が正本化直後 (commit ee1a13a) であり、各 doc の status frontmatter 更新が後続作業として残っているため。本 PLAN は HELIX-workflows 正本群を **design-frozen 扱い** とし、L7 implementation を許可する。

### helix-recover との責務分担

| CLI | 責務 | 担当範囲 |
|---|---|---|
| `helix-route` (本 PLAN) | 検出 → モード振り分け | detect/doctor/drift-check の出力を読み、どのモード (Recovery / Incident / Reverse / Refactor) へ進むべきかを評価して PLAN 起票を suggest する。**判断と推薦**が中核 |
| `helix-recover` (別 PLAN) | Recovery モード起動・実行 | `helix-route` が Recovery を推薦したあと、実際に Recovery ワークフローを起動・進行させる。**実行**が中核 |

`helix-route` は入口 (どこへ向かうか)、`helix-recover` は出口 (Recovery を実際に走らせる)。両者を分離することで、route は軽量なルーター層として単体テスト可能になる。

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 設計読み込み (detection-routing.md 精読 + helix-detect 構造把握 + 既存 router 登録確認) | PM | ✅ done |
| 2 | route_engine.py インタフェース設計 (入力フォーマット / 評価ロジック / 出力フォーマット) | PM | ✅ done (§2.B) |
| 3 | TL adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 4 | TL 指摘反映 | PM | □ pending |
| 5 | SE 委譲: cli/helix-route シェルスクリプト実装 + cli/lib/route_engine.py 実装 | PM → SE | □ pending |
| 6 | test_route_engine.py 実装 (SE 込み、§2.D の test 案に従う) | SE | □ pending |
| 7 | bash -n cli/helix-route / python3 -m py_compile cli/lib/route_engine.py 確認 | SE | □ pending |
| 8 | pytest cli/lib/tests/test_route_engine.py 全 PASS | SE | □ pending |
| 9 | helix ルーター登録 (cli/helix に route 行追加) + helix commands 確認 | SE | □ pending |
| 10 | pmo-sonnet 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 11 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A 設計判断

**detection-routing.md の 4 象限評価方式を Python モジュール (`route_engine.py`) に実装する**。

設計選択理由:
- detection-routing.md §連携フロー は「evaluate (uncertainty × impact の 4象限)」を明記。この評価ロジックをシェルスクリプトではなく Python モジュールに置くことで、単体テストと再利用性を確保する
- `cli/helix-route` はシェルスクリプトとし、Python モジュールへの薄い wrapper とする。既存 `cli/helix-detect` (helix-common.sh + Python 委譲) と同パターン
- 入力は JSON (helix-detect / helix-doctor の出力形式に合わせる) または引数フラグ両対応とする
- 出力は「推薦モード + 起票すべき PLAN kind + suggest コマンド文字列」の JSON を stdout に返す

**PLAN kind enum の確認**: detection-routing.md §検出 → モードルーティング の表で使われる kind は以下のとおり (plan_validator.py の enum に照合済み):

| ルーティング先モード | PLAN kind |
|---|---|
| Reverse (normalization type) | reverse |
| Refactor | refactor |
| Recovery | recovery |
| Incident | troubleshoot |

いずれも plan_validator.py の kind enum に含まれる値であることを確認した。

### §2.B cli/lib/route_engine.py 設計

```python
# cli/lib/route_engine.py
# @helix:index id=route-engine.evaluate domain=cli/lib summary=検出シグナルを4象限評価してルーティング先モードを決定

class RouteEngine:
    """検出シグナル → モード振り分け (detection-routing.md §連携フロー 実装)"""

    SIGNAL_TO_MODE = {
        "drift":      {"mode": "Reverse",  "kind": "reverse",      "subtype": "normalization"},
        "degradation": {"mode": "Refactor", "kind": "refactor",     "subtype": None},
        "runaway":    {"mode": "Recovery",  "kind": "recovery",     "subtype": None},
        "incident":   {"mode": "Incident",  "kind": "troubleshoot", "subtype": None},
        "unknown_design": {"mode": "Reverse", "kind": "reverse",   "subtype": "code"},
    }

    def evaluate(self, signal: str, uncertainty: str, impact: str) -> dict:
        """
        4象限評価 (uncertainty: low/high × impact: low/high) でルーティング決定。
        Returns:
          {"mode": str, "kind": str, "subtype": str|None,
           "suggest_command": str, "plan_hint": str}
        """
        ...

    def from_detect_output(self, detect_json: dict) -> list[dict]:
        """helix-detect / helix-doctor の JSON 出力を受け取り、evaluate を一括実行"""
        ...
```

**入力フォーマット**: `helix route --signal drift --uncertainty low --impact high` または `helix route --from-json <path>` (helix-detect 出力 JSON を直接渡す)

**出力フォーマット** (JSON stdout):
```json
{
  "signal": "drift",
  "mode": "Reverse",
  "kind": "reverse",
  "subtype": "normalization",
  "suggest_command": "helix plan draft --kind reverse --drive be",
  "plan_hint": "設計 ⇔ 実装 drift を検出。Reverse (normalization type) で正規化を推奨。"
}
```

### §2.C cli/helix-route シェルスクリプト設計

```bash
#!/bin/bash
set -euo pipefail

# helix-route: detection-routing.md §連携フロー CLI 実体化
# 検出シグナル (drift/degradation/runaway/incident) → モード (Recovery/Incident/Reverse/Refactor) ルーティング

source "$(cd "$(dirname "$0")" && pwd)/lib/helix-common.sh"

exec python3 "$SCRIPT_DIR/lib/route_engine.py" "$@"
```

subcommand 構成:

| subcommand | 説明 |
|---|---|
| `helix route eval --signal <type> [--uncertainty low/high] [--impact low/high]` | 単発シグナルを評価してルーティング先を返す |
| `helix route eval --from-json <path>` | helix-detect / helix-doctor 出力 JSON を一括評価 |
| `helix route suggest` | 評価結果に基づく PLAN 起票 suggest コマンドを stdout に出力 |
| `helix route list-signals` | 登録済みシグナル種別と対応モード一覧を表示 |
| `helix route help` | 使い方を表示 |

helix ルーター登録 (cli/helix への追加):
```bash
  route)    exec "$SCRIPT_DIR/helix-route" "$@" ;;
```

### §2.D cli/lib/tests/test_route_engine.py 設計

以下 **8 test** を実装する:

- `test_drift_routes_to_reverse_normalization`: signal=drift → mode=Reverse / kind=reverse / subtype=normalization
- `test_degradation_routes_to_refactor`: signal=degradation → mode=Refactor / kind=refactor
- `test_runaway_routes_to_recovery`: signal=runaway → mode=Recovery / kind=recovery
- `test_incident_routes_to_troubleshoot`: signal=incident → mode=Incident / kind=troubleshoot
- `test_unknown_design_routes_to_reverse_code`: signal=unknown_design → mode=Reverse / kind=reverse / subtype=code
- `test_suggest_command_format`: suggest_command が `helix plan draft --kind <kind>` 形式であること
- `test_from_detect_output_batch`: 複数シグナルを含む detect JSON から evaluate を一括実行して件数一致
- `test_invalid_signal_raises`: 未登録シグナルで ValueError または RouteEngineError を raise すること

### §2.E 4象限評価ロジック

detection-routing.md §概要「Discovery の trigger (detect → evaluate 4象限 → transition) 方式を DB 検出全般に拡張する」に基づく評価行列:

| uncertainty | impact | 推奨アクション |
|---|---|---|
| low | low | suggest のみ (P3 レベル) |
| low | high | 即時 PLAN 起票推奨 (P1 レベル) |
| high | low | Discovery/Scrum 先行推奨 (調査フェーズ) |
| high | high | Incident / Recovery 緊急起動推奨 (P0 レベル) |

評価結果は `suggest_command` の末尾フラグに反映する (例: `--priority P1`)。uncertainty / impact が未指定の場合は `low/low` をデフォルトとし、シグナル種別だけでモード決定する。

## §3 成果物

- **製本対象 1**: `cli/helix-route` (新規シェルスクリプト、推定 30-50 行)
- **製本対象 2**: `cli/lib/route_engine.py` (新規 Python モジュール、推定 100-150 行)
- **製本対象 3**: `cli/lib/tests/test_route_engine.py` (新規 pytest、8 test、推定 120-160 行)
- **副次成果物**: `cli/helix` への `route` ルーティング行 1 行追加
- **HELIX-workflows 正本**: [detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md) §連携フロー を CLI として実体化

## §4 受入条件 / DoD

### 機械検証 (必須)

- [ ] `bash -n cli/helix-route` 構文エラーなし
- [ ] `python3 -m py_compile cli/lib/route_engine.py` 成功
- [ ] `python3 -m pytest cli/lib/tests/test_route_engine.py -v` 全 8 test PASS
- [ ] `helix route list-signals` が 5 シグナル (drift / degradation / runaway / incident / unknown_design) を表示
- [ ] `helix route eval --signal drift` が JSON を stdout に返す
- [ ] `helix route eval --from-json /dev/stdin` でパイプ入力を受け付ける
- [ ] `helix commands` に `route` が含まれる (cli/helix ルーター登録確認)
- [ ] `helix plan lint docs/plans/L7/L7-helix-route-implplan.md` PASS (本 PLAN の lint)
- [ ] 既存 pytest 全回帰 PASS (新規 import による破壊なし)

### review 検証

- [ ] tl-advisor adversarial check passed (Step 3-4 完了)
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認 (PLAN doc ↔ detection-routing.md ↔ route_engine.py ↔ test_route_engine.py の reference 整合)
- [ ] helix-recover との責務分担が実装レベルで衝突していないこと (helix-route は suggest のみ、実行は委譲)

## §5 関連 PLAN / ADR / docs

- **正本設計**: HELIX-workflows/helix-process/detection-routing.md (本 PLAN の parent_design)
- **企画書 roadmap**: HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #2
- **検出 CLI**: cli/helix-detect (既存、helix-common.sh + Python 委譲パターンを踏襲)
- **自動化ゲートマップ**: HELIX-workflows/helix-process/automation-gate-map.md
- **helix ルーター**: cli/helix (route 行追加対象)
- **並行起草 PLAN**: L7-helix-recover-implplan (Recovery モード実行側、本 PLAN 完遂後に接続)
- **detector 実装**: cli/lib/detectors/ (axis_01〜13、helix-route の入力元)

## §6 後続 PLAN 候補 (本 PLAN 完遂後)

- **L7-helix-recover-implplan** (並行起草中): Recovery モード実行側 CLI。`helix route suggest` が Recovery を推薦したあと `helix recover` で実際に Recovery ワークフローを起動。本 PLAN の `suggests_command` 出力形式と連携設計が必要
- **#3 retrofit skill**: detection-routing / learning-engine / cross-detection / layer-context-injection の 4 件を workflow スキル化 (integration-map.md §優先順位 #3)
- **cross-detection 連携拡張**: `helix route eval --from-json` の入力として cross-detection の JSON 出力を直接渡せるよう、入力 schema を cross-detection 出力形式に合わせる拡張
- **helix-route watch モード** (将来): helix.db の検出イベントを subscribe してリアルタイムでルーティング推薦を流す常駐モード (自律的な整合ループの自動化)
