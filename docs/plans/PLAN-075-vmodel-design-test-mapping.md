---
plan_id: PLAN-075
title: "PLAN-075: V-model 4 artifact 双方向 trace framework 強化 (5 Phase)"
status: completed
size: L
drive: be
created: 2026-05-17
revised: 2026-05-17 (4 artifact 解釈に訂正)
completed: 2026-05-17 (Phase 5 完遂、commit c2e2ed4)
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-074 (HTTP endpoint 層、4 artifact trace 欠落の起点)
  - PLAN-076 (subagent 工程マッピング、同時並行)
  - PLAN-077 (Sprint Plan 標準化、同時並行)
trigger: |
  ユーザー指摘 2026-05-17 (1):「基本設計は総合テスト設計も含むんだよ？
  詳細設計は結合テスト設計も含むんだよん？機能設計は単体テスト設計も含むんだよ？」

  ユーザー指摘 2026-05-17 (2、訂正): 「同じ文書に書いたらダメだろ？設計とコード、
  テスト設計とテストコードがあるんだから。」
  → 当初の解釈「設計とテスト設計を同じ文書に統合」は誤り。正しくは 4 artifact が
    別文書として存在し、双方向 trace で繋ぐ。

  HELIX framework 全体で 4 artifact (設計 / 実装コード / テスト設計 / テストコード)
  の双方向 trace を framework 化する。
acceptance:
  - HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に V-model 4 artifact 双方向 trace 原則を明文化
  - L2/L3/機能設計テンプレートに「対応するテスト設計ファイル参照」を強制
  - PLAN-074 を retrofit (PLAN-074-unit-test-design.md は維持、D-API EXT 等に双方向 reference を追加)
  - 他既存 PLAN の 4 artifact 揃い + trace 整合性チェック
  - helix doctor / G2-G4 ゲートに自動 lint 追加 (4 artifact 揃い + 双方向 trace 確認)
---

# PLAN-075: V-model 4 artifact 双方向 trace framework 強化 (5 Phase)

## §1 背景

### V-model 4 artifact 構造

ソフトウェア工学の V-model では、設計フェーズの各層と検証 (テスト) フェーズの各層が 1:1 対応する。ただし **4 つの artifact は別々の文書として存在** し、双方向 trace で繋ぐ。同じ文書に統合してはいけない:

```
① 設計層              ←対応関係→  ③ テスト設計層
        ↓ 実装                            ↓ 実装
② 実装コード          ←対応関係→  ④ テストコード
```

| Artifact | 担当層 | 例 (PLAN-074 で言うと) |
|---|---|---|
| **① 設計** | 機能設計 / 詳細設計 / 全体設計 | docs/v2/L3-detailed-design/D-API/D-API-EXTENDED-draft.md §3.X |
| **② 実装コード** | 設計の実装 | cli/lib/http_api/routes/audit.py |
| **③ テスト設計** | テスト計画 (単体/結合/総合) | docs/v2/L4-test-design/PLAN-074-unit-test-design.md |
| **④ テストコード** | テスト設計の実装 | cli/lib/tests/test_http_api_audit.py |

### 当初解釈の誤り (2026-05-17 訂正)

本 PLAN 起票時、「設計とテスト設計を同じ文書に書く」と誤解釈した。**訂正**:
- 設計 (①) と実装コード (②) を同じ文書に書かないのと同様、
- テスト設計 (③) とテストコード (④) も同じ文書に書かない
- 設計 (①) と テスト設計 (③) も同じ文書に書かない (それぞれ別 artifact)
- 4 artifact は **別文書**、**双方向 reference** で trace

### HELIX 現状の整合性

