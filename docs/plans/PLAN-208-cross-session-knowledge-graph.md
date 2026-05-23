---
plan_id: PLAN-208
title: "PLAN-208: cross-session knowledge graph (handover/memory/PLAN 統合 graph)"
kind: impl
layer: cross
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
created: 2026-05-23
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — graph schema + query API 設計 adversarial check"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 PLAN/ADR/handover/memory 資産との整合確認"
  - role: se
    slot_label: "SE — graph DB schema + CRUD + helix graph CLI 実装"
  - role: qa
    slot_label: "QA — graph query + visualization unit test + bats test"
generates:
  - artifact_path: cli/lib/knowledge_graph.py
    artifact_type: python_module
  - artifact_path: cli/helix-graph
    artifact_type: cli_extension
  - artifact_path: cli/lib/migrations/v38_knowledge_graph.py
    artifact_type: schema_migration
  - artifact_path: cli/lib/tests/test_knowledge_graph.py
    artifact_type: test
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-131
    - PLAN-192
  blocks: []
related_plans:
  - PLAN-131
  - PLAN-192
  - PLAN-197
related_adr: []
---

# PLAN-208: cross-session knowledge graph (handover/memory/PLAN 統合 graph)

> **kind**: impl (helix.db 拡張 + CLI 新設)
> **layer**: cross (L1 要件 〜 L4 実装・L11 運用学習を横断する基盤 infrastructure)
> **drive**: be (Python helper + SQLite + CLI 中心)
> **本 PLAN の役割**: PLAN / ADR / handover / memory / commit / skill を単一 knowledge graph で統合し、cross-reference 関係を可視化・クエリ可能にする。セッション断絶による文脈喪失と重複委譲を構造的に解消する。

---

## §0. 起票背景

