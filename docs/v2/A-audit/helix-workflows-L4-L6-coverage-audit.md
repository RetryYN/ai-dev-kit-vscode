---
title: "HELIX-workflows V2 L4/L5/L6 設計カバレッジ監査"
status: draft
created: 2026-05-30
process_layer: A-audit
related:
  - recovery-2026-05-30-design-coverage-baseline
  - skills/workflow/doc-system-architect/references/design-coverage-baseline.md
auditor: pmo-project-explorer
audit_scope:
  - docs/v2/L4-architecture/helix-workflows-system-architecture.md
  - docs/v2/L4-architecture/helix-workflows-functional-design.md
  - docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
  - docs/v2/L5-internal-design/helix-workflows-physical-data-design.md
  - docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md
  - docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
  - docs/v2/L6-functional-design/helix-workflows-class-module-command-design.md
  - docs/v2/L6-functional-design/helix-workflows-function-spec-design.md
  - docs/v2/L6-functional-design/helix-workflows-edge-case-design.md
---

# HELIX-workflows V2 L4/L5/L6 設計カバレッジ監査

## §1 採点サマリ表（23 項目）

### L4 基本設計（9 項目）

| ID | 成果物 | 必須/推奨 | 判定 | evidence file:§ / 根拠 | 一言 |
|---|---|---|---|---|---|
| L4-01 | システムコンテキスト図 (外部境界・アクター) | 必須 | 部分 | system-architecture.md §0.1 arc42§3 対応 (L4 §3 Context → cli/skills/HELIX-workflows の三層構造 §1.1)。専用コンテキスト図節なし、表形式でカバー | 三層表は存在するが arc42§3 相当の境界図として独立した図/節が薄い |
| L4-02 | ビルディングブロック図 (主要コンポーネント・責務) | 必須 | 充足 | system-architecture.md §1.1 三層構造表 + §3.1 cli/lib module 表。arc42§5 Mandatory section に相当する責務割当が表形式で完備 | §1.1/§3.1 で全コンポーネントと責務を網羅 |
| L4-03 | ADR | 必須 | 充足 | system-architecture.md §2.1 PLAN⊃ADR 併存、frontmatter `adr_snapshot: ADR-044`。ADR-044/ADR-045 も存在確認済 | ADR-044/045 が L4 レベルの意思決定を凍結済 |
| L4-04 | デプロイ/方式設計 | 本番運用ありなら必須 | 充足 (N/A 扱い) | system-architecture.md §0.1 arc42§7 対応 `→ .helix runtime state + helix.db + hook`。HELIX は CLI ローカルツールのため本番サーバデプロイが存在せず、N/A 宣言相当。§7.2 配布後の更新方針で代替 | CLI ローカルツールの性質上 N/A 相当 |
| L4-05 | Stakeholder×Concern マトリクス | 推奨 | 部分 | system-architecture.md §0.1 IEEE 42010 対応表 L3「Concern 利害関係者の関心事項: PM/TL/SE/PO + auditable role」として列挙。ただし本格的な Concern×Stakeholder 2 軸マトリクスにはなっていない | Concern 列挙はあるが 2 軸交差マトリクスとしては compact |
| L4-06 | NFR (ISO25010:2023)↔アーキ設計戦略 mapping | 推奨 | 部分 | system-architecture.md §0.1 arc42§10 `NFR-MG / AC judge criteria / BR-RULE-09`、§0.2 NFR:27 カウント言及。ただし 25010:2023 の 9 特性と個別アーキ戦略の明示的 1:1 mapping 表は不在。grep: `NFR.*25010|25010.*NFR` 0 件 | 数値カウントと pointer はあるが mapping 表は欠落 |
| L4-07 | 依存関係マップ | 推奨 | 充足 | design-coverage-baseline.md 自身が「L5 module-decomposition でカバー」と明記。module-decomposition-design.md §4.9 mermaid 依存グラフが存在し、cli→cli/lib の方向依存を明示 | L5 に委譲済、参照 pointer 確認 |
| L4-08 | 総合テスト設計 (V-model L4↔L9 pair) | 必須 (HELIX) | 充足 | system-architecture.md frontmatter `pairs_test_design: docs/v2/L9-test-design/helix-workflows-system-test-design.md`。functional-design.md frontmatter も同様 `pairs_test_design: docs/v2/L9-test-design/helix-workflows-functional-test-design.md` | V-model pair freeze 確立済 |
| L4-09 | 脅威分析/セキュリティ viewpoint (STRIDE 等) | 必須 (セキュリティ関心事あれば) | 欠落 | system-architecture.md で `threat`, `STRIDE`, `脅威`, `attack surface`, `信頼境界`, `trust boundary` を grep → 0 件。functional-design.md でも同様 0 件。HELIX は hook guard/fail-close/model family 検証等のセキュリティ関心事を持つにも関わらず、専用の脅威モデル節が存在しない | hook guard/fail-close あるがセキュリティ viewpoint として統合された脅威分析節が欠落 |

