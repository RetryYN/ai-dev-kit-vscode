# PLAN-067〜074 V-model 4 artifact audit (PLAN-075 Phase 4)

| 項目 | 値 |
|---|---|
| audit_id | AUDIT-075-001 |
| 実施日 | 2026-05-17 |
| 実施者 | Opus (PM、grep 機械判定) |
| 対象 | PLAN-067 〜 PLAN-074 (8 PLAN) |
| 関連 PLAN | PLAN-075 Phase 4 (T401/T402) |
| 方法 | grep / find / ls による reference count 機械判定 |

## §1 サマリ

| PLAN | ① 設計 ref | ② 実装 ref | ③ test-design ref | ④ test-code ref | 判定 |
|---|---|---|---|---|---|
| 067 helix-automation-layer | 0 | 0 | 0 | 0 | **grandfather** (古い、reference 整備期前) |
| 068 vmodel-strengthening | 0/D-DB 1 | 1 | 0 | 0 | **P0 retrofit** (実装系、③ 不在で逆ピラミッド) |
| 069 g3-entry-blocker | 0 | 0 | 0 | 0 | **grandfather** (blocker resolution、scope 限定) |
| 070 l3-schema-and-contract | 12/12 | 1 | 0 | 0 | **P1** (設計系 PLAN、② は他 PLAN 由来。grandfather 化 + 双方向 ref 軽追記) |
| 071 carry-capability-detailing | 31/1 | 0 | 0 | 0 | **P1** (capability 詳細化 PLAN、② は他 PLAN 由来。grandfather 化 + 双方向 ref 軽追記) |
| 072 l4-5-integration | 5/4 | 12 | 0 | 7 | **P1** (実装系、test-code ref あるが ③ 不在。deferred-findings 化) |
| 073 vmodel-p28-test-coverage | 0 | 3 | 0 | 3 | **P2** (test coverage 補強 PLAN、scope 限定。deferred-findings 化) |
| 074 http-endpoint-layer | 23/2 | 15 | **0** | 7 | **P0 partial** (実態は完備、PLAN doc への test-design ref のみ欠落、本 audit で軽 retrofit 対象) |

凡例:
- ① 設計 ref = grep `D-API|D-DB` の count
- ② 実装 ref = grep `cli/lib/.*\.py` の count
- ③ test-design ref = grep `L4-test-design|test-design.md|D-TEST-DESIGN` の count
- ④ test-code ref = grep `cli/lib/tests/test_` の count

## §2 retrofit 優先順位 (Phase 4.3)

### §2.1 本 audit で実施 (本セッション、T404 + 軽 retrofit)

| ID | PLAN | スコープ | 担当 |
|---|---|---|---|
| T404 | PLAN-068 | ③ integration-test-design.md 新規 + PLAN doc に §V-model 4 artifact mapping section 追加 | Codex docs (background bo76ttvw1) |
| (軽) | PLAN-074 | PLAN doc に §V-model 4 artifact mapping section 追加 (実態は本セッション Phase 3 で完備) | Opus 直接 |

### §2.2 grandfather (P1、Phase 5 lint 例外、軽追記のみ)

| PLAN | 理由 | 対応 |
|---|---|---|
| PLAN-070 | 設計系 PLAN (L3 D-API/D-DB 起票)、② は PLAN-074 / 他 PLAN 由来 | §V-model mapping 軽追記 (本 audit のみ、retrofit 不要) |
| PLAN-071 | capability 詳細化 PLAN (D-API-CARRY 分離)、② は他 PLAN 由来 | §V-model mapping 軽追記 |

### §2.3 deferred-findings.yaml 化 (P1/P2)

| PLAN | 理由 | 想定対応 |
|---|---|---|
| PLAN-072 | L4.5 integration 実装系で test-code ref 7 件、③ artifact 化が筋。ただし retrofit cost 中、scope 別 PLAN | 別 PLAN (PLAN-079?) で対応、または Phase 4.4 carry note |
| PLAN-073 | test coverage 補強 PLAN、scope 限定 | deferred-findings、Phase 5 lint で grandfather 例外 |

### §2.4 grandfather (P0 以前、reference 整備期前)

| PLAN | 理由 |
|---|---|
| PLAN-067 | helix-automation-layer 起源 PLAN、reference 0 だが完遂済、設計 trace は他 PLAN (068/072/074) 経由で確立済 |
| PLAN-069 | g3-entry-blocker-resolution、blocker 解消のみのスコープ、4 artifact 該当性が薄い |

