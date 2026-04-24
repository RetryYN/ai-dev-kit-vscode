from __future__ import annotations

import argparse
import re
import sys
from typing import Any, Iterable, Pattern

REDACTED = "[REDACTED]"

COMMON_REDACTION_TOKENS = (
    "/home",
    "password",
    "passwd",
    "token",
    "secret",
    "apikey",
    "api_key",
    "api-key",
    "access_token",
    "refresh_token",
    "private_key",
    "credential",
    "authorization",
    "bearer",
    "ssh-rsa",
    "-----begin",
)

COMMON_REDACTION_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+\b", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9._-]+\b"),
    re.compile(r"\bghp_[A-Za-z0-9]+\b"),
    re.compile(r"\bxox[bap]-[A-Za-z0-9-]+\b", re.IGNORECASE),
)


def _bump(stats: dict[str, int] | None) -> None:
    if stats is not None:
        stats["count"] = stats.get("count", 0) + 1


def should_redact_text(
    text: str,
    *,
    extra_tokens: Iterable[str] | None = None,
    extra_patterns: Iterable[Pattern[str]] | None = None,
) -> bool:
    lowered = text.lower()
    tokens = COMMON_REDACTION_TOKENS + tuple(extra_tokens or ())
    if any(token in lowered for token in tokens):
        return True

    patterns = COMMON_REDACTION_PATTERNS + tuple(extra_patterns or ())
    return any(pattern.search(text) for pattern in patterns)


def redact_value(
    value: Any,
    *,
    key_hint: str = "",
    stats: dict[str, int] | None = None,
    extra_tokens: Iterable[str] | None = None,
    extra_patterns: Iterable[Pattern[str]] | None = None,
    tuple_as_list: bool = False,
) -> Any:
    if isinstance(key_hint, str) and key_hint:
        if should_redact_text(
            key_hint,
            extra_tokens=extra_tokens,
            extra_patterns=extra_patterns,
        ):
            _bump(stats)
            return REDACTED

    if isinstance(value, dict):
        return {
            str(key): redact_value(
                item,
                key_hint=str(key),
                stats=stats,
                extra_tokens=extra_tokens,
                extra_patterns=extra_patterns,
                tuple_as_list=tuple_as_list,
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            redact_value(
                item,
                key_hint=key_hint,
                stats=stats,
                extra_tokens=extra_tokens,
                extra_patterns=extra_patterns,
                tuple_as_list=tuple_as_list,
            )
            for item in value
        ]

    if isinstance(value, tuple):
        items = [
            redact_value(
                item,
                key_hint=key_hint,
                stats=stats,
                extra_tokens=extra_tokens,
                extra_patterns=extra_patterns,
                tuple_as_list=tuple_as_list,
            )
            for item in value
        ]
        if tuple_as_list:
            return items
        return tuple(items)

    if isinstance(value, str):
        if should_redact_text(
            value,
            extra_tokens=extra_tokens,
            extra_patterns=extra_patterns,
        ):
            _bump(stats)
            return REDACTED
        return value

    return value


def redact_stream(lines: Iterable[str]) -> Iterable[str]:
    for raw_line in lines:
        has_newline = raw_line.endswith("\n")
        line = raw_line[:-1] if has_newline else raw_line
        redacted = redact_value(line)
        yield f"{redacted}\n" if has_newline else str(redacted)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HELIX redaction utilities")
    parser.add_argument("--stream", action="store_true", help="redact stdin line-by-line and write to stdout")
    args = parser.parse_args(argv)

    if not args.stream:
        parser.error("supported mode: --stream")

    for line in redact_stream(sys.stdin):
        sys.stdout.write(line)
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
