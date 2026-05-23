---
plan_id: PLAN-149
title: "PLAN-149: ADR Decision Graph topological sort + 循環検出 (PLAN-131 補完)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-131-adr-decision-graph.md   # from dependencies.parent
size: S
created: 2026-05-23
revised: "2026-05-23 (初版起票)"
owner: PM
phases: L4
gates: G4
agent_slots:
  - role: se
    slot_label: "SE — cli/lib/adr_graph.py に topological_sort() + detect_cycles() 強化実装"
  - role: qa
    slot_label: "QA — topological sort + cycle 検出のテスト設計・実装 (T1〜T5)"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-131 との設計整合確認・DoD チェック・G4 review"
generates:
  - artifact_path: cli/lib/adr_graph.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_adr_graph_topo.py
    artifact_type: test
  - artifact_path: docs/plans/PLAN-149-adr-graph-topological-sort.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-131
  requires:
    - PLAN-131
  blocks: []
related_plans:
  - PLAN-131-adr-decision-graph
  - PLAN-091-v5-framework-core
related_adr:
  - ADR-062-adr-decision-graph-schema-extended
  - ADR-052-adr-graph-topological-sort
related_docs:
  - docs/adr/ADR-046-adr-decision-graph-schema.md
  - cli/lib/adr_graph.py
---

# PLAN-149: ADR Decision Graph topological sort + 循環検出 (PLAN-131 補完)

> **kind**: impl (PLAN-131 の機能補完)
> **layer**: L4
> **drive**: be (Python 拡張中心)
> **L2 凍結**: ADR-052 (topological sort 設計選択 snapshot)

---

## §0. 本 PLAN の位置付け

PLAN-131 (ADR Decision Graph) で directed graph の構築・出力・基本 cycle 検出が完成した。
本 PLAN は **topological sort (時系列 + supersedes 順序整列) + 循環検出の精度強化 + 不整合
検証** を追加し、`helix doctor check_adr_decision_graph_cycles` を fail-close 化する
補完 impl PLAN である。

PLAN-131 が parent であり、`cli/lib/adr_graph.py` の既存実装を拡張する。

---

## §1. 目的

1. `AdrGraph.topological_sort()` を実装し、ADR の「時系列順 + supersedes 依存順」を
   決定論的に表示できるようにする
2. `detect_cycles()` を DFS + recStack から networkx `find_cycle` 統合版に強化し、
   cycle path を詳細出力する
3. 不整合検証 (`check_consistency()`) を追加し、`superseded_by` 設定済みなのに
   status=Accepted の ADR を warn として検出する
4. `helix doctor check_adr_decision_graph_cycles` を advisory から fail-close (P0) に昇格させる

---

## §2. 背景

### 2.1 PLAN-131 完遂後の残課題

PLAN-131 Sprint .2 DoD では `helix doctor` への `check_adr_graph_cycles` 追加を
"warn (P2)" として定義した。しかし ADR の循環依存 (A supersedes B → B supersedes A)
は設計矛盾であり、warn ではなく fail-close が適切という判断を本 PLAN で確定させる。

また topological_sort は PLAN-131 の設計方針 §3.2 に「DAG を前提」と記載されているが、
具体的な sort アルゴリズムの実装は明示されていない。本 PLAN で networkx の
`topological_sort` を採用し、出力を安定させる。

### 2.2 WebSearch skip 理由 (PLAN-087 ガードレール遵守)

PLAN-131 §2.2 の WebSearch 3 query で networkx・DFS・mermaid の業界 standard を
調査済みである (Q1〜Q3)。本 PLAN は PLAN-131 の実装補完であり、新規の外部ライブラリや
設計方針の採用はない。WebSearch **skip**。

---

## §3. 設計方針 (L2 凍結 → ADR-052)

### 3.1 topological_sort の設計選択

```python
import networkx as nx

def topological_sort(self) -> list[str]:
    """supersedes 辺を反転した DAG を Kahn's algorithm で整列する。
    古い ADR (superseded) が先、新しい ADR (supersedes) が後になる順序を返す。
    Returns: ADR ID の list (時系列 + supersedes 依存順)
    Raises: networkx.NetworkXUnfeasible (cycle が存在する場合)
    """
    # supersedes 辺は「新 → 旧」方向 (A supersedes B は A→B edge)
    # topological sort は「旧が先」なので辺方向そのままで nx.topological_sort を使う
    try:
        return list(nx.topological_sort(self._graph))
    except nx.NetworkXUnfeasible as e:
        raise CycleDetectedError(str(e)) from e
```

**設計選択の根拠 (ADR-052 で凍結)**:
- networkx `topological_sort` は Kahn's algorithm の Python 実装であり、
  PLAN-131 §5.1 で既に `import networkx as nx` を前提としている
- 辺方向: `supersedes` は「新 ADR → 旧 ADR」。`topological_sort` で旧 ADR が先頭、
  新 ADR が末尾となり「歴史順」になる

### 3.2 detect_cycles 強化

