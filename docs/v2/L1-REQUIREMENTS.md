---
doc_id: V2-L1-REQUIREMENTS
title: "HELIX V2 構造改革 L1 要件定義書 ─ 2 Base 軸 + 基盤 + Emergent value"
status: draft
created: 2026-05-13
author: "PM (Opus + Sonnet 4.6)"
parent: docs/v2/CONCEPT.md
next_doc: docs/v2/MASTER.md (L2 基本設計)
gate: G1 要件完了ゲート
---

# HELIX V2 構造改革 L1 要件定義書

## §0 V2 価値連鎖 (本要件定義の構造原理)

```
[WHY] 3 問題       ← バグ / スパゲッティ化 / 契約漏れ
   ↓ 防止手段
[Base 軸 1] V-model 強化   ← 設計 ↔ 検証 pairing 強制
   ↓ 管理基盤
[基盤] helix.db (4 layer chain)
   ↓ 運用上の痛点
毎回手動 record は無駄
   ↓ 解決手段
[Base 軸 2] 自動化   ← auto-record / auto-detect / auto-sync
   ↓ 両軸が結合して生まれる価値
[Emergent value] 開発全容の可視化
```

本要件定義は **2 Base 軸 + 基盤 + Emergent value** の枠組みで BR/FR/NFR を分類する。

## §1 ステークホルダー

| 役割 | 担当 | 関心事 |
|---|---|---|
| **PO** | 人間ユーザー | V2 が痛点を解消するか / 既存知見の損失なし / 移行コスト |
| **PM** | Opus (チャット) / 必要時 Sonnet | 工程進捗 / 委譲先選択 / コスト管理 / エスカレーション |
| **PMO** | PMO Sonnet / Haiku / pm-advisor | 構造化 audit / docs 整合性 / コスト残量監視 / 難判断補助 |
| **TL** | Codex 5.5 | 技術判断 / 設計 review / 契約整合性 |
| **SE** | Codex 5.4 | 高度実装 / 契約定義 / リファクタリング |
| **PG** | Codex 5.3-codex-spark | 速度重視単機能実装 |
| **QA / Security / DBA / DevOps / Docs** | 各 Codex role | 専門領域 |
| **既存利用者** | 人間 (含む PO) | V1 → V2 移行の smooth 性 |
| **将来利用者** | 人間 / AI agent | V2 framework 利用 |

---

## §2 業務要件 (BR): 2 Base 軸 + 基盤 + Emergent value で構造化

### Base 軸 1: V-model 強化

| ID | 業務要件 | 達成判定 |
|---|---|---|
| **BR-V1** | 設計と検証の対応漏れを schema レベルで強制 | 4 layer chain (contract→code→test_design→test_baseline) が PLAN ごとに整合度算出可、≥ 80% 平均 |
| **BR-V2** | 4 drive (BE/FE/DB/Fullstack) で V-model variant 提供 | drive 列 + vmodel-semantics.yaml で drive 別 semantic 完備 |
| **BR-V3** | 縦/横 review が gate fail-close 連動 | G1-G6 通過判定で design_review.review_axis ('vertical'/'horizontal') 両 passed 必須 |
| **BR-V4** | FE 弱点 (専用 contract/detector/command 不在) の解消 | FE 専用 contract type 5+ / detector 5+ / command 5+ 追加 |

### Base 軸 2: 自動化

| ID | 業務要件 | 達成判定 |
|---|---|---|
| **BR-A1** | file 変更を helix.db に自動 record | PostToolUse hook で Write/Edit 完了時に対応 path → registrar 自動起動 |
| **BR-A2** | Gate / pre-commit で detector 自動実行 | 該当 G ゲート対応 detector が helix gate / pre-commit hook で auto-run |
| **BR-A3** | SessionStart で catalog 自動同期 | 起動時に skill / code / plan catalog の差分 sync 自動完了 |
| **BR-A4** | 自動 record の暴走防止 | dry-run mode / opt-out flag / 80%-100% guard 装備 |

### 付随基盤: helix.db

| ID | 業務要件 | 達成判定 |
|---|---|---|
| **BR-DB1** | 3 問題 (バグ / スパゲッティ / 契約漏れ) を構造的に防止する schema | 各問題に対応する table + detector の組合せで検知率 ≥ 90% |
| **BR-DB2** | V1 (v20) → V2 (v21) の後方互換 migration | v20 で書かれた record も v21 で読める、destructive op なし |
| **BR-DB3** | 段 1 / 段 2 分離を schema で明示 | managed_products / agent_registry table で HELIX が任意 Product を制御する関係を表現 |

### Emergent value: 開発全容の可視化

