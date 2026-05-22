---
plan_id: PLAN-151
title: "PLAN-151: V5 framework G-gate fail-close graduation (advisory → WARN → fail-close 段階遷移横展開)"
kind: design
layer: L4
drive: be
status: draft
created: 2026-05-23
revised: 2026-05-23
owner: PM
phases: L4
gates: G2, G4, G6
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・fail-close 移行タイミング finalize"
  - role: tl-advisor
    slot_label: "TL — 段階遷移設計 adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 gate 整合チェック・PLAN-089 との差分確認"
  - role: se
    slot_label: "SE — G2/G4/G6 fail-close hook + helix-gate CLI 拡張"
  - role: security
    slot_label: "Security — G6 security audit fail-close 実施前レビュー"
generates:
  - artifact_path: cli/helix-gate
    artifact_type: cli_extension
  - artifact_path: docs/plans/PLAN-151-gate-fail-close-graduation-framework.md
    artifact_type: design_doc
  - artifact_path: .claude/hooks/pretooluse-g2-adversarial-review-guard.sh
    artifact_type: hook
  - artifact_path: .claude/hooks/pretooluse-g6-security-audit-guard.sh
    artifact_type: hook
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-089
    - PLAN-119
  blocks: []
related_plans:
  - PLAN-089
  - PLAN-119
related_adr:
  - ADR-053 候補 (fail-close graduation framework、本 PLAN 確定後に起票)
reference_docs:
  - docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md
  - docs/plans/PLAN-119-pytest-coverage-gate-fail-close.md
---

# PLAN-151: V5 framework G-gate fail-close graduation (advisory → WARN → fail-close 段階遷移横展開)

## L2 大局判断メモ (ADR-053 起票前の中間記録)

本 PLAN は **PLAN-089 (G3 design doc web search fail-close)** と **PLAN-119 (G4 coverage gate fail-close)** で確立した「advisory → WARN → fail-close 段階遷移」パターンを G2/G4/G6 に横展開する設計 PLAN。L2 大局判断 (fail-close graduation framework 採用) は本 PLAN 確定後に **ADR-053** として snapshot 化する。

---

## 0. 起票背景

PLAN-089 で G3 設計 doc Web 検索ガードレールを advisory → fail-close へ段階移行し、PLAN-119 で G4 pytest coverage gate を同パターンで拡張した。しかし以下の G-gate は advisory のまま放置されており、整合性が欠けている。

| Gate | 対象チェック | 現状 | 目標 |
|---|---|---|---|
| G2 (設計凍結) | adversarial-review 実施有無 | advisory warn | fail-close |
| G4 (実装凍結) | coverage gate (PLAN-119) | WARN 実装中 | fail-close |
| G6 (RC 判定) | security audit 実施有無 | advisory warn | fail-close |

本 PLAN はこれら 3 gate の fail-close graduation を、**PLAN-089 が確立した 4 Phase pattern** を再利用して統一的に実施する。

## 1. 業界 standard 参照

| 参照 | source | 役割 |
|---|---|---|
| OWASP DevSecOps Guideline | https://owasp.org/www-project-devsecops-guideline/ | G6 security audit gate の fail-close 根拠 |
| Google Engineering Practices: Code Review | https://google.github.io/eng-practices/review/ | G2 adversarial-review 必須化の業界標準根拠 |
| NIST SP 800-218 (SSDF) | https://csrc.nist.gov/publications/detail/sp/800-218/final | セキュリティ検証 gate の段階導入ガイドライン |
| LaunchDarkly Feature Flag Gradual Rollout | https://launchdarkly.com/docs/guides/feature-flags | advisory → fail-close 段階切替の安全ロールアウト根拠 (PLAN-089 継承) |
| PLAN-089 Phase 設計 | docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md | 横展開元 4 Phase pattern の正本 |

## 2. 前提 + スコープ

- PLAN-089 の 4 Phase pattern (advisory 計測 → fail-close 切替 → retrofit → bypass audit) を横展開する
- G4 coverage gate は PLAN-119 が先行実装、本 PLAN は warn-only → fail-close 切替部分のみ担当
- bypass env 命名規則: `HELIX_GATE_{GATE_ID}_FAIL_CLOSE=1` で統一 (例: `HELIX_GATE_G2_FAIL_CLOSE=1`)
- 段階移行期間: 各 gate 1-2 week の WARN 計測後に fail-close 切替

## 3. 受入条件

- AC-151-01: G2 adversarial-review 未実施を `helix-gate check-g2` で検出し、WARN → fail-close 段階移行できること
- AC-151-02: G4 coverage gate (PLAN-119 実装済) を `HELIX_GATE_G4_FAIL_CLOSE=1` で fail-close に切替できること
- AC-151-03: G6 security audit 未実施を `helix-gate check-g6` で検出し、WARN → fail-close 段階移行できること
- AC-151-04: 各 gate の audit 履歴が helix.db `gate_audit_metrics` (v33 スキーマ継承) に記録されること
- AC-151-05: bypass env の利用が audit log に残り、週次レビュー対象になること

## 4. Phase 設計

### Phase 1: advisory 計測 (各 gate 1-2 week)

