---
doc_id: L9-test-design-L4-basic-design-system-test
title: HELIX-workflows V2 L4 基本設計 総合テスト設計
status: frozen
freeze_evidence: "2026-06-02 L0-L3 review + L4 completion session; TL adversarial check; pair docs L14 L12 created; L4-L9 pair; plan_validator 0 ERROR. 2026-06-03 再凍結: L4↔L9 片肺解消 — NFR 6群を per-ID trace 化(TV-NFR-03/04 + TV-IF-03 + ST-NFR-02/03 + ST-IF-04 + TR-IF-05/06 + TR-NFR-AV/OP/MG/PF/SC/SE)、IF-05 永続化境界 + NFR-OP/MG に専用観点付与、trace_symmetry detector で coverage 再計測。2026-06-03 whole-coverage audit re-freeze: orphan18 (全 ST-*) を ST→TV→L4 の正当な2段 trace と semantic 判定 (§7.1)、balance 0.67 は §4 補助指標で合否非影響、audit_verdict=pass (TL+PM)"
owner: QA
process_layer: L9
test_layer: L9
parent_design:
  - docs/v2/L4-basic-design/方式設計.md
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L4-basic-design/データ設計.md
  - docs/v2/L4-basic-design/外部IF設計.md
pairs_design:
  - docs/v2/L4-basic-design/方式設計.md
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L4-basic-design/データ設計.md
  - docs/v2/L4-basic-design/外部IF設計.md
related_process:
  - docs/v2/process/L04-architecture-design-and-system-test-design.md
  - docs/v2/process/L09-system-testing.md
standard_basis:
  - ISO/IEC/IEEE 29119-4
---

# L4 基本設計 総合テスト設計

## 1. 目的と範囲

本書は HELIX-workflows V2 の L4 基本設計 4 文書に対応する L9 総合テスト設計である。L9 では L8 結合テスト完了後のシステム全体を対象に、CLI 入口、workflow 制御、永続化、AI harness、hook、Git / workspace、HTTP 補助 API が L4 の責務分担どおりに連携することを検証する。

対象は総合レベルのテスト観点、テストシナリオ、合格基準、設計項目への trace である。テストコード、fixture の詳細、個別関数の期待値、CLI option 単位の網羅は L7 / L8 / L5 / L6 の対応 artifact に委譲する。

## 2. 対象設計と検証方針

| 対象設計 | L9 で検証する主題 | 総合テスト方針 |
|---|---|---|
| 方式設計 | `cli/helix` を入口に、Bash router、Python application、`helix.db`、hook / harness が責務境界どおりに連携すること | 代表 workflow を end-to-end で実行し、状態・監査・差分出力を横断確認する |
| 機能構成設計 | FR18 件の機能群が入口判定、工程制御、品質監査、継続性、資産統制として破綻なく協調すること | FR 群を機能シナリオへ束ね、主要依存と registry-only 連携を確認する |
| データ設計 | `helix.db` と補助証跡が PLAN、run、gate、audit、session、asset trace を再現可能に保持すること | 実行前後の DB / audit / artifact 関係を照合し、欠落・重複・不整合を検出する |
| 外部IF設計 | 利用者 shell、Codex / Claude harness、Git、SQLite、HTTP 補助 API の境界が許可された方向で動くこと | 外部接続ごとの正常系、失敗系、fail-close、監査証跡を確認する |

## 3. ISO 29119-4 準拠方針

本書は ISO/IEC/IEEE 29119-4 のテスト技法を、L9 総合テスト設計に必要な抽象度へ写像して用いる。

| 技法 | 本書での使い方 | 適用先 |
|---|---|---|
| シナリオテスト | 利用者操作から gate / audit / handover までの一連の流れを検証する | ST-SYS-01, ST-FR-01, ST-IF-01 |
| 状態遷移テスト | PLAN status、handover owner、gate verdict、mode transition の遷移を検証する | ST-SYS-02, ST-DATA-01, ST-FR-04 |
| デシジョンテーブルテスト | gate 判定、plan-only guard、sandbox / approval policy の組合せを検証する | ST-SYS-03, ST-IF-02 |
| 分類木 / 同値分割 | 9 mode、role、FR bucket、外部 IF 種別を代表パターンへ分割する | ST-FR-02, ST-IF-03 |
| 境界値テスト | timeout、許容失敗件数、カバレッジ閾値、ファイル存在数の境界を検証する | ST-NFR-01, ST-DATA-02 |
| エラー推測 | stale handover、schema mismatch、未許可 write、trace 欠落など過去に起きやすい欠陥を狙う | ST-NEG-01, ST-NEG-02 |

