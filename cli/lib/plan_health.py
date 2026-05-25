from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import plan_lint


STATUS_KEYS = ("draft", "in_progress", "completed", "finalized", "other")
KNOWN_STATUSES = set(plan_lint.STATUS_VALUES)


def _empty_result() -> dict[str, object]:
    return {
        "total": 0,
        "valid_frontmatter": 0,
        "invalid_frontmatter": 0,
        "status_distribution": {key: 0 for key in STATUS_KEYS},
        "kind_distribution": {},
        "invalid_examples": [],
    }


def _iter_plan_files(plans_root: Path) -> list[Path]:
    if not plans_root.exists():
        return []
    return sorted(path for path in plans_root.rglob("*plan.md") if path.is_file())


def _parse_plan_frontmatter(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    frontmatter_lines, _ = plan_lint._extract_frontmatter(lines)
    return plan_lint._parse_frontmatter_mapping(frontmatter_lines)


def _normalize_status(status: object) -> str | None:
    if not isinstance(status, str):
        return None
    normalized = status.strip()
    if not normalized:
        return None
    if normalized in KNOWN_STATUSES:
        return normalized
    return "other"


def _relative_file(path: Path, plans_root: Path) -> str:
    try:
        return str(path.relative_to(plans_root))
    except ValueError:
        return str(path)


def scan_all_plans(plans_root: Path) -> dict[str, object]:
    result = _empty_result()
    kind_counter: Counter[str] = Counter()

    for path in _iter_plan_files(plans_root):
        result["total"] += 1
        errors: list[str] = []
        frontmatter: dict[str, object] | None = None

        try:
            frontmatter = _parse_plan_frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))

        if frontmatter is not None:
            normalized_status = _normalize_status(frontmatter.get("status"))
            if normalized_status is not None:
                result["status_distribution"][normalized_status] += 1

            kind = frontmatter.get("kind")
            if isinstance(kind, str) and kind.strip():
                kind_counter[kind] += 1

            errors.extend(
                f"{finding['field']}: {finding['message']}"
                for finding in plan_lint.validate_plan_frontmatter(frontmatter)
                if finding["level"] == "error"
            )

        if errors:
            result["invalid_frontmatter"] += 1
            result["invalid_examples"].append(
                {
                    "file": _relative_file(path, plans_root),
                    "errors": errors,
                }
            )
        else:
            result["valid_frontmatter"] += 1

    result["kind_distribution"] = dict(sorted(kind_counter.items()))
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="helix plan health",
        description="Scan PLAN frontmatter health across docs/plans",
    )
    parser.add_argument("--json", action="store_true", help="結果を JSON で出力する")
    parser.add_argument(
        "--plans-root",
        type=Path,
        default=Path("docs/plans"),
        help="scan 対象の plans root (default: docs/plans)",
    )
    return parser.parse_args()


def _print_human(result: dict[str, object], plans_root: Path) -> None:
    status_distribution = result["status_distribution"]
    kind_distribution = result["kind_distribution"]
    invalid_examples = result["invalid_examples"]

    print(f"Plans Root: {plans_root}")
    print(f"Total Plans: {result['total']}")
    print(f"Valid Frontmatter: {result['valid_frontmatter']}")
    print(f"Invalid Frontmatter: {result['invalid_frontmatter']}")
    print(
        "Status Distribution: "
        + ", ".join(f"{key}={status_distribution[key]}" for key in STATUS_KEYS)
    )
    if kind_distribution:
        print(
            "Kind Distribution: "
            + ", ".join(f"{key}={value}" for key, value in kind_distribution.items())
        )
    else:
        print("Kind Distribution: (none)")
    if invalid_examples:
        print("Invalid Examples:")
        for example in invalid_examples:
            print(f"- {example['file']}: {'; '.join(example['errors'])}")


def main() -> int:
    args = _parse_args()
    result = scan_all_plans(args.plans_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_human(result, args.plans_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
