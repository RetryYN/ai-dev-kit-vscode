---
adr_id: ADR-032
title: "ADR-032: 自動走行 framework 5-layer 採用判断"
status: Proposed
date: 2026-05-20
deciders:
  - PM (Opus)
  - PO
reviewers:
  - tl-advisor (gpt-5.5 high)
related_adrs:
  - ADR-025 (V5 framework core)
  - ADR-026 (PostToolUse plan auto-register)
  - ADR-031 (recovery plan kind)
  - ADR-024 (continueOnBlock / active guidance loop)
related_plans:
  - PLAN-099 (実装計画、本 ADR の実装先)
  - PLAN-091 (V5 framework 本体、frontmatter 語彙正本)
  - PLAN-081 (superseded partial)
  - PLAN-090 (active guidance loop 前駆)
supersedes: []
layer: L2
---

# ADR-032: 自動走行 framework 5-layer 採用判断

> Status: **Proposed** (Layer 4+5 PoC document 段階)  
> 本 ADR は PLAN-099 tree の L2 snapshot。PLAN-099 §4 が担当要素。

---

## 1. 背景 (Context)

### 1.1 解決すべき 3 課題

2026-05-19 の実運用で顕在化した 3 課題:

**課題 A: 14h idle 事故**
- 09:57 に carry 残存のまま turn 終了 → 23:49 まで harness が再起動せず 14h アイドル化
- 根本原因: `run_in_background: true` 完了通知への依存と「turn を終える」ルールの誤適用
- 参考: memory `feedback_dont_stop_with_carry_remaining.md`

**課題 B: context 枯渇中断**
- auto-compact 発火時に重要 state (L2/L3/ADR 判断) が消失し、session restart 後に再現不能
- PreCompact hook (v1.0.46 で追加) を活用した事前永続化が必要
- 参考: CHANGELOG v1.0.46「Added PreCompact hook support: hooks can now block compaction by exiting with code 2 or returning {"decision":"block"}」

**課題 C: carry 残し放置**
- 完了報告後に次 wave を投入しない = 時間枠利用効率の低下
- ScheduleWakeup heartbeat で carry 監視が必要

### 1.2 既存アーキテクチャとの関係

```
既存 hook 構成 (変更しない):
  SessionStart  → sessionstart-harness-summary.sh (HELIX framework summary)
  Stop          → stop.sh + helix-session-summary (session telemetry、軽量化予定)
  PreToolUse    → pretooluse-agent-guard.sh / design-doc-web-search-guard.sh 等
  PostToolUse   → posttooluse-design-doc-web-search-revert.sh / helix-post-tool-use

追加予定 hook (PLAN-099 別 session):
  PreCompact    → precompact-state-snapshot.sh (Layer 3)
  PostToolUse   → posttooluse-helix-job-enqueue.sh (Layer 1)
  SessionStart  → sessionstart-history-injection.sh (Layer 4、既存 hook と共存)
```

### 1.3 業界 standard 調査 (Web 検索実施済)

