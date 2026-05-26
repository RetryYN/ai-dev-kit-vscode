---
doc_id: L3-helix-workflows-functional-requirements-detail
title: "HELIX-workflows V2 機能要件 (確定版、L3 詳細化)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L3
pairs_with: L12
next_pair_freeze: L4
canonical_source: HELIX-workflows/helix-process/L3-requirements-definition.md
parent_plan: L3-helix-workflows-機能要件plan
related_l1:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
pair_artifact: docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md
---

# HELIX-workflows V2 機能要件 (確定版、L3 詳細化)

> **本 doc の位置づけ**: L1 [機能要求 doc](../L1-requirements/helix-workflows-functional-requirements.md) FR-01〜FR-12 と [技術要求 doc](../L1-requirements/helix-workflows-technical-requirements.md) TR-01〜TR-08 を、L3 の規約に従って **機能一覧 (確定版) / 機能仕様 / 入出力定義** に統合詳細化した正本。
>
> **scope**: FR の仕様・CLI 契約・副作用・技術制約まで。API / DB schema の実装詳細、detector algorithm の厳密化、migration script の詳細は L4-L6 で確定する。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 機能一覧 (FR-* 確定版)

| L3 FR-ID | 機能名 | 主な統合元 | 概要 |
|---|---|---|---|
| FR-NSM-01 | NSM 計測・整合スコア機能 | L1 FR-01, TR-05 | V-model 整合 PLAN 完遂数と 6 axes score を集計し、月次・週次 query に返す |
| FR-GR-01 | Guardrail fail-close 機能 | L1 FR-02, TR-02 | Coverage / Error Budget / TTFSP の 3 軸を独立監視し、逸脱時に block または throttle を返す |
| FR-TDD-01 | TDD 順序強制機能 | L1 FR-03, TR-04 | L7 sprint 7 step の順序を機械強制し、テストアフターを fail-close する |
| FR-9MODE-01 | 9 mode 入口判定機能 | L1 FR-04, TR-01 | signal / detect 結果から mode 候補と route 根拠を返す |
| FR-GATE-01 | gate 合成判定機能 | L1 FR-05, TR-05 | `static_subchecks AND ai_review_required_when(...)` を評価して gate verdict を返す |
| FR-IMPACT-01 | 影響範囲 query 機能 | L1 FR-06, TR-05 | 4 artifact trace と mode event を横断して影響範囲を 5 秒以内に返す |
| FR-EVT-01 | Forward 復帰 event 機能 | L1 FR-07, TR-06 | 9 mode closure を記録し、Forward の昇格先と closure metadata を保持する |
| FR-4ART-01 | 4 artifact / pair freeze 監査機能 | L1 FR-08, TR-06 | 設計・実装・テスト設計・テストコードの trace 欠落を warn / fail-close で出す |
| FR-INV-01 | 資産 inventory / density 可視化機能 (+ implementation_status 列必須化) | L1 FR-09, TR-06, **BR-09** (2026-05-26 拡張) | skill / CLI / PLAN / docs / DB schema を工程別に登録し、密度と空白を表示する + 設計 doc 内 `implementation_status` 列 (installed / partial / L4-carry / not-implemented) 必須化、`helix doctor check_glossary_coverage` で L0 §12.1 整合監査 |
| FR-CTX-01 | layer context injection 機能 | L1 FR-10, TR-02, TR-07 | 工程別に agent / skill / command / model route を注入し、AI の選択空間を制約する |
| FR-DRIFT-01 | discrepancy routing 機能 | L1 FR-11, TR-03 | drift / trace 欠落 / 環境差異を検知し、interrupt / recovery / reverse normalization へ送る |
| FR-PLAN-01 | PLAN dependency / generates trace 機能 | L1 FR-12, TR-08 | PLAN frontmatter の依存関係と生成物を追跡し、互換期間中の drift を明示する |
| FR-DOCTOR-01 | doctor 総合監査機能 | L1 FR-08, FR-11, TR-04 | doctor が監査 view を束ね、warn 集計と fail-close 候補を返す |
| FR-MIGR-01 | schema migration / retrofit 機能 (+ Strangler Fig Pattern 段階置換) | L1 TR-05, TR-08, **BR-10** (2026-05-26 拡張) | V1→V2 / advisory→fail-close の移行を migration log つきで進める + **Strangler Fig Pattern (Fowler 2004) 段階置換 + Phase 別残量管理 (Phase α/β/γ kill criteria)**、`helix doctor check_migration_pending` (L4 carry) で残量監査 |
| **FR-DOCREVIEW-01** (新規、2026-05-26) | **ドキュメント品質レビュー機能** | **BR-11** | `helix codex --role doc-reviewer` (gpt-5.5 high read-only) 召喚で 4 視点 (Correctness / Completeness / Consistency / Clarity) + 業界標準 (Diátaxis / arc42 / ISO 26515:2018) + V-model 量閉じ性 / implementation_status 列必須を統合検査、判定 (approve / conditional_approve / blocked) + P0/P1/P2/P3 指摘返却、`helix doctor check_doc_review_coverage` で召喚率 ≥ 95% 監査 |
| **FR-CHANGEPROP-01** (新規、2026-05-26 BR-12 由来) | **変更追跡 + デグレ禁止 ratchet 機能** | **BR-12** | 上流 ID (BR-* / FR-* / NFR-*) 追加・更新・削除 commit を検出 → 下流対応 ID (BR-RULE-* / FR-* / NFR-* / AC-* / OT-*) が同 commit / 直前後 N commit 以内に存在するか機械検証 + balance_ratio < 1.0 regression を前 commit との diff で検出 + 上流 ID 参照の下流 ID trace 切れ検出。3 つの `helix doctor check_*` (`check_upstream_downstream_alignment` + `check_balance_ratio_regression` + `check_id_reference_completeness`) を pre-commit / CI hook で fail-close。Ratchet 機構: balance_ratio の過去最小値より下回ったら fail-close (品質後戻り禁止) |

