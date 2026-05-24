---
plan_id: L7-workflow-skills-pkgplan
title: "L7-workflow-skills-pkgplan: workflow スキル 4 件パッケージ起草 — detection-routing / learning-engine / cross-detection / layer-context-injection (integration-map #3)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/integration-map.md
pairs_test_design:
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/learning-engine.md
  - HELIX-workflows/helix-process/cross-detection.md
  - HELIX-workflows/helix-process/layer-context-injection.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・スコープ確認・SKILL_MAP 追記 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check・4 skill 責務境界確認 (detection/cross 重複 / learning→injection 依存順序 / helix_layer 整合)"
  - role: se
    slot_label: "SE — 4 SKILL.md + references/ 起草実装、SKILL_MAP.md retrofit 追記"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 確認・整合チェック・SKILL_MAP 追記 diff review"
generates:
  - artifact_path: skills/workflow/detection-routing/SKILL.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/detection-routing/references/signal-to-mode-map.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/detection-routing/references/four-quadrant-evaluation.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/learning-engine/SKILL.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/learning-engine/references/recipe-pattern-template.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/learning-engine/references/learning-loop-design.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/cross-detection/SKILL.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/cross-detection/references/detector-axis-map.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/cross-detection/references/cross-detection-checklist.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/layer-context-injection/SKILL.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/layer-context-injection/references/injection-set-schema.md
    artifact_type: markdown_doc
  - artifact_path: skills/workflow/layer-context-injection/references/l-unit-injection-table.md
    artifact_type: markdown_doc
dependencies:
  parent: null
  requires:
    # 以下 3 PLAN は「実装完了」を要求するのではなく、各 v3 接続契約 (signal schema / injection-set schema / recovery handshake) が frozen であることを参照する。
    # Step 7-10 着手前に各 PLAN の接続契約凍結状態を確認すること。実装 (CLI 動作) は本 PLAN と並行して進行してよい。
    - L7-helix-route-implplan
    - L7-helix-recover-implplan
    - L7-vmodel-semantics-injection-setplan
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/detection-routing.md
  - HELIX-workflows/helix-process/learning-engine.md
  - HELIX-workflows/helix-process/cross-detection.md
  - HELIX-workflows/helix-process/layer-context-injection.md
  - HELIX-workflows/helix-process/integration-map.md
  - skills/workflow/retrofit/SKILL.md
  - skills/workflow/retrofit/references/retrofit-matrix-template.md
  - skills/SKILL_MAP.md
  - docs/plans/L7/L7-helix-route-implplan.md
  - docs/plans/L7/L7-helix-recover-implplan.md
  - docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計 (parent_design)**: [HELIX-workflows/helix-process/integration-map.md](../../../HELIX-workflows/helix-process/integration-map.md) §結論と優先順位 #3
> **本 PLAN の対象**: integration-map §結論と優先順位 #3「workflow スキル化」のうち retrofit (commit 4ddf373 で完遂済) を除く残 **4 件**を `skills/workflow/{name}/SKILL.md + references/` として実体化する。

### 対象 4 スキル (各正本 doc → skill 化)

| # | スキル名 | 正本 doc | helix_layer |
|---|---|---|---|
| S-1 | detection-routing | HELIX-workflows/helix-process/detection-routing.md | L4-L14 |
| S-2 | learning-engine | HELIX-workflows/helix-process/learning-engine.md | L14 |
| S-3 | cross-detection | HELIX-workflows/helix-process/cross-detection.md | L4-L9 |
| S-4 | layer-context-injection | HELIX-workflows/helix-process/layer-context-injection.md | L0-L14 |

### retrofit スキルを範例とする理由

`skills/workflow/retrofit/SKILL.md` (commit 4ddf373) は直近に同手法 (HELIX-workflows doc → skills/workflow/ 実体化) で成功した最新事例であり、frontmatter 構造 / references/ 配置 / 責務境界セクション / Forward 接続 / 完了チェックの各パターンを本 PLAN で踏襲する。

