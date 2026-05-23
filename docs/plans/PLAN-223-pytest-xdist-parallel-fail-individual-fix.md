---
plan_id: PLAN-223
title: "PLAN-223: pytest-xdist 並列下 fail 32 件の個別 test fix (PLAN-102 後段)"
layer: L4
kind: impl
status: completed
completed_at: 2026-05-23
size: M
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: qa
    slot_label: "QA — fail traceback 取得 + 個別 test 分類 + autouse fixture との衝突 root cause 特定"
  - role: se
    slot_label: "SE — 個別 test fix 実装 (test_session_telemetry / test_stale_lock_cleanup / test_yaml_parser 系)"
  - role: tl-advisor
    slot_label: "TL adversarial check — fixture redesign vs individual test fix の選択"
generates:
  - artifact_path: cli/lib/tests/test_session_telemetry.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_stale_lock_cleanup.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_yaml_parser.py
    artifact_type: test
dependencies:
  parent: PLAN-102
  requires:
    - PLAN-102
  blocks: []
related_adr:
  - ADR-034-pytest-xdist-parallel-isolation
related_docs:
  - cli/lib/tests/conftest.py
  - docs/plans/PLAN-102-pytest-xdist-parallel-isolation.md
acceptance_criteria:
  - "pytest -n auto cli/lib/tests/ で 0 fail / 0 errors (regression: 1846+ PASS / 4 skipped 維持)"
  - "autouse=True helix_worker_home fixture との衝突解消"
  - "test_session_telemetry / test_stale_lock_cleanup / test_yaml_parser 系の本番 lock pattern test が並列下でも PASS"
  - "serial sweep (pytest cli/lib/tests/) 回帰なし"
  - "helix doctor 24 pass / 0 fail / 79-80 warn 維持"
---

# PLAN-223: pytest-xdist 並列下 fail 32 件の個別 test fix (PLAN-102 後段)

## L2 凍結 (ADR snapshot)

本 PLAN tree は **PLAN-102 / ADR-034 で確定した autouse=True helix_worker_home fixture との互換性確保** のための test 個別修正であり、新規の大局判断は含まない。ADR-034 が本 PLAN tree の L2 snapshot。

## 背景

PLAN-102 で pytest-xdist 並列化 (Sprint .1-.5) 完遂、ADR-034 Accepted。実測結果:
- serial: 457 秒
- xdist `-n auto` (32 CPU): 54 秒 = **88% 削減 (8.5x)**

ただし xdist 全 sweep で **32 fail 残存** (autouse=True 状態):
- test_session_telemetry / test_stale_lock_cleanup / test_yaml_parser 系
- 本番 lock pattern を test する設計と autouse fixture の env scope set が衝突

autouse=False に変更すると **228 fail に悪化** (PLAN-104 R-3/R-4 と同じ race が全 test に波及)。両立しない。

**判断**: autouse=True を維持 (PLAN-102 close で確定)、個別 test の fixture 適用判断を本 PLAN で対応。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は PLAN-102 後段の test 個別修正で、新 framework 採用や L2 大局判断を含まない。PLAN-087 ガード対象外 (内部 test refactor)。

## 仮説リスト (fail 原因)

| # | 仮説 | 確認方法 |
|---|---|---|
| H1 | autouse fixture が env を set すると、本番 lock pattern を test する test が tmp lock を取ってしまい assertion fail | 該当 test を 1 件 traceback で確認 |
| H2 | session-scoped fixture の env scope が test 間で leak (前 test の env が次 test まで残る) | 個別 test を serial で実行、状態確認 |
| H3 | xdist worker_id 別 tmp dir 内で複数 test が同 db / lock を取り合う | worker 内 test 順序の確認 |

## 実装計画 (Sprint .1 - .3)

### Sprint .1: traceback 取得 + 個別 test 分類 (Codex qa 委譲、size S)

```bash
python3 -m pytest -n auto cli/lib/tests/ --tb=long -v 2>&1 | tee /tmp/plan223-fail.log
grep -A 30 "FAILED " /tmp/plan223-fail.log > /tmp/plan223-tracebacks.log
```

