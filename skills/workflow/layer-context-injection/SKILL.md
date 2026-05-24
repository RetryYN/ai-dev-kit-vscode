---
name: layer-context-injection
description: L 単位で owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode の 6 field を注入し、工程ごとの判断負荷を減らす workflow スキル。L0-L14 の概念に対し、実体は 4 drive × 5 layer の 20 セル injection-set で管理する
metadata:
  helix_layer: L0-L14
  category: workflow
  triggers:
    - 工程 L0-L14 に入る時
    - mode switch を行う時
    - その工程で使うべき skill や command が不明な時
    - 注入セットを更新したい時
    - learning-engine が改善提案を出した時
    - 新しい workflow skill を工程へ割り当てたい時
  verification:
    - "injection-set が owner_role / mandatory_agents / recommended_agents / recommended_skills / recommended_commands / orchestration_mode を持つ"
    - "実体キーが drives.{drive}.layers.{layer}.injection に準拠している"
    - "L0-L14 の工程説明と 20 セル実体の対応が説明できる"
    - "学習結果の反映経路が learning-engine との境界で定義済"
compatibility:
  claude: true
  codex: true
---

# Layer Context Injection

## 対応 workflow doc

- [layer-context-injection](../../../HELIX-workflows/helix-process/layer-context-injection.md)

## 目的

工程へ入るたびに「何を使うか」を考え直さなくて済む状態を作る。

- 概念レベル: L0-L14 の各工程に必要な文脈を注入する
- 実体レベル: `drives.{drive}.layers.{layer}.injection` の 20 セルに定義する
- 位置づけ: `HELIX-workflows/helix-process/layer-context-injection.md` のスキル化

正本: [HELIX-workflows/helix-process/layer-context-injection.md](../../../HELIX-workflows/helix-process/layer-context-injection.md)

## 責務境界

| 対象 | 役割 | 本スキルとの違い |
|---|---|---|
| `workflow/layer-context-injection` | 注入セットの定義と適用原則を持つ | 本スキル本体 |
| `workflow/learning-engine` | 改善案を学習し注入セット更新候補を出す | 注入セット自体は保持しない |
| `workflow/detection-routing` | 今どの mode にいるかの判断を補助する | 注入内容の定義はしない |
| `workflow/verification` | 適用された結果を検証する | 注入セットの設計はしない |

## 6 field 契約

本スキルが扱う injection-set は、必ず以下 6 field を持つ。

1. `owner_role`
2. `mandatory_agents`
3. `recommended_agents`
4. `recommended_skills`
5. `recommended_commands`
6. `orchestration_mode`

詳細な schema は [references/injection-set-schema.md](references/injection-set-schema.md) を参照。

## 20 セル構造

実体キーは、4 drive × 5 layer の 20 セルで管理する。

- drive:
  - `be`
  - `fe`
  - `db`
  - `fullstack`
- layer:
  - `planning`
  - `requirement`
  - `architecture`
  - `detailed`
  - `functional`

L0-L14 の工程説明は、この 20 セルへ射影して扱う。対応表は [references/l-unit-injection-table.md](references/l-unit-injection-table.md) を参照。

## 注入するもの

| field | 意味 |
|---|---|
| `owner_role` | 工程の責任者 |
| `mandatory_agents` | その工程で必ず確認する agent |
| `recommended_agents` | 状況次第で使う agent |
| `recommended_skills` | 工程で優先して参照する skill |
| `recommended_commands` | 実行候補の HELIX command |
| `orchestration_mode` | Claude / Codex / 人間の協調方式 |

## 判断負荷を減らす原理

1. 工程に入る
2. その工程に対応する injection-set を引く
3. 必須 agent、推奨 skill、推奨 command、協調方式が先に決まる
4. 実装者は選択肢を一から探索せずに進める

## Forward 接続

| 入力 | 出力 |
|---|---|
| `workflow/learning-engine` の改善候補 | injection-set 更新案 |
| 新しい workflow skill | recommended_skills への追加候補 |
| 運用での実績 | orchestration_mode の見直し候補 |

実装基盤は `docs/plans/L7/L7-vmodel-semantics-injection-setplan.md` を参照する。

## エスカレーション基準

- 工程定義と injection-set が衝突する時
- owner_role を変えないと責務が破綻する時
- recommended_commands に未実装の command を入れたい時
- 学習結果をそのまま mandatory_agents に昇格したい時

## 関連スキル / コマンド

| 種別 | ID | 用途 |
|---|---|---|
| skill | `workflow/learning-engine` | 更新候補の入力元 |
| skill | `workflow/verification` | 注入結果の確認 |
| skill | `workflow/design-doc` | requirement / architecture 系の主要注入先 |
| skill | `common/testing` | functional 系の主要注入先 |
| command | `helix gate` | 工程ごとの主要判断点 |
| command | `helix sprint` | functional 層の進行管理 |
| command | `helix task` | 工程の作業単位管理 |
| command | `helix codex` | 実装委譲の主要導線 |

## 完了チェック

- [ ] 6 field の意味を説明できる
- [ ] L0-L14 と 20 セル実体の対応が説明できる
- [ ] `workflow/learning-engine` との境界が明記されている
- [ ] owner_role と orchestration_mode の関係が破綻していない
