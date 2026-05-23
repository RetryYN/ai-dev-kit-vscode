---
plan_id: PLAN-198
title: hook security audit (hook 権限スコープ静的解析)
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: security
    slot_label: "Security — 危険 pattern 定義・AST 解析方針設計・OWASP A03/A04 hook 適用"
  - role: se
    slot_label: "SE — cli/lib/hook_security_scanner.py 実装・helix doctor check_hook_security 統合"
  - role: pmo-sonnet
    slot_label: "PMO — hook permission matrix 設計確認・PLAN-153 security audit との連携整合チェック"
generates:
  - artifact_type: python_module
    path: cli/lib/hook_security_scanner.py
  - artifact_type: test
    path: cli/lib/tests/test_hook_security_scanner.py
  - artifact_type: doc_update
    path: docs/architecture/hook-permission-matrix.md
dependencies:
  requires:
    - PLAN-153
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - docs/plans/PLAN-153-helix-security-audit-framework.md
  - docs/plans/PLAN-087-web-search-design-doc-guardrail.md
  - docs/plans/PLAN-089-gate-fail-close-design-doc-web-search-audit.md
  - .claude/settings.json
acceptance_criteria:
  - "helix doctor check_hook_security が .claude/hooks/*.sh を静的スキャンして危険 pattern を WARN/FAIL 出力できる"
  - "危険 pattern (rm -rf / curl 外部通信 / chmod 777 / eval / unset -f) を検出できる"
  - "各 hook の file 書き込み範囲 / 環境変数アクセス / 外部 process 起動を permission matrix として出力できる"
  - "python3 -m py_compile cli/lib/hook_security_scanner.py PASS"
  - "pytest test_hook_security_scanner.py 全 PASS (8 case 以上)"
  - "HELIX 既存 15 hook すべてに対してスキャンが完走し、false positive が 0 であることを確認する"
  - "scan 対象外 pattern (.bats / .py / .json) はスキップして WARN を出さない"
---

# PLAN-198: hook security audit (hook 権限スコープ静的解析)

## L2 凍結 (ADR snapshot)

既存 security framework (PLAN-153 / PLAN-087 / PLAN-089) の内部拡張として hook スキャンを追加する。
新規 framework 採用なし。L2 大局判断は PLAN-153 の ADR-054 で凍結予定。
本 PLAN に独立した ADR snapshot は不要。

## 背景

HELIX には 2026-05-23 時点で `.claude/hooks/` に 15 hook が登録されている。
PLAN-087 / PLAN-089 / PLAN-109 / PLAN-113 / PLAN-117 / PLAN-144 等の複数 PLAN で
段階的に hook が追加されてきたが、各 hook の権限スコープ (file 書き込み範囲 /
環境変数アクセス / 外部 process 起動) を横断的に監査する仕組みが存在しない。

問題ケース:

- `rm -rf` / `curl` 外部通信 / `chmod 777` を含む hook が審査なく追加されるリスク
- `.helix/` 外への書き込みが意図せず発生する hook が存在する可能性
- `eval` / `$(...)` による動的コード実行が hook に混入するリスク
- settings.json に登録されていない hook file が `.claude/hooks/` に残置されるリスク

本 PLAN は `cli/lib/hook_security_scanner.py` を実装し `helix doctor check_hook_security`
に統合することで、hook 追加時の権限スコープ監査を机械化する。

## WebSearch 履歴 — skip

bash 静的解析は ShellCheck が標準ツールだが、本 PLAN は HELIX 独自 pattern 検出に特化する
(ShellCheck との併用は carry)。外部 standard 検索は不要。

## 危険 pattern 定義 (7 種)

| ID | pattern | severity | 説明 |
|---|---|---|---|
| H-DANGER-001 | `rm -rf` / `rm -f` | FAIL | 再帰削除・強制削除 |
| H-DANGER-002 | `curl` / `wget` (外部通信) | WARN | 外部 HTTP アクセス |
| H-DANGER-003 | `chmod 777` / `chmod a+w` | WARN | 過剰 permission 付与 |
| H-DANGER-004 | `eval` | FAIL | 動的コード実行 |
| H-DANGER-005 | `unset -f` / `unset -v` | WARN | 関数・変数破壊 |
| H-DANGER-006 | `.helix/` 外への write | WARN | write 範囲逸脱 |
| H-DANGER-007 | settings.json 未登録 hook file | WARN | 孤立 hook |