## §2 機能仕様

### FR-NSM-01 NSM 計測・整合スコア機能

- 振る舞い: `plan_registry`、`gate_pass`、`test_design_pair`、`code_implementation` 等の trace を入力に、`layer / kind / pair_freeze / 4artifact / gate_pass / done` の 6 axes を判定し、対象期間の NSM と `v_model_alignment_score` を返す。
- 状態遷移: `score_status = pending -> computed -> published`。trace 欠落時は `published` に遷移せず `pending` を維持する。
- エラー処理: 必須 row 欠落時は exit code 2、期間指定不正時は exit code 1、DB timeout 時は fail-open せず `score_status=deferred` を返す。

### FR-GR-01 Guardrail fail-close 機能

- 振る舞い: Pair Freeze Coverage、Agent Error Budget、TTFSP を独立計測し、しきい値逸脱ごとに `pass / warn / block / throttle` を返す。
- 状態遷移: `healthy -> warning -> blocking`。手動解除または次回正常観測で `healthy` に戻る。
- エラー処理: Guardrail 定義欠落時は判定不能として exit code 2、計測ソース不在時は `warning` を返し gate 継続を止める。

### FR-TDD-01 TDD 順序強制機能

- 振る舞い: sprint step の進捗、テスト存在、レビュー完了を入力に、S1→S7 の進行可否を判定し、許可されない step 進行を block する。
- 状態遷移: `S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7`。S2 不在で S3 へ、S5 不在で S7 へは遷移不可。
- エラー処理: step metadata 不整合時は `interrupted`、対象テスト不在時は `blocked`、verify command timeout 時は `blocked` を返す。

### FR-9MODE-01 9 mode 入口判定機能

- 振る舞い: signal、artifact の有無、運用イベント、設計差分の有無を入力に、Forward / Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery の候補と根拠を返す。
- 状態遷移: `unclassified -> suggested -> selected`。利用者が明示採用すると `selected` になる。
- エラー処理: signal 不足時は `Forward` を既定にせず `manual_review_required` を返す。相反 signal が並立する場合は優先順位つき候補配列を返す。

### FR-GATE-01 gate 合成判定機能

- 振る舞い: gate 名、対象 PLAN、pair artifact、関連 doc を入力に、`static_subchecks` を先行実行し、その後 `ai_review_required_when(...)` を評価して最終 verdict を生成する。
- 状態遷移: `not_run -> static_checked -> ai_reviewed -> decided`。AI review 不要なら `static_checked -> decided` を許可する。
- エラー処理: 未知 gate 指定は exit code 1、必須 artifact 不在は exit code 2、AI review 実行不能時は `blocked` を返す。

