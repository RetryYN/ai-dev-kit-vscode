# ADR-033: PreToolUse hook の session_id 取得 fallback chain と transcript-based 検証緩和

- Status: Proposed
- Date: 2026-05-22
- Authors:
  - PM (Opus 4.7)
  - SE (Codex gpt-5.4)
- Related: PLAN-101 (本 ADR を実装した PLAN tree)、PLAN-087 (Web 検索ガード初期 framework)、PLAN-089 (gate fail-close advisory→fail-close 段階遷移)
- Supersedes: なし

## Context

`.claude/hooks/pretooluse-design-doc-web-search-guard.sh` は PLAN-087 で導入された設計 doc 起票ガード hook。session_id が missing の場合 fail-close で **全 Write を block** する仕様により、Claude Code が session_id を env / payload に渡さない場合に正当な起票が阻害される問題が判明 ([[feedback_design_doc_hook_session_id_missing_block]])。

加えて、本 ADR 起票時の実測で **MAX_SCAN_BYTES = 512 KB の上限が連続作業 session で超過** (本 session transcript 725 KB) し、WebSearch 履歴があっても scan 不能で block されることを確認。

本 ADR は、hook session_id 取得の fallback chain、transcript-based 検証緩和、MAX_SCAN_BYTES 拡張を L2 大局判断として凍結する。

## Decision

### 1. session_id 取得 fallback chain (5 段優先順位)

| 優先 | 取得経路 | 根拠 |
|---|---|---|
| 1 | HELIX_SESSION_ID env | HELIX 独自 (運用上の override 用) |
| 2 | stdin payload `.session_id` field | Claude Code hook 公式 spec ([Hooks reference](https://code.claude.com/docs/en/hooks)) |
| 3 | CLAUDE_SESSION_ID env | Claude Code env 互換 |
| 4 | CLAUDE_TASK_OUTPUT_DIR UUID 抽出 | 既存 (subagent runtime path) |
| 5 | CLAUDE_TRANSCRIPT_PATH UUID 抽出 | Claude Code transcript path field |

全 fallback 失敗時は空文字を返し、block 動作維持 (Fallback Pattern: 最終 link は default value)。

### 2. transcript file 探索の path 規約

- 探索 target: `~/.claude/projects/<url-encoded-project-path>/<session-uuid>.jsonl`
- url-encoded-project-path: repo_root を `_` で hyphen 置換 (Claude Code 仕様、例: `/home/tenni/ai-dev-kit-vscode` → `-home-tenni-ai-dev-kit-vscode`)
- **sessions/ subdir は無し** (Claude Code 実装の実態に準拠、当初想定した sessions/<id>/transcript.jsonl 構造は誤り)
- session_id 確定時: 該当 jsonl のみ scan
- session_id missing 時: 最新 1 file fallback scan、ただし mtime 直近 1 時間以内に限定 (cross-session pass 禁止)

### 3. MAX_SCAN_BYTES = 4 MB

- 既存 512 KB は連続作業 session (30 分以上の作業) で超過する
- 4 MB は数時間の連続作業 (transcript 数 MB 規模) を許容
- 長期的には tail streaming (file の最後 N KB だけ読む) パターンに移行余地あり (carry)

### 4. fail-close 後退枝 (advisory) の経路

- env `HELIX_DESIGN_DOC_GUARD_ALLOW_MISSING_SESSION=1` + 理由 env `HELIX_DESIGN_DOC_GUARD_MISSING_SESSION_REASON` で missing session bypass を許可
- 理由は必ず会話 / final report に記録
- 既存 `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1` との二重 bypass は排他化 (両方 set されたら ALLOW_MISSING_SESSION を優先 + warning print)

## Consequences

### Positive

- 新規設計 doc 起票 (PLAN-* / ADR-*) が、本 session 内で WebSearch 履歴があれば session_id missing でも pass する
- transcript-based 検証で「同 session 内 Web 検索」を確実に検出
- fail-close 原則維持 (cross-session pass 禁止、mtime 1 時間以内制限)
- Fallback chain pattern が業界 standard (Microservices Resilience) と整合
- 連続作業 session で hook が実用的に機能する (MAX_SCAN_BYTES 拡張で再現性確保)

### Negative / Risks

- MAX_SCAN_BYTES 4 MB は数時間以上の長期 session ではまだ超過リスクあり (tail streaming 実装は carry)
- ADVISORY bypass が常用化されると hook の意義が薄まる → 理由 env を会話 evidence で必ず記録する運用で防御
- mtime 1 時間以内制限は連続作業 session で短い場合 false negative 起こす可能性 (運用観察で 30 分 / 2 時間への調整余地あり)
- transcript file の WebSearch format (`"tool_name":"WebSearch"`) は Anthropic SDK 仕様依存、将来変更リスク

### Neutral

- 既存 12-case strict smoke 全 PASS 維持
- bypass env 設計は subagent guard hook ([[feedback_subagent_guard_hook_fail_close]]) と同型

## Alternatives considered

- **A: hook 自体を削除 (PLAN-087 framework 撤回)**: 設計 doc 起票時の Web 検索励行を失う、却下
- **B: session_id missing 時は常に advisory (block しない)**: PLAN-089 の fail-close 段階遷移と矛盾、却下
- **C: HELIX_ALLOW_DESIGN_DOC_NO_WEB を常用 bypass にする**: 既存 bypass の濫用を招く、却下
- **D (採用)**: fallback chain + transcript scan + MAX_SCAN_BYTES 拡張 + advisory bypass 経路を限定追加

## WebSearch 履歴 (PLAN-087 ガード遵守、本 ADR 起票時)

| Query | 出典 |
|---|---|
| "Claude Code PreToolUse hook session_id environment variable payload 2026" | https://code.claude.com/docs/en/hooks / https://claudefa.st/blog/tools/hooks/hooks-guide |
| "fail-close hook bypass design pattern environment variable fallback chain" | https://nobuti.com/thoughts/resilience-patterns-fallback / https://badia-kharroubi.gitbooks.io/microservices-architecture/content/patterns/communication-patterns/fallback-pattern.html |
| "Claude Code transcript jsonl file path session identification 2026" | https://databunny.medium.com/inside-claude-code-the-session-file-format-and-how-to-inspect-it-b9998e66d56b / https://kentgigger.com/posts/claude-code-conversation-history |

## 関連

- PLAN-101 (本 ADR を実装した PLAN tree、Wave 1 commit 588fc46 + Wave 1.5 patch で完遂)
- PLAN-087 (Web 検索ガード初期 framework)
- PLAN-089 (gate fail-close advisory→fail-close 段階遷移)
- [[feedback_design_doc_hook_session_id_missing_block]] (本 ADR 起票の trigger feedback)
- [[feedback_subagent_guard_hook_fail_close]] (同型 hook 品質 framework)
