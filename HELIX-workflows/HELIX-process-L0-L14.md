# HELIX 工程定義 L0-L14

本書は Forward Vモデルの常時注入正本である。ここには定義と進め方だけを書く。工程詳細、workflow詳細、DB収束、skill推挙は現在地に応じて別途注入する。

Project profile により、一部工程は skip できる。HELIX-workflows 自身は UI を持たないため L2 / L10 を skip するが、画面を持つプロダクトでは L2 / L10 を有効にする。

**絶対原則**（正本: `helix/HELIX_CORE.md §0`）: V モデルが起点。駆動 workflow は V モデルから外れてよいが、必ず V モデルへ戻す。V モデルへ戻し HELIX DB に収束しなければ、成果は trace / drift / coverage の管理対象にならず「完了」として成立しない。

## 定義

- Forward: 要求・設計から実装・検証へ降ろすトップダウンの正本処理。
- Reverse: 既存コード・既存実態・失敗事象から要件・設計・契約を復元し、Forward へ戻すボトムアップ処理。
- Vモデル: ドキュメント、実装、テスト、カバレッジを対応づけて、資産・実体・品質をずらさず管理する骨格。
- Workflow: Forward から外れた作業を受け止め、最終的に Forward と HELIX DB trace へ戻す循環処理。
- 現在地: HELIX DB の `plan_registry` / `transition_history` / `gate_pass` と workflow 補助 state で決まる。常時注入は本書、詳細注入は現在地に応じて決める。

## 工程

| L | 工程 | テスト設計 / 検証 |
|---|---|---|
| L0 | 企画書 | - |
| L1 | 要求定義 | 運用テスト設計 |
| L2 | 画面要求 / 画面設計 / フロントUI | ワイヤーモック作成 |
| L3 | 要件定義 | 受入テスト設計 |
| L4 | 基本設計 / 外部設計 | 総合テスト設計 |
| L5 | 詳細設計 / 内部設計 | 結合テスト設計 |
| L6 | 機能設計 / 仕様書 | 単体テスト設計 |
| L7 | 実装（テスト実装 -> 本体実装 -> 3点レビュー -> テスト追加 -> テスト実施 -> カバレッジ確認 / closure -> 修正 / 完了） | 単体テスト実施 |
| L8 | 結合テスト | L5 の検証 |
| L9 | 総合テスト | L4 の検証 |
| L10 | フロントUX / 業務デザイン磨き上げ | L2 の検証 |
| L11 | 総合レビュー / ユーザー検証 / 要件巻き取り | L1 / L3 の最終突合 |
| L12 | 受入テスト | L3 の検証 |
| L13 | 運用検証 / 運用テスト | 実環境検証 |
| L14 | 運用学習 / 運用改善 | L1 の検証 |

- **工程遷移規律**: L0→G0.5→L1 の遷移（企画→要求の翻訳、PdM 登場・PM/PO 判定）は `helix-process/planning-to-requirements-transition.md` を正本とする。右腕検証戦略は L1 で起票する（`docs/v2/L1-requirements/helix-workflows-verification-strategy.md`、入力は L0 から handoff）。

## テスト設計の対応

| 作る層 | 実行・検証する層 |
|---|---|
| L6 単体テスト設計 | L7 単体テスト実施 |
| L5 結合テスト設計 | L8 結合テスト |
| L4 総合テスト設計 | L9 総合テスト |
| L3 受入テスト設計 | L12 受入テスト |
| L1 運用テスト設計 | L14 運用学習 / 運用改善 |
| L2 ワイヤーモック作成 | L10 フロントUX / 業務デザイン磨き上げ |

## 粒度ペアリング原則

設計⇔検証の対は、量だけでなく**粒度でも対称に閉じる**。各設計層は、対になる検証層のテスト設計と**同じ粒度**で書く。**機能設計 (L6) は単体テスト (L7) の粒度**で書く（関数 / メソッド 1 個 = 単体テスト対象 1 個。モジュール / クラス止まり = 粒度違反）。

| 設計層 ↔ 検証層 | 粒度 |
|---|---|
| L4 ↔ L9 | システム / コンポーネント粒度 |
| L5 ↔ L8 | モジュール / 結合粒度 |
| L6 ↔ L7 | 関数 / 単体粒度（DbC: requires / ensures / invariant） |

粒度を粗く書くと設計とテストの対応が機械的に閉じず、片肺・カバレッジ薄化が起きる（特に L6）。各設計層の必須成果物・粒度・entry/exit 判定の詳細は `skills/workflow/doc-system-architect/references/design-coverage-baseline.md` を正本とする。

