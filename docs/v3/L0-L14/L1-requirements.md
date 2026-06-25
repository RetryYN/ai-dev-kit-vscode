# HELIX V3 — L1 要求定義

> **status: 再構築中** / 入力: [L0 企画書](L0-concept.md) / base SSoT = [capture §5 設計 corpus（FR-L1 registry 51）](../audit/2026-06-26-new-base-comprehensive-capture.md)（harness `requirements_v1.2` / `functional-requirements.md`）。
> 対の検証（V-model L1↔L14）: §4 運用テスト設計（OT-* 47、capture §6 test-design）。

本書は **harness の FR-L1 registry（51 件）を V3 の機能要求として採用**し（V3 は harness の Python 再構築なので機能要求は実質一致）、BR/NFR と V3 固有要求（Python 化 / 公開 API / cutover）を加える。完全な FR 51 件表は [capture §5](../audit/2026-06-26-new-base-comprehensive-capture.md)（harness `requirements_v1.2` = FR registry SSoT）を正本とし、本書は群と V3 差分を示す。

## 1. ビジネス要求（BR — why、concept v3.1 §1 の 4 問題が由来）

| ID | 要求 | 由来 |
|---|---|---|
| BR-V3-01 | 設計⇔実装⇔テストの乖離を機械検出（③設計⇔テスト設計 pair の不在を fail-close） | P1 |
| BR-V3-02 | 役割境界を機械強制（worker≠reviewer、read-only role の非破壊） | P2 |
| BR-V3-03 | PoC を Forward へ収束（Discovery S4 → confirmed → 昇格） | P3 |
| BR-V3-04 | 既存実装への破壊的追加を防止（descent-obligation / 回帰 / review-guard） | P4 |
| BR-V3-05 | 検出を「DB が *あるべき集合* を持つこと」で成立（閉ループ） | L0 §2 |
| BR-V3-06 | 公開 API `@~/.helix/core/<path>` を破壊しない / Python 維持 | L0 §3 |
| BR-V3-07 | V2 以下を clean に廃止（系譜の汚れを断つ、idea は盗むがファイル移さない） | charter §4 |

## 2. 機能要求（FR — harness FR-L1 registry 51 を採用、capture §5 が全件正本）

### 2.1 FR-L1 registry 群（51 件、P0:19 / P1:24 / P2:8）

| 群 | FR-L1 | 要旨 |
|---|---|---|
| V-model/TDD/trace 中核(P0) | 01-03,06,13 | V字工程 PLAN 管理 / TDD 強制（テストファースト）/ V字双方向 trace 4 artifact / 本線 state 一元 / Forward 工程 |
| gate/state/検出(P0) | 04,05,07,08,18 | kind+generates+requires / 決定論 static gate(gate-checks.yaml) / state 自動登録(5 hook+session-log+forced-stop) / 検出→mode routing / 横断検出 doctor 集約 |
| AI ガード/Recovery(P0) | 09,10,11,12 | agent guard(allowlist/budget/lock) / Recovery 収束 / 横断 4 機構 / L 単位文脈注入(orchestration_mode 5 値) |
| 駆動 workflow | 14-16,23-27 | Reverse(R0-R4) / Discovery(S0-S4) / Incident / Scrum / Add-feature / Refactor / Retrofit / Research |
| CI/観測/学習 | 17,19,20 | CI/PR 連携(local gate→CI→branch protection) / Learning Engine / 観測計測層 |
| テスト観点/FE | 21,22 | W字テスト観点 gate / FE detector 5 軸(mock-promotion/token-drift/a11y/visual/state-transition) |
| W/画面/UX | 28,29,30 | UT-TDD W 2 段設計 / 画面設計 workflow(L2) / フロントデザイン UX(L10, tokens SSoT) |
| context/資産棚卸し | 31-35 | context 0.70 fresh 再起動 / フォルダ構成 / 資産棚卸し / 穴優先順位 / 基盤可視化 |
| 評価/推挙 | 36-39,43 | skill 評価 / model・effort 推挙 / model 評価(opt-in) / タスク難易度 / PoC 成功率 |
| drive/provider | 40,41,42,44 | drive 別 state 分離 / drive 自動判定 / provider 間引継ぎ(Claude↔Codex) / 途中導入 onboarding |
| 品質強化(P0/P1) | 45,46-49,50,51 | **doc-reviewer 必須召喚(G1/G3/G7/G11 fail-close)** / 内部資産 UT-TDD 化(roster/skill/command/drift lint) / DDD/TDD 厳格化 automation / artifact progress color projection |

