# HELIX V3 — L1 要求定義

> **status: 再構築中** / 入力: [L0 企画書](L0-concept.md) / base SSoT = [capture §5 設計 corpus（FR-L1 registry 51）](../audit/2026-06-26-new-base-comprehensive-capture.md)（harness `requirements_v1.2` / `functional-requirements.md`）。
> 対の検証（V-model L1↔L14）: §4 運用テスト設計（OT-* 47、capture §6 test-design）。

本書は **harness の FR-L1 registry（51 件）を V3 の機能要求として採用**し（V3 は harness の Python 再構築なので機能要求は実質一致）、BR/NFR と V3 固有要求（Python 化 / 公開 API / cutover）を加える。完全な FR 51 件表は [capture §5](../audit/2026-06-26-new-base-comprehensive-capture.md)（harness `requirements_v1.2` = FR registry SSoT）を正本とし、本書は群と V3 差分を示す。

## 0. L0 handoff 受理（G0.5 → L1）

L1 は [L0 §6.6](L0-concept.md) の handoff items と [G0.5 判定証跡](../gates/G0.5-l0-to-l1-handoff.md) を受け取り、企画を検証可能な要求へ翻訳する。**L0 handoff 未充足のまま L4 へ進むことは禁止**。本書の追加 BR/FR は、すべて L0 handoff のいずれかに trace される。

| L0 handoff | L1 反映 |
|---|---|
| L1-IN-VISION | BR-V3-08 / FR-AUTO-01/02 |
| L1-IN-SCOPE | FR-TPL / FR-REV / FR-PRM / FR-LRN / FR-UPG |
| L1-IN-NON-GOAL | NFR-V3-08/09 と escalation 境界 |
| L1-IN-VALIDATION | §4 運用テスト設計、L3 受入テスト設計への trace |
| L1-IN-DECISIONS | 採択/保留/見送りの判断を BR/FR/NFR に分解 |

## 1. ビジネス要求（BR — why、concept v3.1 §1 の 4 問題 + L0 handoff が由来）

| ID | 要求 | 由来 |
|---|---|---|
| BR-V3-01 | 設計⇔実装⇔テストの乖離を機械検出（③設計⇔テスト設計 pair の不在を fail-close） | P1 |
| BR-V3-02 | 役割境界を機械強制（worker≠reviewer、read-only role の非破壊） | P2 |
| BR-V3-03 | PoC を Forward へ収束（Discovery S4 → confirmed → 昇格） | P3 |
| BR-V3-04 | 既存実装への破壊的追加を防止（descent-obligation / 回帰 / review-guard） | P4 |
| BR-V3-05 | 検出を「DB が *あるべき集合* を持つこと」で成立（閉ループ） | L0 §2 |
| BR-V3-06 | 公開 API `@~/.helix/core/<path>` を破壊しない / Python 維持 | L0 §3 |
| BR-V3-07 | V2 以下を clean に廃止（系譜の汚れを断つ、idea は盗むがファイル移さない） | charter §4 |
| BR-V3-08 | UT-TDD harness の「人間が AI を安全に使う」仕組みを、HELIX 個人開発版では「AI が機械ガードレール内で安全に自走する」仕組みへ拡張する | L0 §0 |
| BR-V3-09 | 設計書テンプレートを知識メモでなく再利用可能な資産として DB 登録し、doc coverage / gate / detector の入力にする | L0 §3 |
| BR-V3-10 | 自動改善・自動保守 loop により、finding / review / postmortem / test result を次 PLAN・rule・template gap へ変換する | L0 §3 |
| BR-V3-11 | 複数観点 review loop と prompt interpretation loop で、実装前の解釈ズレ・観点漏れ・手戻りを減らす | L0 §3 |
| BR-V3-12 | 将来 upgrade を補助駆動モデルとして扱い、Forward DB へ安全に集約する | L0 §4 |

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

### 2.2 HELIX 個人開発版の拡張要求（AI 自走・設計資産化）