| ID | 業務要件 | 達成判定 |
|---|---|---|
| **BR-EM1** | 全 PLAN の 4 layer chain 整合度 / detector verdict / 委譲履歴を 1 dashboard で参照可能 | `helix detect dashboard` + `helix qa vmodel-score --all` 等で全容把握 1s 以内 |
| **BR-EM2** | 関係性 (detector × code × contract × hook) の可視化 | axis-10 relation graph の mermaid 出力が現実の関係を反映 |
| **BR-EM3** | SessionStart で 1 秒以内に全 state 表示 | 既存 session-start hook の拡張 |
| **BR-EM4** | 開発全容を report として export 可能 | `helix report dev-state` で markdown / JSON 出力 |

### 派生業務要件

| ID | 業務要件 | 達成判定 |
|---|---|---|
| **BR-D1** | PMO 役割を schema レベルで分離 | PM / PMO Sonnet / PMO Haiku / pm-advisor / tl-advisor が ROLE_MAP + role conf で機械的に分離 |
| **BR-D2** | V1 知見の V2 集大成 | PLAN-001〜068 未実装 carry すべて Phase I で V2 phase 紐付け済 |
| **BR-D3** | dogfood 成立 | V2 完了後の HELIX 改修が V2 framework で全工程実施可能 |

---

## §3 機能要件 (FR): 5 Phase 順序で分類

順序原則 (§0 価値連鎖 + ユーザー 5 Phase 構想):

```
既存整理 → V-model 強化定義 → V-model 実装 → helix.db 拡張 → 検出ガードレール → 自動化 → 可視化 → 派生 → 工程転換
```

### 3.0 既存整理 (V1 capability inventory、Phase 1)

V2 = V1 累積 (PLAN-001〜068) の集大成構造改革。**何を整理対象とするか** を要件レベルで確定する。これが Before の正本。

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-INV01** | V1 capability 棚卸し doc 起票 | `docs/v2/A-audit/capability-inventory.md` で 12+ capability (V-model schema / 14 detector / 契約 extractor / handover / skill 推挙 / Reverse / Scrum / Agent Transformation 散在 / PMO / pm-tl-advisor / Stop hook / Codex/Claude harness) を実装状態 (実装済 / 部分実装 / carry / 廃止) + 起源 PLAN 付きで列挙 |
| **FR-INV02** | PLAN-001〜068 carry 棚卸し | `docs/v2/A-audit/legacy-plans-carry.md` で全旧 PLAN の deferred-finding と未実装 carry を V2 phase 紐付け候補と共に列挙 |
| **FR-INV03** | 5 層 × 3 問題 capability matrix | `docs/v2/A-audit/capability-matrix.md` で「PM/Orch/Cmd/Skill/Verify × バグ/スパゲッティ/契約漏れ」9 セルに現状 capability を mapping、不足箇所を Phase G〜J 入力に |
| **FR-INV04** | FE 弱点炙り出し | `docs/v2/A-audit/fe-weakness-analysis.md` で FE 専用 contract type / detector / command の不在箇所列挙、Phase G 入力に |
| **FR-INV05** | V1 蓄積知見の正本化 | `docs/v2/A-audit/accumulated-knowledge.md` で V1 から残る運用判断・設計判断 (PLAN 由来) を起源参照付きで列挙、After 設計の根拠に |
| **FR-INV06** | 廃止対象の明示 | INV01-05 で「V2 では廃止」と判定された capability を `deprecated.md` に記録、削除タイミング (Phase J / V3 / 永久 carry) 明示 |

### 3.1 V-model 強化定義 (drive × layer semantics、Phase 2 定義)

After の正本。**何を pairing するかの意味論** を L1 で確定する (具体 entries は L2 と vmodel-semantics.yaml で詳細化)。

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-VD01** | 5 design layer × 5 test layer ペアリング定義 | planning↔operational / requirement↔acceptance / architecture↔system_integration / detailed↔integration / functional↔unit の 5 対が L1 で確定 |
| **FR-VD02** | 4 drive (BE/FE/DB/Fullstack) の定義範囲確定 | 各 drive の起点・典型プロジェクト・必須 layer・必須テスト種別を L1 で要件化 (SKILL_MAP §駆動タイプと整合) |
| **FR-VD03** | drive × layer の必須記述項目 | 各セル (4×5=20 design セル + 4×5=20 test セル) で必須項目 (artifacts / review_unit / review_axes / expected_tests / detectors / promotion policy) を L1 で確定 |
| **FR-VD04** | FE mock promotion lifecycle 定義 | mock_frozen → promoted の append-only 遷移 (row 更新禁止) を要件として明文化、G2 evidence 保全を NFR と接続 |
| **FR-VD05** | 縦軸 review (同脚内 layer 連鎖) 定義 | architecture → detailed → functional の粒度落ち検知ルールを drive 別に要件化 |
| **FR-VD06** | 横軸 review (設計↔検証ペア) 定義 | 同 layer の design 行と test_design 行の 1:1 対応ルールを要件化 |
| **FR-VD07** | origin_mode × evidence_status lifecycle 定義 | Forward (confirmed) / Reverse (observed → inferred → confirmed) / Scrum (confirmed 後に Forward 接続) の状態遷移を要件化 |
| **FR-VD08** | V-model 整合度スコア式定義 | `score = 100 - 15×missing_test_design - 10×missing_baseline - 20×failing_baseline` (TL 推奨、chain break penalty) を要件として固定 |
| **FR-VD09** | 4 layer chain 構造定義 | contract_entries → code_index → test_design_entries → test_baseline の chain 関係と link kind (covers / derives_from / implements / reviews) を要件化 |

