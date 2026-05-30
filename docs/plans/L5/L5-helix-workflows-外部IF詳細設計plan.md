---
plan_id: L5-helix-workflows-外部IF詳細設計plan
title: "L5-helix-workflows-外部IF詳細設計plan: HELIX-workflows V2 CLI API spec / hook payload schema / 出力 format"
kind: design
layer: L5
drive: be
status: draft
created: 2026-05-27
owner: PM
process_layer: L5
parent_process: HELIX-workflows/helix-process/L5-detailed-design.md
pairs_test_design:
  - docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G5 evidence)"
  - role: doc-reviewer
    slot_label: "doc-reviewer — ドキュメント品質レビュー"
generates:
  - artifact_path: docs/v2/L5-detailed-design/IF詳細設計.md
    artifact_type: design_doc
dependencies:
  parent: L4-helix-workflows-外部IF設計plan
  requires:
    - L4-helix-workflows-方式設計plan
    - L4-helix-workflows-機能構成設計plan
    - L4-helix-workflows-データ設計plan
    - L4-helix-workflows-外部IF設計plan
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
  blocks:
    - L8-helix-workflows-結合テストplan
    - L8-helix-workflows-依存関係解消plan
related_docs:
  - HELIX-workflows/helix-process/L5-detailed-design.md
  - HELIX-workflows/helix-process/L8-integration-test.md
  - docs/v2/L4-basic-design/機能構成設計.md
  - docs/v2/L4-basic-design/方式設計.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
---

## §0 PLAN concept

本 PLAN は HELIX-workflows V2 の **CLI API spec / hook event payload schema / 出力 format / error handling** を凍結する。pmo-sonnet inventory で抽出した CLI 34 件 + hook 11 件 の **入出力契約** を確定する。

⚠️ tl-advisor P1 警戒: 本 PLAN scope が大きい (CLI 34 + hook 11) ため、本体起草時に 800 行超過したら IF-core (CLI / 出力 format) + IF-hook (hook event payload) に再分割を検討する。本 PLAN frontmatter `blocks` 構造は分割時に修正可能な状態で凍結する。

### §0.1 担当 scope（L5 4 分割における本 PLAN の責務）

| 観点 | 本 PLAN scope | 隣接 PLAN scope |
|---|---|---|
| CLI API spec (argparse / 出力 format / exit code) | ◎ 本 PLAN | — |
| hook event payload schema | ◎ 本 PLAN | — |
| error handling / fail-close vs fail-open | ◎ 本 PLAN | — |
| 内部処理 algorithm | × | L5-helix-workflows-内部処理設計plan |
| module 配置 | × | L5-helix-workflows-モジュール分割設計plan |
| helix.db schema | × | L5-helix-workflows-データ詳細設計plan |

### §0.2 対象 CLI (pmo-sonnet inventory A-01〜A-34)

| 領域 | CLI 件数 | status |
|---|---:|---|
| F1 doctor (4 ドメイン分離 / SSoT 同期 / 4 artifact trace) | 3 | planned |
| F2 plan validator (frontmatter / 命名 / ADR snapshot drift) | 3 | planned |
| F4 mode routing | 1 | planned |
| F5 parallel / role audit | 2 | planned |
| F6 homeostasis | 2 | planned |
| F7 evolution (fork / score / promote / deprecate) | 4 | planned |
| F8 reproduction (version bump / migrate / portable export/import/adopt) | 6 | planned/partial |
| F9 apoptosis / autophagy | 3 | planned |
| F10 symbiosis (coexist framework / status / adopt) | 3 | planned |
| Reverse 経路 + Recovery | 2 | ⚠️ 不確定 |
| BR-12 ratchet | 2 | partial |
| implementation_status pair | 1 | planned |
| planned CLI aging | 1 | planned |
| framework coexist namespace | 1 | planned |
| **合計** | **34** | — |

### §0.3 対象 hook (pmo-sonnet inventory B-01〜B-11)

