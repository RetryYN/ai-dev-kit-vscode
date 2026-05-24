---
plan_id: L7-docs-template-phase1-implplan
title: "L7-docs-template-phase1-implplan: 工程 L0 / L6 / L7 docs template 提供 (cli/templates/plan/v2/ 配下、phase1)"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: HELIX-workflows/helix-process/L0-concept.md
pairs_test_design:
  - HELIX-workflows/helix-process/L6-functional-design.md
  - HELIX-workflows/helix-process/L7-implementation.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check"
  - role: se
    slot_label: "SE — template ファイル実装"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: cli/templates/plan/v2/L0/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/v2/L6/template.md
    artifact_type: template
  - artifact_path: cli/templates/plan/v2/L7/template.md
    artifact_type: template
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/L0-concept.md
  - HELIX-workflows/helix-process/L6-functional-design.md
  - HELIX-workflows/helix-process/L7-implementation.md
  - HELIX-workflows/HELIX-process-L0-L14.md
  - cli/templates/plan/v2/L00-planning-template.md
  - cli/templates/plan/v2/L06-function-design-template.md
  - cli/templates/plan/v2/L07-implementation-template.md
  - docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #4](../../../HELIX-workflows/helix-process/integration-map.md)
> **本 PLAN の対象**: `cli/templates/plan/v2/` 配下に存在しない L0 / L6 / L7 の工程別 docs template (V2 命名規則準拠の PLAN starter file) を 3 件作成し、各工程の PLAN 起票を標準化する。

### 対象の位置づけ

`cli/templates/plan/v2/` には前 session (2026-05-21) で L1〜L14 工程別 15 template が起草された。ただし integration-map.md が指摘する通り、L0 / L6 / L7 は **template が存在しない穴** として残っている。

現時点で `cli/templates/plan/v2/` に格納されているのは flat 命名 (`L00-planning-template.md` 等) の 15 件であり、**サブディレクトリ `L0/template.md` 形式の template は 0 件**。本 PLAN は integration-map.md §4 の指示に従い、L0 / L6 / L7 の 3 工程分を `L<NN>/template.md` 形式で提供する (phase1)。

### parent_design を複数工程 doc で代替する理由

本 PLAN は「template ファイルを作成する L7 実装」であり、テンプレートが対応する設計 doc (L0 企画 / L6 機能設計 / L7 実装工程) が設計層にあたる。単一の parent_design を指定できないため、HELIX-workflows/helix-process/L0-concept.md を代表として frontmatter に記載し、L6 / L7 の正本は `pairs_test_design` + `related_docs` で参照する設計とした。これは template 実装という特殊性による例外であり、通常の L7 PLAN は L6 機能設計 doc を単一 parent_design とする規則を変えない。

### phase 区分の意図

- **phase1 (本 PLAN)**: L0 / L6 / L7 の 3 工程 template (最優先、V-model 設計-実装の核心部位)
- **phase2 (後続 PLAN)**: L8〜L14 の残 7 工程 template (検証・リリース・運用フェーズ)
- **phase3 (後続 PLAN)**: generates 成果物 template (retrofit-matrix / research-memo / ADR / recovery-log)

## §1 工程表 (作業手順 + 進捗)

PLAN は **工程表 (作業手順 + 進捗) + 実装計画** の 2 要素を内蔵し、作業中断時に再開可能にする。

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | 参考調査: 既存 15 template 確認 + HELIX-workflows 各工程 doc 確認 (L0 / L6 / L7) + V2 範例 (L7-vmodel-semantics-injection-setplan.md) 確認 | PM | ✅ done (本 PLAN 起票の前提リサーチ完了) |
| 2 | L0 / L6 / L7 各工程の PLAN 記載項目 確認 (HELIX-workflows 正本から抽出) | PM | ✅ done (§2.A 参照) |
| 3 | 本 PLAN draft 起票 (pmo-sonnet 担当) | PMO | ✅ done (本ファイル) |
| 4 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 5 | TL 指摘反映 (P1/P2 があれば) | PM | □ pending |
| 6 | SE 委譲: template 3 件の実ファイル作成 (helix codex --role se) | PM → SE | □ pending |
| 7 | 機械検証: plan_validator lint + ファイル存在確認 | SE | □ pending |
| 8 | pmo-sonnet 整合チェック: 既存 15 template との一貫性 + V2 命名規則 | PMO | □ pending |
| 9 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A 各工程の PLAN 記載項目 (HELIX-workflows 正本から抽出)

#### L0 企画書 (L0-concept.md より)

L0 工程の PLAN (`L0-企画書plan`) が記載すべき内容:

- 背景・目的
- 解決する課題
- スコープ (対象 / 対象外)
- 投資対効果
- 成功条件・KGI / KPI
- 想定リスク

