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
| L4↔L9 | 総合（NFR/IF/コンポーネント） | ✅ frozen（machine: cov100%/missing0 clean だが **orphan_test=18≠0**＝machine-clean でない。semantic-pass: ST→TV→L4 の2段trace で excluded・balance0.67 補助、§11/§12/L9 §7.1 re-freeze） |
| L5↔L8 | 結合 | ✅ frozen（machine-clean cov100% / 1.00。gap=IT-MOD-06/IT-DB-03/IT-DB-05 明示=deferred。L5=実質設計と確認 §12） |
| L6↔L7 | 単体（DbC） | ✅ frozen（machine-clean cov100% / 1.00、FN-*↔UT-* 1:1。観測契約 subset=`DF-WCAUDIT-L6L7-001` / 責務粒度 caveat=`DF-WCAUDIT-L6L7-002`、§12 で honest 化） |

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

### 11.7 whole-source ⊆ design coverage（zero-omission、2026-06-07）

> ユーザー goal「設計に既存ソースのすべてが含まれているか徹底検証し、抜け漏れを一切禁止」への回答。§11 の whole-coverage audit は従来「pair が閉じているか」を測ったが、**「既存ソースのすべてが設計層に被覆されているか」** を測る軸を本節で追加する。evidence = [AUDIT-WSDC-001](../../audit/2026-06-07-whole-source-design-coverage-audit.md)、是正 Process = `process-2026-06-07-whole-source-design-coverage-closure`。

**zero-omission の定義（B'、tl-advisor 2026-06-07 採用）**:
```
zero_omission = source ⊆ registry
            AND registry → L1/L3 trace complete（l1_fr/l3_fr 非空・ID 実在）
            AND 全 active registry entry が明示的 coverage_layer 分類を持つ（unknown=0）
```

**coverage_layer 分類基準**（functional-registry 各 entry に付与。「L6 逃げ」防止のため L4/L5 被覆でも design_id 必須・excluded は理由必須）:

| coverage_layer | 線引き（判定基準） | 設計反映 |
|---|---|---|
| `L6_required` | **public callable / 独立した振る舞い契約 / DbC（requires/ensures/invariant）が必要**なもの（例: guard verdict, validator, db CRUD helper） | FN-* + UT-* を 1:1（関数粒度ペアリング厳守） |
| `L5_required` | module 境界 / 結合 / data flow / 内部 process（例: engine, manager, routing） | MOD-* / IT-* で被覆（design_id 必須） |
| `L4_required` | workflow / architecture / NFR / command family / system interaction（例: helix-* CLI family, workflow doc, template） | NFR-* / IF-* / ST-* で被覆（design_id 必須） |
| `excluded_with_reason` | private glue / 生成物 / static template / 参照専用 doc | 新規 FN/UT 不要だが**上位設計 ID + 除外理由が必須**（orphan 禁止） |

- **却下した解釈**: A（全 registry entry を FN/UT 化）= template/workflow doc まで単体テスト化する粒度誤り。C（registry+要件 trace のみ）= 設計層被覆を証明せず goal 未達。
- **機械証明 detector**（§11.6 の機械化対象に追加）: `source_scan_vs_registry`（unregistered=0）/ `registry_trace_complete`（invalid=0）/ **`registry_design_coverage`（新設: coverage_layer + design_id 充足、unknown=0 / missing=0 / wrong_layer=0）** / `trace_symmetry`（L6_required は FN↔UT 1:1）。`check_functional_registry` は clean baseline 後 ratchet→fail-close 昇格。
- **完了判定**: `detector_clean AND semantic_gate_pass`（§11.2 と同式、coverage 100% 単独 pass は禁止）。zero-omission 宣言は registry_design_coverage の unknown=0 と L6_required pair green の両成立後。