### 3.2 V-model 実装 (Phase 2 実装、旧 §3.1)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-V01** | `contract_entries` / `test_design_entries` / `design_review` に `drive` 列追加 | ALTER TABLE 実行、CHECK 制約 (be/fe/db/fullstack) |
| **FR-V02** | `cli/config/vmodel-semantics.yaml` 新設 (drive ごとの design/test semantic 外部化) | 4 drive × 5 design × 5 test の semantic 定義 |
| **FR-V03** | `helix gate --pair-check` に `--drive` 引数追加 | drive 別 semantic を参照して縦/横 review 判定 |
| **FR-V04** | 4 layer chain SQL view 作成 | `view_vmodel_integrity` で contract → code → test_design → test_baseline JOIN |
| **FR-V05** | V-model 整合度スコア算出 CLI | `helix qa vmodel-score --plan-id PLAN-NNN` で 0-100 |
| **FR-V06** | 縦軸検査 CLI | `helix qa vertical-check --plan-id PLAN-NNN` で上位 ↔ 下位 layer 連鎖確認 |
| **FR-V07** | 既存 contract_entries の design_level 再分類 migration | `helix code build --reclassify-design-level` で 5 値分布 |

### 3.3 helix.db v21 schema 拡張 (Phase 3)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-DB01** | `_migrate_v20_to_v21` 実装 | `init_db` 後 `schema_version = 21` |
| **FR-DB02** | `er_diagrams` table 新設 | (plan_id, design_level, drive, diagram_path, mermaid_content, version) |
| **FR-DB03** | `process_maps` table 新設 | (plan_id, design_level, drive, map_kind, map_path, mermaid_content, version) |
| **FR-DB04** | `managed_products` table 新設 | (product_name, product_path, drive, mode, helix_version) |
| **FR-DB05** | `agent_registry` table 新設 | (agent_kind, role, model, thinking, allowed_paths, cost_budget) |
| **FR-DB06** | `contract_entries.design_level` 既存値の再分類 migration | dry-run 必須、batch + transaction |
| **FR-DB07** | `design_sprint_entries` table 新設 (工程転換、§3.8 と連動) | sprint_id × sprint_type × layer × drive × track × pair_status × freeze_gate × subgate |
| **FR-DB08** | `design_sprint_artifact_links` table 新設 | sprint_entry_id × artifact_kind × artifact_ref × link_kind の組合せで UNIQUE |
| **FR-DB09** | `contract_entries.origin_mode` / `evidence_status` 列追加 | TL 推奨 (forward/reverse/scrum) × (observed/inferred/confirmed) で Reverse/Scrum lifecycle |
| **FR-DB10** | `design_review.direction` / `source_phase` 列追加 | TL 推奨 (forward/reverse) で Reverse review lifecycle |

### 3.4 検出ガードレール強化 (Phase 4)

helix.db に蓄積された record を使って **3 問題 (バグ / スパゲッティ / 契約漏れ) を検知 + agent に feedback / stop をかける** 仕組み。自動化の前段として、検知できる状態を作る。

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-GR01** | 14 detector (axis-01〜14、PLAN-063 完了) の運用化 | 全 axis が `helix detect run --axis <N>` で起動可能、stub 0 件、verdict (pass/warn/fail) を `detector_runs` table に record |
| **FR-GR02** | Gate runner 連動 (G ゲート fail-close) | G2/G3/G4/G6 通過判定で該当 detector auto-run、fail なら gate fail-close (FR-A03 と接続) |
| **FR-GR03** | agent feedback mechanism | detector verdict を Claude/Codex hook 経由で agent に返却、PostToolUse 後に該当 axis が fail なら次 tool 呼び出し前に hint 注入 |
| **FR-GR04** | agent stop mechanism | Critical axis (axis-01 dead code / axis-02 spaghetti / axis-07 contract drift など) が fail で PreToolUse hook で Write/Edit を block (PLAN-043 機構の拡張) |
| **FR-GR05** | 5 層介入機構 | PM / Orchestration / Command / Skill / Verify 各層が agent に介入できる hook 機構を要件化 (PM 層 = handover escalation / Orchestration 層 = routing 修正 / Command 層 = CLI guard / Skill 層 = skill 推挙 reroute / Verify 層 = detector fail-close) |
| **FR-GR06** | 検出 → feedback → stop の閉ループ | record → detect → feedback → stop の経路が 1 セッション内で完結、agent が同じ違反を 2 回繰り返す前に介入が発火 |
| **FR-GR07** | guardrail 暴走防止 | false positive threshold / opt-out flag / dry-run mode / 80%-100% cost guard 連動 |

