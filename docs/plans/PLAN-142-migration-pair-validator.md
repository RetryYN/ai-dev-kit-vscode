---
plan_id: PLAN-142
title: "PLAN-142: helix.db schema migration validator (up/down/verify ペア整合)"
kind: impl
layer: L4
drive: be
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
created: 2026-05-23
owner: PMO
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — 設計レビュー・既存 migration 形式の整合確認"
  - role: se
    slot_label: "SE — cli/lib/migration_validator.py AST 解析実装 + helix doctor 統合 + テスト"
  - role: qa
    slot_label: "QA — pytest unit test 設計・実装"
generates:
  - artifact_path: cli/lib/migration_validator.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_migration_validator.py
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_adr: []
related_plans:
  - PLAN-132
related_docs:
  - cli/lib/helix_db.py
  - cli/lib/helix_doctor.py
  - cli/helix-doctor
---

# PLAN-142: helix.db schema migration validator (up/down/verify ペア整合)

> **kind**: impl (新規 Python module + helix doctor 統合)
> **layer**: L4 (実装フェーズ。AST 解析 helper + doctor check 追加 + unit test)
> **drive**: be (CLI / Python helper 実装中心)
> **本 PLAN の役割**: PLAN-132 (helix-db migration test framework) と並列で、各 migration class に `up()` / `down()` / `verify()` 3 method が揃っているかを AST 解析で機械チェックし、欠落を fail-close する validator を実装する。

---

## §0. 本 PLAN の位置付け

`cli/lib/helix_db.py` に蓄積されている schema migration は現行 (v35+) で 35 件超。各 migration は `up()` / `down()` の 2 method が基本形だが、以下の問題がある:

1. **verify() 欠落**: 適用後の状態検証を担う `verify()` method が多くの migration で未実装または空実装
2. **down() 欠落**: rollback 手段がない migration が混在しており、PLAN-086 (helix db rollback) の安全運用を妨げる
3. **機械検証の不在**: migration を追加するたびに手動で 3 method 確認が必要。CI/helix doctor での自動検出がない

本 PLAN で `cli/lib/migration_validator.py` を新規作成し、以下を提供する:

- migration class ごとの `up()` / `down()` / `verify()` 存在確認 (AST 解析)
- helix doctor 統合 (`check_migration_pair` として追加)
- 欠落があれば `helix doctor` の fail 扱いにする (fail-close)

### WebSearch skip 根拠

本 PLAN は Python AST モジュール (標準ライブラリ) を使った内部 lint ツールの追加。外部ライブラリへの新規依存なし。PLAN-087 ガードレール「設計 doc 新規起票・大幅 scope 変更時」に非該当。**WebSearch skip: 標準ライブラリ AST 使用、新技術採用なし**。

---

## §1. 目的

1. `cli/lib/migration_validator.py` を新規作成し、Python AST でmigration class の 3 method 存在を検証する (Sprint .1)
2. `cli/lib/helix_doctor.py` に `check_migration_pair` を追加し、validator を helix doctor に統合する (Sprint .2)
3. unit test を追加して validator の動作を保証する (Sprint .3)

---

## §2. 背景・詳細

### 2.1 migration の現行形式

`cli/lib/helix_db.py` の migration class は以下のパターンを想定:

```python
class MigrationV32:
    version = 32
    description = "..."

    def up(self, conn: sqlite3.Connection) -> None:
        ...  # schema 変更

    def down(self, conn: sqlite3.Connection) -> None:
        ...  # rollback

    def verify(self, conn: sqlite3.Connection) -> bool:
        ...  # 適用後の状態確認、True = OK
```

上記 3 method が揃っていることを AST 解析で確認する。

### 2.2 migration_validator.py の設計

```python
# cli/lib/migration_validator.py

from __future__ import annotations
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple


@dataclass
class MigrationInfo:
    class_name: str
    version: int | None
    has_up: bool = False
    has_down: bool = False
    has_verify: bool = False

    @property
    def is_complete(self) -> bool:
        return self.has_up and self.has_down and self.has_verify

    @property
    def missing_methods(self) -> list[str]:
        missing = []
        if not self.has_up:
            missing.append("up")
        if not self.has_down:
            missing.append("down")
        if not self.has_verify:
            missing.append("verify")
        return missing


def parse_migrations(source_path: Path) -> list[MigrationInfo]:
    """Python ファイルを AST 解析して migration class の情報を返す。"""
    ...


def validate_migration_pairs(source_path: Path) -> list[str]:
    """3 method が揃っていない migration class を error として返す。
    
    Returns:
        error メッセージのリスト。空リストは全件 OK を意味する。
    """
    ...
```