severity=FAIL は helix doctor の FAIL カウントに加算。WARN は WARN カウントに加算。

## permission matrix 出力

各 hook について以下を抽出して `docs/architecture/hook-permission-matrix.md` に出力する:

| hook | trigger | write_paths | env_reads | external_cmds | danger_flags |
|---|---|---|---|---|---|
| pretooluse-agent-guard.sh | PreToolUse | [] | HELIX_ALLOW_RAW_AGENT | jq | none |
| posttooluse-plan-drift-detect.sh | PostToolUse | .helix/cache/plan-drift/ | — | python3 | none |

write_paths 抽出: `>`, `>>`, `tee`, `write_text()` 等の出力先を正規表現で抽出。
env_reads 抽出: `$ENV_VAR` / `${ENV_VAR}` を grep。
external_cmds 抽出: command name (first word of pipeline) を抽出。

## 実装計画

### Sprint .1: scanner core 実装 (Codex se)

`cli/lib/hook_security_scanner.py` に以下を実装する:

- `scan_hook(path: Path) -> HookScanResult`: 1 hook ファイルを静的スキャン
  - 7 pattern を正規表現で検出
  - write_paths / env_reads / external_cmds を抽出
  - `HookScanResult(hook_name, findings, permission_scope)` を返す
- `scan_all_hooks(hooks_dir: Path) -> list[HookScanResult]`: 全 hook を走査
- unit test 4 case (H-DANGER-001 検出 / H-DANGER-004 検出 / clean hook = 0 findings / .bats skip)

完了条件: `python3 -m py_compile` PASS + pytest 4 PASS

### Sprint .2: permission matrix + settings.json 突合 (Codex se)

- `build_permission_matrix(results) -> str`: Markdown table 形式で matrix 生成
- `check_unregistered_hooks(hooks_dir, settings_json) -> list[str]`: settings.json 未登録検出 (H-DANGER-007)
- `docs/architecture/hook-permission-matrix.md` への書き込み (実行時 update)
- unit test 4 case (matrix 生成 / 未登録検出 / write_paths 抽出 / env_reads 抽出)

完了条件: pytest 累計 8 PASS + matrix ドキュメント生成確認

### Sprint .3: helix doctor 統合 + 既存 15 hook 検証 (Codex se)

- `helix doctor check_hook_security` に scanner を統合
  - severity=FAIL → doctor FAIL カウント
  - severity=WARN → doctor WARN カウント
- 既存 15 hook 全スキャン実行 → false positive 0 確認
- HELIX_SKIP_HOOK_SECURITY=1 で bypass 可能にする (CI sandbox 対応)

完了条件: helix doctor check_hook_security 動作確認 + 15 hook false positive = 0

## mandatory in sprint

- [ ] `python3 -m py_compile cli/lib/hook_security_scanner.py` PASS
- [ ] `pytest cli/lib/tests/test_hook_security_scanner.py` 8 case 全 PASS
- [ ] 既存 15 hook に対して false positive = 0 確認
- [ ] helix doctor check_hook_security WARN/FAIL カウント統合確認
- [ ] pmo-sonnet review (Sprint .3)

## DoD

- [ ] hook_security_scanner.py 実装済 (scan_hook / scan_all_hooks / build_permission_matrix)
- [ ] helix doctor check_hook_security 統合済
- [ ] docs/architecture/hook-permission-matrix.md 生成確認
- [ ] pytest 8 PASS
- [ ] 既存 15 hook false positive = 0 確認
- [ ] helix doctor pass 数現行以上維持

## carry / リスク

| リスク | 緩和 |
|---|---|
| bash 正規表現による false positive | 対象 hook を 1 件ずつ検証してパターンを調整する |
| write_paths 抽出の精度 (動的パス) | 動的パス (`$VAR/path`) は WARN ではなく INFO 扱いにする |
| ShellCheck との重複 | ShellCheck は構文・品質、本 scanner は HELIX 固有 pattern に特化し棲み分ける |
| PLAN-153 未完時の先行着手 | requires: PLAN-153 で依存を明示。PLAN-153 完了まで Sprint .1 のみ先行可 |

## 関連 reference

- PLAN-153 (helix security audit framework、requires)
- PLAN-087 (PreToolUse design-doc-web-search-guard、hook 登録範例)
- PLAN-089 (PostToolUse fail-close 設計)
- [[feedback_merge_settings_helix_hook_judge_bug]]
