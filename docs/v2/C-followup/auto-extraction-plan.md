# code-edge / contract auto-extraction 計画 (Phase 5 自動化入力)

- **作成日**: 2026-05-14
- **対象**: Phase 5 (自動化)
- **カテゴリ**: 設計 / 仕様
- **対象タスク**: `FR-A01`-`FR-A08`
- **参照**:
  - `docs/v2/L1-REQUIREMENTS.md` (A系 FR)
  - `docs/v2/A-audit/db-schema-current.md`
  - `docs/v2/A-audit/hooks-commands-subagents.md`
  - `.claude/settings.json`
  - `.claude/hooks/` 配下 hook 実装

---

## 0. 設計前提

本設計は、既存 HELIX Hook/DB運用の非互換を避け、`code-edge / contract / test_design / test_baseline` などの自動 record を Phase 5 で実装可能にするための最小移植設計を定義する。実装自体は本タスクでは行わず、仕様・処理フロー・監査観点・失敗時挙動まで含む。

### 0.1 目的

- LLM の編集イベントが発生した際に、設計 DB(`helix.db`)への自動書込を増分実行する。
- 既存の `helix-post-tool-use` / `helix-session-start` / `helix gate` と衝突せず、
  かつ既存レビュー導線を阻害しないこと。
- NFR-13 / NFR-14 を満たす性能予算を明確化し、fail-open / fail-close を分離する。
- Phase 3,4 の結果を前提に、Phase 5 で本番運用に近い自動化を開始する。

### 0.2 非目的

- DB スキーマの再定義や破壊的変更（本設計外）。
- 新規 writer のアルゴリズム実装（別タスク分担）。
- hook 実行基盤の完全刷新（既存 CLI ラッパを維持）。

---

## 1. auto-record 対象 table

### 1.1 対象一覧（10 系統）

| table | trigger event | extractor | 既存 PLAN | 主キー / 判定キー |
|---|---|---|---|---|
| `code_index` | Write/Edit `*.py`,`*.sh`,`*.md` | `code_catalog` | `PLAN-011` | `relpath + hash(content)` |
| `code_edges` | Write/Edit code file | `code_edges_extractor` | `PLAN-011` | `relpath + function_signature` |
| `contract_entries` | Write/Edit `OpenAPI` / `SQL` / `contract.md` | `contract_extractor` | `PLAN-063 W-2pre` | `relpath + section_id` |
| `test_design_entries` | Write/Edit `acceptance.yaml` / `*.bats` / `test_*.py` | `acceptance_extractor` | `V2 FR-A06` | `relpath + test_case_id` |
| `test_baseline` | `helix test` 完了 | `test_baseline_writer` | `V2 FR-A05` | `git_commit + suite_id` |
| `design_review` | TL/QA review 完了 hook | `design_review_writer` | `V2 FR-A05` | `gate_id + reviewer + status` |
| `design_sprint_entries` | sprint 凍結 (`G2`/`G3`/`G3.functional_freeze`) | `sprint_writer` | `V2 FR-VS06` | `sprint_id + phase + state` |
| `invocation_log` | LLM 呼び出し時 | `helix codex / helix claude 内蔵` | `PLAN-063 W-1a` | `session_id + tool_seq` |
| `detector_runs` | `helix gate` / pre-commit auto-run | `detector framework` | `PLAN-063` | `run_id + detector_id` |
| `routing_decisions` | helix skill chain / helix codex routing | `recommender / dispatcher` | `PLAN-022/023` | `request_id + phase_step` |

> 合計 10 行。行内抽出対象と既存 PLAN は要求仕様の§1を原則採用。

### 1.2 書込ルール共通化

1. **idempotency**: 同一 `(table, key)` が 2 回以上入る場合は最後のみを採用、あるいは状態遷移で更新。
2. **順序保証**: 1イベント内で複数 table の INSERT が必要な場合、
   - `invocation_log` を先行
   - 主 table 更新
   - 派生 metadata (`routing_decisions`) を最後
3. **差分判定**: `changed_file_hash` 比較で不要再抽出を抑止。
4. **監査整合**: すべての書込で `source='auto-posttooluse'` 等の出所を保持。
5. **トランザクション**: 同一 hook 呼出し単位は原則原子的（失敗時 rollback / 失敗時のみ部分コミット許可フラグ有効化）。