### 2.3 helix doctor 統合

`cli/lib/helix_doctor.py` の `check_*` 関数群に `check_migration_pair` を追加:

```python
def check_migration_pair(db_path: Path | None = None) -> CheckResult:
    """helix_db.py の全 migration class で up/down/verify 3 method が揃っているか確認。"""
    from cli.lib.migration_validator import validate_migration_pairs
    helix_db_py = Path(__file__).parent / "helix_db.py"
    errors = validate_migration_pairs(helix_db_py)
    if errors:
        return CheckResult(status="fail", messages=errors)
    return CheckResult(status="pass", messages=[])
```

本 check は fail-close (errors があれば `helix doctor` の fail 件数に加算される)。

### 2.4 既存 migration の扱い

初回導入時、既存 migration に `verify()` が未実装なものが多い場合は、`helix doctor` で一括 fail が発生する可能性がある。このため:

- Sprint .2 で doctor 統合後、初回実行で fail 件数を確認する
- 既存 migration への `verify()` stub 追加は **本 PLAN のスコープ外** とし、別途 PLAN を起票する (§8 リスク参照)
- 初回は warn 扱い (advisory) から開始し、新規追加 migration のみ fail-close とする 2 段階導入を Sprint .2 で選択可能にする

---

## §3. 実装計画

### Sprint .1: migration_validator.py 実装 (Codex se 委譲)

**Entry 条件**: `cli/lib/helix_db.py` の migration class 形式を Read して確認済

実施内容:

1. `cli/lib/migration_validator.py` 新規作成
   - `parse_migrations(source_path)`: AST でクラス名 / version 属性 / method 名を抽出
   - `validate_migration_pairs(source_path)`: 3 method 未実装のクラスを error として列挙
2. `python3 -m py_compile cli/lib/migration_validator.py` PASS
3. `cli/lib/helix_db.py` に対して実行し、現行の欠落状況を確認

Sprint .1 完了条件:

- `validate_migration_pairs(Path("cli/lib/helix_db.py"))` が実行できる
- 欠落 method のエラーメッセージが `"MigrationVXX: missing methods: [verify]"` 形式で出力される

### Sprint .2: helix doctor 統合 (Codex se 委譲)

**Entry 条件**: Sprint .1 完了 + `cli/lib/helix_doctor.py` の `check_*` 追加パターンを Read 済

実施内容:

1. `cli/lib/helix_doctor.py` に `check_migration_pair()` を追加
2. `helix doctor` の check リストに登録 (check 名: `check_migration_pair`)
3. 初回実行で fail 件数が過大な場合は advisory (warn) モードで段階導入
4. `python3 -m py_compile cli/lib/helix_doctor.py` PASS
5. `helix doctor` 実行で `check_migration_pair` が表示されることを確認

Sprint .2 完了条件:

- `helix doctor` 出力に `check_migration_pair` の結果が含まれる
- `helix doctor` の既存 pass 件数が Sprint .1 時点以上 (regression なし)

### Sprint .3: unit test + regression 確認 (Codex qa 委譲)

**Entry 条件**: Sprint .1/.2 完了

実施内容:

1. `cli/lib/tests/test_migration_validator.py` 新規作成
   - `test_complete_migration`: 3 method 揃いの class → error なし
   - `test_missing_down`: `down()` 欠落の class → error に "down" を含む
   - `test_missing_verify`: `verify()` 欠落の class → error に "verify" を含む
   - `test_missing_all`: 3 method 全欠落 → error に 3 method 全て含む
   - `test_up_only`: `up()` のみの class (最小形) → down / verify の欠落を検出
   - `test_parse_version`: `version = 32` 属性の抽出が正確か確認
2. `python3 -m pytest cli/lib/tests/test_migration_validator.py -q` 全 PASS
3. `python3 -m pytest cli/lib/tests/test_helix_doctor.py -q` 全 PASS (regression なし)

Sprint .3 完了条件:

- test_migration_validator 6 件全 PASS
- test_helix_doctor 全 PASS (check_migration_pair 統合で regression なし)

---