| ID | 要求 |
|---|---|
| FR-AUTO-01 | AI は PLAN / workflow / gate / DB 現在地から次 action を選び、green かつ scope 内なら人間の逐次承認なしに進む。runtime rules §10 境界だけ停止する。 |
| FR-AUTO-02 | plan→execute→verify→review→learn の各 step が DB event / projection / gate result を残し、未登録の成果は完了扱いしない。 |
| FR-TPL-01 | 外部・社内設計書テンプレートを `template_catalog` として source_url / doc_kind / layer / required_sections / pair_test_kind / license_note / freshness を持って登録する。 |
| FR-TPL-02 | template catalog から L0-L6/L8-L14 の `doc_coverage` を生成し、要求定義書・基本設計書・詳細設計書・DB設計書・画面設計書・バッチ設計書・テスト仕様書等の coverage gap を検出する。 |
| FR-TPL-03 | テンプレートは本文コピーではなく、必要項目・粒度・検証観点へ正規化する。出典は provenance として保持し、ライセンス判断が必要な場合は人間承認へ回す。 |
| FR-REV-01 | review loop は PM/TL/SE/QA/security/docs/perf/UX の観点別に evidence を分離し、worker≠reviewer / tests_green_at≤reviewed_at / finding closure を機械検証する。 |
| FR-PRM-01 | prompt interpretation loop は user prompt を scope / acceptance / risk / test / doc coverage / escalation の複数視点へ分解し、解釈差分を PLAN の前段 finding として記録する。 |
| FR-LRN-01 | learning engine は detector findings / review comments / test_result_events / postmortem を learning candidate に変換し、PLAN draft / rule candidate / template gap として Forward に戻す。 |
| FR-UPG-01 | upgrade-assist 駆動は version delta / impact / rollback / staged cutover / forward_return を必須契約にし、retrofit と同じく最終的に Forward DB へ集約する。 |

### 2.3 engine keystone（C1-C6、FR-L1 の機械実体）

| ID | 要求 | keystone |
|---|---|---|
| FR-ENG-01 | schema を単一 registry から生成（62-table = harness 56 + V3 base 2 + HELIX personal 4 / SCHEMA_VERSION / 識別子 fail-close） | C1 |
| FR-ENG-02 | 単一 projection-writer が全 artifact を投影（**rebuild ⊥ append_event**） | C2 |
| FR-ENG-03 | projection は idempotent/deletion-aware/stale-aware/secret-safe | C2 |
| FR-ENG-04 | detector は **pure-function 3 層 + source_kind 宣言**で「あるべき−実在=もれ」、absence=ok=false | C3 |
| FR-ENG-05 | runDoctor 相当が ok=AND で fail-close | C3 |
| FR-ENG-06 | lint-wiring が死蔵 detector を禁止（BFS 到達 or DEFERRED 理由付き） | C4 |
| FR-ENG-07 | baseline ratchet が advisory→fail-close を非後退で昇格 | C5 |
| FR-ENG-08 | doc/workflow を機械契約化 + **auto-enroll rule engine(11 型)** | C6 |

### 2.4 V3 固有（Python 化 / cutover）

| ID | 要求 |
|---|---|
| FR-V3-PORT-01 | harness の TS/zod 実装を **Python/pydantic/stdlib sqlite3** へ再構築（設計意図のみ盗用、契約は独自テストで固定） |
| FR-V3-API-01 | 公開 API（`@~/.helix/core/<path>` / gate ID `G0.5-G14` / VALID_SUB_DOCS slug / rule 型 id）を据え置き |
| FR-V3-CUT-01 | cutover gate（pin inventory / dangling / rollback_preflight / rebuild_dry_run の 4 hard check）を備え、V2 engine + pin する退役 inventory（tests/config）を同 commit 退役（**「107 pytest+49 bats」は harness-era 推定で本 repo（実測 270 pytest+117 bats）と不一致 → 退役 subset を cutover scope から L7 で導出・凍結**。[cutover 設計](../cutover/cutover-design.md)） |
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
| NFR-V3-08 | DDD: template / doc / workflow / finding / review / learning candidate の用語と境界は [domain glossary / bounded context](../engine/domain-glossary.md) を経由し、他 context の固有語を未変換で正本 doc に持ち込まない | doc-contract detector |
| NFR-V3-09 | TDD: L6 機能設計は単体テスト設計と同時 freeze し、L7 は red-first evidence / green digest / review evidence なしに完了しない | UT pair / test_result_events |

