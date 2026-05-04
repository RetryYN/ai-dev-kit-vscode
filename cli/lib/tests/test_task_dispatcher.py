import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import task_dispatcher


def test_helix_command_allowlist_requires_exact_or_explicit_wildcard() -> None:
    allowlist = {"helix_commands": ["status", "gate *"]}

    assert task_dispatcher._is_allowed("helix_commands", "status", allowlist) is True
    assert task_dispatcher._is_allowed("helix_commands", "status --json", allowlist) is False
    assert task_dispatcher._is_allowed("helix_commands", "gate G2 --static-only", allowlist) is True
