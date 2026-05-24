---
plan_id: L7-generates-templates-implplan
title: "L7-generates-templates-implplan: generates 成果物テンプレート 4 種整備 — retrofit-matrix / research-memo / ADR / recovery-log"
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
  - docs/plans/L7/L7-generates-templates-implplan.md
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cli/templates/generates/ 4 template 実装 + helix init コピー連携"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 整合チェック + 既存契約との乖離検出"
  - role: tl-advisor
    slot_label: "TL — template schema 設計 adversarial check (recovery-log 既存契約整合 / ADR Nygard-MADR 慣行)"
generates:
  - artifact_path: cli/templates/generates/retrofit-matrix/template.yaml
    artifact_type: yaml_config
  - artifact_path: cli/templates/generates/research-memo/template.md
    artifact_type: markdown_doc
  - artifact_path: cli/templates/generates/adr/template.md
    artifact_type: markdown_doc
  - artifact_path: cli/templates/generates/recovery-log/template.md
    artifact_type: markdown_doc
  - artifact_path: cli/templates/generates/README.md
    artifact_type: markdown_doc
dependencies:
  requires:
    - L7-helix-recover-implplan
  blocks: []
  related:
    - L7-helix-route-implplan
    - L7-vmodel-semantics-injection-setplan
related_docs:
  - HELIX-workflows/helix-process/integration-map.md
  - HELIX-workflows/helix-process/retrofit-workflow.md
  - HELIX-workflows/helix-process/recovery-workflow.md
  - HELIX-workflows/helix-process/research-workflow.md
  - skills/workflow/retrofit/references/retrofit-matrix-template.md
  - cli/lib/recovery_plan_check.py
  - docs/adr/ADR-001-deliverable-matrix-as-source-of-truth.md
  - docs/research/PLAN-029-research-findings.md
---

# L7-generates-templates-implplan: generates 成果物テンプレート 4 種整備

## §0 PLAN concept

### 背景

HELIX integration-map.md §テンプレートの穴 の通り、PLAN kind 11 種の雛形は揃っているが、
その PLAN が生む成果物 (generates) の雛形が 4 種欠落している。

| 欠落 template | 生成元 PLAN kind | 保存先 |
|---|---|---|
| retrofit-matrix | kind=retrofit | docs/plans/\<slug\>-retrofit-matrix.md |
| research-memo | kind=research | docs/research/\<slug\>-research-findings.md |
| ADR | kind=design / impl (L2 大局判断) | docs/adr/ADR-NNN-\<slug\>.md |
| recovery-log | kind=recovery | docs/recovery-log/\<slug\>-recovery-log.md |

