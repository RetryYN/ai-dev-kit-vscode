---
plan_id: L7-v3-engine-cutover-gateplan
title: "L7-v3-engine-cutover-gateplan: V3 cutover-gate (4 hard checks, read-only detector, cli/lib/v3/cutover/, test-first)"
kind: impl
layer: L7
drive: be
status: draft
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: "docs/v3/cutover/cutover-design.md"
dependencies:
  requires:
    - L7-v3-engine-c1-schema-registryplan
    - L7-v3-engine-c2-projection-writerplan
  blocks: []
pairs_test_design:
  - cli/lib/v3/tests/test_cutover_gate.py
is_reference: false
agent_slots:
  - role: se
    slot_label: "SE — cutover-gate 4 hard check の verify-first 実装 (pin/dangling/rollback_preflight/rebuild_dry_run、ok=AND、read-only)"
  - role: qa
    slot_label: "QA — accepted_gap policy / dangling / rollback_preflight / ok=AND の境界網羅判定"
generates:
  - artifact_path: cli/lib/v3/cutover/gate.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/cutover/__init__.py
    artifact_type: python_module
  - artifact_path: cli/lib/v3/tests/test_cutover_gate.py
    artifact_type: test
created: 2026-06-26
revised: 2026-06-26
owner: SE
related_docs:
  - docs/v3/cutover/cutover-design.md
---

# L7-v3-engine-cutover-gateplan

## 0. 目的

V3 cutover-gate（[TL C-4](../../v3/cutover/cutover-design.md) / FR-V3-CUT-01）を Python で実装する。**read-only detector**（破壊なし・自動実行安全）。`ok = AND(pin_inventory, dangling, rollback_preflight, rebuild_dry_run)`、fail-close。**gate green まで cutover EXECUTION 禁止**。

## 0.5 unit 位置づけ（[C6 §4.5](../../v3/engine/doc-workflow-rules.md)）

- **unit_id**: U-ENG-CUT-GATE / **parent_l4_component**: cutover-gate（[cutover 設計](../../v3/cutover/cutover-design.md)）
- **trace_edges**: TL C-4 / FR-V3-CUT-01 → cutover-design §2 → 本 PLAN
- **依存**: C1（schema）+ C2（rebuild_projection。rebuild_dry_run で使用）。
- **buildable now**: dangling + rebuild_dry_run は現 V3 状態で実価値（V3 consistency + rebuild 能力の regression guard）。pin_inventory + rollback_preflight は **退役 inventory / promote reverse / window expiry を config 入力**にし、cutover scope 確定（後続）まで config 駆動で動く。

## 1. 受入条件（DoD）

[cutover-design.md §2/§5](../../v3/cutover/cutover-design.md) に従い下記 UT が green:

1. **rebuild_dry_run**: C1 `migrate` + C2 `rebuild_projection` を throwaway DB へ実行成功 → ok / C2 例外 → fail。
2. **dangling**: docs/v3 + cli/lib/v3 の壊れ参照（md link / Python import / PLAN generates·requires が実在へ解決）0 → ok / 壊れ link 注入 → 検出。
3. **pin_inventory**: 存続 surface（config 列挙）が全在 ∧ 退役 inventory（config）== cutover commit 退役集合 → ok / 過不足 → fail（数値非依存、config 突合）。
4. **rollback_preflight**: archive 先 writable + V2 path inventory（config）未改変 + promote reverse（config）定義済 + window expiry（config）定義済 + restore dry-run 成功 → ok / いずれか欠落 → fail。
5. **ok=AND**: 4 check の 1 つでも fail → gate fail。
6. **detector accepted_gap**: policy 3 要素（期限/owner/bridge）揃い → accepted_gap finding で ok 維持 / いずれか欠落 → fail-close。
7. **finding 機械可読**: 各 check が `{id, severity, subject, missing}` を返す（[C3 Finding](../../v3/engine/detector-wiring.md) 形式）。

## 2. 工程（test-first）

1. **RED**: `cli/lib/v3/tests/test_cutover_gate.py` に UT-CUT-01..07（§1 DoD を 1:1）を先に書き fail 確認。
2. **GREEN**: `cli/lib/v3/cutover/{gate,__init__}.py` 実装し UT green。
3. 3 点レビュー → `python3 -m pytest cli/lib/v3/tests/test_cutover_gate.py -q` + `py_compile`。

## 3. 実装方針

- **pure-function 3 層**（[C3](../../v3/engine/detector-wiring.md)）: `analyze_cutover(input) -> CutoverResult` 純関数 / `load_cutover_input(repo, db, config) -> CutoverInput` で I/O 隔離（git status / fs scan / DB query） / `cutover_messages(result) -> list[Finding]`。
- **stdlib のみ**（sqlite3 + subprocess(git) + os.walk + hashlib）。C1/C2 を import（再実装しない）: `from v3.schema import ddl`、`from v3.projection import writer`。
- rebuild_dry_run = `ddl.migrate(throwaway) → writer.rebuild_projection(throwaway, sources)` を例外捕捉で実行。
- pin_inventory / rollback の **config（退役 inventory / 存続 surface / V2 path inventory / promote reverse / window expiry）は dict/yaml 入力**（実体値は cutover scope 確定時に L7 で凍結。本 unit は config 駆動の判定ロジックと UT を固定）。
- source_kind: rebuild_dry_run=hybrid / dangling=file_snapshot / pin_inventory=hybrid / rollback_preflight=hybrid。

## 4. allowed_files

- `cli/lib/v3/cutover/*.py`（新規）/ `cli/lib/v3/tests/test_cutover_gate.py`（新規）
- **既存 V2 / cli/lib/v3/schema・projection は触らない**（import のみ）。read-only（cutover EXECUTION は実装しない＝本 unit は gate のみ）。

## 5. escalation

- 本 unit は **gate（検査）のみ**。cutover EXECUTION（promote/archive/退役/削除）は実装しない（別・人間承認、[cutover-design §4](../../v3/cutover/cutover-design.md)）。
- C1/C2 未 green なら着手しない。設計矛盾は止めて PM へ。

## 6. 用語 delta

なし。

## 7. FR delta

なし（FR-V3-CUT-01 の cutover-gate 部分の実装）。
