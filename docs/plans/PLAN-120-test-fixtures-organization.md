---
plan_id: PLAN-120
title: test fixtures 整理 (cli/lib/tests/fixtures/ 共通 fixture 集約)
status: draft
kind: refactor
drive: be
layer: L4
size: S
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .1 重複 fixture 検出・分類・集約対象特定"
  - role: se
    slot_label: "SE — Sprint .2 fixtures/ dir 整理・共通 fixture 切り出し実装"
  - role: qa
    slot_label: "QA — Sprint .3 全 test PASS 検証・import 整合確認"
generates:
  - artifact_type: python_module
    path: cli/lib/tests/fixtures/__init__.py
  - artifact_type: python_module
    path: cli/lib/tests/fixtures/helix_home.py
  - artifact_type: python_module
    path: cli/lib/tests/fixtures/helix_db.py
  - artifact_type: python_module
    path: cli/lib/tests/fixtures/handover.py
dependencies:
  requires: []
  blocks: []
  parent: null
related_adr: []
related_docs:
  - docs/plans/PLAN-102-pytest-xdist-parallel-isolation.md
  - docs/plans/PLAN-118-test-coverage-improvement.md
  - cli/lib/tests/conftest.py
acceptance_criteria:
  - "fixtures/ 配下に共通 fixture が集約され、各 test が from .fixtures.X import Y で参照できる"
  - "重複 fixture が 50% 以上削減されている (Sprint .1 の実数を基準)"
  - "全 test PASS 維持 (regression なし)"
  - "pytest collection stop が発生しない (conftest.py 整合)"
  - "fixtures/ の各 file が py_compile PASS"
---

# PLAN-120: test fixtures 整理 (cli/lib/tests/fixtures/ 共通 fixture 集約)

## L2 凍結 (ADR snapshot)

本 PLAN は **test 整理 / refactor** であり、L2 大局判断を含まない。
ADR snapshot **不要**。

根拠: fixtures/ 集約は既存 pytest fixture 分離 pattern の適用であり、
新 framework 採用・fail-close 化・外部仕様採用などの L2 大局判断を含まない。

## 背景

`cli/lib/tests/` 配下には 100+ 件の test file が存在し、以下の重複が多い:

- `HELIX_HOME` / `HELIX_DB_PATH` 環境変数 setup fixture
- `helix.db` 初期化 fixture (migration 実行 + test data 投入)
- handover state 初期化 fixture
- tmp_path ベースの作業ディレクトリ fixture

**問題**:

1. **保守性低下**: 同一 fixture が複数 test file に copy-paste されており、
   fixture の仕様変更時に全ファイルを修正する必要がある
2. **conftest.py 肥大化リスク**: PLAN-102 (xdist 対応) で conftest.py に
   session-scoped fixture を追加したが、このまま fixture を conftest.py に
   集中させると可読性が低下する
3. **新規 test 追加の摩擦**: 「どの fixture を使えばよいか」が分からず、
   重複 fixture をコピーして追加する傾向が続く

**目標**: `cli/lib/tests/fixtures/` 配下に共通 fixture を topic 別に集約し、
test file から `from .fixtures.X import Y` で参照できる構造を確立する。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は **pytest fixture の標準 pattern 適用** であり、外部ライブラリへの
新規依存なし。WebSearch **skip**。

skip 理由: fixtures/ サブディレクトリへの集約は pytest 公式 conftest.py
分割 pattern の直接適用。pytest 公式 doc は既知であり、外部業界 standard
への新規参照は不要。

## 設計方針

### fixtures/ サブディレクトリ構造

```
cli/lib/tests/
├── conftest.py          # session-scoped + xdist fixture (PLAN-102 で追加)
├── fixtures/
│   ├── __init__.py      # 空 or re-export
│   ├── helix_home.py    # HELIX_HOME / HELIX_DB_PATH setup fixture
│   ├── helix_db.py      # helix.db 初期化 fixture (migration + test data)
│   └── handover.py      # handover state 初期化 fixture
└── test_*.py            # 各 test file: from .fixtures.X import Y
```

### fixture の分割方針

| file | 収録 fixture | scope |
|---|---|---|
| `fixtures/helix_home.py` | `helix_home_tmp`, `helix_env_vars` | function または session |
| `fixtures/helix_db.py` | `helix_db_path`, `helix_db_initialized`, `helix_db_with_data` | function または session |
| `fixtures/handover.py` | `handover_current_json`, `handover_clean_state` | function |

### conftest.py との分担

- `conftest.py`: xdist 対応 session-scoped fixture (PLAN-102 で追加)、
  pytest plugin 登録 (sys.path 調整)
- `fixtures/*.py`: topic 別 function-scoped fixture
- test file: `from .fixtures.X import fixture_name` で明示 import

### 後方互換方針

- 既存 test file への変更は最小化: 集約後も既存 fixture name を維持する
- conftest.py の既存 fixture は維持し、fixtures/ に同名 fixture を追加した後で
  conftest.py 側を deprecated として次 sprint で削除 or そのまま共存

## 実装計画

### Sprint .1: 重複 fixture 検出 + 集約対象特定 (PMO Sonnet 委譲、size XS)

**目的**: 全 fixture を列挙し、重複パターンと集約対象を特定する。

実施内容:

1. `grep -rn "@pytest.fixture" cli/lib/tests/*.py` で全 fixture を列挙
2. fixture name 別に出現 file 数を集計 (重複件数の多い順)
3. 上位 10 fixture について:
   - fixture の実装内容 (setup/teardown) を確認
   - 同一内容かどうかを判定 (完全一致 vs 微差あり)
   - fixtures/ 集約の適否を判定
4. 集約対象 fixture リストと配置先 file (helix_home / helix_db / handover) を決定
5. 本 PLAN §重複 fixture 一覧 (Sprint .1 更新) に追記

