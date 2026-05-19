# V5 PLAN 起票案概要メモ (2026-05-20 永続化)

## メタ情報

- session: 2026-05-19〜20
- 確立過程: V1 → V5 (TL 4 ラウンド + ユーザー 12+ ターン訂正)
- 関連 memory: `project_2026_05_20_v5_framework_evolution_recovery.md`（存在する場合）
- 次 session 開始時に本 file を最初に Read すること

---

## V5 framework 17 要素 (確立済み)

| # | 要素 | 概要 |
|---|------|------|
| 1 | PLAN = self-contained workflow ルール doc | TodoWrite → PLAN 永続化置換。PLAN は毎回再読可能な単独完結 doc |
| 2 | V-model layer × drive matrix | L0-L11 (L3.5/L4.5 追加) × drive (be/fe/fullstack/scrum/reverse/db/agent/poc/troubleshoot) |
| 3 | 種別正規化 | design/impl/poc/reverse/troubleshoot/refactor/retrofit/research/add-design/add-impl/recovery の 11 種 |
| 4 | matrix 外 / kind 不在を helix plan CLI で fail-close | helix plan validate で machine 強制 |
| 5 | 生成物 trace | frontmatter `generates:` → V2 BR-V1 4 layer chain 直結 |
| 6 | 依存関係 graph | frontmatter `dependencies: requires/parent/blocks` |
| 7 | agent slot 割当 | frontmatter `agent_slots:` PLAN-088 連動 |
| 8 | PostToolUse hook で PLAN.md → helix.db 自動登録 | PLAN-092 ターゲット |
| 9 | PLAN ↔ 設計 doc drift 検出 | helix doctor axis-08 統合 |
| 10 | 進捗 trace | plan.db sprint_progress + handover メモ短縮化 |
| 11 | ADR snapshot 必須化 | L2 大局判断あれば ADR ペア必須 |
| 12 | workflow template embed | kind 別 Step 1-N を PLAN frontmatter に埋め込み |
| 13 | V-model TDD 駆動 | 設計⇔テスト設計 pair freeze + 実装 TDD 駆動 + QA 追加テスト |
| 14 | PoC = Scrum × Reverse 連携 matrix | Scrum 6 type × Reverse 5 type、PoC リバース合流 R0-R4 mapping |
| 15 | GitHub 運用ルール統合 | helix_github_workflow_rules.md ベース branch/PR/labels/CI |
| 16 | helix_improvement_plan_draft.md 6 Phase 統合 | 失敗集レイヤー + ブランチ別 DB + 抽象化層 3 層 + Curator |
| 17 | リカバリープラン kind 追加 | session 断絶・議論脱線・認識ずれからの再開 workflow |

---

## 起票順序 (parent → blocks chain)

```
PLAN-MM-001 (親設計)
    ├── PLAN-091 ↔ ADR-025  (framework 本体)
    ├── PLAN-092 ↔ ADR-026  (PostToolUse 自動登録 + schema v35)
    ├── PLAN-093 ↔ ADR-027  (drift 検出 + dashboard + Curator)
    ├── PLAN-094 ↔ ADR-021〜024  (既存 retrofit + V2 全面見直し)
    ├── PLAN-095 ↔ ADR-028  (PoC = Scrum × Reverse matrix)
    ├── PLAN-096 ↔ ADR-029  (GitHub Actions + ブランチ別パイプライン)
    ├── PLAN-097 ↔ ADR-030  (抽象化層 + エスカレーション)
    └── PLAN-098 ↔ ADR-031  (リカバリープラン kind 正規化)
```

ADR は対応 PLAN と同時起票。ADR が先（大局判断の明文化）、PLAN が後（工程設計）の順。

---

## PLAN-MM-001: 親設計プラン (V5 全体構想)

