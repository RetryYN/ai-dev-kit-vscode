---
plan_id: PLAN-109
title: helix skill catalog rebuild 自動化 hook (PostToolUse SKILL.md 検出)
status: completed
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
kind: impl
drive: be
layer: L4
size: S
created_at: 2026-05-23
completed_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: se
    slot_label: "SE — posttooluse-skill-catalog-rebuild.sh 実装・settings.json 登録・bats test 起草"
  - role: pmo-sonnet
    slot_label: "PMO — hook 設計 drift 確認・既存 hook 一覧との整合チェック"
generates:
  - artifact_type: hook
    path: .claude/hooks/posttooluse-skill-catalog-rebuild.sh
  - artifact_type: config
    path: .claude/settings.json
  - artifact_type: test
    path: .claude/hooks/tests/test_skill_catalog_rebuild_hook.bats
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_docs:
  - .claude/settings.json
  - cli/helix-skill
  - cli/lib/skill_catalog.py
  - SKILL_MAP.md §自動推挙システム
acceptance_criteria:
  - "skills/*/*/SKILL.md の Write / Edit / MultiEdit 後に helix skill catalog rebuild が自動実行される"
  - ".helix/cache/recommendations/ の全 entry が rebuild 後に invalidate される"
  - "30 秒 debounce により連続 SKILL.md Write でも rebuild は 1 回に集約される"
  - "bg 実行で main thread を block しない (PostToolUse hook timeout 影響なし)"
  - "既存 PostToolUse hook (posttooluse-helix-job-enqueue.sh 等) と干渉しない"
  - "bash -n .claude/hooks/posttooluse-skill-catalog-rebuild.sh PASS"
  - "bats test (6 case) 全 PASS"
---

# PLAN-109: helix skill catalog rebuild 自動化 hook (PostToolUse SKILL.md 検出)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 PostToolUse hook framework の拡張** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- PostToolUse hook 機構は PLAN-087 / PLAN-089 / PLAN-090 で凍結済
- settings.json hook 登録規約は既存 posttooluse-helix-job-enqueue.sh と同型
- debounce 設計は既存 hook 群で実証済のパターン (lock file + mtime 比較)

## 背景

本 session (2026-05-23) で 4 skill を統合:

- `skills/writing/god-writing/` (SKILL.md 313 行 + 97 references)
- `skills/advanced/doc-system-architect/` (SKILL.md)
- `skills/advanced/requirements-deriver/` (SKILL.md)
- `skills/agent-skills/gpt-image/` (SKILL.md)

各統合後に `helix skill catalog rebuild` を**手動実行**する必要があり、
手順を忘れると recommender に新 skill が反映されないまま稼働し続ける。

具体的な問題:

1. `helix skill search "..."` が新 skill を返さない (catalog stale)
2. `.helix/cache/recommendations/` が旧 catalog 基準でキャッシュされたまま (1 時間 TTL)
3. 複数 SKILL.md を連続 Edit した場合、rebuild を何度も手動実行する非効率

PostToolUse hook で SKILL.md 変更を自動検出して rebuild を実行する framework を導入する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **Claude Code PostToolUse hook の内部拡張** であり、外部ライブラリ /
業界 standard への新規依存なし。WebSearch **skip**。

skip 理由:
- PostToolUse hook 機構は本 session 内で posttooluse-helix-job-enqueue.sh 等が
  既稼働であり、実証済の framework 範囲内
- `helix skill catalog rebuild` は HELIX 内部 CLI コマンドで外部仕様非依存
- debounce の実装は lock file + mtime 比較 (POSIX sh 標準機能のみ)

## 設計方針

### 1. 検出条件 (hook trigger)

- **hook type**: PostToolUse
- **matcher**: `Edit|Write|MultiEdit`
- **path-prefix filter**: `skills/` を含むパスのみ処理
- **SKILL.md filter**: `tool_input` の対象 file path が `*/SKILL.md` であること

PostToolUse hook stdin JSON (Claude Code 公式仕様):

