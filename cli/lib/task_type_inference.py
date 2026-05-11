from __future__ import annotations

import argparse
import re


_EXPLICIT_MARKER_RE = re.compile(r"^\s*\[タスク種別\]", re.MULTILINE)
_EXPLICIT_KNOWN_RE = re.compile(
    r"^\s*\[タスク種別\]\s*:?\s*(?:\*\*|__|`)?\s*(実装|レビュー|設計|調査|不明)\b",
    re.MULTILINE,
)
_INFERENCE_PATTERNS = {
    "実装": re.compile(
        r"作成|書き出し|起票|実装|追加|修正|書く|作る|"
        r"\bcreate\b|\bwrite\b|\bimplement\b|\badd\b|\bedit\b|\bfix\b",
        re.IGNORECASE,
    ),
    "レビュー": re.compile(
        r"レビュー|評価|検証|監査|チェック|確認|"
        r"\breview\b|\baudit\b|\bcheck\b|\bverify\b|\bevaluate\b",
        re.IGNORECASE,
    ),
    "設計": re.compile(
        r"設計検討|設計|"
        r"\bdesign\b|\bspec\b|\bplan\b(?!-\d)",
        re.IGNORECASE,
    ),
    "調査": re.compile(
        r"調査|分析|探索|grep|"
        r"\binvestigate\b|\banalyze\b|\bresearch\b|\bexplore\b",
        re.IGNORECASE,
    ),
}


def has_explicit_task_type(task: str) -> bool:
    return bool(_EXPLICIT_MARKER_RE.search(task))


def parse_explicit_task_type(task: str) -> str | None:
    match = _EXPLICIT_KNOWN_RE.search(task)
    if not match:
        return None
    return match.group(1)


def infer_task_type(task: str) -> str:
    matches: list[tuple[int, int, str]] = []
    for priority, task_type in enumerate(("実装", "レビュー", "設計", "調査")):
        match = _INFERENCE_PATTERNS[task_type].search(task)
        if match:
            matches.append((match.start(), priority, task_type))
    if not matches:
        return "不明"
    matches.sort()
    return matches[0][2]


def detect_task_type(task: str) -> str:
    explicit = parse_explicit_task_type(task)
    if explicit:
        return explicit
    if has_explicit_task_type(task):
        return "不明"
    return infer_task_type(task)


def ensure_task_type_prefix(task: str) -> str:
    if has_explicit_task_type(task):
        return task
    return f"[タスク種別] {detect_task_type(task)}\n{task}"


def should_include_review_template(task_type: str) -> bool:
    return task_type == "レビュー"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Infer HELIX task type from task text.")
    parser.add_argument("--mode", choices=("detect", "prefix", "review-template"), required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--task-type", default="")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.mode == "detect":
        print(detect_task_type(args.task))
        return 0
    if args.mode == "prefix":
        print(ensure_task_type_prefix(args.task), end="")
        return 0

    task_type = args.task_type or detect_task_type(args.task)
    print("true" if should_include_review_template(task_type) else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
