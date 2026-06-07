from __future__ import annotations

import sys
from pathlib import Path

import yaml


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import g7_subcheck


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_anchor_map(path: Path, anchors: dict[str, list[str]]) -> None:
    _write(path, yaml.safe_dump({"anchors": anchors}, allow_unicode=True, sort_keys=True))


def test_collect_g7_subcheck_classifies_anchored_unanchored_and_missing(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md",
        "\n".join(
            [
                "| UT ID | 対象 FN | module | 検証観点 | テスト実装 |",
                "| --- | --- | --- | --- | --- |",
                "| UT-WSC-101 | FN-WSC-101 | alpha.py | covered | 実装済 |",
                "| UT-WSC-102 | FN-WSC-102 | beta.py | exists but unanchored | 実装済 |",
                "| UT-WSC-103 | FN-WSC-103 | gamma.py | truly missing | 実装済 |",
                "",
            ]
        ),
    )
    _write(tmp_path / "cli/lib/tests/test_alpha.py", '"""DoD 検証: UT-WSC-101"""\n')
    _write(tmp_path / "cli/lib/tests/test_beta.py", "def test_beta():\n    assert True\n")
    _write_anchor_map(
        tmp_path / "docs/v2/L7-test-design/g7-test-anchor-map.yaml",
        {"UT-WSC-101": ["cli/lib/tests/test_alpha.py"]},
    )

    calls: list[str] = []

    def fake_runner(project_root: Path, rel_path: str) -> dict[str, object]:
        calls.append(rel_path)
        return {"returncode": 0, "stdout": "", "stderr": "", "runner": "pytest", "command": ["pytest", rel_path]}

    report = g7_subcheck.collect_g7_subcheck(
        project_root=tmp_path,
        execute_tests=True,
        test_runner=fake_runner,
    )

    assert report["ut_total"] == 3
    assert report["legacy_inline_anchors"]["count"] == 1
    assert report["anchored"]["count"] == 1
    assert report["exec_pass"]["count"] == 1
    assert report["missing"]["ids"] == ["UT-WSC-103"]
    assert report["unanchored_but_exists"]["ids"] == ["UT-WSC-102"]
    assert report["unanchored_but_exists"]["candidates"]["UT-WSC-102"] == ["cli/lib/tests/test_beta.py"]
    assert calls == ["cli/lib/tests/test_alpha.py"]


def test_collect_g7_subcheck_deduplicates_runner_calls_per_test_file(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/v2/L7-test-design/registry-detector-単体テスト設計.md",
        "\n".join(
            [
                "| UT ID | 対象設計 | 検証内容 | 実装先 |",
                "| --- | --- | --- | --- |",
                "| UT-RDB-01 | FN-RDB-01 | one | `cli/lib/tests/test_registry_checks.py` |",
                "| UT-RDB-02 | FN-RDB-02 | two | `cli/lib/tests/test_registry_checks.py` |",
                "",
            ]
        ),
    )
    _write(tmp_path / "cli/lib/tests/test_registry_checks.py", '"""DoD 検証: UT-RDB-01, UT-RDB-02"""\n')
    _write_anchor_map(
        tmp_path / "docs/v2/L7-test-design/g7-test-anchor-map.yaml",
        {
            "UT-RDB-01": ["cli/lib/tests/test_registry_checks.py"],
            "UT-RDB-02": ["cli/lib/tests/test_registry_checks.py"],
        },
    )

    calls: list[str] = []

    def fake_runner(project_root: Path, rel_path: str) -> dict[str, object]:
        calls.append(rel_path)
        return {"returncode": 0, "stdout": "", "stderr": "", "runner": "pytest", "command": ["pytest", rel_path]}

    report = g7_subcheck.collect_g7_subcheck(
        project_root=tmp_path,
        execute_tests=True,
        test_runner=fake_runner,
    )

    assert report["anchored"]["count"] == 2
    assert report["exec_pass"]["count"] == 2
    assert calls == ["cli/lib/tests/test_registry_checks.py"]


def test_collect_g7_subcheck_ignores_out_of_scope_hook_tests_for_missing_classification(tmp_path: Path) -> None:
    _write(
        tmp_path / "docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md",
        "\n".join(
            [
                "| UT ID | 対象 FN | module | 検証観点 | テスト実装 |",
                "| --- | --- | --- | --- | --- |",
                "| UT-WSC-07 | FN-WSC-07 | pretooluse-agent-fire.sh | hook | 実装済 |",
                "",
            ]
        ),
    )
    _write(tmp_path / "tests/pretooluse-agent-fire.bats", "@test \"hook\" { true }\n")
    _write_anchor_map(tmp_path / "docs/v2/L7-test-design/g7-test-anchor-map.yaml", {})

    report = g7_subcheck.collect_g7_subcheck(project_root=tmp_path, execute_tests=False)

    assert report["anchored"]["count"] == 0
    assert report["unanchored_but_exists"]["count"] == 0
    assert report["missing"]["ids"] == ["UT-WSC-07"]
