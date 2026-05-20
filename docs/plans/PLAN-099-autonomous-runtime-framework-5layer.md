---
plan_id: PLAN-099
title: "PLAN-099: 自動走行 framework 5-layer (autonomous runtime substrate)"
layer: cross
kind: impl
status: draft
size: L
drive: be
created: 2026-05-20
revised: "2026-05-20 (Round 3 反映: revised quote + task_queue 用語 hook 名修正 + P0 guard OR 表現分離)"
owner: PM
phases: L3, L4
gates: G3, G4
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・P0 承認境界管理・Layer A/B 設計確定後 Layer 1-3 実装判断"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメントチェック・fixture 方針整合確認"
  - role: se
    slot_label: "SE — Layer 4+5 本実装・hook 配置・CLI 実装"
  - role: devops
    slot_label: "DevOps — sessionstart hook / scheduler / cron 設定"
  - role: tl-advisor
    slot_label: "TL adversarial check — G3/G4 凍結判定・design review"
generates:
  - artifact_path: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md
    artifact_type: design_doc
  - artifact_path: docs/adr/ADR-032-autonomous-runtime-framework-decision.md
    artifact_type: adr_snapshot
  - artifact_path: .claude/hooks/posttooluse-helix-job-enqueue.sh
    artifact_type: hook
  - artifact_path: .claude/hooks/precompact-state-snapshot.sh
    artifact_type: hook
  - artifact_path: .claude/hooks/sessionstart-history-injection.sh
    artifact_type: hook
  - artifact_path: cli/helix-statusline
    artifact_type: cli_extension
  - artifact_path: cli/helix-heartbeat-scheduler
    artifact_type: cli_extension
  - artifact_path: cli/lib/transcript_summary.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_5layer_fixtures.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-MM-001
    - PLAN-090 (PostToolUse continueOnBlock / active guidance loop pattern 前駆)
  blocks: []
related_adr:
  - ADR-032 (本 PLAN の L2 snapshot)
related_plans:
  - PLAN-081 (Stop-hook auto handover: Layer 1+5 で機能拡張・superseded 範囲あり、下記 §12 参照)
  - PLAN-082 (subagent sprint mechanization: 共存、hook 層 vs subagent 層)
  - PLAN-083 (harness auto integration: 共存、runtime 層 vs plan 自動統合層)
  - PLAN-088 (TodoWrite × agent slot framework: task_queue 競合解消、§10 参照)
  - PLAN-092 (PostToolUse plan 自動登録: Layer 1 の helix.db 連携 upstream)
test_design: docs/plans/PLAN-099-5layer-test-design.md (別 session 起票予定)
---

# PLAN-099: 自動走行 framework 5-layer

> V5 framework §18 担当要素。  
> 本 session scope: **document + fixture 方針のみ**。  
> 本実装 (hook 配置 / scheduler 起動 / DB migration) は別 session。  
> PLAN-091 (Layer A) + PLAN-092 (Layer B) 確定後に Layer 1-3 本実装 (Layer C) へ接続。

---

## 1. 目的

3 つの慢性課題を **1 つの cohesive framework** で同時解決する:

| 課題 | 症状 | 解決 Layer |
|---|---|---|
| 14h idle 事故 | carry 残存で turn 終了 → harness が wake しない | Layer 5 (adaptive heartbeat) |
| context 枯渇中断 | context 満杯で state 消失 → compact 前に永続化できない | Layer 2+3 (statusLine + PreCompact) |
| carry 残し放置 | 完了報告後に次 wave 投入せず停滞 | Layer 1+5 (task-queue 検出 + heartbeat) |

---

## 2. 背景

### 2.1 起点事故 (2026-05-19)

- **14h idle 事故**: 09:57 に carry 残存で turn 終了 → 23:49 まで harness が再起動せず 14h アイドル化。  
  原因: `run_in_background: true` 完了通知への依存と「turn を終える」ルールを、carry 残存状態に誤適用。  
  (memory: `feedback_dont_stop_with_carry_remaining.md` 参照)
