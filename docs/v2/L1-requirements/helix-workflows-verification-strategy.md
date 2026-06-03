---
doc_id: L1-helix-workflows-verification-strategy
title: "HELIX-workflows V2 検証戦略 (Master Verification Strategy, 右腕統括)"
status: draft
created: 2026-06-03
owner: PM
process_layer: L1
doc_kind: verification-strategy
scope: cross-cutting
governs:
  - docs/v2/L14-test-design/helix-workflows-operational-test-design.md
  - docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
  - docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md
related_plans:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/plans/reverse/reverse-2026-06-03-l1-l3-trace-hardening.md
  - docs/plans/discovery/poc-2026-06-03-trace-symmetry-detector.md
---

# HELIX-workflows V2 検証戦略 (Master Verification Strategy)

> 本書は V モデル**右腕（検証側 L7-L14）全体を統括する検証戦略の正本**である。各 L*↔L* ペアのテスト設計（L14/L12/L9/L8/L7）は、本書の ID universe 規約・双方向 trace 規約・gap 指標に従う。
> L0 は「検証を第一級原則とする」方向性のみを持ち、具体の検証方法論は本書（L1）で正本化する（tl-advisor 2026-06-03 Q1 判定）。
> 2026-06-03 session の trace 検証で **false-positive を 3 連発**した教訓を方法論として固定し、再発を機械的に防ぐことが本書の中核目的。

## 1. 検証の第一級原則
1. **設計⇔検証は対で閉じる**（HELIX Core §1）。各設計層は対の検証層と同粒度で、ID 単位で双方向に対応する。
2. **trace は宣言であって推論でない**（ISO 26262 / DO-178C）。forward（設計→テスト）と backward（テスト→設計）の両リンクが frontmatter / trace matrix に**明示**される。「読めば分かる」は trace ではない。
3. **片肺判定は ID universe を確定してから**。各層の実 ID 集合を先に固定せずに coverage を語ると誤検出する（§6）。

## 2. per-layer ID universe 規約（誤検出防止の中核）
各層は**独自の ID 命名規約**を持つ。層間で ID の連続（数字）を仮定してはならない。

| 層 | ID scheme（設計側） | 例 |
|---|---|---|
| L1 要求 | `FR-NN` / `NFR-XX-NN` / `BR-NN` / `TR-NN`（数字ベース） | FR-01, NFR-OP-04, BR-12 |
| L3 要件 | `FR-<NAME>-NN`（名前ベース） / `NFR-XX-NN` | FR-NSM-01, FR-GLOSSARY-01 |
| L4 基本設計 | `NFR-XX-NN` / `IF-NN` / コンポーネント名 | NFR-MG-02, IF-05 |
| テスト側 | `OT-NN`(L14) / `AT-NN`(L12) / `ST-*`(L9) / `TV-*`/`TR-*` | OT-13, AT-25, ST-NFR-01 |

**設計 ID universe = その doc の「定義行」のみ**から抽出する:
- 定義行 = 要件/機能の定義表で ID が**行の左端セル（主キー）**かつ説明列を伴う行。
- **除外**: §mapping/trace/対応/I-O 表（例「L1→L3 mapping」「対応要件 ID」列、CLI input/output 表）に**参照として**現れる上流 ID。これらは自層 universe ではない。
- **除外**: `status: deprecated` doc 内の ID。
- ID 形式 validation: `^(FR|NFR|BR|TR|OT|AT|ST|IF)-[A-Z0-9]+(-[0-9]+)?$`。

## 3. 双方向 trace 規約
- **forward リンク**（設計→テスト）: 設計 doc frontmatter `pairs_test_design` / `generates`。
- **backward リンク**（テスト→設計）: テスト doc の `parent_design` / `pairs_design` + trace matrix の「対応要件 ID」列。
- **pair_layer ≠ verification_layer**: `pairs_test_design` は V-model 構造ペア（pair_layer）の宣言であり、「その doc の全 ID をその層で直接検証する」意味ではない。検証層が pair_layer と異なる場合は `verification_layers` frontmatter で明示する（§7）。