## 9. carry
- **Phase2 完遂（2026-06-03）**: L1↔L14 / L3↔L12 / L4↔L9 / L5↔L8 / L6↔L7 全 5 pair frozen + detector cov100% / missing0 / wrong_layer0 / dup0。「見直し」を whole-coverage audit recipe（§11）として体系化（新駆動 workflow を作らず Forward 検証 activity 化、tl-advisor 諮問2回 passed）。
- **deferred finding（TL P3、whole-coverage audit re-freeze 時の追跡対象）**:
  - `DF-WCAUDIT-L4L9-001`: detector が ST→TV→L4 推移 trace 未対応で orphan18（全 ST-*）を over-report。semantic 判定で excluded（L9 §7.1）。detector の推移 trace 解決は Phase3。
  - `DF-WCAUDIT-L5L8-001`: L5↔L8 gap = IT-MOD-06 / IT-DB-03 / IT-DB-05（結合テスト未実装、設計 gap でない。L8 doc 明示済）。
  - `DF-WCAUDIT-L6L7-001`: ~~L6↔L7 は観測済 public contract 14 に限定（全 139 lib 関数の約 10%、粒度爆発回避の意図的限定）~~ → **SUPERSEDED（2026-06-07）**: goal「抜け漏れ一切禁止」により defer 継続不可。`process-2026-06-07-whole-source-design-coverage-closure`（§11.7 B' / coverage_layer 分類）へ巻取り、全 active entry を L4/L5/L6/excluded に明示分類し L6_required のみ FN/UT 1:1 拡張する。以下は supersede 前の記録。**gap クラスタ**: `FN-CATALOG-01` / `FN-CONTRACT-01` は公開契約を起こしたが背後モジュール `code_catalog` / `contract_registry` / `doc_map_matcher` / `deliverable_gate` の内部実装設計が未定義 = **`DF-WCAUDIT-L5L8-001`（IT-MOD-06/IT-DB-03/IT-DB-05）と同根**（2026-06-03 Phase2 総合見直し pmo Gap-1 で connective 確認）。universe 分類は L6 §5.1。将来 FR 拡張時に再評価。
  - `DF-WCAUDIT-L6L7-002`（2026-06-03 Phase2 総合見直し tl-advisor P1 新規）: L6 `FN-*` は Reverse 由来の **観測契約 / 責務粒度**で、`FN-AGENT-01`(fire/release) `FN-CONTRACT-01`(登録/照合) `FN-DB-01`(接続/CRUD) `FN-HANDOVER-01`(resume/stale) 等が 1 FN に複数オペレーションを束ねており、厳密な「関数 1 個 = UT 1 個 / callable・入力型・例外型明示」より粗い（`FN-ROUTE-01` のみ単一関数）。1 FN↔1 UT で内部整合・detector green だが、厳密分割と callable/error contract 明示は Phase3 L7 実装（TDD sharpening）へ defer。L6 §5.2 記録。
- **Phase3**: detector fail-close gate 化（automation-gate-map 接続、`helix doctor check_pair_trace_symmetry`）+ ST→TV→L4 推移 trace 解決 + whole-coverage audit recipe（§11）の CI 連動。
- detector golden fixture（§6）の整備。

## 12. Phase2 総合見直し refreeze_decision 証跡（2026-06-03、whole-coverage audit recipe §11 実行）

> ユーザー指示「Phase2 の総合的見直し」を §11 whole-coverage audit recipe で実行。必要条件（detector 機械測定）+ 十分条件（tl-advisor adversarial + pmo 事実監査の二重 semantic gate）。**新 finding（L6 粒度 caveat = `DF-WCAUDIT-L6L7-002`、L6/L8 gap 同根クラスタ）を surface**し、freeze 文言を honest 化（design 変更なし）。machine-clean と semantic-pass を以下で明確に分離する。

```yaml
refreeze_decision:                 # Phase2 対象 3 pair（L1↔L14 / L3↔L12 は Phase1 で確定済）
  - pair: L6-L7
    detector:                      # 必要条件（trace_symmetry --json）
      coverage_pct: 100.0
      balance_ratio: 1.0
      orphan_test: 0
      missing_pair: 0
      preflight: pass
    semantic_gate:                 # 十分条件（二重 audit）
      owner: TL(tl-advisor) + PM(Opus)
      verdict: conditional         # 観測契約 subset としては成立、ただし freeze 文言の明確化が条件
      assessment: "14 FN-* は DbC 完備・L7 UT-* と 1:1。ただし (a) 全 139 関数の ~10% subset、(b) FN-* が責務/複数オペレーション粒度で厳密単一関数より粗い、(c) catalog/contract 系 module の内部設計 gap が L8 gap3 と同根。"
      rationale: "universe を §5.1 で明示分類、粒度 caveat を §5.2/DF-WCAUDIT-L6L7-002 で宣言し subset freeze として honest 化。実 expansion・厳密分割は Phase3 L7（TDD sharpening）へ defer。"
    refreeze:
      approvers: [TL, PM]
      design_changed: false        # 範囲宣言の明確化のみ。FN-*/UT-*/DbC は不変、detector green 不変
      routing: {kind: defer, target: Phase3-L7, findings: [DF-WCAUDIT-L6L7-001, DF-WCAUDIT-L6L7-002]}
  - pair: L5-L8
    detector: {coverage_pct: 100.0, balance_ratio: 1.0, orphan_test: 0, missing_pair: 0, preflight: pass}
    semantic_gate:
      owner: TL + PM
      verdict: pass
      assessment: "L5 4 doc（878 行）は実質設計（DDL/Mermaid/擬似コード/状態遷移、placeholder 残存 0）。薄い殻ではない（私の初期仮説を反証）。L8 21 IT-* が L5 21 設計 ID へ双方向 trace。"
      rationale: "gap=IT-MOD-06/IT-DB-03/IT-DB-05 は結合テスト未実装（設計 gap でなく L8 明示済の deferred）。G8 前に observed 化。"
    refreeze:
      approvers: [TL, PM]
      design_changed: false
      routing: {kind: defer, target: Phase5-G8, findings: [DF-WCAUDIT-L5L8-001]}
  - pair: L4-L9
    detector:                      # ★machine と semantic を混同しない（tl-advisor P2）
      coverage_pct: 100.0          # coverage/uncovered/missing_pair/wrong_layer は machine-clean
      balance_ratio: 0.67
      orphan_test: 18              # ★ST-* 全件は machine-clean でない（≠0）。semantic 判定で pass
      missing_pair: 0
      preflight: pass
    semantic_gate:
      owner: TL + PM
      verdict: pass
      assessment: "orphan18=ST-* は ST→TV→L4 の 2 段推移 trace が成立（L9 §7.1）。総合テストのシナリオが TV-* 経由で L4 設計項目へ繋がる構造は妥当（直 backlink を全 ST に足すと冗長）。"
      rationale: "machine: 4 指標 clean だが orphan_test=18（detector が推移 trace 未対応）。semantic: 妥当な 2 段 trace。両者を分離表記（machine-clean + orphan semantic-pass）。"
    refreeze:
      approvers: [TL, PM]
      design_changed: false
      routing: {kind: defer, target: Phase3, findings: [DF-WCAUDIT-L4L9-001]}  # detector 推移 trace 解決
```

