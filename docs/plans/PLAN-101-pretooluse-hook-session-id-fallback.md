---
plan_id: PLAN-101
title: PreToolUse design-doc hook session_id fallback 実装 + transcript-based 検証緩和
status: completed
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-100-existing-retrofit-v2-revision.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-22
completed_at: 2026-05-22
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
agent_slots:
  - role: se
  - role: tl-advisor
generates:
  - artifact_type: hook
    path: .claude/hooks/pretooluse-design-doc-web-search-guard.sh
  - artifact_type: test
    path: .claude/hooks/tests/test_session_id_fallback.bats
  - artifact_type: test
    path: .claude/hooks/tests/test_design_doc_guard_fallback.bats
dependencies:
  requires:
    - PLAN-087
    - PLAN-089
  blocks: []
  parent: PLAN-100
acceptance_criteria:
  - 既存 12-case strict smoke test 全 PASS
  - 新規 bats test (10 case) 全 PASS
  - PLAN-101 / ADR-033 等の新規設計 doc Write が、本 session 内で実施済 WebSearch 履歴に基づき pass する実証
  - bypass env HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 + 理由必須化
  - MAX_SCAN_BYTES を 4 MB に拡張 (連続作業 session 対応、512 KB では transcript size 超過で scan 不能)
---

# PLAN-101: PreToolUse design-doc hook session_id fallback 実装

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-033** で凍結:
- hook session_id 取得 fallback chain の 5 段優先順位 (env → payload → CLAUDE_TASK_OUTPUT_DIR → CLAUDE_TRANSCRIPT_PATH → 空文字)
- transcript file 探索の path 規約 (`~/.claude/projects/<hash>/<session-uuid>.jsonl`、sessions/ subdir 無し)
- fail-close 後退枝の advisory 経路 (HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1 + 理由 env 必須)
- MAX_SCAN_BYTES = 4 MB (連続作業 session 対応)

## 背景

`.claude/hooks/pretooluse-design-doc-web-search-guard.sh` (PLAN-087 framework) が新規設計 doc Write を、Claude Code が session_id を hook env / payload に渡さない場合に **全 block** する仕様問題。

- block 条件: target=docs/plans/PLAN-*.md or docs/adr/ADR-*.md + change=new-file + session_id=missing
- 既存 file 修正 (Edit) は pass する (change ≠ new-file)
- 前 session で実施済の WebSearch 3 query を hook 側が認識できず block ([[feedback_design_doc_hook_session_id_missing_block]])

## WebSearch 履歴 (PLAN-087 ガード遵守)

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code PreToolUse hook session_id environment variable payload 2026" | claudefa.st/blog/tools/hooks/hooks-guide / code.claude.com/docs/en/hooks | PreToolUse hook stdin JSON に session_id field 含まれる ({"session_id", "cwd", "hook_event_name", "tool_name", "tool_input"}) |
| "fail-close hook bypass design pattern environment variable fallback chain" | nobuti.com/thoughts/resilience-patterns-fallback / codecentric.de Resilience Patterns | Fallback chain pattern: 各 link は less optimal but more reliable、最終 link は default value |
| "Claude Code transcript jsonl file path session identification 2026" | databunny.medium.com / kentgigger.com claude-code-conversation-history | transcript path = ~/.claude/projects/<url-encoded-project-path>/<session-uuid>.jsonl (sessions/ subdir 無し)、各 line に sessionId field、parentUuid で chain |

## 業界 standard 参照

- Claude Code Hooks Reference (公式): https://code.claude.com/docs/en/hooks
- Fallback Design Pattern (Microservices Resilience): https://badia-kharroubi.gitbooks.io/microservices-architecture/content/patterns/communication-patterns/fallback-pattern.html
- Session Storage / JSONL Format: https://databunny.medium.com/inside-claude-code-the-session-file-format-and-how-to-inspect-it-b9998e66d56b

## 実装計画 → 実績 (Wave 1 + Wave 1.5 patch で完遂)

