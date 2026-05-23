---
plan_id: PLAN-107
title: helix.db lock 実装 refactor (per-worker isolation 前提確立)
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
kind: refactor
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
agent_slots:
  - role: se
    slot_label: "SE — lock 実装調査・refactor 実装・test_helix_db_lock_isolation.py 起草"
  - role: tl-advisor
    slot_label: "TL adversarial check — lock scope 設計・既存呼び出し元影響評価"
  - role: pmo-sonnet
    slot_label: "PMO — drift 整合確認・本 PLAN doc review"
generates:
  - artifact_type: python_module
    path: cli/lib/helix_db.py
  - artifact_type: test
    path: cli/lib/tests/test_helix_db_lock_isolation.py
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-036-helix-db-lock-refactor.md
dependencies:
  requires:
    - PLAN-102
  blocks: []
  parent: null
related_adr:
  - ADR-036-helix-db-lock-refactor
related_docs:
  - cli/lib/helix_db.py
  - docs/plans/PLAN-102-pytest-xdist-parallel-isolation.md
acceptance_criteria:
  - "cli/lib/ 配下で lock 実装箇所が特定され、設計が文書化されている"
  - "lock path が HELIX_HOME / 'helix-db.lock' に固定 (env HELIX_DB_LOCK_PATH override 可)"
  - "pytest-xdist per-worker HELIX_HOME 配下に lock file が自動分離されることを test_helix_db_lock_isolation.py で確認"
  - "既存 cli/helix-* 呼び出し元への影響評価が完了し regression なし"
  - "python3 -m py_compile cli/lib/helix_db.py PASS"
  - "既存 test suite 全 PASS (1846 passed / 4 skipped 維持)"
  - "ADR-036 snapshot 起票済"
---

# PLAN-107: helix.db lock 実装 refactor (per-worker isolation 前提確立)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-036** で凍結 (本実装前に起票):

- helix-db.lock の path 固定方針 (`HELIX_HOME / "helix-db.lock"`、env override 可)
- lock 実装技術選択 (python-filelock / fcntl / 現行方式継続) の判定
- lock scope の明示 (DB connection 単位 / file 単位 / process 単位)
- pytest-xdist per-worker 分離の自動化戦略 (HELIX_HOME env override 経由)

## 背景

PLAN-102 (pytest-xdist 並列化 + helix-db.lock per-worker fixture isolation) の
実装前提として、`helix.db` の lock 実装が per-worker isolation 可能であることを
保証する必要がある。

本 session (2026-05-23) での調査結果:

- `cli/lib/helix_db.py` への `flock` / `fcntl` / `filelock` の grep = **0 hit**
- `helix-db.lock` ファイルは SQLite ファイルと同ディレクトリに置かれる想定だが、
  lock 取得ロジックの実装場所が未確認
- pytest-xdist の per-worker `tmp_path` 化で自動的に isolation される **理屈** は
  成立するが、lock 実装の場所・設計を確定させないと PLAN-102 の Sprint .1 が
  依存先不明のまま着手できない

本 PLAN で lock 実装の全容を明確化し、refactor 完了後に PLAN-102 の実装基盤を
固める。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN 起票時点では内部 refactor (外部 standard 不要) のため WebSearch skip。
PLAN-102 で実施済 query を流用:

| Query (PLAN-102 実施済) | 抽出した知識 |
|---|---|
| pytest-xdist SQLite lock contention isolation 2026 | per-worker DB 命名 / tmp_path worker-aware fixture |
| pytest-xdist worker_id fixture SQLite per-worker isolation | session-scoped fixture で worker_id ベース path 割当 |
| SQLite WAL mode flock contention performance | WAL = 並列 read + 1 writer 許容、flock contention 大幅減 |

本 PLAN 固有の追加 query (`python-filelock vs fcntl best practice 2026`) は
Sprint .1 調査時に実施し、ADR-036 に証拠として記録する。

## 実装計画

### Sprint .1: lock 実装場所特定・設計確認 (Codex se 委譲、size S)

**目的**: 実装場所と現状設計を把握し、ADR-036 起票の材料を揃える。

実施内容:

```bash
# 実装場所特定
grep -rn "helix-db.lock\|fcntl\|flock\|filelock\|FileLock\|lockfile" \
  cli/lib/ cli/libexec/ scripts/ .claude/hooks/ 2>/dev/null

# helix_db.py の lock 関連 symbol を確認
grep -n "lock\|Lock\|LOCK" cli/lib/helix_db.py

# 呼び出し元 enumerate
grep -rn "helix-db.lock\|lock_path\|lockfile" cli/ 2>/dev/null
```

確認観点:

1. lock 実装技術: python-filelock / fcntl / 自作 / 実装なし の判定
2. lock の scope: DB connection 単位 / file 単位 / process 単位
3. lock path の現状: hardcode / env override 可 / HELIX_HOME 相対
4. 呼び出し元一覧と影響範囲
5. `helix-db.lock` が実際に存在するかの実行時確認:
   `ls -la $(dirname $(helix db path 2>/dev/null))/ 2>/dev/null | grep lock || echo "no lock file found"`

Sprint .1 完了条件:

- 調査結果を Sprint .2 設計方針に反映
- ADR-036 draft 起票 (採用技術 + scope + path 方針を記述)

### Sprint .2: refactor 設計確定 + ADR-036 凍結 (Opus 直接 + tl-advisor)

