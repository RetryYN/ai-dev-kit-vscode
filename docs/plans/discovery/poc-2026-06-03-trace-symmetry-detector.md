---
plan_id: poc-2026-06-03-trace-symmetry-detector
title: "Action(PoC): V2 Phase1 — 設計↔テスト trace 対称性 detector 最小 PoC"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
workflow: discovery
kind: poc
layer: L1
drive: poc
status: in_progress
created: 2026-06-03
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — detector PoC 実装（Codex、cli/lib + helix doctor サブ）"
  - role: tl-advisor
    slot_label: "TL — 指標定義・preflight fail 境界の確認"
generates:
  - artifact_path: cli/lib/trace_symmetry.py
    artifact_type: python_module
dependencies:
  parent: null
  requires: []
  blocks: []
related_docs:
  - docs/plans/process/process-2026-06-03-v2-implementation-roadmap.md
  - docs/plans/reverse/reverse-2026-06-03-l1-l3-trace-hardening.md
---

# Phase1 Action(PoC): 設計↔テスト trace 対称性 detector

V2 Phase1 のワークフロー改善（root cause = 設計ID↔テスト trace の対称性を ID 粒度で機械検出する detector 不在）の最小 PoC。doc 修正前に baseline 化し、修正後の coverage 改善を機械計測する（TL: detector 実装前の手修正は再 drift リスク P1）。

## 1. 仮説 / PoC scope
- **仮説**: markdown doc の frontmatter フィールド（`generates` / `pairs_test_design` / `covers` / `parent_design`）から設計ID と テストID を抽出し、双方向対応を機械計測すれば、L4↔L9 / L1↔L14 / L3↔L12 等の片肺を ID 粒度で検出できる。
- **PoC scope（Phase1 = 最小 lint/監査、fail-close は Phase3）**: 計測と baseline 出力のみ。advisory（warn/json）。`helix doctor` の hard gate 化はしない。

## 2. 採用 / 棄却基準
- 採用: L4↔L9 の既知片肺（NFR 23→観点2、IF-05 欠落）と L3↔L12 の FR-02〜14 uncovered を**誤検出なく**検出できる。
- 棄却: 本文中 ID 参照や deprecated doc を拾って偽陽性が baseline を信用できない水準にする。

## 3. detector 出力（TL 反映、外部調査 OFT/sphinx-traceability 由来）
- `uncovered_req`（設計IDで対応テスト0）/ `orphan_test`（テストで設計に戻れない）/ `coverage_pct`（binary, primary）
- `duplicate_id` / `wrong_layer_pair` / `missing_pair_frontmatter` / `excluded_with_reason` / `deprecated_excluded`
- `balance_ratio` は補助（dashboard/warning のみ、合否主判定にしない）
- **preflight fail（coverage 計算前）**: duplicate_id / missing_pair_frontmatter / wrong_layer_pair
- **誤検出回避**: frontmatter フィールド限定抽出（本文除外）/ deprecated doc 除外（明示）/ ID 形式 validation / duplicate 先行検出 / 移行期は missing_frontmatter を別カテゴリ

## 4. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-03 | PoC 起票。TL 設計確認済。Codex se へ実装委譲予定（cli/lib/trace_symmetry.py + helix doctor 監査サブ、advisory）。 | PM (Opus) |
