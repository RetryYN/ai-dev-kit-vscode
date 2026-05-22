---
plan_id: PLAN-111
title: PreCompact hook 実装 (V5 Layer 3、auto-compact 前 state 永続化)
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — decision:block 3 条件 AND 境界判断・one-shot flag 設計承認"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — 3 条件 AND logic・one-shot flag・GC 設計 review"
  - role: se
    slot_label: "SE — precompact-state-snapshot.sh 実装・bats test 実装"
  - role: qa
    slot_label: "QA — fake fixture test 全ケース検証・hook timeout 確認"
generates:
  - artifact_type: hook
    path: .claude/hooks/precompact-state-snapshot.sh
  - artifact_type: config
    path: .claude/settings.json
  - artifact_type: test
    path: .claude/hooks/tests/test_precompact_hook.bats
  - artifact_type: design_doc
    path: docs/plans/PLAN-111-precompact-hook-state-snapshot.md
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-038-precompact-hook-decision.md
dependencies:
  requires:
    - PLAN-099
  blocks: []
  parent: PLAN-099
related_adr:
  - ADR-032
  - ADR-038
acceptance_criteria:
  - "bash -n .claude/hooks/precompact-state-snapshot.sh PASS"
  - "bats test 全 5 ケース PASS (T3-001〜T3-005、PLAN-099 §11.2 準拠)"
  - "3 条件 AND 成立時のみ decision:block を返し、それ以外は decision:continue"
  - "one-shot flag (.helix/precompact_blocked_sessions) が session 内 2 回目の block を防ぐ"
  - "snapshot GC: .helix/precompact-snapshot/ 配下に最大 5 件保持、古いものは自動削除"
  - "hook timeout ≤ 5 秒 (T6-002 ケース)"
  - "manual /compact を妨害しないこと (3 条件 false 時は decision:continue)"
  - "ADR-038 起票 (L2 大局判断 snapshot)"
  - "helix doctor pass/fail/warn カウント維持 (regression なし)"
---

# PLAN-111: PreCompact hook 実装 (V5 Layer 3)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-038** で凍結 (起票予定):

- PreCompact hook 採用判断 (Claude Code v1.0.46 正式追加、CHANGELOG 確認済)
- decision:block の 3 条件 AND 限定 (TL v5 修正条件 #3 遵守)
- one-shot flag による無限ループ防止設計 (`.helix/precompact_blocked_sessions` per-session)
- snapshot GC 方針 (最大 5 件保持、FIFO)
- 通常 compact 時の backup + warning 経路 (decision:continue + handover update)

## 背景

**PLAN-099 (V5 自動走行 framework 5-layer)** の Layer 3 担当 PLAN。

PLAN-099 §7 で設計を確定済み:
- Layer 3 = `PreCompact hook で auto-compact 前 state 永続化、必要時 decision:block`
- 実装スコープは PLAN-099 の P2b (別 session 本実装) に分類
- 本 PLAN はその実装 PLAN として独立起票

**課題 (PLAN-099 §1 より)**:
- context 枯渇時に auto-compact が発火しても state が消失し、session restart 後に carry が再現できない
- 解決: PreCompact hook が compact 直前に handover snapshot を強制更新し、重要判断が存在する場合のみ compact を一時阻止

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (PreCompact hook + decision:block 設計) を含むため、PLAN-087 ガード対象。PLAN-099 §3 で実施済の WebSearch 3 query を parent として継承し、以下の key evidence を引用する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code PreCompact hook state preservation 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG v1.0.46) | PreCompact hook が v1.0.46 (= 2.1.105) で正式追加、`decision:block` で compact を一時阻止可能、8 回連続 block でターン終了 cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) 導入済み (v2.1.143 fix) |
| "Claude Code hook decision block continueOnBlock exit code specification 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.139 / 2.1.143) | exit 2 = fail-close block。continueOnBlock は PostToolUse 専用 (reject reason を返してターン継続)。PreCompact は `{"decision":"block"}` JSON stdout で compact 阻止 |
| "context window compaction state persistence pattern agent session 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.141) | `transcript_path` が SessionStart/hook で提供。claude-brain 型全量 SQLite キャプチャは secret/PII リスク → HELIX は要約 state + 明示的 retention の独自再実装で対応 |

## 業界 standard 参照

