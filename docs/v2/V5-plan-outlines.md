# V5 PLAN framework 概要 (2026-05-20 確立・起票完遂)

## メタ情報

- session: 2026-05-19〜20
- 確立過程: V1 → V5 (TL 5 ラウンド + ユーザー 12+ ターン訂正)
- 起票完遂: commit da083c3 (PLAN-MM-001 + PLAN-091〜099 + ADR-021〜032、24 file、+8252 行)
- 関連 memory: `project_2026_05_20_v5_framework_completion.md` / `project_2026_05_20_v5_framework_evolution_recovery.md`
- 次 session 開始時に本 file を最初に Read すること

---

## V5 framework 18 要素 (2026-05-20 確立済み、turn 14-15 で 18 番追加)

| # | 要素 | 概要 |
|---|------|------|
| 1 | PLAN = self-contained workflow ルール doc | TodoWrite → PLAN 永続化置換。PLAN は毎回再読可能な単独完結 doc |
| 2 | V-model layer × drive matrix | L0-L11 (L3.5/L4.5 追加) × drive (be/fe/fullstack/scrum/reverse/db/agent/poc/troubleshoot) |
| 3 | 種別正規化 | design/impl/poc/reverse/troubleshoot/refactor/retrofit/research/add-design/add-impl/**recovery** の 11 種 |
| 4 | matrix 外 / kind 不在を helix plan CLI で fail-close | helix plan validate で machine 強制 |
| 5 | 生成物 trace | frontmatter `generates:` → V2 BR-V1 4 layer chain 直結 |
| 6 | 依存関係 graph | frontmatter `dependencies: requires/parent/blocks` |
| 7 | agent slot 割当 | frontmatter `agent_slots:` PLAN-088 連動 |
| 8 | PostToolUse hook で PLAN.md → helix.db 自動登録 | PLAN-092 ターゲット |
| 9 | PLAN ↔ 設計 doc drift 検出 | helix doctor axis-08 統合 |
| 10 | 進捗 trace | plan.db sprint_progress + handover メモ短縮化 |
| 11 | ADR snapshot 必須化 | L2 大局判断あれば、PLAN ⊃ ADR レイヤー併存 (ADR 先順序ではなく同一 PLAN trunk 内併設) |
| 12 | kind 別 workflow template embed | kind 別 Step 1-N を PLAN frontmatter に埋め込み |
| 13 | V-model TDD 駆動 | 設計⇔テスト設計対 pair freeze + 実装 TDD + QA 追加テスト |
| 14 | PoC = Scrum × Reverse 連携 matrix | Scrum 6 type × Reverse 5 type、PoC リバース合流 R0-R4 mapping |
| 15 | GitHub 運用ルール統合 | helix_github_workflow_rules.md ベース branch/PR/labels/CI |
| 16 | helix_improvement_plan_draft.md 6 Phase 統合 | 失敗集レイヤー + ブランチ別 DB + 抽象化層 3 層 + Curator |
| 17 | リカバリープラン kind 追加 (turn 13 確立) | session 断絶・議論脱線・認識ずれからの再開 workflow |
| 18 | **自動走行 framework 5-layer** (turn 14-15 確立) | claw0 + agent_farm + claude-brain + learn-claude-code 4 OSS シナジー。Layer 1: PostToolUse → task_queue auto-enqueue / Layer 2: statusLine context % 監視 4 段階 / Layer 3: PreCompact state 永続化 / Layer 4: SessionStart + UserPromptSubmit 履歴注入 / Layer 5: ScheduleWakeup heartbeat。解決問題: 14h idle 事故 + context 枯渇 + carry 放置の 3 課題同時解消 |

---

## 起票完遂状況 (commit da083c3、2026-05-20)

**全 9 PLAN + 12 ADR 起票完遂済み** (commit da083c3、24 file、+8252 行、TL 5 ラウンド全 passed)。

```
PLAN-MM-001 (親設計) ← 起票完遂
    ├── PLAN-091 ↔ ADR-025  (framework 本体) ← 起票完遂
    ├── PLAN-092 ↔ ADR-026  (PostToolUse 自動登録 + schema v35) ← 起票完遂
    ├── PLAN-093 ↔ ADR-027  (drift 検出 + dashboard + Curator) ← 起票完遂
    ├── PLAN-100 ↔ ADR-021〜024  (既存 retrofit + V2 全面見直し) ← 起票完遂
    ├── PLAN-095 ↔ ADR-028  (PoC = Scrum × Reverse matrix) ← 起票完遂
    ├── PLAN-096 ↔ ADR-029  (GitHub Actions + ブランチタイプ別パイプライン) ← 起票完遂
    ├── PLAN-097 ↔ ADR-030  (抽象化層 + エスカレーション) ← 起票完遂
    ├── PLAN-098 ↔ ADR-031  (リカバリープラン kind 正規化) ← 起票完遂
    └── PLAN-099 ↔ ADR-032  (自動走行 framework 5-layer) ← 起票完遂
```

**ADR ⊃ PLAN レイヤー併存 (訂正済み)**: 「ADR 先・PLAN 後」の順序関係ではなく、PLAN は 1 トピックの implementation tree (L1〜L4 全範囲内包) であり、ADR は PLAN tree 内 L2 大局判断の snapshot として**同一 PLAN trunk 内で併存**する (L2-MASTER §0 line 36 正規 pattern「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」が範例)。

---

## PLAN-MM-001: 親設計プラン (V5 全体構想)

- **kind**: design (cross-layer)
- **layer**: L2 (全体設計フェーズ)
- **drive**: be (CLI 実装中心)
- **agent_slots**: opus + tl-advisor (大局判断のみ、実装は子 PLAN へ委譲)
- **generates**: PLAN-091〜099 の起票計画、段階導入 5 Phase 定義
- **内容**: PLAN-091〜099 の起票順序・依存関係設計 + 段階導入 5 Phase 計画 (P1: warning 導入 → P2: matrix 検証 → P3: enforce → P4: retrofit → P5: Curator 自動化)。V5 framework の全体整合を守るための親設計 doc。TL 5 ラウンド全 passed 確認後、子 PLAN 起票に進んだ。
- **DoD**: PLAN-091〜099 全起票完了 (commit da083c3 達成済み) + V2 全面見直し合流 + 既存 PLAN-001〜090 retrofit 完遂

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

## PLAN-100 ↔ ADR-021〜024: 既存 retrofit + V2 全面見直し

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
| P4 | retrofit + V2 全面見直し | PLAN-100 (並列 N Codex) | 2-3 session |
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

**前提**: commit da083c3 で PLAN-MM-001 + PLAN-091〜099 + ADR-021〜032 全 22 file 起票完遂済み。次 session は各 PLAN の Phase 1 実装着手が主目的。

```
1. 本 file Read (docs/v2/V5-plan-outlines.md)
2. memory/project_2026_05_20_v5_framework_completion.md Read (commit da083c3 完遂記録)
3. memory/project_2026_05_20_v5_framework_evolution_recovery.md Read (V1→V5 議論履歴)
4. memory/feedback_recovery_plan_kind_missing.md Read (存在する場合)
5. memory/feedback_adr_before_plan_violation.md Read (存在する場合)
6. memory/feedback_dont_stop_with_carry_remaining.md Read (存在する場合)
7. helix handover status --json で現在の handover 状態確認
8. git log --oneline -15 で commit 状況確認 (da083c3 が最新であることを確認)
9. V2 企画書見直し (CONCEPT.md / L1-REQUIREMENTS / L2-MASTER §0/§12) ← Layer A 正本確認
10. Layer A 実装着手: V5 要素 1-7, 11-17 の企画書への反映
    - ADR は PLAN tree 内 L2 大局判断 snapshot として PLAN trunk 内に併存 (順序ではなく併存)
    - L2-MASTER §0 line 36 範例「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」を参照
11. Layer B/C は Layer A 確定後に順次着手 (Layer C の PoC C 案のみ並行可)
```

---

## 起票前に確認すべき既存 PLAN 番号

現在の最新 PLAN 番号を `ls docs/plans/ | sort -V | tail -5` で確認し、PLAN-091 が空き番号かを検証すること。本 memo 作成時点 (2026-05-20) の最終 PLAN は PLAN-090 の想定。

## PLAN-099 ↔ ADR-032: 自動走行 framework 5-layer (起票完遂)

- **kind**: impl (runtime substrate)
- **layer**: cross
- **drive**: agent
- **agent_slots**: codex se + pmo-sonnet + tl-advisor
- **generates**:
  - `.claude/hooks/posttooluse-task-enqueue.sh` (Layer 1)
  - `.claude/hooks/status-line-context-monitor.sh` (Layer 2)
  - `.claude/hooks/precompact-state-capture.sh` (Layer 3)
  - `.claude/hooks/session-start-history-inject.sh` (Layer 4)
  - `cli/lib/heartbeat_scheduler.py` (Layer 5)
  - `docs/adr/ADR-032.md`
- **5-layer 構成**:
  - **Layer 1**: PostToolUse(Write|Edit + PLAN.md) → helix.db.task_queue auto-enqueue (plan guard 通過後のみ)
  - **Layer 2**: statusLine hook で context % 先回り監視 4 段階 (>50% 正常 / 30-50% 警告 / ≤30% 圧縮推奨 / ≤20% 緊急)、debounce + hysteresis 必須
  - **Layer 3**: PreCompact hook (v1.0.48+) で auto-compact 前 state 永続化、「重要 state 永続化失敗 AND 未保存 L2/L3/ADR 判断あり AND 一回だけ」条件限定で decision:block、通常は backup + warning
  - **Layer 4**: SessionStart(cleared|compacted) + UserPromptSubmit で関連 PLAN/handover/memory feedback の短い bundle を自動注入 (claude-brain pattern の HELIX 独自再実装、会話 SQLite 全量キャプチャは secret/PII リスクのため transcript_path 参照 + 要約 state + 明示的 retention のみ)
  - **Layer 5**: ScheduleWakeup adaptive heartbeat (carry>0 AND bg task なし AND budget healthy の時のみ、通常 15min / 低予算 30min / critical 5min / active task 中無効)、claw0 cold-start pattern
- **解決問題**: 14h idle 事故 + context 枯渇による中断 + carry 残し放置の 3 課題同時解消
- **依存**: PLAN-091 (frontmatter dependencies 語彙定義) が先。Layer 4/5 PoC は既存 handover/SessionStart/scheduler 上で暫定 schema なしで並行着手可能
- **ADR-032 snapshot 内容**: 自動走行 framework 5-layer の採用判断、claude-brain / claw0 / agent_farm / learn-claude-code 4 OSS のシナジー設計、Layer A/B 確定後の接続方針
- **TL v5 round 5 修正条件 (5 重要項目)**:
  1. PLAN-091 (規約本体) と PLAN-099 (runtime substrate) を独立子 PLAN として並行起票、feature flag / warn-only / fail-close 段階導入
  2. PoC 戦略: C 案 = Layer 4+5 先行 PoC (0.5-1 session)、Layer 1-3 は schema・hook 正本確定後接続
  3. PreCompact decision:block は 3 条件 AND + 一回だけ に限定
  4. statusLine + Stop 役割分担: Stop は軽量化、statusLine に debounce + hysteresis 必須
  5. claude-brain pattern は HELIX 独自再実装、secret/PII リスク対応必須
- **P0 指摘 (絶対遵守)**: 承認なし task pop は HELIX discipline 破壊 → queue worker は必ず plan guard を通すこと

---

## V5 framework 3 層構造 (turn 19、ユーザー指摘で確立、Layer A→B→C 着手順序)

V モデル強化構想は 3 層: **工程管理ハーネス + helix.db 型ハーネス + 連携自動化ハーネス**。DB schema や hook 設計の前に、工程と管理 doc のルール整備 + どう動かすかが決まらないと start できない。V5 18 要素を 3 層に分解し、依存順序を遵守する。

```
[Layer A] 工程・ドキュメント運用ルール整備 ← V2 企画書反映、Layer B/C の前提
  V5 要素 1-7 (PLAN self-contained / matrix / 種別 / fail-close / generates / dependencies / agent_slots)
  V5 要素 11-17 (ADR snapshot / template embed / V-model TDD / PoC=Scrum×Reverse / GitHub / helix_improvement / recovery)
       ↓
[Layer B] helix.db 型ハーネス ← Layer A の実体化
  V5 要素 8 (DB 受け側) / 9 (drift) / 10 (進捗 trace)
  単一実行正本決定 (task_queue / TodoWrite / helix job / handover 競合解消、TL v5 P1)
       ↓
[Layer C] 連携自動化ハーネス ← Layer A/B を hook で動かす
  V5 要素 8 (hook 本体) / 18 (自動走行 framework 5-layer)
  PoC C 案 (Layer 4+5) のみ並行可、本実装 (Layer 1-3) は A/B 確定後
```

**PLAN → Layer マッピング**:
- Layer A: PLAN-091 (matrix + 種別 + template embed) / PLAN-100 (retrofit + V2 見直し) / PLAN-095 (PoC × Reverse) / PLAN-096 (GitHub) / PLAN-097 (抽象化層) / PLAN-098 (recovery kind)
- Layer B: PLAN-092 (DB 受け側 + schema v35) / PLAN-093 (drift + dashboard + Curator)
- Layer C: PLAN-099 (自動走行 5-layer、hook 本体)

**次 session 正順 (Layer A→B→C 遵守)**:
0. V2 企画書見直し (`docs/v2/CONCEPT.md` / L1-REQUIREMENTS / L2-MASTER §0/§12) ← Layer A 正本確認
1. Layer A 確定: V5 要素 1-7, 11-17 を企画書に反映 + ADR-021〜024 後追い snapshot 起票
2. Layer B 確定: 単一実行正本決定 + helix.db schema 設計
3. Layer C 並行: PoC C 案 (Layer 4+5) を Layer A/B 確定待たず先行
4. PLAN 起票は 2026-05-20 commit da083c3 で完遂済み。次は各 PLAN の Phase 1 実装着手

---

## TL 5 ラウンド全 passed 履歴 (V5 確定、turn 17 で round 5 完了)

- v1 (matrix + 種別): passed (bs9wuvqcs)
- v2 (+ 依存 + agent slot + 自動登録): passed (PLAN-091〜093 分割推奨、bppaf3fwe)
- v3 (+ template embed): passed (bkac94gnw)
- v4 (+ V-model TDD + PoC リバース合流): passed (baq742e62)
- **v5 (+ 自動走行 framework 18 番要素): passed_with_minor_changes** (bdnmyhznq、修正条件付き起票 OK → commit da083c3 で完遂)

---

## 補足: V5 確立における主な訂正履歴

1. **V1 初期案**: TodoWrite で管理 → V5 で PLAN 永続化置換に確定
2. **V2 訂正**: layer を L1-L11 のみ → L0 (pre-work) / L3.5 / L4.5 を追加
3. **V3 訂正**: kind を 5 種 → 11 種 (recovery 追加含む) に拡張
4. **V4 訂正**: ADR と PLAN を一体化提案 → 別文書 (ADR 先・PLAN 後) に分離
5. **V5 確定**: PoC × Reverse matrix + GitHub 運用 + helix_improvement 統合 + recovery kind 追加で 17 要素確定
6. **V5 拡張 (turn 14-15)**: 自動走行 framework 5-layer (PLAN-099) を 18 番目の要素として追加、TL round 5 passed_with_minor_changes で確定

訂正理由の詳細は TL 各ラウンドの output と memory feedback に保存済み (存在する場合)。
