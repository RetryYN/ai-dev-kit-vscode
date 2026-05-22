---
plan_id: PLAN-192
title: "PLAN-192: ADR Decision Graph visualization (graphviz / mermaid output)"
layer: L4
kind: impl
status: draft
size: S
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — AdrGraph.to_mermaid / to_dot 実装 + helix adr graph --format 拡張"
  - role: docs
    slot_label: "Docs — README / mkdocs site への mermaid embed 手順起草"
  - role: qa
    slot_label: "QA — mermaid / graphviz 出力形式テスト設計・実装"
  - role: pmo-sonnet
    slot_label: "PMO — 設計整合確認・PLAN-131 依存整合・G4 review"
generates:
  - artifact_path: cli/lib/adr_graph.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_adr_graph_viz.py
    artifact_type: test
  - artifact_path: docs/adr/index.md
    artifact_type: doc_update
  - artifact_path: docs/v2/L4-test-design/PLAN-192-test-design.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-131
  requires:
    - PLAN-131
  blocks: []
related_plans:
  - PLAN-131-adr-decision-graph
  - PLAN-160-helix-mkdocs-site
related_adr:
  - ADR-046-adr-decision-graph-schema
related_docs:
  - docs/adr/index.md
  - docs/commands/index.md
---

# PLAN-192: ADR Decision Graph visualization

> **kind**: impl | **layer**: L4 | **drive**: be | **parent**: PLAN-131

---

## §0. 位置付け

PLAN-131 が ADR 間の有向グラフ (supersedes / influences / contradicts) を Python で構築する。
本 PLAN はその可視化出力層として:

- `--format mermaid`: GitHub Markdown / mkdocs に直接 embed 可能な mermaid 図を生成
- `--format graphviz`: .dot ファイルを生成、`dot -Tpng` で PNG 出力
- edge type ごとに色分け (supersedes=赤、influences=青、contradicts=橙) を適用

**L2 大局判断**: PLAN-131 の ADR-046 を継承する実装拡張であり、新たな ADR snapshot は不要。

---

## §1. 目的

1. `helix adr graph --format mermaid` が GitHub README / mkdocs site に embed 可能な
   mermaid diagram を stdout に出力する
2. `helix adr graph --format graphviz` が .dot ファイルを生成する
3. edge type ごとの色分けで ADR 廃止 / 影響 / 矛盾を視覚的に識別できる

---

## §2. 背景

### 2.1 PLAN-131 との分担

| 機能 | PLAN-131 | 本 PLAN |
|---|---|---|
| directed graph 構築 | 実装済 | 依存 |
| cycle 検出 / helix doctor | 実装済 | 依存 |
| mermaid 出力 (skeleton) | skeleton のみ | **本番実装** |
| graphviz .dot 出力 | 未実装 | **新規実装** |
| edge color 設計 | 未実装 | **新規実装** |
| README / mkdocs embed 手順 | 未実装 | **docs 整備** |

### 2.2 WebSearch 3 query (Sprint .1 で実施、PLAN-087 ガードレール準拠)

| # | Query |
|---|---|
| Q1 | `mermaid graph edge color styling 2025 2026 best practices` |
| Q2 | `graphviz dot ADR architecture decision record visualization 2026` |
| Q3 | `mkdocs mermaid diagram embed GitHub README flowchart styling 2026` |

---

## §3. 設計方針

### 3.1 mermaid 出力形式

```
graph TD
  %% supersedes (廃止): 赤実線
  ADR-046 -->|supersedes| ADR-012
  linkStyle 0 stroke:#e53935,stroke-width:2px

  %% influences (影響): 青破線
  ADR-046 -.->|influences| ADR-033
  linkStyle 1 stroke:#1e88e5,stroke-width:1.5px

  %% superseded ノード: グレー
  ADR-012:::superseded
  classDef superseded fill:#9e9e9e,color:#fff
```

### 3.2 graphviz .dot 出力形式

