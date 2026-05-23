---
adr_id: ADR-034
title: pytest-xdist 並列化 + per-worker HELIX_HOME isolation (default serial、--parallel で opt-in)
status: Accepted
date: 2026-05-23
deciders:
  - PM (Opus)
related_plans:
  - parent: null
  - L2_snapshot_of: PLAN-102
supersedes: []
superseded_by: []
---

# ADR-034: pytest-xdist 並列化 + per-worker HELIX_HOME isolation

## Status

**Accepted** — 2026-05-23

## Context

HELIX の pytest sweep は ~9 分 (530秒、1846 PASS / 4 skipped) で、CI / 開発両方の bottleneck。並列化で 200-300秒以下に短縮できれば開発フロー改善の効果大。

ただし HELIX は SQLite (`helix.db`) + file lock (`helix-db.lock`) で state 管理を行うため、naive な並列化では本番 lock 奪取 race condition が発生する (PLAN-104 R-4 で root cause 確定済)。

### 評価対象

| 候補 | 採用 | 理由 |
|---|---|---|
| **pytest-xdist** (MIT) | ◯ 採用 | de facto standard、`worker_id` fixture で per-worker isolation 標準、stars 1.4k、active maintenance |
| pytest-parallel | × 見送り | maintenance 停滞、threading ベースで SQLite race リスク高 |
| unittest-parallel | × 見送り | unittest 専用、pytest 移行コスト |
| 並列化なし | × 見送り | sweep 9 分が CI / local 開発の継続的負担 |

### per-worker isolation 戦略

| 戦略 | 採用 | 評価 |
|---|---|---|
| **file-per-worker** (per-worker HELIX_HOME / SQLite file) | ◯ 採用 | 既存 file_lock pattern と完全互換、最小変更 |
| in-memory-per-worker (`:memory:` SQLite) | × 見送り | helix_db の migration / persistence pattern と非互換 |
| shared DB + transaction isolation | × 見送り | SQLite の serialization 制約で並列性が出ない |

## Decision

### D1: pytest-xdist 採用

pytest-xdist (MIT、>=3.0) を `requirements-dev.txt` に追加。default は serial 維持、`cli/helix test --parallel` または `pytest -n auto` で opt-in。

### D2: per-worker HELIX_HOME isolation

`cli/lib/tests/conftest.py` に session-scoped `helix_worker_home` fixture を `autouse=True` で追加。`worker_id` fixture 経由で per-worker tmp dir を確保し、`HELIX_HOME` / `HELIX_PROJECT_ROOT` / `HELIX_DB_PATH` を session 全体で env scope set する。

```python
@pytest.fixture(scope="session", autouse=True)
def helix_worker_home(tmp_path_factory, worker_id):
    if worker_id == "master":
        base = tmp_path_factory.mktemp("helix_home_master")
    else:
        base = tmp_path_factory.mktemp(f"helix_home_{worker_id}")
    os.environ["HELIX_HOME"] = str(base)
    os.environ["HELIX_PROJECT_ROOT"] = str(base)
    os.environ["HELIX_DB_PATH"] = str(base / "helix.db")
    yield base
    # finally で元の env に復元 (test 間 leak 防止)
```

PLAN-104 R-4 fix で確立した env scope pattern と整合 (test process 自身の env を tmp に scope set)。

### D3: CI default は serial 維持

CI (.github/workflows/ci.yml) は default serial。`-n auto` の CI 適用は本 ADR の範囲外、別 PLAN で benchmark + flake check を経て採用判断する。理由:
- CI runner は 2 core が一般的、並列効果が限定的
- CI 失敗時の log 解析容易性 (serial の方が出力順序が deterministic)

### D4: bats / shell test scope 外

bats test は subprocess level で既に分離済 (各 test が `setup()` で独自 tmp 作成)。xdist の対象は python test のみ。`cli/helix test --parallel` は python sweep に対してのみ `-n auto` を付与し、bats は serial 維持。

### D5: pyproject.toml で pytest 設定統一

`pyproject.toml` を新設して `[tool.pytest.ini_options]` で testpaths を定義。`addopts = ""` で default serial を明示。

## Consequences

### Positive

- pytest sweep 530秒 → 200-300秒 (40%+ 削減見込み、Sprint .4 で実測)
- per-worker HELIX_HOME isolation で本番 lock 奪取の race 完全排除
- 既存 fixture pattern (個別 test の env override) は維持、後方互換確保
- 開発者は `cli/helix test --parallel` で簡単に並列実行できる

### Negative

- pytest-xdist 依存追加 (requirements-dev.txt)
- session-scoped autouse fixture で全 test の env が変更される (既存 test に env 依存があれば影響、ただし PLAN-104 R-4 で確立した pattern と整合するため実害なし)
- pyproject.toml 新設で既存 setup.cfg / setup.py がある場合は将来統合判断必要 (HELIX は現状どちらも未使用)

### Risks

| risk | 影響 | 緩和策 |
|---|---|---|
| 並列下で test 間 state leak | 偶発 fail | session-scoped finally で env 復元、PLAN-104 R-4 fix pattern 適用 |
| pytest 9.0 + xdist 3.x 互換性 | 起動 fail | Sprint .4 で実測確認、互換性 issue があれば pytest pin 検討 |
| 並列下のみ発生する flake | regression | Sprint .4 で対象 test 10 回ループ flake check |
| CI 環境で並列化要望が出る | 別 PLAN 起票負担 | 別 PLAN で対応、現 ADR の range 外であることを明示 |

## Alternatives Considered

### A1: pytest-parallel 採用 (見送り)

`pytest-parallel` は threading ベースで、SQLite のような GIL 解放 IO race に弱い。pytest-xdist の process-per-worker の方が isolation 確実。

### A2: 並列化なし、test 数削減で高速化 (見送り)

test 削減は coverage 低下リスク。並列化は coverage 維持しつつ wall time 削減できる優位戦略。

### A3: CI で `-n auto` 即時採用 (見送り)

CI runner は 2 core が一般的で並列効果限定的、log 解析容易性 (serial の方が deterministic) の観点から default serial を維持。CI 適用は別 PLAN で benchmark 確定後に判断。

## Related Documents

- PLAN-102 (本 ADR の trigger PLAN)
- PLAN-104 (R-4 fix、per-worker HELIX_HOME isolation の env scope pattern を確立)
- ADR-005 (yaml-sqlite-dual-state、本 ADR は test 並列化のための isolation 戦略を追加)

## References

- pytest-xdist: https://pytest-xdist.readthedocs.io/
- pytest-xdist Issue #139 (per-worker SQLite isolation): https://github.com/pytest-dev/pytest-xdist/issues/139
- SQLAlchemy Discussion #13109 (FastAPI + Pytest + Postgres parallel): https://github.com/sqlalchemy/sqlalchemy/discussions/13109
- SQLite Locking Reference: https://sqlite.org/lockingv3.html
- SQLite WAL Mode: https://www.sqlite.org/wal.html
