---
plan_id: L8-helix-workflows-結合テストplan
title: "L8-helix-workflows-結合テストplan: HELIX-workflows V2 結合テスト (L5 詳細設計 4 doc pair)"
kind: design
layer: L8
drive: be
status: finalized
freeze_note: "L5↔L8 pair freeze (2026-05-29): pair doc integration-test-design.md frozen (IT-IP/IT-MOD/IT-DB/IT-IF, frontmatter追加)。テスト実行/fixture実体は L7-L8 carry"
created: 2026-05-27
owner: PM
process_layer: L8
parent_process: HELIX-workflows/helix-process/L8-integration-test.md
pairs_design:
  - docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
  - docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md
  - docs/v2/L5-internal-design/helix-workflows-physical-data-design.md
  - docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
  - role: tl-advisor
    slot_label: "TL — adversarial check (G8 evidence)"
  - role: qa
    slot_label: "QA — 結合テストケース設計"
generates:
  - artifact_path: docs/v2/L8-test-design/helix-workflows-integration-test-design.md
    artifact_type: design_doc
dependencies:
  parent: L5-helix-workflows-外部IF詳細設計plan
  requires:
    - L5-helix-workflows-内部処理設計plan
    - L5-helix-workflows-モジュール分割設計plan
    - L5-helix-workflows-データ詳細設計plan
    - L5-helix-workflows-外部IF詳細設計plan
  blocks:
    - L8-helix-workflows-依存関係解消plan
related_docs:
  - HELIX-workflows/helix-process/L8-integration-test.md
  - HELIX-workflows/helix-process/L5-detailed-design.md
  - docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md
  - docs/v2/L5-internal-design/helix-workflows-interface-detailed-design.md
  - docs/v2/L9-test-design/helix-workflows-functional-test-design.md
  - docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md
  - docs/adr/ADR-045-helix-workflows-f6-f10-governance-snapshot.md
---

## §0 PLAN concept

本 PLAN は L5 詳細設計 4 doc (内部処理 / モジュール分割 / データ詳細 / 外部IF詳細) と pair で運用する **結合テスト設計** であり、モジュール間結合・インターフェース結合・helix.db migration 結合・hook 連動を機械検証可能な形で確定する。

V-model: L5 ↔ L8 pair freeze の右腕。L5 4 doc に対応する 4 結合テストカテゴリを定義する。

### §0.1 担当 scope

| 観点 | 本 PLAN scope | 隣接 PLAN scope |
|---|---|---|
| モジュール間結合テスト設計 | ◎ 本 PLAN | — |
| インターフェース結合テスト設計 (CLI ↔ hook ↔ DB) | ◎ 本 PLAN | — |
| 依存不整合検出・解消 | × | L8-helix-workflows-依存関係解消plan |

### §0.2 結合テストカテゴリ (L5 4 doc pair)

1. **IT-IP (内部処理結合)**: F1-F10 algorithm が module 跨ぎで連動する pattern (内部処理 doc §1-§12 pair)
2. **IT-MOD (モジュール結合)**: cli/ ↔ cli/lib/ ↔ .claude/hooks/ の責務分担境界 (モジュール分割 doc §3-§9 pair)
3. **IT-DB (helix.db 結合)**: 12 table の FK / CASCADE / migration が module 跨ぎで動作 (物理データ doc §2-§7 pair)
4. **IT-IF (IF 結合)**: CLI 34 + hook 11 の入出力契約が runtime で守られる (外部IF詳細 doc §1-§11 pair)

## §1 工程表