### L5 詳細設計（9 項目）

| ID | 成果物 | 必須/推奨 | 判定 | evidence file:§ / 根拠 | 一言 |
|---|---|---|---|---|---|
| L5-01 | モジュール/クラス構造図 (静的関係・型設計) | 必須 | 充足 | module-decomposition-design.md §1 11 大分類 + §2.1 F1-F10 module 割付 matrix + §4 cli/lib 138 module 4 層分類。class-module-command-design.md §1-§5 で Python class API signature を固定 | module-decomposition (L5) + class design (L6) の 2 層で完備 |
| L5-02 | シーケンス/インタラクション図 | 必須 | 部分 | internal-processing-design.md で F1-F10 各機能の状態遷移図 (mermaid stateDiagram-v2) を完備。ただし明示的なシーケンス図 (sequenceDiagram) は存在せず、擬似コード + 状態遷移で代替。grep `sequenceDiagram` 0 件 | 状態遷移 mermaid は全機能に存在、シーケンス図形式は欠落 |
| L5-03 | API/IF 契約 (D-API) | 必須 | 充足 | interface-detailed-design.md §1-§12 で CLI 36 件 + hook 11 件の入出力契約、payload schema、exit code を固定。JSON Schema を含む | CLI/hook IF 契約を完全定義 |
| L5-04 | データ設計 (D-DB: ER/テーブル/永続化) | 必須 | 充足 | physical-data-design.md §2 既存 6 table DDL 完全形 + §3 新規 6 table DDL + §4 index 戦略 + §5 FK 設計 + §6 migration script | 12 table 完全 DDL + FK + index 完備 |
| L5-05 | 依存詳細・モジュール分割 | 推奨 | 充足 | module-decomposition-design.md §2.1 F1-F10 matrix に `dependency direction` 列あり + §4.9 mermaid 依存グラフ + §12 dependency direction rules | 依存方向が全 F で明示 |
| L5-06 | 横断的関心事設計 (ロギング/エラー/トランザクション) | 推奨 | 部分 | internal-processing-design.md §12 governance hook (PreCompact/SessionStart/UserPromptSubmit) で session/context の横断処理を定義。interface-detailed-design.md §11 error handling 共通ルール (fail-close/fail-open/timeout/retry)。ただし「ロギング方針」「トランザクション境界統合」を 1 節に集約した横断設計節が不在。grep `cross.cutting|横断的関心事` 0 件 | 個別節に散在、集約した横断設計節は欠落 |
| L5-07 | 状態遷移図 | 推奨 | 充足 | internal-processing-design.md §1-§13 で各機能の stateDiagram-v2 mermaid が全機能 (F1-F10) に存在。mode_transition state machine (§4.2)、migration 6-step state machine (§8.1)、homeostasis 4 段階 (§6.2) 等 | 全機能に状態遷移 mermaid あり |
| L5-08 | リソース/性能設計 | 推奨 | 部分 | physical-data-design.md §2.1.5 `想定 row 数 + 増加率` が全 12 table に定義。internal-processing-design.md §1 `collect_latency_ms 300ms 目標`、§3 `skill_catalog_build_ms < 800ms` 等の個別 metric 目標あり。ただし SLO/SLI として統合した性能設計節は不在。grep `SLO|SLI|latency.*goal|throughput` で各目標値は散在 | 個別 latency 目標はあるが SLO として統合した節は欠落 |
| L5-09 | 結合テスト設計 (V-model L5↔L8 pair) | 必須 (HELIX) | 充足 | internal-processing-design.md frontmatter `pairs_test_design: docs/v2/L8-test-design/helix-workflows-integration-test-design.md` + dependency-resolution-design.md。physical-data-design.md / interface-detailed-design.md / module-decomposition-design.md も同一 L8 pair を frontmatter に明記 | 4 ファイル全て L8 pair freeze 完備 |

