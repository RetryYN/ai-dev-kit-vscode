"""pytest conftest — cli/lib/tests/ 配下の共通設定

役割: PROJECT_ROOT を sys.path に追加し、`from cli.lib import ...` 形式の
絶対 import が cwd に依存せず解決できるようにする。

背景: test_agent_mandatory.py 等が `from cli.lib import agent_mandatory` を
使うが、pytest を `cli/lib/tests/` 等から起動すると PROJECT_ROOT が sys.path に
含まれず ModuleNotFoundError で collection が停止し、後続 test が偽 fail で
表示される問題があった ([[feedback_pytest_collection_stop_false_fail]])。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
