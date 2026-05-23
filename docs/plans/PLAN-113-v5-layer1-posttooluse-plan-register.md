---
plan_id: PLAN-113
title: "PostToolUse PLAN.md auto-register + task_queue auto-enqueue (V5 Layer 1)"
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md   # from dependencies.parent
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
    slot_label: "PM — P0 承認 guard 境界判断・task_queue 新設禁止方針承認・単一実行正本確定"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — hook 設計 review・plan guard logic・helix job 競合解消確認"
  - role: se
    slot_label: "SE — posttooluse-plan-registry-sync.sh 実装・settings.json 登録・bats test 実装"
  - role: qa
    slot_label: "QA — fake fixture test 全ケース検証・hook timeout 確認・plan guard smoke"
generates:
  - artifact_type: hook
    artifact_path: .claude/hooks/posttooluse-plan-registry-sync.sh
  - artifact_type: config
    artifact_path: .claude/settings.json
  - artifact_type: test
    artifact_path: .claude/hooks/tests/test_posttooluse_plan_registry.bats
  - artifact_type: design_doc
    artifact_path: docs/plans/PLAN-113-v5-layer1-posttooluse-plan-register.md
  - artifact_type: adr_snapshot
    artifact_path: docs/adr/ADR-040-v5-layer1-posttooluse-plan-register-decision.md
dependencies:
  parent: PLAN-099
  requires:
    - PLAN-099
    - PLAN-091
    - PLAN-116
  blocks: []
related_adr:
  - ADR-032
  - ADR-040
acceptance_criteria:
  - "bash -n .claude/hooks/posttooluse-plan-registry-sync.sh PASS"
  - "bats test 全 4 ケース PASS (T1-001〜T1-004、PLAN-099 §11.2 準拠)"
  - "PLAN.md / ADR*.md 書き込み時に systemMessage で候補提示、decision:continue を返す"
  - "非 PLAN ファイル書き込み時は候補提示なし (T1-003)"
  - "plan guard: HELIX_JOB_CONSENT_REQUIRED=1 (default) 時は自動 enqueue 禁止、候補提示のみ"
  - "queue atomic claim: 並列 worker 競合解消 (T1-004)"
  - "hook timeout ≤ 5 秒 (T6-001 ケース)"
  - "ADR-040 起票 (L2 大局判断 snapshot)"
  - "helix doctor pass/fail/warn カウント維持 (regression なし)"
---

# PLAN-113: PostToolUse PLAN.md auto-register + task_queue auto-enqueue (V5 Layer 1)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-040** で凍結 (起票予定):

- PostToolUse hook による PLAN.md 書き込み検出 + candidate systemMessage 表示採用判断
- task_queue 新設禁止・既存 `helix job` を実行待ちキューとして継続使用する設計選択
- P0 承認 guard (OR 条件: explicit_consent OR wbs_match OR handover_match) の採用
- 単一実行正本 (plan_registry: PLAN-092 / 実行待ち: helix job / 引き継ぎ: handover) の確定
- continueOnBlock との共存設計 (Layer 1 hook は decision:continue 専用)

## 背景

**PLAN-099 (V5 自動走行 framework 5-layer)** の Layer 1 担当 PLAN。

PLAN-099 §5 で設計を確定済み:
- Layer 1 = `PostToolUse(Write|Edit + PLAN.md) → helix job enqueue (task_queue 新設なし、P0 承認 guard 必須)`
- 実装スコープは PLAN-099 の P2b (別 session 本実装) に分類
- 本 PLAN はその実装 PLAN として独立起票

**課題 (PLAN-099 §1 より)**:
- PLAN.md が書き込まれても carry が自動的に helix job に登録されず、PM が手動で追跡する必要がある
- 解決: PostToolUse hook が PLAN.md / ADR*.md への書き込みを検出し、next action 候補を systemMessage で提示する