### 3.5 自動化 (Phase 5、旧 §3.2)

検知ガードレールが効く前提で、record を機械化する。「機能完成 → 自動化」原則。

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-A01** | PostToolUse hook で Write/Edit 検知 → auto-register | `docs/plans/PLAN-*.md` 新規 → `helix plan import --auto` が 5s 以内に発火 |
| **FR-A02** | SessionStart hook で全 catalog 自動同期 | 起動時 skill catalog rebuild + code build (incremental) + plan import 完了 |
| **FR-A03** | Gate runner で detector 自動 run | `helix gate G<N>` 通過判定時に該当 detector auto-run、failed なら fail-close (FR-GR02 と接続) |
| **FR-A04** | pre-commit hook で staged 変更に応じた detector 自動 run | cli/lib/ 変更 → axis-01/02 / skills/ 変更 → axis-04 / docs/ 変更 → axis-07 |
| **FR-A05** | Gate 通過時に design_review / test_baseline 自動 record | TL/QA review 完了 → design_review INSERT、helix test 完了 → test_baseline bulk INSERT |
| **FR-A06** | acceptance.yaml から test_design_entries 自動抽出 | helix plan finalize 時に hook で抽出 |
| **FR-A07** | 統一 `helix sync` CLI | `helix sync --auto / --plans / --skills / --code / --detectors / --force` |
| **FR-A08** | 自動化の暴走防止 | dry-run mode / opt-out flag / cost guard / atomic transaction |

### 3.6 全容可視化 (Phase 6、Emergent value、旧 §3.4)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-EM01** | dashboard 強化 (V-model 整合度 + detector + 委譲履歴 + 全 KPI) | `helix detect dashboard` で 5+ 観点が 1 view 統合表示 |
| **FR-EM02** | relation graph (axis-10) の mermaid 出力品質向上 | detector × code × contract × hook の関係が現実反映 |
| **FR-EM03** | dev-state report export | `helix report dev-state --format markdown|json` |
| **FR-EM04** | SessionStart で 1 秒以内 dashboard 表示 | `helix detect dashboard --quick` で軽量表示 |
| **FR-EM05** | PLAN ごとの V-model 健全性 dashboard | `helix qa vmodel-dashboard --plan-id PLAN-NNN` |
| **FR-EM06** | 全 PLAN 横断の整合度 summary | `helix qa vmodel-score --all` |

### 3.7 派生機能要件

#### FE 弱点強化 (Phase G、Base 軸 1+2 派生)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-FE01** | FE 専用 contract type 5+ 追加 | component_props / state_events / visual_token / a11y_requirement / screen_transition |
| **FR-FE02** | FE 専用 detector 5+ 追加 (axis-15〜19) | mock_promotion / design_token_drift / a11y_regression / visual_regression / state_transition_drift |
| **FR-FE03** | FE 専用 command 5+ 追加 | `helix fe visual-diff` / `a11y-check` / `playwright-run` / `snapshot-update` / `state-events-validate` |
| **FR-FE04** | G5 visual refinement gate 運用化 | MOCK-* auto-enqueue が `routing_decisions` record + 未解消で G5 fail-close |
| **FR-FE05** | FE test_baseline test_kind 拡張 | snapshot / visual_regression / playwright / axe_a11y |
| **FR-FE06** | FE drive vmodel-semantics.yaml entries | mock→本実装 promotion lifecycle、layer 別 semantic 完備 |

#### Agent Transformation サブ層整理 (Phase H、派生)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-AT01** | BaseAgent 統一 IF (`cli/lib/base_agent.py`) | `__init_subclass__` で agent_kind / step / step_ids 強制 |
| **FR-AT02** | LLM Router 集約 (`cli/lib/llm_router.py`) | 既存 helix-codex / helix-claude / fallback / routing_decisions 統合エントリ |
| **FR-AT03** | Cost Guard 集約 (`cli/lib/cost_guard.py`) | helix budget + 各 role conf 統合、80%/100% 動作明示 |
| **FR-AT04** | OpenAPI fragments 出力 CLI | `helix contract export --format openapi --fragment <name>` |
| **FR-AT05** | Tool Registry schema | `agent_registry.allowed_tools` field |