## 4. 総合テスト観点

| 観点 ID | 観点 | 主な検証内容 | 優先度 |
|---|---|---|---|
| TV-SYS-01 | 入口統一 | `helix` 入口から workflow / gate / review / handover / code search が想定 command へ接続される | P1 |
| TV-SYS-02 | 層責務 | Bash router、command、Python application、DB、hook / HTTP が L4 の責務境界を越えない | P1 |
| TV-FR-01 | FR18 連携 | code 16 件と registry-only 2 件が機能群として追跡・監査・継続性に寄与する | P1 |
| TV-FR-02 | V-model trace | 設計、実装、テスト設計、テストコードの pair 欠落を検出できる | P1 |
| TV-DATA-01 | 永続化整合 | PLAN、run、gate、audit、session、asset trace の保存と参照が一貫する | P1 |
| TV-DATA-02 | 再開可能性 | session / workspace / handover が中断後に正しい owner と next action を示す | P2 |
| TV-IF-01 | AI harness 境界 | Codex / Claude wrapper が role、sandbox、approval policy、summary を保持する | P1 |
| TV-IF-02 | fail-close | 未許可操作、stale handover、schema mismatch、trace 欠落で停止・差し戻しが起きる | P1 |
| TV-NFR-01 | 性能・安定性 | 代表的な doctor / code find / plan validate が許容時間内に完了する（NFR-PF-01〜04） | P2 |
| TV-NFR-02 | セキュリティ | raw CLI 抑止、hook guard、secret / credential 非露出、Critical / High 欠陥 0 を確認する（NFR-SE-01〜03、NFR-SC-03） | P1 |
| TV-NFR-03 | 運用保守 | auto-deprecation 判定、累積 audit、warn 上限 alert、lineage trace、verify-before-act が機能する（NFR-OP-01〜05） | P2 |
| TV-NFR-04 | 移行・互換進化 | schema_version、冪等 migration、旧新並存、非破壊中断、drift advisory、Strangler 段階置換が成立する（NFR-MG-01〜03、NFR-SC-01〜05） | P1 |
| TV-IF-03 | 永続化境界 | `helix.db` への state / audit / session / asset trace 保存と再読込、schema mismatch fail-close、破損検知が境界どおり動く（IF-05、NFR-AV-02、NFR-MG-02） | P1 |

## 5. テストシナリオ

