---
plan_id: PLAN-084
title: "PLAN-084: helix.db 6 分離 + Event Sourcing + projector (V2 構築 ③ データベース管理フェーズ本体)"
status: draft
size: L
drive: be
created: 2026-05-17
revised: 2026-05-17 (tl-advisor Round 2 反映: 全 matrix 本文埋め込み + Phase 4 3 sprint 分割)
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
  - 6 db (orchestration / vmodel / scrum / plan / backend / frontend) の責務境界 + entity ownership + cross-db FK 禁止 + ATTACH 許可範囲 (migration/projector 内部に限定) + event envelope + correlation_id 規約が L1 確定 (§2.2)
  - Event Sourcing 6 軸判定 matrix が L1 本文確定 (§2.3)、3 event-sourced + 1 hybrid (plan = state snapshot + change log) + 2 state-store の採用根拠が明示
  - projector 責務分離 + 同期許可リスト 3 件 + timeout 200ms + fallback (async enqueue) + lag 警告境界 100 event / fail-close 境界 1000 event が L1 本文確定 (§2.4)
  - migration gate 表 (dual-write start → mismatch gate → shadow replay → lag stabilization → cutover → rollback) の順序 / 停止条件 / 失敗時 owner が L1 本文確定 (§2.5)
  - compatibility adapter 対象 file 8 件 (agent_slots / harness_monitor / scrum_local / reverse_local / http_api/routes 4 件) が L1 本文列挙、adapter 責務範囲確定 (§2.6)
  - 3 軸トライアングル + 二重らせんが ADR-019 で正式記述、frontend/backend = state-store 再判定条件が ADR-018 に明記
  - L4 完遂で event-sourced 3 db (orchestration/vmodel/scrum) が dual-write 稼働、projector 1+ 稼働 (lag < 100 event)、shadow replay PASS、dual-write mismatch gate 0 件、既存 ② 実行ハーネス機能破壊なし
---

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

### 4 query の検索結果リンク (3-5 件/query)

**Event Sourcing implementation pattern best practice (Martin Fowler / EventStore / Greg Young)**

- https://martinfowler.com/eaaDev/EventSourcing.html
- https://martinfowler.com/articles/201701-event-driven.html
- https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
- https://www.infoq.com/jp/news/2013/02/event-store-read-model/
- https://www.kurrent.io/blog/what-is-event-sourcing/

**Projector pattern read model write model (CQRS / Axon Framework / Lagom)**

- https://docs.axoniq.io/axon-framework-5-getting-started/5.1/implement-read-model/
- https://www.lagomframework.com/documentation/1.6.x/java/ReadSide.html
- https://eventsourcing.readthedocs.io/en/v9.4.1/topics/projection.html
- https://martendb.io/tutorials/read-model-projections
- https://docs.getprooph.org/event-store/projections.html

**UUID v7 RFC 9562 time-ordered identifier (IETF / draft-ietf-uuidrev-rfc4122bis)**

- https://www.ietf.org/rfc/rfc9562
- https://www.ietf.org/rfc/rfc9562.pdf
- https://www.rfc-editor.org/rfc/rfc9562
- https://www.iana.org/assignments/uuid/uuid.xhtml
- https://uuid.ramsey.dev/en/4.x/rfc4122.html

**SQLite ATTACH DATABASE transaction isolation (sqlite.org / 公式 doc)**

- https://www.sqlite.org/lang_attach.html
- https://www.sqlite.org/isolation.html
- https://www.sqlite.org/transactional.html
- https://www.sqlite.org/lang_transaction.html
- https://www.sqlite.org/docs.html

### HELIX 採用根拠

| 採用方針 | 根拠 |
|---|---|
| Event Sourcing 採用 | Martin Fowler は event の逐次保存を真の状態原本として扱うことで、監査可能性・時系列再構成・時点時系列照会を確保すると説明。Event Sourcing を用いることで本 PLAN の event envelope / shadow replay 要件と整合。 |
| Projector 採用 | Axon/Lagom/eventsourcing の projection 参考資料は、write model と read model の分離、read model を replay によって構築・再生成する運用を明示。projector 同期許可・async 併用方針は本 PLAN の負荷制御方針と一致。 |
| UUID v7 採用 | RFC 9562 が RFC4122 を更新し、UUIDv7 の時系列ソート特性を定義。event_id や再現時系列追跡で時系列順序性と衝突低減を担保しやすい。 |
| SQLite ATTACH 採用 | SQLite 公式文書は ATTACH を同一接続で複数 db を扱う手段として認めつつ、トランザクション隔離と実行時制御の特性を示す。migration/projector 内部限定という本 PLAN の運用制限は、実務上の cross-db 衝突回避に整合。 |

### 業界 standard との対応（Phase 4 部品）

| PLAN-084 部品 | 対応する industry pattern |
|---|---|
| Phase 4.A `compatibility_adapter.py` | **移行層 / Adapter pattern + CQRS 境界保護**: 既存 API を壊さず新旧 db 境界を接続する境界層。 |
| Phase 4.B `EventEnvelope` / projector core | **Event Sourcing + Projector (Read model projection)**: write path は event 追加のみ、read side はイベント再生で派生状態を構築する標準的構成に対応。 |
| Phase 4.C `shadow replay` / cutover | **Event replay / rebuild path**: event stream 再生検証と段階的切替を行い、state-sync 比較を前提とする移行フェーズ（影分身検証）に対応。 |

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

PLAN-084 は ③ データベース管理フェーズ本体に該当。①② が完成しており、③ を完遂させないと ④ db detector の本格配備 (Event Sourcing + projector 前提) が成立しない。

### 1.2 既存 docs/v2 における gap

pmo-project-explorer 調査 (本セッション 2026-05-17) で、以下が判明:

| 概念 | 正式 docs | memory | gap |
|---|---|---|---|
| 6 db 分離 | 不在 | あり | 全て新規 L1 要件化 |
| Event Sourcing | **L2-MASTER.md:36 で「含めない」と明示除外** | あり (採用方針) | **除外見直し**が必要 |
| projector | L2-MASTER.md:36 で除外 | あり | 新規 L1 要件化 |
| detector | CONCEPT.md / L1 / L2 に既存 (14 axis) | あり | 既存 14 axis を 6 db 対応へ拡張 |
| 3 軸トライアングル | 不在 | あり (5/15 確立) | ADR 起票 |
| 二重らせん | 不在 | あり (5/15 確立) | ADR 起票 |
| v30 → 6 db migration | 不在 | 言及あり | 全て新規 L2 設計 |

