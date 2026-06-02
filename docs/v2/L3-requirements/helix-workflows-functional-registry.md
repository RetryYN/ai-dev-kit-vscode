---
plan_id: "-"
status: draft
process_layer: L3
artifact_type: functional_registry
related_l1:
  - docs/v2/L1-requirements/helix-workflows-functional-requirements.md
  - docs/v2/L1-requirements/helix-workflows-technical-requirements.md
related_l3_fr:
  - FR-FNREG-01
  - FR-INV-01
generates: []
pairs_test_design: []
implementation_status: in_progress
created: 2026-05-29
audit_history:
  - 2026-05-29: pmo-sonnet (Wave C draft) — Wave A/B inventory 統合
  - 2026-05-29: pmo-sonnet (Wave fix-F) — tl-advisor R1 P1 反映 (CLI 94→80 / skill 132→130 / workflow 50→49 / templates ~108→114 / 合計 ~559→548 同期)
---

# HELIX-workflows 機能一覧 (L3 SSoT)

> **本 doc の位置づけ**: L3 機能要件 doc (FR-FNREG-01 / FR-INV-01) の実体化 SSoT。  
> Wave A (CLI/hook/agent/template ~374 資産) と Wave B (skill/workflow doc ~174 資産) を統合し、計 548 資産の機能一覧を提供する。  
> L1/L3 FR 13/18 件への双方向 trace で漏れを機械検出する。

---

## §1. 目的

1. **FR-FNREG-01** (機能一覧 SSoT) の実体化: HELIX-workflows 全機能を単一 doc で管理し、`cli/config/functional-registry.yaml` (L4 carry) のソースとして機能する
2. **FR-INV-01** (資産 inventory / density 可視化) の補完: CLI / lib / hook / agent / skill / workflow doc / template の全件を工程別 FR trace 付きで一覧化する
3. **helix doctor `check_functional_registry`** (L4 carry) の audit 対象 doc: §3〜§9 の ID と実コードを突合し、未登録資産を warn する基盤を提供する

---

## §1.5 更新規律 — 機能を追加/復元/改廃する駆動 workflow の必須 exit

> **デグレ第一歩の封鎖**: 機能が追加されても本 registry に載らなければ、FR-FNREG-01 (機能一覧 SSoT) が実態から静かに乖離し、`check_functional_registry` の母数が穴あきになる。これが機能網羅カバレッジ劣化の起点である。**機能 inventory を変える駆動 workflow は、本 registry への登録/同期を exit 条件（完了条件）とする**。

| 駆動 workflow | registry 操作 | 必須/任意 |
|---|---|---|
| Add-feature | 新規機能を §該当区分へ **追加登録**（機能名 / 説明 / L1 FR / L3 FR / status） | **必須** |
| Reverse | 復元した既存機能を **登録/補完**（本 registry 自体が Reverse fullback で生成された経緯） | **必須** |
| Retrofit | 改廃・移設に伴い entry を **同期**（path/名称/status 更新、廃止は status 変更） | **必須**（inventory が変わる場合） |
| Refactor | 振る舞い不変が原則。関数の rename/split で entry 名が変わるなら **同期のみ** | inventory 変化時のみ |
| Discovery | confirmed を Forward 昇格（add-feature 等）した時点で登録 | 昇格先 workflow が担保 |
| Incident / Recovery | 恒久対策で新機能を足した場合のみ登録 | 機能追加時のみ |

- **登録単位の必須項目**: 機能名 / 一行説明 / L1 FR trace / L3 FR trace / status（active 等）。§2 summary の件数も同期する。
- **機械 enforcement**: `helix doctor check_functional_registry`（L4 carry）が §3〜§9 の ID と実コード（cli/lib/hook/agent/skill/workflow/template）を突合し、**未登録資産を fail-close で検出**する。実装までは本 exit 条件を手続きで担保し、実装後は gate で担保する（Phase 検証で whole-coverage detector に統合）。
- **駆動 workflow doc 側の参照**: add-feature / reverse / retrofit の各 workflow doc は本 §1.5 を exit 条件として参照する（規律の再定義はせず本 doc を SSoT とする）。

---

## §2. 全体 summary

