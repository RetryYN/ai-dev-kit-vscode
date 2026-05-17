"""Projector lag helper."""

from __future__ import annotations

import logging
from sqlite3 import Connection

LAG_WARN_THRESHOLD = 100
LAG_CRITICAL_THRESHOLD = 1000

logger = logging.getLogger(__name__)


# @helix:index id=projector-lag.check-projector-lag domain=cli/lib summary=projection_state と event_envelope から projector lag を計測する
def _check_projector_lag(conn: Connection, projector_id: str, db_name: str) -> int:
    """Return the backlog count between the last processed event and latest event."""
    row = conn.execute(
        """
        SELECT last_processed_event_id
        FROM projection_state
        WHERE projector_id = ? AND db_name = ?
        """,
        (projector_id, db_name),
    ).fetchone()
    last_processed_event_id = row[0] if row is not None else None

    if last_processed_event_id:
        lag = int(
            conn.execute(
                """
                SELECT COUNT(*)
                FROM event_envelope
                WHERE db_name = ? AND event_id > ?
                """,
                (db_name, last_processed_event_id),
            ).fetchone()[0]
        )
    else:
        lag = int(
            conn.execute(
                "SELECT COUNT(*) FROM event_envelope WHERE db_name = ?",
                (db_name,),
            ).fetchone()[0]
        )

    if lag > LAG_CRITICAL_THRESHOLD:
        logger.critical(
            "projector lag critical: projector_id=%s db_name=%s lag=%d threshold=%d",
            projector_id,
            db_name,
            lag,
            LAG_CRITICAL_THRESHOLD,
        )
    elif lag > LAG_WARN_THRESHOLD:
        logger.warning(
            "projector lag warning: projector_id=%s db_name=%s lag=%d threshold=%d",
            projector_id,
            db_name,
            lag,
            LAG_WARN_THRESHOLD,
        )

    return lag