#### Legacy Import (Phase I、派生)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-LI01** | 旧 PLAN markdown を削除せず history として保持 | `docs/plans/PLAN-NNN-*.md` 全保持 |
| **FR-LI02** | V1 → V2 mapping 表作成 | `docs/v2/I-legacy-import/V2-mapping.md` で全旧 PLAN → V2 phase 対応表 |
| **FR-LI03** | 未実装 carry の V2 取り込み | 各旧 PLAN の deferred-finding が V2 phase 内で処理または defer 継続理由明記 |

### 3.8 工程転換 (V-model スプリント化、Phase 2 + 5 Phase 統合の中核)

設計と対応テスト設計を **同一スプリント内でペア凍結** することで、V1 で頻発する「テスト設計の後追い」を構造的に解消する。TL 推奨に基づき **PLAN 規模で可変 / drive は track 並列 / G3.5 は G3 サブゲート始動** を採用。

#### Before (V1) → After (V2) 工程対比

| 工程 | Before (V1) | After (V2) | ペアリング |
|---|---|---|---|
| メタ設計 | L1 要件定義 (単発) | L1 内側統合 (drive 判定 + Phase 計画 + size 判定) | — |
| 基本設計スプリント | L2 全体設計 (テスト設計は L3 にずれる) | **L2 基本設計 ∥ システム統合テスト設計** (同 sprint 内ペア凍結) | architecture ↔ system_integration |
| 詳細設計スプリント | L3 詳細設計 + テスト設計まとめて | **L3 詳細設計 ∥ 結合テスト設計** | detailed ↔ integration |
| 機能設計スプリント | (なし、L3/L4 に埋没) | **L4 機能設計 ∥ 単体テスト設計** | functional ↔ unit |
| 実装スプリント | L4 マイクロスプリント (.1〜.5) | **実装 ∥ テスト実行 ∥ レビュー** (三位一体) | code apex |

#### ゲート再定義 (G3.5 サブゲート化)

| ゲート | Before | After | 採用方式 |
|---|---|---|---|
| G2 | L2 設計凍結 | 基本設計 + システム統合テスト設計 **両方凍結** | enforce |
| G3 | API/Schema Freeze | 詳細設計 + 結合テスト設計 **両方凍結** + (任意で) `G3.functional_freeze` サブゲート | enforce + subgate |
| **G3.functional_freeze (新設、サブゲート)** | — | 機能設計 + 単体テスト設計 凍結 (L 案件 / fullstack / fe / db で必須) | size/drive 別 enforce |
| G4 | 実装 + テスト PASS | 実装 + テスト実行 + レビュー **三点完了** | enforce |

> **設計判断**: G3.5 を即 public gate として `phase.yaml.gates.G3_5` に昇格すると、既存 CLI / docs / Reverse / Scrum routing への破壊的影響が大きい (TL P1 リスク)。まず G3 内サブゲート (`subgate='functional_freeze'`) として実装し、運用実績後に v22 で public gate 昇格を検討。

#### スプリント粒度 (PLAN 規模で可変)

| size | 必須スプリント | 補足 |
|---|---|---|
| **S** (1-3 file, <100 行) | impl のみ | architecture/detailed/functional は最小化または skip |
| **M** (4-10 file, 101-500 行) | detailed → impl (functional は impl に統合可) | API/DB 変更ある場合 detailed 必須 |
| **L** (11+ file, 501+ 行) | architecture → detailed → functional → impl (4 sprint) | fullstack / fe は functional 必須 |

> **設計判断**: 固定 4 sprint 全 PLAN 強制は SKILL_MAP §タスクサイジング (S/M/L) と衝突するため不採用 (TL P1 リスク)。必要 layer/pair が満たされたかを gate が見る方式に統一。

#### drive 分岐の工程表現 (track 並列)

| drive | スプリント構造 |
|---|---|
| **be** 単独 | 単一 track (`track='be'`) で sprint 進行 |
| **fe** 単独 | 単一 track (`track='fe'`)、mock → 本実装の append-only lifecycle |
| **db** 単独 | 単一 track (`track='db'`) |
| **fullstack** | **同一上位 sprint 内で `track=be ∥ fe ∥ contract`** 並列 |

> **設計判断**: fullstack を BE / FE 別 PLAN または完全別 sprint に分断すると D-CONTRACT / state-events / API freeze の同期点が割れる (TL P1 リスク)。`drive=fullstack` は案件種別、`track=be|fe|contract|shared` は作業線として分離。

#### FR (工程転換)