### 1.3 PLAN-068 (V-model 強化) との関係

memory [[project_2026_05_15_vmodel_as_db_separation_foundation]] で「PLAN-068 = 単一 helix.db 前駆体、PLAN-069 = db 分離 + V-model v2 収束」と整理されていたが、PLAN-069 番号は別タスク (G3 entry blocker resolution) で消費済 (memory [[feedback_opus_plan_number_collision_check]] 該当)。本 PLAN-084 がその「db 分離 + V-model v2 収束」を正式に引き継ぐ。

### 1.4 ユーザー指摘 (5 段階順序の根拠)

> 「工程やルール整備⇒実行ハーネス整備⇒データベース管理⇒問題発見システム配備⇒自動化システム化じゃないの？」(2026-05-17)
>
> 「実装していくうえで② 実行ハーネス整備の問題検出は適時対応。データベースからの問題発見は別枠でしょ。」(2026-05-17)

→ ② harness の検出系 (vmodel_lint / subagent_audit / sprint_lint) は ② の適時対応、④ db detector は ③ 完成後の別レイヤー。PLAN-084 は ③ を確立する。

## 2. 目的と L1 要件確定 (本 doc 本文に matrix 埋め込み、Round 2 反映)

helix.db を 6 db に物理分離し、event-sourced 3 db + hybrid 1 db + state-store 2 db のハイブリッド構成で **record strand (二重らせんの片側)** を物理実装する。projector が event log から read model を構築し、detector が record strand の anomaly を検知する基盤を整える。

本 §2 は L1 要件確定 matrix を本文に固定する (Phase 1.3 で L1-REQUIREMENTS.md §3.9 にも転記)。

### 2.1 確定 9 Gap (G-01〜G-09)

| # | Gap | L1 要件化先 |
|---|---|---|
| G-01 | 6 db 分離 + entity ownership + cross-db 規約 + ATTACH 許可範囲 | §2.2 |
| G-02 | Event Sourcing 6 軸判定 matrix + plan.db hybrid 具体形 | §2.3 |
| G-03 | projector 同期許可リスト + timeout + fallback + lag 境界 | §2.4 |
| G-04 | detector の 6 db 対応 (本 PLAN は責務分離のみ、本格配備は PLAN-085) | §2.5.0 (簡記) |
| G-05 | 3 軸閉ループ (成果物 → 記録 → 実行者 feedback) | §2.5.0 (簡記) |
| G-06 | v30 → 6 db migration gate 表 | §2.5 |
| G-07 | Reverse 例外 (record strand なし) | §2.5.0 (簡記) |
| G-08 | 二重らせん命名原則 ADR-019 | §2.5.0 (簡記) |
| G-09 | frontend/backend state-store の再判定条件 | §2.3 注記 + ADR-018 |

### 2.2 G-01: 6 db 物理分離 + entity ownership + cross-db 規約 (L1 確定)

**entity ownership 表**:

| db | canonical entity | 他 db からの参照経路 |
|---|---|---|
| orchestration.db | phase / gate / agent_slot / harness_event / harness_check_event | event subscribe 経由 (correlation_id で trace) |
| vmodel.db | artifact / artifact_link / cross_drive_integrity / drive_decision | event subscribe + projection_state 経由 |
| scrum.db | hypothesis / scrum_loop / srf_chain / scrum_local_loop / reverse_local_loop | event subscribe 経由 |
| plan.db | plan / sprint / task / wbs / design_sprint_drive_decision | projection_state snapshot 経由 |
| backend.db | api_endpoint / contract / impl_module / automation_run / audit_log / session_telemetry | projection_state snapshot 経由 |
| frontend.db | ui_component / mock / design_token / mock_promotion | projection_state snapshot 経由 |

**cross-db 規約 (契約)**:

| 規約 | 内容 |
|---|---|
| cross-db FK | **禁止** (SQLite ATTACH 下でも foreign key 制約は db 内に閉じる) |
| 許可される cross-db 参照 | projection_state table 経由のみ (snapshot を read) |
| ATTACH 許可範囲 | **migration script + projector 内部のみ**。アプリケーション層 (cli/helix-*) からの ATTACH は禁止、必要なら projection_state 経由 |
| event envelope | 全 event は { event_id, aggregate_id, db_name, event_type, payload, correlation_id, occurred_at } の envelope に統一 |
| correlation_id | cross-db trace に必須、orchestration.db で発行、他 db の event は orchestration の correlation_id を継承 |
| domain logic 配置 | orchestration.db は event 中継のみ、domain logic を持たない (過集中防止、R-08 緩和) |

### 2.3 G-02: Event Sourcing 6 軸判定 matrix (L1 確定)

| db | audit | temporal | event ordering | write 頻度 | retention | replay SLO | 採用方式 |
|---|---|---|---|---|---|---|---|
| orchestration | ◎ 必須 | ◎ 必須 | ◎ 必須 | 高 | 長期 (1y+) | < 5min | **event-sourced** |
| vmodel | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| scrum | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| plan | ◎ 必須 | △ 部分 | ○ 推奨 | 低 | 長期 (1y+) | < 30min | **hybrid (state snapshot + change log)** |
| backend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |
| frontend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |

**採用決定ルール**: audit + temporal + event ordering の 3 軸が全て ◎ 必須 → event-sourced、1 軸でも × → state-store、その間 → hybrid。

**plan.db hybrid の具体形** (Round 2 反映):
- **state 部分**: SQLite table (plan / sprint / task / wbs) で snapshot 保持、直接 update 可、最新 state の query 高速
- **change log 部分**: plan_change_log table に append (status 遷移 / WBS 追加削除 / sprint complete)、event ordering 保持
- **同期方針**: state update と change log append は同一 transaction、不整合は migration mismatch gate と同じ機構で検出
- **projector 不要**: plan.db 内で state と change log が両方持つため、外部 projector 不要 (event-sourced 3 db は projection_state を別 table で持つが、plan.db は内部完結)

