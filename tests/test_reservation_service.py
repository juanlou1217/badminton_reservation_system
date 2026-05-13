from __future__ import annotations

import pytest

from app.models import Reservation
from app.services.reservation_service import ReservationError, ReservationService


def test_create_reservation_books_available_slot(db_session, seeded_db):
    service = ReservationService(db_session)

    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    assert reservation.status == "booked"
    assert reservation.reservation_no.startswith("R")
    assert reservation.court_id == seeded_db["court"].id


def test_create_reservation_rejects_already_booked_slot(db_session, seeded_db):
    service = ReservationService(db_session)
    service.create_reservation(user_id=seeded_db["user"].id, slot_id=seeded_db["slot"].id)

    with pytest.raises(ReservationError, match="时间段已被预约"):
        service.create_reservation(user_id=seeded_db["user"].id, slot_id=seeded_db["slot"].id)


def test_create_reservation_respects_daily_limit(db_session, seeded_db):
    from datetime import date, time

    from app.models import TimeSlot
    from app.services.settings_service import SettingsService

    SettingsService(db_session).set_value("max_daily_reservations", "1", "每日最大预约次数")
    second_slot = TimeSlot(
        court_id=seeded_db["court"].id,
        slot_date=date(2026, 5, 20),
        start_time=time(10, 0),
        end_time=time(12, 0),
        status="available",
    )
    db_session.add(second_slot)
    db_session.commit()
    service = ReservationService(db_session)
    service.create_reservation(user_id=seeded_db["user"].id, slot_id=seeded_db["slot"].id)

    with pytest.raises(ReservationError, match="超过每日预约次数限制"):
        service.create_reservation(user_id=seeded_db["user"].id, slot_id=second_slot.id)


def test_cancel_reservation_only_cancels_owner_booking(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    cancelled = service.cancel_reservation(
        reservation_id=reservation.id,
        current_user_id=seeded_db["user"].id,
        is_admin=False,
    )

    assert cancelled.status == "cancelled"
    assert db_session.query(Reservation).filter_by(id=reservation.id).one().cancelled_at is not None


def test_cancel_reservation_rejects_other_user(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    with pytest.raises(ReservationError, match="只能取消自己的预约"):
        service.cancel_reservation(
            reservation_id=reservation.id,
            current_user_id=999,
            is_admin=False,
        )