設計・仕様は確定済み (integration-map.md §結論と優先順位 #4 「新規判断は不要」)。
残るはリポジトリ上の定義作業。

### 整合性要件

1. **retrofit-matrix**: `skills/workflow/retrofit/references/retrofit-matrix-template.md` と
   内容を二重管理しない。既存 `.md` を参照基盤とし、`cli/templates/generates/` は
   yaml 形式の雛形として機械生成に適した正本を置く。
   `HELIX-workflows/helix-process/retrofit-workflow.md` の Phase 構成と一致させる。

2. **research-memo**: `docs/research/PLAN-029-research-findings.md` の実績形式を正本とし、
   `helix research --topic ... --memo` コマンド出力と互換な見出し構造を維持する。
   ADR 起票判断セクションを末尾に置き、research → ADR の連鎖を明示する。

3. **ADR**: `docs/adr/ADR-001〜032` の 32 件慣行を踏襲する。
   frontmatter キー (adr_id / title / status / date / layer) と
   本文見出し (Status / Context / Decision / Consequences / Alternatives) を維持する。
   MADR 2.1.2 の decision_drivers セクションを追加し、HELIX L2 凍結 snapshot として使える形式にする。

4. **recovery-log**: `cli/lib/recovery_plan_check.py::REQUIRED_TEMPLATE_SECTIONS` の
   7 セクション (事故記録 / timeline / 訂正履歴 / 中間結論 / context 再構築 / 再開ポイント / 再発防止)
   に **完全準拠**。`_SECTION_MARKERS` の別名 (タイムライン / 認識訂正履歴 / context reconstruction / resume point / recurrence prevention)
   も見出しに含め、機械検証 (`check_recovery_template_sections`) が PASS できる形式にする。
   `L7-helix-recover-implplan` が実装する `dump_state()` 出力と同一 schema を維持する。

---

## §1 工程表

### Sprint 全体構成

| Sprint | 内容 | 担当 | 依存 |
|---|---|---|---|
| Sprint .1 | tl-advisor adversarial check + template schema 設計確定 | TL / PM | — |
| Sprint .2 | retrofit-matrix/template.yaml 実装 + 検証 | SE | Sprint .1 |
| Sprint .3 | research-memo/template.md 実装 + 検証 | SE | Sprint .1 |
| Sprint .4 | adr/template.md 実装 + 検証 | SE | Sprint .1 |
| Sprint .5 | recovery-log/template.md 実装 + 機械検証 PASS | SE | Sprint .1 + L7-helix-recover-implplan |
| Sprint .6 | README.md + helix init コピー連携 + 統合検証 | SE | Sprint .2〜.5 |
| Sprint .7 | pmo-sonnet 整合チェック + DoD 確認 | PMO / PM | Sprint .6 |

### Sprint 標準 8 ステップ (各 Sprint 共通)

```
Step 1: Entry 条件確認  (前 Sprint 完遂 / dependency 確認)
Step 2: 実装着手前       (helix code find / 既存 template 確認)
Step 3: 実装            (SE 委譲)
Step 4: 機械チェック    (yamllint / markdownlint / bash -n)
Step 5: テスト起動      (該当範囲 pytest / check_recovery_template_sections)
Step 6: レビュー        (セルフ + pmo-sonnet)
Step 7: commit          (1 Sprint = 1 commit 原則)
Step 8: Exit 条件確認   (DoD チェックリスト)
```

---

## §2 実装計画

### Sprint .1: tl-advisor adversarial check + schema 設計確定

**目的**: 4 template の schema を確定させ、既存契約・慣行との乖離がないことを tl-advisor で保証する。

**確認事項**:
- retrofit-matrix: yaml 形式と既存 `.md` テンプレートの棲み分け設計
- research-memo: `helix research` CLI 出力仕様との整合 (見出し名・順序)
- ADR: 既存 32 件 frontmatter 形式と新 template の後方互換性
- recovery-log: `REQUIRED_TEMPLATE_SECTIONS` 完全充足の機械検証可否

**実行コマンド**:
```bash
helix codex --role tl-advisor --task "generates template 4 種 schema 設計 adversarial check:
- retrofit-matrix yaml 形式設計
- research-memo helix research CLI 整合
- ADR MADR/Nygard 慣行整合
- recovery-log recovery_plan_check.py 完全準拠確認"
```

**Exit 条件**: tl-advisor 承認 + PM の schema 最終確定

---

### Sprint .2: retrofit-matrix/template.yaml

**配置先**: `cli/templates/generates/retrofit-matrix/template.yaml`

**設計方針**:
- `skills/workflow/retrofit/references/retrofit-matrix-template.md` の内容を YAML 雛形として再表現
- 二重管理回避: `.md` は人間向け説明、`.yaml` は機械生成向け構造正本
- `helix retrofit matrix` コマンド (将来) が読み込む形式に準拠

**YAML 構造**:

```yaml
# retrofit-matrix/template.yaml — 保存先: docs/plans/<slug>-retrofit-matrix.yaml
retrofit_matrix:
  slug: "<プロジェクト・タスクの識別子>"
  plan_id: "<L7-xxx-implplan>"
  created: "YYYY-MM-DD"
  owner: "TL"
  status: draft  # draft | active | completed
  baseline_test_pass_count: 0
  target_env:
    from: "<旧環境の概要>"
    to: "<新環境の概要>"

impact_table:
  - id: 1
    component: "<対象コンポーネント>"
    version_from: "<旧バージョン>"
    version_to: "<新バージョン>"
    affected_files:
      - "<影響ファイルパス>"
    priority: High  # Critical | High | Medium | Low
    breaking_change: "<破壊的変更の概要 or なし>"
    migration_ref: "<Migration 手順 URL or なし>"

phases:
  - id: phase-1
    name: "<フェーズ名>"
    targets:
      - "<移行対象ファイル / モジュール>"
    rollback: "<ロールバック手順>"
    acceptance:
      - "<受入条件>"
    owner: "<担当ロール: TL | SE | dba>"
    estimated_effort: "<工数見積: hours>"
    status: not_started  # not_started | in_progress | completed | rolled_back

rollback_detail:
  - phase_id: phase-1
    trigger_conditions:
      - "<FAIL 件数 X 以上>"
      - "<本番エラー率 Y% 超過>"
    approval: "TL + PM"
    steps:
      - "git revert <commit hash>"
      - "pip install -r requirements.lock"
      - "helix test"
    checklist:
      - "旧環境 smoke test PASS"
      - "DB 整合性確認"
      - "SLO モニタリング正常"

completion:
  completed_at: null
  baseline_test_pass_count_after: null
  performance_comparison:
    p50_before: null
    p50_after: null
    p95_before: null
    p95_after: null
  issues_encountered: []
  deprecated_artifacts: []
```

**機械検証**: `yamllint cli/templates/generates/retrofit-matrix/template.yaml`

---

### Sprint .3: research-memo/template.md

**配置先**: `cli/templates/generates/research-memo/template.md`

**設計方針**:
- `docs/research/PLAN-029-research-findings.md` の実績形式を正本参照
- `helix research --topic ... --memo` CLI が生成するファイルと同一見出し構造
- 末尾に ADR 起票判断セクションを置き、research → ADR 連鎖を明示

**markdown 構造**:

```markdown
---
research_id: "<PLAN-NNN-research-findings>"
topic: "<調査テーマ>"
question: "<調査で答えたい問い>"
status: draft  # draft | complete | archived
created: "YYYY-MM-DD"
owner: "<PM | TL>"
related_plan: "<L<NN>-xxx>"
---

# <topic> — 調査概要

## 調査概要

- 目的: <問いに対する答えを得るための調査目的>
- 範囲: <調査の対象範囲 (Web / GitHub / 公式 docs / 著名技術ブログ)>
- 評価軸: <HELIX 適合性 / 運用強制力 / 導入コスト / 監査可能性 / 拡張性>
- 不確実性: <調査時点の限界と再確認が必要な項目>

## <テーマ A>

### A.1 <調査項目タイトル>

- URL: <一次ソース URL>
- 出版元 / 公開日: <出版元> / <公開日 or 公開日不明>
- 概要: <内容の概要>
- メリット: <HELIX 適用時のメリット>
- デメリット: <HELIX 適用時のデメリット・制約>
- 推奨度: 高 | 中 | 低

## findings まとめ

| 項目 | 推奨度 | 採用判断 | 備考 |
|---|---|---|---|
| <A.1> | 高 | 採用 | |

## ADR 起票判断

- ADR 起票が必要か: Yes | No
- 理由: <大局判断が含まれる場合は Yes、既存方針の実装のみなら No>
- 候補 ADR: ADR-NNN-<slug> (未起票 | 起票済)
- next_action: <ADR 起票 | PLAN 実装着手 | 追加調査>
```

**機械検証**: `markdownlint cli/templates/generates/research-memo/template.md`

---

### Sprint .4: adr/template.md

**配置先**: `cli/templates/generates/adr/template.md`

**設計方針**:
- `docs/adr/ADR-001〜032` 32 件の慣行 (Nygard ADR + MADR 2.1.2 混在) を踏襲
- frontmatter キー: `adr_id / title / status / date / layer`
- 本文見出し: `Status / Context / Decision / Consequences / Alternatives / Decision Drivers`
- HELIX L2 凍結 snapshot として利用できる形式

**markdown 構造**:

```markdown
---
adr_id: "ADR-NNN"
title: "ADR-NNN: <タイトル>"
status: Proposed  # Proposed | Accepted | Deprecated | Superseded
date: "YYYY-MM-DD"
layer: L2
related_plan: "<L<NN>-xxx>"
supersedes: null  # 廃止する ADR ID or null
superseded_by: null
---

# ADR-NNN: <タイトル>

## Status

Proposed

## Context

<この決定が必要になった背景・制約・問題>

現行の状態:
- <現状 A>
- <現状 B>

この変更で以下を同時に満たす必要がある:
- <要件 1>
- <要件 2>

## Decision Drivers

- <判断の軸 1 (例: 監査可能性)>
- <判断の軸 2 (例: 導入コストの最小化)>
- <判断の軸 3 (例: 既存 HELIX 慣行との整合)>

## Decision

<選択した設計・方針の宣言>

### 1. <実装要点 1>

<詳細>

### 2. <実装要点 2>

<詳細>

## Consequences

### Positive

- <利点 1>
- <利点 2>

### Negative / Trade-offs

- <懸念 1>
- <懸念 2>

### Neutral

- <中立的変化>

## Alternatives Considered

### Alternative A: <代替案名>

- 概要: <内容>
- 不採用理由: <理由>

### Alternative B: <代替案名>

- 概要: <内容>
- 不採用理由: <理由>

## Links

- 関連 PLAN: <L<NN>-xxx>
- 関連 ADR: ADR-NNN
- 参照 doc: <URL or ファイルパス>
```

**機械検証**: `markdownlint cli/templates/generates/adr/template.md`

---

### Sprint .5: recovery-log/template.md

**配置先**: `cli/templates/generates/recovery-log/template.md`

**設計方針**:
- `cli/lib/recovery_plan_check.py::REQUIRED_TEMPLATE_SECTIONS` の 7 セクションに **完全準拠**
- `_SECTION_MARKERS` の別名を見出しに含め、`check_recovery_template_sections()` が PASS する形式
- `L7-helix-recover-implplan` の `dump_state()` 出力と同一 schema
- 保存先: `docs/recovery-log/<slug>-recovery-log.md`

**必須セクション対照** (recovery_plan_check.py 実装との対応):

| REQUIRED_TEMPLATE_SECTIONS | _SECTION_MARKERS | 見出しに使う表記 |
|---|---|---|
| 事故記録 | ("事故記録",) | `## 事故記録` |
| timeline | ("timeline", "タイムライン") | `## timeline / タイムライン` |
| 訂正履歴 | ("認識訂正履歴", "訂正履歴") | `## 認識訂正履歴 / 訂正履歴` |
| 中間結論 | ("中間結論",) | `## 中間結論` |
| context 再構築 | ("context 再構築", "context reconstruction") | `## context 再構築 / context reconstruction` |
| 再開ポイント | ("再開ポイント", "resume point") | `## 再開ポイント / resume point` |
| 再発防止 | ("再発防止", "recurrence prevention") | `## 再発防止 / recurrence prevention` |

**markdown 構造**:

```markdown
---
recovery_log_id: "<PLAN-kind-recovery-NNN>"
related_plan: "<L<NN>-xxx-implplan>"
status: active  # active | resolved | archived
created: "YYYY-MM-DD HH:MM"
owner: "<PM | TL>"
trigger: "<発火条件: 想定外大規模変更 | 工程逸脱 | 認識ズレ蓄積 | 予算超過>"
severity: P1  # P0 | P1 | P2
---

# Recovery Log: <recovery_log_id>

## 事故記録

- 発生日時: YYYY-MM-DD HH:MM
- 発見者: <PM | TL | 自動検出>
- 発火条件: <4 発火条件のいずれか>
- 影響範囲: <影響を受けたファイル / フェーズ / 成果物>
- 現時点の状態: <active | escalated | resolving>

## timeline / タイムライン

| 時刻 | イベント | 対応者 | 結果 |
|---|---|---|---|
| HH:MM | <何が起きたか> | <PM | TL | agent> | <結果・次アクション> |
| HH:MM | | | |

## 認識訂正履歴 / 訂正履歴

| # | 誤認識 | 正しい認識 | 訂正タイミング | 根拠 |
|---|---|---|---|---|
| 1 | <誤解していた内容> | <正しい内容> | <発覚したタイミング> | <根拠 doc / commit> |

## 中間結論

- 収束状況: <partial | full>
- 暫定対応: <実施した暫定措置>
- 残課題: <まだ解決していない問題>
- 判断保留事項: <次 session で確認が必要な事項>

## context 再構築 / context reconstruction

再開時に必要な最小コンテキスト:

```
phase: <現在の HELIX フェーズ>
active_plan: <L<NN>-xxx-implplan>
last_commit: <git commit hash>
key_decisions: |
  - <直近の重要判断 1>
  - <直近の重要判断 2>
open_questions:
  - <未解決の問い 1>
```

## 再開ポイント / resume point

- 再開コマンド: `helix handover resume` → RESUME.md 確認
- 再開前確認事項:
  - [ ] ESCALATION.md を Read して状況把握
  - [ ] git log で最終 commit 確認
  - [ ] helix doctor で健全性確認
- 担当: <PM | TL>
- 推定再開コスト: <Small | Medium | Large>

## 再発防止 / recurrence prevention

| # | 原因 | 防止策 | 実装方法 | 優先度 |
|---|---|---|---|---|
| 1 | <根本原因> | <防止策の概要> | <hook / lint / PLAN 追加等> | P0 | P1 | P2 |

- carry PLAN 候補: <関連 PLAN ID or 新規起票提案>
- framework 改善提案: <CLAUDE.md / HELIX_CORE.md 等への反映候補>
```

**機械検証**:
```bash
python3 -c "
from cli.lib.recovery_plan_check import check_recovery_template_sections
result = check_recovery_template_sections('cli/templates/generates/recovery-log/template.md')
assert result == [], f'missing sections: {result}'
print('PASS: 7 sections OK')
"
```

---

### Sprint .6: README.md + helix init コピー連携

**配置先**: `cli/templates/generates/README.md`

**内容**:

```markdown
# cli/templates/generates/

PLAN が `generates:` フィールドで宣言する成果物の雛形 (template) ディレクトリ。

## 収録 template

| template | 保存先 (project 内) | 生成元 kind |
|---|---|---|
| retrofit-matrix/template.yaml | docs/plans/<slug>-retrofit-matrix.yaml | retrofit |
| research-memo/template.md | docs/research/<slug>-research-findings.md | research |
| adr/template.md | docs/adr/ADR-NNN-<slug>.md | design / impl (L2 snapshot) |
| recovery-log/template.md | docs/recovery-log/<slug>-recovery-log.md | recovery |

## 使用方法

### helix init 経由 (推奨)

`helix init` 実行時に `cli/templates/generates/` 配下が
`docs/adr/`, `docs/research/`, `docs/recovery-log/` 等へコピーされる。

### 手動コピー

```bash
cp cli/templates/generates/adr/template.md docs/adr/ADR-NNN-<slug>.md
cp cli/templates/generates/recovery-log/template.md docs/recovery-log/<slug>-recovery-log.md
```

## 機械検証

recovery-log template は `cli/lib/recovery_plan_check.py` の
`check_recovery_template_sections()` で 7 セクション充足を確認できる。

```bash
python3 -c "
from cli.lib.recovery_plan_check import check_recovery_template_sections
r = check_recovery_template_sections('cli/templates/generates/recovery-log/template.md')
print('OK' if not r else f'missing: {r}')
"
```
```

**helix init コピー連携**:

`cli/helix-init` または `cli/templates/` の既存コピー処理に以下を追加する:

```bash
# helix-init 内の generates template コピー処理
GENERATES_SRC="$HELIX_HOME/cli/templates/generates"
if [ -d "$GENERATES_SRC" ]; then
    mkdir -p docs/adr docs/research docs/recovery-log
    # README のみコピー、template ファイルは helix generates コマンド経由
fi
```

**機械検証**: `bash -n cli/helix-init` (構文検証)

---

### Sprint .7: pmo-sonnet 整合チェック + DoD 確認

**実行**:
```bash
helix claude --role pmo --model sonnet --execute --task "
L7-generates-templates-implplan Sprint .6 完了後の整合チェック:
1. recovery-log/template.md の 7 セクション充足確認 (check_recovery_template_sections)
2. adr/template.md の既存 docs/adr/ 32 件 frontmatter 形式との整合
3. retrofit-matrix/template.yaml と skills/workflow/retrofit/references/retrofit-matrix-template.md の二重管理確認
4. research-memo/template.md と docs/research/PLAN-029-research-findings.md の見出し整合
5. 4 artifact 双方向 trace (generates フィールド → 実ファイル → 参照 doc) の確認
"
```

---

## §3 成果物一覧

| # | 成果物パス | 形式 | Sprint |
|---|---|---|---|
| 1 | cli/templates/generates/retrofit-matrix/template.yaml | yaml_config | .2 |
| 2 | cli/templates/generates/research-memo/template.md | markdown_doc | .3 |
| 3 | cli/templates/generates/adr/template.md | markdown_doc | .4 |
| 4 | cli/templates/generates/recovery-log/template.md | markdown_doc | .5 |
| 5 | cli/templates/generates/README.md | markdown_doc | .6 |

---

## §4 受入条件 / DoD

### 機械検証 (mandatory in sprint)

- [ ] `yamllint cli/templates/generates/retrofit-matrix/template.yaml` — PASS
- [ ] `markdownlint cli/templates/generates/research-memo/template.md` — PASS
- [ ] `markdownlint cli/templates/generates/adr/template.md` — PASS
- [ ] `markdownlint cli/templates/generates/recovery-log/template.md` — PASS
- [ ] `check_recovery_template_sections("cli/templates/generates/recovery-log/template.md")` — `[]` (missing なし)
- [ ] `helix plan lint docs/plans/L7/L7-generates-templates-implplan.md` — PASS
- [ ] `helix doctor` — 既存 PASS 数を維持 (warn 増加は許容、fail 増加は禁止)

### 内容整合検証

- [ ] retrofit-matrix/template.yaml の `phases` 構造が `retrofit-matrix-template.md` の Phase 構成と一致
- [ ] research-memo/template.md の見出しが `PLAN-029-research-findings.md` と同一順序
- [ ] adr/template.md の frontmatter キーが `docs/adr/ADR-001〜032` の慣行と後方互換
- [ ] recovery-log/template.md の全 7 セクション見出しが `_SECTION_MARKERS` のいずれかの alias を含む
- [ ] recovery-log schema が `L7-helix-recover-implplan` の `dump_state()` 出力と互換 (依存 PLAN 完了後に確認)

### レビュー

- [ ] tl-advisor adversarial check PASS (Sprint .1)
- [ ] pmo-sonnet 整合チェック PASS (Sprint .7)
- [ ] PM 最終確認

---

## §5 関連 doc

| doc | 参照目的 |
|---|---|
| HELIX-workflows/helix-process/integration-map.md | テンプレートの穴 §結論と優先順位 #4 |
| HELIX-workflows/helix-process/retrofit-workflow.md | retrofit-matrix Phase 構成の整合 |
| HELIX-workflows/helix-process/recovery-workflow.md | recovery-log schema の整合 |
| HELIX-workflows/helix-process/research-workflow.md | research-memo 見出し構造の整合 |
| skills/workflow/retrofit/references/retrofit-matrix-template.md | retrofit-matrix 既存 .md 正本 |
| cli/lib/recovery_plan_check.py | recovery-log 7 セクション機械検証基盤 |
| docs/adr/ADR-001-deliverable-matrix-as-source-of-truth.md | ADR 慣行 (frontmatter + 見出し) |
| docs/research/PLAN-029-research-findings.md | research-memo 実績形式 |
| cli/templates/plan/ | 既存 PLAN kind template (この PLAN は generates 成果物側を対象とする) |

---

## §6 後続 PLAN 候補

| 候補 | 内容 | 優先度 |
|---|---|---|
| L7-generates-l0-l14-templates-implplan | 工程テンプレート補完: L0 / L6〜L14 の不足分 (integration-map §テンプレートの穴 続き) | P2 |
| L7-helix-init-generates-integration-implplan | `helix init` での generates template 自動コピー本実装 (Sprint .6 の helix-init 連携を完全実装) | P2 |
| ADR-NNN | retrofit-matrix の yaml vs. md 二重管理廃止方針 (どちらを正本とするか L2 大局判断) | P2 (二重管理が問題化した場合) |
