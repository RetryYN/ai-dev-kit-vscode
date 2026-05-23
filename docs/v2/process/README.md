---
doc_id: process-overview
title: "HELIX 工程定義概観 — 工程 ⊃ 成果物 ⊃ PLAN の構造"
status: maintained
created: 2026-05-24
owner: PM
---

# HELIX 工程定義概観

## 基本構造

HELIX V2 は **工程 (process)** を起点とする。PLAN は **L4 実装工程の subordinate** であり、PLAN が工程を先導することはない。

```
工程 (L1〜L11)
  ⊃ 進め方 (process: 何をどう進めるか)
  ⊃ 入力 (前段工程の成果物)
  ⊃ 成果物 (artifact: doc / コード / テスト)
  ⊃ PLAN (L4 工程の中の実装単位、L4 以外には存在しない)
```

V2 企画書 [`docs/v2/CONCEPT.md` §5 line 300-316](../CONCEPT.md) の「工程転換 (V-model スプリント化)」が正本。本ディレクトリ (`docs/v2/process/`) は各工程の進め方を明文化する。

## 工程ごとの定義 (Forward HELIX)

| 工程 | 進め方 doc | 成果物 (artifact) | PLAN | テスト設計ペア凍結 |
|---|---|---|---|---|
| L1 要件定義 | [L1-requirements-process.md](L1-requirements-process.md) | `docs/v2/L1-REQUIREMENTS.md` (FR-* / BR-* / NFR-*) | なし | L8 受入テスト設計 |
| L2 全体設計 | [L2-design-process.md](L2-design-process.md) | `docs/v2/L2-MASTER.md` / `docs/v2/CONCEPT.md` / `docs/adr/ADR-*.md` | なし | L6 統合テスト設計 |
| L3 詳細設計 | [L3-detailed-design-process.md](L3-detailed-design-process.md) | `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/*.md` | なし | L4.5 結合テスト設計 + 単体テスト設計 (`docs/v2/L4-test-design/`) |
| L4 実装 | [L4-implementation-process.md](L4-implementation-process.md) | コード (`cli/lib/*` / `cli/helix-*`) + テスト (`cli/lib/tests/test_*`) | `docs/plans/PLAN-*.md` (L3 設計 doc の subordinate) | テスト実行 (artifact ④) と pair 実行 |
| L5 Visual Refinement | (UI/fullstack 案件のみ、本 V2 で詳細化候補) | デザイン assets | なし | — |
| L6 統合検証 | (本 V2 で詳細化候補) | E2E test result | なし | L2 設計とペア検証 |
| L7 デプロイ | (本 V2 で詳細化候補) | release artifact | なし | — |
| L8 受入 | (本 V2 で詳細化候補) | 受入結果 | なし | L1 要件とペア検証 |
| L9-L11 Run | (本 V2 で詳細化候補) | 運用 KPI / postmortem | なし | — |

## PLAN の位置づけ (重要)

- PLAN は **L4 実装工程の中の実装単位**。L1/L2/L3 では PLAN を起点にしない
- PLAN frontmatter は `parent_design: docs/v2/L3-detailed-design/<area>/<feature>.md` (または該当 L2 doc / ADR snapshot) を必須記載
- PLAN.md は **Sprint .1〜.5 の実装計画** のみを記述、背景・要件・設計は parent doc を参照
- PLAN.md に背景 / 設計方針 / ADR-* 起票 を埋め込むのは V-model 違反 (PLAN-156/PLAN-224 が該当、retrofit 対象)

## L4 実装工程の標準フロー

```
[入力] L3 詳細設計 doc (例: docs/v2/L3-detailed-design/D-API/workspace-manager.md)
        +
       L3 単体テスト設計 doc (例: docs/v2/L4-test-design/workspace-manager-unit-test-design.md)
   ↓
[進め方] L3 設計から PLAN を作成 (cli/templates/plan/impl/template.md を template に)
         frontmatter:
           parent_design: docs/v2/L3-detailed-design/D-API/workspace-manager.md
           kind: impl
           layer: L4
   ↓
[Sprint] .1 (Entry) → .2 (実装) → .3 (機械チェック + テスト) → .4 (レビュー) → .5 (Exit)
   ↓
[成果物] コード (cli/lib/workspace_manager.py 等)
         テストコード (cli/lib/tests/test_workspace_manager.py)
         テスト実行結果 (artifact ④)
   ↓
[ゲート] G4 = mandatory step 全 PASS + V-model 4 artifact 双方向 trace 完備
```

## Reverse モード / Scrum モードの工程

Reverse HELIX (`R0→R4→Forward→RGC`) と Scrum (`S0→S4`) も同じく工程起点。詳細は `skills/SKILL_MAP.md §Reverse / §Scrum` 参照。本 V2 process/ は Forward HELIX の L1-L11 を主体に整備する。

## 既存資産との関係

- `helix/HELIX_CORE.md` §タスク受領: 本 process doc を実行するための CLI/skill コマンドを定義
- `skills/SKILL_MAP.md`: 各工程で読まれる skill 一覧
- `cli/templates/plan/*/template.md`: L4 工程内で PLAN を起こす template (本 process と整合)
- `helix/HELIX_CORE.md §設計⇔テスト対応`: V-model 4 artifact 双方向 trace (本 process が前提)

## 改革対象 (本 commit で着手)

| 領域 | 旧 (V1 / 改革前) | 新 (本 V2 process) |
|---|---|---|
| 起点 | PLAN-NNN が独立 doc として起票され、設計を内包 | 工程が起点、PLAN は L4 工程の subordinate |
| 設計の所在 | PLAN.md 内に背景 + 設計 + 実装計画 + テスト全部詰め込み | `docs/v2/L1〜L3` doc 群が正本、PLAN.md は実装計画のみ |
| 大局判断 | PLAN から後追いで ADR 起票 | L2 全体設計工程で大局判断 → ADR snapshot を L2 doc 内 or 別 file |
| V-model trace | 後付け | 設計とテスト設計を **同一スプリントでペア凍結** (CONCEPT.md §5 line 304-309) |
| 命名 | `PLAN-NNN-<slug>.md` 連番 | (検討中) 工程 + 設計対象 + slug 構造化 |
