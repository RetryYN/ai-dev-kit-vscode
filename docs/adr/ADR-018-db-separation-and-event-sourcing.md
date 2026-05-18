# ADR-018: helix.db 6 分離 + Event Sourcing + projector 境界

## Status

Accepted (2026-05-18)

> proposed (2026-05-17) → Accepted (2026-05-18) PO 承認。PLAN-084 Phase 4.A + 4.B + 4.C 実装完遂後、PO (yoshiyuki0907yn@gmail.com) が「OK」と承認。

## 業界 standard 参照 (Web 検索 retrofit 2026-05-19)

### 4 query の検索結果（3〜5 件/query）

- **Martin Fowler Event Sourcing pattern**
  - https://www.martinfowler.com/eaaDev/EventSourcing.html
  - https://martinfowler.com/bliki/CommandQuerySeparation.html
  - https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
- **Greg Young CQRS Event Sourcing pattern**
  - https://learncqrs.com/do6pMI
  - https://virtualddd.com/videos/greg-young-a-decade-of-ddd-cqrs-event-sourcing/
  - https://www.tjenwellens.eu/blog/greg-young-cqrs-and-event-sourcing-code-on-the-beach-2014-youtube/
  - https://www.infoq.com/news/2014/09/greg-young-event-sourcing/
- **DDD Bounded Context per database (Eric Evans / Vaughn Vernon)**
  - https://www.domainlanguage.com/ddd/reference/
  - https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf
  - https://www.oreilly.com/library/view/domain-driven-design-distilled/9780134434964/ch02.html
- **SQLite ATTACH DATABASE multi-db transaction**
  - https://www.sqlite.org/lang_attach.html
  - https://sqlite.org/atomiccommit.html
  - https://system.data.sqlite.org/home/raw/Doc/Extra/lang_attach.html?name=8427ac0a57f6628d0c87ab302a11042ba45d4eb5

### HELIX 採用根拠

- **Event Sourcing の選定理由**: `helix.db` を全 DB で event-sourced にするのではなく、監査要件・時間軸整合性・再構築性が高い db (`orchestration.db`, `vmodel.db`, `scrum.db`) のみを ES 化し、既知の高頻度/短寿命用途 (`backend.db`, `frontend.db`) は state-store を採ることで更新負荷と運用複雑性を抑える。これは Martin Fowler が Event Sourcing の価値（監査可能な状態履歴、再水和）を示す設計と整合する。
- **CQRS 採用判断**: `record` 書き込みと `projection` 読み取りを分離し、`projector` の再計算で read model を再構築する構成を採用。決定の `event-sourced 3 db + hybrid` と一致し、Greg Young が CQRS を「command/query 分離」として主張する観点と一致する。
- **DDD Bounded Context per DB の根拠**: `plan`/`orchestration`/`vmodel`/`scrum`/`backend`/`frontend` を DB 単位で責務明確化し、cross-db 参照を projection_state 経由のみとすることで、bounded context 境界に沿った「1 モデル = 1 所有領域」を保持する。これは DDD の bounded context 原則（Eric Evans）および実務書での戦略設計（Vernon）に整合する。
- **SQLite ATTACH 採用根拠**: migration と projection 内部でのみ `ATTACH DATABASE` を許可し、同一接続で複数 db の multi-db transaction を活用。公式 doc の atomic multi-file commit 特性を前提に、アプリ層の自由 ATTACH を禁止することで参照規約を守る。

### 業界 standard との対応（FR-DB / AC-DB）

| 要件 | 対応 business pattern | 対応箇所 |
|---|---|---|
| FR-DB-SEP-01 / FR-DB-SEP-07 / FR-DB-SEP-09 | Bounded Context / Database per Context | Decision §1（db 分離・所有権・跨ぎ規約）、Decision §4（再判定条件） |
| FR-DB-SEP-02 / FR-DB-SEP-04 / AC-DB-SEP-01 | Event Sourcing（監査・時間軸一貫性） | Decision §2（6 軸判定） |
| FR-DB-SEP-03 / FR-DB-SEP-05 / AC-DB-SEP-02 / AC-DB-SEP-03 | CQRS + Projection / Read model | Decision §2（ハイブリッド）、Decision §3（projection 境界） |
| FR-DB-SEP-06 / AC-DB-SEP-04 / AC-DB-SEP-07 | ATTACH Database + atomic multi-file transaction 制御 | Decision §1（ATTACH 許可範囲）・Decision §5（migration gate） |
| AC-DB-SEP-05 / AC-DB-SEP-06 / FR-DB-SEP-08 | Adapter / 検証ゲート + 段階移行 | Decision §5（6 段階 migration gate） |

