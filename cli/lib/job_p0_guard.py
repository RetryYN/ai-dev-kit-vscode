#!/usr/bin/env python3
"""契約: PLAN-091 §12."""

from __future__ import annotations

import argparse
import json
import os
import sys

import job_queue_helper


DEFAULT_PHASE = "P1"
VALID_PHASES = {"P1", "P2", "P3"}
AUTHORIZATION_ALIASES = {
    "explicit_consent": "explicit_consent",
    "wbs_match": "wbs_match",
    "current_wbs_match": "wbs_match",
    "handover_match": "handover_match",
    "handover_next_action_match": "handover_match",
}


def _normalize_phase(current_phase: str | None) -> str:
    phase = (current_phase or DEFAULT_PHASE).strip().upper()
    if phase not in VALID_PHASES:
        raise ValueError(f"current_phase must be one of: {', '.join(sorted(VALID_PHASES))}")
    return phase


def _normalize_authorized_by(authorized_by: str | None) -> tuple[set[str], list[str]]:
    raw = (authorized_by or "").strip()
    if not raw:
        return set(), []

    values: list[str]
    if raw.startswith("["):
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("authorized_by JSON must be a list")
        values = [str(item).strip() for item in parsed if str(item).strip()]
    else:
        values = [item.strip() for item in raw.replace("|", ",").split(",") if item.strip()]

    normalized: set[str] = set()
    unknown: list[str] = []
    for value in values:
        canonical = AUTHORIZATION_ALIASES.get(value)
        if canonical is None:
            unknown.append(value)
            continue
        normalized.add(canonical)
    return normalized, unknown


def validate_authorization(
    authorization_ref: str | None,
    source_plan_id: str | None,
    authorized_by: str | None,
    current_phase: str | None,
) -> tuple[bool, list[str]]:
    """PLAN-091 §12 の P0 guard 条件を評価する。"""
    phase = _normalize_phase(current_phase)
    matched, unknown = _normalize_authorized_by(authorized_by)
    messages: list[str] = []

    if not (authorization_ref or "").strip():
        messages.append("authorization_ref is required")
    if not (source_plan_id or "").strip():
        messages.append("source_plan_id is required")
    if unknown:
        messages.append("authorized_by contains unknown values: " + ", ".join(sorted(unknown)))
    if not matched:
        messages.append(
            "authorized_by must include one of: explicit_consent, wbs_match, handover_match"
        )

    if phase == "P1":
        return True, messages
    return len(messages) == 0, messages


def _resolve_phase(value: str | None) -> str:
    return _normalize_phase(
        value
        or os.getenv("HELIX_JOB_P0_PHASE")
        or os.getenv("HELIX_JOB_GUARD_PHASE")
        or os.getenv("HELIX_JOB_PHASE")
        or DEFAULT_PHASE
    )


def _env_or_arg(value: str | None, *env_names: str) -> str | None:
    if value:
        return value
    for env_name in env_names:
        env_value = os.getenv(env_name)
        if env_value:
            return env_value
    return None


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _pop_job(args: argparse.Namespace) -> int:
    phase = _resolve_phase(args.phase)
    authorization_ref = _env_or_arg(
        args.authorization_ref,
        "HELIX_JOB_AUTHORIZATION_REF",
        "HELIX_AUTHORIZATION_REF",
    )
    source_plan_id = _env_or_arg(
        args.source_plan_id,
        "HELIX_JOB_SOURCE_PLAN_ID",
        "HELIX_SOURCE_PLAN_ID",
    )
    authorized_by = _env_or_arg(
        args.authorized_by,
        "HELIX_JOB_AUTHORIZED_BY",
        "HELIX_AUTHORIZED_BY",
    )
    ok, messages = validate_authorization(
        authorization_ref,
        source_plan_id,
        authorized_by,
        phase,
    )
    if not ok:
        for message in messages:
            print(f"P0 guard: {message}", file=sys.stderr)
        return 2 if phase == "P3" else 1

    for message in messages:
        print(f"P0 guard warning: {message}", file=sys.stderr)

    job = job_queue_helper.claim_next_job(args.db_path)
    matched, _ = _normalize_authorized_by(authorized_by)
    _print_json(
        {
            "authorization": {
                "authorization_ref": authorization_ref,
                "authorized_by": sorted(matched),
                "phase": phase,
                "source_plan_id": source_plan_id,
            },
            "job": job,
            "messages": messages,
        }
    )
    return 0