### HELIX-workflows draft status 採用の方針

4 件の正本 doc はいずれも frontmatter `status: draft`。これは HELIX-workflows 正本化直後 (commit ee1a13a) の状態であり、各 doc の status 更新は後続作業として残っている。本 PLAN は 4 doc を **design-frozen 扱い** とし、SE はスキル化実装時に正本 doc の内容を変更しない。

### 4 スキルの位置づけ (integration-map 全体像内)

```
integration-map §優先順位
  #1 自動登録 (db-auto-registration) ← 完遂済または別 PLAN
  #2 コマンド 2 件                    ← L7-helix-route / L7-helix-recover PLAN 進行中
  #3 workflow スキル化 (本 PLAN)      ← retrofit 完遂済 + 本 PLAN で残 4 件
  #4 templates                        ← 後続 PLAN 候補
  #5 文書統合                         ← 後続 PLAN 候補
```

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 正本 4 doc 精読 (detection-routing / learning-engine / cross-detection / layer-context-injection) | PM | ✅ done |
| 2 | 範例精読 (retrofit SKILL.md + references/) | PM | ✅ done |
| 3 | 本 PLAN 起票 + tl-advisor 第 1 ラウンド依頼 | PM | ✅ done (draft 起票完了) |
| 4 | tl-advisor 第 1 ラウンド adversarial check | PM → TL | ✅ done (needs_revision P1×4 受領) |
| 5 | TL 第 1 ラウンド指摘反映 | PM | ✅ done (pmo-sonnet 反映済) |
| 6 | tl-advisor 第 2 ラウンド (必要に応じて) | PM → TL | □ pending |
| 7 | SE 委譲: S-1 detection-routing SKILL.md + 2 references/ 起草 | PM → SE | □ pending |
| 8 | SE 委譲: S-2 learning-engine SKILL.md + 2 references/ 起草 | PM → SE | □ pending |
| 9 | SE 委譲: S-3 cross-detection SKILL.md + 2 references/ 起草 | PM → SE | □ pending |
| 10 | SE 委譲: S-4 layer-context-injection SKILL.md + 2 references/ 起草 | PM → SE | □ pending |
| 11 | SKILL_MAP.md §スキル群配置 workflow/ リスト に 4 件追記 | SE | □ pending |
| 12 | helix plan lint + plan_validator 全件確認 | PM / SE | □ pending |
| 13 | pmo-sonnet 4 artifact 双方向 trace 確認 | PM → PMO | □ pending |
| 14 | commit + push | PM | □ pending |

### Step 7-10 並列化方針

S-1〜S-4 は **相互にファイル衝突しない** (各自独立ディレクトリ)。依存関係:
- S-1 detection-routing は S-3 cross-detection の参照先であるが、SKILL.md の内容は各自独立して起草可能
- S-4 layer-context-injection は S-2 learning-engine の出力先 (注入セット更新) だが、これも起草として独立
- よって Step 7-10 は **4 並列** 投入可能 (Codex SE × 4 または SE × 2 + PMO-Sonnet × 2)

### Step 7-10 着手前提条件

以下が揃ってから Step 7-10 (SE 委譲) を投入すること:
1. **共有語彙の凍結**: signal / mode / priority / aggregate_signal の定義が detection-routing.md / cross-detection.md で確定済
2. **signal schema の凍結**: SIGNAL_TO_MODE マップの key / value 型が helix route PLAN v3 接続契約として frozen
3. **injection-set frontmatter template 確定**: `drives.{drive}.layers.{layer}.injection` の 20 セル YAML スキーマが vmodel-semantics-injection-setplan v3 で frozen
4. **関連スキル名の凍結**: 4 SKILL.md が相互参照するスキル名 (detection-routing / cross-detection / learning-engine / layer-context-injection) が本 PLAN §2 で確定済 (SE はこの名称を使う)

---

## §2 実装計画

以下、4 スキルそれぞれの SKILL.md + references/ の設計要件を定義する。SE はこのセクションを実装の入力として使用する。

