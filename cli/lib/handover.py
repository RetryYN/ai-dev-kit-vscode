#!/usr/bin/env python3
"""helix handover コアロジック (JSON + Markdown)。"""

import argparse
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_CHECK_FAILED = 1
EXIT_INPUT_ERROR = 2
EXIT_PREREQ_ERROR = 3
EXIT_INTERNAL_ERROR = 127

ALLOWED_OWNER = {"opus", "codex"}
ALLOWED_SCOPE = {"backend"}
ALLOWED_PHASE = {f"L{i}" for i in range(1, 9)}
ALLOWED_SPRINT = {".1a", ".1b", ".2", ".3", ".4", ".5"}
ALLOWED_STATUS = {"in_progress", "blocked", "ready_for_review", "escalated"}
ALLOWED_STATUS_UPDATE = {"in_progress", "blocked", "ready_for_review"}
SHA40_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class HandoverError(Exception):
    def __init__(self, message, exit_code=EXIT_CHECK_FAILED):
        super().__init__(message)
        self.exit_code = exit_code


def now_iso():
    return datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()


def archive_stamp():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H-%M-%S")


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def read_text(path):
    return path.read_text(encoding="utf-8")


def write_text(path, content):
    path.write_text(content, encoding="utf-8")


def load_json(path):
    try:
        return json.loads(read_text(path))
    except FileNotFoundError as exc:
        raise HandoverError(f"CURRENT.json が見つかりません: {path}", EXIT_PREREQ_ERROR) from exc
    except json.JSONDecodeError as exc:
        raise HandoverError(f"CURRENT.json の JSON 解析に失敗: {exc}", EXIT_INPUT_ERROR) from exc


def dump_json(path, payload):
    ensure_dir(path.parent)
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def normalize_list_value(raw):
    items = []
    if raw is None:
        return items
    for part in raw.split(","):
        value = part.strip()
        if value:
            items.append(value)
    return items


def parse_tests(raw_values):
    tests = []
    for raw in raw_values or []:
        for chunk in raw.split(";"):
            cmd = chunk.strip()
            if cmd:
                tests.append(cmd)
    return tests


def run_git(project_root, args, strict=True):
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise HandoverError("git timeout", EXIT_PREREQ_ERROR) from exc
    if proc.returncode != 0:
        if strict:
            msg = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
            raise HandoverError(f"git コマンド失敗: {' '.join(args)}: {msg}", EXIT_PREREQ_ERROR)
        return None
    return proc.stdout.strip()


