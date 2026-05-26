---
doc_id: L14-test-design-helix-workflows-operational
title: "HELIX-workflows 運用テスト設計 (L14 ペア artifact)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L14
pairs_with: L1
canonical_source: HELIX-workflows/helix-process/L14-operation-verification.md
parent_l1_plan: L1-helix-workflows-業務要求plan
related_l1_doc: docs/v2/L1-requirements/helix-workflows-business-requirements.md
---

# HELIX-workflows 運用テスト設計 (L14 ペア artifact)

> **本 doc の位置づけ**: L1 業務要求 (`L1-helix-workflows-業務要求plan` + `docs/v2/L1-requirements/helix-workflows-business-requirements.md`) との V-model **L1↔L14 ペア凍結** artifact。各業務要求 BR-* に対して L14 運用検証フェーズでどう検証するかを設計する。L1 起票時に skeleton として同時起票し、L1 製本 doc 完成時に各 BR-* に対応する OT-* (Operational Test) を埋める。
>
> **status**: draft (skeleton)。L1-業務要求plan §1 Step 3 完了時に同時 detail 化。
>
> **正本**: [HELIX-workflows/helix-process/L14-operation-verification.md](../../../HELIX-workflows/helix-process/L14-operation-verification.md)

## §0 ペア凍結契約