- Claude Code CHANGELOG v1.0.46: https://github.com/anthropics/claude-code/releases (PreCompact hook 正式追加)
- Claude Code CHANGELOG v2.1.143: https://github.com/anthropics/claude-code/releases (CLAUDE_CODE_STOP_HOOK_BLOCK_CAP 導入)
- Claude Code CHANGELOG v2.1.141: https://github.com/anthropics/claude-code/releases (transcript_path の SessionStart 提供確認)
- HELIX PLAN-099 §3/§7: parent PLAN の設計根拠 (本 PLAN は §7 仕様を実装する)

## 設計方針 (TL v5 round 5 修正条件 遵守)

CLAUDE.md §TL v5 round 5 修正条件 を厳密遵守する。特に修正条件 **#3 (PreCompact decision:block 制限)** が本 PLAN の核心:

> 「PreCompact decision:block 制限: `重要 state 永続化失敗` AND `未保存の L2/L3/ADR 判断がある` AND `一回だけ`」に限定。常用は context 枯渇継続事故リスク、通常は backup + warning」

### 3 条件 AND 判定 (CRITICAL)

PLAN-099 §7.2 を実装根拠として引用。decision:block を返してよいのは **以下 3 条件すべてが成立する場合のみ**:

```
条件 1: 重要 state 永続化失敗
  検証: .helix/handover/CURRENT.json の updated_at が現在時刻から >5 分古い
  実装: stat + date コマンドで age 計算

条件 2: 未保存の L2/L3/ADR 判断がある
  検証: HELIX_UNSAVED_DECISIONS 環境変数 == "1"
  設定タイミング: PM (Opus) が設計判断確定時に手動セット、または設計 doc Write 完了時に自動クリア

条件 3: 同 session 内で block が初回
  検証: ~/.helix/precompact_blocked_sessions に session_id が未記録
  実装: grep で session_id file 存在確認
```

**3 条件 AND** でなければ:

```bash
# 通常ケース: state backup + warning + decision:continue
helix handover update --note "PreCompact: state backup at $(date -u +%Y-%m-%dT%H:%MZ)"
echo '{"decision":"continue","message":"PreCompact: state backed up, compaction proceeding"}'
```

### one-shot flag 設計

```
block 発生時: echo "<session_id>" >> ~/.helix/precompact_blocked_sessions
block 判定時: grep -qF "$SESSION_ID" ~/.helix/precompact_blocked_sessions && 条件 3 = false
GC: 7 日以上古いエントリを自動削除 (cron 不要、hook 内で起動時に実行)
```

これにより同 session 内で **2 回以上の block が発生しない** (TL v5 修正条件 #3「一回だけ」を厳守)。

### snapshot 設計

```
保存先: .helix/precompact-snapshot/<timestamp>-<session_id_short>.json
内容:
  - handover CURRENT.json のコピー
  - HELIX_UNSAVED_DECISIONS フラグ値
  - 実行中 PLAN IDs (helix plan status --json から抽出)
  - 保存タイムスタンプ
GC: .helix/precompact-snapshot/ 配下を mtime 降順でソートし、6 件目以降を削除
```

### Stop hook との役割分担

- **Stop hook** (既存 stop.sh): handover auto snapshot / session telemetry / stale lock release
- **PreCompact hook** (本 PLAN): compact 直前の state backup + 必要時 decision:block
- 重複しない。Stop は session 終了時、PreCompact は context 圧縮直前

## 実装計画

### Sprint .1: 3 条件 AND 判定 + snapshot 書き込み (Codex se 委譲)

**対象ファイル**: `.claude/hooks/precompact-state-snapshot.sh` (新規)

実装内容:
- `detect_session_id()` 関数 (PLAN-101 の fallback chain 実装を参照)
- `check_condition_1()`: handover updated_at age 計算
- `check_condition_2()`: HELIX_UNSAVED_DECISIONS 環境変数確認
- `check_condition_3()`: one-shot flag ファイル確認
- `write_snapshot()`: .helix/precompact-snapshot/ へ JSON 書き込み
- `gc_snapshots()`: 古い snapshot GC (6 件目以降削除 + 7 日経過 flag エントリ削除)
- メインロジック: 3 条件 AND 分岐

mandatory in sprint:
- `bash -n .claude/hooks/precompact-state-snapshot.sh` PASS

### Sprint .2: settings.json hook 登録 + one-shot flag 管理 (Codex se 委譲)

**対象ファイル**: `.claude/settings.json` (Edit)

実装内容:
- PreCompact hook 登録 (matcher: PreCompact、timeout: 5)
- 既存 hooks 配列への追加 (append のみ、他 hook を変更しない)
- session_id 取得は HELIX_SESSION_ID → stdin payload → CLAUDE_SESSION_ID の優先順 (PLAN-101 pattern)

mandatory in sprint:
- settings.json の JSON syntax 確認 (`python3 -c "import json; json.load(open('.claude/settings.json'))"`)
- 既存 hook 回帰 (pretooluse-design-doc-web-search-guard.sh 等が引き続き動作)

### Sprint .3: fake fixture bats test 実装 + DoD 確認 (Codex qa 委譲)

**対象ファイル**: `.claude/hooks/tests/test_precompact_hook.bats` (新規)

テストケース (PLAN-099 §11.2 T3-001〜T3-005 + T6-002 完全準拠):

| ケース | 内容 |
|---|---|
| T3-001 | 3 条件 AND 成立 → decision:block が stdout に出力される |
| T3-002 | 条件 1 false (handover 更新済、1 分以内) → decision:continue |
| T3-003 | 条件 2 false (HELIX_UNSAVED_DECISIONS=0) → decision:continue |
| T3-004 | 条件 3 false (同 session 内 2 回目) → decision:continue (one-shot 強制) |
| T3-005 | block 後に HELIX_UNSAVED_DECISIONS=0 セット → 次 invocation は continue |
| T6-002 | hook 実行時間 ≤ 5 秒 (time コマンドで計測) |

fake fixture 方針:
- `HELIX_HOME` を `$BATS_TMPDIR/helix_home_<test>` に向ける
- fake handover CURRENT.json を `updated_at` を操作して作成 (条件 1 テスト用)
- `HELIX_UNSAVED_DECISIONS` を env で直接制御
- fake session_id = "test-session-001" (one-shot flag テスト用)

mandatory in sprint:
- `bats .claude/hooks/tests/test_precompact_hook.bats` 全 6 ケース PASS
- `python3 -m py_compile` で Python 補助スクリプトがある場合 PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit 時、本 PLAN が G4 相当)