| 調査対象 | 確認事項 | Source |
|---|---|---|
| PreCompact hook 仕様 | v1.0.46 (= ~2.1.105 相当) で追加。decision:block で compact を一時阻止可能。8 回連続 block で cap (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP で上書き可、v2.1.143 fix) | [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) v1.0.46 / v2.1.143 / [hooks reference](https://code.claude.com/docs/en/hooks) |
| transcript_path の取扱い | hook 環境変数として提供。EnterWorktree 後の wrong-dir bug は 2.1.141 で修正済み。全量 SQLite キャプチャは secret/PII リスクあり | [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) 2.1.141 / [hooks guide](https://docs.claude.com/en/docs/claude-code/hooks-guide) |
| heartbeat / carry 監視 | ScheduleWakeup は外部状態 polling 専用 (HELIX CLAUDE.md §ScheduleWakeup 運用ルール)。/loop (/proactive alias) は 2.1.105 で追加。Stop hook block cap は 2.1.143 で修正 | [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) 2.1.143 / [/loop docs](https://code.claude.com/docs/en/cli-reference) |

---

## 2. 決定 (Decision)

**5-layer 自動走行 framework を採用する (C 案 = Layer 4+5 PoC 先行)**

```
Layer 1: PostToolUse(Write|Edit + PLAN.md) → helix job enqueue 候補提示 (task_queue 新設なし、Plan Consent / P0 guard 必須)
Layer 2: statusLine で context % 4 段階監視 (debounce + hysteresis 必須)
Layer 3: PreCompact hook で state 永続化 (decision:block は 3 条件 AND 限定)
Layer 4: SessionStart/UserPromptSubmit で関連履歴自動注入 (HELIX 独自再実装)
Layer 5: ScheduleWakeup adaptive heartbeat (carry check + 候補提示)
```

---

## 3. 検討した代替案 (Alternatives)

### A 案: 全 layer 一括実装 (棄却)

- 全 5 layer を 1 session で一括実装
- 期間: 2-3 session
- 棄却理由: Layer A (PLAN-091 frontmatter 語彙) / Layer B (PLAN-092 DB schema) が確定前に Layer 1-3 を実装すると、schema 変更で全 hook を書き直す必要が生じる。TL v5 修正条件 #2 で棄却。

### B 案: 段階的実装 (全 layer 順番待ち) (棄却)

- Layer A → B → C の確定を順番に待って各 layer を実装
- 期間: 4-6 session
- 棄却理由: Layer 4+5 (SessionStart 注入 + heartbeat) は Layer A/B を必要としない。既存 handover/SessionStart/scheduler 上で実装可能。非効率。TL v5 修正条件 #2 で棄却。

### C 案 (採用): Layer 4+5 PoC 先行 + Layer 1-3 は A/B 確定後

- Layer 4+5: Layer A/B 不要。0.5-1 session で PoC 実装可能
- Layer 1-3: PLAN-091 + PLAN-092 確定後に実装 (1-2 session)
- 総期間: 2-3 session (A 案と同期間だが blockers が少ない)
- **採用理由**: 最短で 14h idle 事故 (課題 A) と carry 放置 (課題 C) を解消できる。Layer A/B ブロッカーを回避。

---

## 4. 肯定的影響 (Positive Consequences)

| 影響 | 詳細 |
|---|---|
| 14h idle 事故解消 | Layer 5 heartbeat が carry > 0 を検出し、ScheduleWakeup で自動 wake |
| context 枯渇予測 | Layer 2 statusLine が 4 段階で事前警告、Layer 3 が compact 前に state 永続化 |
| carry 自動消化 | Layer 1 が PLAN.md 書き込み後に候補提示、Layer 5 が heartbeat で候補を再提示 |
| session 復帰精度向上 | Layer 4 が cleared/compacted 後に関連 state を bundle 注入 |

---

## 5. 否定的影響とリスク対策 (Negative Consequences)

| リスク | TL v5 指摘 | 対策 |
|---|---|---|
| PreCompact decision:block の無限 loop | P1 / 修正条件 #3 | 3 条件 AND 限定 + one-shot flag (同 session 内 1 回) + 8 回 cap (Claude Code 仕様) |
| transcript 取扱い secret 漏洩 | P1 / 修正条件 #5 | transcript_path 参照 + 要約 state + sensitive_fields 除外 + 人間確認対象化 |
| hook foreground 性能影響 | P2 | SessionStart は fail-open、重い sync は background (transcript_summary は async) |
| statusLine ノイズ化 | P2 / 修正条件 #4 | debounce 30s + hysteresis 5% gap で警告連打防止 |
| Plan Consent 破壊 | P0 | queue worker は必ず Plan Consent / WBS / handover Next Action guard を通す |
| PLAN-088 との競合 | P1 | task_queue 新設なし。Layer 1 は helix job enqueue を使い、plan_registry (PLAN-092) が正本。単一実行正本を維持 |

---

## Related

### 関連 ADR

- [ADR-025](ADR-025-v5-framework-core-decision.md): V5 framework 本体採用判断 (Layer C 自動走行 framework は V5 要素 #18)
- [ADR-026](ADR-026-posttooluse-plan-auto-register-decision.md): PostToolUse 自動登録 (Layer 1 と統合点)
- [ADR-031](ADR-031-recovery-plan-kind-decision.md): リカバリープラン kind (Layer 4 SessionStart 履歴注入 source)
- [ADR-009](ADR-009-hook-strategy.md): hook strategy (本 ADR は hook 5-layer 拡張)

### 関連 PLAN

- [PLAN-MM-001](../plans/PLAN-MM-001-v5-framework-master-plan.md): V5 framework 親設計 (本 ADR の parent)
- [PLAN-091](../plans/PLAN-091-v5-framework-core.md): V5 framework 本体 (frontmatter 語彙正本、本 PLAN-099 の requires)
- [PLAN-099](../plans/PLAN-099-autonomous-runtime-framework-5layer.md): 本 ADR の対応実装 PLAN (5-layer 詳細設計)
- [PLAN-090](../plans/PLAN-090-posttooluse-continueonblock-refactor.md): active guidance loop pattern (Layer 1 hook 前駆、本 ADR が継承)
- [PLAN-081](../plans/PLAN-081-stop-hook-auto-handover.md): Stop hook 旧設計 (本 ADR の Layer 1+5 で **superseded**)
- [PLAN-082](../plans/PLAN-082-subagent-sprint-mechanization.md): subagent sprint 機械化 (共存、本 ADR は hook 層、PLAN-082 は subagent 層)
- [PLAN-083](../plans/PLAN-083-harness-auto-integration.md): harness 自動統合 (共存、本 ADR は runtime 層)

### 関連 memory feedback

- `feedback_dont_stop_with_carry_remaining` (14h idle 事故、本 ADR の課題 A 直接 source)
- `feedback_recovery_plan_kind_missing` (中間結論消失、本 ADR の課題 B 直接 source)
- `feedback_task_notification_trust` (harness 通知信用、本 ADR Layer 5 heartbeat 設計の前提)

---

## 6. 実装計画 (Implementation Plan)

```
P1 (本 session): document + fixture 方針確定
  → PLAN-099 起票 + ADR-032 起票 + fixture 方針 30+ ケース確定

P2a (別 session、C 案 PoC): Layer 4+5 先行実装
  → sessionstart-history-injection.sh (Layer 4)
  → helix-heartbeat-scheduler (Layer 5)
  → transcript_summary.py skeleton
  → test_5layer_fixtures.py Layer 4-5 ケース PASS

P2b (別 session): Layer 1-3 本実装
  → PLAN-091 (Layer A) + PLAN-092 (Layer B) 確定後に着手
  → posttooluse-helix-job-enqueue.sh (Layer 1)
  → helix-statusline (Layer 2)
  → precompact-state-snapshot.sh (Layer 3)
  → 全 T1〜T6 ケース PASS

P3 (別 session): fail-close 化
  → warn-only → fail-close 段階遷移
  → statusLine + PreCompact の block 有効化
  → PLAN-091 fail-close lint 統合
```

---

## 7. PLAN-081 との関係

PLAN-081 (Stop-hook auto handover) Phase 1 は完遂済み。本 ADR が採用する 5-layer framework は PLAN-081 を **partial supersede** する:

| PLAN-081 範囲 | ADR-032 での扱い |
|---|---|
| Stop hook → handover snapshot | 維持 (Layer 3 PreCompact が補完) |
| compact recommendation (systemMessage) | Layer 2 statusLine が引き継ぎ (Stop hook から分離) |
| compacted 後 SessionStart 復帰 | Layer 4 が拡張 (bundle 注入まで担当) |

**PLAN-081 doc は変更しない**。本 ADR の §7 が正本。

---

## 8. 承認条件 (Acceptance Criteria for Status Change)

| 状態 | 条件 |
|---|---|
| Proposed → Accepted | Layer 4+5 PoC (P2a) で T4-001〜006 + T5-001〜007 が全 PASS + PM 承認 |
| Accepted → Deprecated | 5-layer framework を別 framework に置き換える場合、ADR-033 で supersede |

---

### 関連リンク (機械可読パス table)

| 文書 | パス |
|---|---|
| PLAN-099 (実装計画) | docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md |
| PLAN-MM-001 (親設計) | docs/plans/PLAN-MM-001-v5-framework-master-plan.md |
| PLAN-091 (Layer A、frontmatter 語彙正本) | docs/plans/PLAN-091-v5-framework-core.md |
| PLAN-090 (continueOnBlock 前駆) | docs/plans/PLAN-090-posttooluse-continueonblock-refactor.md |
| PLAN-081 (partial superseded) | docs/plans/PLAN-081-stop-hook-auto-handover.md |
| Claude Code CHANGELOG 参照 | https://github.com/anthropics/claude-code/releases |