### FR-IMPACT-01 影響範囲 query 機能

- 振る舞い: `plan_id`、artifact path、symbol、schema object のいずれかを起点に、双方向 trace と mode event をたどって関連 PLAN / doc / test design / code / migration を返す。
- 状態遷移: `requested -> resolved -> rendered`。候補 0 件でも `rendered` には到達する。
- エラー処理: 5 秒 SLA 超過時は部分結果と `timeout=true` を返す。起点未解決時は空結果ではなく `not_found` を返す。

### FR-EVT-01 Forward 復帰 event 機能

- 振る舞い: mode closure 時に `source_mode`、`target_forward_layer`、`closure_reason`、`idempotency_key` を記録し、Forward の昇格候補を返す。
- 状態遷移: `open -> closing -> forwarded`。重複 event は `closing` を再実行せず idempotent に処理する。
- エラー処理: target layer 未決定時は `forward_pending`、同一 key 衝突時は既存 row を返し重複作成しない。

### FR-4ART-01 4 artifact / pair freeze 監査機能

- 振る舞い: PLAN frontmatter、設計 doc、テスト設計 doc、テストコード、実装コードの trace link を照合し、欠落・不整合・片方向リンクを抽出する。
- 状態遷移: `unchecked -> consistent` または `unchecked -> warning -> blocking`。
- エラー処理: expected set が定義されていない工程は `advisory_only`、必須工程で欠落した場合は `blocking` を返す。

### FR-INV-01 資産 inventory / density 可視化機能

- 振る舞い: skill、CLI、PLAN、docs、DB schema を工程タグつきで登録し、工程別件数、孤立資産、未割当資産、密度分布を返す。
- 状態遷移: `discovered -> mapped -> published`。未割当は `mapped` に到達できず `needs_classification` を維持する。
- エラー処理: 工程タグ未定義は `warning`、重複登録は既存 row を更新候補として返す。

### FR-CTX-01 layer context injection 機能

- 振る舞い: process layer と role を入力に、`vmodel-semantics.yaml` と `models.yaml` から mandatory_agents、recommended_skills、recommended_commands、model route を束ねて返す。
- 状態遷移: `requested -> bundled -> injected`。bundle 生成後に CLI/hook へ注入される。
- エラー処理: layer 未定義は exit code 2、skill path 不在は `bundle_warning`、model route 欠落は role 既定値で代替し warning を返す。

### FR-DRIFT-01 discrepancy routing 機能

- 振る舞い: doctor、drift-check、inventory audit、OS/runtime 検知結果を入力に、`manual_review / interrupt / recovery / reverse_normalization` の送出先を決める。
- 状態遷移: `detected -> classified -> routed -> closed`。
- エラー処理: 分類不能時は `manual_review` に倒す。Linux/macOS 差異で再現性が割れる場合は `environment_mismatch` を記録する。

### FR-PLAN-01 PLAN dependency / generates trace 機能

- 振る舞い: PLAN frontmatter の `dependencies` と `generates` を解釈し、上流下流、artifact 逆引き、deprecated path の互換追跡を返す。
- 状態遷移: `parsed -> linked -> validated`。互換 path を含む場合は `validated_with_warning` を許可する。
- エラー処理: parent 不在は `warning` または `blocking`、path 不達は `broken_link`、互換期限切れは `blocking` を返す。

### FR-DOCTOR-01 doctor 総合監査機能

- 振る舞い: pair freeze、4 artifact、inventory、migration、context injection、mode transition の監査結果を束ね、warn 件数、severity、修復候補を返す。
- 状態遷移: `scanned -> summarized -> reported`。
- エラー処理: 個別監査が一部失敗しても summary は返す。ただし `critical` が 1 件でもある場合は exit code 2 とする。

### FR-DOCREVIEW-01 ドキュメント品質レビュー機能 (2026-05-26 BR-11 由来、新規追加)