| Hook | 種別 | status |
|---|---|---|
| statusLine | statusLine | implemented |
| PreCompact | PreCompact | implemented |
| pretooluse-agent-guard.sh | PreToolUse (Agent) | implemented |
| pre-commit doc lint | pre-commit | planned |
| pre-commit plan validate | pre-commit | implemented |
| post-task skill log | PostToolUse (Task) | planned |
| SessionStart (mode hint) | SessionStart | implemented |
| weekly cron / GitHub Actions | scheduled | planned |
| mutation hook | ⚠️ 不確定 | planned |
| migration event hook | ⚠️ 不確定 | planned |
| coexist event hook | ⚠️ 不確定 | planned |

### §0.4 不確定事項からの引き継ぎ（pmo-sonnet inventory より）

本 PLAN で確定すべき不確定事項:

- U-01: `helix budget --homeostasis` vs `helix budget status --homeostasis` (subverb 構造確定)
- U-02: `helix portable adopt` vs `helix coexist adopt` の重複 (1 CLI 統合 or 2 CLI 分岐)
- U-03: `helix doctor --check-mode-routing` vs `--check-mode-transition` の flag 名称統一
- U-04: `helix recovery --finalize-to-adr` vs `helix recover` の正本一本化
- U-05: `helix doctor --check-planned-cli-age` の aging 判定基準 + 出力 format
- U-06: `post-task skill log` hook の PostToolUse matcher 名確定
- U-07: mutation / migration / coexist event hook の種別 + 発火条件 + payload schema

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | CLI 34 件の現状実装 status を `helix --help` + `grep` で確認 | PM + pmo-sonnet | done |
| 2 | 各 CLI の argparse spec (positional / optional / flag) 起草 | PM | done |
| 3 | 各 CLI の出力 format (text / json / yaml) 確定 | PM | done |
| 4 | 各 CLI の exit code 確定 (0/1/2/N 別ルール) | PM | done |
| 5 | hook 11 件の event payload schema (JSON Schema) 起草 | PM | done |
| 6 | hook fail-close / fail-open 判定確定 | PM + security | done |
| 7 | 不確定 U-01〜U-07 を tl-advisor adversarial で確定 | tl-advisor | done |
| 8 | error handling 共通ルール (timeout / retry / blocking) 凍結 | PM | done |
| 9 | 800 行超過時の分割判定 (IF-core + IF-hook) | PM | done |
| 10 | 二重 audit R1 (tl-advisor + pmo-sonnet) | TL + PMO | done |
| 11 | R1 反映 + R2 audit | PM + TL + PMO | done |
| 12 | L8 結合テスト設計 pair freeze | PM | done |
| 13 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L5-detailed-design/IF詳細設計.md`:

```
§0 PLAN reference + scope 宣言
§1 CLI API 共通ルール
  §1.1 argparse pattern (positional / --flag / --json)
  §1.2 出力 format (text default, --json で構造化)
  §1.3 exit code ルール (0 success / 1 user error / 2 fail-close / N domain error)
  §1.4 timeout / retry / blocking
§2 helix doctor check_* (F1/F2/F4/F5/F6/BR-12)
  §2.1 --check-4-domain-separation
  §2.2 --check-ssot-sync
  §2.3 --check-4-artifact-trace
  §2.4 --check-plan-frontmatter-completeness
  §2.5 --check-plan-naming-convention
  §2.6 --check-plan-adr-snapshot
  §2.7 --check-mode-routing (U-03 確定)
  §2.8 --check-parallel-compliance
  §2.9 --check-role-assignment
  §2.10 --check-homeostasis
  §2.11 --check-implementation-status-pair
  §2.12 --check-planned-cli-age (U-05 確定)
  §2.13 --check-framework-coexist
  §2.14 --check-changeprop / --check-changeprop --update
§3 helix budget (F6 homeostasis)
  §3.1 budget status (既存) → --homeostasis flag (U-01 確定)
§4 helix plan (F2 / F7 / F9)
  §4.1 plan fork (F7)
  §4.2 plan apoptosis (F9)