- **context 枯渇**: auto-compact が発火しても state が消失し、session restart 後に carry が再現できない。
- **carry 放置**: 完了報告後に次 wave を投入しない = 時間枠利用効率の低下。

### 2.2 既存設計との接続

- PLAN-081 (Stop-hook auto handover) は Phase 1 完遂済み。本 PLAN の Layer 1+5 は PLAN-081 の設計を引き継ぎつつ機能拡張する。Stop hook の責務を軽量化し、statusLine (Layer 2) に threshold 監視を移管する。
- PLAN-082/083 は hook 層・plan 統合層として共存。本 PLAN は **runtime substrate 層** (session continuity / context 監視 / carry 自動検出) に特化。
- PLAN-090 (continueOnBlock / active guidance loop) が Layer 1 hook 設計の直接前駆。

---

## 3. 業界 standard 参照 (Web 検索 3 query 実施済)

| Query | Source URL | 参照意図 |
|---|---|---|
| Claude Code PreCompact hook state preservation 2026 | https://github.com/anthropics/claude-code/releases (CHANGELOG v1.0.46) | PreCompact hook が v1.0.46 (= 2.1.105) で正式追加、`decision:block` で compact を一時阻止可能、8 回連続 block でターン終了 cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) 導入済み (v2.1.143 fix) |
| claude-brain transcript path session memory injection 2026 | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.141) | `transcript_path` が SessionStart/hook で提供される、EnterWorktree 後の wrong-dir bug は 2.1.141 で修正済み。claude-brain 型全量 SQLite キャプチャは secret/PII リスクあり → HELIX は `transcript_path 参照 + 要約 state + 明示的 retention` 独自再実装 |
| agent farm scheduler heartbeat cron 2026 | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143) | Stop hook block が 8 回 loop で cap される修正 + background session worktree isolation + `/loop` (`/proactive`) alias 確認。ScheduleWakeup は external state polling 専用 (HELIX CLAUDE.md 運用ルール) |

> 追加確認: CHANGELOG 2.1.144 で `/resume` background session 対応、2.1.143 で `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` env 変数追加。

---

## 4. V5 framework 担当要素

本 PLAN は **V5 framework 18 要素の #18** を実装する:

```
#18 自動走行 framework 5-layer:
  Layer 1: PostToolUse(Write|Edit + PLAN.md) → helix job enqueue (task_queue 新設なし、P0 承認 guard 必須)
  Layer 2: statusLine hook で context % 先回り監視 (4 段階)
  Layer 3: PreCompact hook で auto-compact 前 state 永続化
  Layer 4: SessionStart(cleared|compacted) + UserPromptSubmit で関連履歴自動注入
  Layer 5: ScheduleWakeup adaptive heartbeat で carry check + task pop
```

**依存順序 (Layer A → B → C)**:
- Layer A (PLAN-091): frontmatter 語彙・generates・dependencies 語彙の正本定義 → 本 PLAN の記述基盤
- Layer B (PLAN-092): helix.db の plan_registry schema → Layer 1 の helix job enqueue 連携先
- Layer C (本 PLAN): hook + CLI の runtime substrate → Layer A/B 確定後に Layer 1-3 本実装

**本 session scope**: Layer A/B 確定前でも **Layer 4+5 PoC は既存 handover/SessionStart/scheduler 上で実装可能**。  
本 session は document + fixture 方針を確定させ、別 session で PoC 実装 (C 案、0.5-1 session) を完遂する。

---

## 5. Layer 1: PostToolUse → helix job enqueue (task_queue は新設しない)

### 5.1 概要

`PostToolUse(matcher: Write|Edit|MultiEdit)` hook が PLAN.md / ADR*.md へのファイル書き込みを検出し、**候補をシステムメッセージで表示** する。実際の enqueue は **Plan Consent guard (P0) を通過した後のみ**。

### 5.2 P0 承認 guard (CRITICAL)

> TL v5 Round 5 P0 指摘: 「承認なし task pop は Plan Consent / WBS / handover Next Action を超える設計 → HELIX discipline 破壊。queue worker は必ず plan guard を通すこと」