---

### §2.1 S-1: detection-routing (skills/workflow/detection-routing/)

#### SKILL.md frontmatter

```yaml
name: detection-routing
description: 検出シグナル (drift / degradation / runaway / incident) を受け取り、4 象限 (uncertainty × impact) 評価と SIGNAL_TO_MODE 固定マップで対応モード (Recovery / Incident / Reverse / Refactor) へルーティング判定する。helix route CLI の設計根拠スキル
metadata:
  helix_layer: L4-L14
  category: workflow
  triggers:
    - drift 検出時 (設計 ⇔ 実装乖離)
    - コード劣化・負債蓄積検出時
    - AI 暴走・独断専行検出時
    - 本番障害・SLO 逸脱検出時
    - 設計不明箇所 (unknown_design) 多発時
    - helix route eval を使う判断に迷う時
    - PLAN kind の選択 (recovery / refactor / reverse / troubleshoot) で迷う時
  verification:
    - "SIGNAL_TO_MODE マップに対象シグナルが登録済"
    - "4 象限で priority が P0-P3 のいずれかに決定"
    - "mode は SIGNAL_TO_MODE で固定 (4 象限で上書きしない)"
    - "suggest_command が helix route eval の出力と一致"
compatibility:
  claude: true
  codex: true
```

#### SKILL.md 本文構成

- **目的**: 検出シグナル → モード決定の設計根拠を提供し、AI の mode 選択判断を機械化する
- **責務境界**: cross-detection (横断集約) との分担を明確化
  - detection-routing: 個別シグナルを受け取り mode/priority を決定 (判断)
  - cross-detection: 複数 axis の結果を集約して detection-routing に渡す (集約)
- **SIGNAL_TO_MODE マップ**: references/signal-to-mode-map.md を参照
- **4 象限評価**: references/four-quadrant-evaluation.md を参照
- **基本フロー**: 正本 detection-routing.md §連携フロー の再掲 + CLI 使用例
- **Forward 接続**: 各 mode 別の PLAN 起票ルール (recovery / refactor / reverse / troubleshoot)
- **エスカレーション基準**: P0 シグナルを検出した場合の人間確認要件
- **完了チェック**: mode 決定 + priority 付与 + suggest_command 生成の 3 点確認
- **関連スキル / コマンド**: helix route / cross-detection / learning-engine / helix-doctor

#### references/ ファイル (2 件)

**references/signal-to-mode-map.md**

```
> 目的: 検出シグナルと対応モード・kind の固定マップ。SIGNAL_TO_MODE の設計根拠として SKILL.md から参照する
```

内容:
- 全シグナルの mode / kind / subtype / 説明 のテーブル
- deprecated alias (degradation) の扱い
- 各シグナルの典型例と検出 CLI

**references/four-quadrant-evaluation.md**

```
> 目的: uncertainty × impact の 4 象限評価で priority (P0-P3) と action を決定する設計根拠
```

内容:
- 4 象限マトリクス (low/low → P3 / low/high → P1 / high/low → P2 / high/high → P0)
- priority と action の対応 (suggest_only / immediate_plan_draft / discovery_first / emergency_routing)
- mode は上書きしない原則の説明 (P2-1 設計原則)

---

### §2.2 S-2: learning-engine (skills/workflow/learning-engine/)

#### SKILL.md frontmatter

