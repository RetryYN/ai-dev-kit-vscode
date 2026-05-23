---
plan_id: PLAN-131
title: "PLAN-131: ADR Decision Graph (FR-V5-22) 実装 — supersedes/influences/contradicts 有向グラフ可視化"
layer: L4
kind: impl
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-100-existing-retrofit-v2-revision.md   # from dependencies.parent
size: M
drive: be
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — cli/lib/adr_graph.py 新規実装 + helix-adr graph subcommand 実装"
  - role: dba
    slot_label: "DBA — ADR frontmatter schema 拡張 (supersedes/superseded_by/influences/contradicts 4 field) + migration"
  - role: qa
    slot_label: "QA — ADR-001〜044 bulk import + graph 整合性テスト設計・実装"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-100/PLAN-091 との依存整合・G4 review"
  - role: tl-advisor
    slot_label: "TL adversarial check — graph schema 設計・cycle detection アルゴリズム・ADR-046 凍結判定"
generates:
  - artifact_path: cli/lib/adr_graph.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_adr_graph.py
    artifact_type: test
  - artifact_path: docs/adr/ADR-046-adr-decision-graph-schema.md
    artifact_type: adr_snapshot
  - artifact_path: docs/plans/PLAN-131-adr-decision-graph.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-100
  requires:
    - PLAN-100
  blocks: []
related_plans:
  - PLAN-091-v5-framework-core
  - PLAN-093-drift-detect-progress-trace
  - PLAN-100-existing-retrofit-v2-revision
related_adr:
  - ADR-046-adr-decision-graph-schema
related_docs:
  - docs/v2/L1-REQUIREMENTS.md
  - docs/v2/L2-MASTER.md
---

# PLAN-131: ADR Decision Graph (FR-V5-22) 実装

> **kind**: impl (ADR graph framework 新規実装)
> **layer**: L4 (実装フェーズ)
> **drive**: be (Python CLI 実装中心)
> **L2 凍結**: ADR-046 (graph schema + relation type 設計、L2 大局判断)

---

## §0. 本 PLAN の位置付け

本 PLAN は L1-REQUIREMENTS **FR-V5-22 (ADR Decision Graph、P0)** の実装本体。
PLAN-100 §13 で FR-V5-22 採用が確定し、ADR 間の `supersedes` / `superseded_by` /
`influences` / `contradicts` 関係を有向グラフで可視化する framework を実装する。

PLAN-100 が parent PLAN であり、V5 framework Layer A (工程・ドキュメント運用ルール整備)
の一部として位置付けられる。

---

## §1. 目的

1. ADR frontmatter に 4 種の relation field を追加し、ADR 間の依存・影響・矛盾関係を機械可読にする
2. `helix adr graph` CLI で有向グラフを text / mermaid / graphviz 形式で出力する
3. 既存 ADR-001〜044 を bulk import し、graph 整合性 (cycle 検出 / orphan 検出) を確認する
4. graph を `helix doctor` の audit 対象に追加し、ADR 廃止漏れ / 矛盾 ADR の放置を防止する

---

## §2. 背景

### 2.1 FR-V5-22 の確立経緯

