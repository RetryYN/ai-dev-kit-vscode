---
plan_id: PLAN-084
title: "PLAN-084: helix.db 6 分離 + Event Sourcing + projector (V2 構築 ③ データベース管理フェーズ本体)"
status: draft
size: L
drive: be
created: 2026-05-17
revised: 2026-05-17 (tl-advisor adversarial check Round 1 反映)
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-068 (V-model 強化 = db 分離アーキテクチャの基盤工事、単一 helix.db 前駆体)
  - PLAN-070 (L3 schema and contract design、D-DB EXT 既存基盤)
  - PLAN-075 (V-model 4 artifact 双方向 trace framework)
  - PLAN-078 (agent_slots v28、② 実行ハーネスの schema 基盤)
  - PLAN-083 (Harness 自動統合、② 実行ハーネス完成)
related_memories:
  - project_2026_05_17_v2_5stage_construction_order
  - project_2026_05_15_helix_triangle_principle
  - project_2026_05_15_helix_spiral_final_form
  - project_2026_05_15_vmodel_as_db_separation_foundation
  - project_2026_05_15_vmodel_real_phase_start
  - feedback_v2_basic_design_first_not_plan_level
acceptance:
  - 6 db (orchestration / vmodel / scrum / plan / backend / frontend) の責務境界 + entity ownership + cross-db FK 禁止/許可 + event envelope + correlation_id 規約が L1 要件 + L2 ADR で確定
  - Event Sourcing 採用範囲が 6 軸判定表 (audit trail / temporal query / event ordering / write 頻度 / retention / replay SLO) で L1 確定、plan.db hybrid の具体形 (state snapshot + change log) が明示
  - projector の責務分離 + 同期許可リスト + timeout + 失敗時 fallback + lag 境界 (警告/fail-close) が L1 + L2 で確定
  - migration 戦略に compatibility adapter + shadow replay 検証 + dual-write mismatch gate + rollback point + cutover 条件が含まれ、Phase 3 受入条件で明示
  - 3 軸トライアングル + 二重らせんが ADR-019 で正式記述、frontend/backend = state-store の再判定条件が ADR-018 に明記
  - L4 完遂で event-sourced 3 db (orchestration/vmodel/scrum) が dual-write 稼働、projector 1+ 稼働、shadow replay PASS、既存 ② 実行ハーネス機能破壊なし
---

# PLAN-084: helix.db 6 分離 + Event Sourcing + projector

## 1. 背景

### 1.1 V2 構築 5 段階順序における位置付け

memory [[project_2026_05_17_v2_5stage_construction_order]] (2026-05-17 確立) で、V2 構築は 5 段階順序であることを確立した:

```
① 工程やルール整備   ✅ 完成 (PLAN-075/076/077)
② 実行ハーネス整備   ✅ 完成 (PLAN-078〜083)
③ データベース管理   ❌ 未着手 ← 本 PLAN-084
④ 問題発見配備      ❌ ③ 完成後の別枠フェーズ
⑤ 自動化システム化   ❌ 全段階貫通配備
```

PLAN-084 は ③ データベース管理フェーズ本体に該当する。①② が完成しており、③ を完遂させないと ④ db detector の本格配備 (Event Sourcing + projector 前提) が成立しない。

### 1.2 既存 docs/v2 における gap

pmo-project-explorer 調査 (本セッション 2026-05-17) で、以下が判明した:

| 概念 | 正式 docs | memory | gap |
|---|---|---|---|
| 6 db 分離 | 不在 | あり | 全て新規 L1 要件化 |
| Event Sourcing | **L2-MASTER.md:36 で「含めない」と明示除外** | あり (採用方針) | **除外見直し**が必要 |
| projector | L2-MASTER.md:36 で除外 | あり | 新規 L1 要件化 |
| detector | CONCEPT.md / L1 / L2 に既存 (14 axis) | あり | **既存 14 axis を 6 db 対応へ拡張** |
| 3 軸トライアングル | 不在 | あり (5/15 確立) | ADR 起票 |
| 二重らせん | 不在 | あり (5/15 確立) | ADR 起票 |
| v30 → 6 db migration | 不在 | 言及あり | 全て新規 L2 設計 |

### 1.3 PLAN-068 (V-model 強化) との関係

memory [[project_2026_05_15_vmodel_as_db_separation_foundation]] で「PLAN-068 = 単一 helix.db 前駆体、PLAN-069 = db 分離 + V-model v2 収束」と整理されていたが、PLAN-069 番号は別タスク (G3 entry blocker resolution) で消費済 (memory [[feedback_opus_plan_number_collision_check]] 該当)。本 PLAN-084 がその「db 分離 + V-model v2 収束」を正式に引き継ぐ。