| 区分 | 件数 |
|---|---|
| CLI binaries (cli/helix-*) | 80 |
| CLI lib modules (cli/lib/*.py) | 139 |
| Hooks (.claude/hooks/*.sh) | 17 |
| Subagents (.claude/agents/*.md) | 19 |
| Skills (skills/**/SKILL.md) | 130 |
| HELIX-workflows doc (helix-process/*.md + root) | 49 |
| Templates (cli/templates/**) | 114 |
| **総計** | **548** |

### FR mapping coverage

| 対象 | L1 FR | L3 FR | coverage |
|---|---|---|---|
| CLI (80) | FR-01〜FR-13 全13件 に1件以上対応 | FR-NSM-01〜FR-MIGR-01 全18件 に1件以上対応 | 100% |
| lib (139) | 全13件 | 全18件 | 100% |
| hook (17) | 全13件 | 全18件 | 100% |
| agent (19) | 全13件 | 全18件 | 100% |
| skill (130) | 全13件 | FR-FNREG-01 / FR-GLOSSARY-01 = 間接のみ | 16/18 (89%) |
| workflow doc (49) | 全13件 | FR-FNREG-01 / FR-GLOSSARY-01 = 間接のみ | 16/18 (89%) |

### 漏れ候補数

| 方向 | 件数 |
|---|---|
| 逆方向 (実装あり要件なし) | 10 件 (§12.1 参照) |
| 順方向 (要件あり実装なし) | 2 件 (§12.2 参照) |

---

## §3. CLI binaries (cli/helix-*)

全 80 件。状態凡例: `active` / `deprecated` / `legacy alias` / `mandatory` / `experimental`

> **注**: `ls cli/helix-*` で 94 件が表示されるのは `cli/helix-plan-cmds/` ディレクトリ配下の 12 件 sub-script (_shared.sh / deps.sh / draft.sh / finalize.sh / generates.sh / import.sh / lint.sh / list.sh / mini.sh / reset.sh / review.sh / status.sh) と dir entry 2 件を ls が含めるため。`find cli -maxdepth 1 -type f -executable -name 'helix-*'` で再 verify 結果は **80 件 (独立 CLI)**。

| CLI | 主機能 | 関連 L1 FR | 関連 L3 FR | 状態 |
|---|---|---|---|---|
| helix-add-feature | Add-feature workflow mode CLI (既存 system 追補、add_feature_engine.py 委譲) | FR-04 | FR-9MODE-01 | active |
| helix-agent | subagent slot 管理 (fire-mandatory / suggest / slots / audit、PLAN-076/082 機械化) | FR-10 | FR-CTX-01 | active |
| helix-asset | 既存資産 inventory CLI (コード index catalog 系 motif/design 管理) | FR-09 | FR-INV-01 | active |
| helix-audit | Phase 0 preflight 一括実行 / A1 state machine 操作 (preflight/decisions/status) | FR-09 | FR-INV-01 | active |
| helix-auto-run | 自動走行 framework skeleton CLI (auto_run_engine.py 委譲、5-layer auto-run) | FR-07 | FR-EVT-01 | experimental |
| helix-bats-cleanup | Bats テスト一時ファイル (/tmp/bats-run-*, /tmp/bats-test-*) クリーンアップ | - | - | active |
| helix-bench | プロジェクトメトリクスサマリ表示 (project metrics summary) | FR-09 | FR-INV-01 | active |
| helix-budget | Claude/Codex 消費取得・予測・残量表示 (status/simulate/forecast サブコマンド) | FR-07 | FR-CTX-01 | active |
| helix-builder | Builder System CLI (型登録・builder registry 操作) | FR-12 | FR-PLAN-01 | active |
| helix-check-claudemd | 後方互換 shim (旧 CLAUDE.md チェック) | - | - | deprecated |
| helix-claude | Claude Code 向け plan/task 管理 harness (--role PMO/advisor/pmo 委譲) | FR-01 | FR-9MODE-01 | active |
| helix-code | コード index catalog 管理・表示・検索 (build/find/show/dup/stats/list、PLAN-011〜013) | FR-09 | FR-INV-01 | active |
| helix-codex | HELIX スキル注入付き Codex CLI ラッパー (--role 別スキル + plan guard 注入) | FR-01 | FR-CTX-01 | mandatory |
| helix-commands | コマンドカタログ表示 (route/help 由来コマンド一覧 list/show/check) | FR-09 | FR-INV-01 | active |
| helix-context | context / memory guardrail checks (context 枯渇監視 / guardrail 整合確認) | FR-02 | FR-GR-01 | active |
| helix-dashboard | HELIX state dashboard (プロジェクト全体状態ビジュアル表示) | FR-09 | FR-INV-01 | active |
| helix-db | HELIX DB utilities (helix.db 操作 / local rollback drill / schema 管理) | FR-08 | FR-MIGR-01 | active |
| helix-debt | 技術負債台帳管理 (deferred-findings / debt 登録・一覧・クリア) | FR-09 | FR-INV-01 | active |
| helix-debug | HELIX デバッグツール (内部状態ダンプ / hook デバッグ) | - | - | active |
| helix-detect | PLAN-063 detector router entrypoint (axis-01〜14 detector 実行・verdict 記録) | FR-02 | FR-GR-01 | active |
| helix-discover | local/global recipe から類似候補検索 (Discovery 旧版、recipe 系) | FR-04 | FR-9MODE-01 | active |
| helix-discovery | HELIX Discovery 検証駆動開発 CLI (D0-D4 仮説検証フロー、init/backlog/plan/poc/verify/decide) | FR-04 | FR-9MODE-01 | active |
| helix-doctor | 環境チェック・ドキュメント整合監査 (pass/warn/error 判定、--json/--type フラグ) | FR-11 | FR-DOCTOR-01 | mandatory |
| helix-drift-check | 設計 doc と実装の契約ドリフト検知 (D-API/D-DB vs 実装コード比較) | FR-05 | FR-DRIFT-01 | active |
| helix-entry | HELIX entry (7 軸 + 関連 link の単体表示 / 一覧フィルタ) | FR-09 | FR-INV-01 | active |
| helix-gate | HELIX ゲート自動検証 (G0-G14 ゲート通過判定 / --pair-check / --drive 引数) | FR-03 | FR-GATE-01 | mandatory |
| helix-gate-api-check | 後方互換 shim (旧 gate API チェック) | - | - | deprecated |
| helix-handover | Claude Code ⇔ Codex CLI 非同期 handover 管理 (dump/update/resume/clear/status) | FR-07 | FR-EVT-01 | mandatory |
| helix-harness | AI harness コア操作 (recommend-compact / auto-dump / harness サブコマンド) | FR-07 | FR-EVT-01 | active |
| helix-heartbeat-scheduler | PLAN-099 §9 ハートビートスケジューラ (carry>0 AND bg task なし時の adaptive 起動) | FR-07 | FR-EVT-01 | experimental |
| helix-hook | 後方互換 shim (旧 hook 管理) | - | - | deprecated |
| helix-incident | Incident mode CLI (hotfix / incident_engine.py 委譲) | FR-04 | FR-9MODE-01 | active |
| helix-init | HELIX プロジェクト初期化 (テンプレート配布 / .helix/ ディレクトリ構築) | FR-01 | FR-9MODE-01 | mandatory |
| helix-innovation | PdM innovation pipeline (tech/marketing/manager 翻案フロー) | FR-01 | FR-CTX-01 | active |
| helix-interrupt | IIP (Interrupt In Progress) / CC の割り込み管理 | FR-07 | FR-EVT-01 | active |
| helix-job | ジョブキュー操作 (enqueue/pop/list/status/clear、PLAN-091 P0 guard 連動) | FR-07 | FR-EVT-01 | active |
| helix-learn | 成功タスクから recipe 生成 + global.db 同期 (learning_engine 委譲) | FR-07 | FR-EVT-01 | active |
| helix-lock | Single-host ロック管理 (acquire/release/status、scope home|project) | FR-07 | FR-EVT-01 | active |
| helix-log | HELIX ログ・評価システム (task 実行履歴 / report / session 集計) | FR-09 | FR-INV-01 | active |
| helix-matrix | matrix.yaml ベースの生成/検証ユーティリティ (drive × layer matrix) | FR-01 | FR-GATE-01 | active |
| helix-meta-phase | PLAN-006 L1 内メタ工程 (pattern.yaml 固定ルール契約検証) | FR-03 | FR-GATE-01 | active |
| helix-migrate | HELIX 配布対象への安全なマージアップデート (template migration) | FR-08 | FR-MIGR-01 | active |
| helix-mode | 開発モード/drive 管理 (be/fe/fullstack/scrum/agent/db/reverse など切替) | FR-04 | FR-9MODE-01 | active |
| helix-observe | observability イベント操作 (log --event / stats / export) | FR-09 | FR-INV-01 | active |
| helix-plan | 設計提案の下書き/レビュー/確定管理 (draft/review/finalize/lint/list/status) | FR-06 | FR-PLAN-01 | mandatory |
| helix-pr | ゲート結果から PR テンプレート自動生成 | FR-03 | FR-GATE-01 | active |
| helix-promote | Builder registry 型登録 (promote サブコマンド) | FR-09 | FR-INV-01 | active |
| helix-push | git push ゲート (6 ゲート検証 + 全 PASS 時のみ push 実行) | FR-03 | FR-GATE-01 | mandatory |
| helix-readiness | HELIX readiness exit 判定 / deferred-finding 操作 | FR-03 | FR-GATE-01 | active |
| helix-recipe | 成功パターン学習系コマンド統合ディスパッチャ (learn/promote/discover) | FR-07 | FR-EVT-01 | active |
| helix-recover | Recovery mode CLI (recovery_engine.py 委譲、AI 暴走収束) | FR-04 | FR-9MODE-01 | active |
| helix-recovery | Recovery workflow CLI (recovery_workflow_engine.py 委譲、詳細フロー) | FR-04 | FR-9MODE-01 | active |
| helix-refactor | Refactor mode CLI (refactor_engine.py 委譲、振る舞い不変構造改善) | FR-04 | FR-9MODE-01 | active |
| helix-research | L1-L3 設計厳格化向け技術調査テーマ生成 (--layer L2|L3 / --auto / --dry-run) | FR-04 | FR-9MODE-01 | active |
| helix-retro | ミニレトロ管理 (G2/G4/L8 通過時のレトロ記録・表示) | FR-03 | FR-GATE-01 | active |
| helix-retrofit | Retrofit mode CLI (retrofit_engine.py 委譲、依存・基盤の段階改修) | FR-04 | FR-9MODE-01 | active |
| helix-reverse | Reverse HELIX pipeline (R0-R4-RGC、既存コード→設計復元) | FR-04 | FR-9MODE-01 | active |
| helix-review | Codex 自動レビュー (--uncommitted / --plan-id、review_output.py 利用) | FR-03 | FR-DOCREVIEW-01 | active |
| helix-route | L7-helix-route-implplan route entrypoint (route_engine.py、mode 自動推奨) | FR-04 | FR-9MODE-01 | active |
| helix-scheduler | スケジューラ操作 (add/remove/list/run、cron / +Nm 形式) | FR-07 | FR-EVT-01 | active |
| helix-scrum | DEPRECATED alias shim → helix-discovery へ転送 | - | - | legacy alias |
| helix-scrum-agile | Scrum (アジャイル) mode CLI (scrum_agile_engine.py 委譲) | FR-04 | FR-9MODE-01 | active |
| helix-session-start | 後方互換 shim (旧 session-start) | - | - | deprecated |
| helix-session-summary | セッション終了時 cost_log INSERT (helix.db cost_log テーブル記録) | FR-07 | FR-EVT-01 | active |
| helix-setup | HELIX コンポーネント初期化・検証 (verify/install/list サブコマンド) | FR-01 | FR-9MODE-01 | active |
| helix-size | タスクサイジング + フェーズスキップ自動判定 (S/M/L × drive × フラグ判定) | FR-01 | FR-9MODE-01 | mandatory |
| helix-skill | スキル catalog 管理・表示・検索 (list/show/catalog/search/use/chain/stats) | FR-09 | FR-INV-01 | mandatory |
| helix-sprint | L7 実装スプリント管理 (plan/start/complete/status/addon、標準 8 ステップ) | FR-06 | FR-PLAN-01 | mandatory |
| helix-status | プロジェクト全体の HELIX 状態表示 (phase.yaml / handover / doctor 統合) | FR-09 | FR-INV-01 | active |
| helix-statusline | コンテキスト % 先回り監視 (>50%/30-50%/≤30%/≤20% 4 段階 warning) | FR-07 | FR-EVT-01 | active |
| helix-stop-hook | Stop hook エントリ (handover auto dump + compact recommendation) | FR-07 | FR-EVT-01 | active |
| helix-task | HELIX タスクオペレーティングシステム (task create/update/list/show/pop) | FR-06 | FR-PLAN-01 | active |
| helix-team | エージェントチーム実行 (team_runner.py 委譲、複数 role 協調) | FR-10 | FR-CTX-01 | active |
| helix-test | HELIX CLI 全ツールセルフテスト (bats + pytest 統合実行) | - | - | active |
| helix-test-debug | debug-enabled セルフテスト wrapper | - | - | active |
| helix-test-design-scaffold | テスト設計 scaffold 生成 CLI (test-design-scaffold.py 委譲、pair layer) | FR-08 | FR-4ART-01 | active |
| helix-verify-agent | PLAN-010 verification agent CLI (verify_agent.py 委譲) | FR-08 | FR-4ART-01 | active |
| helix-verify-all | HELIX 全レイヤー検証を 1 コマンドで実行 | FR-08 | FR-4ART-01 | active |
| helix-vmodel | V-model 操作 (list/show/vmodel-score/vertical-check、--drive/--injection-only) | FR-08 | FR-4ART-01 | active |
| helix-workspace | Workspace manager dispatcher (PLAN-156/ADR-040、isolation/exec/list/cleanup) | FR-07 | FR-EVT-01 | active |

---

## §4. CLI lib modules (cli/lib/*.py)

全 139 件。

| Module | 責務 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| add_feature_engine.py | Add-feature mode CLI backend | FR-04 | FR-9MODE-01 |
| agent_engine.py | HELIX W agent drive CLI backend | FR-10 | FR-CTX-01 |
| agent_mandatory.py | subagent fire-mandatory + suggest + audit (PLAN-076/082 機械化) | FR-10 | FR-CTX-01 |
| agent_policy_guard.py | HELIX team 委譲定義のポリシーチェック | FR-02 | FR-GR-01 |
| agent_slots.py | agent slot fire / list / stale 検出 | FR-10 | FR-CTX-01 |
| allowed_files_estimator.py | 実装タスクで変更される可能性があるファイル群の事前推定 | FR-10 | FR-CTX-01 |
| audit_a1.py | A1 state machine: decisions.yaml → audit_decisions / import_runs 同期 | FR-09 | FR-INV-01 |
| audit_hash.py | A1 canonical hash 計算 (PLAN-002 v3 凍結済み仕様) | FR-09 | FR-INV-01 |
| audit_inventory.py | inventory discovery 出力から A0 decisions.yaml 下書き生成 | FR-09 | FR-INV-01 |
| audit_validator.py | decisions.yaml スキーマ検証 (PLAN-002 Sprint 2a) | FR-09 | FR-INV-01 |
| auto_run_engine.py | helix auto-run framework skeleton (5-layer 自動走行) | FR-07 | FR-EVT-01 |
| budget.py | Claude/Codex 消費取得とキャッシュ・予測 | FR-07 | FR-CTX-01 |
| budget_cli.py | helix-budget サブコマンドエントリ | FR-07 | FR-CTX-01 |
| budget_forecast.py | budget 枯渇 forecast helpers | FR-07 | FR-CTX-01 |
| code_catalog.py | HELIX code index catalog 生成・保存・検索 | FR-09 | FR-INV-01 |
| code_edges.py | コード依存グラフ edge 管理 | FR-09 | FR-INV-01 |
| code_recommender.py | code index 流用候補を Codex で推挙 | FR-09 | FR-INV-01 |
| codex_post_hook.py | helix-codex TL review 出力の後処理 helpers | FR-10 | FR-CTX-01 |
| codex_post_validation.py | Codex 出力の後処理バリデーション | FR-02 | FR-GR-01 |
| codex_thinking.py | HELIX Codex thinking level 解決 (CLI / auto classification / role config) | FR-10 | FR-CTX-01 |
| command_catalog.py | HELIX CLI コマンドカタログ helpers (routing/help/docs チェック) | FR-09 | FR-INV-01 |
| command_mapper.py | HELIX コマンドマッピング (layer/gate/category → 関連コマンドリスト) | FR-03 | FR-GATE-01 |
| compaction_adapter.py | auto-run 用 compaction adapter PoC | FR-07 | FR-EVT-01 |
| compatibility_adapter.py | helix.db 分離の段階的移行 compatibility adapter (PLAN-084) | FR-08 | FR-MIGR-01 |
| concurrent_lock.py | 並列 lock 管理 (workspace isolation 用) | FR-07 | FR-EVT-01 |
| context_guard.py | HELIX context / guardrail 整合確認チェック | FR-02 | FR-GR-01 |
| contract_registry.py | API/DB 契約 registry 管理 | FR-08 | FR-4ART-01 |
| correlation_context.py | cross-db trace propagation 用 correlation context helpers | FR-07 | FR-EVT-01 |
| cutover_orchestrator.py | PLAN-084 Phase 4.C cutover gate 5 orchestration helpers | FR-08 | FR-MIGR-01 |
| db_cli.py | HELIX DB CLI helpers (local rollback drill) | FR-08 | FR-MIGR-01 |
| defaults_loader.py | cli/config/defaults.yaml からの共通 HELIX CLI defaults 読み込み | FR-10 | FR-CTX-01 |
| deferred_findings.py | deferred-finding (carry) の登録・参照・解消 | FR-03 | FR-GATE-01 |
| deliverable_gate.py | HELIX deliverable gate checker (成果物存在確認) | FR-03 | FR-GATE-01 |
| demotion_checker.py | PLAN-097 §10 demotion 判定 (skill/command 降格チェック) | FR-09 | FR-INV-01 |
| discovery_compat.py | Discovery mode 後方互換 adapter (scrum → discovery 移行) | FR-04 | FR-9MODE-01 |
| discovery_migrate.py | scrum → discovery state machine migration (Stage 1-4) | FR-04 | FR-9MODE-01 |
| doc_map_matcher.py | doc-map.yaml トリガーマッチャー | FR-08 | FR-4ART-01 |
| doctor_plan_checks.py | PLAN-093 §5 doctor plan 系チェック (plan drift / generates / dependencies) | FR-11 | FR-DOCTOR-01 |
| doctor_recovery_check.py | PLAN-098 §9 doctor recovery チェック | FR-11 | FR-DOCTOR-01 |
| doctor_summary.py | helix doctor --summary 集計出力 | FR-11 | FR-DOCTOR-01 |
| drift_db_diff.py | D-DB markdown schema vs SQLite DB の diff 検出 | FR-05 | FR-DRIFT-01 |
| dual_write_connection.py | PLAN-084 compatibility adapter 用 dual-write SQLite connection wrapper | FR-08 | FR-MIGR-01 |
| dual_write_mismatch.py | PLAN-084 Phase 4.B.6 dual-write mismatch detector | FR-08 | FR-MIGR-01 |
| effort_classifier.py | タスク難度 → effort 自動判定 (effort-classifier role) | FR-10 | FR-CTX-01 |
| entry_helper.py | HELIX entry (7 軸 + 関連 link) 操作 helpers | FR-09 | FR-INV-01 |
| escalation_engine.py | PLAN-097 §8/9 escalation engine (handover escalate / recovery 起動) | FR-07 | FR-EVT-01 |
| escalation_integration.py | PLAN-097 §8/11 + PLAN-093 §7 escalation integration | FR-07 | FR-EVT-01 |
| event_envelope.py | PLAN-084 event-sourced databases 用 event envelope helpers | FR-07 | FR-EVT-01 |
| feedback_hook.py | PLAN-004 gate feedback hook | FR-03 | FR-GATE-01 |
| freeze_checker.py | HELIX freeze-break checker (runtime/index.json 駆動) | FR-03 | FR-GATE-01 |
| gate_check_generator.py | gate/doc-map generator (matrix_compiler から抽出) | FR-03 | FR-GATE-01 |
| gate_policy_helper.py | gate-policy.md から gate accuracy weights 読み込み helpers | FR-03 | FR-GATE-01 |
| global_store.py | HELIX global recipe store | FR-07 | FR-EVT-01 |
| handover.py | handover コアロジック (JSON + Markdown、dump/update/resume/clear) | FR-07 | FR-EVT-01 |
| handover_auto_dump.py | Stop hook 用 handover auto dump + compact recommendation | FR-07 | FR-EVT-01 |
| harness_monitor.py | harness check event 記録 / recent events 取得 | FR-07 | FR-EVT-01 |
| helix_db.py | HELIX ログ DB (SQLite ベース task 実行・評価・改善追跡) | FR-07 | FR-EVT-01 |
| hook_payload.py | Claude Code hook payload helpers | FR-07 | FR-EVT-01 |
| incident_engine.py | Incident mode CLI backend | FR-04 | FR-9MODE-01 |
| init_helpers.py | helix-init 後処理 helpers | FR-04 | FR-9MODE-01 |
| invocation_helper.py | CLI 呼び出し共通 helpers | FR-10 | FR-CTX-01 |
| job_p0_guard.py | PLAN-091 §12 job P0 guard (plan consent 通過確認) | FR-07 | FR-EVT-01 |
| job_queue_helper.py | job queue 操作 helpers (enqueue/pop/list/status) | FR-07 | FR-EVT-01 |
| learning_engine.py | HELIX learning engine (成功パターン recipe 生成・学習) | FR-07 | FR-EVT-01 |
| llm_classifier_base.py | HELIX LLM バックドクラシファイヤー base class | FR-10 | FR-CTX-01 |
| llm_guard.py | 生 LLM CLI 実行 PreToolUse guard (HELIX_ALLOW_RAW_CODEX 制御) | FR-02 | FR-GR-01 |
| lock_helper.py | Single-host HELIX lock helper | FR-07 | FR-EVT-01 |
| matrix_advisor.py | HELIX matrix advisory checker (Phase 3: advisory only) | FR-03 | FR-GATE-01 |
| matrix_compiler.py | HELIX matrix compiler (drive × layer matrix 生成) | FR-03 | FR-GATE-01 |
| merge_settings.py | ~/.claude/settings.json に HELIX hooks を安全にマージ/除去 | FR-02 | FR-GR-01 |
| meta_phase.py | PLAN-006 meta-phase helpers (pattern.yaml ルール契約検証) | FR-03 | FR-GATE-01 |
| migrate.py | HELIX template migration utility | FR-08 | FR-MIGR-01 |
| model_fallback.py | 枯渇モデルからの降格提案 | FR-10 | FR-CTX-01 |
| model_registry.py | models.yaml からロール別モデル解決 | FR-10 | FR-CTX-01 |
| observability_helper.py | observability event log / stats helpers | FR-09 | FR-INV-01 |
| paths.py | HELIX 共通パス解決 helpers | FR-10 | FR-CTX-01 |
| phase_guard.py | HELIX phase guard checker (フェーズ逸脱防止) | FR-03 | FR-GATE-01 |
| plan_dependencies.py | PLAN dependency graph 管理 | FR-12 | FR-PLAN-01 |
| plan_deps_helper.py | PLAN dependency helpers (requires/parent/blocks 解決) | FR-12 | FR-PLAN-01 |
| plan_frontmatter.py | PLAN markdown frontmatter + YAML state の atomic finalize helper | FR-12 | FR-PLAN-01 |
| plan_health.py | PLAN health チェック (plan_health score 算出) | FR-12 | FR-PLAN-01 |
| plan_lint.py | PLAN frontmatter lint (VALID_KINDS 同期、plan_validator と一致 test) | FR-12 | FR-PLAN-01 |
| plan_parser.py | PLAN-092 §5/7/8 PLAN frontmatter parser | FR-12 | FR-PLAN-01 |
| plan_registry.py | PLAN-100 Phase 4 Wave 4 plan registry (is_reference filter 付き) | FR-12 | FR-PLAN-01 |
| plan_schema.py | PLAN.yaml schema helpers (gate/plan tooling 用) | FR-12 | FR-PLAN-01 |
| plan_validator.py | 新 15 工程 (L0-L14) PLAN frontmatter 検証 (VALID_KINDS 22 種) | FR-12 | FR-PLAN-01 |
| projector_lag.py | Projector lag helper (handover/review 遅延検出) | FR-07 | FR-EVT-01 |
| push_gate.py | git push 前の 6 ゲート検証 (push_gate) | FR-03 | FR-GATE-01 |
| recovery_engine.py | Recovery mode CLI backend | FR-04 | FR-9MODE-01 |
| recovery_plan_check.py | PLAN-098 §5/6/9 recovery plan check | FR-04 | FR-9MODE-01 |
| recovery_workflow_engine.py | Recovery workflow CLI backend | FR-04 | FR-9MODE-01 |
| redaction.py | 秘密情報 redaction helpers (secret/PII マスク) | FR-02 | FR-GR-01 |
| refactor_engine.py | Refactor mode CLI backend | FR-04 | FR-9MODE-01 |
| research_guard.py | HELIX G1R research gate fail-close checks | FR-03 | FR-GATE-01 |
| research_tool_guard.py | WebSearch/WebFetch hook events PreToolUse guard | FR-02 | FR-GR-01 |
| retrofit_engine.py | Retrofit mode CLI backend | FR-04 | FR-9MODE-01 |
| reverse_local.py | confirmed scrum → reverse routing init helpers | FR-04 | FR-9MODE-01 |
| review_output.py | HELIX review JSON 出力の検証・正規化 | FR-08 | FR-DOCREVIEW-01 |
| rollback_orchestrator.py | PLAN-084 gate 6 rollback orchestration helpers | FR-08 | FR-MIGR-01 |
| route_engine.py | HELIX route engine (mode 自動推奨、9 mode + drive_agent + auto_run) | FR-04 | FR-9MODE-01 |
| scheduler_helper.py | スケジューラ操作 helpers (cron / +Nm 形式 add/remove/run) | FR-07 | FR-EVT-01 |
| scrum_agile_engine.py | Scrum (agile) mode CLI backend | FR-04 | FR-9MODE-01 |
| scrum_local.py | UPS loop local scrum state management | FR-04 | FR-9MODE-01 |
| scrum_reverse_matrix.py | PLAN-095 §5/6/7 scrum × reverse matrix | FR-04 | FR-9MODE-01 |
| scrum_to_reverse_routing.py | PLAN-095 §8/9 scrum → reverse routing | FR-04 | FR-9MODE-01 |
| scrum_trigger.py | scrum 開始 trigger helpers | FR-04 | FR-9MODE-01 |
| session_cleaner.py | HELIX auto-run 用 session cleaner PoC | FR-07 | FR-EVT-01 |
| session_helper.py | PLAN-083 Phase 4 session_id 検出 helper | FR-07 | FR-EVT-01 |
| session_start_helpers.py | SessionStart hook 用進捗サマリ生成 | FR-07 | FR-EVT-01 |
| setup_helper.py | HELIX setup コンポーネント runner | FR-04 | FR-9MODE-01 |
| shadow_replay.py | PLAN-084 Phase 4.C shadow replay helpers | FR-08 | FR-MIGR-01 |
| skill_catalog.py | スキル catalog 生成・保存・検索 (SKILL.md frontmatter + references parser) | FR-09 | FR-INV-01 |
| skill_classifier.py | HELIX スキル分類を Codex で実行 | FR-09 | FR-INV-01 |
| skill_classify_runner.py | スキル分類実行 runner | FR-09 | FR-INV-01 |
| skill_dispatcher.py | スキル推挙結果 → 実際の委譲アクション変換 | FR-09 | FR-INV-01 |
| skill_frontmatter_lint.py | SKILL.md frontmatter lint | FR-09 | FR-INV-01 |
| skill_helix_layer_audit.py | SKILL.md helix_layer フィールド audit | FR-09 | FR-INV-01 |
| skill_jsonl_schema.py | skill JSONL schema helpers | FR-09 | FR-INV-01 |
| skill_recommender.py | HELIX スキル推挙を Codex で実行 (gpt-5.4-mini 経由、1 時間 TTL キャッシュ) | FR-09 | FR-INV-01 |
| skill_review.py | skill 品質レビュー helpers | FR-08 | FR-DOCREVIEW-01 |
| skip_annotation_linter.py | @skip アノテーション lint (テスト skip 過剰検出) | FR-08 | FR-4ART-01 |
| sprint_auto_check.py | Sprint auto check (Step 4 mandatory: py_compile / lint / test) | FR-12 | FR-PLAN-01 |
| sprint_lint.py | PLAN-082 Phase 3 Sprint completion audit helpers | FR-12 | FR-PLAN-01 |
| task_dispatcher.py | task dispatch helpers (task_type_inference 連携) | FR-12 | FR-PLAN-01 |
| task_type_inference.py | task type 推論 (impl/design/review/research 等の分類) | FR-10 | FR-CTX-01 |
| team_runner.py | HELIX Team Runner (複数 role 協調実行) | FR-10 | FR-CTX-01 |
| test_design_scaffold.py | テスト設計 scaffold 生成 (pair_layer / title 組み合わせ) | FR-08 | FR-4ART-01 |
| transcript_summary.py | PLAN-099 §8 transcript summary (会話要約 + 関連 PLAN/handover bundle) | FR-07 | FR-EVT-01 |
| uuid7_generator.py | UUID v7 generator (event_id 発行用) | FR-07 | FR-EVT-01 |
| verify_agent.py | PLAN-010 verification agent (spec 駆動検証) | FR-08 | FR-4ART-01 |
| vmodel_lint.py | V-model 4 artifact 双方向 trace lint (PLAN-075 Phase 5) | FR-08 | FR-4ART-01 |
| vmodel_loader.py | V-model semantics loader (PLAN V2-PHASE-2 Task B) | FR-08 | FR-4ART-01 |
| vmodel_pair_freeze.py | V-model pair freeze 管理 (L1↔L14 等の pair 凍結) | FR-08 | FR-4ART-01 |
| workflow_dsl_parser.py | PLAN-097 §6/7 workflow DSL parser (recovery/escalation workflow) | FR-04 | FR-9MODE-01 |
| workspace_cli.py | `helix workspace` CLI entrypoint | FR-07 | FR-EVT-01 |
| workspace_manager.py | HELIX workspace manager (PLAN-156/ADR-040、isolation/lock/exec) | FR-07 | FR-EVT-01 |
| workspace_snapshot.py | HELIX workspace state snapshot generator (PLAN-156/ADR-040 D3) | FR-07 | FR-EVT-01 |
| yaml_parser.py | Lightweight YAML parser (PyYAML 不要、frontmatter 用) | FR-10 | FR-CTX-01 |
| zizmor_ignore_lint.py | PLAN-222 AC-5: zizmor:ignore コメント metadata 機械検査 | FR-02 | FR-GR-01 |

---

## §5. Hooks (.claude/hooks/*.sh)

全 17 件。

| Hook | event | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|---|
| post-tool-use.sh | PostToolUse | 汎用 PostToolUse ディスパッチャ (複数後処理の統合) | FR-02 | FR-GR-01 |
| posttooluse-design-doc-web-search-revert.sh | PostToolUse | Edit/Write/MultiEdit 後、設計 doc の WebSearch 不要 revert チェック (PLAN-087 guard) | FR-02 | FR-GR-01 |
| posttooluse-helix-job-enqueue.sh | PostToolUse | ツール完了後 job P0 guard 確認 + advisory enqueue | FR-07 | FR-EVT-01 |
| posttooluse-plan-auto-register.sh | PostToolUse | PLAN.md Write/Edit 時に helix.db に PLAN 自動登録 (PLAN-092 PostToolUse hook) | FR-12 | FR-PLAN-01 |
| posttooluse-skill-catalog-rebuild.sh | PostToolUse | SKILL.md Write/Edit 時に skill catalog を debounce 付きで自動 rebuild | FR-09 | FR-INV-01 |
| precompact-state-snapshot.sh | PreCompact | /compact 前の state snapshot (blocked_sessions 記録 + state 永続化) | FR-07 | FR-EVT-01 |
| pretooluse-agent-fire.sh | PreToolUse | PLAN-083 Phase 2: Agent tool 呼び出し自動 fire (agent_slots 記録) | FR-10 | FR-CTX-01 |
| pretooluse-agent-guard.sh | PreToolUse | subagent guard fail-close (許可 12 種 + model family 一致、exit 2 block) | FR-02 | FR-GR-01 |
| pretooluse-askuserquestion.sh | PreToolUse | AskUserQuestion tool 呼び出し時の DB 記録 + policy チェック | FR-02 | FR-GR-01 |
| pretooluse-codex-slot-check.sh | PreToolUse | Codex CLI 呼び出し前の active slot 数チェック (並列上限確認) | FR-10 | FR-CTX-01 |
| pretooluse-design-doc-web-search-guard.sh | PreToolUse | Edit/Write/MultiEdit 前、設計 doc 改定時の WebSearch 3 query 必須ガード (PLAN-087) | FR-02 | FR-GR-01 |
| pretooluse-opus-repo-block.sh | PreToolUse | Opus による BE コード直接 Edit 禁止ガード (audit log 付き) | FR-02 | FR-GR-01 |
| sessionstart-harness-summary.sh | SessionStart | セッション開始時 stale slot 数 + critical event 数をサマリ表示 | FR-07 | FR-EVT-01 |
| sessionstart-history-injection.sh | SessionStart | セッション開始時 memory/handover/PLAN 要約を context bundle として注入 | FR-10 | FR-CTX-01 |
| stop-recovery-update.sh | Stop | セッション終了時 recovery workflow state snapshot (snapshot_on_stop) | FR-04 | FR-9MODE-01 |
| stop.sh | Stop | Stop hook 汎用ディスパッチャ (handover auto dump 連携) | FR-07 | FR-EVT-01 |
| userpromptsubmit-context-bundle.sh | UserPromptSubmit | ユーザープロンプト送信時 memory/handover/PLAN 関連 summary を context bundle として前付け注入 | FR-10 | FR-CTX-01 |

---

## §6. Subagents (.claude/agents/*.md)

全 19 件。

| Agent | model | 役割 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|---|
| be-api.md | claude-sonnet-4-6 | BE API 実装 (RESTful/GraphQL 設計・endpoint 実装・バリデーション・エラーハンドリング) | FR-04 | FR-9MODE-01 |
| be-logic.md | claude-sonnet-4-6 | BE ビジネスロジック実装 (ドメインモデル・サービス層・ユースケース実装) | FR-04 | FR-9MODE-01 |
| code-reviewer.md | claude-sonnet-4-6 | Senior Staff Engineer 視点 5 軸レビュー (Critical/Important/Minor 整理、実装なし) | FR-08 | FR-DOCREVIEW-01 |
| db-schema.md | claude-sonnet-4-6 | DB スキーマ設計・マイグレーション (ER 図・FK・インデックス・マイグレーション手順) | FR-04 | FR-9MODE-01 |
| devops-deploy.md | claude-sonnet-4-6 | デプロイ・インフラ設計 (Docker/CI-CD/環境分離/監視・アラート) | FR-04 | FR-9MODE-01 |
| pdm-innovation-manager.md | claude-opus-4-7 | PdM Innovation Manager (pdm-tech/marketing 統合 + 新方向性策定 + L1 要件接続) | FR-10 | FR-CTX-01 |
| pdm-marketing-innovation.md | claude-opus-4-7 | PdM Marketing Innovation (海外マーケ思想 PLG/JTBD/NSM 等を日本版適応案に翻案) | FR-10 | FR-CTX-01 |
| pdm-tech-innovation.md | claude-opus-4-7 | PdM Tech Innovation (海外技術思想 Spotify/Stripe/Linear 等を日本版実装案に翻案) | FR-10 | FR-CTX-01 |
| pmo-haiku.md | claude-haiku-4-5-20251001 | PMO 軽作業 (docs/** 限定軽修正・Web 検索・短文 doc 確認、Haiku 4.5 low thinking) | FR-09 | FR-INV-01 |
| pmo-helix-explorer.md | claude-sonnet-4-6 | HELIX Repository Explorer (skills/templates/cli/docs 詳細探索・設計整合チェック前段) | FR-09 | FR-INV-01 |
| pmo-helix-scout.md | claude-haiku-4-5-20251001 | HELIX Repository Scout (HELIX 内軽量目星付け・候補列挙、即応性最大) | FR-09 | FR-INV-01 |
| pmo-project-explorer.md | claude-sonnet-4-6 | Project Repository Explorer (project 内 code/docs/config 詳細探索・流用判断前段) | FR-09 | FR-INV-01 |
| pmo-project-scout.md | claude-haiku-4-5-20251001 | Project Repository Scout (project 内軽量目星付け・候補列挙) | FR-09 | FR-INV-01 |
| pmo-sonnet.md | claude-sonnet-4-6 | PMO 状況把握・docs/PLAN/review 構造化チェック (read-only 中心、Opus context 保護) | FR-09 | FR-INV-01 |
| pmo-tech-docs.md | claude-sonnet-4-6 | Tech Document Manager (設計手法・アーキテクチャ外部 doc 精読 + HELIX 適用案) | FR-09 | FR-INV-01 |
| pmo-tech-fork.md | claude-sonnet-4-6 | Tech Fork Manager (OSS/plugin GitHub 探索・license/maintenance 評価・転用可能性 report) | FR-09 | FR-INV-01 |
| pmo-tech-news.md | claude-sonnet-4-6 | Tech News Advisor (AI/Dev tools/security/cloud 最新動向 sweep、週次 watch) | FR-09 | FR-INV-01 |
| qa-test.md | claude-sonnet-4-6 | QA テスト設計・実行 (戦略・カバレッジ・E2E・perf・security test、L6 検証/G4/G6 gate) | FR-08 | FR-4ART-01 |
| security-audit.md | claude-sonnet-4-6 | セキュリティ監査 (OWASP Top 10・認証認可・脆弱性・依存管理、G2/G4/G6/G7 gate) | FR-02 | FR-GR-01 |

---

## §7. Skills (skills/**/SKILL.md)