| Step | 作業 | 担当 | 状態 |
|---|---|---|---|
| 1 | L5 4 doc を accepted 状態で読み込み、結合テストカテゴリ 4 種 (IT-IP / IT-MOD / IT-DB / IT-IF) の test case candidate 抽出 | PM + QA | pending |
| 2 | 各カテゴリで 結合 path × 期待動作 × failure mode × 検証 metric の 4 列 table を起草 | QA | pending |
| 3 | 既存 cli/tests/ (bats + pytest) との重複確認・補完 case 設計 | QA | pending |
| 4 | helix-workspace isolation 内 fixture pattern (PLAN-156 連動) | QA + DBA | pending |
| 5 | F6-F10 新規機能の結合 path 追加 (homeostasis ↔ statusLine ↔ event_log 等) | QA | pending |
| 6 | 結合テスト実行戦略 (CI / pre-push / local quick / nightly full) | PM + QA | pending |
| 7 | 二重 audit R1 (tl-advisor + pmo-sonnet) | TL + PMO | pending |
| 8 | R1 反映 + R2 audit | PM + TL + PMO | pending |
| 9 | L8 依存関係解消plan への blocks 設定 + dependency graph validation | PM | pending |
| 10 | commit + push | PM | pending |

## §2 実装計画

### §2.1 doc 構造 candidate

`docs/v2/L8-test-design/helix-workflows-integration-test-design.md`:

```
§0 PLAN reference + scope 宣言
§1 結合テスト全体方針
  §1.1 4 カテゴリ (IT-IP / IT-MOD / IT-DB / IT-IF)
  §1.2 実行戦略 (CI / pre-push / local / nightly)
  §1.3 fixture pattern (helix-workspace isolation, PLAN-156)
§2 IT-IP 内部処理結合 (L5 内部処理 doc §1-§12 pair)
  §2.1 F1-F5 結合 path
  §2.2 F6-F10 結合 path
  §2.3 Reverse 経路 + governance hook 結合
§3 IT-MOD モジュール結合 (L5 モジュール分割 doc §3-§9 pair)
  §3.1 cli/ ↔ cli/lib/ 結合 path
  §3.2 .claude/hooks/ ↔ cli/lib/ via helix CLI call
  §3.3 subagent ↔ Agent tool 結合 (許可リスト + model family 整合)
§4 IT-DB helix.db 結合 (L5 物理データ doc §2-§7 pair)
  §4.1 12 table の FK / CASCADE 動作検証
  §4.2 migration 6-step 結合
  §4.3 rollback evidence + obsolete_record 連動
§5 IT-IF IF 結合 (L5 外部IF詳細 doc §1-§11 pair)
  §5.1 CLI 34 件の exit code 整合
  §5.2 hook 11 件の payload schema 検証
  §5.3 fail-close / fail-open 動作
§6 結合テスト実行戦略 詳細
  §6.1 CI: GitHub Actions workflow (.github/workflows/)
  §6.2 pre-push: scripts/git-hooks/pre-push 連動
  §6.3 local quick: helix test --no-pytest --bats-only
  §6.4 nightly full: helix test --regression --since 24h
§7 4 artifact 双方向 trace
§8 implementation_status 表 (planned/partial/implemented)
```

## §3 DoD

- AC-IT-01: IT-IP / IT-MOD / IT-DB / IT-IF 4 カテゴリ全件の test case candidate 起票
- AC-IT-02: 各 case の 結合 path × 期待動作 × failure mode × 検証 metric 4 列確定
- AC-IT-03: F6-F10 新規機能の結合 path 5 件以上
- AC-IT-04: 既存 cli/tests/ 重複確認 + 補完 case 設計
- AC-IT-05: helix-workspace isolation fixture pattern 適用
- AC-IT-06: 結合テスト実行戦略 (CI / pre-push / local / nightly) 凍結
- AC-IT-07: 二重 audit R1 + R2 PASS
- AC-IT-08: L8 依存関係解消plan への blocks 設定
- AC-IT-09: implementation_status 表に planned/partial/implemented 全件記載

## §4 関連

- pair: L5 4 doc (内部処理 / モジュール分割 / 物理データ / 外部IF詳細)
- parent: L5-helix-workflows-外部IF詳細設計plan (L5 cascade 終端)
- siblings: L8-helix-workflows-依存関係解消plan
- ADR snapshot 候補: 不要 (本 PLAN 内で大局判断は発生しない見込み)