### L6 機能設計（5 項目）

| ID | 成果物 | 必須/推奨 | 判定 | evidence file:§ / 根拠 | 一言 |
|---|---|---|---|---|---|
| L6-01 | エンドポイント/関数仕様 (入出力・事前事後条件・副作用) | 必須 | 充足 | function-spec-design.md §1-§6 で F1-F10 の全 public 関数 66 件 (signature/args/returns/exit code/stdout/stderr/side effect) を固定。事前条件は 境界 critical 補足節に記述 | 66 関数仕様完備 |
| L6-02 | アルゴリズム/処理ロジック仕様 | 必須 (複雑ロジックあれば) | 充足 | internal-processing-design.md (L5) が擬似コード + 算定式を F1-F10 全機能に定義。function-spec-design.md §3.2 score 算定式、§6.2 evolution score 式も存在。L5 doc が L6 のアルゴリズム観点をカバー | L5 内部処理設計が algorithm viewpoint を担当 |
| L6-03 | エラー処理設計 (エラーコード体系・例外方針・リトライ) | 必須 (全体統一) | 充足 | edge-case-design.md §0.2 exit code 体系 (0/1/2/1001/1010/1020/1030/1040/1050/1060) + §0.3 fail-close/fail-open/retry/rollback 方針 + §1 共通エラー処理パターン (EP-001〜008) + §2-§7 機能別 71 edge case | exit code 体系・retry 方針・71 edge case 完備 |
| L6-04 | 状態・イベント定義 (機能粒度) | 推奨 | 部分 | class-module-command-design.md で mode state machine (CMD-F4-02)、hook event type (HOOK-F5-01〜06) の envelope を定義。function-spec-design.md §4 F4 `scrum_local.init_local_loop()` / `decide_loop()` でループ状態を定義。ただし全機能の状態・イベント一覧を 1 箇所に集約した表は不在。状態定義は L5 内部処理設計に分散 | hook event type / state machine は存在、機能粒度の統合イベント一覧は散在 |
| L6-05 | 単体テスト設計 (V-model L6↔L7 pair・境界値・異常系) | 必須 (HELIX) | 充足 | class-module-command-design.md frontmatter `pairs_test_design: docs/v2/L7-test-design/helix-workflows-unit-test-design.md`。function-spec-design.md 同様。edge-case-design.md で 71 edge case 全件に `→ UT-Fx-NNN` L7 pointer を明記。2026-05-29 に L7 単体テスト設計 doc 作成済で双方向 trace 解決 | L7 pair freeze + 71 edge case pointer 完備 |

---

## §2 充足判定（最低充足セット評価）

### L4 最低充足セット (L4-01+L4-02+L4-03+L4-08)

| 判定 | 根拠 |
|---|---|
| **YES** | L4-02 ビルディングブロック: 充足。L4-03 ADR: 充足。L4-08 総合テスト設計: 充足。L4-01 コンテキスト図: 部分だが三層表で minimum 充足水準に達する |

追加必須 (セキュリティ関心事あり): **L4-09 が欠落** のため、hook guard/fail-close を持つ HELIX においてセキュリティ viewpoint 不足。最低充足セットを満たしてはいるが、L4-09 対応は必須追補対象。

### L5 最低充足セット (L5-01+L5-02+L5-03+L5-04+L5-09)

| 判定 | 根拠 |
|---|---|
| **YES** | L5-01 モジュール構造: 充足。L5-02 シーケンス/インタラクション: 部分 (状態遷移で代替)。L5-03 IF 契約: 充足。L5-04 データ設計: 充足。L5-09 結合テスト設計: 充足 |

L5-02 は「シーケンス図形式」が欠落しているが、擬似コード + 状態遷移で意図が伝わるため、最低充足セットとしては OK と判定。

### L6 最低充足セット (L6-01+L6-05)

| 判定 | 根拠 |
|---|---|
| **YES** | L6-01 関数仕様 66 件: 充足。L6-05 単体テスト設計 V-model pair: 充足 |

---

## §3 やり直し対象（欠落/部分項目の追補内容）