| ID | 要件 | 受入条件 |
|---|---|---|
| **FR-VS01** | `design_sprint_entries` table 新設 | sprint_type (architecture/detailed/functional/impl) × layer × drive × track × pair_status |
| **FR-VS02** | `design_sprint_artifact_links` table 新設 | sprint_entry_id × artifact_kind (design/test_design/review/baseline) × link_kind (covers/derives_from/reviews/implements) |
| **FR-VS03** | G3 サブゲート `functional_freeze` 実装 | `helix gate G3 --subgate functional_freeze` で pair_status='paired' 確認、size=L / drive in (fe/fullstack/db) で必須 |
| **FR-VS04** | スプリント粒度の size 別判定 | `helix sprint plan --size <S/M/L> --drive <drive>` で必須 sprint_type 列挙 |
| **FR-VS05** | fullstack track 並列管理 | 同一 sprint_id で track=be / fe / contract が独立進行、片 track 未完了で G3/G4 fail-close |
| **FR-VS06** | pair_status 遷移管理 | pending → design_only / test_only → paired → (waived / failed) の状態遷移検証 |
| **FR-VS07** | Reverse / Scrum モード対応 | Reverse: RG2/RG3 後の Forward 接続で必要な gap のみ functional_freeze 要求。Scrum: confirmed まで対象外、confirmed 後に Forward contract 生成と同時に sprint 開始 |

---

## §4 非機能要件 (NFR): 7 カテゴリ網羅

### 4.1 互換性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-01** | V1 動作互換性 | V2 完了まで V1 CLI / SKILL / hook 動作維持、helix.db v20 → v21 後方互換 |
| **NFR-02** | 段階的 migration | Phase ごとに既存テスト PASS 維持 (pytest 1138+ / bats 433+ / shell 614+) |

### 4.2 性能

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-10** | helix detect 全実行 ≤ 30s | `helix detect dashboard` 完了が 30s 以内 |
| **NFR-11** | pair-check ≤ 5s | `helix gate G<N> --pair-check <layer>` 完了 |
| **NFR-12** | SessionStart dashboard ≤ 1s | `helix detect dashboard --quick` 完了 |
| **NFR-13** | PostToolUse auto-record ≤ 5s | Write 完了 → DB 反映 |
| **NFR-14** | helix sync ≤ 60s | `helix sync --auto` 完了 |

### 4.3 コスト効率

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-20** | PM token 50% 削減 | PMO 委譲経路で PM 単独運用比 -50% |
| **NFR-21** | V2 構築は既存予算内 | 5-10 セッション × 既存 budget で完結 |
| **NFR-22** | Cost Guard 80%/100% | 80% 到達で追加予算申請、100% で自動停止 |

### 4.4 安全性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-30** | destructive op 禁止 (人間承認なしで) | git reset --hard / DROP TABLE / 履歴破壊系 |
| **NFR-31** | Codex 委譲 scope 強制 | `--allowed-files` 違反は axis-14 で検知 |
| **NFR-32** | 秘密情報 redaction | invocation_log redaction + secret scan |
| **NFR-33** | auto-record の暴走防止 | dry-run / opt-out / 80%-100% guard |
| **NFR-34** | atomic transaction | sync / migration が部分失敗時 rollback |

### 4.5 拡張性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-40** | enum (5 design / 5 test) 固定 | 変更時の migration コスト最小化 |
| **NFR-41** | drive 追加可能 (1 file 修正) | vmodel-semantics.yaml に entry 追加で完了 |
| **NFR-42** | V3 への path 残す | managed_products / agent_registry が multi-tenancy / リモート同期に拡張可能 |

### 4.6 可観測性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-50** | invocation_log 完備 | 全 LLM 呼び出し record (PLAN-063 W-1a 既存) |
| **NFR-51** | detector_runs 完備 | 全 detector 実行 record |
| **NFR-52** | session-start dashboard | 1 秒以内表示 |
| **NFR-53** | dev-state report 可能 | markdown / JSON export |

### 4.7 ドキュメンテーション

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-60** | V2 全 phase で D-shard 整備 | `docs/v2/<phase>/` 存在 |
| **NFR-61** | 用語 SSOT 一貫 | 既存 SKILL_MAP / CLAUDE.md / AGENTS.md と矛盾なし (axis-07 通過) |
| **NFR-62** | 既存 source 参照 attach | docs 内の link が具体的なファイル / PLAN / SKILL を指す |

---

## §5 受入条件 (AC): V2 全体の G1 通過基準

