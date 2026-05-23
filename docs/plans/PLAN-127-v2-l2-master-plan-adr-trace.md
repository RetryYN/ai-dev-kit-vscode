---
plan_id: PLAN-127
title: "PLAN-127: V2 L2-MASTER PLAN ↔ ADR 双方向 trace 完遂"
layer: L2
kind: retrofit
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
drive: be
created: 2026-05-23
owner: PMO
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — trace map 抽出・L2-MASTER §0 拡張案作成・整合確認"
  - role: docs
    slot_label: "Docs — L2-MASTER.md §0 範例 section 編集"
generates:
  - artifact_path: docs/v2/L2-MASTER.md
    artifact_type: doc_update
dependencies:
  parent: null
  requires:
    - PLAN-100
  blocks: []
related_adr: []
related_plans:
  - PLAN-100-existing-retrofit-v2-revision
related_docs:
  - docs/v2/L2-MASTER.md
  - docs/plans/PLAN-100-existing-retrofit-v2-revision.md
  - helix/HELIX_CORE.md
---

# PLAN-127: V2 L2-MASTER PLAN ↔ ADR 双方向 trace 完遂

> **kind**: retrofit (既存 L2-MASTER.md §0 の PLAN↔ADR 範例を現行状態に合わせる更新)
> **layer**: L2 (L2-MASTER.md = 全体設計文書の更新)
> **drive**: be (CLI / framework doc 中心)
> **本 PLAN の役割**: PLAN-100 Phase 4 Wave 3 で計画されていた「L2-MASTER §0 範例拡張」を実施する。本 session で新規起票した PLAN ↔ ADR 双方向 trace を L2-MASTER §0 に明記し、次以降の PLAN 起票者が範例を正しく参照できる状態にする。

---

## §0. 本 PLAN の位置付け

PLAN-100 §6.3 は「L2-MASTER §0 line 36 の PLAN↔ADR 範例を更新する」計画を立てたが、実施は別 session とした。本 PLAN がその実施計画である。

現状の L2-MASTER §0 line 36 の記述:

```
「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」
```

この範例は V5 framework 確立前 (PLAN-084 / ADR-018/019) の例のみを示しており、本 session 以降に起票された PLAN 群 (PLAN-MM-001, PLAN-091〜127+) との対応関係が一切記載されていない。参照者が誤った古いパターンを手本にするリスクがある。

---

## §1. 目的

1. 全 PLAN frontmatter の `related_adr` + 全 ADR frontmatter の `related_plans` から trace map を機械的に抽出し、PLAN ↔ ADR 対応表を作成する (Sprint .1)
2. L2-MASTER §0 の「PLAN↔ADR 範例」section を更新し、V5 以降の trace 21+ 件を追加する (Sprint .2)
3. `helix doctor check_plan_adr_snapshot` による全件 PASS を確認し、双方向 trace 完全性を保証する (Sprint .3)

---

## §2. 背景

### 2.1 L2-MASTER §0 range の現状

PLAN-100 §6.3 で観測された drift:

| 記述 | 現状 | 正本 (CLAUDE.md / PLAN-100 §6.3) |
|---|---|---|
| PLAN↔ADR 範例 | PLAN-084 ↔ ADR-018/019 のみ | PLAN-MM-001〜127+ ↔ ADR-021〜044+ を含む最新版 |
| §12 既知矛盾 | M-01〜M-04 のみ | M-09〜M-12 具体内容が未追記 (PLAN-100 §6.3 Sprint 0 補完で計画済) |

### 2.2 trace 対象の規模

PLAN-100 完遂 (commit 803fc08) 以降に起票された PLAN は PLAN-101〜127 の 27 件。うち L2 大局判断を含む PLAN に対応する ADR が起票されていれば trace map に含める。

対応する ADR 群の例:

| PLAN | ADR | L2 大局判断内容 |
|---|---|---|
| PLAN-087 | ADR-021 | 設計 doc Web 検索ガードレール採用 |
| PLAN-088 | ADR-022 | TodoWrite × agent slot framework 採用 |
| PLAN-089 | ADR-023 | gate fail-close 段階遷移採用 |
| PLAN-090 | ADR-024 | continueOnBlock / active guidance loop 採用 |
| PLAN-101 | ADR-033 | ADR Decision Graph Registry 採用 |
| PLAN-MM-001 | ADR-025〜032 | V5 framework 全体設計 (8 ADR) |
| PLAN-091 | ADR-025 | V5 framework core (plan_validator + template) |
| PLAN-092 | ADR-026 | PostToolUse 自動登録 + helix.db v35 schema |
| PLAN-093 | ADR-027 | drift 検出 + 進捗 trace |
| PLAN-095 | ADR-028 | PoC = Scrum × Reverse matrix |
| PLAN-096 | ADR-029 | GitHub Actions ブランチタイプ別パイプライン |
| PLAN-097 | ADR-030 | 抽象化層 + エスカレーション |
| PLAN-098 | ADR-031 | リカバリープラン kind 正規化 |
| PLAN-099 | ADR-032 | 自動走行 framework 5-layer |

### 2.3 WebSearch skip 根拠

本 PLAN は既存文書 (L2-MASTER §0) の範例 section 更新であり、新 framework 採用や L2 大局判断を含まない。PLAN-087 ガードレールの「設計 doc 新規起票・大幅 scope 変更時」には該当しない。WebSearch skip 理由を evidence として記録する: **本 PLAN = retrofit (既存 doc の trace 情報追記)、L2 大局判断なし**。

