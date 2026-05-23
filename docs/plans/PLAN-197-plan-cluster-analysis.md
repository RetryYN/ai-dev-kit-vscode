---
plan_id: PLAN-197
title: PLAN cluster analysis (依存 graph cluster detection)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — networkx 依存 graph 構築・community detection algorithm 実装・CLI 拡張"
  - role: pmo-sonnet
    slot_label: "PMO — cluster summary 設計確認・既存 plan_validator 整合チェック"
generates:
  - artifact_type: python_module
    path: cli/lib/plan_cluster.py
  - artifact_type: cli_extension
    path: cli/helix-plan
  - artifact_type: test
    path: cli/lib/tests/test_plan_cluster.py
  - artifact_type: doc_update
    path: docs/commands/index.md
dependencies:
  requires:
    - PLAN-131
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - docs/plans/PLAN-131-adr-dependency-graph.md
  - cli/lib/plan_validator.py
  - docs/plans/PLAN-091-v5-plan-framework-core.md
acceptance_criteria:
  - "helix plan cluster が全 PLAN.md を読み込み dependencies graph を構築できる"
  - "Louvain / Leiden algorithm で cluster を検出し、cluster ID と構成 PLAN を JSON / text で出力できる"
  - "各 cluster の summary (構成 PLAN 数 / 共通 kind / 共通 drive / 重複候補ペア) を表示できる"
  - "同一 cluster 内で title 類似度が高い PLAN ペアを重複統合候補として flagging できる"
  - "python3 -m py_compile cli/lib/plan_cluster.py PASS"
  - "pytest test_plan_cluster.py 全 PASS (8 case 以上)"
  - "networkx / python-louvain が未インストールの場合は graceful degradation (WARN + 終了)"
---

# PLAN-197: PLAN cluster analysis (依存 graph cluster detection)

## L2 凍結 (ADR snapshot)

networkx + community detection 採用は新規外部ライブラリ依存だが、HELIX 既存の
依存 graph 基盤 (PLAN-131) の延長実装にとどまる。L2 大局判断は PLAN-131 で凍結済み。
本 PLAN に独立した ADR snapshot は不要。

## 背景

本 session で 87 PLAN が起票され、docs/plans/ に PLAN-001〜197 が蓄積された。
PLAN frontmatter の dependencies フィールドにより graph 構造は既に定義されているが、
関連 PLAN 群の「かたまり」は目視で識別するしかない状況にある。

問題ケース:

- 同一機能に複数 PLAN が分散して重複している可能性がある
- parent のない孤立 PLAN が drift の原因となる
- セキュリティ / DB / hook 等の領域で類似 PLAN が並立している

community detection algorithm (Louvain / Leiden) を適用して関連 PLAN を自動 grouping し、
重複候補の抽出と整理判断を機械支援する。

## WebSearch 履歴 — skip

networkx は Python 標準的グラフ解析ライブラリ (MIT ライセンス)。
python-louvain (community package) は Blondel et al. 2008 アルゴリズム実装。
PLAN-131 で採用済みの技術スタックを拡張するため外部 standard 検索は不要。

## 設計方針

### graph 構築

dependencies.requires / dependencies.parent を有向エッジとして読み込む。
plan_validator.py の `_build_dependency_graph` を再利用する。

```
PLAN-A ──requires──▶ PLAN-B
PLAN-C ──parent──▶  PLAN-D
```

無向 graph に変換した上で community detection を適用する (有向 graph のままでは
Louvain が未サポート)。

### cluster 検出

```python
import community as community_louvain
import networkx as nx

G = nx.Graph()
# edges を追加
partition = community_louvain.best_partition(G)
# partition: {plan_id: cluster_id, ...}
```

networkx が未インストールの場合は `ImportError` をキャッチし WARN を出力して終了。

### 重複候補スコアリング

同一 cluster 内で以下のいずれかに該当するペアを重複統合候補として出力する:

| 条件 | スコア |
|---|---|
| title に共通語句 3 words 以上 | +2 |
| kind が同一 | +1 |
| drive が同一 | +1 |
| generates の path prefix が一致 | +2 |

スコア >= 4 を重複候補 (HIGH)、2-3 を類似候補 (MEDIUM) として区分する。

### 出力形式

```bash
# text (default)
helix plan cluster

Cluster 0 (8 plans): hook / impl / be
  PLAN-087, PLAN-089, PLAN-109, PLAN-117, PLAN-125, PLAN-144, PLAN-157, PLAN-163
  Duplicate candidates (HIGH):
    - PLAN-109 ↔ PLAN-117: "PostToolUse hook" common (score=5)

# JSON
helix plan cluster --format json
```

## 実装計画

### Sprint .1: graph 構築 + community detection (Codex se)

`cli/lib/plan_cluster.py` に以下を実装する:

- `build_graph(plans_dir: Path) -> nx.Graph`: 全 PLAN.md を scan して依存 graph 構築
- `detect_clusters(G: nx.Graph) -> dict[str, int]`: Louvain で partition を返す
- `summarize_clusters(plans_dir, partition) -> list[ClusterSummary]`: kind / drive 集計
- unit test 4 case (build_graph / detect_clusters / graceful_degradation / single_node)

完了条件: `python3 -m py_compile` PASS + pytest 4 PASS

### Sprint .2: 重複候補スコアリング (Codex se)

- `score_duplicates(cluster: list[PlanMeta]) -> list[DuplicateCandidate]`: スコア算出
- HIGH / MEDIUM 区分出力
- unit test 4 case (高スコアペア / 同 kind / generates prefix / 閾値境界)

完了条件: pytest 累計 8 PASS

### Sprint .3: CLI 統合 + helix-plan サブコマンド (Codex se)

- `cli/helix-plan` に `cluster` subcommand 追加
- `--format text|json` / `--min-score N` / `--cluster-id N` フィルタ対応
- docs/commands/index.md に `helix plan cluster` コマンド追記
- bats test 4 case (help / text output / json output / graceful_degradation)

完了条件: bats 4 PASS + docs 更新済

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/plan_cluster.py` PASS
- [ ] `pytest cli/lib/tests/test_plan_cluster.py` 8 case 全 PASS
- [ ] bats test 4 case PASS
- [ ] networkx 未インストール時の graceful degradation 確認
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] cli/lib/plan_cluster.py 実装済 (build_graph / detect_clusters / score_duplicates)
- [ ] `helix plan cluster` subcommand 動作確認
- [ ] pytest 8 PASS + bats 4 PASS
- [ ] docs/commands/index.md 更新済
- [ ] graceful degradation (networkx 未インストール) 動作確認
- [ ] helix doctor pass 数現行以上維持

## carry / リスク

- networkx + python-louvain は pip install 必要。requirements.txt / pyproject.toml への追記が別途必要
- Louvain は非決定的アルゴリズム (random seed 依存) → test は cluster 数や partition ではなく
  同一 component 内で connected であることを検証する
- PLAN 数増加で scan 時間が増大する → `--plans-dir` で対象絞り込みを提供する

## 関連 reference

- PLAN-131 (ADR dependency graph、requires)
- PLAN-091 (V5 framework core、parent)
- [[feedback_codex_parallel_dependency_check]]