```
PostToolUse hook 検出
      ↓
  systemMessage で「PLAN-NNN 検出、next action 候補: [XXX]」表示
      ↓
  decision: continue (ターン継続、hook は block しない)
      ↓
  PM (Opus) または handover Next Action が承認
      ↓
  helix job pending 登録 (既存 helix job 系 CLI を使う)
      ↓
  worker が claim → 実行
```

**自動 pop は候補提示まで**。承認フロー前に worker が自律実行することは禁止。

### 5.3 PLAN-088 との関係 (TL v5 補助 #7)

- `task_queue` テーブルは新設しない
- `plan_registry` = PLAN-092 が担当
- `実行待ち` = 既存 `helix job` に寄せる
- `session continuity` = 既存 handover
- `ephemeral checklist` = 既存 TodoWrite (撤廃しない)

**単一実行正本**: `plan_registry` (PLAN-092) が定義し、`helix job` が実行待ちを管理し、`handover CURRENT.json` が引き継ぎを担う。重複 state 禁止。

### 5.4 フック仕様 (実装 draft)

```bash
# .claude/hooks/posttooluse-helix-job-enqueue.sh (別 session 実装)
# PostToolUse matcher: Write|Edit|MultiEdit
# Input (stdin): JSON {tool_name, tool_input:{file_path,...}, tool_response}
# Output: decision:continue + systemMessage (enqueue 候補提示)

PLAN_PATTERN="PLAN-[0-9]+-.*\.md|ADR-[0-9]+-.*\.md"
# ファイルパスが PLAN/ADR パターンにマッチ → 候補提示
# helix job list でキュー状態を表示
# 承認 guard flag: $HELIX_JOB_CONSENT_REQUIRED (default 1、P0 guard は OR 条件: explicit_consent OR wbs_match OR handover_match)
```

### 5.5 continueOnBlock 連携 (PLAN-090 前駆)

PostToolUse で `decision:block` + `continueOnBlock:true` を設定している既存 hook (PLAN-090) と共存。  
Layer 1 hook は原則 `decision:continue` (block しない)。systemMessage 提示のみ。

---

## 6. Layer 2: statusLine context % 4 段階監視

### 6.1 4 段階定義

| 残量 | 状態 | 表示色 | アクション |
|---|---|---|---|
| > 50% | 正常 | 緑 | なし |
| 30-50% | 警告 | 黄 |「/compact 推奨」表示 |
| ≤ 30% | 危険 | 橙 | 「state 永続化実行推奨」+ handover update 促進 |
| ≤ 20% | 緊急 | 赤 | 「PreCompact block 条件チェック中」+ Stop hook 連携 |

### 6.2 debounce + hysteresis (CRITICAL)

> TL v5 修正条件 #4: 「statusLine + Stop 役割分担: statusLine に debounce + hysteresis 必須 (警告連打防止)」

```
debounce:
  - context 変化検出から 30 秒以内は同一 threshold の警告を再発しない
  - 実装: last_warned_at + threshold_level を状態として持つ

hysteresis:
  - 黄 (≤50%) に入ったら、緑 (>55%) に戻るまで黄維持 (5% gap)
  - 橙 (≤30%) に入ったら、黄 (>35%) に戻るまで橙維持 (5% gap)
  - 赤 (≤20%) に入ったら、橙 (>25%) に戻るまで赤維持 (5% gap)
  - 理由: 境界値付近での振動でユーザーに不要な警告連打を与えない
```

### 6.3 Stop 役割分担

- **Stop hook** (既存 `stop.sh` / `helix-session-summary`): 軽量化。handover snapshot / session telemetry / stale lock release のみ。threshold 監視は **statusLine** が担当
- **statusLine**: context % 監視 + 段階的警告 + debounce/hysteresis + PreCompact 条件チェック

### 6.4 フック仕様 (実装 draft)

```bash
# cli/helix-statusline (別 session 実装)
# 呼び出し: SessionStart + 定期 PostToolUse で context % を取得し状態遷移
# HELIX_STATUSLINE_DEBOUNCE_SEC=30 (default)
# HELIX_STATUSLINE_HYSTERESIS_PCT=5 (default)
# Output: HELIX_CONTEXT_PCT env / statusMessage フィールド
```