全 130 件。カテゴリ別に分割。

### §7.1 workflow/ skills (40 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| workflow/adversarial-review | 設計批判レビュー (G2 固有)、脅威モデルは threat-model 委譲 | FR-05 | FR-GATE-01 |
| workflow/api-contract | API 契約 (D-API/D-CONTRACT)、スキーマ・レスポンス整合検証 | FR-12 | FR-PLAN-01 |
| workflow/compliance | 法令遵守・ライセンス・規制対応 | - | - |
| workflow/context-memory | CLAUDE.md 運用含む AI コンテキスト管理・知識永続化 | FR-10 | FR-CTX-01 |
| workflow/cross-detection | 横断的劣化を複数 axis 組合せで集約検出、後続 routing 渡し | FR-11 | FR-DRIFT-01 |
| workflow/debt-register | G4 通過条件の負債台帳生成・更新 | FR-05 | FR-GATE-01 |
| workflow/dependency-map | 依存関係マップ作成、脆弱性・ライセンス・循環依存検証 | FR-12 | FR-PLAN-01 |
| workflow/deploy | Blue/Green デプロイ戦略・ロールバック・smoke test・G7/G9 連携 | FR-07 | FR-EVT-01 |
| workflow/design-doc | D-API/D-DB/D-CONTRACT/D-STATE テンプレート、G2/G3 ゲート連携 | FR-12 | FR-PLAN-01 |
| workflow/detection-routing | 検出シグナル → SIGNAL_TO_MODE マップ → 後続フロー接続 | FR-11 | FR-DRIFT-01 |
| workflow/dev-policy | 開発方針・品質基準・完成の定義・チームルール雛形 | - | - |
| workflow/dev-setup | OS 別セットアップ・VSCode 設定・開発環境構築 | - | - |
| workflow/doc-review | ドキュメント品質レビュー専用 (4 視点 + 業界標準 + V-model 量閉じ性) | FR-08 | FR-DOCREVIEW-01 |
| workflow/doc-system-architect | 「何を・どこまで・どの粒度で書くか」をメタ設計するスキル | FR-08 | FR-DOCREVIEW-01 |
| workflow/estimation | 三点見積もり・リスク係数・スプリント計画見積もり | - | - |
| workflow/gate-planning | G0.5/G1.5 企画突合・PoC ゲート専用、技術スタック選定 | FR-05 | FR-GATE-01 |
| workflow/incident | 重要度判定 (P0-P3)・対応手順・連絡テンプレート・SLO 達成率検証 | FR-01 | FR-NSM-01 |
| workflow/layer-context-injection | L 単位 owner_role/mandatory_agents/6field 注入、工程別判断負荷削減 | FR-10 | FR-CTX-01 |
| workflow/learning-engine | 検出結果・recovery-log 学習、再発パターン整理、次サイクル改善候補接続 | FR-11 | FR-DRIFT-01 |
| workflow/observability-sre | SLO/SLI 設計・アラート・ダッシュボード・リアルタイム監視設計 | FR-01 | FR-NSM-01 |
| workflow/poc | G1.5 PoC ゲート専用、kill criteria 伴う最小検証、実装着手可否判定 | FR-05 | FR-GATE-01 |
| workflow/postmortem | 5Whys 分析・再発防止アクション・L11 運用学習/G11 連携 | FR-01 | FR-NSM-01 |
| workflow/project-management | ダッシュボード・カンバンテンプレート・計画・進捗・報告運用 | FR-12 | FR-PLAN-01 |
| workflow/quality-lv5 | テスト品質 Lv1-5 評価、テストピラミッド比率・カバレッジ目標検証 | FR-03 | FR-TDD-01 |
| workflow/requirements-deriver | 機能要件→非機能要件導出、R1-R14 シグナル、IPA×ISO 25010 二軸展開 | FR-08 | FR-4ART-01 |
| workflow/requirements-handover | 要件曖昧時の確認質問・仮定管理・引継ぎチェックリスト | FR-08 | FR-4ART-01 |
| workflow/research | G1R 事前調査ゲート、一次情報収集、research_report 作成標準化 | FR-05 | FR-GATE-01 |
| workflow/retrofit | 依存更新・基盤移行・構成変更を段階的に実施する改修モード | FR-04 | FR-9MODE-01 |
| workflow/reverse-analysis | Reverse Phase R 全体ルーター、R0-R4+RGC 統括、5 type 判定 | FR-04 | FR-9MODE-01 |
| workflow/reverse-r0 | R0 証拠収集、code/DB/config/ops 4 軸 evidence_map 作成、RG0 通過判定 | FR-04 | FR-9MODE-01 |
| workflow/reverse-r1 | R1 Observed Contracts 抽出、API・DB・型機械抽出 + characterization tests | FR-04 | FR-9MODE-01 |
| workflow/reverse-r2 | R2 As-Is Design 復元、観測契約から内部構造再構成 + ADR 推定 | FR-04 | FR-9MODE-01 |
| workflow/reverse-r3 | R3 Intent Hypotheses、要件仮説生成 + PO 検証 + Session Hypothesis Log | FR-04 | FR-9MODE-01 |
| workflow/reverse-r4 | R4 Gap & Routing、R3 Intent と As-Is 差分 → Forward HELIX 振り分け | FR-04 | FR-9MODE-01 |
| workflow/reverse-rgc | Reverse Gap Closure、L6/L8 pass 後に Reverse gap 閉塞検証 | FR-04 | FR-9MODE-01 |
| workflow/review-stage-routing | レビュー 6 段階×ロール分業境界、AI 逆説ルール、ADR 降下 | FR-08 | FR-4ART-01 |
| workflow/runbook | L6 Runbook (運用準備書) 生成スキル、G6 RC 判定通過条件 | FR-05 | FR-GATE-01 |
| workflow/schedule-wbs | L3 工程表 (WBS+feature flag+rollback) 生成、G3 通過条件充足 | FR-12 | FR-PLAN-01 |
| workflow/threat-model | G2 通過条件の脅威モデル書生成、STRIDE/DREAD + common/security 連携 | FR-02 | FR-GR-01 |
| workflow/verification | L1〜V-L6 各検証レイヤー、Spec 駆動検証、L8 仕様突合、Reverse RG0-RGC | FR-03 | FR-TDD-01 |