- **kind**: design (cross-layer)
- **layer**: L2 (全体設計フェーズ)
- **drive**: be (CLI 実装中心)
- **agent_slots**: opus + tl-advisor (大局判断のみ、実装は子 PLAN へ委譲)
- **generates**: PLAN-091〜098 の起票計画、段階導入 5 Phase 定義
- **内容**: PLAN-091〜098 の起票順序・依存関係設計 + 段階導入 5 Phase 計画 (P1: warning 導入 → P2: matrix 検証 → P3: enforce → P4: retrofit → P5: Curator 自動化)。V5 framework の全体整合を守るための親設計 doc。TL 5 ラウンド目 adversarial check を受けてから子 PLAN 起票に進む。
- **DoD**: PLAN-091〜098 全起票完了 + V2 全面見直し合流 + 既存 PLAN-001〜090 retrofit 完遂

---

## PLAN-091 ↔ ADR-025: framework 本体

- **kind**: impl (core framework)
- **layer**: cross (L0-L11 全層)
- **drive**: be
- **agent_slots**: codex se × 2 + codex docs + pmo-sonnet + tl-advisor
- **generates**:
  - `helix.db` v35 (一部、詳細は PLAN-092)
  - `cli/helix-plan` 拡張 (--layer/--drive/--kind/--parent/--validates-matrix フラグ)
  - `cli/templates/plan/{kind}/template.md` (11 種 × template file)
  - `helix doctor` check_plan_matrix / check_plan_kind / check_template_embed
  - `docs/adr/ADR-025.md` (snapshot)
- **Phase 1-4**:
  - P1: kind/layer/drive 必須フィールド追加 + warning 表示
  - P2: matrix 整合性 lint (helix plan validate)
  - P3: fail-close 強制 (helix plan create で matrix 外を reject)
  - P4: 既存 PLAN-001〜090 の frontmatter 一括 retrofit (pmo-sonnet 並列)
- **ADR-025 snapshot 内容**: V-model layer × drive matrix を PLAN 正規体系として採用する大局判断、既存 SKILL_MAP との整合、L3.5/L4.5 追加の根拠
- **概要**: V5 の中核。PLAN doc の種別・layer・drive を matrix で正規化し、CLI で fail-close 強制する。12 種の workflow template を kind 別に埋め込み、設計⇔テスト設計 pair freeze (V-model TDD) を PLAN frontmatter で宣言可能にする。既存 107 スキルの SKILL_MAP とは補完関係（スキルは知識、PLAN は工程ルール）。

---

## PLAN-092 ↔ ADR-026: PostToolUse 自動登録 + helix.db v35 schema

- **kind**: impl (hook + schema)
- **layer**: cross
- **drive**: be
- **agent_slots**: codex se + pmo-sonnet
- **generates**:
  - `.claude/hooks/posttooluse-plan-auto-register.sh`
  - `cli/lib/migrations/v35_plan_registry.py`
  - `cli/lib/plan_parser.py` (frontmatter → DB 変換)
  - `tests/test_plan_parser.py`
  - `docs/adr/ADR-026.md`
- **helix.db v35 新規テーブル**:
  - `plan_registry` (id/kind/layer/drive/status/frontmatter JSON)
  - `plan_dependencies` (plan_id/requires/parent/blocks)
  - `plan_agent_slots` (plan_id/role/model)
  - `plan_references` (plan_id/doc_path/section)
  - `plan_generates` (plan_id/artifact_path/artifact_type)
  - `sprint_progress` (plan_id/sprint_id/status/timestamp)
  - `failure_log` (session_id/failure_type/context/recovery_plan_id)
  - `poc_validation_log` (hypothesis_id/scrum_type/reverse_type/result)
  - `refactor_degrade_pattern` (pattern_id/trigger/escalation_level)
  - `hotfix_incident_log` (incident_id/severity/root_cause/recovery_ref)