**注記**: `FR-DB-SEP-01〜09 / AC-DB-SEP-01〜07` は本 ADR の `Decision §1〜§5`（`PLAN-084`）で対応付け済みであり、`L1-REQUIREMENTS.md §3.9` の要件群と一対一に trace 可能。

## Deciders

- PM (Opus)
- TL (Codex tl-advisor、Round 1-3 反映)
- PO (yoshiyuki0907yn@gmail.com、2026-05-18 承認)

---

## Context

HELIX V2 構築は 5 段階順序で進行する。

```
① 工程やルール整備   完成 (PLAN-075/076/077)
② 実行ハーネス整備   完成 (PLAN-078〜083)
③ データベース管理   未着手 ← 本 ADR の対象 (PLAN-084)
④ 問題発見配備      ③ 完成後の別枠フェーズ
⑤ 自動化システム化   全段階貫通配備
```

ADR-015 (V2 orchestration) が確立した PM 実装禁止・PMO 新設・TL/SE/PE 分離の運用体制の上に、③ データベース管理フェーズとして本 ADR を位置づける。

V2 構築が進むにつれ、単一 `helix.db` に以下の 9 Gap が顕在化した。

| # | Gap | 本 ADR の対応 |
|---|---|---|
| G-01 | 6 db 分離 + entity ownership + cross-db 規約 + ATTACH 許可範囲 | Decision §1 で凍結 |
| G-02 | Event Sourcing 6 軸判定 matrix + plan.db hybrid 具体形 | Decision §2 で凍結 |
| G-03 | projector 同期許可リスト + timeout + fallback + lag 境界 | Decision §3 で凍結 |
| G-04 | detector の 6 db 対応 (責務分離のみ) | PLAN-085 委譲、Decision §3 で境界明示 |
| G-05 | 3 軸閉ループ (成果物 → 記録 → 実行者 feedback) | ADR-019 / PLAN-085 委譲 |
| G-06 | v30 → 6 db migration gate 表 | Decision §5 で凍結 |
| G-07 | Reverse 例外 (record strand なし) | Decision §1 注記に明示 |
| G-08 | 二重らせん命名原則 | ADR-019 で別途対応 |
| G-09 | frontend/backend state-store 再判定条件 | Decision §4 で凍結 |

本 ADR は G-01 / G-02 / G-03 / G-06 / G-09 を L2 設計として凍結し、G-04 / G-05 / G-07 / G-08 の委譲先を明確にする。

前提 L1 要件: `L1-REQUIREMENTS.md §3.9` の FR-DB-SEP-01〜09 / AC-DB-SEP-01〜07 が本 ADR の受入条件に対応する。

**V2 構築の文脈**: PLAN-068 (V-model 強化 = 単一 helix.db 前駆体) がデータ基盤の最初の一手を打ち、PLAN-075 (V-model 4 artifact 双方向 trace) が artifact strand を確立した。PLAN-078〜083 (harness 自動統合) が実行ハーネスを完成させたことで、③ データベース管理フェーズの前提が整った。helix.db を 6 db に分離することで、HELIX の設計原理 "二重らせん" の record strand が物理実装される。artifact strand (V-model 4 artifact 双方向 trace) と record strand (event log) が揃って初めて、④ 問題発見配備 (PLAN-085 予定) の db detector が record strand の anomaly を検知する基盤が成立する。

**tl-advisor 合意**: 本 ADR の Decision は tl-advisor Round 1-3 の adversarial check を経て確定した。特に以下の 3 点は Round 2 の重大指摘 (Critical P1) として反映された。

1. 6 軸判定 matrix を "委譲先で決める" のではなく PLAN doc 本文に実データで埋め込む (G-02)
2. migration gate 表を 6 ゲートで owner 区分 (Codex se / PM / PO) まで含めて本文確定する (G-06)
3. projector 同期許可リストを 3 件に絞り、timeout 200ms / fallback / lag 境界を数値確定する (G-03)

## Decision

> **凍結する 5 事項**: (1) 6 db 物理分離 + entity ownership (2) Event Sourcing 6 軸判定ハイブリッド採用 (3) projector 境界 (4) frontend/backend 再判定条件 (5) migration gate 6 段階。
> 以下の各節はこの 5 事項を PLAN-084 §2.2-2.6 matrix から ADR 形式に再構成したものである。

### 1. 6 db 物理分離 + entity ownership + cross-db 規約 (G-01 / FR-DB-SEP-01)