**前駆 PLAN との関係**:
- PLAN-090 (continueOnBlock / active guidance loop pattern) が Layer 1 hook の PostToolUse 設計の直接前駆
- PLAN-092 (helix.db plan_registry) が本 PLAN の enqueue 先として機能する

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (PostToolUse hook による PLAN 自動追跡設計) を含むため、PLAN-087 ガード対象。PLAN-099 §3 で実施済の WebSearch 3 query を parent として継承し、以下の key evidence を引用する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code PostToolUse hook decision continue systemMessage specification 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.139) | PostToolUse で `continueOnBlock:true` を設定すると reject reason を Claude に返してターン継続できる。Layer 1 は block せず systemMessage 提示のみ = `decision:continue` 専用。exit 2 = fail-close block は PreToolUse / PreCompact 専用 |
| "agent framework task queue auto register plan consent guard 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143) / HELIX CLAUDE.md | 「承認なし task pop は Plan Consent / WBS / handover Next Action を超える設計 = HELIX discipline 破壊」(TL v5 P0 指摘)。queue worker は必ず plan guard を通すこと。HELIX 独自原則として CLAUDE.md に永続化済み |
| "posttooluse file pattern match helix job enqueue atomic claim concurrency 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG v2.1.141) | PostToolUse hook は tool_input.file_path で対象ファイルを判別可能。helix job の atomic claim はファイルロック + SQL transaction で実装するのが定番パターン |

## 業界 standard 参照

- Claude Code CHANGELOG 2.1.139: https://github.com/anthropics/claude-code/releases (PostToolUse continueOnBlock 追加)
- Claude Code CHANGELOG 2.1.143: https://github.com/anthropics/claude-code/releases (background session worktree isolation)
- Claude Code CHANGELOG v2.1.141: https://github.com/anthropics/claude-code/releases (transcript_path / file_path hook 提供確認)
- HELIX PLAN-099 §5: parent PLAN の設計根拠 (本 PLAN は §5 仕様を実装する)
- HELIX CLAUDE.md §PLAN ⊃ ADR レイヤー併存: PLAN は implementation tree、ADR は L2 snapshot の設計原則

## 設計方針 (TL v5 round 5 修正条件 遵守)

CLAUDE.md §TL v5 round 5 修正条件 を厳密遵守する。特に P0 指摘と補助 #7 が本 PLAN の核心:

> (P0) 「承認なし task pop は Plan Consent / WBS / handover Next Action を超える設計 → HELIX discipline 破壊。queue worker は必ず plan guard を通すこと」