## §4. 段階導入

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | migration_validator.py AST 解析実装 | se | `validate_migration_pairs()` が動作 / 欠落 method を検出 |
| **Sprint .2** | helix doctor 統合 (check_migration_pair) | se | `helix doctor` に check が表示 / regression なし |
| **Sprint .3** | unit test + regression 確認 | qa | test 6 件 PASS / doctor test 全 PASS |

---

## §5. デグレ禁止項目

1. `cli/lib/helix_db.py` は read-only (本 PLAN では編集しない。既存 migration への stub 追加は別 PLAN)
2. `cli/lib/helix_doctor.py` の既存 check 動作は変更しない (check_migration_pair を追加するのみ)
3. `helix doctor` の既存 pass 件数は維持または増加する (新 check が正常 migration に対して fail を出さない)
4. PLAN-132 (migration test framework) のスコープを侵食しない。本 PLAN は AST 静的解析のみ。動的テスト実行は PLAN-132

---

## §6. DoD (Definition of Done)

1. `cli/lib/migration_validator.py` が存在し、`parse_migrations()` / `validate_migration_pairs()` を提供する
2. `validate_migration_pairs(Path("cli/lib/helix_db.py"))` が実行でき、欠落 method を列挙する
3. `helix doctor` の check リストに `check_migration_pair` が含まれる
4. `python3 -m pytest cli/lib/tests/test_migration_validator.py -q` 全 PASS (6 件)
5. `python3 -m pytest cli/lib/tests/test_helix_doctor.py -q` 全 PASS (regression なし)
6. `python3 -m py_compile cli/lib/migration_validator.py` PASS
7. `python3 -m py_compile cli/lib/helix_doctor.py` PASS
8. `python3 cli/lib/plan_validator.py docs/plans/PLAN-142-*.md` が PASS

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-142-migration-pair-validator.md |
| ② 実装コード | Sprint .1〜.2 で実装 | cli/lib/migration_validator.py / cli/lib/helix_doctor.py |
| ③ テスト設計 | Sprint .3 entry で策定 | docs/v2/L4-test-design/PLAN-142-migration-validator-test-design.md (予定) |
| ④ テストコード | Sprint .3 で実装 | cli/lib/tests/test_migration_validator.py |

**双方向 reference**:

- 本 PLAN → 実装コード: `generates.artifact_path` に `cli/lib/migration_validator.py` を明記
- 実装コード → 本 PLAN: `migration_validator.py` の module docstring に「設計: PLAN-142」を追記
- 本 PLAN → テストコード: `generates.artifact_path` に `cli/lib/tests/test_migration_validator.py` を明記
- テストコード → 本 PLAN: test file docstring に「DoD 検証: PLAN-142 §6」を追記

---

## §8. 関連 PLAN / ADR

### 関連 PLAN

- PLAN-132: helix-db migration test framework (動的テスト実行が中核。本 PLAN は静的解析の補完)

### 関連 ADR

なし (標準ライブラリ AST 使用の内部 lint 追加。L2 大局判断なし)

---

## §9. リスク

| リスク | 緩和策 |
|---|---|
| 既存 migration に verify() が大量に未実装で helix doctor fail が激増する | Sprint .2 の初回実行で件数を確認。20 件超の fail が発生する場合は advisory (warn) モードで段階導入し、既存 migration への stub 追加を別 PLAN で並行起票する |
| helix_db.py の migration class 形式が標準形 (up/down/verify) 以外も混在する | Sprint .1 の `parse_migrations()` で class 名が `Migration` で始まる class のみを対象とし、その他は skip する条件を追加 |
| AST 解析が Python バージョン差異で失敗する | `ast.parse()` はメジャー Python 3.8+ で安定。py_compile で事前確認済みの file を対象とするため問題は最小 |
| PLAN-132 との機能重複 | 責務分離を明確化: 本 PLAN = AST 静的解析 (method 存在確認)、PLAN-132 = 動的テスト実行 (up/down/verify の実際の動作確認)。docs 参照で双方向 trace を保つ |

---

## §10. mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/migration_validator.py` PASS
- [ ] `python3 -m py_compile cli/lib/helix_doctor.py` PASS
- [ ] `python3 -m pytest cli/lib/tests/test_migration_validator.py -q` 全 PASS
- [ ] `python3 -m pytest cli/lib/tests/test_helix_doctor.py -q` 全 PASS (regression なし)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
