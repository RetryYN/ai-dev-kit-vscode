---
plan_id: PLAN-117
title: PostToolUse PLAN.md drift 検出 hook
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-093-plan-drift-detection-curator.md   # from dependencies.parent
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
    slot_label: "SE — posttooluse-plan-drift-detect.sh 実装・helix doctor check_plan_drift 統合"
  - role: pmo-sonnet
    slot_label: "PMO — drift パターン設計確認・既存 hook 整合チェック"
generates:
  - artifact_type: hook
    path: .claude/hooks/posttooluse-plan-drift-detect.sh
  - artifact_type: python_module
    path: cli/lib/plan_drift_checker.py
  - artifact_type: test
    path: .claude/hooks/tests/test_plan_drift_detect_hook.bats
  - artifact_type: config
    path: .claude/settings.json
dependencies:
  requires:
    - PLAN-093
  blocks: []
  parent: PLAN-093
related_adr: []
related_docs:
  - docs/plans/PLAN-093-drift-detect-progress-trace.md
  - docs/plans/PLAN-109-skill-catalog-rebuild-hook.md
  - cli/lib/plan_validator.py
  - .claude/settings.json
acceptance_criteria:
  - "PLAN.md Edit / Write 後に drift check が bg 実行され .helix/cache/plan-drift/<plan-id>.json に書かれる"
  - "generates.path file 不在 / DoD 未完 completed / requires 未完 / ADR 不在 の drift を検出できる"
  - "helix doctor check_plan_drift が .helix/cache/plan-drift/ を集約して advisory WARN を出す"
  - "bash -n .claude/hooks/posttooluse-plan-drift-detect.sh PASS"
  - "bats test (6 case) 全 PASS"
  - "既存 PostToolUse hook と干渉しない"
---

# PLAN-117: PostToolUse PLAN.md drift 検出 hook

## L2 凍結 (ADR snapshot)

既存 PostToolUse hook framework (PLAN-089) と drift Curator (PLAN-093) の機械化拡張のため
ADR snapshot は不要。PostToolUse hook 機構は PLAN-087/089/090 で凍結済。

## 背景

PLAN-093 (drift Curator) は PLAN.md と実体の drift を検出する framework だが、
2026-05-23 時点では手動 `helix doctor` 実行に依存し、PLAN.md 変更直後の drift が即時可視化されない。
問題ケース: generates.path file 不在 / requires 未完なのに着手 / related_adr 削除後も参照 / DoD 未完 completed。
PostToolUse hook で PLAN.md 変更を自動検出し bg で機械チェックする。

## WebSearch 履歴 — skip

内部 hook 拡張のみ。外部ライブラリ新規依存なし。plan_validator.py の VALID_* / REQUIRED_FIELDS 流用。

## drift パターン定義 (5 種)

| ID | 説明 | 検出ロジック |
|---|---|---|
| D-GEN-001 | generates.path 不在 | `test -f <path>` |
| D-DOD-001 | completed + DoD `- [ ]` 残 | status: completed AND `## DoD` セクション内 `- [ ]` |
| D-REQ-001 | requires PLAN が未完 | requires PLAN の `status:` grep |
| D-ADR-001 | related_adr 不在 | `docs/adr/<id>.md` 存在チェック |
| D-FMT-001 | frontmatter 必須 field 欠如 | plan_validator.py REQUIRED_FIELDS 参照 |

drift 検出は **advisory WARN** のみ (fail-close 化は PLAN-093 Phase 4 に委ねる)。

## hook 設計

- **trigger**: PostToolUse / Edit|Write|MultiEdit / `docs/plans/PLAN-*.md` match
- **処理**: plan_id 抽出 → `nohup python3 cli/lib/plan_drift_checker.py "$plan_id" &` → exit 0
- **結果**: `{ plan_id, checked_at, drift_count, drifts:[{pattern,path,message}] }` を
  `.helix/cache/plan-drift/<plan-id>.json` に書き込み

## 実装計画

### Sprint .1: Python helper 実装 (Codex se、size S)

`cli/lib/plan_drift_checker.py`: yaml.safe_load で frontmatter 読み取り、5 drift パターン実装、結果 JSON 書き込み。
unit test `test_plan_drift_checker.py` 5 case。`python3 -m py_compile` + test 5 PASS が完了条件。

### Sprint .2: hook 実装 + settings.json 登録 (Codex se、size S)

`.claude/hooks/posttooluse-plan-drift-detect.sh` 新規。stdin jq 抽出 → PLAN-*.md match → bg 実行。
settings.json PostToolUse 節登録。既存 hook 干渉確認 ([[feedback_merge_settings_helix_hook_judge_bug]] 注記)。
`bash -n` PASS + settings.json 登録済が完了条件。

### Sprint .3: helix doctor 統合 + bats test (Codex se、size S)

`helix doctor check_plan_drift` で `.helix/cache/plan-drift/` 集約 WARN 表示。
`test_plan_drift_detect_hook.bats` 6 case (trigger / skip 2 種 / bg non-blocking / JSON 生成 / no-drift)。
bats 6 PASS + helix doctor WARN 表示確認が完了条件。

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/plan_drift_checker.py` PASS
- [ ] `bash -n .claude/hooks/posttooluse-plan-drift-detect.sh` PASS
- [ ] unit test 5 PASS + bats test 6 PASS
- [ ] 既存 PostToolUse hook smoke test 干渉なし
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] posttooluse-plan-drift-detect.sh 実装・`bash -n` PASS
- [ ] plan_drift_checker.py 5 drift パターン対応
- [ ] settings.json hook 登録済
- [ ] helix doctor check_plan_drift advisory WARN 表示
- [ ] unit test 5 + bats test 6 PASS
- [ ] helix doctor pass 数現行以上

## carry / 学び

- D-REQ-001 は直接 requires のみ (再帰は carry)
- D-DOD-001 は `## DoD` セクション限定 (実装計画 checkbox は対象外)
- _is_helix_hook bug 未修正なら PLAN-102 完了後に接続
- `.helix/cache/plan-drift/` は checker 初回実行時に `mkdir -p` 自動作成

## 関連 reference

- PLAN-093 (drift Curator 本体、parent)
- PLAN-089 (PostToolUse hook fail-close 設計)
- PLAN-109 (PostToolUse 同型 hook、format reference)
- [[feedback_merge_settings_helix_hook_judge_bug]]
