"""HELIX route engine.

契約: docs/plans/L7/L7-helix-route-implplan.md §2.B-§2.E
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TextIO


Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot"]
Priority = Literal["P0", "P1", "P2", "P3"]
Action = Literal["suggest_only", "immediate_plan_draft", "discovery_first", "emergency_routing"]
Severity = Literal["low", "high"]
Env = Literal["prod", "dev"]

SOURCE_SCHEMA = "helix_detect_run_json_v1"
VALID_SEVERITY = ("low", "high")
RECOVER_LINKED_SIGNALS = {"runaway", "regression_dev"}


class RouteEngineError(ValueError):
    """Unknown signal or invalid routing input."""


@dataclass(frozen=True, slots=True)
class RouteResult:
    signal: str
    mode: Mode
    kind: Kind
    subtype: str | None
    priority: Priority
    action: Action
    env: Env
    source_schema: str
    suggest_command: str
    recover_args: dict[str, str] | None
    plan_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RouteEngine:
    """検出シグナルを mode 固定 + 4 象限評価でルーティングする。"""

    SIGNAL_TO_MODE: dict[str, dict[str, str | None]] = {
        "drift": {"mode": "Reverse", "kind": "reverse", "subtype": "normalization"},
        "debt_degradation": {"mode": "Refactor", "kind": "refactor", "subtype": None},
        "regression_prod": {"mode": "Incident", "kind": "recovery", "subtype": None},
        "regression_dev": {"mode": "Recovery", "kind": "recovery", "subtype": None},
        "runaway": {"mode": "Recovery", "kind": "recovery", "subtype": None},
        "incident": {"mode": "Incident", "kind": "_env_dependent", "subtype": None},
        "unknown_design": {"mode": "Reverse", "kind": "reverse", "subtype": "code"},
    }

    DEPRECATED_ALIAS: dict[str, str] = {
        "degradation": "debt_degradation or regression_{prod,dev}",
    }

    PRIORITY_ACTION: dict[tuple[Severity, Severity], tuple[Priority, Action]] = {
        ("low", "low"): ("P3", "suggest_only"),
        ("low", "high"): ("P1", "immediate_plan_draft"),
        ("high", "low"): ("P2", "discovery_first"),
        ("high", "high"): ("P0", "emergency_routing"),
    }

    def __init__(self, stderr: TextIO | None = None) -> None:
        self._stderr = stderr if stderr is not None else sys.stderr

    def evaluate(
        self,
        signal: str,
        uncertainty: Severity = "low",
        impact: Severity = "low",
        env: Env | None = None,
        reopen_point: str = "HEAD",
    ) -> RouteResult:
        signal_id = self._normalize_signal(signal)
        normalized_uncertainty = self._normalize_severity("uncertainty", uncertainty)
        normalized_impact = self._normalize_severity("impact", impact)
        normalized_env = self._resolve_env(signal_id, env)
        route = self._resolve_route(signal_id, normalized_env)
        priority, action = self.PRIORITY_ACTION[(normalized_uncertainty, normalized_impact)]
        suggest_command, recover_args = self._build_suggest_command(signal_id, route["kind"], normalized_env, reopen_point)
        plan_hint = self._build_plan_hint(signal_id, route["mode"], priority, action)
        return RouteResult(
            signal=signal_id,
            mode=route["mode"],
            kind=route["kind"],
            subtype=route["subtype"],
            priority=priority,
            action=action,
            env=normalized_env,
            source_schema=SOURCE_SCHEMA,
            suggest_command=suggest_command,
            recover_args=recover_args,
            plan_hint=plan_hint,
        )

    def from_detect_output(self, detect_run_json: dict[str, Any] | list[dict[str, Any]]) -> list[RouteResult]:
        items: list[dict[str, Any]]
        if isinstance(detect_run_json, dict):
            if {"detector", "status", "result"} <= set(detect_run_json.keys()):
                items = [detect_run_json]
            elif {"axes", "counts"} <= set(detect_run_json.keys()) or "route_events" in detect_run_json:
                raise ValueError("adapter required for cross-detection/dashboard/route_events schema")
            else:
                raise ValueError("unsupported detect schema; expected detector/status/result")
        elif isinstance(detect_run_json, list):
            items = detect_run_json
        else:
            raise ValueError("unsupported detect schema; expected list or dict")

        results: list[RouteResult] = []
        for item in items:
            if not isinstance(item, dict) or {"detector", "status", "result"} - set(item.keys()):
                raise ValueError("unsupported detect schema; expected detector/status/result")
            result = item.get("result")
            if not isinstance(result, dict):
                raise ValueError("unsupported detect schema; result must be an object")
            results.append(
                self.evaluate(
                    str(item["status"]),
                    uncertainty=str(result.get("uncertainty", "low")),
                    impact=str(result.get("impact", "low")),
                    env=self._env_from_result(result),
                    reopen_point=str(result.get("reopen_point", "HEAD")),
                )
            )
        return results

    def list_signals(self) -> list[dict[str, Any]]:
        items = [
            {
                "signal": signal,
                "mode": values["mode"],
                "kind": self._display_kind(signal, "dev"),
                "subtype": values["subtype"],
                "deprecated": False,
            }
            for signal, values in self.SIGNAL_TO_MODE.items()
        ]
        items.append(
            {
                "signal": "degradation",
                "mode": "alias",
                "kind": "alias",
                "subtype": None,
                "deprecated": True,
                "replacement": self.DEPRECATED_ALIAS["degradation"],
            }
        )
        return items

    def _normalize_signal(self, signal: str) -> str:
        signal_id = signal.strip()
        if signal_id in self.DEPRECATED_ALIAS:
            replacement = self.DEPRECATED_ALIAS[signal_id]
            print(
                f"deprecation warning: '{signal_id}' is deprecated; use {replacement}",
                file=self._stderr,
            )
            return "debt_degradation"
        if signal_id not in self.SIGNAL_TO_MODE:
            raise RouteEngineError(f"unknown signal: {signal_id}")
        return signal_id

    def _normalize_severity(self, label: str, value: str) -> Severity:
        normalized = value.strip().lower()
        if normalized not in VALID_SEVERITY:
            raise RouteEngineError(f"invalid {label}: {value}")
        return normalized  # type: ignore[return-value]

    def _resolve_env(self, signal: str, env: str | None) -> Env:
        if signal in {"incident", "regression_prod"}:
            if env is None or not str(env).strip():
                raise ValueError(f"env is required for signal={signal}")
        normalized = str(env).strip().lower() if env is not None else "dev"
        if normalized not in {"dev", "prod"}:
            raise ValueError(f"invalid env: {env}")
        return normalized  # type: ignore[return-value]

    def _resolve_route(self, signal: str, env: Env) -> dict[str, Any]:
        mapping = self.SIGNAL_TO_MODE[signal]
        mode = mapping["mode"]
        subtype = mapping["subtype"]
        kind = mapping["kind"]
        if signal == "incident":
            kind = "recovery" if env == "prod" else "troubleshoot"
        return {
            "mode": mode,
            "kind": kind,
            "subtype": subtype,
        }

    def _build_suggest_command(
        self,
        signal: str,
        kind: Kind,
        env: Env,
        reopen_point: str,
    ) -> tuple[str, dict[str, str] | None]:
        if signal in RECOVER_LINKED_SIGNALS or (signal == "incident" and env == "prod"):
            recover_args = {
                "signal_id": signal,
                "reopen_point": reopen_point,
                "auto_routed_from": "helix-route",
            }
            return (
                "helix recover plan "
                f"--signal-id {signal} --reopen-point {reopen_point} --auto-routed-from helix-route",
                recover_args,
            )
        return (f"helix plan draft --kind {kind}", None)

    def _build_plan_hint(self, signal: str, mode: Mode, priority: Priority, action: Action) -> str:
        return f"{signal} routed to {mode} ({priority}, {action})"

    def _display_kind(self, signal: str, env: Env) -> str:
        return str(self._resolve_route(signal, env)["kind"])

    @staticmethod
    def _env_from_result(result: dict[str, Any]) -> str | None:
        value = result.get("env")
        if value is None:
            return None
        return str(value)


def _load_json_input(path: str) -> Any:
    if path in {"-", "/dev/stdin"}:
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _print_route_help() -> None:
    print(
        "Usage: helix route <eval|list-signals|help> [args...]\n\n"
        "Commands:\n"
        "  eval          signal または detect JSON から route を評価\n"
        "  list-signals  登録済 signal と alias を表示\n"
        "  help          この usage を表示\n"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix route", add_help=False)
    sub = parser.add_subparsers(dest="command")

    eval_parser = sub.add_parser("eval")
    source_group = eval_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--signal")
    source_group.add_argument("--from-json")
    eval_parser.add_argument("--uncertainty", default="low")
    eval_parser.add_argument("--impact", default="low")
    eval_parser.add_argument("--env")
    eval_parser.add_argument("--reopen-point", default="HEAD")
    eval_parser.add_argument("--format", choices=("json", "command"), default="json")

    list_parser = sub.add_parser("list-signals")
    list_parser.add_argument("--json", action="store_true")

    sub.add_parser("help")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command in {None, "help"}:
        _print_route_help()
        return 0

    engine = RouteEngine()
    try:
        if args.command == "list-signals":
            items = engine.list_signals()
            if args.json:
                print(json.dumps(items, ensure_ascii=False, sort_keys=True))
            else:
                for item in items:
                    line = f"{item['signal']} mode={item['mode']} kind={item['kind']}"
                    if item.get("subtype"):
                        line += f" subtype={item['subtype']}"
                    if item.get("deprecated"):
                        line += f" deprecated replacement={item['replacement']}"
                    print(line)
            return 0

        if args.from_json:
            results = engine.from_detect_output(_load_json_input(args.from_json))
            if args.format == "command":
                for result in results:
                    print(result.suggest_command)
            else:
                print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, sort_keys=True))
            return 0

        result = engine.evaluate(
            args.signal,
            uncertainty=args.uncertainty,
            impact=args.impact,
            env=args.env,
            reopen_point=args.reopen_point,
        )
        if args.format == "command":
            print(result.suggest_command)
        else:
            print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
        return 0
    except (RouteEngineError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
