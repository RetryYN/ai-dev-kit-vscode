---
plan_id: L7-helix-workflows-単体テストplan
title: "L7-helix-workflows-単体テストplan: HELIX-workflows V2 単体テスト設計 (L6 機能設計 3 doc pair)"
kind: design
layer: L7
drive: be
status: finalized
created: 2026-05-29
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
pairs_design:
  - docs/v2/L6-functional-design/helix-workflows-function-spec-design.md
  - docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md
  - docs/v2/L6-functional-design/helix-workflows-edge-case-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G6 evidence)"
generates:
  - artifact_path: docs/v2/L7-test-design/helix-workflows-unit-test-design.md
    artifact_type: design_doc
dependencies:
  parent: L6-helix-workflows-関数仕様plan
  requires:
    - L6-helix-workflows-関数仕様plan
    - L6-helix-workflows-クラス設計plan
    - L6-helix-workflows-エッジケースplan
related_docs:
  - HELIX-workflows/helix-process/L6-functional-design.md
  - HELIX-workflows/helix-process/L7-implementation.md
  - docs/v2/L6-functional-design/helix-workflows-function-spec-design.md
---

## §0 PLAN concept

本 PLAN は L6 機能設計 (関数仕様 / Class-Module-Command / エッジケース) の pair となる L7 単体テスト設計を担う。V-model L6↔L7 (Sprint Step 2 単体テスト実装) の左右対応を凍結する。テスト観点・ケース ID・期待結果・対象設計 ID を設計し、fixture 実体・テストコードは L7 実装スプリント carry とする。

### §0.1 担当 scope
- F1-F5 中核機能の関数 / class / command に対する単体テスト設計 (正常系 + 異常系 + 境界値)
- エッジケース doc の境界値・例外パターンを単体テストケースに展開
- F6-F10 は planned test contract

## §1 工程表

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | L6 3 doc (関数仕様 / class / edge) を入力に単体テストケース inventory | ✅ done |
| 2 | F1-F5 単体テスト設計本体化 (UT-Fx-NNN: 対象関数/入力/期待/異常系) | ✅ done |
| 3 | エッジケース由来の境界値・例外テスト展開 | ✅ done |
| 4 | F6-F10 planned test contract | ✅ done |
| 5 | L6↔L7-test 双方向 trace 配線 | ✅ done |
| 6 | tl-advisor + pmo-sonnet 二重監査 → frozen | ✅ done |

## §2 実装計画

- 生成物: `docs/v2/L7-test-design/helix-workflows-unit-test-design.md`
- 入力: L6 機能設計 3 doc
- pair: L6 機能設計 3 doc (双方向 trace)
- 各ケースに対象設計 ID (関数/class) + implementation_status + fixture 種別 (実体は L7 carry)

## §3 DoD

1. F1-F5 の単体テスト設計 (UT-Fx-NNN、正常/異常/境界) 確定
2. F6-F10 planned test contract
3. L6↔L7-test 双方向 trace
4. implementation_status 完備 (全 planned、実行は L7 Sprint Step 2 carry)
5. tl-advisor PASS + pmo-sonnet OK
6. plan_lint PASS

## §4 関連

- 親: L6-helix-workflows-関数仕様plan
- pair: L6 機能設計 3 doc

## L6/L7 freeze evidence (2026-05-29)

- 設計 doc 本体化完遂、frontmatter status: frozen (L6 機能設計 3 doc) / L7 単体テスト設計 frozen
- pair freeze: L6↔L7-test 双方向 trace (L6 各 `→ UT-Fx-NNN` 83/83 解決、L7 98 case 定義)
- 監査: Opus 機械検証 (placeholder 0 / dangling trace 0 / F1-F5 signature 完備 / impl_status 正確) + tl-advisor adversarial (G6 changes_required → P1[§8集計 98更新/stale未作成解消] + P2[status frozen] 全反映 → passed)
- F1-F5 完全本体化 (実装入口契約 = command/function/schema/error) / F6-F10 planned/partial contract
- carry (L7 Sprint Step 2): fixture 実体 / テストコード / coverage gate 接続 / planned module (F6-F10 new) の implemented 遷移
