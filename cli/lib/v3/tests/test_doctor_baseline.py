from __future__ import annotations

from cli.lib.v3.doctor import build_current_baseline, run_v3_doctor


def test_doctor_is_green_with_its_own_baseline(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    baseline = build_current_baseline(str(tmp_path))
    # 同じ state から作った baseline で doctor は緑(既知 debt grandfather = regression 検出器)
    assert run_v3_doctor(str(tmp_path), baselines=baseline).ok is True


def test_doctor_red_without_baseline_on_violations(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    # baseline 無し: absence/violation で赤(engine が問題を検出している証拠)
    assert run_v3_doctor(str(tmp_path)).ok is False


def test_build_current_baseline_returns_per_detector_subjects(tmp_path):
    (tmp_path / "test_x.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
    baseline = build_current_baseline(str(tmp_path))
    assert isinstance(baseline, dict)
    assert all(isinstance(v, frozenset) for v in baseline.values())