```yaml
name: learning-engine
description: スキル発火・トラブル・成功実行のログから recipe (成功パターン) を蓄積・再利用し、頻出トラブルを予防ルール (gate / detector) へ昇格させる HELIX Learning Engine。helix learn CLI + analyze_success + save_recipe が実装基盤
metadata:
  helix_layer: L14
  category: workflow
  triggers:
    - 同種 incident / recovery が繰り返し発生する時
    - recovery-log に類似パターンが蓄積した時
    - drift 検出が反復する工程を改善したい時
    - layer-context-injection の注入セットを更新したい時
    - 成功実行の手順を recipe として保存したい時
    - skill-radar の推薦精度を改善したい時
    - G9 / L9 総合検証 完了後に検証結果を学習したい時
    - G10 / L10 UX 検証 完了後にフィードバックを取り込みたい時
    - G11 / L11 RC / ユーザー検証 完了後に知見を recipe 化したい時
    - G14 / L14 運用検証 完了後に次サイクルへ学習を引き継ぎたい時
  verification:
    - "analyze_success が成功 run を分析し recipe を保存済"
    - "頻出トラブルが PLAN / PR 候補化され、gate / detector への直接変更は TL 確認後のみ実施"
    - "layer-context-injection の注入セットに学習結果が反映済"
    - "recipe は pattern_key で検索可能"
    - "G9-G11 / L9-L11 / L14 の検証フィードバックが feedback_hook / detector 結果 / recovery-log として入力済"
compatibility:
  claude: true
  codex: true
```

#### SKILL.md 本文構成

- **目的**: ログからパターンを学習し、次回の工程参照コストを削減する
- **責務境界**: layer-context-injection との関係
  - learning-engine: 学習 → recipe / 予防ルール化
  - layer-context-injection: 注入セットの定義・実行 (learning-engine の出力を受け取る)
- **学習の入力**: 正本の入力源テーブルを再掲 + helix.db との連携。入力に以下を明示すること:
  - feedback_hook (ゲート通過後の 5 軸 Lv1-5 フィードバック)
  - detector 結果 (drift / 劣化 / 回帰の検出履歴)
  - recovery-log (AI 暴走・収束の履歴)
  - G9 / L9 総合検証 結果 (総合テスト完了後のフィードバック)
  - G10 / L10 UX 検証 結果 (FE UX 磨き上げ完了後のフィードバック)
  - G11 / L11 RC / ユーザー検証 結果 (RC 判定後のユーザーフィードバック)
  - G14 / L14 運用検証 結果 (次サイクル L0 input となる運用知見)
- **学習の処理**: analyze_success → save_recipe フロー
- **学習の出力**: recipe 再利用 / スキル推薦改善 / 予防ルール化 / L 単位注入の更新。出力の性質を明示すること:
  - 予防ルール化の結果は **gate / detector への直接変更ではなく PLAN / PR 候補化** にとどまる
  - gate / detector の実際の変更は TL 確認後に別 PLAN として実施する
- **学習ループ**: 正本の循環図を再掲 + helix learn CLI 使用例
- **Forward 接続**: L14 運用学習 → 次サイクル L0 input の接続規則
- **エスカレーション基準**: recipe 昇格が gate 変更を伴う場合の TL 確認要件
- **完了チェック**: recipe 保存 + 予防ルール化 (PLAN/PR 候補化) + 注入セット更新の 3 点確認

#### references/ ファイル (2 件)

**references/recipe-pattern-template.md**

```
> 目的: save_recipe が保存する recipe の標準フォーマットテンプレート。pattern_key / context / steps / outcome の構造を定義する
```

内容:
- recipe YAML テンプレート (pattern_key / trigger_conditions / context / steps / outcome / confidence_score)
- recipe 品質基準 (再利用可能な最小単位、失敗時の fallback 記載)
- recipe 昇格基準 (N 回以上の類似成功 → gate / detector 候補)

**references/learning-loop-design.md**

```
> 目的: 学習ループ (ログ蓄積 → analyze_success → save_recipe → 予防ルール化 → 実行 → ログ蓄積) の実装設計根拠
```

内容:
- helix learn CLI サブコマンド一覧 (analyze / save / promote / list)
- helix.db テーブル連携 (skill_usage / feedback / recovery_log / gate_log)
- 予防ルール昇格フロー (recipe.confidence_score ≥ threshold → detector 候補 PR 起票)

---

### §2.3 S-3: cross-detection (skills/workflow/cross-detection/)

#### SKILL.md frontmatter

