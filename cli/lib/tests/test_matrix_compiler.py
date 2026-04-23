"""matrix_compiler.py のテスト。"""

import json
import sys
from pathlib import Path

import pytest

LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import matrix_compiler


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _minimal_matrix_yaml() -> str:
    return (
        "project:\n"
        "  name: test-proj\n"
        "  version: '1.0'\n"
        "features:\n"
        "  auth:\n"
        "    drive: be\n"
        "    scope: feature\n"
        "    risk_flags: []\n"
        "    ui: false\n"
        "    docs_root: docs/features/auth\n"
        "    src_root: src/features/auth\n"
        "    requires:\n"
        "      L1: [D-REQ-F, D-REQ-NF, D-ACC]\n"
        "      L2: [D-ARCH, D-ADR, D-THREAT]\n"
        "      L3: [D-API, D-DB, D-MIG-PLAN, D-DEP, D-TEST, D-PLAN]\n"
        "      L4: [D-IMPL, D-MIG, D-CONFIG]\n"
    )


def _setup_project(tmp_path: Path) -> Path:
    """tmp_path 内に最小限の HELIX プロジェクトを構成する。"""
    helix = tmp_path / ".helix"
    helix.mkdir()
    (helix / "matrix.yaml").write_text(_minimal_matrix_yaml(), encoding="utf-8")

    # rules 正本は cli/templates/rules
    rules_src = Path(__file__).resolve().parents[2] / "templates" / "rules"
    rules_dst = helix / "rules"
    if rules_src.exists():
        rules_dst.mkdir(parents=True, exist_ok=True)
        for f in rules_src.iterdir():
            (rules_dst / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def _repo_rules_dir() -> Path:
    rules_dir = Path(__file__).resolve().parents[2] / "templates" / "rules"
    if not rules_dir.exists():
        pytest.skip("cli/templates/rules が存在しない")
    return rules_dir


# ---------------------------------------------------------------------------
# SimpleYamlParser
# ---------------------------------------------------------------------------

class TestSimpleYamlParser:
    def test_parse_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        result = matrix_compiler.load_yaml(p)
        assert result == {}

    def test_parse_simple_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "simple.yaml"
        p.write_text("key: value\ncount: 3\n", encoding="utf-8")
        result = matrix_compiler.load_yaml(p)
        assert result["key"] == "value"
        assert result["count"] == 3

    def test_parse_nested_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "nested.yaml"
        p.write_text("parent:\n  child: hello\n", encoding="utf-8")
        result = matrix_compiler.load_yaml(p)
        assert result["parent"]["child"] == "hello"

    def test_parse_inline_list(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("items: [a, b, c]\n", encoding="utf-8")
        result = matrix_compiler.load_yaml(p)
        assert result["items"] == ["a", "b", "c"]

    def test_parse_boolean_values(self, tmp_path: Path) -> None:
        p = tmp_path / "bool.yaml"
        p.write_text("yes_val: true\nno_val: false\n", encoding="utf-8")
        result = matrix_compiler.load_yaml(p)
        assert result["yes_val"] is True
        assert result["no_val"] is False

    def test_tab_indent_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "tab.yaml"
        p.write_text("key:\n\tvalue: bad\n", encoding="utf-8")
        with pytest.raises(matrix_compiler.MatrixError, match="タブ"):
            matrix_compiler.load_yaml(p)


# ---------------------------------------------------------------------------
# build_state
# ---------------------------------------------------------------------------

class TestBuildState:
    def test_build_state_generates_pending_entries(self) -> None:
        matrix = {
            "features": {
                "feat-a": {
                    "requires": {
                        "L1": ["D-REQ-F"],
                        "L2": ["D-ARCH"],
                    }
                }
            }
        }
        result = matrix_compiler.build_state(matrix, "2026-01-01T00:00:00")
        deliverables = result["features"]["feat-a"]["deliverables"]
        assert deliverables["D-REQ-F"]["status"] == "pending"
        assert deliverables["D-ARCH"]["status"] == "pending"

    def test_build_state_non_dict_features_raises(self) -> None:
        with pytest.raises(matrix_compiler.MatrixError):
            matrix_compiler.build_state({"features": "bad"}, "2026-01-01T00:00:00")


# ---------------------------------------------------------------------------
# validate_matrix（部分テスト）
# ---------------------------------------------------------------------------

class TestValidateMatrix:
    def _rules(self) -> dict:
        rules_dir = _repo_rules_dir()
        deliverables = matrix_compiler.load_yaml(rules_dir / "deliverables.yaml")
        return deliverables

    def _naming(self) -> dict:
        rules_dir = _repo_rules_dir()
        naming = matrix_compiler.load_yaml(rules_dir / "naming.yaml")
        return naming if isinstance(naming, dict) else {}

    def test_validate_non_dict_raises(self) -> None:
        with pytest.raises(matrix_compiler.MatrixError, match="トップレベル"):
            matrix_compiler.validate_matrix("bad", {}, {})

    def test_validate_missing_project(self) -> None:
        with pytest.raises(matrix_compiler.MatrixError, match="project"):
            matrix_compiler.validate_matrix({"features": {}}, self._rules(), self._naming())

    def test_validate_bad_feature_id(self) -> None:
        matrix = {
            "project": {"name": "test"},
            "features": {
                "BAD_NAME": {
                    "drive": "be",
                    "scope": "feature",
                    "requires": {},
                }
            },
        }
        with pytest.raises(matrix_compiler.MatrixError, match="命名規則"):
            matrix_compiler.validate_matrix(matrix, self._rules(), self._naming())


# ---------------------------------------------------------------------------
# compile / auto_detect / validate / status (統合テスト)
# ---------------------------------------------------------------------------

class TestCompileIntegration:
    def test_compile_creates_outputs(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        matrix_compiler.compile_matrix(project, force_state=True)

        assert (project / ".helix" / "doc-map.yaml").exists()
        assert (project / ".helix" / "gate-checks.yaml").exists()
        assert (project / ".helix" / "state" / "deliverables.json").exists()
        assert (project / ".helix" / "runtime" / "index.json").exists()

    def test_compile_state_not_overwritten_without_force(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        state_path = project / ".helix" / "state" / "deliverables.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text('{"features":{}}', encoding="utf-8")
        matrix_compiler.compile_matrix(project, force_state=False)
        # state should remain unchanged (not overwritten)
        content = json.loads(state_path.read_text(encoding="utf-8"))
        assert content == {"features": {}}

    def test_validate_only_succeeds(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        # Should not raise
        matrix_compiler.validate_only(project)

    def test_status_matrix_runs(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        matrix_compiler.compile_matrix(project, force_state=True)
        # Should not raise
        matrix_compiler.status_matrix(project)

    def test_auto_detect_state_runs(self, tmp_path: Path) -> None:
        project = _setup_project(tmp_path)
        matrix_compiler.compile_matrix(project, force_state=True)
        # Should not raise
        matrix_compiler.auto_detect_state(project)

    def test_compile_no_helix_dir_raises(self, tmp_path: Path) -> None:
        with pytest.raises(matrix_compiler.MatrixError, match=".helix"):
            matrix_compiler.compile_matrix(tmp_path)


# ---------------------------------------------------------------------------
# _build_requires_for_drive
# ---------------------------------------------------------------------------

class TestBuildRequiresForDrive:
    def test_be_drive(self) -> None:
        result = matrix_compiler._build_requires_for_drive("be", ui=False)
        assert "L3" in result
        assert "D-API" in result["L3"]

    def test_fe_drive_includes_ui(self) -> None:
        result = matrix_compiler._build_requires_for_drive("fe", ui=True)
        assert "L5" in result
        assert "D-VISUAL" in result["L5"]

    def test_invalid_drive_raises(self) -> None:
        with pytest.raises(matrix_compiler.MatrixError, match="drive"):
            matrix_compiler._build_requires_for_drive("invalid", ui=False)


# ---------------------------------------------------------------------------
# detect_project_root
# ---------------------------------------------------------------------------

class TestDetectProjectRoot:
    def test_explicit_argument(self, tmp_path: Path) -> None:
        result = matrix_compiler.detect_project_root(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_env_variable(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("HELIX_PROJECT_ROOT", str(tmp_path))
        result = matrix_compiler.detect_project_root(None)
        assert result == tmp_path.resolve()

    def test_cwd_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HELIX_PROJECT_ROOT", raising=False)
        result = matrix_compiler.detect_project_root(None)
        assert result == Path.cwd().resolve()