### §7.2 common/ skills (12 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| common/code-review | L7/G7 連携コードレビュー、OWASP・パフォーマンス・設計観点、Google reviewer guide 統合 | FR-08 | FR-4ART-01 |
| common/coding | 命名・構造・型安全性チェック、eslint/ruff/tsc/mypy 連携 | FR-03 | FR-TDD-01 |
| common/design | UI/UX とコンポーネント設計、日本市場向けデザイン原則 | - | - |
| common/documentation | README/API 仕様書/ADR テンプレート・品質確認チェックリスト | FR-08 | FR-DOCREVIEW-01 |
| common/error-fix | 原因特定フロー・デバッグ手順・再現テスト・失敗パターンレジストリ | FR-11 | FR-DRIFT-01 |
| common/git | ブランチ命名規則・コミットメッセージフォーマット・PR テンプレート | FR-12 | FR-PLAN-01 |
| common/infrastructure | Docker・PostgreSQL・Redis・Nginx 本番構成と安全設定 | - | - |
| common/performance | Core Web Vitals 目標値・ボトルネック診断・計測手順 | FR-01 | FR-NSM-01 |
| common/refactoring | 責務分離パターン・共通化判断基準・デグレ対策手順 | FR-11 | FR-DRIFT-01 |
| common/security | OWASP・秘密情報管理・GitHub Actions workflow security (zizmor) | FR-02 | FR-GR-01 |
| common/testing | テストピラミッド戦略、ユニット/統合/E2E テンプレート、G7/G11 カバレッジ目標 | FR-03 | FR-TDD-01 |
| common/visual-design | ビジュアルデザイン基礎 (配色・タイポグラフィ・余白・視線誘導)、デザイン判断支援 | - | - |

