# ADR-024: Claude Code continueOnBlock + active guidance loop pattern 採用

## Status

Proposed (2026-05-20、後追い snapshot — PLAN-090 実装済の L2 凍結)

> **後追い snapshot 注記**: PLAN-090 は 2026-05-19 に起票済み (調査完了・一部実装)。本 ADR は PLAN ⊃ ADR レイヤー併存ルールに基づき、L2 大局判断 snapshot として後追い起票する。外部新仕様 (Claude Code 2.1.139 continueOnBlock) の採用判断は L2 大局判断に該当するため、ADR snapshot 必須 (PLAN-091 §7.1 条件「外部新仕様の採用」)。

## Deciders

- PM (Opus、yoshiyuki0907yn@gmail.com)
- PO (yoshiyuki0907yn@gmail.com)
- pmo-tech-news 調査 (2026-05-19 W10、Claude Code 最新 changelog 確認)

## Supersedes

なし (新規 ADR)

## Related

- PLAN-090-posttooluse-continueonblock-refactor (実装 PLAN、本 ADR が L2 凍結する)
- PLAN-100-existing-retrofit-v2-revision (retrofit master、§4.4 に本 ADR の context 記載)
- PLAN-087-design-doc-web-search-guardrail (PostToolUse hook の前段 framework)
- PLAN-089-gate-fail-close-design-doc-web-search-audit (PostToolUse hook と連携)
- ADR-025-v5-framework-core-decision (V5 framework 本体)

## 業界 standard 参照

| 参照 | Source URL | 本 ADR での引用箇所 |
|---|---|---|
| Claude Code Hooks 公式 changelog (2.1.139 continueOnBlock 追加) | https://code.claude.com/docs/en/changelog | continueOnBlock の仕様根拠 (PostToolUse で decision:block + reject reason → ターン継続) |
| Claude Code Hooks reference (PostToolUse) | https://code.claude.com/docs/en/hooks | PostToolUse の exit code 2 / decision フィールド / additionalContext の仕様 |
| GitHub Issues #21988 (PreToolUse exit code 無視 bug → CLOSED) | https://github.com/anthropics/claude-code/issues/21988 | PreToolUse exit code 仕様明確化 (exit 2 = block / exit 1 = non-blocking) の根拠 |
| GitHub Issues #24327 (exit 2 後 Claude 待機問題) | https://github.com/anthropics/claude-code/issues/24327 | モデル挙動の問題 (hook 解決不可) の根拠、continueOnBlock が代替解 |
| Claude Code 2.1.119 changelog (additionalContext drop bug fix) | https://code.claude.com/docs/en/changelog | additionalContext が正しく届くようになった (PreToolUse block 後の context 改善) |

---

## Context

### 問題の発端

HELIX の PostToolUse hook (`.claude/hooks/posttooluse-design-doc-web-search-revert.sh`) は、設計 doc の無断起票を検知した際に `stderr + exit 1 (warn-only)` で警告していたが、以下の問題があった:

1. **reject reason が Claude に返らない**: warn-only (exit 1) では Claude は「何を修正すべきか」を把握できず、同じ操作を繰り返す可能性がある
2. **二重防御の限界**: PreToolUse (block) と PostToolUse (warn-only) の組み合わせで「二重防御」を実装していたが、PostToolUse の warn-only は実質的に機能していなかった
3. **self-inflicted revert 問題**: PostToolUse が block 判定した場合に file を revert する実装 (posttooluse-design-doc-web-search-revert.sh) が、hook 自身の Write を block する「自 hook 自 revert」pattern を引き起こした

### 外部仕様の変化

Claude Code 2.1.139 で PostToolUse に `continueOnBlock` が追加された:

- **continueOnBlock = true**: PostToolUse の `decision: "block"` が出ても Claude のターンを継続する (以前は block で完全停止)
- **効果**: reject reason を systemMessage や additionalContext で Claude に伝えることで、Claude が同一ターン内で「Web 検索を先に実行する」「別の approach を試みる」等のリトライが可能になる

### Codex CLI の制約

調査で判明した重要な制約:
- Codex CLI 内の Write は Claude Code hook を bypass する (別 process で動くため、Claude Code settings.json の hook を継承しない)
- この制約は HELIX 設計において Codex 委譲 task は hook 対象外として扱うことを意味する

---

## Decision

**PostToolUse hook に continueOnBlock を採用し、reject reason を Claude に返す「active guidance loop」pattern を確立する。二重防御 (PreToolUse block + PostToolUse warn-only) より、新仕様 (continueOnBlock) 準拠に切替える。**

具体的な実装:
1. **continueOnBlock = true + JSON decision**: PostToolUse hook の block 時に `{"decision": "block", "reason": "...", "continueOnBlock": true}` を返す
2. **active guidance loop**: reject reason を Claude に伝え、Claude が同一ターン内で「Web 検索を 3 query 以上実行してから再起票」を自律的に実行できるようにする
3. **二重防御の整理**: PreToolUse (fail-close) を主防衛線とし、PostToolUse は「block 後の guidance」に特化。warn-only の PostToolUse revert は廃止
4. **Codex bypass 対策の分離**: Codex CLI が hook を bypass する問題は、helix codex 側のプロンプト injection で対処 (hook での対処は不可)

---

## Consequences

### Positive

- Claude が reject reason を理解し、同一ターン内で自動リトライできる (idle time 削減)
- 「自 hook 自 revert」pattern を排除できる (self-inflicted revert の root cause 解消)
- continueOnBlock により block が「完全停止」から「guided retry」に変わり、UX が改善される

### Negative

- continueOnBlock の挙動は Claude Code 2.1.139 以降に限定 (旧バージョンでは動作が異なる可能性)
- Codex CLI の hook bypass 問題は continueOnBlock では解決できない (別途対応が必要)
- Issue #24327 (exit 2 後 Claude 待機) はモデル挙動の問題で hook 側では解決不可

---

## Alternatives

### A案 (棄却): warn-only (exit 1) 継続 + 人間確認依存

- 採用しない理由: Claude に reject reason が伝わらず、同一 mistake を繰り返すリスクが高い。AskUserQuestion 0 回目標と矛盾する

### B案 (棄却): 二重防御 (PreToolUse block + PostToolUse revert) 維持

- 採用しない理由: 「自 hook 自 revert」pattern が発覚し、PostToolUse revert が意図しない file 削除を引き起こした。continueOnBlock 採用により二重防御より精度の高い制御が可能

### C案 (採用): continueOnBlock + active guidance loop (本 ADR の実装方針)

- 採用済み: PLAN-090 の設計として組み込まれている

---

## Implementation Status

**設計完了・一部実装 (2026-05-19)**: PLAN-090 が起票済み。continueOnBlock の調査と設計は完了。実装は carry。本 ADR は L2 凍結 snapshot として後追い起票 (2026-05-20)。

| 実装内容 | 状態 |
|---|---|
| Claude Code 2.1.139 continueOnBlock 仕様調査 (pmo-tech-news W10) | 完了 |
| PLAN-090 設計起票 | 完了 |
| posttooluse hook の continueOnBlock 移行実装 | carry (別 session) |
| 二重防御 (revert hook) の廃止 | carry (別 session) |

**Codex CLI bypass 確認** (実測 commit b9wl210l): Codex CLI 内 Write が Claude Code hook を bypass することを実測で確認済み。この制約は HELIX 設計の前提として固定する。

**本 ADR 起票後**: PLAN-090 frontmatter への `related_adr: [ADR-024]` 追加は PLAN-100 Phase 2 (別 session) で実施する。
