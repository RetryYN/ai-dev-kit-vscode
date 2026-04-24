import json
import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import matrix_advisor


MODULE_PATH = LIB_DIR / "matrix_advisor.py"


def _write_index(path: Path, features: dict | None = None) -> Path:
    payload = {
        "features": features
        if features is not None
        else {
            "auth": {
                "scope": "feature",
                "requires": {
                    "L1": ["D-REQ-F"],
                    "L2": ["D-ARCH"],
                    "L3": ["D-API"],
                    "L4": ["D-IMPL"],
                },
            }
        },
        "rules": {
            "roots": {"docs_root": "docs", "src_root": "src"},
            "path_mapping": {
                "D-REQ-F": {"root": "docs", "primary_path": "{docs_scope_root}/D-REQ-F/README.md"},
                "D-ARCH": {"root": "docs", "primary_path": "{docs_scope_root}/D-ARCH/README.md"},
                "D-API": {"root": "docs", "primary_path": "{docs_scope_root}/D-API/spec.md"},
            },
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_state(path: Path, statuses: dict[str, str] | None = None) -> Path:
    payload = {"features": {"auth": {"deliverables": {}}}}
    if statuses:
        payload["features"]["auth"]["deliverables"] = {
            deliverable_id: {"status": status} for deliverable_id, status in statuses.items()
        }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_infer_path_info_detects_src_scope_and_deliverable() -> None:
    info = matrix_advisor.infer_path_info("src/features/auth/D-IMPL/main.py")

    assert info.root_kind == "src"
    assert info.scope_collection == "features"
    assert info.scope_type == "feature"
    assert info.scope_id == "auth"
    assert info.deliverable_id == "D-IMPL"
    assert info.is_src_scope_path is True


def test_run_advisory_warns_for_unregistered_scope(tmp_path: Path, capsys) -> None:
    index_path = _write_index(tmp_path / "index.json", features={})
    state_path = _write_state(tmp_path / "deliverables.json")

    matrix_advisor.run_advisory(index_path, state_path, "src/features/auth/main.py", tmp_path)
    output = capsys.readouterr().out

    assert "未登録" in output
    assert "src/features/auth/" in output


def test_run_advisory_warns_when_required_docs_are_missing(tmp_path: Path, capsys) -> None:
    index_path = _write_index(tmp_path / "index.json")
    state_path = _write_state(
        tmp_path / "deliverables.json",
        {"D-REQ-F": "done", "D-ARCH": "done", "D-API": "done"},
    )

    matrix_advisor.run_advisory(index_path, state_path, "src/features/auth/main.py", tmp_path)
    output = capsys.readouterr().out

    assert "docs 欠落" in output
    assert "D-REQ-F" in output


def test_run_advisory_warns_phase_skip_for_l4_change(tmp_path: Path, capsys) -> None:
    index_path = _write_index(tmp_path / "index.json")
    state_path = _write_state(
        tmp_path / "deliverables.json",
        {"D-REQ-F": "done", "D-ARCH": "pending", "D-API": "waived"},
    )
    for rel_path in (
        "docs/features/auth/D-REQ-F/README.md",
        "docs/features/auth/D-ARCH/README.md",
        "docs/features/auth/D-API/spec.md",
    ):
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    matrix_advisor.run_advisory(index_path, state_path, "src/features/auth/main.py", tmp_path)
    output = capsys.readouterr().out

    assert "フェーズ飛ばし" in output
    assert "D-ARCH(pending)" in output


def test_run_advisory_ignores_docs_updates(tmp_path: Path, capsys) -> None:
    index_path = _write_index(tmp_path / "index.json")
    state_path = _write_state(tmp_path / "deliverables.json")

    matrix_advisor.run_advisory(index_path, state_path, "docs/features/auth/D-ARCH/README.md", tmp_path)

    assert capsys.readouterr().out == ""