**G-09: frontend/backend 再判定条件 (ADR-018 で明記)**:
- write 頻度が中→低に低下 → temporal query 要件の再評価
- audit 要件が法令/compliance で必須化 → audit trail 化
- cross-db 参照が頻繁化 (cross-db FK 禁止規約の常時違反) → 該当 db を hybrid 化検討
- 再判定: 6 ヶ月毎 ADR review、または上記トリガ発生時

### 2.4 G-03: projector 責務分離 + 同期境界 (L1 確定)

**projector 制約**:

| 制約 | 内容 |
|---|---|
| writer API | **禁止** (projector は event 生成 API を持たない、read model 生成専用) |
| cross-projection join | **禁止** (1 projector = 1 read model、依存 projection 間の結合は上位 query layer の責務) |
| replay idempotency | **必須** (dedup key = event_id + projector_id で冪等保証) |
| 配信方式 | async standard、同期は許可リストのみ |
| failure isolation | projector failure は self 検知せず、detector が last_processed_event_id を監視 |

**同期許可リスト** (3 件のみ、tl-advisor Round 2 #3 反映):

| 同期 projector | 同期理由 | timeout |
|---|---|---|
| phase projector | phase.yaml 更新は orchestration 全体の同期ポイント | 200ms |
| gate projector | gate 通過判定は次 phase 遷移の前提 | 200ms |
| agent_slot projector | fire/release は real-time UI / harness 監視に必要 | 200ms |

**timeout / fallback / lag 境界**:

| 項目 | 値 |
|---|---|
| 同期 projector timeout | 200ms |
| timeout 時 fallback | async queue にエンキュー、caller には 200 OK + warning header 返却 |
| lag 警告境界 | last_processed_event_id 差分 100 event 超過 → WARN log + harness_monitor に notify |
| lag fail-close 境界 | 同 1000 event 超過 → gate 通過判定 block (G2/G3/G4 全てで fail-close) |
| lag 時 read 挙動 | 同期 projector: stale data 許容 + warning header / async projector: 直近 snapshot 返却 + retry-after header |

### 2.5 G-06: v30 → 6 db migration gate 表 (L1 確定、Round 2 反映)

**migration ゲート順序 + 停止条件 + 失敗時 owner**:

| # | ゲート名 | 通過条件 | 停止条件 | 失敗時 owner / 動作 |
|---|---|---|---|---|
| 1 | dual-write start (v31 migration) | orchestration_events + projection_state + event_envelope table 追加完了、既存 v30 table 破壊なし | migration script の sqlite3 error / table 既存 conflict | **owner: Codex se** / rollback (v30 維持、v31 schema drop) |
| 2 | dual-write mismatch gate | 旧 db state と新 event log + projection_state の divergence 0 件 (10000 write 連続) | 1 件でも divergence 検出 | **owner: Codex se** (Opus は integration support) / fail-close (cutover 不可、divergence 解消まで dual-write 継続) |
| 3 | shadow replay 検証 | 過去 1000 event を新 projector で replay → derived state が旧 db state と byte-level 一致 | replay 不一致 / projector exception | **owner: Codex se** / fail-close (projector bug 修正後 retry) |
| 4 | projector lag stabilization | lag < 100 event が連続 24h | lag > 100 event の発生 | **owner: PM (Opus)** / warning (cutover 延期、lag 原因調査) |
| 5 | cutover | 上記 4 ゲート全 PASS + ユーザー (PO) 承認 | ユーザー却下 / 4 ゲートいずれか fail | **owner: PM (Opus) → ユーザー (PO) 承認** / execute (旧 state table tombstone → drop)、または rollback |
| 6 | rollback point | cutover 後 7d 以内に重大 anomaly (data loss / projector down >1h) | anomaly 検出 | **owner: PM (Opus) → ユーザー (PO) 承認** / 旧 db への切り戻し可能 (event log は保持、新 projection は drop) |

**rollback owner 補足**: ゲート 1-3 は自動 (Codex se 実装)、ゲート 4-6 は判断必須 (PM/Opus、ユーザー/PO)。

**migration 中の不変条件**:
- 既存 ② 実行ハーネス機能 (PLAN-078〜083) は dual-write 期間中も 100% 機能維持
- shadow replay 検証は migration 期間中常時稼働 (一度 PASS して終わりではない)

### 2.5.0 G-04 / G-05 / G-07 / G-08 (簡記、Phase 2 ADR で詳細化)

- **G-04 detector の 6 db 対応**: 既存 14 axis を 6 db each に割当、record strand anomaly 系 (schema drift / event order violation / projector lag / aggregate invariant violation) を追加。本 PLAN は責務分離のみ、本格配備は PLAN-085 想定 (④ 問題発見配備)。detector 入力は常に event log、artifact strand 直接 scan は V-model lint のみ
- **G-05 3 軸閉ループ**: 成果物 (vmodel.db) → 記録 (orchestration.db event log) → detector → 実行者 (agent_slots) feedback → artifact 修正 → 成果物。closed loop が成立することを L1 受入条件とする
- **G-07 Reverse 例外**: Reverse 機能 (R0-R4 + RGC) は record strand を持たない例外、新規 event 生成を伴わないため event log への write 対象外 (read のみ)
- **G-08 二重らせん命名 ADR**: HELIX 命名 = DNA 二重らせん由来を ADR-019 で正式化 (Phase 2 起票)

### 2.6 compatibility adapter 対象 file 一覧 (L1 確定、実 grep 結果、Round 2 #4 反映)

`grep -rln "_write_connection" cli/lib/` (2026-05-17 実行) で確定した adapt 対象:

| # | file | _write_connection 利用箇所数 | 6 db 分離後の所属 |
|---|---|---|---|
| 1 | cli/lib/agent_slots.py | 5 | orchestration.db |
| 2 | cli/lib/harness_monitor.py | 4 | orchestration.db |
| 3 | cli/lib/scrum_local.py | 6 | scrum.db |
| 4 | cli/lib/reverse_local.py | 5 | scrum.db |
| 5 | cli/lib/http_api/routes/audit.py | ≥1 | backend.db (audit_log) |
| 6 | cli/lib/http_api/routes/push_pr.py | ≥1 | backend.db (automation_run) |
| 7 | cli/lib/http_api/routes/hooks.py | ≥1 | backend.db (audit_log) |
| 8 | cli/lib/http_api/routes/telemetry.py | ≥1 | backend.db (session_telemetry) |
| 9 | cli/helix-pr (top-level CLI) | 2 | backend.db (automation_run) |
| 10 | cli/helix-push (top-level CLI) | 2 | backend.db (automation_run) |
| 11 | cli/helix-agent (top-level CLI、embed Python) | 1 | orchestration.db (agent_slots) |

合計: **11 file (lib 8 + top-level CLI 3) + 30+ 箇所** (helix_db.py 自身は adapter 定義側で除外、tl-advisor Round 2 important #2 反映で top-level CLI 3 file 追加)。

**棚卸し方針**: 単発 grep で凍結せず、`grep -rln "_write_connection" cli/` を Phase 4.A 着手時に再実行して本表に未列挙の callsite が無いことを検証対象とする。`tests/` 配下と `helix_db.py` 自身は adapter 定義側のため対象外、`cli/libexec/helix-session-start` は内部 helper として L3 で adapter 対象外の根拠を明記する (tl-advisor Round 2 carry)。

**compatibility_adapter.py の責務**:
- 既存 `helix_db._write_connection(None)` 呼び出しを 11 file (lib 8 + top-level CLI 3) 全てで透過的に 6 db 経路へ adapt
- API 互換 100% 維持 (上位 file は変更不要、import 切替のみ)
- dual-write 期間中: 旧 helix.db と新 6 db 両方に write、mismatch gate 検証
- cutover 後: 旧 helix.db への write を停止、6 db のみへ
- adapter 自身が compatibility_adapter テストで 11 file (lib 8 + top-level CLI 3) 全 path をカバー

## 3. スコープ

### 3.1 in-scope (L サイズ想定)

#### Phase 1: L1 要件定義 (本 PLAN doc + L1 doc 拡張)
- ✅ 本 PLAN-084 doc 完成 (要件項目 G-01〜G-09 を §2 に matrix 含めて確定)
- `docs/v2/L1-REQUIREMENTS.md` 拡張: §3.9 章追加 (本 doc §2 を転記、6 軸判定表 + entity ownership 表 + projector 境界表 + migration ゲート表 + adapter file 表)

#### Phase 2: L2 基本設計 (CONCEPT.md 更新 + ADR 起票)
- `docs/v2/CONCEPT.md` 更新: §3-axis-triangle / §double-helix-strand / §6-db-separation 章追加、L2-MASTER.md:36 「Event Sourcing 含めない」明示除外を **「採用 (6 軸判定により条件付き)」に修正**
- `docs/adr/ADR-018-db-separation-and-event-sourcing.md` 起票 (6 db 責務境界 + entity ownership + cross-db FK 規約 + ATTACH 許可範囲 + Event Sourcing 6 軸判定 + projector 責務 + detector 責務 + frontend/backend 再判定条件)
- `docs/adr/ADR-019-double-helix-naming-principle.md` 起票
- L2-MASTER.md 該当箇所修正

#### Phase 3: L3 詳細設計 (D-DB EXT + D-API EXT + migration plan)
- `docs/v2/L3-detailed-design/D-DB-SEP-draft.md` 起票 (6 db 各 schema 設計 + event log table + projection_state table + event envelope + correlation_id)
- `docs/v2/L3-detailed-design/D-API-SEP-draft.md` 起票 (event append API + projector read API + detector subscribe API + 同期許可リスト 3 件 + timeout / fallback / lag 境界 凍結)
- ~~`docs/v2/L3-detailed-design/D-DB-MIGRATION.md` 起票~~ → **取り消し**: migration 詳細は D-DB-SEP §6 (migration v30→v31 step 7) に統合済、別 file 起票は不要 (tl-advisor L3 Round 4 minor 反映)
- `docs/v2/L4-test-design/PLAN-084-unit-test-design.md` + `PLAN-084-integration-test-design.md` 起票

#### Phase 4: L4 実装 (3 sprint 分割、Round 2 Minor #6 反映)

**Phase 4.A** (migration + compatibility adapter):
- `cli/lib/compatibility_adapter.py` 新規 (§2.6 の 11 file (lib 8 + top-level CLI 3) × 30+ 箇所を adapt)
- `cli/lib/helix_db_orchestration.py` / `helix_db_vmodel.py` / `helix_db_scrum.py` 新規 (6 db 接続)
- `cli/lib/helix_db.py` 拡張: ATTACH DATABASE (migration/projector 内部限定)
- migration script v30 → v31 (orchestration_events + projection_state + event_envelope table 追加、dual-write 開始)
- adapter test (11 file (lib 8 + top-level CLI 3) 全 path PASS、API 互換 100% 確認)

**Phase 4.B** (event_log + projector + dual-write):
- `cli/lib/event_log.py` 新規 (event append + replay + envelope + correlation_id)
- `cli/lib/projector.py` 新規 (event → read model + idempotency + lag 監視)
- phase / gate / agent_slot の 3 同期 projector 実装 (許可リスト)
- dual-write mismatch gate 実装 (Phase 3 仕様準拠)
- projector unit + integration test

**Phase 4.C** (shadow replay + cutover):
- shadow replay 検証 script + 自動実行 hook
- projector lag 監視 + harness_monitor 統合
- cutover script (PO 承認後実行、rollback point 配備)
- 既存 phase.yaml の併存 / 廃止判断を ADR-020 で記録
- L4 全回帰 + helix doctor 0 fail

### 3.2 out-of-scope

- **④ db detector の本格配備** (= PLAN-085 想定)
- **⑤ 自動化システム化** (= 別 PLAN、全段階貫通配備)
- **② advisory lint fail-close 化** (vmodel_lint / subagent_audit / sprint_lint)。本 PLAN scope から **明示分離** (Round 1 important #5)、② 適時対応 carry として handover で別管理
- **frontend.db / backend.db の event-sourced 化** (= 別 PLAN、再判定条件を G-09 で ADR 化)
- **plan.db の完全 event-sourced 化** (= hybrid 採用、本 PLAN はここまで)
- **HTTP endpoint 層の event subscribe API** (= L6 統合検証 or 別 PLAN)
- **scrum_local / reverse_local の SRF 拡張機能** (= PLAN-079 Phase 2-5 carry)

## 4. Phase 構成 (Phase 4 を 3 sprint 分割、Round 2 Minor #6 反映)

| Phase | スコープ | size | 担当 | 期間想定 |
|---|---|---|---|---|
| Phase 1 | L1 要件定義 (本 PLAN doc + L1 doc §3.9 拡張) | M | Opus + tl-advisor | 1-2 セッション |
| Phase 2 | L2 基本設計 (CONCEPT.md + ADR-018 + ADR-019 + L2-MASTER 修正) | M-L | Opus + tl-advisor + pmo-tech-docs | 2-3 セッション |
| Phase 3 | L3 詳細設計 (D-DB-SEP-draft + D-API-SEP-draft + D-CONTRACT-EVENT-draft + test design 2 doc。migration 詳細は D-DB-SEP §6 に統合) | M-L | Codex se + tl-advisor | 2-3 セッション |
| Phase 4.A | L4 実装 sprint A (migration + adapter) | M | Codex se + Opus 統合 | 1-2 セッション |
| Phase 4.B | L4 実装 sprint B (event_log + projector + dual-write) | M | Codex se + pg | 1-2 セッション |
| Phase 4.C | L4 実装 sprint C (shadow replay + cutover + ADR-020) | M | Codex se + Opus | 1-2 セッション |

合計: **8-14 セッション想定** (was 8-12、Phase 4 sprint 分割で +0-2)、L サイズ。

## 4.5 V-model 4 artifact (PLAN-075 準拠)

| Artifact | 担当層 | 想定パス |
|---|---|---|
| ① 設計 | L2 基本設計 + L3 詳細設計 | docs/v2/CONCEPT.md (§3-axis + §double-helix + §6-db-separation) + docs/adr/ADR-018 + ADR-019 + ADR-020 (Phase 4.C cutover 判断、未起票) + docs/v2/L3-detailed-design/D-DB-SEP-draft.md + D-API-SEP-draft.md + D-CONTRACT-EVENT-draft.md (migration 詳細は D-DB-SEP §6 に統合) |
| ② 実装コード | L4 実装 | cli/lib/event_log.py + projector.py + compatibility_adapter.py + helix_db_orchestration.py + helix_db_vmodel.py + helix_db_scrum.py + cli/lib/helix_db.py (ATTACH 拡張) + migration v30 → v31 + shadow replay script + cutover script |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-084-unit-test-design.md + PLAN-084-integration-test-design.md (Phase 3 で起票) |
| ④ テストコード | L4 実装 | cli/lib/tests/test_event_log_unit.py + test_event_log_integration.py + test_projector_unit.py + test_projector_integration.py + test_compatibility_adapter.py (11 file (lib 8 + top-level CLI 3) × 30+ path) + test_db_separation_migration.py + test_shadow_replay.py + bats: tests/db-separation-cutover.bats + tests/dual-write-mismatch-gate.bats |

## 5. 受入条件

frontmatter `acceptance` 7 項目すべて達成 + 以下:

- Phase 1 完遂: 本 PLAN doc 完成 + `docs/v2/L1-REQUIREMENTS.md` §3.9 章追加 (本 doc §2 を転記)
- Phase 2 完遂: CONCEPT.md / L2-MASTER.md 修正 + ADR-018 + ADR-019 起票 + tl-advisor adversarial check PASS
- Phase 3 完遂: D-DB-SEP-draft (本 doc §2.5/§2.6 + migration step を §6 で詳細化) + D-API-SEP-draft + D-CONTRACT-EVENT-draft + 単体/結合 test 設計起票 (PLAN-084-unit-test-design + PLAN-084-integration-test-design)
- Phase 4.A 完遂: compatibility adapter + 6 db 接続 + migration v30 → v31 + adapter test 11 file (lib 8 + top-level CLI 3) × 30+ path PASS
- Phase 4.B 完遂: event_log + projector + dual-write + mismatch gate + projector test
- Phase 4.C 完遂: shadow replay PASS + cutover script + ADR-020 起票 + helix doctor 0 fail
- pytest + bats 全 PASS、既存 ② 実行ハーネス機能 (PLAN-078〜083) 破壊なし

## 6. リスク (Round 2 反映で migration owner / adapter 範囲 / ATTACH 衝突 を強化)

| ID | リスク | 影響 | 緩和策 |
|---|---|---|---|
| R-01 | migration 中断時の cross-db 整合性 | helix.db v30 と 6 db の二重真実 | §2.5 migration gate 表 (順序 + 停止条件 + owner 明示) + rollback point (gate 6) |
| R-02 | projector lag による read 一貫性低下 | UI / CLI が古い state を表示 | §2.4 lag 警告境界 100 event / fail-close 1000 event + last_processed_event_id 監視 (PLAN-085 で detector 実装) |
| R-03 | SQLite ATTACH DATABASE の性能劣化 | cross-db query が遅い | §2.2 ATTACH 許可範囲を migration/projector 内部に限定、性能 NFR < 100ms (L1、Phase 3 D-DB/D-API で正式 NFR に昇格予定) |
| R-04 | phase.yaml と projector derived state の二重真実 | Phase 4.C cutover 判断ミス | Phase 4.C 末で「併存期間維持」または「phase.yaml 廃止」を ADR-020 で記録 |
| R-05 | ② 実行ハーネス (agent_slots / harness_monitor 等) の破壊 | PLAN-078〜083 機能停止 | §2.6 compatibility adapter で 11 file (lib 8 + top-level CLI 3) × 30+ 箇所を adapt、API 互換 100% 維持、adapter test で全 path 検証 |
| R-06 | Event Sourcing 採用範囲の判断ミス (plan.db hybrid) | 中期的 re-architecture コスト | §2.3 6 軸判定 matrix + plan.db hybrid 具体形 (state snapshot + change log) を本文確定 |
| R-07 | L 規模 PLAN の途中 cancel リスク | framework 中断で advisory 状態が長期化 | Phase 4 を 3 sprint (A/B/C) に分割で部分完遂可、advisory lint fail-close 化は本 PLAN scope から分離 |
| R-08 | orchestration.db 過集中 (central event bus 化) | 全 db 暗黙 bus 化で責務分離崩壊 | §2.2 entity owner / canonical source / cross-db FK 禁止 を L1 明記、orchestration は event 中継のみで domain logic 持たない |
| R-09 | Event Sourcing 採用基準不足 (1/3 条件のみで hybrid) | plan.db hybrid 根拠が後段で覆る | §2.3 6 軸判定 matrix で全 db 評価、各 db 根拠を ADR-018 で公開 |
| R-10 | dual-write mismatch の沈黙故障 | 旧 db と新 event log の divergence | §2.5 dual-write mismatch gate (10000 write 連続 0 件、shadow replay 定期検証) |
| **R-11** | **ATTACH 許可範囲の運用 drift** | アプリ層からの ATTACH 利用で cross-db FK 禁止規約が形骸化 | §2.2 で ATTACH 許可を migration/projector 内部に限定明記、Phase 3 D-API で ATTACH 利用箇所を全列挙、Phase 4 adapter test で禁止違反検出 |
| **R-12** | **compatibility adapter の漏れ** | 11 file (lib 8 + top-level CLI 3) 以外で `_write_connection(None)` 利用が将来発生 | Phase 4.A で `helix code stats --uncovered` + grep CI gate を追加、新規 `_write_connection(None)` 利用に lint で警告 |

## 7. 依存

- PLAN-068 V-model 強化 (単一 helix.db 前駆体、v22-v23 schema 既存)
- PLAN-070 L3 schema and contract design (D-DB / D-CONTRACT 既存基盤)
- PLAN-075 V-model 4 artifact 双方向 trace framework (Phase 4.5 必須)
- PLAN-078 agent_slots v28 schema (Phase 4.A で orchestration.db へ移動対象、compatibility adapter で API 互換維持)
- PLAN-079 scrum_local / reverse_local (Phase 4.A で scrum.db へ移動対象)
- PLAN-080 harness_monitor v30 schema (Phase 4.A で orchestration.db へ移動対象)
- PLAN-083 Harness 自動統合 (Phase 4.A で API 互換維持必須)
- 既存 helix.db v30 schema (orchestration_events / projection_state / event_envelope table 追加で v31 へ)
- 既存 cli/lib/helix_db.py の `_write_connection(None)` pattern (11 file (lib 8 + top-level CLI 3) × 30+ 箇所、§2.6 列挙)

## 8. Next Action

1. ✅ Phase 1.1: 本 PLAN doc 起票完了 (本 commit、tl-advisor Round 1 + Round 2 反映済)
2. ⏭️ Phase 1.2: tl-advisor Round 3 adversarial check (本 doc Round 2 反映の妥当性再検証、approve 期待)
3. Phase 1.3: `docs/v2/L1-REQUIREMENTS.md` 拡張 prompt 投入 → pmo-sonnet または Codex docs に委譲 (本 doc §2 を §3.9 に転記、Round 2 反映後の実 matrix 含む)
4. Phase 1.4: handover update + Phase 2 (L2 基本設計) prompt 作成
5. Phase 2.1: CONCEPT.md 更新 + L2-MASTER.md 修正 → Opus 直接または pmo-sonnet
6. Phase 2.2: ADR-018 / ADR-019 起票 → Codex docs
7. Phase 3 以降は L3 詳細設計、別セッションで継続

## 9. 設計上の意図 (memory との trace)

- 3 軸トライアングル [[project_2026_05_15_helix_triangle_principle]]: 成果物 (vmodel.db) ・実行者 (orchestration.db / agent_slot projector) ・記録 (全 event-sourced db の event log) を物理 db に対応
- 二重らせん [[project_2026_05_15_helix_spiral_final_form]]: artifact strand (V-model 4 artifact 双方向 trace、PLAN-075) と record strand (event log、本 PLAN) を二重らせん化、Sprint 1 周で 1 回転、自己組織的進化
- V2 領域は L2 基本設計から [[feedback_v2_basic_design_first_not_plan_level]]: Phase 1 で L1 → Phase 2 で L2 基本設計 (CONCEPT + ADR) を厳守

## 10. tl-advisor 反映履歴

### Round 1 (2026-05-17、changes_required)

| 指摘 ID | 優先 | 反映箇所 | 内容 |
|---|---|---|---|
| #1 Critical | P1 | §2.1 G-02 / §6 R-09 / acceptance | 6 軸判定軸の追加、plan.db hybrid 具体形の言及 (Round 2 で matrix を本文埋め込みへ昇格) |
| #2 Critical | P1 | §2.1 G-01 / §6 R-08 / acceptance | entity owner / cross-db FK 禁止 / orchestration 過集中リスク R-08 を独立 (Round 2 で実 ownership 表を本文埋め込みへ昇格) |
| #3 Critical | P1 | §3.1 Phase 3 / §6 R-01/R-05/R-10 / acceptance | compatibility adapter + shadow replay + dual-write mismatch gate + rollback point + cutover 条件 を追加 (Round 2 で実 gate 表 + adapter file 一覧を本文埋め込みへ昇格) |
| #4 Important | P2 | §2.1 G-03 / §6 R-02 | projector 同期許可リスト + timeout + fallback + lag 境界を概念追加 (Round 2 で 3 件具体化を本文埋め込みへ昇格) |
| #5 Important | P2 | §3.2 / §4 期間想定 / §6 R-07 | advisory lint fail-close 化を out-of-scope 分離、Phase 期間 5-8 → 8-12 セッション |
| #6 Minor | P3 | §2.1 G-09 / §3.1 Phase 2 ADR-018 | frontend/backend 再判定条件 G-09 独立 |

### Round 2 (2026-05-17、changes_required)

| 指摘 ID | 優先 | 反映箇所 | 内容 |
|---|---|---|---|
| #1 Critical | P1 | §2.3 本文 matrix | 6 軸判定 matrix を「Phase 1.3 委譲」から本 PLAN doc §2.3 本文に実データで埋め込み、plan.db hybrid 具体形を 4 項目で詳細化 |
| #2 Critical | P1 | §2.5 本文 matrix | migration gate 表を 6 ゲート (順序 + 通過条件 + 停止条件 + owner) で本文確定、ゲート 1-3 = Codex se、4-6 = PM/PO の owner 区分 |
| #3 Important | P2 | §2.4 本文 matrix | projector 同期許可リスト 3 件 (phase / gate / agent_slot)、timeout 200ms、fallback (async enqueue)、lag 警告 100 / fail-close 1000 event、lag 時 read 挙動を本文確定 |
| #4 Important | P2 | §2.6 本文 + §3.1 Phase 4.A | compatibility adapter 対象を grep 実行で確定 (11 file (lib 8 + top-level CLI 3) × 30+ 箇所)、scrum_local / reverse_local / http_api/routes 4 件を追加、Phase 4.A で adapter test 全 path 検証 |
| #5 Important | P2 | §2.2 + §6 R-11 | cross-db FK 禁止 vs ATTACH の衝突を契約化、ATTACH 許可範囲を migration/projector 内部に限定、R-11 (ATTACH drift) 独立 |
| #6 Minor | P3 | §4 Phase 4 分割 / §6 R-12 | Phase 4 を 4.A/4.B/4.C の 3 sprint に分割、合計 8-14 セッション。compatibility adapter 漏れ R-12 を独立 |

### Round 3 (2026-05-17、passed approved_with_minor_changes)

| 指摘 ID | 優先 | 反映箇所 | 内容 |
|---|---|---|---|
| #1 minor | — | L3 carry | PLAN-084 §2.2 event envelope を旧形のまま維持 (Phase 2.2 / L3 では ADR-018 を正本引用、blocker ではない) |
| #2 minor | — | carry note | ADR-019 carry 表は 8 件で実体一致 (commit メッセージ memo「9 件」は誤、本体問題なし) |

### CONCEPT review (2026-05-17、approved_with_minor_changes)

CONCEPT.md 拡張 (commit dd3be44) に対する tl-advisor 単独 review。

| 指摘 ID | 優先 | 反映箇所 | 内容 |
|---|---|---|---|
| #1 Important | P2 | L1-REQUIREMENTS.md §3.9 adapter 表 + L436 + L467 + L563 | L1 側 8→11 file 同期 (commit dc5dce7 で反映、§3.9 表 8→11 row 拡張 + 3 箇所文章修正) |
| #2 Minor | P3 | CONCEPT.md §6-db-separation 6 軸表 | replay SLO 列省略の根拠を blockquote で明記 (commit dc5dce7 で反映) |

## 11. Phase 2 完遂凍結 (2026-05-17)

### G2 ゲート判定: PASS

Phase 2 (L2 基本設計) を tl-advisor 4 rounds passed をもって完遂凍結する。

- Phase 2.0 FR-DB ID 改番 ✓ (commit 953e8ba、carry A 解消、§3.3 EXT / §3.9 SEP 接頭辞)
- Phase 2.1 ADR-018/019 起票 ✓ (commit d5bae22、321 + 254 行、Decision 9 件確定)
- Phase 2.2 CONCEPT.md +125 行 3 章 ✓ (commit dd3be44 + dc5dce7、3 軸トライアングル + 二重らせん strand + 6 db 分離 + ES 概念)
- Phase 2.3 L2-MASTER.md:36 修正 ✓ (commit d5bae22 内、「含めない」→「ADR-018/019 で扱う」)
- Phase 2.4 tl-advisor 4 rounds ✓ (ADR Round 1-2 changes_required → Round 3 passed / CONCEPT Round 1 approved_with_minor_changes)

5 doc 全同期 (CONCEPT / ADR-018 / ADR-019 / PLAN-084 / L1-REQUIREMENTS で 11 file × 30+ 箇所)。

**注記**: ADR-018/019 frontmatter `status: proposed` は維持 (Accepted は PO 承認待ち、本 PLAN doc は PM 判定として G2 凍結を宣言する)。

### Phase 3 着手 (本 commit から開始)

L3 詳細設計を `docs/v2/L3-detailed-design/` 配下に起票:

- ✅ D-DB-SEP-draft.md (Phase 3.1、708 行、ADR-018 §Decision.1/2/3/5 schema 展開、15 table + 9 carry to Phase 4)
- ✅ D-API-SEP-draft.md (Phase 3.2、607 行、compatibility adapter interface + Python helper API、12 carry to Phase 4)
- ✅ D-CONTRACT-EVENT-draft.md (Phase 3.3、706 行、event envelope dataclass + UUID v7 generator + correlation_id、11 carry to Phase 4)
- ⏭️ tl-advisor L3 review (3 doc 揃った、本セッション末で投入、G3 凍結判定)

### Phase 3 doc 群の双方向 trace 構造

3 doc は frontmatter `sibling_docs` と各 §References で相互参照:

- **D-DB-SEP-draft**: schema 正本 (table 定義 + migration step)
- **D-API-SEP-draft**: adapter API 正本 (write_connection / read_cross_db_projection)
- **D-CONTRACT-EVENT-draft**: event class 正本 (EventEnvelope dataclass + UUID v7 + correlation)

各 doc は他 2 doc を sibling として参照し、責務境界を明示 (D-DB-SEP = schema / D-API-SEP = adapter API / D-CONTRACT-EVENT = event class)。重複実装を防ぐ。

### Phase 3 carry to Phase 4 累計

3 doc 合計 carry items = 9 (D-DB-SEP) + 12 (D-API-SEP) + 11 (D-CONTRACT-EVENT) = **32 carry items**。

主な Phase 4 担当分担:
- Phase 4.A (migration + adapter): UUID v7 generator 実装 / adapter routing logic / adapter unit test / smoke test / ATTACH CI gate
- Phase 4.B (event + projector + dual-write): EventEnvelope dataclass 実装 / correlation_context / payload schema / projector lag 監視
- Phase 4.C (shadow replay + cutover): shadow replay test / cutover gate 5 PO 承認 runbook / ADR-020 起票

### Phase 2 完遂後の commit chain

| commit | 内容 | Phase |
|---|---|---|
| 953e8ba | FR-DB ID 改番 (carry A 解消) | 2.0 |
| d5bae22 | ADR-018/019 起票 + L2-MASTER:36 修正 | 2.1 / 2.3 |
| f5c258e | tl-advisor Round 1 反映 | 2.4 |
| 2b01bd9 | tl-advisor Round 2 反映 | 2.4 |
| dd3be44 | Phase 2.2 CONCEPT.md 拡張 | 2.2 |
| dc5dce7 | tl-advisor CONCEPT review 反映 + Phase 2 完遂凍結 | 2.2 / 2.4 |

## 12. Phase 3 完遂凍結 (2026-05-17)

### G3 ゲート判定: PASS

Phase 3 (L3 詳細設計) を tl-advisor 4 rounds (L3 Round 1-3 changes_required → Round 4 passed) をもって完遂凍結する。

- Phase 3.1 D-DB-SEP-draft 起票 ✓ (commit 8ef856e、708 行、15 table + migration step)
- Phase 3.2 D-API-SEP-draft 起票 ✓ (commit ed934f1、607 行、compatibility adapter API)
- Phase 3.3 D-CONTRACT-EVENT-draft 起票 ✓ (commit ed934f1、706 行、EventEnvelope class)
- Phase 3.4 test design 2 doc 起票 ✓ (commit ff04129、unit 510 行 35 case + integration 783 行 40 case)
- Phase 3.4 tl-advisor L3 Round 1-4 ✓
  - Round 1 (ff04129): changes_required → important 6 + minor 3 反映
  - Round 2 (2f82284): changes_required → important 4 + minor 1 反映
  - Round 3 (2e286ef): changes_required → important 3 + minor 1 反映 (grep 漏れ全件除去)
  - **Round 4 (本 commit)**: **passed (approved_with_minor_changes)** — critical 0 / important 0 / minor 2 (本 commit で stale cleanup 完了)

### V-model 4 artifact 完備状態

- ① 設計: ADR-018 / ADR-019 (L2) + D-DB-SEP-draft / D-API-SEP-draft / D-CONTRACT-EVENT-draft (L3)
- ② 実装コード: Phase 4.A/4.B/4.C で起票 (cli/lib/migrations/v31_db_separation.py / compatibility_adapter.py / event_envelope.py / projector.py 等)
- ③ テスト設計: PLAN-084-unit-test-design.md (35 case) + PLAN-084-integration-test-design.md (40 case)
- ④ テストコード: Phase 4 で起票 (cli/lib/tests/test_*.py + cli/tests/*.bats)

5 L3/L4 doc 全同期 (V-model 4 artifact ① ⇔ ③ 双方向 trace 完備)、PLAN-084 / L1-REQUIREMENTS / CONCEPT.md と整合確認済。

**注記**: ADR-018/019 frontmatter `status: proposed` は維持 (Accepted は PO 承認待ち)。Phase 4.A 着手は本 G3 PASS 判定により着手 OK。

### G3 軽量再判定 (2026-05-19、commit 9145239 + 611ab74)

L3 addendum merge (commit 9145239) + tl-advisor 指摘反映 (commit 611ab74、P1 4件 + P2 2件 + P3 1件) による `D-API-SEP-draft.md` / `D-CONTRACT-EVENT-draft.md` 本文変更について、Opus 自己軽量再判定を実施。

判定: **PASS 継続** (frozen contract 非破壊)

根拠:

| # | 変更内容 | 評価 |
|---|---|---|
| P1.1-2 | D-CONTRACT §4.3 threading.local → historical / §4.8 alias 規約明示 | 既存実装 `cli/lib/correlation_context.py` (Phase 4.B 完遂、commit b6facdf) に doc を寄せる訂正。新規契約なし |
| P1.3-4 | D-API §2.6 _DualWriteConnection 実装 2 file 併記 + docstring 英語化 | class signature 不変、`cli/lib/dual_write_connection.py` (commit b6facdf 既存) の追加列挙のみ |
| P2.1 | D-CONTRACT V-model trace ② に `correlation_context.py` 追加列挙 | 既存 file 列挙拡張 |
| P2.2 | addendum.md frontmatter status=merged 整合 | doc 内部整合のみ |
| P3.1 | テスト file 名 typo 訂正 (test_uuid7_generator_unit.py 他) | 実 file 名整合 |

新規 contract 追加・signature 変更・破壊変更は無し。Phase 4.A/4.B/4.C 完遂済の実装 (cli/lib/compatibility_adapter.py / dual_write_connection.py / correlation_context.py / event_envelope.py / projector.py / shadow_replay.py / cutover_orchestrator.py / rollback_orchestrator.py) と doc 乖離なし。tl-advisor 再 review は任意 carry とし、Phase 4.A〜4.C 完遂 + PO 承認 path (PLAN-085 / PLAN-086) を継続する。

### L4 carry list 最終確定 (tl-advisor Round 4 助言)

| Phase 4 sprint | scope | carry items 主要 |
|---|---|---|
| **Phase 4.A (migration + adapter)** | v30 → v31 / compatibility_adapter / routing / UUID v7 (3.12 fallback) | adapter 本実装 / `_FILE_TO_DB` 再 grep / UUID v7 generator (uuid7-py or 自前) / adapter unit test (U-ADAPTER 15) / smoke test (I-SMOKE 6) / ATTACH 禁止 CI gate / session-start 対象外 smoke / runbook 下準備 / inspect.stack frame index 実測確定 (PM 承認) |
| **Phase 4.B (event + projector + dual-write)** | EventEnvelope / correlation / projector / dual-write mismatch | EventEnvelope dataclass 実装 / `create_event_envelope` factory / payload JSON schema + jsonschema validator / correlation_context (thread-local) / projector + lag 監視 / dual-write mismatch gate / EventEnvelope/correlation tests (U-EVT 10 + U-UUID 5 + U-CORR 5 + I-DUALWRITE 8 + I-CORR 6) |
| **Phase 4.C (shadow replay + cutover)** | shadow replay / cutover / rollback / ADR-020 | shadow replay test (I-REPLAY 8) / cutover script + gate 5 PO 承認 / rollback gate 6 / ADR-020 起票 (gate 5 pass 後 - gate 6 前) / 全回帰 (pytest 1622+ / bats / shell) / helix doctor 0 fail / soak 短縮条件確定 |

### Phase 3 完遂後の commit chain

| commit | 内容 | Phase |
|---|---|---|
| 8ef856e | D-DB-SEP-draft 起票 + Phase 2 凍結宣言 | 3.1 |
| ed934f1 | D-API-SEP + D-CONTRACT-EVENT 起票 | 3.2 / 3.3 |
| ff04129 | L3 review Round 1 反映 + test design 2 doc 起票 | 3.4 |
| 2f82284 | L3 Round 2 反映 (V-model trace 凍結 + fail-close + schema byte-level) | 3.4 |
| 2e286ef | L3 Round 3 反映 (grep 漏れ全件除去) | 3.4 |
| **本 commit** | **L3 Round 4 minor 反映 + G3 凍結宣言** | **3.4 / G3** |

next: Phase 4.A 着手準備 (compatibility_adapter.py + migration v31 + UUID v7 generator + adapter unit/smoke test 実装、次セッション carry)。

## Revision History

- 2026-05-19 業界 standard 引用 retrofit (W5b-B、PLAN-087 ガードレール準拠)
