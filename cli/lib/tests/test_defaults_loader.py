from pathlib import Path

import defaults_loader


def test_load_defaults_returns_classifier_keys():
    defaults_loader.load_defaults.cache_clear()

    defaults = defaults_loader.load_defaults()

    assert defaults["classifier"]["cache_ttl_sec"] == 3600
    assert defaults["classifier"]["llm_timeout_sec"] == 10
    assert defaults["classifier"]["boundary_scores"] == [3, 4, 7, 8, 12, 13]


def test_load_defaults_returns_recommender_keys():
    defaults_loader.load_defaults.cache_clear()

    defaults = defaults_loader.load_defaults()

    assert defaults["recommender"]["cache_ttl_sec"] == 3600
    assert defaults["recommender"]["default_top_n"] == 5


def test_load_defaults_fallback_when_file_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "defaults.yaml"
    monkeypatch.setattr(defaults_loader, "DEFAULTS_PATH", missing_path)
    defaults_loader.load_defaults.cache_clear()

    defaults = defaults_loader.load_defaults()

    assert defaults["classifier"]["cache_ttl_sec"] == 3600
    assert defaults["classifier"]["llm_timeout_sec"] == 10
    assert defaults["classifier"]["boundary_scores"] == [3, 4, 7, 8, 12, 13]
    assert defaults["recommender"]["cache_ttl_sec"] == 3600


def test_load_defaults_is_cached(monkeypatch, tmp_path):
    defaults_file = tmp_path / "defaults.yaml"
    defaults_file.write_text(
        "classifier:\n"
        "  cache_ttl_sec: 1\n"
        "  llm_timeout_sec: 2\n"
        "  boundary_scores: [3]\n"
        "recommender:\n"
        "  cache_ttl_sec: 4\n"
        "  default_top_n: 5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(defaults_loader, "DEFAULTS_PATH", Path(defaults_file))
    defaults_loader.load_defaults.cache_clear()

    first = defaults_loader.load_defaults()
    second = defaults_loader.load_defaults()

    assert first is second