| シナリオ ID | 対象観点 | 前提 | 手順概要 | 合格基準 |
|---|---|---|---|---|
| ST-SYS-01 | TV-SYS-01, TV-SYS-02 | clean checkout、L4 / L9 doc が存在する | `helix help`、代表 workflow command、`helix code find` を実行し、入口から実体 command / library へ到達することを確認する | 全 command が想定 exit code を返し、未定義入口・重複 dispatch・raw CLI 逸脱がない |
| ST-SYS-02 | TV-SYS-02, TV-DATA-01 | L8 結合テストが完了し DB が利用可能 | 代表 PLAN を読み込み、gate 判定、audit log、session telemetry の関連を追跡する | L4 の層責務どおり、判断は Python application 層に集約され、DB は state 保存だけを担う |
| ST-SYS-03 | TV-IF-01, TV-IF-02 | role / sandbox / approval policy の代表値を準備 | plan-only、approved、workspace-write、read-only の組合せで wrapper の判定を確認する | 明示承認なし write、禁止 path、commit / push が block され、summary marker が保持される |
| ST-FR-01 | TV-FR-01 | FR18 registry と L4 機能構成設計が一致する | Entry and Routing から Plan and Gate Control、Audit and Quality、Runtime and Continuity、Asset and Knowledge Governance までを 1 フローで追跡する | code 16 件は実装接続点が追跡され、registry-only 2 件は統制基準として欠落理由と昇格条件を持つ |
| ST-FR-02 | TV-FR-01, TV-FR-02 | mode 入口、role、layer context の代表入力を準備 | 9 mode 入口判定、context injection、drift routing、Forward 復帰記録を総合的に確認する | 誤 mode への遷移、context 欠落、drift 未分類、Forward 復帰 event 欠落がない |
| ST-FR-03 | TV-FR-02, TV-DATA-01 | 4 artifact trace 対象の設計 / テスト設計を準備 | pair freeze 監査を実行し、L4 4 文書と本 L9 文書の相互参照を検証する | `pairs_test_design` と `parent_design` / `pairs_design` が一致し、trace 欠落が fail として検出される |
| ST-FR-04 | TV-FR-01, TV-IF-02 | gate 条件と TDD 順序の代表 PLAN を準備 | PLAN dependency、TDD 順序、gate verdict、doctor summary、change propagation を横断確認する | テストアフター、依存未完了、balance ratio 後退、review 欠落が gate で止まる |
| ST-DATA-01 | TV-DATA-01 | `helix.db` と監査補助ファイルが利用可能 | PLAN 登録、task run、action log、gate run、audit log、session telemetry、asset trace の関連を確認する | 主エンティティが孤立せず、再現に必要な timestamp / owner / source / result が保存される |
| ST-DATA-02 | TV-DATA-01, TV-DATA-02 | schema version と migration 履歴を準備 | schema mismatch、migration 中断、rollback 境界、asset index 更新前後の状態を確認する | mismatch は検出され、destructive 操作なしで中断理由と再開条件が記録される |
| ST-IF-01 | TV-IF-01 | Codex / Claude / Git / SQLite / HTTP 補助 API の代表接続を準備 | 外部 IF ごとの正常リクエスト相当を流し、入力、出力、監査証跡を確認する | 各 IF が L4 外部IF設計の方向・入口・役割どおりに動き、内部責務を保持しない |
| ST-IF-02 | TV-IF-02, TV-NFR-02 | 未許可 write、raw CLI、secret 参照、stale handover を準備 | guard / hook / wrapper の fail-close を確認する | 禁止操作は block され、secret / credential の値は出力・保存されず、理由が監査ログに残る |
| ST-IF-03 | TV-SYS-01, TV-IF-01 | Git worktree と PR 補助導線を準備 | workspace 分離、diff review、PR 前 gate、summary 出力の代表フローを確認する | workspace 衝突がなく、未 review 差分や gate fail で PR / push 導線が止まる |
| ST-NFR-01 | TV-NFR-01 | 代表規模の docs / code index / DB を準備 | `helix doctor`、`helix code find`、plan validation、pair trace scan の実行時間と安定性を確認する | L4 非機能方針の許容範囲内で完了し、Flaky 率 5% 未満、再実行で同一 verdict を返す |
| ST-NFR-02 | TV-NFR-03 | warn 累積 / doctor / gate / trace 欠落の fixture を準備 | auto-deprecation 判定、累積 audit 完走、warn 上限 alert、lineage trace 充足、verify-before-act 強制を総合確認する（NFR-OP-01〜05） | pass してはならない運用劣化（P0 老廃物残存、warn 上限超過の未 alert、lineage 孤立、verify-before-act 違反）が fail-close される |
| ST-NFR-03 | TV-NFR-04 | schema version、migration 履歴、旧新並存対象を準備 | migration 再実行、中断、rollback 境界、schema mismatch、Strangler 段階置換と kill criteria を確認する（NFR-MG-01〜03、NFR-SC-01〜05） | destructive 操作なしで中断理由と再開条件が記録され、旧新並存・冪等・非破壊が保たれ、互換期間中に drift advisory を返す |
| ST-IF-04 | TV-IF-03 | `helix.db` と監査補助、破損 / mismatch fixture を準備 | CLI から run / audit / session / asset trace を発生させ、SQLite への保存・再読込、schema mismatch・破損検知の証跡化を確認する（IF-05、NFR-AV-02、NFR-MG-02） | 永続化が `helix_db.py` 境界経由で行われ、mismatch / 破損は fail-close され、value は露出せず理由が監査ログに残る |
| ST-NEG-01 | TV-IF-02, TV-DATA-02 | 不整合 fixture を準備 | parent_design 欠落、pairs_design 不一致、存在しない L4 doc、存在しない L9 doc を検出する | いずれも G4 / G9 の blocking issue として報告される |
| ST-NEG-02 | TV-FR-02, TV-NFR-02 | review / security 証跡欠落を準備 | doc-reviewer、tl-advisor、security audit の不足時動作を確認する | P0 / P1 未解消、Critical / High 欠陥、証跡欠落が pass にならない |