- **ADR-026 snapshot 内容**: PostToolUse hook による PLAN.md 自動解析・DB 登録の採用判断。PLAN-087/089/090 PostToolUse 系列の延長として位置づけ。
- **概要**: PLAN.md を Write/Edit するたびに PostToolUse hook が frontmatter を parse して helix.db v35 へ自動登録する。agent_slot・dependency・generates の triple を DB に保持し、PLAN-093 の drift 検出・dashboard 表示と PLAN-095 の PoC matrix 管理に供給する基盤 schema。

---

## PLAN-093 ↔ ADR-027: drift 検出 + 進捗 trace dashboard + Curator

- **kind**: impl (monitoring + automation)
- **layer**: cross
- **drive**: be
- **agent_slots**: codex se + pmo-sonnet
- **generates**:
  - `cli/helix-dashboard` 拡張 (helix dashboard plan-progress)
  - `cli/lib/plan_drift_checker.py`
  - `cli/lib/curator/curator_engine.py`
  - `cli/lib/curator/escalation_matrix.py`
  - `tests/test_plan_drift_checker.py`
  - `docs/adr/ADR-027.md`
- **helix doctor 追加 check**:
  - `check_plan_drift`: PLAN frontmatter の generates ↔ 実ファイル存在確認
  - `check_plan_freshness`: status=active PLAN の最終更新 N 日超過警告
  - `check_recovery_plan_freshness`: recovery kind PLAN の stale 検出
- **Curator 機構** (helix_improvement Phase 6 統合):
  - 発火回数 / 再失敗回数ベースでルール昇格判定
  - 未使用期間 / 違反検出ゼロで降格
  - レビュー注入機構 (人間 / エージェント / council 切替)
- **ADR-027 snapshot 内容**: drift 検出と Curator 自動化の採用判断、既存 helix doctor との統合方針。
- **概要**: PLAN-092 の DB を読んで「設計 doc が存在するのに実装ファイルが生成されていない」「PLAN が active のまま N 日更新なし」等の drift を自動検出。dashboard でスプリント進捗を可視化し、Curator が failure_log + refactor_degrade_pattern を分析してルールの昇格・降格を自動判定する。handover メモの短縮化はここで実現する（progress は DB から引く）。

---

## PLAN-094 ↔ ADR-021〜024: 既存 retrofit + V2 全面見直し

- **kind**: retrofit (cross-version)
- **layer**: cross
- **drive**: be
- **agent_slots**: codex docs × 4 (並列 retrofit) + pmo-sonnet (整合確認)
- **generates**:
  - `docs/adr/ADR-021.md` (PLAN-087 Web 検索ガードレール snapshot)
  - `docs/adr/ADR-022.md` (PLAN-088 agent slot framework snapshot)
  - `docs/adr/ADR-023.md` (PLAN-089 PostToolUse Write hook snapshot)
  - `docs/adr/ADR-024.md` (PLAN-090 active guidance loop snapshot)
  - `docs/v2/V2-mapping.md` (V5 要素 ↔ V2 doc 対応表)
  - `docs/plans/PLAN-001〜090 frontmatter` 拡張 (kind/layer/drive/generates 追加)
- **ADR-021〜024 の位置づけ**: PLAN-087〜090 は本 session 実装済みだが ADR snapshot が未起票。retrofit として後追い起票し、大局判断の明文化を補完する。
- **概要**: PLAN-001〜090 を V5 matrix へ機械マッピングし、frontmatter を一括拡張する retrofit。PLAN-087〜090 の後追い ADR 起票も含む。V2 の CONCEPT/L1-REQUIREMENTS/L2-MASTER を V5 framework の観点で改修し、既存資産と新 framework の整合を保証する。並列 retrofit は pmo-sonnet で整合確認後、codex docs 4 並列投入。

---

## PLAN-095 ↔ ADR-028: PoC = Scrum × Reverse 連携 matrix

