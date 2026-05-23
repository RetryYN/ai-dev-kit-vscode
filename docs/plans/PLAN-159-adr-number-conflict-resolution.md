---
plan_id: PLAN-159
title: "PLAN-159: ADR-040〜053 番号衝突解消 — 本 session 全 PLAN の related_adr 一意化 batch fix"
layer: cross
kind: retrofit
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: S
drive: be
created: 2026-05-23
owner: PMO
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 全 PLAN frontmatter related_adr grep + 重複検出 + 再割当案作成"
  - role: docs
    slot_label: "Docs — 各 PLAN.md の related_adr フィールドを再割当番号に書き換え"
generates:
  - artifact_path: docs/plans/PLAN-102-through-158-frontmatter-related-adr
    artifact_type: doc_update
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-127-v2-l2-master-plan-adr-trace
related_docs:
  - docs/plans/
  - helix/HELIX_CORE.md
---

# PLAN-159: ADR-040〜053 番号衝突解消 — 本 session 全 PLAN の related_adr 一意化 batch fix

> **kind**: retrofit (frontmatter の related_adr 番号を一意に再割当するだけ。ADR 本文起票は各 PLAN の responsibility)
> **layer**: cross (PLAN-102〜158 にまたがる横断変更)
> **drive**: be (CLI / framework doc 管理)
> **本 PLAN の役割**: 本 session で 30+ PLAN を起票した際、複数 PLAN が同一 ADR 候補番号を重複予約しているケースを batch で解消し、1 PLAN = 1 ADR の reciprocal 整合を確立する。

---

## §0. 本 PLAN の位置付け

本 session (2026-05-23) で PLAN-102〜158 を起票した際、各 PLAN frontmatter の `related_adr` に ADR snapshot 候補番号を記載した。しかし複数 PLAN が同一番号 (例: ADR-041 を PLAN-114 と PLAN-139 が同時予約) を記載しているケースが発生している。

このまま ADR 本文起票を進めると:
- ADR-041 のファイルが「どの PLAN の凍結か」不明になる
- `helix doctor check_plan_adr_snapshot` で「related_adr あり ADR ファイル不在」が多数 WARN
- L2-MASTER §0 の trace 表更新 (PLAN-127) で誤対応関係が記録される

本 PLAN で batch fix を先行させ、PLAN-127 の trace 抽出が正確に動く前提を整える。

---

## §1. 目的

1. `docs/plans/PLAN-102-*.md` から `docs/plans/PLAN-158-*.md` の全 frontmatter `related_adr` を grep し、重複番号を検出する (Sprint .1)
2. 各 PLAN に唯一の ADR 番号を ADR-040 から順に再割当する (Sprint .2)
3. 各 PLAN.md の `related_adr` フィールドを再割当番号に書き換え、plan_validator clean を確認する (Sprint .3)

---

## §2. 背景

### 2.1 重複発生の構造的原因

本 session では pmo-sonnet 複数スレッドで PLAN を並列起票した。各スレッドは「現時点での最大 ADR 番号 + 1」を独立に採番するため、同一番号が複数 PLAN に割り当てられる競合が必然的に起きた。

これは並列起票の副作用であり、HELIX の並列推奨方針 (CLAUDE.md §並列実行ルール) に従った結果として生じた構造的課題である。

### 2.2 影響範囲

| 影響 | 詳細 |
|---|---|
| ADR 本文起票時の混乱 | 同一番号を複数 PLAN が参照しているため、どの PLAN の凍結判断を文書化すべきか不明 |
| helix doctor WARN | related_adr で参照した ADR ファイルが不在の場合 WARN 増加 |
| PLAN-127 trace 精度 | trace map 抽出で誤対応関係を拾うリスク |

### 2.3 WebSearch skip 根拠

本 PLAN は frontmatter フィールド値の重複除去という機械的 retrofit であり、新 framework 採用や L2 大局判断を含まない。PLAN-087 ガードレール対象外。

---

## §3. 実装方針

### Sprint .1: 重複検出

実行手順:

```bash
# 全 PLAN の related_adr フィールドを抽出 (yaml frontmatter)
grep -h "related_adr" docs/plans/PLAN-1[0-5][0-9]-*.md \
  docs/plans/PLAN-10[2-9]-*.md 2>/dev/null | sort | uniq -d
```

ただし frontmatter が `related_adr: []` (空リスト) の場合は重複対象外。
重複が確認されたら Sprint .2 へ進む。重複なし確認でも Sprint .2 (一意採番の確認) は実施する。

