---
plan_id: PLAN-075
title: "PLAN-075: V-model 4 artifact 双方向 trace framework 強化 (5 Phase)"
status: draft
size: L
drive: be
created: 2026-05-17
revised: 2026-05-17 (4 artifact 解釈に訂正)
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

### Phase 2 — テンプレート + skill 責務再整理 (size: L)

- `cli/templates/` 配下の PLAN テンプレートに「4 artifact 双方向 reference」セクション
- `skills/workflow/design-doc/SKILL.md` を update (① 設計、③ 総合/結合テスト設計への reference 必須)
- `skills/workflow/api-contract/SKILL.md` を update (① 詳細設計、③ 結合テスト設計への reference)
- `skills/common/testing/SKILL.md` を update (③ テスト設計 + ④ テストコードの責務分離)
- `skills/workflow/verification/SKILL.md` を update (4 artifact 双方向 trace 検証)
- 既存 reference 文書 (gate-policy.md / workflow-core.md) の関連箇所 update
- 受入: 全 skill が 4 artifact 原則と整合、テンプレートで双方向 reference を強制化

### Phase 3 — PLAN-074 retrofit (size: M)

**PLAN-074-unit-test-design.md は維持** (③ テスト設計の正しい artifact)。双方向 trace の欠落部分を補完:

- D-API EXT §3.1-3.5 各 endpoint に「**テスト設計ファイル**: PLAN-074-unit-test-design.md §2.X」追記 (① → ③ 参照)
- PLAN-074-unit-test-design.md §2.X 各 module 冒頭に「**対象設計**: D-API EXT §3.X」追記 (③ → ① 参照)
- PLAN-074 §12 (新規) に **総合テスト設計** (E2E 25 シナリオ) を新規 file `PLAN-074-system-test-design.md` で起票 (L2 全体設計対応)
- 結合テスト設計を `PLAN-074-integration-test-design.md` で新規起票 (L3 詳細設計対応、現 integration 27 cases の設計親)
- 単体テスト 63 cases を実装 (WBS-074-L4-008、PLAN-074-unit-test-design.md §5 ファイル構造規約に従う)
- 各 test_*.py docstring に「DoD 検証: PLAN-074-*-design.md U-XXX-N〜M」 (④ → ③ 参照、既存 4 ノード trace に ③ を追加)

### Phase 4 — 他既存 PLAN audit + retrofit (size: M-L)

- PLAN-067〜074 の 4 artifact 揃い + 双方向 trace audit
- 欠落 artifact (③ テスト設計が多くで欠落見込み) を retrofit
- 必要に応じて remedial test design 起票

### Phase 5 — helix doctor / G2-G4 自動 lint 追加 (size: M)

- helix doctor に「4 artifact 揃い check」追加:
  - 各 PLAN で設計 / 実装 / テスト設計 / テストコードの 4 ファイル群が揃っているか
  - 各 artifact から他 artifact への双方向 reference 存在チェック
- G2 / G3 / G4 ゲートで上記 check を強制化 (P0 stop)

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
