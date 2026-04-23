import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import model_fallback


def test_load_rules_reads_yaml_file(tmp_path: Path) -> None:
    config = tmp_path / "model-fallback.yaml"
    config.write_text(
        "version: 1\n"
        "rules:\n"
        "  - model: gpt-5.4\n"
        "    hold: true\n"
        "    trigger_pct: 95\n"
        "  - model: gpt-5.3-codex\n"
        "    same_tier: [gpt-5.4-mini]\n"
        "    trigger_pct: 90\n",
        encoding="utf-8",
    )

    rules = model_fallback.load_rules(config)

    assert rules == [
        {"model": "gpt-5.4", "hold": True, "trigger_pct": 95},
        {"model": "gpt-5.3-codex", "same_tier": ["gpt-5.4-mini"], "trigger_pct": 90},
    ]


def test_load_rules_returns_default_rules_when_yaml_has_no_rules_key(tmp_path: Path) -> None:
    config = tmp_path / "model-fallback.yaml"
    config.write_text("version: 1\ncurrent: gpt-5.4\n", encoding="utf-8")

    assert model_fallback.load_rules(config) == model_fallback.DEFAULT_RULES


def test_suggest_model_uses_fallback_when_threshold_exceeded() -> None:
    result = model_fallback.suggest_model(
        "gpt-5.3-codex",
        budget_snapshot={
            "codex": {
                "weekly_used_pct": 91,
                "by_model": {"gpt-5.3-codex": {"used_pct": 91}},
            }
        },
        effort="high",
        size="M",
    )

    assert result["recommended_model"] == "gpt-5.4"
    assert result["fallback_applied"] is True
    assert "effort=high" in result["reason"]


def test_suggest_model_returns_current_model_for_unknown_rule() -> None:
    result = model_fallback.suggest_model("unknown-model", budget_snapshot={"codex": {"weekly_used_pct": 99}})

    assert result == {
        "recommended_model": "unknown-model",
        "original_model": "unknown-model",
        "fallback_applied": False,
        "reason": "ルール未定義、現行維持",
    }