## DoD (Definition of Done)

- [ ] `bash -n .claude/hooks/precompact-state-snapshot.sh` PASS
- [ ] bats test 全 6 ケース PASS (T3-001〜T3-005 + T6-002)
- [ ] 3 条件 AND のみ decision:block、それ以外は decision:continue (smoke 確認)
- [ ] one-shot flag が session 内 2 回目 block を防ぐ (T3-004 PASS)
- [ ] snapshot GC が .helix/precompact-snapshot/ 配下を 5 件以下に保つ
- [ ] settings.json hook 登録 PASS (JSON syntax valid)
- [ ] 既存 hook 回帰なし (pretooluse / posttooluse / sessionstart 系が影響を受けない)
- [ ] hook timeout ≤ 5 秒 (T6-002 PASS)
- [ ] ADR-038 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §実装計画 Sprint .3 ケース一覧 (T3-001〜T3-005 + T6-002) |
| ② 実装コード | .claude/hooks/precompact-state-snapshot.sh (Sprint .1-.2 で実装) |
| ④ テストコード | .claude/hooks/tests/test_precompact_hook.bats (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T3/T6 番号明記
- テストコード → 設計: bats test の `# PLAN-111 T3-001` コメントで対応付け (Sprint .3 実装時)
- テスト設計 → テストコード: bats describe 名称で T3-NNN 対応 (Sprint .3 実装時)

## carry / 学び (起票時記録)

- **session_id 取得の fallback chain**: PLAN-101 が確立した 5 段優先順位を参照。同じ pattern を再実装しないこと
- **HELIX_UNSAVED_DECISIONS のセットタイミング**: 自動化前は PM (Opus) が手動でセット。Layer 1 PostToolUse hook (PLAN-099 §5) が自動化する予定だが、本 PLAN 実装時点では手動運用で許容
- **GC の実行タイミング**: PreCompact hook 内で起動時に GC を走らせる。重い処理は Stop hook 側に任せる方針 (TL v5 修正条件 #4 役割分担)
- **manual /compact との共存**: 3 条件 false 時は必ず decision:continue を返し、ユーザーの意図的 /compact を妨害しない

## 関連 reference

- PLAN-099 §7 (Layer 3 設計、本 PLAN の実装根拠)
- PLAN-099 §11.2 (テストケース T3-001〜T3-005 + T6-002)
- PLAN-101 (session_id fallback chain pattern)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-038 (本 PLAN の L2 snapshot、起票予定)
- [[feedback_design_doc_hook_session_id_missing_block]] (session_id 取得の関連 feedback)
- [[feedback_dont_stop_with_carry_remaining]] (context 枯渇による中断課題の背景)
- CLAUDE.md §TL v5 round 5 修正条件 (設計方針の根拠)
