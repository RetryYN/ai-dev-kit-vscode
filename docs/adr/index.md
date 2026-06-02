# ADR Index

| # | Title | Status | Date |
|---|-------|--------|------|
| ADR-001-deliverable-matrix-as-source-of-truth | ADR-001: Deliverable Matrix as Source of Truth | Accepted | 2026-04-02 |
| ADR-002-builder-system-foundations | ADR-002: Builder System Foundations | Accepted | 2026-04-03 |
| ADR-003-learning-engine | ADR-003: Learning Engine Foundations | Accepted | 2026-04-03 |
| ADR-004-bash-python-hybrid | ADR-004: Bash-Python ハイブリッドアーキテクチャ | Accepted | 2026-04-05 |
| ADR-005-yaml-sqlite-dual-state | ADR-005: YAML-SQLite 二重状態管理 | Accepted | 2026-04-05 |
| ADR-006-template-copy-architecture | ADR-006: テンプレートコピーアーキテクチャ | Accepted | 2026-04-05 |
| ADR-007-three-mode-integration | ADR-007: 3モード統合（Forward / Reverse / Scrum） | Accepted | 2026-04-14 |
| ADR-008-builder-abstraction | ADR-008: ビルダーシステムによる成果物生成の抽象化 | Accepted | 2026-04-14 |
| ADR-009-hook-strategy | ADR-009: Hook 戦略（doc-map トリガー中心） | Accepted | 2026-04-14 |
| ADR-010-task-os | ADR-010: Task OS（2層構造: タスク→アクション） | Accepted | 2026-04-14 |
| ADR-011-test-duplication | ADR-011: helix-test / helix-test-debug の重複管理方針 | Accepted | 2026-04-15 |
| ADR-012-g1-gate-design | ADR-012: G1 ゲート運用方針 | Accepted | 2026-04-15 |
| ADR-013-r4-gate-design | ADR-013: R4 専用ゲートの要否 | Accepted | 2026-04-15 |
| ADR-014-roles-config-format | ADR-014: cli/roles/*.conf を正本とする決定 (conf vs yaml 二重管理の整理) | Accepted | 2026-05-08 |
| ADR-015-helix-v2-orchestration | ADR-015: HELIX v2 orchestration (PM 実装禁止 + PMO 新設 + ロール再配置) | Accepted | 2026-05-08 |
| ADR-016-concurrent-lock-primitive | ADR-016: concurrent lock primitive を standalone module として導入する | Accepted | 2026-05-10 |
| ADR-018-db-separation-and-event-sourcing | ADR-018: helix.db 6 分離 + Event Sourcing + projector 境界 | Accepted | 2026-05-18 |
| ADR-019-double-helix-naming-principle | ADR-019: HELIX = DNA 二重らせん命名原則と 3 軸トライアングル | Accepted | 2026-05-18 |
| ADR-020-cutover-rollback-gates | ADR-020: PLAN-084 migration gate 5 (cutover) + gate 6 (rollback) 採用 — local CLI tool 用簡略版 (Web 検索ベース再書き直し) | Accepted | 2026-05-18 |
| ADR-021-design-doc-web-search-guardrail-snapshot | ADR-021: 設計 doc 作成時 Web 検索ガードレール framework 採用 | Proposed | 2026-05-20 |
| ADR-022-todowrite-agent-slot-framework-snapshot | ADR-022: TodoWrite × agent slot framework 採用 | Proposed | 2026-05-20 |
| ADR-023-gate-fail-close-staged-adoption-snapshot | ADR-023: gate fail-close 段階導入 (advisory → fail-close 段階遷移) 採用 | Proposed | 2026-05-20 |
| ADR-024-continueonblock-active-guidance-loop-snapshot | ADR-024: Claude Code continueOnBlock + active guidance loop pattern 採用 | Proposed | 2026-05-20 |
| ADR-025-v5-framework-core-decision | ADR-025: V5 framework 本体採用判断 | Proposed | 2026-05-20 |
| ADR-026-posttooluse-plan-auto-register-decision | ADR-026: PostToolUse 自動登録 + helix.db v35 schema 採用判断 | Proposed | 2026-05-20 |
| ADR-027-plan-drift-detection-curator-decision | ADR-027: drift 検出 + Curator 自動化採用判断 | Proposed | 2026-05-20 |
| ADR-028-poc-scrum-reverse-matrix-decision | ADR-028: PoC = Scrum × Reverse 連携 matrix 採用判断 | Proposed | 2026-05-20 |
| ADR-029-github-actions-branch-pipeline-decision | ADR-029: GitHub Actions + ブランチタイプ別パイプライン採用判断 | Accepted | 2026-05-20 |
| ADR-030-abstraction-layer-escalation-decision | ADR-030: 抽象化層 3 層 (スキル/ワークフロー/ハーネス) + エスカレーション機構採用判断 | Proposed | 2026-05-20 |
| ADR-031-recovery-plan-kind-decision | ADR-031: リカバリープラン kind 正規化採用判断 | Proposed | 2026-05-20 |
| ADR-032-autonomous-runtime-framework-decision | ADR-032: 自動走行 framework 5-layer 採用判断 | Proposed | 2026-05-20 |
| ADR-033-design-doc-guard-session-id-fallback | ADR-033: PreToolUse hook の session_id 取得 fallback chain と transcript-based 検証緩和 | Proposed | 2026-05-22 |
| ADR-034-pytest-xdist-parallel-isolation | pytest-xdist 並列化 + per-worker HELIX_HOME isolation (default serial、--parallel で opt-in) | Accepted | 2026-05-23 |
| ADR-035-external-skills-integration-2026-05-23 | 外部素材 skill 4 件の HELIX 体系統合 (doc-system-architect / requirements-deriver / god-writing / gpt-image) | Accepted | 2026-05-23 |
| ADR-036-zizmor-adoption-decision | zizmor (GitHub Actions security audit) 採用 + 3 段統合 (CI enforcement + local advisory + knowledge reference) | Accepted with conditions | 2026-05-23 |
| ADR-040-helix-workspace-isolation | helix workspace isolation (git worktree-based per-task sandbox + filtered materialized init) | Accepted | 2026-05-23 |
| ADR-041-drift-type-7-categories-routing-decision | drift_type 7 種分類 + Reverse/Refactor/Retrofit 3 mode 分岐ルーティング契約 | Accepted | 2026-05-24 |
| ADR-042-recommended-command-machine-vs-display-decision | recommended_command 機械契約 vs 人間表示の役割分離 (suggest_command backward compat + 新 field 役割固定) | Accepted | 2026-05-24 |
| ADR-043-mode-enum-extension-retrofit-freeze-break-decision | Mode enum 拡張 (Retrofit 追加) — parent design freeze break + additive backward compat 凍結 | Accepted | 2026-05-24 |
| ADR-044-helix-workflows-v2-architecture-snapshot | HELIX-workflows V2 dogfooding 方式設計 snapshot | Proposed | 2026-05-27 |
| ADR-045-helix-workflows-f6-f10-governance-snapshot | HELIX-workflows V2 F6-F10 governance and survival operations snapshot | Proposed | 2026-05-27 |