```yaml
name: cross-detection
description: 単一 detector では見えない横断的劣化 (依存漏れ / 契約漏れ / 接続欠損 / デグレ) を helix-doctor が全 detector 横断実行で検出し、detection-routing でモード発動につなぐ。axis-07/10/11/12 の組合せ評価が中核
metadata:
  helix_layer: L4-L9
  category: workflow
  triggers:
    - helix doctor を実行した時
    - 複数 axis が同時 WARN / FAIL した時
    - 依存グラフに orphan / missing / cycle を検出した時
    - 設計 doc が missing required doc 状態の時
    - コンポーネント間の接続欠損を検出した時
    - test_baseline との比較でデグレを検出した時
    - detection-routing に集計済シグナルを渡したい時
  verification:
    - "helix doctor が全 detector を横断実行し結果を集約済"
    - "検出した漏れ・デグレが detection-routing でモード発動につながっている"
    - "baseline が最新 commit に更新されている"
    - "デグレ検出時は fail-close で停止している"
compatibility:
  claude: true
  codex: true
```

#### SKILL.md 本文構成

- **目的**: 単工程内で見えない横断的漏れを機械的に拾い、対応モードへつなぐ
- **責務境界**: detection-routing との分担を明確化
  - cross-detection: 複数 detector の結果を集約し aggregate signal を生成 (集約)
  - detection-routing: aggregate signal を受け取り mode/priority を決定 (判断)
- **検出対象**: axis-07 / axis-10 / axis-11 / axis-12 の役割と検出内容
- **横断集約フロー**: helix-doctor → detector 横断 → 集計 → detection-routing 連携
- **デグレ回避**: baseline 更新方針 + fail-close 基準
- **detection-routing 連携**: aggregate signal の schema と渡し方
- **Forward 接続**: 検出種別ごとのルーティング先 (Reverse / Incident / Recovery)
- **完了チェック**: doctor 全件実行 + 漏れ 0 + baseline 更新の 3 点確認

#### references/ ファイル (2 件)

**references/detector-axis-map.md**

```
> 目的: cross-detection で使用する detector axis の一覧と、各 axis が検出する内容・集約方式を定義する
```

内容:
- axis-07 (doc-drift) / axis-10 (relation-graph) / axis-11 (regression) / axis-12 (connection-deficiency) の詳細説明
- 各 axis の CLI 実行例と出力形式
- aggregate signal 生成のルール (複数 axis WARN/FAIL の組合せ評価)

**references/cross-detection-checklist.md**

```
> 目的: cross-detection の実施チェックリスト。G2/G4/G9 ゲート前の横断確認手順を標準化する
```

内容:
- ゲート別チェックリスト (G2: 依存・契約漏れ / G4: デグレ / G9: 統合デグレ)
- helix doctor コマンド実行手順
- WARN / FAIL 時の対応フロー (detection-routing 連携 → PLAN 起票)

---

### §2.4 S-4: layer-context-injection (skills/workflow/layer-context-injection/)

#### SKILL.md frontmatter

```yaml
name: layer-context-injection
description: 各 L (工程 L0-L14) 入口で mandatory_skills / recommended_commands / required_agents / orchestration_mode を文脈注入し、AI の工程選択の迷いを消す機構。vmodel-semantics.yaml の injection-set と helix-context CLI が実装基盤。injection-set の実体キーは drive × layer の 20 セル構造 (4 drive × 5 layer) で管理される
metadata:
  helix_layer: L0-L14
  category: workflow
  triggers:
    - 工程 L に入る時 (L0-L14 すべて)
    - mode switch (forward / reverse / scrum / discovery 等) 時
    - 工程開始時に使うべきスキル・コマンドが不明瞭な時
    - vmodel-semantics の injection-set を更新したい時
    - learning-engine が注入セット改善を提案した時
    - 新しい L 向けスキルを injection-set に追加した時
  verification:
    - "工程 L に対応する injection-set が vmodel-semantics.yaml に定義済"
    - "injection-set のキーが drive × layer 20 セル構造 (drives.{drive}.layers.{layer}.injection) に準拠している"
    - "helix-context が当該 L の injection-set を正しく注入済"
    - "必須 agent が agent_mandatory.list_mandatory_for_phase で定義済"
    - "orchestration 方式が axis-14-orchestration-integrity で検証済"
compatibility:
  claude: true
  codex: true
```

