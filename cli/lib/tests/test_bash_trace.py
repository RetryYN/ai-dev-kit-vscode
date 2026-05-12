import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from extractors.bash_trace import MAIN_FUNCTION, scan_helix_bash_scripts


def test_scan_helix_bash_scripts_extracts_source_and_function_calls(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cli_dir = repo_root / "cli"
    cli_dir.mkdir(parents=True, exist_ok=True)
    (cli_dir / "helix-sample").write_text(
        "#!/bin/bash\n"
        "source \"./lib/common.sh\"\n"
        "\n"
        "helper() {\n"
        "  :\n"
        "}\n"
        "\n"
        "build() {\n"
        "  helper\n"
        "}\n"
        "\n"
        "build\n",
        encoding="utf-8",
    )

    rows = scan_helix_bash_scripts(repo_root)
    index = {(row["script"], row["function"]): row["callees"] for row in rows}

    assert index[("cli/helix-sample", MAIN_FUNCTION)] == ["build", "source:./lib/common.sh"]
    assert index[("cli/helix-sample", "build")] == ["helper"]
    assert index[("cli/helix-sample", "helper")] == []
