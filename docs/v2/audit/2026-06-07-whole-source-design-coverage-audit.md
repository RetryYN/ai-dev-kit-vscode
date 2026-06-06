# Whole-source ⊆ Design Coverage Audit (2026-06-07)

> 「V2 設計が既存ソースのすべてを内包しているか」の**徹底検証 (whole-coverage audit)** 結果。
> goal「設計に既存ソースのすべてが含まれているか徹底検証し、なければ追加設計をする Recovery を回す。抜け漏れの一切の禁止」。
> 本書は検証 evidence の正本。是正は `process-2026-06-07-whole-source-design-coverage-closure` Process で実行する。

| 項目 | 値 |
|---|---|
| audit_id | AUDIT-WSDC-001 |
| 実施日 | 2026-06-07 |
| recipe | verification-strategy §11 whole-coverage audit |
| 判定式 | `detector_clean AND semantic_gate_pass`（coverage 100% 単独 pass 禁止） |
| 検証手段 | grep / ls / `helix doctor` / `functional_registry_checks.py` 実行（全件コマンド実測） |
| 結論 | **NOT covered**（3 segment に抜け漏れ）→ Recovery Process へ routing |

## 1. 検証対象 universe（母数の固定）

### 1.1 既存ソース universe（registry の DEFAULT_SCAN_TARGETS = 7 domain）
| domain | scan glob | ディスク実数 |
|---|---|---|
| cli | `cli/helix-*` | 94 |
| lib | `cli/lib/*.py`（非 test, 非再帰） | 144 |
| hook | `.claude/hooks/*` | 18 |
| agent | `.claude/agents/*.md` | （registry 19） |
| skill | `skills/**/SKILL.md` | （registry 131） |
| workflow | `HELIX-workflows/helix-process/*.md` | （registry 49 + 未登録 6） |
| template | `cli/templates/**/*` | 114 |

> 注: scan glob は `cli/lib/*.py` 非再帰のため `cli/lib/tests/*.py`(248) は対象外（test は source ではないため意図的除外）。`cli/libexec/`(9) は現 scan target に含まれない（**検出器の盲点候補**、Action2 で要評価）。

### 1.2 設計 universe（docs/v2 設計層）
- L4-basic-design / L5-detailed-design / **L6-functional-design**（FN-* 機能設計）。
- L6-functional-design の FN-* ユニーク総数 = **33**（FN-RDB19/DDD12/CRREG10/FREG9/GUARD3/DB3/CONTRACT3/ROUTE2/HANDOVER2/CATALOG2/AGENT2/WS1/PLAN1/HTTP1/AUDIT1）。
- L7-test-design の UT-* ユニーク総数 = 33。

### 1.3 橋渡し = functional-registry（L3 SSoT）
- `cli/config/functional-registry.yaml` = **557 entry**（id 実数。CLAUDE.md/memory の「548」は drift、要 SSoT 是正）。
- domain 別: lib147 / skill131 / template114 / cli80 / workflow49 / agent19 / hook17。
- status 別: active540 / mandatory10 / deprecated4 / experimental2 / legacy_alias1。
- 各 entry = `{id: FR-*, code_paths:[...], l1_fr:[...], l3_fr:[...]}`。

## 2. coverage chain と segment 別 gap

```
既存ソース ──[seg1: check_functional_registry]──▶ functional-registry(557) ──[seg2: l1_fr/l3_fr]──▶ L1/L3 要件 ──[seg3: trace_symmetry]──▶ L6 FN-*(33)/L5 MOD-*/L4 NFR-IF-*
```

### Segment 1: source → registry（registry 完全性）— **8 件未登録**
ディスク上に存在するが registry 未登録の asset:
- workflow doc 6: `document-topology.md` / `forward-return-discipline.md` / `github-operations.md` / `plan-model.md` / `planning-to-requirements-transition.md` / `workflow-self-evaluation.md`（全て `HELIX-workflows/helix-process/`）
- template 2: `cli/templates/plan/v2/L02-ui-design-template.md` / `cli/templates/plan/v2/L06-function-design-template.md`

### Segment 2: registry → 要件 trace（l1_fr/l3_fr）— **44 件 invalid_fr_trace**
`l1_fr` と `l3_fr` が両方空 = 要件へ未トレースの entry（44件）:
- CLI(4): FR-CLI-006, 019, 074, 075
- SKILL(29): FR-SKILL-003,011,012,015,043,047,052,055,056,057,058,071,074,077,079,083,084,089,091,092,093,094,096,097,098,099,101,116,119
- WORKFLOW(3): FR-WORKFLOW-011, 027, 038
- TEMPLATE(8): FR-TEMPLATE-025,026,027,028,029,030,031,083

### Segment 3: registry/要件 → L6 機能設計（最大の穴）— **約 524 entry が設計未定義**
- registry 557 entry に対し L6 FN-* は **33 件のみ**（active540 基準でも約 94% が L6 機能設計を持たない）。
- これは既知 deferred finding `DF-WCAUDIT-L6L7-001`（「lib 関数の約 10% のみ freeze、残は設計未定義」）を Phase3 defer していたもの。**本 goal はこの defer の解消を要求**。

## 3. semantic 判定（十分条件）

- segment1/2 は機械 warn として検出済（`check_functional_registry`、warn-only）。fail-close 未昇格。
- segment3 を測る detector は**存在しない**（registry→設計層 被覆を機械検出する手段が無い = 抜け漏れが機械検出すらされない最重要 gap）。
- ∴ `detector_clean` 不成立、`semantic_gate_pass` 不成立 → **audit verdict = NOT covered**。

## 4. routing 判定（TL 諮問 2026-06-07 反映）

zero-omission の正しい定義（TL 採用 = **B'**）:
```
zero_omission = source⊆registry
            AND registry→L1/L3 trace complete
            AND 全 active registry entry が明示的な coverage_layer 分類を持つ（unknown=0）
```
- coverage_layer: `L6_required`（public callable/契約/DbC → FN+UT 1:1）/ `L5_required`（module境界/結合）/ `L4_required`（workflow/NFR/command family）/ `excluded_with_reason`（private glue/生成物/static template、上位設計ID+理由必須）。
- 却下: A（全 557 FN/UT 化 = 粒度誤り）/ C（registry+要件のみ = 設計未反映を温存）。

→ routing 先 = `process-2026-06-07-whole-source-design-coverage-closure`（workflow_chain: recovery→reverse→forward_refreeze、forward_return: L3 + 該当設計層 L4/L5/L6 と対 pair）。

## 5. 是正完了の機械的証明条件（Action 群の exit）

| detector | 合格条件 | 状態 |
|---|---|---|
| `source_scan_vs_registry`（=check_functional_registry の unregistered 部分） | unregistered=0 | seg1 解消で達成 |
| `registry_trace_complete`（=invalid_fr_trace 部分） | invalid=0、ID 実在 | seg2 解消で達成 |
| `registry_design_coverage`（**新設**） | 全 active entry に coverage_layer + design_id、unknown=0 / missing=0 / wrong_layer=0 | Action3 で新設 |
| `trace_symmetry` | L6_required は FN↔UT 1:1（balance_ratio≥1.0） | Action4 で達成 |
| semantic_gate | excluded / 層割当の妥当性を TL/PM 判定 | 機械化しない |

完了判定 = 上記 detector_clean **AND** semantic_gate_pass。`check_functional_registry` は clean baseline 後に ratchet→fail-close 昇格。
