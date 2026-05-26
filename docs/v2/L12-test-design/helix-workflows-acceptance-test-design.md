---
doc_id: L12-test-design-helix-workflows-acceptance
title: "HELIX-workflows 受入テスト設計 (L12 ペア artifact、L3 3 PLAN 共通)"
status: draft
created: 2026-05-26
owner: PM
process_layer: L12
pairs_with: L3
canonical_source: HELIX-workflows/helix-process/L12-deployment.md
parent_l3_plans:
  - L3-helix-workflows-業務要件plan
  - L3-helix-workflows-機能要件plan
  - L3-helix-workflows-非機能要件plan
related_l3_docs:
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-nfr-detail.md
---

# HELIX-workflows 受入テスト設計 (L12 ペア artifact)

> **本 doc の位置づけ**: L3 要件定義 3 PLAN (業務要件 / 機能要件 / 非機能要件) との V-model **L3↔L12 ペア凍結** artifact。各要件 (BR-* / FR-* / NFR-*) に対して L12 デプロイ後の受入テスト (AC-*) を設計する。L3 3 PLAN 起票完遂 (2026-05-26) で §1-§3 すべて detail 化、57 AC (BR 12 + FR 16 + NFR 29) で balance_ratio ≥ 1.0 (本 session BR-09/10/11/12 + FR-DOCREVIEW-01 + FR-CHANGEPROP-01 + NFR-OP-06/07/08 + NFR-MG-04 追加で 47→57 件)。
>
> **status**: draft (G3 evidence 完成、§1 業務系 AC-BR-01〜12 + §2 機能系 AC-FR-01〜16 + §3 非機能系 AC-NFR 29 件すべて detail 化済 2026-05-26、BR-12 ratchet 機構準拠で 本 session BR-09/10/11/12 追従済)。
>
> **正本**: [HELIX-workflows/helix-process/L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md)

## §0 ペア凍結契約

L3 3 PLAN それぞれに対応する AC-* を 3 section で構成:

| L3 PLAN | L3 要件 ID prefix | L12 AC ID prefix | 本 doc 該当 section | 起票 timing |
|---|---|---|---|---|
| L3-業務要件plan | BR-* (L1 BR を確定版に詳細化) | AC-BR-* | §1 業務系受入テスト | Phase E.A.4 (本 turn) |
| L3-機能要件plan | FR-* (L1 FR + TR を統合詳細化) | AC-FR-* | §2 機能系受入テスト | Phase E.B (Codex SE) |
| L3-非機能要件plan | NFR-* (L1 NFR IPA グレード値確定) | AC-NFR-* | §3 非機能系受入テスト | Phase E.B (Codex SE) |

