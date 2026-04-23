"""budget.py — Claude/Codex 消費取得とキャッシュ・予測。

Minimum Viable 実装: ccusage / state.db があれば利用、なければフォールバック。
詳細仕様: docs/features/helix-budget-autothinking/D-ARCH/architecture.md
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

from helix_db import DEFAULT_SQLITE_TIMEOUT_SEC, get_connection


class BudgetCache:
    def __init__(self, cache_dir: Path | None = None, ttl_sec: int = 3600):
        self.cache_dir = cache_dir or Path(".helix/budget/cache")
        self.ttl_sec = ttl_sec

    def get(self, key: str) -> dict[str, Any] | None:
        p = self.cache_dir / f"{key}.json"
        if not p.exists():
            return None
        age = time.time() - p.stat().st_mtime
        if age > self.ttl_sec:
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            data["_cache_age_sec"] = int(age)
            return data
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        p = self.cache_dir / f"{key}.json"
        try:
            p.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


class ClaudeBudget:
    @staticmethod
    def get(home: Path | None = None) -> dict[str, Any]:
        home = home or Path(os.environ.get("HOME", "/tmp"))
        ccusage = shutil.which("ccusage")
        if ccusage:
            try:
                result = subprocess.run(
                    [ccusage, "--json"],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return {
                        "plan": "max",
                        "weekly_used_pct": int(data.get("weekly_usage_pct", 0)),
                        "weekly_remaining_pct": 100 - int(data.get("weekly_usage_pct", 0)),
                        "source": "ccusage",
                    }
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
                pass

        projects_dir = home / ".claude" / "projects"
        if not projects_dir.exists():
            return {
                "plan": "max",
                "weekly_used_pct": 0,
                "weekly_remaining_pct": 100,
                "source": "unavailable",
                "warning": "ccusage 未インストール かつ ~/.claude/projects/ 未存在",
            }

        line_count = 0
        for p in projects_dir.rglob("*.jsonl"):
            try:
                with p.open("r", encoding="utf-8", errors="ignore") as f:
                    for _ in f:
                        line_count += 1
                        if line_count > 100000:
                            break
            except OSError:
                continue
            if line_count > 100000:
                break

        approximate_pct = min(100, int(line_count / 500))
        return {
            "plan": "max",
            "weekly_used_pct": approximate_pct,
            "weekly_remaining_pct": 100 - approximate_pct,
            "source": "jsonl-fallback",
            "approx_line_count": line_count,
        }


class CodexBudget:
    @staticmethod
    def get(home: Path | None = None) -> dict[str, Any]:
        home = home or Path(os.environ.get("HOME", "/tmp"))
        state_db = home / ".codex" / "state.db"
        if not state_db.exists():
            return {
                "plan": "max",
                "five_hour_used_pct": 0,
                "weekly_used_pct": 0,
                "by_model": {},
                "source": "unavailable",
                "warning": "~/.codex/state.db 未存在",
            }

        try:
            conn = get_connection(db_path=state_db, timeout=DEFAULT_SQLITE_TIMEOUT_SEC)
            try:
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                five_hour = 0
                weekly = 0
                if "rollout_state" in tables:
                    try:
                        row = conn.execute(
                            "SELECT five_hour_pct, weekly_pct FROM rollout_state LIMIT 1"
                        ).fetchone()
                        if row:
                            five_hour = int(row[0] or 0)
                            weekly = int(row[1] or 0)
                    except sqlite3.Error:
                        pass
                return {
                    "plan": "max",
                    "five_hour_used_pct": five_hour,
                    "weekly_used_pct": weekly,
                    "by_model": {},
                    "source": "state.db",
                }
            finally:
                conn.close()
        except sqlite3.Error as e:
            return {
                "plan": "max",
                "five_hour_used_pct": 0,
                "weekly_used_pct": 0,
                "by_model": {},
                "source": "state.db-error",
                "warning": f"state.db query failed: {type(e).__name__}",
            }


class ForecastEngine:
    @staticmethod
    def predict(claude: dict, codex: dict, days: int = 7) -> dict[str, Any]:
        claude_pct = claude.get("weekly_used_pct", 0)
        codex_pct = codex.get("weekly_used_pct", 0)
        ratio = days / 7.0
        claude_fc = round(claude_pct * ratio, 1)
        codex_fc = round(codex_pct * ratio, 1)
        worst = max(claude_fc, codex_fc)
        if worst < 50:
            risk = "low"
        elif worst < 80:
            risk = "medium"
        elif worst < 100:
            risk = "high"
        else:
            risk = "critical"
        return {
            "days": days,
            "avg_daily_claude_pct": round(claude_pct / 7.0, 2),
            "avg_daily_codex_pct": round(codex_pct / 7.0, 2),
            "claude_forecast_pct": claude_fc,
            "codex_forecast_pct": codex_fc,
            "risk": risk,
        }


def collect_status(use_cache: bool = True) -> dict[str, Any]:
    cache = BudgetCache()
    if use_cache:
        hit = cache.get("status")
        if hit:
            hit["cached"] = True
            return hit

    claude = ClaudeBudget.get()
    codex = CodexBudget.get()
    recommendations: list[dict[str, str]] = []
    for label, data in (("Claude", claude), ("Codex", codex)):
        if data.get("weekly_used_pct", 0) >= 80:
            recommendations.append({
                "severity": "warning" if data["weekly_used_pct"] < 95 else "critical",
                "message": f"{label} 残 < 20% — 軽量タスクへの切り替え推奨",
            })
        if data.get("warning"):
            recommendations.append({"severity": "info", "message": data["warning"]})

    result = {
        "claude": claude,
        "codex": codex,
        "recommendations": recommendations,
        "cached": False,
    }
    cache.set("status", result)
    return result