| L1 業務要求 (BR-*) | L14 運用テスト (OT-*) | 検証タイミング | fail 時の措置 |
|---|---|---|---|
| BR-01 dogfooding 稼働 | OT-01 V-model 整合 PLAN 完遂数 (NSM) 測定 | 毎週月曜 | < 50 / month で Guardrail GR-1 fail-close 発火 |
| BR-02 4 artifact retrofit | OT-02 helix doctor warn 数の月次推移 | 毎月末 | warn > 20 で Phase α exit blocker |
| BR-03 drift 解消 | OT-03 detector 新規 drift 件数の週次推移 | 毎週金曜 | 新規 drift > 0 で interrupt 発火 → Reverse normalization mode |
| BR-04 9 mode 入口判定 + Forward 回帰 | OT-04 mode_transition event 登録率 = 9 mode closure / Forward 復帰 event の月次比率 | 毎月末 | 比率 < 95% で routing 設定 audit + closure event hook 修正 |
| BR-05 ペア凍結監査 | OT-05 V-model ペア凍結 coverage = `balance_ratio` 5 pair (L1↔L14, L3↔L12, L4↔L9, L5↔L8, L6↔L7) 各々 ≥ 1.0 の比率 | 毎週金曜 | < 80% で Guardrail GR-1 fail-close 発火 |
| BR-06 影響範囲分析 | OT-06 影響範囲 query 応答時間 (helix.db 4 artifact trace) | 機能改修 trigger 都度 | > 5 秒で query 最適化 + index 設計レビュー |
| BR-07 AI agent 配線 | OT-07 vmodel-semantics.yaml 注入セット利用率 = 各工程 entry 時の mandatory_skills / recommended_commands 注入成功率 | 毎週月曜 | < 90% で helix-context 設定 audit + skill / command catalog rebuild |
| BR-08 採用 project 展開 | OT-08 採用 project の dogfooding 稼働率 (採用 project の V-model 整合 PLAN 完遂数 / 期待値) | 毎月末 | 稼働率 < 50% で onboarding doc + CLI portable 化 carry 起票 |
| BR-09 既存資産整理・マッピング | OT-09 inventory drift 監査 (helix-* CLI / helix.db schema / .helix/ runtime / docs/adr/* と L0 §12.1 Glossary mapping の整合率) | 毎週金曜 | drift 率 > 5% で `helix doctor check_glossary_coverage` (L4 carry) fail-close、設計 doc の implementation_status 列 retrofit 起票 |
| BR-10 既存資産の段階移行・retrofit | OT-10 migration pipeline 残量監査 (V1 PLAN の `is_reference: true` 化率 / 旧 enum 残存件数 / Strangler 段階置換進捗) | 毎週金曜 | 残量 > 期待値 で `helix doctor check_migration_pending` (L4 carry) fail-close、Phase 別残量 dashboard 起票 |
| BR-11 doc 品質継続レビュー | OT-11 doc-reviewer 召喚 coverage 監査 (大規模 doc 改定 commit のうち `helix codex --role doc-reviewer` 召喚 evidence + 判定結果が残された率) | 毎週金曜 | 召喚率 < 95% で `helix doctor check_doc_review_coverage` (L4 carry) fail-close、tl-advisor / doc-reviewer 責務分離違反 sample audit + retrofit carry 起票 |
| BR-12 デグレ禁止ガードレール | OT-12 デグレ件数監査 (上流 ID 追加 commit で下流対応不在 件数 / balance_ratio regression 件数 / 上流↔下流 trace 切れ件数) | 毎日 (pre-commit + CI hook 連動)、週次集計は金曜 | 違反 > 0 件で `helix doctor check_upstream_downstream_alignment` / `check_balance_ratio_regression` / `check_id_reference_completeness` (L4 carry、3 件) fail-close、Ratchet baseline 後戻り検出時 immediate alert + commit reject |

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 運用テスト設計の詳細 (Step 3 で埋める)

### OT-01: V-model 整合 PLAN 完遂数 (NSM 測定)

- **対象 BR**: BR-01 dogfooding 稼働
- **検証内容**: 過去 4 週間に **V-model 整合** (process_layer + parent_process + pairs_test_design field 揃い、kind enum 一致、G ゲート通過記録あり) で完遂した PLAN 数を helix.db.plan_registry から SQL 集計
- **測定式**: `SELECT COUNT(*) FROM plan_registry WHERE status='complete' AND process_layer IS NOT NULL AND completed_at >= date('now', '-28 days')` (V5 framework 完遂後の schema 前提)
- **target**: ≥ 50 / month (NSM、L0 §5.1)
- **fail 措置**: < 50 で Guardrail GR-1 fail-close 発火、Incident mode に切替えて根本原因分析

### OT-02: 4 artifact 双方向 trace warn 数の月次推移

- **対象 BR**: BR-02 4 artifact retrofit
- **検証内容**: `helix doctor --json` の warn 数のうち 4 artifact trace 関連 warn (id_pattern: `axis-04-artifact-*`) を月次計測
- **測定式**: `helix doctor --json | jq '.warns[] | select(.id | startswith("axis-04-artifact-")) | .id' | wc -l`
- **target**: Phase α 完了時 ≤ 20 (L0 §5.4 KGI)
- **fail 措置**: > 20 で Phase α exit blocker、retrofit PLAN を 追加起票

### OT-03: drift detector 新規発生件数の週次推移

- **対象 BR**: BR-03 drift 解消
- **検証内容**: 過去 7 日間で新規発生した drift 件数を helix.db.discrepancy_log から週次集計
- **測定式**: `SELECT COUNT(*) FROM discrepancy_log WHERE severity IN ('P0', 'P1') AND created_at >= date('now', '-7 days') AND status='new'` (V5 framework 完遂後の schema 前提)
- **target**: 0 件 / week (定常運用維持)
- **fail 措置**: > 0 で interrupt 発火 → 重大度 P0 は Recovery mode、P1 は Reverse normalization mode に切替

### OT-04: 9 mode closure → Forward 復帰 event 登録率

- **対象 BR**: BR-04 9 mode 入口判定 + Forward 回帰
- **検証内容**: 過去 1 ヶ月の 9 mode closure 件数に対する Forward 復帰 event (`helix.db.mode_transition` table 登録) の比率
- **測定式**: `SELECT (SELECT COUNT(*) FROM mode_transition WHERE created_at >= date('now', '-30 days')) * 1.0 / (SELECT COUNT(*) FROM mode_closure_log WHERE closed_at >= date('now', '-30 days')) AS forward_return_ratio` (V5 framework 完遂後)
- **target**: ≥ 95% (L0 §5.3 Cascade KPI)
- **fail 措置**: < 95% で route_engine 設定 audit + 各 mode の closure event hook 不在を検出 + PLAN 追加起票

### OT-05: V-model ペア凍結 coverage (5 pair の `balance_ratio`)

- **対象 BR**: BR-05 ペア凍結監査
- **検証内容**: 5 ペア (L1↔L14 運用 / L3↔L12 受入 / L4↔L9 総合 / L5↔L8 結合 / L6↔L7 単体) について `balance_ratio = test_count / design_count` を週次計測、各 pair で ≥ 1.0 を満たす比率
- **測定式**: `SELECT design_layer, test_layer, balance_ratio FROM pair_volume_balance WHERE balance_ratio >= 1.0` (V5 framework 完遂後の view)
- **target**: ≥ 80% (L0 §5.2 GR-1 Guardrail、fail-close)
- **fail 措置**: < 80% で Guardrail GR-1 fail-close 発火、不足ペアの追加テスト起票 (L7/L8/L9 sprint への carry)

### OT-06: 影響範囲 query 応答時間

- **対象 BR**: BR-06 影響範囲分析
- **検証内容**: 機能改修 trigger 時に helix.db 4 artifact trace (design ↔ test_design ↔ impl ↔ test_code) から過去変更 trace を retrieve する query 応答時間
- **測定式**: `time helix code impact-range --plan-id <id>` (V5 framework 完遂後の CLI)、計測サンプル ≥ 10 回 / 月の中央値
- **target**: ≤ 5 秒 (L0 §5.3 Cascade KPI)
- **fail 措置**: > 5 秒で helix.db schema index 設計レビュー + query 最適化、coverage_link / transition_history table の partition 検討

### OT-07: vmodel-semantics.yaml 注入セット利用率

- **対象 BR**: BR-07 AI agent 配線
- **検証内容**: 各工程 (L0-L14) entry 時に `helix-context` が `mandatory_skills` / `recommended_commands` / `mandatory_agents` を機械注入した成功率 (注入 attempt 数 / 工程 entry 件数)
- **測定式**: `SELECT (SELECT COUNT(*) FROM injection_log WHERE status='success' AND created_at >= date('now', '-7 days')) * 1.0 / (SELECT COUNT(*) FROM phase_entry_log WHERE entered_at >= date('now', '-7 days')) AS injection_rate` (V5 framework 完遂後)
- **target**: ≥ 90%
- **fail 措置**: < 90% で `helix-context` 設定 audit + skill_catalog / command_catalog rebuild + vmodel-semantics.yaml drift 検証

### OT-12: デグレ件数監査 (BR-12 由来、2026-05-26 ユーザー指摘反映)

- **対象 BR**: BR-12 デグレ禁止ガードレール業務 (変更追跡 + ratchet 機構)
- **計測内容**: (1) 上流 ID (BR-* / FR-* / NFR-*) 追加 commit で下流対応 ID 不在の件数 (2) balance_ratio < 1.0 regression 件数 (3) 上流↔下流 trace 切れ件数 (4) Ratchet baseline 後戻り件数
- **頻度**: pre-commit + CI hook 連動 (immediate)、週次集計は毎週金曜
- **target**: 全 4 項目 = 0 件 (Ratchet 機構: 過去最小値より下回らない)
- **検証手段**: `helix doctor --check-changeprop` (L4 carry、新設) で 3 軸 check 一括実行、`.helix/audit/changeprop-violations.yaml` (L4 carry) に違反 log 出力、`.helix/audit/balance-ratio-baseline.yaml` (L4 carry) で Ratchet baseline 管理
- **異常時アクション**: 違反 > 0 件で immediate commit reject (pre-commit / CI hook)、Ratchet baseline 後戻り検出時は alert + commit block、deferred-findings.yaml 登録経由のみで破壊的変更通過

### OT-11: doc-reviewer 召喚 coverage 監査 (BR-11 由来、2026-05-26 ユーザー指摘反映)

- **対象 BR**: BR-11 doc 品質継続レビュー業務
- **計測内容**: 大規模 doc 改定 (~500 行+) commit / G0.5・G1・G3・G7 ゲート evidence のうち、`helix codex --role doc-reviewer` 召喚 evidence + 判定結果 (approve / conditional_approve / blocked) が commit message / final report / 会話 history のいずれかに残された率
- **頻度**: 毎週金曜
- **target**: 召喚 coverage ≥ 95%
- **検証手段**: `helix doctor check_doc_review_coverage` (L4 carry、新設) で 直近 30 commit を grep + 召喚率集計、tl-advisor / doc-reviewer 責務分離違反 (技術判断のみで doc 品質視点が漏れている commit) を sample audit
- **異常時アクション**: coverage < 95% で fail-close、未召喚 doc 改定 commit を warn 出力 + retrofit doc-review 召喚 carry 起票、責務分離違反 commit は postmortem 起票

### OT-09: 既存資産 inventory drift 監査 (BR-09 由来、2026-05-26 ユーザー指摘反映)

- **対象 BR**: BR-09 既存資産整理・マッピング業務
- **計測内容**: HELIX-workflows 既存資産 (helix-* CLI 81 件 / helix.db 50+ table + view 1 / cli/config/*.yaml 5 件 / .helix/* runtime / docs/adr/* 41 件 / cli/templates/plan/v2/* 15 件 / .claude/agents/*.md 19 件) と L0 §12.1 Glossary mapping の **drift 率**
- **頻度**: 毎週金曜
- **target**: drift 率 ≤ 5%
- **検証手段**: `helix doctor check_glossary_coverage` (L4 carry、新設) で 5 列充足率 + L0 §12.1 19 用語の `implementation_status` 列と実体の整合性を機械判定
- **異常時アクション**: drift > 5% で fail-close、設計 doc の implementation_status 列 retrofit 起票 (`feedback_memory_verify_before_act` 整合)

### OT-10: migration pipeline 残量監査 (BR-10 由来、2026-05-26 ユーザー指摘反映)

- **対象 BR**: BR-10 既存資産の段階移行・retrofit 業務
- **計測内容**: V1 → V2 / 旧 process L1-L11 → 新 L0-L14 / 旧 enum → 新 enum の段階 migration 残量
- **頻度**: 毎週金曜
- **target**: Phase α 終了時 V1 PLAN `is_reference: true` 化率 100% / Phase β 終了時 旧 enum 残存 0 / Phase γ 終了時 Strangler 段階置換完了
- **検証手段**: `helix doctor check_migration_pending` (L4 carry、新設) で Phase 別残量 + Strangler Fig Pattern 段階置換進捗を JSON 出力、Phase 別 dashboard 生成
- **異常時アクション**: 残量 > 期待値 で fail-close、Phase 別残量 dashboard 起票 + L4 基本設計の migration pipeline 再凍結

### OT-08: 採用 project の dogfooding 稼働率

- **対象 BR**: BR-08 採用 project 展開
- **検証内容**: HELIX-workflows V2 採用 project の V-model 整合 PLAN 完遂数 / 期待値 (各 project の OT-01 相当を集約)
- **測定式**: project 別 OT-01 計測値を集約 (採用 project は HELIX-workflows portable package を取り込んだ remote project、各 project 末端で `helix budget status --json` 経由で報告)
- **target**: 採用 project 稼働率 ≥ 50% (Phase β 完了条件、L0 §5.4 KGI)
- **fail 措置**: < 50% で onboarding doc 改善 + CLI portable 化 carry 起票 + 採用 project hearing で blocker 抽出

## §2 運用テスト実行体制

- **頻度**: 週次 (OT-01 + OT-03 + OT-05 + OT-07) / 月次 (OT-02 + OT-04 + OT-08) / トリガ都度 (OT-06)
- **実行者**: 自動 (helix-readiness CLI + cron) で計測、PM がレビュー
- **記録先**: `docs/v2/L14-test-results/<YYYY-MM>-operational-test-result.md` (L14 工程で生成)
- **postmortem 起票条件**: OT-* のいずれかが fail → 月次 postmortem に集約

## §3 V-model L1↔L14 ペア凍結確認

- L1 業務要求 doc (`docs/v2/L1-requirements/helix-workflows-business-requirements.md`) の各 BR-* と本 doc の OT-* が **1:1 対応** していることを確認
- 対応欠落 (BR-* に対応する OT-* がない、または OT-* に対応する BR-* がない) は **G1 ゲート blocker**
- `helix gate G1` で機械検証 (V5 framework 完遂後)

## §4 関連 doc

- **L1 ペア相手**: [L1-helix-workflows-業務要求plan](../../plans/L1/L1-helix-workflows-業務要求plan.md)
- **L1 製本 doc** (Step 3 で起票): [helix-workflows-business-requirements.md](../L1-requirements/helix-workflows-business-requirements.md)
- **L14 工程 doc**: [docs/v2/process/L14-operations-and-improvement.md](../process/L14-operations-and-improvement.md)
- **HELIX-workflows L14 正本**: [HELIX-workflows/helix-process/L14-operation-verification.md](../../../HELIX-workflows/helix-process/L14-operation-verification.md)
- **L0 概念 (NSM / Guardrail / Cascade KPI)**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md) §5

## §5 carry / 既知の不足

- **L14-test-design template skeleton 不在 carry**: 本 doc は L1-業務要求plan 起票時に手動作成。`cli/templates/plan/v2/` に L14-test-design 用 template (各 OT-* の SQL / 測定式 / fail 措置 フォーマット定型化) を整備すると次 PLAN 起票時に作業効率化。L1-helix-workflows-業務要求plan §1 Step 3 完了時に template 化 carry を別 PLAN で起票候補。
- **helix.db schema 前提**: §1 OT-01〜OT-08 の SQL は V5 framework 完遂後の `plan_registry` / `discrepancy_log` / `mode_transition` / `mode_closure_log` / `pair_volume_balance` view / `injection_log` / `phase_entry_log` 等の schema を前提とする。schema 確定前は手動計測 (helix doctor 出力を script で集計) で代替。L1-技術要求plan §4 L1-IN-10 (helix.db V-model DB schema) で schema 詳細を確定。
- **OT-04〜OT-08 (2026-05-26 tl-advisor G1 adversarial P0 #1 反映)**: 当初 skeleton では OT-01〜OT-03 のみ (BR 8 / OT 3 で量閉じ違反 `balance_ratio = 0.375`)、tl-advisor 指摘で OT-04〜OT-08 を追加して BR-* と 1:1 対応 (balance_ratio = 1.0) を確立。helix.db schema 確定前は手動計測 fallback で運用。
- **採用 project 計測の仕組み (OT-08)**: 採用 project の OT-01 相当を集約する portable 計測 pipeline は Phase β 完了条件。Phase α では HELIX 自身のみ計測。
