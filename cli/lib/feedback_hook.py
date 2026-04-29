"""Gate feedback hook for PLAN-004.

Runs after a HELIX gate passes, asks Codex TL for 5-axis Lv1-5 feedback,
prints the user-facing message, and stores each score in accuracy_score.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

import helix_db
import yaml_parser


DIMENSIONS = ("density", "depth", "breadth", "accuracy", "maintainability")
HOOK_GATES = ("G2", "G3", "G4", "G5", "G6", "G7", "L8")
DEFAULT_CODEX_TIMEOUT_SEC = 300


class FeedbackHookError(RuntimeError):
    """Recoverable hook error. Gate pass must remain fail-open."""


@dataclass(frozen=True)
class FeedbackScore:
    dimension: str
    level: int
    comment: str


@dataclass(frozen=True)
class FeedbackResult:
    feedback_message: str
    scores: tuple[FeedbackScore, ...]


def resolve_plan_id(phase_file: Path, env: dict[str, str] | None = None) -> str | None:
    env_map = env if env is not None else os.environ
    env_plan_id = env_map.get("HELIX_PLAN_ID", "").strip()
    if env_plan_id:
        return env_plan_id

    if not phase_file.exists():
        return None

    data = yaml_parser.parse_yaml(phase_file.read_text(encoding="utf-8"))
    plan_id = data.get("plan_id")
    if isinstance(plan_id, str) and plan_id.strip():
        return plan_id.strip()
    return None


def recent_work_summary(project_root: Path) -> str:
    branch = _run_git(project_root, ["branch", "--show-current"]) or _run_git(
        project_root, ["rev-parse", "--abbrev-ref", "HEAD"]
    )
    commits = _run_git(project_root, ["log", "-3", "--oneline"])
    parts = []
    if branch:
        parts.append(f"branch: {branch}")
    if commits:
        parts.append("recent commits:\n" + commits)
    return "\n".join(parts) if parts else "git context unavailable"


def _run_git(project_root: Path, args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(project_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def render_prompt(
    template_path: Path,
    *,
    plan_id: str,
    gate_name: str,
    recent_summary: str,
    findings_summary: str,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    replacements = {
        "{plan_id}": plan_id,
        "{gate_name}": gate_name,
        "{recent_work_summary}": recent_summary,
        "{findings_summary}": findings_summary,
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def call_codex_tl(
    prompt: str,
    *,
    codex_cmd: list[str],
    project_root: Path,
    timeout_sec: int = DEFAULT_CODEX_TIMEOUT_SEC,
) -> str:
    try:
        proc = subprocess.run(
            [*codex_cmd, "--role", "tl", "--thinking", "medium", "--task", prompt],
            cwd=str(project_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout_sec,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FeedbackHookError(f"Codex TL 呼び出しに失敗しました: {exc}") from exc

    output = "\n".join(proc.stdout.splitlines()[-200:])
    if proc.returncode != 0:
        raise FeedbackHookError(f"Codex TL が失敗しました (exit={proc.returncode})\n{output}")
    return output


def parse_feedback_json(output: str) -> FeedbackResult:
    payload = _load_json_object(output)
    message = payload.get("feedback_message")
    raw_scores = payload.get("scores")
    if not isinstance(message, str) or not message.strip():
        raise FeedbackHookError("feedback_message が空です")
    if not isinstance(raw_scores, list):
        raise FeedbackHookError("scores が配列ではありません")

    scores_by_dimension: dict[str, FeedbackScore] = {}
    for raw_score in raw_scores:
        if not isinstance(raw_score, dict):
            raise FeedbackHookError("scores の要素が object ではありません")
        dimension = raw_score.get("dimension")
        level = raw_score.get("level")
        comment = raw_score.get("comment", "")
        if dimension not in DIMENSIONS:
            raise FeedbackHookError(f"不正な dimension: {dimension}")
        if type(level) is not int or not 1 <= level <= 5:
            raise FeedbackHookError(f"不正な level: {level}")
        if not isinstance(comment, str):
            raise FeedbackHookError(f"不正な comment: {dimension}")
        scores_by_dimension[str(dimension)] = FeedbackScore(str(dimension), level, comment)

    missing = [dimension for dimension in DIMENSIONS if dimension not in scores_by_dimension]
    if missing:
        raise FeedbackHookError(f"不足 dimension: {', '.join(missing)}")

    return FeedbackResult(
        feedback_message=message.strip(),
        scores=tuple(scores_by_dimension[dimension] for dimension in DIMENSIONS),
    )


def _load_json_object(output: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        payload = _extract_json_object(output)
    if not isinstance(payload, dict):
        raise FeedbackHookError("Codex TL 出力が JSON object ではありません")
    return payload


def _extract_json_object(output: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    start = output.find("{")
    while start != -1:
        try:
            payload, _ = decoder.raw_decode(output[start:])
        except json.JSONDecodeError:
            start = output.find("{", start + 1)
            continue
        if isinstance(payload, dict):
            return payload
        start = output.find("{", start + 1)
    raise FeedbackHookError("Codex TL 出力から JSON を抽出できません")


def record_scores(
    db_path: Path,
    *,
    plan_id: str,
    gate: str,
    result: FeedbackResult,
    evidence: str,
    sprint: str | None = None,
) -> None:
    for score in result.scores:
        helix_db.record_accuracy_score(
            str(db_path),
            plan_id=plan_id,
            gate=gate,
            dimension=score.dimension,
            level=score.level,
            comment=score.comment,
            evidence=evidence,
            sprint=sprint,
            reviewer="codex-feedback-hook",
        )


def display_feedback(result: FeedbackResult, stdout: TextIO) -> None:
    print("", file=stdout)
    print(_color("[helix-gate] 5軸 Lv1-5 feedback", "36"), file=stdout)
    print(result.feedback_message, file=stdout)
    for score in result.scores:
        print(
            f"  - {score.dimension}: Lv{score.level} {score.comment}",
            file=stdout,
        )


def _color(text: str, code: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def emit_feedback(
    *,
    project_root: Path,
    helix_dir: Path,
    gate: str,
    gate_name: str,
    findings_summary: str,
    db_path: Path | None = None,
    template_path: Path | None = None,
    codex_cmd: list[str] | None = None,
    env: dict[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> bool:
    stdout = stdout if stdout is not None else sys.stdout
    stderr = stderr if stderr is not None else sys.stderr
    env_map = env if env is not None else os.environ

    if env_map.get("HELIX_DISABLE_FEEDBACK") == "1":
        return False
    if gate not in HOOK_GATES:
        return False

    phase_file = helix_dir / "phase.yaml"
    plan_id = resolve_plan_id(phase_file, env_map)
    if plan_id is None:
        print("[helix-gate] feedback hook skip: plan_id が不明です", file=stderr)
        return False

    template = template_path or (Path(__file__).resolve().parents[1] / "templates" / "feedback-prompt.md")
    db = db_path or (helix_dir / "helix.db")
    codex = codex_cmd or [str(Path(__file__).resolve().parents[1] / "helix-codex")]

    try:
        recent_summary = recent_work_summary(project_root)
        prompt = render_prompt(
            template,
            plan_id=plan_id,
            gate_name=gate,
            recent_summary=recent_summary,
            findings_summary=findings_summary,
        )
        output = call_codex_tl(prompt, codex_cmd=codex, project_root=project_root)
        result = parse_feedback_json(output)
        evidence = (
            f"gate_name: {gate_name or gate}\n"
            f"recent_work_summary:\n{recent_summary}\n"
            f"findings_summary:\n{findings_summary}"
        )
        record_scores(db, plan_id=plan_id, gate=gate, result=result, evidence=evidence)
        display_feedback(result, stdout)
        return True
    except Exception as exc:
        print(f"[helix-gate] WARN: feedback hook skipped: {exc}", file=stderr)
        return False


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit HELIX gate feedback hook")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--helix-dir", required=True)
    parser.add_argument("--gate", required=True, choices=HOOK_GATES)
    parser.add_argument("--gate-name", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--db-path")
    parser.add_argument("--template")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    emit_feedback(
        project_root=Path(args.project_root),
        helix_dir=Path(args.helix_dir),
        gate=args.gate,
        gate_name=args.gate_name,
        findings_summary=args.summary,
        db_path=Path(args.db_path) if args.db_path else None,
        template_path=Path(args.template) if args.template else None,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    raise SystemExit(main())