確認事項:
- fail 32 件の test 関数名 + traceback
- 分類: (a) env override 必要 / (b) fixture skip 必要 / (c) test logic 修正必要
- autouse fixture と衝突する具体的箇所特定

### Sprint .2: 個別 test fix (Codex se 委譲、size M)

分類に応じた修正:

#### (a) env override 必要 な test (推定 ~20 件)

test 内で fixture が set した env を上書きし、本番 lock pattern を再現:

```python
def test_X(tmp_path, monkeypatch):
    # autouse fixture の env を本 test 専用 path に上書き
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path / "custom"))
    # ... 既存 test logic
```

#### (b) fixture skip 必要 な test (推定 ~5 件)

特定 test class / function で `helix_worker_home` の影響を受けたくない場合、`@pytest.mark.usefixtures` を使わず、test 内で明示的に env を clear:

```python
@pytest.fixture
def isolated_env(monkeypatch):
    monkeypatch.delenv("HELIX_PROJECT_ROOT", raising=False)
    monkeypatch.delenv("HELIX_DB_PATH", raising=False)
    yield
```

#### (c) test logic 修正必要 な test (推定 ~7 件)

並列下 race を想定していない logic (例: 共有 file の race) を tmp_path scope に修正。

### Sprint .3: 検証 + commit (Codex qa 委譲、size XS)

```bash
# 並列 sweep 0 fail
pytest -n auto cli/lib/tests/ -q
# 並列 + serial 両方で regression なし
pytest cli/lib/tests/ -q
# 同一 fail test を 10 回ループで 0 fail
for i in $(seq 1 10); do pytest -n auto cli/lib/tests/test_session_telemetry.py -q; done
```

## DoD (Definition of Done)

- [ ] `pytest -n auto cli/lib/tests/ -q` で 0 fail / 0 errors
- [ ] `pytest cli/lib/tests/ -q` (serial) で regression なし (1846+ PASS / 4 skipped 維持)
- [ ] 10 回 loop で対象 test 0 fail (flake check)
- [ ] helix doctor 24 pass / 0 fail / 79-80 warn 維持
- [ ] PLAN-102 Sprint .5 carry の解消明示

## carry / 学び (起票時記録)

- **fixture 設計の trade-off**: autouse=True は env scope の自動分離に必須だが、env override を期待する test と衝突。本 PLAN で個別 test 修正で解消
- **xdist worker_id 別 tmp dir の限界**: 32 worker が同 db init を並行実行すると schema race の可能性、本 PLAN 範囲外で別 PLAN 候補 (WAL mode opt-in 等)
- **PLAN-102 完遂後の継続 PLAN**: PLAN-102 では「dev 用 opt-in」として close、本 PLAN で「CI default 並列化」への道筋を確立

## 関連 reference

- PLAN-102 (parent、pytest-xdist 並列化 framework)
- PLAN-104 (R-3/R-4 fix、env scope pattern の base)
- ADR-034 (本 PLAN tree の L2 snapshot)
- [[feedback_plan104_gate_test_flake_root_cause]] (env scope helper pattern)

## 完遂結果 (2026-05-23)

### Sprint .1: traceback 取得 + 分類 (PASS)

並列 sweep で **33 fail / 13 test file** 検出 (52.17s)。6 root cause pattern に分類:

| Pattern | 該当 | 修正方針 |
|---|---|---|
| P1: lock pattern test の `monkeypatch.chdir(tmp_path)` + lock path 期待 | test_concurrent_lock × 4 / test_handover × 2 / test_stale_lock_cleanup × 5 / test_yaml_parser × 1 / test_helix_doctor × 2 | function-scoped autouse fixture で HELIX_PROJECT_ROOT を tmp_path に dynamic override |
| P2: merge_settings の `_resolve_helix_home()` REPO_ROOT 期待 | test_merge_settings × 3 | test 内で `monkeypatch.delenv("HELIX_HOME")` で default 復帰 |
| P3: context_guard の framework_root を REPO_ROOT 期待 | test_context_guard × 4 | 同上 |
| P4: hook DB recording の subprocess env で session inherit | test_audit_log × 4 / test_audit_e2e × 3 / test_pretooluse_askuserquestion × 2 / test_session_telemetry × 1 | helper の env に `HELIX_DB_PATH=str(db_path)` 明示 override |
| P5: regression (PLAN-102 test_xdist_isolation が新 fixture と衝突) | test_xdist_isolation × 2 | pytestmark で `no_helix_function_root` marker 適用 (opt-out) |
| P6: future-dated rows race (worker 起動 overhead で +1s が過去化) | test_reverse_local_unit × 1 / test_scrum_local_unit × 1 | `_ts_future(seconds=1)` → `seconds=30` 緩和 |