## 6. FR18 総合動作・連携検証

| 機能群 | 対象 FR | 総合シナリオ | 合格基準 |
|---|---|---|---|
| Entry and Routing | FR-9MODE-01, FR-CTX-01, FR-DRIFT-01 | 入力 signal から mode 候補を選び、role / layer context を注入し、drift を interrupt / recovery / reverse / Forward へ分類する | mode、context、routing result が同一 task trace に残り、未分類 drift がない |
| Plan and Gate Control | FR-PLAN-01, FR-GATE-01, FR-TDD-01, FR-4ART-01 | PLAN dependency、TDD 順序、gate verdict、4 artifact trace を 1 回の gate 判定へ集約する | 依存未完了、テストアフター、trace 欠落が fail-close される |
| Audit and Quality | FR-DOCTOR-01, FR-GR-01, FR-DOCREVIEW-01, FR-CHANGEPROP-01 | guardrail、doctor、doc review、change propagation を同一 evidence set で突合する | Critical / High 0、P0 / P1 未解消 0、balance ratio 後退 0 |
| Runtime and Continuity | FR-EVT-01, FR-NSM-01, FR-IMPACT-01, FR-MIGR-01 | event 記録、整合スコア、影響範囲 query、migration 状態を中断・再開込みで確認する | event から再開条件を復元でき、migration / impact / score が相互矛盾しない |
| Asset and Knowledge Governance | FR-INV-01, FR-FNREG-01, FR-GLOSSARY-01 | asset inventory が機能 SSoT と用語 SSoT を参照し、registry-only の昇格条件を可視化する | registry-only 2 件が未実装扱いで放置されず、昇格条件または免除理由が記録される |

## 7. L4 設計項目 trace