### 3.1 L0 handoff からの非機能要件導出（requirements-deriver 適用）

L0 で追加した HELIX 個人開発版の要求は、AI 自走・外部テンプレート・自動改善・upgrade を含むため、L1 で非機能要件として明示する。分類は IPA 非機能要求グレード × ISO/IEC 25010:2023 の二軸で扱う。

| シグナル | 導出 NFR | IPA 分類 | ISO/IEC 25010:2023 | 設計判断 |
|---|---|---|---|---|
| AI が自動で進行する | gate fail-close / audit trail / human escalation boundary | 運用・保守性 / セキュリティ | Reliability / Security / Safety | `planned/executed/verified/reviewed/learned` event を残し、§10 signal で停止 |
| 外部テンプレートを大量に仕入れる | provenance / freshness / license review / normalized sections | 保守性 / セキュリティ | Maintainability / Security | 本文複製ではなく `template_catalog` に正規化し、license 不明は human review |
| 自動改善・自動保守 | learning candidate の根拠・戻し先・破棄理由 | 運用・保守性 | Maintainability / Reliability | Forward return または discard reason を必須化 |
| 複数観点 review loop | 観点別 evidence / worker≠reviewer / unresolved critical closure | セキュリティ / 運用・保守性 | Security / Maintainability | security critical は他観点 pass で相殺しない |
| prompt 複数視点解釈 | scope / acceptance / risk / test / doc / escalation の差分検出 | 運用・保守性 / セキュリティ | Reliability / Security | PLAN 前段 finding として保存し、曖昧さを実装へ持ち込まない |
| upgrade-assist | rollback / staged gate / impact / version delta | 移行性 / 運用・保守性 | Maintainability / Flexibility | retrofit と分離し、将来差分を Forward DB へ収束 |

ISO 25010:2023 の 9 特性チェック: Functional Suitability は L3 AC、Performance Efficiency は detector 実行時間/DB projection、Compatibility は public API 不変、Interaction Capability は UI/agent prompt 体験、Reliability は fail-close と idempotent rebuild、Security は secret/license/escalation、Maintainability は template/learning、Flexibility は upgrade-assist、Safety は destructive/prod/PII signal の人間承認で扱う。

## 4. 運用テスト設計（L1 ↔ L14 pair、OT-* 47 = capture §6 test-design が正本）

| OT-ID | 運用検証 | 対応 |
|---|---|---|
| OT-V3-01 | DB drift = 0 運用監視（plan_registry 等 DB==disk 継続） | BR-05, FR-ENG-02/03 |
| OT-V3-02 | detector green 維持（死蔵 detector 再発しない = lint-wiring 常時 pass） | FR-ENG-06 |
| OT-V3-03 | 公開 API 回帰ゼロ（消費側 loader が `@~/.helix/core` を読める） | BR-06, FR-V3-API-01 |
| OT-V3-04 | baseline 縮小のみ推移（debt 増加検出） | NFR-V3-03 |
| OT-V3-05 | FE governance 発火（§1c per-layer coverage が運用で fail-close） | BR-V3-01, FR-L1-22/29/30 |
| OT-V3-06 | template catalog の freshness / coverage gap が運用で検出され、古いテンプレートや欠落 doc kind が learning candidate へ上がる | FR-TPL-01/02, FR-LRN-01 |
| OT-V3-07 | 自動改善 loop が finding→PLAN draft candidate を生成し、Forward return 不在の candidate を reject する | FR-LRN-01 |
| OT-V3-08 | upgrade-assist 実行後、delta / rollback / staged gate / Forward return が DB に残り、legacy 差分が未収束なら gate fail | FR-UPG-01 |
| OT(harness 47) | L0-L14 通し / team PR / AI 委譲回帰 / 15 画面個別 / G1-trace / provider handover 等 | capture §6 |

## 5. 次工程

→ **L3 要件定義**（FR を AC-FR と対にして要件粒度へ。harness L3 = AC-FR-XX-01/02/03 正常/異常/境界 + 人間判断点）。engine 構造詳細（62-table / projection rule / detector 分類）は L4/L5 で確定。
