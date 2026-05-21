---
doc_id: V2-CONCEPT
title: "【企画書】HELIX V2 構造改革 ─ V-model 強化 + 自動化で開発全容を可視化"
status: draft
created: 2026-05-13
author: "PM (Opus + Sonnet 4.6)"
decision_request: "V1 → V2 構造改革への着手承認"
next_doc: docs/v2/L1-REQUIREMENTS.md (要件定義) → docs/v2/MASTER.md (基本設計)
---

# 【企画書】HELIX V2 構造改革 ─ V-model 強化 + 自動化で開発全容を可視化

## 提案サマリー (一文)

> **V-model 強化を schema で固定し、自動 record で helix.db に蓄積させることで、開発全容を可視化しつつ 3 問題 (バグ・スパゲッティ化・契約漏れ) を構造的に防止する。**

| 項目 | 内容 |
|---|---|
| **採否判断** | V1 incremental 継続 ／ **V2 構造改革に着手** ／ 修正後再提案 |
| **想定投資** | 5-10 セッション + 既存 token 予算内 |
| **完了状態** | V-model 整合度 ≥ 80% / 自動 record 稼働 / 全容 dashboard 可視 / 3 問題検知率向上 |
| **承認後の第一歩** | docs/v2/L1-REQUIREMENTS.md 起票 → G1 ゲート → MASTER.md (L2 基本設計) |

---

## §1 V2 の価値連鎖 (Why → How → Where → 自動化 → 可視化)

```
[WHY]   3 問題     ←  バグ / スパゲッティ化 / 契約漏れ
            ↓ これを防ぐには
[HOW]   V-model 強化  ←  設計 ↔ 検証 pairing schema 強制
            ↓ どこで管理するか
[WHERE] helix.db      ←  4 layer chain で metadata 蓄積
            ↓ 運用上の痛点
        毎回手動 record は無駄
            ↓ 解決
[Base 軸 2] 自動化    ←  auto-record / auto-detect / auto-sync
            ↓ 両軸が揃って初めて引き出される価値
[Emergent value] 開発全容の可視化  ←  dashboard / relation graph / dev-state map
```

V2 = この 5 段の価値連鎖を構造化する全工程。**1 段でも欠ければ V2 の価値は半減**:
- V-model 強化のみ → 空 schema (PLAN-065 の現状)
- 自動化のみ → 何を record するかが決まらず無意味

---

## §2 背景: なぜ今 V2 か

### V1 で限界が露呈

| 痛点 | 実例 | 影響 |
|---|---|---|
| **V-model schema が空運用** | PLAN-065 で table 作成済だが design_review / test_baseline は 0 record | 整合性検証が機能していない |
| **手動 record の無駄** | gate 通過 / test 実行 / contract 変更を毎回手動で record する想定が現実的でない | schema が定義されても活用されない |
| **開発全容が見えない** | 14 detector / 102 SKILL / 18 table / 60+ CLI が散在、関係性が暗黙 | 新規参画コストが高い、運用判断が感覚的 |
| **PLAN 累積による散在** | PLAN-001〜068、incremental patch の重畳、未実装 carry | 集大成のタイミングを過ぎると悪化のみ |
| **FE 弱点の構造的放置** | FE 専用 contract type / detector / command 不在 | UX 品質が人間レビュー依存 |

→ V1 incremental では **2 Base 軸 (V-model 強化 + 自動化) が連結しない**。連結しないと「開発全容可視化」が実現しない。

### V2 を今やる理由

1. **知見蓄積がピーク**: V-model schema (PLAN-065) と 14 detector (PLAN-063) が出揃った今が連結のタイミング
2. **自動化前夜**: V-model schema 完成 → 自動化 → 可視化 の順序が成立する状態
3. **集大成スタンス**: ゼロ設計でなく、散在する V1 capability の formalize で実現可能

---

## §3 V2 の 2 Base 軸 + 基盤 + 派生価値

### Base 軸 1: V-model 強化

設計と検証の対応漏れを schema レベルで強制:

```
左脚 (設計 5 layer)        右脚 (検証 5 layer)
planning            ←→     operational
requirement         ←→     acceptance
architecture        ←→     system_integration
detailed            ←→     integration
functional          ←→     unit
        ↓                          ↑
        └──[L4 code review apex]──┘  (impl + test 両 review)
```

