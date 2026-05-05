---
id: PLAN-018
title: "PLAN-018: LLM Guard / agent policy / research guard の事後正式化と強制導線強化"
status: finalized
size: L
phases:
  - L1
  - L2
  - L3
  - L4
created: "2026-05-05"
owner: tl
reviewers:
  - TL
  - QA
depends_on:
  - PLAN-017
supersedes: []
reference_docs:
  - helix/HELIX_CORE.md
  - skills/SKILL_MAP.md
  - helix/CODEX_TL_MODE.md
  - docs/commands/ai-harness.md
  - .claude/memory/decisions.md
acceptance:
  - "raw Codex / Claude 直叩きが HELIX harness を経由しない場合に fail-close する"
  - "WebSearch / WebFetch など調査ツールの利用漏れを PreToolUse と role policy で抑止する"
  - "team / codex harness の role assignment が許可外 delegation を拒否する"
  - "context guard が hook / memory / stale docs の不整合を検出する"
  - "G2/G3/G4 dry-run と helix test の結果を evidence として記録する"
---

# PLAN-018: LLM Guard / agent policy / research guard の事後正式化と強制導線強化

## §1 メタ

- plan id: `PLAN-018`
- status: `finalized`
- size: `L`
- type: `retroactive-plan`
- reason: T2 LLM Guard は `PLAN` なしで `761e2d3 feat(llm-guard): raw codex/claude 直叩きを PreToolUse Bash hook で遮断` として実装済みだった。21 files / +5749 lines の変更であり、HELIX の `size -> plan -> matrix -> gate -> sprint -> test` を満たしていなかったため、事後 PLAN と retro で正式化する。

## §2 スコープ

### 2.1 in-scope

- raw LLM CLI guard: `cli/lib/llm_guard.py`, `cli/libexec/helix-pre-bash`, `cli/codex`, `cli/claude`
- harness discipline: `cli/helix-codex`, `cli/lib/agent_policy_guard.py`, `cli/lib/team_runner.py`
- research discipline: `cli/lib/research_guard.py`, `cli/lib/research_tool_guard.py`, `cli/libexec/helix-pre-research`, `cli/helix-gate` G1R
- context discipline: `cli/lib/context_guard.py`, `cli/helix-context`, `.claude/settings.json`, `cli/lib/merge_settings.py`
- docs / skills: `docs/commands/ai-harness.md`, `skills/tools/ai-coding/**`, workflow guard references

### 2.2 out-of-scope

- 外部 provider SDK / API 直結 fallback の追加
- secret / credential / env の実値変更
- production infra / external API 設定変更
- Claude Code runtime 本体の仕様変更

## §3 Retroactive Gate Evaluation

- G2: PASS。`./cli/helix-gate G2 --static-only --dry-run --readiness-mode skip` で設計凍結 dry-run PASS。
- G3: PASS。`./cli/helix-gate G3 --static-only --dry-run --readiness-mode skip` で契約凍結 dry-run PASS。
- G4: PASS。`./cli/helix-gate G4 --static-only --dry-run --readiness-mode skip` で実装凍結 dry-run PASS。
- phase.yaml note: 事後評価のため `.helix/phase.yaml` の履歴状態は正本として更新しない。証跡は本 PLAN と memory に記録する。

## §4 実装済み / 追加修正

1. PreToolUse Bash hook と PATH shim で raw `codex exec` / raw `claude` を遮断。
2. `helix codex` に plan-only / approved / evidence / allowed-files の guard を追加。
3. role policy で research task を research role へ強制し、implementation role の Web 調査逃れを拒否。
4. `helix-pre-research` を導入し、WebSearch / WebFetch の調査証跡・role 制約を fail-close 化。
5. `context_guard` が required hook、guard file、stale team command docs、local raw codex allowlist を検出。
6. `helix-gate` static runner を `bash -o pipefail -c` に修正し、`! rg ... | head` 系の absence check 誤判定を解消。
7. `helix-test` の G2 fixture を BE / ui=false に固定し、fullstack 前段状態の漏れを防止。

## §5 Acceptance Evidence

- `python3 -m pytest cli/lib/tests/test_context_guard.py -q --tb=short`: 13 passed。
- `./cli/helix-gate G2 --static-only --dry-run --readiness-mode skip`: PASS。
- `./cli/helix-gate G3 --static-only --dry-run --readiness-mode skip`: PASS。
- `./cli/helix-gate G4 --static-only --dry-run --readiness-mode skip`: PASS。
- `./cli/helix test`: shell 609 passed / Bats 267 passed / pytest 826 passed。

## §6 Process Retro

- violation: T2 は PLAN なしで実装され、設計/レビュー/ゲート/テスト証跡が commit より後になった。
- correction: PLAN-018 を retroactive source of truth とし、事後 gate evidence と full regression を紐付ける。
- prevention: LLM / research / delegation / context の各 guard を code と hook に置き、prompt 指示だけに依存しない。
- remaining risk: retroactive PLAN は事前承認の代替ではない。以後、L 変更は PLAN finalized なしに implementation commit へ進めない。
