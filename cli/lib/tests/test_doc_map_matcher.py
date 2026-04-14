import py_compile
import sys
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import doc_map_matcher


MODULE_PATH = LIB_DIR / "doc_map_matcher.py"


def _write_doc_map(path: Path) -> Path:
    path.write_text(
        (
            "# generated doc map\n"
            "triggers:\n"
            '  - pattern: "docs/features/auth/D-ARCH/*.md"\n'
            "    phase: L2\n"
            "    on_write: gate_ready\n"
            "    gate: G2\n"
            "  - pattern: 'src/features/auth/**/*'\n"
            "    phase: L4\n"
            "    on_write: design_sync\n"
            '    design_ref: "docs/features/auth/D-API/spec.md"\n'
            "  - pattern: docs/features/auth/**/*.py\n"
            "    phase: L4\n"
            "    on_write: coverage_check\n"
            "  - pattern: docs/adr/*.md\n"
            "    phase: L3\n"
            "    on_write: adr_index\n"
        ),
        encoding="utf-8",
    )
    return path


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_glob_match_supports_single_and_double_star() -> None:
    assert doc_map_matcher._glob_match("docs/features/auth/D-ARCH/spec.md", "docs/features/auth/D-ARCH/*.md")
    assert doc_map_matcher._glob_match("src/features/auth/nested/main.ts", "src/features/auth/**/*")
    assert not doc_map_matcher._glob_match("src/platform/main.ts", "src/features/auth/**/*")


def test_parse_doc_map_reads_quoted_values(tmp_path: Path) -> None:
    triggers = doc_map_matcher._parse_doc_map(_write_doc_map(tmp_path / "doc-map.yaml"))

    assert triggers[0]["pattern"] == "docs/features/auth/D-ARCH/*.md"
    assert triggers[1]["design_ref"] == "docs/features/auth/D-API/spec.md"
    assert triggers[3]["on_write"] == "adr_index"


def test_main_emits_matching_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    doc_map_path = _write_doc_map(tmp_path / "doc-map.yaml")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "doc_map_matcher.py",
            str(doc_map_path),
            "src/features/auth/nested/main.ts",
        ],
    )

    result = doc_map_matcher.main()
    output = capsys.readouterr().out.strip()

    assert result == 0
    assert output == "DESIGN_SYNC|docs/features/auth/D-API/spec.md|src/features/auth/nested/main.ts"


def test_main_returns_zero_when_doc_map_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["doc_map_matcher.py", str(tmp_path / "missing.yaml"), "docs/features/auth/D-ARCH/spec.md"],
    )

    assert doc_map_matcher.main() == 0