---

## 7. Layer 3: PreCompact hook で state 永続化

### 7.1 PreCompact hook 正式確認

- **追加バージョン**: Claude Code v1.0.46 (CHANGELOG 参照)
- **block 方法**: `exit 2` または `{"decision":"block"}` JSON を stdout
- **上限**: 連続 block 8 回でターン終了 (cap、`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` でオーバーライド可、v2.1.143 fix)

### 7.2 decision:block 3 条件 AND 限定 (CRITICAL)

> TL v5 修正条件 #3: 「PreCompact decision:block 制限: 3 条件 AND 限定。常用は context 枯渇継続事故リスク」

PreCompact で `decision:block` を返してよいのは **以下 3 条件すべてが成立する場合のみ**:

```
条件 1: 重要 state 永続化失敗
  → 直前の handover update / memory write が exit != 0 で失敗した
  → 証拠: .helix/handover/CURRENT.json の updated_at が古い (>5分)

条件 2: 未保存の L2/L3/ADR 判断がある
  → chat 内で設計判断が確定したが、対応する doc ファイルが未作成 / 未更新
  → 証拠: HELIX_UNSAVED_DECISIONS env flag が "1"

条件 3: 同 session 内で block が初回
  → session_id ベースの one-shot flag が未セット
  → 証拠: ~/.helix/precompact_blocked_sessions に session_id が未記録
```

**3 条件 AND** でなければ `decision:continue` + `{"message": "compact proceeding, state backed up"}` を返す。

### 7.3 通常 compact 動作 (3 条件 false 時)

```bash
# 通常ケース: backup + warning
helix handover update --note "PreCompact: state backup at $(date -u +%Y-%m-%dT%H:%MZ)"
echo '{"decision":"continue","message":"PreCompact: state backed up, compaction proceeding"}' 
# manual /compact を妨害しない
```

### 7.4 block 後の復帰

- block 後に Claude が state 永続化 (handover update + memory write) を実行
- 完了したら HELIX_UNSAVED_DECISIONS を "0" にセット
- 次の PreCompact invocation では条件 2 が false → `continue` で compact が進む

### 7.5 フック仕様 (実装 draft)

```bash
# .claude/hooks/precompact-state-snapshot.sh (別 session 実装)
# PreCompact hook: event hook
# 入力: HELIX_UNSAVED_DECISIONS / session_id 環境変数
# 出力: decision:block (3 条件 AND 時) / decision:continue (それ以外)
# state: ~/.helix/precompact_blocked_sessions (session_id one-shot flag)
```

---

## 8. Layer 4: SessionStart + UserPromptSubmit で履歴自動注入 (claude-brain HELIX 独自再実装)

### 8.1 claude-brain pattern HELIX 独自再実装 (CRITICAL)

> TL v5 修正条件 #5: 「claude-brain pattern: HELIX 独自再実装が筋。会話 SQLite 全量キャプチャは secret/PII/予算情報リスク」

**原典 claude-brain**: 6 Python hook で SQLite に会話全量キャプチャ + UserPromptSubmit で履歴注入。  
**HELIX 独自再実装**: transcript_path 参照 + 要約 state + 明示的 retention。

```
全量 SQLite キャプチャ    ← 禁止 (secret/PII/予算情報リスク = 人間確認対象)
           ↓
transcript_path 参照     ← 許可 (Claude Code が提供する公式パス)
要約 state 別 file 保存   ← 許可 (要約のみ、raw 会話は保存しない)
明示的 retention 設定     ← 必須 (default 7日、人間設定可)
```

### 8.2 SessionStart hook 動作

```
SessionStart イベント受信
  event.session_type == "cleared" または "compacted"
      ↓
  transcript_path から直前の compact 前 state を読む (要約のみ)
      ↓
  関連 PLAN / handover Next Action / memory feedback の bundle 生成
  bundle サイズ上限: ~500 token 以下 (短い bundle に制限)
      ↓
  systemMessage に bundle を注入 (UserPromptSubmit でも同様)
```

### 8.3 UserPromptSubmit hook 動作