- **kind**: impl (framework extension)
- **layer**: cross (S0-S4 + R0-R4)
- **drive**: scrum + reverse
- **agent_slots**: codex se + pmo-sonnet + tl-advisor
- **generates**:
  - `cli/helix-scrum` 拡張 (--reverse-merge / --scrum-type フラグ)
  - `cli/helix-reverse` 統合 CLI 拡張 (--from-scrum / --scrum-hypothesis フラグ)
  - `cli/lib/scrum_reverse_matrix.py`
  - `cli/lib/poc_validation_log.py`
  - `tests/test_scrum_reverse_matrix.py`
  - `docs/adr/ADR-028.md`
- **Scrum 6 type × Reverse 5 type matrix**:
  - Scrum type: hypothesis-test / tech-spike / design-spike / perf-spike / security-spike / ux-spike
  - Reverse type: code / design / upgrade / normalization / fullback
  - PoC リバース合流 R0-R4 mapping: Scrum S4 decide --confirmed → どの Reverse type で R0-R4 を通すかを matrix で決定
- **ADR-028 snapshot 内容**: Scrum と Reverse を独立モードから interlocked chain に拡張する採用判断。既存 helix scrum / helix reverse CLI との整合。
- **概要**: PoC (Scrum) で仮説検証した成果を Reverse フローで設計文書化し、Forward HELIX 本実装へ橋渡しする連携 matrix。6×5 の組み合わせで「どの Scrum type の PoC は、どの Reverse type で文書化すべきか」を機械決定可能にする。helix scrum decide --confirmed --reverse-merge で S4→R0 の自動 routing を実現。

---

## PLAN-096 ↔ ADR-029: GitHub Actions + ブランチタイプ別パイプライン

- **kind**: impl (CI/CD + governance)
- **layer**: cross (L4〜L7)
- **drive**: be
- **agent_slots**: codex se + codex docs + tl-advisor (CODEOWNERS の判断)
- **generates**:
  - `.github/workflows/feature.yml`
  - `.github/workflows/poc.yml`
  - `.github/workflows/refactor.yml`
  - `.github/workflows/hotfix.yml`
  - `.github/pull_request_template.md`
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
  - `.github/CODEOWNERS`
  - `docs/adr/ADR-029.md`
- **helix_github_workflow_rules.md ベース**:
  - branch 命名: `feature/PLAN-NNN-description`, `poc/H-NNN-description`, `refactor/scope`, `hotfix/incident-id`
  - Conventional Commits 強制 (commitlint)
  - PR template に PLAN-id / kind / ADR ref 必須フィールド
  - ブランチタイプ ↔ HELIX kind マッピング (feature→impl/design、poc→poc、refactor→refactor/retrofit、hotfix→recovery)
- **helix_improvement Phase 1-3 統合**: branch DB 分離 + パイプライン並列化 + status check 自動化
- **ADR-029 snapshot 内容**: GitHub Actions を HELIX 工程管理と統合する採用判断、ブランチ戦略と kind の対応規約。
- **概要**: helix_github_workflow_rules.md の規約を .github/ に実装し、ブランチタイプ・HELIX kind・CI パイプラインを三点セットで紐づける。feature ブランチは L4 sprint lint + test、poc は Scrum verify スクリプト実行、refactor は degrade detector、hotfix は incident log 自動生成を CI で実行。

---

## PLAN-097 ↔ ADR-030: 抽象化層 (スキル/ワークフロー/ハーネス) + エスカレーション

- **kind**: impl (architecture)
- **layer**: L2 (全体設計)
- **drive**: agent
- **agent_slots**: codex se + codex docs + pmo-sonnet
- **generates**:
  - `workflows/` ディレクトリ (ワークフロー層 YAML 定義)
  - `harness/` ディレクトリ (ハーネス層 定義)
  - `cli/lib/escalation_engine.py`
  - `cli/lib/demotion_checker.py`
  - `tests/test_escalation_engine.py`
  - `docs/adr/ADR-030.md`
