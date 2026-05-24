---
adr_id: ADR-043
title: Mode enum 拡張 (Retrofit 追加) — parent design freeze break + additive backward compat 凍結
status: Proposed
date: 2026-05-24
deciders:
  - PM (Opus)
  - TL-advisor (gpt-5.5 high、tl-advisor R1 (PLAN C') で「accepted parent design への Retrofit 追加は ADR snapshot 必須」指摘、ADR snapshot で凍結)
related_plans:
  - parent: null
  - L2_snapshot_of: L7-route-engine-drift-type-retrofit-ext (PLAN C')
  - dependent_plans: L7-cli-helix-retrofit-impl (PLAN C)
supersedes: []
superseded_by: []
---

# ADR-043: Mode enum 拡張 (Retrofit 追加) — parent design freeze break

## Status

**Proposed** — 2026-05-24 (tl-advisor R2 + pm-advisor adversarial check 後に Accepted へ推進予定)

### Status History

- 2026-05-24 (初版): **Proposed** — tl-advisor R1 (PLAN C') で「accepted parent design (detection-routing.md) は Retrofit 含まない、Mode enum に Retrofit 追加するなら L2 ADR snapshot で凍結すること」指摘、本 ADR で凍結
- 2026-05-24 (R1 revision): tl-advisor R1 (3 ADR 統合 review) で **needs_revision** 判定、P0-2 (parent design footnote 自己矛盾、detection-routing.md に §5 不在) を **PLAN frontmatter `parent_design` 複数値並記 pattern** に変更 (detection-routing.md 完全不変更維持)、P1-5 (additive backward compat 影響調査) を §Decision 末尾に追加、tl-advisor R2 待ち

## Context

### 動機

`cli/lib/route_engine.py` 現行:
```python
Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]
```

HELIX-workflows V2 で **Retrofit mode** が独立 mode として整理されたが (`HELIX-workflows/helix-process/retrofit-workflow.md` accepted)、`route_engine.py` の Mode enum と `detection-routing.md` (accepted parent design) には **Retrofit 未追加**。

PLAN C (retrofit CLI) + PLAN C' (route_engine 拡張) を SE 実装するには、Mode enum に `Retrofit` を追加する必要があるが、これは **accepted parent design の freeze break** に相当し、CLAUDE.md §PLAN ⊃ ADR レイヤー併存原則により **L2 ADR snapshot で凍結が必須**。

### 既存 mitigation の限界

- **PLAN C' frontmatter `parent_design`** (現在 `detection-routing.md`): 追記なしでは Retrofit mode が parent design に存在しないため、SE 実装が context drift する
- **`detection-routing.md` 直接編集**: accepted 状態の parent design を ADR snapshot なしで変更するのは HELIX V2 規約違反 (commit f409c55 で V1 PLAN は is_reference: true marked、V2 accepted doc も同様の凍結思想)
- **PLAN C 内で Mode 拡張記述**: PLAN は実装計画、L2 大局判断 (parent design 変更) を含めるのは責務違反

### 業界動向 (WebSearch 3 query 結果、2026-05-24)

| query | findings | 引用箇所 |
|---|---|---|
| enum extension backward compatibility ADR architecture decision record pattern 2026 | **ADR pattern**: 「Once an ADR is accepted, it should never be reopened or changed - instead it should be superseded」(adr.github.io)、Backstage / VA Design System / AWS Prescriptive Guidance 全て同 pattern。**Status flow**: proposed → accepted → superseded。**Martin Fowler ADR**: short document, single decision, context + consequences + open questions | 本 ADR は detection-routing.md を superseded せず、**追補 ADR として並存** させる pattern を採用 (additive backward compat) |

詳細 source: [adr.github.io: Architectural Decision Records](https://adr.github.io/), [Martin Fowler bliki: ADR](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html), [AWS Prescriptive Guidance: ADR process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html)

### 実測

PLAN C' draft §2.1 で Mode enum 拡張仕様あるが、parent design freeze break の ADR snapshot 不在。tl-advisor R1 で「Mode enum 拡張前に L2 ADR snapshot 必須」と blocking 指摘。

## Decision

### Mode enum 拡張 (additive backward compat)

```python
# cli/lib/route_engine.py 拡張後
Mode = Literal["Reverse", "Refactor", "Retrofit", "Recovery", "Incident"]
```

**順序**: Retrofit は Refactor と Recovery の間 (関連 mode を隣接)。既存値 (Reverse/Refactor/Recovery/Incident) の順序・spelling は変更しない (backward compat)。

### parent design (detection-routing.md) との関係 (R1 P0-2 反映、自己矛盾解消)

**重要 (R1 P0-2 反映)**: 当初案「detection-routing.md 本文不変更 + §5 footnote 追記」は、現行 detection-routing.md に §5 / Mode 一覧が**存在しない**ため自己矛盾。本 revision で **detection-routing.md は完全不変更** + **PLAN frontmatter で `parent_design` 複数値並記** pattern に修正。

- `detection-routing.md` 本文は **完全に変更しない** (accepted 凍結維持、footnote 追記も行わない)
- PLAN C / C' (および本 ADR 影響範囲) の `parent_design` field を **複数値 list** にし、`detection-routing.md` と `ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md` の両方を併記:

```yaml
# PLAN C' frontmatter 例 (R3 反映で対応)
parent_design:
  - HELIX-workflows/helix-process/detection-routing.md   # 上位 parent
  - docs/adr/ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md   # 追補 ADR (必読)
```

- PLAN reader (Codex SE / pmo-sonnet) は `parent_design` を順次 read し、ADR-043 で Retrofit mode の追補を必ず認識する
- ADR index.md / `docs/adr/helix-workflows-appendix.md` で ADR-043 を「detection-routing.md 追補」明示
- 将来 detection-routing.md v2 (新版) を起こす際に本 ADR を統合 → ADR-043 を superseded marker で凍結

### additive backward compat の影響調査 (R1 P1-5 反映)

旧 parser / caller が Mode enum を exhaustive parse している場合の破壊 risk 確認:

| caller | enum 扱い | 影響 | 対策 |
|---|---|---|---|
| `cli/lib/route_engine.py` 内部 | `Mode = Literal[...]` (mypy strict) | None (本 ADR で更新) | Mode に Retrofit 追加するだけ、既存 caller 不変 |
| `cli/lib/tests/test_route_engine.py` | assertion で Mode 値参照 | None (本 ADR で test 拡張) | Retrofit 含む新規 test case 追加、既存 test 不変 |
| `cli/helix-route` (bash) | JSON output の `mode` field を string 比較 | additive (Retrofit 値が新たに出現可) | 既存 caller は `mode in [Reverse|Refactor|Recovery|Incident]` の if-elif chain なら fallthrough、case match なら unknown error |
| `cli/helix-recover` | route_engine 経由で Mode 受領 | None (Retrofit を Recovery に escalation しない設計) | 影響なし |
| 外部 JSON consumer (HELIX 外) | unknown | **要調査** | 本 PLAN scope 外、carry C-AT として `helix doctor` で Mode caller 検出 framework 別 PLAN candidate |

→ **HELIX 内部 caller には破壊 risk なし**、外部 JSON consumer の調査は別 PLAN carry。

### backward compat 保証

1. **既存 Mode 値の値変更禁止**: Reverse / Refactor / Recovery / Incident の spelling は変更しない
2. **strict parser 対応**: 旧 parser で `Retrofit` を unknown enum として fallback (例: Incident) ではなく fail-close (`RouteEngineError: unknown mode 'Retrofit'`) する設計
3. **既存 test 互換**: `test_route_engine.py` の Mode 関連 assertion は変更不要、Retrofit を含む新規 test ケースのみ追加 (PLAN C' で U-EXT-001〜022 新規)
4. **既存呼び出し元**: `cli/helix-route` / `cli/helix-recover` 等の既存 caller は Mode 値の追加に依存しない (生成時に Mode を参照、enum 拡張で壊れない)

## Consequences

### 利点

- HELIX-workflows V2 の `retrofit-workflow.md` (accepted) と route_engine.py が論理的に整合
- PLAN C (retrofit CLI) と PLAN C' (route_engine 拡張) の SE 実装が parent design context drift なしで進行
- ADR snapshot pattern (proposed → accepted → superseded) を HELIX 内で運用実証
- 将来の mode 追加 (例: Add-feature / Refactor 細分化) でも同じ pattern (追補 ADR) で extend 可能

### 受け入れる欠点

- ADR snapshot 起票工数 (~120 行) が PLAN 起票時に追加発生
- `detection-routing.md` 本体と ADR-043 を 2 箇所 read する必要 (将来 v2 統合まで)
- parent design freeze break の ADR が増えると、ADR-021〜032 のような snapshot ADR が累積 (運用負荷)

### 運用影響

- HELIX-workflows V2 entry mode 判定で Retrofit が有効化
- `helix mode` / `helix size` / `helix doctor` の Mode 列挙対象に Retrofit 追加 (別 PLAN candidate carry)
- `cli/lib/plan_validator.py` の `VALID_KINDS` は既に `retrofit` 含む (PLAN C R1 で確認済)、ADR-043 で公式凍結

## Alternatives

### 代替案 A: detection-routing.md を直接編集 (ADR snapshot なし)

不採用理由: accepted parent design の freeze break 直接実施は HELIX V2 規約違反 (CLAUDE.md §PLAN ⊃ ADR レイヤー併存)。trace 不能、変更履歴が doc 内に残らない。

### 代替案 B: Retrofit mode 自体を諦め、Refactor で代替

不採用理由: HELIX-workflows V2 で Refactor (振る舞い不変) と Retrofit (依存・基盤段階改修) は意味的に別。混合すると workflow doc 整合性が崩れる。retrofit-workflow.md (accepted) との論理的整合が取れない。

### 代替案 C: 新 route_engine v2 を別 path に作る (現行は legacy)

不採用理由: route_engine の利用箇所が多 (helix-route / helix-recover / 将来の helix-refactor/retrofit/recovery / helix-discovery)、別 path 化は migration が広範囲。additive な enum 拡張で十分。

### 代替案 D: detection-routing.md v2 (新版) を本 session で起こす + Retrofit 含めて再 accept

不採用理由: detection-routing.md v2 起票は scope 過大 (本 session 規模を超える)、ADR snapshot で並存させる方が時間効率高い。将来 v2 起票時に本 ADR を統合 → superseded 化する pattern。

## Related

- 関連 PLAN: L7-cli-helix-retrofit-impl (PLAN C) / L7-route-engine-drift-type-retrofit-ext (PLAN C')
- 関連 D-shard: なし (本 ADR は L2 大局判断、D-shard は SE 委譲段階で生成)
- 関連 ADR:
  - ADR-041 (drift_type 7 種分類) — Mode 分岐先で参照
  - ADR-042 (recommended_command 共存方針) — Mode 値が `recommended_command.args.kind` に対応
- parent design: HELIX-workflows/helix-process/detection-routing.md (accepted、本 ADR で追補)

## 業界 standard 参照

| 参照 | source URL | 引用箇所 |
|---|---|---|
| adr.github.io: Architectural Decision Records | https://adr.github.io/ | §Decision 追補 ADR pattern (superseded vs additive) |
| Martin Fowler bliki: ADR | https://martinfowler.com/bliki/ArchitectureDecisionRecord.html | §Context (ADR は single decision を凍結) |
| AWS Prescriptive Guidance: ADR process | https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html | §Status (Status flow: proposed → accepted → superseded) |

## References

- 公式ドキュメント: HELIX-workflows/helix-process/detection-routing.md (parent design、本 ADR で追補)、HELIX-workflows/helix-process/retrofit-workflow.md (accepted、Retrofit mode の workflow 正本)
- 調査メモ: PLAN C' R1 rollout JSONL (`~/.codex/sessions/2026/05/24/rollout-2026-05-24T22-16-05*.jsonl`)、特に L2 凍結 候補 #3 (Mode enum 拡張)
- 実装 / テスト: cli/lib/route_engine.py (Mode Literal 拡張対象)、cli/lib/tests/test_route_engine.py (Mode = Retrofit assertion 新規)
