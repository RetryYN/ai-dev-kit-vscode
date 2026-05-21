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
| **FR-DB-EXT-01** | `_migrate_v20_to_v21` 実装 | `init_db` 後 `schema_version = 21` |
| **FR-DB-EXT-02** | `er_diagrams` table 新設 | (plan_id, design_level, drive, diagram_path, mermaid_content, version) |
| **FR-DB-EXT-03** | `process_maps` table 新設 | (plan_id, design_level, drive, map_kind, map_path, mermaid_content, version) |
| **FR-DB-EXT-04** | `managed_products` table 新設 | (product_name, product_path, drive, mode, helix_version) |
| **FR-DB-EXT-05** | `agent_registry` table 新設 | (agent_kind, role, model, thinking, allowed_paths, cost_budget) |
| **FR-DB-EXT-06** | `contract_entries.design_level` 既存値の再分類 migration | dry-run 必須、batch + transaction |
| **FR-DB-EXT-07** | `design_sprint_entries` table 新設 (工程転換、§3.8 と連動) | sprint_id × sprint_type × layer × drive × track × pair_status × freeze_gate × subgate |
| **FR-DB-EXT-08** | `design_sprint_artifact_links` table 新設 | sprint_entry_id × artifact_kind × artifact_ref × link_kind の組合せで UNIQUE |
| **FR-DB-EXT-09** | `contract_entries.origin_mode` / `evidence_status` 列追加 | TL 推奨 (forward/reverse/scrum) × (observed/inferred/confirmed) で Reverse/Scrum lifecycle |
| **FR-DB-EXT-10** | `design_review.direction` / `source_phase` 列追加 | TL 推奨 (forward/reverse) で Reverse review lifecycle |

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
| **FR-GR08** | **doc artifact registry** | `helix doc register --path <path>` で helix.db `doc_artifacts` table に登録、PostToolUse hook で write 完了時に auto-register、期待 doc list vs 実体 file の差分検出 (Codex completion ≠ 実体出力 問題への構造的解決) |
| **FR-GR09** | **lint / formatter ecosystem 統合** | markdownlint (docs/*.md) / vale (prose) / shellcheck (cli/helix-*) / ruff + black (cli/lib/*.py) / yamllint (cli/config/*.yaml) / sqlfluff (migration *.sql) を pre-commit + Gate runner 連動、各 lint failure を `detector_runs` に record |
| **FR-GR10** | **artifact 期待値仕様** | PLAN/Sprint ごとの「期待される artifact 一覧」を `expected_artifacts.yaml` で定義可、不在検出で gate fail-close (FR-GR08 と連動) |
| **FR-GR11** | **fail_fix_log table** (穴を埋める原則の構造化) | helix.db に `fail_fix_log` table 新設 (event_kind / context_json / root_cause / mitigation_kind / mitigation_ref / status / created_at / resolved_at)。失敗事象を自動 / 手動で log、対策の構造化を強制。`helix incident log` / `helix incident list` CLI、PostToolUse hook で auto-log、memory feedback と双方向連携 |
| **FR-GR12** | **scan tool ecosystem** (FR-GR09 の補完) | gitleaks (secret scan) / trufflehog (credential leak) / semgrep (静的セキュリティ) を pre-commit / G2 / G4 / G6 で連動、結果を `fail_fix_log` + `detector_runs` に record |
| **FR-GR13** | **推挙システム経由 dispatch 必須化** | Opus が `helix codex --role X` を直書きするのを禁止、`helix skill chain "<task>"` 経由で recommender (gpt-5.4-mini) + effort-classifier が role/effort/skill を自動推挙 → dispatcher が codex 実行。例外条件 (推挙キャッシュ更新 cost 高 / 単発極小修正 / 明確 override) は理由を `fail_fix_log` に record |

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
| **FR-VS03** | G3 サブゲート `functional_freeze` 判定実装（master） | 判定式 `size=L AND drive in (fe/fullstack/db)` が成り立つ場合、`helix gate G3 --subgate functional_freeze` で pair_status='paired' を要求。L1 を master とし、`vmodel-semantics.yaml` の `requires_functional_freeze` は**要件準拠の補助情報**として反映 |
| **FR-VS04** | スプリント粒度の size 別判定 | `helix sprint plan --size <S/M/L> --drive <drive>` で必須 sprint_type 列挙 |
| **FR-VS05** | fullstack track 並列管理 | 同一 sprint_id で track=be / fe / contract が独立進行、片 track 未完了で G3/G4 fail-close |
| **FR-VS06** | pair_status 遷移管理（初期値含む） | 新規 `design_sprint_entries` は初期値 `pending`。遷移は `pending -> design_only / test_only -> paired` または `pending -> failed`、または `pending -> waived`（例外）を許容。`waived` は PM 明示承認が必要 |
| **FR-VS06.4** | pair_status waived 遷移運用 | `waived` は PM の明示承認（`approved` 判定）でのみ付与可。承認文脈は design_sprint_entry / plan / sprint_id と紐付けて記録 |
| **FR-VS07** | Reverse / Scrum モード対応（lifecycle 明文化） | 1) Reverse: RG4 (Gap & Routing) 完了時に `origin_mode` を `forward` へ自動遷移。2) `observed` / `inferred` は保持し、`observed`→`inferred`→`confirmed` の順で遷移。`confirmed` 遷移は RG3（Intent Hypotheses）完了後の PO 承認時のみ。3) Scrum: `confirmed` まで対象外、confirmed 後に Forward contract 生成と同時に sprint 開始 |

### 3.9 db 分離 + Event Sourcing + projector (Phase 7、PLAN-084 scope)

> **PLAN trace**: PLAN-084 (helix.db 6 分離 + Event Sourcing + projector)
> **V2 構築 5 段階**: ③ データベース管理フェーズ本体 (①② 完成後の位置付け)
> **前提**: §3.3 (helix.db v21 schema 拡張) を **6 db 物理分離へ拡張** する。§3.3 は否定せず、本 §3.9 が次段として接続する
> **tl-advisor Round 1 + Round 2 反映**: 6 軸判定表 / entity ownership / migration ゲート / projector 境界 / compatibility adapter を本文確定

#### FR-DB-SEP-01: 6 db 物理分離 + entity ownership + cross-db 規約

helix.db を 6 db (orchestration / vmodel / scrum / plan / backend / frontend) に物理分離する。各 db は SQLite file として独立し、cross-db 参照は projection_state table 経由のみ許可する。SQLite ATTACH DATABASE の利用は migration script / projector 内部に限定する。

**entity ownership 表**:

| db | canonical entity | 他 db からの参照経路 |
|---|---|---|
| orchestration.db | phase / gate / agent_slot / harness_event / harness_check_event | event subscribe 経由 (correlation_id で trace) |
| vmodel.db | artifact / artifact_link / cross_drive_integrity / drive_decision | event subscribe + projection_state 経由 |
| scrum.db | hypothesis / scrum_loop / srf_chain / scrum_local_loop / reverse_local_loop | event subscribe 経由 |
| plan.db | plan / sprint / task / wbs / design_sprint_drive_decision | projection_state snapshot 経由 |
| backend.db | api_endpoint / contract / impl_module / automation_run / audit_log / session_telemetry | projection_state snapshot 経由 |
| frontend.db | ui_component / mock / design_token / mock_promotion | projection_state snapshot 経由 |

**cross-db 規約**:

| 規約 | 内容 |
|---|---|
| cross-db FK | **禁止** (SQLite ATTACH 下でも foreign key 制約は db 内に閉じる) |
| 許可される cross-db 参照 | projection_state table 経由のみ (snapshot を read) |
| ATTACH 許可範囲 | **migration script + projector 内部のみ**。アプリケーション層 (cli/helix-*) からの ATTACH は禁止 |
| event envelope | 全 event は { event_id, aggregate_id, db_name, event_type, payload, correlation_id, occurred_at } の envelope に統一 |
| correlation_id | cross-db trace に必須。orchestration.db で発行、他 db の event は orchestration の correlation_id を継承 |
| domain logic 配置 | orchestration.db は event 中継のみ、domain logic を持たない (過集中防止) |

#### FR-DB-SEP-02: Event Sourcing 6 軸判定 hybrid 採用

6 db 一律ではなく、以下の 6 軸判定に基づくハイブリッド構成を採用する。

**6 軸判定表**:

| db | audit | temporal | event ordering | write 頻度 | retention | replay SLO | 採用方式 |
|---|---|---|---|---|---|---|---|
| orchestration | ◎ 必須 | ◎ 必須 | ◎ 必須 | 高 | 長期 (1y+) | < 5min | **event-sourced** |
| vmodel | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| scrum | ◎ 必須 | ◎ 必須 | ◎ 必須 | 中 | 長期 (1y+) | < 5min | **event-sourced** |
| plan | ◎ 必須 | △ 部分 | ○ 推奨 | 低 | 長期 (1y+) | < 30min | **hybrid (state snapshot + change log)** |
| backend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |
| frontend | △ 部分 | × 不要 | × 不要 | 高 | 短期 (90d) | n/a | **state-store** |

**採用決定ルール**: audit + temporal + event ordering の 3 軸が全て ◎ 必須 → event-sourced、1 軸でも × → state-store、その間 → hybrid。

**plan.db hybrid の具体形**:
- **state 部分**: SQLite table (plan / sprint / task / wbs) で snapshot 保持、直接 update 可、最新 state の query 高速
- **change log 部分**: plan_change_log table に append (status 遷移 / WBS 追加削除 / sprint complete)、event ordering 保持
- **同期方針**: state update と change log append は同一 transaction、不整合は migration mismatch gate と同じ機構で検出
- **projector 不要**: plan.db 内で state と change log が両方持つため外部 projector 不要 (event-sourced 3 db は projection_state を別 table で持つが plan.db は内部完結)

#### FR-DB-SEP-03: projector 責務分離 + 同期境界

event-sourced 3 db (orchestration/vmodel/scrum) には projector を配置し、event log から read model を構築する。projector は以下の制約を持つ。

**projector 制約表**:

| 制約 | 内容 |
|---|---|
| writer API | **禁止** (projector は event 生成 API を持たない、read model 生成専用) |
| cross-projection join | **禁止** (1 projector = 1 read model、依存 projection 間の結合は上位 query layer の責務) |
| replay idempotency | **必須** (dedup key = event_id + projector_id で冪等保証) |
| 配信方式 | async standard、同期は許可リスト 3 件のみ |
| failure isolation | projector failure は self 検知せず、detector が last_processed_event_id を監視 |

**同期許可リスト** (3 件のみ):

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
| lag fail-close 境界 | 同 1000 event 超過 → G2/G3/G4 gate 通過判定 block |
| lag 時 read 挙動 | 同期 projector: stale data 許容 + warning header / async projector: 直近 snapshot 返却 + retry-after header |

#### FR-DB-SEP-04: detector の 6 db 対応拡張 (本 PLAN は責務分離のみ)

既存 14 axis detector (§3.4) を 6 db each に割り当て、record strand anomaly 系 (schema drift / event order violation / projector lag / aggregate invariant violation) を追加する。本 PLAN-084 では責務分離のみ確定し、本格実装は PLAN-085 想定 (④ 問題発見配備フェーズ) で実施する。

責務分離:
- detector の入力は **常に event log** (record strand)
- artifact strand を直接 scan するのは V-model lint のみ (PLAN-075 scope)
- detector は orchestration.db 経由で実行者 (agent_slots) へ feedback channel を確立

#### FR-DB-SEP-05: 3 軸閉ループ (成果物 → 記録 → 実行者 feedback)

3 軸トライアングル (成果物・実行者・記録) を db 物理実装で閉ループ化する:

```
成果物 (vmodel.db) → 記録 (orchestration.db event log) → detector → 実行者 (agent_slots) feedback
                                                            ↓
                                                  artifact 修正 → 成果物へ
```

closed loop が成立することを L1 受入条件とする。

#### FR-DB-SEP-06: v30 → 6 db migration 戦略 (Strangler Fig + dual-write + compatibility adapter)

単一 helix.db (v30) → 6 db 分離は **Strangler Fig + dual-write + compatibility adapter** で段階移行する。

**migration ゲート表**:

| # | ゲート名 | 通過条件 | 停止条件 | 失敗時 owner / 動作 |
|---|---|---|---|---|
| 1 | dual-write start (v31 migration) | orchestration_events + projection_state + event_envelope table 追加完了、既存 v30 table 破壊なし | migration script の sqlite3 error / table 既存 conflict | **owner: Codex se** / rollback (v30 維持、v31 schema drop) |
| 2 | dual-write mismatch gate | 旧 db state と新 event log + projection_state の divergence 0 件 (10000 write 連続) | 1 件でも divergence 検出 | **owner: Codex se** / fail-close (cutover 不可、divergence 解消まで dual-write 継続) |
| 3 | shadow replay 検証 | 過去 1000 event を新 projector で replay → derived state が旧 db state と byte-level 一致 | replay 不一致 / projector exception | **owner: Codex se** / fail-close (projector bug 修正後 retry) |
| 4 | projector lag stabilization | lag < 100 event が連続 24h | lag > 100 event の発生 | **owner: PM (Opus)** / warning (cutover 延期、lag 原因調査) |
| 5 | cutover | 上記 4 ゲート全 PASS + ユーザー (PO) 承認 | ユーザー却下 / 4 ゲートいずれか fail | **owner: PM (Opus) → ユーザー (PO) 承認** / execute (旧 state table tombstone → drop) |
| 6 | rollback point | cutover 後 7d 以内に重大 anomaly (data loss / projector down >1h) | anomaly 検出 | **owner: PM (Opus) → ユーザー (PO) 承認** / 旧 db への切り戻し可能 (event log は保持) |

**migration 中の不変条件**:
- 既存 ② 実行ハーネス機能 (PLAN-078〜083) は dual-write 期間中も 100% 機能維持
- shadow replay 検証は migration 期間中常時稼働 (一度 PASS して終わりではない)

**compatibility adapter 対象 file 一覧** (grep 実結果、PLAN-084 §2.6):

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

adapter 責務: 既存 `helix_db._write_connection(None)` 呼び出しを 11 file (lib 8 + top-level CLI 3) 全てで透過的に 6 db 経路へ adapt、API 互換 100% 維持、dual-write 期間は旧 helix.db と新 6 db 両方に write。Phase 4.A smoke test で `helix-pr` / `helix-push` / `helix-agent list` の 3 top-level CLI smoke を必須化する (tl-advisor Round 1-3 反映、PLAN-084 §2.6 表と同期)。

#### FR-DB-SEP-07: Reverse の例外扱い

Reverse 機能 (R0-R4 + RGC、SKILL_MAP.md §HELIX Reverse) は **record strand を持たない例外** として扱う。Reverse は既存 code/設計の逆引きであり、新規 event 生成を伴わないため event log への write 対象外とする (read のみ)。

#### FR-DB-SEP-08: 二重らせん命名原則 ADR-019

HELIX 命名 = DNA 二重らせん由来を ADR-019 で正式化する (Phase 2 で起票)。artifact strand (V-model 4 artifact 双方向 trace) と record strand (event log) の二重らせんが L1 設計原理として機能する。L1 doc では FR として「ADR-019 を Phase 2 完遂時点で起票する」を要件化する。

#### FR-DB-SEP-09: frontend/backend state-store の再判定条件 (ADR-018 で管理)

frontend.db / backend.db は現時点で state-store 採用 (FR-DB02 6 軸判定で audit △ / temporal × / event ordering ×)。将来 event 化への再判定条件を ADR-018 に明記する:

| 再判定トリガ | 内容 |
|---|---|
| write 頻度低下 | 高頻度 → 中頻度以下に低下した場合、temporal query 要件の再評価 |
| audit 要件変化 | 法令対応 / compliance で audit trail が必須化した場合 |
| cross-db 参照増加 | backend/frontend → orchestration への参照が cross-db FK 禁止規約を頻繁に違反する場合 |
| 再判定タイミング | 6 ヶ月毎 ADR review、または上記トリガ発生時の臨時 review |

---

### 3.10 V5 framework 拡張 (Phase K、PLAN-091〜099 + PLAN-101 scope)

V5 framework 19 要素 (CONCEPT.md §10) を機能要件として確定。2026-05-22 readiness report に基づく段階採用 (#22 のみ Phase 4 P0、他は Phase 5 carry)。

| FR ID | 優先度 | 内容 | 採用根拠 |
|---|---|---|---|
| **FR-V5-22** | **P0 (Phase 4)** | **ADR Decision Graph Registry**: ADR 同士の supersedes / refines / relates_to を adr_decision_graph table で機械化、`helix adr graph` CLI で DOT/Mermaid 形式 export、ADR-021〜032 の関連性を可視化 | pdm tl-advisor 推奨 P0、MADR 2.1.2 cross-reference を拡張 (PLAN-101 + ADR-033 で実装) |
| FR-V5-19 | P1 (Phase 5 carry) | DORA mirror-multiplier guard (Curator rework rate): 同一 PLAN への retroactive 修正回数を helix.db で計測、閾値超過で WARN | DORA framework mirror、Curator 多重 rework 検出 |
| FR-V5-20 | P1 (Phase 5 carry) | Multi-agent topology (agent_slots 拡張): PLAN frontmatter agent_slots を hub-spoke / pipeline / parallel の topology 別に分類、role 重複を fail-close 化 | Anthropic multi-agent topology research 翻案 |
| FR-V5-MK01 | P1 (Phase 5 carry) | Northstar Metric (NSM): carry consumed/session を helix.db `session_carry_metric` table で計測、`helix metrics nsm` CLI で trend 表示 | marketing NSM 思想を internal dev tool に翻訳 |
| FR-V5-MK02 | P1 (Phase 5 carry) | Progressive disclosure: CLAUDE.md / SessionStart hook を初心者 → 熟練者で段階開示、context 過多防止 | Reforge Bowling Alley framework 翻案 |

#### FR-V5 受入条件 (AC-V5)

- AC-V5-22-1: `helix adr graph` で ADR 30+ 件の supersedes/refines graph が DOT 出力できる
- AC-V5-22-2: adr_decision_graph table が helix.db v36 schema (PLAN-101 で導入) に存在
- AC-V5-22-3: ADR 間の循環参照 (A supersedes B and B supersedes A) を `helix doctor` で fail-close 化
- AC-V5-19/20/MK01/MK02: Phase 5 carry のため AC は Phase 5 起票時に確定

#### Phase 5 carry 条件

FR-V5-19/20/MK01/MK02 は Phase 4 で **doc only** (本 §3.10 への記載) とし、実装は Phase 5 へ deferred。Phase 5 起票時に既存 PLAN-091 (agent_slots) / PLAN-093 (drift Curator) を scoped extension する形で取り込む (新規 PLAN 増やさない原則、tl-advisor 5 原則準拠)。

---

## §4 非機能要件 (NFR): 7 カテゴリ網羅

### 4.1 互換性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-01** | V1 動作互換性 | V2 完了まで V1 CLI / SKILL / hook 動作維持、helix.db v20 → v21 後方互換 |
| **NFR-02** | 段階的 migration | Phase ごとに既存テスト PASS 維持 (pytest 1138+ / bats 433+ / shell 614+) |
| **NFR-03** | 6 db 分離 compatibility adapter (PLAN-084) | v30 → v31 migration で既存 ② 実行ハーネス機能 (PLAN-078〜083) を破壊しない。`cli/lib/compatibility_adapter.py` で 11 file (lib 8 + top-level CLI 3) × 30+ 箇所の API 互換 100% 維持 (§3.9 FR-DB-SEP-06 参照) |

### 4.2 性能

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-10** | helix detect 全実行 ≤ 30s | `helix detect dashboard` 完了が 30s 以内 |
| **NFR-11** | pair-check ≤ 5s | `helix gate G<N> --pair-check <layer>` 完了 |
| **NFR-12** | SessionStart dashboard ≤ 1s | `helix detect dashboard --quick` 完了 |
| **NFR-13** | PostToolUse auto-record ≤ 5s | Write 完了 → DB 反映 |
| **NFR-14** | helix sync ≤ 60s | `helix sync --auto` 完了 |
| **NFR-15** | 6 db cross-db query lag (PLAN-084) | SQLite ATTACH DATABASE による cross-db query lag < 100ms (migration/projector 内部限定の ATTACH に適用) |
| **NFR-16** | event append latency (PLAN-084) | event log への append latency < 50ms (orchestration / vmodel / scrum の event-sourced 3 db 対象) |
| **NFR-17** | projector lag 平常時 (PLAN-084) | projector lag (last_processed_event_id 差分) < 100 event を平常稼働状態と定義。100 event 超過で WARN、1000 event 超過で gate fail-close (§3.9 FR-DB-SEP-03 参照) |

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
| **NFR-43** | 6 db 独立 migration (PLAN-084) | 6 db 分離後、各 db 単独で schema migration 可能。db 間の migration 依存を持たない設計を L3 D-DB-SEP-draft で確定する |
| **NFR-44** | frontend/backend 将来 event 化 (PLAN-084) | frontend.db / backend.db の event-sourced 化可否は ADR-018 で定義した再判定条件 (write 頻度低下 / audit 必須化 / cross-db 参照増加) に基づき 6 ヶ月毎に review する (§3.9 FR-DB-SEP-09 参照) |

### 4.6 可観測性

| ID | 要件 | 受入条件 |
|---|---|---|
| **NFR-50** | invocation_log 完備 | 全 LLM 呼び出し record (PLAN-063 W-1a 既存) |
| **NFR-51** | detector_runs 完備 | 全 detector 実行 record |
| **NFR-52** | session-start dashboard | 1 秒以内表示 |
| **NFR-53** | dev-state report 可能 | markdown / JSON export |
| **NFR-54** | projector lag 監視 (PLAN-084) | projector lag (last_processed_event_id 差分) を harness_monitor で継続監視、WARN/fail-close 境界を harness_monitor_events table に record する (§3.9 FR-DB-SEP-03 参照) |
| **NFR-55** | dual-write mismatch gate 監視 (PLAN-084) | migration 期間中、dual-write mismatch gate (旧 db state vs 新 event log の divergence 検出) を常時稼働させ、divergence 件数を detector_runs table に record する (§3.9 FR-DB-SEP-06 参照) |

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
| **AC-15** | 工程転換 (V-model スプリント化) 稼働 | **L4.5 Phase A**: 同一上位 sprint 内で `BE Sprint ∥ FE Sprint ∥ Contract Sprint` を同時進行。**L4.5 Phase B**: ① 3 track の成果物差分突合（設計 / テスト設計 / 実装 / review）。② 契約整合（contract と forward 接続）。③ 回帰テスト実行。`design_sprint_entries` table 存在、size 別必須 sprint_type CLI、fullstack track 並列管理、Phase B 完了時に G4 entry 条件を満たす |
| **AC-16** | G3 functional_freeze サブゲート動作 | `helix gate G3 --subgate functional_freeze --plan-id <id>` で pair_status='paired' 確認。判定式は `size=L AND drive in (fe/fullstack/db)`（L1 master）。vmodel-semantics.yaml は次 sprint で補助情報を同期。矛盾時は L1 を先行適用 |
| **AC-17** | origin_mode / evidence_status / direction 3 列追加 | `PRAGMA table_info` で contract_entries / design_review に該当列存在 |

### PLAN-084 (db 分離 + Event Sourcing) G1 通過条件

以下 7 項目が L1 本文に確定していることを PLAN-084 の G1 通過条件とする (frontmatter `acceptance` に対応):

| ID | 条件 | 対応箇所 |
|---|---|---|
| **AC-DB-SEP-01** | 6 db (orchestration / vmodel / scrum / plan / backend / frontend) の責務境界 + entity ownership + cross-db FK 禁止 + ATTACH 許可範囲 (migration/projector 内部限定) + event envelope + correlation_id 規約が L1 確定 | §3.9 FR-DB-SEP-01 entity ownership 表 + cross-db 規約表 |
| **AC-DB-SEP-02** | Event Sourcing 6 軸判定 matrix が L1 本文確定。3 event-sourced + 1 hybrid (plan = state snapshot + change log) + 2 state-store の採用根拠が明示 | §3.9 FR-DB-SEP-02 6 軸判定表 + plan.db hybrid 具体形 |
| **AC-DB-SEP-03** | projector 責務分離 + 同期許可リスト 3 件 + timeout 200ms + fallback (async enqueue) + lag 警告境界 100 event / fail-close 境界 1000 event が L1 本文確定 | §3.9 FR-DB-SEP-03 projector 制約表 + 同期許可リスト + timeout/lag 境界表 |
| **AC-DB-SEP-04** | migration gate 表 (dual-write start → mismatch gate → shadow replay → lag stabilization → cutover → rollback) の順序 / 停止条件 / 失敗時 owner が L1 本文確定 | §3.9 FR-DB-SEP-06 migration ゲート表 |
| **AC-DB-SEP-05** | compatibility adapter 対象 file 11 件 (lib 8: agent_slots / harness_monitor / scrum_local / reverse_local / http_api/routes 4 件 + top-level CLI 3: helix-pr / helix-push / helix-agent) が L1 本文列挙、adapter 責務範囲確定、Phase 4.A smoke test で top-level CLI 3 件カバー必須 | §3.9 FR-DB-SEP-06 compatibility adapter 対象 file 一覧 |
| **AC-DB-SEP-06** | 3 軸トライアングル + 二重らせんが ADR-019 で正式記述 (Phase 2 起票)、frontend/backend = state-store 再判定条件が ADR-018 に明記 (Phase 2 起票) | §3.9 FR-DB-SEP-08 / FR-DB-SEP-09 |
| **AC-DB-SEP-07** | L4 完遂で event-sourced 3 db (orchestration/vmodel/scrum) が dual-write 稼働、projector 1+ 稼働 (lag < 100 event)、shadow replay PASS、dual-write mismatch gate 0 件、既存 ② 実行ハーネス機能 (PLAN-078〜083) 破壊なし | L4 Phase 4.B / 4.C 完遂時の受入確認 |

> **PLAN trace**: PLAN-084 Phase 1.3 完遂 (2026-05-17)。Phase 2 (CONCEPT.md + ADR-018/ADR-019 起票) で L2 本文を確定する。

### L4.5 phase B 補完定義

#### P2-4: Phase B 詳細（追加定義）

- **Phase A（L4.5 前半）**: `drive=fullstack` では `BE Sprint ∥ FE Sprint ∥ Contract Sprint` の 3 track を同一上位 sprint 内で並列実行する。  
  - 並列開始条件:
    - `design_sprint_entries` で 3 track それぞれの `sprint_id` を揃える
    - `track=be` / `track=fe` / `track=contract` の依存を `design_sprint_artifact_links` へ明示登録
    - pair_status は `pending` で初期化し、PM が waived 条件を申請していない状態を確認
- **Phase B（L4.5 後半）**: 下記を同一 sprint 内で実施してから G4 entry 判定に進む。
  - 3 track の成果物差分突合（設計差分、テスト差分、実装差分）を `design_sprint_artifact_links` の関連証跡として保存
  - 起点 contract / Forward contract への契約整合性照合（未整合時は G4 entry 条件不成立）
  - 回帰テスト実行、失敗時は該当 track の `pair_status` を `failed` に更新し再計画
  - 契約整合結果を forward 接続時に再検査し、差分未解決は hold へ戻す
- **完了条件**: 上記完了時点を L4.5 Phase B 完了条件とし、次の G4 entry 可能条件は `all_track_status=done ∧ pair_status in (paired, waived)`。
- **size 別 sprint 粒度**: S=1 sprint、M=2 sprint、L=3 sprint。L が 3 sprint の場合は最終 sprint で Phase A/B を明示的に閉じる。

#### P2-5: functional_freeze 判定優先順位

- **master 宣言**: `size=L AND drive in (fe/fullstack/db)` の判定は本 L1（§5 AC-16）を優先する。
- **補助参照**: `cli/config/vmodel-semantics.yaml` の `requires_functional_freeze` は L1 判定結果を再現するための実装ガイド。
- **矛盾時の扱い**: 判定が競合した場合は本 L1 を正とし、yaml 側は次 sprint の再同期対象として backlog 化。

#### P2-7: Reverse → Forward lifecycle 明文化

- `origin_mode='reverse'` の場合、`RG4`（Gap & Routing）完了後に `forward` へ自動遷移し、`functional_freeze` は forward 接続後 sprint から評価。
- `origin_mode` と `evidence_status` は同一 entry 上でトレース可能に保持し、`evidence_status` は `observed -> inferred -> confirmed` として遷移。
- `observed / inferred` から `confirmed` への遷移タイミングは **RG3 終了後の PO 承認**。その後 `RG4` を経て forward 接続を実行。
- 逆方向の再接続時は Reverse 側の `functional_freeze` を skip（forward 側にのみ適用）。

#### P2-6: pair_status 遷移図（明確化）

| step | from | to | 前提 |
|---|---|---|---|
| 1 | pending | design_only | architecture / detailed の設計側作業のみ完了 |
| 2 | pending | test_only | 対応テスト側の設計・実装のみ完了 |
| 3 | design_only | paired | テスト側の対応が完了し、pairing 条件を満たす |
| 4 | test_only | paired | 設計側の対応が完了し、pairing 条件を満たす |
| 5 | pending | failed | 重大阻害（再計画が必要） |
| 6 | pending | waived | PM approved を満たし、pairing 例外申請を受理 |

- `waived` からの復帰は同一 sprint 中は原則不可。`waived` は監査上 "承認付き未ペア" として独立管理し、再開条件は次 sprint の再起動時点で再評価。

#### P2-4 補遺: L4.5 受入チェックリスト

- Phase A 完了チェック:
  - 3 track の sprint_id 粒度が一致
  - `design_sprint_entries` に be/fe/contract の track レコードが揃っている
  - 3 track 合意の依存順が sprint 設計図（artifact links）に反映されている
- Phase B 完了チェック:
  - diff 突合の照合結果が全 track で "pass"
  - forward contract 生成前に整合失敗を 0 件化
  - 回帰テストの再実行結果が G4 前提として pass
- G4 entry 条件:
  - `all_track_status=done`
  - `forward_ready=true`
  - `pair_status in (paired, waived)`
- `vmodel-semantics.yaml` の lifecycle 更新は本 L1 受入条件後、W-5 で追加実装する（本 W-4 は文言明文化のみ）。

#### P2-4 補助: Phase B 運用シナリオ

1. **正常系**:  
   1. Track 3 本が設計完了 `paired` を達成  
   2. 差分突合結果が全 track pass  
   3. 契約整合チェックを通過  
   4. 回帰 test が green  
   5. G4 entry 条件で承認し次 sprint へ進行
2. **再試行系**:  
   1. 差分突合 fail の track は `failed` に変更  
   2. 監査ログへ再試行計画を記載  
   3. track 側修正後、`pending` を経由して再遷移可能
3. **waived 系**:  
   1. 既存要件を満たせない場合のみ `waived` 申請  
   2. PM 承認で例外扱い、`pair_status in (paired, waived)` 判定を引き続き成立

#### P2-5 補助: 受入時の判定照合

- 判定対象項目:
  - `size` が L かどうか
  - `drive` が fe/fullstack/db のいずれかか
  - 実際の `requires_functional_freeze` 設定値
- 運用時ルール:
  - L1 判定が true であれば、yaml の値が false でも WIP ではなく **実行上は強制 true** と扱う
  - yaml の値だけで true が立つ場合は次 sprint backlog として `yaml_sync_backlog` に起票
  - 競合解消後は AC-16 で示した優先順位に従って再判定

#### P2-6 補助: 監査トレース定義

| フィールド | 必須 | 説明 |
|---|---|---|
| `pair_status` | ○ | pending / design_only / test_only / paired / waived / failed |
| `evidence_status` | ○ | observed / inferred / confirmed |
| `origin_mode` | ○ | reverse / forward |
| `track` | ○ | be / fe / contract / shared |
| `actor` | ○ | 申請者 / 承認者識別子 |
| `approved_by` | × | waived 申請の場合のみ必須 |

- 監査上の invalid 遷移例:
  - `paired -> waived`
  - `failed -> waived`
  - `design_only -> test_only`（中間ステータス飛び越え）

#### P2-7 補助: Reverse → Forward 証跡の保存方針

- Reverse 完了時 (`origin_mode=reverse`) は evidence を保持したまま保留状態とする
- RG3 で PO 承認を受けて `confirmed` を確定してから RG4 実施
- RG4 完了後、`origin_mode` を forward に更新し、forward 側にのみ functional_freeze を適用
- この仕様は `audit-summary.md DR-014` の「Reverse の R3 後 Forward 接続」に整合

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
- [ ] §3 FR 5 Phase 順序で 11 セクション網羅 (計 79、§3.9 PLAN-084 / §3.10 V5 framework 追加)
  - §3.0 既存整理 INV01-06 (6)
  - §3.1 V-model 強化定義 VD01-09 (9)
  - §3.2 V-model 実装 V01-07 (7)
  - §3.3 helix.db 拡張 DB01-10 (10)
  - §3.4 検出ガードレール強化 GR01-07 (7)
  - §3.5 自動化 A01-08 (8)
  - §3.6 可視化 EM01-06 (6)
  - §3.7 派生 (FE01-06 / AT01-05 / LI01-03 計 14)
  - §3.8 工程転換 VS01-VS07 (7)
  - §3.9 db 分離 + Event Sourcing (PLAN-084 scope、FR-DB01-09 / AC-DB01-07)
  - §3.10 V5 framework 拡張 FR-V5-22 / 19 / 20 / MK01 / MK02 (5、P0=1 件 + P1=4 件 Phase 5 carry)
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