## 4. gap 指標（detector 出力 = 機械判定の正本）
| 指標 | 定義 | 合否 |
|---|---|---|
| `coverage_pct`（**primary**） | (対応テスト≥1 の設計ID) / 全設計ID × 100（binary） | = 100 |
| `uncovered_req` | 対応テスト 0 の設計 ID | = 0 |
| `orphan_test` | 設計 ID に戻れないテスト ID | = 0 |
| `duplicate_id` | 複数 doc に同一 ID | preflight fail |
| `wrong_layer_pair` | pairs_test_design が V-model pair 表と別層 | preflight fail |
| `missing_pair_frontmatter` | 設計 doc に pair 宣言なし | preflight fail |
| `excluded_with_reason` | `acceptance_scope: excluded` 等＋代替層＋理由 | 許容（記録） |
| `deprecated_excluded` | deprecated 除外 doc | 記録のみ |
| `balance_ratio`（**補助**） | テストID数 / 設計ID数 | dashboard/warning のみ（合否主判定にしない）。doc-reviewer（FR-DOCREVIEW-01）の `balance_ratio ≥ 1.0` 検査は **doc 品質の目安（warning）**、whole-coverage audit の **合否（pass/fail）は coverage / missing_pair / preflight が主判定**。2 段 trace 構造（例 L4↔L9 の ST→TV→L4）では balance < 1.0 でも semantic 判定で pass しうる（§11.2、P2 整合） |

**preflight**: duplicate_id / wrong_layer_pair / missing_pair_frontmatter は coverage 計算前に fail とする（数値が信用できないため）。

## 5. detector（ワークフロー改善の実体）
- 実体: `cli/lib/trace_symmetry.py`（[[poc-2026-06-03-trace-symmetry-detector]]）。
- Phase1 = advisory PoC（計測・baseline、exit 0 維持）。**Phase3 で fail-close gate 化**（automation-gate-map に接続）。
- JSON schema（早期固定、tl-advisor 推奨）: `target_pair` / `design_id_count` / `test_id_count` / `missing_reverse_trace` / `orphan_test_ids` / `balance_ratio` / `id_universe` / `false_positive_reason`。
- 抽出規約は §2、gap 指標は §4 に従う。

## 6. false-positive 教訓（2026-06-03、再発防止 golden 化対象）
| # | 誤検出 | 根因 | 防止策（発火要件） |
|---|---|---|---|
| 1 | L3↔L12「FR-02〜14 uncovered」 | L3 は名前ベース ID なのに L1 数字式で grep | 各層の ID scheme を先に識別（§2） |
| 2 | L1↔L14 片肺 | doc の pair-routing 節（FR→L3↔L12 委譲明記）を未読 | 片肺宣言前に対象 doc の検証層ルーティング節を読む |
| 3 | detector も同 over-report | 自層定義 ID と上流参照 ID を未分離 | 定義行のみ抽出・mapping/参照列除外（§2） |
| — | 誤前提を TL に渡し判定汚染 | 検出結果を自己 verify せず諮問 | **検出結果は advisor 諮問前に PM が grep 自己 verify** |

**golden fixture 化（必須）**: ①健全 fixture（L1↔L14, L3↔L12）②真陽性 fixture（L4↔L9 = NFR viewpoint gap / IF-05）③false-positive 再発 fixture（ID 体系混同）。detector 昇格前に ID-universe 分離の単体テスト必須。

## 7. verification_layers 契約（pair_layer と検証層の分離）
L1 要求 doc は `pairs_with: L14`（構造ペア）を持つが、要求種別ごとに実検証層が異なる:
- **BR / 運用 NFR（AV/OP）** → L14（運用検証）で直接検証。
- **FR** → L3↔L12（受入）/ L4↔L9（総合）/ L7（単体）へ routing。
- **TR** → L4/L9, L5/L8, L7。
- **NFR-MG/PF/SC/SE** → L12/L9/専用 security・perf。

→ L1 functional/technical/nfr doc に `verification_layers` frontmatter を追加し、detector が「pair_layer=L14 ≠ 検証層」を機械識別できるようにする（frozen doc 改変につき G1 再凍結を伴う、実施可否は Phase1/Phase2 で判断）。

