#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import helix_db


REDACTED = "***"
SEVERITIES = ("debug", "info", "warning", "error", "critical")
COMMON_DENYLIST = (
    r"password", r"passwd", r"api[_-]?key", r"secret", r"token",
    r"credential", r"authorization", r"bearer\s+[A-Za-z0-9._~+/=-]+",
    r"AKIA[0-9A-Z]{16}", r"ASIA[0-9A-Z]{16}", r"sk-[A-Za-z0-9._-]+",
    r"ghp_[A-Za-z0-9]+", r"xox[bap]-[A-Za-z0-9-]+",
)


def _compile_patterns(denylist: list[str] | None = None) -> list[re.Pattern[str]]:
    patterns = []
    for raw in [*COMMON_DENYLIST, *(denylist or [])]:
        if not raw:
            continue
        try:
            patterns.append(re.compile(str(raw), re.IGNORECASE))
        except re.error:
            patterns.append(re.compile(re.escape(str(raw)), re.IGNORECASE))
    return patterns


def load_local_denylist(path: Path | None = None) -> list[str]:
    denylist_path = path or Path.home() / ".config" / "helix" / "redaction-denylist.local.yaml"
    if not denylist_path.exists():
        return []
    entries = []
    for raw_line in denylist_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            line = line[1:].strip()
        if ":" in line:
            key, value = line.split(":", 1)
            if key.strip() not in {"pattern", "regex", "token", "value"}:
                continue
            line = value.strip()
        line = line.strip("\"'")
        if line:
            entries.append(line)
    return entries


def redact_data(data: dict, denylist: list) -> dict:
    patterns = _compile_patterns([str(item) for item in denylist])

    def should_redact(text: str) -> bool:
        return any(pattern.search(text) for pattern in patterns)

    def walk(value: Any, key_hint: str = "") -> Any:
        if key_hint and should_redact(key_hint):
            return REDACTED
        if isinstance(value, dict):
            return {str(key): walk(item, str(key)) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item, key_hint) for item in value]
        if isinstance(value, tuple):
            return [walk(item, key_hint) for item in value]
        if isinstance(value, str) and should_redact(value):
            return REDACTED
        return value

    if not isinstance(data, dict):
        raise ValueError("redact_data requires a dict")
    return walk(data)


