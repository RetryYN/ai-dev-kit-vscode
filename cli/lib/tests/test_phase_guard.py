import json
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import phase_guard


MODULE_PATH = LIB_DIR / "phase_guard.py"


def _init_fake_repo(tmp_path: Path) -> tuple[Path, Path]:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    helix_dir = tmp_path / ".helix"
    helix_dir.mkdir()
    phase_file = helix_dir / "phase.yaml"
    return tmp_path, phase_file


def _write_phase(path: Path, current_phase: str, statuses: dict[str, str] | None = None) -> Path:
    merged = {
        "G1": "pending",
        "G2": "pending",
        "G3": "pending",
        "G4": "pending",
        "G5": "pending",
        "G6": "pending",
        "G7": "pending",
    }
    if statuses:
        merged.update(statuses)

    lines = [f"current_phase: {current_phase}", "gates:"]
    for gate, status in merged.items():
        lines.append(f"  {gate}: {{ status: {status} }}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_index(path: Path) -> Path:
    payload = {
        "rules": {
            "deliverables": [
                {"id": "D-VIS", "layer": "L5"},
                {"id": "D-ARCH", "layer": "L2"},
            ]
        }
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run_main(monkeypatch: pytest.MonkeyPatch, phase_file: Path, changed_file: str, index_path: Path | None = None) -> int:
    argv = ["phase_guard.py", "--phase-file", str(phase_file), "--file", changed_file]
    if index_path is not None:
        argv.extend(["--index", str(index_path)])
    monkeypatch.setattr(sys, "argv", argv)
    return phase_guard.main()


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_main_blocks_unsized_src_change_in_fake_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, phase_file = _init_fake_repo(tmp_path)
    _write_phase(phase_file, "null")
    changed_file = str(repo_root / "src" / "features" / "auth" / "main.py")

    result = _run_main(monkeypatch, phase_file, changed_file)
    output = capsys.readouterr().out

    assert result == 1
    assert "未サイジング" in output


def test_main_allows_unsized_docs_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, phase_file = _init_fake_repo(tmp_path)
    _write_phase(phase_file, "null")

    result = _run_main(monkeypatch, phase_file, str(repo_root / "docs" / "features" / "auth" / "D-ARCH" / "README.md"))

    assert result == 0


def test_main_allows_test_file_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, phase_file = _init_fake_repo(tmp_path)
    _write_phase(phase_file, "L4", {"G1": "passed", "G2": "passed", "G3": "passed"})

    result = _run_main(monkeypatch, phase_file, str(repo_root / "src" / "features" / "auth" / "widget.test.ts"))

    assert result == 0


def test_main_blocks_l5_change_before_g4(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo_root, phase_file = _init_fake_repo(tmp_path)
    _write_phase(phase_file, "L4", {"G1": "passed", "G2": "passed", "G3": "passed"})
    index_path = _write_index(repo_root / ".helix" / "runtime" / "index.json")

    result = _run_main(
        monkeypatch,
        phase_file,
        str(repo_root / "docs" / "features" / "auth" / "D-VIS" / "screen.md"),
        index_path,
    )
    output = capsys.readouterr().out

    assert result == 1
    assert "フェーズ違反" in output
    assert "G4" in output


def test_main_allows_l5_change_after_g4_passed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root, phase_file = _init_fake_repo(tmp_path)
    _write_phase(
        phase_file,
        "L4",
        {"G1": "passed", "G2": "passed", "G3": "passed", "G4": "passed"},
    )
    index_path = _write_index(repo_root / ".helix" / "runtime" / "index.json")

    result = _run_main(
        monkeypatch,
        phase_file,
        str(repo_root / "docs" / "features" / "auth" / "D-VIS" / "screen.md"),
        index_path,
    )

    assert result == 0


def test_main_returns_zero_when_phase_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / ".helix" / "phase.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        ["phase_guard.py", "--phase-file", str(missing), "--file", str(tmp_path / "src" / "main.py")],
    )

    assert phase_guard.main() == 0
