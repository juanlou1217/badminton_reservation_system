from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from app.db import get_engine


@pytest.mark.skipif(
    os.getenv("RUN_MYSQL_TESTS") != "1",
    reason="Set RUN_MYSQL_TESTS=1 and DB_* variables to run remote MySQL checks.",
)
def test_remote_mysql_connection_and_tables_exist():
    expected_tables = {"users", "courts", "time_slots", "reservations", "settings"}

    with get_engine().connect() as connection:
        database = connection.execute(text("SELECT DATABASE()")).scalar_one()
        charset = connection.execute(text("SELECT @@character_set_database")).scalar_one()
        first_ping = connection.execute(text("SELECT 1")).scalar_one()
        tables = {row[0] for row in connection.execute(text("SHOW TABLES")).fetchall()}
        reservation_columns = {
            row[0]: row for row in connection.execute(text("SHOW COLUMNS FROM reservations")).fetchall()
        }
        reservation_indexes = {
            row[2] for row in connection.execute(text("SHOW INDEX FROM reservations")).fetchall()
        }
    with get_engine().connect() as connection:
        second_ping = connection.execute(text("SELECT 1")).scalar_one()

    assert database == os.environ["DB_NAME"]
    assert charset == "utf8mb4"
    assert first_ping == 1
    assert second_ping == 1
    assert expected_tables.issubset(tables)
    assert "active_slot_id" in reservation_columns
    assert "GENERATED" in reservation_columns["active_slot_id"].Extra.upper()
    assert "uq_reservations_active_slot" in reservation_indexes
