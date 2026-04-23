import json
import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import freeze_checker


MODULE_PATH = LIB_DIR / "freeze_checker.py"


def _write_phase(path: Path, statuses: dict[str, str]) -> Path:
    lines = ["current_phase: L6", "gates:"]
    defaults = {
        "G1": "passed",
        "G2": "pending",
        "G3": "pending",
        "G4": "pending",
        "G5": "pending",
        "G6": "pending",
        "G7": "pending",
    }
    defaults.update(statuses)
    for gate, status in defaults.items():
        lines.append(f"  {gate}: {{ status: {status} }}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_index(path: Path) -> Path:
    payload = {
        "features": {
            "auth": {
                "scope": "feature",
                "requires": {
                    "L2": ["D-ARCH"],
                    "L3": ["D-API"],
                },
            }
        },
        "rules": {
            "roots": {"docs_root": "docs", "src_root": "src"},
            "deliverables": [
                {"id": "D-ARCH", "layer": "L2"},
                {"id": "D-API", "layer": "L3"},
            ],
            "path_mapping": {
                "D-ARCH": {"primary_path": "{docs_scope_root}/D-ARCH/README.md"},
                "D-API": {
                    "primary_path": "{docs_scope_root}/D-API/spec.md",
                    "alternate_paths": ["{docs_scope_root}/D-API/openapi.yaml"],
                    "capture_globs": ["{src_scope_root}/D-API/**/*"],
                },
            },
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_candidate_patterns_for_deliverable_includes_primary_alt_and_globs() -> None:
    patterns = freeze_checker._candidate_patterns_for_deliverable(
        "auth",
        {"scope": "feature"},
        "D-API",
        _write_index(Path("/tmp/freeze-index.json")).read_text() and json.loads(_write_index(Path("/tmp/freeze-index.json")).read_text(encoding="utf-8"))["rules"],
    )

    assert "docs/features/auth/D-API/spec.md" in patterns
    assert "docs/features/auth/D-API/**/*" in patterns
    assert "docs/features/auth/D-API/openapi.yaml" in patterns
    assert "src/features/auth/D-API/**/*" in patterns


def test_run_invalidates_downstream_gates_for_passed_freeze(tmp_path: Path, capsys) -> None:
    phase_file = _write_phase(
        tmp_path / ".helix" / "phase.yaml",
        {"G2": "passed", "G3": "passed", "G4": "passed", "G5": "passed"},
    )
    index_file = _write_index(tmp_path / ".helix" / "runtime" / "index.json")
    (tmp_path / ".helix" / "matrix.yaml").write_text("project:\n  name: test\n", encoding="utf-8")

    result = freeze_checker.run(phase_file, index_file, "docs/features/auth/D-ARCH/README.md")
    output = capsys.readouterr().out
    phase_text = phase_file.read_text(encoding="utf-8")

    assert result == 0
    assert "設計凍結違反" in output
    assert "下流ゲート無効化: G3 G4 G5" in output
    assert "gates.G3.status" not in phase_text
    assert "status: invalidated" in phase_text


def test_run_skips_when_gate_is_not_passed(tmp_path: Path, capsys) -> None:
    phase_file = _write_phase(tmp_path / ".helix" / "phase.yaml", {"G2": "pending", "G3": "passed"})
    index_file = _write_index(tmp_path / ".helix" / "runtime" / "index.json")

    result = freeze_checker.run(phase_file, index_file, "docs/features/auth/D-ARCH/README.md")

    assert result == 0
    assert capsys.readouterr().out == ""
    assert "invalidated" not in phase_file.read_text(encoding="utf-8")


def test_run_uses_legacy_layer_for_api_paths(tmp_path: Path, capsys) -> None:
    phase_file = _write_phase(
        tmp_path / ".helix" / "phase.yaml",
        {"G3": "passed", "G4": "passed", "G5": "passed"},
    )
    index_file = _write_index(tmp_path / ".helix" / "runtime" / "index.json")

    freeze_checker.run(phase_file, index_file, "src/api/users.py")
    output = capsys.readouterr().out

    assert "API凍結違反" in output
    assert "下流ゲート無効化: G4 G5" in output


def test_run_ignores_unmatched_path(tmp_path: Path, capsys) -> None:
    phase_file = _write_phase(tmp_path / ".helix" / "phase.yaml", {"G2": "passed"})
    index_file = _write_index(tmp_path / ".helix" / "runtime" / "index.json")

    assert freeze_checker.run(phase_file, index_file, "README.md") == 0
    assert capsys.readouterr().out == ""


def test_main_returns_two_on_internal_error(
    monkeypatch,
    capsys,
) -> None:
    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(freeze_checker, "parse_args", _boom)

    assert freeze_checker.main() == 2
    assert "ERROR: freeze check failed: boom" in capsys.readouterr().err
