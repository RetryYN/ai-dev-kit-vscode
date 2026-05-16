---
plan_id: PLAN-081
title: "PLAN-081: Stop-hook auto handover + compact recommendation"
status: completed_phase1
size: M
drive: be
created: 2026-05-17
owner: PM
phases: L1, L2, L3, L4
gates: G1, G2, G3, G4
related_plans:
  - PLAN-080 (Harness Dynamic Monitoring、同じく harness 強化系)
  - PLAN-075 (V-model 4 artifact 双方向 trace、context 切れ対策の起点)
related_memories:
  - feedback_claude_code_compact_hook (Claude Code hook 仕様確認、2026-05-17)
---

# PLAN-081: Stop-hook auto handover + compact recommendation

## 1. 背景

### 1.1 起点 (本セッションで顕在化)

- 2026-05-17 PLAN-075 完遂セッションで「context が厳しい」発言を 5 回程度繰り返したが、auto-compact は実際 fire しておらず、根拠なき自己保護発言だった (memory [[claude-context-tight-without-basis]] 候補)
- ユーザー指摘: 「コンテキストが厳しいって毎回言っているけどそれは本当なの？オートコンパクトも出てないし」
- /compact 手動実行も 500 Internal Server Error で失敗、セッション継続を強制された
- 結果: PLAN-075 Phase 5 を Opus 直接実装 + handover memo 一切なし + 次セッションの引き継ぎ root が不在

### 1.2 Claude Code hook 仕様 (claude-code-guide 確認済、memory [[claude-code-compact-hook]])

Claude Code 公式 hook 8 種:
- `SessionStart` / `SessionEnd`
- `UserPromptSubmit`
- `Stop` / `StopFailure`
- `PreToolUse` / `PostToolUse`
- `PermissionRequest`

**PreCompact / OnContextLimit hook は存在しない**。`/compact` は内部コマンドで shell から発火する API もない。

### 1.3 半自動アプローチ (現実解)

| 機構 | 実装可否 | 方式 |
|---|---|---|
| auto-compact 発火 | × | Claude Code 内部、外部から制御不可 |
| Stop hook | ◯ | `~/.claude/hooks/stop.sh` で handover dump 自動実行 |
| systemMessage 注入 | ◯ | Stop hook script の stdout が systemMessage として表示される |
| context 残量取得 | △ | tokens 直接取得 API なし、msg count + 推定で代用 |

## 2. 目的

Stop hook を用いて以下を半自動化:
1. **handover dump 自動化**: ユーザーが turn 終了する直前に `.helix/handover/CURRENT.json` を自動更新 (現タスク + 進捗 + 残 carry を機械抽出)
2. **compact 推奨表示**: msg count + 推定 token 利用率が threshold 超過時に「context X%、/compact 推奨」を systemMessage として表示
3. **next-session boot 補助**: 次回 SessionStart hook で handover/CURRENT.json を自動 Read、Opus に context 注入

## 3. スコープ

### 3.1 in-scope (M サイズ想定)

- `~/.claude/hooks/stop.sh` 新規 (handover dump + compact 推奨 stdout)
- `cli/lib/handover_auto_dump.py` 新規 (機械抽出 logic: git log diff + todo list + last 5 user msg)
- `~/.claude/hooks/session-start.sh` 拡張 (handover/CURRENT.json を Read → systemMessage 注入)
- `helix harness recommend-compact` CLI 新規 (現セッション msg count 監視、推奨判定)

### 3.2 out-of-scope

- `/compact` の自動実行 (技術的に不可)
- token 正確取得 (Claude Code API なし、推定値で代用)
- PreCompact hook 実装 (上流 Anthropic が hook 追加を待つ)

## 4. Phase 構成 (5 Phase 想定)

- Phase 1: 設計 (L1-L2、stop.sh + handover_auto_dump.py の I/O 仕様)
- Phase 2: 実装 (L3-L4、stop.sh + handover_auto_dump.py + helix harness recommend-compact)
- Phase 3: 統合 (session-start.sh 拡張 + handover/CURRENT.json schema 更新)
- Phase 4: テスト (pytest + bats、Stop hook fire 検証)
- Phase 5: 過去 stop 機構との互換性確認 + commit

## 4.5 V-model 4 artifact (PLAN-075 準拠、Phase 1 完遂版)

| Artifact | 担当層 | パス |
|---|---|---|
| ① 設計 | L3 詳細設計 | docs/v2/L3-detailed-design/D-CONCEPT.md (補完: PLAN-081 §2-§4 が機能設計を兼ねる) |
| ② 実装コード | L4 実装 | cli/lib/handover_auto_dump.py + cli/helix-stop-hook + cli/helix-harness (recommend-compact / auto-dump subcommand) |
| ③ テスト設計 | L4 設計 | docs/v2/L4-test-design/PLAN-081-phase4-test-design.md (Phase 4 carry) |
| ④ テストコード | L4 実装 | cli/lib/tests/test_handover_auto_dump.py (Phase 4 carry、現状 Phase 1 完遂時は動作確認のみ) |

Phase 1 完遂状態では ③ ④ は Phase 4 carry。implementation 動作確認は手動 (`cli/helix-stop-hook` 単独実行 → handover/CURRENT.json revision +1)。Phase 4 着手時に正式 V-model 4 artifact を完備する。

## 5. 受入条件

- `Stop` 時に handover dump 自動実行 (失敗時も session 継続)
- systemMessage に「Context X% (推定)、/compact 推奨」を threshold 70% 超過時に表示
- 次セッション SessionStart で handover/CURRENT.json を Read、Opus が直前タスクを把握可能
- pytest + bats 全 PASS

## 6. 関連メモリ

- [[claude-code-compact-hook]] (hook 仕様確認)
- [[helix-context-tight-without-basis]] (本セッション失敗の起点)

## 7. carry

- 次セッションで Phase 1 設計から着手
- PLAN-080 (Harness Dynamic Monitoring) と類似領域だが、PLAN-080 は 3 軸 Pull/Push/Audit、本 PLAN は Stop hook 単機能特化で別 PLAN として並走可能
