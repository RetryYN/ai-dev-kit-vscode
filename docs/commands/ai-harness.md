# Codex / Claude Code 管理 harness

HELIX は Codex と Claude Code を直接 API 統合として扱わず、契約プラン + ローカル CLI / hook を `plan` / `task` / `role` / `handover` で管理する。

## 指示ファイル

| 対象 | 正本 | 役割 |
|---|---|---|
| Claude Code | `CLAUDE.md` | project context、技術スタック、共通 HELIX workflow |
| Claude runtime | `.claude/CLAUDE.md` | Claude Code hook / command / orchestration policy |
| Codex CLI | `AGENTS.md` | Codex TL mode、handover、検証、編集ルール |
| 個人差分 | `CLAUDE.local.md` / `AGENTS.override.md` | Git 追跡しない個人設定 |

## 役割分担

| 領域 | コマンド | 役割 |
|---|---|---|
| Codex 実行 | `helix codex` | role 設定に基づいて Codex CLI へタスク委譲 |
| Claude Code 委譲 | `helix claude` | Claude Code 用 prompt / task-file を生成 |
| チーム実行 | `helix team` | Codex は実行、Claude は `helix claude` prompt 生成で委譲 |
| レビュー | `helix review` | Codex による差分レビュー |
| スキル | `helix skill` | HELIX skill の検索・参照 |
| 予算・難度 | `helix budget` | Claude/Codex の消費状況とモデル推奨 |
| Harness 監視 | `helix harness` | active slot、harness warning、DB feedback-loop candidate の確認 |
| Hook | `helix hook` / `helix check-claudemd` / `cli/libexec/helix-post-tool-use` | Claude Code tool hook |
| Context guard | `helix context check` / `helix context bundle` | AGENTS / CLAUDE / hook / memory の強制導線を検査し、context budget と短い注入 context を生成 |
| セッション | `helix session-start` / `helix session-summary` | Claude Code session hook |
| 引継ぎ | `helix handover` | Opus / Codex のファイル経由 handover |

## 基本導線

```bash
# 1) 計画を凍結
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001

# 2) Codex に実装委譲
helix codex --role se --task "PLAN-001 の L7 実装"

# 3) Claude Code 用 prompt を生成
helix claude --role pg --plan-id PLAN-001 --task "PLAN-001 の通常実装を継続" --dry-run

# 4) 差分レビュー
helix review --uncommitted
```

Codex 側は `helix codex` 経由を原則にする。素の `codex exec` は `Codex Mandatory Discipline` の強制注入と plan-only guard が効かないため、PATH 上の `cli/codex` shim でブロックする。Claude 側も素の `claude` 直叩きでは role / plan / handover 文脈が注入されないため、`cli/claude` shim で `helix claude --dry-run` へ寄せる。

```bash
# 計画だけ。read-only + no-full-auto が強制される
helix codex --role tl --task "実装順を整理" --plan-only

# 承認済み実装。WBS 文脈を注入する
helix codex --role se \
  --task "PLAN-001 / WBS-003 の最小実装" \
  --approved \
  --plan-id PLAN-001 \
  --wbs-id WBS-003 \
  --l4-sprint .2 \
  --reference-doc docs/design/L3-schedule-wbs.md \
  --acceptance "主要 happy path が通る"

# 強制運用: write 実行には --approved が必須
HELIX_CODEX_REQUIRE_APPROVED=1 helix codex --role se --task "実装" --approved

# 承認証跡も必須化
mkdir -p .helix/approvals
printf 'approved by user\n' > .helix/approvals/WBS-003.approved
HELIX_CODEX_REQUIRE_APPROVAL_EVIDENCE=1 \
  helix codex --role se --task "WBS-003 を実装" --approved --wbs-id WBS-003

# 編集可能範囲を機械検査
helix codex --role se --task "WBS-003 を実装" \
  --approved \
  --allowed-files 'cli/helix-codex,cli/helix-test'
```

