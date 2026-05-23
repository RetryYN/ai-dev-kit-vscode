---
plan_id: PLAN-125
title: "PLAN-125: V2 CONCEPT.md V5 framework retrofit 完遂"
layer: cross
kind: retrofit
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
size: M
drive: be
created: 2026-05-23
owner: pmo-sonnet
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — drift 検出・監査・双方向 trace 確認"
  - role: docs
    slot_label: "Docs #1 — CONCEPT.md §11 PLAN 一覧拡張実装"
  - role: docs
    slot_label: "Docs #2 — CONCEPT.md §12 既知矛盾更新実装"
generates:
  - artifact_path: docs/v2/CONCEPT.md
    artifact_type: doc_update
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-100
  blocks: []
related_plans:
  - PLAN-100-existing-retrofit-v2-revision
  - PLAN-MM-001-v5-framework-master-plan
related_docs:
  - docs/v2/CONCEPT.md
  - docs/v2/V5-plan-outlines.md
  - docs/v2/L2-MASTER.md
---

# PLAN-125: V2 CONCEPT.md V5 framework retrofit 完遂

> **kind**: retrofit (既存 doc を V5 framework 新規約に合わせる更新)
> **layer**: cross (CONCEPT.md は V2 全体の頂上設計 doc であり横断影響)
> **drive**: be (CLI / framework ドキュメント中心)
> **本 PLAN の役割**: PLAN-100 で着手した V2 全面見直しのうち、CONCEPT.md への最新 PLAN 反映を完結させる。

---

## §0. 本 PLAN の位置付け

本 PLAN は **PLAN-100 §6 V2 doc 全面見直しの CONCEPT.md 担当**。

PLAN-100 完遂後に起票された PLAN-101〜122 に対して、CONCEPT.md §11 (PLAN 一覧) および §12 (既知矛盾) の反映が未了のまま drift が累積している。本 PLAN はこの drift を解消し、CONCEPT.md が V2 全体の正本として機能する状態を回復する。

---

## §1. 目的

1. PLAN-101〜122 (本 session 起票分含む) を CONCEPT.md §11 PLAN 一覧に反映する
2. CONCEPT.md §12 既知矛盾に本 session で判明した新規矛盾を追記する
3. CONCEPT.md ↔ PLAN 一覧の双方向 trace を確立し、helix doctor で lint 可能な状態にする

---

## §2. 背景

### 2.1 CONCEPT.md の現状

`docs/v2/CONCEPT.md` (409 行) は §10 に V5 framework 19 要素統合済だが、§11 PLAN 一覧と §12 既知矛盾は以下の状態にある:

| セクション | 現状 | 問題 |
|---|---|---|
| §11 PLAN 一覧 | PLAN-091〜100 + PLAN-MM-001 のみ記載 | PLAN-101〜122 が未反映 |
| §12 既知矛盾 | M-01〜M-04 のみ (PLAN-069 resolved pattern) | 本 session 判明の矛盾 (datetime deprecation / helix-db.lock isolation 不足 / gate flake 1 件) が未記録 |

### 2.2 drift 発生経緯

PLAN-100 が 2026-05-22 に complete 遷移した後、Phase 4 carry (Wave 2〜Wave 3) で PLAN-101〜122 が連続起票された。CONCEPT.md の §11 は PLAN-100 の完遂時点で freeze されたため、22 件の PLAN が一覧から欠落した状態となっている。

### 2.3 影響範囲

- `helix doctor check_concept_plan_coverage` (予定) での false positive
- CONCEPT.md を参照する PM / TL の PLAN 全体像把握が不完全になる
- PLAN-MM-001 の「CONCEPT を正本」方針との矛盾

---

## §3. 業界 standard 参照 (WebSearch skip 理由)

本 PLAN は PLAN-100 内拡張であり、既存 PLAN-100 §3 で引用済みの業界 standard (Nygard ADR / Fowler Strangler Fig / AWS ADR Best Practices) が直接適用される。PLAN-087 ガードレールの「既存 PLAN 拡張時は skip OK」条件に該当。

skip 根拠: 本 PLAN の技術判断範囲はすべて PLAN-100 の ADR snapshot 済み決定 (ADR-021〜024) の範囲内であり、新規 L2 大局判断を含まない。

---

## §4. スコープ

### In scope
- CONCEPT.md §11 PLAN 一覧: PLAN-101〜122 の追記
- CONCEPT.md §12 既知矛盾: 本 session 判明矛盾の追記
- CONCEPT.md ↔ 各 PLAN の双方向 reference 確立 (CONCEPT.md 側の記載)

