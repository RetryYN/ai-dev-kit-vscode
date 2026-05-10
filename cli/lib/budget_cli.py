"""budget_cli.py — helix-budget サブコマンドエントリ。"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from budget import ClaudeBudget, CodexBudget, ForecastEngine, collect_status
from effort_classifier import classify
from model_fallback import suggest_model


def _format_minutes_to_hours_minutes(minutes: int) -> str:
    minutes = max(0, int(minutes))
    hours, rem_minutes = divmod(minutes, 60)
    return f"{hours}h{rem_minutes}m"


def _print_claude_budget(c: dict[str, Any]) -> None:
    weekly_cost = c.get("weekly_cost_usd", 0)
    weekly_budget = c.get("weekly_budget_usd", 0)
    print(
        f"Claude (weekly ref $200): {c.get('weekly_used_pct', 0)}% used "
        f"/ {c.get('weekly_remaining_pct', 0)}% remaining "
        f"(${weekly_cost:.2f} of ${weekly_budget:.0f}, source: {c.get('source', '?')})"
    )
    if all(key in c for key in (
        "block_cost_usd",
        "block_burn_per_hour",
        "block_projected_cost",
        "block_remaining_minutes",
        "block_end_time",
    )):
        print(
            "Claude (5h block):        "
            f"${c['block_cost_usd']:.2f} used | "
            f"burn ${c['block_burn_per_hour']:.2f}/h | "
            f"proj ${c['block_projected_cost']:.2f} | "
            f"{_format_minutes_to_hours_minutes(c['block_remaining_minutes'])} remaining "
            f"(source: ccusage blocks)"
        )
        print(
            "  [note] $200 weekly は helix の reference budget。"
            "Anthropic 公式 weekly quota とは異なる"
        )
        print(
            "  [note] ccusage cost と Anthropic UI 表示は別 metric "
            "(cache/session weight 差)、UI 値は console.anthropic.com で確認"
        )


def _print_status(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    c = result.get("claude", {})
    x = result.get("codex", {})
    _print_claude_budget(c)
    print(f"Codex  ({x.get('plan', '?')}): {x.get('five_hour_used_pct', 0)}% (5h) "
          f"/ {x.get('weekly_used_pct', 0)}% (weekly)  (source: {x.get('source', '?')})")
    for rec in result.get("recommendations", []):
        print(f"  [{rec['severity']}] {rec['message']}")
    if result.get("cached"):
        print(f"  (cached {result.get('_cache_age_sec', 0)}s ago)")


def cmd_status(args) -> int:
    result = collect_status(use_cache=not args.no_cache)
    _print_status(result, args.json)
    return 0


def cmd_forecast(args) -> int:
    status = collect_status(use_cache=not args.no_cache)
    fc = ForecastEngine.predict(status["claude"], status["codex"], days=args.days)
    if args.json:
        print(json.dumps(fc, ensure_ascii=False, indent=2))
    else:
        print(f"days: {fc['days']}")
        print(f"  claude forecast: {fc['claude_forecast_pct']}%")
        print(f"  codex forecast:  {fc['codex_forecast_pct']}%")
        print(f"  risk: {fc['risk']}")
    return 0


def cmd_classify(args) -> int:
    if not args.task:
        print("error: --task is required", file=sys.stderr)
        return 2
    result = classify(
        args.task, role=args.role, size=args.size,
        files=args.files, lines=args.lines,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"effort: {result['effort']} (score={result['score']})")
        print(f"recommended_thinking: {result['recommended_thinking']}")
        if result.get("split_recommended"):
            print("  [warn] 分割推奨 (xhigh + S)", file=sys.stderr)
        print(f"breakdown: {result['breakdown']}")
        print(f"reason: {result['reason']}")
    return 0


def cmd_simulate(args) -> int:
    if not args.task:
        print("error: --task is required", file=sys.stderr)
        return 2
    cls = classify(args.task, role=args.role, size=args.size)
    budget = collect_status(use_cache=True)
    role_model = {
        "se": "gpt-5.3-codex", "pg": "gpt-5.3-codex-spark", "tl": "gpt-5.4",
        "qa": "gpt-5.3-codex", "security": "gpt-5.4", "dba": "gpt-5.4",
        "devops": "gpt-5.4", "docs": "gpt-5.4-mini", "research": "gpt-5.4",
        "legacy": "gpt-5.3-codex", "perf": "gpt-5.4", "fe": "gpt-5.3-codex",
    }
    current = role_model.get(args.role or "se", "gpt-5.3-codex")
    fb = suggest_model(current, budget, effort=cls["effort"], size=args.size or "M")
    result = {
        "recommended_model": fb["recommended_model"],
        "recommended_thinking": cls["recommended_thinking"],
        "fallback_applied": fb["fallback_applied"],
        "original_model": fb["original_model"],
        "reason": fb["reason"],
        "effort": cls["effort"],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"分類: effort={result['effort']}")
        print(f"推奨モデル: {result['recommended_model']} "
              f"(thinking={result['recommended_thinking']})")
        if result["fallback_applied"]:
            print(f"  [fallback] {result['original_model']} -> {result['recommended_model']}")
        print(f"理由: {result['reason']}")
    return 0


def cmd_cache(args) -> int:
    from pathlib import Path
    cache_dir = Path(".helix/budget/cache")
    if args.cache_action == "clear":
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        print("cache cleared")
        return 0
    if cache_dir.exists():
        files = list(cache_dir.glob("*.json"))
        print(f"cache entries: {len(files)}")
        for f in files:
            print(f"  {f.name} ({f.stat().st_size}B)")
    else:
        print("cache: empty")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix-budget")
    sub = parser.add_subparsers(dest="subcmd", required=True)

    p_s = sub.add_parser("status")
    p_s.add_argument("--json", action="store_true")
    p_s.add_argument("--no-cache", action="store_true")
    p_s.add_argument("--breakdown", action="store_true")
    p_s.set_defaults(func=cmd_status)

    p_f = sub.add_parser("forecast")
    p_f.add_argument("--days", type=int, default=7)
    p_f.add_argument("--json", action="store_true")
    p_f.add_argument("--no-cache", action="store_true")
    p_f.set_defaults(func=cmd_forecast)

    p_c = sub.add_parser("classify")
    p_c.add_argument("--task", required=True)
    p_c.add_argument("--role")
    p_c.add_argument("--size", choices=["S", "M", "L"])
    p_c.add_argument("--files", type=int)
    p_c.add_argument("--lines", type=int)
    p_c.add_argument("--json", action="store_true")
    p_c.set_defaults(func=cmd_classify)

    p_sim = sub.add_parser("simulate")
    p_sim.add_argument("--task", required=True)
    p_sim.add_argument("--role")
    p_sim.add_argument("--size", choices=["S", "M", "L"])
    p_sim.add_argument("--json", action="store_true")
    p_sim.set_defaults(func=cmd_simulate)

    p_ca = sub.add_parser("cache")
    p_ca.add_argument("cache_action", choices=["status", "clear"])
    p_ca.set_defaults(func=cmd_cache)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python < 3.7
    sys.exit(main())