```
UserPromptSubmit イベント受信
  ユーザープロンプト受信時
      ↓
  キーワードマッチ (PLAN-NNN / handover / carry / 継続) で関連 state を特定
      ↓
  top-N bundle (N ≤ 5 件) を生成
  bundle サイズ上限: ~500 token 以下
      ↓
  additionalContext に bundle を追加
```

### 8.4 retention ポリシー

```yaml
# cli/lib/transcript_summary.py 設定 (別 session 実装)
retention_days: 7          # default、人間が設定可能
max_bundle_tokens: 500     # UserPromptSubmit 注入上限
summary_only: true         # raw 会話保存禁止
sensitive_fields:          # 除外フィールド (PII/secret/認証情報)
  - api_key
  - credential
  - password
  - bearer_token
  - pii_*
auto_purge: true           # retention_days 経過後自動削除
```

### 8.5 secret/PII 取扱い

- transcript_path の raw 会話を SQLite に全量保存することは **禁止**
- 要約スクリプト (`transcript_summary.py`) は sensitive_fields を除外してから要約
- 要約内容に secret が含まれると判定した場合 (正規表現マッチ) は保存をスキップし警告
- **このポリシーは人間確認対象**: retention 日数 / sensitive_fields の設定変更は PM 承認必須

### 8.6 フック仕様 (実装 draft)

```bash
# .claude/hooks/sessionstart-history-injection.sh (別 session 実装)
# SessionStart: event hook (command type)
# 入力: HELIX_SESSION_TYPE (cleared/compacted/new)、transcript_path
# 処理: transcript_summary.py で要約 → bundle 生成 → systemMessage
# cli/lib/transcript_summary.py: 要約 + retention 管理 + secret 除外
```

---

## 9. Layer 5: ScheduleWakeup adaptive heartbeat

### 9.1 adaptive interval

> TL v5 補助 #8: 「15min heartbeat: adaptive (通常 15min / 低予算 30min / critical/hotfix 5min / active task 中無効)。固定値禁止」

| 状況 | interval | 条件 |
|---|---|---|
| 通常 | 15 min | budget 正常 + carry > 0 + bg task なし |
| 低予算 | 30 min | budget ≤ 30% |
| critical / hotfix | 5 min | HELIX_PHASE=critical または hotfix |
| active task 中 | 無効 | bg task 実行中 (run_in_background active) |
| carry 0 | 停止 | carry == 0 AND 時間枠満了 |

### 9.2 発火条件 (CLAUDE.md §ScheduleWakeup 運用ルール準拠)

```
carry > 0                 (残タスクあり)
AND bg task なし          (run_in_background active がない)
AND budget healthy        (Opus 残量 > 20%)
AND ユーザー時間枠内      (「N 時間連続」「24 時まで」等の明示指示がある場合)
```

**外れたら**: carry 0 または時間枠満了または budget 枯渇 → ScheduleWakeup をセットしない。  
**ScheduleWakeup の用途確認**: harness 追跡外の外部状態 polling 専用 (GitHub Actions / CI / リモートデプロイ)。  
carry heartbeat はこの「外部状態 polling」に準ずるもの (HELIX harness が知らない session 間隔の管理)。

### 9.3 carry check ロジック

```bash
# cli/helix-heartbeat-scheduler (別 session 実装)
# 1. helix handover status --json で carry 確認
# 2. helix budget status で残量確認
# 3. 条件マッチで next ScheduleWakeup を設定
# 4. carry > 0 なら「継続作業: [Next Action top-1]」を systemMessage 表示
# 5. Plan Consent guard: carry pop は候補提示のみ、自動実行禁止 (P0)
```

### 9.4 P0 guard (CRITICAL)

> TL v5 P0 指摘と同じ: queue worker (heartbeat で起動する carry worker) は **Plan Consent guard を必ず通す**。  
> heartbeat は「carry あり → 候補提示 → PM 承認 → 実行」の順。自律 pop 禁止。

---

## 10. 単一実行正本決定との整合 (TL v5 P1)

> TL v5 P1 指摘: 「task_queue / TodoWrite / helix job / handover が競合する恐れ → 単一の実行正本を決める」

