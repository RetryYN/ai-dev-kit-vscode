---
plan_id: L7-helix-doctor-json-implplan
title: "L7-helix-doctor-json-implplan: helix doctor --json オプション追加 — helix recover C2 検出ロジック改善"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
revised: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-helix-recover-implplan.md
pairs_test_design:
  - docs/plans/L7/L7-helix-doctor-json-implplan.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — スコープ確認・finalize"
  - role: tl-advisor
    slot_label: "TL — JSON schema 設計 + 既存 doctor 出力との互換性確認"
  - role: se
    slot_label: "SE — cli/helix-doctor 修正 + JSON 出力実装 + test 追加"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・recover C2 連携確認"
generates:
  - artifact_path: cli/helix-doctor
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_doctor_json.py
    artifact_type: test
  - artifact_path: cli/tests/helix-doctor-json.bats
    artifact_type: test
dependencies:
  parent: null
  requires:
    - L7-helix-recover-implplan
  blocks: []
related_docs:
  - cli/helix-doctor
  - cli/lib/recovery_engine.py
  - docs/plans/L7/L7-helix-recover-implplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計 (parent_design)**: [L7-helix-recover-implplan.md](L7-helix-recover-implplan.md) (recover C2 検出が helix doctor --json を呼ぶが、現状 doctor は --json オプション未対応 = minor bug の修正)
> **本 PLAN の対象**: `cli/helix-doctor` に `--json` オプションを追加し、機械可読 JSON 出力 (pass/fail/warn 件数 + advisory 詳細) を提供する。
> **位置づけ**: 2026-05-24 本 session smoke test (helix recover check 実行時) で発覚した minor bug 修正。recover C2 検出は `helix doctor --json` を呼ぶが、現状の helix-doctor は `--json` 引数を受け付けず "不明なオプション: --json" でエラーを返す。recover はこれを WARN として扱う (安全側に倒れている) が、本来は CLEAR (audit 全 PASS の時) を返すべき。

### 発見経緯

L7-helix-recover-implplan v3 (commit 904c4f6) 実装後の Opus smoke test:
```
helix recover check 2>&1
  C2 工程逸脱: WARN (missing_count=1, エラー: 不明なオプション: --json
  使い方: helix doctor [check_recovery_plan_freshness] [--fix] [--cleanup-stale-locks] [--max-age-days N]) [agent_mandatory_audit]
```
C2 検出 source=agent_mandatory_audit で `helix doctor --json` を呼ぶが、helix doctor は `--json` を認識しない → WARN に倒される。recover の振る舞いとしては安全 (UNKNOWN ではなく WARN = 注意喚起) だが、doctor 側の --json 対応が筋。

### 修正範囲

最小修正:
- cli/helix-doctor に `--json` 引数 parser を追加
- JSON 出力 schema: `{"pass": N, "fail": N, "warn": N, "advisories": [{"category": "...", "name": "...", "status": "...", "detail": "..."}], "summary": "..."}`
- 既存 text 出力 (--json 不在時) は変更なし

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 1 | parent_design (L7-helix-recover) C2 検出 source 確認 + 現 helix-doctor 出力構造把握 | PM | ✅ done |
| 2 | JSON 出力 schema 設計 | PM | ✅ done (§2.A) |
| 3 | tl-advisor adversarial check 第 1 ラウンド | PM → TL | □ pending |
| 4 | SE 委譲: cli/helix-doctor 修正 + JSON 出力 + test | PM → SE | □ pending |
| 5 | bash -n / py_compile / pytest / bats 全 PASS | SE | □ pending |
| 6 | helix recover check で C2 が CLEAR (audit 全 PASS 時) を返すこと確認 | SE | □ pending |
| 7 | commit + push | PM | □ pending |

## §2 実装計画

### §2.A JSON 出力 schema