```json
{
  "session_id": "...",
  "tool_name": "Write|Edit|MultiEdit",
  "tool_input": { "file_path": "skills/writing/god-writing/SKILL.md", ... },
  "tool_response": { "output": "..." }
}
```

### 2. debounce 設計 (30 秒)

連続 SKILL.md Write (複数 skill 統合時) で rebuild が N 回実行される問題を防ぐ。

```bash
DEBOUNCE_FILE="${TMPDIR:-/tmp}/.helix_skill_rebuild_debounce"
DEBOUNCE_SEC=30

now=$(date +%s)
if [ -f "$DEBOUNCE_FILE" ]; then
    last_run=$(cat "$DEBOUNCE_FILE")
    elapsed=$((now - last_run))
    if [ "$elapsed" -lt "$DEBOUNCE_SEC" ]; then
        exit 0  # debounce 中: skip
    fi
fi
echo "$now" > "$DEBOUNCE_FILE"
```

### 3. cache invalidate

rebuild 前に `.helix/cache/recommendations/` 配下の全 JSON を削除する。
TTL 1 時間を待たず即時 invalidate することで、rebuild 後の検索で旧 cache が
ヒットしない状態を保証する。

```bash
HELIX_HOME="${HELIX_HOME:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME/.helix")}"
CACHE_DIR="${HELIX_HOME}/.helix/cache/recommendations"
if [ -d "$CACHE_DIR" ]; then
    rm -f "${CACHE_DIR}"/*.json 2>/dev/null
fi
```

### 4. bg 実行

`helix skill catalog rebuild` は catalog.json 再生成を伴い 3-10 秒程度の処理。
PostToolUse hook は同期実行されるため、rebuild 完了まで hook が block すると
次の tool call が遅延する。bg 実行で非 block 化する。

```bash
nohup helix skill catalog rebuild >> /tmp/helix_skill_catalog_rebuild.log 2>&1 &
```

ログは `/tmp/helix_skill_catalog_rebuild.log` に append。エラーは log で確認可能。

### 5. settings.json 登録

