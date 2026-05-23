---
doc_id: process-L4-implementation
title: "L4 実装工程の進め方 — PLAN は本工程の subordinate"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L4
pairs_with_test_phase: L4_unit_and_integration
---

# L4 実装工程の進め方

## 入力 (必須)

- `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT,D-STATE,D-UI}/<feature>.md` (L3 工程の成果物)
- `docs/v2/L4-test-design/<feature>-unit-test-design.md` (L3 工程でペア凍結済、V-model artifact ③ 単体)
- `docs/v2/L4-test-design/<feature>-integration-test-design.md` (L3 工程でペア凍結済、artifact ③ 結合)
- 工程表 (`.helix/task-plan.yaml` or L3 schedule doc)
- skill: `common/coding` / `common/testing` / `agent-skills/incremental-implementation` / `agent-skills/test-driven-development` / `tools/ai-coding`

## 進め方

### Step 1: L3 設計から PLAN を作成
- L3 設計 doc 1 つに対し、1 つ以上の L4 PLAN を起票
- PLAN template: `cli/templates/plan/impl/template.md`
- frontmatter 必須 field:
  ```yaml
  plan_id: PLAN-NNN-<slug>          # 連番 + slug (移行期、将来 ULID 化候補)
  kind: impl                         # design は L2/L3 工程で完結、impl は L4 のみ
  layer: L4
  drive: be|fe|fullstack|db|agent|scrum
  parent_design: docs/v2/L3-detailed-design/<area>/<feature>.md   # ★必須、L3 設計 doc への path
  pairs_test_design:                                               # ★必須、artifact ③ への path
    - docs/v2/L4-test-design/<feature>-unit-test-design.md
    - docs/v2/L4-test-design/<feature>-integration-test-design.md
  dependencies:
    parent: PLAN-NNN-parent          # 上位 PLAN があれば
    requires: []
    blocks: []
  ```
- PLAN.md 本文は **Sprint .1〜.5 の実装計画のみ**。背景 / 設計 / 要件は `parent_design` の doc を参照、コピペしない

### Step 2: Sprint .1 (Entry)
- 前 PLAN の完了確認 / 依存条件確認 / role 整合確認
- `helix code find` で再利用候補 / 重複シンボル / 既存テストの有無確認

### Step 3: Sprint .2 (実装、TDD)
- L3 単体テスト設計 (artifact ③) から **失敗するテスト** を先に書く (artifact ④ 着手)
- テストが通る最小実装 (artifact ②)
- skill: `agent-skills/test-driven-development`

### Step 4: Sprint .3 (機械チェック + テスト)
- `python3 -m py_compile` / `bash -n` / `helix code stats` / `helix doctor`
- 該当範囲のテスト + 全回帰 (`helix test`)
- mandatory in sprint (`helix/HELIX_CORE.md §Sprint Plan 標準構造` 参照)

### Step 5: Sprint .4 (レビュー)
- セルフレビュー (Opus)
- `pmo-sonnet review` (G2/G4 時)
- on-demand: `tl-advisor` (技術選択で迷ったとき adversarial check)
- skill: `common/code-review` / `agent-skills/code-review-and-quality`

### Step 6: Sprint .5 (Exit + commit)
- DoD 確認
- carry note 残し
- commit message に `PLAN-NNN sprint .X` 明示

### Step 7: G4 ゲート通過判定
- mandatory step 全 PASS + V-model 4 artifact 双方向 trace 完備
- セキュリティ② + ミニレトロ

## 成果物

- **コード**: `cli/lib/<module>.py` / `cli/helix-<command>` 等 (artifact ②)
- **テストコード**: `cli/lib/tests/test_<module>.py` (artifact ④)
- **テスト実行結果**: pytest / bats raw output (artifact ④ の動作証明)
- **PLAN doc**: `docs/plans/PLAN-NNN-<slug>.md` (本工程の管理 doc、設計 doc ではない)
- **トレーサビリティ**: `helix.db.plan_registry` / `helix.db.sprint_progress` (V5 framework #8 完遂後に自動同期)

## PLAN は L4 工程の subordinate

PLAN は **本工程の中で起こされる実装管理単位**であり、L1/L2/L3 工程では起票しない。PLAN.md に背景 / 要件 / 設計を書くのは V-model 違反 (PLAN-156 / PLAN-224 で発覚)。

V-model 4 artifact 双方向 trace は本工程で確立される:

```
① 設計 (L3 doc)        ←対応→  ③ テスト設計 (L4-test-design/)
       ↓                              ↓
② 実装コード (本工程出力) ←対応→  ④ テストコード (本工程出力)
```

## ゲート

- **G4 (実装凍結ゲート)**: TL + PM 判定、セキュリティ② + ミニレトロ + V-model テスト実装網羅
- mandatory subagent: `qa-test` / `code-reviewer` / `security-audit` (PLAN-076 工程別 subagent 起動マップ参照)

## 関連 skill

- `common/coding` / `common/testing` / `common/refactoring` / `common/code-review`
- `agent-skills/incremental-implementation` / `agent-skills/test-driven-development`
- `tools/ai-coding` (Codex / Claude harness)
- `workflow/quality-lv5` (G4 で読まれる)

## アンチパターン

- ❌ `parent_design:` 不在で PLAN 起票 (本日 PLAN-156/PLAN-224 で発覚した V-model 違反)
- ❌ PLAN.md 内に背景 / 設計を書く (L3 設計 doc を `parent_design:` 参照すれば不要)
- ❌ 単体テスト / 結合テスト設計 (artifact ③) を L3 工程で作らずに L4 で後追い (V-model 違反、L3 工程で pair 凍結すべき)
- ❌ L3 設計 doc なしに直接 L4 PLAN を起票 (本日 PLAN-156 / PLAN-224 で発覚、設計工程を skip)
- ❌ Codex 委譲を `helix codex` 直接 + ファイル衝突未確認で並列起動 (`helix workspace exec` 経由が default、PLAN-156/PLAN-224 完遂分の活用)
- ❌ commit を skip して次 Sprint へ進む (DoD trace が失われる)