> (補助 #7) 「task_queue テーブルは新設しない。plan_registry = PLAN-092。実行待ち = 既存 helix job。session continuity = 既存 handover。ephemeral checklist = 既存 TodoWrite (廃止しない)」

### P0 承認 guard (CRITICAL)

PLAN-099 §5.2 を実装根拠として引用。自動 enqueue は候補提示まで。実際の enqueue は Plan Consent guard を通過した後のみ:

```
PostToolUse hook 検出 (PLAN.md / ADR*.md 書き込み)
      ↓
  systemMessage で「PLAN-NNN 検出、next action 候補: [XXX]」表示
      ↓
  decision: continue (ターン継続、hook は block しない)
      ↓
  PM (Opus) または handover Next Action または WBS が承認
  (OR 条件: explicit_consent OR wbs_match OR handover_match)
      ↓
  helix job pending 登録
      ↓
  worker が claim → 実行
```

承認前の worker 自律実行は **絶対禁止** (TL v5 P0、HELIX discipline 破壊)。

### 単一実行正本 (TL v5 P1 遵守)

| 概念 | 担当 | 備考 |
|---|---|---|
| PLAN 定義 (永続) | `plan_registry` (PLAN-092 担当) | helix.db に永続、本 PLAN は候補提示のみ |
| 実行待ちキュー | 既存 `helix job` | task_queue 新設なし |
| session 引き継ぎ | `handover CURRENT.json` | 既存 handover CLI を使う |
| ephemeral checklist | 既存 `TodoWrite` | 廃止しない |
| PLAN 書き込み検出 | 本 PLAN (Layer 1 hook) | runtime substrate として追加 |

### hook 設計: decision:continue 専用

Layer 1 hook は原則 `decision:continue` (block しない)。systemMessage による候補提示のみを担う。PLAN-090 の `continueOnBlock:true` とは目的が異なる (PLAN-090 は reject reason 返却、本 PLAN は候補提示)。

```
PLAN_PATTERN="docs/plans/PLAN-[0-9]+-.*\.md"
ADR_PATTERN="docs/adr/ADR-[0-9]+-.*\.md"
```

### feature flag による段階導入 (PLAN-099 §13.2 準拠)

```
P2b (本 PLAN): warn-only (block なし、systemMessage 候補提示のみ)
P3: fail-close (block 有効、P0 guard = OR 条件)
```

デフォルト `HELIX_LAYER1_ENABLED=0` (opt-in)。運用確認後に `=1` に昇格。

## 実装計画

### Sprint .1: PLAN.md 検出 + systemMessage 候補提示 (Codex se 委譲)

**対象ファイル**: `.claude/hooks/posttooluse-plan-registry-sync.sh` (新規)

実装内容:
- `detect_plan_file()` 関数: tool_input.file_path が PLAN_PATTERN / ADR_PATTERN にマッチするか判定
- `extract_plan_id()` 関数: ファイルパスから PLAN-NNN / ADR-NNN を抽出
- `build_candidate_message()` 関数: `「PLAN-NNN 検出、next action 候補」` の systemMessage を生成
- `check_plan_guard()` 関数: HELIX_JOB_CONSENT_REQUIRED 確認 (default 1、P0 guard 有効)
- メインロジック: 検出 → guard 確認 → systemMessage 出力 → `decision:continue` 返却

hook 入力仕様 (stdin JSON):
```json
{
  "tool_name": "Write|Edit|MultiEdit",
  "tool_input": { "file_path": "docs/plans/PLAN-NNN-*.md" },
  "tool_response": {}
}
```

hook 出力仕様 (stdout JSON):
```json
{
  "decision": "continue",
  "systemMessage": "PLAN-NNN 検出 (Layer 1): next action 候補 — [sprint .1 着手 / ADR-NNN snapshot 起票]。承認後に `helix job pending --plan PLAN-NNN` で登録してください"
}
```

mandatory in sprint:
- `bash -n .claude/hooks/posttooluse-plan-registry-sync.sh` PASS

### Sprint .2: settings.json hook 登録 + queue atomic claim 補助 (Codex se 委譲)

**対象ファイル**: `.claude/settings.json` (Edit)

実装内容:
- PostToolUse hook 登録 (matcher: Write|Edit|MultiEdit、timeout: 5)
- 既存 hooks 配列への append のみ (他 hook を変更しない)
- `helix job claim --atomic` 補助スクリプト呼び出し方針のコメント追記
  (実際の atomic claim 実装は PLAN-092 helix.db v36 schema 確定後)
- `HELIX_LAYER1_ENABLED` feature flag 確認ロジック (0 時は hook を no-op で通過)

mandatory in sprint:
- `python3 -c "import json; json.load(open('.claude/settings.json'))"` PASS (JSON syntax)
- 既存 hook 回帰 (pretooluse-design-doc-web-search-guard.sh 等が引き続き動作)

### Sprint .3: bats fixture test 実装 + DoD 確認 (Codex qa 委譲)

**対象ファイル**: `.claude/hooks/tests/test_posttooluse_plan_registry.bats` (新規)

テストケース (PLAN-099 §11.2 T1-001〜T1-004 + T6-001 完全準拠):

| ケース | 内容 |
|---|---|
| T1-001 | PLAN.md 書き込み → systemMessage に候補提示、decision:continue が stdout に出力 |
| T1-002 | ADR.md 書き込み → 同上 (ADR_PATTERN マッチ確認) |
| T1-003 | 非 PLAN ファイル書き込み (cli/helix など) → systemMessage なし、decision:continue のみ |
| T1-004 | HELIX_JOB_CONSENT_REQUIRED=1 時に自動 enqueue コマンドが実行されないことを確認 |
| T6-001 | hook 実行時間 ≤ 5 秒 (time コマンドで計測) |

fake fixture 方針:
- `HELIX_HOME` を `$BATS_TMPDIR/helix_home_<test>` に向ける
- fake stdin JSON を echo でパイプして hook に渡す
- `HELIX_LAYER1_ENABLED=1` を設定してテスト実行
- `HELIX_JOB_CONSENT_REQUIRED=1` (default) で plan guard 有効化確認

mandatory in sprint:
- `bats .claude/hooks/tests/test_posttooluse_plan_registry.bats` 全 5 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit 時、本 PLAN が G4 相当)

