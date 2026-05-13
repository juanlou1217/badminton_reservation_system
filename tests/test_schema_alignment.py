from __future__ import annotations

from sqlalchemy import create_engine, inspect

from app.models import Base


def test_create_all_includes_active_slot_constraint():
    engine = create_engine("sqlite:///:memory:", future=True)

    Base.metadata.create_all(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("reservations")}
    unique_constraints = {
        constraint["name"]
        for constraint in inspect(engine).get_unique_constraints("reservations")
    }
    assert "active_slot_id" in columns
    assert "uq_reservations_active_slot" in unique_constraints
