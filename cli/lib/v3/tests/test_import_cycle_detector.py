from __future__ import annotations

import sqlite3

from cli.lib.v3.detectors.core import (
    ImportCycleInput,
    ImportCycleResult,
    analyze_import_cycle,
    import_cycle_messages,
    load_import_cycle_input,
)


def test_fn_det_17_analyze_has_no_findings_without_cycles() -> None:
    result = analyze_import_cycle(
        ImportCycleInput(
            scanned=True,
            python_files=("cli/lib/alpha.py", "cli/lib/beta.py"),
            bash_files=("cli/run.sh",),
            adjacency=(
                ("cli/lib/alpha.py", ("cli/lib/beta.py",)),
                ("cli/lib/beta.py", ()),
                ("cli/run.sh", ()),
            ),
        )
    )

    assert result == ImportCycleResult(ok=True, missing_sources=(), cycles=())
    assert import_cycle_messages(result) == []


def test_fn_det_17_analyze_detects_two_module_cycle() -> None:
    result = analyze_import_cycle(
        ImportCycleInput(
            scanned=True,
            python_files=("cli/lib/a.py", "cli/lib/b.py"),
            bash_files=(),
            adjacency=(
                ("cli/lib/a.py", ("cli/lib/b.py",)),
                ("cli/lib/b.py", ("cli/lib/a.py",)),
            ),
        )
    )

    assert result.ok is False
    assert result.cycles == (("cli/lib/a.py", "cli/lib/b.py", "cli/lib/a.py"),)
    assert import_cycle_messages(result)[0].subject == "cli/lib/a.py -> cli/lib/b.py -> cli/lib/a.py"


def test_fn_det_17_analyze_detects_three_module_cycle() -> None:
    result = analyze_import_cycle(
        ImportCycleInput(
            scanned=True,
            python_files=("cli/lib/a.py", "cli/lib/b.py", "cli/lib/c.py"),
            bash_files=(),
            adjacency=(
                ("cli/lib/a.py", ("cli/lib/b.py",)),
                ("cli/lib/b.py", ("cli/lib/c.py",)),
                ("cli/lib/c.py", ("cli/lib/a.py",)),
            ),
        )
    )

    assert result.ok is False
    assert result.cycles == (("cli/lib/a.py", "cli/lib/b.py", "cli/lib/c.py", "cli/lib/a.py"),)


def test_fn_det_17_analyze_reports_absence_when_scan_source_missing() -> None:
    result = analyze_import_cycle(
        ImportCycleInput(
            scanned=False,
            python_files=(),
            bash_files=(),
            adjacency=(),
        )
    )

    assert result == ImportCycleResult(ok=False, missing_sources=("repo-root-unreadable",), cycles=())
    assert import_cycle_messages(result)[0].missing == ("repo-root-unreadable",)


def test_fn_det_17_analyze_ok_when_no_target_files_exist() -> None:
    result = analyze_import_cycle(
        ImportCycleInput(
            scanned=True,
            python_files=(),
            bash_files=(),
            adjacency=(),
        )
    )

    assert result == ImportCycleResult(ok=True, missing_sources=(), cycles=())
    assert import_cycle_messages(result) == []


def test_fn_det_17_load_detects_python_cycle_from_repo_files(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / "cli/lib").mkdir(parents=True)
    (repo_root / "cli/bin").mkdir(parents=True)
    (repo_root / "cli/lib/a.py").write_text("import cli.lib.b\n", encoding="utf-8")
    (repo_root / "cli/lib/b.py").write_text("import cli.lib.a\n", encoding="utf-8")
    (repo_root / "cli/bin/run.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    monkeypatch.setattr("cli.lib.v3.detectors.core._REPO_ROOT", str(repo_root))

    loaded = load_import_cycle_input(sqlite3.connect(":memory:"))
    result = analyze_import_cycle(loaded)

    assert result.ok is False
    assert result.cycles == (("cli/lib/a.py", "cli/lib/b.py", "cli/lib/a.py"),)


def test_fn_det_17_load_detects_bash_source_cycle_from_repo_files(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path
    (repo_root / "cli/lib").mkdir(parents=True)
    (repo_root / "cli/scripts").mkdir(parents=True)
    (repo_root / "cli/lib/leaf.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo_root / "cli/scripts/a.sh").write_text(
        "#!/usr/bin/env bash\nsource ./b.sh\n",
        encoding="utf-8",
    )
    (repo_root / "cli/scripts/b.sh").write_text(
        "#!/usr/bin/env bash\nsource ./a.sh\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("cli.lib.v3.detectors.core._REPO_ROOT", str(repo_root))

    loaded = load_import_cycle_input(sqlite3.connect(":memory:"))
    result = analyze_import_cycle(loaded)

    assert result.ok is False
    assert result.cycles == (("cli/scripts/a.sh", "cli/scripts/b.sh", "cli/scripts/a.sh"),)
