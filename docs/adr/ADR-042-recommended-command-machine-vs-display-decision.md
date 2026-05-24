---
adr_id: ADR-042
title: recommended_command 機械契約 vs 人間表示の役割分離 (suggest_command backward compat + 新 field 役割固定)
status: Proposed
date: 2026-05-24
deciders:
  - PM (Opus)
  - TL-advisor (gpt-5.5 high、tl-advisor R1 (PLAN C') で recommended_command の二重契約矛盾発覚、ADR snapshot 必須化判定)
related_plans:
  - parent: null
  - L2_snapshot_of: L7-route-engine-drift-type-retrofit-ext (PLAN C')
  - dependent_plans: L7-cli-helix-refactor-impl (PLAN B), L7-cli-helix-retrofit-impl (PLAN C), L7-cli-helix-recovery-impl (PLAN D)
supersedes: []
superseded_by: []
---

# ADR-042: recommended_command 機械契約 vs 人間表示の役割分離

## Status

**Proposed** — 2026-05-24 (tl-advisor R2 + pm-advisor adversarial check 後に Accepted へ推進予定)

### Status History

- 2026-05-24 (初版): **Proposed** — tl-advisor R1 (PLAN C') で `recommended_command` が「人間向け表示専用」と「後続 CLI に渡す契約」の両方として書かれ矛盾発覚、ADR snapshot で役割凍結

## Context

### 動機

PLAN C' (route_engine 拡張) で `recommended_command` field を新設したが、tl-advisor R1 (P1 指摘) で **二重契約矛盾** が発覚:

- 一方の解釈: `recommended_command` は「人間向け表示専用」 (cli_hint、文字列、informational)
- 他方の解釈: `recommended_command` は「後続 CLI に渡す機械契約」 (parsable command, 構造化 args)

さらに PLAN B/C/D で **接続コマンドの非統一**:
- PLAN B: `helix refactor init --drift-type ...`
- PLAN C: `helix retrofit init --slug ...`
- PLAN C': `helix plan draft --kind retrofit --drift-type ...`
- PLAN D: `helix recovery start --signal-id runaway`

→ どれが正式契約か **route_engine 側で決まらず** に SE 実装に入ると、`helix retrofit init` と `helix plan draft --kind retrofit` の二重入口が発生する。

### 既存 mitigation の限界

- **`suggest_command` field** (現行 `RouteResult`): 「人間向け表示」として既に存在、変更不可 (backward compat)
- **PLAN 各々で接続コマンド記述**: PLAN B/C/D で drift しやすい、route_engine と PLAN の整合が取れない
- **detection-routing.md** (parent design): signal → mode マッピングのみで、接続コマンド契約は未定義

### 業界動向 (WebSearch 3 query 結果、2026-05-24)

| query | findings | 引用箇所 |
|---|---|---|
| CLI command field human display vs machine contract separation API design 2026 | **Dual-Interface Architecture**: 2026 標準、CLI/MCP の両方を支援。**Separation of Presentation and Data Layers**: presentation layer (terminal printing) と data layer を分離して MCP 経由で公開推奨。**TTY vs JSON**: human が terminal 実行 → table、agent が non-TTY 実行 → JSON 自動。**CLI as API Contract**: agent には consistency、human には adaptability | 本 ADR §Decision の役割分離は industry standard の Dual-Interface Architecture に整合 |

詳細 source: [Fern: API design best practices 2026](https://www.buildwithfern.com/post/api-design-best-practices-guide), [Jonnyzzz: CLI is the New API and MCP](https://jonnyzzz.com/blog/2026/02/20/cli-tools-for-ai-agents/), [Apideck: MCP Server Eating Context Window](https://www.apideck.com/blog/mcp-server-eating-context-window-cli-alternative)

### 実測

PLAN C' draft §V3 接続契約に `recommended_command` field 仕様が記載されているが、人間 / 機械 どちらの契約かが曖昧。SE 実装段階で gap risk 高い。

## Decision

### 役割分離契約

| field | 役割 | 形式 | backward compat |
|---|---|---|---|
| `suggest_command` (既存) | **人間向け表示専用** (cli_hint) | 自然言語混じり可、stable string | **値変更禁止** (backward compat 最優先) |
| `recommended_command` (新規) | **後続 CLI に渡す機械契約** | parsable command + 構造化 args、JSON-serializable | 新規 field、additive |

### 機械契約の構造化 args (`recommended_command`)

```json
{
  "command": "helix plan draft",
  "args": {
    "kind": "retrofit",
    "drift_type": "dependency_outdated",
    "signal_id": "drift",
    "slug": "<auto>"
  },
  "exit_code_expectations": {
    "0": "PLAN draft created",
    "1": "validation error",
    "2": "duplicate plan_id"
  }
}
```

### 接続コマンド統一 (PLAN B/C/C'/D 共通)

route_engine の `recommended_command` は **`helix plan draft --kind <mode>` 統一**:
- PLAN B: `helix plan draft --kind refactor --drift-type code_smell`
- PLAN C: `helix plan draft --kind retrofit --drift-type dependency_outdated`
- PLAN D: `helix plan draft --kind recovery --signal-id runaway`

→ route_engine の責務 = **PLAN 起票を推奨**、各 mode CLI (`helix refactor init` 等) は PLAN 起票後の **手動着手** に限定。

不採用: `helix refactor init` / `helix retrofit init` を recommended_command に直接含める → route_engine が複数 mode CLI に依存、test surface 増。

### `suggest_command` (人間表示) との関係

```python
# 例
suggest_command = "コード劣化を検出しました。`helix plan draft --kind refactor` で PLAN を起票してください。"
recommended_command = {
  "command": "helix plan draft",
  "args": {"kind": "refactor", "drift_type": "code_smell", "signal_id": "drift"}
}
```

`suggest_command` は人間向け解説、`recommended_command` は agent / CI 向けの構造化契約。両者は意味的に等価だが、formal な機械契約は `recommended_command` のみ。

## Consequences

### 利点

- PLAN B/C/D の接続コマンド drift が発生しない (route_engine が SoT)
- agent (Codex / Claude) が `recommended_command` を JSON parse して直接実行可能
- 人間が terminal で `helix route eval` を実行した時、`suggest_command` で読みやすい説明取得
- backward compat: 既存 `suggest_command` を使う test / CI が引き続き動作

### 受け入れる欠点

- `recommended_command` 新設で route_engine の RouteResult dataclass field 増 (1 field)
- 機械契約の JSON schema 管理が将来課題 (ADR-041 と組合せて strict parser に推進)
- `suggest_command` と `recommended_command` の意味的等価性 test が必要

### 運用影響

- `helix route eval --format machine` で `recommended_command` JSON 取得 (新規 format)
- `helix route eval --format command` は `suggest_command` 文字列を出力 (既存、backward compat)
- 各 mode CLI (refactor / retrofit / recovery) は PLAN 起票後の手動着手フローに整理

## Alternatives

### 代替案 A: `recommended_command` を廃止、`suggest_command` 一本化

不採用理由: 人間表示と機械契約を 1 field に詰めると、agent の JSON parsing が壊れる。industry standard (Dual-Interface Architecture) と逆行。

### 代替案 B: `recommended_command` に各 mode CLI (`helix refactor init` 等) を直接含める

不採用理由: route_engine が 4 mode CLI に依存、test surface 増。PLAN 起票を経由しない直接実行は HELIX V2 PLAN-first 原則 (全工程 PLAN 起票) に反する。

### 代替案 C: `recommended_command` を ADR snapshot せず PLAN 内で完結

不採用理由: 4 PLAN (B/C/D/C') で drift しやすい、SoT 不在で integration test 不可。L2 大局判断は ADR snapshot 必須 (CLAUDE.md §PLAN ⊃ ADR レイヤー併存)。

## Related

- 関連 PLAN: L7-cli-helix-refactor-impl (PLAN B) / L7-cli-helix-retrofit-impl (PLAN C) / L7-cli-helix-recovery-impl (PLAN D) / L7-route-engine-drift-type-retrofit-ext (PLAN C')
- 関連 D-shard: なし (本 ADR は L2 大局判断、D-shard は SE 委譲段階で生成)
- 関連 ADR:
  - ADR-041 (drift_type 7 種分類) — 同時起票、`recommended_command.args.drift_type` で参照
  - ADR-043 (Mode enum 拡張) — Mode 値が `recommended_command.args.kind` に対応

## 業界 standard 参照

| 参照 | source URL | 引用箇所 |
|---|---|---|
| Fern: API design best practices 2026 | https://www.buildwithfern.com/post/api-design-best-practices-guide | §Context 業界動向 (Contract-first design 概念) |
| Jonnyzzz: CLI is the New API and MCP | https://jonnyzzz.com/blog/2026/02/20/cli-tools-for-ai-agents/ | §Context 業界動向 (Dual-Interface Architecture、CLI as API Contract) |
| Apideck: MCP Server Eating Context Window | https://www.apideck.com/blog/mcp-server-eating-context-window-cli-alternative | §Context 業界動向 (Presentation vs Data Layer separation、TTY vs JSON) |

## References

- 公式ドキュメント: HELIX-workflows/helix-process/detection-routing.md (parent design)
- 調査メモ: PLAN C' R1 rollout JSONL (`~/.codex/sessions/2026/05/24/rollout-2026-05-24T22-16-05*.jsonl`)、特に P0-3 (B/C/C' 接続コマンド契約未確定) + P1 (recommended_command 二重契約)
- 実装 / テスト: cli/lib/route_engine.py (RouteResult 拡張)、cli/lib/tests/test_route_engine.py (`recommended_command` JSON 構造 test)
