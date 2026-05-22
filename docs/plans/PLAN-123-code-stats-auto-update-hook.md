---
plan_id: PLAN-123
title: helix code stats coverage 自動 report hook (PostToolUse Python 変更検出)
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
    slot_label: "SE — posttooluse-code-stats-update.sh 実装・settings.json 登録・bats test 起草"
  - role: pmo-sonnet
    slot_label: "PMO — hook 設計 drift 確認・既存 hook 一覧との整合チェック"
generates:
  - artifact_type: hook
    path: .claude/hooks/posttooluse-code-stats-update.sh
  - artifact_type: config
    path: .claude/settings.json
  - artifact_type: test
    path: .claude/hooks/tests/test_code_stats_update_hook.bats
dependencies:
  requires:
    - PLAN-013
  blocks: []
  parent: null
related_adr: []
related_docs:
  - cli/lib/helix_code_catalog.py
  - cli/helix-code
  - SKILL_MAP.md §コードインデックス
  - docs/plans/PLAN-013-code-catalog-taxonomy.md
acceptance_criteria:
  - "cli/lib/*.py の Write / Edit / MultiEdit 後に helix code build が bg 実行される"
  - "debounce 60 秒により連続 Python Edit でも build は 1 回に集約される"
  - "bg 実行で main thread を block しない (PostToolUse hook timeout 影響なし)"
  - "既存 PostToolUse hook (posttooluse-skill-catalog-rebuild.sh 等) と干渉しない"
  - "bash -n .claude/hooks/posttooluse-code-stats-update.sh PASS"
  - "bats test (6 case) 全 PASS"
---

# PLAN-123: helix code stats coverage 自動 report hook (PostToolUse Python 変更検出)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 PostToolUse hook framework の拡張** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- PostToolUse hook 機構は PLAN-087 / PLAN-089 / PLAN-090 で凍結済
- settings.json hook 登録規約は既存 posttooluse-skill-catalog-rebuild.sh と同型
- debounce 設計は既存 hook 群で実証済のパターン (lock file + mtime 比較)

## 背景

PLAN-013 (code catalog taxonomy) で `helix code build` を**手動実行**する運用が前提。
Python file Edit のたびに手動実行しないと catalog が stale になり、以下が発生する:

1. `helix code find` が新規 symbol を返さない
2. G4 gate の coverage 判定 (`helix code stats --scope core5 --fail-under 80`) が旧数値を参照

PostToolUse hook で `cli/lib/*.py` 変更を自動検出し `helix code build` を bg 実行する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

PostToolUse hook 内部拡張、外部ライブラリ / 業界 standard への新規依存なし。
PLAN-087 / PLAN-089 / PLAN-109 の実証済 framework 範囲内。WebSearch **skip**。

## 設計方針

### 1. 検出条件 (hook trigger)

- **hook type**: PostToolUse / **matcher**: `Edit|Write|MultiEdit`
- **path filter**: `tool_input.file_path` が `cli/lib/*.py` または `.claude/hooks/*.sh` を含む場合のみ処理

### 2. debounce 設計 (60 秒)

連続 Python Edit で build が N 回実行される問題を防ぐ。
PLAN-109 (skill catalog rebuild 30 秒) より長い 60 秒に設定 (symbol parse を伴うため)。

```bash
DEBOUNCE_FILE="${TMPDIR:-/tmp}/.helix_code_stats_debounce"
DEBOUNCE_SEC=60
now=$(date +%s)
[ -f "$DEBOUNCE_FILE" ] && elapsed=$((now - $(cat "$DEBOUNCE_FILE"))) && [ "$elapsed" -lt "$DEBOUNCE_SEC" ] && exit 0
echo "$now" > "$DEBOUNCE_FILE"
```

### 3. bg 実行 + settings.json 登録

```bash
nohup helix code build >> /tmp/helix_code_stats_update.log 2>&1 &
```

settings.json 登録は PLAN-109 準拠。`_is_helix_hook()` 判定対応のため `.claude/hooks/` 配下に配置。

## 実装計画

### Sprint .1: hook スクリプト実装 (Codex se 委譲)

1. `.claude/hooks/posttooluse-code-stats-update.sh` 新規作成
   - stdin JSON `tool_input.file_path` を jq 抽出 → `cli/lib/*.py` / `.claude/hooks/*.sh` match 判定
   - debounce 60 秒チェック → `nohup helix code build &` bg 実行
   - jq 不在時 python3 fallback

完了条件: `bash -n posttooluse-code-stats-update.sh` PASS

### Sprint .2: settings.json 登録 + 干渉確認 (Codex se 委譲)

1. `.claude/settings.json` PostToolUse 節に hook 登録
2. `posttooluse-skill-catalog-rebuild.sh` / `posttooluse-helix-job-enqueue.sh` との同時発火確認
3. `_is_helix_hook()` 判定で HELIX hook と認識されることを確認

完了条件: `helix settings check` で hook 登録確認

### Sprint .3: bats test + 動作実証 (Codex se 委譲)

`.claude/hooks/tests/test_code_stats_update_hook.bats` 6 case:
- `cli/lib/helix_db.py` Write → build 起動
- `.claude/hooks/foo.sh` Write → build 起動
- `docs/foo.md` Write → skip
- `skills/foo/SKILL.md` Write → skip (PLAN-109 担当)
- 60 秒以内 2 回目 → skip
- bg 実行: hook exit が build 完了前に返る

完了条件: bats 6 case PASS + `helix code stats` 自動更新確認

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `bash -n .claude/hooks/posttooluse-code-stats-update.sh` PASS
- [ ] bats test 全 6 case PASS
- [ ] 既存 PostToolUse hook smoke test 全 PASS (干渉なし確認)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] commit message に `PLAN-123 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `.claude/hooks/posttooluse-code-stats-update.sh` 実装済
- [ ] `bash -n` PASS
- [ ] `.claude/settings.json` hook 登録済
- [ ] debounce (60 秒) が動作し連続 Python Edit でも build は 1 回に集約される
- [ ] bg 実行で PostToolUse hook が non-blocking であること確認済
- [ ] bats test 6 case PASS
- [ ] `helix code stats` が Python file Edit 後に自動更新されること確認
- [ ] helix doctor pass 数が現行以上 (regression なし)

## carry / 学び (起票時記録)

- **対象 path の拡張**: 将来的に `cli/helix-*` (bash CLI) も対象に追加を検討 (carry)
- **build 完了確認**: nohup bg 実行のため build 完了は保証されない。
  将来的には `.helix/cache/code_build_done` flag pattern への移行を検討 (carry)
- **`_is_helix_hook` bug**: [[feedback_merge_settings_helix_hook_judge_bug]] が未修正の場合、
  本 hook が `helix-init` 実行時に削除されるリスクあり。Sprint .2 で確認する

## 関連 reference

- [[feedback_merge_settings_helix_hook_judge_bug]] (settings.json 登録時の干渉リスク)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- PLAN-013 (code catalog taxonomy、本 PLAN の前提)
- PLAN-087 (Web 検索ガード framework)
- PLAN-089 (PostToolUse hook fail-close 設計)
- PLAN-109 (SKILL.md rebuild hook、同型の実装参考)
- SKILL_MAP.md §コードインデックス (helix code コマンド体系)
- cli/lib/helix_code_catalog.py (code build 実装の正本)
