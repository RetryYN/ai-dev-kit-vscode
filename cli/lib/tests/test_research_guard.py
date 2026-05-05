import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import research_guard


MODULE_PATH = LIB_DIR / "research_guard.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_g1r_fails_without_research_report(tmp_path: Path) -> None:
    payload = research_guard.check_research_gate(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "missing_research_report" for item in payload["errors"])


def test_g1r_passes_with_sources_decision_and_no_blockers(tmp_path: Path) -> None:
    report = tmp_path / "docs" / "research" / "library-choice.md"
    report.parent.mkdir(parents=True)
    report.write_text(
        "# 調査\n\n"
        "## 出典\n"
        "- https://example.com/official\n\n"
        "## 判断\n"
        "採用: 公式 API が要件を満たす。\n\n"
        "open_blockers: 0\n",
        encoding="utf-8",
    )

    payload = research_guard.check_research_gate(tmp_path)

    assert payload["ok"] is True
    assert payload["reports"] == ["docs/research/library-choice.md"]


def test_g1r_rejects_report_without_decision(tmp_path: Path) -> None:
    report = tmp_path / "docs" / "features" / "x" / "D-RES" / "research.md"
    report.parent.mkdir(parents=True)
    report.write_text("## Sources\nhttps://example.com\n", encoding="utf-8")

    payload = research_guard.check_research_gate(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "missing_decision" for item in payload["errors"])


def test_g1r_rejects_open_blockers(tmp_path: Path) -> None:
    report = tmp_path / ".helix" / "research" / "task" / "research.md"
    report.parent.mkdir(parents=True)
    report.write_text(
        "## Sources\nhttps://example.com\n\n"
        "## Decision\nadopt with follow-up\n\n"
        "- [ ] blocker: license must be checked\n",
        encoding="utf-8",
    )

    payload = research_guard.check_research_gate(tmp_path)

    assert payload["ok"] is False
    assert any(item["code"] == "open_blockers" for item in payload["errors"])