### 2.2 engine keystone（C1-C6、FR-L1 の機械実体）

| ID | 要求 | keystone |
|---|---|---|
| FR-ENG-01 | schema を単一 registry から生成（58-table = harness 56 + V3 2 / SCHEMA_VERSION / 識別子 fail-close） | C1 |
| FR-ENG-02 | 単一 projection-writer が全 artifact を投影（**rebuild ⊥ append_event**） | C2 |
| FR-ENG-03 | projection は idempotent/deletion-aware/stale-aware/secret-safe | C2 |
| FR-ENG-04 | detector は **pure-function 3 層 + source_kind 宣言**で「あるべき−実在=もれ」、absence=ok=false | C3 |
| FR-ENG-05 | runDoctor 相当が ok=AND で fail-close | C3 |
| FR-ENG-06 | lint-wiring が死蔵 detector を禁止（BFS 到達 or DEFERRED 理由付き） | C4 |
| FR-ENG-07 | baseline ratchet が advisory→fail-close を非後退で昇格 | C5 |
| FR-ENG-08 | doc/workflow を機械契約化 + **auto-enroll rule engine(11 型)** | C6 |

### 2.3 V3 固有（Python 化 / cutover）

| ID | 要求 |
|---|---|
| FR-V3-PORT-01 | harness の TS/zod 実装を **Python/pydantic/stdlib sqlite3** へ再構築（設計意図のみ盗用、契約は独自テストで固定） |
| FR-V3-API-01 | 公開 API（`@~/.helix/core/<path>` / gate ID `G0.5-G14` / VALID_SUB_DOCS slug / rule 型 id）を据え置き |
| FR-V3-CUT-01 | cutover gate（pin inventory / dangling detector / rollback）を備え、V2 + pin する 107 pytest+49 bats+config を同 commit 退役 |
| FR-V3-CFG-01 | HELIX 設定を harness の workflow 契約形式へ差し替え（FR-ENG-08 に合わせる） |

## 3. 非機能要求（NFR — harness nfr-grade 採用、IPA グレード × ISO 25010）

| ID | 要求（グレード） | 検証方向 |
|---|---|---|
| NFR-V3-01 | projection は idempotent/deletion/stale を最優先契約（Lv2 信頼性） | 再実行不変・削除反映・stale 検出の単体 |
| NFR-V3-02 | 物理 FK は同一 DB 内のみ（境界越え=logical ref + detector） | schema レビューで cross-DB FK ゼロ |
| NFR-V3-03 | fail-close 昇格は非後退（baseline 縮小のみ） | ratchet テストで増加 reject |
| NFR-V3-04 | cross-platform 3OS / 4 実行 mode 非依存（NFR-01/03 相当） | OS×mode マトリクス |
| NFR-V3-05 | fail-close = exit 1/2、session-log = fail-open（NFR-06） | guard/gate と log の別 |
| NFR-V3-06 | 役割分離 worker≠reviewer（NFR-11）/ 統合セキュリティ（NFR-17: secret-scan + OWASP Agentic Top10 + human oversight） | review tier / agent-guard / secret 境界 |
| NFR-V3-07 | TS→Python は設計意図のみ盗用、契約は独自テストで固定（等価ズレ防止） | parity でなく契約テスト |

## 4. 運用テスト設計（L1 ↔ L14 pair、OT-* 47 = capture §6 test-design が正本）

| OT-ID | 運用検証 | 対応 |
|---|---|---|
| OT-V3-01 | DB drift = 0 運用監視（plan_registry 等 DB==disk 継続） | BR-05, FR-ENG-02/03 |
| OT-V3-02 | detector green 維持（死蔵 detector 再発しない = lint-wiring 常時 pass） | FR-ENG-06 |
| OT-V3-03 | 公開 API 回帰ゼロ（消費側 loader が `@~/.helix/core` を読める） | BR-06, FR-V3-API-01 |
| OT-V3-04 | baseline 縮小のみ推移（debt 増加検出） | NFR-V3-03 |
| OT-V3-05 | FE governance 発火（§1c per-layer coverage が運用で fail-close） | BR-V3-01, FR-L1-22/29/30 |
| OT(harness 47) | L0-L14 通し / team PR / AI 委譲回帰 / 15 画面個別 / G1-trace / provider handover 等 | capture §6 |

## 5. 次工程

→ **L3 要件定義**（FR を AC-FR と対にして要件粒度へ。harness L3 = AC-FR-XX-01/02/03 正常/異常/境界 + 人間判断点）。engine 構造詳細（58-table / projection rule / detector 分類）は L4/L5 で確定。
