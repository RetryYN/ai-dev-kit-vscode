"""UT-WSC-218 unit tests for cli/lib/zizmor_ignore_lint.py.

DoD 検証: docs/v2/L7-test-design/whole-source-coverage-単体テスト設計.md UT-WSC-218
"""

from __future__ import annotations

from pathlib import Path

from cli.lib import zizmor_ignore_lint


class TestZizmorIgnoreLint:
    def test_ut_wsc_218_scan_file_marks_compliant_ignore(self, tmp_path: Path) -> None:
        """DoD 検証: UT-WSC-218 ensures compliant metadata を True 判定する"""
        workflow = tmp_path / "ci.yml"
        workflow.write_text(
            "\n".join(
                [
                    "jobs:",
                    "  test:",
                    "    steps:",
                    "      - run: echo test  # zizmor:ignore[template-injection] reason=templated workflow owner=@openai expires=2026-12-31",
                ]
            ),
            encoding="utf-8",
        )

        findings = zizmor_ignore_lint.scan_file(workflow)

        assert len(findings) == 1
        assert findings[0].is_compliant is True
        assert "template-injection" in findings[0].raw_line

    def test_ut_wsc_218_scan_file_reports_missing_metadata(self, tmp_path: Path) -> None:
        """DoD 検証: UT-WSC-218 invariant missing metadata を fail-close 相当で検出する"""
        workflow = tmp_path / "ci.yml"
        workflow.write_text(
            "run: echo test  # zizmor:ignore reason=temporary\n",
            encoding="utf-8",
        )

        findings = zizmor_ignore_lint.scan_file(workflow)

        assert len(findings) == 1
        assert findings[0].is_compliant is False
        assert findings[0].missing_fields() == ["owner", "expires or re-evaluate-when"]

    def test_ut_wsc_218_scan_paths_recurses_yaml_and_skips_unreadable(self, tmp_path: Path) -> None:
        """DoD 検証: UT-WSC-218 ensures directory recurse + unreadable file skip"""
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        readable = workflows / "readable.yaml"
        readable.write_text(
            "run: echo ok  # zizmor:ignore owner=@team reason=known expires=2026-12-31\n",
            encoding="utf-8",
        )
        unreadable = workflows / "secret.yml"
        unreadable.write_text(
            "run: echo ng  # zizmor:ignore reason=missing owner=@team expires=2026-12-31\n",
            encoding="utf-8",
        )
        unreadable.chmod(0)
        ignored = workflows / "notes.txt"
        ignored.write_text("zizmor:ignore should not be scanned\n", encoding="utf-8")

        try:
            findings = zizmor_ignore_lint.scan_paths([workflows])
        finally:
            unreadable.chmod(0o600)

        assert [finding.path.name for finding in findings] == ["readable.yaml"]

    def test_ut_wsc_218_main_strict_returns_1_for_non_compliant(self, tmp_path: Path, capsys) -> None:
        """DoD 検証: UT-WSC-218 invariant strict mode は non-compliant を exit 1 にする"""
        workflow = tmp_path / "strict.yml"
        workflow.write_text(
            "run: echo test  # zizmor:ignore reason=temporary owner=@team\n",
            encoding="utf-8",
        )

        result = zizmor_ignore_lint.main(["--strict", str(workflow)])
        output = capsys.readouterr().out

        assert result == 1
        assert "non-compliant finding(s)" in output
        assert "expires or re-evaluate-when" in output

    def test_ut_wsc_218_main_returns_0_when_no_ignore_comments(self, tmp_path: Path, capsys) -> None:
        """DoD 検証: UT-WSC-218 ensures ignore comment 不在時は fail-open で 0 を返す"""
        workflow = tmp_path / "clean.yml"
        workflow.write_text("run: echo clean\n", encoding="utf-8")

        result = zizmor_ignore_lint.main([str(workflow)])
        output = capsys.readouterr().out

        assert result == 0
        assert "no ignore comments found" in output