Codex 側の post-validation は、設計 doc（例: `docs/adr/ADR-*.md`）の新規作成 / 変更に WebSearch / WebFetch 証跡を要求する。証跡は `HELIX_CODEX_DESIGN_WEB_EVIDENCE` に transcript / evidence path を `:` 区切りで渡す。未指定のまま対象設計 doc を変更した場合は fail-close する。

```bash
HELIX_CODEX_DESIGN_WEB_EVIDENCE=.helix/research/session.jsonl \
  helix codex --role se --task "ADR を更新" --approved
```

DB feedback-loop の現状は `helix harness feedback-loop` で確認する。既存 `harness_check_events` / `hook_events` / `automation_runs` / `feedback` / `events` / `metrics` / `verify_runs` と `VG-overview` の strict full-flow summary を読み、route candidate / learning candidate / PLAN draft candidate / PR candidate を返す。実行時は snapshot 要約を既存 `events` / `metrics` に append し、`feedback` が空なら missing feedback input を既存 `feedback` table に自動登録する。schema migration、自動実行、gate / detector 変更は行わない。

```bash
helix harness feedback-loop --json
```

G7 subcheck の full execution は anchor 先の pytest / Bats を起動する。構造確認だけなら `--no-exec` または `HELIX_DOCTOR_SKIP_EXEC_TESTS=1` を使う。full execution では各 test file に `HELIX_G7_TEST_TIMEOUT_SECONDS`（既定 120 秒）の timeout を適用し、timeout 時はプロセスグループを停止して `returncode=124` / `timed_out=true` を記録する。

```bash
HELIX_G7_TEST_TIMEOUT_SECONDS=30 python3 -m cli.lib.g7_subcheck --json
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --json
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor check_vg_overview --strict-full-flow --json
HELIX_DOCTOR_SKIP_EXEC_TESTS=1 helix doctor --gate --json
```

`helix doctor --gate` は VG-overview pre-push を fail-close 評価する。`helix push --gate` では `G-vg-overview` として同じ overview を接続し、既存の full pytest / Bats 後に structural G7 anchor / registry / trace / L6 requirement drift を確認する。`required_clean.requirement_drift.clean=false` の場合、L6 設計への閉塞または reason 付き waiver が必要。

`--strict-full-flow` は L6 focus の完了確認ではなく、L0-L14 完全対応監査用である。`approved_deferred` execution gate が残る場合、`vg_overview.full_flow_execution.deferred_pairs[]` に `pair` / `gate_id` / `target` / `next_action` を列挙し、`overall_clean=false` として返す。`not_applicable` pair は `not_applicable_pairs[]` に waiver object として残し、L2-L10 の `ui_absent` のような skip が owner / reason / unskip 条件つきで追跡できるようにする。

`helix harness feedback-loop` は上記 strict full-flow summary を `vg_overview` として snapshot に含め、`full_flow_deferred_execution_gate` / `not_applicable_pair_waiver` learning candidate を生成する。観測系には `harness.feedback_loop.full_flow_deferred_gates` と `harness.feedback_loop.not_applicable_pairs` の metrics を append するため、L6 focus の clean と L8/L9/L12/L14 実行ゲート残を同時に追跡できる。

## TL discipline

Codex / Claude Code は、計画を作ったあとに工程表を無視して実装へ進まない。

> **用語注意**: ここでの「工程表」は **L3 工程表 (`.helix/task-plan.yaml` / WBS)** を指す。これは、L7 着手前に機能設計↔単体テスト (FN↔UT) の充足を見る **L7 worklist** とは別概念である。L7 worklist は機能一覧 (functional-registry) 由来の read-only view (`helix doctor check_l7_worklist` / `helix sprint status` で surfacing、FN↔UT 充足ビュー) で、`missing_ut` を sprint backlog / PLAN へ手動反映する起点に使う (自動起票はしない)。

