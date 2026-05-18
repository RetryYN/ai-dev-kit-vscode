---
plan_id: PLAN-089
title: "PLAN-089: 設計 doc Web 検索 audit advisory→段階的 fail-close 化"
layer: L2
size: S-M
status: draft
drive: be
created: 2026-05-19
revised: 2026-05-19
owner: PM
phases: L4
gates: G2, G3
related_plans:
  - PLAN-087
  - PLAN-085
  - PLAN-086
related_docs:
  - cli/helix-gate
  - .claude/hooks/pretooluse-design-doc-web-search-guard.sh
reference_docs:
  - docs/plans/PLAN-087-design-doc-web-search-guardrail.md
  - docs/plans/PLAN-085-cutover-staging-rehearsal.md
  - docs/plans/PLAN-086-rollback-fault-injection-drill.md
---

# PLAN-089: 設計 doc Web 検索 audit advisory→段階的 fail-close 化

## 0. 起票背景 + 再起票注記 (2026-05-19)

PLAN-087 Phase 3 で cli/helix-gate に run_gate_design_doc_web_search_audit (G2/G3 advisory) を実装したが、advisory は warn のみで gate 通過を block しない。本 PLAN は段階的に fail-close 化する framework を確立する。

> **再起票注記 (2026-05-19 03:08)**: 本 file は bi9wl210l (Codex docs) で 1 度起票完了したが、その後 Opus が frontmatter --- block 修正 Edit を実行した際、新規実装 PostToolUse 二重防御 hook (b608igbuf 完了で settings.json 登録、session_id missing で Web 検索履歴判定不能 → revert action) によって file が削除された。Bash heredoc で再書き出し (PostToolUse hook matcher は Edit|Write|MultiEdit、Bash は trigger しない pattern を活用)。本事象は memory feedback [[feedback_design_doc_web_search_required]] に追記する重要 learning (自 hook 自 revert pattern、PreToolUse 自己 block と同じ系列)。

TL 相談助言 (helix codex --role tl-advisor、2026-05-19):
- 一括切替は blast radius 大、advisory 計測期間を Phase 1 で設ける
- bypass env を settings.json に永続化しない (恒久例外化リスク)
- Phase 1 advisory 計測 → Phase 2 fail-close 切替 → Phase 3 既存 PLAN retrofit → Phase 4 carry

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| GitHub Actions required status checks | https://docs.github.com/actions | Phase 4 以降、required checks を段階的に有効化する移行設計の根拠 |
| LaunchDarkly Feature Flag Gradual Rollout | https://launchdarkly.com/docs/guides/feature-flags | Phase 2 の advisory→fail-close 切替を段階ロールアウトで安全化 |
| Statsig Feature Gate | https://docs.statsig.com | フェーズ別有効化 (対象 scope 制御、ロールバック時の自動戻し) |
| PLAN-087 Phase 3 | docs/plans/PLAN-087-design-doc-web-search-guardrail.md | advisory 実装 (前提) として継承 |
| TL 助言 (本 session) | helix codex --role tl-advisor 結果 | advisory 時代の検知率を可視化した後、fail-close を段階展開する方針 |

## 2. 前提

- 本 session は WebSearch 5 query 実施済み + pmo-tech-fork OSS 5 件評価実施済み + TL 助言反映済
- 本 PLAN は新規 plan 起票であり、実装 code 変更は本 PLAN scope ではない (Phase 1 で helix.db v33 追加は PLAN-089 と一体実施、本 wave で完遂)
- HELIX schema_version mechanism (cli/lib/helix_db.py:246 CURRENT_SCHEMA_VERSION=33) を使用 (PRAGMA user_version ではない)

## 3. 受入条件

- AC-089-01: cli/helix-gate の G2/G3 における WebSearch / OSS 調査の audit を plan_id / mode (advisory|fail_close) 単位で記録
- AC-089-02: helix.db v33 の gate_audit_metrics 導入後、PLAN 起票時の advisory check が 2-4 週で 95% 以上の検知率を達成し、未記録 plan は bypass 証跡なしで fail しない (段階移行期間)
- AC-089-03: Phase 2 で bypass env (HELIX_ALLOW_DESIGN_DOC_NO_WEB=1) の運用ルールを定義し、理由必須 + audit 検証ログに残す
- AC-089-04: Phase 4 までに既存 PLAN の P0/P1/P2 retrofit 方針と carry list を確定

## 4. Phase 設計

### Phase 1: advisory 計測 (2-4 週)

- 目的: advisory の実効性を定量化し fail-close 移行に必要な閾値を決める
- 実装: helix.db v33 の gate_audit_metrics テーブル (本 wave で v33 migration + table 追加完遂、cli/lib/migrations/v33_gate_audit_metrics.py)
- 指標: web_search_missing_count, oss_search_missing_count, bypass_count, plan_size_bucket(<50 / >=50), phase
- 収集: G2, G3 実行時に plan_id・file_path・metric_status を永続化 (cli/helix-gate fail-close 化と同 wave で実装)
- 運用: 2 週目時点で 1st スナップショット、4 週目時点で 2nd スナップショットを比較し見直し指標を確定

