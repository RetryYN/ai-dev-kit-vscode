---
plan_id: add-feature-2026-06-15-c2-ruff-shellcheck-advisory
title: "Action(add-feature): L7 自動化② — ruff/shellcheck advisory CI job (continue-on-error, not required)"
plan_scope: action
parent_process: docs/plans/process/process-2026-06-08-verification-forward-gate.md
workflow: add-feature
kind: impl
layer: L7
process_layer: L7
parent_design: docs/v2/L6-functional-design/registry-detector-機能設計.md  # trace: coding_rule_lint (FR-LIB-156/FN-WSC-225) の L6 設計。本 Action は detector logic 不変、CI advisory 配線 + 境界契約 evolution。
forward_return: "ci.yml に ruff-shellcheck-advisory job (continue-on-error, helix doctor check_coding_rule_lint --json, Required 非対象) を追加 -> automation-gate-map §3.4/§5 に approved C-2 advisory CI を記録 -> L7 境界契約 forbidden_now #4 を精緻化 (install/execute external tools as required/fail-close gate のみ禁止、advisory は C-2 で解禁) -> static CI 契約 test で required/broad 化を fail-close 防止 -> L6↔L7 G7 pending gate evidence に帰属 (weakness-map W17)."
drive: be
status: completed
status_note: "2026-06-16 完遂。Process §4.1 後続着手順②。ユーザーが AskUserQuestion で C-2 を明示承認 (forbidden_now install/execute external tools を advisory-only に限定解禁)。完遂境界 = advisory-only CI job (continue-on-error, Required 非対象, detector-gate/doctor --gate/push gate へ fail-close 接続しない) + 境界契約 evolution + static guard test。required 化 / broad 化 / requirements-dev.txt への ruff 混入は禁止 (依然 forbidden)。検証=全 pytest 2603 passed (1 = automation_run timing flake, 単独 3/3 pass=clock skew で C-2 無関係) + 全 bats 796 0-fail + contract 88 passed。"
current_task_scope: c2_ruff_shellcheck_advisory_ci_job
approval_required_before_l7_work: false  # ユーザー AskUserQuestion で C-2 明示承認済 (advisory-only 限定)
tl_review: approve  # design 諮問(2026-06-15)=approve/条件付き(P1=requirements-dev に ruff 入れない・forbidden_now #4 精緻化必須=反映済)。impl review(tl-advisor, 2026-06-16)=approve(P0/P1 なし, P2×2/P3×2 全 non-blocking)。P3-1(tautological assert)=反映済(dead assert 除去, 88維持)。P2-1(audit boundary boolean)=no-change(値は「この ledger 自身は外部ツール未実行」意味で semantically 正、forbidden_now #4 で C-2 例外を既に明文化、flip すると数十の pinned assertion 破壊)。P2-2(generates 列挙)=本文 §2 で全 artifact 説明済 (frontmatter は plan_lint schema 互換の generates のみ)。P3-2(ruff version pin)=defer(advisory なら許容、required 化段階で対応)。
ticket_is_completion_evidence: false
created: 2026-06-15
owner: PM
target_l_pairs:
  - "L6↔L7 (単体): coding_rule_lint (ruff/shellcheck 含む) を CI advisory として実走 (detector logic 不変)"
  - "automation-gate-map: approved C-2 advisory CI を enforcement 段階に記録 (required 非対象)"
design_change_class: design_or_contract_changed  # CI workflow 追加 + latest_user_boundary (forbidden_now #4) の境界契約 evolution。schema/API 変更ではない。再凍結 scope: L6-L7 (W18/L4-L9 は触れない)。
agent_slots:
  - role: se
    slot_label: "SE — ci.yml advisory job + static CI 契約 assertion（Codex）"
  - role: tl-advisor
    slot_label: "TL — advisory 境界 (continue-on-error/required 非混入) / 境界 evolution / guard 非弱体化 の adversarial check"
generates:
  - artifact_path: .github/workflows/ci.yml
    artifact_type: config
  - artifact_path: HELIX-workflows/helix-process/automation-gate-map.md
    artifact_type: doc_update
dependencies:
  parent: docs/plans/process/process-2026-06-08-verification-forward-gate.md
  requires: []
  blocks: []