### 1.4 ユーザー指摘 (5 段階順序の根拠)

> 「工程やルール整備⇒実行ハーネス整備⇒データベース管理⇒問題発見システム配備⇒自動化システム化じゃないの？」(2026-05-17)
>
> 「実装していくうえで② 実行ハーネス整備の問題検出は適時対応。データベースからの問題発見は別枠でしょ。」(2026-05-17)

→ ② harness の検出系 (vmodel_lint / subagent_audit / sprint_lint) は ② の適時対応、④ db detector は ③ 完成後の別レイヤーであることを確認。PLAN-084 は ③ を確立する。

## 2. 目的

helix.db を 6 db に物理分離し、event-sourced 3 db + hybrid 1 db + state-store 2 db のハイブリッド構成で **record strand (二重らせんの片側)** を物理実装する。projector が event log から read model を構築し、detector が record strand の anomaly を検知する基盤を整える。

### 2.1 確定すべき L1 要件項目 (Gap G-01〜G-09、tl-advisor Round 1 反映)

| # | Gap | L1 要件化内容 |
|---|---|---|
| G-01 | 6 db 分離 + entity ownership | 6 db 名 / 責務境界 / **entity owner / canonical source / cross-db FK 禁止 (許可は read model 経由参照のみ) / event envelope + correlation_id 規約** |
| G-02 | Event Sourcing 採用範囲 (6 軸判定) | 全 db 一律でなくハイブリッド、**6 軸 (audit trail / temporal query / event ordering / write 頻度 / retention / replay SLO) で判定、plan.db hybrid の具体形 = state snapshot + change log** を明示 |
| G-03 | projector / observer pattern | writer API 禁止 / cross-projection join 禁止 / replay idempotency 必須 / **同期許可リスト (例: phase.yaml 更新) + timeout + 失敗時 fallback + lag 警告境界 100 event / lag fail-close 境界 1000 event** |
| G-04 | detector の 6 db 対応拡張 | 既存 14 axis を 6 db each に割当、record strand anomaly 系を追加 (本 PLAN は責務分離のみ、本格配備は PLAN-085 想定) |
| G-05 | 3 軸閉ループ (成果物 → 記録 → 実行者 feedback) | record strand から detector → 実行者 feedback channel を要件化 |
| G-06 | v30 → 6 db migration 戦略 | Strangler Fig + dual-write + **compatibility adapter + shadow replay 検証 + dual-write mismatch gate + rollback point + cutover 条件** |
| G-07 | Reverse (db なし機能) 正式 L1 要件化 | Reverse は record strand を持たない例外として明示 |
| G-08 | 二重らせん命名原則の ADR | HELIX 命名 = DNA 二重らせん由来を ADR-019 で正式化 |
| **G-09** | **frontend/backend state-store の再判定条件** | **将来 event 化の再判定条件 (write 頻度・audit 要件の変化トリガ) を ADR-018 に明記** |

## 3. スコープ

### 3.1 in-scope (L サイズ想定)

#### Phase 1: L1 要件定義 (本 PLAN doc + L1 doc 拡張)
- 本 PLAN-084 doc 完成 (要件項目 G-01〜G-09 を確定)
- `docs/v2/L1-REQUIREMENTS.md` 拡張: §3.9 章追加 (G-01〜G-09 を FR/NFR/AC として記述、6 軸判定表 + entity ownership 表 + projector 境界表 + migration ゲート表 を含む)

#### Phase 2: L2 基本設計 (CONCEPT.md 更新 + ADR 起票)
- `docs/v2/CONCEPT.md` 更新: §3-axis-triangle / §double-helix-strand / §6-db-separation 章追加、L2-MASTER.md:36 「Event Sourcing 含めない」明示除外を **「採用 (6 軸判定により条件付き)」に修正**
- `docs/adr/ADR-018-db-separation-and-event-sourcing.md` 起票 (6 db 責務境界 + entity ownership + cross-db FK 規約 + Event Sourcing 採用範囲 6 軸判定 + projector 責務 + detector 責務 + **frontend/backend 再判定条件**)
- `docs/adr/ADR-019-double-helix-naming-principle.md` 起票 (3 軸 + 二重らせん命名原則の正式化)
- L2-MASTER.md 該当箇所修正 (除外宣言の見直し)