Sprint .1 完了条件:

- 全 fixture 名と出現ファイル数が判明
- 集約対象 fixture リストが確定 (最低 5 件以上)
- fixtures/ 内の file 構成が確定

### Sprint .2: fixtures/ dir 整理 + 共通 fixture 実装 (Codex se 委譲、size S)

**目的**: Sprint .1 の集約対象を `fixtures/` 配下に実装し、test file を更新する。

実施内容:

1. `cli/lib/tests/fixtures/` ディレクトリ新規作成
2. `fixtures/__init__.py` (空 file)
3. `fixtures/helix_home.py` — HELIX_HOME / HELIX_DB_PATH setup fixture 実装:

   ```python
   # cli/lib/tests/fixtures/helix_home.py
   import os
   import pytest

   @pytest.fixture
   def helix_home_tmp(tmp_path):
       """HELIX_HOME を tmp_path に設定する function-scoped fixture"""
       original = os.environ.get("HELIX_HOME")
       os.environ["HELIX_HOME"] = str(tmp_path)
       yield tmp_path
       if original is None:
           os.environ.pop("HELIX_HOME", None)
       else:
           os.environ["HELIX_HOME"] = original
   ```

4. `fixtures/helix_db.py` — helix.db 初期化 fixture 実装
5. `fixtures/handover.py` — handover state fixture 実装
6. 集約対象 test file の import を `from .fixtures.X import Y` に更新
   (対象は Sprint .1 で特定した重複件数上位 file から着手)

mandatory:
- `python3 -m py_compile cli/lib/tests/fixtures/*.py` PASS
- 変更した test file の直接実行 `pytest cli/lib/tests/test_X.py -v` PASS

Sprint .2 完了条件:

- `fixtures/` 配下に 3 file + __init__.py が存在
- 集約対象 fixture が fixtures/ に実装済
- 変更した test file が直接実行で PASS

### Sprint .3: 全 test PASS 検証 + import 整合確認 (Codex qa 委譲、size XS)

**目的**: fixtures/ 集約後の全 test PASS と import 整合を確認する。

実施内容:

1. `python3 -m pytest cli/lib/tests/ -q --tb=short` 全回帰
2. pytest collection stop が発生しないことを確認
   (`Collecting ... stop` が出ないことを出力で確認)
3. `helix code stats --uncovered --scope core5` で coverage 変化なし確認
4. `helix doctor` pass 件数・fail 0 件維持確認
5. 重複 fixture 削減数を集計 (目標: Sprint .1 実数の 50%+ 削減)

Sprint .3 完了条件:

- 全 test PASS (regression なし)
- pytest collection stop 0 件
- helix doctor fail 0 件維持

## 重複 fixture 一覧 (Sprint .1 更新予定)

本 PLAN 起票時点では `grep` 実行前の推定:

| fixture name (推定) | 推定出現 file 数 | 集約先 |
|---|---|---|
| `helix_home` / `helix_env` 系 | 高 (~15 file) | fixtures/helix_home.py |
| `helix_db_path` / `db_init` 系 | 高 (~20 file) | fixtures/helix_db.py |
| `handover_json` / `handover_state` 系 | 中 (~8 file) | fixtures/handover.py |
| `tmp_helix_dir` 系 | 中 (~10 file) | fixtures/helix_home.py |

注: 数値は Sprint .1 の grep 前の推定値。Sprint .1 で実数に更新する。

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/tests/fixtures/*.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/ -q --tb=short` 全回帰 PASS
- [ ] pytest collection stop 0 件確認
- [ ] helix doctor fail 0 件維持
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] commit message に `PLAN-120 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `cli/lib/tests/fixtures/` ディレクトリが存在し、3 topic file + __init__.py を含む
- [ ] 共通 fixture が `fixtures/*.py` に集約済
- [ ] 集約対象 test file が `from .fixtures.X import Y` で import 済
- [ ] 重複 fixture が Sprint .1 実数の 50%+ 削減
- [ ] 全 test PASS (regression なし)
- [ ] pytest collection stop 0 件
- [ ] helix doctor fail 0 件維持
- [ ] `python3 -m py_compile cli/lib/tests/fixtures/*.py` 全 PASS

## carry / 学び (起票時記録、Sprint 進行で更新)

- **conftest.py との役割分担**: session-scoped fixture (PLAN-102 追加) は conftest.py に
  残し、function-scoped fixture のみ fixtures/ に集約する。conftest.py を
  fixtures/ に移動しない (pytest の conftest.py 自動探索が前提)
- **__init__.py の要否**: pytest fixture を `from .fixtures.X import Y` で import するには
  `cli/lib/tests/` が package (= __init__.py あり) である必要あり。Sprint .1 で
  `cli/lib/tests/__init__.py` の存在確認必須。不在の場合は conftest.py に
  `sys.path` 調整が必要
- **PLAN-102 との関係**: xdist 対応 session-scoped fixture は conftest.py に配置済 (PLAN-102)。
  本 PLAN は function-scoped fixture のみを対象とし、conftest.py の session fixture には
  触れない
- **段階的移行**: 全 test file を一度に更新するのではなく、重複件数の多い fixture から
  順に移行する。全移行は複数 sprint にまたがる可能性があり、その場合は
  PLAN-120-followup として carry する

## 関連 reference

- PLAN-102 (pytest-xdist 並列化、conftest.py session-scoped fixture の前提)
- PLAN-118 (test coverage improvement、本 PLAN の保守性改善は coverage 追加を容易にする)
- cli/lib/tests/conftest.py (本 PLAN と協調する file)
- [[feedback_pytest_collection_stop_false_fail]] (collection stop 解消の前提確認)
