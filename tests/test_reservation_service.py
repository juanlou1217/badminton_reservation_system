from __future__ import annotations

import pytest

from app.models import Reservation, User
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

    SettingsService(db_session, seeded_db["admin"]).set_value("max_daily_reservations", "1", "每日最大预约次数")
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


def test_create_reservation_counts_verified_booking_in_daily_limit(db_session, seeded_db):
    from datetime import date, time

    from app.models import TimeSlot
    from app.services.settings_service import SettingsService

    SettingsService(db_session, seeded_db["admin"]).set_value("max_daily_reservations", "1", "每日最大预约次数")
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
    reservation = service.create_reservation(user_id=seeded_db["user"].id, slot_id=seeded_db["slot"].id)
    service.verify_reservation(reservation.id, seeded_db["admin"])

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
        current_user=seeded_db["user"],
    )

    assert cancelled.status == "cancelled"
    assert db_session.query(Reservation).filter_by(id=reservation.id).one().cancelled_at is not None


def test_cancel_reservation_rejects_other_user(db_session, seeded_db):
    service = ReservationService(db_session)
    other_user = User(
        username="charlie",
        phone="13600000000",
        password_hash="placeholder",
        role="user",
        status="normal",
    )
    db_session.add(other_user)
    db_session.commit()
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    with pytest.raises(ReservationError, match="只能取消自己的预约"):
        service.cancel_reservation(
            reservation_id=reservation.id,
            current_user=other_user,
        )


def test_admin_can_cancel_any_booking(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    cancelled = service.cancel_reservation(
        reservation_id=reservation.id,
        current_user=seeded_db["admin"],
    )

    assert cancelled.status == "cancelled"


def test_admin_can_verify_booked_reservation(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    verified = service.verify_reservation(
        reservation_id=reservation.id,
        current_user=seeded_db["admin"],
    )

    assert verified.status == "finished"
    assert seeded_db["slot"].status == "booked"


def test_verify_reservation_requires_admin(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )

    with pytest.raises(ReservationError, match="需要管理员权限"):
        service.verify_reservation(
            reservation_id=reservation.id,
            current_user=seeded_db["user"],
        )


def test_cancel_reservation_rejects_verified_booking(db_session, seeded_db):
    service = ReservationService(db_session)
    reservation = service.create_reservation(
        user_id=seeded_db["user"].id,
        slot_id=seeded_db["slot"].id,
    )
    service.verify_reservation(
        reservation_id=reservation.id,
        current_user=seeded_db["admin"],
    )

    with pytest.raises(ReservationError, match="预约已取消或已完成"):
        service.cancel_reservation(
            reservation_id=reservation.id,
            current_user=seeded_db["admin"],
        )


def test_list_all_reservations_requires_admin(db_session, seeded_db):
    service = ReservationService(db_session)

    with pytest.raises(ReservationError, match="需要管理员权限"):
        service.list_all_reservations(current_user=seeded_db["user"])