### 10.1 役割分担 (確定)

| 概念 | 担当 | 備考 |
|---|---|---|
| PLAN 定義 (永続) | `plan_registry` (PLAN-092 担当) | helix.db に永続、PLAN-099 は依存するのみ |
| 実行待ちキュー | 既存 `helix job` | task_queue 新設なし (TL v5 補助 #7) |
| session 引き継ぎ | `handover CURRENT.json` | 既存 handover CLI を使う |
| ephemeral checklist | 既存 `TodoWrite` | 廃止しない (ephemeral は TodoWrite の責務) |
| context / session 状態 | 本 PLAN (Layer 1-5) | runtime substrate として追加 |

### 10.2 競合解消ルール

1. PLAN 定義は `plan_registry` (PLAN-092) が正本。本 PLAN の PostToolUse hook は `plan_registry` への候補提示のみ
2. carry の実行権は `handover Next Action` が持つ。heartbeat は候補を提示し、PM 承認後に `helix job` 経由で実行
3. TodoWrite は ephemeral checklist のまま維持。carry の永続化は handover / plan_registry を使う
4. PLAN-088 (TodoWrite × agent slot) の role_assignment との衝突: agent_slots は PLAN-091 frontmatter が正本、TodoWrite 上の assign は補助的 UI のみ

---

## 11. テスト戦略 (fixture 方針、本 session 確定)

> 本実装前にテスト戦略を文書固定する (V-model TDD 原則、TL v5 修正条件 #13)。  
> fixture 実装ファイル: `cli/lib/tests/test_5layer_fixtures.py` (別 session)

### 11.1 fixture 一覧

| fixture | Layer | 検証内容 |
|---|---|---|
| `fake_transcript` | Layer 4 | SessionStart cleared/compacted 後の bundle 注入 snapshot test |
| `fake_handover` | Layer 4, 5 | carry > 0 / carry 0 境界テスト |
| `fake_carry` | Layer 5 | budget low / critical / active task 中の no-op 検証 |
| `fake_timer` | Layer 5 | adaptive interval: 5min / 15min / 30min 遷移検証 |
| `fake_precompact_session` | Layer 3 | one-shot block flag (同 session 内多重 block 禁止) |
| `fake_sensitive_transcript` | Layer 4 | secret 除外ロジック (api_key / credential 含む会話) |

### 11.2 ケース一覧 (最小 PoC)

```
[Layer 1]
T1-001: PLAN.md 書き込み → systemMessage で候補提示 (decision:continue)
T1-002: ADR.md 書き込み → 同上
T1-003: 非 PLAN ファイル書き込み → 候補提示なし
T1-004: queue atomic claim (並列 worker 競合解消、helix job claim)

[Layer 2]
T2-001: context 51% → 警告なし
T2-002: context 49% → 黄警告
T2-003: context 49% → 31% 推移 → debounce 30s 内は再警告なし
T2-004: context 49% → 51% → 46% → hysteresis gap で黄維持
T2-005: context 29% → 橙警告
T2-006: context 19% → 赤警告

[Layer 3]
T3-001: 3 条件 AND → decision:block
T3-002: 条件 1 false (handover 成功) → decision:continue
T3-003: 条件 2 false (HELIX_UNSAVED_DECISIONS=0) → decision:continue
T3-004: 条件 3 false (session 内 2 回目) → decision:continue (one-shot 強制)
T3-005: block 後 state 永続化完了 → 次 invocation は continue

[Layer 4]
T4-001: SessionStart cleared → bundle 注入 (≤500 token)
T4-002: SessionStart compacted → bundle 注入 (≤500 token)
T4-003: SessionStart new → bundle 注入なし
T4-004: sensitive_fields 含む transcript → 除外後に要約
T4-005: retention 7日 経過 → purge
T4-006: UserPromptSubmit で keyword match → top-5 注入

[Layer 5]
T5-001: carry > 0 + budget 正常 → 15min heartbeat set
T5-002: carry > 0 + budget ≤ 30% → 30min heartbeat set
T5-003: carry > 0 + HELIX_PHASE=critical → 5min heartbeat set
T5-004: carry > 0 + bg task active → heartbeat 無効 (no-op)
T5-005: carry 0 → heartbeat 停止
T5-006: 時間枠満了 → heartbeat 停止
T5-007: heartbeat wake → 候補提示のみ (自動実行禁止、P0 guard)
```

### 11.3 hook timeout test

各 Layer hook は 5 秒以内に応答必須 (settings.json timeout: 5):

```
T6-001: posttooluse-helix-job-enqueue.sh → ≤ 5s で decision 返却
T6-002: precompact-state-snapshot.sh → ≤ 5s で decision 返却
T6-003: sessionstart-history-injection.sh → ≤ 5s (SessionStart timeout: 5)
T6-004: helix-statusline → ≤ 5s
```

---

## 12. 関連 PLAN の obsolete/superseded 明記 (CRITICAL)

> tl-advisor Round 5 補助 #6 + デグレ禁止制約: 既存 doc は編集しない。本 PLAN 内で superseded 範囲を明記。

### 12.1 PLAN-081 (Stop-hook auto handover)

**状態**: `superseded (partial) by PLAN-099`

| PLAN-081 範囲 | 本 PLAN での扱い |
|---|---|
| Stop hook で handover snapshot | 維持 (Layer 3 PreCompact に移管・拡張) |
| compact recommendation (systemMessage) | Layer 2 statusLine が引き継ぎ |
| compacted 後の SessionStart 復帰 | Layer 4 が拡張実装 |

**superseded 範囲**: PLAN-081 §3.3 (compact recommendation の systemMessage 部分) は Layer 2 に移管。  
**共存範囲**: PLAN-081 §3.1 (Stop hook auto handover snapshot) は引き続き有効 (既存 stop.sh を使う)。

PLAN-081 doc 自体は **編集しない**。本 PLAN のこのセクションが正本。

### 12.2 PLAN-082 (subagent sprint mechanization)

**状態**: `shared (co-exist with PLAN-099)`

- PLAN-082: subagent 層 (agent_slots / mandatory subagent fire / sprint 標準 8 ステップ)
- PLAN-099: runtime substrate 層 (session continuity / context 監視 / carry 自動検出)
- 競合なし。PLAN-082 の sprint mandatory は Layer 1 の task-queue candidate として扱える。

### 12.3 PLAN-083 (harness auto integration)

**状態**: `shared (co-exist with PLAN-099)`

- PLAN-083: plan 自動統合層 (PreToolUse で agent_slots auto-fire / PLAN 自動登録 hook)
- PLAN-099: runtime substrate 層 (context 監視 / heartbeat / history injection)
- 競合なし。PLAN-083 の PostToolUse が Layer 1 の upstream として機能。

---

## 13. 段階導入 (P1 → P2 → P3)

| Phase | scope | session | 条件 |
|---|---|---|---|
| P1 (本 session) | document + fixture 方針確定 | 1 session | PLAN-099 + ADR-032 起票完了 |
| P2a (別 session) | Layer 4+5 PoC (C 案) | 0.5-1 session | Layer A/B 確定前に並行可能 |
| P2b (別 session) | Layer 1-3 本実装 | 1-2 session | PLAN-091 (Layer A) + PLAN-092 (Layer B) 確定後 |
| P3 (別 session) | statusLine + PreCompact fail-close 化 | 1 session | P2 全完遂後 |

### 13.1 P2a PoC C 案 (Layer 4+5 先行) 選択理由

> TL v5 修正条件 #2: 「PoC 戦略: C 案 = Layer 4 + Layer 5 を先行 PoC (0.5-1 session)」

- Layer 4: 既存 SessionStart hook (sessionstart-harness-summary.sh) を拡張し、transcript_path 参照 + bundle 注入を追加
- Layer 5: 既存 ScheduleWakeup 運用ルールを heartbeat CLI に実装、carry check を自動化
- Layer A (frontmatter 語彙) / Layer B (DB schema) の確定を待たずに作れる
- A 案 (全 layer 一括 2-3 session) / B 案 (段階的 4-6 session) は非効率 → 棄却

### 13.2 feature flag / warn-only / fail-close 段階

> TL v5 修正条件 #1 (設計選択): 「feature flag / warn-only / fail-close 段階導入」

```
P2a: feature flag OFF (default)、opt-in で PoC 動作
P2b: warn-only (block なし、systemMessage 候補提示のみ)
P3:  fail-close (block 有効、P0 guard = OR 条件 [explicit_consent OR wbs_match OR handover_match]、PreCompact decision:block は別概念で 3 条件 AND 限定)
```

---

## 14. DoD (完了条件)

### 14.1 本 session (P1) DoD

- [x] PLAN-099 文書起票 (本 file)
- [x] ADR-032 文書起票 (別 file)
- [x] 業界 standard 参照 (Web 検索 3 query + Sources URL)
- [x] TL v5 修正条件 5 重要 + 8 補助 + P0 + P1 全件反映 (本 PLAN §内で証跡)
- [x] fixture 方針確定 (§11 テスト戦略、30+ ケース)
- [x] 関連 PLAN superseded/co-exist 明記 (§12)
- [x] 段階導入方針確定 (§13)

### 14.2 別 session (P2a) DoD

- [ ] Layer 4 PoC hook 実装 (sessionstart-history-injection.sh)
- [ ] Layer 5 PoC CLI 実装 (helix-heartbeat-scheduler)
- [ ] transcript_summary.py skeleton (secret 除外ロジック込み)
- [ ] test_5layer_fixtures.py Layer 4-5 PoC ケース PASS (T4-001〜006 + T5-001〜007)
- [ ] 既存 hook 回帰 (stop.sh / sessionstart-harness-summary.sh デグレなし)

### 14.3 別 session (P2b) DoD

- [ ] Layer 1 hook (posttooluse-helix-job-enqueue.sh)
- [ ] Layer 2 CLI (helix-statusline + debounce/hysteresis)
- [ ] Layer 3 hook (precompact-state-snapshot.sh + one-shot flag)
- [ ] 全 T1〜T6 ケース PASS
- [ ] PLAN-091 frontmatter 語彙との整合確認 (generates field)
- [ ] PLAN-092 helix.db schema との整合確認 (plan_registry 連携)

---

## 15. V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §5-9 Layer 1-5 設計 |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-099-unit-test-design.md (別 session 起票予定)。本 PLAN §11 はテスト戦略概要のみ (fixture 方針 + 30+ ケース概要) |
| ② 実装コード | 別 session (P2a/P2b) で実装 |
| ④ テストコード | `cli/lib/tests/test_5layer_fixtures.py` (別 session) |

双方向 trace:
- 本 PLAN → テスト設計: §11 にケース一覧記載
- テスト設計 → 本 PLAN: テストコード docstring に「PLAN-099 §11 T{N}-{NNN}」明記 (別 session)
- テスト設計 → テストコード: fixture class 名で対応 (別 session)

---

## 16. 関連リンク

| 文書 | パス |
|---|---|
| ADR-032 (本 PLAN の L2 snapshot) | docs/adr/ADR-032-autonomous-runtime-framework-decision.md |
| PLAN-MM-001 (親設計) | docs/plans/PLAN-MM-001-v5-framework-master-plan.md |
| PLAN-091 (Layer A 正本) | docs/plans/PLAN-091-v5-framework-core.md |
| PLAN-090 (active guidance loop 前駆) | docs/plans/PLAN-090-posttooluse-continueonblock-refactor.md |
| PLAN-081 (superseded partial) | docs/plans/PLAN-081-stop-hook-auto-handover.md |
| PLAN-082 (co-exist) | docs/plans/PLAN-082-subagent-sprint-mechanization.md |
| PLAN-083 (co-exist) | docs/plans/PLAN-083-harness-auto-integration.md |
| 既存 settings.json hook 設定 | .claude/settings.json |
| CLAUDE.md §ScheduleWakeup 運用ルール | CLAUDE.md |
| memory: carry 残し禁止 | .claude/agent-memory/pmo-sonnet/feedback_dont_stop_with_carry_remaining.md |
