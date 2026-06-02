---
plan_id: recovery-2026-06-03-whole-coverage-rescope
title: "Recovery: Phase1 早すぎる完遂宣言 + 全設計カバレッジ認識ズレ + プラン漏れの収束"
kind: recovery
layer: recovery
drive: be
status: completed
created: 2026-06-03
owner: PM
parent_process: HELIX-workflows/helix-process/recovery-workflow.md
forward_return: "V2 実装計画 roadmap (process-2026-06-03) の whole-design coverage 完遂。再開ポイント = 全設計書 L0-L6 の coverage 検証 + 欠落 doc 作成 + detector whole-coverage 化"
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/v2/L1-requirements/helix-workflows-verification-strategy.md
  - HELIX-workflows/helix-process/recovery-workflow.md
---

# Recovery: 全設計カバレッジ認識ズレの収束

## 1. 逸脱起点（recovery-workflow step3 = どこから逸脱したか）
- **逸脱起点 = 私(PM/Opus)が「Phase1 完遂」を宣言した時点**。設計カバレッジの範囲を **L0-L3 と誤認**し、**whole-design coverage(L0-L6 + 全テストペア)を検証せず**完遂と主張した。
- さらに **PLAN を検索せず**「L6/L7/L8 doc が無い → missing」と早合点しかけた（実際は PLAN は存在、doc が未作成）。ユーザー指摘「検索は絶対・プラン漏れしてる」が的中。
- 症状の層(Phase1=L0-L3)でなく、**逸脱起点は「完遂判定基準に whole-coverage 検証を含めなかった」プロセス**（[[feedback_recovery_locate_deviation_before_plan]]: 再開ポイントは逸脱起点の層）。

## 2. 認識ズレ（収束対象）
ユーザー確定: **設計書類のカバー範囲は全体(L0-L6)。L4 が holey な状態で進むのは無理**。私の「L4↔L9 を Phase2 へ先送りして Phase1 完遂」は逃げ。

## 3. 現状（網羅検索 2026-06-03、絶対検索の結果）
| L | docs/v2 設計/テスト doc | PLAN(status) | 判定 |
|---|---|---|---|
| L0 企画 | ✓ 1 | finalized | OK |
| L1 要求 | ✓ 5 | 5 finalized | OK |
| L3 要件 | ✓ 4 | 4 finalized | OK |
| L4 基本設計 | ✓ 4 | 4 finalized | OK |
| **L5 詳細設計** | 4 doc(全 draft, **pairs_test_design 未宣言**) | 4 PLAN 未 finalize | ⚠️ unpaired |
| **L6 機能設計** | ❌ doc 無し | 3 PLAN 未 finalize | 🔴 doc 欠落 |
| **L7 単体テスト設計** | ❌ doc 無し | impl 系 PLAN 多数 | 🔴 設計 doc 欠落 |
| **L8 結合テスト設計** | ❌ doc 無し | 2 PLAN finalized | 🔴 doc 欠落 |
| L9/L12/L14 | ✓ 各1 | — | OK(L9 は本日片肺解消 100%) |

→ 設計カバレッジ完遂は **L0-L4 + L9/L12/L14 のみ**。L5 unpaired / L6・L7・L8 doc 欠落。

## 4. 本 session で既に収束した分
- **L4↔L9 片肺解消**: L9 に NFR 6群 per-ID trace + IF-05 永続化観点を追加、detector で **coverage 100% / uncovered=0** を機械確認、再凍結。

## 5. 再開ポイント（forward_return への path）
1. **detector を whole-coverage 化**(feature): L5/L6 設計 ID 抽出 + verification_layers 契約尊重 + missing-pair 検出。これで全ペアが measurable に。
2. **L5↔L8 pairing**: L5 4 doc に pairs_test_design 宣言 + **L8 結合テスト設計 doc 作成**(L8 PLAN 正本化)。
3. **L6↔L7**: **L6 機能設計 doc + L7 単体テスト設計 doc 作成**(L6/L7 PLAN 正本化、単体は DbC 粒度)。
4. **L1↔L14 verification_layers 契約**(FR→L3↔L12 routing を機械明示、detector 誤検出解消)。
5. **GitHub 早期実装**(ユーザー優先指示): ISSUE_TEMPLATE(駆動→Issue) + concurrency + ADR-029 reconcile。
6. **handover で中断継続性**を確保(要件は中断/引き継ぎ同様)。

## 6. 完遂基準（再発防止 = whole-coverage を判定に含める）
- 全設計層(L0-L6)が doc 実体を持ち、対テスト設計と pairs_test_design 双方向宣言で閉じる。
- detector(trace_symmetry)が **全ペア(L1↔L14/L3↔L12/L4↔L9/L5↔L8/L6↔L7)で coverage を出せ、uncovered が説明可能(0 or verification_layers/excluded 契約付き)**。
- 「Phase 完遂」判定に whole-coverage detector run を必須化（[[verification-strategy]] §4 + 反芻機構）。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-03 | Recovery 起票。逸脱起点=早すぎる完遂宣言+whole-coverage 未検証+プラン漏れ未検索。網羅検索で現状確定。L4↔L9 は本日 100% 収束済。 | PM (Opus) |
| 2026-06-03 | **収束完了 (forward_return 達成)**。再開ポイント全消化: ①detector whole-coverage 化 (L5/L6 ID 抽出+verification_layers+missing-pair、commit 91c9a16) ②L5↔L8 pairing (L5 per-item ID + L8 結合テスト設計 doc Reverse、2c0fbbe) ③L6↔L7 (L6 機能設計+L7 単体テスト設計 DbC、3e33b82) ④L1↔L14 verification_layers 契約 (over-report 解消、3ecdddc) ⑤GitHub 早期実装 (99b9ebe)。**全5 V-model pair が detector green** (coverage100%/uncovered0/missing-pair0/wrong_layer_pair0)。L5↔L8/L6↔L7 を tl-advisor check (P1修正) 後 V-model pair-freeze (96fb028)。**§6 完遂基準を満たす** (L0-L6 全設計層が doc+対テスト双方向、detector 全ペア measurable)。**残 finding**: L4↔L9 orphan18 (全 ST-* system scenario、forward coverage100% だが reverse-trace 弱、次 L9 re-freeze で ST-*→L4 verifies backlink 推奨=tl-advisor)。 | PM (Opus) |