- **目的**: tl-advisor (技術判断) / pm-advisor (大局判断) / pmo-sonnet (汎用) / code-reviewer (5 軸 code) と責務分離した **doc 品質専用 review** を提供
- **CLI 契約**: `helix codex --role doc-reviewer --task "..."` または `--task-file <path>` で召喚、read-only (Edit/Write/NotebookEdit 禁止)
- **入力**: review 対象 doc path / scope / 該当工程 (L0/L1/L3/L4/G ゲート) / 既存指摘 (前段 audit 結果)
- **出力**: 判定 (approve / conditional_approve / blocked) + P0/P1/P2/P3 指摘 + 修正案 + 残リスク + 観点 (Correctness / Completeness / Consistency / Clarity / 業界標準 / V-model)
- **観点 4 視点**:
  1. **Correctness** (事実整合): 主張 ↔ 実体 (CLI / file / schema / table / view / config) の diff、`implementation_status` 列必須
  2. **Completeness** (章充足): doc-system-architect 必須 6 項目 + arc42 章 + Diátaxis 4 mode + V-model 4 artifact の存在
  3. **Consistency** (用語・構造整合): L0 §12 Glossary SSoT との用語ゆれ、anti-corruption layer 遵守
  4. **Clarity** (可読性): Why > What > How 順序、section / 図表 / cross-reference の適切性
- **業界標準整合**: Diátaxis (Procida 2017) / arc42 v8 / ISO/IEC/IEEE 26515:2018 / ISO/IEC/IEEE 26513:2017 / DDD SSoT (Evans 2003)
- **HELIX 固有検査**: balance_ratio ≥ 1.0 / pair freeze frontmatter / implementation_status 列 / V-model 4 artifact 双方向 trace / migration pipeline 整合 (BR-RULE-09 + BR-RULE-10)
- **召喚タイミング**: 大規模 doc 改定 (~500 行+) / G0.5・G1・G3・G7 ゲート evidence / V-model pair freeze 前
- **責務分離**: tl-advisor (技術判断 adversarial) と並走、code-reviewer (code 5 軸) は対象外、pmo-sonnet (汎用 read-only) より特化
- **実体化**: `cli/roles/doc-reviewer.conf` (gpt-5.5 high read-only) + `skills/workflow/doc-review/SKILL.md`
- **副作用**: なし (read-only)
- **技術制約**: Codex CLI gpt-5.5 high、thinking budget 大 (~30-60 sec response、token ~50-130K)、stdout に SUMMARY block + rollout.jsonl で詳細取得可能 ([[feedback_rollout_jsonl_bypass_pattern]])
- **機械判定 carry (L4)**: `helix doctor check_doc_review_coverage` 新設、直近 30 commit のうち大規模 doc 改定 commit で召喚 evidence + 判定結果が残された率 ≥ 95% を fail-close

### FR-CHANGEPROP-01 変更追跡 + デグレ禁止 ratchet 機能 (2026-05-26 BR-12 由来、新規追加)

- **目的**: 既存 V-model pair freeze (balance_ratio ≥ 1.0) は結果整合のみで、**上流変更 → 下流必須修正の機械追跡が完全不在** という framework 欠陥を解消
- **3 軸機械強制 (L4 carry、`helix doctor check_*` 3 件 + pre-commit / CI hook)**:
  1. **`check_upstream_downstream_alignment`**: 上流 ID (BR-* / FR-* / NFR-*) 追加 / 更新 / 削除 commit で下流対応 ID (BR-RULE-* / FR-* / NFR-* / AC-* / OT-*) が同 commit / 直前後 N commit (default N=3) 以内に存在するか機械検証、不在で fail-close。例外: `kind=reference` / `is_reference: true` doc / deferred-findings.yaml 登録済 deprecation
  2. **`check_balance_ratio_regression`**: 全 V-model pair (L1↔L14, L2↔L10, L3↔L12, L4↔L9, L5↔L8, L6↔L7) の `balance_ratio` を前 commit との diff で集計、< 1.0 regression または **過去最小値より下回り (Ratchet 機構)** で fail-close
  3. **`check_id_reference_completeness`**: 上流 ID を参照する下流 ID の trace 切れ (例: BR-09 参照の FR-INV-01 が削除された) を grep + frontmatter trace で検出、孤立 ID を warn → fail-close
