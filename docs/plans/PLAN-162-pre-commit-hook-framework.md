---
plan_id: PLAN-162
title: "PLAN-162: pre-commit hook framework"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: M
created: 2026-05-23
revised: 2026-05-23
owner: PM
agent_slots:
  - role: se
    slot_label: "SE — pre-commit hook 本体・helix doctor 統合・設定ファイル実装"
  - role: security
    slot_label: "Security — gitleaks / secret scan 設計レビュー・opt-out 条件確認"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 hook 整合チェック・PLAN-153/110 との重複確認"
generates:
  - artifact_path: .git/hooks/pre-commit
    artifact_type: script
  - artifact_path: cli/lib/pre_commit_runner.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_pre_commit_runner.py
    artifact_type: test
  - artifact_path: .helix/config/pre-commit-config.yaml
    artifact_type: yaml_config
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_docs:
  - docs/plans/PLAN-153-security-audit-integration.md
  - docs/plans/PLAN-110-doctor-warn-reduction.md
  - .claude/hooks/pretooluse-agent-guard.sh
  - cli/helix-doctor
acceptance_criteria:
  - "pre-commit hook が lint (shellcheck / yamllint / markdownlint) を staged file に対して実行する"
  - "helix doctor smoke (helix doctor --quick) を pre-commit 内で実行し fail 時は commit を block する"
  - "gitleaks または grep ベースの secret scan が staged file に対して動作する"
  - "HELIX_SKIP_PRE_COMMIT=1 で全チェックを skip し opt-out を audit log に記録する"
  - "bash -n .git/hooks/pre-commit PASS"
  - "unit test 8 case 全 PASS"
  - "commit 失敗時に staged file 名と修正案を stderr に表示する"
---

# PLAN-162: pre-commit hook framework

## L2 凍結 (ADR snapshot)

本 PLAN は既存 Claude Code hook framework (PLAN-087/089) とは独立した Git hook 領域の追加であり、
新規アーキテクチャ判断は含まない。既存の `.git/hooks/` 慣例に従う実装のため ADR snapshot は不要。

## 背景

HELIX repo には `.claude/hooks/` 配下の Claude Code フック (PreToolUse / PostToolUse) と
`.claude/hooks/pre-push` が存在するが、`pre-commit` hook が不在。
結果として以下の問題が発生している:

- shellcheck 未通過の bash スクリプトがコミット可能
- yamllint 違反の frontmatter を含む PLAN.md がコミット可能
- secret / token の誤コミットを防ぐ機械的ガードがない
- helix doctor の warn が commit 後まで気づかれず積み上がる

pre-push hook は存在するが (`EMAIL_PATTERN` 等)、push 直前では修正コストが高い。
pre-commit で早期検知・早期修正を実現する。

## WebSearch 履歴

内部 Git hook 実装。外部ライブラリ新規依存なし。
shellcheck / yamllint / markdownlint / gitleaks は既存ツール利用を前提とし、
インストール不在時は advisory warning にとどめて commit を block しない。

## 3 段チェック設計

### Stage 1: lint チェック

| ツール | 対象 | インストール不在時 |
|---|---|---|
| `shellcheck` | staged `*.sh` ファイル | WARN のみ、block なし |
| `yamllint` | staged `*.yaml / *.yml` ファイル | WARN のみ、block なし |
| `markdownlint` | staged `*.md` ファイル | WARN のみ、block なし |
| `bash -n` | staged `*.sh` ファイル | 常に実行、fail → block |

`bash -n` は外部ツール不要のため常に block 対象とする。

### Stage 2: smoke チェック

`helix doctor --quick` を実行し、`pass < (fail + 5)` の場合（fail が前回比で増加した場合）に block。
閾値は `.helix/config/pre-commit-config.yaml` で設定変更可能。

対象 check のうち fail-close 指定済みのもの (PLAN-089/093 等) のみを smoke 対象とする。
advisory WARN のみの check は commit を block しない。

### Stage 3: secret scan

gitleaks が利用可能な場合: `gitleaks detect --source . --staged` を実行し fail → block。
gitleaks 不在の場合: `grep` ベースの簡易 pattern scan (API key / AWS / GH token 等) で代替。
簡易 scan の false positive は bypass 可能 (HELIX_SKIP_SECRET_SCAN=1)。

## opt-out 設計

`HELIX_SKIP_PRE_COMMIT=1` で全チェックを skip。`HELIX_SKIP_LINT=1` / `HELIX_SKIP_DOCTOR=1` /
`HELIX_SKIP_SECRET_SCAN=1` で stage 別 skip。
スキップ時は `~/.helix/logs/pre-commit-skip.log` に日時・コミット hash を記録する。
CI 環境 (`CI=true`) では自動 skip（push-side で検証済み前提）。

## 実装計画

### Sprint .1: Python helper 実装 (Codex se、size S)