### Out of scope
- CONCEPT.md §1〜§10 の内容変更 (V5 framework 19 要素は既に整合済)
- L1-REQUIREMENTS / L2-MASTER の変更 (PLAN-126 担当)
- 各 PLAN の `related_docs` への CONCEPT.md 追記 (スケールアウト候補、後続 carry)

---

## §5. 実装計画

### Sprint .1: drift 検出 (pmo-sonnet 担当)

- `docs/plans/PLAN-10*.md` `docs/plans/PLAN-11*.md` `docs/plans/PLAN-12*.md` の frontmatter `title` / `status` を一覧化
- CONCEPT.md §11 と比較し、未反映 PLAN ID を列挙
- §12 既知矛盾として追記すべき内容を MEMORY.md / session handover から抽出
- **成果物**: drift リスト (PLAN ID / status / title の未反映件数)

受入条件:
- 未反映 PLAN を漏れなく (N 件) 特定できる
- §12 追記候補 3 件以上を evidence 付きで抽出できる

### Sprint .2: 反映実装 (Codex docs 委譲 × 2 並列)

**Docs #1 — §11 PLAN 一覧拡張**:
- Sprint .1 で特定した未反映 PLAN を §11 に追記
- 各 PLAN の `plan_id` / `title` / `status` / `layer` / `kind` を table 形式で一覧化
- 既存 PLAN-091〜100 行との一貫したフォーマットを維持

**Docs #2 — §12 既知矛盾更新**:
- Sprint .1 で抽出した新規矛盾を M-05 以降として追記
- 各矛盾に「発覚 session」「関連 PLAN」「解消策 (または pending)」を記載
- PLAN-069 resolved pattern (M-01〜M-04) の記法を踏襲

受入条件:
- §11 に PLAN-101〜122 がすべて列挙されている
- §12 に M-05 以降として新規矛盾が追記されている
- plan_validator が CONCEPT.md の参照 PLAN ID に対して孤立 warning を出さない

### Sprint .3: 検証 (pmo-sonnet 担当)

- `helix doctor` 実行で CONCEPT.md 関連 check が pass することを確認
- PLAN-101〜122 の `related_docs` に CONCEPT.md が含まれるか最小 spot check (5 件)
- §11 一覧 と `ls docs/plans/PLAN-1*.md` のカバレッジ一致確認

受入条件:
- helix doctor pass ≥ 20 (warn は許容、fail = 0)
- §11 一覧 ↔ `ls docs/plans/PLAN-1*.md` で欠落 0 件

---

## §6. 依存・前提

| 依存 | 理由 |
|---|---|
| PLAN-100 complete | §11 拡張の起点 (PLAN-091〜100 の記述フォーマット参照) |
| PLAN-102〜122 frontmatter 確定 | Sprint .1 で title / status を読み取る対象 |

---

## §7. リスク

| リスク | P | I | 緩和策 |
|---|---|---|---|
| Sprint .2 中に新 PLAN (PLAN-123 以降) が追加起票される | M | L | Sprint .3 で `ls` 再実行し差分があれば §11 に追記 |
| §12 矛盾追記が既存 M-01〜M-04 の resolved 状態を誤変更する | L | M | Docs #2 は M-05 以降のみ追記、既存行は read-only で扱う |
| CONCEPT.md 編集が §10 V5 framework 記述と干渉する | L | H | Sprint .2 前に §10 末尾行番号を確認し、§11 の insert 位置を明示する |

---

## §8. DoD (完了条件)

- [ ] CONCEPT.md §11 に PLAN-101〜122 (+ 本 session 起票分) が全件追記されている
- [ ] CONCEPT.md §12 に M-05 以降として新規矛盾 ≥ 3 件が追記されている
- [ ] helix doctor fail = 0
- [ ] plan_validator: `python3 cli/lib/plan_validator.py --file docs/plans/PLAN-125-v2-concept-v5-retrofit.md` が warnings のみ (errors = 0)

---

## §9. 関連資産

- `docs/v2/CONCEPT.md` — 編集対象 (§11 / §12 のみ)
- `docs/v2/V5-plan-outlines.md` — §11 PLAN 一覧の参照資産
- `docs/plans/PLAN-100-existing-retrofit-v2-revision.md` — parent retrofit PLAN
- `docs/plans/PLAN-MM-001-v5-framework-master-plan.md` — 最上位 master plan