#### SKILL.md 本文構成

- **目的**: 工程開始時の参照負荷を機械化し、AI が一から判断しなくて済む状態を作る
- **責務境界**: detection-routing / learning-engine との接続
  - layer-context-injection: injection-set の定義と実行 (helix-context)
  - learning-engine: 学習結果を injection-set に反映 (L 単位注入の更新)
  - detection-routing: injection-set の「どのモードか」情報を受け取る連携
- **注入 5 要素**: スキル / ワークフロー / サブエージェント / コマンド / オーケストレーション
- **injection-set 実体キー構造**: vmodel-semantics.yaml における injection-set の実体は `4 drive × 5 layer = 20 セル構造` (`drives.{drive}.layers.{layer}.injection`) であることを明記し、L0-L14 全工程の概念説明と区別する。SKILL.md では「L0-L14 工程別の概念」を説明しつつ、references/injection-set-schema.md では 20 セル構造の実体キーを正本とすること
- **L 単位注入セット**: references/l-unit-injection-table.md を参照
- **injection-set schema**: references/injection-set-schema.md を参照 (実体キー: `drives.{drive}.layers.{layer}.injection` = 20 セル)
- **AI の判断の迷いを消す原理**: 正本の「選択肢を事前に絞る」方針の再掲
- **オーケストレーション制御**: agent_slots / Claude Code (判断) vs Codex (実装) 二軸 / axis-14 検証
- **Forward 接続**: vmodel-semantics.yaml 更新フロー (learning-engine → injection-set 更新 → helix-context 反映)
- **エスカレーション基準**: injection-set が工程定義と衝突する場合の TL 確認
- **完了チェック**: injection-set 定義 + helix-context 注入確認 + axis-14 検証の 3 点確認

#### references/ ファイル (2 件)

**references/injection-set-schema.md**

```
> 目的: vmodel-semantics.yaml の injection-set 定義スキーマ。各 layer に注入する 5 要素の YAML 構造を標準化する
```

内容 (tl-advisor R2 P1 反映、L7-vmodel-semantics-injection-setplan v3 §2 frozen 契約と完全一致):
- injection-set YAML スキーマ定義 (**6 field**): `owner_role` / `mandatory_agents` / `recommended_agents` / `recommended_skills` / `recommended_commands` / `orchestration_mode`
- 各 field 定義と valid values (vmodel_loader.VModelSemantics._validate_injection と一致)
- `layer` は injection 内 field ではなく、`drives.{drive}.layers.{layer}.injection` の parent key (PLAN §0 で明示)
- 既存 vmodel-semantics.yaml の injection-set 現状 (L7-vmodel-semantics-injection-setplan v3 §2.E 20 セル展開、connection-frozen 参照のみ実装完了不要)

**references/l-unit-injection-table.md**

```
> 目的: 全 L0-L14 工程別の注入セット一覧テーブル。SKILL.md §L 単位の注入セット から参照する
```

内容:
- 正本 layer-context-injection.md §L 単位の注入セット のテーブルを拡張
- 各 L の owner_role / 必須 agent / スキル群 / 推奨 command / orchestration 詳細
- mode 別 (forward / reverse / scrum / discovery) の injection-set 差分

---

## §3 成果物

### 製本対象 (12 ファイル)

#### S-1 detection-routing

- `skills/workflow/detection-routing/SKILL.md` (推定 180-230 行)
- `skills/workflow/detection-routing/references/signal-to-mode-map.md` (推定 60-80 行)
- `skills/workflow/detection-routing/references/four-quadrant-evaluation.md` (推定 50-70 行)

#### S-2 learning-engine

