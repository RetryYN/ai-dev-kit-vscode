---
plan_id: PLAN-124
title: helix doctor --json output 標準化 (machine-readable CI / hook 統合)
status: draft
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — --json flag 実装・schema 設計・python_module 修正"
  - role: qa
    slot_label: "QA — schema validation test・既存 text output regression 確認"
  - role: pmo-sonnet
    slot_label: "PMO — JSON schema 妥当性確認・PLAN-110 warn framework との整合チェック"
generates:
  - artifact_type: python_module
    path: cli/lib/helix_doctor.py
  - artifact_type: design_doc
    path: docs/v2/L4-test-design/PLAN-124-unit-test-design.md
  - artifact_type: test
    path: cli/lib/tests/test_helix_doctor_json.py
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_docs:
  - cli/lib/helix_doctor.py
  - cli/helix-doctor
  - docs/plans/PLAN-110-helix-doctor-warn-reduction.md
  - docs/plans/PLAN-077-sprint-plan-standardization.md
acceptance_criteria:
  - "helix doctor --json が valid JSON を stdout に出力する"
  - "JSON schema に checks (check_id / status / count / reasons) 配列が含まれる"
  - "summary フィールドに passed / failed / warnings の件数が含まれる"
  - "helix doctor (既存 text output) に regression がない"
  - "python3 -m py_compile cli/lib/helix_doctor.py PASS"
  - "unit test (pytest) 全 PASS"
  - "PLAN-110 Sprint .1 が helix doctor --json を利用して warn 分類できること確認"
---

# PLAN-124: helix doctor --json output 標準化 (machine-readable CI / hook 統合)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 CLI への flag 追加** であり、新規 framework 採用 / fail-close 化 /
外部仕様採用を含まない。ADR snapshot は不要。

根拠:
- JSON 出力は既存 Python module の出力形式追加であり、設計方針の大局判断を伴わない
- schema 設計は内部 check 構造の直接 serialize で外部 standard 依存なし
- PLAN-110 warn 分類 framework の utility 拡張として位置づける

## 背景

`helix doctor` は現在 human-readable text output のみ。以下の課題がある:

1. **CI 統合困難**: GitHub Actions / hook から warn 件数を取得するには脆弱な text parse が必要
2. **PLAN-110 Sprint .1 の障壁**: warn 80 件の check 別集計に `grep | awk` text parse が必要
3. **dashboard 統合不可**: structured data が取得できない

`--json` flag で machine-readable 出力を標準化し、CI / PLAN-110 warn 分類 / dashboard 統合を実現する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

内部 CLI への flag 追加、外部ライブラリ / 業界 standard への新規依存なし。
JSON 出力 schema は既存 check 構造の直接 serialize で完結。WebSearch **skip**。

## 設計方針

### JSON schema 設計

```json
{
  "summary": { "passed": 24, "failed": 0, "warnings": 80 },
  "checks": [
    {
      "check_id": "check_adr_index",
      "status": "pass",
      "count": 1,
      "reasons": ["24 ADRs indexed"]
    },
    {
      "check_id": "check_subagent_phase",
      "status": "warn",
      "count": 20,
      "reasons": ["pmo-haiku not fired in L2", "..."]
    }
  ]
}
```

フィールド:
- `summary`: passed / failed / warnings の件数 (PLAN-110 と整合)
- `checks[].check_id`: check 識別子、`checks[].status`: pass/warn/fail
- `checks[].count`: reasons 件数、`checks[].reasons`: 説明文リスト

### CLI flag 追加

```bash
helix doctor          # 既存 text output (変更なし)
helix doctor --json   # JSON output を stdout に出力
```

`--json` flag は `cli/helix-doctor` (bash) 受け取り → Python module に渡す。
text / json は独立した出力経路、互いに影響しない。

## 実装計画

### Sprint .1: Python module 修正 (Codex se 委譲)

1. `cli/lib/helix_doctor.py` check 実行結果収集ロジックを確認
2. `format_json(checks, summary) -> str` 関数を追加
3. `cli/helix-doctor` (bash) に `--json` flag 解析を追加し Python module に渡す

完了条件: `helix doctor --json` が valid JSON を stdout に出力 + `python3 -m py_compile` PASS

### Sprint .2: unit test + V-model artifact (Codex qa 委譲)

1. `docs/v2/L4-test-design/PLAN-124-unit-test-design.md` 新規作成 (V-model artifact ③)
2. `cli/lib/tests/test_helix_doctor_json.py` 新規作成 (V-model artifact ④) 6 case:
   - JSON parse 可能
   - summary に passed/failed/warnings が含まれる
   - checks 配列に check_id/status/count/reasons が含まれる
   - status が pass/warn/fail のいずれか
   - `--json` なし text output に変化なし
   - summary 件数が checks 配列と整合する

完了条件: `pytest cli/lib/tests/test_helix_doctor_json.py -v` 全 PASS

### Sprint .3: PLAN-110 統合確認 + regression (Codex qa 委譲)

1. `helix doctor --json` で check 別集計 → PLAN-110 Sprint .1 が利用可能であることを実証
2. `helix doctor` (text) regression: pass 件数維持 / fail 0 / warn 件数不変
3. pmo-sonnet review

完了条件: regression なし + pmo-sonnet review PASS

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/helix_doctor.py` PASS
- [ ] `pytest cli/lib/tests/test_helix_doctor_json.py -v` 全 PASS
- [ ] `helix doctor` (text) に regression がないこと確認
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] V-model artifact ③ test design doc 起票済 (PLAN-124-unit-test-design.md)
- [ ] commit message に `PLAN-124 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `helix doctor --json` が valid JSON を stdout に出力する
- [ ] JSON schema (summary + checks[]) が仕様通り
- [ ] `helix doctor` 既存 text output に regression なし
- [ ] `python3 -m py_compile` PASS
- [ ] unit test 全 PASS (6 case)
- [ ] V-model artifact ③ test design doc (PLAN-124-unit-test-design.md) 存在
- [ ] PLAN-110 Sprint .1 が `helix doctor --json` を利用できることを確認
- [ ] helix doctor pass 数が現行以上 (regression なし)

## carry / 学び (起票時記録)

- **bash vs Python の実装場所**: `--json` flag の受け渡しは bash 側で `HELIX_DOCTOR_JSON=1`
  環境変数経由か Python argparse に直接渡す。Sprint .1 でファイル構造を確認してから決定する
- **suppress yaml との統合**: PLAN-110 Wave C で `.helix/doctor-suppress.yaml` 導入後、
  `--json` output に `suppressed` フィールドを追加する (PLAN-110 完了後 carry)
- **JSON Schema formal 定義**: 本 PLAN は informal 設計に留める。JSON Schema draft-07 は将来 carry

## 関連 reference

- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- PLAN-013 (code catalog taxonomy、helix code stats との構造参考)
- PLAN-077 (Sprint Plan 標準構造、mandatory in sprint の根拠)
- PLAN-110 (helix doctor warn 漸減 framework、Sprint .1 が --json を要求)
- cli/lib/helix_doctor.py (warn check 実装の正本)
- cli/helix-doctor (bash CLI dispatcher)