```
digraph adr_graph {
  rankdir=LR; node [shape=box, style=filled, fillcolor=white];
  "ADR-046" -> "ADR-012" [label="supersedes", color="#e53935", penwidth=2.0];
  "ADR-046" -> "ADR-033" [label="influences", color="#1e88e5", style=dashed];
  "ADR-012" [fillcolor="#9e9e9e", fontcolor=white];
}
```

### 3.3 CLI 拡張 (`helix adr graph` オプション追加)

| オプション | 説明 |
|---|---|
| `--format mermaid` | mermaid flowchart を stdout に出力 |
| `--format graphviz` | graphviz .dot を stdout または `--out` 先に出力 |
| `--out file` | 出力先ファイル (省略時 stdout) |
| `--filter ADR-ID,...` | 指定 ADR と 1 hop neighbors の subgraph のみ出力 |

---

## §4. 実装計画

| Sprint | 内容 | 担当 | 受入条件 |
|---|---|---|---|
| **.1** | WebSearch 3 query + to_mermaid/to_dot API 設計確定 | pmo-sonnet | WebSearch 証拠記録済、メソッドシグネチャ確定 |
| **.2** | AdrGraph.to_mermaid / to_dot / _edge_color 実装 | SE | py_compile PASS、§3.1/3.2 形式で出力 |
| **.3** | CLI `--format/--out/--filter` 拡張 + docs embed 手順 | SE + docs | `helix adr graph --format mermaid` が stdout 出力 |
| **.4** | `test_adr_graph_viz.py` 実装 + QA | QA | T1〜T5 全件 PASS / `helix test` 回帰 PASS |

### Sprint .2 — 追加メソッド

```python
# cli/lib/adr_graph.py に追加
def to_mermaid(self, filter_ids: list[str] | None = None) -> str: ...
def to_dot(self, filter_ids: list[str] | None = None) -> str: ...
def _edge_color(self, relation: str) -> str: ...
```

### Sprint .4 — テスト 5 scenario

T1: to_mermaid に `graph TD` / `linkStyle` を含む。T2: to_dot に `digraph` / `rankdir` を含む。
T3: edge color mapping (supersedes → #e53935)。T4: `--filter` で 1 hop subgraph のみ。
T5: superseded ノードに classDef / fillcolor が適用される。

---

## §5. DoD

- [ ] `python3 -m py_compile cli/lib/adr_graph.py` PASS
- [ ] `pytest cli/lib/tests/test_adr_graph_viz.py -v` 全件 PASS (5 test 以上)
- [ ] PLAN-131 の `test_adr_graph.py` に回帰なし
- [ ] `helix adr graph --format mermaid` / `--format graphviz` が正常出力する
- [ ] `docs/adr/index.md` に mermaid embed 手順が記載されている
- [ ] WebSearch 3 query 証拠が §2.2 に記録されている
- [ ] `python3 cli/lib/plan_validator.py docs/plans/PLAN-192-*.md` PASS

---

## §6. V-model 4 artifact trace

| Artifact | ファイル |
|---|---|
| ① 設計 | docs/plans/PLAN-192-*.md |
| ② 実装コード | cli/lib/adr_graph.py (to_mermaid / to_dot 拡張) |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-192-test-design.md (Sprint .1) |
| ④ テストコード | cli/lib/tests/test_adr_graph_viz.py |

双方向 reference: adr_graph.py docstring に `# PLAN-192` 明記。テスト設計 frontmatter に `related_plans: [PLAN-192]` 明記。

---

## §7. リスク

| リスク | 緩和策 |
|---|---|
| PLAN-131 未完了時の着手 | AdrGraph skeleton 完了を Entry 条件とする |
| mermaid linkStyle 番号がエッジ順序に依存 | Sprint .1 WebSearch で確認。代替は classDef のみで色分け |
| graphviz dot が CI 環境に未インストール | .dot 生成は依存ゼロ。PNG 変換は利用者環境に委ねる |
| 44+ ADR で mermaid が縦に巨大 | `--filter` subgraph 抽出で対応 |

---

## §8. 完了記録

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