- `skills/workflow/learning-engine/SKILL.md` (推定 180-230 行)
- `skills/workflow/learning-engine/references/recipe-pattern-template.md` (推定 80-100 行)
- `skills/workflow/learning-engine/references/learning-loop-design.md` (推定 60-80 行)

#### S-3 cross-detection

- `skills/workflow/cross-detection/SKILL.md` (推定 180-230 行)
- `skills/workflow/cross-detection/references/detector-axis-map.md` (推定 70-90 行)
- `skills/workflow/cross-detection/references/cross-detection-checklist.md` (推定 50-70 行)

#### S-4 layer-context-injection

- `skills/workflow/layer-context-injection/SKILL.md` (推定 200-250 行)
- `skills/workflow/layer-context-injection/references/injection-set-schema.md` (推定 80-100 行)
- `skills/workflow/layer-context-injection/references/l-unit-injection-table.md` (推定 80-100 行)

### 副次成果物 (1 件)

- **`skills/SKILL_MAP.md` §スキル群配置 workflow/ リスト**: 4 件追記 (detection-routing / learning-engine / cross-detection / layer-context-injection)

### 製本対象外 (後続 PLAN 候補)

- helix-context CLI 実装 (layer-context-injection の実行基盤、別 L7 impl PLAN)
- helix learn CLI 実装 (learning-engine の実行基盤、別 L7 impl PLAN)
- vmodel-semantics.yaml injection-set 全 L 入力 (L7-vmodel-semantics-injection-setplan 後続 Sprint)

---

## §4 受入条件 / DoD

### 機械検証 (必須)

**4 スキル共通:**
- [ ] 各 SKILL.md が `bash -n` / `markdownlint` を通過
- [ ] 各 SKILL.md frontmatter に `name` / `description` / `metadata.helix_layer` / `metadata.category` / `metadata.triggers` / `metadata.verification` / `compatibility` が全件存在
- [ ] enum 違反 placeholder が存在しない (`drive: execution` 等の非 enum 値がないこと)
- [ ] 各 references/ ファイル冒頭に `> 目的: ...` blockquote が存在する (skill-catalog parser 対応)

**SKILL_MAP 追記検証:**
- [ ] `skills/SKILL_MAP.md` §スキル群配置 workflow/ リストに 4 件追記済
- [ ] 追記後の SKILL_MAP.md に重複エントリが存在しない