```json
{
  "timestamp": "2026-05-24T15:30:00+09:00",
  "pass": 22,
  "fail": 0,
  "warn": 149,
  "advisories": [
    {
      "category": "PLAN registry advisory",
      "name": "plan drift advisory",
      "status": "warning",
      "warnings_count": 54,
      "rows_count": 86,
      "detail": "PLAN-129:.claude/hooks/agent-stuck-recovery.sh (missing_artifact); ..."
    },
    {
      "category": "subagent + sprint 機械化",
      "name": "check_subagent_phase",
      "status": "warning",
      "detail": "1 mandatory subagent 不在 (current_phase=L4)"
    }
  ],
  "summary": "22 pass, 0 fail, 149 warn"
}
```

### §2.B cli/helix-doctor 引数 parser 拡張

既存 helix-doctor の引数 parser に `--json` フラグを追加:
- `--json` 指定時: 全 check 結果を集計して JSON を stdout に出力 (text 出力は stderr or 抑止)
- `--json` 不在時: 既存 text 出力 (変更なし)

互換性:
- 既存 `[check_recovery_plan_freshness] [--fix] [--cleanup-stale-locks] [--max-age-days N]` は維持
- `--json` を追加引数として共存

### §2.C 出力実装

helix-doctor の各 check (PLAN registry / process_layer / subagent + sprint / stale locks 等) の結果を構造化:
- 各 check function が pass / fail / warn count と advisory list を返す
- 統合 dict にまとめて json.dumps で出力

### §2.D テスト設計

unit test (test_doctor_json.py) 5 件:
- test_doctor_json_returns_valid_json: --json 出力が json.loads でパース可能
- test_doctor_json_schema_required_keys: timestamp / pass / fail / warn / advisories / summary の必須 key
- test_doctor_json_advisories_structure: 各 advisory に category / name / status / detail
- test_doctor_json_pass_count_matches_text: --json と text 出力の pass/fail/warn 数が一致
- test_doctor_json_does_not_affect_text_output: --json 不在時に既存 text 出力が変化しない

bats test (helix-doctor-json.bats) 3 件:
- helix doctor --json が valid JSON を出力する
- helix doctor (--json なし) が text 出力する (既存互換)
- helix recover check が C2 が CLEAR を返す (audit 全 PASS 時)

## §3 成果物

- cli/helix-doctor 修正 (~20-30 行追加、--json 引数 parser + 構造化出力)
- cli/lib/tests/test_doctor_json.py 新規 (5 unit test、~100 行)
- cli/tests/helix-doctor-json.bats 新規 (3 bats、~50 行)
- 副次: docs/commands/index.md に --json オプション追記 (1 行)

## §4 受入条件 / DoD

- [ ] bash -n cli/helix-doctor 構文 PASS
- [ ] python3 -m pytest cli/lib/tests/test_doctor_json.py -v 5 test 全 PASS
- [ ] bats cli/tests/helix-doctor-json.bats 3 ケース全 PASS
- [ ] helix doctor --json で valid JSON 出力 (json.loads PASS)
- [ ] helix doctor (--json なし) で既存 text 出力 (regression なし)
- [ ] helix recover check で C2 が CLEAR を返す (audit 全 PASS 時、現状は WARN)
- [ ] helix commands check PASS
- [ ] plan_validator warnings 0
- [ ] 既存 pytest 全回帰 PASS

## §5 関連 PLAN / docs

- parent: L7-helix-recover-implplan (C2 検出が --json を呼ぶ前提)
- 関連: cli/lib/recovery_engine.py (RecoveryEngine.check_conditions C2 ロジック)
- 関連: cli/helix-doctor 既存実装

## §6 後続 PLAN 候補

- helix doctor --json --filter <category> でカテゴリ別出力
- helix doctor --json --advisories-only で advisory のみ出力 (recover C2 用途特化)
- recover の C2 検出を helix doctor --json failure 時 UNKNOWN にする fallback 強化 (本 PLAN 完遂後でも残る安全網)