| ID | 条件 | 検証コマンド |
|---|---|---|
| **AC-01** | helix.db v21 migration 動作 | `sqlite3 .helix/helix.db 'SELECT MAX(version) FROM schema_version'` = 21 |
| **AC-02** | drive 列が 3 table に存在 | `PRAGMA table_info(contract_entries)` で drive 列 |
| **AC-03** | 新 4 table 存在 | er_diagrams / process_maps / managed_products / agent_registry |
| **AC-04** | vmodel-semantics.yaml 完備 | 4 drive × 5 design × 5 test entries |
| **AC-05** | 自動 record 稼働 | PostToolUse hook で 5s 以内に DB 反映 |
| **AC-06** | Gate auto-detect 稼働 | `helix gate G4` で対応 detector auto-run |
| **AC-07** | dashboard 統合表示 | `helix detect dashboard` で 5+ 観点表示 1s 以内 |
| **AC-08** | V-model 整合度算出 | `helix qa vmodel-score --plan-id <id>` が 0-100 |
| **AC-09** | FE 専用 5 種 5+ each | contract type / detector / command それぞれ 5+ |
| **AC-10** | docs/v2/A-audit/ 4 doc 完備 | 4 audit doc 存在 |
| **AC-11** | V1 → V2 mapping 完備 | 全旧 PLAN がエントリ |
| **AC-12** | テスト suite PASS 維持 | pytest 1138+ / bats 433+ / shell 614+ |
| **AC-13** | PMO 5 role conf 完備 | pmo-sonnet / pmo-haiku / pm-advisor / tl-advisor / impl-sonnet |
| **AC-14** | dogfood 確認 | V2 完了後の HELIX 改修が V2 framework で完結 |
| **AC-15** | 工程転換 (V-model スプリント化) 稼働 | `design_sprint_entries` table 存在、size 別必須 sprint_type 列挙 CLI 動作、fullstack の track 並列管理動作 |
| **AC-16** | G3 functional_freeze サブゲート動作 | `helix gate G3 --subgate functional_freeze --plan-id <id>` で pair_status='paired' 確認、size=L / drive in (fe/fullstack/db) で必須 enforce |
| **AC-17** | origin_mode / evidence_status / direction 3 列追加 | `PRAGMA table_info` で contract_entries / design_review に該当列存在 |

---

## §6 スコープ

### V2 で含む (Phase A〜J)

- ✅ 集大成 audit (Phase A)
- ✅ 上流 architecture (Phase B)
- ✅ helix.db v21 schema 拡張 (Phase C)
- ✅ **V-model 実装 (Phase D、Base 軸 1)**
- ✅ **自動化実装 (Phase E、Base 軸 2)**
- ✅ **全容可視化 (Phase F、Emergent value)**
- ✅ FE 弱点強化 (Phase G)
- ✅ Agent Transformation 整理 (Phase H)
- ✅ Legacy Import (Phase I)
- ✅ dogfood / 運用安定化 (Phase J)

### V2 で含まない (V3 候補)

- ⏸ CI/CD integration
- ⏸ リモート同期 / multi-tenancy
- ⏸ FE UI dashboard 強化 (本 V2 は CLI dashboard まで)
- ⏸ ペンテスト / SIEM / 監視運用

---

## §7 制約条件

| ID | 制約 | 影響 |
|---|---|---|
| **CON-01** | 旧 PLAN markdown 削除禁止 | history 保持、Phase I で参照 |
| **CON-02** | V1 CLI / SKILL は V2 完了まで動作維持 | 段階的 migration |
| **CON-03** | 人間承認必須ゲート | G0.5 (企画) / G1 (要件) / G6 (RC) / G7 (本番) / L8 (受入) / G9-11 (Run) |
| **CON-04** | Codex token 上限 | impl-sonnet 経路で代替 |
| **CON-05** | destructive op 制限 | 人間承認必須 |
| **CON-06** | PreToolUse hook bypass 不可 (PLAN-043) | Opus 直接 Edit は repo 内で blocked |

---

## §8 依存・前提

| ID | 依存 | 確認方法 |
|---|---|---|
| **DEP-01** | helix.db v20 (PLAN-065 W-2) 完了 | `helix doctor` |
| **DEP-02** | PLAN-063 detector 14 軸完了 | `cli/helix-detect list` で stub 0 |
| **DEP-03** | PMO role conf 既存 | `ls cli/roles/pmo-*.conf` |
| **DEP-04** | pm-advisor / tl-advisor / impl-sonnet 追加済 | 本セッション内で commit 済 |
| **DEP-05** | Automation-SEO 参照可能 (段 1 product 参考) | SSH key 経由 |
| **DEP-06** | docs/v2/CONCEPT.md 起票済 (G0.5 通過) | 本企画書 §1 |

---

## §9 リスクと対策 (要件レベル)

