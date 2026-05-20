# ADR-023: gate fail-close 段階導入 (advisory → fail-close 段階遷移) 採用

## Status

Proposed (2026-05-20、後追い snapshot — PLAN-089 実装済の L2 凍結)

> **後追い snapshot 注記**: PLAN-089 は 2026-05-19 に実装完了済み (commit 35d8a30 等)。本 ADR は PLAN ⊃ ADR レイヤー併存ルールに基づき、L2 大局判断 snapshot として後追い起票する。

## Deciders

- PM (Opus、yoshiyuki0907yn@gmail.com)
- PO (yoshiyuki0907yn@gmail.com)
- tl-advisor (gpt-5.5 high、段階遷移の妥当性を adversarial check、bi9qaatd6)

## Supersedes

なし (新規 ADR)

## Related

- PLAN-089-gate-fail-close-design-doc-web-search-audit (実装 PLAN、本 ADR が L2 凍結する)
- PLAN-100-existing-retrofit-v2-revision (retrofit master、§4.3 に本 ADR の context 記載)
- PLAN-087-design-doc-web-search-guardrail (Web 検索ガードレールの前段、本 ADR の upstream)
- ADR-021-design-doc-web-search-guardrail-snapshot (前段 ADR)
- ADR-025-v5-framework-core-decision (V5 framework 本体、要素 #4 段階導入の正本)

## 業界 standard 参照

| 参照 | Source URL | 本 ADR での引用箇所 |
|---|---|---|
| Flagsmith: Feature flags staged rollout (warn-only → fail-close) | https://www.flagsmith.com/blog/how-to-enhance-phased-rollouts-with-feature-flags | 段階導入 (Phase 1 advisory → Phase 2 fail-close) の業界整合 |
| OpenFeature / Cloudflare Flagship progressive delivery | https://www.infoq.com/news/2026/05/cloudflare-flagship-openfeature/ | 継続フィードバックループ + 段階遷移の設計パターン |
| Claude Code Hooks 公式 doc (exit code 2 = block) | https://code.claude.com/docs/en/hooks | PreToolUse exit 2 の fail-close block 仕様 |
| HELIX tl-advisor review (bi9qaatd6) | helix codex --role tl-advisor 内部 | 「一括切替は blast radius 大、advisory 計測期間を Phase 1 で設ける」の根拠 |
| SQLite schema_version table (migrate() 冪等) | https://www.sqliteforum.com/p/sqlite-versioning-and-migration-strategies | helix.db v33 migration の業界整合 |

---

## Context

### 問題の発端

PLAN-087 Phase 3 で `helix-gate` に `run_gate_design_doc_web_search_audit` を実装した。しかし、この実装は G2/G3 ゲートで Web 検索 audit を行うものの、**advisory (warn-only)** であり、audit 結果が fail であっても gate 通過を block しない。

問題点:
1. **advisory は無視されるリスクが高い**: ゲートを通過しても audit 結果が残らない (実質的なフィードバックがない)
2. **fail-close への一括切替は危険**: advisory → fail-close を即時切替すると、既存の PLAN-001〜090 で Web 検索 section 不在の設計 doc が全件 block され、blast radius が大きい
3. **段階計測なしでは fail-close 閾値が不明**: 計測期間なしに fail-close にすると、bypass env の乱用が増える可能性がある

### 関連する実装の範囲

PLAN-089 の実装範囲:
- `cli/helix-gate`: `run_gate_design_doc_web_search_audit` advisory → fail-close 段階設計
- `cli/lib/migrations/v33_*.py`: helix.db v33 migration (schema_version table drift 修正も同時実施)
- PRAGMA → schema_version table への全面置換 (ADR-020 注記に記載の carry 解消)

---

## Decision

**設計 doc Web 検索 audit の fail-close 化を 4 Phase で段階的に実施する。**

具体的な実装:
1. **Phase 1 (advisory 計測)**: helix-gate G2/G3 で advisory チェックを実施し、未準拠率を計測する。bypass 使用を記録する (環境変数は settings.json に永続化しない)
2. **Phase 2 (fail-close 化)**: 計測期間 (1-2 session) のデータを元に fail-close に切替。helix-gate G2/G3 が Web 検索 section 不在 → exit 2 で block
3. **Phase 3 (既存 PLAN retrofit)**: PLAN-001〜090 に業界 standard 参照 section を追加 (PLAN-100 Phase 3 と連動)
4. **Phase 4 (carry 解消)**: Phase 1-3 で発見した残件を解消

**tl-advisor 相談の意見** (bi9qaatd6):
- 「一括切替は blast radius 大、advisory 計測期間を Phase 1 で設ける」
- 「bypass env を settings.json に永続化しない (恒久例外化リスク)」
- 両方の意見を採用済み

**helix.db v33 migration の同時実施**:
- PRAGMA user_version → schema_version table への全面置換 (ADR-020 注記の carry 解消)
- v33 migration は idempotent (`CREATE TABLE IF NOT EXISTS`) で実装

---

## Consequences

### Positive

- 段階導入により blast radius を最小化した上で fail-close を達成できる
- advisory 計測期間のデータに基づいた evidence-driven な fail-close 閾値設定が可能
- helix.db v33 で schema_version drift が解消され、migration 基盤が安定化する

### Negative

- Phase 1→2 の遷移判断タイミングが曖昧になりやすい (計測期間の明示が必要)
- 段階導入中は「advisory で通過したが実際は非準拠」の状態が継続する
- bypass env の管理が session をまたぐ場合に難しい (Claude Code は tool call 間で env を継承しない)

---

## Alternatives

### A案 (棄却): 即時 fail-close (一括切替)

- 採用しない理由: tl-advisor 相談で「blast radius 大」と評価。既存 PLAN-001〜090 の全件が block されることは HELIX 開発継続に支障が出る

### B案 (棄却): advisory のみで運用継続 (fail-close なし)

- 採用しない理由: advisory は無視されるリスクが高い。PLAN-087 のガードレール目的 (思いつき設計の構造的防止) に反する

### C案 (採用): 段階的 fail-close (本 ADR の実装方針)

- 採用済み: Phase 1 advisory 計測 → Phase 2 fail-close の段階移行が PLAN-089 の設計に組み込まれている

---

## Implementation Status

**実装完了 (2026-05-19)**: PLAN-089 が commit 35d8a30 で実装済み。本 ADR は L2 凍結 snapshot として後追い起票 (2026-05-20)。

| 実装内容 | commit | 状態 |
|---|---|---|
| helix-gate advisory audit 実装 (Phase 1) | 22ce096 / 35d8a30 | 完了 |
| helix.db v33 migration (schema_version drift 修正) | 35d8a30 | 完了 |
| PreToolUse hook fail-close (Phase 2 本番) | 35d8a30 | 完了 (hook 側は完了、gate 側は Phase 2 carry) |
| 既存 PLAN retrofit (Phase 3) | - | PLAN-100 Phase 3 carry |

**本 ADR 起票後**: PLAN-089 frontmatter への `related_adr: [ADR-023]` 追加は PLAN-100 Phase 2 (別 session) で実施する。