本 PLAN は Wave 1 (commit 588fc46) で 1 commit、Wave 1.5 (本 commit) で MAX_SCAN_BYTES patch を追加して完遂。

### Sprint .1: detect_session_id() の fallback chain 強化 ✅ (commit 588fc46)

- Priority 1: HELIX_SESSION_ID env (既存維持)
- Priority 2: stdin payload `.session_id` field (新規追加、Claude Code 公式 spec)
- Priority 3: CLAUDE_SESSION_ID env (既存維持)
- Priority 4: CLAUDE_TASK_OUTPUT_DIR UUID 抽出 (既存維持)
- Priority 5: CLAUDE_TRANSCRIPT_PATH UUID 抽出 (新規追加)
- 全 fallback 失敗時: 空文字返却 (block 動作維持)

### Sprint .2: scan_transcripts() の path 規約変更 ✅ (commit 588fc46)

- 追加 scan target: `~/.claude/projects/<url-encoded-project-path>/<session-uuid>.jsonl`
- url-encoded-project-path 構築: `repo_root` を `_` で hyphen 置換 (Claude Code 仕様)
- session_id が取れたら該当 jsonl のみ scan、取れなかったら最新 1 file fallback scan (mtime 直近 1 時間以内)
- WEB_PATTERNS + SUBAGENT_PATTERNS 検索ロジックは既存維持

### Sprint .3: advisory bypass 経路追加 ✅ (commit 588fc46)

- env `HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1` + 理由 env `HELIX_DESIGN_DOC_GUARD_MISSING_SESSION_REASON` で missing session でも pass + warning print
- 既存 `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1` との二重 bypass にしない (排他)

### Sprint .4: bats test 追加 ✅ (commit 588fc46)

- `.claude/hooks/tests/test_session_id_fallback.bats` 新規 (5 case = Priority 1-5)
- `.claude/hooks/tests/test_design_doc_guard_fallback.bats` 新規 (5 case = transcript 検出 / mtime fallback / missing session bypass / cross-session pass 禁止 / new-file allowance)

### Sprint .5: MAX_SCAN_BYTES 拡張 + commit ✅ (本 commit)

- 既存 `MAX_SCAN_BYTES = 512 * 1024` → `4 * 1024 * 1024` (4 MB)
- 根拠: 本 session transcript size 725580 bytes > 524288 (512 KB) で WebSearch 履歴を scan 不能 = framework が実環境で機能しない
- mandatory in sprint: `bash -n` PASS、PLAN-101 + ADR-033 Write 動作実証 PASS

## DoD (Definition of Done) 実績

- [x] `bash -n .claude/hooks/pretooluse-design-doc-web-search-guard.sh` PASS
- [x] 新規 bats test 全 PASS (10 case)
- [x] 既存 12-case strict smoke 全 PASS
- [x] PLAN-101 自身の Write が、本 session 内 WebSearch 履歴に基づき pass する実証 (MAX_SCAN_BYTES patch 後)
- [x] ADR-033 起票も同様に pass する実証
- [x] settings.json hook 登録の Edit が影響受けないこと (Wave 1 で carry 2 と独立 commit)

## carry / 学び

- **MAX_SCAN_BYTES 上限**: 512 KB は数十分の連続 session で超過する。長期的には tail streaming (file の最後 N KB だけ読む) に変更してメモリ効率を保つ pattern が望ましい (carry として記録)
- **WebSearch evidence format**: transcript jsonl の `"tool_name":"WebSearch"` を grep する設計は Anthropic SDK format に依存、将来 SDK 仕様変更で破綻リスク

## 関連 reference

- [[feedback_design_doc_hook_session_id_missing_block]] (本 PLAN 起票の trigger feedback)
- [[feedback_design_doc_web_search_required]] (PLAN-087)
- [[feedback_subagent_guard_hook_fail_close]] (同型 hook 品質)
- ADR-033 (本 PLAN tree の L2 snapshot)
- PLAN-087 (Web 検索ガード初期 framework)
- PLAN-089 (gate fail-close advisory→fail-close 段階遷移)