#### L6 機能設計 (L6-functional-design.md より)

L6 工程の PLAN が記載すべき内容 (3 種の PLAN 形式が存在):

- `L6-関数仕様plan`: 関数 / メソッド仕様 / 引数 / 戻り値
- `L6-クラス設計plan`: クラス構成 / 責務
- `L6-エッジケースplan`: 境界値 / 例外・エラー処理パターン

template は汎用形として 1 ファイルで設計し、section ヘッダ `<!-- @placeholder: 関数仕様 | クラス設計 | エッジケース -->` で切り替え可能にする。

#### L7 実装 (L7-implementation.md より)

L7 工程の PLAN (`L7-<機能名>plan`) が記載すべき内容:

- 対象機能
- 実装手順 (TDD フロー: テスト実装 → 本体実装 → 3点レビュー → テストパターン追加 → テスト実施 → 修正 → 完了)
- 進捗状態

既存の `L07-implementation-template.md` (flat 命名) は概要的な scaffold であり、V2 命名の `L7/template.md` は**実際に L7 PLAN を起票する starter** として以下を追加する:

- Sprint Step 1〜8 の標準 8 ステップ (HELIX_CORE.md §Sprint Plan 標準構造 反映)
- mandatory in sprint の checklist (py_compile / lint / test / review)
- parent_design + pairs_test_design の記載例
- §2 実装計画のサブセクション例 (TDD 具体手順 / 実装ファイル一覧)

### §2.B L0 template 設計方針

**ファイルパス**: `cli/templates/plan/v2/L0/template.md`

```markdown
---
plan_id: L0-<企画名>plan
title: "L0-<企画名>plan: <タイトル placeholder>"
kind: design
layer: L0
drive: be              # be|fe|fullstack|db|agent|scrum|poc
status: draft
...
```

**section 構造**:

| § | タイトル | 内容 |
|---|---|---|
| §0 | PLAN concept | 企画の北極星指標・ゴール概要 |
| §1 | 工程表 | 参考調査→ヒアリング→draft→TLレビュー→確定 の 6〜7 step |
| §2 | 背景・目的 | 事業課題・解決したいペイン |
| §3 | 解決する課題 | 課題の構造化 (JTBD / Jobs-to-be-done 形式推奨) |
| §4 | スコープ | 対象 / 対象外 の明示 |
| §5 | 投資対効果 | ROI 概算 / リソース概算 |
| §6 | 成功条件・KGI / KPI | 定量目標 |
| §7 | 仮説リスト | 前提仮説の列挙 + 検証方法 |
| §8 | 想定リスク | 技術 / ビジネス / 体制 リスク + 緩和策 |
| §9 | G0.5 ゲート受入条件 | PM + PdM が満たすべき checklist |
| §10 | 関連 PLAN / ADR / docs | 参照先一覧 |

**frontmatter の特徴**:

- `kind=design` (L0 は設計文書層、impl ではない)
- `pairs_test_design: []` (L0 ペア凍結なし)
- `parent_design` 不要 (`# コメントアウト例として記載`)
- agent_slots に `pdm-tech-innovation` / `pdm-marketing-innovation` / `pdm-innovation-manager` を追加 (G0.5 PdM 必須)
- generates は `docs/v2/L0-<企画名>/concept.md` (kind=markdown_doc)

### §2.C L6 template 設計方針

**ファイルパス**: `cli/templates/plan/v2/L6/template.md`

```markdown
---
plan_id: L6-<機能名>plan
title: "L6-<機能名>plan: <タイトル placeholder>"
kind: design
layer: L6
drive: be              # be|fe|fullstack|db
status: draft
...
```

**section 構造**:

| § | タイトル | 内容 |
|---|---|---|
| §0 | PLAN concept | 機能設計スコープの概要 (L5 詳細設計からの委譲内容) |
| §1 | 工程表 | 参考調査→仕様確認→schema draft→TL レビュー→G6 凍結 の 7〜8 step |
| §2 | 機能スコープ | 対象機能一覧 + 対象外の明示 |
| §3 | endpoint / 関数 schema | 各 endpoint / 関数の signature + 入出力型 |
| §4 | 入出力契約 | request / response 例 (JSON / 型) |
| §5 | 状態遷移 | FSM / 状態図 (該当する場合) |
| §6 | エラー処理パターン | 境界値 / 例外種別 / HTTP status code 対応 |
| §7 | 単体テスト設計 ref | 対応する単体テスト設計 doc へのリンク (V-model L6↔L7 trace) |
| §8 | G6 凍結受入条件 | TL が承認するための checklist |
| §9 | 関連 PLAN / ADR / docs | 参照先一覧 |

