"""Scrum (agile) mode CLI backend.

契約: docs/plans/L7/L7-cli-helix-scrum-agile-implplan.md §2
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

try:
    from .paths import project_root as detect_project_root
except ImportError:  # pragma: no cover
    from paths import project_root as detect_project_root


STATE_DIR = Path(".helix") / "scrum-agile"


class ScrumAgileError(RuntimeError):
    """Raised when Scrum Agile input or state is invalid."""


@dataclass(frozen=True, slots=True)
class StateFile:
    relative_path: str
    initial_payload: dict[str, Any]


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


class ScrumAgileEngine:
    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or detect_project_root()).expanduser().resolve()
        self.state_dir = self.project_root / STATE_DIR
        self.files = (
            StateFile("backlog.yaml", {"version": 1, "items": []}),
            StateFile("sprint.yaml", {"version": 1, "active_sprint": None, "history": []}),
            StateFile("reviews.yaml", {"version": 1, "entries": []}),
            StateFile("retros.yaml", {"version": 1, "entries": []}),
            StateFile("increments.yaml", {"version": 1, "entries": []}),
        )

    def init_state(self) -> list[str]:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        created: list[str] = []
        for entry in self.files:
            path = self.state_dir / entry.relative_path
            if not path.exists():
                path.write_text(_dump_yaml(entry.initial_payload), encoding="utf-8")
            created.append(str(path.relative_to(self.project_root)))
        return created

    def _require_initialized(self) -> None:
        missing = [entry.relative_path for entry in self.files if not (self.state_dir / entry.relative_path).exists()]
        if missing:
            raise ScrumAgileError("state is not initialized; run `helix scrum-agile init` first")

    def _load_yaml(self, relative_name: str) -> dict[str, Any]:
        self._require_initialized()
        path = self.state_dir / relative_name
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(payload, dict):
            raise ScrumAgileError(f"invalid YAML payload: {relative_name}")
        return payload

    def _save_yaml(self, relative_name: str, payload: dict[str, Any]) -> None:
        path = self.state_dir / relative_name
        path.write_text(_dump_yaml(payload), encoding="utf-8")

    def _next_prefixed_id(self, rows: list[dict[str, Any]], prefix: str) -> str:
        max_value = 0
        for row in rows:
            raw_id = str(row.get("id") or row.get("sprint_id") or row.get("increment_id") or "")
            if raw_id.startswith(prefix):
                suffix = raw_id.removeprefix(prefix)
                if suffix.isdigit():
                    max_value = max(max_value, int(suffix))
        return f"{prefix}{max_value + 1:03d}"

    def list_backlog(self) -> list[dict[str, Any]]:
        return list(self._load_yaml("backlog.yaml").get("items") or [])

    def add_backlog_item(self, title: str, description: str, *, priority: str = "medium") -> dict[str, Any]:
        title = title.strip()
        description = description.strip()
        priority = priority.strip().lower()
        if not title:
            raise ScrumAgileError("title is required")
        if not description:
            raise ScrumAgileError("description is required")
        if priority not in {"low", "medium", "high"}:
            raise ScrumAgileError("priority must be one of low|medium|high")

        payload = self._load_yaml("backlog.yaml")
        items = list(payload.get("items") or [])
        item = {
            "id": self._next_prefixed_id(items, "SB-"),
            "title": title,
            "description": description,
            "priority": priority,
            "status": "todo",
            "created_at": _now_iso(),
        }
        items.append(item)
        payload["items"] = items
        self._save_yaml("backlog.yaml", payload)
        return item

    def _find_backlog_items(self, item_ids: list[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        payload = self._load_yaml("backlog.yaml")
        items = list(payload.get("items") or [])
        found: list[dict[str, Any]] = []
        for item_id in item_ids:
            matched = next((item for item in items if item["id"] == item_id), None)
            if matched is None:
                raise ScrumAgileError(f"backlog item not found: {item_id}")
            found.append(matched)
        return payload, found

    def plan_sprint(self, goal: str, item_ids: list[str]) -> dict[str, Any]:
        goal = goal.strip()
        if not goal:
            raise ScrumAgileError("goal is required")
        if not item_ids:
            raise ScrumAgileError("at least one --item is required")

        sprint_payload = self._load_yaml("sprint.yaml")
        if sprint_payload.get("active_sprint"):
            raise ScrumAgileError("active sprint already exists")

        backlog_payload, items = self._find_backlog_items(item_ids)
        for item in items:
            if item["status"] == "done":
                raise ScrumAgileError(f"backlog item already completed: {item['id']}")

        history = list(sprint_payload.get("history") or [])
        sprint = {
            "sprint_id": self._next_prefixed_id(history, "SPRINT-"),
            "goal": goal,
            "item_ids": [item["id"] for item in items],
            "status": "active",
            "reviewed": False,
            "retrospected": False,
            "started_at": _now_iso(),
        }
        sprint_payload["active_sprint"] = sprint
        self._save_yaml("sprint.yaml", sprint_payload)

        for item in backlog_payload["items"]:
            if item["id"] in sprint["item_ids"]:
                item["status"] = "planned"
        self._save_yaml("backlog.yaml", backlog_payload)
        return sprint

    def _active_sprint(self) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = self._load_yaml("sprint.yaml")
        active = payload.get("active_sprint")
        if not isinstance(active, dict):
            raise ScrumAgileError("active sprint is not found")
        return payload, active

    def record_review(self, summary: str, feedback: str) -> dict[str, Any]:
        summary = summary.strip()
        feedback = feedback.strip()
        if not summary:
            raise ScrumAgileError("summary is required")
        if not feedback:
            raise ScrumAgileError("feedback is required")

        sprint_payload, sprint = self._active_sprint()
        entry = {
            "sprint_id": sprint["sprint_id"],
            "summary": summary,
            "feedback": feedback,
            "recorded_at": _now_iso(),
        }
        reviews_payload = self._load_yaml("reviews.yaml")
        reviews = list(reviews_payload.get("entries") or [])
        reviews.append(entry)
        reviews_payload["entries"] = reviews
        self._save_yaml("reviews.yaml", reviews_payload)

        sprint["reviewed"] = True
        self._save_yaml("sprint.yaml", sprint_payload)
        return entry

    def record_retro(self, went_well: str, improve: str, action: str) -> dict[str, Any]:
        went_well = went_well.strip()
        improve = improve.strip()
        action = action.strip()
        if not went_well or not improve or not action:
            raise ScrumAgileError("went-well, improve, action are required")

        sprint_payload, sprint = self._active_sprint()
        entry = {
            "sprint_id": sprint["sprint_id"],
            "went_well": went_well,
            "improve": improve,
            "action": action,
            "recorded_at": _now_iso(),
        }
        retros_payload = self._load_yaml("retros.yaml")
        retros = list(retros_payload.get("entries") or [])
        retros.append(entry)
        retros_payload["entries"] = retros
        self._save_yaml("retros.yaml", retros_payload)

        sprint["retrospected"] = True
        self._save_yaml("sprint.yaml", sprint_payload)
        return entry

    def record_increment(self, title: str, summary: str) -> dict[str, Any]:
        title = title.strip()
        summary = summary.strip()
        if not title:
            raise ScrumAgileError("title is required")
        if not summary:
            raise ScrumAgileError("summary is required")

        sprint_payload, sprint = self._active_sprint()
        if not sprint.get("reviewed"):
            raise ScrumAgileError("review must be recorded before increment")
        if not sprint.get("retrospected"):
            raise ScrumAgileError("retro must be recorded before increment")

        increments_payload = self._load_yaml("increments.yaml")
        increments = list(increments_payload.get("entries") or [])
        increment = {
            "increment_id": self._next_prefixed_id(increments, "INC-"),
            "sprint_id": sprint["sprint_id"],
            "title": title,
            "summary": summary,
            "item_ids": list(sprint.get("item_ids") or []),
            "reverse_fullback_ready": True,
            "recommended_next_command": "helix reverse fullback",
            "recorded_at": _now_iso(),
        }
        increments.append(increment)
        increments_payload["entries"] = increments
        self._save_yaml("increments.yaml", increments_payload)

        backlog_payload = self._load_yaml("backlog.yaml")
        for item in backlog_payload.get("items") or []:
            if item["id"] in increment["item_ids"]:
                item["status"] = "done"
        self._save_yaml("backlog.yaml", backlog_payload)

        history = list(sprint_payload.get("history") or [])
        completed_sprint = dict(sprint)
        completed_sprint["status"] = "completed"
        completed_sprint["completed_at"] = _now_iso()
        history.append(completed_sprint)
        sprint_payload["history"] = history
        sprint_payload["active_sprint"] = None
        self._save_yaml("sprint.yaml", sprint_payload)
        return increment


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix scrum-agile")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    backlog = sub.add_parser("backlog")
    backlog_sub = backlog.add_subparsers(dest="backlog_command", required=True)
    backlog_add = backlog_sub.add_parser("add")
    backlog_add.add_argument("--title", required=True)
    backlog_add.add_argument("--description", required=True)
    backlog_add.add_argument("--priority", default="medium")
    backlog_sub.add_parser("list")

    plan = sub.add_parser("plan")
    plan.add_argument("--goal", required=True)
    plan.add_argument("--item", action="append", default=[])

    review = sub.add_parser("review")
    review.add_argument("--summary", required=True)
    review.add_argument("--feedback", required=True)

    retro = sub.add_parser("retro")
    retro.add_argument("--went-well", required=True)
    retro.add_argument("--improve", required=True)
    retro.add_argument("--action", required=True)

    increment = sub.add_parser("increment")
    increment.add_argument("--title", required=True)
    increment.add_argument("--summary", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    engine = ScrumAgileEngine()

    try:
        if args.command == "init":
            created = engine.init_state()
            print("[scrum-agile] initialized")
            for path in created:
                print(path)
            return 0

        if args.command == "backlog":
            if args.backlog_command == "add":
                item = engine.add_backlog_item(args.title, args.description, priority=args.priority)
                print(f"[scrum-agile] backlog item added: {item['id']} {item['title']}")
                return 0
            rows = engine.list_backlog()
            if not rows:
                print("backlog is empty")
                return 0
            for row in rows:
                print(f"{row['id']}\t{row['priority']}\t{row['status']}\t{row['title']}")
            return 0

        if args.command == "plan":
            sprint = engine.plan_sprint(args.goal, list(args.item))
            print(f"[scrum-agile] sprint planned: {sprint['sprint_id']}")
            print(f"goal: {sprint['goal']}")
            return 0

        if args.command == "review":
            entry = engine.record_review(args.summary, args.feedback)
            print(f"[scrum-agile] review recorded: {entry['sprint_id']}")
            return 0

        if args.command == "retro":
            entry = engine.record_retro(args.went_well, args.improve, args.action)
            print(f"[scrum-agile] retro recorded: {entry['sprint_id']}")
            return 0

        if args.command == "increment":
            entry = engine.record_increment(args.title, args.summary)
            print(f"[scrum-agile] increment completed: {entry['increment_id']}")
            print("reverse_fullback_ready: true")
            print(f"recommended_next_command: {entry['recommended_next_command']}")
            return 0
    except ScrumAgileError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