**目的**: lock 実装の refactor 設計を確定し、ADR-036 で凍結する。

設計方針 (Sprint .1 結果次第で調整):

```python
# cli/lib/helix_db.py (想定 refactor 後)
import os
from pathlib import Path

def _get_lock_path(db_path: str | Path | None = None) -> Path:
    """
    helix-db.lock の path を返す。
    優先順位:
      1. HELIX_DB_LOCK_PATH env (明示 override)
      2. db_path と同 dir の helix-db.lock
      3. HELIX_HOME / helix-db.lock (fallback)
    """
    if override := os.getenv("HELIX_DB_LOCK_PATH"):
        return Path(override)
    if db_path:
        return Path(db_path).parent / "helix-db.lock"
    helix_home = os.getenv("HELIX_HOME", str(Path.home() / ".helix"))
    return Path(helix_home) / "helix-db.lock"
```

設計確認観点:

- pytest-xdist の `HELIX_HOME = tmp_path_factory.mktemp(f"helix_home_{worker_id}")`
  により lock path が自動的に per-worker に分離されるか検証
- 既存 `cli/helix-*` (Bash) から lock path を使う場合の env 変数 propagation 確認
- tl-advisor 召喚: lock scope + env override 設計の adversarial check

Sprint .2 完了条件:

- ADR-036 が凍結済 (Sprint .1 draft → Sprint .2 accepted)
- refactor diff が明確 (どのファイルを何行変更するか特定)

### Sprint .3: 実装 + test 新規追加 (Codex se 委譲、size S)

**目的**: refactor 実装 + per-worker isolation を確認する test を追加。

実施内容:

1. `cli/lib/helix_db.py` の lock path 関数を `_get_lock_path()` に統一
2. `cli/lib/tests/test_helix_db_lock_isolation.py` 新規作成 (4 test case):
   - `test_lock_path_uses_helix_home_env`: HELIX_HOME env が lock path に反映される
   - `test_lock_path_explicit_override`: HELIX_DB_LOCK_PATH env が最優先される
   - `test_lock_path_follows_db_path`: db_path と同 dir に lock が置かれる
   - `test_per_worker_isolation_via_helix_home`: 2 worker が異なる HELIX_HOME を使うと lock path が分離される
3. mandatory in sprint 実行:
   - `python3 -m py_compile cli/lib/helix_db.py`
   - `pytest cli/lib/tests/test_helix_db_lock_isolation.py -v`
   - 既存 test 全体 `pytest cli/lib/tests/ -q` で regression 確認

Sprint .3 完了条件:

- `test_helix_db_lock_isolation.py` 全 case PASS
- 既存 1846 PASS / 4 skipped 維持
- `helix doctor` pass 数維持

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/helix_db.py`
- [ ] `pytest cli/lib/tests/test_helix_db_lock_isolation.py -v` 全 PASS
- [ ] `pytest cli/lib/tests/ -q` (serial, 全回帰) PASS
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .3 完了時)
- [ ] ADR-036 accepted 状態で exists
- [ ] commit message に `PLAN-107 sprint .X` 明示

## DoD (Definition of Done)

- [ ] lock 実装箇所が特定され、ADR-036 に文書化
- [ ] `_get_lock_path()` 関数が `HELIX_DB_LOCK_PATH` env override + db_path fallback で動作
- [ ] `cli/lib/tests/test_helix_db_lock_isolation.py` 全 case PASS
- [ ] pytest-xdist per-worker HELIX_HOME 分離で lock 衝突が 0 件になる構造が実証済
- [ ] 既存 test suite 1846 PASS / 4 skipped 維持 (regression なし)
- [ ] `helix doctor` pass 数維持
- [ ] ADR-036 snapshot 起票済 (accepted)
- [ ] PLAN-102 Sprint .1 が本 PLAN 完遂後に着手可能な状態であることを確認

## carry / 学び (起票時記録)

- **lock 実装が見つからない可能性**: `grep` 0 hit の原因が「実装なし (SQLite 組み込み
  locking のみ依存)」の場合、refactor ではなく「lock 明示化」の新実装になる。
  Sprint .1 で判定し、実装方針を ADR-036 に記録する
- **python-filelock vs fcntl**: python-filelock (portalocker ベース) は Windows/POSIX
  両対応、fcntl は POSIX 専用。HELIX は Linux/Mac 専用前提なら fcntl で十分
  だが、WSL2 環境での fcntl 動作確認が必要
- **PLAN-102 との実装順序**: 本 PLAN (PLAN-107) が先に完遂されるべき。
  PLAN-102 Sprint .1 の `helix-db.lock 実装位置特定` は本 PLAN Sprint .1 と
  重複する。本 PLAN 完遂後に PLAN-102 Sprint .1 をスキップして Sprint .2 から
  着手可能

## 関連 reference

- [[feedback_pytest_collection_stop_false_fail]] (本 PLAN の動機となる pytest 改善の前提)
- [[feedback_pytest_fixture_time_dependent_flake]] (datetime 動的化 pattern、並列下でも適用)
- [[feedback_codex_parallel_dependency_check]] (Codex 並列投入前の衝突判定)
- ADR-036 (本 PLAN tree の L2 snapshot)
- PLAN-102 (本 PLAN の後段、xdist 並列化の実装)
- PLAN-087 (Web 検索ガード、本 PLAN 起票時の適用確認済)