**frontmatter の特徴**:

- `kind=design` (L6 は機能設計文書、impl ではない)
- `pairs_test_design: []` (L7 のみ V-model trace 必須、L6 は記載不要だがコメントで説明)
- `parent_design` 不要 (L5 詳細設計は `related_docs` で参照)
- generates は `docs/v2/L6-<機能名>/functional-design.md` (kind=markdown_doc)
- V-model L6↔L7 pair freeze の旨を §7 で明示

### §2.D L7 template 設計方針

**ファイルパス**: `cli/templates/plan/v2/L7/template.md`

```markdown
---
plan_id: L7-<機能名>plan
title: "L7-<機能名>plan: <タイトル placeholder>"
kind: impl
layer: L7
drive: be              # be|fe|fullstack
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/v2/L6-<feature>/<feature>-functional-design.md
...
```

**section 構造**:

| § | タイトル | 内容 |
|---|---|---|
| §0 | PLAN concept | 対象機能の概要 + parent_design 採用理由 (draft の場合) |
| §1 | 工程表 | Sprint Step 1〜8 (標準 8 ステップ) + 進捗欄 |
| §2 | 実装計画 | TDD 具体手順 / 実装ファイル一覧 / design 判断事項 |
| §3 | 成果物 | 製本対象ファイル一覧 (impl code + test + docs) |
| §4 | 受入条件 / DoD | 機械検証 checklist + review 検証 checklist |
| §5 | 関連 PLAN / ADR / docs | 参照先一覧 |
| §6 | 後続 PLAN 候補 | 本 PLAN 完遂後の next step |

**Sprint Step 1〜8 (標準 8 ステップ)** の記載例 (§1 工程表に展開):

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | Entry 条件確認 (前 Sprint 完遂 / dependency 確認) | PM | □ pending |
| 2 | 実装着手前調査 (helix code find / pmo-project-scout) | PM | □ pending |
| 3 | ★単体テスト実装 (L6 機能設計 pair freeze → TDD Red phase) | SE | □ pending |
| 4 | 本体実装 (TDD Green phase / Codex 委譲 or 直接) | SE | □ pending |
| 5 | ★機械チェック (py_compile / lint / yamllint / helix code stats) | SE | □ pending |
| 6 | ★テスト実施 (単体テスト / 結合テスト / 全回帰 helix test) | SE | □ pending |
| 7 | ★レビュー (セルフレビュー + pmo-sonnet G4 時) | PM / PMO | □ pending |
| 8 | commit + carry note + Exit 条件確認 (DoD) | PM | □ pending |

★ = mandatory in sprint (Sprint Exit 前必須)

**frontmatter の特徴**:

- `kind=impl` (L7 のみ impl)
- `process_layer=L7` 必須
- `parent_design=L6 機能設計 doc` 必須
- `pairs_test_design` に L7 単体テスト設計 / L8 結合テスト設計 / L9 総合テスト設計を列挙
- agent_slots に `tl-advisor` + `se` を追加 (実装レビュー必須)
- generates に impl コード + テストコード + (必要なら) markdown_doc

**V2 範例との整合**: 既存 `L7-vmodel-semantics-injection-setplan.md` (commit 8fc82dd) の frontmatter / section 構造を踏襲しつつ、**機能 PLAN 汎用 starter** としての placeholder 展開を充実させる。

## §3 成果物

### 主成果物 (3 template ファイル)

| ファイルパス | 対応工程 | frontmatter kind | 行数概算 |
|---|---|---|---|
| `cli/templates/plan/v2/L0/template.md` | L0 企画書 | design | 120〜150 行 |
| `cli/templates/plan/v2/L6/template.md` | L6 機能設計 | design | 130〜160 行 |
| `cli/templates/plan/v2/L7/template.md` | L7 実装スプリント | impl | 160〜200 行 |

### 副次成果物

- 各 `L<NN>/` ディレクトリの新設 (L0 / L6 / L7 の 3 ディレクトリ)
- 既存 `L07-implementation-template.md` (flat 命名) は **deprecated 予定** として README.md にコメント追加 (phase2 で整理)

### 確認事項 (既存 template との関係)

既存の `L00-planning-template.md` / `L06-function-design-template.md` / `L07-implementation-template.md` (flat 命名 15 件) は V2 命名サブディレクトリ形式の template とは **別物** として共存する。flat 命名は `helix plan draft` CLI の旧 backend として残置し、サブディレクトリ形式は新規 PLAN 手動起票のための starter ファイルと位置づける。統合判断は phase3 carry。

## §4 受入条件 / DoD

### 機械検証

