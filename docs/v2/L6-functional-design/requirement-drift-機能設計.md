---
doc_id: L6-FUNCTIONAL-DESIGN-REQUIREMENT-DRIFT
title: "requirement_drift detector 機能設計"
status: draft
layer: L6
pairs_with: L7
pairs_test_design: docs/v2/L7-test-design/requirement-drift-単体テスト設計.md
parent_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
implementation_status: implemented-mvp
owner: TL
created: 2026-06-09
---

# requirement_drift detector 機能設計

## 1. 目的

`requirement_drift` は、L1 数字式 FR と L3 名前ベース FR の ID scheme 差を考慮し、L1/L3 要件から L4-L6 設計までの縦 trace 欠落を検出する L6 detector である。検出結果は `VG-overview.required_clean.requirement_drift` に接続し、明確な L6 設計欠落だけを `helix doctor --gate` / `helix push --gate` の block 対象にする。

## 2. 上位 Trace

| L3 FR | 関連 L1 FR | 本機能での役割 |
|---|---|---|
| FR-DRIFT-01 | FR-11 | 要件 / 設計 trace drift の検出と routing |
| FR-CHANGEPROP-01 | BR-12 由来 | 上流 ID 変更に対する下流追従確認 |
| FR-4ART-01 | FR-08 | L6↔L7 pair / 4 artifact trace への接続 |
| FR-GATE-01 | FR-05 | `G-vg-overview` fail-close への接続 |

## 3. 機能一覧

| FN-ID | 関数 / surface | 入力 | 出力 | 判定 |
|---|---|---|---|---|
| FN-RD-01 | `collect_requirement_drift(project_root, focus="L6", check_stale=false)` | project root、focus、check_stale | JSON 互換 dict | L1/L3 FR 定義、L3 parent-child mapping、L4-L6 design link を集計 |
| FN-RD-02 | parent-child mapping | L3 requirement table | `parent_id -> child_ids` | L1 数字式 FR が L3 名前ベース FR に詳細化されていれば downstream とみなす |
| FN-RD-03 | blocking/advisory 分離 | findings | `blocking_clean`, `summary.blocking_findings` | `missing_downstream` / `orphan_design` / `orphan_code` のみ fail-close 対象 |
| FN-RD-04 | waiver validation | `.helix/requirement-drift-waivers.yaml` | `waived_with_reason` | reason / owner / expires を持つ waiver のみ有効 |
| FN-RD-05 | CLI / doctor surface | `python3 -m cli.lib.requirement_drift`, `helix doctor check_requirement_drift` | JSON / text | 既定 `focus=L6`、`--focus L7` 明示時のみ code/test を集計。mtime stale は `--check-stale` 明示時のみ集計 |

## 4. 判定ルール

| Finding | Gate 扱い | 理由 |
|---|---|---|
| `missing_downstream` | blocking | L1/L3 FR が L4-L6 設計へ接続していない |
| `orphan_design` | blocking | L4-L6 設計上の FR ID が上流定義へ戻れない |
| `orphan_code` | blocking only in `focus=L7` | L7 code/test scan 明示時だけ対象 |
| `semantic_label_mismatch` | advisory | L4-L6 表の説明文は要約・カテゴリを含むため、機械的な語彙差だけでは block しない。`code` / `registry-only` などの総称 downstream label は mismatch 対象外 |
| `stale_freeze` | advisory opt-in | dirty worktree の mtime で過検出しやすいため、`--check-stale` 明示時のみ再凍結候補として扱う |

## 5. L7 Pair

単体テスト設計は `docs/v2/L7-test-design/requirement-drift-単体テスト設計.md` を正とする。`RD-UT-*` は requirement_drift 専用 ID であり、G7 の `UT-*` inventory には混入させない。