| ID | 判定 | 追補すべき内容 |
|---|---|---|
| L4-01 | 部分 | system-architecture.md に arc42§3 Context 専用節を追加し、外部アクター (PM/TL/SE/PO/adopter project) × インターフェース境界を図または表で明示する |
| L4-05 | 部分 | system-architecture.md に Stakeholder×Concern マトリクス表を追加する。行=PM/TL/SE/PO/project owner、列=可用性/保守性/監査/セキュリティ/workspace isolation 等 |
| L4-06 | 部分 | system-architecture.md に NFR (ISO25010:2023 9 特性) とアーキ設計戦略の 1:1 mapping 表を追加する。L3 非機能要件 doc (helix-workflows-nfr-detail.md) の NFR-ID を architecture decision に接続する |
| L4-09 | 欠落 | L4 設計いずれかに脅威分析節を追加する。最低限: 信頼境界 (hook guard / fail-close / model family validation / pretooluse-agent-guard) の STRIDE 観点整理。詳細は workflow/threat-model skill を参照。これは必須追補 |
| L5-02 | 部分 | internal-processing-design.md か module-decomposition-design.md に 1〜2 件の代表シーケンス図 (mermaid sequenceDiagram) を追加する。例: plan auto-register hook 発火フロー (PostToolUse → plan_parser → helix.db)、mode 切替フロー (helix route → RouteEngine → mode_transition) |
| L5-06 | 部分 | L5 いずれかの doc (または独立節) に横断的関心事設計をまとめた節を追加する。最低限: ロギング方針 (event_log への記録標準)、エラー伝播方針 (fail-close/fail-open の選択基準)、トランザクション境界 (compatibility_adapter.write_connection による DB write 統一) の 3 点 |
| L5-08 | 部分 | physical-data-design.md §7 (現 migration) か独立節に SLO/性能設計サマリを追加する。DB 主要 query の想定 latency 目標、metrics_log 収集頻度上限、CLI timeout 設計根拠の 3 点を集約 |
| L6-04 | 部分 | class-module-command-design.md か function-spec-design.md に hook event type 一覧表を追加する。event_type enum (11 種: cli_command/hook_fired/gate_judged/plan_status_changed/Mutation/Migration/Coexist 等) と各イベントの発火元/受信先/payload 型の一覧 |

---

## §4 採点メモ（full read で判明した点・前回 partial read 報告との差分）

### 今回 full read で判明した点

1. **L4-09 欠落は確定**: system-architecture.md / functional-design.md の両方を全文精査した結果、threat/STRIDE/脅威/attack の語が 0 件。hook guard の実装 (pretooluse-agent-guard.sh, model family validation) は存在するが、これらをセキュリティ viewpoint として統合した L4 設計節は明確に欠落している。

2. **L5-02 状態遷移はある、シーケンス図形式はない**: internal-processing-design.md を 1624 行全文読了した。F1〜F10 + Reverse + governance hook + 4 artifact trace の全機能に `stateDiagram-v2` mermaid が存在する。ただし `sequenceDiagram` は 0 件。擬似コードが interaction 代替として機能しているため「部分」判定が適切。

3. **L5-06 は真の欠落ではなく散在**: 横断的関心事は interface-detailed-design.md §11 にエラー共通ルールとして存在し、internal-processing-design.md §12 に governance hook 群がある。「欠落」ではなく「集約節が不在」という状態で「部分」が正確。

4. **L4-07 依存関係マップ**: baseline コメント「L5 module-decomposition でカバー」を確認。module-decomposition-design.md §4.9 mermaid 依存グラフ実在を確認し「充足」で合致。

5. **L6-04 状態・イベント定義**: class-module-command-design.md §4 hook/agent contract 設計で HOOK event type 8 件を定義済。function-spec-design.md §4 で `scrum_local` の loop 状態 API も定義。ただし全 hook event_type enum を一覧した独立表がなく「部分」が適切。

6. **physical-data-design.md は 1339 行**: 末尾 (L1131〜1339) も migration script と backup/restore 設計。SLO 統合節は全文確認でも不在。

7. **interface-detailed-design.md は 1856 行**: 末尾まで読了できていない箇所があるが §0.5 に IEEE 1016 Interface viewpoint 整合を明示、CLI 36 件 + hook 11 件の payload schema (JSON Schema) が完備していることを確認。

### 判定変更点（前回 explorer 報告との差分）

今回は初回 full read のため「前回 partial read 報告」との比較はなし。ただし baseline.md の HELIX-workflows V2 現状コメントと今回判定の相違を整理する:

| ID | baseline コメント | 今回判定 | 差分 |
|---|---|---|---|
| L4-01 | 薄い (arc42§3 は mapping 表にあるが専用節・図が薄い) | 部分 | 一致 |
| L4-04 | N/A 宣言が必要 (明示なし) | 充足 (N/A 扱い) | baseline より good: §7.2 で配布後方針を定義、CLI local tool の文脈からは実質 N/A |
| L4-06 | 薄い (L3 への pointer 中心) | 部分 | 一致 |
| L4-09 | 欠落 | 欠落 | 一致 |
| L5-02 | 明示シーケンス図は薄い | 部分 | 一致 |
| L5-06 | 散在・未集約 | 部分 | 一致 |
| L5-08 | 薄い | 部分 | 一致 |

---

## §5 追補後 再採点 (recovery-2026-05-30 step 3-4 完了後)

audit §3 やり直し対象 8 件を recovery で追補 → 再 grep 実証で全件 closed。

| ID | 旧判定 | 追補後 | 追補先 (grep 実証済) |
|---|---|---|---|
| L4-09 脅威分析 | **欠落(必須)** | **充足** | system-architecture §9 (STRIDE×信頼境界6 + 25010:2023 Security/Safety) |
| L4-06 NFR↔arch | 部分 | 充足 | system-architecture §10 (25010:2023 9特性 1:1 mapping) |
| L4-01 context | 部分 | 充足 | system-architecture §11 (アクター7種 + C4 L1 mermaid + 境界表) |
| L4-05 stakeholder matrix | 部分 | 充足 | system-architecture §12 (6×6 matrix) |
| L5-02 sequence | 部分 | 充足 | internal-processing §15 (sequenceDiagram ×2: PLAN登録/skill推挙) |
| L5-06 横断的関心事 | 部分 | 充足 | interface-detailed §14 (ロギング/エラー伝播/トランザクション/セキュリティ横断 集約) |
| L6-04 event_type enum | 部分 | 充足 | interface-detailed §15 (11 hook enum 一覧表) |
| L5-08 SLO/性能 | 部分 | 充足 | physical-data §13 (SLO/SLI統合 + リソース競合、未確定値は L14 carry 明示) |

**結論**: L4/L5/L6 は業界標準カバー基準 (design-coverage-baseline) を全項目で充足。Forward は **L6 から再開可能** (L7 実装スプリントへ進める状態)。

**forward carry (本 recovery のスコープ外、L6 再開には不要)**:
- L4-09 threat model に対応する L9 総合テストの security 観点 (ST-9) = planned。V-model L4↔L9 pair の右腕は L9 工程で実装
- L5-08 の SLO 数値 (plan登録/skill推挙/doctor full の latency 目標) = L14 運用検証で実測確定
- helix doctor `check_design_coverage` の機械 lint 化 = L14 carry

---

## §6 文書レベル完備 (recovery 追加 step: 設計書を全部そろえる)

§5 まで viewpoint/節レベルで充足を確認したが、業界標準で「独立設計書」であるべきものが §節に埋まっていた 3 件を独立文書化 (正本移設 + 元§はポインタ化で SSoT 維持)。

| 成果物 | 旧 (節内包) | 新 (独立設計書) |
|---|---|---|
| L4-09 脅威分析 | system-architecture §9 | **helix-workflows-threat-model.md** (125行、L9 ST-9 security pair trace) |
| L4-01+L4-05 context+stakeholder | system-architecture §11+§12 | **helix-workflows-system-context.md** (112行、arc42§1-3 + ISO42010§5.2) |
| L5-06 横断的関心事 | interface-detailed §14 | **helix-workflows-cross-cutting-design.md** (117行、IEEE1016 Patterns use + arc42§8) |

**結論**: L4/L5/L6 の設計書セットは**文書レベルで完備**。必須成果物の完全欠落なし、標準上独立文書が筋の 3 件も独立化済。Forward は L6 から再開可能。

**スコープ外 carry (本 recovery では触らない)**:
- `docs/v2/L3-detailed-design/` の D-API/D-DB/D-CONTRACT draft は別スコープ (PLAN-070 helix CLI / PLAN-084 workspace 分離=SEP)。folder naming drift (V2 では L3=要件定義なのに detailed-design 名) あり → 別 retrofit PLAN 候補
- `docs/v2/B-design/` の vmodel-semantics-* 等は正式 L4/L5/L6 フォルダ未昇格 → 別整理
