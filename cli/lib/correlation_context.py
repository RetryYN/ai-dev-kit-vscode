"""Correlation context helpers for cross-db trace propagation.

Design reference:
- docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-EVENT-draft.md §4
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Iterator

from . import uuid7_generator

_CORRELATION_CONTEXT: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "helix_correlation_id",
    default=None,
)


# @helix:index id=correlation-context.current domain=cli/lib summary=現在 thread の correlation_id を取得
def current_correlation_id() -> str | None:
    """Return the active correlation_id for the current context, if any."""
    return _CORRELATION_CONTEXT.get()


# @helix:index id=correlation-context.current-legacy domain=cli/lib summary=L3 draft 名 get_current_correlation_id の互換 alias
def get_current_correlation_id() -> str | None:
    """Backward-compatible alias for the L3 draft naming."""
    return current_correlation_id()


# @helix:index id=correlation-context.scope domain=cli/lib summary=correlation_id を context-local に発行/継承
@contextmanager
def correlation_context(parent: str | None = None) -> Iterator[str]:
    """Issue or inherit a context-local correlation_id.

    - ``parent is None``: issue a new UUID v7 correlation_id
    - ``parent`` is provided: inherit that correlation_id

    ``contextvars`` keeps nested contexts isolated and restores the prior value
    on exit. Other threads do not observe the current correlation_id unless
    they explicitly propagate context.
    """
    correlation_id = parent if parent is not None else uuid7_generator.generate_event_id()
    token = _CORRELATION_CONTEXT.set(correlation_id)
    try:
        yield correlation_id
    finally:
        _CORRELATION_CONTEXT.reset(token)
