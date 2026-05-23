---
plan_id: PLAN-221
title: "rollback simulation framework (本番想定 dry-run rollback test)"
kind: impl
layer: L4
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-MM-001-v5-framework-master-plan.md   # from dependencies.parent
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: tl-advisor
    slot_label: "TL adversarial check — simulation 設計 (dry-run boundary / snapshot 方式) review"
  - role: se
    slot_label: "SE — rollback_simulator.py 実装・helix-db --simulate flag 統合"
  - role: qa
    slot_label: "QA — pytest test 設計・dry-run 非破壊性確認・整合性 report 検証"
  - role: pmo-sonnet
    slot_label: "PMO — PLAN-086 / PLAN-132 との整合確認・Sprint review"
generates:
  - artifact_type: python_module
    path: cli/lib/rollback_simulator.py
  - artifact_type: cli_extension
    path: cli/helix-db
  - artifact_type: test
    path: cli/lib/tests/test_rollback_simulator.py
dependencies:
  requires:
    - PLAN-086
    - PLAN-132
  blocks: []
  parent: PLAN-MM-001
related_adr: []
related_docs:
  - cli/lib/helix_db.py
  - cli/helix-db
  - docs/plans/PLAN-086-rollback-fault-injection-drill.md
  - docs/plans/PLAN-132-helix-db-migration-test-framework.md
acceptance_criteria:
  - "helix db rollback --simulate <version> が dry-run で変更内容レポートを出力する"
  - "helix db rollback --simulate <version> で helix.db の実データが変更されないこと"
  - "レポートに affected_tables / row_counts_before / row_counts_after (推定) / sql_statements が含まれる"
  - "helix db rollback --apply <version> で実 rollback が実行される (既存 PLAN-086 挙動維持)"
  - "--simulate なしの helix db rollback は既存の help / 引数パースと後方互換を維持する"
  - "python3 -m py_compile cli/lib/rollback_simulator.py PASS"
  - "pytest test_rollback_simulator.py 全 PASS"
---

# PLAN-221: rollback simulation framework (本番想定 dry-run rollback test)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **既存 PLAN-086 (helix db rollback) への dry-run 拡張** であり、
新規の大局判断 (新 framework 採用 / fail-close 化 / 外部仕様採用) を含まない。
ADR snapshot は不要。

根拠:
- 設計選択は「SQLite の BEGIN / ROLLBACK を使った dry-run」の一択
- CLI 体系は既存 `helix db rollback` への flag 追加であり、新エントリポイントは作らない
- schema 変更なし (simulation は in-memory で完結)

## 背景

PLAN-086 で `helix db rollback` は実装済だが、本番 helix.db に対して rollback を
試すのはリスクが高い。特に以下の問題がある:

1. **本番 helix.db での rollback リスク**: sprint 進行中に rollback コマンドを誤実行すると
   確定済み task / PLAN / audit log が消失するリスクがある
2. **migration の影響範囲が事前不明**: どのテーブルが何行変更されるかを
   rollback 前に確認する手段がなく、本番適用前の検証ができない
3. **自動テストでの回帰検証不足**: PLAN-132 (migration test framework) では
   migration の forward 検証は整備されているが、dry-run rollback の
   自動確認は未整備

`helix db rollback --simulate <version>` で dry-run rollback を実行し、
変更内容と整合性レポートを出力する framework を確立する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **HELIX 内部 CLI の既存コマンド拡張** であり、外部ライブラリへの新規依存なし。
WebSearch **skip**。

skip 理由:
- SQLite の BEGIN / ROLLBACK は標準 Python sqlite3 module のみ使用
- dry-run 設計は既存 PLAN-086 の `--dev-only` guard を拡張する pattern
- PLAN-132 の migration fixture 設計を再利用するため調査不要

## 設計方針

### dry-run の実現方式

SQLite の **transaction rollback** を利用する:

```python
# dry-run の骨格
conn = sqlite3.connect(db_path)
conn.execute("BEGIN")
try:
    # rollback SQL を実行 (実際の helix-db rollback logic を呼び出す)
    execute_rollback_sql(conn, target_version)
    report = build_report(conn, target_version)  # 変更後の状態を観測
finally:
    conn.execute("ROLLBACK")  # 必ず元に戻す
return report
```

この方式の利点:
- 実際の DB ファイルを変更しない (ROLLBACK で確実に元に戻る)
- 変更後の状態 (row_counts 等) を SELECT で観測できる
- BEGIN 〜 ROLLBACK 内であれば途中状態の読み取りが可能

### simulation レポート構造

```json
{
  "simulated_at": "2026-05-23T14:00:00Z",
  "target_version": 28,
  "current_version": 33,
  "dry_run": true,
  "affected_tables": ["plan_registry", "agent_slots"],
  "row_counts": {
    "plan_registry": {"before": 102, "after_estimate": 98},
    "agent_slots":   {"before": 45,  "after_estimate": 45}
  },
  "sql_statements": [
    "DROP TABLE IF EXISTS plan_dependencies",
    "ALTER TABLE plan_registry DROP COLUMN agent_slots"
  ],
  "data_integrity": {
    "foreign_key_violations": 0,
    "orphan_rows": 0
  },
  "warnings": []
}
```