- [ ] `cli/templates/plan/v2/L0/template.md` が存在する (`ls -la cli/templates/plan/v2/L0/`)
- [ ] `cli/templates/plan/v2/L6/template.md` が存在する
- [ ] `cli/templates/plan/v2/L7/template.md` が存在する
- [ ] 各 template の frontmatter が YAML として valid (`python3 -c "import yaml; yaml.safe_load(open('<path>'))"` 成功)
- [ ] `python3 cli/lib/plan_validator.py docs/plans/L7/L7-docs-template-phase1-implplan.md` PASS (warnings 0 件)
- [ ] `kind=design` (L0 / L6) / `kind=impl` (L7) が plan_validator の enum に合致する
- [ ] `layer=L0` / `layer=L6` / `layer=L7` が plan_validator の enum に合致する
- [ ] 各 template の `generates[].artifact_type` が plan_validator 許可値 (template / markdown_doc / python_module 等) を使っている
- [ ] L7 template に Sprint Step 1〜8 のテーブルが含まれる
- [ ] L7 template に mandatory in sprint (★) のマーキングが含まれる
- [ ] L0 template に G0.5 ゲート受入条件セクション (§9 相当) が含まれる
- [ ] L6 template に V-model L6↔L7 pair freeze の言及が含まれる

### review 検証

- [ ] tl-advisor adversarial check 第 1 ラウンド passed (本 PLAN §1 Step 4)
- [ ] pmo-sonnet 整合チェック: 既存 15 template との命名・section 一貫性 (本 PLAN §1 Step 8)
- [ ] 3 template の section 構造が §2.B / §2.C / §2.D の設計方針と整合している
- [ ] V2 命名規則 (`L<NN>-○○○plan` 形式の plan_id placeholder) が 3 template すべてに含まれる

## §5 関連 PLAN / ADR / docs

- **integration-map.md 正本**: [HELIX-workflows/helix-process/integration-map.md §結論と優先順位 #4](../../../HELIX-workflows/helix-process/integration-map.md) — 本 PLAN の根拠
- **HELIX-workflows 工程 doc**:
  - [HELIX-workflows/helix-process/L0-concept.md](../../../HELIX-workflows/helix-process/L0-concept.md) — L0 企画書 工程定義
  - [HELIX-workflows/helix-process/L6-functional-design.md](../../../HELIX-workflows/helix-process/L6-functional-design.md) — L6 機能設計 工程定義
  - [HELIX-workflows/helix-process/L7-implementation.md](../../../HELIX-workflows/helix-process/L7-implementation.md) — L7 実装 工程定義
- **HELIX-process 全工程**: [HELIX-workflows/HELIX-process-L0-L14.md](../../../HELIX-workflows/HELIX-process-L0-L14.md)
- **V2 範例 PLAN**: [docs/plans/L7/L7-vmodel-semantics-injection-setplan.md](./L7-vmodel-semantics-injection-setplan.md) — V2 命名規則初の起票事例
- **既存 template (flat 命名)**:
  - [cli/templates/plan/v2/L00-planning-template.md](../../../cli/templates/plan/v2/L00-planning-template.md)
  - [cli/templates/plan/v2/L06-function-design-template.md](../../../cli/templates/plan/v2/L06-function-design-template.md)
  - [cli/templates/plan/v2/L07-implementation-template.md](../../../cli/templates/plan/v2/L07-implementation-template.md)
- **Sprint Plan 標準構造**: `helix/HELIX_CORE.md §Sprint Plan 標準構造` (Sprint Step 1〜8 の正本)
- **V-model 4 artifact 双方向 trace**: `helix/HELIX_CORE.md §設計⇔テスト対応` (L6↔L7 pair freeze の正本)
- **plan_validator**: `cli/lib/plan_validator.py` (frontmatter enum 検証に使用)

## §6 後続 PLAN 候補

### 直接後続 (本 PLAN 完遂が前提)

- **phase2 PLAN**: `L7-docs-template-phase2-implplan` — L8〜L14 の残 7 工程 template 提供 (検証・リリース・運用フェーズ、integration-map.md #4 残分)
- **phase3 PLAN**: `L7-docs-template-phase3-implplan` — generates 成果物 template (retrofit-matrix / research-memo / ADR / recovery-log、integration-map.md #4 generates 分)

### 関連後続 (並行起票可)

- `L7-docs-template-drive-agent-implplan` — drive=agent の 2 段設計 Stage 2 昇華 template (integration-map.md §テンプレートの穴に記載)
- flat 命名 15 件の deprecated 化 + サブディレクトリ形式への統合 (phase3 以降で整理、`cli/templates/plan/v2/README.md` 更新込み)
- `helix plan draft` CLI の backend を flat 命名 → サブディレクトリ形式に切り替える実装 (L7 実装スプリント、別 PLAN 候補)