## 8. 各 pair の検証層マッピング（現状）
| pair | 検証層の意味 | 2026-06-03 状態（Phase2 完遂後） |
|---|---|---|
| L1↔L14 | 運用検証（BR+運用NFR） | ✅ frozen（cov100% / 1.00、verification_layers 契約で FR を L3↔L12/L9/L7 へ routing・excluded 36） |
| L3↔L12 | 受入（FR+NFR） | ✅ frozen（18 名前ベース FR 全 AT、cov100% / 1.00） |
| L4↔L9 | 総合（NFR/IF/コンポーネント） | ✅ frozen（cov100% / missing0、orphan18=ST→TV→L4 の2段trace で excluded・balance0.67 補助、§11/L9 §7.1 re-freeze） |
| L5↔L8 | 結合 | ✅ frozen（cov100% / 1.00。gap=IT-MOD-06/IT-DB-03/IT-DB-05 明示=deferred） |
| L6↔L7 | 単体（DbC） | ✅ frozen（cov100% / 1.00、FN-*↔UT-* 1:1。観測済14契約に限定=deferred） |

## 10. 定量判定 vs 定性判定の基準（ユーザー指摘 2026-06-03）
**結論: 組合せが最適（角度が最も高い）。** HELIX は既に gate で `gate_verdict = static_subchecks AND ai_review_required_when(...)` を採用済（L0 concept §6.5）。定量を先行・必要条件、定性を最終・十分条件に置く。

| | 定量判定（機械） | 定性判定（AI/人） |
|---|---|---|
| 対象 | 客観・再現可能・ID 単位の事実（coverage_pct / count / trace 存在 / frontmatter / exit 0） | 意味・文脈（真の片肺か正当 routing か / 設計の妥当性 / 検証深度） |
| 長所 | 速い・スケール・fail-close・gate 化可能 | 意図と文脈を読める |
| 弱点 | **モデルが正しい時のみ正しい**（誤モデル → over-report = false positive） | 主観・コスト・誤前提に弱い |

**判断基準（どちらを使うか）**:
- **定量で足りる**: 客観計測可能 **かつ モデル検証済**（例: 各設計 ID に ≥1 テスト、ただし ID universe 確定後 §2）。
- **定性が要る**: 意味理解が必要（例: NFR の検証深度が十分か、gap が片肺か委譲か）。
- **組合せ**: 定量を **preflight 必要条件**（fail-close）、定性を **最終十分条件**（semantic gate）。これが最高精度。

**相互ガード（今 session の実証）**: 定量（detector）は**新規/未検証モデル**だと false positive を出す → 定性（TL/PM）が捕捉。逆に定性（TL）は**誤った定量前提**を渡されると判定が汚染される → 定量は**自己 verify してから諮問**。**両者は相互ガードし合う。単独運用はどちらも危険**。新規 detector/指標は定性 cross-check で golden 化してから fail-close gate に昇格させる（§6）。

## 11. whole-coverage audit recipe（見直しの体系化 — 駆動モデルでなく Forward 検証 activity）

> ユーザー指摘（2026-06-03）「見直しが何度も発生する。駆動モデルは作る／ある？」への回答。**「設計成果物の質・カバレッジ・整合を横断再検査して re-freeze する見直し」は新しい駆動 workflow にしない**（tl-advisor 条件付き推奨 (B)）。V から外れた別入口ではなく「V-model pair が閉じているかの再検査」= Forward 右腕の検証 + Core §4 自動検出ループの activity だから。新駆動化は HELIX 絶対原則（V 起点・枝は最小・必ず V へ戻す）に反し、既存 `helix audit`（A0/A1 decision 用）とも用語衝突する。`whole-coverage audit` は workflow / kind ではなく **gate recipe（activity）** として定義する。今まで Recovery で代用してきたが、Recovery の本旨（逸脱・破綻の収束）と「健全進行後の品質再検査」は意味がミスマッチであり、本 recipe で分離する。

### 11.1 トリガ
- Phase / freeze 前（必須）、定期、ユーザー指示、detector の whole-coverage 劣化検出（detection-routing の trace 不整合）。

