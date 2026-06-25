from __future__ import annotations

from cli.lib.v3.doctor import V3DoctorReport, format_report, run_v3_doctor

KEY_TABLES = {"plan_registry", "artifact_registry", "test_cases", "functional_registry", "trace_edges"}


def test_run_v3_doctor_end_to_end(tmp_path):
    # project_test_files は path 非依存(.py の def test_*)なので fixture で確実に投影される
    (tmp_path / "test_x.py").write_text("def test_a():\n    pass\n\ndef test_b():\n    pass\n", encoding="utf-8")

    report = run_v3_doctor(str(tmp_path))

    assert isinstance(report, V3DoctorReport)
    assert set(report.projection_counts) >= KEY_TABLES
    assert report.projection_counts["test_cases"] == 2  # rebuild が走った証拠
    assert isinstance(report.ok, bool)
    assert isinstance(report.total_findings, int)


def test_format_report_renders_counts(tmp_path):
    (tmp_path / "test_y.py").write_text("def test_c():\n    pass\n", encoding="utf-8")
    text = format_report(run_v3_doctor(str(tmp_path)))
    assert "V3 doctor:" in text
    assert "test_cases=1" in text