#### Phase 3: L3 詳細設計 (D-DB EXT + D-API EXT + migration plan)
- `docs/v2/L3-detailed-design/D-DB-SEPARATION.md` 起票 (6 db 各 schema 設計 + event log table + projection_state table + event envelope + correlation_id)
- `docs/v2/L3-detailed-design/D-API-EVENT-SOURCING.md` 起票 (event append API + projector read API + detector subscribe API + 同期許可リスト)
- `docs/v2/L3-detailed-design/D-DB-MIGRATION.md` 起票 (Strangler Fig + dual-write 手順 + **compatibility adapter 設計** + **shadow replay 検証手順** + **dual-write mismatch gate 仕様** + **rollback point 定義** + **cutover 条件** + v30 → 6 db 段階移行)
- `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` + `PLAN-084-integration-test-design.md` 起票

#### Phase 4: L4 実装 (migration + dual-write + projector + cutover)
- `cli/lib/event_log.py` 新規 (event append + replay + envelope + correlation_id)
- `cli/lib/projector.py` 新規 (event → read model + idempotency + lag 監視)
- `cli/lib/compatibility_adapter.py` 新規 (既存 agent_slots.py / harness_monitor.py 等の `_write_connection(None)` 前提を 6 db 経路へ adapt)
- `cli/lib/helix_db_orchestration.py` 新規 (orchestration.db 専用接続)
- `cli/lib/helix_db_vmodel.py` 新規 (vmodel.db 専用接続)
- `cli/lib/helix_db_scrum.py` 新規 (scrum.db 専用接続)
- `cli/lib/helix_db.py` 拡張: ATTACH DATABASE で cross-db 整合性維持
- migration script v30 → v31 (orchestration_events + projection_state + event_envelope table 追加、dual-write 開始 + mismatch gate 配備)
- shadow replay 検証 script + dual-write mismatch 検出 script
- 既存 phase.yaml は併存期間維持 (Phase 4 末で projector derived state へ cutover 判断、判断 ADR-020 で記録)

### 3.2 out-of-scope