2026-05-22 の Phase 4 着手前リサーチ wave で、pmo-tech-docs が以下を調査・報告した:
- **MADR 2.1.2** (adr/madr): ADR の `status` field で `superseded by ADR-XXXX` を表現するが、
  machine-readable な relation graph は未対応。frontmatter に `supersedes:` list を追加する
  拡張パターンが OSS コミュニティで普及している (adr/madr#118 等の議論を確認)。
- **log4brains** (thomvaill/log4brains): `AdrRelation { from, relation, to }` の typed domain
  model でリレーションを管理。`relation` string は `supersedes` / `amended by` 等の自然語。
  graph 可視化は独自 React UI で実装。
- **Event Sourcing upcasting**: ADR 自体は immutable (log4brains README の設計哲学) だが、
  新 ADR が旧 ADR を supersede することで schema evolution を表現する。
  この upcasting pattern は HELIX の ADR 廃止 / 段階遷移管理に直接適用できる。
- **pdm-innovation-manager** 統合判断で FR-V5-22 を P0 採用確定 (PLAN-100 §13、
  docs/v2/phase4-readiness-report-2026-05-22.md 参照)。

### 2.2 業界 standard 参照 (WebSearch 3 query、PLAN-087 ガードレール準拠)

| # | Query | Source | 本 PLAN への引用 |
|---|---|---|---|
| Q1 | "MADR 2.1.2 ADR decision graph supersedes 2026" | github.com/adr/madr — `adr-template.md` status field: `"superseded by ADR-0123"` | §3 frontmatter schema 設計の status 表現形式 |
| Q2 | "Event Sourcing upcasting ADR evolution supersedes" | github.com/thomvaill/log4brains — `AdrRelation.ts`: `{ from, relation, to }` typed ValueObject | §3 relation type 設計 + §5.1 Python 実装の data model |
| Q3 | "Architecture Decision Record graphviz mermaid visualization graph" | github.com/thomvaill/log4brains — README: ADR は immutable、status のみ変化可能 | §5.2 CLI 出力形式設計 (mermaid 優先) + §4 不変性保証設計 |

---

## §3. 設計方針 (L2 凍結 → ADR-046)

### 3.1 ADR frontmatter 拡張 schema

```yaml
# ADR frontmatter 拡張 (4 relation field)
supersedes:
  - ADR-012-old-decision
superseded_by: ADR-045-new-decision   # この ADR が廃止された場合
influences:
  - ADR-033-related-hook-design
contradicts:
  - ADR-007-conflicting-approach
```

**設計選択の根拠 (ADR-046 で凍結)**:
- `superseded_by` は単数 (1 ADR は 1 ADR にしか置き換えられない) — MADR template に準拠
- `supersedes` は list (1 ADR が複数の旧 ADR を一括置換できる) — log4brains 実装に準拠
- `influences` / `contradicts` は list (参照・影響関係は多対多) — 独自拡張
- relation type は 4 種に固定 (自由 string は graph 整合性検証を困難にする)

### 3.2 graph 構築ルール

- Directed Acyclic Graph (DAG) を前提とする (cycle は helix doctor で fail-close)
- `supersedes` / `superseded_by` は bidirectional edge として双方向に登録
- `influences` / `contradicts` は directed edge (from → to)
- node は ADR ID、edge label は relation type

### 3.3 出力形式

| format | 用途 | 実装 |
|---|---|---|
| text | terminal 表示、human-readable summary | `__str__` |
| mermaid | docs 埋め込み、GitHub rendering | `to_mermaid()` |
| graphviz dot | 大規模グラフ、PDF 出力 | `to_dot()` |

---

## §4. DoD (Definition of Done)

- [ ] ADR frontmatter に 4 relation field を追加する schema 変更ガイドを docs に記載
- [ ] `cli/lib/adr_graph.py` が ADR frontmatter を parse して directed graph を構築する
- [ ] `helix adr graph` が text / mermaid / graphviz の 3 形式で出力する
- [ ] cycle 検出 (DFS + recStack) で循環 ADR 依存を fail-close 報告する
- [ ] `helix doctor` に `check_adr_graph_cycles` を追加する
- [ ] `cli/lib/tests/test_adr_graph.py` で 5 test scenario 以上を通過する
- [ ] 既存 ADR-001〜044 に 少なくとも supersedes / superseded_by が判明しているものを retrofit
- [ ] ADR-046 を L2 大局判断 snapshot として起票 (本 PLAN 起票時点では placeholder)
- [ ] `python3 -m py_compile cli/lib/adr_graph.py` が PASS
- [ ] `python3 -m pytest cli/lib/tests/test_adr_graph.py -v` が全件 PASS

---

## §5. 実装計画

### Sprint .1 — schema 設計 + Python module skeleton

**担当**: SE + DBA

**作業**:
1. ADR frontmatter schema 設計を ADR-046 として起票 (L2 大局判断凍結)
2. `cli/lib/adr_graph.py` skeleton 実装:
   - `AdrNode` dataclass: `adr_id`, `title`, `status`, `supersedes`, `superseded_by`, `influences`, `contradicts`
   - `AdrGraph` class: `add_node()`, `add_edges_from_node()`, `build_from_directory(path)`, `detect_cycles()`
   - `load_adr_frontmatter(path)` — yaml.safe_load + 4 relation field 抽出
3. `detect_cycles()` — DFS + recStack algorithm (PLAN-092 unit-test-design §7 で確立した Kahn's algorithm より DFS を選択、cycle path の trace に優れる)
4. `to_mermaid()` / `to_dot()` / `__str__()` 出力メソッド実装

**受入条件**:
- `AdrGraph.build_from_directory(docs/adr/)` が 44 ADR を parse して graph を構築する
- `detect_cycles()` が cycle なし (空 list) を返す
- `py_compile` PASS

### Sprint .2 — CLI 実装 + helix-adr subcommand

**担当**: SE

**作業**:
1. `cli/helix-adr` bash subcommand 新規:
   - `helix adr graph [--format text|mermaid|dot] [--adr-dir path]`
   - `helix adr graph --check-cycles` (cycle 検出専用、exit 1 on cycle)
2. `cli/helix` top-level router に `adr` を登録
3. `helix doctor` に `check_adr_graph_cycles` hook 追加:
   - `adr_graph.detect_cycles()` が 1 件以上 → `fail` (P0)
   - `superseded_by` が設定されているのに status が `Accepted` のまま → `warn` (P2)
4. docs 更新: `docs/commands/index.md` に `helix adr graph` 追記

**受入条件**:
- `helix adr graph --format mermaid` が全 ADR の mermaid diagram を stdout 出力
- `helix adr graph --check-cycles` が exit 0 で終了 (cycle なし確認)
- `helix doctor` に `check_adr_graph_cycles` が追加され、pass/fail/warn を返す

### Sprint .3 — 既存 ADR retrofit + 全体検証

**担当**: QA + SE

**作業**:
1. ADR-001〜044 をスキャンし、判明している `supersedes` / `superseded_by` 関係を frontmatter に追加:
   - `superseded_by` が既知のもの: ADR-007 (PRAGMA → schema_version、ADR-026 で置換)、
     ADR-012 (roles config v1 → ADR-014 で置換) 等
   - `supersedes` を記述する新 ADR にも双方向 link を追加
2. `cli/lib/tests/test_adr_graph.py` 実装:
   - T1: empty graph build (no ADR files)
   - T2: single ADR no relations
   - T3: supersedes chain (A supersedes B, B supersedes C)
   - T4: cycle detection (A influences B, B contradicts A) → cycle 検出
   - T5: bulk load ADR-001〜044 → 44 node、cycle なし、mermaid 出力形式確認
3. `helix doctor` 全体実行で check_adr_graph_cycles が pass を確認

**受入条件**:
- `pytest cli/lib/tests/test_adr_graph.py -v` 全件 PASS
- `helix doctor` が `check_adr_graph_cycles: pass` を返す
- `helix adr graph` が 44 ADR の mermaid を出力 (visual 確認)

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| 既存 ADR に frontmatter がないものが存在 | Sprint .3 の bulk load が失敗 | load_adr_frontmatter に try/except + skip log を実装、PLAN-100 Phase 4 で retrofit 済の 31 ADR は frontmatter 確認済 |
| ADR 間の関係が実際には cycle を形成している | detect_cycles が fail-close 発動 | Sprint .1 で cycle 検出を先行実装し、retrofit 前に現状の graph 状態を確認してから追加する |
| helix doctor への hook 追加が既存 check に干渉 | helix doctor 全体 fail | Sprint .2 で hook を最後に追加、helix doctor 単体実行で影響確認後にコミット |
| mermaid 出力が大規模 ADR で見づらい | 実用性低下 | `--filter` / `--depth` オプションで subgraph 抽出 (Sprint .2 optional) |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