related_docs:
  - docs/plans/add-feature/add-feature-2026-06-15-w1-narrow-failclose-promotion.md
  - docs/plans/add-feature/add-feature-2026-06-08-detector-failclose-ci-gate.md
  - HELIX-workflows/helix-process/automation-gate-map.md
  - .github/workflows/ci.yml
---

# Action 自動化②: ruff/shellcheck advisory CI job

> 親 Process: [検証 = Forward 内在ゲート](../process/process-2026-06-08-verification-forward-gate.md) §4.1 後続 Forward 着手順 **②ruff/shellcheck advisory**。
> ユーザーが AskUserQuestion（2026-06-15）で C-2 を明示承認（forbidden_now「install/execute external tools」を **advisory-only に限定**して解禁）。C-1（W1 狭い fail-close）は LANDED 済（origin/dogfood 4eb9244）。

## 1. 目的 / 解く問題
pre-L7 Phase2 で `coding_rule_lint`（bash -n / py_compile 常時 + ruff / shellcheck は**存在時のみ** graceful skip）を新設したが、CI 環境には ruff/shellcheck が install されておらず、CI 上では ruff/shellcheck が実質未走（local 依存）。

→ C-2 = ruff/shellcheck を **CI で install/execute する advisory job** を追加し、CI 上でも lint シグナルを可視化する。ただし **advisory-only**（continue-on-error、Required 非対象、PR/CI を落とさない）に限定する。required 化 = forbidden_now（別 Action / 明示承認）。

## 2. スコープ
### In（この Action でやる）
- `.github/workflows/ci.yml` に **専用 job `ruff-shellcheck-advisory`** を追加:
  - `permissions: contents: read` / `continue-on-error: true`
  - checkout + setup-python
  - ruff = job 内 `python3 -m pip install --quiet ruff`（**requirements-dev.txt には追加しない**）
  - shellcheck = job 内 `sudo apt-get install -y shellcheck`
  - 実行 = `helix doctor check_coding_rule_lint --json`（既存 wrapper 経由。直接 ruff/shellcheck surface を新設しない）
  - `--gate` を付けない。`needs:` で test/detector-gate に依存させない。
- automation-gate-map §3.4/§5 に「approved C-2 advisory CI（required 非対象）」を記録。
- **L7 境界契約 evolution**: forbidden_now #4「install/execute external tools」→「install/execute external tools outside approved C-2 ruff/shellcheck advisory CI job or as required/fail-close gate」に精緻化（advisory を C-2 で解禁、required/fail-close 化は forbidden 維持）。C-2 を `current_scope_authorized` に追加。current_allowed_work に C-2 advisory を追記。
- static CI 契約 test（既存 CI 契約 test 関数を拡張 = 新規 test 関数を増やさず 88 件維持）で required/broad 化を fail-close 防止。

### Out（やらない = forbidden_now / 別 Action）
- ruff/shellcheck の **required 化 / detector-gate・doctor --gate・push gate への fail-close 接続**（forbidden、別 Action / 明示承認）。
- `requirements-dev.txt` への ruff 追加（test/detector-gate へ波及 = advisory 境界崩壊、TL P1）。
- W17/W18 ratchet full-required（C-3）/ 右腕 execution gate（C-4）/ DB（後工程）。
- ruff/shellcheck version pin（C-2 最小では不要、TL P3 = 将来）。

## 3. 受入条件
1. **advisory-only**: `ruff-shellcheck-advisory` job が存在し `continue-on-error: true`、Required 非対象、`needs:` なし、`--gate` なし、`check_vg_overview`/`doctor --gate`/`push --gate`/`--strict-full-flow` を含まない。
2. **detector-gate / test job 不変**: 既存 2 job の script に diff なし。`requirements-dev.txt` に ruff なし。
3. **境界契約整合**: forbidden_now 5 項目（#4 精緻化、count 5 維持）が yaml + test term list + handover で一貫。C-2 が current_scope_authorized 枠（ticket 11 不変、l7_work_allowed=false 維持）。
4. **count 同期**: add-feature 19→20 / 派生 ref counts のリップルが audit yaml ×6 + python contract + bats mirror で一貫。
5. **全テスト緑**: 全 pytest + **全 bats**（C-1 の検証漏れ教訓: 件数 pin 含む全 bats を回す）+ contract test green。

