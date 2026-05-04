import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import command_catalog


def test_build_catalog_includes_routed_help_entries() -> None:
    catalog = command_catalog.build_catalog(REPO_ROOT)
    by_name = {entry.name: entry for entry in catalog}

    assert by_name["commands"].category == "HELIX 全体管理"
    assert by_name["commands"].target == "helix-commands"
    assert by_name["learn"].deprecated is True


def test_command_catalog_check_passes_for_repo() -> None:
    assert command_catalog.check_catalog(REPO_ROOT) == []


def test_parse_docs_index_returns_public_commands() -> None:
    docs_commands = command_catalog.parse_docs_index(REPO_ROOT / "docs" / "commands" / "index.md")

    assert "commands" in docs_commands
    assert "scheduler" in docs_commands


def test_integration_contracts_pass_for_repo() -> None:
    assert command_catalog.check_integration_contracts(REPO_ROOT) == []