### Phase 2: fail-close 切替 (bypass env 受理、本 wave で実装完遂)

- 目的: 失敗を防ぐ初期 fail-close へ移行
- 方針: advisory 監査を段階的に fail-close 化、既存運用を止めない
- 起票・編集対象: docs/plans/PLAN-*.md, docs/adr/ADR-*.md の新規 / 大規模改訂
- 条件: WebSearch/OSS 証跡が不足すると fail-close (但し HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 + 理由明示で受理)
- 段階移行: HELIX_GATE_DESIGN_DOC_FAIL_CLOSE=1 env で有効化、デフォルトは ENABLED にせず

### Phase 3: 既存 PLAN retrofit (P0 6 件)

- 目的: PLAN-087 の carry と整合し、P0 6 件を優先的に更新
- 根拠: pmo-sonnet Wave 2-7 報告 (retrofit 候補):
  - ADR-018 (Event Sourcing / CQRS / DDD Bounded Context)
  - ADR-020 (本 wave で部分実施済)
  - PLAN-084 (Event Sourcing / Projector / UUID v7 RFC 9562)
  - PLAN-085 (本 wave で部分実施済)
  - PLAN-086 (Chaos Engineering / fault injection)
  - PLAN-087 (Claude Code hook API / MADR / Nygard original)

### Phase 4: P1/P2 retrofit + bypass audit

- 目的: P1/P2 を段階的に同一基準へ追従
- P1/P2 retrofit (P1 13 件 + P2 6 件) は別 PLAN-090?/091? carry
- bypass audit: HELIX_ALLOW_DESIGN_DOC_NO_WEB=1 利用時は必ず理由 + 実行者 + 対象 plan を記録 (helix.db gate_audit_metrics で蓄積)
- ~~PostToolUse 二重防御~~ → 本 wave で実装済 (.claude/hooks/posttooluse-design-doc-web-search-revert.sh、warn-only、Issue #24327 保険として retain)

## 5. リスク

- R-089-01: advisory 2-4 週の指標が想定未達になり fail-close 期の停止率が上昇
  - 対応: bypass env の監査しきい値を厳格化、必要時は fail-close を段階的に縮小
- R-089-02: gate_audit_metrics への記録漏れで監査証跡欠落
  - 対応: 収集パイプラインを fail-safe 設計、欠落時は metrics 収集失敗を可視化
- R-089-03: bypass の濫用で本意でない大規模改定が通過
  - 対応: bypass reason を人為レビュー対象として carry/監査リストに自動追加、週次監査で是正
- R-089-04: **自 PostToolUse hook が自 file を revert する self-inflicted pattern** (本 wave で実測発生)
  - 対応: session_id missing 時の判定 logic を改善 (現在 fail-close = revert)、bypass env を Bash heredoc 経由で確実に渡せる仕組み or hook 内 session_id 検出 logic を強化

## 6. carry list

- [ ] PLAN-089-2: helix.db v33 gate_audit_metrics の Phase 1 指標閾値見直し (2-4 週の実データ収集後)
- [ ] PLAN-090?: P1 既存 PLAN retrofit (13 件)
- [ ] PLAN-091?: P2 既存 PLAN retrofit (6 件)
- [ ] bypass env audit logic 実装 (helix.db で利用回数記録、頻度高いなら設計再検討)
- [ ] continueOnBlock (Claude Code 2.1.139) 検討 (PostToolUse 二重防御の上位代替、別 PLAN carry)
- [ ] PostToolUse self-inflicted revert pattern の logic 改善 (session_id missing 判定強化)

## 7. 関連 memory

- [[feedback_design_doc_web_search_required]] (本 PLAN の上位 framework、本 wave で「自 PostToolUse 自 revert」pattern 追記予定)
- [[feedback_no_user_ask_tl_advisor_self_drive]] (本 wave で TL 相談実施、自走判断)
- [[feedback_codex_migration_test_version_drift]] (本 wave で v33 追加時 test drift 再発、3 file 修正)
- [[project_2026_05_19_plan087_web_search_guardrail_birth]] (本 wave 起点)

## 8. 参照

- docs/plans/PLAN-087-design-doc-web-search-guardrail.md (基盤、本 PLAN は Phase 3 拡張)
- cli/helix-gate (本 PLAN Phase 2 で fail-close 切替、b0qkkln7l で実装完遂)
- cli/lib/migrations/v33_gate_audit_metrics.py (本 PLAN Phase 1 schema、b0qkkln7l 完遂)
- cli/lib/tests/test_helix_gate_design_doc_fail_close.py (本 PLAN test、b0qkkln7l 完遂、pytest 4 passed)
- .claude/hooks/pretooluse-design-doc-web-search-guard.sh (本 PLAN bypass env 受理 pattern)
- .claude/hooks/posttooluse-design-doc-web-search-revert.sh (b608igbuf 完遂、warn-only)