## 4. テスト計画
- static CI 契約 assertion（既存 CI 契約 test 関数を拡張、新規 test 関数なし）: §2.4 受入 1-2 を assert。bats mirror も同期。
- 境界契約 contract test（forbidden_now #4 精緻化 + count 19→20）が green。
- 実 CI 実行は GitHub 上で観測（advisory job が PR を落とさないこと）。

## 5. forward_return / 収束
- forward_return: frontmatter の通り。automation-gate-map §3.4/§5 + 境界契約 evolution → L6↔L7 G7 pending gate evidence（weakness-map W17）に帰属。
- design_change_class = design_or_contract_changed（CI workflow + boundary contract evolution）。再凍結 scope = L6-L7（W18/L4-L9 不可侵）。[forward-return-discipline](../../../HELIX-workflows/helix-process/forward-return-discipline.md) 適用。

## 6. escalation / リスク
- CI workflow 追加（消費側 CI 挙動変化）だが advisory-only で PR/CI を落とさない。auth/payment/PII/secret/schema 変更ではない。
- リスク: advisory が required / detector-gate / push gate に混入すると契約違反（TL P1/P2）→ static CI 契約 test で機械防止。
- リスク: requirements-dev.txt に ruff 混入で test/detector-gate へ波及 → §3-2 + static test で防止。

## 7. 進捗ログ
| 日付 | 内容 | 担当 |
|---|---|---|
| 2026-06-15 | Action 起票（Process §4.1 ②）。ユーザー AskUserQuestion で C-2 明示承認。tl-advisor 設計諮問=approve/条件付き（P0なし、P1=requirements-dev に ruff 入れない・forbidden_now #4 精緻化必須、P2=check_coding_rule_lint wrapper 経由）。ci.yml advisory job + 境界 evolution + static guard test の設計確定。 | PM (Opus) |
| 2026-06-15 | 実装: ci.yml `ruff-shellcheck-advisory` job（continue-on-error / permissions contents:read / needs なし / `helix doctor check_coding_rule_lint --json` / ruff は job 内 pip install で requirements-dev.txt 非混入 / shellcheck は apt-get）+ 既存 CI 契約 test 関数を拡張した static assertion（新規 test 関数なし=88 維持）+ automation-gate-map §3.4 に approved C-2 advisory CI を記録。境界契約 evolution（forbidden_now #4 精緻化 + C-2 を current_scope_authorized + add-feature count 19→20 のリップルを audit yaml ×6 + contract py + bats mirror で同期）。 | PM (Opus) |
| 2026-06-15 | 障害復旧: count sweep 中に WSL2 read-only FS フラップで docs/v2/audit/ 29 ファイル + contract test 2 ファイルが 0 byte 化 → C-2 成果物（ci.yml/PLAN/automation-gate-map/helix-doctor/process）の無事を確認 → `git checkout HEAD -- ...` で C-1 状態へ復元 → C-2 境界 evolution を empty-guard 付き script で再適用 + 即時整合検証。全復旧。 | PM (Opus) |
| 2026-06-16 | PM 独立検証（C-1 教訓: gate は全 bats を回す）: 全 pytest **2603 passed**（1 failed = `test_helix_push_records_automation_run` の started_at>ended_at timing flake、単独 3/3 pass で clock skew 確定・C-2 無関係）+ 全 bats **796 0-fail** + contract **88 passed**。product コード混入なし（cli/** 実装不変、CI config + boundary doc/test のみ）。 | PM (Opus) |
| 2026-06-16 | TL impl review（tl-advisor, biyoudogv）= **approve**（P0/P1 なし）。non-blocking: P3-1（tautological `assert "advisory" in "ruff-shellcheck-advisory"`）→ dead assert 除去（88 維持）/ P2-1（audit boundary boolean）→ no-change（「この ledger 自身は外部ツール未実行」意味で正、forbidden_now #4 で C-2 例外明文化済、flip は数十 pinned assertion 破壊）/ P2-2（generates）→ 本文 §2 で全 artifact 説明済 / P3-2（ruff pin）→ defer。受入条件 1-5 全充足 → status=completed / tl_review=approve。次=atomic commit + gate-driven push。 | PM (Opus) |