## §3 PLAN-074 軽 retrofit (実態確認)

PLAN-074 は本セッション Phase 3 (commit aa8a948) で 4 artifact 実態は完備:
- ① D-API EXT §3.1-3.5 5 endpoint reference 23
- ② cli/lib/http_api/* 実装 15
- ③ docs/v2/L4-test-design/PLAN-074-{unit,integration,system}-test-design.md 全 3 種揃い (本セッション新規)
- ④ cli/lib/tests/test_http_api_*.py 13 file (既存 5 結合 + 新規 8 単体、合計 90 cases PASS)

ただし PLAN-074.md 自体に test-design.md への reference が 0。本 audit で §V-model 4 artifact mapping section を追加し carry 解消。

## §4 Phase 5 lint への影響

Phase 5 で実装する `vmodel_lint.py` (helix doctor 統合 + G2-G4 fail-close) では:
- **lint 対象**: PLAN-074 / PLAN-068 (retrofit 後) と、本 audit 以降の新規 PLAN
- **grandfather 対象** (lint 例外): PLAN-067 / PLAN-069 / PLAN-070 / PLAN-071 / PLAN-072 / PLAN-073
- 例外リストは `.helix/audit/deferred-findings.yaml` に記録、lint 実行時に skip

## §5 deferred-findings 推奨追記

```yaml
# .helix/audit/deferred-findings.yaml に追記推奨
plan_068_retrofit_test_code_docstring:
  plan_id: PLAN-068
  severity: P2
  finding: "v22/v23 migration test の docstring に PLAN-068-integration-test-design.md case ID reference 未追記"
  reason: "T404 で ③ artifact 新規作成は完遂、④ docstring 追記は scope 過大"
  resolution: "次セッション or 別 PLAN で対応"

plan_070_071_grandfather:
  plan_ids: [PLAN-070, PLAN-071]
  severity: P1
  finding: "設計系 PLAN だが ② 実装が他 PLAN 由来のため 4 artifact 揃わない"
  reason: "設計系 PLAN の特性上、PLAN 単独の 4 artifact 完備は不可能"
  resolution: "Phase 5 lint で grandfather 例外指定"

plan_072_073_test_design_carry:
  plan_ids: [PLAN-072, PLAN-073]
  severity: P1
  finding: "実装系 PLAN で ④ test-code ref あるが ③ test-design 不在"
  reason: "retrofit cost 中、scope 別 PLAN で対応"
  resolution: "別 PLAN (PLAN-079?) または Phase 5 完遂後 carry session で対応"

plan_067_069_grandfather:
  plan_ids: [PLAN-067, PLAN-069]
  severity: P2
  finding: "reference 整備期前の PLAN、4 artifact 該当性薄"
  reason: "他 PLAN で実質 trace 確立済"
  resolution: "Phase 5 lint で grandfather 例外指定"
```

## §6 evidence

```
=== 各 PLAN の reference count (2026-05-17 audit) ===
PLAN-067 | D-API=0 | D-DB=0 | test-design=0 | test-code=0 | impl=0
PLAN-068 | D-API=0 | D-DB=1 | test-design=0 | test-code=0 | impl=1
PLAN-069 | D-API=0 | D-DB=0 | test-design=0 | test-code=0 | impl=0
PLAN-070 | D-API=12 | D-DB=12 | test-design=0 | test-code=0 | impl=1
PLAN-071 | D-API=31 | D-DB=1 | test-design=0 | test-code=0 | impl=0
PLAN-072 | D-API=5 | D-DB=4 | test-design=0 | test-code=7 | impl=12
PLAN-073 | D-API=0 | D-DB=0 | test-design=0 | test-code=3 | impl=3
PLAN-074 | D-API=23 | D-DB=2 | test-design=0 | test-code=7 | impl=15
```

ファイル一覧:
- docs/v2/L4-test-design/PLAN-074-{unit,integration,system}-test-design.md (3 種揃い、本セッション完遂)
- docs/v2/L3-detailed-design/D-API/D-API-{draft,EXTENDED-draft,CARRY-draft}.md (3 種揃い)
- docs/v2/L3-detailed-design/D-DB/D-DB-{draft,EXTENDED-draft}.md (2 種揃い)