- 縦軸 review: 同脚内 layer 連鎖 (粒度落ち検知)
- 横軸 review: 設計 ↔ 検証 1:1 対応
- 4 layer chain: contract → code → test_design → test_baseline

### Base 軸 2: 自動化

「毎回手動 record は無駄」を解消:

- **auto-record**: PostToolUse hook で file 変更 → helix.db 自動登録
- **auto-detect**: Gate runner / pre-commit で detector 自動実行
- **auto-sync**: SessionStart で skill / code / plan catalog 自動更新

### 付随基盤: helix.db (両軸を支える)

```
helix.db = {
    [V-model 関連 tables]  contract_entries / test_design_entries / design_review / test_baseline
  + [自動化 関連 tables]   invocation_log / detector_runs / routing_decisions / skill_usage
  + [基盤 tables]          code_index / code_edges / plans / managed_products (新規)
} で 3 問題 (バグ / スパゲッティ / 契約漏れ) を schema で防止
```

### 3 軸トライアングル原則

HELIX framework の根本構造は **「成果物 → 実行者 → 記録」** の 3 軸で構成され、
この**順序は固定**である ([ADR-019 §Decision.3](../adr/ADR-019-double-helix-naming-principle.md)):

```
① 成果物 (V-model 工程群)
   ↓  成果物が決まって初めて
② 実行者 (Actor = subagent 14 種 + CLI roles 30 種)
   ↓  実行者が決まって初めて
③ 記録 (DB = 6 db 分離後の event log + state snapshot)
```