- **CLI 契約**: `helix doctor --check-changeprop` で 3 軸一括実行、`--ratchet` flag で過去最小値ベース ratchet 適用、`--commit-range <range>` で diff scope 指定
- **入力**: commit range (default: HEAD~1..HEAD)、N commit window (default: 3)、ratchet baseline (default: `.helix/audit/balance-ratio-baseline.yaml`、L4 carry)
- **出力**: pass / fail / warn 各 ID 列 + 違反 ID list + 修正 suggestion (例: 「BR-09 追加されたが下流 FR-INV-01 拡張なし → L3 FR doc §1 に BR-09 列追加が必要」)
- **副作用**: `.helix/audit/balance-ratio-baseline.yaml` (Ratchet baseline、L4 carry) 更新、`.helix/audit/changeprop-violations.yaml` (違反 log、L4 carry) 出力
- **業界標準整合**:
  - **Continuous Delivery** (Humble & Farley 2010): automated test + 段階 deploy で品質後戻り禁止
  - **Don't Break the Build** (Google "Building Secure & Reliable Systems" 2020): branch protection + required checks
  - **Ratchet Constraints** (Google Testing Blog "The Tax Strikes Back" 2020): 機械強制 ratchet で過去最良値を baseline 化
  - **Hyrum's Law** (Hyrum Wright): observable behavior に依存する下流が存在する前提で上流変更を扱う
  - **Semantic Versioning 2.0.0**: ID rename / delete は破壊的変更扱い、deferred-findings.yaml 登録必須
  - **Trunk-based Development + branch protection**: required checks に本機能 3 件を組込
- **technical 制約**: pre-commit hook + CI hook 統合、`helix-doctor` 拡張 (実装: cli/lib/changeprop_check.py 新設、L4 carry)、SQLite (`helix.db`) に `changeprop_violations` table 追加 (L4 carry)
- **責務分離**: BR-09 (実在マッピング) / BR-10 (Strangler Fig 段階移行) / BR-11 (doc-reviewer 召喚) は **個別品質維持**、BR-12 (本 FR) は **全 BR-* / FR-* / NFR-* / AC-* / OT-* の上流↔下流 alignment 横断強制**

### FR-MIGR-01 schema migration / retrofit 機能

- 振る舞い: DB schema version、retrofit 対象、互換ウィンドウ設定を入力に、migration plan、実行結果、rollback 可否、retrofit backlog を返す。
- 状態遷移: `planned -> running -> completed` または `planned -> blocked`。
- エラー処理: destructive migration は自動実行せず `manual_approval_required`、互換期間外の古い router が残る場合は `warning` を返す。

## §3 入出力定義