**PLAN 検証:**
- [ ] `helix plan lint docs/plans/L7/L7-workflow-skills-pkgplan.md` PASS
- [ ] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-workflow-skills-pkgplan.md` warnings 0

### review 検証 (必須)

- [ ] tl-advisor adversarial check 第 1 ラウンド passed (Step 4)
- [ ] pmo-sonnet 4 artifact 双方向 trace 確認 (Step 13)
  - ① 正本設計 (4 正本 doc) ↔ ③ テスト設計に相当するもの (各 SKILL.md §verification)
  - ② 成果物 (4 SKILL.md + 8 references/) ↔ ④ 完了チェックが受入条件に対応
- [ ] SKILL_MAP 追記が既存エントリと整合していること (重複・矛盾なし)

### コンテンツ検証 (必須)

- [ ] 各 SKILL.md に **責務境界セクション** が存在し、近接スキルとの違いが明示されている
- [ ] 各 SKILL.md に **関連スキル / コマンド テーブル** が存在する
- [ ] 各 SKILL.md の **関連スキル / コマンド** に対応する正本 CLI / スキル名が HELIX に実在する
- [ ] detection-routing ↔ cross-detection の責務分担 (集約 vs 判断) が両 SKILL.md で整合している
- [ ] learning-engine → layer-context-injection の出力-入力関係が両 SKILL.md で整合している

---

## §5 関連 PLAN / ADR / docs

### 正本設計 (本 PLAN の直接の parent_design)

- [HELIX-workflows/helix-process/integration-map.md](../../../HELIX-workflows/helix-process/integration-map.md) — §結論と優先順位 #3 が本 PLAN の起源

### 各スキル正本 doc

- [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md) — S-1 の parent_design
- [HELIX-workflows/helix-process/learning-engine.md](../../../HELIX-workflows/helix-process/learning-engine.md) — S-2 の parent_design
- [HELIX-workflows/helix-process/cross-detection.md](../../../HELIX-workflows/helix-process/cross-detection.md) — S-3 の parent_design
- [HELIX-workflows/helix-process/layer-context-injection.md](../../../HELIX-workflows/helix-process/layer-context-injection.md) — S-4 の parent_design

### 範例・依存

- `skills/workflow/retrofit/SKILL.md` — 直近の同手法スキル化事例 (範例)
- `skills/workflow/retrofit/references/retrofit-matrix-template.md` — references/ 構造の参考
- `skills/SKILL_MAP.md` — §スキル群配置 workflow/ リスト追記対象 + §責務境界クリア化 参考パターン
- `docs/plans/L7/L7-helix-route-implplan.md` — detection-routing.md を CLI 化した実装 PLAN (S-1 の後続)。本 PLAN では route PLAN の実装完了を要求せず、signal schema v3 接続契約が frozen であることのみ参照する
- `docs/plans/L7/L7-helix-recover-implplan.md` — learning-engine / detection-routing と連携する Recovery CLI
- `docs/plans/L7/L7-vmodel-semantics-injection-setplan.md` — S-4 の injection-set 実体 (vmodel-semantics.yaml)

### 参考 (HELIX-workflows 関連)

- `HELIX-workflows/helix-process/automation-gate-map.md` — S-1/S-3 が参照する自動化ゲートマップ
- `HELIX-workflows/helix-process/cross-cutting-mechanisms.md` — S-3/S-4 の横断機構全体像

---

## §6 後続 PLAN 候補 (本 PLAN 完遂後)

| # | 後続 PLAN 候補 | 概要 | 依存 |
|---|---|---|---|
| 1 | `L7-helix-context-implplan` | helix-context CLI 実装 (layer-context-injection の実行基盤) | 本 PLAN (S-4 SKILL.md) |
| 2 | `L7-helix-learn-implplan` | helix learn CLI 実装 (learning-engine の実行基盤) | 本 PLAN (S-2 SKILL.md) |
| 3 | `L7-vmodel-semantics-injection-setplan Sprint .2` | vmodel-semantics.yaml injection-set 全 L 入力 | 本 PLAN (S-4 injection-set-schema.md) |
| 4 | integration-map #4 templates | HELIX-workflows template 群のスキル化または docs 配備 | 本 PLAN 完遂後 |
| 5 | integration-map #5 文書統合 | HELIX-workflows 複数 doc の統合・整理 | 本 PLAN 完遂後 |

---

## §7 tl-advisor 第 1 ラウンド チェック依頼事項 (PM 記録)

本 PLAN は draft 起票完了の段階。PM が tl-advisor に依頼する確認観点:

1. **4 スキルの helix_layer 整合**: S-1 (L4) / S-2 (L14) / S-3 (L4-L9) / S-4 (L0-L14) は正本 doc の記述と整合しているか
2. **detection-routing ↔ cross-detection の責務境界**: 「cross-detection が集約、detection-routing が判断」の分担が SKILL.md 本文構成として適切か
3. **learning-engine → layer-context-injection の依存順序**: S-2 → S-4 の出力-入力関係が SKILL.md の記述で明示できているか
4. **references/ 2 件構成の妥当性**: 各スキルで 2 references/ としたが、retrofit (1 references/) との比較で過剰または不足はないか
5. **SKILL_MAP.md 追記の責務境界クリア化**: SKILL_MAP §責務境界クリア化 に 4 スキルの使い分けセクションを追加すべきか、または workflow/ リスト追記のみで十分か
6. **Step 7-10 並列化の安全性**: 4 スキル並列起草でファイル衝突・内容衝突リスクがないか確認