### CLI インターフェース変更

既存の `helix db rollback` に以下の flag を追加する (後方互換維持):

```
helix db rollback [OPTIONS]

新規 flag:
  --simulate <version>   dry-run で変更内容レポートを出力 (DB 変更なし)
  --apply <version>      実 rollback を実行 (既存 --dev-only guard を継承)

既存 flag (変更なし):
  --help                 usage 表示
  --dev-only             本番 DB に対する誤実行を防ぐ guard (PLAN-086 実装済)
```

`--simulate` と `--apply` は排他。両方指定時はエラーで終了。

## 実装計画

### Sprint .1: rollback_simulator.py 実装 (Codex se 委譲)

実施内容:

1. `cli/lib/rollback_simulator.py` 新規作成:
   - `SimulationReport` dataclass
   - `simulate_rollback(db_path, target_version)` → SimulationReport
     - BEGIN → rollback SQL 実行 → SELECT で状態観測 → ROLLBACK の順
   - `format_report(report, fmt)` → str (json / text)
   - helix_db.py の既存 rollback logic を import して再利用
   - `python3 -m py_compile` PASS を mandatory とする

Sprint .1 完了条件:
- `py_compile` PASS
- `simulate_rollback` が fixture DB で SimulationReport を返す

### Sprint .2: helix-db `--simulate` flag 統合 (Codex se 委譲)

実施内容:

1. `cli/helix-db` の `rollback` サブコマンドに `--simulate` / `--apply` flag 追加:
   - `--simulate <version>` → rollback_simulator.py を呼び出し、レポート出力
   - `--apply <version>` → 既存 rollback 処理 (PLAN-086) に委譲
   - `--simulate` なしの `helix db rollback` は既存ヘルプを表示 (後方互換)
   - `bash -n cli/helix-db` PASS を mandatory とする

2. `helix db rollback --simulate` のヘルプ表示確認

Sprint .2 完了条件:
- `bash -n` PASS
- `helix db rollback --simulate <version>` でレポート出力
- `helix db rollback --apply <version>` で実 rollback (PLAN-086 既存動作維持)

### Sprint .3: pytest test (Codex qa 委譲)

対象: `cli/lib/tests/test_rollback_simulator.py`

| ケース | 内容 |
|---|---|
| T1-001 | simulate 後に helix.db の実データが変更されていない |
| T1-002 | SimulationReport に affected_tables / row_counts / sql_statements が含まれる |
| T1-003 | target_version が current_version 以上 → エラー終了 |
| T2-001 | affected_tables が正確 (fixture migration で対象テーブルを確認) |
| T2-002 | row_counts.before が現在の実 row 数と一致 |
| T3-001 | --simulate と --apply の排他チェック: 両方指定でエラー |
| T3-002 | --simulate なしの `helix db rollback` は既存 help を表示 (後方互換) |
| T4-001 | JSON format report のスキーマ: 全必須フィールド存在 |

mandatory in sprint:
- `pytest test_rollback_simulator.py -v` 全 8 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit、PLAN-086 / PLAN-132 整合確認含む)

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/rollback_simulator.py` PASS
- [ ] `bash -n cli/helix-db` PASS
- [ ] pytest `test_rollback_simulator.py` 全 PASS
- [ ] T1-001 (非破壊性) PASS 確認
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] tl-advisor adversarial check (Sprint .1 完了後、transaction 方式の安全性確認)
- [ ] commit message に `PLAN-221 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `cli/lib/rollback_simulator.py` 実装済、`py_compile` PASS
- [ ] `helix db rollback --simulate <version>` でレポート出力が動作する
- [ ] dry-run 実行後に helix.db の実データが変更されていない (T1-001 PASS)
- [ ] `helix db rollback --apply <version>` で実 rollback が動作する (PLAN-086 後方互換)
- [ ] `helix db rollback` (flag なし) が既存 help を表示する (後方互換)
- [ ] pytest 全 8 ケース PASS
- [ ] helix doctor pass 数が現行以上

## carry / 学び (起票時記録)

- Sprint .1 着手前に `cli/lib/helix_db.py` の既存 rollback logic を Read し、
  import 可能か確認する。CLI 直書きの場合は関数抽出を Sprint .1 scope に含める
- DDL (DROP TABLE / ALTER TABLE) は SQLite で ROLLBACK が戻せる保証がない。
  Sprint .1 の fixture テストで確認する
- PLAN-132 の sqlite fixture を `conftest.py` 経由で共有できるか Sprint .3 着手前に確認する

## 関連 reference

- PLAN-086 (helix db rollback 実装、本 PLAN の前提)
- PLAN-132 (helix db migration test framework、fixture 共有先)
- cli/lib/helix_db.py (SQLite access layer、rollback logic の正本)
- cli/helix-db (helix db サブコマンド、本 PLAN の拡張対象)