- **④ db detector の本格配備** (= PLAN-085 想定)。本 PLAN は detector の責務分離を L1/L2 で確定するのみ
- **⑤ 自動化システム化** (= 別 PLAN、全段階貫通配備)
- **② advisory lint fail-close 化** (vmodel_lint / subagent_audit / sprint_lint)。本 PLAN scope から **明示分離** (tl-advisor important #5)、② 適時対応 carry として handover で別管理
- **frontend.db / backend.db の event-sourced 化** (= 別 PLAN、再判定条件を G-09 で ADR 化)
- **plan.db の完全 event-sourced 化** (= hybrid 採用、本 PLAN ではここまで)
- **HTTP endpoint 層の event subscribe API** (= L6 統合検証 or 別 PLAN)

## 4. Phase 構成 (4 Phase 想定、L サイズ複数セッション、tl-advisor Round 1 反映)

| Phase | スコープ | size | 担当 | 期間想定 (修正) |
|---|---|---|---|---|
| Phase 1 | L1 要件定義 (本 PLAN doc + L1 doc §3.9 拡張) | M | Opus + tl-advisor adversarial check | **1-2 セッション** |
| Phase 2 | L2 基本設計 (CONCEPT.md + ADR-018 + ADR-019 + L2-MASTER 修正) | M-L | Opus + tl-advisor + pmo-tech-docs | **2-3 セッション** (tl-advisor #5: L1-L2 だけで 2-3 セッション必要) |
| Phase 3 | L3 詳細設計 (D-DB-SEPARATION + D-API-EVENT-SOURCING + D-DB-MIGRATION + compatibility adapter 設計 + shadow replay 設計 + test design) | M-L | Codex se + tl-advisor | **2-3 セッション** |
| Phase 4 | L4 実装 (event_log + projector + compatibility adapter + 6 db 分離 + migration + dual-write + shadow replay + cutover) | L | Codex se + pg + Opus 統合 | **3-4 セッション** |

合計: **8-12 セッション想定** (was 5-8、L サイズ、tl-advisor Round 1 反映で +3-4)。

## 4.5 V-model 4 artifact (PLAN-075 準拠)

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L2 基本設計 + L3 詳細設計 | docs/v2/CONCEPT.md (§3-axis + §double-helix + §6-db-separation) + docs/adr/ADR-018 + docs/adr/ADR-019 + docs/v2/L3-detailed-design/D-DB-SEPARATION.md + D-API-EVENT-SOURCING.md + D-DB-MIGRATION.md |
| ② 実装コード | L4 実装 | cli/lib/event_log.py + projector.py + compatibility_adapter.py + helix_db_orchestration.py + helix_db_vmodel.py + helix_db_scrum.py + cli/lib/helix_db.py (ATTACH) + migration v30 → v31 + shadow replay script |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-084-unit-test-design.md + PLAN-084-integration-test-design.md (Phase 3 で起票) |
| ④ テストコード | L4 実装 | cli/lib/tests/test_event_log_unit.py + test_event_log_integration.py + test_projector_unit.py + test_projector_integration.py + test_compatibility_adapter.py + test_db_separation_migration.py + test_shadow_replay.py + bats: tests/db-separation-cutover.bats + tests/dual-write-mismatch-gate.bats |

## 5. 受入条件

- frontmatter `acceptance` 6 項目すべて達成
- Phase 1 完遂: 本 PLAN doc 完成 + `docs/v2/L1-REQUIREMENTS.md` に §3.9 章追加 (G-01〜G-09 を FR/NFR/AC として記述、6 軸判定表 + entity ownership 表 + projector 境界表 + migration ゲート表 を含む)
- Phase 2 完遂: CONCEPT.md / L2-MASTER.md 修正 + ADR-018 + ADR-019 起票 + tl-advisor adversarial check PASS
- Phase 3 完遂: D-DB-SEPARATION + D-API-EVENT-SOURCING + D-DB-MIGRATION (compatibility adapter / shadow replay / dual-write mismatch gate / rollback / cutover 条件を含む) + 単体/結合 test 設計起票
- Phase 4 完遂: event-sourced 3 db (orchestration/vmodel/scrum) dual-write 稼働、projector 1+ 稼働 (lag < 100 event)、shadow replay PASS、dual-write mismatch gate 0 件、migration v30 → v31 PASS、既存 ② 実行ハーネス機能 (PLAN-078〜083) 破壊なし
- pytest + bats 全 PASS
- helix doctor 0 fail

## 6. リスク (tl-advisor Round 1 反映で R-08〜R-10 追加)

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | migration 中断時の cross-db 整合性 | helix.db v30 と 6 db の二重真実 | **Strangler Fig + dual-write + mismatch gate (Phase 3 受入条件)** + rollback point 明示 + cutover は projector derived state が安定 (lag < 100 event) してから |
| R-02 | projector lag による read 一貫性低下 | UI / CLI が古い state を表示 | **lag 警告境界 100 event / fail-close 境界 1000 event** + last_processed_event_id 監視 (PLAN-085 で detector 実装) |
| R-03 | SQLite ATTACH DATABASE の性能劣化 | cross-db query が遅い | event-sourced 3 db に限定、backend/frontend は state-store 単独で ATTACH 不要、性能 NFR < 100ms (L1) |
| R-04 | phase.yaml と projector derived state の二重真実 | Phase 4 cutover 判断ミス | Phase 4 末で「併存期間維持」または「phase.yaml 廃止」を ADR-020 で記録 |
| R-05 | ② 実行ハーネス (agent_slots / harness_monitor) の破壊 | PLAN-078〜083 機能停止 | **compatibility adapter (cli/lib/compatibility_adapter.py)** で既存 `_write_connection(None)` 前提を 6 db 経路へ adapt、API 互換 100% 維持 |
| R-06 | Event Sourcing 採用範囲の判断ミス (plan.db を hybrid 採用) | 中期的に re-architecture コスト | **L1 で 6 軸判定表を確定** (audit / temporal / event ordering / write 頻度 / retention / replay SLO)、plan.db hybrid 具体形 = state snapshot + change log を ADR-018 で明示 |
| R-07 | L 規模 PLAN の途中 cancel リスク | framework 中断で advisory 状態が長期化 | Phase 1-2 (L1-L2 設計) を確実に完遂してから Phase 3-4 へ進む。**advisory lint fail-close 化は本 PLAN scope から分離** (out-of-scope、② 適時対応 carry) |
| **R-08** | **orchestration.db 過集中 (central event bus 化で責務膨張)** | 全 db 暗黙 bus 化で責務分離崩壊 | **entity owner / canonical source / cross-db FK 禁止 を L1 で明記**、orchestration は event 中継のみで domain logic 持たない、correlation_id で cross-db trace |
| **R-09** | **Event Sourcing 採用基準不足 (1/3 条件のみで hybrid 採用は弱い)** | plan.db の hybrid 採用根拠が後段で覆る | **6 軸判定表で全 db 評価**、各 db の判定根拠を ADR-018 で公開、hybrid の具体形 (state snapshot + change log) を仕様化 |
| **R-10** | **dual-write mismatch の沈黙故障** | 旧 db と新 event log が divergence | **dual-write mismatch gate (Phase 3 受入条件)** で全 write を検証、mismatch 検出時 fail-close、shadow replay で定期検証 |

## 7. 依存

- PLAN-068 V-model 強化 (単一 helix.db 前駆体、v22-v23 schema 既存)
- PLAN-070 L3 schema and contract design (D-DB / D-CONTRACT 既存基盤)
- PLAN-075 V-model 4 artifact 双方向 trace framework (Phase 4.5 必須)
- PLAN-078 agent_slots v28 schema (Phase 4 で vmodel.db へ移動対象、compatibility adapter で API 互換維持)
- PLAN-083 Harness 自動統合 (Phase 4 で API 互換維持必須)
- 既存 helix.db v30 schema (orchestration_events / projection_state / event_envelope table 追加で v31 へ)
- 既存 cli/lib/helix_db.py の `_write_connection(None)` pattern (compatibility adapter の adapt 対象)

## 8. Next Action

1. ✅ Phase 1.1: 本 PLAN doc 起票完了 (本 commit、tl-advisor Round 1 反映済)
2. ⏭️ Phase 1.2: tl-advisor Round 2 adversarial check (本 doc の修正反映が妥当か再検証)
3. Phase 1.3: `docs/v2/L1-REQUIREMENTS.md` 拡張 prompt 投入 → pmo-sonnet または Codex docs に委譲 (§3.9 章追加、G-01〜G-09 を FR/NFR/AC として記述、6 軸判定表 + entity ownership 表 + projector 境界表 + migration ゲート表 を含む)
4. Phase 1.4: handover update + Phase 2 (L2 基本設計) prompt 作成
5. Phase 2.1: CONCEPT.md 更新 + L2-MASTER.md 修正 (Event Sourcing 除外見直し) → Opus 直接または pmo-sonnet
6. Phase 2.2: ADR-018 (db 分離 + Event Sourcing + 6 軸判定 + frontend/backend 再判定条件) + ADR-019 (3 軸 + 二重らせん命名) 起票 → Codex docs
7. Phase 3 以降は L3 詳細設計、別セッションで継続

## 9. 設計上の意図 (memory との trace)

- 3 軸トライアングル [[project_2026_05_15_helix_triangle_principle]]: 成果物 (vmodel.db) ・実行者 (orchestration.db / agent_slots) ・記録 (全 db の event log) を物理 db に対応させる
- 二重らせん [[project_2026_05_15_helix_spiral_final_form]]: artifact strand (V-model 4 artifact 双方向 trace、PLAN-075) と record strand (event log、本 PLAN) を二重らせん化、Sprint 1 周で 1 回転、自己組織的進化
- V2 領域は L2 基本設計から [[feedback_v2_basic_design_first_not_plan_level]]: Phase 1 で L1 → Phase 2 で L2 基本設計 (CONCEPT + ADR) を厳守、Phase 3 以降に進む前に L2 凍結ゲートを通す

## 10. tl-advisor Round 1 反映履歴 (2026-05-17)

| 指摘 ID | 優先 | 反映箇所 | 内容 |
|---|---|---|---|
| #1 Critical | P1 | §2.1 G-02 / §6 R-09 / acceptance | 6 軸判定表 (audit / temporal / event ordering / write 頻度 / retention / replay SLO) 追加、plan.db hybrid 具体形 = state snapshot + change log を明示 |
| #2 Critical | P1 | §2.1 G-01 / §6 R-08 / acceptance | entity owner / canonical source / event envelope / correlation_id / cross-db FK 禁止 を L1 明記、orchestration 過集中リスクを R-08 として独立 |
| #3 Critical | P1 | §3.1 Phase 3 / §6 R-01/R-05/R-10 / acceptance | compatibility adapter + shadow replay + dual-write mismatch gate + rollback point + cutover 条件 を Phase 3 受入条件に追加、cli/lib/compatibility_adapter.py を Phase 4 実装に追加 |
| #4 Important | P2 | §2.1 G-03 / §6 R-02 | projector 同期許可リスト + timeout + 失敗時 fallback + lag 警告境界 100 event / fail-close 境界 1000 event を L1 明記 |
| #5 Important | P2 | §3.2 / §4 期間想定 / §6 R-07 | advisory lint fail-close 化を本 PLAN out-of-scope へ分離、Phase 期間を 5-8 → 8-12 セッションに修正 |
| #6 Minor | P3 | §2.1 G-09 / §3.1 Phase 2 ADR-018 | frontend/backend = state-store の再判定条件 (write 頻度・audit 要件の変化トリガ) を ADR-018 に明記 |
