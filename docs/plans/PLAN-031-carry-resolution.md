---
plan_id: PLAN-031
title: HELIX v2/30 carry 解消
status: completed
created: 2026-05-09
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
acceptance:
  - W-1 (skill_recommender の CODEX_BIN unset) で `cli/helix-test` の self-test「codex allowed-files rejects out-of-scope new file」が PASS。
  - W-2 (claude shim guard 強化テスト) で `cli/tests/test-helix-codex.bats` の既存 2 ケース (raw override evidence / allow flag lacks reason) と重複しない差分ケース (HELIX_CLAUDE_INTERNAL=1 / 通常呼び出し誘導) を追加し全 PASS。
  - W-3 (test_code_catalog 4 failed 解消) で project-root の `pytest tests/test_code_catalog.py` が 0 failed。
  - `.helix/retros/PLAN-030.md §Try PLAN-031候補 1/2/3` が resolved 状態に遷移。
  - 既存 regression: `pytest cli/lib/tests/` と `bats cli/tests` が PASS (件数は実行時の baseline を維持)。
related: [PLAN-030, PLAN-028, PLAN-029, ADR-014, ADR-015]
---

## §1 背景・前提

PLAN-030 完遂時点で、carry として残存した以下 3 件を PLAN-031 へ集約する。

- PLAN-030 W-2 carry: `skill_recommender` の `CODEX_BIN` 継承解消
- PLAN-028 retro Try: `raw claude shim` の `HELIX_CLAUDE_INTERNAL` guard 追加検証
- PLAN-013 起因の `tests/test_code_catalog.py` 回帰失敗 4 件の解消

本 PLAN は PLAN-030 の carry 候補を 1 文書で収束し、再発防止までを含む実装計画として定義する。

## §2 スコープ

### §2.1 対象

- skill_recommender の `CODEX_BIN` 解除（子プロセス helix-codex 呼び出し時）
- raw claude shim guard の bats テスト強化（本体は変更せず、既存バリデーションを確認）
- `tests/test_code_catalog.py` の 4 件 failed 解消
- PLAN-030 retro #1 / #2 / #3 の resolved 遷移

### §2.2 非対象

- TUI / Web ダッシュボード（PLAN-029 W-10 §6 の将来検討）
- Codex 役割追加分類（PLAN-030 W-3 で構造的に解消済み扱い）
- tests/ と cli/lib/tests/ の最終統合方針は `§3 axis-3` で判断し、テスト実装の最小変更を前提とする

## §3 axis-by-axis 設計

### axis-1: skill_recommender 実行モデル

- 対象: `cli/lib/skill_recommender.py`
- 方針: `skill_recommender` がヘルパーとして呼ぶ `helix-codex` 子プロセスへ、`CODEX_BIN` を受け渡さない。
- 狙い: 親の baseline 取得前にモック・悪性実行先を起こすケースを回避し、`cli/helix-test` の self-test を正しく検知対象化する。
- リスク: 呼び出し側が明示で `CODEX_BIN` を要求する経路との整合を確認（`tests` と最小影響の範囲外）。

### axis-2: claude shim 制御

- 対象: `cli/tests/test_claude_shim_guard.bats`（新規 or 既存 bats の拡張）
- 方針: 本体実装は原則変更しない。
- 追加観点:
  - 通常呼び出しは `helix claude --dry-run` へ誘導
  - `HELIX_CLAUDE_INTERNAL=1` で生 claude 呼び出しを許可
  - `HELIX_ALLOW_RAW_CLAUDE=1` + `HELIX_RAW_CLAUDE_REASON=<理由>` で生 claude 呼び出しを許可
  - `HELIX_ALLOW_RAW_CLAUDE=1` のみは拒否
- 狙い: guard の防御順序（内部フラグ > 例外理由 > デフォルト拒否）を明文化。

### axis-3: pytest 重複構造の統治

- 対象: `tests/test_code_catalog.py`（project-root `tests/`）および `cli/lib/tests/`（既存 963 件）
- 現状認識:
  - `cli/lib/helix_db.py` の `CURRENT_SCHEMA_VERSION = 19`、v10→v19 まで段階的 migration 関数が存在
  - `tests/test_code_catalog.py::test_migration_v14_to_v15_idempotent` は legacy v14 schema を作成 → `migrate()` 呼び出しを期待するが、現行 `migrate()` は v14→v19 まで一気に進める
  - 失敗理由: v15→v16 段 (`_migrate_skill_usage_v5` 系) で `skill_usage` テーブルへ `session_id` 列を ALTER しようとするが、legacy v14 schema には `skill_usage` 自体が未作成のため `no such table: skill_usage` で raise
- 方針:
  - 修正は最小限とし `cli/lib/helix_db.py` の migration を v14 schema 由来でも安全に v19 まで通すこと (idempotent + create-if-missing パターン)
  - `tests/test_code_catalog.py` の各テスト 4 件は v14→v19 全段 migration 通過後を assert する形へ揃える (test 側の最小修正で吸収可)
  - `tests/` と `cli/lib/tests/` の役割境界 (root tests = catalog 公開挙動 / cli/lib/tests = unit) を W-3 完了時に短い記述として残す (PLAN-031 §3 axis-3 末尾 or W-3 DoD コメント)

## §4 Sprint plan（W-1..W-4）