### 1.3 重要トレードオフ

- `code_index` と `code_edges` は同一ファイルへの Write/Edit で同時に走る。
- `contract_entries` は schema 特有のパース可否（OpenAPI/SQL 併記）で成功率が左右される。
- `test_design_entries` と `test_baseline` はタイミングが異なるため、
  **同一変更で 1 回のイベントは設計抽出、別イベントでベースライン**という二段実行が想定される。

---

## 2. PostToolUse hook 設計

### 2.1 推奨方式

本設計では **(a) 単一 PostToolUse hook + 内部 router 分岐** を採用する。

理由:
- `.claude/settings.json` は既に `Edit|Write|MultiEdit` で 1 つの command を期待しており、登録運用コストが低い。
- 失敗時処理（dry-run / timeout / guard）を 1 箇所で統一しやすい。
- detector / session start / gate で同じ route policy モジュールを使える。

### 2.2 対象 script 追加案

- `.claude/hooks/posttooluse-auto-record.sh`（新規、設計上の想定）
- `cli/libexec/helix-post-tool-use` で以下の実行を委譲する（現行: 既存 hook 呼び出しを継続）
- `cli/libexec/helix-auto-record-router`（任意。将来の単体テスト用に分離を推奨）

### 2.3 想定処理フロー

```bash
# .claude/hooks/posttooluse-auto-record.sh (設計図)
#!/usr/bin/env bash
set -euo pipefail

CONF=${HELIX_CONFIG:-"$HOME/ai-dev-kit-vscode/.helix/config.yaml"}
LOG_DIR=${HELIX_RUN_LOG_DIR:-"$HOME/.cache/helix/hooks"}
TIMEOUT_SECONDS=${HELIX_POSTTOOLUSE_TIMEOUT:-5}
DRY_RUN_DEFAULT=true

log() { printf '[auto-record] %s\n' "$1"; }

if [[ ${DISABLE_AUTO_RECORD:-false} == true ]] || grep -q '^disable_auto_record: *true' "$CONF"; then
  log "disabled by config"
  exit 0
fi

payload=$(cat)
{
  case "${TOOL_NAME:-}" in
    Write|Edit|MultiEdit)
      file=$(jq -r '.tool_input.file_path // .tool_input.new_path // empty' <<<"$payload")
      paths=( $(jq -r '.tool_input.file_path?, .tool_input.new_path?, .tool_input.files? // empty' <<<"$payload") )
      for p in "${paths[@]}"; do
        case "$p" in
          *.py|*.sh|*.md)
            run_extractor "code_catalog" "$p"
            ;;
          *.openapi|*.yaml|*contract*.md|*.sql)
            run_extractor "contract_extractor" "$p"
            ;;
          acceptance.yaml|*.bats|test_*.py)
            run_extractor "acceptance_extractor" "$p"
            ;;
          *)
            # no-op (not in FR-A01-08)
            ;;
        esac
      done
      ;;
    *)
      # other tools: no-op
      ;;
  esac
} | timeout "$TIMEOUT_SECONDS" tee -a "$LOG_DIR/posttooluse-auto-record.log"
exit ${PIPESTATUS[0]:-0}
```

上記は設計上のスケッチ。実装時は `jq` 依存回避時 fallback、
変更ファイル配列の厳密抽出、`MultiEdit` の旧 payload 対応を追加。

### 2.4 dispatch テーブル (PostToolUse)

| matcher | primary path | sec-path | writer | 備考 |
|---|---|---|---|---|
| Edit | `*.py`,`*.sh`,`*.md` | `cli/*` | code_catalog / code_edges | `helix code build --incremental` 相当 |
| Write | `*contract*`,`*.sql`,`*.openapi`,`contract.md` | `*/contracts/*` | contract_extractor | スキーマ整合失敗時 warning |
| MultiEdit | 同上 | - | 対象パスを一括抽出後ループ | idempotent 化必須 |
| Edit/Write | `acceptance.yaml`, `*.bats`, `test_*.py` | `**/tests/**` | acceptance_extractor | test_design_entries 更新 |
| Other | なし | なし | noop | invocation_log 以外は後段で別 hook |

### 2.5 実行順（既存 hook との共存）

