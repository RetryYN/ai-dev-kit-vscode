---
doc_id: process-L07
title: "L7 実装スプリント — テスト実装 → 本体実装 → 3 点レビュー → テスト追加 → 実施 → 完了"
status: maintained
created: 2026-05-24
owner: PM
process_layer: L7
pairs_with: L6
canonical_source: HELIX-workflows/helix-process/L7-implementation.md
---

# L7 実装スプリント工程

## 入力 (必須)

- L6 機能設計 doc (`docs/v2/L6-function-design/<feature>/<function>.md`)
- L7 単体テスト設計 doc (`docs/v2/L7-test-design/<feature>-unit-test-design.md`、L6 でペア凍結済)
- 工程表 / WBS
- skill: `common/coding` / `common/testing` / `common/code-review` / `agent-skills/test-driven-development` / `agent-skills/incremental-implementation` / `tools/ai-coding`

## 進め方 (本工程の核 = 7 ステップ)

### Step 1: PLAN 起票 (本工程の subordinate)
- L6 機能設計 doc から L7 PLAN を起票
- template: `cli/templates/plan/impl/template.md`
- frontmatter 必須:
  ```yaml
  process_layer: L7
  parent_design: docs/v2/L6-function-design/<feature>/<function>.md
  pairs_test_design:
    - docs/v2/L7-test-design/<feature>-unit-test-design.md
    - docs/v2/L8-test-design/<feature>-integration-test-design.md   # L8 で実施されるテスト設計を参照
    - docs/v2/L9-test-design/<feature>-system-test-design.md         # L9 で実施されるテスト設計を参照
  ```
- PLAN.md 本文は **Sprint .1〜.5 の実装計画のみ**

### Step 2: テスト実装 (TDD、artifact ④ 着手)
- L7 単体テスト設計 (artifact ③) を読んで **失敗するテスト** を先に書く
- skill: `agent-skills/test-driven-development`

### Step 3: 本体実装 (artifact ② 着手)
- テストが通る最小実装
- 機能設計の signature を守る

### Step 4: 3 点レビュー (設計 ⇔ テスト ⇔ 実装)
- **設計 (artifact ①)** と **テスト (artifact ③④)** と **実装 (artifact ②)** の三位一体を確認
- セルフレビュー (Opus)
- pmo-sonnet review (G7 時)
- on-demand: tl-advisor (技術選択で迷ったとき)
- 3 点に矛盾あれば該当工程 (L4/L5/L6 設計 or 単体テスト設計) に差し戻し

### Step 5: テストパターン追加
- 3 点レビューで「設計に書いてあるが test design に不在」を発見 → test design に追記 + テストコード追加
- 「実装したが設計にない」を発見 → 設計に追記 or 実装削除

### Step 6: テスト実施
- 該当範囲のテスト + 全回帰
- `helix test` で機械実行
- pytest / bats raw output を artifact ④ として保存

### Step 7: 修正 / 実装完了
- mandatory check (py_compile / bash -n / lint / 全回帰) PASS
- DoD 確認 + commit
- G7 ゲート通過判定

## 成果物

- **コード (artifact ②)**: `cli/lib/<module>.py` / `cli/helix-<command>` 等
- **テストコード (artifact ④)**: `cli/lib/tests/test_<module>.py`
- **テスト実行結果**: pytest / bats raw output
- **PLAN doc (管理用)**: `docs/plans/PLAN-NNN-<slug>.md` (本工程の管理単位)
- **3 点レビュー記録**: PLAN.md §3 点レビューに記録

## V-model 4 artifact 完備

```
① 設計 (L4/L5/L6 doc)        ←対応→  ③ テスト設計 (L7/L8/L9 test design)
       ↓                                    ↓
② 実装コード (本工程出力)     ←対応→  ④ テストコード (本工程出力)
```

## ペア凍結相手

L6 機能設計 (L6 で凍結された単体テスト設計を L7 で実装+検証)

## ゲート

- **G7 実装凍結ゲート**: TL + PM 判定、mandatory step 全 PASS + V-model 4 artifact 双方向 trace 完備 + セキュリティ②

## 関連 skill

- `common/coding` / `common/testing` / `common/refactoring`
- `common/code-review` (Google reviewer guide 統合)
- `agent-skills/test-driven-development` / `agent-skills/incremental-implementation`
- `agent-skills/code-review-and-quality`
- `tools/ai-coding` (Codex / Claude harness)
- `workflow/quality-lv5` (G7 で読まれる)

## アンチパターン

- ❌ `parent_design:` 不在で PLAN 起票 (V-model 違反、本日 PLAN-156/224 で発覚)
- ❌ PLAN.md 内に背景 / 設計を書く (L4/L5/L6 doc を参照すれば不要)
- ❌ テスト実装より本体実装を先 (TDD 違反、artifact ④ → ② の順序を守る)
- ❌ 3 点レビューを skip (設計 ⇔ テスト ⇔ 実装の整合性が崩れる)
- ❌ commit を skip して次 Sprint へ (DoD trace が失われる)
- ❌ L8/L9 テスト設計 (artifact ③) を本工程で起票 (本来 L4/L5 でペア凍結済のはず、後追いは V-model 違反)

---

## 正本 (HELIX-workflows) 抽出 — 2026-05-24 V2 完全移行

> 正本: [L7-implementation.md](../../../HELIX-workflows/helix-process/L7-implementation.md)
> 本 doc は HELIX-workflows に同期。差分は HELIX-workflows を優先。

### 工程の位置づけ (HELIX-workflows 正本)

| 項目 | 内容 |
|---|---|
| 区分 | V字 谷（実装工程） |
| 入力 | L6 機能設計 |
| 出力 | L8 結合テスト への入力 |
| 工程表 | 実装する機能の順番を定義 |
| PLAN | 機能の中身の実装手順書として起票 |

### この工程の PLAN (HELIX-workflows 正本)

L7 の工程表が実装機能の順番を定義し、その配下の PLAN が各機能の中身の実装手順書になる。

### `L7-<機能名>plan`
- 対象機能
- 実装手順（下記フロー）
- 進捗状態

> **PLAN が内蔵するもの** (HELIX-workflows 共通):
> - **工程表**: そのドキュメントを完成させる手順 (例: 参考調査 Web 検索 → 既存資料整理 → ドラフト → TL レビュー → 確定) と各手順の進捗
> - **実装計画**: 記載項目をどう埋めるかの計画

