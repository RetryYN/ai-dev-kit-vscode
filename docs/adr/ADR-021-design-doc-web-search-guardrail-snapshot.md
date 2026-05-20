# ADR-021: 設計 doc 作成時 Web 検索ガードレール framework 採用

## Status

Proposed (2026-05-20、後追い snapshot — PLAN-087 実装済の L2 凍結)

> **後追い snapshot 注記**: PLAN-087 は 2026-05-19 に実装完了済み。本 ADR は PLAN ⊃ ADR レイヤー併存ルール (feedback_adr_before_plan_violation で確立) に基づき、L2 大局判断 snapshot として後追い起票する。ADR は append-only log として retroactive 起票が業界標準 pattern (Nygard ADR original、Cognitect blog 2011)。

## Deciders

- PM (Opus、yoshiyuki0907yn@gmail.com)
- PO (yoshiyuki0907yn@gmail.com)

## Supersedes

なし (新規 ADR)

## Related

- PLAN-087-design-doc-web-search-guardrail (実装 PLAN、本 ADR が L2 凍結する)
- PLAN-100-existing-retrofit-v2-revision (retrofit master、§4.1 に本 ADR の context 記載)
- ADR-025-v5-framework-core-decision (V5 framework 本体、要素 #11 ADR snapshot 必須化ルール)
- PLAN-085-cutover-staging-rehearsal (本ガードレール試行運用の起点)
- PLAN-086-rollback-fault-injection-drill (同上)

## 業界 standard 参照

| 参照 | Source URL | 本 ADR での引用箇所 |
|---|---|---|
| Nygard ADR original pattern (2011) | https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | retroactive ADR 起票の業界標準根拠。ADR は「決定が行われた時点で」起票するのが理想だが、後追い起票も有効 |
| AWS ADR best practices | https://aws.amazon.com/blogs/architecture/master-architecture-decision-records-adrs-best-practices-for-effective-decision-making/ | ADR に Alternatives + Consequences を必須化する構造 |
| Microsoft Azure Well-Architected ADR | https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record | ADR は append-only log、Supersedes で置換履歴管理 |
| Claude Code Hooks 公式 doc | https://code.claude.com/docs/en/hooks | PreToolUse の exit code 2 = fail-close block の仕様根拠 |
| Flagsmith: Feature flags staged rollout | https://www.flagsmith.com/blog/how-to-enhance-phased-rollouts-with-feature-flags | warn-only → fail-close の段階移行の業界整合 |

---

## Context

### 問題の発端

HELIX 運用において、設計 doc (ADR / PLAN / spec) を新規起票・大幅 scope 変更する際に、業界 standard や既存 OSS の慣行を事前調査せずに「思いつき」で書き始める pattern が繰り返し発生していた。

具体的な事例:
- PLAN-085 / PLAN-086 / ADR-020 初版 (commit 445b27e / 996c05f / 5d730ec / b94395b) で SaaS 本番運用テンプレート (PO 承認 PR / S3 backup / 24h on-call / multi-reviewer 等) を local CLI tool である HELIX に過剰適用
- 第 1 次 scope down (ユーザー指摘後) も Web 検索なしの思いつき書き直しで、再度 scope 問題が発覚
- ユーザー指摘「だから設計ドキュメント作るときに Web 検索をはさめって言ってんだろ」「工程内にガードレール組み込め」で構造化の必要性を認識

### 影響範囲

設計 doc の過剰適用・scope 誤りは、その後の実装を誤った方向に誘導し、複数の commit retract / scope down 再作業が必要になる。設計段階での cost は実装段階の 5〜10 倍以上 (industry estimate)。HELIX では PM (Opus) が設計判断を行うため、PM の「思いつき」が downstream に直接影響する。

### 対象範囲

以下の操作を trigger とする:
- 新規 ADR / PLAN / spec doc の Write (Edit|Write|MultiEdit)
- 既存 ADR / PLAN / spec の大幅変更 (scope / CLI signature / 命名規約の変更)

---

## Decision

**設計 doc (ADR / PLAN / spec) 新規起票・大幅 scope 変更前に、WebSearch / WebFetch / pmo-tech-docs / pmo-tech-fork で業界 standard を 3 query 以上調査することを機械強制する。**

具体的な実装:
1. **PreToolUse hook** (`.claude/hooks/pretooluse-design-doc-web-search-guard.sh`): Edit|Write|MultiEdit trigger で設計 doc 検出 → session_id に対応する Web 検索履歴を helix.db で確認 → 3 query 未満なら exit 2 で fail-close block
2. **設計 doc テンプレート必須 section 化**: `docs/templates/adr-template.md` / `docs/templates/plan-template.md` に「業界 standard 参照」section を必須化 (Sources URL を含む)
3. **helix-gate G2/G3 audit**: 設計 doc の業界 standard 参照 section の存在を advisory チェック (PLAN-089 で fail-close 化段階予定)
4. **bypass**: `HELIX_ALLOW_DESIGN_DOC_NO_WEB=1` 環境変数 + 理由を evidence に残す (緊急時のみ)

---

## Consequences

### Positive

- 設計 doc の「思いつき」起票を機械的に防止できる
- 業界 standard 参照の明示化により、後追いレビューで根拠が確認できる
- scope 過剰適用 / 過小適用の発生率を下げる (設計修正コストの削減)
- HELIX framework の各 PLAN に「業界 standard 参照」が蓄積され、知識ベースが充実する

### Negative

- 緊急の設計 doc 起票に遅延が生じる可能性がある (3 query 調査の時間コスト)
- session_id が missing の場合 (PreToolUse session 跨ぎ等) に fail-close が空振りする可能性がある
- Codex CLI 内 Write は Claude Code hook を bypass するため、Codex が設計 doc を書く場合は hook 対象外 (別途 Codex 側のガードレール設計が必要)

---

## Alternatives

### A案 (棄却): advisory warn-only のみ (fail-close なし)

- 採用しない理由: memory feedback で確立した「ガードレール = 工程内強制が必要」の原則と矛盾する。warn-only は無視されるリスクが高い

### B案 (棄却): レビュー段階での事後チェック (G2/G3 ゲートのみ)

- 採用しない理由: 設計起票 → レビューの lag が長く、「思いつき書き」が中間 commit に残る。PreToolUse での事前 block が cost 最小

### C案 (部分採用): 段階的 fail-close (PLAN-089 連動)

- 現状採用済み: Phase 1 (advisory 計測) → Phase 2 (fail-close) の段階移行を PLAN-089 で実施。本 ADR の決定 (PreToolUse fail-close) は最終状態 (Phase 2 以降) の実装

---

## Implementation Status

**実装完了 (2026-05-19)**: PLAN-087 Phase 1-3 が commit 22ce096 / 35d8a30 で実装済み。本 ADR は L2 凍結 snapshot として後追い起票 (2026-05-20)。

| Phase | 実装内容 | commit | 状態 |
|---|---|---|---|
| Phase 1 | template 必須 section 化 + G2/G3 advisory audit | 22ce096 | 完了 |
| Phase 2 | PreToolUse hook fail-close (7-case smoke 7/7 PASS) | 22ce096 | 完了 |
| Phase 3 | helix-gate G2/G3 advisory gate + helix-doctor check | 22ce096 | 完了 (advisory) |
| Phase 4 (carry) | helix-gate fail-close 化 (PLAN-089 §Phase 2 待ち) | - | PLAN-089 carry |

**本 ADR 起票後**: PLAN-087 frontmatter への `related_adr: [ADR-021]` 追加 + PLAN-087 本文への `## L2 凍結 (ADR-021 snapshot)` section 追加は PLAN-100 Phase 2 (別 session) で実施する。