`cli/lib/pre_commit_runner.py`:
- `get_staged_files(extensions: list[str]) -> list[Path]`
  `git diff --cached --name-only --diff-filter=ACMR` で staged file 一覧取得
- `run_lint_checks(staged_files: list[Path]) -> list[str]`
  bash -n / shellcheck / yamllint / markdownlint を順次実行し、エラー行を収集
- `run_doctor_smoke() -> bool`
  `helix doctor --quick` を subprocess 実行し ok/fail を返す
- `run_secret_scan(staged_files: list[Path]) -> list[str]`
  gitleaks または grep ベース scan を実行し検出行を返す
- `should_skip() -> dict[str, bool]`
  `HELIX_SKIP_*` 環境変数と `CI` フラグを解釈して stage 別 skip map を返す

単体テスト `cli/lib/tests/test_pre_commit_runner.py` 8 case:
- T1: staged file 一覧取得 (git mock)
- T2: bash -n エラー検出
- T3: shellcheck 不在時の graceful fallback (WARN のみ)
- T4: doctor smoke pass
- T5: doctor smoke fail (fail 数増加)
- T6: secret scan pattern マッチ
- T7: HELIX_SKIP_PRE_COMMIT=1 で全 skip
- T8: CI=true で自動 skip

完了条件: `python3 -m py_compile cli/lib/pre_commit_runner.py` PASS + unit test 8 PASS

### Sprint .2: hook スクリプト実装 (Codex se、size S)

`.git/hooks/pre-commit` 新規作成:
shebang + `python3 "$HELIX_ROOT/cli/lib/pre_commit_runner.py" --hook-mode` を呼ぶ最小 wrapper。
`--hook-mode` で 3 stage 順次実行、失敗時は staged file 名 + 修正案を stderr 出力して exit 1。
skip 時は audit log 記録して exit 0。

`.helix/config/pre-commit-config.yaml`:
`doctor_fail_threshold` / `lint_block` / `lint_warn` / `secret_scan_patterns` を定義。
初期値: lint_block=[bash-n]、lint_warn=[shellcheck, yamllint, markdownlint]、threshold=5。

完了条件: `bash -n .git/hooks/pre-commit` PASS + `git commit` で hook 動作確認

### Sprint .3: helix doctor 統合 + 設置ガイド (Codex se + Docs、size S)

`helix doctor check_pre_commit_hook` 追加:
- `.git/hooks/pre-commit` 存在チェック → 不在で advisory WARN
- `bash -n .git/hooks/pre-commit` 結果 → fail で advisory WARN

helix doctor コマンドで `check_pre_commit_hook` を既存 check 群に追加。
`cli/helix init` (template 配布) で `.git/hooks/pre-commit` 自動インストールを検討
（template 配布は `.helix/install/pre-commit` に格納し、`helix init --setup-hooks` で有効化）。

完了条件: helix doctor WARN 表示確認 + `helix init --setup-hooks` 動作確認

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/pre_commit_runner.py` PASS
- [ ] `bash -n .git/hooks/pre-commit` PASS
- [ ] unit test 8 case PASS
- [ ] `HELIX_SKIP_PRE_COMMIT=1 git commit` で skip + audit log 記録確認
- [ ] CI=true 環境での自動 skip 確認
- [ ] helix doctor check_pre_commit_hook advisory WARN 表示確認
- [ ] security role review (Sprint .2 完了後、secret scan パターン妥当性確認)
- [ ] pmo-sonnet review (Sprint .3 完了後)

## DoD

- [ ] `.git/hooks/pre-commit` 実装・`bash -n` PASS
- [ ] `cli/lib/pre_commit_runner.py` 3 stage 対応
- [ ] `.helix/config/pre-commit-config.yaml` 設定ファイル作成済
- [ ] `HELIX_SKIP_PRE_COMMIT=1` opt-out + audit log 記録動作
- [ ] unit test 8 case PASS
- [ ] helix doctor check_pre_commit_hook WARN 表示
- [ ] helix doctor pass 数現行以上

## V-model 4 artifact trace

| artifact | パス |
|---|---|
| ① 設計 | docs/plans/PLAN-162-pre-commit-hook-framework.md |
| ② 実装コード | .git/hooks/pre-commit / cli/lib/pre_commit_runner.py |
| ③ テスト設計 | 本文 §Sprint .1 T1-T8 + §mandatory in sprint |
| ④ テストコード | cli/lib/tests/test_pre_commit_runner.py |

## carry / リスク

- `.git/hooks/` は git 管理外 → `helix init --setup-hooks` で手動インストール手順必須
- gitleaks 未インストール時は grep 代替、false negative リスクあり (carry 候補)
- markdownlint は Node.js 依存、不在時は warn のみで carry

## 関連 reference

- PLAN-153 (security audit integration)
- PLAN-110 (helix doctor warn 漸減)
- PLAN-087 (設計 doc Web 検索ガードレール、PreToolUse hook 設計参考)
- .claude/hooks/pretooluse-agent-guard.sh (hook 実装パターン参考)
