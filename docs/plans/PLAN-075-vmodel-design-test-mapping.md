---
plan_id: PLAN-075
title: "PLAN-075: V-model 設計⇔テスト対応 framework 強化 (5 Phase)"
status: draft
size: L
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-074 (HTTP endpoint 層、V-model 違反の起点)
  - PLAN-072 (L4.5 結合、carry check 対象)
trigger: |
  ユーザー指摘 2026-05-17: 「基本設計は総合テスト設計も含むんだよ？
  詳細設計は結合テスト設計も含むんだよん？機能設計は単体テスト設計も含むんだよ？」

  PLAN-074 で 単体テスト設計を独立ドキュメント化したのが V-model 違反。
  HELIX framework 全体で「設計⇔テストの対応関係を 1 文書に束ねる」原則を強制化する。
acceptance:
  - HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に V-model 設計⇔テスト対応原則を明文化
  - L2/L3 テンプレートに「設計 + テスト設計 2 親」を強制
  - PLAN-074 を retrofit (PLAN-074-unit-test-design.md 削除、D-API EXT に統合)
  - 他既存 PLAN の V-model 整合性チェック + 必要に応じて retrofit
  - helix doctor / G2-G4 ゲートに自動 lint 追加
---

# PLAN-075: V-model 設計⇔テスト対応 framework 強化 (5 Phase)

## §1 背景

### V-model 設計⇔テスト対応の基本原則

ソフトウェア工学の V-model では、設計フェーズの各層と検証 (テスト) フェーズの各層が 1:1 対応する。設計とテストは **同じ文書に書く** のが原則:

```
         要件定義 ←──────→ 受入テスト
              \           /
              基本設計 ←─→ 総合テスト (システムテスト)
                  \       /
                  詳細設計 ←→ 結合テスト
                      \   /
                      機能設計 ←→ 単体テスト

  ↑                                       ↑
  (左下がり: 設計、上向き)                (右上がり: テスト、下向き)
```

各層の本質:
- **基本設計** (アーキテクチャ、ADR): どんな **総合テスト** で検証するかが決まる
- **詳細設計** (D-API / D-DB / D-CONTRACT): どんな **結合テスト** で検証するかが決まる
- **機能設計** (各関数 / 各 endpoint の input/output schema、境界値): どんな **単体テスト** で検証するかが決まる

設計とテストを分離した文書にすると、設計変更時のテスト追従漏れ / テスト変更時の設計逸脱検出漏れが発生する。これが V-model 違反。

### HELIX 現状の整合性

| HELIX 層 | 設計成果物 | テスト設計の現状 |
|---|---|---|
| L1 要件定義 | requirements / acceptance | 受入テスト基準 (L8 受入) | △ (受入条件はあるが、テストとしての形式が薄い) |
| L2 全体設計 | CONCEPT / ADR / visual-design | **総合テスト設計が欠落** | ❌ |
| L3 詳細設計 | D-API / D-DB / D-CONTRACT | **結合テスト設計が欠落** (test 実装はある) | ❌ |
| L3-L4 機能設計 | endpoint の request/response schema | **単体テスト設計が欠落** (test 実装も欠落 PLAN-074) | ❌ |
| L4 実装 | コード | (テスト実装フェーズ、設計層ではない) | - |

→ HELIX framework 全体で設計⇔テスト対応が崩れている。本 PLAN で是正する。

## §2 5 Phase 構成

### Phase 1 — V-model 原則を HELIX core に明文化 (size: M)

- `helix/HELIX_CORE.md` に「§設計⇔テスト対応 (V-model)」セクション追加
- `skills/SKILL_MAP.md` の各 L レイヤ説明に「テスト設計を含む」明示
- `CLAUDE.md` (project + global) に V-model 原則の運用ルール追加
- 受入: 3 文書全件に V-model 原則が明文化されている

### Phase 2 — L2/L3 テンプレートと skill 責務再整理 (size: L)

- `cli/templates/` 配下の PLAN テンプレートに「設計 + テスト設計 2 親」セクション強制
- `skills/workflow/design-doc/SKILL.md` を update (総合テスト設計を含む)
- `skills/workflow/api-contract/SKILL.md` を update (結合テスト設計を含む)
- `skills/common/testing/SKILL.md` を update (機能設計連動 / 単体テスト設計担当)
- `skills/workflow/verification/SKILL.md` を update (V-model 突合検証の責務)
- 既存 reference 文書 (gate-policy.md / workflow-core.md) の関連箇所 update
- 受入: 全 skill が V-model 原則と整合、テンプレートで強制化される

### Phase 3 — PLAN-074 retrofit (size: M)

- `docs/v2/L4-test-design/PLAN-074-unit-test-design.md` 削除
- `docs/v2/L4-test-design/` dir 削除 (空になるなら)
- D-API EXT §3.1-3.5 各 endpoint に以下 2 セクション追加:
  - **機能設計 + 単体テストケース** (input/output bound、境界値、例外パス)
  - **詳細設計 + 結合テストケース** (現 integration test 27 cases の設計上の親)