### §7.3 project/ skills (19 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| project/api | RESTful/GraphQL API 設計、エンドポイント規約・認証認可パターン | FR-12 | FR-PLAN-01 |
| project/db | D-DB スキーマテンプレート・インデックス設計・マイグレーション安全手順・G3 Schema Freeze 連携 | FR-12 | FR-PLAN-01 |
| project/fe-a11y | axe-core 検証・WCAG 2.1 AA 準拠チェックリスト | - | - |
| project/fe-component | Atomic Design コンポーネントツリー設計・TypeScript Props 型定義 | - | - |
| project/fe-design | FE 情報アーキテクチャ (D-IA) 設計、ページマップ・ナビゲーション階層 | - | - |
| project/fe-style | デザイントークン 3 層定義 (primitive/semantic/component)・CSS/Tailwind 実装方針 | - | - |
| project/fe-test | Storybook/Playwright E2E/VRT 設計と実装 | FR-03 | FR-TDD-01 |
| project/fe-testing/01-taxonomy | FE テスト分類体系 | FR-03 | FR-TDD-01 |
| project/fe-testing/02-strategy-selection | FE テスト戦略選択 | FR-03 | FR-TDD-01 |
| project/fe-testing/03-test-design | FE テスト設計 | FR-03 | FR-TDD-01 |
| project/fe-testing/04-tooling | FE テストツール選定 | FR-03 | FR-TDD-01 |
| project/fe-testing/05-unit-logic | FE 単体テスト (ロジック) | FR-03 | FR-TDD-01 |
| project/fe-testing/06-interaction | FE インタラクションテスト | FR-03 | FR-TDD-01 |
| project/fe-testing/07-integration-msw | FE 統合テスト (MSW) | FR-03 | FR-TDD-01 |
| project/fe-testing/08-visual-regression | FE ビジュアルリグレッション | FR-03 | FR-TDD-01 |
| project/fe-testing/09-accessibility | FE アクセシビリティテスト | FR-03 | FR-TDD-01 |
| project/fe-testing/10-e2e | FE E2E テスト | FR-03 | FR-TDD-01 |
| project/fe-testing/11-ci-flake | FE CI flake 解消 | FR-03 | FR-TDD-01 |
| project/ui | FE 設計知識群インデックス、情報設計・コンポーネント・スタイル・a11y・テストへ接続 | - | - |

### §7.4 advanced/ skills (9 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| advanced/ai-integration | LLM 組み込み・RAG・エージェント設計、ルーティング・ベクトル検索・コンテキスト管理 | FR-10 | FR-CTX-01 |
| advanced/external-api | 外部 API 連携、アダプターパターン・リトライ・サーキットブレーカー堅牢化設計 | FR-12 | FR-PLAN-01 |
| advanced/i18n | 多言語対応、Next.js/FastAPI i18n 実装パターン・Intl API 適用 | - | - |
| advanced/innovation-mgr | PdM Tech/Marketing 出力統合 + 新方向性策定 + L1 接続、意思決定 phase | FR-04 | FR-9MODE-01 |
| advanced/legacy | レガシーコード改修、特性テスト・Strangler Fig パターン・段階的リファクタリング | FR-04 | FR-9MODE-01 |
| advanced/marketing-innovation | 海外マーケティング思想 (Product-led/JTBD/NSM/Reforge/Bowling Alley) 翻案 | - | - |
| advanced/migration | ETL スクリプト・データ整合性検証・Strangler Fig・段階的移行計画 + G7 安定性ゲート | FR-07 | FR-MIGR-01 |
| advanced/tech-innovation | 海外技術思想 (Spotify Squad/Stripe/Linear/DORA/SPACE) 日本版実装翻案 | - | - |
| advanced/tech-selection | 技術選定評価マトリクス・SWOT 分析・ADR テンプレート・選定プロセス | FR-05 | FR-GATE-01 |

### §7.5 tools/ skills (4 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| tools/ai-coding | 構造化プロンプトテンプレート・マルチエージェント戦略・CI/CD エージェント統合・出力レビューチェックリスト | FR-10 | FR-CTX-01 |
| tools/ai-search | Haiku 4.5 リサーチロール委譲、仮説生成・長尺調査要約・多ソース統合 | FR-10 | FR-CTX-01 |
| tools/ide-tools | IDE・AI ツール選定・MCP 設定比較・セットアップ手順 | - | - |
| tools/web-search | ビルトイン WebSearch+WebFetch、一次情報収集・ドキュメント確認・競合調査 | - | - |

### §7.6 integration/ skills (3 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| integration/agent-cost-design | AI エージェント構築着手前のコスト予算・ガードレール確定、生成フロー/マルチベンダー/コスト見積/予算監視 | FR-02 | FR-GR-01 |
| integration/agent-design | LLM agent/task の structural design (要素・骨格・前段制約・後段責務) 参照マップ | FR-10 | FR-CTX-01 |
| integration/agent-teams | 複数エージェント協調運用・役割設計・チーム構成・ビジュアルワークフロー・コスト管理 | FR-10 | FR-CTX-01 |

### §7.7 writing/ skills (6 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| writing/explain | 技術文書の「概要・使い方・例・制約」4 部構成、EEAT コンテンツ品質監査 | FR-08 | FR-DOCREVIEW-01 |
| writing/god-writing | LP/SEO/コピー/UX 文章/セールスコピー統合ライティング (AIDA/PAS/BAB + 心理学 + UX writing + E-E-A-T) | - | - |
| writing/japanese | textlint 統合日本語技術文書品質チェック・JTF 表記ルール準拠 | FR-08 | FR-DOCREVIEW-01 |
| writing/presentation | Marp CLI Markdown→PPTX/PDF スライド自動生成 | - | - |
| writing/social | リリースノート・技術ブログ→X/LinkedIn/Bluesky SNS 投稿案自動生成 | - | - |
| writing/story | ストーリーテリング | - | - |

### §7.8 design-tools/ skills (6 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| design-tools/character | AI 画像生成プロンプト設計でキャラクター・マスコット・アバターデザイン方針構造化 | - | - |
| design-tools/diagram | Mermaid/D2 テキストベース図表生成、フローチャート・シーケンス図・ER 図・アーキテクチャ図 | FR-08 | FR-DOCREVIEW-01 |
| design-tools/gpt-image | GPT Image 2 で SEO 記事アイキャッチ・図解・LP ヒーロー画像生成 ($imagegen built-in) | - | - |
| design-tools/graphic | Vercel Satori 等による SVG/OGP 画像動的生成、ブログ・リリースアイキャッチ自動作成 | - | - |
| design-tools/pptx | python-pptx テンプレートベース PPTX 自動生成、定型報告書・提案書スライドデータ駆動作成 | - | - |
| design-tools/web-system | shadcn/ui デザインシステム構築、コンポーネント選定・テーマ設定・トークン管理 | - | - |