```python
def detect_cycles(self) -> list[list[str]]:
    """cycle を持つ path を全件返す。cycle なし = []。
    PLAN-131 の DFS + recStack 版から networkx find_cycle に移行。
    cycle path が list[str] (ADR ID 列) として取得でき、エラー出力に活用できる。
    """
    cycles = []
    try:
        # find_cycle は最初の cycle を返す (nx.simple_cycles で全件取得)
        for cycle_edges in nx.simple_cycles(self._graph):
            cycles.append(cycle_edges)
    except nx.NetworkXNoCycle:
        pass
    return cycles
```

### 3.3 check_consistency 設計

不整合検出の対象:

| 不整合パターン | severity | 検出ロジック |
|---|---|---|
| `superseded_by` 設定 + status=Accepted | P1 warn | node の superseded_by フィールドと status を照合 |
| `supersedes` に存在しない ADR ID を指定 | P1 warn | edge 先の node が graph に存在するか確認 |
| cycle (A supersedes → B supersedes → A) | P0 fail | `detect_cycles()` 非空 |

### 3.4 helix doctor fail-close 昇格

```bash
# helix-hook (helix doctor 内) 変更
check_adr_decision_graph_cycles() {
    local cycles
    cycles=$(python3 -c "
from cli.lib.adr_graph import AdrGraph
g = AdrGraph.build_from_directory('docs/adr/')
cycles = g.detect_cycles()
print(len(cycles))
")
    if [[ "$cycles" -gt 0 ]]; then
        echo "FAIL: ADR decision graph に cycle が $cycles 件検出された"
        return 1  # P0 fail
    fi
    echo "PASS: ADR decision graph に cycle なし"
}
```

---

## §4. DoD (Definition of Done)

- [ ] `AdrGraph.topological_sort()` が networkx ベースで実装されている
- [ ] `AdrGraph.detect_cycles()` が networkx `simple_cycles` ベースに強化されている
- [ ] `AdrGraph.check_consistency()` が 3 パターンの不整合を検出する
- [ ] `helix doctor check_adr_decision_graph_cycles` が fail-close (exit 1) で動作する
- [ ] `helix adr graph --topological` オプションで時系列順 ADR 一覧が出力される
- [ ] `cli/lib/tests/test_adr_graph_topo.py` で T1〜T5 全件 PASS
- [ ] ADR-052 を L2 大局判断 snapshot として起票
- [ ] `python3 -m py_compile cli/lib/adr_graph.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_adr_graph_topo.py -v` 全件 PASS
- [ ] `helix doctor` 実行で check_adr_decision_graph_cycles が pass を返す

---

## §5. 実装計画

### Sprint .1 — topological_sort + detect_cycles 強化

**担当**: SE

**作業**:
1. `cli/lib/adr_graph.py` に `topological_sort()` 追加
2. `detect_cycles()` を networkx `simple_cycles` ベースに置き換え (cycle path 詳細出力)
3. `check_consistency()` 追加 (3 パターン検出)
4. `CycleDetectedError` 例外クラス定義

**受入条件**:
- `py_compile` PASS
- `AdrGraph(test_data).topological_sort()` がサイクルなし graph で決定論的な list を返す
- `AdrGraph(cycle_data).detect_cycles()` が cycle path を含む list を返す

### Sprint .2 — CLI 拡張 + helix doctor fail-close 化

**担当**: SE

**作業**:
1. `helix adr graph --topological` オプション追加 (topological_sort 出力)
2. `helix doctor` の `check_adr_decision_graph_cycles` を fail-close (exit 1) に変更
3. helix doctor 出力に `check_adr_consistency` (warn) を追加

**受入条件**:
- `helix adr graph --topological` が時系列順 ADR ID 一覧を stdout 出力
- `helix doctor` が cycle なし状態で pass を返す
- ADR-052 の起票が完了している

### Sprint .3 — テスト実装

**担当**: QA

**テストシナリオ**:

| ID | テスト内容 | 期待値 |
|---|---|---|
| T1 | cycle なし DAG の topological_sort | 決定論的な ADR ID list |
| T2 | supersedes chain (A→B→C) の sort 順 | [C, B, A] (旧が先) |
| T3 | cycle あり graph の detect_cycles | cycle path が返る |
| T4 | superseded_by 設定 + status=Accepted の check_consistency | warn が返る |
| T5 | 存在しない ADR ID への supersedes 参照の check_consistency | warn が返る |

**受入条件**:
- `pytest cli/lib/tests/test_adr_graph_topo.py -v` T1〜T5 全件 PASS

---

## §6. リスクと緩和策

| リスク | 影響 | 緩和策 |
|---|---|---|
| PLAN-131 の detect_cycles (DFS) と新版 (networkx) の挙動差 | 既存 test の regression | Sprint .1 で PLAN-131 の既存テストを先に通過させてから置き換え |
| networkx が未インストールの環境 | ImportError | PLAN-131 §5.1 で既に networkx を採用しているため問題なし |
| helix doctor fail-close 化で既存 ADR に意図せず cycle が発生 | helix doctor が全体 fail | Sprint .1 で現状 ADR の cycle 有無を先行確認してから fail-close 化 |

---

## §7. 完了記録 (実装後記入)

- completion_commits: (TBD)
- 実際の Sprint 所要: (TBD)
- 残 carry / debt: (TBD)