## 検証ゲート（Forward 内在、原則）

検証は別途追いかける「ロードマップ/Phase」ではなく、**各 L の exit を通すゲート**として Forward に内在させる（2026-06-08 確立）。各 L の `entry = 前段 exit + 必要入力 + freeze 有効` / `exit = 成果物 + readiness + 検証閉合（pair_closure / 横断ゲート）`。

- **公開 gate ID `G0.5/G1〜G14`** は維持し、意味を「対応 L の exit gate」に固定する（番号を作り直さない）。
- **pair_closure**（設計⇔検証ペアの閉合）= `design + test_design + test_code_anchor + test_execution_pass + trace_symmetry + semantic_gate`。左腕 freeze（G1-G6）は前半、右腕 execution（G7/G8/G9/G10/G12/G14）は後半まで要求。cov100% 単独 pass は禁止。
- **横断ゲート**: 要件ずれ（requirement_drift = L1→L3→L4-6→code→test の縦 trace）と全体俯瞰（VG-overview = whole-source⊆design + **applicable な pair が clean/semantically-accepted**、not_applicable/approved_deferred は理由必須）を freeze 前・push 前に通す。
- **退化防止**: ゲートは Forward の通過条件であって独立タスク台帳でない。未完は新 Phase でなく該当 L-pair の pending gate evidence に帰属。実効化は static check 候補（deprecated Process を新 Action の parent にしない 等）で担保する。
- 判定式・evidence schema = [verification-strategy §14](../docs/v2/L1-requirements/helix-workflows-verification-strategy.md)、detector↔gate↔push 配線 = [automation-gate-map](helix-process/automation-gate-map.md)、readiness = [gate-policy](../skills/tools/ai-coding/references/gate-policy.md)。

## 進め方

1. HELIX DB の現在地を確認する。
2. 現在地が Forward なら、該当 L の成果物とテスト設計を作る。
3. 現在地が既存実態・障害・逸脱・探索なら、該当 workflow を経由して Forward へ戻す。
4. 実装を伴う場合は、合格基準となるテストを先に作る。
5. 完了時は、docs / code / test / coverage / contract の trace を HELIX DB に登録・更新する。

## DB 登録と注入制御

現在地と注入範囲はシステムが DB から決める。LLM は DB から渡された現在地・成果物・注入セットに従い、自分の判断で次工程や注入範囲を広げない。

| DB / 定義 | 役割 |
|---|---|
| `plan_registry` | PLAN、kind、工程、成果物を登録する |
| `transition_history` | L 間遷移と workflow から Forward への復帰を記録する |
| `gate_pass` | gate の通過状態を記録する |
| workflow 補助 state | Reverse / Discovery / Incident などの中間状態を保持する |
| closure event | 補助 state を Vモデル DB へ統合する |
| `vmodel-semantics` / 注入定義 | 現在の L / workflow に応じた doc、skill、command、agent を決める |

工程進捗を更新する場合は、PLAN / gate / transition / closure event のいずれかとして登録し、DB 上の現在地を更新してから作業する。

## Workflow 入口

| 入口 | workflow | 戻し先 |
|---|---|---|
| 要件・設計・契約が明確 | Forward | L0-L14 |
| 要件を反復確認したい | Scrum | Reverse fullback 経由で Forward |
| 不明点・実現性を確認したい | Discovery | L1 / L3 / L4-L6 |
| 既存コード・設計資産から戻したい | Reverse | L1 / L3 / L4 / L7 / L8-L11 |
| 本番障害が発生した | Incident | L1 / L3 / L4-L6 / L14 |
| 既存システムへ機能追加する | Add-feature | L4-L7 |
| 振る舞いを変えず構造改善する | Refactor | L7 |
| 既存を改修・移行する | Retrofit | L4-L9 |
| 実装前に調査・意思決定する | Research | L1 / L4 |
| AI が暴走・工程逸脱した | Recovery | 再開ポイントから L0-L14 |

> **全駆動 workflow の引き戻し規律（必須）**: 上表の「戻し先」へ Forward 復帰するとき、各駆動 workflow は [helix-process/forward-return-discipline.md](helix-process/forward-return-discipline.md) を必須適用する。戻し先が実装/検証層（L7/L8/L9）でも、`design_change_class` が `pure_impl` と証明できない限り対の design 層（L6/L5/L4）を再凍結する（片肺禁止 = 絶対原則 §0/§1 の operationalize）。