§5 helix evolution (F7)
  §5.1 evolution score
  §5.2 evolution promote
  §5.3 evolution deprecate
§6 helix version / migrate / portable (F8 / F10)
  §6.1 version bump --major / --minor
  §6.2 migrate v<from> --to v<to>
  §6.3 portable export / import / adopt (U-02 確定)
§7 helix db autophagy (F9)
§8 helix coexist (F10)
  §8.1 coexist framework
  §8.2 coexist status
  §8.3 coexist adopt (U-02 連動)
§9 helix recovery (Recovery mode)
  §9.1 recovery --finalize-to-adr (U-04 確定)
§10 hook payload schema
  §10.1 statusLine (implemented)
  §10.2 PreCompact (implemented)
  §10.3 pretooluse-agent-guard (implemented)
  §10.4 SessionStart cleared/compacted (implemented)
  §10.5 UserPromptSubmit (implemented)
  §10.6 pre-commit doc lint / plan validate
  §10.7 PostToolUse (Task) → skill_usage (U-06 確定)
  §10.8 weekly cron / GitHub Actions
  §10.9 mutation hook (U-07a 確定)
  §10.10 migration event hook (U-07b 確定)
  §10.11 coexist event hook (U-07c 確定)
§11 error handling 共通ルール
  §11.1 fail-close 判定基準
  §11.2 fail-open 判定基準
  §11.3 timeout / retry
§12 4 artifact 双方向 trace
§13 implementation_status 表 (planned/partial/implemented)
```

### §2.2 IF 粒度

各 CLI / hook について以下を含む:

**CLI**:
1. usage (positional / optional / flag)
2. 入力 (stdin / file / argument)
3. 出力 (text / json schema)
4. exit code (success / user error / fail-close)
5. side effect (helix.db write / file write)
6. error message template

**hook**:
1. event type / matcher
2. event payload schema (JSON Schema or pydantic spec)
3. expected exit code interpretation (Claude Code 仕様)
4. fail-close / fail-open
5. timeout
6. audit log 連動 (role_audit / event_log)

## §3 DoD

- AC-IF-01: CLI 34 件全件の argparse spec 凍結
- AC-IF-02: CLI 34 件全件の出力 format (text / json) 凍結
- AC-IF-03: CLI 34 件全件の exit code 凍結
- AC-IF-04: hook 11 件全件の event payload schema 凍結
- AC-IF-05: hook 11 件全件の fail-close / fail-open 判定凍結
- AC-IF-06: 不確定 U-01〜U-07 全件確定
- AC-IF-07: error handling 共通ルール凍結
- AC-IF-08: 二重 audit R1 + R2 PASS
- AC-IF-09: L8 pair PLAN への blocks 設定
- AC-IF-10: implementation_status 表に planned/partial/implemented 全件記載
- AC-IF-11: 800 行超過時の分割判定実施 (超過時は IF-core + IF-hook に分割)

## §4 関連

- pair: docs/v2/L8-test-design/L5-detailed-design-結合テスト設計.md
- parent: L4-helix-workflows-外部IF設計plan
- siblings: L5-helix-workflows-内部処理設計plan / L5-helix-workflows-モジュール分割設計plan / L5-helix-workflows-データ詳細設計plan
- ADR snapshot 候補: ADR-046 (CLI 34 件 + hook 11 件 の正本一本化と契約凍結の大局判断時)

## L5 完遂 evidence (2026-05-29)

- 設計 doc: docs/v2/L5-detailed-design/IF詳細設計.md — 本体化完遂、frontmatter status: frozen
- pair freeze: L5↔L8 双方向 trace (IT-IF 結合テスト設計: integration-test-design.md §IF section)
- 監査: pmo-sonnet 機械検証 (placeholder 0 / CLI 34 件 + hook 11 件 全件 spec 記載確認) + tl-advisor adversarial check
- DoD: AC-IF-01〜AC-IF-11 達成 (U-01〜U-07 全件確定済)
- carry (L7 実装): planned CLI (34 件のうち planned/partial) の実装遷移 + mutation / migration / coexist event hook の実体実装