- W-1（size: M / axis-1）: skill_recommender で子 `helix-codex` 呼び出し時に `CODEX_BIN` を unset
  - 実装: `cli/lib/skill_recommender.py`
  - テスト: `cli/helix-test` 自動テスト「`codex allowed-files rejects out-of-scope new file`」を PASS
  - DoD:
    - `subprocess` 呼び出し env から `CODEX_BIN` が明示的に除外
    - 関連既存テスト `cli/lib/tests/test_skill_recommender*` の PASS 維持
    - 自己テスト 1 件が Fail → Pass

- W-2（size: S / axis-2）: raw claude shim guard テスト追加
  - 実装ファイル: `cli/tests/test-helix-codex.bats` を拡張 (新規 bats 作成は禁止、既存ファイルへの差分追加のみ)
  - 既存ケース (重複追加禁止):
    - `claude shim allows explicit raw override with evidence` (HELIX_ALLOW_RAW_CLAUDE=1 + REASON)
    - `claude shim blocks raw invocation when allow flag lacks reason`
  - 追加ケース (差分のみ、現行 `cli/claude` 実装に合致):
    1. `HELIX_CLAUDE_INTERNAL=1` で raw claude を通過 (PMO 内部経路、`exec real_claude` ルート)
    2. env なしで raw claude を呼ぶと exit 64 + "[helix] raw claude is blocked. Use 'helix claude --role <role> ...' instead." を stderr に出力
  - DoD:
    - bats 2 ケース新規追加・PASS (`cli/tests/test-helix-codex.bats` 内)
    - shim 本体 (`cli/claude`) 変更なし、現状振る舞い維持
    - 既存 2 ケースとの重複なし

- W-3（size: M / axis-3）: `tests/test_code_catalog.py` の 4 failed 解消
  - 実装: `cli/lib/helix_db.py` (migration を v14 schema 由来でも安全に v19 まで通す create-if-missing 化) を主、`tests/test_code_catalog.py` 側の最小調整は許容
  - 期待挙動: legacy v14 schema → `migrate()` → v19 まで一気に上昇しても全段で `no such table` 等を起こさない
  - DoD:
    - `pytest tests/test_code_catalog.py` が 0 failed (4 件 → 0 件)
    - 4 失敗再現ケース (test_default_seed_metadata_for_three_buckets / test_filter_by_seed_candidate_true / test_summary_seed_candidate_count_present / test_migration_v14_to_v15_idempotent) を再発しない
    - `pytest cli/lib/tests/` 全 PASS 維持 (現 baseline 963)
    - `tests/` と `cli/lib/tests/` の役割境界記述を §3 axis-3 末尾 or W-3 commit msg に残す

- W-4（size: S / 統合）: 統合検証 + retro + 完了申請
  - 担当: Opus (PM統合 + 完了判定のみ、コード実装なし)
  - DoD:
    - 統合再実行: `pytest cli/lib/tests/`、`bats cli/tests`、`pytest tests/`、`helix doctor`
    - `.helix/retros/PLAN-030.md §Try PLAN-031候補 1/2/3` を resolved 化 (note 追加 or PLAN-031 retro でクロスリンク)
    - `.helix/retros/PLAN-031.md` を新規作成 (Keep/Problem/Try)
    - PLAN-031 frontmatter `status: draft → completed` に更新

## §5 受入条件（PLAN-030 retrospective 解決条件）

### 5.1 carry 解消条件

参照先: `.helix/retros/PLAN-030.md §Try (次回試すこと) > PLAN-031 候補`

- PLAN-031 候補 1 (skill_recommender CODEX_BIN 継承の解消) resolved
- PLAN-031 候補 2 (raw claude shim HELIX_CLAUDE_INTERNAL guard 強化テスト) resolved
- PLAN-031 候補 3 (project-root tests/test_code_catalog.py 4 failed の解消) resolved

### 5.2 機能受入条件（本 PLAN）

- W-1: self-test の out-of-scope new file 判定が PASS
- W-2: `HELIX_CLAUDE_INTERNAL` guard bats が PASS
- W-3: `tests/test_code_catalog.py` の 4件失敗が解消
- W-4: 既存テスト群（`pytest cli/lib/tests/` / `bats cli/tests`）が回帰なし
- W-4: PLAN-031 draft → completed への更新と関連 retro 反映

## §6 関連リンク

- PLAN-028: [docs/plans/PLAN-028-helix-v2-orchestration.md](PLAN-028-helix-v2-orchestration.md)
- PLAN-029: [docs/plans/PLAN-029-helix-rigor-expansion.md](PLAN-029-helix-rigor-expansion.md)
- PLAN-030: [docs/plans/PLAN-030-carry-consolidation.md](PLAN-030-carry-consolidation.md)
- ADR-014: [docs/adr/ADR-014-roles-config-format.md](../adr/ADR-014-roles-config-format.md)
- ADR-015: [docs/adr/ADR-015-helix-v2-orchestration.md](../adr/ADR-015-helix-v2-orchestration.md)
- 対象コード: `cli/lib/skill_recommender.py`
- 対象テスト: `cli/helix-test` (W-1 self-test)、`cli/tests/test-helix-codex.bats` (W-2 既存 bats 拡張)、`tests/test_code_catalog.py` (W-3)
