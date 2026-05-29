---
plan_id: L6-helix-workflows-クラス設計plan
title: "L6-helix-workflows-クラス設計plan: HELIX-workflows V2 Class / Module / Command 設計"
kind: design
layer: L6
drive: be
status: finalized
created: 2026-05-29
owner: PM
process_layer: L6
parent_process: HELIX-workflows/helix-process/L6-functional-design.md
pairs_test_design:
  - docs/v2/L7-test-design/helix-workflows-unit-test-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G6 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー"
generates:
  - artifact_path: docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md
    artifact_type: design_doc
dependencies:
  parent: L6-helix-workflows-関数仕様plan
  requires:
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
    - L6-helix-workflows-関数仕様plan
  blocks:
    - L6-helix-workflows-エッジケースplan
related_docs:
  - HELIX-workflows/helix-process/L6-functional-design.md
  - HELIX-workflows/helix-process/L7-implementation.md
  - docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
  - docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md
  - docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
  - docs/v2/L5-internal-design/helix-workflows-physical-data-design.md
---

## §0 PLAN concept

本 PLAN は L6 機能設計 (実装直前の最下層設計) の HELIX-workflows V2 Class / Module / Command 設計 を担う。L5 詳細設計 4 doc を入力に、L7 実装スプリントへ直接落とせる粒度の機能設計を凍結する。pair となる L7 単体テスト設計と双方向 trace で freeze する。

### §0.1 担当 scope
- Python lib: class / dataclass / module API 設計 (責務・属性・公開メソッド)
- bash CLI: サブコマンド仕様 (引数・exit code・stdout/stderr・side effect)
- config/schema: YAML/JSON schema・validation・default・互換性
- hook/agent: event contract・入出力 envelope・失敗時動作
(TL 助言: 「クラス設計」を Class/Module/Command Design として広く読む)

### §0.2 完遂方針 (24h dogfood、TL fallback 準拠)
- **F1-F5 (中核機能) は完全本体化** (実装入口契約 = command/function/schema/error を確定)
- **F6-F10 (拡張 governance 機能) は planned contract** (signature/責務レベル、実装は L7 carry)
- planned/partial/implemented を明示分離し、L7 carry を carry 理由列に残す

## §1 工程表

| Step | 作業内容 | 進捗 |
|---|---|---|
| 1 | L5 module-decomposition §3-§9 + 関数仕様 doc を入力に class/module/command inventory | ✅ done |
| 2 | F1-F5 の Python class/dataclass + bash subcommand + config schema + hook contract 本体化 | ✅ done |
| 3 | F6-F10 planned contract | ✅ done |
| 4 | L7 単体テスト設計 pointer 配線 | ✅ done |
| 5 | 二重監査 | ✅ done |
| 6 | G6 → frozen | ✅ done |

## §2 実装計画

- 生成物: `docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md`
- 入力: L5 4 doc (module-decomposition §2.1 matrix / interface CLI 36件 / internal アルゴリズム / physical schema)
- pair: `docs/v2/L7-test-design/helix-workflows-unit-test-design.md` (L6↔L7-test 双方向 trace)
- 各項目に implementation_status (implemented/partial/planned) + L7 carry 理由を付す

## §3 DoD

1. F1-F5 の class/module/command/config/hook 設計確定
2. F6-F10 planned
3. L6↔L7-test 双方向 trace
4. implementation_status 完備
5. tl-advisor PASS + pmo OK
6. plan_lint PASS

## §4 関連

- 親: L6-helix-workflows-関数仕様plan
- L5 入力: module-decomposition / interface-detailed / internal-processing / physical-data
- pair: L7 単体テスト設計 (docs/v2/L7-test-design/helix-workflows-unit-test-design.md)

## L6/L7 freeze evidence (2026-05-29)

- 設計 doc 本体化完遂、frontmatter status: frozen (L6 機能設計 3 doc) / L7 単体テスト設計 frozen
- pair freeze: L6↔L7-test 双方向 trace (L6 各 `→ UT-Fx-NNN` 83/83 解決、L7 98 case 定義)
- 監査: Opus 機械検証 (placeholder 0 / dangling trace 0 / F1-F5 signature 完備 / impl_status 正確) + tl-advisor adversarial (G6 changes_required → P1[§8集計 98更新/stale未作成解消] + P2[status frozen] 全反映 → passed)
- F1-F5 完全本体化 (実装入口契約 = command/function/schema/error) / F6-F10 planned/partial contract
- carry (L7 Sprint Step 2): fixture 実体 / テストコード / coverage gate 接続 / planned module (F6-F10 new) の implemented 遷移