| Trace ID | L4 文書 | 設計項目 | 検証観点 / シナリオ | 合格基準 |
|---|---|---|---|---|
| TR-ARCH-01 | 方式設計 §2 | システムコンテキスト、外部主体、`cli/helix` 入口 | TV-SYS-01 / ST-SYS-01 | 利用者、Codex、Claude、Git、SQLite、L4/L9 文書群の接続が確認できる |
| TR-ARCH-02 | 方式設計 §3 | 正本分離、入口統一、ポリシー集約、永続化、hook / harness 連携 | TV-SYS-02 / ST-SYS-02 | 文書正本、実装、DB state、hook の責務が混在しない |
| TR-ARCH-03 | 方式設計 §4 | 層構成と責務境界 | TV-SYS-02 / ST-SYS-02 | Bash router、command、Python application、DB、統合層の境界逸脱がない |
| TR-ARCH-04 | 方式設計 §5 | Workflow Control、Runtime Governance、Audit and Persistence、Handover and Workspace、Automation API | TV-FR-01 / ST-FR-01 | 主要ブロックが FR18 機能群と連動して確認できる |
| TR-ARCH-05 | 方式設計 §7 | NFR 6 群（可用性・移行・運用保守・性能・互換拡張・セキュリティ）全体方針 | TV-NFR-01〜04, TV-IF-03 / ST-NFR-01〜03, ST-IF-04, ST-IF-02 | NFR 6 群が各々 1 件以上の観点・シナリオへ接続される（下記 TR-NFR-* で個別 trace） |
| TR-FUNC-01 | 機能構成設計 §2 | code 16 件 / registry-only 2 件 | TV-FR-01 / ST-FR-01 | FR18 の分類が L3 registry と一致し、registry-only の扱いが明示される |
| TR-FUNC-02 | 機能構成設計 §3 | 5 機能群 | TV-FR-01 / ST-FR-01 | 各機能群の主責務と相互依存が総合フローで確認できる |
| TR-FUNC-03 | 機能構成設計 §4 | FR 一覧と主な連携先 | TV-FR-01 / ST-FR-01, ST-FR-04 | FR ごとの連携先が実行 trace または統制 trace に現れる |
| TR-FUNC-04 | 機能構成設計 §5 | 機能間連携、mode / context / drift / plan / gate / doctor の流れ | TV-FR-01, TV-FR-02 / ST-FR-02, ST-FR-04 | 入口から監査までの連携が中断なく追跡できる |
| TR-DATA-01 | データ設計 §2 | 5 データ領域 | TV-DATA-01 / ST-DATA-01 | Plan Governance、Execution Tracking、Automation Audit、Workspace、Asset Trace が保存される |
| TR-DATA-02 | データ設計 §3 | 主要テーブル概要 | TV-DATA-01 / ST-DATA-01 | 主要テーブル間に孤立・重複・欠落がない |
| TR-DATA-03 | データ設計 §4 | エンティティ関連 | TV-DATA-01 / ST-DATA-01 | PLAN、task、automation、session、asset の関連が再現できる |
| TR-DATA-04 | データ設計 §5 | PLAN と実行の流れ、資産索引の流れ | TV-DATA-01, TV-DATA-02 / ST-DATA-01, ST-DATA-02 | 実行前後の状態遷移と asset trace が一致する |
| TR-IF-01 | 外部IF設計 §2 | IF-01〜IF-06 外部接続一覧 | TV-IF-01 / ST-IF-01 | 各 IF の方向、入口、役割が実行証跡と一致する |
| TR-IF-02 | 外部IF設計 §3 | CLI、AI harness、VCS、DB、HTTP 境界 | TV-IF-01, TV-IF-02 / ST-IF-01, ST-IF-02 | HELIX 内責務と接続先責務が交差しない |
| TR-IF-03 | 外部IF設計 §4 | CLI 入口、Codex / Claude harness、Git / workspace、SQLite、HTTP API | TV-IF-01 / ST-IF-01, ST-IF-03 | 主要 IF が正常系で連携し、監査証跡を残す |
| TR-IF-04 | 外部IF設計 §6 | IF ごとの制約 | TV-IF-02, TV-NFR-02 / ST-IF-02, ST-NEG-02 | 明示承認なし write、未許可 tool、workspace 衝突、schema mismatch が fail-close される |
| TR-IF-05 | 外部IF設計 §4 / §6.1 | IF-05 SQLite `helix.db` 永続化境界（`helix_db.py`） | TV-IF-03 / ST-IF-04 | state / audit / session / asset trace が境界経由で保存・再読込され、mismatch / 破損が fail-close される |
| TR-IF-06 | 外部IF設計 §2 / §4 | IF-02 Codex / IF-03 Claude / IF-04 Git の各接続 | TV-IF-01 / ST-IF-01, ST-IF-03 | IF-02/03/04 が方向・入口・役割どおり連携し内部責務を保持しない |
| TR-NFR-AV | 方式設計 §7 / データ §5.3 | NFR-AV-01〜03 可用性（CLI 起動、DB 整合、中断再開） | TV-IF-03, TV-NFR-01 / ST-IF-04, ST-DATA-02 | DB 整合（NFR-AV-02）と中断再開（NFR-AV-03）が総合系で確認できる（CLI 起動率 NFR-AV-01 は L14 OT-18 と分担） |
| TR-NFR-OP | 方式設計 §7 | NFR-OP-01〜05 運用保守 | TV-NFR-03 / ST-NFR-02 | auto-deprecation / 累積 audit / warn 上限 / lineage / verify-before-act が機能し劣化が fail-close される |
| TR-NFR-MG | 方式設計 §7 / データ §5.3 | NFR-MG-01 / NFR-MG-02 / NFR-MG-03 移行（schema_version / 冪等 / 非破壊 / Strangler） | TV-NFR-04, TV-IF-03 / ST-NFR-03, ST-IF-04 | migration が冪等・非破壊で、中断 / rollback / mismatch が destructive 操作なしで再開可能 |
| TR-NFR-PF | 方式設計 §7 | NFR-PF-01〜04 性能 | TV-NFR-01 / ST-NFR-01 | 代表 command が許容時間内、Flaky 率 5% 未満、再実行同一 verdict |
| TR-NFR-SC | 方式設計 §7 | NFR-SC-01〜05 互換・拡張 | TV-NFR-04 / ST-NFR-03 | 旧新並存・互換期間 drift advisory・段階置換 kill criteria が成立する |
| TR-NFR-SE | 方式設計 §7 | NFR-SE-01〜03 セキュリティ | TV-NFR-02 / ST-IF-02, ST-NEG-02 | raw CLI 抑止、secret 非露出、未許可 write block が総合系で確認できる |

### 7.1 whole-coverage audit — orphan semantic 判定 (2026-06-03 re-freeze)