helix.db を 6 個の SQLite file に物理分離する。各 db は独立した SQLite file として存在し、entity の canonical 所属は以下の ownership 表で凍結する。

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
| cross-db FK | **禁止**。SQLite ATTACH 下でも foreign key 制約は db 内に閉じる |
| 許可される cross-db 参照 | projection_state table 経由のみ (snapshot を read) |
| ATTACH 許可範囲 | **migration script + projector 内部のみ**。アプリケーション層 (cli/helix-*) からの ATTACH は禁止。必要な cross-db 参照は projection_state 経由とする |
| event envelope | 全 event は `{ event_id, aggregate_id, aggregate_type, db_name, event_type, payload, correlation_id, occurred_at }` の envelope に統一 |
| event_id | **global unique** (UUID v7 推奨)。`{db_name, event_id}` の composite key で identity を保証する |
| aggregate identity | aggregate key は `{db_name, aggregate_type, aggregate_id}` の **composite key**。`aggregate_id` 単体での global uniqueness は要求しない (db 内 uniqueness のみ)。L3 契約で詳細 schema を確定 (tl-advisor Round 2 important #3 反映、carry: L3 で event envelope schema 確定) |
| correlation_id | cross-db trace に必須。orchestration.db で発行し、他 db の event は orchestration の correlation_id を継承する |
| domain logic 配置 | orchestration.db は event 中継のみ担当し、domain logic を持たない (過集中防止) |

**Reverse 例外** (G-07 境界明示、FR-DB-SEP-07 準拠): Reverse 機能 (R0-R4 + RGC) は record strand を持たない例外として扱う。既存 code / 設計の逆引きであり、新規 event 生成を伴わないため event log への write 対象外とする (read のみ)。Reverse は "artifact strand を逆方向に辿る操作" であり、orchestration event log への write は発生しない。

**[破壊的変更フラグ]** 既存の `helix_db._write_connection(None)` を直接呼び出す 11 file (lib 8 + top-level CLI 3) は、compatibility_adapter.py が適用されるまでの dual-write 期間中は旧 helix.db への write で動作を維持する。adapter 適用後の 6 db 分離環境では、adapter なしの raw 呼び出しは動作しなくなる。

### 2. Event Sourcing 6 軸判定 + ハイブリッド採用 (G-02 / FR-DB-SEP-02)

6 db を一律に event-sourced にするのではなく、audit / temporal / event ordering / write 頻度 / retention / replay SLO の 6 軸で判定したハイブリッド構成を採用する。

**6 軸判定 matrix**:

| db | audit | temporal | event ordering | write 頻度 | retention | replay SLO | 採用方式 |
|---|---|---|---|---|---|---|---|
| orchestration | ◎ 必須 | ◎ 必須 | ◎ 必須 | 高 | 長期 (1y+) | < 5min | **event-sourced** |
| vmodel | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| scrum | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| plan | ◎ 必須 | △ 部分 | ○ 推奨 | 低 | 長期 (1y+) | < 30min | **hybrid (state snapshot + change log)** |
| backend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |
| frontend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |

**採用決定ルール**: audit + temporal + event ordering の 3 軸が全て ◎ 必須 → event-sourced。1 軸でも × → state-store。その間 → hybrid。

**各 db の採用根拠**:

- **orchestration.db**: phase 遷移 / gate 通過 / agent_slot fire/release は発生順序と時刻が critical。gate 通過の audit trail が法令・品質保証上必須。replay SLO 5min は障害復旧要件から導出 → event-sourced
- **vmodel.db**: V-model 4 artifact の artifact / artifact_link は設計変更の追跡 (temporal) が必須。cross_drive_integrity の event ordering がデータ整合性を担保する → event-sourced
- **scrum.db**: hypothesis 検証の時系列記録と scrum_loop / srf_chain の event ordering が PoC 結果の再現可能性を支える → event-sourced
- **plan.db**: plan / sprint / task は最新 state への高速アクセスが主用途 (temporal 要件は部分的)。change log による audit trail で十分な履歴が得られる → hybrid
- **backend.db**: automation_run / session_telemetry は短期 (90d) の state 管理が主用途。replay 不要 → state-store
- **frontend.db**: ui_component / mock は CI/CD 高頻度更新対応が優先。temporal 要件なし → state-store

**plan.db hybrid の具体形**:

- **state 部分**: SQLite table (plan / sprint / task / wbs) で snapshot 保持。直接 update 可。最新 state の query が高速
- **change log 部分**: plan_change_log table に append (status 遷移 / WBS 追加削除 / sprint complete)。event ordering 保持
- **同期方針**: state update と change log append は同一 transaction とし、不整合は migration mismatch gate と同じ機構で検出する
- **projector 不要**: plan.db 内で state と change log の両方を持つため外部 projector は不要。event-sourced 3 db は projection_state を別 table で持つが、plan.db は内部完結

**L2-MASTER.md との整合**: L2-MASTER.md:36 の旧 "Event Sourcing 含めない / L2 工程群確定後の話題" 記述は、本 ADR の採択と同時 (commit d5bae22) に "Event Sourcing / projector / ADR-018/019 で扱う / PLAN-084 で L1 確定" へ修正済み。orchestration / vmodel / scrum の 3 db に限定した event-sourced 採用であり、全面的な事後採用とは区別する。

### 3. projector 境界 (G-03 / FR-DB-SEP-03)

event-sourced 3 db (orchestration / vmodel / scrum) には projector を配置し、event log から read model を構築する。

**projector 制約**:

| 制約 | 内容 |
|---|---|
| writer API | **禁止**。projector は event 生成 API を持たない。read model 生成専用 |
| cross-projection join | **禁止**。1 projector = 1 read model。依存 projection 間の結合は上位 query layer の責務 |
| replay idempotency | **必須**。dedup key = event_id + projector_id で冪等保証 |
| 配信方式 | async standard。同期は許可リスト 3 件のみ |
| failure isolation | projector failure は self 検知せず、detector が last_processed_event_id を監視 |

**同期許可リスト** (3 件のみ、tl-advisor Round 2 #3 反映):

同期 projector は orchestration 全体の blocking point になりうるため最小限に絞る。同期許可 = 「その projector の処理完了を待たずに次処理を進めると system invariant が破れる」場合のみ。

| 同期 projector | 同期理由 | timeout |
|---|---|---|
| phase projector | phase.yaml 更新は orchestration 全体の同期ポイント。phase 遷移前に projection_state と phase.yaml が一致していないと gate 判定が誤る | 200ms |
| gate projector | gate 通過判定は次 phase 遷移の前提。gate PASS の projection が完了していないと G2/G3/G4 が誤って block される | 200ms |
| agent_slot projector | fire/release は real-time UI / harness 監視に必要。UI 上の slot 空き表示と実際の slot 状態が乖離すると多重 fire が発生する | 200ms |

上記 3 件以外は **async enqueue** とし、caller は 200 OK + warning header を受け取った後、自身の処理を継続する。

**timeout / fallback / lag 境界**:

| 項目 | 値 |
|---|---|
| 同期 projector timeout | 200ms |
| timeout 時 fallback | async queue にエンキュー。caller には 200 OK + `X-Projector-Warning: fallback-to-async` header を返却 |
| lag 警告境界 | last_processed_event_id 差分 100 event 超過 → WARN log + harness_monitor_events に record |
| lag fail-close 境界 | 同 1000 event 超過 → **Phase 4.B (projector + harness_monitor 有効化) 以降**に G2/G3/G4 gate 通過判定を block (gate projector が stale な場合の safety net)。G2/G3 時点では projector 未実装のため本 fail-close は適用されず、G2/G3 ゲートは設計 artifact の存在・契約整合の評価のみを行う |
| lag 時 read 挙動 (同期) | stale data 許容 + `X-Projection-Lag: <n>` warning header 付与 |
| lag 時 read 挙動 (async) | 直近 snapshot 返却 + `Retry-After: <t>` header 付与 |

**G-04 責務境界** (PLAN-085 委譲): detector の 6 db 対応 (既存 14 axis を 6 db each に割り当て + record strand anomaly 系追加) は本 PLAN-084 では責務分離のみ確定する。本格実装は PLAN-085 (④ 問題発見配備) で実施する。以下の責務境界を本 ADR で凍結する。

| detector の境界 | 内容 |
|---|---|
| detector の入力 | 常に event log (record strand)。projector derived state は参照しない |
| artifact strand scan | V-model lint (PLAN-075) の専管。detector は artifact 文書を直接 scan しない |
| feedback channel | orchestration.db 経由で実行者 (agent_slots) へ feedback を送信 |
| 本格配備 | PLAN-085 で実施。本 ADR は責務境界の確立のみ |

### 4. frontend/backend state-store 再判定条件 (G-09 / FR-DB-SEP-09)

frontend.db / backend.db は現時点で state-store を採用する (6 軸判定: audit △ / temporal × / event ordering ×)。将来 event-sourced への昇格条件を以下に凍結する。本項目は ADR-018 の管理下で 6 ヶ月毎に見直す。

**再判定トリガ**:

| 再判定トリガ | 詳細 |
|---|---|
| write 頻度低下 | backend.db / frontend.db の write 頻度が高頻度から中頻度以下 (1 min あたり 100 write 以下の目安) に低下した場合、temporal query 要件の再評価を実施する |
| audit 要件変化 | 法令対応 / compliance で backend.db (audit_log) または frontend.db の audit trail が法的要件として必須化した場合。現状 audit_log は append-only trigger で対応しているが、event envelope での完全記録が必要になった場合に昇格検討 |
| cross-db 参照増加 | backend/frontend → orchestration への参照が cross-db FK 禁止規約を頻繁に違反する事象が継続する場合。projection_state 経由での回避が困難な場合に hybrid 化を検討する |
| 再判定タイミング | 6 ヶ月毎の ADR review。または上記トリガ発生時の臨時 review。PM + TL で判定し、PO 承認を経て ADR-018 を改訂する |

### 5. migration gate 6 段階 (G-06 / FR-DB-SEP-06)

v30 (単一 helix.db) → 6 db 分離は **Strangler Fig + dual-write + compatibility adapter** パターンで段階移行する。

**migration ゲート順序 + 停止条件 + 失敗時 owner**:

| # | ゲート名 | 通過条件 | 停止条件 | 失敗時 owner / 動作 |
|---|---|---|---|---|
| 1 | dual-write start (v31 migration) | orchestration_events + projection_state + event_envelope table 追加完了、既存 v30 table 破壊なし | migration script の sqlite3 error / table 既存 conflict | **owner: Codex se** / rollback (v30 維持、v31 schema drop) |
| 2 | dual-write mismatch gate | 旧 db state と新 event log + projection_state の divergence 0 件 (10000 write 連続) | 1 件でも divergence 検出 | **owner: Codex se** / fail-close (cutover 不可、divergence 解消まで dual-write 継続) |
| 3 | shadow replay 検証 | 過去 1000 event を新 projector で replay → derived state が旧 db state と byte-level 一致 | replay 不一致 / projector exception | **owner: Codex se** / fail-close (projector bug 修正後 retry) |
| 4 | projector lag stabilization | lag < 100 event が連続 24h | lag > 100 event の発生 | **owner: PM (Opus)** / warning (cutover 延期、lag 原因調査) |
| 5 | cutover | 上記 4 ゲート全 PASS + ユーザー (PO) 承認 | ユーザー却下 / 4 ゲートいずれか fail | **owner: PM (Opus) → ユーザー (PO) 承認** / execute (旧 state table tombstone → drop)、または rollback |
| 6 | rollback point | cutover 後 7d 以内に重大 anomaly (data loss / projector down >1h) | anomaly 検出 | **owner: PM (Opus) → ユーザー (PO) 承認** / 旧 db への切り戻し可能 (event log は保持、新 projection は drop) |

**ゲート ownership 分類**:

- ゲート 1-3: 自動判定 (Codex se 実装、条件充足で通過)
- ゲート 4: PM 監視 (lag 監視ツールで 24h 継続確認、人間が lag グラフを確認)
- ゲート 5-6: 人間承認必須 (PM が推奨、PO が最終承認)

**migration 中の不変条件**:

- 既存 ② 実行ハーネス機能 (PLAN-078〜083) は dual-write 期間中も 100% 機能維持
- shadow replay 検証は migration 期間中常時稼働 (一度 PASS して終わりではなく、継続的に実施)
- compatibility_adapter.py が API 互換 100% を担保するまで、既存 11 file (lib 8 + top-level CLI 3) への変更は禁止

**compatibility adapter 対象 file 一覧** (`grep -rln "_write_connection" cli/` 2026-05-17 実行結果、tl-advisor Round 1 #1 反映で top-level CLI 追加):

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

合計: 11 file / 30+ 箇所 (lib 8 + top-level CLI 3、helix_db.py 自身は adapter 定義側で除外)。

**棚卸し方針**: 単発 grep で凍結せず、`grep -rln "_write_connection" cli/` を Phase 4.A 着手時に再実行し、本表に未列挙の callsite が無いことを検証対象とする。中期的には `helix_db._write_connection` 内部で 6 db 経路への routing を完結させ、呼び出し側の列挙を最小化する。

**Phase 4.A smoke test 必須項目**: adapter 適用後に `helix-pr` / `helix-push` / `helix-agent list` の 3 top-level CLI が新 6 db 経路で正常動作することを smoke test で確認する。lib 8 file の path は既存 pytest suite (1622+) で回帰確認。

**compatibility_adapter.py の責務**:

- 既存 `helix_db._write_connection(None)` 呼び出しを 11 file (lib 8 + top-level CLI 3) 全てで透過的に 6 db 経路へ adapt
- API 互換 100% 維持 (上位 11 file (lib 8 + top-level CLI 3) は import 切替のみ、内部ロジック変更不要)
- dual-write 期間中: 旧 helix.db と新 6 db 両方に write し、mismatch gate 検証に使用
- cutover 後: 旧 helix.db への write を停止し、6 db のみへ転送
- adapter 自身が unit test で 11 file (lib 8 + top-level CLI 3) 全 path をカバー (Phase 4.A Exit 条件)

## Consequences

### Positive

- **V-model 検証強化**: vmodel.db が独立することで artifact / artifact_link の event trail が orchestration 系 event と物理分離され、V-model lint (PLAN-075) が独立して replay・検証可能になる。設計 artifact の変更履歴が event log として永続化され、任意時点の artifact state を復元できる
- **audit 完備**: orchestration.db / vmodel.db / scrum.db の 3 db が event-sourced になり、全操作が append-only の audit trail として保持される。改ざん検知は append-only trigger で対応済み (backend.db audit_log は PLAN-074 で実装済み)。event envelope の correlation_id により cross-db trace が可能になる
- **replay 可能性**: event log から任意時点の状態を再構築できる。projector を差し替えることで read model の形式を変更できる (backward compatibility 不要)。障害時の状態復元が event log replay で完結し、バックアップリストアに依存しない
- **entity ownership の明確化**: 6 db の canonical entity 表により「どの data がどの db に属するか」が単一の正本で判定できる。コードレビューで entity ownership 違反を早期検出できる。新機能追加時に entity の配置先判断が ownership 表で即決される
- **cross-db 参照の制御**: projection_state 経由のみを許可することで、cross-db JOIN の暗黙的依存が排除され、db 間の独立性が保たれる。各 db が独立して schema migration 可能になり、vmodel.db の schema 変更が orchestration.db に波及しない
- **compatibility adapter による安全な段階移行**: 既存 11 file (lib 8 + top-level CLI 3) を変更せず adapter 経由で 6 db へ移行できるため、既存テスト (pytest 1622+ / bats / shell) の PASS 維持が容易。dual-write 期間中の mismatch gate により、divergence を検出して cutover を安全に制御できる
- **④ 問題発見配備の前提整備**: 6 db 分離が完成することで PLAN-085 (detector 本格配備) が record strand anomaly を db 単位で独立して監視できるようになる。単一 helix.db では db 横断 anomaly の原因特定が困難だった

### Negative

- **migration 工数増**: 6 段階の migration gate と shadow replay 検証の実装により、Phase 4 が 4.A (migration + adapter) / 4.B (event_log + projector + dual-write) / 4.C (shadow replay + cutover) の 3 sprint に分割される (tl-advisor Round 2 Minor #6 反映)。8-12 セッションの見込みが 8-14 セッションに拡大する
- **projector lag 管理必須**: 同期 projector 3 件の timeout 200ms 管理と lag 境界 (WARN 100 / fail-close 1000 event) の常時監視が運用コストを増加させる。harness_monitor への統合は Phase 4.B に追加され、**Phase 4.B (projector + harness_monitor 有効化) 以降**で lag > 1000 event が発生すると G2/G3/G4 が block されるため、開発フローが停止するリスクを常に持つ。Phase 4.B 完成までは本 lag fail-close は不適用 (Phase 4.A の dual-write 中は projector 未稼働のため block 発火対象外)
- **compatibility adapter 11 file (lib 8 + top-level CLI 3) 追加**: adapter 経由で API 互換を維持するが、dual-write 期間中は旧 helix.db と新 6 db の両方に write するため I/O 負荷が一時的に増加する (ゲート 5 cutover 後に解消)。adapter layer が中間に入ることでデバッグ時のトレースが複雑になる
- **6 db ファイル管理**: 単一 helix.db から 6 file への移行でバックアップ・リストア・デプロイ手順が複雑化する。`.helix/` 配下のファイル命名規則の更新が必要。テスト環境での 6 db セットアップが pytest fixture の変更を伴う可能性がある
- **phase.yaml との二重真実**: Phase 4.C cutover 完了まで、phase.yaml (既存) と orchestration.db projection_state が並存し、二重真実状態になる。ADR-020 (cutover 後の phase.yaml 廃止判断) で解決するが、それまでの期間は両者の整合性を運用で保証する必要がある

### Risks

- **projector 同期失敗時の gate block** (**Phase 4.B 以降適用**): projector lag が 1000 event を超えると G2/G3/G4 の gate 通過判定が全て block される。本 fail-close は **Phase 4.B (projector + harness_monitor 有効化) 以降にのみ適用** され、Phase 4.A 完成までの G2/G3 評価は本 ADR の設計 artifact 存在・契約整合の確認のみで行う。harness_monitor による lag 監視の実装が Phase 4.B 完成時点で機能していない場合、開発プロセス全体が停止するリスク
  - 緩和策: Phase 4.B で projector lag 監視を harness_monitor 統合と同時実装する。Phase 4.A の adapter 先行実装中に lag 監視の skeleton (last_processed_event_id 記録) を準備する。Phase 4.B 完成までは fail-close 不適用とすることで、設計 phase (G2/G3) の評価が runtime 未実装に阻害されないよう分離する
- **dual-write 期間中の mismatch 発見遅延**: divergence gate は 10000 write 連続の監視であり、実際の divergence 発見まで時間を要する場合がある
  - 緩和策: shadow replay (gate 3) を gate 2 と並行稼働させ、divergence を早期検出する。divergence 検出時のアラートを harness_monitor_events に記録し PM に即時通知する
- **compatibility_adapter.py の API 互換失敗**: 11 file (lib 8 + top-level CLI 3) × 30+ 箇所の adapter 適用で一部の呼び出しが新 db 経路に正しくルーティングされない場合、既存テストが破損する
  - 緩和策: adapter テストで 11 file (lib 8 + top-level CLI 3) 全 path をカバーし、API 互換 100% を Phase 4.A Exit 条件とする。既存テスト suite (pytest / bats) を adapter 適用後に全回帰する

## Alternatives considered

### A. 単一 db 維持 (V-model 拡張のみ)

- **内容**: helix.db を分離せず、V-model 強化 (PLAN-075) の schema 拡張のみを継続する。entity ownership は命名規則 (テーブル名プレフィックス等) で管理し、ATTACH は禁止したまま単一 db を拡張する
- **却下理由**:
  - entity ownership が不明確なまま schema が拡張し続けると、cross-db 参照の制御が困難になる。PLAN-074 時点での D-DB EXT / D-API EXT の実装で既に orchestration / backend / frontend の table が 1 ファイルに混在しており、これを放置すると PLAN-085 detector が "どの table が何の責任か" を判定できなくなる
  - orchestration / vmodel / scrum 領域で audit / temporal 要件が高いにもかかわらず同一 db に混在することで、event-sourcing が必要な table と state-store で足りる table が同じ設計方針を強制される。特に backend.db の automation_run (高頻度 write) と orchestration.db の phase (低頻度・高 audit) が混在することで、retention 設計が困難になる
  - V2 構築 5 段階の ③ データベース管理フェーズを回避すると、④ 問題発見配備 (PLAN-085) の db detector が単一 db を前提に実装され、将来の分離コストが指数的に増大する
  - vmodel.db が独立していないと V-model lint (PLAN-075) の replay 検証が orchestration event と混在して精度が低下する。artifact_link の event trail を独立して検証できない

### B. 全 db event-sourced

- **内容**: 6 db 全てを event-sourced にし、state-store と hybrid を使用しない。全 entity の操作を event として append-only で記録し、projector が全 db の read model を構築する
- **却下理由**:
  - backend.db / frontend.db の write 頻度は高く (90d retention / replay SLO = n/a)、全 event を append-only で保持することでストレージ増加とクエリ遅延が生じる。automation_run (CI 1 回あたり複数 write) / session_telemetry (session 毎に高頻度 upsert) は最新 state を高速に返すことが主な用途であり、event replay を必要としない
  - tl-advisor Round 2 の 6 軸判定で backend / frontend が「temporal × / event ordering ×」と判定されており、event-sourced を強制すると projector lag の管理コストが不要に増大する。projector 数が 6 db 全てに比例して増加し、lag fail-close 境界 (1000 event) の監視対象が拡大して運用負荷が高まる
  - plan.db も temporal 要件は部分的であり、hybrid (state snapshot + change log) で十分な audit trail が得られる。plan の status 遷移記録は change log で補完でき、full event-sourced にする必要がない

### C. ATTACH 自由化

- **内容**: cli/helix-* アプリケーション層でも SQLite ATTACH DATABASE を自由に使用し、cross-db JOIN を許可する。migration script だけでなく通常の CLI コマンドからも ATTACH を許容する
- **却下理由**:
  - ATTACH を自由化すると entity ownership の境界が形骸化し、どの table がどの db に canonical に属するかの管理が崩壊する。"便宜上 ATTACH して JOIN する" コードが散在し始めると、projection_state 経由の参照制約が守られなくなる
  - direct cross-db FK が生まれる可能性がある。これは Decision §1 の cross-db FK 禁止規約と根本的に矛盾する。SQLite ATTACH 下でも foreign key 制約は db 内に閉じる必要があり、cross-db の参照整合性を SQLite が保証しない状態での JOIN は data 不整合リスクを生む
  - ATTACH を使用した JOIN は SQLite のトランザクション境界を複雑化し、複数 db に跨る atomic write の rollback 一貫性が保証できなくなる。migration gate 2 (dual-write mismatch gate) の divergence 検出精度も低下する
  - HELIX の長期保守性を考慮すると、entity ownership 境界の明確化は ATTACH 制限なしには維持できない。R-11 (ATTACH 許可範囲の運用 drift) のリスクが顕在化する

### D. 2 db 分離 (orchestration + その他)

- **内容**: orchestration.db のみを分離し、残りを helix.db として維持する。事実上の 2 db 構成にする
- **却下理由**: vmodel.db / scrum.db の event-sourced 採用 (audit / temporal 要件が高い) が実現できない。backend.db / frontend.db の短期 retention 分離も達成できず、6 db 分離の正規化メリットの大半が失われる。PLAN-085 detector の db 単位 anomaly 監視が部分的にしか実現できない。結果的に中途半端な分離になり、将来の 6 db 完全分離コストが残存する

## Related

| ADR / PLAN | 関係 |
|---|---|
| PLAN-084 | 本 ADR の L1 要件確定 PLAN。§2.2-2.6 matrix が本 ADR の根拠源。本 ADR は Phase 2.1 (L2 基本設計) の成果物 |
| ADR-015 | V2 orchestration 文脈。PM 実装禁止・PMO 新設・TL/SE/PE 分離の運用体制を確立。本 ADR はその体制の上で DB 管理を定義する前提 |
| ADR-014 | cli/roles/*.conf を正本とする決定。本 ADR は DB 管理レイヤーであり、role 設定変更は不要。参照のみ |
| ADR-019 | HELIX 二重らせん命名原則。本 ADR と同時起票 (G-08、2026-05-17)。artifact strand (PLAN-075) と record strand (本 ADR) の二重らせんを命名レベルで正式化する |
| ADR-020 | cutover 後の phase.yaml 併存 / 廃止判断。Phase 4.C で起票予定。本 ADR の migration gate 5 (cutover) が完了した後の判断を記録する |
| FR-DB-SEP-01〜09 / AC-DB-SEP-01〜07 | L1-REQUIREMENTS.md §3.9 に記載の L1 受入条件。本 ADR の Decision 1-5 がこれらの受入条件に対応する |
| PLAN-075 | V-model 4 artifact 双方向 trace framework。vmodel.db が独立することで PLAN-075 の artifact / artifact_link の event trail が独立し、replay 検証が精度向上する |
| PLAN-078〜083 | harness 自動統合。compatibility adapter (Decision §5) が保護する対象。agent_slots / harness_monitor / scrum_local / reverse_local / http_api/routes 4 件が adapter 対象 |
| PLAN-085 | detector 本格配備予定 (④ 問題発見配備フェーズ)。本 ADR が G-04 の責務境界を確立し、PLAN-085 が 6 db 単位の anomaly 監視を本格実装する |

## References

- `PLAN-084 §2.2-2.6` matrix (entity ownership / 6 軸判定 / projector 境界 / migration gate / adapter file 一覧、本 ADR の根拠)
- `helix.db schema v30` (migration gate 6 段階の起点。v31 = dual-write start として gate 1 が通過条件になる)
- `docs/v2/L1-REQUIREMENTS.md §3.9` (FR-DB-SEP-01〜09 / AC-DB-SEP-01〜07)
- tl-advisor Round 1-3 反映: 同期許可リスト 3 件確定 (Round 2 #3)、Phase 4 を 3 sprint 分割 (Round 2 Minor #6)、6 軸判定 matrix 本文埋め込み (Round 2 Critical #1)
- `cli/lib/helix_db.py` (compatibility adapter の参照元、`_write_connection` pattern)
- `docs/v2/L2-MASTER.md:36` (旧 "Event Sourcing 含めない" 記述、本 ADR 採択時 commit d5bae22 で "ADR-018/019 で扱う" へ修正済み)

## Revision History

- 2026-05-19 業界 standard 引用 retrofit (W5b-A、PLAN-087 ガードレール準拠)
