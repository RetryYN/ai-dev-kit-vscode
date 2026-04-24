import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import gate_check_generator


MODULE_PATH = LIB_DIR / "gate_check_generator.py"


def _deliverables_rules() -> dict:
    return {
        "deliverables": [
            {
                "id": "D-ARCH",
                "layer": "L2",
                "name": "Architecture",
                "gate_ownership": ["G2"],
                "validators": [{"type": "exists"}],
            },
            {
                "id": "D-API",
                "layer": "L3",
                "name": "API Spec",
                "gate_ownership": ["G3"],
                "validators": [{"type": "heading_check", "params": {"required": ["# Overview"]}}],
            },
            {
                "id": "D-CONTRACT",
                "layer": "L3",
                "name": "Contract",
                "gate_ownership": ["G3"],
                "validators": [{"type": "exists"}],
            },
            {
                "id": "D-IMPL",
                "layer": "L4",
                "name": "Implementation",
                "gate_ownership": ["G4"],
                "validators": [
                    {"type": "exists"},
                    {"type": "ai_review", "params": {"role": "qa", "focus": "回帰と異常系"}},
                ],
            },
            {
                "id": "D-VIS",
                "layer": "L5",
                "name": "Visual",
                "gate_ownership": ["G5"],
                "validators": [{"type": "exists"}],
            },
        ]
    }


def _matrix(ui: bool = True) -> dict:
    return {
        "features": {
            "auth": {
                "ui": ui,
                "requires": {
                    "L2": ["D-ARCH"],
                    "L3": ["D-API", "D-CONTRACT"],
                    "L4": ["D-IMPL"],
                    "L5": ["D-VIS"] if ui else [],
                },
            }
        }
    }


def _catalog_index(rules: dict) -> dict:
    return {item["id"]: item for item in rules["deliverables"]}


def _resolve_paths(feature_id: str, _feature: dict, deliverable_id: str, _structure: dict) -> dict:
    mapping = {
        "D-ARCH": {"primary": f"docs/features/{feature_id}/D-ARCH/README.md"},
        "D-API": {"primary": f"docs/features/{feature_id}/D-API/spec.md"},
        "D-CONTRACT": {"primary": f"docs/features/{feature_id}/D-CONTRACT/contract.md"},
        "D-IMPL": {
            "primary": f"src/features/{feature_id}/D-IMPL/main.py",
            "capture": [f"src/features/{feature_id}/**/*"],
        },
        "D-VIS": {"primary": f"docs/features/{feature_id}/D-VIS/screen.md"},
    }
    return mapping[deliverable_id]


def _d_contract_pattern(feature_id: str, _feature: dict, _structure: dict) -> str:
    return f"docs/features/{feature_id}/D-CONTRACT/**/*.md"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_build_doc_map_generates_gate_and_design_sync_triggers() -> None:
    doc_map = gate_check_generator.build_doc_map(
        _matrix(),
        _deliverables_rules(),
        {},
        catalog_index=_catalog_index,
        resolve_paths=_resolve_paths,
        d_contract_doc_pattern=_d_contract_pattern,
    )

    assert {"pattern": "docs/features/auth/D-ARCH/README.md", "phase": "L2", "on_write": "gate_ready", "gate": "G2"} in doc_map["triggers"]
    assert {"pattern": "docs/features/auth/D-CONTRACT/**/*.md", "phase": "L3", "on_write": "gate_ready", "gate": "G3"} in doc_map["triggers"]
    assert {
        "pattern": "src/features/auth/**/*",
        "phase": "L4",
        "on_write": "design_sync",
        "design_ref": "docs/features/auth/D-API/spec.md",
    } in doc_map["triggers"]


def test_build_doc_map_deduplicates_duplicate_deliverables() -> None:
    matrix = _matrix()
    matrix["features"]["auth"]["requires"]["L3"] = ["D-API", "D-API"]

    doc_map = gate_check_generator.build_doc_map(
        matrix,
        _deliverables_rules(),
        {},
        catalog_index=_catalog_index,
        resolve_paths=_resolve_paths,
        d_contract_doc_pattern=_d_contract_pattern,
    )

    patterns = [item["pattern"] for item in doc_map["triggers"] if item["phase"] == "L3"]
    assert patterns.count("docs/features/auth/D-API/spec.md") == 1


def test_build_doc_map_raises_when_features_is_not_dict() -> None:
    with pytest.raises(ValueError, match="matrix.features"):
        gate_check_generator.build_doc_map(
            {"features": []},
            _deliverables_rules(),
            {},
            catalog_index=_catalog_index,
            resolve_paths=_resolve_paths,
            d_contract_doc_pattern=_d_contract_pattern,
        )


def test_build_gate_checks_collects_validators_and_required_files() -> None:
    gate_checks = gate_check_generator.build_gate_checks(
        _matrix(),
        _deliverables_rules(),
        {},
        catalog_index=_catalog_index,
        resolve_paths=_resolve_paths,
        d_contract_doc_pattern=_d_contract_pattern,
    )

    g3_static = gate_checks["G3"]["static"]
    g4_ai = gate_checks["G4"]["ai"]

    assert any(item["name"] == "auth D-API 見出しチェック" for item in g3_static)
    assert any(item["cmd"] == "test -f docs/features/auth/D-API/spec.md" for item in g3_static)
    assert any(item["cmd"] == "ls docs/features/auth/D-CONTRACT/**/*.md >/dev/null 2>&1" for item in g3_static)
    assert g4_ai == [
        {
            "role": "qa",
            "task": "G4 検証: auth の D-IMPL（Implementation）を確認する。観点: 回帰と異常系",
        }
    ]


def test_build_gate_checks_adds_framework_and_policy_checks() -> None:
    gate_checks = gate_check_generator.build_gate_checks(
        _matrix(),
        _deliverables_rules(),
        {},
        framework={"detected": "python", "tools": {"lint": "ruff check cli/lib"}},
        catalog_index=_catalog_index,
        resolve_paths=_resolve_paths,
        d_contract_doc_pattern=_d_contract_pattern,
    )

    g4_names = [item["name"] for item in gate_checks["G4"]["static"]]
    assert "framework python lint" in g4_names
    assert "技術負債台帳の存在" in g4_names


def test_dump_yaml_outputs_escape_quotes_and_task_blocks() -> None:
    doc_map_yaml = gate_check_generator.dump_doc_map_yaml(
        {"triggers": [{"pattern": 'docs/"quoted".md', "phase": "L2", "on_write": "gate_ready", "gate": "G2"}]}
    )
    gate_yaml = gate_check_generator.dump_gate_checks_yaml(
        {
            "G4": {
                "name": 'name "quoted"',
                "static": [{"name": "exists", "cmd": 'test -f "quoted".md'}],
                "ai": [{"role": "qa", "task": "line1\nline2"}],
            }
        }
    )

    assert 'pattern: "docs/\\"quoted\\".md"' in doc_map_yaml
    assert 'name: "name \\"quoted\\""' in gate_yaml
    assert "      task: |" in gate_yaml
    assert "        line2" in gate_yaml