### §7.9 automation/ skills (8 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| automation/browser-script | Playwright codegen によるブラウザ操作記録→E2E テスト雛形自動生成 | FR-03 | FR-TDD-01 |
| automation/flow-optimize | サイトマップ・Playwright 操作記録からユーザーフロー分析・ステップ数削減提案 | - | - |
| automation/init-setup | HELIX automation 初期化検証・導入・修復・DB 追跡 | FR-09 | FR-INV-01 |
| automation/job-queue | HELIX 非同期ジョブ登録・worker・retry・list 管理 | FR-09 | FR-INV-01 |
| automation/lock | HELIX single-host file lock + DB metadata lock 管理 | FR-09 | FR-INV-01 |
| automation/observability | HELIX automation events・metrics 記録・集計・export | FR-01 | FR-NSM-01 |
| automation/scheduler | cron-like 定期実行・単発 at 実行・期限到達 task 実行管理 | FR-09 | FR-INV-01 |
| automation/site-mapping | Crawl4AI・Firecrawl でサイト構造抽出・Reverse 証拠収集・構造化データ抽出自動化 | FR-04 | FR-9MODE-01 |

### §7.10 agent-skills/ skills (24 件)

| skill-id | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| agent-skills/api-and-interface-design | 安定 API・インターフェース設計 (REST/GraphQL/型契約/BE-FE 境界) | FR-12 | FR-PLAN-01 |
| agent-skills/browser-testing-with-devtools | 実ブラウザテスト、DOM 検査・コンソールエラー・ネットワーク・性能・Chrome DevTools MCP | FR-03 | FR-TDD-01 |
| agent-skills/ci-cd-and-automation | CI/CD パイプライン自動化、品質ゲート・テストランナー・デプロイ戦略 | FR-03 | FR-TDD-01 |
| agent-skills/code-review-and-quality | 5 軸 (Correctness/Readability/Architecture/Security/Performance) 多次元コードレビュー | FR-08 | FR-4ART-01 |
| agent-skills/context-engineering | エージェント context 最適化、セッション開始・ルールファイル設定 | FR-10 | FR-CTX-01 |
| agent-skills/debugging-and-error-recovery | 根本原因特定デバッグ、テスト失敗・ビルドエラー・期待外動作への体系的アプローチ | FR-11 | FR-DRIFT-01 |
| agent-skills/deprecation-and-migration | 廃止・移行管理、旧 API/機能廃止・ユーザー移行・sunset 判断 | FR-07 | FR-MIGR-01 |
| agent-skills/documentation-and-adrs | アーキテクチャ決定・公開 API 変更・機能リリース記録、ADR 作成 | FR-08 | FR-DOCREVIEW-01 |
| agent-skills/frontend-ui-engineering | 本番品質 UI 構築、コンポーネント・レイアウト・状態管理 | - | - |
| agent-skills/helix-discovery | 仮説検証駆動開発 D0-D4、confirmed 仮説 → L1 要件昇格 | FR-04 | FR-9MODE-01 |
| agent-skills/helix-scrum | helix-discovery の legacy alias (同機能) | FR-04 | FR-9MODE-01 |
| agent-skills/idea-refine | アイデア反復精錬、発散・収束思考 | - | - |
| agent-skills/incremental-implementation | 段階的変更実装、複数ファイル変更・大規模タスク分割 | FR-12 | FR-PLAN-01 |
| agent-skills/mock-driven-development | FE 駆動 L2 設計でモック→UX 固定→API 契約導出、debt (MOCK-HARDCODE/LEAK/DERIVED) ライフサイクル | FR-04 | FR-9MODE-01 |
| agent-skills/performance-optimization | パフォーマンス要件充足、性能リグレッション・Core Web Vitals・ボトルネック修正 | FR-01 | FR-NSM-01 |
| agent-skills/planning-and-task-breakdown | 作業タスク分解・実装可能単位化・規模見積もり・並列作業判断 | FR-12 | FR-PLAN-01 |
| agent-skills/security-and-hardening | コード脆弱性対策、ユーザー入力・認証・データストレージ・外部連携の hardening | FR-02 | FR-GR-01 |
| agent-skills/shipping-and-launch | 本番ローンチ準備、pre-launch チェックリスト・監視設定・段階的ロールアウト・ロールバック戦略 | FR-07 | FR-EVT-01 |
| agent-skills/source-driven-development | 公式 doc 根拠コード、authoritative・source-cited 実装、古いパターン排除 | FR-08 | FR-4ART-01 |
| agent-skills/spec-driven-development | spec 先行コーディング、要件曖昧・仕様なしプロジェクトの spec 作成 | FR-08 | FR-4ART-01 |
| agent-skills/system-design-sizing | システム規模・スケーラビリティ見積もり、容量計画・ボトルネック特定・トレードオフ分析 | FR-06 | FR-IMPACT-01 |
| agent-skills/technical-writing | Google Technical Writing 原則適用、設計書・API doc・README・SKILL.md・ADR 品質向上 | FR-08 | FR-DOCREVIEW-01 |
| agent-skills/test-driven-development | TDD 全面適用、ロジック実装・バグ修正・動作変更への「テスト→実装」強制 | FR-03 | FR-TDD-01 |
| agent-skills/using-agent-skills | エージェントスキル探索・起動のメタスキル、セッション開始・タスク適合スキル発見 | FR-10 | FR-CTX-01 |

---

## §8. HELIX-workflows doc 一覧

