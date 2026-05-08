---
plan_id: PLAN-032
title: HELIX v2/31 carry 解消 (helix-test self-test + 並列誤検出 + tests 統合)
status: completed
created: 2026-05-09
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
acceptance:
  - W-1 (self-test 期待値追従) で test 255/400/459/685 4 件 PASS。
  - W-2 (`cli/helix-codex` の `detect_plan_only_task` 判定順序改修、task_type_inference.py 自体は無変更) で test 507/508 PASS。
  - W-3 (sprint complete state seed) で test 622 PASS。
  - W-4 (allowed-files 並列誤検出) で 3 並列 helix-codex で warning 0 件。
  - W-5 (tests/ vs cli/lib/tests/ 重複整理) は最小限の境界記述で対応可。
  - cli/helix-test の shell-based self-test が 0 failed (現 7 -> 0)。
  - 既存 regression: pytest cli/lib/tests/ + pytest tests/ + bats cli/tests に regression なし。
related: [PLAN-028, PLAN-029, PLAN-030, PLAN-031, ADR-014, ADR-015]
---

## §1 背景・前提

PLAN-031 完遂後、`cli/helix-test` 全体走査で 7 件の self-test failed を確認し、PLAN-031 retro carry 2 件を加えて 9 件を PLAN-032 に集約する。

A. helix-test self-test 失敗 7 件

- agents copied は `.claude/agents` 配布が空になったため失敗。
- manual --thinking の期待値が v2 の運用表記（「手動」）と未一致。
- jsonl schema allowed agents count が 11 に低下し 16 を期待すると fail。
- plan-only auto guard の結果判定が「実装」分類に寄っており既存期待値と不一致。
- codex plan-only auto guard が full-auto を無効化しない判定に未追従。
- sprint complete のガイド期待が「helix gate G4」から ESLint 混入へ逸脱。
- G7 が「デプロイ前チェックリスト」を参照する文言に更新されず「G6.9 未通過」を出力。

B. PLAN-031 retro carry 2 件

- allowed-files 並列誤検出の `own_baseline` 前後の concurrent 判定の追加改修。
- `tests/` と `cli/lib/tests/` の重複整理と境界記述の整備。

## §2 スコープ

### §2.1 対象

- helix-test 失敗 7 件（test 255/400/459/507/508/622/685）。
- PLAN-031 retro carry 2 件。
- 既存 PLAN-031 の関連 retro carry 反映。

### §2.2 非対象

- TUI/Web ダッシュボード (`PLAN-029` W-10 §6 の将来検討対象)。
- 本番データ破壊や外部 API / インフラ変更を伴う改修。

## §3 axis-by-axis 設計

### axis-1: helix-test self-test 期待値 v2 追従

- 対象: `cli/helix-test`。
- 方針: test 255/400/459/685 を v2 実行時の実測値に合わせて期待値を更新し、`cli/templates/agents/` 配布も復元。
- DoD: 該当セルフトテストの文字列一致 PASS。

### axis-2: task_type_inference + detect_plan_only_task

- 対象: `cli/helix-codex` (`detect_plan_only_task` 関数 line 317 周辺) を **主**。`cli/lib/task_type_inference.py` は **無変更** (regression 対象として PASS 維持のみ)
- 構造的な原因: `detect_plan_only_task` が `task_type=実装` を早期 return → plan-pattern (整理|計画|工程表|...) が含まれていても auto consent guard が発火しない
- 方針:
  - **明示 `[タスク種別] 実装` は実装扱いを維持** (ユーザー意図優先)
  - **`--approved` 指定時は workspace-write 維持** (consent 明示尊重)
  - **`--consent auto` の場合のみ**、`detect_plan_only_task` で plan-pattern を inferred task_type の「実装」判定より優先して plan-only 発火
  - task_type_inference.py 自体は触らず、`detect_plan_only_task` の判定順序のみ変更 (「整理」を「設計」へ移すと「コードを整理して」等が設計過剰分類されるため)
- DoD: test 507/508 PASS、既存関連テスト維持、3 動作 (auto + plan-pattern → plan-only / 明示 [タスク種別] 実装 → 実装維持 / --approved → workspace-write 維持) すべて確認

### axis-3: helix-sprint complete state seed

- 対象: `cli/helix-test` (production の `cli/helix-sprint complete` には test mode flag を追加しない、TL 推奨)。
- 方針: test 622 実行前に sprint state を **「.5 完了直前」** (`.5` ステップが残っており complete 実行で gate G4 guidance を誘導できる状態) に seed する。`current_step=completed` ではないことに注意 (completed 状態は「完了対象なし」エラーになる)。
- DoD: test 622 PASS、`helix gate G4` 文字列が complete 出力に含まれる。

### axis-4: allowed-files 並列誤検出

- 対象: `cli/lib/codex_post_validation.py`。
- 方針: `load_newer_baselines` の `own_baseline` 前後での concurrent 判定を拡張し、同時実行間の誤検出を抑止。
- DoD: 3 並列 `helix-codex` 実行で stderr warning0 件。

## §4 Sprint plan（W-1..W-6）

### W-1（size: S / axis-1）: self-test 4 件期待値追従