| FR-ID | CLI input | CLI output | 副作用 | L1 TR 技術制約 |
|---|---|---|---|---|
| FR-NSM-01 | `helix db query-functional-freeze-status --from <date> --to <date>` | `stdout`: NSM / score JSON、`stderr`: 欠落 trace、`exit 0/1/2` | helix.db view 参照、集計 cache 更新 | Python 3.11+、SQLite 3.40+、`schema_migration_log` / score view 利用 |
| FR-GR-01 | `helix gate guardrail --metric <coverage|error-budget|ttfsp>` | `stdout`: verdict、`stderr`: 逸脱理由、`exit 0/2` | guardrail event 記録、agent throttle flag 更新 | model routing は `models.yaml` 正本、guardrail は fail-close 優先 |
| FR-TDD-01 | `helix sprint check-order --plan-id <id> --step <Sx>` | `stdout`: allow / block、`stderr`: 欠落 step、`exit 0/2` | sprint state 更新、block reason 記録 | pytest / Bats / verify script が判定ソース |
| FR-9MODE-01 | `helix route eval --signal <json>` | `stdout`: mode 候補配列、`stderr`: 不足 signal、`exit 0/1/2` | suggestion log 更新 | Python + Bash runtime 共存、Linux / macOS 対応 |
| FR-GATE-01 | `helix gate G3 --plan <path>` | `stdout`: verdict / static summary、`stderr`: blocker 詳細、`exit 0/2` | gate_pass、decision_trace 更新 | SQLite view と AI review 条件を併用 |
| FR-IMPACT-01 | `helix code impact-range --plan-id <id>` | `stdout`: 影響範囲一覧、`stderr`: timeout / not found、`exit 0/1/2` | trace cache 参照、query metric 記録 | 5 秒 SLA、4 artifact trace / mode event 利用 |
| FR-EVT-01 | `helix mode close --mode <name> --target-layer <Lx>` | `stdout`: closure result、`stderr`: route 保留理由、`exit 0/2` | `mode_transition` row 追加 | event row に `source_workflow` / `idempotency_key` 必須 |
| FR-4ART-01 | `helix doctor --check trace` | `stdout`: trace summary、`stderr`: 欠落一覧、`exit 0/2` | warning / blocker 集計更新 | 双方向 trace metadata を DB / doc の両方で保持 |
| FR-INV-01 | `helix asset inventory --layer L3` または `helix code stats --inventory` | `stdout`: density report、`stderr`: 未割当資産、`exit 0/1` | inventory table 更新 | `source_workflow` 付き metadata、工程タグ必須 |
| FR-CTX-01 | `helix context bundle --layer L3 --role se` | `stdout`: 注入 bundle、`stderr`: 欠落 skill、`exit 0/2` | bundle cache 更新、hook 注入 | `models.yaml` / `vmodel-semantics.yaml` が正本 |
| FR-DRIFT-01 | `helix drift-check --json` | `stdout`: routed discrepancy、`stderr`: 分類不能項目、`exit 0/2` | discrepancy log 更新、route suggestion 記録 | Linux / macOS 差異を区別、Claude/Codex 両 runtime で再現 |
| FR-PLAN-01 | `helix plan generates --plan-id <id>` | `stdout`: dependency graph、`stderr`: broken link、`exit 0/1/2` | plan graph cache 更新 | 1 release 互換を維持し deprecated warning を返す |
| FR-DOCTOR-01 | `helix doctor --json` | `stdout`: audit summary JSON、`stderr`: critical findings、`exit 0/2` | warn 集計、readiness input 更新 | pytest / Bats / verify / inventory audit を横断 |
| FR-MIGR-01 | `helix db migrate --plan v2-freeze` | `stdout`: migration result、`stderr`: manual approval required、`exit 0/2` | schema version 更新、migration log 追加 | SQLite migration、互換期間中 router 並走、rollback 情報保持 |

## §4 L1 → L3 統合 mapping

| L1 ID | L3 FR-ID | 統合内容 |
|---|---|---|
| FR-01 | FR-NSM-01 | 6 axes 判定、NSM 集計、alignment score |
| FR-02 | FR-GR-01 | Guardrail 3 軸、fail-close、throttle |
| FR-03 | FR-TDD-01 | L7 sprint 7 step、順序 block |
| FR-04 | FR-9MODE-01 | 9 mode 入口判定 |
| FR-05 | FR-GATE-01 | gate 合成式、static/AI 境界 |
| FR-06 | FR-IMPACT-01 | 影響範囲 query、5 秒 SLA |
| FR-07 | FR-EVT-01 | Forward 復帰 event、target layer |
| FR-08 | FR-4ART-01, FR-DOCTOR-01 | 4 artifact / pair freeze 監査、doctor 集約 |
| FR-09 | FR-INV-01 | 資産 inventory、density 可視化 |
| FR-10 | FR-CTX-01 | layer context injection |
| FR-11 | FR-DRIFT-01, FR-DOCTOR-01 | discrepancy routing、doctor 集約 |
| FR-12 | FR-PLAN-01 | dependencies / generates trace |
| TR-01 | FR-9MODE-01 | Python/Bash runtime 前提 |
| TR-02 | FR-GR-01, FR-CTX-01 | model routing、role-based injection |
| TR-03 | FR-DRIFT-01 | Linux/macOS 差異、Claude/Codex 両対応 |
| TR-04 | FR-TDD-01, FR-DOCTOR-01 | pytest / Bats / verify の検証面 |
| TR-05 | FR-NSM-01, FR-GATE-01, FR-IMPACT-01, FR-MIGR-01 | helix.db schema、view、migration log |
| TR-06 | FR-EVT-01, FR-4ART-01, FR-INV-01 | trace metadata、source_workflow、inventory row |
| TR-07 | FR-CTX-01 | `vmodel-semantics.yaml` 注入契約 |
| TR-08 | FR-PLAN-01, FR-MIGR-01 | compatibility、deprecated warning、段階 retrofit |

## L12 PAIR PROPOSE (§2 機能系 AC-FR-*)

### AC-FR-01: NSM 計測・整合スコア