全 49 件 (helix-process/*.md 48 件 + HELIX-process-L0-L14.md 1 件)。分類別に sub-section 分割。

> **注**: `two-stage-agent-design.md` は §8.3 と §8.4 の両 section にクロス掲載されているが、実体は 1 ファイル。合計 49 件は重複なし。

### §8.1 工程定義 doc (L0-L14) — 15 件

| doc | 工程 | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|---|
| L0-concept.md | L0 | 企画書・北極星指標・市場仮説 | FR-04 | FR-9MODE-01 |
| L1-requirements.md | L1 | 要求定義・機能要求・非機能要求・受入条件・運用テスト設計 | FR-08 | FR-4ART-01 |
| L2-ui-design.md | L2 | 画面設計・フロント UI・ワイヤーモック・state-events.md | FR-04 | FR-9MODE-01 |
| L3-requirements-definition.md | L3 | 要件定義・受入テスト設計・FR/NFR 詳細 | FR-08 | FR-4ART-01 |
| L4-basic-design.md | L4 | 基本設計・アーキテクチャ・ADR・総合テスト設計 | FR-05 | FR-GATE-01 |
| L5-detailed-design.md | L5 | 詳細設計・D-API/D-DB・結合テスト設計 | FR-12 | FR-PLAN-01 |
| L6-functional-design.md | L6 | 機能設計・endpoint/関数 schema・単体テスト設計 | FR-12 | FR-PLAN-01 |
| L7-implementation.md | L7 | 実装スプリント、単体テスト実装→本体→3 点レビュー | FR-03 | FR-TDD-01 |
| L8-integration-test.md | L8 | 結合テスト・依存関係解消 (L5 詳細設計↔結合テスト設計 pair) | FR-03 | FR-TDD-01 |
| L9-system-test.md | L9 | 総合テスト・依存関係解消 (L4 基本設計↔総合テスト設計 pair) | FR-03 | FR-TDD-01 |
| L10-ux-refinement.md | L10 | フロント UX 磨き上げ・ビジュアル磨き・コピー磨き (L2↔L10 pair) | - | - |
| L11-final-review.md | L11 | 総合レビュー・ユーザー検証・要件巻き取り・PO 検証・drift 解消 | FR-08 | FR-4ART-01 |
| L12-deployment.md | L12 | デプロイ・受入テスト・環境差異巻き取り (L3↔L12 pair) | FR-07 | FR-EVT-01 |
| L13-post-deployment-verification.md | L13 | デプロイ後検証・smoke/canary・初期インシデント対応 | FR-01 | FR-NSM-01 |
| L14-operation-verification.md | L14 | 運用検証・機能改善 (L1↔L14 pair execute → 次 L0 input) | FR-01 | FR-NSM-01 |

### §8.2 9 mode workflow — 10 件

| doc | mode | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|---|
| HELIX-process-L0-L14.md | Forward | V-model 本体 L0-L14 15 工程 | FR-03 + FR-04 + FR-05 + FR-08 | FR-TDD-01 + FR-9MODE-01 + FR-GATE-01 + FR-4ART-01 |
| scrum-workflow.md | Scrum | アジャイル反復・ユーザー要件すり合わせ | FR-04 | FR-9MODE-01 |
| discovery-workflow.md | Discovery | 仮説検証駆動 D0-D4、confirmed → L1 昇格 | FR-04 | FR-9MODE-01 |
| reverse-workflow.md | Reverse | 既存コード逆引き R0-R4+RGC | FR-04 | FR-9MODE-01 |
| incident-workflow.md | Incident | 本番障害 hotfix、暫定収束→恒久対策 L1/L3/L4-L6 | FR-04 | FR-9MODE-01 |
| add-feature-workflow.md | Add-feature | 既存システムへの差分追補 L4-L7 | FR-04 + FR-07 | FR-9MODE-01 + FR-EVT-01 |
| refactor-workflow.md | Refactor | 振る舞い不変の構造改善 (dedicated CLI 未整備) | FR-04 | FR-9MODE-01 |
| retrofit-workflow.md | Retrofit | 依存・基盤の段階改修・移行 (dedicated CLI 未整備) | FR-04 | FR-9MODE-01 |
| research-workflow.md | Research | 技術調査・意思決定 (helix research CLI あり) | FR-04 | FR-9MODE-01 |
| recovery-workflow.md | Recovery | AI 暴走 guard + 収束 (dedicated CLI 未整備) | FR-04 | FR-9MODE-01 |

### §8.3 工程専門・特殊 workflow — 3 件

| doc | 種別 | 機能 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|---|
| screen-design-workflow.md | 工程専門 (L2) | 画面設計・UI/ワイヤーフレーム (L2 担当) | FR-04 | FR-9MODE-01 |
| frontend-design-workflow.md | 工程専門 (L10) | フロントデザインワークフロー・UX/ビジュアル (L10 担当) | - | - |
| two-stage-agent-design.md | HELIX W (特殊) | 2 段 V 字合流型 Phase1+2+3、AI エージェントシステム構築時専用 | FR-04 | FR-9MODE-01 |

### §8.4 管理基盤 doc — 22 件

| doc | 役割 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| README.md | HELIX-workflows 索引、全 doc へのナビ | FR-09 | FR-INV-01 |
| integration-map.md | スキル・コマンドの穴と統合状況 INDEX・優先度付き roadmap | FR-09 | FR-INV-01 |
| automation-gate-map.md | V-model 自動化・ゲートマップ | FR-05 | FR-GATE-01 |
| asset-mapping.md | 既存資産の整理と設計マッピング (BR-09/10/11/12 対応) | FR-09 | FR-INV-01 |
| detection-routing.md | 検出シグナル→モード連携 (HELIX DB 検出) | FR-11 | FR-DRIFT-01 |
| deviation-plan-map.md | V-model 逸脱と PLAN 起票マップ | FR-11 | FR-DRIFT-01 |
| fe-detector-spec.md | FE detector 判定仕様・動的検証組み込み | FR-11 | FR-DRIFT-01 |
| observability-metrics.md | HELIX 観測・計測機構 (NSM 等) | FR-01 | FR-NSM-01 |
| infra-readiness.md | 検証・テスト・検出基盤の整備状況 | FR-09 | FR-INV-01 |
| folder-structure-review.md | フォルダ構成レビューと再構成 | - | - |
| cross-cutting-mechanisms.md | HELIX 横断機構 | FR-11 | FR-DRIFT-01 |
| cross-detection.md | 横断検出・依存漏れ・契約漏れ・デグレ回避 | FR-11 | FR-DRIFT-01 |
| layer-context-injection.md | L 単位文脈注入機構 (6field injection-set) | FR-10 | FR-CTX-01 |
| test-perspective-gate.md | テスト観点ゲート (W 字補強) | FR-03 | FR-TDD-01 |
| db-auto-registration.md | HELIX DB 自動登録機構 | FR-09 | FR-INV-01 |
| db-integration.md | V-model 本線 DB への収束・接続 | FR-09 | FR-INV-01 |
| learning-engine.md | HELIX Learning Engine・ログ学習機構 | FR-11 | FR-DRIFT-01 |
| continuous-run-context-management.md | 自動走行とコンテキスト管理 | FR-10 | FR-CTX-01 |
| ci-pr-workflow.md | CI / GitHub 運用ワークフロー | FR-03 | FR-TDD-01 |
| review-stage-routing.md | レビュー段階ルーティング (6 段階×ロール分業) | FR-08 | FR-4ART-01 |
| v2-9mode-ecosystem.md | HELIX-workflows V2 9 mode ecosystem アーキテクチャ概観 | FR-04 | FR-9MODE-01 |
| two-stage-agent-design.md | ※§8.3 参照 (管理基盤 doc にも分類) | FR-04 | FR-9MODE-01 |

---

## §9. Templates (cli/templates/*)

全 114 件。フォルダ別に分割。

### §9.1 init 配布テンプレート (AGENTS.md / CLAUDE.md)

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| AGENTS.md.template | helix-init 配布: Codex AGENTS.md テンプレート | FR-04 | FR-9MODE-01 |
| CLAUDE.md.template | helix-init 配布: Claude Code CLAUDE.md テンプレート | FR-04 | FR-9MODE-01 |

### §9.2 設計 doc テンプレート (D-*)

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| D-AGENT-EXEC.md | エージェント実行設計 doc テンプレート | FR-10 | FR-CTX-01 |
| D-AGENT-INFRA.md | エージェントインフラ設計 doc テンプレート | FR-10 | FR-CTX-01 |
| D-TECH-STACK.md | 技術スタック設計 doc テンプレート | FR-04 | FR-9MODE-01 |

### §9.3 agents/ テンプレート (19 件)

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| agents/be-api.md〜security-audit.md (19 file) | helix-init 配布: 全 agent 定義テンプレート | FR-10 | FR-CTX-01 |

### §9.4 assets/ テンプレート (7 件)

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| assets/banner.md〜thumb.md (7 file) | LP / SEO 記事用画像生成プロンプトテンプレート (gpt-image 向け) | - | - |

### §9.5 config / state / gate 系テンプレート

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| action-types.yaml | action type 定義 YAML | FR-07 | FR-EVT-01 |
| config.yaml | helix-init 配布: プロジェクト設定テンプレート | FR-04 | FR-9MODE-01 |
| doc-map.yaml | doc-map トリガー定義テンプレート | FR-08 | FR-4ART-01 |
| framework.yaml | HELIX framework 定義テンプレート | FR-04 | FR-9MODE-01 |
| gate-checks.yaml | gate check 定義 YAML テンプレート | FR-03 | FR-GATE-01 |
| matrix.yaml | drive × layer matrix YAML テンプレート | FR-03 | FR-GATE-01 |
| patterns/pattern.yaml | PLAN-006 固定ルール契約パターン YAML | FR-03 | FR-GATE-01 |
| phase.yaml | phase 状態定義テンプレート | FR-03 | FR-GATE-01 |
| state-machine.yaml | state machine 定義 YAML テンプレート | FR-07 | FR-EVT-01 |
| state/deliverables.json | 成果物 state JSON テンプレート | FR-12 | FR-PLAN-01 |
| state/vmodel.json | V-model state JSON テンプレート | FR-08 | FR-4ART-01 |
| task-catalog.yaml | task catalog YAML テンプレート | FR-12 | FR-PLAN-01 |

### §9.6 docs/ sprint/PLAN テンプレート

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| docs/L1-requirements.md | L1 要件定義 doc テンプレート | FR-12 | FR-PLAN-01 |
| docs/L2-design.md | L2 画面設計 doc テンプレート | FR-12 | FR-PLAN-01 |
| docs/L3-detailed-design.md | L3 詳細設計 doc テンプレート | FR-12 | FR-PLAN-01 |
| docs/L3-schedule-wbs.md | L3 スケジュール WBS テンプレート | FR-12 | FR-PLAN-01 |
| docs/L4-agent-sprint-guide.md | L4 agent drive sprint ガイドテンプレート | FR-12 | FR-PLAN-01 |
| docs/L4-be-sprint-guide.md | L4 BE sprint ガイドテンプレート | FR-12 | FR-PLAN-01 |
| docs/L4-db-sprint-guide.md | L4 DB sprint ガイドテンプレート | FR-12 | FR-PLAN-01 |
| docs/L4-fe-sprint-guide.md | L4 FE sprint ガイドテンプレート | FR-12 | FR-PLAN-01 |
| docs/L4-fullstack-sprint-guide.md | L4 fullstack sprint ガイドテンプレート | FR-12 | FR-PLAN-01 |
| docs/L5-visual-design.md | L5 UX 磨き上げ設計 doc テンプレート | FR-12 | FR-PLAN-01 |
| docs/PLAN.md.template | PLAN.md 汎用テンプレート (frontmatter + 工程表) | FR-12 | FR-PLAN-01 |
| docs/project-status.md.template | project-status.md テンプレート | FR-09 | FR-INV-01 |

### §9.7 plan/ kind 別テンプレート

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| plan/acceptance.yaml | plan acceptance 条件 YAML テンプレート | FR-12 | FR-PLAN-01 |
| plan/add-design/template.md | Add-design kind PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/add-impl/template.md | Add-impl kind PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/design-sprint.yaml.template | Design sprint YAML テンプレート | FR-12 | FR-PLAN-01 |
| plan/design/template.md | Design kind PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/functional-freeze-report.md.template | 機能凍結 report テンプレート (G3/G5 gate 証跡) | FR-03 | FR-GATE-01 |
| plan/impl/template.md | Impl kind PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/innovation-output.yaml.template | PdM innovation 出力 YAML テンプレート | FR-10 | FR-CTX-01 |
| plan/pair-status-checklist.md.template | V-model pair 凍結チェックリストテンプレート | FR-08 | FR-4ART-01 |
| plan/poc/template.md | PoC kind PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/recovery/postmortem-template.md | Recovery postmortem テンプレート | FR-04 | FR-9MODE-01 |
| plan/recovery/template.md | Recovery kind PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/refactor/template.md | Refactor kind PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/research/template.md | Research kind PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/retrofit/template.md | Retrofit kind PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/reverse/template.md | Reverse kind PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/troubleshoot/template.md | Troubleshoot kind PLAN テンプレート | FR-12 | FR-PLAN-01 |

### §9.8 plan/v2/ テンプレート (L0-L14 全工程)

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| plan/v2/L00-planning-template.md | L0 企画書 PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/v2/L01-requirements-template.md | L1 要件定義 PLAN テンプレート | FR-08 | FR-4ART-01 |
| plan/v2/L02-screen-design-template.md | L2 画面設計 PLAN テンプレート | FR-04 | FR-9MODE-01 |
| plan/v2/L03-requirements-definition-template.md | L3 要件定義 PLAN テンプレート | FR-08 | FR-4ART-01 |
| plan/v2/L04-basic-design-template.md | L4 基本設計 PLAN テンプレート | FR-05 | FR-GATE-01 |
| plan/v2/L05-detailed-design-template.md | L5 詳細設計 PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/v2/L06-functional-design-template.md | L6 機能設計 PLAN テンプレート | FR-12 | FR-PLAN-01 |
| plan/v2/L07-implementation-template.md | L7 実装スプリント PLAN テンプレート | FR-03 | FR-TDD-01 |
| plan/v2/L08-integration-test-template.md | L8 結合テスト PLAN テンプレート | FR-03 | FR-TDD-01 |
| plan/v2/L09-system-test-template.md | L9 総合テスト PLAN テンプレート | FR-03 | FR-TDD-01 |
| plan/v2/L10-ux-refinement-template.md | L10 UX 磨き上げ PLAN テンプレート | - | - |
| plan/v2/L11-final-review-template.md | L11 総合レビュー PLAN テンプレート | FR-08 | FR-4ART-01 |
| plan/v2/L12-deployment-template.md | L12 デプロイ PLAN テンプレート | FR-07 | FR-EVT-01 |
| plan/v2/L13-post-deployment-template.md | L13 デプロイ後検証 PLAN テンプレート | FR-01 | FR-NSM-01 |
| plan/v2/L14-operation-verification-template.md | L14 運用検証 PLAN テンプレート | FR-01 | FR-NSM-01 |
| plan/v2/README.md | V2 PLAN テンプレート README | FR-12 | FR-PLAN-01 |

### §9.9 prompts / rules / scrum / teams / hooks / workspace / retro テンプレート

| Path | 用途 | 関連 L1 FR | 関連 L3 FR |
|---|---|---|---|
| prompts/_skeleton.md | プロンプトテンプレートスケルトン | FR-10 | FR-CTX-01 |
| prompts/code-search.md | code 検索プロンプトテンプレート | FR-09 | FR-INV-01 |
| prompts/codex-review.md | Codex レビュープロンプトテンプレート | FR-08 | FR-DOCREVIEW-01 |
| prompts/effort-classify.md | effort 分類プロンプトテンプレート | FR-10 | FR-CTX-01 |
| prompts/feedback.md | gate feedback プロンプトテンプレート | FR-03 | FR-GATE-01 |
| prompts/pmo-base.md | PMO base プロンプトテンプレート | FR-09 | FR-INV-01 |
| prompts/skill-classify.md | skill 分類プロンプトテンプレート | FR-09 | FR-INV-01 |
| prompts/skill-search.md | skill 検索プロンプトテンプレート (9 種 agent 決定マッピング含む) | FR-09 | FR-INV-01 |
| retro.md.template | ミニレトロ記録テンプレート | FR-03 | FR-GATE-01 |
| rules/common-defs.yaml | 共通定義ルール YAML | FR-12 | FR-PLAN-01 |
| rules/deliverables.yaml | 成果物ルール YAML | FR-12 | FR-PLAN-01 |
| rules/naming.yaml | 命名規則 YAML | FR-12 | FR-PLAN-01 |
| rules/structure.yaml | 構造ルール YAML | FR-12 | FR-PLAN-01 |
| scrum-backlog.yaml | Scrum backlog YAML テンプレート | FR-04 | FR-9MODE-01 |
| scrum-handoff.md.template | Scrum handoff md テンプレート | FR-04 | FR-9MODE-01 |
| scrum-sprint.yaml | Scrum sprint YAML テンプレート | FR-04 | FR-9MODE-01 |
| teams/implementation-team.yaml | Implementation team 定義テンプレート | FR-10 | FR-CTX-01 |
| teams/innovation-team.yaml | Innovation team 定義テンプレート | FR-10 | FR-CTX-01 |
| teams/review-team.yaml | Review team 定義テンプレート | FR-10 | FR-CTX-01 |
| teams/twin-sprint.yaml | Twin sprint (BE∥FE) team 定義テンプレート | FR-10 | FR-CTX-01 |
| hooks/commit-msg | git hook: commit message lint テンプレート | FR-02 | FR-GR-01 |
| hooks/post-merge | git hook: post-merge 後処理テンプレート | FR-02 | FR-GR-01 |
| hooks/pre-commit | git hook: pre-commit ガードテンプレート | FR-02 | FR-GR-01 |
| workspace/workspace.yaml | workspace 設定 YAML テンプレート | FR-07 | FR-EVT-01 |
| handover-current.json.template | handover CURRENT.json テンプレート | FR-07 | FR-EVT-01 |
| handover-current.md.template | handover CURRENT.md (人間可読) テンプレート | FR-07 | FR-EVT-01 |

---

## §10. L1 FR → 実装資産 逆引き表

| L1 FR-ID | L1 概要 | 実装資産 (代表、CLI/lib/hook/agent/skill/workflow doc) | L3 FR | 実装状態 |
|---|---|---|---|---|
| FR-01 | NSM 計測・観測指標 | observability-metrics.md / automation/observability / workflow/observability-sre / helix-observe / observability_helper.py / common/performance | FR-NSM-01 | 部分実装 (check_header_count_consistency 等 L4 carry) |
| FR-02 | Guardrail 3 軸 | pretooluse-agent-guard.sh / pretooluse-opus-repo-block.sh / pretooluse-design-doc-web-search-guard.sh / integration/agent-cost-design / common/security / llm_guard.py / context_guard.py / agent_policy_guard.py | FR-GR-01 | 完全実装 |
| FR-03 | TDD 順序強制 | workflow/verification / common/testing / agent-skills/test-driven-development / L7-implementation.md / helix-gate / helix-sprint / sprint_auto_check.py | FR-TDD-01 | 完全実装 |
| FR-04 | 9 mode 入口判定 | helix-route / route_engine.py / 9 mode workflow 全 10 件 / helix-discovery / helix-recover / helix-refactor / helix-retrofit / helix-research / helix-scrum-agile | FR-9MODE-01 | 完全実装 |
| FR-05 | gate 合成判定 | helix-gate / helix-readiness / helix-push / push_gate.py / gate_check_generator.py / workflow/gate-planning / automation-gate-map.md | FR-GATE-01 | 完全実装 |
| FR-06 | 影響範囲 query | agent-skills/system-design-sizing / workflow/dependency-map / helix-detect / drift_db_diff.py | FR-IMPACT-01 | 部分実装 (5 秒 SLA / impact query CLI は L4 carry) |
| FR-07 | Forward 復帰 event | helix-handover / helix-harness / helix-job / helix-workspace / handover.py / handover_auto_dump.py / add-feature-workflow.md | FR-EVT-01 | 完全実装 |
| FR-08 | 4 artifact / pair freeze | helix-vmodel / helix-test-design-scaffold / vmodel_lint.py / vmodel_pair_freeze.py / test_design_scaffold.py / workflow/requirements-deriver / workflow/review-stage-routing | FR-4ART-01 | 完全実装 |
| FR-09 | 資産 inventory | helix-code / helix-skill / helix-status / helix-asset / skill_catalog.py / code_catalog.py / integration-map.md / asset-mapping.md | FR-INV-01 | 完全実装 (check_functional_registry yaml 化は L4 carry) |
| FR-10 | layer context injection | helix-agent / helix-team / sessionstart-history-injection.sh / userpromptsubmit-context-bundle.sh / workflow/layer-context-injection / layer-context-injection.md | FR-CTX-01 | 完全実装 |
| FR-11 | discrepancy routing | helix-detect / helix-drift-check / workflow/cross-detection / workflow/detection-routing / drift_db_diff.py / cross-detection.md | FR-DRIFT-01 | 完全実装 |
| FR-12 | PLAN dependency / generates | helix-plan / helix-sprint / plan_validator.py / plan_lint.py / plan_dependencies.py / posttooluse-plan-auto-register.sh | FR-PLAN-01 | 完全実装 |
| FR-13 | PLAN 起票レビュー (2026-05-28) | plan_validator.py / pretooluse-agent-guard.sh / posttooluse-plan-auto-register.sh / helix-doctor | FR-GATE-01 + FR-PLAN-01 + FR-CTX-01 | 完全実装 |

---

## §11. L3 FR → 実装資産 逆引き表

| L3 FR-ID | L3 概要 | 実装資産 (代表) | 実装状態 |
|---|---|---|---|
| FR-NSM-01 | NSM 計測・整合スコア機能 | observability-metrics.md / helix-observe / observability_helper.py / automation/observability | 部分実装 |
| FR-GR-01 | Guardrail fail-close 機能 | pretooluse-agent-guard.sh / pretooluse-opus-repo-block.sh / llm_guard.py / integration/agent-cost-design / common/security / workflow/threat-model | 完全実装 |
| FR-TDD-01 | TDD 順序強制機能 | helix-sprint / sprint_auto_check.py / workflow/verification / common/testing / agent-skills/test-driven-development | 完全実装 |
| FR-9MODE-01 | 9 mode 入口判定機能 | helix-route / route_engine.py / discovery-workflow.md / reverse-workflow.md / recovery-workflow.md / refactor-workflow.md | 完全実装 |
| FR-GATE-01 | gate 合成判定機能 | helix-gate / push_gate.py / gate_check_generator.py / automation-gate-map.md / test-perspective-gate.md | 完全実装 |
| FR-IMPACT-01 | 影響範囲 query 機能 | agent-skills/system-design-sizing / workflow/dependency-map / helix-detect | 部分実装 (L4 carry) |
| FR-EVT-01 | Forward 復帰 event 機能 | helix-handover / helix-harness / helix-job / handover.py / posttooluse-helix-job-enqueue.sh | 完全実装 |
| FR-4ART-01 | 4 artifact / pair freeze 監査機能 | helix-vmodel / vmodel_lint.py / vmodel_pair_freeze.py / test_design_scaffold.py / workflow/requirements-deriver | 完全実装 |
| FR-INV-01 | 資産 inventory / density 可視化機能 | helix-skill / helix-code / skill_catalog.py / code_catalog.py / posttooluse-skill-catalog-rebuild.sh | 完全実装 (yaml 化は L4 carry) |
| FR-CTX-01 | layer context injection 機能 | helix-agent / sessionstart-history-injection.sh / userpromptsubmit-context-bundle.sh / workflow/layer-context-injection / layer-context-injection.md | 完全実装 |
| FR-DRIFT-01 | discrepancy routing 機能 | helix-detect / helix-drift-check / drift_db_diff.py / workflow/cross-detection / detection-routing.md | 完全実装 |
| FR-PLAN-01 | PLAN dependency / generates trace 機能 | helix-plan / plan_validator.py / plan_lint.py / plan_dependencies.py / posttooluse-plan-auto-register.sh | 完全実装 |
| FR-DOCTOR-01 | doctor 総合監査機能 | helix-doctor / doctor_plan_checks.py / doctor_summary.py / doctor_recovery_check.py | 完全実装 (check_* 追加は L4 carry) |
| FR-MIGR-01 | schema migration / retrofit 機能 | helix-db / helix-migrate / migrate.py / compatibility_adapter.py / rollback_orchestrator.py | 完全実装 |
| FR-DOCREVIEW-01 | ドキュメント品質レビュー機能 | helix-review / review_output.py / workflow/doc-review / review-stage-routing.md / code-reviewer.md | 完全実装 |
| FR-CHANGEPROP-01 | 変更追跡 + デグレ禁止 ratchet 機能 | workflow/cross-detection / deviation-plan-map.md / vmodel_lint.py | 部分実装 (3 check_* fail-close は L4 carry) |
| FR-FNREG-01 | 機能一覧 SSoT + 自動チェック機能 | **本 doc** (SSoT draft) / integration-map.md / asset-mapping.md | **本 doc で部分実体化** (yaml 化 + check_fr_sot_alignment は L4 carry) |
| FR-GLOSSARY-01 | ドメイン用語 SSoT + 自動チェック機能 | L0 §12 Glossary 19 用語 (skeleton) | 未実装 (Wave D: helix-workflows-glossary-registry.md 起草 + yaml 化 は carry) |

---

## §12. 漏れ整理

### §12.1 逆方向漏れ (実装あり要件なし)

| 資産 | 種別 | 候補理由 | 推奨アクション | 状態 |
|---|---|---|---|---|
| helix-check-claudemd | CLI | DEPRECATED shim、後継 helix-doctor で吸収、FR なし | L1 FR doc の deprecated section に明示 + NFR-OP-01 (auto-deprecation) で扱う | open |
| helix-gate-api-check | CLI | DEPRECATED shim、FR なし | 同上 | open |
| helix-hook | CLI | DEPRECATED shim、FR なし | 同上 | open |
| helix-session-start | CLI | DEPRECATED shim、FR なし | 同上 | open |
| helix-scrum | CLI | helix-discovery legacy alias、SKILL_MAP 明示済。廃止タイミング未定 | 廃止リリース番号確定 (L4 carry) | open |
| helix-test / helix-test-debug | CLI | テスト実行インフラ CLI、直接対応する L1/L3 FR なし | NFR-AV-02 (テスト実行インフラ) 派生として trace 追加 | resolved |
| helix-bats-cleanup | CLI | Bats 一時 file 管理インフラ、FR なし | NFR-OP-02 (月次 audit) 派生として扱う | resolved |
| assets/ 7 file | template | gpt-image / LP 用画像生成テンプレート、HELIX workflow FR なし | skills/design-tools/gpt-image 参照として整理 (scope 外) | resolved |
| folder-structure-review.md | workflow doc | フォルダ構成監査、L1/L3 FR に直接対応なし | FR-INV-01 (inventory/資産登録) 派生として §11 で trace 追加 | resolved |
| helix-debug | CLI | デバッグ専用 CLI、L1/L3 FR で明示要求なし | NFR-OP-03 (運用観測補助) 派生として扱う | resolved |

### §12.2 順方向漏れ (要件あり実装なし)

| L3 FR | 漏れ内容 | 解消アクション | 状態 |
|---|---|---|---|
| FR-FNREG-01 | `cli/config/functional-registry.yaml` 実体 + `helix doctor check_fr_sot_alignment` が L4 carry のみ。専用 skill 不在 | **本 doc が SSoT として機能 (部分実体化)**。L4 で `functional-registry.yaml` + `helix function registry` CLI + `check_fr_sot_alignment` を実装 | **本 doc で部分実体化済** |
| FR-GLOSSARY-01 | `cli/config/glossary.yaml` + `helix doctor check_glossary_coverage` が L4 carry のみ。専用 skill / doc 不在 | L0 §12 Glossary skeleton 19 用語を昇格。`helix-workflows-glossary-registry.md` 起草 (Wave D) + `glossary.yaml` yaml 化 + `check_glossary_coverage` 実装は L4 carry | open (Wave D 候補) |

---

## §13. helix doctor 連携 (L4 carry)

本 doc は §3〜§9 の全資産一覧を機械検査の入力として提供する。L4 フェーズで以下を実体化する。

| check 名 | 対象 | 判定基準 | L4 carry 状態 |
|---|---|---|---|
| `check_functional_registry` | §3〜§9 の ID と実コード id 一覧を突合 | 未登録資産 0 件 | L4 carry |
| `check_fr_sot_alignment` | §10/§11 の L1/L3 FR → 実装資産 mapping | drift ≤ 5% / 未定義 ID 0 件 | L4 carry |
| `check_deprecated_registry` | §12.1 逆方向漏れ の deprecated 資産 | deprecated 明示 + 廃止 milestone 設定 | L4 carry |

詳細は L4 機能設計 doc 起草時に実体化する。

---

> **SSoT 更新ルール**: 本 doc を変更する際は §2 summary カウント、§10/§11 逆引き表の実装状態も同時更新すること。変更粒度が大きい場合 (資産 10 件超追加 / FR 追加) は pmo-sonnet audit 後に commit する。
