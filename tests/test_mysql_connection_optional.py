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
        tables = {row[0] for row in connection.execute(text("SHOW TABLES")).fetchall()}

    assert database == os.environ["DB_NAME"]
    assert expected_tables.issubset(tables)
