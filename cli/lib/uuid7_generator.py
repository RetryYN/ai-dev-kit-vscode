"""UUID v7 generator for event_id issuance.

Design reference:
- D-CONTRACT-EVENT-draft §3
"""

import os
import sys
import threading
import time
import uuid

_HAS_STDLIB_UUID7 = sys.version_info >= (3, 14) and hasattr(uuid, "uuid7")
_LAST_TIMESTAMP_MS: int = 0
_COUNTER: int = 0
_LOCK = threading.Lock()


def _timestamp_ms() -> int:
    return time.time_ns() // 1_000_000


def _random_bits(bit_count: int) -> int:
    byte_count = (bit_count + 7) // 8
    random_bytes = os.urandom(byte_count)
    return int.from_bytes(random_bytes, "big") & ((1 << bit_count) - 1)


def _split_rand_b(rand_b: int) -> tuple[int, int]:
    return (rand_b >> 48) & 0x3FFF, rand_b & 0xFFFFFFFFFFFF


# @helix:index id=uuid7-generator.next-monotonic-timestamp domain=cli/lib summary=同一ms内でも UUID v7 timestamp を strict monotonic に進める helper
def _next_monotonic_timestamp() -> int:
    """同 ms 内多発時に counter を加算して strict monotonic を保つ"""
    global _LAST_TIMESTAMP_MS, _COUNTER

    current_timestamp_ms = _timestamp_ms()
    with _LOCK:
        if current_timestamp_ms > _LAST_TIMESTAMP_MS:
            _LAST_TIMESTAMP_MS = current_timestamp_ms
            _COUNTER = 0
            return _LAST_TIMESTAMP_MS

        _COUNTER += 1
        _LAST_TIMESTAMP_MS += 1
        return _LAST_TIMESTAMP_MS


def _validate_uuid7(value: str) -> str:
    parts = value.split("-")
    if len(parts) != 5:
        raise RuntimeError("UUID v7 generation failed: invalid group count")
    if any(not part for part in parts):
        raise RuntimeError("UUID v7 generation failed: empty group")
    if len(value) != 36:
        raise RuntimeError("UUID v7 generation failed: invalid length")
    if parts[2][0] != "7":
        raise RuntimeError("UUID v7 generation failed: invalid version nibble")
    if parts[3][0] not in {"8", "9", "a", "b"}:
        raise RuntimeError("UUID v7 generation failed: invalid variant nibble")
    return value


def _format_uuid7(timestamp_ms: int, rand_a: int, rand_b: int) -> str:
    timestamp_hex = format(timestamp_ms & 0xFFFFFFFFFFFF, "012x")
    rand_b_high, rand_b_low = _split_rand_b(rand_b)
    return (
        f"{timestamp_hex[:8]}-{timestamp_hex[8:12]}-7{rand_a:03x}-"
        f"{0x8000 | rand_b_high:04x}-{rand_b_low:012x}"
    )


def _uuid7_fallback() -> str:
    try:
        timestamp_ms = _next_monotonic_timestamp()
        rand_a = _random_bits(12)
        rand_b = _random_bits(62)
    except OSError as exc:
        raise RuntimeError("UUID v7 generation failed") from exc

    return _format_uuid7(timestamp_ms, rand_a, rand_b)


# @helix:index id=uuid7-generator.generate-event-id domain=cli/lib summary=UUID v7 (RFC 9562) 形式の event_id 生成、Python 3.12 fallback
def generate_event_id() -> str:
    """Generate an RFC 9562 UUID v7 string.

    Python 3.12 does not provide ``uuid.uuid7()``, so HELIX uses a small local
    formatter based on a 48-bit millisecond timestamp and 74 bits of randomness
    split across the version and variant fields.
    """
    if _HAS_STDLIB_UUID7:
        return _validate_uuid7(str(uuid.uuid7()))

    return _validate_uuid7(_uuid7_fallback())