## DoD (Definition of Done)

- [ ] `bash -n .claude/hooks/posttooluse-plan-registry-sync.sh` PASS
- [ ] bats test 全 5 ケース PASS (T1-001〜T1-004 + T6-001)
- [ ] PLAN.md / ADR*.md 書き込み時に systemMessage で候補提示、decision:continue を返す
- [ ] 非 PLAN ファイル書き込み時は候補提示なし (T1-003 PASS)
- [ ] HELIX_JOB_CONSENT_REQUIRED=1 時に自動 enqueue が発生しない (plan guard 確認)
- [ ] settings.json hook 登録 PASS (JSON syntax valid)
- [ ] 既存 hook 回帰なし (pretooluse / other posttooluse / sessionstart 系が影響を受けない)
- [ ] hook timeout ≤ 5 秒 (T6-001 PASS)
- [ ] feature flag HELIX_LAYER1_ENABLED=0 時は hook が no-op で通過する
- [ ] ADR-040 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §実装計画 Sprint .3 ケース一覧 (T1-001〜T1-004 + T6-001) |
| ② 実装コード | .claude/hooks/posttooluse-plan-registry-sync.sh (Sprint .1-.2 で実装) |
| ④ テストコード | .claude/hooks/tests/test_posttooluse_plan_registry.bats (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T1/T6 番号明記
- テストコード → 設計: bats test の `# PLAN-113 T1-001` コメントで対応付け (Sprint .3 実装時)
- テスト設計 → テストコード: bats describe 名称で T1-NNN 対応 (Sprint .3 実装時)

## carry / 学び (起票時記録)

- **PLAN-092 との依存順序**: Sprint .2 の atomic claim 補助は PLAN-092 helix.db v36 schema 確定後に本実装。本 PLAN Sprint .2 では呼び出し方針のコメント追記にとどめ、schema 確定を待つ
- **HELIX_LAYER1_ENABLED の初期値**: 既存 hook 群への影響を最小化するため `=0` (opt-in) でリリース。運用で問題がなければ `=1` に昇格する段階導入を徹底する
- **plan guard OR 条件の実装優先度**: explicit_consent が最も単純。wbs_match / handover_match は PLAN-092 plan_registry の lookup が必要なため、Sprint .1-2 では explicit_consent のみを実装し、残りは PLAN-092 確定後に追加する
- **非 PLAN ファイルとの誤検知**: PLAN-087 hook (design-doc-web-search-guard.sh) と matcher が重複しないよう、Pattern を docs/plans/PLAN-*.md / docs/adr/ADR-*.md に限定する
- **既存 posttooluse-helix-job-enqueue.sh との関係**: PLAN-099 §5.4 に記載の `posttooluse-helix-job-enqueue.sh` は本 PLAN が代替実装する。ファイル名は `posttooluse-plan-registry-sync.sh` に統一する (PLAN-099 generates フィールドとの差異は本 PLAN の ADR-040 で確定)

## 関連 reference

- PLAN-099 §5 (Layer 1 設計、本 PLAN の実装根拠)
- PLAN-099 §11.2 (テストケース T1-001〜T1-004 + T6-001)
- PLAN-090 (PostToolUse continueOnBlock / active guidance loop、前駆)
- PLAN-091 (V5 framework core、frontmatter 語彙正本)
- PLAN-092 (helix.db plan_registry、enqueue 先 upstream)
- PLAN-088 (TodoWrite × agent slot framework、task_queue 競合解消の背景)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-040 (本 PLAN の L2 snapshot、起票予定)
- [[feedback_design_doc_hook_session_id_missing_block]] (hook が自分の Write を block する関連 feedback)
- [[feedback_dont_stop_with_carry_remaining]] (carry 残し放置の背景課題)
- CLAUDE.md §TL v5 round 5 修正条件 (設計方針の根拠、P0 / 補助 #7)