def _unique_nonempty(items):
    seen = set()
    out = []
    for raw in items:
        value = str(raw).strip().replace("\\", "/")
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _collect_changed_files(project_root):
    files = []
    commands = [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except Exception:
            continue
        if proc.returncode != 0:
            continue
        files.extend(line for line in proc.stdout.splitlines() if line.strip())
    return _unique_nonempty(files)


def _load_fe_feature_ids(project_root):
    matrix_path = project_root / ".helix" / "matrix.yaml"
    if not matrix_path.exists():
        return set()

    payload = None
    try:
        from matrix_compiler import load_yaml as _matrix_load_yaml

        payload = _matrix_load_yaml(matrix_path)
    except Exception:
        try:
            from yaml_parser import parse_yaml as _parse_yaml

            payload = _parse_yaml(matrix_path.read_text(encoding="utf-8"))
        except Exception:
            return set()

    if not isinstance(payload, dict):
        return set()
    features = payload.get("features")
    if not isinstance(features, dict):
        return set()

    fe_ids = set()
    for feature_id, raw in features.items():
        if not isinstance(feature_id, str) or not isinstance(raw, dict):
            continue
        if str(raw.get("drive", "")).strip().lower() == "fe":
            fe_ids.add(feature_id)
    return fe_ids


def _is_fe_path(path, fe_feature_ids):
    normalized = str(path).strip().replace("\\", "/")
    if not normalized:
        return False
    lower = normalized.lower()

    if lower.endswith((".tsx", ".jsx", ".vue")):
        return True
    if "/d-vis/" in lower:
        return True
    if "/fe/" in lower:
        return True

    with_slashes = f"/{normalized}"
    for feature_id in fe_feature_ids:
        marker = f"/features/{feature_id}/"
        if marker in with_slashes:
            return True
    return False


def detect_fe_drift(project_root, changed_files=None):
    files = changed_files if changed_files is not None else _collect_changed_files(project_root)
    fe_feature_ids = _load_fe_feature_ids(project_root)
    return [path for path in files if _is_fe_path(path, fe_feature_ids)]


def _run_drift_check(project_root, changed_files):
    drift_check = Path(__file__).resolve().parents[1] / "helix-drift-check"
    if not drift_check.exists():
        return

    for rel_path in changed_files:
        target = str((project_root / rel_path).resolve())
        try:
            proc = subprocess.run(
                [str(drift_check), target],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except Exception as exc:
            print(f"[handover] WARN: drift-check 実行失敗 ({rel_path}): {exc}", file=sys.stderr)
            continue

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            print(f"[handover] WARN: drift-check 失敗 ({rel_path}): {detail}", file=sys.stderr)


def _write_auto_escalation(escalation_path, state, fe_files):
    timestamp = now_iso()
    lines = [
        "# HELIX Auto Escalation",
        "",
        f"Timestamp: {timestamp}",
        "From: handover update (auto detection)",
        f"Task: {state['task']['id']} {state['task']['title']} ({state['phase']} Sprint {state['sprint']})",
        "",
        "## Reason",
        "scope=backend のまま FE 変更を検知しました。",
        "",
        "## FE Drift Files",
    ]
    lines.extend(f"- {path}" for path in fe_files)
    lines.extend(
        [
            "",
            "## CURRENT snapshot",
            "```json",
            json.dumps(state, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    block = "\n".join(lines)

    ensure_dir(escalation_path.parent)
    if escalation_path.exists():
        existing = read_text(escalation_path).rstrip()
        write_text(escalation_path, existing + "\n\n---\n\n" + block)
    else:
        write_text(escalation_path, block)


def lock_open(lock_path):
    ensure_dir(lock_path.parent)
    fh = lock_path.open("a+", encoding="utf-8")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def lock_close(lock_fh):
    try:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
    finally:
        lock_fh.close()


def validate_sprint(value, field_name="sprint"):
    if value is None:
        return
    if value not in ALLOWED_SPRINT:
        raise HandoverError(
            f"{field_name} は {sorted(ALLOWED_SPRINT)} のいずれかである必要があります: {value}",
            EXIT_INPUT_ERROR,
        )


def validate_phase(value):
    if value not in ALLOWED_PHASE:
        raise HandoverError(
            f"phase は L1〜L8 のみ許可されています: {value}",
            EXIT_INPUT_ERROR,
        )


def validate_state(state):
    owner = state.get("owner")
    if owner not in ALLOWED_OWNER:
        raise HandoverError(f"owner は opus/codex のみ許可されています: {owner}", EXIT_INPUT_ERROR)

    scope = state.get("scope")
    if scope not in ALLOWED_SCOPE:
        raise HandoverError(f"scope は backend のみ許可されています: {scope}", EXIT_INPUT_ERROR)

    phase = state.get("phase")
    validate_phase(phase)

    sprint = state.get("sprint")
    if sprint is not None:
        validate_sprint(sprint)

    task = state.get("task", {})
    status = task.get("status")
    if status not in ALLOWED_STATUS:
        raise HandoverError(f"task.status が不正です: {status}", EXIT_INPUT_ERROR)

    git_info = state.get("git", {})
    sha = git_info.get("head_sha", "")
    if not isinstance(sha, str) or not SHA40_RE.fullmatch(sha):
        raise HandoverError("git.head_sha は 40 桁 full SHA 必須です", EXIT_INPUT_ERROR)

    if not isinstance(state.get("revision"), int):
        raise HandoverError("revision は integer 必須です", EXIT_INPUT_ERROR)


def current_paths(handover_dir):
    return {
        "json": handover_dir / "CURRENT.json",
        "md": handover_dir / "CURRENT.md",
        "escalation": handover_dir / "ESCALATION.md",
        "archive": handover_dir / "archive",
        "lock": handover_dir / ".lock",
    }


def load_template(name):
    template_path = Path(__file__).resolve().parent.parent / "templates" / name
    if not template_path.exists():
        raise HandoverError(f"template が見つかりません: {template_path}", EXIT_INTERNAL_ERROR)
    return read_text(template_path)


def render_json_template(state):
    tmpl = load_template("handover-current.json.template")
    mapping = {
        "SCHEMA_VERSION": json.dumps(state["schema_version"], ensure_ascii=False),
        "GENERATED_AT": json.dumps(state["generated_at"], ensure_ascii=False),
        "UPDATED_AT": json.dumps(state["updated_at"], ensure_ascii=False),
        "REVISION": json.dumps(state["revision"], ensure_ascii=False),
        "OWNER": json.dumps(state["owner"], ensure_ascii=False),
        "SCOPE": json.dumps(state["scope"], ensure_ascii=False),
        "BRANCH": json.dumps(state["git"]["branch"], ensure_ascii=False),
        "HEAD_SHA": json.dumps(state["git"]["head_sha"], ensure_ascii=False),
        "DIRTY": json.dumps(state["git"]["dirty"], ensure_ascii=False),
        "PHASE": json.dumps(state["phase"], ensure_ascii=False),
        "SPRINT": json.dumps(state["sprint"], ensure_ascii=False),
        "PROJECT": json.dumps(state["project"], ensure_ascii=False),
        "TASK_ID": json.dumps(state["task"]["id"], ensure_ascii=False),
        "TASK_TITLE": json.dumps(state["task"]["title"], ensure_ascii=False),
        "TASK_STATUS": json.dumps(state["task"]["status"], ensure_ascii=False),
        "D_API": json.dumps(state["contracts"]["d_api"], ensure_ascii=False),
        "D_DB": json.dumps(state["contracts"]["d_db"], ensure_ascii=False),
        "D_CONTRACT": json.dumps(state["contracts"]["d_contract"], ensure_ascii=False),
        "TARGET": json.dumps(state["files"]["target"], ensure_ascii=False),
        "COMPLETED": json.dumps(state["files"]["completed"], ensure_ascii=False),
        "PENDING": json.dumps(state["files"]["pending"], ensure_ascii=False),
        "TESTS": json.dumps(state["tests"], ensure_ascii=False),
    }
    rendered = tmpl
    for key, value in mapping.items():
        rendered = rendered.replace(f"__{key}__", value)
    return json.loads(rendered)


def default_next_action(state):
    pending = state.get("files", {}).get("pending", [])
    if not pending:
        return "1. `helix handover status --json` で状態を確認\n2. 必要作業を進め、完了後に `helix handover update --status ready_for_review`"

    lines = []
    for idx, path in enumerate(pending, 1):
        lines.append(f"{idx}. `{path}` を進める")
    lines.append(f"{len(lines) + 1}. 完了後に `helix handover update --status ready_for_review` で更新")
    return "\n".join(lines)


def render_md_template(state, next_action, dump_note):
    tmpl = load_template("handover-current.md.template")
    task_line = f"{state['task']['id']} {state['task']['title']} ({state['phase']} Sprint {state['sprint']})"
    replaced = (
        tmpl.replace("__TASK_LINE__", task_line)
        .replace("__NEXT_ACTION__", next_action)
        .replace("__TIMESTAMP__", state["generated_at"])
        .replace("__OWNER__", state["owner"])
        .replace("__STATUS__", state["task"]["status"])
        .replace("__DUMP_NOTE__", dump_note)
    )
    return replaced.strip() + "\n"


def ensure_md_exists(md_path, state):
    if md_path.exists():
        return
    next_action = default_next_action(state)
    write_text(md_path, render_md_template(state, next_action, "初期 dump"))


def append_event(md_path, event_type, owner, body, status=None, timestamp=None):
    ts = timestamp or now_iso()
    suffix = f", status: {status}" if status else ""
    event_header = f"### [{ts}] {event_type} (owner: {owner}{suffix})"
    event_body = body.strip() if body and body.strip() else "(no detail)"

    with md_path.open("a", encoding="utf-8") as fh:
        fh.write("\n")
        fh.write("\n")
        fh.write(event_header)
        fh.write("\n")
        fh.write(event_body)
        fh.write("\n")


def replace_next_action(md_text, new_next_action):
    pattern = re.compile(
        r"(## Next Action \(Codex 向け\)\n)(.*?)(\n## イベントログ\n)",
        re.DOTALL,
    )
    m = pattern.search(md_text)
    if not m:
        raise HandoverError("CURRENT.md の Next Action セクションを検出できません", EXIT_INPUT_ERROR)
    replacement = m.group(1) + new_next_action.rstrip() + "\n" + m.group(3)
    return md_text[: m.start()] + replacement + md_text[m.end() :]


def read_next_action(md_text):
    m = re.search(r"## Next Action \(Codex 向け\)\n(.*?)(\n## イベントログ\n)", md_text, re.DOTALL)
    if not m:
        return ""
    return m.group(1).strip()


def archive_current(paths):
    stamp = archive_stamp()
    archive_dir = paths["archive"] / stamp
    idx = 1
    while archive_dir.exists():
        archive_dir = paths["archive"] / f"{stamp}-{idx}"
        idx += 1
    ensure_dir(archive_dir)

    pairs = []
    for name in ("json", "md", "escalation"):
        src = paths[name]
        pairs.append((src, archive_dir / src.name))

    tmp_staging = Path(tempfile.mkdtemp(prefix="helix-handover-archive-"))
    staged = []
    try:
        for src, dst in pairs:
            if not src.exists():
                continue
            tmp = tmp_staging / src.name
            shutil.copy2(src, tmp)
            staged.append((src, dst, tmp))
    except Exception:
        shutil.rmtree(tmp_staging, ignore_errors=True)
        raise HandoverError("archive staging failed", EXIT_CHECK_FAILED) from None

    if not staged:
        shutil.rmtree(tmp_staging, ignore_errors=True)
        raise HandoverError("archive 対象ファイルが存在しません", EXIT_CHECK_FAILED)

    completed = []
    try:
        for src, dst, tmp in staged:
            os.replace(tmp, dst)
            completed.append((src, dst))
        for src, _dst in completed:
            src.unlink(missing_ok=True)
    except Exception as exc:
        for src, dst in reversed(completed):
            try:
                os.replace(dst, src)
            except Exception as rollback_exc:
                print(
                    f"[handover] WARN: archive rollback failed: {dst} -> {src}: {rollback_exc}. "
                    "手動リカバリが必要な可能性があります",
                    file=sys.stderr,
                )
        raise HandoverError(f"archive commit failed: {exc}", EXIT_CHECK_FAILED) from exc
    finally:
        shutil.rmtree(tmp_staging, ignore_errors=True)

    return archive_dir


def atomic_write_json_with_revision(current_json, new_state, expected_revision):
    tmp = current_json.parent / f"{current_json.name}.tmp.{os.getpid()}"
    dump_json(tmp, new_state)

    test_sleep = os.environ.get("HELIX_HANDOVER_TEST_SLEEP_SEC", "").strip()
    if test_sleep:
        subprocess.run(["sleep", test_sleep], capture_output=True, text=True, check=False)

    latest = load_json(current_json)
    latest_rev = latest.get("revision")
    if latest_rev != expected_revision:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise HandoverError("revision conflict", EXIT_CHECK_FAILED)

    os.replace(tmp, current_json)


def transition_status(current_status, next_status):
    if next_status == "escalated":
        raise HandoverError("update --status escalated は禁止です。helix handover escalate を使用してください", EXIT_INPUT_ERROR)

    allowed = {
        ("in_progress", "blocked"),
        ("blocked", "in_progress"),
        ("in_progress", "ready_for_review"),
    }
    if (current_status, next_status) not in allowed:
        raise HandoverError(f"不正な status 遷移です: {current_status} -> {next_status}", EXIT_CHECK_FAILED)


def stale_check(state, project_root, enabled):
    if not enabled:
        return False, []

    reasons = []
    saved_git = state.get("git", {})

    current_branch = run_git(project_root, ["rev-parse", "--abbrev-ref", "HEAD"], strict=False)
    if current_branch is None or current_branch != saved_git.get("branch"):
        reasons.append("branch_mismatch")

    saved_sha = saved_git.get("head_sha", "")
    log_text = run_git(project_root, ["log", "--format=%H", "-n", "50"], strict=False)
    if not SHA40_RE.fullmatch(saved_sha):
        reasons.append("head_sha_unreachable")
    elif log_text is None:
        reasons.append("head_sha_unreachable")
    else:
        reachable = set(line.strip() for line in log_text.splitlines() if line.strip())
        if saved_sha not in reachable:
            reasons.append("head_sha_unreachable")

    try:
        updated_at = datetime.datetime.fromisoformat(state.get("updated_at", ""))
        now = datetime.datetime.now().astimezone()
        stale_hours = int(os.environ.get("HELIX_HANDOVER_STALE_HOURS", "72"))
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=now.tzinfo)
        if now - updated_at > datetime.timedelta(hours=stale_hours):
            reasons.append("updated_at_expired")
    except Exception:
        reasons.append("updated_at_expired")

    # 重複除去（順序維持）
    uniq = []
    for reason in reasons:
        if reason not in uniq:
            uniq.append(reason)
    return len(uniq) > 0, uniq


def build_dump_state(args):
    validate_phase(args.phase)
    if args.scope not in ALLOWED_SCOPE:
        raise HandoverError("scope は backend のみ対応です", EXIT_INPUT_ERROR)

    sprint = args.sprint or args.phase_sprint
    if not sprint:
        raise HandoverError("phase.yaml の sprint.current_step が null のため --sprint が必須です", EXIT_INPUT_ERROR)
    validate_sprint(sprint)

    if not args.task_id or not args.task_title:
        raise HandoverError("dump には --task-id と --task-title が必要です", EXIT_INPUT_ERROR)

    branch = run_git(args.project_root, ["rev-parse", "--abbrev-ref", "HEAD"], strict=True)
    head_sha = run_git(args.project_root, ["rev-parse", "HEAD"], strict=True)
    if not SHA40_RE.fullmatch(head_sha):
        raise HandoverError("git rev-parse HEAD が 40 桁 SHA を返しませんでした", EXIT_PREREQ_ERROR)

    dirty_text = run_git(args.project_root, ["status", "--porcelain"], strict=True)
    dirty = bool(dirty_text.strip())

    target_files = normalize_list_value(args.files)
    pending_files = normalize_list_value(args.pending) if args.pending else list(target_files)

    contracts = {
        "d_api": args.contracts_api,
        "d_db": args.contracts_db,
        "d_contract": args.contracts_contract,
    }

    state = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "updated_at": now_iso(),
        "revision": 1,
        "owner": "opus",
        "scope": args.scope,
        "git": {
            "branch": branch,
            "head_sha": head_sha,
            "dirty": dirty,
        },
        "phase": args.phase,
        "sprint": sprint,
        "project": args.project,
        "task": {
            "id": args.task_id,
            "title": args.task_title,
            "status": "in_progress",
        },
        "contracts": contracts,
        "files": {
            "target": target_files,
            "completed": [],
            "pending": pending_files,
        },
        "tests": parse_tests(args.tests),
    }
    validate_state(state)
    return render_json_template(state)


def cmd_dump(args):
    paths = current_paths(args.handover_dir)
    ensure_dir(args.handover_dir)
    lock_fh = lock_open(paths["lock"])
    try:
        if paths["json"].exists():
            if not args.force:
                raise HandoverError("CURRENT.json が既に存在します。--force で archive 後に再生成してください", EXIT_CHECK_FAILED)
            archive_current(paths)

        state = build_dump_state(args)
        dump_json(paths["json"], state)

        next_action = args.next.strip() if args.next else default_next_action(state)
        dump_note = args.note.strip() if args.note else "初期 dump"
        write_text(paths["md"], render_md_template(state, next_action, dump_note))
    finally:
        lock_close(lock_fh)

    print("handover dump completed")


def build_status_payload(state, args, stale, stale_reasons):
    files = state.get("files", {})
    return {
        "exists": True,
        "schema_version": state.get("schema_version"),
        "path": ".helix/handover/CURRENT.json",
        "updated_at": state.get("updated_at"),
        "revision": state.get("revision"),
        "owner": state.get("owner"),
        "scope": state.get("scope"),
        "task": state.get("task"),
        "phase": state.get("phase"),
        "sprint": state.get("sprint"),
        "git": state.get("git"),
        "stale": stale,
        "stale_reasons": stale_reasons,
        "files": {
            "completed_count": len(files.get("completed", [])),
            "pending_count": len(files.get("pending", [])),
            "completed": files.get("completed", []),
            "pending": files.get("pending", []),
        },
    }


def cmd_status(args):
    paths = current_paths(args.handover_dir)
    if not paths["json"].exists():
        if args.json:
            print(json.dumps({"exists": False}, ensure_ascii=False))
        else:
            print("{\"exists\": false}")
        return

    state = load_json(paths["json"])
    validate_state(state)

    stale, reasons = stale_check(state, args.project_root, args.check_stale)
    payload = build_status_payload(state, args, stale, reasons)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    print(f"exists: {payload['exists']}")
    print(f"task: {state['task']['id']} {state['task']['title']}")
    print(f"status: {state['task']['status']}")
    print(f"phase/sprint: {state['phase']} {state['sprint']}")
    print(f"owner: {state['owner']}")
    print(f"revision: {state['revision']}")
    print(f"stale: {str(stale).lower()}")
    if reasons:
        print("stale_reasons: " + ",".join(reasons))
    if args.full:
        print("\n--- CURRENT.json ---")
        print(read_text(paths["json"]).rstrip())
        if paths["md"].exists():
            print("\n--- CURRENT.md ---")
            print(read_text(paths["md"]).rstrip())


def cmd_update(args):
    if args.status == "escalated":
        raise HandoverError("update --status escalated は禁止です。helix handover escalate を使用してください", EXIT_INPUT_ERROR)

    if args.blocker and args.unblock:
        raise HandoverError("--blocker と --unblock は同時指定できません", EXIT_INPUT_ERROR)
    if args.status and (args.blocker or args.unblock):
        raise HandoverError("--status と --blocker/--unblock の同時指定はできません", EXIT_INPUT_ERROR)

    paths = current_paths(args.handover_dir)
    lock_fh = lock_open(paths["lock"])
    try:
        if not paths["json"].exists():
            raise HandoverError("CURRENT.json が存在しません", EXIT_PREREQ_ERROR)

        state = load_json(paths["json"])
        validate_state(state)
        expected_revision = state["revision"]
        updated = json.loads(json.dumps(state, ensure_ascii=False))

        changed = False
        events = []
        ready_for_review_transition = False

        # status 更新
        current_status = updated["task"]["status"]
        if args.status:
            transition_status(current_status, args.status)
            updated["task"]["status"] = args.status
            events.append(("status_change", f"{current_status} -> {args.status}", None))
            changed = True
            current_status = args.status
            if args.status == "ready_for_review":
                ready_for_review_transition = True

        # blocker / unblock
        if args.blocker:
            if current_status != "in_progress":
                raise HandoverError("--blocker は in_progress 状態でのみ実行できます", EXIT_CHECK_FAILED)
            updated["task"]["status"] = "blocked"
            current_status = "blocked"
            events.append(("blocker", args.blocker, "blocked"))
            changed = True

        if args.unblock:
            if current_status != "blocked":
                raise HandoverError("--unblock は blocked 状態でのみ実行できます", EXIT_CHECK_FAILED)
            updated["task"]["status"] = "in_progress"
            current_status = "in_progress"
            events.append(("unblock", args.unblock, "in_progress"))
            changed = True

        # sprint 更新
        if args.sprint:
            validate_sprint(args.sprint)
            if updated.get("sprint") != args.sprint:
                updated["sprint"] = args.sprint
                changed = True

        # owner 更新
        if args.owner:
            if args.owner not in ALLOWED_OWNER:
                raise HandoverError("owner は opus/codex のみ", EXIT_INPUT_ERROR)
            if updated.get("owner") != args.owner:
                before = updated.get("owner")
                updated["owner"] = args.owner
                events.append(("owner_change", f"{before} -> {args.owner}", None))
                changed = True

        # files.complete
        if args.complete:
            pending = list(updated["files"].get("pending", []))
            completed = list(updated["files"].get("completed", []))
            completed_paths = {entry.get("path") for entry in completed if isinstance(entry, dict)}

            for raw in args.complete:
                path = raw.strip()
                if not path:
                    continue
                pending = [p for p in pending if p != path]
                if path not in completed_paths:
                    completed.append({"path": path, "note": args.complete_note})
                    completed_paths.add(path)
                    note = f"{path}" if not args.complete_note else f"{path} ({args.complete_note})"
                    events.append(("complete", note, None))
                    changed = True

            updated["files"]["pending"] = pending
            updated["files"]["completed"] = completed

        # pending 追加
        if args.pending_add:
            pending = list(updated["files"].get("pending", []))
            for raw in args.pending_add:
                path = raw.strip()
                if path and path not in pending:
                    pending.append(path)
                    changed = True
            updated["files"]["pending"] = pending

        # note
        if args.note:
            events.append(("note", args.note, None))
            changed = True

        # Next Action 更新（ヘッダ置換可）
        md_text = read_text(paths["md"]) if paths["md"].exists() else None
        if args.update_next_action:
            if md_text is None:
                md_text = render_md_template(updated, default_next_action(updated), "初期 dump")
            old_next = read_next_action(md_text)
            md_text = replace_next_action(md_text, args.update_next_action)
            events.append(("note", f"Next Action updated\n(before)\n{old_next}", None))
            changed = True

        if not changed:
            raise HandoverError("update する内容が指定されていません", EXIT_INPUT_ERROR)

        updated["updated_at"] = now_iso()
        updated["revision"] = expected_revision + 1
        validate_state(updated)

        atomic_write_json_with_revision(paths["json"], updated, expected_revision)

        ensure_md_exists(paths["md"], updated)
        if md_text is not None:
            write_text(paths["md"], md_text)

        for event_type, body, event_status in events:
            append_event(paths["md"], event_type, updated["owner"], body, status=event_status)

        if ready_for_review_transition:
            changed_files = _collect_changed_files(args.project_root)
            _run_drift_check(args.project_root, changed_files)

            fe_drift = detect_fe_drift(args.project_root, changed_files=changed_files)
            if fe_drift and updated.get("scope") == "backend":
                print("[handover] 警告: scope=backend だが FE ファイル変更を検知しました", file=sys.stderr)
                for path in fe_drift[:5]:
                    print(f"  - {path}", file=sys.stderr)
                print("[handover] ESCALATION.md を自動更新しました", file=sys.stderr)

                _write_auto_escalation(paths["escalation"], updated, fe_drift)
                append_event(
                    paths["md"],
                    "fe_drift",
                    updated["owner"],
                    "\n".join(fe_drift),
                    status="ready_for_review",
                )
    finally:
        lock_close(lock_fh)

    print("handover update completed")


def cmd_clear(args):
    paths = current_paths(args.handover_dir)
    lock_fh = lock_open(paths["lock"])
    try:
        if not paths["json"].exists():
            raise HandoverError("CURRENT.json が存在しません", EXIT_PREREQ_ERROR)

        state = load_json(paths["json"])
        validate_state(state)
        status = state["task"]["status"]

        if args.reason == "completed" and status != "ready_for_review":
            raise HandoverError("clear --reason completed は status=ready_for_review のみ許可", EXIT_CHECK_FAILED)
        if args.reason == "escalated" and status != "escalated":
            raise HandoverError("clear --reason escalated は status=escalated のみ許可", EXIT_CHECK_FAILED)
        if args.reason == "abandoned" and not args.force:
            raise HandoverError("clear --reason abandoned には --force が必要です", EXIT_INPUT_ERROR)

        archived = archive_current(paths)
    finally:
        lock_close(lock_fh)

    print(f"handover cleared: {archived}")


def cmd_escalate(args):
    paths = current_paths(args.handover_dir)
    lock_fh = lock_open(paths["lock"])
    try:
        if not paths["json"].exists():
            raise HandoverError("CURRENT.json が存在しません", EXIT_PREREQ_ERROR)

        state = load_json(paths["json"])
        validate_state(state)
        if state["task"]["status"] == "escalated":
            raise HandoverError("既に escalated 状態です", EXIT_CHECK_FAILED)

        expected_revision = state["revision"]
        updated = json.loads(json.dumps(state, ensure_ascii=False))
        before_owner = updated["owner"]
        updated["owner"] = "codex"
        updated["task"]["status"] = "escalated"
        updated["updated_at"] = now_iso()
        updated["revision"] = expected_revision + 1
        validate_state(updated)

        atomic_write_json_with_revision(paths["json"], updated, expected_revision)

        ensure_md_exists(paths["md"], updated)
        if before_owner != "codex":
            append_event(paths["md"], "owner_change", "codex", f"{before_owner} -> codex")
        append_event(
            paths["md"],
            "escalate",
            "codex",
            f"reason: {args.reason}\n\ncontext:\n{args.context}",
            status="escalated",
        )

        escalation = (
            "# HELIX Escalation\n\n"
            f"Timestamp: {updated['updated_at']}\n"
            "From: codex\n"
            f"Task: {updated['task']['id']} {updated['task']['title']} ({updated['phase']} Sprint {updated['sprint']})\n\n"
            "## Reason\n"
            f"{args.reason}\n\n"
            "## Context\n"
            f"{args.context}\n\n"
            "## CURRENT snapshot\n"
            "```json\n"
            f"{json.dumps(updated, ensure_ascii=False, indent=2)}\n"
            "```\n"
        )
        write_text(paths["escalation"], escalation)
    finally:
        lock_close(lock_fh)

    print("handover escalated")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="HELIX handover core")
    parser.add_argument("--handover-dir", default=".helix/handover")
    parser.add_argument("--project-root", default=".")

    sub = parser.add_subparsers(dest="subcommand", required=True)

    dump_p = sub.add_parser("dump", help="CURRENT を生成")
    dump_p.add_argument("--task-id", required=True)
    dump_p.add_argument("--task-title", required=True)
    dump_p.add_argument("--files", default="")
    dump_p.add_argument("--pending", default="")
    dump_p.add_argument("--tests", action="append", default=[])
    dump_p.add_argument("--next", default="")
    dump_p.add_argument("--note", default="")
    dump_p.add_argument("--contracts-api", default=None)
    dump_p.add_argument("--contracts-db", default=None)
    dump_p.add_argument("--contracts-contract", default=None)
    dump_p.add_argument("--sprint", default=None)
    dump_p.add_argument("--phase-sprint", default=None)
    dump_p.add_argument("--phase", required=True)
    dump_p.add_argument("--project", required=True)
    dump_p.add_argument("--scope", default="backend")
    dump_p.add_argument("--force", action="store_true")

    status_p = sub.add_parser("status", help="状態表示")
    status_p.add_argument("--json", action="store_true")
    status_p.add_argument("--full", action="store_true")
    stale_group = status_p.add_mutually_exclusive_group()
    stale_group.add_argument("--check-stale", dest="check_stale", action="store_true")
    stale_group.add_argument("--no-check-stale", dest="check_stale", action="store_false")
    status_p.set_defaults(check_stale=True)

    update_p = sub.add_parser("update", help="状態更新")
    update_p.add_argument("--status", choices=sorted(ALLOWED_STATUS_UPDATE))
    update_p.add_argument("--sprint", default=None)
    update_p.add_argument("--note", default=None)
    update_p.add_argument("--complete", action="append", default=[])
    update_p.add_argument("--complete-note", default=None)
    update_p.add_argument("--pending-add", action="append", default=[])
    update_p.add_argument("--blocker", default=None)
    update_p.add_argument("--unblock", default=None)
    update_p.add_argument("--owner", choices=sorted(ALLOWED_OWNER), default=None)
    update_p.add_argument("--update-next-action", default=None)

    clear_p = sub.add_parser("clear", help="archive 移動")
    clear_p.add_argument("--reason", required=True, choices=["completed", "abandoned", "escalated"])
    clear_p.add_argument("--force", action="store_true")

    escalate_p = sub.add_parser("escalate", help="escalation 作成")
    escalate_p.add_argument("--reason", required=True)
    escalate_p.add_argument("--context", required=True)

    args = parser.parse_args(argv)
    args.handover_dir = Path(args.handover_dir).resolve()
    args.project_root = Path(args.project_root).resolve()
    return args


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.subcommand == "dump":
        cmd_dump(args)
    elif args.subcommand == "status":
        cmd_status(args)
    elif args.subcommand == "update":
        cmd_update(args)
    elif args.subcommand == "clear":
        cmd_clear(args)
    elif args.subcommand == "escalate":
        cmd_escalate(args)
    else:
        raise HandoverError(f"unknown subcommand: {args.subcommand}", EXIT_INPUT_ERROR)


if __name__ == "__main__":
    try:
        main()
    except HandoverError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        sys.exit(exc.exit_code)
    except KeyboardInterrupt:
        print("エラー: interrupted", file=sys.stderr)
        sys.exit(EXIT_INTERNAL_ERROR)
    except Exception as exc:
        print(f"エラー: internal error: {exc}", file=sys.stderr)
        sys.exit(EXIT_INTERNAL_ERROR)