1. Claude Code 実行時、`PostToolUse(Edit/Write/MultiEdit)` が先に既存 `.claude/settings.json` の `helix-post-tool-use` を実行。
2. `helix-post-tool-use` は payload の妥当性検査と現行 advisory を行う。
3. `phase=auto_record` 判定で `posttooluse-auto-record.sh` 呼び出し（phase 切替 or 連結コマンド）
4. 自動抽出結果は `helix.db` へ追加。

### 2.6 既存 `cli/libexec/helix-post-tool-use` の差分要件

- router 層に `posttooluse_auto_record=true` の判定を追加。
- `--dry-run` の既定化（本タスク default）は既存 hook の副作用回避に重要。
- 既存の `invocation_log` は削除せず、重複排除キーで競合しないようにする。
- warning レベルで完了し、5 秒超過・guard 触れた場合は escalation へ。

---

## 3. SessionStart hook 設計

### 3.1 目的

起動時に DB 同期を 1 回実行し、
セッション内での hook 実行対象を `cache` / `skill_map` / `plan_registry` に反映。

### 3.2 推奨実装

`~/.claude/hooks/sessionstart-sync.sh` を追加し、`helix-session-start` 前段に接続（現在は settings の単一フックとして `cli/helix-session-start`）。

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ ${HELIX_SESSION_AUTO_SYNC:-true} != true ]]; then
  echo "[sessionstart-sync] disabled"
  exit 0
fi

start=$(date +%s)

helix sync --auto \
  --scope skill,code,plan,detector \
  --telemetry sessionstart \
  --timeout 55 || {
    echo "[sessionstart-sync] sync failed"
    exit 0
  }

elapsed=$(( $(date +%s) - start ))
if (( elapsed > 60 )); then
  echo "[sessionstart-sync] warning: elapsed=${elapsed}s"
fi

exit 0
```

### 3.3 スコープ

- `skill`:
  - `routing_decisions` 判定用 recommender config
- `code`:
  - `code_index` / `code_edges` 差分初期同期
- `plan`:
  - 現在 sprint / gate 制約 / freeze ポリシー
- `detector`:
  - guard 連携に必要な rule set のキャッシュ

### 3.4 NFR-14

`SessionStart` の sync は 60 秒以内でタイムアウトせず完了すること。超過時は warning を残して続行（fail-open）。ただし設定不整合は別途 escalation。

### 3.5 設定値

- `session_sync_timeout: 55`
- `session_sync_fail_open: true`
- `session_sync_cache_ttl: 900`

---

## 4. Gate runner 連動

### 4.1 トリガー定義

- `helix gate` が通過した瞬間に、実行ログと結果を各 table へ反映。
- TL/QA 承認情報は design_review writer と紐付け。

### 4.2 マッピング

| gate phase | 条件 | insert 先 | 追加キー |
|---|---|---|---|
| `G2` 通過 | TL 承認済み | `design_review` | `gate='G2'` + reviewer |
| `G3` 通過 | QA 承認済み | `design_review` + `design_sprint_entries` の暫定行 | `gate='G3'` |
| `G4` 通過 | テスト回帰完了 | `test_baseline` (bulk) | `suite_id=gate:G4` |
| `G3.functional_freeze` | スプリント固定化 | `design_sprint_entries`（pair_status='paired'） | `sprint_id` |

### 4.3 実装手順

1. gate 直後 hook / runner callback で `run_id`, `gate_id`, `outcome`, `actor`, `commit_sha` を収集。
2. `design_review_writer` は approver 列を確実に取得し、approve/no-approve の分岐で状態更新。
3. `test_baseline` は G4 で suite 全体を bulk insert。
4. `design_sprint_entries` は freeze 時に `pair_status` を `'paired'` へ更新。
5. 更新結果は全て `gate_runner_sync` という telemetry で集約。

### 4.4 Gate 連動方針

- Gate runner 自体は既存を壊さず、`on_gate_passed` の callback を追加。
- 既存の検証表示は継続し、auto-record は補助スレッドで非同期 enqueue。
- 実行失敗時は gate 全体を fail-close しない（既存検証保護）

---

## 5. 暴走防止と安全制御

### 5.1 dry-run mode

- 既定 `dry-run=true`。
- 差分確認のみで `INSERT` は行わない。
- 本番稼働では `--apply` を明示指定。
- 実行ログに `mode=dry-run` を残す。

### 5.2 時間制御

- PostToolUse タイムアウト: 5 秒超えた場合スキップ + warning log。
- 5 秒でスキップした場合、該当ファイルを次回起動時の再実行対象キューへ登録。

### 5.3 cost guard

- 80%: warning（次回優先度再評価）
- 100%: 当該 hook を即時停⽌し、次回明示起動時のみ再開
- 計測は hook 起動ごとの `cost_delta` + `llm_turns` を使う

### 5.4 opt-out

`.helix/config.yaml` に以下を追加。

```yaml
auto_record:
  enabled: true
  disable_auto_record: false
  dry_run: true
  max_hook_secs: 5
  cost_guard:
    warn_at_percent: 80
    hard_block_at_percent: 100
