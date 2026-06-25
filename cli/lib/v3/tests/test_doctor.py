from __future__ import annotations

from cli.lib.v3.doctor import V3DoctorReport, format_report, run_v3_doctor


def test_run_v3_doctor_end_to_end(tmp_path):
    (tmp_path / "plan.md").write_text(
        "---\nplan_id: P-1\nkind: impl\nlayer: L7\ndrive: be\nstatus: draft\n---\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / "test_x.py").write_text("def test_a():\n    pass\n", encoding="utf-8")

    report = run_v3_doctor(str(tmp_path))

    assert isinstance(report, V3DoctorReport)
    assert report.projection_counts["plan_registry"] == 1
    assert report.projection_counts["test_cases"] == 1
    assert isinstance(report.ok, bool)
    assert isinstance(report.total_findings, int)


def test_format_report_renders_counts(tmp_path):
    (tmp_path / "plan.md").write_text(
        "---\nplan_id: P-2\nkind: impl\nlayer: L7\ndrive: be\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    text = format_report(run_v3_doctor(str(tmp_path)))
    assert "V3 doctor:" in text
    assert "plan_registry=1" in text