**Phase2 見直し総括**: 3 pair とも design 変更不要（freeze 維持）。L5↔L8 / L4↔L9 は既存 deferred finding を独立再確認、L6↔L7 は新 finding（粒度 caveat + gap 同根クラスタ）を surface し freeze 文言を honest 化。**用語規律**: 「全 5 pair frozen」は正しいが「全 5 pair machine-green」は誤り（L4↔L9 は orphan_test=18 で machine-clean でなく semantic-pass）。今後は **machine-clean（coverage/uncovered/missing_pair/wrong_layer の 4 指標）と semantic-pass（orphan/balance の意味判定）を分離**して表現する。

## 13. Action4 L6↔L7 whole-source coverage refreeze_decision（2026-06-07、§11.7 zero-omission B'）

> `process-2026-06-07-whole-source-design-coverage-closure` Action4。L6_required 65 entry に FN-WSC-* + UT-WSC-* を 1:1 付与（11 既存FN接続 + 54 新規）し L6↔L7 を再凍結。forward-return-discipline 適用（design_or_contract_changed = FN universe 拡張、対 design 層 L6 を再凍結）。

```yaml
refreeze_decision:
  pair: L6-L7
  trigger: whole-source-design-coverage (AUDIT-WSDC-001, goal=zero-omission)
  design_change_class: design_or_contract_changed   # FN universe 33→87 拡張 (pure_impl 不可)
  detector:                          # machine-clean (全指標)
    coverage_pct: 100.0
    balance_ratio: 1.0
    missing_pair: 0
    duplicate_id: 0
    orphan_test: 0
    preflight: pass
  registry_design_coverage:          # zero-omission 機械証明 (新 detector、necessary condition)
    active_entries: 549
    unknown_coverage_layer: 0
    design_id_missing: 0
    wrong_layer: 0
    l6_design_pending: 0
    proof_scope: "anchor/prefix 整合 + semantic review 補完 (実 doc ID 存在チェックではない=必要条件)。WSC ID の実 doc 存在は L6/L7 doc + trace_symmetry で別途担保"
  semantic_gate:
    owner: TL
    verdict: approve                 # TL impl review changes_required → P1/P2 反映 → re-review passed (zero-omission approve, P0-P3 指摘なし)
    note: "TL 抜き取り検証で分類妥当・FN-WSC DbC faithful (agent guard deny / post-tool-use fail-open / push_gate execute・main guard / job enqueue advisory 実コード整合) を確認済。changes_required は証跡品質3点のみで、反映済。approve は re-review で確定"
  refreeze:
    approvers: [TL, PM]
    routing: {kind: closed, target: L7-sprint, findings: []}
    deferred_finding:
      id: WSC-TEST-IMPL
      count: 0
      detail: "2026-06-07 verify-first closure 完了。既存充足 1 (FN-WSC-10 pretooluse-codex-slot-check)、新規/補助テスト実装 11 (FN-WSC-02/03/04/05/06/12/13/15/17/213 uuid7_generator/218)。設計の抜け漏れではなく test 実装 carry だったことを確認し、L7 whole-source-coverage-単体テスト設計.md / L7-wsc-test-impl-closureplan の実体と一致。"
```

**Action4 総括**: zero-omission（B'）の machine 証明が成立 — source⊆registry（unregistered=0）⊆要件 trace（invalid=0）⊆設計層（registry_design_coverage: unknown=0 / pending=0 / wrong_layer=0、**必要条件**）+ L6↔L7 trace_symmetry balance1.0 + semantic gate（TL impl review approve）。**設計の抜け漏れ = 0**。`WSC-TEST-IMPL` は 2026-06-07 に closure 済みで、verify-first 実測と L7 台帳が一致している。`registry_design_coverage` は design_id を anchor/prefix で解決する**必要条件 detector**であり、「実 doc ID 存在証明」ではない（WSC ID の実在は L6/L7 doc + trace_symmetry が担保）。