def parse_tags(raw: str | None) -> dict[str, str]:
    if raw is None or raw.strip() == "":
        return {}
    tags = {}
    for item in raw.split(","):
        pair = item.strip()
        if not pair:
            continue
        if "=" not in pair:
            raise ValueError(f"invalid tag: {pair}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key):
            raise ValueError(f"invalid tag key: {key}")
        tags[key] = value.strip()
    if len(tags) > 20:
        raise ValueError("tags must contain at most 20 entries")
    return tags


def _parse_json_object(raw: str, field_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return parsed


def _parse_time_filter(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    raw = str(value).strip()
    if raw.isdigit():
        return int(raw)
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid ISO timestamp: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _decode_json_text(value: str | None) -> Any:
    if value is None or value == "":
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _row_to_event(row: Any) -> dict[str, Any]:
    return {
        "type": "event", "id": row["id"], "event_name": row["event_name"],
        "occurred_at": row["occurred_at"], "data": _decode_json_text(row["data_json"]),
        "source": row["source"], "severity": row["severity"],
    }


def _row_to_metric(row: Any) -> dict[str, Any]:
    return {
        "type": "metric", "id": row["id"], "metric_name": row["metric_name"],
        "value": row["value"], "tags": _decode_json_text(row["tags_json"]),
        "recorded_at": row["recorded_at"],
    }


def _redact_record(record: dict[str, Any], denylist: list[str] | None = None) -> dict[str, Any]:
    copied = dict(record)
    if isinstance(copied.get("data"), dict):
        copied["data"] = redact_data(copied["data"], denylist or load_local_denylist())
    if isinstance(copied.get("tags"), dict):
        copied["tags"] = redact_data(copied["tags"], denylist or load_local_denylist())
    return copied


def record_event(db_path, event_name, data, severity="info", source=None):
    return helix_db.insert_event(db_path, event_name, data, severity=severity, source=source)


def record_metric(db_path, metric_name, value, tags=None):
    return helix_db.insert_metric(db_path, metric_name, value, tags=tags)


def query_events(db_path, **filters) -> list:
    since = _parse_time_filter(filters.get("since"))
    until = _parse_time_filter(filters.get("until"))
    params, where = [], []
    if filters.get("event"):
        where.append("event_name = ?")
        params.append(filters["event"])
    if filters.get("severity"):
        where.append("severity = ?")
        params.append(filters["severity"])
    if since is not None:
        where.append("occurred_at >= ?")
        params.append(since)
    if until is not None:
        where.append("occurred_at <= ?")
        params.append(until)
    sql = "SELECT * FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY occurred_at DESC, id DESC"
    if filters.get("limit") is not None:
        sql += " LIMIT ?"
        params.append(int(filters["limit"]))
    conn = helix_db.get_connection(db_path)
    try:
        return [_row_to_event(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def query_metrics(db_path, **filters) -> list:
    since = _parse_time_filter(filters.get("since"))
    until = _parse_time_filter(filters.get("until"))
    params, where = [], []
    if filters.get("metric"):
        where.append("metric_name = ?")
        params.append(filters["metric"])
    if since is not None:
        where.append("recorded_at >= ?")
        params.append(since)
    if until is not None:
        where.append("recorded_at <= ?")
        params.append(until)
    sql = "SELECT * FROM metrics"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY recorded_at DESC, id DESC"
    if filters.get("limit") is not None:
        sql += " LIMIT ?"
        params.append(int(filters["limit"]))
    conn = helix_db.get_connection(db_path)
    try:
        return [_row_to_metric(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def _sanitize_metric_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_:]", "_", name)
    return sanitized if re.match(r"[A-Za-z_:]", sanitized) else f"_{sanitized}"


def _format_labels(tags: dict[str, Any]) -> str:
    labels = []
    for key in sorted(tags):
        label_key = str(key).replace(".", "_").replace("-", "_")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label_key):
            continue
        label_value = str(tags[key]).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
        labels.append(f'{label_key}="{label_value}"')
    return "{" + ",".join(labels) + "}" if labels else ""


def format_prometheus(events_or_metrics) -> str:
    lines = ["# HELP helix_events_total HELIX observed events", "# TYPE helix_events_total counter"]
    emitted = set()
    for item in events_or_metrics:
        if item.get("type") == "event":
            labels = _format_labels({
                "event": item.get("event_name", ""),
                "severity": item.get("severity", "info"),
                "source": item.get("source") or "",
            })
            lines.append(f"helix_events_total{labels} 1 {int(item.get('occurred_at', 0)) * 1000}")
            continue
        metric_name = _sanitize_metric_name(f"helix_{item.get('metric_name', 'metric')}")
        if metric_name not in emitted:
            lines.extend([f"# HELP {metric_name} HELIX observed metric", f"# TYPE {metric_name} gauge"])
            emitted.add(metric_name)
        labels = _format_labels(item.get("tags") if isinstance(item.get("tags"), dict) else {})
        lines.append(f"{metric_name}{labels} {float(item.get('value', 0.0))} {int(item.get('recorded_at', 0)) * 1000}")
    return "\n".join(lines) + "\n"


def format_json(events_or_metrics) -> str:
    return json.dumps(list(events_or_metrics), ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def format_text(events: list[dict[str, Any]], metrics: list[dict[str, Any]]) -> str:
    lines = ["HELIX observability report", f"events: {len(events)}"]
    for event in events:
        data = json.dumps(event["data"], ensure_ascii=False, sort_keys=True)
        lines.append(f"- event {event['event_name']} severity={event['severity']} source={event.get('source') or '-'} at={event['occurred_at']} data={data}")
    lines.append(f"metrics: {len(metrics)}")
    for metric in metrics:
        tags = json.dumps(metric["tags"], ensure_ascii=False, sort_keys=True)
        lines.append(f"- metric {metric['metric_name']} value={metric['value']} tags={tags} at={metric['recorded_at']}")
    return "\n".join(lines) + "\n"


def _query_combined(db_path: str, args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events, metrics = [], []
    if getattr(args, "metric", None) is None:
        events = query_events(db_path, event=getattr(args, "event", None), severity=getattr(args, "severity", None), since=getattr(args, "since", None), until=getattr(args, "until", None), limit=getattr(args, "limit", None))
    if getattr(args, "event", None) is None and getattr(args, "severity", None) is None:
        metrics = query_metrics(db_path, metric=getattr(args, "metric", None), since=getattr(args, "since", None), until=getattr(args, "until", None), limit=getattr(args, "limit", None))
    return events, metrics


def _quarantine_path(output: str) -> Path:
    quarantine = (Path.home() / ".helix" / "quarantine").resolve()
    quarantine.mkdir(parents=True, exist_ok=True)
    try:
        quarantine.chmod(0o700)
    except OSError:
        pass
    target = Path(output).expanduser().resolve(strict=False)
    if target != quarantine and quarantine not in target.parents:
        raise PermissionError(f"export output must be under {quarantine}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def _chmod_db(db_path: str) -> None:
    try:
        Path(db_path).chmod(0o600)
    except OSError:
        pass


def _audit_warning(db_path: str, event_name: str, reason: str) -> None:
    try:
        record_event(db_path, event_name, {"reason": reason}, severity="warning", source="helix-observe")
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helix observe", description="Record and export HELIX observability data")
    parser.add_argument("--db-path", default=helix_db.resolve_default_db_path())
    sub = parser.add_subparsers(dest="command", required=True)
    log = sub.add_parser("log", help="record an event")
    log.add_argument("--event", required=True)
    log.add_argument("--data", required=True)
    log.add_argument("--severity", choices=SEVERITIES, default="info")
    log.add_argument("--source")
    log.add_argument("--no-redact", action="store_true")
    metric = sub.add_parser("metric", help="record a metric")
    metric.add_argument("--name", required=True)
    metric.add_argument("--value", required=True, type=float)
    metric.add_argument("--tags")
    metric.add_argument("--no-redact", action="store_true")
    report = sub.add_parser("report", help="query observability data")
    report.add_argument("--event")
    report.add_argument("--metric")
    report.add_argument("--severity", choices=SEVERITIES)
    report.add_argument("--since")
    report.add_argument("--until")
    report.add_argument("--limit", type=int)
    report.add_argument("--format", choices=("text", "json"), default="text")
    export = sub.add_parser("export", help="export observability data")
    export.add_argument("--event")
    export.add_argument("--metric")
    export.add_argument("--severity", choices=SEVERITIES)
    export.add_argument("--since")
    export.add_argument("--until")
    export.add_argument("--format", choices=("json", "prometheus"), required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--include-secrets", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db_path = args.db_path
    try:
        if args.command == "log":
            data = _parse_json_object(args.data, "--data")
            if args.no_redact:
                print("warning: --no-redact is PM-only and may store sensitive values", file=sys.stderr)
                _audit_warning(db_path, "observability.no_redact", "--no-redact used")
            else:
                data = redact_data(data, load_local_denylist())
            row_id = record_event(db_path, args.event, data, severity=args.severity, source=args.source)
            _chmod_db(db_path)
            print(f"recorded event id={row_id}")
            return 0
        if args.command == "metric":
            tags = parse_tags(args.tags)
            if args.no_redact:
                print("warning: --no-redact is PM-only and may store sensitive values", file=sys.stderr)
                _audit_warning(db_path, "observability.no_redact", "--no-redact used for metric")
            else:
                tags = redact_data(tags, load_local_denylist())
            row_id = record_metric(db_path, args.name, args.value, tags=tags)
            _chmod_db(db_path)
            print(f"recorded metric id={row_id}")
            return 0
        if args.command == "report":
            events, metrics = _query_combined(db_path, args)
            denylist = load_local_denylist()
            events = [_redact_record(event, denylist) for event in events]
            metrics = [_redact_record(metric, denylist) for metric in metrics]
            print(format_json([*events, *metrics]) if args.format == "json" else format_text(events, metrics), end="")
            return 0
        if args.command == "export":
            try:
                output = _quarantine_path(args.output)
            except PermissionError as exc:
                print(f"OBS_05: {exc}", file=sys.stderr)
                return 1
            if args.include_secrets:
                print("warning: --include-secrets is PM-only and may export sensitive values", file=sys.stderr)
                _audit_warning(db_path, "observability.include_secrets", "--include-secrets used")
            events, metrics = _query_combined(db_path, args)
            records = [*events, *metrics]
            if not args.include_secrets:
                denylist = load_local_denylist()
                records = [_redact_record(record, denylist) for record in records]
            content = format_json(records) if args.format == "json" else format_prometheus(records)
            output.write_text(content, encoding="utf-8")
            print(f"exported path={output}")
            return 0
    except (ValueError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
