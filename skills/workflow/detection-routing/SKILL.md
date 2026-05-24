---
name: detection-routing
description: 検出シグナルを受け取り、SIGNAL_TO_MODE 固定マップと 4 象限評価で対応モードと優先度を決める workflow スキル。cross-detection が集約した結果も受け取り、owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode を持つ後続フローへ接続する
metadata:
  helix_layer: L4-L14
  category: workflow
  triggers:
    - drift 検出時 (設計と実装の乖離)
    - コード劣化や負債蓄積を検出した時
    - AI 暴走や独断専行を検出した時
    - 本番障害や SLO 逸脱を検出した時
    - unknown_design が多発しモード選択に迷う時
    - helix route 相当の判断根拠を確認したい時
    - PLAN kind の選択 (recovery / refactor / reverse / troubleshoot) に迷う時
  verification:
    - "SIGNAL_TO_MODE マップに対象シグナルが登録済"
    - "4 象限評価で priority が P0-P3 のいずれかに決定"
    - "mode は SIGNAL_TO_MODE で固定され、4 象限で上書きしない"
    - "後続アクションが PLAN draft または Recovery 起動候補として説明可能"
compatibility:
  claude: true
  codex: true
---

# Detection Routing

## 対応 workflow doc

- [detection-routing](../../../HELIX-workflows/helix-process/detection-routing.md)

## 目的

検出シグナルを「どのモードへ渡すか」という判断に変換する。

- 入力: 単一シグナル、または cross-detection が集約した aggregate signal
- 出力: mode / kind / subtype / priority / action
- 位置づけ: `docs/plans/L7/L7-helix-route-implplan.md` の設計根拠

正本: [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md)

## 責務境界

| 対象 | 役割 | 本スキルとの違い |
|---|---|---|
| `workflow/detection-routing` | signal から mode と priority を決める | 本スキル本体 |
| `workflow/cross-detection` | 複数 detector の結果を集約し aggregate signal を作る | 集約のみで、最終判断はしない |
| `workflow/reverse-analysis` | reverse 系の実行手順を案内する | mode 決定後の実行フェーズ |
| `common/refactoring` | refactor 実施時のコード改善手順を担う | mode が Refactor に決まった後の実装フェーズ |
| `workflow/retrofit` | 既存基盤の移行計画を扱う | 検出起点ではなく移行起点 |

使い分け:

- 複数の detector 結果をまとめたい時は `workflow/cross-detection`
- すでに signal が決まっていて mode 判定だけしたい時は本スキル
- mode が Reverse に決まった後の復元作業は `workflow/reverse-analysis`
- mode が Refactor に決まった後の実装は `common/refactoring`

## 入力シグナル

本スキルは、単一 signal と aggregate signal を同じ判定器に流す。

- 単一 signal:
  - `drift`
  - `debt_degradation`
  - `regression_prod`
  - `regression_dev`
  - `runaway`
  - `incident`
  - `unknown_design`
- alias:
  - `degradation`
- aggregate signal:
  - `drift_degradation`
  - `doc_connection_gap`
  - `regression_dependency`
  - `runaway_feedback_loop`

詳細なマップは [references/signal-to-mode-mapping.md](references/signal-to-mode-mapping.md) を参照。

## 判定ルール

### 1. mode は固定マップで決める

- signal から mode / kind / subtype を決定する
- 4 象限評価は mode を変えない
- `incident` は環境に応じて kind を補助的に切り替えるが、mode は Incident のまま

### 2. priority は 4 象限で決める

- 軸: `uncertainty` × `impact`
- 出力: `P0` / `P1` / `P2` / `P3`
- action:
  - `suggest_only`
  - `immediate_plan_draft`
  - `discovery_first`
  - `emergency_routing`

評価表は [references/4-quadrant-evaluation.md](references/4-quadrant-evaluation.md) を参照。

## 基本フロー

1. detector または doctor が signal を出す
2. 必要なら `workflow/cross-detection` が aggregate signal を生成する
3. 本スキルが SIGNAL_TO_MODE を引いて mode / kind / subtype を決める
4. 4 象限評価で priority / action を付与する
5. 後続の PLAN draft、Recovery 起動、Reverse 着手候補へ渡す

## Forward 接続

| 判定結果 | 次の接続先 | 期待する成果物 |
|---|---|---|
| Reverse | `workflow/reverse-analysis` | reverse kind の PLAN draft |
| Refactor | `common/refactoring` | refactor kind の作業計画 |
| Recovery | `HELIX-workflows/helix-process/recovery-workflow.md` | recovery-log と recovery kind の PLAN 候補 |
| Incident | `workflow/incident` | troubleshoot または recovery の起票判断 |

実装基盤としての CLI は `docs/plans/L7/L7-helix-route-implplan.md` を参照する。

## エスカレーション基準

以下は人間確認を前提にする。

- `P0` かつ `incident` または `runaway`
- `unknown_design` が継続し reverse の範囲が広すぎる時
- signal 自体の語彙が未登録で、固定マップに載せられない時
- 本番影響のある routing 判定をそのまま自動実行したい時

## 関連スキル / コマンド

| 種別 | ID | 用途 |
|---|---|---|
| skill | `workflow/cross-detection` | aggregate signal の入力元 |
| skill | `workflow/reverse-analysis` | Reverse 判定後の実行 |
| skill | `workflow/incident` | Incident 判定後の実行 |
| skill | `common/refactoring` | Refactor 判定後の実行 |
| command | `helix gate` | ゲート前後で signal の優先度を確認 |
| command | `helix plan` | PLAN draft 化の実行先 |
| command | `helix review --uncommitted` | 判定結果に紐づく差分レビュー |

## 完了チェック

- [ ] signal が固定マップに登録されている
- [ ] 4 象限評価で priority と action を説明できる
- [ ] `workflow/cross-detection` との責務分担が崩れていない
- [ ] 後続の Reverse / Refactor / Recovery / Incident のどこへ渡すか決められる