`trace_symmetry` detector の L4↔L9 実測: coverage 100% / missing_pair 0 / balance_ratio 0.67 / orphan_test 18（全 ST-*）。本節は [verification-strategy §11.5](../L1-requirements/helix-workflows-verification-strategy.md) の `semantic_gate.orphan_assessment` 証跡である。

- **判定: orphan ではない（excluded_with_reason）**。ST-*（シナリオテスト、§5）は各々 TV-*（テスト観点、§4）を verify し、TV-* が本 §7 trace 表で L4 設計項目に紐づく。すなわち **ST-* → TV-* → L4 の 2 段（推移）trace** であり、ST-* は L4 への直接 backlink を持たない設計（シナリオは観点経由で設計に紐づく、というテスト設計の意図）。
- detector は ST-* の L4 *直* backlink を探すため間接 trace を辿れず orphan 計上するが、これは真の片肺ではない（coverage 100% / missing_pair 0 が forward 完備を示す）。
- balance_ratio 0.67 はこの 2 段 trace 構造に由来する補助指標であり、verification-strategy §4 により **合否主判定にしない**（dashboard / warning のみ）。
- **対応**: ST-* への L4 直 backlink は追加しない。detector の ST→TV→L4 推移 trace 解決は Phase3 の fail-close gate 化と同時に実装する（deferred finding DF-WCAUDIT-L4L9-001）。
- **audit_verdict = detector_clean（coverage100 / missing0 / preflight pass、必要条件）AND semantic_pass（orphan は正当な2段 trace、十分条件）= pass**。approvers: TL + PM（tl-advisor 諮問2回 passed）。

## 8. G4 / G9 合格基準

| ゲート | 判定項目 | 合格基準 |
|---|---|---|
| G4 基本設計凍結 | L4↔L9 pair freeze | L4 4 文書の `pairs_test_design` が本書を指し、本書の `parent_design` / `pairs_design` が L4 4 文書を列挙する |
| G4 基本設計凍結 | trace 完備 | §7 trace 表で L4 4 文書の主要設計項目が 1 件以上の観点・シナリオ・合格基準へ接続される |
| G4 基本設計凍結 | セキュリティ① | raw CLI 抑止、secret / credential 非露出、未許可 write block の総合観点が存在する |
| G9 総合検証 | システム総合動作 | ST-SYS / ST-FR / ST-DATA / ST-IF / ST-NFR / ST-NEG が実行され、P1 シナリオが全 pass する |
| G9 総合検証 | 品質レベル | L9 実行時のテスト品質は T4 を目標とし、P1 クリティカルパス 100%、Flaky 率 5% 未満、Critical / High 0 を満たす |
| G9 総合検証 | 差し戻し条件 | L4 設計違反は L4 へ、L9 テスト設計不足は本書へ、L5 / L6 契約不足は該当設計へ差し戻す |

## 9. 未検出リスク

| リスク | 内容 | 緩和策 |
|---|---|---|
| L5 / L6 詳細未確定による実行粒度不足 | 本書は L4 総合レベルの設計であり、payload、DDL、関数仕様の詳細は含まない | L9 実行前に L5 / L6 / L8 artifact と突合し、未確定箇所を blocking issue として扱う |
| 外部実行器の環境差異 | Codex / Claude / GitHub Actions / MCP の実行環境差で結果が変わる可能性がある | wrapper と hook の契約を基準にし、provider 固有差分は外部 IF の異常系で記録する |
| 性能基準の実測不足 | L4 では具体的な閾値が限定的であり、代表 command の実測が後続工程に残る | L9 実行時に baseline を採取し、閾値が不足する場合は NFR / L4 へ差し戻す |
| registry-only FR の過小検出 | FR-FNREG-01 / FR-GLOSSARY-01 は実行主体がなく、総合テストで見逃されやすい | inventory / doctor の統制基準として観測し、昇格条件または免除理由を必ず検査する |

## 10. 自己検証チェックリスト

- [x] 本書が `docs/v2/L9-test-design/L4-basic-design-総合テスト設計.md` に存在する。
- [x] frontmatter `parent_design` に L4 4 文書がすべて列挙されている。
- [x] frontmatter `pairs_design` に L4 4 文書がすべて列挙されている。
- [x] L4 4 文書の `pairs_test_design` が本書を逆参照している。
- [x] §7 trace 表が 4 文書すべての主要設計項目をカバーしている。
- [x] 禁止された比喩表現を使用していない。