| リスク | 影響 | 対策 |
|---|---|---|
| FR-V07 (design_level 再分類) で誤った reclassify | 中 | `--dry-run` mode 必須、batch + transaction、ログ保存 |
| FR-FE02 (FE detector) の false positive | 中 | threshold 設定可、第一版 warning のみ、強制化は後続 |
| FR-A01 (PostToolUse hook) の処理時間が編集体感に悪影響 | 中 | incremental + async (background) |
| FR-A03 (Gate auto-detect) で commit が止まる | 中 | --no-verify bypass / threshold / 既存テスト保護 |
| NFR-20 (PM token 50% 減) 未達成 | 低 | 移動平均で評価、目標調整可 |
| AC-12 (テスト suite PASS 維持) 破壊 | 高 | 各 Phase baseline 取得 |
| FR-EM01 (dashboard 性能) 劣化 | 中 | 集計 cache / incremental |

---

## §10 用語集

[CONCEPT.md §9 補足](./CONCEPT.md) を継承。追加用語のみ:

| 用語 | 定義 |
|---|---|
| **2 Base 軸** | V-model 強化 (BR-V) + 自動化 (BR-A) |
| **付随基盤** | helix.db (両軸を支える foundation、BR-DB) |
| **Emergent value** | 両軸結合で生まれる「開発全容の可視化」(BR-EM) |
| **派生要件** | 2 Base 軸からの派生 (FE 強化 / Agent Transformation / 集大成 / Legacy Import) |
| **4 layer chain** | contract_entries → code_index → test_design_entries → test_baseline |
| **V-model 整合度スコア** | 4 layer chain が PLAN ごとに埋まる率 (0-100)。score = 100 - 15×missing_test_design - 10×missing_baseline - 20×failing_baseline (TL 推奨、chain break penalty) |
| **設計スプリント** | 設計 layer (architecture/detailed/functional) と対応テスト設計を同時凍結する作業単位。Before の「テスト設計後追い」を構造解消 |
| **track** | drive 内部の作業線 (be/fe/db/contract/shared)。fullstack で BE/FE/contract が並列進行する場合に使う |
| **pair_status** | 設計と対応テスト設計の凍結状態 (pending / design_only / test_only / paired / waived / failed) |
| **origin_mode** | contract の起源 (forward / reverse / scrum)。Forward 通常工程・Reverse 既存コード復元・Scrum 仮説検証 |
| **evidence_status** | 証跡の確度 (observed 観測 / inferred 推定 / confirmed 確認)。Reverse の R0-R3 lifecycle で遷移 |
| **G3.functional_freeze** | G3 のサブゲート。機能設計 + 単体テスト設計の pair_status='paired' を size=L / drive in (fe/fullstack/db) で enforce |

---

## §11 G1 要件完了ゲート通過条件

- [ ] §2 BR (V-V4 / A1-A4 / DB1-DB3 / EM1-EM4 / D1-D3 計 18) すべて PO レビュー済
- [ ] §3 FR 5 Phase 順序で 9 セクション網羅 (計 74)
  - §3.0 既存整理 INV01-06 (6)
  - §3.1 V-model 強化定義 VD01-09 (9)
  - §3.2 V-model 実装 V01-07 (7)
  - §3.3 helix.db 拡張 DB01-10 (10)
  - §3.4 検出ガードレール強化 GR01-07 (7)
  - §3.5 自動化 A01-08 (8)
  - §3.6 可視化 EM01-06 (6)
  - §3.7 派生 (FE01-06 / AT01-05 / LI01-03 計 14)
  - §3.8 工程転換 VS01-VS07 (7)
- [ ] §3.0/§3.1 (既存整理 + V-model 強化定義) が §3.8 (Before/After 工程転換) の根拠として完結している
- [ ] §3.4 検出ガードレール強化 が §3.5 自動化 の前段として要件化されている
- [ ] §4 NFR (互換 / 性能 / コスト / 安全 / 拡張 / 可観測 / docs 計 24) カテゴリ網羅
- [ ] §5 AC (01-17) 検証コマンド付き
- [ ] §6 スコープ in/out 明示
- [ ] §7-8 制約 / 依存 抜けなし
- [ ] PO 承認

G1 passed → Phase B (MASTER.md = L2 基本設計) へ。

---

## §12 次のアクション

### G1 通過後

1. `docs/v2/MASTER.md` (L2 基本設計) 起票
   - BR-V / BR-A / BR-DB / BR-EM をどう実現するかの architecture
   - Phase A〜J の入出力 / dependency / 委譲先 / timeline
2. `docs/v2/CAPABILITY-MATRIX.md` 起票 (Phase A 入力)
3. Phase A audit 着手

### 本要件定義へのフィードバック

PO は以下のいずれかで判断:
- (a) approve → MASTER.md 起票
- (b) needs revision → 追加・修正点指摘
- (c) reject → 要件レベル再検討

---

**承認**: PO ____________
**G1 判定**: [ ] passed / [ ] needs revision / [ ] failed
**G1 判定日**: 2026-05-__