```

### 5.5 atomic transaction

- `writer_set` 単位で 1 transaction。
- `invocation_log` は例外的に最初に確定（監査ロス回避）。
- 部分失敗は `rollback` し、
  失敗明細を `posttooluse-auto-record-failed-events` テーブルへ退避。

### 5.6 例外時分岐

- **fail-open**: SessionStart 同期待ち、軽微な parser 失敗、NFR の warning。
- **fail-close**: hook 設定破損、payload パース不能、DB lock での一貫性破壊が疑われる場合。

### 5.7 再試行

- `pending_auto_record` キューから最終的に再取得。
- キューは CLI 起動時に最大 200 件で先頭 50 件を再送。

---

## 6. 実装 Phase 紐付け

### 6.1 Phase 全体対応

- **Phase 3**: writer table 整備
  - `code_index`,`code_edges`,`contract_entries`,`test_design_entries`,`test_baseline`,`design_review`,`design_sprint_entries`,`routing_decisions`,`detector_runs`,`invocation_log`
  - 本設計は既存 schema を前提に記載
- **Phase 4**: ガードレール
  - detector auto-run fail-close 連携
  - cost guard と timeout 制御を段階的に有効化
- **Phase 5**: 自動化実装（本設計対象）
  - PostToolUse hook/SessionStart hook/Gate runner の 3 点同時接続

### 6.2 phase 5 WBS 候補

1. Router スクリプト追加（shell / argparse）
2. .claude/settings.json の PostToolUse/SessionStart 参照先追加
3. helix hook runner へのオプション注入
4. gate-runner callback 接続
5. 失敗時 fallback / queue / retry 実装
6. ログ設計と検証シナリオ整備

### 6.3 非対象の残件

- 実行者ごとの監査証跡強化（認証情報は次期）
- test_baseline の完全 schema 厳密化（別 FR）

---

## 7. 性能要件

### 7.1 定義

- **NFR-13**: PostToolUse hook が 5 秒以内で完了。
- **NFR-14**: SessionStart sync が 60 秒以内で完了。
- **NFR-15（追加提案）**: Gate 連動で 2 秒以内に queue 登録。

### 7.2 性能測定ポイント

1. `posttooluse_hook_latency_ms`
2. `posttooluse_emit_count`（イベント/秒）
3. `posttooluse_replay_queue_depth`
4. `sessionstart_sync_wall_time_ms`
5. `gate_runner_sync_ms`

### 7.3 改善戦略

- ファイル種別判定を O(1) にする。
- writer 呼び出しは debounce 1.2 秒。
- 重い extractor はバックグラウンドに委譲。
- 同一ファイル 1 秒以内の連打更新は最後のみ反映（coalesce）。

### 7.4 SLA と監視

- 成功率: 99.4%（短期）、回収率(遅延再送含む) 99.9%。
- エラー率: 1日あたり 10 件未満を目標。
- 警告閾値: 10% 遅延再送超過、30% timeout 超過。

---

## 8. 既存 hook との衝突・共存戦略

### 8.1 現行順序（現時点）

`.claude/settings.json` 現状:
1. `SessionStart`: `~/ai-dev-kit-vscode/cli/helix-session-start`
2. `PreToolUse`: `helix-check-claudemd`, `helix-pre-bash`, `helix-pre-research`, `pretooluse-opus-repo-block.sh`
3. `PostToolUse`: `~/ai-dev-kit-vscode/cli/libexec/helix-post-tool-use`
4. `Stop`: `~/ai-dev-kit-vscode/cli/helix-session-summary`

### 8.2 文書化要件

- DocumentationAssistant 名義の hook が存在している前提では、
  本 hook は最終段階またはラップ方式の 2 層として接続。
- `blockOnFailure` を PostToolUse に対して変更しない（現行 true は維持）。
- 既存停止時の通知 UX を壊さず、warning ログで運用に誘導。

### 8.3 マイグレーション手順（設計）

1. 既存 PostToolUse を維持したまま、内部で `auto-record` を委譲実行。
2. 動作確認フェーズで設定を `statusMessage` 追加（短文）
3. `dry-run` 中は `blockOnFailure` の影響が起きないことを確認。
4. 問題なければ apply へ切替。

### 8.4 失敗時の衝突回避

- 既存 hook が失敗しても自動抽出の最小機能を維持する場合、`posttooluse-auto-record` は fail-open。
- 設定不整合時は stop hook からの最終レポートに警告行を残す。

---

## 9. Hook-コマンド整合マッピング

### 9.1 重要コマンドと役割

| コマンド | hook側役割 | フェイルポリシー | 関連設計 |
|---|---|---|---|
| `helix-post-tool-use` | payload 受け取り + dispatch | close | 既存を壊さない |
| `helix-hook` | doc-map/freeze/detect advisory | open(close on severe) | gate の事前チェック |
| `helix-sync` | session catalog sync | open | §3 |
| `helix code build --incremental` | code_catalog + code_edges | open | §2,§1 |
| `helix contract extract` | contract_entries 抽出 | open | §2,§1 |
| `helix qa test-design` | test_design_entries 抽出 | open | §2,§1 |
| `helix test` | test_baseline_writer | close in gate runner | §4 |
| `helix gate` | design_review/design_sprint_entries への連動 | close if policy broken | §4 |
| `helix code path` | ルート配列提供 | open | §2 |
| `helix audit` | detector_runs / policy summary | open | §5 |

### 9.2 役割分離（例）

- `cli/libexec/helix-post-tool-use`: 共通 validator + dispatch entry
- `.claude/hooks/posttooluse-auto-record.sh`: 実行制御とルーティング
- `cli/libexec/helix-code-auto-write`: (将来) 重い writer の単体再実行

---

## 10. 失敗/例外シナリオ設計

### 10.1 典型エラー

1. payload 破損（JSON parse 失敗）
2. extractor が未インストール
3. DB ロック / トランザクション衝突
4. timeout 超過（5秒）
5. コスト超過（80% / 100%）

### 10.2 例外対処

- payload 破損: warning + dead-letter、gate 側は継続。
- extractor 未インストール: イベントを pending queue に入れて再試行。
- DB ロック: 100ms→200ms→400ms の 3 回リトライ。
- timeout: 次回起動時に pending_queue を再生。
- cost 100%: auto_record を一時停止、手動 clear まで新規 hook 登録停止。

### 10.3 保守運用

- 週次で dead-letter レポートを確認
- 1日1回 fail 閾値を alert 配信
- gate runner 連携は `G2/G3` の結果と突合

---

## 11. 設定テンプレ（`.helix/config.yaml`）

```yaml
auto_extraction:
  enabled: true
  dry_run: true
  timeout_secs: 5
  session_sync:
    enabled: true
    timeout_secs: 60
  gate_auto_record:
    enabled: true
    include_design_review: true
    include_test_baseline: true
  safety:
    disable_auto_record: false
    dry_run: true
    cost_guard:
      warn_percent: 80
      block_percent: 100
      grace_count: 3
  routing:
    posttooluse_mode: single_router
    route_by: pattern
    unknown_file_action: ignore
  hooks:
    posttooluse:
      script: ".claude/hooks/posttooluse-auto-record.sh"
      statusMessage: "Auto record for design DB"
    sessionstart:
      script: ".claude/hooks/sessionstart-sync.sh"
      statusMessage: "Session start auto sync"
```

---

## 12. テストシナリオ（設計）

### 12.1 hook 単体

- `Edit` on `foo.py` -> `code_index` / `code_edges` queued