- **抽象化層 3 層** (helix_improvement Phase 4 統合):
  - 層 1 スキル層: 既存 SKILL_MAP (107 スキル) 維持
  - 層 2 ワークフロー層: スキルを組み合わせた再利用可能なフロー定義 (workflows/*.yaml)
  - 層 3 ハーネス層: ワークフローを自動実行するオーケストレーター (harness/*.yaml)
- **エスカレーション機構**:
  - 発火回数 N 回以上 → 上位レビュー注入 (エージェント → council → 人間)
  - 再失敗回数 M 回以上 → 昇格判定 (ルール強化 / kind 変更 推奨)
  - 降格基準: 未使用期間 T 日超過 / 違反検出ゼロ継続 → warning → 非アクティブ化
- **ADR-030 snapshot 内容**: SKILL_MAP に workflows/harness の 2 層を追加し、エスカレーション機構を組み込む採用判断。
- **概要**: 既存 SKILL_MAP (スキル層) の上に、スキルを組み合わせるワークフロー層と自動実行するハーネス層を追加。Curator (PLAN-093) と連携してルールの発火・降格を自動管理し、人間レビューが必要なエスカレーションを判定する。レビュー注入 3 段階 (agent / council / human) により blast radius を制御。

---

## PLAN-098 ↔ ADR-031: リカバリープラン kind 正規化

- **kind**: design + impl (新 kind 追加)
- **layer**: cross
- **drive**: troubleshoot
- **agent_slots**: codex se + pmo-sonnet
- **generates**:
  - `cli/templates/plan/recovery/template.md`
  - `cli/lib/recovery_plan_check.py`
  - `helix doctor` check_recovery_plan_freshness 追加
  - `tests/test_recovery_plan_check.py`
  - `docs/adr/ADR-031.md`
- **recovery template 必須セクション**:
  1. 事故記録 (何が起きたか: session 断絶 / 議論脱線 / 認識ずれ)
  2. 議論順序 timeline (いつ何を議論したか)
  3. 認識訂正履歴 (V1→V2→...→Vn の遷移と各訂正理由)
  4. 中間結論 list (確定済み / 未確定 / 破棄済みを 3 列で管理)
  5. context 再構築チェックリスト (次 session 開始前に確認すべき 5 項目)
  6. 再開ポイント (どこから再開するか、前提条件)
  7. 再発防止策 (session 終了前チェックリスト 4 項目 fail-close)
- **session 終了前チェックリスト 4 項目** (fail-close):
  1. 中間結論が docs に永続化されているか
  2. carry 残件が PLAN or handover に明記されているか
  3. 認識訂正があった場合 memory feedback が更新されているか
  4. recovery kind PLAN が必要な場合 draft 起票済みか
- **ADR-031 snapshot 内容**: recovery kind の追加と session 断絶リカバリー機構の標準化採用判断。本 session で「中間結論が消えた」「carry 残件が不明確」という問題が発覚した直接的な教訓から。
- **概要**: session 断絶・議論脱線・認識ずれからの再開を標準化する recovery kind を追加。helix doctor で stale recovery plan を検出し、session 終了前チェックリスト 4 項目を fail-close で強制することで「気づいたら次 session で何もわからない」状態を防ぐ。本 session で確立した feedback_recovery_plan_kind_missing の直接実装。

---

## 段階導入 5 Phase

| Phase | 内容 | 対象 PLAN | 目安期間 |
|-------|------|-----------|----------|
| P1 | warning 導入 (matrix 外でも続行、警告のみ) | PLAN-091 partial | 1 session |
| P2 | matrix 検証 (helix plan validate + drift 検出) | PLAN-091 + 092 + 093 | 2-3 session |
| P3 | fail-close 強制 (helix plan create で matrix 外 reject) | PLAN-091 enforce | 1 session |
| P4 | retrofit + V2 全面見直し | PLAN-094 (並列 N Codex) | 2-3 session |
| P5 | Curator 自動化 + GitHub/抽象化層/PoC matrix 統合 | PLAN-095〜098 | 3-5 session |

---

## 既存 HELIX 資産との統合 mapping

| V5 新要素 | 既存資産 | 接続点 |
|-----------|---------|--------|
| V-model TDD pair | V2 L1-REQUIREMENTS §3.6 + PLAN-075 (V-model 4 artifact) | L3.5 機能設計 ↔ 単体テスト設計 pair freeze |
| L3.5 機能設計 | V2 G3.functional_freeze | helix plan --layer L3.5 で明示 |
| L4 TDD 駆動 | agent-skills/test-driven-development | PLAN-091 template に embed |
| 複数観点 QA 追加テスト | qa-test subagent + workflow/quality-lv5 | agent_slots に qa-test を明示 |
| PoC × Reverse matrix | helix scrum + helix reverse (既存 CLI) | PLAN-095 で CLI 統合拡張 |
| PostToolUse 自動登録 hook | PLAN-087/089/090 PostToolUse 系列 (本 session 実装済) | PLAN-092 で PLAN.md 特化拡張 |
| 4 layer chain (generates) | V2 BR-V1 trace | frontmatter generates → artifact_path → DB |
| GitHub 運用 | helix_github_workflow_rules.md (本 session 確認) | PLAN-096 で .github/ 実装 |
| 失敗集レイヤー | helix_improvement Phase 2 (新規) | PLAN-092 failure_log table + PLAN-093 Curator |
| 抽象化層 3 層 | 既存 SKILL_MAP + helix_improvement Phase 4 | PLAN-097 workflows/harness 追加 |
| リカバリープラン | feedback_recovery_plan_kind_missing (本 session 確立) | PLAN-098 recovery kind + template |
| ADR snapshot 必須化 | 既存 docs/adr/ (ADR-001〜024) | 各 PLAN と同時起票 (PLAN-091〜098 ↔ ADR-025〜031) |
| Curator | helix_improvement Phase 6 | PLAN-093 curator_engine.py |

---

## 次 session 開始時の手順 (recovery 用)

```
1. 本 file Read (docs/v2/V5-plan-outlines.md)
2. memory/project_2026_05_20_v5_framework_evolution_recovery.md Read (存在する場合)
3. memory/feedback_recovery_plan_kind_missing.md Read (存在する場合)
4. memory/feedback_adr_before_plan_violation.md Read (存在する場合)
5. memory/feedback_dont_stop_with_carry_remaining.md Read (存在する場合)
6. helix handover status --json で現在の handover 状態確認
7. git log --oneline -15 で本 session の commit 状況確認
8. V5 TL 5 ラウンド目 adversarial check 投入
   - 確認観点: Scrum × Reverse matrix の妥当性
   - 確認観点: GitHub 運用との整合
   - 確認観点: helix_improvement 6 Phase の統合順序
   - 確認観点: recovery kind の必要十分性
9. TL passed 後、PLAN-MM-001 → PLAN-091 起票着手
10. ADR は対応 PLAN と同時起票 (ADR が先、PLAN が後)
```

---

## 起票前に確認すべき既存 PLAN 番号

現在の最新 PLAN 番号を `ls docs/plans/ | sort -V | tail -5` で確認し、PLAN-091 が空き番号かを検証すること。本 memo 作成時点 (2026-05-20) の最終 PLAN は PLAN-090 の想定。

## 補足: V5 確立における主な訂正履歴

1. **V1 初期案**: TodoWrite で管理 → V5 で PLAN 永続化置換に確定
2. **V2 訂正**: layer を L1-L11 のみ → L0 (pre-work) / L3.5 / L4.5 を追加
3. **V3 訂正**: kind を 5 種 → 11 種 (recovery 追加含む) に拡張
4. **V4 訂正**: ADR と PLAN を一体化提案 → 別文書 (ADR 先・PLAN 後) に分離
5. **V5 確定**: PoC × Reverse matrix + GitHub 運用 + helix_improvement 統合 + recovery kind 追加で 17 要素確定

訂正理由の詳細は TL 各ラウンドの output と memory feedback に保存済み (存在する場合)。
