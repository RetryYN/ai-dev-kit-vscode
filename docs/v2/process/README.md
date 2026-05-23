---
doc_id: process-overview
title: "HELIX V2 工程定義 — L0 企画 → L14 運用検証 (15 工程)"
status: maintained
created: 2026-05-24
owner: PM
---

# HELIX V2 工程定義 — 15 工程構造

## 基本構造

工程 (process) が起点。PLAN は **L7 実装スプリント工程の subordinate** であり、L1〜L6 設計工程・L8 以降の検証/運用工程では PLAN を起票しない。

```
工程 (L0〜L14)
  ⊃ 進め方 (process)
  ⊃ 入力 (前段工程の成果物)
  ⊃ 成果物 (doc / コード / テスト)
  ⊃ PLAN (L7 実装スプリントの中の管理単位のみ)
```

## 15 工程一覧 + V-model ペア対応

```
L0 企画書
  ↓
L1 要求定義 / 運用テスト設計 ─────────────────────────────┐
  ↓                                                       │
L2 画面設計・フロント UI / ワイヤーモック ───────────┐     │
  ↓                                                  │     │
L3 要件定義 / 受け入れテスト設計 ─────────────┐      │     │
  ↓                                            │      │     │
L4 基本設計 / 総合テスト設計 ──────────┐       │      │     │
  ↓                                    │       │      │     │
L5 詳細設計 / 結合テスト設計 ──┐       │       │      │     │
  ↓                            │       │       │      │     │
L6 機能設計 / 単体テスト設計   │       │       │      │     │
  ↓                            │       │       │      │     │
L7 テスト実装 → 本体実装 → 3 点レビュー → テスト追加 → テスト実施 → 修正/完了
  ↓ (機能設計と単体テスト設計を pair として L7 内で実装+検証)
  ↑                            │       │       │      │     │
L8 結合テスト / 依存関係解消 ←┘       │       │      │     │
  ↑                                    │       │      │     │
L9 総合テスト / 依存関係解消 ←────────┘       │      │     │
  ↑                                            │      │     │
L10 フロント UX・ビジネスデザイン磨き上げ ←────┘      │     │
  ↑                                                   │     │
L11 総合レビュー / ユーザー検証 / 要件巻き取り        │     │
  ↑                                                   │     │
L12 デプロイ / 受入テスト / 環境差異巻き取り ←───────┘     │
  ↑                                                         │
L13 デプロイ後検証 / 実環境運用                            │
  ↑                                                         │
L14 運用検証 / 機能改善 ←─────────────────────────────────┘
```

### V-model ペア凍結表

| 設計工程 (V-model 左側) | ペア検証工程 (V-model 右側) | テスト設計成果物の配置 |
|---|---|---|
| **L1** 要求定義 | **L14** 運用検証 / 機能改善 | `docs/v2/L14-test-design/<feature>-operational-test-design.md` |
| **L2** 画面設計・ワイヤーモック | **L10** フロント UX 磨き上げ | (UI 案件のみ、磨き上げペア) |
| **L3** 要件定義 | **L12** デプロイ / 受入テスト | `docs/v2/L12-test-design/<feature>-acceptance-test-design.md` |
| **L4** 基本設計 | **L9** 総合テスト | `docs/v2/L9-test-design/<feature>-system-test-design.md` |
| **L5** 詳細設計 | **L8** 結合テスト | `docs/v2/L8-test-design/<feature>-integration-test-design.md` |
| **L6** 機能設計 | **L7** 単体テスト (L7 実装スプリント内で実装+検証) | `docs/v2/L7-test-design/<feature>-unit-test-design.md` |

各設計工程は **テスト設計をペア凍結** する (V-model 左右同時進行)。テスト「実装」は L7、テスト「実施」は L8 以降の対応工程。

## PLAN の位置づけ (重要)

| 工程 | PLAN 起票 | 成果物 |
|---|---|---|
| L0-L6 (設計工程) | **起票しない** | doc + ADR (L4) / 工程表 (L6 末) |
| **L7** 実装スプリント | **起票する** (本工程の subordinate) | コード + テスト + 3 点レビュー記録 |
| L8-L14 (検証/運用工程) | **起票しない** | テスト結果 / レビュー記録 / 運用 KPI / postmortem |

PLAN frontmatter 必須 field (impl template):
```yaml
process_layer: L7        # 実装スプリント工程の subordinate
parent_design: docs/v2/L6-function-design/<area>/<feature>.md  # L6 機能設計 doc への path
pairs_test_design:
  - docs/v2/L7-test-design/<feature>-unit-test-design.md       # 単体 (L6 とペア凍結済)
  - docs/v2/L8-test-design/<feature>-integration-test-design.md # 結合 (L5 とペア凍結済、L8 で実施)
  - docs/v2/L9-test-design/<feature>-system-test-design.md      # 総合 (L4 とペア凍結済、L9 で実施)
```

PLAN.md 本文は **Sprint .1〜.5 の実装計画のみ**。背景 / 要件 / 設計は parent doc 群を参照、PLAN.md に書かない。

## 工程ごとの process doc