現行 HELIX では handover / memory / PLAN がそれぞれ独立したストア (CURRENT.json / MEMORY.md / docs/plans/*.md) に分散しており、以下の問題が恒常的に発生している。

1. **cross-reference の不可視化**: PLAN-X が ADR-Y に依存し、ADR-Y が handover タスクで詰まっているという連鎖が、手作業で 3 ファイルを読むまで分からない。
2. **重複委譲**: 前 session で同一 skill/ADR に言及した handover を見落とし、同じ調査を再委譲する。
3. **影響波及の追跡不能**: commit C が PLAN-X の Sprint .3 を閉じた事実が自動記録されず、LeafToRoot の影響評価が人間依存になっている。

knowledge graph を helix.db に埋め込み、既存 HELIX asset をノードとして取り込むことで上記 3 問題を解消する。

---

## §1. 目的

1. helix.db に `kg_node` / `kg_edge` テーブルを追加し、6 ノード種別・7 エッジ種別を定義する (Sprint .1)
2. 既存 PLAN / ADR / handover / memory / commit / skill を graph に import する CLI を実装する (Sprint .2)
3. `helix graph query <node>` でノード周辺の edge を返し、graphviz dot 形式で出力する (Sprint .3)
4. 既存 test 全 PASS + graph 操作 unit test を追加する (Sprint .4)

---

## §2. 設計

### 2.1 ノード種別

| node_type | 代表 ID 例 | import 元 |
|---|---|---|
| `plan` | PLAN-208 | docs/plans/*.md frontmatter |
| `adr` | ADR-025 | docs/adr/*.md frontmatter |
| `handover` | task_id から生成 | .helix/handover/CURRENT.json |
| `memory` | memory file slug | .claude/agent-memory/**/*.md |
| `commit` | sha[:8] | git log |
| `skill` | common/testing | skills/*/SKILL.md frontmatter |

### 2.2 エッジ種別

| edge_type | 意味 | 典型例 |
|---|---|---|
| `requires` | 前提依存 | PLAN-208 requires PLAN-131 |
| `blocks` | 後続ブロック | PLAN-A blocks PLAN-B |
| `parent` | 親子 | PLAN-208 parent PLAN-MM-001 |
| `related` | 緩い関連 | PLAN-208 related ADR-025 |
| `supersedes` | 上書き/廃止 | ADR-new supersedes ADR-old |
| `cites` | 参照 | handover cites PLAN-208 |
| `closes` | 完了対応 | commit closes PLAN-208 |

### 2.3 helix.db schema (v38 migration)

```sql
CREATE TABLE IF NOT EXISTS kg_node (
    id TEXT PRIMARY KEY,           -- 例: "plan:PLAN-208", "commit:abc1234f"
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kg_edge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id TEXT NOT NULL REFERENCES kg_node(id),
    dst_id TEXT NOT NULL REFERENCES kg_node(id),
    edge_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS ix_kg_edge_src ON kg_edge(src_id);
CREATE INDEX IF NOT EXISTS ix_kg_edge_dst ON kg_edge(dst_id);
```

---

## §3. CLI 設計

```
helix graph import [--node-type plan|adr|handover|memory|commit|skill] [--all]
helix graph query <node-id> [--depth N] [--edge-type TYPE] [--json]
helix graph viz <node-id> [--depth N] [--output FILE]   # graphviz dot 生成
helix graph stats                                       # ノード/エッジ数 集計
helix graph diff <commit1> <commit2>                    # graph 差分 (Sprint .3 後半)
```

`helix graph viz` は graphviz dot 形式を stdout へ出力する。`--output FILE` 指定時は `dot -Tpng` を自動実行 (graphviz CLI が存在する場合のみ)。不在時は dot テキストのみ出力して warn する。

---

## §4. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| Sprint .1 | kg_node / kg_edge schema 定義 + v38 migration | se | `helix db migrate` で v38 が idempotent 適用 PASS |
| Sprint .2 | import コマンド実装 (plan/adr/handover/memory 対象) | se | `helix graph import --all` で既存資産 50+ ノードが登録される |
| Sprint .3 | query + viz CLI 実装 | se | `helix graph query PLAN-208 --depth 2` が隣接ノード一覧を返す |
| Sprint .4 | unit test + bats test + 既存回帰 PASS | qa | `pytest cli/lib/tests/test_knowledge_graph.py` 全 PASS |

---

## §5. WebSearch skip 根拠

本 PLAN は SQLite adjacency list + graphviz という枯れた技術スタック。新 framework 採用・L2 大局判断なし。PLAN-087 ガードレール「設計 doc 新規起票・大幅 scope 変更時」に非該当。**WebSearch skip: 既存技術スタック延長 (SQLite + graphviz dot)、新技術採用なし**。

---

## §6. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-208-cross-session-knowledge-graph.md |
| ② 実装コード | Sprint .1〜.3 で起票 | cli/lib/knowledge_graph.py / cli/helix-graph |
| ③ テスト設計 | Sprint .4 entry で策定 | docs/v2/L4-test-design/PLAN-208-kg-test-design.md (予定) |
| ④ テストコード | Sprint .4 で実装 | cli/lib/tests/test_knowledge_graph.py |

**双方向 reference**:
- 本 PLAN → 実装: generates.artifact_path `cli/lib/knowledge_graph.py`
- 実装 → 本 PLAN: module docstring に「設計: PLAN-208」を追記
- 本 PLAN → テストコード: generates.artifact_path `cli/lib/tests/test_knowledge_graph.py`
- テストコード → 本 PLAN: test docstring に「DoD 検証: PLAN-208 §7」を追記

---

## §7. DoD (Definition of Done)

1. Sprint .1: v38 migration が `helix db migrate` で idempotent 適用される
2. Sprint .2: `helix graph import --node-type plan` で docs/plans/*.md が kg_node に登録される
3. Sprint .3: `helix graph query PLAN-208 --depth 1 --json` が隣接ノード + エッジ種別を JSON で返す
4. Sprint .3: `helix graph viz PLAN-208 --depth 2` が graphviz dot テキストを stdout 出力する
5. Sprint .4: `pytest cli/lib/tests/test_knowledge_graph.py -q` が全 PASS
6. Sprint .4: `bash -n cli/helix-graph` が syntax check PASS
7. `python3 cli/lib/plan_validator.py docs/plans/PLAN-208-*.md` が PASS

---

## §8. リスク

| リスク | 緩和策 |
|---|---|
| v38 migration 番号が他 PLAN と衝突 | Sprint .1 entry で `helix db version` を確認し番号確定 |
| graphviz CLI 不在時に viz が失敗 | dot コマンド存在チェック + warn-only (dot テキストのみ出力) |
| import が重くなりタイムアウト | batch size 100 + progress 表示、import は background 実行可 |
| PLAN-131/192 未完了時の依存詰まり | Sprint .1 は schema のみ。import/query は PLAN-131/192 なしでも動作可能にする |

---

## §9. 関連 PLAN

- PLAN-131: ADR graph 実装。本 PLAN の adr ノード import 設計の参考実装
- PLAN-192: graph viz 基盤。本 PLAN の viz CLI と設計統合を検討
- PLAN-197: cluster analysis。本 PLAN が蓄積した edge データを PLAN-197 が活用する後続 PLAN