### 11.2 判定式（必要条件 AND 十分条件）
`audit_verdict = detector_clean（必要条件）AND semantic_gate_pass（十分条件）`
1. **必要条件（機械）**: `cli/lib/trace_symmetry.py` で全 pair を measure。preflight（duplicate_id / wrong_layer_pair / missing_pair_frontmatter）が fail なら数値無効 → 先に修正（§4 preflight）。coverage / missing_pair / balance を取得。
2. **十分条件（semantic）**: TL/PM が orphan_test / excluded_with_reason / balance warning を意味判定（真の片肺か正当 routing か、検証深度が十分か）。§10 の定量 vs 定性基準に従う。
   - **coverage 100% だけで re-freeze pass にしない**（balance / orphan が残れば semantic 判定必須。例: L4↔L9 の ST-* orphan）。

### 11.3 owner と承認
| activity | owner |
|---|---|
| detector 実行 + semantic gate 判定 | TL |
| re-freeze 承認 | 該当 gate owner（L4/L9=TL+PM、L1/L14=PM/PO） |
| 要件・scope・NFR の意味が変わる | PM/PO 承認（freeze-break / CC 扱い） |

### 11.4 gap 検出時の routing（既存駆動へ、新 kind を作らない）
[detection-routing](../../../HELIX-workflows/helix-process/detection-routing.md) の routing 表に従う:

| gap 種別 | routing |
|---|---|
| 設計 ⇔ テスト設計の欠落 | 該当 Forward L の再凍結作業 |
| 既存実態から設計復元が必要 | `kind=reverse` |
| コード構造劣化 | `kind=refactor` |
| AI/工程逸脱・早すぎる完遂宣言 | `kind=recovery` |
| 基盤・形式移行 | `kind=retrofit` |

### 11.5 evidence schema（semantic re-freeze の証跡 — gate 内完結で証跡が消えるのを防ぐ）
re-freeze は次の schema で記録し、DB / PLAN / audit trail から追えるようにする:

```yaml
refreeze_decision:
  pair: L4-L9
  detector:                      # 必要条件（機械、trace_symmetry --json）
    coverage_pct: 100.0
    balance_ratio: 0.67
    orphan_test_ids: [ST-...]
    missing_pair: 0
    preflight: pass
  semantic_gate:                 # 十分条件（TL/PM の意味判定）
    owner: TL
    verdict: pass | conditional | fail
    orphan_assessment: "..."     # orphan / excluded の妥当性
    rationale: "..."
  refreeze:
    approvers: [TL, PM]
    routing: none | {kind, plan_id}   # gap があれば既存 kind へ
```
- **detector clean かつ semantic 判定のみ（gap なし）**: 新 PLAN 不要。該当 L/gate evidence、readiness/deferred finding、または既存 Process Plan の closure evidence に記録。
- **gap 修正が必要**: §11.4 の該当 kind PLAN を起票し routing。

### 11.6 機械化の段階
- 現状: detector advisory（exit 0）。**Phase3 で fail-close gate 化**（`helix doctor check_pair_trace_symmetry` / automation-gate-map 接続、§9 carry）。
- semantic gate は AI/人の判定であり機械化しない（§10）。detector はその必要条件を供給するに留める。

## 9. carry
- **Phase2 完遂（2026-06-03）**: L1↔L14 / L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7 全 5 pair frozen + detector cov100% / missing0 / wrong_layer0 / dup0。「見直し」を whole-coverage audit recipe（§11）として体系化（新駆動 workflow を作らず Forward 検証 activity 化、tl-advisor 諮問2回 passed）。
- **deferred finding（TL P3、whole-coverage audit re-freeze 時の追跡対象）**:
  - `DF-WCAUDIT-L4L9-001`: detector が ST→TV→L4 推移 trace 未対応で orphan18（全 ST-*）を over-report。semantic 判定で excluded（L9 §7.1）。detector の推移 trace 解決は Phase3。
  - `DF-WCAUDIT-L5L8-001`: L5↔L8 gap = IT-MOD-06 / IT-DB-03 / IT-DB-05（結合テスト未実装、設計 gap でない。L8 doc 明示済）。
  - `DF-WCAUDIT-L6L7-001`: L6↔L7 は観測済 public contract 14 に限定（全関数網羅でない、粒度爆発回避の意図的限定）。将来 FR 拡張時に再評価。
- **Phase3**: detector fail-close gate 化（automation-gate-map 接続、`helix doctor check_pair_trace_symmetry`）+ ST→TV→L4 推移 trace 解決 + whole-coverage audit recipe（§11）の CI 連動。
- detector golden fixture（§6）の整備。
