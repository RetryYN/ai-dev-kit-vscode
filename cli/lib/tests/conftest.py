"""pytest conftest — cli/lib/tests/ 配下の共通設定

役割:
1. PROJECT_ROOT を sys.path に追加し、`from cli.lib import ...` 形式の絶対 import が
   cwd に依存せず解決できるようにする (collection stop 防止)
2. PLAN-102: pytest-xdist 並列実行下で `worker_id` fixture 経由で per-worker
   HELIX_HOME / HELIX_DB_PATH を割当、本番 helix-db.lock 奪取を完全回避

背景:
- collection stop: test_agent_mandatory.py 等が `from cli.lib import agent_mandatory` を
  使うが、pytest を `cli/lib/tests/` 等から起動すると PROJECT_ROOT が sys.path に
  含まれず ModuleNotFoundError で collection が停止し、後続 test が偽 fail で
  表示される問題があった ([[feedback_pytest_collection_stop_false_fail]])
- xdist isolation: PLAN-104 R-4 で test が helix_db.init_db() 呼び出し時に
  HELIX_PROJECT_ROOT 未設定で本番 helix-db.lock を奪取する race が確定。
  pytest-xdist で並列実行する場合、worker_id 別に HELIX_HOME を分離して
  per-worker DB / lock を保証する
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _scrub_gate_context_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """gate/automation 実行由来の ambient env を test から隔離する。

    HELIX_DB_CUTOVER / HELIX_DB_DISCOVERY は db_cli の preflight 既定 (CUTOVER="1")
    が gate/push 経由で漏れると、compatibility_adapter の split-DB routing が有効化し、
    explicit legacy seed と routed SUT の DB が分裂して cross-DB FK 不一致で hermetic
    test が間欠 fail する。明示 cutover/discovery test は body 内で monkeypatch.setenv
    し直すため、この autouse scrub 後に再設定され壊れない (HELIX_DB_PATH は温存)。
    """
    for key in tuple(os.environ):
        if key.startswith("HELIX_AUTOMATION_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("HELIX_ASKUSERQUESTION_NOW", raising=False)
    monkeypatch.delenv("HELIX_DB_CUTOVER", raising=False)
    monkeypatch.delenv("HELIX_DB_DISCOVERY", raising=False)


@pytest.fixture(scope="session", autouse=True)
def helix_worker_home(tmp_path_factory, worker_id):
    """PLAN-102: pytest-xdist worker ごとに独立した HELIX_HOME / HELIX_DB_PATH を割当

    - worker_id: pytest-xdist 提供 fixture (`master`: serial、`gw0`/`gw1`/...: parallel)
    - tmp_path_factory: pytest 提供 fixture (session 内で unique tmp dir 自動 cleanup)
    - 既存 test の env override (個別 HELIX_PROJECT_ROOT / HELIX_DB_PATH 設定) は維持

    本 fixture が session 開始時に env を session-scope で set することで、
    helix_db.init_db() / file_lock("helix-db") が本番 lock に fallback しない
    """
    if worker_id == "master":
        base = tmp_path_factory.mktemp("helix_home_master")
    else:
        base = tmp_path_factory.mktemp(f"helix_home_{worker_id}")
    previous_home = os.environ.get("HELIX_HOME")
    previous_project = os.environ.get("HELIX_PROJECT_ROOT")
    previous_db = os.environ.get("HELIX_DB_PATH")
    os.environ["HELIX_HOME"] = str(base)
    os.environ["HELIX_PROJECT_ROOT"] = str(base)
    os.environ["HELIX_DB_PATH"] = str(base / "helix.db")
    try:
        yield base
    finally:
        for key, prev in (
            ("HELIX_HOME", previous_home),
            ("HELIX_PROJECT_ROOT", previous_project),
            ("HELIX_DB_PATH", previous_db),
        ):
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev


@pytest.fixture(autouse=True)
def helix_function_root(request, monkeypatch, tmp_path):
    """PLAN-223: test ごとに tmp_path を HELIX_PROJECT_ROOT/HELIX_DB_PATH に動的 override

    session-scoped helix_worker_home が worker_base に env を固定するが、
    多くの test は tmp_path 配下に lock/.helix/helix.db を作る前提なので
    function-scope で tmp_path に上書きする。

    monkeypatch を使うため test 終了時に session env (worker_base) に自動復元される。

    例外: HELIX_HOME は worker_base 維持 (merge_settings._resolve_helix_home() で
    `cli/libexec/` 等の framework path 計算に使われるため、test_merge_settings 等は
    REPO_ROOT を期待する別 fixture で個別 override する)。

    opt-out: `@pytest.mark.no_helix_function_root` を付けた test では override しない
    (worker_base を維持したい test 用、test_merge_settings 等)。
    """
    _scrub_gate_context_env(monkeypatch)
    if request.node.get_closest_marker("no_helix_function_root"):
        yield
        return
    monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("HELIX_DB_PATH", str(tmp_path / ".helix" / "helix.db"))
    yield