| 工程 | doc | ペア |
|---|---|---|
| L0 企画書 | [L00-planning.md](L00-planning.md) | — |
| L1 要求定義 + 運用テスト設計 | [L01-requirements-and-operational-test-design.md](L01-requirements-and-operational-test-design.md) | L14 |
| L2 画面設計 + ワイヤーモック | [L02-screen-design-and-wireframe.md](L02-screen-design-and-wireframe.md) | L10 |
| L3 要件定義 + 受入テスト設計 | [L03-requirements-definition-and-acceptance-test-design.md](L03-requirements-definition-and-acceptance-test-design.md) | L12 |
| L4 基本設計 + 総合テスト設計 | [L04-architecture-design-and-system-test-design.md](L04-architecture-design-and-system-test-design.md) | L9 |
| L5 詳細設計 + 結合テスト設計 | [L05-detailed-design-and-integration-test-design.md](L05-detailed-design-and-integration-test-design.md) | L8 |
| L6 機能設計 + 単体テスト設計 | [L06-function-design-and-unit-test-design.md](L06-function-design-and-unit-test-design.md) | L7 |
| L7 実装スプリント (テスト → 実装 → 3 点レビュー → テスト追加 → 実施 → 完了) | [L07-implementation-sprint.md](L07-implementation-sprint.md) | L6 |
| L8 結合テスト + 依存関係解消 | [L08-integration-testing.md](L08-integration-testing.md) | L5 |
| L9 総合テスト + 依存関係解消 | [L09-system-testing.md](L09-system-testing.md) | L4 |
| L10 フロント UX 磨き上げ | [L10-frontend-ux-polish.md](L10-frontend-ux-polish.md) | L2 |
| L11 総合レビュー + ユーザー検証 + 要件巻き取り | [L11-review-and-user-validation.md](L11-review-and-user-validation.md) | — |
| L12 デプロイ + 受入テスト + 環境差異 | [L12-deployment-and-acceptance-test.md](L12-deployment-and-acceptance-test.md) | L3 |
| L13 デプロイ後検証 + 実環境運用 | [L13-post-deployment-verification.md](L13-post-deployment-verification.md) | — |
| L14 運用検証 + 機能改善 | [L14-operations-and-improvement.md](L14-operations-and-improvement.md) | L1 |

## 既存資産との関係 (移行)

### 旧 L1-L11 から新 L0-L14 への対応

| 旧 (L1-L11) | 新 (L0-L14) | 備考 |
|---|---|---|
| L1 要件定義 | **L1** 要求定義 + **L3** 要件定義 に分割 | 業務要求 ↔ システム要件で 2 段階 |
| L2 全体設計 | **L4** 基本設計 | (L2 は画面設計に再割当) |
| L3 詳細設計 | **L5** 詳細設計 + **L6** 機能設計 に分割 | 詳細 ↔ 機能で 2 段階 |
| L4 実装 | **L7** 実装スプリント | 3 点レビュー (設計⇔テスト⇔実装) 構造を追加 |
| L5 Visual Refinement | **L2** 画面設計 (前段) + **L10** UX 磨き (後段) | 画面設計を上流に、磨きを下流に分割 |
| L6 統合検証 | **L8** 結合テスト + **L9** 総合テスト + **L11** レビュー に分割 | 検証粒度で 3 段階 |
| L7 デプロイ | **L12** デプロイ | — |
| L8 受入 | **L12** 受入テスト | (L12 でデプロイと統合) |
| L9 デプロイ検証 | **L13** デプロイ後検証 | — |
| L10 観測 | **L13/L14** に統合 | — |
| L11 運用学習 | **L14** 運用検証 + 機能改善 | — |

### 既存設計 doc の再配置 carry

- `docs/v2/L1-REQUIREMENTS.md` → 新 L1 要求 + 新 L3 要件 に分割再構成 (carry)
- `docs/v2/L2-MASTER.md` → 新 L4 基本設計 に再配置 (carry)
- `docs/v2/L3-detailed-design/{D-API,D-DB,D-CONTRACT}/` → 新 L5 詳細 + 新 L6 機能 に分割再配置 (carry)
- `docs/v2/L4-test-design/` → 新 L7/L8/L9/L12/L14 各テスト設計 doc 群に分散再配置 (carry)
- 既存 PLAN-001〜PLAN-225 → `process_layer: L7` で統一 retrofit + `parent_design:` 後追い補完 (carry)

### 既存 skills/SKILL_MAP.md との同期 carry

- `SKILL_MAP.md §オーケストレーションフロー` の L1-L11 表記を L0-L14 に置換 (carry)
- gate-policy.md の G1〜G11 を G0-G14 に再採番 (carry)
- HELIX_CORE.md の工程参照 update (carry)

## 改革のポイント

1. **設計とテスト設計をペア凍結** (V-model 左右同時進行、各設計工程の成果物にペアとなるテスト設計が必須)
2. **L7 実装スプリント内で 3 点レビュー** (設計 ⇔ テスト ⇔ 実装の三位一体)
3. **PLAN は L7 のみで起票** (L1-L6 設計工程・L8-L14 検証運用工程では PLAN なし、doc + テスト設計が成果物)
4. **plan_validator が `process_layer != L7` で起票を blocking** (V-model 違反を機械防止、後続 commit)
5. **dual-design** (各工程は本体設計 + テスト設計を同時に成果物として持つ、後追いペア凍結を排除)