- **対象 FR**: FR-NSM-01
- **デプロイ後検証内容**: 週次 / 月次で NSM と `v_model_alignment_score` を集計し、6 axes 欠落時に未公開で止まることを確認する
- **受入基準**: `aligned_plan_count >= 5/week` かつ 欠落 trace を含む PLAN が `published` に遷移しない
- **検証 step**: (1) 正常 trace を持つ PLAN 群を集計する (2) 欠落 trace を混ぜる (3) score と status を比較する

### AC-FR-02: Guardrail fail-close

- **対象 FR**: FR-GR-01
- **デプロイ後検証内容**: Coverage、Error Budget、TTFSP の 3 軸が独立に warning / block / throttle を返すことを確認する
- **受入基準**: 各軸が単独逸脱時に正しい verdict を返し、他軸の健全状態を壊さない
- **検証 step**: (1) Coverage < 80% (2) Error Budget > 5% (3) TTFSP > 30min を個別に作る (4) verdict を比較する

### AC-FR-03: TDD 順序強制

- **対象 FR**: FR-TDD-01
- **デプロイ後検証内容**: S2 不在の S3 着手と S5 不在の S7 着手が block されることを確認する
- **受入基準**: 違反遷移は exit code 2、正順遷移は exit code 0 を返す
- **検証 step**: (1) sprint 状態を S1/S4 に置く (2) 禁止 step を要求する (3) 正順 step を要求して差分を確認する

### AC-FR-04: 9 mode 入口判定

- **対象 FR**: FR-9MODE-01
- **デプロイ後検証内容**: 代表 signal に対して mode 候補と route 根拠が返ることを確認する
- **受入基準**: 9 mode 全件で少なくとも 1 件の正答シナリオを持ち、signal 不足時は `manual_review_required` を返す
- **検証 step**: (1) Discovery/Reverse/Incident などの signal fixture を流す (2) 推奨 mode を確認する (3) signal 欠落 fixture で manual review を確認する

### AC-FR-05: gate 合成判定

- **対象 FR**: FR-GATE-01
- **デプロイ後検証内容**: static_subchecks 先行通過と AI review 必須条件の分離が機能することを確認する
- **受入基準**: static 合格かつ AI review 不要の gate は即時 decided、AI review 必須 gate は `static_checked` に止まる
- **検証 step**: (1) G3/G7 相当の fixture を作る (2) AI review 必須/不要の差を確認する (3) final verdict を比較する

### AC-FR-06: 影響範囲 query

- **対象 FR**: FR-IMPACT-01
- **デプロイ後検証内容**: PLAN 起点と artifact 起点の両方で 5 秒以内に trace が返ることを確認する
- **受入基準**: 10 回の試行で中央値 5 秒以下、timeout 時は部分結果と `timeout=true` を返す
- **検証 step**: (1) 小 / 中 / 大規模 trace を用意する (2) query 時間を計測する (3) timeout fixture で部分結果を確認する

### AC-FR-07: Forward 復帰 event

- **対象 FR**: FR-EVT-01
- **デプロイ後検証内容**: 9 mode closure 時に idempotent な Forward event が記録されることを確認する
- **受入基準**: 同一 `idempotency_key` の重複実行で row 数が増えず、target layer が保存される
- **検証 step**: (1) closure event を 2 回送る (2) row 数を確認する (3) target layer と closure_reason を照合する

### AC-FR-08: 4 artifact / pair freeze 監査

- **対象 FR**: FR-4ART-01
- **デプロイ後検証内容**: 片方向リンク、pair 欠落、4 artifact 欠落を warning / blocking に分類できることを確認する
- **受入基準**: 必須工程欠落は `blocking`、advisory 工程欠落は `advisory_only` または `warning`
- **検証 step**: (1) 4 artifact 完備 case (2) pair 欠落 case (3) advisory case を流す

### AC-FR-09: 資産 inventory / density 可視化

- **対象 FR**: FR-INV-01
- **デプロイ後検証内容**: 工程別 density と未割当資産が同時に返ることを確認する
- **受入基準**: `needs_classification` 資産が明示され、工程別件数が再計算される
- **検証 step**: (1) skill/CLI/docs/PLAN を登録する (2) 工程タグ欠落資産を混ぜる (3) density report を確認する

### AC-FR-10: layer context injection