出力形式 (Sprint .1 成果物):

```
ADR-041: PLAN-114, PLAN-139  ← 重複
ADR-043: PLAN-122, PLAN-131  ← 重複
...
```

### Sprint .2: 再割当案作成

再割当ルール:
1. ADR-040 から番号順に、L2 大局判断を含む PLAN へ 1 件ずつ割当
2. L2 大局判断なし (kind=retrofit / refactor / add-impl 等) の PLAN は `related_adr: []` のまま維持
3. 割当順は PLAN 番号昇順 (PLAN-102 → PLAN-158)

再割当表の形式:

| PLAN | 旧 related_adr | 新 related_adr | L2 判断内容 (1 行) |
|---|---|---|---|
| PLAN-NNN | ADR-041 | ADR-040 | … |

### Sprint .3: 一括書き換え + 検証

```bash
# 各 PLAN.md の related_adr を sed で書き換え (Sprint .2 の対応表を元に)
# 書き換え後に plan_validator を全件実行
for f in docs/plans/PLAN-1[0-5][0-9]-*.md docs/plans/PLAN-10[2-9]-*.md; do
  python3 cli/lib/plan_validator.py "$f" 2>&1 | grep -v "^$"
done

# WARN 0 件確認
python3 cli/lib/plan_validator.py docs/plans/PLAN-159-adr-number-conflict-resolution.md
```

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | related_adr 全件 grep + 重複検出レポート作成 | pmo-sonnet | 重複 PLAN リスト確定 |
| **Sprint .2** | ADR-040〜 再割当表作成 (1 PLAN = 1 ADR、昇順) | pmo-sonnet | 再割当表で全 PLAN に唯一番号が割当済 |
| **Sprint .3** | 各 PLAN.md 書き換え + plan_validator 全件 PASS | docs | 全対象 PLAN で WARN 0 件 |

---

## §5. デグレ禁止項目

1. `related_adr: []` の PLAN に番号を追加しない (既存 ADR 不在 PLAN への誤割当防止)
2. ADR-001〜039 は変更しない (既存 ADR との衝突回避)
3. PLAN frontmatter の `related_adr` 以外のフィールドは書き換えない
4. ADR ファイル本文は本 PLAN の scope 外 (起票は各 PLAN 実施時に行う)

---

## §6. DoD (Definition of Done)

1. Sprint .1: 重複 ADR 番号リストが作成されている
2. Sprint .2: 全 L2 大局判断 PLAN に ADR-040 以降の一意番号が割当済
3. Sprint .3: 対象 PLAN 全件で `python3 cli/lib/plan_validator.py` WARN 0 件
4. Sprint .3: `python3 cli/lib/plan_validator.py docs/plans/PLAN-159-*.md` PASS
5. デグレ禁止 (§5) を git diff で確認

---

## §7. V-model 4 artifact trace

本 PLAN は設計 artifact (①) として機能する。実装コード変更なし、テスト設計不要。

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-159-adr-number-conflict-resolution.md |
| ② 実装コード | N/A (frontmatter 書き換えのみ) | — |
| ③ テスト設計 | 不要 (plan_validator 機械検証で代替) | — |
| ④ テストコード | 不要 | — |

**双方向 reference**:
- 本 PLAN → 対象 PLAN 群: generates.artifact_path + §3 Sprint .3
- 対象 PLAN 群 → 本 PLAN: 各 PLAN の related_plans に PLAN-159 を追記 (Sprint .3 実施時)

---

## §8. 関連 PLAN / ADR

### 前段 (requires)
- なし (本 PLAN は独立実施可能)

### 後段 (blocks)
- PLAN-127: trace map 抽出の精度向上に寄与 (blocks 関係ではなく recommended 先行実施)

### 関連 ADR
- なし (本 PLAN は L2 大局判断を含まないため ADR snapshot 不要)

---

## §9. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| grep 抽出漏れ (YAML multi-line 形式) | 重複を見落とす | Sprint .1 で Python yaml.safe_load を使った補完抽出も実施 |
| 再割当後に ADR 番号が既存 ADR-034〜039 と衝突 | 既存 ADR を上書きするリスク | Sprint .2 着手前に `ls docs/adr/ADR-03*.md` で空き番号を確認 |
| sed 書き換えで related_adr 以外を破壊 | frontmatter 破損 | 書き換え前に git stash 等で snapshot を保持 |