| 軸 | 内容 | HELIX 実体 |
|---|---|---|
| ① 成果物 | L1〜L11 工程で生まれる docs / code / test | docs/v2/L1〜L11 doc 群 / cli/lib/*.py / cli/helix-* |
| ② 実行者 | mandatory 10 種 + on-demand 4 種 の subagent + CLI roles 30 種 | .claude/agents/*.md / cli/roles/*.conf |
| ③ 記録 | 6 db の event log + state snapshot | cli/lib/helix_db.py → 6 db 分離後 |

**db 設計は最後段**: ③ 記録 (db 設計) を ① 成果物定義より先に議論・実装することは
3 軸トライアングル違反として reject する。「db 設計から始める」アプローチは
「DB 駆動アンチパターン」に陥る (ADR-019 §Decision.3)。

**3 軸とこれまでの §3 記述の接続**: §3 内の「Base 軸 1 (V-model 強化)」と「Base 軸 2 (自動化)」は
軸 ① 成果物と軸 ② 実行者の中核を成す。「付随基盤: helix.db」が軸 ③ 記録の前身であり、
本 §3 後段の「6 db 分離 + Event Sourcing 概念」でその物理実装を詳述する。

### 二重らせん strand 構造

HELIX という命名は **DNA 二重らせん構造** に由来する
([ADR-019 §Decision.1](../adr/ADR-019-double-helix-naming-principle.md))。
2 本の strand が塩基対 (Actor + detector) で結合し、Sprint 1 周 = 1 回転として
時間軸で自己組織的に進化する構造が HELIX の設計原理と物理実装を統一的に説明する。

```
artifact strand                       record strand
──────────────────────────            ──────────────────────────
L1 要件 / 受入テスト設計               orchestration.db
L2 全体設計 / 総合テスト設計     ◇◇◇  vmodel.db
L3 詳細設計 / 結合テスト設計     塩基対  scrum.db
L4 実装コード / 単体テストコード  ◇◇◇  plan.db
Sprint commit chain                   backend.db
docs/v2 docs hierarchy                frontend.db
──────────────────────────            ──────────────────────────
        ↑ Actor (helix CLI command) + detector が結合を維持 ↑
```

**artifact strand** (左鎖): V-model 工程群が生む成果物の累積
— docs / code / test design / test code が Sprint ごとに積み上がる。

**record strand** (右鎖): CLI 操作・ゲート通過・Agent 呼び出しの event log 累積
— 6 db に分離されたイベントストアとして状態が保持される。

**strand mapping 対応表** ([ADR-019 §Decision.2](../adr/ADR-019-double-helix-naming-principle.md) 要約):

| artifact strand (V-model 成果物累積) | record strand (6 db event log / state) |
|---|---|
| docs/v2/L1-REQUIREMENTS.md (要件 + 受入テスト設計) | orchestration.db — phase / gate / sprint 遷移 event |
| docs/v2/L2-MASTER.md + ADR-* (全体設計 + 総合テスト設計) | vmodel.db — artifact / test_design / review event |
| D-API / D-DB / D-CONTRACT (詳細設計 + 結合テスト設計) | scrum.db — hypothesis / poc / verify / decide event |
| cli/lib/*.py + cli/helix-* (実装コード + 単体テストコード) | plan.db — PLAN doc 進行 state snapshot + change log |
| docs/v2/L4-test-design/*.md + cli/lib/tests/test_*.py | backend.db — be coverage / drive 切替 state |
| .claude/agents/*.md + cli/templates/agents/*.md | frontend.db — visual mock / FE 成果物 state |

**塩基対 (binding)**:
- Actor (PM / TL / SE / PE / QA / PMO / PdM) が `helix` CLI command を実行すると、
  artifact strand の成果物変化と record strand への event write が **同時に発生**する
- detector (lint / audit / advisor) が record strand の anomaly を検知し、
  artifact strand の修正要求として Actor へフィードバックする

**Sprint = らせん 1 回転**: Sprint N で両 strand がそれぞれ延伸し、
Sprint N+1 に向けてらせんが 1 段積まれる。V2 完了状態 = らせんが L1-L11 + Run (L9-L11)
を 1 周したことを意味する。

**例外**: Reverse 機能 (R0-R4 + RGC) は record strand を持たない。
既存 code の逆引きであり新規 event を生成しないため、orchestration event log への
write は発生しない (ADR-018 §Decision.1 注記)。

### 6 db 分離 + Event Sourcing 概念

HELIX V2 の③ 記録フェーズとして、単一 `helix.db` を 6 個の SQLite file に物理分離する
([ADR-018 §Decision.1](../adr/ADR-018-db-separation-and-event-sourcing.md))。
各 db は独立した entity ownership を持ち、cross-db FK は禁止、
アプリケーション層からの ATTACH も禁止する (migration script + projector 内部のみ許可)。

**6 db を一律に event-sourced にするのではなく**、audit / temporal / event ordering /
write 頻度 / retention / replay SLO の **6 軸判定**でハイブリッド構成を採用する
([ADR-018 §Decision.2](../adr/ADR-018-db-separation-and-event-sourcing.md)):

> **企画書レベルの抜粋表**: 以下の表は主要 5 軸 + 採用方式に絞った要約。replay SLO 列は冗長性回避のため省略 (event-sourced = < 5min / hybrid = < 30min / state-store = n/a)。完全な 6 軸 matrix は ADR-018 §Decision.2 を参照。

| db | audit | temporal | event ordering | write 頻度 | retention | 採用方式 |
|---|---|---|---|---|---|---|
| orchestration | ◎ 必須 | ◎ 必須 | ◎ 必須 | 高 | 長期 (1y+) | **event-sourced** |
| vmodel | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | **event-sourced** |
| scrum | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | **event-sourced** |
| plan | ◎ 必須 | △ 部分 | ○ 推奨 | 低 | 長期 (1y+) | **hybrid (state snapshot + change log)** |
| backend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | **state-store** |
| frontend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | **state-store** |

採用決定ルール: audit + temporal + event ordering の 3 軸が全て ◎ 必須 → event-sourced。
1 軸でも × → state-store。その間 → hybrid。

**projector 境界** ([ADR-018 §Decision.3](../adr/ADR-018-db-separation-and-event-sourcing.md)):
event-sourced 3 db (orchestration / vmodel / scrum) には projector を配置し、
event log から read model を構築する。同期許可は **3 件のみ**
(phase projector / gate projector / agent_slot projector、いずれも timeout 200ms)。
それ以外は async enqueue。lag > 1000 event で **Phase 4.B 以降** に G2/G3/G4 gate を block
(Phase 4.B 完成まで本 fail-close は不適用)。

**migration gate 6 段階** ([ADR-018 §Decision.5](../adr/ADR-018-db-separation-and-event-sourcing.md)):
v30 (単一 helix.db) → 6 db 分離は Strangler Fig + dual-write + compatibility adapter で段階移行:

1. **dual-write start** — orchestration_events + projection_state 追加、既存 v30 破壊なし (自動)
2. **dual-write mismatch gate** — 旧 db と新 event log の divergence 0 件 (10000 write 連続) (自動)
3. **shadow replay 検証** — 過去 1000 event replay → derived state が byte-level 一致 (自動)
4. **projector lag stabilization** — lag < 100 event 連続 24h (PM 監視)
5. **cutover** — 4 ゲート全 PASS + PO 承認 (人間承認必須)
6. **rollback point** — cutover 後 7d 以内の重大 anomaly で切り戻し可能 (人間承認必須)

compatibility adapter (compatibility_adapter.py) が既存 11 file (lib 8 + top-level CLI 3) を
API 互換 100% で 6 db 経路へ adapt する (Phase 4.A)。

**補足 — backend / frontend の再判定**: backend.db / frontend.db は現時点で state-store だが、
write 頻度低下・audit 要件変化・cross-db 参照増加 等のトリガで将来 event-sourced への
昇格を検討する (ADR-018 §Decision.4、6 ヶ月毎に PM + TL で見直し)。

### Emergent value: 開発全容の可視化

両軸 (V-model schema + 自動 record) が揃って初めて実現:

- **dev-state dashboard**: 全 PLAN の 4 layer chain 整合度 / 14 detector verdict / role 委譲履歴
- **relation graph (axis-10)**: detector × code × contract × hook の全関係 (mermaid)
- **session-start view**: セッション開始時に全 state が 1 秒以内に表示

---

## §4 期待効果

### 定量

| 指標 | 現状 | V2 完了時目標 |
|---|---|---|
| V-model 整合度 (4 layer chain 埋まる率) | 0% (空 record) | ≥ 80% |
| 手動 record 操作数 | 都度手動 | 自動化により 90% 削減 |
| 開発全容把握所要時間 | 数時間 (新規参画時) | 1 セッション開始時 1 秒以内 (dashboard) |
| 3 問題検知率 | 部分的 (G ゲート単発) | 構造的 (自動 record × detector 自動 run) |
| FE 専用 capability | 0 | 5+ contract type / 5+ detector / 5+ command |

### 定性

- **AI エージェントが状況を即把握**: dashboard を参照 → 即判断
- **「テスト全 PASS」がざるにならない**: regression baseline の自動更新 + flaky 自動判定
- **設計デグレ自動検知**: PLAN finalize 後の暗黙改変を axis-08 + design_review で検出
- **HELIX を任意 Product に転用可能**: 段 1/段 2 分離 + managed_products schema
- **dogfood 成立**: HELIX 自身が V2 後 HELIX で開発される

---

## §5 V2 スコープ

### Phase 構成 (10 Phase)

| Phase | 内容 | 軸 |
|---|---|---|
| **A** | 集大成 audit (V1 capability 棚卸し + 5 層 × 3 問題 mapping + FE 弱点炙り出し) | 両軸前段 |
| **B** | 上流 architecture (V-model 多軸 + 自動化 architecture + 可視化 design) | 両軸 |
| **C** | helix.db v21 schema 拡張 (drive 列 / er_diagrams / process_maps / managed_products / agent_registry) | 基盤 |
| **D** | **V-model 実装** (4 layer chain / drive 別 semantic / pair-check 拡張) | **Base 軸 1** |
| **E** | **自動化実装** (PostToolUse auto-record / Gate auto-detect / SessionStart auto-sync) | **Base 軸 2** |
| **F** | **全容可視化** (dashboard 強化 / relation graph / dev-state report) | **Emergent value** |
| G | FE 弱点強化 (V-model variant + FE 自動化) | 軸 1+2 派生 |
| H | Agent Transformation 整理 (段 2 内集約) | 派生 |
| I | Legacy Import (PLAN-001〜068 carry の V2 取り込み) | 派生 |
| J | dogfood / 運用安定化 | 検証 |
| **K** | **V5 framework 統合** (V5 19要素 3層構造 + PLAN ⊃ ADR レイヤー併存 + 自動走行 5-layer + ADR Decision Graph + GenAI semconv 観測性、§10 参照) | **拡張 framework** |

### 順序の論理

```
V-model schema 完成 (Phase D)
  ↓ 「何を record するか」確定
自動化 (Phase E) 起動
  ↓ 「いつ record するか」機械化
record が蓄積
  ↓ 「貯まったものをどう見せるか」
全容可視化 (Phase F) 機能
```

→ user 原則「機能完成 → 自動化」を保持。V-model schema (機能) 完成後に自動化、その後に可視化。

### 工程転換 (V-model スプリント化)

Phase D の中核として **「設計と対応テスト設計を同一スプリントでペア凍結」** 構造を導入する。詳細は [L1-REQUIREMENTS.md §3.6](./L1-REQUIREMENTS.md#36-工程転換-v-model-スプリント化phase-d--base-軸-1-中核) を参照。

| 工程 | Before (V1) | After (V2) |
|---|---|---|
| 基本設計スプリント | L2 単独 (テスト設計は L3 後追い) | 基本設計 ∥ システム統合テスト設計 (ペア凍結) |
| 詳細設計スプリント | L3 設計 + テスト設計まとめて | 詳細設計 ∥ 結合テスト設計 (ペア凍結) |
| 機能設計スプリント | (なし、L3/L4 に埋没) | 機能設計 ∥ 単体テスト設計 (ペア凍結) |
| 実装スプリント | L4 マイクロスプリント (.1〜.5) | 実装 ∥ テスト実行 ∥ レビュー (三位一体) |

設計判断 (TL 助言反映):
- **粒度は PLAN 規模 (S/M/L) で可変** (固定 4 sprint 強制は不採用)
- **drive 分岐は track 並列** (fullstack は同一上位 sprint 内で BE ∥ FE ∥ contract 並走)
- **G3.5 はサブゲートから始動** (`G3.functional_freeze`、size=L / drive in (fe/fullstack/db) で必須)
- **FE mock promotion は append-only** (row 更新禁止、G2 evidence 保全)

### 含まないもの

- ⏸ CI/CD integration (V3 候補)
- ⏸ リモート同期 / multi-tenancy (V3 候補)
- ⏸ FE UI dashboard 強化 (本 V2 では CLI dashboard まで)

---

## §6 投資・リスク

### 投資

| 項目 | 想定 |
|---|---|
| 期間 | 5-10 セッション (Phase A-J) |
| 工数 | PM は採否判断と review のみ、実装は Codex/Opus に委譲 |
| Token 予算 | 現状予算内で完結 (PMO 委譲で PM 単独運用より効率向上) |
| 既存機能停止 | なし (V1 機能は V2 完了まで動作維持) |

### 主要リスク

| リスク | 影響 | 対策 |
|---|---|---|
| V1 互換性破壊 | 大 | 段階的 migration / helix.db v20 → v21 後方互換 |
| 自動化の暴走 | 中 | 80% / 100% guard / opt-out flag / dry-run mode |
| dashboard 性能劣化 | 中 | 集計 cache / incremental update |
| Codex token 上限 | 中 | impl-sonnet 経路 / PMO 委譲分散 |
| schema 設計判断ミス | 中 | yaml 外部化で吸収 / enum 固定 |

---

## §7 採否判断基準

### approve の条件 (1 つで approve 可)

- (a) §1 価値連鎖の論理に納得
- (b) §2 痛点を自プロジェクトで感じている
- (c) §4 期待効果のいずれかが投資 (5-10 セッション) に見合う
- (d) V1 incremental では §1 連鎖が完成しないと判断

### needs revision の場合

- §N に対する追加・修正点を指摘

### reject の場合

- V1 incremental 継続 / 別アプローチ検討

---

## §8 次のアクション

### approve 後 (即時)

1. `docs/v2/L1-REQUIREMENTS.md` 起票 (要件定義書)
   - BR/FR/NFR を 2 Base 軸 + Emergent value で構造化
   - G1 要件完了ゲート通過判定
2. G1 通過後: `docs/v2/MASTER.md` 起票 (L2 基本設計)
3. Phase A audit 着手

### 短期

- Phase A-C 完了 → Phase D (V-model 実装) 着手

### 中期

- Phase D-F 完了 → V2 core 機能完成
- Phase G-J 完了 → V2 完成

---

## §9 補足: V1 既存資産との関係

V2 は **ゼロ設計ではなく V1 資産の formalize + 連結**:

| V1 資産 | V2 での扱い |
|---|---|
| V-model schema (PLAN-065 W-2、helix.db v20) | Phase D で drive 拡張 + 4 layer chain 完備 |
| 14 detector (PLAN-063) | Phase E で auto-detect 連動、Phase F で dashboard 集約 |
| 契約 extractor (PLAN-063 W-2pre) | Phase E で PostToolUse 連動 → auto-record |
| handover protocol | Phase H で statemap 化 |
| skill 推挙 + recommender | Phase E SessionStart で auto-sync |
| Reverse / Scrum mode | Phase D で V-model 統合 |
| Agent Transformation 散在 | Phase H で集約整理 |
| Automation-SEO (段 1 product 参考) | Phase D-H の参考実装 |
| **PLAN-084 (helix.db 6 分離 + Event Sourcing)** | **Phase K Layer B の前段 (DB 分離 + projector 基盤)** |
| **PLAN-087〜090 (Web 検索ガード / TodoWrite × agent slot / gate fail-close / continueOnBlock)** | **Phase K の PLAN ⊃ ADR 範例 (ADR-021〜024 と双方向 trace)** |
| **PLAN-091〜099 (V5 framework 本体 / 自動登録 / drift 検出 / PoC=Scrum×Reverse / GitHub / 抽象化層 / recovery / 自動走行 5-layer)** | **Phase K の中核実装 (Layer A→B→C 順)** |
| **PLAN-100 (既存 retrofit + V2 全面見直し)** | **Phase K と Phase I (Legacy Import) の橋渡し、PLAN-091〜099 完遂後の後段 retrofit** |

---

## §10 V5 framework 統合 (2026-05-22 Phase K として追加)

### §10.1 V5 framework 19 要素マッピング

V5 framework は 3 層構造で 19 要素を統合する (Layer A → B → C 依存順)。

| Layer | 要素 (19) | 概要 |
|---|---|---|
| **A** 工程ルール | 1-7, 11-18 | PLAN self-contained / matrix / 種別 / fail-close / generates / dependencies / agent_slots / ADR snapshot / template embed / V-model TDD / PoC=Scrum×Reverse / GitHub 統合 / recovery / 自動走行 5-layer |
| **B** helix.db 型 | 8, 9, 10 | DB 受け側 / drift 検出 / 進捗 trace |
| **C** 連携自動化 | 8 (hook 本体), 18 | PostToolUse / SessionStart / statusLine / PreCompact / 5-layer hook |

19 番目要素 (#22 ADR Decision Graph) は 2026-05-22 readiness report で追加採用 (P0、Phase 4 同時実装)。PLAN-101 + ADR-033 で実装。

### §10.2 3 層依存順序 (Layer A → B → C、着手必須順)

```
[Layer A] 工程・ドキュメント運用ルール整備 ← V2 企画書反映、Layer B/C の前提
  V5 要素 1-7 (PLAN self-contained / matrix / 種別 / fail-close / generates / dependencies / agent_slots)
  V5 要素 11-17 (ADR snapshot / template embed / V-model TDD / PoC / GitHub / helix_improvement / recovery)
       ↓
[Layer B] helix.db 型ハーネス ← Layer A の実体化
  V5 要素 8 (DB 受け側) / 9 (drift 検出) / 10 (進捗 trace)
  単一実行正本決定 (task_queue / TodoWrite / helix job / handover 競合解消)
       ↓
[Layer C] 連携自動化ハーネス ← Layer A/B を hook で動かす
  V5 要素 8 (hook 本体) / 18 (自動走行 framework 5-layer)
  PoC C 案 (Layer 4+5 = SessionStart + heartbeat) のみ並行可、本実装は A/B 確定後
```

工程ルール (A) が確定しないと DB schema (B) は設計できず、B が動かないと hook (C) が連動しない。並行可能なのは Layer C の PoC (Layer 4+5) のみ。本実装は A/B 確定後。

### §10.3 PLAN ⊃ ADR レイヤー併存 範例

PLAN は L1〜L4 を内包する implementation tree、ADR は PLAN tree 内 L2 大局判断の snapshot (任意・併設):

| PLAN | tree 範囲 | ADR snapshot | L2 大局判断 |
|---|---|---|---|
| PLAN-084 | L1〜L4 (helix.db 6 分離 + Event Sourcing) | ADR-018 / ADR-019 | 6 分離 + 命名原則 + 3 軸トライアングル |
| PLAN-087 | L1〜L4 (設計 doc Web 検索ガード) | ADR-021 | Web 検索 fail-close 採用 |
| PLAN-088 | L1〜L4 (TodoWrite × agent slot) | ADR-022 | framework 採用 |
| PLAN-089 | L1〜L4 (gate fail-close 段階導入) | ADR-023 | advisory → fail-close 段階遷移 |
| PLAN-090 | L1〜L4 (continueOnBlock + active guidance) | ADR-024 | 外部新仕様採用 |

「ADR 先 / PLAN 後」順序ではなく、同 trunk 内併存 (L2-MASTER §0 line 36 範例)。`helix doctor check_plan_adr_snapshot` (新設予定) で PLAN tree 内 L2 大局判断あり + ADR snapshot 不在を fail-close 化。

### §10.4 V5 観測性 (GenAI Semantic Conventions 採用、OpenTelemetry 準拠)

OpenTelemetry GenAI Semantic Conventions (2026-02 client spans 安定化) を agent observability の正本とする:

- **span 名 / attribute key / metric / event shape** は OTel GenAI 準拠 ([opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/))
- agent invocation / tool call / retrieval を **child span** として記録 (推論 chain の完全 trace)
- token usage / latency / error rate を **metric** 化
- HELIX 独自 wide events として helix.db に append-only 蓄積 (event_envelope + audit_hash で tampering 防止)
- PII / secret は redaction layer 経由 (Datadog / Honeycomb / New Relic 等の業界 standard 踏襲)

major vendor (Datadog / Honeycomb / New Relic) + framework (LangChain / CrewAI / AutoGen / AG2) が OTel-compliant span を native emit、HELIX は SQLite-based wide events で同等の audit を local 完結。

### §10.5 V5 差別化軸 (一般 AI dev tool / Cursor / Copilot 対比)

| 項目 | HELIX V5 | 一般 AI dev tool |
|---|---|---|
| **V-model traceability** | 4 artifact 双方向 trace (設計 ↔ 実装 ↔ テスト設計 ↔ テストコード) を frontmatter + helix.db で機械強制 | コード生成中心、設計と test の trace 弱い |
| **helix.db audit** | append-only event 蓄積、reciprocal dependency / drift 検出 / 進捗 trace を SQLite で sealed | 履歴は chat log のみ、structural audit なし |
| **PLAN ⊃ ADR** | implementation tree (L1〜L4) + L2 snapshot (任意併設、`helix doctor` で fail-close 化) | spec / decision 分離なし |
| **自動走行 5-layer** | PostToolUse / SessionStart / statusLine / PreCompact / heartbeat で context 枯渇 + carry 放置 + idle 三課題同時解決 | context 管理は手動、carry 放置可 |
| **Event Sourcing + projector** | append-only event + upcaster + read model projection で schema evolution 安全化 (MADR 2.1.2 + 業界 Event Sourcing pattern) | state mutation 中心 |
| **gate fail-close 段階導入** | advisory → fail-close 段階遷移で破壊的導入を回避 (ADR-023) | hard fail のみ or gate なし |

Event Sourcing upcasting pattern は domain 標準 (Artium / Microsoft Azure / quintans 等) を採用。ADR format は MADR 2.1.2 ([adr.github.io/madr/](https://adr.github.io/madr/)) 準拠。

### §10.6 status review 遷移フロー (PLAN 規約 v5)

PLAN status は frontmatter `status` を正本に、`draft → finalized → completed` の 3 状態で遷移する。各遷移条件:

- `draft` → `finalized`: tl-advisor adversarial review PASS + plan_validator (`helix plan lint --v5`) PASS + ADR snapshot 併設 (L2 大局判断があれば)
- `finalized` → `completed`: Sprint Exit 条件全充足 + handover Next Action 消化 + 全 gate PASS + V-model 4 artifact 揃い (`helix doctor` check)
- **逆遷移は禁止** (degrade 防止)。誤遷移は recovery plan kind (V5 要素 17) で別 PLAN 起票して trace。

frontmatter `status` 更新時、PostToolUse hook (V5 要素 8) が helix.db `plan_registry` に自動同期し、`helix doctor check_plan_status_drift` で本文との drift を fail-close 化。

---

**判断待ち**: 本企画書 (V2 価値連鎖 + 2 Base 軸 + 基盤 + Emergent value + V5 framework 統合) を読み、§7 採否判断基準に照らして判断ください。approve なら即 L1-REQUIREMENTS.md 起票へ。

| 採否 | [ ] approve / [ ] needs revision / [ ] reject |
|---|---|
| 判断根拠 | ____________ |
| 承認日 | 2026-05-__ |