- PLAN-074 §12 (新規) に **総合テスト設計** 追加 (E2E 25 シナリオの設計上の親)
- task-plan.yaml に WBS-074-L4-008 (単体テスト 63 cases 実装) を追加
- 受入: PLAN-074 で V-model 4 層 (要件/基本/詳細/機能) ↔ テスト 4 層 (受入/総合/結合/単体) が全件対応

### Phase 4 — 他既存 PLAN の V-model 整合性チェック + retrofit (size: M-L)

- PLAN-072 (L4.5 結合): 設計⇔テスト対応 audit、retrofit 要否判定
- PLAN-071 (capability detailing): 同上
- PLAN-068 (V-model 強化、皮肉にも違反、completed): 文書上 retrofit
- PLAN-067 (helix-automation-layer): 同上
- 受入: 既存 PLAN 全件で V-model 整合性 audit 完了、必要 retrofit 完遂

### Phase 5 — helix doctor / G2-G4 自動 lint 追加 (size: M)

- `helix doctor` に「V-model 設計⇔テスト対応 check」追加:
  - L2/L3 設計文書に「総合テスト設計」「結合テスト設計」セクション有無
  - 機能設計 (D-API §X) に「単体テスト設計」セクション有無
  - 各 test ファイル docstring に設計参照 (§X) があるか
- G2 / G3 / G4 ゲートで上記 check を強制化 (P0 stop)
- 受入: lint が fail-close で動作、過去 PLAN の違反を機械的に検出

## §3 Sprint 構成

本 PLAN 自体が複数 Phase / 複数セッションにまたがるため、Phase 単位で Sprint を切る。

### Sprint .1 (Phase 1) — HELIX core 文書化

| Sub-sprint | 内容 | role | WBS |
|---|---|---|---|
| .1.1a | V-model 原則の文書化案 (本 PLAN §1-§2) | PM | WBS-075-P1-001 |
| .1.1b | HELIX_CORE.md に §設計⇔テスト対応 追加 | PM (small docs edit) | WBS-075-P1-002 |
| .1.2 | SKILL_MAP.md 各 L レイヤ説明 update | PM | WBS-075-P1-003 |
| .1.3 | CLAUDE.md (project + global) 運用ルール追加 | PM | WBS-075-P1-004 |
| .1.4 | Phase 1 commit + push | PM | WBS-075-P1-005 |

(L 規模 docs 起草は通常 Codex docs 委譲だが、core 文書の文書改定は PM 直接編集が許容範囲)

### Sprint .2 (Phase 2) — テンプレート / skill 整理 (別セッション)

詳細は Phase 1 完了後に確定。

### Sprint .3 (Phase 3) — PLAN-074 retrofit (別セッション)

詳細は Phase 2 完了後に確定。

### Sprint .4 (Phase 4) — 他 PLAN retrofit (別セッション)

詳細は Phase 3 完了後に確定。

### Sprint .5 (Phase 5) — lint / 自動化 (別セッション)

詳細は Phase 4 完了後に確定。

## §4 受入条件

- HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に V-model 原則が明文化されている (Phase 1)
- L2/L3 テンプレートに「設計 + テスト設計 2 親」が強制されている (Phase 2)
- PLAN-074 が V-model 原則準拠で retrofit 済 (Phase 3)
- 既存 PLAN の V-model 整合性 audit 完了 (Phase 4)
- helix doctor / G2-G4 で V-model lint が fail-close で動作 (Phase 5)

## §5 リスク

| ID | 内容 | 影響 | 対策 |
|---|---|---|---|
| R-01 | Phase 2 (テンプレート整理) が想定外に広範化 | 工数超過 | Phase 単位で session を分割、必要に応じて scope 削減 |
| R-02 | 既存 skill 責務変更で他 PLAN に影響 | 回帰 | Phase 2 後に helix test 全回帰、PLAN-074 retrofit (Phase 3) で動作確認 |
| R-03 | 自動 lint (Phase 5) が過去 PLAN で大量 fail | 着地遅延 | Phase 4 で retrofit を先行、lint は最後に有効化 |

## §6 依存関係

- 前提: PLAN-074 が G4 ready 状態 (commit 13de2af) であること ✅
- Phase 3 着手前: PLAN-074-unit-test-design.md が残存 (Phase 1 完了後の Phase 3 で削除)
- Phase 4 着手前: Phase 2 テンプレート / skill update が完了

## §7 Next Action

1. **本セッション**: Phase 1 (HELIX core 文書化) 完遂
   - HELIX_CORE.md §設計⇔テスト対応 (V-model) 追加
   - SKILL_MAP.md の L レイヤ説明 update
   - CLAUDE.md (project + global) 運用ルール追加
   - commit + push
2. **次セッション以降**: Phase 2-5 を段階的に実施