**量閉じ性 (Chargaff's rule、L0 §5.3)**: 各 section で対応要件と AC が `balance_ratio = AC_count / requirement_count ≥ 1.0` を満たすことを G3 機械検証。

> **SSoT 参照** (2026-05-26 doc-system-architect retrofit): ユビキタス言語 = [L0 §12 Glossary](../L0-helix-workflows/concept.md) / 業界標準整合 = §13 / Bounded Context = §14。本 doc は L0 §12-§14 を parent_doc reference とし、用語独自定義は行わない (anti-corruption layer)。

## §1 業務系受入テスト (BR-* ↔ AC-BR-*、Phase E.A で確定)

### AC-BR-01: dogfooding 稼働 受入テスト

- **対象 BR**: BR-01 dogfooding 稼働 (L1 業務要求 doc / L3 業務要件 doc §1.1)
- **デプロイ後検証内容**: HELIX-workflows V2 採用後 1 ヶ月時点で NSM (V-model 整合 PLAN 完遂数) を計測、初期目標 ≥ 50 / month 達成を確認
- **受入基準**: NSM ≥ 50 / month AND Guardrail GR-1 fail-close 動作確認 (発火条件: < 50 で fail-close)
- **検証 step**: (1) helix.db.plan_registry から月次 V-model 整合 PLAN 完遂数を SQL 集計 → (2) NSM ≥ 50 を確認 → (3) 意図的に < 50 のシナリオで Guardrail GR-1 fail-close 発火を確認

### AC-BR-02: 4 artifact retrofit 受入テスト

- **対象 BR**: BR-02 4 artifact retrofit
- **デプロイ後検証内容**: 既存 PLAN 324 件に対する retrofit 完遂率を月次計測、warn 数の月次推移を確認
- **受入基準**: Phase α 完了時点で `helix doctor warn ≤ 20` AND retrofit 完遂率 ≥ 90%
- **検証 step**: (1) `helix doctor --json | jq` で warn 数取得 → (2) 月次推移を grafana / SQL view で確認 → (3) Phase α exit blocker (warn > 20) で fail-close

### AC-BR-03: drift 解消 受入テスト

- **対象 BR**: BR-03 drift 解消
- **デプロイ後検証内容**: 週次 detector 検出 → Reverse normalization mode 自動切替の動作確認、新規 drift 0 件 / week 維持
- **受入基準**: 検出 → normalization 完了時間 ≤ 24 時間 AND 新規 drift 件数 = 0 / week (定常運用)
- **検証 step**: (1) 意図的に drift を発生させる → (2) 週次 detector が検出 → (3) Reverse normalization mode が自動起動 → (4) 24 時間以内に normalization 完遂を確認

### AC-BR-04: 9 mode → Forward 回帰 受入テスト

- **対象 BR**: BR-04 9 mode 入口判定 + Forward 回帰
- **デプロイ後検証内容**: 9 mode (Scrum / Discovery / Reverse / Incident / Add-feature / Refactor / Retrofit / Research / Recovery) 各々の入口判定 + closure → Forward 復帰 event 登録動作を確認
- **受入基準**: 各 mode で closure event → helix.db.mode_transition table 登録成功率 ≥ 95%
- **検証 step**: (1) 9 mode それぞれを意図的に起動 → (2) closure event 発火 → (3) mode_transition table に row 追加確認 → (4) Forward L1/L3/L4-L6/L7 への接続確認

### AC-BR-05: ペア凍結監査 受入テスト

- **対象 BR**: BR-05 ペア凍結監査
- **デプロイ後検証内容**: V-model 5 pair (L1↔L14, L3↔L12, L4↔L9, L5↔L8, L6↔L7) の `balance_ratio` 週次計測
- **受入基準**: 5 pair 各々で `balance_ratio ≥ 1.0` を満たす比率 ≥ 80% (Guardrail GR-1 閾値)
- **検証 step**: (1) `pair_volume_balance` view query → (2) 5 pair の balance_ratio 確認 → (3) 1.0 未満 pair で fail-close 動作確認

### AC-BR-06: 影響範囲分析 受入テスト

- **対象 BR**: BR-06 影響範囲分析
- **デプロイ後検証内容**: 機能改修 trigger → 過去 trace retrieve 応答時間 ≤ 5 秒 を確認
- **受入基準**: 影響範囲 query 応答時間 中央値 ≤ 5 秒 (サンプル ≥ 10 回 / 月)
- **検証 step**: (1) 異なる規模の機能改修を 10 件以上 trigger → (2) `helix code impact-range` 応答時間計測 → (3) 中央値 ≤ 5 秒確認

### AC-BR-07: AI agent 配線 受入テスト

- **対象 BR**: BR-07 AI agent 配線
- **デプロイ後検証内容**: 各工程 entry 時に vmodel-semantics.yaml 注入セット (mandatory_skills / commands / agents) の自動注入動作確認
- **受入基準**: 注入成功率 ≥ 90% AND AI 判断削減率 ≥ 70% (L0 §5.3 Cascade KPI)
- **検証 step**: (1) 各 L 工程 (L0-L14) を順次 entry → (2) helix-context が注入セット読込 → (3) injection_log で成功率計測 → (4) 注入後の AI 判断 vs 機械判定の比率測定

### AC-BR-08: 採用 project 展開 受入テスト

- **対象 BR**: BR-08 採用 project 展開
- **デプロイ後検証内容**: HELIX-workflows portable package が他 project に取込可能 + 各 project で dogfooding 稼働率 計測
- **受入基準**: 採用 project の OT-01 相当稼働率 ≥ 50% (Phase β 完了条件)
- **検証 step**: (1) HELIX-workflows V2 portable package 化 (carry) → (2) 採用候補 project に取込 → (3) 各 project で `helix budget status --json` 経由で稼働率報告 → (4) 集約 ≥ 50% 確認

### AC-BR-09: 既存資産整理・マッピング 受入テスト (2026-05-26 ユーザー指摘反映、BR-RULE-09 由来)

- **対象 BR**: BR-09 既存資産整理・マッピング業務
- **デプロイ後検証内容**: 設計 doc 内の「対応 CLI / file path / schema field / table / view / config」主張に対し `implementation_status` 列 (installed / partial / L4-carry / not-implemented) が **必須充足**、`helix doctor check_glossary_coverage` (L4 carry) で drift 検出
- **受入基準**: L0 §12.1 Glossary 19 用語 + L1 §10 業務 entity 12 件 + 後続 L3/L4 設計 doc 全件で `implementation_status` 列 = 5 列 (CLI / file / schema / grep / status) 充足、inventory drift 率 ≤ 5% (毎週金曜)
- **検証 step**: (1) L0 §12.1 で機械判定 grep (5 列充足チェック) → (2) L1 §10 で entity ↔ L0 Glossary term 列で 1:1 対応確認 → (3) L3/L4 doc に implementation_status 列ありを sample audit → (4) 不足 doc を carry 起票
- **机上宣言禁止**: [[feedback_memory_verify_before_act]] verify-before-act 整合

### AC-BR-10: 既存資産の段階移行・retrofit 受入テスト (2026-05-26 ユーザー指摘反映、BR-RULE-10 由来)

- **対象 BR**: BR-10 既存資産の段階移行・retrofit 業務
- **デプロイ後検証内容**: V1 → V2 / 旧 process L1-L11 → 新 L0-L14 / 旧 enum → 新 enum の **段階 migration pipeline** が Strangler Fig Pattern (Fowler 2004) ベースで凍結、`helix doctor check_migration_pending` (L4 carry) で残量管理
- **受入基準**: V1 PLAN 223 件の `is_reference: true` 化率 100%、旧 enum (旧 G2/G3/G4 / 旧 layer L1-L11) 残存 = 0、Phase 別残量 dashboard で Phase α/β/γ kill criteria 満たすこと
- **検証 step**: (1) `find docs/plans/ -name '*.md' | xargs grep -l 'is_reference: true' | wc -l` で V1 PLAN 移行率 → (2) `git grep -E 'G[2-9]|G14' --` で旧 enum 残存 → (3) frontmatter field migration (例: kind=impl→process_layer=L7) を機械検証 → (4) ADR snapshot 後追い起票件数を audit → (5) Phase 別残量と kill criteria 突合

### AC-BR-11: doc 品質継続レビュー 受入テスト (2026-05-26 ユーザー指摘反映、BR-RULE-11 由来)

- **対象 BR**: BR-11 doc 品質継続レビュー業務
- **デプロイ後検証内容**: 大規模 doc 改定 / G ゲート evidence / V-model 4 artifact pair freeze 前で **doc-reviewer 専用 role (Codex gpt-5.5 high)** が召喚され、4 視点 (Correctness / Completeness / Consistency / Clarity) + 業界標準 (Diátaxis / arc42 / ISO/IEC/IEEE 26515:2018) + HELIX V-model 量閉じ性 / implementation_status 列必須を統合検査して判定 (approve / conditional_approve / blocked) を返す
- **受入基準**: 該当 doc 改定の commit message / final report / 会話 history のいずれかに `helix codex --role doc-reviewer` 召喚 evidence + 判定結果が記載されている率 ≥ 95% (`helix doctor check_doc_review_coverage` (L4 carry) で機械監査)
- **検証 step**: (1) 直近 30 commit のうち doc 改定 (~500 行+) 該当 commit を抽出 → (2) 各 commit message + 会話 history で doc-reviewer 召喚 evidence を grep → (3) 召喚率 + 判定の分布 (approve / conditional / blocked) を集計 → (4) 召喚不在 commit を warn 出力 + retrofit 起票 → (5) tl-advisor (技術判断) / doc-reviewer (doc 品質) の責務分離が遵守されているか sample audit

### AC-BR-12: デグレ禁止ガードレール 受入テスト (2026-05-26 BR-RULE-12 由来、新規追加)

- **対象 BR**: BR-12 デグレ禁止ガードレール業務 (変更追跡 + ratchet 機構)
- **デプロイ後検証内容**: 上流 ID (BR-* / FR-* / NFR-*) 追加・更新・削除 commit で下流対応 ID (BR-RULE-* / FR-* / NFR-* / AC-* / OT-*) が同 commit / 直前後 N commit (default N=3) 以内に存在するか + balance_ratio regression + 上流↔下流 trace 切れ を `helix doctor check_*` 3 件 (`check_upstream_downstream_alignment` + `check_balance_ratio_regression` + `check_id_reference_completeness`) で機械強制 (pre-commit + CI hook 統合)
- **受入基準**: (1) 違反 commit が hook で block されること (2) balance_ratio 過去最小値より下回ったら fail-close (Ratchet 機構) (3) 上流↔下流 alignment 違反率 = 0% (`.helix/audit/changeprop-violations.yaml` で 0 件維持) (4) Hyrum's Law ベースの破壊的変更が deferred-findings.yaml 登録必須
- **検証 step**: (1) sample commit で BR-* 追加 (下流対応なし) → block 確認 → (2) sample commit で balance_ratio 下げ → block 確認 → (3) sample commit で上流 ID delete → trace 切れ警告 → (4) `.helix/audit/balance-ratio-baseline.yaml` (L4 carry) との突合確認 → (5) deferred-findings 登録時の例外 path 確認

## §2 機能系受入テスト (FR-* ↔ AC-FR-*、Phase E.B Codex SE bxwlot2t6 PROPOSE 反映 2026-05-26)

L3 [機能要件 doc](../L3-requirements/helix-workflows-functional-requirements-detail.md) **core FR 14 件** (FR-NSM-01 / FR-GR-01 / FR-TDD-01 / FR-9MODE-01 / FR-GATE-01 / FR-IMPACT-01 / FR-EVT-01 / FR-4ART-01 / FR-INV-01 / FR-CTX-01 / FR-DRIFT-01 / FR-PLAN-01 / FR-DOCTOR-01 / FR-MIGR-01、L1 FR + L1 TR 統合詳細化) に対する受入テスト。balance_ratio = **AC-FR 14 件 / core FR 14 件 = 1.0**。L3 doc 内の FR-* 参照出現数は 28 件あるが、これは core FR + cross-reference 出現の合計で AC 母数ではない (2026-05-26 tl-advisor G3 P1 #3 反映)。

### AC-FR-01: NSM 計測・整合スコア
- **対象 FR**: FR-NSM-01
- **デプロイ後検証内容**: 週次 / 月次で NSM と `v_model_alignment_score` を集計し、6 axes 欠落時に未公開で止まることを確認
- **受入基準**: `aligned_plan_count >= 5/week` AND 欠落 trace を含む PLAN が `published` に遷移しない
- **検証 step**: (1) 正常 trace を持つ PLAN 群を集計 (2) 欠落 trace を混ぜる (3) score と status を比較

### AC-FR-02: Guardrail fail-close
- **対象 FR**: FR-GR-01
- **デプロイ後検証内容**: Coverage / Error Budget / TTFSP 3 軸が独立に warning / block / throttle を返す
- **受入基準**: 各軸が単独逸脱時に正しい verdict、他軸の健全状態を壊さない
- **検証 step**: (1) Coverage < 80% (2) Error Budget > 5% (3) TTFSP > 30min を個別に作る (4) verdict を比較

### AC-FR-03: TDD 順序強制
- **対象 FR**: FR-TDD-01
- **デプロイ後検証内容**: S2 不在の S3 着手 / S5 不在の S7 着手が block される
- **受入基準**: 違反遷移は exit code 2、正順遷移は exit code 0
- **検証 step**: (1) sprint 状態を S1/S4 に置く (2) 禁止 step を要求 (3) 正順 step との差分確認

### AC-FR-04: 9 mode 入口判定
- **対象 FR**: FR-9MODE-01
- **デプロイ後検証内容**: 代表 signal に対して mode 候補と route 根拠が返る
- **受入基準**: 9 mode 全件で少なくとも 1 件の正答シナリオ、signal 不足時は `manual_review_required`
- **検証 step**: (1) Discovery/Reverse/Incident signal fixture を流す (2) 推奨 mode 確認 (3) signal 欠落で manual review 確認

### AC-FR-05: gate 合成判定
- **対象 FR**: FR-GATE-01
- **デプロイ後検証内容**: static_subchecks 先行通過 + AI review 必須条件の分離が機能
- **受入基準**: static 合格 AND AI review 不要 → 即時 decided、AI review 必須 → `static_checked` に止まる
- **検証 step**: (1) G3/G7 相当 fixture を作る (2) AI review 必須/不要の差を確認 (3) final verdict 比較

### AC-FR-06: 影響範囲 query
- **対象 FR**: FR-IMPACT-01
- **デプロイ後検証内容**: PLAN 起点 / artifact 起点の両方で 5 秒以内に trace が返る
- **受入基準**: 10 回試行で中央値 ≤ 5 秒、timeout 時は部分結果 + `timeout=true`
- **検証 step**: (1) 小/中/大規模 trace を用意 (2) query 時間計測 (3) timeout fixture で部分結果確認

### AC-FR-07: Forward 復帰 event
- **対象 FR**: FR-EVT-01
- **デプロイ後検証内容**: 9 mode closure 時に idempotent な Forward event が記録される
- **受入基準**: 同一 `idempotency_key` の重複実行で row 数が増えず、target layer が保存
- **検証 step**: (1) closure event を 2 回送る (2) row 数確認 (3) target layer + closure_reason 照合

### AC-FR-08: 4 artifact / pair freeze 監査
- **対象 FR**: FR-4ART-01
- **デプロイ後検証内容**: 片方向リンク / pair 欠落 / 4 artifact 欠落を warning / blocking 分類
- **受入基準**: 必須工程欠落は `blocking`、advisory 工程欠落は `advisory_only` or `warning`
- **検証 step**: (1) 4 artifact 完備 case (2) pair 欠落 case (3) advisory case を流す

### AC-FR-09: 資産 inventory / density 可視化
- **対象 FR**: FR-INV-01
- **デプロイ後検証内容**: 工程別 density と未割当資産が同時に返る
- **受入基準**: `needs_classification` 資産が明示され、工程別件数が再計算
- **検証 step**: (1) skill/CLI/docs/PLAN を登録 (2) 工程タグ欠落資産を混ぜる (3) density report 確認

### AC-FR-10: layer context injection
- **対象 FR**: FR-CTX-01
- **デプロイ後検証内容**: process layer + role に応じて agent / skill / command / model route が束ねて返る
- **受入基準**: `L3 + se` で mandatory_agents + recommended_commands 両方返り、欠落 skill は warning
- **検証 step**: (1) `helix context bundle --layer L3 --role se` 実行 (2) bundle 内容確認 (3) 欠落 skill fixture で warning

### AC-FR-11: discrepancy routing
- **対象 FR**: FR-DRIFT-01
- **デプロイ後検証内容**: drift / trace 欠落 / OS 差異が適切な routing 先へ分類
- **受入基準**: 少なくとも `interrupt / recovery / reverse_normalization / manual_review` 4 先が再現可能
- **検証 step**: (1) 各種 discrepancy fixture を作る (2) route 結果比較 (3) environment mismatch 確認

### AC-FR-12: PLAN dependency / generates trace
- **対象 FR**: FR-PLAN-01
- **デプロイ後検証内容**: `dependencies` と `generates` が graph 化、broken link と deprecated path を返す
- **受入基準**: 正常 graph は `validated`、broken link は `exit code 2`、deprecated path は warning
- **検証 step**: (1) 正常 frontmatter 用意 (2) broken link を混ぜる (3) deprecated path を混ぜて比較

### AC-FR-13: doctor 総合監査
- **対象 FR**: FR-DOCTOR-01
- **デプロイ後検証内容**: doctor が trace / inventory / migration / context の監査結果を 1 summary に束ねる
- **受入基準**: critical ≥ 1 件で exit code 2、critical 0 件なら summary JSON
- **検証 step**: (1) 軽微 warning case (2) critical case を作る (3) exit code + summary 比較

### AC-FR-15: ドキュメント品質レビュー機能 (2026-05-26 FR-DOCREVIEW-01 / BR-11 由来、新規追加)

- **対象 FR**: FR-DOCREVIEW-01
- **デプロイ後検証内容**: `helix codex --role doc-reviewer --task "..."` 召喚で gpt-5.5 high read-only が起動し、4 視点 (Correctness / Completeness / Consistency / Clarity) + 業界標準 (Diátaxis / arc42 / ISO 26515) + V-model 量閉じ性 / implementation_status 列を統合検査して judgement 返却
- **受入基準**: (1) `cli/roles/doc-reviewer.conf` 存在 + gpt-5.5 + read-only + skills 配置正しい (2) `skills/workflow/doc-review/SKILL.md` 存在 + 9 section 構成 (3) サンプル doc に対して召喚 → SUMMARY block に decision (approve/conditional_approve/blocked) + P0/P1/P2/P3 列挙が返る (4) Edit/Write/NotebookEdit 試行が block される (read-only 強制)
- **検証 step**: (1) `helix codex --role doc-reviewer --task-file <sample>` で起動 → (2) stdout SUMMARY block parse → (3) rollout.jsonl の `response_item.output_text` で詳細取得 → (4) Edit 試行 → block 確認 → (5) `tl-advisor` との同時召喚で responsibility 分離確認

### AC-FR-16: 変更追跡 + デグレ禁止 ratchet 機能 (2026-05-26 FR-CHANGEPROP-01 / BR-12 由来、新規追加)

- **対象 FR**: FR-CHANGEPROP-01
- **デプロイ後検証内容**: `helix doctor --check-changeprop [--ratchet] [--commit-range <range>]` で 3 軸 (`check_upstream_downstream_alignment` + `check_balance_ratio_regression` + `check_id_reference_completeness`) 一括実行、pre-commit hook + CI hook 統合
- **受入基準**: (1) 3 軸 check の実装存在 (`cli/lib/changeprop_check.py` 等) (2) 違反 commit が pre-commit hook で reject される (3) `.helix/audit/balance-ratio-baseline.yaml` の Ratchet baseline 更新が正しく動作 (4) `.helix/audit/changeprop-violations.yaml` に違反 log 出力 (5) `--commit-range HEAD~10..HEAD` で過去 10 commit の集計が正常
- **検証 step**: (1) `helix doctor --check-changeprop --commit-range HEAD~1..HEAD` で 3 軸個別 check 結果取得 → (2) sample 違反 commit を生成 → block 確認 → (3) `--ratchet` flag で過去最小値ベース ratchet 動作確認 → (4) deferred-findings.yaml 登録時の例外 path 動作確認 → (5) pre-commit + CI hook 統合の smoke test

### AC-FR-14: schema migration / retrofit
- **対象 FR**: FR-MIGR-01
- **デプロイ後検証内容**: migration plan / manual approval requirement / compatibility warning が分離
- **受入基準**: migration 成功率 ≥ 95%、approval 必須 case が auto-merge を block、compat warning 漏れ 0
- **検証 step**: (1) migration plan 実行 (2) approval 必須 case で auto-merge block 確認 (3) compat warning 動作確認

## §3 非機能系受入テスト (NFR-* ↔ AC-NFR-*、Phase E.B Codex SE bi6xoaz58 PROPOSE 反映 2026-05-26)

L3 [NFR doc](../L3-requirements/helix-workflows-nfr-detail.md) NFR-AV/PF/OP/MG/SC/SE 6 領域 27 件 (本 session BR-09/10/11/12 由来で NFR-OP-06/07/08 + NFR-MG-04 を追加、23→27) + ISO 25010 再導出 2 件 (使用性 US / 機能適合性 FS) に対する受入テスト。balance_ratio = AC-NFR 29 件 / NFR 27 件 = 1.07 (≥ 1.0、追加 US/FS で網羅性強化)。

### 可用性 (AV)
- **AC-NFR-AV-01** (対象: NFR-AV-01) — 検証: 月次 CLI 起動成功率 / 受入: ≥ 99.9% / step: 起動ログ集計 → 閾値判定
- **AC-NFR-AV-02** (対象: NFR-AV-02) — 検証: `helix.db` 整合性 / 受入: corruption 0 件 AND 整合性 100% / step: health check → 破損監査
- **AC-NFR-AV-03** (対象: NFR-AV-03) — 検証: handover dump / 受入: 自動生成率 ≥ 95% AND 復旧開始 ≤ 15 分 / step: 中断再現 → dump 確認 → 復旧時間計測

### 性能・拡張性 (PF)
- **AC-NFR-PF-01** (対象: NFR-PF-01) — 検証: `helix doctor` 性能 / 受入: ≤ 30 秒 / step: 324 PLAN 相当で計測
- **AC-NFR-PF-02** (対象: NFR-PF-02) — 検証: impact-range query / 受入: 中央値 ≤ 5 秒 AND p95 ≤ 10 秒 / step: 複数ケース計測
- **AC-NFR-PF-03** (対象: NFR-PF-03) — 検証: 8 並列 Codex / 受入: workspace 衝突 0 件 / step: 8 並列実行 → 完走確認
- **AC-NFR-PF-04** (対象: NFR-PF-04) — 検証: PLAN 初稿生成 / 受入: ≤ 1 分 AND 失敗率 < 5% / step: 複数起票を連続実行

### 運用・保守性 (OP)
- **AC-NFR-OP-01** (対象: NFR-OP-01) — 検証: auto-deprecation (L1-IN-12 排泄系) / 受入: stale 資産 archive 率 ≥ 90% / step: 対象抽出 → archive 実行 → 結果確認
- **AC-NFR-OP-02** (対象: NFR-OP-02) — 検証: 月次 audit / 受入: audit 完遂率 100% AND P0 排出率 100% / step: audit report → P0 対応確認
- **AC-NFR-OP-03** (対象: NFR-OP-03) — 検証: warn 閾値 / 受入: 50 件で alert AND Phase α exit ≤ 20 / step: warn 数操作 → alert/exit 条件確認
- **AC-NFR-OP-04** (対象: NFR-OP-04) — 検証: lineage trace / 受入: 欠損 0 件 / step: skill/command/agent の trace 抽出
- **AC-NFR-OP-05** (対象: NFR-OP-05) — 検証: verify-before-act ([[feedback_memory_verify_before_act]]) / 受入: 違反 0 件 AND verify 実施率 100% / step: carry 実行前後ログ確認
- **AC-NFR-OP-06** (対象: NFR-OP-06、2026-05-26 BR-09 由来) — 検証: inventory drift 監査 / 受入: drift 率 ≤ 5% AND 新規 doc 起票時 implementation_status 列充足率 100% / step: (1) 直近 30 commit の doc 改定で implementation_status 列充足率を grep → (2) `helix doctor check_glossary_coverage` (L4 carry) で drift 集計 → (3) ≤ 5% 確認
- **AC-NFR-OP-07** (対象: NFR-OP-07、2026-05-26 BR-11 由来) — 検証: doc-reviewer 召喚 coverage / 受入: 大規模 doc 改定 (~500 行+) の `helix codex --role doc-reviewer` 召喚 + 判定結果残置率 ≥ 95% / step: (1) 直近 30 commit のうち doc 改定 (~500 行+) 該当 commit 抽出 → (2) commit message + final report + 会話 history で召喚 evidence + 判定 grep → (3) 召喚率 ≥ 95% 確認
- **AC-NFR-OP-08** (対象: NFR-OP-08、2026-05-26 BR-12 由来) — 検証: デグレ禁止 ratchet 機構機械強制 / 受入: 違反 commit の hook block 率 100% AND balance_ratio < 1.0 regression 検出率 100% AND 上流↔下流 trace 切れ件数 0 / step: (1) `helix doctor --check-changeprop` 3 軸個別 check → (2) sample 違反 commit で hook block 確認 → (3) `.helix/audit/changeprop-violations.yaml` 0 件維持 → (4) Ratchet baseline 更新動作確認 → (5) Hyrum's Law ベースの破壊的変更が deferred-findings 登録経由のみで通過することを確認

### 移行性 (MG)
- **AC-NFR-MG-01** (対象: NFR-MG-01) — 検証: V1→V2 retrofit / 受入: 再実行成功率 ≥ 95% / step: retrofit → rerun → rollback 確認
- **AC-NFR-MG-02** (対象: NFR-MG-02) — 検証: migration idempotency / 受入: 副作用 0 件 / step: migration 2 回実行 → 差分確認
- **AC-NFR-MG-03** (対象: NFR-MG-03) — 検証: package bootstrap / 受入: 導入初期化 ≤ 30 分 / step: 新規 project で bootstrap
- **AC-NFR-MG-04** (対象: NFR-MG-04、2026-05-26 BR-10 由来) — 検証: Strangler Fig Pattern 段階置換進捗 / 受入: Phase α 終了時 V1 PLAN `is_reference: true` 化率 100% AND Phase β 終了時 旧 enum 残存 0 AND Phase γ 終了時 Strangler 段階置換完了 / step: (1) `find docs/plans/ -name '*.md' | xargs grep -l 'is_reference: true' | wc -l` で V1 PLAN 移行率 → (2) `git grep -E 'G[2-9]|G14' --` で旧 enum 残存 → (3) Phase 別残量 dashboard と kill criteria 突合

### セキュリティ (SC)
- **AC-NFR-SC-01** (対象: NFR-SC-01) — 検証: secret scan / 受入: 検出 0 件 / step: repository scan 実行
- **AC-NFR-SC-02** (対象: NFR-SC-02) — 検証: repeated regen guard ([[feedback_settings_json_auto_regen_repeated]]) / 受入: 検知率 100% / step: regen 反復 → diff 確認強制
- **AC-NFR-SC-03** (対象: NFR-SC-03) — 検証: tool guard (PMO+PdM 12 種以外 block) / 受入: 非許可 tool block 率 100% / step: 禁止 tool 呼出 → block 確認
- **AC-NFR-SC-04** (対象: NFR-SC-04) — 検証: commit/push guard / 受入: 違反 0 件 / step: Codex 経路で禁止操作検証
- **AC-NFR-SC-05** (対象: NFR-SC-05) — 検証: human approval boundary / 受入: 対象変更の人間確認率 100% / step: 境界ケース実行 → confirm 必須確認

### システム環境 (SE)
- **AC-NFR-SE-01** (対象: NFR-SE-01) — 検証: Linux/macOS matrix / 受入: 主要コマンド成功率 100% / step: OS 別 smoke
- **AC-NFR-SE-02** (対象: NFR-SE-02) — 検証: Claude/Codex 両導線 / 受入: core entry flow 継続率 100% / step: 両 CLI で同一フロー確認
- **AC-NFR-SE-03** (対象: NFR-SE-03) — 検証: runtime 下限 (Python 3.11+ / Bash 5.0+ / SQLite 3.40+ / git 2.40+) / 受入: version 違反 0 件 / step: version check 実行

### ISO 25010 再導出 (L1 未掲示 2 特性、L3 で補完)
- **AC-NFR-US-01** (追加観点: ISO 使用性) — 検証: CLI usability / 受入: `helix help` 完備率 ≥ 90% AND TTFSP ≤ 30 分 / step: 初回利用者フローを計測 (docs site / TUI 追加時は L2/L10 unskip trigger)
- **AC-NFR-FS-01** (追加観点: ISO 機能適合性) — 検証: FR-* と AC-FR-* の量閉じ性 / 受入: `balance_ratio ≥ 1.0` / step: requirement_count と AC_count を機械集計

## §4 V-model L3↔L12 ペア凍結確認

- L3 3 PLAN の各要件 doc (`business-requirements-detail.md` / `functional-requirements-detail.md` / `nfr-detail.md`) の BR-*/FR-*/NFR-* と本 doc §1/§2/§3 の AC-* が **1:1 対応** していることを確認
- 対応欠落 (要件に対応する AC がない) は **G3 ゲート blocker**
- `helix gate G3` で機械検証 (V5 framework 完遂後)

## §5 関連 doc

- **L3 ペア相手**: [L3-業務要件plan](../../plans/L3/L3-helix-workflows-業務要件plan.md) + L3-機能要件plan + L3-非機能要件plan (Phase E.B 起票予定)
- **L3 製本 doc** (Step 2-3 で起票):
  - [helix-workflows-business-requirements-detail.md](../L3-requirements/helix-workflows-business-requirements-detail.md)
  - helix-workflows-functional-requirements-detail.md (Phase E.B)
  - helix-workflows-nfr-detail.md (Phase E.B)
- **L12 工程 doc**: docs/v2/process/L12-deployment-and-acceptance-test.md (HELIX-workflows V2 同期 doc、不在の場合は carry)
- **HELIX-workflows L12 正本**: [HELIX-workflows/helix-process/L12-deployment.md](../../../HELIX-workflows/helix-process/L12-deployment.md)
- **L0 概念**: [docs/v2/L0-helix-workflows/concept.md](../L0-helix-workflows/concept.md) §5
- **上流 L1 ペア (運用テスト設計)**: [../L14-test-design/helix-workflows-operational-test-design.md](../L14-test-design/helix-workflows-operational-test-design.md)

## §6 carry / 既知の不足

- **L12-test-design template skeleton 不在 carry**: 本 doc は L3-業務要件plan 起票時に手動作成。L14 と同様、`cli/templates/plan/v2/` に L12-test-design 用 template 整備候補 (別 PLAN)。
- ~~§2 / §3 AC 未定義~~: **解消済 (2026-05-26 Phase E.B.1 完了)** — §2 機能系 AC-FR-01〜14 + §3 非機能系 AC-NFR 25 件すべて detail 化、balance_ratio 全 pair ≥ 1.0。
- **L12 工程 doc 不在の可能性**: `docs/v2/process/L12-*` の存在を verify 必要、不在なら carry。
- **AC-BR-08 受入テストの実行可能性**: 採用 project が現状 self のみのため、Phase β 以降の検証 (carry)。Phase α では「採用 project portable 化準備」を AC 化代替。