既存の PostToolUse hook 登録パターンに準拠:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/posttooluse-skill-catalog-rebuild.sh"
          }
        ]
      }
    ]
  }
}
```

注意: matcher は既存 PostToolUse hook と共有する形式にするか、
または独立した hook entry として追加する。既存との干渉は Sprint .2 で確認する。

## 実装計画

### Sprint .1: hook スクリプト実装 (Codex se 委譲、size S)

実施内容:

1. `.claude/hooks/posttooluse-skill-catalog-rebuild.sh` 新規作成
   - stdin JSON の `tool_input.file_path` を jq で抽出
   - `*/SKILL.md` パターン match 判定
   - debounce チェック (30 秒)
   - cache invalidate (`.helix/cache/recommendations/*.json` 削除)
   - `helix skill catalog rebuild` を nohup bg 実行
   - `bash -n` PASS を mandatory in sprint とする

2. hook 処理フロー:

```
stdin JSON →
  jq .tool_input.file_path →
    SKILL.md match?
      No → exit 0
      Yes → debounce check?
        debounce active → exit 0
        else → update debounce file
               rm cache JSONs
               nohup helix skill catalog rebuild &
               exit 0
```

Sprint .1 完了条件:

- `bash -n .claude/hooks/posttooluse-skill-catalog-rebuild.sh` PASS
- スクリプトが `jq` 依存で動作すること、または `jq` 不在時の fallback が実装済

### Sprint .2: settings.json 登録 + 既存 hook 干渉確認 (Codex se 委譲、size S)

実施内容:

1. `.claude/settings.json` の PostToolUse 節に hook 登録追加
2. 既存 hook との干渉確認:
   - `posttooluse-helix-job-enqueue.sh` との matcher 重複確認
   - 同一 SKILL.md Write に対して両 hook が発火した場合の挙動確認
3. `pretooluse-agent-guard.sh` 等の PreToolUse hook に影響しないことを確認

Sprint .2 完了条件:

- settings.json hook 登録が merge_settings.py の `_is_helix_hook()` 判定で
  HELIX hook として認識されること (PLAN-102 carry の `_is_helix_hook` bug 修正前なら注記)
- `helix settings check` (または手動確認) で hook 登録を確認

### Sprint .3: bats test + 動作実証 (Codex se 委譲、size S)

実施内容:

1. `.claude/hooks/tests/test_skill_catalog_rebuild_hook.bats` 新規作成 (6 case):
   - `test_triggers_on_skill_md_write`: `skills/foo/SKILL.md` Write で rebuild 起動
   - `test_skips_non_skill_md`: `skills/foo/README.md` Write は rebuild skip
   - `test_skips_outside_skills_dir`: `docs/foo.md` Write は skip
   - `test_debounce_skips_within_30s`: 30 秒以内の 2 回目呼び出しは skip
   - `test_cache_invalidated_on_rebuild`: rebuild 前に cache JSONs が削除される
   - `test_bg_execution_non_blocking`: hook の exit が rebuild 完了前に返る

2. 本 session 統合済 4 skill での動作実証:
   - 4 skill のうち 1 つを手動 Edit → PostToolUse hook 発火 → `helix skill list` で反映確認

Sprint .3 完了条件:

- bats test 全 6 case PASS
- `helix skill search "ライティング"` が god-writing を返すこと確認
- `helix skill search "ドキュメント設計"` が doc-system-architect を返すこと確認

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `bash -n .claude/hooks/posttooluse-skill-catalog-rebuild.sh` PASS
- [ ] bats test 全 6 case PASS (`.claude/hooks/tests/test_skill_catalog_rebuild_hook.bats`)
- [ ] 既存 PostToolUse hook smoke test 全 PASS (干渉なし確認)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] commit message に `PLAN-109 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `.claude/hooks/posttooluse-skill-catalog-rebuild.sh` 実装済
- [ ] `bash -n` PASS
- [ ] `.claude/settings.json` hook 登録済
- [ ] debounce (30 秒) が動作し連続 Write で rebuild は 1 回に集約される
- [ ] `.helix/cache/recommendations/` が rebuild 前に invalidate される
- [ ] bg 実行で PostToolUse hook が non-blocking であること確認済
- [ ] bats test 6 case PASS
- [ ] 本 session 4 新規 skill が `helix skill search` で返ること確認
- [ ] helix doctor pass 数が現行以上 (regression なし)

## carry / 学び (起票時記録)

- **jq 依存**: `.claude/hooks/` の多くが jq を使用しており環境依存 low だが、
  jq 不在環境のために grep / python fallback を用意するか Sprint .1 で判断
- **debounce file の tmp path**: `/tmp/` は OS 再起動でクリアされる。
  セッション開始直後の SKILL.md Write で必ず rebuild が走ることは期待動作
- **bg プロセスの完了確認**: nohup bg 実行のため rebuild 完了は保証されない。
  次の `helix skill search` 呼び出し時に rebuild が完了していない可能性がある。
  将来的には rebuild 完了後に `.helix/cache/rebuild_done` flag を置く pattern への
  移行を検討 (carry として記録)
- **merge_settings.py の `_is_helix_hook` bug**: PLAN-102 carry の `_is_helix_hook()`
  判定 bug が未修正の場合、本 hook が `helix-init / migrate.py` 実行時に
  削除されるリスクあり。Sprint .2 で確認し、問題があれば PLAN-102 修正後に本 PLAN を
  着手するよう依存追加する

## 関連 reference

- [[feedback_merge_settings_helix_hook_judge_bug]] (settings.json 登録時の干渉リスク)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否判定、本 PLAN は不要と確認)
- SKILL_MAP.md §自動推挙システム (skill catalog の仕組みと rebuild 手順)
- cli/lib/skill_catalog.py (catalog 生成実装)
- cli/helix-skill (rebuild コマンドの dispatch)
- PLAN-087 (Web 検索ガード framework)
- PLAN-089 (PostToolUse hook fail-close 設計)
