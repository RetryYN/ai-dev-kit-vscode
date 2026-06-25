# HELIX V3 — L4 基本設計（外部設計）

> **status: draft**（TL review → freeze 前 / 一部 inventory は L5/L6 で fork 抽出反映）
> 入力: [L3 要件定義](L3-requirements-spec.md)（REQ + AC）
> 対の検証（V-model L4↔L9）: §6 総合テスト設計
> engine keystone 契約の詳細は `docs/v3/engine/` を正本（本書は system 分解とインタフェース）

本書は V3 engine を**コンポーネントに分解**し、責務・インタフェース・データフロー・主要設計判断を確定する。テーブル群・detector 一覧の具体 inventory は **L5 詳細設計 / L6 機能設計**で fork 抽出（`docs/research/2026-06-25-fork-engine-design-extract.md`）を反映して確定する。

---

## 0. 位置づけ

V3 engine は L0 §2 の閉ループ doctrine を 6 コンポーネントで実体化する。fork(TS) の設計意図を盗むが、**Python/SQLite の HELIX オリジナル設計**として分解する（fork のクラス構成を写経しない＝NFR-V3-05）。

## 1. コンポーネント分解

| ID | コンポーネント | 責務 | 主インタフェース | 対応 REQ |
|---|---|---|---|---|
| **C1** | schema-registry | 全テーブル DDL を単一定義から生成。SCHEMA_VERSION 管理。物理 FK 同一 DB のみ | `build_ddl() -> str` / `SCHEMA_VERSION` / `tables() -> [TableDef]` | REQ-SCH-01/02/03 |
| **C2** | projection-writer | doc/workflow/code/test/FR/設計 を rule で DB へ投影。**rebuild ⊥ append_event**・idempotent/deletion/stale/secret-safe | `rebuild_projection(db, sources)` / `append_event(db, event)` / `project_<kind>(...)` | REQ-PRJ-01〜06 |
| **C3** | detector-runner / doctor | **pure-function 3 層**（analyze/load/messages）+ `source_kind` 宣言で「あるべき−実在=もれ」を出し ok=AND で集約 | `run_doctor(db) -> DoctorResult{ok, findings[]}` | REQ-DET-01/02/03 |
| **C4** | lint-wiring | 実行口から BFS 到達不能な detector を死蔵として禁止。DEFERRED 明示 | `check_wiring(registry, entrypoints) -> WiringResult` | REQ-WIR-01/02 |
| **C5** | baseline-ratchet | advisory→fail-close を非後退（縮小のみ）で昇格 | `ratchet(current, baseline) -> {regressed, allowed}` | REQ-RAT-01/02 |
| **C6** | doc/workflow contract parser | frontmatter/ID/必須セクション/forward_return を機械パース | `parse(path) -> Contract` / `validate(Contract) -> [Violation]` | REQ-DOC-01/02/03 |

> C1-C6 各々の入出力契約・不変条件（DbC）は `docs/v3/engine/{schema-registry,projection-writer,detector-wiring,baseline-ratchet,doc-workflow-rules}.md` を正本とする（本書はインタフェース署名まで）。

## 2. データフロー（閉ループ）

```
[ doc / workflow / code / test / 設計 (機械契約 = C6 パース) ]
        │  parse + validate
        ▼
[ C2 projection-writer ]  ──rebuild(idempotent/deletion/stale)──▶  [ SQLite DB (C1 schema, SSoT) ]
                                                                          │ query「あるべき集合」
                                                                          ▼
[ C4 lint-wiring (死蔵禁止) ] ──登録保証──▶ [ C3 detector-runner / doctor (ok=AND) ]
                                                                          │ findings
                                                                          ▼
                                              [ C5 baseline-ratchet (非後退昇格) ]
                                                                          │ exit code
                                                                          ▼
                                              [ 実行口: helix doctor / push gate / CI ]
```

要点: detector（C3）は file を見ず **DB（C1 が定義し C2 が満たす）を query** する。これが「DB が *あるべき集合* を持つから検出が成立する」の機械的実体。

## 3. 外部インタフェース

| IF | 内容 | 制約 |
|---|---|---|
| CLI 実行口 | `helix doctor`（C3 集約）/ push gate / CI が exit code で合否判定 | RUNTIME_ENTRYPOINTS として C4 の BFS 起点 |
| 公開 API | `@~/.helix/core/<path>` import（消費側 loader が直接読む） | **据え置き厳守**（BR-V3-03 / REQ-DST-01）。core-manifest⇔setup.sh⇔loader 一致を C3 detector で検証 |
| DB | `.helix/helix.db`（SQLite, gitignored runtime state） | rebuildable projection（捨てて再生成可）。Phase 5 cutover で旧 DB 破棄 |
| automation | hook/CLI が artifact 変更時に C2 を起動（Phase 6） | projection 起動は冪等前提 |