- **対象 FR**: FR-CTX-01
- **デプロイ後検証内容**: process layer と role に応じて agent / skill / command / model route が束ねて返ることを確認する
- **受入基準**: `L3 + se` で mandatory_agents と recommended_commands が両方返り、欠落 skill は warning になる
- **検証 step**: (1) `helix context bundle --layer L3 --role se` を実行する (2) bundle 内容を確認する (3) 欠落 skill fixture で warning を確認する

### AC-FR-11: discrepancy routing

- **対象 FR**: FR-DRIFT-01
- **デプロイ後検証内容**: drift / trace 欠落 / OS 差異が適切な routing 先へ分類されることを確認する
- **受入基準**: 少なくとも `interrupt / recovery / reverse_normalization / manual_review` の 4 先が再現できる
- **検証 step**: (1) 各種 discrepancy fixture を作る (2) route 結果を比較する (3) environment mismatch を確認する

### AC-FR-12: PLAN dependency / generates trace

- **対象 FR**: FR-PLAN-01
- **デプロイ後検証内容**: `dependencies` と `generates` が graph 化され、broken link と deprecated path を返すことを確認する
- **受入基準**: 正常 graph は `validated`、broken link は `exit code 2`、deprecated path は warning を返す
- **検証 step**: (1) 正常 frontmatter を用意する (2) broken link を混ぜる (3) deprecated path を混ぜて比較する

### AC-FR-13: doctor 総合監査

- **対象 FR**: FR-DOCTOR-01
- **デプロイ後検証内容**: doctor が trace / inventory / migration / context の監査結果を 1 つの summary に束ねることを確認する
- **受入基準**: critical 1 件以上で exit code 2、critical 0 件なら summary JSON を返す
- **検証 step**: (1) 軽微 warning case (2) critical case を作る (3) exit code と summary を比較する

### AC-FR-14: schema migration / retrofit

- **対象 FR**: FR-MIGR-01
- **デプロイ後検証内容**: migration plan、manual approval requirement、compatibility warning が分離されることを確認する
- **受入基準**: destructive migration は自動実行されず `manual_approval_required`、互換期間中 router は warning 止まり
- **検証 step**: (1) 非破壊 migration (2) 破壊的 migration (3) 互換 router 残存 case を流して比較する

## §5 関連 doc

- **上流 L1**:
  - [helix-workflows-functional-requirements.md](../L1-requirements/helix-workflows-functional-requirements.md)
  - [helix-workflows-technical-requirements.md](../L1-requirements/helix-workflows-technical-requirements.md)
- **PLAN (本 doc を生成)**: [L3-helix-workflows-機能要件plan.md](../../plans/L3/L3-helix-workflows-機能要件plan.md)
- **姉妹 L3 doc**: [helix-workflows-business-requirements-detail.md](./helix-workflows-business-requirements-detail.md)
- **L12 ペア相手**: [helix-workflows-acceptance-test-design.md](../L12-test-design/helix-workflows-acceptance-test-design.md) §2
- **HELIX-workflows L3 正本**: [HELIX-workflows/helix-process/L3-requirements-definition.md](../../../HELIX-workflows/helix-process/L3-requirements-definition.md)
- **工程 doc**: [docs/v2/process/L03-requirements-definition-and-acceptance-test-design.md](../process/L03-requirements-definition-and-acceptance-test-design.md)
- **L0 概念**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md)

## §6 carry / 既知の不足

- L12 pair file 本体は編集禁止のため、AC-FR-* は本 doc の propose section に保持した。Opus PM が `docs/v2/L12-test-design/helix-workflows-acceptance-test-design.md` §2 へ移送する前提。
- `FR-DOCTOR-01` と `FR-MIGR-01` は L1 FR に直接 1:1 対応しない派生 FR であり、L4 基本設計で detector / migration / view の責務境界を更に分離する必要がある。
- `FR-9MODE-01` と `FR-EVT-01` の route 優先順位、`FR-DRIFT-01` の routing matrix は L4 で state machine として確定する必要がある。
- `FR-IMPACT-01` の 5 秒 SLA は acceptance target であり、index 設計・cache 方針は L4/L5 carry。
- `FR-PLAN-01` の 1 release 互換期限は `cli/helix-*` 側の deprecation policy と同期して L4 で凍結する必要がある。
