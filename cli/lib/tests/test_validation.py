import math
import sqlite3
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import helix_db


def _init_db(tmp_path: Path, name: str) -> Path:
    db_path = tmp_path / name / ".helix" / "helix.db"
    with redirect_stdout(StringIO()):
        helix_db.init_db(str(db_path))
    return db_path


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0.0),
        (1, 1.0),
        (1.25, 1.25),
    ],
)
def test_validate_positive_number_accepts_int_and_float(value: int | float, expected: float) -> None:
    assert helix_db._validate_positive_number(value, "cost_usd") == pytest.approx(expected)


@pytest.mark.parametrize("value", [-1, -0.01])
def test_validate_positive_number_rejects_negative_values(value: int | float) -> None:
    with pytest.raises(ValueError, match="cost_usd must be >= 0"):
        helix_db._validate_positive_number(value, "cost_usd")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_validate_positive_number_rejects_nan_and_inf(value: float) -> None:
    with pytest.raises(ValueError, match="cost_usd must be finite"):
        helix_db._validate_positive_number(value, "cost_usd")


@pytest.mark.parametrize("value", [True, False, "1.2", None])
def test_validate_positive_number_rejects_non_numeric_values(value: object) -> None:
    with pytest.raises(ValueError, match="cost_usd must be a number"):
        helix_db._validate_positive_number(value, "cost_usd")


@pytest.mark.parametrize("cost_usd", [math.nan, math.inf, -math.inf])
def test_upsert_session_telemetry_rejects_non_finite_cost(tmp_path: Path, cost_usd: float) -> None:
    db_path = _init_db(tmp_path, "non-finite-cost")

    with helix_db._write_connection(str(db_path)) as conn:
        with pytest.raises(ValueError, match="cost_usd must be finite"):
            helix_db.upsert_session_telemetry(
                conn,
                "sess-non-finite",
                actor="stop.sh",
                cost_usd=cost_usd,
            )


def test_upsert_session_telemetry_accepts_float_cost(tmp_path: Path) -> None:
    db_path = _init_db(tmp_path, "float-cost")

    with helix_db._write_connection(str(db_path)) as conn:
        helix_db.upsert_session_telemetry(
            conn,
            "sess-float",
            actor="stop.sh",
            cost_usd=0.125,
        )

    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT cost_usd FROM session_telemetry WHERE session_id = ?",
            ("sess-float",),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row[0] == pytest.approx(0.125)
