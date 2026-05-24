---
adr_id: ADR-042
title: recommended_command 機械契約 vs 人間表示の役割分離 (suggest_command backward compat + 新 field 役割固定)
status: Accepted
date: 2026-05-24
accepted_date: 2026-05-25
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

**Accepted with conditions** — 2026-05-25 (tl-advisor R5 で P0 なし、PLAN C' P1-R5-1/-2 修正済を確認、Accepted 化推進)

### Status History

- 2026-05-24 (初版): **Proposed** — tl-advisor R1 (PLAN C') で `recommended_command` が「人間向け表示専用」と「後続 CLI に渡す契約」の両方として書かれ矛盾発覚、ADR snapshot で役割凍結
- 2026-05-24 (R1 revision): tl-advisor R1 (3 ADR 統合 review) で **needs_revision** 判定、P0-1 (JSON object vs string 矛盾) を `RecommendedCommandV1` schema + `schema_version`/`safety` field で一本化、P1-3 (Recovery 接続例外) を §接続コマンド統一表に追加、P1-4 (`suggest_command` backward compat 固定表) を §Decision 末尾に追加、tl-advisor R2 待ち
- 2026-05-24 (R2 revision): tl-advisor R2 で **needs_revision** (P0 なし、P1 5 件)、P1-3 (`safety.requires_preflight` field 追加) + P1-4 (`suggest_command` 固定表を route_engine.py L53-61 全 signal 11 行に拡張、`regression_prod`/`unknown_design`/`degradation` alias/`incident` env 分岐含む) + P1-2 (`helix plan draft` machine args 拡張は別 PLAN carry `L7-helix-plan-draft-machine-args-ext` として明示) + P1-5 (`--format machine` 廃止、`--format json` additive 採用 = 代替案 C) を §Decision に反映、tl-advisor R3 待ち
- 2026-05-24 (R3/R4 revision): R3/R4 統合 review P1 8 件全反映 (commit 3633646)、`recommended_command` JSON object 一本化を schema_version/safety 3 field (auto_apply/requires_human_approval/requires_preflight) で完全化
- 2026-05-25 (R5 → Accepted with conditions): tl-advisor R5 (rollout JSONL bypass) で **P0 なし**、PLAN C' P1-R5-1 (safety 4 field の誤記 → 3 field 訂正)、P1-R5-2 (PLAN C' R4 役割逆転訂正 = `recommended_command` 機械契約 / `suggest_command` 人間表示) を本 session で修正済。Accepted with conditions の条件 = (1) PLAN C' 上記 2 件修正反映済 (2) `helix plan draft` machine args 拡張 (`L7-helix-plan-draft-machine-args-ext`) は後続 PLAN 依存 (3) PLAN C' §10 で本 ADR の Accepted 化と同期済

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
| `suggest_command` (既存) | **人間向け表示専用** (cli_hint) | 自然言語混じり可、stable string | **値変更禁止** (既存 signal 全件、§Decision 末尾の固定表参照) |
| `recommended_command` (新規) | **後続 CLI に渡す機械契約** | **JSON object 一本化** (string 形式は禁止)、JSON-serializable | 新規 field、additive |

**重要 (R1 P0-1 反映)**: `recommended_command` は string 形式を**禁止**、必ず JSON object。PLAN C'/B/C/D の string 期待記述は R3 反映で JSON parse に修正必須。

### 機械契約 schema `RecommendedCommandV1` (R1 P0-1 反映、JSON 一本化)

```json
{
  "schema_version": "v1",
  "command": "helix plan draft",
  "args": {
    "kind": "retrofit",
    "drift_type": "dependency_outdated",
    "signal_id": "drift",
    "slug": "<auto>"
  },
  "safety": {
    "auto_apply": false,
    "requires_human_approval": false,
    "requires_preflight": false
  },
  "exit_code_expectations": {
    "0": "PLAN draft created",
    "1": "validation error",
    "2": "duplicate plan_id"
  }
}
```

`schema_version`: 将来の schema 変更時に additive で `v2` 等に拡張。strict parser は unknown schema_version で fail-close。
`safety.auto_apply`: agent が確認なしに即実行可否 (default false)。
`safety.requires_human_approval`: 人間承認必須フラグ (env/infra/prod 変更時 true、R1 P1-2 反映)。
`safety.requires_preflight`: **前段 preflight 必須フラグ** (R2 P1-3 反映、ADR-041 `upgrade` 高リスク時の Reverse upgrade R0-R4 前段に対応、default false)。requires_preflight=true 時は `command` を `helix reverse upgrade R0` 等に変更してから本 command 実行。

### 接続コマンド統一 (PLAN B/C/C' 共通) + **Recovery 例外** (R1 P1-3 反映)

route_engine の `recommended_command` は **`helix plan draft --kind <mode>` 統一**:
- PLAN B (Refactor): `helix plan draft --kind refactor --drift-type code_smell`
- PLAN C (Retrofit): `helix plan draft --kind retrofit --drift-type dependency_outdated`

**★ Recovery は例外** (PLAN D 既存契約 `helix recover plan --signal-id` 維持):
- PLAN D (Recovery): `helix recover plan --signal-id runaway --auto-routed-from helix-route`
- 理由: PLAN D §11 と現行 `cli/lib/route_engine.py` の `signal_to_condition()` が既に `recover plan` 契約を持つ。`helix plan draft --kind recovery` への移行は別 PLAN candidate carry (PLAN D 完遂後検討)

→ route_engine の責務 = **refactor/retrofit は PLAN 起票推奨、recovery は recover plan 推奨**。

各 mode CLI (`helix refactor init` / `helix retrofit init` 等) は PLAN 起票後の **手動着手** に限定 (refactor/retrofit のみ)。

### `suggest_command` backward compat 固定表 (R2 P1-4 反映、現行 route_engine.py L53-61 全 signal)

`cli/lib/route_engine.py:53-61` の `SIGNAL_TO_MODE` 全 signal を全件凍結:

| signal | 既存 `suggest_command` | mode | 値変更可否 |
|---|---|---|---|
| `drift` (schema/contract) | `helix reverse normalization R0` | Reverse | **凍結** (変更禁止) |
| `drift` (code_smell/structural) | `helix plan draft --kind refactor` (新規) | Refactor | 追加 (本 ADR で凍結) |
| `dependency_outdated` / `upgrade` / `config_drift` | `helix plan draft --kind retrofit` (新規) | Retrofit | 追加 (本 ADR で凍結) |
| `runaway` | `helix recover plan --signal-id runaway` | Recovery | **凍結** (PLAN D 既存、Recovery 例外) |
| `regression_dev` | 既存値 (recover_engine.signal_to_condition 参照) | Recovery | **凍結** |
| `regression_prod` | 既存値 (現行 route_engine が返す) | Recovery | **凍結** (R2 P1-4 追加) |
| `incident` (env=prod) | `helix recover plan --signal-id incident` (Recovery 経由) | Recovery | **凍結** |
| `incident` (env=dev) | `helix plan draft --kind troubleshoot` (Incident と区別) | Troubleshoot | **凍結** (R2 P1-4 追加、env 分岐明示) |
| `unknown_design` | `helix reverse code R0` (現状 Reverse(code) 固定) | Reverse | **凍結** (R2 P1-4 追加) |
| `degradation` (alias) | `debt_degradation` への alias 維持 | Refactor (debt_degradation 経由) | **凍結** (R2 P1-4 追加、alias) |
| `debt_degradation` | `helix plan draft --kind refactor --from-debt-id <id>` | Refactor | 追加 |

既存 `eval --format command` は本表の `suggest_command` 文字列を返す (R2 P1-4 反映で route_engine.py L53-61 全 signal 凍結、deprecation alias 含む)。

### `helix plan draft` machine args 接続 (R2 P1-2 反映)

ADR-042 の `recommended_command.command = "helix plan draft"` + `args` (`kind/drift_type/signal_id/slug`) は **現行 `cli/helix-plan-cmds/draft.sh:28-54` が受けない args**。R2 で以下を carry C-NEW として確定:

1. **`helix plan draft --kind/--drift-type/--signal-id/--slug` 拡張**は別 PLAN candidate (`L7-helix-plan-draft-machine-args-ext`、ADR-042 Accepted 後の前提依存) として起票必須
2. **本 ADR Accepted の前提依存 dependency**: 本 ADR の `recommended_command` machine contract を実行可能にするには、上記別 PLAN の完遂が必要 (本 ADR Status を `Accepted with conditions` とし、condition #2 として明示)
3. **暫定対応**: 別 PLAN 完遂前は `recommended_command.command = "helix plan draft"` + `args` を suggestion (人間が args を手動で `--title`/`--file`/`--plan-id` に変換) として使う

### `--format machine` 廃止、`--format json` に additive 拡張 (R2 P1-5 代替案 C 採用)

ADR-042 当初案 `--format machine` 新規 format は現行 `cli/lib/route_engine.py:265` が `json|command` のみで不整合。R2 で **代替案 C 採用**:

- `--format machine` は**廃止** (新 format 増やさない)
- `--format json` 出力に `recommended_command` object を **additive 追加** (既存 caller 互換)
- 既存 `--format json` consumer は新 field を ignore で動作維持 (additive backward compat)

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

- `helix route eval --format json` 出力に `recommended_command` JSON object を additive 追加 (R2 P1-5 代替案 C 採用、既存 caller 互換維持)
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