---

## §3. 実装方針

### Sprint .1: trace map 抽出

- 対象: `docs/plans/PLAN-*.md` の frontmatter `related_adr` フィールド + `docs/adr/ADR-*.md` の frontmatter `related_plans` フィールド
- 手順:
  1. `pmo-sonnet` で全 PLAN frontmatter の `related_adr` を grep 抽出
  2. 全 ADR frontmatter の `related_plans` を grep 抽出
  3. 両方向を突合して trace 表 (PLAN ↔ ADR) を作成
  4. 片方向のみ trace (missing reverse) を P2 として carry note に記録

出力形式:

```markdown
| PLAN | ADR | 方向 | L2 大局判断内容 |
|---|---|---|---|
| PLAN-087 | ADR-021 | 双方向 | 設計 doc Web 検索ガードレール採用 |
...
```

### Sprint .2: L2-MASTER §0 拡張

更新対象: `docs/v2/L2-MASTER.md` §0 (line 36 付近の PLAN↔ADR 範例)

更新方針:
1. 既存の「PLAN-084 で L1 確定、ADR-018/019 で L2 凍結」の記述を保持 (backward compat)
2. 新規に「V5 framework 以降の trace 一覧」subsection を追加
3. Sprint .1 で作成した trace 表をそのまま挿入
4. §12 既知矛盾 M-09〜M-12 の具体内容追記 (PLAN-100 §6.3 Sprint 0 補完の carry)

更新しない事項:
- §0 line 36 より前の記述
- §12 M-01〜M-08 の既存記述
- §1〜§11 の本文

### Sprint .3: 検証

```bash
# plan_validator での全件 PASS 確認
python3 cli/lib/plan_validator.py docs/plans/PLAN-127-v2-l2-master-plan-adr-trace.md

# helix doctor での check_plan_adr_snapshot 全件確認
helix doctor check_plan_adr_snapshot --all

# L2-MASTER.md の編集範囲確認 (§0 のみに限定)
git diff docs/v2/L2-MASTER.md
```

---

## §4. 段階導入

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | trace map 抽出 (PLAN frontmatter grep + ADR frontmatter grep + 突合) | pmo-sonnet | trace 表 20+ 行が作成される |
| **Sprint .2** | L2-MASTER §0 range 拡張 (trace 表挿入 + M-09〜M-12 追記) | docs | L2-MASTER §0 に V5 以降 trace 一覧が追加される |
| **Sprint .3** | plan_validator PASS + helix doctor check_plan_adr_snapshot PASS | pmo-sonnet | 全件 PASS 確認済み |

---

## §5. デグレ禁止項目

1. L2-MASTER §0 の既存「PLAN-084 ↔ ADR-018/019」範例は削除しない (backward compat)
2. L2-MASTER §1〜§11 は編集しない
3. L2-MASTER §12 M-01〜M-08 の既存記述は編集しない (M-09〜M-12 追記のみ)
4. PLAN-100 本体 (status: complete) は編集しない
5. 既存 ADR-021〜033 の本文は編集しない (trace reference のみ追加)

---

## §6. DoD (Definition of Done)

1. Sprint .1: PLAN ↔ ADR trace 表が作成され、20+ 件の対応関係が記録されている
2. Sprint .2: `docs/v2/L2-MASTER.md` §0 に V5 framework 以降の trace 一覧 subsection が追加されている
3. Sprint .2: §12 に M-09〜M-12 の具体内容が追記されている
4. Sprint .3: `python3 cli/lib/plan_validator.py docs/plans/PLAN-127-*.md` が PASS
5. Sprint .3: `helix doctor check_plan_adr_snapshot --all` で新規 failure 増加なし
6. デグレ禁止 (§5) を git diff で確認

---

## §7. V-model 4 artifact trace

本 PLAN は設計 artifact (①) として機能する。

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-127-v2-l2-master-plan-adr-trace.md |
| ② 実装コード | N/A (doc 更新のみ) | — |
| ③ テスト設計 | 不要 (doc 更新 + helix doctor による機械検証) | — |
| ④ テストコード | 不要 | — |

**双方向 reference**:
- 本 PLAN → L2-MASTER.md: generates.artifact_path + §3 Sprint .2
- L2-MASTER.md → 本 PLAN: §0 更新時に「更新履歴: PLAN-127」を末尾に追記

---

## §8. 関連 PLAN / ADR

### 前段 PLAN (requires)
- PLAN-100: V2 全面見直し計画 (§6.3 L2-MASTER 更新計画が本 PLAN の起源)

### 関連 ADR
- なし (本 PLAN は L2 大局判断を含まないため ADR snapshot 不要)

### 関連 docs
- docs/v2/L2-MASTER.md: 本 PLAN の唯一の編集対象
- CLAUDE.md §PLAN ⊃ ADR レイヤー併存: trace 原則の根拠

---

## §9. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| trace map 抽出漏れ | 対応関係が incomplete なまま追記される | Sprint .1 で grep 両方向突合を必須化、片方向 miss を carry note に記録 |
| §0 range 以外の編集 | 意図しない §1〜§11 の変更 | Sprint .3 で git diff の編集範囲を §0 に限定確認 |
| M-09〜M-12 内容の陳腐化 | carry から時間経過で実態と乖離 | PLAN-100 §6.3 Sprint 0 補完内容 (commit 根拠あり) を verbatim 参照 |