| HELIX 層 | ① 設計 | ② 実装コード | ③ テスト設計 | ④ テストコード |
|---|---|---|---|---|
| L1 要件定義 | requirements/acceptance | - | **受入テスト設計 欠落** | (L8 受入) |
| L2 全体設計 | CONCEPT / ADR | - | **総合テスト設計 欠落** | (L6 統合検証) |
| L3 詳細設計 | D-API / D-DB | routes/*.py 等 | **結合テスト設計 欠落** | test_http_api_*.py (現 integration) |
| L3-L4 機能設計 | request/response schema | routes/*.py | **単体テスト設計 一部のみ** (PLAN-074-unit-test-design.md) | **欠落** (PLAN-074-L4-008 で実装予定) |

→ ③ テスト設計が全層で欠落 ⇔ ④ テストコードが部分的に存在 (=逆ピラミッド)。本 PLAN で是正する。

### 双方向 trace ルール

各 artifact は対応関係を明示する:

| From → To | 記述方法 |
|---|---|
| 設計 ① → 実装コード ② | 設計に「実装ファイル: X.py」 |
| 実装コード ② → 設計 ① | コード docstring に「契約: D-API EXT §3.X」 |
| 設計 ① → テスト設計 ③ | 設計に「テスト設計: PLAN-XXX-*-design.md」 |
| テスト設計 ③ → 設計 ① | テスト設計に「対象設計: D-API EXT §3.X」 |
| テスト設計 ③ → テストコード ④ | テスト設計に「テスト実装: test_*.py、各 case U-XXX-001 対応」 |
| テストコード ④ → テスト設計 ③ | テスト docstring に「DoD 検証: PLAN-XXX-*-design.md U-XXX-001〜N」 |

## §2 5 Phase 構成

### Phase 1 — V-model 4 artifact 原則を HELIX core に明文化 (size: M)

- `helix/HELIX_CORE.md` に「§設計⇔テスト対応 (V-model 4 artifact)」セクション追加
- `skills/SKILL_MAP.md` の各 L レイヤ説明に「4 artifact + 双方向 trace」明示
- `CLAUDE.md` (project + global) に V-model 4 artifact 運用ルール追加
- 受入: 3 文書全件に 4 artifact 原則が明文化されている

### Phase 2 — テンプレート + skill 責務再整理 (size: L、estimate 60-90 min)

#### Phase 2 sub-sprint 構成 (HELIX 標準粒度準拠)

| WBS | sub-sprint | 内容 | role | 並列 |
|---|---|---|---|---|
| WBS-075-P2-001 | .2.1a | 影響範囲確認 (skills/SKILL_MAP.md / workflow-core.md / gate-policy.md 読み) | pm | 単独 |
| WBS-075-P2-002 | .2.1b | テンプレート設計 (4 artifact reference セクション構造) | pm | 単独 |
| WBS-075-P2-003 | .2.2a | cli/templates/PLAN.md.template に 4 artifact reference セクション追加 | pm or docs | A 系 |
| WBS-075-P2-004 | .2.2b | skills/workflow/design-doc/SKILL.md update (① 設計 + ③ 総合/結合テスト設計 reference) | docs | A 系 |
| WBS-075-P2-005 | .2.2c | skills/workflow/api-contract/SKILL.md update (① 詳細設計 + ③ 結合テスト設計 reference) | docs | A 系 |
| WBS-075-P2-006 | .2.2d | skills/common/testing/SKILL.md update (③ テスト設計 ↔ ④ テストコードの責務分離) | docs | B 系 |
| WBS-075-P2-007 | .2.2e | skills/workflow/verification/SKILL.md update (4 artifact 双方向 trace 検証) | docs | B 系 |
| WBS-075-P2-008 | .2.3 | reference 文書 (gate-policy.md / workflow-core.md) 関連箇所 update | pm | 単独 |
| WBS-075-P2-009 | .2.4 | bash -n / py_compile / markdownlint / 全回帰 (mandatory in sprint) | pm | 単独 |
| WBS-075-P2-010 | .2.5 | commit + push | pm | 単独 |

**並列性**: A 系 (.2.2a/b/c) と B 系 (.2.2d/e) は対象ファイル群が独立、並列投入可。

**受入条件**:
- cli/templates/PLAN.md.template が 4 artifact reference を強制
- workflow/design-doc / api-contract が ① 設計 → ③ テスト設計 reference 義務
- common/testing が ③ テスト設計 ↔ ④ テストコードの分離を明示
- workflow/verification が 4 artifact 揃いの検証責務
- pytest / bats 全回帰 PASS

### Phase 3 — PLAN-074 retrofit (size: M-L、estimate 90-150 min)

**PLAN-074-unit-test-design.md は維持** (③ テスト設計の正しい artifact)。双方向 trace の欠落部分を補完。

#### Phase 3 sub-sprint 構成

| WBS | sub-sprint | 内容 | role | 並列 |
|---|---|---|---|---|
| WBS-075-P3-001 | .3.1a | 既存 ④ test 27 cases の 5 endpoint 別 分類確認 (read) | pm | 単独 |
| WBS-075-P3-002 | .3.1b | 新規 ③ artifact 命名規約確定 (PLAN-074-system-test-design.md / PLAN-074-integration-test-design.md) | pm | 単独 |
| WBS-075-P3-003 | .3.2a | D-API EXT §3.1-3.5 に「テスト設計ファイル」3 行追記 (① → ③、5 endpoint) | pm | 単独 |
| WBS-075-P3-004 | .3.2b | PLAN-074-unit-test-design.md §2.X 各 module に「対象設計: D-API EXT §3.X」追記 (③ → ①) | pm | 単独 (.3.2a 完了後) |
| WBS-075-P3-005 | .3.3a | PLAN-074-system-test-design.md 新規 (総合テスト設計、E2E 25 シナリオ) | docs | A 系 |
| WBS-075-P3-006 | .3.3b | PLAN-074-integration-test-design.md 新規 (結合テスト設計、現 27 cases の設計親) | docs | A 系 |
| WBS-075-P3-007 | .3.4a | 単体 test 23 cases 実装 (auth/envelope/validation/server unit) | qa | B 系 |
| WBS-075-P3-008 | .3.4b | 単体 test 26 cases 実装 (routes/audit + telemetry unit) | qa | B 系 |
| WBS-075-P3-009 | .3.4c | 単体 test 14 cases 実装 (routes/hooks + push_pr unit) | qa | B 系 |
| WBS-075-P3-010 | .3.5 | test_http_api_*.py docstring に「DoD 検証: PLAN-074-*-design.md」追記 (④ → ③、5 file) | pm | 単独 |
| WBS-075-P3-011 | .3.6 | 4 artifact 揃い検証 + 全回帰 (pytest 1319+63=1382 PASS、bats 479 PASS) | pm | 単独 |
| WBS-075-P3-012 | .3.7 | commit + push (4 artifact retrofit + 単体 test 63 cases) | pm | 単独 |

**並列性**:
- A 系 (.3.3a/b): system-test-design / integration-test-design 同時 Write (異なるファイル)
- B 系 (.3.4a/b/c): 3 並列 Codex qa 投入 (test ファイル独立、helix_db 経由 mock 戦略は PLAN-074-unit-test-design.md §4 で共通化済)

**受入条件**:
- D-API EXT §3.1-3.5 全件で「テスト設計ファイル」reference 存在
- PLAN-074-unit-test-design.md / system-test-design.md / integration-test-design.md の 3 ③ artifact が揃う
- 単体 test 63/63 PASS、結合 27/27 維持、全回帰 1382/1382 + 479 + 614 PASS
- 5 test ファイル docstring に「DoD 検証: PLAN-074-*-design.md」reference 存在
- grep -r "PLAN-074-unit-test-design" で 4 ノード (① 設計 + ③ テスト設計 + ④ テストコード + PLAN-074.md) ヒット

### Phase 4 — 他既存 PLAN audit + retrofit (size: M-L、estimate 60-120 min)

#### Phase 4 sub-sprint 構成

| WBS | sub-sprint | 内容 | role | 並列 |
|---|---|---|---|---|
| WBS-075-P4-001 | .4.1a | audit 対象 PLAN 一覧化 (PLAN-067〜074) + 各 PLAN の 4 artifact 状況を spreadsheet 化 | pmo-sonnet (Agent 委譲) | 単独 |
| WBS-075-P4-002 | .4.1b | audit 結果集計表 (`docs/v2/audit/plan-067-074-vmodel-audit.md` 新規) | pm | 単独 |
| WBS-075-P4-003 | .4.2 | P0 retrofit (③ テスト設計欠落で本番影響あり) — 各 PLAN 個別 issue 化 | pm | 単独 |
| WBS-075-P4-004 | .4.3a | PLAN-068 (V-model 強化) retrofit | docs | A 系 |
| WBS-075-P4-005 | .4.3b | PLAN-070 (L3 schema and contract) retrofit | docs | A 系 |
| WBS-075-P4-006 | .4.3c | PLAN-071 (carry capability detailing) retrofit | docs | A 系 |
| WBS-075-P4-007 | .4.4 | retrofit 困難な PLAN を carry note 化 (deferred-findings.yaml 追加) | pm | 単独 |
| WBS-075-P4-008 | .4.5 | commit + push | pm | 単独 |

**audit 観点 (PLAN ごとに チェック)**:
1. ① 設計 artifact 存在? (D-API EXT 等)
2. ② 実装コード存在? (cli/lib/*)
3. ③ テスト設計 artifact 存在? (docs/v2/L4-test-design/*-design.md)
4. ④ テストコード存在? (cli/lib/tests/*)
5. ① → ②, ① → ③, ③ → ④ の双方向 reference 存在?

**並列性**: A 系 (.4.3a/b/c) は異なる PLAN なのでファイル衝突なし、3 並列可。

**受入条件**:
- docs/v2/audit/plan-067-074-vmodel-audit.md で全 PLAN の 4 artifact 状況可視化
- P0 retrofit 完遂 (本番影響あるもの)
- P1 以下は deferred-findings.yaml で carry 管理

### Phase 5 — helix doctor / G2-G4 自動 lint 追加 (size: M、estimate 60-90 min)

#### Phase 5 sub-sprint 構成

| WBS | sub-sprint | 内容 | role | 並列 |
|---|---|---|---|---|
| WBS-075-P5-001 | .5.1a | lint 仕様設計 (4 artifact + 双方向 trace check の判定基準) | pm | 単独 |
| WBS-075-P5-002 | .5.1b | cli/lib/doctor.py の現状確認 (既存 check 構造、整合性) | pm | 単独 |
| WBS-075-P5-003 | .5.2 | vmodel_lint.py 新規実装 (4 artifact + reference check、PLAN frontmatter parse) | se | 単独 |
| WBS-075-P5-004 | .5.3 | helix doctor 統合 (vmodel_lint 呼び出し追加) | se | 単独 (.5.2 完了後) |
| WBS-075-P5-005 | .5.4 | G2 / G3 / G4 ゲートで vmodel_lint 強制 (gate-policy.md update + cli/helix-gate 拡張) | se | 単独 |
| WBS-075-P5-006 | .5.5 | pytest unit test (vmodel_lint 単体) + bats test (helix doctor 結合) | qa | 並列 (test 設計後) |
| WBS-075-P5-007 | .5.6 | 過去 PLAN への影響確認 (lint 走らせて fail PLAN を特定 → Phase 4 retrofit 補完) | pm | 単独 |
| WBS-075-P5-008 | .5.7 | commit + push (vmodel_lint + helix doctor 統合 + ゲート強制) | pm | 単独 |

**vmodel_lint.py の判定 logic**:
```python
def lint_plan(plan_id: str) -> LintResult:
    plan_path = f"docs/plans/{plan_id}-*.md"
    # 1. Read frontmatter from plan_path
    # 2. Check: design_artifact (① 設計) exists?
    # 3. Check: impl_artifact (② 実装) exists?
    # 4. Check: test_design_artifact (③ テスト設計) exists?
    # 5. Check: test_code_artifact (④ テストコード) exists?
    # 6. Check: 各 artifact 内で他 3 artifact への reference 存在?
    # 7. severity: P0 if ① + ② exist but ③ + ④ missing (= 逆ピラミッド)
    return result
```

**受入条件**:
- vmodel_lint.py 単体 pytest 全 PASS
- helix doctor で「[V-model 4 artifact] PLAN-XXX 不足」を表示
- G2 / G3 / G4 で fail-close 動作 (P0 found → block)
- 過去 PLAN の lint 結果を Phase 4 retrofit に feed back

## §3 受入条件

- HELIX_CORE.md / SKILL_MAP.md / CLAUDE.md に 4 artifact 双方向 trace 原則明文化 (Phase 1)
- テンプレートに「4 artifact 双方向 reference」が強制 (Phase 2)
- PLAN-074 が 4 artifact 揃い + 双方向 trace 完備で retrofit 済 (Phase 3)
- 既存 PLAN の 4 artifact 整合性 audit 完了 (Phase 4)
- helix doctor / G2-G4 で 4 artifact lint が fail-close で動作 (Phase 5)

## §4 リスク

| ID | 内容 | 影響 | 対策 |
|---|---|---|---|
| R-01 | 4 artifact retrofit で既存 PLAN が大量変更 | scope 拡大 | Phase 4 で必要最小限に絞る、carry note で段階化 |
| R-02 | 双方向 trace lint で過去 PLAN が大量 fail | 着地遅延 | Phase 4 で retrofit を先行、lint は最後に有効化 |
| R-03 | テスト設計 file 増加で repo 肥大 | 認知負荷 | docs/v2/L4-test-design/ で集約、命名規約統一 |

## §5 依存関係

- 前提: PLAN-074 G4 ready (commit 13de2af) ✅
- PLAN-076 (subagent), PLAN-077 (Sprint Plan) と独立並行可能

## §6 Next Action

1. **今セッション**: Phase 1 完遂 (commit 024499f で完了、訂正反映で本 commit)
2. **次セッション以降**: Phase 2-5 を段階的に

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

- V-model における検証・妥当性確認フェーズ: NASA SW Engineering Handbook の V&V 記述は、要件・設計・実装の各段階で確認活動を行い検証・妥当性検証へ対応づける構造を示している (SWEHB 付録では各段階の検証活動が定義され、Validation を伴う V モデルでの検証計画が示される)。
  - 参照: [NASA SW Engineering Handbook Appendix](https://swehb.nasa.gov/x/MYHxAQ), [SWE Handbook PDF](https://swehb.nasa.gov/download/attachments/76447896/SWE_Handbook_Rel0.1_March2011_RevC.pdf?api=v2&modificationDate=1579537520000&version=1)
- IEEE 系統の V 構造は、システム開発フェーズと対応する検証活動の整理として広く参照され、実務では設計・実装と検証間の対応を前提にレビュー/試験を計画する運用に使われる。
  - 参照: [V-model (software development)](https://en.wikipedia.org/wiki/V-model_%28software_development%29)
- DO-178C では、開発ライフサイクル中の verification / validation を明示し、特に安全性要求が高いソフトウェアにおける厳密な開発・検証工程の設計が求められる。
  - 参照: [DO-178C Introduction](https://www.do178.org/do178_introduction.html), [DO-178C Verification Handbook PDF](https://studylib.net/doc/28106580/do-178c-handbook)

- 要件とテスト成果物の双方向追跡は、ISO 26262 が要求する requirements management の重要な要素として明文化され、要件から実装・検証までの追跡性が要求される。
  - 参照: [Parasoft: ISO 26262 Requirements Traceability](https://www.parasoft.com/learning-center/iso-26262/requirements-traceability/)
- CMMI の要求管理実務では、要件-実装-検証の上下位リンクを維持することが要求され、影響分析とカバレッジ分析を支える基礎として扱われる。
  - 参照: [CMMI v2.0 SP 1.4](https://cmmiinstitute.com/cmmi-model/level-2/requirements-management), [Jama bidirectional traceability guide](https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/bidirectional-traceability)
- IEEE 829 のテスト成果物は各テスト段階で異なる文書を想定し、要件ベースでの追跡を前提とする運用系で参照される。
  - 参照: [Wikipedia: IEEE 829](https://es.wikipedia.org/wiki/IEEE_829), [IEEE 829-2008 PDF (archival reference)](https://www.studylib.net/doc/26178238/ieee-computer-society---ieee-std-829-2008-ieee-standard-f...)

- テスト設計仕様は、ISO/IEC/IEEE 29119-2 のテスト仕様・設計観点で、単体/結合/システム系の設計を検証可能な文書構造として扱い、テストタイプ別に一貫した設計証跡を持つことを示している。
  - 参照: [ISO/IEC/IEEE 29119 PDF](https://standards.ieee.org/wp-content/uploads/import/documents/tocs/ISO_IEC_IEEE_29119.pdf), [ISO/IEC/IEEE 29119-2:2013](https://standards.iteh.ai/catalog/standards/iso/cb1fbb24-b1de-4482-8573-478dd3d19307/iso-iec-ieee-29119-2-2013)

### Revision History

- W5c-9 / 2026-05-19: PLAN-075 に「業界 standard 参照」セクションを追加し、既存セクション不変で「V-model フェーズ / 双方向追跡 / テスト設計仕様標準」観点の参照を追記。
