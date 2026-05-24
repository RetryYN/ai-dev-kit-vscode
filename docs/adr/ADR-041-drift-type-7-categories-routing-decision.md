---
adr_id: ADR-041
title: drift_type 7 種分類 + Reverse/Refactor/Retrofit 3 mode 分岐ルーティング契約
status: Proposed
date: 2026-05-24
deciders:
  - PM (Opus)
  - TL-advisor (gpt-5.5 high、tl-advisor R1 (PLAN C') で本契約の必要性発見、ADR snapshot 必須化判定)
related_plans:
  - parent: null
  - L2_snapshot_of: L7-route-engine-drift-type-retrofit-ext (PLAN C')
  - dependent_plans: L7-cli-helix-refactor-impl (PLAN B), L7-cli-helix-retrofit-impl (PLAN C)
supersedes: []
superseded_by: []
---

# ADR-041: drift_type 7 種分類 + Reverse/Refactor/Retrofit 3 mode 分岐ルーティング契約

## Status

**Proposed** — 2026-05-24 (tl-advisor R2 + pm-advisor adversarial check 後に Accepted へ推進予定)

### Status History

- 2026-05-24 (初版): **Proposed** — PLAN B/C/C' の tl-advisor R1 で drift_type 7 種境界の必要性発覚 (PLAN C' R1 §L2 凍結 候補 #1)、本 ADR で contract 凍結
- 2026-05-24 (R1 revision): tl-advisor R1 (3 ADR 統合 review、rollout JSONL bypass で抽出) で **needs_revision** 判定、P1-1 (upgrade Reverse vs Retrofit 境界) + P1-2 (config_drift env/infra 人間承認) を §Decision に反映、tl-advisor R2 待ち
- 2026-05-24 (R2 revision): tl-advisor R2 で **needs_revision** (P0 なし、P1 5 件 + P2 3 件)、P1-3 (`requires_preflight` schema 不整合) を ADR-042 schema 拡張 + 本 ADR `upgrade` 行で参照、tl-advisor R3 待ち

## Context

### 動機

HELIX-workflows V2 で `refactor` / `retrofit` mode が独立 mode として整理されたが、`detection-routing.md` の上位 signal `drift` (設計⇔実装乖離) を 3 mode (Reverse / Refactor / Retrofit) に分岐する **drift_type の正式分類が PLAN B/C/C' で不一致**:

- 当初 PLAN B (refactor) の §8 で 4 種 (schema/contract/code_smell/structural) のみ列挙
- PLAN C' (route_engine 拡張) で 7 種 (前 4 + dependency_outdated/upgrade/config_drift) と再定義
- PLAN B/C/C' で「drift_type 7 種統一」を申し合わせたが、**正式 contract として ADR snapshot で凍結する必要**

これは PLAN ⊃ ADR レイヤー併存原則 (CLAUDE.md §PLAN ⊃ ADR レイヤー併存) に該当する L2 大局判断であり、3 PLAN の SE 委譲前に共通契約として凍結する。

### 既存 mitigation の限界

- **PLAN 内 drift_type 表** (PLAN B §8 / PLAN C §9 / PLAN C' §2.2): 3 PLAN で表内容が drift しやすい
- **route_engine.py 直接実装** (現行): `Mode = Reverse|Refactor|Recovery|Incident` のみで Retrofit 未対応、drift_type field 不在
- **detection-routing.md** (accepted parent design): signal `drift` を Reverse normalization に固定、Refactor / Retrofit への分岐根拠なし

### 業界動向 (WebSearch 3 query 結果、2026-05-24)

| query | findings | 引用箇所 |
|---|---|---|
| drift detection signal taxonomy code quality refactor retrofit 2026 | FutureAGI: input-output-cost-rubric drift taxonomy / 6 metric categories (input/output/embedding/rubric/operational/retrieval health)、Context Drift Detection: 4 signals (schema staleness, glossary age, lineage gaps, ownership freshness) | 本 ADR §Decision の drift_type 7 種分類は industry standard の signal taxonomy 概念に整合 |
| - | - | - |

詳細 source: [FutureAGI: What is LLM Drift?](https://futureagi.com/blog/what-is-llm-drift-2026), [Context Drift Detection Guide](https://atlan.com/know/context-drift-detection/)

### 実測

`cli/lib/route_engine.py` 現行:
- L16: `Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]` (Retrofit 未追加)
- `SIGNAL_TO_MODE` に `dependency_outdated/upgrade/config_drift` キー不在
- `RouteResult` dataclass に `drift_type` field 不在

PLAN B/C/C' 起票時点で drift_type 表の整合性確認が必須となっている。

## Decision

### drift_type 7 種正式分類

| drift_type | ルーティング先 | 説明 |
|---|---|---|
| `schema` | **Reverse (normalization)** | DB schema drift (DDL ↔ migration) |
| `contract` | **Reverse (normalization)** | API contract / Type definition drift |
| `code_smell` | **Refactor** | コード品質劣化 (複雑度 / 重複 / 命名) |
| `structural` | **Refactor** | 内部構造改善 (振る舞い不変) |
| `dependency_outdated` | **Retrofit** | 依存 library version 古い |
| `upgrade` | **Retrofit (条件付き)** | runtime / framework / language version 移行。**uncertainty=high or impact=high 時は Reverse upgrade R0-R4 を前段** (R1 P1-1 反映、機械契約は `recommended_command.safety.requires_preflight=true` + `recommended_command.command = "helix reverse upgrade R0"`、ADR-042 schema §RecommendedCommandV1 `safety.requires_preflight` field を参照、R2 P1-3 反映)。低リスク時のみ Retrofit 直行 |
| `config_drift` | **Retrofit (人間承認必須)** | config / env / infra 設定 drift。**env / infrastructure / production config は人間確認対象** (HELIX escalation 境界、CLAUDE.md §禁止事項)。route_engine は plan draft 提案まで、**auto apply 禁止**、`recommended_command.safety.requires_human_approval=true` 固定 (R1 P1-2 反映) |

### 実装契約

1. `cli/lib/route_engine.py`:
   - `Mode` enum に `Retrofit` 追加 (additive、ADR-043 で別 freeze)
   - `RouteResult` dataclass に `drift_type: str | None` field 追加
   - `DRIFT_TYPE_TO_MODE` dict 新設: `{"schema": "Reverse", "contract": "Reverse", "code_smell": "Refactor", ..., "config_drift": "Retrofit"}`
   - shortcut signal (`dependency_outdated`/`upgrade`/`config_drift`) は `SIGNAL_TO_MODE` で直接 Retrofit に mapping + `_resolve_drift_type()` で `RouteResult.drift_type` に正しい値を必ず埋める (PLAN C' R1 P0-1 解消)

2. `helix route eval` / `helix route suggest` の出力:
   - JSON に `drift_type` field 追加 (additive、既存 parser 互換)
   - `eval --format command` の `suggest_command` 値は変更しない (backward compat、ADR-042 と整合)

3. PLAN B/C/C' の §V3 接続契約:
   - 本 ADR-041 を `related_docs` に明示 reference
   - drift_type 表を本 ADR から copy せず、本 ADR を single source of truth として参照

## Consequences

### 利点

- 3 PLAN (B/C/C') の drift_type 表 drift が物理的に発生しない (本 ADR が SoT)
- route_engine 拡張時の test coverage が drift_type 7 種で網羅化 (U-EXT 系)
- 将来の mode 追加 (例: Add-feature / Refactor 細分化) でも本 ADR を superseded → 新 ADR で extend する pattern が確立

### 受け入れる欠点

- ADR snapshot 起票工数 (~150 行) が PLAN 起票時に追加発生
- drift_type 増減時に本 ADR の Status History 更新が必要 (運用負荷)
- 既存 `detection-routing.md` (parent design) との freeze break は ADR-043 で別途凍結 (依存)

### 運用影響

- HELIX-workflows V2 entry mode 判定で `drift_type` が一次入力に昇格 (signal は補助)
- `helix doctor` の drift_type 矛盾検出が将来課題 (本 ADR scope 外、別 PLAN candidate)
- detection-routing.md の Reverse(normalization) 行は `schema/contract` 限定に補足注記必要

## Alternatives

### 代替案 A: PLAN 内 drift_type 表のみで運用 (ADR 不要)

不採用理由: 3 PLAN で drift しやすい、SoT 不在で integration test 不可。本 session で実際に 4 種 (PLAN B 初版) vs 7 種 (PLAN C' 初版) の drift 発覚。

### 代替案 B: drift_type を route_engine 内部 enum のみで管理 (PLAN 外)

不採用理由: PLAN B/C の §V3 接続契約 で drift_type 7 種を参照する必要、PLAN frontmatter の `requires` 依存が解決できない。L2 大局判断は ADR snapshot 必須 (HELIX 原則)。

### 代替案 C: drift_type を 4 種に絞る (前 4 のみ、Retrofit 系は別 signal にする)

不採用理由: detection-routing.md の上位 signal `drift` を細分化する方が概念的に clean。`dependency_outdated`/`upgrade`/`config_drift` を独立 signal にすると signal vocabulary が肥大化 (5 → 8+ 種)、route_engine の `SIGNAL_TO_MODE` が複雑化。

## Related

- 関連 PLAN: L7-cli-helix-refactor-impl (PLAN B) / L7-cli-helix-retrofit-impl (PLAN C) / L7-route-engine-drift-type-retrofit-ext (PLAN C')
- 関連 D-shard: なし (本 ADR は L2 大局判断、D-shard は SE 委譲段階で生成)
- 関連 ADR:
  - ADR-042 (recommended_command 共存方針) — 同時起票、本 ADR と integration
  - ADR-043 (Mode enum 拡張 parent design freeze break) — 本 ADR の前提依存
  - ADR-020 (cutover rollback gates) — recovery_engine 関連で間接参照

## 業界 standard 参照

| 参照 | source URL | 引用箇所 |
|---|---|---|
| FutureAGI: LLM Drift Taxonomy 2026 | https://futureagi.com/blog/what-is-llm-drift-2026 | §Context 業界動向 (input-output-cost-rubric drift taxonomy / 6 metric categories) |
| Context Drift Detection Guide (Atlan) | https://atlan.com/know/context-drift-detection/ | §Context 業界動向 (4 signals: schema staleness / glossary age / lineage gaps / ownership freshness) |
| Architectural Decision Records | https://adr.github.io/ | §Status (superseded pattern、ADR-043 と組合せ) |

## References

- 公式ドキュメント: HELIX-workflows/helix-process/detection-routing.md (parent design)
- 調査メモ: PLAN C' R1 rollout JSONL (`~/.codex/sessions/2026/05/24/rollout-2026-05-24T22-16-05*.jsonl`)
- 実装 / テスト: cli/lib/route_engine.py (拡張対象)、cli/lib/tests/test_route_engine.py + cli/lib/tests/bats/helix_route.bats (PLAN C' で新規)
