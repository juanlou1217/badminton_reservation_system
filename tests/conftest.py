from __future__ import annotations

from datetime import date, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Court, TimeSlot, User


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seeded_db(db_session):
    admin = User(
        username="admin",
        phone="13800000000",
        password_hash="placeholder",
        role="admin",
        status="normal",
    )
    user = User(
        username="alice",
        phone="13900000000",
        password_hash="placeholder",
        role="user",
        status="normal",
    )
    court = Court(
        court_no="C01",
        name="一号场",
        location="体育馆一层",
        status="open",
        remark="",
    )
    db_session.add_all([admin, user, court])
    db_session.flush()
    slot = TimeSlot(
        court_id=court.id,
        slot_date=date(2026, 5, 20),
        start_time=time(8, 0),
        end_time=time(10, 0),
        status="available",
    )
    db_session.add(slot)
    db_session.commit()
    return {"admin": admin, "user": user, "court": court, "slot": slot}