def _worker_results(
    db_path: str,
    *,
    max_jobs: int | None = None,
    idle_sleep: float = 1.0,
) -> list[dict[str, object]]:
    if max_jobs is not None and int(max_jobs) < 1:
        raise ValueError("max_jobs must be >= 1")
    if idle_sleep < 0:
        raise ValueError("idle_sleep must be >= 0")

    results: list[dict[str, object]] = []
    processed = 0
    while max_jobs is None or processed < max_jobs:
        job = job_queue_helper.claim_next_job(db_path)
        if not job:
            if max_jobs is not None:
                break
            job_queue_helper.time.sleep(idle_sleep)
            continue
        ok, output = job_queue_helper.task_dispatcher.dispatch_task(
            job["task_type"],
            job["task_payload"],
        )
        updated = job_queue_helper.mark_completed(db_path, job["id"], ok, None if ok else output)
        processed += 1
        results.append(
            {
                "id": job["id"],
                "ok": ok,
                "output": output,
                "retry_count": updated["retry_count"] if updated else None,
                "status": updated["status"] if updated else None,
            }
        )
    return results


def _worker_job(args: argparse.Namespace) -> int:
    phase = _resolve_phase(args.phase)
    authorization_ref = _env_or_arg(
        args.authorization_ref,
        "HELIX_JOB_AUTHORIZATION_REF",
        "HELIX_AUTHORIZATION_REF",
    )
    source_plan_id = _env_or_arg(
        args.source_plan_id,
        "HELIX_JOB_SOURCE_PLAN_ID",
        "HELIX_SOURCE_PLAN_ID",
    )
    authorized_by = _env_or_arg(
        args.authorized_by,
        "HELIX_JOB_AUTHORIZED_BY",
        "HELIX_AUTHORIZED_BY",
    )
    ok, messages = validate_authorization(
        authorization_ref,
        source_plan_id,
        authorized_by,
        phase,
    )
    if not ok:
        for message in messages:
            print(f"P0 guard: {message}", file=sys.stderr)
        return 2 if phase == "P3" else 1

    for message in messages:
        print(f"P0 guard warning: {message}", file=sys.stderr)

    stale: list[dict[str, object]] = []
    if not args.no_requeue_stale:
        stale = job_queue_helper.requeue_stale_jobs(
            args.db_path,
            older_than=args.requeue_stale_older_than,
        )
    jobs = _worker_results(
        args.db_path,
        max_jobs=args.max_jobs,
        idle_sleep=args.idle_sleep,
    )
    payload: object = jobs if args.no_requeue_stale else {"jobs": jobs, "stale": stale}
    _print_json(payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="job_p0_guard")
    parser.add_argument("--db-path", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    pop = sub.add_parser("pop")
    pop.add_argument("--authorization-ref")
    pop.add_argument("--source-plan-id")
    pop.add_argument("--authorized-by")
    pop.add_argument("--phase")

    worker = sub.add_parser("worker")
    worker.add_argument("--authorization-ref")
    worker.add_argument("--source-plan-id")
    worker.add_argument("--authorized-by")
    worker.add_argument("--phase")
    worker.add_argument("--max-jobs", type=int)
    worker.add_argument("--idle-sleep", type=float, default=1.0)
    worker.add_argument("--requeue-stale-older-than", type=int, default=3600)
    worker.add_argument("--no-requeue-stale", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "pop":
        return _pop_job(args)
    if args.command == "worker":
        return _worker_job(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