- 実装前に L3 工程表、`.helix/task-plan.yaml`、handover Next Action の該当行を確認する
- `plan_id`、`task_id` または `WBS ID`、`L7 Sprint`、依存、受入条件、reference_docs を委譲 prompt に含める
- ユーザーへ計画・実装順・整理案を提示した場合、明示承認があるまで編集へ進まない
- 工程表の role に応じて `helix codex`、`helix claude --dry-run`、`helix team` を使う
- `.2` と `.5` では `helix review --uncommitted` を実行する
- サブエージェントやコマンドを使えない場合は、理由を gate evidence / final に残す

工程表行を task-file に落とす例:

```bash
mkdir -p .helix/tasks
cat > .helix/tasks/WBS-003.md <<'EOF'
plan_id: PLAN-001
wbs_id: WBS-003
l4_sprint: .2
role: se
reference_docs:
  - docs/design/L3-schedule-wbs.md
acceptance:
  - 主要 happy path が通る
required_commands:
  - helix code find auth
  - helix review --uncommitted
task:
  PLAN-001 / WBS-003 の最小実装を工程表どおりに進める。
EOF

helix codex --role se --task-file .helix/tasks/WBS-003.md
helix claude --role pg --task-file .helix/tasks/WBS-003.md --dry-run
```

## Claude Code harness の前提

`helix claude` v1 は prompt 生成中心の harness。HELIX は外部プロバイダ呼び出しや認証情報を直接扱わない。`helix team` の Claude member もこの harness を通り、`.helix/tasks/team-*.claude.md` に委譲 prompt を残す。

Claude Code の PostToolUse は `Edit|Write|MultiEdit` を対象にし、settings からは `cli/libexec/helix-post-tool-use` を呼ぶ。wrapper が Claude Code の hook payload から安全な変更ファイルパスだけを抽出し、ファイルごとに `helix hook` の doc-map / freeze / drift advisory を実行する。

Claude Code の PreToolUse は `Write` で `helix check-claudemd`、`Bash` で `cli/libexec/helix-pre-bash`、`WebSearch|WebFetch` で `cli/libexec/helix-pre-research` を呼ぶ。`helix-pre-bash` は raw `codex exec` / `npx codex exec` と raw `claude` をブロックし、`helix codex` または `helix claude --dry-run` 経由へ寄せる。G1R の調査証跡は `research_guard.py` が gate 時に fail-close で検査する。例外的に raw CLI が必要な場合は、同じ Bash command に対象別の証跡 env を含め、final / evidence に代替不能性を残す。

Codex は Claude Code の PreToolUse と同じタイミングでは止められないため、`helix codex` 終了後の post-validation で同等条件を fail-close する。

```bash
# Codex 例外
HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=<理由> codex exec ...

# Claude 例外
HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=<理由> claude ...
```

Context / memory 側の drift は `helix context check` で検査する。SessionStart など短い注入文が必要な場面では `helix context bundle` を使う。bundle には `context_budget` と `context_profile` の要約が含まれ、常時注入・動的注入・除外対象を確認できる。

```bash
helix claude --role pg --task "バグ修正" --dry-run
helix claude --role docs --task-file .helix/tasks/T001.md --output .helix/tasks/T001.claude.md
helix claude --role se --plan-id PLAN-002 --handover --task "Next Action に従って継続" --dry-run
```

生成 prompt には以下が含まれる。

- role / plan_id
- role の system_prompt
- common_docs / skills
- handover 参照指示
- task input
- HELIX 運用ルール

## Handover 連携

Opus セッション上限や作業中断がある場合は `.helix/handover/` を正本にする。

```bash
helix handover status --json
helix handover update --owner codex
helix claude --role pg --handover --task "CURRENT.md の Next Action を実行" --dry-run
```

## 判断境界

以下は Codex / Claude Code のどちらでも人間確認なしに確定しない。

- 認証・認可
- PII
- ライセンス
- 決済
- 本番影響
- destructive な DB / data 操作
- 外部 API / infrastructure / 環境変数の変更