- 実装対象: `cli/helix-test`（line 255, 400, 459, 685）および `cli/templates/agents/`。
- 担当: pg --thinking medium。
- DoD:
  - test 255/400/459/685 PASS。
  - `cli/templates/agents/*.md` に `.claude/agents/*.md` 現行 7 ファイルを配置。

### W-2（size: M / axis-2）: detect_plan_only_task の判定順序改修

- 実装対象: `cli/helix-codex` (`detect_plan_only_task` 関数、line 317 周辺)。task_type_inference.py 自体は触らない。
- 担当: SE --thinking high。
- 修正方針: `--consent auto` のとき、plan-pattern マッチを inferred task_type=実装 の早期 return より優先する。明示 [タスク種別] 実装 と --approved は plan-only を発火させない。
- DoD:
  - test 507/508 PASS (`実装計画を整理して` で auto → plan-only 発火、Sandbox: read-only / Full-Auto: off)
  - 明示 `[タスク種別] 実装` を含む task で auto は plan-only を発火しない (実装扱い維持)
  - `--approved` 指定時は workspace-write 維持
  - task_type_inference 関連テスト 8 件 PASS 維持
  - `bats codex_role_intent` 6 件 PASS 維持

### W-3（size: S / axis-3）: helix-sprint complete state seed

- 実装対象: `cli/helix-test` (test 622 直前で sprint state を「.5 完了直前」に seed)。
- 担当: pg --thinking medium。
- DoD:
  - test 622 PASS (`helix gate G4` 文字列が complete 出力に含まれる)
  - seed する状態は `.5` ステップが残っており complete 実行で gate G4 guidance を誘導できる状態 (current_step=completed ではない)
  - sprint 関連 self-test の regression なし

### W-4（size: M / axis-4）: allowed-files 並列誤検出

- 実装対象: `cli/lib/codex_post_validation.py` (load_newer_baselines を own_baseline 前後の両方向で拾うよう拡張)。
- 担当: SE --thinking high。
- DoD:
  - 3 並列 helix-codex 実行で stderr の `allowed-files 外の変更を検出` warning 0 件。
  - **false negative 防止**: 古い (own_baseline mtime 以前の) baseline によって本来 violation すべき tracked 変更が ambiguous_tracked に隠されない。
  - **new untracked は concurrent baseline があっても reject される** (untracked file は self-only と判断、ambiguous_tracked から除外する現行ロジックを維持)。
  - 関連 pytest test 5 件 + bats 3 件 PASS 維持 + 上記 2 条件の新規 test 追加 (concurrent baseline で隠されないこと、untracked が reject されること)。
- 非対象 (PLAN-033 候補): baseline ファイル名に PID を含める / crash cleanup / 監査機能追加。

### W-5（size: S / docs-only）: tests/ vs cli/lib/tests/ 役割境界文書化

- 対象: `docs/architecture/test-layout.md`（新規）に役割境界を docs-only で記述。
- 担当: pg --thinking low。
- スコープ: **docs-only**。物理重複ファイルの削除・移動は本 PLAN 非対象 (別 PLAN で扱う)。
- DoD:
  - 役割境界 (project-root `tests/` = catalog 公開挙動 + migration end-to-end / `cli/lib/tests/` = unit) が `docs/architecture/test-layout.md` に記述されている。
  - 既存 pytest / bats regression が PASS 維持 (コード変更なし)。
- 非対象 (PLAN-033 候補): tests/ 重複ファイル物理削除、ディレクトリ統合。

### W-6（size: S / 統合）: 統合、retro、completed 遷移

- 担当: Opus（受入・統合判定のみ、ファイル更新は docs/pg へ route）。
- DoD:
  - `cli/helix-test` failed 件数を 0 に収束 (現 7 → 0、shell-based 597 + W-3 seed 影響を許容)。
  - retro 反映 (`.helix/retros/PLAN-032.md` 新規作成は pg/docs 委譲)。
  - PLAN-031 retro `.helix/retros/PLAN-031.md` の Try セクションに resolved 状態追記 (pg/docs 委譲)。
  - `PLAN-032` frontmatter `status: draft → completed` (Opus 直接 Edit 可、軽量更新のため例外として PM が実施)。

## §5 受入条件

- §4 全 DoD 達成。
- PLAN-031 retro carry 2 件を resolved 化。
- `PLAN-031` carry 反映: `.helix/retros/PLAN-031.md` の Try セクションへ resolved 状態追記。

## §6 関連リンク

- PLAN-028: [docs/plans/PLAN-028-helix-v2-orchestration.md](PLAN-028-helix-v2-orchestration.md)
- PLAN-029: [docs/plans/PLAN-029-helix-rigor-expansion.md](PLAN-029-helix-rigor-expansion.md)
- PLAN-030: [docs/plans/PLAN-030-carry-consolidation.md](PLAN-030-carry-consolidation.md)
- PLAN-031: [docs/plans/PLAN-031-carry-resolution.md](PLAN-031-carry-resolution.md)
- ADR-014: [docs/adr/ADR-014-roles-config-format.md](../adr/ADR-014-roles-config-format.md)
- ADR-015: [docs/adr/ADR-015-helix-v2-orchestration.md](../adr/ADR-015-helix-v2-orchestration.md)