## 4. 主要設計判断（ADR 候補）

| # | 判断 | 根拠 |
|---|---|---|
| D-01 | **Python/SQLite 維持**（fork は TS/Bun だが取らない） | 公開 API・テスト資産保護（BR-05） |
| D-02 | **物理 FK は同一 DB 内のみ**、境界越えは logical reference + consistency detector | `HELIX_DB_CUTOVER` cross-DB FK 物理破綻の教訓（NFR-V3-02） |
| D-03 | **projection は rebuild ⊥ append_event**: projection table は全消し再投影（idempotent 最優先）/ append_event table は冪等追記（時系列監査の証跡） | projection-only では red-first/監査の履歴要求を満たせない（TL C-1, NFR-V3-01） |
| D-04 | **fail-close は baseline ratchet 経由**で段階昇格（初手 advisory） | count-pin ripple / debt 移行の安全弁（NFR-V3-03） |
| D-05 | **detector は source_kind 宣言**（db_projection/file_snapshot/hybrid）、core は pure function・I/O は loader 隔離・absence=ok=false | clean harness は file/DB 混在が実態。「DB-only」でなく source 宣言 + pure + ok=AND で厳格性担保（TL C-3） |
| D-06 | **FE 設計ガバナンスを harness から盗む**（§1c per-layer / frontend-design-coverage / screen-impl-pair-freeze）、実 UI 描画のみ greenfield | charter D7 訂正（FE は HELIX 独自優位でなく harness 保有） |
| D-07 | **doc/workflow は機械契約 + 13-14 駆動 mode + auto-enroll rule engine** | 機械登録の前提（FR-ENG-08） |

> D-01〜D-06 のうち不可逆な大局判断（D-01 スタック / D-02 FK 方針）は ADR 起票候補。

## 5. capture で確定済の inventory（L5/L6 で詳細降下）

clean harness の網羅 capture（[capture §B3](../audit/2026-06-26-new-base-comprehensive-capture.md)）で実体が確定済。L5/L6 はこれを Python へ降ろす:

- **テーブル inventory**: **56 table**（core 27 / evaluation 10 / graph 20）+ 41 index、各 table は projection/append_event/config 分類 → C1/L5。
- **projection rule 表**: artifact 種別 → table と logical_key/stale_key/delete_scope → C2/L5。
- **detector inventory**: **~60 detector**（FE/descent/trace/graph/verification/plan/gate/governance）を pure-function 3 層 + source_kind で分類 → C3/L6（FN-* + DbC）。
- **enum SSoT**: 全 enum（Kind 12/Layer 16/V_MODEL_PAIRS 6/VALID_SUB_DOCS/Drive 5/...）→ C1 enums.py。
- **workflow 契約 schema**: frontmatter / 必須セクション / forward_routing / 13-14 mode → C6/L5。

## 6. 総合テスト設計（L4 ↔ L9 pair・対の検証）

system レベルの end-to-end シナリオ（コンポーネント結合）:

| ST-ID | シナリオ | 対応 |
|---|---|---|
| ST-V3-01 | doc を 1 件追加 → C6 parse → C2 rebuild → DB に行が増える → C3 が「もれなし」を返す | C2+C3+C6 結合 |
| ST-V3-02 | doc を 1 件削除 → rebuild → DB 行が消え orphan 0、C3 が整合を保つ | REQ-PRJ-03 結合 |
| ST-V3-03 | 「あるべき」設計を 1 件 DB から抜く（実 artifact 削除）→ C3 が欠落を検出し doctor fail | 閉ループ end-to-end |
| ST-V3-04 | 配線していない detector を C3 に足す → C4 が死蔵検出で全体 fail | C3+C4 結合 |
| ST-V3-05 | baseline を増やす → C5 が reject、減らす → 通る | C5 |
| ST-V3-06 | 公開 API パス参照（消費側 loader 模擬）→ 解決成功（回帰なし） | REQ-DST-01 |
| ST-V3-07 | rebuild 2 回 → DB diff 空（idempotent） | REQ-PRJ-02 |

## 7. 次工程

→ **L5 詳細設計**（C1 テーブル inventory / C2 projection rule / C6 workflow 契約 schema を fork 抽出反映で確定。結合テスト設計と対）→ **L6 機能設計**（C3 detector を関数粒度 + DbC で確定。単体テスト設計と対）。