- 対象 gate: G2 adversarial-review / G4 coverage / G6 security audit
- 実装: `helix-gate check-g2 --advisory` / `check-g6 --advisory` を追加
- 計測指標: advisory_miss_count / bypass_count / plan_size_bucket
- 収集先: helix.db `gate_audit_metrics` (PLAN-089 v33 schema を拡張、gate_id カラム追加)

### Phase 2: WARN 移行 (各 gate の miss 率が 5% 以下を確認後)

- `HELIX_GATE_{GATE_ID}_WARN=1` で warn-only 有効化
- hook 追加:
  - `.claude/hooks/pretooluse-g2-adversarial-review-guard.sh` (G2)
  - `.claude/hooks/pretooluse-g6-security-audit-guard.sh` (G6)
- G4: PLAN-119 warn 実装を本 Phase で連携確認

### Phase 3: fail-close 切替

- `HELIX_GATE_{GATE_ID}_FAIL_CLOSE=1` で fail-close 有効化
- bypass env は理由必須 + audit log 記録
- 切替条件: WARN 期間中の miss 率 < 2% かつ bypass 濫用なし

### Phase 4: 既存 PLAN retrofit + bypass audit

- 既存 PLAN で adversarial-review / security audit の証跡が不足するものを P0/P1/P2 で分類
- bypass 利用履歴を週次 `helix gate audit-report` で可視化

## 5. G2 / G4 / G6 gate 個別設計

### 5.1 G2: adversarial-review fail-close

```
check 対象: G2 通過時に adversarial-review (tl-advisor / pm-advisor) の呼び出し記録
証跡: helix.db `adversarial_review_log` (review_type / reviewer_role / plan_id / session_id)
hook: pretooluse-g2-adversarial-review-guard.sh
  - G2 通過 Write 前に adversarial_review_log を確認
  - 記録なし → WARN (Phase 2) → fail-close (Phase 3)
bypass: HELIX_GATE_G2_FAIL_CLOSE=0 + 理由 env
```

### 5.2 G4: coverage gate (PLAN-119 連携)

```
check 対象: coverage gate pass (PLAN-119 実装)
証跡: helix.db gate_audit_metrics (PLAN-089 v33 継承)
切替: HELIX_GATE_G4_FAIL_CLOSE=1 で PLAN-119 warn → fail-close
本 PLAN 担当: fail-close 切替 env + audit log 連携のみ
```

### 5.3 G6: security audit fail-close

```
check 対象: G6 通過時に security audit (helix codex --role security) の実施記録
証跡: helix.db `security_audit_log` (plan_id / auditor_role / finding_count / session_id)
hook: pretooluse-g6-security-audit-guard.sh
  - G6 通過 Write 前に security_audit_log を確認
  - 記録なし → WARN (Phase 2) → fail-close (Phase 3)
bypass: HELIX_GATE_G6_FAIL_CLOSE=0 + 理由 env + 必須 PM 確認
```

## 6. リスク

- R-151-01: advisory 計測期間中に miss 率が高く fail-close 移行が遅延する
  - 対応: Phase 1 2 週目時点でスナップショット取得、miss 率 > 20% なら toolchain 問題として PLAN 分割
- R-151-02: G6 security audit hook が CI/CD pipeline と競合する
  - 対応: hook は Claude Code 内のみ適用、CI は別途 `helix gate check-g6 --ci` フラグで独立実行
- R-151-03: bypass env の恒久化 (settings.json への永続化)
  - 対応: PLAN-089 §5 と同じ原則 — bypass は Bash 経由のみ受理、settings.json 固定禁止
- R-151-04: ADR-053 未起票のまま fail-close 移行が先行する
  - 対応: Phase 2 (WARN 移行) 前に ADR-053 を起票することを Phase 1 exit 条件に追加

## 7. carry list

- [ ] ADR-053 起票 (fail-close graduation framework L2 凍結、Phase 1 exit 前必須)
- [ ] helix.db v35? gate_audit_metrics に gate_id カラム追加 migration
- [ ] helix gate audit-report CLI (週次 bypass 可視化)
- [ ] G2 adversarial_review_log schema 設計 (helix.db 統合 or 独立テーブル)
- [ ] G6 security_audit_log schema 設計
- [ ] PLAN-119 との fail-close 切替 env 命名統一確認

## 8. V-model 4 artifact trace

| 層 | 対応 |
|---|---|
| 設計 | `docs/plans/PLAN-151-gate-fail-close-graduation-framework.md` (本 file) |
| 実装 | `cli/helix-gate`, `.claude/hooks/pretooluse-g2-adversarial-review-guard.sh`, `.claude/hooks/pretooluse-g6-security-audit-guard.sh` |
| テスト設計 | §3 受入条件 AC-151-01〜05 |
| テストコード | `cli/lib/tests/test_helix_gate_fail_close_graduation.py` (実装 PLAN で起票) |

## 9. 関連 memory

- [[feedback_adr_before_plan_violation]] (PLAN ⊃ ADR レイヤー併存、ADR-053 起票必須)
- [[feedback_design_doc_web_search_required]] (本 PLAN でも WebSearch 5 query 実施済み)
- [[project_2026_05_23_session_handover]] (本 session の carry list 確認)