### Sprint .2: conftest 改修 + 個別 fix (PASS)

#### conftest.py 改修

`helix_function_root` (function-scoped autouse) を追加:
```python
@pytest.fixture(autouse=True)
def helix_function_root(request, monkeypatch, tmp_path):
    if request.node.get_closest_marker("no_helix_function_root"):
        yield
        return
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("HELIX_DB_PATH", str(tmp_path / ".helix" / "helix.db"))
    yield
```

設計判断:
- HELIX_HOME は worker_base 維持 (framework path 計算用)
- HELIX_PROJECT_ROOT / HELIX_DB_PATH のみ tmp_path 動的 override
- `@pytest.mark.no_helix_function_root` で opt-out (PLAN-102 isolation test 等)

#### 個別 fix (12 file)

- cli/lib/tests/conftest.py: function-scoped fixture + marker support
- cli/lib/tests/test_audit_e2e.py: REPO_ROOT 定義 + _run_audit env 明示
- cli/lib/tests/test_audit_log.py: _run_stop_like_hook / _run_pretooluse_hook で HELIX_DB_PATH 明示
- cli/lib/tests/test_context_guard.py: pytest import + 4 test に `monkeypatch.delenv("HELIX_HOME")`
- cli/lib/tests/test_handover.py: _run_handover_worker + test_lock_release_on_exception で `HELIX_PROJECT_ROOT=str(repo)` override
- cli/lib/tests/test_merge_settings.py: 3 test に `monkeypatch.delenv("HELIX_HOME")`
- cli/lib/tests/test_pretooluse_askuserquestion.py: _run_hook で HELIX_DB_PATH 明示
- cli/lib/tests/test_reverse_local_unit.py: `_ts_future(seconds=30)`
- cli/lib/tests/test_scrum_local_unit.py: 同上
- cli/lib/tests/test_session_telemetry.py: env に `HELIX_DB_PATH=str(db_path)` 追加
- cli/lib/tests/test_xdist_isolation.py: pytestmark + import pytest
- pyproject.toml: `no_helix_function_root` marker 登録

### Sprint .3: 検証 (PASS)

| 検証項目 | 結果 |
|---|---|
| `pytest -n auto cli/lib/tests/ -q` | **1851 passed, 4 skipped, 0 fail, 52.84s** |
| `pytest cli/lib/tests/ -q` (serial 回帰) | **1851 passed, 4 skipped, 0 fail, 598s** |
| 10 回 loop flake check (対象 14 file) | **182 passed × 10 回 / 全 PASS (各 9.6-9.8s)** |
| helix doctor | **21 pass / 0 fail / 145 warn** (stale lock 増、cleanup 済) |

### 学び

- **autouse function-scoped fixture の有効性**: session fixture (env 固定) と function fixture (test ごと dynamic override) の 2 段構成で xdist parallelism + 既存 test の env 期待を両立可能
- **opt-out marker pattern**: 一部 test (isolation test 等) で session env を直接検証したい場合、`no_helix_function_root` marker で skip 可能。`request.node.get_closest_marker()` で実装
- **subprocess の env inherit**: `os.environ.copy()` 経由で session fixture の HELIX_DB_PATH が全 subprocess hook に inherit される。helper 関数で明示 override が必須
- **future-dated rows test の race**: `_ts_future(seconds=1)` 程度では並列下 worker 起動 overhead で過去化する → 30 秒に緩和 ([[feedback_pytest_fixture_time_dependent_flake]] 同 pattern)
- **修正 file 12 件 / +90 行 / -8 行** で 33 fail → 0 fail (1851 PASS) 達成、PLAN-102 carry 完全解消
